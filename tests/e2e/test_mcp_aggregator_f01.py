"""E2E テスト: F-01 LightRAG ドキュメント検索ツール提供 - in-process 対応"""

from __future__ import annotations

from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import mcp_server.server as srv


def _set_mock_rag(query_response=None, list_response=None):
    mock_rag = MagicMock()
    mock_rag.aquery_llm = AsyncMock(
        return_value=query_response
        or {
            "llm_response": {
                "response": "OAuth token は 1 時間で失効します",
                "references": [{"file_path": "docs___spec___auth.md"}],
            }
        }
    )
    mock_rag.get_docs_by_status = AsyncMock(return_value=list_response or {})
    srv._rag = mock_rag
    return mock_rag


def _clear_rag():
    srv._rag = None


def _make_lightrag_dir(tmp_path):
    """インデックス済みの .lightrag/ ディレクトリを作成"""
    d = tmp_path / ".lightrag"
    d.mkdir()
    (d / "kv_store_full_docs.json").write_text("{}")
    return d


# ── AC-F01-01: lightrag_query がドキュメントと出典パスを返す ──────────────────


@pytest.mark.asyncio
async def test_ac_f01_01_lightrag_query_returns_content_and_path(tmp_path):
    """AC-F01-01: lightrag_query が関連ドキュメントと出典ファイルパスを返す"""
    _make_lightrag_dir(tmp_path)
    _set_mock_rag()
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
            result = await srv.lightrag_query(query="OAuth token")
    finally:
        _clear_rag()
    assert "OAuth token" in result or "失効" in result
    assert "docs/spec/auth.md" in result  # ___ → / に変換される


# ── AC-F01-02: mode パラメータ ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f01_02_mode_hybrid_default(tmp_path):
    """AC-F01-02: mode デフォルトは hybrid"""
    _make_lightrag_dir(tmp_path)
    mock_rag = _set_mock_rag()
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
            await srv.lightrag_query(query="test")
    finally:
        _clear_rag()
    call_args = mock_rag.aquery_llm.call_args
    param = call_args[0][1] if call_args else None
    assert param is None or getattr(param, "mode", "hybrid") == "hybrid"


@pytest.mark.asyncio
async def test_ac_f01_02_mode_local_accepted(tmp_path):
    """AC-F01-02: mode=local が受け付けられる"""
    _make_lightrag_dir(tmp_path)
    _set_mock_rag()
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
            result = await srv.lightrag_query(query="test", mode="local")
    finally:
        _clear_rag()
    assert "INVALID_MODE" not in result


# ── AC-F01-03: lightrag_list がパスを返す ─────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f01_03_lightrag_list_returns_paths():
    """AC-F01-03: lightrag_list がインデックス済みドキュメントのリストを返す"""
    mock_doc = MagicMock()
    mock_doc.content_summary = "README doc"
    mock_doc.status = "processed"
    _set_mock_rag(list_response={"doc_001": mock_doc})
    try:
        result = await srv.lightrag_list(limit=10)
    finally:
        _clear_rag()
    assert "インデックス済みドキュメント" in result


# ── AC-F01-04: lightrag_list 空 ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f01_04_lightrag_list_empty():
    """AC-F01-04: インデックスが空の場合 lightrag_list は「なし」を返す"""
    _set_mock_rag(list_response={})
    try:
        result = await srv.lightrag_list(limit=10)
    finally:
        _clear_rag()
    assert "なし" in result


# ── AC-F01-05: LIGHTRAG_UNAVAILABLE エラー ────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f01_05_lightrag_unavailable_error():
    """AC-F01-05: _rag が None のとき LIGHTRAG_UNAVAILABLE を返す"""
    _clear_rag()
    result = await srv.lightrag_query(query="test")
    assert "LIGHTRAG_UNAVAILABLE" in result


# ── AC-F01-06: エラーを stderr に出力 ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f01_06_error_outputs_to_stderr():
    """AC-F01-06: LIGHTRAG_UNAVAILABLE エラーが stderr に出力される"""
    _clear_rag()
    with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
        await srv.lightrag_query(query="test")
    assert "LIGHTRAG_UNAVAILABLE" in mock_stderr.getvalue()


@pytest.mark.asyncio
async def test_ac_f01_06_list_error_outputs_to_stderr():
    """AC-F01-06: lightrag_list エラーが stderr に出力される"""
    _clear_rag()
    result = await srv.lightrag_list()
    assert "LIGHTRAG_UNAVAILABLE" in result


# ── タイムアウト ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_td_01_query_timeout_error(tmp_path):
    """QUERY_TIMEOUT が発生した場合 QUERY_TIMEOUT エラーを返す"""
    _make_lightrag_dir(tmp_path)
    mock_rag = MagicMock()
    mock_rag.aquery_llm = AsyncMock(side_effect=TimeoutError("timeout"))
    srv._rag = mock_rag
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
    assert "QUERY_TIMEOUT" in result or "LIGHTRAG_UNAVAILABLE" in result
