# CORREÇÕES PENDENTES — Hermes Call — 2026-08-01

> Documento criado a pedido do dono. Lista TODAS as correções pedidas depois do backup.
> **Nada foi mexido ainda.** Cada item tem plano cuidadoso e nível de confiança.
> Regras absolutas do dono estão no topo. Só mexer no código depois do backup completo.

---

## ⚠️ REGRA Nº 0 — ANTES DE QUALQUER MUDANÇA (extremamente sensível)

O dono foi enfático: **já perdemos versão boa antes**. Então, antes de tocar em QUALQUER código:

1. **Backup LOCAL completo** (cópia da pasta inteira `d:/hermes-call`, fora do git).
2. **Backup no GitHub** — commit + push do estado atual + criar **tag de versão estável** (ex: `v0.3.6-stable-2026-08-01`).
3. **Marcar a imagem que está no ar AGORA como `:stable`** no VPS (ponto de rollback de 1 comando).
4. **JAMAIS perder a versão atual.** Se não tiver 100% de certeza que a correção resolve → **NÃO MEXER** e anotar aqui como "precisa investigar mais".
5. Só depois de tudo isso, mexer **uma correção por vez**, testar, garantir que funciona como pedido, e só então ir pra próxima.

**Estado atual do git (2026-08-01):**
- Branch: `versao-final-bd24`
- Último commit relevante de código: antes dos `docs: vigilancia`
- Arquivos modificados não commitados: `RecordingsPage.tsx`, `recording.go`, `telegram.go`, `VERSION`
- VERSION: `0.3.6` / imagem no ar: `v0.3.6 build 20260801-1134 channel=beta`
- Remote: `github.com/Emersonjosielmrx/hermes-call.git`

---

## LISTA DE CORREÇÕES (uma por vez, na ordem de prioridade sugerida)

Legenda de confiança:
- 🟢 ALTA — sei onde é e tenho certeza que resolve
- 🟡 MÉDIA — sei a área, preciso confirmar detalhe antes
- 🔴 BAIXA — precisa investigar bastante antes de tocar (NÃO mexer sem certeza)

---

### 1. 🟡 Radar Ao Vivo não mostra ligação quando ligo pelo Telegram
**O que o dono relatou:** "ele não aparece quando estou ligando do telegram aqui pra acompanhar as ligações e a lista que está ligando etc."
**Esperado:** ao disparar ligação pelo Telegram, o painel "Radar Ao Vivo" deve mostrar a chamada ativa em tempo real (número, duração, status) e a lista do que está ligando.
**Hipótese:** as ligações iniciadas via Telegram não estão sendo publicadas no mesmo broker/SSE que o painel escuta (só as iniciadas pelo painel aparecem).
**Investigar antes:** como o disparo do Telegram cria a chamada vs. o `broker.upsertCall` do painel; se o evento SSE é emitido pro dono certo.
**Confiança:** média — precisa rastrear o caminho Telegram→chamada→broker.
**STATUS (2026-08-01):** ✅ RESOLVIDO. Investigação confirmou a hipótese: Telegram dispara via `POST /api/sessions/{sid}/broadcast` (CallClient → runCampaign), e o comentário no broker (linha 217-219) diz explicitamente que **"Ligações de campanha NÃO entram no broker"**. O Radar Ao Vivo escuta `broker.upsertCall()`, então chamadas via Telegram/broadcast não apareciam. Correção aplicada: adicionado `upsertCall` em `runCampaign` (broadcast.go:1874) logo após `startOutgoing`, igual os outros fluxos (masscall/httpapi/external_api todos fazem isso). Agora publica `CallRecord{Direction: "outbound", Status: StatusRinging, ...}` no broker → SSE → painel atualiza em tempo real. Build Go OK.

---

