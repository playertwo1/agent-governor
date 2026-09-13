# Agent Governor

Camada universal e determinística de governança para agentes de programação. O agente pode **propor** uma ação; o Governor decide se ela pode ser executada.

> Estado: **v1.0.0 (release local instalável)**. Integração suportada: Google Antigravity `PreToolUse`. Inclui contratos persistentes, circuit breaker SQLite, recibos fingerprintados, perfis iniciais, auditoria estruturada, diagnóstico, instalação e remoção segura. Adapters específicos para Codex e Claude continuam fora da matriz suportada desta release.

## Por que existe

Arquivos como `AGENTS.md`, `GEMINI.md` e prompts são orientação probabilística. Regras críticas precisam ser verificadas fora do modelo. O Agent Governor combina:

- política universal (comandos destrutivos, bypass de testes, push e dependências);
- contrato limitado para cada tarefa;
- proteção contra modificação do próprio Governor;
- bloqueio antes da ferramenta (`PreToolUse`);
- validação do `git diff` depois da execução;
- log JSONL e circuit breaker para violações repetidas;
- comportamento **fail-closed** quando a configuração está ausente ou inválida.

## Fluxo

```mermaid
flowchart TD
    U["Tarefa do usuário"] --> C["Task Contract"]
    C --> G["Pre-action gate"]
    G -->|allow| A["Agente executor"]
    G -->|ask| H["Aprovação humana"]
    G -->|deny| B["Bloqueio + log"]
    A --> V["Diff + testes + evidências"]
    V -->|pass| X["Auditoria Codex"]
    V -->|fail| B
```

## Instalação local

Requer Python 3.11+.

```bash
python -m pip install -e .
governor init /caminho/do/projeto --profile generic
```

Edite `.governor/task-contract.json` antes da tarefa:

```json
{
  "schema_version": 1,
  "task_id": "RIN-042",
  "objective": "Implementar conexão Android com o daemon",
  "allowed_paths": ["android/**", "shared/protocol/**", "tests/**"],
  "forbidden_paths": [".governor/**", "auth/**"],
  "max_files_changed": 8,
  "required_commands": ["./gradlew test", "./gradlew lint"],
  "required_evidence": [],
  "architecture_changes": false,
  "dependency_changes": false
}
```

## Integração com Antigravity

Copie `integrations/antigravity/hooks.json` para `.agents/hooks.json` no projeto governado. Se o Governor estiver instalado apenas no ambiente virtual, ajuste o comando para o executável correto.

Teste o gate sem executar nenhuma ação:

```bash
printf '%s' '{"toolCall":{"name":"run_command","args":{"CommandLine":"git push --force"}}}' | governor hook
```

Resposta esperada:

```json
{"decision":"deny","reason":"[GIT-001] Destructive Git history operation blocked."}
```

O contrato oficial do Antigravity aceita `allow`, `deny`, `ask`, `force_ask` e `deny_unless_prior_grant`. O `hooks.json` registra o Governor para todas as ferramentas.

## Verificação pós-ação

```bash
governor verify --base HEAD~1
```

O comando bloqueia a aprovação quando o diff excede `max_files_changed` ou contém arquivos fora de `allowed_paths`. O comando `validate` executa os comandos declarados e grava recibos fingerprintados em `.governor/evidence/`; alterações posteriores invalidam a prova.

Depois da validação, gere o pacote que o Codex deve revisar:

```bash
governor audit --base HEAD
```

O resultado é JSON com tarefa, arquivos alterados, recibo de evidência e achados. `PASS` significa que os gates determinísticos passaram; ainda é necessária a revisão técnica do Codex.

## Segurança e limites da v0.1

- A proteção é tão forte quanto o isolamento do executável e dos arquivos de política. Para uso rigoroso, mantenha a política mestre fora do workspace e somente leitura para o agente.
- Regex de shell não substitui sandbox do sistema operacional. Use também permissões e sandbox nativos do Antigravity.
- `force_ask` depende da interface do Antigravity para obter aprovação humana.
- O Governor não executa comandos propostos; apenas autoriza, pede confirmação ou bloqueia.
- Nenhum código de terceiros foi copiado nesta versão. As fontes abaixo foram usadas como referências arquiteturais e de interface.

## Fontes e projetos estudados

### Documentação primária

- [Google Antigravity — Hooks](https://antigravity.google/docs/hooks): schema de `.agents/hooks.json`, eventos, payload `toolCall` e decisões de `PreToolUse`.
- [Google Antigravity — Permissions](https://antigravity.google/docs/permissions): camada nativa de permissões e precedência de regras.
- [Google Antigravity — Rules](https://antigravity.google/docs/ide/rules): regras globais e de workspace.
- [OpenAI — Harness engineering](https://openai.com/index/harness-engineering/): documentação curta como mapa e invariantes verificáveis no repositório.
- [OpenAI Codex — AGENTS.md](https://developers.openai.com/codex/guides/agents-md/): instruções hierárquicas para projetos auditados pelo Codex.

### Projetos open source

| Projeto | Licença observada | Ideia estudada/aproveitada conceitualmente |
|---|---:|---|
| [toininoi/agent-guard](https://github.com/toininoi/agent-guard) | Apache-2.0 | boundary de autorização, normalização multi-driver, invariantes e eventos |
| [logi-cmd/agent-guardrails](https://github.com/logi-cmd/agent-guardrails) | MIT | task brief, allowed paths, limite de escopo, evidência e review gate |
| [shanraisshan/claude-code-hooks](https://github.com/shanraisshan/claude-code-hooks) | MIT | catálogo e ciclo de vida de hooks |
| [h3rrkent/claude-code-guardrails](https://github.com/h3rrkent/claude-code-guardrails) | licença não encontrada na revisão | defesa em camadas; usado somente como referência pública, sem incorporação de código |

Os projetos `roboticforce/agent-guardrails`, `laundromatic/agent-guardrails` e `google-antigravity/antigravity-sdk-python` foram citados em uma exploração inicial, mas não entram como fonte desta versão porque os endereços ou conteúdos não foram confirmados de forma suficiente durante a implementação. Essa distinção evita atribuir funcionalidade a um repositório errado.

## Roadmap resumido

- **v1.0.0 entregue:** motor fail-closed, contrato, Antigravity hook, scope check, log, circuit breaker, recibos, perfis, auditoria e instalador.
- **Pós-v1.0:** bundles assinados, armazenamento externo append-only, isolamento forte e adapters adicionais.

Veja [ROADMAP.md](docs/ROADMAP.md) e [ARCHITECTURE.md](docs/ARCHITECTURE.md).

O passo a passo completo para instalar em novos projetos está em [INSTALL.md](docs/INSTALL.md). O histórico da release está em [CHANGELOG.md](CHANGELOG.md).

## Licença

MIT. Consulte [LICENSE](LICENSE).
