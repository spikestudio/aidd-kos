# 用語集

<!-- aidd-glossary によって管理。手動編集可。追加・更新時は /aidd-glossary を実行する -->

最終更新: 2026-06-04

## 用語一覧

### Agentic Knowledge OS (aidd-kos)

**定義**: AI エージェントが開発プロジェクトの「コード・設計書・業務文脈」を横断的に理解・検索できるナレッジ基盤。LightRAG ナレッジグラフと MCP サーバーを組み合わせたローカル実行ツール。

**用例**: aidd-kos を MCP 経由で Claude Code に接続することで、AI エージェントがプロジェクトの設計書・ADR・議事録を自然言語で即座に検索できる。

---

### AI 駆動開発エンジニア

**定義**: Claude Code / Cursor 等の AI ツールを日常利用するソフトウェアエンジニアを指す Primary ペルソナ。プロジェクトの設計書や ADR を AI Agent 経由で即座に検索・参照することを主な目的とする。

**用例**: AI 駆動開発エンジニアは aidd-kos を介してプロジェクトの過去の意思決定を自然言語で検索し、実装方針を素早く確認する。

---

### LightRAG

**定義**: Vector（ベクトル検索）と Graph（グラフ検索）を組み合わせた Dual-Level Retrieval を実現する RAG フレームワーク（lightrag-hku）。更新性能と検索速度が AI Agent 用途に最適化されている。

**用例**: LightRAG はドキュメントを Entity と Relation に分解してナレッジグラフに格納し、lightrag_query 実行時に Vector と Graph の両経路で関連情報を取得する。

---

### Dual-Level Retrieval

**定義**: Vector 検索（意味的類似性）とナレッジグラフ（Entity-Relation 構造）の 2 つの検索経路を組み合わせた LightRAG 固有の検索方式。単一手法より検索精度と網羅性が高い。

**用例**: Dual-Level Retrieval により、キーワードが直接一致しない場合でも Entity 間の関係を辿って関連ドキュメントを取得できる。

---

### MCP (Model Context Protocol)

**定義**: AI エージェント（Claude Code / Claude Desktop 等）が外部ツールやデータソースと通信するための標準プロトコル。aidd-kos では stdio 経由で FastMCP サーバーへ接続し、ナレッジ検索ツールを提供する。

**用例**: Claude Code は MCP stdio を経由して aidd-kos の lightrag_query ツールを呼び出し、プロジェクトドキュメントを検索する。

---

### FastMCP

**定義**: Python ネイティブの MCP サーバー実装フレームワーク（バージョン 2.0+）。最小限のコードで MCP ツールを公開でき、aidd-kos の MCP インターフェース層として採用されている。

**用例**: FastMCP を使用することで、lightrag_query / lightrag_list / kos_status の 3 つの MCP ツールを簡潔に定義・公開している。

---

### Agent Harness

**定義**: AI Agent が aidd-kos を活用するための高度な機能群。Phase 2 で強化予定であり、クエリ精度向上・マルチプロジェクト対応・Secondary ペルソナ対応を含む。

**用例**: Agent Harness が整備されることで、DX 推進担当者が組織横断の複数プロジェクトの知識を AI Agent 経由で統合管理できるようになる。

---

### ナレッジグラフ (Knowledge Graph)

**定義**: ドキュメントから抽出した Entity（エンティティ）と Relation（関係）をグラフ構造で表現したデータ構造。LightRAG が .lightrag/ ディレクトリにローカル保存する。

**用例**: aidd-kos はドキュメントをインデックス構築時にナレッジグラフへ変換し、Dual-Level Retrieval の Graph 経路で活用する。

---

### Entity（エンティティ）

**定義**: LightRAG がドキュメントから抽出する知識の基本単位（概念・人物・技術名・機能名等）。ナレッジグラフのノードとして格納される。

**用例**: "FastMCP"・"lightrag_query"・"Dual-Level Retrieval" はそれぞれ Entity として抽出され、相互の Relation とともにナレッジグラフに保存される。

---

### Relation（関係）

**定義**: LightRAG がドキュメントから抽出する Entity 間の意味的な結びつき。ナレッジグラフのエッジとして格納され、Entity 間の文脈を保持する。

**用例**: "FastMCP が MCP ツールを公開する" という Relation により、lightrag_query と FastMCP の依存関係をグラフ検索で辿ることができる。

