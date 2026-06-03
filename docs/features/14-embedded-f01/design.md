# ナレッジ検索が MCP サーバー起動直後から利用可能になる Design

Feature Issue: #14
Epic: #3

## Spec

docs/spec/embedded-startup.md → Feature: F-01 (#14)

## 変更内容

`mcp_server/server.py` に FastMCP `lifespan` フックを追加し、
MCP Server 起動時に LightRAG をサブプロセスとして自動起動する。

| 変更ファイル | 変更内容 | 対応 AC |
|------------|---------|---------|
| `aidd_kos/errors.py` | `LIGHTRAG_STARTUP_FAILED` エラーコード追加（ADR-001 準拠）| AC-F14-03a/03b |
| `mcp_server/server.py` | `_LIGHTRAG_PORT` 定数追加（`LIGHTRAG_PORT` 環境変数、デフォルト 9621）| 全件 |
| `mcp_server/server.py` | `_lifespan` async context manager 追加 | AC-F14-01〜04b 全件 |
| `mcp_server/server.py` | `FastMCP(lifespan=_lifespan)` に変更 | AC-F14-01〜04b 全件 |

**`_LIGHTRAG_PORT` 設計:**
`LIGHTRAG_PORT` 環境変数（デフォルト 9621）を独立管理する。`LIGHTRAG_URL` パースは URL 形式変化時の挙動が未定義のため採用しない。
embedded 起動のバインドポートは `_LIGHTRAG_PORT` で管理し、`LIGHTRAG_URL` はツールの HTTP 接続先として現状のまま使用する。

**`_lifespan` 設計:**

```text
MCP Server 起動
  └→ lightrag_dir = Path.cwd() / ".lightrag" を作成（mkdir exist_ok=True）
  └→ stdout に lightrag_dir パスをログ出力
  └→ subprocess.Popen([sys.executable, "-m", "lightrag.api.lightrag_server",
                        "--host", "127.0.0.1",
                        "--port", str(_LIGHTRAG_PORT),
                        "--working-dir", str(lightrag_dir)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
  └→ ヘルスチェックループ（最大 30 回）
       ├→ proc.poll() が None 以外 → プロセス即時終了 → ループ脱出
       ├→ urllib.request.urlopen(f"http://127.0.0.1:{_LIGHTRAG_PORT}/health", timeout=1)
       │    成功 → started=True → ループ break → stdout に起動成功ログ → yield
       └→ URLError/OSError → await asyncio.sleep(1) → 次のループ

  started=False（ループ完了後）:
    proc.terminate()
    emit_error(LIGHTRAG_STARTUP_FAILED, "対処手順")  → stderr（即時）
    raise RuntimeError("LIGHTRAG_STARTUP_FAILED")

MCP Server 停止（finally 節）
  └→ stdout に LightRAG 停止開始をログ
  └→ proc.terminate()
  └→ proc.wait(timeout=5)
       タイムアウト時: proc.kill() → proc.wait()  ← ゾンビプロセス防止
  └→ stdout に LightRAG 停止完了をログ
```

## Related Docs

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/14-embedded-f01.md | lifespan 起動・停止・失敗シナリオ（新規）|

※ openapi.yaml・schema.sql・screens の変更なし（内部サーバー動作のみ）

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| ログ | `mcp_server/server.py:_lifespan()` 起動開始直後 | `lightrag_dir` パスを stdout に出力 |
| ログ | `mcp_server/server.py:_lifespan()` ヘルスチェック成功時 | 起動成功 + 待機時間（秒）を stdout |
| エラー | `mcp_server/server.py:_lifespan()` 起動失敗時 | `LIGHTRAG_STARTUP_FAILED` + 対処手順を `emit_error()` 経由で stderr（即時）|
| ログ | `mcp_server/server.py:_lifespan()` finally 節先頭 | LightRAG 停止開始を stdout |
| ログ | `mcp_server/server.py:_lifespan()` finally 節末尾（wait 完了後）| LightRAG 停止完了を stdout |

## Implementation Tasks

### Spec 追記

- [x] `specs/e2e/14-embedded-f01.md` 作成
  → 完了条件: AC-F14-01〜04b 全 6 件（含む 03a/03b の分割）がシナリオに対応している

### テスト実装（RED）

- [x] E2E テスト `tests/e2e/test_embedded_f01.py` 実装
  → 完了条件: `subprocess.Popen`・`urllib.request.urlopen`・`asyncio.sleep` をモック化し、
     AC-F14-01〜04b の全シナリオが RED（テスト実行で失敗）

### 実装・検証

- [x] `aidd_kos/errors.py` に `LIGHTRAG_STARTUP_FAILED = "LIGHTRAG_STARTUP_FAILED"` を追加
  → 完了条件: `from aidd_kos.errors import LIGHTRAG_STARTUP_FAILED` が成功する

- [x] `mcp_server/server.py` に `_LIGHTRAG_PORT` 定数・`_lifespan` 関数を実装
  → 完了条件: 上記設計（`_lifespan` フロー）どおりの実装が動作する

- [x] `mcp_server/server.py` の `mcp = FastMCP(...)` に `lifespan=_lifespan` を追加
  → 完了条件: `mcp = FastMCP(name="aidd-kos", ..., lifespan=_lifespan)` になっている

- [x] 全テスト GREEN 確認（`uv run pytest -q`）
  → 完了条件: 87 passed（統合テスト含む全件 GREEN）

- [x] リファクタ（型チェック・lint）
  → 完了条件: `uv run ruff check mcp_server/ aidd_kos/` exit 0

- [x] AC カバレッジ確認（全 AC テスト対応確認）
  → 完了条件: AC-F14-01〜04b 全 6 件が E2E + Unit でカバー済み

### 追加対応（自己批判の解消）

- [x] FastMCP lifespan RuntimeError 振る舞い確認（ソース調査）
  → `stack.enter_async_context` が RuntimeError を伝播 → サーバー停止 → stderr 出力。AC 想定通り
- [x] `lightrag.api.lightrag_server` モジュール存在確認 → OK
- [x] `aidd_kos/install.py` urllib ローカルインポートをモジュールレベルに移動（integration test バグ修正）
- [x] `tests/e2e/test_install.py` mock_subprocesses fixture 修正（.codegraph 作成）→ 87 passed
