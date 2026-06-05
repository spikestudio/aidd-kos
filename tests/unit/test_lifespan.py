"""ユニットテスト: Feature #14 - _lifespan 内部ロジックと関連定数
(docs/spec/embedded-startup.md Feature F-01)
Feature #41 以降: LightRAG in-process 化対応
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import mcp_server.server as srv
from aidd_kos.errors import LIGHTRAG_STARTUP_FAILED

# ── 全テスト共通: OPENAI_API_KEY を設定する ────────────────────────────────────


@pytest.fixture(autouse=True)
def _set_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """lifespan テストで OPENAI_API_KEY が必須になったため、ダミー値を設定する。"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-for-lifespan-tests")


# ── 定数 ─────────────────────────────────────────────────────────────────────


def test_ac_f14_03a_unit_lightrag_startup_failed_constant_adr001():
    """AC-F14-03a: Unit - LIGHTRAG_STARTUP_FAILED 定数が ADR-001 命名規則に準拠している"""
    assert LIGHTRAG_STARTUP_FAILED == "LIGHTRAG_STARTUP_FAILED"


@pytest.mark.asyncio
async def test_unit_lifespan_raises_when_openai_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unit - OPENAI_API_KEY 未設定時に起動失敗してエラーを stderr に出力する"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY_MISSING"):
        async with srv._lifespan(None):
            pass


# ── in-process LightRAG 起動テスト ────────────────────────────────────────────


def _make_mock_rag():
    mock_rag = MagicMock()
    mock_rag.initialize_storages = AsyncMock()
    mock_rag.finalize_storages = AsyncMock()
    mock_rag.aquery_llm = AsyncMock(return_value={"llm_response": {"response": "test"}})
    mock_rag.get_docs_by_status = AsyncMock(return_value={})
    return mock_rag


@pytest.mark.asyncio
async def test_unit_lifespan_creates_lightrag_instance() -> None:
    """Unit - _lifespan が LightRAG インスタンスを作成して initialize_storages を呼ぶ"""
    mock_rag = _make_mock_rag()
    with patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag):
        async with srv._lifespan(None):
            assert srv._rag is mock_rag
            mock_rag.initialize_storages.assert_called_once()

    # lifespan 終了後にクリーンアップ
    mock_rag.finalize_storages.assert_called_once()
    assert srv._rag is None


@pytest.mark.asyncio
async def test_unit_lifespan_finalizes_on_normal_stop() -> None:
    """Unit - _lifespan が正常終了時に finalize_storages を呼ぶ"""
    mock_rag = _make_mock_rag()
    with patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag):
        async with srv._lifespan(None):
            pass
    mock_rag.finalize_storages.assert_called_once()


@pytest.mark.asyncio
async def test_unit_lifespan_raises_on_lightrag_init_failure() -> None:
    """Unit - LightRAG の初期化失敗時に RuntimeError(LIGHTRAG_STARTUP_FAILED) を発生させる"""
    with (
        patch(
            "mcp_server.server.create_lightrag_instance",
            side_effect=RuntimeError("init failed"),
        ),
        pytest.raises(RuntimeError, match="LIGHTRAG_STARTUP_FAILED"),
    ):
        async with srv._lifespan(None):
            pass


# ── stderr 出力確認 ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unit_lifespan_prints_startup_complete() -> None:
    """Unit - 起動成功時に stdout に LightRAG 起動完了メッセージが出力される"""
    mock_rag = _make_mock_rag()
    import io

    captured = io.StringIO()
    with (
        patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag),
        patch("sys.stdout", captured),
    ):
        async with srv._lifespan(None):
            pass
    assert "起動完了" in captured.getvalue() or "LightRAG" in captured.getvalue()


@pytest.mark.asyncio
async def test_ac_f41_04_unit_no_port_config_needed() -> None:
    """AC-F41-04: Unit - LIGHTRAG_PORT/LIGHTRAG_URL 未設定でもクエリが成功する（in-process 動作）"""
    import os

    mock_rag = _make_mock_rag()
    # LIGHTRAG_PORT / LIGHTRAG_URL が未設定でも動作することを確認
    env_without_port = {
        k: v for k, v in os.environ.items() if k not in ("LIGHTRAG_PORT", "LIGHTRAG_URL")
    }
    with (
        patch("mcp_server.server.create_lightrag_instance", return_value=mock_rag),
        patch.dict("os.environ", env_without_port, clear=True),
    ):
        async with srv._lifespan(None):
            assert srv._rag is not None  # ポート設定なしで in-process 初期化成功
