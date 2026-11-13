# Changelog

Todas as mudanças relevantes do Hermes Call.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/).
**Regra de versão:** cada melhoria sobe **+1 ponto** (o MINOR) e o projeto fica
**sempre abaixo de v1.0** (série `v0.x`): `v0.1.0` → `v0.2.0` → … Política e
procedimento de release em [`VERSIONING.md`](VERSIONING.md).

## Não lançado

## v0.21.5 — 2026-11-10

- Tirado o quadro "Prefere fazer manual?" da aba "Sem celular" (v0.21.4): só repetia o QR Code e o Por código,
  que já ficam nas abas de cima. A tela volta a ser a da v0.21.3. Só tela; o servidor não mudou.

## v0.21.4 — 2026-11-10

- **Opção manual sempre visível na aba "Sem celular"** do conectar linha: um quadro "Prefere fazer manual?" com os
  botões **QR Code** e **Por código**, que levam direto a conectar pelo WhatsApp de um celular de verdade (chip no
  aparelho). Aparece antes de começar e durante/depois de um erro do automático (ex.: "Couldn't connect" de 10/11).
  Só tela; o servidor não mudou.

## v0.21.3 — 2026-11-04

- **Linhas "conectadas" que pararam de receber mensagens** (Globo Solar e Advance, do FluxIA): depois do 405 de
  02/11, essas linhas enviavam mas não recebiam nada, nem depois de reiniciar o Hermes (não completavam a fila
  offline); a Globo pareada de novo em 03/11 travou outra vez às 04:20 de 04/11, repetindo os mesmos 4 eventos a
  cada reconexão. Biblioteca whatsmeow atualizada de 30/06/2026 para 02/11/2026 (`54038813c47f`).
- Ajustes pela biblioteca nova: lista de bloqueados agora vem com LID e número (a API devolve o número quando existe,
  como antes); `SetStatusMessage` recebe o texto numa estrutura.
- Migrações do banco das linhas (v15 e v16 do whatsmeow) só acrescentam colunas e são compatíveis com a versão
  anterior: voltar para a v0.21.2 continua seguro.

## v0.21.2 — 2026-11-02

- **Todas as linhas recusadas pelo WhatsApp por versão desatualizada (erro 405, aviso "client_outdated")**: desde
  02/11 19h o WhatsApp não aceita mais a versão do WhatsApp Web embutida no whatsmeow de jun/2026
  (2.3000.1042386815). Agora o Hermes busca a versão atual no web.whatsapp.com a cada início e, se a busca falhar,
  usa a última conhecida (2.3000.1052747707). A biblioteca whatsmeow continua a mesma.

## v0.21.1 — 2026-10-27

- **Disparo de mensagens não chegava em celulares sem o nono dígito no WhatsApp** (DDD 31 para cima, como o Pará): o
  número era montado com o 9, o envio "dava certo" e a mensagem ia para um número que não existe. Agora o disparo
  pergunta ao WhatsApp o número certo antes de mandar (como as ligações já faziam).
- **Bloquear sem aviso**: quem toca em "🚫 Bloquear" não aparece mais no Telegram (nem na ponte dos clientes, onde
  virava "interessado", nem num aviso à parte). Testado em 27/10 no celular da dona: botões chegaram e o Bloquear
  colocou o número na lista de não contatar.

## v0.21.0 — 2026-10-27

**Botões no primeiro contato do disparo** — *pedido da dona: "quem nunca recebeu mensagem daquele número recebe dois
botões, estou interessado e bloquear; o bloquear o mais parecido com o do WhatsApp, para em vez da pessoa bloquear de
verdade (problema com a Meta) nos avisar para não mandar mais"*
- No disparo de mensagens (`/api/mass-message`), quem nunca trocou mensagem com a linha recebe o texto com os botões
  **✅ Tenho interesse** e **🚫 Bloquear**. Quem já conversou recebe o texto simples, como antes.
- É opcional: no painel (Envio em Massa) o interruptor **Botões no primeiro contato** vem ligado; pela API vale
  `first_contact_buttons: true` (sem o campo = sem botões, como antes). Quem foi pulado aparece como "Pulado".
- **🚫 Bloquear**: o número entra na lista de não contatar da conta (vale para disparos, campanhas de ligação e retornos),
  a IA para de responder naquela conversa, a pessoa recebe "Pronto! Você não vai mais receber mensagens nem ligações
  deste número" e a dona é avisada no Telegram.
- **✅ Tenho interesse**: a dona é avisada no Telegram e a IA continua a conversa.
- O disparo agora pula quem está na lista de não contatar (antes mandava mesmo assim) e grava as mensagens enviadas no
  histórico da conversa.

## v0.20.1 — 2026-10-27

- **Campanha com várias linhas parava de discar** quando todas as linhas caíam e uma voltava: a fila inteira ficava na
  linha que caiu por último, e a que voltou (sem números) saía da campanha. Visto em 27/10: 277 números presos na 4247
  desconectada enquanto a 5106 estava conectada e parada. Agora a campanha lembra de todas as linhas que já discaram por ela; a
  que volta sem fila recebe a fila da linha desconectada (ou metade da fila de uma conectada), e as linhas voltam a se revezar.

## v0.20.0 — 2026-10-27

**Linha "sem celular" caiu: banido ou só desconectado?** — *pedido da dona: "se foram banidos, fazer o pedido de contestação, acompanhar de x em x horas e conectar o número assim que voltar, com o dono confirmando no Telegram"*
- Quando uma linha pareada num celular virtual cai, o Hermes pede ao ativador para ligar o celular e conferir o WhatsApp.
  Banido: o ativador pede a análise (contestação) sozinho e confere de 6 em 6 h; a dona recebe o aviso. Conta normal: a dona
  recebe na hora o botão **✅ Reconectar** no Telegram. Quando o banimento sai, chega o mesmo botão. Nada reconecta sem o toque dela.
- **Anti-loop robô x robô mais firme**: em 27/10 a IA da linha 4247 ficou conversando com o robô de atendimento de uma
  imobiliária (respostas em ~5 s, textos diferentes, nenhum limite pegava). Agora pausa o contato por 30 min com 3 respostas
  em menos de 10 s seguidas, 3 mensagens iguais ou mais de 6 trocas em 10 min.
- **Ponte do Telegram: linhas pessoais fora** (`HERMES_LEADS_SKIP_PHONES`): as mensagens continuam guardadas no Hermes,
  só não vão ao Telegram.

## v0.19.1 — 2026-10-27

- **Ponte do Telegram mandava mensagens vazias "do número para ele mesmo"** sempre que uma linha conectava ou religava:
  o celular troca mensagens internas com os próprios aparelhos (chaves, histórico, sincronização), que viravam
  "📱 Respondido pelo aparelho … [mandou uma mensagem]". Agora a ponte ignora mensagens internas (peer/protocolo), a
  conversa da linha com a própria conta e as mensagens entre linhas da dona.

## v0.19.0 — 2026-10-26

**Ponte dos clientes no Telegram** — *pedido da dona: "as mensagens dos clientes, independente do número, num único chat do Telegram (bot interessados no produto); o bot responde e eu recebo a resposta também; e posso marcar a mensagem e o cliente recebe do mesmo celular que ele enviou"*
- Toda mensagem recebida (fora grupos/status) em qualquer linha da conta configurada vai para um chat do Telegram, com o
  nome, o número do cliente e a linha. A resposta da IA vai junto ("🤖 IA respondeu"), e o que a dona responder pelo
  próprio aparelho também aparece ("📱 Respondido pelo aparelho").
- Respondendo (marcando) a mensagem no Telegram, o texto vai ao cliente pela mesma linha em que ele escreveu, entra no
  histórico da conversa (a IA fica sabendo) e o bot confirma "✅ Enviado pela linha …". Linha desconectada = avisa e não envia.
- Linha e contato vão no rodapé da mensagem (nada guardado; sobrevive a reinício). Só o chat configurado pode responder.
- Config: HERMES_LEADS_BOT_TOKEN / HERMES_LEADS_CHAT_ID / HERMES_LEADS_USER_ID (vazio = desligada). `lead_bridge.go`.

## v0.18.3 — 2026-10-26

- **Pareamento por código ("Por código" e "Sem celular") voltava sempre "400 bad-request"**: o nome do aparelho ia como
  "Hermes Call", e o WhatsApp só aceita "Navegador (Sistema)" de navegador/sistema comum. Agora vai "Chrome (Linux)".

## v0.18.2 — 2026-10-26

- Código de pareamento: o número vai no formato do WhatsApp (Brasil, DDD 31+ sem o nono dígito; 11–28 com ele) e só
  tenta o outro formato se der 400 — o "400 bad-request" do 91 98407-4247 era isso, não pressa. Com "429 rate-overlimit" o
  acompanhamento do celular virtual para na hora.

## v0.18.1 — 2026-10-26

- Conectar sem celular: pedir o código de pareamento logo depois de conectar dava "400 bad-request" (linha que estava
  deslogada). Agora espera o socket, tenta de novo e, por fim, o número sem o nono dígito. O acompanhamento que desiste
  não é mais relançado pelo painel aberto (eram 34 pedidos seguidos ao WhatsApp).

## v0.18.0 — 2026-10-26

**Conectar sem celular (aba "Sem celular" na tela de conectar a linha)** — *pedido da dona: "a pessoa entra no Hermes Call, digita o número e o sistema conecta ao WhatsApp e já conecta ao Hermes também, pra quem não quer ter celular pra fazer as ligações"*
- Na tela de conectar a linha, além de QR e "Por código", uma 3ª opção: a pessoa digita o número, o sistema registra num celular
  virtual (serviço "ativador", na VPS 157) e pareia ESTA linha. Quando o WhatsApp manda o SMS, a pessoa digita o código no painel;
  o pareamento é conferido por este servidor (a linha é do cliente; o ativador nunca a acessa) e, no fim, o celular virtual desliga
  sozinho (não gasta CPU) — dá pra ter vários números. Botão "Ver a tela do celular" mostra o andamento ao vivo.
- Backend: rotas `GET/POST/DELETE /api/sessions/{sid}/emulador`, `POST .../emulador/codigo`, `GET .../emulador/tela` que repassam
  ao ativador (`emulador.go`, `emulador_api.go`); o navegador nunca fala direto com o ativador. Configuração nova:
  `HERMES_ATIVADOR_URL` e `HERMES_ATIVADOR_TOKEN` (vazio = a opção não aparece). O pareamento é acompanhado numa goroutine que
  pede o código a este servidor (`PairPhone`) na hora certa.
- Frontend: `client/src/services/emulador.ts` e a aba nova em `SessionPairing.tsx`.
- Depende do ativador `whatsapp-activator2` com o modo de pareamento externo (aceita `hermes_session_id`; rotas `/link-code` e
  `/linked`). O que destravou isso (26/10): o celular virtual Redroid passou a vencer o Play Integrity (keybox de hardware) e o
  toque automático na tela do número (app Toque) — antes, em 08/10, esse caminho tinha sido dado como impossível.
