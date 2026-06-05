"""E2E テスト: Feature #29 差分インデックス実行 - in-process 対応"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()

_PAST_UTC = "2020-01-01T00:00:00"
_FUTURE_UTC = "2099-01-01T00:00:00"
_PAST_MTIME = 1577836800.0


def _make_doc_status(file_path: str, updated_at: str, doc_id: str = "doc_001"):
    mock_status = MagicMock()
    mock_status.file_path = file_path
    mock_status.updated_at = updated_at
    return mock_status


def _make_rag_with_docs(docs: list[dict]):
    """ドキュメントリストから get_docs_by_status の戻り値を設定した mock rag を返す"""
    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    docs_dict = {d["id"]: _make_doc_status(d["file_path"], d["updated_at"], d["id"]) for d in docs}
    mock_rag.get_docs_by_status = AsyncMock(return_value=docs_dict)
    mock_rag.ainsert = AsyncMock()
    mock_rag.adelete_by_doc_id = AsyncMock()
    return mock_rag


# ── AC-F29-01: 変更なし → 全件スキップ ───────────────────────────────────────


def test_ac_f29_01_e2e_no_changes_all_skipped(tmp_path: Path) -> None:
    """AC-F29-01: E2E - ファイルを変更していないとき全件スキップされ差分モード出力"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    os.utime(f, (_PAST_MTIME, _PAST_MTIME))

    mock_rag = _make_rag_with_docs(
        [{"id": "doc_001", "file_path": "doc.md", "updated_at": _FUTURE_UTC}]
    )

    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "差分モード" in result.output
    assert "追加 0" in result.output
    assert "更新 0" in result.output
    assert "削除 0" in result.output
    assert "スキップ" in result.output


# ── AC-F29-02: 1 件変更 → 更新 1 件 ──────────────────────────────────────────


def test_ac_f29_02_e2e_one_modified_shows_update(tmp_path: Path) -> None:
    """AC-F29-02: E2E - 既存ファイルを 1 件編集したとき更新 1 件"""
    f = tmp_path / "doc.md"
    f.write_text("content")

    mock_rag = _make_rag_with_docs(
        [{"id": "doc_001", "file_path": "doc.md", "updated_at": _PAST_UTC}]
    )

    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "更新" in result.output


# ── AC-F29-03: 新規 1 件追加 → 追加 1 件 ─────────────────────────────────────


def test_ac_f29_03_e2e_new_file_shows_add(tmp_path: Path) -> None:
    """AC-F29-03: E2E - 新規ファイルを 1 件追加したとき追加 1 件"""
    (tmp_path / "new.md").write_text("new content")

    mock_rag = _make_rag_with_docs([])

    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "追加" in result.output


# ── AC-F29-04: 初回実行 → 全件追加 ───────────────────────────────────────────


def test_ac_f29_04_e2e_first_run_indexes_all(tmp_path: Path) -> None:
    """AC-F29-04: E2E - 初回実行で全 .md/.txt ファイルが追加: N 件として処理される"""
    for name in ("a.md", "b.md", "c.txt"):
        (tmp_path / name).write_text(f"content of {name}")

    mock_rag = _make_rag_with_docs([])

    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "追加" in result.output
    assert "3" in result.output


# ── AC-F29-05: 複合状態 → 差分モード出力 ─────────────────────────────────────


def test_ac_f29_05_e2e_mixed_state_diff_output(tmp_path: Path) -> None:
    """AC-F29-05: E2E - 追加・更新・スキップが混在するとき差分モード出力に全件数が表示される"""
    fa = tmp_path / "file_a.md"
    fa.write_text("unchanged")
    os.utime(fa, (_PAST_MTIME, _PAST_MTIME))

    (tmp_path / "file_b.md").write_text("new file")

    fc = tmp_path / "file_c.md"
    fc.write_text("modified")

    mock_rag = _make_rag_with_docs(
        [
            {"id": "doc_a", "file_path": "file_a.md", "updated_at": _FUTURE_UTC},
            {"id": "doc_c", "file_path": "file_c.md", "updated_at": _PAST_UTC},
        ]
    )

    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = runner.invoke(app, ["index", str(tmp_path)])

    assert result.exit_code == 0
    output = result.output
    assert "差分モード" in output
    assert "追加" in output
    assert "更新" in output
    assert "削除 0" in output
    assert "スキップ" in output
