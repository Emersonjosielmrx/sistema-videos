# 🚀 Master Backend Implementation Plan (Hipercool AI)

> **NOTA IMPORTANTE:** Este arquivo consolida e substitui todos os guias de backend anteriores (backend_onboarding_prompt, backend_implementation_plan 1 e 2, e backend_features_blueprint).

> ⚠️ **CORREÇÃO DE STACK (2026-07-20).** Este documento menciona "Node.js/TypeScript"
> em vários pontos — está DESATUALIZADO. O backend real do Hermes Call é **Go**
> (single-binary, `cmd/server`), com **pgvector** para RAG. **Decisão firme da dona:
> NÃO usar GraphRAG/Python/Node no backend.** Onde ler "Node/TS", entenda "Go".
> Priorização: uma feature grande de cada vez, por ROI da campanha, com validação ao vivo.

> ✅ **JÁ IMPLEMENTADO (builds 0113→0200 + lote 2026-07-20):** veja a auditoria honesta
> na **seção 7**. Além do que está lá, neste lote foram ligados ao backend REAL:
> - **Banner de falha de credenciais** (seção 1): já NÃO é mais falso — `App.tsx` consulta
>   `GET /api/settings/ai/credentials` e só mostra quando há chave com status≠active/falhas.
> - **Sandbox "Guerra de Bots" / Juiz Semântico** (seção 8): era `setTimeout` fake; agora
>   `POST /api/agents/{id}/wargame` (IA atacante gera objeções + agente responde de verdade)
>   e `POST /api/agents/{id}/evaluate` (LLM-as-a-judge real). Ver `agent_wargame.go`.
> - **Central de Conhecimento (RAG)**: `GlobalRagManager` era mock; a base por funcionário
>   agora lista/sobe/deleta documentos REAIS via `/api/rag/documents` (chunk+embed+pgvector).
> - **Anti-loop bot-vs-bot** (seção 4 do plano parte 1): `loopguard.go` detecta ping-pong
>   rápido/eco entre automações e pausa a auto-resposta do contato por cooldown.

---

# Instruções para o Desenvolvedor Backend (Integração do Wizard "Configura Fácil")

## Contexto do Frontend
Acabamos de finalizar o frontend do `EasySettingsWizard`, um fluxo de onboarding de 9 etapas desenhado para ser "à prova de burrice". Ele capta desde as chaves de API das IAs (Groq, ElevenLabs, OpenAI) até a criação de grupos de WhatsApp, cadastro de equipe, identidade visual e regras semânticas de CRM. 

Sua missão é construir a infraestrutura do Backend (Node.js/TypeScript) para receber, processar e aplicar essas configurações de forma segura na arquitetura multitenant (Workspace) do sistema.

---

## 1. Endpoints Necessários

### A. Validação em Tempo Real (Opcional, mas recomendado)
O front faz verificações mockadas, mas o ideal é que você crie rotas de validação real:
- `POST /api/validate/llm`: Recebe a provider (groq/openai) e a key. Faça uma requisição de teste leve (ex: "diga oi") para validar saldo e autenticação.
- `POST /api/validate/telegram`: Recebe o `botToken` e bate na API `https://api.telegram.org/bot<token>/getMe` para retornar os dados do bot.

### B. Endpoint de Finalização do Wizard
- `POST /api/settings/easy-wizard-finish`
- **Descrição**: Este é o endpoint principal. Ele receberá um grande payload JSON com todo o estado final do Wizard. Você precisa fatiar esse JSON e distribuir as configurações nas respectivas tabelas do banco de dados (Workspace, Users, AI_Settings, Integrations).

---

## 2. Estrutura do Payload Esperado
O frontend enviará um objeto semelhante a este:

```json
{
  "workspaceName": "Acme Corp",
  "brandColor": "#10b981",
  "credentials": {
    "groq": "gsk_...",
    "elevenlabs": "sk_..."
  },
  "textModel": "groq",
  "sttModel": "gratis",
  "ttsModel": "elevenlabs",
  "ttsAmbient": true,
  "ttsAmbientType": "office",
  "chatChannel": "whatsapp_group", // ou "telegram_bot", "whatsapp_pv"
  "botToken": "", 
  "chatId": "",
  "wppGroupName": "Equipe de Vendas VIP",
  "teamMembers": [
    { "email": "joao@empresa.com", "pass": "senha123" }
  ],
  "crmSetup": { "defaultFunnel": true, "basicTags": true },
  "customTags": [
    { "text": "Lead Frio" }, { "text": "Cliente Vip" }
  ],
  "alerts": { "sales": true, "errors": true, "lost": false, "summary": true, "newLead": false },
  "customAlerts": [
    { "text": "Avisar se o cliente falar a palavra PROCESSO" }
  ]
}
```

---

## 3. Lógicas e Funções Específicas a serem implementadas

Você precisará criar Services/Controllers específicos para lidar com cada parte desse payload:

### A. Serviço de Gerenciamento de Identidade (Workspace & Equipe)
1. Atualize a tabela `Workspaces` com o `workspaceName` e `brandColor`.
2. Para o array `teamMembers`: Você precisa rodar um loop que aplique *Hash (Bcrypt)* na senha temporária que veio do front, crie o usuário na tabela `Users` (amarrado ao WorkspaceId correto) com role de "Colaborador/Vendedor".
   - *Atenção*: Certifique-se de ignorar ou tratar erros de e-mails duplicados.

### B. Serviço de Armazenamento de Chaves de IA
As chaves que vierem em `credentials` devem ser salvas de forma **Criptografada** no banco de dados (usando AES-256 ou similar). Nunca salve a API Key do Groq ou ElevenLabs em texto plano.

### C. Sistema de "Ambientação" de Voz (ttsAmbient)
O backend de áudio/telefonia (o microserviço que cuida da chamada SIP/WebRTC) precisa ler os campos `ttsAmbient` e `ttsAmbientType`.
- **Implementação**: Se `ttsAmbient` for `true`, durante a chamada, sua engine de áudio deve tocar um arquivo MP3 de ruído de fundo (ex: som de escritório) mixado em volume baixo (~15%) junto com o buffer de áudio que retorna da ElevenLabs/TTS.

### D. Serviço de Provisionamento de Chat (Telegram/WhatsApp)
Se `chatChannel` for...
- **`telegram_bot`**: Salve o Token e o ChatID. Registre o webhook do Telegram nesse bot apontando para o nosso servidor.
- **`whatsapp_group`**: Salve o `wppGroupName` como um estado "pendente". Quando a API de WhatsApp (Baileys/EvolutionAPI) for conectada pela leitura do QRCode, você deve rodar um worker que dispara a criação de um grupo no WhatsApp com esse nome, adiciona o número do dono da empresa e define o grupo como o canal principal de envios de logs.

