"""E2E テスト共通 fixtures"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def lightrag_index_ready(tmp_path_factory):
    """全 E2E テストでインデックスチェックを PASS させる。
    conftest 専用ディレクトリに .lightrag/ を作成し Path.cwd() をモック化する。
    AC-F15-02 のような「インデックス未構築」テストは patch("mcp_server.server.Path")
    で Path クラス全体を上書きするため、このモックより優先される。
    """
    own_tmp = tmp_path_factory.mktemp("lightrag_index")
    lightrag_dir = own_tmp / ".lightrag"
    lightrag_dir.mkdir()
    (lightrag_dir / "graph_chunk_entity_relation.graphml").write_text("<graphml/>")
    with patch("mcp_server.server.Path.cwd", return_value=own_tmp):
        yield own_tmp
