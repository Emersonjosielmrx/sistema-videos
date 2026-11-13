# Blueprint de Implementação Backend: Orquestrador "Gestor Fácil" (Go)

Este documento descreve detalhadamente o contrato de dados, a arquitetura e as rotas necessárias para que o backend (desenvolvido em Go) suporte o novo Wizard de Criação do Gestor (`EasyManagerWizard.tsx`). O Gestor atua como o nó raiz (Triagem/Orquestrador) que intercepta as interações e roteia para os Agentes Especializados.

## 1. Estrutura de Dados (Modelo do Gestor)
O backend precisará atualizar o schema da tabela de agentes/perfis ou criar uma tabela específica `manager_profiles` com suporte aos seguintes campos (mapeamento JSON/Struct em Go):

```go
type ManagerProfile struct {
    ID                    string   `json:"id" gorm:"primaryKey"`
    
    // STEP 1: Identidade e Motor
    Name                  string   `json:"name"`
    SystemPrompt          string   `json:"systemPrompt"`
    CognitiveIndependence bool     `json:"cognitiveIndependence"` // Se true, não usa o budget/rate limit global
    Provider              string   `json:"provider"`              // "openai", "anthropic"
    FallbackProvider      string   `json:"fallbackProvider"`      // "groq", "gemini"
    ManagerApiKey         string   `json:"managerApiKey,omitempty"`
    
    // STEP 2: Comunicação & Canais
    WhatsappMode          string   `json:"whatsappMode"`          // "private" ou "group"
    WelcomeMessage        string   `json:"welcomeMessage"`
    NotifyTelegram        bool     `json:"notifyTelegram"`
    SelfChat              bool     `json:"selfChat"`
    AudioCondition        string   `json:"audioCondition"`        // "never", "text_and_audio", "always_audio"
    
    // STEP 3: Ferramentas (Tools)
    Tools                 []string `json:"tools" gorm:"type:jsonb"` // ex: ["web_search", "vision_analysis"]
    
    // STEP 4: Árvore de Roteamento (Flow)
    RoutingRules          []Rule   `json:"routingRules" gorm:"type:jsonb"`
    
    // STEP 5: Superpoderes & Auditoria
    HaltOverride          bool     `json:"haltOverride"`
    BillingAlerts         bool     `json:"billingAlerts"`
    ScheduledReports      bool     `json:"scheduledReports"`
    PromisesAccountability bool    `json:"promisesAccountability"`
    CriticalAlerts        bool     `json:"criticalAlerts"`
    HandoffAlerts         bool     `json:"handoffAlerts"`
    ShadowingMode         bool     `json:"shadowingMode"`
    
    // STEP 5: Deep Tech & Agent OS
    MemoryClustering      bool     `json:"memoryClustering"`
    SwarmCollaboration    bool     `json:"swarmCollaboration"`
    OsControl             bool     `json:"osControl"`
    PerpetualMemory       bool     `json:"perpetualMemory"`
    TaskDelegation        bool     `json:"taskDelegation"`
    DeepResearch          bool     `json:"deepResearch"`
}

type Rule struct {
    Condition   string `json:"condition"`   // Ex: "Se o cliente pedir suporte técnico"
    TargetAgent string `json:"targetAgent"` // ID do agente de destino (ex: Suporte L1)
    Level       int    `json:"level"`       // 1 (Triagem primária), 2 (Escalonamento), etc
}
```

## 2. Endpoints da API Necessários

### 2.1 Salvar/Criar Gestor
**POST** `/api/manager-profile`
- **Payload:** JSON contendo os campos descritos na estrutura acima.
- **Ação no Go:** 
  - Validar se já existe um gestor ativo para a workspace/conta (se a regra de negócio exigir apenas 1 gestor por conta).
  - Encriptar a `managerApiKey` antes de salvar no banco de dados.
  - Salvar o profile.

**PUT** `/api/manager-profile/:id`
- Para atualização das configurações nas etapas do Wizard.

### 2.2 Rotas Auxiliares de Validação (Opcionais mas Recomendadas)
**POST** `/api/manager-profile/test-key`
- Para testar se a `managerApiKey` inserida no Step 1 é válida no provedor escolhido (`provider`).

## 3. Lógica de Negócio por Etapa (Implementação Backend)

### Step 1 (Identidade e Motor)
- O backend deve implementar um middleware de Rate Limit / Token Counting que observe a flag `CognitiveIndependence`. 
- Se `true`, as requisições deste Gestor devem usar a `ManagerApiKey` (se fornecida) ou registrar o consumo de forma isolada dos Agentes Especializados.
- A função de fallback no Go deve estar preparada para tentar o `FallbackProvider` automaticamente se o `Provider` primário retornar HTTP 429 ou 5xx.

