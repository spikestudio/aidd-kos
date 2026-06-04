# E2E テスト仕様: F-02 GitHub Release から PyPI へ自動公開されるパイプライン

Feature Issue: #20
Epic: #17

> 注: AC-F20-01/02/03 の本番確認は GitHub Actions 実行後にのみ可能（LOCAL-FIRST 例外）。
> ローカルではワークフローファイルの存在・構造正確性をユニットテストで確認する。

| AC ID | シナリオ | 前提データ | 操作手順 | 確認内容 |
|-------|---------|-----------|---------|---------|
| AC-F20-01（ローカル代替）| publish ワークフローが存在し on.release トリガーを持つ | publish.yml が存在する | ワークフローファイルを読み込む | `on.release.types` に `published` が含まれること |
| AC-F20-01（ローカル代替）| ワークフローが v* タグ付き Release のみを対象とする | publish.yml が存在する | ワークフローファイルを読み込む | `if: startsWith(github.ref, 'refs/tags/v')` またはタグフィルタが存在すること |
| AC-F20-02（ローカル代替）| ワークフローが uv build と PyPI publish ステップを持つ | publish.yml が存在する | ワークフローファイルを読み込む | `uv build` ステップと `pypa/gh-action-pypi-publish` ステップが含まれること |
| AC-F20-03（ローカル代替）| ワークフローが失敗時に failure ステータスになる | GitHub Actions の標準動作 | ワークフロー失敗時 | GitHub Actions 標準の失敗ステータス伝播（明示的設定不要）|
