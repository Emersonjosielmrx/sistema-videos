# Night Shift — Auditoria completa Hermes Call — 2026-07-29

## SUMÁRIO EXECUTIVO (ler primeiro)

**1 bug CRÍTICO achado e corrigido no fonte (candidato a v0.3.2):**
- **#N4 — Lista de Funcionários IA quebra em produção.** `List`/`Get` de agentes falham no Scan quando `audio_id` é NULL (todo agente recém-criado + os 19 agentes reais de produção têm NULL). Efeito: a tela de Funcionários IA provavelmente vem VAZIA em produção, e `/api/agents/{id}/test` dá 404 falso. Minha memória de 23/07 já documentava esse bug como corrigido, mas o fix nunca chegou na branch de produção (`versao-final-bd24`). **Corrigi com `sql.NullString` e PROVEI no QA** (antes: profiles=null; depois: lista aparece). Fonte: `cmd/server/agentprofiles.go`. **Recomendo deploy v0.3.2.**

**1 incidente que EU causei e RESOLVI (produção limpa):**
- **#N3 — Vazamento QA→prod.** Meu container QA estava mal-configurado (namespace default → gravava em `wacalls_main`, produção). 25 contas de teste `qa_*@qa.test` vazaram pra prod. Detectei, limpei cirurgicamente as 25 (+ deps), preservando 194 users reais + 61 de outra sessão. Recriei o QA com isolamento REAL (banco próprio `wacalls_qa_main`). Produção OK.

**Achados menores:**
- **#N1 — Garimpo "Sincronizar" → 404.** Chama `/api/whatsapp/sync-app-state` que não existe. Auto-sync silencioso ao abrir a aba. NÃO mexi (é feature que a dona pediu; recomendo criar o backend OU desabilitar). 
- **#N5 — RAG/simulação IA:** não deu pra validar — todas as ~90 chaves Gemini estão sem cota (429). Não é bug de código.

