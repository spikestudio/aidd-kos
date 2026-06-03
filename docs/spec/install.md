# Spec: Install & CLI

Epic: #4 aidd-kos CLI & Install フロー
Milestone: Core MVP（#1）

---

## Feature: install コマンド（全自動セットアップ）(F-01)

### Story S-01: 1 コマンドで aidd-kos の全セットアップが完了する

As an AI 駆動開発エンジニア（オペレーター）, I want to set up aidd-kos with a single command,
so that I don't need to manually install LightRAG, CodeGraph, or configure MCP settings.

根拠: [ユーザー入力]

**AC:**

| ID | 条件 |
|----|------|
| AC-F01-01 | `uvx aidd-kos install` を実行すると LightRAG・CodeGraph のインストール、インデックス構築、MCP 登録、.gitignore 更新が全て自動実行されること |
| AC-F01-02 | 完了後に「✅ セットアップ完了。Claude Code を再起動してください」が表示されること |
| AC-F01-03 | `~/.claude/settings.json` の `mcpServers` キー配下に `aidd-kos` エントリが追加されること |
| AC-F01-04 | `.lightrag/` と `.codegraph/` が対象プロジェクトのルートに作成されること |

---

### Story S-02: 前提条件未充足時に対処方法付きエラーが表示される

As an AI 駆動開発エンジニア（オペレーター）, I want to be notified of missing prerequisites before install starts,
so that I can fix the issue without wasting time.

根拠: Charter §NFR「障害時は 3 秒以内に stderr へエラーコードと対処方法を出力」

**AC:**

| ID | 条件 |
|----|------|
| AC-F01-05 | `mise` 未インストール時に 3 秒以内に stderr へ `MISE_NOT_FOUND` エラーコードとインストール手順（URL 付き）が出力されること（エラーコード規則: ADR-001）|
| AC-F01-06 | `OPENAI_API_KEY` 未設定時に 3 秒以内に stderr へ `OPENAI_API_KEY_MISSING` エラーコードと `.env` 設定方法が出力されること（エラーコード規則: ADR-001）|

---

### Story S-03: インデックスファイルが .gitignore に自動除外される

As an AI 駆動開発エンジニア（オペレーター）, I want index directories added to .gitignore automatically,
so that I don't accidentally commit large index files.

根拠: [ユーザー入力]

**AC:**

| ID | 条件 |
|----|------|
| AC-F01-07 | install 後に対象プロジェクトの `.gitignore` に `.lightrag/` が追記されていること |
| AC-F01-08 | install 後に対象プロジェクトの `.gitignore` に `.codegraph/` が追記されていること |
| AC-F01-09 | すでに記載済みの場合は重複追記しないこと |

---

### Story S-04: 再 install 時に既存インデックスを保持できる

As an AI 駆動開発エンジニア（オペレーター）, I want a safe re-install when aidd-kos is already installed,
so that I don't lose my existing knowledge index.

根拠: [ユーザー入力]

**AC:**

| ID | 条件 |
|----|------|
| AC-F01-10 | 既存の `.lightrag/`・`.codegraph/` ディレクトリが削除されないこと |
| AC-F01-11 | 再 install 後も既存インデックスファイルが読み取り可能な状態であること |
| AC-F01-12 | `~/.claude/settings.json` の他 MCP エントリを変更せず `aidd-kos` エントリのみ追加・更新すること |

---

## Feature: index コマンド（ドキュメント再インデックス）(F-02)

### Story S-05: 新しいドキュメント追加後にインデックスを更新できる

As an AI 駆動開発エンジニア（オペレーター）, I want to re-index project documents after adding new files,
so that the AI Agent can search the latest knowledge.

根拠: [ユーザー入力]

**AC:**

| ID | 条件 |
|----|------|
| AC-F02-01 | `aidd-kos index [path]` を実行すると `.md`・`.txt` ファイルが LightRAG に再インデックスされること |
| AC-F02-02 | path 省略時はカレントディレクトリを対象とすること |
| AC-F02-03 | 完了後に処理ファイル数が表示されること |
| AC-F02-04 | 完了後に所要時間が表示されること |

---

### Story S-06: LightRAG 未起動時に明確なエラーが表示される

As an AI 駆動開発エンジニア（オペレーター）, I want to be notified when LightRAG is not running during re-index,
so that I can resolve the issue quickly.

根拠: Charter §NFR、[AI補完: エラーケース]

**AC:**

| ID | 条件 |
|----|------|
| AC-F02-05 | LightRAG 未起動時に 3 秒以内に stderr へ `LIGHTRAG_UNAVAILABLE` エラーコードと対処方法が出力されること（エラーコード規則: ADR-001）|

---

## Feature: status コマンド（全エンジン状態確認）(F-03)

### Story S-07: 全エンジンの状態を一括確認できる

As an AI 駆動開発エンジニア（オペレーター）, I want to check the status of all knowledge engines,
so that I can verify everything is working before starting a work session.

根拠: [ユーザー入力]

**AC:**

| ID | 条件 |
|----|------|
| AC-F03-01 | `aidd-kos status` を実行すると LightRAG（ready/unavailable/indexing）・CodeGraph（ready/unavailable）の状態とインデックス日時・件数が表示されること |
| AC-F03-02 | `--json` フラグで JSON 形式の出力が得られること |
