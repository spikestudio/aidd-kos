"""E2E テスト: Feature #30 削除ファイルのインデックス除去 - in-process 対応"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()

_PAST_UTC = "2020-01-01T00:00:00"


def _make_doc_status(file_path: str, doc_id: str):
    mock_status = MagicMock()
    mock_status.file_path = file_path
    mock_status.updated_at = _PAST_UTC
    return mock_status


def _make_rag_with_docs(docs: list[dict]):
    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    docs_dict = {d["id"]: _make_doc_status(d["file_path"], d["id"]) for d in docs}
    mock_rag.get_docs_by_status = AsyncMock(return_value=docs_dict)
    mock_rag.ainsert = AsyncMock()
    mock_rag.adelete_by_doc_id = AsyncMock()
    return mock_rag


# ── AC-F30-01: 削除ファイルが stdout に表示される ──────────────────────────────


def test_ac_f30_01_e2e_deleted_file_shows_in_output(tmp_path: Path) -> None:
    """AC-F30-01: E2E - indexed 済みファイルが filesystem にないとき「削除 1 件」が stdout に表示される"""
    mock_rag = _make_rag_with_docs([{"id": "doc_sample", "file_path": "sample.md"}])

    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "削除 1" in result.output


# ── AC-F30-02: 正しい doc_id で削除 API が呼ばれる ─────────────────────────────


def test_ac_f30_02_e2e_delete_api_called_with_correct_doc_id(tmp_path: Path) -> None:
    """AC-F30-02: E2E - adelete_by_doc_id が "doc_sample" で呼び出される"""
    mock_rag = _make_rag_with_docs([{"id": "doc_sample", "file_path": "sample.md"}])

    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    # adelete_by_doc_id が doc_sample で呼ばれたことを確認
    calls = [str(c) for c in mock_rag.adelete_by_doc_id.call_args_list]
    assert any("doc_sample" in c for c in calls)
