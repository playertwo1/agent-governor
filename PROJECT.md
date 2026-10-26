# PROJECT — Agent Governor

Contrato de visão. Atualize quando o projeto nasce e quando a visão muda; o resto (marcos, estado) fica em `ROADMAP.md` e `STATE.md`. Resumo do [README](README.md), do [ROADMAP](ROADMAP.md) §1 e §13 e de [ARCHITECTURE](docs/ARCHITECTURE.md).

## Problema
Arquivos como `AGENTS.md`, `GEMINI.md` e prompts são orientação probabilística. Regras críticas de agentes de programação (comandos destrutivos, bypass de testes, push, dependências, escopo) precisam ser verificadas fora do modelo.

## Para quem
Rafael, para governar tarefas de agentes (inicialmente no Google Antigravity) em seus projetos, com auditoria independente do Codex.

## MVP — até três fluxos que entregam valor
1. Bloqueio antes da ferramenta: o hook `PreToolUse` decide `allow`, `ask` ou `deny` com política universal e contrato da tarefa, fail-closed.
2. Verificação depois da ação: `governor verify` checa o diff contra o escopo; `governor validate` grava recibos fingerprintados.
3. Pacote de auditoria: `governor audit` junta tarefa, arquivos, recibos e achados para a revisão do Codex.

## Fora do MVP (escrito para não voltar escondido)
- Dashboard web, notificações Telegram, execução remota em produção.
- Aprendizado autônomo que altera políticas; suporte universal a todos os agentes; detecção semântica infalível.
- Adapters Codex/Claude antes de confirmar interfaces primárias e validar payloads no host real.

## Restrições
- Plataforma/ambiente: Python 3.11+, CLI local, prioridade Windows e Linux; estado em SQLite e log JSONL.
- Dados sensíveis e privacidade: não registrar comandos ou conteúdo sensível integralmente (redação); a proteção depende do isolamento do executável e da política.
- Custos, licenças, integrações obrigatórias: licença MIT; nenhum código de terceiros copiado (fontes estudadas listadas no README).

## Como saberemos que funcionou
Definition of Done da v1.0 (`ROADMAP.md` §13): escrita proibida não altera o arquivo no Antigravity real, gate remoto impede merge com checks falhos e piloto concluído sem achado crítico ou alto.

## Autoridade de produto
Rafael define objetivo e autorizações; o executor implementa; o Governor aplica restrições; o auditor avalia a entrega.

## Alternativas consideradas
Projetos open source estudados como referência conceitual (agent-guard, agent-guardrails, claude-code-hooks, claude-code-guardrails), sem incorporação de código; detalhes no README.
