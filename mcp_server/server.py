"""aidd-kos MCP サーバー。LightRAG REST API を MCP ツールとして公開する。"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP

LIGHTRAG_URL = os.environ.get("LIGHTRAG_URL", "http://localhost:9621")
LIGHTRAG_API_KEY = os.environ.get("LIGHTRAG_API_KEY", "")

mcp = FastMCP(
    name="aidd-kos",
    instructions="Project documentation knowledge graph. Use query_documents to search architectural decisions, specifications, and domain knowledge.",
)


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if LIGHTRAG_API_KEY:
        h["Authorization"] = f"Bearer {LIGHTRAG_API_KEY}"
    return h


@mcp.tool()
async def query_documents(query: str, mode: str = "hybrid") -> str:
    """Search project documentation using LightRAG knowledge graph.

    Args:
        query: Natural language question about the project.
        mode: Search mode. 'hybrid' (recommended), 'mix', 'local', 'global', 'naive'.
    """
    async with httpx.AsyncClient(timeout=60) as client:
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


@mcp.tool()
async def get_status() -> str:
    """Check LightRAG server health and index status."""
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


@mcp.tool()
async def list_documents(limit: int = 20) -> str:
    """List indexed documents in the knowledge graph."""
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
