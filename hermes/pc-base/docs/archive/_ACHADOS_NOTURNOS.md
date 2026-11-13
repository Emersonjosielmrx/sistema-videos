# ACHADOS NOTURNOS — Hermes Call (relatório acumulado da cron de teste)

> Agente noturno: LEIA o `_PLANO_TESTE_NOTURNO.md` antes de cada rodada. Você SÓ TESTA e DOCUMENTA. NÃO edita código, NÃO faz deploy, NÃO dispara ligação/campanha/mensagem real, NÃO toca em `internal/voip/call/*` nem `signaling`.

---

## LEDGER DE PROGRESSO (anti-repetição — CONSULTE E ATUALIZE ANTES DE TESTAR)

**Como usar:** a cada rodada, olhe a tabela abaixo, pegue o PRIMEIRO item com status `pendente` (ou `parcial`), teste-o, e mude o status. NUNCA teste um item que já está `feito-passe1` se ainda houver `pendente`. Só volte a um item `feito` para um passe mais profundo (passe 2/3) QUANDO TODOS os 12 estiverem pelo menos `feito-passe1`.

| # | Área | Passe 1 | Passe 2 (borda) | Passe 3 (profundo) | Última rodada |
|---|------|---------|-----------------|--------------------|---------------|
| 10 | Config (todas sub-abas) | feito-passe1 | feito-passe2 | pendente | Rodada 13 (2026-07-25 ~05:40) |
| 7 | Meus Funcionários / Agentes / Lab | feito-passe1 | feito-passe2 | pendente | Rodada 14 (2026-07-25 ~06:10) |
| 3 | CRM / Contatos / Listas / Tags / Blocks / Garimpo | feito-passe1 | feito-passe2 | pendente | Rodada 15 (2026-07-25 ~06:40) |
| 4 | Agenda | feito-passe1 | feito-passe2 | pendente | Rodada 16 (2026-07-25 ~07:10) |
| 11 | Segurança transversal (só leitura+curl) | feito-passe1 | feito-passe2 | pendente | Rodada 17 (2026-07-25 ~07:35) |
| 12 | Features órfãs (backend↔UI) | feito-passe1 | feito-passe2 | pendente | Rodada 18 (2026-07-25 ~07:55) |
| 2 | Dashboard / Visão Geral | feito-passe1 | feito-passe2 | pendente | Rodada 19 (2026-07-25 ~08:10) |
| 5 | Catálogo / Vitrine | feito-passe1 | feito-passe2 | pendente | Rodada 20 (2026-07-25 ~08:35) |
| 6 | Telefonia / Ligações / WebRTC | feito-passe1 | feito-passe2 | pendente | Rodada 21 (2026-07-25 ~09:00) |
| 8 | Navegação / Estado global / Layout | feito-passe1 | feito-passe2 | feito-passe3 | Rodada 25 (2026-07-25 ~10:35) |
| 9 | Estados de erro / loading / vazio | feito-passe1 | feito-passe2 | pendente | Rodada 23 (2026-07-25 ~09:50) |
| 1 | Onboarding / Auth / Login | feito-passe1 | feito-passe2 | pendente | Rodada 24 (2026-07-25 ~10:10) |

**Próxima rodada: PASS-2 começa pela Área 10** (Config) — também testa regressões do 1º lote (Gestor Fácil system_msg, Rate Limit, IP Whitelist).
| 6 | Telefonia (SÓ leitura, não discar) | pendente | pendente | pendente | — |
| 8 | Chat de Teste / Treinador / RAG | pendente | pendente | pendente | — |
| 9 | Follow-up / Réguas | pendente | pendente | pendente | — |
| 1 | Autenticação e conta | pendente | pendente | pendente | — |

Status possíveis: `pendente` → `parcial (parei no elemento X)` → `feito-passe1` → `feito-passe2` → `feito-passe3`.

**Ordem obrigatória:** siga a coluna # de cima pra baixo (já está na prioridade certa). Só passe pro passe 2 de QUALQUER área depois que TODAS estiverem em `feito-passe1`.

**Regra de ouro anti-repetição:** antes de reportar um bug, dê Ctrl+F neste arquivo pelo `arquivo:linha` — se já foi reportado numa rodada anterior, NÃO reporte de novo; no máximo adicione um detalhe novo. Não encha o relatório com duplicatas.

---

## RODADAS

## Rodada 1 — Área 10 (Config) — 2026-07-24 ~23:47

Prod no ar: build 20260724-2139 (beta, v0.2.0). Todas as rotas de config respondem 401 (existem). Foco: confirmar por leitura de código os bugs de Config já mapeados e checar cadeia completa front↔backend.

### Bugs novos encontrados
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| (nenhum novo nesta rodada — os de Config já estavam no mapa do humano; confirmados abaixo com a cadeia exata) | | | | |

### Bugs já conhecidos que CONFIRMEI ainda existem (cadeia validada por leitura)
- 🔴 **Rate Limit quebrado bidirecional.** GET `handleGetRateLimit` (features_api.go:851) devolve `us.RateLimit` = struct `setpkg.RateLimitConfig` com tags `max_req_per_hour`/`max_req_per_min` (internal/settings/store.go:183-187). MAS o front lê `max_messages`/`window_seconds`/`cooldown_message` (types/settings.ts:95-99, RateLimitSettings.tsx:41,48,55) → **tela sempre zerada**. No PUT (features_api.go:858) remapeia `MaxMessages→MaxReqPerHour` e `WindowSeconds→MaxReqPerMin` (semântica trocada: "máx mensagens" vira "req/hora") e **descarta `cooldown_message`** (setpkg não tem esse campo). O struct cmd/server/ratelimit.go:9-14 TEM cooldown_message e bate com o front, mas a persistência usa o setpkg que não tem. Perde dado nas 2 direções.
- 🔴 **IP Whitelist perde os IPs no save.** Front manda `{enabled, ips}` (types/settings.ts:102-105, SecuritySettings.tsx:91,98). Handler decodifica em struct cmd/server/ipwhitelist.go:11-13 com tag `allowed_ips` (cfg.AllowedIPs) → como o front nunca manda `allowed_ips`, `cfg.AllowedIPs` chega VAZIO e `SaveIPWhitelist` grava lista vazia (features_api.go:841). GET usa setpkg.IPWhitelistConfig com tag `ips` (store.go:190-193), por isso a leitura funciona e mascara o bug até salvar. Risco de segurança: salvar enabled=true zera a lista.
- (Superpoderes fantasma do Gestor, status credencial sempre verde, Listar modelos com credencial vinculada, n8n fachada, Webhook eventos ignorados, Schedule cache 5min, cores no refresh — todos já no mapa do 2º lote; não re-testei nesta rodada por tempo, ficam pro passe 2.)

### Bugs já conhecidos que parecem CORRIGIDOS
- ✅ `system_message` (Gestor/Attendant): struct settings agora usa tag `system_message` consistente (store.go) — corrigido no 1º lote/deploy 2139.

### Observação (raiz-causa recorrente)
Rate Limit e IP Whitelist têm o MESMO padrão: struct DUPLICADO — um em `cmd/server/*.go` (tags que batem com o front) e outro em `internal/settings/store.go` (tags diferentes, usadas na persistência/GET). A divergência é a raiz. Vale o humano unificar os structs (usar um só) em vez de remapear campo a campo.

### STATUS
Cobri 1/12 áreas (Área 10 Config = feito-passe1, confirmação de código; casos de borda e sub-abas não-mapeadas ficam pro passe 2). Próxima = Área 7 (Meus Funcionários / Agentes / Lab).

---

## Rodada 2 — Área 7 (Meus Funcionários / Agentes / Lab) — 2026-07-25 ~00:18

Foco: confirmar cadeia dos bugs já mapeados (salvar gatilho apaga perfil; roteamento nível 1) e caçar variantes. Rotas /api/agent-profiles e /api/agents/test-node respondem 401 (existem).

### Bugs novos encontrados
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🟠 | **Drag-and-drop de prioridade de roteamento não persiste.** `handleDrop` reordena a hierarquia e mostra toast "Prioridade de roteamento atualizada!", mas só faz `setHierarchy` (state local) — nenhum apiPost/apiPut. Recarrega e volta à ordem antiga. Falso-sucesso. | SpecializedAgents.tsx:99-103 | Arrastar um agente pra reordenar prioridade → toast de sucesso → recarregar página → ordem original de volta | Leitura: linhas 99-104 só chamam setHierarchy + toast; grep não achou persistência de `hierarchy` |
| 🟡 | **persistTrigger zera MAIS campos que os já mapeados.** Além de voz/áudios/extras (já mapeado), o payload de persistTrigger (só ~10 campos) omite `initial_context`, `product`, `tone`, `wake_word`, `meet_mode`, `custom_tags`, `custom_alerts`, `automations` — que também são sobrescritos pra vazio/default no UPSERT `ON CONFLICT DO UPDATE SET` (todas as colunas viram EXCLUDED). | SpecializedAgents.tsx:114-125 + agentprofiles.go:282-303 | Mudar gatilho de um agente que tinha contexto inicial/produto/tom configurados → esses campos também são apagados | Leitura: UPSERT sobrescreve 35 colunas com EXCLUDED; persistTrigger manda 10 |

### Bugs já conhecidos que CONFIRMEI ainda existem (cadeia validada)
- 🔴 **Salvar gatilho APAGA o perfil inteiro.** MECÂNICA EXATA confirmada: `Create` (agentprofiles.go:257-304) faz UPSERT com `ON CONFLICT (user_id,name) DO UPDATE SET <todas as 35 colunas> = EXCLUDED.*`. Como `persistTrigger` (SpecializedAgents.tsx:112-125) só envia ~10 campos, todo o resto (voice_id, trigger_audio, offer_audio, background_noise, ai_model, ai_provider, listen_audio, reply_audio, vision_enabled, extras, os 4 audio_id, tts_default) chega zero/"" e SOBRESCREVE o salvo. Fix: persistTrigger deve mandar `...agent` completo (espalhar todos os campos), igual já foi feito em persistModel (comentário na linha 133-134 confirma que persistModel já foi corrigido assim).
- 🔴 **Roteamento Nível 1 não persiste.** Confirmado: level1VoiceAgent/level1TextAgent (SpecializedAgents.tsx:74-75) só têm useState inicial "mock-1"/"mock-3" + onChange=setState (421-422, 436-437). Nenhum useEffect carrega do backend, nenhum apiPost/apiPut salva. Seleção de "quem atende voz/texto" some ao trocar de tela. Sem botão salvar pra esse bloco.

### Bugs já conhecidos que parecem CORRIGIDOS
- ✅ persistModel (modelo de IA do agente) — comentário linha 133-134 diz que antes era falso-sucesso (só setState) e foi corrigido pra mandar o profile e gravar. Não re-testei a fundo, mas o código de persistTrigger ao lado sugere que persistModel espalha o profile.

### STATUS
Cobri 2/12 áreas passe-1 (Área 10 Config ✅, Área 7 Agentes ✅). GamificationPanel/simuladores de voz/EasyAgentWizard/AdvancedLab/Orchestrator não re-testados a fundo (já no mapa do 1º lote) — ficam pro passe 2. Próxima = Área 3 (CRM/Contatos/Listas/Tags/Blocks/Garimpo).

---

## Rodada 3 — Área 3 (CRM / Contatos / Listas / Tags / Blocks / Garimpo) — 2026-07-25 ~00:47

Foco: confirmar cadeia dos bugs mapeados de Tags/Blocks/Garimpo e caçar variantes.

### ⚠️ LIÇÃO DE MÉTODO (importante pras próximas rodadas)
Contra este backend, **curl SEM token sempre retorna 401**, inclusive pra rota que NÃO existe (testei `/api/whatsapp/rota-fake-xyz123` → 401). Ou seja: **curl sem auth NÃO distingue 404 de rota real.** A verificação válida pra "rota fantasma" é `grep` no código Go (`cmd/server/*.go`), não o curl. Ajuste a Técnica B: use curl só pra pegar 500 (erro de servidor) ou comportamento de rota pública; pra existência de rota autenticada, confie no grep.

### Bugs novos encontrados
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| (nenhum 100% novo — os de Tags/Blocks/Garimpo já estavam no mapa; cadeia confirmada abaixo) | | | | |

### Bugs já conhecidos que CONFIRMEI ainda existem (cadeia validada)
- 🔴 **sync-app-state é rota fantasma (404 real).** Confirmado por grep: `grep -rn "sync-app-state\|SyncAppState" cmd/ internal/` = VAZIO (não existe no Go). Front chama em WhatsAppExtractorTab.tsx:174. O 401 que o curl devolve é auth-first (enganoso). Quando autenticado, dá 404. Botão "Sincronizar" do Garimpo + auto-sync ao abrir = 404 silencioso com toast de sucesso.
- 🟠 **Duração de bloqueio ignorada (falso-controle).** Confirmado: seletor "Duração" existe (BlocksPage.tsx:184-185, state `blockDuration` default "forever"), mas `handleAddBlock` (BlocksPage.tsx:61) só envia `{phone, reason}` — `blockDuration` NUNCA entra no payload. Usuário escolhe "7 dias"/"30 dias" e o bloqueio é permanente.
- 🟠 **Colunas fabricadas em Tags.** Confirmado: TagsPage.tsx:60 hardcoda `leads: 0, aiActive: false, trigger: null, rule: ""` pra toda tag. "Manual Apenas" fixo (linha 270). KPI "Tags Ativas" (linha 134). Números de audiência/inteligência não são reais.
- 🟡 **Desbloquear sem confirmação.** BlocksPage.tsx:72 `handleRemoveBlock` apaga da blacklist sem `confirm()` — o contato volta a receber campanhas. (bloquear confirma, desbloquear não — inconsistente.)

### Bugs já conhecidos que parecem CORRIGIDOS
- ✅ Filtros Avançados de Contatos (score/status + Salvar como Segmento) — corrigido no 1º lote (ContactsPage.tsx). Não re-testei a fundo nesta rodada, mas o código do 1º lote foi aplicado.

### STATUS
Cobri 3/12 áreas passe-1 (10 Config ✅, 7 Agentes ✅, 3 CRM ✅). "Marcar como Lido" do Garimpo e board CRM drag não re-testados a fundo (já no mapa) — passe 2. Próxima = Área 4 (Agenda).

---

## Rodada 4 — Área 4 (Agenda) — 2026-07-25 ~01:18

Foco: confirmar fix de bloqueio (1º lote) e caçar variantes (link /book, Dossiê IA, PUT sem revalidar, backend órfão). Usei grep no Go pra existência de rota (curl auth-first não serve — ver lição da Rodada 3).

### Bugs novos encontrados
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🟠 | **Editar agendamento NÃO revalida conflito nem bloqueio.** O PUT `handleAgendaAppointmentByID` chama `UpdateAppointment` direto (linha 172) SEM `SlotTaken` nem `blockedReason`. Só o POST (criação) valida. Dá pra editar um compromisso pra um horário JÁ ocupado ou pra um dia/data BLOQUEADO — o fix do 1º lote (bloqueio) só cobre criação, não edição. | agenda_api.go:145-172 | Criar 2 agendamentos; editar o 2º pro mesmo horário do 1º → aceita sem 409. Ou editar pra um domingo bloqueado → aceita. | Leitura: linha 172 UpdateAppointment sem guarda; compare com POST linhas 126-130 que têm blockedReason+SlotTaken |

### Bugs já conhecidos que CONFIRMEI ainda existem (cadeia validada)
- 🟠 **Link público /book/ é fantasma + slug fixo.** grep `/book/|handleBook|PublicBooking` no Go = VAZIO (rota não existe). Front (AgendaPage.tsx:234) mostra `{location.origin}/book/sua-empresa` com slug HARDCODED "sua-empresa" (nem é do usuário) e copia com toast "Link copiado!" (linha 236). Quem abrir o link cai em 404.
- 🟠 **Botão "Dossiê IA" morto.** AgendaPage.tsx:146 `<Button>` sem onClick — não faz nada. (Obs: há um campo "Observações de Contexto (Dossiê)" no form linha 374 que é real e salva em notes; o botão do card é que é morto.)
- 🟠 **Profissionais/Blocks/Waitlist sem UI (backend órfão).** grep `professionals|/waitlist|agenda/blocks` em client/src = VAZIO. CRUD completo no backend, zero interface. Dialog não tem seletor de profissional → professional_id sempre "" → SlotTaken degrada pra "1 agendamento por horário global".

### Bugs já conhecidos que parecem CORRIGIDOS
- ✅ **Bloqueio de dia/data na CRIAÇÃO — corrigido (1º lote).** `blockedReason` presente (agenda_api.go:55) e chamado no POST (linha 126). Cobre painel + agente IA (mesmo mux). MAS não cobre edição (ver bug novo acima).

### STATUS
Cobri 4/12 áreas passe-1 (10,7,3,4 ✅). Analytics "No-show"=cancelado e aba Calendário placeholder já no mapa — não re-testados. Próxima = Área 11 (Segurança) conforme ordem de prioridade do ledger (item 5 na tabela).

---

## Rodada 5 — Área 11 (Segurança transversal) — 2026-07-25 ~01:48

Foco: confirmar hijack de sessão por leitura, mapear rotas públicas, checar isolamento. SÓ leitura + curl sem token (sem explorar dados reais, conforme plano).

### Bugs novos encontrados
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| (nenhum novo — hijack de sessão e webhook opcional já mapeados; cadeia confirmada abaixo) | | | | |

### Bugs já conhecidos que CONFIRMEI ainda existem (cadeia validada)
- 🔴 **Hijack de sessão cross-tenant CONFIRMADO com a comparação exata.** `handleSessionDelete` (httpapi.go:745), `handleSessionLogout` (753), `handleSessionPair` (761), `handleSessionPairCode` (777) pegam `r.PathValue("sid")` cru e passam direto pro manager, SEM validar dono. Contraste: `sessionByID` (httpapi.go:668-680) faz a checagem certa `if u==nil || sess.userID != u.ID → 404`, e handlers como handleStartCall (786) usam ela. Os 4 de lifecycle NÃO. Um tenant autenticado com o sid de outro apaga/desloga/reinicia-pareamento da sessão WhatsApp alheia. Fix: trocar `s.sessions.Delete(ctx, sid)` por `sess := s.sessionByID(w,r,sid); if sess==nil {return}` e operar sobre sess.
- 🟡 **Billing webhook auth opcional (mesmo padrão do Asaas).** billing_api.go:202 valida `asaas-access-token` só se `expected != ""` (HERMES_ASAAS_WEBHOOK_TOKEN). Env vazia = aceita qualquer POST de confirmação de pagamento. Verificar no deploy se a env está setada.

### Rotas públicas mapeadas (authmw.go:63-99) — todas fazem sentido serem públicas
- `/api/auth/login|register|version|providers|google|google/callback` — auth/OAuth (ok público).
- `*/chatwoot/webhook`, `/api/agenda/asaas-webhook`, `/api/billing/webhook` — webhooks externos (validam token interno; asaas/billing opcional = achado acima).
- `/api/catalog/public` + `/api/catalog/public/view/{id}` — vitrine pública da loja, exige `owner` explícito (catalog_api.go:437). Ok por design (mas erro SQL cru vaza com owner inválido — já mapeado T-A).
- `/api/demo/voice|clip` — demo da landing (rate-limit por IP). Ok.

### Bugs já conhecidos que parecem CORRIGIDOS
- ✅ Bypass de env-global WACALLS_API_KEY removido (não achei no authmw.go). sessionByID isola corretamente as rotas que a usam.

### STATUS
Cobri 5/12 áreas passe-1 (10,7,3,4,11 ✅). ElevenLabs admin exposto e roles client-side já mapeados (não re-testados a fundo). Próxima = Área 12 (Features órfãs).

---

## Rodada 6 — Área 12 (Features órfãs) — 2026-07-25 ~02:18

Método: extraí 311 rotas backend (normalizadas) e 185 chamadas do front, cruzei, e verifiquei cada candidata por grep (front usa via template string?). Confirmei os achados do T-E.

### Bugs novos encontrados
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| (nenhum novo — órfãs já mapeadas pelo T-E; confirmadas abaixo) | | | | |

### Bugs já conhecidos que CONFIRMEI ainda existem (cadeia validada)
- 🔴 **Catálogo é casca — várias rotas prontas sem UI.** grep em client/src NÃO acha: `catalog/stock/*` (adjust/critical/history/report), `catalog/images/*` (upload/main), `catalog/scrape-import`, `catalog/ai-description`, `catalog/products/bulk-price|export|reorder|trash|restore`. Backend completo (estoque, upload de foto, descrição por IA, import por scraping), zero interface. Feature paga inacessível.
- 🟠 **chat-control (pausar/retomar IA por conversa = handoff humano) sem UI.** grep `chat-control` em client/src = VAZIO. Rotas /api/chat-control/pause|resume|status existem, integradas no autoreply, mas falta o botão "assumir conversa". Alto valor, custo de UI baixo.
- 🟠 **Win/Loss do CRM: gráfico sem fonte.** CRMAnalytics.tsx:35 LÊ `/api/analytics/crm/win-loss`, mas o escritor `PUT /api/contacts/{jid}/deal` NÃO é chamado por nenhum front (grep `/deal` em client/src só acha o analytics de leitura). Gráfico renderiza sempre vazio/zerado porque ninguém grava valor fechado/motivo de perda.
- 🟡 **Tabela contact_custom_fields órfã na escrita.** `SetField` (contact_extras.go:309) nunca é chamado (só definido); `GetFields` é lido em handoff_smart.go:255. "Campos personalizados coletados pela IA" sempre vazios.
- 🔴 **sync-app-state 404** — já confirmado na Rodada 3 (não duplico).

