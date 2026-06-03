# PROJECT CHARTER — aidd-kos (Agentic Knowledge OS)

| 項目 | 内容 |
|------|------|
| ステータス | ドラフト |
| 日付 | 2026-06-03 |

## 1. ビジョン

AI エージェントが開発プロジェクトの「コード・設計書・業務文脈」を横断的に理解・検索できるナレッジ OS を提供し、AI 駆動開発の生産性を飛躍的に向上させる。

## 2. ビジネスゴール

| # | ゴール | 測定指標 |
|---|--------|---------|
| 1 | AI Agent が自然言語でプロジェクトドキュメントを検索できる | query_documents P95 応答 < 2秒（1万ドキュメント規模） |
| 2 | MCP 接続確認まで 10 分以内（インデックス構築を除く） | 100 ドキュメント以下のプロジェクトで `uv sync` → `task server:start` → MCP 疎通確認の所要時間 |
| 3 | 主要 AI エージェント（Claude Code / Claude Desktop）との MCP 統合を実現する | E2E テストで query_documents を呼び出し関連ドキュメントが返却されること |

## 3. 対象ユーザー / ペルソナ

| ペルソナ | 役割 | 主な目的 |
|---------|------|---------|
| **Primary**: AI 駆動開発エンジニア | Claude Code / Cursor 等を日常利用するソフトウェアエンジニア | プロジェクトの設計書・ADR・議事録を AI Agent 経由で即座に検索・参照したい |
| **Secondary**: DX 推進担当者 / EM | チームへの AI エージェント展開を推進するエンジニアリングマネージャー | 組織の開発知識を AI が活用できる形で蓄積・管理したい（Phase 2 マルチプロジェクト対応後に本格利用） |
| **Negative**: 従来型開発者 | AI ツールを使用せず、ドキュメントを手動検索する開発者 | このプロダクトの価値を見出しにくい |

## 4. Phase ロードマップ

| Phase | 名称 | スコープ概要 | 状態 |
|-------|------|------------|------|
| Phase 1 | Core MVP | LightRAG インデックス + MCP サーバー基本実装（query_documents / get_status / list_documents）+ テスト・ドキュメント整備 | 実装完了、MVP 品質担保中 |
| Phase 2 | Agent Harness | クエリ精度向上・マルチプロジェクト対応・AI Agent ハーネス機能強化（Secondary ペルソナ対応） | 未着手 |
| Phase 3 | Ecosystem | CodeGraph 統合・外部システム連携（GitHub Issues / ADR / Confluence / Jira）・Embedding プロバイダー拡充 | 未着手 |

## 4.1 スコープ外

以下はこのプロジェクトの対象外とする。

- Web UI / ダッシュボード（Phase 3 以降で検討）
- GraphRAG / Neo4j 統合（Phase 3 以降で検討）
- マルチユーザー SaaS 化
- モバイルアプリ

## 5. 非機能要件（6 分類）

<!-- IPA 非機能要求グレード準拠。定量目標を必須とし「速い」「安全」等の形容詞のみは禁止 -->

| 分類 | 定量目標 | 計測方法 | 優先度 |
|------|---------|---------|--------|
| **可用性**（稼働率, RTO, RPO） | ローカルツールのため SLO なし。障害時は 3 秒以内に stderr へエラーコードと対処方法を出力 | 手動テスト（startup failure シナリオ） | MUST |
| **性能・拡張性**（応答時間, スループット） | query_documents P95 < 2秒（1万ドキュメント）、インデックス構築 < 30分（1万ドキュメント） | 手動計測（将来的に pytest-benchmark 導入） | MUST |
| **運用・保守性**（監視, 障害検知） | get_status でインデックス状態を即時確認可能。ログは stdout に出力（エラーは stderr）。LightRAG サーバー未起動時は接続エラーを明示 | 動作確認 | MUST |
| **移行性**（移行量, ダウンタイム） | N/A（新規開発、既存システムからの移行なし） | — | N/A |
| **セキュリティ**（認証, 暗号化, 監査） | API キー（OPENAI_API_KEY / LIGHTRAG_API_KEY 等）を .env で管理しログ出力禁止。LightRAG REST API は HTTP（localhost のみ。外部公開環境では TLS 必須とし README に警告を記載する） | コードレビュー / .env 検査 | MUST |
| **環境・エコロジー** | N/A（ローカル実行ツール、クラウド環境なし） | — | N/A |

