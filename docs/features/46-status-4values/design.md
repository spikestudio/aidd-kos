# インデックス状態の 4 値可視化・エラー診断（CLI + MCP）Design

Feature Issue: #46
Epic: #27

## Spec

docs/spec/status-visibility.md → Feature F01: インデックス状態の 4 値可視化・エラー診断（CLI + MCP）(#46)

## Related Docs（このFeatureが追記・生成するファイル）

| 種別 | ファイル | 変更内容 |
|------|---------|---------|
| E2E | specs/e2e/46-status-4values.md | CLI + MCP 状態確認シナリオ（新規）|

## 変更対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `aidd_kos/index.py` | `IndexOrchestrator.run()` 正常完了後に `.lightrag/last_indexed_at` を書き込む |
| `aidd_kos/status.py` | `_check_lightrag()` に Stale 検出追加・`unavailable` → `error` + `error_code` 追加 |
| `aidd_kos/cli.py` | `status()` 出力フォーマット更新・Error 時 stderr 出力追加 |
| `mcp_server/server.py` | `kos_status()` を JSON 構造化レスポンスに変更・Stale 検出追加 |

## 設計メモ

### 状態判定優先順（CLI StatusChecker）

サーバー疎通チェックと Stale 検出を独立した処理パスとして位置づける。

```text
1. HTTP health endpoint に接続できない → error（LIGHTRAG_UNAVAILABLE）
   ※ mtime 比較はスキップする
2. HTTP 到達可能 + pipeline busy → indexing（Stale チェックスキップ）
3. HTTP 到達可能 + pipeline not busy + changed_count > 0 → stale（changed_count）
4. HTTP 到達可能 + pipeline not busy + changed_count = 0 → ready
```

「サーバー落ち + ファイル変更済み」の場合は `error` を返す（Stale チェック不要）。

### Stale 検出アルゴリズム

条件: HTTP 到達可能 + pipeline not busy の場合のみ実行。

```text
1. .lightrag/last_indexed_at を読む
   - 存在しない → changed_count = 0（未インデックス扱い、stale にしない）
2. project_dir 配下の .md / .txt ファイルを列挙
3. mtime > last_indexed_at のファイル数 = changed_count
4. changed_count > 0 → stale(changed_count) / 0 → ready
```

### last_indexed_at 書き込みルール（index.py）

- `IndexOrchestrator.run()` が正常完了（`sys.exit()` なし）した場合のみ書き込む
- `--full` モード: `shutil.rmtree` → `mkdir .lightrag` → インデックス処理 → 成功後に `last_indexed_at` を書き込む（rmtree の後に書き込むこと）
- `--full` モードで `_send_files` が失敗して `sys.exit(1)` する場合は書き込まない

### kos_status レスポンス形式（JSON 構造化）— 破壊的変更

現在の `str` 返却から JSON 文字列に変更する（後方互換性なし）。

```json
{
  "lightrag": {
    "status": "ready|stale|indexing|error",
    "changed_count": 0,
    "error_code": null,
    "indexed_at": "2026-06-09T...",
    "doc_count": 42
  },
  "codegraph": {"status": "ready|unavailable", "node_count": 72},
  "available_tools": ["lightrag_query", "lightrag_list", "kos_status"]
}
```

### AC-F46-06 のテスト前提

MCP サーバーの lifespan は `_rag` が `None` の場合に `RuntimeError` を raise するため、
本番動作では `kos_status` が `_rag is None` の状態で呼ばれることはない。
ただし `_rag` グローバル変数を `None` にモックすることでコードパスの単体テストが可能。
ユニットテストのみを想定したモック前提シナリオとして実装する。

### CLI stdout/stderr 出力フォーマット（インデント込み）

```text
  LightRAG:   ready              ← AC-F46-01
  LightRAG:   stale (変更 N 件)  ← AC-F46-02
  LightRAG:   error              ← AC-F46-03
```

stderr（Error 時のみ）:

```text
[LIGHTRAG_UNAVAILABLE] LightRAG サーバーが起動していません。再試行: aidd-kos serve
```

### STRIDE メモ

stderr 出力には現在固定文字列のみを使用する。将来 `project_dir` の絶対パスを含む
remediation メッセージを追加する場合は `errors.py` の `emit_error()` マスクパターンを
拡張すること（`/Users/[username]/...` 等のパス露出に注意）。

## 観測ポイント

| 種別 | 場所 | 計測内容 |
|------|------|---------|
| stdout | `aidd_kos/cli.py:status()` | `LightRAG: {status}` または `LightRAG: stale (変更 N 件)` |
| stderr | `aidd_kos/cli.py:status()` | Error 時のみ: `[LIGHTRAG_UNAVAILABLE] ...` |
| ログ | `mcp_server/server.py:kos_status()` | JSON レスポンスの `lightrag.status` フィールド |

## Implementation Tasks

### Spec 追記

- [ ] specs/e2e/46-status-4values.md 作成
  → 完了条件: AC-F46-01〜06 が全て 1 件以上のシナリオに対応

### テスト実装（RED）

- [ ] ユニットテスト実装（tests/unit/test_status.py に追記）
  → 完了条件: AC-F46-01〜04 の各状態をカバーするテストが RED
- [ ] ユニットテスト実装（tests/unit/test_lifespan.py または新規ファイルに追記）
  → 完了条件: AC-F46-05/06 をカバーするテストが RED（`_rag` モック前提）
- [ ] E2E テスト実装（tests/e2e/test_status.py に追記）
  → 完了条件: E2E シナリオが RED

### 実装・検証

- [ ] `aidd_kos/index.py` に `last_indexed_at` 書き込みを追加
  → 完了条件: 正常完了後に `.lightrag/last_indexed_at` が書き込まれる。
     `--full` モードでは `rmtree` の後に書き込む。`sys.exit(1)` 時は書き込まない
- [ ] `aidd_kos/status.py:StatusChecker._check_lightrag()` を拡張（判定優先順に従う）
  → 完了条件: ユニットテスト GREEN（error/indexing/stale/ready の各状態）
- [ ] `aidd_kos/cli.py:status()` 出力フォーマット更新（上記インデント込みフォーマット）
  → 完了条件: ユニットテスト GREEN + stdout/stderr フォーマット一致
- [ ] `mcp_server/server.py:kos_status()` を JSON レスポンスに更新
  → 完了条件: ユニットテスト GREEN + AC-F46-05/06 充足（`_rag` モック使用）
- [ ] リファクタ
  → 完了条件: 全テストが GREEN かつ `uv run ruff check . && uv run ruff format --check .` PASS
- [ ] AC カバレッジ確認
  → 完了条件: `git grep "AC-F46"` で全テストコードが発見できること
