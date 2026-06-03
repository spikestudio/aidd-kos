"""エラーコード定数と出力関数 (ADR-001: {COMPONENT}_{ERROR_TYPE} 形式)"""

from __future__ import annotations

import re
import sys

# エラーコード定数 (ADR-001)
MISE_NOT_FOUND = "MISE_NOT_FOUND"
OPENAI_API_KEY_MISSING = "OPENAI_API_KEY_MISSING"
LIGHTRAG_UNAVAILABLE = "LIGHTRAG_UNAVAILABLE"
CODEGRAPH_UNAVAILABLE = "CODEGRAPH_UNAVAILABLE"
CLAUDE_SETTINGS_TOO_LARGE = "CLAUDE_SETTINGS_TOO_LARGE"
PORT_IN_USE = "PORT_IN_USE"
QUERY_TIMEOUT = "QUERY_TIMEOUT"
INVALID_MODE = "INVALID_MODE"
LIGHTRAG_STARTUP_FAILED = "LIGHTRAG_STARTUP_FAILED"

# API キーのパターン（ログマスク用）
_SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9\-_]{10,}")


def _mask_secrets(text: str) -> str:
    return _SECRET_PATTERN.sub("sk-***", text)


def emit_error(code: str, remediation: str) -> None:
    """エラーコードと対処方法を stderr に出力する。秘密情報はマスクする。"""
    masked = _mask_secrets(remediation)
    print(f"[aidd-kos] ERROR: {code}", file=sys.stderr)
    print(f"[aidd-kos] → {masked}", file=sys.stderr)
