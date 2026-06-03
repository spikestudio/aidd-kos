# setup-complete レビュー観点

`/aidd-review` が setup-complete（基盤整備）と判定したときに読み込まれる観点集。

**判定したいこと:** プロジェクトとして開発を始められる状態か？

**観点数:** 6

---

## 共通出力フォーマット

MANDATORY: 各観点の Agent は以下フォーマットで結果を返すこと。フォーマット逸脱時は orchestrator が再要求する。

```markdown
## 観点 N レビュー結果: [観点名]

### Critical
- [問題タイトル]
  - 該当箇所: [ファイル名:行 / Issue / PR 番号]
  - 理由: [なぜ問題か・観測根拠を 1〜2 行]
  - 修正方針: [具体的アクション・関連ファイル]

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

DO NOT: 各セクションを省略する。該当なしの場合は明示的に「- なし」と書く。
DO NOT: 「〜かもしれない」「〜の可能性」のみの推測指摘（観測根拠を必ず添える）。
MANDATORY: 該当箇所はファイル名 + 行番号（または Issue/PR 番号）まで具体化する。

---

## 観点 1: プロジェクトビジョン・戦略整合性 — aidd-product-manager

### レビュー対象

- `docs/PROJECT-CHARTER.md`

### MANDATORY チェック項目

1. **ビジョン・ミッションの明確性**
   - プロジェクトの目的・存在意義が 1〜3 文で書かれている
   - 解決する課題と提供する価値が抽象論ではなく具体例で述べられている
   - DO NOT: 「価値を最大化する」「最高のサービスを目指す」等の測定不能な表現

2. **成功基準（KPI/OKR）の定義**
   - 定量的に測定可能な成功指標が定義されている（数値 + 単位 + 期限）
   - 目標値とベースライン値が両方記載されている
   - DO NOT: 「向上」「改善」のみで具体的数値がない

3. **ペルソナ・ターゲット顧客の特定**
   - 主要ペルソナが 1〜5 名定義されている
   - 各ペルソナの「課題（Job）」「利得（Gain）」「痛み（Pain）」が箇条書き 3 個以上で整理されている
   - DO NOT: 「ユーザー全般」「すべてのお客様」等の抽象ターゲット

4. **スコープと Won't Have**
   - 「やること」が機能領域単位（5〜10 領域）で列挙されている
   - 「やらないこと（Won't Have）」が明示されている（最低 3 件）

5. **Phase ロードマップの妥当性**
   - Phase 分割が完成順序で示されている
   - 各 Phase のゴールが 1 文で記述され Charter のビジョンに紐付く

### 重要度判定基準

- **Critical**: ビジョン・成功基準・ペルソナの 1 つ以上が欠落、または測定不能表現のみ
- **Suggestion**: 指標の精度向上・ペルソナの追加・Won't Have の追加候補
- **OK Point**: 全要素が具体・測定可能・ペルソナ解像度が業界標準（Jobs-to-be-done 等）に従う

---

## 観点 2: 技術基盤の準備 — aidd-architect

### レビュー対象

- `docs/architecture/tech-stack.md`
- `docs/architecture/adr/*.md`
- `CLAUDE.md` / `AGENTS.md`（プロジェクト固有ルール）

### MANDATORY チェック項目

1. **技術スタックの選定理由**
   - 主要技術（言語・FW・DB・インフラ）が決定されており名称・バージョンが書かれている
   - 各技術の選定理由が ADR に 100 文字以上で記録されている（背景・候補・選定根拠）
   - DO NOT: 技術名のみで根拠なし

2. **アーキテクチャ全体像**
   - システム構成図（Mermaid・PlantUML 等）が存在する
   - 主要モジュール境界とデータフローが図解されている

3. **プロジェクト固有ルールの記述**
   - CLAUDE.md / AGENTS.md にプロジェクト固有のルール（命名・規約の例外・スタック固有のパターン等）が記述されている
   - スタック別共通規約は `aidd-framework/conventions/` で参照可能（terraform / nextjs 等）

4. **非機能要件（NFR）**
   - 性能（レイテンシ・スループット）・可用性（稼働率）・拡張性（同時接続）の目標値が定義されている
   - DO NOT: NFR セクションが「TBD」のまま

5. **初期 ADR の存在**
   - 認証方式・データ永続化・通信プロトコルの ADR が最低 3 件存在
   - ADR テンプレートが `skills/aidd-create-adr/references/adr.md` に整備されている

### 重要度判定基準

- **Critical**: 技術スタック未決定、CLAUDE.md / AGENTS.md にプロジェクト固有ルール記述ゼロ、ADR テンプレート不在
- **Suggestion**: 細粒化されたルール追加・図解の充実・追加 ADR
- **OK Point**: 選定理由が ADR で完備・横断的整合がとれている

---

## 観点 3: 開発環境・CI/CD — aidd-builder

### レビュー対象

- `.mise.toml` / `mise.toml` / `Taskfile.yml` / `package.json` / `Makefile`
- `lefthook.yml`
- `.github/workflows/*.yml`
- `.envrc` / `mise.local.toml.example`
- `scripts/README.md`

### MANDATORY チェック項目

1. **Primary command surface の確立**
   - `dev` / `test` / `lint` 相当のコマンドが定義され、`<runner> <task>` 形式で実行可能
   - 採用方式（mise tasks / Taskfile / package scripts / Makefile）が 1 つに集約されている
   - DO NOT: 複数方式が併存して primary が不明確

2. **依存管理**
   - ツール・ライブラリの lock file（pnpm-lock.yaml・package-lock.json・mise lock 等）が存在
   - インストール手順が `task install` 等の単一コマンドで再現可能

3. **ローカル CI フック**
   - lefthook の pre-commit / pre-push が設定されている
   - pre-commit で lint / type check / test の少なくとも 1 つが実行される

4. **CI/CD パイプライン**
   - GitHub Actions 等で main へのマージ前に自動検証が走る
   - CI の検証項目とローカル lefthook の項目が 80% 以上一致している（過不足が許容範囲内）

5. **env/secrets 管理**
   - 環境変数テンプレート（`.env.example` / `mise.local.toml.example`）が存在
   - `.gitignore` に `.env` / `*.key` / `*.pem` / `mise.local.toml` のいずれかが含まれる

### 重要度判定基準

- **Critical**: `dev` コマンド未定義・CI 設定ファイルなし・`.gitignore` に秘密情報パターンなし
- **Suggestion**: CI 並列化・キャッシュ戦略・実行時間短縮
- **OK Point**: 新規参加者が 30 分以内に環境構築完了できる構造

---

## 観点 4: セキュリティ基盤 — aidd-security-specialist

### レビュー対象

- ブランチ保護: `gh api repos/{owner}/{repo}/branches/main/protection`
- `.gitignore`
- 依存スキャン設定（`.github/dependabot.yml` / `renovate.json`）
- `lefthook.yml`
- 認証・認可方針 ADR

### MANDATORY チェック項目

1. **ブランチ保護ルール**
   - main 直接 push 禁止: `allow_force_pushes.enabled` が false
   - PR レビュー必須: `required_pull_request_reviews` が存在
   - CI ステータスチェック必須: `required_status_checks` が存在
   - DO NOT: `enforce_admins.enabled` が false（管理者バイパスは原則 NG）

2. **秘密情報管理**
   - `.gitignore` に `.env` / `*.key` / `*.pem` の各パターンが含まれる
   - 過去 100 コミットを git log -p で grep して `aws_secret_access_key` / `api_key` / `password=` 等のキーワードが ヒットしない
   - DO NOT: ハードコードされた API キーがコミットに含まれる

3. **依存ライブラリの脆弱性監視**
   - Dependabot / Renovate の設定ファイルが存在し schedule が定義されている
   - lock file（pnpm-lock.yaml 等）が存在しコミットされている
   - DO NOT: lock file が `.gitignore` に含まれる

4. **認証・認可方針**
   - 認証方式（OAuth / Session / JWT 等）の ADR が存在する
   - 認可モデル（RBAC / ABAC / Policy）が明文化されている
   - 個人情報（PII）取扱い方針が文書化されている（PII を扱う場合のみ）

5. **セキュリティレビュープロセス**
   - PR レビューでのセキュリティチェック担当が CODEOWNERS 等で定義されている
   - 脆弱性発見時のエスカレーション手順がドキュメントに存在

### 重要度判定基準

- **Critical**: ブランチ保護なし・秘密情報のコミット履歴あり・PII 方針なし（PII 取扱い時）
- **Suggestion**: シークレットスキャナ追加（gitleaks 等）・SCA 強化
- **OK Point**: 多層防御が機能・CODEOWNERS とブランチ保護が整合

---

## 観点 5: ドキュメント基盤 — aidd-technical-writer

### レビュー対象

- `README.md`
- `CLAUDE.md` / `AGENTS.md`
- `docs/playbook/*.md`
- `docs/glossary.md`
- `aidd-framework/`
- `skills/aidd-create-adr/references/adr.md`

### MANDATORY チェック項目

1. **README の品質**
   - プロジェクト概要・セットアップ手順・主要コマンドの 3 セクションが存在する
   - セットアップ手順を最初から実行して 30 分以内に開発開始できる
   - DO NOT: README が「Hello World」レベル（10 行以下）

2. **AI エージェント指示（CLAUDE.md / AGENTS.md）**
   - プロジェクト固有のルール（規約・禁止事項・推奨パターン）が箇条書きで列挙されている
   - 「DO NOT」「MANDATORY」「ALWAYS」等の命令キーワードで具体指示が記述されている
   - `aidd-framework/` への参照が含まれる

3. **用語集（glossary）**
   - プロジェクト固有用語が 10 件以上定義されている（初期 Phase 完了時点での目安）
   - 多義語・略語の使い分けが明示されている

4. **プレイブック・ガイド**
   - `docs/playbook/` に最低 1 ファイル（はじめに・セットアップ・開発フロー等）が存在
   - 失敗パターン・FAQ・トラブルシューティングが最低 1 件記載されている

5. **テンプレート整備**
   - PR テンプレート（`.github/PULL_REQUEST_TEMPLATE.md`）が存在
   - Issue テンプレート（`.github/ISSUE_TEMPLATE/*.yml`）が epic・task・feedback 等で複数存在
   - ADR テンプレート（`skills/aidd-create-adr/references/adr.md`）が存在

### 重要度判定基準

- **Critical**: README 不在 or 10 行未満、AI エージェント指示なし、Issue テンプレートが 1 種類以下
- **Suggestion**: 図解追加・FAQ 拡充・サンプルコード追加
- **OK Point**: 新規参加者が迷子にならない構造・全テンプレートが充足

---

## 観点 6: Charter セクション 10 採用フレームワーク準拠 — aidd-architect

### レビュー対象

- `docs/PROJECT-CHARTER.md` セクション 10「業界標準フレームワーク採用方針」
- 本ゲート対象の成果物（プロジェクト初期構成（CHARTER / agents / mocks 等））

### MANDATORY チェック項目

1. **Charter セクション 10 の参照**
   - 本ゲートの成果物が Charter セクション 10 で「採用」と判定されたフレームワークに準拠しているか
   - 「不採用」と判定されたフレームワークが勝手に採用されていないか

2. **採用フレームワーク別チェック**
   - Conventional Commits 準拠で git log が記録されているか（採用時）
   - ADR (Michael Nygard) 形式で ADR が記録されているか（採用時・`docs/architecture/adr/`）
   - C4 Model 階層が明示されたアーキテクチャ図が存在するか（採用時）

3. **未決定方針の検出**
   - Charter セクション 10 が未作成の場合は `/aidd-charter` 実行を MANDATORY 推奨
   - 採用判定が古い場合は Charter 見直し（`/aidd-charter` 更新モード）を提案

### 重要度判定基準

- **Critical**: Charter 「不採用」フレームワークの無断採用 / Charter「採用」フレームワーク準拠違反
- **Suggestion**: 採用方針の見直し提案 / 準拠強化の追加チェック
- **OK Point**: Charter セクション 10 完全準拠

---

## 集約後の判定基準

`/aidd-review` が全 6 観点のレビュー結果を集約した後、以下で setup-complete 通過/不通過を判定する:

| 状態 | 条件 |
|------|------|
| **PASS** | 全観点で Critical が 0 件 |
| **FAIL** | Critical が 1 件以上残存 |

DO NOT: Critical を残したまま PASS とする。FAIL の場合は Critical を全て解消してから再レビューを実行する。
