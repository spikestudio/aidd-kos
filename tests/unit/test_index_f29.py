"""ユニットテスト: Feature #29 差分インデックス (IndexOrchestrator 差分ロジック)"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from aidd_kos.index import IndexOrchestrator

# タイムスタンプ定数
_PAST_UTC = "2020-01-01T00:00:00"
_FUTURE_UTC = "2099-01-01T00:00:00"
_PAST_MTIME = 1577836800.0  # 2020-01-01T00:00:00 UTC


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


def _doc(file_path: str, updated_at: str, doc_id: str = "doc_001") -> dict:
    return {
        "id": doc_id,
        "file_path": file_path,
        "updated_at": updated_at,
        "status": "PROCESSED",
        "content_summary": "test",
        "content_length": 10,
        "created_at": updated_at,
    }


class _FakeResp:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *a: object) -> None:
        pass


# ── _fetch_indexed_docs ───────────────────────────────────────────────────────


def test_ac_f29_01_unit_fetch_returns_empty_when_no_docs(tmp_path: Path) -> None:
    """AC-F29-01: Unit - LightRAG にドキュメントがなければ空 dict を返す"""
    idx = IndexOrchestrator(project_dir=tmp_path)

    with patch(
        "aidd_kos.index.urllib.request.urlopen",
        return_value=_FakeResp(_paginated([])),
    ):
        result = idx._fetch_indexed_docs()

    assert result == {}


def test_ac_f29_01_unit_fetch_returns_file_path_map(tmp_path: Path) -> None:
    """AC-F29-01: Unit - LightRAG のドキュメントを {file_path: {id, updated_at}} で返す"""
    idx = IndexOrchestrator(project_dir=tmp_path)
    docs = [_doc("readme.md", _PAST_UTC, "doc_abc")]

    with patch(
        "aidd_kos.index.urllib.request.urlopen",
        return_value=_FakeResp(_paginated(docs)),
    ):
        result = idx._fetch_indexed_docs()

    assert "readme.md" in result
    assert result["readme.md"]["id"] == "doc_abc"
    assert result["readme.md"]["updated_at"] == _PAST_UTC


def test_ac_f29_01_unit_fetch_handles_pagination(tmp_path: Path) -> None:
    """AC-F29-01: Unit - ページネーション has_next=True のとき 2 ページ目も取得する"""
    idx = IndexOrchestrator(project_dir=tmp_path)

    page1 = json.dumps(
        {
            "documents": [_doc("a.md", _PAST_UTC, "doc_a")],
            "pagination": {
                "page": 1,
                "page_size": 1,
                "total_count": 2,
                "total_pages": 2,
                "has_next": True,
                "has_prev": False,
            },
            "status_counts": {},
        }
    ).encode()

    page2 = json.dumps(
        {
            "documents": [_doc("b.md", _PAST_UTC, "doc_b")],
            "pagination": {
                "page": 2,
                "page_size": 1,
                "total_count": 2,
                "total_pages": 2,
                "has_next": False,
                "has_prev": True,
            },
            "status_counts": {},
        }
    ).encode()

    responses = [_FakeResp(page1), _FakeResp(page2)]
    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=responses):
        result = idx._fetch_indexed_docs()

    assert "a.md" in result
    assert "b.md" in result


# ── _classify_files ───────────────────────────────────────────────────────────


def test_ac_f29_03_unit_classify_new_file(tmp_path: Path) -> None:
    """AC-F29-03: Unit - LightRAG にないファイルは new に分類される"""
    f = tmp_path / "new.md"
    f.write_text("content")

    idx = IndexOrchestrator(project_dir=tmp_path)
    indexed: dict = {}
    new_files, modified_files, skip_files = idx._classify_files([f], indexed)

    assert f in new_files
    assert f not in modified_files
    assert f not in skip_files


def test_ac_f29_02_unit_classify_modified_file(tmp_path: Path) -> None:
    """AC-F29-02: Unit - mtime > updated_at のファイルは modified に分類される"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    # mtime = now > _PAST_UTC

    idx = IndexOrchestrator(project_dir=tmp_path)
    indexed = {"doc.md": {"id": "doc_001", "updated_at": _PAST_UTC}}
    new_files, modified_files, skip_files = idx._classify_files([f], indexed)

    assert f in modified_files
    assert f not in new_files
    assert f not in skip_files


