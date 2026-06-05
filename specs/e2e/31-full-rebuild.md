# E2E テスト仕様: 全件再構築 (#31)

Feature: #31 全件再構築で確実にインデックスを最新化できる
Epic: #25 インデックス差分更新

## シナリオ一覧

| AC ID | インターフェース | 前提データ | 操作手順 | 確認内容 |
|-------|---------------|----------|---------|---------|
| AC-F31-01 | CLI | dir に .md/.txt ファイルが N 件（変更有無問わず）| `aidd-kos index --full <dir>` 実行 | stdout に「全件再構築モード: N 件」が含まれ exit code 0 |
| AC-F31-02 | CLI | LightRAG に一部 indexed 済みファイルが存在する状態 | `aidd-kos index --full <dir>` 実行 | 差分判定なしで全件が処理され「スキップ」という文字列が stdout に含まれないこと |

## モック戦略

- `POST /documents/texts` → 成功応答
- `POST /documents/paginated` は `--full` 時は呼ばれないことを確認
