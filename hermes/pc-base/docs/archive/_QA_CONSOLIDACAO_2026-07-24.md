# QA Consolidação — Hermes Call painel (2026-07-24)

Mapa único de TODOS os bugs achados pela rodada de 18 auditores (11 por-aba + 7 transversais).
NÃO corrigir nada até todos os 18 voltarem. Correção em 1 lote só.

Legenda gravidade: 🔴 crítico (perda de dado / segurança / build) · 🟠 grave (feature fake que parece real) · 🟡 médio (mock rotulado / cosmético) · ⚪ menor.

---

## ✅ JÁ CORRIGIDOS (lote 1 — feito, aguardando deploy junto do lote maior)

Backend `go build ./cmd/server/` OK · Frontend `vite build` OK.

1. **Gestor Fácil sobrescrevia prompt real com default** — mismatch chave JSON `system_msg` vs `system_message`. Fix: `system_message` canônico em settingsapi.go (GET attendant+manager), types/settings.ts, DualAgentSettings.tsx, ManagerAgentSettings.tsx, SettingsPage.tsx default. Conserta tb. o save silenciosamente quebrado dos fronts avançados.
2. **Agenda: bloqueios decorativos** — blocked_days/blocked_dates salvavam mas nunca liam. Fix: `blockedReason()` em agenda_api.go checa dia-da-semana (PT, fuso America/Sao_Paulo) + data no POST, retorna 409. Cobre painel E agente de IA (mesmo mux via internalAPICall). Fail-open em erro de config.
3. **Filtros Avançados de Contatos = fachada** — sem state/onClick. Fix: score min/max + status de ligação (answered/interested/no-answer) ligados no useMemo real; "Salvar como Segmento" cria lista real (createContactList). Removidos selects sem lastro (data criação/origem — Contact não tem esses campos).
4. **Catch inventava dado fake** — FollowUpPage injetava régua fantasma "Recuperação de Carrinho" + fingia create/delete (backend EXISTE, comentário obsoleto); ProfilePage fingia WhatsApp conectado via setTimeout + nome/email reais hardcoded. Fix: fallbacks removidos, toast honesto no erro, defaults vazios + placeholders, role/nome carregados de /api/profile.
5. **"Testar voz TTS" exigia API key no Piper (local/grátis)** — VoiceSettings.tsx:187 só isentava edge-tts, esquecia piper. Fix: usa `isLocalTTS` (cobre edge-tts+piper). Backend /api/tts/test já não exige key — era trava só do front. Reportado pela dona (voz grátis da VPS).

---

## STATUS DOS AUDITORES

| # | Auditor | Status | Recebido |
|---|---|---|---|
| Dashboard | Visão Geral | ✅ | sim |
| Leads | CRM/Gestão de Leads | ✅ | sim |
| CriarFacil | Criar Fácil + Gestor Fácil | ✅ | sim |
| Funcionarios | Meus Funcionários + Lab | ✅ (parcial) | sim |
| Chat | Chat/Teste + Treinador + Base | ✅ | sim |
| Agenda | Agenda | ✅ | sim |
| Catalogo | Catálogo/Vitrine | ✅ | sim |
| Telefonia | Central de Telefonia | ✅ | sim |
| Config1 | Config parte 1 | ✅ | sim |
| Config2 | Config parte 2 | ✅ | sim |
| Rodape | rodapé + navegação global | ✅ | sim |
| T-A | Transversal Segurança | ✅ | sim |
| T-B | Transversal Fluxo de dados | ✅ | sim |
| T-C | Transversal Estados erro/vazio/loading | ✅ | sim |
| T-D | Transversal Responsividade | ✅ | sim |
| T-E | Transversal Features órfãs | ✅ | sim |
| T-F | Transversal Mock/hardcoded | ✅ | sim |
| T-G | Transversal Feedback/consistência | ✅ | sim |

---

## ACHADOS CONSOLIDADOS

### Dashboard / Visão Geral (DashboardPage.tsx)
- 🟡 `healthStatus` hardcoded `"ok"` — sem setter, dead code. Banner de alerta inalcançável.

### Meus Funcionários + Lab (parcial)
- 🟠 `MOCK_PERFORMANCE` renderizado (linha ~1423) → dados fake de performance.
- 🟠 `getSales(id)` em uso (linha ~1409) → vendas fake.

