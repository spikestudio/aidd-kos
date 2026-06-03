<!-- aidd-fw:managed-start -->

# AGENTS.md
<!-- Codex / Open Agent Skills 向け設定ファイル。概要・セットアップ等は README.md 参照 -->

## フレームワーク本体

MANDATORY: セッション開始時に `aidd-framework/FRAMEWORK.md` を必ず読み、そのルールを最優先で適用する。
`aidd-framework/` 配下はフレームワーク本体であり、フレームワーク更新時に最新版で上書きされる。プロジェクト固有の変更を加えてはならない。

<!-- aidd-fw:managed-end -->

## プロジェクト概要

aidd-kos（Agentic Knowledge OS）— LightRAG ナレッジグラフ + MCP サーバー。プロジェクトドキュメントをインデックス化し、Claude Code 等の AI エージェントにナレッジグラフ検索ツールを提供する。

## プロジェクト固有の発見事項

<!-- AI が間違えたパターンを発見した都度、ここに追記する -->
<!-- 形式: - **[要点]**: [説明]（#Issue番号） -->

## ビルド・テストコマンド

```bash
# 依存インストール
uv sync

# テスト
uv run pytest

# サーバー起動
task server:start
```
