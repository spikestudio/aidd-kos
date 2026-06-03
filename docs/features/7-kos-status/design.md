# 統合ステータス確認（kos_status）Design

Feature Issue: #7
Epic: #2

## Spec

docs/spec/mcp-aggregator.md → Feature F-03

## 変更内容

`get_status`（deprecated）を `kos_status` に置き換える。

- `aidd_kos.status.StatusChecker` を使い LightRAG・CodeGraph 両エンジンの状態を返す
- `available_tools` フィールドを含む（AC-F03-03）
- LightRAG の状態: ready / unavailable / indexing

## Implementation Tasks

- [x] `kos_status` MCP ツールを `mcp_server/server.py` に実装
- [x] E2E テスト実装（全 AC GREEN）
