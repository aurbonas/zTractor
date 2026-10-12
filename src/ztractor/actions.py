"""Catalogo de acoes do zTractor e o comando Zowe de cada uma.

Cada tarefa e um dict (uma linha da planilha, um item do JSON, uma linha do
texto) com a chave `action` e os parametros da acao. A acao vira uma lista de
argumentos do Zowe CLI; quem executa e o ZoweRunner.

Risco:
  leitura    - so le; roda sem confirmacao
  escrita    - grava ou submete; roda sem confirmacao, mas aparece no plano
  destrutiva - apaga, cancela, sobrescreve ou fala com o operador; exige --yes
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

LEITURA = "leitura"
ESCRITA = "escrita"
DESTRUTIVA = "destrutiva"

TRUE_WORDS = {"1", "true", "yes", "y", "sim", "s", "x", "verdadeiro"}


class TaskError(ValueError):
    pass


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in TRUE_WORDS


def _get(task: dict, key: str, default=None):
    value = task.get(key, default)
    if value is None:
        return default
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    value = str(value).strip() if not isinstance(value, bool) else value
    return value if value != "" else default


def _req(task: dict, key: str) -> str:
    value = _get(task, key)
    if value is None:
        raise TaskError(f"acao '{task.get('action')}' precisa do campo '{key}'")
    return value


def _opt(args: List[str], flag: str, value) -> None:
    if value is not None and value != "":
        args += [flag, str(value)]


def _flag(args: List[str], flag: str, value) -> None:
    if as_bool(value):
        args.append(flag)


def dsn(value: str) -> str:
    """Nomes de dataset vao em maiusculas; o membro fica entre parenteses."""
    return value.strip().strip("'\"").upper()


Build = Tuple[List[str], Optional[str]]


@dataclass
class Action:
    name: str
    family: str
    risk: str
    summary: str
    required: Tuple[str, ...]
    build: Callable[[dict], Build]
    risk_fn: Optional[Callable[[dict], str]] = None

    def risk_for(self, task: dict) -> str:
        return self.risk_fn(task) if self.risk_fn else self.risk


ACTIONS: Dict[str, Action] = {}


def action(name, family, risk, summary, required=(), risk_fn=None):
    def deco(fn):
        ACTIONS[name] = Action(name, family, risk, summary, tuple(required), fn, risk_fn)
        return fn

    return deco


# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------


@action("setup.check", "setup", LEITURA, "Verifica se o z/OSMF responde com o perfil")
def _setup_check(t):
    return ["zosmf", "check", "status"], None


@action("setup.systems", "setup", LEITURA, "Lista os sistemas definidos no z/OSMF")
def _setup_systems(t):
    return ["zosmf", "list", "systems"], None


# --------------------------------------------------------------------------
# Jobs
# --------------------------------------------------------------------------


@action("jobs.list", "jobs", LEITURA, "Lista jobs por owner e prefixo")
def _jobs_list(t):
    args = ["zos-jobs", "list", "jobs"]
    _opt(args, "--owner", _get(t, "owner"))
    _opt(args, "--prefix", _get(t, "prefix"))
    _flag(args, "--exec-data", _get(t, "exec_data"))
    return args, None


@action("jobs.status", "jobs", LEITURA, "Status e retcode de um JOBID", ["target"])
def _jobs_status(t):
    return ["zos-jobs", "view", "job-status-by-jobid", _req(t, "target").upper()], None


@action("jobs.submit", "jobs", ESCRITA, "Submete JCL de dataset, arquivo local ou arquivo USS", ["target"])
def _jobs_submit(t):
    source = (_get(t, "source") or "").lower()
    target = _req(t, "target")
    if not source:
        if target.startswith("/"):
            source = "uss"
        elif re.search(r"[\\/]|\.jcl$|\.txt$", target, re.I):
            source = "local"
        else:
            source = "dataset"
    if source in ("dataset", "data-set", "ds"):
        args = ["zos-jobs", "submit", "data-set", dsn(target)]
    elif source in ("local", "arquivo", "file", "local-file"):
        args = ["zos-jobs", "submit", "local-file", target]
    elif source == "uss":
        args = ["zos-jobs", "submit", "uss-file", target]
    else:
        raise TaskError(f"source invalido para jobs.submit: {source} (use dataset, local ou uss)")
    _opt(args, "--jcl-symbols", _get(t, "jcl_symbols"))
    if as_bool(_get(t, "wait", "sim")):
        args.append("--wait-for-output")
    return args, None


@action("jobs.spool-list", "jobs", LEITURA, "Lista os DDs do spool de um job", ["target"])
def _jobs_spool_list(t):
    return ["zos-jobs", "list", "spool-files-by-jobid", _req(t, "target").upper()], None


@action("jobs.spool-view", "jobs", LEITURA, "Le um DD do spool pelo id (spool_id)", ["target", "spool_id"])
def _jobs_spool_view(t):
    return ["zos-jobs", "view", "spool-file-by-id", _req(t, "target").upper(), _req(t, "spool_id")], None


@action("jobs.spool-all", "jobs", LEITURA, "Le toda a sysout de um job", ["target"])
def _jobs_spool_all(t):
    return ["zos-jobs", "view", "all-spool-content", _req(t, "target").upper()], None


@action("jobs.download", "jobs", LEITURA, "Baixa a sysout para um diretorio local", ["target"])
def _jobs_download(t):
    args = ["zos-jobs", "download", "output", _req(t, "target").upper()]
    _opt(args, "--directory", _get(t, "dir", "./out"))
    return args, None


@action("jobs.cancel", "jobs", DESTRUTIVA, "Cancela um job em execucao", ["target"])
def _jobs_cancel(t):
    return ["zos-jobs", "cancel", "job", _req(t, "target").upper()], None


@action("jobs.delete", "jobs", DESTRUTIVA, "Purga um job do spool", ["target"])
def _jobs_delete(t):
    return ["zos-jobs", "delete", "job", _req(t, "target").upper()], None


# --------------------------------------------------------------------------
# Datasets
# --------------------------------------------------------------------------


@action("ds.list", "datasets", LEITURA, "Lista datasets por padrao, com atributos", ["target"])
def _ds_list(t):
    pattern = dsn(_req(t, "target"))
    if pattern in ("*", "**") or pattern.startswith("*"):
        raise TaskError("ds.list exige pelo menos o HLQ no padrao (ex.: HLQ.**)")
    args = ["zos-files", "list", "data-set", pattern, "--attributes"]
    _opt(args, "--volume-serial", _get(t, "volume"))
    return args, None


@action("ds.members", "datasets", LEITURA, "Lista membros de uma PDS/PDSE", ["target"])
def _ds_members(t):
    args = ["zos-files", "list", "all-members", dsn(_req(t, "target")), "--attributes"]
    _opt(args, "--pattern", _get(t, "pattern"))
    return args, None


@action("ds.view", "datasets", LEITURA, "Le o conteudo de um dataset ou membro", ["target"])
def _ds_view(t):
    args = ["zos-files", "view", "data-set", dsn(_req(t, "target"))]
    _opt(args, "--range", _get(t, "range"))
    _opt(args, "--encoding", _get(t, "encoding"))
    _flag(args, "--binary", _get(t, "binary"))
    return args, None


@action("ds.download", "datasets", LEITURA, "Baixa dataset ou membro para arquivo local", ["target"])
def _ds_download(t):
    args = ["zos-files", "download", "data-set", dsn(_req(t, "target"))]
    _opt(args, "--file", _get(t, "file"))
    _opt(args, "--encoding", _get(t, "encoding"))
    _flag(args, "--binary", _get(t, "binary"))
    return args, None


@action("ds.download-members", "datasets", LEITURA, "Baixa todos os membros de uma PDS", ["target"])
def _ds_download_members(t):
    args = ["zos-files", "download", "all-members", dsn(_req(t, "target"))]
    _opt(args, "--directory", _get(t, "dir"))
    _opt(args, "--encoding", _get(t, "encoding"))
    _flag(args, "--binary", _get(t, "binary"))
    return args, None


@action("ds.search", "datasets", LEITURA, "Procura texto em datasets", ["target", "text"])
def _ds_search(t):
    return ["zos-files", "search", "data-sets", dsn(_req(t, "target")), _req(t, "text")], None


@action("ds.upload", "datasets", DESTRUTIVA, "Grava arquivo local em dataset ou membro (sobrescreve)", ["target", "file"])
def _ds_upload(t):
    args = ["zos-files", "upload", "file-to-data-set", _req(t, "file"), dsn(_req(t, "target"))]
    _opt(args, "--encoding", _get(t, "encoding"))
    _flag(args, "--binary", _get(t, "binary"))
    return args, None


@action("ds.write", "datasets", DESTRUTIVA, "Grava o texto do campo content em dataset ou membro (sobrescreve)", ["target", "content"])
def _ds_write(t):
    content = _req(t, "content").replace("\\n", "\n")
    if not content.endswith("\n"):
        content += "\n"
    return ["zos-files", "upload", "stdin-to-data-set", dsn(_req(t, "target"))], content


@action("ds.create", "datasets", ESCRITA, "Aloca dataset novo (type: seq, pds, pdse, like)", ["target"])
def _ds_create(t):
    kind = (_get(t, "type") or "seq").lower()
    name = dsn(_req(t, "target"))
    if kind == "like" or _get(t, "like"):
        args = ["zos-files", "create", "data-set", name, "--like", dsn(_req(t, "like"))]
        return args, None
    if kind in ("seq", "ps", "sequencial"):
        args = ["zos-files", "create", "data-set-sequential", name]
    elif kind in ("pds", "po"):
        args = ["zos-files", "create", "data-set-partitioned", name, "--data-set-type", "PDS"]
    elif kind in ("pdse", "library", "lib"):
        args = ["zos-files", "create", "data-set-partitioned", name, "--data-set-type", "LIBRARY"]
    else:
        raise TaskError(f"type invalido para ds.create: {kind} (use seq, pds, pdse ou like)")
    _opt(args, "--record-format", _get(t, "recfm"))
    _opt(args, "--record-length", _get(t, "lrecl"))
    _opt(args, "--block-size", _get(t, "blksize"))
    _opt(args, "--size", _get(t, "size"))
    _opt(args, "--volume-serial", _get(t, "volume"))
    _opt(args, "--storage-class", _get(t, "storclas"))
    _opt(args, "--management-class", _get(t, "mgmtclas"))
    _opt(args, "--data-class", _get(t, "dataclas"))
    return args, None


@action("ds.copy", "datasets", ESCRITA, "Copia dataset ou membro (replace=sim sobrescreve)", ["target", "to"],
        risk_fn=lambda t: DESTRUTIVA if as_bool(t.get("replace")) else ESCRITA)
def _ds_copy(t):
    args = ["zos-files", "copy", "data-set", dsn(_req(t, "target")), dsn(_req(t, "to"))]
    _flag(args, "--replace", _get(t, "replace"))
    return args, None


@action("ds.rename", "datasets", DESTRUTIVA, "Renomeia dataset", ["target", "to"])
def _ds_rename(t):
    return ["zos-files", "rename", "data-set", dsn(_req(t, "target")), dsn(_req(t, "to"))], None


@action("ds.delete", "datasets", DESTRUTIVA, "Apaga dataset ou membro", ["target"])
def _ds_delete(t):
    name = dsn(_req(t, "target"))
    if "*" in name or "%" in name:
        raise TaskError("ds.delete nao aceita curinga; liste e apague um por um")
    return ["zos-files", "delete", "data-set", name, "--for-sure"], None


@action("ds.recall", "datasets", ESCRITA, "Faz recall de dataset migrado", ["target"])
def _ds_recall(t):
    return ["zos-files", "recall", "data-set", dsn(_req(t, "target"))], None


# --------------------------------------------------------------------------
# USS (via z/OSMF, sem SSH)
# --------------------------------------------------------------------------


@action("uss.list", "uss", LEITURA, "Lista arquivos de um diretorio USS", ["target"])
def _uss_list(t):
    return ["zos-files", "list", "uss-files", _req(t, "target")], None


@action("uss.view", "uss", LEITURA, "Le um arquivo USS", ["target"])
def _uss_view(t):
    args = ["zos-files", "view", "uss-file", _req(t, "target")]
    _opt(args, "--encoding", _get(t, "encoding"))
    _flag(args, "--binary", _get(t, "binary"))
    return args, None


@action("uss.download", "uss", LEITURA, "Baixa arquivo USS para local", ["target"])
def _uss_download(t):
    args = ["zos-files", "download", "uss-file", _req(t, "target")]
    _opt(args, "--file", _get(t, "file"))
    _opt(args, "--encoding", _get(t, "encoding"))
    _flag(args, "--binary", _get(t, "binary"))
    return args, None


@action("uss.upload", "uss", DESTRUTIVA, "Envia arquivo local para o USS (sobrescreve)", ["target", "file"])
def _uss_upload(t):
    args = ["zos-files", "upload", "file-to-uss", _req(t, "file"), _req(t, "target")]
    _opt(args, "--encoding", _get(t, "encoding"))
    _flag(args, "--binary", _get(t, "binary"))
    return args, None


@action("uss.mkdir", "uss", ESCRITA, "Cria diretorio USS", ["target"])
def _uss_mkdir(t):
    args = ["zos-files", "create", "uss-directory", _req(t, "target")]
    _opt(args, "--mode", _get(t, "mode"))
    return args, None


@action("uss.delete", "uss", DESTRUTIVA, "Apaga arquivo ou diretorio USS (recursive=sim)", ["target"])
def _uss_delete(t):
    path = _req(t, "target")
    if path.rstrip("/") in ("", "/u", "/tmp", "/etc", "/usr", "/bin", "/var"):
        raise TaskError(f"uss.delete recusado para caminho de sistema: {path}")
    args = ["zos-files", "delete", "uss-file", path, "--for-sure"]
    _flag(args, "--recursive", _get(t, "recursive"))
    return args, None


# --------------------------------------------------------------------------
# Console e log do sistema
# --------------------------------------------------------------------------

DISPLAY_RE = re.compile(r"^\s*(D|DISPLAY|\$D|\$DJ|\$DA|\$DQ)\b", re.I)


def console_risk(t: dict) -> str:
    return LEITURA if DISPLAY_RE.match(str(t.get("command") or "")) else DESTRUTIVA


@action("console.issue", "console", DESTRUTIVA, "Comando de operador (D ... sem confirmacao; resto exige --yes)",
        ["command"], risk_fn=console_risk)
def _console_issue(t):
    args = ["zos-console", "issue", "command", _req(t, "command")]
    _opt(args, "--console-name", _get(t, "console"))
    _opt(args, "--solicited-keyword", _get(t, "keyword"))
    _opt(args, "--sysplex-system", _get(t, "system"))
    return args, None


@action("console.logs", "console", LEITURA, "Le o OPERLOG por janela de tempo (start, range)")
def _console_logs(t):
    args = ["zos-logs", "list", "logs"]
    _opt(args, "--start-time", _get(t, "start"))
    _opt(args, "--range", _get(t, "range", "10m"))
    _opt(args, "--direction", _get(t, "direction"))
    return args, None


# --------------------------------------------------------------------------
# TSO
# --------------------------------------------------------------------------

TSO_READ_RE = re.compile(r"^\s*(LISTCAT|LISTC|LISTDS|LISTD|LISTALC|LISTA|TIME|STATUS|ST|PROFILE|LU|LISTUSER|LD|LISTDSD|SR|SEARCH)\b", re.I)


def tso_risk(t: dict) -> str:
    return LEITURA if TSO_READ_RE.match(str(t.get("command") or "")) else DESTRUTIVA


@action("tso.issue", "tso", DESTRUTIVA, "Comando TSO (LISTCAT, LISTDS... sem confirmacao; resto exige --yes)",
        ["command"], risk_fn=tso_risk)
def _tso_issue(t):
    args = ["zos-tso", "issue", "command", _req(t, "command")]
    _opt(args, "--account", _get(t, "account"))
    _opt(args, "--tso-profile", _get(t, "tso_profile"))
    return args, None


def build(task: dict) -> Tuple[Action, List[str], Optional[str]]:
    name = str(task.get("action") or "").strip().lower()
    if not name:
        raise TaskError("tarefa sem o campo 'action'")
    act = ACTIONS.get(name)
    if not act:
        raise TaskError(f"acao desconhecida: {name}. Use `ztractor actions` para ver a lista")
    for key in act.required:
        _req(task, key)
    args, stdin = act.build(task)
    profile = _get(task, "profile")
    if profile:
        args += ["--zosmf-profile", profile]
    return act, args, stdin
