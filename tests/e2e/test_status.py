"""E2E テスト: F-03 status コマンド (docs/spec/install.md)"""

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
    """AC-F03-01: E2E - LightRAG が unavailable の場合 unavailable と表示される"""
    import urllib.error
    import urllib.request

    with patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "unavailable" in result.output


# ── AC-F03-02: --json フラグ ───────────────────────────────────────────────────


def test_ac_f03_02_e2e_json_output(lightrag_ready: None, codegraph_ready: None) -> None:
    """AC-F03-02: E2E - --json フラグで JSON 形式の出力が得られる"""
    import json

    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0
    # JSON としてパース可能なこと
    data = json.loads(result.output.strip())
    assert "lightrag" in data or "LightRAG" in str(data)
