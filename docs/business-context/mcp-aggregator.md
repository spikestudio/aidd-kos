# Business Context: MCP Aggregator

Epic: #2  
対象 Phase: Phase 1 (Core MVP)  
作成日: 2026-06-03

---

## ドメイン概念

| 概念 | 定義 | 備考 |
|------|------|------|
| MCP Aggregator | 複数のナレッジエンジンが提供するツール群を単一の MCP エンドポイントに束ねる FastMCP サーバー。AI Agent は aidd-kos 1 本だけを MCP 登録すれば全エンジンのツールが使える | Phase 2 以降もエンジン追加に際して AI Agent 側の設定変更は不要 |
| Doc Intelligence Engine | LightRAG によるドキュメント知識エンジン。`lightrag_*` prefix のツールを公開する | MCP Server の embedded サブプロセスとして起動 |
| Code Intelligence Engine | CodeGraph による AST・呼び出しグラフ知識エンジン。`codegraph_*` prefix のツールを公開する | MCP Server が npx プロセスを proxy して公開 |
| エンジン prefix | MCP ツール名に付与する `lightrag_` / `codegraph_` 等のエンジン識別子。AI Agent がどのエンジンを呼んでいるか認識した上で自律判断できるようにする | 新エンジン追加時も prefix 体系で一意性を保つ |
| エンジン状態 | `ready` / `unavailable` / `indexing` の 3 値。`indexing` は LightRAG 側のみ発生し得る（CodeGraph は起動成否の 2 値） | AC-F03-01 参照。エンジン種別によって取りうる状態値が異なる点に注意 |
| アプリケーション層エラーコード | `LIGHTRAG_UNAVAILABLE` / `CODEGRAPH_UNAVAILABLE` 等のエラー識別子。MCP 標準の JSON-RPC エラーコード（`-32xxx`）とは別の、aidd-kos 固有のアプリケーション層エラー文字列 | remediation（対処方法）を必ずセットで返す |
| remediation | エラーコードに付随する対処手順文字列。AI Agent が次のアクションを自律決定できるよう、エラーと対で必ず返す | NFR: 3秒以内に stderr へ出力 |
| available_tools | `kos_status` ツールが返す応答フィールド。現在利用可能なすべての MCP ツール名一覧。MCP 標準の `tools/list` とは別の kos_status 固有フィールド | AC-F03-03 参照 |

---

## ビジネスルール

| ID | ルール |
|----|--------|
| BR-01 | MCP ツール名は `{engine_prefix}_{tool_name}` の命名規則に従う。engine_prefix は `lightrag` / `codegraph` のように小文字スネークケース |
| BR-02 | エンジンが未起動・到達不能な場合は、ツール呼び出しを黙って失敗させず、必ずエラーコードと remediation を返す。無言の空レスポンスは禁止 |
| BR-03 | エラーコードと remediation は 3 秒以内に stderr へ出力する（NFR: 可用性） |
| BR-04 | `lightrag_query` の mode パラメータ省略時のデフォルト値を明示する（未定義のままにしない）。hybrid / local / global のいずれかを必ずデフォルトとして宣言する |
| BR-05 | `lightrag_list` は空インデックスのとき空リストを返す（null / エラーは不可） |
| BR-06 | `kos_status` は常に全エンジンの状態と `available_tools` を返す。エンジンが unavailable でも status 自体は成功レスポンスとして返す |
| BR-07 | codegraph_* ツールは `codegraph_` prefix で 6 ツールを公開する（AC-F02-01〜03）。ツール名は実装前に確定させ PRD に明記すること（→ 差し戻し事項参照） |
| BR-08 | `codegraph_impact` の応答形式は `{impacts: [{name, kind}]}` に固定する。フォーマット変更はバージョンアップ時の破壊的変更として扱う |
| BR-09 | STDIO servers はシェル環境変数を継承しない（FastMCP 3.x 仕様）。CodeGraph proxy に必要な環境変数は `env_vars` で明示的に渡す |

---

## ユビキタス言語（このコンテキストでの用語）

