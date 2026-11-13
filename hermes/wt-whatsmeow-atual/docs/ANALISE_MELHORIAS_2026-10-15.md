# Análise de melhorias: todas as áreas (15/10/2026)

> Pedido da dona em 15/10: "veja o que pode melhorar nesse sistema de campanha", com a campanha piloto rodando.
> Base: produção **v0.13.0** (build `20261015-0904_1c1f593`, no ar desde 09:10), banco `wacalls_main`, registro
> (`journalctl -u hermes-call`) de 14 e 15/10 até 11:30, e o código do ramo `pc/v0.8.0` (= o que está no ar).
> **Nada foi alterado na produção**: só leitura de logs e consultas ao banco. Telefones mascarados (×1234).
> A análise anterior é `ANALISE_MELHORIAS_2026-10-02.md`; a seção 0.4 diz o que dela já foi resolvido.

Legenda de esforço: **P** pequeno (horas) · **M** médio (1-2 dias) · **G** grande. 👤 = só a dona faz (segurança/senha/decisão).

## 0. Retrato da produção (15/10, 11:30)

### 0.1 Saúde
- v0.13.0 no ar desde 09:10 (reinícios de hoje: 06:57 para a isca nova, 09:10 para a v0.13.0). 5 reinícios em 7 dias,
  todos publicações. VPS de pé há 105 dias; RAM 3,4 GB usados de 7,9; disco 29% (101 GB livres); journal 910 MB (teto 2 GB).
- Avisos da semana (nível WARN/ERROR): 28 "telegram poll error" (só ao reiniciar, inofensivo), 7 "número não está no
  WhatsApp", 4 "IsOnWhatsApp falhou (timeout)", 3 "parte da resposta não tocou (TTS falhou)", 2 "motor primário sem
  resposta a tempo", 1 "retry motor primário" (503 do Gemini), 1 "chave recusada 401" (Groq), 1 "offer decrypt call key",
  1 "watchdog: chamada presa" (14/10 17:19). Nenhum pânico.
- Backup diário do Hermes: **OK** hoje às 03:31 (9 bancos, cópia no Drive em 24 min). Backup de todas as VPS:
  **falhando há 7 dias** (item 1.2). Avisos de operação no Telegram: **nenhum chega** (item 1.1).

### 0.2 Campanha piloto `8843d578…` (297 imobiliárias, 48/dia, 7h–18h, seg–sex)

| | 14/10 (isca 5,7 s) | 15/10 até 11:20 (isca 9,6 s) | Total |
|---|---|---|---|
| Discadas | 47 | 19 | 66 de 297 (22%) |
| Atendidas | 13 (28%) | 3 (16%) | 16 (24%) |
| Não atenderam | 29 | 12 | 41 |
| Sem WhatsApp | 3 | 4 | 7 (11%) |
| Sem conexão | 2 | 0 | 2 |
| Chegaram à oferta | 6 | 0 | 6 |
| Conversaram com a IA | 3 | 0 | 3 |
| Demonstração marcada | 0 | 0 | 0 |

- 0 pedidos de "não me ligue" (`do_not_call` vazia), 0 erro de preço/produto (a IA quase não falou), nenhuma parada
  por risco (`line_risk_events` vazia). Espaçamento ~11–14 min, conforme o esperado.
- **O painel mostra "594 contatos"** para 297 números (item 3.1).
- **Custo por ligação não dá para medir**: `ai_cost_monthly` registra R$ 0,24 em outubro e `ai_cost` parou em 24/09,
  embora as 16 ligações tenham usado Gemini, ElevenLabs e Groq (item 4.3).
- v0.13.0 (lead manda mensagem → liga na hora) **ainda não disparou nenhuma vez**: nenhuma linha "mensagem de lead:"
  desde 09:10. Continua sem teste real.

### 0.3 O dado mais importante: onde a ligação morre

As 16 atendidas, pelo registro (`gate pcm2` → `áudio 1 (isca) tocado` → `call terminated by peer`):

