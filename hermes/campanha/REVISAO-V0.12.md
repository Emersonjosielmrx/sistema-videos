# Revisão v0.12.0 — para outro agente conferir

Escrito em 14/10/2026. Branch `ia-so-campanha`, worktree `D:\hermes\wt-campanha-only`.

---

## O que foi feito (commits na branch)

### 1. Opção "só campanha" (`campaign_only`) — commit bbd08a0

**O que é:** nova opção por conta que faz a IA só responder texto no WhatsApp e só retornar
ligação perdida de quem foi discado numa campanha em massa recente (rodando ou terminada há
até 30 dias). Amigos, família e números de teste antigos não recebem nenhuma ação da IA.

**Arquivos alterados:**
- `internal/settings/store.go` (~linha 231): campo `CampaignOnly bool` em `AgentChatSettings`
- `internal/whatsapp_campaigns/store.go` (~linha 958): `InRecentCampaignAny` — SQL que conta
  `campaign_results` por campanha (não usa `campaigns.total`, que conta 2x) e casa por número,
  JID ou parte do JID
- `cmd/server/autoreply.go` (~linha 302): guard `CampaignOnly` no pipeline de auto-reply
- `cmd/server/missed_callback.go` (~linha 140): guard `CampaignOnly` em `callbackBlockedReason`
- `cmd/server/settingsapi.go`: GET e PUT preservam `campaign_only`
- Testes: `so_campanha_test.go` (2 testes DB), `agentchat_preserva_test.go`

**Pontos para conferir:**
- [ ] `InRecentCampaignAny`: a subquery `(SELECT COUNT(*) FROM campaign_results x ...)` pode
      ser lenta em campanhas grandes. Verificar se há índice em `campaign_results(campaign_id)`.
- [ ] O guard em `autoreply.go` está DEPOIS do `OutboundOnly` — está correto? O `CampaignOnly`
      é mais restritivo, então se ambos estiverem ligados, `CampaignOnly` é o que filtra de fato.
- [ ] O teste `RetornoDeLigacao` agora inicializa `dnc` — mas `callbackBlockedReason` também
      acessa `contactExtras` e `chatControl` (nil-guarded; ok) e `savedInAgenda` (que checa
      `s.client`, nil; ok). Confirmar que não há outro campo sem nil-guard.

### 2. Retorno herda perfil da campanha — commit 6086379

**O que é:** quando alguém da campanha liga de volta e ninguém atende, o retorno automático
(`maybeCallback`) agora herda o `ProfileID` e `AgentPrompt` da campanha que discou para esse
número. Antes usava o prompt genérico fixo (`defaultCallConversationPrompt`).

**Arquivos alterados:**
- `internal/whatsapp_campaigns/store.go`: nova query `RecentCampaignRequest` — busca o JSON
  `request` da campanha mais recente
- `cmd/server/session.go` (~linha 453): extrai `profile_id` do request, resolve com
  `buildAgentSystemPrompt`, passa no `broadcastRequest`

**Pontos para conferir:**
- [ ] O `RecentCampaignRequest` engole o erro do banco (`_ = s.db.QueryRowContext`). Se o
      banco falhar, retorna nil e cai no prompt genérico — comportamento aceitável?
- [ ] A query é igual à de `InRecentCampaignAny` (mesma performance, mesma lógica de filtro).
- [ ] O `buildAgentSystemPrompt` é chamado dentro da goroutine do retorno, usando
      `srv.sessions.appCtx` — ok porque o server está vivo nesse ponto.
- [ ] O `phoneCandidates(phone, types.JID{})` gera candidatos sem JID — confirmar que funciona
      (JID vazio é tratado como sem JID, só telefone).

### 3. Re-engajamento após silêncio — commit 6086379

**O que é:** se o cliente fica 8s em silêncio após a IA falar (na conversa, não durante os
áudios pré-gravados), a IA diz "Olá? Está me ouvindo?" uma vez por ligação. Reseta o timer
de inatividade para dar mais 60s.

**Arquivo alterado:**
- `cmd/server/broadcast.go` (`runConversation`, ~linha 1828)

**Pontos para conferir:**
- [ ] `SayLater` usa `playback` que NÃO chama `touch()`. O `ResetIdle()` manual que eu adicionei
      reseta o timer. Mas se o `SayLater` demora mais que 8s para sintetizar+tocar (TTS lento),
      o timer pode ter subido novamente? Verificar se `ResetIdle` é chamado no momento certo
      (antes do SayLater, que é assíncrono).
