"""ユニットテスト: Feature #14 - _lifespan 内部ロジックと関連定数
(docs/spec/embedded-startup.md Feature F-01)
"""

from __future__ import annotations

import subprocess
import urllib.error
from io import StringIO
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


def test_unit_lightrag_port_default_is_9621():
    """Unit - _LIGHTRAG_PORT が LIGHTRAG_PORT 環境変数未設定時に 9621 になっている"""
    assert srv._LIGHTRAG_PORT == 9621


# ── ヘルスチェックループ ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f14_02_unit_no_sleep_when_health_check_succeeds_immediately():
    """AC-F14-02: Unit - ヘルスチェックが 1 回目で成功するとスリープなしで起動完了する（30 秒未満）"""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.wait.return_value = None
    sleep_mock = AsyncMock()

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", return_value=MagicMock()),
        patch("asyncio.sleep", sleep_mock),
    ):
        async with srv._lifespan(None):
            pass

    sleep_mock.assert_not_called()


@pytest.mark.asyncio
async def test_ac_f14_03b_unit_health_check_retries_exactly_30_times_on_timeout():
    """AC-F14-03b: Unit - ヘルスチェックが 30 回連続失敗するとタイムアウトエラーになる"""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.wait.return_value = None
    urlopen_call_count = 0

    def always_failing_urlopen(url, timeout=None):
        nonlocal urlopen_call_count
        urlopen_call_count += 1
        raise urllib.error.URLError("connection refused")

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", side_effect=always_failing_urlopen),
        patch("asyncio.sleep"),
        patch("sys.stderr", new_callable=StringIO),
        pytest.raises(RuntimeError, match="LIGHTRAG_STARTUP_FAILED"),
    ):
        async with srv._lifespan(None):
            pass

    assert urlopen_call_count == srv._LIGHTRAG_HEALTH_CHECK_RETRIES  # S-5: 定数と連動


@pytest.mark.asyncio
async def test_ac_f14_03a_unit_urlopen_not_called_when_proc_exits_immediately():
    """AC-F14-03a: Unit - proc.poll() が終了コードを返すと urlopen を呼ばずにループを脱出してエラーになる"""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = 1
    mock_proc.wait.return_value = None
    urlopen_mock = MagicMock()

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", urlopen_mock),
        patch("asyncio.sleep"),
        patch("sys.stderr", new_callable=StringIO),
        pytest.raises(RuntimeError, match="LIGHTRAG_STARTUP_FAILED"),
    ):
        async with srv._lifespan(None):
            pass

    urlopen_mock.assert_not_called()


# ── シャットダウンシーケンス ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f14_04a_unit_terminate_then_wait_on_normal_stop():
    """AC-F14-04a: Unit - 正常停止時に proc.terminate() の後に proc.wait() が呼ばれる"""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    call_order: list[str] = []

    mock_proc.terminate.side_effect = lambda: call_order.append("terminate")
    mock_proc.wait.side_effect = lambda timeout=None: call_order.append(f"wait(timeout={timeout})")

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", return_value=MagicMock()),
        patch("asyncio.sleep"),
    ):
        async with srv._lifespan(None):
            pass

    assert call_order[0] == "terminate"
    assert any("wait" in c for c in call_order)


@pytest.mark.asyncio
async def test_ac_f14_04a_unit_kill_then_wait_when_proc_wait_times_out():
    """AC-F14-04a: Unit - proc.wait(timeout=5) がタイムアウトした場合に proc.kill() → proc.wait() の順で呼ばれる"""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    call_order: list[str] = []
    wait_call_count = 0

    def wait_side_effect(timeout=None):
        nonlocal wait_call_count
        wait_call_count += 1
        call_order.append(f"wait({wait_call_count})")
        if timeout is not None:
            raise subprocess.TimeoutExpired(cmd="lightrag", timeout=timeout)

    mock_proc.terminate.side_effect = lambda: call_order.append("terminate")
    mock_proc.wait.side_effect = wait_side_effect
    mock_proc.kill.side_effect = lambda: call_order.append("kill")

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", return_value=MagicMock()),
        patch("asyncio.sleep"),
    ):
        async with srv._lifespan(None):
            pass

    assert "terminate" in call_order
    assert "kill" in call_order
    assert call_order.index("kill") > call_order.index("wait(1)")
    assert wait_call_count == 2


# ── stderr 出力確認 ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac_f14_03a_unit_stderr_contains_startup_failed_on_process_exit():
    """AC-F14-03a: Unit - プロセス即時終了時に stderr へ LIGHTRAG_STARTUP_FAILED が出力される"""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = 1
    mock_proc.wait.return_value = None

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen"),
        patch("asyncio.sleep"),
        patch("sys.stderr", new_callable=StringIO) as mock_stderr,
        pytest.raises(RuntimeError),
    ):
        async with srv._lifespan(None):
            pass

    assert "LIGHTRAG_STARTUP_FAILED" in mock_stderr.getvalue()


@pytest.mark.asyncio
async def test_ac_f14_03b_unit_stderr_contains_startup_failed_on_timeout():
    """AC-F14-03b: Unit - タイムアウト時に stderr へ LIGHTRAG_STARTUP_FAILED が出力される"""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.wait.return_value = None

    with (
        patch("subprocess.Popen", return_value=mock_proc),
        patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")),
        patch("asyncio.sleep"),
        patch("sys.stderr", new_callable=StringIO) as mock_stderr,
        pytest.raises(RuntimeError),
    ):
        async with srv._lifespan(None):
            pass

    assert "LIGHTRAG_STARTUP_FAILED" in mock_stderr.getvalue()
