# 05/10 11:38 — ligação de verdade: bancada (8288, v0.8.1) → celular da dona (8653). Ela achou boa.

Primeira ligação limpa com o código da v0.8.0/v0.8.1: só a dona e a IA "Vendas Hermes Call". 1 min 39 s de conversa.
Build da bancada: `20261005-1122_516c731` (a voz é a mesma da v0.8.0 que está no ar; a v0.8.1 não mexe na voz).
**Opinião da dona, logo depois: "pareceu boa".**

## Como foi
| Hora | O que aconteceu |
|---|---|
| 11:37:33 | oferta enviada; o celular estava reiniciando |
| 11:38:03 | o celular voltou e começou a tocar (`preaccept` + 3 `relaylatency`) |
| 11:38:07 | a dona tocou em atender (mais 3 `relaylatency`: o celular conectando no relay) |
| 11:38:14 | `accept` do celular → `remote accepted call` → `call ACTIVE` |
| 11:38:14–21 | isca (6,8 s) |
| 11:38:28 | resposta à isca: o Whisper devolveu islandês ("Ég er að hér."), o filtro descartou e a resposta ficou vazia; a oferta tocou assim mesmo |
| 11:38:28–52 | oferta inteira (23,4 s), sem interrupção |
| 11:38:55 | dona: "Sim, pode. Quanto custa?" → IA em 3,3 s: "Os planos começam em cento e noventa e nove reais por mês…" |
| 11:39:02 | a dona interrompeu ("Eu consigo testar a grátis?") e a IA parou na hora; resposta em 2,1 s |
| 11:39:08 | interrompeu de novo (repetiu a pergunta); resposta em 1,9 s, desta vez até o fim |
| 11:39:28 | "No momento eu não estou fazendo nenhum." → 1,9 s |
| 11:39:40 | "Vamos olhar o teste grátis, né?" → 1,7 s: "Posso pedir pra nossa equipe entrar em contato no seu WhatsApp…?" |
| 11:39:54 | a dona desligou (`terminate audio_duration=98701`) |

## Números
- **Tempo de resposta** (fim da fala → 1º áudio): 3,3 s na primeira; depois 2,1 / 1,9 / 1,9 / 1,7 s. Nenhum 429.
- **Interrupção:** funcionou nas duas vezes (a IA parou em menos de 1 s).
- **Preço:** respondeu o valor da tabela (R$ 199/mês) e o teste grátis de 10 horas; não fugiu nem inventou.
- **Rede:** `rx_perda_pct=0.3` (3 pacotes perdidos em 966), 4 fora de ordem, jitter 42,8 ms.
- Gravação: `registro=ok transcricao=ok`, 141 s; não foi ao Telegram porque a conta da bancada não tem bot.

## O que ainda dá para melhorar (visto nesta ligação)
1. **Depois de ser interrompida, a IA recomeça a resposta do começo.** "Os planos começam em cento e noventa e nove
   reais por mês" foi dito 3 vezes seguidas (uma por interrupção). Deveria continuar de onde parou ou responder só a
   pergunta nova.
2. **O resumo "qualidade do áudio" disse "com cortes" numa ligação boa.** Motivos: `rx_buracos=112` e `tx_buracos=8`.
   Os 112 são o silêncio da dona (o celular para de mandar áudio quando a pessoa cala), não corte. A regra do
   `Verdict()` (`internal/voip/call/audio_quality.go`: mais de 3 buracos recebidos = "com cortes") marca toda ligação
   com celular de verdade. Os 8 buracos no envio (maior: 281 ms) são nossos e merecem ser olhados.
3. A resposta à isca se perdeu (transcrição inventada, descartada). A oferta de 23 s toca inteira mesmo sem resposta.

## Antes dela: três tentativas que ficaram em "Conectando" (11:32, 11:33, 11:35)
- Nas três o celular tocou na hora, a dona atendeu, a tela ficou em "Conectando" e o **celular encerrou sozinho**
  16,0 a 17,5 s depois, sem mandar `accept`.
