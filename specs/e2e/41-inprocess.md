# E2E テスト仕様: LightRAG in-process 化 (#41)

Feature: #41 LightRAG in-process 化
Epic: #38 マルチプロジェクト対応
Spec: docs/spec/multi-project.md → Feature F02

## シナリオ一覧

| AC ID | インターフェース | 前提データ | 操作手順 | 確認内容 |
|-------|---------------|----------|---------|---------|
| AC-F41-01 | MCP Tool | プロジェクト A で aidd-kos MCP が起動済み | プロジェクト B でも aidd-kos MCP を起動する | プロジェクト A の `lightrag_query` がエラーなしに応答を返すこと |
| AC-F41-02 | MCP Tool | 各プロジェクトに異なるドキュメントをインデックス済み | プロジェクト B の `lightrag_query` で固有内容を検索 | プロジェクト B のドキュメントが返され A のドキュメントが含まれないこと |
| AC-F41-03 | CLI | aidd-kos MCP サーバーが動作中 | `lsof -i :9621` を実行する | 9621 番ポートが LISTEN 状態にないこと |
| AC-F41-04 | CLI | LIGHTRAG_PORT 未設定 | `aidd-kos serve` を起動して `lightrag_query` を呼び出す | ポート設定なしでクエリが成功すること |
| AC-F41-05 | CLI | aidd-kos MCP サーバーが起動している | `ps aux` で lightrag_server を検索する | `lightrag_server` という名称のプロセスが存在しないこと |

## モック戦略

- AC-F41-01/02: 2プロジェクト同時起動は Claude Code の実動作に依存するため、
  自動テストでは `_lifespan` で `_rag` が初期化されクエリが返ることを検証（test_embedded_f01.py）
- AC-F41-03: ポート 9621 が LISTEN 状態にないことを `socket.create_connection` でテスト
- AC-F41-04: `create_lightrag_instance` をモックし、ポート設定なしで `lightrag_query` が成功することを確認
- AC-F41-05: `mcp_server/server.py` に `subprocess.Popen(lightrag_server)` が存在しないことを確認

## 実施記録

- AC-F41-03: `lsof -i :9621` 結果「port 9621: free」確認済み（2026-06-05 動作確認）
- AC-F41-05: `ps aux | grep lightrag_server` 結果「no lightrag_server process」確認済み（2026-06-05）
- AC-F41-04: `aidd-kos index --full .` が 92 件処理成功（ポート設定なし）確認済み（2026-06-05）
