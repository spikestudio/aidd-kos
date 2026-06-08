# 自動同期トリガー

> このファイルは Epic #26 承認時点のスナップショットです。
> 現在の仕様は docs/spec/ を参照してください。

Issue: #26
Milestone: Operational Excellence（#2）
作成日: 2026-06-08

## 背景・課題

Epic #25 で `aidd-kos index` が差分インデックスに対応したが、
オペレーターが手動で実行しなければ AI Agent のインデックスが古くなる。
git commit 後にインデックス更新を忘れると、AI Agent は古い情報を返し続ける。

## Value Proposition

git commit のたびにオペレーターが手動操作なしにインデックスが最新化される状態にする。
AI Agent は常に最新のナレッジグラフを参照して回答精度を維持できる。

## ユーザー（ペルソナ）

Primary: AI 駆動開発エンジニア（オペレーター）
Secondary: AI Agent（Claude Code 等）

## 成功指標

- docs/playbook/auto-sync.md に lefthook.yml の設定例と lefthook install の手順が含まれること
- ドキュメントに記載の手順を実行後、git commit を行うと `aidd-kos index` が実行されること
  （ローカルで `lefthook run post-commit` を実行して確認可能）

## スコープ外

- aidd-kos install による lefthook.yml の自動書き換え
- AI Agent ツール実行トリガーによる同期（別途検討）
- watchdog 等のファイル監視デーモン
- lefthook 未導入プロジェクトへの lefthook インストール手順

## この Epic で追加・変更した仕様

| Feature | Spec |
|---------|------|
| F01: コミット後の自動インデックス設定手順の提供 | docs/spec/auto-sync.md |

## 関連ドキュメント

- Business Context: docs/business-context/auto-sync.md
- Epic Issue: #26
- 依存 Epic: #25（差分インデックス基盤）
