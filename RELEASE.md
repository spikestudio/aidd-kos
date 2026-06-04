# aidd-kos リリース手順

このドキュメントは aidd-kos メンテナー向けのリリース作業手順書です。

---

## 1. バージョン番号の更新

`pyproject.toml` の `version` フィールドを新しいバージョン番号に変更します。

```bash
# 例: 0.1.0 → 0.2.0
# pyproject.toml の version = "0.1.0" を version = "0.2.0" に変更する
```

変更後、コミットします。

```bash
git add pyproject.toml
git commit -m "chore: bump version to v0.2.0"
git push origin main
```

---

## 2. タグの作成

バージョンコミットに対して `v` プレフィックス付きのタグを作成し、リモートに push します。

```bash
git tag v0.2.0
git push origin v0.2.0
```

> タグ名は必ず `v` で始める（例: `v0.2.0`）。
> これが GitHub Release のトリガーとなり、PyPI への自動公開が実行されます。

---

## 3. GitHub Release の作成

GitHub CLI を使って GitHub Release を作成します。

```bash
gh release create v0.2.0 \
  --title "v0.2.0" \
  --notes "## 変更点

- 主な変更点をここに記述する

## インストール

\`\`\`bash
uvx aidd-kos@0.2.0 install
\`\`\`"
```

Release が公開されると `.github/workflows/publish.yml` が自動起動し、
PyPI への publish が実行されます。

### PyPI 公開確認

数分後に以下で確認できます。

```bash
pip index versions aidd-kos
```

---

## 注意事項

- PyPI OIDC Trusted Publisher の設定が完了していること（初回のみ）
- main ブランチへのコミット後にタグを作成すること
- `v*` パターン以外のタグでは publish ワークフローが起動しません
