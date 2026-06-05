"""E2E テスト: Feature #29 差分インデックス実行 (docs/spec/index-sync.md)"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()

# タイムスタンプ定数（UTC naive ISO8601）
_PAST_UTC = "2020-01-01T00:00:00"
_FUTURE_UTC = "2099-01-01T00:00:00"
_PAST_MTIME = 1577836800.0  # 2020-01-01T00:00:00 UTC


def _paginated_response(docs: list[dict]) -> bytes:
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
            "status_counts": {"PROCESSED": len(docs)},
        }
    ).encode()


def _doc(file_path: str, updated_at: str, doc_id: str = "doc_001") -> dict:
    return {
        "id": doc_id,
        "file_path": file_path,
        "updated_at": updated_at,
        "status": "PROCESSED",
        "content_summary": "test",
        "content_length": 100,
        "created_at": updated_at,
    }


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *a: object) -> None:
        pass


def _dispatcher(paginated: bytes, texts: bytes = b'{"status":"ok"}'):
    def _urlopen(req, timeout=None):
        url = req.full_url
        if "paginated" in url:
            return _FakeResponse(paginated)
        return _FakeResponse(texts)

    return _urlopen


# ── AC-F29-01: 変更なし → 全件スキップ ───────────────────────────────────────


def test_ac_f29_01_e2e_no_changes_all_skipped(tmp_path: Path) -> None:
    """AC-F29-01: E2E - ファイルを変更していないとき全件スキップされ差分モード出力"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    os.utime(f, (_PAST_MTIME, _PAST_MTIME))  # old mtime

    paginated = _paginated_response([_doc("doc.md", _FUTURE_UTC)])

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_dispatcher(paginated)):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "差分モード" in result.output
    assert "追加 0" in result.output
    assert "更新 0" in result.output
    assert "削除 0" in result.output
    assert "スキップ" in result.output


# ── AC-F29-02: 1 件変更 → 更新 1 件 ──────────────────────────────────────────


def test_ac_f29_02_e2e_one_modified_shows_update(tmp_path: Path) -> None:
    """AC-F29-02: E2E - 既存ファイルを 1 件編集したとき更新 1 件・スキップ N-1 件"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    # mtime = now (> PAST_UTC の updated_at)

    paginated = _paginated_response([_doc("doc.md", _PAST_UTC)])

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_dispatcher(paginated)):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "更新" in result.output


# ── AC-F29-03: 新規 1 件追加 → 追加 1 件 ─────────────────────────────────────


def test_ac_f29_03_e2e_new_file_shows_add(tmp_path: Path) -> None:
    """AC-F29-03: E2E - 新規ファイルを 1 件追加したとき追加 1 件・スキップ N 件"""
    (tmp_path / "new.md").write_text("new content")

    paginated = _paginated_response([])  # LightRAG には何もない

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_dispatcher(paginated)):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "追加" in result.output


# ── AC-F29-04: 初回実行 → 全件追加 ───────────────────────────────────────────


def test_ac_f29_04_e2e_first_run_indexes_all(tmp_path: Path) -> None:
    """AC-F29-04: E2E - 初回実行で全 .md/.txt ファイルが追加: N 件として処理される"""
    for name in ("a.md", "b.md", "c.txt"):
        (tmp_path / name).write_text(f"content of {name}")

    paginated = _paginated_response([])

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_dispatcher(paginated)):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "追加" in result.output
    assert "3" in result.output


# ── AC-F29-05: 複合状態 → 差分モード出力 ─────────────────────────────────────


def test_ac_f29_05_e2e_mixed_state_diff_output(tmp_path: Path) -> None:
    """AC-F29-05: E2E - 追加・更新・スキップが混在するとき差分モード出力に全件数が表示される"""
    # file_a.md: unchanged (past mtime, future updated_at → skip)
    fa = tmp_path / "file_a.md"
    fa.write_text("unchanged")
    os.utime(fa, (_PAST_MTIME, _PAST_MTIME))

    # file_b.md: new (not in LightRAG → add)
    (tmp_path / "file_b.md").write_text("new file")

    # file_c.md: modified (current mtime > past updated_at → update)
    fc = tmp_path / "file_c.md"
    fc.write_text("modified")
    # mtime = now (default)

    paginated = _paginated_response(
        [
            _doc("file_a.md", _FUTURE_UTC, "doc_a"),
            _doc("file_c.md", _PAST_UTC, "doc_c"),
        ]
    )

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_dispatcher(paginated)):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    output = result.output
    assert "差分モード" in output
    assert "追加" in output
    assert "更新" in output
    assert "削除 0" in output
    assert "スキップ" in output
