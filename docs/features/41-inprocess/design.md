# LightRAG in-process 化 Design

Feature Issue: #41
Epic: #38

## Spec

docs/spec/multi-project.md → Feature: LightRAG in-process 化 (#41)

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| 実装 | mcp_server/server.py | _lifespan を in-process に変更・lightrag_query/lightrag_list をライブラリ呼び出しに変更 |
| 実装 | aidd_kos/index.py | HTTP URL 定数削除・_fetch_indexed_docs/_send_files/_delete_docs を Python ライブラリ呼び出しに変更 |
| 実装 | aidd_kos/config.py | LightRAG インスタンス生成ヘルパー関数を追加 |
| 実装 | aidd_kos/install.py | start_lightrag_and_index から HTTP サーバー起動ロジックを削除 |
| テスト | tests/unit/test_lifespan.py | in-process 起動に合わせてモック更新 |
| テスト | tests/e2e/test_index_f41.py | ポート 9621 不使用・プロセス不存在を検証 |

## 設計概要

### LightRAG インスタンス生成（aidd_kos/config.py に追加）

```text
_create_lightrag(working_dir: str) -> LightRAG:
  - LLM: openai_complete_if_cache (gpt-4o-mini)
  - Embedding: openai_embed (text-embedding-3-small, dim=1536)
  - Storage: JsonKV / NanoVectorDB / NetworkX（デフォルト）
  - 環境変数: OPENAI_API_KEY（必須）・LLM_MODEL・EMBEDDING_MODEL
```

### mcp_server/server.py の変更

```text
旧:
  _lifespan → lightrag_server サブプロセス起動 → HTTP 経由でツール呼び出し

新:
  _lifespan → LightRAG インスタンス生成 + initialize_storages()
  module-level: _rag: LightRAG | None = None
  lightrag_query → rag.aquery()
  lightrag_list → rag.get_docs_by_status()
  kos_status → rag instance check
```

### aidd_kos/index.py の変更

```text
_fetch_indexed_docs():
  asyncio.run(rag.get_docs_by_status(DocStatus.PROCESSED))
  → {file_path: {id: doc_id, updated_at: updated_at}} の形式に変換

_send_files():
  rag.insert(texts, file_paths=sources)  ← 同期ラッパー
  ainsert() は apipeline_process_enqueue_documents() を待機するため完了保証あり

_delete_docs():
  asyncio.run(rag.adelete_by_doc_id(doc_id, delete_llm_cache=False))

_wait_pipeline_idle() → 不要（削除）
_LIGHTRAG_*_URL 定数 → 削除
```

### aidd_kos/install.py の変更

`start_lightrag_and_index()` から HTTP サーバー起動ロジックを削除。
IndexOrchestrator を直接呼ぶだけになる。

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| ポート | システム | 9621 番ポートが LISTEN 状態にないこと（AC-F41-03）|
| プロセス | システム | lightrag_server プロセスが存在しないこと（AC-F41-05）|
| 機能 | lightrag_query | MCP ツールが正常にクエリを返すこと（AC-F41-01）|

## Implementation Tasks

### テスト実装（RED）

- [ ] tests/e2e/test_index_f41.py 実装
  → 完了条件: AC-F41-03・AC-F41-04・AC-F41-05 のテストが RED
- [ ] tests/unit/test_lifespan.py の既存テストをモック更新（subprocess なしに対応）

### 実装

- [ ] `aidd_kos/config.py` に `create_lightrag_instance()` 追加
- [ ] `aidd_kos/index.py` を LightRAG Python ライブラリ呼び出しに変更
  → `_LIGHTRAG_*_URL` 定数を削除・`_wait_pipeline_idle()` を削除
- [ ] `mcp_server/server.py` を in-process に変更
  → `_rag` モジュール変数・`_lifespan` 変更・ツール関数変更
- [ ] `aidd_kos/install.py` の `start_lightrag_and_index()` を簡略化

### 検証

- [ ] 全テスト GREEN + lint PASS
- [ ] ポート 9621 LISTEN なし（手動確認）
- [ ] lightrag_server プロセスなし（手動確認）