| 用語 | 定義 |
|------|------|
| lightrag_query | LightRAG ドキュメント意味検索ツール。`query` と `mode`（hybrid/local/global）を受け取り、関連ドキュメントの内容と出典パスを返す |
| lightrag_list | LightRAG インデックス済みドキュメント一覧ツール。インデックスされているファイルのパス一覧を返す |
| codegraph_explore | CodeGraph コード探索ツール（代表例）。コードの構造・シンボル・呼び出しグラフを探索する |
| codegraph_impact | 変更影響範囲分析ツール。`{impacts: [{name, kind}]}` 形式で影響を受けるシンボル一覧を返す |
| kos_status | 全エンジンの状態（ready/unavailable/indexing）・最終更新日時・インデックス件数・available_tools を返す統合ステータスツール |
| エンジン未起動エラー | LightRAG または CodeGraph のプロセスが到達不能なときに返すエラー。`LIGHTRAG_UNAVAILABLE` / `CODEGRAPH_UNAVAILABLE` のエラーコードと remediation をセットで返す |
| embedded 起動 | MCP Server が LightRAG をサブプロセスとして自動起動・自動停止する方式。オペレーターが LightRAG を独立起動する必要がない（Epic #3 で実装） |
| proxy | FastMCP が外部プロセス（CodeGraph npx）のツールを自サーバーのツールとして公開する機能。`create_proxy()` + `mount(namespace=)` で実現 |
| namespace mount | `FastMCP.mount(server, namespace="codegraph")` により外部サーバーのツールを `codegraph_{tool_name}` に前置して公開すること |

---

## 境界コンテキスト

### このコンテキストが扱う範囲

- MCP Aggregator としての FastMCP サーバー設計（ツール公開・エンジン proxy・エラーハンドリング）
- `lightrag_*` ツールの外部インターフェース仕様（パラメータ・応答形式・エラーコード）
- `codegraph_*` ツールの外部インターフェース仕様（prefix 命名・応答形式・エラーコード）
- `kos_status` ツールの統合ステータス仕様
- エンジン状態モデル（ready / unavailable / indexing）の定義

### このコンテキストが扱わない範囲（隣接コンテキスト）

| 隣接コンテキスト | 担当 Epic | 境界 |
|----------------|-----------|------|
| LightRAG の embedded 起動・プロセス管理 | Epic #3 | MCP Server が LightRAG を subprocess で自動起動する実装は Epic #3 で担当。本 Epic では LightRAG が外部で起動済みであることを前提とする |
| ストレージ配置（`.lightrag/` の対象プロジェクト内配置） | Epic #3 | ストレージの物理的な配置場所の変更は Epic #3 のスコープ |
| `aidd-kos install` コマンド | Epic #4 | MCP 登録・ストレージ初期化を行う CLI は Epic #4 で実装 |
| LightRAG 内部の検索アルゴリズム（Dual-Level Retrieval）| Doc Intelligence | LightRAG の内部実装は本コンテキストの関心外。`lightrag_query` の応答形式と SLA のみを規定する |
| CodeGraph の AST 解析ロジック | Code Intelligence | CodeGraph の内部実装は本コンテキストの関心外。ツール名・応答形式の仕様のみを規定する |

---

## 差し戻し事項（PRD との矛盾・不足）

### 1. [MUST] codegraph_* の 6 ツール名が未定義

AC-F02-02 では 6 ツールを列挙しているが、FRAMEWORK.md から確認済み:
`codegraph_context` / `codegraph_explore` / `codegraph_impact` /
`codegraph_trace` / `codegraph_callers` / `codegraph_callees`。

**対処要求**: 解消済み（docs/spec/mcp-aggregator.md AC-F02-02 に全 6 ツール名を明記）。

### 2. [SHOULD] `lightrag_query` の mode デフォルト値が未定義

AC-F01-02 では mode パラメータの種類は定義済み。
省略時のデフォルトは `hybrid` と docs/spec/mcp-aggregator.md に明記済み。

### 3. [INFO] CodeGraph に `indexing` 状態は不適用

`indexing` は Doc Intelligence Engine（LightRAG）のみ返す状態値。
CodeGraph は `ready` / `unavailable` の 2 状態のみ。
AC-F03-01 に注記済み（docs/spec/mcp-aggregator.md）。