### Chat / Teste (AgentChatTest.tsx)
- ✅ Núcleo real: `handleSend` (POST /api/agents/{id}/test), juiz `evaluate`, `wargame`.
- 🟠 Botão "Stress Test (Carga)" — só toast, zero código.
- 🟠 "Configs (Funcionário Fácil)" → "Aplicar Parâmetros" só fecha dialog, não aplica (temperature/topP/freqPenalty nunca vão ao backend).
- 🟠 "Injetar Contexto" → "Injetar no Agente" só fecha e dá toast; JSON nunca enviado.
- 🟠 "Split Screen (A/B)" — só toggle visual, nenhuma variante.
- 🟠 Anexar imagem — injeta string no chat, arquivo nunca enviado.
- 🟠 Botão mic — cronômetro local, áudio nunca capturado/enviado.
- 🟠 Botão stop geração — não tem AbortController, request já foi.
- 🟠 Regerar resposta — corta histórico mas não chama backend.
- 🟡 Cenários crise (objeção/ameaça/competidor) — ataques hardcoded, não geração dinâmica.

### O Treinador (AgentTrainerPanel.tsx)
- ✅ Pipeline real ponta-a-ponta: estimate → jobs (criar/listar/cancelar) → prompts (listar/ver/ativar).
- 🟡 Diff linha-a-linha — placeholder, documentado "Em breve".
- 🟡 Auto-Corrigir Guardrails — `disabled`, documentado.
- 🟠 "Modo Fantasma/Shadow Mode" — só toast, sem rota backend.
- 🟠 "+ Novo agente": `createAgent` só envia name+system_prompt fixo ("Você é um assistente."); ignora inputs `chave` e `números`.

### Base de Conhecimento
- 🔴 `KnowledgeManagerTab` (view "knowledge" em App.tsx:134) é 100% fake — todo botão `disabled`, dados hardcoded ("142 páginas indexadas"), autor admite "prévia visual". **É o que o dono vê ao clicar "Base de Conhecimento" no menu.**
- 🟠 `GlobalRagManager` (o REAL, em SpecializedAgents.tsx:1566) mistura real+mock:
  - ✅ Real: upload (POST /api/rag/documents), delete, bases por funcionário (/api/rag/documents?agent_id=).
  - 🟠 Fake: "Bases Globais" (createNewDataset só state local, nunca salva; some ao recarregar), card base global injeta doc hardcoded.
  - 🟠 Morto: "Auditoria" (só toast), sliders chunk size/overlap (só state), "Salvar Parâmetros e Reindexar" (só toast), `mockChunks` editáveis (nunca persiste), "Copilot da Base" (sem handler), aba "Saúde" tabela hardcoded, toggle auto-tune.

### Central de Telefonia (TelephonyPage.tsx)
- ✅ Espinha real e verificada (200): discar, atender, rejeitar, encerrar, gravar, listar gravações/transcrições, parear linha, criar sessão, medidores áudio, player com ?apiKey=JWT.
- 🔴/🟠 `CallsPage.tsx:98-107` "Copiloto AI (Sussurro)" — 100% mock SEM rótulo "Em breve"; mostra sugestões fixas ("João", "objeção de preço") como se ouvisse em tempo real. **O mais enganoso** (parece ativo/funcional).
- 🟡 `TelephonyPage.tsx:152-190` "Copiloto (Modo Fantasma)" no Radar — mock, MAS honesto (badge "Em breve" + Switch disabled).
- 🟡 Handoff "Assumir" — `disabled` + "Em breve" (honesto).
- ⚪ Badge "Monitoramento Ativo" sempre verde estático. Texto promete "sentimento em tempo real" que não existe na UI.

### Responsividade (Transversal D)
- 🔴 `DialogContent` base sem `max-h-[90vh] overflow-y-auto` → 10+ modais estouram viewport <700px sem scroll (ProxyDialog, ChatwootDialog, AICredentialsSettings, APIKeysSettings, AgentChatTest, EasyAgentWizard...). Fix 1 linha resolve todos.
- 🟠 ContactsPage drawer perfil (linha ~514) sem overflow-y-auto interno — some conteúdo em 568px.
- 🟠 4+ FABs brigando por `bottom-6 right-6` (Delegar IA, InstallApp, ProfilePage Voice/Theme, InstallAppFloat, GlobalRagManager, AdminSummonCard) — sobreposição, FABs de baixo não-clicáveis.
- 🟡 2 alturas hardcoded (SplitPaneCRM `calc(100vh-220px)`, GlobalRagManager `h-[600px]`) cortam em viewport baixa.
- ✅ Sidebar já corrigida (bug do Rafael). 31 tabelas usam overflow-x-auto (boa higiene).

