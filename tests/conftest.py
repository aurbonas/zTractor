import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent


@pytest.fixture
def fake_zowe(tmp_path, monkeypatch):
    """Aponta o zTractor para o Zowe falso e devolve a funcao que le as chamadas."""
    if os.name == "nt":
        pytest.skip("Zowe falso usa shebang; no Windows rode os testes unitarios")
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("ZTRACTOR_ZOWE", str(HERE / "fake_zowe.py"))
    monkeypatch.setenv("FAKE_ZOWE_LOG", str(log))

    def calls():
        if not log.exists():
            return []
        return [json.loads(l) for l in log.read_text().splitlines()]

    return calls
