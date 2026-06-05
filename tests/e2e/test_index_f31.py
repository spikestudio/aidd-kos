"""E2E テスト: Feature #31 全件再構築 (docs/spec/index-sync.md)"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from aidd_kos.cli import app

runner = CliRunner()


class _FakeResp:
    def __init__(self, body: bytes = b'{"status":"ok"}') -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *a: object) -> None:
        pass


# ── AC-F31-01: --full で全件再構築モード出力 ──────────────────────────────────


def test_ac_f31_01_e2e_full_flag_shows_rebuild_mode(tmp_path: Path) -> None:
    """AC-F31-01: E2E - --full 実行で「全件再構築モード: N 件」が stdout に表示される"""
    for name in ("a.md", "b.txt"):
        (tmp_path / name).write_text(f"content {name}")

    with patch("aidd_kos.index.urllib.request.urlopen", return_value=_FakeResp()):
        result = runner.invoke(app, ["index", "--full", str(tmp_path)])

    assert result.exit_code == 0
    assert "全件再構築モード" in result.output
    assert "2" in result.output


# ── AC-F31-02: --full でスキップなし ─────────────────────────────────────────


def test_ac_f31_02_e2e_full_flag_no_skip(tmp_path: Path) -> None:
    """AC-F31-02: E2E - --full 実行でスキップが 0 件（差分判定なし）"""
    (tmp_path / "doc.md").write_text("content")

    paginated_called = []

    def _urlopen(req, timeout=None):
        url = req.full_url
        if "paginated" in url:
            paginated_called.append(url)
        return _FakeResp()

    with patch("aidd_kos.index.urllib.request.urlopen", side_effect=_urlopen):
        result = runner.invoke(app, ["index", "--full", str(tmp_path)])

    assert result.exit_code == 0
    assert "スキップ" not in result.output
    assert len(paginated_called) == 0  # --full のとき paginated は呼ばれない