def test_ac_f29_01_unit_classify_skip_file(tmp_path: Path) -> None:
    """AC-F29-01: Unit - mtime <= updated_at のファイルは skip に分類される"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    os.utime(f, (_PAST_MTIME, _PAST_MTIME))

    idx = IndexOrchestrator(project_dir=tmp_path)
    indexed = {"doc.md": {"id": "doc_001", "updated_at": _FUTURE_UTC}}
    new_files, modified_files, skip_files = idx._classify_files([f], indexed)

    assert f in skip_files
    assert f not in new_files
    assert f not in modified_files


def test_ac_f29_05_unit_classify_mixed(tmp_path: Path) -> None:
    """AC-F29-05: Unit - 混在状態で new/modified/skip を正しく分類する"""
    fa = tmp_path / "a.md"
    fa.write_text("unchanged")
    os.utime(fa, (_PAST_MTIME, _PAST_MTIME))

    fb = tmp_path / "b.md"
    fb.write_text("new file")

    fc = tmp_path / "c.md"
    fc.write_text("modified")
    # mtime = now

    idx = IndexOrchestrator(project_dir=tmp_path)
    indexed = {
        "a.md": {"id": "doc_a", "updated_at": _FUTURE_UTC},
        "c.md": {"id": "doc_c", "updated_at": _PAST_UTC},
    }
    new_files, modified_files, skip_files = idx._classify_files([fa, fb, fc], indexed)

    assert fb in new_files
    assert fc in modified_files
    assert fa in skip_files


# ── run() 差分モード出力 ───────────────────────────────────────────────────────


def test_ac_f29_05_unit_run_returns_diff_counts(tmp_path: Path) -> None:
    """AC-F29-05: Unit - run() が追加・更新・スキップ件数を含む結果を返す"""
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

    assert "new_count" in result
    assert "updated_count" in result
    assert "skip_count" in result
    assert result["new_count"] == 1


def test_ac_f29_04_unit_run_first_run_all_new(tmp_path: Path) -> None:
    """AC-F29-04: Unit - 初回実行（LightRAG 空）では全ファイルが new_count に計上される"""
    for name in ("a.md", "b.txt"):
        (tmp_path / name).write_text(f"content {name}")

    idx = IndexOrchestrator(project_dir=tmp_path)

    def _urlopen(req, timeout=None):
        url = req.full_url
        if "paginated" in url:
            return _FakeResp(_paginated([]))
        return _FakeResp(b'{"status":"ok"}')

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        result = idx.run()

    assert result["new_count"] == 2
    assert result["skip_count"] == 0


def test_ac_f29_01_unit_run_no_changes_zero_api_calls(tmp_path: Path) -> None:
    """AC-F29-01: Unit - 変更なしのとき texts API が呼ばれずゼロコストで完了する"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    os.utime(f, (_PAST_MTIME, _PAST_MTIME))

    idx = IndexOrchestrator(project_dir=tmp_path)
    texts_call_count = 0

    def _urlopen(req, timeout=None):
        nonlocal texts_call_count
        url = req.full_url
        if "paginated" in url:
            return _FakeResp(_paginated([_doc("doc.md", _FUTURE_UTC)]))
        texts_call_count += 1
        return _FakeResp(b'{"status":"ok"}')

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        result = idx.run()

    assert texts_call_count == 0
    assert result["skip_count"] == 1
    assert result["new_count"] == 0
    assert result["updated_count"] == 0


@pytest.mark.parametrize("exc_on_url", ["paginated", "texts"])
def test_ac_f29_01_unit_lightrag_unavailable_exits(tmp_path: Path, exc_on_url: str) -> None:
    """AC-F29-01: Unit - LightRAG 未起動時に SystemExit(1) が発生する"""
    import urllib.error

    (tmp_path / "doc.md").write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)

    def _urlopen(req, timeout=None):
        url = req.full_url
        if exc_on_url in url:
            raise urllib.error.URLError("refused")
        return _FakeResp(_paginated([]))

    with (
        patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen),
        pytest.raises(SystemExit) as exc_info,
    ):
        idx.run()
    assert exc_info.value.code == 1
