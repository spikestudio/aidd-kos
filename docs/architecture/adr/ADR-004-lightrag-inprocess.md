# ADR-004: LightRAG in-process 化（HTTP サーバーレス）

| 項目 | 内容 |
|------|------|
| ステータス | 承認済み |
| 日付 | 2026-06-05 |
| 決定者 | sanojimaru |

## コンテキスト

現在の aidd-kos は LightRAG を `lightrag_server` サブプロセス（固定ポート 9621）として起動し、
MCP サーバーと `aidd-kos index` コマンドがともに HTTP API 経由でアクセスする。

この設計では、2 つのプロジェクトで同時に Claude Code を開くと LightRAG が 2 つ起動しようとして
ポート 9621 が競合し、後から起動した方がクラッシュする。

Epic #38 のゴール「複数 Claude Code ウィンドウの同時起動」を実現するには、
LightRAG がポートを占有しない形に変更する必要がある。

## 決定事項

**`lightrag_server` サブプロセスを廃止し、LightRAG Python ライブラリを MCP サーバープロセス内で
直接呼び出す（in-process 化）。`aidd_kos/index.py` も HTTP API から Python ライブラリ呼び出しに変更する。**

```python
# Before: HTTP サーバー経由
requests.post("http://127.0.0.1:9621/documents/texts", json={...})

# After: in-process（Python ライブラリ直接呼び出し）
from lightrag import LightRAG, QueryParam
rag = LightRAG(working_dir=".lightrag", ...)
await rag.ainsert(content)
result = await rag.aquery(query, param=QueryParam(mode="hybrid"))
```

LightRAG Python API が HTTP API の全操作をカバーすることを確認済み:

- `ainsert()` → `/documents/texts`
- `aquery_llm()` → `/query`（`references` フィールドを含む完全なレスポンスが必要なため `aquery` ではなく `aquery_llm` を使用）
- `adelete_by_doc_id()` → `/documents/delete_document`
- `get_docs_by_status()` → `/documents/paginated`

## 根拠

1. **ポート占有ゼロ**: in-process 化によりネットワークポートを使用しない
2. **複数インスタンス**: 各プロジェクトが独立した LightRAG インスタンスを持てる
3. **アーキテクチャ簡潔化**: `scripts/server.py`・LightRAG プロセス管理コードが不要になる
4. **HTTP オーバーヘッド削減**: 直接呼び出しにより query レスポンスが高速化する可能性
5. **完全な Python API**: LightRAG v1.5.0 の Python ライブラリが HTTP API と同等の操作を提供

## 代替案

### 代替案 A: LightRAG in-process 化（**採用**）

- メリット: ポート占有ゼロ・複数インスタンス対応・アーキテクチャ簡潔化
- デメリット: 2 プロジェクト同時起動時はメモリが 2 倍になる（LightRAG が各プロセスにロード）

### 代替案 B: 動的ポート割り当て（ランダムポートで LightRAG を起動）

- メリット: 既存の HTTP アーキテクチャを維持できる
- デメリット: ポート検出機構の実装が複雑・各 MCP サーバーが使用ポートを伝える仕組みが必要・
  `aidd-kos index` が正しい LightRAG インスタンスを見つける問題が残る

### 代替案 C: Unix ソケット通信

- メリット: ポート競合なし・HTTP より高速
- デメリット: Windows 非対応（クロスプラットフォーム制約）・実装コスト大

## 影響・トレードオフ

- **影響を受けるコンポーネント:**
  - `mcp_server/server.py`（`_lifespan` の LightRAG 起動方式を全面変更）
  - `aidd_kos/index.py`（HTTP API 呼び出しを Python ライブラリ呼び出しに変更）
  - `aidd_kos/config.py`（LightRAG インスタンスの設定を集約）
  - `scripts/server.py`（不要になるため廃止または空実装に変更）
  - `aidd_kos/install.py`（LightRAG 起動チェックロジックの変更）
- **影響を受ける Epic / Phase:** Epic #38（マルチプロジェクト対応）
- **Charter §10 採用方針との関係:**
  Charter §9「LightRAG 起動（embedded）」の記述が変更される。
  旧記述「MCP サーバーのサブプロセスとして起動」→ 新記述「in-process で直接呼び出し」
- **マスタドキュメントの更新:**
  - `docs/architecture/baseline.md` §C4 Container 図 の LightRAG 起動方式を更新
  - `docs/PROJECT-CHARTER.md` §9 アーキテクチャ方針「LightRAG 起動（embedded）」の説明を更新
  - `docs/business-context/install.md` §前提チェック から「ポート 9621 使用可能」を削除
- **トレードオフ:**
  - 2 プロジェクト同時起動時はメモリ使用量が約 2 倍になる。
    LightRAG のベース使用量は数百 MB 程度であり、ソロ開発者ツールとして許容範囲と判断する。
  - LightRAG の Python ライブラリ API が HTTP API と完全一致しない場合はアダプタ層が必要になる可能性がある。
    v1.5.0 での調査では `ainsert`・`aquery`・`adelete_by_doc_id`・`get_docs_by_status` がすべて確認済み。
  - `aidd-kos index` コマンドと MCP サーバーが同じ `.lightrag/` ディレクトリに対して
    並行書き込みを行う場合の排他制御は LightRAG 内部実装に委ねる（v1.5.0 で確認済みの pipeline_busy 機構）。