### Mock/hardcoded residual (Transversal F) — varredura completa client/src
**P1 — números falsos exibidos como métricas reais (remover ou ligar já):**
- 🔴 SpecializedAgents GamificationPanel — `getSales()`+`MOCK_PERFORMANCE` (receita/MVP/gráfico). [dup Funcionarios]
- 🔴 AgentOrchestratorFlow.tsx:640-672 — histórico "João Silva/Maria/Carlos" que se diz "produção".
- 🔴 TagsAndBlocks.tsx:113-129 — blocklist `5511999999999`/`tag:golpe` fixos. Ligar API blocklist.
- 🔴 SplitPaneCRM.tsx:164-178 — timeline "Há 15 min / IA Finalizou Ligação" fixos.
- 🟠 TelephonyPage.tsx:174-185 — transcrição/sugestão fake (esconder bloco enquanto "Em breve", não só disabled). [dup Telefonia]
- 🔴 GlobalRagManager — MOCK_DATASETS, mockChunks, tabela gaps fixa, handleSyncConnector chunks:145. [dup Chat]
- 🟠 AdvancedLab.tsx:627-629 — dropzone fabrica doc com chunks aleatórios.
**P2 — preview/simulação (marcar claro ou tornar real):**
- 🟠 KnowledgeManagerTab — tem banner "Em breve" MAS ainda renderiza 142 páginas/CNPJ/docs/site falsos. [dup Chat]
- 🟡 EasyAgentWizard.tsx:738-743 — "Gerar Rosto AI" pravatar aleatório.
- 🟡 AgentOrchestratorFlow.tsx:585-593,447 — simulador randomAgent + toast "(Mock)".
- 🟡 CampaignsPage.tsx:62-71 — curva de retenção sintética.
- 🟡 dropdowns transferência "Closer/Suporte" fixos (EasyManagerWizard, AgentOrchestratorFlow:466, SpecializedAgents:1234-1235) — popular com agent-profiles reais.
**P3 — cosmético:**
- ⚪ level1VoiceAgent default `"mock-1"` → `""`.
- ⚪ MOCK_AGENDA_DATA/MOCK_PEAK_DATA/SHOW_NO_SHOW_DATA + `value:1` das pizzas (mitigado por overlay "Sem dados").
- ✅ Limpos: catálogos estáticos (ARCHETYPES/vozes/modelos/planos), ChatPage, ListsPage (saneado), DashboardPage.

---

### Catálogo / Vitrine (WhatsAppExtractorTab, SubscriptionTab, catalog CRUD)
- ✅ Backend robusto e verificado: criar/listar/deletar produto, categorias, stock report, trash+restore, vitrine pública oculta cost/ai_pitch/max_discount/upsell_id (bom p/ margem/privacidade).
- 🔴 Vitrine pública ÓRFÃ ponta-a-ponta: backend serve /api/catalog/public mas NÃO existe página storefront no client (grep rota pública = 0). InstallAppFloat anuncia "Instalar Vitrine IA" que não abre nada. Dono cadastra produto mas não vê/compartilha a vitrine — propósito central não fecha.
- 🔴 Impossível editar produto ou repor estoque pela UI: só há dialog de CRIAR. PUT /products/{id} e POST /stock/adjust existem no backend, sem botão/tela. Errou preço → tem que excluir e recriar. Vendeu → estoque nunca baixa.
- 🟠 Soft-delete sem tela de lixeira/restaurar no front → produto excluído por engano vira invisível permanente.
- 🟠 `upsell_id` dado-fantasma: campo "Upsell Automático" salva mas nenhuma linha do backend lê (product_context.go nunca injeta upsell). IA nunca faz cross-sell.
- 🟠 3 add-ons de assinatura (Modelo Opus, Armazenamento, Links Asaas) são `<div>` sem onClick/backend — vendem função inexistente. "Modelo Opus" já é grátis em Credenciais.
- 🟡 Campo categoria: `fCategory` existe no state mas input não é renderizado no dialog → produto nasce sem categoria.
- 🟡 Cupom não "gruda": POST /api/billing/coupon retorna applied:true mas GET /api/billing seguinte volta pending (self-heal re-consulta Asaas e sobrescreve).
- ⚪ Backend pronto sem UI: Export CSV, Bulk-price, Reorder (Kanban sem drag), Gerador descrição IA, Scrape-import.

---

