# API dos módulos novos (integração Inovare)

Contrato dos endpoints de backend que o painel (frontend) consome. Tudo sob `/api/*`
exige autenticação (Bearer JWT do login OU `X-API-Key: hk_...`). Escopo por dono
(cada tenant só vê o próprio dado). Respostas são JSON. Erros vêm como
`{ "error": "mensagem" }` com status 4xx/5xx.

Status: **Fase 1 (RAG) e Fase 2 (Follow-up) prontas no backend.** Agenda, Vitrine e
Superchat/Painel virão nas próximas fases.

---

## Fase 1 — RAG + Chat de teste (dentro dos Agentes Especializados)

Base de conhecimento por agente (`agent_id` = id do agente especializado, tabela
`agent_profiles`). RAG só é consultado para agentes de TEXTO (kind != "call").

| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| POST | `/api/rag/documents?agent_id=` | multipart campo `file` (txt/md/csv/json) **ou** JSON `{name,text}` | `{id, chunks}` |
| GET | `/api/rag/documents?agent_id=` | — | `{documents:[{id,agent_id,name,source,chunks,created_at}]}` |
| DELETE | `/api/rag/documents/{id}` | — | `{ok:true}` |
| POST | `/api/rag/search` | `{agent_id, query, top_k?}` | `{chunks:[{id,document_id,content,score}]}` |
| POST | `/api/rag/ingest-conversations` | `{agent_id, limit?}` | `{id, chunks}` — indexa transcrições de ligação como conhecimento |
| POST | `/api/agents/{id}/test` | `{message, history?:[{role,content}]}` | `{reply, used_rag}` — conversa de teste, não afeta produção |

Observações:
- Upload limitado a 8 MB. PDF ainda não suportado (só texto puro por enquanto).
- `used_rag=true` indica que a resposta usou a base de conhecimento.
- Requer chave OpenAI cadastrada em Credenciais (provider `openai`) para gerar embeddings.

---

## Fase 2 — Follow-up (cadenciador de mensagens)

Campanhas com etapas (mensagem + atraso em minutos). Contatos entram, o scheduler
(1 min) envia a etapa atual pela sessão WhatsApp pareada e avança. Respeita blacklist.

### Campanhas
| Método | Rota | Body | Resposta |
|---|---|---|---|
| GET | `/api/followup/campaigns` | — | `{campaigns:[{id,name,description,is_active,is_archived,steps,contacts,created_at}]}` |
| POST | `/api/followup/campaigns` | `{name, description?}` | `{id}` |
| PUT | `/api/followup/campaigns/{id}` | `{name,description,is_active,is_archived}` | `{ok:true}` |
| DELETE | `/api/followup/campaigns/{id}` | — | `{ok:true}` |

### Etapas (steps)
| Método | Rota | Body | Resposta |
|---|---|---|---|
| GET | `/api/followup/campaigns/{id}/steps` | — | `{steps:[{id,campaign_id,order,delay_minutes,message_text,created_at}]}` |
| POST | `/api/followup/campaigns/{id}/steps` | `{order, delay_minutes, message_text}` | `{id}` |
| DELETE | `/api/followup/steps/{id}` | — | `{ok:true}` |

### Contatos
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| GET | `/api/followup/contacts?campaign_id=&status=` | — | `{contacts:[{id,name,phone_number,campaign_id,current_step,status,source,last_contact_at,next_execution,profile_data,created_at}]}` |
| POST | `/api/followup/contacts` | `{campaign_id, phone, name?, source?}` | `{id}` ou `{blocked:true}` se na blacklist |
| DELETE | `/api/followup/contacts/{id}` | — | `{ok:true}` |
| PUT | `/api/followup/contacts/{id}/status` | `{status}` (active/paused/completed/failed/blocked) | `{ok:true}` |
| PUT | `/api/followup/contacts/{id}/profile` | corpo = JSON livre (perfil/pagamento) salvo em `profile_data` | `{ok:true}` |

### Tags
| Método | Rota | Body | Resposta |
|---|---|---|---|
| GET | `/api/followup/tags` | — | `{tags:[{id,name,color}]}` |
| POST | `/api/followup/tags` | `{name, color?}` | `{id}` |
| DELETE | `/api/followup/tags/{id}` | — | `{ok:true}` |

