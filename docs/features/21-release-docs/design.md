# リリース手順が標準化・ドキュメント化される Design

Feature Issue: #21
Epic: #17

## Spec

docs/spec/distribution.md → Feature: F-03 (#21)

## 変更内容

`RELEASE.md` を新規作成し、メンテナーがリリース作業を実施するための手順書を整備する。

| 変更ファイル | 変更内容 | 対応 AC |
|------------|---------|---------|
| `RELEASE.md` | リリース手順書を新規作成 | AC-F21-01 |

**RELEASE.md 必須セクション（AC-F21-01 要件）:**

1. バージョン番号の更新（pyproject.toml の version 変更）
2. タグの作成（`git tag v0.x.y` → `git push origin v0.x.y`）
3. GitHub Release の作成（GitHub UI または gh コマンド）

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| Spec | docs/spec/distribution.md | Feature: F-03 (#21)（参照）|
| E2E | specs/e2e/21-release-docs.md | RELEASE.md 存在・セクション確認（新規）|

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| 文書確認 | `RELEASE.md` | 3 セクションが存在すること（機械的確認可能）|

## Implementation Tasks

- [x] `specs/e2e/21-release-docs.md` 作成
- [x] ユニットテスト `tests/unit/test_release_docs.py` 実装（RED）
- [x] `RELEASE.md` 作成（GREEN）
- [x] lint PASS
