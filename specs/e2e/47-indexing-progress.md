# E2E Spec: インデックス処理中の進捗表示

Feature: #47
Epic: #27

## CLI シナリオ

| AC ID | インターフェース | 前提データ | 操作手順 | 確認内容 |
|-------|--------------|----------|---------|---------|
| AC-F47-01 | CLI | LightRAG HTTP が busy=true, docs=10, cur_batch=3 を返す | `aidd-kos status` を実行する | stdout に `LightRAG: indexing (処理中: 3/10 件)` が含まれ、exit code が 0 であること |
| AC-F47-01-edge | CLI | LightRAG HTTP が busy=true, docs=0, cur_batch=0 を返す（進捗情報なし）| `aidd-kos status` を実行する | stdout に `LightRAG: indexing` が含まれ `(処理中:` が含まれないこと。exit code が 0 であること |
| AC-F47-03 | CLI | LightRAG HTTP が busy=false を返し、`.lightrag/last_indexed_at` が現在時刻以降に設定済みで変更ファイルが 0 件 | `aidd-kos status` を実行する | stdout に `LightRAG: ready` が含まれ `indexing` が含まれないこと。exit code が 0 であること |

## MCP シナリオ

| AC ID | インターフェース | 前提データ | 操作手順 | 確認内容 |
|-------|--------------|----------|---------|---------|
| AC-F47-02 | MCP | LightRAG が busy=true, docs=10, cur_batch=3 の pipeline_status を返す | `kos_status` MCP ツールを呼び出す | レスポンスの JSON から `lightrag.status` が `"indexing"` であり、`lightrag.progress.processed` と `lightrag.progress.total` が数値で存在すること |