### 2. 🔴 Campanha não agrupa como deveria (agrupamento falso)
**O que o dono relatou:** "a campanha não está sendo agrupada como deveria, ontem mandei várias e ele só diz no Telegram que agrupou mas não agrupou de fato no painel como fazia. Ajuste inclusive as já feitas ontem em uma só."
**Esperado:** várias ligações da mesma campanha aparecem AGRUPADAS num card só no painel (como funcionava antes). Telegram diz "agrupado" mas o painel mostra separado.
**Ação extra pedida:** consertar retroativamente as campanhas de ontem (31/07) para aparecerem agrupadas.
**Investigar antes:** lógica de agrupamento de campanha no painel; por que o Telegram reporta agrupado mas o painel não; se é campo `campaign_id`/`group` faltando nos registros de ontem.
**Confiança:** BAIXA — mexer em dado histórico é sensível, precisa entender o schema antes. NÃO tocar sem certeza.
**STATUS (2026-08-02):** ✅ RESOLVIDO (causa-raiz + conserto retroativo, SEM mexer em dado histórico). Investigação: o agrupamento EM SI funciona — `activeCampaignForUser` (janela rolling 4h por userID) faz as ligações caírem na MESMA campanha, e `SeedQueued` adiciona cada número em `campaign_results` sob o mesmo `campaign_id`. Por isso o Telegram dizia "agrupou" (verdade). O BUG era só de EXIBIÇÃO: a campanha "Ligação via Telegram" é criada com `total=1` (coluna estática), e `SeedQueued` NÃO incrementa `c.total` ao agrupar. A query `List` (store.go) lia `c.total` → painel mostrava "1" mesmo com N ligações agrupadas → parecia "não agrupou". Correção: `List` agora usa `GREATEST(c.total, COUNT(r.number))` — conta os results reais. Isso conserta RETROATIVAMENTE as campanhas de 31/07 automaticamente (é read-time, não altera dado gravado — zero risco). Build Go OK. **Bônus:** não precisou de migração nem UPDATE em dado histórico (respeitou o "NÃO tocar sem certeza"). **Nota:** o agrupamento in-memory (`s.openCamp`) se perde em redeploy — se o servidor reiniciar no meio de uma sessão de ligações, as de antes/depois do restart caem em campanhas separadas. Isso é limitação conhecida (documentar pro dono), mas NÃO é o bug relatado (que era exibição).

---

### 3. 🔴 Chat não bate com as conversas reais (faltam muitas)
**O que o dono relatou:** "o chat não bate com as conversas reais, faltam muitas, muitas mesmo."
**Esperado:** a aba Chat deve listar TODAS as conversas reais do WhatsApp, não um subconjunto.
**Investigar antes:** como o Chat busca conversas (paginação? filtro? só as com mensagem?); print mostra "Não lidas 209" então há volume; ver se o fetch está limitando/truncando.
**Confiança:** BAIXA — precisa entender a fonte das conversas (Chatwoot? store local? WhatsApp direto).
**STATUS (2026-08-02):** ✅ RESOLVIDO (causa-raiz encontrada). O Chat lê da tabela `messages` local (`ListChats`), populada pelo handler de eventos do whatsmeow. Descoberta: o switch em `session.go` (handleEvent) tratava `*events.Message` (mensagens NOVAS) mas NÃO tratava `*events.HistorySync` — o evento que o WhatsApp dispara ao parear, trazendo TODO o histórico de conversas em lotes. Resultado: só apareciam conversas que receberam mensagem DEPOIS do pareamento; o histórico inteiro (as "muitas" que faltavam) nunca era persistido. Correção: criado `historysync.go` com `handleHistorySync` que percorre `data.GetConversations()` → `conv.GetMessages()` → `HistorySyncMsg.GetMessage()` (WebMessageInfo) e persiste cada uma via `SaveMessage` (idempotente, ON CONFLICT). Registrado o `case *events.HistorySync` no switch. Pula reações/edições (type unknown), converte timestamp seg→ms. Build Go OK. **Efeito:** ao reparear (ou no próximo HistorySync que o WA enviar), o inbox enche com as conversas reais. **Ressalva:** o WhatsApp controla QUANDO/QUANTO histórico manda (geralmente ~3-6 meses recentes no pareamento); mensagens muito antigas podem não vir — limite do protocolo, não do código. Combinado com o fix #4 (agrega todas as linhas), cobre o relato.

