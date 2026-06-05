"""ユニットテスト: aidd_kos.install (InstallOrchestrator)"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aidd_kos.install import InstallOrchestrator


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


def test_ac_f01_05_unit_preflight_raises_if_mise_missing(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-F01-05: Unit - mise が PATH にない場合 preflight_check() が SystemExit を発生させる"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("PATH", "/nonexistent")
    orch = InstallOrchestrator(project_dir=project_dir)
    with pytest.raises(SystemExit) as exc_info:
        orch.preflight_check()
    assert exc_info.value.code == 1


def test_ac_f01_06_unit_preflight_raises_if_no_api_key(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-F01-06: Unit - OPENAI_API_KEY が未設定の場合 preflight_check() が SystemExit を発生させる"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    orch = InstallOrchestrator(project_dir=project_dir)
    with pytest.raises(SystemExit) as exc_info:
        orch.preflight_check()
    assert exc_info.value.code == 1


def test_ac_f01_07_unit_update_gitignore_adds_lightrag(project_dir: Path) -> None:
    """AC-F01-07: Unit - update_gitignore() が .lightrag/ を .gitignore に追記する"""
    orch = InstallOrchestrator(project_dir=project_dir)
    orch.update_gitignore()
    assert ".lightrag/" in (project_dir / ".gitignore").read_text()


def test_ac_f01_08_unit_update_gitignore_adds_codegraph(project_dir: Path) -> None:
    """AC-F01-08: Unit - update_gitignore() が .codegraph/ を .gitignore に追記する"""
    orch = InstallOrchestrator(project_dir=project_dir)
    orch.update_gitignore()
    assert ".codegraph/" in (project_dir / ".gitignore").read_text()


def test_ac_f01_09_unit_update_gitignore_no_duplicate(project_dir: Path) -> None:
    """AC-F01-09: Unit - .gitignore に既に記載済みの場合は重複しない"""
    gitignore = project_dir / ".gitignore"
    gitignore.write_text(".lightrag/\n")
    orch = InstallOrchestrator(project_dir=project_dir)
    orch.update_gitignore()
    assert gitignore.read_text().count(".lightrag/") == 1


def test_ac_f01_10_unit_init_storage_preserves_existing_lightrag(project_dir: Path) -> None:
    """AC-F01-10: Unit - init_storage() が既存 .lightrag/ を削除しない"""
    dummy = project_dir / ".lightrag" / "existing.txt"
    dummy.parent.mkdir()
    dummy.write_text("keep me")
    with patch("aidd_kos.install.subprocess") as mock_sub:
        mock_sub.run.return_value = MagicMock(returncode=0)
        orch = InstallOrchestrator(project_dir=project_dir)
        orch.init_storage()
    assert dummy.exists()


def test_ac_f01_10_unit_init_storage_creates_lightrag_dir(project_dir: Path) -> None:
    """AC-F01-04/10: Unit - init_storage() が .lightrag/ を作成する"""
    with patch("aidd_kos.install.subprocess") as mock_sub:
        mock_sub.run.return_value = MagicMock(returncode=0)
        orch = InstallOrchestrator(project_dir=project_dir)
        orch.init_storage()
    assert (project_dir / ".lightrag").is_dir()


# ── Feature #40: プロジェクトレベル MCP 登録 ─────────────────────────────────────


def test_ac_f40_01_unit_register_mcp_default_writes_settings_local(
    project_dir: Path, fake_home: Path
) -> None:
    """AC-F40-01: Unit - デフォルト動作で .claude/settings.local.json に cwd なしで書き込む"""
    orch = InstallOrchestrator(project_dir=project_dir, global_install=False)
    orch.register_mcp()

    local_settings = project_dir / ".claude" / "settings.local.json"
    assert local_settings.exists()
    data = local_settings.read_text()
    import json

    parsed = json.loads(data)
    entry = parsed["mcpServers"]["aidd-kos"]
    assert "cwd" not in entry


def test_ac_f40_01_unit_register_mcp_default_does_not_write_global(
    project_dir: Path, fake_home: Path
) -> None:
    """AC-F40-03: Unit - デフォルト動作で ~/.claude/settings.json に書き込まない"""
    orch = InstallOrchestrator(project_dir=project_dir, global_install=False)
    orch.register_mcp()

    global_settings = fake_home / ".claude" / "settings.json"
    assert not global_settings.exists(), "~/.claude/settings.json に書き込まれた"


def test_ac_f40_03_unit_register_mcp_does_not_modify_existing_global(
    project_dir: Path, fake_home: Path
) -> None:
    """AC-F40-03: Unit - 既存グローバル設定の aidd-kos エントリを変更しない"""
    import json

    global_path = fake_home / ".claude" / "settings.json"
    global_path.parent.mkdir(parents=True, exist_ok=True)
    original = {"command": "uvx", "args": ["old"], "cwd": "/old/path"}
    global_path.write_text(json.dumps({"mcpServers": {"aidd-kos": original}}))

    orch = InstallOrchestrator(project_dir=project_dir, global_install=False)
    orch.register_mcp()

    data = json.loads(global_path.read_text())
    assert data["mcpServers"]["aidd-kos"] == original


def test_ac_f40_04_unit_register_mcp_global_writes_cwd(project_dir: Path, fake_home: Path) -> None:
    """AC-F40-04: Unit - --global で ~/.claude/settings.json に cwd 付きで書き込む"""
    import json

    orch = InstallOrchestrator(project_dir=project_dir, global_install=True)
    orch.register_mcp()

    global_settings = fake_home / ".claude" / "settings.json"
    assert global_settings.exists()
    data = json.loads(global_settings.read_text())
    entry = data["mcpServers"]["aidd-kos"]
    assert entry["cwd"] == str(project_dir.resolve())
