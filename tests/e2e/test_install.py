"""E2E テスト: F-01 install コマンド (specs/e2e/8-install.md)"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from aidd_kos.cli import app
from typer.testing import CliRunner

runner = CliRunner(mix_stderr=False)


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    """テスト用一時プロジェクトディレクトリ"""
    return tmp_path


@pytest.fixture()
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """~/.claude/settings.json 書き込みを一時ディレクトリに向ける"""
    home = tmp_path / "fake_home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture()
def env_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPENAI_API_KEY を設定"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")


@pytest.fixture()
def env_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPENAI_API_KEY を未設定にする"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# ── AC-F01-01: 全自動実行 ─────────────────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_01_e2e_install_full_auto(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-01: E2E - install コマンドが全ステップを自動実行する"""
    result = runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert result.exit_code == 0
    assert (project_dir / ".lightrag").exists()
    assert (project_dir / ".codegraph").exists()


# ── AC-F01-02: 完了メッセージ ─────────────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_02_e2e_completion_message(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-02: E2E - 完了後に「Claude Code を再起動してください」が表示される"""
    result = runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert "Claude Code を再起動してください" in result.output


# ── AC-F01-03: MCP エントリ追加 ───────────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_03_e2e_mcp_entry_added(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-03: E2E - ~/.claude/settings.json に aidd-kos エントリが追加される"""
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    claude_settings = fake_home / ".claude" / "settings.json"
    assert claude_settings.exists()
    data = json.loads(claude_settings.read_text())
    assert "aidd-kos" in data.get("mcpServers", {})


# ── AC-F01-04: ストレージ作成 ─────────────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_04_e2e_storage_created(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-04: E2E - .lightrag/ と .codegraph/ が対象プロジェクト内に作成される"""
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert (project_dir / ".lightrag").is_dir()
    assert (project_dir / ".codegraph").is_dir()


# ── AC-F01-05: MISE_NOT_FOUND エラー ─────────────────────────────────────────


def test_ac_f01_05_e2e_mise_not_found_error(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch, env_with_key: None
) -> None:
    """AC-F01-05: E2E - mise 未インストール時に MISE_NOT_FOUND エラーが stderr に出力される"""
    # PATH から mise を除外して存在しない環境をシミュレート
    monkeypatch.setenv("PATH", "/nonexistent_path")
    result = runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert result.exit_code == 1
    assert "MISE_NOT_FOUND" in result.stderr


# ── AC-F01-06: OPENAI_API_KEY_MISSING エラー ─────────────────────────────────


def test_ac_f01_06_e2e_openai_key_missing_error(project_dir: Path, env_without_key: None) -> None:
    """AC-F01-06: E2E - OPENAI_API_KEY 未設定時に OPENAI_API_KEY_MISSING エラーが stderr に出力される"""
    result = runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert result.exit_code == 1
    assert "OPENAI_API_KEY_MISSING" in result.stderr


# ── AC-F01-07: .gitignore に .lightrag/ 追記 ──────────────────────────────────


@pytest.mark.integration
def test_ac_f01_07_e2e_gitignore_lightrag(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-07: E2E - install 後に .gitignore に .lightrag/ が追記される"""
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    gitignore = project_dir / ".gitignore"
    assert gitignore.exists()
    assert ".lightrag/" in gitignore.read_text()


# ── AC-F01-08: .gitignore に .codegraph/ 追記 ─────────────────────────────────


@pytest.mark.integration
def test_ac_f01_08_e2e_gitignore_codegraph(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-08: E2E - install 後に .gitignore に .codegraph/ が追記される"""
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    gitignore = project_dir / ".gitignore"
    assert ".codegraph/" in gitignore.read_text()


# ── AC-F01-09: .gitignore 重複追記なし ────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_09_e2e_gitignore_no_duplicate(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-09: E2E - .gitignore に .lightrag/ がすでにある場合は重複追記しない"""
    gitignore = project_dir / ".gitignore"
    gitignore.write_text(".lightrag/\n")
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    content = gitignore.read_text()
    assert content.count(".lightrag/") == 1


# ── AC-F01-10: 再 install 時 .lightrag/ 保持 ──────────────────────────────────


@pytest.mark.integration
def test_ac_f01_10_e2e_reinstall_preserves_lightrag(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-10: E2E - 再 install 時に既存の .lightrag/ が削除されない"""
    dummy = project_dir / ".lightrag" / "test.txt"
    dummy.parent.mkdir(parents=True)
    dummy.write_text("dummy")
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert dummy.exists()


# ── AC-F01-11: 再 install 時インデックス読み取り可能 ──────────────────────────


@pytest.mark.integration
def test_ac_f01_11_e2e_reinstall_index_readable(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-11: E2E - 再 install 後も .lightrag/ 配下が読み取り可能な状態を維持する"""
    dummy = project_dir / ".lightrag" / "index.bin"
    dummy.parent.mkdir(parents=True)
    dummy.write_bytes(b"\x00\x01\x02")
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert os.access(dummy, os.R_OK)


# ── AC-F01-12: 他 MCP エントリ保護 ───────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_12_e2e_other_mcp_entries_preserved(
    project_dir: Path, fake_home: Path, env_with_key: None
) -> None:
    """AC-F01-12: E2E - 他の MCP エントリが上書きされない"""
    claude_dir = fake_home / ".claude"
    claude_dir.mkdir(parents=True)
    settings = claude_dir / "settings.json"
    settings.write_text(
        json.dumps({"mcpServers": {"other-tool": {"command": "npx", "args": ["other"]}}})
    )
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    data = json.loads(settings.read_text())
    assert "other-tool" in data["mcpServers"]
    assert data["mcpServers"]["other-tool"]["command"] == "npx"
