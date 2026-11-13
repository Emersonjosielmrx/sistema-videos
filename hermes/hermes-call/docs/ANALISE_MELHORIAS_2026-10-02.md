# Análise de melhorias: todas as áreas (02/10/2026)

> Pedido da dona em 02/10: "analise tudo que pode ser melhorado no projeto em todas as áreas;
> a versão em produção está com a ligação até boa, mas nada que não possa melhorar".
> Base: dados reais da produção (últimos 7 a 30 dias), logs da ligação de teste de 02/10 20:07
> e leitura do código do `main` (= v0.5.0 no ar, build `20260925-0158_29e4e85`).
> Nada de código foi alterado. Única ação na produção: cancelado 1 agendamento falso (ver 0.3).

Legenda de esforço: **P** pequeno (horas) · **M** médio (1-2 dias) · **G** grande.

## 0. Retrato da produção

### 0.1 Saúde
- v0.5.0 no ar desde 25/09 02:07, **0 reinícios**, 140 MB de RAM. Disco da VPS em 81% (29 GB livres).
- Em 7 dias: 3.996 linhas de log, 30 avisos e 13 erros. Nenhum travamento.
- A VPS 62.171.128.241 **não é exclusiva** do Hermes, ao contrário do que diz o CLAUDE.md: roda também o Atlas e o Lucrativa (trader).

### 0.2 Uso real (30 dias)
- 15 tentativas de ligação: **1 atendida** (o teste da dona em 02/10), 10 "sem WhatsApp", 3 "não completou", 1 abortada.
- As 10 "sem WhatsApp" são o **retorno automático de ligação perdida discando o LID** como telefone (item 1.2).
  Ou seja: ~8 pessoas ligaram para a linha na semana e nenhuma recebeu retorno.
- 215 usuários cadastrados (166 de teste desativados em 24/09). Nenhum pagante (Asaas ainda sem chave).

### 0.3 Ligação de teste de 02/10 20:07 (pelo Telegram, "Ligue pra ...")
| Momento | O que aconteceu |
|---|---|
| +0 s | Telegram: "Vou ligar usando o agente *e*" (escolhido por engano, item 1.1) |
| +10 s | Atendeu (chamou por 10 s). Conexão perfeita: 0% de perda, 0 erro de codec |
| +16 s | Isca de 5,4 s ("Alô, oi! Tudo bem com você?") |
| +19 a +42 s | Oferta gravada de **23 s**, que não pode ser interrompida |
| +48 s | Cliente: "Sim, quanto custa?" (STT 0,3 s) |
| +49 s | IA começa a responder em ~1 s, com resposta longa e **sem preço** |
| +60 s | Cliente desliga no meio da resposta. Classificado "🔥 Interessado, nota 90" |

### 0.4 Ação feita em 02/10 (com OK da dona)
O detector de promessas tinha agendado uma ligação da IA para **"Caetano" em 03/10 às 09:00**, a partir de uma
conversa pessoal ("eu vou esperar ela me ligar... ela vai me ligar sábado... pra me olhar a casa").
O status foi trocado de `pending` para `cancelled` (id `53cae5a3-6532-4a5f-a002-246eb52f8296`).
Para desfazer: `UPDATE scheduled_calls SET status='pending' WHERE id='53cae5a3-...'`.

---

## 1. Urgente: riscos e perdas (todos de esforço pequeno)

### 1.1 Telegram pode ligar sem querer (agente "e")
- `matchAgentByText` (`cmd/server/telegram.go:1496-1522`) usa `strings.Contains(texto, nome)`, sem tamanho mínimo.
  O agente chamado **"e"** casa com quase qualquer frase ("Lig**ue** pra...").
- Pior: `telegram.go:715-719`. **Qualquer mensagem curta sem número** (até 6 palavras) que contenha "e"
  ("beleza", "entendi") chama `handlePickCallAgent`, que **liga na hora** para o último número citado.
- **Correção:** casar por palavra inteira, nome com no mínimo 3 letras, e só aceitar o nome solto logo depois
  de o bot perguntar "qual agente?". Validar o nome ao criar o agente. Mitigação imediata: renomear ou apagar o agente "e". **P**
