"""aidd-kos ドキュメントインデックス更新。"""
from __future__ import annotations
import asyncio
import os
import sys
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LIGHTRAG_DIR = PROJECT_ROOT / ".lightrag"
LIGHTRAG_PORT = 9621
IGNORE_FILE = PROJECT_ROOT / ".lightrag-ignore"


def _load_ignore_patterns() -> list[str]:
    """`.lightrag-ignore` から除外パターンを読み込む。"""
    if not IGNORE_FILE.exists():
        return []
    lines = IGNORE_FILE.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def _should_ignore(path: Path, patterns: list[str]) -> bool:
    """パスが除外パターンに一致するか判定する。"""
    path_str = str(path)
    for pattern in patterns:
        # ディレクトリパターン（末尾 `/`）はパス内に含まれるかで判定
        if pattern.endswith("/"):
            if pattern.rstrip("/") in path_str:
                return True
        elif pattern in path_str:
            return True
    return False


def _collect_files(root: Path, patterns: list[str]) -> list[Path]:
    """インデックス対象ファイルを収集する。"""
    files: list[Path] = []
    for ext in ("*.md", "*.txt"):
        for f in root.rglob(ext):
            if not _should_ignore(f, patterns):
                files.append(f)
    return files


def _is_server_running() -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{LIGHTRAG_PORT}/health", timeout=2)
        return True
    except Exception:
        return False


def _scan_via_rest(input_dir: str) -> None:
    """REST API 経由でディレクトリをスキャン・インデックス。"""
    payload = json.dumps({"input_dir": input_dir}).encode()
    req = urllib.request.Request(
        f"http://localhost:{LIGHTRAG_PORT}/documents/scan",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=30)


async def _index_via_python_api(files: list[Path]) -> None:
    """Python API 経由で直接インデックス。サーバー未起動時に使用する。"""
    from lightrag import LightRAG
    from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
    from lightrag.utils import EmbeddingFunc

    rag = LightRAG(
        working_dir=str(LIGHTRAG_DIR),
        llm_model_func=gpt_4o_mini_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=8192,
            func=openai_embed,
        ),
    )
    await rag.initialize_storages()

    texts = [f.read_text(encoding="utf-8", errors="ignore") for f in files]
    ids = [str(f.relative_to(PROJECT_ROOT)) for f in files]
    paths = [str(f.relative_to(PROJECT_ROOT)) for f in files]

    await rag.ainsert(texts, ids=ids, file_paths=paths)
    await rag.finalize_storages()


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("[aidd-kos] エラー: OPENAI_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    target_dir = sys.argv[1] if len(sys.argv) > 1 else str(PROJECT_ROOT)

    if _is_server_running():
        print("[aidd-kos] サーバー起動中 → REST API でスキャン")
        _scan_via_rest(target_dir)
    else:
        print("[aidd-kos] サーバー未起動 → Python API で直接インデックス")
        ignore_patterns = _load_ignore_patterns()
        root = Path(target_dir)
        files = _collect_files(root, ignore_patterns)

        if not files:
            print("[aidd-kos] インデックス対象ファイルなし")
            return

        print(f"[aidd-kos] {len(files)} ファイルをインデックス中...")
        asyncio.run(_index_via_python_api(files))

    # タイムスタンプ記録
    LIGHTRAG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    (LIGHTRAG_DIR / "last_indexed_at").write_text(ts)
    print(f"[aidd-kos] インデックス完了: {ts}")


if __name__ == "__main__":
    main()
