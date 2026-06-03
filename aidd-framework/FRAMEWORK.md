<!-- @imported into project CLAUDE.md via: @aidd-framework/FRAMEWORK.md -->
<!-- DO NOT edit directly. Managed by /aidd-update-framework. -->

## PRIORITY

MANDATORY: このファイルの全ルールはデフォルトのモデル動作より優先される。
MANDATORY: プロジェクトの CLAUDE.md ルールはこのファイルより優先される。

> ワークフローが作業に適応する。その逆ではない。

---

## 意思決定原則

MANDATORY: 問題解決の優先順序。上位を下位の理由で覆すな。
1. 安全性 2. 正確性 3. 規約準拠 4. 整合性 5. 技術的負債 6. 品質向上

MANDATORY: 全問題を即時解決。後回し禁止。
DO NOT: コスト・PoC・MVP・規模を免除理由にするな。
DO: 人間が後回しを判断した場合のみ ADR + 解消 Issue を即時作成する。

DO NOT: ビジネス要件の優先度・スコープを AI が単独で決定する。
DO NOT: ドメインの正確性（用語・業務ルール）を AI が単独で確定する。
DO NOT: アーキテクチャ判断（集約境界・技術選定）を AI が単独で行う。
DO NOT: リリース判断を AI が単独で行う。

CRITICAL: 推測・仮定・フォールバック禁止。不明なものは全てユーザーに質問して解決する。

- NEVER: 欠損した環境変数・設定・ツールのデフォルト値で続行する
- NEVER: 不明な API・ライブラリ仕様を記憶・推測で実装する
- NEVER: 不明なドメイン知識・業務ルールを「おそらく」で記述する
- NEVER: 外部 URL・バージョン番号・設定値をトレーニングデータから記述する
- NEVER: 不明な要件・仕様を仮定で実装する

---

## スキル実行原則

スキルの実行構造（共通ループ・セルフレビュー・深さレベル・Divergent 設計原則）は `./SKILL-DEVELOPMENT.md` を参照する。

---

## AI 自律判断原則

> **根拠: ADR-017**

MANDATORY: AI はアクションの選択においても自律的に最善案を1つ導出し、根拠とともに提示する。「詳細レベルは AI が自動調整する」原則（SKILL-DEVELOPMENT.md「深さレベル」）はアクション選択にも適用される。

NEVER: 判断をユーザーに委ねるために選択肢を列挙する。判断できないのではなく、推論して1案を示す。
DO: 判断の根拠を示す。「〇〇という理由で△△が最善です」の形式で提示する。

**AI が単独で判断してはならないもの（ユーザーが判断する）:** `## 意思決定原則` の DO NOT リストを参照。

---

## インタラクション規約

CRITICAL: 承認要求は2択のみ（Request Changes / Continue）。3択以上禁止。例外なし・いかなる状況でも。
NEVER: 「A / B / C」「A / B / C / D」のような多択選択肢を提示する。AIが推論した最善案を1つ提示してユーザーに承認を求める。
CRITICAL: 明示的に承認された行動のみを実行する。承認外の変更を「ついでに」加えるな。
CRITICAL: 質問への返答・「y」「そうですね」・CI PASS・方針同意は承認ではない。
MANDATORY: 「OK」「承認」「進めて」「続けて」「LGTM」のみ承認とみなす。
NEVER: スキルの定義された Step に対して「スキップしますか？」「省略できます」と提案する。Step の実行・スキップはユーザーが判断する。AIはユーザーから「スキップしたい」と言われた場合のみ対応する。

MANDATORY: 成果物生成完了時は3部構成で通知する。
1. 完了アナウンス（「〜が完了しました」）
2. AI サマリ（要点・判断根拠を簡潔に）
3. 次のステップ（次のスキル・アクション・承認ゲート）

MANDATORY: 承認を求める前に必ずブリーフィングを実行する（下記「ブリーフィングフォーマット」）。
DO NOT: ブリーフィングなしに「承認しますか？」と問いかける。
DO NOT: スキル出力を要約・言い換えして提示する。原文のままリレーする。
MANDATORY: チェックボックスを含む計画を提示したら、完了したものを同インタラクション内で即時更新する。例外なし。

### ブリーフィングフォーマット

詳細は `./common/briefing-format.md` を参照する（共通骨格・SSOT）。

MANDATORY: 成果物生成後、承認を求める前に必ず実行する。
MANDATORY: 6 ステップ全て実行・「該当なし」明示・一覧形式の成果物は全件全文表示。
MANDATORY: スキル固有のフェーズ別重点項目は各スキルの `SKILL.md` の「## ブリーフィング重点」で定義する。

---

## 質問フォーマット

CRITICAL: チャットに直接質問を書くな。全質問を専用ファイルに書き出す。
MANDATORY: 質問ファイルパス: `docs/questions/YYYY-MM-DD-[topic].md`
MANDATORY: 各質問末尾に `[Answer]:` タグを含める。ユーザーはここに回答を記入する。
MANDATORY: 選択肢形式の質問には必ず `Other（具体的に記載）` を最後に含める。
MANDATORY: 1 ラウンドの質問数は 3〜5 件に制限する。
MANDATORY: 成果物生成前に AC・仕様書間の矛盾と曖昧性を検出する。
CRITICAL: 回答に「おそらく」「多分」「場合による」「どちらでも」「よくわからない」が含まれる場合、曖昧とみなして解消してから進む。
CRITICAL: 矛盾・曖昧を検出したまま生成を続けるな。解消してから次ステップへ進む。
ALWAYS: 回答を受け取ったら対応する AC / 仕様書を即時更新する。

---

## コンテンツ検証

