# E2E テスト仕様: F-03 統合ステータス確認（kos_status）

Feature Issue: #7
Epic: #2

| AC ID | シナリオ | 前提データ | 操作手順 | 確認内容 |
|-------|---------|-----------|---------|---------|
| AC-F03-01 | kos_status が両エンジンの状態を返す | LightRAG・CodeGraph が ready | MCP で `kos_status()` を呼び出す | `lightrag`・`codegraph` 両キーの状態（ready/unavailable/indexing）が含まれること |
| AC-F03-01 | LightRAG が unavailable の場合 | LightRAG が未起動 | MCP で `kos_status()` を呼び出す | `lightrag.status == "unavailable"` が返ること |
| AC-F03-01 | LightRAG が indexing の場合 | LightRAG がインデックス中 | MCP で `kos_status()` を呼び出す | `lightrag.status == "indexing"` が返ること |
| AC-F03-02 | --json フラグで JSON 出力 | — | CLI で `aidd-kos status --json` を実行 | JSON としてパース可能な出力が得られること |
| AC-F03-03 | available_tools フィールドが含まれる | LightRAG・CodeGraph が ready | MCP で `kos_status()` を呼び出す | `available_tools` フィールドに `lightrag_query`・`codegraph_explore` が含まれること |
