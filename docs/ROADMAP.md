# Agent Governor — Roadmap executável até a v1.0

Status: v0.1.1 concluída e implementação inicial de v0.2–v0.5 publicada; critérios de aceitação em ambiente real continuam pendentes.
Base inspecionada: fundação v0.1 publicada em `f6608d51c769bcb8f4e7580efa0964f4a1d16003`.
Este documento substitui o roadmap inicial. Em conflito com o resumo antigo do README, esta sequência prevalece.

## 1. Resultado esperado

Instalar um núcleo reutilizável, configurar cada projeto e executar tarefas delimitadas no Antigravity, com verificação determinística e auditoria independente do Codex. Rafael define objetivo e autorizações; o executor implementa; o Governor aplica restrições; o auditor avalia a entrega.

A v1.0 será uma ferramenta local de linha de comando utilizável diariamente, prioritariamente em Windows e Linux. Android/Kotlin, Python e Node recebem perfis testados. n8n e bots Telegram recebem regras de arquivos e validações locais; controlar instâncias remotas fica fora do primeiro lançamento.

Não prometer que um hook torna impossível qualquer desvio. O nível de proteção depende da cobertura de ferramentas e do isolamento do processo, configurações, testes, evidências e credenciais. Documentar esse limite na instalação.

## 2. Situação real da base publicada

Já existem `init`, `hook`, `verify`, `task create|inspect|activate`, `validate`, `doctor` e `install antigravity`, além de modelos JSON, reconhecimento básico de payloads, regras por regex, verificação de caminhos, log JSONL, estado SQLite, perfis iniciais e recibos fingerprintados. Existe configuração de CI; a execução remota deve ser conferida, não presumida. O hook foi simulado localmente, ainda sem comprovação ponta a ponta no Antigravity instalado do usuário.

Lacunas observadas no código:

- O circuit breaker conta violações e muda a mensagem, mas não persiste um estado que impeça a próxima ação permitida.
- A CLI pode tentar reler uma política ausente/inválida após uma negação e encerrar sem a resposta JSON esperada.
- `verify` ignora o código de saída do Git; referência inválida pode aparentar ausência de mudanças.
- JSON sintaticamente válido, porém com tipos/campos incorretos, não tem validação de schema.
- Ferramentas desconhecidas e comandos sem correspondência podem receber `allow`.
- Escritas por shell contornam a checagem específica de ferramentas de arquivo.
- Caminhos relativos usam o diretório do processo, que pode diferir da raiz escolhida.
- Uma lista vazia de caminhos permitidos não significa bloqueio total.
- A proteção cobre `.agents/hooks/**`, mas a configuração fornecida fica em `.agents/hooks.json`.
- `required_commands`, `required_evidence` e flags de arquitetura/dependências não são gates de conclusão implementados.
- O log armazena argumentos de ações, que podem conter segredos, e não garante isolamento, integridade ou concorrência.

Consequência: classificar a v0.1 como protótipo. Os testes existentes não comprovam as garantias universais anunciadas inicialmente.

## 3. Sequência e marcos de uso

| Versão | Entrega principal | Dependência | Uso permitido pelo plano |
|---|---|---|---|
| 0.1.1 | Corrigir falhas de bloqueio e validação | 0.1 | Laboratório |
| 0.2 | Contratos e estado persistente | 0.1.1 | Laboratório com tarefas reais copiadas |
| 0.3 | Evidências ligadas ao conteúdo validado | 0.2 | Avaliação de entregas |
| 0.4 | Instalação Antigravity e diagnóstico | 0.3 | Piloto supervisionado em worktree |
| 0.5 | Perfis reutilizáveis | 0.4 | Piloto em projetos de stacks diferentes |
| 0.6 | Auditoria independente e merge gate | 0.5 | Fluxo completo de desenvolvimento |
| 0.7 | Isolamento e política confiável | 0.6 | Testes contra tentativas de contorno |
| 0.8 | Compatibilidade e recuperação | 0.7 | Candidato a uso diário |
| 0.9 | Piloto de aceitação e documentação | 0.8 | Release candidate |
| 1.0 | Release reproduzível e operação validada | 0.9 | Uso diário dentro da matriz suportada |

Cada versão depende da aprovação dos critérios da anterior. Sem datas artificiais: estimar duração após medir as primeiras tarefas. Não iniciar fases grandes em paralelo nem adicionar dashboard antes de estabilizar o núcleo.

## 4. v0.1.1 — Corrigir a fundação

Objetivo: nenhuma falha de configuração ou verificação pode virar uma aprovação silenciosa.