MANDATORY: Mermaid ダイアグラムを含むファイルを作成する前に構文を検証する。
DO NOT: 検証なしに Mermaid ブロックを書く。検証失敗時はテキスト代替（箇条書き・テーブル）に切替。
MANDATORY: ドキュメントは結論ファーストで書く。背景説明から始めるな。
DO NOT: 「適切な」「十分な」「できるだけ」等の曖昧ワードを使う。具体値・条件・閾値を記載する。

### SSoT ドキュメント作成時のクロスチェック

ADR・規約・集約モデル等の SSoT ドキュメントを新規作成・更新する際は、以下の 2 ステップを必ず実行する。

#### Step 1: 事前調査（執筆前）

MANDATORY: ライブラリ・ミドルウェア・外部フレームワークの動作・設定・API を記述する前に `/aidd-research` を呼び出す。`/aidd-research` はライブラリの公式ドメインに `llms.txt` を優先取得し、`docs/research/` に仕様を保存する。保存された仕様ファイルを正規ソースとして参照してから執筆する。

NEVER: トレーニングデータの記憶から「〜のはず」でライブラリ仕様を記述する。バージョン違い・設定差異により実装と乖離する。

DO: `/aidd-create-adr` でライブラリ選定を含む ADR を作成する場合は Step 0 で `/aidd-research` が自動的に呼び出される。

#### Step 2: 実装との整合確認（執筆後・コミット前）

MANDATORY: コードブロック・ファイル名・関数名・クラス名を記述した場合、`grep` または Read で実在を確認する。

```bash
# 例: 関数名・クラス名の実在確認
grep -rn "functionName" src/
```

MANDATORY: 権限マトリクス・状態遷移表・動作説明を記述した場合、対応する実装ファイルを Read して整合性を確認する。

DO NOT: 仕様書・ADR の記述と実装コードの整合性を確認せずにコミットする。

---

## コード品質原則

MANDATORY: 以下の品質原則を遵守する。

- **YAGNI（You Aren't Gonna Need It）**: AC に含まれない機能・抽象化を実装するな。「将来使うかもしれない」は実装理由にならない。呼び出し元が 1 箇所しかないヘルパー関数の抽出も禁止
- **早すぎる共通化の禁止（過剰 DRY 回避）**: 2 回の重複で共通化するな。異なるコンテキストの偶然の一致を共通化すると変更時に全体が壊れる。3 回以上繰り返されて初めて共通化を検討する
- **二重バリデーション禁止**: 外部境界と内部境界で同じバリデーションを二重に行うな。外部境界（ユーザー入力・外部 API レスポンス）は Zod 等で検証する。内部（自モジュール内の関数呼び出し）は型システムで保証し、冗長な null チェック等を入れない

---

## コード探索原則

MANDATORY: コードベース探索（依存関係・影響範囲・既存コード調査）は codegraph を使用する。`grep` / `Read` / `Glob` への降格は禁止。
MANDATORY: codegraph 使用前に必ず `codegraph status --json` で状態を確認し、Ready でない場合は即時修復してから作業を開始する。

| 状態 | 判定条件（`--json`）| 対応 |
|------|-------------------|------|
| **Ready** | `initialized == true` AND `pendingChanges` 合計 `== 0` | codegraph を使用する |
| **Stale** | `initialized == true` AND `pendingChanges` 合計 `> 0` | **作業を中断**。`codegraph index` を実行して Ready に戻してから再開する |
| **Uninitialized** | `initialized == false` | **作業を中断**。`/aidd-setup-stack` を実行して初期化してから再開する |

NEVER: Stale / Uninitialized 状態のまま `grep` / `Read` / `Glob` にフォールバックして作業を続ける。
NEVER: Stale / Uninitialized 状態で codegraph クエリを強制実行する。

### codegraph フル活用フェーズ

| フェーズ | スキル・Step | 主な用途 | 推奨ツール |
|---------|------------|---------|-----------|
| 設計 | `/aidd-epic-design` Step 0〜3 | 既存コード構造・アーキテクチャパターンの把握 | `codegraph_context`・`codegraph_explore` |
| 影響範囲調査 | `/aidd-epic-design` Step 2・3-2 | 変更による影響半径の確認 | `codegraph_impact`・`codegraph_trace` |
| 実装 | `/aidd-impl` Step 0 | 依存関係・既存コードパターンの観察 | `codegraph_explore`・`codegraph_callers`・`codegraph_impact` |
| リファクタ | `/aidd-impl` Step 0（事前観察） | 呼び出し元・呼び出し先の確認 | `codegraph_callers`・`codegraph_callees` |

### インデックス自動維持（ADR-021）

MANDATORY: lefthook post-commit フックに `codegraph index --quiet || true` を設定し、コミット後に自動更新する。
DO NOT: post-commit フック失敗時にコミットをブロックする（`|| true` で失敗を分離する）。

---

## ドキュメント探索原則

MANDATORY: 仕様・設計判断・業務知識・用語定義を参照する際、ファイル Read より先に Doc Intelligence MCP ツールを使用する。
MANDATORY: Doc Intelligence 使用前に必ず `task lightrag:status` で状態を確認し、Ready でない場合は即時修復してから作業を開始する。

| 状態 | 判定条件 | 対応 |
|------|---------|------|
| **Ready** | `task lightrag:status` が `Status: Ready` を表示 | Doc Intelligence MCP ツールを使用する |
| **Stale** | `task lightrag:status` が `Status: Stale` を表示 | **作業を中断**。`task lightrag:index` を実行して Ready に戻してから再開する |
| **Uninitialized** | `task lightrag:status` が `Status: Uninitialized` を表示 | **作業を中断**。`task lightrag:start` を実行して初期化してから再開する |
| **Indexing** | `task lightrag:status` が `Status: Indexing` を表示 | **作業を中断**。インデックス構築完了を待ち Ready になってから再開する |

