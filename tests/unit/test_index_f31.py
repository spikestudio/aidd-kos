"""ユニットテスト: Feature #31 全件再構築 (IndexOrchestrator full モード)"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from aidd_kos.index import IndexOrchestrator


class _FakeResp:
    def __init__(self, body: bytes = b'{"status":"ok"}') -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *a: object) -> None:
        pass


def test_ac_f31_01_unit_run_full_returns_full_count(tmp_path: Path) -> None:
    """AC-F31-01: Unit - run(full=True) が full_count を返す"""
    for name in ("a.md", "b.txt"):
        (tmp_path / name).write_text(f"content {name}")

    idx = IndexOrchestrator(project_dir=tmp_path)

    with patch("aidd_kos.index.urllib.request.urlopen", return_value=_FakeResp()):
        result = idx.run(full=True)

    assert "full_count" in result
    assert result["full_count"] == 2


def test_ac_f31_02_unit_run_full_skip_count_zero(tmp_path: Path) -> None:
    """AC-F31-02: Unit - run(full=True) のとき skip_count は 0"""
    (tmp_path / "doc.md").write_text("content")

    idx = IndexOrchestrator(project_dir=tmp_path)

    with patch("aidd_kos.index.urllib.request.urlopen", return_value=_FakeResp()):
        result = idx.run(full=True)

    assert result["skip_count"] == 0


def test_ac_f31_02_unit_run_full_does_not_call_paginated(tmp_path: Path) -> None:
    """AC-F31-02: Unit - run(full=True) では paginated API を呼ばない"""
    (tmp_path / "doc.md").write_text("content")

    idx = IndexOrchestrator(project_dir=tmp_path)
    paginated_calls = 0

    def _urlopen(req, timeout=None):
        nonlocal paginated_calls
        if "paginated" in req.full_url:
            paginated_calls += 1
        return _FakeResp()

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        idx.run(full=True)

    assert paginated_calls == 0


def test_ac_f31_01_unit_run_default_still_uses_diff(tmp_path: Path) -> None:
    """AC-F31-01: Unit - run() デフォルト（full=False）では差分モードが維持される"""
    (tmp_path / "doc.md").write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)

    paginated_calls = 0

    def _urlopen(req, timeout=None):
        nonlocal paginated_calls
        if "paginated" in req.full_url:
            paginated_calls += 1
            import json

            return _FakeResp(
                json.dumps(
                    {
                        "documents": [],
                        "pagination": {
                            "page": 1,
                            "page_size": 500,
                            "total_count": 0,
                            "total_pages": 1,
                            "has_next": False,
                            "has_prev": False,
                        },
                        "status_counts": {},
                    }
                ).encode()
            )
        return _FakeResp()

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        idx.run(full=False)

    assert paginated_calls >= 1  # 差分モードでは paginated が呼ばれる
