# PROJECT CHARTER — aidd-kos (Agentic Knowledge OS)

| 項目 | 内容 |
|------|------|
| ステータス | ドラフト |
| 日付 | 2026-06-03 |

## 1. ビジョン

`uvx aidd-kos install` の 1 コマンドで、AI エージェントが開発プロジェクトの「コード・設計書・業務文脈」を
横断的に理解・検索できるナレッジ OS が即座に稼働する。LightRAG・CodeGraph 等の個別ツールを
個別にセットアップ・運用する手間はない。AI Agent は単一の MCP サーバーが提供するナレッジツール群を
自律的に組み合わせながら、開発を最速・最大効率で推進できる。

## 2. ビジネスゴール

| # | ゴール | 測定指標 |
|---|--------|---------|
| 1 | AI Agent が自然言語でプロジェクト知識を横断検索できる | query P95 応答 < 2秒（1万ドキュメント規模）、関連ドキュメントの適合率 > 80% |
| 2 | `aidd-kos` 導入から MCP 稼働まで 10 分以内 | 100 ドキュメント以下で `uvx aidd-kos install` → Claude Code 再起動 → MCP 疎通確認の所要時間（インデックス構築を除く） |
| 3 | AI Agent が単一 MCP サーバー内のツールを自律的に使い分けて開発を推進できる | Agent が 1 タスク内で複数ナレッジツールを組み合わせて呼び出し、目的を達成できること（E2E テストで検証） |
| 4 | `aidd-kos` のバージョンアップだけで、Agent が使えるナレッジエンジンが増え・改善される | 新バージョン導入後に既存 MCP 接続設定を変えずに新ツールが利用可能になること |

## 3. 対象ユーザー / ペルソナ

<!-- aidd-kos は AI Agent を直接の主ユーザーとして設計する。
     人間開発者は「インストール・設定・インデックス投入」を行うオペレーター。
     AI Agent は「MCP ツールを自律的に呼び出す」能動的ユーザー。
     この非対称性がすべての設計判断の基準となる。 -->

| ペルソナ | 役割 | 主な目的 |
|---------|------|---------|
| **Primary**: AI Agent（Claude Code / Cursor 等） | MCP ツールを自律的に呼び出す AI コーディングエージェント | 開発タスクに必要な知識（設計書・ADR・コード構造・議事録）を自力で検索・推論し、開発を最速で推進したい |
| **Secondary**: AI 駆動開発エンジニア（オペレーター）| aidd-kos を導入・設定し、AI Agent に最善の知識基盤を提供する人間開発者 | ツール選定・設定を意識せず `aidd-kos` を入れるだけで Agent が動く状態にしたい |
| **Tertiary**: DX 推進担当者 / EM | チームへの AI エージェント展開を推進するマネージャー | 組織の開発知識を AI が活用できる形で蓄積・管理したい（Phase 2 マルチプロジェクト対応後に本格利用） |
| **Negative**: 従来型開発者 | AI ツールを使用せず、ドキュメントを手動検索する開発者 | このプロダクトの価値を見出しにくい |

## 4. Phase ロードマップ

| Phase | 名称 | スコープ概要 | 状態 |
|-------|------|------------|------|
| Phase 1 | Core MVP | **LightRAG（ドキュメント検索）+ CodeGraph（コード検索）を単一 MCP サーバーで公開**。`uvx aidd-kos install` 1 コマンドで対象プロジェクトへの導入完結（.lightrag/ + .codegraph/ 配置・MCP 登録・embedded 起動）。CLI（install / index / status）+ テスト・ドキュメント整備 | 一部実装完了。CLI・embedded 起動・install フロー・CodeGraph MCP 公開は未実装 |
| Phase 2 | Operational Excellence | インデックス自動同期・差分更新・lefthook 連携・ステータス可視化・エラーリカバリーなど、**運用を支える機能群を実装**。インストール後の日常利用で人間の管理コストをゼロに近づける | 着手中 |
| Phase 3 | Multi-Engine | Phase 1 の 2 エンジンを基盤に、**第 3・第 4 のナレッジエンジンを追加実装**（ADR 特化検索・外部システム連携等）。Agent が使い分けて推論できる状態をさらに拡充 | 未着手 |
| Phase 4 | Ecosystem | 外部システム連携エンジン（GitHub Issues / Confluence / Jira 等）・Embedding プロバイダー拡充・精度改善サイクルの確立 | 未着手 |