### Blacklist
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| GET | `/api/followup/blacklist` | — | `{blacklist:[{phone_number,reason,created_at}]}` |
| POST | `/api/followup/blacklist` | `{phone, reason?}` | `{ok:true}` |
| DELETE | `/api/followup/blacklist?phone=` | — | `{ok:true}` |

### Logs e webhook
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| GET | `/api/followup/logs?limit=` | — | `{logs:[{contact_id,campaign_id,step_order,message_text,status,error_msg,sent_at}]}` |
| POST | `/api/followup/webhook` | `{campaign_id, phone, name?}` | `{id}` ou `{blocked:true}` — entrada externa (n8n/site) |

Observações:
- `status` do contato: `active` (na cadência), `paused`, `completed`, `failed`, `blocked`.
- O envio real só ocorre se houver uma sessão WhatsApp pareada; sem sessão, o tick
  deixa pra próxima volta (não marca falha).

---

## Fase 3 — Agenda (compromissos, lembretes, cobrança)

Compromissos que os agentes marcam (source="agent") ou o dono no painel. Cron de 15 min
envia lembretes (24h e 1h antes) pela sessão WhatsApp. Datas em ISO 8601.

### Compromissos
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| GET | `/api/agenda/appointments?from=&to=&status=` | — | `{appointments:[{id,name,whatsapp,start_at,end_at,status,service,professional_id,source,agent_id,payment_status,payment_amount,notes,...}]}` |
| POST | `/api/agenda/appointments` | `{name, start_at(ISO), whatsapp?, end_at?, service?, professional_id?, agent_id?, source?, payment_amount?, notes?}` | `{id}` ou 409 se horário ocupado |
| PUT | `/api/agenda/appointments/{id}` | `{name,whatsapp,start_at,end_at,service,professional_id,notes}` | `{ok:true}` |
| DELETE | `/api/agenda/appointments/{id}` | — | `{ok:true}` |
| PUT | `/api/agenda/appointments/{id}/status` | `{status}` (confirmado/pendente/cancelado/concluido/aguardando_pagamento) | `{ok:true}` |

### Profissionais / Bloqueios / Lista de espera
| Método | Rota | Body | Resposta |
|---|---|---|---|
| GET/POST | `/api/agenda/professionals` | POST `{name, services?, commission_pct?}` | `{professionals:[...]}` / `{id}` |
| DELETE | `/api/agenda/professionals/{id}` | — | `{ok:true}` |
| GET/POST | `/api/agenda/blocks` | POST `{professional_id?, start_at, end_at, reason?}` | `{blocks:[...]}` / `{id}` |
| DELETE | `/api/agenda/blocks/{id}` | — | `{ok:true}` |
| GET/POST | `/api/agenda/waitlist` | POST `{name, whatsapp, service?, desired_at?}` | `{waitlist:[...]}` / `{id}` |
| DELETE | `/api/agenda/waitlist/{id}` | — | `{ok:true}` |

### Config (integrações) e cobrança
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| GET | `/api/agenda/config/{key}` | — | `{key, value}` (value=JSON salvo, ou null) |
| PUT | `/api/agenda/config/{key}` | corpo = JSON válido (ex.: tokens Google Calendar, chaves Asaas) | `{ok:true}` |
| POST | `/api/agenda/asaas-webhook` | `{event, payment:{id}}` — **público** (Asaas chama) | `{ok:true}` — confirma pagamento por asaas_id |

---

## Fase 4 — Catálogo (vitrine: produtos, estoque, imagens, IA)

### Produtos
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| GET | `/api/catalog/products?q=&category=&company=&active=&featured=&sort=&limit=` | sort: name/price/stock/views/recent | `{products:[{id,name,company,description,price,cost,stock,sku,category,tags,active,featured,position,views,payment_link,main_image,margin_pct,created_at}]}` |
| POST | `/api/catalog/products` | `{name, company?, description?, price?, cost?, stock?, sku?, category?, tags?, featured?, payment_link?}` | `{id}` |
| GET | `/api/catalog/products/{id}` | — | produto (incrementa views) |
| PUT | `/api/catalog/products/{id}` | mesmos campos do POST + `active` | `{ok:true}` |
| DELETE | `/api/catalog/products/{id}` | — | `{ok:true}` (soft-delete → lixeira) |
| POST | `/api/catalog/products/{id}/restore` | — | `{ok:true}` |
| PUT | `/api/catalog/products/reorder` | `{ids:[]}` | `{ok:true}` |
| POST | `/api/catalog/products/bulk-price` | `{ids, mode:"pct"|"fixo", value}` | `{ok:true}` |
| GET | `/api/catalog/products/trash` | — | `{products:[...]}` |
| GET | `/api/catalog/products/export` | — | CSV (download) |
| GET | `/api/catalog/categories` | — | `{categories:[{category,count}]}` |

