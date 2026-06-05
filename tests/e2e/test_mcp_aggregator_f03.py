"""E2E テスト: F-03 kos_status ツール - in-process 対応"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import mcp_server.server as srv


def _set_mock_rag():
    mock_rag = MagicMock()
    srv._rag = mock_rag
    return mock_rag


def _clear_rag():
    srv._rag = None


@pytest.mark.asyncio
async def test_ac_f03_01_kos_status_returns_both_engines():
    """AC-F03-01: kos_status が LightRAG と CodeGraph の状態を返す"""
    _set_mock_rag()
    try:
        with patch("aidd_kos.status.StatusChecker.check") as mock_check:
            mock_check.return_value = {
                "lightrag": {"status": "ready"},
                "codegraph": {"status": "ready", "node_count": 100},
            }
            result = await srv.kos_status()
    finally:
        _clear_rag()
    assert "LightRAG" in result
    assert "CodeGraph" in result


@pytest.mark.asyncio
async def test_ac_f03_01_lightrag_unavailable():
    """AC-F03-01: _rag が None のとき LightRAG が unavailable として表示される"""
    _clear_rag()
    with patch("aidd_kos.status.StatusChecker.check") as mock_check:
        mock_check.return_value = {
            "lightrag": {"status": "unavailable"},
            "codegraph": {"status": "unavailable", "node_count": 0},
        }
        result = await srv.kos_status()
    assert "unavailable" in result


@pytest.mark.asyncio
async def test_ac_f03_01_lightrag_indexing():
    """AC-F03-01: _rag が設定されているとき LightRAG が ready として表示される"""
    _set_mock_rag()
    try:
        with patch("aidd_kos.status.StatusChecker.check") as mock_check:
            mock_check.return_value = {
                "lightrag": {"status": "indexing"},
                "codegraph": {"status": "ready", "node_count": 50},
            }
            result = await srv.kos_status()
    finally:
        _clear_rag()
    assert "LightRAG" in result
    assert "in-process" in result


@pytest.mark.asyncio
async def test_ac_f03_03_available_tools_in_response():
    """AC-F03-03: kos_status レスポンスに利用可能ツールリストが含まれる"""
    _set_mock_rag()
    try:
        with patch("aidd_kos.status.StatusChecker.check") as mock_check:
            mock_check.return_value = {
                "lightrag": {"status": "ready"},
                "codegraph": {"status": "ready", "node_count": 10},
            }
            result = await srv.kos_status()
    finally:
        _clear_rag()
    assert "available_tools" in result
    assert "lightrag_query" in result
