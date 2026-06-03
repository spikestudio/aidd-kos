# Business Context: Install & CLI

Epic: #4
対象 Phase: Phase 1 (Core MVP)
作成日: 2026-06-03

---

## ドメイン概念

| 概念 | 定義 | 備考 |
|------|------|------|
| install コマンド | `uvx aidd-kos install` の 1 コマンドで LightRAG・CodeGraph のインストール〜インデックス初期化〜MCP 登録を全自動化する CLI エントリポイント | オペレーター（人間開発者）が対象プロジェクトのルートで 1 回だけ実行する |
| 前提チェック | install コマンドが実行前に検証する必須条件の集合。mise インストール済み・OPENAI_API_KEY 設定済み・ポート 9621 使用可能が含まれる | 未充足時は 3 秒以内に stderr へエラーコードと対処方法を出力して終了（AC-F01-05/06） |
| MCP 登録 | `~/.claude/settings.json` の `mcpServers` セクションに `aidd-kos` エントリを追記すること。Claude Code 再起動後に AI Agent が MCP ツールを使える状態になる | キーが既存の場合は上書きせず既存値を保持（冪等性保証） |
| ストレージ初期化 | 対象プロジェクトのルートに `.lightrag/` と `.codegraph/` を作成すること。DB サーバー不要でローカルファイルのみで動作する設計を実現する | 既存ディレクトリが存在する場合は削除・上書きせず保持（AC-F01-10〜12） |
| .gitignore 自動更新 | install コマンドが対象プロジェクトの `.gitignore` に `.lightrag/` と `.codegraph/` を自動追記すること。既に記載済みの場合は追記しない（冪等性） | インデックスデータが意図せず VCS に混入するのを防ぐ（AC-F01-07〜09） |
| index コマンド | `aidd-kos index` の 1 コマンドで対象プロジェクトの `.md` / `.txt` ファイルを LightRAG へ再インデックスするCLIコマンド | インデックス構築は OpenAI API を消費する。LightRAG 未起動時はエラーを返す（AC-F02-05） |
| status コマンド | `aidd-kos status` で LightRAG・CodeGraph の両エンジンの稼働状態を確認する CLI コマンド | エンジン状態は `ready` / `unavailable` / `indexing` の 3 値（AC-F03-01〜02） |
| 再 install（冪等性） | 既にインストール済みの環境で `aidd-kos install` を再実行した場合、既存のインデックスデータ・MCP 登録を保持し上書きしないこと | データ消失リスクを排除するためデフォルト動作は保持。強制再初期化は明示オプションで提供 |
| AIDD_KOS_PROJECT_DIR | install コマンドが `~/.claude/settings.json` に書き込む MCP server の環境変数。対象プロジェクトのルートパスを絶対パスで格納する。MCP Server が `.lightrag/` と `.codegraph/` の配置先を決定するために参照する | 対象プロジェクト内にストレージを配置するアーキテクチャ方針の実装キー |
| uvx 実行 | `uv tool run` の省略形。aidd-kos を pip install せずに使い捨て実行する PyPA 標準の配布方式。インストール済みかどうかを問わず最新版を取得して実行できる | 配布は GitHub Release 経由。PyPI は将来対応 |
| mise 前提 | mise（ツールバージョン管理）がインストール済みであることを install の前提条件とする | Python / uv のバージョン管理を mise に委譲する設計方針に起因 |

---

## ビジネスルール

