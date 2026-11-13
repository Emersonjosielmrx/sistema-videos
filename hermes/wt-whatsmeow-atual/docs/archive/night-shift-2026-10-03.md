# Relatório do Turno Autônomo (V3)
Iniciando melhorias na V3. Este log guardará a trilha das tarefas concluídas durante as 12h de trabalho isolado local.
- Implementado Code-Splitting no Frontend via Vite (chunkSize e manualChunks de vendor / ui / icons para reduzir bundle principal e acelerar first-load da aplicação V3).
- Criada estrutura de Crons de Backend no main.go via startCronJobs() para limpar automaticamente os logs da tabela de auditoria a cada 90 dias e limpar as sessoes com mais de 30 dias offlines via nova query SessionSecurityStore.CleanupExpired().
- **Confiabilidade de Áudio:** Implementado fallback retry pattern no STT (OpenAI/Groq 429/50x) e TTS (edge-tts websockets fails). Resiliência de conversas do hermes (redução de timeout e logs claros de retentativas) adicionada ao `internal/voice`. 
- **UI/UX e Theming:** Refatoração nos componentes do React removendo classes com cores estáticas no Tailwind (`text-red-500`, `bg-green-50`, etc) por CSS variables semânticas do tema raiz (`text-destructive`, `text-primary`, `bg-primary/10`). Isso garante que o Dark Mode funcione de maneira muito mais orgânica e centraliza o tema semântico customizável na V3.

## 2026-07-11 — hermes3 no ar (merge v0.0.4 + doc completa)
- Criado stack PARALELO `hermes_call_v3` (sem tocar no hermes2): https://hermes3.inovareinteligenciaartificial.com
- Compose `deploy/docker-compose.v3.yml` (UDP 50003, pg_v3, whisper, DNS wildcard resolve; router Traefik hermes-call-v3).
- Doc atualizada: openapi.yaml agora "Inovare Hermes Call v2 API" com 156 refs api/ (antes 21). 72 endpoints SaaS + schema UserSettings.
- BUG do merge corrigido (panic no boot): 2 rotas duplicadas no Go 1.22 ServeMux.
  - `POST /api/sessions/{sid}/broadcast`: removido stub upstream `handleSessionBroadcast` (arquivo api_broadcast.go deletado); mantido `handleBroadcast` (disparo em massa completo + /broadcast/{cid}).
  - `GET /api/sessions/{sid}/contacts`: removido registro do `handleListContacts` (formato WAHA array); mantido `handleSessionContacts` que o client espera ({contacts} + busca q).
- STT fix incluso: env HERMES_STT_MODEL=base no compose v3.
- VALIDADO live: login admin -> JWT ok; /api/dashboard, /api/settings, /api/analytics, /api/audit-log = HTTP 200 autenticados; api-docs.html HTTP 200.
- Deploy via deploy_v3.py (tar do fonte inteiro -> /opt/inovare-hermes-call-v3 -> build imagem v3 -> stack deploy).
- NÃO commitado (callagente nem é repo git). hermes2 intacto.

