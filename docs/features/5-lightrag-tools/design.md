# LightRAG ドキュメント検索ツール提供 Design

Feature Issue: #5
Epic: #2

## Spec

docs/spec/mcp-aggregator.md → Feature F-01

## 変更内容

`mcp_server/server.py` の既存ツール名をリネームし品質を改善する:

| 変更前 | 変更後 | 対応 AC |
|--------|--------|---------|
| `query_documents` | `lightrag_query` | AC-F01-01/02 |
| `list_documents` | `lightrag_list` | AC-F01-03/04 |
| タイムアウト 60秒 | 5秒（`LIGHTRAG_QUERY_TIMEOUT_MS` env で上書き可） | TD-01 解消 |
| mode: 無検証 | allowlist: `{"hybrid","mix","local","global","naive"}` | AC-F01-02 |
| エラー: 例外のみ | stderr へ ADR-001 エラーコード出力 | AC-F01-05/06・TD-02 解消 |

**`get_status` の扱い:** F-03（`kos_status`）で置き換える。F-01 完了時点では残存させ、F-03 実装時に削除する。

**FastMCP instructions 更新:** `"Use lightrag_query to search..."` に変更（S-2 対応）

**依存方向:** `server.py`（Interface Layer）が `httpx` 経由で LightRAG API を呼ぶ構造は baseline.md N-5 の既知負債として継続。F-01 はこの負債を増やさない範囲に留まる。

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/5-lightrag-tools.md | lightrag_query/list 全 AC シナリオ（新規）|
| 技術的負債 | docs/architecture/baseline.md | TD-01・TD-02 を解消済みに更新 |

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| ログ | `server.py:lightrag_query()` 開始時 | クエリ文字列（マスク済み）・mode を stdout |
| エラー | `server.py:lightrag_query()` except 節 | `LIGHTRAG_UNAVAILABLE` / `QUERY_TIMEOUT` を stderr へ（3秒以内）|
| エラー | `server.py:lightrag_list()` except 節 | `LIGHTRAG_UNAVAILABLE` を stderr へ（3秒以内）|

## Implementation Tasks

### Spec 追記

- [ ] `specs/e2e/5-lightrag-tools.md` 作成
  → 完了条件: 全 AC-F01-01〜06 + QUERY_TIMEOUT シナリオが1件以上対応

### テスト実装（RED）

- [ ] E2E テスト実装（specs/e2e/5-lightrag-tools.md 全シナリオ）
  → 完了条件: pytest が全シナリオで失敗（RED）

### 実装

- [ ] `query_documents` → `lightrag_query` にリネーム（mode allowlist・タイムアウト 5秒・QUERY_TIMEOUT エラー・stderr 出力）
- [ ] `list_documents` → `lightrag_list` にリネーム（タイムアウト・stderr 出力）
- [ ] FastMCP `instructions` を `"Use lightrag_query to search..."` に更新
- [ ] `QUERY_TIMEOUT` エラーコードを `aidd_kos/errors.py` に追加（ADR-001 準拠）

### 検証

- [ ] 全テスト GREEN
- [ ] `uv run ruff check . && uv run ruff format --check .` PASS
- [ ] TD-01・TD-02 が baseline.md で解消済みに更新されていること