| ID | ルール | 情報源 |
|----|--------|--------|
| BR-I01 | `aidd-kos install` は対象プロジェクトのルートディレクトリ（cwd）を基準に動作する。cwd が git リポジトリのルートでない場合は警告を出力するが中断はしない | CHARTER §9 アーキテクチャ方針 |
| BR-I02 | 前提チェック未充足時は 3 秒以内に stderr へ `エラーコード: 対処方法` 形式で出力し、非ゼロ exit code で終了する | NFR（可用性）／AC-F01-05・06 |
| BR-I03 | `~/.claude/settings.json` へのMCP登録はキーが存在しない場合のみ追記する。既存エントリは上書きしない（冪等性の保証） | AC-F01-10〜12 |
| BR-I04 | `.gitignore` への追記は `.lightrag/` と `.codegraph/` それぞれについて、既に記載済みの場合は追記しない。重複追記禁止 | AC-F01-07〜09 |
| BR-I05 | `.lightrag/` と `.codegraph/` が既に存在する場合、install は既存ディレクトリを保持する。--force オプション等の明示的な上書き指示がない限りデータを削除しない | AC-F01-10〜12（データ消失リスク排除） |
| BR-I06 | `aidd-kos index` は LightRAG サーバーが起動中（`LIGHTRAG_URL` に到達可能）であることを前提とする。未起動時は `LIGHTRAG_UNAVAILABLE` エラーコードと remediation を stderr に出力して終了する | AC-F02-05 |
| BR-I07 | `aidd-kos index` がスキャンする対象は `.lightrag-ignore` の除外設定を適用した後の `.md` / `.txt` ファイルに限定する。他の拡張子はスコープ外 | AC-F02-01〜04 |
| BR-I08 | `aidd-kos status` は LightRAG・CodeGraph の両エンジンの状態を必ず返す。片方のエンジンが unavailable であっても status コマンド自体は成功（exit 0）で終了する | AC-F03-01〜02（MCP Aggregator の BR-06 と整合） |
| BR-I09 | OPENAI_API_KEY は `.env` ファイルまたは環境変数で管理し、CLI の標準出力・ログに絶対に露出しない | CHARTER §NFR セキュリティ |
| BR-I10 | LightRAG のデフォルトポートは 9621。`LIGHTRAG_PORT` 環境変数で変更可能とし、install コマンドは `LIGHTRAG_URL` 環境変数を `http://127.0.0.1:{LIGHTRAG_PORT}` として MCP server 設定に書き込む | CHARTER §7 前提条件 |
| BR-I11 | インデックス構築は OpenAI API（Embedding / LLM）を消費する。コスト管理のため `.lightrag-ignore` によるスキャン対象の除外設定を install 時に案内する | CHARTER §8 リスク（OpenAI API コスト超過） |

---

## ユビキタス言語

| 用語 | 定義 |
|------|------|
| install | `uvx aidd-kos install` の 1 コマンドで対象プロジェクトへの全自動セットアップを完了させる動詞・コマンド名。単なる「パッケージのインストール」ではなく、MCP 登録・ストレージ初期化・.gitignore 更新まで含む |
| index | `aidd-kos index` コマンド。対象プロジェクトの `.md` / `.txt` ファイルを LightRAG に再インデックスさせる操作。インデックスの差分更新（既存エントリの扱い）は LightRAG の内部実装に委譲する |
| status | `aidd-kos status` コマンド。LightRAG・CodeGraph の両エンジンの状態を人間が読める形式で stdout に出力する |
| 前提チェック | install コマンドが実行前に必ず検証するシステム状態の集合。mise・OPENAI_API_KEY・ポート 9621 の可用性が該当。英語では "preflight check" |
| MCP 登録 | `~/.claude/settings.json` の `mcpServers` への aidd-kos エントリ追記。Claude Code 再起動後に AI Agent が MCP ツールを利用できる状態を作る最終ステップ |
| 冪等 install | 同じ install コマンドを複数回実行しても結果が変わらないこと。既存のインデックス・MCP 登録・.gitignore エントリは保持される |
| .lightrag/ | LightRAG がグラフデータとベクトルデータを保存するローカルディレクトリ（対象プロジェクトのルート直下）。install で初期化され、index 実行ごとにデータが蓄積される |
| .codegraph/ | CodeGraph がコード AST インデックスを保存するローカルディレクトリ（対象プロジェクトのルート直下）。install で `npx codegraph init` により初期化される |
| .lightrag-ignore | インデックス構築対象から除外するファイル・ディレクトリを指定する設定ファイル。`.gitignore` と同様の書式。`aidd-kos index` がこのファイルを参照してスキャン範囲を決定する |
| ready | エンジンが正常起動しクエリを受け付けられる状態 |
| unavailable | エンジンプロセスに到達不能な状態。起動失敗またはプロセスが停止している |
| indexing | エンジンがインデックス構築中の状態。LightRAG のみ取りうる状態値。CodeGraph は ready / unavailable のみ |
| AIDD_KOS_PROJECT_DIR | MCP Server に対象プロジェクトのルートパスを伝える環境変数。`aidd-kos install` が `~/.claude/settings.json` に書き込む |

---

## 境界コンテキスト

### このコンテキストが扱う範囲

