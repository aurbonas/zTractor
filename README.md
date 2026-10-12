# zTractor

Operação z/OS com o **Zowe CLI**, a partir de **planilhas Excel, APIs REST e documentos de texto**,
em **Windows ou Linux**. Todo acesso ao mainframe passa pelo z/OSMF via `zowe`; não há SSH.

O zTractor tem duas partes:

- **Motor `ztractor`** (Python): lê a entrada, transforma cada linha numa ação, monta o comando
  `zowe ... --rfj`, pede confirmação para o que é destrutivo, executa e grava os resultados
  em Excel, CSV, JSON ou por POST numa API.
- **Skills** em [`.claude/skills`](.claude/skills): ensinam o Claude a usar o motor por família
  (setup, lote, jobs, datasets, USS, console, TSO), com regras de segurança de cada uma.

```
Excel / CSV / JSON / YAML / texto / API REST
              │
              ▼
   ztractor plan  ──►  revisão do plano (risco por tarefa)
              │
              ▼
   ztractor run   ──►  zowe <comando> --rfj  ──►  z/OSMF  ──►  z/OS
              │
              ▼
   resultados.xlsx / .csv / .json / POST
```

## Instalação

Pré-requisitos: Node.js 18+, Python 3.9+ e acesso ao z/OSMF.

```bash
npm install -g @zowe/cli@zowe-v3-lts
python -m pip install -e .          # dentro deste repositório
zowe config init --global-config    # host, porta e usuário do z/OSMF
zowe config secure --global-config  # senha no cofre seguro do Zowe
ztractor do setup.check
```

No Windows os mesmos comandos funcionam no PowerShell ou no cmd. Se o `zowe` não for achado,
defina `ZTRACTOR_ZOWE` com o caminho do `zowe.cmd`.

## Uso

```bash
ztractor actions                              # catálogo de ações, risco e campos
ztractor template tarefas.xlsx                # planilha modelo
ztractor plan tarefas.xlsx                    # mostra os comandos, não executa
ztractor run tarefas.xlsx -o resultados.xlsx  # executa; destrutivas ficam puladas
ztractor run tarefas.xlsx --yes               # executa também as destrutivas
ztractor do ds.list "HLQ.**"                  # uma ação avulsa
```

Opções de `plan` e `run`: `--sheet ABA`, `--var NOME=valor`, `--profile PERFIL`,
`--only jobs,ds.list`, `--header "Authorization: Bearer ${API_TOKEN}"`,
`--post-results URL`, `--stop-on-error`.

Código de saída: `0` tudo ok, `1` alguma tarefa falhou ou é inválida, `2` alguma destrutiva ficou sem confirmação.

## Formatos de entrada

Cada tarefa tem `action` e os campos da ação. `${NOME}` em qualquer campo é trocado pela variável
do plano, de `--var` ou do ambiente.

| Formato | Como escrever |
| --- | --- |
| Excel (`.xlsx`) | aba `tasks` com cabeçalho na linha 1; aba `vars` com `name` e `value`; coluna `enabled` = `nao` desliga a linha |
| CSV | mesmo cabeçalho; separador `,` ou `;` |
| JSON / YAML | lista de tarefas ou `{"vars": {...}, "tasks": [...]}` |
| Texto | `acao alvo chave=valor` por linha; `set NOME=valor`; `#` comenta |
| API REST | URL `http(s)` que devolve o JSON acima; cabeçalhos com `--header` |

Exemplos em [`examples/`](examples).

## Ações

| Família | Ações |
| --- | --- |
| setup | `setup.check`, `setup.systems` |
| jobs | `jobs.list`, `jobs.status`, `jobs.submit`, `jobs.spool-list`, `jobs.spool-view`, `jobs.spool-all`, `jobs.download`, `jobs.cancel`, `jobs.delete` |
| datasets | `ds.list`, `ds.members`, `ds.view`, `ds.download`, `ds.download-members`, `ds.search`, `ds.create`, `ds.recall`, `ds.copy`, `ds.write`, `ds.upload`, `ds.rename`, `ds.delete` |
| uss | `uss.list`, `uss.view`, `uss.download`, `uss.mkdir`, `uss.upload`, `uss.delete` |
| console | `console.issue`, `console.logs` |
| tso | `tso.issue` |

Risco de cada ação: **leitura** roda direto; **escrita** roda e aparece no plano; **destrutiva**
(apagar, sobrescrever, cancelar, comando de operador que não seja display, TSO que altera) exige
`--yes` ou confirmação no terminal.

## Desenvolvimento

```bash
python -m pip install -e ".[dev]"
python -m pytest                      # usa um Zowe simulado
python tools/check_zowe_flags.py      # confere cada comando e flag no Zowe CLI instalado
```