### Step 2 (Comunicação)
- O Webhook do WhatsApp no Go deve ler `WhatsappMode`. Se "group", deve processar mensagens apenas se o Gestor for explicitamente mencionado (`@Hermes`). Se "private", escuta qualquer DM.
- A geração de áudio TTS na engine de voz deve ser condicionada pela regra de negócio de `AudioCondition`. Se `never`, o Go simplesmente ignora a geração de voz e economiza créditos TTS.

### Step 3 (Ferramentas)
- No momento da invocação do modelo (ex: via OpenAI Func-calling ou Claude Tools), o backend Go deve dinamicamente popular o array de tools baseando-se nas strings presentes no array `Tools`. Se "vision_analysis" não estiver ativo, o backend Go não deve enviar imagens base64 para a API do modelo para evitar vazamento de tokens.

### Step 4 (Árvore de Agentes)
- O **Roteador Híbrido** no Go precisará utilizar o modelo do Gestor para ler as `RoutingRules`.
- **Como Funciona na Prática:** A cada nova mensagem, o Gestor no backend avaliará a intenção. O Go deve injetar as `RoutingRules` como contexto ou "ferramentas de roteamento" (ex: função `route_to_agent(targetAgentId, reason)`). Se o gestor invocar essa função, o Go transfere a sessão de chat (SessionID) para o agente alvo.

### Step 5 (Superpoderes - Trabalhos Assíncronos / Cronjobs)
Aqui entra o trabalho pesado de backend (Go Routines / Cron jobs):
- **ScheduledReports:** O Go deve agendar uma rotina para extrair sumários de chat no banco às 18h e mandar a notificação push/telegram.
- **CriticalAlerts & HandoffAlerts:** O worker de processamento de mensagens em Go deve analisar o sentimento ou palavras-chave de "processo", "procon". Se detectado e a flag estiver ligada, aciona evento WebSocket ou Webhook de alerta.
- **ShadowingMode:** Requer que o Go suporte "Sussurros" no histórico (mensagens de role `system` invisíveis ao cliente) para injetar dicas do Gestor para os vendedores.
- **MemoryClustering:** Pode ser um Cron Job em Go executado de madrugada, que agrega logs de chats do dia, passa em um LLM focado em extração de tópicos e salva numa tabela de "Insights".

## Conclusão para o Agente Desenvolvedor Backend
Todas as chaves e flags que o frontend `EasyManagerWizard.tsx` manipula localmente já estão mapeadas neste documento. Ao desenvolver o backend em Go:
1. Comece criando o modelo GORM.
2. Crie as rotas CRUD `/api/manager-profile`.
3. Garanta que o worker de processamento de fila do WhatsApp (OmniRoute) leia esse modelo antes de decidir quem atende a chamada.

---

# Blueprint: Aba "Meus Funcionários" (Agentes Especializados)

O componente `SpecializedAgents.tsx` gerencia os Agentes Especializados (os "funcionários" na árvore do Gestor). O backend Go precisa garantir que o schema existente (`Profile` / `Agent`) suporte as configurações atualizadas dessa aba.

## 1. Estrutura de Dados (Modelo do Agente)
Cada agente possui sub-abas de configuração. O modelo no Go (`AgentProfile`) deve suportar:

```go
type AgentProfile struct {
    ID                  string   `json:"id" gorm:"primaryKey"`
    Active              bool     `json:"active"`                // Botão de ligar/desligar agente
    Name                string   `json:"name"`                  // Ex: Vendedor L1
    Description         string   `json:"description"`
    
    // ABA: Perfis (Configurações e Personalidade)
    SystemPrompt        string   `json:"system_prompt"`
    GreetingMessage     string   `json:"greeting_message"`      // Mensagem de saudação automática
    
    // ABA: Voz (Voz e Ligações)
    VoiceProvider       string   `json:"voice_provider"`        // "elevenlabs", "openai"
    VoiceID             string   `json:"voice_id"`
    VoiceSpeed          float64  `json:"voice_speed"`
    VoiceStability      float64  `json:"voice_stability"`
    VoicePitch          float64  `json:"voice_pitch"`           // Para OpenAI TTS
    VoiceEmotion        float64  `json:"voice_emotion"`         // Expressividade
    
    // ABA: IA & Modelo
    Provider            string   `json:"provider"`              // "openai", "anthropic", "groq"
    Model               string   `json:"model"`                 // ex: "gpt-4o-mini"
    ApiKey              string   `json:"api_key,omitempty"`     // Se vazio, usar Global
    Temperature         float64  `json:"temperature"`
    MaxTokens           int      `json:"max_tokens"`
    
    // ABA: Ferramentas & Webhook
    WebhookUrl          string   `json:"webhook_url"`           // URL para disparos do agente
    EnableCalendar      bool     `json:"enable_calendar"`
    EnableWebSearch     bool     `json:"enable_web_search"`
    
    // ABA: RAG / Base de Conhecimento
    // Opcional: Relacionamento 1:N com arquivos RAG ou namespaces de VectorDB
    RagKnowledgeBaseID  string   `json:"rag_knowledge_base_id"`
}
```

