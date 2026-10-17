# STATE — ponto de retomada

Qualquer agente deve conseguir retomar só com este arquivo + a seção ativa do `ROADMAP.md`, sem a conversa anterior. Curto: o que não for estado atual sai daqui.

**Atualizado:** 2026-10-17 · **Marco ativo:** v1.0 — validação operacional pendente (itens abertos de §13 do `ROADMAP.md`) · **Estado:** IN_PROGRESS

## O que funciona hoje (confirmado no código)
- Pacote `agent-governor` versão `1.0.0` (`pyproject.toml`), release local instalável de 2026-09-13.
- CLI com `init`, `hook`, `verify`, `task create|inspect|activate`, `validate`, `audit`, `doctor`, `install antigravity` e desinstalação; perfis generic, Python, Node, Android/Kotlin e n8n/Telegram; circuit breaker em SQLite; recibos fingerprintados.
- CI `test` (`python -m unittest discover -s tests -v`) passou no último commit (`c5b71a7`, 2026-09-13).

## Última atividade
- ID / commit: `c5b71a7` (2026-09-13) — release agent governor v1.0.0.
- Resultado real: CI `test` com sucesso.
- Testes executados nesta sessão de padronização (2026-10-17, só documentação): `PYTHONPATH=src python3 -m unittest discover -s tests` → 17 de 18 passam. `test_successful_receipt_is_invalidated_by_mutation` falha porque o ambiente não tem o executável `python` (o teste chama `python -c pass`). Falha igual no `main`; não tem relação com a mudança.
- Evidência: CI do GitHub Actions; `CHANGELOG.md` 1.0.0.

## Próxima ação
- Validar no Antigravity real a instalação protegida (IN-002 a IN-005) e iniciar o piloto em worktree (IN-007), conforme `ROADMAP.md` §7 e §14.

## Bloqueios e aprovações humanas
- Gate remoto (branch protection com checks obrigatórios) depende de configuração do dono do repositório (AU-005).
- Isolamento do executável e da política mestre exige configuração do host (SE-001 a SE-006).

## Divergências entre roadmap e implementação
- `ROADMAP.md` §3 lista versões 0.1.1 a 1.0, mas a release 1.0.0 foi publicada com itens da §13 ainda abertos (gate remoto, isolamento, piloto, pacote com checksums, tag). Não há tags no repositório.
- O README ainda tem uma seção chamada "Segurança e limites da v0.1".
- `CHANGELOG.md` e `GEMINI.md` estão em inglês; o padrão pede pt-BR.
