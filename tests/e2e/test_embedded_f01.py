"""E2E テスト: F-01 ナレッジ検索が MCP サーバー起動直後から利用可能になる
(specs/e2e/14-embedded-f01.md)
"""

from __future__ import annotations

import urllib.error
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

import mcp_server.server as srv


def _make_proc_mock(poll_return=None):
    """subprocess.Popen モックを生成する（poll_return=None: プロセス実行中）"""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = poll_return
    mock_proc.wait.return_value = None
    return mock_proc


def _make_ok_lightrag_response():
    """LightRAG が正常レスポンスを返すモック"""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "テスト結果", "references": []}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _make_httpx_client_mock(response=None, side_effect=None):
    """httpx.AsyncClient モックを生成する"""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    if side_effect is not None:
        mock_client.post = AsyncMock(side_effect=side_effect)
    else:
        mock_client.post = AsyncMock(return_value=response or _make_ok_lightrag_response())
    return mock_client


# ── AC-F14-01 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f14_01_lightrag_query_available_immediately_after_startup():
    """AC-F14-01: E2E - MCP Server 起動後すぐに lightrag_query が LIGHTRAG_UNAVAILABLE なしに応答する"""
    mock_proc = _make_proc_mock(poll_return=None)
    mock_client = _make_httpx_client_mock()

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", return_value=MagicMock()),
        patch("asyncio.sleep"),
        patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client),
    ):
        async with srv._lifespan(None):
            result = await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_UNAVAILABLE" not in result
    assert result != ""  # S-1: 検索結果が空でないこと（肯定形アサート）


# ── AC-F14-02 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f14_02_startup_completes_within_30_seconds():
    """AC-F14-02: E2E - 起動から 30 秒以内に最初のクエリが成功する"""
    mock_proc = _make_proc_mock(poll_return=None)
    mock_client = _make_httpx_client_mock()
    total_sleep = 0.0

    async def counting_sleep(seconds):
        nonlocal total_sleep
        total_sleep += float(seconds)

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", return_value=MagicMock()),
        patch("asyncio.sleep", side_effect=counting_sleep),
        patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client),
    ):
        async with srv._lifespan(None):
            result = await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_UNAVAILABLE" not in result
    assert total_sleep < 30.0


# ── AC-F14-03a ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f14_03a_startup_fails_on_immediate_process_exit():
    """AC-F14-03a: E2E - プロセス即時終了時に RuntimeError が送出され stderr に LIGHTRAG_STARTUP_FAILED が出力される"""
    mock_proc = _make_proc_mock(poll_return=1)

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen"),
        patch("asyncio.sleep"),
        patch("sys.stderr", new_callable=StringIO) as mock_stderr,
        pytest.raises(RuntimeError, match="LIGHTRAG_STARTUP_FAILED"),
    ):
        async with srv._lifespan(None):
            pass  # 到達しない

    assert "LIGHTRAG_STARTUP_FAILED" in mock_stderr.getvalue()


# ── AC-F14-03b ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f14_03b_startup_fails_on_30s_timeout():
    """AC-F14-03b: E2E - 30 秒タイムアウト到達時に RuntimeError が送出され stderr に LIGHTRAG_STARTUP_FAILED が出力される"""
    mock_proc = _make_proc_mock(poll_return=None)

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ),
        patch("asyncio.sleep"),
        patch("sys.stderr", new_callable=StringIO) as mock_stderr,
        pytest.raises(RuntimeError, match="LIGHTRAG_STARTUP_FAILED"),
    ):
        async with srv._lifespan(None):
            pass  # 到達しない

    assert "LIGHTRAG_STARTUP_FAILED" in mock_stderr.getvalue()


# ── AC-F14-04a ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f14_04a_proc_terminate_called_on_server_stop():
    """AC-F14-04a: E2E - MCP Server 停止時に LightRAG バックグラウンドプロセスが terminate される"""
    mock_proc = _make_proc_mock(poll_return=None)

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", return_value=MagicMock()),
        patch("asyncio.sleep"),
    ):
        async with srv._lifespan(None):
            pass

    mock_proc.terminate.assert_called_once()


# ── AC-F14-04b ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f14_04b_query_after_stop_returns_unavailable():
    """AC-F14-04b: E2E - MCP Server 停止後に lightrag_query を呼ぶと LIGHTRAG_UNAVAILABLE が返る"""
    mock_proc = _make_proc_mock(poll_return=None)
    mock_client = _make_httpx_client_mock(side_effect=httpx.ConnectError("Connection refused"))

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", return_value=MagicMock()),
        patch("asyncio.sleep"),
        patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client),
    ):
        async with srv._lifespan(None):
            pass

        result = await srv.lightrag_query(query="停止後のクエリ")

    assert "LIGHTRAG_UNAVAILABLE" in result
