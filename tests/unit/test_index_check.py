"""ユニットテスト: Feature #15 - LIGHTRAG_INDEX_NOT_FOUND と インデックスチェックロジック
(docs/spec/embedded-startup.md Feature F-02)
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


@pytest.mark.asyncio
async def test_ac_f15_02_unit_no_lightrag_dir_returns_index_not_found(tmp_path):
    """AC-F15-02: Unit - .lightrag/ が存在しない場合 LIGHTRAG_INDEX_NOT_FOUND を返す"""
    with (
        patch("mcp_server.server.Path") as mock_path_cls,
        patch("sys.stderr", new_callable=StringIO),
    ):
        mock_path_cls.cwd.return_value = tmp_path
        result = await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_INDEX_NOT_FOUND" in result


@pytest.mark.asyncio
async def test_ac_f15_02_unit_empty_lightrag_dir_returns_index_not_found(tmp_path):
    """AC-F15-02: Unit - .lightrag/ が空ディレクトリの場合 LIGHTRAG_INDEX_NOT_FOUND を返す"""
    (tmp_path / ".lightrag").mkdir()

    with (
        patch("mcp_server.server.Path") as mock_path_cls,
        patch("sys.stderr", new_callable=StringIO),
    ):
        mock_path_cls.cwd.return_value = tmp_path
        result = await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_INDEX_NOT_FOUND" in result


@pytest.mark.asyncio
async def test_ac_f15_02_unit_lightrag_dir_with_json_skips_index_check(tmp_path):
    """AC-F15-02: Unit - .lightrag/ に .json ファイルがある場合はインデックスチェックをスキップして HTTP クエリへ進む"""
    lightrag_dir = tmp_path / ".lightrag"
    lightrag_dir.mkdir()
    (lightrag_dir / "kv_store_full_docs.json").write_text("{}")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "テスト結果", "references": []}
    mock_resp.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with (
        patch("mcp_server.server.Path") as mock_path_cls,
        patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_path_cls.cwd.return_value = tmp_path
        result = await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_INDEX_NOT_FOUND" not in result
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_ac_f15_02_unit_lightrag_dir_with_graphml_skips_index_check(tmp_path):
    """AC-F15-02: Unit - .lightrag/ に .graphml ファイルがある場合はインデックスチェックをスキップする"""
    lightrag_dir = tmp_path / ".lightrag"
    lightrag_dir.mkdir()
    (lightrag_dir / "graph_chunk_entity_relation.graphml").write_text("<graphml/>")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "テスト結果", "references": []}
    mock_resp.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with (
        patch("mcp_server.server.Path") as mock_path_cls,
        patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_path_cls.cwd.return_value = tmp_path
        result = await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_INDEX_NOT_FOUND" not in result


@pytest.mark.asyncio
async def test_ac_f15_02_unit_stderr_output_on_index_not_found(tmp_path):
    """AC-F15-02: Unit - インデックス未構築時に stderr へ LIGHTRAG_INDEX_NOT_FOUND が出力される"""
    with (
        patch("mcp_server.server.Path") as mock_path_cls,
        patch("sys.stderr", new_callable=StringIO) as mock_stderr,
    ):
        mock_path_cls.cwd.return_value = tmp_path
        await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_INDEX_NOT_FOUND" in mock_stderr.getvalue()
