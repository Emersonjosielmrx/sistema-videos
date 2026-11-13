# 06 — CRM: nomes do WhatsApp nos cards + ações de etapa (lista/campanha)

Backend PRONTO e no ar (2026-07-21). Este doc é o contrato pro agente de FRONTEND ligar.

## 1. Nome do perfil WhatsApp no card (backend feito)
`GET /api/crm/board` agora inclui `name` em cada lead quando conhecido.
- Vem do cache `wa_contact_names`. Quem ainda não tem nome cacheado é resolvido em
  BACKGROUND (via sessão WhatsApp) e salvo — no 2º load o nome aparece. "Resolve uma vez
  e reusa", como pedido.
- **Front:** no card, usar `lead.name` quando existir; senão cair pro telefone (não "Lead"
  fixo). Formato do lead: `{jid, phone, name?, score, notes, updated_at}`.
- Observação: a 1ª abertura pode vir sem alguns nomes (resolvendo em background). Recarregar
  mostra os resolvidos. Não precisa polling — só reabrir.

## 2. Ações em massa sobre uma etapa (backend feito)
`POST /api/crm/stage-action` — pega TODOS os telefones da etapa e faz uma de 3 ações.
> O nome da etapa vai no BODY (não na URL) porque tem "/" e espaço (ex.: "Não completou / Erro").

**Request:**
```json
{ "stage": "Não completou / Erro", "action": "new_list", "list_name": "Re-ligar erros" }
{ "stage": "Não atendeu 1x",       "action": "append_list", "list_id": "<id>" }
{ "stage": "Conversou",            "action": "campaign", "session_id": "<opcional>" }
```
**Responses:**
- `new_list`   → `{ok:true, count, list_id}`
- `append_list`→ `{ok:true, count, list_id}`
- `campaign`   → `{ok:true, count, campaign_id}`

**Comportamento do `campaign`:** cria a campanha persistida com os números **enfileirados
(queued)**, modo `paced`, e devolve `campaign_id`. **NÃO dispara sozinha** — a dona ajusta
áudio/modo (agora/paced/multilinha, incl. 2 áudios) e dispara na tela de Campanhas, que já
tem o motor completo. Discar mudo daqui seria ruim.

**Front (sugestão de UX):** no header de cada coluna do Kanban (perto da lixeira), um menu
"⋯" com: "Criar lista", "Adicionar a lista…" (mostra as listas via `GET /api/contact-lists`),
"Virar campanha". Após `campaign`, redirecionar pra `/campanhas` com o `campaign_id`.

## 3. Preferências de layout do CRM (backend feito — doc 03/easy-wins)
`GET/PUT /api/users/me/preferences` (JSON livre; GET vazio devolve `{}`). O front deve
persistir `focusMode`/`compactMode`/`collapsedStages`/`funnelView` aqui (hoje são `useState`
local e somem ao recarregar). Ver CRMPage.tsx.

## 4. FRONTEND PURO (não é backend — pro agente de front fazer)
- **Barra de rolagem horizontal no TOPO do Kanban** (além da de baixo), pra facilitar. É CSS/
  JS no container das colunas (sincronizar scroll de uma barra-espelho no topo). Nenhum backend.
- **Botão "Lista" bugado** (CRMPage.tsx:121): hoje faz `setFunnelView("list")` + `setActiveTab("contacts")`
  ao mesmo tempo, e `list` cai no mesmo componente do "Dividido". Construir a TABELA real
  (estilo Excel) e parar de redirecionar pra Contatos.
- **Minimapa do funil** (item 6 do pedido antigo): não existe. Frontend puro.

## Verificação
- Board: card mostra nome do WhatsApp (reabrir se resolveu em background).
- `curl POST /api/crm/stage-action {stage,action:"new_list",list_name}` → lista criada com N contatos.
- `action:"campaign"` → aparece campanha nova (queued) na tela de Campanhas.
