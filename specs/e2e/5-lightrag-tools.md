# E2E テスト仕様: F-01 LightRAG ドキュメント検索ツール提供

Feature Issue: #5
Epic: #2

| AC ID | シナリオ | 前提データ | 操作手順 | 確認内容 |
|-------|---------|-----------|---------|---------|
| AC-F01-01 | lightrag_query が関連ドキュメントと出典パスを返す | LightRAG が起動済み・ドキュメントがインデックス済み | MCP で `lightrag_query(query="OAuth token")` を呼び出す | レスポンスに文書内容と出典ファイルパスが含まれること |
| AC-F01-02 | mode パラメータが指定できる（hybrid） | 同上 | `lightrag_query(query="test", mode="hybrid")` を呼び出す | exit code 0・エラーなし |
| AC-F01-02 | mode パラメータが指定できる（local） | 同上 | `lightrag_query(query="test", mode="local")` を呼び出す | exit code 0・エラーなし |
| AC-F01-02 | mode デフォルトは hybrid | 同上 | `lightrag_query(query="test")` を呼び出す（mode 省略）| デフォルト "hybrid" で実行されること |
| AC-F01-02 | 無効な mode はエラーを返す | — | `lightrag_query(query="test", mode="invalid")` を呼び出す | エラーレスポンスが返ること |
| AC-F01-03 | lightrag_list がドキュメント一覧を返す | ドキュメントがインデックス済み | MCP で `lightrag_list()` を呼び出す | ファイルパスの一覧が返されること |
| AC-F01-04 | インデックスが空なら空リストを返す | インデックスが空 | MCP で `lightrag_list()` を呼び出す | 空リストが返されること |
| AC-F01-05 | LIGHTRAG_UNAVAILABLE エラーが返る | LightRAG が未起動 | MCP で `lightrag_query(query="test")` を呼び出す | `LIGHTRAG_UNAVAILABLE` を含むエラーレスポンスが返ること |
| AC-F01-06 | エラー時に 3 秒以内に stderr へ出力 | LightRAG が未起動 | MCP で `lightrag_query(query="test")` を呼び出す | 3 秒以内に stderr へエラーコードと対処方法が出力されること |
| AC-F01-06 | lightrag_list エラー時も stderr 出力 | LightRAG が未起動 | MCP で `lightrag_list()` を呼び出す | 3 秒以内に stderr へ `LIGHTRAG_UNAVAILABLE` が出力されること |
| TD-01 | タイムアウト 5 秒でエラーを返す | LightRAG が応答に 6 秒かかる（モック） | MCP で `lightrag_query(query="test")` を呼び出す | 5 秒以内に `QUERY_TIMEOUT` エラーが返ること |
