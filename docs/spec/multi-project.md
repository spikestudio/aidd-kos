# Spec: Multi-Project（マルチプロジェクト対応）

Epic: #38 マルチプロジェクト対応
Milestone: Operational Excellence（#2）

---

## Feature: プロジェクトレベル MCP 登録 (F01)

### Story S1: 複数プロジェクトを切り替えなしに使える

As an AI 駆動開発エンジニア（オペレーター）,
I want to use each project's knowledge base without re-running aidd-kos install
when switching between multiple projects,
So that Claude Code restarts are not needed when switching projects.

### Story S2: --global オプションで旧動作を維持できる

As an AI 駆動開発エンジニア（オペレーター）,
I want to register aidd-kos in user-global settings with the --global option,
So that projects using global settings can be upgraded without changing configuration.

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F40-01 | プロジェクト A のルートディレクトリで `--global` オプションなし | `uvx aidd-kos install` を実行する | `{プロジェクト A}/.claude/settings.local.json` の `mcpServers.aidd-kos` エントリが存在し、かつ `cwd` フィールドが存在しないこと |
| AC-F40-02 | プロジェクト A とプロジェクト B それぞれに `install` 済みで、各プロジェクトに異なるドキュメントをインデックス済み | プロジェクト A の Claude Code ウィンドウで `lightrag_query` を実行する | プロジェクト A のドキュメントが検索結果に含まれ、プロジェクト B 固有のドキュメントが含まれないこと |
| AC-F40-03 | `~/.claude/settings.json` に `aidd-kos` エントリが存在する状態で | `uvx aidd-kos install` を実行する | install 前後で `~/.claude/settings.json` の `mcpServers.aidd-kos` フィールドの内容が変更されていないこと |
| AC-F40-04 | プロジェクトルートで `--global` オプションを指定 | `uvx aidd-kos install --global` を実行する | `~/.claude/settings.json` の `mcpServers.aidd-kos` エントリに `"cwd"` フィールドが存在し、プロジェクトルートの絶対パスが設定されていること |
| AC-F40-05 | `.claude/settings.local.json` の `mcpServers.aidd-kos` エントリが既に存在する状態で | `uvx aidd-kos install` を再実行する | `.claude/settings.local.json` の `mcpServers.aidd-kos` エントリが 1 件のみ存在すること（重複追記なし）|

---

## Feature: LightRAG in-process 化 (F02)

### Story S3: 複数 Claude Code ウィンドウで同時に動作する

As an AI 駆動開発エンジニア（オペレーター）,
I want each project's AI search to operate independently even when multiple
Claude Code windows for different projects are open simultaneously,
So that knowledge search failures due to port conflicts during parallel development are eliminated.

### Story S4: ポート設定なしに AI 検索を使える

As an AI 駆動開発エンジニア（オペレーター）,
I want to use AI search without being aware of port numbers or server settings
after aidd-kos install,
So that port conflict checks and configuration changes are unnecessary,
lowering the barrier to installation.

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F41-01 | プロジェクト A で aidd-kos MCP が起動済み | プロジェクト B でも aidd-kos MCP を起動する | プロジェクト A の `lightrag_query` がエラーなしに応答を返すこと |
| AC-F41-02 | プロジェクト A とプロジェクト B の両方で aidd-kos MCP が起動済みで、各プロジェクトに異なるドキュメントをインデックス済み | プロジェクト B の `lightrag_query` でプロジェクト B 固有の内容を検索する | プロジェクト B のドキュメントが返され、プロジェクト A のドキュメントが含まれないこと |
| AC-F41-03 | aidd-kos MCP サーバーが起動している | システムの TCP ポート一覧を取得する | 9621 番ポートが LISTEN 状態にないこと |
| AC-F41-04 | `LIGHTRAG_PORT` 環境変数が未設定の状態で | `aidd-kos serve` を起動して `lightrag_query` を呼び出す | ポート設定なしでクエリが成功し、レスポンスが返ること |
| AC-F41-05 | aidd-kos MCP サーバーが起動している | 実行中のプロセス一覧を取得する | `lightrag_server` という名称のプロセスが存在しないこと |
