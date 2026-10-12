---
name: ztractor-uss
description: Lista, le, baixa, envia, cria e apaga arquivos e diretorios no z/OS UNIX (USS) via z/OSMF com Zowe CLI, sem SSH. Use para pedidos sobre caminhos /u/..., arquivos USS ou zFS.
---

# zTractor: USS

| Acao | Risco | Campos | Zowe |
| --- | --- | --- | --- |
| uss.list | leitura | target=diretorio | `zos-files list uss-files` |
| uss.view | leitura | target, encoding, binary | `zos-files view uss-file` |
| uss.download | leitura | target, file, binary | `zos-files download uss-file` |
| uss.mkdir | escrita | target, mode | `zos-files create uss-directory` |
| uss.upload | destrutiva | target, file, binary, render | `zos-files upload file-to-uss` |
| uss.delete | destrutiva | target, recursive | `zos-files delete uss-file --for-sure` |

## Exemplos

```
ztractor do uss.list /u/z63181
ztractor do uss.view /u/z63181/app/config.properties
ztractor do uss.upload /u/z63181/app/run.sh file=scripts/run.sh --yes
```

## Regras

- Nao executa comandos de shell: o projeto nao usa SSH. Para rodar algo no USS, submeta um job com BPXBATCH (ztractor-jobs).
- Texto e convertido entre UTF-8 e EBCDIC; use `binary=sim` para zip, jar e imagens.
- `uss.delete` recusa diretorios de sistema; `recursive=sim` exige confirmacao explicita do usuario e `--yes`.
