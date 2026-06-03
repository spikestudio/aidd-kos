# 用語集

<!-- aidd-glossary によって管理。手動編集可。追加・更新時は /aidd-glossary を実行する -->

最終更新: 2026-06-03

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

**用例**: LightRAG はドキュメントを Entity と Relation に分解してナレッジグラフに格納し、query_documents 実行時に Vector と Graph の両経路で関連情報を取得する。

---

### Dual-Level Retrieval

**定義**: Vector 検索（意味的類似性）とナレッジグラフ（Entity-Relation 構造）の 2 つの検索経路を組み合わせた LightRAG 固有の検索方式。単一手法より検索精度と網羅性が高い。

**用例**: Dual-Level Retrieval により、キーワードが直接一致しない場合でも Entity 間の関係を辿って関連ドキュメントを取得できる。

---

### MCP (Model Context Protocol)

**定義**: AI エージェント（Claude Code / Claude Desktop 等）が外部ツールやデータソースと通信するための標準プロトコル。aidd-kos では stdio 経由で FastMCP サーバーへ接続し、ナレッジ検索ツールを提供する。

**用例**: Claude Code は MCP stdio を経由して aidd-kos の query_documents ツールを呼び出し、プロジェクトドキュメントを検索する。

---

### FastMCP

**定義**: Python ネイティブの MCP サーバー実装フレームワーク（バージョン 2.0+）。最小限のコードで MCP ツールを公開でき、aidd-kos の MCP インターフェース層として採用されている。

**用例**: FastMCP を使用することで、query_documents / get_status / list_documents の 3 つの MCP ツールを簡潔に定義・公開している。

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

**用例**: "FastMCP"・"query_documents"・"Dual-Level Retrieval" はそれぞれ Entity として抽出され、相互の Relation とともにナレッジグラフに保存される。

---

### Relation（関係）

**定義**: LightRAG がドキュメントから抽出する Entity 間の意味的な結びつき。ナレッジグラフのエッジとして格納され、Entity 間の文脈を保持する。

**用例**: "FastMCP が MCP ツールを公開する" という Relation により、query_documents と FastMCP の依存関係をグラフ検索で辿ることができる。

---

### query_documents

**定義**: aidd-kos が提供する MCP ツールの一つ。自然言語クエリを受け取り、LightRAG の Dual-Level Retrieval で関連ドキュメントを検索・返却する。P95 応答時間 2 秒未満（1 万ドキュメント規模）が目標値。

**用例**: Claude Code が query_documents を呼び出し「このプロジェクトの認証方式は？」と問い合わせると、関連する ADR や設計書が返却される。

---

### get_status

**定義**: aidd-kos が提供する MCP ツールの一つ。LightRAG インデックスの現在の状態（インデックス済みドキュメント数・ストレージ状況等）を即時確認する。

**用例**: get_status を呼び出すことで、インデックス構築が完了しているかどうかを MCP 経由で即座に確認できる。

---

### list_documents

**定義**: aidd-kos が提供する MCP ツールの一つ。インデックスに登録済みのドキュメント一覧を返却する。

**用例**: list_documents を実行してインデックス対象のドキュメントが正しく登録されているか確認した上で、query_documents の検索精度を評価する。

---

### .lightrag/

**定義**: LightRAG がグラフデータとベクトルデータをローカルファイルとして保存するディレクトリ。DB サーバーを不要とし、ローカル実行ツールとしての導入摩擦を最小化する設計。

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

### LIGHTRAG_URL

**定義**: LightRAG REST API のエンドポイント URL を指定する環境変数。デフォルト値は `http://localhost:9621`。外部ホストや別ポートを使用する場合にこの変数で上書きする。

**用例**: Docker コンテナ内で LightRAG を起動する場合、`LIGHTRAG_URL=http://host.docker.internal:9621` と設定して aidd-kos からアクセスする。

---
