# E2E テスト仕様: プロジェクトレベル MCP 登録 (#40)

Feature: #40 プロジェクトレベル MCP 登録
Epic: #38 マルチプロジェクト対応
Spec: docs/spec/multi-project.md → Feature F01

## シナリオ一覧

| AC ID | インターフェース | 前提データ | 操作手順 | 確認内容 |
|-------|---------------|----------|---------|---------|
| AC-F40-01 | CLI | tmp_path に git リポジトリあり、`--global` なし | `aidd-kos install --project-dir {tmp_path}` 実行 | `{tmp_path}/.claude/settings.local.json` に `mcpServers.aidd-kos` エントリが存在し `cwd` フィールドが存在しないこと |
| AC-F40-03 | CLI | `~/.claude/settings.json` に `aidd-kos` エントリが存在する状態 | `aidd-kos install --project-dir {tmp_path}` 実行 | install 前後で `~/.claude/settings.json` の `mcpServers.aidd-kos` フィールドが変更されていないこと |
| AC-F40-04 | CLI | tmp_path に git リポジトリあり | `aidd-kos install --project-dir {tmp_path} --global` 実行 | `~/.claude/settings.json` の `mcpServers.aidd-kos.cwd` が `{tmp_path}` の絶対パスであること |
| AC-F40-05 | CLI | `{tmp_path}/.claude/settings.local.json` に `aidd-kos` エントリが既に存在 | `aidd-kos install --project-dir {tmp_path}` を再実行 | `settings.local.json` の `aidd-kos` エントリが 1 件のみ存在すること（重複なし）|

> AC-F40-02 は Claude Code の実際の MCP 起動挙動に依存するため、
> ユニット・E2E テストでは AC-F40-01（各プロジェクトに独立した設定が書き込まれる）で代替する。

## モック戦略

- `mise install`・`uv sync`・`npx codegraph init`・LightRAG 起動: `subprocess.run/Popen` を patch
- `~/.claude/settings.json`: tmp_path にダミーファイルを作成して ClaudeSettings が読み書き
- `ClaudeSettings._write()`: 実際にファイルを書き込む（tmp_path 配下なので安全）