NEVER: Stale / Uninitialized 状態のまま `Read` / `Grep` にフォールバックしてドキュメントを再発見する。

### Doc Intelligence フル活用フェーズ

| フェーズ | スキル・Step | 主な用途 |
|---------|------------|---------|
| Epic 設計 | `/aidd-epic-design` Step 0〜3 | ADR の設計理由・既存ドメイン知識の参照 |
| スキル実行中 | 任意スキル | 業務コンテキスト・用語定義・仕様の問い合わせ |
| ドキュメント更新 | `/aidd-impl-docs` | 既存ドキュメントとの drift 検出前の参照 |

### インデックス自動維持（ADR-023）

MANDATORY: lefthook post-commit フックに `task lightrag:index || true` を設定し、コミット後に自動更新する。
DO NOT: post-commit フック失敗時にコミットをブロックする（`|| true` で失敗を分離する）。

---

## SESSION START

MANDATORY: セッション開始時に以下を実行してから応答する。

1. SessionStart Hook の注入内容でプロジェクト状態を確認する
2. `gh issue list --label "status:in-progress"` を実行する
3. 進行中 Issue の関連ドキュメント（Epic Spec / Feature 設計）を docs/epics/, docs/spec/, docs/features/ から読む

MANDATORY: 読み込み完了後、根拠とともに次のアクションを提案する。

`status:in-progress` の Issue が存在する場合、Phase・進行中 Epic・未着手 Task・ブロッカーを提示して推奨アクションを1件提案する。

---

## ロール分担

AIDD-FW のパイプラインは「何を作るか」と「どう作るか」を明確に分離し、それぞれ適切なロールが担当する。

| ロール | 担当フェーズ | 主なスキル | 技術知識 |
|-------|------------|-----------|---------|
| **ビジネスロール**（PO / PM / 企画者）| setup-complete → spec-approved | `/aidd-new-epic`・`/aidd-prototype` | 不要 |
| **テクニカルロール**（TL / 開発者）| spec-approved 以降 | `/aidd-epic-design`・`/aidd-impl` | 必要 |
| **共同**（PO + TL）| 基盤整備・Phase 作成・各 Phase/Epic 完了判定 | `/aidd-setup`・`/aidd-charter`・`/aidd-review` | — |

**spec-approved ゲートが「何を作るか」と「どう作るか」の引き渡し点。**

- **spec-approved 以前**（ビジネスロール主導）: 課題・ペルソナ・ストーリー・成功指標・スコープを定義する。技術用語・実装手段を使わない
- **spec-approved 以降**（テクニカルロール主導）: 承認済み Epic Spec（`docs/spec/`・`docs/business-context/`）を起点に技術設計・実装・テストを担う。ビジネス要件を覆す決定は PO に差し戻す

DO NOT: ビジネスロールが spec-approved 前に実装詳細・アーキテクチャ判断を行う。
DO NOT: テクニカルロールが Epic Spec に技術用語・設計詳細を書き込んで spec-approved を受ける。

---

## 階層構造とゲート

| 階層 | 単位 | 意味 |
|------|------|------|
| **Phase** | GitHub Milestone + `docs/PROJECT-CHARTER.md §Phase 定義` | 名前 + ゴール + 期限 + スコープ + 成功条件 |
| **Epic** | GitHub Issue + `docs/epics/[N]-context.md` | ユーザーが認識できる機能。Issue 本文に Feature タスクリストを持つ。`context.md` に背景・成功指標・スコープを記録する |
| **Feature** | GitHub Issue（コンテキストバンドル）| Epic 内のサブ機能。Issue 本文に Related Docs を持ち、AI エージェントの実装開始点となる |
| **Story** | `docs/spec/[domain].md` の Story セクション | PO/PM 言語でユーザー価値を表現。AC と紐付く。GitHub Issue 化しない（リポジトリが正本）|
| **AC** | `docs/spec/[domain].md` の AC テーブル | Given/When/Then 形式の受け入れ条件。`AC-F[Feature Issue 番号]-NN` 形式で採番。テスト名・specs ファイルに AC-ID を含めて機械的なトレーサビリティを確保する |
| **Task** | `docs/features/[N]-[slug]/design.md` の Implementation Tasks | Outside-In TDD で実装する最小単位。完了条件は観測可能・機械的判定可能であること |

MANDATORY: 任意の成果物から人間の意図（Phase → Story → AC）まで逆方向に追跡できる状態を維持する。AC-ID は `git grep "AC-F[N]-NN"` で全関連ファイルを横断検索できる唯一のキーとなる。テスト名は `AC-F[N]-NN:` プレフィックス形式で記述し言語・フレームワーク非依存のグラフ連結を実現する（ADR-020）。

MANDATORY: 全ての開発成果物（Issue・設計書・OpenAPI・テスト・ドメイン定義）は明示的なリンクでグラフ状に繋がれている状態を維持する。リンクのない孤立した成果物を作らない。

MANDATORY: Phase のゴール・スコープ・成功条件は `docs/PROJECT-CHARTER.md` の `## Phase 定義` セクションに記述する。GitHub Milestone の description は Phase 名とゴール 1 文のみを記載し、詳細は CHARTER を参照する。`/aidd-new-phase` がこの追記を自動実行する。

### ゲート

| ゲート | 意味 | 承認者 | 発火タイミング |
|-------|------|--------|------------|
| **setup-complete** | 基盤整備完了 | PO + TL | プロジェクト初期化時 1 回 |
| **spec-approved** | Epic Spec 承認（`docs/epics/[N]-context.md` + `docs/spec/` 追記 + `docs/business-context/` 追記 + `docs/glossary.md` 追記）| PO / PM | Epic ごと 1 回 |
| **epic-complete** | Epic 完了 | TL | Epic ごと 1 回（全 Feature 完了確認） |
| **phase-complete** | Phase 完了 | PO + TL | Phase ごと 1 回 |

