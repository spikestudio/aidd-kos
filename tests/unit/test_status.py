"""ユニットテスト: aidd_kos.status (StatusChecker)"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch


def _make_url_mock(responses: dict):
    """URL ごとに異なるレスポンスを返すモック urlopen を生成する。"""

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        resp = MagicMock()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        for pattern, body in responses.items():
            if pattern in url:
                resp.read.return_value = body.encode() if isinstance(body, str) else body
                return resp
        # デフォルト: 接続拒否
        raise urllib.error.URLError("not found")

    return fake_urlopen


def test_ac_f03_01_unit_lightrag_ready() -> None:
    """AC-F03-01: Unit - LightRAG が応答する場合 ready を返す"""
    fake = _make_url_mock(
        {
            "/health": "ok",
            "/documents/pipeline_status": '{"busy": false}',
            "/documents": "[]",
        }
    )
    with patch.object(urllib.request, "urlopen", fake):
        from aidd_kos.status import StatusChecker

        checker = StatusChecker()
        result = checker.check()
    assert result["lightrag"]["status"] == "ready"


def test_ac_f03_01_unit_lightrag_indexing() -> None:
    """AC-F03-01: Unit - LightRAG がインデックス構築中の場合 indexing を返す"""
    fake = _make_url_mock(
        {
            "/health": "ok",
            "/documents/pipeline_status": '{"busy": true}',
            "/documents": "[]",
        }
    )
    with patch.object(urllib.request, "urlopen", fake):
        from aidd_kos.status import StatusChecker

        checker = StatusChecker()
        result = checker.check()
    assert result["lightrag"]["status"] == "indexing"


def test_ac_f03_01_unit_lightrag_unavailable() -> None:
    """AC-F03-01: Unit - LightRAG が応答しない場合 unavailable を返す"""
    with patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
        from aidd_kos.status import StatusChecker

        checker = StatusChecker()
        result = checker.check()
    assert result["lightrag"]["status"] == "unavailable"


def test_ac_f03_01_unit_lightrag_returns_indexed_at(tmp_path) -> None:
    """AC-F03-01: Unit - LightRAG の応答にインデックス日時が含まれる"""
    # .lightrag/last_indexed_at ファイルを作成
    lightrag_dir = tmp_path / ".lightrag"
    lightrag_dir.mkdir()
    (lightrag_dir / "last_indexed_at").write_text("2026-06-03T20:00:00")

    fake = _make_url_mock(
        {
            "/health": "ok",
            "/documents/pipeline_status": '{"busy": false}',
            "/documents": '[{"id": "1"}]',
        }
    )
    with patch.object(urllib.request, "urlopen", fake):
        from aidd_kos.status import StatusChecker

        checker = StatusChecker(project_dir=tmp_path)
        result = checker.check()
    assert result["lightrag"]["indexed_at"] == "2026-06-03T20:00:00"
    assert result["lightrag"]["doc_count"] == 1


def test_ac_f03_01_unit_codegraph_ready() -> None:
    """AC-F03-01: Unit - CodeGraph が初期化済みの場合 ready を返す"""
    import subprocess

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"initialized": true, "nodeCount": 72}'
    with (
        patch.object(subprocess, "run", return_value=mock_result),
        patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")),
    ):
        from aidd_kos.status import StatusChecker

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
    with (
        patch.object(subprocess, "run", return_value=mock_result),
        patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")),
    ):
        from aidd_kos.status import StatusChecker

        checker = StatusChecker()
        result = checker.check()
    assert result["codegraph"]["status"] == "unavailable"


def test_ac_f03_02_unit_check_returns_dict() -> None:
    """AC-F03-02: Unit - check() が JSON シリアライズ可能な dict を返す"""
    with patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
        from aidd_kos.status import StatusChecker

        checker = StatusChecker()
        result = checker.check()
    json.dumps(result)
