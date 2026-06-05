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
    def __init__(self, project_dir: Path, *, global_install: bool = False) -> None:
        self.project_dir = project_dir.resolve()
        self.global_install = global_install

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
        """Step 5: MCP エントリを設定ファイルに追加する。
        global_install=True のとき ~/.claude/settings.json に cwd 付きで書き込む（旧動作）。
        global_install=False のとき .claude/settings.local.json に cwd なしで書き込む（デフォルト）。
        """
        home = Path(os.environ.get("HOME", Path.home()))
        if self.global_install:
            settings_path = home / ".claude" / "settings.json"
            entry = {
                "command": "uvx",
                "args": ["aidd-kos@latest", "serve"],
                "cwd": str(self.project_dir),
            }
        else:
            settings_path = self.project_dir / ".claude" / "settings.local.json"
            entry = {
                "command": "uvx",
                "args": ["aidd-kos@latest", "serve"],
            }
            # グローバル設定に既存エントリがある場合は通知（AC-F40-03）
            global_path = home / ".claude" / "settings.json"
            if global_path.exists():
                existing = ClaudeSettings(global_path)._read()
                if "aidd-kos" in existing.get("mcpServers", {}):
                    print(
                        "[aidd-kos] グローバル設定が検出されました。"
                        " ~/.claude/settings.json の aidd-kos エントリは手動で削除することを推奨します。"
                    )
        cs = ClaudeSettings(settings_path)
        cs.add_mcp_entry("aidd-kos", entry)

    def start_lightrag_and_index(self) -> None:
        """Step 6-7: LightRAG in-process 起動 + 初回インデックス（ADR-004）。
        HTTP サーバーは起動しない（ポート不使用）。
        """
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