- Ela reiniciou o telefone e a quarta (11:37) conectou. Entre a v0.7.0 e a v0.8.0 nada mudou no que quem liga faz
  da oferta até o aceite (`git diff af7413e b9bf587 -- internal/voip cmd/server/broadcast.go`: em `internal/voip` só
  a medição de qualidade, o aceite presumido da bancada e as variantes do aceite RECEBIDO; em `broadcast.go` nada
  sobre aceite), e a mesma bancada conectou com o mesmo celular às 11:09 e às 11:38. **Tudo indica que era o
  telefone** (o celular só manda o `accept` depois de conectar no relay, e era isso que não completava). Não ficou
  provado: se voltar a acontecer com o telefone recém-ligado, investigar o lado do Hermes.
- Se um cliente relatar "atendi e ficou em conectando", olhar no registro: `preaccept` do celular, nenhum `accept` e
  um `terminate` do outro lado ~16 s depois.

## Captura do aceite de um celular de verdade (pedido 4 / A3) — FEITA
O que o celular manda quando atende (visto por quem liga, 11:38:14; igual ao das 11:09:56):
```
<call from="N@lid"><accept call-creator="N:14@lid" call-id="…">
  <audio enc="opus" rate="16000"/><net medium="2"/><encopt keygen="2"/>
  <metadata peer_abtest_bucket="…" peer_abtest_bucket_id_list="…"/>
</accept></call>
```
O que o Hermes manda quando atende (produção como "cliente" no ensaio das 11:09:41; o WhatsApp não repassou a quem ligou):
```
<call id="…" to="N@lid"><accept call-creator="N:14@lid" call-id="…">
  <audio enc="opus" rate="16000"/><net medium="3"/>
  <enc count="0" type="msg" v="2">[98 bytes]</enc><encopt keygen="2"/>
</accept></call>
```
**Diferenças que nenhuma das variantes 1 a 7 cobre** (novas hipóteses, a confirmar testando):
1. **`relaylatency`:** o celular manda 3 logo depois do `preaccept` e mais 3 quando a pessoa toca em atender, e só
   ~6 s depois manda o `accept`. O Hermes, quando atende, manda `preaccept` e `accept` e **nenhum `relaylatency`**
   (o montador existe: `signaling_build.go`, tag `relaylatency`).
2. **`<enc>` dentro do accept:** o Hermes manda; o do celular chega sem.
3. **`<net medium>`:** celular `2`, Hermes `3`.
4. Depois do accept o celular manda `mute_v2` (1,4 s depois). Quem liga (Hermes) responde `transport` + `mute_v2`.

Próximo passo: três peças novas no `HERMES_ACEITE_VARIANTE` (8 = manda `relaylatency` antes do accept; 16 = accept sem
`<enc>`; 32 = `medium="2"`) e testar na bancada com um celular da dona LIGANDO para o 8288
(`HERMES_AUTO_ANSWER_ACEITAR=true` só na bancada, com ela avisada: REGRESSOES §6).

## Na produção (aparelho 30 da mesma conta do 8653)
- Ligação atendida no celular: a produção recebeu o `accept` e encerrou certo (`answered_elsewhere`, sem retorno).
- Nas três que o celular encerrou sem atender, a produção **não foi avisada** e ficou com a ligação "tocando" até o
  vigia de 6 min (`callback: não retorno motivo="encerrada por local (watchdog)"`). Igual ao que aconteceu às 10:56 e
  10:58, quando quem desistiu foi a bancada. Com cliente de verdade ligando e desistindo, a produção recebe o
  `terminate` e faz o retorno (3 retornos desde 01/10).

