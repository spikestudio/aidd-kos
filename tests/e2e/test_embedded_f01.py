"""E2E テスト: F-01 ナレッジ検索が MCP サーバー起動直後から利用可能になる
(specs/e2e/14-embedded-f01.md)
Feature #41 以降: LightRAG in-process 化対応
"""

from __future__ import annotations

import socket
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import mcp_server.server as srv


@pytest.fixture(autouse=True)
def _set_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-for-embedded-tests")


def _make_mock_rag():
    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    mock_rag.aquery_llm = AsyncMock(
        return_value={"llm_response": {"response": "テスト結果", "references": []}}
    )
    mock_rag.get_docs_by_status = AsyncMock(return_value={})
    return mock_rag


@pytest.mark.asyncio
async def test_ac_f14_01_lightrag_query_available_immediately_after_startup():
    """AC-F14-01: E2E - MCP Server 起動後すぐに lightrag_query が LIGHTRAG_UNAVAILABLE なしに応答する"""
    mock_rag = _make_mock_rag()
    mock_lightrag_dir = MagicMock()
    mock_lightrag_dir.exists.return_value = True
    mock_json_file = MagicMock()
    mock_json_file.suffix = ".json"
    mock_lightrag_dir.iterdir.return_value = iter([mock_json_file])
    mock_lightrag_dir.mkdir = MagicMock()

    with (
        patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag),
        patch("mcp_server.server.Path") as mock_path_cls,
    ):
        mock_cwd = MagicMock()
        mock_cwd.__truediv__ = lambda s, x: mock_lightrag_dir
        mock_path_cls.cwd.return_value = mock_cwd
        async with srv._lifespan(None):
            result = await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_UNAVAILABLE" not in result


@pytest.mark.asyncio
@pytest.mark.skip(reason="テスト環境で LightRAG が稼働中の場合があるため手動確認")
async def test_ac_f14_02_startup_completes_without_port_binding():
    """AC-F14-02: E2E - 起動が外部ポートなしで完了する（in-process）"""
    mock_rag = _make_mock_rag()
    port_9621_used = False
    with patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag):
        async with srv._lifespan(None):
            try:
                with socket.create_connection(("127.0.0.1", 9621), timeout=0.1):
                    port_9621_used = True
            except (ConnectionRefusedError, OSError):
                port_9621_used = False
    assert not port_9621_used


@pytest.mark.asyncio
async def test_ac_f14_03a_startup_fails_on_immediate_process_exit():
    """AC-F14-03a: E2E - LightRAG 初期化失敗時に RuntimeError が送出される"""
    with (
        patch(
            "mcp_server.server.create_lightrag_instance",
            side_effect=Exception("init error"),
        ),
        pytest.raises(RuntimeError, match="LIGHTRAG_STARTUP_FAILED"),
    ):
        async with srv._lifespan(None):
            pass


@pytest.mark.asyncio
async def test_ac_f14_03b_startup_fails_on_30s_timeout(monkeypatch):
    """AC-F14-03b: E2E - OPENAI_API_KEY 未設定時に RuntimeError が送出される"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY_MISSING"):
        async with srv._lifespan(None):
            pass


@pytest.mark.asyncio
async def test_ac_f14_04a_proc_terminate_called_on_server_stop():
    """AC-F14-04a: E2E - MCP Server 停止時に finalize_storages が呼ばれる"""
    mock_rag = _make_mock_rag()
    with patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag):
        async with srv._lifespan(None):
            pass
    mock_rag.finalize_storages.assert_called_once()


@pytest.mark.asyncio
async def test_ac_f14_04b_query_after_stop_returns_unavailable():
    """AC-F14-04b: E2E - MCP Server 停止後に lightrag_query を呼ぶと LIGHTRAG_UNAVAILABLE が返る"""
    mock_rag = _make_mock_rag()
    with patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag):
        async with srv._lifespan(None):
            pass
    result = await srv.lightrag_query(query="停止後のクエリ")
    assert "LIGHTRAG_UNAVAILABLE" in result
