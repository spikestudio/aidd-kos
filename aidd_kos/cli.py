"""aidd-kos CLI — Typer エントリポイント"""

from __future__ import annotations

import json
from importlib.metadata import version as pkg_version
from pathlib import Path

import typer

app = typer.Typer(help="Agentic Knowledge OS — ナレッジ基盤の構築・管理")


def _version_callback(value: bool) -> None:
    if value:
        v = pkg_version("aidd-kos")
        typer.echo(f"aidd-kos {v}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool | None = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="バージョン番号を表示して終了する",
    ),
) -> None:
    """Agentic Knowledge OS — ナレッジ基盤の構築・管理"""


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
    from aidd_kos.index import IndexOrchestrator

    target = path or Path.cwd()
    typer.echo(f"[aidd-kos] 差分インデックス: {target}")
    idx = IndexOrchestrator(project_dir=target)
    result = idx.run()
    typer.echo(
        f"[aidd-kos] 差分モード: 追加 {result['new_count']} 件・"
        f"更新 {result['updated_count']} 件・削除 0 件・"
        f"スキップ {result['skip_count']} 件 ({result['elapsed_seconds']:.1f}s)"
    )


@app.command()
def status(
    output_json: bool = typer.Option(False, "--json", help="JSON 形式で出力する"),
) -> None:
    """全ナレッジエンジンの状態を確認する"""
    from aidd_kos.status import StatusChecker

    checker = StatusChecker()
    data = checker.check()

    if output_json:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    lr = data["lightrag"]
    cg = data["codegraph"]
    typer.echo(f"  LightRAG:   {lr['status']}")
    typer.echo(f"  CodeGraph:  {cg['status']} (nodes: {cg.get('node_count', 0)})")


@app.command()
def serve() -> None:
    """MCP サーバーを起動する（Claude Code が内部で呼び出す）"""
    from mcp_server.server import main

    main()


if __name__ == "__main__":
    app()