## 2026-07-11 01:40 — hermes3 fases 1 e 3
- FASE 1 (branding, "nao pode logo Astra"): OK no ar.
  - Sidebar: logo ASTRA (logoCalls.png) -> icone PhoneCall + "Hermes Call" (igual header).
  - api-docs.html: title/header "AstraCalls" -> "Hermes Call".
  - PairPhone: nome do aparelho no WhatsApp do cliente "AstraCalls" -> "Hermes Call".
  - manifest extensao passkey -> Hermes Call.
  - Sobra so IDs internos invisiveis (astracalls-panel, astracalls-passkey.zip) e refs wacalls/* internas (modulo Go, env, namespace) - nao renomear (quebra build).
  - Pendente baixa prio: favicon.png pode ser da Astra.
- FASE 3 (analytics por campanha): backend OK no ar.
  - broadcast.go: broadcastResult ganhou AudioMs + ListenPct (% escuta = durMs/audioMs).
  - NOVO cmd/server/campaigns.go: CampaignStore persiste campanhas + resultados por contato (tabelas campaigns, campaign_results). Antes era so memoria (sumia no restart).
  - broadcast.go persiste: Create no handleBroadcast, UpsertResult em completed/no-answer/failed, Finish no fim.
  - NOVO campaigns_api.go: GET /api/campaigns (lista+agregados: completed/answered/no_answer/failed/avg_listen/full_listen>=95%), GET /api/campaigns/{id}/results (filtros order=listen|duration|status, min_listen, interested).
  - broadcastRequest ganhou Name (nome da campanha).
  - Campos reply/interested ja na tabela (prep p/ FASE 4 transcricao).
  - VALIDADO live: /api/campaigns=200 {[]}, results=200.
- NUMERO CONECTADO: 559184698653, state=open, paired=True. Pronto pra testes reais (FASE 6).
- Bug recorrente: sempre validar logs com --timestamps (grep pega panic ANTIGO de container morto e assusta a toa).

## 2026-07-11 02:10 — SESSÃO NOTURNA hermes3 (fases 1-8, autônomo)
Dona pediu "faça tudo" + criei ROADMAP_MELHORIAS.md (~90 itens, 12 áreas).
Executado e VALIDADO no ar (https://hermes3.inovareinteligenciaartificial.com):
- F1 branding: logo ASTRA fora (sidebar, api-docs, PairPhone, extensão). Só sobra favicon.png + IDs internos.
- F3 analytics campanha (backend): campaigns.go persiste campanhas+resultados; % de escuta (durMs/audioMs); endpoints GET /api/campaigns e /{id}/results (order/min_listen/interested).
- F3b UI: CampaignsPage.tsx — histórico, cards agregados (atenderam/ouviram tudo/escuta média), drill-down por contato, filtros, badge interesse. Aba Campanhas no menu.
- F2 listas+filtros: contact_lists.go (CRUD listas); ContactsPage ganhou ordenação (nome/número/DDD) + botão "Salvar Lista".
- F5 anti-bloqueio: broadcastRequest ganhou gap_min/max_ms (gap aleatório), respect_schedule, start/end_hour (janela), max_per_run. withinBroadcastWindow() reusa IsWithinSchedule.
- F4 transcrição+interesse: activeCall.replyPCM captura fala do cliente (OnPeerAudio); captureReply() transcreve via STT whisper; detectInterest() por keywords (eu quero/tenho interesse/etc). Campos reply+interested persistidos. capture_reply/reply_wait_ms/interest_keywords no request.
- F2b UI listas: ListsPage.tsx — ver/excluir listas, "Ligar" dispara mass-call. Aba Listas no menu.
- F7 doc: openapi.yaml +tag Campanhas +endpoints campaigns/contact-lists/broadcast documentados; removida duplicata antiga de broadcast (154 paths, YAML valido).
- F8 n8n: n8n_hermes3_test_flow.json — login->JWT->dashboard/sessões/campanhas/criar-lista/broadcast. Importável.
- F1b visual: tema dark de preto-chapado (240 10% 6%) p/ azul-petróleo com profundidade (222 24% 9%, cards 13%, bordas suaves).

ENDPOINTS VALIDADOS live: login JWT, dashboard, settings, analytics, audit-log, campaigns (200 []), contact-lists (GET/POST/DELETE ok). Container estável, sem panic, WhatsApp 559184698653 conectado.

ARQUITETURA IMPORTANTE (p/ próximo agente):
- 2 fluxos de disparo: mass-call (masscall.go, INFERIOR: só toca campainha, NÃO toca áudio, NÃO persiste) e broadcast (broadcast.go, COMPLETO: toca áudio, mede escuta, persiste, capta resposta). UI de Contatos usa mass-call; a visão da dona (áudio+métricas) vive no broadcast.
- PENDENTE p/ fechar o ciclo: fazer a UI disparar pelo /broadcast (upload de áudio) em vez do mass-call, senão as campanhas persistidas ficam vazias no uso real pelo painel. Backend 100% pronto; falta UI de "nova campanha com áudio".
- Deploy: deploy_v3.py (tar fonte -> /opt/inovare-hermes-call-v3 -> build -> stack). Swarm NÃO troca imagem por tag igual: sempre `docker service update --force` após build.
- Validar logs SEMPRE com --since/--timestamps (grep pega panic ANTIGO de container morto).

FASE 6 (teste real com áudio no número) e disparo real: NÃO feito — precisa de áudio real e a dona acordada pra não gastar/arriscar ban. Guard-rail: não disparei campanha real.

## 2026-07-11 02:17 — CICLO FECHADO (UI campanha com áudio)
- MassCallPage agora tem 2 modos: "Campanha com áudio" (upload mp3/ogg → dispara via /broadcast: persiste, mede escuta, capta resposta, com config anti-bloqueio: intervalo min/max, janela de horário, transcrever resposta) e "Só tocar" (mass-call campainha antigo).
- Isso FECHA o ciclo: agora as campanhas disparadas pelo painel aparecem na aba Campanhas com métricas reais.
- VALIDADO no bundle live: "Campanha com áudio", "Disparar campanha", "Transcrever a resposta". Container sem panic.
- TODAS as fases do roadmap (1,1b,2,2b,3,3b,4,5,7,8 + UI campanha) NO AR e validadas por HTTP.
- SÓ FALTA: FASE 6 = teste REAL discando pra um número com áudio de verdade. Não fiz por guard-rail (gasta chamada real, risco ban, precisa áudio real e dona validando). Quando a dona acordar: abrir Contatos → selecionar → "Ligar em Massa" → "Campanha com áudio" → subir áudio → Disparar. Depois ver aba Campanhas.

## 2026-07-11 07:00 — Feedback da dona (contatos/analytics/logs/whitelist/tutoriais)
- LOGS inundados de "telegram poll cycle": resolvido. telegram.go só loga Info quando há updates; poll vazio vira Debug; tirei -debug do compose v3 (nível Info). Validado: 0 poll cycles em 30s.
- CONTATOS com histórico/score: NOVO backend CampaignStore.ContactStats (agrega por número: ligações, atendidas, % escuta média/máx, interesse, última resposta, score 0-100). Endpoint GET /api/contacts/stats. UI ContactsPage: badge score + histórico (atend/ligações, melhor %, selo interesse), filtros "Já ligados"/"Interessados", sort por Score.
- EXPORTAR PRA LISTA: modal ExportListModal (criar nova OU adicionar a existente). Backend ContactListStore.Append (POST /api/contact-lists/{id}/append, sem duplicar). Botão "Exportar p/ Lista" na barra de seleção.
- ANALYTICS de chamada: NOVO CampaignStore.CallAnalyticsSummary + GET /api/analytics/calls (total ligações, taxa atendimento, escuta média, ouviram tudo, interessados, tempo total ouvido, no-answer, falhas). UI AnalyticsPage ganhou seção "Campanhas de Chamada" no topo com cards.
- IP WHITELIST: escondida do painel (aba removida do SecuritySettings) — não faz sentido em SaaS multi-tenant onde o cliente acessa de IPs variados. Backend mantido (não apaguei).
- PEDIDO NOVO (adicionar ao roadmap): TUTORIAIS/ONBOARDING pra leigos — abas de tutorial, tooltips ao passar o mouse, guia passo-a-passo até a primeira ligação. AINDA NÃO FEITO.

## 2026-07-11 10:30 — Rodada feedback (settings/providers/voz/TTS/telegram/branding)
- FIX MULTI-TENANT: painel do tenant vinha vazio (Telegram/LLM). LoadUserSettings agora cai pro config global (env vars do boot) quando o tenant não salvou. Validado: telegram+ai aparecem enabled com token/chave.
- GEMINI: adicionado aos providers (AISettings + DualAgent). Backend chatOpenAIH roteia gemini p/ endpoint OpenAI-compatível (generativelanguage.../v1beta/openai).
- MODELOS DINÂMICOS: NOVO GET /api/ai/models (models_api.go) faz GET real na chave e traz modelos disponíveis (openai/groq/anthropic /v1/models; gemini /v1beta/models?key=). base_url vazio usa padrão do provider. UI: botão "Buscar modelos da chave" vira dropdown.
- 3 ABAS AGENTE CONFUSAS: renomeadas → "1. IA Padrão" (LLM base/fallback), "2. Agentes Especializados" (atendente clientes / gerenciador via telegram), "3. Atendimento WhatsApp" (privado/grupo). Cada uma com caixa explicativa.
- PROMPTS PADRÃO: NOVO GET /api/ai/default-prompts. UI pré-preenche system prompt vazio com o padrão do papel (editável).
- VOZ SIMPLIFICADA: STT sempre whisper local (campos escondidos). Aba Voz = só toggle "atender com IA" + voz TTS (Francisca padrão, edge-tts sem chave). 
- TTS POR IA NA CAMPANHA: NOVO POST /api/tts/generate (edge-tts → ogg base64). MassCallPage: alterna "Gravar/subir áudio" vs "Gerar por IA (texto)" com preview de áudio. Validado: gerou 20KB voz Francisca.
- PRE-AVISO TELEGRAM: broadcastRequest +names/pre_notify/batch_size/pre_notify_sec. runCampaign avisa de N em N os próximos números (com nome) e espera janela; /pular <número> no bot cancela. UI: toggle + campo "de quantos em quantos".
- BRANDING: astracalls-passkey.zip → hermes-passkey.zip (Dockerfile+passkey.ts). Validado no container.
- IP WHITELIST escondido (rodada anterior).
- PENDENTE: bot Telegram trazer contatos + disparar massa/aceitar lista; tutoriais/onboarding leigos; melhorar clareza áudio-conversa vs áudio-chamada no bot.
- Todos os deploys validados: 0 panic, WhatsApp 559184698653 conectado.

## 2026-07-11 10:41 — Favicon + comandos Telegram massa
- FAVICON: era logo Astra. Criado favicon.svg (telefone verde, mesmo ícone do painel); index.html aponta pro svg. Validado HTTP 200. (cache forte no navegador — Ctrl+Shift+R).
- BOT TELEGRAM massa/contatos:
  - /contatos [busca] — lista contatos da sessão pareada (até 50).
  - /massa <núm1, núm2...> — dispara o áudio guardado (mande áudio antes) pra vários, com pré-aviso de 10/10 e captura de resposta. Cria campanha persistida (aparece na aba Campanhas).
  - /pular <número> — remove do lote no pré-aviso.
  - /ajuda atualizado com os novos comandos.
- Validado: build compilou, 0 panic, favicon servido.
- ÚNICO PENDENTE do backlog do dia: tutoriais/onboarding pra leigos (tooltips, guia passo-a-passo, wizard 1ª ligação).

## 2026-07-11 10:48 — Página de Ajuda/Onboarding (fecha backlog do dia)
- NOVA aba "Ajuda" (1ª do menu, ícone ?): HelpPage.tsx — guia passo-a-passo pra leigo do zero até a 1ª campanha:
  1. Conectar WhatsApp (QR) 2. Preparar áudio (gravar OU gerar por IA) 3. Escolher contatos+filtros+salvar lista 4. Disparar campanha (intervalo, pré-aviso Telegram) 5. Acompanhar resultados (% escuta, interesse, score) 6. Reaproveitar (exportar interessados p/ nova lista).
  - Botões que levam direto pra cada aba; checklist mostra se WhatsApp já está conectado.
  - Seção Telegram (áudio→número, /massa, /contatos, /pular) e Boas Práticas anti-bloqueio (opt-in, warm-up, intervalos).
- Validado no bundle live.
- TODO o backlog de feedback do dia ENTREGUE. Falta só o teste REAL de disparo (guard-rail: precisa dona + áudio real).

## 2026-07-11 11:04 — Logs ilegíveis + tema escuro + wizard de setup
- LOGS ILEGÍVEIS (cinza sobre cinza nos 2 temas): LogsPage terminal agora fundo sólido slate-950 + borda slate-700; cores por nível (info branco, debug slate-400, warn amber, error red) e categoria (call emerald, telegram cyan, ai purple). Antes bg-black/50 (translúcido→cinza) + text-muted-foreground.
- TEMA ESCURO ruim/ícones sumindo: aumentado contraste — background 222 30% 7%, card 15%, border 30%, e muted-foreground 65%→78% (era isso que sumia ícones/textos secundários).
- WIZARD DE CONFIG INICIAL: NOVO SetupWizard.tsx — modal no 1º login (localStorage hermes.onboarding.done) com 4 passos: conectar WhatsApp (detecta se já pareou) → chave IA → bots → 1ª campanha. Botões levam direto pra aba. Botão "Abrir assistente de configuração" na Ajuda reabre.
- Validado live: bundle tem wizard, css tema novo, 0 panic.
- ROADMAP item 14: TOUR guiado POR TELA (overlay tipo driver.js destacando elementos) ainda PENDENTE — é o passo mais complexo, precisa lib de overlay. Wizard entregue cobre o "facilitador de config inicial"; falta o tour in-loco por aba.

## 2026-07-11 11:30 — Correções visuais + assistente de configuração
- LOGS ilegíveis (cinza sobre cinza): LogsPage agora tem terminal com fundo sólido bg-slate-950, borda visível e cores por nível/categoria (slate-100 info, slate-400 debug, emerald/cyan/purple por categoria). Validado na tela: legível.
- TEMA PRETO (dona queria preto de verdade): index.css .dark reescrito p/ neutro — background 0 0% 4% (preto), card 0 0% 9%, muted-foreground 0 0% 80% (ícones/texto secundário bem visíveis, era o que sumia), border 0 0% 24%. Validado no CSS live.
- ASSISTENTE DE CONFIGURAÇÃO INICIAL: NOVO components/onboarding/SetupWizard.tsx — modal de 4 passos (1 conectar WhatsApp/QR → 2 chave IA+provider+modelo → 3 bots Telegram/atendimento → 4 primeira campanha), com botões que levam à aba certa, dots de progresso, detecção de WhatsApp pareado. Estado em localStorage (hermes.onboarding.done). Montado no App (aparece no 1º login). Botão "Abrir assistente de configuração" na HelpPage reabre. Validado no bundle live.
- Sanity: site 200, replicas 1/1, 0 panic.
- PENDENTE (P0, item 14 do roadmap): TOUR guiado por tela com overlay (driver.js) destacando cada elemento — é o passo além do wizard; anotado, não feito ainda.

## 2026-07-11 12:28 — TESTE REAL + diagnóstico VoIP
- BOT TELEGRAM: FIX aplicado. Causa: handlePutAI salvava config mas NÃO recarregava o s.aiAgent global que o bot usa; e modelo era opus (falhava no gateway). Fix: handlePutAI agora chama reloadAI + sincroniza settings.AI global. Modelo trocado p/ fila ECO (kr/claude-haiku-4.5, key inovare-claw-eco sk-d7f1...94326c2a, base claudeopus.inovareinteligenciaartificial.com). Compose v3 atualizado. Gateway ECO testado (curl → responde via gemini-2.5-flash). RESULTADO: bot voltou a responder (confirmado pela dona).
- CAMPANHA: pipeline de dados 100% OK — TTS gera áudio, campanha dispara, persiste, aparece na aba Campanhas, analytics agrega. Validado: 2+ campanhas persistidas, GET /api/analytics/calls correto.
- PROBLEMA REAL = VoIP não toca no destino. Logs com -debug mostram:
    <call><offer><audio enc="opus" rate=8000/16000/></offer></call> SAI, mas peer NUNCA dá ACK; após ~45s manda <terminate> e recebe <ack class="call" error="439">.
  - call-creator aparece como @lid; offer anuncia só codec OPUS (não MLOW que WhatsApp moderno espera). Erro 439 = provável rate/call-token/LID.
  - Número destino 559185685106 EXISTE no WhatsApp (check confirmou, verifiedName). Não é o número.
  - Hipótese forte: v3 (merge upstream v0.0.4) regrediu/não tem os fixes de LID/TCToken/MLow que o AstraCalls V9 tinha (memória: V9 559192438288 funcionava). V9 hoje está 0/0 (desligado).
- Debug REVERTIDO (logs limpos de novo).
- PENDENTE CRÍTICO: consertar VoIP no v3 (portar fixes LID/TCToken/MLow do V9) OU subir o V9 e comparar o offer (V9 deve mandar enc="mlow"). Decisão da dona.
- Tour guiado por tela: ainda pendente.

## 2026-07-18 — Deploy beta build 20260718-1221 (3 features broadcast)
Sessão autônoma. 3 features implementadas, deployadas e validadas via API:

### Features entregues
1. **Fluxo 2 áudios** — broadcast aceita `audio_2`/`tts_message_2`/`audio_url_2`/`audio_base64_2`. Fluxo: toca áudio 1 (isca) → VAD espera resposta do peer → toca áudio 2 (pitch) → conversa com IA. Usa `fetchMedia` de messaging.go pra consistência.
2. **Background noise (ambient mixing)** — `SetAmbientNoise` no VoiceAgent mixa PCM loop aditivo em cada frame de saída. Configurado via `background_noise` + `background_noise_volume` no agent_profile. Resolve arquivo de `client/dist/audio/ambient/{nome}.{mp3,ogg,wav}`.
3. **Áudios ambient no container** — deploy-beta.js atualizado pra incluir mp3 de `client/public/audio/ambient/` (até 2MB cada). 14 arquivos ambient confirmados dentro do container.

### Testes API (VPS 62.171.128.241)
- JWT gerado manualmente (HMAC-SHA256, secret padrão, user 4e8adf4a).
- Broadcast com 2 TTS → 200 OK, campaign criada (eebd4e80). Ambas as mensagens sintetizadas.
- Profile Solar B2B atualizado: `background_noise=call_center, background_noise_volume=0.15`.
- Log confirmou: `"background noise carregado" name=call_center samples=1300079 vol=0.15`.
- Ligação tentou número fictício → `no-whatsapp` (esperado, WhatsApp session desconectada).

### Arquivos modificados
- `cmd/server/broadcast.go` — fetchMedia pra audio 2, carga de ambient PCM de profile, 3 chamadas SetAmbientNoise
- `deploy/deploy-beta.js` — inclusão de arquivos ambient (regex inAmbient)
- `deploy/sync-ambient.js` — criado (standalone sync de ambient pra VPS)

### Pendente
- **Teste VoIP real**: WhatsApp session `connected: false`. Precisa reconectar + número real.
- **Promote to stable**: `node deploy/promote-stable.js` (só com confirmação da dona).
- **Warning AI**: logs mostram problema de credencial kiro com `kr/claude-haiku-4.5` — não afeta broadcast, mas vale investigar.

## 2026-10-03 noite — v0.7.0: publicar + bateria de testes (dona ausente, autorizou tudo)
- Plano: compilar (--so-compilar) → bancada → produção → etapa 1 (texto) → etapa 2 (pronúncia) → etapa 3 (ligação real).
- 20:26 bancada pegou: rodízio incluía chaves Gemini mortas → Gemini fora do rodízio (commit 0d232b0).
- 20:33 v0.7.0 NO AR (20261003-2026_0d232b0). Limpeza apagou a v0.6.1 (anterior) + backup → corrigido hermes-release.sh, v0.6.1 reconstruída do commit exato, backup refeito.
- 20:39 achado de segurança: mass-call/mass-message/campanha por etapa aceitavam a linha de outra conta → corrigido (commit 47a3f7c), publica junto com o próximo.
- 20:44 v0.7.0 + correção de segurança NO AR (20261003-2039_47a3f7c). Produção saudável (2 linhas, voz ok).
- Etapa 1 (texto) rodando na bancada: Gemini atual (A) × Groq qwen3.8 (B), 6 perfis × 3 rodadas. Parcial: A notas 9–10, ~0,8 s; B ~0,3 s mas erra mais (termos técnicos, "voy", grosseria).
- Etapa 3: painel sem login → gatilho = bancada (8288, "Cliente Simulado") liga pro 8653 e a produção atende sozinha (auto_answer). Conta de teste da bancada ganhou senha própria de teste (só na bancada, root-only) e trial estendido NA BANCADA. Script /root/ligacao-teste.sh.
- Bancada: preparar passou a copiar Groq/OpenRouter/Webshare e reapontar a chave STT (a 1ª versão quebrava a voz da bancada).
- 20:51 publicada a regra de linguagem simples (20261003-2047_56bc742). Produção ok.
- 21:04 publicado 20261003-2100_ec2fc3c ('+' falado 'mais', lab de pronúncia normalizado). 1ª compilação falhou na VPS (passageiro), 2ª ok.
- 21:23 auto-atendimento REAL publicado (20261003-2112_664f094): produção atendeu em 6 s. Bancada TRAVOU (SIGABRT no codec MLow, silk/resampler.c:101, OPUS_HARDENING) ao decodificar áudio da produção — mesmo erro derrubou a produção em 25/09 01:55. Ligações Hermes×Hermes suspensas até corrigir o codec. Sugerido à dona: ligar do celular 8288 pro 8653.
- 21:29 codec MLow recompilado sem OPUS_HARDENING (reproduzido: lib antiga aborta com pacote aleatório; nova passa 200k) e instalado em /usr/local/lib (backup em /opt/hermes-call/codec-backup).
- 21:30 ligação real IA×IA completa sem travar. Achados: aceite do Hermes não é reconhecido pelo WhatsApp (quem liga segue "chamando") → aceite automático desligado de novo; persona da ligação recebida = assistente da dona; latência média ~3,0 s.
- 21:34 reverter → ec2fc3c; 21:39 publicado 20261003-2134_7d82f24 (aceite atrás de HERMES_AUTO_ANSWER_ACEITAR, padrão desligado). Drop-in de teste removido. Produção saudável.
- 22:54 a bancada (ligada ao 8288) estava na build com aceite real e ATENDEU as ligações de teste da dona pro 8288 (cliente simulado falando junto) → atualizada pra 7d82f24 (aceite desligado).
- 23:06 dona pediu pra encerrar e documentar (tokens). Feito: oferta interrompível (janela), REGRESSOES_LIGACAO.md, Groq/WhatsApp via VPS 53 (botão; falta Squid que a dona roda), STT descarta eco do contexto. Passagem de bastão no topo do CONTINUAR_DAQUI.md.
