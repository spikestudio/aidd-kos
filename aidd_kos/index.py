"""index コマンドのオーケストレーション"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from aidd_kos.errors import LIGHTRAG_UNAVAILABLE, emit_error

_INDEX_EXTENSIONS = {".md", ".txt"}
_LIGHTRAG_TEXTS_URL = os.environ.get("LIGHTRAG_URL", "http://localhost:9621") + "/documents/texts"
_BATCH_SIZE = 10  # LightRAG に一度に送るファイル数


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

        # LightRAG v1.5.0: /documents/texts にファイル内容を直接送信する
        batches_sent = 0
        skipped_files = 0
        for i in range(0, len(files), _BATCH_SIZE):
            batch = files[i : i + _BATCH_SIZE]

            texts = []
            sources = []
            for f in batch:
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    texts.append(content)
                    sources.append(str(f.relative_to(self.project_dir)))
                except OSError:
                    skipped_files += 1
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

        # C-3: ファイルが存在するのに1件も送信できなかった場合はエラーを通知する
        if files and batches_sent == 0:
            emit_error(
                LIGHTRAG_UNAVAILABLE,
                f"全 {len(files)} ファイルの読み取りに失敗しました。ファイルのアクセス権限を確認してください。",
            )
            sys.exit(1)

        elapsed = time.monotonic() - start
        sent_count = len(files) - skipped_files
        return {"file_count": sent_count, "elapsed_seconds": elapsed}
