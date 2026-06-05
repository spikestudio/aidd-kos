# Business Context: Multi-Project（マルチプロジェクト対応）

Epic: #38
対象 Phase: Operational Excellence（#2）
作成日: 2026-06-05

---

## 業務目的

複数プロジェクトを並行開発するオペレーターが、プロジェクトを切り替えるたびに
`aidd-kos install` と Claude Code 再起動を行うことなく、各プロジェクトを開くだけで
正しい知識ベースが自動参照される状態を実現する。

---

## 既存定義からの変更（install.md §MCP 登録 との差分）

| 項目 | 旧定義（Epic #4 / install.md）| 新定義（Epic #38）|
|------|------|------|
| デフォルト書き込み先 | `~/.claude/settings.json` | `.claude/settings.local.json` |
| `cwd` フィールド | 含む（絶対パス）| 含まない（Claude Code が自動設定）|
| 旧動作への切り替え | なし | `--global` オプションで維持 |
| LightRAG 起動方式 | ポート 9621 別プロセス（Epic #3）| in-process（ポートなし）|

---

## 登場人物

| 役割 | 説明 |
|------|------|
| AI 駆動開発エンジニア（オペレーター）| 各プロジェクトに `aidd-kos install` を実行し導入・管理する人間開発者 |
| AI Agent（Claude Code 等）| プロジェクトを開いたとき MCP 経由でそのプロジェクトの知識ベースを参照する受益者 |

---

## ドメイン概念

| 用語 | 定義 | 備考 |
|------|------|------|
| プロジェクトレベル MCP 登録 | `.claude/settings.local.json`（プロジェクトルート直下）の `mcpServers` セクションに `cwd` なしで `aidd-kos` エントリを書き込むこと。Epic #38 以降の `install` デフォルト動作 | Claude Code がプロジェクトルートを作業ディレクトリとして MCP サーバーを起動する |
| グローバル MCP 登録 | `~/.claude/settings.json` の `mcpServers` セクションに `cwd` 付きで書き込む。`--global` オプションで選択できる旧動作 | install.md §MCP 登録 の旧定義に相当 |
| in-process 起動 | aidd-kos MCP サーバープロセス内部で LightRAG を Python ライブラリとして直接実行する方式。外部ポートを占有しない | Epic #3 の「ポート 9621 別プロセス起動」から変更 |
| MCP 設定ファイル | aidd-kos エントリが書き込まれる設定ファイル。プロジェクトレベルは `.claude/settings.local.json`、グローバルは `~/.claude/settings.json` | Claude Code はプロジェクトレベルを優先して読み込む |

---

## MCP 登録状態遷移

| 遷移 | トリガー |
|------|---------|
| 未登録 → プロジェクトレベル登録済み | `aidd-kos install`（`--global` なし）|
| 未登録 → グローバル登録済み | `aidd-kos install --global` |
| 登録済み → 登録済み（変化なし・冪等）| 再 `aidd-kos install` |

**状態の制約:**

- 未登録 では Claude Code でプロジェクトを開いても `lightrag_query` が使えない
- プロジェクトレベル登録済み では Claude Code を開くだけで AI 検索が使える

---

## ビジネスルール

| ID | ルール | 根拠 AC |
|----|--------|---------|
| BR-MP-01 | `aidd-kos install` のデフォルト書き込み先は `.claude/settings.local.json` | AC-F[F01]-01 |
| BR-MP-02 | プロジェクトレベル MCP 登録のエントリに `cwd` フィールドを含まない | AC-F[F01]-01 |
| BR-MP-03 | `--global` オプション指定時のみ `~/.claude/settings.json` に `cwd` 付きで書き込む | AC-F[F01]-04 |
| BR-MP-04 | 同一プロジェクトへの再 install は MCP エントリを重複させない（冪等）| AC-F[F01]-05 |
| BR-MP-05 | `install`（`--global` なし）は既存の `~/.claude/settings.json` の `aidd-kos` エントリを変更しない | AC-F[F01]-03 |
| BR-MP-06 | aidd-kos MCP サーバーは外部ポートを Listen しない（in-process 起動）。Epic #3 の「ポート 9621 別プロセス」から変更 | AC-F[F02]-03・AC-F[F02]-05 |
| BR-MP-07 | `.claude/settings.local.json` は `.gitignore` に追記しない。VCS の管理対象としてコミットする | Q-MP-01 解決（2026-06-05）|

---

## 例外・禁止事項

| ID | 条件 | システムの振る舞い |
|----|------|----------------|
| EX-MP-01 | install 実行時に `.claude/` ディレクトリが存在しない | `.claude/` を作成してから `settings.local.json` を書き込む |
| EX-MP-02 | install 実行時に `~/.claude/settings.json` に既存の `aidd-kos` エントリが検出された | stdout に「グローバル設定が検出されました。~/.claude/settings.json の aidd-kos エントリは手動で削除することを推奨します」と出力する。処理は続行する |

---

## 業務イベント

| イベント名 | 発生条件 | 後続アクション |
|----------|---------|-------------|
| プロジェクト MCP 登録完了 | `aidd-kos install` が `.claude/settings.local.json` への書き込みを完了したとき | Claude Code 再起動後にそのプロジェクトの AI 検索が使える状態になる |
| 複数プロジェクト同時起動 | 2 つ以上のプロジェクトで aidd-kos MCP が起動したとき | 各サーバーが独立して動作し互いの検索結果に影響を与えない |

---

## ユビキタス言語

| 用語 | 定義 |
|------|------|
| プロジェクトレベル MCP 登録 | `.claude/settings.local.json` に `cwd` なしで書き込む install のデフォルト動作 |
| グローバル MCP 登録 | `~/.claude/settings.json` に `cwd` 付きで書き込む `--global` オプション動作 |
| in-process 起動 | ポートを占有せず aidd-kos MCP サーバー内で LightRAG を直接実行する方式 |
