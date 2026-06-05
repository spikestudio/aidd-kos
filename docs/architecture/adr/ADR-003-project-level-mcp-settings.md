# ADR-003: install のデフォルト MCP 設定先をプロジェクトレベルに変更

| 項目 | 内容 |
|------|------|
| ステータス | 承認済み |
| 日付 | 2026-06-05 |
| 決定者 | sanojimaru |

## コンテキスト

Epic #4 の `aidd-kos install` は MCP エントリを `~/.claude/settings.json`（グローバル）に
絶対パス付きの `cwd` フィールドとともに書き込む。

この設計では、複数プロジェクトを並行開発する際に2つの問題が発生する:

1. グローバル設定は最後に `install` したプロジェクトの `cwd` で上書きされるため、
   プロジェクトを切り替えるたびに `aidd-kos install` + Claude Code 再起動が必要になる
2. `cwd` に絶対パスが含まれるため、プロジェクトを別のパスに移動すると設定が壊れる

Claude Code は `.claude/settings.local.json`（プロジェクトルート直下）を
`~/.claude/settings.json` より優先して読み込む。
プロジェクトレベル設定に `cwd` フィールドを含めない場合、
Claude Code はそのプロジェクトのルートを作業ディレクトリとして MCP サーバーを自動起動する。

この動作を利用すれば、各プロジェクトに独立した MCP 設定を持たせることができる。

## 決定事項

**`aidd-kos install` のデフォルト書き込み先を `.claude/settings.local.json` に変更し、
`cwd` フィールドを含めない。`--global` オプションで旧動作（`~/.claude/settings.json` + `cwd`）を維持する。**

```json
// .claude/settings.local.json（デフォルト・cwd なし）
{
  "mcpServers": {
    "aidd-kos": {
      "command": "uvx",
      "args": ["aidd-kos@latest", "serve"]
    }
  }
}
```

`.claude/settings.local.json` は VCS の管理対象としてコミットする（絶対パスを含まないため安全）。

## 根拠

1. **プロジェクト独立**: 各プロジェクトが独自の MCP 設定を持ち、切り替えに再インストール不要
2. **ポータブル**: `cwd` を含まないため、プロジェクトを別のパスに移動しても設定が有効
3. **VCS 管理可能**: 絶対パスを含まない設定はチームメンバーと共有できる
4. **Claude Code の仕様活用**: `.claude/settings.local.json` のグローバル設定優先は Claude Code の公式動作

## 代替案

### 代替案 A: `.claude/settings.local.json` + `cwd` なし（**採用**）

- メリット: プロジェクト独立・ポータブル・VCS 管理可能
- デメリット: 既存ユーザーが手動移行（旧グローバル設定の削除）が必要

### 代替案 B: 現状維持（`~/.claude/settings.json` + `cwd`）

- メリット: 既存ユーザーへの影響なし
- デメリット: プロジェクト切替で再インストール必要・絶対パスのハードコード・マルチプロジェクト不可

### 代替案 C: 動的ポート検出（各プロジェクトがランダムポートで LightRAG を起動）

- メリット: グローバル設定を維持したままポート競合を解消できる
- デメリット: ポート検出の複雑さ・`cwd` の根本問題は未解決・Epic #38 の目標を完全には達成できない

## 影響・トレードオフ

- **影響を受けるコンポーネント:**
  - `aidd_kos/install.py`（`register_mcp()` メソッドの書き込み先変更）
  - `aidd_kos/claude_settings.py`（`ClaudeSettings` クラスの汎用化）
  - `aidd_kos/cli.py`（`install` コマンドへの `--global` オプション追加）
- **影響を受ける Epic / Phase:** Epic #38（マルチプロジェクト対応）
- **Charter §10 採用方針との関係:** 該当なし（MCP 設定の記録先はツール固有）
- **マスタドキュメントの更新:**
  - `docs/business-context/install.md` §MCP 登録 の定義を Epic #38 仕様に合わせて更新（プロジェクトレベルをデフォルト、グローバルを `--global` オプションで明記）
- **トレードオフ:**
  - 既存ユーザーは `~/.claude/settings.json` の `aidd-kos` エントリを手動削除することを推奨する
    （削除しなくても `.claude/settings.local.json` が優先されるため動作には影響しない）
  - `.claude/settings.local.json` が VCS 管理対象になることで、ブランチ切り替え時に
    MCP 設定が意図せず変わる可能性がある（通常は許容範囲）