- Melhoria: agente padrão de ligação configurável (`/agentepadrao`). **M**

### 1.2 Retorno de ligação perdida 100% quebrado (LID)
- `maybeCallback` (`cmd/server/session.go:354-357`) usa `jid.User` do `@lid` como telefone. O pré-filtro
  (`broadcast.go:1169-1196` → `messaging.go:112-178`) diz "sem WhatsApp" e encerra.
- O telefone real chega na oferta (`caller_pn` / `evt.CallCreatorAlt`), mas é descartado em
  `internal/voip/call/callmanager_signaling.go:41`.
- **Correção:** usar `caller_pn` → `Store.LIDs.GetPNForLID` → ou discar o `N@lid` direto (ligar para `@lid` já
  funciona). Tratar entradas com "@" como válidas no pré-filtro. **P**
- O mesmo problema LID × telefone aparece em: OutboundOnly (`autoreply.go:283`), admin/handoff
  (`autoreply.go:113,483`, `handoff_smart.go:88-124`), CRM duplicado, lista de acesso (`accesslist.go:57-59`),
  contatos e Chatwoot. Correção: um helper único "telefone oficial do contato". **M**

### 1.3 Detector de promessas cria ligações falsas
- É só uma regex (`scheduled_calls_detect.go:34-40`). O `me ligar` no infinitivo pega "ela vai **me ligar**".
- Roda **antes** de todos os filtros (modo, OutboundOnly, horário, lista de acesso, humano assumiu:
  `autoreply.go:248-257` vs `:259-336`). Horário sempre fixo (amanhã 9h). Dispara sozinho, sem confirmação.
- **Correção:**
  - P: tirar o infinitivo, excluir terceira pessoa, mover depois dos filtros e exigir que seja lead/CRM.
  - P/M: status `awaiting_confirmation` com botões no Telegram (Confirmar / Descartar / Mudar horário).
  - M: classificar por IA "quem liga para quem / quando" e extrair o horário do texto.

### 1.4 Tela "Logs" mostra o servidor inteiro para qualquer cliente
- `GET /api/logs` (`httpapi.go:566`, `logstream.go:107-147`) não checa papel. Qualquer conta logada, até de teste,
  vê mensagens de outros clientes, e-mails, telefones e o token do bot do Telegram.
- **Correção:** só admin da plataforma, ou filtrar por `userID`. **P**

### 1.5 Segredos nos logs
- O token do Telegram vai inteiro no erro de rede (`telegram.go:545,2478,2510,2622,2665`, `telegram_buttons.go:32`,
  `voiceservice.go:139`, `monitor.go:97`). Está no journal da produção. A chave do Gemini vai em `?key=` na URL
  (`call_audio_gemini.go:78`, `models_api.go:150,367`) e pode voltar ao navegador.
- **Correção:** máscara central no `logStreamHandler.Handle` e Gemini com o cabeçalho `x-goog-api-key`. **P**

### 1.6 Sem backup diário e sem cópia fora da VPS
- Backup do banco só ao publicar (`ops/publicar.sh:70`), só do `wacalls_main`, no mesmo disco, 3 últimos.
  O cron de backup que existe na VPS é de outro sistema e falha todo dia ("container infra_postgres não encontrado").
- Ficam de fora:
  - os bancos de cada linha (chaves e histórico do WhatsApp, o que se perdeu em 24/09);
  - **as gravações, que estão em `/tmp/wacalls-recordings`** (sem `WACALLS_RECORDING_DIR` definido);
  - os uploads;
  - o áudio de ambiente das ligações (só existe no `dist` da VPS).
- **Correção:** timer diário com `pg_dump` de todos os `wacalls_*` + tar de gravações/uploads/áudios, envio para
  fora (rclone para B2/Drive), retenção de 7 diários e 4 semanais, aviso no Telegram se falhar. Mover as gravações para fora do `/tmp`. **M**

### 1.7 Sem alertas
- `/opt/hermes-call/monitor_registrations.sh` (cron a cada 5 min) **falha sempre**
  (`PGPASSWORD=...: command not found`): a dona não recebe aviso de cadastro novo nem de acesso suspeito.
  O script também tem token e senha escritos dentro.
