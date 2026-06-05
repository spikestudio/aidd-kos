"""index コマンドのオーケストレーション"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from aidd_kos.errors import LIGHTRAG_UNAVAILABLE, emit_error

_INDEX_EXTENSIONS = {".md", ".txt"}
_BASE_URL = os.environ.get("LIGHTRAG_URL", "http://localhost:9621")
_LIGHTRAG_TEXTS_URL = _BASE_URL + "/documents/texts"
_LIGHTRAG_PAGINATED_URL = _BASE_URL + "/documents/paginated"
_LIGHTRAG_DELETE_URL = _BASE_URL + "/documents/delete_document"
_LIGHTRAG_CLEAR_URL = _BASE_URL + "/documents"
_LIGHTRAG_HEALTH_URL = _BASE_URL + "/health"
_BATCH_SIZE = 10
_PAGE_SIZE = 200  # LightRAG v1.5.0 の page_size 上限
_PIPELINE_WAIT_TIMEOUT = 60  # 秒


class IndexOrchestrator:
    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = (project_dir or Path.cwd()).resolve()

    def collect_files(self) -> list[Path]:
        files = []
        for ext in _INDEX_EXTENSIONS:
            files.extend(self.project_dir.rglob(f"*{ext}"))
        return [f for f in files if not any(p.startswith(".") for p in f.parts)]

    def _to_source_key(self, f: Path) -> str:
        """LightRAG に送る file_source キーを生成する。
        LightRAG v1.5.0 は file_sources をベースネームに正規化するため、
        as_posix() で OS 非依存の相対パスを取得し、'/' を '___'（トリプルアンダースコア）
        に置換してパス情報を保持する。
        例: docs/spec/install.md → docs___spec___install.md
        制約: ファイル名に '___' を含むファイルは非対応。
        """
        return f.relative_to(self.project_dir).as_posix().replace("/", "___")

    def _fetch_indexed_docs(self) -> dict[str, dict]:
        """LightRAG の /documents/paginated から全インデックス済みドキュメントを取得する。
        URLError 以外の例外（JSON パース失敗等）は空 dict を返す（全件処理にフォールバック）。
        """
        result: dict[str, dict] = {}
        page = 1
        while True:
            payload = json.dumps({"page": page, "page_size": _PAGE_SIZE}).encode()
            req = urllib.request.Request(
                _LIGHTRAG_PAGINATED_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
                for doc in data["documents"]:
                    result[doc["file_path"]] = {
                        "id": doc["id"],
                        "updated_at": doc["updated_at"],
                    }
                if not data["pagination"]["has_next"]:
                    break
                page += 1
            except urllib.error.URLError:
                emit_error(LIGHTRAG_UNAVAILABLE, "task server:start を実行してください")
                sys.exit(1)
            except Exception as e:
                emit_error(
                    LIGHTRAG_UNAVAILABLE,
                    f"paginated API のレスポンス解析に失敗しました ({type(e).__name__}）: 全件処理にフォールバックします",
                )
                return {}
        return result

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
                updated_at_ts = (
                    datetime.fromisoformat(updated_at_str).replace(tzinfo=UTC).timestamp()
                )
                if f.stat().st_mtime > updated_at_ts:
                    modified_files.append(f)
                else:
                    skip_files.append(f)

        return new_files, modified_files, skip_files

    def _detect_deleted(
        self,
        files: list[Path],
        indexed: dict[str, dict],
    ) -> dict[str, str]:
        """indexed にあるが filesystem にないファイルを検出し {source_key: doc_id} で返す。"""
        fs_keys = {self._to_source_key(f) for f in files}
        return {key: info["id"] for key, info in indexed.items() if key not in fs_keys}

    def _delete_docs(self, deleted: dict[str, str], *, _max_retries: int = 3) -> int:
        """deleted_docs ({source_key: doc_id}) を LightRAG から削除し削除件数を返す。
        deleted が空の場合は API を呼ばずに 0 を返す。
        LightRAG がパイプライン busy を返した場合は _wait_pipeline_idle 後にリトライする。
        """
        if not deleted:
            return 0
        payload = json.dumps(
            {"doc_ids": list(deleted.values()), "delete_file": False, "delete_llm_cache": False}
        ).encode()
        for attempt in range(_max_retries):
            req = urllib.request.Request(
                _LIGHTRAG_DELETE_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="DELETE",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
            except urllib.error.URLError:
                emit_error(LIGHTRAG_UNAVAILABLE, "task server:start を実行してください")
                sys.exit(1)
            if data.get("status") != "busy":
                return len(deleted)
            if attempt < _max_retries - 1:
                self._wait_pipeline_idle()
        print(
            "[aidd-kos] 警告: LightRAG パイプラインが busy のため削除をスキップしました。"
            " `aidd-kos index --full` で再構築してください。",
            file=sys.stderr,
        )
        return 0

    def _wait_pipeline_idle(self) -> None:
        """LightRAG のパイプラインが idle になるまで待機する（最大 _PIPELINE_WAIT_TIMEOUT 秒）。"""
        deadline = time.monotonic() + _PIPELINE_WAIT_TIMEOUT
        while time.monotonic() < deadline:
            try:
                req = urllib.request.Request(_LIGHTRAG_HEALTH_URL, method="GET")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                if not data.get("pipeline_busy") and data.get("pipeline_pending_enqueues", 0) == 0:
                    return
            except Exception:
                pass
            time.sleep(2)
        print(
            "[aidd-kos] 警告: LightRAG パイプライン待機がタイムアウトしました。処理を続行します。",
            file=sys.stderr,
        )

    def _send_files(self, files: list[Path]) -> tuple[int, int]:
        """files を LightRAG に送信し (batches_sent, skipped_read) を返す。"""
        batches_sent = 0
        skipped_read = 0
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

            payload = json.dumps({"texts": texts, "file_sources": sources}).encode()
            req = urllib.request.Request(
                _LIGHTRAG_TEXTS_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30):
                    pass
                batches_sent += 1
            except urllib.error.HTTPError as e:
                if e.code == 409:
                    skipped_read += len(texts)  # 既存ドキュメント: スキップ扱い
                else:
                    emit_error(
                        LIGHTRAG_UNAVAILABLE,
                        f"LightRAG API エラー (HTTP {e.code}): task server:start を実行してください",
                    )
                    sys.exit(1)
            except urllib.error.URLError:
                emit_error(LIGHTRAG_UNAVAILABLE, "task server:start を実行してください")
                sys.exit(1)
        return batches_sent, skipped_read

    def run(self, *, full: bool = False) -> dict:
        files = self.collect_files()
        start = time.monotonic()

        if full:
            # --full: 全ドキュメントをクリアしてから全件インサート
            clear_req = urllib.request.Request(
                _LIGHTRAG_CLEAR_URL,
                headers={"Content-Type": "application/json"},
                method="DELETE",
            )
            try:
                with urllib.request.urlopen(clear_req, timeout=30):
                    pass
                self._wait_pipeline_idle()
            except urllib.error.URLError:
                emit_error(LIGHTRAG_UNAVAILABLE, "task server:start を実行してください")
                sys.exit(1)
            except Exception:
                pass  # clear 失敗は無視して続行
            batches_sent, skipped_read = self._send_files(files)
            if files and batches_sent == 0:
                emit_error(
                    LIGHTRAG_UNAVAILABLE,
                    f"全 {len(files)} ファイルの読み取りに失敗しました。ファイルのアクセス権限を確認してください。",
                )
                sys.exit(1)
            elapsed = time.monotonic() - start
            full_count = len(files) - skipped_read
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
        if docs_to_delete:
            self._wait_pipeline_idle()

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
        return {
            "new_count": len(new_files),
            "updated_count": len(modified_files),
            "skip_count": len(skip_files),
            "deleted_count": len(deleted_docs),  # ユーザー視点: filesystem から削除されたファイル数
            "elapsed_seconds": elapsed,
            "file_count": sent_count,  # backward compat
        }
