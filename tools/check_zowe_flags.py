"""Confere se cada comando e flag que o zTractor gera existe no Zowe CLI instalado.

Uso: python tools/check_zowe_flags.py
Roda `zowe <grupo> <acao> <objeto> --help` para cada acao do catalogo.
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ztractor.actions import ACTIONS, build  # noqa: E402
from ztractor.zowe import find_zowe  # noqa: E402

SAMPLE = {
    "target": "HLQ.TEST", "to": "HLQ.TEST2", "file": "x.txt", "dir": "out", "content": "x",
    "command": "D T", "spool_id": "2", "text": "ABC", "owner": "U", "prefix": "P*",
    "range": "0,10", "encoding": "IBM-1047", "binary": "sim", "recfm": "FB", "lrecl": 80,
    "blksize": 27920, "size": "5CYL", "volume": "VOL001", "storclas": "S", "mgmtclas": "M",
    "dataclas": "D", "replace": "sim", "recursive": "sim", "mode": "rwxr-xr-x", "console": "C",
    "keyword": "IEE", "system": "S0W1", "start": "2026-10-12T08:00:00Z", "direction": "forward",
    "account": "ACCT", "tso_profile": "tso", "profile": "lab", "jcl_symbols": "A=1",
    "pattern": "A*", "exec_data": "sim",
}


def main() -> int:
    zowe = find_zowe()
    cache = {}
    bad = 0
    for name, act in sorted(ACTIONS.items()):
        task = dict(SAMPLE, action=name)
        if name == "ds.create":
            task.pop("like", None)
        if name.startswith("uss.") or name == "jobs.submit":
            task["target"] = "/u/test/x"
        _, args, _ = build(task)
        path = []
        for a in args:
            if a.startswith("-") or len(path) == 3:
                break
            path.append(a)
        if name.startswith("setup."):
            path = args[:3]
        key = tuple(path)
        if key not in cache:
            out = subprocess.run([zowe, *path, "--help"], capture_output=True, text=True)
            cache[key] = out.stdout + out.stderr
        text = cache[key]
        if "Command failed" in text or "Unknown" in text and "USAGE" not in text:
            print(f"ERRO {name}: comando inexistente: zowe {' '.join(path)}")
            bad += 1
            continue
        for flag in [a for a in args if a.startswith("--")]:
            if not re.search(rf"(^|\s){re.escape(flag)}(\s|$|\|)", text, re.M):
                print(f"ERRO {name}: flag {flag} nao existe em zowe {' '.join(path)}")
                bad += 1
        print(f"ok   {name}: zowe {' '.join(path)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
