# zTractor

z/OS operations with the **Zowe CLI**, driven by **Excel spreadsheets, REST APIs and text documents**,
on **Windows or Linux**. All mainframe access goes through z/OSMF via `zowe`; there is no SSH.

zTractor has two parts:

- **`ztractor` engine** (Python): reads the input, turns each row into an action, builds the
  `zowe ... --rfj` command, asks for confirmation on anything destructive, runs it and writes the
  results to Excel, CSV, JSON or a POST to an API.
- **Skills** in [`.claude/skills`](.claude/skills): teach Claude how to use the engine for each family
  (setup, batch, jobs, datasets, USS, console, TSO), with the safety rules for each one.

```
Excel / CSV / JSON / YAML / text / REST API
              │
              ▼
   ztractor plan  ──►  plan review (risk per task)
              │
              ▼
   ztractor run   ──►  zowe <command> --rfj  ──►  z/OSMF  ──►  z/OS
              │
              ▼
   results.xlsx / .csv / .json / POST
```

## Installation

Prerequisites: Node.js 18+, Python 3.9+ and access to z/OSMF.

```bash
npm install -g @zowe/cli@zowe-v3-lts
python -m pip install -e .          # inside this repository
zowe config init --global-config    # z/OSMF host, port and user
zowe config secure --global-config  # password in Zowe's secure credential store
ztractor do setup.check
```

On Windows the same commands work in PowerShell or cmd. If `zowe` is not found,
set `ZTRACTOR_ZOWE` to the path of `zowe.cmd`.

## Usage

```bash
ztractor actions                              # action catalog, risk and fields
ztractor template tasks.xlsx                  # template spreadsheet
ztractor plan tasks.xlsx                      # shows the commands, does not run them
ztractor run tasks.xlsx -o results.xlsx       # runs; destructive tasks are skipped
ztractor run tasks.xlsx --yes                 # also runs destructive tasks
ztractor do ds.list "HLQ.**"                  # a single ad hoc action
```

Options for `plan` and `run`: `--sheet SHEET`, `--var NAME=value`, `--profile PROFILE`,
`--only jobs,ds.list`, `--header "Authorization: Bearer ${API_TOKEN}"`,
`--post-results URL`, `--stop-on-error`.

Exit code: `0` all ok, `1` some task failed or is invalid, `2` some destructive task was left unconfirmed.

## Input formats

Each task has an `action` and that action's fields. `${NAME}` in any field is replaced by the plan
variable, by `--var` or by the environment variable of that name.

| Format | How to write it |
| --- | --- |
| Excel (`.xlsx`) | `tasks` sheet with the header on row 1; `vars` sheet with `name` and `value`; an `enabled` column set to `no` (or `nao`) turns a row off |
| CSV | same header; `,` or `;` separator |
| JSON / YAML | a list of tasks or `{"vars": {...}, "tasks": [...]}` |
| Text | `action target key=value` per line; `set NAME=value`; `#` starts a comment |
| REST API | an `http(s)` URL that returns the JSON above; headers via `--header` |

Examples in [`examples/`](examples).

## Actions

| Family | Actions |
| --- | --- |
| setup | `setup.check`, `setup.systems` |
| jobs | `jobs.list`, `jobs.status`, `jobs.submit`, `jobs.spool-list`, `jobs.spool-view`, `jobs.spool-all`, `jobs.download`, `jobs.cancel`, `jobs.delete` |
| datasets | `ds.list`, `ds.members`, `ds.view`, `ds.download`, `ds.download-members`, `ds.search`, `ds.create`, `ds.recall`, `ds.copy`, `ds.write`, `ds.upload`, `ds.rename`, `ds.delete` |
| uss | `uss.list`, `uss.view`, `uss.download`, `uss.mkdir`, `uss.upload`, `uss.delete` |
| console | `console.issue`, `console.logs` |
| tso | `tso.issue` |

Risk levels (shown in the tool's output with their Portuguese names): **leitura** (read) runs
directly; **escrita** (write) runs and is listed in the plan; **destrutiva** (destructive: delete,
overwrite, cancel, any operator command other than display, TSO commands that change something)
requires `--yes` or confirmation at the terminal.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest                      # uses a simulated Zowe
python tools/check_zowe_flags.py      # checks every command and flag against the installed Zowe CLI
```
