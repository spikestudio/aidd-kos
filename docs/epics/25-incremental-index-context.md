# インデックス差分更新

> このファイルは Epic #25 承認時点のスナップショットです。
> 現在の仕様は docs/spec/index-sync.md を参照してください。

Issue: #25
Milestone: Operational Excellence（#2）
作成日: 2026-06-04

## 背景・課題

`aidd-kos index` は毎回全 `.md`/`.txt` ファイルを LightRAG に送信する。
1 ファイルの変更でも全件分の OpenAI API（Embedding + LLM）が呼び出されるため、
コストが高く、インデックス反映に躊躇が生まれる。
結果として AI Agent が参照するインデックスが古いまま放置されやすい。

## Value Proposition

変更・追加ファイルのみを検出して再処理することで、
1 ファイルの変更なら数秒・数円以下でインデックスを最新化できる状態にする。
変更がないときは API 呼び出しゼロで完了し、人間が `index` を気軽に実行できる。
AI Agent は常に最新のインデックスを参照して回答精度を維持できる。
Epic #26（自動同期トリガー）の基盤でもある。

## ユーザー（ペルソナ）

Primary: AI 駆動開発エンジニア（オペレーター）— docs/PROJECT-CHARTER.md §ペルソナ 参照
Secondary: AI Agent（Claude Code 等）— 最新インデックスを検索に利用する受益者

## 成功指標

- 変更ファイルが 1 件のとき、LightRAG への insert/update 呼び出しが 1 回だけ発生する
  （統合テストで LightRAG モックへの呼び出し回数を確認）
- 変更がないとき、`aidd-kos index` が LightRAG API 呼び出しゼロで exit code 0 で完了する
  （ユニットテストで確認）
- `aidd-kos index --full` で全件処理が引き続き実行できる
  （E2E テストで確認）

## スコープ外

- CodeGraph の差分インデックス（既に差分対応済み）
- F02（削除ファイルのインデックス除去）: LightRAG DELETE API の存在を
  `/aidd-epic-design` Step 0 で確認後に実装可否を確定する。
  DELETE API が存在しない場合は Won't Have として本 Epic スコープ外とし、
  別 Issue で代替実装（全件再構築による間接削除等）を検討する
- `.lightrag-ignore` 除外設定の変更（既存機能のまま）
- リアルタイムファイル監視（Epic #26 のスコープ）

## この Epic で追加・変更した仕様

| Feature | Spec |
|---------|------|
| F01: 変更・追加されたファイルだけが再インデックスされる | docs/spec/index-sync.md |
| F02: 削除したファイルがインデックスから取り除かれる | docs/spec/index-sync.md |
| F03: 全件再構築で確実にインデックスを最新化できる | docs/spec/index-sync.md |

## 関連ドキュメント

- Spec: docs/spec/index-sync.md
- Business Context: docs/business-context/index-sync.md
- Epic Issue: #25
- 依存 Epic（後続）: #26（自動同期トリガー）