### E. Injeção de Contexto (Tags e Alertas) no LLM
Essa é a parte mais inteligente.
- Salve `customTags` e `customAlerts` no banco.
- **No momento da ligação**: O System Prompt (instrução base) do agente Groq/OpenAI precisa ser montado dinamicamente no backend. 
  - Você deve concatenar as tags no prompt: *"Ao final da ligação, classifique o lead usando UMA destas tags: [array de customTags]"*.
  - Você deve concatenar os alertas: *"Sua regra de notificação: [array de customAlerts]. Se algo na conversa acionar essa regra, dispare o comando tool_alert(mensagem)."*

---

## 4. O que o Frontend espera de retorno
Após o POST no `/api/settings/easy-wizard-finish`, retorne um status 200 se tudo for provisionado. Caso alguma criação falhe (ex: erro ao criar um dos usuários da equipe), faça um *Graceful Degradation* (salve o resto e avise no JSON de resposta o que falhou) em vez de dar Rollback em tudo.


---

# Plano de Implementação Backend - Ecossistema de IA Enterprise

Este documento centraliza todas as regras de negócio e integrações necessárias para suportar as interfaces de alto nível criadas no front-end. O "Agente Backend" deverá utilizar este guia para modelar o banco de dados e expor as rotas corretas.

## 1. Segurança Operacional: Handoff e Intervenção Humana
**Onde no Front-end:** `SpecializedAgents.tsx` e `EasyAgentWizard.tsx`.
**Objetivo:** Permitir que uma IA transfira a conversa para um atendente humano quando não conseguir resolver ou quando palavras-chave forem acionadas.

### Novas Colunas/Atributos no Banco de Dados (`agent_profiles`):
- `escalation_keywords` (string/array): Gatilhos em texto que forçam o transbordo (ex: "falar com humano", "cancelar", "procon").
- `handoff_method` (string): Enum para o método de transbordo: `panel` (Apenas painel), `sip_transfer` (Transferência PABX para telefone), ou `swarm` (Encaminhar para outra IA especialista).
- `handoff_message` (string): A mensagem que a IA deve reproduzir (TTS) ou enviar em texto antes de pausar sua execução e chamar o humano (ex: "Um momento, vou chamar um especialista").
- `handoff_notify` (string): Enum/String para onde o aviso de transbordo deve ir: `whatsapp`, `telegram`, `panel`, `call_forward`.

### Lógica Necessária:
O motor de processamento LLM (OmniRoute/Proxy) precisa checar a intenção e comparar com `escalation_keywords`. Se bater, pausa a sessão da IA, emite `handoff_message` e aciona um Webhook para notificar a equipe conforme `handoff_notify`.

### Diferença de Pausa (Texto vs Voz)
- **Canais de Texto (WhatsApp/Chat):** A sessão (thread) é colocada no estado `paused`. O LLM cessa qualquer inferência para este cliente até que o status seja alterado por um admin (`resume_ai`).
- **Canais de Voz (Telefone/Meet):** A sessão **NÃO** entra em `paused`. O agente emite um alerta assíncrono para o dashboard/painel do humano, enquanto o LLM recebe uma injeção de prompt `mode: stall`. Ele é instruído a jogar conversa fora e tranquilizar o cliente (ex: "Só um instante, já estão te atendendo, enquanto isso, como está o tempo aí?") até que o administrador clique em "Interceptar Áudio", momento em que o LLM é silenciado e a stream de áudio do microfone do admin é conectada à stream do cliente.

### Dossiê Instantâneo (LLM Secundário)
- Imediatamente após o trigger de handoff, o backend envia a lista de mensagens (`chat_history`) para um LLM rápido e barato (Llama3-8b / GPT-4o-mini).
- O prompt solicita: *"Gere um resumo de 3 linhas focado na equipe de transbordo: 1. Qual o problema. 2. O que o cliente deseja. 3. O que a IA já tentou oferecer."*
- O resultado é salvo no banco de dados atrelado à sessão e exibido na interface do Atendente.

---

## 2. Monitoramento de Campanhas em Tempo Real (Analytics)
**Onde no Front-end:** `CampaignsPage.tsx`.
**Objetivo:** Visualizar as ligações massivas ativas, quantidade de agentes pendurados, falhas e conectividade.

### Rotas e WebSocket Necessários:
- O painel possui um botão "Monitoramento em Tempo Real". O Backend precisa fornecer um endpoint (preferencialmente WebSockets ou SSE) em `/api/campaigns/live` ou `/api/analytics/live` que entregue:
  - Total de conexões ativas.
  - Taxa de sucesso/atendimento vs secretária eletrônica.
  - Alocação de recursos da CPU/OmniRoute.

---

## 3. IA em Reuniões (Meeting Bot)
**Onde no Front-end:** `MeetingAIPage.tsx`.
**Objetivo:** O painel agora suporta o envio de agentes cadastrados para salas de Zoom/Meet, com diversas habilidades.

### Novos Atributos e Estados:
- **`meeting_context`** (string): Contexto temporário injetado no system prompt apenas durante a duração daquela sala. Não deve ser salvo definitivamente no `agent_profiles`.
- **Habilidades (Premium Skills):** A página envia flags booleanas para ativar funções especiais no bot da reunião. O backend precisa suportar:
  - `skillAvatar` (Avatar de Vídeo): Integração com HeyGen Streaming API.
  - `skillCRM` (CRM Auto-Update): Conexão entre as intenções extraídas pelo Whisper/LLM e o banco de dados de CRM para mover cards via chamada de função.
  - `skillTranslation` (Tradução Simultânea): Routing de áudio bidirecional e bypass do system prompt para focar na tradução.
  - `skillScreen` (Screen Parsing): Captura de frame da tela compartilhada no Meet e envio para modelos Vision (Gemini 1.5 Pro / GPT-4o).
  - `skillEmotion` (Análise de Sentimento): Análise do tom de voz do usuário via modelos como Hume AI ou prompt avançado de áudio.
  - `skillTimekeeper` (Guardião da Pauta): Prompt injetado com timer global informando a duração e tópicos pendentes.
  - `skillFollowUp` (Disparo Autônomo): Ferramenta (Function Call) que o LLM executa no final para disparar um POST no Mailgun/Resend enviando a Ata.

---

## 4. Alerta Global de Falha Crítica na API (OmniRoute / Credenciais)
**Onde no Front-end:** `App.tsx` (GlobalAIErrorBanner).
**Objetivo:** Avisar imediatamente se o saldo da OpenAI/Groq acabar.

