"""コマンドラインから LightRAG にクエリを実行する。"""
from __future__ import annotations
import json
import sys
import urllib.request

LIGHTRAG_PORT = 9621


def _is_server_running() -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{LIGHTRAG_PORT}/health", timeout=2)
        return True
    except Exception:
        return False


def _query(q: str, mode: str = "hybrid") -> dict:
    payload = json.dumps({"query": q, "mode": mode, "include_references": True}).encode()
    req = urllib.request.Request(
        f"http://localhost:{LIGHTRAG_PORT}/query",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mode_args = [a for a in sys.argv[1:] if a.startswith("--mode=")]
    mode = mode_args[0].split("=", 1)[1] if mode_args else "hybrid"

    if not args:
        print("使い方: task query -- 'クエリ文字列' [--mode=hybrid|mix|local|global|naive]", file=sys.stderr)
        sys.exit(1)

    query_text = " ".join(args)

    if not _is_server_running():
        print("[aidd-kos] エラー: LightRAG サーバーが起動していません", file=sys.stderr)
        print("[aidd-kos] 起動するには: task server:start", file=sys.stderr)
        sys.exit(1)

    print(f"[aidd-kos] クエリ: {query_text} (mode: {mode})")
    print("---")

    data = _query(query_text, mode)
    answer = data.get("response", "（回答なし）")
    print(answer)

    refs = data.get("references") or []
    sources = [r["file_path"] for r in refs if isinstance(r, dict) and "file_path" in r]
    if sources:
        print("\n参照:")
        for s in sources:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