- Nada avisa se o serviço cai ou se a linha do WhatsApp desconecta (`session.go:558-559` só muda o estado;
  `monitor.notifyError` nunca é chamado).
- **Correção:**
  - P: consertar o script (ou trazer para dentro do Go).
  - P: `OnFailure=` no systemd mais uptime externo.
  - P: avisar no Telegram em `LoggedOut`/`TemporaryBan`/`ConnectFailure`.

### 1.8 Cobrança: brechas
- O cupom `TESTE_GRATIS` está fixo no código (`billing_api.go:282,298-299`) e põe a assinatura como "active",
  reativando quem está com pagamento atrasado. Para conta nova não estende nada, mas a tela diz "aplicado". **P**
- O webhook do Asaas aceita tudo se o token estiver vazio (`billing_api.go:314-318`; agenda `agenda_api.go:430`).
  Recusar quando a chave estiver configurada e o token não, e usar comparação de tempo constante. **P**

---

## 2. Qualidade da ligação (o coração do produto)

### 2.1 A ligação avulsa (Telegram/painel) ignora o roteiro do agente: é por isso que fugiu do preço
- `doCallWithTTS` (`aiagent_actions.go:637-709`) nunca preenche `AgentPrompt`, `InitialContext` nem `OfferContext`.
  A IA conversa com o prompt padrão (`broadcast.go:1550-1571`), que manda "NUNCA invente preço… diga 'confiro e já
  te retorno'" e "descubra a dor". Os preços colocados no "Vendas Hermes Call" não são lidos nesse caminho.
- A IA também não sabe o que a isca e a oferta disseram.
- **Correção:** `AgentPrompt = buildAgentSystemPrompt(perfil)`, mais os textos da isca e da oferta no contexto. **P**
- Campo "tabela de preços" no perfil + regra "se perguntarem preço, diga o valor na 1ª frase". **P**

### 2.2 Abertura de 32 s antes de o cliente poder conversar
- Oferta padrão de ~390 caracteres (≈23 s), tocada por `pumpAudio` (`broadcast.go:2430-2463`), que **não aceita
  interrupção**. Um barge-in durante a oferta deixa um "stop" pendurado que engole a próxima fala da IA.
- A resposta do cliente à isca é **descartada** (`voiceagent.go:757-768`), assim como o que ele fala na oferta.
- **Correção:**
  - P: oferta de no máximo ~150 caracteres (8-10 s), terminando em pergunta.
  - M: oferta interrompível.
  - M: transcrever a resposta à isca e, se for "quem fala?"/"não tenho interesse", pular a oferta.

### 2.3 Respostas longas demais para voz
- `max_tokens: 1024` em todos os caminhos (`aiagent.go:1231,1324,1396,1483`), sem regra fixa de brevidade na ligação.
- **Correção:** ~150 tokens na ligação + regra "responda à pergunta na 1ª frase; máx. 2 frases; termine com 1 pergunta". **P**

### 2.4 Quando a IA falha (503 "high demand", visto 3 vezes na semana)
- Não há motor reserva na voz. São até 5 tentativas (≈33 s de espera) com o "keep-alive" já desligado. No fim,
  **a frase "⚠️ Erro ao processar com IA. Tente novamente ou use comandos diretos (/ajuda)" é falada ao cliente**
  (`aiagent_loop.go:34`).
- **Correção:**
  - P: na voz, frase neutra ("só um instantinho") e keep-alive ativo.
  - M: 1 tentativa curta; se o 1º token não vier em ~2,5 s, usar o motor reserva.

### 2.5 Interromper a IA (barge-in)
- A fala do cliente que interrompe é perdida (`voiceagent.go:841-843`). Ele precisa repetir.
- Depois de um corte, o contexto cancelado entra nas novas tentativas (`aiagent.go:1188-1194`, `time.Sleep` sem olhar
  o contexto): até ~33 s de IA "surda".
- No modo sem streaming, a frase seguinte ainda toca depois do corte (`voiceagent.go:1120-1129`).
- **Correção:** não tentar de novo com contexto cancelado, guardar ~500 ms de áudio no corte, parar a fila de frases. **M**