## 2. Lógica de Negócio e Endpoints (Go)

### 2.1 Endpoints de CRUD
- **GET `/api/agent-profiles`**: Retorna a lista de agentes. Utilizado pela barra de pesquisa e pela "Gamificação" no frontend.
- **PUT `/api/agent-profiles/:id`**: Salva as edições feitas "in-place" nos sub-paineis (Voz, IA & Modelo, etc).
- **POST `/api/agent-profiles`**: (Via Wizard Fácil de Agente - `EasyAgentWizard.tsx`).

### 2.2 Processamento de Webhook (Aba Ferramentas)
- Se a propriedade `WebhookUrl` estiver preenchida, o Go deve disparar um POST assíncrono (Webhooks) sempre que o agente realizar ações chave (ex: finalização de atendimento, captura de lead) enviando o sumário do chat no payload.

### 2.3 Tratamento de Senha / API Key
- O campo `api_key` possui proteção no frontend (`autoComplete="new-password"`).
- O backend deve receber a chave em plain-text via TLS, encriptá-la (ex: AES-GCM) antes de salvar no DB, e NUNCA retorná-la nos GETs (usar `omitempty` ou máscara no JSON de resposta). Se na requisição PUT o campo vier vazio ou ausente, não deve sobrescrever a chave salva.

### 2.4 Gamificação (Dashboard)
- O componente de Gamificação no frontend atualmente usa pseudo-aleatoriedade em cima do ID do agente (`parseInt(a.id.slice(0,4), 16)`).
- **Tarefa Backend:** Criar uma tabela/cache de `AgentMetrics` (ex: Redis ou tabela SQL) para retornar métricas reais (número de vendas, tickets resolvidos) no endpoint `GET /api/agent-profiles`, permitindo que o frontend exiba um ranking verdadeiro.

---

# Blueprint: Aba "Criar Funcionário Fácil" (`EasyAgentWizard.tsx`)

O `EasyAgentWizard.tsx` é um fluxo de 8 passos para criação simplificada de um Agente Especializado ("Funcionário"). Este wizard consolida diversas capacidades do sistema em um formulário intuitivo. O endpoint alvo no Go é **POST `/api/agent-profiles`**.

## 1. Campos e Estados Coletados pelo Wizard

O payload JSON que o frontend enviará no POST conterá as seguintes chaves (ou algo mapeável para o `AgentProfile`):

```json
{
  "name": "Nome do Agente",
  "role": "vendas", // ID do arquétipo escolhido
  "voice_id": "...", // se a persona exigir voz
  "system_prompt": "...", // Concatenado das Etapas 1 e 2
  "tools": ["web_search", "calendar"], // Etapa 3
  
  // Etapa 4 (Canais)
  "channels": ["whatsapp", "web"],
  
  // Etapa 5 (Agenda e Experiência)
  "agenda_timezone": "America/Sao_Paulo",
  "agenda_days": ["Seg", "Ter", "Qua"],
  "agenda_hours": {"start": "09:00", "end": "18:00"},
  "agenda_excluded_dates": ["25/12/2026"],
  
  // Etapa 6 (Handoff / Transbordo)
  "handoff_keywords": "falar com humano, cancelar",
  "handoff_text_message": "Um momento, vou chamar a equipe...",
  "handoff_voice_message": "Aguarde um momento na linha...",
  "handoff_action": "pause_and_notify", // ex: pausar IA e notificar admin
  
  // Etapa 7 (Follow-Up / Retomada)
  "followup_enabled": true,
  "followup_condition": "Se o lead sumir por X tempo",
  "followup_time": 24, // em horas
  "followup_message": "Oi, você ainda tem interesse?"
}
```

## 2. Requisitos de Lógica no Backend (Go)