| Dia/hora | Nº | O que aconteceu | Duração real |
|---|---|---|---|
| 14 11:13 | ×4943 | ouviu a isca inteira (5,64 s), desligou 1,6 s depois, sem fala completa | 7,2 s |
| 14 11:23 | ×0405 | idem, 1,7 s depois | 7,3 s |
| 14 11:30 | ×3537 | oferta 100%; "estou em reunião"; IA respondeu; desligou | 42 s |
| 14 12:24 | ×1417 | isca inteira, desligou 2,1 s depois | 7,7 s |
| 14 13:25 | ×6388 | isca inteira, desligou 1,5 s depois | 7,2 s |
| 14 13:36 | ×8788 | desligou **no meio da isca** (4,3 s) | 4,3 s |
| 14 13:44 | ×9901 | cortou a oferta em 49%, não conversou | 20 s |
| 14 14:03 | ×3250 | oferta 100%, ficou calado 30 s, desligou (antes do re-engajamento da v0.12.0) | 75 s |
| 14 16:00 | ×0914 | desligou **no meio da isca** (3,9 s) | 3,9 s |
| 14 16:07 | ×7134 | oferta 50%; "não tenho interesse, estou em reunião" | 29 s |
| 14 16:16 | ×8077 | oferta 100%; "Sim"; "Supermercado"; IA demorou 4,4 s; desligou | 61 s |
| 14 16:53 | ×0408 | oferta 96%, ficou calado, desligou | 31 s |
| 14 17:03 | ×3016 | isca inteira, desligou 1,9 s depois | 7,5 s |
| 15 07:12 | ×4500 | desligou **no meio da isca nova** (6,0 de 9,6 s) | 6,0 s |
| 15 08:33 | ×1700 | idem (6,5 s) | 6,5 s |
| 15 10:35 | ×1318 | idem (8,6 s) | 8,6 s |

**Resposta à pergunta dos "5.641 a 5.663 ms"**: é medição, não comportamento. Nos 5 casos a isca tocou inteira
(`durMs=5641…5663`, o áudio tem 5.669 ms), o sistema entrou em "aguardando resposta do cliente" e a pessoa desligou
**1,5 a 2,1 s depois**. O código devolve só a duração da isca quando a chamada cai nessa espera
(`broadcast.go:2670-2673` → `return dur1, 0, true, false`; gravado em `:2306-2307`), por isso o banco mostra 5,65 s
para ligações que duraram 7,2–7,7 s (item 2.2). Não há atraso nem silêncio técnico entre atender e a isca
(0,4–0,5 s de aquecimento), nem entre a isca e a espera.

O que a pessoa fez nesses 1,5–2 s o registro não diz: não houve fala completa (o detector precisa de 600 ms de
silêncio depois da fala; quem diz "não, obrigado" e desliga na hora não fecha uma fala). A gravação no Telegram
responde; a revisão de 14/10 13:55 anotou "sem falar ou com 'não tenho interesse'". Ou seja: **a pessoa ouve a
abertura inteira e recusa ou desliga na hora**. É o roteiro, não a técnica.

**Leitura dos 16 casos:** 10 de 16 (62%) não passaram da isca; 6 ouviram a oferta; 3 conversaram; 0 marcaram.
A isca nova de 9,6 s piorou: 3 de 3 desligaram no meio dela (com a antiga, 2 de 13 desligaram no meio).
Dos 6 que ouviram a oferta de 23 s, 3 ficaram calados até desligar.

Dois detalhes técnicos que dão cara de robô, vistos no código (`broadcast.go:2267-2271, 2647-2653`): a isca começa
0,4 s depois do atendimento, **antes de a pessoa dizer "alô"**, e **não é interrompível** (de propósito,
`docs/REGRESSOES_LIGACAO.md` §1): o "alô?" ou o "quem é?" dela é atropelado pela gravação.

**Proposta (uma mudança por vez, medindo 10 atendidas entre cada):**

1. **Isca curta, ≤ 3,5 s, terminando em pergunta** (sem código). Sugestão de texto, a dona decide:
   *"Oi, tudo bem? Aqui é da Inovári. Posso falar um minutinho com você?"* Gerar com a mesma voz
   (`hpp4J3VqNfWAUOO0d1Us`), trocar `audio_ref`, `audio_ms`, `request.audio_id` e `request.tts_message` (a IA usa
   esse texto como "o que o cliente já ouviu") e reiniciar o serviço sem ligação ativa, como em 15/10 06:57.
2. **Esperar o "alô" antes de falar** (código, P, v0.14.0): depois do atendimento, esperar até ~1,5 s por fala do
   cliente (ou o fim dela) e só então tocar a isca; e trocar a espera de 15 s pela resposta (`broadcast.go:2663`)
   por 4 s seguidos de um "Alô, tá me ouvindo?". Chave `HERMES_VOICE_WAIT_HELLO_MS` (padrão 1500; 0 = como hoje),
   teste no simulador (`internal/voice`, cenário novo) e ligação de verdade antes de publicar.