## 4.1 スコープ外

以下はこのプロジェクトの対象外とする。

- Web UI / ダッシュボード（Phase 3 以降で検討）
- マルチユーザー SaaS 化
- モバイルアプリ

## 5. 非機能要件（6 分類）

<!-- IPA 非機能要求グレード準拠。定量目標を必須とし「速い」「安全」等の形容詞のみは禁止 -->

| 分類 | 定量目標 | 計測方法 | 優先度 |
|------|---------|---------|--------|
| **可用性**（稼働率, RTO, RPO） | ローカルツールのため SLO なし。障害時は 3 秒以内に stderr へエラーコードと対処方法を出力 | 手動テスト（startup failure シナリオ） | MUST |
| **性能・拡張性**（応答時間, スループット） | query P95 < 2秒（1万ドキュメント）。AI Agent は 1 タスクで 20〜50 回連続呼び出しを想定：累積待機 = 2秒 × 50回 = 100秒以内。インデックス構築 < 30分（1万ドキュメント） | 手動計測（将来的に pytest-benchmark 導入） | MUST |
| **運用・保守性**（監視, 障害検知） | kos_status でインデックス状態を即時確認可能。ログは stdout に出力（エラーは stderr）。LightRAG サーバー未起動時は接続エラーを明示 | 動作確認 | MUST |
| **移行性**（移行量, ダウンタイム） | N/A（新規開発、既存システムからの移行なし） | — | N/A |
| **セキュリティ**（認証, 暗号化, 監査） | API キー（OPENAI_API_KEY / LIGHTRAG_API_KEY 等）を .env で管理しログ出力禁止。LightRAG REST API は HTTP（localhost のみ。外部公開環境では TLS 必須とし README に警告を記載する） | コードレビュー / .env 検査 | MUST |
| **環境・エコロジー** | N/A（ローカル実行ツール、クラウド環境なし） | — | N/A |

## 6. 制約事項

- **技術的制約**: LightRAG は OpenAI API（Embedding / LLM）に依存。API コスト・レート制限が制約となる
- **配布制約**: PyPI 経由（Phase 1 Core MVP で対応済み）。`uvx aidd-kos@latest` でインストール。GitHub Release をトリガーに自動公開
- **ビジネス制約**: スパイクスタジオの内部ツールとして開始し、OSS として公開（MIT ライセンス）
- **リソース制約**: ソロ開発（1名）。Phase 1 MVP を優先

## 7. 前提条件

- ユーザーが有効な OpenAI API キーを所持していること
- Python 3.10 以上 + uv がインストール済みであること
- ポート 9621 は Epic #38 以降不要（LightRAG in-process 化。ADR-004）

## 8. リスク

| リスク | 影響度 | 発生確率 | 対策 |
|--------|-------|---------|------|
| LightRAG API の破壊的変更 | 高 | 中 | バージョンを pyproject.toml で固定（`>=1.5.0`）、CHANGELOG 追跡 |
| OpenAI API コスト超過 | 中 | 低 | インデックス構築時のトークン使用量を事前表示、.lightrag-ignore で除外設定 |
| インデックス精度が実用に達しない | 高 | 低 | Phase 1 で精度評価テストを含める、クエリモード（hybrid / local / global）選択機能 |
| MCP プロトコルの仕様変更 | 中 | 低 | FastMCP バージョン固定、MCP spec 追跡 |
| Embedding プロバイダー依存（OpenAI のみ） | 中 | 中 | Phase 3 で LightRAG の複数バックエンドサポートを活用して選択肢を拡充（ADR 候補） |

