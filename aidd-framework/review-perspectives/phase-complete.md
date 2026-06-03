# phase-complete レビュー観点

`/aidd-review` が phase-complete（Phase 完了）と判定したときに読み込まれる観点集。

**判定したいこと:** Phase の目標を達成し、次の Phase に進める状態か？

**観点数:** 3

> Epic 単位の品質（アーキテクチャ・コード品質・テスト・運用準備・マスタドキュメント反映）は epic-complete レビューで既に検証済み。phase-complete は **Phase 全体としての整合性** のみを確認する。

---

## 共通出力フォーマット

MANDATORY: 各観点の Agent は以下フォーマットで結果を返すこと。フォーマット逸脱時は orchestrator が再要求する。

```markdown
## 観点 N レビュー結果: [観点名]

### Critical
- [問題タイトル]
  - 該当箇所: [ファイル名:行 / Issue 番号 / Milestone 番号]
  - 理由: [なぜ問題か・観測根拠を 1〜2 行]
  - 修正方針: [具体的アクション]

### Suggestions
- [改善提案タイトル]
  - 該当箇所: [ファイル名:行]
  - 提案理由: [改善で得られる効果]

### OK Points
- [評価する設計判断]

### Analysis Notes
- レビュー限界: [確認できなかった範囲]
- 不確実性: [前提条件・情報不足箇所]
```

DO NOT: 各セクションを省略する。該当なしの場合は「- なし」と明記。
DO NOT: 推測のみでの指摘（観測根拠を必ず添える）。
MANDATORY: 該当箇所はファイル名 + 行番号（または Issue / Milestone 番号）まで具体化する。

---

## 観点 1: Charter 整合性 — aidd-product-manager

### レビュー対象

- `docs/PROJECT-CHARTER.md`（特にセクション 10「業界標準フレームワーク採用方針」）
- 全 Epic の PRD（`docs/epics/[N]-*.md`）

### MANDATORY チェック項目

1. **ビジョン・成功指標整合性**
   - Charter のビジョン・成功指標に対する Phase の貢献が記録されている
   - Phase の成果が Charter の方向性と矛盾しない

2. **Won't Have 遵守**
   - Charter で「対象外」と定義された機能が実装されていない
   - 混入があった場合、経緯と判断が PR description / Issue コメントに記録されている
   - DO NOT: Won't Have 違反を放置

3. **業界標準フレームワーク採用方針の準拠（セクション 10）**
   - Charter セクション 10 で「採用」と判定されたフレームワークが Phase 内の各 Epic で実際に適用されている
   - 「不採用」と判定されたフレームワークが Epic Plan / Feature Design で勝手に採用されていない
   - Charter の不採用理由が依然として妥当か（プロジェクト性質の変化を検知）
   - 採用判定の見直しが必要な場合は `/aidd-charter` 実行を提案

### 重要度判定基準

- **Critical**: Charter ビジョンへの貢献記述なし / Won't Have 違反の放置 / Charter で不採用としたフレームワークの無断採用
- **Suggestion**: 貢献度の定量化・指標追加 / 採用判定の見直し提案
- **OK Point**: ビジョン整合・Won't Have 完全遵守・採用方針 100% 準拠

---

## 観点 2: Milestone ゴール整合性 — aidd-product-owner

### レビュー対象

- 対象 Milestone のゴール文（`gh api repos/<owner>/<repo>/milestones/<num>` の description）
- Phase 内 Epic 一覧（`gh issue list --milestone "$MILESTONE_TITLE"`）

### MANDATORY チェック項目

1. **Milestone ゴール達成度**
   - Milestone のゴール文が示す目的を Phase の Epic 群が達成している
   - 未達成側面がある場合、未達理由と次 Phase 対応方針が記載されている

2. **計画スコープ遵守**
   - Phase 計画時の Epic マッピングからの逸脱（追加 / 削除）が記録されている
   - スコープクリープ / スコープ縮小があった場合は経緯と判断理由が明示されている

3. **次 Phase への要件引き継ぎ**
   - 次 Phase で対応する要件・残課題が「次 Phase」「将来検討」「やらない」のいずれかに分類されている

### 重要度判定基準

- **Critical**: Milestone ゴール未達かつ理由・対策なし / スコープ逸脱の放置
- **Suggestion**: 引き継ぎ分類の見直し
- **OK Point**: ゴール達成・スコープ通り完成・引き継ぎ明確

---

## 観点 3: 全 Epic 完了確認 — aidd-builder

### レビュー対象

- 全 Epic Issue 状態（`gh issue list --label epic --milestone "$MILESTONE_TITLE" --state all`）
- 全 Feature Issue 状態（`gh issue list --label feature --milestone "$MILESTONE_TITLE" --state all`）
- 監査ログ（`docs/audit/YYYY-MM.md`）

### MANDATORY チェック項目

1. **全 Issue closed 確認**
   - 全 Epic Issue が closed
   - 全 Feature Issue が closed
   - epic-complete 通過記録が全 Epic 分 `docs/audit/` に存在

2. **未完了の扱い**
   - 未完了 Epic / Feature がある場合、状態（次 Phase 移送 / 延期 / キャンセル）が明確
   - 持ち越し Issue が作成されている

3. **品質ゲート**
   - 各 Epic は epic-complete レビュー PASS 済み（アーキテクチャ・コード品質・運用準備・マスタドキュメントは Epic レビューで検証済み）

### 重要度判定基準

- **Critical**: open のままの Epic / Feature 残存・epic-complete 未通過 Epic 存在
- **Suggestion**: 持ち越し Issue の分類追記
- **OK Point**: 全 Issue closed・全 epic-complete 通過記録あり

---

## 集約後の判定基準

`/aidd-review` が全 3 観点のレビュー結果を集約した後、以下で phase-complete 通過/不通過を判定する:

| 状態 | 条件 |
|------|------|
| **PASS** | 全観点で Critical が 0 件 |
| **FAIL** | Critical が 1 件以上残存 |

DO NOT: Critical を残したまま PASS とする。FAIL の場合は Critical を全て解消してから再レビューを実行する。

phase-complete 通過後は `/aidd-phase-closing` を呼び出して、Milestone クローズ・レトロスペクティブ記録・次 Phase 準備を実施する。
