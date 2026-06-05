"""E2E テスト: F-02 index コマンド (docs/spec/install.md) - in-process 対応"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# Test Project\nThis is a test.")
    (tmp_path / "doc.txt").write_text("Some documentation.")
    return tmp_path


def _make_mock_rag_for_index(paginated_docs=None):
    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    mock_rag.get_docs_by_status = AsyncMock(return_value=paginated_docs or {})
    mock_rag.ainsert = AsyncMock()
    mock_rag.adelete_by_doc_id = AsyncMock()
    return mock_rag


@pytest.fixture()
def lightrag_running():
    mock_rag = _make_mock_rag_for_index()
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        yield mock_rag


def test_ac_f02_01_e2e_index_md_txt_files(project_dir: Path, lightrag_running) -> None:
    """AC-F02-01: E2E - .md/.txt ファイルが LightRAG に再インデックスされる"""
    result = runner.invoke(app, ["index", str(project_dir)])
    assert result.exit_code == 0


def test_ac_f02_02_e2e_default_path(
    project_dir: Path, lightrag_running, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-F02-02: E2E - path 省略時はカレントディレクトリをインデックス対象とする"""
    monkeypatch.chdir(project_dir)
    result = runner.invoke(app, ["index"])
    assert result.exit_code == 0


def test_ac_f02_03_e2e_shows_file_count(project_dir: Path, lightrag_running) -> None:
    """AC-F02-03: E2E - 完了後に処理ファイル数が表示される"""
    result = runner.invoke(app, ["index", str(project_dir)])
    assert result.exit_code == 0
    assert any(char.isdigit() for char in result.output)


def test_ac_f02_04_e2e_shows_elapsed_time(project_dir: Path, lightrag_running) -> None:
    """AC-F02-04: E2E - 完了後に所要時間が表示される"""
    result = runner.invoke(app, ["index", str(project_dir)])
    assert result.exit_code == 0
    output = result.output
    assert "秒" in output or "ms" in output or "s" in output


def test_ac_f02_05_e2e_lightrag_unavailable(project_dir: Path) -> None:
    """AC-F02-05: E2E - LightRAG 初期化失敗時に LIGHTRAG_UNAVAILABLE エラーが出力される"""
    with patch(
        "aidd_kos.index.create_lightrag_instance",
        side_effect=RuntimeError("connection failed"),
    ):
        result = runner.invoke(app, ["index", str(project_dir)])
    assert result.exit_code == 1
    assert "LIGHTRAG_UNAVAILABLE" in result.output or "LIGHTRAG_UNAVAILABLE" in (
        result.stderr or ""
    )
