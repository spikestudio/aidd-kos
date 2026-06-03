"""status コマンドの実装"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request

_LIGHTRAG_HEALTH_URL = "http://localhost:9621/health"


class StatusChecker:
    def check(self) -> dict:
        return {
            "lightrag": self._check_lightrag(),
            "codegraph": self._check_codegraph(),
        }

    def _check_lightrag(self) -> dict:
        try:
            with urllib.request.urlopen(_LIGHTRAG_HEALTH_URL, timeout=3):
                return {"status": "ready"}
        except (urllib.error.URLError, OSError):
            return {"status": "unavailable"}

    def _check_codegraph(self) -> dict:
        try:
            result = subprocess.run(
                ["npx", "@colbymchenry/codegraph", "status", "--json", "."],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return {"status": "unavailable", "node_count": 0}
            data = json.loads(result.stdout)
            if data.get("initialized"):
                return {"status": "ready", "node_count": data.get("nodeCount", 0)}
            return {"status": "unavailable", "node_count": 0}
        except Exception:
            return {"status": "unavailable", "node_count": 0}
