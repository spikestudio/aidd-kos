# FastMCP 2.x / 3.x 複数 MCP サーバー集約 (Aggregator / Proxy / Composition) 調査

- 調査日: 2026-06-03
- 調査者: aidd-researcher
- 対象バージョン: fastmcp 3.4.0（プロジェクト `.venv` にインストール済み）
- pyproject.toml 依存宣言: `fastmcp>=2.0.0`

---

## 調査目的

aidd-kos MCP Server で以下の 2 つを単一エンドポイントに束ねる実装方針を確定する。

| コンポーネント | 種別 | 起動方法 |
|---|---|---|
| LightRAG ツール | 直接実装（Python decorator） | `mcp_server/server.py` 内 `@mcp.tool()` |
| CodeGraph | 外部 npm パッケージ | `npx @colbymchenry/codegraph serve` |

---

## 調査結果

### 1. process proxy（外部プロセス起動）機能の有無

**確認済み。FastMCP 3.x に存在する。**

FastMCP は以下 2 つのルートで外部プロセスを proxy できる。

#### ルート A: `NpxStdioTransport` + `create_proxy()` + `mount()`

```python
from fastmcp.client.transports import NpxStdioTransport
from fastmcp.server import create_proxy
from fastmcp import FastMCP

# 外部 npx パッケージを subprocess として起動し proxy する
codegraph_proxy = create_proxy(
    NpxStdioTransport(
        package="@colbymchenry/codegraph",
        args=["serve"],
        env_vars={"NODE_ENV": "production"},  # 必要な環境変数を明示
        keep_alive=True,                       # デフォルト True: 接続間で subprocess を再利用
    ),
    name="CodeGraph",
)

# 既存の FastMCP インスタンスに namespace 付きでマウント
mcp = FastMCP("aidd-kos")
mcp.mount(codegraph_proxy, namespace="codegraph")
```

- `NpxStdioTransport(package, args, env_vars, project_directory, use_package_lock, keep_alive)` は FastMCP 3.x に存在する（実機確認済み）。
- STDIO servers は**シェル環境変数を継承しない**。必要な変数は `env_vars` で明示的に渡すこと。
- `keep_alive=True`（デフォルト）で subprocess をセッション間で再利用する。

#### ルート B: `MCPConfig` dict + `create_proxy()` + `mount()`

```python
from fastmcp.server import create_proxy
from fastmcp import FastMCP

config = {
    "mcpServers": {
        "codegraph": {
            "command": "npx",
            "args": ["-y", "@colbymchenry/codegraph", "serve"],
            # "env": {"NODE_ENV": "production"},   # 任意
            # "cwd": "/path/to/project",           # 任意
        }
    }
}

# config dict は MCPConfig.model_validate() で StdioMCPServer に変換される（実機確認済み）
codegraph_proxy = create_proxy(config, name="CodeGraph")

mcp = FastMCP("aidd-kos")
mcp.mount(codegraph_proxy, namespace="codegraph")
```

- `MCPConfig` の `mcpServers` 値は `StdioMCPServer | RemoteMCPServer | TransformingStdioMCPServer | TransformingRemoteMCPServer` の Union 型。
- `command: "npx"`, `args: [...]` 形式で `StdioMCPServer` としてパースされることを実機確認済み。
- `MCPConfigTransport` が「サーバーが 1 つ」の場合は直接 transport を生成し、「複数」の場合は内部で自動的に mount して composite client を返す。

### 2. 正確な API 名・メソッド名（FastMCP 3.4.0 実機確認）

| API | モジュール | 用途 |
|---|---|---|
| `create_proxy(target, **settings)` | `fastmcp.server` | target を proxy する `FastMCPProxy` を返す |
| `FastMCP.mount(server, namespace, tool_names, ...)` | `fastmcp` | proxy サーバーを親にマウント（動的・ライブ接続） |
| `NpxStdioTransport(package, args, env_vars, ...)` | `fastmcp.client.transports` | `npx <package>` をサブプロセス起動する transport |
| `StdioTransport(command, args, env, cwd, ...)` | `fastmcp.client.transports` | 任意コマンドをサブプロセス起動する汎用 transport |
| `MCPConfigTransport(config, name_as_prefix)` | `fastmcp.client.transports` | MCP JSON config 形式で複数サーバーに一括接続 |
| `MCPConfig` | `fastmcp.mcp_config` | MCP JSON config の Pydantic モデル |

**非推奨 API:**

- `FastMCP.import_server()`: 廃止予定。`mount()` を使うこと（docstring に明記）。
- `mount()` の `as_proxy` パラメータ: 廃止予定。`create_proxy()` を先に呼ぶこと。
- `mount()` の `prefix` パラメータ: 廃止予定。`namespace` を使うこと。

### 3. `create_proxy()` のシグネチャ

```python
create_proxy(
    target: (
        Client | ClientTransport | FastMCP | FastMCP1Server
        | AnyUrl | Path | MCPConfig | dict | str
    ),
    **settings: Any
) -> FastMCPProxy
```

`target` に渡せるもの:

