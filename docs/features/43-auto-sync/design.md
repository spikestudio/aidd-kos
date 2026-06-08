# コミット後の自動インデックス設定手順の提供 Design

Feature Issue: #43
Epic: #26

## Spec

docs/spec/auto-sync.md → Feature: コミット後の自動インデックス設定手順の提供 (#43)

## Related Docs（このFeatureが追記・生成するファイル）

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| Playbook | docs/playbook/auto-sync.md | 自動インデックス設定手順（新規作成）|

## 観測ポイント

該当なし（docs-only Feature）

## Implementation Tasks

### Spec 追記

該当なし（docs-only。openapi / schema / screens / e2e は不要）

### ドキュメント実装

- [x] docs/playbook/auto-sync.md 作成
  → 完了条件:
  - AC-F43-01: 以下の YAML 構造を含む post-commit 設定ブロックが記載されていること

    ```yaml
    post-commit:
      commands:
        aidd-kos-index:
          run: aidd-kos index || true
    ```

  - AC-F43-02: `lefthook install` コマンドがセットアップ手順として記載されていること
  - AC-F43-03: `|| true` の技術的意味（コマンドが非ゼロで終了しても exit code 0 を返すため
    lefthook がコミットをブロックしない）が本文中に明示されていること
  - 前提条件として lefthook がインストール済みであることが記載されていること（SHOULD FIX-3）
  - aidd-kos コマンドが利用可能であること（`uvx aidd-kos install` 等）への参照が含まれること（SHOULD FIX-4）

### 検証

- [x] AC カバレッジ確認
  → 完了条件: AC-F43-01/02/03 が全件充足（ファイル内容で目視確認）

## Tier 判定

Tier 0（docs/** のみ変更）→ ビルド/起動/実働確認スキップ