- `aidd-kos install` / `index` / `status` の CLI インターフェース設計（コマンド名・引数・終了コード・標準出力形式）
- 前提チェックの検証項目と失敗時のエラーコード・remediation 仕様
- `~/.claude/settings.json` への MCP 登録手順と冪等性保証の仕様
- `.gitignore` 自動更新の条件（追記 vs スキップ）
- `.lightrag/` / `.codegraph/` のストレージ初期化条件と冪等性保証
- 再 install 時のデータ保持ポリシー
- `.lightrag-ignore` の参照タイミングと適用範囲

### このコンテキストが扱わない範囲（隣接コンテキスト）

| 隣接コンテキスト | 担当 Epic | 境界 |
|----------------|-----------|------|
| LightRAG の embedded 起動（MCP Server のサブプロセス管理） | Epic #3 | install フローでは外部起動済みの LightRAG を前提とする。サブプロセス自動起動・自動停止は Epic #3 のスコープ |
| ストレージ配置パスの変更（`AIDD_KOS_PROJECT_DIR` の動的切り替え） | Epic #3 | Phase 1 の install は cwd を対象プロジェクトとして固定する。複数プロジェクト切り替えは Epic #3 |
| MCP Aggregator のツール設計（`lightrag_*` / `codegraph_*` の仕様） | Epic #2 | install が登録する MCP Server が公開するツールの仕様は Epic #2 のスコープ |
| LightRAG 内部のインデックスアルゴリズム | Doc Intelligence | `aidd-kos index` は LightRAG REST API を呼び出すのみ。内部の Dual-Level Retrieval 実装は本コンテキストの関心外 |
| CodeGraph の AST 解析ロジック | Code Intelligence | `npx codegraph init` を呼び出すのみ。内部実装は本コンテキストの関心外 |
| aidd-kos のバージョンアップ・アンインストール | 将来 Epic | Epic #4 のスコープ外（CHARTER §4 スコープ外参照） |

---

## 差し戻し事項（PRD との矛盾・不足）

### 1. [MUST] `~/.claude/settings.json` の書き込みスキーマが未定義

MCP 登録（AC-F01-03）で書き込む `mcpServers` エントリの具体的なスキーマ（`command` / `args` / `env` フィールドの値）が PRD に明記されていない。

**対処要求**: `docs/spec/install.md` に以下を明記すること。

```json
{
  "mcpServers": {
    "aidd-kos": {
      "command": "uvx",
      "args": ["aidd-kos-mcp"],
      "env": {
        "AIDD_KOS_PROJECT_DIR": "<対象プロジェクトの絶対パス>",
        "LIGHTRAG_URL": "http://127.0.0.1:9621",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

`OPENAI_API_KEY` を settings.json にプレーンテキストで書き込むとセキュリティ上の問題が生じる。環境変数参照構文の可否・代替策（`.env` ファイル参照）を明確にすること。

### 2. [MUST] 前提チェックの具体的なエラーコード体系が未定義

AC-F01-05/06 でエラー出力は規定されているが、エラーコード文字列が未定義。

**対処要求**: `docs/spec/install.md` にエラーコード一覧を定義し、
`LIGHTRAG_UNAVAILABLE` 形式（BR-02）と命名規則を統一すること。

### 3. [SHOULD] CodeGraph の初期化コマンドが未確定

AC-F01-02 で `.codegraph/` 作成が含まれるが、初期化コマンドが PRD に未記載。

**対処要求**: `docs/spec/install.md` に CodeGraph 初期化コマンドとオプションを明記すること。

### 4. [SHOULD] `aidd-kos index` の差分インデックス動作が未定義

再インデックス時の動作（完全再構築 vs 差分更新）が AC-F02-01〜04 に未定義。

**対処要求**: `docs/spec/install.md` に再インデックス時の差分処理方針を明記すること。

### 5. [INFO] `aidd-kos status` と `kos_status` MCP ツールの関係を整理

`aidd-kos status` CLI（F-03）と Epic #2 の `kos_status` MCP ツール（AC-F03 相当）は異なるインターフェースだが、返却する情報（エンジン状態・インデックス件数等）が重複している。

**情報共有**: 実装時は `kos_status` ツールを CLI から呼び出す（または共通ロジックを切り出す）ことで重複実装を避けることを推奨する。仕様上の矛盾はないが、設計判断として ADR 化を検討すること。
