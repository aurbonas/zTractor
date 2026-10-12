import pytest

from ztractor.actions import ACTIONS, DESTRUTIVA, LEITURA, TaskError, build


def args_of(**task):
    return build(task)[1]


def test_every_action_has_summary_and_family():
    assert len(ACTIONS) >= 30
    for a in ACTIONS.values():
        assert a.summary and a.family and a.risk in ("leitura", "escrita", "destrutiva")


def test_dataset_names_are_upper_and_unquoted():
    assert args_of(action="ds.view", target="'z1.jcl(daily01)'")[3] == "Z1.JCL(DAILY01)"


def test_submit_detects_source():
    assert args_of(action="jobs.submit", target="Z1.JCL(A)")[:3] == ["zos-jobs", "submit", "data-set"]
    assert args_of(action="jobs.submit", target="jcl/a.jcl")[:3] == ["zos-jobs", "submit", "local-file"]
    assert args_of(action="jobs.submit", target="/u/z1/a.jcl")[:3] == ["zos-jobs", "submit", "uss-file"]
    assert "--wait-for-output" in args_of(action="jobs.submit", target="Z1.JCL(A)")
    assert "--wait-for-output" not in args_of(action="jobs.submit", target="Z1.JCL(A)", wait="nao")


def test_create_types():
    a = args_of(action="ds.create", target="z1.lib", type="pdse", recfm="FB", lrecl=80.0)
    assert a[:4] == ["zos-files", "create", "data-set-partitioned", "Z1.LIB"]
    assert a[a.index("--data-set-type") + 1] == "LIBRARY"
    assert a[a.index("--record-length") + 1] == "80"
    assert args_of(action="ds.create", target="z1.new", like="z1.old")[3:] == ["Z1.NEW", "--like", "Z1.OLD"]


def test_required_fields():
    with pytest.raises(TaskError, match="target"):
        build({"action": "ds.view"})
    with pytest.raises(TaskError, match="desconhecida"):
        build({"action": "ds.nada"})


def test_guards():
    with pytest.raises(TaskError, match="curinga"):
        build({"action": "ds.delete", "target": "Z1.*"})
    with pytest.raises(TaskError, match="HLQ"):
        build({"action": "ds.list", "target": "**"})
    with pytest.raises(TaskError, match="sistema"):
        build({"action": "uss.delete", "target": "/tmp/"})


def test_console_and_tso_risk():
    assert build({"action": "console.issue", "command": "D A,L"})[0].risk_for({"command": "D A,L"}) == LEITURA
    assert ACTIONS["console.issue"].risk_for({"command": "P JES2"}) == DESTRUTIVA
    assert ACTIONS["tso.issue"].risk_for({"command": "LISTCAT LEVEL(Z1)"}) == LEITURA
    assert ACTIONS["tso.issue"].risk_for({"command": "DELETE 'Z1.X'"}) == DESTRUTIVA
    assert ACTIONS["ds.copy"].risk_for({"replace": "sim"}) == DESTRUTIVA


def test_profile_flag():
    assert args_of(action="jobs.list", profile="prod")[-2:] == ["--zosmf-profile", "prod"]
