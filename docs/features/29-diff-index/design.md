# 変更・追加されたファイルだけが再インデックスされる Design

Feature Issue: #29
Epic: #25

## Spec

docs/spec/index-sync.md → Feature: 変更・追加されたファイルだけが再インデックスされる (#29)

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/29-diff-index.md | 差分インデックス E2E シナリオ（新規）|
| 実装 | aidd_kos/index.py | IndexOrchestrator に差分ロジック追加 |
| テスト | tests/unit/test_index.py | 差分ロジックのユニットテスト追記 |
| テスト | tests/e2e/test_index_f29.py | 差分インデックス E2E テスト（新規）|

## 設計概要

LightRAG の `POST /documents/paginated` を正規ソースとして使い、
aidd-kos 側に状態ファイルを持たずに差分を検出する。

```text
run() の処理フロー:
  1. POST /documents/paginated (全件取得、ページネーション対応)
     → {file_path: {id, updated_at}} の辞書を構築
  2. collect_files() でファイルシステムの対象ファイルを収集
  3. 分類:
     - rel_path が LightRAG にない → new（追加）
     - rel_path が LightRAG にある & mtime > updated_at → modified（更新）
     - rel_path が LightRAG にある & mtime ≤ updated_at → skip（スキップ）
  4. new + modified のファイルを既存 _send_batch ロジックで送信
  5. 出力: 「差分モード: 追加 N 件・更新 M 件・削除 K 件・スキップ L 件 (Xs)」
     ※ F29 では削除ロジックを持たないため K は常に 0。F30（#30）が実値を埋める
```

**LightRAG API（.venv 内の document_routes.py:4160 および DocStatusResponse:624 で実在確認済み）:**

- エンドポイント: `POST {LIGHTRAG_URL}/documents/paginated`
- リクエスト: `{"page": 1, "page_size": 500, "status_filter": null}`
- レスポンス: `PaginatedDocsResponse.documents[].{file_path, id, updated_at}`
- ページネーション: `total_count > page_size` の場合は page を増やして全件取得

**mtime 比較（タイムゾーン注意）:**

- LightRAG の `updated_at` は naive UTC 文字列で返る可能性がある
- `datetime.fromisoformat(updated_at).replace(tzinfo=timezone.utc).timestamp()` で明示的に UTC として扱う
- `file.stat().st_mtime` (Unix timestamp float, UTC) と比較
- `st_mtime > updated_at_timestamp` → 変更あり

**`--full` フラグについて:**

- F29 実装時点では `--full` フラグは存在しない（F31 が追加する）
- AC-F29-05 の「`--full` なし」注釈は F31 実装後の区別を示すもの
- F29 の E2E テストでは `aidd-kos index` のみテストし、`--full` フラグへの言及は不要

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| stdout | `IndexOrchestrator.run()` の最終出力 | 追加・更新・スキップ件数と所要時間 |
| stdout | `IndexOrchestrator.run()` の開始ログ | 差分インデックス開始ログ |

## Implementation Tasks

### Spec 追記

- [ ] specs/e2e/29-diff-index.md 作成
  → 完了条件: AC-F29-01〜05 が全て 1 件以上のシナリオに対応している

### テスト実装（RED）

- [ ] tests/e2e/test_index_f29.py 実装（AC-F29-01〜05 を E2E でカバー）
  → 完了条件: 全テストが RED（IndexOrchestrator が差分ロジックを持たないため失敗）
- [ ] tests/unit/test_index.py に差分ロジックのユニットテストを追記
  → 完了条件: `_fetch_indexed_docs`・`_classify_files` のテストが RED

### 実装

- [ ] `IndexOrchestrator._fetch_indexed_docs()` 実装
  → 完了条件: `POST /documents/paginated` を全ページ取得し `{file_path: {id, updated_at}}` を返す
- [ ] `IndexOrchestrator._classify_files()` 実装
  → 完了条件: new / modified / skip の 3 分類を返す
- [ ] `IndexOrchestrator.run()` を差分モードに変更
  → 完了条件: new + modified のみ送信し、出力形式が「差分モード: 追加 N・更新 M・スキップ L (Xs)」になる
- [ ] `aidd_kos/cli.py` の index コマンド出力を新フォーマットに合わせて更新
  → 完了条件: 全 E2E テストが GREEN

### 検証

- [ ] リファクタ
  → 完了条件: 全テスト GREEN かつ `uv run ruff check` / `uv run ruff format --check` PASS
- [ ] AC カバレッジ確認
  → 完了条件: `git grep "AC-F29"` で全 AC-ID がテストに存在する
