---
name: ztractor-setup
description: Instala e configura o Zowe CLI e o zTractor no Windows ou Linux, cria o perfil z/OSMF e testa a conexao com o mainframe. Use antes de qualquer outra Skill ztractor, ou quando um comando zowe falhar por conexao, certificado ou credencial.
---

# zTractor: setup

Objetivo: deixar a maquina pronta para rodar `zowe` e `ztractor` contra o z/OS, via z/OSMF. Nao usa SSH.

## Passos

1. Confirme os pre-requisitos e mostre as versoes:
   - Node.js 18+ (`node --version`) e Python 3.9+ (`python --version` no Windows, `python3 --version` no Linux).
2. Instale o Zowe CLI v3 se `zowe --version` falhar:
   ```
   npm install -g @zowe/cli@zowe-v3-lts
   ```
3. Instale o zTractor a partir da raiz do repositorio:
   ```
   python -m pip install -e .
   ```
4. Crie o team config, se nao existir (`zowe config list` mostra o atual):
   ```
   zowe config init --global-config
   ```
   Peca ao usuario host, porta do z/OSMF e usuario. A senha **nunca** passa pela linha de comando nem pelo chat:
   o usuario roda `zowe config secure --global-config` e digita no prompt.
   Para mais de um ambiente, crie um perfil por ambiente (ex.: `lab`, `prod`) em `profiles` do `zowe.config.json`.
5. Teste:
   ```
   ztractor do setup.check
   ztractor do setup.systems
   ```

## Saidas

- `setup.check`: versao do z/OSMF, sistema e plugins ativos. `success: false` indica problema de conexao.

## Problemas comuns

| Sintoma | Causa provavel | Acao |
| --- | --- | --- |
| `self signed certificate` | certificado interno do z/OSMF | importar a CA; `rejectUnauthorized: false` so em laboratorio |
| HTTP 401 | usuario ou senha | `zowe config secure` de novo |
| `ECONNREFUSED` / timeout | host, porta ou firewall | confirmar porta do z/OSMF (geralmente 443 ou 10443) |
| `zowe` nao encontrado no Windows | PATH do npm | abrir terminal novo ou definir `ZTRACTOR_ZOWE` com o caminho do `zowe.cmd` |

## Riscos

- Nao grave senha, token ou certificado no repositorio nem em planilhas de entrada.
- Confirme com o usuario qual perfil e de producao antes de usar.
