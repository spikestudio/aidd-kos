"""aidd-kos MCP サーバー（MCP Aggregator）。

LightRAG ツール（lightrag_*）を FastMCP で直接実装する。
CodeGraph ツール（codegraph_*）は F-02 で proxy として追加される。
"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP

from aidd_kos.errors import LIGHTRAG_UNAVAILABLE, QUERY_TIMEOUT, emit_error

LIGHTRAG_URL = os.environ.get("LIGHTRAG_URL", "http://localhost:9621")
LIGHTRAG_API_KEY = os.environ.get("LIGHTRAG_API_KEY", "")
_QUERY_TIMEOUT_S = float(os.environ.get("LIGHTRAG_QUERY_TIMEOUT_MS", "5000")) / 1000.0
_ALLOWED_MODES = frozenset({"hybrid", "mix", "local", "global", "naive"})

mcp = FastMCP(
    name="aidd-kos",
    instructions=(
        "Agentic Knowledge OS — project knowledge graph.\n"
        "Use lightrag_query to search documentation, ADRs, and design decisions.\n"
        "Use lightrag_list to see indexed documents.\n"
        "Use kos_status to check engine health."
    ),
)


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if LIGHTRAG_API_KEY:
        h["Authorization"] = f"Bearer {LIGHTRAG_API_KEY}"
    return h


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
        return f"INVALID_MODE: '{mode}' は無効です。有効な値: {', '.join(sorted(_ALLOWED_MODES))}"

    try:
        async with httpx.AsyncClient(timeout=_QUERY_TIMEOUT_S) as client:
            resp = await client.post(
                f"{LIGHTRAG_URL}/query",
                json={"query": query, "mode": mode, "include_references": True},
                headers=_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("response", "")
            refs = data.get("references") or []
            sources = [r["file_path"] for r in refs if isinstance(r, dict) and "file_path" in r]
            if sources:
                answer += "\n\n参照:\n" + "\n".join(f"- {s}" for s in sources)
            return answer
    except httpx.TimeoutException:
        emit_error(
            QUERY_TIMEOUT,
            f"クエリがタイムアウトしました（{_QUERY_TIMEOUT_S:.0f}秒）。LIGHTRAG_QUERY_TIMEOUT_MS 環境変数で調整できます。",
        )
        return "QUERY_TIMEOUT: クエリがタイムアウトしました"
    except (httpx.ConnectError, httpx.HTTPStatusError, Exception) as e:
        emit_error(LIGHTRAG_UNAVAILABLE, "task server:start を実行してください")
        return f"LIGHTRAG_UNAVAILABLE: LightRAG サーバーに接続できません ({type(e).__name__})"


@mcp.tool()
async def lightrag_list(limit: int = 20) -> str:
    """List indexed documents in the knowledge graph.

    Use this tool to understand what project knowledge is available
    before making queries, or to verify indexing status.

    Args:
        limit: Maximum number of documents to list.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{LIGHTRAG_URL}/documents/list",
                json={"limit": limit},
                headers=_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            docs = data.get("statuses") or []
            if not docs:
                return "インデックス済みドキュメントなし"
            lines = [
                f"- {d.get('file_path', d.get('id', '?'))} ({d.get('status', '?')})"
                for d in docs[:limit]
            ]
            return f"インデックス済みドキュメント ({len(docs)} 件):\n" + "\n".join(lines)
    except (httpx.ConnectError, httpx.HTTPStatusError, Exception) as e:
        emit_error(LIGHTRAG_UNAVAILABLE, "task server:start を実行してください")
        return f"LIGHTRAG_UNAVAILABLE: LightRAG サーバーに接続できません ({type(e).__name__})"


@mcp.tool()
async def get_status() -> str:
    """Check LightRAG server health and index status.

    Deprecated: use kos_status instead (will be replaced in F-03).
    """
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            h = await client.get(f"{LIGHTRAG_URL}/health", headers=_headers())
            health = h.json()
        except Exception as e:
            return f"Uninitialized: サーバー未起動 ({e})"

        try:
            p = await client.get(f"{LIGHTRAG_URL}/documents/pipeline_status", headers=_headers())
            pipeline = p.json()
        except Exception:
            pipeline = {}

        status = health.get("status", "unknown")
        busy = pipeline.get("busy", False)
        if busy:
            return "Indexing: インデックス処理中"
        return f"Status: {status}"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
