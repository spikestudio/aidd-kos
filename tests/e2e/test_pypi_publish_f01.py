"""E2E テスト: F-01 uvx aidd-kos が PyPI から動作する (specs/e2e/19-pypi-publish.md)

LOCAL-FIRST 例外: AC-F19-01・AC-F19-02 は PyPI 公開後のみ完全検証可能。
本テストはローカル代替（ビルド成功・メタデータ完全性・CLI 起動）を検証する。
"""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent


# ── AC-F19-01（ローカル代替）: ビルド成功・メタデータ完全性 ───────────────────


def test_ac_f19_01_e2e_pyproject_has_readme():
    """AC-F19-01: E2E - pyproject.toml に readme フィールドが設定されている"""
    pyproject = REPO_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    assert "readme" in data["project"], "pyproject.toml に readme フィールドがない"


def test_ac_f19_01_e2e_pyproject_has_license():
    """AC-F19-01: E2E - pyproject.toml に license フィールドが設定されている"""
    pyproject = REPO_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    assert "license" in data["project"], "pyproject.toml に license フィールドがない"


def test_ac_f19_01_e2e_pyproject_has_classifiers():
    """AC-F19-01: E2E - pyproject.toml に classifiers が設定されている"""
    pyproject = REPO_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    classifiers = data["project"].get("classifiers", [])
    assert len(classifiers) > 0, "pyproject.toml に classifiers がない"


def test_ac_f19_01_e2e_pyproject_has_project_urls():
    """AC-F19-01: E2E - pyproject.toml に [project.urls] が設定されている"""
    pyproject = REPO_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    urls = data["project"].get("urls", {})
    assert len(urls) > 0, "pyproject.toml に [project.urls] がない"


def test_ac_f19_01_e2e_readme_exists():
    """AC-F19-01: E2E - README.md が存在する（pyproject.toml の readme 参照先）"""
    readme = REPO_ROOT / "README.md"
    assert readme.exists(), "README.md が存在しない"


@pytest.mark.integration
def test_ac_f19_01_e2e_uv_build_succeeds():
    """AC-F19-01: E2E - uv build が exit 0 で完了しビルド成果物が生成される（要: uv インストール済み）"""
    result = subprocess.run(
        ["uv", "build"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"uv build が失敗: {result.stderr}"
    dist = REPO_ROOT / "dist"
    whl_files = list(dist.glob("*.whl"))
    tar_files = list(dist.glob("*.tar.gz"))
    assert len(whl_files) > 0, "dist/ に .whl ファイルが存在しない"
    assert len(tar_files) > 0, "dist/ に .tar.gz ファイルが存在しない"


# ── AC-F19-02（ローカル代替）: CLI 起動確認 ───────────────────────────────────


def test_ac_f19_02_e2e_aidd_kos_version_exits_zero():
    """AC-F19-02: E2E - aidd-kos --version が exit code 0 で動作する"""
    result = subprocess.run(
        ["uv", "run", "aidd-kos", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"aidd-kos --version が失敗: {result.stderr}"