MANDATORY: ゲートをスキップしてはならない。人間の明示的な承認なしにゲートを通過してはならない。
MANDATORY: Feature ループ（design → impl）は内部処理。各ステップでユーザー確認は必要だが、ゲート扱いはしない。
MANDATORY: 1 Feature の設計から実装まで完了してから次の Feature へ進む（Per-Feature Loop）。
MANDATORY: ゲート通過は `docs/audit/YYYY-MM.md` に AUDIT LOGGING 形式で記録する。

### ゲートの責務

| 責務 | 内容 |
|------|------|
| 統合確認 | 複数の成果物が揃い相互に整合しているかを確認 |
| ゲート記録 | 通過事実を `docs/audit/YYYY-MM.md` に記録 |
| 遷移判定 | 次の段階に進む準備が整っているか判断し人間の承認を得る |

DO NOT: 個々の成果物の品質を再検査する（各スキルが実行時に保証する）。

### 遷移の 3 条件（全て満たす）

| # | 条件 | 責任者 |
|---|------|--------|
| 1 | AI 補完完了 — 全成果物で AI 補完が完了 | AI（各スキル）|
| 2 | AI レビュー PASS — 全観点で Critical 全件解決済み かつ Suggestions 全件適用済み | AI（`/aidd-review`）|
| 3 | 人間承認 — 判断者全員が統合結果を承認 | 判断者（PO / TL）|

DO NOT: 部分的な通過を認める。例外承認時は未達成項目のリスクを明記し解消 Issue を必ず作成する。

### レビュー見送りポリシー

MANDATORY: `/aidd-review` スキルにおける見送り（deferred）は Critical・Suggestions ともに禁止。

| 分類 | ポリシー |
|------|---------|
| Critical | 全件解決必須。見送り禁止。CONDITIONAL PASS 不可。 |
| Suggestions | 全件適用必須。見送り禁止。 |

NEVER: Critical または Suggestions の「見送り」選択肢を提示・受け付ける。
NEVER: ADR を根拠に Critical の見送りを許可する。

### ゲート判定の問い

詳細チェックリストは `aidd-framework/review-perspectives/{ゲート名}.md` を参照。

| ゲート | 問い |
|--------|------|
| setup-complete | プロジェクトの方向性が合意され、技術基盤が動作確認済みか？ |
| spec-approved | Epic Spec が承認されているか？`docs/spec/` の Stories + AC・`docs/business-context/` の DC・成功指標・Won't Have が明示されているか？ |
| epic-complete | 全 Feature が完了し、全テスト（E2E / 統合 / ユニット）が GREEN であり、`task check:ac-coverage` が PASS し、lint / 型チェックが PASS し、LOCAL-FIRST VERIFICATION の Epic 行が全項目通過し、コードレビュー（`/aidd-review epic` 観点 5）が PASS しているか？ |
| phase-complete | Phase の全 Epic がクローズされ、Milestone のゴールを満たしているか？ |

---

## AUDIT LOGGING

> **目的:** 重要な意思決定の独立した不変記録。PR/Issue/会話ログから独立した監査証跡として、PR が削除されても・Issue がクローズされても残る形で「誰がいつ何を承認・却下・見送ったか」を残す。

MANDATORY: 以下を `docs/audit/YYYY-MM.md` に追記する。ファイルが存在しない場合は作成する。

| 種別 | 形式 | 担当スキル |
|------|------|-----------|
| ゲート通過 | `[ISO8601] GATE <id> PASS — <参照>` | `/aidd-review`（setup-complete / spec-approved / epic-complete）・`/aidd-phase-closing`（phase-complete）|
| ゲート却下 | `[ISO8601] GATE <id> REJECT — <項目>` | `/aidd-review`（phase-complete を含む全ゲート。PASS と異なり REJECT は判定スキルが一元記録） |
| 意思決定見送り | `[ISO8601] DEFER <area> — <理由 + 解消 Issue 番号>` | `/aidd-discuss` / `/aidd-review` / `/aidd-quick-task` 等で見送り判定をしたスキル |
| 規約逸脱許可 | `[ISO8601] EXCEPTION <rule> — <理由>` | 該当スキル（人間が例外承認した場合） |
| 承認ロールバック | `[ISO8601] REVOKE <gate/decision> — <理由>` | 該当スキル（一度通過したゲートを取り消す場合） |

DO NOT: ユーザー入力・スキル実行ログをここに記録する（それぞれ会話 jsonl・git log で記録済み）。
DO NOT: 軽微な変更・通常の作業ログを追記する（監査ログの SN 比を下げる）。
DO: 監査ログは追記専用（過去エントリの編集・削除は禁止）。誤記載は新エントリで訂正する（`[ISO8601] CORRECT <prev-line> — <訂正内容>`）。

---

## FEEDBACK 記録

MANDATORY: ユーザーから訂正・指摘・仕様変更を受けた場合、修正を最優先で実施した上で以下を実行する。

- 同じパターンが再発しうる指摘 → `gh issue create --label feedback --title "FB: <概要>" --body "<種別・関連 Task・内容・正しい対応>"` で feedback Issue を作成する
- AI ミスパターンの再発防止 → `CLAUDE.md` の「プロジェクト固有の発見事項」セクションに具体的に追記する（「X の場合は Y を確認する」形式）
- 規約逸脱が判明したパターン → `CLAUDE.md` / `AGENTS.md` の該当規約に追記する
- 仕様変更 → 該当 `docs/spec/[domain].md`・`docs/features/[N]-[slug]/design.md` を即座に更新する

