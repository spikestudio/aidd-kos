"""E2E テスト: Feature #40 プロジェクトレベル MCP 登録 (docs/spec/multi-project.md)"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "fake_home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture()
def env_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")


@pytest.fixture()
def mock_subprocesses(monkeypatch: pytest.MonkeyPatch):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_popen = MagicMock()
    mock_popen.poll.return_value = None
    with (
        patch("subprocess.run", return_value=mock_result),
        patch("subprocess.Popen", return_value=mock_popen),
        patch("urllib.request.urlopen"),
        patch("aidd_kos.install.InstallOrchestrator.start_lightrag_and_index"),
    ):
        yield


# ── AC-F40-01: デフォルトで .claude/settings.local.json に cwd なし ──────────────


@pytest.mark.integration
def test_ac_f40_01_e2e_default_writes_settings_local_json(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
) -> None:
    """AC-F40-01: E2E - デフォルト install で .claude/settings.local.json に cwd なしエントリが作成される"""
    result = runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert result.exit_code == 0

    local_settings = project_dir / ".claude" / "settings.local.json"
    assert local_settings.exists(), (
        f".claude/settings.local.json が作成されていない: {result.output}"
    )

    data = json.loads(local_settings.read_text())
    entry = data.get("mcpServers", {}).get("aidd-kos", {})
    assert entry, "mcpServers.aidd-kos エントリが存在しない"
    assert "cwd" not in entry, f"cwd フィールドが存在する（存在しないこと）: {entry}"


# ── AC-F40-03: デフォルト install は ~/.claude/settings.json を変更しない ──────────


@pytest.mark.integration
def test_ac_f40_03_e2e_global_settings_unchanged(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
) -> None:
    """AC-F40-03: E2E - デフォルト install は ~/.claude/settings.json の既存 aidd-kos エントリを変更しない"""
    global_settings_path = fake_home / ".claude" / "settings.json"
    global_settings_path.parent.mkdir(parents=True, exist_ok=True)
    original_entry = {"command": "uvx", "args": ["old-version"], "cwd": "/old/path"}
    global_settings_path.write_text(json.dumps({"mcpServers": {"aidd-kos": original_entry}}))

    result = runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert result.exit_code == 0

    data = json.loads(global_settings_path.read_text())
    assert data["mcpServers"]["aidd-kos"] == original_entry, (
        "~/.claude/settings.json の aidd-kos エントリが変更された"
    )


# ── AC-F40-04: --global で ~/.claude/settings.json に cwd 付き ─────────────────


@pytest.mark.integration
def test_ac_f40_04_e2e_global_flag_writes_settings_json_with_cwd(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
) -> None:
    """AC-F40-04: E2E - --global 指定で ~/.claude/settings.json に cwd 付きエントリが作成される"""
    result = runner.invoke(app, ["install", "--project-dir", str(project_dir), "--global"])
    assert result.exit_code == 0

    global_settings = fake_home / ".claude" / "settings.json"
    assert global_settings.exists(), "~/.claude/settings.json が作成されていない"

    data = json.loads(global_settings.read_text())
    entry = data.get("mcpServers", {}).get("aidd-kos", {})
    assert "cwd" in entry, "cwd フィールドが存在しない"
    assert entry["cwd"] == str(project_dir.resolve()), (
        f"cwd がプロジェクトルートの絶対パスでない: {entry['cwd']}"
    )


# ── AC-F40-05: 再 install で冪等性 ───────────────────────────────────────────


@pytest.mark.integration
def test_ac_f40_05_e2e_reinstall_idempotent(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
) -> None:
    """AC-F40-05: E2E - 再 install でエントリが重複しない"""
    for _ in range(2):
        runner.invoke(app, ["install", "--project-dir", str(project_dir)])

    local_settings = project_dir / ".claude" / "settings.local.json"
    data = json.loads(local_settings.read_text())
    mcp_servers = data.get("mcpServers", {})
    assert list(mcp_servers.keys()).count("aidd-kos") == 1, "aidd-kos エントリが重複している"