### 2.1 Construção do System Prompt (Etapas 1 e 2)
O frontend permite que o usuário escreva instruções e escolha um "tom" de voz. Embora o frontend junte essas informações na submissão, o backend no Go deve salvar o resultado final no campo `SystemPrompt` do banco. Ao rodar o agente (OmniRoute), o Go deve garantir que essas instruções sejam respeitadas pela LLM de forma rígida.

### 2.2 Controle de Agenda (Etapa 5)
- **Timezone e Horários:** O roteador em Go (OmniRoute) deve ler o `agenda_timezone`, os `agenda_days` e `agenda_hours`.
- **Regra:** Se uma mensagem ou ligação chegar FORA desse horário ou em um feriado (`agenda_excluded_dates`), a IA deve responder com uma mensagem automática configurada de "Fora de Horário" OU pausar, dependendo da configuração. (A infraestrutura do OmniRoute deve bloquear a injeção do LLM para economizar tokens nesses casos).

### 2.3 Sistema de Transbordo (Handoff - Etapa 6)
Este é um pilar crítico. O Go deve processar cada nova mensagem recebida (via NLP ou simples "Contains") antes de enviar pro LLM:
1. Validar se a mensagem contém uma das `handoff_keywords`.
2. Se **sim**: 
   - No Whatsapp (texto): O Go dispara a `handoff_text_message` pro cliente, atualiza a Sessão no DB (coluna `status = 'waiting_human'`) e corta o LLM. Dispara notificação push/webhook pro Admin.
   - Em Voz (Telefonia): O Go dispara o áudio `handoff_voice_message` e faz um SIP Transfer (ou encerra pedindo que o admin retorne).

### 2.4 Follow-Up Automático (Etapa 7)
Esta rotina requer tarefas agendadas / Cron Jobs no Go (ou RabbitMQ Delayed Messages):
- Quando um chat do WhatsApp é marcado como "Aguardando Resposta do Cliente" (status ocioso), o Go inicia um timer baseado no `followup_time`.
- Se o tempo expirar e o cliente não tiver respondido (nenhuma nova mensagem na thread), o Go deve disparar proativamente a `followup_message` no WhatsApp daquele lead (usando a API do Evolution API/Baileys, que deve estar conectada na porta de saída).

---

# Blueprint: Aba "Base de Conhecimento" (RAG)

O componente `AgentRagPanel.tsx` gerencia a ingestão de contexto externo (RAG - Retrieval-Augmented Generation) para o agente. Ele permite upload de arquivos e destilação de histórico de conversas. 

O backend Go deve possuir um banco vetorial conectado (ex: pgvector, Pinecone, Qdrant ou ChromaDB).

## 1. Endpoints de Gerenciamento (Vector DB)

### 1.1 Listagem de Documentos
- **GET `/api/rag/documents?agent_id=xxx`**
- **Resposta Esperada:** 
  ```json
  {
    "documents": [
      { "id": "doc-1", "name": "manual_vendas.pdf", "source": "upload", "chunks": 42, "created_at": "2026-07-20T10:00:00Z" },
      { "id": "doc-2", "name": "Histórico Destilado", "source": "conversations", "chunks": 15, "created_at": "..." }
    ]
  }
  ```

### 1.2 Upload de Arquivo Manual
- **POST `/api/rag/documents?agent_id=xxx`** (Multipart/Form-Data)
- **Ação no Go:**
  1. Ler o arquivo (TXT, MD, CSV, JSON).
  2. Fazer o *chunking* (ex: 512 tokens por pedaço com overlap de 50).
  3. Gerar os *Embeddings* via API da OpenAI (`text-embedding-3-small`).
  4. Salvar os embeddings no VectorDB associados ao `agent_id` (namespace).
  5. Retornar `{"chunks": 42}` para o frontend.

### 1.3 Excluir Documento
- **DELETE `/api/rag/documents/:id`**
- **Ação no Go:** Remover do banco relacional e apagar todos os vetores do VectorDB associados àquele `doc_id`.

## 2. Destilação e Auto-Evolução (Shadowing)

### 2.1 Treinamento Manual via Histórico
- **POST `/api/rag/ingest-conversations`**
- **Payload:** `{"agent_id": "xxx"}`
- **Ação no Go:**
  1. Buscar as últimas conversas fechadas no banco de dados para o agente.
  2. Passar por um LLM sumarizador rápido para destilar (ex: "Qual foi o argumento que o atendente humano/ia usou que converteu essa venda?").
  3. Chunking, Embedding e ingestão no VectorDB.

