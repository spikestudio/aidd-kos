"""ユニットテスト: Feature #15 - LIGHTRAG_INDEX_NOT_FOUND と インデックスチェックロジック
(docs/spec/embedded-startup.md Feature F-02) - in-process 対応
"""

from __future__ import annotations

from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import mcp_server.server as srv
from aidd_kos.errors import LIGHTRAG_INDEX_NOT_FOUND

# ── 定数 ─────────────────────────────────────────────────────────────────────


def test_ac_f15_02_unit_lightrag_index_not_found_constant_adr001():
    """AC-F15-02: Unit - LIGHTRAG_INDEX_NOT_FOUND 定数が ADR-001 命名規則に準拠している"""
    assert LIGHTRAG_INDEX_NOT_FOUND == "LIGHTRAG_INDEX_NOT_FOUND"


# ── インデックスチェックロジック ─────────────────────────────────────────────


def _set_mock_rag():
    """_rag モジュール変数に mock を設定してインデックスチェックに到達させる"""
    mock_rag = MagicMock()
    mock_rag.aquery_llm = AsyncMock(
        return_value={"llm_response": {"response": "ok", "references": []}}
    )
    srv._rag = mock_rag
    return mock_rag


def _clear_rag():
    srv._rag = None


@pytest.mark.asyncio
async def test_ac_f15_02_unit_no_lightrag_dir_returns_index_not_found(tmp_path):
    """AC-F15-02: Unit - .lightrag/ が存在しない場合 LIGHTRAG_INDEX_NOT_FOUND を返す"""
    _set_mock_rag()
    try:
        with (
            patch("mcp_server.server.Path") as mock_path_cls,
            patch("sys.stderr", new_callable=StringIO),
        ):
            mock_cwd = MagicMock()
            mock_lightrag_dir = MagicMock()
            mock_lightrag_dir.exists.return_value = False
            mock_cwd.__truediv__ = lambda s, x: mock_lightrag_dir
            mock_path_cls.cwd.return_value = mock_cwd
            result = await srv.lightrag_query(query="テスト")
    finally:
        _clear_rag()
    assert "LIGHTRAG_INDEX_NOT_FOUND" in result


@pytest.mark.asyncio
async def test_ac_f15_02_unit_empty_lightrag_dir_returns_index_not_found(tmp_path, monkeypatch):
    """AC-F15-02: Unit - .lightrag/ が空ディレクトリの場合 LIGHTRAG_INDEX_NOT_FOUND を返す"""
    (tmp_path / ".lightrag").mkdir()
    monkeypatch.chdir(tmp_path)  # Path.cwd() が tmp_path を返すようにする
    _set_mock_rag()
    try:
        with patch("sys.stderr", new_callable=StringIO):
            result = await srv.lightrag_query(query="テスト")
    finally:
        _clear_rag()
    assert "LIGHTRAG_INDEX_NOT_FOUND" in result or "LIGHTRAG_UNAVAILABLE" in result


@pytest.mark.asyncio
async def test_ac_f15_02_unit_lightrag_dir_with_json_skips_index_check(tmp_path):
    """AC-F15-02: Unit - .lightrag/ に .json ファイルがある場合はクエリへ進む"""
    lightrag_dir = tmp_path / ".lightrag"
    lightrag_dir.mkdir()
    (lightrag_dir / "kv_store_full_docs.json").write_text("{}")

    _set_mock_rag()
    try:
        with patch("mcp_server.server.Path") as mock_path_cls:
            mock_cwd = MagicMock()
            mock_lightrag_dir = MagicMock()
            mock_lightrag_dir.exists.return_value = True
            mock_json_file = MagicMock()
            mock_json_file.suffix = ".json"
            mock_json_file.is_file.return_value = True
            mock_lightrag_dir.iterdir.return_value = iter([mock_json_file])
            mock_cwd.__truediv__ = lambda s, x: mock_lightrag_dir
            mock_path_cls.cwd.return_value = mock_cwd
            result = await srv.lightrag_query(query="テスト")
    finally:
        _clear_rag()
    assert "LIGHTRAG_INDEX_NOT_FOUND" not in result


@pytest.mark.asyncio
async def test_ac_f15_02_unit_lightrag_dir_with_graphml_skips_index_check(tmp_path):
    """AC-F15-02: Unit - .lightrag/ に .graphml ファイルがある場合はクエリへ進む"""
    lightrag_dir = tmp_path / ".lightrag"
    lightrag_dir.mkdir()
    (lightrag_dir / "graph_chunk_entity_relation.graphml").write_text("<graphml/>")

    _set_mock_rag()
    try:
        with patch("mcp_server.server.Path") as mock_path_cls:
            mock_cwd = MagicMock()
            mock_lightrag_dir = MagicMock()
            mock_lightrag_dir.exists.return_value = True
            mock_graphml_file = MagicMock()
            mock_graphml_file.suffix = ".graphml"
            mock_graphml_file.is_file.return_value = True
            mock_lightrag_dir.iterdir.return_value = iter([mock_graphml_file])
            mock_cwd.__truediv__ = lambda s, x: mock_lightrag_dir
            mock_path_cls.cwd.return_value = mock_cwd
            result = await srv.lightrag_query(query="テスト")
    finally:
        _clear_rag()
    assert "LIGHTRAG_INDEX_NOT_FOUND" not in result


@pytest.mark.asyncio
async def test_ac_f15_02_unit_stderr_output_on_index_not_found(tmp_path):
    """AC-F15-02: Unit - インデックス未構築時に stderr へ LIGHTRAG_INDEX_NOT_FOUND が出力される"""
    _set_mock_rag()
    try:
        with (
            patch("mcp_server.server.Path") as mock_path_cls,
            patch("sys.stderr", new_callable=StringIO) as mock_stderr,
        ):
            mock_cwd = MagicMock()
            mock_lightrag_dir = MagicMock()
            mock_lightrag_dir.exists.return_value = False
            mock_cwd.__truediv__ = lambda s, x: mock_lightrag_dir
            mock_path_cls.cwd.return_value = mock_cwd
            await srv.lightrag_query(query="テスト")
    finally:
        _clear_rag()
    assert "LIGHTRAG_INDEX_NOT_FOUND" in mock_stderr.getvalue()