### Rodapé + navegação global (AppShell, Sidebar, CommandPalette, SetupWizard, Login/Register, Help, AuthGate)
- ✅ Confirmado fix Sidebar (lista `min-h-0 overflow-y-auto`, item "calls" rola em vez de cortar).
- 🟠 SetupWizard (onboarding) no mobile — não acha âncoras; popover driver.js aparece solto/centralizado sem destacar nada.
- 🟠 Linha de ações do rodapé pode estourar horizontal em modo expandido: até 5 ícones h-9 w-9 + botão colapsar; quando Reset aparece (superadmin + itens ocultos) fica no limite/quebra. Validar.
- 🟡 Grid 2x2 (Config/Nova Linha/Ajuda/Suporte) fica FORA da área de rolagem (Sidebar.tsx:207, após filler flex-1) — em telas ~600px altura pode espremer.
- 🟡 LoginScreen trial-expired chama setErr/onTrialExpired de dentro de `import().then` (LoginScreen.tsx:32-38) — padrão frágil.
- ⚪ Comentário CommandPalette.tsx:9 desatualizado (diz que "Delegar para IA" abre paleta; na verdade chama setChatOpen). Paleta só abre por Ctrl+K, nenhum botão visível.
- ⚪ Número suporte `wa.me/5591984698653` hardcoded em 2 lugares (Sidebar.tsx:219,235) + SubscriptionTab. Centralizar.

---

### Agenda (AgendaPage, AgendaSettings, AgendaAnalytics)
- ✅ Núcleo real e verificado (curl 200): criar/editar/status/excluir agendamento, conflito 409 (SlotTaken), busca, Kanban, métricas, aba Lista, analytics (volume 7d, distribuição horários — SQL real).
- 🔴 Bloqueios da Settings decorativos (FALSO-SUCESSO): `blocked_days` e `blocked_dates` salvam e mostram "bloqueado com sucesso!", mas NENHUM código de agendamento lê essas chaves (grep: só escrita). Dono acha que proibiu IA de agendar no Natal/domingo, e ela agenda. É a promessa central da aba.
- 🔴 Link público "/book/sua-empresa" QUEBRADO: slug fixo (nem é do usuário), copia com sucesso, mas não existe rota /book/ no front nem endpoint público de booking → 404.
- 🔴 Profissionais/Bloqueios/Waitlist sem UI (backend órfão): tabelas+store+rotas completas (agenda_professionals/blocks/waitlist), zero interface. Dialog não tem seletor de profissional → professional_id sempre vazio → SlotTaken degrada p/ "1 agendamento por horário global".
- 🟠 Editar agendamento: PUT existe no backend mas SEM UI de edição no AgendaPage (só criar/status/excluir). E o PUT não revalida SlotTaken (edita p/ horário ocupado sem 409).
- 🟠 Botão "Dossiê IA" (por card, AgendaPage.tsx:146) — `<Button>` sem onClick, morto.
- 🟡 Analytics "No-show" na verdade conta `cancelado` (comentário admite "não há no-show real") — dado real, rótulo enganoso.
- 🟡 Aba Calendário (AgendaPage.tsx:340) — placeholder honesto ("Novembro 2026" fixo, "em desenvolvimento"). "Sync Calendar" e "Conectar Google Calendar" disabled + "Em breve" (honestos).

---

### CRM / Gestão de Leads (CRMPage, ContactsPage, ListsPage, TagsPage, BlocksPage, WhatsAppExtractorTab)
- ✅ Reais e verificados (curl): board CRM, tags CRUD, listas, blocks CRUD básico, contatos.
- 🔴 Drawer "Filtros Avançados" de Contatos (ContactsPage.tsx:459-508) é fachada COMPLETA: campos (data/score/status/origem) sem state, "Aplicar Filtros" e "Salvar como Segmento Dinâmico" sem onClick. Monta filtro, clica, nada muda. Pior falso-sucesso (parece a feature mais poderosa).
- 🔴 Colunas fabricadas exibidas como reais: TagsPage "Audiência" sempre "0 leads" (hardcoded leads:0 linha 60), "Status Inteligência" sempre "Manual Apenas", KPI "Tags Ativas" repete total. BlocksPage categorias (Opt-out/Quarentena/Spam) inferidas por regex sobre texto livre (linha 48), "Tentativas Evitadas" sempre 0, "Origem" sempre "Manual". Dona decide segmentação sobre números que não existem.
- 🟠 "Marcar como Lido" no Garimpo (WhatsAppExtractorTab.tsx:237-241) — toast de sucesso mas só state local, sem servidor. Recarrega e volta "não lido".
- 🟠 Select "Duração" do bloqueio (BlocksPage.tsx:185) oferece "7/30 dias" mas handleAddBlock nunca envia o valor → todo bloqueio é permanente.
- 🟡 `TagsAndBlocks.tsx` 100% mock (inputs sem state, tags/blocklist fixas, 🗑 sem onClick) MAS parece órfão (não importado por CRMPage) — CONFIRMAR antes de descartar. [T-F já listou os mocks internos]
- ⚪ Botões enfeite (onclick-vazio): "Importar", "Chamar no WhatsApp"/"Mais opções" (Contatos); "Disparar Campanha WhatsApp"/"Opções" (Listas); "Ver leads"/"Editar" (Tags); buscas e filtro "Categoria" (Tags/Blocks).

