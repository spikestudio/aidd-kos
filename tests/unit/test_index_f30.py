"""ユニットテスト: Feature #30 削除ファイルのインデックス除去 - in-process 対応"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from aidd_kos.index import IndexOrchestrator

_PAST_UTC = "2020-01-01T00:00:00"


def _make_doc_status(file_path: str, doc_id: str):
    mock_status = MagicMock()
    mock_status.file_path = file_path
    mock_status.updated_at = _PAST_UTC
    return mock_status


def _make_mock_rag(docs=None):
    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    docs_dict = {}
    if docs:
        docs_dict = {d["id"]: _make_doc_status(d["file_path"], d["id"]) for d in docs}
    mock_rag.get_docs_by_status = AsyncMock(return_value=docs_dict)
    mock_rag.ainsert = AsyncMock()
    mock_rag.adelete_by_doc_id = AsyncMock()
    return mock_rag


# ── _detect_deleted ──────────────────────────────────────────────────────────


def test_ac_f30_01_unit_detect_deleted_returns_doc_id(tmp_path: Path) -> None:
    """AC-F30-01: Unit - filesystem にないファイルが deleted に検出される"""
    indexed = {"sample.md": {"id": "doc_sample", "updated_at": _PAST_UTC}}
    idx = IndexOrchestrator(project_dir=tmp_path)
    deleted = idx._detect_deleted([], indexed)
    assert "sample.md" in deleted
    assert deleted["sample.md"] == "doc_sample"


def test_ac_f30_01_unit_detect_no_deleted_when_file_exists(tmp_path: Path) -> None:
    """AC-F30-01: Unit - filesystem にあるファイルは deleted に含まれない"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    indexed = {"doc.md": {"id": "doc_001", "updated_at": _PAST_UTC}}
    idx = IndexOrchestrator(project_dir=tmp_path)
    deleted = idx._detect_deleted([f], indexed)
    assert deleted == {}


# ── _delete_docs ─────────────────────────────────────────────────────────────


def test_ac_f30_02_unit_delete_docs_calls_adelete(tmp_path: Path) -> None:
    """AC-F30-02: Unit - _delete_docs が adelete_by_doc_id を正しい doc_id で呼び出す"""
    idx = IndexOrchestrator(project_dir=tmp_path)
    mock_rag = _make_mock_rag()
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        count = idx._delete_docs({"sample.md": "doc_sample"})
    assert count == 1
    mock_rag.adelete_by_doc_id.assert_called_once()


def test_ac_f30_01_unit_delete_docs_skips_when_empty(tmp_path: Path) -> None:
    """AC-F30-01: Unit - 削除対象がゼロ件のとき adelete_by_doc_id を呼ばずに 0 を返す"""
    idx = IndexOrchestrator(project_dir=tmp_path)
    mock_rag = _make_mock_rag()
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        count = idx._delete_docs({})
    assert count == 0
    mock_rag.adelete_by_doc_id.assert_not_called()


# ── run() 統合 ───────────────────────────────────────────────────────────────


def test_ac_f30_01_unit_run_returns_deleted_count(tmp_path: Path) -> None:
    """AC-F30-01: Unit - run() が deleted_count を返す"""
    idx = IndexOrchestrator(project_dir=tmp_path)
    mock_rag = _make_mock_rag([{"id": "doc_gone", "file_path": "gone.md"}])
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = idx.run()
    assert "deleted_count" in result
    assert result["deleted_count"] == 1


def test_ac_f30_01_unit_run_deleted_count_zero_when_no_deletions(tmp_path: Path) -> None:
    """AC-F30-01: Unit - 削除なしのとき deleted_count は 0"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)
    mock_rag = _make_mock_rag([])
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = idx.run()
    assert result["deleted_count"] == 0