### Lógica Necessária:
- O Gateway (Proxy/OmniRoute) deve interceptar erros `429 Too Many Requests`, `401 Unauthorized` ou `402 Payment Required` vindo dos LLMs.
- Atualizar a tabela de credenciais com `status = 'error'` e incrementar contador de falhas.
- Disparar um evento (WebSocket) para o front-end exibir o `GlobalAIErrorBanner` sobre a tela atual.

---

## 5. Swarm AI (Orquestração Multi-Agente)
**Onde no Front-end:** `MeetingAIPage.tsx` (Seleção Múltipla) e `SpecializedAgents.tsx`.
**Objetivo:** Permitir que dois ou mais agentes conversem entre si e com o cliente na mesma sessão de áudio/chat.
### Lógica Necessária:
- O Gateway (OmniRoute) deve instanciar múltiplos workers de LLM atrelados a um único canal de áudio (Mixer).
- Utilizar *Tool Calling* (transfer_to_agent) onde a IA atual decide passar a palavra para a outra (ex: Vendas invoca Suporte Técnico). O sistema de Roteamento (Router) faz o hot-swap do WebSocket ativo.

## 6. Modo Copiloto "Fantasma" (Real-Time Agent Assist)
**Onde no Front-end:** `TelephonyPage.tsx` e `ManagerChat.tsx`.
**Objetivo:** Quando o humano (Handoff) assume o controle, a IA se transforma em um assessor silencioso que escuta/lê a conversa e sugere respostas para o atendente.
### Lógica Necessária:
- Manter o canal do LLM aberto recebendo os *streams* de áudio do cliente E do humano, mas desativar o TTS (saída de voz) da IA.
- Expor via WebSocket (`/api/copilot/suggestions`) *cards* JSON com dicas geradas pela IA (ex: "Ofereça 10% de desconto").

## 7. RAG Auto-Evolutivo (Feedback Loop & Shadowing)
**Onde no Front-end:** `SpecializedAgents.tsx` (Aba RAG).
**Objetivo:** A IA atualiza sua própria base de conhecimento ao analisar reuniões/chats onde o humano obteve sucesso na conversão/resolução.
### Lógica Necessária:
- Escutar encerramentos de sessões (`session_ended`). Se o status for `sucesso`, o sistema (via um LLM secundário de sumarização) extrai a "Lição Aprendida" e as objeções superadas.
- Converter essa lição em *Embeddings* e injetar automaticamente no banco vetorial (Pinecone/Weaviate) associado ao agente.

## 8. Lógicas do "Funcionário Fácil" (EasyAgentWizard & FollowUp)
**Onde no Front-end:** `EasyAgentWizard.tsx` e `EasyFollowUpWizard.tsx`.
**Objetivo:** Instruções avançadas injetadas na criação do agente para comportamentos orgânicos e automações invisíveis.

### Comportamento e Prompting:
- **Waterfall de Desconto (maxDiscount):** O Agent Core deve embutir no System Prompt uma regra calculada instruindo a concessão gradual de desconto, apenas mediante detecção de intenção de desistência, até o teto de `maxDiscount`.
- **Hot Lead Tagger:** Habilitar uma *Function Calling* silenciada de uso livre chamada `tag_lead(status: 'hot')`. Se o agente detectar sinais fortes de compra, aciona a tool e o backend viaja pelo Webhook/Event Bus para alterar a cor do lead no CRM.
- **Dupla Personalidade (Turno Dia/Noite):** O backend (OmniRoute) deve interceptar o timezone do request. Se for entre 18h e 08h, ele injeta no prompt as regras contidas em `dualPersonaRules`, sobresscrevendo o tom diurno.
- **Simulador de Digitação:** Ao invés de *streaming* direto e imediato para canais de texto (WhatsApp), o backend calcula: `delay = length(response) * human_typing_speed`. Bloqueia o envio e sinaliza "Digitando..." via API oficial do WhatsApp antes do disparo.
- **RAG Reverso (Auditoria):** Injeção de "Vendas Perdidas". O LLM analisa o log, e o backend deve salvar o `guardrail` invertido extraído na tabela do agente.

### Gestor de Promessas e Accountability (ASYNC)
**Extremamente Crítico:** Esta rotina NUNCA deve ser acionada via *Tool Calling/Function Calling* ativa DURANTE o turno do cliente, pois causaria lentidão e quebra de fluxo conversacional.
1. Quando uma sessão de Chat/Chamada finaliza (`status = 'ended'`), o backend empilha a transcrição em uma fila secundária (SQS/Redis).
2. Um Worker assíncrono consome a fila e roda uma query LLM de baixo custo (ex: Llama3-8b / GPT-4o-mini).
3. Prompt de extração: *"Quais promessas o agente IA fez ao cliente e não resolveu na hora? Ex: Enviar boleto amanhã, retornar ligação."*
4. O resultado é populado na nova tabela `agent_promises` e exibido no frontend na aba **Gestão de Promessas**.

### Termômetro de Empatia (Sensory Empathy)
- **Lógica Prompt-Time:** O LLM principal avalia a gravidade do input do usuário (Sentiment Analysis).
- Se a intenção for detectada como `crise`, `raiva`, ou `perda_financeira`, o sistema força a variável `emoji_usage: false` e `tone: solene/urgente` e emite a resposta baseada nesse preset, abandonando o tom festivo padrão.

### Ponto Eletrônico / Escalonamento Silencioso (Human SOS)
**Onde no Front-end:** `HumanAssistTab.tsx` (Ponto Eletrônico).
**Objetivo:** Agente de IA "pesca" a resposta com o chefe sem desligar ou passar a chamada pro chefe, apenas ganhando tempo.
- Quando o LLM trava ou cai em "out_of_knowledge", ele invoca a tool secreta `ask_manager(question)`.
- O backend dispara um ping/mensagem via API (WhatsApp/Telegram) ou faz uma chamada rápida (via Twilio) para o Admin.
- Enquanto a resposta não chega (Webhook/Polling), o LLM entra em "Modo Enrolação" injetando *filler tokens* ("Só um minutinho que estou checando isso no sistema... enquanto isso, me diga, qual seu volume atual?").
- Assim que o Admin responde via texto, o backend resolve a `Promise` da tool original e o LLM cospe a resposta para o cliente.

## 9. Hipercool Labs (Funcionalidades em Incubação)
**Objetivo:** Arquiteturas altamente complexas e em fase de P&D (Pesquisa e Desenvolvimento) que serão integradas gradativamente ao motor principal.

