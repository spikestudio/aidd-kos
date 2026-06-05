"""E2E テスト: F-01 install コマンド (specs/e2e/8-install.md)"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()


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


@pytest.fixture()
def mock_subprocesses(monkeypatch: pytest.MonkeyPatch):
    """mise install / uv sync / codegraph init の subprocess 呼び出しをモック化する。
    integration テストが実際の外部ツール（mise/npx/LightRAG）なしに実行できるようにする。"""
    from unittest.mock import MagicMock, patch

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"initialized": true}'

    # LightRAG ヘルスチェックは即座に OK を返す

    def fake_urlopen(req, timeout=None):
        resp = MagicMock()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        resp.read.return_value = b'{"status": "ok"}'
        return resp

    def fake_subprocess_run(cmd, **kwargs):
        """codegraph init/index 呼び出し時に .codegraph/ を作成するモック"""
        is_codegraph = any("codegraph" in str(part) for part in cmd)
        is_init_or_index = "init" in cmd or "index" in cmd
        if is_codegraph and is_init_or_index:
            for part in cmd:
                s = str(part)
                if s not in ("npx", "@colbymchenry/codegraph", "init", "index"):
                    from pathlib import Path

                    target = Path(s)
                    target.mkdir(exist_ok=True)
                    (target / ".codegraph").mkdir(exist_ok=True)
                    break
        return mock_result

    with (
        patch("aidd_kos.install.subprocess.run", side_effect=fake_subprocess_run),
        patch("aidd_kos.install.subprocess.Popen"),
        patch("aidd_kos.install.urllib.request.urlopen", fake_urlopen),
        # Feature #41: index.py は in-process LightRAG を使用するため urllib patch 不要
        # start_lightrag_and_index をモック化してインデックス構築をスキップ
        patch("aidd_kos.install.InstallOrchestrator.start_lightrag_and_index"),
    ):
        yield


# ── AC-F01-01: 全自動実行 ─────────────────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_01_e2e_install_full_auto(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
) -> None:
    """AC-F01-01: E2E - install コマンドが全ステップを自動実行する"""
    result = runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert result.exit_code == 0
    assert (project_dir / ".lightrag").exists()
    assert (project_dir / ".codegraph").exists()


# ── AC-F01-02: 完了メッセージ ─────────────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_02_e2e_completion_message(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
) -> None:
    """AC-F01-02: E2E - 完了後に「Claude Code を再起動してください」が表示される"""
    result = runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    assert "Claude Code を再起動してください" in result.output


# ── AC-F01-03: MCP エントリ追加 ───────────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_03_e2e_mcp_entry_added(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
) -> None:
    """AC-F01-03: E2E - --global で ~/.claude/settings.json に aidd-kos エントリが追加される
    (Feature #40: デフォルトは .claude/settings.local.json に変更された)
    """
    runner.invoke(app, ["install", "--project-dir", str(project_dir), "--global"])
    claude_settings = fake_home / ".claude" / "settings.json"
    assert claude_settings.exists()
    data = json.loads(claude_settings.read_text())
    assert "aidd-kos" in data.get("mcpServers", {})


# ── AC-F01-04: ストレージ作成 ─────────────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_04_e2e_storage_created(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
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
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
) -> None:
    """AC-F01-07: E2E - install 後に .gitignore に .lightrag/ が追記される"""
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    gitignore = project_dir / ".gitignore"
    assert gitignore.exists()
    assert ".lightrag/" in gitignore.read_text()


# ── AC-F01-08: .gitignore に .codegraph/ 追記 ─────────────────────────────────


@pytest.mark.integration
def test_ac_f01_08_e2e_gitignore_codegraph(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
) -> None:
    """AC-F01-08: E2E - install 後に .gitignore に .codegraph/ が追記される"""
    runner.invoke(app, ["install", "--project-dir", str(project_dir)])
    gitignore = project_dir / ".gitignore"
    assert ".codegraph/" in gitignore.read_text()


# ── AC-F01-09: .gitignore 重複追記なし ────────────────────────────────────────


@pytest.mark.integration
def test_ac_f01_09_e2e_gitignore_no_duplicate(
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
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
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
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
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
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
    project_dir: Path, fake_home: Path, env_with_key: None, mock_subprocesses: None
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