---

### Estados erro/vazio/loading (Transversal C)
**Padrão sistêmico:** modo dominante `.catch(()=>{})` / `.catch(()=>setX([]))` → erro de servidor/rede vira "estado vazio", indistinguível de conta nova, sem toast.error. Pior variante: catch cai em MOCK/fake (usuário vê dado inventado quando API dá 500/rede cai).
**TOP 5 piores:**
- 🔴 FollowUpPage.tsx:46-58 — O PIOR. Falha de API/rede INJETA sequência inventada ("Recuperação de Carrinho", 2 etapas). Dono acredita ter régua de follow-up que não existe no backend. Create/Delete também simulam sucesso no catch (l.85-88,98-100) — muda tela sem persistir.
- 🔴 SpecializedAgents GamificationPanel:1359-1374 — ranking/gráfico fabricados do hash hex do ID (`parseInt(id.slice(0,4),16)*1.5+1200`). Faturamento falso como métrica real. [dup Funcionarios/T-F]
- 🔴 ProfilePage.tsx:44-48 — no erro de /api/whatsapp/status um setTimeout FINGE número conectado ("+55 (11) 99999-9999 Auto-Detectado: Conectado"). Dono pensa que linha está pareada quando pode estar caída. + nome/email hardcoded ("Emerson", "1234@1234").
- 🟠 CallsPage.tsx:100-107 — Copiloto Sussurro fixo. [dup Telefonia]
- 🟠 SecurityPage.tsx:16-20 — 3 `.catch(()=>{})` deixam abas Horário Comercial/Rate Limit em branco (gated por `schedule &&`). DashboardPage.tsx:149,162 — se fetchDashboard falha, data=null → skeleton pulsando pra sempre sem toast.
**Modelos certos (referência):** CRMPage, RecordingsPage, TranscriptsPage, CollectedDataTab, CampaignsPage usam toast.error; TeamPage/GlobalAIErrorBanner não inventam dado; AICredentialsSettings comenta "se API falhar NÃO inventa erro de credencial".
**Fix de fundo:** (a) matar os 4 fallbacks p/ mock (itens 1-4); (b) padronizar catch com toast + estado `error` separado de `empty`; (c) tratar não-401 (500/rede) no lib/api.ts.
- 🟠 SecuritySettings.tsx:40-42 — 3 catch vazios → sessões/IP/audit vazios sem aviso.
- 🟠 EasySettingsWizard.tsx:144,174,225 — catch vazio + saves parciais `.catch(()=>{})` → progresso do wizard pode se perder mudo.

---

### Criar Funcionário Fácil + Criar Gestor Fácil (EasyAgentWizard, EasyManagerWizard, EasySettingsWizard)
- ✅ Boa notícia: arquitetura base do Funcionário Fácil grava (perfil criado/editado/apagado via curl em prod ok). Modelo/baseURL preservados via savedModel/savedBaseURL.
- 🔴 Gestor Fácil DESCARTA ~30 campos avançados: PUT /api/settings/manager só aceita 6 campos (AgentConfig). Handler rico (handlePutManagerWizard, bloco manager_wizard) está `+build ignore`, rota GET /api/easy-manager/wizard → 404 em prod. OpenClaw, memória perpétua, delegação, alertas, modo sombra, swarm, osControl etc. jogados fora silenciosamente.
- 🔴 Gestor Fácil não carrega prompt atual (mismatch de chave JSON): wizard lê `m.system_message`, backend devolve `system_msg`. Ao reabrir, prompt real some e mostra default — se salvar, SOBRESCREVE o prompt real com default. Fix trivial (1 linha), hoje é perda de dados.
- 🔴 Funcionário Fácil descarta Handoff top-level (Etapa 6): escalation_keywords, handoff_message, handoff_method(top), handoff_agent, handoff_notify, messageVoice, destAgent2, askForHelp vão como campos raiz mas agentSaveBody (agents_adapter.go:81-100) não os lê → viram "". Confirmado por curl. Só sobrevive subconjunto em `extras`. Tela promete "transbordo por palavra-chave" que não grava nas colunas dedicadas.
- 🟡 Fake/cosmético: Chat de Simulação, "Simular Cliente Grosseiro", "Teste de Voz" (Etapa 8) 100% falsos; "Gerar Rosto AI"/upload avatar não persistem; state.tools (Superpoderes) nunca populado ("0 ativos" sempre); validação de etapas desativada (`return true`) → permite publicar agente vazio.