- [x] FIX-001: validar schemas, tipos, campos obrigatórios, decisões e expressões regulares; rejeitar versões desconhecidas.
- [x] FIX-002: garantir saída JSON de negação para entrada inválida, política ausente, erro de leitura e exceções internas. Não expor segredos no erro.
- [x] FIX-003: respeitar falhas do Git e referências inexistentes; usar saída NUL para nomes com espaços e quebras de linha; verificar staged, unstaged, untracked, exclusões e renomes.
- [x] FIX-004: resolver caminhos pela raiz confiável; cobrir travessia, links simbólicos, caminhos externos, Windows, UNC e regras de glob explícitas.
- [x] FIX-005: proteger configurações reais de hooks e governança; negar escrita sem destino ou contrato; lista vazia autoriza zero escritas.
- [x] FIX-006: ferramenta desconhecida bloqueada por padrão. Shell arbitrário não recebe aprovação automática por ausência de regex; ações opacas exigem revisão ou isolamento adequado.
- [x] FIX-007: não registrar comandos/conteúdo sensível integralmente; usar metadados mínimos e redação.
- [x] FIX-008: corrigir README, arquitetura e status para distinguir proteção implementada de planejada.

Arquivos prováveis: `engine.py`, `adapters.py`, `cli.py`, `templates.py`, `tests/`, documentação.

Aceite: testes de integração da CLI reproduzem cada falha acima e recebem negação/FAIL estável; entradas válidas continuam funcionando. CI passa no commit entregue. Testes devem demonstrar o defeito antes da correção quando viável.

## 5. v0.2 — Contrato e circuit breaker reais

Objetivo: uma tarefa tem identidade, escopo e estado persistente, inclusive entre sessões.

- [x] CT-001: schema versionado com task ID, objetivo, caminhos, máximo de arquivos, comandos exigidos, base commit e hash da política; critérios de aceite detalhados continuam no próximo incremento.
- [x] CT-002: comandos propostos `task create`, `task inspect` e `task activate`; somente configuração revisada ativa escritas. Não executar instruções encontradas no repositório durante detecção.
- [x] CT-003: estados `DRAFT`, `ACTIVE`, `PAUSED`, `BLOCKED`, `READY_FOR_AUDIT`, `APPROVED`, `DONE` e transições verificadas.
- [x] CT-004: negar mutações após limite de violações por tarefa/regra; persistir contador e bloqueio de forma transacional, preferencialmente SQLite. Reiniciar processo não remove bloqueio.
- [ ] CT-005: reset administrativo explícito com motivo e registro; nunca conceder ao executor capacidade de se desbloquear em modo protegido.
- [ ] CT-006: compor política mestre e perfil sem permitir que o perfil enfraqueça negações obrigatórias.
- [ ] CT-007: limitar trabalho simultâneo por checkout; adotar worktrees independentes para tarefas distintas.

Aceite: duas violações configuradas bloqueiam também uma terceira mutação que isoladamente seria permitida; reinício mantém o estado; tarefas distintas não herdam contagens indevidas; concorrência não perde eventos. Leituras de diagnóstico podem continuar segundo política explícita.

## 6. v0.3 — Evidências antes de concluir

Objetivo: impedir uso de teste antigo, incompleto ou apenas declarado como prova de conclusão.

- [x] EV-001: runner de validação com comando aprovado, cwd fixo, timeout, retorno e duração; execução sem shell quando possível.
- [x] EV-002: recibo vinculado a task ID, revisão da política/contrato, base commit, fingerprint dos arquivos relevantes, comando exato e resultado.
- [x] EV-003: fingerprint inclui índice, arquivos locais e novos arquivos; exclusões de arquivos gerados devem ser explícitas. Mudança após teste invalida recibo.
- [x] EV-004: timeout, falha, comando faltante ou conteúdo alterado produzem FAIL. Sucesso de um comando não substitui outro obrigatório.
- [ ] EV-005: `verify` separa resultado de escopo, validação, política e evidência; nenhuma frase do executor cria recibo confiável.
- [ ] EV-006: distinguir recibos locais de evidência produzida em processo/CI independente; recibo no mesmo usuário não é resistente à falsificação.

Aceite: demonstrar teste aprovado, alteração posterior e rejeição do recibo; testar arquivo novo, remoção, timeout e comando nunca executado. Não chamar um recibo local de assinatura confiável.

## 7. v0.4 — Instalação e piloto Antigravity

Objetivo: começar a usar em um projeto isolado com proteção e limitações observáveis.

