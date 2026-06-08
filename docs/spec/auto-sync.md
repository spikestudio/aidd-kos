# Spec: 自動同期トリガー（Epic #26）

## Feature F01: コミット後の自動インデックス設定手順の提供

Issue: #[Feature Issue番号 — 作成後に更新]
Epic: #26

### Stories

| ID | As a | I want to | So that |
|----|------|-----------|---------|
| S1 | AI 駆動開発エンジニア | git commit のたびに自動でインデックスが更新されるよう lefthook を設定したい | インデックス更新を手動で実行し忘れることなく AI Agent が常に最新情報を参照できる |

### Acceptance Criteria

| AC ID | Story | Given | When | Then |
|-------|-------|-------|------|------|
| AC-F[TBD]-01 | S1 | docs/playbook/auto-sync.md が存在する | オペレーターがファイルを読む | `aidd-kos index \|\| true` を含む lefthook.yml の post-commit 設定ブロックが記載されていること |
| AC-F[TBD]-02 | S1 | docs/playbook/auto-sync.md が存在する | オペレーターがファイルを読む | `lefthook install` コマンドがセットアップ手順として記載されていること |
| AC-F[TBD]-03 | S1 | docs/playbook/auto-sync.md が存在する | オペレーターがファイルを読む | `\|\| true` によってインデックス失敗がコミットを中断しない理由の説明が記載されていること |
