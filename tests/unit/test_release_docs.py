"""ユニットテスト: Feature #21 - RELEASE.md 存在・セクション構造検証
(docs/spec/distribution.md Feature F-03)
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
RELEASE_MD = REPO_ROOT / "RELEASE.md"


def _read_release() -> str:
    return RELEASE_MD.read_text(encoding="utf-8")


def test_ac_f21_01_unit_release_md_exists():
    """AC-F21-01: Unit - RELEASE.md がリポジトリルートに存在する"""
    assert RELEASE_MD.exists(), "RELEASE.md が存在しない"


def test_ac_f21_01_unit_release_md_has_version_section():
    """AC-F21-01: Unit - RELEASE.md にバージョン番号の更新セクションが含まれる"""
    content = _read_release()
    has_version = any(kw in content for kw in ("バージョン", "version", "Version", "CHANGELOG"))
    assert has_version, "RELEASE.md にバージョン番号更新セクションがない"


def test_ac_f21_01_unit_release_md_has_tag_section():
    """AC-F21-01: Unit - RELEASE.md にタグ作成セクションが含まれる"""
    content = _read_release()
    has_tag = any(kw in content for kw in ("タグ", "tag", "Tag", "git tag"))
    assert has_tag, "RELEASE.md にタグ作成セクションがない"


def test_ac_f21_01_unit_release_md_has_github_release_section():
    """AC-F21-01: Unit - RELEASE.md に GitHub Release 作成セクションが含まれる"""
    content = _read_release()
    has_release = any(
        kw in content for kw in ("GitHub Release", "github release", "Release を作成", "gh release")
    )
    assert has_release, "RELEASE.md に GitHub Release 作成セクションがない"