- `NpxStdioTransport(...)` — npx コマンドの subprocess
- `StdioTransport(command, args)` — 任意コマンドの subprocess
- `"http://..."` / `AnyUrl` — HTTP/SSE リモートサーバー
- `Path("./server.py")` / `"./server.py"` — Python スクリプト（subprocess）
- `MCPConfig` / `dict` — MCP JSON config 形式

### 4. `FastMCP.mount()` のシグネチャ

```python
mount(
    server: FastMCP,
    namespace: str | None = None,    # ツール名のプレフィックス（例: "codegraph" → "codegraph_tool_name"）
    tool_names: dict[str, str] | None = None,  # 個別ツール名のオーバーライド
) -> None
```

- namespace を指定するとツール名が `{namespace}_{original_name}` になる。
- namespace なしで複数サーバーをマウントすると名前衝突時は後勝ち。
- ライフスパン（lifespan）は親サーバー起動時に実行される。

---

## 確認できなかった点

- `@colbymchenry/codegraph` の MCP サーバー実装詳細（tool 名・スキーマ）は未確認。実際にマウント後に tool 一覧で確認が必要。
- `npx @colbymchenry/codegraph serve` のデフォルト transport（stdio か http か）は未確認。stdio であれば `NpxStdioTransport` でそのまま動作するが、http ポートを起動するなら `StdioTransport` + 起動後 HTTP 接続に変更が必要。

---

## 推薦実装方針（1 案）

### 方針: `NpxStdioTransport` + `create_proxy()` + `mount(namespace="codegraph")`

`mcp_server/server.py` の `mcp` インスタンスに、CodeGraph を namespace 付きでマウントする。

**理由:**

1. `NpxStdioTransport` が FastMCP 3.4.0 に存在することを実機確認済みで、最も直接的な API。
2. `create_proxy()` → `mount()` の組み合わせは公式ドキュメントで推奨パターン（composition ページに明記）。
3. `namespace="codegraph"` を指定すると CodeGraph のツールが `codegraph_xxx` に前置され、LightRAG ツールと名前衝突しない。
4. `keep_alive=True`（デフォルト）により subprocess の起動オーバーヘッドが 1 回のみになる。

**実装例:**

```python
# mcp_server/server.py（追記部分）

from fastmcp.client.transports import NpxStdioTransport
from fastmcp.server import create_proxy

# ... 既存の mcp = FastMCP("aidd-kos") および @mcp.tool() 定義は変更なし ...

# CodeGraph を外部プロセスとして起動し、mcp に namespace 付きでマウント
_codegraph_proxy = create_proxy(
    NpxStdioTransport(
        package="@colbymchenry/codegraph",
        args=["serve"],
        # STDIO servers はシェル環境変数を継承しない。
        # CodeGraph が必要とする環境変数があれば env_vars で渡す。
        # env_vars={"SOME_VAR": os.environ.get("SOME_VAR", "")},
    ),
    name="CodeGraph",
)
mcp.mount(_codegraph_proxy, namespace="codegraph")


def main() -> None:
    mcp.run()
```

**注意事項:**

- STDIO 環境変数の非継承: `npx` 実行時にシェルの `PATH` が引き継がれない場合がある。`npx` が見つからない場合は `StdioTransport(command="npx", args=["@colbymchenry/codegraph", "serve"])` で絶対パス指定に切り替える。
- `npx -y` フラグ: パッケージが未インストールなら自動インストールする。CI 環境では `args=["-y", "@colbymchenry/codegraph", "serve"]` の形式が安全（ただし `NpxStdioTransport` は `package` 引数のみで `-y` を自動付与するかは要確認）。確実にするなら `StdioTransport(command="npx", args=["-y", "@colbymchenry/codegraph", "serve"])` を使う。
- CodeGraph の transport が stdio でない場合: `npx @colbymchenry/codegraph serve` が HTTP サーバーを起動するなら、`StdioTransport` で起動後に `create_proxy("http://localhost:{port}/mcp")` に切り替える二段構成になる。

---

## 参照ソース

| ソース | URL / パス | 参照日 |
|---|---|---|
| FastMCP 公式 Composition ドキュメント | <https://gofastmcp.com/servers/composition> | 2026-06-03 |
| FastMCP 公式 Proxy パターンドキュメント | <https://gofastmcp.com/patterns/proxy> | 2026-06-03 |
| FastMCP 公式 Client Transports ドキュメント | <https://gofastmcp.com/clients/transports> | 2026-06-03 |
| jlowin/fastmcp-proxy ブログ | <https://jlowin.dev/blog/fastmcp-proxy> | 2026-06-03 |
| PyPI fastmcp | <https://pypi.org/project/fastmcp/> | 2026-06-03 |
| 実機確認: `NpxStdioTransport` help() | `.venv/bin/python -c "from fastmcp.client.transports import NpxStdioTransport; help(NpxStdioTransport)"` | 2026-06-03 |
| 実機確認: `create_proxy` signature | `.venv/bin/python -c "from fastmcp.server import create_proxy; ..."` | 2026-06-03 |
| 実機確認: `MCPConfig` parse | `.venv/bin/python -c "from fastmcp.mcp_config import MCPConfig; MCPConfig.model_validate(...)"` | 2026-06-03 |
| 実機確認: `FastMCP.mount` signature | `.venv/bin/python -c "from fastmcp import FastMCP; ..."` | 2026-06-03 |
