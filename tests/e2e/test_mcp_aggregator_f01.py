"""E2E テスト: F-01 LightRAG ドキュメント検索ツール提供 (specs/e2e/5-lightrag-tools.md)"""

from __future__ import annotations

from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# MCP ツールを直接テストするためにサーバーモジュールをインポート
import mcp_server.server as srv


@pytest.fixture()
def lightrag_ok_response():
    """LightRAG がドキュメントを返すモック"""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "response": "OAuth token は 1 時間で失効します",
        "references": [{"file_path": "docs/spec/auth.md"}],
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


@pytest.fixture()
def lightrag_empty_list():
    """空のドキュメントリストを返すモック"""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"statuses": []}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


@pytest.fixture()
def lightrag_doc_list():
    """ドキュメントリストを返すモック"""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "statuses": [{"file_path": "docs/README.md", "status": "indexed"}]
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ── AC-F01-01: lightrag_query がドキュメントと出典パスを返す ──────────────────


@pytest.mark.asyncio
async def test_ac_f01_01_lightrag_query_returns_content_and_path(lightrag_ok_response):
    """AC-F01-01: lightrag_query が関連ドキュメントと出典ファイルパスを返す"""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=lightrag_ok_response)

    with patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client):
        result = await srv.lightrag_query(query="OAuth token")

    assert "OAuth token" in result or "失効" in result
    assert "docs/spec/auth.md" in result


# ── AC-F01-02: mode パラメータ ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f01_02_mode_hybrid_default(lightrag_ok_response):
    """AC-F01-02: mode デフォルトは hybrid"""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=lightrag_ok_response)

    with patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client):
        await srv.lightrag_query(query="test")

    call_kwargs = mock_client.post.call_args
    assert call_kwargs[1]["json"]["mode"] == "hybrid"


@pytest.mark.asyncio
async def test_ac_f01_02_mode_local_accepted(lightrag_ok_response):
    """AC-F01-02: mode=local が受け付けられる"""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=lightrag_ok_response)

    with patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client):
        result = await srv.lightrag_query(query="test", mode="local")

    assert "error" not in result.lower() or "INVALID_MODE" not in result


@pytest.mark.asyncio
async def test_ac_f01_02_invalid_mode_rejected():
    """AC-F01-02: 無効な mode はエラーを返す"""
    result = await srv.lightrag_query(query="test", mode="invalid_mode")
    assert "INVALID_MODE" in result or "error" in result.lower()


# ── AC-F01-03/04: lightrag_list ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f01_03_lightrag_list_returns_paths(lightrag_doc_list):
    """AC-F01-03: lightrag_list がドキュメントのパス一覧を返す"""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=lightrag_doc_list)

    with patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client):
        result = await srv.lightrag_list()

    assert "docs/README.md" in result


@pytest.mark.asyncio
async def test_ac_f01_04_lightrag_list_empty(lightrag_empty_list):
    """AC-F01-04: インデックスが空なら空リスト相当のレスポンスを返す"""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=lightrag_empty_list)

    with patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client):
        result = await srv.lightrag_list()

    assert "なし" in result or result == "" or "0" in result


# ── AC-F01-05/06: エラーハンドリング ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f01_05_lightrag_unavailable_error():
    """AC-F01-05: LightRAG 未起動時に LIGHTRAG_UNAVAILABLE エラーが返る"""
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))

    with patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client):
        result = await srv.lightrag_query(query="test")

    assert "LIGHTRAG_UNAVAILABLE" in result


@pytest.mark.asyncio
async def test_ac_f01_06_error_outputs_to_stderr():
    """AC-F01-06: エラー時に stderr へ出力される"""
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))

    with (
        patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client),
        patch("sys.stderr", new_callable=StringIO) as mock_stderr,
    ):
        await srv.lightrag_query(query="test")
        stderr_output = mock_stderr.getvalue()

    assert "LIGHTRAG_UNAVAILABLE" in stderr_output


@pytest.mark.asyncio
async def test_ac_f01_06_list_error_outputs_to_stderr():
    """AC-F01-06: lightrag_list エラー時も stderr へ LIGHTRAG_UNAVAILABLE が出力される"""
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))

    with (
        patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client),
        patch("sys.stderr", new_callable=StringIO) as mock_stderr,
    ):
        await srv.lightrag_list()
        stderr_output = mock_stderr.getvalue()

    assert "LIGHTRAG_UNAVAILABLE" in stderr_output


# ── TD-01: QUERY_TIMEOUT ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_td_01_query_timeout_error():
    """TD-01: タイムアウト時に QUERY_TIMEOUT エラーが返る"""
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client):
        result = await srv.lightrag_query(query="test")

    assert "QUERY_TIMEOUT" in result
