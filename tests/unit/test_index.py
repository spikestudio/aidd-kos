"""ユニットテスト: aidd_kos.index (IndexOrchestrator)"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aidd_kos.index import IndexOrchestrator


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / "doc.txt").write_text("doc")
    (tmp_path / "ignore.py").write_text("code")  # Python ファイルは除外
    return tmp_path


def test_ac_f02_01_unit_collect_md_txt_only(project_dir: Path) -> None:
    """AC-F02-01: Unit - .md と .txt ファイルのみ収集される"""
    idx = IndexOrchestrator(project_dir=project_dir)
    files = idx.collect_files()
    exts = {f.suffix for f in files}
    assert ".md" in exts or ".txt" in exts
    assert ".py" not in exts


def test_ac_f02_02_unit_default_to_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-F02-02: Unit - project_dir が None の場合 cwd を使用する"""
    (tmp_path / "doc.md").write_text("doc")
    monkeypatch.chdir(tmp_path)
    idx = IndexOrchestrator(project_dir=None)
    assert idx.project_dir == tmp_path.resolve()


def test_ac_f02_03_unit_returns_file_count(project_dir: Path) -> None:
    """AC-F02-03: Unit - run() がファイル数を含む結果を返す"""
    with patch("aidd_kos.index.urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        idx = IndexOrchestrator(project_dir=project_dir)
        result = idx.run()
    assert result["file_count"] >= 1


def test_ac_f02_04_unit_returns_elapsed_seconds(project_dir: Path) -> None:
    """AC-F02-04: Unit - run() が所要時間（秒）を含む結果を返す"""
    with patch("aidd_kos.index.urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        idx = IndexOrchestrator(project_dir=project_dir)
        result = idx.run()
    assert "elapsed_seconds" in result
    assert result["elapsed_seconds"] >= 0


def test_ac_f02_05_unit_raises_on_lightrag_unavailable(project_dir: Path) -> None:
    """AC-F02-05: Unit - LightRAG 未起動時に LIGHTRAG_UNAVAILABLE エラーを発生させる"""
    import urllib.error

    with patch(
        "aidd_kos.index.urllib.request.urlopen", side_effect=urllib.error.URLError("refused")
    ):
        idx = IndexOrchestrator(project_dir=project_dir)
        with pytest.raises(SystemExit) as exc_info:
            idx.run()
    assert exc_info.value.code == 1
