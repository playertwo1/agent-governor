# Arquitetura

## Princípios

1. **Autorização fora do modelo:** prompts explicam; código restringe.
2. **Fail-closed:** política ausente, JSON inválido ou payload inválido bloqueiam.
3. **Menor escopo:** cada tarefa declara caminhos e limite de arquivos.
4. **Autoproteção:** o agente não altera política, hooks ou workflow do Governor.
5. **Evidência antes de “pronto”:** o gate pós-ação deve provar escopo e validação.
6. **Humano como autoridade:** mudanças de dependência, publicação e arquitetura pedem aprovação.

## Componentes

- `adapters.py`: converte payloads de ferramentas para `{tool, command, path}`.
- `engine.py`: avalia política universal e contrato do projeto.
- `cli.py hook`: protocolo stdin/stdout para hooks.
- `cli.py verify`: valida arquivos do diff.
- `.governor/policy.json`: política executável.
- `.governor/task-contract.json`: autorização específica da tarefa.
- `.governor/project-profile.json`: stack e comandos relevantes do projeto.
- `.governor/violations.jsonl`: trilha de violações.

## Ordem de decisão

1. Configuração válida?
2. Comando corresponde a bloqueio ou aprovação obrigatória?
3. Escrita ocorre fora do workspace?
4. Caminho é protegido?
5. Caminho está autorizado pelo contrato?
6. Aplica decisão padrão.

Regras mais restritivas são avaliadas primeiro. Uma negação não pode ser rebaixada pelo agente executor.

