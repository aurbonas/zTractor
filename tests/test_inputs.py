import json

import pytest
from openpyxl import Workbook

from ztractor.inputs import load, resolve
from ztractor.inputs.text import parse_text


def test_text_parser():
    v, t = parse_text('set HLQ=Z1\n# comentario\nds.view ${HLQ}.JCL(A) range=0,5\nconsole.issue command="D A,L"\n')
    assert v == {"HLQ": "Z1"}
    assert t[0]["action"] == "ds.view" and t[0]["target"] == "${HLQ}.JCL(A)" and t[0]["range"] == "0,5"
    assert t[1]["command"] == "D A,L"


def test_excel_with_vars_and_disabled(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "tasks"
    ws.append(["Action", "Target", "Enabled", "LRECL"])
    ws.append(["ds.list", "${HLQ}.**", "sim", None])
    ws.append(["ds.delete", "Z1.X", "nao", None])
    ws.append([None, None, None, None])
    ws.append(["ds.create", "Z1.N", None, 80])
    wv = wb.create_sheet("vars")
    wv.append(["name", "value"])
    wv.append(["HLQ", "Z1"])
    path = tmp_path / "t.xlsx"
    wb.save(path)
    plan = load(str(path))
    assert plan.vars == {"HLQ": "Z1"}
    assert [t["action"] for t in plan.tasks] == ["ds.list", "ds.create"]
    assert plan.tasks[1]["lrecl"] == 80
    assert resolve(plan.tasks[0], plan.vars)["target"] == "Z1.**"


def test_csv_semicolon(tmp_path):
    path = tmp_path / "t.csv"
    path.write_text("action;target\nds.list;Z1.**\n", encoding="utf-8")
    assert load(str(path)).tasks == [{"action": "ds.list", "target": "Z1.**", "enabled": "sim"}]


def test_json_list_and_object(tmp_path):
    p1 = tmp_path / "a.json"
    p1.write_text(json.dumps([{"action": "jobs.list"}]))
    p2 = tmp_path / "b.json"
    p2.write_text(json.dumps({"vars": {"A": "1"}, "tasks": [{"action": "jobs.list"}]}))
    assert load(str(p1)).tasks[0]["action"] == "jobs.list"
    assert load(str(p2)).vars == {"A": "1"}


def test_missing_variable():
    with pytest.raises(KeyError, match="NAO_EXISTE"):
        resolve({"target": "${NAO_EXISTE}"}, {})


def test_rest_input(monkeypatch):
    import ztractor.inputs.rest as rest

    seen = {}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"vars": {"HLQ": "Z9"}, "tasks": [{"action": "ds.list", "target": "${HLQ}.**"}]}

    def fake_get(url, headers, timeout):
        seen.update(url=url, headers=headers)
        return Resp()

    monkeypatch.setattr(rest.requests, "get", fake_get)
    monkeypatch.setenv("API_TOKEN", "abc")
    plan = load("https://api.exemplo/tarefas", headers={"Authorization": "Bearer ${API_TOKEN}"})
    assert seen["headers"]["Authorization"] == "Bearer abc"
    assert plan.vars == {"HLQ": "Z9"} and plan.tasks[0]["target"] == "${HLQ}.**"
