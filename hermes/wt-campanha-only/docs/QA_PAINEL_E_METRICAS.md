# QA do Painel — Teste de cada aba/botão + Auditoria de Métricas

> ## ⚠️ DOCUMENTO DE JULHO — conferido no código em 06/10/2026: **não é lista de pendência**
>
> Tudo o que a Parte 3 pede já foi feito. Conferido no ramo `pc/v0.8.0`:
> - Ligações Hoje / Duração média / Taxa de atendimento: reais (`cmd/server/dashboard.go`, não é mais zero fixo);
> - Sentimento, gráficos pequenos, volume por hora e a lista "ao vivo" do Dashboard: vêm do servidor
>   (`client/src/pages/DashboardPage.tsx`); o "85%" fixo e os eventos inventados saíram;
> - mapa de calor falso do Analytics, "Lead Score" e "Mock Activity" do CRM: removidos;
> - régua de follow-up: é disparada (`cmd/server/followup_cron.go`);
> - abas sem função (Telefonia, Google Calendar): aparecem com a etiqueta "Em breve", sem fingir que funcionam.
>
> As séries "sempre 0" dos analytics continuam assim de propósito (o banco não guarda o dado).
> Estado de verdade de cada bug: `docs/PENDENCIAS_BUGS.md`. O roteiro de teste da Parte 2 ainda serve.

Documento de verificação do painel Hermes Call. Duas partes:
1. **Auditoria de métricas** — o que é dado REAL vs SIMULADO/hardcoded (com arquivo:linha).
2. **Roteiro de QA** — cada aba e sub-aba, o que clicar, e o resultado esperado.

Ambiente: https://hermescall.opus-sem-limites.com.br (channel=beta). Login admin@hermescall.com.

---

## PARTE 1 — AUDITORIA DE MÉTRICAS (real vs simulado)

### Dashboard / Visão Geral (`client/src/pages/DashboardPage.tsx`)

| Métrica | Estado | Origem / Motivo |
|---|---|---|
| Sessões total/pareadas | ✅ REAL | `/api/dashboard` → conta sessões whatsmeow |
| **Em Ligação (agora)** | ✅ REAL | `data.calls.active` — conta chamadas ativas no broker |
| **Ligações Hoje** | ❌ STUB | backend `dashboard.go:26`: `callsToday := 0 // not implemented`. Sempre 0 mesmo ligando. |
| **Duração média** | ❌ STUB | `dashboard.go:26`: `avgDuration := 0`. Sempre 0s. |
| **Taxa de Atendimento (%)** | ❌ STUB | `dashboard.go:26`: `answerRate := 0.0`. Sempre 0%. |
| Ligações (Histórico) | ⚠️ PARCIAL | usa `/api/transcripts` (real) MAS com fallback fake `Math.max(today*12,3)` quando vazio (`DashboardPage.tsx:128`) |
| Sentimento Positivo (85%) | ❌ HARDCODED | valor fixo `"85%"` no JSX (`DashboardPage.tsx:198`) |
| Economia / ROI / Tempo economizado / Atendentes | ⚠️ DERIVADO | cálculo a partir de `baseCalls` com constantes fixas (`DashboardPage.tsx:127-131`). Não é medição real. |
| Todas as sparklines dos cards | ❌ HARDCODED | arrays fixos `chartData={[...]}` em cada StatCard |
| Gráfico "Volume de Ligações (Hoje)" | ❌ DERIVADO | pontos calculados de `baseCalls * 0.1..1.0` (`DashboardPage.tsx:256-262`) — não é volume por hora real |
| Funil "Jornada do Lead" | ⚠️ VERIFICAR | usa `funil.*` — checar se vem de dados reais ou objeto fixo |
| Live Activity Feed | ❌ HARDCODED | eventos fake (números/horários inventados) |

