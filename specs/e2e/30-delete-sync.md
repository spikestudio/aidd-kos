# E2E テスト仕様: 削除ファイルのインデックス除去 (#30)

Feature: #30 削除したファイルがインデックスから取り除かれる
Epic: #25 インデックス差分更新
Spec: docs/spec/index-sync.md → Feature F02

## シナリオ一覧

| AC ID | インターフェース | 前提データ | 操作手順 | 確認内容 |
|-------|---------------|----------|---------|---------|
| AC-F30-01 | CLI | LightRAG に「sample.md」が indexed 済み（doc_id = "doc_sample"）、filesystem に sample.md は存在しない | `aidd-kos index <dir>` 実行 | stdout に「削除: 1 件」が含まれ、`DELETE /documents/delete_document` が doc_ids=["doc_sample"] で呼ばれる。exit code 0 |
| AC-F30-02 | CLI | LightRAG に「sample.md」（doc_id = "doc_sample"）が indexed 済み、filesystem に sample.md は存在しない | `aidd-kos index <dir>` 実行 | `DELETE /documents/delete_document` が `doc_ids=["doc_sample"]` で呼び出されること。exit code 0 |

## モック戦略

- `POST /documents/paginated` → indexed docs に sample.md を含む応答を返す
- `DELETE /documents/delete_document` → 成功応答 + 呼び出し引数を記録
- `POST /documents/texts` → 追加・更新ファイルがあれば使われる（本 Feature では不使用）
- URL ディスパッチ: `req.full_url` で `paginated` / `delete_document` / `texts` を振り分ける
