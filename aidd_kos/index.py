"""index コマンドのオーケストレーション（LightRAG in-process 化）"""

from __future__ import annotations

import asyncio
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from aidd_kos.config import create_lightrag_instance
from aidd_kos.errors import LIGHTRAG_UNAVAILABLE, emit_error

_INDEX_EXTENSIONS = {".md", ".txt"}
_BATCH_SIZE = 10


class IndexOrchestrator:
    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = (project_dir or Path.cwd()).resolve()
        self._lightrag_dir = str(self.project_dir / ".lightrag")

    def collect_files(self) -> list[Path]:
        files = []
        for ext in _INDEX_EXTENSIONS:
            files.extend(self.project_dir.rglob(f"*{ext}"))
        # project_dir からの相対パスで判定することで、絶対パスに含まれる . 始まりディレクトリを誤除外しない
        return [
            f
            for f in files
            if not any(p.startswith(".") for p in f.relative_to(self.project_dir).parts)
        ]

    def _to_source_key(self, f: Path) -> str:
        """LightRAG に送る file_source キーを生成する。
        as_posix() で OS 非依存の相対パスを取得し、'/' を '___'（トリプルアンダースコア）
        に置換してパス情報を保持する。
        例: docs/spec/install.md → docs___spec___install.md
        制約: ファイル名に '___' を含むファイルは非対応。
        """
        return f.relative_to(self.project_dir).as_posix().replace("/", "___")

    def _fetch_indexed_docs(self) -> dict[str, dict]:
        """LightRAG の Python API から全インデックス済みドキュメントを取得する。
        例外発生時は空 dict を返す（全件処理にフォールバック）。
        """
        try:
            from lightrag.base import DocStatus

            rag = create_lightrag_instance(self._lightrag_dir)

            async def _fetch() -> dict[str, dict]:
                await rag.initialize_storages()
                try:
                    docs = await rag.get_docs_by_status(DocStatus.PROCESSED)
                    return {
                        doc.file_path: {
                            "id": doc_id,
                            "updated_at": doc.updated_at if hasattr(doc, "updated_at") else "",
                        }
                        for doc_id, doc in docs.items()
                    }
                finally:
                    await rag.finalize_storages()

            return asyncio.run(_fetch())
        except Exception as e:
            emit_error(
                LIGHTRAG_UNAVAILABLE,
                f"インデックス状態の取得に失敗しました ({type(e).__name__}）: 全件処理にフォールバックします",
            )
            return {}

    def _classify_files(
        self,
        files: list[Path],
        indexed: dict[str, dict],
    ) -> tuple[list[Path], list[Path], list[Path]]:
        """ファイルを new / modified / skip に分類する。
        mtime と LightRAG の updated_at（UTC naive ISO8601）を比較する。
        """
        new_files: list[Path] = []
        modified_files: list[Path] = []
        skip_files: list[Path] = []

        for f in files:
            key = self._to_source_key(f)
            if key not in indexed:
                new_files.append(f)
            else:
                updated_at_str = indexed[key]["updated_at"]
                try:
                    updated_at_ts = (
                        datetime.fromisoformat(updated_at_str).replace(tzinfo=UTC).timestamp()
                    )
                    if f.stat().st_mtime > updated_at_ts:
                        modified_files.append(f)
                    else:
                        skip_files.append(f)
                except (ValueError, OSError):
                    modified_files.append(f)

        return new_files, modified_files, skip_files

    def _detect_deleted(
        self,
        files: list[Path],
        indexed: dict[str, dict],
    ) -> dict[str, str]:
        """indexed にあるが filesystem にないファイルを検出し {source_key: doc_id} で返す。"""
        fs_keys = {self._to_source_key(f) for f in files}
        return {key: info["id"] for key, info in indexed.items() if key not in fs_keys}

    def _delete_docs(self, deleted: dict[str, str]) -> int:
        """deleted_docs ({source_key: doc_id}) を LightRAG から削除し削除件数を返す。
        deleted が空の場合は 0 を返す。
        """
        if not deleted:
            return 0
        try:
            rag = create_lightrag_instance(self._lightrag_dir)

            async def _delete() -> None:
                await rag.initialize_storages()
                try:
                    for doc_id in deleted.values():
                        await rag.adelete_by_doc_id(doc_id)
                finally:
                    await rag.finalize_storages()

            asyncio.run(_delete())
            return len(deleted)
        except Exception:
            print(
                "[aidd-kos] 警告: 削除中にエラーが発生しました。処理を続行します。",
                file=sys.stderr,
            )
            return 0

    def _send_files(self, files: list[Path]) -> tuple[int, int]:
        """files を LightRAG に送信し (batches_sent, skipped_read) を返す。"""
        batches_sent = 0
        skipped_read = 0

        try:
            rag = create_lightrag_instance(self._lightrag_dir)

            async def _insert_all() -> tuple[int, int]:
                nonlocal batches_sent, skipped_read
                await rag.initialize_storages()
                try:
                    for i in range(0, len(files), _BATCH_SIZE):
                        batch = files[i : i + _BATCH_SIZE]
                        texts = []
                        sources = []
                        for f in batch:
                            try:
                                content = f.read_text(encoding="utf-8", errors="replace")
                                if not content.strip():
                                    skipped_read += 1
                                    continue
                                texts.append(content)
                                sources.append(self._to_source_key(f))
                            except OSError:
                                skipped_read += 1
                                continue
                        if not texts:
                            continue
                        await rag.ainsert(texts, file_paths=sources)
                        batches_sent += 1
                finally:
                    await rag.finalize_storages()
                return batches_sent, skipped_read

            return asyncio.run(_insert_all())
        except Exception as e:
            emit_error(
                LIGHTRAG_UNAVAILABLE,
                f"LightRAG へのインデックス送信に失敗しました ({type(e).__name__}）",
            )
            sys.exit(1)

    def _write_last_indexed_at(self) -> None:
        """正常完了後に .lightrag/last_indexed_at を更新する。"""
        lightrag_path = Path(self._lightrag_dir)
        lightrag_path.mkdir(parents=True, exist_ok=True)
        (lightrag_path / "last_indexed_at").write_text(datetime.now(UTC).isoformat())

    def run(self, *, full: bool = False) -> dict:
        files = self.collect_files()
        start = time.monotonic()

        if full:
            # --full: .lightrag/ を再初期化してから全件インサート
            lightrag_path = Path(self._lightrag_dir)
            if lightrag_path.exists():
                shutil.rmtree(lightrag_path)
            lightrag_path.mkdir(parents=True, exist_ok=True)

            batches_sent, skipped_read = self._send_files(files)
            if files and batches_sent == 0:
                emit_error(
                    LIGHTRAG_UNAVAILABLE,
                    f"全 {len(files)} ファイルの読み取りに失敗しました。ファイルのアクセス権限を確認してください。",
                )
                sys.exit(1)
            elapsed = time.monotonic() - start
            full_count = len(files) - skipped_read
            self._write_last_indexed_at()
            return {
                "full_count": full_count,
                "new_count": full_count,
                "updated_count": 0,
                "skip_count": 0,
                "deleted_count": 0,
                "elapsed_seconds": elapsed,
                "file_count": full_count,  # backward compat
            }

        indexed = self._fetch_indexed_docs()
        new_files, modified_files, skip_files = self._classify_files(files, indexed)

        # 変更ファイルは LightRAG が上書き禁止のため先に DELETE してから再インサートする
        modified_docs = {
            self._to_source_key(f): indexed[self._to_source_key(f)]["id"]
            for f in modified_files
            if self._to_source_key(f) in indexed
        }
        deleted_docs = self._detect_deleted(files, indexed)
        docs_to_delete = {**modified_docs, **deleted_docs}
        self._delete_docs(docs_to_delete)

        to_process = new_files + modified_files
        batches_sent, skipped_read = self._send_files(to_process)

        # C-3: 送信対象があるのに1件も送信できなかった場合はエラーを通知する
        if to_process and batches_sent == 0:
            emit_error(
                LIGHTRAG_UNAVAILABLE,
                f"全 {len(to_process)} ファイルの読み取りに失敗しました。ファイルのアクセス権限を確認してください。",
            )
            sys.exit(1)

        elapsed = time.monotonic() - start
        sent_count = len(to_process) - skipped_read
        self._write_last_indexed_at()
        return {
            "new_count": len(new_files),
            "updated_count": len(modified_files),
            "skip_count": len(skip_files),
            "deleted_count": len(deleted_docs),  # ユーザー視点: filesystem から削除されたファイル数
            "elapsed_seconds": elapsed,
            "file_count": sent_count,  # backward compat
        }
