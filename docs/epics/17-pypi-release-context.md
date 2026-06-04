<!-- このファイルは Epic #17 承認時点のスナップショットです。現在の仕様は docs/spec/ を参照してください。 -->

# PyPI 公開・リリースパイプライン整備

Issue: #17
Milestone: Core MVP（#1）
作成日: 2026-06-04

## 背景・課題

`uvx aidd-kos install` / `uvx aidd-kos@latest serve` がどのユーザー環境でも動くためには
PyPI 公開が必要だが、現状 PyPI に未登録のため git URL 指定が必要。
Charter §6 の「GitHub Release 経由（PyPI は将来対応）」の「将来」を本 Epic で実現する。
本 Epic のスコープに Charter §6 の更新（「Phase 1 Core MVP で対応済み」への改定）を含む。

## Value Proposition

GitHub Release 作成をトリガーに PyPI へ自動公開するパイプラインを整備することで、
`uvx aidd-kos install` がどのユーザー環境でも動作する状態を作る。

## ユーザー（ペルソナ）

Primary: AI 駆動開発エンジニア（オペレーター）— docs/PROJECT-CHARTER.md §ペルソナ 参照
Secondary: aidd-kos メンテナー（スパイクスタジオ開発者）— aidd-kos を開発・リリースする担当者
※ aidd-kos メンテナーは Charter §3 未定義のプロジェクト固有役割。Charter 更新候補。

## 成功指標

1. `uvx aidd-kos install` を実行すると PyPI からインストールが完了し `aidd-kos --version` が動作すること
2. `v*` タグ付き GitHub Release 作成後、GitHub Actions が自動で PyPI へ publish すること
3. `RELEASE.md` が存在し、バージョン更新・タグ作成・GitHub Release 作成の 3 セクションが含まれること

## スコープ外

- aidd-fw リポジトリ側のスキル追加（別プロジェクトのスコープ）
- conda / Homebrew 等他パッケージマネージャー対応
- Web UI / SaaS 化
- CHANGELOG の自動生成（手動管理）

## この Epic で追加・変更した仕様

> AC ID は Feature Issue 作成後（Step 6）に確定番号へ置換される。

| Feature | Spec |
|---------|------|
| F-01: `uvx aidd-kos` が PyPI から動作する（#TBD） | docs/spec/distribution.md |
| F-02: GitHub Release から PyPI へ自動公開されるパイプライン（#TBD） | docs/spec/distribution.md |
| F-03: リリース手順が標準化・ドキュメント化される（#TBD） | docs/spec/distribution.md |

## 関連ドキュメント

- Business Context: docs/business-context/distribution.md
- Epic Issue: #17
