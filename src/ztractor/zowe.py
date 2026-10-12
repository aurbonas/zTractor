"""Execucao do Zowe CLI, igual em Windows e Linux.

Toda chamada usa --rfj (response format JSON), entao o resultado vem com
campos nomeados e nunca e preciso ler colunas de texto.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any, List, Optional


class ZoweNotFound(RuntimeError):
    pass


@dataclass
class ZoweResult:
    command: List[str]
    success: bool
    exit_code: int
    message: str = ""
    stdout: str = ""
    stderr: str = ""
    data: Any = None
    raw: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "command": " ".join(self.command),
            "success": self.success,
            "exit_code": self.exit_code,
            "message": self.message,
            "stderr": self.stderr,
            "data": self.data,
        }


def find_zowe() -> str:
    """Localiza o executavel do Zowe.

    No Windows o npm instala `zowe.cmd`; shutil.which resolve isso via PATHEXT.
    ZTRACTOR_ZOWE permite apontar um caminho fixo.
    """
    explicit = os.environ.get("ZTRACTOR_ZOWE")
    if explicit:
        return explicit
    path = shutil.which("zowe")
    if not path:
        raise ZoweNotFound(
            "Zowe CLI nao encontrado no PATH. Instale com: npm install -g @zowe/cli@zowe-v3-lts"
        )
    return path


def parse_rfj(text: str) -> dict:
    """Le a resposta --rfj. Avisos impressos antes do JSON sao descartados."""
    text = text.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start >= 0:
            try:
                return json.loads(text[start:])
            except json.JSONDecodeError:
                pass
    return {"success": False, "message": "resposta do Zowe nao e JSON", "stdout": text}


class ZoweRunner:
    """Executa `zowe <args> --rfj`.

    profile: nome do perfil zosmf (vira --zosmf-profile); tso_profile idem para TSO.
    """

    def __init__(self, zowe_path: Optional[str] = None, timeout: int = 900):
        self._zowe_path = zowe_path
        self.timeout = timeout

    @property
    def zowe_path(self) -> str:
        if not self._zowe_path:
            self._zowe_path = find_zowe()
        return self._zowe_path

    def command_line(self, args: List[str]) -> List[str]:
        return ["zowe", *args, "--rfj"]

    def run(self, args: List[str], stdin: Optional[str] = None) -> ZoweResult:
        cmd = [self.zowe_path, *args, "--rfj"]
        env = dict(os.environ)
        # sem cores nem prompts interativos: o agente nao tem terminal
        env.setdefault("FORCE_COLOR", "0")
        env.setdefault("ZOWE_SHOW_SECURE_ARGS", "false")
        proc = subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout,
            env=env,
        )
        payload = parse_rfj(proc.stdout)
        success = bool(payload.get("success", proc.returncode == 0)) and proc.returncode == 0
        return ZoweResult(
            command=self.command_line(args),
            success=success,
            exit_code=int(payload.get("exitCode", proc.returncode)),
            message=str(payload.get("message", "") or ""),
            stdout=str(payload.get("stdout", "") or ""),
            stderr=str(payload.get("stderr", "") or proc.stderr or ""),
            data=payload.get("data"),
            raw=payload,
        )