## 9. アーキテクチャ方針

<!-- 設計の核心: aidd-kos は「ワンパッケージで最良のナレッジ基盤を提供する」Knowledge OS。
     LightRAG・CodeGraph 等の個別ツールを個別にセットアップ・運用する手間をオペレーターから取り除く。
     Agent はどのエンジンを使っているかを認識した上で自律的に選択・呼び出す（Agentic RAG）。
     「どう組み合わせるか」は Agent が判断し、「何を用意して動かすか」は aidd-kos が担う。 -->

| 項目 | 方針 |
|------|------|
| **MCP Aggregator** | aidd-kos の MCP Server は **MCP Aggregator** として実装する。LightRAG（embedded サブプロセス）と CodeGraph（npx プロセス proxy）のツールを単一の MCP エンドポイントに束ね、AI Agent には `aidd-kos` 1 本だけを登録すれば全ナレッジツールが使える状態にする。将来エンジンが増えても AI Agent 側の設定変更は不要 |
| 配布・インストール | GitHub Release 経由。対象プロジェクトのルートで `uvx aidd-kos install` の 1 コマンドで完結。~/.claude/settings.json へ MCP 登録・.lightrag/ 初期化・.gitignore 更新をすべて自動実行する |
| ストレージ配置 | `.lightrag/`（ドキュメント知識）・`.codegraph/`（コード知識）はともに**対象プロジェクトのルート**に配置する。aidd-kos 自身のディレクトリには保存しない |
| LightRAG 起動（embedded） | LightRAG は MCP サーバーのサブプロセスとして起動する。Claude Code が MCP サーバーを起動すると LightRAG も自動起動し、MCP サーバーが停止すると自動終了する。オペレーターはサーバー起動を意識しない |
| 構成（Phase 1） | `uvx aidd-kos install` → MCP Server（FastMCP）起動 → LightRAG サブプロセス自動起動（localhost:9621）→ .lightrag/（対象プロジェクト内） |
| 構成（Phase 2〜） | 単一 MCP サーバーが複数のナレッジエンジンをツールとして公開。どのエンジンを搭載するかは aidd-kos が企画・実装する。ユーザーはバージョンアップするだけで最新のエンジン群を得る |
| MCP ツール命名 | エンジン名 prefix を付ける（`lightrag_*`・`codegraph_*`）。Agent はどのエンジンを呼んでいるか認識した上で判断する |
| ツール設計原則 | 各 MCP ツールに「いつ使うか（`when_to_use`）」「何を返すか」を明示する。Agent が迷わず選べる記述が品質基準 |
| エンジン追加方針 | 新エンジンは aidd-kos のリリースとして提供する。ユーザー側の設定変更・追加作業は発生しない |
| CLI（オペレーター向け） | `aidd-kos <command>` がオペレーター（人間開発者）の唯一の操作窓口。install / index / status / update を提供。LightRAG の直接操作は不要（embedded のため） |
| データフロー（Phase 1） | Claude Code → MCP stdio → FastMCP server（LightRAG embedded）→ .lightrag/（対象プロジェクト） |
| データフロー（Phase 2〜） | Claude Code → MCP stdio → FastMCP server → Agent が選んだツール → {LightRAG, CodeGraph, ...} |
| 外部連携 | Phase 1: OpenAI API のみ。Phase 2〜: Embedding プロバイダー選択肢を aidd-kos が実装・提供 |

## 10. 技術スタック

<!-- 確定値。「未定」なし。/aidd-setup-stack の前提条件を満たす -->

