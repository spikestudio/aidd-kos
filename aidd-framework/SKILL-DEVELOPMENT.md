<!-- @imported via FRAMEWORK.md: see ## スキル実行原則 -->
<!-- DO NOT edit directly without updating /aidd-create-new-skill, aidd-framework/FRAMEWORK.md, and CLAUDE.md -->

# SKILL DEVELOPMENT

> 新規スキル作成・既存スキル改修時に参照する。日常開発では参照不要。

---

## スキル設計原則

### 全スキルは Divergent として設計する

**手順（Default Workflow）はゴール達成の初期方針。** Success Criteria を満たすことが目的であり、手順を守ることは目的ではない。

LLM スキルとして実装する価値があるのは、フローが固定でも各ステップに判断・解釈が必要なもの。手順が完全に固定で判断不要なタスクはスクリプトやワークフローエンジンで代替する。

### SKILL.md の標準構造

```
## Mission（達成目標）
## Success Criteria（完了条件）
## Default Workflow（初期方針）
## Absolute Rules（このスキル固有の絶対ルール）  ← 固有ルールがある場合のみ
## インターフェース（前提・入力・出力・後続スキル）
## 重要なルール
```

### 各セクションの定義

| セクション | 内容 | 必須 |
|-----------|------|------|
| Mission | スキルが達成する目標（1〜2文）| 必須 |
| Success Criteria | 完了条件。ユーザーが承認の根拠にする粒度で記述 | 必須 |
| Default Workflow | 初期方針として標準手順を記述。状況に応じて調整可 | 必須 |
| Absolute Rules | このスキル固有の絶対ルール（FRAMEWORK.md の横断 Absolute Rules に加えて必要なもののみ）| 任意 |
| インターフェース | 前提・入力・出力・後続スキル | 必須 |

### Absolute Rules の2層構造

```
全スキル横断（FRAMEWORK.md が SSOT）
  └─ 承認2択のみ / ブリーフィング省略禁止 / 推測・仮定禁止 など

スキル固有（各 SKILL.md の ## Absolute Rules が SSOT）
  └─ 例: /aidd-impl → テストなしに実装開始しない（TDD 規律）
  └─ 例: /aidd-new-epic → PRD に技術用語を書かない
  └─ 例: /aidd-review → Critical を AI が見送り提案しない
```

MANDATORY: Default Workflow ではなく Success Criteria を満たすことを優先する旨を「重要なルール」に含める。

---

## 共通ループ（Default Workflow の骨格）

全スキルの Default Workflow はこのループ構造を出発点とする。状況に応じてステップの省略・統合・追加が可能。ただし Approve（人間の承認）は Absolute Rule として省略不可。

1. Observe: 入力・コンテキスト・既存成果物を収集する
2. Orient: 不足情報を補完する。不足が残る場合は人間に質問する
3. Generate: 成果物を生成する
4. Review: セルフレビューを実行する（下記「セルフレビュー反復ループ」）
5. Brief: 人間にブリーフィングする（`aidd-framework/common/briefing-format.md` 参照・省略禁止）
6. Approve: 人間の承認を得る。修正指示なら Step 3 に戻る

### セルフレビュー反復ループ

スキル自身が生成した成果物をチェックし、問題があれば修正する反復ループ。

> **`/aidd-review` のゲートレビューとの違い:** セルフレビューはスキル実行中の内部処理（MUST FIX 0 件で PASS）。ゲートレビューはゲート通過時の独立レビュー（Critical 0 件で PASS）。両者は別レイヤー。

MANDATORY: MUST FIX が残っている間は最大 3 ラウンド反復する。
MANDATORY: 3 ラウンドで解消しない MUST FIX は必ずユーザーに報告する。
DO NOT: MUST FIX を残したままブリーフィングへ進む。

#### 重大度判定

| 判断軸 | 重大度 |
|--------|--------|
| 規約違反 / AC 不準拠 / 設計整合性の不一致 / テンプレート必須セクション欠落 / 上位ドキュメントとの矛盾 / 曖昧な記述 | MUST FIX |
| パフォーマンス改善（規約外）| SHOULD FIX |
| 可読性・保守性の改善 | CONSIDER |

