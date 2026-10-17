# AGENTS.md — Agent Governor

Este arquivo é um mapa, não o motor de políticas. Regras críticas são verificadas pelo próprio Governor, fora do modelo.

## Fontes de verdade
- `STATE.md` — onde paramos e a próxima ação. **Comece por aqui.**
- `ROADMAP.md` — versões, itens com ID e critérios de aceite.
- `docs/ARCHITECTURE.md` — leia antes de mudar a lógica de enforcement.
- `PROJECT.md` — problema, MVP e fora de escopo. `docs/INSTALL.md` — instalação em novos projetos.
- `GEMINI.md` — regras de execução no Antigravity.

## Comandos
- Instalar para desenvolvimento: `python -m pip install -e .`
- Verificar (igual ao CI `test.yml`): `python -m unittest discover -s tests -v` — rode antes de reportar conclusão.
- Empacotar (igual ao CI `package.yml`): `python -m build`

## Regras deste projeto
1. Nunca enfraqueça o comportamento fail-closed nem a autoproteção da governança.
2. Nunca apague nem relaxe testes para a validação passar.
3. Mudanças nas regras de comando exigem testes dos dois lados: negação e permissão.
4. A atribuição de fontes no `README.md` faz parte do contrato do produto; mantenha-a correta.
5. Não declare proteção que não foi demonstrada; diferencie implementado de validado no host real.

## Git
- `CLAUDE.md` só importa este arquivo (`@AGENTS.md`).
- Ao encerrar sessão relevante, atualize `STATE.md` e `CHANGELOG.md` (`## X.Y.Z — AAAA-MM-DD`).
- Nunca force push nem reescreva histórico.