### Gerador Automático de Checkout (Pagamento em 1-Clique no Chat)
- **Tool Calling Nativa:** O Agente de Inteligência Artificial receberá uma *Function Calling* atrelada aos gateways (Stripe / MercadoPago / Asaas).
- **Lógica de Trigger:** Quando o LLM identificar, com confiança > 95%, a intenção `ready_to_buy` E o produto desejado estiver mapeado no RAG/Catálogo, ele invoca `generate_payment_link(product_id, amount)`.
- **Callback:** O backend acessa a API do provedor financeiro, cria um link de pagamento (PIX ou Cartão) de uso único e devolve para o chat.
- **Webhook Secundário:** O backend fica escutando o Webhook do Stripe/MercadoPago. Quando o status mudar para `paid`, o backend manda uma mensagem ativa via WhatsApp (System -> User) agradecendo a compra e liberando o acesso, sem intervenção humana.
---

## 4. Atualizações do Funcionário Fácil (EasyAgentWizard)
**Onde no Front-end:** EasyAgentWizard.tsx.
**Objetivo:** Adicionar maior nível de humanização, flexibilidade de chamadas de API nativas e regras avançadas de RAG/Vendas.

### Novos Atributos e Estados:
- **ehavior.humanTyping e 	ypingSpeedMs (number):** Controle de delay de resposta no WhatsApp. O backend deve calcular 	ypingSpeedMs * promptResponseLength e injetar um delay (com a flag 	yping_indicator) antes de enviar a mensagem final.
- **ehavior.splitMessages (boolean):** Se 	rue, o LLM proxy ou o backend interceptador deve dar um split na resposta toda vez que encontrar dupla quebra de linha (\n\n), enviando como mensagens separadas.
- **ehavior.audioCondition (enum):** Define quando o TTS (Text-To-Speech) via WhatsApp será invocado. Opções: 
ever, lways, when_audio (só responde com áudio se o inbound_type for áudio), e long_text (se a resposta for maior que 500 caracteres).
- **
ag.maxLength (number):** Injeta nativamente no System Prompt uma restrição estrita: "Não responda com mais de X caracteres".
- **
ag.dataToCollect (string):** Injeta uma instrução de foco: "Antes de finalizar a tarefa, você PRECISA coletar os seguintes dados: [dataToCollect].".
- **utomations.waitForResponse (boolean):** Se 	rue e a ctionType for Webhook/API, o backend deve pausar o event loop de resposta do LLM e disparar um fetch bloqueante. A resposta recebida da API externa será parseada via string e adicionada ao System Prompt ("SYSTEM_UPDATE: A API retornou: [dados]"), e só então a IA finaliza o streaming pro usuário.
- **utomations.actionType (enum):** Adicionados webhook_fixed (passa o payload literal como POST) e pi_query (chama a URL, lê a resposta e fornece junto a instruction).
- **handoff.adminNumber e skForHelp:** Permite transbordo para notificar ativamente o adminNumber configurado e autoriza a IA a disparar handoff preventivo se não souber resolver o problema.

### Proteção Contra Loops Infinitos (Bot vs Bot) e Limites de Tentativas
**Onde no Backend:** Camada de interceptação OmniRoute / Gerenciador de Estado do Canal (WhatsApp/Voice).
**Objetivo:** Impedir que o nosso agente entre em um "loop infinito" ao conversar com um robô de autoatendimento ou outro bot, torrando os créditos da API.
**Lógica Necessária:**
1. **Rate Limiting de Interações:** Se houver uma troca de mensagens extremamente rápida (ex: 5 mensagens trocadas em menos de 10 segundos) sem o delay natural de digitação humana, o sistema entra em lockdown.
2. **Fingerprinting de Bot:** Se a mensagem recebida contiver padrões clássicos de bot (ex: "Digite 1 para...", "Desculpe, não entendi", "Protocolo de atendimento", ou mensagens enviadas instantaneamente após o read-receipt), o OmniRoute deve pausar a sessão (status: paused_suspected_bot) e sinalizar o administrador.
3. **Limite de Interações Sem Resolução:** Se a conversa passar de X turnos (ex: 20 interações) e a intenção não caminhar para fechamento, coleta de dados ou handoff humano, disparar um aviso de atigue no painel. O LLM não deve interagir infinitamente sem avanço de funil.

### Auto-Treinamento e RAG de Casos de Sucesso (Self-Reflecting Memory)
**Onde no Backend:** Pós-processamento de sessão (Post-Chat Pipeline)
**Objetivo:** Permitir que a IA aprenda com os próprios acertos e crie um RAG dinâmico de melhores práticas sem intervenção humana.
**Lógica Necessária:**
1. **Trigger de Sucesso:** Quando a variável KPI_Achieved (ex: venda fechada, reunião agendada) for ativada na sessão.
2. **Extração de Insight (Sub-LLM):** O backend dispara uma job assíncrona para um modelo menor (ex: Llama3/GPT-4o-mini). O prompt será: *"Analise a transcrição desta venda bem-sucedida. Qual foi a objeção do cliente e qual argumento exato a IA usou para convencê-lo? Resuma em um parágrafo."*
3. **Injeção no RAG Global:** O insight extraído é vetorizado e salvo no banco de dados vetorial daquele agente sob a tag golden_arguments.
4. **Retroalimentação:** Em conversas futuras, se um novo cliente apresentar a mesma objeção, o RAG trará esse argumento vitorioso como contexto prioritário para a IA usar.


---

# Plano de Implementação Backend - Parte 2 (Gestor e Hub CRM)

Este documento complementa o plano original, detalhando a arquitetura backend necessária para suportar as novas estruturas e componentes aninhados no painel frontend, focando especificamente no "Agente Gestor", nas regras de CRM avançado e no treinamento de RAG isolado. O "Agente Backend" deve utilizar este guia para preparar o banco de dados e as novas lógicas de permissão.

---

## 1. O Funcionário Gestor (Manager Agent)
**Onde no Front-end:** `ManagerChat.tsx` (Sidebar e Modal Interativo).
**Objetivo:** Criar um Super-Agente que serve de "Cérebro Secundário" para o dono da empresa. Ele possui autonomia para ler métricas, auditar outros agentes, e executar comandos diretos no sistema via NLP (Natural Language Processing).

### Novas Lógicas Necessárias no Backend:
- **Scope Level:** O `agent_profile` precisa de uma flag `is_manager: boolean` ou `role: 'manager'`. Agentes com essa role têm acesso irrestrito (bypass) a todo o banco de dados do tenant, mas NÃO falam diretamente com os leads/clientes. O Gestor fala apenas com o Dono (via painel, WhatsApp do dono ou áudio interno).
- **RAG de Telemetria:** Diferente do RAG convencional (que lê PDFs de vendas), o RAG do Gestor consome **Logs do Sistema** em tempo real. O backend deve plugar os endpoints de `/api/analytics` e `/api/logs` no contexto desse LLM.
- **Tools/Function Calling Obrigatórias:**
  - `audit_agent(agent_id)`: Lê as últimas 50 conversas de um funcionário IA específico e avalia sua performance.
  - `pause_agent(agent_id)`: Desativa emergencialmente um agente que esteja alucinando.
  - `generate_report(date_range)`: Agrega dados de vendas e custos e devolve em formato Markdown para o painel.
