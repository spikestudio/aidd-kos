"""LightRAG サーバーを停止する。"""

from __future__ import annotations

import os
import signal
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PID_FILE = PROJECT_ROOT / ".lightrag" / "server.pid"


def main() -> None:
    if not PID_FILE.exists():
        print("[aidd-kos] サーバーは起動していません（PID ファイルなし）")
        return

    pid = int(PID_FILE.read_text().strip())

    try:
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink()
        print(f"[aidd-kos] サーバーを停止しました (PID: {pid})")
    except ProcessLookupError:
        PID_FILE.unlink()
        print(f"[aidd-kos] プロセスが見つかりません (PID: {pid})。PID ファイルを削除しました")
    except PermissionError:
        print(f"[aidd-kos] エラー: プロセス {pid} を停止する権限がありません", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
