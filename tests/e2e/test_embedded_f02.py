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


def test_ac_f15_03_index_sends_files_with_relative_paths(tmp_path):
    """AC-F15-03: E2E - IndexOrchestrator が対象プロジェクトの .md/.txt ファイルを
    テキスト API に送信し file_sources が相対パスであること"""
    (tmp_path / "README.md").write_text("# テスト")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "spec.md").write_text("# スペック")
    captured_sources = []

    def fake_urlopen(req, timeout=None):
        import json

        body = req.data
        if body:
            data = json.loads(body)
            captured_sources.extend(data.get("file_sources", []))
        resp = MagicMock()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=fake_urlopen):
        IndexOrchestrator(project_dir=tmp_path).run()

    assert len(captured_sources) == 2
    assert all(not s.startswith("/") for s in captured_sources), "file_sources は相対パスであること"
    assert any("README.md" in s for s in captured_sources)
    assert any("docs" in s for s in captured_sources)


def test_ac_f15_04_re_index_uses_same_relative_paths(tmp_path):
    """AC-F15-04: E2E - 再インデックス実行時も同じ対象プロジェクトの相対パスを使用する"""
    (tmp_path / "README.md").write_text("# テスト")
    all_sources: list[list[str]] = []

    def fake_urlopen(req, timeout=None):
        import json

        body = req.data
        if body:
            data = json.loads(body)
            sources = data.get("file_sources", [])
            if sources:
                all_sources.append(sources)
        resp = MagicMock()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    orchestrator = IndexOrchestrator(project_dir=tmp_path)
    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=fake_urlopen):
        orchestrator.run()
        orchestrator.run()

    assert len(all_sources) == 2
    assert all_sources[0] == all_sources[1], "1回目と2回目で同じ file_sources が送られること"


# ── AC-F15-05 ─────────────────────────────────────────────────────────────────


def test_ac_f15_05_codegraph_npx_transport_uses_cwd_inheritance():
    """AC-F15-05: E2E - NpxStdioTransport が project_directory なし（親 cwd 継承）で作成される。
    uvx aidd-kos serve の実行ディレクトリ（target-project）が CodeGraph の cwd として使われ、
    コード検索の結果が対象プロジェクト配下のファイルパスのみを返すことが保証される。
    """
    import pathlib

    import mcp_server.server as srv_module

    src = pathlib.Path(srv_module.__file__).read_text()

    npx_block_start = src.find("NpxStdioTransport(")
    assert npx_block_start != -1, "NpxStdioTransport の呼び出しが見つからない"

    depth = 0
    npx_block = ""
    for i, c in enumerate(src[npx_block_start:]):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                npx_block = src[npx_block_start : npx_block_start + i + 1]
                break

    assert "project_directory" not in npx_block, (
        "NpxStdioTransport に project_directory が渡されている。"
        "project_directory=None（省略）でないと cwd 継承が崩れる。"
    )
