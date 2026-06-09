"""ユニットテスト: aidd_kos.config (create_lightrag_instance)

LightRAG との接合部（_llm_func クロージャ）の呼び出し規約を検証する。
外部ライブラリ lightrag-hku の API 変更による回帰を防ぐ。

# バグ #55 の実際の原因（回帰防止のため記録）
# lightrag-hku 1.5.1+ は llm_model_func を位置引数で呼ぶ。
#   use_llm_func(safe_user_prompt, system_prompt=..., ...)
# openai_complete_if_cache の第1引数は model であるため、
#   partial(openai_complete_if_cache, model=llm_model)(safe_user_prompt, ...)
# は「model」を位置引数と keyword 引数の両方で受け取り TypeError になる。
# クロージャで model を先頭位置引数として渡すことで衝突を回避する。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_lightrag_mock():
    """LightRAG インスタンスのモックを生成する。"""
    mock = MagicMock()
    mock.initialize_storages = AsyncMock()
    mock.finalize_storages = AsyncMock()
    return mock


# ── AC: _llm_func はモデルを位置引数として渡す ────────────────────────────────


@pytest.mark.asyncio
async def test_llm_func_passes_model_as_positional_arg(monkeypatch) -> None:
    """_llm_func は model を第1位置引数として openai_complete_if_cache に渡す。"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")

    mock_complete = AsyncMock(return_value="response")
    mock_lightrag_cls = MagicMock(return_value=_make_lightrag_mock())

    with (
        patch("lightrag.LightRAG", mock_lightrag_cls),
        patch("lightrag.llm.openai.openai_complete_if_cache", mock_complete),
    ):
        from aidd_kos.config import create_lightrag_instance

        create_lightrag_instance("/tmp/test")
        llm_func = mock_lightrag_cls.call_args.kwargs["llm_model_func"]

        await llm_func("prompt text")

    # model が第1位置引数として渡されている
    _args, kwargs = mock_complete.call_args
    assert _args[0] == "gpt-4o-mini"
    assert _args[1] == "prompt text"
    assert "model" not in kwargs


@pytest.mark.asyncio
async def test_llm_func_no_double_model_arg_regression(monkeypatch) -> None:
    """#55 回帰防止: partial(model=...) 方式では起きる「multiple values for model」が起きないこと。

    lightrag-hku 1.5.1+ は use_llm_func(safe_user_prompt, ...) と位置引数で呼ぶ。
    openai_complete_if_cache の第1引数は model なので、
    partial(model=llm_model) では safe_user_prompt が model に位置バインドされ衝突する。
    クロージャ方式では llm_model が先頭位置引数のため衝突しない。
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")

    mock_complete = AsyncMock(return_value="response")
    mock_lightrag_cls = MagicMock(return_value=_make_lightrag_mock())

    with (
        patch("lightrag.LightRAG", mock_lightrag_cls),
        patch("lightrag.llm.openai.openai_complete_if_cache", mock_complete),
    ):
        from aidd_kos.config import create_lightrag_instance

        create_lightrag_instance("/tmp/test")
        llm_func = mock_lightrag_cls.call_args.kwargs["llm_model_func"]

        # LightRAG 1.5.1 スタイル: prompt を第1位置引数で渡す（model は来ない）
        await llm_func("safe_user_prompt_text", system_prompt="sys")

    # モデルは先頭位置引数として正しく渡され、二重指定エラーは起きない
    _args, kwargs = mock_complete.call_args
    assert _args[0] == "gpt-4o-mini"
    assert _args[1] == "safe_user_prompt_text"
    assert kwargs.get("system_prompt") == "sys"


@pytest.mark.asyncio
async def test_llm_func_passes_through_other_kwargs(monkeypatch) -> None:
    """system_prompt / history_messages などのキーワード引数は透過的に渡される。"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    mock_complete = AsyncMock(return_value="response")
    mock_lightrag_cls = MagicMock(return_value=_make_lightrag_mock())

    with (
        patch("lightrag.LightRAG", mock_lightrag_cls),
        patch("lightrag.llm.openai.openai_complete_if_cache", mock_complete),
    ):
        from aidd_kos.config import create_lightrag_instance

        create_lightrag_instance("/tmp/test")
        llm_func = mock_lightrag_cls.call_args.kwargs["llm_model_func"]

        await llm_func("prompt", system_prompt="sys", temperature=0.7)

    _args, kwargs = mock_complete.call_args
    assert kwargs.get("system_prompt") == "sys"
    assert kwargs.get("temperature") == 0.7


@pytest.mark.asyncio
async def test_llm_model_env_var_is_respected(monkeypatch) -> None:
    """LLM_MODEL 環境変数が _llm_func のモデル名に反映される。"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4-turbo")

    mock_complete = AsyncMock(return_value="response")
    mock_lightrag_cls = MagicMock(return_value=_make_lightrag_mock())

    with (
        patch("lightrag.LightRAG", mock_lightrag_cls),
        patch("lightrag.llm.openai.openai_complete_if_cache", mock_complete),
    ):
        from aidd_kos.config import create_lightrag_instance

        create_lightrag_instance("/tmp/test")
        llm_func = mock_lightrag_cls.call_args.kwargs["llm_model_func"]
        await llm_func("prompt")

    _args, _ = mock_complete.call_args
    assert _args[0] == "gpt-4-turbo"
