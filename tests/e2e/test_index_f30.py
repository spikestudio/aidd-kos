"""E2E テスト: Feature #30 削除ファイルのインデックス除去 (docs/spec/index-sync.md)"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()

_PAST_UTC = "2020-01-01T00:00:00"


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


class _FakeResp:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *a: object) -> None:
        pass


# ── AC-F30-01: 削除ファイルが stdout に「削除: 1 件」と表示される ──────────────


def test_ac_f30_01_e2e_deleted_file_shows_in_output(tmp_path: Path) -> None:
    """AC-F30-01: E2E - indexed 済みファイルが filesystem にないとき「削除: 1 件」が stdout に表示される"""
    # filesystem: 空（sample.md は削除済み）
    paginated = _paginated([_doc("sample.md", "doc_sample")])

    def _urlopen(req, timeout=None):
        url = req.full_url
        if "paginated" in url:
            return _FakeResp(paginated)
        if "delete_document" in url:
            return _FakeResp(b'{"status":"deletion_started"}')
        return _FakeResp(b'{"status":"ok"}')

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "削除 1" in result.output


# ── AC-F30-02: DELETE API が正しい doc_id で呼ばれる ─────────────────────────


def test_ac_f30_02_e2e_delete_api_called_with_correct_doc_id(tmp_path: Path) -> None:
    """AC-F30-02: E2E - DELETE /documents/delete_document が doc_ids=['doc_sample'] で呼び出される"""
    paginated = _paginated([_doc("sample.md", "doc_sample")])
    delete_calls: list[dict] = []

    def _urlopen(req, timeout=None):
        url = req.full_url
        if "paginated" in url:
            return _FakeResp(paginated)
        if "delete_document" in url:
            body = json.loads(req.data)
            delete_calls.append(body)
            return _FakeResp(b'{"status":"deletion_started"}')
        return _FakeResp(b'{"status":"ok"}')

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert len(delete_calls) == 1
    assert delete_calls[0]["doc_ids"] == ["doc_sample"]
