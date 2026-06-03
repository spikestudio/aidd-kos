# aidd-kos CLI & Install フロー

<!-- このファイルは Epic #4 承認時点のスナップショットです。現在の仕様は docs/spec/ を参照してください。 -->

Issue: #4
Milestone: Core MVP（#1）
作成日: 2026-06-03

## 背景・課題

AI 駆動開発エンジニアが aidd-kos を導入するには、LightRAG（Python）・CodeGraph（npm）の
インストール・サーバー起動・インデックス構築・MCP 登録など多くの手順を個別に実行する必要があり、
手順が多くミスが起きやすい。

## Value Proposition

mise がインストール済みの環境で `uvx aidd-kos install` の 1 コマンドを実行するだけで、
LightRAG・CodeGraph のインストール〜インデックス構築〜MCP 登録を全自動化し、
Claude Code 再起動後すぐにナレッジ検索が使える状態にする。

## ユーザー（ペルソナ）

Primary: AI Agent（Claude Code / Cursor 等）— docs/PROJECT-CHARTER.md §ペルソナ 参照
Secondary: AI 駆動開発エンジニア（オペレーター）

> **注記:** この Epic の主操作者は Secondary のオペレーターだが、
> install の恩恵を受ける直接ユーザーは Primary の AI Agent。
> AC はオペレーター操作の観点で記述し、ゴールは AI Agent が即座に使える状態を達成すること。

## 成功指標

1. `uvx aidd-kos install` 実行後、Claude Code 再起動で AI Agent がナレッジ検索を実行できる（100 ドキュメント以下・インデックス構築を除く 10 分以内・E2E テスト PASS）
2. install 完了後に `aidd-kos status` で LightRAG・CodeGraph 両エンジンが `ready` を返すこと
3. aidd-kos 自身のプロジェクトに install を実行し、設計方針に関する自然言語クエリで関連ドキュメントが返ること（E2E テスト PASS）

## スコープ外

- LightRAG の embedded 起動（MCP Server 起動時の自動起動）→ Epic #3 で対応
- ストレージ配置の変更（.lightrag/ パスの AIDD_KOS_PROJECT_DIR 対応）→ Epic #3 で対応
- MCP Aggregator（lightrag_*/codegraph_* ツール統合）→ Epic #2 で対応
- aidd-kos のバージョンアップ・アンインストール機能（将来 Epic / Phase 未定）
- 後続 Epic 実行順: 本 Epic（#4）→ #2（MCP Aggregator）→ #3（Embedded 起動・ストレージ移動）

## この Epic で追加・変更した仕様

| Feature | Spec |
|---------|------|
| F-01: install コマンド | docs/spec/install.md |
| F-02: index コマンド | docs/spec/install.md |
| F-03: status コマンド | docs/spec/install.md |

## 関連ドキュメント

- Business Context: docs/business-context/install.md
- Epic Issue: #4
