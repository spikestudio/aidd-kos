"""E2E テスト: F-03 status コマンド (docs/spec/install.md)
F-01 インデックス状態の 4 値可視化・エラー診断（docs/spec/status-visibility.md）"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()


@pytest.fixture()
def lightrag_ready():
    """LightRAG が ready 状態をモックする（複数エンドポイント対応）"""
    import urllib.error
    import urllib.request

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        resp = MagicMock()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        if "pipeline_status" in url:
            resp.read.return_value = b'{"busy": false}'
        elif "documents" in url:
            resp.read.return_value = b"[]"
        else:
            resp.read.return_value = b"ok"
        return resp

    with patch.object(urllib.request, "urlopen", fake_urlopen):
        yield


@pytest.fixture()
def codegraph_ready():
    """CodeGraph が ready 状態をモックする"""
    import subprocess

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"initialized": true, "nodeCount": 72}'

    with patch.object(subprocess, "run", return_value=mock_result):
        yield


# ── AC-F03-01: 両エンジンの状態表示 ──────────────────────────────────────────


def test_ac_f03_01_e2e_shows_both_engine_statuses(
    lightrag_ready: None, codegraph_ready: None
) -> None:
    """AC-F03-01: E2E - LightRAG と CodeGraph の状態が表示される"""
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "LightRAG" in result.output or "lightrag" in result.output.lower()
    assert "CodeGraph" in result.output or "codegraph" in result.output.lower()


def test_ac_f03_01_e2e_lightrag_ready_status(lightrag_ready: None, codegraph_ready: None) -> None:
    """AC-F03-01: E2E - LightRAG が ready の場合 ready と表示される"""
    result = runner.invoke(app, ["status"])
    assert "ready" in result.output


def test_ac_f03_01_e2e_lightrag_unavailable_status() -> None:
    """AC-F03-01: E2E - LightRAG が error 状態の場合 error と表示される（旧: unavailable）"""
    import urllib.error
    import urllib.request

    with patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "error" in result.output


# ── AC-F03-02: --json フラグ ───────────────────────────────────────────────────


def test_ac_f03_02_e2e_json_output(lightrag_ready: None, codegraph_ready: None) -> None:
    """AC-F03-02: E2E - --json フラグで JSON 形式の出力が得られる"""
    import json

    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0
    # JSON としてパース可能なこと
    data = json.loads(result.output.strip())
    assert "lightrag" in data or "LightRAG" in str(data)


# ── AC-F46: インデックス状態の 4 値可視化・エラー診断（CLI + MCP）─────────────────


def _patch_check(status: str, changed_count: int = 0, error_code: str | None = None):
    """StatusChecker._check_lightrag の戻り値を制御するパッチを返す。"""
    from aidd_kos import status as status_mod

    def fake_check_lightrag(self):
        return {
            "status": status,
            "indexed_at": None,
            "doc_count": 0,
            "changed_count": changed_count,
            "error_code": error_code,
        }

    return patch.object(status_mod.StatusChecker, "_check_lightrag", fake_check_lightrag)


def test_ac_f46_01_e2e_cli_ready_when_no_changed_files() -> None:
    """AC-F46-01: E2E - 変更ファイル 0 件のとき stdout に LightRAG: ready が表示される"""
    with _patch_check("ready", changed_count=0):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "ready" in result.output
    assert "LightRAG" in result.output


def test_ac_f46_02_e2e_cli_stale_with_changed_count() -> None:
    """AC-F46-02: E2E - 変更ファイルがある場合 stdout に LightRAG: stale (変更 3 件) が表示される"""
    with _patch_check("stale", changed_count=3):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "stale" in result.output
    assert "3" in result.output


def test_ac_f46_03_e2e_cli_error_in_stdout() -> None:
    """AC-F46-03: E2E - LightRAG 未起動時 stdout に LightRAG: error が表示される"""
    import urllib.error
    import urllib.request

    with patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "error" in result.output


def test_ac_f46_04_e2e_cli_error_in_stderr() -> None:
    """AC-F46-04: E2E - LightRAG 未起動時 LIGHTRAG_UNAVAILABLE と再試行コマンドが出力される。
    Note: CliRunner は stderr と stdout を混在させるため combined output で検証する。"""
    import urllib.error
    import urllib.request

    with patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "LIGHTRAG_UNAVAILABLE" in result.output
    assert "aidd-kos serve" in result.output


@pytest.mark.asyncio
async def test_ac_f46_05_e2e_mcp_kos_status_stale() -> None:
    """AC-F46-05: E2E - kos_status MCP ツールが stale 状態を返す"""
    import json

    import mcp_server.server as srv

    # Stale 検出が走るよう _rag をモック（初期化済み）
    mock_rag = MagicMock()
    # past_time で last_indexed_at を設定し stale になるようにする
    with patch.object(srv, "_rag", mock_rag):
        import aidd_kos.status as status_mod

        def fake_check_lightrag(self):
            return {
                "status": "stale",
                "indexed_at": None,
                "doc_count": 0,
                "changed_count": 2,
                "error_code": None,
            }

        with patch.object(status_mod.StatusChecker, "_check_lightrag", fake_check_lightrag):
            response_str = await srv.kos_status()

    data = json.loads(response_str)
    assert data["lightrag"]["status"] == "stale"


@pytest.mark.asyncio
async def test_ac_f46_06_e2e_mcp_kos_status_error() -> None:
    """AC-F46-06: E2E - kos_status MCP が error 状態と LIGHTRAG_UNAVAILABLE を返す"""
    import json

    import mcp_server.server as srv

    with patch.object(srv, "_rag", None):
        response_str = await srv.kos_status()

    data = json.loads(response_str)
    assert data["lightrag"]["status"] == "error"
    assert data["lightrag"]["error_code"] == "LIGHTRAG_UNAVAILABLE"


# ── AC-F47: インデックス処理中の進捗表示 ─────────────────────────────────────────


def _patch_check_indexing(docs: int = 10, cur_batch: int = 3):
    """StatusChecker._check_lightrag が indexing 状態を返すパッチ。"""
    from aidd_kos import status as status_mod

    progress = {"processed": cur_batch, "total": docs} if docs > 0 else None

    def fake_check_lightrag(self):
        return {
            "status": "indexing",
            "indexed_at": None,
            "doc_count": 0,
            "changed_count": 0,
            "error_code": None,
            "progress": progress,
        }

    return patch.object(status_mod.StatusChecker, "_check_lightrag", fake_check_lightrag)


def test_ac_f47_01_e2e_cli_indexing_with_progress() -> None:
    """AC-F47-01: E2E - Indexing 中に処理済み/総数が stdout に表示される"""
    with _patch_check_indexing(docs=10, cur_batch=3):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "indexing" in result.output
    assert "3" in result.output
    assert "10" in result.output


def test_ac_f47_03_e2e_cli_ready_after_indexing() -> None:
    """AC-F47-03: E2E - Indexing 完了後に ready が表示され indexing 表示が消える"""
    with _patch_check("ready", changed_count=0):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "ready" in result.output
    assert "indexing" not in result.output


@pytest.mark.asyncio
async def test_ac_f47_02_e2e_mcp_kos_status_indexing_progress() -> None:
    """AC-F47-02: E2E - kos_status MCP が indexing 状態と progress フィールドを返す"""
    import json

    import mcp_server.server as srv

    mock_rag = MagicMock()
    with patch.object(srv, "_rag", mock_rag):
        import aidd_kos.status as status_mod

        def fake_check_lightrag(self):
            return {
                "status": "indexing",
                "indexed_at": None,
                "doc_count": 0,
                "changed_count": 0,
                "error_code": None,
                "progress": {"processed": 3, "total": 10},
            }

        with patch.object(status_mod.StatusChecker, "_check_lightrag", fake_check_lightrag):
            response_str = await srv.kos_status()

    data = json.loads(response_str)
    assert data["lightrag"]["status"] == "indexing"
    assert isinstance(data["lightrag"]["progress"]["processed"], int)
    assert isinstance(data["lightrag"]["progress"]["total"], int)