---

### Feedback e consistência (Transversal G) — 2º lote
Base madura: lib/api.ts lança erro em !r.ok, quase todo mutation tem try/catch+toast.error. Problemas reais = UI fake exibida como real + deletes sem confirm + terminologia tripla.
- 🔴 Roteamento Nível 1 NÃO persiste (SpecializedAgents.tsx:74-75,418-444): level1VoiceAgent/level1TextAgent começam em "mock-1"/"mock-3", onChange só faz setState, SEM apiPost/apiPut e sem botão salvar. Dono escolhe quem atende ligação/texto, troca de tela, escolha some sem aviso. Config central.
- 🟠 GlobalRagManager meio-fake: handleSyncConnector (129-133) só toast + linha fake chunks:145, sem API; mockChunks (54-58,271-288) editáveis em useState local que nunca vai ao backend. Dono acha que treinou a IA e não treinou. [dup T-F item 6]
- 🟠 RecordingsPage.tsx:44-52 excluir gravação SEM confirm — destrutivo/irreversível, 1 clique.
- 🟠 WorkspaceSettings.tsx:69-77 remover workspace SEM confirm — apaga projeto inteiro, alto blast radius.
- 🟡 Deletes sem confirm inconsistentes: TagsPage:79-87, BlocksPage:72-80 (desbloquear), GlobalRagManager/AgentRagPanel (doc RAG). Padrão bom (JÁ confirmam): Agenda/Catalog/CRM/Contacts/Lists/Transcripts/FollowUp/Campaigns/Cost/AICredentials/APIKeys/Promises.
- 🟡 SpecializedAgents.tsx:225-228 catch vaza texto de debug "(Pode estar mockado)" pro usuário.
- 🟡 Terminologia tripla Funcionário/Agente/Bot (Sidebar vs SpecializedAgents vs AgentTrainerPanel) — confunde leigo.
- 🟡 BlocksPage:224-256 blocklist sem estado vazio ("Nenhum contato bloqueado").
- ⚪ Botões sem onClick: GlobalRagManager "Ver Grafo 3D"/"Novo Chunk Manual" (265-266). AgentChatSettings.tsx:51 diz "Settings→" (menu é "Configurações"). Login Google "Em breve" (honesto).
- ✅ Falsos positivos investigados e OK: toast.success em catch de EasySettingsWizard:318 (avisa modo básico) e CampaignsPage:319 (reporta ok/total reais) — honestos.

---

### Config parte 1 (Cérebro/Agente Avançado, Credenciais IA, Modelos/LLM) — 2º lote
- 🔴 4 switches "Superpoderes" do Gestor são FANTASMAS (ManagerAgentSettings.tsx:224-272): askManagerEnabled/shadowingEnabled/copilotEnabled/promisesEnabled gravados via `(cfg as any)` mas AgentConfig Go (store.go:162-169) não tem esses campos → json.Decode descarta. Toast "Salvo" mente, some no reload. Sem consumo backend (promises_cron.go está +build ignore). 4 features anunciadas ("Ponto Eletrônico", "RAG Reverso", "Copiloto", "Cobrador de Promessas") que não fazem nada.
- 🟠 Status de credencial SEMPRE "Conectado" (AICredentialsSettings.tsx:276-303): infra existe (credential_failures, RecordFailure) mas RecordFailure NUNCA é invocado em nenhum call site LLM/STT/TTS. failsThisWeek sempre 0, chave estourada/sem saldo aparece verde. Falso-positivo de saúde — dono no escuro quando IA para por chave inválida.
- 🟡 "Listar modelos" quebra com credencial vinculada (AISettings.tsx:78 vs aimodels.ts:5): passa credential_id como 4º arg pra fetchAIModels que só aceita 3 → ignorado, request vai com api_key vazio → erro. Só funciona com chave manual digitada. GET /api/ai/models não resolve credential_id.
- ✅ Honestos (avisam "em desenvolvimento"): Ferramentas do Agente, Fallback em Cascata, Roteador Semântico. Funcionam ponta a ponta: OpenClaw/Orquestração, Circuit Breaker Financeiro (budget real).

