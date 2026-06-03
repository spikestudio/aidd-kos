# 全ナレッジエンジンが対象プロジェクトを正しく参照する Design

Feature Issue: #15
Epic: #3

## Spec

docs/spec/embedded-startup.md → Feature: F-02 (#15)

## 変更内容

`lightrag_query` にインデックス未構築チェックを追加する。
`.lightrag/` のパス正確性・CodeGraph の cwd 継承は Feature #14 完了時点で達成済み。

| 変更ファイル | 変更内容 | 対応 AC |
|------------|---------|---------|
| `aidd_kos/errors.py` | `LIGHTRAG_INDEX_NOT_FOUND` エラーコード追加（ADR-001 準拠）| AC-F15-02 |
| `mcp_server/server.py` | `lightrag_query` にインデックス未構築チェック追加 | AC-F15-02 |

**インデックス未構築チェック設計:**

```text
lightrag_query 呼び出し時
  └→ lightrag_dir = Path.cwd() / ".lightrag"
  └→ index_ready = lightrag_dir.exists() AND .lightrag/ に .json/.graphml ファイルが存在する
  └→ index_ready=False:
       emit_error(LIGHTRAG_INDEX_NOT_FOUND, "aidd-kos index を実行してください")
       return "LIGHTRAG_INDEX_NOT_FOUND: ..."
  └→ index_ready=True:
       既存の HTTP クエリ処理へ
```

**AC-F15-01・F15-03・F15-04・F15-05 は既実装で達成済み:**

| AC | 達成手段 |
|----|---------|
| AC-F15-01（プロジェクト A のみ参照）| Feature #14 の `_lifespan` が `--working-dir Path.cwd()/.lightrag` で LightRAG 起動 |
| AC-F15-03（`.lightrag/` 配置確認）| `aidd_kos/index.py` が `Path.cwd()` を使用（実装済み）|
| AC-F15-04（再インデックスで同 `.lightrag/` 更新）| `aidd_kos/index.py` の `scan` API が同ディレクトリを使用（実装済み）|
| AC-F15-05（codegraph ファイルパスが target-project 配下）| `NpxStdioTransport(project_directory=None)` → 親 cwd 継承（確認済み）|

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/15-embedded-f02.md | 対象プロジェクト参照正確性・インデックス未構築シナリオ（新規）|

※ openapi.yaml・schema.sql の変更なし

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| エラー | `mcp_server/server.py:lightrag_query()` インデックスチェック時 | `LIGHTRAG_INDEX_NOT_FOUND` + 対処手順を stderr へ（即時）|

## Implementation Tasks

### Spec 追記

- [x] `specs/e2e/15-embedded-f02.md` 作成
  → 完了条件: AC-F15-01〜05 全 5 件がシナリオに対応している

### テスト実装（RED）

- [x] E2E テスト `tests/e2e/test_embedded_f02.py` 実装（12 件）
- [x] ユニットテスト `tests/unit/test_index_check.py` 実装（6 件）

### 実装・検証

- [x] `aidd_kos/errors.py` に `LIGHTRAG_INDEX_NOT_FOUND` 追加
- [x] `mcp_server/server.py` の `lightrag_query` にインデックスチェック追加
- [x] `tests/e2e/conftest.py` autouse fixture 追加（既存テストとの互換性維持）
- [x] 全テスト GREEN（99 passed）
- [x] ruff check PASS