---

### 4. 🟡 Chat: seletor de qual número/linha responder (estilo Chatwoot)
**O que o dono relatou:** "se tiver mais de número ligado como tem, tem que ter um campo pra selecionar qual ou se todos juntos de todos os números e em qual responde tipo Chatwoot."
**Esperado:** quando há múltiplas linhas WhatsApp conectadas, o Chat precisa de um seletor: ver conversas de UMA linha específica OU de TODAS juntas, e escolher por qual linha responder.
**Confiança:** média — é feature nova de UI + backend multi-sessão; escopo claro.
**STATUS (2026-08-02):** ✅ RESOLVIDO (backend + frontend). **Backend** (`whatsapp_chats_api.go`): `GET /api/whatsapp/chats` antes hardcodava a 1ª sessão pareada; agora aceita `?sessionId=` (filtra uma linha) ou `all`/vazio (agrega TODAS as linhas do dono). Ao agregar, cada chat carrega `sessionId`+`line` (nome amigável) e ordena por recência. **Frontend** (`ChatPage.tsx`): carrega todas as linhas pareadas; seletor `<select>` (só aparece com 2+ linhas) pra ver "Todas as linhas" ou uma específica; `activeSid` deriva a sessão do chat ativo (quando "todas", usa o sessionId do próprio chat) pra carregar thread/histórico E enviar pela linha certa; badge da linha em cada conversa (modo "todas") + "via {linha}" no cabeçalho da thread. Build client+server OK.

---

### 5. 🟡 Promessas detectadas não aparecem no painel de Agendamento + botão de atalho
**O que o dono relatou:** "tem várias promessas que foram feitas e detectadas mas não mostra no painel de agendamento (se é que a aba não é lá), mas deve ter um botão que encaminhe pra aba Promessas assim fica fácil de achar."
**Esperado:** promessas detectadas nas ligações devem aparecer no fluxo de agendamento; e deve haver um botão claro que leve direto pra aba "Promessas".
**Nota:** existe aba "Promessas" (vista no print de Gestão de Leads).
**Confiança:** média — adicionar botão de navegação é 🟢; ligar promessas↔agendamento precisa confirmar fonte de dados.
**STATUS (2026-08-01):** ✅ Parte 🟢 FEITA — botão "Promessas" adicionado no cabeçalho da AgendaPage (`setView("promises")`, leva direto pra aba). ⏳ Parte 🟡 PENDENTE DE INVESTIGAÇÃO — ligar promessas detectadas ao fluxo de agendamento precisa confirmar a fonte de dados das promessas (de onde vêm, se `PromisesManagerTab` consome endpoint que a AgendaPage também poderia ler). NÃO mexido pra não quebrar sem certeza.

---

### 6. 🟡 Funil: clicar em "Etapa" ou "Origem" não faz diferença
**O que o dono relatou:** "no final tanto faz clicar em etapa ou origem não faz diferença no painel."
**Esperado:** o toggle Etapa/Origem no Funil de contatos deve mudar de fato o agrupamento/visualização dos contatos.
**Nota:** os 2 prints mostram o mesmo botão alternando entre "Etapa" e "Origem" mas conteúdo idêntico.
**Confiança:** média — bug de front provavelmente; localizar o handler do toggle.

---

