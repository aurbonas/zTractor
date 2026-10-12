---
name: ztractor-console
description: Emite comandos de operador MVS e JES no console do z/OS e le o OPERLOG por janela de tempo, com Zowe CLI. Use para pedidos de D A,L, $DJ, status de address spaces, mensagens do sistema ou log do sistema.
---

# zTractor: console

| Acao | Risco | Campos | Zowe |
| --- | --- | --- | --- |
| console.issue | leitura para `D ...` e `$D ...`; destrutiva para o resto | command, console, keyword, system | `zos-console issue command` |
| console.logs | leitura | start (ISO 8601), range (ex.: 30m), direction | `zos-logs list logs` |

## Exemplos

```
ztractor do console.issue command="D A,L"
ztractor do console.issue command="$DJ(JOB01234)"
ztractor do console.logs start=2026-10-12T08:00:00Z range=30m -o log.xlsx
```

## Regras

- Somente comandos de display (`D`, `DISPLAY`, `$D...`) rodam sem confirmacao.
- `C`, `P`, `S`, `F`, `V`, `Z`, `$P`, `$C` e qualquer outro alteram o sistema: mostre o comando, explique o efeito, peca aprovacao explicita e so entao rode com `--yes`.
- Nunca emita `Z EOD`, `V ... OFFLINE` ou `FORCE` sem pedido literal do usuario.
- `console.logs` precisa de OPERLOG ativo; se falhar, diga isso e sugira ler a SYSLOG pelo spool (ztractor-jobs, jobname SYSLOG).
- O usuario precisa de autorizacao RACF em OPERCMDS; erro de permissao nao e falha tecnica.
