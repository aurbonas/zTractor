---
name: ztractor-jobs
description: Submete JCL, lista jobs, consulta status e retcode, le e baixa sysout, cancela e purga jobs no z/OS com Zowe CLI. Use para qualquer pedido sobre jobs batch, JES, spool, JOBID ou retcode.
---

# zTractor: jobs

Todas as acoes rodam com `ztractor do ACAO alvo chave=valor` (uma tarefa) ou via ztractor-lote (varias).

| Acao | Risco | Campos | Zowe |
| --- | --- | --- | --- |
| jobs.list | leitura | owner, prefix | `zos-jobs list jobs` |
| jobs.status | leitura | target=JOBID | `zos-jobs view job-status-by-jobid` |
| jobs.spool-list | leitura | target=JOBID | `zos-jobs list spool-files-by-jobid` |
| jobs.spool-view | leitura | target=JOBID, spool_id | `zos-jobs view spool-file-by-id` |
| jobs.spool-all | leitura | target=JOBID | `zos-jobs view all-spool-content` |
| jobs.download | leitura | target=JOBID, dir | `zos-jobs download output` |
| jobs.submit | escrita | target, source, wait, jcl_symbols | `zos-jobs submit data-set / local-file / uss-file` |
| jobs.cancel | destrutiva | target=JOBID | `zos-jobs cancel job` |
| jobs.delete | destrutiva | target=JOBID | `zos-jobs delete job` |

## Exemplos

```
ztractor do jobs.list owner=Z63181 prefix="DAILY*"
ztractor do jobs.submit "Z63181.JCL(DAILY01)"
ztractor do jobs.submit jcl/carga.jcl --var DATA=20261012
ztractor do jobs.spool-list JOB01234
ztractor do jobs.spool-view JOB01234 spool_id=3
```

## Regras

- `jobs.submit` espera o fim do job por padrao (`wait=nao` para nao esperar) e devolve `jobid`, `status` e `retcode`.
- JCL local com `${VAR}` e substituido antes do envio; JCL em dataset usa `jcl_symbols="A=1 B=2"`.
- Antes de submeter, leia o JCL e avise o usuario se houver `DISP=OLD/MOD`, `DELETE`, IDCAMS ou gravacao em datasets de producao.
- Para analisar falha, liste o spool e leia `JESMSGLG` e `JESYSMSG` antes do resto; sysout grande vai para arquivo com `jobs.download`.
- `jobs.cancel` e `jobs.delete` so com aprovacao explicita e `--yes`; purgar apaga a evidencia de uma falha.

## Saidas

- `retcode`: `CC 0000` ok; `CC 0004` aviso; `ABEND S0C7` etc. abend; `JCL ERROR`; `null` com status ACTIVE ou INPUT = ainda rodando.