| カテゴリ | 採用技術 / バージョン | 選定理由 |
|---------|---------------------|---------|
| 言語 | Python 3.10+ | LightRAG / FastMCP が Python。型ヒント対応・async サポート充実 |
| Doc Intelligence | LightRAG (lightrag-hku) 1.5+ | Vector + Graph の Dual-Level Retrieval。更新性能・検索速度が AI Agent 用途に最適 |
| Code Intelligence | CodeGraph (@colbymchenry/codegraph) | AST・呼び出しグラフ・シンボル検索。npx で実行、MCP server として AI Agent に公開 |
| MCP フレームワーク | FastMCP 2.0+ | Python ネイティブ MCP サーバー実装。最小コードで MCP ツール公開可能 |
| Doc ストレージ | .lightrag/（対象プロジェクト内） | グラフ + ベクトルをローカルファイルに保存。DB サーバー不要 |
| Code ストレージ | .codegraph/（対象プロジェクト内） | コード AST インデックスをローカルに保存 |
| 配布 | GitHub Release + uvx | `uvx aidd-kos install` 1 コマンドでインストール完結 |
| インフラ | ローカル実行 | 開発者ツールとして導入摩擦を最小化 |
| CI/CD | GitHub Actions | aidd-fw 標準 |
| パッケージマネージャー | uv | Python 高速パッケージマネージャー。仮想環境管理含む |
| ツールバージョン管理 | mise | aidd-fw 標準（固定）|
| CLI フレームワーク | Typer | Python ネイティブ、型ヒントベースで Click より記述量が少ない。`aidd-kos` コマンド実装に使用 |
| タスクランナー | Task (Taskfile.yml) | 開発者向け内部タスク（CI 等）。ユーザー向け操作は CLI に移管 |

## 11. 関連ドキュメント

- [README.md](../README.md): クイックスタートガイド
- [docs/architecture/](./architecture/): アーキテクチャ設計
- [docs/glossary.md](./glossary.md): 用語集

## 12. 業界標準フレームワーク採用方針

<!-- aidd-fw 標準: framework-adoption.md の固定採用ロジックに従う。動的選定禁止 -->

### 常時採用（全プロジェクト共通）

| カテゴリ | 採用フレームワーク | 状態 |
|---------|-----------------|------|
| 品質モデル全体 | ISO/IEC 25010 | 採用 |
| ストーリー記述形式 | As a / I want to / So that (Mike Cohn) | 採用 |
| ストーリー粒度・分割 | INVEST + Story Splitting Patterns | 採用 |
| ペルソナ手法 | Cooper Persona (Primary/Secondary/Negative) | 採用 |
| ドメイン設計 | DDD (Eric Evans / Vaughn Vernon) | 採用 |
| アーキテクチャ図 | C4 Model (Simon Brown) | 採用 |
| 設計判断記録 | ADR (Michael Nygard) | 採用 |
| Performance/Availability 指標 | Google SRE (SLI/SLO/SLA + Error Budget) | 採用 |
| RTO/RPO | BCP/DR 用語標準 | 採用 |
| Security 脅威モデリング | STRIDE | 採用（OPENAI_API_KEY 等の認証情報を扱うため不採用条件に非該当） |
| Security 暗号化 | TLS 1.2+ / AES-256 | 採用 |
| Operability 運用指標 | DORA 4 メトリクス | 採用（GitHub Actions CI で計測。計測インフラは /aidd-setup-stack で整備） |
| コミットメッセージ | Conventional Commits | 採用 |
| バージョン管理 | Semantic Versioning (SemVer 2.0) | 採用 |

### 条件付き採用（採用条件による判定）

