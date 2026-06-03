"""スモークテスト — モジュールのインポート可能性を確認する。"""

from __future__ import annotations


def test_mcp_server_importable() -> None:
    import mcp_server.server  # noqa: F401
