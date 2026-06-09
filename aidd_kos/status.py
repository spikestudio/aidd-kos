"""status コマンドの実装"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

_LIGHTRAG_HEALTH_URL_TPL = "{}/health"
_LIGHTRAG_PIPELINE_URL_TPL = "{}/documents/pipeline_status"
_LIGHTRAG_DOCS_URL_TPL = "{}/documents"
_INDEX_EXTS = frozenset({".md", ".txt"})

_LIGHTRAG_UNAVAILABLE = "LIGHTRAG_UNAVAILABLE"


class StatusChecker:
    def __init__(self, project_dir: Path | None = None) -> None:
        self._project_dir = (project_dir or Path.cwd()).resolve()
        self._lightrag_url = os.environ.get("LIGHTRAG_URL", "http://localhost:9621")

    def check(self) -> dict:
        return {
            "lightrag": self._check_lightrag(),
            "codegraph": self._check_codegraph(),
        }

    def _check_lightrag(self) -> dict:
        health_url = _LIGHTRAG_HEALTH_URL_TPL.format(self._lightrag_url)
        try:
            with urllib.request.urlopen(health_url, timeout=3):
                pass
        except (urllib.error.URLError, OSError):
            return {
                "status": "error",
                "indexed_at": None,
                "doc_count": 0,
                "changed_count": 0,
                "error_code": _LIGHTRAG_UNAVAILABLE,
            }

        # 判定優先順: indexing → stale → ready
        status = "ready"
        progress: dict | None = None
        pipeline_url = _LIGHTRAG_PIPELINE_URL_TPL.format(self._lightrag_url)
        try:
            with urllib.request.urlopen(pipeline_url, timeout=2) as resp:
                pipeline = json.loads(resp.read())
            if pipeline.get("busy"):
                status = "indexing"
                docs = pipeline.get("docs", 0)
                cur_batch = pipeline.get("cur_batch", 0)
                if docs > 0:
                    progress = {"processed": cur_batch, "total": docs}
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            pass

        # インデックス日時
        lightrag_dir = self._project_dir / ".lightrag"
        last_indexed_file = lightrag_dir / "last_indexed_at"
        indexed_at = last_indexed_file.read_text().strip() if last_indexed_file.exists() else None

        # Stale 検出（indexing 中はスキップ）
        changed_count = 0
        if status == "ready" and indexed_at:
            changed_count = self._count_changed_files(indexed_at)
            if changed_count > 0:
                status = "stale"

        # ドキュメント件数
        doc_count = 0
        docs_url = _LIGHTRAG_DOCS_URL_TPL.format(self._lightrag_url)
        try:
            with urllib.request.urlopen(docs_url, timeout=2) as resp:
                docs = json.loads(resp.read())
                if isinstance(docs, list):
                    doc_count = len(docs)
                elif isinstance(docs, dict):
                    statuses = docs.get("statuses", docs.get("data", []))
                    if isinstance(statuses, list):
                        doc_count = len(statuses)
                    elif isinstance(statuses, dict):
                        doc_count = sum(len(v) for v in statuses.values() if isinstance(v, list))
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            pass

        return {
            "status": status,
            "indexed_at": indexed_at,
            "doc_count": doc_count,
            "changed_count": changed_count,
            "error_code": None,
            "progress": progress,
        }

    def _count_changed_files(self, indexed_at: str) -> int:
        """last_indexed_at より新しい .md/.txt ファイル数を返す。"""
        try:
            ts = datetime.fromisoformat(indexed_at).astimezone(UTC).timestamp()
        except (ValueError, TypeError):
            return 0
        count = 0
        for f in self._project_dir.rglob("*"):
            if f.suffix in _INDEX_EXTS and f.is_file():
                try:
                    if f.stat().st_mtime > ts:
                        count += 1
                except OSError:
                    pass
        return count

    def _check_codegraph(self) -> dict:
        try:
            result = subprocess.run(
                ["npx", "@colbymchenry/codegraph", "status", "--json", "."],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return {"status": "unavailable", "node_count": 0}
            data = json.loads(result.stdout)
            if data.get("initialized"):
                return {"status": "ready", "node_count": data.get("nodeCount", 0)}
            return {"status": "unavailable", "node_count": 0}
        except Exception:
            return {"status": "unavailable", "node_count": 0}
