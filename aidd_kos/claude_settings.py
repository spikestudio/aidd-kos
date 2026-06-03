"""~/.claude/settings.json の安全な読み書き"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from aidd_kos.errors import CLAUDE_SETTINGS_TOO_LARGE

_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


class ClaudeSettings:
    def __init__(self, path: Path) -> None:
        self._path = path

    def _read(self) -> dict:
        if not self._path.exists():
            return {}
        size = self._path.stat().st_size
        if size > _MAX_SIZE_BYTES:
            raise ValueError(CLAUDE_SETTINGS_TOO_LARGE)
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # バックアップを作成してから書き込み
        if self._path.exists():
            shutil.copy2(self._path, self._path.with_suffix(".json.bak"))
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_mcp_entry(self, name: str, entry: dict) -> None:
        """mcpServers に name エントリを追加する。既存エントリは保持する。"""
        existing = self._read()
        before_count = len(existing.get("mcpServers", {}))

        mcp_servers = existing.setdefault("mcpServers", {})
        mcp_servers[name] = entry

        after_count = len(mcp_servers)
        if after_count < before_count:
            raise RuntimeError("マージ後のキー数が減少しました。ロールバックします。")

        self._write(existing)
