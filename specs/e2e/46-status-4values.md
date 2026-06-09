# E2E Spec: インデックス状態の 4 値可視化・エラー診断（CLI + MCP）

Feature: #46
Epic: #27

## CLI シナリオ

| AC ID | インターフェース | 前提データ | 操作手順 | 確認内容 |
|-------|--------------|----------|---------|---------|
| AC-F46-01 | CLI | `.lightrag/last_indexed_at` が存在し、プロジェクト内の `.md`/`.txt` ファイルの mtime が全て `last_indexed_at` 以前 | `aidd-kos status` を実行する | stdout に `LightRAG: ready` が含まれ、exit code が 0 であること |
| AC-F46-02 | CLI | `.lightrag/last_indexed_at` が存在し、1 件以上の `.md`/`.txt` ファイルの mtime が `last_indexed_at` より新しい | `aidd-kos status` を実行する | stdout に `LightRAG: stale (変更 N 件)` が含まれ、exit code が 0 であること（N は変更ファイル数）|
| AC-F46-03 | CLI | LightRAG HTTP サーバーが停止しており、in-process MCP も未起動 | `aidd-kos status` を実行する | stdout に `LightRAG: error` が含まれ、exit code が 0 であること |
| AC-F46-04 | CLI | AC-F46-03 と同じ条件 | `aidd-kos status` を実行する | stderr に `[LIGHTRAG_UNAVAILABLE] LightRAG サーバーが起動していません。再試行: aidd-kos serve` が含まれること |

## MCP シナリオ

| AC ID | インターフェース | 前提データ | 操作手順 | 確認内容 |
|-------|--------------|----------|---------|---------|
| AC-F46-05 | MCP | `.lightrag/last_indexed_at` が存在し、1 件以上の `.md`/`.txt` ファイルの mtime が `last_indexed_at` より新しい | `kos_status` MCP ツールを呼び出す | レスポンスの JSON から `lightrag.status` が `"stale"` であること |
| AC-F46-06 | MCP | `_rag` が `None`（LightRAG 未初期化）| `kos_status` MCP ツールを呼び出す | レスポンスの JSON から `lightrag.status` が `"error"` かつ `lightrag.error_code` が `"LIGHTRAG_UNAVAILABLE"` であること |
