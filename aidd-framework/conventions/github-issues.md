# GitHub Issues 規約

## 階層構造

```
Milestone（Phase）
  └─ Issue [epic]     Epic
       └─ Issue [feature]  Feature   ← コンテキストバンドルの単位
            └─ Issue [story]   Story
                 └─ AC-N: ...（Story 本文内）
```

親子関係は **GitHub ネイティブのタスクリスト**で表現する。
親 Issue 本文に `- [ ] #子Issue番号 タイトル` と書くと、
GitHub が自動で「tracked by」関係を生成する。

## Milestone = Phase

| 規約 | 内容 |
|---|---|
| タイトル | `Phase N: フェーズ名`（例: `Phase 1: 認証基盤`） |
| Due date | Phase の目標完了日を設定する |
| アサイン | Phase に属する全 Issue（Epic/Feature/Story）に同じ Milestone を設定する |

スキル `/aidd-new-phase` が Milestone を自動作成する。

## ラベル規約

### Type ラベル（必須・1つ）

| ラベル | 対象 | 作成スキル |
|---|---|---|
| `epic` | Epic Issue | `/aidd-new-epic` |
| `feature` | Feature Issue | `/aidd-new-epic`（Step 6-3）|
| `bug` | バグ修正 | `/aidd-quick-task` |
| `task` | 単発作業 | `/aidd-quick-task` |

### Status ラベル（必須・1つ）

| ラベル | 意味 | 遷移タイミング |
|---|---|---|
| `status: backlog` | 未着手 | Issue 作成時のデフォルト |
| `status: ready` | 着手可能 | 前提 Issue がクローズされたとき |
| `status: in-progress` | 実装中 | `/aidd-impl` 開始時 |
| `status: review` | PR レビュー待ち | PR 作成時 |
| `status: blocked` | ブロック中 | 手動（理由をコメントに記載） |

## PR との連結

PR 本文に `Closes #Story番号` を記述することで Story と PR が自動連結される。

```markdown
## Summary
ログイン機能の実装

Closes #42
Closes #43
```

## GitHub MCP による走査パターン

AI エージェントが「Feature X の実装コンテキストを取得する」手順（概念的な擬似コード。実際のツール名は MCP 設定に依存）：

```pseudocode
1. get_issue(feature_id)
   → Overview / Related Docs を取得

2. Related Docs のパスを使って
   → get_file_contents("docs/spec/[domain].md") で Stories + AC を取得
   → get_file_contents(design_path) で技術設計ドキュメントを取得

合計: 1 + M(ドキュメント数) 回
SDD では Story は GitHub Issue 化しない（docs/spec/ が正本）。
従来の grep × 20 / Read × 15 から大幅削減。
```

## Acceptance Criteria の命名規約

Story Issue 内の AC は `AC-F[Feature Issue番号]-NN:` 形式で記述する（FRAMEWORK.md と同一）。

```markdown
- [ ] AC-F42-01: 正しい認証情報でログインするとダッシュボードにリダイレクトされる
- [ ] AC-F42-02: 誤ったパスワードでは 401 エラーが返る
```

テストファイル内でもテスト名に同じ AC-ID プレフィックスを含めることで、言語・フレームワーク非依存でグラフが AC とテストを自動連結する（ADR-020）。

```typescript
// TypeScript（Jest/Vitest）
describe('AC-F42-01: 正しい認証情報でログインするとダッシュボードにリダイレクトされる', () => {
  ...
})
```

```python
# Python（pytest）
def test_ac_f42_01_login_with_valid_credentials():  # AC-F42-01: をテスト名に含める
    ...
```

抽出ルール: テストファイル全体から `AC-F\d+-\d+` パターンにマッチするテスト名を検索する。プレフィックスなしのテストは AcIdRef エッジを持たない。

## スキルとの対応

| スキル | Issue 操作 |
|---|---|
| `/aidd-new-phase` | Milestone 作成 |
| `/aidd-new-epic` | Epic Issue 作成・Milestone アサイン |
| `/aidd-new-epic` | Feature Issue 作成（Step 6-3）・Epic タスクリストに追記 |
| `/aidd-impl` | Feature の status を `in-progress` に更新 |
| `/aidd-quick-task` | Task/Bug Issue 作成 |
| `/aidd-status` | Milestone・Issue の進捗を集計して表示 |