### Estoque
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| GET | `/api/catalog/stock/critical?limit=` | — | `{products:[...]}` (estoque ≤ limite, default 3) |
| GET | `/api/catalog/stock/report` | — | `{items:[{id,name,stock,status}], resumo:{esgotado,critico,baixo,ok}}` |
| GET | `/api/catalog/stock/history/{id}` | — | `{history:[{qty_before,qty_after,delta,note,created_at}]}` |
| POST | `/api/catalog/stock/adjust` | `{product_id, delta, note?}` | `{stock_before, stock_after}` |

### Imagens
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| GET | `/api/catalog/images/{productId}` | — | `{images:[{id,product_id,url,main}]}` |
| POST | `/api/catalog/images` | `{product_id, url, main?}` | `{id}` |
| POST | `/api/catalog/images/upload/{productId}` | multipart campo `image` (jpg/png/webp/gif, ≤5MB) | `{id, url}` (servida em /uploads/) |
| DELETE | `/api/catalog/images/{id}` | — | `{ok:true}` (apaga arquivo do disco) |
| PUT | `/api/catalog/images/{id}/main` | — | `{ok:true}` |

### IA e catálogo público
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| POST | `/api/catalog/ai-description` | `{name, company?}` | `{description}` — gerada pela IA do dono |
| GET | `/api/catalog/public?owner=<user_id>` | **público** | `{products:[...]}` (ativos, estoque>0) |
| POST | `/api/catalog/public/view/{id}?owner=<user_id>` | **público** | `{ok:true}` (conta visualização) |

Observações:
- `tags` é lista de strings. `margin_pct` é calculado (preço−custo)/preço·100.
- Upload de imagem vai pra disco (`HERMES_UPLOADS_DIR`, default `data/uploads`), servido em `/uploads/`.
- Catálogo público não exige auth; o dono é identificado por `?owner=<user_id>`.

---

## Fase 5 — Perfil do negócio + Superchat

### Perfil (painel Inovare) — tela própria
| Método | Rota | Body | Resposta |
|---|---|---|---|
| GET | `/api/profile` | — | `{user_id,store_name,whatsapp,email,logo_url,segment,address,extra,updated_at}` |
| PUT | `/api/profile` | `{store_name,whatsapp,email,logo_url,segment,address,extra?}` (`extra` = objeto JSON livre) | `{ok:true}` |

### Superchat (Chatwoot)
Já integrado nativamente no Hermes (não foi reimplementado). Espelha o WhatsApp como
inbox multicanal e recebe respostas via webhook. Endpoints existentes:
`/api/sessions/{sid}/chatwoot` (GET/POST/DELETE config), `/api/sessions/{sid}/chatwoot/webhook`,
`/api/chatwoot/resolve`, abrir grupo/canal. Nenhuma mudança nesta fase.

### Analytics e Disparo em massa
Já existem no Hermes (mantidos com tela/campos próprios, conforme pedido). Não migram
pros agentes especializados.

---

## Fase 6 — Billing / Assinatura (Asaas) [do suite Inovare]

Assinatura SaaS por tenant, cobrada via Asaas (token da plataforma em `HERMES_ASAAS_API_KEY`).
Planos: `basic` (R$199/mês), `pro` (R$399/mês), `enterprise` (sob consulta). Cupom
`TESTE_GRATIS` libera na hora.

| Método | Rota | Body | Resposta |
|---|---|---|---|
| GET | `/api/billing` | — | `{plan_code,plan_name,plan_value,status,invoice_url,coupon,is_free_trial,has_asaas,member_since}` (consulta status real no Asaas) |
| POST | `/api/billing/subscribe` | `{plan, cpf_cnpj?}` | `{subscription_id, invoice_url, status}` — cria cliente+assinatura, devolve link de pagamento |
| POST | `/api/billing/check` | — | `{status, invoice_url}` — força re-checagem no Asaas (self-heal pós-pagamento) |
| POST | `/api/billing/coupon` | `{coupon}` | `{status, applied}` — TESTE_GRATIS ativa na hora |
| POST | `/api/billing/webhook` | `{event, payment:{subscription,status}}` — **público**, valida header `asaas-access-token` | `{received:true}` |

