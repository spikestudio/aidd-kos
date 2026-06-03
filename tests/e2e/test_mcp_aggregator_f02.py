"""E2E テスト: F-02 CodeGraph コード検索ツール統合 (specs/e2e/6-codegraph-proxy.md)"""

from __future__ import annotations

import pytest

import mcp_server.server as srv

# ── AC-F02-01/02/03: CodeGraph proxy が mcp にマウントされている ─────────────


def test_ac_f02_01_codegraph_proxy_mounted():
    """AC-F02-01: aidd-kos mcp に CodeGraph proxy がマウントされている"""
    providers = srv.mcp.providers
    # codegraph namespace でラップされたプロバイダーが存在する
    has_codegraph = any(
        "codegraph" in str(p).lower() or "Namespace('codegraph')" in str(p) for p in providers
    )
    assert has_codegraph, f"CodeGraph proxy が見つかりません。providers: {providers}"


def test_ac_f02_02_lightrag_tools_also_present():
    """AC-F02-01: lightrag_* と codegraph_* が同一 mcp インスタンスに共存"""
    providers = srv.mcp.providers
    # LocalProvider（lightrag ツール）が存在する
    has_local = any("LocalProvider" in str(p) for p in providers)
    # CodeGraph proxy が存在する
    has_codegraph = any("codegraph" in str(p).lower() for p in providers)
    assert has_local, "LocalProvider（lightrag ツール）が見つかりません"
    assert has_codegraph, "CodeGraph proxy が見つかりません"


def test_ac_f02_03_namespace_is_codegraph():
    """AC-F02-03: CodeGraph proxy のツールが codegraph_ prefix で公開される（ADR-002）"""
    providers = srv.mcp.providers
    codegraph_provider = next((p for p in providers if "codegraph" in str(p).lower()), None)
    assert codegraph_provider is not None
    # namespace="codegraph" が設定されていることを確認
    assert "codegraph" in str(codegraph_provider).lower()


# ── 統合確認: lightrag_query が直接実装として存在する ────────────────────────


@pytest.mark.asyncio
async def test_ac_f02_lightrag_query_still_works():
    """F-02: CodeGraph proxy 追加後も lightrag_query が引き続き機能する"""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "test answer", "references": []}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client):
        result = await srv.lightrag_query(query="test")

    assert "LIGHTRAG_UNAVAILABLE" not in result
    assert result == "test answer"
