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
    注: openai_complete_if_cache の第1引数は model。lightrag-hku 1.5.1+ は
        llm_model_func を位置引数で呼ぶため（safe_user_prompt が第1位置引数）、
        partial(model=llm_model) では「got multiple values for argument 'model'」エラーになる（#55）。
        クロージャで model を先頭位置引数として渡すことで衝突を回避する。
    """
    from lightrag import LightRAG
    from lightrag.llm.openai import openai_complete_if_cache, openai_embed

    llm_model = os.environ.get("LLM_MODEL", LIGHTRAG_ENV_DEFAULTS["LLM_MODEL"])

    async def _llm_func(*args: object, **kwargs: object) -> str:
        return await openai_complete_if_cache(llm_model, *args, **kwargs)  # type: ignore[arg-type]

    return LightRAG(
        working_dir=working_dir,
        llm_model_func=_llm_func,
        llm_model_name=llm_model,
        embedding_func=openai_embed,
    )