**Raiz das 3 métricas 0 que você viu:** [dashboard.go:26](../cmd/server/dashboard.go#L26) devolve `0, 0, 0.0` fixo. Precisa calcular de `call_transcripts` (tem `created_at`, `interested`) e/ou do broker history.

### Analytics (`client/src/pages/AnalyticsPage.tsx`)
| Item | Estado |
|---|---|
| Conversão / Ligações / Semanal | ✅ REAL (`/api/analytics/conversion`, `/calls`, `/weekly`) |
| "Mapa de Calor: Horários de Pico" | ❌ HARDCODED (`AnalyticsPage.tsx:236`, comentário admite mock) |

### Analytics por aba (endpoints NOVOS que criei — `panel_analytics.go`)
| Endpoint | Estado | Observação |
|---|---|---|
| `/api/analytics/crm` (funil, win/loss) | ✅ REAL | agrega `contact_leads`; win = stage 'Fechado'; **"Perdas" sempre 0** (schema não tem stage de perda) |
| `/api/analytics/agenda` | ⚠️ PARCIAL | agendados/cancelados e pico REAIS; **"no-show" na verdade é "cancelado"** (schema não tem no-show) |
| `/api/analytics/catalog` | ⚠️ PARCIAL | criações/exclusões/stock REAIS; **"edições" sempre 0** (não há timestamp de edição) |
| `/api/analytics/followup` | ⚠️ PARCIAL | envios e engagement REAIS; **"respostas" sempre 0** (log é só de saída) |
| `/api/analytics/tags` | ⚠️ PARCIAL | distribuição REAL; **"aplicadas/manuais por dia" sempre 0** (sem timestamp de aplicação) |
| `/api/analytics/blocks` | ✅ REAL | bloqueios por dia via `fu_blacklist.created_at` |

> As séries "sempre 0" acima NÃO são bug — o banco não guarda esse dado. Decisão consciente de retornar zero em vez de inventar. Pra ter esses números seria preciso passar a gravar (ex.: timestamp na aplicação de tag, flag de resposta no follow-up).

---

## PARTE 2 — ROTEIRO DE QA (cada aba, cada botão, resultado esperado)

Marque ✅/❌ em cada linha ao testar no navegador.

### Conexão de Linha / QR
- [ ] Botão "+" / conectar → abre QR real. **Esperado:** QR aparece, escaneou → linha pareada, some da tela.
- [ ] Linha aparece na lista com status "conectado". **Esperado:** nome + número reais.
- [ ] Logout da linha. **Esperado:** sessão sai da lista.

### Funcionários IA
- [ ] Listar agentes. **Esperado:** mostra "Vendas Hermes Call" (e os que você criar). Fonte: `/api/agent-profiles`.
- [ ] Criar agente novo (nome, prompt, voz). **Esperado:** salva e aparece na lista imediatamente.
- [ ] Editar agente existente e salvar. **Esperado:** mudanças persistem; **NÃO** cria duplicata; **NÃO** apaga voz/contexto (bug corrigido nesta leva).
- [ ] Renomear agente. **Esperado:** nome muda no mesmo card (não cria um segundo). ⚠️ testar — era bug, foi corrigido.
- [ ] Chat de teste do agente (digitar mensagem). **Esperado:** agente responde via LLM real. Requer credencial LLM configurada.
- [ ] Sub-aba **Advanced Lab**: selecionar agente → carrega campos. Salvar. **Esperado:** persiste sem zerar campos de Funcionários IA.
- [ ] Advanced Lab sem agente selecionado + enviar no chat. **Esperado:** aviso "Selecione ou grave um agente" (não 404).
- [ ] Advanced Lab: dropdown de instância WhatsApp. **Esperado:** lista as linhas pareadas (`/api/whatsapp/instances`).
- [ ] **Treinador** (sub-aba, front do outro agente): iniciar treino. **Esperado:** cria job, mostra progresso, gera prompt. Backend pronto (`/api/training/*`).

### CRM / Gestão de Leads
- [ ] Ver board (kanban) com etapas. **Esperado:** colunas reais (`/api/crm/board`).
- [ ] Criar etapa. **Esperado:** nova coluna aparece.
- [ ] Renomear/excluir etapa. **Esperado:** reflete no board.
- [ ] Arrastar lead entre etapas. **Esperado:** persiste (recarregar mantém).
- [ ] Sub-aba **Analytics CRM**. **Esperado:** funil com números reais; "Perdas" fica 0 (limitação de schema — documentar pro usuário).
- [ ] "Lead Score" (bolinhas). ⚠️ **Cosmético/mock** — não é score real.
- [ ] Timeline "Mock Activity". ⚠️ **Hardcoded** — não é atividade real.

### Agenda
- [ ] Listar compromissos. **Esperado:** `/api/agenda/appointments` reais.
- [ ] Criar compromisso. **Esperado:** aparece na lista.
- [ ] Mudar status / excluir. **Esperado:** persiste.
- [ ] Sub-aba **Configurações → Dias bloqueados**. **Esperado (corrigido):** marca dia da semana e salva; recarregar mantém. Datas específicas idem.
- [ ] "Conectar Google Calendar". ⚠️ só toast "em breve" — não conecta de verdade.
- [ ] Sub-aba **Analytics Agenda**. **Esperado:** agendados/cancelados/pico reais; "no-show" = cancelados (limitação).

### Vitrine / Catálogo
- [ ] Listar produtos. **Esperado:** `/api/catalog/products` reais.
- [ ] Criar/editar/excluir produto. **Esperado:** persiste.
- [ ] Sub-aba **Analytics Catálogo**. **Esperado:** criações/stock reais; "edições" fica 0 (limitação).

### Central de Telefonia
- [ ] Aba **Ligações**. **Esperado:** lista chamadas reais (`/api/sessions/{sid}/calls`).
- [ ] Aba **Transcrições**. **Esperado:** transcrições reais (`/api/transcripts`).
- [ ] Aba **Gravações**. **Esperado:** `/api/recordings`.
- [ ] Abas **"Em Andamento"** e **"Instâncias SIP"**. ⚠️ **placeholders vazios** — sem dados.

### Disparo em Massa (Mass Message / Mass Call)
- [ ] Selecionar contatos + escrever mensagem + iniciar. **Esperado:** job criado, progresso atualiza (polling 3s — SSE quebrado foi removido).
- [ ] Cancelar job. **Esperado:** para.

### Follow-Up
- [ ] Criar régua (tag + horas + mensagem). **Esperado (corrigido):** salva via `/api/followup/rules`, aparece na lista.
- [ ] Excluir régua. **Esperado:** some da lista.
- [ ] Sub-aba **Analytics Follow-Up**. **Esperado:** envios/engagement reais; "respostas" fica 0 (limitação).
- [ ] ⚠️ **Atenção:** régua não é DISPARADA automaticamente ainda — só cadastrada. O disparo por tag+inatividade precisaria de um cron (não implementado).

### Configurações
- [ ] **Perfil da Empresa** → editar e salvar. **Esperado (corrigido):** persiste em `/api/profile`; recarregar mantém.
- [ ] **n8n** → salvar URL/token. **Esperado (corrigido):** persiste; token volta mascarado.
- [ ] **Workspaces/Projetos** → criar/excluir. **Esperado (corrigido):** persiste em `/api/projects`.
- [ ] **IA / Credenciais** → salvar chave LLM. **Esperado:** salva e fica disponível pros agentes (fonte única de credencial).
- [ ] **Voz / STT** → configurar. **Esperado:** persiste.
- [ ] **Segurança / 2FA / Sessões** → ativar 2FA, revogar sessão. **Esperado:** real.
- [ ] **Custos / Orçamento** → definir teto. **Esperado:** persiste; bloqueia IA ao estourar (se hard limit).

### Chat Gestor
- [ ] Enviar mensagem ao gestor IA. **Esperado:** responde via `/api/chat/*` (real).

---

## PARTE 3 — PENDÊNCIAS PRIORIZADAS (o que fazer pra métricas ficarem reais)

1. **[ALTA] Dashboard: Ligações Hoje / Duração média / Taxa de Atendimento** — implementar em `dashboard.go` a partir de `call_transcripts` (count de hoje, taxa por `interested`/status) e do broker history (duração). Hoje é `0` fixo.
2. **[MÉDIA] Dashboard: Sentimento, sparklines, Volume por hora, Live Feed** — hardcoded; ligar a dados reais ou remover/rotular como estimativa.
3. **[MÉDIA] Follow-up réguas** — cron que efetivamente dispara a régua (hoje só cadastra).
4. **[BAIXA] Séries "sempre 0" dos analytics** — exigem passar a gravar o dado (timestamp de aplicação de tag, flag de resposta, no-show na agenda, timestamp de edição de produto).
5. **[BAIXA] Central de Telefonia: abas "Em Andamento"/"Instâncias SIP"** — placeholders.
6. **[BAIXA] Google Calendar / Lead Score / Mock Activity** — recursos anunciados na UI mas não implementados.
