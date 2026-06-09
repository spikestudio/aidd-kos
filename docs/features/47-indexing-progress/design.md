# インデックス処理中の進捗表示 Design

Feature Issue: #47
Epic: #27

## Spec

docs/spec/status-visibility.md → Feature F02: インデックス処理中の進捗表示 (#47)

## Related Docs（このFeatureが追記・生成するファイル）

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/47-indexing-progress.md | 進捗表示シナリオ（新規）|

## 変更対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `aidd_kos/status.py` | `_check_lightrag()` の pipeline_status レスポンスから `docs`・`cur_batch` を取得 |
| `aidd_kos/cli.py` | `indexing` 状態の表示に `(処理中: N/M 件)` を追加 |
| `mcp_server/server.py` | `kos_status()` の `lightrag` フィールドに `progress` を追加 |

## 設計メモ

### LightRAG pipeline_status API の進捗フィールド（調査済み）

`PipelineStatusResponse`（`lightrag/api/routers/document_routes.py`）:

```text
docs: int = 0       # 総インデックス対象ドキュメント数
cur_batch: int = 0  # 現在処理中のバッチ番号
batchs: int = 0     # 総バッチ数
busy: bool = False  # 処理中フラグ
```

### 進捗マッピング

- `progress.total: int` = `pipeline.docs`（総ドキュメント数）
- `progress.processed: int` = `pipeline.cur_batch`（バッチ進行数）

`docs=0`（進捗情報なし）の場合は `progress = None` → CLI は `LightRAG: indexing` のみ表示。
`docs > 0` の場合は `progress = {"processed": cur_batch, "total": docs}`。

### CLI 出力フォーマット

```text
LightRAG: indexing (処理中: 3/10 件)  ← docs > 0 の場合
LightRAG: indexing                    ← docs = 0 の場合
```

### MCP kos_status レスポンス（Indexing 時の lightrag フィールド）

```json
{
  "lightrag": {
    "status": "indexing",
    "indexed_at": null,
    "doc_count": 0,
    "changed_count": 0,
    "error_code": null,
    "progress": {"processed": 3, "total": 10}
  }
}
```

`progress` フィールドは `indexing` 状態のときのみ存在する（他の状態では `null` または省略）。

### AC-F47-03（Indexing → Ready 遷移）

インデックス処理完了後に `aidd-kos status` を実行すると `pipeline.busy = false` となり、
Feature #46 の Stale 検出ロジックに引き渡される（`last_indexed_at` 更新後なら `ready`、
更新前なら `stale`）。`indexing` 表示が消えることは `busy=false` → `ready/stale` 遷移で保証。

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| stdout | `aidd_kos/cli.py:status()` | `LightRAG: indexing (処理中: N/M 件)` |
| ログ | `mcp_server/server.py:kos_status()` | JSON の `lightrag.progress` フィールド |

## Implementation Tasks

### Spec 追記

- [x] specs/e2e/47-indexing-progress.md 作成
  → 完了条件: AC-F47-01/02/03 が全て 1 件以上のシナリオに対応

### テスト実装（RED）

- [x] ユニットテスト実装（tests/unit/test_status.py に追記）
  → 完了条件: AC-F47-01〜03 をカバーするテストが RED
- [x] E2E テスト実装（tests/e2e/test_status.py に追記）
  → 完了条件: E2E シナリオが RED

### 実装・検証

- [x] `aidd_kos/status.py:_check_lightrag()` に `progress` フィールド追加
  → 完了条件: `busy=true` 時に `progress.total=docs, progress.processed=cur_batch` を返す
- [x] `aidd_kos/cli.py:status()` の indexing 表示に進捗を追加
  → 完了条件: ユニットテスト GREEN + `LightRAG: indexing (処理中: N/M 件)` が表示される
- [x] `mcp_server/server.py:kos_status()` に `progress` フィールド追加
  → 完了条件: ユニットテスト GREEN + AC-F47-02 充足
- [x] リファクタ
  → 完了条件: 全テストが GREEN かつ lint/型チェック PASS
- [x] AC カバレッジ確認
  → 完了条件: `git grep "AC-F47"` で全テストコードが発見できること