- Revisão (26/10 manhã): o acompanhamento do pareamento espera até 60 min (antes 15, menos que boot + SMS + passo manual),
  confirma pelo JID da linha com o mesmo número (antes só "conectado"), tenta o código de pareamento 3 vezes e volta sozinho
  se este servidor reiniciar no meio (o painel aberto relança). Linha já conectada é recusada logo no começo. Ativador
  ocupado ou número já em outra linha voltam com mensagem clara. Rota nova `POST .../emulador/toque` e o painel deixa tocar
  na imagem da tela (para um passo que a automação não fizer). Erro da última tentativa aparece na etapa do número.
  Linha que caiu: digitar o mesmo número de novo na MESMA linha só repareia, sem SMS (outra linha é recusada).
- No ativador: um container Redroid por número, só um ligado por vez e desligado no fim (cada número isolado: dados,
  keystore, android_id).
- **Falta antes de publicar:** rede entre a VPS da produção e o ativador na 157 (túnel/porta com token) e um teste de ponta a ponta
  com número real.

## v0.17.0 — 2026-10-24

**Retorno pedido na ligação funcionando de ponta a ponta** — *pedido: "esse sistema de retorno deve ter um aí já mas não deve estar funcionando"*
- A ligação agendada (promessa) saía SEM o agente de vendas (o `agent_id` da promessa era gravado e nunca lido) e com a
  frase genérica "Estou ligando conforme combinamos". Agora usa o agente da promessa ou, sem ele, o da campanha que ligou
  para o número (igual ao retorno de ligação perdida). A promessa criada pela ligação usa uma saudação própria ("te
  ligando de volta como você pediu na nossa ligação").
- Saía pela primeira linha conectada da conta (podia ser a 8288). Agora sai pela linha que já ligou para esse número (procura com e sem o 9)
  (`number_line_history`), com a primeira pareada como reserva.
- Ligação que acabava antes da conversa (falou só na abertura e desligou na oferta) ficava "sem_conversa" sem análise:
  o "liga mais tarde" se perdia (caso real ×3452 em 21/10). Agora a gravação é analisada; se for `pediu_retorno` ou
  `interessado`, a classificação é trocada, a promessa é criada (botões no Telegram) e sai o aviso de interesse.
- Arquivos: `cmd/server/scheduled_calls_cron.go`, `scheduled_calls_detect.go`, `call_outcome.go`, `recording.go`,
  `interest_alert.go`, `autoreply.go`.

## v0.16.0 — 2026-10-21

**Alô de volta, retorno de ligação, aviso de interesse e monitor de grupos** — *pedido: "a pessoa só diz alô e o bot já diz 'é o seguinte'; tem clientes que pediram retorno que não sei se retornou; quero aviso separado de interesse; quero monitor de grupos"*

- **Alô de volta (A):** novo tipo `BaitReplyGreeting` em `voice.ClassifyBaitReply`. Quando o cliente responde à isca
  com apenas um cumprimento ("Alô?", "Oi, tudo bem?", "E aí?", "Bom dia", "Fala!", "Diga"), a IA cumprimenta de volta
  em vez de despejar a oferta gravada de 23 s. Identidade e recusa continuam com prioridade ("Alô, quem é?" → identity);
  "Pode falar" e "Sim, sou eu" continuam tocando a oferta. 11 novos casos de teste.
  Arquivos: `internal/voice/bait.go`, `internal/voice/bait_test.go`.

- **Retorno pedido na ligação (B):** quando a análise da IA classifica a ligação como `pediu_retorno`, agora cria uma
  promessa (scheduled call) com botões no Telegram (Confirmar / Amanhã 9h / Descartar), idêntico ao fluxo que já
  existia para pedidos por texto. Antes, `pediu_retorno` por voz não gerava nenhuma ação.
  Arquivo: `cmd/server/call_outcome.go`.

- **Aviso de interesse separado (C):** quando a classificação é `interessado` (🔥) ou `pediu_retorno` (📅), um segundo
  alerta distinto é enviado no Telegram, separado da notificação normal da ligação. Pronto para trocar de bot.
  Arquivo: `cmd/server/interest_alert.go` (novo).

- **Monitor de grupos (D):** verifica as mensagens de grupo contra ~30 palavras-chave (n8n, automação, agente IA,
  vibe code, cursor, chatbot, etc), como palavra inteira ("claude" não casa "Claudete"). Detecta pedidos de ajuda e
  anúncios de serviço. Envia notificação no Telegram com botões SIM/NÃO; o SIM devolve o número pra chamar (não fala
  com ninguém sozinho). No máximo 1 aviso por pessoa por grupo a cada 12 h. As decisões ficam em memória com as
  palavras e o trecho, pra calibrar depois. **Liga/desliga por conta** em Configurações › Voz › "Monitor de grupos"
  (`voice.group_monitor`), **desligado por padrão** pra que as outras contas do servidor não passem a receber aviso.
  Usa o mesmo bot por enquanto; `getGroupMonitorBot` isolada para trocar.
  Arquivos: `cmd/server/group_monitor.go` (novo, com teste), `cmd/server/session.go`, `cmd/server/telegram_buttons.go`,
  `internal/settings/store.go`, `cmd/server/settingsapi.go`, `client/src/components/settings/VoiceSettings.tsx`.

## v0.15.1 — 2026-10-19

**Webhook sai na hora (não espera mais até 30 s)** — *pedido: "respondeu mas demorou muito, veja se deu algo errado"*
- O evento era gravado em `webhook_queue` e só entregue na passada seguinte do worker, a cada 30 s. Medido em 19/10:
  mensagem do cliente entrou na fila às 14:44:26.988 e chegou ao FluxIA ~14:44:56; nas anteriores, de 6 a 28 s.
- Agora cada sessão tem uma fila em memória que entrega na hora e em ordem. O evento continua gravado antes
  (`next_try_at` = +1 min): se a entrega imediata falhar, ou a fila em memória estiver cheia, ou o serviço cair no meio,
  o worker de 30 s entrega com o backoff de sempre. A entrega imediata só tenta eventos com menos de 45 s, e o worker
  só pega os de 1 min ou mais: os dois não entregam o mesmo evento.
- Testes: `webhook_queue_test.go` (com Postgres de teste): os 3 eventos chegam em ordem em menos de 3 s e o worker não
  reentrega; falha na hora fica pendente para daqui a 2 min. Com o código antigo o 1º teste falha (nada chega em 3 s).
- Arquivo: `cmd/server/webhook_queue.go`.

## v0.15.0 — 2026-10-18

**Botões e listas clicáveis no WhatsApp (sem API oficial)** — *pedido: "adicionar ao Hermes" o que o AstraCalls tem,
para o FluxIA usar no lugar da enquete*
- Novos envios: `POST /api/sessions/{sid}/messages/buttons` (até 3 botões de resposta), `/messages/list` (botão que
  abre lista de opções) e `/messages/interactive` (botões de link, copiar texto, ligar e resposta). Portado do
  AstraCalls (mesmo whatsmeow): `messageSecret` + nó `<biz>` de native flow no envio; botões de resposta dentro de
  `documentWithCaptionMessage`. Em grupo, botão de resposta vira link wa.me (não posta a escolha para todos).
- **Quem toca num botão/lista chega no webhook `message` como `type: text`**, com `text` = escolha e o campo novo
  `buttonReply: {id, text, messageId}` (`messageId` = a mensagem com os botões). Antes chegava `unknown` e sem texto
  (também para botões vindos de outras ferramentas); no Chatwoot aparece a escolha. O agente de IA do próprio Hermes
  continua lendo só texto digitado (`extractMessageText`): não responde a toque em botão.
- Os botões enviados entram no histórico da conversa (`type: buttons`); antes `unknown` era descartado.
- Ainda não visto num celular de verdade se os botões aparecem em Android, iPhone e WhatsApp Web.
- Arquivos: `cmd/server/interactive.go` (novo), `webhook.go`, `httpapi.go`, `client/public/openapi.yaml`.

## v0.14.1 — 2026-10-15

**Linha que caiu não some mais no reinício** — *pedido da dona: "tente reaproveitar a mesma e faça essa correção"*
- Antes, uma linha deslogada (`logged_out`) tinha o cadastro apagado no próximo reinício, e o banco dela era
  arquivado. Ao reconectar, ela voltava com **id novo**, e campanha, teto e aquecimento da linha continuavam presos
  ao id antigo: a campanha não ligava nem com a linha conectada. Aconteceu com a 8653 em 15/10 14:42 (reinício das
  14:44).
- Agora a linha que já foi pareada fica no cadastro, desconectada ("Desconectado — use Reativar"). Reativar (QR ou
  "Por código") reconecta com o **mesmo id**, e tudo o que era dela continua valendo.
- Linha criada que nunca chegou a parear continua sendo descartada no reinício, como antes.
- Arquivo: `cmd/server/sessionmanager.go` (`Restore`).

## v0.14.0 — 2026-10-15

**Campanha espaçada: pré-filtro, rediscagem e A/B** — *pedido da dona: "não só a isca: as captações dos números, ligar
de novo para quem não atendeu, estratégias diferentes para testar"*
- **Pré-filtro de WhatsApp no modo espaçado.** Uma vez por hora a campanha confere no WhatsApp os próximos 60 da fila
  (lotes de 25, pausa de 2 s) e tira os que não têm conta antes de gastarem uma vaga do dia (no piloto, 7 de 66
  discadas eram número sem WhatsApp: cada um custava uma das 48 vagas e ~11 min). Mortos viram "Sem WhatsApp" no
  funil e não contam em `sent_today` nem no teto da linha. Lote cuja consulta falha fica para a próxima hora (não é
  dado como vivo). `HERMES_CAMPAIGN_PREFILTER=false` desliga, nos dois modos.
- **Rediscagem de quem não atendeu** (`pace_config.retry_no_answer`: 0 = desligado, no máximo 2 extras;
  `retry_gap_hours`, padrão 4): o não atendido volta à fila depois do intervalo, pelo mesmo caminho (conta nas 48 e
  no teto da linha); primeiro contato antes de rediscagem; a campanha só fecha quando as tentativas acabam. **Quem
  recusou a chamada não é rediscado** (coluna `rejected`: tocou e a pessoa encerrou), nem quem já atendeu depois em
  outra ligação. Campanha com rediscagem própria fica fora da repescagem antiga (`HERMES_AUTO_RETRY`). Coluna aditiva
  `campaign_results.attempts`. Ainda sem botão: liga por SQL no `pace_config`.
- **A/B da isca no modo espaçado:** `request.audio_id_b` volta da biblioteca depois de reinício; a variante que cada
  número ouviu fica em `campaign_results.variant` (aditiva) e se mantém na rediscagem; comparativo em
  `GET /api/campaigns/{id}/variants` (discadas, atendidas, conversaram, interessados, duração média).
- **Total da campanha não sai mais dobrado** (297 números apareciam como 594): `SeedQueued` não soma por cima do
  total gravado na criação.
- Arquivos: `cmd/server/campaign_paced_extras.go` (novo), `campaign_scheduler.go`, `campaigns_api.go`,
  `broadcast.go`, `internal/whatsapp_campaigns/store.go`; testes em `campaign_scheduler_test.go` e `store_test.go`
  (com Postgres).

**Ligação: medição e abertura**
- **Duração real** quando a pessoa desliga na isca ou na espera da resposta (antes gravava só a duração da isca:
  5 ligações de 7,2–7,7 s apareceram com 5,65 s no banco).
- **Esperar o "alô" antes da isca** (`HERMES_VOICE_WAIT_HELLO_MS`, padrão 0 = desligado): espera até esse tempo a
  primeira fala de quem atendeu e toca a isca depois que ela para (teto +2 s); o "alô" é descartado e não gera
  transcrição antecipada. A isca continua não interrompível. Só ligar depois de uma ligação de verdade
  (`docs/REGRESSOES_LIGACAO.md` §1).
- `HERMES_VOICE_BAIT_WAIT_MS` (padrão 15000): quanto esperar a resposta à isca antes de tocar a oferta.
- Arquivos: `broadcast.go` (`playTwoAudioOpening`, `runCampaign`), `internal/voice/alo.go` (novo); testes
  `TestSimulador_EsperaDoAlo_*`.

**Registro das ligações e mensagem do lead**
- **Ligação que cai na isca entra na aba Ligações** como "🔇 Sem conversa" (`call_transcripts`, com trava por
  `call_id` para a conversa completa prevalecer quando a análise e a gravação terminam juntas). Só ligação feita
  pelo Hermes; a recebida fica como estava. "Sem conversa" não entra na memória entre ligações, nas métricas de
  conversão, no pie do Dashboard nem no import do RAG.
- **XML da sinalização só em Debug** por padrão (era ~85% dos bytes do log de produção); `HERMES_CALL_TRACE=true`
  volta a Info, XML inteiro (bancada); `false` desliga.
- **v0.13.0: a mensagem do lead não passa mais duas vezes pelo detector de intenção** (o webhook `ai_field_detected`
  saía repetido quando a pessoa não atendia a ligação de retorno).
- Arquivos: `recording.go`, `transcript_store.go`, `call_outcome.go`, `call_memory.go`, `rag_api.go`,
  `call_trace.go`, `autoreply.go`, `client/src/pages/TranscriptsPage.tsx`.

**Captação: conferir o WhatsApp antes de ligar**
- `POST /api/sessions/{sid}/contacts/check-batch` (até 100 números; lotes de 25 com pausa; 503 com a linha
  desconectada e 502 quando a consulta ao WhatsApp falha, nunca "todos vivos" sem ter checado) e o script
  `D:\hermes\campanha\captacao\validar-whatsapp.py` (lotes de 50, pausa de 10 s, ~300 por dia, chave só por
  variável de ambiente), que gera `pronto-hermes-validado.csv` e `sem-whatsapp.csv`.

**Operação (scripts que a dona roda, em `ops/`)**
- `LIGAR-AVISOS-TELEGRAM.bat` → `ops/vps/configurar-alertas.sh`: preenche `/etc/hermes-call/alertas.env` (estava
  vazio desde 03/10: nenhum aviso de backup, queda ou disco chegava) e manda um aviso de teste.
- `TRANCAR-SERVICO-E-SENHAS.bat` → `ops/vps/trancar-servico.sh`: unit do serviço de 666 para 644, token do Telegram
  e URL do banco para o drop-in de segredos (600), senha do banco aleatória, token novo do bot (opcional), monitor de
  linha caída com o bot dos avisos, reinício só sem ligação em curso; desfaz sozinho se o serviço não subir.
- `FECHAR-SSH-POR-SENHA.bat` → `ops/vps/fechar-ssh-senha.sh`: SSH só por chave (o `50-cloud-init.conf` mantinha a
  senha de root ligada; 24 mil IPs banidos pelo fail2ban).
- `ops/vps/backup-todas/backup-vps.sh`: lista `IGNORAR` no `backup-vps.env` (um Postgres alheio na VPS de teste
  derrubava a unidade do backup todo dia).

**Sem mudança de comportamento por padrão:** rediscagem, variante B e espera do alô ficam desligadas até serem ligadas
por campanha ou variável. Migrações aditivas: `campaign_results.attempts`, `.variant`, `.rejected`; índice
`idx_transcripts_call`.

## v0.13.0 — 2026-10-15

**Lead da campanha mandou mensagem: o Hermes liga primeiro** — *pedido da dona: "liga de novo na hora; se não atender, aí responde"*
- Quando alguém de uma campanha em massa recente escreve no WhatsApp, o Hermes liga para a pessoa na hora, com
  o agente da campanha ("Oi, tudo bem? Vi sua mensagem e preferi te ligar rapidinho…"). Se atender, a conversa
  segue na voz e não sai texto. Se não atender, a IA responde a mensagem por texto, como antes.
- É uma ligação por contato a cada 12 h: as mensagens seguintes vão direto para o texto. Só liga dentro da
  janela de ligações da própria campanha (por exemplo, 7h–18h de segunda a sexta). Também não liga com a linha
  ocupada nem nos mesmos casos em que o retorno de ligação perdida não liga: "não ligar", lista de acesso,
  atendimento humano, IA pausada ou contato salvo na agenda. Nesses casos vai direto para o texto.
- A ligação não atendida não vira card, não entra no histórico e não vai para a repescagem (mesma marca do
  retorno de ligação perdida).

## v0.12.0 — 2026-10-14

**Atendente: opção "só campanha"** — *pedido da dona: no celular pessoal (8653), a IA só age com quem está na campanha*
- **Nova opção por conta, `campaign_only` (desligada por padrão; quem não ligar não muda nada).** Ligada, a IA só
  responde mensagem no privado, só retorna ligação perdida e só atende ligação de quem foi discado numa campanha
  em massa da conta que está rodando ou terminou há até 30 dias. Amigos, família, desconhecidos e números de testes
  antigos ficam sem nenhuma ação da IA. Grupos, os comandos da dona pelo Telegram e as mensagens do próprio número
  continuam como estão.
- Campanha em massa é a que tem mais de 1 número: ligação avulsa pela IA ou pelo Telegram, ligação agendada
  (promessa) e retorno de ligação perdida não contam, nem número que ainda está na fila. A pessoa é reconhecida pelo
  número da lista (com ou sem 55, com ou sem o 9) ou pelo número que o WhatsApp devolveu na ligação (inclusive
  quando ele esconde o telefone).
- É mais estreita que o "só ativo" (`outbound_only`), que vale para qualquer um que já recebeu ligação do Hermes,
  inclusive de testes e campanhas antigas. Se o banco falhar na hora de conferir, a IA não responde nem liga.
- Ainda sem botão no painel: liga pela API, mandando em `PUT /api/settings/agent-chat` o bloco `agent_chat` que o
  `GET /api/settings` devolve, com `"campaign_only": true`. Salvar a tela do painel não desliga a opção.
- Arquivos: `internal/settings/store.go`, `internal/whatsapp_campaigns/store.go` (`InRecentCampaignAny`),
  `cmd/server/autoreply.go`, `cmd/server/missed_callback.go`, `cmd/server/settingsapi.go`; testes em
  `cmd/server/so_campanha_test.go` e `cmd/server/agentchat_preserva_test.go`. Sem migração de banco (a opção vai
  no JSON do `agent_chat`).

**Retorno de ligação perdida herda o perfil da campanha**
- Quando alguém que foi discado numa campanha liga de volta e ninguém atende, o retorno automático agora usa o
  mesmo perfil/roteiro da campanha (não mais o prompt genérico fixo). O Hermes consulta a campanha mais recente
  que discou para aquele número e carrega o perfil de vendas configurado nela.
- Arquivos: `cmd/server/session.go` (`maybeCallback`), `internal/whatsapp_campaigns/store.go`
  (`RecentCampaignRequest`).

**Re-engajamento após silêncio do cliente**
- Se o cliente fica 8 segundos em silêncio após a IA falar, ela diz "Olá? Está me ouvindo?", uma vez por ligação.
  Antes o cliente ouvia a oferta inteira e ficava em silêncio até a chamada cair por inatividade (60s).
  O re-engajamento reseta o timer de inatividade.
- Arquivo: `cmd/server/broadcast.go` (`runConversation`).

**Correção: teste RetornoDeLigacao**
- `TestDB_SoCampanha_RetornoDeLigacao` falhava porque o mock de `server` não inicializava `DoNotCallStore`.
  `callbackBlockedReason` chama `srv.dnc.Has` sem nil-guard (panic). Agora o teste cria o store.
- Arquivo: `cmd/server/so_campanha_test.go`.

## v0.11.0 — 2026-10-14

**Campanhas** — *pedido da dona para a 1ª campanha de divulgação (48 por dia na linha 8653, no horário comercial)*
- **A campanha "ao longo do dia" espalha as ligações pelo horário.** Ela soltava uma ligação por minuto assim que a
  janela abria até bater o alvo do dia (48 ligações entre 9h e 9h50), uma rajada que é o que o WhatsApp lê como robô.
  Agora o que falta do dia é dividido pelo resto da janela: 48 das 9h às 18h dá uma a cada ~11 min, variando de
  70% a 110% do intervalo para não ficar fixo. "Por minuto" continua valendo como piso. Sem janela simples
  (0h–0h ou cruzando a meia-noite) o ritmo é o de antes.
- **Uma ligação por vez na linha.** A campanha não abre outra chamada enquanto a linha tem uma conversa em andamento
  (antes a próxima saía no horário mesmo com a anterior ainda falando); espera e tenta no minuto seguinte.
- **A campanha "ao longo do dia" toca a oferta.** Com agente de 2 áudios (isca + oferta), o cadenciador remontava a
  campanha só com a isca: a oferta não tocava, o som de fundo do agente sumia e a IA não sabia o que o cliente já
  tinha ouvido. Agora reusa a campanha montada na criação e, depois de um reinício do servidor, refaz isca, oferta
  (guardada na biblioteca de áudios ao criar), contexto e som de fundo do agente.
- **Só dias úteis (opcional).** `weekdays_only: true` na criação da campanha (`POST /api/sessions/{sid}/broadcast`,
  modos `paced`/`multiline`): sábado e domingo a campanha espera e volta segunda no início da janela. Sem a opção,
  tudo igual. Ainda não tem botão no painel.
- Arquivos: `cmd/server/campaign_scheduler.go`, `cmd/server/broadcast.go`; testes em
  `cmd/server/campaign_scheduler_test.go`. Sem migração de banco (a opção nova vai no `pace_config`, que já é JSON).

## v0.10.0 — 2026-10-08 (no ar desde 08/10/2026 15:48, build `20261008-1541_b0605a3`)

**Painel**
- **Conectar o WhatsApp sem ler o QR Code.** A tela de conexão da linha ganhou duas abas: "QR Code" (como era)
  e "Por código". Na segunda, você digita o número com DDI e DDD e o painel mostra um código de 8 dígitos para
  digitar no WhatsApp do aparelho (Aparelhos conectados › Conectar aparelho › Conectar com número de telefone).
  Serve para quem não tem câmera à mão ou está conectando de longe. O servidor já fazia isso desde antes
  (`POST /api/sessions/{sid}/pair-code`, usado pelo agente do Telegram); faltava a tela.
  Arquivos: `client/src/components/domain/session/SessionPairing.tsx`,
  `client/src/services/sessions.ts`. Sem mudança no backend e sem migração de banco.

> **Isto NÃO registra um número novo no WhatsApp.** O pareamento por código conecta o Hermes como aparelho
> secundário de uma conta que já existe. Criar conta do zero exige o aplicativo oficial num aparelho (ou celular
> virtual) e a pessoa digitando o número e o SMS — o WhatsApp bloqueia esse cadastro por automação de propósito,
> e o projeto não contorna isso (ver `whatsapp-activator/AVALIACAO.md`).

## v0.9.0 — 2026-10-07 (no ar desde 07/10/2026 14:33, build `20261007-1425_cdad439`)

Conferida em duas ligações de verdade pela bancada, com a dona: 06/10 17:46 ("pareceu melhor") e 07/10 14:15, já
com a bancada na VPS de teste ("parece que não picotou"; registro: qualidade boa, nenhum atraso no envio).

**Voz** — *visto na ligação de verdade de 05/10 11:38; falta uma ligação para confirmar*
- **Depois de interrompida, a IA não recomeça a resposta do começo.** Ela descartava da memória tudo o que já tinha
  dito naquela resposta, e na vez seguinte repetia (a dona ouviu o preço 3 vezes). Agora as frases que o cliente ouviu
  até o fim ficam na memória; a frase cortada no meio e as seguintes continuam de fora.
- **"Qualidade do áudio" não marca mais "com cortes" em ligação boa.** Contava como corte o silêncio do cliente (o
  celular para de mandar áudio quando a pessoa cala) e a passagem normal da fala da IA para o silêncio. Agora buraco
  recebido só pesa junto com perda de pacotes, e o limite do nosso envio foi de 200 para 400 ms. Os números
  continuam aparecendo iguais; mudou só o resultado ("boa" / "com cortes").

- **Fala e gravação picotadas** (ligação de 06/10 12:46: "picotando tanto a minha voz como a da IA"). A VPS da produção
  pausa o Hermes por 0,1 a 0,25 s várias vezes por segundo (é a máquina; as outras duas VPS não fazem isso). O Hermes não
  tolerava: (1) depois de cada pausa a fala inteira saía atrasada, e o celular ouvia um buraco; agora os pedaços
  atrasados saem em seguida e o ritmo é retomado; (2) um pedaço de silêncio entrava no meio da palavra; não entra mais;
  (3) a gravação punha cada pedaço na hora em que chegou (buraco + pedaços somados): agora cada voz é montada em
  sequência, sem buraco. *Falta uma ligação de verdade para ouvir. O engasgo da máquina continua: é com o provedor ou
  mudando de VPS.* Análise em `docs/ensaios/2026-10-06_1246_ligacao-picotada.md`.

- **1ª resposta da ligação mais rápida.** As conexões com a voz e a IA só eram abertas no aceite da ligação, e a 1ª
  resposta vem ~40 s depois (isca e oferta são áudio gravado): a conexão já tinha esfriado (3,3 s na 1ª resposta,
  ~2 s nas seguintes). Agora são reabertas quando o áudio gravado termina e no começo de cada fala do cliente, no
  máximo uma vez a cada 20 s. *A conferir na próxima ligação de verdade: `tts_ms` da 1ª resposta.*

**Achados da varredura de julho que ainda valiam** (`docs/archive/ACHADOS_JULHO_TRIAGEM_2026-10-05.md`)
- **Endereço de quem acessa não pode mais ser inventado.** Os limites por IP (cadastro, login, "esqueci a senha",
  demonstração) usavam o primeiro endereço do cabeçalho `X-Forwarded-For`, que o próprio cliente escreve. Agora só
  vale o que o proxy da máquina informa. (Risco real era baixo: o Traefik já descarta o cabeçalho de fora e a porta
  8080 é fechada; agora não depende disso.)
- **Apagar ou etiquetar contatos em massa sem selecionar nenhum** respondia "ok"; agora avisa. **Exportar contatos**
  ganhou teto de 5.000 por vez (cada contato é uma consulta ao banco).
- **Renomear/apagar etapa do funil e apagar agente que não existem** (ou são de outra conta) respondiam "ok"; agora
  respondem "não encontrado".
- **Agenda:** o relatório chamava de "No-show" o número de cancelados; agora diz "Cancelados". Salvar configuração da
  agenda aceitava corpo de qualquer tamanho; agora até 1 MB.
- **Limite diário de ligações da campanha** comparava o dia do banco com o dia do servidor; com fusos diferentes o
  contador zerava das 21h à meia-noite. Agora os dois lados usam o relógio do banco. (Na produção os fusos são
  iguais; o defeito aparecia no teste do PC depois das 21h.)
- **Tema:** o botão claro/escuro esquecia que a pessoa usava o escuro azul e voltava para o escuro preto.

**Laboratório Avançado: a "Criatividade" passou a valer** (último pedaço do achado F19)
- O controle abria sempre em 0,70, qualquer que fosse o agente, e o valor ia num lugar do pedido que o servidor
  descarta: mexer nele não mudava nada. Agora mostra o valor que o agente tem e grava onde o servidor lê (o mesmo
  lugar que "Meus Funcionários" e o assistente usam). Agente que nunca teve valor aparece como "padrão do modelo"
  e continua assim se a pessoa abrir e gravar sem mexer.
- Saiu o controle "Max Tokens (Saída)": não era gravado nem lido (o tamanho da resposta é fixo no servidor, curto
  na ligação por ser falado).
- Conferido na tela, numa cópia local com banco descartável (06/10): abrir, gravar sem mexer e gravar mexendo.

**Painel: um caminho só no primeiro acesso** (P2 do plano, 1ª parte)
- O tour de boas-vindas (8 telas) não abre mais sozinho por cima do cartão "Primeiros passos" (conectar o WhatsApp →
  escolher o agente → ligação de teste → plano). Quem quiser ver o tour abre pelo link "Ver o tour do painel" do
  cartão. Os assistentes de Configurações continuam onde estavam.

**Painel: saiu o que prometia e não existia** (P3 do plano)
- Configurações › IA: o cartão "Motor Enterprise & God Mode" virou "Controle de gasto da IA" e ficou só com o teto de
  gasto, que funciona. Saíram "Fallback em Cascata" e "Roteador Semântico" (só diziam "em desenvolvimento").
- Gestor: saiu o passo "Superpoderes" do assistente (13 chaves que o servidor nunca leu) e o cartão "Habilidades
  Avançadas (em breve)". O que já estava salvo não é apagado.
- Agentes: saiu a opção "Transferir ligação SIP (Celular Secundário)" (o servidor não conhece essa ação) e as
  sugestões de pergunta sobre ramais e provedor SIP.
- A página "Equipe" já não aparecia no menu. O passo "Colaboradores" do assistente de configurações fica: ele cria
  as contas de verdade.

**Aceite da ligação recebida** — *só bancada; sem `HERMES_ACEITE_VARIANTE` o aceite continua exatamente o de sempre*
- Três peças novas para testar o aceite (`HERMES_ACEITE_VARIANTE` agora vai de 0 a 63), tiradas da captura de um
  celular de verdade atendendo (05/10): 8 = manda `relaylatency` antes do aceite, 16 = aceite sem `<enc>`,
  32 = `medium="2"`. 57 (1+8+16+32) é o mais parecido com o celular. As variantes 1 a 7 não mudaram.

## v0.8.1 — 2026-10-05 (no ar desde 05/10/2026 11:53, build `20261005-1148_f28526a`)

Três itens que sobraram da lista da dona (item 4), feitos pelo PC depois que a v0.8.0 foi ao ar. Nada mexe na voz.
Testado com `go build/vet/test` (com Postgres), `tsc` e `vite build`.

- **Campanhas antigas sem dono** (F31): ao subir, cada campanha sem dono ganha o dono da linha
  dela (só preenche o vazio, nada é apagado; pode fazer campanhas antigas aparecerem na lista da conta dona). As que
  não têm dono identificável ficam como estão e só o admin da plataforma pode apagá-las (antes qualquer conta apagava).
- **Planilhas (CSV) iguais em todo o painel:** Listas, Dados coletados, Captação de leads e Contatos
  saem no mesmo formato (abre direto no Excel em português, telefone como texto, texto que começa com = + - @ não vira
  fórmula, aspas no nome não quebram a linha). O botão "Exportar CSV" das Transcrições, que não fazia nada, agora baixa
  as ligações da tela (ou as marcadas).
- **Token do bot do Telegram no Gestor Fácil:** a tela recebia o token inteiro do servidor; agora só o
  fim aparece ("***abcd"). Salvar sem mexer não troca o token, colar outro troca, apagar o campo apaga. O "Testar
  Telegram" continua funcionando com o token salvo.
- Ensaio IA × IA (`ops/vps/ensaio.sh`): o fim de uma ligação é reconhecido pela linha `entrega=` (a v0.8.0 mudou o
  registro e o ensaio recusava rodar achando que havia ligação em andamento). Já instalado na VPS.

## v0.8.0 (segunda parte) — trabalho de 04 e 05/10, no ar desde 05/10 11:05 junto com a v0.8.0

Feito na nuvem, no ramo `claude/gallant-mendel-f1xney` (em cima de `pc/v0.8.0`). Divisão do trabalho em
`docs/DIVISAO_TRABALHO_PC_ONLINE.md`; o que o PC precisa testar está em `docs/PEDIDOS_AO_PC.md`. Tudo com
`go build/vet/test` (com Postgres) e o simulador de ligação.

**Aceite da ligação (A1, A2)** — *só bancada; nada muda na produção sem as chaves*
- `HERMES_VOICE_ESPERA_ACEITE=false` (IA ouve desde o começo) e `HERMES_TESTE_ACEITE_POR_RELAY=true` (na ligação
  que o Hermes faz, ~1 s de áudio do relay sem accept = aceita) para o ensaio IA × IA.
- `HERMES_ACEITE_VARIANTE=0..7`: formatos do accept da ligação recebida para testar na bancada (tabela em
  `docs/REGRESSOES_LIGACAO.md` §5). 0/vazio = o aceite de sempre.
- `/saude-local` lista as chaves só-bancada ligadas em `chaves_de_teste` (a publicação pode recusar a produção).

**Segurança entre contas (auditoria do mês 2)**
- **Ligações só para a conta dona da linha** (F01/F07/F10): o canal de eventos do painel mandava as ligações
  ativas de todas as contas; encerrar com o id de outra conta mexia na ligação dela. Os avisos de ligação
  recebida voltam a chegar ao dono certo (o popup abre).
- **Catálogo** (F02): remover imagem não apaga mais arquivo fora da pasta de uploads nem a foto de outra conta.
- **Motores globais só da dona** (F03/F05): salvar "Voz e Transcrição", "IA Padrão", "IA da ligação" ou o
  assistente fácil numa conta comum não troca mais a transcrição, o resumo das gravações, as travas de envio nem
  a IA de TODAS as contas; cada conta salva só para si. Só a conta da dona (admin do sistema) remonta o global.
  A IA da ligação salva vale na hora (antes esperava até 5 min de cache).
- **Chaves ElevenLabs da plataforma só para a dona** (F04): outra conta usa só as chaves do próprio cofre (antes
  gastava o crédito da dona e as chaves iam para o endereço que a conta escolhesse). Conta com ElevenLabs e sem
  chave nenhuma passa para a voz grátis (edge-tts) em vez de ficar muda. **Atenção na publicação:** outra conta
  da dona que use ElevenLabs sem chave própria muda para edge-tts — ponha uma chave no cofre dela ou o e-mail
  dela em `HERMES_PLATFORM_ADMINS`.

**Defeitos corrigidos (auditoria do mês 2)**
- **Criar agente com nome repetido não apaga mais o agente** (F06): "+ Novo agente" no Treinador, o Funcionário
  Fácil/Lab sem id e o "cria o agente X" do Telegram regravavam o agente de mesmo nome só com nome e prompt
  (sumiam roteiro, base, voz e os 2 áudios). Agora o painel recusa com "já existe um agente com esse nome" (409)
  e o Treinador seleciona o existente; pelo chat muda só o que foi pedido. O id devolvido ao salvar é o real.

- **Follow-up só na campanha da própria conta** (F08): pela API dava para pôr etapa ou inscrever contato na campanha
  de follow-up de outra conta sabendo o id dela. Agora responde 404, e o disparo ignora etapas e contatos que não
  são do dono da campanha.

- **Resposta do Chatwoot volta a chegar no WhatsApp** (F09): o webhook Chatwoot → WhatsApp respondia 404 sempre
  (pedia um login que o Chatwoot não manda), então a resposta do atendente nunca saía. Agora cada linha tem um
  token secreto no endereço do webhook. **Na publicação:** quem usa Chatwoot precisa abrir a config do Chatwoot da
  linha, salvar de novo e colar o endereço novo (com `?token=`) na inbox do Chatwoot.

- **Meu Perfil volta a salvar** (F11/F17): as preferências e o cargo eram gravados como texto e voltavam ao padrão;
  do segundo salvamento em diante aparecia "Falha ao salvar" (e não dava mais para trocar o nome da empresa, que a
  recepcionista usa). "Salvar preferências" também podia apagar a foto. O servidor agora troca só o que veio e
  conserta na leitura os perfis já gravados errado.

- **Gestor Fácil não desliga mais o aviso no Telegram nem o OpenClaw** (F12): o assistente salvava o bloco do
  agente sem esses campos e o servidor gravava "desligado". Agora o que não vem fica como estava, e o interruptor
  "Notificar no Telegram" do assistente passa a valer de verdade.

- **Configura Fácil aplica as chaves escolhidas** (F13): as chaves do passo 1 iam para o cofre, mas as
  configurações recebiam um id inventado pelo navegador — a IA, a transcrição e a voz ficavam sem chave e a tela
  dizia "configurado com sucesso". Agora o servidor usa o id real, chave reserva do mesmo provedor não apaga a
  principal, a opção grátis vira de fato whisper local/edge-tts, e a tela mostra erro ou aviso quando algo não
  foi aplicado.

**Gravação da ligação no Telegram** (relato da dona de 04/10: "na recebida e no retorno não chega")
- O áudio da ligação vai para o Telegram **mesmo quando a transcrição falha ou vem vazia** (legenda "sem
  transcrição"). Antes o envio só acontecia depois de uma transcrição com texto, e falhava calado.
- Cada ponto em que a entrega parava sem aviso agora deixa registro no log (gravação descartada por falta de áudio,
  linha sem dono, conta sem bot do Telegram, transcrição indisponível).
- Legenda cortada por caractere (antes por byte: podia partir um acento e o Telegram recusava o envio).
- A aba Gravações mostra a direção certa (recebida/feita).
- **Limite conhecido:** a ligação recebida só vai gravar quando o aceite do Hermes funcionar (A2/A3 com o PC);
  hoje ela só toca, e quem conversa é o retorno automático.
- *(05/10, PC)* **Uma linha no registro por ligação** dizendo onde a entrega parou, com o `call_id`
  (`entrega=sem_gravacao | nao_atendida | sem_audio | encode_falhou | sem_dono | sem_telegram | telegram_falhou |
  entregue`) e o que faltou no caminho (registro, transcrição, resumo, chats do Telegram). Ligação não atendida
  registra "sem gravação: ligação não atendida" — não é perda (no período do relato os retornos não foram atendidos).
- *(05/10, PC)* Ligação não atendida não gera mais MP3 (um áudio solto durante o toque podia virar uma "gravação"
  de silêncio no Telegram). A legenda diz quando o resumo falhou e por quê (transcrição com erro, nenhuma fala
  reconhecida, transcrição não configurada, IA sem resposta).

- **Editar agente no Funcionário Fácil não zera mais as configurações avançadas** (F15): a tela lia o extras salvo
  como objeto, mas ele vinha como texto; gatilhos de ligação, número do gerente, desconto, temperatura, motor
  reserva etc. voltavam ao padrão a cada edição. Agora a tela lê o que está gravado e o servidor junta as chaves.

- **Ligação em massa: uma por conta** (F18): o disparo pela tela "Ligação em massa" tinha uma vaga só para o servidor;
  enquanto uma conta disparava (podia levar horas), as outras recebiam "já existe um disparo". Agora cada conta tem o
  seu, e dois cliques seguidos não criam dois disparos.

- **Testes e geração de voz com a chave do cofre** (F20/F21): o "Testar voz" de Voz e Transcrição e o "Gerar áudio
  por IA" da Ligação em massa ignoravam a chave guardada no cofre (só funcionavam com a chave digitada).
- **Teste de transcrição de verdade** (F22): o Configura Fácil testava a chave de transcrição no teste de chat (nunca
  passava) e o teste não mandava o modelo (o Groq recusava com chave boa).
- **Desligar o som ambiente fica desligado** (F23): ao recarregar, o som "escritório" voltava sozinho.

- **Notas do vendedor ficam** (F24): cada ligação de campanha trocava as "Notas do Vendedor" do contato pelo resumo.
  Agora a nota escrita no painel é mantida (sem nota, o resumo da ligação continua aparecendo).
- **Chave "Responder só quem eu já liguei" não desfaz o Roteamento** (F25) e **"Testar Telegram" do Gestor Fácil não
  revoga os outros chats** (F26: o chat testado é acrescentado à lista).
- **Salvar o Chatwoot não desliga grupos, canais, assinatura, sempre online e leitura automática** (F28). Pela API,
  para desligar uma opção agora é preciso mandar o campo com false.
- *(05/10, PC)* **Etiqueta só da própria conta** (F30): aplicar etiqueta (uma a uma ou em lote) aceitava o id de uma
  etiqueta de outra conta, e a ficha do contato mostrava o nome e a cor dela. Agora responde 404 e não grava; a ficha
  só mostra etiquetas da conta.
- *(05/10, PC)* **Configura Fácil não apaga mais o som ambiente de um agente** (F34): concluir o assistente sem ligar
  "Adicionar som ambiente" zerava o som do agente mais antigo da conta. Agora som desligado não mexe em nada, e o som,
  as tags e os alertas do assistente vão só para o agente escolhido ("Quem faz as ligações que você pede", ou o único
  agente da conta). Com vários agentes e nenhum escolhido, a tela avisa e nenhum agente é alterado.
- *(05/10, PC)* **Funil: "Mover para..." e "Disparo em Massa" da seleção funcionam** (F32): os dois botões da barra
  "N leads selecionados" não faziam nada. "Mover para..." abre a lista de etapas e move os marcados pela mesma rota do
  arrastar (com os mesmos avisos e a pausa da IA em "Atendimento Humano"); "Disparo em Massa" leva os marcados para a
  Ligação em massa ou a Mensagem em massa, onde a dona confere e dispara (nada é disparado direto do funil).
- *(05/10, PC)* **Contatos: a ficha não inventa mais histórico** (F33): sem interações registradas, a ficha mostrava
  dois eventos de exemplo ("atendeu e demonstrou interesse", "não atendeu") como se fossem reais — também enquanto
  carregava ou quando a busca falhava. Agora mostra "Nenhuma interação registrada ainda" (ou carregando/erro), e o
  "Score de Lead" mostra "—" quando não há nota (antes mostrava o número de ligações).
- *(05/10, PC)* **Reforço F29:** ver ou pausar/retomar uma campanha criada sem dono (pela IA, Telegram, cron ou
  transbordo) agora exige ser a conta dona da linha da campanha.

**Revisão do PC**
- Planilhas (CSV) do painel e de contatos: célula que começa com = + - @ ganha apóstrofo (o Excel não executa
  fórmula vinda de lead) e o telefone "+55…" aparece como texto.
- `internal/testpg` recusa banco sem "test" no nome; a tela "Configuração do servidor" esconde usuário e senha
  dentro de URLs; o teste do catálogo de variáveis aceita fim de linha do Windows; CI com permissões mínimas e
  govulncheck em versão fixa.

## v0.8.0 — 2026-10-04 (no ar desde 05/10/2026 11:05, build `20261005-1058_b9bf587`)

Plano do mês (`docs/PLANO_MES_OUTUBRO_2026.md`), feito pela nuvem em 04/10. Tudo testado com `go test`
(inclusive com Postgres e detector de corrida), `vite build` e `tsc`; as telas novas foram abertas num navegador
(computador, celular e modo escuro). **O que ainda não foi testado numa ligação de verdade está marcado.**
Na publicação: o branch `claude/gallant-mendel-f1xney` avança a `main` sem conflito (fast-forward).

**Ligação (voz)** — *falta ligação real (PC + dona) para dar como pronto, regra de `docs/REGRESSOES_LIGACAO.md`*
- **A IA só ouve depois que a ligação é aceita** (L2): som que chega antes do aceite (bancada, eco do toque) não
  vira mais "fala do cliente".
- **Qualidade do som por ligação** (L3): ao fim de cada ligação, o registro `qualidade do áudio da ligação` diz perda,
  pacotes fora de ordem, buracos e jitter nos dois sentidos, com um veredito ("boa", "com cortes", "sem áudio").
  Como ler: `docs/COMO_DEBUGAR.md`, cenário 5.
- **Registro da sinalização** (L4, parte 1): as mensagens trocadas com o WhatsApp em cada ligação vão para o log (até
  40, sem chaves), para descobrir o formato certo do aceite da ligação recebida. Passo a passo: REGRESSOES §5.
  `HERMES_CALL_TRACE=false` desliga.
- **Resposta mais rápida** (L6): a transcrição começa na micro-pausa do cliente e as conexões de transcrição e voz são
  aquecidas quando a ligação é aceita. No simulador: 1,73 s → 1,23 s. `HERMES_VOICE_STT_ANTECIPADO=false` e
  `HERMES_VOICE_AQUECER=false` desligam.
- **Recepcionista padrão** (L8): ligação recebida sem agente escolhido não é mais atendida pelo assistente da dona
  ("posso disparar campanhas"), e sim por uma recepcionista com o nome, o ramo e o endereço do perfil do negócio.
- **Memória entre ligações** (L10): ligou de novo para o mesmo número (até 90 dias), a IA sabe o resumo da última
  conversa. `HERMES_VOICE_MEMORIA=false` desliga.
- **Marcar horário na ligação** (L11): "pode ser terça às 10?" vira compromisso PENDENTE na Agenda (a dona confirma)
  e aviso no Telegram; horário ocupado, passado ou longe demais a IA pede outro. `HERMES_VOICE_AGENDAR=false` desliga.
- **Lead quente** (L12): aviso de lead quente ligado por padrão (só avisa) e botão "Entrar na ligação" no painel.
- **Simulador de ligação** (L5): `go test ./internal/voice/ -run Simulador` roda o agente de voz inteiro com uma linha
  falsa (8 cenários: nada antes do aceite, oferta cortada pela fala, tempo de resposta, interromper, eco, frase
  interna, transcrição antecipada, pausa no meio da frase). Roda no CI.

**Painel**
- **Saúde das ligações** (Configurações, só a dona da plataforma): cada ligação guarda a qualidade do som e o tempo de
  cada resposta da IA (meta: 2,5 s). Tabela nova `call_health` (aditiva, 90 dias).
- **Configuração do servidor** (Configurações, só a dona da plataforma): todas as variáveis de ambiente, se estão
  definidas e o valor (segredos só como "definido"), e aviso de nome digitado errado. Catálogo `.env.example`.
- **Proteção das linhas** (Campanhas): por linha, dia de uso, teto de hoje (o aquecimento sobe 20 → 40 → 80 → 150 →
  300 ligações por dia), ligações dos últimos 7 dias, campanha rodando com falhas seguidas e os acontecimentos
  (parada por risco, teto atingido, bloqueio, desconexão). Tabela nova `line_risk_events` (aditiva).
- **Aviso de retorno de campanha**: quem recebeu ligação de campanha (30 dias) e manda mensagem no WhatsApp gera
  aviso no Telegram na hora (1 por contato a cada 6 h). O botão "Modo Retorno de Campanha" prometia "a IA liga na
  hora" e não fazia nada; virou este aviso (ligar sozinho contraria a regra da dona).
- **Exportar interessados**: dentro de uma campanha, o botão exporta os contatos da tabela com o filtro da tela (antes
  baixava o resumo de todas as campanhas). CSV que abre direto no Excel em português.

**Defeitos corrigidos**
- **Salvar uma tela apagava configurações**: a leitura das configurações não trazia as credenciais escolhidas no
  cofre (IA, IA da ligação, transcrição e voz), o "interromper a IA" e o "só responde quem já recebeu ligação"; ao
  salvar, voltavam vazios. Agora a leitura traz tudo (teste trava se faltar) e o servidor só troca o que veio.
- Teste do agente: clicar em enviar mandava o clique como texto. Assistente do Gestor: lista de chaves sempre vazia.
  Agentes especializados: temperatura, webhook e outros campos não salvavam. Assistente de criação: duas seções
  nunca apareciam. Foto do contato ignorada no chat. Avisos no modo escuro.
- **Segurança (4 vazamentos entre contas)**: a lista de diagnósticos e as chaves da ElevenLabs (da plataforma
  inteira) abriam para qualquer conta; o andamento/cancelamento de envio em massa e o "resolver conversa" do Chatwoot
  aceitavam o id de outra conta. Agora os dois primeiros são só da dona da plataforma e os outros conferem o dono.
- Chave primária das tabelas `settings` e `ai_cost` conferida no banco inteiro (fazia o CI falhar de vez em quando).
- Bibliotecas: `golang-jwt` 5.2.1 → 5.2.2 (um token enorme fazia o login gastar memória demais) e `x/text` 0.38 → 0.39
  (laço infinito com texto inválido). As outras 7 falhas que o govulncheck aponta são da biblioteca padrão do Go e
  somem com o Go 1.26.6 na VPS (tarefa do PC, ver `CONTINUAR_DAQUI.md`).

**Publicação e qualidade**
- `ops/publicar.sh` confere, depois de trocar a versão, que as linhas do WhatsApp voltaram a conectar e que não houve
  pânico no registro (senão volta sozinho), e acerta a bancada para a versão nova. Rota `/saude-local` (só de dentro
  da VPS).
- CI: detector de corrida, testes com Postgres de verdade, `tsc` sem erros e travando, aviso de falhas conhecidas nas
  bibliotecas (govulncheck/npm audit). Catálogo `.env.example` com teste.

**Atenção na publicação:** tabelas novas `call_health` e `line_risk_events` (criadas sozinhas, aditivas). Nenhuma
variável nova é obrigatória (todas as novas vêm ligadas por padrão).

## v0.7.0 — 2026-10-03 (no ar desde 03/10 21:39)

Plano da dona pros motores de IA (ligação no Groq, reserva no OpenRouter, várias contas):
- **Rodízio de chaves (pool):** todas as chaves do cofre pro mesmo serviço (mesmo endereço, ou mesmo
  provedor) são usadas em rodízio. Chave recusada (limite, sem crédito, inválida) descansa e a próxima é
  tentada na hora, antes de o cliente ouvir qualquer coisa. Vale pra Groq, OpenRouter e qualquer proxy.
  Só entram chaves do cofre da própria conta. **Gemini fica fora do rodízio** (as chaves extras do cofre são
  grátis/antigas). Chave inválida respondida com 400 (Google) também conta como recusada.
- **Reserva da ligação no OpenRouter com o MESMO modelo:** com a ligação no Groq (`qwen/qwen3.8-27b`),
  se o Groq falhar/travar o reserva é o mesmo qwen3.8 pelo OpenRouter (pedindo o provedor mais rápido).
  Basta ter chave do OpenRouter no cofre. Reserva de perfil igual ao principal (o antigo groq/llama) é
  ignorado. Desliga com `HERMES_CALL_OPENROUTER_RESERVE=false`.
- **Cofre de credenciais:** opção "OpenRouter (várias contas em rodízio)" (endereço preenchido sozinho) e
  modo **"Várias de uma vez"** (uma chave por linha, cada uma testada antes de salvar; as recusadas ficam
  na caixa). Corrigido: o "Testar e Salvar" recusava toda chave Groq/OpenAI/proxy ("informe um modelo");
  a chave do OpenRouter é conferida sem gastar crédito.
- **Regra geral da ligação — linguagem simples:** só português do Brasil, sem termos técnicos (RAG, API,
  instância…), despedida educada. Achado da bateria do Laboratório (o qwen3.8 leu "RAG básica" pra um cliente
  apressado, escapou "voy" e se despediu com "Perdeu").
- **Rede / VPS (Configurações, só a dona da plataforma):** botão pra dividir as chamadas do Groq (IA e
  transcrição) com a VPS 53 — uma direta, a seguinte pela VPS; VPS fora → direto na hora (espera máx. 1,5 s,
  depois descansa). E, como reserva contra bloqueio de IP, a conexão do WhatsApp de cada linha pela outra VPS (a
  ligação em si continua direta). Precisa do proxy na VPS 53 (`ops/vps/rede-vps53-squid.sh`, a dona roda) e de
  `HERMES_GROQ_VPS_PROXY` / `HERMES_WHATSAPP_VPS_PROXY` na produção.
- **Transcrição:** o eco do texto de contexto do Whisper em silêncio ("Ligação comercial em português do Brasil.")
  é descartado — antes a IA respondia a isso.
- **Interromper a oferta gravada voltou a funcionar:** pra cortar a oferta exigia 420 ms de voz em frames
  SEGUIDOS; a pausa natural entre sílabas zerava a conta e a oferta (27 s) não parava ("falei e ela não parou",
  ligação da dona de 03/10). Agora conta voz dentro de uma janela (7 de 10 frames). Log novo quando um áudio gravado
  NÃO é cortado mesmo com voz por cima.
- **Regressões documentadas:** `docs/REGRESSOES_LIGACAO.md` (sintoma → causa → correção → teste que protege) e
  regra no `CLAUDE.md` pra qualquer agente que mexer na voz. Testes novos: oferta com pausas entre sílabas,
  dois áudios não intercalam (voz picotada).
- **Codec de áudio (MLow) não derruba mais o servidor:** a biblioteca nativa estava compilada com
  `OPUS_HARDENING=ON`, e um pacote de áudio inesperado ABORTAVA o processo inteiro (todas as ligações caíam).
  Aconteceu na produção em 25/09 e na bancada em 03/10. Recompilada sem a trava e instalada em `/usr/local/lib`
  (a antiga guardada em `/opt/hermes-call/codec-backup/`). Teste com 200 mil pacotes aleatórios.
- **"Atender chamadas com agente de voz IA":** descoberto que NUNCA mandava o aceite (só registrava). O aceite
  real foi feito (depois de ~6 s de toque, com as proteções do retorno automático) e testado, mas o WhatsApp não
  reconhece o aceite enviado pelo Hermes: o áudio passa, porém quem liga continua vendo "chamando". Por isso fica
  desligado (`HERMES_AUTO_ANSWER_ACEITAR=true` só pra teste) e vale o retorno automático, como antes.
  Pendente: corrigir o formato do aceite.
- **Voz:** "+" solto entre palavras é falado "mais" ("Pro + IA" era ouvido "PROBI e IA").
- **Laboratório (pronúncia):** a transcrição passa pela mesma conversão de fala antes de comparar (algarismos
  e grafia normal — "R$ 199,00", "WhatsApp" — não contam mais como erro de pronúncia).
- **Segurança:** disparo de ligações em massa, mensagens em massa e campanha por etapa do CRM aceitavam o id
  da linha de OUTRA conta (discava/mandava pela linha alheia). Agora só a linha da própria conta.
- **Publicação:** a limpeza de versões antigas nunca apaga mais a versão ANTERIOR (destino do "voltar").
- **Endereço com `/v1`** (o formato que a tela pede) não vira mais `.../v1/v1/chat/completions`.
- **Proxy de saída (Webshare) pros pedidos SEM pressa:** atendimento por texto, assistente, análises e testes
  do Laboratório saem por proxy (cofre: "Proxy Webshare", ordem = prioridade; plano acabou ou caiu → o próximo
  assume; nenhum → direto). A **ligação continua direta** (medido: outra VPS no caminho soma 0,1–0,5 s por fala)
  e o **Gemini fica de fora**. Também aceita `HERMES_PROXY_URLS`; desliga com `HERMES_PROXY_LLM=false`.

## v0.6.2 — 2026-10-03 (canal: estável)

Achados do novo **Laboratório de Ligações** (IA vendedora × IA cliente em texto, com juiz):
- **Regras gerais da ligação** (todos os agentes): não inventa desconto/condição; não promete mandar link
  ou mensagem durante a ligação; não inventa de onde veio o contato; pedido de "me tira da lista"/"não me
  liga mais" encerra com educação, sem insistir; pergunta que ficou sem resposta é respondida primeiro.
- **Lista "não ligar" de verdade:** o pedido feito na ligação bloqueia o número pras campanhas, retornos
  automáticos e promessas, e a dona é avisada no Telegram (ligação pedida por ela ainda sai, com aviso).
- **Motor reserva da ligação voltou a funcionar:** o Groq aposentou a linha Llama (o reserva
  `llama3-8b-8192` respondia "decommissioned"); modelos aposentados vão pro `qwen/qwen3.8-27b` (0,3 s).
- **Laboratório de Ligações** no painel (teste do agente › "📞 Laboratório de ligação"): conversa completa
  com cliente simulado (curioso, preço, desconfiado, apressado, sem interesse, quem liga), mesmo prompt/
  modelo/regras da ligação, nota do juiz, tempo até a 1ª frase, comparação de modelos/chaves e teste de
  pronúncia (voz real → transcrição). Ações simuladas; nada é enviado.

## v0.6.1 — 2026-10-03 (canal: estável)

Ajustes da ligação de teste da dona (03/10, logo depois da v0.6.0):
- **Interromper a IA voltou a funcionar** (na oferta gravada e nas respostas): a proteção contra eco
  exigia que a voz do cliente chegasse 2× mais alta que a própria voz da IA — impossível num celular.
  Agora ela mede o eco real de cada ligação e se ajusta (eco baixo = basta falar; viva-voz com eco
  forte continua protegido). A sensibilidade do painel continua valendo.
- **Preço falado direito:** valores em reais vão por extenso pra voz ("R$ 99/mês" → "noventa e nove
  reais por mês"; "R$ 1.497,00" → "mil quatrocentos e noventa e sete reais"), sem quebrar no ponto.
- **Voz igual à da v0.5.0:** volta o áudio do ElevenLabs em MP3 44 kHz (o PCM direto fica opcional,
  `HERMES_ELEVEN_PCM=true`) e o som de fundo não abaixa mais sob a voz (opcional,
  `HERMES_VOICE_AMBIENT_DUCK_DB=8`).

## v0.6.0 — 2026-10-03 (canal: estável)

Leva de correções da análise de 02/10 (`docs/ANALISE_MELHORIAS_2026-10-02.md`), feita em 5 frentes
revisadas de forma independente (`docs/PASSAGEM_LEVA_v060_2026-10-02.md`).

### 📞 Ligação mais natural e certa
- Ligação pedida pelo Telegram/painel segue o roteiro do agente e sabe o que a isca e a oferta disseram.
- A IA diz o preço na 1ª frase (tabela oficial de planos) e responde em no máximo 2 frases curtas.
- O cliente pode interromper a oferta gravada; o que ele fala ao cortar a IA não se perde.
- A resposta ao "alô" é ouvida: se perguntar "quem fala?" ou recusar, a IA responde na hora.
- Frases sem buracos entre elas; a linha nunca fica muda enquanto a IA pensa; fim da fala detectado mais cedo.
- Se a IA falhar, entra um motor reserva; nunca é falado erro técnico ao cliente.
- Na ligação, quem está do outro lado não consegue mandar a IA executar ações (só chamar humano,
  perguntar ao dono ou transferir). Treino, catálogo e simulações também não executam ações.
- "Interessado" depende da análise da IA (não basta um "sim"); a resposta ao "alô" não conta;
  a duração gravada é a real; a ligação cai na hora no limite de 2 min.
- ElevenLabs gasta menos (palavras de apoio em cache, geradas só depois de atender) e responde mais rápido;
  o som de fundo abaixa sob a voz e não reinicia no meio.
- Base de conhecimento e catálogo valem também durante a ligação; nova base "global" para todos os agentes.
- Editar o agente "Vendas Hermes Call" não é mais desfeito ao reiniciar.

### 🔁 Retornos, agendamentos e Telegram
- Retorno automático de ligação perdida liga para o telefone real (antes falhava sempre), só quando ninguém
  atendeu — não liga se você atendeu ou recusou no celular — e respeita bloqueios e contatos pessoais.
- Telegram: não escolhe o agente errado nem liga por mensagens curtas, negativas ou perguntas; bot privado
  (só chats autorizados); novo `/agentepadrao`.
- Pedidos de retorno detectados nas conversas esperam sua confirmação no Telegram e entendem o horário pedido;
  conversa pessoal não vira ligação.
- Ligações agendadas mostram o resultado, tentam de novo sozinhas e não travam a fila; "tocou mas não atendeu" correto.
- Horário comercial no fuso de Brasília. Aviso no Telegram quando a linha do WhatsApp cai ou é bloqueada.
- Ligação recebida usa o agente de voz escolhido no painel.
- **Nada disca sem pedido claro (revisão de 03/10):** "liga pra ele não", "liga amanhã", "ele liga depois",
  "chama no zap" não ligam; número tirado do histórico ("liga pra ele") sempre pergunta com o número na
  tela; "de novo"/"repete" soltos pedem confirmação; "sim" para ligar só em resposta curta; "sim" a uma
  confirmação de envio nunca vira ligação; ligação proposta pela IA com número que não estava na sua
  mensagem pede confirmação.
- Retorno automático: não liga para contatos salvos na agenda do celular (só leads e números
  desconhecidos), nem com a IA pausada ou em atendimento humano; aviso com botão **"Cancelar retorno"**
  e 45 s de espera.
- Ligação agendada que passa do prazo (8 min) é cancelada de verdade (não disca depois); promessa
  detectada só disca confirmada; erro numa ligação não derruba o servidor.
- Relógio do servidor adiantado não faz mais ignorar as ligações recebidas (a fila offline é reconhecida
  pelo aviso do WhatsApp).
- Telegram: novo `/acessos` para ver e revogar quem fala com o bot; chat que sai da configuração perde o acesso.
- Chat: cliente que pede atendente volta a ser atendido; contato externo não consegue ler dados internos
  pela IA; pausa da IA vale também quando o cliente escreve pelo WhatsApp Web; contato apagado do CRM
  que volta reaparece no kanban.
- **Atenção:** comandos pelo WhatsApp do seu número PESSOAL agora exigem cadastrá-lo com `/addadmin`.

### 🔒 Segurança
- Tela Logs só para a administração; senhas, tokens e chaves aparecem escondidos nos registros.
- "Esqueci a senha" com código pelo WhatsApp; verificação em duas etapas de verdade no login.
- Sair e "Encerrar sessões" desconectam na hora; proteção contra tentativas de senha e cadastros em massa
  (sem permitir que alguém tranque a conta de outra pessoa).
- Cabeçalhos de segurança no navegador; a pasta de imagens não lista mais os arquivos.
- Segredos tirados dos documentos do repositório (o histórico do git ainda os contém).

### 💳 Cobrança
- Trocar de plano (vale quando o pagamento confirmar; redução no próximo ciclo) e cancelar pelo painel.
- CPF/CNPJ validado no plano pago (inclusive CNPJ com letras); cupom estende o teste; o cupom fixo deixou de existir.
- Confirmação de pagamento do Asaas só com token; brechas de tolerância e de "equipe" grátis fechadas.
- Plano Start passa a abrir a tela de agentes.

### 🖥️ Painel
- Primeiro carregamento ~5× menor; pagamento em nova aba com conferência automática; cartão "Primeiros passos".
- Removidos números, nomes e documentos de exemplo que pareciam reais; o que ainda não funciona aparece como "em breve".

### 🛠️ Operação
- Backup diário de todos os bancos + gravações/uploads (incremental), alertas de queda e de disco (`ops/vps/`).
- Gravações fora da pasta temporária; `/api/version` mostra o canal "producao"; publicação roda `go vet` e envia a tag ao GitHub.
- CI destravado (testes antigos fora do build) e raiz do repositório organizada (`docs/archive/`).

## v0.5.0 — 2026-09-24 (canal: estável)

Tudo da v0.4.0 (que não chegou a ir ao ar) mais a revisão completa dos relatórios de bugs
(ver `docs/PENDENCIAS_BUGS.md`).

### 🔒 Segurança
- Servidor recusa iniciar sem `HERMES_JWT_SECRET` (a produção rodava com o segredo padrão
  público; o segredo foi definido na VPS em 24/09).
- Apagar/deslogar/parear linha e entrar em ligação (ponte) conferem o dono (antes qualquer
  usuário com o id alheio conseguia).
- Lista de IPs permitidos passa a ser aplicada por conta (antes era só enfeite e salvar apagava a lista).
- Conta desativada não entra mais (o campo existia mas não era conferido).
- Vitrine pública não vaza erro do banco; agenda escapa chave e valida status.
- Porta 8080 fechada na internet (só o Traefik/HTTPS chega no servidor).

### 💳 Cobrança
- Cadastro nasce em teste; plano pago gera a assinatura e leva ao pagamento.
- Pagamento confirmado aplica o plano. Assinatura pendente segura o teste por 5 dias.
- Cobrança vencida há mais de 5 dias bloqueia (tela para pagar dentro do app).
- A tela de teste vencido passa a permitir assinar (antes apontava para um domínio fora do ar).
- Plano "basic" antigo recebe os recursos do Start.

### 🐛 Correções
- Reinício não apaga mais o banco de linhas desconectadas: agora arquiva.
- Correções de 02/ago recuperadas: Funil por Origem, Mensagem em Massa, "Enviar pra
  Disparos", atalho Voz & Whisper.
- Garimpo: "Sincronizar" (rota não existia) e "Marcar como lido" (não salvava).
- Bloqueio com prazo (7/30 dias) funciona; desbloquear pede confirmação.
- Agenda: edição confere conflito/bloqueio; calendário mensal real; Dossiê IA.
- Números presos em campanha encerrada são fechados (286 na produção).
- "Interessado" alinhado com a classificação da IA.
- Duplicar agente copia tudo com nome único; Roteamento Nível 1 de mensagens funciona.
- Canal de eventos do painel reconecta sozinho.
- Anti-ban: no mínimo 20s entre ligações acima do teto diário em campanha sem intervalo.

### 🧹 Honestidade do painel
- Copiloto não mostra sugestões fixas; Visão Geral sem curva inventada; link público da
  agenda e histórico de versões marcados "em breve"; logo não troca mais o papel.
- "Esqueci minha senha" leva ao suporte no WhatsApp.

## v0.4.0 — 2026-09-24 (canal: estável)

Primeira versão publicada pelo `ops/publicar.sh` (com volta fácil). Parte da produção
TOC-fix de 26/ago e junta as correções de agosto que estavam num ramo paralelo.

### 🐛 Correções
- **Ligações agendadas (Promessas) falhavam 100%** desde jul/2026: o cron usava edge-tts
  com o ID de voz da ElevenLabs das settings globais ("Invalid voice"). Agora usa a mesma
  voz/motor da conversa ao vivo do dono. Mesmo defeito corrigido no **retorno automático
  de ligação perdida**. O edge-tts passa a cair na voz padrão se receber uma voz inválida.
- **Promessas criadas por engano**: qualquer mensagem com "quando/próximo/horário" virava
  ligação agendada, inclusive com ID interno do WhatsApp (LID) no lugar do telefone. Agora
  só cria se o cliente pedir retorno por telefone ("me liga", "pode me ligar"…), só com
  telefone real, e o cron recusa discar pra contato sem telefone válido.
- Assistente do Gestor: ícone `RotateCcw` não importado quebrava o passo de modelos.
- Histórico do WhatsApp (HistorySync) não era importado: a função existia mas não era chamada.
- Credencial escolhida no assistente do Gestor/Atendente agora é usada de fato; se falhar,
  libera os fallbacks (causa de "ligação muda").
- Radar Ao Vivo mostra ligações disparadas por campanha/Telegram.
- Total de campanhas agrupadas exibido certo (retroativo).

### ✨ Melhorias (trazidas do ramo de 02/ago)
- Áudio da gravação vai pro Telegram junto da transcrição; "Carregando…" em Gravações.
- Entrada manual de números em Disparo de ligação/mensagem; atalho Promessas na Agenda.
- Captação de leads persiste após recarregar, botão Limpar, leva pra Listas ao exportar.
- Otimizar prompt mostra a explicação da IA do que mudou.
- Laboratório Avançado: credencial própria do fallback; campos avançados reidratam no reload.
- CRM: agrupar por origem; Chat/garimpo agregam todas as linhas do dono.
- Teste de voz real no assistente (`/api/ai/simulate-voice`).
- Painel: "Fundo Sonoro" + botão "Ouvir Preview" (feitos na VPS em ago, nunca publicados).

## v0.2.0 — 2026-07-16 (canal: beta)

Leva de voz (latência), organização do painel e inteligência comercial.

### ✨ Novidades

**Voz / latência da ligação**
- **Piper TTS** integrado como provider (serviço local na VPS, `127.0.0.1:8090`, vozes
  faber/jeff/cadu). Recomendado pra ligação: baixa latência, sem depender de rede/OOM
  do edge-tts. Selecionável na aba Voz (sem chave).
- **VAD de dois estágios**: o filler ("ok/entendo") toca aos ~240ms de pausa (ack
  rápido) e o STT só dispara aos 550ms — resposta parece imediata sem cortar quem faz
  uma pausa curta.
- **LLM em streaming → TTS**: na ligação, o agente fala frase a frase enquanto o LLM
  ainda gera (menos silêncio). Salvaguarda anti-JSON: se a resposta for uma ação, NUNCA
  fala o JSON — cai no caminho normal. Fallback total pro modo atual em qualquer erro.

**Organização do painel**
- Abas reorganizadas: **Segurança** foi pra dentro de Configurações, **Gravações** pra
  dentro do CRM, e **Analytics** pra dentro de **Custos & ROI**.
- **Painel de ROI**: mostra o valor gerado — tempo economizado, salários de atendentes
  economizados (com encargos), atendentes equivalentes e atendimentos em plantão (fora
  do horário). Parâmetros ajustáveis (salário, encargos, minutos por atendimento).

**Inteligência comercial**
- **Histórico buscável de ligações**: transcrição + resumo + classificação de cada
  ligação, pesquisável por número ou palavra falada (aba "Ligações").
- **Analytics de conversão por campanha** (interessados/total) + **custo estimado por
  campanha** (por participação no gasto do tenant).
- **Teste A/B de áudio**: 2 roteiros por campanha (alterna A/B entre os contatos) e
  comparação de conversão por variante.
- **Retry inteligente**: quem não atendeu é re-ligado automaticamente no horário
  comercial, com limite de 3 tentativas (não liga pra sempre).

**Telegram**
- O agente assume que "mandar áudio" = tocar na **ligação** (ou massa), não enviar
  mensagem de voz. Só envia como voz se o dono pedir explicitamente.

### ⚙️ Migrações de banco (aditivas, seguras para rollback)

- `call_transcripts` (CREATE IF NOT EXISTS) + coluna `variant` (A/B).
- `daily_retries`: passa a respeitar limite de tentativas (sem mudança de schema).

## v0.1.0 — 2026-07-16 (canal: beta)

Primeira release com número minor (0.1.0). Leva grande de CRM, credenciais, controle
de custos e melhorias de UI/agente. Sobe como **beta** — a versão estável em produção
segue restaurável via `deploy/rollback.js` (ver `deploy/DEPLOY.md`).

### ✨ Novidades

**Credenciais (estilo n8n)**
- Aba única de Credenciais no painel: cadastra chaves nomeadas (nome + tipo + provedor
  + chave + base URL) uma vez e só seleciona por dropdown nas abas de IA/Voz.
- Tipos `llm` / `stt` / `tts`; a chave nunca volta em texto puro (mascarada na listagem).
- `AISettings`, `CallAISettings` e `VoiceSettings` passam a enviar só o `credential_id`
  (ou `stt_credential_id`/`tts_credential_id`); o backend resolve a chave em runtime.

**CRM**
- Prompt por etapa: cada etapa do Kanban tem um `system_prompt` próprio; o agente que
  atende o lead lê o prompt da etapa atual pra saber como conduzi-lo à próxima.
- Etapa **"Atendimento Humano"**: pausa a IA para aquele contato, notifica o dono no
  Telegram e dispara **callback reverso** (liga pro número do dono avisando do handoff).
- Gatilho por etapa: agente especializado é acionado quando o lead entra numa etapa cujo
  nome bate com o `trigger` do agente (antes era só por palavra no texto).
- Editor de prompt por coluna na UI do Kanban.
- Sub-abas de Contatos, Campanhas e Listas agrupadas dentro do CRM.

**Controle rígido de custos (hard limit)**
- Teto de gasto de IA por mês por tenant. Ao atingir o teto (com bloqueio ligado), as
  chamadas ao LLM são bloqueadas até o mês virar; aviso ao dono a partir de X% do teto.
- Gasto mensal (`ai_cost_monthly`, reinicia sozinho por período) + UI de orçamento com
  barra de progresso na página de Custos.

**Webhooks e notificações**
- Webhook `stage_change` ao mover lead de etapa (via CRM ou API).
- Intenção "quer falar com humano" move o lead pra "Atendimento Humano" automaticamente.
- Notificação no Telegram quando um agente especializado é acionado.

**IA de diagnóstico**
- Passa a "ouvir" o áudio real das chamadas: análise da forma de onda (silêncio, voz
  baixa, clipping/distorção, cortes por rede) alimenta o diagnóstico, não só a transcrição.

**Chat web / mobile**
- Gravação e envio de áudio pelo navegador (MediaRecorder → `/api/chat/audio`), com
  transcrição + resposta em voz.
- Responsividade do chat no celular; bolhas de mensagem não estouram mais o layout.

**Agente opera o painel**
- QR Code de pareamento enviado como **imagem** no Telegram (além do código em texto).

**Versionamento e deploy**
- `/api/version` agora reporta `version` + `channel` (stable|beta) + `build`.
- Fluxo versionado: `deploy/release.js` (tag Git `vX.Y.Z` + push Docker Hub),
  `deploy/deploy-beta.js` (sobe beta preservando a estável), `deploy/rollback.js`
  (restaura estável) e `deploy/promote-stable.js` (promove beta a estável).

### 🐛 Correções

- Chat web chamava `/api/console/*` (inexistente) → corrigido para `/api/chat/*`.
- Gateway compatível com OpenAI que só responde em streaming (omniroute) dava EOF sem
  `stream:true`: `chatOpenAIH` agora usa SSE (`stream:true` + parse de chunks) para
  provider `custom` e cai pra streaming automaticamente em EOF. Remove a necessidade da
  porta `:20129` provisória.

### ⚙️ Migrações de banco (aditivas, seguras para rollback)

- `crm_stages.prompt` (ADD COLUMN IF NOT EXISTS).
- `ai_cost_monthly` (CREATE TABLE IF NOT EXISTS) para o gasto mensal.
- `settings` chave `budget` (BudgetConfig) por tenant.

## v0.0.4 — 2026-07-10

### 🐛 Correções

- **Codec de áudio portável (corrige crash em CPUs sem AVX):** o codec MLow
  (`libopus_mlow.so`) era compilado com `-mavx` fixo, sem detecção de CPU em
  tempo de execução. Em servidores cujo processador não tem **AVX** (VPS com CPU
  restrita, processadores mais antigos), o AstraCalls **quebrava (SIGILL/SIGSEGV)**
  ao iniciar uma chamada — a ligação não completava. Agora o codec é compilado em
  baseline (SSE2), rodando em qualquer x86-64. Os fontes do MLow são C puro, sem
  perda funcional.

### ✨ Novidades

- **`groups_skip_incoming`** na config do Chatwoot: com `groups: true`, não reflete
  as mensagens dos outros membros do grupo (quando outra fonte já as traz pro mesmo
  inbox), postando só as mensagens do próprio aparelho e os avisos de entrada/saída —
  evita duplicação.

## v0.0.3 — 2026-07-10

Melhorias na integração com o Chatwoot: paridade com a Evolution e cobertura de
grupos. Todas as flags novas ficam na mesma config `POST /api/sessions/{sid}/chatwoot`.

### ✨ Novidades

**Assinatura do atendente e paridade com a Evolution**
- `sign_msg` — prefixa `*Nome do atendente*` no texto e na legenda de mídia das
  mensagens de saída (o nome vem do sender do webhook; não fica salvo na conversa)
- `always_online` — mantém a presença da conta sempre como online
- `read_messages` — confirma leitura automática das mensagens recebidas

**Grupos no Chatwoot**
- Mensagens que a conta envia **pelo aparelho** dentro de um grupo agora refletem
  no Chatwoot como nota privada (antes só conversas 1:1 espelhavam)
- Eventos de participantes de grupo (entrar, sair, virar/deixar de ser admin) —
  os mesmos avisos que o WhatsApp mostra na janela do grupo:
  - Novo evento de webhook `group_participants` (`group`, `actor`, `joined`, `left`, `promoted`, `demoted`)
  - Nota informativa na conversa do grupo (➕ entrou / ➖ saiu / ⭐ admin)

## v0.0.2 — 2026-07-08

Primeira versão estável desde a v0.0.1. Destaques: API completa estilo WAHA,
recepção de novos tipos de mensagem no Chatwoot, recursos avançados do whatsmeow
e suporte a pareamento por passkey.

### ✨ Novidades

**API completa (compatível com clientes estilo WAHA)**
- Mensagens e contatos
- Grupos (criar, participantes, admin)
- Canais, status, presença e perfil
- Histórico de conversas e mensagens
- Aliases de compatibilidade nos payloads (`id`/`chatId`/`subject`/`role`/`from`…)
- Documentação OpenAPI/Swagger de todas as rotas

**Novos tipos de mensagem recebida (renderizados no Chatwoot e no webhook)**
- Enquete/poll — criação, encaminhamento e recebimento de votos decodificados
- Figurinha (sticker/WebP) vira anexo
- Catálogo/produto e pedido do WhatsApp Business
- Cobrança Pix
- Evento do WhatsApp (nome/descrição/data BRT/local/link) + RSVP (Vou/Talvez/Não vou)
- Contato/vCard (nome + telefones)
- Reação (com o ID da mensagem reagida)
- Visualização única (desembrulha ViewOnce V2/V2Extension/legado; avisa quando indisponível)

**Recursos avançados do whatsmeow**
- Pareamento por código (sem QR)
- Privacidade da conta (leitura e alteração; privacidade de status)
- Mensagens temporárias (padrão e por conversa)
- Admin de grupo — solicitações de entrada, modo de aprovação e quem pode adicionar membros
- Perfil Business de contato e link/QR "me adicione"

**Passkey (WebAuthn)**
- Pareamento de contas que o WhatsApp passou a exigir passkey
- Extensão AstraCalls Passkey (Chrome) + integração no painel e download pelo próprio painel

**Integração Chatwoot**
- Abre conversas de grupos e canais (com toggles)
- Espelha como nota privada as mensagens 1:1 enviadas pelo aparelho (anti-loop por id)
- Resposta com citação bidirecional (Chatwoot ↔ WhatsApp)
- Grava `source_id` na mensagem de saída do agente
- Não reutiliza contato de grupo legado em conversa 1:1

**Chamadas**
- Gravação de chamada opt-in por sessão → nota privada no Chatwoot + webhook
- Disparo em massa de ligações com áudio pré-gravado

**Rede**
- Proxy de saída por sessão (http/https/socks5) via painel e API

**Interface**
- Redesign com identidade AstraCalls (logo, favicon, paleta navy/azul, layout de cards flutuantes, pt-BR)

### 🐛 Ajustes
- Selects de áudio responsivos (empilham no mobile, não estouram o box)
- Cabeçalho da conta responsivo (ações quebram linha; rótulos viram ícone no mobile)
- Bolinha do Switch encosta corretamente no fim
- Sidebar e conteúdo unificados num único container

## v0.0.1 — 2026-06-26

Versão inicial marcada do AstraCalls (chamadas WhatsApp no navegador + integração Chatwoot).