### 2.6 Latência real ≈ 2,2-2,5 s (o log "first audio 999 ms" não mede tudo)
| Etapa | Hoje | Melhoria | Esforço |
|---|---|---|---|
| Fim de fala | 600 ms | testar 450-500 ms | P |
| STT | `whisper-large-v3` (300 ms) | `-turbo` | P |
| Streaming | sintetiza e toca frase por frase, em série (`voiceagent.go:1001-1014`) | separar a síntese da reprodução | M |
| LLM | espera o filler acabar antes de chamar (`:999`) | não esperar | P |
| ElevenLabs | MP3 + ffmpeg via arquivo temporário (`tts.go:410-438`) | `pcm_16000` + `/stream` | P/M |

### 2.7 Custo do ElevenLabs
- Fillers e acks são pré-gerados **2 vezes por ligação**, sem cache: 48 sínteses. A 1ª rodada roda antes de tocar,
  então até número que não atende gasta 24 (`voiceservice.go:163-181`, `broadcast.go:1657-1692`).
- **Correção:** cache por voz+texto em memória e pré-gerar só depois de atender. **P**

### 2.8 Classificação e nota do lead
- "Interessado" vem de uma busca por palavra com **"sim"** na lista (`broadcast.go:1809-1827`), e vira nota 90
  (`lead_journey.go:27`). A IA de análise não recebe duração nem quem desligou.
- A duração gravada é isca + oferta, sem a conversa (`broadcast.go:2161`).
- O valor cru alimenta lead, Telegram e o **auto-treino do RAG** (falsos sucessos viram "conhecimento").
- A transcrição salva não tem isca, resposta à isca nem oferta.
- **Correção:** palavra inteira sem "sim", resultado reconciliado em todos os destinos, duração real, transcrição completa. **P**

### 2.9 Outros
- RAG e catálogo não entram no modo streaming da ligação (`aiagent.go:264-359` vs `:1113-1122`). **P/M**
- Bug "tocou mas não atendeu": vira sempre "não consegui completar" (`broadcast.go:1991-2007` lê a chamada depois
  de apagá-la); quem rejeita espera os 40 s inteiros. **P**
- Resultado da ligação agendada não volta para `scheduled_calls`, e não há nova tentativa. As 70 `failed` antigas
  nunca são retentadas nem limpas; as `pending` não expiram. **P/M**
- O painel mostra um horário comercial padrão que o backend não aplica (`features_api.go:800-807`). **P**
- Fundo `call_center` reinicia o loop no meio (`voiceagent.go:291`), sem abaixar sob a voz; o gate de ambiente só
  vale nos 800 ms de cauda (`voiceagent.go:849-853`). **P**
- Limite de 2 min por conversa: ao estourar, a análise roda antes de desligar (até ~25 s de linha muda). **P**

---

## 3. Produto, cobrança e painel

| Item | Onde | Esforço |
|---|---|---|
| **Asaas sem chave na produção**: ninguém paga (pendência da dona) | `/etc/systemd/.../10-segredos.conf` | dona |
| Não dá para trocar de plano nem cancelar; pedir Pro com assinatura Start viva gera fatura do Start | `billing_api.go:131-143`, `asaas.go` | M |
| Checkout sai do app sem volta (sem webhook, precisa clicar "Já paguei") | `AuthGate.tsx:79`, `RegisterScreen.tsx:133` | P |
| CPF/CNPJ opcional no plano pago, e a conta vira teste sem avisar direito | `auth_handlers.go:75`, `RegisterScreen.tsx:139` | P |
| Teste de só 10 h para parear, configurar e testar | `internal/auth/types.go:44` | decisão comercial |
| Onboarding é só um tour visual; 5 wizards sobrepostos (até 2.500 linhas) | `SetupWizard.tsx`, `EasyAgentWizard.tsx`… | M |
| "Superpoderes do Gestor" **não salvam** (o backend descarta os campos sem avisar) | `ManagerAgentSettings.tsx:245-290`, `settingsapi.go:239` | P (marcar "em breve") |
| RAG global com dados de exemplo; backend sem escopo global | `GlobalRagManager.tsx:16-75` | M |
| Roteamento Nível 1 salvo mas não aplicado nas ligações recebidas | `settingsapi.go:454`, `session.go:465-508` | M |
| Dados falsos que restam: AdvancedLab, Orquestrador, MeetingAI "Athena", Telefonia, Agenda | ver `5.3` do relatório de segurança/painel | P cada |
| Esqueci minha senha automático (código pelo WhatsApp) | — | M |
| Painel em 1 arquivo JS de 2,27 MB, sem carregamento por tela | `vite.config.ts`, `App.tsx` | P/M |

