"""Documento de texto de entrada.

Uma tarefa por linha: a acao, depois o alvo, depois parametros chave=valor.
Valores com espacos vao entre aspas. Linhas com # sao comentarios.
`set NOME=valor` define uma variavel.

    set HLQ=Z63181
    ds.list ${HLQ}.**
    jobs.submit ${HLQ}.JCL(DAILY01) wait=sim
    console.issue command="D A,L"
"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Dict, List, Tuple


def parse_text(text: str) -> Tuple[Dict[str, str], List[dict]]:
    variables: Dict[str, str] = {}
    tasks: List[dict] = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line, posix=True)
        except ValueError as exc:
            raise ValueError(f"linha {number}: {exc}") from None
        head, rest = parts[0], parts[1:]
        if head.lower() == "set":
            for item in rest:
                if "=" not in item:
                    raise ValueError(f"linha {number}: use set NOME=valor")
                k, v = item.split("=", 1)
                variables[k.strip()] = v
            continue
        task = {"action": head, "line": number}
        for item in rest:
            if "=" in item and not item.startswith("/") and item.split("=", 1)[0].isidentifier():
                k, v = item.split("=", 1)
                task[k] = v
            elif "target" not in task:
                task["target"] = item
            else:
                raise ValueError(f"linha {number}: valor solto '{item}'; use chave=valor")
        tasks.append(task)
    return variables, tasks


def read_text(path: Path) -> Tuple[Dict[str, str], List[dict]]:
    return parse_text(path.read_text(encoding="utf-8-sig"))
