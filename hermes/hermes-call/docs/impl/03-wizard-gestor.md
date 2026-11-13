# 03 — Wizard "Gestor Fácil" (EasyManagerWizard)

**Esforço:** médio. **Impacto:** alto (o front tem um wizard de 588 linhas que NÃO salva nada).
**Verificado no código:**
- `client/src/components/settings/EasyManagerWizard.tsx` existe (588 linhas) mas **`handleSave`
  só faz `toast.success`** (linha ~63-65) — nenhum `apiPost`. Todo o estado é local e some ao recarregar.
- `/api/easy-wizard*` → **0 rotas** no backend.
- **PORÉM já existe `PUT/GET /api/settings/manager`** (usado por ManagerAgentSettings) e o
  agente gestor já roda (tools de sistema, `srv.tgBots[userID]`). Ou seja: o "cérebro" do gestor
  existe; falta **persistir a config rica do wizard** e o front chamar.

## Decisão de design
NÃO criar tabela `manager_profiles` nova do zero. O gestor já vive como **settings do tenant**
(`internal/settings/store.go`, tabela `settings`, com blocos JSON por área). Estender esse
modelo é mais barato e não duplica. Adicionar um bloco `manager` (JSON) no settings.

## Campos que o wizard coleta (do estado real do componente)
```
Identidade/Motor: enabled, name, systemPrompt, cognitiveIndependence, managerApiKey,
                  provider, fallbackProvider, treeViewMode
Comunicação:      whatsappMode(private|group), welcomeMessage, notifyTelegram, selfChat,
                  audioCondition(never|text_and_audio|always_audio), chunkMessages
Ferramentas:      tools[], openclawEnabled, openclawUrl, openclawKey
Superpoderes:     haltOverride, billingAlerts, scheduledReports, promisesAccountability,
                  criticalAlerts, handoffAlerts, shadowingMode
Deep Tech:        memoryClustering, swarmCollaboration
Agent OS:         osControl, perpetualMemory, taskDelegation, deepResearch
```

## Passo 1 — Backend: bloco `manager` no settings
- Em `internal/settings/store.go`, adicionar um struct `ManagerConfig` (todos os campos acima)
  e incluí-lo no struct de settings do tenant (JSON, aditivo — sem migration de coluna nova
  se o settings já é um JSON grande; senão `ADD COLUMN IF NOT EXISTS manager JSONB DEFAULT '{}'`).
- Endpoints: **reusar `GET/PUT /api/settings/manager`** se o shape couber; se o shape atual for
  menor, ESTENDER o handler pra aceitar os campos novos (não quebrar o que ManagerAgentSettings
  já manda). Handler provável em `settingsapi.go` ou `features_api.go` — `grep "settings/manager" cmd/server/httpapi.go`.
- **Segredos:** `managerApiKey`/`openclawKey` — NÃO retornar no GET (mascarar), preservar no PUT
  se vier vazio (mesmo padrão de credenciais/n8n já usado no projeto).

## Passo 2 — Aplicar a config no motor do gestor
- O gestor já existe (AIAgent modo manager). Ao rodar, ler o bloco `manager` do settings:
  - `systemPrompt` → prompt base do gestor.
  - `tools[]` → habilitar/desabilitar as tools (o AIAgent já tem tools; filtrar pelas ligadas).
  - `provider/fallbackProvider/managerApiKey/cognitiveIndependence` → escolha de modelo e se
    ignora o budget global.
  - `audioCondition/chunkMessages/whatsappMode/welcomeMessage/selfChat/notifyTelegram` →
    comportamento de resposta (vários já existem em autoreply/manager settings — reusar).
  - Flags de superpoder (billingAlerts, criticalAlerts, handoffAlerts, promisesAccountability,
    scheduledReports) → gatilhos de notificação. `promisesAccountability` liga o doc 02.
  - Flags Deep Tech / Agent OS (osControl, deepResearch, swarmCollaboration, taskDelegation,
    memoryClustering, perpetualMemory, shadowingMode) → **muitas são features futuras**; por ora
    PERSISTIR o valor (pra não perder a escolha) e ligar só as que já têm motor. Marcar no UI as
    que ainda são "em breve" em vez de fingir que funcionam.

## Passo 3 — Frontend: ligar o wizard
- `EasyManagerWizard.tsx` `handleSave` → `await apiPut("/api/settings/manager", state)` (mapear
  nomes se o backend usar snake_case). Carregar o estado inicial do `GET` ao abrir.
- **Honestidade:** os toggles Deep Tech/OS que o backend ainda não executa devem aparecer como
  "em breve" (desabilitados) — não como ligados-mas-sem-efeito.

## Verificação
- Preencher o wizard, salvar, recarregar a página → os valores voltam do backend.
- Mudar `systemPrompt` e `tools` → conversar com o gestor no Telegram e confirmar que ele segue
  o prompt novo e só usa as tools ligadas.
- Confirmar que `managerApiKey` não vaza no GET (vem mascarado).

## Trade-offs
- Reusar settings/manager evita tabela nova, mas o handler precisa aceitar mais campos sem
  quebrar o ManagerAgentSettings antigo — testar os dois consumidores.
- Não prometer no UI o que o motor ainda não faz (Deep Tech). Persistir ≠ executar.