DO NOT: 軽微な指摘（typo・フォーマット）を feedback Issue 化する（ノイズ削減）。
DO NOT: 「注意する」等の曖昧な追記をする（具体的な検出パターンを記述）。
DO NOT: ユーザー承認なしに Issue 作成・規約追記を実行する。

---

## DIRECTORY STRUCTURE

- アプリケーションコード: ルート `/`
- ドキュメント: `docs/`
- フレームワーク: `aidd-framework/`（プロジェクト固有変更禁止）
  - `aidd-framework/conventions/` — スタック別規約（`terraform.md` / `nextjs.md` 等。プロジェクトの採用スタックに該当するファイルを参照）
  - `aidd-framework/agents/` — エージェントペルソナの SSOT（Markdown + YAML frontmatter）。`scripts/build-agents.py` が `agents/`（Claude Code 用）と `.codex/agents/`（Codex 用 TOML）を生成。ペルソナ編集は SSOT のみ。ビルド成果物の直接編集禁止
  - `aidd-framework/common/` — 全スキル共通の骨格 SSOT。`presentation-format.md`（Step ループ提示）・`briefing-format.md`（フェーズ完了ブリーフィング）。スキル固有差分は SKILL.md に記述
  - `aidd-framework/review-perspectives/` — ゲート別レビューチェックリスト

### 成果物配置マップ

**プロジェクトレベル SSoT（正本）**

| 成果物 | 配置パス | 性質 |
|------|---------|------|
| Phase 詳細定義 | `docs/PROJECT-CHARTER.md §Phase 定義` | 正本 |
| ビジョン・NFR | `docs/PROJECT-CHARTER.md` | 正本 |
| アーキテクチャ基盤 | `docs/architecture/baseline.md` | 正本 |
| 技術規約 | `aidd-framework/conventions/[stack].md`（共通）+ `docs/project-conventions/overrides.md`（差分のみ・任意）| 正本 |
| 業務知識（ドメイン SSoT）| `docs/business-context/[domain].md`（分割前提）| 正本・Epic ごとに追記 |
| 業務用語集 | `docs/glossary.md` | 正本・Epic ごとに追記 |
| Feature→Story→AC（仕様 SSoT）| `docs/spec/[domain].md`（分割前提）| 正本・Epic ごとに追記 |
| API 仕様 | `specs/openapi.yaml` | 正本・Feature ごとに追記 |
| DB スキーマ | `specs/schema.sql` | 正本・Feature ごとに追記 |
| 画面詳細仕様 | `specs/screens/[screen].md` | 正本・Feature ごとに追記 |
| E2E テスト仕様 | `specs/e2e/[feature].md` | 正本・Feature ごとに生成 |
| 設計判断 | `docs/architecture/adr/ADR-NNN-*.md` | 正本 |

**Epic・Feature レベル（記録・作業）**

| 成果物 | 配置パス | 性質 |
|------|---------|------|
| Epic コンテキスト | `docs/epics/[N]-context.md`（背景・成功指標・スコープ）| 記録（承認時スナップショット）|
| Feature 技術設計 | `docs/features/[N]-[slug]/design.md`（Related Docs・観測ポイント・Tasks）| 作業ドキュメント |
| Task 完了条件付きチェックリスト | `docs/features/[N]-[slug]/design.md` §Tasks | 作業ドキュメント |

**プロトタイプ（視覚化・具体化）**

| 成果物 | 配置パス |
|------|---------|
| UI プロトタイプ | `mocks/ui/*.tsx` |
| CLI プロトタイプ仕様 | `mocks/cli/spec.md` |

**その他**

| 成果物 | 配置パス |
|------|---------|
| 監査ログ | `docs/audit/YYYY-MM.md` |
| 質問ファイル | `docs/questions/YYYY-MM-DD-[topic].md` |
| モダナイゼーション RE 設計 | `docs/modernize/` |

---

## DOCUMENT LINKAGE

MANDATORY: ADR・規約・設計判断に影響する変更は、対応するマスタドキュメント（CHARTER / 規約 / `docs/spec/` / `docs/business-context/` 等）を**同一 PR（同一コミット）内で更新する**。
DO NOT: マスタドキュメント未更新のまま ADR だけ作成して PR を出す。
DO: ADR 作成時の連動更新は `/aidd-create-adr` Step 4 が自動実行する。

### 全成果物トレーサビリティ

aidd-fw の哲学「全ての開発ドキュメントをリポジトリで管理する」の技術的な完結形として、リポジトリが正本となり GitHub Issues は進捗管理のみを担う。AC-ID が全アーティファクトを縦串に繋ぐ統一キー。

```
Phase（Milestone）
  └─[タスクリスト]─ Epic Issue → docs/epics/[N]-context.md（背景・指標・スコープ）
       └─[タスクリスト]─ Feature Issue
            └─[Related Docs]─ docs/spec/[domain].md（Stories + AC 正本）
            └─[Related Docs]─ docs/features/[N]-[slug]/design.md（技術設計）
            └─[Related Docs]─ docs/business-context/[domain].md（ドメイン知識）

AC-F[N]-01（docs/spec/[domain].md に定義）
  ├─ specs/openapi.yaml（x-ac: [AC-F[N]-01]）
  ├─ specs/schema.sql（-- AC: AC-F[N]-01）
  ├─ specs/screens/[screen].md（参照 AC 列）
  └─ specs/e2e/[feature].md（AC ID 列）
       └─ e2e/[feature].spec.ts（test("AC-F[N]-01: E2E ...")）
       └─ integration/[feature].spec.ts（test("AC-F[N]-01: Integration ...")）
       └─ unit/[feature].spec.ts（test("AC-F[N]-01: Unit ...")）
```

**エッジの種類と形式:**

