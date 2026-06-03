"""aidd-kos MCP サーバー（MCP Aggregator）。

LightRAG ツール（lightrag_*）を FastMCP で直接実装する。
CodeGraph ツール（codegraph_*）を FastMCP process proxy で統合する（ADR-002）。
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastmcp import FastMCP
from fastmcp.client.transports import NpxStdioTransport
from fastmcp.server import create_proxy

from aidd_kos.errors import (
    LIGHTRAG_STARTUP_FAILED,
    LIGHTRAG_UNAVAILABLE,
    QUERY_TIMEOUT,
    emit_error,
)

LIGHTRAG_URL = os.environ.get("LIGHTRAG_URL", "http://localhost:9621")
LIGHTRAG_API_KEY = os.environ.get("LIGHTRAG_API_KEY", "")
_QUERY_TIMEOUT_S = float(os.environ.get("LIGHTRAG_QUERY_TIMEOUT_MS", "5000")) / 1000.0
_ALLOWED_MODES = frozenset({"hybrid", "mix", "local", "global", "naive"})
_LIGHTRAG_PORT = int(os.environ.get("LIGHTRAG_PORT", "9621"))
_LIGHTRAG_STARTUP_TIMEOUT_S = 30


@asynccontextmanager
async def _lifespan(app):
    lightrag_dir = Path.cwd() / ".lightrag"
    lightrag_dir.mkdir(exist_ok=True)
    print(f"[aidd-kos] LightRAG embedded 起動: {lightrag_dir}", flush=True)

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "lightrag.api.lightrag_server",
            "--host",
            "127.0.0.1",
            "--port",
            str(_LIGHTRAG_PORT),
            "--working-dir",
            str(lightrag_dir),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    health_url = f"http://127.0.0.1:{_LIGHTRAG_PORT}/health"
    started = False
    for _ in range(_LIGHTRAG_STARTUP_TIMEOUT_S):
        if proc.poll() is not None:
            break
        try:
            urllib.request.urlopen(health_url, timeout=1)
            started = True
            break
        except (urllib.error.URLError, OSError):
            await asyncio.sleep(1)

    if not started:
        proc.terminate()
        emit_error(
            LIGHTRAG_STARTUP_FAILED,
            "LightRAG の起動に失敗しました。ポート競合・依存関係の確認を行ってください。",
        )
        raise RuntimeError("LIGHTRAG_STARTUP_FAILED")

    print("[aidd-kos] LightRAG 起動完了", flush=True)
    try:
        yield
    finally:
        print("[aidd-kos] LightRAG 停止中...", flush=True)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
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
        from aidd_kos.errors import INVALID_MODE

        emit_error(INVALID_MODE, f"有効な mode: {', '.join(sorted(_ALLOWED_MODES))}")
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
        async with httpx.AsyncClient(timeout=_QUERY_TIMEOUT_S) as client:
            resp = await client.post(
                f"{LIGHTRAG_URL}/documents/list",
                json={"limit": min(limit, 100)},
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

    lr = data["lightrag"]
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

    # AC-F03-02: インデックス日時・ドキュメント数を含める
    lr_detail = lr["status"]
    if lr.get("indexed_at"):
        lr_detail += f" (indexed: {lr['indexed_at']}, docs: {lr.get('doc_count', 0)})"

    lines = [
        f"LightRAG:   {lr_detail}",
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
