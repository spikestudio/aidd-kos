"""LightRAG サーバーをバックグラウンドプロセスとして起動する。"""
from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LIGHTRAG_DIR = PROJECT_ROOT / ".lightrag"
PID_FILE = LIGHTRAG_DIR / "server.pid"
LIGHTRAG_PORT = 9621


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("[aidd-kos] エラー: OPENAI_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    LIGHTRAG_DIR.mkdir(parents=True, exist_ok=True)

    # 既に起動中かチェック
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, 0)
            print(f"[aidd-kos] サーバーは既に起動中です (PID: {pid})")
            return
        except ProcessLookupError:
            # PID ファイルが古い
            PID_FILE.unlink()

    cmd = [
        sys.executable, "-m", "lightrag.api.lightrag_server",
        "--host", "127.0.0.1",
        "--port", str(LIGHTRAG_PORT),
        "--working-dir", str(LIGHTRAG_DIR),
    ]

    log_file = LIGHTRAG_DIR / "server.log"
    proc = subprocess.Popen(
        cmd,
        stdout=open(log_file, "a"),
        stderr=subprocess.STDOUT,
        env=os.environ.copy(),
    )

    PID_FILE.write_text(str(proc.pid))
    print(f"[aidd-kos] LightRAG サーバーを起動しました (PID: {proc.pid})")
    print(f"[aidd-kos] ログ: {log_file}")
    print(f"[aidd-kos] エンドポイント: http://127.0.0.1:{LIGHTRAG_PORT}")


if __name__ == "__main__":
    main()
