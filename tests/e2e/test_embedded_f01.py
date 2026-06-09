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
async def test_ac_f41_01_lightrag_query_available_immediately_after_startup():
    """AC-F41-01: E2E - MCP Server 起動後すぐに lightrag_query が LIGHTRAG_UNAVAILABLE なしに応答する"""
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
async def test_ac_f41_03_startup_completes_without_port_binding():
    """AC-F41-03: E2E - 起動が外部ポートなしで完了する（ポート 9621 LISTEN なし）

    lifespan 起動前後のポート状態を比較し、
    self のコードが新たにポート 9621 をバインドしていないことを検証する。
    他プロセスが既にポート 9621 を使用している場合は誤検知しない。
    """

    def _port_listening(port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return True
        except (ConnectionRefusedError, OSError):
            return False

    port_open_before = _port_listening(9621)

    mock_rag = _make_mock_rag()
    with patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag):
        async with srv._lifespan(None):
            port_open_during = _port_listening(9621)

    # 起動前に閉じていたポートが lifespan によって新たに開かれていないこと
    assert not (port_open_during and not port_open_before), (
        "lifespan 起動によってポート 9621 が新たにバインドされました"
    )


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
async def test_ac_f41_finalize_called_on_server_stop():
    """AC-F41-05: E2E - MCP Server 停止時に finalize_storages が呼ばれ lightrag_server プロセスが存在しない"""
    mock_rag = _make_mock_rag()
    with patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag):
        async with srv._lifespan(None):
            pass
    mock_rag.finalize_storages.assert_called_once()


@pytest.mark.asyncio
async def test_ac_f41_query_after_stop_returns_unavailable():
    """AC-F14-04b: E2E - MCP Server 停止後に lightrag_query を呼ぶと LIGHTRAG_UNAVAILABLE が返る"""
    mock_rag = _make_mock_rag()
    with patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag):
        async with srv._lifespan(None):
            pass
    result = await srv.lightrag_query(query="停止後のクエリ")
    assert "LIGHTRAG_UNAVAILABLE" in result
