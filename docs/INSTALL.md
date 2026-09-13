# Instalação por projeto

O Governor é instalado uma vez no computador e inicializado dentro de cada repositório.

## Windows PowerShell

```powershell
py -3.11 -m pip install "git+https://github.com/playertwo1/agent-governor.git@main"
cd C:\Projetos\meu-projeto
py -3.11 -m agent_governor.cli init . --profile generic
py -3.11 -m agent_governor.cli task create TASK-001 `
  --objective "Descrever a tarefa" `
  --allowed-path "src/**" `
  --allowed-path "tests/**" `
  --required-command "python -m unittest discover -s tests -v" `
  --root .
py -3.11 -m agent_governor.cli task activate TASK-001 --root .
py -3.11 -m agent_governor.cli install antigravity --root .
py -3.11 -m agent_governor.cli doctor --root .
```

Para Android, use `--profile android-kotlin` e declare os módulos reais. No Windows, o comando usual é `.\gradlew.bat test`; ele deve ser declarado como uma string do contrato.

## Linux/macOS

```bash
python3 -m pip install "git+https://github.com/playertwo1/agent-governor.git@main"
cd ~/src/meu-projeto
python3 -m agent_governor.cli init . --profile generic
python3 -m agent_governor.cli task create TASK-001 \
  --objective "Descrever a tarefa" \
  --allowed-path 'src/**' \
  --allowed-path 'tests/**' \
  --required-command 'python -m unittest discover -s tests -v' \
  --root .
python3 -m agent_governor.cli task activate TASK-001 --root .
python3 -m agent_governor.cli install antigravity --root .
python3 -m agent_governor.cli doctor --root .
```

## Ciclo de uma tarefa

1. Edite o contrato apenas para declarar a tarefa, os caminhos e os comandos esperados.
2. Ative a tarefa.
3. Abra ou reabra o workspace no Antigravity.
4. Execute a implementação dentro do escopo.
5. Rode `validate` e depois `audit`.
6. Envie o JSON de `audit` ao Codex para revisão independente.

```bash
python -m agent_governor.cli validate --root .
python -m agent_governor.cli audit --base HEAD --root .
```

Política, contrato, perfil e `.agents/hooks.json` podem ser versionados. O banco, violações e recibos são ignorados pelo `.governor/.gitignore`.

## Remoção

```bash
python -m agent_governor.cli uninstall antigravity --root .
```

A remoção retira somente a entrada `agent-governor` e preserva os demais hooks.