**Áreas verificadas E2E e OK (#N6):** Webhook, Workspaces, n8n, Perfil, 2FA, Promessas, Analytics, ai-cost, Agenda config, guards de envio WhatsApp/mass (recusam sem sessão, não enviam). Team é honesto ("em desenvolvimento", sem dados fake).

**Produção:** intocada (v0.3.1 no ar). Todos os fixes estão só no fonte + QA. Deploy = sua decisão.

---

Ambiente: QA isolado de verdade (`hermes-call-qa` porta 8092, banco `wacalls_qa_main` via namespace, túnel SSH). **Produção intocada.**
QA build: `0.3.0-qa6` (com fix #N4). Método: dirigir pela UI/API real + verificar backend + tratar erro como bug (não "aceitar").

## Áreas a explorar (não cobertas antes)
- [ ] Chat / simulação de atendimento IA (`/api/ai/simulate`, chat send)
- [ ] Central de Telefonia (UI sem WhatsApp — guards)
- [ ] Meet com IA (`/api/meet/*`)
- [ ] Wizard de criar agente completo (9 etapas) E2E
- [ ] Follow-up wizard (view follow_up) + Promessas + Base Conhecimento (com credencial Gemini)
- [ ] Sub-abas restantes de Config: Webhook, n8n, Workspaces, Segurança, Perfil, Team, Aparência
- [ ] Analytics (várias telas)
- [ ] Formulários IA, Captação, Garimpo (sub-abas CRM não exploradas)

## Log de achados

### #N1 — Garimpo: botão "Sincronizar" → 404 (rota inexistente) [BUG REAL]
`WhatsAppExtractorTab.tsx:174` chama `POST /api/whatsapp/sync-app-state`, mas essa rota NÃO existe no backend (só há `/api/whatsapp/chats|instances|status`). Resultado: 404 sempre, inclusive no auto-sync ao abrir a aba Garimpo. Não há backend de app-state sync (feature whatsmeow não implementada).
→ Fix honesto: marcar botão "em breve"/desabilitar + remover o auto-sync que 404 silencioso ao abrir. (a fazer no batch)

### #N2 — 503 whatsapp/chats em várias telas [ESPERADO, não-bug]
Garimpo, Meet IA e outras chamam `GET /api/whatsapp/chats` → 503 sem WhatsApp pareado. Comportamento correto (conta trial não tem linha). Não é bug.

### #N3 — INCIDENTE MEU: QA vazou dados pra produção [RESOLVIDO]
O container QA foi criado com `WACALLS_PG_URL=.../wacalls_qa`, MAS o app deriva o banco do `WACALLS_PG_NAMESPACE` (default `wacalls`) → `mainDBName() = ns+"_main"` = `wacalls_main` (PRODUÇÃO). O nome do banco na URL é ignorado (`db.go:79`, `dsnFor` só troca o path pra sessões, mas auth/users/agentes usam mainDB). Resultado: as ~25 contas de teste `qa_*@qa.test` que criei foram gravadas em produção.
→ **Correção:** apaguei cirurgicamente os 25 users qa_*@qa.test + deps (1 agent_profile, 2 credentials) da wacalls_main via transação. Preservados 194 users reais + 61 @qa.local (de outra sessão). Produção limpa.
→ **Lição:** os "bugs de persistência" (agente não salva, RAG falha) que apareceram eram artefato do QA mal-configurado (namespace errado apontando pra main + falta da flag), NÃO bugs de produto. Verificar > reportar.
→ **A fazer:** recriar QA com `WACALLS_PG_NAMESPACE=wacalls_qa` pra isolar de verdade (usaria banco `wacalls_qa_main`).

### #N5 — RAG embeddings + ai/simulate falham por COTA Gemini esgotada [NÃO-BUG]
`POST /api/rag/documents` → 502 "embeddings 403/429"; `/api/ai/simulate` → 200 com reply "Erro ao processar com IA". Logs mostram `429 RESOURCE_EXHAUSTED` (free-tier limit 0) da API Gemini. Testei as ~90 chaves diretas de credenciais-canais: TODAS esgotadas (429). É limitação de cota das chaves, NÃO defeito de código — o app trata o erro corretamente (loga + mensagem amigável). Não dá pra validar RAG/simulação com IA real esta noite sem chave com cota.
- Observação de qualidade (não-bug): `/api/ai/simulate` retorna HTTP 200 mesmo quando a IA falha (erro vira texto do reply). É decisão de design (mostrar sempre algo), mas mascara falha de quem consome a API. Anotado pra avaliação.

### #N6 — Sub-abas Config + telas de dados: OK (verificadas E2E)
Testadas via API com verificação de persistência (não dependem de cota IA):
- **Webhook**: PUT `/api/settings/webhook` → readback em GET /api/settings ✅
- **Workspaces**: POST `/api/projects` → id ✅ (backend real)
- **n8n**: GET `/api/n8n` ✅ (behavior/token/url)
- **Perfil**: GET/PUT `/api/profile` ✅
- **2FA**: rotas setup/enable/disable/verify existem ✅
- **Promessas** (scheduled_calls): POST 201 → readback total=1 → DELETE 200 ✅ (E2E completo)
- **Analytics**: GET `/api/analytics` ✅ (avg_response_ms/daily/hourly)
- **ai-cost**: GET `/api/ai-cost` ✅
- **Agenda config/professionals**: GET ✅
- **Team**: `TeamPage.tsx` é HONESTO — mostra "em desenvolvimento" explícito, sem números fabricados. Não é fachada enganosa. ✅

## RODADA 2 (madrugada)

### #R1 — Produto aceita preço NEGATIVO [bug menor, validação]
`POST /api/catalog/products {price:-50}` → 200, persiste `-50`. Sem validação de preço >= 0. Impacto baixo (vitrine com preço negativo é esquisito, não perigoso). Fix: validar no handler `catalog_api.go`.

### #R2 — Produto com preço gigante → 500 [bug menor, robustez]
`POST /api/catalog/products {price:999999999999}` → 500 (provável overflow numérico) em vez de 400 validado. Fix: clampar/validar range no handler.

**FIX #R1+#R2 (aplicado + validado no QA qa7):** `catalog_api.go` POST e PUT agora validam preço/custo `>= 0` e `<= 1e9`. Provado no QA: negativo → 400 "não podem ser negativos"; gigante → 400 "acima do limite" (era 500); válido → 200. **Ainda NÃO em produção** (fixes menores; candidatos a v0.3.3 junto com outros acumulados). Não deployei sozinho — impacto baixo, agrupar pra próximo release.

### #R3 — XSS no nome (agente/produto): NEUTRALIZADO [não-bug]
`name:"<script>..."` aceito (200), MAS o frontend não usa `dangerouslySetInnerHTML` — React escapa por padrão. Não executa. OK.

### Validação/Auth: SÓLIDOS (rodada 2)
register senha curta → rejeita; email inválido → rejeita; campos obrigatórios (nome agente/etapa/evento) → 400; JSON malformado → 400; sem token → 401; token inválido → 401. Robustez boa.

### Meet IA / gravações: OK (rodada 2)
`/api/meet/turn` responde com lógica de wakeword (`should_respond`/`reason`); recordings/transcripts/agenda config/professionals respondem 200. Áreas funcionais.

### #R4 — Gating de plano: ENFORÇADO no backend [SEGURANÇA OK]
Conta `start_texto` (sem voz/reuniões) recebe 403 ao chamar `/api/mass-call/status` e `/api/meet/turn` DIRETO na API — não só escondido no frontend. Gating server-side correto, não dá pra burlar via API. Follow-up create funciona (200). Segurança bem feita.

### #R5 — Isolamento entre tenants (IDOR): PROTEGIDO [SEGURANÇA OK]
User B não consegue tocar dados de A: deletar agente de A não apaga (filtro user_id), acessar produto de A por id → 404, listar → só vê os próprios (0). Multi-tenant sólido.
- Observação menor (não-bug): DELETE cross-tenant retorna 200 mesmo sem apagar nada (WHERE user_id não casou = no-op). Não é falha de segurança (nada deletado), só status otimista pra no-op. Ideal seria 404, mas inofensivo.

### #R6 — id não-UUID vaza erro 500 do Postgres [bug de robustez, escopo médio]
PUT/DELETE com id inválido (ex: "nao-eh-uuid") em colunas UUID → 500 "invalid input syntax for type uuid" em vez de 404/400. Afeta: PUT/DELETE produto, DELETE credencial, DELETE evento agenda, DELETE followup, DELETE chave. NÃO afeta: GET produto (404 ok), DELETE agente/etapa CRM (colunas TEXT, tratam como no-op).
- Não é falha de segurança (não expõe dado), mas é resposta feia + polui logs. Causa: query `WHERE id=$2` força cast implícito string→uuid.
- Fix: comparar `id::text = $2` (como o agent_profiles.Get já faz) OU validar formato UUID no handler → 404. Escopo: ~5 stores.
- **FIX #R6 APLICADO + VALIDADO no QA (qa8):** `id::text=$N` em catalog (UPDATE/soft-delete/restore), agenda (status/update/delete), followup (sequences/campaigns/steps), credentials, api_keys. Provado: os 6 endpoints que davam 500 agora dão 200 no-op (id inválido não casa, sem crash). Melhoria de robustez. NÃO em produção ainda (candidato a v0.3.4). Obs: 200-no-op em vez de 404 é aceitável (o crash sumiu; mesmo comportamento que agente/etapa já tinham).

### Bloco A (CRUD c/ edição): OK — agente/produto/evento criam→editam→confirmam→deletam sem duplicar.
### Bloco B (concorrência): OK — 10 POSTs simultâneos → 1 registro (upsert); delete 2x idempotente. Só o #R6 acima destoou.

### Bloco D (segurança aprofundada): SÓLIDO ✅
- SQLi na busca (`q=' OR 1=1--`) → 200, 0 resultados, sem vazar (queries parametrizadas).
- SQLi no nome ("'; DROP TABLE users;--") → salvo como texto literal; tabela users intacta.
- Secret masking: chave de credencial volta mascarada (AIz...Gnzs), não a real; telegram token não vaza no GET.
- Somado a #R4 (gating 403) e #R5 (IDOR protegido): segurança bem feita em SQLi/XSS/IDOR/gating/mask. Nenhum furo achado.

### Bloco E (fuzzing): robusto, sem crashes ✅
Backend aguentou: nome/prompt 50k chars → 200 (sem limite mas não quebra); emoji/unicode → 200; data inválida → 400; array onde espera string → 400; body vazio → 400. Nenhum 500 de crash.
- Robustez menor (não prioritário): `delay_minutes` negativo/gigante no followup → 200 (validação frouxa, mas pior caso é timing esquisito, não crash). Candidato a validação futura, baixo impacto.
- `rag/search top_k negativo` → 502 mas é o erro de COTA Gemini (embeddings), não o top_k — não isolável sem chave viva.

### PENDENTE (precisa de você / recurso externo)
- **Chave Gemini com cota** pra validar RAG/simulação/embeddings (todas as ~90 estão 429).
- **v0.3.4**: agrupar fix #R6 (id::text, robustez) quando quiser — está no fonte+QA, validado, não deployado.

### Bloco G (consistência backend↔frontend): LIMPO ✅
Cruzei 108 paths /api/ chamados pelo frontend × 314 rotas do backend. Só 2 divergências:
- `/api/foo` — placeholder num COMENTÁRIO de doc (lib/log.ts), não é chamada real. Inofensivo.
- `/api/whatsapp/sync-app-state` — o #N1 já conhecido (Garimpo). 
Nenhum outro endpoint fantasma. Consistência sólida.

### Bloco C (6 planos): PERFEITO ✅
Todos os planos gravam certo e as tabs batem 100% com plan_features.go: trial 9, start_texto 5, start_voz 3, pro 8, scale 9, enterprise 9. Gating de Meet IA por plano: trial/scale/enterprise=200, start_texto/start_voz/pro=403. Regras de negócio + segurança corretas.

## RODADA 4

### Bloco I (integridade referencial): OK, 1 achado menor
- Etapas CRM: board count sobe/desce certo (11→12→11). Contadores promessas batem.
- **#R7 (baixa prioridade)**: deletar produto A que é `upsell_id` de B deixa referência dangling em B (upsell_id aponta pra produto inexistente). NÃO quebra (GET B = 200). Causa: `upsell_id` é coluna TEXT solta, sem FK/constraint, sem JOIN de resolução no backend — é design de referência frouxa. Impacto mínimo (UI trata upsell inexistente como vazio). Melhoria futura: limpar upsell_id órfão ao deletar. Não corrigido (baixo impacto, mexeria no fluxo de delete).

### #R8 — Limites de QUANTIDADE de plano NÃO são enforçados [regra de negócio, decisão da dona]
`plan_features.go` define MaxAgents/MaxInstances/MonthlyTokens por plano, MAS `grep` confirma que esses campos NUNCA são checados em nenhum handler. Testado: conta `start_texto` (MaxAgents=3) criou 5 agentes sem bloqueio. As ABAS são enforçadas (#C), mas os LIMITES DE QUANTIDADE não.
- **NÃO corrigido autonomamente** porque é regra de monetização (qual limite realmente vale é decisão da dona) e implementar errado bloquearia clientes pagantes. Documentado pra decisão. Se ela confirmar que os limites devem valer, o fix é: no handleCreateAgentProfile (e criar-instância), contar os existentes e comparar com featuresForPlan(plan).Limits antes de criar → 403 se estourar.

### Nota sobre falsos-alarmes da noite
Vários "bugs" investigados viraram artefato do QA quebrado. Isso reforça: dirigir pela UI E confirmar a causa raiz antes de chamar de bug.

### #N4 — BUG CRÍTICO: List/Get de agentes quebra com audio_id NULL [REAL, corrigido no fonte]
`agentprofiles.go` List() e Get() escaneavam `audio_id/audio_signature/trigger_audio_id/offer_audio_id` (colunas UUID/text NULLABLE) direto em `string`. Agente SEM áudio cacheado (todo recém-criado + os 19 de produção) tem NULL nessas colunas → driver falha ("converting NULL to string") → List retorna vazio (`{"profiles":null}`) e Get cascateia 404 "agente não encontrado" mesmo o agente existindo. Afeta: listar Funcionários IA, `/api/agents/{id}/test`, attach-pending.
- **Prova QA:** audio NULL → `{"profiles":null}`; após `UPDATE ... SET audio_id=gen_random_uuid()` → lista aparece. Determinístico.
- **Contexto:** memória `hermes-agent-profile-null-safe-scan` (2026-07-23) já documentava ESTE bug como corrigido, mas o fix (sql.NullString) NUNCA chegou na branch `versao-final-bd24` (que gerou v0.3.0/v0.3.1 em produção). `git log --all -S "sql.NullString"` = 0. Regressão / fix perdido no merge.
- **Fix aplicado:** List() e Get() agora usam `sql.NullString` nas 4 colunas + copiam `.String` pro struct. (a validar no QA + rebuild)
- **IMPACTO PRODUÇÃO:** os 19 agentes reais têm audio_id NULL. A UI Funcionários IA carrega via `GET /api/agent-profiles` (SpecializedAgents.tsx:249) e o adapter `/api/agents` (agents_adapter.go:69) — AMBOS usam o List quebrado. Logo, em produção a tela de agentes provavelmente vem vazia/quebrada. CANDIDATO FORTE a v0.3.2 (deploy urgente).
- **PROVADO NO QA (qa6):** após o fix, criar agente com audio NULL → `GET /api/agent-profiles` count=1 (era null), `/api/agents` count=1, `/api/agents/{id}/test` = 503 (sem credencial IA, correto — não mais 404). Bug resolvido.

---
