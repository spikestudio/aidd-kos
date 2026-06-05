"""aidd-kos MCP サーバー（MCP Aggregator）。

LightRAG ツール（lightrag_*）を FastMCP で in-process 呼び出しとして実装する（ADR-004）。
CodeGraph ツール（codegraph_*）を FastMCP process proxy で統合する（ADR-002）。
"""

from __future__ import annotations

import contextlib
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.client.transports import NpxStdioTransport
from fastmcp.server import create_proxy

from aidd_kos.config import create_lightrag_instance
from aidd_kos.errors import (
    LIGHTRAG_INDEX_NOT_FOUND,
    LIGHTRAG_STARTUP_FAILED,
    LIGHTRAG_UNAVAILABLE,
    OPENAI_API_KEY_MISSING,
    QUERY_TIMEOUT,
    emit_error,
)

_QUERY_TIMEOUT_S = float(os.environ.get("LIGHTRAG_QUERY_TIMEOUT_MS", "5000")) / 1000.0
_ALLOWED_MODES = frozenset({"hybrid", "mix", "local", "global", "naive"})

# in-process LightRAG インスタンス（lifespan で初期化・finalize される）
_rag = None


@asynccontextmanager
async def _lifespan(app):
    global _rag

    if not os.environ.get("OPENAI_API_KEY"):
        emit_error(OPENAI_API_KEY_MISSING, ".env ファイルに OPENAI_API_KEY を設定してください")
        raise RuntimeError("OPENAI_API_KEY_MISSING")

    lightrag_dir = Path.cwd() / ".lightrag"
    lightrag_dir.mkdir(exist_ok=True)
    print(f"[aidd-kos] LightRAG in-process 起動: {lightrag_dir}", flush=True)

    try:
        _rag = create_lightrag_instance(str(lightrag_dir))
        await _rag.initialize_storages()
        print("[aidd-kos] LightRAG 起動完了", flush=True)
    except Exception as e:
        emit_error(LIGHTRAG_STARTUP_FAILED, f"LightRAG の起動に失敗しました: {e}")
        raise RuntimeError("LIGHTRAG_STARTUP_FAILED") from e

    try:
        yield
    finally:
        print("[aidd-kos] LightRAG 停止中...", flush=True)
        if _rag is not None:
            with contextlib.suppress(Exception):
                await _rag.finalize_storages()
        _rag = None
        print("[aidd-kos] LightRAG 停止完了", flush=True)


mcp = FastMCP(
    name="aidd-kos",
    instructions=(
        "Agentic Knowledge OS — project knowledge graph.\n"
        "Use lightrag_query to search documentation, ADRs, and design decisions.\n"
        "Use lightrag_list to see indexed documents.\n"
        "Use kos_status to check engine health."
    ),
    lifespan=_lifespan,
)


@mcp.tool()
async def lightrag_query(query: str, mode: str = "hybrid") -> str:
    """Search project documentation using LightRAG knowledge graph.

    Use this tool when you need to find design decisions, ADRs, meeting notes,
    or any project documentation by natural language query.

    Args:
        query: Natural language question about the project.
        mode: Search mode — hybrid (recommended), mix, local, global, naive.
    """
    if mode not in _ALLOWED_MODES:
        from aidd_kos.errors import INVALID_MODE

        emit_error(INVALID_MODE, f"有効な mode: {', '.join(sorted(_ALLOWED_MODES))}")
        return f"INVALID_MODE: '{mode}' は無効です。有効な値: {', '.join(sorted(_ALLOWED_MODES))}"

    if _rag is None:
        emit_error(LIGHTRAG_UNAVAILABLE, "LightRAG が初期化されていません")
        return "LIGHTRAG_UNAVAILABLE: LightRAG が初期化されていません"

    lightrag_dir = Path.cwd() / ".lightrag"
    index_ready = lightrag_dir.exists() and any(
        f.suffix in {".json", ".graphml"} for f in lightrag_dir.iterdir() if f.is_file()
    )
    if not index_ready:
        emit_error(
            LIGHTRAG_INDEX_NOT_FOUND,
            "aidd-kos index を実行してインデックスを構築してください",
        )
        return (
            "LIGHTRAG_INDEX_NOT_FOUND: インデックスが未構築です。aidd-kos index を実行してください"
        )

    try:
        import asyncio

        from lightrag import QueryParam

        async def _run_query() -> str:
            result = await _rag.aquery_llm(query, QueryParam(mode=mode))
            llm_resp = result.get("llm_response", {})
            answer = llm_resp.get("response", "")
            refs = llm_resp.get("references") or []
            sources = [
                r["file_path"].replace("___", "/")
                for r in refs
                if isinstance(r, dict) and "file_path" in r
            ]
            if sources:
                answer += "\n\n参照:\n" + "\n".join(f"- {s}" for s in sources)
            return answer

        return await asyncio.wait_for(_run_query(), timeout=_QUERY_TIMEOUT_S)
    except TimeoutError:
        emit_error(
            QUERY_TIMEOUT,
            f"クエリがタイムアウトしました（{_QUERY_TIMEOUT_S:.0f}秒）。LIGHTRAG_QUERY_TIMEOUT_MS 環境変数で調整できます。",
        )
        return "QUERY_TIMEOUT: クエリがタイムアウトしました"
    except Exception as e:
        emit_error(LIGHTRAG_UNAVAILABLE, f"クエリ中にエラーが発生しました: {e}")
        return f"LIGHTRAG_UNAVAILABLE: クエリ中にエラーが発生しました ({type(e).__name__})"


