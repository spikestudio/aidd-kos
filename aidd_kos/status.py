"""status コマンドの実装"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

_LIGHTRAG_HEALTH_URL_TPL = "{}/health"
_LIGHTRAG_PIPELINE_URL_TPL = "{}/documents/pipeline_status"
_LIGHTRAG_DOCS_URL_TPL = "{}/documents"


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
            return {"status": "unavailable", "indexed_at": None, "doc_count": 0}

        # indexing 状態確認
        status = "ready"
        pipeline_url = _LIGHTRAG_PIPELINE_URL_TPL.format(self._lightrag_url)
        try:
            with urllib.request.urlopen(pipeline_url, timeout=2) as resp:
                pipeline = json.loads(resp.read())
            if pipeline.get("busy"):
                status = "indexing"
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            pass

        # インデックス日時（.lightrag/last_indexed_at ファイルから）
        lightrag_dir = self._project_dir / ".lightrag"
        last_indexed_file = lightrag_dir / "last_indexed_at"
        indexed_at = last_indexed_file.read_text().strip() if last_indexed_file.exists() else None

        # ドキュメント件数
        doc_count = 0
        docs_url = _LIGHTRAG_DOCS_URL_TPL.format(self._lightrag_url)
        try:
            with urllib.request.urlopen(docs_url, timeout=2) as resp:
                docs = json.loads(resp.read())
                if isinstance(docs, list):
                    doc_count = len(docs)
                elif isinstance(docs, dict):
                    doc_count = len(docs.get("data", []))
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            pass

        return {"status": status, "indexed_at": indexed_at, "doc_count": doc_count}

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