## 4. Engenharia e operação

| Item | Onde | Esforço |
|---|---|---|
| **CI sempre vermelho**: 2 testes antigos que não compilam travam os 17 outros | `cmd/server/sessionmanager_test.go`, `sessionstore_test.go` | P |
| Sem testes de cobrança e de login (`internal/auth` tem 0 testes) | — | M |
| `publicar.sh` não roda `go vet`/testes antes; tag `PRODUCAO-*` não vai ao GitHub | `ops/publicar.sh` | P |
| `/api/version` mostra `"channel":"beta"` em produção | `ops/publicar.sh:58` (+ `-X main.appChannel=producao`) | P |
| Senhas/tokens em docs versionados (senha root, Postgres, Telegram, Groq, Docker Hub, contas de teste), copiados também para `/opt/hermes-call-fonte` nas 2 VPS | `deploy/DEPLOY.md:149`, `docs/ARCHITECTURE.md:365-371`, `tests/.state/accounts.json` etc. | P (limpar) + dona (trocar) |
| Logout e "Encerrar sessões" não invalidam o token; 2FA nunca é pedido no login | `authmw.go:105-143`, `auth_handlers.go:88-133` | M |
| Limite de tentativas de login só por e-mail+IP; cadastro sem limite | `internal/auth/store.go:149-202`, `authmw.go:63` | P |
| `/uploads/` lista as imagens de todos os clientes | `httpapi.go:570` | P |
| Sem cabeçalhos de segurança (HSTS, nosniff, X-Frame-Options) no Go | `httpapi.go` | P |
| `cmd/server`: 189 arquivos / 48,7 mil linhas num pacote só (`telegram.go` 2.870, `broadcast.go` 2.463) | — | G (aos poucos) |
| Raiz do repositório: 20 relatórios `.md`, `_DOCS_PRESERVADOS/` duplicado, bundle de 7,6 MB, ~360 MB de lixo local | ver relatório | P |
| Docs desatualizados: "VPS exclusiva", seções de Docker no CLAUDE.md, Makefile apontando para `deploy/*.js` | `CLAUDE.md`, `Makefile` | P |

---

## 5. Plano sugerido

**Leva 1, v0.6.0 (itens pequenos de alto impacto, 1-2 dias):**
1.1, 1.2 (callback), 1.3 (regex + ordem + só leads), 1.4, 1.5, 1.8, 2.1, 2.3, 2.4 (frase neutra),
2.7 (cache), 2.8, bug "tocou" (2.9), CI verde (4), `channel`. Na VPS, sem código: backup diário + alertas (1.6, 1.7).
Publicar com `ops/publicar-teste.sh` antes e `ops/publicar.sh` depois, com volta por `ops/reverter.sh`.

**Leva 2, v0.7.0 (conversa mais natural):**
oferta curta e interrompível + resposta à isca transcrita (2.2), barge-in (2.5), motor reserva (2.4),
streaming em paralelo + ElevenLabs PCM (2.6), RAG na ligação, confirmação de promessas no Telegram (1.3).

**Leva 3 (produto):** troca/cancelamento de plano, onboarding guiado, limpeza de telas falsas, painel mais leve,
helper único LID → telefone em todo o sistema.

**Só a dona pode fazer:** chave e token do Asaas; cancelar assinaturas de teste no Asaas; revogar/trocar tokens
(GitHub, Docker Hub, Telegram, Groq) e senha root; decidir o tamanho da oferta e a duração do teste grátis.