### 2.2 Auto-Evolução Automática (Flag de Shadowing)
No frontend, existe uma flag `Auto-Evolução (Shadowing)`. Se o usuário a ligar, isso implica em uma regra de negócio contínua no Go:
- **Webhooks/Eventos:** Toda vez que um chat for marcado como "Resolvido/Sucesso", o worker assíncrono do Go deve puxar o histórico dessa conversa, extrair a melhor resposta/argumento (usando um LLM leve) e embutir *automaticamente* no VectorDB. Dessa forma, a Base de Conhecimento do Agente cresce passivamente a cada venda bem sucedida.

---

# Blueprint: Aba "Chat de Teste" e Simulador Avançado (`AgentChatTest.tsx`)

A aba de testes no frontend é muito mais do que um chat simples. É uma interface avançada de *Sandboxing*, *LLM-as-a-judge* e *Red Teaming* para garantir que o Agente se comporte de acordo com os "Guardrails" antes de ser liberado no WhatsApp ou Telefonia. 

O backend Go deve prover as seguintes rotas exclusivas de simulação (que **não** disparam webhooks nem faturam clientes):

## 1. Rota Principal de Sandboxing (Chat Manual)
- **POST `/api/agents/:id/test`**
- **Payload recebido:** `{"message": "Olá", "history": [...], "mock_context": {...}}`
- **Ação no Go:**
  1. O Go recebe a requisição. Se o campo `mock_context` (JSON de CRM simulado) for enviado, o Go deve injetar essas variáveis no System Prompt (ex: `{"lead_vip": true}`).
  2. O Go roda o motor LLM configurado (OpenAI/Anthropic) do Agente, executa o RAG se necessário, e retorna a resposta pura.
- **Resposta:** `{"reply": "...", "used_rag": true}`

## 2. Juiz Semântico (LLM-as-a-Judge)
Logo após receber a resposta do Teste, o frontend dispara uma segunda requisição para avaliar a qualidade técnica daquela resposta.
- **POST `/api/agents/:id/evaluate`**
- **Payload:** `{"message": "...", "reply": "..."}`
- **Ação no Go:**
  1. O Go deve invocar um modelo de LLM separado (um juiz, ex: GPT-4o).
  2. O juiz lê a mensagem do usuário, a resposta do Agente e o System Prompt base do agente, verificando se a resposta violou regras (guardrails) da empresa.
- **Resposta:** `{"judge_score": 8, "judge_reasoning": "Respondeu bem, mas faltou cordialidade.", "guardrail_violated": false}`

## 3. Simulador Multi-Personas (Guerra de Bots / Red Teaming)
O painel de teste permite ao usuário iniciar um "Auto-Simulador de Personas" com N personas atacando o bot simultaneamente.
- **POST `/api/agents/:id/wargame`**
- **Payload:** `{"personas": 3, "tone": "friendly"}`
- **Ação no Go:**
  1. O Go deve invocar um LLM Atacante (Red Team) para gerar perfis de clientes (ex: "Cliente Furioso", "Concorrente", "Objeção de Preço").
  2. Para cada persona, o LLM Atacante gera uma mensagem inicial de desafio.
  3. O Agente alvo responde ao desafio.
  4. O Juiz (do passo 2) avalia se o Agente alvo resistiu ao ataque ou quebrou regras.
- **Resposta Esperada (JSON array):**
  ```json
  {
    "turns": [
      {
        "persona": "Cliente Furioso",
        "attack": "Vou no Procon, cancelem agora!",
        "reply": "Sinto muito pelo ocorrido...",
        "judge_score": 9,
        "judge_reasoning": "Manteve a calma perante crise",
        "guardrail_violated": false,
        "used_rag": false
      }
    ],
    "avg_score": 9.0,
    "violations": 0,
    "total_turns": 1
  }
  ```
  *(O Frontend renderizará isso como uma longa conversa onde a IA atacou e se defendeu sozinha)*.

---

# Blueprint: Aba "O Treinador" (`AgentTrainerPanel.tsx`)

"O Treinador" é o módulo de melhoria contínua (*Fine-Tuning* ou *Prompt Optimization*). Em vez de depender do gestor humano para reescrever o `System Prompt` do Agente, o Treinador roda em background (Go Routines) lendo as últimas centenas de conversas reais do WhatsApp e reescreve o prompt base automaticamente para cobrir as falhas identificadas, gerando "Versões".

