"""Leitura das entradas: Excel, CSV, JSON, YAML, texto e API REST.

Toda entrada vira um Plan: um dict de variaveis e uma lista de tarefas.
Cada tarefa e um dict com `action` e os parametros da acao.

Formato comum (JSON/YAML/REST):
    {"vars": {"HLQ": "Z63181"}, "tasks": [{"action": "ds.list", "target": "${HLQ}.**"}]}
ou apenas a lista de tarefas.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .excel import read_excel
from .rest import read_rest
from .structured import read_csv, read_json, read_yaml, plan_from_obj
from .text import read_text


@dataclass
class Plan:
    vars: Dict[str, str] = field(default_factory=dict)
    tasks: List[dict] = field(default_factory=list)
    source: str = ""


def normalize_task(task: dict) -> dict:
    """Chaves em minusculas, sem espacos; celulas vazias somem."""
    out = {}
    for key, value in task.items():
        if key is None:
            continue
        k = re.sub(r"\s+", "_", str(key).strip().lower())
        if value is None or (isinstance(value, str) and value.strip() == ""):
            continue
        out[k] = value
    return out


def load(source: str, sheet: Optional[str] = None, headers: Optional[Dict[str, str]] = None) -> Plan:
    if re.match(r"^https?://", source, re.I):
        vars_, tasks = read_rest(source, headers or {})
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"entrada nao encontrada: {source}")
        ext = path.suffix.lower()
        if ext in (".xlsx", ".xlsm"):
            vars_, tasks = read_excel(path, sheet)
        elif ext == ".csv":
            vars_, tasks = read_csv(path)
        elif ext == ".json":
            vars_, tasks = read_json(path)
        elif ext in (".yaml", ".yml"):
            vars_, tasks = read_yaml(path)
        else:
            vars_, tasks = read_text(path)
    tasks = [normalize_task(t) for t in tasks]
    tasks = [t for t in tasks if t.get("action") and not str(t.get("action")).startswith("#")]
    for t in tasks:
        t.setdefault("enabled", "sim")
    tasks = [t for t in tasks if _enabled(t)]
    return Plan({str(k): str(v) for k, v in vars_.items()}, tasks, source)


def _enabled(task: dict) -> bool:
    value = str(task.get("enabled", "sim")).strip().lower()
    return value not in ("0", "false", "no", "nao", "não", "n")


VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def substitute(value, variables: Dict[str, str]):
    """Troca ${NOME} pelo valor da variavel do plano ou do ambiente."""
    if not isinstance(value, str):
        return value

    def repl(m):
        name = m.group(1)
        if name in variables:
            return variables[name]
        if name in os.environ:
            return os.environ[name]
        raise KeyError(f"variavel nao definida: {name}")

    return VAR_RE.sub(repl, value)


def resolve(task: dict, variables: Dict[str, str]) -> dict:
    return {k: substitute(v, variables) for k, v in task.items()}


__all__ = ["Plan", "load", "resolve", "substitute", "plan_from_obj"]
