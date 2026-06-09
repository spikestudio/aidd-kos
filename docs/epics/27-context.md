# ステータス & エラー可視化

> このファイルは Epic #27 承認時点のスナップショットです。
> 現在の仕様は docs/spec/status-visibility.md を参照してください。

Issue: #27
Milestone: Operational Excellence（#2）
作成日: 2026-06-09

## 背景・課題

Epic #25 で差分インデックスが実装され `aidd-kos index` が日常コマンドになった。
しかし現在の `aidd-kos status` は `ready` / `indexing` / `unavailable` の 3 値しか返さず、
「インデックスが最新か（Stale 状態）」「前回の失敗原因は何か」「今何件処理中か」がわからない。
AI Agent はインデックスが古い状態を検知できないため古い情報で回答し続けるリスクがあり、
オペレーターはトラブル時にログを掘るしかない。

## Value Proposition

`aidd-kos status` の 1 回実行で、インデックスの正確な状態（Ready / Stale / Indexing / Error）・
エラー発生時の原因の種類と次に実行すべきコマンド・インデックス中のプログレスが把握できる。
追加操作ゼロ。

## ユーザー（ペルソナ）

Primary: AI Agent（Claude Code / Cursor 等）— ステータス確認機能でインデックスの鮮度を検知し、
         Stale・Error な場合に自律的にオペレーターへ再同期を促す判断ができる
Secondary: AI 駆動開発エンジニア（オペレーター）— `aidd-kos status` CLI で
           インデックス状態を確認しトラブルシューティングを行う

## 成功指標

- `aidd-kos status` が Ready / Stale / Indexing / Error の 4 値を返すこと
- Stale: プロジェクト配下の `.md`/`.txt` ファイルが最終インデックス実行後に 1 件以上変更されたとき
  `stale` を返すこと
- エラー発生時にエラーの種類と次に実行すべきコマンドがターミナルに表示されること
- Indexing 時に処理済み件数・総件数が表示されること
- AI Agent がステータス確認機能を通じてインデックスの正確な状態と進捗情報を取得できること

## スコープ外

- CodeGraph の状態細分化（本 Epic は LightRAG のみ対象）
- `--watch` / `--follow` 等の継続監視モード（ポーリング実行）
- Web UI / ダッシュボード形式のステータス表示
- プッシュ通知・アラート機能
- エラーログの自動収集・送信

## この Epic で追加・変更した仕様

| Feature | Spec |
|---------|------|
| F01: インデックス状態の 4 値可視化・エラー診断（CLI + MCP）| docs/spec/status-visibility.md |
| F02: インデックス処理中の進捗表示 | docs/spec/status-visibility.md |

## 関連ドキュメント

- Business Context: docs/business-context/status-visibility.md
- Epic Issue: #27
- 依存 Epic: #25（インデックス差分更新）