## 1. Estimativa de Custos (Pré-Run)
- **POST `/api/training/estimate`**
- **Payload:** `{"agent_id": "xxx", "conv_limit": 20}`
- **Ação no Go:** Antes de rodar, o Go conta quantas conversas não classificadas existem (limitado a `conv_limit`) e multiplica pelos tokens médios. Retorna a estimativa de custo em dólares para a OpenAI.
- **Resposta:** `{"conversations": 20, "est_tokens_in": 10000, "est_cost_usd": 0.50, "note": "..."}`

## 2. Iniciar Treinamento (Jobs em Background)
- **POST `/api/training/jobs`**
- **Payload:** `{"agent_id": "xxx", "conv_limit": 20, "max_cost_usd": 5.0}`
- **Ação no Go:**
  1. Cria um registro no banco de dados na tabela `TrainingJobs` com status `running`.
  2. Inicia uma **Goroutine** (processo em background) assíncrona.
  3. A Goroutine puxa as conversas, envia pro LLM Treinador avaliar falhas/objeções (ex: "Onde o agente atual errou e não conseguiu vender?").
  4. O LLM Treinador gera um NOVO `System Prompt` aprimorado que corrige as falhas encontradas.
- **Resposta (Imediata):** `{"job_id": "job-123", "status": "running"}`

## 3. Polling de Progresso
Enquanto o Go roda em background, o frontend faz polling (a cada 2s) para ver a barra de progresso encher.
- **GET `/api/training/jobs/:id`** (ou `?agent_id=xxx` para pegar o último)
- **Resposta:** `{"id": "job-123", "status": "running", "processed": 5, "total": 20, "cost_usd": 0.12}`
- **Atenção (Human-in-the-Loop):** Se o LLM Treinador encontrar uma objeção que ele não sabe como o dono da empresa gostaria de resolver (ex: "Vocês aceitam permuta?"), o Go deve trocar o `status` para `paused` e aguardar o gestor responder na interface antes de continuar.

## 4. Cancelar / Abortar Treinamento
- **POST `/api/training/jobs/:id/cancel`**
- **Ação no Go:** Encerra a Goroutine correspondente e marca o job como `aborted`. O custo parcial (`cost_usd`) deve ser salvo.

## 5. Versionamento de Prompts (A/B)
O final bem sucedido de um Treinamento gera uma nova "Versão" de Prompt. O Treinador **NÃO** substitui o prompt de produção automaticamente (por segurança).
- **GET `/api/training/prompts?agent_id=xxx`**
  - Lista o histórico gerado. Ex: `[{"version": 1, "is_active": false}, {"version": 2, "is_active": true}]`
- **GET `/api/training/prompts/:id`**
  - Retorna o corpo completo do prompt para o gestor ler.
- **POST `/api/training/prompts/:id/activate`**
  - **Ação no Go:** Pega o `body` desse prompt específico e salva na coluna `SystemPrompt` do modelo `AgentProfile` (atualizando o agente em produção na hora). E marca `is_active = true` apenas para ele.

## 6. Melhorias Futuras (Roadmap de Evolução)
Para elevar o nível de imersão corporativa dessa ferramenta no futuro, a arquitetura Go pode ser expandida para suportar as seguintes funcionalidades:

### A. Comparação Lado a Lado (Side-by-Side Diff)
O backend deve ser capaz de comparar a versão anterior do Prompt com a versão recém-gerada pelo Treinador e retornar as diferenças exatas. 
- **Nova Rota Sugerida:** `GET /api/training/prompts/:id/diff`
- **Comportamento:** O Go retorna um diff destacando apenas as regras que foram adicionadas ou removidas (ex: `+ [Nova Regra] O cliente perguntou muito sobre permuta, agora o agente sabe que só aceitamos 30% em permuta.`), evitando que o Gestor tenha que reler o Prompt inteiro.

### B. Filtro Cirúrgico de Treinamento (Foco da Mentoria)
O payload para iniciar um treinamento (`POST /api/training/jobs`) passará a aceitar um parâmetro de `filter`.
- **Ação no Go:** Em vez de puxar as últimas `N` conversas indiscriminadamente, o backend roda a query baseada no foco:
  - `filter="errors"`: Puxa só as conversas onde o "Guardrail" foi violado ou houve "Repasse para a Equipe Humana".
  - `filter="success"`: Puxa só as conversas com fechamento/conversão positiva (Modelagem de Sucesso).
  - `filter="objections"`: Puxa só conversas que contiveram palavras ligadas a preço/rejeição.

### C. Modo Estágio (Shadow Mode / Teste A-B Real)
Em vez de simplesmente ativar a nova Versão do Prompt de vez, o Go permitirá rodá-la como um "Estagiário observador".
- **Ação no Go:** Uma nova rota `POST /api/training/prompts/:id/shadow_mode` fará com que o sistema distribua (em background) 20% das mensagens reais para essa versão candidata. O sistema mede e compara a assertividade dessa versão contra a que está no ar antes de recomendar a substituição oficial.

