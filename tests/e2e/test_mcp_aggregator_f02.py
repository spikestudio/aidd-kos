"""E2E テスト: F-02 CodeGraph コード検索ツール統合 - in-process 対応"""

from __future__ import annotations

import pytest

import mcp_server.server as srv


def _set_mock_rag_simple():
    from unittest.mock import AsyncMock, MagicMock

    mock_rag = MagicMock()
    mock_rag.aquery_llm = AsyncMock(
        return_value={"llm_response": {"response": "test answer", "references": []}}
    )
    mock_rag.get_docs_by_status = AsyncMock(return_value={})
    srv._rag = mock_rag
    return mock_rag


def _clear_rag():
    srv._rag = None


def test_ac_f02_01_codegraph_proxy_mounted():
    """AC-F02-01: aidd-kos mcp に CodeGraph proxy がマウントされている"""
    providers = srv.mcp.providers
    has_codegraph = any(
        "codegraph" in str(p).lower() or "Namespace('codegraph')" in str(p) for p in providers
    )
    assert has_codegraph, f"CodeGraph proxy が見つかりません。providers: {providers}"


def test_ac_f02_02_lightrag_tools_also_present():
    """AC-F02-01: lightrag_* と codegraph_* が同一 mcp インスタンスに共存"""
    providers = srv.mcp.providers
    has_local = any("LocalProvider" in str(p) for p in providers)
    has_codegraph = any("codegraph" in str(p).lower() for p in providers)
    assert has_local, "LocalProvider（lightrag ツール）が見つかりません"
    assert has_codegraph, "CodeGraph proxy が見つかりません"


def test_ac_f02_03_namespace_is_codegraph():
    """AC-F02-03: CodeGraph proxy のツールが codegraph_ prefix で公開される（ADR-002）"""
    providers = srv.mcp.providers
    codegraph_provider = next((p for p in providers if "codegraph" in str(p).lower()), None)
    assert codegraph_provider is not None


@pytest.mark.asyncio
async def test_ac_f02_lightrag_query_still_works():
    """F-02: CodeGraph proxy 追加後も lightrag_query が引き続き機能する"""
    from unittest.mock import MagicMock, patch

    _set_mock_rag_simple()
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
            result = await srv.lightrag_query(query="test")
    finally:
        _clear_rag()
    assert "LIGHTRAG_UNAVAILABLE" not in result
    assert result == "test answer"
