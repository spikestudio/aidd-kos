"""aidd-kos デフォルト設定値"""

from __future__ import annotations

import os

# LightRAG に渡す LLM/Embedding バインディングのデフォルト値。
# ユーザーは OPENAI_API_KEY のみ設定すれば動作する。
# 変更時はこのファイル 1 箇所のみ更新すること。
LIGHTRAG_ENV_DEFAULTS: dict[str, str] = {
    "LLM_BINDING": "openai",
    "LLM_MODEL": "gpt-4o-mini",
    "EMBEDDING_BINDING": "openai",
    "EMBEDDING_MODEL": "text-embedding-3-small",
}


def create_lightrag_instance(working_dir: str):  # type: ignore[return]
    """LightRAG インスタンスを生成する（OpenAI バインディング）。
    OPENAI_API_KEY が必要。LLM_MODEL・EMBEDDING_MODEL は環境変数またはデフォルト値を使用する。
    注: openai_embed は既に EmbeddingFunc インスタンスのため、二重ラップ禁止。
    注: lightrag-hku 1.5.1+ は llm_model_func 呼び出し時に model= をキーワードで渡す場合がある。
        functools.partial(model=...) を使うと二重指定エラー（#55）になるため、クロージャを使用する。
    """
    from lightrag import LightRAG
    from lightrag.llm.openai import openai_complete_if_cache, openai_embed

    llm_model = os.environ.get("LLM_MODEL", LIGHTRAG_ENV_DEFAULTS["LLM_MODEL"])

    async def _llm_func(*args: object, **kwargs: object) -> str:
        # LightRAG が model= をキーワードで渡してくる場合に備えて除去し、
        # 位置引数として正確に渡す
        kwargs.pop("model", None)
        return await openai_complete_if_cache(llm_model, *args, **kwargs)  # type: ignore[arg-type]

    return LightRAG(
        working_dir=working_dir,
        llm_model_func=_llm_func,
        llm_model_name=llm_model,
        embedding_func=openai_embed,
    )