| エッジ | 形式 | 信頼度 |
|---|---|---|
| Epic → Feature | Issue 本文タスクリスト `- [ ] #N` | 決定論的 |
| Feature → Spec | Issue 本文 `Related Docs` に `docs/spec/[domain].md` | 決定論的 |
| Feature → Design | Issue 本文 `Related Docs` に `docs/features/[N]-[slug]/design.md` | 決定論的 |
| AC → specs ファイル | `x-ac` / コメント / 参照 AC 列に `AC-F[N]-NN` | 決定論的 |
| AC → テスト | テスト名に `AC-F[N]-NN:` プレフィックス（ADR-020 準拠）| 決定論的 |
| Story → PR | PR 本文 `Closes #FeatureIssue` | 決定論的 |

MANDATORY: 新しい成果物を作成するとき、必ず `docs/spec/` への AC-ID 記載と Feature Issue の Related Docs 追記を同時に行う。孤立した AC・孤立した specs ファイルを作らない。

MANDATORY: `git grep "AC-F[Feature Issue#]-NN"` で AC に関連する全 specs ファイル・テストコードが発見できる状態を常に維持する。

---

## LOCAL-FIRST VERIFICATION

MANDATORY: 全動作確認はローカルで行い、PASS 後に push / PR 作成 / phase-complete 判定へ進む。
DO NOT: CI/CD や dev 環境を動作確認の場として使う。
DO: ローカル再現が物理的に不可能な環境依存（クラウド IAM 等）のみ例外を許容。PR コメントに理由を明記する。

### 確認マトリクス

| 確認種別 | Task（コミット前） | Epic（PR 作成前） | Phase（phase-complete 前） |
|---------|------------------|-----------------|----------------------|
| ビルド | 静的チェック（型/lint） | `task build` | `task build` |
| 起動 | — | `task dev` 起動確認 | フルスタック起動 |
| 実働 | ユニットテスト（対象 AC）| Tier 判定 ↓ | `docs/spec/` 主要 AC を通し実行 |

### Tier 判定（Epic 実働確認）

変更ファイルから最高 Tier を適用する。

| Tier | 判定条件 | 実行内容 |
|------|---------|---------|
| 0 | `*.md` / `docs/**` / `skills/**` のみ | スキップ |
| 1 | API コード変更 | dev server にリクエスト送信・レスポンス確認 |
| 2 | UI コード変更 | agent-browser でローカル dev server 画面確認 |
| 3 | IaC / DB スキーマ変更 | plan / migration diff を提示。apply は人間が実行 |

DO: Phase 実働確認は実行前にユーザー承認を得る。
NEVER: PR 作成 → CI 待ち → 修正 / マージ → dev 環境で動作確認 / デプロイして原因特定。

---

## GIT & PR RULES

### 基本ルール

- DO NOT: main に直接コミット・プッシュする
- DO NOT: ユーザーの承認なしにブランチ・ワークツリーを作成する
- DO NOT: `--admin` フラグで CI をスキップする
- DO NOT: 明示的な「merge」指示なしに `gh pr merge` を実行する
- MANDATORY: PR を経由してマージする（CI PASS 必須）
- MANDATORY: ワークツリー作成は `task wt:create BRANCH=<branch>`（手動 `git worktree add` 禁止）
- MANDATORY: 1 PR = 1 Epic。Phase = Milestone。Task = Feature Issue 本文チェックリスト項目
- MANDATORY: PR description に `Closes #N` または `Related #N` を含める

### ブランチ命名規則

GitHub Flow を採用。main から分岐し、PR 経由でマージする。

| 種別 | パターン | 例 |
|------|---------|-----|
| 機能開発（Epic）| `feature/ES-NNN-slug` | `feature/ES-001-user-auth` |
| バグ修正 | `fix/ISSUE-NNN-slug` | `fix/ISSUE-012-login-error` |
| 緊急修正 | `hotfix/ISSUE-NNN-slug` | `hotfix/ISSUE-045-crash` |
| 雑務 | `chore/slug` | `chore/update-deps` |

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) に従う。

| type | 用途 |
|------|------|
| `feat` | 新機能の追加 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみの変更 |
| `refactor` | リファクタリング（機能変更なし）|
| `test` | テストの追加・修正 |
| `chore` | ビルド・CI・依存関係などの雑務 |

### マージ方式

Squash merge を使う。1 PR = 1 Epic = 1 コミットで履歴を簡潔に保つ。

### 階層別 git 操作

| 階層 | git 操作 |
|------|---------|
| Phase | git 操作なし（GitHub Milestone のメタデータ） |
| Epic | `feature/ES-NNN-slug` ブランチ + ワークツリーを `/aidd-new-epic` Step 1 承認時に作成。draft PR を spec-approved（Step 6）承認時に作成。`/aidd-review epic` PASS 後に draft 解除 |
| Feature | Epic ブランチ上でコミット（独立ブランチを作らない） |
| Task | Feature Issue 本文チェックリスト項目 + コミット |
| 単発作業 | `/aidd-quick-task` 経由（fix / hotfix / chore） |

### ブランチ・ワークツリー運用

DO NOT: Epic フロー中にブランチを切り替える（`/aidd-new-epic` 〜 `/aidd-review epic` まで一貫）。
DO NOT: 中間 PR を作成する（spec-approved 後に draft PR を 1 本作成し、完了時に ready に変換）。
DO NOT: squash merge 済みのブランチを再利用する（追加修正は main から新規ブランチ）。
DO: PR 作成前に `git rebase origin/main` を実行する。
DO: 並行 Epic はそれぞれ独立したワークツリーで作業する。
DO: PR マージ後は速やかに `task wt:remove BRANCH=<branch>` で削除する。

### Epic PR マージ手順

1. `/aidd-review epic` PASS（`gate:reviewed` ラベル付与）
2. ユーザーの明示的な「merge」指示
3. `git push origin HEAD`
4. `gh pr merge --squash --delete-branch`
5. `git checkout main && git pull --ff-only`