- **Persistence (Memória de Longo Prazo):** A thread do Gestor (`manager_thread_id`) deve ser perpétua. Ele deve lembrar do que o dono pediu ontem. O banco precisa suportar `long_term_memory` (memória sumarizada periódica usando Llama3).

---

## 2. Hub de CRM: Follow-Up Fácil & Gestor de Promessas
**Onde no Front-end:** `CRMPage.tsx` (Abas `followup` e `promises`).
**Objetivo:** Consolidar todas as rotinas que dependem da jornada do lead dentro de um único ecossistema central, saindo do menu global e operando atreladas aos contatos.

### Follow-Up Fácil (Réguas de Cadência)
- **Engine Assíncrono (Cron/Workers):** O backend precisa de um orquestrador de fila (como Celery, BullMQ ou SQS). 
- **Entidades (`follow_up_sequences`, `follow_up_steps`, `follow_up_jobs`):**
  - Quando um gatilho é disparado (ex: mudança de status no Kanban via `move_lead()`), o backend consulta `follow_up_sequences` buscando `trigger_value == new_status`.
  - Se bater, ele agenda uma entrada na tabela `follow_up_jobs` para cada `step` da régua, respeitando a variável `delay_hours`.
  - **Cancelamento Automático:** Se a configuração `stop_on_reply` estiver `true`, qualquer payload de recebimento no Webhook do WhatsApp do lead em questão deverá cancelar/deletar todos os `follow_up_jobs` pendentes para aquele `jid`.

### Gestor de Promessas (Accountability Board)
- **Extração Semântica (Pós-venda):** Ao encerrar uma interação (`session_ended`), uma IA secundária e leve analisa a transcrição buscando "promessas" usando Few-Shot Prompting.
- **Entidade `agent_promises`:**
  - `id`, `lead_id`, `agent_id`, `promise_description`, `deadline_at`, `status` (pending, fulfilled, overdue), `trust_score_impact`.
- **Feedback Loop com o Gestor:** O "Funcionário Gestor" varre a tabela `agent_promises` a cada hora. Promessas em atraso reduzem o *Trust Score* do agente de vendas que a fez, e geram um alerta silencioso no painel do administrador.

---

## 3. Treinamento RAG Aninhado (Funcionários IA)
**Onde no Front-end:** `SpecializedAgentsPage.tsx` (E abas internas de Configuração).
**Objetivo:** O RAG deixou de ser global e passou a ser modular (KnowledgeManagerTab). Cada agente pode herdar o RAG global da empresa, mas também possui sua própria base vetorial focada.

### Arquitetura do Vector Database (Pinecone/Weaviate/Qdrant):
- **Namespaces Dinâmicos:** O backend deve separar a memória por tenant E por agente. 
  - `namespace = tenant_{id}_global` (Conhecimentos da empresa que todos os agentes sabem).
  - `namespace = tenant_{id}_agent_{id}` (Manuais específicos de suporte ou scripts agressivos de venda).
- **RAG Reverso (Correção do Dono):** No painel, o dono pode clicar em uma conversa em que o agente errou e fornecer a "Resposta Certa". 
  - O backend captura esse feedback e injeta no vetor de `tenant_{id}_agent_{id}` com peso altíssimo (`top_k` priority match), forçando a IA a não repetir o erro.

---

## 4. Otimizações de Banco e Payload
Para evitar o erro persistente de tela branca e delays na montagem da tela pelo React:
- Os endpoints consolidados (como o `CRMPage`) devem retornar payloads rasos (Shallow payloads). Exemplo: Retornar a lista de `promises` e `follow_ups` apenas nas suas respectivas sub-rotas (`/api/crm/promises`, `/api/crm/followups`), não pendurando TUDO na consulta inicial do Funil.
- O Frontend passará a usar *Polling* ou *WebSocket* apenas nas abas ativas para preservar conexão.

## Próximos Passos para a Engenharia de Backend
1. **Migrations:** Criar tabelas `agent_promises`, `follow_up_sequences` e adicionar `is_manager` em `agent_profiles`.
2. **Filas:** Subir um worker dedicado (Background Task) exclusivo para (a) disparar cadências de Follow-Up e (b) extrair as promessas do chat_history.
3. **Roteamento LLM:** Isolar a thread do *Funcionário Gestor*, pois ela nunca encerra (`infinite_session`) e precisa de sumarização periódica para evitar estourar o limite de tokens do LLM (Context Window Exhaustion).

## 5. Integrações Específicas do Front-End (EasyAgentWizard & Follow-Up Avançado)
**Onde no Front-end:** `EasyAgentWizard.tsx` (Configurações Avançadas) e `FollowUpPage.tsx`.
**Objetivo:** Garantir que o backend absorva fielmente as chaves específicas que foram criadas no frontend durante a sessão de auditoria.

### Lógicas Adicionais Obrigatórias:
- **`audio_condition`**: Regra de processamento para TTS. O backend deve checar essa variável antes de gerar o áudio de saída da IA (`never`, `always`, `when_audio`, `long_text`).
- **`max_discount`**: O *Agent Core* deve embutir no System Prompt uma regra limitando descontos dinâmicos.
- **`splitMessages`**: Quando `true`, o LLM proxy ou o backend deve dar um split na resposta quando encontrar quebras de linha enviando no WhatsApp como balões de mensagem separados.
- **`handoff.askForHelp`**: Permite que a IA ative a *tool* de transbordo espontaneamente se o nível de confiança (Confidence Score) for muito baixo, chamando o Admin antes do cliente ficar irritado.
- **Voz no Follow-Up**: O backend do Follow-up Fácil precisa suportar o canal `voice` (Ligação VoIP) e não apenas WhatsApp, permitindo que a IA disque pro ativamente com um prompt de "oferecer X% de desconto" injetado pelo *Step* da cadência.
- **`whatsapp_audio` no Follow-Up**: Suporte para o canal "WhatsApp Áudio", onde o LLM converte a intenção da régua para voz usando TTS e envia para o lead como se fosse um áudio gravado na hora.

## 6. Módulos Avançados de Inteligência (Deep Tech)
**Objetivo:** Arquiteturas de ponta para orquestração autônoma e insights preditivos.

