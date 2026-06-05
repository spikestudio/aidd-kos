# E2E テスト仕様: 差分インデックス実行 (#29)

Feature: #29 変更・追加されたファイルだけが再インデックスされる
Epic: #25 インデックス差分更新
Spec: docs/spec/index-sync.md → Feature F01

## シナリオ一覧

| AC ID | インターフェース | 前提データ | 操作手順 | 確認内容 |
|-------|---------------|----------|---------|---------|
| AC-F29-01 | CLI | LightRAG に file_a.md が indexed 済み（updated_at = 過去 UTC）、file_a.md の mtime ≤ updated_at | `aidd-kos index <dir>` 実行 | stdout に「差分モード:」「スキップ: 1 件」が含まれ exit code 0 |
| AC-F29-02 | CLI | LightRAG に file_a.md が indexed 済み（updated_at = 過去 UTC）、file_a.md の mtime > updated_at | `aidd-kos index <dir>` 実行 | stdout に「更新: 1 件」が含まれ exit code 0 |
| AC-F29-03 | CLI | LightRAG に何も indexed されていない状態で file_new.md を追加 | `aidd-kos index <dir>` 実行 | stdout に「追加: 1 件」が含まれ exit code 0 |
| AC-F29-04 | CLI | LightRAG に何もなし（初回実行）、dir に .md ファイルが 3 件 | `aidd-kos index <dir>` 実行 | stdout に「追加: 3 件」が含まれ exit code 0 |
| AC-F29-05 | CLI | LightRAG に file_a.md indexed 済み、file_b.md は新規、file_c.md は変更済み | `aidd-kos index <dir>` 実行 | stdout に「差分モード:」「追加 1 件」「更新 1 件」「削除 0 件」「スキップ 1 件」が全て含まれ exit code 0 |

## モック戦略

- `POST /documents/paginated` → `unittest.mock.patch` で `urllib.request.urlopen` をモック
  - 返却値: `PaginatedDocsResponse` 相当の JSON
- `POST /documents/texts` → 同上
- ファイルの mtime 操作: `tmp_path` に実ファイルを作成し `os.utime()` で mtime を制御
