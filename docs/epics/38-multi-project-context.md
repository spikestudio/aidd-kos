# マルチプロジェクト対応

> このファイルは Epic #38 承認時点のスナップショットです。
> 現在の仕様は docs/spec/multi-project.md を参照してください。

Issue: #38
Milestone: Operational Excellence（#2）
作成日: 2026-06-05

## 背景・課題

現在の aidd-kos は MCP 設定をユーザーグローバル（~/.claude/settings.json）に書き込み、
LightRAG を固定ポート 9621 の別プロセスとして起動する。
これにより複数プロジェクトを並行開発する際に 2 つの問題が発生する:

1. MCP 登録が最後に install したプロジェクトに固定され、プロジェクト切替のたびに再インストールが必要
2. LightRAG の固定ポートにより、2 つのプロジェクトを同時に開くとポート競合でクラッシュする

## Value Proposition

各プロジェクトを Claude Code で開くだけで、再設定なしにそのプロジェクトの正しい
知識ベースが自動的に参照される状態にする。複数ウィンドウの同時起動でも AI 検索が
独立して動作する。

## ユーザー（ペルソナ）

Primary: AI 駆動開発エンジニア（オペレーター）— 本 Epic はオペレーターの課題解決が主目的
Secondary: AI Agent（Claude Code 等）— 正しいプロジェクトのインデックスを検索に利用する受益者

## 成功指標

- 2 つのプロジェクトで Claude Code を同時に開いた状態で、両方の `lightrag_query` が
  それぞれのプロジェクトのドキュメントを返すこと
- `aidd-kos install` を 1 回実行すれば、そのプロジェクトを Claude Code で開くたびに
  再設定なしに AI 検索が使える状態になること
- 2 プロジェクト同時起動時に `Address already in use` エラーが発生しないこと

## スコープ外

- 同一プロジェクトを複数の Claude Code ウィンドウで同時に開く場合の競合対策
- CodeGraph のマルチプロジェクト対応（本 Epic は LightRAG のみ対象）
- クラウド/リモート LightRAG への接続（ローカル実行のみ）
- グローバル設定（~/.claude/settings.json）の既存エントリの自動移行
  （既存ユーザーはアップグレード後、~/.claude/settings.json の aidd-kos エントリを
  手動で削除することを推奨する）

## この Epic で追加・変更した仕様

| Feature | Spec |
|---------|------|
| F01: プロジェクトレベル MCP 登録 | docs/spec/multi-project.md |
| F02: LightRAG in-process 化 | docs/spec/multi-project.md |

## 関連ドキュメント

- Spec: docs/spec/multi-project.md
- Business Context: docs/business-context/multi-project.md
- Epic Issue: #38
- 後続 Epic: #26（自動同期トリガー）・#27（ステータス可視化）—
  #38 完了後に本格的な運用自動化の効果が最大化される
