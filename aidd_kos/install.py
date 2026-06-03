"""install コマンドのオーケストレーション"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from aidd_kos.claude_settings import ClaudeSettings
from aidd_kos.errors import (
    MISE_NOT_FOUND,
    OPENAI_API_KEY_MISSING,
    emit_error,
)

_GITIGNORE_ENTRIES = [".lightrag/", ".codegraph/"]


class InstallOrchestrator:
    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir.resolve()

    def preflight_check(self) -> None:
        """Step 1: 前提条件チェック（最初に実行して 3 秒以内のエラー出力を保証）"""
        if not shutil.which("mise", path=os.environ.get("PATH")):
            emit_error(
                MISE_NOT_FOUND,
                "mise をインストールしてください: https://mise.jdx.dev",
            )
            sys.exit(1)

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            # .env ファイルも確認
            env_file = self.project_dir / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("OPENAI_API_KEY=") and "=" in line:
                        val = line.split("=", 1)[1].strip()
                        if val and val != "sk-...":
                            return
            emit_error(
                OPENAI_API_KEY_MISSING,
                ".env ファイルに OPENAI_API_KEY を設定してください",
            )
            sys.exit(1)

    def run_mise_install(self) -> None:
        """Step 2: mise install"""
        subprocess.run(["mise", "install"], cwd=self.project_dir, check=True)

    def run_uv_sync(self) -> None:
        """Step 3: uv sync"""
        subprocess.run(["uv", "sync"], cwd=self.project_dir, check=True)

    def init_storage(self) -> None:
        """Step 4: .lightrag/ 初期化 + .codegraph/ 初期化"""
        lightrag_dir = self.project_dir / ".lightrag"
        lightrag_dir.mkdir(exist_ok=True)

        codegraph_dir = self.project_dir / ".codegraph"
        if not codegraph_dir.exists():
            result = subprocess.run(
                ["npx", "@colbymchenry/codegraph", "init", str(self.project_dir)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                # 既存の .codegraph/ がある場合は index にフォールバック
                subprocess.run(
                    ["npx", "@colbymchenry/codegraph", "index", str(self.project_dir)],
                    check=False,
                )
        else:
            subprocess.run(
                ["npx", "@colbymchenry/codegraph", "index", str(self.project_dir)],
                check=False,
            )

    def register_mcp(self) -> None:
        """Step 5: ~/.claude/settings.json に MCP エントリを追加"""
        home = Path(os.environ.get("HOME", Path.home()))
        settings_path = home / ".claude" / "settings.json"
        cs = ClaudeSettings(settings_path)
        cs.add_mcp_entry(
            "aidd-kos",
            {
                "command": "uvx",
                "args": ["aidd-kos@latest", "serve"],
                "cwd": str(self.project_dir),
            },
        )

    def start_lightrag_and_index(self) -> None:
        """Step 6-7: LightRAG 起動 → ドキュメントインデックス構築"""
        import time
        import urllib.request

        lightrag_url = os.environ.get("LIGHTRAG_URL", "http://localhost:9621")
        lightrag_dir = self.project_dir / ".lightrag"

        # Step 6: LightRAG サーバー起動（既に起動中なら再利用）
        server_running = False
        try:
            urllib.request.urlopen(f"{lightrag_url}/health", timeout=2)
            server_running = True
        except (urllib.error.URLError, OSError):
            pass

        if not server_running:
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "lightrag.api.lightrag_server",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "9621",
                    "--working-dir",
                    str(lightrag_dir),
                ],
                env={**os.environ, "LIGHTRAG_WORKING_DIR": str(lightrag_dir)},
            )
            # 起動待ち（最大 30 秒）
            for _ in range(30):
                try:
                    urllib.request.urlopen(f"{lightrag_url}/health", timeout=1)
                    server_running = True
                    break
                except (urllib.error.URLError, OSError):
                    time.sleep(1)

        # Step 7: ドキュメントをインデックス
        if server_running:
            from aidd_kos.index import IndexOrchestrator

            idx = IndexOrchestrator(project_dir=self.project_dir)
            result = idx.run()
            print(f"[aidd-kos] インデックス完了: {result['file_count']} ファイル")

    def update_gitignore(self) -> None:
        """Step 8: .gitignore に .lightrag/ .codegraph/ を追記（重複なし）"""
        gitignore_path = self.project_dir / ".gitignore"
        existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
        lines = existing.splitlines()
        added = False
        for entry in _GITIGNORE_ENTRIES:
            if entry not in lines:
                lines.append(entry)
                added = True
        if added:
            content = "\n".join(lines)
            if content and not content.endswith("\n"):
                content += "\n"
            gitignore_path.write_text(content, encoding="utf-8")

    def print_completion(self) -> None:
        """完了メッセージを表示"""
        print("✅ セットアップ完了。Claude Code を再起動してください")

    def run(self) -> None:
        """install フロー全体を実行する"""
        print("[1/8] 前提確認中...")
        self.preflight_check()
        print("[2/8] mise install 実行中...")
        self.run_mise_install()
        print("[3/8] uv sync 実行中...")
        self.run_uv_sync()
        print("[4/8] ストレージ初期化中...")
        self.init_storage()
        print("[5/8] MCP 登録中...")
        self.register_mcp()
        print("[6/8] LightRAG 起動中...")
        self.start_lightrag_and_index()
        print("[7/8] インデックス構築中（別途 aidd-kos index を実行してください）...")
        print("[8/8] .gitignore 更新中...")
        self.update_gitignore()
        self.print_completion()
