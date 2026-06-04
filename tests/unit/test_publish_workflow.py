"""ユニットテスト: Feature #20 - GitHub Actions publish ワークフロー構造検証
(docs/spec/distribution.md Feature F-02)
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "publish.yml"


def _read_workflow() -> str:
    return PUBLISH_WORKFLOW.read_text(encoding="utf-8")


# ── ファイル存在確認 ──────────────────────────────────────────────────────────


def test_ac_f20_01_unit_publish_workflow_exists():
    """AC-F20-01: Unit - .github/workflows/publish.yml が存在する"""
    assert PUBLISH_WORKFLOW.exists(), ".github/workflows/publish.yml が存在しない"


# ── トリガー確認 ──────────────────────────────────────────────────────────────


def test_ac_f20_01_unit_workflow_triggers_on_release_published():
    """AC-F20-01: Unit - ワークフローが release: published トリガーを持つ"""
    content = _read_workflow()
    assert "published" in content, "ワークフローに published トリガーがない"
    assert "release" in content, "ワークフローに release トリガーがない"


def test_ac_f20_01_unit_workflow_filters_v_tags():
    """AC-F20-01: Unit - ワークフローが v* タグ付き Release のみを対象とする"""
    content = _read_workflow()
    assert "refs/tags/v" in content or "tags/v*" in content, "ワークフローに v* タグフィルタがない"


# ── ビルド・公開ステップ確認 ──────────────────────────────────────────────────


def test_ac_f20_02_unit_workflow_has_uv_build_step():
    """AC-F20-02: Unit - ワークフローに uv build ステップが含まれる"""
    content = _read_workflow()
    assert "uv build" in content, "ワークフローに uv build ステップがない"


def test_ac_f20_02_unit_workflow_has_pypi_publish_action():
    """AC-F20-02: Unit - ワークフローに pypa/gh-action-pypi-publish が含まれる"""
    content = _read_workflow()
    assert "pypa/gh-action-pypi-publish" in content, (
        "ワークフローに pypa/gh-action-pypi-publish アクションがない"
    )


# ── OIDC 設定確認 ─────────────────────────────────────────────────────────────


def test_ac_f20_02_unit_workflow_has_oidc_permission():
    """AC-F20-02: Unit - ワークフローに OIDC Trusted Publisher 用の id-token 権限がある"""
    content = _read_workflow()
    assert "id-token" in content, "ワークフローに id-token 権限がない（OIDC 認証に必要）"


# ── 失敗ステータス伝播確認（AC-F20-03） ───────────────────────────────────────


def test_ac_f20_03_unit_workflow_failure_propagates():
    """AC-F20-03: Unit - ワークフローに continue-on-error: true が含まれない（失敗ステータスが伝播する）"""
    content = _read_workflow()
    assert "continue-on-error: true" not in content, (
        "continue-on-error: true が設定されているため失敗ステータスが伝播しない"
    )
