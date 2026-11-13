# PLANO DE TESTE NOTURNO — Hermes Call (12h autônomas)

> **LEIA ISTO PRIMEIRO. VOCÊ É UM AGENTE DE TESTE. SUA ÚNICA FUNÇÃO É TESTAR E DOCUMENTAR BUGS.**
>
> **REGRA MÁXIMA — NÃO EDITE NADA.** Você está PROIBIDO de: editar qualquer arquivo `.go`, `.ts`, `.tsx`; rodar deploy; commitar; alterar banco de dados de produção; apagar dados que você não criou. Se você sentir vontade de "corrigir" um bug, PARE — apenas ANOTE no relatório. Quem corrige é o humano de manhã.
>
> **O QUE VOCÊ FAZ:** roda testes, observa o resultado, e ESCREVE o que encontrou no arquivo de relatório. Só isso.

---

## 0. CONTEXTO (o que é esse sistema)

- **Hermes Call** = SaaS multi-tenant de WhatsApp + IA + telefonia. Cada cliente ("tenant") tem sua conta, suas linhas de WhatsApp, seus agentes de IA, contatos, campanhas de ligação, agenda, catálogo.
- **Produção:** https://hermescall.opus-sem-limites.com.br (Traefik → porta 8080). Está no ar como **beta**.
- **Working dir:** `d:/hipercool-refactor`. Backend Go em `cmd/server/` + `internal/`. Frontend React+Vite em `client/src/`.
- **Rotas da API:** registradas em `cmd/server/httpapi.go` (procure por `mux.HandleFunc`). São ~378 rotas.
- **Auth:** toda rota (menos algumas públicas) exige header `Authorization: Bearer <token>` OU `X-API-Key`. Sem token → HTTP 401.
- **Multi-tenant:** cada handler filtra por `userFromCtx(u.ID)`. Bug de segurança comum = handler que NÃO filtra por dono.

## 0.1 ZONA PROIBIDA (NÃO TESTE, NÃO TOQUE)

- **NÃO** dispare ligações reais nem campanhas de verdade (custa dinheiro e pode banir a linha WhatsApp da dona).
- **NÃO** teste `internal/voip/call/*` nem `internal/voip/signaling/*` — outro agente está mexendo lá.
- **NÃO** envie mensagens de WhatsApp reais pra números que não sejam de teste.
- **NÃO** delete campanhas, contatos, agendamentos, gravações que já existem (só apague o que VOCÊ criou pra teste, e sempre limpe depois).
- Se for criar dados de teste, use prefixo `qaNIGHT-` no nome pra identificar e limpar depois.

---

## 1. COMO TESTAR (as duas técnicas)

### Técnica A — Leitura de código (a principal)
Para cada tela/botão/campo, ABRA o arquivo e RASTREIE o caminho completo:
1. **Frontend:** ache o componente em `client/src/`. Veja se o botão tem `onClick`/`onChange` de verdade (não vazio).
2. **Chamada:** veja qual função de serviço ele chama (`apiGet`/`apiPost`/`apiPut`/`apiDelete` em `client/src/lib/api.ts` ou `client/src/services/`).
3. **Rota:** confirme que essa rota EXISTE em `cmd/server/httpapi.go`.
4. **Backend:** abra o handler Go. Veja o que ele faz com os dados.
5. **Chave JSON:** COMPARE o campo que o front envia com a tag `json:"..."` do struct Go que decodifica. **Se forem diferentes, o dado é PERDIDO silenciosamente.** (Esse foi o bug mais comum já achado: front manda `system_msg`, backend lê `system_message`.)
6. **Persistência:** veja se o handler realmente grava no banco (`INSERT`/`UPDATE`) ou só responde OK sem salvar.

### Técnica B — Teste HTTP contra produção (confirmação)
Use `curl` contra `https://hermescall.opus-sem-limites.com.br`. Regras:
- Rota sensível SEM token deve dar **401** (não 200, não 404, não 500).
- **401** = rota existe e exige auth (bom). **404** = rota não existe (UI pode estar chamando endpoint fantasma). **500** = erro no servidor (bug).
- Para testar com login, veja se há credenciais de teste em `tests/.state/accounts.json`. Se houver, use o token de lá. Se NÃO houver, faça só os testes de leitura de código + os curl sem token (checando 401 vs 404 vs 500).
- **NUNCA** rode curl que dispare ligação, campanha ou mensagem real.
- Sempre use `--max-time 15` pra não travar. No Git Bash, use `export MSYS_NO_PATHCONV=1` antes dos curl com path `/api/...`.