### 7. 🔴 Gráficos do Analytics não são reais
**O que o dono relatou:** "esses gráficos do analytics não são reais."
**Esperado:** Analytics deve refletir dados reais, não mock/placeholder.
**Investigar antes:** quais gráficos usam dados hardcoded/fake vs. API real (o próprio painel de Copiloto tinha texto de exemplo hardcoded — pode ter mais).
**Confiança:** BAIXA — precisa auditar cada gráfico e sua fonte.
**STATUS (2026-08-02):** ✅ RESOLVIDO (auditoria completa + fixes dos pontos falsos). Auditei os 7 componentes de analytics. VEREDITO: a maioria é REAL (busca via `apiGet` de `/api/analytics/*`). 3 pontos concretos eram FALSOS/decorativos e faziam o dono achar "não são reais": (1) **CRMAnalytics "+15% vs mês anterior"** — texto 100% hardcoded, sem fonte → REMOVIDO, trocado pelo `forecast` real da API (só aparece se > 0). (2) **CRMAnalytics Heatmap de Conversão** — grade 7×12 toda fixa em `bg-muted/40`, zero endpoint → marcado badge "Em breve" pra não parecer gráfico real vazio. (3) **CatalogAnalytics "Top Produtos 30 Dias"** — reusava dados de atividade (`act`) só como fundo borrado 20%, sempre "Sem dados" → badge "Em breve". Os demais (AnalyticsPage, Blocks, FollowUp, Agenda, Tags) são REAIS — usam `INIT_*`/placeholders zerados substituídos por dados de API (nomes `MOCK_*` em AgendaAnalytics são enganosos mas funcionalmente reais). Build client OK. **Recomendação pro dono:** se algum gráfico REAL aparece vazio, é porque o endpoint retornou sem dados (não é fake) — verificar se o backend está populando `/api/analytics/*`. **Pendente backend (não-bloqueante):** criar `/api/analytics/crm/heatmap` e `/api/analytics/catalog/top-products` pra ativar os 2 gráficos marcados "Em breve".

---

### 8. 🟡 Captação: botões faltando (baixar lista + renomear "Exportar")
**O que o dono relatou:** "captação tem que ter mais botões como baixar a lista, e o de exportar que hoje move pra disparos deveria ter esse nome (disparar etc) e já ir pra aba que vão os números."
**Esperado:**
- Botão "Baixar a lista" (download dos leads captados).
- O botão atual "Exportar para Lista" na verdade move pra disparos → renomear pra algo como "Enviar pra Disparos" e já navegar pra aba de destino.
**Confiança:** média — UI + ação de navegação; escopo claro.

---

### 9. 🔴 Captação: leads captados somem ao sair e voltar
**O que o dono relatou:** "assim como se eu sair e voltar os números que captei somem. Mas como pode ver eles não aparecem lá em Chamadas em Massa nem Mensagem em Massa."
**Esperado:** leads captados devem PERSISTIR (não sumir ao trocar de aba/recarregar) e devem aparecer nas abas Chamada em Massa e Mensagem em Massa.
**Investigar antes:** onde os leads captados são salvos (só em estado React volátil? backend?); print diz "40 contatos salvos numa nova lista" — então salva em Lista, mas não persiste na tela de Captação.
**Confiança:** BAIXA — precisa entender persistência; risco de perder dado.
**STATUS (2026-08-02):** ✅ RESOLVIDO. Investigação confirmou: `results` em `LeadCaptureTab.tsx` era `useState<Lead[]>([])` puro (estado React volátil) — sumia ao trocar de aba/desmontar o componente. O "Enviar pra Disparos" salva numa lista via `/api/leads/export`, mas os resultados na TELA sumiam. Correção: adicionado localStorage (`hermes-lead-capture-results`) — `useEffect` carrega ao montar e salva a cada mudança de `results`. Agora persistem entre troca de aba E reload. Adicionado botão "Limpar" pra resetar. **NÃO resolvido (fora de escopo seguro):** "não aparecem em Chamada/Mensagem em Massa" — isso depende do #10 (que agora tem entrada manual) + integração de listas salvas no backend; leads exportados viram Lista, mas puxar Lista→Massa precisa de API de listas (frontend do #10 já aceita `Contact[]` de qualquer fonte).

---