### 6.1 Multi-Agent Swarm (Conselho Jedi de IAs)
- **Arquitetura Backend:** Ao invés de um único worker LLM responder a requisição do usuário, o OmniRoute deve ser capaz de instanciar uma 'Thread Interna'.
- **Execução:** O agente principal (Frontend Chat) aciona a tool `consult_team(problem_description, target_agents)`. O backend paralela requests para os agentes secundários através de uma Queue/PubSub. Quando todos responderem na thread invisível, um modelo sumarizador (Llama3) consolida o consenso e devolve para o agente principal formular a resposta final pro cliente.

### 6.2 Clustering de Memória (Insights Não-Solicitados)
- **Arquitetura Backend:** Um cron job semanal (ex: Sábado 02:00 AM) que aciona um pipeline de extração e clusterização.
- **Execução:** O Worker extrai todas as sessões marcadas como 'perdidas' no banco de dados. Usa um modelo de embedding para clusterizar queixas recorrentes (K-Means). Pega os maiores clusters e envia para o LLM gerar um Insight Estratégico, injetando ativamente na thread do Gestor.

### 6.3 Sandboxing de Código Autônomo (Code Interpreter)
- **Arquitetura Backend:** O Agente Gestor ganha acesso a uma ferramenta `execute_python_script(code)`.
- **Execução:** O backend deve possuir um ambiente dockerizado leve. Quando o Gestor precisa de cálculos complexos em tabelas gigantes, ele gera o código, o backend roda no sandbox isolado e retorna o console para o LLM.

## 7. Integração Oficial Meta (Instagram e Facebook)
**Objetivo:** Permitir que os Agentes de Vendas e o Gestor atuem nas redes sociais (Directs, Messenger e Comentários).

### 7.1. Arquitetura de Conectividade (Graph API)
- **Tokens e Autenticação:** A tabela `tenant_credentials` recebe `meta_access_token`, `meta_app_id`, `meta_app_secret`, `instagram_account_id` e `facebook_page_id`.
- **Webhook Centralizado:** Endpoint `/api/webhooks/meta` cadastrado na Meta. Deve validar o `hub.challenge` e assinar requests com SHA256 (App Secret).

### 7.2 Roteamento de Mensagens (Direct & Messenger)
- **Inbound:** Recebe o evento `messages`. Busca sessão baseada no `sender.id`. Se for novo lead, cria no CRM e invoca a fila do LLM.
- **Regra das 24 Horas:** A Meta exige respostas em até 24h. O backend injeta a flag `window_expired: true` se passar do tempo para evitar bloqueio da conta.

### 7.3 Interação com Comentários (Comments API)
- **Inbound:** Evento `comments` aciona o Agente de Vendas.
- **Ação:** Responde publicamente `POST /{comment_id}/replies` e chama no privado enviando os detalhes usando `POST /me/messages`.

### 7.4 Monitoramento do Gestor (Social Listening)
- **Gestão:** Tool `analyze_social_engagement()`. Consulta Graph API e traz métricas de curtidas/comentários dos últimos posts diretamente pro WhatsApp/Painel do Dono.

### 7.5 Agente Criador de Conteúdo (Auto-Publicação)
- **Objetivo:** O Agente Gestor decide proativamente quando criar e postar conteúdo no feed do Instagram/Facebook.
- **Mecânica Backend:** Um `CRON job` aciona a Tool `plan_content()`. O Gestor analisa o estoque ou blog, gera um prompt de imagem, chama a API do DALL-E 3 ou Midjourney para gerar a mídia.
- **Publicação:** O backend recebe a imagem, faz o upload para um bucket (S3), e utiliza o endpoint `POST /{ig-user-id}/media` com a `image_url` e a `caption` gerada pelo LLM. Após receber o `creation_id`, chama o endpoint `POST /{ig-user-id}/media_publish` para efetivar a postagem sem intervenção humana.

## 8. Arquitetura de Agente Pessoal & OS Control (Inspirado em MemGPT / OpenClaw)
**Objetivo:** Elevar o Agente Gestor de um mero chatbot para um orquestrador de sistemas com memória infinita e acesso à infraestrutura.

### 8.1 Sistema Operacional de Agente (OS Control & Local Execution)
- **Arquitetura Backend:** O Agente Gestor ganha acesso a uma Tool especial `execute_bash_command(command)` rodando em um ambiente isolado (ex: gVisor, Firecracker ou container Docker seguro).
- **Execução:** Quando solicitado, o Agente pode fazer dumps de banco de dados, acessar logs, rodar scripts Python e interagir com o sistema de arquivos. O output do bash (stdout/stderr) é devolvido para o LLM interpretar. O ambiente precisa ter limite rígido de timeout (ex: 60s) e restrições de rede para segurança.

### 8.2 Memória Perpétua Auto-Mutável (Arquitetura MemGPT)
- **Arquitetura Backend:** Implementar um mecanismo de 'Memória Hierárquica'. O prompt do Gestor é dividido em blocos estáticos e dinâmicos (`core_memory`, `archival_memory`).
- **Execução:** O Gestor possui Tools de Autoedição: `core_memory_append()`, `core_memory_replace()`. Conforme interage, o próprio LLM decide atualizar seu prompt base (ex: inserindo "O dono prefere tabelas Markdown") permanentemente no banco (tabela `agent_memory`), reescrevendo sua própria personalidade ao longo do tempo.

### 8.3 Orquestração Hierárquica Assíncrona (Task Delegation)
- **Arquitetura Backend:** Sistema de Jobs assíncronos de longa duração (usando BullMQ ou temporal.io).
- **Execução:** O Gestor pode usar a Tool `delegate_task(task_description, sub_agent_id)`. Se o Gestor recebe uma meta grande, ele quebra em sub-tarefas, distribui para agentes especialistas (Vendas, Suporte) através de filas, e fica em "modo suspenso" aguardando os webhooks de retorno. Quando todos finalizam, o Gestor acorda, sintetiza o resultado e envia para o Dono.

### 8.4 Pesquisador Profundo Autônomo (Deep Research Agent)
- **Arquitetura Backend:** Worker integrado a um Headless Browser (Puppeteer/Playwright) de longa duração.
- **Execução:** O Gestor inicia um job de pesquisa (`start_deep_research(query)`). O Worker em background varre dezenas de páginas da web iterativamente, extrai dados (Scraping + LLM Vision), resolve problemas sozinho e, horas depois, insere um Dossiê estruturado na thread do usuário, acionando notificação via Socket/Telegram.

---

# Backend Blueprint - Inteligência Artificial & Ferramentas Avançadas

