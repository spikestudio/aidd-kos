<!-- このファイルは Epic #3 承認時点のスナップショットです。現在の仕様は docs/spec/ を参照してください。 -->

# Embedded 起動 & ストレージ移動

Issue: #3
Milestone: Core MVP（#1）
作成日: 2026-06-03

## 背景・課題

MCP Server（aidd-kos）を利用するには、LightRAG を手動で別途起動する必要がある。
また `.lightrag/` ディレクトリが対象プロジェクトではなく aidd-kos 自身のディレクトリを参照しているため、
AI Agent が対象プロジェクトのナレッジを検索できない（TD-05・TD-06）。
CodeGraph についても cwd 参照パスが対象プロジェクトを正しく指しているか確認・修正が必要。
結果として「`uvx aidd-kos serve` だけで使える」というビジョンを達成できていない。

## Value Proposition

`uvx aidd-kos serve` を対象プロジェクトで実行すると、LightRAG がサーバー起動と連動して自動起動し、
`.lightrag/` ディレクトリが対象プロジェクト内に配置される。
手動起動不要で、AI Agent は接続後すぐにプロジェクト固有のナレッジ検索・コード検索が使える状態になる。

## ユーザー（ペルソナ）

Primary: AI Agent（Claude Code / Cursor 等）— docs/PROJECT-CHARTER.md §3 ペルソナ 参照
Secondary: AI 駆動開発エンジニア（オペレーター）— 同上

## 成功指標

1. `uvx aidd-kos serve` 実行後、ナレッジエンジンの手動起動なしで `lightrag_query` が `LIGHTRAG_UNAVAILABLE` エラーなしに応答すること（E2E テスト PASS）
2. MCP サーバー起動から 30 秒以内に `lightrag_query` が最初の検索結果を返すこと（E2E テスト PASS）
3. `.lightrag/` が対象プロジェクトのルートディレクトリ配下に作成・更新されること（ファイルシステム確認）
4. MCP サーバー停止後にナレッジエンジンのバックグラウンドプロセスが終了していること（プロセス確認）

## スコープ外

- LightRAG のクラスター化・冗長化
- 複数プロジェクトの `.lightrag/` を同一サーバーから同時管理
- LightRAG 起動設定のカスタマイズ（ポート以外）
- CodeGraph の起動方式の変更（CodeGraph は NpxStdioTransport 経由で既に自動起動済み。本 Epic では参照パスの確認・修正のみ）

## この Epic で追加・変更した仕様

> AC ID は Feature Issue 作成後（Step 6）に確定番号へ置換される。ドラフト段階では仮番号（F01/F02）を使用。

| Feature | Spec |
|---------|------|
| F-01: ナレッジ検索が MCP サーバー起動直後から利用可能になる（#TBD） | docs/spec/embedded-startup.md |
| F-02: 全ナレッジエンジンが対象プロジェクトを正しく参照する（#TBD） | docs/spec/embedded-startup.md |

## 関連ドキュメント

- Business Context: docs/business-context/embedded-startup.md
- Epic Issue: #3