3. **Oferta curta, ≤ 150 caracteres (~10 s), terminando em pergunta** (sem código): já pedida em 02/10 (item 2.2)
   e ainda com 390 caracteres / 23 s. Das 6 que a ouviram, só 2 falaram algo depois.

Outras opções avaliadas: **voltar à isca antiga** não resolve (7 de 13 não passaram dela). **IA ao vivo desde o
início** (sem áudio gravado) só depois de resolver a latência (item 2.1): hoje a 1ª resposta da IA levou 6,5 s
(15/10 09:01) e 4,4 s (14/10 16:16); com a isca gravada a 1ª frase sai na hora.

### 0.4 O que a análise de 02/10 listou e já foi resolvido

| Item de 02/10 | Estado |
|---|---|
| 1.1 Telegram liga sem querer (agente "e") | ✅ v0.6.0 |
| 1.2 Retorno de ligação perdida quebrado (LID) | ✅ v0.6.0 (retornos funcionando em 14/10) |
| 1.3 Detector de promessas cria ligações falsas | ✅ v0.6.0 (confirmação no Telegram) |
| 1.4 Tela Logs para qualquer cliente | ✅ v0.6.0 |
| 1.5 Segredos nos logs | ✅ v0.6.0 (`redact.go`; "bot<redacted>" no journal de hoje) |
| 1.6 Sem backup diário | ✅ v0.6.0 + `ops/vps/` (OK hoje 03:31; o de todas as VPS falha, item 1.2) |
| 1.7 Sem alertas | 🟠 scripts prontos, **mas o arquivo de configuração está vazio** (item 1.1) |
| 1.8 Cobrança: brechas | ✅ v0.6.0 |
| 2.1 Ligação avulsa ignora o roteiro | ✅ v0.6.0 |
| 2.2 Abertura de 32 s | 🟠 oferta interrompível ✅ (v0.7.0), resposta à isca transcrita ✅; **oferta continua com 23 s** |
| 2.3 Respostas longas | ✅ v0.6.0 |
| 2.4 Motor reserva na voz | ✅ v0.7.0, **mas a chave da reserva está recusada** (item 1.5) |
| 2.5 Barge-in | ✅ v0.6.1 / v0.7.0 |
| 2.6 Latência (STT turbo, aquecer, STT antecipado) | ✅ v0.8.0 (whisper-large-v3-turbo, aquecimento); a latência que resta é do motor de IA (item 2.1) |
| 2.7 Custo do ElevenLabs (cache) | ✅ v0.6.0 |
| 2.8 Classificação e nota do lead | ✅ v0.6.0 |
| 2.9 RAG na ligação, bug "tocou", agendadas, fuso, fundo, limite 2 min | ✅ v0.6.0 / v0.9.0 |
| 3 Asaas sem chave | 👤 adiado pela dona |
| 3 Trocar plano, checkout, CPF, superpoderes, dados falsos, esqueci senha, painel leve | ✅ v0.6.0 / v0.9.0 |
| 3 Teste de 10 h | 👤 decisão comercial |
| 4 CI vermelho, `go vet` no publicar, channel, headers, `/uploads/`, logout/2FA, limite de login | ✅ v0.6.0 / v0.8.0 |
| 4 Senhas em docs | ✅ removidas (o histórico do git ainda as tem; a dona trocou as senhas em 03/10) |
| 4 Testes de cobrança e login | ✅ parcial (E3 em 04/10 com Postgres); `internal/auth` segue com 2 arquivos de teste |
| 4 `cmd/server` monolito (331 arquivos hoje) | 🟠 G, aos poucos |
| 4 Docs desatualizados | 🟠 de novo (item 5) |
| Login por senha no SSH (05/10) | 🟠 **ainda ligado** (item 1.4) |

---

## 1. Urgente (esforço P; nada mexe no roteiro)

### 1.1 Nenhum aviso de operação chega no Telegram
- **Problema:** `/etc/hermes-call/alertas.env` existe desde 03/10, mas `ALERTA_TG_TOKEN` e `ALERTA_TG_CHAT` estão
  **vazios**. `hermes-alerta.sh` então só escreve no journal. `HERMES_MONITOR_BOT_TOKEN`/`CHAT_ID` também não
  estão definidos no serviço.