## Log da bancada (números trocados por N, linhas longas cortadas)
```
time=2026-10-05T11:37:31.489-03:00 level=INFO msg="audio_2: campos recebidos" tts_message_2=true tts_len=387 audio_id_2="" audio_url_2=false audio_base64_2=false
time=2026-10-05T11:37:31.489-03:00 level=INFO msg="audio_2: sintetizando TTS" voice=hpp4J3VqNfWAUOO0d1Us text_len=387
time=2026-10-05T11:37:32.315-03:00 level=INFO msg="audio_2: TTS resultado" bytes=371191 err=<nil>
time=2026-10-05T11:37:32.541-03:00 level=INFO msg="audio_2: PCM2 OK" samples=370329 conversational=true
time=2026-10-05T11:37:33.124-03:00 level=INFO msg="resolveCallPeer: JID real difere do normalizado" input=N resolved=N
time=2026-10-05T11:37:33.137-03:00 level=INFO msg="voz: motor reserva da ligação (perfil)" userID=6dbb3d22-87e7-49f9-a7ac-2883eeebba31 perfil="Teste E (renomeado 02-10)" fallback=llama3-8b-8192
time=2026-10-05T11:37:33.147-03:00 level=INFO msg="TTS per-user criado" owner=6dbb3d22-87e7-49f9-a7ac-2883eeebba31 provider=elevenlabs voice=hpp4J3VqNfWAUOO0d1Us
time=2026-10-05T11:37:33.150-03:00 level=WARN msg="ATENÇÃO (teste, só bancada): a IA ouve antes do aceite (HERMES_VOICE_ESPERA_ACEITE=false)" callID=1F28C0317991F20C7602838BD4FC91BE
time=2026-10-05T11:37:33.152-03:00 level=INFO msg="voice agent attached to call" callID=1F28C0317991F20C7602838BD4FC91BE aguardando_aceite=false
time=2026-10-05T11:37:33.251-03:00 level=INFO msg="call offer sent" call_id=1F28C0317991F20C7602838BD4FC91BE peer=N@lid
time=2026-10-05T11:37:33.252-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=enviada ordem=1 xml="<call id=\"55B7ADA00AA7F298FA60F5A659DE39CA\" to=\"N@lid\"><offer call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><audio enc=\"opus\" rate=\"8000\"/><audio enc=\"opus\" rate=\"16000\"/><net medium=\"3\"/><capability ver=\"1\">[7 bytes]</capability><destination><to jid=\"N@lid\"><enc count=\"0\" type=\"msg\" v=\"2\">[118 bytes]</enc></to><to jid=\"N:2 …[cortado]
time=2026-10-05T11:37:33.555-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=resposta ordem=2 xml="<ack class=\"call\" from=\"N@lid\" id=\"55B7ADA00AA7F298FA60F5A659DE39CA\" type=\"offer\"><relay attribute_padding=\"1\" call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\" joinable=\"1\" peer_pid=\"0\" self_pid=\"1\" uuid=\"4s7Rzjs-mcoThIfD\"><participant jid=\"N@lid\" pid=\"0\"/><participant jid=\"N:23@lid\" pid=\"2\"/><participant jid=\"N:29@lid\" pi …[cortado]
time=2026-10-05T11:37:33.558-03:00 level=INFO msg="offer ack" xml="<ack class=\"call\" from=\"N@lid\" id=\"55B7ADA00AA7F298FA60F5A659DE39CA\" type=\"offer\"><relay attribute_padding=\"1\" call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\" joinable=\"1\" peer_pid=\"0\" self_pid=\"1\" uuid=\"4s7Rzjs-mcoThIfD\"><participant jid=\"N@lid\" pid=\"0\"/><participant jid=\"N:23@lid\" pid=\"2\"/><participant jid=\"N:29@lid\" pid=\"3\"/><participant jid=\"N:30@lid\" pid=\"4\"/><token id=\"0\"><!-- 193 byte …[cortado]
seq_req\":\"10\",\"audio_ts_jitter_use_frame_ts\":\"true\",\"call_replayer_use_v2\":\"true\",\"callee_precall_e2e_bind_interval_ms\":\"200\",\"caller_timeout\":\"90\",\"check_rx_active_when_disable_prefer_relay_with_active_p2p\":\"1\",\"client_relay_election_latency_threshold_ms\":\"100\",\"client_relay_election_strategy\":\"1\",\"clock_callback_process_step\":\"3\",\"compute_rx_audio_level\":\"true\",\"connected_fix_bitmap\":\"4\",\"debug_metric_1\":\"100\",\"debug_metric_2\":\"100\",\"debug_metric_3\":\"100\",\"d …[cortado]
time=2026-10-05T11:37:33.564-03:00 level=INFO msg="offer ack received" relays=3 participants=4
time=2026-10-05T11:37:33.564-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=enviada ordem=3 xml="<call id=\"65ADA95C6B2CC1F54DC7A3A9F9C66777\" to=\"N@lid\"><preaccept call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><audio enc=\"opus\" rate=\"16000\"/><encopt keygen=\"2\"/><capability ver=\"1\">[7 bytes]</capability></preaccept></call>"
time=2026-10-05T11:37:33.565-03:00 level=INFO msg="relay connecting" id=157.240.212.133:3478#0 name=lis1c01
time=2026-10-05T11:37:33.566-03:00 level=INFO msg="relay connecting" id=57.144.155.57:3478#0 name=cdg4c01
time=2026-10-05T11:37:33.567-03:00 level=INFO msg="relay ice state" id=157.240.212.133:3478#0 state=checking
time=2026-10-05T11:37:33.567-03:00 level=INFO msg="relay connecting" id=57.144.63.57:3478#0 name=lhr11c01
time=2026-10-05T11:37:33.568-03:00 level=INFO msg="relay ice state" id=57.144.155.57:3478#0 state=checking
time=2026-10-05T11:37:33.569-03:00 level=INFO msg="relay configured" connected=0
time=2026-10-05T11:37:33.569-03:00 level=INFO msg="relay ice state" id=57.144.63.57:3478#0 state=checking
time=2026-10-05T11:37:33.802-03:00 level=INFO msg="relay ice state" id=57.144.155.57:3478#0 state=connected
time=2026-10-05T11:37:33.809-03:00 level=INFO msg="relay ice state" id=57.144.63.57:3478#0 state=connected
time=2026-10-05T11:37:33.828-03:00 level=INFO msg="relay ice state" id=157.240.212.133:3478#0 state=connected
time=2026-10-05T11:37:33.857-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=4 xml="<call from=\"N:30@lid\"><preaccept call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><audio enc=\"opus\" rate=\"16000\"/><encopt keygen=\"2\"/><capability ver=\"1\">[7 bytes]</capability></preaccept></call>"
time=2026-10-05T11:37:33.864-03:00 level=INFO msg="relay datachannel open" id=57.144.155.57:3478#0
time=2026-10-05T11:37:33.911-03:00 level=INFO msg="relay datachannel open" id=57.144.63.57:3478#0
time=2026-10-05T11:37:34.002-03:00 level=INFO msg="relay datachannel open" id=157.240.212.133:3478#0
time=2026-10-05T11:38:03.683-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=5 xml="<call from=\"N@lid\"><preaccept call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><audio enc=\"opus\" rate=\"16000\"/><encopt keygen=\"2\"/><capability ver=\"1\">[7 bytes]</capability></preaccept></call>"
time=2026-10-05T11:38:03.791-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=6 xml="<call from=\"N@lid\"><relaylatency call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><te latency=\"33554545\" relay_name=\"lis1c01\">[6 bytes]</te></relaylatency></call>"
time=2026-10-05T11:38:03.830-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=7 xml="<call from=\"N@lid\"><relaylatency call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><te latency=\"33554578\" relay_name=\"lhr11c01\">[6 bytes]</te></relaylatency></call>"
time=2026-10-05T11:38:03.875-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=8 xml="<call from=\"N@lid\"><relaylatency call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><te latency=\"33554632\" relay_name=\"cdg4c01\">[6 bytes]</te></relaylatency></call>"
time=2026-10-05T11:38:07.855-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=9 xml="<call from=\"N@lid\"><relaylatency call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><te latency=\"100663408\" relay_name=\"lis1c01\">[6 bytes]</te></relaylatency></call>"
time=2026-10-05T11:38:07.894-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=10 xml="<call from=\"N@lid\"><relaylatency call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><te latency=\"100663443\" relay_name=\"lhr11c01\">[6 bytes]</te></relaylatency></call>"
time=2026-10-05T11:38:07.935-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=11 xml="<call from=\"N@lid\"><relaylatency call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><te latency=\"100663494\" relay_name=\"cdg4c01\">[6 bytes]</te></relaylatency></call>"
time=2026-10-05T11:38:14.154-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=12 xml="<call from=\"N@lid\"><accept call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\"><audio enc=\"opus\" rate=\"16000\"/><net medium=\"2\"/><encopt keygen=\"2\"/><metadata peer_abtest_bucket=\"wa_subteam_calling_1_on_1_reliability_holdout_2026_h1_rollout\" peer_abtest_bucket_id_list=\"142126,143296,96918\"/></accept></call>"
time=2026-10-05T11:38:14.155-03:00 level=INFO msg="remote accepted call" call_id=1F28C0317991F20C7602838BD4FC91BE peer=N@lid relay_connected=true relay_endpoints=3
time=2026-10-05T11:38:14.155-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=enviada ordem=13 xml="<call id=\"A1FE1934CB441E772E5D20E10436C47F\" to=\"N@lid\"><transport call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\" p2p-cand-round=\"1\" transport-message-type=\"1\"><net medium=\"2\" protocol=\"0\"/></transport></call>"
time=2026-10-05T11:38:14.155-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=enviada ordem=14 xml="<call id=\"220D869BEDF142E7C4A40C4C3AE7565B\" to=\"N@lid\"><mute_v2 call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\" mute-state=\"0\"/></call>"
time=2026-10-05T11:38:14.192-03:00 level=INFO msg="call ACTIVE (media path established)" call_id=1F28C0317991F20C7602838BD4FC91BE audio=true
time=2026-10-05T11:38:14.716-03:00 level=INFO msg="runCampaign: gate pcm2" callID=1F28C0317991F20C7602838BD4FC91BE pcm2_len=370329 conversational=true voiceSvcNil=false
time=2026-10-05T11:38:14.717-03:00 level=INFO msg="2-audio: reg.get resultado" callID=1F28C0317991F20C7602838BD4FC91BE hasAC=true acNil=false voiceAgentNil=false
time=2026-10-05T11:38:15.590-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=15 xml="<call from=\"N@lid\" id=\"N-21\" t=\"N\"><mute_v2 call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\" mute-state=\"0\"/></call>"
time=2026-10-05T11:38:21.482-03:00 level=INFO msg="2-audio: áudio 1 (isca) tocado" callID=1F28C0317991F20C7602838BD4FC91BE durMs=6763
time=2026-10-05T11:38:21.483-03:00 level=INFO msg="2-audio: aguardando resposta do cliente" callID=1F28C0317991F20C7602838BD4FC91BE
time=2026-10-05T11:38:28.325-03:00 level=INFO msg="stt request" provider=groq model=whisper-large-v3-turbo url=https://api.groq.com/openai/v1/audio/transcriptions
time=2026-10-05T11:38:28.662-03:00 level=INFO msg="stt: trecho de baixa confiança descartado" motivo="baixa confiança (avg_logprob baixo)" trechos_descartados=1 trechos=1 texto="Ég er að hér."
time=2026-10-05T11:38:28.662-03:00 level=INFO msg="stt: nada confiável na fala, tratada como não entendida"
time=2026-10-05T11:38:28.662-03:00 level=INFO msg="voice: transcrição antecipada aproveitada" text=""
time=2026-10-05T11:38:28.662-03:00 level=INFO msg="2-audio: resposta à isca" callID=1F28C0317991F20C7602838BD4FC91BE texto="" stt_ms=196
time=2026-10-05T11:38:52.066-03:00 level=INFO msg="voice: áudio gravado não foi cortado" frames_com_voz=3 maior_sequencia=2 exigido=7 barge_desligado=false
time=2026-10-05T11:38:52.067-03:00 level=INFO msg="2-audio: áudio 2 (oferta) tocado" callID=1F28C0317991F20C7602838BD4FC91BE durMs=23404 interrompida=false pct=100
time=2026-10-05T11:38:52.083-03:00 level=INFO msg="ligação: voz aplicada (pool/profile)" callID=1F28C0317991F20C7602838BD4FC91BE voice=hpp4J3VqNfWAUOO0d1Us
time=2026-10-05T11:38:52.085-03:00 level=INFO msg="conversational mode started" callID=1F28C0317991F20C7602838BD4FC91BE maxMs=240000 idleHangupSec=60
time=2026-10-05T11:38:54.391-03:00 level=INFO msg="barge-in ack pré-gerado" count=6 de=6 cache_hits=1 ms=2305 em_uso=true
time=2026-10-05T11:38:55.291-03:00 level=INFO msg="stt request" provider=groq model=whisper-large-v3-turbo url=https://api.groq.com/openai/v1/audio/transcriptions
time=2026-10-05T11:38:55.504-03:00 level=INFO msg="voice: transcrição antecipada aproveitada" text="Sim, pode. Quanto custa?"
time=2026-10-05T11:38:55.505-03:00 level=INFO msg="voice transcribed" text="Sim, pode. Quanto custa?"
time=2026-10-05T11:38:56.522-03:00 level=INFO msg="voice first audio" ms=1016
time=2026-10-05T11:38:58.215-03:00 level=INFO msg="voice latência real" ms_fim_fala_ate_1o_audio=3311 vad_ms=601 stt_ms=0 llm_1a_frase_ms=1016 tts_ms=1693
time=2026-10-05T11:38:59.429-03:00 level=INFO msg="filler pré-gerado" count=18 de=18 cache_hits=4 ms=7344 em_uso=true
time=2026-10-05T11:39:02.325-03:00 level=INFO msg="voice barge-in" rms_in=0.N threshold=0.N fator_eco=0.N eco_medido=1.Ne-08 preroll_ms=540
time=2026-10-05T11:39:02.344-03:00 level=INFO msg="voice reply descartado por barge-in" reply_parcial="Os planos começam em cento e noventa e nove reais por mês. Qual é o volume de atendimento que você faz hoje no seu negócio?"
time=2026-10-05T11:39:02.493-03:00 level=INFO msg="voice barge-in" rms_in=0.N threshold=0.N fator_eco=0.N eco_medido=1.Ne-08 preroll_ms=0
time=2026-10-05T11:39:03.542-03:00 level=INFO msg="stt request" provider=groq model=whisper-large-v3-turbo url=https://api.groq.com/openai/v1/audio/transcriptions
time=2026-10-05T11:39:03.816-03:00 level=INFO msg="voice: transcrição antecipada aproveitada" text="Eu consigo testar a grátis?"
time=2026-10-05T11:39:03.817-03:00 level=INFO msg="voice transcribed" text="Eu consigo testar a grátis?"
time=2026-10-05T11:39:04.450-03:00 level=INFO msg="voice first audio" ms=632
time=2026-10-05T11:39:05.316-03:00 level=INFO msg="voice latência real" ms_fim_fala_ate_1o_audio=2100 vad_ms=601 stt_ms=0 llm_1a_frase_ms=632 tts_ms=866
time=2026-10-05T11:39:08.155-03:00 level=INFO msg="voice barge-in" rms_in=0.N threshold=0.N fator_eco=0.N eco_medido=7.Ne-09 preroll_ms=540
time=2026-10-05T11:39:08.155-03:00 level=INFO msg="voice reply descartado por barge-in" reply_parcial="Os planos começam em cento e noventa e nove reais por mês. E sim, você pode testar grátis por dez horas direto no nosso site, sem precisar colocar cartão. Me conta um pouco do seu negócio, você atende mais no WhatsApp ou por ligação?"
time=2026-10-05T11:39:09.956-03:00 level=INFO msg="stt request" provider=groq model=whisper-large-v3-turbo url=https://api.groq.com/openai/v1/audio/transcriptions
time=2026-10-05T11:39:10.199-03:00 level=INFO msg="voice: transcrição antecipada aproveitada" text="Eu consigo testar grátis."
time=2026-10-05T11:39:10.200-03:00 level=INFO msg="voice transcribed" text="Eu consigo testar grátis."
time=2026-10-05T11:39:10.999-03:00 level=INFO msg="voice first audio" ms=799
time=2026-10-05T11:39:11.458-03:00 level=INFO msg="voice latência real" ms_fim_fala_ate_1o_audio=1911 vad_ms=600 stt_ms=52 llm_1a_frase_ms=799 tts_ms=459
time=2026-10-05T11:39:24.923-03:00 level=INFO msg="voice ai reply" reply="Os planos começam em cento e noventa e nove reais por mês. E sim, você tem um teste grátis de dez horas para experimentar tudo sem precisar cadastrar cartão! Qual é o volume de atendimentos que você faz por dia hoje?" streamed=true
time=2026-10-05T11:39:27.940-03:00 level=INFO msg="stt request" provider=groq model=whisper-large-v3-turbo url=https://api.groq.com/openai/v1/audio/transcriptions
time=2026-10-05T11:39:28.187-03:00 level=INFO msg="voice: transcrição antecipada aproveitada" text="No momento eu não estou fazendo nenhum."
time=2026-10-05T11:39:28.187-03:00 level=INFO msg="voice transcribed" text="No momento eu não estou fazendo nenhum."
time=2026-10-05T11:39:28.946-03:00 level=INFO msg="voice first audio" ms=759
time=2026-10-05T11:39:29.436-03:00 level=INFO msg="voice latência real" ms_fim_fala_ate_1o_audio=1906 vad_ms=600 stt_ms=58 llm_1a_frase_ms=759 tts_ms=489
time=2026-10-05T11:39:37.358-03:00 level=INFO msg="voice ai reply" reply="Ah, entendi! E você está planejando começar algum negócio em breve ou prefere dar uma olhada no teste grátis para já deixar tudo pronto?" streamed=true
time=2026-10-05T11:39:40.489-03:00 level=INFO msg="stt request" provider=groq model=whisper-large-v3-turbo url=https://api.groq.com/openai/v1/audio/transcriptions
time=2026-10-05T11:39:40.753-03:00 level=INFO msg="voice: transcrição antecipada aproveitada" text="Vamos olhar o teste grátis, né?"
time=2026-10-05T11:39:40.753-03:00 level=INFO msg="voice transcribed" text="Vamos olhar o teste grátis, né?"
time=2026-10-05T11:39:41.397-03:00 level=INFO msg="voice first audio" ms=644
time=2026-10-05T11:39:41.732-03:00 level=INFO msg="voice latência real" ms_fim_fala_ate_1o_audio=1665 vad_ms=600 stt_ms=86 llm_1a_frase_ms=644 tts_ms=334
time=2026-10-05T11:39:50.977-03:00 level=INFO msg="voice ai reply" reply="Perfeito! O teste é direto no nosso site e dá pra começar na hora. Posso pedir pra nossa equipe entrar em contato no seu WhatsApp para te mandar o passo a passo?" streamed=true
time=2026-10-05T11:39:54.256-03:00 level=INFO msg="sinalização da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE sentido=recebida ordem=16 xml="<call from=\"N@lid\"><terminate audio_duration=\"98701\" call-creator=\"N:14@lid\" call-id=\"1F28C0317991F20C7602838BD4FC91BE\" duration=\"98701\"/></call>"
time=2026-10-05T11:39:54.256-03:00 level=INFO msg="call terminated by peer" call_id=1F28C0317991F20C7602838BD4FC91BE reason=user_ended ended_by=peer
time=2026-10-05T11:39:54.260-03:00 level=INFO msg="relay ice state" id=157.240.212.133:3478#0 state=closed
time=2026-10-05T11:39:54.265-03:00 level=INFO msg="relay ice state" id=57.144.155.57:3478#0 state=closed
time=2026-10-05T11:39:54.266-03:00 level=INFO msg="qualidade do áudio da ligação" call_id=1F28C0317991F20C7602838BD4FC91BE resultado="com cortes" rx_pacotes=966 rx_perdidos=3 rx_perda_pct=0.3 rx_fora_ordem=4 rx_repetidos=0 rx_erros_srtp=0 rx_erros_decodificar=0 rx_jitter_ms=42.8 rx_maior_buraco_ms=6764 rx_buracos=112 tx_frames=1150 tx_erros_codificar=0 tx_erros_srtp=0 tx_maior_buraco_ms=281 tx_buracos=8
time=2026-10-05T11:39:54.266-03:00 level=INFO msg="relay ice state" id=57.144.63.57:3478#0 state=closed
time=2026-10-05T11:39:54.483-03:00 level=INFO msg="conversational: chamada encerrada" callID=1F28C0317991F20C7602838BD4FC91BE motivo=user_ended encerrou=cliente
time=2026-10-05T11:39:54.483-03:00 level=INFO msg="media stats da ligação" callID=1F28C0317991F20C7602838BD4FC91BE framesEncoded=1150 encodeErrs=0 srtpErrs=0 lossPct=0
time=2026-10-05T11:39:54.530-03:00 level=INFO msg="lead journey gravado" jid=N@s.whatsapp.net stage=Conversou score=60
time=2026-10-05T11:39:55.006-03:00 level=INFO msg="stt request" provider=groq model=whisper-large-v3-turbo url=https://api.groq.com/openai/v1/audio/transcriptions
time=2026-10-05T11:39:55.562-03:00 level=INFO msg="gravação não enviada ao Telegram: a conta não tem bot nem chat (o áudio fica na aba Gravações)" call_id=1F28C0317991F20C7602838BD4FC91BE entrega=sem_telegram direcao=outbound motivo_fim=user_ended segundos=141 registro=ok transcricao=ok resumo=sem_ia
time=2026-10-05T11:39:56.553-03:00 level=INFO msg="audio quality analisado" callID=16d9435a-2ae7-48b3-a6ce-a4820065eced status=OK peer=N@lid
```
