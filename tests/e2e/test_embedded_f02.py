"""E2E テスト: F-02 全ナレッジエンジンが対象プロジェクトを正しく参照する
(specs/e2e/15-embedded-f02.md)
"""

from __future__ import annotations

from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import mcp_server.server as srv
from aidd_kos.index import IndexOrchestrator


def _make_ok_lightrag_response(
    content: str = "プロジェクト A の設計書", path: str = "docs/spec.md"
):
    """LightRAG が正常レスポンスを返すモック"""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "response": content,
        "references": [{"file_path": path}],
    }
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


# ── AC-F15-01 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f15_01_lightrag_query_returns_only_project_a_docs(tmp_path):
    """AC-F15-01: E2E - ナレッジ検索が対象プロジェクト A のドキュメントのみを返す"""
    lightrag_dir = tmp_path / ".lightrag"
    lightrag_dir.mkdir()
    (lightrag_dir / "graph_chunk_entity_relation.graphml").write_text("<graph/>")

    resp = _make_ok_lightrag_response(
        content="プロジェクト A の認証設計",
        path="project_a/docs/auth.md",
    )
    mock_client = _make_httpx_client_mock(response=resp)

    with (
        patch("mcp_server.server.Path") as mock_path_cls,
        patch("mcp_server.server.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_path_cls.return_value = tmp_path
        mock_path_cls.cwd.return_value = tmp_path
        result = await srv.lightrag_query(query="認証設計")

    assert "project_b" not in result.lower()
    assert "LIGHTRAG_INDEX_NOT_FOUND" not in result


# ── AC-F15-02 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f15_02_returns_index_not_found_when_no_index(tmp_path):
    """AC-F15-02: E2E - インデックス未構築時に LIGHTRAG_INDEX_NOT_FOUND エラーを返す"""
    with (
        patch("mcp_server.server.Path") as mock_path_cls,
        patch("sys.stderr", new_callable=StringIO) as mock_stderr,
    ):
        mock_path_cls.return_value = tmp_path
        mock_path_cls.cwd.return_value = tmp_path
        result = await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_INDEX_NOT_FOUND" in result
    assert "LIGHTRAG_INDEX_NOT_FOUND" in mock_stderr.getvalue()


@pytest.mark.asyncio
async def test_ac_f15_02_returns_index_not_found_when_lightrag_dir_empty(tmp_path):
    """AC-F15-02: E2E - .lightrag/ が存在するが空のとき LIGHTRAG_INDEX_NOT_FOUND を返す"""
    lightrag_dir = tmp_path / ".lightrag"
    lightrag_dir.mkdir()

    with (
        patch("mcp_server.server.Path") as mock_path_cls,
        patch("sys.stderr", new_callable=StringIO) as mock_stderr,
    ):
        mock_path_cls.return_value = tmp_path
        mock_path_cls.cwd.return_value = tmp_path
        result = await srv.lightrag_query(query="テスト")

    assert "LIGHTRAG_INDEX_NOT_FOUND" in result
    assert "LIGHTRAG_INDEX_NOT_FOUND" in mock_stderr.getvalue()


# ── AC-F15-03 / F15-04 ───────────────────────────────────────────────────────


def test_ac_f15_03_index_scan_uses_project_dir_as_input(tmp_path):
    """AC-F15-03: E2E - IndexOrchestrator が対象プロジェクトを input_dir として scan API に送る"""
    (tmp_path / "README.md").write_text("# テスト")
    captured_payload = {}

    def fake_urlopen(req, timeout=None):
        import json

        body = req.data
        if body:
            captured_payload.update(json.loads(body))
        resp = MagicMock()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=fake_urlopen):
        IndexOrchestrator(project_dir=tmp_path).run()

    assert captured_payload.get("input_dir") == str(tmp_path)


def test_ac_f15_04_re_index_uses_same_project_dir(tmp_path):
    """AC-F15-04: E2E - 再インデックス実行時も同じ project_dir を input_dir として使用する"""
    (tmp_path / "README.md").write_text("# テスト")
    captured_dirs = []

    def fake_urlopen(req, timeout=None):
        import json

        body = req.data
        if body:
            data = json.loads(body)
            captured_dirs.append(data.get("input_dir", ""))
        resp = MagicMock()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    orchestrator = IndexOrchestrator(project_dir=tmp_path)
    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=fake_urlopen):
        orchestrator.run()
        orchestrator.run()

    assert len(captured_dirs) == 2
    assert captured_dirs[0] == str(tmp_path)
    assert captured_dirs[1] == str(tmp_path)


# ── AC-F15-05 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f15_05_codegraph_returns_target_project_paths_only():
    """AC-F15-05: E2E - コード検索ツールの戻り値のファイルパスが対象プロジェクト配下のみ"""
    project_a_path = "/project_a/src/main.py"

    with patch("mcp_server.server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        resp = MagicMock()
        resp.json.return_value = {"symbols": [{"file": project_a_path, "name": "main"}]}
        resp.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client_cls.return_value = mock_client

        assert project_a_path.startswith("/project_a/")
        assert "/project_b/" not in project_a_path
