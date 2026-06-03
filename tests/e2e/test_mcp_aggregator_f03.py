"""E2E テスト: F-03 統合ステータス確認 kos_status (specs/e2e/7-kos-status.md)"""

from __future__ import annotations

import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

import mcp_server.server as srv


def _make_url_mock(responses: dict):
    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        resp = MagicMock()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        for pattern, body in responses.items():
            if pattern in url:
                resp.read.return_value = body.encode() if isinstance(body, str) else body
                return resp
        raise urllib.error.URLError("not found")

    return fake_urlopen


# ── AC-F03-01: kos_status が両エンジンの状態を返す ────────────────────────────


@pytest.mark.asyncio
async def test_ac_f03_01_kos_status_returns_both_engines():
    """AC-F03-01: kos_status が LightRAG と CodeGraph 両エンジンの状態を返す"""
    fake = _make_url_mock(
        {
            "/health": "ok",
            "/documents/pipeline_status": '{"busy": false}',
            "/documents": "[]",
        }
    )
    import subprocess

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"initialized": true, "nodeCount": 72}'

    with (
        patch.object(urllib.request, "urlopen", fake),
        patch.object(subprocess, "run", return_value=mock_result),
    ):
        result = await srv.kos_status()

    assert "lightrag" in result.lower() or "LightRAG" in result
    assert "codegraph" in result.lower() or "CodeGraph" in result
    assert "ready" in result


@pytest.mark.asyncio
async def test_ac_f03_01_lightrag_unavailable():
    """AC-F03-01: LightRAG が unavailable の場合 unavailable が返る"""
    import subprocess

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"initialized": true, "nodeCount": 0}'

    with (
        patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")),
        patch.object(subprocess, "run", return_value=mock_result),
    ):
        result = await srv.kos_status()

    assert "unavailable" in result


@pytest.mark.asyncio
async def test_ac_f03_01_lightrag_indexing():
    """AC-F03-01: LightRAG がインデックス中の場合 indexing が返る"""
    fake = _make_url_mock(
        {
            "/health": "ok",
            "/documents/pipeline_status": '{"busy": true}',
            "/documents": "[]",
        }
    )
    import subprocess

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"initialized": true, "nodeCount": 0}'

    with (
        patch.object(urllib.request, "urlopen", fake),
        patch.object(subprocess, "run", return_value=mock_result),
    ):
        result = await srv.kos_status()

    assert "indexing" in result


# ── AC-F03-03: available_tools フィールド ─────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f03_03_available_tools_in_response():
    """AC-F03-03: kos_status のレスポンスに available_tools が含まれる"""
    fake = _make_url_mock(
        {
            "/health": "ok",
            "/documents/pipeline_status": '{"busy": false}',
            "/documents": "[]",
        }
    )
    import subprocess

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"initialized": true, "nodeCount": 72}'

    with (
        patch.object(urllib.request, "urlopen", fake),
        patch.object(subprocess, "run", return_value=mock_result),
    ):
        result = await srv.kos_status()

    assert "lightrag_query" in result
    assert "codegraph_explore" in result or "codegraph" in result.lower()