### Como classificar cada bug encontrado
- 🔴 **crítico** — perda de dado, falha de segurança (cross-tenant), ou quebra de build.
- 🟠 **grave** — feature fake que PARECE real e funcional (falso-sucesso: mostra "salvo!" mas não salva; mostra dado inventado como se fosse real).
- 🟡 **médio** — mock claramente rotulado, cosmético, ou config que salva mas ninguém lê.
- ⚪ **menor** — texto errado, inconsistência de nome, botão sem onClick que não engana ninguém.

---

## 2. ONDE JÁ SABEMOS QUE TEM BUG (confirme se ainda existem, NÃO conserte)

Estes já foram achados. Sua tarefa é **CONFIRMAR se ainda estão lá** (alguns podem ter sido corrigidos no último deploy) e procurar VARIANTES parecidas em telas que ninguém olhou:

- **Struct duplicado com tags divergentes** (raiz de vários bugs): existe um struct em `cmd/server/*.go` com tag JSON errada E outro em `internal/settings/store.go` com a tag certa. Procure TODOS os casos: `grep` por campos que aparecem nos dois lugares com nomes diferentes. Exemplos já achados: Rate Limit (`features_api.go:848`), IP Whitelist (`ipwhitelist.go:13` usa `allowed_ips`, front usa `ips`).
- **Salvar X apaga Y**: em `SpecializedAgents.tsx:112`, salvar o gatilho manda um objeto parcial que zera voz/áudios/extras do agente. Procure outros saves que mandam objeto incompleto (padrão: `apiPut(rota, { só_alguns_campos })` quando o backend substitui o registro inteiro).
- **Config que salva mas ninguém lê**: n8n (`n8n_api.go` — token salvo, nada consome), Webhook eventos (`WebhookSettings.tsx:67` — seleção ignorada, dispara tudo). Procure outras: pra CADA config salva, faça `grep` se algum código de runtime a LÊ.
- **Switch/campo fantasma**: `ManagerAgentSettings.tsx:224-272` — 4 superpoderes gravados via `(cfg as any)` que o struct Go descarta. Procure outros `(cfg as any)` ou campos que o front manda mas não existem no struct.
- **Catch que inventa dado**: telas que no `catch` de erro mostram dado fake (ex. antes: FollowUpPage régua fantasma, ProfilePage WhatsApp fake). Procure `.catch(` seguido de `setState(algo_fixo)`.
- **Status sempre verde**: `AICredentialsSettings.tsx:276` — `RecordFailure` nunca é chamado, chave estourada aparece "Conectado". Veja se há outros indicadores de saúde que nunca mudam.
- **Delete sem confirmação**: RecordingsPage, WorkspaceSettings, TagsPage, BlocksPage apagam sem `confirm()`. Liste todos os deletes e diga quais confirmam e quais não.
- **Segurança cross-tenant**: `httpapi.go:744-783` (Delete/Logout/Pair de sessão) não validam dono. Procure outros handlers `{id}` que operam sem `sessionByID` ou sem `WHERE user_id=`.

---

## 3. ROTEIRO DE TESTE POR ÁREA (faça NA ORDEM, uma por vez)

> Para CADA área: liste os elementos (botões/campos/toggles), teste cada um pelas Técnicas A e B, e escreva os achados no relatório ANTES de passar pra próxima área. Marque a área como ✅ no relatório quando terminar.

### ÁREA 1 — Autenticação e conta
- Arquivos: `client/src/components/auth/LoginScreen.tsx`, `RegisterScreen.tsx`, `client/src/AuthGate.tsx`, `cmd/server/auth_handlers.go`, `internal/auth/store.go`.
- Testar: login (rate limit funciona? quantas tentativas?), registro (planos aceitos — o backend aceita `start_voz`/`start_texto`/`scale` ou só trial/pro/enterprise?), trial expirado (fluxo), logout.
- curl: `POST /api/auth/login` com corpo vazio → deve dar erro tratado, não 500.

