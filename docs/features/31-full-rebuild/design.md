# 全件再構築で確実にインデックスを最新化できる Design

Feature Issue: #31
Epic: #25

## Spec

docs/spec/index-sync.md → Feature: 全件再構築で確実にインデックスを最新化できる (#31)

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| 実装 | aidd_kos/index.py | `run(full=False)` パラメータ追加 |
| 実装 | aidd_kos/cli.py | `index --full` フラグ追加 |
| テスト | tests/unit/test_index_f31.py | 全件再構築のユニットテスト（新規）|
| テスト | tests/e2e/test_index_f31.py | 全件再構築 E2E テスト（新規）|

## 設計概要

`aidd-kos index --full` で差分ロジックをバイパスし全ファイルを処理する。

```text
run(full=True) のフロー:
  1. collect_files() → filesystem ファイル一覧
  2. _fetch_indexed_docs()・_detect_deleted()・_classify_files() をスキップ
  3. 全ファイルを POST /documents/texts で送信
  4. 出力: 「全件再構築モード: N 件 (Xs)」
     ※ 差分モード出力とは別の行になる
```

```text
run(full=False) のフロー（変更なし・F29/F30 実装済み）:
  → 差分モード出力
```

**CLIフラグ追加:**

```python
@app.command()
def index(
    path: ...,
    full: bool = typer.Option(False, "--full", help="全件再構築モードで実行する"),
) -> None:
```

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| stdout | `cli.py index` | 「全件再構築モード: N 件」が表示される |

## Implementation Tasks

### テスト実装（RED）

- [ ] tests/e2e/test_index_f31.py 実装（AC-F31-01・AC-F31-02）
- [ ] tests/unit/test_index_f31.py 実装

### 実装

- [ ] `IndexOrchestrator.run(full: bool = False)` に `full` パラメータ追加
  → `full=True` のとき差分ロジックをスキップして全件処理・スキップ 0 件を返す
- [ ] `aidd_kos/cli.py` に `--full` フラグを追加
  → `result` に `full_count` キーを追加（全件数）

### 検証

- [ ] 全テスト GREEN + lint PASS
- [ ] `git grep "AC-F31"` で全 AC-ID がテストに存在する