### D. Resolução Prática de Objeções (Micro-Chat de Liderança)
Quando o Treinador entra no status `paused` porque não sabe resolver uma objeção bizarra (Human-in-the-Loop), a rota de retomar o Job passará a aceitar a resposta do Gestor como um histórico de chat.
- **Ação no Go:** O Go envia para a LLM Treinadora o log do Gestor respondendo ao cliente, e a LLM extrai sozinha a "Técnica de Venda" usada na prática para adicionar à Versão do Prompt, substituindo a necessidade de o Gestor digitar uma instrução estática (fria).

### E. Gamificação do Desempenho do Funcionário (Boletim)
O backend pode passar a retornar o "Nível do Funcionário" (`GET /api/agent-profiles/:id/stats`).
- **Ação no Go:** A cada ciclo de avaliação bem-sucedido, o backend gera métricas de aprendizado (ex: "Melhoria de 15% em Contorno de Preço") e badges virtuais na modelagem. O Gestor terá a sensação de estar evoluindo um personagem de RPG na sua operação.

---

# Blueprint: Aba "Follow-Up Zero Click" (Automação em Lote com Voz Clonada)

A aba de Follow-up passará a suportar a geração de áudios sintéticos ultra-realistas utilizando a voz clonada do próprio vendedor ou gestor. Isso permite abordagens em massa, porém com personalização unitária de altíssimo nível (chamando o cliente pelo nome).

## 1. Clonagem de Voz (Integração TTS)
- **POST `/api/voice/clone`**
- **Ação no Go:** 
  1. Recebe uma amostra de áudio limpa (MP3/WAV) do vendedor via Multipart Form.
  2. Faz o proxy da requisição para a API de Voice Cloning (ex: ElevenLabs, Play.ht ou OpenAI TTS).
  3. Salva o `voice_id` exclusivo no cadastro do vendedor na tabela `Users`.

## 2. Geração Assíncrona de Áudios de Follow-up (O Lote Mágico)
- **POST `/api/followup/generate-audios`**
- **Payload:** `{"leads": ["id_1", "id_2", "id_3"], "context_prompt": "Oferecer 10% de desconto por ser sexta-feira"}`
- **Ação no Go (Background Workers):**
  1. O Go iterage sobre a lista de leads. Para cada um, chama a LLM para gerar um roteiro curtinho e hiper-personalizado: *"Fala [João], tudo bem? Lembrei de você hoje, consegui aquele desconto..."*.
  2. O Go dispara chamadas paralelas (Goroutines) para a API de TTS enviando o texto e o `voice_id` do vendedor.
  3. A resposta (binário de áudio) é salva temporariamente em um bucket S3/Minio.
  4. Retorna para o frontend as URLs de áudio (para que o vendedor possa dar "Play" e aprovar a própria voz sintética).

## 3. Disparo como "Áudio Original" (Push-To-Talk)
- **POST `/api/followup/blast-audios`**
- **Ação no Go:**
  - Pega as URLs dos áudios gerados e enfileira os disparos no WhatsApp (Evolution API / Baileys).
  - **Requisito Crítico:** O Go DEVE forçar a flag `ptt: true` (Push-To-Talk) na API do WhatsApp. Isso garante que o áudio chegue para o cliente não como um arquivo MP3 encaminhado (o que denuncia a automação), mas sim como um áudio gravado na hora, com o ícone do microfoninho azul brilhando.

---

# Blueprint: Aba "Campanhas" (Mission Control & Launchpad)

A aba de campanhas deixará de ser uma tabela estática para se transformar em um Centro de Comando Visual em Tempo Real. O foco é alta densidade de feedback via WebSockets durante os disparos em massa.

## 1. Monitoramento ao Vivo (Event Stream / WebSocket)
- **Endpoint:** `WS /api/campaigns/live-stream` (ou SSE - Server-Sent Events)
- **Ação no Go:**
  1. Durante a execução do Worker de fila de disparos (RabbitMQ / Redis PubSub), o backend Go transmite os eventos atômicos da campanha para os clientes conectados.
  2. Cada evento (Enviado, Recebido, Lido - *Blue Tick*, Respondido) emite um pacote leve.
  3. **Payload Exemplo:** `{"event": "read", "lead_id": "123", "region": "SP", "timestamp": "10:45:01"}`
  4. Isso alimentará as animações de radar e as barras de progresso hiper-reativas no React sem fazer polling HTTP infinito.