---

### Config parte 2 (Webhook/n8n, Workspace, Aparência, Schedule, API Keys) — 2º lote
- 🟠 N8nSettings integração é FACHADA: URL+token salvam/persistem (n8n_api.go:44), monitor mostra "Endpoint Configurado", mas NENHUM código consome. s.n8n.Get só é lido dentro do próprio /api/n8n. Sem forward de eventos, sem uso do token. Card promete "enviar e receber eventos" — não cumpre.
- 🟠 WebhookSettings seletor de Tópicos/Eventos decorativo: 12 botões de evento (toggleEvent WebhookSettings.tsx:67) salvam cfg.events[], mas sendNotification (webhook.go:61) NUNCA filtra por evento — dispara tudo sempre. Webhook.Events só ecoado no GET. Usuário acha que assina alguns tópicos, recebe todos.
- 🟡 ScheduleSettings save não invalida cache (features_api.go:773): SaveSchedule sem s.invalidateUserSettings. LoadUserSettings tem TTL 5min. "Horário salvo" na hora, mas enforcement (IsWithinSchedule) usa horário antigo por até 5min. Config sensível (bloqueio fora de horário).
- 🟡 AppearanceSettings cores (brandColor/bgColor) só no localStorage, nada reaplica no boot (só theme em theme.ts). Refresh/outro device perde customização.
- ✅ Corretos: Schedule (enforcement real 6 pontos), API Keys (validadas no middleware, last_used real), Workspace (CRUD real, "Em breve" honestos), Webhook Retry/DLQ (WebhookQueue real). Nenhum 🔴 na área.

---

