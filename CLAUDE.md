# CLAUDE.md
<!-- AI コーディングエージェント向け設定ファイル。概要・セットアップ等は README.md 参照 -->

<!-- aidd-fw:import-start -->
@aidd-framework/FRAMEWORK.md
<!-- aidd-fw:import-end -->

## プロジェクト概要

<!-- TODO: プロジェクト名・概要を 1〜2 文で記述してください -->

## プロジェクト固有の発見事項

<!-- AI が間違えたパターンを発見した都度、ここに追記する -->
<!-- 形式: - **[要点]**: [説明]（#Issue番号） -->
<!-- 汎用ルールは @aidd-framework/FRAMEWORK.md に記載済み。プロジェクト固有の発見事項のみここに追記する -->

<!-- uikit を使用する場合: 以下のコメントを解除すると AI がコンポーネント仕様を自動参照できる（/aidd-setup project で自動追記） -->
<!-- @node_modules/@spikestudio-jp/uikit/dist/llms.txt -->

<!-- codegraph を使用する場合: 以下のコメントを解除する（/aidd-setup-stack で codegraph セットアップ完了後に解除） -->
<!-- ## コード探索規則
コード探索は codegraph を使用する。grep / Read / Glob へのフォールバック禁止。

MANDATORY: 使用前に必ず `codegraph status --json` で状態を確認する。
- Ready（initialized==true かつ pendingChanges==0）→ codegraph を使用する
- Stale（initialized==true かつ pendingChanges>0）→ 作業を中断し `codegraph index` で修復してから再開する
- Uninitialized（initialized==false）→ 作業を中断し `/aidd-setup-stack` で初期化してから再開する

主要 MCP ツール:
- `codegraph_context`: タスク説明からコンテキストを構築
- `codegraph_explore`: シンボル周辺の依存関係を一括取得
- `codegraph_impact`: 変更影響半径を分析
- `codegraph_trace`: 2シンボル間の呼び出しパスを追跡
- `codegraph_callers` / `codegraph_callees`: 呼び出し元・呼び出し先の検出
-->

## ビルド・テストコマンド

```bash
# ビルド
# [コマンド]

# テスト
# [コマンド]

# リント
# [コマンド]
```
