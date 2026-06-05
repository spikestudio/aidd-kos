"""ユニットテスト: Feature #30 削除ファイルのインデックス除去"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from aidd_kos.index import IndexOrchestrator

_PAST_UTC = "2020-01-01T00:00:00"


class _FakeResp:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *a: object) -> None:
        pass


def _paginated(docs: list[dict]) -> bytes:
    return json.dumps(
        {
            "documents": docs,
            "pagination": {
                "page": 1,
                "page_size": 500,
                "total_count": len(docs),
                "total_pages": 1,
                "has_next": False,
                "has_prev": False,
            },
            "status_counts": {},
        }
    ).encode()


def _doc(file_path: str, doc_id: str) -> dict:
    return {
        "id": doc_id,
        "file_path": file_path,
        "updated_at": _PAST_UTC,
        "status": "PROCESSED",
        "content_summary": "test",
        "content_length": 10,
        "created_at": _PAST_UTC,
    }


# ── _detect_deleted ──────────────────────────────────────────────────────────


def test_ac_f30_01_unit_detect_deleted_returns_doc_id(tmp_path: Path) -> None:
    """AC-F30-01: Unit - filesystem にないファイルが deleted に検出される"""
    # indexed: sample.md は LightRAG にある
    indexed = {"sample.md": {"id": "doc_sample", "updated_at": _PAST_UTC}}
    # filesystem: sample.md は存在しない
    files: list[Path] = []

    idx = IndexOrchestrator(project_dir=tmp_path)
    deleted = idx._detect_deleted(files, indexed)

    assert "sample.md" in deleted
    assert deleted["sample.md"] == "doc_sample"


def test_ac_f30_01_unit_detect_no_deleted_when_file_exists(tmp_path: Path) -> None:
    """AC-F30-01: Unit - filesystem にあるファイルは deleted に含まれない"""
    f = tmp_path / "doc.md"
    f.write_text("content")

    indexed = {"doc.md": {"id": "doc_001", "updated_at": _PAST_UTC}}
    idx = IndexOrchestrator(project_dir=tmp_path)
    deleted = idx._detect_deleted([f], indexed)

    assert deleted == {}


def test_ac_f30_01_unit_detect_empty_when_nothing_indexed(tmp_path: Path) -> None:
    """AC-F30-01: Unit - indexed が空のとき deleted は空"""
    f = tmp_path / "doc.md"
    f.write_text("content")

    idx = IndexOrchestrator(project_dir=tmp_path)
    deleted = idx._detect_deleted([f], {})

    assert deleted == {}


# ── _delete_docs ─────────────────────────────────────────────────────────────


def test_ac_f30_02_unit_delete_docs_calls_api(tmp_path: Path) -> None:
    """AC-F30-02: Unit - _delete_docs が DELETE API を正しい doc_id で呼び出す"""
    idx = IndexOrchestrator(project_dir=tmp_path)
    captured: list[dict] = []

    def _urlopen(req, timeout=None):
        body = json.loads(req.data)
        captured.append(body)
        return _FakeResp(b'{"status":"deletion_started"}')

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        count = idx._delete_docs({"sample.md": "doc_sample"})

    assert count == 1
    assert len(captured) == 1
    assert captured[0]["doc_ids"] == ["doc_sample"]
    assert captured[0]["delete_file"] is False


def test_ac_f30_01_unit_delete_docs_skips_when_empty(tmp_path: Path) -> None:
    """AC-F30-01: Unit - 削除対象がゼロ件のとき DELETE API を呼ばずに 0 を返す"""
    idx = IndexOrchestrator(project_dir=tmp_path)
    call_count = 0

    def _urlopen(req, timeout=None):
        nonlocal call_count
        call_count += 1
        return _FakeResp(b"{}")

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        count = idx._delete_docs({})

    assert count == 0
    assert call_count == 0


def test_ac_f30_01_unit_delete_docs_lightrag_unavailable(tmp_path: Path) -> None:
    """AC-F30-01: Unit - DELETE API で URLError が発生したとき SystemExit(1)"""
    import urllib.error

    idx = IndexOrchestrator(project_dir=tmp_path)

    with (
        patch(
            "aidd_kos.index.urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        idx._delete_docs({"gone.md": "doc_gone"})
    assert exc_info.value.code == 1


# ── run() 統合 ───────────────────────────────────────────────────────────────


def test_ac_f30_01_unit_run_returns_deleted_count(tmp_path: Path) -> None:
    """AC-F30-01: Unit - run() が deleted_count を返す"""
    # filesystem: 空（全削除）
    idx = IndexOrchestrator(project_dir=tmp_path)
    paginated = _paginated([_doc("gone.md", "doc_gone")])

    def _urlopen(req, timeout=None):
        url = req.full_url
        if "paginated" in url:
            return _FakeResp(paginated)
        if "delete_document" in url:
            return _FakeResp(b'{"status":"deletion_started"}')
        return _FakeResp(b'{"status":"ok"}')

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        result = idx.run()

    assert "deleted_count" in result
    assert result["deleted_count"] == 1


def test_ac_f30_01_unit_run_deleted_count_zero_when_no_deletions(tmp_path: Path) -> None:
    """AC-F30-01: Unit - 削除なしのとき deleted_count は 0"""
    f = tmp_path / "doc.md"
    f.write_text("content")

    idx = IndexOrchestrator(project_dir=tmp_path)

    def _urlopen(req, timeout=None):
        url = req.full_url
        if "paginated" in url:
            return _FakeResp(_paginated([]))
        return _FakeResp(b'{"status":"ok"}')

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        result = idx.run()

    assert result["deleted_count"] == 0
