"""aidd-kos CLI — Typer エントリポイント"""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Agentic Knowledge OS — ナレッジ基盤の構築・管理")


@app.command()
def install(
    project_dir: Path | None = typer.Option(
        None,
        "--project-dir",
        help="対象プロジェクトのディレクトリ（デフォルト: カレントディレクトリ）",
    ),
) -> None:
    """対象プロジェクトに aidd-kos を全自動セットアップする"""
    from aidd_kos.install import InstallOrchestrator

    target = project_dir or Path.cwd()
    orch = InstallOrchestrator(project_dir=target)
    orch.run()


@app.command()
def index(
    path: Path | None = typer.Argument(
        None, help="インデックス対象パス（デフォルト: カレントディレクトリ）"
    ),
) -> None:
    """プロジェクトのドキュメントを LightRAG にインデックスする"""
    import urllib.request

    target = path or Path.cwd()
    typer.echo(f"[aidd-kos] インデックス構築中: {target}")

    lightrag_url = "http://localhost:9621"
    import json

    payload = json.dumps({"input_dir": str(target)}).encode()
    req = urllib.request.Request(
        f"{lightrag_url}/documents/scan",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=30)
        typer.echo("[aidd-kos] インデックス完了")
    except Exception as e:
        from aidd_kos.errors import LIGHTRAG_UNAVAILABLE, emit_error

        emit_error(LIGHTRAG_UNAVAILABLE, f"task server:start を実行してください: {e}")
        raise typer.Exit(1) from e


@app.command()
def status() -> None:
    """全ナレッジエンジンの状態を確認する"""
    import json
    import subprocess
    import urllib.request

    typer.echo("[aidd-kos] ステータス確認中...")

    # LightRAG
    try:
        urllib.request.urlopen("http://localhost:9621/health", timeout=3)
        lightrag_status = "ready"
    except Exception:
        lightrag_status = "unavailable"

    # CodeGraph
    try:
        result = subprocess.run(
            ["npx", "@colbymchenry/codegraph", "status", "--json", "."],
            capture_output=True,
            text=True,
            timeout=10,
        )
        cg_data = json.loads(result.stdout) if result.returncode == 0 else {}
        codegraph_status = "ready" if cg_data.get("initialized") else "unavailable"
        cg_nodes = cg_data.get("nodeCount", 0)
    except Exception:
        codegraph_status = "unavailable"
        cg_nodes = 0

    typer.echo(f"  LightRAG:   {lightrag_status}")
    typer.echo(f"  CodeGraph:  {codegraph_status} (nodes: {cg_nodes})")


@app.command()
def serve() -> None:
    """MCP サーバーを起動する（Claude Code が内部で呼び出す）"""
    from mcp_server.server import main

    main()


if __name__ == "__main__":
    app()
