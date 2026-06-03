"""index コマンドのオーケストレーション"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from aidd_kos.errors import LIGHTRAG_UNAVAILABLE, emit_error

_INDEX_EXTENSIONS = {".md", ".txt"}
_LIGHTRAG_SCAN_URL = "http://localhost:9621/documents/scan"


class IndexOrchestrator:
    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = (project_dir or Path.cwd()).resolve()

    def collect_files(self) -> list[Path]:
        files = []
        for ext in _INDEX_EXTENSIONS:
            files.extend(self.project_dir.rglob(f"*{ext}"))
        return [f for f in files if not any(p.startswith(".") for p in f.parts)]

    def run(self) -> dict:
        files = self.collect_files()
        start = time.monotonic()

        payload = json.dumps({"input_dir": str(self.project_dir)}).encode()
        req = urllib.request.Request(
            _LIGHTRAG_SCAN_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30):
                pass
        except urllib.error.URLError:
            emit_error(LIGHTRAG_UNAVAILABLE, "task server:start を実行してください")
            sys.exit(1)

        elapsed = time.monotonic() - start
        return {"file_count": len(files), "elapsed_seconds": elapsed}