## 6. 制約事項

- **技術的制約**: LightRAG は OpenAI API（Embedding / LLM）に依存。API コスト・レート制限が制約となる。LightRAG デフォルトポート 9621（`LIGHTRAG_URL` 環境変数で上書き可能）
- **ビジネス制約**: スパイクスタジオの内部ツールとして開始し、OSS として公開（MIT ライセンス）
- **リソース制約**: ソロ開発（1名）。Phase 1 MVP を優先

## 7. 前提条件

- ユーザーが有効な OpenAI API キーを所持していること
- Python 3.10 以上がインストール済みであること
- LightRAG サーバーがローカルで起動可能であること（ポート 9621 が使用可能）

## 8. リスク

| リスク | 影響度 | 発生確率 | 対策 |
|--------|-------|---------|------|
| LightRAG API の破壊的変更 | 高 | 中 | バージョンを pyproject.toml で固定（`>=1.5.0`）、CHANGELOG 追跡 |
| OpenAI API コスト超過 | 中 | 低 | インデックス構築時のトークン使用量を事前表示、.lightrag-ignore で除外設定 |
| インデックス精度が実用に達しない | 高 | 低 | Phase 1 で精度評価テストを含める、クエリモード（hybrid / local / global）選択機能 |
| MCP プロトコルの仕様変更 | 中 | 低 | FastMCP バージョン固定、MCP spec 追跡 |
| Embedding プロバイダー依存（OpenAI のみ） | 中 | 中 | Phase 3 で LightRAG の複数バックエンドサポートを活用して選択肢を拡充（ADR 候補） |

## 9. アーキテクチャ方針

| 項目 | 方針 |
|------|------|
| 構成 | ローカル実行：MCP サーバー（FastMCP）+ LightRAG REST API（localhost:9621）+ .lightrag/（ローカル graph/vector DB） |
| パターン | シングルサービス + ローカルファイルストレージ。マイクロサービス化はスコープ外 |
| データフロー | Claude Code → MCP stdio → FastMCP server → HTTP → LightRAG API → .lightrag/ |
| 外部連携 | OpenAI API（Embedding / LLM）のみ。他外部 API は Phase 3 で検討 |

## 10. 技術スタック

<!-- 確定値。「未定」なし。/aidd-setup-stack の前提条件を満たす -->

| カテゴリ | 採用技術 / バージョン | 選定理由 |
|---------|---------------------|---------|
| 言語 | Python 3.10+ | LightRAG / FastMCP が Python。型ヒント対応・async サポート充実 |
| RAG フレームワーク | LightRAG (lightrag-hku) 1.5+ | Vector + Graph の Dual-Level Retrieval。更新性能・検索速度が AI Agent 用途に最適 |
| MCP フレームワーク | FastMCP 2.0+ | Python ネイティブ MCP サーバー実装。最小コードで MCP ツール公開可能 |
| DB / ストレージ | LightRAG ローカルストレージ（.lightrag/） | グラフ + ベクトルをローカルファイルに保存。DB サーバー不要 |
| インフラ | ローカル実行（Docker オプション） | 開発者ツールとして導入摩擦を最小化 |
| CI/CD | GitHub Actions | aidd-fw 標準 |
| パッケージマネージャー | uv | Python 高速パッケージマネージャー。仮想環境管理含む |
| ツールバージョン管理 | mise | aidd-fw 標準（固定）|
| タスクランナー | Task (Taskfile.yml) | 既存プロジェクトで採用済み |

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
