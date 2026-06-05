"""aidd-kos デフォルト設定値"""

from __future__ import annotations

# LightRAG に渡す LLM/Embedding バインディングのデフォルト値。
# ユーザーは OPENAI_API_KEY のみ設定すれば動作する。
# 変更時はこのファイル 1 箇所のみ更新すること。
LIGHTRAG_ENV_DEFAULTS: dict[str, str] = {
    "LLM_BINDING": "openai",
    "LLM_MODEL": "gpt-4o-mini",
    "EMBEDDING_BINDING": "openai",
    "EMBEDDING_MODEL": "text-embedding-3-small",
}