### ÁREA 2 — Dashboard / Visão Geral
- Arquivos: `client/src/pages/DashboardPage.tsx`, `cmd/server/panel_analytics.go`.
- Testar: cada card/número vem de dado real ou hardcoded? Gráficos com dado real ou mock? O que acontece se a API falha (skeleton infinito? toast?).
- Já sabido: `healthStatus` é hardcoded "ok" (banner de alerta nunca aparece). Confirme.

### ÁREA 3 — CRM / Gestão de Leads
- Arquivos: `client/src/pages/CRMPage.tsx`, `ContactsPage.tsx`, `ListsPage.tsx`, `TagsPage.tsx`, `BlocksPage.tsx`, `client/src/components/catalog/WhatsAppExtractorTab.tsx`, `crm_store.go`, `crm_api.go`, `contacts.go`.
- Testar: board CRM (mover lead persiste?), Filtros Avançados de Contatos (score/status funcionam? — foi corrigido recentemente, confirme), "Salvar como Segmento", tags (coluna "Audiência" tem número real ou hardcoded 0?), blocklist (duração 7/30 dias é enviada ou todo bloqueio é permanente?), "Marcar como Lido" no Garimpo (persiste ou só state local?).

### ÁREA 4 — Agenda
- Arquivos: `client/src/pages/AgendaPage.tsx`, `client/src/components/settings/AgendaSettings.tsx`, `AgendaAnalytics.tsx`, `agenda_api.go`, `agenda_store.go`.
- Testar: criar agendamento (persiste? conflito 409?), bloqueios de dia/data (foi corrigido — confirme que agendar num dia bloqueado agora dá erro 409), link público `/book/` (existe a rota ou dá 404?), botão "Dossiê IA" (tem onClick?), profissionais/blocks/waitlist (têm UI ou é backend órfão?).

### ÁREA 5 — Catálogo / Vitrine
- Arquivos: `client/src/pages/` (catálogo), `client/src/components/catalog/*`, `catalog_api.go`, `catalog_store.go`.
- Testar: criar/editar produto, estoque crítico, catálogo público (`GET /api/catalog/public?owner=<uuid>` — e teste com owner inválido: vaza erro SQL cru?), aba de assinatura (add-ons são reais ou decorativos?).

### ÁREA 6 — Telefonia (SÓ LEITURA — NÃO DISPARE NADA)
- Arquivos: `client/src/pages/TelephonyPage.tsx`, `CallsPage.tsx`, `client/src/components/session/*`.
- Testar (SÓ olhando código e UI, SEM ligar): Copiloto/Sussurro é real ou texto fixo? Badges "Monitoramento Ativo"/"Latência" são reais ou estáticos? Análise de sentimento existe? **NÃO clique em discar/ligar.**

### ÁREA 7 — Meus Funcionários / Agentes / Lab
- Arquivos: `client/src/components/settings/SpecializedAgents.tsx`, `EasyAgentWizard.tsx`, `AdvancedLab.tsx`, `AgentOrchestratorFlow.tsx`, `agentprofiles.go`.
- Testar: criar agente (persiste?), Roteamento Nível 1 (quem atende voz/texto — a seleção salva ou some ao trocar de tela?), GamificationPanel (receita/ranking é real ou hash do ID?), salvar gatilho (apaga o resto do perfil? — já sabido, confirme), simuladores/testes de voz (reais ou fake?).

### ÁREA 8 — Chat de Teste / Treinador / Base de Conhecimento (RAG)
- Arquivos: `client/src/components/settings/AgentChatTest.tsx`, `AgentTrainerPanel.tsx`, `GlobalRagManager.tsx`, `KnowledgeManagerTab.tsx`, `AgentRagPanel.tsx`, RAG no backend.
- Testar: KnowledgeManagerTab (é placebo? botões disabled?), GlobalRagManager (bases globais são fake/`MOCK_DATASETS`? sync de conector persiste? chunks editáveis vão ao backend?), chat de teste (núcleo funciona? controles de áudio/anexo/stress são decorativos?).

### ÁREA 9 — Follow-up / Réguas
- Arquivos: `client/src/pages/FollowUpPage.tsx`, `followup_sequences.go`, `followup_api.go`.
- Testar: carregar sequências (mostra dado real ou régua fantasma no erro? — corrigido, confirme), criar/deletar sequência (persiste ou finge no catch?).

