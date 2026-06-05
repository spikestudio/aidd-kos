"""LightRAG サーバーをバックグラウンドプロセスとして起動する。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from aidd_kos.config import LIGHTRAG_ENV_DEFAULTS

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
        sys.executable,
        "-m",
        "lightrag.api.lightrag_server",
        "--host",
        "127.0.0.1",
        "--port",
        str(LIGHTRAG_PORT),
        "--working-dir",
        str(LIGHTRAG_DIR),
    ]

    # LightRAG に渡す環境変数: 未設定の場合は OpenAI バインディングをデフォルトとして補完
    env = os.environ.copy()
    for k, v in LIGHTRAG_ENV_DEFAULTS.items():
        env.setdefault(k, v)

    log_file = LIGHTRAG_DIR / "server.log"
    with open(log_file, "a") as log_fp:
        proc = subprocess.Popen(
            cmd,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            env=env,
        )

    PID_FILE.write_text(str(proc.pid))
    print(f"[aidd-kos] LightRAG サーバーを起動しました (PID: {proc.pid})")
    print(f"[aidd-kos] ログ: {log_file}")
    print(f"[aidd-kos] エンドポイント: http://127.0.0.1:{LIGHTRAG_PORT}")


if __name__ == "__main__":
    main()
