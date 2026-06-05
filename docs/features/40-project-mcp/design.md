# プロジェクトレベル MCP 登録 Design

Feature Issue: #40
Epic: #38

## Spec

docs/spec/multi-project.md → Feature: プロジェクトレベル MCP 登録 (#40)

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/40-project-mcp.md | プロジェクトレベル MCP 登録 E2E シナリオ（新規）|
| 実装 | aidd_kos/install.py | `__init__` に `global_install` 追加・`register_mcp()` デフォルト変更 |
| 実装 | aidd_kos/cli.py | `install` コマンドに `--global` フラグ追加 |
| テスト | tests/unit/test_install.py | register_mcp 新動作テスト追加・既存 AC-F01-03 テスト調整 |
| テスト | tests/e2e/test_install_f40.py | プロジェクトレベル MCP 登録 E2E テスト（新規）|

## 設計概要

`InstallOrchestrator` に `global_install: bool = False` を追加し、
`register_mcp()` は `self.global_install` を参照して書き込み先を切り替える。

```text
--global なし（デフォルト）:
  書き込み先: {project_dir}/.claude/settings.local.json
  entry: {"command": "uvx", "args": ["aidd-kos@latest", "serve"]}  ← cwd なし
  ~/.claude/settings.json への書き込みは行わない（AC-F40-03）
  副作用: ~/.claude/settings.json に aidd-kos エントリがある場合は stdout に通知

--global オプション:
  書き込み先: ~/.claude/settings.json
  entry: {"command": "uvx", "args": ["aidd-kos@latest", "serve"], "cwd": "{project_dir}"}
  → 旧動作（AC-F40-04）
```

`ClaudeSettings` クラスはパスを受け取るだけなので変更不要。
`.claude/settings.local.json` は BR-MP-07 に従い VCS 管理対象（`.gitignore` 追加不要）。

**AC-F40-02 の扱い:**
Claude Code の実動作（どのプロジェクトの MCP が起動されるか）に依存するため自動テスト対象外。
手動確認項目: 2プロジェクトに install 後、各 Claude Code ウィンドウで
`lightrag_query` が正しいプロジェクトのドキュメントを返すことを確認する。

**既存テスト `test_ac_f01_03` への影響:**
Feature #40 のデフォルト動作変更（グローバル書き込みなし）により、
`tests/e2e/test_install.py::test_ac_f01_03`（`~/.claude/settings.json` に書き込まれることを検証）が RED になる。
この既存テストの修正を Implementation Tasks に含める。

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| ファイル | `{project_dir}/.claude/settings.local.json` | install デフォルト動作で作成・cwd なしのエントリ |
| ファイル | `~/.claude/settings.json` | install --global で cwd 付きエントリ・デフォルト動作では変更なし |
| stdout | `InstallOrchestrator.register_mcp()` | グローバル設定検出時の通知メッセージ |

## Implementation Tasks

### Spec 追記

- [ ] specs/e2e/40-project-mcp.md 作成
  → 完了条件: AC-F40-01〜05 が 1 件以上のシナリオに対応している

### テスト実装（RED）

- [ ] tests/e2e/test_install_f40.py 実装（AC-F40-01・03・04・05 E2E テスト）
  → 完了条件: 全テストが RED
- [ ] tests/unit/test_install.py に register_mcp 新動作テストを追記（AC-F40-01・03・04）
  → 完了条件: 新テストが RED

### 実装

- [ ] `InstallOrchestrator.__init__()` に `global_install: bool = False` パラメータを追加
  → `self.global_install = global_install` を設定する
- [ ] `InstallOrchestrator.register_mcp()` を変更
  → `self.global_install = False` のとき: `.claude/settings.local.json` に cwd なしで書き込む。
     `~/.claude/settings.json` への書き込みは行わない。
     `~/.claude/settings.json` に既存エントリがあれば stdout に通知する。
  → `self.global_install = True` のとき: `~/.claude/settings.json` に cwd 付きで書き込む（旧動作）。
- [ ] `InstallOrchestrator.run()` を変更
  → 特にシグネチャ変更なし（`self.global_install` を参照するため）
- [ ] `aidd_kos/cli.py` の `install` コマンドに `--global` フラグを追加
  → `global_install=True` を `InstallOrchestrator()` に渡す
  → 全テスト GREEN
- [ ] 既存テスト `tests/e2e/test_install.py::test_ac_f01_03` を修正
  → Feature #40 デフォルト動作に合わせて `settings.local.json` を確認するよう更新

### 検証

- [ ] リファクタ + `uv run ruff check` / `uv run ruff format --check` PASS
- [ ] `git grep "AC-F40"` で全 AC-ID がテストに存在する
