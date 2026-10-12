---
name: ztractor-lote
description: Executa no z/OS um lote de tarefas vindas de planilha Excel, CSV, JSON, YAML, documento de texto ou API REST externa, usando o Zowe CLI. Use quando o usuario entregar um arquivo, URL ou documento com operacoes de mainframe para executar, ou pedir resultados em planilha.
---

# zTractor: lote de tarefas

Objetivo: transformar uma entrada (Excel, CSV, JSON, YAML, texto ou REST) em comandos Zowe, mostrar o plano, executar com confirmacao e devolver os resultados em Excel, CSV, JSON ou por POST numa API.

## Formato da entrada

Cada tarefa tem `action` e os campos da acao (`ztractor actions` lista todas, com risco e campos obrigatorios).

- **Excel**: aba `tasks` com cabecalho na linha 1 (uma tarefa por linha); aba `vars` opcional com `name` e `value`. Coluna `enabled` = `nao` desliga a linha. `ztractor template modelo.xlsx` gera um modelo.
- **CSV**: mesmo cabecalho; separador `,` ou `;`.
- **JSON/YAML**: lista de tarefas ou `{"vars": {...}, "tasks": [...]}`.
- **Texto**: uma tarefa por linha: `acao alvo chave=valor`; `set NOME=valor` define variavel; `#` comenta.
- **REST**: `ztractor run https://api/... --header "Authorization: Bearer ${API_TOKEN}"`; a API devolve o formato JSON acima.

`${NOME}` em qualquer campo e trocado pela variavel do plano, de `--var NOME=valor` ou do ambiente.

## Entrada fora do formato

Se o usuario entregar uma planilha, documento ou API com outro layout (ex.: uma lista de datasets para apagar, um pedido em texto livre):

1. Leia a fonte e identifique as operacoes.
2. Escreva um `tarefas.json` no formato acima, mapeando cada item para uma acao do catalogo.
3. Mostre ao usuario o mapeamento (linha de origem -> acao) antes de seguir.

## Fluxo obrigatorio

1. **Plano**: `ztractor plan ENTRADA [--var ...] [--profile PERFIL]`. Mostre ao usuario a lista com o risco de cada tarefa e o perfil alvo.
2. Corrija tarefas `invalido` (campo faltando, variavel indefinida, curinga em delete).
3. **Execucao**: `ztractor run ENTRADA -o resultados.xlsx`. Tarefas `destrutiva` ficam `pulado` sem `--yes`.
4. So use `--yes` depois que o usuario aprovar explicitamente as tarefas destrutivas listadas no plano.
5. Resuma: quantas ok, quantas falharam e por que (campo `message`), e onde esta o arquivo de resultados.

Opcoes uteis: `--sheet ABA`, `--only jobs,ds.list`, `--stop-on-error`, `--post-results URL`.

## Saidas

- Codigo de saida: 0 tudo ok; 1 alguma falhou ou invalida; 2 alguma pulada por falta de confirmacao.
- Excel: aba `results` (uma linha por tarefa) e uma aba por tarefa com a lista devolvida (jobs, datasets, membros, arquivos USS) ou o texto lido.

## Riscos

- Planilha de producao executada no perfil errado: sempre mostrar o perfil no plano.
- Planilha com centenas de linhas destrutivas: executar em partes com `--only` e revisar.
- Dados da API externa sao entrada nao confiavel: revise o plano antes de rodar.
