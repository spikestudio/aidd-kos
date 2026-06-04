# Spec: Index Sync

Epic: #25 インデックス差分更新
Milestone: Operational Excellence（#2）

---

## Feature: 変更・追加されたファイルだけが再インデックスされる (F01)

### Story S1: 変更・追加ファイルだけをインデックスに反映させたい

As an AI 駆動開発エンジニア（オペレーター）,
I want to re-index only changed or newly added files when running the index command,
So that 変更ファイル数 / 総ファイル数 の比率分だけ API 呼び出し回数と処理時間が短縮され、変更がないときはゼロコストで完了できる。

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F29-01 | インデックスを 1 回以上実行済みで、ファイルを何も変更していない | `aidd-kos index` を実行する | 「差分モード: 追加 0 件・更新 0 件・削除 0 件・スキップ N 件」が stdout に表示され exit code 0 で終了すること |
| AC-F29-02 | インデックスを 1 回以上実行済みで、既存ファイルを 1 件編集した | `aidd-kos index` を実行する | 「更新: 1 件」として処理され、「スキップ: N-1 件（N = インデックス済みファイル総数）」が表示されること |
| AC-F29-03 | インデックスを 1 回以上実行済みで、新規ファイルを 1 件追加した | `aidd-kos index` を実行する | 「追加: 1 件」として処理され、「スキップ: N 件（N = 既存インデックス済みファイル数）」が表示されること |
| AC-F29-04 | インデックスを一度も実行していない（初回実行）| `aidd-kos index` を実行する | 指定ディレクトリ配下の `.md`・`.txt` ファイル全件が処理され「追加: N 件（N = 対象ファイルの実数）」が stdout に表示されること |
| AC-F29-05 | インデックスを 1 回以上実行済みで、ファイルを 1 件編集している | `aidd-kos index`（`--full` なし）を実行する | 「差分モード: 追加 N 件・更新 M 件・削除 K 件・スキップ L 件」が stdout に表示されること |

> AC ID の `[TBD]` は Feature Issue 作成後に実際の Issue 番号へ置換する。

---

## Feature: 削除したファイルがインデックスから取り除かれる (F02)

> ⚠️ LightRAG DELETE API の有無を `/aidd-epic-design` Step 0 で確認後に実装可否を確定する。
> DELETE API が存在しない場合は Won't Have として Epic スコープ外とする。

### Story S2: 削除したファイルをナレッジインデックスからも自動的に除去したい

As an AI 駆動開発エンジニア（オペレーター）,
I want deleted files to be automatically removed from the knowledge index,
So that 古い情報が AI Agent に返却されず、検索結果の鮮度を保てる。

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F30-01 | インデックス済みファイル「sample.md」をプロジェクトから削除した | `aidd-kos index` を実行する | 「削除: 1 件」が stdout に表示されること |
| AC-F30-02 | AC-F30-01 の実行完了後 | `lightrag_query` で「sample.md」固有のテキストを含むクエリを実行する | レスポンスの `file_sources` フィールドに `sample.md` が含まれないこと |

---

## Feature: 全件再構築で確実にインデックスを最新化できる (F03)

### Story S3: インデックスが壊れたとき・疑わしいとき、全件を強制的に再構築したい

As an AI 駆動開発エンジニア（オペレーター）,
I want to force a full rebuild of all documents when the index seems broken or unreliable,
So that クリーンな状態に戻してから作業を再開できる。

**AC:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-F31-01 | ファイルが変更されているかどうかに関わらず | `aidd-kos index --full` を実行する | 指定ディレクトリ配下の `.md`・`.txt` ファイル全件が処理対象となり「全件再構築モード: N 件」が stdout に表示されること |
| AC-F31-02 | インデックスを 1 回以上実行済みで、一部ファイルのみ変更されている | `aidd-kos index --full` を実行する | 変更の有無にかかわらず全件が処理され、スキップが 0 件であること |