- **Evidência:** journal dos últimos 7 dias, 7 vezes: `[hermes-alerta] sem /etc/hermes-call/alertas.env
  (ALERTA_TG_TOKEN/ALERTA_TG_CHAT): aviso só no journal`, sempre logo após `❌ BACKUP DAS VPS com falha`.
- **Impacto:** queda do serviço (`OnFailure` do `20-alerta-falha.conf`), backup com falha, disco cheio e o
  healthcheck de 5 min avisam ninguém. O CONTINUAR_DAQUI de 06/10 já anotava "aviso de falha no Telegram não chega".
- **Proposta (👤 P):** a dona preenche token e chat (pode ser o bot do Telegram que já usa no Hermes) e roda
  `bash /opt/hermes-call/ops/hermes-alerta.sh "teste"`. O agente prepara o comando com `read -s` para ela não colar
  o token no chat.

### 1.2 Backup de todas as VPS falha há 7 dias por um contêiner alheio
- **Problema:** na VPS de teste (209) existe um Postgres sem nome (`wizardly_kepler`, imagem `postgres:15`, "Up 7
  days", criado ~08/10 por alguém) cuja exportação falha; o `backup-vps.sh` termina com `fim COM FALHAS` e o
  `systemd` marca a unidade como `failed`.
- **Evidência:** `MANIFESTO.txt` de 15/10 no Drive: 7 itens `ok` (inclusive `postegresp2` 1,1 GB e o n8n) e
  `FALHA pg.wizardly_kepler - 3s (a exportação na origem falhou)`; `systemctl`: `hermes-backup-vps.service failed`.
- **Impacto:** o backup das outras VPS **está** sendo feito, mas a falha diária mascara uma falha real futura e
  (com 1.1 resolvido) vai mandar um alarme por dia.
- **Proposta (P):** descobrir de quem é o contêiner (não é do Hermes; perguntar à dona/ao agente do outro projeto);
  lista de exclusão em `backup-vps.sh` (ou pular contêiner sem nome de serviço) e tratar falha de 1 item como
  aviso, não como erro da unidade. Nada disso toca a produção do Hermes.

### 1.3 Arquivo do serviço gravável por qualquer usuário, com token e senha dentro
- **Problema:** `/etc/systemd/system/hermes-call.service` está com permissão **`-rw-rw-rw-`** (666) e traz
  `HERMES_TELEGRAM_TOKEN=…` e `WACALLS_PG_URL=postgres://hermes_call_v3test:<senha igual ao usuário>@…` em
  `Environment=`, fora do `10-segredos.conf` (600).
- **Evidência:** `ls -l /etc/systemd/system/hermes-call.service` (ago/05, 666); `grep Environment` do arquivo.
- **Impacto:** a VPS é compartilhada (Atlas, Lucrativa, contêineres): qualquer processo local lê o token do bot e
  pode trocar o `ExecStart`, que roda como root no próximo reinício. A senha do banco é o próprio nome do usuário.
- **Proposta (👤 P, regra 7):** `chmod 644` no `.service`; mover os dois `Environment=` para o `10-segredos.conf`;
  trocar o token no BotFather e a senha do usuário `hermes_call_v3test` (`ALTER USER … PASSWORD`), atualizar o
  drop-in e reiniciar fora da janela de discagem. O agente prepara o script; a dona roda e o agente confere.

### 1.4 SSH ainda aceita senha de root
- **Problema:** `/etc/ssh/sshd_config.d/50-cloud-init.conf` tem `PasswordAuthentication yes` (vence o `no` do
  arquivo principal) e `PermitRootLogin yes`. Apontado em 02/10 e 05/10; continua.
- **Evidência:** `fail2ban-client status sshd`: 24.381 IPs banidos no total, 9 agora.
- **Impacto:** o que protege o root é só a senha e o fail2ban. Chaves já estão em uso (`ssh hermes-prod`).
- **Proposta (👤 P):** `PasswordAuthentication no` no `.d` e `PermitRootLogin prohibit-password`; `sshd -t`;
  reiniciar o sshd **mantendo a sessão aberta** e testar a chave numa segunda sessão antes de fechar.

### 1.5 A reserva da IA da ligação não funciona (chave Groq recusada)
- **Problema:** quando o Gemini demora, a ligação tenta a reserva no Groq e a chave é recusada (401).
- **Evidência:** 14/10 16:16:19 `voz: motor primário sem resposta a tempo, usando o reserva primary=gemini-flash-lite-latest`
  → 16:16:36 `pool de chaves: chave recusada status=401 chave=b242f2ef modelo=llama3-8b-8192` → latência real
  4.373 ms e 3.846 ms (`call_health` 14/10 16:16). A transcrição (Groq, whisper) funciona com outra chave.
- **Impacto:** sem reserva, a IA fica muda 4–6 s; o lead ×8077 (o melhor do dia) desligou nessa espera.
- **Proposta (👤 P):** no cofre, conferir/renovar a chave Groq `b242f2ef…` (ou apagar). Ver também 2.1.

### 1.6 Número sem WhatsApp gasta uma vaga das 48 e ~11 min da janela
- **Problema:** o pré-filtro em lote (`IsOnWhatsApp`) existe só no modo imediato (`broadcast.go:1223-1261`). No
  modo espaçado (`paced`) cada número é descoberto na hora de discar (`messaging.go:100`) e, mesmo sem ligação,
  conta em `sent_today` (`campaign_scheduler.go:160-161`), no teto da linha (`:150-152`) e ocupa um intervalo.
- **Evidência:** 7 de 66 discadas (11%) foram `no-whatsapp`; `sent_today=19` hoje inclui as 4 de hoje.
- **Impacto:** ~5 vagas por dia perdidas; menos atendidas por dia.
- **Proposta (P/M):** no 1º tick de cada dia, conferir em lotes de 20–30 os próximos ~60 da fila
  (`filterOnWhatsApp`) e marcar `no-whatsapp` sem discar; e quando `resolveCallPeer` falhar, não reprogramar o
  slot (discar o próximo no mesmo tick). Atenção: a consulta em lote deu `info query timed out` 4× em 14/10.

---

## 2. Qualidade da ligação e roteiro

### 2.1 Latência da IA: 1ª resposta em 4,4–6,5 s
- **Evidência:** `voice latência real ms_fim_fala_ate_1o_audio=6496 … llm_1a_frase_ms=5328` (15/10 09:01, retorno
  ao ×9058, que disse "Sim" duas vezes e desligou); `call_health` 14/10 16:16: 4.373 e 3.846 ms, `esperas_longas=1`
  hoje. O motor da ligação é `gemini-flash-lite-latest` (`call_ai`), o mesmo que deu 503 "high demand" às 08:33.
- **Impacto:** cada segundo mudo depois do "sim" é um lead a menos; os 2 casos com conversa real tiveram isso.
- **Proposta (👤 P):** motor da ligação no Groq (`qwen/qwen3.8-27b`, ~0,3 s, decisão de v0.7.0) com reserva no
  OpenRouter (mesmo modelo), chaves válidas no cofre; depois conferir no `call_health` (`latencia_media_ms`).

### 2.2 Duração gravada errada quando a pessoa desliga na espera da resposta
- **Evidência:** 5 ligações com `duration_ms` 5.641–5.663 que duraram 7,2–7,7 s (seção 0.3); `broadcast.go:2306`
  e `:2337` gravam `dur1`.
- **Impacto:** relatórios e a revisão horária leem "desligou na isca" onde foi "desligou depois da isca".
- **Proposta (P):** nos três retornos `ended=true`, gravar `time.Since(answeredAt)` (como `finishConversationCall`
  faz) e um motivo (`isca`, `espera`, `oferta`) em `reply`/`classificacao`.

### 2.3 Ligação que termina na isca não entra em `call_transcripts`
- **Evidência:** 16 atendidas, 4 linhas em `call_transcripts` (3 da campanha + o retorno das 09:01). A de 10:35
  (×1318) foi ao Telegram com `transcricao=ok` (`gravação entregue no Telegram`), mas o `Save` só acontece em
  `call_outcome.go:271-279`, dentro de `finishConversationCall`, que só roda se a conversa com a IA começou.
- **Impacto:** a aba Ligações, a exportação, a memória entre ligações (`call_memory.go`) e a revisão horária veem
  3 de 16. É por isso que "a transcrição foi ao Telegram e a tabela não tem nada". O texto existe, mas em
  `call_recordings.transcription` (aba Gravações, `recording.go:165`), que a aba Ligações e a memória não leem.
- **Proposta (P):** em `recording.go` (`transcribeAndSummarize`), gravar também em `call_transcripts` quando não
  houver linha para o `call_id`, com classificação `desligou_na_isca` / `desligou_na_oferta` / `desligou_na_espera`.

### 2.4 Oferta de 23 s (item 2.2 de 02/10, aberto)
- **Evidência:** `tts_message_2` com 390 caracteres; áudio `0628a381…` de 23,3 s. Dos 6 que a ouviram, 3 ficaram
  calados depois (×3250 30 s, ×0408, ×9901 cortou em 49%).
- **Proposta (👤 texto + P):** ≤ 150 caracteres terminando em pergunta; gerar áudio, trocar `audio_id_2` e
  `tts_message_2`, reiniciar. Terceira mudança da seção 0.3.

### 2.5 Espera de 15 s em silêncio depois da isca
- **Evidência:** `broadcast.go:2663` `WaitForUtterance(15 * time.Second)`; ninguém esperou tanto, mas quem esperar
  ouve 15 s de nada. **Proposta (P):** 4 s e um "Alô, tá me ouvindo?" (parte da mudança 2 da seção 0.3).

### 2.6 Resumo da gravação falha com 503 e não usa a reserva
- **Evidência:** 15/10 08:33:52 `retry motor primário tentativa=1 waitMs=500 err="openai 503 … high demand"` →
  `resumo=falhou` na entrega ao Telegram. `recording.go:151` chama `srv.aiAgent.plainText` (motor da plataforma, sem
  `withAnalysisReserve`, que `call_outcome.go:260` usa).
- **Proposta (P):** mesma reserva do `finishConversationCall`; 2 tentativas.

### 2.7 Metade da resposta da IA não toca (TTS falhou) em 3 ligações
- **Evidência:** 14/10 11:30:54, 16:07:14 e 16:16:39 `voice: parte da resposta não tocou (TTS falhou); histórico só
  com o que foi ouvido` — a 2ª frase ("Que dia e horário eu posso te ligar de volta…", "Você já usa alguma
  automação…") não saiu. Nas 3 o cliente desligou logo em seguida; o registro não traz o erro do ElevenLabs.
- **Proposta (P):** registrar o erro do TTS nessa linha (hoje só o texto) e conferir se é limite da chave do
  ElevenLabs ou corte por desligamento; se for o segundo caso, rebaixar para INFO.

### 2.8 Retorno quando o celular da dona recusa a ligação (`rejected_elsewhere`)
- **Evidência:** 08:04:24 ×9058 ligou; 08:04:30 `call terminated by peer reason=rejected_elsewhere ended_by=own_device`
  → `callback: não retorno`. O `reject` veio de `<LID da linha>@lid` **sem sufixo de aparelho** = o aparelho
  principal (o Hermes é o aparelho `:30`). Ou seja: **o próprio celular 8653 recusou**, 6 s depois de tocar (toque
  recusado, modo não perturbe ou outra ligação em curso).
- **Impacto:** lead de campanha que liga de volta e cai nesse caso fica sem retorno (é a regra de v0.6.0: "não liga
  se você atendeu ou recusou").
- **Proposta (👤 decisão + P):** para quem é de campanha recente, tratar recusa no celular em < 10 s como "não
  atendida" e retornar; ou manter como está e a dona ciente de que recusar no celular cancela o retorno.

### 2.9 Pequenos
- Re-engajamento da v0.12.0 ("Olá? Está me ouvindo?") ainda não disparou numa ligação real (o caso ×3250 foi
  antes da publicação). Conferir na próxima que ficar calada. ℹ️
- Pronúncia de "Inovári" na isca nova: não conferida por máquina; a dona ouve na biblioteca. 👤
- `offer decrypt call key … old counter` (14/10 17:13) e `watchdog: chamada presa` (17:19): 1 caso cada; observar.

---

## 3. Campanha, lista e painel

### 3.1 Painel mostra 594 contatos para 297
- **Evidência:** `campaigns.total=594`; `Create` grava `total=len(numbers)` (`broadcast.go:645`, `store.go:211`) e
  `SeedQueued` soma `total+1` por número novo (`store.go:304-321`). **Proposta (P):** `SeedQueued` não incrementa
  quando a campanha foi criada com a lista; corrigir o valor da campanha atual por `UPDATE` (com OK).

### 3.2 Opções sem botão no painel
- `paced` com `weekdays_only`, `start_hour/end_hour` e `campaign_only` só pela API (`MassCallPage.tsx`,
  Configurações › Atendente). Hoje a dona depende do agente para pausar/retomar/ajustar. **M.**

### 3.3 v0.13.0: mensagem de lead passa 2× pelo detector e sem teste real
- **Evidência:** `autoreply.go:227-240` (`detectAIField` + webhook/notificação `ai_field_detected`) roda antes de
  `callLeadBeforeText` (`:319`); se ninguém atende, `textReply()` chama `aiAutoReply` de novo (`campaign_msg_callback.go:87`).
  Só o teste da janela existe (`campaign_msg_callback_test.go`).
- **Proposta (P):** passar pelo contexto uma marca "já detectado" (ou mover a detecção para depois do `callLeadBeforeText`);
  teste com `Session` falsa cobrindo "liga → não atende → texto uma vez".

### 3.4 `scheduled_calls` com 15 `dispatched` desde julho e 13 `failed`
- Nunca fecham nem expiram (`status` em `scheduled_calls`). **P:** arquivar os anteriores a 30 dias.

### 3.5 Leads que escreveram
- ×8077 (mensagem manual 14/10 16:27) e ×7007 (09:01) sem resposta. Mensagem para quem conversou é da dona. ℹ️

### 3.6 Horário das atendidas (amostra pequena, só anotar)
- 14/10 9h–18h: 13 de 47 (28%); 15/10 7h–11h20: 3 de 19 (16%). Antes de mexer no horário, medir por faixa de hora
  ao fim da semana (`updated_at` de `campaign_results`).

---

## 4. Backend, testes, segurança, operação, custo

### 4.1 XML da sinalização entope o journal
- **Evidência:** `call_trace.go:52` registra em **INFO** até 40 mensagens por ligação; hoje 176 de 789 linhas (22%)
  com 3,7 KB cada ≈ 660 KB, **~85% dos bytes** do dia; journal em 910 MB.
- **Proposta (P):** `Debug` por padrão (o `HERMES_CALL_TRACE=true` passa a ligar o Info), ou cortar a 300
  caracteres na produção e manter o XML inteiro só na bancada (onde ele serve para o aceite, REGRESSOES §5).

### 4.2 Tabela `messages` com 1,28 GB (95% do banco)
- **Evidência:** 464.843 mensagens desde 05/2024 com `raw jsonb`; dump diário de 496 MB para o Drive; 3,9 GB em
  `/var/backups/hermes-call`. Nenhum `DELETE FROM messages` no código.
- **Proposta (👤 decisão + P/M):** reter N meses (LGPD ajuda a decidir) ou limpar `raw` de mensagens antigas;
  `VACUUM FULL` fora da janela.

### 4.3 Custo por ligação não é medido
- **Evidência:** `ai_cost` parada em 24/09; `ai_cost_monthly` R$ 0,24 em outubro com 16 ligações, 3 transcrições e
  resumos. O PLANO §4 depende desse número ("custo por cliente").
- **Proposta (M):** conferir por que a conversa da ligação (Gemini) e o ElevenLabs não lançam em `billing`;
  registrar por ligação em `call_health.voz` (tokens, caracteres TTS, segundos STT) e somar no painel de Custos.

### 4.4 `main` e GitHub 4 commits atrás do que está no ar
- **Evidência:** `git log main..HEAD` = 4 (v0.12.0 e v0.13.0 só no ramo `pc/v0.8.0` e nas tags `PRODUCAO-*`);
  `origin/main..HEAD` = 4; `ops/atualizar-copias.sh` não rodou nas duas últimas publicações. Regra 1 da dona.
- **Proposta (P, com OK):** avançar `main` (fast-forward) e enviar aos dois remotos; rodar `atualizar-copias.sh`;
  renomear o ramo `pc/v0.8.0` (carrega a v0.13.0) para algo sem versão.

### 4.5 Testes
- 96 arquivos em `cmd/server`, 41 em `internal`; CI com vet/build/test/race/govulncheck/npm audit/tsc. No PC:
  `go build ./...` e `go vet` OK; `go test ./cmd/server -run 'Campaign|Paced|…'` OK (sem banco).
- **Lacunas (P/M):** nada cobre "lead manda mensagem → liga → não atende → texto uma vez" (3.3); nenhum teste do fluxo
  2 áudios com desligamento na espera (a medição errada de 2.2 passaria); `internal/auth` com 2 arquivos.

### 4.6 Chaves de IA em texto puro em `settings`
- **Evidência:** `settings.value` de `ai`/`call_ai` guarda `api_key` junto do `credential_id` do cofre; vai inteiro
  no dump diário. **Proposta (M):** ler só do cofre e apagar o campo ao salvar.

### 4.7 Porta 8080 escuta em todas as interfaces
- `main.go:54` padrão `:8080`; `ss` mostra `*:8080`. O `ufw` (ativo) é o que fecha. **P:** `-addr 127.0.0.1:8080`
  no serviço para não depender do firewall (CLAUDE.md item 6).

### 4.8 Sobras na produção e na 209
- `/opt/whatsapp-activator` (serviço parado, escuta em `127.0.0.1:8091`), imagem `budtmo/docker-android` 6,8 GB,
  conta `ac***@internal.local`, linha "Linha Campanha - 5544" + banco; `wizardly_kepler` na 209 (1.2).
  **👤 P:** apagar com OK (já listado em 07/10).

### 4.9 Healthcheck não olha a campanha nem as linhas
- `hermes-healthcheck.sh` confere `/api/version` e disco. **Proposta (P/M):** conferir `/saude-local` (linhas
  conectadas) e "campanha ativa sem discagem há 60 min dentro da janela" — o que a revisão horária faz à mão —
  e avisar pelo `hermes-alerta.sh` (depois de 1.1).

### 4.10 Postgres
- Só em `localhost`, `peer` para socket e `scram` para TCP: OK. Índice `idx_campaign_results_cid` existe (a dúvida
  da REVISAO-V0.12 sobre `InRecentCampaignAny` está resolvida). Usuário com senha fraca: 1.3.

---

## 5. Documentação

| Item | Estado | Esforço |
|---|---|---|
| `CONTINUAR_DAQUI.md` com topo de 14/10 10:35 (v0.11.0) | atualizado nesta análise (15/10) | feito |
| `CLAUDE.md` "ESTADO ATUAL (04/10)": ramo `pc/v0.8.0` como pasta de trabalho, "v0.8.0" no nome com a v0.13.0 dentro | 🟠 | P |
| `docs/VERSOES.md` (05/10) e `docs/PENDENCIAS_BUGS.md` (24/09, §6 04/10) | 🟠 não citam v0.9–v0.13 | P |
| `docs/PLANO_MES_OUTUBRO_2026.md`: registro para em 08/10 | 🟠 v0.11–v0.13 e o piloto não anotados | P |
| `campanha/REVISAO-V0.12.md`: pendências A, B, E resolvidas; C (isca) em curso | 🟠 marcar | P |
| `.env.example`: chaves novas propostas aqui (`HERMES_VOICE_WAIT_HELLO_MS`) entram no catálogo com o teste `TestEnvCatalog` | — | junto com o código |

---

## 6. Plano sugerido

**Leva A (hoje, sem código; a dona roda, o agente prepara e confere):** 1.1 avisos, 1.3 e 1.4 segurança, 1.5 chave
Groq, 2.1 motor da ligação.

**Leva B (roteiro, uma mudança por vez, 10 atendidas entre cada; só com OK da dona):** isca curta (0.3-1) →
esperar o "alô" + espera de 4 s (0.3-2, v0.14.0) → oferta curta (0.3-3).

**Leva C (v0.14.0/v0.15.0, código P, com `publicar.sh` e volta por `reverter.sh`):** 2.2 duração real, 2.3
transcrição das que caem na isca, 1.6 pré-filtro no modo espaçado, 4.1 XML em Debug, 3.1 total, 3.3 detecção
dupla + teste, 2.6 reserva no resumo, 2.7 erro do TTS no registro.

**Leva D (depois do piloto):** 4.2 retenção de mensagens, 4.3 custo por ligação, 4.9 healthcheck da campanha,
3.2 botões no painel, 4.4 `main` e nome do ramo, 4.6 chaves só no cofre, 1.2 exclusão no backup das VPS.

**Só a dona:** token/chat dos avisos, permissões e senhas do servidor, SSH, chave Groq, motor da ligação, texto da
isca e da oferta, retenção de mensagens, apagar sobras.
