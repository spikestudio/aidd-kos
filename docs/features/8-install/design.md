# install コマンド（全自動セットアップ）Design

Feature Issue: #8
Epic: #4

## Spec

docs/spec/install.md → Feature F-01

## 実装アーキテクチャ

baseline.md のレイヤー定義（Interface → Application → Infrastructure）に準拠する。

```text
Interface Layer:   aidd_kos/cli.py        Typer app（install/index/status コマンド定義）
Application Layer: aidd_kos/install.py    install フロー 8 ステップのオーケストレーション
Infrastructure:    aidd_kos/errors.py     ADR-001 エラーコード定数 + emit_error()
                   aidd_kos/claude_settings.py  ~/.claude/settings.json 安全な読み書き
```

**新規作成ファイル:**

- `aidd_kos/__init__.py`
- `aidd_kos/cli.py`
- `aidd_kos/install.py`
- `aidd_kos/errors.py`
- `aidd_kos/claude_settings.py`

**pyproject.toml 変更:**

```toml
# dependencies に追加
typer>=0.12.0

# [tool.hatch.build.targets.wheel]
packages = ["mcp_server", "aidd_kos"]  # aidd_kos を追加

# [project.scripts]
aidd-kos = "aidd_kos.cli:app"  # エントリポイント追加
```

## install フロー（8 ステップ）

`InstallOrchestrator` クラスで各ステップを担い、前提チェックを最初に実行する
（エラー 3 秒以内 stderr 出力を保証するため重い処理より先に実行）。

```text
Step 1: preflight_check()     mise 存在確認 → MISE_NOT_FOUND
                               OPENAI_API_KEY 確認 → OPENAI_API_KEY_MISSING
Step 2: run_mise_install()    mise install（Python/uv/Node.js 等）
Step 3: run_uv_sync()         uv sync（LightRAG/FastMCP/Typer 等）
Step 4: init_codegraph()      npx @colbymchenry/codegraph init <project-dir>
Step 5: register_mcp()        ~/.claude/settings.json に aidd-kos エントリ追加
                               （OPENAI_API_KEY は env に書かない — 下記セキュリティ注参照）
Step 6: start_lightrag()      LightRAG サーバー起動（インデックス構築用）
Step 7: index_documents()     対象プロジェクトのドキュメントをインデックス
Step 8: update_gitignore()    .lightrag/ .codegraph/ を .gitignore に追記（重複なし）
        print_completion()    「✅ セットアップ完了。Claude Code を再起動してください」
```

### セキュリティ設計（C-2 対応）

**OPENAI_API_KEY は `~/.claude/settings.json` の `env` フィールドに書き込まない。**

理由: settings.json はコミット可能ファイルとして扱われる場合があり、
API キーが漏洩するリスクがある（Charter §NFR「API キーをログ出力禁止」、ADR-001）。

MCP Server 起動時は Claude Code が現在のシェル環境変数を継承する。
オペレーターは `.env` に `OPENAI_API_KEY` を設定し、シェルで `source .env` または
`direnv allow` を実行する運用とする。

`register_mcp()` が設定する settings.json エントリ:

```json
{
  "mcpServers": {
    "aidd-kos": {
      "command": "uvx",
      "args": ["aidd-kos@latest", "serve"],
      "cwd": "<project-dir>"
    }
  }
}
```

`env` フィールドは設定しない。

### 冪等性設計（AC-F01-09〜12 対応）

- `.gitignore` 更新前に既存エントリを確認し、重複追記しない
- `~/.claude/settings.json` 更新時は既存の `mcpServers` キーを保持し、
  `aidd-kos` エントリのみ追加・更新する（AC-F01-12）
- `.lightrag/`・`.codegraph/` が存在する場合は削除せず差分更新（AC-F01-10〜11）
- `codegraph init` が既存 `.codegraph/` に対してエラーを返す場合は
  `codegraph index` にフォールバックする

### settings.json 安全マージ設計（S-2 対応）

`claude_settings.py` の安全マージルール:

1. ファイルサイズ上限チェック（10MB 超はエラー `CLAUDE_SETTINGS_TOO_LARGE`）
2. JSON 読み込み失敗時はバックアップを作成してから上書き
3. マージ後のキー数が既存より減少した場合はロールバック

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/8-install.md | install コマンド 12 AC・全シナリオ（作成済み）|

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| ログ | `install.py:InstallOrchestrator.run()` | 各ステップ開始・完了を stdout に出力（例: `[1/8] 前提確認中...`）|
| エラー | `errors.py:emit_error()` | エラーコード + remediation を stderr へ出力（3 秒以内保証: preflight が最初） |
| セキュリティ | `errors.py:emit_error()` | OPENAI_API_KEY 等の秘密情報をマスクしてからログ出力（`***` で置換）|

## Implementation Tasks

### Spec 追記

- [ ] specs/e2e/8-install.md（作成済み）
  → 完了条件: 全 12 AC がシナリオにトレース可能

### テスト実装（RED）

- [ ] E2E テスト実装（specs/e2e/8-install.md の全 12 シナリオ）
  → 完了条件: pytest が全シナリオで失敗（RED）

### 実装

- [ ] `pyproject.toml`: `typer>=0.12.0` を dependencies に追加、`aidd_kos` をパッケージに追加、エントリポイント追加
- [ ] `uv sync`: 更新後に lockfile を再生成
- [ ] `aidd_kos/errors.py`: エラーコード定数（ADR-001）+ `emit_error(code, remediation)` 関数
- [ ] `aidd_kos/claude_settings.py`: 安全な JSON マージ実装（サイズ上限・バックアップ・ロールバック）
- [ ] `aidd_kos/install.py`: `InstallOrchestrator` クラス（8 ステップ、前提チェック最初）
- [ ] `aidd_kos/cli.py`: Typer app、`install` コマンド（`--project-dir` オプション付き）
- [ ] `aidd_kos/__init__.py`: パッケージ初期化

### 検証

- [ ] 全テストが GREEN
- [ ] `uv run ruff check . && uv run ruff format --check .` PASS
- [ ] `uvx aidd-kos --help` が動作すること（エントリポイント確認）