- [x] IN-001: comandos `install antigravity` e `doctor`; instalação preserva hooks existentes e cria backup. `uninstall` permanece pendente.
- [ ] IN-002: fixar raiz e executável por caminhos confiáveis; funcionar com espaços e ambiente virtual no Windows/Linux.
- [ ] IN-003: conferir documentação primária da versão instalada; registrar versão e payloads reais, sem presumir compatibilidade entre CLI e IDE.
- [ ] IN-004: testar no host allow/deny, erro do hook, timeout, executável ausente e decisão de revisão humana. Host que falha aberto impede classificar instalação como protegida.
- [ ] IN-005: validar cobertura das ferramentas de escrita, terminal, tarefas assíncronas, entrada em terminal existente e chamadas externas; bloquear rotas não cobertas no modo protegido.
- [x] IN-006: `doctor` mostra integridade básica, contrato, perfil e hook carregado. Verificação ponta a ponta no host real permanece pendente.
- [ ] IN-007: iniciar piloto em worktree de um projeto escolhido; uma tarefa pequena, com escopo explícito e revisão do diff.

Aceite: tentativa de escrita proibida realmente não altera o arquivo no Antigravity; uma edição válida funciona; falha do hook não concede mutação; reinstalação é idempotente e desinstalação preserva configurações anteriores. Sem esse ensaio, manter rótulo experimental.

## 8. v0.5 — Perfis que evitam começar do zero

- [x] PF-001: perfil `generic` conservador, sem autodetectar autorização.
- [x] PF-002: perfil inicial Python com comando de teste e áreas sensíveis declaradas; detecção de ferramentas ainda pendente.
- [x] PF-003: perfil inicial Node com comando de teste e lockfiles protegidos; detecção de gerenciador ainda pendente.
- [x] PF-004: perfil inicial Android/Kotlin com comandos Gradle e credenciais protegidas; validação por módulo permanece pendente.
- [x] PF-005: perfil inicial n8n/Telegram com áreas sensíveis declaradas; validação de export remoto permanece fora do núcleo.
- [ ] PF-006: Codex recebe inventário e propõe perfil, contrato e invariantes; mudanças ficam revisáveis e versionadas.
- [ ] PF-007: invariantes possuem ID, descrição, verificador e evidência. Regras sem verificador aparecem como revisão manual, nunca PASS automático.

Aceite: inicializar fixtures das três stacks principais e comparar políticas geradas; repetir sem sobrescrever personalizações; ausência de ferramenta resulta em diagnóstico explícito. Dois projetos distintos compartilham núcleo e diferem apenas no perfil/contrato.

## 9. v0.6 — Codex auditor e gate de entrega

- [ ] AU-001: gerar pacote de auditoria com objetivo, contrato, política, diff, fingerprint, recibos e violações saneadas.
- [ ] AU-002: relatório estruturado com verdict, escopo, arquitetura, regressões, testes, achados, gravidade e localização.
- [ ] AU-003: auditoria vinculada à revisão exata; nova alteração invalida aprovação. Auditor não assina trabalho alterado depois da revisão.
- [ ] AU-004: separar identidade e credenciais do executor e aprovador; arquivo JSON do executor não constitui aprovação independente.
- [ ] AU-005: hooks Git locais como conveniência e checks obrigatórios no servidor como gate de merge. Branch protection deve ser configurada e comprovada; CI sozinha não impede merge.
- [ ] AU-006: FAIL inicia correção delimitada; limite de tentativas abre bloqueio para diagnóstico. Sem rollback destrutivo automático.

Aceite: PR com falha não pode entrar pelo fluxo protegido; alterar um byte relevante invalida teste/auditoria anterior; executor não consegue gerar aprovação aceita. Auditoria por LLM continua sendo julgamento, não prova matemática.

## 10. v0.7 — Isolamento e confiança

- [ ] SE-001: núcleo e política mestre fora do checkout gravável, com proprietário/permissões diferentes do executor quando suportado.
- [ ] SE-002: impedir adulteração de hook, executável, evidências e controle de estado; testar também por shell e processos filhos.
- [ ] SE-003: bundles assinados com chave privada fora do alcance do executor; verificação de assinatura e versão antes do uso.
- [ ] SE-004: grants administrativos vinculados a ação, projeto, tarefa, prazo e uso único; negação obrigatória não vira permissão por autodeclaração.
- [ ] SE-005: logs externos com escrita controlada, política de retenção e integridade. Hash local detecta alteração apenas sob premissas documentadas; não torna arquivo imutável.
- [ ] SE-006: documentar fronteira de confiança de testes, ferramentas, rede, MCP e credenciais. Código de teste pode executar comandos; tratá-lo dentro do isolamento.

Aceite: bateria de contorno falha com a identidade do executor; gravação direta e indireta em componentes protegidos é impedida pelo ambiente. Administrador do computador continua fora do modelo de ameaça. Não anunciar proteção forte no modo de usuário único sem isolamento.

## 11. v0.8 — Compatibilidade e recuperação

