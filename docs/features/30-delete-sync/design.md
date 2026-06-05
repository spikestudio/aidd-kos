# 削除したファイルがインデックスから取り除かれる Design

Feature Issue: #30
Epic: #25

## Spec

docs/spec/index-sync.md → Feature: 削除したファイルがインデックスから取り除かれる (#30)

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/30-delete-sync.md | 削除検出 E2E シナリオ（新規）|
| 実装 | aidd_kos/index.py | IndexOrchestrator に削除検出・DELETE API 呼び出しを追加 |
| テスト | tests/unit/test_index_f30.py | 削除ロジックのユニットテスト（新規）|
| テスト | tests/e2e/test_index_f30.py | 削除 E2E テスト（新規）|

## 設計概要

F29 で実装した `_fetch_indexed_docs()` の戻り値と `collect_files()` の差分から削除ファイルを検出し、
LightRAG の `DELETE /documents/delete_document` API で除去する。

```text
run() の拡張フロー:
  1. _fetch_indexed_docs() → {file_path: {id, updated_at}}
  2. collect_files() → filesystem ファイル一覧
  3. filesystem 相対パス集合を生成（F29 の _classify_files() と同じ正規化:
     str(f.relative_to(self.project_dir)) を使用）
  4. 削除検出: indexed のキー集合 - filesystem 相対パス集合 → deleted_docs
  5. deleted_docs が空でない場合のみ DELETE API を呼び出す（空の場合はスキップ）
  6. _classify_files() で new/modified/skip を分類（変更なし）
  7. new + modified を POST /documents/texts で送信（変更なし）
  8. 出力: 「差分モード: 追加 N 件・更新 M 件・削除 K 件・スキップ L 件 (Xs)」
     K = deleted_count（F29 で 0 ハードコードだった箇所が実値に変わる）
```

**LightRAG DELETE API（document_routes.py:3957 で実在確認済み）:**

- エンドポイント: `DELETE {LIGHTRAG_URL}/documents/delete_document`
- リクエスト: `{"doc_ids": ["doc_id1", ...], "delete_file": false, "delete_llm_cache": false}`
- `doc_ids` は `_fetch_indexed_docs()` が返す `id` フィールド
- 空 `doc_ids` はバリデーションエラーになるため、削除対象ゼロ件の場合は呼び出しをスキップする
- 削除件数が少ない（プロジェクト規模）ため 1 リクエスト全件送信を選択する

**パス正規化の統一:**

- `_detect_deleted()` では `str(f.relative_to(self.project_dir))` を使わず
  indexed の key（= `_fetch_indexed_docs()` が返す `file_path`）と
  filesystem から生成した相対パス文字列（`str(f.relative_to(self.project_dir))`）を比較する
- `_classify_files()` と同一ロジックのため誤検出なし

**run() 戻り値への `deleted_count` 追加:**

```python
return {
    "new_count": ...,
    "updated_count": ...,
    "skip_count": ...,
    "deleted_count": deleted_count,  # F30 で追加
    "elapsed_seconds": ...,
    "file_count": ...,  # backward compat
}
```

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| stdout | `IndexOrchestrator.run()` 差分モード出力 | 削除件数「削除 K 件」が実値になる |
| HTTP | `DELETE /documents/delete_document` 呼び出し | 正しい doc_id が渡されていること（AC-F30-02）|

## Implementation Tasks

### Spec 追記

- [ ] specs/e2e/30-delete-sync.md 作成
  → 完了条件: AC-F30-01・AC-F30-02 が 1 件以上のシナリオに対応している

### テスト実装（RED）

- [ ] tests/e2e/test_index_f30.py 実装（AC-F30-01・AC-F30-02 E2E テスト）
  → 完了条件: 全テストが RED
- [ ] tests/unit/test_index_f30.py 実装（削除検出・DELETE API 呼び出しユニットテスト）
  → 完了条件: 全テストが RED

### 実装

- [ ] `IndexOrchestrator._detect_deleted()` 実装
  → 完了条件: `str(f.relative_to(project_dir))` と同一正規化で indexed との差分から `{file_path: doc_id}` を返す
- [ ] `IndexOrchestrator._delete_docs()` 実装
  → 完了条件: `deleted_docs` が空でなければ DELETE API を呼び出し deleted_count を返す。空の場合は 0 を返す
- [ ] `IndexOrchestrator.run()` に deleted_count を追加
  → 完了条件: `result["deleted_count"]` が存在し実値が入る
- [ ] `aidd_kos/cli.py` の削除 0 件ハードコードを `result['deleted_count']` に置き換える
  → 完了条件: 全テスト GREEN

### 検証

- [ ] リファクタ + `uv run ruff check` / `uv run ruff format --check` PASS
- [ ] AC カバレッジ確認: `git grep "AC-F30"` で全 AC-ID がテストに存在する
