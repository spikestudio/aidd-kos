"""サーバー・インデックスの状態を確認する。"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LIGHTRAG_DIR = PROJECT_ROOT / ".lightrag"
LAST_INDEXED_FILE = LIGHTRAG_DIR / "last_indexed_at"
LIGHTRAG_PORT = 9621

# インデックスが Stale とみなす閾値（秒）
STALE_THRESHOLD_SECONDS = 3600


def _check_server() -> tuple[bool, dict]:
    """サーバーの疎通確認とパイプライン状態を返す。"""
    try:
        with urllib.request.urlopen(f"http://localhost:{LIGHTRAG_PORT}/health", timeout=2) as resp:
            health = json.loads(resp.read())
    except Exception:
        return False, {}

    try:
        with urllib.request.urlopen(
            f"http://localhost:{LIGHTRAG_PORT}/documents/pipeline_status", timeout=2
        ) as resp:
            pipeline = json.loads(resp.read())
    except Exception:
        pipeline = {}

    return True, {**health, **pipeline}


def _determine_status(server_running: bool, pipeline: dict) -> str:
    """状態を判定する。"""
    if not server_running:
        if not LIGHTRAG_DIR.exists() or not LAST_INDEXED_FILE.exists():
            return "Uninitialized"
        return "Ready"  # サーバー停止中でもインデックスが存在すれば Ready

    if pipeline.get("busy", False):
        return "Indexing"

    if not LAST_INDEXED_FILE.exists():
        return "Uninitialized"

    ts_str = LAST_INDEXED_FILE.read_text().strip()
    try:
        last_indexed = datetime.fromisoformat(ts_str).replace(tzinfo=UTC)
        elapsed = (datetime.now(UTC) - last_indexed).total_seconds()
        if elapsed > STALE_THRESHOLD_SECONDS:
            return "Stale"
    except ValueError:
        return "Stale"

    return "Ready"


def main() -> None:
    use_json = "--json" in sys.argv

    server_running, pipeline = _check_server()
    status = _determine_status(server_running, pipeline)

    last_indexed = None
    if LAST_INDEXED_FILE.exists():
        last_indexed = LAST_INDEXED_FILE.read_text().strip()

    if use_json:
        result = {
            "status": status,
            "server_running": server_running,
            "last_indexed_at": last_indexed,
        }
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Status: {status}")
        print(f"サーバー: {'起動中' if server_running else '停止中'}")
        if last_indexed:
            print(f"最終インデックス: {last_indexed} UTC")
        else:
            print("最終インデックス: なし（未インデックス）")


if __name__ == "__main__":
    main()