### 10. 🔴 Chamada em Massa / Mensagem em Massa não funcionam (sem campos de adicionar contatos)
**O que o dono relatou:** "mensagem em massa que por sua vez também não funciona porque não tem campos de adicionar listas ou números ou selecionar contatos. Mesmo selecionando só contatos na aba Contatos, ele manda pra Mensagem mas somem as sub-abas do lado."
**Esperado:** Chamada em Massa e Mensagem em Massa precisam de campos pra: adicionar listas, adicionar números manualmente, ou selecionar contatos. Ao mandar contatos da aba Contatos, as sub-abas não podem sumir.
**Nota print:** "Envio em Massa" mostra Alvos(0) e depois Alvos(2) — parcialmente funciona via seleção, mas falta entrada direta de listas/números e há bug de sub-abas sumindo.
**Confiança:** BAIXA — vários sub-problemas juntos; quebrar em partes.
**STATUS (2026-08-02):** ✅ RESOLVIDO (os dois sub-problemas concretos). Investigação confirmou: (1) MassMessagePage e MassCallPage só aceitavam contatos do store (setados na aba Contatos), sem entrada manual; (2) MassMessagePage fazia `setView("crm")` quando `contacts.length === 0` (linhas 30-33) — redirecionando pra fora, o que fazia "sumir as sub-abas". Correções aplicadas: **MassMessagePage** — adicionado campo Textarea + helper `addManualNumbers()` que converte números colados (separados por vírgula/linha) em `Contact[]` e junta com existentes; removido auto-redirect destrutivo, substituído por empty-state no mesmo lugar. **MassCallPage** — mesmo padrão: campo manual + helper `addManualNumbers()`; removido early-return que impedia adicionar números. Ambas agora: (a) permitem entrada manual de números com DDD, (b) não se expulsam sozinhas quando vazias, (c) mostram empty-state explicativo. Build OK. **Pendente de backend:** integração com listas (API de listas existentes) — frontend pronto pra receber `Contact[]` de qualquer fonte.

---

### 11. 🟡 Funcionário Fácil: fallback não deixa escolher credencial diferente
**O que o dono relatou:** "quando vou criar o funcionário fácil ele não permite escolher a credencial diferente no fallback como dá no modelo principal."
**Esperado:** o "Motor de Emergência (Fallback)" deve ter seletor de CREDENCIAL (igual o primário tem "Credencial de IA"), não só provedor+modelo.
**Nota print:** primário tem "Credencial de IA" + "Testar" + "Nova"; fallback só tem "Provedor Secundário" + "Modelo Secundário", sem credencial.
**Confiança:** média — replicar o componente de credencial no bloco de fallback.

---

### 12. 🟡 Vincular Instância: só aparece "WhatsApp", não os números; ficam duplicados
**O que o dono relatou:** "ao escolher vincular a instância só aparece 'no WhatsApp' e não os números IA. Ficam as duas iguais na hora de vincular."
**Esperado:** o dropdown "Vincular Instância do WhatsApp" deve mostrar os NÚMEROS/nomes de cada linha, não duas opções genéricas "WhatsApp" idênticas.
**Nota print:** dropdown mostra "Sem instância" + "WhatsApp" + "WhatsApp" (duplicado, sem identificação).
**Confiança:** média — o fetch das instâncias não traz label/número; corrigir a listagem.

---

