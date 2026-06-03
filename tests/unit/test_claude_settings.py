"""ユニットテスト: aidd_kos.claude_settings (settings.json 安全マージ)"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aidd_kos.claude_settings import ClaudeSettings


@pytest.fixture()
def settings_path(tmp_path: Path) -> Path:
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    return claude_dir / "settings.json"


def test_ac_f01_03_unit_add_mcp_entry(settings_path: Path) -> None:
    """AC-F01-03: Unit - add_mcp_entry() が mcpServers に aidd-kos エントリを追加する"""
    cs = ClaudeSettings(settings_path)
    cs.add_mcp_entry("aidd-kos", {"command": "uvx", "args": ["aidd-kos@latest", "serve"]})
    data = json.loads(settings_path.read_text())
    assert "aidd-kos" in data["mcpServers"]
    assert data["mcpServers"]["aidd-kos"]["command"] == "uvx"


def test_ac_f01_03_unit_mcp_entry_no_env_field(settings_path: Path) -> None:
    """AC-F01-03: Unit - OPENAI_API_KEY は settings.json の env フィールドに書き込まれない（セキュリティ）"""
    cs = ClaudeSettings(settings_path)
    cs.add_mcp_entry("aidd-kos", {"command": "uvx", "args": ["aidd-kos@latest", "serve"]})
    data = json.loads(settings_path.read_text())
    entry = data["mcpServers"]["aidd-kos"]
    assert "env" not in entry


def test_ac_f01_12_unit_other_entries_preserved(settings_path: Path) -> None:
    """AC-F01-12: Unit - 既存の他 MCP エントリが保持される"""
    settings_path.write_text(
        json.dumps({"mcpServers": {"other-tool": {"command": "npx", "args": ["other"]}}})
    )
    cs = ClaudeSettings(settings_path)
    cs.add_mcp_entry("aidd-kos", {"command": "uvx", "args": ["aidd-kos@latest", "serve"]})
    data = json.loads(settings_path.read_text())
    assert "other-tool" in data["mcpServers"]
    assert data["mcpServers"]["other-tool"]["command"] == "npx"


def test_ac_f01_12_unit_key_count_preserved(settings_path: Path) -> None:
    """AC-F01-12: Unit - マージ後のキー数が既存以上であること（ロールバック安全保証）"""
    initial = {"mcpServers": {"tool-a": {}, "tool-b": {}}}
    settings_path.write_text(json.dumps(initial))
    cs = ClaudeSettings(settings_path)
    cs.add_mcp_entry("aidd-kos", {"command": "uvx", "args": []})
    data = json.loads(settings_path.read_text())
    assert len(data["mcpServers"]) >= 2


def test_unit_file_size_limit(settings_path: Path) -> None:
    """Unit - 10MB 超の settings.json はエラーになる"""
    large_content = "x" * (10 * 1024 * 1024 + 1)
    settings_path.write_text(large_content)
    cs = ClaudeSettings(settings_path)
    with pytest.raises(ValueError, match="CLAUDE_SETTINGS_TOO_LARGE"):
        cs.add_mcp_entry("aidd-kos", {})


def test_unit_new_file_created_if_not_exists(tmp_path: Path) -> None:
    """Unit - settings.json が存在しない場合は新規作成される"""
    path = tmp_path / ".claude" / "settings.json"
    path.parent.mkdir()
    cs = ClaudeSettings(path)
    cs.add_mcp_entry("aidd-kos", {"command": "uvx", "args": []})
    assert path.exists()
