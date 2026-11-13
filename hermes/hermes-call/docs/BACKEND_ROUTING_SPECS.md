# Especificações de Roteamento e Agentes (Backend)

Este documento centraliza a estrutura de dados e as regras de negócio para a implementação das novas lógicas de roteamento no backend (Níveis 2 e 3 do Orquestrador).

## 1. Estrutura do Agente (`Agent` / `Profile`)
Para suportar o Kanban Dinâmico (Nível 2) e o Fluxograma Inteligente (Nível 3), a tabela de Agentes precisa das seguintes colunas/propriedades novas:

- `logic_type` (Enum/String): Tipo da regra exata.
  - Valores: `none`, `tag`, `stage`, `time`, `contains`, `exact`, `similar`.
- `trigger` (String): O valor da regra (ex: "vip", "08:00-18:00", "comprar").
- `ai_trigger` (String/Text): Instrução semântica para o LLM Triador (Ex: "Cliente quer saber o preço").
- `priority` (Enum/String): Como resolver o conflito caso a IA e a Lógica Exata deem *match* ao mesmo tempo.
  - Valores: `rule_first` (Forçar Lógica), `ai_first` (Deixar IA Triadora decidir).

## 2. Configurações Globais do Workspace (Nível 1 e Hierarquia)
Além da tabela de agentes, a tabela de configurações do workspace (`workspace_settings`) precisa armazenar os ponteiros de roteamento globais:

- `default_voice_agent_id` (UUID): O agente que atende qualquer ligação de voz caso não haja regras específicas (Nível 1).
- `default_text_agent_id` (UUID): O agente que responde qualquer WhatsApp de texto caso não haja regras específicas (Nível 1).
- `routing_hierarchy` (Array de Strings): Ordem de avaliação das regras no Nível 2. Ex: `['time', 'stage', 'tag', 'exact', 'contains', 'similar']`.

## 3. Fluxo do Roteador (Engine de Decisão)
Quando uma nova mensagem ou ligação chega, o backend deve passar pelo **Router Node (Triagem Central)** respeitando os níveis:

0. **Verificação de Nível:**
   - O backend lê as configurações para saber se o usuário está usando Roteamento Nível 1, 2 ou 3.
   - **Se Nível 1:** Vai direto para o `default_voice_agent_id` (se for áudio/ligação) ou `default_text_agent_id` (se for texto). Fim.

1. **Avaliação Estática (Regras Exatas - Nível 2 e 3):**
   - O backend varre os agentes ativos.
   - Verifica `logic_type`.
   - Se `logic_type == 'time'`, checa a hora do servidor `time.Now()` contra o `trigger`.
   - Se `logic_type == 'tag'` ou `stage`, checa o banco de dados do Lead.
   - Se `contains`, `exact` ou `similar`, roda regex/comparação simples na última mensagem recebida.
   
2. **Avaliação IA (Intenção):**
   - Manda a mensagem pro LLM Triador (Groq/Gemini) junto com os `ai_trigger` disponíveis.
   - Pede pro LLM retornar o ID do agente ideal (JSON estruturado).

3. **Resolução de Conflito (`priority`):**
   - Se a Avaliação Estática disse "Agente A" e a Avaliação IA disse "Agente B".
   - O backend olha a flag `priority`. Se `rule_first`, roteia pro A. Se `ai_first`, roteia pro B.

## 3. Backlog de Ideias Avançadas (Próximas Fases)
Ideias levantadas no frontend que exigirão arquitetura backend no futuro:

* **Swarm (Multi-Agentes):** Capacidade de um nó colocar 2 IAs num loop interno para debater (Consenso/Revisão) antes de disparar o webhook de resposta para a fila do WhatsApp.
* **Cron Jobs (Agendamento Ativo):** Worker no backend rodando a cada minuto checando horários para acordar agentes que devem fazer follow-ups ativos (sem *inbound* do cliente).
* **Webhook Listeners Inbound:** Endpoint aberto na API (ex: `/api/webhooks/rdstation`) que cria o contexto da conversa e injeta direto no prompt do agente, disparando a primeira mensagem pro WhatsApp.
* **Nodes Utilitários:**
  - `Limpar Memória`: Backend apaga/trunca o vetor de mensagens do Redis/Postgres para aquele session_id.
  - `HTTP Request (IA)`: O Agente LLM cospe um JSON com a URL e Body; o backend dispara o `axios/fetch` no meio da *chain* e devolve a resposta pra ele continuar a falar.
