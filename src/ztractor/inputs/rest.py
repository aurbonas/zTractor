"""API REST externa como entrada e como destino dos resultados.

A API devolve JSON no formato comum (lista de tarefas ou {"vars", "tasks"}).
Cabecalhos aceitam ${VAR} do ambiente, para o token nao ficar na linha de comando:
    --header "Authorization: Bearer ${API_TOKEN}"
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple

import requests

from .structured import plan_from_obj

ENV_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def expand_env(value: str) -> str:
    def repl(m):
        name = m.group(1)
        if name not in os.environ:
            raise KeyError(f"variavel de ambiente nao definida: {name}")
        return os.environ[name]

    return ENV_RE.sub(repl, value)


def _headers(headers: Dict[str, str]) -> Dict[str, str]:
    return {k: expand_env(v) for k, v in headers.items()}


def read_rest(url: str, headers: Dict[str, str], timeout: int = 60) -> Tuple[Dict[str, str], List[dict]]:
    resp = requests.get(url, headers=_headers(headers), timeout=timeout)
    resp.raise_for_status()
    return plan_from_obj(resp.json())


def post_results(url: str, results: List[dict], headers: Dict[str, str], timeout: int = 60) -> int:
    resp = requests.post(url, json={"results": results}, headers=_headers(headers), timeout=timeout)
    resp.raise_for_status()
    return resp.status_code