#### 反復ループ手順

| ラウンド | 処理 | PASS 条件 | FAIL 時の遷移 |
|---------|------|---------|------------|
| 1 | スキル固有の観点 + 重大度判定でレビュー実施 | MUST FIX 0 件 | 修正してラウンド 2 へ |
| 2 | 全観点で再レビュー（修正の波及効果対応）| MUST FIX 0 件 | 修正してラウンド 3 へ |
| 3 | 全観点で再レビュー | MUST FIX 0 件 | ユーザー判断を仰ぐ |

#### レビュー結果の報告フォーマット

```
### セルフレビュー結果（ラウンド N/3）

| # | 重大度 | 観点 | 指摘内容 | 対応状況 |
|---|--------|------|---------|---------|

判定: PASS / FAIL（MUST FIX 残 N 件）
```

DO NOT: SHOULD FIX / CONSIDER を反復ループの対象にする（MUST FIX のみが反復条件）。
DO: SHOULD FIX / CONSIDER はブリーフィングで一覧提示し、対応要否をユーザーに判断いただく。

---

## 深さレベル

MANDATORY: 詳細レベルは問題に合わせて AI が自動調整する。ユーザーに選択を求めるな。

> 問題に必要なだけの詳細を作れ。単純な問題を膨らませるな。複雑な問題を省略するな。

影響要因: リクエストの明確さ / 問題の複雑さ / スコープ / リスクレベル / コンテキスト量 / ユーザー意向

---

## 対話パターン

全スキル共通の対話スタイルの基本形。ゴール・要件・方針が未確定な場面で特に重要になる。旧「探索的フェーズ専用」の原則ではなく、全スキルの Default Workflow に組み込まれるべき対話原則。

1. ふわっとした入力を受け付ける（課題でも構想でも可）
2. AI が推論して仮説・提案を **1 つだけ**提示する（選択肢を列挙しない）
3. 不明瞭な点を**指向性ある質問**で確認する
4. ユーザーと合意してから次のフェーズへ進む

対話ステートと詳細パターンは `aidd-framework/common/divergent-dialogue-format.md` を参照。

---

## スキル開発規約

| 項目 | ルール |
|------|--------|
| frontmatter | `name`・`description` 必須。`name` はディレクトリ名と一致 |
| context | 原則省略（インライン実行）。完全自己完結の単発タスクのみ `context: fork`（例外）|
| references/ 配置 | Step 詳細・レビュー指示・スキル固有テンプレートは `references/` に配置。共通骨格（提示・ブリーフィング）は `aidd-framework/common/` を参照 |
| Agent 呼び出し記法 | SKILL.md body 内では「自然言語 + ファイルパス明示」で記述（クロスプラットフォーム portable）。`Agent(subagent_type=...)` 等のプラットフォーム固有構文を直接書かない |
| ブリーフィング | 共通骨格は `aidd-framework/common/briefing-format.md`。スキル固有のフェーズ別重点は SKILL.md の「## ブリーフィング重点」に記述 |
| 提示フォーマット | 共通骨格は `aidd-framework/common/presentation-format.md`。スキル固有差分（Sub1/Sub2 見出し・選択肢 B）は SKILL.md の「## 提示フォーマット差分」に記述 |
| 対話言語 | 日本語 |
| 意思決定基準 | 「**FRAMEWORK.md の意思決定基準に従う**」を重要なルールに含める |
| ユーザー対話 | ユーザー確認なしの自動実行禁止 |
| ゲート制御 | ステップ内で明示的に実行（Absolute Rule: Default Workflow の調整対象外）|
| 命名規則 | 小文字英数字 + ハイフン。`aidd-` プレフィックス必須 |
| SKILL.md サイズ | 500 行以下（詳細は references/ に分離）|
| skill bundle 責務境界 | `skills/<skill-name>/` 配下には `SKILL.md` を起点に、必要な `references/`・`scripts/`・`schemas/`・`tests/`・`agents/` だけを同梱する。責務と無関係なファイルを置かない |
| 引数スキル | Step 1 で 3 パターン統一: 引数あり→特定 / なし→自動推定+確認 / 失敗→エラー+案内 |