### Fluxo de dados entre telas (Transversal B) — 2º lote
Raiz-causa recorrente: struct DUPLICADO — um em cmd/server/*.go (tags erradas) e outro em internal/settings/store.go (tags certas usadas no GET). Divergência = perda de dado no save.
- 🔴 Rate Limit quebrado bidirecional (features_api.go:848-862): GET devolve chaves que o front não lê (tela sempre zerada) + PUT descarta cooldown_message e remapeia semântica dos outros 2 campos. Perde dado E exibe errado nas duas direções. Mesma família do system_msg.
- 🔴 Salvar gatilho de agente APAGA o perfil inteiro (SpecializedAgents.tsx:112 + agentprofiles.go:282): mudar gatilho zera voz, áudios pré-gravados, background noise e os 30 campos extras. Fix idêntico ao já aplicado em persistModel (espalhar ...agent).
- 🔴 IP Whitelist perde os IPs no save (ipwhitelist.go:13 `allowed_ips` vs front `ips`): perde dado + segurança (salvar enabled=true com lista vazia pode bloquear acesso legítimo). GET mascarado esconde até recarregar.
- ⚪ Agent Chat outbound_only (settings.ts:74-83 não tem o campo): backend tem OutboundOnly, front manda objeto sem ele → Go zera pra false. Sem UI; se ligado por outra via, próximo save apaga.
- ✅ SEM problema (batem): Agenda, Catálogo, CRM stages/move (mesma tabela contact_leads, consistente), Follow-up, Broadcast/campanha A/B+paced, Campaign-defaults, Scheduled calls, Orchestration, Tags/Notes/Leads, Settings AI/Voice/CallAI/Manager (system_message já corrigido), create-group.

---

### Segurança e permissões (Transversal A) — 2º lote
- 🔴 Destruição/hijack de sessão CROSS-TENANT (httpapi.go:744-783 → sessionmanager.go:224,250,267,286): Delete/Logout/Pair/PairCode NÃO usam sessionByID (que valida sess.userID==u.ID), passam sid cru pro manager. Tenant A com sid de B faz DELETE /api/sessions/{sid-B} e apaga/derruba o WhatsApp alheio ANTES de qualquer filtro. Fix: usar s.sessionByID(w,r,sid) e operar sobre sess.
- 🟠 Chave ElevenLabs do admin exposta a qualquer tenant (credentials_api.go:46-62, server.go:271-283): handleElevenKeys chama List(ctx) sem u.ID, manager fixado em admin.ID. Qualquer logado faz GET /api/settings/eleven/keys e vê inventário (nome, mascarada, crédito, reset). Fix: exigir u.IsAdmin ou manager per-tenant.
- 🟠 Roles/permissões 100% client-side (navigation.ts:21,40,52): userRole/isEmployeeEditMode no zustand+localStorage, default "admin", sem enforcement no backend. "Funcionário" edita localStorage ou chama API direto → abas escondidas não são barradas. Único gate server-side é planAllowsTab (por plano, não por role). Fix: persistir role no auth.User + checar no middleware.
- 🟡 Webhooks Asaas auth OPCIONAL (billing_api.go:201-205, agenda_api.go:403-407): valida token só se HERMES_ASAAS_WEBHOOK_TOKEN setado; env vazia = aceita qualquer POST (ativa assinatura sem pagar). Verificar env no deploy.
- ⚪ Erro SQL cru vazado em rota pública (catalog_api.go:441-444): PublicCatalog devolve erro Postgres direto (SQLSTATE, tipo de coluna). ⚪ CORS * (httpapi.go:601) — baixo risco (auth por header, não cookie).
- ✅ Correto: withUserAuth sem bypass (leak antigo WACALLS_API_KEY removido), sessionByID isola certo, agenda/recordings/credentials/contatos/followup/send* filtram por u.ID, credenciais mascaradas, prod 401 sem token, sem chaves logadas.

---

### Features órfãs (Transversal E) — 2º lote
- 🔴 UI SEM BACKEND: POST /api/whatsapp/sync-app-state (WhatsAppExtractorTab.tsx:174) — botão "Sincronizar" + auto-sync ao abrir Garimpo chamam rota que NÃO existe no Go (só há instances/chats/status). Cada clique = 404, mas mostra toast de sucesso e recarrega. Falso-sucesso.
- 🟡 Tabela órfã contact_custom_fields (contact_extras.go:75): lida em handoff_smart.go:255 (GetFields) mas o escritor SetField (309) nunca é chamado. "Campos personalizados coletados pela IA" morto na origem, sempre vazio.
**TOP 5 features prontas mas INACESSÍVEIS (backend completo, falta UI):**
1. 🔴 Cadenciador de Follow-up multi-etapa — 7 tabelas + scheduler 24/7 (main.go:87), sem tela pra criar campanha. followup_api.go. [NOTA: FollowUpPage existe e chama /followup/sequences — verificar se cobre; auditor pode ter olhado versão antiga]
2. 🔴 Agenda: Profissionais+Bloqueios+Waitlist — CRUD completo (httpapi.go:305-313), só falta tela. [dup Agenda]
3. 🟠 Catálogo completo (estoque/imagens/IA/import scraping) — UI atual é casca (httpapi.go:321-340).
4. 🟡 Pausar IA por conversa (handoff humano) — integrado em autoreply.go:314, falta botão "assumir". httpapi.go:377-379.
5. 🟡 Deal/Win-Loss CRM — PUT /contacts/{jid}/deal grava valor/motivo que alimentam gráficos que JÁ existem em CRMAnalytics.tsx mas nunca recebem dado. httpapi.go:519.
- ✅ NÃO são órfãs (têm consumidor via cron/webhook/telegram/landing/API externa): auth/google*, demo/clip+voice, agent/call|hangup|status, sessions/*/webhook, campaigns/{id}/results, conversations, logs, rag/ingest-conversations.

---

## ✅ TODOS OS 18 AUDITORES COMPLETOS (11 por-aba + 7 transversais). Mapa fechado 2026-07-24 22:55.

## PLANO DE CORREÇÃO — 2º LOTE (a corrigir de manhã; 1º lote de 5 fixes já está em beta)
**🔴 Críticos (perda de dado / segurança):**
1. Hijack sessão cross-tenant (httpapi.go:744-783) — SEGURANÇA, topo da lista.
2. Rate Limit quebrado bidirecional (features_api.go:848-862).
3. Salvar gatilho apaga perfil inteiro (SpecializedAgents.tsx:112 + agentprofiles.go:282).
4. IP Whitelist perde IPs no save (ipwhitelist.go:13).
5. 4 superpoderes do Gestor fantasma (ManagerAgentSettings.tsx:224-272).
6. Roteamento Nível 1 não persiste (SpecializedAgents.tsx:74-75,418-444).
7. sync-app-state 404 falso-sucesso (WhatsAppExtractorTab.tsx:174).
**🟠 Graves (fachada/falso-sucesso):**
8. n8n fachada, Webhook eventos ignorados, status credencial sempre verde, RAG global mock, ElevenLabs admin exposto, roles client-side.
9. Deletes sem confirm (Recordings/Workspace).
**🟡/⚪:** Schedule cache 5min, cores no refresh, terminologia tripla, catch vaza "(mockado)", erro SQL cru público, CORS.
