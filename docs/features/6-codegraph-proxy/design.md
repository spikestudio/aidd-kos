# CodeGraph コード検索ツール統合 Design

Feature Issue: #6
Epic: #2

## Spec

docs/spec/mcp-aggregator.md → Feature F-02

## 変更内容

ADR-002 の実装: FastMCP `NpxStdioTransport` + `create_proxy()` + `mount(namespace="codegraph")` で
CodeGraph の 6 ツールを aidd-kos MCP Server に proxy 統合する。

```python
# mcp_server/server.py に追加
from fastmcp.client.transports import NpxStdioTransport
from fastmcp.server import create_proxy

_codegraph_proxy = create_proxy(
    NpxStdioTransport(
        package="@colbymchenry/codegraph",
        args=["serve"],
        env_vars={"PATH": os.environ.get("PATH", "")},
    )
)
mcp.mount(_codegraph_proxy, namespace="codegraph")
```

`namespace="codegraph"` により `codegraph_explore`・`codegraph_impact` 等が自動公開される。

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/6-codegraph-proxy.md | codegraph_* 全 AC シナリオ |
| ADR | docs/architecture/adr/ADR-002-fastmcp-process-proxy.md | 参照 |

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| ログ | `server.py` モジュール初期化時 | CodeGraph proxy のマウント成功/失敗を stdout |
| エラー | CodeGraph 未起動/未初期化時 | `kos_status` の `codegraph.status` が `"unavailable"` になること（AC-F02-06）。stderr タイムアウト出力（AC-F02-07、手動確認）|

## Implementation Tasks

### Spec 追記

- [x] `specs/e2e/6-codegraph-proxy.md` 作成
  → 完了条件: 全 AC-F02-01〜07 が1件以上のシナリオに対応

### テスト実装（RED）

- [x] E2E テスト実装（specs/e2e/6-codegraph-proxy.md 全シナリオ）
  → 完了条件: pytest が全シナリオで失敗（RED）

### 実装

- [x] `mcp_server/server.py` に CodeGraph proxy を追加（ADR-002 準拠）
  → PATH 環境変数を明示的に渡す（ADR-002 §トレードオフ参照）

### 検証

- [x] 全テスト GREEN
- [x] `uv run ruff check . && uv run ruff format --check .` PASS
