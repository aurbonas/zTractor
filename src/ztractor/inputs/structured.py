"""Entradas estruturadas: CSV, JSON e YAML."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple


def plan_from_obj(obj) -> Tuple[Dict[str, str], List[dict]]:
    """Aceita uma lista de tarefas ou {"vars": {...}, "tasks": [...]}."""
    if isinstance(obj, list):
        return {}, [dict(t) for t in obj if isinstance(t, dict)]
    if isinstance(obj, dict):
        tasks = obj.get("tasks")
        if tasks is None and "action" in obj:
            tasks = [obj]
        if not isinstance(tasks, list):
            raise ValueError("JSON/YAML precisa ser uma lista de tarefas ou ter a chave 'tasks'")
        return dict(obj.get("vars") or {}), [dict(t) for t in tasks if isinstance(t, dict)]
    raise ValueError("formato de entrada nao reconhecido")


def read_csv(path: Path) -> Tuple[Dict[str, str], List[dict]]:
    raw = path.read_text(encoding="utf-8-sig")
    try:
        dialect = csv.Sniffer().sniff(raw.splitlines()[0], delimiters=",;\t")
    except (csv.Error, IndexError):
        dialect = csv.excel
    return {}, list(csv.DictReader(raw.splitlines(), dialect=dialect))


def read_json(path: Path) -> Tuple[Dict[str, str], List[dict]]:
    return plan_from_obj(json.loads(path.read_text(encoding="utf-8-sig")))


def read_yaml(path: Path) -> Tuple[Dict[str, str], List[dict]]:
    import yaml

    return plan_from_obj(yaml.safe_load(path.read_text(encoding="utf-8-sig")))
