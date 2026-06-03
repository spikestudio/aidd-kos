# E2E テスト仕様: F-01 install コマンド

Feature Issue: #8
Epic: #4

| AC ID | シナリオ | 前提データ | 操作手順 | 確認内容 |
|-------|---------|-----------|---------|---------|
| AC-F01-01 | install 全自動実行 | 空の temp プロジェクト、OPENAI_API_KEY 設定済み、mise インストール済み | `aidd-kos install --project-dir <tmpdir>` を実行 | .lightrag/・.codegraph/ が作成される、~/.claude/settings.json に aidd-kos エントリが追加される、.gitignore が更新される |
| AC-F01-02 | 完了メッセージ表示 | 同上 | `aidd-kos install` を実行 | stdout に「✅ セットアップ完了。Claude Code を再起動してください」が含まれること |
| AC-F01-03 | MCP エントリ追加 | ~/.claude/settings.json が空または既存エントリあり | `aidd-kos install` を実行 | ~/.claude/settings.json の mcpServers.aidd-kos キーが存在すること |
| AC-F01-04 | ストレージ作成 | 空のプロジェクト | `aidd-kos install` を実行 | `.lightrag/` ディレクトリが存在すること、`.codegraph/` ディレクトリが存在すること |
| AC-F01-05 | MISE_NOT_FOUND エラー | mise が PATH に存在しない環境 | `aidd-kos install` を実行 | stderr に `MISE_NOT_FOUND` が含まれること、3 秒以内に出力されること、exit code が 1 であること |
| AC-F01-06 | OPENAI_API_KEY_MISSING エラー | OPENAI_API_KEY 未設定・.env なし | `aidd-kos install` を実行 | stderr に `OPENAI_API_KEY_MISSING` が含まれること、3 秒以内に出力されること、exit code が 1 であること |
| AC-F01-07 | .gitignore に .lightrag/ 追記 | .gitignore が存在しない | `aidd-kos install` を実行 | .gitignore に `.lightrag/` が存在すること |
| AC-F01-08 | .gitignore に .codegraph/ 追記 | .gitignore が存在しない | `aidd-kos install` を実行 | .gitignore に `.codegraph/` が存在すること |
| AC-F01-09 | .gitignore 重複追記なし | .gitignore に `.lightrag/` が既に記載済み | `aidd-kos install` を 2 回実行 | .gitignore 内の `.lightrag/` の出現回数が 1 であること |
| AC-F01-10 | 再 install 時 .lightrag/ 保持 | .lightrag/ にダミーファイル `test.txt` を配置済み | `aidd-kos install` を再実行 | `.lightrag/test.txt` が削除されていないこと |
| AC-F01-11 | 再 install 時インデックス読み取り可能 | .lightrag/ が存在し lightrag_list が返却実績あり | `aidd-kos install` を再実行 | `.lightrag/` 配下のファイルが読み取り可能（os.access で確認）であること |
| AC-F01-12 | 他 MCP エントリ保護 | ~/.claude/settings.json に `other-tool` エントリが存在 | `aidd-kos install` を実行 | mcpServers.other-tool エントリが変更されていないこと |
