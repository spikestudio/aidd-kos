# uvx aidd-kos が PyPI から動作する Design

Feature Issue: #19
Epic: #17

## Spec

docs/spec/distribution.md → Feature: F-01 (#19)

## 変更内容

`pyproject.toml` に PyPI 公開に必須のメタデータを追加し、`uv build` でビルド可能な状態にする。
あわせて `docs/PROJECT-CHARTER.md` §6 配布制約の「PyPI は将来対応」を実績に更新する。

| 変更ファイル | 変更内容 | 対応 AC |
|------------|---------|---------|
| `pyproject.toml` | `readme`・`license`・`classifiers`・`[project.urls]` を追加 | AC-F19-01, AC-F19-02 |
| `docs/PROJECT-CHARTER.md` §6 | 「PyPI は将来対応」→「PyPI 経由（Phase 1 Core MVP で対応済み）」| Epic コンテキスト整合 |

**pyproject.toml 追加内容:**

```toml
[project]
# 既存: name / version / description / requires-python / dependencies
readme = "README.md"
license = {text = "MIT"}
classifiers = [
  "Development Status :: 3 - Alpha",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Topic :: Software Development :: Libraries :: Python Modules",
]
keywords = ["mcp", "ai", "knowledge-graph", "lightrag", "codegraph"]

[project.urls]
Homepage = "https://github.com/spikestudio/aidd-kos"
Source = "https://github.com/spikestudio/aidd-kos"
Issues = "https://github.com/spikestudio/aidd-kos/issues"
```

**LOCAL-FIRST VERIFICATION の注記:**

AC-F19-01（`uvx aidd-kos install` が PyPI から動作する）と AC-F19-02（`uvx aidd-kos@latest serve`）は
PyPI への実際の公開後でのみ検証可能。FRAMEWORK.md §LOCAL-FIRST VERIFICATION の例外条件
「ローカル再現が物理的に不可能な環境依存」に該当する。
ローカルでは `uv build` の成功とメタデータ完全性を確認し、PyPI 疎通確認は F-02 完了後に CI/CD 経由で実施する。

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| Spec | docs/spec/distribution.md | Feature: F-01 (#19)（参照）|
| E2E | specs/e2e/19-pypi-publish.md | uvx インストール・サーバー起動シナリオ（新規）|

※ openapi.yaml・schema.sql・screens の変更なし（パッケージング設定のみ）

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| ビルド確認 | CI / `uv build` | wheel・sdist が生成されること（exit 0）|
| メタデータ検証 | CI / `uv run twine check dist/*` | PyPI 要件を満たすメタデータであること（exit 0）|

## Implementation Tasks

### Spec 追記

- [x] `specs/e2e/19-pypi-publish.md` 作成
  → 完了条件: AC-F19-01・AC-F19-02 のシナリオが含まれる

### 実装

- [x] `pyproject.toml` に `readme`・`license`・`classifiers`・`keywords`・`[project.urls]` を追加
  → 完了条件: `uv build` が exit 0、`dist/` に `.whl` と `.tar.gz` が生成される

- [x] `docs/PROJECT-CHARTER.md` §6 配布制約を更新
  → 完了条件: 「PyPI は将来対応」→「PyPI 経由（Phase 1 Core MVP で対応済み）」に変更されている

### 検証

- [x] README.md の実在確認（既確認: ✅ 存在する）
  → 完了条件: `ls README.md` が exit 0

- [x] `aidd-kos install` コマンドの実在確認（既確認: ✅ aidd_kos/cli.py に定義済み）
  → 完了条件: `uv run aidd-kos --help` に `install` が表示される

- [x] twine を dev-dependencies に追加（`uv run twine check` 実行のため）
  → 完了条件: `uv run twine --version` が exit 0

- [x] ローカルビルド確認
  → 完了条件: `uv build && uv run twine check dist/*` が exit 0

- [x] パッケージメタデータ完全性確認
  → 完了条件: `readme`・`license`・`classifiers`・`urls` が pyproject.toml に存在する

- [x] lint・型チェック
  → 完了条件: `uv run ruff check .` が exit 0

### PyPI 疎通確認（CI/CD 経由・F-02 完了後）

- [ ] TestPyPI での動作確認
  → 完了条件: `uvx --index-url https://test.pypi.org/simple/ aidd-kos --version` が exit 0
  → 注: F-02 の publish ワークフロー完成後に実施。PR コメントに理由を明記する
