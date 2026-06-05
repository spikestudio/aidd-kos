# aidd-kos — Agentic Knowledge OS

[![CI](https://github.com/spikestudio/aidd-kos/actions/workflows/ci.yml/badge.svg)](https://github.com/spikestudio/aidd-kos/actions/workflows/ci.yml)

`uvx aidd-kos install` の 1 コマンドで、AI エージェントが開発プロジェクトの
「コード・設計書・業務文脈」を横断的に理解・検索できるナレッジ OS が即座に稼働する。
LightRAG・CodeGraph 等の個別ツールを個別にセットアップ・運用する手間はない。

## 概要

aidd-kos は **MCP Aggregator** として動作し、複数のナレッジエンジンを単一の MCP エンドポイントに束ねます。

| ゴール | 指標 |
|--------|------|
| AI Agent が自然言語でプロジェクト知識を横断検索できる | P95 応答 < 2秒（1万ドキュメント） |
| `aidd-kos` 導入から MCP 稼働まで 10 分以内 | `uvx aidd-kos install` → Claude Code 再起動 → MCP 疎通確認 |
| 単一 MCP エンドポイントで全ナレッジツールにアクセスできる | AI Agent 側の設定変更なしにエンジン追加が完了すること |

### MCP ツール

| ツール | エンジン | 用途 |
|--------|---------|------|
| `lightrag_query` | LightRAG | 設計書・ADR・議事録を意味検索（Dual-Level Retrieval） |
| `lightrag_list` | LightRAG | インデックス済みドキュメントの一覧取得 |
| `codegraph_context` | CodeGraph | タスク説明からコードコンテキストを構築 |
| `codegraph_explore` | CodeGraph | シンボル周辺の依存関係を一括取得 |
| `codegraph_impact` | CodeGraph | 変更影響半径を分析 |
| `codegraph_trace` | CodeGraph | 2 シンボル間の呼び出しパスを追跡 |
| `codegraph_callers` | CodeGraph | 呼び出し元の検出 |
| `codegraph_callees` | CodeGraph | 呼び出し先の検出 |
| `kos_status` | aidd-kos | 全エンジンの統合ステータス確認 |

### アーキテクチャ

```text
AI Agent (Claude Code / Cursor 等)
    ↓ MCP stdio（aidd-kos 1本のみ登録）
MCP Server（FastMCP + Aggregator）
    ├─ lightrag_*  ← LightRAG embedded（.lightrag/ は対象プロジェクト内）
    └─ codegraph_* ← CodeGraph proxy（.codegraph/ は対象プロジェクト内）
```

## セットアップ

### 前提条件

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) — Python パッケージマネージャー
- [mise](https://mise.jdx.dev/) — ツールバージョン管理
- OpenAI API キー（LightRAG のインデックス構築に必要）

### インストール

対象プロジェクトのルートで 1 コマンド実行するだけで完了します:

```bash
uvx aidd-kos install
```

上記コマンドは以下を全自動実行します:

1. `mise install` でツール（Python / uv / Node.js 等）をインストール
2. `uv sync` で Python 依存（LightRAG / FastMCP 等）をインストール
3. CodeGraph を初期化してコードインデックスを構築
4. `~/.claude/settings.json` に MCP サーバーを登録
5. LightRAG サーバーを起動してドキュメントをインデックス
6. `.gitignore` に `.lightrag/` `.codegraph/` を追記
7. 「Claude Code を再起動してください」と案内

完了後に Claude Code を再起動すると `lightrag_query` / `codegraph_explore` が使えます。

### インデックス更新

インストール後、新しいドキュメントを追加・変更した場合は以下でインデックスを更新します:

```bash
# 差分インデックス（変更・追加ファイルのみ処理・デフォルト）
aidd-kos index

# 全件再構築（インデックスが破損した場合や確実にリセットしたい場合）
aidd-kos index --full
```

差分インデックスは LightRAG が管理するインデックス状態と比較して変更・追加・削除ファイルのみを処理するため、大規模プロジェクトでも API コストを最小化できます。

> **v0.2.0 → v0.2.1 以降へのアップグレード時の注意**
> インデックスのエンコード形式が変更されました（`__` → `___`）。
> アップグレード後、初回の `aidd-kos index` は全ファイルを自動的に再エンコードします。
> クリーンに再構築したい場合は `aidd-kos index --full` を実行してください。

### 環境変数

| 変数 | 必須 | 説明 |
|------|------|------|
| `OPENAI_API_KEY` | ✅ | OpenAI API キー（インデックス構築・検索に使用） |
| `LIGHTRAG_API_KEY` | — | LightRAG サーバーの API キー（外部公開時のみ） |
| `LIGHTRAG_URL` | — | LightRAG API URL（デフォルト: `http://localhost:9621`） |
| `LLM_BINDING` | — | LLM バインディング（デフォルト: `openai`） |
| `LLM_MODEL` | — | LLM モデル（デフォルト: `gpt-4o-mini`） |
| `EMBEDDING_BINDING` | — | Embedding バインディング（デフォルト: `openai`） |
| `EMBEDDING_MODEL` | — | Embedding モデル（デフォルト: `text-embedding-3-small`） |
| `LIGHTRAG_QUERY_TIMEOUT_MS` | — | lightrag_query のタイムアウト（デフォルト: `5000` ms） |

詳細: [docs/playbook/secrets.md](docs/playbook/secrets.md)

## 開発

```bash
# テスト
uv run pytest

# Lint / フォーマット
task lint        # ruff check + format --check
task lint:fix    # ruff の自動修正

# Git フック（初回のみ）
lefthook install
```

## ドキュメント

| ドキュメント | 内容 |
|------------|------|
| [docs/PROJECT-CHARTER.md](docs/PROJECT-CHARTER.md) | ビジョン・ゴール・アーキテクチャ方針 |
| [docs/architecture/baseline.md](docs/architecture/baseline.md) | C4 Container 図・レイヤー構成 |
| [docs/glossary.md](docs/glossary.md) | 用語集 |
| [docs/playbook/secrets.md](docs/playbook/secrets.md) | シークレット管理方針 |

## 技術スタック

| カテゴリ | 採用技術 |
|---------|---------|
| 言語 | Python 3.12+ |
| Doc Intelligence | LightRAG (lightrag-hku) 1.5+ |
| Code Intelligence | CodeGraph (@colbymchenry/codegraph) |
| MCP フレームワーク | FastMCP 2.0+ |
| CLI フレームワーク | Typer |
| パッケージマネージャー | uv |
| ツールバージョン管理 | mise |
| CI/CD | GitHub Actions |

## コントリビュート

[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

MIT — [LICENSE](LICENSE)