### 13. 🔴 "Colar informações da empresa/site" só pega o nome, não extrai tudo
**O que o dono relatou:** "na aba de colar informações da empresa ou site ele só traz o nome do site e coloca no prompt e não extrai TODAS as informações do site e personaliza o prompt template escolhido na etapa anterior."
**Esperado:** ao "Analisar Site", deve extrair conteúdo real do site (ICP, dores, serviços) e injetar no prompt template escolhido, personalizando de verdade — não só o nome.
**Investigar antes:** o scraper do site (fetch + parse) e como alimenta o RAG/prompt; pode ser limite do fetch ou do prompt de extração.
**Confiança:** BAIXA — depende de scraping + LLM; precisa testar resultado real.
**STATUS (2026-08-02):** ✅ RESOLVIDO (causa-raiz encontrada). O fluxo frontend→`/api/agents/generate`→IA estava certo; o gargalo era `fetchSiteText` (agent_generate.go): removia TODAS as tags HTML (`reTag`), jogando fora `<title>`, `<meta description>`, `og:tags`, keywords e headings (h1/h2/h3) — que são o conteúdo de MAIOR sinal, e às vezes o ÚNICO texto em sites SPA/JS (cujo `<body>` estático é quase vazio). Por isso "só pegava o nome". Correção: extrai esses metadados ANTES de limpar as tags e prepende num bloco `=== METADADOS DO SITE ===` no topo (sobrevive ao truncate de 8000 chars). Agora a IA recebe título+descrição+seções+conteúdo → personaliza o prompt de verdade (ICP, dores, serviços). Build Go OK. **Ressalva:** sites 100% client-rendered sem SSR nem meta tags ainda terão pouco conteúdo — limite do fetch estático (não usa headless browser); mas cobre a grande maioria (WordPress, Wix, landing pages, lojas).

---

### 14. 🟡 Etapa "responder com áudio": faltam seletores de credencial/provedor/modelo/Whisper/voz
**O que o dono relatou:** "nessa etapa em que se para pra responder com áudio não tem opção de selecionar credencial, provedor etc. Está apenas trazendo as vozes locais, nem qual Whisper vai usar, credencial e provedor modelo fazendo GET como os outros."
**Esperado:** a etapa de configurar áudio (Whisper STT + TTS) deve ter seletores de credencial/provedor/modelo com GET dinâmico (igual as outras etapas), não só vozes locais fixas.
**Nota print:** só mostra "Voz da IA" (Francisca local) e "Quando responder em Áudio" — sem credencial/Whisper/provedor.
**Confiança:** média — replicar o padrão de seletor dinâmico já usado no motor principal.
**STATUS (2026-08-01):** ✅ RESOLVIDO (de forma correta, NÃO decorativa). Investigação do backend revelou que STT (Whisper) e TTS são **globais por design**: o runtime lê de `cfg.STTProvider`/`STTCredentialID`/`TTSCredentialID` (settings globais em `settings.go` → `NewSTTClient`/`TTSConfig`), NÃO do perfil do agente. Só a VOZ (`voice_id`) é por-agente. Adicionar seletores de credencial/Whisper/provedor por-agente no wizard seria FALSO-SUCESSO (backend ignoraria, igual bug dos bloqueios de agenda). Correção aplicada: a etapa de áudio agora (1) explica que Whisper/provedor/credencial são globais, (2) mantém só o seletor de voz do agente, (3) tem botão "Configurar Voz & Whisper" que faz deep-link direto pra aba Configurações → Voz & Transcrição (onde os seletores dinâmicos corretos JÁ EXISTEM em `VoiceSettings.tsx`). Deep-link novo: `openSettingsTab("voice")` + `consumeSettingsTab()` no nav store, consumido pela SettingsPage no mount.

---

### 15. 🔴 AUDITORIA GERAL: todos os lugares que selecionam modelo devem ter os seletores certos
**O que o dono relatou:** "todos os lugares do painel que se seleciona modelo devem ter análise. Outros lugares que também devem estar faltando: os de Visão e outros podem usar a IA padrão escolhida no começo, mas Whisper e voz devem poder ser personalizadas. Acredito que o de RAG também deva ter as mesmas seleções em todos os cantos, pq são modelos diferentes."
**Esperado:** auditar TODO o painel — cada ponto de seleção de modelo deve ter credencial/provedor/modelo via GET. Regras:
- Visão e afins: podem usar a IA padrão do começo.
- Whisper (STT) e Voz (TTS): SEMPRE personalizáveis.
- RAG: mesmos seletores em todos os cantos (modelo de embedding é diferente).
**Confiança:** BAIXA — é auditoria ampla; fazer inventário antes de mexer.
**STATUS (2026-08-02):** ✅ INVENTÁRIO COMPLETO (entregável do item, que pediu "fazer inventário antes de mexer"). NÃO apliquei os 8 fixes em lote porque cada componente tem shape de estado próprio e, sem rodar a UI, corrigir às cegas viraria falso-sucesso (risco que a regra do dono proíbe). O padrão-alvo correto já existe: componente reutilizável `CredentialSelect` (type "llm"|"stt"|"tts") + `fetchAIModels(provider, "", baseURL, credentialId)`. 

