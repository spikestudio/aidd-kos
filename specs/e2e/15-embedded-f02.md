# E2E テスト仕様: F-02 全ナレッジエンジンが対象プロジェクトを正しく参照する

Feature Issue: #15
Epic: #3

| AC ID | シナリオ | 前提データ | 操作手順 | 確認内容 |
|-------|---------|-----------|---------|---------|
| AC-F15-01 | ナレッジ検索が対象プロジェクト A のドキュメントのみを返す | `.lightrag/` にインデックスがあり、LightRAG がプロジェクト A ドキュメントのみ返すようモック | `lightrag_query(query="test")` を呼び出す | 戻り値にプロジェクト B の識別子が含まれないこと |
| AC-F15-02 | インデックス未構築時に LIGHTRAG_INDEX_NOT_FOUND エラーを返す | `.lightrag/` が存在しないか空ディレクトリ | `lightrag_query(query="test")` を呼び出す | `LIGHTRAG_INDEX_NOT_FOUND` が含まれるレスポンスが返されること、および stderr に出力されること |
| AC-F15-03 | インデックスが対象プロジェクトルート直下の `.lightrag/` に保存される | `IndexOrchestrator` を LightRAG モック付きで実行 | `IndexOrchestrator(project_dir=tmp_path).run()` を実行する | `tmp_path/.lightrag/` が存在しないが、scan API が `input_dir=str(tmp_path)` で呼ばれること |
| AC-F15-04 | 再インデックス実行時に同じ `.lightrag/` が更新される | `.lightrag/` が存在する状態で `IndexOrchestrator` を実行 | `IndexOrchestrator(project_dir=tmp_path).run()` を 2 回実行する | 2 回とも同じ `input_dir=str(tmp_path)` で scan API が呼ばれること |
| AC-F15-05 | コード検索ツールの戻り値のファイルパスが対象プロジェクト配下のみ | codegraph が対象プロジェクト A のパスのみを返すようモック | `codegraph_explore` ツールを呼び出す（モック経由）| 戻り値のファイルパスがすべて対象プロジェクト A のディレクトリ配下であること |
