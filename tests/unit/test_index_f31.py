"""ユニットテスト: Feature #31 全件再構築 - in-process 対応"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from aidd_kos.index import IndexOrchestrator


def _make_mock_rag():
    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    mock_rag.get_docs_by_status = AsyncMock(return_value={})
    mock_rag.ainsert = AsyncMock()
    mock_rag.adelete_by_doc_id = AsyncMock()
    return mock_rag


def test_ac_f31_01_unit_run_full_returns_full_count(tmp_path: Path) -> None:
    """AC-F31-01: Unit - run(full=True) が full_count を返す"""
    for name in ("a.md", "b.txt"):
        (tmp_path / name).write_text(f"content {name}")
    idx = IndexOrchestrator(project_dir=tmp_path)
    with patch("aidd_kos.index.create_lightrag_instance", return_value=_make_mock_rag()):
        result = idx.run(full=True)
    assert "full_count" in result
    assert result["full_count"] == 2


def test_ac_f31_02_unit_run_full_skip_count_zero(tmp_path: Path) -> None:
    """AC-F31-02: Unit - run(full=True) のとき skip_count は 0"""
    (tmp_path / "doc.md").write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)
    with patch("aidd_kos.index.create_lightrag_instance", return_value=_make_mock_rag()):
        result = idx.run(full=True)
    assert result["skip_count"] == 0


def test_ac_f31_02_unit_run_full_clears_lightrag_dir(tmp_path: Path) -> None:
    """AC-F31-02: Unit - run(full=True) では .lightrag/ を再作成する"""
    lightrag_dir = tmp_path / ".lightrag"
    lightrag_dir.mkdir()
    (lightrag_dir / "old_data.json").write_text("{}")
    (tmp_path / "doc.md").write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)
    with patch("aidd_kos.index.create_lightrag_instance", return_value=_make_mock_rag()):
        idx.run(full=True)
    # .lightrag/ が再作成されていること（old_data.json が削除されている）
    assert lightrag_dir.exists()
    assert not (lightrag_dir / "old_data.json").exists()


def test_ac_f31_01_unit_run_default_still_uses_diff(tmp_path: Path) -> None:
    """AC-F31-01: Unit - run()（full=False）では差分モードが維持される"""
    (tmp_path / "doc.md").write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)
    mock_rag = _make_mock_rag()
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        idx.run(full=False)
    # 差分モードでは get_docs_by_status が呼ばれる
    mock_rag.get_docs_by_status.assert_called()
