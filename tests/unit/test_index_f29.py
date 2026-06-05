"""ユニットテスト: Feature #29 差分インデックス (IndexOrchestrator 差分ロジック) - in-process 対応"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aidd_kos.index import IndexOrchestrator

_PAST_UTC = "2020-01-01T00:00:00"
_FUTURE_UTC = "2099-01-01T00:00:00"
_PAST_MTIME = 1577836800.0


def _make_doc_status(file_path: str, updated_at: str, doc_id: str = "doc_001"):
    mock_status = MagicMock()
    mock_status.file_path = file_path
    mock_status.updated_at = updated_at
    return mock_status


def _make_mock_rag(docs: list[dict] | None = None):
    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    docs_dict = {}
    if docs:
        docs_dict = {
            d["id"]: _make_doc_status(d["file_path"], d["updated_at"], d["id"]) for d in docs
        }
    mock_rag.get_docs_by_status = AsyncMock(return_value=docs_dict)
    mock_rag.ainsert = AsyncMock()
    mock_rag.adelete_by_doc_id = AsyncMock()
    return mock_rag


# ── _fetch_indexed_docs ───────────────────────────────────────────────────────


def test_ac_f29_01_unit_fetch_returns_empty_when_no_docs(tmp_path: Path) -> None:
    """AC-F29-01: Unit - LightRAG にドキュメントがなければ空 dict を返す"""
    idx = IndexOrchestrator(project_dir=tmp_path)
    mock_rag = _make_mock_rag([])
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = idx._fetch_indexed_docs()
    assert result == {}


def test_ac_f29_01_unit_fetch_returns_file_path_map(tmp_path: Path) -> None:
    """AC-F29-01: Unit - LightRAG のドキュメントを {file_path: {id, updated_at}} で返す"""
    idx = IndexOrchestrator(project_dir=tmp_path)
    mock_rag = _make_mock_rag(
        [{"id": "doc_abc", "file_path": "readme.md", "updated_at": _PAST_UTC}]
    )
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = idx._fetch_indexed_docs()
    assert "readme.md" in result
    assert result["readme.md"]["id"] == "doc_abc"


# ── _classify_files ───────────────────────────────────────────────────────────


def test_ac_f29_03_unit_classify_new_file(tmp_path: Path) -> None:
    """AC-F29-03: Unit - LightRAG にないファイルは new に分類される"""
    f = tmp_path / "new.md"
    f.write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)
    indexed: dict = {}
    new_files, modified_files, _ = idx._classify_files([f], indexed)
    assert f in new_files
    assert f not in modified_files


def test_ac_f29_02_unit_classify_modified_file(tmp_path: Path) -> None:
    """AC-F29-02: Unit - mtime > updated_at のファイルは modified に分類される"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)
    indexed = {"doc.md": {"id": "doc_001", "updated_at": _PAST_UTC}}
    _, modified_files, _ = idx._classify_files([f], indexed)
    assert f in modified_files


def test_ac_f29_01_unit_classify_skip_file(tmp_path: Path) -> None:
    """AC-F29-01: Unit - mtime <= updated_at のファイルは skip に分類される"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    os.utime(f, (_PAST_MTIME, _PAST_MTIME))
    idx = IndexOrchestrator(project_dir=tmp_path)
    indexed = {"doc.md": {"id": "doc_001", "updated_at": _FUTURE_UTC}}
    _, _, skip_files = idx._classify_files([f], indexed)
    assert f in skip_files


# ── run() 差分モード ──────────────────────────────────────────────────────────


def test_ac_f29_05_unit_run_returns_diff_counts(tmp_path: Path) -> None:
    """AC-F29-05: Unit - run() が追加・更新・スキップ件数を含む結果を返す"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)
    mock_rag = _make_mock_rag([])
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
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
    mock_rag = _make_mock_rag([])
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = idx.run()
    assert result["new_count"] == 2
    assert result["skip_count"] == 0


def test_ac_f29_01_unit_run_no_changes_zero_api_calls(tmp_path: Path) -> None:
    """AC-F29-01: Unit - 変更なしのとき ainsert が呼ばれずゼロコストで完了する"""
    f = tmp_path / "doc.md"
    f.write_text("content")
    os.utime(f, (_PAST_MTIME, _PAST_MTIME))
    idx = IndexOrchestrator(project_dir=tmp_path)
    mock_rag = _make_mock_rag([{"id": "doc_001", "file_path": "doc.md", "updated_at": _FUTURE_UTC}])
    with patch("aidd_kos.index.create_lightrag_instance", return_value=mock_rag):
        result = idx.run()
    assert result["skip_count"] == 1
    assert result["new_count"] == 0
    assert result["updated_count"] == 0


def test_ac_f29_01_unit_lightrag_unavailable_exits(tmp_path: Path) -> None:
    """AC-F29-01: Unit - LightRAG 初期化失敗時に SystemExit(1) が発生する"""
    (tmp_path / "doc.md").write_text("content")
    idx = IndexOrchestrator(project_dir=tmp_path)
    with (
        patch("aidd_kos.index.create_lightrag_instance", side_effect=RuntimeError("error")),
        pytest.raises(SystemExit) as exc_info,
    ):
        idx.run()
    assert exc_info.value.code == 1
