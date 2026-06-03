# 推奨技術スタック

> **このファイルの責務: ツール選定の根拠管理。**
> 「どのツールを使うか」の意思決定と根拠を管理する。「どのバージョンを使うか」は `mise.toml` が担う。
>
> `/aidd-charter` の §10 技術スタック確定時のデフォルト値として使用し、
> `/aidd-setup-stack` はこのファイルを参照してセットアップを実行する。
> プロジェクト固有の要件でスタックを変更する場合は Charter §10 に理由付きで上書きする。
>
> **スコープ外:** ECR・AWS Secrets Manager・監視 SaaS 等のクラウド固有サービスはプロジェクト固有の選択とし、このファイルには含めない。

---

## フロントエンド（Web Frontend）

| カテゴリ | 推奨 | バージョン基準 |
|---------|------|-------------|
| 言語 | TypeScript | latest stable |
| フレームワーク | Next.js App Router | latest stable |
| UI ライブラリ | Spikestudio UIKit | latest stable |
| Linter / Formatter | Biome | latest stable |
| Unit test | Vitest | latest stable |
| E2E | Playwright | latest stable |
| API モック | MSW | latest stable |
| バリデーション | Zod | latest stable |
| ランタイム | Node.js LTS | LTS |

## BFF（Backend For Frontend）

| カテゴリ | 推奨 | バージョン基準 |
|---------|------|-------------|
| フレームワーク | Next.js App Router | latest stable |
| バリデーション | Zod | latest stable |
| Integration test | Supertest | latest stable |

## Web バックエンド

| カテゴリ | 推奨 | バージョン基準 |
|---------|------|-------------|
| 言語 | TypeScript | latest stable |
| フレームワーク | Hono | latest stable |
| API 契約（内部） | Hono RPC（`hc<typeof app>`） | — |
| API 契約（外部公開） | @hono/zod-openapi + openapi-typescript | latest stable |
| バリデーション | Zod | latest stable |
| Linter / Formatter | Biome | latest stable |
| Unit test | Vitest | latest stable |
| Integration test | Supertest | latest stable |

## バックエンド・バッチ（Go）

| カテゴリ | 推奨 | バージョン基準 |
|---------|------|-------------|
| 言語 | Go | latest stable |
| Linter | golangci-lint | latest stable |
| Formatter | gofmt + goimports | 標準（Go 同梱） |
| Unit test | go test + testify | latest stable |
| Integration test | testcontainers-go | latest stable |
| クエリ | sqlc + pgx | latest stable |

## データベース

| カテゴリ | 推奨 | バージョン基準 |
|---------|------|-------------|
| ORM（TS） | Prisma | latest stable |
| クエリビルダ（Go） | sqlc | latest stable |
| マイグレーション | Atlas | latest stable |
| Integration test DB | Testcontainers（PostgreSQL） | latest stable |

> **Atlas 選定理由:** Go + TS 横断でスキーマ管理を統一できる唯一のツール。golang-migrate は Go 側のみ、Drizzle migrate は TS 側のみのため棄却。

## モノレポ・パッケージ管理

| カテゴリ | 推奨 | バージョン基準 |
|---------|------|-------------|
| パッケージマネージャ | pnpm | latest stable |
| モノレポ管理 | Turborepo | latest stable |
| ツールバージョン管理 | mise | latest stable |

> **Go のタスク管理:** Turborepo のタスクグラフは TS レイヤーのみ対象。Go は Makefile または `mise tasks` で独立管理する。

## インフラ・CI/CD

| カテゴリ | 推奨 | バージョン基準 |
|---------|------|-------------|
| IaC | Terraform + Terragrunt | latest stable |
| コンテナオーケストレーション | Kubernetes | latest stable |
| ローカル K8s | Kind | latest stable |
| コンテナ | Docker + Docker Compose | latest stable |
| CI/CD | GitHub Actions | — |
| クラウド | AWS | — |
| 依存関係更新 | Dependabot | — |

## Observability

| カテゴリ | 推奨 | バージョン基準 |
|---------|------|-------------|
| ロギング（Node.js/Hono） | pino | latest stable |
| ロギング（Go） | zerolog | latest stable |
| トレーシング | OpenTelemetry SDK | latest stable |
| トレースバックエンド | Grafana Tempo | latest stable |
| メトリクス | Prometheus + Grafana | latest stable |
| ログ集約 | Loki | latest stable |
| ローカル展開 | Grafana Stack（Helm on Kind） | latest stable |

---

## 設定ファイルの方針

- **ローカルに設定ファイルテンプレートを持たない。** フレームワークが静的テンプレートを配布するアプローチはツールのバージョンアップで乖離が生じるため採用しない
- **利用バージョンは常に最新安定版。** `mise` でインストールし、そのバージョンの公式推奨設定または業界標準を都度取得して生成する
- **設定ファイルには取得元 URL・対象バージョン・取得日をヘッダに記録する。** 将来の更新時に何を参照して生成したかを追跡可能にする
- **できる限り厳格な設定を採用する。** 基本の推奨設定（recommended）にとどまらず、strictest オプション・静的解析・スコアリングツールを積極的に有効化する。設定を緩めた場合は理由をコメントに記録する

MANDATORY: `/aidd-setup-stack` 実行時、設定ファイルは `/aidd-research` で最新の公式推奨設定を取得して生成する。記憶・推測で設定値・ルール名・オプション名を記述しない。
