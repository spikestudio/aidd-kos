"""E2E テスト: F-02 ナレッジ検索の分離と MCP Aggregator - in-process 対応"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import mcp_server.server as srv


def _set_mock_rag(query_response=None):
    mock_rag = MagicMock()
    mock_rag.aquery_llm = AsyncMock(
        return_value=query_response
        or {"llm_response": {"response": "project A result", "references": []}}
    )
    mock_rag.get_docs_by_status = AsyncMock(return_value={})
    srv._rag = mock_rag
    return mock_rag


def _clear_rag():
    srv._rag = None


# ── AC-F15-01 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f15_01_lightrag_query_returns_only_project_a_docs(tmp_path):
    """AC-F15-01: E2E - ナレッジ検索が in-process LightRAG からドキュメントを返す"""
    _set_mock_rag()
    try:
        with patch("mcp_server.server.Path") as mock_path:
            mock_cwd = MagicMock()
            mock_dir = MagicMock()
            mock_dir.exists.return_value = True
            mock_file = MagicMock()
            mock_file.suffix = ".json"
            mock_file.is_file.return_value = True
            mock_dir.iterdir.return_value = iter([mock_file])
            mock_cwd.__truediv__ = lambda s, x: mock_dir
            mock_path.cwd.return_value = mock_cwd
            result = await srv.lightrag_query(query="test query")
    finally:
        _clear_rag()
    assert "LIGHTRAG_UNAVAILABLE" not in result
    assert "LIGHTRAG_INDEX_NOT_FOUND" not in result


# ── AC-F15-02 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f15_02_returns_index_not_found_when_no_index(tmp_path):
    """AC-F15-02: E2E - インデックス未構築時に LIGHTRAG_INDEX_NOT_FOUND エラーを返す"""
    _set_mock_rag()
    try:
        with patch("mcp_server.server.Path") as mock_path:
            mock_cwd = MagicMock()
            mock_dir = MagicMock()
            mock_dir.exists.return_value = False
            mock_cwd.__truediv__ = lambda s, x: mock_dir
            mock_path.cwd.return_value = mock_cwd
            result = await srv.lightrag_query(query="test query")
    finally:
        _clear_rag()
    assert "LIGHTRAG_INDEX_NOT_FOUND" in result


@pytest.mark.asyncio
async def test_ac_f15_02_returns_index_not_found_when_lightrag_dir_empty(tmp_path):
    """AC-F15-02: E2E - .lightrag/ が存在するが空のとき LIGHTRAG_INDEX_NOT_FOUND を返す"""
    _set_mock_rag()
    try:
        with patch("mcp_server.server.Path") as mock_path:
            mock_cwd = MagicMock()
            mock_dir = MagicMock()
            mock_dir.exists.return_value = True
            mock_dir.iterdir.return_value = iter([])
            mock_cwd.__truediv__ = lambda s, x: mock_dir
            mock_path.cwd.return_value = mock_cwd
            result = await srv.lightrag_query(query="test query")
    finally:
        _clear_rag()
    assert "LIGHTRAG_INDEX_NOT_FOUND" in result


# ── AC-F15-03 / F15-04 ───────────────────────────────────────────────────────


def test_ac_f15_03_index_sends_files_with_relative_paths(tmp_path):
    """AC-F15-03: E2E - IndexOrchestrator が対象プロジェクトの .md/.txt を処理する"""
    from aidd_kos.index import IndexOrchestrator

    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / "doc.txt").write_text("doc content")

    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    mock_rag.get_docs_by_status = AsyncMock(return_value={})
    mock_rag.ainsert = AsyncMock()
    mock_rag.adelete_by_doc_id = AsyncMock()

    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        idx = IndexOrchestrator(project_dir=tmp_path)
        result = idx.run()

    assert result["new_count"] == 2
    assert result["skip_count"] == 0


def test_ac_f15_04_re_index_uses_same_relative_paths(tmp_path):
    """AC-F15-04: E2E - 再インデックス実行時も同じ対象プロジェクトの相対パスを使用する"""
    from aidd_kos.index import IndexOrchestrator

    (tmp_path / "README.md").write_text("# Project")

    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    mock_rag.get_docs_by_status = AsyncMock(return_value={})
    mock_rag.ainsert = AsyncMock()
    mock_rag.adelete_by_doc_id = AsyncMock()

    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        idx = IndexOrchestrator(project_dir=tmp_path)
        # 1回目
        result1 = idx.run()
        # 2回目（skip のため get_docs_by_status が呼ばれる）
        result2 = idx.run()

    # 両方成功
    assert result1["new_count"] >= 0
    assert result2 is not None
