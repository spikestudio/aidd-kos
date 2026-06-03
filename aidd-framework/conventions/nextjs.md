# Next.js 規約

Next.js + Vitest + Supertest + Playwright + Biome を使うプロジェクトに適用せよ。

---

## 1. ディレクトリ構成（この構造に従え）

```
src/
├── app/                    # App Router: ページ・レイアウト・ルートハンドラー
│   ├── (routes)/           # ルートグループ
│   ├── api/                # Route Handlers
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/                 # 汎用プリミティブ
│   └── features/           # ドメイン単位コンポーネント
├── lib/                    # ユーティリティ・ヘルパー
├── hooks/                  # カスタム React フック
└── types/                  # グローバルスコープ型定義

e2e/                        # Playwright E2E テスト
```

### DO / DO NOT

| DO | DO NOT |
|----|--------|
| `app/` にはページ・レイアウト・Route Handlers のみ置け | `app/` にビジネスロジックを持ち込むな |
| 汎用コンポーネントは `ui/`、ドメイン単位は `features/` に置け | プロジェクト固有構成を ADR に記録せずに変更するな |

---

## 2. テスト戦略

| レイヤー | ツール | 対象 | 配置 |
|---------|--------|------|------|
| ユニットテスト | Vitest | 関数・コンポーネント単体 | `*.test.ts(x)`（コロケーション） |
| 統合テスト | Supertest | API ルートの入出力 | `*.test.ts` |
| E2E テスト | Playwright | ユーザーシナリオ全体 | `e2e/` |

### カバレッジ基準

| レイヤー | 閾値 |
|---------|------|
| ユニットテスト | 80% 以上（行カバレッジ）|
| 統合テスト | 主要 API エンドポイントのハッピーパス + 主要エラーケース（400/401/403/404/500）を必ずカバー |
| E2E テスト | クリティカルなユーザーシナリオ（認証・主要業務フロー）のみ。網羅率より再現性を優先する |

### テストデータ方針

| 種別 | 使い分け |
|------|---------|
| インラインデータ | テスト関数内で完結する単純な値（文字列・数値）|
| Factory 関数 | 複数テストで共通する複雑なオブジェクト（`createUser()` 等）|
| Fixture ファイル | 外部 API レスポンス・大きな JSON のモック（`__fixtures__/` 配下に配置）|

DO NOT: テスト間でグローバル状態を共有するな。各テストは独立して実行可能にせよ。

### モック方針

- 外部 API・サードパーティサービス: モックする（Vitest の `vi.mock()` または MSW）
- DB: Vitest の `vi.mock()` または MSW でモックする（Supertest での統合テストでも実 DB への直接接続は原則禁止）
- 同一モジュール内の関数: モックしない（実装で直接テストする）

### MANDATORY

- 純粋関数・ユーティリティには必ずユニットテストを書け
- Supertest では DB・サードパーティを原則モックせよ。ハッピーパス + 主要エラーケースをカバーせよ
- E2E はクリティカルなシナリオのみカバーせよ（量より質）
- テスト間の依存を持たせるな（CI 並行実行前提）
- テスト名は AC-ID プレフィックス形式（`AC-F[N]-NN: テスト内容の説明`）で記述せよ（ADR-020）

---

## 3. 命名規約

| 対象 | 規約 | 例 |
|------|------|---|
| コンポーネントファイル | PascalCase | `UserCard.tsx` |
| ページ・レイアウト | Next.js 規約 | `page.tsx`, `layout.tsx` |
| フックファイル | camelCase（`use` プレフィックス） | `useUserData.ts` |
| ユーティリティ | camelCase | `formatDate.ts` |
| テストファイル | 対象 + `.test` | `UserCard.test.tsx` |

- コンポーネント名は PascalCase（例: `UserProfileCard`）
- 汎用コンポーネントは一般名詞（例: `Button`, `Modal`）
- 機能コンポーネントはドメイン + 役割（例: `OrderSummaryPanel`）
- イベントハンドラーは `handle` プレフィックス（例: `handleSubmit`）
- ブール型変数は `is` / `has` / `can` プレフィックス（例: `isLoading`, `hasError`）

---

## 4. Biome 設定

`biome.json` はリポジトリルートに配置し、全パッケージで共通設定を継承せよ。

```json
{
  "$schema": "https://biomejs.dev/schemas/1.x.x/schema.json",
  "organizeImports": { "enabled": true },
  "linter": { "enabled": true, "rules": { "recommended": true } },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": { "quoteStyle": "double", "trailingCommas": "all" }
  }
}
```

### MANDATORY

- `biome check` を lefthook（pre-commit）および CI に組み込め
- プロジェクト固有ルール追加は `biome.json` の `overrides` で管理し、ADR に理由を記録せよ

### DO NOT

- `// biome-ignore` による抑制を使うな。根本原因を修正せよ

---

## 5. エラーハンドリング

### 基本方針

- HTTP API は RFC 7807（Problem Details for HTTP APIs）準拠のレスポンスを返す
- `Content-Type: application/problem+json`
- 必須フィールド: `type` / `title` / `status`、任意フィールド: `detail` / `instance`

### エラー種別と HTTP ステータス

| エラー種別 | HTTP ステータス | 対応方針 |
|-----------|---------------|---------|
| バリデーションエラー | 400 / 422 | Zod スキーマで検証し、フィールド単位のエラー詳細を `detail` に含める |
| 認証エラー | 401 | セッション・トークン無効。再認証を促す |
| 認可エラー | 403 | リソースへのアクセス権なし。詳細は返さない |
| リソース不在 | 404 | 対象 ID をメッセージに含める |
| ビジネスルール違反 | 409 | 競合・制約違反の理由を `detail` に明記する |
| サーバーエラー | 500 | スタックトレースをクライアントに返さない。ログに記録する |

### DO / DO NOT

| DO | DO NOT |
|----|--------|
| Route Handler の外側で Next.js の `middleware` または共通ユーティリティでエラーを整形する | 各 Route Handler でバラバラにエラーレスポンスを組み立てる |
| `instanceof` でエラー型を判定し、既知エラーと未知エラーを分岐する | `catch (e: unknown)` をそのまま 500 で返す |

---

## 6. ロギング

### 基本方針

- 構造化ログ（JSON 形式）を使用する
- ログレベル: `error` / `warn` / `info` / `debug`
- サーバーサイド（Route Handler・Server Component）のみでログを出力する。クライアントコンポーネントではログを出力しない

### ログレベル定義

| レベル | 使用基準 | 例 |
|-------|---------|-----|
| `error` | 予期しない例外・サービス停止相当 | DB 接続エラー、外部 API 呼び出し失敗 |
| `warn` | 業務的に想定される異常・降格した処理 | レート制限到達、リトライ発生 |
| `info` | 主要なビジネスイベント | ユーザー登録完了、注文作成 |
| `debug` | 開発時の詳細トレース（本番は無効化） | 関数の入出力値 |

### 必須ログコンテキスト

リクエスト起因のログには以下を含める：

| フィールド | 説明 |
|-----------|------|
| `requestId` | トレーシング用 UUID（`x-request-id` ヘッダーから取得 or 生成） |
| `userId` | 認証済みユーザーの ID（未認証は `null`） |
| `path` | リクエストパス |
| `durationMs` | レスポンスタイム（ms）|

### DO / DO NOT

| DO | DO NOT |
|----|--------|
| `console.log` の代わりに採用ロギングライブラリ（pino 等）を使う | `console.log` をプロダクションコードに残す |
| 個人情報（メールアドレス・パスワード等）をログに出力しない | リクエストボディをそのままログに流す |
