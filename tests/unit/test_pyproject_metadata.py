"""ユニットテスト: Feature #19 - pyproject.toml PyPI メタデータ検証
(docs/spec/distribution.md Feature F-01)
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _load_pyproject() -> dict:
    with open(PYPROJECT, "rb") as f:
        return tomllib.load(f)


# ── 定数 / 基本フィールド ──────────────────────────────────────────────────────


def test_ac_f19_01_unit_name_is_aidd_kos():
    """AC-F19-01: Unit - pyproject.toml の name が aidd-kos である"""
    data = _load_pyproject()
    assert data["project"]["name"] == "aidd-kos"


def test_ac_f19_01_unit_readme_field_exists():
    """AC-F19-01: Unit - pyproject.toml に readme フィールドが存在する"""
    data = _load_pyproject()
    assert "readme" in data["project"], "readme フィールドがない"


def test_ac_f19_01_unit_readme_points_to_readme_md():
    """AC-F19-01: Unit - readme フィールドが README.md を指している"""
    data = _load_pyproject()
    readme = data["project"].get("readme", "")
    assert "README.md" in str(readme), f"readme が README.md を指していない: {readme}"


def test_ac_f19_01_unit_license_field_exists():
    """AC-F19-01: Unit - pyproject.toml に license フィールドが存在する"""
    data = _load_pyproject()
    assert "license" in data["project"], "license フィールドがない"


def test_ac_f19_01_unit_license_is_mit():
    """AC-F19-01: Unit - license が MIT である"""
    data = _load_pyproject()
    license_field = data["project"].get("license", {})
    license_text = (
        license_field.get("text", "") if isinstance(license_field, dict) else str(license_field)
    )
    assert "MIT" in license_text, f"license が MIT でない: {license_text}"


def test_ac_f19_01_unit_classifiers_exist():
    """AC-F19-01: Unit - pyproject.toml に classifiers が存在する"""
    data = _load_pyproject()
    classifiers = data["project"].get("classifiers", [])
    assert len(classifiers) > 0, "classifiers が空"


def test_ac_f19_01_unit_classifiers_include_python():
    """AC-F19-01: Unit - classifiers に Python バージョン情報が含まれる"""
    data = _load_pyproject()
    classifiers = data["project"].get("classifiers", [])
    python_classifiers = [c for c in classifiers if "Python" in c]
    assert len(python_classifiers) > 0, "classifiers に Python バージョン情報がない"


def test_ac_f19_01_unit_classifiers_include_license():
    """AC-F19-01: Unit - classifiers に License 情報が含まれる"""
    data = _load_pyproject()
    classifiers = data["project"].get("classifiers", [])
    license_classifiers = [c for c in classifiers if "License" in c]
    assert len(license_classifiers) > 0, "classifiers に License 情報がない"


def test_ac_f19_01_unit_project_urls_exist():
    """AC-F19-01: Unit - pyproject.toml に [project.urls] が存在する"""
    data = _load_pyproject()
    urls = data["project"].get("urls", {})
    assert len(urls) > 0, "[project.urls] が空"


def test_ac_f19_01_unit_project_urls_has_homepage():
    """AC-F19-01: Unit - [project.urls] に Homepage または Source が含まれる"""
    data = _load_pyproject()
    urls = data["project"].get("urls", {})
    has_repo = any(k in urls for k in ("Homepage", "Source", "Repository"))
    assert has_repo, f"[project.urls] に Homepage/Source がない: {list(urls.keys())}"


# ── --version コマンド ────────────────────────────────────────────────────────


def test_ac_f19_01_unit_version_defined_in_pyproject():
    """AC-F19-01: Unit - pyproject.toml に version が定義されている"""
    data = _load_pyproject()
    version = data["project"].get("version", "")
    assert version, "version が定義されていない"
    parts = version.split(".")
    assert len(parts) >= 2, f"version が semver 形式でない: {version}"