- [ ] `reEngaged = true` faz o re-engajamento disparar APENAS UMA VEZ por ligação, mesmo
      que o cliente fique em silêncio de novo. Isso é intencional (não ficar repetindo "olá?"),
      mas talvez 2 tentativas seria melhor.
- [ ] O delay de 8s é hardcoded. Considere tornar configurável via env.
- [ ] A frase "Olá? Está me ouvindo?" é fixa. O ideal seria pedir à IA para gerar uma frase
      contextual (usando o histórico da conversa). Isso requer `QueueTextTurn` com um sistema
      de "proactive nudge" que não existe hoje.

---

## O que NÃO foi feito (pendente)

### A. Publicação v0.12.0 — FEITA em 14/10 ~15:50

- Publicada como build `20261014-1549_743285d` (main em 743285d).
- `campaign_only` ligado às ~16:05 pela API (`PUT /api/settings/agent-chat`, header `X-API-Key`).
  **Cuidado ao conferir:** esse PUT não preserva `enabled` nem `welcome_msg` quando eles não vêm
  no corpo. Mandar só `{"campaign_only": true}` desligou o atendimento por texto; foi religado
  na hora com `enabled` e `welcome_msg` no corpo. A boa-vinda gravada antes estava com acento
  quebrado (`OlÃ¡`); a regravada está certa (`Olá`).
- **Volta (rollback):** no PC, em `D:\hermes\pc-base`, `bash ops/reverter.sh` sem argumento.
  Vai para a v0.11.0 (`20261014-1024_a2683c0`). NÃO usar `voltar-estavel.sh`: a estável marcada
  é `20260925-0158_29e4e85` (25/09) e perderia a v0.11.0.
- `marcar-estavel.sh` ainda não foi rodado (roda do PC, não da VPS; as versões ficam em
  `/opt/hermes-call/releases`). Depende do OK da dona.

### B. Corrigir fallback "Teste E" (operação de dados)

As ligações da campanha mostram `fallback=llama3-8b-8192` do perfil "Teste E" descontinuado.
O perfil tem `extras.fallbackProvider=groq` e `extras.fallbackModel=llama3-8b-8192`. Esse
modelo foi removido do Groq.

Correção: na produção, listar perfis do dono e apagar/corrigir o "Teste E":
```
GET /api/agent-profiles
DELETE /api/agent-profiles/{id-do-teste-e}
```
Ou editar o extras para apontar para um modelo válido.

### C. Abertura nova das imobiliárias (áudio da isca)

5 de 7 desligaram nos 5 primeiros segundos. A isca diz "Daynovari" em vez de "Inovári".
Mudar o texto NÃO regenera o áudio (é pré-gravado e cacheado). Procedimento:
1. Gerar novo áudio via API ou painel
2. Atualizar `campaigns.audio_ref` para o novo ID
3. Reiniciar o serviço para limpar o cache (`basePCM`)

### D. Testes na VPS (container Postgres)

O container `hermes-test-pg` na staging (porta 55432) pode estar parado. Para rodar os testes:
```bash
ssh hermes-staging 'docker start hermes-test-pg'
ssh -L 55432:localhost:55432 hermes-staging  # túnel
HERMES_TEST_DB="postgres://postgres:testpass@localhost:55432/hermestest?sslmode=disable" \
  go test -tags mlow -run 'TestDB_SoCampanha' ./cmd/server/ -v
```

### E. Limpeza

- Container `hermes-test-pg` na staging: `docker rm -f hermes-test-pg`
- `v0.11.0` nunca foi marcada como estável: `bash ops/marcar-estavel.sh`

---

## Estado da campanha (última verificação ~14:37 de 14/10)

- 27 ligações feitas, 8 atendidas
- Campanha ativa, cadenciador rodando
- WhatsApp texto: configurado para responder pessoas da campanha (perfil "Vendas Hermes Call - WhatsApp", mode "private", outbound_only=true)
- campaign_only: **ATIVO** desde ~16:05 (v0.12.0 no ar). Fim do dia 1: 47 discadas, 13 atendidas.
- Perfil "Teste E" apagado às ~16:28 com OK da dona (item B resolvido).

---

## Diagrama: fluxo do retorno com perfil da campanha

```
Ligação recebida → ninguém atende → maybeCallback
  ↓
callbackBlockedReason (access list, dnc, campaign_only, etc.)
  ↓ passa
RecentCampaignRequest(userID, candidatos)  ← NOVO
  ↓ request JSON
Extrai profile_id → agentProfiles.Get → buildAgentSystemPrompt
  ↓ profileID + agentPrompt
broadcastRequest{ProfileID, AgentPrompt, ...}
  ↓
runCampaign → runConversation (usa o perfil da campanha)
```
