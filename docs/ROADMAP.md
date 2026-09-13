# Roadmap

## Fase 0 — Fundação (v0.1)

- [x] CLI instalável sem dependências de runtime.
- [x] Motor fail-closed.
- [x] Política universal inicial.
- [x] Task Contract e Project Profile.
- [x] Adapter de payload Antigravity.
- [x] PreToolUse hook.
- [x] Scope verifier.
- [x] Eventos JSONL e circuit breaker.
- [x] Testes unitários e CI.

## Fase 1 — Evidência confiável (v0.2)

- [ ] Registrar comando, exit code, hash do diff e timestamp.
- [ ] Impedir “concluído” sem os testes exigidos.
- [ ] Validar `forbidden_paths`, alterações de arquitetura e dependências no diff.
- [ ] Criar perfis `android-kotlin`, `python`, `node`, `n8n`, `telegram-bot` e `generic`.
- [ ] Detectar segredos com ferramenta dedicada e resultado atestado.
- [ ] Assinar política mestre e detectar adulteração.

## Fase 2 — Instalação universal (v0.3)

- [ ] `governor init --detect` com perfil sugerido e revisão Codex.
- [ ] Merge seguro com `AGENTS.md`, `GEMINI.md` e configurações existentes.
- [ ] Instalação global somente leitura.
- [ ] Adapters e testes de contrato para Codex, Claude Code e Gemini CLI.
- [ ] Hooks pós-ação e de encerramento.
- [ ] JSON estruturado de auditoria Codex.

## Fase 3 — Isolamento e operação (v1.0)

- [ ] Policy bundles versionados e assinados.
- [ ] Trilhas append-only fora do workspace.
- [ ] Aprovação humana com grants de curta duração.
- [ ] Sandbox por projeto e separação de identidade do agente.
- [ ] Dashboard de violações, drift e auditorias.
- [ ] Instalação/rollback multiplataforma, incluindo Windows.

