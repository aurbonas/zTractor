#!/usr/bin/env python3
"""Zowe falso para testes: registra a chamada e devolve JSON no formato --rfj."""
import json
import os
import sys

args = sys.argv[1:]
stdin = "" if sys.stdin.isatty() else sys.stdin.read()
log = os.environ.get("FAKE_ZOWE_LOG")
if log:
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"args": args, "stdin": stdin}) + "\n")

if "FAIL" in " ".join(args):
    print(json.dumps({"success": False, "exitCode": 1, "message": "falha simulada", "stdout": "", "stderr": "erro", "data": None}))
    sys.exit(1)

data = None
if args[:3] == ["zos-jobs", "list", "jobs"]:
    data = [{"jobname": "DAILY01", "jobid": "JOB00001", "owner": "Z1", "status": "OUTPUT", "retcode": "CC 0000"}]
elif args[:3] == ["zos-files", "list", "data-set"]:
    data = {"apiResponse": {"items": [{"dsname": "Z1.JCL", "dsorg": "PO", "recfm": "FB", "lrecl": "80"}]}}
elif args[:3] == ["zos-files", "view", "data-set"]:
    data = "//JOB1 JOB\n//S1 EXEC PGM=IEFBR14\n"
print("Aviso qualquer antes do JSON")
print(json.dumps({"success": True, "exitCode": 0, "message": "ok", "stdout": "", "stderr": "", "data": data}))
