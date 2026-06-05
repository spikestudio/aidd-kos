"""E2E テスト: Feature #31 全件再構築 - in-process 対応"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()


def _make_mock_rag():
    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    mock_rag.get_docs_by_status = AsyncMock(return_value={})
    mock_rag.ainsert = AsyncMock()
    mock_rag.adelete_by_doc_id = AsyncMock()
    return mock_rag


# ── AC-F31-01: --full で全件再構築モード出力 ──────────────────────────────────


def test_ac_f31_01_e2e_full_flag_shows_rebuild_mode(tmp_path: Path) -> None:
    """AC-F31-01: E2E - --full 実行で「全件再構築モード: N 件」が stdout に表示される"""
    for name in ("a.md", "b.txt"):
        (tmp_path / name).write_text(f"content {name}")

    with patch("aidd_kos.index.create_lightrag_instance", return_value=_make_mock_rag()):
        result = runner.invoke(app, ["index", "--full", str(tmp_path)])

    assert result.exit_code == 0
    assert "全件再構築モード" in result.output
    assert "2" in result.output


# ── AC-F31-02: --full でスキップなし ─────────────────────────────────────────


def test_ac_f31_02_e2e_full_flag_no_skip(tmp_path: Path) -> None:
    """AC-F31-02: E2E - --full 実行でスキップが 0 件"""
    (tmp_path / "doc.md").write_text("content")

    with patch("aidd_kos.index.create_lightrag_instance", return_value=_make_mock_rag()):
        result = runner.invoke(app, ["index", "--full", str(tmp_path)])

    assert result.exit_code == 0
    assert "スキップ" not in result.output
