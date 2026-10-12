---
name: ztractor-tso
description: Executa comandos TSO no z/OS com Zowe CLI, como LISTCAT, LISTDS, STATUS e comandos RACF de consulta. Use quando o pedido citar TSO, LISTCAT, catalogo ou consulta RACF.
---

# zTractor: TSO

| Acao | Risco | Campos | Zowe |
| --- | --- | --- | --- |
| tso.issue | leitura para LISTCAT, LISTDS, LISTALC, STATUS, TIME, PROFILE, LU, LD, SR; destrutiva para o resto | command, account, tso_profile | `zos-tso issue command` |

## Exemplos

```
ztractor do tso.issue command="LISTCAT LEVEL(Z63181)"
ztractor do tso.issue command="LISTDS 'Z63181.JCL' MEMBERS"
ztractor do tso.issue command="LU Z63181"
```

## Regras

- O account number vem do perfil `tso` do team config; `account=` sobrescreve para um comando.
- Comandos que alteram (DELETE, ALLOC, RENAME, ALTUSER, PERMIT, RDEFINE) exigem aprovacao explicita e `--yes`.
- Para alocar, apagar ou renomear datasets prefira ztractor-datasets, que tem protecoes proprias.
- Erro de logon geralmente e account number ou logon procedure errados no perfil `tso`.
