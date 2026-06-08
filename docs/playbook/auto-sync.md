# コミット後の自動インデックス更新

`lefthook.yml` に以下を追加し `lefthook install` で有効化する:

```yaml
post-commit:
  commands:
    aidd-kos-index:
      run: aidd-kos index || true
```

## 前提条件

- lefthook がインストール済みであること（[lefthook](https://github.com/evilmartians/lefthook) 参照）
- `aidd-kos` コマンドが利用可能であること（`uvx aidd-kos install` 実行済み）

## 設定手順

### 1. lefthook.yml に post-commit フックを追加する

プロジェクトルートの `lefthook.yml`（なければ新規作成）に上記の `post-commit:` ブロックを追加する。

既に `post-commit:` セクションが存在する場合は、`commands:` 以下に `aidd-kos-index:` ブロックのみ追記する。

### 2. フックを有効化する

```bash
lefthook install
```

以降の git commit のたびに `aidd-kos index`（差分インデックス）が自動実行される。

## `|| true` について

`aidd-kos index || true` の `|| true` は、コマンドが非ゼロで終了したとき exit code を強制的に 0 にするシェル制御である。

`post-commit` フックはコミット完了後に実行されるため、フックの成否はコミット自体に影響しない。しかし lefthook は
フックコマンドが非ゼロで終了するとターミナルにエラーを表示する。`|| true` を付けることで aidd-kos がエラーを
返しても（LightRAG 未起動・ネットワーク障害等）exit code が 0 となり、lefthook がコミット操作をブロックしない。

## 動作確認

フック設定後、以下で手動実行して動作を確認できる:

```bash
lefthook run post-commit
```
