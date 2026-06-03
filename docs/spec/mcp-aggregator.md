# Spec: MCP Aggregator

Epic: #2 MCP Aggregator 実装
Milestone: Core MVP（#1）

---

## Feature: LightRAG ドキュメント検索ツール提供 (F-01)

### Story S-01: ドキュメントを意味検索できる

As an AI Agent, I want to search project knowledge with `lightrag_query`,
so that I can find relevant design documents, ADRs, and meeting notes for my current task.

根拠: [ユーザー入力]

**AC:**

| ID | 条件 |
|----|------|
| AC-F01-01 | `lightrag_query(query="OAuth token")` を呼び出すと関連ドキュメントの内容と出典ファイルパスを含むレスポンスが返されること |
| AC-F01-02 | `mode` パラメータ（"hybrid" / "local" / "global"）を指定でき、デフォルトは "hybrid" であること |

**非機能 AC（F-01 全体）:** クエリ応答 P95 ≤ 2 秒（1 万ドキュメント規模）

---

### Story S-02: インデックス済みドキュメントを一覧確認できる

As an AI Agent, I want to see which documents are indexed with `lightrag_list`,
so that I can understand the scope of available knowledge and avoid unnecessary queries.

根拠: [ユーザー入力]

**AC:**

| ID | 条件 |
|----|------|
| AC-F01-03 | `lightrag_list()` を呼び出すとインデックス済みドキュメントのパス一覧が返されること |
| AC-F01-04 | インデックスが空の場合は空リストが返されること |

---

### Story S-03: LightRAG 未起動時に構造化エラーを受け取れる

As an AI Agent, I want to receive a structured error when LightRAG is unavailable,
so that I can report the issue with a clear diagnosis.

根拠: Charter §NFR「障害時は 3 秒以内に stderr へエラーコードと対処方法を出力」、[AI補完: エラーケース]

**AC:**

| ID | 条件 |
|----|------|
| AC-F01-05 | LightRAG サーバー未起動時に `{"error": "LIGHTRAG_UNAVAILABLE", "remediation": "task server:start を実行してください"}` を含むレスポンスが返されること |
| AC-F01-06 | エラー発生時に 3 秒以内に stderr へエラーコードと対処手順が出力されること |

---

## Feature: CodeGraph コード検索ツール統合 (F-02)

### Story S-04: コード検索ツールをドキュメント検索と同一 MCP エンドポイントで使える

As an AI Agent, I want to access code search tools through the same MCP endpoint as document search,
so that I can combine code and document knowledge without managing multiple MCP configurations.

根拠: [ユーザー入力], [Problem Statement]

**AC:**

| ID | 条件 |
|----|------|
| AC-F02-01 | `aidd-kos` 1 本のみを MCP 登録した状態で `codegraph_explore` が応答すること |
| AC-F02-02 | Phase 1 時点で以下 6 ツールが利用可能であること: `codegraph_context` / `codegraph_explore` / `codegraph_impact` / `codegraph_trace` / `codegraph_callers` / `codegraph_callees` |
| AC-F02-03 | 全 CodeGraph ツール名が `codegraph_` prefix で始まること |

---

### Story S-05: コード変更の影響範囲を分析できる

As an AI Agent, I want to analyze code change impact with `codegraph_impact`,
so that I can assess the blast radius before suggesting modifications.

根拠: [ユーザー入力]

**AC:**

| ID | 条件 |
|----|------|
| AC-F02-04 | `codegraph_impact(symbol="FooClass")` を呼び出すと `{"impacts": [{"name": string, "kind": string}]}` 形式のリストが返されること |
| AC-F02-05 | 影響がない場合は空リストが返されること |

---

### Story S-06: CodeGraph 未起動時に構造化エラーを受け取れる

As an AI Agent, I want to receive a structured error when CodeGraph is unavailable,
so that I can fall back to other knowledge sources.

根拠: Charter §NFR「障害時は 3 秒以内に stderr へエラーコードと対処方法を出力」、[AI補完: エラーケース]

**AC:**

| ID | 条件 |
|----|------|
| AC-F02-06 | CodeGraph インデックス未初期化時に `{"error": "CODEGRAPH_UNAVAILABLE", "remediation": "task codegraph:init を実行してください"}` を含むレスポンスが返されること |
| AC-F02-07 | エラー発生時に 3 秒以内に stderr へエラーコードと対処手順が出力されること |

---

## Feature: 統合ステータス確認 (F-03)

### Story S-07: 全エンジンの状態と利用可能ツールを一括確認できる

As an AI 駆動開発エンジニア（オペレーター）and AI Agent, I want to check all engine statuses and available tools with `kos_status`,
so that I can verify the system is ready and decide which tools to use for the current task.

根拠: [ユーザー入力]

**AC:**

| ID | 条件 |
|----|------|
| AC-F03-01 | `kos_status()` を呼び出すと LightRAG・CodeGraph 両エンジンの状態（`ready` / `unavailable` / `indexing`）を含む JSON が返されること（CodeGraph は `ready` / `unavailable` のみ） |
| AC-F03-02 | 各エンジンについてインデックス日時・ドキュメント数（LightRAG）またはノード数（CodeGraph）が含まれること |
| AC-F03-03 | レスポンスに `available_tools: ["lightrag_query", "lightrag_list", "codegraph_context", ...]` フィールドが含まれること |