### ÁREA 10 — Configurações (todas as sub-abas)
- Arquivos: `client/src/components/settings/*`, `settingsapi.go`, `models_api.go`, `features_api.go`.
- Testar: Gestor Fácil (prompt real carrega? não sobrescreve com default? — corrigido, confirme), 4 superpoderes do Gestor (salvam de verdade ou são fantasma?), Credenciais IA (status sempre "Conectado"?), Listar modelos (funciona com credencial vinculada ou só com chave manual?), Voz/TTS (testar voz Piper NÃO exige mais API key — confirme; teste Edge também), Webhook (seletor de eventos filtra ou dispara tudo?), n8n (config é consumida ou fachada?), Schedule (horário comercial vale na hora ou demora 5min?), Aparência (cores persistem no refresh?), Rate Limit (tela carrega valores salvos? save preserva os 3 campos?), IP Whitelist (IPs persistem no save?).

### ÁREA 11 — Segurança transversal (SÓ curl sem token + leitura, NÃO explore de verdade)
- Testar (documentar, NÃO explorar contra dados reais): liste rotas públicas em `authmw.go` e diga se cada uma DEVE ser pública. Confirme (por leitura de código) o hijack de sessão em `httpapi.go:744-783`. **NÃO** faça o ataque real de apagar sessão de outro tenant — só descreva o caminho no código.

### ÁREA 12 — Features órfãs (backend sem UI / UI sem backend)
- Extraia todas as rotas de `httpapi.go` (`grep mux.HandleFunc`). Extraia todas as chamadas de API do front (`grep apiGet/apiPost/apiPut/apiDelete/fetch` em `client/src`). Compare: rotas backend que NENHUM front chama = candidatas a órfãs (confirme que não são chamadas por cron/webhook/telegram antes de listar). E o inverso: chamadas do front pra rotas que não existem.

---

## 4. FORMATO DO RELATÓRIO (onde escrever)

Escreva TUDO no arquivo **`_ACHADOS_NOTURNOS.md`** (na raiz `d:/hipercool-refactor`). NÃO edite o `_QA_CONSOLIDACAO_2026-07-24.md` (é o mapa do humano).

Estrutura do relatório — a cada rodada, ADICIONE (nunca apague o que já escreveu):

```
## Rodada N — <área testada> — <timestamp>

### Bugs novos encontrados
| Gravidade | Bug | Arquivo:linha | Como reproduzir | Evidência (curl/leitura) |
|-----------|-----|---------------|-----------------|--------------------------|
| 🔴 | ... | ... | ... | ... |

### Bugs já conhecidos que CONFIRMEI ainda existem
- ...

### Bugs já conhecidos que parecem CORRIGIDOS
- ...

### Áreas cobertas nesta rodada
- ✅ Área X (100% dos elementos)
- ⏳ Área Y (parei no elemento Z, continuar daqui)
```

**Regras do relatório:**
- Seja ESPECÍFICO: sempre `arquivo:linha`. "Tem um bug no CRM" é inútil. "TagsPage.tsx:60 hardcoda `leads:0`" é útil.
- Se você não CONSEGUIU testar algo (faltou credencial, etc.), ANOTE como "não testado: motivo".
- NUNCA invente um resultado. Se não rodou, não escreva que passou.
- No fim de cada rodada, escreva uma linha de STATUS: quantas áreas cobertas de 12, e qual a próxima.

---

## 5. CHECKLIST DE FIM DE CADA RODADA (marque mentalmente)
1. [ ] Escrevi os achados no `_ACHADOS_NOTURNOS.md`?
2. [ ] NÃO editei nenhum arquivo de código?
3. [ ] NÃO disparei ligação/campanha/mensagem real?
4. [ ] Limpei os dados de teste `qaNIGHT-` que criei?
5. [ ] Anotei onde parei pra próxima rodada continuar?

## 6. ORDEM DE PRIORIDADE (se o tempo acabar antes de cobrir tudo)
Cubra nesta ordem — as primeiras são as que mais importam pro dono:
1. Áreas 10 (Config — onde mais aparece falso-sucesso) e 7 (Agentes)
2. Área 3 (CRM) e 4 (Agenda)
3. Área 11 (Segurança) e 12 (Órfãs)
4. Resto (Dashboard, Catálogo, Telefonia, Chat/RAG, Follow-up, Auth)

Se já cobriu tudo uma vez e ainda há tempo: FAÇA DE NOVO com mais profundidade — teste casos de borda (campos vazios, valores enormes, caracteres especiais, unicode, campos que dependem de outros).
