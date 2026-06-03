"""ユニットテスト: aidd_kos.errors (ADR-001 エラーコード体系)"""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch

from aidd_kos.errors import (
    CODEGRAPH_UNAVAILABLE,
    LIGHTRAG_UNAVAILABLE,
    MISE_NOT_FOUND,
    OPENAI_API_KEY_MISSING,
    emit_error,
)


def test_ac_f01_05_unit_mise_not_found_constant() -> None:
    """AC-F01-05: Unit - MISE_NOT_FOUND 定数が ADR-001 命名規則に準拠している"""
    assert MISE_NOT_FOUND == "MISE_NOT_FOUND"


def test_ac_f01_06_unit_openai_key_missing_constant() -> None:
    """AC-F01-06: Unit - OPENAI_API_KEY_MISSING 定数が ADR-001 命名規則に準拠している"""
    assert OPENAI_API_KEY_MISSING == "OPENAI_API_KEY_MISSING"


def test_unit_lightrag_unavailable_constant() -> None:
    """Unit - LIGHTRAG_UNAVAILABLE 定数が ADR-001 命名規則に準拠している（Epic #2 との整合）"""
    assert LIGHTRAG_UNAVAILABLE == "LIGHTRAG_UNAVAILABLE"


def test_unit_codegraph_unavailable_constant() -> None:
    """Unit - CODEGRAPH_UNAVAILABLE 定数が ADR-001 命名規則に準拠している"""
    assert CODEGRAPH_UNAVAILABLE == "CODEGRAPH_UNAVAILABLE"


def test_ac_f01_05_unit_emit_error_writes_to_stderr() -> None:
    """AC-F01-05: Unit - emit_error() がエラーコードを stderr に出力する"""
    with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
        emit_error(MISE_NOT_FOUND, "mise をインストールしてください: https://mise.jdx.dev")
        output = mock_stderr.getvalue()
    assert MISE_NOT_FOUND in output


def test_ac_f01_05_unit_emit_error_includes_remediation() -> None:
    """AC-F01-05: Unit - emit_error() が remediation を stderr に含める"""
    remediation = "mise をインストールしてください: https://mise.jdx.dev"
    with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
        emit_error(MISE_NOT_FOUND, remediation)
        output = mock_stderr.getvalue()
    assert remediation in output


def test_unit_emit_error_does_not_leak_api_key() -> None:
    """Unit - emit_error() が秘密情報（API キー）をマスクして出力する"""
    with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
        emit_error(OPENAI_API_KEY_MISSING, "sk-secret-key-12345 を .env に設定してください")
        output = mock_stderr.getvalue()
    assert "sk-secret-key-12345" not in output