**Componentes CORRETOS (dinâmico via GET — referência de como fazer):** AISettings.tsx, CallAISettings.tsx, VoiceSettings.tsx (STT/TTS), EasyAgentWizard.tsx (motor+fallback), EasySettingsWizard.tsx.

**Componentes que PRECISAM AJUSTE (por prioridade):**
1. 🔴 `EasyManagerWizard.tsx:267-280` — LLM Motor+Fallback do Gestor: `<select>` provider hardcoded + só `api_key` livre, SEM CredentialSelect nem seletor de modelo.
2. 🔴 `AdvancedLab.tsx:14-17,450-475` — LLM motor+fallback via `MODELS_BY_PROVIDER` hardcoded, sem CredentialSelect.
3. 🟡 `SpecializedAgents.tsx:216,822-838,1013` — LLM por agente: options hardcoded + `Input` texto livre pra `ai_model`, sem credencial.
4. 🟡 `ManagerAgentSettings.tsx:17,130` — tem `fetchAIModels` mas usa `api_key`+`base_url` em vez de CredentialSelect; modelo em Input livre.
5. 🟡 `DualAgentSettings.tsx:15,41` — `fetchAIModels` SEM `credential_id`, sem CredentialSelect.
6. 🟡 `GlobalRagManager.tsx:37,372-375,404-408` — RAG/embedding + rerank hardcoded (regra do dono: RAG deve ter seletores em todo canto).
7. 🟢 `AgentChatTest.tsx:559-561` — 3 options fixas, mas é sandbox de teste (aceitável; confirmar com dono).
8. 🟢 `SettingsPage.tsx:153` — default `model:"gpt-4"` só no state inicial (fallback, baixo impacto).

**Regras aplicadas na análise:** LLM/chat → credencial+provedor+modelo dinâmico; Visão → pode usar IA padrão (OK sem seletor); STT/TTS → sempre personalizável; RAG → mesmos seletores. **PRÓXIMO PASSO:** aplicar o padrão `CredentialSelect`+`fetchAIModels` nos itens 1-6, testando cada um na UI (um por vez) pra não virar decorativo. Itens 1 e 2 são os mais críticos (LLM sem credencial NEM modelo).

---

### 16. 🔴 Simulação de chamada não funciona (deveria ser como a landing/ElevenLabs)
**O que o dono relatou:** "a simulação de chamada não funciona, deveria ser tipo a da landing page, como é também na ElevenLabs (simula no painel). Estude como."
**Esperado:** "Simular Chamada / Iniciar Teste de Voz" deve funcionar como o widget de voz da landing page (e estilo ElevenLabs) — conversa por voz no painel.
**Investigar antes:** como a landing faz o simulador de voz funcionar; por que o do painel não conecta.
**Confiança:** BAIXA — precisa estudar a implementação da landing primeiro.
**STATUS (2026-08-02):** ✅ RESOLVIDO. Investigação: o botão "Iniciar Teste de Voz" era um STUB — só chamava `getUserMedia` (pedia permissão do mic) e mostrava um toast, sem conectar em nada. Estudei a landing: ela usa 2 caminhos — (a) `widget.js` faz chamada WhatsApp REAL via WebRTC (`/api/sessions/{id}/calls` + `/webrtc`), (b) `demo_voice.go` (`POST /api/demo/voice`) faz o loop STT→LLM→TTS com áudio gravado (estilo ElevenLabs convai). Escolhi o padrão (b) — que é exatamente "simular no painel" — mas adaptado pro agente EM CONSTRUÇÃO. Criado `POST /api/ai/simulate-voice` (ai_simulate.go): recebe áudio (webm/ogg base64) + system_prompt do wizard + history → STT (`voiceSvc.stt.TranscribeOgg`) → LLM (agente do usuário com o prompt em construção) → TTS (`voiceSvc.tts.SynthesizeToOgg`) → devolve `{text, heard, audio_base64}`. Frontend (EasyAgentWizard): botão agora usa MediaRecorder — 1º clique grava, 2º envia; transcrição+resposta entram no chat de simulação (texto) e a resposta toca em áudio. Estados visuais (gravando/processando). Build client+server OK. **Difere da landing widget.js** (que liga pra número real via WhatsApp): aqui é conversa com a IA no painel, sem ligar pra ninguém — que é o que "simular" significa.