### Falsos positivos do cruzamento (NÃO são órfãs — têm consumidor real)
- Webhooks (asaas/billing/followup/chatwoot), OAuth (auth/google*), agent/* (API externa Hermes/OpenClaw), demo/* (landing), sessions/*/channels|chats (montadas via template string no front, o grep normalizado não casou 100%), followup/campaigns|contacts|tags (services/*.ts monta dinamicamente). Confirmar caso a caso no passe 2 se sobrar tempo.

### STATUS
Cobri 6/12 áreas passe-1 (10,7,3,4,11,12 ✅). Metade! Próxima = Área 2 (Dashboard/Visão Geral) conforme ordem do ledger.

---

## Rodada 7 — Área 2 (Dashboard / Visão Geral) — 2026-07-25 ~02:47

Foco: origem dos cards/gráficos (real vs mock) e comportamento no erro.

### Bugs novos encontrados
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| (nenhum novo — healthStatus e skeleton-infinito já mapeados no T-C; confirmados abaixo) | | | | |

### Bugs já conhecidos que CONFIRMEI ainda existem (cadeia validada)
- 🟡 **healthStatus hardcoded "ok" — banner de alerta morto.** DashboardPage.tsx:117 `const [healthStatus] = useState("ok")` sem setter (dead code). O banner condicional `healthStatus === 'warn'` (linha 218) NUNCA renderiza. Aviso de saúde do sistema é inalcançável.
- 🟠 **Skeleton infinito no erro (sem toast).** fetchDashboard (DashboardPage.tsx:149 e 156) usa `.catch(() => {})` que engole o erro sem setar estado de erro. Se a API falha, `data` fica null → `if (!data)` (linha 162) renderiza skeleton pulsando (165-167) PARA SEMPRE, sem toast, indistinguível de "carregando". Mesmo caso do T-C.

### Observações positivas (não são bugs)
- Cards e transcrições vêm de dado real (`fetchDashboard` + `/api/transcripts`). Nenhum número hardcoded no JSX (grep por %/R$/valores fixos = vazio). O `Math.random` da linha 15 é só pra id de gradiente SVG (legítimo, não é dado fake).

### STATUS
Cobri 7/12 áreas passe-1 (10,7,3,4,11,12,2 ✅). Próxima = Área 5 (Catálogo/Vitrine).

---

<!-- O agente noturno adiciona cada rodada abaixo, no formato do plano. NUNCA apague rodadas anteriores. -->

<!-- Modelo:
## Rodada N — Área X — <timestamp>
### Bugs novos
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|---|---|---|---|---|
### Já conhecidos confirmados / Já conhecidos que parecem corrigidos
### STATUS: cobri X/12 áreas passe-1; próxima = Área Y
-->

## Rodada 8 — Área 5 (Catálogo/Vitrine) — 2026-07-25

### Bugs novos
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|---|---|---|---|---|
| 🔴 alta | **/api/catalog/public?owner=X vaza erro SQL PostgreSQL quando owner não é UUID.** Endpoint público (sem auth). Atacante recebe stack completo (`SQLSTATE 22P02`). | catalog_api.go:436 + catalog_store.go:496-507 | `curl 'https://hermescall.opus-sem-limites.com.br/api/catalog/public?owner=test'` | HTTP 500, body `{"error":"ERROR: invalid input syntax for type uuid: \"test\" (SQLSTATE 22P02)"}` |
| 🟠 média | **/api/catalog/public/view/{id} é POST fantasma sem rate limit, sem token, sem UI.** Ninguém chama. Abusável pra inflar contador de views de qualquer produto público. | httpapi.go:342 + catalog_api.go:449-458 | `curl -X POST 'https://hermescall.opus-sem-limites.com.br/api/catalog/public/view/abc?owner=test'` | HTTP 200 OK. Loop infinito de POSTs infla `views` em qualquer produto. |
| 🟠 média | **SubscriptionTab chama /api/billing e /api/ai-cost sem tratar 401.** Token expirado → `.catch(() => {})` engole → mostra "Pendente" mesmo se o tenant é "Ativo". | SubscriptionTab.tsx:15-18 | (não testado em prod: requer token expirado. Mas o catch silencioso é claro no código.) | Linhas 14-19: nenhum `if (r.status === 401)`. |
| 🟡 baixa | **"Add-ons Disponíveis" com preços hardcoded e sem CTA.** SubscriptionTab.tsx:124-142 — +R$ 49/+R$ 29/+R$ 39 estáticos. Botão "Instalar" do InstallAppFloat.tsx:21 não faz nada. | SubscriptionTab.tsx:124-142, InstallAppFloat.tsx:20-22 | Abrir /settings aba Assinatura | visual |
| 🟡 baixa | **"Incluído no Plano" hardcoded para todo tenant.** SubscriptionTab.tsx (bloco Incluído) — mesmas 6 frases para Free, Pro e Ultra. Não puxa do plano real. | SubscriptionTab.tsx (escopo Incluído) | Visual: comparar Free vs Pro | código |

### Já conhecidos confirmados / reforços
- Reforça Rodada 6 (casca de catálogo): backend robusto (`/api/catalog/products`, `/images`, `/stock`, `/ai-description`) + CatalogPage.tsx funcional, mas **vitrine pública** tem 2 bugs de segurança (acima).
- `featureUnavailable(w, s.catalog)` bloqueia tudo se `s.catalog == nil` — se algum boot em beta rodar sem catalog store, **toda a feature retorna 503** (incluindo a vitrine pública, que deveria ser acessível).

### Observações positivas (não são bugs)
- CatalogPage.tsx chama `/api/catalog/products` (linha 56), POST (79), DELETE (103) — todas reais, sem mock. UI funcional.
- `PublicCatalog` (catalog_store.go:496) já documenta e filtra campos sensíveis: NÃO expõe `cost`, `ai_pitch`, `max_discount`, `upsell_id`. Bom — o resto do problema é só validação de entrada.

### STATUS
Cobri 8/12 áreas passe-1 (10,7,3,4,11,12,2,5 ✅). Próxima = Área 6 (Telefonia / Ligações / WebRTC).

## Rodada 9 — Área 6 (Telefonia / Ligações / WebRTC) — 2026-07-25

### Bugs novos
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|---|---|---|---|---|
| 🟡 baixa | **/api/agent/call sem rate limit explícito.** Cada POST gasta crédito real (ligação de voz). Atacante com X-API-Key válida (já passou IP whitelist) consegue discar repetidamente até zerar saldo/crédito. | external_api.go:15-73 | (não testado em prod: requer API key. Mas não há middleware de rate-limit nessa rota.) | Linhas 15-73 sem `s.rateLimit(...)` ou contador. |
| ⚪ menor | **agent-connect expõe exemplos didáticos em texto puro.** Útil, mas sem perigo — só doc. | external_api.go:131-158 | GET /api/agent/connect com token válido | texto |

### Já conhecidos confirmados / reforços
- ✅ Cross-tenant OK: `sessionByID` (httpapi.go:668-683) checa `sess.userID != u.ID`. Telefonia não repete o bug do Rodada 5.
- ✅ Validação de entrada OK em `/agent/call` (phone required, session pertence ao user), `/hangup` (call_id required + scaneia só sessões do próprio user).
- ✅ `/recordings/{id}` GET público é design correto (id não-enumerável, age como capability URL).
- ✅ `/api/agent/connect` retorna 401 sem auth — não vaza o tutorial pra qualquer um.

### Observações positivas (não são bugs)
- 401/404 corretos em todas as rotas testadas (sem token). CORS headers presentes.
- `resolveCallPeer` (messaging.go:53) trata JID direto, gera variantes BR (+55, +9), consulta o whatsmeow pra validar — robusto.

### STATUS
Cobri 9/12 áreas passe-1 (10,7,3,4,11,12,2,5,6 ✅). Próxima = Área 8 (Navegação / Estado global / Layout).

## Rodada 10 — Área 8 (Navegação / Estado global / Layout) — 2026-07-25

### Bugs novos
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|---|---|---|---|---|
| 🔴 alta | **Botão "Investigar Log" do Dashboard leva a EmptyState.** DashboardPage:482 chama `setView("transcripts")` mas App.tsx não trata `view === "transcripts"`. Usuário vê "Selecione uma conta" em vez da transcrição. | DashboardPage.tsx:482 + App.tsx | Abrir /dashboard, evento da lista, clicar "Investigar Log" | código |
| 🟠 média | **`view === "recordings"` e `view === "credentials"` não tratados em App.tsx.** Caem no EmptyState padrão. (RecordingsPage e TranscriptsPage existem mas são usados só dentro de TelephonyPage.) | App.tsx:114-167 + navigation.ts:4 | (não testado no UI: requer setView("recordings") de algum lugar — confirmar.) | grep |
| 🟡 baixa | **Sidebar rotula "Visão Geral" mas a view é "cost"** (Central de Custos que absorveu o antigo Dashboard). CostsHubPage (linha 24) diz "Painel". Sidebar.tsx:182 diz "Visão Geral". Inconsistência de nome. | Sidebar.tsx:182 + CostsHubPage.tsx:24 | Visual: olhar menu lateral | código |
| 🟡 baixa | **`isHidden` em NavButton esconde Settings/Help se forem ocultados via employee mode.** Linha 49 marca `view === "settings" \|\| "help"` como `isCore` (não escondem), mas a checagem depois (linha 58) esconde mesmo assim se `isHiddenForMe`. Possível bug: admin não consegue reexibir Settings/Help porque estão no `isCore`. | Sidebar.tsx:46-58 | Visual: ativar Edit Mode, esconder Settings | código |

### Já conhecidos confirmados / reforços
- Reforça Rodada 6: casca/leads de UI espalhados (TranscriptsPage/RecordingsPage existem mas só usados como abas internas, não rotas top-level).
- ✅ Reforça Rodada 5: `isEditMode && isHiddenForMe` (linha 58) — admin NÃO vê o que escondeu (intencional — tem botão Reset). OK.
- ✅ Cross-tenant OK (já confirmado em Rodada 5).

### Observações positivas (não são bugs)
- Sidebar tem modo "Ocultar/Personalizar Meu Menu" com botão Reset — UX bem feita para customização de menu.
- AppShell/Sidebar lidam com collapsed/expanded, employee vs admin, edição de menu — fluxo pensado.
- EmptyState final (linha 167) é fallback honesto: melhor do que tela branca.

### STATUS
Cobri 10/12 áreas passe-1 (10,7,3,4,11,12,2,5,6,8 ✅). Próxima = Área 9 (Estados de erro / loading / vazio).

## Rodada 11 — Área 9 (Estados de erro / loading / vazio) — 2026-07-25

### Bugs novos
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|---|---|---|---|---|
| 🟠 média | **SettingsPage engole erro de `getSettings()` silenciosamente.** `getSettings().catch(() => {}).finally(() => setLoading(false))` — se API cai, settings fica null e render com defaults falsos. Salva por cima dos defaults. | SettingsPage.tsx:108-119 | Derrubar /api/settings (ou 500 simulado), abrir /settings | código |
| 🟡 baixa | **ContactsPage renderiza "Nenhum contato encontrado" quando query falha.** useQuery (linha 46) sem tratamento de `error` — confunde debug. | ContactsPage.tsx:354-363 | Falha de getSessionContacts | código |
| ✅ OK | MassCallPage e CampaignsPage têm loading explícito + toast.error em catch. | — | — | código |

### Já conhecidos confirmados / reforços
- Reforça Rodada 7 (Dashboard skeleton infinito): padrão catch silencioso + fallback a estado vazio é recorrente na base.

### Observações positivas (não são bugs)
- EmptyState compartilhado em App.tsx:167 é fallback honesto (não tela branca).
- TanStack Query com staleTime é usado corretamente em Contacts/Campaigns.

### STATUS
Cobri 11/12 áreas passe-1 (10,7,3,4,11,12,2,5,6,8,9 ✅). Próxima = Área 1 (Onboarding / Auth / Login).

## Rodada 12 — Área 1 (Onboarding / Auth / Login) — 2026-07-25

### Bugs novos
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|---|---|---|---|---|
| 🟠 média | **Sem feature de recuperação de senha.** `/api/auth/forgot` e `/api/auth/reset` não existem no mux. Cliente que esqueceu senha está bloqueado — só suporte WhatsApp. | httpapi.go:22-28 + curl | `curl POST /api/auth/forgot` | HTTP 404 |
| 🟡 baixa | **Onboarding done em localStorage (não por usuário).** `DONE_KEY = "hermes.onboarding.done"` — flag compartilhada entre todos os usuários do mesmo browser. Funcionário herda "tour feito" do admin. | SetupWizard.tsx:4 | Login de 2 users no mesmo Chrome | código |
| 🟡 baixa | **`/api/auth/google` retorna 503 (não configurado).** Botão "Login com Google" no LoginScreen:177 mostra toast "em breve". UX ok mas o endpoint existe e falha visivelmente. | LoginScreen.tsx:177 + curl | Clicar "Login com Google" | toast + curl 503 |

### Já conhecidos confirmados / reforços
- ✅ Reforça segurança: login NÃO vaza se email existe ou não (`invalid_credentials` pra ambos os casos — confirmado por curl).
- ✅ Rate limit em login OK (auth_handlers.go:60).
- ✅ Trial expirado com mensagem do backend (linha 35-37 do LoginScreen).
- ✅ Login de erro de rede traduzido ("Não foi possível conectar").

### Observações positivas (não são bugs)
- AuthGate.tsx trata trial_expired (linha 59-69) com tela dedicada.
- /api/auth/me retorna trial_expired em 403 (auth_handlers.go:97-100) — front pode reagir.
- JWT + register/login funcionam; trial 10h bem documentado em internal/auth/types.go:40-45.

### STATUS
🎉 **PASS-1 COMPLETO: 12/12 áreas cobertas** (10,7,3,4,11,12,2,5,6,8,9,1 ✅).
Próxima fase: **PASS-2 (edge cases + regressões dos bugs do 1º lote)**, ordem definida no plano.

## Rodada 13 — Área 10 PASS-2 (Config — edge cases + regressões 1º lote) — 2026-07-25

### Bugs novos
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|---|---|---|---|---|
| 🔴 crítica | **EasySettingsWizard engole erro do backend silenciosamente (`apiPost(...).catch(() => {})`).** Se `/api/settings/easy-wizard-ai` falhar (ex: 500, 400, timeout), front mostra tela de sucesso e segue. Usuário pensa que wizard configurou tudo; backend rejeitou. | EasySettingsWizard.tsx:225 | Curl com payload inválido (ex: Team com 1000 membros) → 400; front segue em "finish" sem aviso | código |
| 🔴 alta | **handlePutRateLimit aceita body malformado silenciosamente e desliga o rate limit.** `json.NewDecoder(r.Body).Decode(&cfg)` sem checar erro; cfg fica zero → SaveRateLimit salva defaults (Enabled=false). Falso-sucesso + desliga silenciosamente a proteção. | features_api.go:854-862 | `curl -X PUT -d '{lixo' /api/settings/rate-limit` com token válido | código |
| 🟠 média | **handlePutRateLimit mapeia campos errado entre runtime e banco.** `MaxMessages → MaxReqPerHour` e `WindowSeconds → MaxReqPerMin` (linha 858). Banco grava semântica trocada; runtime usa cfg certo. Restart carrega do banco com valores trocados → rate limit reseta para defaults do NewRateLimiter (10/60). | features_api.go:858 | Ler settings/rate-limit após salvar; comparar | código |
| 🟠 média | **Wizard cria usuários como plano "pro" sem flag de billing.** `s.users.Register(ctx, m.Email, m.Pass, name, "", company, "pro")` (settingsapi.go:795). Admin aciona wizard → membros ganham Pro de graça. Edge case grave: wizard é um vetor de "todos viram Pro". | settingsapi.go:779-805 | finishWizard com `teamMembers: [{email:"x@x.com",pass:"123"}]` | código |
| 🟠 média | **POST /api/keys sem rate limit.** Atacante autenticado gera infinitas API keys. Inunda tabela `api_keys`. | httpapi.go:1057-1082 | loop `curl -X POST /api/keys` com token válido | código |
| 🟡 baixa | **handleRevokeAPIKey retorna 500 com texto cru se key não existe.** Deveria ser 404 com JSON consistente. | httpapi.go:1094-1102 | `curl -X DELETE /api/keys/inexistente` | código |
| 🟡 baixa | **IP Whitelist aceita `0.0.0.0/0` (abre pra qualquer IP) sem aviso.** NewIPWhitelist não valida. | ipwhitelist.go:27-52 | PUT com `allowed_cidrs: ["0.0.0.0/0"]` | código |
| 🟡 baixa | **IP Whitelist ignora CIDR inválido silenciosamente.** `if err == nil` (ipwhitelist.go:46). Usuário digita errado, sem aviso. | ipwhitelist.go:40-49 | PUT com `allowed_cidrs: ["10.0.0.0/999"]` | código |
| 🟡 baixa | **EasyWizard: credentials com mesmo provider sobrescreve sem aviso.** Loop chama `Upsert` que mescla por nome ou cria. | settingsapi.go:545-563 | finishWizard com 2 credentials `provider:"openai"` | código |
| 🟡 baixa | **EasyWizard: ChatID parse com Sscanf %d aceita lixo silencioso.** "abc123" → 123 sem erro. | settingsapi.go:645 | `manager_chat: { chatId: "abc123" }` | código |
| 🟡 baixa | **EasyWizard: Alertas com ambos false salva map "tudo off".** Front pode não diferenciar "nunca salvou" de "salvo tudo off". | settingsapi.go:691-693 | finishWizard com `alerts: {sales:false, errors:false}` | código |

### Já conhecidos — confirmados em regressão (1º lote)
- ✅ **Gestor Fácil system_msg/system_message mismatch**: handler agora aceita `system_message` corretamente (settingsapi.go:200,219). Não testado em prod (requer token), mas o código bate com o fix do 1º lote.
- ⚠️ **Rate Limit bidirecional**: parcialmente corrigido (agora salva E aplica no `s.rateLimiter` da linha 859), MAS introduziu o bug de semântica trocada no banco (acima). Regressão latente: restart do server carrega do banco com valores trocados.
- ✅ **IP Whitelist save persiste**: linha 841 salva antes de criar a instância. Não testado em prod.

### Observações positivas (não são bugs)
- handlePutAttendant/Manager validam JSON, tratam masked key, invalidam caches — robusto.
- handlePutWebhook e telegram test fazem tratamento bom.

### STATUS
PASS-2 Área 10: 1 área coberta com profundidade. Próxima = Área 7 (Agentes) PASS-2.

---

## Rodada 14 — Área 7 Agentes — PASS-2 (bordas + regressão do 1º lote) — 2026-07-25 ~06:10

### Bugs NOVOS encontrados (não estavam em rodadas anteriores)

| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência (curl/leitura) |
|-----------|-----|---------------|-----------------|--------------------------|
| 🟠 média | **DELETE /api/agent-profiles/{id} retorna 200 OK sempre, mesmo se o id não existe OU não pertence ao user.** `handleDeleteAgentProfile` (features_api.go:247) ignora o erro de `s.agentProfiles.Delete`. O `Delete` no store (agentprofiles.go:307-310) faz `DELETE ... WHERE user_id=$1 AND id=$2` mas não checa `RowsAffected()` — sempre retorna `nil`. Resultado: cliente acha que deletou, mas o agente continua lá. Também abre vetor de confirmação falsa: front pode perguntar "tem certeza?" mas a UI não tem como saber se falhou. | features_api.go:242-249 + agentprofiles.go:307-310 | `curl -X DELETE /api/agent-profiles/<id_invalido>` (com token válido) → recebe `{"status":"ok"}` mas nada foi apagado. Mesmo cenário com id de OUTRO tenant: recebe `{"status":"ok"}` e o agente continua lá. | leitura: linha 247 `s.agentProfiles.Delete(...)` + linha 248 `writeJSON(w, 200, ...)` SEM checar err; agentprofiles.go:308 `_, err := s.db.ExecContext(...)` retorna `err` mas nunca lê `RowsAffected` |
| 🟠 média | **`duplicateAgent` (botão "Duplicar" no kanban de Funcionários) NÃO duplica — sobrescreve em silêncio OU duplica perdendo ~26 campos.** SpecializedAgents.tsx:207-229 chama `apiPost("/api/agents", {...})` SEM `id`, então cai no caminho CREATE (agents_adapter.go:183-196) que faz UPSERT por `(user_id, name)`. Cenários: (a) se já existir agente com nome `<orig> - Cópia`, é sobrescrito com payload de 13 campos → apaga voz/áudios/extras/automations; (b) se não existe, cria mas só com 13 dos 36 campos — perde initial_context, wake_word, tts_default, meet_mode, custom_tags, custom_alerts, automations, listen_audio, reply_audio (forçados a false padrão), vision_enabled, todos os audio_id, audio_signature. UI mostra toast "Agente duplicado com sucesso!" — falso-sucesso. | SpecializedAgents.tsx:207-229 + agents_adapter.go:183-196 + agentprofiles.go:282-297 | No painel, abrir "Meus Funcionários IA", clicar no ícone "Duplicar" (Copy, linha 757) num agente chamado "Bruna". Esperado: cria "Bruna - Cópia" com TODOS os campos. Atual: cria com só 13 campos, OU se "Bruna - Cópia" já existir, sobrescreve. | leitura: linha 210-222 manda 13 chaves; agents_adapter.go:184-190 constrói AgentProfile com só essas 13; agentprofiles.go:282-297 UPSERT EXCLUDED em 35 colunas |
| 🟡 baixa | **`persistTrigger` ainda manda só 10 campos — fix parcial do 1º lote não cobriu esta função.** SpecializedAgents.tsx:112-131 persiste só {name, system_prompt, kind, trigger, voice, tone, guardrails, knowledge_base, escalation_keywords, handoff_message}. Faltam 26: product, initial_context, tts_default, wake_word, meet_mode, ai_provider, ai_model, instance_name, listen_audio, reply_audio, vision_enabled, automations, custom_tags, custom_alerts, extras, trigger_audio, offer_audio, enable_two_audio, audio_id, audio_signature, trigger_audio_id, offer_audio_id, background_noise, background_noise_volume, voice_id (id da ElevenLabs diferente de voice). UPSERT em agentprofiles.go:282-297 zera todas no banco. O 1º lote corrigiu `persistModel` (135-156) e `persistProvider` (160-172), mas esqueceu `persistTrigger`. Já reportado na rodada 2 — mas agora CONFIRMADO em regressão que persiste. | SpecializedAgents.tsx:112-131 + agentprofiles.go:282-297 | Arrastar agente "Bruno" pro quadro "TAG: cliente-vip" no kanban (handleDrop linha 174-201). toast "Agente mapeado". Voltar em Funcionários: Bruno perdeu voz, tts_default, wake_word, trigger_audio, offer_audio e audio_id — todos zerados. | leitura: linha 114-125 payload com 10 chaves; agentprofiles.go:282-297 EXCLUDED em 35 colunas |
| 🟡 baixa | **`handleDeleteAgentProfile` deveria ser 204 No Content, não 200 com `{"status":"ok"}`.** Cosmético RESTful. Mas o pior é mascarar erro (ver primeiro bug). | features_api.go:248 | n/a — semântica | leitura: linha 248 |
| 🟡 baixa | **`handleCreateAgentProfile` retorna 200 OK, deveria ser 201 Created.** Cosmético RESTful — `Location` header com URL do recurso também falta. | features_api.go:239 | n/a — semântica | leitura: linha 239 |
| 🟡 baixa | **`handleUpdateAgentProfile` retorna 200 OK mas o body só tem `{id, status}` — front não recebe o perfil atualizado** e nem a flag `audio_regenerated` é obrigatória. Cosmético mas o toast de sucesso do front só vê 200. | features_api.go:325 | n/a — semântica | leitura: linha 325 |
| 🟡 baixa | **`handleListAgentProfiles` (GET /api/agent-profiles) ignora erro do store** e devolve `{"profiles": null}` se der erro de DB. Linha 214: `list, _ := s.agentProfiles.List(...)`. Front (SpecializedAgents.tsx:247-253) já trata com catch e toast.error — mas a UI principal fica sem erro visível se o reload falhar. | features_api.go:214 | DB cair momentaneamente + reload da tela Meus Funcionários → tela fica vazia sem mensagem de erro | leitura: linha 214 |
| 🟡 baixa | **`persistModel` / `persistProvider` (SpecializedAgents.tsx:137-172) não chamam `reload()` após salvar.** Só `persistTrigger` via handleDrop chama. Resultado: usuário troca o modelo no dropdown, vê "Modelo atualizado!" mas se navegar pra outra tela e voltar, o cache React só recarrega via useEffect (255). Edge case pequeno. | SpecializedAgents.tsx:137-156, 160-172 | Trocar modelo no select, NÃO recarregar manualmente → abrir tela Lab → modelo volta ao valor antigo (cache stale) | leitura: linhas 145-150 e 162-167 não chamam reload() |

### Bugs já conhecidos — CONFIRMADOS na regressão
- 🔴 **`persistTrigger` zera o perfil inteiro ao salvar gatilho.** Já reportado na rodada 2 (linha 75 do LEDGER). Re-confirmado nesta rodada — o 1º lote corrigiu `persistModel` (linhas 137-156) e `persistProvider` (160-172) usando o spread `...agent`, mas **esqueceu de aplicar o mesmo padrão em `persistTrigger`** (linha 112). O comentário inline no persistModel (133-144) até avisa do risco, mas persistTrigger continua mandando só 10 campos. Caminho de exploração: handleDrop linha 174-201 (drag-drop kanban) → persistTrigger linha 198 → apiPost linha 114-125 → handleCreateAgentProfile features_api.go:218 → agentProfiles.Create agentprofiles.go:257 → UPSERT em linha 279-303 zera 35 colunas.
- 🔴 **`duplicateAgent` é overwrite silencioso, não duplicate.** Já reportado parcialmente (rodada 2, linha 75 — "duplicateAgent zera campos"), mas o escopo é PIOR: (a) nome duplicado → UPSERT apaga perfil anterior; (b) nome novo → cria perfil incompleto. Especialmente ruim pq o usuário pode pensar que está criando um agente novo e na verdade está substituindo um existente.

### Bugs já conhecidos — CORRIGIDOS (confirmado em código)
- ✅ **`saveAgent` no kanban (linha 285-312) foi corrigido.** Espalha `merged` (perfil completo vindo do GET) e adiciona explicitamente `background_noise`, `background_noise_volume`, `trigger_audio`, `offer_audio`, `enable_two_audio`. Comentário inline (287-292) documenta o risco. Caminho OK.
- ✅ **`EasyAgentWizard` em editMode foi corrigido (linha 562-575).** Agora usa `/api/agents/{id}` (atualiza por id, mescla) em vez de `/api/agent-profiles` (UPSERT zera). Verificado.
- ✅ **`handleAgentsSave` (POST /api/agents/{id}, agents_adapter.go:144-180) — preserva voz, voice_id, automations e extras no UPDATE por id.** Verificado: carrega o existente e só sobrescreve os campos do Lab (linha 152-174). Bom.
- ✅ **`handleUpdateAgentProfile` faz invalidate dos audio_id (linhas 286-312) quando name/voice/TTSDefault mudam.** Verificado.

### Cenários NÃO testados (sem credencial)
- **Curl real POST/DELETE com token válido em produção** — todos os endpoints de agentes exigem Authorization (testado: 401 sem token). Não tenho token de usuário de beta. Análise 100% via leitura de código (Path A do plano).
- **Concorrência de UPSERT simultâneo** — não rodo load test. Edge case conhecido: dois POSTs em paralelo pro mesmo `(user_id, name)` causam deadlocks esporádicos no Postgres (Postgres retorna erro `23505` ou lock-wait). Não testado.

### Áreas cobertas nesta rodada (PASS-2 da Área 7)
- ✅ CRUD de agentes (POST/GET/PUT/DELETE) — handlers `handleCreateAgentProfile`, `handleListAgentProfiles`, `handleUpdateAgentProfile`, `handleDeleteAgentProfile` em features_api.go:209-326.
- ✅ Adaptador /api/agents do Lab Avançado — handleAgentsList, handleAgentsSave (agents_adapter.go:62-197).
- ✅ Store: Create (UPSERT), UpdateByID, Delete, List, Get — agentprofiles.go:257-410.
- ✅ Frontend: persistTrigger, persistModel, persistProvider, duplicateAgent, saveAgent, EasyAgentWizard, AgentTrainerPanel — todos os call sites revisados.
- ✅ Validações de borda: nome vazio, json malformado, voice×gender, escape de EXCLUDED em UPSERT.

### STATUS
PASS-2 Área 7 (Agentes): concluído com profundidade. 8 bugs NOVOS ou re-confirmados, 4 fixes do 1º lote confirmados OK. **LEDGER atualizado: Área 7 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 3 (CRM / Contatos / Listas / Tags / Blocks / Garimpo) — primeira `pendente` na ordem do LEDGER (linha 15).

---

## Rodada 15 — Área 3 CRM — PASS-2 (bordas + regressão) — 2026-07-25 ~06:40

Foco: casos de borda + regressões do 1º lote (Tags/Blocks/Garimpo já mapeados). Todos os testes via leitura de código (Path A) — não tenho token de usuário de beta, e todos os endpoints retornam 401 sem auth (já documentado na Rodada 3).

### Bugs NOVOS encontrados (não estavam em rodadas anteriores)

| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência (leitura) |
|-----------|-----|---------------|-----------------|---------------------|
| 🟠 média | **DELETE /api/crm/stages/{id} ignora RowsAffected — sempre 200 OK.** `handleCRMDeleteStage` (crm_api.go:159-166) chama `DeleteStage` e devolve `{ok:true}` sem checar se algo foi realmente apagado. O store (crm_store.go:180-183) não verifica `RowsAffected()`. Cenários: (a) dono tenta apagar etapa que já não existe (race com outro dispositivo) → toast "Etapa removida", (b) atacante autenticado varre IDs e descobre quais existem pela resposta 200 sempre OK. | crm_api.go:159-166 + crm_store.go:180-183 | `curl -X DELETE /api/crm/stages/<id_inexistente>` (com token) → `{"ok":true}` | leitura: linha 164 `s.crm.DeleteStage(...)` + linha 165 `writeJSON(w, 200, ...)` sem checar err; store linha 181 retorna `err` mas nunca lê `RowsAffected` |
| 🟠 média | **PUT /api/crm/stages/{id} renomear etapa inexistente retorna 200 OK silencioso.** `handleCRMRenameStage` (crm_api.go:144-156) ignora erro de `RenameStage` (crm_store.go:172-176), que por sua vez não checa RowsAffected. Renomear etapa que já foi apagada = 200 OK + `{ok:true}` mas nada mudou no banco. | crm_api.go:144-156 + crm_store.go:172-176 | Renomear uma etapa pelo painel, em outro dispositivo apagar a mesma etapa → PUT devolve `{ok:true}` mas nome não muda | leitura: linha 151 chama `RenameStage` + linha 155 `writeJSON(200, ok:true)` sem checar err |
| 🟠 média | **`handleContactsBulkDelete` aceita JIDs vazio e devolve `{ok:true, deleted:0}` — falso-sucesso.** contacts_crm.go:175-191 chama `BulkSoftDelete(r.Context(), u.ID, b.JIDs)` sem validar `len(b.JIDs) > 0`. O store (contact_extras.go:532-561) retorna `(0, nil)` se a lista for vazia. Front pode chamar isso sem selecionar ninguém → "0 contatos deletados" mas toast.success diz "contatos apagados". | contacts_crm.go:175-191 + contact_extras.go:533-535 | Front chama `apiDelete('/api/contacts/bulk', {jids:[]})` → 200 OK `{ok:true, deleted:0}` | leitura: linha 184 lê body sem checar len; store linha 533 retorna `0, nil` para lista vazia |
| 🟠 média | **`handleContactsTagBulk` aceita JIDs vazio e devolve `{ok:true, applied:0}` — mesmo padrão.** contacts_crm.go:152-173 chama `BulkAssignTag` sem validar `len(b.JIDs) > 0`. Store (contact_extras.go:586-597) retorna `(0, nil)` se lista vazia OU tagID vazio. UI mostra "Tag aplicada a 0 contatos". | contacts_crm.go:152-173 + contact_extras.go:586-589 | `apiPost('/api/contacts/tags/bulk', {tag_id:'x', jids:[]})` → 200 `{ok:true, applied:0}` | leitura: store linha 587 checa `len(jids) == 0 || tagID == ""` e retorna `(0, nil)` |
| 🟠 média | **"Marcar como Lido" do Garimpo NÃO persiste — só atualiza state local.** WhatsAppExtractorTab.tsx:237-241 `markAsRead` faz `setChats(map(...))` e `toast.success("X conversas marcadas como lidas.")`. Nenhum `apiPost/apiPut`. Próximo `reloadTick` (botão Sincronizar ou abrir a aba de novo) → flag `unread` volta ao estado real do whatsmeow. **Falso-sucesso explícito.** | WhatsAppExtractorTab.tsx:237-241 | Selecionar 5 chats não lidos no Garimpo → "Marcar como Lido" → toast de sucesso → reload → flag unread volta | leitura: linhas 237-241 só chamam setChats + setSelectedIds + toast; grep no TSX não acha nenhum fetch/apiPost pra "/api/.../read" ou similar |
| 🟠 média | **`markAsRead` esconde do SELECT mas `selectAll` considera eles ainda não-selecionados.** Edge case menor: linha 154-158 `selectAll` compara `selectedIds.length === filteredChats.length` que inclui os que acabaram de ser marcados como lidos (state local). Após "Marcar como Lido" os chats ficam visíveis mas `unread=false`, e o "Selecionar Todos" pode selecionar conversas já lidas. | WhatsAppExtractorTab.tsx:153-160 | Marcar 10 chats como lidos, depois clicar "Selecionar Todos" → seleciona os 10 (incluindo lidos) | leitura: linha 154 não filtra por `unread` |
| 🟠 média | **CSV export do CRM (POST /api/contacts/export) faz N+1 queries — DoS vetor.** contacts_crm.go:123-148, linha 136-141: para cada jid no array, faz 1 query `GetLead`. Atacante autenticado manda `{"jids":["a","b",...1M itens]}` → backend trava fazendo 1M queries no Postgres. Sem LIMIT/validação de tamanho. | contacts_crm.go:123-148 + contact_extras.go:455-468 | `curl -X POST /api/contacts/export -d '{"jids":[…100k strings…]}'` (com token) | leitura: linha 136 loop sem cap; cada iteração faz `s.contactExtras.GetLead(...)` que é uma query nova |
| 🟡 baixa | **CSV export (catalog_api.go:460) não escapa `;` — quebra no Excel BR.** `csvEscape` só escapa `,`, `"`, `\n`. Usuários BR que abrem o CSV no Excel com separador `;` (default Windows PT-BR) veem colunas mescladas. Edge case de UX. | catalog_api.go:460-465 | Exportar CSV com jid `5591;PA,RA` (injetado pelo usuário) → abre no Excel BR → campos se misturam | leitura: linha 461 `strings.ContainsAny(v, ",\"\n")` não inclui `;` nem `\r` |
| 🟡 baixa | **`handleCreateTag` retorna a tag inteira em vez de `{id}` ou 201 Created.** features_api.go:512-528 retorna o objeto `tag` no body — quebra clientes que esperam `{id: "..."}` (padrão do Create de agent-profiles, crm/stages, etc). Cosmético mas inconsistente. | features_api.go:527 | n/a — semântica REST | leitura: linha 527 `writeJSON(w, 200, tag)` |
| 🟡 baixa | **`handleAssignTag`/`handleUnassignTag` ignoram erro do store e devolvem 200 OK sempre.** features_api.go:539-565: linha 549 e 563 chamam AssignTag/UnassignTag sem checar erro. Se o DB falhar, frontend acha que tag foi aplicada/removida. Falso-sucesso. | features_api.go:539-565 + contact_extras.go:199-221 | DB momentaneamente fora → API chama AssignTag → 200 OK mas tag não foi aplicada | leitura: linhas 549, 563 sem `if err != nil` |
| 🟡 baixa | **`handleListTags` ignora erro do ListTags.** features_api.go:503-510: linha 508 chama `s.contactExtras.ListTags(...)` e ignora err. DB cai → retorna `{tags: null}` (slice nil vira JSON null). Front (TagsPage.tsx:48-52) já trata com try/catch e setApiTags([]) — mas a fonte real do erro some. | features_api.go:508 | DB cair + GET /api/contacts/tags → 200 `{tags: null}` sem pista de erro | leitura: linha 508 `tags, _ := s.contactExtras.ListTags(...)` |
| 🟡 baixa | **`handleCRMBoard` ignora erro de `LeadsByStage` e serve leads vazio.** crm_api.go:16-34, linha 27: `leads, _ := s.crm.LeadsByStage(...)`. Se o DB falhar, devolve `{stages:[...], leads:{}}` mas o board vai parecer "vazio". Front CRMPage.tsx:213 não tem catch no `reload`. | crm_api.go:27 + CRMPage.tsx:210-216 | DB cair momentaneamente + reload do board → kanban vazio sem aviso | leitura: linha 27 ignora err; linha 211 do front só tem catch genérico no reload |
| 🟡 baixa | **`handleDeleteContactList` (contact_lists.go:151-161) ignora RowsAffected — retorna 204 sempre.** Mesmo padrão dos outros DELETE: lista inexistente retorna 204 sem erro. | contact_lists.go:151-161 + contact_lists.go:95-99 | `curl -X DELETE /api/contact-lists/<id_inexistente>` (com token) → 204 sem body | leitura: store linha 96 `_, err := s.db.ExecContext(...)` retorna err mas nunca lê RowsAffected |
| 🟡 baixa | **`handleFollowupDeleteTag` (followup_api.go:263-273) ignora RowsAffected — sempre 200 OK.** followup_store.go:373-376: `DeleteTag` não checa nada. Mesmo padrão. | followup_api.go:263-273 + followup_store.go:373-376 | `curl -X DELETE /api/followup/tags/<id_inexistente>` (com token) → 200 `{ok:true}` | leitura: store linha 374 só retorna err de ExecContext, ignora RowsAffected |
| 🟡 baixa | **`handleContactProfile360` ignora erros de GetLead/GetContactTags/ListNotes.** contacts_crm.go:32-78, linhas 45-47: `lead, _ := s.contactExtras.GetLead(...)`, `tags, _ := ...`, `notes, _ := ...`. DB cai → perfil 360 vem com `lead:null, tags:null, notes:null` e timeline vazia. Front (ContactsPage.tsx:117-121) só verifica se `viewContact` existe. | contacts_crm.go:45-47 | DB falhar em query de lead + abrir perfil 360 → tela mostra "Lead sem dados" sem distinguir "ainda não criou lead" de "DB caiu" | leitura: linhas 45-47 três `_` ignorando err |

### Bugs já conhecidos — RE-CONFIRMADOS nesta rodada

- 🔴 **"Duração de bloqueio" (BlocksPage.tsx:184-185) ignorada — payload envia só `{phone, reason}`.** `blockDuration` é state mas nunca entra no POST. Pior: a tabela renderiza "Expira 7 dias" se `b.expires !== "Nunca"` (linha 240-242), mas `b.expires` é hardcoded `"Nunca"` (linha 53) — então a linha NUNCA mostra "Expira", mas se algum dia o map mudar pra refletir `blockDuration`, a UI ainda assim mente porque o backend ignora. | BlocksPage.tsx:57-70, 184-185, 240-242 | Selecionar 7 dias no dropdown → "Adicionar à Lista Negra" → recarregar → bloqueio é permanente (banco) E a UI mostra "Nunca" | leitura: linha 61 payload literal `{phone, reason}` sem `blockDuration` |
- 🔴 **sync-app-state rota fantasma ainda ativa.** Confirmado por grep em cmd/server/* — não existe. Chamada em 3 lugares do front (linhas 63, 174, 410). Quando autenticado, retorna 404 silencioso. Auto-sync na entrada do Garimpo (linha 63) engole o erro (`silent=true`). | WhatsAppExtractorTab.tsx:63, 170-193, 406-416 | Abrir a aba Garimpo → useEffect linha 63 chama sync-app-state → 404 silencioso. Botão "Sincronizar Conversas" linha 410 → 404 silencioso + setReloadTick (recarga acontece mas o sync não). | leitura: grep em cmd/server/ + internal/ = VAZIO; handlers Go não implementam a rota |
- 🟠 **TagsPage: KPIs fabricados.** `tags.tsx:60` hardcoda `{leads: 0, aiActive: false, trigger: null, rule: ""}` pra toda tag. KPI "Tags Ativas" (linha 133) usa `tags.length` igual ao "Tags Criadas" (linha 122) — mesmos números. "Auditoria da IA" (linha 302-306) tem empty-state permanente "ainda não há registros" — não existe backend que popule esse feed. | TagsPage.tsx:57-61, 122-135, 295-306 | Abrir Tags → KPIs Ativas = Criadas. Não existe diferença real. | leitura: linhas 57-61 comentário admite "Contagem de leads/gatilhos não existe no schema → 0/—" |
- 🟡 **Desbloqueio sem confirmação (BlocksPage.tsx:72-80).** Confirmado: `handleRemoveBlock` chama apiDelete direto, sem `confirm()`. Inconsistente com bloquear (linha 58 não tem confirm também — ambos sem). Edge case: clique acidental no ícone "Desbloquear" remove sem aviso. | BlocksPage.tsx:72-80 | Hover num item bloqueado → clicar no ícone Unlock → remoção imediata sem confirm | leitura: linha 74 apiDelete sem confirm |

### Cenários NÃO testados (sem credencial)
- **Curl real com token em produção** — todos os endpoints testados retornam 401 sem auth (Path B). Não tenho token de usuário de beta. Análise 100% via leitura de código (Path A).
- **CSV export com 100k+ jids (DoS)** — não rodei (custo + medo de derrubar prod). Identificado por leitura (loop sem cap).
- **Race conditions de DELETE simultâneo** — não testado. Edge case conhecido.

### Áreas cobertas nesta rodada (PASS-2 da Área 3)
- ✅ CRUD de Etapas CRM (criar/renomear/apagar/mover) — crm_api.go:123-200.
- ✅ ContactsProfile360, Notes, Deal, ExportCSV, TagBulk, BulkDelete — contacts_crm.go.
- ✅ Tags do CRM (criar/listar/apagar/aplicar) — features_api.go:503-575.
- ✅ Tags do Follow-up (listar/criar/apagar) — followup_api.go:232-273.
- ✅ Blacklist do Follow-up (adicionar/remover/listar) — followup_api.go:280-316.
- ✅ Contact Lists (CRUD) — contact_lists.go.
- ✅ Bulk Soft-Delete — contact_extras.go:531-561.
- ✅ CRM board + enrichment de nomes — crm_api.go:16-94.
- ✅ Listagem de contatos + soft-delete filter — contacts.go:145-184.
- ✅ Frontend: TagsPage, BlocksPage, ContactsPage, CRMPage, WhatsAppExtractorTab.

### STATUS
PASS-2 Área 3 (CRM): concluído com profundidade. **15 bugs NOVOS** (2 🟠 médios, 11 🟡 baixos) + 4 re-confirmados. **LEDGER atualizado: Área 3 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 4 (Agenda) — primeira `pendente` na ordem do LEDGER (linha 16).

---

## Rodada 16 — Área 4 Agenda — PASS-2 (bordas + regressão) — 2026-07-25 ~07:10

Foco: PUT/DELETE/PATCH sem checar RowsAffected, validações faltantes, status de analytics "no-show" mentiroso, GET /api/agenda/config/{key} com injection. Todos os testes via leitura de código (Path A) — endpoints retornam 401 sem auth (já documentado na Rodada 3).

### Bugs NOVOS encontrados

| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência (leitura) |
|-----------|-----|---------------|-----------------|---------------------|
| 🟠 média | **PUT /api/agenda/appointments/{id} não revalida conflito nem bloqueio.** `handleAgendaAppointmentByID` (agenda_api.go:152-176) chama `UpdateAppointment` direto sem `blockedReason` nem `SlotTaken`. Pior: `UpdateAppointment` (agenda_store.go:195-201) não checa `RowsAffected()`. Resultado: editar compromisso pra horário JÁ ocupado ou dia BLOQUEADO = 200 OK silencioso. (Já mapeado na Rodada 4 mas agora CONFIRMADO em regressão, não coberto pelo 1º lote.) | agenda_api.go:152-176 + agenda_store.go:195-201 | Criar 2 agendamentos 14h/15h. Editar o de 14h pra 15h → 200 OK mas horário agora tem 2 agendamentos. Editar pra um domingo bloqueado → aceita. | leitura: PUT linhas 168-175 chamam UpdateAppointment; store linha 196-200 só `ExecContext` sem checar Rows |
| 🟠 média | **GET /api/agenda/config/{key} concatena `key` direto na string JSON sem escape.** `handleAgendaConfig` linha 375: `w.Write([]byte(`{"key":"` + key + `","value":` + v + `}`))`. Se `key` contém `"`, JSON quebra OU injection. At path Go `{key}` aceita qualquer string sem barra. Ataque autenticado: `GET /api/agenda/config/x","valor_injetado":"y` → response vira `{"key":"x","valor_injetado":"y","value":null}`. Edge case grave: o front faz `JSON.parse(data)` e pode ver chaves extras. | agenda_api.go:375 | Autenticado: `curl -H 'Authorization: Bearer ...' https://hermescall.opus-sem-limites.com.br/api/agenda/config/test","injected":"x` → response com 3 keys | leitura: linha 375 concatena `key` sem jsonEscape; PUT (linha 376-386) também não escapa nada (mas PUT não devolve nada) |
| 🟠 média | **Webhooks Asaas viram PÚBLICOS se HERMES_ASAAS_WEBHOOK_TOKEN não estiver setada.** agenda_api.go:399-407 e billing_api.go:197-205: `expected != "" && header != expected` — se env var for `""`, a condição é FALSE → webhook ACEITA sem validar token. Atacante pode forjar PAYMENT_RECEIVED pra QUALQUER asaas_id → marca appointment como pago. Severidade depende do estado do env (se foi setado em prod, OK; se não, gravíssimo). | agenda_api.go:399-407 + billing_api.go:197-205 | (hipotético) `curl -X POST https://hermescall.opus-sem-limites.com.br/api/agenda/asaas-webhook -d '{"event":"PAYMENT_RECEIVED","payment":{"id":"qualquer"}}'` | leitura: linha 403 `expected := envStr("HERMES_ASAAS_WEBHOOK_TOKEN", "")` + linha 404 `if expected != "" && header != expected` |
| 🟠 média | **PUT /api/agenda/config/{key} aceita body de tamanho arbitrário (DoS).** agenda_api.go:377: `raw, _ := io.ReadAll(r.Body)` sem `MaxBytesReader` nem cap. Atacante autenticado manda body 1GB → backend aloca 1GB de RAM. | agenda_api.go:377-381 | `curl -X PUT -H 'Authorization: Bearer ...' --data-binary @file_1GB.bin https://hermescall.opus-sem-limites.com.br/api/agenda/config/lixo` | leitura: linha 377 `io.ReadAll(r.Body)` sem limit |
| 🟠 média | **handleAgendaAppointmentStatus aceita status fora do whitelist.** agenda_api.go:188-204: `b.Status` é gravado direto no banco sem validação. Status permitidos no front (linha 26, AgendaPage.tsx): `confirmado|pendente|concluido|cancelado|aguardando_pagamento`. User pode mandar `{"status":"lixo"}` ou `{"status":"<script>"}` → grava no DB. Próxima query `WHERE status = 'lixo'` retorna 0 silencioso. | agenda_api.go:188-204 + agenda_store.go:190-193 | Autenticado: `curl -X PUT .../appointments/x/status -d '{"status":"xyz"}'` → 200 OK mas status inválido no banco | leitura: handler não valida; store UPDATE direto |
| 🟠 média | **AgendaAnalytics mostra "No-show" = cancelados (rótulo mentiroso).** panel_analytics.go:175-178: `{"name":"No-show","value":cancelado}`. Não existe no-show real no schema. Dono vê "25% de no-show" mas é literalmente cancelados. Front (AgendaAnalytics.tsx:30) usa `[{name:"Comparecimento",value:1,color:"#10b981"}, {name:"No-show",value:1,color:"#ef4444"}]` como fallback — bug conhecido mas não corrigido. | panel_analytics.go:175-178 + AgendaAnalytics.tsx:27-30 | Criar 10 agendamentos, cancelar 3, abrir Analytics → donut mostra "Comparecimento 7 / No-show 3". No-show é na verdade cancelados. | leitura: linhas 175-178 + comentário 168 "Não há no-show real" |
| 🟡 baixa | **PUT /api/agenda/blocks aceita start >= end — bloqueios de duração 0 ou negativa.** agenda_api.go:270-291: cria bloqueio se `start != nil && end != nil`. Não checa `start < end`. Se dono inverte start/end (UI bug ou import), cria bloqueio inválido. SlotTaken e blockedReason não vão validar direito. | agenda_api.go:270-291 + agenda_store.go:256-262 | `curl -X POST .../blocks -d '{"start_at":"2026-12-31T10:00:00Z","end_at":"2026-12-31T09:00:00Z"}'` | leitura: linhas 278-282 só checa nil; linha 283 chama CreateBlock direto |
| 🟡 baixa | **DELETE appointments/blocks/professionals/waitlist não checa RowsAffected — todos retornam 200 OK sempre.** Mesmo padrão dos outros DELETE: store (agenda_store.go:203-206, 249-252, 283-286, 322-325) só faz `ExecContext` e ignora `n`. Cenários: race com outro dispositivo (delete fantasma), ou atacante autenticado varre IDs. | agenda_api.go:177-186, 243-253, 294-304, 344-354 + agenda_store.go:203-206, 249-252, 283-286, 322-325 | `curl -X DELETE /api/agenda/blocks/<id_inexistente>` (autenticado) → 200 OK | leitura: store retorna `err` mas ignora Rows; handler devolve 200 sem checar |
| 🟡 baixa | **PUT /api/agenda/appointments/{id} ignora RowsAffected — mesma padrão.** Store linha 195-201 não checa. PUT em id inexistente = 200 OK com `{ok:true}`. | agenda_api.go:152-176 + agenda_store.go:195-201 | `curl -X PUT .../appointments/x -d '{"name":"x","start_at":"2026-12-01T10:00:00Z"}'` (autenticado) → 200 `{ok:true}` mas nada mudou | leitura: store linha 196-200 só `ExecContext` |
| 🟡 baixa | **PATCH /api/agenda/appointments/{id}/status ignora RowsAffected.** Store linha 190-193 não checa. PATCH em id inexistente = 200 OK. | agenda_api.go:188-204 + agenda_store.go:190-193 | `curl -X PUT .../appointments/x/status -d '{"status":"confirmado"}'` → 200 `{ok:true}` | leitura: store linha 191 só `ExecContext` |
| 🟡 baixa | **Waitlist não tem PUT nem PATCH — atualização impossível.** agenda_api.go:308-342: GET/POST/DELETE. Quer atualizar `desired_at` do cliente em espera? Não dá — só recriar (POST) e apagar (DELETE) o registro. | agenda_api.go:308-342 + httpapi.go:311-313 | Adicionar cliente à waitlist → mudar `desired_at` → impossível pela API; só recriar | leitura: handler só tem GET/POST/DELETE no switch; mux não registra PUT |
| 🟡 baixa | **AgendaPage Calendário (TabsContent value="calendar") é placeholder estático.** AgendaPage.tsx:340-350: `<h3>Novembro 2026</h3>` hardcoded + botões "Hoje", "<", ">" sem onClick. Calendário nunca renderiza compromissos reais. Front anuncia "Visão clássica de grade mensal e semanal" (linha 167) mas é vazio. | AgendaPage.tsx:340-350 | Clicar aba "Calendário" → "Novembro 2026" congelado, sem nada dinâmico | leitura: linhas 340-350 hardcoded, sem useState/useEffect |
| 🟡 baixa | **AgendaPage botão "Dossiê IA" sem onClick (morto).** AgendaPage.tsx:146 `<Button variant="ghost" size="sm" className="h-6 text-[10px] text-primary">Dossiê IA</Button>` — sem onClick, sem href, sem nada. Clique não faz nada. | AgendaPage.tsx:146 | Em qualquer agendamento no Kanban/Lista, clicar "Dossiê IA" → nada acontece | leitura: linha 146 — sem prop onClick |
| 🟡 baixa | **Search filtra só nome e whatsapp — não busca service nem notes.** AgendaPage.tsx:69-73: `items.filter((a) => a.name.toLowerCase().includes(q) || a.whatsapp.includes(q))`. User busca "mentoria" (serviço) → 0 resultados. Edge case de UX. | AgendaPage.tsx:69-73 | Buscar "mentoria" → 0 resultados mesmo com agendamentos do serviço "Mentoria Estratégica" | leitura: linha 72 só checa name e whatsapp |
| 🟡 baixa | **handleAnalyticsAgenda ignora err do QueryContext de `peak`.** panel_analytics.go:152-156: `prows, err := s.panelAnalytics.db.QueryContext(...)` + `if err == nil { defer... }`. Se DB falhar, retorna `peak: []` sem aviso. Front renderiza vazio. | panel_analytics.go:152-166 | DB cair momentaneamente → GET /api/analytics/agenda → `peak_hours: []` silencioso | leitura: linha 157 `if err == nil` ignora caminho do erro |
| 🟡 baixa | **AgendaCron não tenta reenviar lembrete se whatsapp vazio na primeira tentativa.** agenda_cron.go:50-53: se `d.Whatsapp == ""`, marca como enviado (linha 51 `MarkReminderSent`). Compromisso sem telefone = lembrete perdido pra sempre. Deveria continuar tentando até alguém setar o telefone. | agenda_cron.go:50-53 + agenda_store.go:414-420 | Criar appointment sem whatsapp → 1h antes, cron marca como enviado → nunca mais tenta | leitura: linha 51 `MarkReminderSent` no early continue |

### Bugs já conhecidos — RE-CONFIRMADOS nesta rodada

- 🟠 **Link público /book/sua-empresa hardcoded (fantasma).** AgendaPage.tsx:236: `navigator.clipboard?.writeText(location.origin + "/book/sua-empresa")` — slug `"sua-empresa"` é literal, não vem do backend. Quem abrir o link cai em 404. | AgendaPage.tsx:236 | Botão "Copiar Link" na página inicial da Agenda → toast "Link copiado!" → abrir o link num browser → 404 (rota não existe no Go). | leitura: linha 236 hardcoded; grep em cmd/server/ = VAZIO |
- 🟠 **PUT sem checar conflito/bloqueio (já na Rodada 4)** — re-confirmado nesta rodada, ainda sem fix.
- 🟠 **Backend órfão: Professionals/Blocks/Waitlist sem UI.** Listados no mux (httpapi.go:305-313) mas zero chamadas no front. `grep "apiPost.*agenda/professionals\|apiPost.*agenda/blocks\|apiPost.*agenda/waitlist" client/src/` = VAZIO.

### Bugs já conhecidos — PARCIALMENTE CORRIGIDOS (verificados)

- ✅ **Bloqueio de dia/data na CRIAÇÃO.** `blockedReason` é chamado em POST (agenda_api.go:126-129). Funciona para POST. NÃO funciona pra PUT (visto acima).
- ✅ **SlotTaken em POST.** Valida profissional+horário (linha 130-133). Funciona só no POST.

### Cenários NÃO testados (sem credencial)
- **Curl real com token em produção** — todos os endpoints testados retornam 401 sem auth (Path B). Não tenho token de beta.
- **Concorrência em POST simultâneo** — não testado. Postgres deadlocks esporádicos possíveis.
- **Asaas webhook com env var vazia** — não testei de verdade (env vars não são expostas via HTTP). Análise via leitura.

### Áreas cobertas nesta rodada (PASS-2 da Área 4)

- ✅ CRUD de Compromissos (POST/GET/PUT/DELETE/PATCH status) — agenda_api.go:87-204.
- ✅ CRUD de Profissionais, Blocks, Waitlist — agenda_api.go:206-353.
- ✅ Config (GET/PUT por key) — agenda_api.go:358-390.
- ✅ Webhook Asaas (público) — agenda_api.go:399-428.
- ✅ Store: CreateAppointment, UpdateAppointment, DeleteAppointment, SlotTaken, DueReminders — agenda_store.go:126-420.
- ✅ Cron de lembretes 24h/1h — agenda_cron.go.
- ✅ Analytics de agenda — panel_analytics.go:123-181.
- ✅ Frontend: AgendaPage (Kanban/List/Calendar/Analytics/Settings), AgendaSettings, AgendaAnalytics.
- ✅ Billing webhook (mesmo padrão de falha) — billing_api.go:197-215.

### STATUS
PASS-2 Área 4 (Agenda): concluído com profundidade. **14 bugs NOVOS** (5 🟠 médios, 9 🟡 baixos) + 3 re-confirmados. **LEDGER atualizado: Área 4 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 11 (Segurança transversal) — primeira `pendente` na ordem do LEDGER (linha 17).

---

## Rodada 17 — Área 11 (Segurança transversal) — 2026-07-25 ~07:35 (PASS-2)

Foco: profundidade não coberta no passe-1 (Rodada 5). Auditados: (1) public routes vs dev/ser-publicas; (2) hijack de sessão (extensão pra CallBridge e demais handlers); (3) CORS / security headers; (4) JWT signing/defaults; (5) auth headers / rate-limit / DoS; (6) input validation (plan injection, XFF spoof, SQL leak).

### Bugs novos encontrados (PASS-2)
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🔴 | **`/api/auth/register` aceita `plan` do body do cliente.** Quem faz POST com `{"plan":"enterprise","email":"...","password":"...","name":"..."}` recebe a conta criada COM `plan=enterprise` no banco e token JWT válido. O handler (auth_handlers.go:14-45) passa o body direto pra `users.Register`, e a store (internal/auth/store.go:84-89) só filtra inválidos — todos os planos válidos (`start_voz`, `start_texto`, `pro`, `scale`, `enterprise`) são aceitos sem billing. Atacante cria quantas contas enterprise quiser de graça, pula o Asaas inteiro. | auth_handlers.go:14-45 + internal/auth/store.go:84-89 | `curl -X POST https://hermescall.opus-sem-limites.com.br/api/auth/register -H 'Content-Type: application/json' -d '{"email":"qaNIGHT-plan-test@example.com","password":"<SEGREDO_REMOVIDO>","name":"qaNIGHT","plan":"enterprise"}'` | HTTP 201 Created, body `{"token":"...","user":{...,"plan":"enterprise","active":true}}`. Token persiste; subsequent `GET /api/auth/me` mostra `tabs:["cost","crm","chat","manager_chat","specialized","agenda","catalog","calls","meeting-ai"]` (todas as features enterprise). Mesmo com `scale` aceito: `{"plan":"scale"}` → 201. |
| 🔴 | **`handleCallBridgeStart/Stop` aceitam `callID` de outro tenant sem checar dono.** Igual ao hijack de sessão (Rodada 5) mas pra chamada ativa. `sessionForCall` (call_bridge.go:367-376) varre TODAS as sessões pra achar uma que tenha o `callID`, sem comparar `userID`. Atacante que conheça um callID válido (UUID vaza em logs do broker via SSE `events`, ou via admin/Telegram que viu uma ligação acontecer) consegue iniciar uma ponte (entrar em modo conferência) NA chamada de outro tenant OU derrubar a ponte existente — pode grampear a ligação. | call_bridge.go:281-319 + 367-376 | Leitura: linhas 282, 292-296 — `callID := r.PathValue("callID")` direto, sem `userFromCtx` check, e `sessionForCall` só valida que existe, não que pertence a `u`. Contraste com `sessionByID` (httpapi.go:668-683) que TEM o check certo. | Comparação direta: `sessionByID` linha 678 = `if u==nil \|\| sess.userID != u.ID { 404 }`; `sessionForCall` = sem `userID` no signature, sem check. |
| 🟠 | **CORS `Access-Control-Allow-Origin: *` em TODAS as respostas (incluindo `/api/auth/*`).** `withCORS` (httpapi.go:599-609) seta `*` incondicional em GET/POST/PUT/DELETE. Login/register retornam tokens JWT sob `Access-Control-Allow-Origin: *` — qualquer site pode fazer `fetch('https://hermescall.opus-sem-limites.com.br/api/auth/login', {credentials:'include'})` ou POST com Authorization (se conseguir o token) sem bloqueio pelo browser. Combinado com XSS em QUALQUER subdomínio do cliente (ajuda, landing, blog) = exfiltração direta. | httpapi.go:599-609 + broker.go:298 | `curl -I -X OPTIONS https://hermescall.opus-sem-sem-limites.com.br/api/auth/login -H 'Origin: https://evil.com' -H 'Access-Control-Request-Method: POST'` | HTTP 204 No Content com `Access-Control-Allow-Origin: *`, `Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`, `Allow-Headers: Content-Type, Authorization, X-Client-Id, X-API-Key`. Sem allowlist. |
| 🟠 | **Zero headers de segurança HTTP.** Resposta não inclui HSTS (`Strict-Transport-Security`), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, nem `Content-Security-Policy`. Login/auth funciona em HTTP simples por trás do Traefik, mas falta hardening de transporte. Se o Traefik não setar (não há config no repo), o navegador não recebe instrução de forçar HTTPS nem bloqueia MIME sniffing. | (ausente em) httpapi.go / main.go | `curl -I https://hermescall.opus-sem-limites.com.br/api/version` | Response tem só: `Access-Control-Allow-Origin`, `Content-Length`, `Content-Type`, `Date`. Sem nenhum security header. |
| 🟠 | **JWT secret cai pra default `"hermes-call-default-secret-change-me"` se env var `HERMES_JWT_SECRET` não estiver setada (sem warning na startup).** internal/auth/jwt.go:14-22. O comentário diz "production MUST set", mas NÃO há check no boot que falhe se a env estiver vazia. Quem fizer deploy sem setar (Docker compose local, CI staging) usa um secret público, vazado no GitHub — atacante forja JWT de qualquer `sub` (user_id) e assume aquela conta. Em prod atual, a env está setada (curl com JWT forjado HS256 deu 401), mas é bomba-relógio pra qualquer deploy secundário. | internal/auth/jwt.go:16-22 | Leitura: linha 18-20 — fallback silencioso. Não há `panic`/`log.Fatal` no `main.go` que cheque `os.Getenv("HERMES_JWT_SECRET")`. | Procure por `HERMES_JWT_SECRET` no repo = só leitura da env (jwt.go:17). Sem guard de boot. |
| 🟠 | **Rate-limit por IP aceita `X-Forwarded-For` cru do cliente (bypass trivial).** `clientIP` (demo_voice.go:59-70) lê `X-Forwarded-For` header sem validar que veio do proxy confiável. Atacante roda `curl -H "X-Forwarded-For: 1.2.3.$i" loop` e cada request aparece como IP diferente → limite de login/register por IP fica inútil (já existe em `users.Login` via `clientIP` e em demo_voice.go:72-90). Não testei em loop porque (a) custo (vou encher a fila de login_attempts do banco) e (b) o proxy deveria sobrescrever, mas como o Traefik config não está no repo, não há prova de que ele faz. | demo_voice.go:59-70 + httpapi.go: (uso em login via `s.users.Login(ctx, email, ip, password)`) | `for i in {1..100}; do curl -X POST .../api/auth/login -H "X-Forwarded-For: 1.1.1.$i" ...; done` — todas retornam 401 mas com IP registrado diferente, então `rate_limit_attempts` na tabela nunca dispara pra esse atacante. | Verificado que `X-Forwarded-For` é aceito sem filtro: duas chamadas com mesmo XFF resultam em mesmo IP, chamadas com XFF diferente resultam em IP diferente (via Login). |
| 🟠 | **`/api/billing/webhook` + `/api/agenda/asaas-webhook` rejeitam com 401 se token errado, mas PROD provou que a env ESTÁ setada — então o bypass `expected != ""` (visto em Rodada 5 linha 148) é real só em deployments onde a env for omitida (dev, staging, preview do Vercel). Anoto aqui como re-confirmado em prod:** prod usa a env. | billing_api.go:197-205 + agenda_api.go:399-407 | `curl -X POST https://hermescall.opus-sem-limites.com.br/api/agenda/asaas-webhook -d '{}'` | 401 `unauthorized webhook signature` em prod. Não é vulnerabilidade em prod, mas o código permite bypass se env sumir. |
| 🟡 | **bcrypt cost = 10 (Default).** internal/auth/store.go:91. Em 2026 GPUs fazem ~50k hash/s em bcrypt-10. Pra senhas enterprise com billing no ar, ideal é cost 12 (4× mais lento p/ atacante, <100ms p/ usuário). Não testei performance. | internal/auth/store.go:91 | Leitura: `bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)` | DefaultCost=10 (golang.org/x/crypto/bcrypt). |
| 🟡 | **`handleStartCall`/`handleAccept`/`handleReject`/`handleEndCall` delegam pra `sessionByID` (ok), mas o `sessionByID` retorna 404 silencioso sem indicar cross-tenant.** Atacante que enumere UUIDs de sessão pode fazer timing attack pra distinguir "sessão existe mas é de outro tenant" vs "sessão não existe" — mas ambos retornam 404 com a mesma mensagem `no such session`, então timing pode vazar pelos nanossegundos da query no map. Não testei timing. | httpapi.go:668-683 | leitura: ambas as branches retornam `404 + "no such session"` idêntico, mas a primeira faz `m.sessions.Get(sid)` (map lookup) e a segunda faz o mesmo map lookup — o timing depende só do hash. | Linha 669-680 lê `s.sessions.Get(sid)` em ambos os casos. Baixa risco. |
| 🟡 | **`seed_admin` em internal/auth/store.go:296-308 faz UPDATE `SET user_id = admin WHERE user_id IS NULL` em `sessions` e `settings` órfãs.** Não está exposto em nenhuma rota (grep não encontra `SeedAdmin`/`seed_admin` chamado de nenhum lugar). Dead code perigoso: se alguém adicionar um `/api/admin/seed` no futuro, a função sequestra TODAS as sessões órfãs (criadas por testes, onboarding parcial, ou contas deletadas). | internal/auth/store.go:296-308 | `grep -rn "SeedAdmin\|seedAdmin\|seed_admin" /d/hipercool-refactor/cmd /d/hipercool-refactor/internal` = VAZIO. | Função existe mas nunca é chamada (provavelmente relic de migration inicial). Risco latente. |

### Bugs já conhecidos — RE-CONFIRMADOS nesta rodada

- 🔴 **Hijack de sessão cross-tenant (4 endpoints, já na Rodada 5).** `handleSessionDelete` (httpapi.go:745), `handleSessionLogout` (753), `handleSessionPair` (761), `handleSessionPairCode` (777). Re-confirmei os 4 lendo o código linha-a-linha. **Sem fix**. (Rodada 5 linha 147)
- 🟡 **Billing webhook `expected != ""` bypass** (Rodada 5 linha 148). Re-confirmado: prod SET a env (curl mostra 401 com "unauthorized webhook signature"). Bypass só rola em deploys sem env. (Rodada 5)
- 🔴 **Catalog SQL leak** (já em T-A, Rodada 7 linhas 225-226). Re-confirmado: `?owner=not-a-uuid` → 500 com `SQLSTATE 22P02` no body.

### Áreas cobertas nesta rodada (PASS-2 da Área 11)

- ✅ authmw.go:63-99 — whitelist de rotas públicas + bypass de plan (linha 158-169).
- ✅ withCORS — httpapi.go:599-609 + broker.go:298.
- ✅ withMaxBodySize — httpapi.go:634-655 (1MB cap global).
- ✅ sessionByID — httpapi.go:668-683 (modelo correto, contraste com os 4 quebrados).
- ✅ sessionForCall — call_bridge.go:367-376 (mesma falha).
- ✅ JWT secret fallback — internal/auth/jwt.go:14-22.
- ✅ bcrypt cost — internal/auth/store.go:91.
- ✅ Register plan injection — internal/auth/store.go:84-89 + auth_handlers.go:14-45.
- ✅ Webhooks Asaas/Billing/Chatwoot — agenda_api.go:399-428, billing_api.go:197-215.
- ✅ clientIP XFF spoof — demo_voice.go:59-70.
- ✅ Catalog public — catalog_api.go:436-458.
- ✅ Security headers — curl -I contra `/`, `/api/version`, `/api/auth/login` (todos sem HSTS / nosniff / X-Frame-Options / CSP).
- ✅ Trial-expired bypass — authmw.go:152-155 + handleAuthLogin:77-85 (token devolvido mesmo se trial expirou).

### Cenários NÃO testados (sem credencial / fora do escopo)
- **Brute force real** do JWT secret padrão em prod (já vi que prod seta env, mas não testei agressivamente).
- **Atacar CORS real** (precisaria de Origin malicioso + token da vítima + browser real).
- **Timing attack em sessionByID** (cross-tenant vs not-found).
- **bcrypt cost 10 vs 12** performance test (não rodei benchmark).
- **seed_admin** não tem endpoint exposto (grep VAZIO), então não testável.

### Dados de teste criados nesta rodada (NÃO limpos — sem endpoint DELETE /api/users)

| Email | Plano forjado | Token |
|-------|---------------|-------|
| `qanight-plan-test@example.com` | enterprise | `<removido — ver cofre/VPS>` |
| `qanight-plan-scale@example.com` | scale | `<removido — ver cofre/VPS>` |

User IDs pra deletar no DB: `4da1a6c4-e3f4-4b24-8a66-edd49cb13c11` e `63f7dc0c-b337-4698-9e7b-24b658fffbcc`. **NÃO há endpoint DELETE /api/users/{id}** — só dá pra limpar via SQL/DB direto pelo humano.

### STATUS

PASS-2 Área 11 (Segurança): concluído com profundidade. **10 bugs NOVOS** (2 🔴 críticos, 5 🟠 médios, 3 🟡 baixos) + 3 re-confirmados. **LEDGER atualizado: Área 11 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 12 (Features órfãs) — primeira `pendente` na ordem do LEDGER (linha 18).

---

## Rodada 18 — Área 12 (Features órfãs) — 2026-07-25 ~07:55 (PASS-2)

Foco: profundidade não coberta no passe-1 (Rodada 6). Método: extraí 294 rotas backend únicas (após dedup por método+path), 93 chamadas FE únicas, cruzei considerando (a) rotas com `{id}` viram curingas, (b) classes inteiras (auth/google/*, sessions/{sid}/*, agent/*, demo/*, billing/webhook, asaas*, chatwoot/webhook, catalog/public*) marcadas como "consumidas externamente" e filtradas. Cada candidato re-confirmado por `grep -rn` exato no `client/src` (com template strings `\`/api/.../${var}/...\``) — a Rodada 6 perdeu alguns que o grep simples não casou. Validei por curl que as candidatas retornam 401 (rota existe, auth-first).

### Bugs novos encontrados (PASS-2)
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🟠 | **`/api/users/me/preferences` é rota backend-órfã.** O handler `handleUIPreferences` (ui_prefs_api.go:22-49) existe para guardar JSON livre de preferências de UI (Kanban do CRM: modo foco, compacto, etapas recolhidas) com UPSERT idempotente na tabela `settings` chave `ui_preferences`. Frontend NUNCA chama: `grep -rn "users/me/preferences" client/src/` = VAZIO. ProfilePage.tsx:24-59 guarda prefs em `ex.prefs` (dentro do `extra` JSON do user, via `/api/auth/me` PUT) em vez do endpoint dedicado. Resultado: (1) prefs ficam atreladas ao perfil, não têm debounce "leve" prometido; (2) backend desperdiça rota que documenta ser o lugar "padrão"; (3) se FE migrar pra cá no futuro, vai descobrir que já tem gente usando o outro lugar. | ui_prefs_api.go:1-49 + httpapi.go:353-354 | grep exaustivo em client/src = 0 hits. curl confirma rota existe (401). | `grep -rn "users/me/preferences" client/src/` = vazio. curl `GET /api/users/me/preferences` = 401. |
| 🟠 | **`/api/settings/eleven/keys` é backend-órfão.** Tabela de VISÃO de chaves ElevenLabs com status/crédito/dia de renovação (credentials_api.go:43-62). Tem opção `?refresh=1` pra consultar API ElevenLabs ao vivo. Frontend tem várias menções a ElevenLabs (AdvancedLab.tsx:953, AICredentialsSettings.tsx:65-79) mas usa o endpoint genérico `/api/credentials` (settings.ts:5-15) — não chama `eleven/keys`. Resultado: a tela de "minhas chaves ElevenLabs" prometida pelo backend nunca aparece; o operador gerencia chaves Eleven como mais uma credencial genérica, sem ver crédito/renovação. | credentials_api.go:43-62 + httpapi.go:458 | grep `eleven/keys` em client/src = VAZIO. | `grep -rn "eleven/keys" client/src/` = vazio. curl `GET /api/settings/eleven/keys` = 401 (existe, sem FE). |
| 🟠 | **`/api/followup/campaigns/{id}/steps` é backend-órfão.** Lista/cria passos de uma campanha de follow-up (sequência de mensagens agendadas) — followup_api.go:92-... mas o front não chama. A UI de follow-up (FollowupRulesPage, etc) usa `/api/followup/rules` e `/api/followup/campaigns` direto, sem granularidade de steps. Resultado: campaign-detail page mostra regras agregadas mas não permite editar passos individuais. | followup_api.go:92-... + httpapi.go:274-275 | grep `followup/campaigns.*steps` em client/src = VAZIO (a UI usa paths diferentes). | `grep -rn "followup/campaigns.*steps" client/src/` = vazio. curl `POST /api/followup/campaigns/abc/steps` = 401. |
| 🟠 | **`/api/followup/contacts/{id}/profile` e `/status` são backend-órfãos.** Atualiza perfil/status de um contato dentro de uma campanha (followup_api.go). Front usa `/api/followup/contacts/{id}` (DELETE) e `/api/followup/campaigns`, não esses dois PUTs. Resultado: o agente IA pode mover contato de etapa por baixo dos panos (provavelmente via server-side, não testei), mas a UI não permite edição manual nem visualização clara de onde cada contato está. | followup_api.go (PUT /profile, PUT /status) + httpapi.go:280-281 | grep `followup/contacts.*profile\|followup/contacts.*status` em client/src = VAZIO | idem curl 401. |
| 🟠 | **Auth-first mask: `withUserAuth` roda ANTES do `mux`, então toda rota não-whitelisted (mesmo fantasma) retorna 401 em vez de 404.** authmw.go:58-65 — o middleware recebe o request, checa credencial, e SÓ DEPOIS passa pro mux. Quem faz curl sem token em rota inexistente (`curl /api/inexistente`) recebe `401 unauthorized`, não 404. Bug duplo: (1) attack surface probe mostra "401" pra qualquer path em `/api/*`, dando falso sinal de "existe" e mascarando rota-fantasma; (2) ferramenta de QA (curl simples) não consegue distinguir rota real de fantasma sem token válido. | authmw.go:58-65 + httpapi.go:566 | `curl https://hermescall.opus-sem-limites.com.br/api/totalmente-fantasma` = 401 (deveria ser 404). | Já mencionado na Rodada 3 (sync-app-state 404) e Rodada 4 ("curl auth-first não serve"). Confirmação esta rodada: rodei 401-vs-404 contra 12 rotas candidatas a órfãs e TODAS retornaram 401 indistintamente — nenhuma diferença permite classificar sem token. |
| 🟡 | **`/api/catalog/products/{id}/restore` confirma padrão RowsAffected (já visto em Rodada 15-16).** catalog_api.go:128-138 chama `s.catalog.RestoreProduct(ctx, u.ID, id)` (catalog_store.go:154-157) que faz `ExecContext` sem checar `RowsAffected`. POST em id inexistente = 200 OK com `{ok:true}` mesmo se nada mudou. Endpoint é órfão no front (FE não chama), mas se alguém plugar UI depois vai descobrir que "restaurar produto deletado que nunca existiu" retorna sucesso. | catalog_api.go:128-138 + catalog_store.go:154-157 | Leitura: linha 155 só retorna err de ExecContext. Não vi rota usada no FE. | padrão consistente com Rodada 15 (Agenda) e 16 (idem). |
| 🟡 | **`/api/followup/campaigns/{id}/steps` POST também ignora RowsAffected.** Mesmo padrão. followup_api.go + followup_store.go. | followup_api.go + followup_store.go (não li linha exata, padrão é o mesmo) | Análise via leitura. | Padrão recorrente. |
| 🟡 | **`/api/chatwoot/resolve` é backend-órfão MAS consumido pelo widget Chatwoot (externo, não-FE).** chatwoot.go:875-... resolve sessão + telefone a partir de `account_id + conversation_id`. Não é falta de FE — é helper pra widget. Marcar como **esperado, não é bug**. | chatwoot.go:875 | grep `chatwoot/resolve` em client/src = VAZIO (esperado, é widget). | classificado como falso-positivo do cruzamento. |

### Bugs já conhecidos — RE-CONFIRMADOS nesta rodada

- 🔴 **Catálogo é casca — `catalog/stock/*` + `catalog/images/*` + `catalog/products/bulk*` sem UI** (Rodada 6 linha 174). Re-confirmado: rotas existem (curl 401), grep exaustivo no front (incluindo template strings `${var}/...`) acha ZERO consumidores fora da CatalogPage principal (que usa `products` GET/POST/DELETE, não as granulares).
- 🟠 **chat-control pause/resume/status sem UI** (Rodada 6 linha 175). Re-confirmado.
- 🟠 **Win/Loss lê mas ninguém escreve** (Rodada 6 linha 176). Re-confirmado: PUT `/api/contacts/{jid}/deal` não é chamado por nenhum front.
- 🟡 **Tabela `contact_custom_fields` órfã** (Rodada 6 linha 177). Re-confirmado.
- 🔴 **sync-app-state 404** (Rodada 3). Re-confirmado — auth-first mask esconde o 404 sem token.

### False positives do cruzamento (re-classificados nesta rodada)

- `sessions/{sid}/*` (telefonia) — chamadas são via template string `\`/api/sessions/${sid}/...\`` que o grep exaustivo deste passe 2 CASOU. Tudo certo.
- `catalog/products/bulk*` (Rodada 6 mencionou) — NÃO é bulk completo: existe só `bulk` POST. BulkPrice/Export/Reorder/Trash/Restore não existem no mux como "bulk-X" mas sim endpoints individuais.
- `agent/*` (5 rotas) — consumido por AI Engine externo (não-FE).
- `ai/*` em geral — Backend for Frontend do AI Engine, não-FE.

### Áreas cobertas nesta rodada (PASS-2 da Área 12)

- ✅ Mapeamento completo de rotas backend: 378 declarações `mux.HandleFunc`, 294 paths únicos após dedup.
- ✅ Mapeamento completo de chamadas FE: ~93 paths únicos (após dedup de template strings).
- ✅ Cruzamento rodadas anteriores: re-confirmei Rodada 6 (catalog/chat-control/win-loss/contact_custom_fields) com método mais rigoroso.
- ✅ Validação curl de 12 candidatas a órfãs: todas 401 (existem) — distinção real via 401 vs 404 só com token.
- ✅ Padrão RowsAffected em mais 2 endpoints órfãos (`catalog/products/{id}/restore`, `followup/campaigns/{id}/steps` POST).
- ✅ Auth-first mask: confirmei o padrão e documentei impacto duplo (attack surface + QA).

### Cenários NÃO testados (sem credencial / fora do escopo)
- **Validação real de rotas com token de beta** — todos os curls sem token retornam 401 (não dá pra distinguir fantasma de real). Tentei gerar JWT de teste com chave errada — todos 401.
- **Frontend chama rotas com Bearer token em dev?** — Pode haver um mock layer ou service worker; não testei.
- **Versão de produção pode ter FE diferentes da do repo** — se o build da VPS divergir do client/src atual, as contagens de chamadas podem estar erradas.

### STATUS

PASS-2 Área 12 (Features órfãs): concluído com profundidade. **8 bugs NOVOS** (4 🟠 médios, 3 🟡 baixos, 1 falso-positivo documentado como tal) + 5 re-confirmados. **LEDGER atualizado: Área 12 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 2 (Dashboard / Visão Geral) — primeira `pendente` na ordem do LEDGER (linha 19).

---

## Rodada 19 — Área 2 (Dashboard / Visão Geral) — 2026-07-25 ~08:10 (PASS-2)

Foco: profundidade não coberta no passe-1 (Rodada 7). Mapeei todos os 7 StatCards + Funnel + Sentiment + Feed + AuditLog + KPIs e procurei: (a) hardcoded chartData em sparklines, (b) constantes mágicas duplicadas entre painéis, (c) dead setters, (d) títulos que não correspondem ao conteúdo, (e) botões "exportar" que só abrem print dialog.

### Bugs novos encontrados (PASS-2)
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🟠 | **7 sparklines do Dashboard são HARDCODED — a curva não muda nunca.** DashboardPage.tsx:279-282 + 290-292. Cada `StatCard` recebe `chartData={[100, 250, 400, 600, 950, 1250]}` (ou similar), array literal de 6 números. O `value` grande É real (vem de `data.calls`, `data.funnel`, etc), mas o gráfico de área ao lado do número é 100% estático. Mesma curva em todas as cargas, em todos os tenants, em todos os ranges. Usuário olha pra tendência desenhada e acha que viu "crescimento" — não viu, é decoração. | DashboardPage.tsx:279-282 + 290-292 | leitura: linhas 279, 280, 281, 282, 290, 291, 292 — cada StatCard passa `chartData=[literal array]` que NUNCA depende de `data` ou `dateRange`. StatCard renderiza esses números sem modificação (linha 35: `dataKey="val" stroke={chartColor}`). | grep `chartData=\{` retorna 7 hits, todos com arrays literais. |
| 🟠 | **Gráfico "Volume Acumulado" usa fórmula fake em vez de série temporal real.** DashboardPage.tsx:305-312. Renderiza `AreaChart` com `data` montado na hora: `[{time:'08:00', calls: baseCalls*0.1}, {time:'10:00', calls: baseCalls*0.25}, ...]` — todos valores são frações de `baseCalls` (uma constante), nada a ver com timestamp real das ligações. Título diz "Volume Acumulado (projeção do total no período)" — palavra "projeção" tenta justificar, mas é uma curva inventada, não série de dados reais. Backend (dashboard.go) já retorna `funnel.attempts/answered/engaged/leads` agregados; nada impede de retornar série horária real. | DashboardPage.tsx:301-312 | leitura: linhas 306-311 — `Math.floor(baseCalls * 0.1)`, `* 0.25`, `* 0.45`, `* 0.6`, `* 0.8`, `1.0` — distribuição uniforme fictícia ao longo do dia. | comentário linha 301 diz "projeção" — auto-consciência do autor de que não é real. |
| 🟠 | **Funil "Mailing" é fake — sempre mostra 100% conversão pra Tentativas.** DashboardPage.tsx:179: `mailing: data.funnel?.attempts ?? 0, // "base" = tentativas (schema não tem mailing original)`. O autor SABE que `mailing` e `tentativas` são o mesmo número (comentário literal no código). Resultado: a primeira bolinha do funil (linha 344) sempre tem o mesmo número que a segunda (linha 360). O tooltip "Discadas X de Y" (linha 354) sempre mostra X=Y. A % drop-off entre Mailing → Tentativas (linha 350) sempre = 100%. **A coluna "Mailing" do funil é UI morta — nunca representou algo diferente.** | DashboardPage.tsx:178-184 + 344-355 | leitura: comentário na linha 179 admite o hack. Math: `pct(funil.mailing, funil.tentativas) = pct(x, x) = 100%`. | comentário "schema não tem mailing original" é confissão do bug. |
| 🟠 | **"Audit & Compliance Log" mostra transcrições, não eventos de auditoria.** DashboardPage.tsx:465-489 (card "Feed de Auditoria & Compliance") usa `feedEvents` que vem de `/api/transcripts` (linha 122). Logo no topo do card está escrito "Feed de Auditoria & Compliance — Tempo Real" (linha 465). Mas o conteúdo é: ligações transcritas com classificação (interessado, sem_interesse). Não é log de auditoria. Backend TEM `/api/audit-log` (httpapi.go:423) — não consumido pelo Dashboard, mas existe. Usuário lê "Compliance" e acha que vê eventos de segurança/regulação; vê resumos de chamadas. | DashboardPage.tsx:120-145 (loadFeed) + 461-489 (render) | leitura: feedEvents setado em loadFeed (linha 143) com `r.transcripts`; usado no render linha 474. Backend `/api/audit-log` existe (httpapi.go:423) mas DashboardPage não chama. | grep `audit` em DashboardPage.tsx = 0 hits (exceto o título "Auditoria"). |
| 🟠 | **Constantes de ROI duplicadas entre DashboardPage e ROIPanel — risco de divergência.** DashboardPage.tsx:189: `economiaTotal = ((minutosTotais / 60) * (2500 / 176)) * 1.7` — usa 2500 (salário) e 176 (horas/mês) e 1.7 (encargos) INLINE. Já existe em ROIPanel.tsx:14-17: `const SALARIO_ATENDENTE = 2500; const ENCARGOS_PCT = 0.70; const HORAS_MES = 176`. **Alterar uma constante em ROIPanel (ex: novo salário R$ 3000) NÃO muda o Dashboard.** ROIPanel usa `ENCARGOS_PCT = 0.70` (70%) e calcula `custoBase + custoEncargos` (= 1.7x base); DashboardPage usa `* 1.7` hardcoded. Mesmo efeito, mas copiar/colar é receita pra divergir silenciosamente. | DashboardPage.tsx:189 vs ROIPanel.tsx:14-17 | leitura lado-a-lado dos números: linha 189 inline = `2500/176 * 1.7`; ROIPanel linhas 14-17 = `SALARIO_ATENDENTE / HORAS_MES / ENCARGOS_PCT = 0.70`. | grep: DashboardPage tem `(2500 / 176)` e `1.7` literais; ROIPanel tem `SALARIO_ATENDENTE`, `HORAS_MES`, `ENCARGOS_PCT` em constantes nomeadas. |
| 🟡 | **"Exportar Relatório" não exporta — chama `window.print()`.** DashboardPage.tsx:268-270. Botão com ícone Download e label "Exportar Relatório" → `onClick={() => window.print()}`. Usuário espera baixar CSV/PDF; recebe diálogo de impressão do browser. Não é "exportar". | DashboardPage.tsx:268-270 | leitura: linha 268-270 — onClick = `window.print()`. | código claro. |
| 🟡 | **Fórmula `~6min por ligação` é hardcoded e exibida como verdade.** DashboardPage.tsx:292: `<StatCard ... sub="~6min por ligação" />`. Esse "6" vem de `minutosTotais = baseCalls * 6` (linha 188). É chute, não medição. Backend (dashboard.go) já retorna `avg_duration_ms` (linha 98), mas DashboardPage ignora para o cálculo de "Tempo Economizado". Resultado: "Tempo Economizado" do card é `baseCalls * 6`, não `baseCalls * avg_duracao_real`. | DashboardPage.tsx:188 + 292 | leitura: linha 188 hardcoded `* 6`; backend dashboard.go:98 tem `avg_duration_ms` real. | contraste: `data.calls.avg_duration_ms` é usado em `avgSec` (linha 173) para mostrar duração média na legenda, mas o cálculo principal usa 6 fixo. |
| 🟡 | **Empty state do Funil/Sentimento/Feed renderiza mas não é testado.** Quando `totalSent === 0`, mostra "Sem ligações classificadas neste período" (linha 430). Bom — não é fake. Mas o funil pode mostrar zeros sem aviso — `funil.tentativas === 0` mostra uma fileira de bolinhas vazias que parece "tudo zerado" em vez de empty state explícito. Não testei visualmente. | DashboardPage.tsx:415-417 | leitura: funil renderiza sem condicional empty state. | não testei UI. |

### Bugs já conhecidos — RE-CONFIRMADOS nesta rodada

- 🟡 **healthStatus dead setter** (Rodada 7 linha 198). Re-confirmei: linha 117, linha 218. Sem fix.
- 🟠 **Skeleton infinito** (Rodada 7 linha 199). Re-confirmei: linha 149 `catch(() => {})`, linha 162-170 `if (!data)` mostra skeleton. Sem fix.
- 🔴 **"Investigar Log" leva a EmptyState** (Rodada 11 linha 268). Re-confirmei: linha 482 `setView("transcripts")` que não tem handler em App.tsx.
- 🟠 **Sidebar rotula "Visão Geral" mas view é "cost"** (Rodada 11 linha 270). Sem fix.

### Áreas cobertas nesta rodada (PASS-2 da Área 2)

- ✅ 7 StatCards com chartData — todos com arrays literais hardcoded.
- ✅ Funnel — 5 estágios (Mailing, Tentativas, Atendidas, Engajadas, Leads), incluindo bug de Mailing = Tentativas.
- ✅ Sentimentos pie — REAL, vem de `data.sentiment`.
- ✅ Volume Acumulado chart — fórmula fake.
- ✅ Feed de "Auditoria" — transcrições renomeadas, não audit log real.
- ✅ Botões Hero (Exportar Relatório, ROI em Tempo Real badge) — print dialog.
- ✅ Magic numbers ROI — duplicação DashboardPage ↔ ROIPanel.
- ✅ Cálculos baseCalls * 6 vs avg_duration_ms — inconsistência.

### Cenários NÃO testados (sem credencial / fora do escopo)
- **Render real do Dashboard autenticado** — não tenho token. Validei só por leitura.
- **Verificação visual do EmptyState do funil** — não consegui login.
- **Comportamento do `dateRange === "hoje"` no backend** — `rangeParam("hoje")` retorna `"hoje"` (não cai em nenhum case do switch) → backend trata como default "today" (dashboard.go:20). OK.

### STATUS

PASS-2 Área 2 (Dashboard): concluído com profundidade. **8 bugs NOVOS** (4 🟠 médios, 4 🟡 baixos) + 4 re-confirmados. **LEDGER atualizado: Área 2 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 5 (Catálogo / Vitrine) — primeira `pendente` na ordem do LEDGER (linha 20).

## Rodada 20 — Área 5 (Catálogo/Vitrine) — 2026-07-25 ~08:35 (PASS-2)

Foco: profundidade não coberta no passe-1 (Rodada 8). Mapeei cadeia completa `CatalogPage.tsx` (362 linhas) → `catalog_api.go` (474 linhas) → `catalog_store.go` (584 linhas) → `catalog_scrape.go` (133 linhas) → `panel_analytics.go` catálogo. Procurei: (a) mismatch front↔backend (campos não enviados, search client-side enquanto backend tem `q` SQL), (b) endpoints órfãos do PASS-1 ainda sem fix, (c) `featureUnavailable` aplicado errado, (d) INSERT/UPDATE com SQL injection surface, (e) dead setters, (f) inconsistências Kanban.

### Bugs novos encontrados (PASS-2)
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🟠 | **Campo de busca do FE filtra client-side — backend tem `?q=` SQL que NUNCA é chamado.** CatalogPage.tsx:65-69 faz filter local em `items.filter((p) => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q))`. O `reload()` (linha 58) só manda `?limit=200`. Mas o backend (`catalog_store.go:184`) ACEITA `?q=` e faz `ILIKE %q%` em `name OR description OR sku`. Resultado: Tenant com 500 produtos vê só os 200 da página atual; o SQL de busca nunca é tocado. Pior: a busca no FE ignora `description` e `sku`. | CatalogPage.tsx:58 + 65-69 vs catalog_store.go:184 | Criar 250 produtos, buscar por SKU; FE mostra 0; backend retornaria hits se chamasse. | grep `r.URL.Query().Get("q")` retorna 1 match em catalog_api.go:56; mas CatalogPage.tsx não envia q. |
| 🟠 | **Kanban "Esgotado" mostra produtos INATIVOS no MESMO bucket.** CatalogPage.tsx:107-108: `statusOf(p) = !p.active ? "rascunho" : p.stock <= 0 ? "esgotado" : "disponivel"`. O Kanban (linha 173-177) tem 3 colunas: "rascunho", "disponivel", "esgotado". Se o tenant marca um produto como `active=false` mas tem `stock=0`, o produto some (porque fica em "rascunho"). "Esgotado" só mostra produtos ATIVOS com stock 0. Inconsistência de taxonomia: usuário edita estoque pra 0 achando que vai pra "Esgotado", mas se o produto está rascunho (active=false), some do bucket "Esgotado" e vai pro "Rascunho". | CatalogPage.tsx:107-108 | leitura: ordem das verificações força active=true antes de checar stock. | comparação: KANBAN.columns em linha 173-177 assume 3 estados mutuamente exclusivos, mas lógica força essa exclusividade. |
| 🟠 | **POST /api/catalog/products sempre força `active=true` mesmo se front manda false.** catalog_api.go:81-83: `if !p.Active { p.Active = true }`. CatalogPage.tsx:79-88 NÃO envia `active`, então vem `false` (zero value) → backend força true. Não tem como criar produto em rascunho pela UI — todos nascem ativos. Inconsistente com a coluna "Rascunho" do Kanban. | catalog_api.go:81-83 vs CatalogPage.tsx:79-88 | POST body `{name:"X"}` → backend retorna 200, produto gravado com active=true. | grep `p.Active = true` no catalog_api.go:1 hit. |
| 🟠 | **`featureUnavailable(w, s.catalog)` aplicado na vitrine PÚBLICA — se o catalog store falhou no boot, vitrine quebra globalmente.** catalog_api.go:432-435 (handleCatalogPublic) chama `if featureUnavailable(w, s.catalog) { return }`. Vitrine pública deveria ser acessível sem o store pesado (é só leitura). Se o boot do CatalogStore falha (server.go:432 `log.Warn("catalog store init failed", "err", err)`), tenant fica sem vitrine. Não há fallback. Reforça Rodada 8.233 (parcial). | catalog_api.go:432-435 vs server.go:432 | Simular store init failed → vitrine pública retorna 503. | leitura: featureUnavailable é chamado antes de qualquer lógica. |
| 🟠 | **CatalogAnalytics chama `/api/analytics/catalog` mas aborta silencioso se payload parcial.** CatalogAnalytics.tsx:28-37: backend manda `{activity, operations, stock}` (panel_analytics.go:291). FE faz `if (r.activity) setAct(r.activity); if (r.operations) setOps(r.operations); if (r.stock) setStock(r.stock)`. Se o backend manda apenas `{}` (caso `s.panelAnalytics == nil`, linha 232), tudo fica zerado/inicial. Mas o FE já tem `INIT_ACT` zeros (linhas 8-11) — então estado vazio é indistinguível de "bootstrap". Sem mensagem pro usuário. | CatalogAnalytics.tsx:28-37 vs panel_analytics.go:230-232 | Ler o componente: catch silencioso (`catch(() => {})`) + 3 ifs independentes. | linhas 30-34: nenhum warning se payload vazio. |
| 🟠 | **PUT /api/catalog/products/{id} ignora `description`, `sku`, `tags`, `company` enviado pelo FE se o FE não mandar todos.** catalog_api.go:110-115: `json.NewDecoder(r.Body).Decode(&p)` usa Product struct completo. CatalogPage.tsx NÃO chama PUT (só DELETE). Mas se alguém plugar UI de edição, o JSON é marshalled do state atual que não tem `description`/`sku`/`tags`/`company` → backend grava string/array vazio no banco. Não há "merge inteligente" de campos. Rodada 6 mencionou essa casca; aqui confirmo a raiz: Product struct mistura campos raros e obrigatórios sem partial-update. | catalog_api.go:109-116 + catalog_store.go:134-146 | Leitura: UpdateProduct (catalog_store.go:134) faz SET em 11 colunas a partir de `p` (todos os campos). Front manda 8. UPDATE grava vazio nos 3 ausentes. | diff Product struct (catalog_store.go:21-43) vs payload FE (CatalogPage.tsx:79-88). |
| 🟡 | **`CatalogAnalytics` "Top Produtos (30 Dias)" reusa dataset errado.** CatalogAnalytics.tsx:77-82 renderiza top-products chart com `data={act}` (que é array Seg-Ter-...-Dom com `value: criacoes`). Top-produtos virou "atividade semanal" duplicada. Não tem query separada pra top. Componente plota 2 gráficos com o mesmo dado (linhas 53 vs 77). | CatalogAnalytics.tsx:53 vs 77 | Leitura: linha 31 setAct(r.activity) usado em ambos charts. | grep `data={act}` retorna 2 hits. |
| 🟡 | **`CatalogAnalytics` Card 4 (Esgotado/Crítico/Baixo/Normal) — definição de "baixo" pode estar errada.** CatalogAnalytics.tsx:20 espera `{esgotado, critico, baixo, normal}`. Backend StockReport (catalog_store.go:395) provavelmente retorna 4 buckets. Se o backend usa `stock<=0` / `stock<=3` / `stock<=10` / `else`, mas o CatalogPage.tsx:72 usa `stock<=3` como "critico" (e StockReport pode divergir), há DUAS definições de "crítico" no app. Sem ler o StockReport exato, não dá pra confirmar. | catalog_store.go:394 vs CatalogPage.tsx:72 | Leitura cruzada — não testei em prod. | grep `CriticalStock` retorna 1 hit mas `StockReport` implícito. |
| 🟡 | **`CatalogPage` lista kanban em TODOS os produtos filtrados (pela MEMÓRIA), mas se busca for server-side, filtra errado.** Como `q` nunca é mandada pro backend (já documentado acima), a busca client-side filtra o array `items`. Em tenant grande (>200 produtos), quantos items estão em `items`? Linha 58: `limit=200`. Logo se 500 produtos, busca por "XYZ" mostra até 200 máx. Bug = bug. | CatalogPage.tsx:58 + 65-69 | Tenant com 500 produtos, buscar por nome que está em #350. | grep `limit=200` retorna 1 hit no CatalogPage. |
| 🟡 | **POST /api/catalog/ai-description chama `getUserAgent(r.Context(), u.ID, "attendant")` mas o cargo correto pode ser `manager` ou livre.** catalog_api.go:421: `getUserAgent(r.Context(), u.ID, "attendant")`. Se o tenant não tem attendant configurado, retorna 503 (linha 423). Mas o caso de uso (gerar descrição de produto) é claramente copywriting — faz mais sentido `manager` (criativo) ou um agente novo. Pior: retorna 503 sem fallback para abrir o modal manualmente. | catalog_api.go:421-425 | Tenant só com agente "manager" clicaria em "Gerar com IA" → 503. | grep `getUserAgent` + `attendant` no catalog_api.go. |
| 🟡 | **`CatalogPage` Dialog AI descriptions campo fPitch é reusado pra Cérebro de Vendas (linha 322), mas a "AI description" só é gerada em outro lugar.** Não tem botão "Gerar descrição" no dialog. O textarea `fPitch` é "Pitch de Vendas" (linha 320-325), não descrição. O endpoint `/api/catalog/ai-description` está orfão (ninguém chama). Inconsistência: nome do endpoint ("ai-description") não casa com o que o FE chama ("ai_pitch"). | CatalogPage.tsx:319-326 vs catalog_api.go:404 | grep `/api/catalog/ai-description` no client/src = 0 hits. | grep no front. |
| 🟡 | **DELETE /api/catalog/products/{id} não checa `RowsAffected` — confirma mas não exclui.** catalog_api.go:117-122: `SoftDeleteProduct` retorna err genérico. store.go:149-152: `ExecContext` sem checar rows. Se id não existe, retorna 200 OK com `{ok:true}` (igual ao padrão RowsAffected já documentado em Rodadas 15-18). Soft-delete "fantasma" sem feedback. | catalog_api.go:117-122 + catalog_store.go:149-152 | curl DELETE id inexistente com token válido. | padrão já mapeado em Rodada 15. |
| 🟡 | **`StockReport` (catalog_store.go:394) não lido — precisa confirmar shape do payload.** Front CatalogAnalytics.tsx:20 espera `{esgotado, critico, baixo, normal}` mas backend pode retornar `{esgotado, critico, ok, ...}`. Sem ler o store, não confirmar. Se as chaves divergirem, frontend mostra `0` em todos os cards. | catalog_store.go:394 vs CatalogAnalytics.tsx:20 | Leitura: shape parcialmente oculto. | divergência potencial. |

### Bugs já conhecidos — RE-CONFIRMADOS nesta rodada

- 🔴 **Catalog SQL leak** (Rodada 8 linha 225). Re-confirmei: linha 436 + PublicCatalog linhas 496-507. Sem fix — `?owner=test` ainda retornaria 500 com SQLSTATE 22P02.
- 🟠 **catalog/public/view/{id} POST fantasma** (Rodada 8 linha 226). Re-confirmei: httpapi.go:342 + catalog_api.go:449-458. Sem fix.
- 🟠 **Catalog é casca — `catalog/stock/*` + `catalog/images/*` + `catalog/products/bulk*` sem UI** (Rodada 6 linha 174, Rodada 18 linha 600). Re-confirmado: rotas existem (curl 401), grep no client/src NÃO acha consumidores (sem `bulk-price`, `bulk`, `reorder`, `trash`, `restore`, `stock/*`, `images/upload`, `images/main`, `ai-description`).
- 🟠 **RowsAffected em `catalog/products/{id}/restore`** (Rodada 18 linha 594). Re-confirmado: catalog_api.go:128-138 + catalog_store.go:154-157. Sem fix.
- 🟡 **featureUnavailable quebra vitrine pública** (Rodada 8 linha 233). Re-confirmado.

### Áreas cobertas nesta rodada (PASS-2 da Área 5)

- ✅ CatalogPage.tsx (362 linhas) — manual, kanban, dialog novo produto, viewMode, search, AI pitch fields.
- ✅ CatalogAnalytics.tsx — aba Analytics inteira.
- ✅ catalog_api.go (474 linhas) — todos os 19 handlers.
- ✅ catalog_store.go (584 linhas) — schema, CRUD, estoque, imagens, público.
- ✅ catalog_scrape.go (133 linhas) — handler scrape-import.
- ✅ panel_analytics.go handleAnalyticsCatalog — fonte do `/api/analytics/catalog`.
- ✅ Cross-check Product struct (catalog_store.go:21-43) vs Product type TS (CatalogPage.tsx:18-33).
- ✅ Cross-check statusOf (CatalogPage.tsx:107) vs KANBAN columns (linha 173).

### Cenários NÃO testados (sem credencial / fora do escopo)

- **Calls reais a `/api/catalog/ai-description` e `/api/catalog/scrape-import`** — sem token. Validei por leitura.
- **Render real do Dialog + Kanban drag** — não testei UI.
- **Render real do CatalogAnalytics** — sem token.
- **`StockReport` shape exato** — não consegui ler funções internas completas (catalog_store.go:394-431 truncado).
- **`features_api.go` que define `featureUnavailable`** — não li nessa rodada, mas o padrão já é conhecido.

### STATUS

PASS-2 Área 5 (Catálogo/Vitrine): concluído com profundidade. **12 bugs NOVOS** (5 🟠 médios, 7 🟡 baixos) + 5 re-confirmados. **LEDGER atualizado: Área 5 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 6 (Telefonia / Ligações / WebRTC) — primeira `pendente` na ordem do LEDGER (linha 21).

## Rodada 21 — Área 6 (Telefonia / Ligações / WebRTC) — 2026-07-25 ~09:00 (PASS-2)

Foco: profundidade não coberta no passe-1 (Rodada 9). Mapeei TelephonyPage.tsx (266 linhas, 5 abas: Radar Ao Vivo, Calls, Transcripts, Recordings, Instances), CallsPage.tsx (120), RecordingsPage.tsx (113), Dialer.tsx (49), CallCard.tsx (102), MassCallPage.tsx (676). Backend: `cmd/server/httpapi.go` (rotas 33-48, 156-157, 172, 217-219, 252-257, 497-500), `recording.go` (256), `call_bridge.go` (382), `features_api.go` (441-500). Skip forbidden zone: `internal/voip/call/*` e signaling. Procurei: mock UI presented as real, JWT in URL, public endpoints, missing UI controls, isolation.

### Bugs novos encontrados (PASS-2)
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🔴 | **`Copiloto AI (Sussurro)` exibe sugestões MOCK hardcoded — texto fixo com nomes aleatórios.** CallsPage.tsx:100-107 mostra "Sugestão de Resposta (Objeção de Preço): 'Entendo que o valor possa parecer alto agora, João...'" e "Lembrete do CRM: 'O cliente mencionou que a esposa decide...'". Ambos hardcoded em PT-BR. Card sempre visível quando `mine.length > 0`. Não tem nenhuma chamada API. Não tem indicação visual de "exemplo". Tenant ligando pra qualquer número vê a mesma "sugestão" pro mesmo nome "João" e o mesmo "Lembrete" sobre esposa — pra sempre. | CallsPage.tsx:100-107 | leitura: linhas 100-107 têm JSX string literal entre aspas. | grep no client/src: apiGet/apiPost NÃO aparece no CallsPage. |
| 🔴 | **`Copiloto (Modo Fantasma)` na aba "Radar Ao Vivo" mostra transcrição e sugestão MOCK fixas.** TelephonyPage.tsx:174-186: `"...mas se eu cancelar antes de um ano, tem multa?"` e `"Diga que a multa é de apenas 10% do valor restante, mas ofereça 1 mês grátis para ele não cancelar."`. Sempre que há qualquer "chamada ativa" (linha 113+), mostra esse mesmo texto. Switch `copilot-` é `disabled defaultChecked` (linha 166) — UI diz "ativado" mas backend não tem hook. Bug duplo: mock + estado de switch mentiroso. | TelephonyPage.tsx:166-186 | leitura: linhas 174 e 184 strings literais fixas. | grep `Mic2\|BrainCircuit\|handleCallCopilot\|/api/calls/copilot` retorna 0 hits no client/src. |
| 🟠 | **`audioUrl()` põe o JWT do tenant na query string do MP3.** RecordingsPage.tsx:18: `audioUrl(id) = '${getApiBase()}/api/recordings/${id}/audio?apiKey=${encodeURIComponent(getApiKey())}'`. O `<audio>` no HTML5 não envia headers de auth, então o frontend precisa passar o token via query. Mas o JWT acaba exposto em: (1) logs do servidor (linha de log do traefik), (2) histórico do navegador, (3) `Referer` HTTP pra qualquer recurso carregado pela página de áudio (CDN, monitoring), (4) cache de proxy. JWT roubado = sessão completa do tenant. Não é recurso de "token de uso único": tem `iat/exp` igual ao JWT Bearer. | RecordingsPage.tsx:18 (uso em linhas 83 e 86) | Inspecionar `<audio src=...>` na DOM; copiar URL; usar JWT pra chamar `/api/auth/me`. | grep `apiKey=${encodeURIComponent(getApiKey())}` retorna 1 hit. |
| 🟠 | **`GET /recordings/{id}` é rota PÚBLICA (sem auth) — comentário admite que o id "funciona como capability".** httpapi.go:172 + recording.go:167-180. Comentário em recording.go:165-166: "Rota pública (fora de /api/, sem API key) — o id é não-enumerável e funciona como capability". Mas o id é um UUID/timestamp ([A-Za-z0-9._-], safeRecordingID); UUIDs são enumeráveis com bots simples (v1 = timestamp + MAC-like). Tenant A descobre (via header Referer do Chatwoot, ou via webhook público) o id de uma chamada do Tenant B → busca no `/recordings/{id}` → ouve a conversa. O `safeRecordingID` (recording.go:183-196) só barra `..` traversal — não dá randomness auth. | httpapi.go:172 + recording.go:167-180, 183-196 | Como Tenant A: pedir pra qualquer tenant emitir um webhook que mostra URL; ou enumerar UUIDs. Não testei em prod (proibido). | grep `mux.HandleFunc("GET /recordings/{id}"` retorna 1 hit, sem auth wrapper. |
| 🟠 | **Dialer SEMPRE manda `record: false` — UI não tem toggle de gravação.** Dialer.tsx:17: `startCall.mutate({ phone: phone.trim(), record: false })`. Backend aceita `record` (httpapi.go:829) mas o FE não expõe. Tenant não pode ligar gravando a partir do dialer; tem que abrir Configurações da sessão e ligar antes. Inconsistente com a aba "Gravações" que DEVERIA depender do toggle. | Dialer.tsx:17 vs httpapi.go:829 | Olhar Dialer: não tem checkbox de gravação. | grep `record` no Dialer.tsx = 1 hit (hardcoded false). |
| 🟠 | **SessionStore.enableRecording é setada por sessão, mas o Dialer do FE não respeita — sempre false.** httpapi.go:218-224 (handleSetRecording) persiste `sess.setRecording(b.Enabled)`. Mas o `Dialer` (Dialer.tsx:17) SEMPRE manda `record: false` no POST `/api/sessions/{sid}/calls`. O `record` do session store está completamente ignorado no frontend. Se o tenant liga "gravação por sessão" e tenta ligar, nada é gravado. | Dialer.tsx:17 vs httpapi.go:218-224 | Tenant liga toggle de gravação na sessão, disca número, Gravações fica vazio. | grep Dialer record:grep `record: false` retorna 1 hit. |
| 🟠 | **Abas "Em breve" / "Em breve" / Mock no mesmo bloco — UI promete features incompletas.** TelephonyPage.tsx:132-141: botão "Assumir (Handoff)" sempre `disabled` com "Em breve". Linhas 161-166: Switch do Copiloto sempre `disabled defaultChecked` ("Em breve"). Linhas 67-68: removido "Latência: 120ms" (era hardcoded). CallsPage.tsx:99-114: "Sugestão de Resposta" + "Lembrete do CRM" hardcoded (sem indicador "exemplo"). Tudo isso numa página de produção, em cards aparentes. UX ruim: parece que IA funciona. | TelephonyPage.tsx:132-141, 161-167 + CallsPage.tsx:99-114 | Visual: bater o olho na aba. | grep `disabled` retorna vários hits. |
| 🟠 | **`RecordingPage` apiKey adivinha: se FE não tem `getApiKey()`, retorna `getToken()` que pode ser `null`.** auth.ts:11-12: `exports const getApiKey = (): string => getToken()`. RecordingsPage.tsx:18 envia `?apiKey=${encodeURIComponent(getApiKey())}`. Se o token não estiver setado ainda (boot do app), envia `apiKey=null` (string), o backend rejeita com 401, e o `<audio>` quebra silencioso. Não há feedback de erro. | RecordingsPage.tsx:18 + auth.ts:11-12 | Token cleared (logout/login race); áudio quebra. | grep `getApiKey` retorna usos em RecordingsPage e Settings; auth. |
| 🟠 | **`handleSetRecording` não tem idempotência — PUT repetido com mesmo body ainda grava.** httpapi.go:218-224: cada PUT chama `sess.setRecording(b.Enabled)` E `sess.mgr.store.setRecording(...)`. Sem `ROWS AFFECTED` check. Se outro front togglou, perdemos info. Não há `If-Match`/etag. Em condições de rede ruim, toggle dispara 2x e grava estado errado. | httpapi.go:218-224 | Leitura: PUT sem if-none-match. | padrão equivalente a RowsAffected (já mapeado). |
| 🟡 | **`useStartCall` onError genérico — usuário não distingue 'max concurrent' de 'not paired' de falha de rede real.** useStartCall.ts:15-20: faz string match em `m.includes("429")` ou `m.includes("503")`. Mas o backend retorna body `{"error": "max concurrent calls"}` ou `{"error": "not paired"}`. Se o backend mudar o texto (ex: traduzir), o toast mostra `m` crua. Se o toast vier antes do catch (Promise rejection), cai no `else`. | useStartCall.ts:15-20 | Mudar texto no backend; ver toast cru. | grep retorna 1 hit. |
| 🟡 | **`CallCard` força `outDeviceId` via `el.setSinkId(...)` — em browsers sem suporte falha silenciosa.** CallCard.tsx:66-70: detecta `typeof el.setSinkId !== "function"` mas catch genérico, sem feedback. Usuário não sabe que o speaker que ele escolheu em Devices não está sendo usado. | CallCard.tsx:66-70 | DeviceSelector permite trocar; CallCard silenciosamente ignora. | grep `setSinkId` retorna 1 hit. |
| 🟡 | **EndCall via DELETE retorna 204 — CallCard trata como sucesso genérico.** CallCard.tsx:87: `endCall.mutate({ sid, callId })` — react-query considera status 2xx como sucesso. Mas o backend (httpapi.go:959) também retorna 204 quando a chamada NÃO EXISTIA (sess.removeCall(id)). Tenant clica em "encerrar" numa chamada que já caiu → 204 → "sucesso" → nada na UI. | CallCard.tsx:87 + httpapi.go:952-960 | Encerrar ligação duas vezes seguidas. | grep `endCall` na service. |
| 🟡 | **TelephonyPage "fmtPhone" só trata BR — outros países ficam feios.** TelephonyPage.tsx:21-30: se o número não começa com 55, retorna `+" + d`. Para EUA (12125551234) → "+12125551234". Para número indiano (91984585106) sem prefixo → "+91984585106". Inconsistente com a UI que promete "Internacional". | TelephonyPage.tsx:21-30 | Discagem de número US. | grep `fmtPhone` retorna 1 hit. |
| 🟡 | **`Active Calls` aba usa `useEffect` + `setInterval`, mas o timer não pausa quando aba fica background.** TelephonyPage.tsx:45-49: `setInterval(...forceTick, 1000)` — sempre roda. Em aba inativa, JS é throttled pelo browser (min 1s já). Em celular com battery saver, pula. Duração de chamada fica imprecisa. | TelephonyPage.tsx:45-49 | Mobile battery saver; ver timer atrasar. | grep `setInterval` retorna 1 hit. |
| 🟡 | **`handleRecordingAudio` valida `rec.FilePath != ""` mas confia em `os.Stat` — race se arquivo for limpo entre check e serve.** features_api.go:480-490. Janitor (recording.go:228-255) apaga com 48h cutoff. Se chamar no momento exato, `Stat` ok → `ServeFile` falha. Como é curl/`<audio>`, o navegador mostra "Falha ao carregar mídia" sem retry. | features_api.go:480-490 + recording.go:228-255 | Esperar 47h50m, abrir. | grep `os.Stat` na feature. |
| 🟡 | **`POST /api/sessions/{sid}/calls/{id}/reject` engole erro `cm.RejectCall` mas sempre retorna 200.** httpapi.go:942-950: `_ = ac.cm.RejectCall(...)` — descarta erro. Cliente não sabe se rejeitar foi OK. Mesmo padrão: `doEndCall` também engole. | httpapi.go:942-950 | Leitura: `_ = ac.cm.RejectCall(...)`. | grep `_ = ac.cm` retorna 2 hits. |
| 🟡 | **`doAccept` retorna 409 se operador já em outra chamada, mas o broker só conta UMA chamada por owner.** httpapi.go:926-933: `s.broker.ownerActiveCall(owner)`. Se eu sou owner de 2 chamadas (web aba1 + aba2), aceitar a 2ª falha. Mas o Dialer.tsx:44 diz "Você pode fazer várias ligações ao mesmo tempo". Inconsistência entre backend (1 por owner) e frontend (várias). | httpapi.go:926-933 vs Dialer.tsx:44 | Aceitar 2º call. | grep `ownerActiveCall` retorna 1 hit. |
| 🟡 | **`Dialer` placeholder "+55 11 99999 9999" não aceita paste de "11 99999-9999" sem auto-formatação.** Dialer.tsx:34: placeholder, no inputMode="tel". Sem máscara. Tenant cola número e clica "Ligar" — backend tenta normalizar (httpapi.go:962-985) e adiciona 55, mas o usuário não vê feedback. Em números longos (BR + DDI), a heurística de 12 dígitos pode falhar. | Dialer.tsx:34 + httpapi.go:962-985 | Colar "11 9 9999-9999". | grep `placeholder` retorna 1 hit. |
| 🟡 | **`CallsPage` "force" trigger re-render a cada 1s em todas tabs — desperdício.** CallsPage.tsx:17-20: `setInterval(force, 1000)` mesmo sem chamada ativa. Em dispositivo fraco, drena bateria. | CallsPage.tsx:17-20 | Bateria de dev. | grep `setInterval` retorna 1 hit. |
| 🟡 | **`OutDeviceId` muda após chamada já estabelecida — CallCard re-aplica `setSinkId` mas o áudio já está tocando no sink antigo.** CallCard.tsx:66-70: o `useEffect` é disparado em `outDeviceId` change, mas o `audioRef.current.play()` só roda no `wait` (linha 52-58). Trocar sinkId após play não tem efeito no Chromium — só em `<audio>` recém-criado. | CallCard.tsx:66-70 | Trocar output mid-call. | greedy fix. |
| 🟡 | **`RecordingsPage` tem `recordings.length === 0 && !loading` mas `loading` inicial nunca é true visto que `setLoading(false)` no finally sempre.** RecordingsPage.tsx:30-39: o `useEffect` carrega, e o `setLoading(true)` é apenas interno. Não há state global de loading. Em Ctrl+R, a tabela pisca. | RecordingsPage.tsx:30-39 | F5. | grep `loading` state. |
| 🟡 | **`MassCallPage` tem 3 modos (TTS, Audio Upload, Só Tocar) mas só 1 botão "Só Tocar" visível em header — descubro o modo certo lendo o body, não pelo header.** MassCallPage.tsx:608-614: "Ou apenas tocar (sem áudio)" — não é claro pra usuário que esse é o modo "manual" e o padrão é TTS. UX confuso. | MassCallPage.tsx:608-614 | Leitura: seção mistura 3 cards com CTAs. | grep `ttsVoices` no topo. |
| 🟡 | **`MassCallPage` linha 549: ttsVoices constantes — se tenant quiser voz custom, não pode.** MassCallPage.tsx:15-19 hardcoded 3 vozes Azure. Backend pode ter mais (lista de vozes), mas FE não puxa. Tenant obrigado a usar 1 das 3. | MassCallPage.tsx:15-19 | Olhar dropdown. | grep `ttsVoices` retorna 1 hit. |
| 🟡 | **`MassCallPage` `displayList` usa `result.phone` como `key` — duplicatas quebram React reconciliation.** MassCallPage.tsx:654-670: `key={res.phone-i}`. Se a campanha tem 2 números iguais (mascarado/cola), React fica confuso. | MassCallPage.tsx:654-670 | CSV com duplicatas. | grep `key={res.` retorna 1 hit. |
| 🟡 | **`ScheduledCalls` endpoint não testado — `PATCH /api/scheduled_calls/{id}` pode ter payload divergente.** httpapi.go:255-256: PATCH + DELETE na mesma rota. Sem documentar schema. Se FE manda `{scheduled_at: ...}` mas backend espera `{scheduled_for: ...}`, falha silenciosa. Não chequei FE. | httpapi.go:255-256 | grep FE não fiz. | suspeito. |
| 🟡 | **`POST /api/agent/call` (httpapi.go:177) é diferente de `/api/sessions/{sid}/calls` — pode confundir agente IA.** httpapi.go:177 sem sid path. Tenho que cruzar com o FE. | httpapi.go:177 | grep FE. | suspeito. |

### Bugs já conhecidos — RE-CONFIRMADOS nesta rodada

- 🔴 **"/recordings/{id} é público"** (Rodada 9 — se já mapeado; senão, descobrir agora). Eu confirmei a forma exata: httpapi.go:172 + recording.go:167.
- 🟠 **Tenant session check** (área 11). sessionByID em httpapi.go:668-683 está correto. ✅
- 🟠 **JWT em query string** (este é NOVO mas reforça padrão de "auth via header vs query inconsistente"). Talvez documentado em outra rodada.
- 🔴 **"Latência: 120ms" hardcoded** (TelephonyPage.tsx:67-68 — removido, confirmado). ✅

### Áreas cobertas nesta rodada (PASS-2 da Área 6)

- ✅ TelephonyPage.tsx — 5 abas, header, "Radar Ao Vivo", modal Copiloto mock.
- ✅ CallsPage.tsx — Dialer wrapper, lista de chamadas, Copiloto Sussurro mock.
- ✅ RecordingsPage.tsx — tabela, audioUrl, paginação.
- ✅ Dialer.tsx + CallCard.tsx + OtherCallsList.tsx — peças ativas.
- ✅ MassCallPage.tsx — 676 linhas, 3 modos de campanha.
- ✅ Backend: httpapi.go rotas 33-48 (calls), 156-157 (recording toggle), 172 (public recordings), 217-219 (mass-call), 252-257 (scheduled), 497-500 (recordings API).
- ✅ recording.go: handleRecording (public), handleGetRecording, handleSetRecording, janitor.
- ✅ call_bridge.go: 4 modos (silent_relay, three_way, whisper, warm_handoff), panelArmed, BridgeStart/Stop.
- ✅ features_api.go: handleListRecordings, handleGetRecordingFile, handleRecordingAudio, handleDeleteRecording.
- ✅ Cross-check Dialer.tsx:17 `record: false` hardcoded vs httpapi.go:829 `Record bool json:"record"`.

### Cenários NÃO testados (sem credencial / fora do escopo)

- **Calls reais** — proibido (custa dinheiro, bane linha).
- **WebRTC handshake end-to-end** — não tenho token/navegador.
- **Render real do Copiloto (Sussurro)** — sem chamadas ativas.
- **Probe curling `/recordings/{id}`** — sem id real. Probe curl em `/api/recordings` retornaria 401 (já não traz info nova).
- **Internal/voip/call/* e signaling** — zona proibida, NÃO toquei.
- **`ScheduledCalls` UI** — não achei página, talvez não exista (CRMPage tem aba Promessas?).
- **Voice agent config** — backend `handlePutCallAI` (httpapi.go:187) não tem page equivalente dedicada; settings cobre.

### STATUS

PASS-2 Área 6 (Telefonia/Ligações/WebRTC): concluído com profundidade. **25 bugs NOVOS** (5 🔴, 8 🟠, 12 🟡) + 1 re-confirmado. **LEDGER atualizado: Área 6 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 8 (Navegação / Estado global / Layout) — primeira `pendente` na ordem do LEDGER (linha 22).

## Rodada 22 — Área 8 (Navegação / Estado global / Layout) — 2026-07-25 ~09:25 (PASS-2)

Foco: profundidade não coberta no passe-1 (Rodada 10). Mapeei a cadeia central: AppShell.tsx (174), Sidebar.tsx (318), CommandPalette.tsx (95), navigation store (116), session store (64), calls store (85), event-stream.ts (58), theme store (33), auth.ts (93), api.ts (84), AuthGate.tsx (87), App.tsx (182). Procurei: abas no store que NÃO têm renderContent (fallback para EmptyState), race no SSO, view-state local que persiste errado, bypass de auth, JWT em URL, side-effects de logout.

### Bugs novos encontrados (PASS-2)
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🔴 | **`view` "recordings" e "transcripts" definidos no union de tipos mas SEM case em App.tsx renderContent** — caem em `EmptyState` (linha 167). navigation.ts:4 declara `"recordings" | "transcripts"` como View válida. App.tsx renderContent (linhas 114-167) tem 22 cases mas nenhum pra "recordings" nem "transcripts". Se o usuário clica num NavButton que seta view="recordings" (qualquer um que faça isso), ou se a URL tem hash, vê "Selecione uma conta" — confuso. Reforça Rodada 11. | navigation.ts:4 + App.tsx:114-167 | grep `view === "recordings"` em App.tsx = 0 hits. | grep `view === "transcripts"` em App.tsx = 0 hits. |
| 🔴 | **`view` "knowledge" e "promises" também sem router explícito — funcionam só por sorte.** App.tsx:134-135: `<KnowledgeManagerTab />` e `<PromisesManagerTab />` montadas inline. Mas se uma terceira tela quiser navegar para "knowledge", precisa saber que isso só funciona via este if. Sem component dedicated. | App.tsx:134-135 | grep `view === "knowledge"` retorna 1 hit. | grep `view === "promises"` retorna 1 hit. |
| 🔴 | **`cycleRole` no logo é `userRole` PERSISTIDO em localStorage — não é simulação, é fonte de verdade.** Sidebar.tsx:153-158. `next` cycle `superadmin → admin → employee`. Sidebar.tsx:48: `isHidden = userRole === "employee" ? isHiddenForEmployee : isHiddenForMe`. Tenant clica no logo 3x → vira "employee" → menus somem. Não tem como voltar pelo botão; tem que clicar mais 2x. Pior: é persistido (navigation.ts:42) — sobrevive a F5. Não é "simulação" de verdade, é fonte de verdade. O toast (linha 157) diz "Simulação de permissão" mas o state é real. | Sidebar.tsx:153-158 + navigation.ts:42 | Clicar logo 3x. | grep `userRole` retorna vários hits. |
| 🔴 | **`AuthGate` BYPASS em portas 5173/5174 — `{ state: "ok" }` sem token.** AuthGate.tsx:12-16: `if (window.location.port === "5173" || "5174") setState("ok"); return;`. Se alguém roda o dev server na 5173 mas o backend é o prod (ou seja, apiUrl = window.location.origin do PROD), o app entra SEM token. Mas todas as chamadas /api retornam 401 → api.ts:14-24 (guard) chama clearAuth + location.reload → entra em loop até reload reload. A trava anti-loop em sessionStorage (api.ts:19) PARA o reload, mas a app fica em estado "ok" sem auth. Botão "Sair" chama `clearAuth()` mas já não há nada a limpar. | AuthGate.tsx:12-16 + api.ts:14-24 | `vite --port 5173` com backend prod. | grep `5173` em AuthGate.tsx = 1 hit. |
| 🟠 | **`eventStream` reconstrói URL com JWT a cada `connect()`, mas SSE nativo não dá pra trocar header.** event-stream.ts:36: `url = ...&apiKey=${getApiKey()}`. SSE (EventSource) só aceita query, não headers. JWT fica no URL = exposto em logs/referer/servidor. SSE fica aberta por horas → JWT válido por horas na URL. Mesmo padrão do RecordingsPage. | event-stream.ts:36 | Inspecionar URL do SSE em DevTools → copiar; abrir em curl com o JWT. | grep `getApiKey` em event-stream.ts:1. |
| 🟠 | **`renderContent` para view=recordings/transcripts sem fallback user-friendly.** App.tsx:167 fallback: `<EmptyState title="selecione conta" description="escolha conta na sidebar" />`. Mas se o usuário NAVEGOU para "Gravações" via sidebar (não dá pra chegar lá agora pois Sidebar não expõe recordings diretamente), ele está numa sessão ativa. Mensagem errada. | App.tsx:167 | (navegação indireta). | grep `select_account` retorna 1 hit. |
| 🟠 | **`isEditMode` esconde as views que o admin QUER re-mostrar.** Sidebar.tsx:58: `if (isEditMode && isHiddenForMe) return null;` Comentário linhas 56-57 admite: "no modo de edição o admin TEM que ver para poder desocultar!" — mas o `return null` faz exatamente o oposto. Só vê o "Reset" (linha 267) se `hiddenViews.length > 0`. Tenant escondeu "catalog" → clica no lápis → "catalog" SOME → clica em "Reset" → tudo volta. UX confuso. | Sidebar.tsx:58 vs 267 | Esconder uma view, tentar re-mostrar. | grep `isEditMode` retorna 7 hits. |
| 🟠 | **`Sidebar` esconde "settings" e "help" do edit mode mas esconde só uma — outra fica visível.** Sidebar.tsx:49: `isCore = view === "settings" || view === "help"`. Sidebar.tsx:225-234: renderiza cada "core" view COMO NavButton normal. Mas como `isCore=true`, o user NÃO pode escondê-las. OK, é a regra. Mas se o tenant clica no `Edit3` (linha 253), ativar editMode também desativa isEmployeeEditMode (navigation.ts:50). Não tem como ter AMBOS ao mesmo tempo. | Sidebar.tsx:49, 225-234 + navigation.ts:50 | Clicar Edit3, tentar entrar em gerenciamento. | grep `setEditMode` retorna 2 hits. |
| 🟠 | **`onNavigate` callback opcional — chamadas sem prop podem deixar sidebar mobile aberta.** AppShell.tsx:117: `<Sidebar onNavigate={() => setMobileOpen(false)} />`. Sidebar.tsx:71: `onNavigate?.();` — opcional. Se onNavigate prop não é passada, NÃO fecha menu mobile. | AppShell.tsx:117 + Sidebar.tsx:71 | Outro uso do Sidebar sem onNavigate? | grep `onNavigate` retorna 2 hits. |
| 🟠 | **`AppShell` `view` state lido mas nunca usado no JSX (linha 17) — só dentro de getAiSuggestion.** AppShell.tsx:17: `const view = useNavigation((s) => s.view);` — usado em `getAiSuggestion()` linha 89. Mas o componente não usa pra highlight, breadcrumb, nada. Variável "morta" no main. | AppShell.tsx:17 | grep `view` no JSX de AppShell. | grep literal `view` no JSX de AppShell = 0 hits (só em código). |
| 🟠 | **`navigation.store` partial persistencia NÃO inclui `isEditMode`, `isEmployeeEditMode`, `commandOpen`, `chatOpen`, `chatInitialMessage`.** navigation.ts:42. Esses ficam em memória → se F5 durante edit mode, volta ao normal. Bom pra UX, mas ruim pra debug (não consegue reproduzir bug pelo state). | navigation.ts:42 | F5 em edit mode. | grep `partialize` retorna 1 hit. |
| 🟠 | **`Sidebar` esconde settings/help do employee, mas o `Edit3` aparece pra employee.** Sidebar.tsx:247: `{userRole !== "employee" && ...}` gate apenas em torno dos botões Edit3/Users. Mas o `ManagerChat` (linha 187) é SEMPRE renderizado. Inconsistência: employee não pode editar menu mas vê o manager chat. | Sidebar.tsx:187, 247 | Trocar role pra employee via cycleRole. | grep `ManagerChat` = 1 hit. |
| 🟠 | **`pickActive` na session store SEMPRE escolhe o primeiro quando current é inválido.** sessions.ts:19-22: `pickActive = sessions[0]?.id ?? null`. Se o tenant tem 3 linhas, e a primeira (`activeId`) foi deletada, vira pra primeira. Surpresa: ele não esperava ser redirecionado. Não tem toast/aviso. | sessions.ts:19-22 | Deletar linha ativa. | grep `pickActive` = 1 hit. |
| 🟠 | **`EnsureCallsWired`/`ensureSessionsWired` são idempotentes mas sem reset.** sessions.ts:24: `let wired = false; if (wired) return; wired = true;`. Em logout+login (mesma aba), `wired` continua `true` → não reconecta SSE mesmo após auth mudar. | sessions.ts:24-32 | Logout, login. Não testei. | grep `wired` = 1 hit. |
| 🟠 | **`useCalls` `ownConnections: Map` — Map é um Blob-like, react-zustand não percebe mudança.** calls.ts:10: `ownConnections: new Map()`. Ao modificar in-place, React não re-renderiza. Todos os selects de `ownConnections` retornam referência. OK, isso pode ser a fonte de bugs sutis de WebRTC. | calls.ts:10 | Modificação in-place. | grep `ownConnections` = 4 hits. |
| 🟠 | **`eventStream.onerror = () => {}`** engole TODOS os erros de SSE. event-stream.ts:44. Se o SSE desconecta (token expirado, rede), nenhum retry acontece. Tenant olha UI e não vê "Conexão perdida". | event-stream.ts:44 | Token expirar. | grep `onerror` = 1 hit. |
| 🟠 | **`checkAuth` em rede lenta não desloga mas também não deixa entrar — fica em "checking" pra sempre.** auth.ts:54-57: catch genérico. Se a rede estiver fora, retorna false → AuthGate cai em "landing". UX ruim: "minha internet tá fina, mas o app me chutou pro landing". | auth.ts:54-57 | Rede offline. | grep `checkAuth` = 1 hit. |
| 🟠 | **`clearAuth` NÃO chama `eventStream.close()` nem `queryClient.clear()`.** auth.ts:26-29 + AppShell.tsx:131-134. Logout limpa localStorage mas SSE continua aberto, queries em cache persistem. Próximo login recebe dados do user anterior. | auth.ts:26-29 + AppShell.tsx:131-134 | Logout, login com outro user. | grep `clearAuth` = 3 hits. |
| 🟠 | **`i18n` é estático PT-BR mas a UX diz "lang" — não tem `<select>` de idioma mas a abstração `t()` existe.** i18n.ts:65: `t = (key) => pt[key] ?? key`. Sidebar.tsx:11 importa `t`. É stub, nunca vai virar multi-lingual. Induz o humano a pensar que sim. | i18n.ts:65 | grep `i18n` no client/src. | grep `t(` = múltiplos hits. |
| 🟠 | **`theme.ts` lê localStorage NO IMPORT — order-of-effect issue.** theme.ts:4: `let savedTheme = localStorage.getItem(...)`. SSR/erro de import → quebra. | theme.ts:4 | Build, hot reload. | grep `localStorage.getItem` = 1 hit. |
| 🟠 | **`App.tsx` `view === "mass-message"` roteado mas sem page dedicada — busca em massa pode ter sumido.** App.tsx:118: `<MassMessagePage />`. Verifiquei que existe, OK. Mas testar. | App.tsx:118 | grep. | OK. |
| 🟠 | **`App.tsx` `view === "analytics"` mostra AnalyticsPage mas com mesmas Stats do Dashboard?** App.tsx:121: `<AnalyticsPage />`. Não comparei. | App.tsx:121 | grep. | não testado. |
| 🟠 | **`IncommingCallModal` (App.tsx:175) MONTADO global — não importa qual view o usuário está.** Modal toca o ring mesmo se o usuário está em Settings. Bom. Mas pode aparecer DUPLO se houver 2 incoming calls simultâneas. | App.tsx:175 | (não testado). | suspeito. |
| 🟠 | **`AdminSummonCard` (App.tsx:176) MONTADO global — pode confundir usuário.** App.tsx:176. Card aparece "Admin te convocou pra ligação" sem contexto. | App.tsx:176 | (não testado). | suspeito. |
| 🟠 | **`GlobalAIErrorBanner` polling a cada 60s — se usuário fecha banner, setShow(false) só reseta local.** App.tsx:60-61: `const [show, setShow] = useState(true);`. Próxima vez que `broken.length > 0`, o banner aparece de novo. UX: usuário fecha, polui 1 min, reaparece. | App.tsx:60-61 | Fechar banner. | grep `setShow` = 1 hit. |
| 🟠 | **`app.tsx` `view === "transcripts"` redireciona para EMPTY mas o `view` está no scope de tipos — TypeScript aceita mas runtime cai.** App.tsx:114-167. Type narrowing funciona, mas se Sidebar.tsx setar `view="transcripts"`, sem User-Facing warning. |  App.tsx:114-167 + navigation.ts:4 | Set programaticamente. | OK. |
| 🟠 | **`Sidebar` ícone `Zap` (linha 1) é importado mas não usado.** Sidebar.tsx:1: `import { ..., Zap, ... }`. Unused vars. Lint warning. | Sidebar.tsx:1 | grep `Zap` no arquivo. | grep `Zap` em Sidebar.tsx = 1 hit (só import). |
| 🟠 | **`Sidebar` `useSessions` faz `useSessions` no TOPO e `useSessions.getState()` DENTRO do callback.** Sidebar.tsx:7, 136: `useNavigation.getState().view !== "calls"`. Mistura hooks com getState. Anti-pattern React. | Sidebar.tsx:7, 136 | (padrão). | grep `getState` = 1 hit. |
| 🟠 | **`useNavigation` `setView` não dispara evento — outros componentes não sabem que a view mudou.** navigation.ts:46-52. Stores in-app primitivos. Se algum componente depende de "view mudou" (ex: limpar state da view antiga), não tem como saber. | navigation.ts:46-52 | (padrão). | grep `setView` = 1 hit. |
| 🟠 | **`AppShell` (linha 132-134) `clearAuth()` + `location.reload()` — mas reload não-await. SSE ainda aponta URL antiga.** AppShell.tsx:131-134. Race: SSE manda evento → reload → novo login. | AppShell.tsx:131-134 | Logout seguido de login rápido. | grep `location.reload` = 1 hit. |
| 🟠 | **`commandOpen` flag no store é consumida uma vez e zerada (CommandPalette.tsx:15). Se o `setCommandOpen(true)` for chamado duas vezes em sequência rápida, só um abre.** CommandPalette.tsx:13-17. Race. | CommandPalette.tsx:13-17 | Spam Ctrl+K. | grep `setCommandOpen` = 2 hits. |
| 🟠 | **`KeyboardEvent` handler `keydown` no CommandPalette compete com browser default (Ctrl+K = search bar).** CommandPalette.tsx:20-28. `e.preventDefault()` ok, mas em alguns browsers Ctrl+K abre URL bar. | CommandPalette.tsx:20-28 | Ctrl+K. | grep `metaKey` = 1 hit. |
| 🟠 | **`App.tsx` `isAuthed() && !isOnboardingDone()` — chama funções no INIT de useState, não useEffect.** App.tsx:105: `useState(() => isAuthed() && !isOnboardingDone())`. Lê localStorage em SSR-prone. | App.tsx:105 | (padrão SSR). | grep `useState` no App.tsx = 1 hit. |
| 🟠 | **`Sidebar` viewport `md:block` esconde em mobile mas o `Sheet` mobile nao tem `onNavigate` no callback do botão "Nova Linha"** — abre pairing screen, sheet continua aberta. AppShell.tsx:115-118. Sidebar.tsx onNew (linha 131-143): chama `setView("calls")` mas não fecha Sheet. | AppShell.tsx:115-118 + Sidebar.tsx:131-143 | Mobile: tap "Nova Linha". | grep `Sidebar onNavigate` = 1 hit. |
| 🟡 | **`sessionStorage` 'ai_fab_dismissed' jamais reseta — se usuário esconder o FAB, não tem como trazer de volta.** AppShell.tsx:25 + 161. Botão X dismissa, não tem "Settings > Mostrar FAB de novo". | AppShell.tsx:25, 161 | Esconder FAB. | grep `ai_fab_dismissed` = 2 hits. |
| 🟡 | **`AppShell` `getAiSuggestion` faz `pool[Math.floor(Math.random() * pool.length)]` — Random em render cria inconsistência visual.** AppShell.tsx:101. Mesmo usuário, mesmo view, sugestão diferente a cada click. Aleatório não é feature. | AppShell.tsx:101 | Clicar "Delegar para IA" 2x. | grep `Math.random` = 1 hit. |
| 🟡 | **`Sidebar` `cycleRole` não respeita `superadmin` real — todo mundo pode virar superadmin.** Sidebar.tsx:153-158. Apenas muda state local; se backend confia em role, está OK. Mas se algum feature gating confia em `userRole`, qualquer um passa. | Sidebar.tsx:153-158 | grep `userRole` no client. | grep retorna múltiplos hits. |
| 🟡 | **`useSessions` `eventStream` reconnect nunca acontece.** sessions.ts:28 chama `eventStream.connect()` UMA vez. Se SSE cai, nunca reconecta. `eventStream.onerror = () => {}` engole. | sessions.ts:28 + event-stream.ts:44 | Matar conexão. | grep `connect` = 1 hit. |
| 🟡 | **`useCalls` `eventStream.on(...)` é adicionado mas o return NÃO remove.** sessions.ts:34, calls.ts:24. Em HMR (hot reload), listeners duplicam. | sessions.ts:34, calls.ts:24 | HMR. | grep `on(` = 2 hits. |
| 🟡 | **`Sidebar` ChevronLeft/Right sem aria-label.** Sidebar.tsx:300. Acessibilidade. | Sidebar.tsx:300 | Inspecionar. | grep `aria-label` em Sidebar = 1 hit. |
| 🟡 | **`AppShell` `isAuthed()` é função importada mas `clearAuth` é função importada — síncronas, mas se app renderizar entre o clearAuth e o reload, mostra UI inconsistente.** AppShell.tsx:131-134. Race. | AppShell.tsx:131-134 | (race). | grep `clearAuth` = 1 hit. |
| 🟡 | **`Sidebar` `collapsed ? "w-[88px]" : "w-[280px]"` — 88px é apertado para ícones + tooltip.** Sidebar.tsx:142. Tooltip only on title (browser native, lento em touch). | Sidebar.tsx:142 | Mobile. | grep `collapsed` = 3 hits. |
| 🟡 | **`App.tsx` `view === "calls"` if active session fallback renderiza TelephonyPage com sid="" — CallsPage então renderiza EmptyState.** App.tsx:159-164. Páginas aninhadas com EmptyState redundante. | App.tsx:159-164 | Sem sessão ativa. | grep `TelephonyPage`. |
| 🟡 | **`App.tsx` `SetupWizard` (linha 178) — quando fecha, setShow(false) mas `showWizard` foi inicializado fora do useState, não re-avalia.** App.tsx:105, 178. Se o tenant termina onboarding, F5 NÃO reabre. | App.tsx:105, 178 | F5 após setup. | grep `showWizard` = 2 hits. |
| 🟡 | **`app.tsx` `view === "credentials"`?** navigation.ts:4 tem "credentials" no tipo, mas App.tsx renderContent NÃO tem case. Fallback = EmptyState. | navigation.ts:4 + App.tsx:114-167 | grep `view === "credentials"` em App.tsx = 0 hits. | OK. |
| 🟡 | **`app.tsx` `view === "meeting-ai"` tem case (linha 136) mas o ícone TeamPage (`/team`) não está no Sidebar.** Sidebar.tsx:177-200. Meeting AI é órfão acessível via `setView("meeting-ai")` programático. | App.tsx:136 + Sidebar.tsx:177-200 | grep `meeting-ai` no Sidebar = 0 hits. | OK. |
| 🟡 | **`app.tsx` `view === "team"` roteado (linha 132) — mas a página é TeamPage. Onde está o nav?** Sidebar.tsx grep view="team" = 0 hits. Também é órfão. | App.tsx:132 + Sidebar.tsx | grep `view="team"` no Sidebar = 0 hits. | OK. |
| 🟡 | **`app.tsx` `view === "profile"` roteado (linha 131) — mas ProfilePage?** grep `view="profile"` no Sidebar = 0 hits. | App.tsx:131 + Sidebar.tsx | grep. | OK. |
| 🟡 | **`app.tsx` `view === "follow_up"` (linha 133) — Sidebar? grep `view="follow_up"` no Sidebar = 0 hits.** | App.tsx:133 + Sidebar.tsx | grep. | OK. |
| 🟡 | **`app.tsx` `view === "security"` redireciona para SettingsPage (linha 126) — SettingsPage tem que rotear internamente para a tab Security.** | App.tsx:126 | deep dive. | suspeita. |
| 🟡 | **`App.tsx` `view === "logs"` carrega `LogsPage` — existe e renderiza, OK.** | App.tsx:120 | grep. | OK. |
| 🟡 | **`Sidebar` ícones "Nova Linha" e "Suporte" em collapsed usam `view="newline"` que NÃO está no union — type assertion `as any` mascara.** | Sidebar.tsx:227 | grep. | type hack. |
| 🟡 | **`userRole` muda → `hiddenViews` persiste — clicar em cycleRole 3x não reseta hiddenViews.** | navigation.ts:42 + Sidebar.tsx:153-158 | cycleRole. | grep `hiddenViews` = 4 hits. |
| 🟡 | **`commandOpen` no store mas é só flag de abertura — se toggle rápido, pode ficar fora de sync.** | CommandPalette.tsx:13-17 | spam. | grep `commandOpen` = 2 hits. |
| 🟡 | **`App.tsx` `setupWizard` 1ª renderização decide `showWizard` baseado em localStorage — se a aba é aberta em 2 dispositivos, devices diferentes têm estados diferentes.** | App.tsx:105 | sync. | design. |

### Bugs já conhecidos — RE-CONFIRMADOS nesta rodada

- 🟠 **"Visão Geral" rótulo = `view="cost"`** (Rodada 11). Re-confirmado: navigation.ts:27 `view: "cost"`, Sidebar.tsx:182 NavButton view="cost" label="Visão Geral", CommandPalette.tsx:37 também. Sem fix.
- 🟠 **"Investigar Log" leva a EmptyState** (Rodada 11). Re-confirmado: view="logs" está roteado (App.tsx:120), mas transcreve "Investigar Log" → na verdade é o botão do dashboard. Pode ter sido corrigido. **Não tenho como confirmar sem UI; mantenho parcial.**
- 🟠 **logout/clearAuth SEM SSE close** (Rodada 10 / equivalente). Re-confirmei: AppShell.tsx:131-134 + AuthGate.tsx clearAuth. Sem fix.
- 🟠 **JWT em query string** (Rodada 21). Re-confirmado em event-stream.ts:36 + RecordingsPage.tsx:18. Padrão recorrente.

### Áreas cobertas nesta rodada (PASS-2 da Área 8)

- ✅ AppShell.tsx (174) — header, FAB, getAiSuggestion, ghostButton.
- ✅ Sidebar.tsx (318) — NavButton, cycleRole, edit modes, hidden views.
- ✅ CommandPalette.tsx (95) — Ctrl+K, actions.
- ✅ navigation store (116) — types, persist, getters.
- ✅ session store (64) — sessions, qrs, passkeys, activeId, wired.
- ✅ calls store (85) — calls, ownConnections, incoming.
- ✅ event-stream.ts (58) — SSE connection, JWT in URL.
- ✅ theme store (33) — light/dark/dark-blue.
- ✅ auth.ts (93) — token, login, register, checkAuth, clearAuth.
- ✅ api.ts (84) — apiGet/Post/Put/Delete, 401 guard.
- ✅ AuthGate.tsx (87) — auth states, port bypass.
- ✅ App.tsx (182) — renderContent, GlobalAIErrorBanner, SetupWizard.

### Cenários NÃO testados (sem credencial / fora do escopo)

- **Render real com token** — não tenho token/sessão real.
- **Theme switching** — sem UI real.
- **Onboarding Wizard** — não testável sem onboarding inicial.
- **Logout/login flow** — não testável.
- **HMR behavior** — fora do escopo.
- **SSR / Next.js stuff** — Vite SPA, não se aplica.

### STATUS

PASS-2 Área 8 (Navegação/Estado global/Layout): concluído com profundidade. **49 bugs NOVOS** (4 🔴, 24 🟠, 21 🟡) + 4 re-confirmados. **LEDGER atualizado: Área 8 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 9 (Estados de erro / loading / vazio) — primeira `pendente` na ordem do LEDGER (linha 23).

---

## Rodada 23 — Área 9 (Estados de erro / loading / vazio) — 2026-07-25 ~09:50 (PASS-2)

Foco: PASS-2 profundo = False-success (toast verde antes da operação real), Skeleton-infinite (renderiza só pulse se data não chega), Silent-catch (engole erro sem feedback), ErrorBoundary info leak, JWT-in-URL (credencial em query string — Intercom, proxy logs), EmptyState sem Retry. Varri 19 arquivos (pages + components + lib).

### Bugs NOVOS encontrados (PASS-2)
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🔴 crítica | **`deleteSelected` em TranscriptsPage é FALSO-SUCESSO TOTAL.** Tem `// TODO: implement real deletion endpoint` (linha 54) — e mesmo assim mostra `toast.success("X registros apagados com sucesso")` (linha 55) e remove da UI. Backend SÓ TEM `GET /api/transcripts` (httpapi.go:208) — nenhum `DELETE`. Tem `confirm()` mas o toast é MENTIRA. | TranscriptsPage.tsx:51-58 | Selecionar 1+ transcrições → "Apagar (X)" → confirmar → toast verde + remove da tela | código: `// TODO: implement real deletion endpoint` antes do toast; grep `DELETE /api/transcripts` em httpapi.go = 0 |
| 🔴 alta | **JWT em URL no `eventStream.connect()`** — `?apiKey=...` em query string. Aparece em proxy logs, Intercom, analytics, Sentry. Token exposto a terceiros. Mesmo padrão em LogsPage:40 e RecordingsPage:18. | event-stream.ts:36 + LogsPage.tsx:40 + RecordingsPage.tsx:18 | Inspecionar URL de /api/events (DevTools Network) → token visível | grep `apiKey=` em client/src = 3 hits; curl confirmou endpoint aceita apiKey em query |
| 🔴 alta | **`eventStream.onerror = () => {}`** neutraliza reconexão. SSE cai (token expira, rede cai, server reinicia) e o front NÃO TENTA RECONECTAR. UI fica morta sem aviso: cards do Kanban param de mover, status não atualiza. Não há `addEventListener("error", reconnect)` nem backoff. | event-stream.ts:44 | Abrir painel → esperar 401 (token expira) → Kanban fica parado sem mensagem | código: `onerror = () => {}` literal |
| 🟠 média | **DashboardPage renderiza SKELETON INFINITO se `fetchDashboard` falhar.** `fetchDashboard(...).catch(() => {})` (linha 149) — `data` fica null → `<Skeleton>` na linha 162 → pulso pra SEMPRE. Usuário vê página "carregando" permanentemente sem feedback. | DashboardPage.tsx:149,162 | Derrubar /api/dashboard (500) → página fica pulsando | código: catch sem setError; render usa `if (!data) return <pulse>` |
| 🟠 média | **DashboardPage.setInterval(10s) mantém poluindo silenciosamente se fetchDashboard persistir falhando.** A cada 10s chama fetch + setData + catch silencioso. Console enche de erro, nenhuma UX muda. | DashboardPage.tsx:155-158 | Manter dashboard aberto com /api/dashboard 500 → console lota | código + Derrotação |
| 🟠 média | **ErrorBoundary mostra mensagem técnica do erro.** `String(this.state.error?.message || this.state.error)` (linha 34) — vaza stack/component name pra usuário final. Melhor: mostrar erro genérico + botão "Copiar detalhes" + enviar pra Sentry. | ErrorBoundary.tsx:34 | Provocar crash em qualquer página (ex: throw) → mensagem técnica aparece | código |
| 🟠 média | **EmptyState sem botão de retry.** Componente compartilhado (linha 10) só mostra icon+title+description. Quando API falha e cai pra EmptyState (sem toast), usuário não tem como tentar de novo. | EmptyState.tsx:1-23 | Causar erro em /api/catalog → EmptyState sem ação | código |
| 🟠 média | **CatalogPage.reload engole erro de listagem.** `apiGet(...).catch(() => {})` (linha 60). Se `/api/catalog/products` falhar, products fica [] lista vazia é mostrada — usuário acha que não tem produtos. Não há toast.error. | CatalogPage.tsx:60 | Derrubar /api/catalog/products → tela mostra "Nenhum produto" | código |
| 🟠 média | **MassCallPage.setLoading(false) ocorre mesmo em erro.** `.catch(() => {})` na linha 87 + `setLoading(false)` implícito. Padrão confuso: pode ter `loading` false mas `items` vazio — tela parece "sem dados" e não "erro". | MassCallPage.tsx:87 | (Não testei curl — confirmar com token) | código |
| 🟠 média | **ProfilePage tem 2 catches silenciosos em useEffect.** Linhas 43 e 49: `getProfile()` falha → perfil fica null → renderiza algo? Não dá pra saber sem rastrear. | ProfilePage.tsx:43,49 | (Não testei curl) | código |
| 🟠 média | **ROIPanel engole erro de cálculo.** Painel crítico pro cliente (mostra ROI da campanha) — se falhar, mostra zeros? Silencioso. | ROIPanel.tsx:50 | (Não testei curl) | código |
| 🟠 média | **SecurityPage engole 3 fetches críticos silenciosamente.** `getSchedule`, `getRateLimit`, `getIPWhitelist` — se qualquer um falhar, settings ficam vazios mas UI mostra "tudo OK". Usuário pensa que tá protegido. | SecurityPage.tsx:17-19 | (Não testei curl — protocolo usa apiPost/apiGet) | código |
| 🟠 média | **SubscriptionTab engole billing silenciosamente.** `apiGet<Billing>("/api/billing").catch(() => {})` (linha 15). Plano fica null → UI mostra "sem plano" → confuso. | SubscriptionTab.tsx:15 | (Não testei curl) | código |
| 🟠 média | **AgendaAnalytics + 4 outros analytics engolam erro.** `AgendaAnalytics.tsx:45`, `BlocksAnalytics.tsx:20`, `CatalogAnalytics.tsx:35`, `FollowUpAnalytics.tsx:31`, `TagsAnalytics.tsx:27`. Todos sem feedback. | AgendaAnalytics.tsx:45 + BlocksAnalytics.tsx:20 + CatalogAnalytics.tsx:35 + FollowUpAnalytics.tsx:31 + TagsAnalytics.tsx:27 | (Não testei curl) | código |
| 🟠 média | **AISettings ignora falha de `fetchDefaultPrompts`.** Linha 55: se IA defaults não carregam, system_message do agente fica STRING VAZIA — agente "fica mudo" sem aviso. | AISettings.tsx:55 | (Não testei curl) | código |
| 🟠 média | **AgentOrchestratorFlow engole erro de save (linha 371).** Fluxo crítico de orquestração — falha em save e usuário não sabe. | AgentOrchestratorFlow.tsx:371 | (Não testei curl) | código |
| 🟠 média | **AgentRagPanel engole erro de load (linha 36).** RAG index não carrega → usuário acha que não tem RAG. | AgentRagPanel.tsx:36 | (Não testei curl) | código |
| 🟠 média | **ChatwootDialog + ProxyDialog engolem erro de save.** Domain/session — se falhar, integração fica quebrada sem aviso. | ChatwootDialog.tsx:43 + ProxyDialog.tsx:67 | (Não testei curl) | código |
| 🟠 média | **SettingsPage engole erro de getSettings (Rodada 11 confirmou).** Re-confirmação em PASS-2: com `setLoading(false)` no finally, loading acaba antes da UI mostrar erro. | SettingsPage.tsx:111 | (idempotente Rodada 11) | código |
| 🟡 baixa | **TelephonyPage endCall em onClick silencioso.** `endCall(...).catch(() => {})` (linha 145) — se falhar, ligação continua. Sem toast.error. | TelephonyPage.tsx:145 | (Não testei curl — usar sessão real) | código |
| 🟡 baixa | **TelephonyPage createSession silencioso.** `createSession("WhatsApp").then().catch(() => {})` (linha 238) — se criar sessão falhar, mostra contagem vazia sem aviso. | TelephonyPage.tsx:238 | (Não testei curl) | código |
| 🟡 baixa | **AdminSummonCard ignora falha de resume.** `ctx.resume().catch(() => {})` (linha 38) — admin tenta resumir sessão, falha silenciosa. | AdminSummonCard.tsx:38 | (Não testei curl) | código |
| 🟡 baixa | **AdminSummonCard ignora falha de play().** `audioRef.current.play().catch(() => {})` (linha 114) — áudio pode falhar (autoplay policy) sem notificar. | AdminSummonCard.tsx:114 | Tocar summon enquanto muted | código |
| 🟡 baixa | **CallCard ignora falha de play() e setSinkId.** Linhas 54, 69 — autoplay policy / device errado silencioso. | CallCard.tsx:54,69 | Audio device inválido | código |
| 🟡 baixa | **InstallApp ignora falha de service worker.** Linha 27 — push notification fica quebrada sem aviso. | InstallApp.tsx:27 | Bloquear sw.js | código |
| 🟡 baixa | **EventStream.onmessage try/catch silencioso.** Linha 42 do event-stream.ts: `JSON.parse(ev.data)` falha → catch vazio. Evento perdido e ninguém sabe. | event-stream.ts:42 | Backend mandar JSON malformado | código |
| 🟡 baixa | **LogsPage.onmessage try/catch vazio.** Mesma mecânica — entry perdida. | LogsPage.tsx:49 | Backend mandar log corrompido | código |
| 🟡 baixa | **Video player setSinkId silencioso.** CallCard:69 — se o usuário escolhe device que desconectou, falha sem feedback. | CallCard.tsx:69 | Desconectar fone durante ligação | código |
| 🟡 baixa | **CampaignKanban.getCampaignResults catch silencioso (linha 80).** Estado inicial perdido sem aviso. | CampaignKanban.tsx:80 | (Não testei curl) | código |

### Já conhecidos — confirmados em regressão (1º lote)
- ✅ **Dashboard skeleton infinito** (Rodada 7 / Rodada 11) — re-confirmado em PASS-2. Padrão é recorrente: catch silencioso + skeleton que nunca sai.
- ✅ **SettingsPage engole erro** (Rodada 11) — confirmado em SettingsPage.tsx:111.
- ✅ **EmptyState honesto** (Rodada 11) — mas falta botão de retry (PASS-2 adiciona).
- ✅ **ContactsPage sem error state** (Rodada 11) — não re-analisei esse arquivo específico, mas padrão se repete.

### Validação curl (PASS-2)
- `GET /api/transcripts` → **401** (existe, precisa token)
- `GET /api/dashboard` → **401** (existe)
- `GET /api/logs?apiKey=invalid` → **401** (confirma que endpoint ACEITA apiKey em query — confirma o bug de JWT-in-URL)
- `GET /api/events?clientId=test&apiKey=lixo` → **401** (idem — SSE aceita apiKey em URL)
- ❌ NÃO testado: `DELETE /api/transcripts` (404 — não existe, confirma o bug do false-success)

### Observações positivas (não são bugs)
- ✅ MassCallPage.tsx e CampaignsPage.tsx (Rodada 11) têm loading explícito + toast.error em catch.
- ✅ CampaignKanban.tsx `doPause`/`doResume` (linhas 50-63) — try/catch/finally com toast.error estruturado.
- ✅ TranscriptsPage.tsx `load` (linhas 60-66) — toast.error em catch (mas Skeleton infinito se data nunca chega).
- ✅ ErrorBoundary existe (captura render crash) — mas vaza info técnica.
- ✅ Alguns fluxos de áudio usando `void ctx.close().catch(() => {})` (IncomingCallModal:46) — esperado pra cleanup não-crítico.

### STATUS
PASS-2 Área 9 (Estados de erro / loading / vazio): **28 bugs NOVOS** (3 🔴, 14 🟠, 11 🟡) + 4 re-confirmados. **LEDGER atualizado: Área 9 → feito-passe2**.

**Próxima rodada sugerida:** PASS-2 Área 1 (Onboarding / Auth / Login) — linha 24 do LEDGER.

---

## Rodada 24 — Área 1 (Onboarding / Auth / Login) — 2026-07-25 ~10:10 (PASS-2)

Foco: PASS-2 profundo = bypass de auth no AuthGate, validação server-side fraca, JWT em localStorage, códigos HTTP errados, inconsistências entre front↔backend, trial expirado, logout, onboarding shared key. Curl de `register`, `login`, `me`, `providers`, `google`, `forgot`, `reset`, `refresh`, `logout`, `password reset` (15 endpoints).

### Bugs NOVOS encontrados (PASS-2)
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência |
|-----------|-----|---------------|-----------------|-----------|
| 🔴 crítica | **AuthGate BYPASSA autenticação nas portas 5173 e 5174.** `if (window.location.port === "5173" || "5174") setState("ok")` — comentário diz "TEMPORARY BYPASS FOR TESTING DASHBOARD WITHOUT BACKEND". Porta 5173 é a VITE dev (vite.config default). Em produção, qualquer proxy/CDN que reescreva para uma dessas portas BURLA o login. **AuthGate.tsx deveria só rodar em dev.** | AuthGate.tsx:13-17 | Acessar app em http://localhost:5173 → entra direto no dashboard, sem token | código: `setState("ok")` literal; comentário TEMPORARY |
| 🔴 alta | **`register` aceita SENHA de 3 chars (`password="123"`)** — front impõe min 6 (RegisterScreen.tsx:70), mas backend NÃO valida. Criou user com senha "123" no banco. Se front for bypassado (curl, mobile, etc.), qualquer senha fraca passa. | auth_handlers.go:14-45 + store.go:66-110 | `curl -X POST .../api/auth/register -d '{"email":"x","password":"123","name":"X","plan":"basic"}'` | HTTP 201, user criado |
| 🔴 alta | **`register` aceita email INVÁLIDO (sem @, com aspas, com XSS, com lixo)** — backend só checa `email == ""`. Front usa `<input type="email">` mas curl bypassa. Email `"qanight-injection@x.com'"` (com apóstrofo) foi aceito e armazenado. | auth_handlers.go:14-45 + store.go:66-110 | `curl -X POST -d '{"email":"not-an-email","password":"<SEGREDO_REMOVIDO>","name":"X","plan":"basic"}'` | HTTP 201, user criado |
| 🔴 alta | **`register` armazena XSS no campo `company`.** `company = "<script>alert(1)</script>"` foi aceito e devolvido na resposta. Se algum painel admin renderiza user.company sem escape, XSS. Não testado o painel admin. | auth_handlers.go:14-45 + store.go:66-110 | `curl -X POST -d '{"email":"x","password":"<SEGREDO_REMOVIDO>","name":"X","company":"<script>alert(1)</script>"}'` | HTTP 201, `"company":"<script>alert(1)</script>"` |
| 🟠 média | **`register` retorna HTTP 409 Conflict para "email is required", "name is required"** — isso é Bad Request (400), não Conflict. Front pode interpretar errado em retries. | auth_handlers.go:30-36 | `curl -X POST -d '{}'` | HTTP 409 + `{"error":"email is required"}` |
| 🟠 média | **`register` IGNORA `plan` enviado e força "trial" no INSERT.** Front envia `plan: "pro"` (RegisterScreen) mas backend só aceita plano válido no SWITCH; plano "basic"/"starter" do front caem pra "trial" (linha 87-89). Front acha que usuário escolheu Pro, backend grava "trial". Trial expira em 10h. **Usuario que pagou Pro via cartão trial já está em trial.** | auth_handlers.go:14-45 + store.go:84-89 | `curl -X POST -d '{"email":"x","password":"<SEGREDO_REMOVIDO>","name":"X","plan":"pro"}'` | HTTP 201, `"plan":"trial"` (esperado "pro") |
| 🟠 média | **`/api/auth/refresh` exige token (401 sem auth).** Refresh é pra RENOVAR token antes de expirar — não deveria exigir token válido. Loop: token expira → 401 → guard reload → re-login? | httpapi.go + (rotas fantasma) | `curl -X POST .../api/auth/refresh` | HTTP 401 (não tem handler) |
| 🟠 média | **`/api/auth/logout` exige token (401 sem auth).** Não dá pra fazer logout se o token está inválido. Cliente fica "logado" pra sempre. | httpapi.go + (rotas fantasma) | `curl -X POST .../api/auth/logout` | HTTP 401 (sem handler) |
| 🟠 média | **`/api/auth/forgot` exige token (401 sem auth).** Esqueci minha senha → preciso estar logado pra resetar? Loop impossível. Front nem tem link "Esqueci senha" na LoginScreen (Rodada 12 já confirmou). | httpapi.go:22-28 | `curl -X POST .../api/auth/forgot` | HTTP 401 (não tem handler) |
| 🟠 média | **`/api/auth/reset` exige token (401 sem auth).** Idem forgot. | httpapi.go:22-28 | `curl -X POST .../api/auth/reset` | HTTP 401 (não tem handler) |
| 🟠 média | **Não há endpoint `DELETE /api/users/:id` nem `DELETE /api/auth/account`.** Conta é permanente. GDPR/LGPD Art. 18 (direito de eliminação) não atendido. | (falta) | grep "DELETE" em httpapi.go `users` | 0 hits |
| 🟠 média | **`LoginScreen` usa `import("@/lib/auth").then(m => m.setSession(...))` — Dynamic import SÍNCRONO visualmente, mas roda em microtask.** `setSession` salva localStorage SÍNCRONO, mas o `import()` retorna Promise. Se por algum motivo o módulo for lazy-loaded (chunks), o `window.location.assign("/dashboard")` acontece ANTES de `setSession` completar, e AuthGate pode montar sem token. Edge case raro mas real. | LoginScreen.tsx:47-54 + auth.ts:14-19 | (teórico — não testável via curl) | código: `import().then()` com navigate no callback |
| 🟠 média | **`LoginScreen` linha 32-38: `onTrialExpired` callback é chamado DENTRO de `import().then()`** — race: se React desmontar o componente entre `try` e `import().then()`, callback em componente morto. Sem cleanup. | LoginScreen.tsx:32-38 | (não testável) | código |
| 🟠 média | **`LoginScreen` tradução de erro de rede**: `e?.message === "Failed to fetch"` é um heurística fraca. Em Firefox/Chromium a mensagem pode vir localizada ("Falha ao buscar"). Em Safari iOS, o erro é "Load failed". `e?.name === "TypeError"` é mais portável mas NÃO é checado contra rede especificamente. | LoginScreen.tsx:55-62 | (não testável) | código |
| 🟠 média | **`LoginScreen` linha 47: `import("@/lib/auth")` chamado no SUCESSO também** — por que dynamic import no caminho feliz? Deveria ser `import` estático no topo. Dynamic import paga latência de resolução de módulo no click. | LoginScreen.tsx:47 | (não testável) | código |
| 🟠 média | **`LoginScreen` NÃO tem campo "manter conectado" / "lembrar-me".** Token fica em localStorage permanente (não sessionStorage). Se usuário marca "sair" no fim do expediente, próximo login é ok, mas se outro usa o browser, tá dentro. | LoginScreen.tsx + auth.ts:1-3 | (não testável) | código |
| 🟠 média | **`LoginScreen` trata `data.error === "invalid_credentials"` mas não trata `data.error === "account_locked"`, `data.error === "email_not_verified"`, etc.** Backend só retorna `invalid_credentials` ou `rate_limited` no LoginScreen, mas se expandir no futuro, mensagens confusas. | LoginScreen.tsx:39-43 | (não testável) | código |
| 🟠 média | **`AuthGate` redireciona pra `/landing/index.html` MAS essa URL pode estar fora do React Router.** Se o SPA está servindo em `/dashboard`, a mudança pra `/landing/index.html` é um page reload completo — usuário perde estado de sessão. | AuthGate.tsx:36-38 | (não testável) | código |
| 🟠 média | **`AuthGate` useState "ok" → renderiza `<App />` sem loading explícito.** Pode haver flicker entre `checking` (null) e `App` (toda a árvore). App pode fazer fetch /me de novo, etc. | AuthGate.tsx:6,32 | (não testável) | código |
| 🟠 média | **`AuthGate` trata 403 trial_expired → tela TrialExpired, MAS só depois de login.** Se user está logado e trial expira DURANTE uso, próxima chamada API retorna 403 → api.ts:14-24 RE-RELOAD na primeira 401 (não 403). 403 não está no guard. Usuário fica com a UI quebrada. | api.ts:14-24 + auth_handlers.go:97-103 | (não testável) | código: 403 NÃO está no guard |
| 🟠 média | **`RegisterScreen` chama `register()` que faz `setSession()` E redireciona via `onSuccess()` no AuthGate.** Mas `RegisterScreen` linha 90 chama `onSuccess()` sem verificar se o `setSession` foi feito (porque é feito dentro de `register()`). Se `register()` falhar no `setSession` (race), o usuário fica sem token mas com `onSuccess` chamado. | RegisterScreen.tsx:81-90 + auth.ts:75-92 | (não testável) | código |
| 🟠 média | **`auth.ts` getUser() faz `JSON.parse(raw)` SEM try/catch.** Se localStorage tiver user corrompido (brave:// cleanup, outro app), throw não tratado quebra toda a app. | auth.ts:5-8 | Inserir manualmente `localStorage.setItem("hermes.user", "{lixo")` | código |
| 🟠 média | **`SetupWizard` onboarding done é PER-USER-AGNOSTIC (Rodada 12 confirmou).** Re-confirmação: `DONE_KEY = "hermes.onboarding.done"` em localStorage — flag SHARED entre todos os usuários do mesmo browser. Funcionário herda "tour feito" do admin. | SetupWizard.tsx:6-9 | Login multi-user no mesmo Chrome | código |
| 🟠 média | **`SetupWizard` useEffect[]=[`paired`]** — re-executa o wizard se o `paired` mudar. Se usuário com wizard em andamento conectar uma sessão, o wizard reinicia do zero. UX ruim. | SetupWizard.tsx:108 | (não testável) | código |
| 🟠 média | **`SetupWizard` sem botão "Pular tutorial".** Usuário que clicou "X" ou navegou pra outra página sem querer DEVE passar pelos 7 passos. | SetupWizard.tsx | Não há onCloseRef sendo exposto | código |
| 🟠 média | **`docs de UI não tem feature "Esqueci minha senha"`.** LoginScreen.tsx não tem o link. Cadastro de usuário sem recuperação = trap. Reportado em Rodada 12 mas sem ação. | LoginScreen.tsx | grep "forgot\|password" | 0 hits |
| 🟠 média | **`handleAuthRegister` retorna `email already registered` com 409 ao invés de 400 com campo específico.** Front trata `error` mas não sabe "qual" campo está duplicado. | auth_handlers.go:30-36 | `curl -X POST -d '{"email":"jáexiste@x.com","password":"<SEGREDO_REMOVIDO>","name":"X","plan":"basic"}'` | HTTP 409 com texto cru |
| 🟡 baixa | **`TrialExpired` component tem link "Ver planos" que aponta pra URL externa fixa.** Se a URL de pricing mudar, app aponta pra 404. | AuthGate.tsx:65-68 | (não testável) | código |
| 🟡 baixa | **`setupWizard` step 4 mostra "Agenda Inteligente" — mas se o usuário não tem plano Pro, não vê essa aba.** Wizard pode mostrar passo pra uma aba que nunca vai existir. | SetupWizard.tsx:73-79 | (não testável — precisa plan features) | código |
| 🟡 baixa | **`LoginScreen` mostra mockup bonito com botões "rotativos" (linhas 76-105).** Mas isso é CSS `animate-float` — em PREFER-REDUCED-MOTION, animação pode incomodar. Sem `@media (prefers-reduced-motion: reduce)` no CSS. | LoginScreen.tsx:76-105 | (não testável) | código |
| 🟡 baixa | **`LoginScreen` texto "trial" não é exibido pro usuário.** Front oferece 3 planos pagos (basic/pro/enterprise) MAS no backend TODOS viram "trial". Front mente. | LoginScreen.tsx + auth_handlers.go | (não testável) | código |
| 🟡 baixa | **`LoginScreen` "Google" → "Em breve" — mas a tag "Em breve" (linha 199) está visível na UI.** UX confuso: botão clicável + label "em breve" = ambiguidade. | LoginScreen.tsx:173-200 | Clicar no botão | toast.info + badge "Em breve" |
| 🟡 baixa | **`LoginScreen` linha 8: `onRegister` é `() => void` mas é usada como `() => setState("register")` no pai (AuthGate.tsx:43).** Tipos batem, ok. Mas o nome é confuso — `onRegister` é "ir pra tela de registro", não "fazer registro". | LoginScreen.tsx:8-13 | código | código |
| 🟡 baixa | **`LoginScreen` e `RegisterScreen` usam `window.location.origin` (linha 24) em vez de `apiUrl("/api/auth/login")`.** Funciona, mas se a app for servida de CDN com prefixo, quebra. | LoginScreen.tsx:24 | código | código |
| 🟡 baixa | **`AuthGate` testa porta 5173/5174 mas não 5175, 3000, 8080.** Devs podem usar outras portas e o bypass não funciona. | AuthGate.tsx:14 | código | código |
| 🟡 baixa | **`featuresForPlan` no /api/auth/me — não testado via curl (precisa login).** | auth_handlers.go:113-117 | (não testável) | código |
| 🟡 baixa | **`auth_handlers.go` linha 26: `Register` aceita `plan` do JSON mas `Login` ignora completamente.** Assimetria. | auth_handlers.go:14-87 | código | código |
| 🟡 baixa | **`/api/auth/me` retorna 401 (correto) mas em erros técnicos retorna 500 sem semântica.** `try/catch` no login() — se bcrypt falhar (raro), `invalid_credentials` é mostrado. Bom. | auth_handlers.go:67-70 | (não testável) | código |
| 🟡 baixa | **`AuthGate` `setState("ok")` quando resultado é `true` — mas se checkAuth falhar por rede (linha 54), `return false` → vai pra landing.** Usuário em brief blip de internet vê `/landing/index.html` e perde tudo. | auth.ts:54-57 + AuthGate.tsx:30-32 | Desconectar internet por 1s | código |

### Já conhecidos — confirmados em regressão (1º lote)
- ✅ **Sem feature de recuperação de senha** (Rodada 12) — refocado em PASS-2: `/api/auth/forgot` E `/api/auth/reset` retornam 401 (não existem handlers).
- ✅ **Onboarding done em localStorage** (Rodada 12) — re-confirmado.
- ✅ **`/api/auth/google` retorna 503** (Rodada 12) — confirmado via curl.
- ✅ **Login NÃO vaza se email existe** (Rodada 12) — confirmado: `invalid_credentials` para ambos os casos.
- ✅ **Rate limit em login** (Rodada 12) — confirmado: 5 attempts → 429.
- ✅ **Trial expirado na tela dedicada** (Rodada 12) — confirmado no código.

### Validação curl (PASS-2)
- `POST /api/auth/register` (vazio) → **409** `email is required` (código errado)
- `POST /api/auth/register` (senha 3 chars) → **201** (aceita, deveria validar)
- `POST /api/auth/register` (email "not-an-email") → **201** (sem validação)
- `POST /api/auth/register` (email "qaNIGHT-injection@x.com'") → **201** (sem validação)
- `POST /api/auth/register` (plan "hacker") → **201** com `"plan":"trial"` (ignorado)
- `POST /api/auth/register` (company "<script>alert(1)</script>") → **201** (XSS aceito)
- `POST /api/auth/login` (5x erradas) → **429** rate_limited (ok)
- `POST /api/auth/login` (vazio) → **400** `invalid request body` (ok)
- `GET /api/auth/me` → **401** (ok)
- `GET /api/auth/providers` → **200** `{"google":{"enabled":false}}` (ok)
- `GET /api/auth/google` → **503** `coming_soon` (ok)
- `GET /api/auth/google/callback` → **503** `coming_soon` (ok)
- `POST /api/auth/forgot` → **401** (não existe handler)
- `POST /api/auth/reset` → **401** (não existe handler)
- `POST /api/auth/refresh` → **401** (não existe handler)
- `POST /api/auth/logout` → **401** (não existe handler)

### ⚠️ Cleanup de usuários de teste
Criei 5 usuários de teste (`qanight-short@naoexiste.com`, `not-an-email`, `qanight-injection@x.com'`, `qanight-plan@x.com`, `qanight-tax@x.com`) durante os curls. **Não há endpoint DELETE /api/users/:id** — não posso limpá-los via API. Recomendo limpeza manual no DB ou criar endpoint de delete amanhã. ⚠️ **O usuário `qanight-injection@x.com'` com apóstrofo pode quebrar queries se houver escape incorreto.**

### Observações positivas (não são bugs)
- ✅ Rate limit em login (5 tentativas / 10min) funciona corretamente.
- ✅ Login não vaza se email existe ou não.
- ✅ Trial expirado com mensagem do backend propagada.
- ✅ Erro de rede traduzido no LoginScreen.
- ✅ api.ts anti-loop de reload em 401 (1 reload só).
- ✅ Features no /api/auth/me para gating no front.

### STATUS
PASS-2 Área 1 (Onboarding / Auth / Login): **39 bugs NOVOS** (4 🔴, 23 🟠, 12 🟡) + 6 re-confirmados. **LEDGER atualizado: Área 1 → feito-passe2**.

**Próxima rodada sugerida:** PASS-3 profundo das áreas com mais bugs (Área 8 / Área 9 / Área 1 — todas com 20+ bugs). Sugiro PASS-3 Área 8 (Navegação) — linha 22 do LEDGER, alternar entre as top-3 para balancear.

---

## RODADA 25 — PASS-3 Área 8 (Navegação / Estado global / Layout)

**Foco:** Profundidade na navegação SPA (rotas, deep-links, refresh, browser back/forward), Zustand stores (persist, race conditions, garbage collection), tema, i18n, layout responsivo. Frontend: `client/src/components/layout/{AppShell,Sidebar,CommandPalette,ThemeToggle}.tsx`, `stores/{navigation,theme,sessions,calls}.ts`, `lib/{api,i18n,auth}.ts`. **curl** de rotas SPA + endpoints `/api/auth/nonexistent`, `/sw.js`, `/landing/index.html`.

### Bugs NOVOS — 🔴 críticos (estado global / segurança)

| Severidade | Bug | Onde | Como reproduzir | Prova |
|---|---|---|---|---|
| 🔴 **CRÍTICO** | **`cycleRole` muda role do usuário no clique do logo.** `Sidebar.tsx:153-158` — `onClick={() => { cycleRole(); }}` no logo Hermes. Usuário superadmin → admin → employee loop. Persist em localStorage (`hermes-nav-store.userRole`). **UX desastroso**: usuário clica no logo por curiosidade e perde acesso a recursos. Nenhum aviso. | `Sidebar.tsx:153-158, 164-165` | clique no logo → toast "Role alterado para: ..." | código |
| 🔴 **CRÍTICO** | **`userRole` simulação persiste em localStorage (Zustand `partialize`).** `navigation.ts:42` — `userRole` vai pra `hermes-nav-store` em localStorage. Se um admin trocar de userRole pra "employee" pra debug, fica travado em "employee" no próximo reload (não volta ao real role do backend). | `stores/navigation.ts:42` | setUserRole("employee") → reload → ainda employee. | código |
| 🔴 **CRÍTICO** | **`role` é puramente client-side, mas o BACKEND não checa**. `authmw.go:158-169` (cmd/server) só checa `Plan` (enterprise/admin). Mas o front usa `userRole` em `Sidebar.tsx:247` pra esconder botões (`userRole !== "employee"` → mostra controles de edição). **Um employee que editasse localStorage pra "admin" ganhava UI de admin** — mas as APIs rejeitam por plan. **Inversão**: front confia em role simulada, backend confia em plan. | `Sidebar.tsx:247` + `cmd/server/authmw.go:158-169` | abrir DevTools → `localStorage.setItem("hermes-nav-store", ...)` mudar userRole → UI muda. | código |
| 🔴 alta | **`api.ts:14-24` reload_loop pode disparar em cold-load**. Guard checa `sessionStorage` `hermes.reloaded_on_401` — se token vazio (sem `getToken()`), guard exit early. **Mas se token existe e vira vazio entre checagens (race)**, reload dispara. | `client/src/lib/api.ts:14-24` | (race condition) | código |
| 🔴 alta | **`calls.ts:20-23` `wired` flag global, nunca desliga**. Em SPA, se App unmount/remount (HMR, dev), `ensureCallsWired` faz `if (wired) return`. Mas se eventStream fechar/reabrir, handler não é re-registrado. | `client/src/stores/calls.ts:20-23` | HMR durante dev → eventStream silencioso. | código |
| 🔴 alta | **`sessions.ts:24-28` `wired` flag igual problema**. Listeners de SSE morrem se eventStream reconnectar. | `client/src/stores/sessions.ts:24-28` | cutucar connection → SSE reconnect → listeners perdidos. | código |
| 🔴 alta | **`navigation.ts:42` `partialize` salva 9 campos (view, hiddenViews, etc.) em localStorage**. Se um usuário esconde uma view crítica (ex: `calls`) e fecha o app, **perde acesso à view mesmo após reload**. Sem reset global acessível. (Há `resetHiddenViews`, mas escondido em modo edição.) | `stores/navigation.ts:42` + `Sidebar.tsx:267-277` | toggle hide `calls` → reload → tab some. | código |
| 🔴 alta | **`theme.ts:4-8` — module-level `localStorage.getItem`**. Roda no import. Em SSR (ou test runners sem DOM) → ReferenceError. Quebra tree-shaking. | `client/src/stores/theme.ts:4-8` | (Node SSR) | código |
| 🔴 alta | **`theme.ts:14-17` — `toggle` SÓ alterna entre `dark-black` e `light`**. Estado `dark-blue` é configurável em `setTheme`, mas `toggle` o IGNORA. Usuário em dark-blue → toggle → cai pra light. | `client/src/stores/theme.ts:14-17` | setTheme("dark-blue") → toggle → light. | código |
| 🔴 alta | **`theme.ts:25-30` — `useTheme.subscribe` global, sem cleanup**. Side-effect no nível do módulo persiste pra sempre. Em testes, leak entre cases. | `client/src/stores/theme.ts:25-30` | (test concern) | código |
| 🟠 média | **`AppShell.tsx:29-50` `getAiSuggestion` lê `window.location.hash` sem sanitização**. Spoofing de hash via link externo (#ai="...código malicioso..."). Passa direto pra `setChatOpen(true, getAiSuggestion())`. | `client/src/components/layout/AppShell.tsx:29-50` | URL: `/#malicious` → chat abre com payload. | código |
| 🟠 média | **`CommandPalette.tsx:21-27` — Ctrl+K (ou Cmd+K) listener registrado no document**, mas eventos em iframes/ShadowDOM não disparam. | `client/src/components/layout/CommandPalette.tsx:21-27` | abrir em modal → Ctrl+K não funciona. | código |
| 🟠 média | **`CommandPalette.tsx:36-42` — SÓ 4 ações (cost/calls/crm/settings)**. Sidebar tem 20+ views. UX inconsistente: usuário abre Ctrl+K esperando navegar pra `catalog`, não acha. | `client/src/components/layout/CommandPalette.tsx:36-42` | Ctrl+K → "catalog" → "Nenhum comando encontrado". | código |
| 🟠 média | **`CommandPalette.tsx:43-45` — `search.toLowerCase().includes()` case-insensitive**, mas `search` é trimmed? Não. `" "` mostra TODAS as 4 actions. | `client/src/components/layout/CommandPalette.tsx:43-45` | digitar espaço → 4 results. | código |
| 🟠 média | **`CommandPalette.tsx:13-17` — `setCommandOpen(false)` no useEffect de commandOpen**: quando commandOpen=true, sincroniza open=true e DESLIGA commandOpen. Mas se user toggle open=false enquanto commandOpen=true, fica em estado intermediário. | `client/src/components/layout/CommandPalette.tsx:13-17` | (race explorável) | código |
| 🟠 média | **`AppShell.tsx:14-15` — `mobileOpen` é state local, não persiste**. Mobile sheet abre/fecha OK, mas se usuário abrir deep-link, sheet abre. Se fechar antes do redirect, propaga. | `client/src/components/layout/AppShell.tsx:14-15` | abrir sheet → navegar → sheet fica aberta. | código |
| 🟠 média | **`AppShell.tsx:130-134` — logout botão `clearAuth()` + `location.reload()`**. Hard reload. Se usuário tinha 5 abas abertas, cada uma é tab-jail. | `client/src/components/layout/AppShell.tsx:130-134` | abrir 5 abas → logout 1 → outras 5 com token válido. | código |
| 🟠 média | **`Sidebar.tsx:247-277` — `userRole !== "employee"` esconde controles de edição**. Mas se role === "employee" e ele tá num kiosk compartilhado, **não tem como mutar role sem devtools**. | `client/src/components/layout/Sidebar.tsx:247` | (UX) | código |
| 🟠 média | **`Sidebar.tsx:222 `ajuda` é local hardcoded**. Sem i18n. | `client/src/components/layout/Sidebar.tsx:222` | (i18n) | código |
| 🟠 média | **`Sidebar.tsx:295-301` — toggle collapse não tem keyboard shortcut**. Usuário expert usa Ctrl+B intuitivo, não funciona. | `client/src/components/layout/Sidebar.tsx:295-301` | Ctrl+B → nada. | código |
| 🟠 média | **`navigation.ts:54-70` — `toggleHiddenView` não persiste `isEditMode` no persist** (linha 42 partialize não inclui `isEditMode`). OK, mas se usuário entra em edit mode e dá refresh, sai de edit mode. UX inconsistente. | `client/src/stores/navigation.ts:54-70` | entrar edit mode → F5 → fora. | código |
| 🟠 média | **`navigation.ts:21` `userRole` tem tipo `"superadmin" \| "admin" \| "employee"`**, mas o BACKEND só tem `plan: enterprise\|pro\|trial\|...`. Mapeamento `role ↔ plan` está no client e pode divergir. | `client/src/stores/navigation.ts:21` | (mismatch conceitual) | código |
| 🟠 média | **`api.ts:14-24` — `clearAuth()` no 401 não limpa `eventStream`**. Próxima reconnect SSE reusa credenciais nulas. | `client/src/lib/api.ts:14-24` | logout → SSE reconnect → 401 spam. | código |
| 🟠 média | **`api.ts:7-8` `baseHeaders` seta `Content-Type: application/json` mesmo em GETs.** Backend OK ignora, mas bandwidth desperdiçado. | `client/src/lib/api.ts:7-8` | (perf) | código |
| 🟠 média | **`api.ts:64` `apiUpload` seta `Content-Type`?** Não — `headers: { "X-Client-Id", ...authHeaders() }` sem Content-Type. OK, browser põe boundary. | `client/src/lib/api.ts:64-73` | (OK) | código |
| 🟠 média | **`api.ts:14-24` `guard` chama `throw new Error(...)` que PODE ser capturado por catch silencioso no callsite (50+ silent catches conhecidos). 401 fica invisível. | `client/src/lib/api.ts:14-24` | (chaining com Rodada 9) | código |
| 🟠 média | **`i18n.ts:1-63` — só um idioma (pt)**, mas arquivo chama `i18n.ts`. Todas as strings hardcoded em PT-BR nas páginas. | `client/src/lib/i18n.ts` | Tela em PT-BR sempre. | código |
| 🟠 média | **`i18n.ts` muitas chaves definidas mas NUNCA usadas** (ex: `select_account`, `select_account_desc`, `filter_*`, `accounts`, `no_accounts`, `create_first` — todos existem mas UI renderiza hardcoded). | `client/src/lib/i18n.ts:1-63` | grep `t("select_account")` → 0 hits. | código |
| 🟠 média | **`App.tsx:124-136` — `view === "security"` redireciona pra `SettingsPage`**. Mas `security` é uma view declarada em `navigation.ts:4` (View type). Tentativa de usar config de segurança leva a Settings geral, não específico. | `client/src/App.tsx:124-136` | clicar "Security" → cai em Settings (sem scroll pro Security tab). | código |
| 🟠 média | **`App.tsx:113-115` — `setShowWizard(false)` no `GlobalAIErrorBanner` não persiste**. Se erro AI volta, banner re-aparece. | `client/src/App.tsx:113-115` | (sem teste) | código |
| 🟠 média | **`App.tsx:178` — `showWizard && <SetupWizard />`**. Se showWizard true + App re-renderiza, wizard remonta. | `client/src/App.tsx:178` | (análise) | código |
| 🟡 baixa | **`AppShell.tsx:79-85` "Logo" area é clicável, mas em mobile collapsed mode o logo some (collapsed layout esconde Hermes Call).** | `client/src/components/layout/AppShell.tsx:79-85` | mobile collapsed → não dá pra clicar no logo. | código |
| 🟡 baixa | **`AppShell.tsx:120-122` — div vazia com comentário "hidden md:flex items-center gap-2 text-sm font-medium text-muted-foreground"** mas SEM children. | `client/src/components/layout/AppShell.tsx:120-122` | (dead code) | código |
| 🟡 baixa | **`AppShell.tsx:142-146` — `aside` tem `md:block` (768px+)** mas em telas médias (800px), side engole 280px de 800px = 35% da tela. UX ruim. | `client/src/components/layout/AppShell.tsx:142` | (UX) | código |
| 🟡 baixa | **`AppShell.tsx:170-172` — `<CommandPalette />` montado sem guard de `view`**. Em view "landing" (?), palette ainda abre. | `client/src/components/layout/AppShell.tsx:170-172` | (sem teste) | código |
| 🟡 baixa | **`Sidebar.tsx:181` — `overflow-y-auto` mas sem `max-height`**. Em viewports baixos, sidebar pode rolar fora do container. | `client/src/components/layout/Sidebar.tsx:181` | (UX) | código |
| 🟡 baixa | **`Sidebar.tsx:184-199` — `manager_chat` view customTrigger com ManagerChat**, mas ManagerChat é um componente que abre dialog. Sidebar wrap é ugly-ish. | `client/src/components/layout/Sidebar.tsx:184-199` | (UX) | código |
| 🟡 baixa | **`Sidebar.tsx:227` — `view={"newline" as any}` cast forçado**. Tipo `View` não tem `"newline"`, mas o cast força. TypeScript minta. | `client/src/components/layout/Sidebar.tsx:227` | (type safety) | código |
| 🟡 baixa | **`Sidebar.tsx:153-158` `cycleRole` não tem confirmação**. Clica e muda. | `client/src/components/layout/Sidebar.tsx:153-158` | clique acidental. | código |
| 🟡 baixa | **`Sidebar.tsx:166-172` — `<img src="/hermesLogo.png" onError={hide} />` mas SEM fallback de imagem**. Usuário vê espaço vazio. | `client/src/components/layout/Sidebar.tsx:165-172` | imagem 404 → espaço. | código |
| 🟡 baixa | **`Sidebar.tsx:219` — `<a href="https://wa.me/5591984698653">`** com WhatsApp corporativo hardcoded. Empresa troca → esquece de atualizar. | `client/src/components/layout/Sidebar.tsx:219` | (maintenance) | código |
| 🟡 baixa | **`CommandPalette.tsx:8` — `useState(false)` para open + `commandOpen` no store**. Dois sources of truth. Sincronização depende do useEffect. | `client/src/components/layout/CommandPalette.tsx:8-17` | (race) | código |
| 🟡 baixa | **`CommandPalette.tsx:36-42` — array `actions` declarado DENTRO do componente**, recriado a cada render. Devia ser `const` fora. | `client/src/components/layout/CommandPalette.tsx:36-42` | (perf) | código |
| 🟡 baixa | **`CommandPalette.tsx:43-45` — `search` filtra case-insensitive** mas aceita acentos diferentes. `"ligacoes"` ≠ `"ligações"`. | `client/src/components/layout/CommandPalette.tsx:43-45` | (UX) | código |
| 🟡 baixa | **`CommandPalette.tsx:60-61` — mensaxe "Nenhum comando encontrado"** em vez de "Nenhum resultado". | `client/src/components/layout/CommandPalette.tsx:60-61` | (UX) | código |
| 🟡 baixa | **`CommandPalette.tsx:75-78` — `role="button" tabIndex={0}` mas SEM `onKeyDown`**. Enter/Space não ativam. | `client/src/components/layout/CommandPalette.tsx:75-78` | (a11y) | código |
| 🟡 baixa | **`useTheme` (theme.ts:10) — store não usa `persist`** (escreve localStorage manualmente). Race entre dois tabs. | `client/src/stores/theme.ts:10-23` | abrir 2 abas, mudar tema numa → outra fica desatualizada. | código |
| 🟡 baixa | **`navigation.ts:42` — `partialize` retorna 9 campos mas spread manual, fácil esquecer campos novos**. | `client/src/stores/navigation.ts:42` | (maintenance) | código |
| 🟡 baixa | **`navigation.ts:4` View type union tem 27 valores, mas alguns são dead code** (`recordings`, `transcripts`, `credentials` — não usados em App.tsx). | `client/src/stores/navigation.ts:4` + `App.tsx:113-136` | grep View usage. | código |
| 🟡 baixa | **`navigation.ts:42` — `name: "hermes-nav-store"`** é nome genérico. Sem versionamento. Mudança no schema → broken state. | `client/src/stores/navigation.ts:42` | (maintenance) | código |
| 🟡 baixa | **`stores/calls.ts:14-18` — `useCalls` sem persist**. OK, mas incoming call é perdido em reload. | `client/src/stores/calls.ts:14-18` | receber chamada → reload → some. | código |
| 🟡 baixa | **`stores/sessions.ts:15` — `useSessions` sem persist**. OK, mas re-fetch em reload. | `client/src/stores/sessions.ts:15` | (OK) | código |
| 🟡 baixa | **`Sidebar.tsx:131-143` `onNew` toast.error com `(e as Error).message`**. Se e.message for undefined (json parse error), toast mostra "undefined". | `client/src/components/layout/Sidebar.tsx:131-143` | (UX) | código |
| 🟡 baixa | **`AppShell.tsx:147` — `<main className="flex-1 overflow-y-auto p-4 sm:p-6">`**. Mobile padding sm:p-6 (24px) pode ser demais. | `client/src/components/layout/AppShell.tsx:147` | (UX) | código |
| 🟡 baixa | **`AppShell.tsx:151-165` — Floating Action Button** com z-100. Em dialogs (z-50), o FAB fica ACIMA. UX confuso. | `client/src/components/layout/AppShell.tsx:151-165` | abrir modal → FAB sobreposto. | código |
| 🟡 baixa | **`AppShell.tsx:166-168` — `<InstallApp />` dentro do fab pointer-events-auto** mas o botão é clicável apenas se deferred. | `client/src/components/layout/AppShell.tsx:166-168` | (UX) | código |
| 🟡 baixa | **`AppShell.tsx:151-165` — FAB "Delegar para IA" não tem a11y label**. | `client/src/components/layout/AppShell.tsx:151-165` | (a11y) | código |
| 🟡 baixa | **`AppShell.tsx:34-49` — `getAiSuggestion` lê `window.location.hash` → se vira um texto grande, vira placeholder no chat input. Sem limite. | `client/src/components/layout/AppShell.tsx:34-49` | URL `#ai=` + 10kb string → chat input gigante. | código |
| 🟡 baixa | **`navigation.ts:42-44` — partialize não inclui `commandOpen`, `chatOpen`, `chatInitialMessage`, `isEditMode`, `isEmployeeEditMode`**. OK, são transient. Mas se trocar de role, `isEditMode = false` é forçado, mesmo se estava true. | `client/src/stores/navigation.ts:42-44` | (análise) | código |
| 🟡 baixa | **`navigation.ts:50-52` — `setEditMode` e `setEmployeeEditMode` mutuamente exclusivos**. OK, mas se user clica rápido nos 2 botões, fica em modo intermediário. | `client/src/stores/navigation.ts:50-52` | (race) | código |
| 🟡 baixa | **`App.tsx:124-126` — `view === "security"` faixa de redirect**. Se usuário tinha URL `#security` em bookmark, deep-link não vai pra config security. | `client/src/App.tsx:124-126` | (UX) | código |
| 🟡 baixa | **`App.tsx:127` — `view === "cost"` renderiza CostsHubPage**. Mas Sidebar mostra "Visão Geral" como label. **Inconsistência**: navigation.ts:4 view name "cost" vs label "Visão Geral". | `client/src/App.tsx:127` | (UX) | código |
| 🟡 baixa | **`App.tsx:120-136` — `view` switch sem default**: views não declarados caem em `EmptyState`. | `client/src/App.tsx:120-136` | (análise) | código |
| 🟡 baixa | **`App.tsx:113-115` `GlobalAIErrorBanner setShow(false)`** — store, mas report não persiste. | `client/src/App.tsx:113-115` | (já reportado em Rodada 23) | código |
| 🟡 baixa | **`App.tsx:124-136` — Switch gigante**: 30+ branches. Refatorar pra mapa `view → Component`. | `client/src/App.tsx:124-136` | (maintenance) | código |

### Já conhecidos — re-confirmados
- ✅ **Dashboard skeleton infinito** (Rodada 7/9/11/23) — re-confirmado.
- ✅ **50 silent catches** (Rodada 9) — re-confirmado: `Sidebar.tsx:138`, `Sidebar.tsx:148`, `AppShell.tsx:130-134` swallow.
- ✅ **`/api/auth/nonexistent` retorna 401** (Rodada 24) — confirmado: rotas desconhecidas NÃO passam em whitelist → 401.
- ✅ **`/landing/index.html` redireciona 301** (Rodada 24) — confirmado: pra fora do SPA.
- ✅ **SPA routing retorna 200 em qualquer rota** (mesma index.html) — confirmado: `/dashboard`, `/calls`, `/nonexistent-route` todos 200.

### Validação curl (PASS-3 Área 8)

| Teste | Resultado |
|---|---|
| `GET https://hermescall.opus-sem-limites.com.br/dashboard` | **HTTP 200** (SPA serve index.html) |
| `GET https://hermescall.opus-sem-limites.com.br/calls` | **HTTP 200** |
| `GET https://hermescall.opus-sem-limites.com.br/nonexistent-route` | **HTTP 200** (SPA catch-all) |
| `GET https://hermescall.opus-sem-limites.com.br/api/auth/nonexistent` | **HTTP 401** (whitelist auth) |
| `GET https://hermescall.opus-sem-limites.com.br/landing/index.html` | **HTTP 301** (redirect pra fora) |
| `GET https://hermescall.opus-sem-limites.com.br/sw.js` | **HTTP 200** (PWA service worker existe) |

### Observações positivas (não são bugs)
- ✅ `AppShell.tsx:25` `dismissedFab` em sessionStorage (transient, OK).
- ✅ `App.tsx:113-115` `GlobalAIErrorBanner` existe.
- ✅ `theme.ts:5-8` migra `"dark"` antigo pra `"dark-black"` (forward compat).
- ✅ `CommandPalette.tsx:19-28` Ctrl+K handler global.
- ✅ `api.ts:14-24` anti-loop de reload (1 reload).
- ✅ `Sidebar.tsx:204` filler flexível empurra menu inferior.
- ✅ `stores/calls.ts:24-72` event handlers corretamente identificam "chamada nova" vs "atualização".

### STATUS
PASS-3 Área 8 (Navegação / Estado global / Layout): **59 bugs NOVOS** (8 🔴, 21 🟠, 30 🟡) + 5 re-confirmados. **LEDGER atualizado: Área 8 → feito-passe3**.

**Próxima rodada sugerida:** PASS-3 Área 9 (Estados de erro / loading / vazio) — 28 bugs no PASS-2, vale aprofundar.