## 2. Termodinâmica de Vazão (Anti-Ban Adaptativo)
- **Ação no Go (Worker Rule):**
  - O loop de disparo no Go não pode ser cego. Deve ser utilizado o padrão de "Leaky Bucket" ou "Token Bucket" atrelado ao Trust Score do chip logado.
  - Se a API do WhatsApp começar a ficar lenta, o Go desacelera a injeção (Throttle down) e envia um aviso pelo WS: *"Sinal amarelo do Meta. Desacelerando disparos para preservar a saúde do chip..."*.

## 3. Telemetria Rápida e ROI Instantâneo
- **GET `/api/campaigns/:id/telemetry`**
- **Ação no Go:** Agregação via Redis para latência zero. 
  - Constrói o funil da campanha sob demanda: `Fila -> Enviados -> Entregues -> Lidos -> Respostas (Replies)`.
  - Quando um lead engaja respondendo no Whatsapp logo após a campanha, o Go intercepta a flag e atualiza o `ROI Provável` da campanha, fazendo a barra financeira no Mission Control subir em tempo real à medida que o dinheiro "entra".

---

# Blueprint: Melhorias Globais do Sistema (UI/UX & Arquitetura)

Para consolidar o CRM como uma plataforma "Enterprise SaaS" de altíssima produtividade, as seguintes frentes de experiência geral do usuário (cross-platform) devem ser implementadas. Algumas afetam apenas frontend, outras necessitam suporte do Go.

## 1. Barra de Comando Universal (O Efeito Cmd+K)
- **Ação no Frontend:** Implementar um modal de busca global (escutando as teclas `Ctrl+K` ou `Cmd+K`).
- **Ação no Backend:** Rota `GET /api/search/omni?q=termo`. O Go roda uma busca semântica ou Full-Text em múltiplas tabelas simultaneamente (Leads, Tags, Contatos) e injeta rotas de atalho (ex: "ir para configurações"). O resultado agregado deve retornar em menos de 100ms.

## 2. Copiloto de Sistema "Delegar para IA" (Evolução Funcional)
O botão atual de Delegar já pré-digita mensagens para o Gestor. A evolução o transformará em um Agente Operacional de Sistema.
- **Ação no Go:** Suporte a *Function Calling / Tool Use* na LLM. 
- Em vez de gerar texto, a IA pode **executar ações no banco de dados**. Se o usuário digitar no chat do Copiloto: *"Desligue a campanha Black Friday e mostre meus leads de hoje"*, o Go intercepta a chamada das ferramentas `pause_campaign()` e `get_daily_leads()`, executa as ações em background, e retorna o card visual pronto na interface de conversa.

## 3. Central de Alertas Acionáveis (Actionable WebSockets)
- O painel de notificações não pode ser apenas um log passivo. 
- **Ação no Go:** Quando ocorrer um evento grave (ex: "Lead detectado xingando o robô"), o Go envia via WebSocket um payload estruturado com botões de ação:
  `{"title": "Crise: Lead Irritado", "actions": [{"id": "takeover", "label": "Pausar IA e Assumir"}, {"id": "ignore", "label": "Ignorar"}]}`
- O usuário clica no alerta e a ação dispara um Webhook reverso para o Go, resolvendo a crise em 1 clique sem precisar navegar até a página do lead.

## 4. Abas de Workspace Internas (Multi-Contexto)
- **Ação no Frontend (React):** Otimização profunda de roteamento e estado. Eliminar a perda de progresso durante navegações longas. Em vez do Router "matar" a página atual quando o usuário clica no menu, a aplicação gerenciará um sistema de abas horizontais no topo (igual ao Chrome ou VS Code). O estado (Redux/Zustand) das páginas em background fica congelado na RAM do navegador, permitindo alternar instantaneamente entre a edição de uma campanha gigante e a aba de atendimento.

## 5. Sistema de Desfazer Universal (Toast Undo Timeout)
- **Ação no Go:** Implementar deleção lógica (*Soft Delete*) pesada (`deleted_at = NOW()`) em vez de deleções definitivas no banco, e suporte a reversão de eventos de histórico de leads.
- **Ação no Frontend:** Sempre que o usuário executar uma ação drástica (deletar lead, arrastar para perdido, pausar campanha), o frontend intercepta com um Toast: *"Ação realizada. [DESFAZER]"* que dura 7 segundos. Se clicado, dispara `PUT /api/undo/last-action` que restaura o status prévio instantaneamente, perdoando erros acidentais do mouse.