Este documento centraliza as regras de negócio, estruturas de dados e arquitetura necessárias no **Backend (Node.js/Go)** para sustentar as novas funcionalidades implementadas no Frontend. Ele deve ser atualizado sempre que uma nova funcionalidade for adicionada ao sistema.

## 1. Monitoramento de Credenciais IA (Live Failures)
- **Funcionalidade:** O painel exibe alertas vermelhos no `AppShell` e no cofre de credenciais caso as chaves da OpenAI, Groq, etc., comecem a dar erro (401/429).
- **Integração:** O backend deve interceptar falhas HTTP no consumo das APIs LLM e incrementar a coluna `failsThisWeek`. Se o número de falhas consecutivas passar de X, a flag `status` da credencial muda para `"error"`.
- **Referência O.S.:** Inspirado na resiliência do *LiteLLM* e *Portkey*.

> ⚠️ **BUG ABERTO (frontend) — banner de falha é FALSO. 2026-07-18.**
> Em `client/src/App.tsx` (~linhas 45-51) o banner "Atenção Crítica: Falha em
> Credenciais de IA" é disparado por um `setTimeout(() => setHasError(true), 2500)`
> hardcoded — código de demonstração ("Aparece após 2.5s para demonstrar"). Ele
> NUNCA consulta a API, então aparece SEMPRE, mesmo com tudo saudável.
> **Backend está OK e pronto:** `GET /api/settings/ai/credentials` já devolve, por
> credencial, `status` e `failsThisWeek`. Testado 2026-07-18: 26 chaves, todas
> `status:"active"`, `failsThisWeek:0` → o banner NÃO deveria aparecer.
> **Fix no front:** buscar esse endpoint e só mostrar o banner se houver alguma
> credencial com `status !== "active"` OU `failsThisWeek > 0`; e exibir a SOMA de
> `failsThisWeek` no texto (ex: "3 falhas esta semana"), como a dona pediu.

## 2. Filtros Dinâmicos de Datas
- **Funcionalidade:** Dashboard, Custos e CRM agora aceitam `1d` (24 horas) e `all` (Tudo).
- **Integração:** As rotas REST de estatísticas devem parsear a query `?range=1d` e `?range=all`, removendo ou ajustando a cláusula `WHERE created_at > ...` no banco de dados.

## 3. Roteamento Multi-Agente (Swarm)
- **Funcionalidade:** Capacidade da IA de transferir a ligação para um "Closer" (IA especialista técnica) durante o atendimento.
- **Integração:** O backend SIP/Voice (ex: FreeSWITCH/Asterisk + WebSocket) deve suportar a invocação da tool `transfer_to_agent("closer")`. O backend altera o `system_prompt` na mosca sem derrubar a chamada RTP.
- **Referência O.S.:** Baseado na arquitetura do repositório *OpenAI Swarm* e *Vapi.ai*.

