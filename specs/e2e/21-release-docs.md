# E2E テスト仕様: F-03 リリース手順が標準化・ドキュメント化される

Feature Issue: #21
Epic: #17

| AC ID | シナリオ | 前提データ | 操作手順 | 確認内容 |
|-------|---------|-----------|---------|---------|
| AC-F21-01 | RELEASE.md が存在する | RELEASE.md がリポジトリルートに作成済み | ls RELEASE.md を実行する | ファイルが存在すること（exit 0）|
| AC-F21-01 | RELEASE.md にバージョン番号更新セクションが含まれる | RELEASE.md が存在する | RELEASE.md を参照する | バージョン番号の更新手順を示すセクションが含まれること |
| AC-F21-01 | RELEASE.md にタグ作成セクションが含まれる | RELEASE.md が存在する | RELEASE.md を参照する | タグ作成の手順を示すセクションが含まれること |
| AC-F21-01 | RELEASE.md に GitHub Release 作成セクションが含まれる | RELEASE.md が存在する | RELEASE.md を参照する | GitHub Release 作成の手順を示すセクションが含まれること |