---

### lightrag_query

**定義**: aidd-kos が提供する MCP ツール。自然言語クエリで LightRAG の Dual-Level Retrieval を使い
関連ドキュメントを返却する。P95 応答時間 2 秒未満（1 万ドキュメント規模）が目標値。
旧名称: `query_documents`（Epic #2 で改名）。

**用例**: AI Agent が lightrag_query を呼び出し「このプロジェクトの認証方式は？」と問い合わせると、関連する ADR や設計書が返却される。

---

### lightrag_list

**定義**: aidd-kos が提供する MCP ツール。インデックスに登録済みのドキュメント一覧を返却する。
旧名称: `list_documents`（Epic #2 で改名）。

**用例**: lightrag_list を実行してインデックス対象のドキュメントが正しく登録されているか確認した上で、lightrag_query の検索精度を評価する。

---

### kos_status

**定義**: aidd-kos が提供する MCP ツール。LightRAG・CodeGraph 両エンジンの状態（ready/unavailable/indexing）・
インデックス日時・利用可能ツール一覧を統合して返却する。旧名称: `get_status`（Epic #2 で改名）。

**用例**: kos_status を呼び出すことで、全ナレッジエンジンの稼働状態と利用可能ツールを MCP 経由で即座に確認できる。

---

### QUERY_TIMEOUT

**定義**: aidd-kos のエラーコード（ADR-001 準拠: `{COMPONENT}_{ERROR_TYPE}` 形式）。lightrag_query が `LIGHTRAG_QUERY_TIMEOUT_MS`（デフォルト 5000ms）以内に応答しなかった場合に返却される。

**用例**: 大規模インデックスでのクエリが 5 秒を超えた場合、AI Agent は `QUERY_TIMEOUT: クエリがタイムアウトしました` を受け取り、`LIGHTRAG_QUERY_TIMEOUT_MS` の調整を案内される。

---

### .lightrag/

**定義**: LightRAG がグラフデータとベクトルデータをローカルファイルとして保存するディレクトリ。対象プロジェクトのルートディレクトリ直下（`{target-project}/.lightrag/`）に配置される。DB サーバーを不要とし、ローカル実行ツールとしての導入摩擦を最小化する設計。

**用例**: .lightrag/ ディレクトリを別のマシンにコピーすることで、インデックスを再構築せずにナレッジグラフを移行できる。

---

### クエリモード

**定義**: LightRAG が提供する検索戦略の選択肢。hybrid（Vector + Graph の統合）・local（近傍の Entity を優先）・global（グラフ全体を対象）の 3 モードがある。検索精度とユースケースに応じて選択する。

**用例**: 特定の技術仕様を深掘りする場合は local モード、プロジェクト全体の方針を把握したい場合は global モードを使用する。

---

### .lightrag-ignore

**定義**: インデックス構築対象から除外するファイル・ディレクトリを指定する設定ファイル。.gitignore と同様の書式を想定。OpenAI API コスト管理のために不要ファイルを除外するために使用する。

**用例**: .lightrag-ignore に `node_modules/` や `*.log` を記載することで、インデックス構築時のトークン使用量とコストを削減できる。

---

### DX 推進担当者 / EM

**定義**: チームへの AI エージェント展開を推進するエンジニアリングマネージャーを指す Secondary ペルソナ。組織の開発知識を AI が活用できる形で蓄積・管理することを主な目的とする（Phase 2 マルチプロジェクト対応後に本格利用）。

**用例**: DX 推進担当者 / EM は Phase 2 の Agent Harness 完成後、複数プロジェクトの知識を aidd-kos で統合管理し、チームの AI 活用を推進する。

---

### 対象プロジェクト

**定義**: aidd-kos がナレッジインデックスを作成・参照するプロジェクト。`uvx aidd-kos serve` の実行ディレクトリが対象プロジェクトとなる。複数プロジェクトを同一サーバーで同時管理しない。

**用例**: 対象プロジェクト A で `uvx aidd-kos serve` を実行すると、`.lightrag/` が
`{project-A}/.lightrag/` に配置され、lightrag_query はプロジェクト A のドキュメントのみを返す。

---

### ナレッジエンジン自動起動

