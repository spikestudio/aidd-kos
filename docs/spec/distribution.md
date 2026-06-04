# Spec: PyPI 公開・リリースパイプライン整備

Epic: #17 PyPI 公開・リリースパイプライン整備
Milestone: Core MVP（#1）

> AC ID の [N]/[M]/[L] は Feature Issue 作成後に実際の Issue 番号に置換する。

---

## Feature: `uvx aidd-kos` が PyPI から動作する (F01)

### Story S-01: `uvx aidd-kos install` でセットアップできること

As an AI 駆動開発エンジニア（オペレーター）, I want to install aidd-kos by running `uvx aidd-kos install`,
so that I can set up aidd-kos without specifying a git URL.

根拠: [Problem Statement]

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F19-01 | aidd-kos が PyPI に公開されている | オペレーターが `uvx aidd-kos install` を実行したとき | インストールが完了し `aidd-kos --version` が exit code 0 で動作すること |

---

### Story S-02: `uvx aidd-kos@latest serve` で最新版 MCP サーバーを起動できること

As an AI 駆動開発エンジニア（オペレーター）, I want to start the latest MCP server with `uvx aidd-kos@latest serve`,
so that I can keep using the latest features without reinstalling or changing MCP settings.

根拠: [Problem Statement]

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F19-02 | aidd-kos の最新バージョンが PyPI に公開されている | オペレーターが `uvx aidd-kos@latest serve` を実行したとき | MCP サーバーが起動し stdio 経由の `initialize` リクエストに対してレスポンスが返ること |

---

## Feature: GitHub Release から PyPI へ自動公開されるパイプライン (F02)

### Story S-03: GitHub Release 作成だけで PyPI へ自動公開されること

As an aidd-kos メンテナー, I want PyPI publication to be triggered automatically when I create a GitHub Release,
so that I can release reliably without manually running publish commands.

根拠: [ユーザー入力]

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F20-01 | `v*` パターンのタグが付いた GitHub Release が作成された | リリースが公開された直後 | GitHub Actions の publish ワークフローが自動起動すること |
| AC-F20-02 | publish ワークフローが正常完了した | `pip index versions aidd-kos` を実行したとき | 新バージョンが PyPI のバージョン一覧に含まれること |

---

### Story S-04: PyPI 公開失敗時に GitHub で検知できること

As an aidd-kos メンテナー, I want to be notified on GitHub when PyPI publication fails,
so that I can detect the failure quickly and take recovery action.

根拠: [AI 補完: エラーケース]

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F20-03 | PyPI への公開処理が失敗した | publish ワークフローが失敗したとき | GitHub Actions のワークフロー実行ステータスが "failure" となること |

---

## Feature: リリース手順が標準化・ドキュメント化される (F03)

### Story S-05: リリース手順ドキュメントに従って新バージョンをリリースできること

As an aidd-kos メンテナー, I want to follow a documented release process to create a new version,
so that I can release consistently without forgetting or making mistakes.

根拠: [ユーザー入力]

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F21-01 | リリース手順ドキュメントが `RELEASE.md` として存在する | メンテナーがファイルを参照したとき | バージョン番号の更新・タグ作成・GitHub Release 作成の 3 セクションがそれぞれ含まれていること |