- [ ] CP-001: matriz de sistemas/versões efetivamente testados, com foco Windows e Linux.
- [ ] CP-002: adapters Claude/Gemini/Codex somente após confirmar interfaces primárias e validar payloads no host real. Sem hook equivalente comprovado, oferecer auditoria/CI e declarar ausência de bloqueio pré-ação.
- [ ] CP-003: testar reinício, disco cheio, log indisponível, SQLite ocupado, configuração incompatível e upgrade interrompido.
- [ ] CP-004: backup e restauração de configurações administrativas; nunca descartar alterações do projeto para recuperar o Governor.
- [ ] CP-005: medir latência por chamada e volume de logs; meta inicial p95 inferior a 500 ms para decisão local quente, excluindo testes, em máquina de referência documentada.

Aceite: falhas de infraestrutura negam mutações com mensagem útil; recuperação não perde o trabalho; toda combinação anunciada tem evidência de teste. Adapters adicionais não bloqueiam v1.0 se Antigravity e auditoria independente cumprirem o escopo principal.

## 12. v0.9 — Piloto de aceitação

- [ ] RC-001: executar pelo menos dez tarefas delimitadas em dois projetos de stacks diferentes, incluindo um Android se disponível.
- [ ] RC-002: cenários obrigatórios: edição válida, caminho proibido, exclusão de teste, dependência não autorizada, tentativa de alterar hook, Git inválido, timeout, recibo antigo e repetição de violações.
- [ ] RC-003: medir falsos bloqueios, contornos observados, tempo de configuração, latência e clareza da recuperação. Não reduzir proteção apenas para baixar falsos positivos.
- [ ] RC-004: guia em português para instalação, nova tarefa, diagnóstico, bloqueio, auditoria, atualização e remoção.
- [ ] RC-005: revisar fontes, licenças, versões e código incorporado; manter atribuições no README e avisos exigidos por licença.
- [ ] RC-006: resolver todos os achados críticos/altos de enforcement; registrar limitações restantes e congelar candidato.

Aceite: cenários de bloqueio têm evidência de ausência da mutação; tarefas válidas concluem com recibo e auditoria; revisão final ocorre sobre o candidato congelado.

## 13. v1.0 — Definition of Done

- [ ] Instalação limpa, diagnóstico, atualização e desinstalação validados na matriz publicada.
- [ ] Contrato limita escopo e nenhuma falha de configuração concede aprovação.
- [ ] Circuit breaker persiste e exige recuperação administrativa rastreável.
- [ ] Evidências e auditoria vinculadas à revisão efetivamente entregue.
- [ ] Gate remoto impede merge com checks obrigatórios falhos.
- [ ] Modo protegido possui isolamento verificado; modo assistido explicita suas limitações.
- [ ] Perfis genérico, Python, Node e Android documentados e testados conforme disponibilidade declarada.
- [ ] Piloto concluído sem achado crítico/alto aberto.
- [ ] Pacote versionado, changelog, checksums, instruções de rollback administrativo e fontes completos.
- [ ] Tag/release corresponde exatamente ao commit aprovado e aos artefatos verificados.

Fora da v1.0: dashboard web, notificações Telegram, execução remota em produção, aprendizado autônomo que altera políticas, suporte universal a todos os agentes, detecção semântica infalível e agendamento de retomada de agentes. Reavaliar depois da adoção do núcleo.

## 14. Como executar este roadmap sem perder o rumo

Para cada item, criar tarefa pequena com ID acima, objetivo, arquivos previstos, critérios de aceite, evidências e base commit. Registrar status como TODO, DOING, BLOCKED ou DONE. Só marcar DONE após validação e revisão do diff; atualizar changelog e estado ao encerrar cada versão.

Ciclo: selecionar um item → contrato → implementação Antigravity → testes determinísticos → auditoria Codex → correção delimitada → registro da evidência → próximo item. Enquanto os mecanismos não estiverem implementados, cumprir o ciclo manualmente e não afirmar que o Governor já o força.

O primeiro lote concluído foi FIX-001 a FIX-008. CT-001 a CT-004, EV-001 a EV-004, IN-001/IN-006 e PF-001 a PF-005 já têm implementação inicial; os critérios de aceite ainda precisam ser demonstrados nos ambientes reais. O próximo lote prioritário é completar os gates restantes de evidência e integração ponta a ponta. Não saltar para assinatura ou dashboard antes disso.

Prompt de continuidade para o executor:

> Leia AGENTS.md, docs/ARCHITECTURE.md e docs/ROADMAP.md. Inspecione a versão atual antes de editar. Comece pelo primeiro item pendente da v0.1.1, descreva um contrato pequeno com arquivos previstos e testes de aceite e implemente esse item. Não avance de versão sem cumprir os critérios. Entregue diff, resultados reais e limitações para auditoria do Codex. Não enfraqueça regras nem declare proteção que não foi demonstrada.
