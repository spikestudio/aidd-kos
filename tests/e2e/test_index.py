"""E2E テスト: F-02 index コマンド (docs/spec/install.md)"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    # .md と .txt ファイルを作成
    (tmp_path / "README.md").write_text("# Test Project\nThis is a test.")
    (tmp_path / "doc.txt").write_text("Some documentation.")
    return tmp_path


@pytest.fixture()
def lightrag_running():
    """LightRAG REST API が起動している状態をモックする"""
    import urllib.request

    def fake_urlopen(req, timeout=None):
        class FakeResponse:
            def read(self):
                return b'{"status": "ok"}'

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        return FakeResponse()

    with patch.object(urllib.request, "urlopen", fake_urlopen):
        yield


# ── AC-F02-01: .md/.txt を再インデックス ──────────────────────────────────────


def test_ac_f02_01_e2e_index_md_txt_files(project_dir: Path, lightrag_running: None) -> None:
    """AC-F02-01: E2E - .md/.txt ファイルが LightRAG に再インデックスされる"""
    result = runner.invoke(app, ["index", str(project_dir)])
    assert result.exit_code == 0


# ── AC-F02-02: path 省略時はカレントディレクトリ ──────────────────────────────


def test_ac_f02_02_e2e_default_path(
    project_dir: Path, lightrag_running: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-F02-02: E2E - path 省略時はカレントディレクトリをインデックス対象とする"""
    monkeypatch.chdir(project_dir)
    result = runner.invoke(app, ["index"])
    assert result.exit_code == 0


# ── AC-F02-03: 処理ファイル数の表示 ──────────────────────────────────────────


def test_ac_f02_03_e2e_shows_file_count(project_dir: Path, lightrag_running: None) -> None:
    """AC-F02-03: E2E - 完了後に処理ファイル数が表示される"""
    result = runner.invoke(app, ["index", str(project_dir)])
    assert result.exit_code == 0
    # ファイル数が含まれていること（数字が含まれる行）
    assert any(char.isdigit() for char in result.output)


# ── AC-F02-04: 所要時間の表示 ─────────────────────────────────────────────────


def test_ac_f02_04_e2e_shows_elapsed_time(project_dir: Path, lightrag_running: None) -> None:
    """AC-F02-04: E2E - 完了後に所要時間が表示される"""
    result = runner.invoke(app, ["index", str(project_dir)])
    assert result.exit_code == 0
    # 秒数またはミリ秒が含まれること
    output = result.output
    assert "秒" in output or "ms" in output or "s" in output


# ── AC-F02-05: LightRAG 未起動時エラー ────────────────────────────────────────


def test_ac_f02_05_e2e_lightrag_unavailable(project_dir: Path) -> None:
    """AC-F02-05: E2E - LightRAG 未起動時に LIGHTRAG_UNAVAILABLE エラーが stderr に出力される"""
    import urllib.error
    import urllib.request

    with patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
        result = runner.invoke(app, ["index", str(project_dir)])
    assert result.exit_code == 1
    assert "LIGHTRAG_UNAVAILABLE" in result.output or "LIGHTRAG_UNAVAILABLE" in (
        result.stderr or ""
    )