| カテゴリ | 採用フレームワーク | 状態 | 根拠 |
|---------|-----------------|------|------|
| API 仕様記述 | OpenAPI 3.0+ | 不採用 | MCP protocol のため標準 REST API 仕様書不要 |
| API エラー形式 | RFC 7807 (Problem Details) | 不採用 | REST API 提供なし（MCP protocol 準拠） |
| HTTP セマンティクス | RFC 9110 | 不採用 | REST API 提供なし |
| Scalability | 水平スケール優先 | 不採用 | ローカルツール。スケールアウト設計不要 |
| Security 認証 | OAuth 2.0 / OIDC | 不採用 | 認証不要（ローカルツール、API キーは .env 管理） |
| Security 既知リスク (Web) | OWASP Top 10（最新版） | 不採用 | Web UI なし |
| Security 既知リスク (API) | OWASP API Security Top 10（最新版） | 不採用 | 外部公開 API なし |
| Maintainability テスト | Test Pyramid (Mike Cohn) | 採用 | Python コード生成プロジェクト |
| Maintainability コード品質 | SOLID 原則 | 採用 | Python / OOP |
| Observability | Three Pillars + OpenTelemetry | 不採用 | ローカルツール / Phase 1 MVP。Phase 2 以降で検討 |
| Compliance 基盤 | NIST CSF | 不採用 | 内部ツール / 小規模 OSS、規制対象外 |
| Operability デプロイ戦略 | Progressive Delivery (Canary / Blue-Green / Rolling) | 不採用 | PyPI パッケージリリース形式。Canary/Blue-Green 不要 |
| CLI 設計 | POSIX.1 / GNU CLI / clig.dev / 12 Factor CLI / XDG Base Directory | 採用 | scripts/ 配下の CLI ツール・task コマンド |
| UI コンポーネント参照 | catalog.json (spikestudio UIKit) | 不採用 | UI なし |
| UI アクセシビリティ | WCAG 2.1（最新版） | 不採用 | UI なし |
| UI 使いやすさ | Nielsen 10 Usability Heuristics | 不採用 | UI なし |
| UI フォーム設計 | Form Design Patterns (Adam Silver) | 不採用 | UI なし |
| 依存性管理 | SBOM (CycloneDX / SPDX) | 採用 | MIT ライセンスで OSS 公開 |
| ライセンス記述 | SPDX License List | 採用 | OSS 配布・MIT ライセンス |
| 国際化 | ICU MessageFormat + Unicode CLDR | 不採用 | 単一言語（日本語 / 英語混在だが i18n フレームワーク不要） |

### 規制（個別採用）

| 規制 | 状態 | 根拠 |
|------|------|------|
| GDPR | 不採用 | EU 個人情報なし |
| CCPA | 不採用 | カリフォルニア展開なし |
| HIPAA | 不採用 | 医療データなし |
| PCI-DSS | 不採用 | 決済なし |
| SOC 2 | 不採用 | B2B SaaS でない |
| ISO 27001 | 不採用 | 任意採用・現時点では採用しない |

## Phase 定義

### Operational Excellence（Milestone #2）

| 項目 | 内容 |
|------|------|
| ゴール | aidd-kos の運用を支える機能群を実装し、インストール後の日常利用で人間の管理コストがゼロに近い状態 |
| スコープ | インデックス自動同期・差分更新・lefthook 連携・ステータス可視化・エラーリカバリー・運用 CLI 拡充 |
| 成功条件 | Phase 内の全 Epic が完了し、インストール済みプロジェクトで追加設定なしに運用機能が稼働している |
| 期限 | 未定 |
| 対応 Epic | #25（[1] インデックス差分更新）・#26（[2] 自動同期トリガー）・#27（[3] ステータス & エラー可視化）|

### Core MVP（Milestone #1）

| 項目 | 内容 |
|------|------|
| ゴール | `uvx aidd-kos install` の 1 コマンドで LightRAG + CodeGraph が単一 MCP エンドポイントから稼働し、AI Agent が `lightrag_*` / `codegraph_*` ツールを即座に使える状態 |
| スコープ | MCP Aggregator 実装・LightRAG embedded 起動・対象プロジェクトへのストレージ配置・aidd-kos CLI（install / index / status）|
| 成功条件 | `uvx aidd-kos install` → Claude Code 再起動 → `lightrag_query` / `codegraph_explore` が応答する（E2E テスト PASS）|
| 期限 | 2026-07-31 |
| 対応 Epic | #4（[1] aidd-kos CLI & Install フロー）・#2（[2] MCP Aggregator 実装）・#3（[3] Embedded 起動 & ストレージ移動）・#17（[5] PyPI 公開・リリースパイプライン整備）|
