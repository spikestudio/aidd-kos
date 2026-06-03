# ADR-002: FastMCP process proxy による CodeGraph MCP 統合方式

| 項目 | 内容 |
|------|------|
| ステータス | 承認済み |
| 日付 | 2026-06-03 |
| 決定者 | sanojimaru |

## コンテキスト

aidd-kos は Python/FastMCP で実装された MCP Aggregator として動作し、
複数のナレッジエンジンのツールを単一エンドポイントに束ねる（CHARTER §9 MCP Aggregator パターン）。

CodeGraph（`@colbymchenry/codegraph`）は Node.js/npm パッケージとして提供されており、
Python MCP Server から `codegraph_*` ツールを AI Agent に公開するには、
外部プロセスとして起動して proxy する仕組みが必要。

FastMCP 3.4.x の `NpxStdioTransport` + `create_proxy()` + `mount(namespace=...)` が
この用途の公式サポート API として確認済み（`docs/research/fastmcp-aggregator.md`）。

## 決定事項

**FastMCP `NpxStdioTransport` + `create_proxy()` + `mount(namespace="codegraph")` を採用する。**

```python
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

`namespace="codegraph"` により、CodeGraph の全ツール名に `codegraph_` prefix が自動付与される。
将来エンジンを追加する際も同パターンで拡張できる。

## 根拠

1. **実装量最小**: FastMCP の公式 API を使うことで約 10 行で実装完了
2. **prefix 自動付与**: `namespace="codegraph"` により `codegraph_explore` 等が自動生成され、ADR-001 のエラーコード命名規則と同様の一貫性を確保
3. **CodeGraph 更新追従**: proxy 方式のため CodeGraph のツール追加・変更が自動反映される
4. **拡張パターン確立**: 将来の Engine N 追加も同パターンで実現可能

## 代替案

### 代替案 A: FastMCP `NpxStdioTransport` + `create_proxy()` + `mount()`（**採用**）

- メリット: 実装量最小・prefix 自動付与・拡張パターン確立
- デメリット: FastMCP バージョン依存（API 変更時に追従が必要）

### 代替案 B: 独自実装（MCP JSON-RPC クライアントで手動ツール転送）

- メリット: FastMCP 非依存
- デメリット: 実装コスト中規模・Engine 追加のたびに実装が必要

### 代替案 C: CodeGraph の機能を Python で再実装

- メリット: 外部 npm 依存なし
- デメリット: AST 解析・呼び出しグラフ構築等の実装コストが非現実的。CodeGraph の更新に手動追従が必要

## 影響・トレードオフ

- **影響を受けるコンポーネント:** `mcp_server/server.py`・Epic #2 全 Feature（#5/6/7）
- **影響を受ける Epic / Phase:** Epic #2（MCP Aggregator 実装）・将来の Engine 追加 Epic
- **Charter §10 採用方針との関係:** 該当なし（FastMCP は既採用技術スタック）
- **マスタドキュメントの更新:** `docs/architecture/baseline.md` §MCP Aggregator パターンに実装例を追記
- **トレードオフ:** FastMCP 3.4.x の `NpxStdioTransport` API に依存する。
  FastMCP のメジャーバージョンアップ時に API 変更があれば追従が必要（`docs/research/fastmcp-aggregator.md` で非推奨 API を記録済み）。
  PATH 環境変数の明示的な引き渡し（`env_vars={"PATH": ...}`）が必要な場合がある（STDIO 環境変数の非継承問題）。
