# Business Context: Status Visibility（ステータス & エラー可視化）

Epic: #27
対象 Phase: Operational Excellence（#2）
作成日: 2026-06-09

> **既存状態値からの変更について**
>
> Epic #25 以前の `aidd-kos status` / `kos_status` は `ready / unavailable / indexing` の 3 値を返していた。
> 本 Epic では `unavailable` を `Error` に改名・具体化し、`ready` を `Ready / Stale` に細分化する。
> 承認後に以下のドキュメントを同一 PR 内で更新する:
>
> - `docs/glossary.md` § kos_status（状態値の記述を更新）
> - `docs/business-context/mcp-aggregator.md` § エンジン状態（状態値を新 4 値に更新）

---

## 業務目的

`aidd-kos status`（既存 CLI コマンドの拡張）と `kos_status` MCP ツールの 1 回呼び出しで、
ナレッジインデックスの正確な状態・エラーの原因と解消方法・インデックス中の進捗を把握できる状態にする。
AI Agent はインデックスの鮮度を自律的に判断し、
オペレーターはトラブル時に追加操作なしで原因と対処を特定できる。

---

## 登場人物

| 役割 | 説明 |
|------|------|
| AI Agent（Claude Code / Cursor 等）| ステータス確認機能でインデックスの鮮度を検知し、Stale・Error な場合に自律的にオペレーターへ再同期を促す判断を行う |
| AI 駆動開発エンジニア（オペレーター）| `aidd-kos status` でインデックス状態を確認し、Error 時は表示された再試行コマンドを実行してトラブルシューティングを行う |

---

## ドメイン概念

| 用語 | 定義 | 備考 |
|------|------|------|
| インデックス状態 | ナレッジインデックスの現在の鮮度・稼働状況を 4 値（Ready / Stale / Indexing / Error）で表した分類 | `aidd-kos status` および `kos_status` MCP ツールが返す |
| Ready（最新）| インデックス済みで、最終インデックス実行後に `mtime > indexed_at` のファイルが 0 件の状態 | AI Agent がナレッジ検索を実行できる最良の状態 |
| Stale（古い）| インデックス済みだが、最終インデックス実行後にプロジェクト配下の `.md`/`.txt` ファイルが 1 件以上変更された状態 | `aidd-kos index` の実行で Ready に戻る |
| Indexing（処理中）| LightRAG が現在インデックス処理を実行中の状態 | 処理済み件数・総件数とともに表示される |
| Error（エラー）| LightRAG サーバーに接続できない状態（旧: unavailable を改名・拡張）| エラーコードと再試行コマンドが表示される |
| エラーコード | Error 状態の具体的な原因を識別する文字列（例: `LIGHTRAG_UNAVAILABLE`）| ターミナルに表示されオペレーターが対処方法を特定するために使用する |
| 再試行コマンド | エラー解消のために実行すべき具体的な CLI コマンド | エラーコードとともに表示される（例: `aidd-kos serve`）|
| インデックス進捗 | Indexing 状態のとき表示される「処理済み件数 / 総件数」の情報 | 完了見込みの目安としてオペレーターが参照する |

---

## インデックス状態遷移

| 現在の状態 | 遷移先 | トリガー |
|-----------|--------|---------|
| 未インデックス（初回）| Indexing | `aidd-kos index` を初回実行する |
| Indexing | Ready | LightRAG のインデックス処理が完了する |
| Ready | Stale | プロジェクト配下の `.md`/`.txt` ファイルが変更・追加・削除される |
| Stale | Indexing | `aidd-kos index` を実行する |
| Ready | Indexing | `aidd-kos index` を実行する（変更なしでも実行可能）|
| Error | Ready | エラー解消後に `aidd-kos serve` を実行し再接続する |

---

## ビジネスルール

| ID | ルール |
|----|--------|
| BR-STATUS-01 | `mtime > indexed_at` のファイルが 1 件以上存在する場合は Stale と判定する（猶予なし）|
| BR-STATUS-02 | LightRAG サーバーに接続できない場合は Error と判定し、エラーコードと再試行コマンドを表示する。exit code 0 で正常終了する（サーバー未起動はツール自体の失敗ではない）|
| BR-STATUS-03 | Indexing 状態の場合は処理済み件数と総件数を表示する |
| BR-STATUS-04 | インデックス処理が完了した後は Ready として表示する（Indexing 表示は消える）|
| BR-STATUS-05 | `aidd-kos status` CLI は Ready / Stale / Indexing / Error いずれの状態でも exit code 0 で正常終了する（状態の報告はツールの正常動作）|

---

## 業務イベント

| イベント名 | 発生条件 | 後続アクション |
|----------|---------|-------------|
| インデックス鮮度確認 | オペレーターまたは AI Agent がステータス確認を実行したとき | 現在の状態が Ready / Stale / Indexing / Error のいずれかとして返される |
| エラー診断表示 | ステータス確認時に Error 状態と判定されたとき | エラーコードと再試行コマンドがターミナルに表示される |

---

## 未解決事項

なし

---

## ユビキタス言語

| 用語 | 定義 |
|------|------|
| インデックス状態 | ナレッジインデックスの現在の鮮度・稼働状況を Ready / Stale / Indexing / Error の 4 値で表した分類 |
| Stale（古い）| 最終インデックス実行後にファイルが変更された状態。`aidd-kos index` で解消する |
| エラーコード | Error 状態の原因を識別する文字列 |
| 再試行コマンド | エラー解消のために実行すべき CLI コマンド |
| インデックス進捗 | Indexing 状態のとき表示される処理済み件数・総件数 |