Status possíveis: `pending`, `active`, `overdue`, `cancelled`.

Config (deploy/.env.deploy, injetado no container):
- `HERMES_ASAAS_API_KEY` — token da plataforma (produção).
- `HERMES_ASAAS_API_URL` — default `https://api.asaas.com/v3`.
- `HERMES_ASAAS_WEBHOOK_TOKEN` — valida o webhook (configure o mesmo no painel Asaas).

---

## Fase 7 — Outras features do suite Inovare

### Projetos / workspaces
| Método | Rota | Body | Resposta |
|---|---|---|---|
| GET | `/api/projects` | — | `{projects:[{id,name,description,tags,priority,created_at}]}` |
| POST | `/api/projects` | `{name, description?, tags?, priority?}` | `{id}` |
| PUT | `/api/projects/{id}` | `{name,description,tags,priority}` | `{ok:true}` |
| DELETE | `/api/projects/{id}` | — | `{ok:true}` |

### Builder de agentes (estende os Agentes Especializados)
Os agentes (`/api/agent-profiles`) ganharam campos do builder: `tone`, `guardrails`,
`knowledge_base`, `escalation_keywords` (além dos já existentes). São aplicados
automaticamente no prompt efetivo (chat de teste e execução).
| Método | Rota | Body | Resposta |
|---|---|---|---|
| POST | `/api/agents/refine` | `{name, role, tone, steps, knowledge, guardrails, automations:[{trigger,action}]}` | `{refined_prompt}` — monta o mega-prompt (lapidado pela IA se configurada) |

(Chat de teste do agente já documentado na Fase 1: `POST /api/agents/{id}/test`.)

### Monitor de chat — pausa manual da IA
Kanban por estágio, notas e tags já existem no Hermes (CRM/contatos). Adicionado o
controle manual de pausa da IA por conversa:
| Método | Rota | Body / Query | Resposta |
|---|---|---|---|
| POST | `/api/chat-control/pause` | `{jid, minutes?}` (minutes=0 → indefinida) | `{ok:true}` |
| POST | `/api/chat-control/resume` | `{jid}` | `{ok:true}` |
| GET | `/api/chat-control/status?jid=` | — | `{paused}` |

Quando pausada, o autoreply não responde aquele contato (o dono assume manualmente).

### Integração n8n (config por tenant)
| Método | Rota | Body | Resposta |
|---|---|---|---|
| GET | `/api/n8n` | — | `{url, token(mascarado), behavior, has_token}` |
| POST | `/api/n8n` | `{url, token, behavior}` (behavior: substitute/augment) | `{ok:true}` |

Token vazio/mascarado no POST preserva o valor salvo.

### Login com Google (OAuth) — "em breve" até ter credenciais
Fluxo OAuth completo no backend. Enquanto `HERMES_GOOGLE_CLIENT_ID/SECRET` não estiverem
preenchidos, os endpoints respondem `503 {error:"coming_soon"}` e o front deve mostrar o
botão "Entrar com Google" **desativado (em breve)**. Ao preencher no `.env.deploy`, liga sozinho.
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/auth/providers` | `{google:{enabled:bool}}` — o front decide se ativa o botão |
| GET | `/api/auth/google` | redireciona pro consentimento do Google (ou 503 coming_soon) |
| GET | `/api/auth/google/callback` | troca o code, faz upsert do usuário, redireciona pro front com `?token=<jwt>` |

Config (deploy/.env.deploy): `HERMES_GOOGLE_CLIENT_ID`, `HERMES_GOOGLE_CLIENT_SECRET`,
`HERMES_GOOGLE_REDIRECT_URL` (…/api/auth/google/callback), `HERMES_OAUTH_SUCCESS_URL`.

### Já existentes no Hermes (não reimplementados)
- **Superchat (Chatwoot)**: inbox multicanal nativo (`/api/sessions/{sid}/chatwoot*`).
- **WhatsApp / instâncias**: pareamento e sessões já são o núcleo do Hermes.
- **Analytics, disparo em massa (mass-call/mass-message)**: telas próprias já existentes.
- **BYOK (chaves de IA por provider)**: via Credenciais (`/api/credentials`).
