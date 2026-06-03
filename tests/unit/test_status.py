"""ユニットテスト: aidd_kos.status (StatusChecker)"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aidd_kos.status import StatusChecker


def test_ac_f03_01_unit_lightrag_ready() -> None:
    """AC-F03-01: Unit - LightRAG が応答する場合 ready を返す"""
    import urllib.request

    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch.object(urllib.request, "urlopen", return_value=mock_resp):
        checker = StatusChecker()
        result = checker.check()
    assert result["lightrag"]["status"] == "ready"


def test_ac_f03_01_unit_lightrag_unavailable() -> None:
    """AC-F03-01: Unit - LightRAG が応答しない場合 unavailable を返す"""
    import urllib.error
    import urllib.request

    with patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
        checker = StatusChecker()
        result = checker.check()
    assert result["lightrag"]["status"] == "unavailable"


def test_ac_f03_01_unit_codegraph_ready() -> None:
    """AC-F03-01: Unit - CodeGraph が初期化済みの場合 ready を返す"""
    import subprocess

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"initialized": true, "nodeCount": 72}'
    with patch.object(subprocess, "run", return_value=mock_result):
        checker = StatusChecker()
        result = checker.check()
    assert result["codegraph"]["status"] == "ready"
    assert result["codegraph"]["node_count"] == 72


def test_ac_f03_01_unit_codegraph_unavailable() -> None:
    """AC-F03-01: Unit - CodeGraph が未初期化の場合 unavailable を返す"""
    import subprocess

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"initialized": false, "nodeCount": 0}'
    with patch.object(subprocess, "run", return_value=mock_result):
        checker = StatusChecker()
        result = checker.check()
    assert result["codegraph"]["status"] == "unavailable"


def test_ac_f03_02_unit_check_returns_dict() -> None:
    """AC-F03-02: Unit - check() が JSON シリアライズ可能な dict を返す"""
    import json
    import urllib.error
    import urllib.request

    with patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
        checker = StatusChecker()
        result = checker.check()
    # JSON としてシリアライズ可能なこと
    json.dumps(result)