### Merge Guard

PR マージには `gate:reviewed` ラベルが必要。

| ラベル | 付与タイミング | 付与スキル |
|-------|-------------|-----------|
| `gate:reviewed` | `/aidd-review epic` PASS 時 | `/aidd-review epic` |

`gate:reviewed` は一度付与されると sticky（push しても自動除去されない）。未レビューのまま merge されることを防ぐためのゲートであり、push ごとの再レビューは強制しない。手動で外す場合は明示的に `gh pr edit --remove-label "gate:reviewed"` を実行する。

---

## SDD MIGRATION GUIDE

v3.x（DDD パイプライン）から v4.x（SDD パイプライン）への移行手順。

### 廃止された成果物と移行先

| 旧成果物 | 移行方法 |
|---------|---------|
| `docs/epics/[N]-[slug].md`（PRD）| `docs/epics/[N]-context.md`（背景・指標・スコープのみ）に軽量化。Stories + AC は `docs/spec/[domain].md` に移行 |
| `docs/epics/[N]-plan.md`（Epic Plan）| 廃止。内容は `docs/features/[N]-[slug]/design.md` に分散 |
| `docs/domain/bounded-contexts.md` | `docs/business-context/[domain].md` に移行（SDD 形式に書き直し）|
| `docs/domain/aggregates/[名前].md` | `docs/business-context/[domain].md` の管理対象セクションに統合。**例外**: ES-1374 で追加された `ArtifactEdge.md`・`ArtifactGraphSchema.md`・`IssueContextBundle.md` はフレームワーク自身の ArtifactGraph BC 定義であり `docs/domain/` に維持する（#1406 で移行計画を検討）|
| `docs/domain/events.md` | `docs/business-context/[domain].md` の業務イベントセクションに統合 |
| `docs/features/[N]-design.md`（旧形式）| `docs/features/[N]-[slug]/design.md`（新ディレクトリ形式）に移行 |
| Story Issues（GitHub）| `docs/spec/[domain].md` の Story セクションに移行。Issue はクローズ |
| `mocks/api/openapi.yaml` | `specs/openapi.yaml` に移行（`mocks/api/` は削除）|
| `mocks/ui/screens.md` | `specs/screens/[screen].md` に移行 |
| `docs/project-conventions/error-handling.md` / `logging.md` / `test-strategy.md` | `aidd-framework/conventions/[stack].md` が正本となった（#1417）。共通部分は削除し、プロジェクト固有の差分のみ `docs/project-conventions/overrides.md` に残す |

### 廃止されたスキル

| 廃止スキル | 代替 |
|-----------|------|
| `/aidd-epic-plan` | `/aidd-epic-design` |
| `/aidd-feature-design` | `/aidd-epic-design`（Feature ループ Step 3）|
| `/aidd-feature-design-spec` | `/aidd-epic-design` Step 3 に統合 |
| `/aidd-feature-design-quality` | `/aidd-epic-design` Step 3 に統合 |
| `/aidd-feature-design-verify` | `/aidd-epic-design` Step 3 に統合 |
| `/aidd-epic-plan-verify` | `/aidd-epic-design` 各 Step 完了条件に統合 |
| `/aidd-epic-plan-foundation` | `/aidd-epic-design` Step 1 にインライン統合 |
| `/aidd-epic-plan-domain` | **廃止ではなく再設計**: 旧: `/aidd-epic-plan` Step 1 の DDD 設計サブスキル → 新: `/aidd-new-epic` Step 5 の SDD Domain Context 抽出サブスキル |
| `/aidd-epic-plan-features` | **廃止ではなく再設計**: 旧: `/aidd-epic-plan` Step 3 の Feature 分解サブスキル → 新: `/aidd-new-epic` Step 3 の Stories+AC co-create サブスキル |
| `/aidd-setup-conventions` | `aidd-framework/conventions/[stack].md` を直接参照（#1417）|

### 移行手順

1. `docs/domain/` 配下を `docs/business-context/[domain].md` 形式に書き直す（`/aidd-doc-drift` が補助）
2. 既存の PRD（`docs/epics/[N]-[slug].md`）から Stories + AC を `docs/spec/[domain].md` に抽出・移行
3. PRD ファイルを `docs/epics/[N]-context.md`（背景・指標のみ）に縮小
4. Story Issues をクローズし `docs/spec/` を正本にする
5. `mocks/api/openapi.yaml` を `specs/openapi.yaml` に移動
6. `mocks/ui/screens.md` を `specs/screens/` に移動・分割
7. 旧 `docs/features/[N]-design.md` を `docs/features/[N]-[slug]/design.md` に移行

---

## SKILL DEVELOPMENT

MANDATORY: 新規スキルを追加する場合は `/aidd-create-new-skill` を使う。
規約・設計パターン・Divergent 設計原則の詳細は `./SKILL-DEVELOPMENT.md` を参照する。

---

## SKILL PIPELINE

### 実行パターン（AC-F1446-01/02/03）

spec-approved ゲートを境に、以下のいずれかのパターンで実行できる:

| パターン | 担当 | 手順 |
|---------|------|------|
| **PO/PM パターン（分離実行）** | ビジネスロール | `/aidd-new-epic` を実行して spec-approved まで担当する。完了後はハンドオフパッケージが Epic Issue 本文に自動生成される。テクニカルロールに Epic Issue 番号（#N）を通知してテックフェーズを引き渡す |
| **エンジニアパターン（分離実行）** | テクニカルロール | Epic Issue 番号を起点に `/aidd-epic-design [Issue#]` を実行して技術設計から実装を担当する |
| **連続実行パターン** | 単一担当者 | 同一セッションで `/aidd-new-epic` → `/aidd-epic-design` を連続実行する（`/aidd-epic-design` は直前の Epic を自動推定して起動する。ハンドオフパッケージも生成されるが連続実行では参照不要）|

