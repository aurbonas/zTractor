---
name: ztractor-datasets
description: Lista, le, pesquisa, edita, aloca, copia, renomeia e apaga datasets e membros de PDS no z/OS com Zowe CLI. Use para qualquer pedido sobre datasets, PDS, PDSE, membros, LRECL, RECFM ou conteudo de arquivos MVS.
---

# zTractor: datasets

| Acao | Risco | Campos | Zowe |
| --- | --- | --- | --- |
| ds.list | leitura | target=padrao (ex.: HLQ.**), volume | `zos-files list data-set --attributes` |
| ds.members | leitura | target=PDS, pattern | `zos-files list all-members --attributes` |
| ds.view | leitura | target, range, encoding, binary | `zos-files view data-set` |
| ds.download | leitura | target, file | `zos-files download data-set` |
| ds.download-members | leitura | target=PDS, dir | `zos-files download all-members` |
| ds.search | leitura | target=padrao, text | `zos-files search data-sets` |
| ds.create | escrita | target, type (seq/pds/pdse/like), recfm, lrecl, blksize, size, like | `zos-files create data-set-*` |
| ds.recall | escrita | target | `zos-files recall data-set` |
| ds.copy | escrita (destrutiva com replace=sim) | target, to, replace | `zos-files copy data-set` |
| ds.write | destrutiva | target, content | `zos-files upload stdin-to-data-set` |
| ds.upload | destrutiva | target, file, render | `zos-files upload file-to-data-set` |
| ds.rename | destrutiva | target, to | `zos-files rename data-set` |
| ds.delete | destrutiva | target (sem curinga) | `zos-files delete data-set --for-sure` |

## Exemplos

```
ztractor do ds.list "Z63181.**" -o datasets.xlsx
ztractor do ds.view "Z63181.JCL(DAILY01)" range=0,40
ztractor do ds.create Z63181.NOVO.JCL type=pdse recfm=FB lrecl=80 size=5CYL
ztractor do ds.upload "Z63181.NOVO.JCL(CARGA)" file=jcl/carga.jcl render=sim --yes
```

## Editar com seguranca

1. `ds.download` para um arquivo local.
2. Altere o arquivo e mostre o diff ao usuario.
3. Depois da aprovacao, `ds.upload` com `--yes`.
4. Releia com `ds.view` e confirme.

## Regras

- Nomes vao em maiusculas; membro entre parenteses; use aspas no shell por causa dos parenteses e asteriscos.
- `ds.list` exige o HLQ no padrao; `ds.delete` recusa curinga: liste antes e apague um por um.
- Linhas maiores que o LRECL sao truncadas no upload; confira `lrecl` com `ds.list` antes de gravar.
- Load modules e arquivos binarios usam `binary=sim`.
- Dataset migrado faz recall automatico e demora; use `ds.recall` antes de lotes grandes.
