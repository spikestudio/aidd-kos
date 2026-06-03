# MCP Aggregator 実装

<!-- このファイルは Epic #2 承認時点のスナップショットです。現在の仕様は docs/spec/ を参照してください。 -->

Issue: #2
Milestone: Core MVP（#1）
作成日: 2026-06-03

## 背景・課題

AI 駆動開発エンジニアが LightRAG と CodeGraph を個別にセットアップし、
`~/.claude/settings.json` に複数の MCP サーバーを手動登録する必要があるため導入コストが高い。
また現状のツール名（`query_documents`・`get_status`）はどのエンジン由来か不明確で、
AI Agent が意図的に使い分けしにくい。

## Value Proposition

aidd-kos MCP Server を MCP Aggregator として実装し、`lightrag_*`・`codegraph_*` を
単一エンドポイントに束ねることで、オペレーターの登録作業を 1 件に削減し、
AI Agent がエンジンを認識した上で自律的に使い分けられる状態を実現する。

## ユーザー（ペルソナ）

Primary: AI Agent（Claude Code / Cursor 等）— docs/PROJECT-CHARTER.md §ペルソナ 参照
Secondary: AI 駆動開発エンジニア（オペレーター）— 同上
※ この Epic に関係するペルソナのみ記載。Tertiary（DX 推進担当者/EM）は対象外。

## 成功指標

1. `aidd-kos` 1 本のみを MCP 登録した状態で `lightrag_query`・`codegraph_explore` が応答する（E2E テスト PASS）
2. `kos_status()` 呼び出し時に `available_tools` フィールドに `lightrag_*`・`codegraph_*` 全ツールが含まれること（テストで確認）
3. AI Agent が 1 タスク内で `lightrag_query` と `codegraph_impact` を連続呼び出しし、両ツールの結果を統合した回答を返す E2E テストシナリオが PASS すること

## スコープ外

- LightRAG の embedded 起動（MCP Server 起動時の自動起動）→ Epic #3 で対応
- `aidd-kos install` コマンド → Epic #4 で対応
- ストレージ配置（`.lightrag/` の対象プロジェクト内配置）→ Epic #3 で対応
- 既存ツール名（`query_documents` 等）の後方互換 alias → Phase 1 新規のため不要
- Epic 完了後に `docs/glossary.md` を新ツール名（`lightrag_query` 等）へ更新すること（`/aidd-glossary` 実行）

## この Epic で追加・変更した仕様

| Feature | Spec |
|---------|------|
| F-01: LightRAG ドキュメント検索ツール提供 | docs/spec/mcp-aggregator.md |
| F-02: CodeGraph コード検索ツール統合 | docs/spec/mcp-aggregator.md |
| F-03: 統合ステータス確認 | docs/spec/mcp-aggregator.md |

## 関連ドキュメント

- Business Context: docs/business-context/mcp-aggregator.md
- Epic Issue: #2
- 調査結果: docs/research/fastmcp-aggregator.md
- Architecture: docs/architecture/baseline.md §MCP Aggregator パターン
