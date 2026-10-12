"""Executa um Plan: resolve variaveis, monta o comando, confirma e roda."""

from __future__ import annotations

import os
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from . import actions as A
from .inputs import Plan, VAR_RE, resolve, substitute
from .zowe import ZoweRunner

# estados de cada tarefa no resultado
OK = "ok"
FALHOU = "falhou"
PLANEJADO = "planejado"
PULADO = "pulado"
INVALIDO = "invalido"


@dataclass
class TaskResult:
    index: int
    action: str
    target: str
    risk: str
    status: str
    command: str = ""
    exit_code: Optional[int] = None
    message: str = ""
    seconds: float = 0.0
    data: object = None
    task: dict = field(default_factory=dict)

    def as_row(self) -> dict:
        return {
            "n": self.index,
            "action": self.action,
            "target": self.target,
            "risk": self.risk,
            "status": self.status,
            "exit_code": self.exit_code,
            "message": self.message,
            "command": self.command,
            "seconds": round(self.seconds, 2),
        }


def _quote(arg: str) -> str:
    return f'"{arg}"' if any(c in arg for c in " ()*'$&|;<>") else arg


def _render_local_jcl(path: str, variables: dict) -> str:
    """JCL local com ${VAR} vira um arquivo temporario ja substituido."""
    text = Path(path).read_text(encoding="utf-8")
    if not VAR_RE.search(text):
        return path
    rendered = substitute(text, variables)
    fd, tmp = tempfile.mkstemp(prefix="ztractor-", suffix=".jcl")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(rendered)
    return tmp


def default_confirm(result: TaskResult) -> bool:
    if not sys.stdin.isatty():
        return False
    answer = input(f"[{result.risk}] {result.command}\nExecutar? (s/N) ").strip().lower()
    return answer in ("s", "sim", "y", "yes")


def run_plan(
    plan: Plan,
    runner: Optional[ZoweRunner] = None,
    dry_run: bool = False,
    yes: bool = False,
    stop_on_error: bool = False,
    profile: Optional[str] = None,
    confirm: Callable[[TaskResult], bool] = default_confirm,
    log: Callable[[str], None] = lambda s: print(s, file=sys.stderr),
) -> List[TaskResult]:
    runner = runner or ZoweRunner()
    results: List[TaskResult] = []
    temp_files: List[str] = []
    try:
        for i, raw in enumerate(plan.tasks, 1):
            action = str(raw.get("action", "")).strip().lower()
            target = str(raw.get("target", raw.get("command", "")) or "")
            try:
                task = resolve(raw, plan.vars)
                if profile and not task.get("profile"):
                    task["profile"] = profile
                # arquivo local com ${VAR}: submit sempre substitui; upload so com render=sim
                key = "target" if action == "jobs.submit" else "file"
                wants = action == "jobs.submit" or (
                    action in ("ds.upload", "uss.upload") and A.as_bool(task.get("render")))
                if wants and not dry_run and Path(str(task.get(key, ""))).is_file():
                    src = str(task[key])
                    rendered = _render_local_jcl(src, plan.vars)
                    if rendered != src:
                        temp_files.append(rendered)
                        task[key] = rendered
                        if action == "jobs.submit":
                            task.setdefault("source", "local")
                act, args, stdin = A.build(task)
                target = str(task.get("target", task.get("command", "")) or "")
                risk = act.risk_for(task)
            except (A.TaskError, KeyError, OSError) as exc:
                res = TaskResult(i, action, target, "-", INVALIDO, message=str(exc).strip("'\""), task=raw)
                results.append(res)
                log(f"[{i}] {action} {target}: {res.message}")
                if stop_on_error:
                    break
                continue

            res = TaskResult(i, action, target, risk, PLANEJADO, task=raw,
                             command=" ".join(_quote(a) for a in runner.command_line(args)))
            if dry_run:
                results.append(res)
                log(f"[{i}] ({risk}) {res.command}")
                continue
            if risk == A.DESTRUTIVA and not yes and not confirm(res):
                res.status = PULADO
                res.message = "acao destrutiva sem confirmacao; use --yes depois de revisar o plano"
                results.append(res)
                log(f"[{i}] pulado: {res.command}")
                continue

            started = time.time()
            try:
                z = runner.run(args, stdin=stdin)
            except Exception as exc:  # zowe ausente, timeout
                res.status, res.message = FALHOU, str(exc)
            else:
                res.status = OK if z.success else FALHOU
                res.exit_code = z.exit_code
                res.message = (z.message or z.stderr or "").strip()[:2000]
                res.data = z.data if z.data is not None else (z.stdout or None)
            res.seconds = time.time() - started
            results.append(res)
            log(f"[{i}] {res.status}: {res.command}")
            if stop_on_error and res.status != OK:
                break
    finally:
        for tmp in temp_files:
            try:
                os.remove(tmp)
            except OSError:
                pass
    return results
