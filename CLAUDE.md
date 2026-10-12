# zTractor

Operação z/OS só com Zowe CLI (z/OSMF), em Windows e Linux. Nada de SSH.

- Motor em `src/ztractor`: `actions.py` (catálogo ação -> comando zowe e risco), `inputs/` (Excel, CSV, JSON, YAML, texto, REST), `engine.py` (variáveis, confirmação, execução), `outputs.py`, `cli.py`.
- Skills em `.claude/skills/ztractor-*`. Ao mudar uma ação, atualize a tabela da Skill da família e o README.
- Toda ação nova: comando com `--rfj`, risco correto e teste em `tests/test_actions.py`; rode `python tools/check_zowe_flags.py` para conferir comando e flags no Zowe instalado.
- Ações destrutivas nunca rodam sem `--yes` ou confirmação explícita do usuário.
- Textos e mensagens em português.