**定義**: MCP サーバーの起動に連動してナレッジエンジン（LightRAG）が自動的に起動される動作。`embedded 起動` とも呼ばれる。手動起動不要でナレッジ検索を即座に利用可能にする。起動待機時間の上限は 30 秒。

**用例**: `uvx aidd-kos serve` を実行するだけで LightRAG が自動起動し、AI Agent は接続後すぐに lightrag_query でドキュメント検索を開始できる。

---

### PyPI（Python Package Index）

**定義**: Python パッケージの公式リポジトリ。`pip install` / `uvx` でパッケージをインストールする際の参照先。
aidd-kos は PyPI に公開されており `uvx aidd-kos install` でインストール可能。

**用例**: `uvx aidd-kos@latest serve` を実行すると、PyPI から最新バージョンの aidd-kos を取得して MCP サーバーを起動する。

---

### GitHub Release

**定義**: GitHub 上でタグと成果物（リリースノート等）を紐付けて公開する仕組み。aidd-kos では `v*` パターンのタグ付きリリースが PyPI への自動公開のトリガーとなる。

**用例**: `v0.2.0` タグを付けた GitHub Release を作成すると、GitHub Actions が自動的に aidd-kos を PyPI へパブリッシュする。

---

### パブリッシュ

**定義**: aidd-kos のビルド成果物（wheel / sdist）を PyPI に登録し、外部から `pip install` / `uvx` でインストール可能な状態にすること。GitHub Release 作成をトリガーに自動実行される。

**用例**: GitHub Release を作成すると publish ワークフローが起動し、aidd-kos が PyPI にパブリッシュされる。

---

### aidd-kos メンテナー

**定義**: aidd-kos を開発・リリースするスパイクスタジオ開発者。バージョン番号の更新・タグ作成・GitHub Release 作成・リリース手順書（RELEASE.md）の管理を担当する。Charter §3 未定義のプロジェクト固有役割。

**用例**: aidd-kos メンテナーが GitHub Release を作成すると、自動的に PyPI へのパブリッシュが実行される。

---

### LIGHTRAG_URL

**定義**: LightRAG REST API のエンドポイント URL を指定する環境変数。デフォルト値は `http://localhost:9621`。外部ホストや別ポートを使用する場合にこの変数で上書きする。

**用例**: Docker コンテナ内で LightRAG を起動する場合、`LIGHTRAG_URL=http://host.docker.internal:9621` と設定して aidd-kos からアクセスする。

---

### 差分インデックス

**定義**: 前回インデックス処理時から変更・追加・削除されたファイルのみを対象とするインデックス更新操作。`aidd-kos index`（デフォルト）で実行される。

**用例**: ドキュメントを 1 件編集後に `aidd-kos index` を実行すると、差分インデックスにより変更ファイルのみが処理され、他のファイルはスキップされる。

---

### 全件再構築

**定義**: 変更の有無に関わらず全対象ファイルを強制再処理するインデックス更新操作。`aidd-kos index --full` で実行される。

**用例**: インデックスが壊れた疑いがある場合に `aidd-kos index --full` を実行し、クリーンな状態に再構築する。

---

### LightRAG インデックス状態

**定義**: LightRAG の `/documents/paginated` API が返す、既にインデックス済みのドキュメント一覧。
差分検出の正規ソースとして `aidd-kos index` が参照する。ローカルへの状態ファイル保存は不要。

**用例**: `aidd-kos index` 実行時に LightRAG インデックス状態を取得し、ファイルシステムと比較して変更・追加・削除を検出する。

---

### 変更検出

**定義**: 前回インデックス処理時から変更・追加されたファイルを特定する操作。インデックス状態ファイルとの比較により実行される。

**用例**: `aidd-kos index` は変更検出により更新対象ファイルを絞り込み、API 呼び出しを最小化する。

---

### 削除検出

**定義**: 前回インデックス処理時以降に削除されたファイルを特定し、インデックスから除去対象として識別する操作。

**用例**: プロジェクトから `old-design.md` を削除後に `aidd-kos index` を実行すると、削除検出によりそのファイルがインデックスから除去される。

---

### スキップ（インデックス文脈）

**定義**: 差分インデックス実行時に変更なしと判定され、処理対象外となったファイル。API 呼び出しは発生しない。

**用例**: 100 件中 1 件を変更した場合、`aidd-kos index` の実行後に「スキップ: 99 件」と表示され、API コストが 1/100 に削減される。

---