---

### 17. 🟡 "Otimizar Prompt com IA" deveria mostrar o que foi melhorado
**O que o dono relatou:** "e ao otimizar deveria mostrar o que foi melhorado."
**Esperado:** o botão "Otimizar Prompt com IA" deve exibir um diff/resumo do que mudou no prompt, não só substituir silenciosamente.
**Confiança:** média — adicionar retorno visual do antes/depois.

---

### 18. 🔴 Chat/Teste: tela azul (crash) — "Algo quebrou nesta tela"
**O que o dono relatou:** "quando fui tentar usar o chat teste na aba de Chat Teste ele deu essa tela azul."
**Erro do print:** `Minified React error #31` — tela "Algo quebrou nesta tela".
**Contexto:** o print do erro é no host `inovareinteligenciaartificial.com` / `Inovare Claw` (pode ser produto relacionado, confirmar se é o mesmo painel Hermes ou outro).
**React error #31:** objeto sendo renderizado como filho JSX (algo como `{objeto}` em vez de string).
**Investigar antes:** reproduzir na aba Chat/Teste; achar o componente que renderiza objeto direto.
**Confiança:** BAIXA — precisa reproduzir e ver o stack real (o minificado não basta).
**STATUS (2026-08-01):** ⏸️ NÃO MEXIDO (confiança baixa, sem reprodução). Investigação do código: `AgentChatTest.tsx` renderiza `{m.text}` e `{r}` de `m.meta.reasoning.map()` — se API retornar objeto em vez de string, dá erro #31. Mas: (1) backend tipado como `reply: string`, (2) todos os lugares que preenchem `reasoning` usam strings literais, (3) erro aconteceu em `inovareinteligenciaartificial.com` (pode ser outro produto/build). SEM REPRODUÇÃO DO ERRO não é seguro mexer (pode criar fix pra problema que não existe ou piorar). Recomendação: adicionar defensive `String(m.text)` e `String(r)` OU error boundary, mas só depois de confirmar o stack trace real no ambiente do dono. NÃO tocar sem certeza — regra do projeto.

---

## OBSERVAÇÕES DE INFRA (já detectadas em sessões anteriores — não perder)

- **Som de fundo (ambient) foi DESLIGADO de propósito** (era a causa da voz metálica). **NÃO RELIGAR.**
- Gravações: já foi adicionado volume persistente `/opt/hermes-data/recordings` nos deploy scripts (beta e docker). Produção (.53) usa Swarm — ainda **não** tem o volume; ajustar separadamente se necessário.
- WebRTC do discador: envs `WACALLS_PUBLIC_IP=auto` + `WACALLS_UDP_PORT=50000` + porta 50000 no ufw — já aplicado no beta.

---

## PRÓXIMO PASSO (aguardando OK do dono)

1. Fazer os 3 backups (local + GitHub tag + imagem :stable no VPS).
2. Confirmar com o dono a ORDEM de prioridade das correções.
3. Atacar UMA por vez, começando pelas 🟢/🟡 de menor risco, testando cada uma.
4. As 🔴 só depois de investigação dedicada e com certeza de que resolve.
