"""E2E テスト: F-03 kos_status ツール - in-process 対応（JSON レスポンス形式）"""

from __future__ import annotations

import json
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
    """AC-F03-01: kos_status が LightRAG と CodeGraph の状態を JSON で返す"""
    _set_mock_rag()
    try:
        with patch("aidd_kos.status.StatusChecker.check") as mock_check:
            mock_check.return_value = {
                "lightrag": {
                    "status": "ready",
                    "indexed_at": None,
                    "doc_count": 0,
                    "changed_count": 0,
                    "error_code": None,
                },
                "codegraph": {"status": "ready", "node_count": 100},
            }
            result = await srv.kos_status()
    finally:
        _clear_rag()
    data = json.loads(result)
    assert "lightrag" in data
    assert "codegraph" in data


@pytest.mark.asyncio
async def test_ac_f03_01_lightrag_unavailable():
    """AC-F03-01: _rag が None のとき LightRAG が error として返される"""
    _clear_rag()
    with patch("aidd_kos.status.StatusChecker.check") as mock_check:
        mock_check.return_value = {
            "lightrag": {
                "status": "unavailable",
                "indexed_at": None,
                "doc_count": 0,
                "changed_count": 0,
                "error_code": None,
            },
            "codegraph": {"status": "unavailable", "node_count": 0},
        }
        result = await srv.kos_status()
    data = json.loads(result)
    assert data["lightrag"]["status"] == "error"
    assert data["lightrag"]["error_code"] == "LIGHTRAG_UNAVAILABLE"


@pytest.mark.asyncio
async def test_ac_f03_01_lightrag_indexing():
    """AC-F03-01: _rag が設定されているとき StatusChecker の状態がそのまま返される"""
    _set_mock_rag()
    try:
        with patch("aidd_kos.status.StatusChecker.check") as mock_check:
            mock_check.return_value = {
                "lightrag": {
                    "status": "indexing",
                    "indexed_at": None,
                    "doc_count": 0,
                    "changed_count": 0,
                    "error_code": None,
                },
                "codegraph": {"status": "ready", "node_count": 50},
            }
            result = await srv.kos_status()
    finally:
        _clear_rag()
    data = json.loads(result)
    assert data["lightrag"]["status"] == "indexing"


@pytest.mark.asyncio
async def test_ac_f03_03_available_tools_in_response():
    """AC-F03-03: kos_status レスポンスに利用可能ツールリストが含まれる"""
    _set_mock_rag()
    try:
        with patch("aidd_kos.status.StatusChecker.check") as mock_check:
            mock_check.return_value = {
                "lightrag": {
                    "status": "ready",
                    "indexed_at": None,
                    "doc_count": 0,
                    "changed_count": 0,
                    "error_code": None,
                },
                "codegraph": {"status": "ready", "node_count": 10},
            }
            result = await srv.kos_status()
    finally:
        _clear_rag()
    data = json.loads(result)
    assert "available_tools" in data
    assert "lightrag_query" in data["available_tools"]