### パイプライン全体

| ステージ | スキル | ゲート | 主担当ロール |
|---------|-------|-------|------------|
| 基盤整備 | `/aidd-setup` → `/aidd-charter` → `/aidd-setup-stack` → `/aidd-setup-architecture` → `/aidd-setup-readme` | setup-complete | 共同（PO + TL）|
| Phase 作成 | `/aidd-new-phase`（Milestone 作成）| — | 共同（PO + TL）|
| Epic Spec 作成 | `/aidd-new-epic`（Stories+AC co-create / DC 抽出）| spec-approved | **ビジネスロール**（PO / PM）|
| 具体化（任意）| `/aidd-prototype`（ui / api / cli サブスキル）| — | **ビジネスロール**（PO / PM）|
| ↑ここまでが「何を作るか」ゾーン ↓ここからが「どう作るか」ゾーン | — | **spec-approved が引き渡しゲート** | — |
| Epic 設計・実装 | `/aidd-epic-design`（NFR確認 → 実装順序 → Feature ループ: design.md + specs/ 追記 → `/aidd-impl`）| — | **テクニカルロール**（TL / Dev）|
| Epic 完了 | `/aidd-review epic` | epic-complete | テクニカルロール（TL）|
| Phase 完了 | `/aidd-review phase` → `/aidd-phase-closing` | phase-complete | 共同（PO + TL）|

### スキル一覧（カテゴリ別）

#### 基盤整備

| スキル | 入力 | 出力 |
|--------|------|------|
| `/aidd-setup` | — | git init・GitHub Labels・ディレクトリ・branch protection 基本設定 |
| `/aidd-charter` | プロジェクト雑入力 | `docs/PROJECT-CHARTER.md`（ビジョン・ゴール・ペルソナ・アーキテクチャ方針・技術スタック・NFR・採用業界標準フレームワーク）|
| `/aidd-setup-stack` | Charter §技術スタック | mise.toml・.env.example・CI/CD・branch protection 拡張 |
| `/aidd-setup-architecture` | Charter + ドメイン設計 | `docs/architecture/baseline.md`（C4 Container 図・レイヤー構成）|
| `/aidd-setup-readme` | Charter + 技術スタック + CI | `README.md` |

#### Phase

| スキル | 入力 | 出力 |
|--------|------|------|
| `/aidd-new-phase` | 機能意図 | GitHub Milestone |

#### Epic

| スキル | 入力 | 出力 |
|--------|------|------|
| `/aidd-new-epic` | 機能意図 | `docs/epics/[N]-context.md` + `docs/spec/[domain].md` 追記 + `docs/business-context/[domain].md` 追記 + `docs/glossary.md` 追記 + Feature Issue 群 |
| `/aidd-prototype`（ui/api/cli）| Stories | `mocks/{ui,api,cli}/` への追記（視覚化プロトタイプ）|
| `/aidd-epic-design`（NFR確認 / 実装順序 / Feature ループ）| Epic Spec（`docs/spec/` + `docs/business-context/`）| `docs/features/[N]-[slug]/design.md` + `specs/` 追記 + 実装コミット |

#### Feature ループ（/aidd-epic-design 内部）

| ステップ | 出力 |
|---------|------|
| Feature 技術設計 | `docs/features/[N]-[slug]/design.md`（Related Docs・観測ポイント・Tasks）+ `specs/` への構造的追記 |
| TDD 実装（Outside-In）| E2E テスト（RED）→ 統合テスト（RED）→ ユニットテスト（RED）→ 実装（GREEN）→ リファクタ |

#### 完了処理

| スキル | 入力 | 出力 |
|--------|------|------|
| `/aidd-review epic` | Epic + 全 Feature 実装 | epic-complete レビュー |
| `/aidd-review phase` | Phase + 全 Epic | phase-complete レビュー |
| `/aidd-phase-closing` | phase-complete PASS | Milestone クローズ + レトロスペクティブ |

### 横断スキル

| スキル | 用途 |
|--------|------|
| `/aidd-next` | 次のアクション提案 |
| `/aidd-status` | 進捗確認 |
| `/aidd-doctor` | 環境健康診断 |
| `/aidd-create-adr` | ADR 対話的作成 |
| `/aidd-review` | フレームワーク文脈レビュアー（auto/trace/spec/epic/phase/setup/code）。信頼度フィルタ・トレーサビリティ検証・コードレビュー委譲を統合 |
| `/aidd-discuss` | 方針決定の議論 |
| `/aidd-doc-drift` | ドキュメント乖離検出 |
| `/aidd-quick-task` | 単発作業（fix / hotfix / chore）|
| `/aidd-research` | 技術調査 |
| `/aidd-update-playbook` | プレイブック差分更新 |
| `/aidd-update-framework` | フレームワーク更新 |
| `/aidd-lint` | ArtifactEdge EdgeType フォーマット検証・AcIdRef 逆引き（TasklistRef / DocPathRef / AcIdRef）|
| `/aidd-create-new-skill` | 新規スキル作成（チェックリスト・ペルソナカタログ統合）|
| `/aidd-glossary` | docs/glossary.md 自律メンテナンス（用語抽出・差分提案・削除提案）|
| `/aidd-publish` | プラグインリリース |
| `/aidd-supply-chain-check` | サプライチェーン baseline hardening 点検・低リスク patch plan 生成 |
| `/aidd-codegraph-status` | codegraph インデックス状態確認・既存プロジェクトへの後付けセットアップ案内 |
| `/aidd-troubleshoot` | 状況不明瞭な事案（バグ調査・デプロイ確認・環境トラブル）を OODA ループで構造的に解決（ADR-022）|
