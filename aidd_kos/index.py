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
_BATCH_SIZE = 10
_PAGE_SIZE = 500


class IndexOrchestrator:
    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = (project_dir or Path.cwd()).resolve()

    def collect_files(self) -> list[Path]:
        files = []
        for ext in _INDEX_EXTENSIONS:
            files.extend(self.project_dir.rglob(f"*{ext}"))
        return [f for f in files if not any(p.startswith(".") for p in f.parts)]

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
            except Exception:
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
            rel_path = str(f.relative_to(self.project_dir))
            if rel_path not in indexed:
                new_files.append(f)
            else:
                updated_at_str = indexed[rel_path]["updated_at"]
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
        """indexed にあるが filesystem にないファイルを検出し {rel_path: doc_id} で返す。"""
        fs_paths = {str(f.relative_to(self.project_dir)) for f in files}
        return {
            rel_path: info["id"] for rel_path, info in indexed.items() if rel_path not in fs_paths
        }

    def _delete_docs(self, deleted: dict[str, str]) -> int:
        """deleted_docs ({rel_path: doc_id}) を LightRAG から削除し削除件数を返す。
        deleted が空の場合は API を呼ばずに 0 を返す。
        """
        if not deleted:
            return 0
        payload = json.dumps(
            {"doc_ids": list(deleted.values()), "delete_file": False, "delete_llm_cache": False}
        ).encode()
        req = urllib.request.Request(
            _LIGHTRAG_DELETE_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(req, timeout=30):
                pass
        except urllib.error.URLError:
            emit_error(LIGHTRAG_UNAVAILABLE, "task server:start を実行してください")
            sys.exit(1)
        return len(deleted)

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
                    sources.append(str(f.relative_to(self.project_dir)))
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
            except urllib.error.URLError:
                emit_error(LIGHTRAG_UNAVAILABLE, "task server:start を実行してください")
                sys.exit(1)
        return batches_sent, skipped_read

    def run(self, *, full: bool = False) -> dict:
        files = self.collect_files()
        start = time.monotonic()

        if full:
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
        deleted_docs = self._detect_deleted(files, indexed)
        deleted_count = self._delete_docs(deleted_docs)
        new_files, modified_files, skip_files = self._classify_files(files, indexed)

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
            "deleted_count": deleted_count,
            "elapsed_seconds": elapsed,
            "file_count": sent_count,  # backward compat
        }