詳細チェックリスト・frontmatter テンプレート・ペルソナカタログ・サイレント障害対策は `/aidd-create-new-skill` を参照。

---

## SKILL DESIGN PATTERNS

### 3 層構造

スキルは「オーケストレーター + サブスキル + references」の 3 層で構成する。

| 層 | 役割 | 禁止事項 |
|----|------|---------|
| オーケストレーター（親）| フロー制御・ユーザー承認取得・最終ファイル書き込み | Agent の二重ネスト |
| サブスキル（depth 1）| 成果物生成のみ（Read / Glob / Grep）| ユーザー対話・別 Agent 起動・ファイル書き込み |
| references/ | レビュー指示・フォーマット定義・検証ルール | — |

ディレクトリ構造:

```
aidd-framework/common/
  presentation-format.md         # 提示フォーマット骨格（SSOT・全スキル共通）
  briefing-format.md             # ブリーフィングフォーマット骨格（SSOT・全スキル共通）

skills/aidd-<name>/
  SKILL.md                       # オーケストレーター（共通骨格を参照・スキル固有差分を「## 提示フォーマット差分」「## ブリーフィング重点」に記述）
  references/
    review-<artifact>.md         # レビュー指示（スキル固有）
    output-validation.md         # 出力検証ルール（スキル固有）
    loop-back-matrix.md          # 差し戻し先マトリクス（スキル固有）
```

### 3 ステージループ（Sub1 → Sub2 → 人間）

```
Stage 1（Sub1: aidd-builder）
  └─ 成果物を生成してオーケストレーターに返す

Stage 2（Sub2: AI レビュー）
  ├─ `aidd-architect` エージェント: 設計観点レビュー
  └─ `aidd-business-analyst` エージェント: 業務観点レビュー（並行起動可）

Stage 3（人間レビュー）
  └─ aidd-framework/common/presentation-format.md に従い提示 → ユーザーの明確な承認を待つ
```

DO: 出力検証ルール不合格時、最大 3 回 Sub1 を再実行する。3 回失敗でエラー停止。
NEVER: depth 2 ネスト（Agent 内で Agent を起動）。

### Agent 呼び出し記法（クロスプラットフォーム portable）

MANDATORY: SKILL.md body 内で named subagent（aidd-architect / aidd-product-owner 等）を起動する場合は、以下の portable 記法を使う。プラットフォーム固有構文（`Agent(subagent_type=...)`・`Agent(prompt=...)` のコードブロック）を直接書かない。

理由: Claude Code は `Agent(subagent_type=...)` を、Codex は自然言語によるエージェント名指定をそれぞれサポートする。Agent Skills オープン標準には共通の起動構文がないため、両プラットフォーム LLM が解釈できる記法を採用する。

#### 推奨記法

```markdown
### [Step 名 / セクション名]

**専門家エージェント: `<agent-name>`**
（定義 SSOT: `aidd-framework/agents/<agent-name>.md` — 役割: <短い役割説明>）

`<agent-name>` エージェントを起動し、以下を実施してください:

## prompt

[実際の prompt 内容]

## 参照

- [必要な参照ファイル]
```

#### 並行起動の場合

```markdown
### 並行レビュー（Step N）

以下の専門家を 1 メッセージ内で並行起動してください:

| エージェント | 定義 SSOT | 観点 |
|------------|---------|------|
| `aidd-architect` | `aidd-framework/agents/aidd-architect.md` | 設計判断 |
| `aidd-business-analyst` | `aidd-framework/agents/aidd-business-analyst.md` | 業務要件 |

各エージェントへの prompt:
[省略]
```

DO: 自然言語で「`<agent-name>` エージェントを起動」と明示する。
DO: 定義 SSOT パス（`aidd-framework/agents/<agent-name>.md`）を併記してプラットフォーム解釈の精度を上げる。
DO NOT: `Agent(subagent_type=...)` 等のコード形式を SKILL.md body に直接書く（Claude Code 固有・Codex で動かない）。
DO NOT: agent 名のみで定義ファイルパスを省略する（LLM 解釈の確実性が下がる）。
