# Spec: ステータス & エラー可視化（Epic #27）

## Feature F01: インデックス状態の 4 値可視化・エラー診断（CLI + MCP）

Issue: #46
Epic: #27

### Stories

| ID | As a | I want to | So that |
|----|------|-----------|---------|
| S1 | AI 駆動開発エンジニア（オペレーター）| `aidd-kos status` を実行したとき、インデックス状態を Ready / Stale / Indexing / Error の 4 値で確認したい | インデックスが最新か・問題があるか・今何が起きているかを追加操作なしに把握できる |
| S2 | AI 駆動開発エンジニア（オペレーター）| インデックス状態が Error のとき、ターミナルに原因コードと具体的な再試行コマンドが表示されてほしい | ログを掘らずに原因と対処方法が分かる |
| S4 | AI Agent（Claude Code / Cursor 等）| `kos_status` MCP ツールの結果に Ready / Stale / Indexing / Error の状態が含まれてほしい | インデックスが最新でない場合に自律的にオペレーターへ再同期を促す判断ができる |

### Acceptance Criteria

| AC ID | Story | Given | When | Then |
|-------|-------|-------|------|------|
| AC-F46-01 | S1 | インデックス済みで、最終インデックス実行後に `mtime > indexed_at` のファイルが 0 件 | `aidd-kos status` を実行する | stdout に `LightRAG: ready` が表示され exit code 0 で終了すること |
| AC-F46-02 | S1 | インデックス済みで、最終インデックス実行後に `mtime > indexed_at` のファイルが 1 件以上存在する | `aidd-kos status` を実行する | stdout に `LightRAG: stale (変更 N 件)` が表示され exit code 0 で終了すること |
| AC-F46-03 | S1 | LightRAG サーバーに接続できない（LIGHTRAG_UNAVAILABLE 状態）| `aidd-kos status` を実行する | stdout に `LightRAG: error` が表示され exit code 0 で終了すること |
| AC-F46-04 | S2 | LightRAG サーバーに接続できない（LIGHTRAG_UNAVAILABLE 状態）| `aidd-kos status` を実行する | stderr に `[LIGHTRAG_UNAVAILABLE] LightRAG サーバーが起動していません。再試行: aidd-kos serve` が出力されること |
| AC-F46-05 | S4 | インデックスが Stale な状態 | `kos_status` MCP ツールを呼び出す | レスポンスの `lightrag.status` フィールドが `"stale"` であること |
| AC-F46-06 | S4 | LightRAG サーバーに接続できない（LIGHTRAG_UNAVAILABLE 状態）| `kos_status` MCP ツールを呼び出す | レスポンスの `lightrag.status` フィールドが `"error"` であり、`lightrag.error_code` フィールドが `"LIGHTRAG_UNAVAILABLE"` であること |

---

## Feature F02: インデックス処理中の進捗表示

Issue: #47
Epic: #27

### Stories F02

| ID | As a | I want to | So that |
|----|------|-----------|---------|
| S3 | AI 駆動開発エンジニア（オペレーター）| インデックス処理中に処理済み件数・総件数が表示されてほしい | いつ完了するかの目安を把握できる |

### Acceptance Criteria F02

| AC ID | Story | Given | When | Then |
|-------|-------|-------|------|------|
| AC-F47-01 | S3 | LightRAG が現在インデックス処理を実行中（処理完了前の状態）| `aidd-kos status` を実行する | stdout に `LightRAG: indexing (処理中: N/M 件)` が表示され exit code 0 で終了すること |
| AC-F47-02 | S3 | LightRAG が現在インデックス処理を実行中（処理完了前の状態）| `kos_status` MCP ツールを呼び出す | レスポンスの `lightrag.status` が `"indexing"` であり、`lightrag.progress.processed` と `lightrag.progress.total` フィールドが数値で存在すること |
| AC-F47-03 | S3 | LightRAG のインデックス処理が完了した直後 | `aidd-kos status` を実行する | stdout に `LightRAG: ready` が表示され `indexing` 表示が消えていること。exit code 0 で終了すること |
