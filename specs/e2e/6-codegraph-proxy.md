# E2E テスト仕様: F-02 CodeGraph コード検索ツール統合

Feature Issue: #6
Epic: #2

| AC ID | シナリオ | 前提データ | 操作手順 | 確認内容 |
|-------|---------|-----------|---------|---------|
| AC-F02-01 | aidd-kos 1本で codegraph_explore が応答する | aidd-kos MCP 1本のみ登録 | MCP で `codegraph_explore` ツールを呼び出す | exit_code 0・エラーなし |
| AC-F02-02 | Phase 1 の 6 ツールが利用可能 | 同上 | MCP の tools/list を取得する | `codegraph_explore`・`codegraph_impact`・`codegraph_context`・`codegraph_callers`・`codegraph_callees`・`codegraph_trace` が含まれること |
| AC-F02-03 | 全 CodeGraph ツールが codegraph_ prefix | 同上 | MCP の tools/list を取得する | CodeGraph 由来の全ツール名が `codegraph_` で始まること |
| AC-F02-04 | codegraph_impact が impacts リストを返す | .codegraph/ 初期化済み | `codegraph_impact(symbol="FooClass")` を呼び出す | `{impacts: [{name, kind}]}` 形式のレスポンスが返ること |
| AC-F02-05 | 影響がない場合は空リストを返す | 同上 | 存在しないシンボルで `codegraph_impact` を呼び出す | 空リストが返ること |
| AC-F02-06 | CodeGraph 未初期化時に CODEGRAPH_UNAVAILABLE が返る | .codegraph/ なし | `codegraph_explore` を呼び出す | `CODEGRAPH_UNAVAILABLE` を含むレスポンスが返ること |
| AC-F02-07 | エラー時に 3 秒以内に stderr へ出力 | 同上 | `codegraph_explore` を呼び出す | 3 秒以内に stderr へエラーコードが出力されること |