@mcp.tool()
async def lightrag_list(limit: int = 20) -> str:
    """List indexed documents in the knowledge graph.

    Use this tool to understand what project knowledge is available
    before making queries, or to verify indexing status.

    Args:
        limit: Maximum number of documents to list.
    """
    if _rag is None:
        return "LIGHTRAG_UNAVAILABLE: LightRAG が初期化されていません"

    try:
        from lightrag.base import DocStatus

        docs_dict = await _rag.get_docs_by_status(DocStatus.PROCESSED)
        docs = list(docs_dict.values())[:limit]
        if not docs:
            return "インデックス済みドキュメントなし"
        lines = [
            f"- {str(getattr(d, 'content_summary', None) or getattr(d, 'file_path', '?'))[:80]}"
            f" ({getattr(d, 'status', '?')})"
            for d in docs
        ]
        return f"インデックス済みドキュメント ({len(docs)} 件):\n" + "\n".join(lines)
    except Exception as e:
        emit_error(LIGHTRAG_UNAVAILABLE, f"ドキュメント一覧の取得に失敗しました: {e}")
        return f"LIGHTRAG_UNAVAILABLE: ドキュメント一覧の取得に失敗しました ({type(e).__name__})"


@mcp.tool()
async def kos_status() -> str:
    """Check the status of all aidd-kos knowledge engines.

    Use this tool to verify the system is ready before starting a work session,
    or to understand which tools are available.

    Returns status of LightRAG (ready/unavailable/indexing) and CodeGraph (ready/unavailable),
    plus the list of available tools.
    """
    from aidd_kos.status import StatusChecker

    checker = StatusChecker()
    data = checker.check()

    # LightRAG は in-process なのでプロセス状態を直接確認する
    lr_status = "ready" if _rag is not None else "unavailable"

    cg = data["codegraph"]

    available_tools = [
        "lightrag_query",
        "lightrag_list",
    ]
    if cg["status"] == "ready":
        available_tools.extend(
            [
                "codegraph_explore",
                "codegraph_impact",
                "codegraph_context",
                "codegraph_callers",
                "codegraph_callees",
                "codegraph_trace",
            ]
        )

    lines = [
        f"LightRAG:   {lr_status} (in-process)",
        f"CodeGraph:  {cg['status']} (nodes: {cg.get('node_count', 0)})",
        f"available_tools: {', '.join(available_tools)}",
    ]
    return "\n".join(lines)


# ── CodeGraph proxy（ADR-002: NpxStdioTransport + create_proxy + mount）─────────
# namespace="codegraph" により全ツールが codegraph_* prefix で公開される
try:
    _codegraph_proxy = create_proxy(
        NpxStdioTransport(
            package="@colbymchenry/codegraph",
            args=["serve"],
            env_vars={"PATH": os.environ.get("PATH", "")},
        )
    )
    mcp.mount(_codegraph_proxy, namespace="codegraph")
except Exception as _e:
    print(f"[aidd-kos] CodeGraph proxy の登録に失敗しました: {_e}", flush=True)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