> ⚠️ **BUG ABERTO (frontend) — wizard Funcionários IA quebra a tela ao finalizar. 2026-07-19.**
> Em `client/src/components/settings/EasyAgentWizard.tsx` (~linha 344), após o deploy
> do agente / criação de credencial o código faz `setTimeout(() => window.location.reload(), 1500)`.
> Esse `window.location.reload()` recarrega a página inteira no meio do fluxo — o React
> re-monta do zero e a tela volta num estado quebrado (inputs SEM os rótulos "Nome do
> Agente", "Papel Principal", "Provedor/Modelo Secundário"; URL cai em `?action=login`).
> A dona reportou: "quando está criando credencial ele apaga a tela e quando volta fica assim".
> **Fix no front:** NÃO recarregar a página. Após sucesso, atualizar o estado localmente —
> re-fetch das credenciais (`apiGet('/api/credentials')` → `setCredentials`) e/ou navegar
> para a lista de agentes via o store de navegação (`useNavigation`), sem `location.reload()`.
> Backend não tem nada a fazer aqui (as rotas `/api/credentials` e `/api/agents` já funcionam).

## 4. IA em Reuniões (Google Meet Bot)
- **Funcionalidade:** O usuário pode colar a URL de um Google Meet. O backend envia um bot "headless" para entrar na sala. A IA ouve e, se chamada pelo nome, abre o microfone e fala.
- **Novas Opções Mapeadas no Frontend:**
  - `wakeWord` (ex: "Athena"): A palavra-chave que desmuta a IA.
  - `listenMode`: "continuous" (escuta toda a call), "chunks_15" (grava de 15 em 15 min), "wake_only".
  - `postAction`: "email_summary", "crm_log", "webhook" (Ação automática ao sair da call).
  - `autoMute`: IA já entra com microfone/câmera desativados por padrão.
- **Integração:** 
  - Usar *Puppeteer* ou *Playwright* rodando em um contêiner Docker rodando xvfb (Headless Chrome com virtual audio cables).
  - O bot captura o áudio da aba, envia para Whisper STT. Se o texto contiver o nome da IA, ativa o módulo LLM + TTS, joga o áudio virtual de volta pro Chrome.
- **Referência O.S.:** *Recall.ai*, *Meet Summary Bot* (Puppeteer WebRTC injection).

## 5. Live Call Handoff e Barge-In (Intervenção Humana)
- **Funcionalidade:** O humano pode assumir uma ligação em andamento ou a IA pode parar de falar instantaneamente se ouvir ruído do cliente.
- **Configuração no Frontend:** A tela de Configurações de Voz agora envia `barge_in_enabled` (boolean) e `barge_in_sensitivity` ("high", "medium", "low").
- **Integração:** O VoiceEngine (FreeSWITCH/Asterisk) precisa rodar VAD contínuo (Voice Activity Detection). Se o limiar de DB for batido no microfone do cliente durante o TTS da IA (e o barge_in estiver ativo), o stream RTP do TTS deve ser cortado (flush buffer).
- **Referência O.S.:** *Vocode* (Python/TS).

## 6. Base de Conhecimento Dinâmica (RAG)
- **Funcionalidade:** Upload de PDFs/URLs no painel para treinar o agente de voz.
- **Integração:** Backend processa o documento usando *LangChain* (document split, embeddings da OpenAI/BGE) e guarda em um *Vector DB* (Qdrant, Pinecone ou pgvector). O LLM faz query RAG antes de falar.
- **Referência O.S.:** *Flowise*, *AnythingLLM*.

> ✅ **STATUS 2026-07-19 (madrugada):** RAG-na-voz IMPLEMENTADO e no ar.
> - pgvector instalado no Postgres de produção; tabelas `rag_documents`/`rag_chunks` criadas.
> - `ragContextForUser` injeta os trechos relevantes no prompt ANTES da fala (gated:
>   no-op se o usuário não tem docs — zero risco/latência pra campanha).
> - Embeddings: `resolveEmbedKey` usa OpenAI se houver; SENÃO cai pra a chave **Gemini
>   da ligação** (`call_ai`) via endpoint OpenAI-compat, modelo `gemini-embedding-001`,
>   dimensions=1536 (casa com pgvector). Testado: Gemini gera 1536-d OK.
> - **Pra usar:** subir documentos em /api/rag/documents?agent_id=... (aba Treinamento/RAG).

## 7. Status geral dos planos de implementação (backend_implementation_plan.md e _2.md)
> Auditoria 2026-07-19. Os dois planos são uma VISÃO DE PRODUTO ampla (roadmap), não
> uma lista curta de pendências. Estado real por item:
>
> **FEITO / no ar:**
> - Swarm / `transfer_to_agent` (troca perfil na ligação ao vivo, sem derrubar RTP).
> - Handoff por escalation_keywords + handoff_message/method/notify (colunas no agent_profiles).
> - RAG (upload, busca, injeção na conversa) — ver seção 6.
> - Barge-in + filler + som ambiente contínuo + voz PT (language_code).
> - Filtros de data 1d/7d/30d/all (rangeSince).
> - Agente Gestor (manager) com tools de sistema; captação de leads (lead_capture.py, OSM keyless).
> - Meet Bot (cérebro + worker; falta só mic virtual no host).
>
> **FALTA (features grandes, cada uma = dias/semanas + infra nova; NENHUMA bloqueia a campanha):**
> - Handoff SIP/PABX real (transferência telefônica) — hoje é painel/swarm.
> - WebSocket de campanha em tempo real (analytics live) — hoje é polling/REST.
> - Worker assíncrono de Promessas/Accountability (fila Redis/SQS + sub-LLM pós-sessão).
> - Auto-treinamento RAG de casos de sucesso (golden_arguments) — depende do worker acima.
> - Checkout 1-clique (Stripe/MercadoPago/Asaas function calling).
> - Anti-loop bot-vs-bot (rate limit + fingerprinting) — parcialmente coberto por limites atuais.
>   auto-post Instagram/Facebook, delegação hierárquica (BullMQ/temporal).
> Recomendação: priorizar por ROI da campanha, uma de cada vez, com validação ao vivo.

## 8. Sandbox de Testes LLM e Avaliação (AgentChatTest)
- **Funcionalidade:** Ambiente de simulação avançado no painel (`AgentChatTest`) que testa a IA do usuário contra clientes simulados, realiza testes de carga e avalia respostas via LLM-as-a-Judge.
- **Novos Endpoints e Lógicas Necessárias no Backend:**
  - **`POST /api/agents/{id}/simulate_persona`**: Um endpoint onde uma "IA Atacante" (ex: GPT-4) lê o RAG do cliente e gera automaticamente objeções complexas (Objeção de Preço, Ameaças PROCON, Comparação de Concorrentes). O backend precisa instanciar uma LLM independente para atuar como cliente.
  - **`POST /api/agents/{id}/evaluate_response`**: O Juiz Semântico. Após o agente gerar uma resposta, o backend avalia (em background ou síncrono no modo dev) se a guardrail foi violada e atribui um Score (0-10) baseado na empatia e aderência ao `system_prompt`.
  - **Guerra de Bots (Batch Testing):** O backend deve aceitar um payload de N personas e orçamento máximo, instanciar múltiplas conversas (IA Atacante vs IA Defensora) e retornar o log completo de sucessos e falhas de guardrails.
  - **Split Screen (A/B Test Backend):** O endpoint principal de inferência do painel deve aceitar um modo A/B, onde o mesmo histórico e a mesma query do usuário são enviados para DOIS provedores diferentes (ex: Groq/Llama3 vs OpenAI/GPT-4o) em paralelo. O backend retorna a `reply_A` e `reply_B` junto com métricas comparativas de latência e custo para serem renderizadas lado a lado no UI.
  - **Injeção Dinâmica de RAG no Contexto:** Em vez de apenas um JSON estático, o botão "Injetar Contexto" no painel deve bater num endpoint que vasculha o VectorDB (pgvector) baseado num termo (ex: "Políticas de Reembolso") e força a injeção desse snippet como se o cliente tivesse ativado o gatilho, permitindo testar se a IA usa a base corretamente.

## 9. Níveis de Roteamento (Routing Architecture)
**Objetivo:** Evitar conflitos de orquestração definindo que apenas UM nível de roteamento pode estar ativo por tenant/canal. O Backend deve impor essa trava de segurança.

- **Nível 1 (Lista):** Roteamento Básico (Direct Mapping).
  - O gestor escolhe 1 agente específico para atender texto, e 1 para atender voz.
  - Ou 1 agente para as 2 funções, ativando uma flag booleana de `single_agent_mode = true`.
- **Nível 2 (Kanban / Agentes por Etapa):** Roteamento Condicional.
  - O encaminhamento de mensagens ocorre via regras de lógica pré-estabelecidas no backend (if/else).
  - O agente que atende depende de: Etapa atual do atendimento no funil CRM, tags no Lead, ou qual lista o contato pertence (ex: lista de fornecedores bate no Agente de Compras; lista de devedores bate na IA de Cobrança).
- **Nível 3 (Hierarquia / Orquestrador IA):** Roteamento Multi-Agente (Swarm).
  - Nível de autonomia máxima. Não usa regras estáticas rígidas, mas sim condições inteligentes de IA.
  - A ligação ou chat inicia com um Agente "Triador" ou primário, e ocorre *hot-swap* (trocas instantâneas) via *Tool Calling* (`transfer_to_agent`) quando a IA julga necessário o envolvimento de um especialista (ex: Vendas chama o Suporte Técnico e a IA do suporte assume a sessão imediatamente).
  - **Contexto da Transferência (Memória):** O backend deve suportar `transfer_mode = 'full_memory'` (passa a thread inteira alterando apenas o System Prompt do novo agente) ou `transfer_mode = 'summary'` (envia apenas um resumo compacto da conversa pro novo agente para economizar tokens).
  - **Identidade da Transferência (Apresentação):** 
    - *Modo Explícito:* O agente atual avisa "Vou te transferir para o setor tal", e o novo agente inicia se apresentando.
    - *Modo Silencioso:* Ocorre a troca de IA no backend, mas o bot mantém o mesmo "Nome" para o cliente, alterando apenas a base de conhecimento/skill secretamente sem o cliente saber que foi transferido.

**Regra de Ouro Backend:** Para evitar loops bizarros ou múltiplos agentes tentando responder a mesma mensagem do Webhook, o Backend deve garantir que apenas um Nível (1, 2 ou 3) de Roteamento Geral seja o 'Source of Truth' para o workspace/canal em dado momento.
