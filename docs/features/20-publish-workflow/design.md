# GitHub Release から PyPI へ自動公開されるパイプライン Design

Feature Issue: #20
Epic: #17

## Spec

docs/spec/distribution.md → Feature: F-02 (#20)

## 変更内容

`.github/workflows/publish.yml` を新規作成し、`v*` タグ付き GitHub Release 公開を
トリガーに PyPI へ自動 publish するワークフローを実装する。
認証方式は PyPI OIDC Trusted Publisher（API トークン不要）を採用する。

| 変更ファイル | 変更内容 | 対応 AC |
|------------|---------|---------|
| `.github/workflows/publish.yml` | publish ワークフロー新規作成 | AC-F20-01, AC-F20-02, AC-F20-03 |

**ワークフロー設計:**

```text
on:
  release:
    types: [published]  # v* タグ付き Release 公開がトリガー

permissions:
  id-token: write  # OIDC Trusted Publisher に必要

jobs:
  publish:
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    environment: pypi  # PyPI Trusted Publisher 設定に紐付ける環境
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv build          # wheel + sdist 生成
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist/  # OIDC 認証で PyPI へ公開
```

**LOCAL-FIRST の注記:**
ワークフローの実動作（AC-F20-01/02/03 の本番確認）は GitHub Actions 環境でのみ検証可能。
PyPI OIDC 設定は PyPI 側でプロジェクトの Trusted Publisher を登録してから有効になる。
ローカルでは workflow ファイルの存在・構造正確性をユニットテストで確認する。

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| Spec | docs/spec/distribution.md | Feature: F-02 (#20)（参照）|
| E2E | specs/e2e/20-publish-workflow.md | ワークフロー構造確認シナリオ（新規）|

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| CI 確認 | `.github/workflows/publish.yml` / GitHub Actions | v* タグ Release 作成後にワークフローが起動すること |

## Implementation Tasks

### Spec 追記

- [ ] `specs/e2e/20-publish-workflow.md` 作成

### テスト実装（RED）

- [ ] ユニットテスト `tests/unit/test_publish_workflow.py` 実装
  → 完了条件: publish.yml 未存在のため RED

### 実装

- [ ] `.github/workflows/publish.yml` 作成
  → 完了条件: 全テストが GREEN

### 検証

- [ ] ruff check PASS
- [ ] actionlint（workflow 構文検証）PASS
