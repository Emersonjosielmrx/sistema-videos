# Regressões da ligação — sintoma → causa → correção → teste que protege

> **Por que existe:** a dona notou que alguns problemas da ligação são corrigidos e VOLTAM quando outro
> agente mexe no código ("fica nesse ciclo"). Este arquivo é a memória desses problemas.
>
> **Regra pra qualquer agente (vale acima de pressa):**
> 1. Antes de mexer em `internal/voice/`, `cmd/server/broadcast.go` (abertura de 2 áudios, conversa),
>    `cmd/server/session.go` (ligação recebida) ou no codec (`internal/voip/media`, `Dockerfile`), leia esta página.
> 2. Os testes listados aqui **não podem ser apagados, pulados nem afrouxados** pra "passar". Se um deles quebrar,
>    o seu código trouxe o problema de volta.
> 3. Rode `go test ./internal/voice/ ./cmd/server/` antes de commitar; no codec, o teste com a tag `mlow` na VPS.
>    O **simulador de ligação** (`internal/voice/simulador_test.go`, `go test ./internal/voice/ -run Simulador -v`)
>    roda o agente de voz inteiro com uma linha telefônica falsa e confere os problemas desta página em tempo real
>    (~18 s). Cada cenário foi conferido recolocando o defeito antigo no código: o teste falha. Problema novo que
>    volta = cenário novo lá.
> 4. Mudou a voz? Faça uma ligação de verdade antes de dizer que está pronto (`/root/ligacao-teste.sh` na VPS ou
>    uma ligação com a dona) e confira no log: `voice barge-in`, `áudio 2 (oferta) tocado … interrompida`,
>    `voice latência real`.
> 5. Achou um problema novo que volta? Acrescente uma linha aqui com o teste que o segura.

## 1. "Falei e ela não parou de falar" (interromper a IA)

| Quando | Causa | Correção | Teste |
|---|---|---|---|
| v0.6.0 (02/10) | Anti-eco exigia a voz do cliente 2× mais alta que a saída da IA — impossível no celular | v0.6.1: mede o eco REAL de cada ligação (`observeEchoCoupling`, `echoGateFactorNow`) | `internal/voice/echo_couple_test.go`, `echo_gate_test.go` |
| 03/10 noite | Pra cortar a OFERTA gravada exigia 7 frames (420 ms) de voz **seguidos**; a pausa natural entre sílabas (1 frame de 60 ms abaixo do limiar) zerava a conta → a oferta (27 s) quase nunca era cortada | Conta voz **dentro de uma janela** (`bargeVoiced`: 7 em 10 frames; respostas 3 em 4). Log `voice: áudio gravado não foi cortado` mostra frames com voz × exigido quando não corta | `TestOferta_VozComPausasEntreSilabasCorta` (falha no código antigo), `TestOferta_UhumNaoCorta`, `TestPlayExternal_OfertaInterrompivel`, `TestSimulador_OfertaCortadaPelaFala`, `TestSimulador_InterromperResposta` |

Não mexer sem teste: `HERMES_VOICE_OFFER_BARGE_MS` (420), `HERMES_VOICE_OFFER_GRACE_MS` (700), a isca é de propósito
NÃO interrompível (`TestPlayExternal_IscaNaoInterrompivel`).

## 2. Servidor cai no meio da ligação (todas as ligações caem juntas)

| Quando | Causa | Correção | Teste |
|---|---|---|---|
| 25/09 (produção) e 03/10 (bancada) | Codec MLow (`libopus_mlow.so`) compilado com `OPUS_HARDENING=ON`: um pacote de áudio inesperado faz um `assert` em C ABORTAR o processo (`silk/resampler.c:101`) | Lib recompilada com `-DOPUS_HARDENING=OFF -DOPUS_ASSERTIONS=OFF` (Dockerfile + `/usr/local/lib` na VPS; antiga em `/opt/hermes-call/codec-backup/`) | `TestMLowDecodeGarbage` e `TestMLowHermesToHermes` (`internal/voip/media/mlow_stress_test.go`, tag `mlow`, roda na VPS) |

Se reinstalar/recompilar a lib: confira `strings /usr/local/lib/libopus_mlow.so | grep -c "assertion failed"` = 0.

## 3. Voz diferente / picotada / fundo abaixando

| Quando | Causa | Correção | Teste |
|---|---|---|---|
| 31/07 | Dois playbacks ao mesmo tempo intercalavam frames ("uma sílaba sim, outra não") | `playbackMu` serializa o playback inteiro | `TestPlay_DoisAudiosNaoIntercalam` |
| v0.6.0 | ElevenLabs em PCM 16 kHz e fundo abaixando sob a voz | v0.6.1: MP3 44 kHz (PCM só com `HERMES_ELEVEN_PCM=true`), `defaultDuckGain = 0 dB` | `tts_pcm_test.go`, `mix_test.go` |
| 04/10 (revisão do v0.8.0) | A dona entrava pelo card do lead quente (gatilho só-aviso) e a IA seguia falando junto (voz da dona + IA no mesmo `FeedCapturedPCM`); o `Mute` só barrava o PRÓXIMO áudio (a frase/oferta em curso e o fundo seguiam); sair do navegador derrubava a ligação; e com a IA calada a conversa caía "por silêncio" em 1 min | Todo gatilho arma o modo painel (ponte silenciosa no só-aviso); `Mute` corta o áudio em curso (inclusive gravado) e o fundo, cancela o turno; `IdleFor` = 0 com a IA calada; sair do navegador reativa a IA sem derrubar (`onBrowserGone`, `DELETE …/webrtc`) | `TestMute_CortaOAudioEmCursoENaoDeixaTocarOutro`, `TestMute_NaoContaComoSilencio`, `TestPainel_EntrarCalaASairVoltaSemDerrubar`, `TestPainel_SairPeloBotao` |
| 06/10 | A VPS da produção pausa o processo por 100–250 ms várias vezes por segundo (medido; as outras duas VPS não). O envio seguia um `time.Ticker`, que descarta os ticks perdidos: depois de cada engasgo a fala toda saía atrasada e o celular ouvia um buraco. O silêncio de manutenção (120 ms sem áudio) ainda punha um frame mudo entre duas sílabas. E a gravação punha cada frame na hora em que chegou: buraco + frames somados um em cima do outro (132 buracos em 69 s) | Ritmo por prazo (`pacer`): frame atrasado sai em seguida, até 300 ms. Silêncio de manutenção só com 300 ms sem áudio (`keepaliveIdle`). Gravação montada em sequência por lado (`recLane`). **Não troque o `pacer` por `time.Ticker` nem ponha frame de gravação "pela hora de chegada".** Análise: `docs/ensaios/2026-10-06_1246_ligacao-picotada.md` | `TestPlay_RecuperaAtrasoDoServidor`, `TestPacer_AtrasoGrandeRecomecaDeAgora`, `TestKeepalive_EngasgoNoMeioDaFalaNaoViraSilencio`, `TestGravacao_AtrasoERajadaNaoViramBuracoNemSobreposicao`, `TestGravacao_PausaDeVerdadeEOutroLadoFicamNaHoraDeChegada` |

## 4. Preço "enrolado"

| Quando | Causa | Correção | Teste |
|---|---|---|---|
| v0.6.0 | "R$ 199/mês" ia cru pro TTS | `spellMoneyPTBR` por extenso; `+` entre palavras vira "mais" | `tts_numeros_test.go` |

## 5. Ligação recebida "atendida" mas quem liga continua vendo "chamando"

| Quando | Causa | Situação |
|---|---|---|
| desde sempre (descoberto 03/10) | O "atender automaticamente" nunca mandava o aceite. Com o aceite implementado, o WhatsApp NÃO reconhece o aceite enviado pelo Hermes (áudio passa, mas o outro lado segue "chamando" e desliga em ~40 s) | **Desligado** (`HERMES_AUTO_ANSWER_ACEITAR`, padrão off); vale o retorno automático. Pendente: formato de `signaling.BuildAcceptStanza` |

**Como investigar (04/10, plano item L4):** toda ligação agora registra cada mensagem de sinalização, nos dois
sentidos, com chaves e tokens apagados (`cmd/server/call_trace.go`, linha `sinalização da ligação`).
1. Ligue do Hermes pro celular da dona e atenda no celular. As linhas `sentido=recebida` mostram como um celular
   ACEITA (`preaccept`, `accept`, `transport`, `relaylatency`, recibos).
2. Na bancada, com `HERMES_AUTO_ANSWER_ACEITAR=true`, ligue do 8653 pro 8288. As linhas `sentido=enviada` da
   bancada mostram como o Hermes aceita.
3. Compare. Diferenças que já aparecem no código (`internal/voip/signaling/signaling_build.go`), a confirmar:
   - o `<preaccept>` (mandado quando a oferta chega, `HandleCallOffer`) vai pro APARELHO exato de quem liga
     (`peerJid`), mas o `<accept>` vai pro número SEM o aparelho (`CleanJID`);
   - anuncia só `audio rate=16000` (a oferta do Hermes anuncia 8000 e 16000) e não tem `<capability>`;
   - na ligação que o Hermes FAZ, depois do aceite do celular ele manda `transport` (tipo 1), `mute_v2` e um recibo
     do aceite (`HandleCallAccept`); na que ele ATENDE, não manda nada disso.

**Variantes para testar na bancada (A2, 04/10):** `HERMES_ACEITE_VARIANTE` = soma das peças
(`signaling.AcceptVariant`, `internal/voip/signaling/signaling_build.go`). Só vale com o aceite automático ligado
(`HERMES_AUTO_ANSWER_ACEITAR=true`), e as duas só na bancada. O log mostra `aceite: VARIANTE em teste`.

| Variante | Peças | O que muda no accept |
|---|---|---|
| 0 | — | o aceite de sempre (para o número sem aparelho, só 16000, sem capability) |
| 1 | aparelho | `to` = aparelho exato de quem liga (igual ao `<preaccept>`) |
| 2 | taxas | `audio` 8000 e 16000 + `<capability>` do preaccept |
| 3 | 1+2 | as duas acima |
| 4 | depois | depois do accept manda `transport` (tipo 1, rodada 1) e `mute_v2` para o aparelho de quem liga |
| 5 | 1+4 | |
| 6 | 2+4 | |
| 7 | 1+2+4 | as três primeiras juntas |
| 8 | relaylatency | antes do accept, um `<relaylatency>` por relay da oferta (o celular manda; o Hermes não mandava) |
| 16 | sem enc | accept sem `<enc>` e sem device-identity (o accept do celular chega sem) |
| 32 | medium | `<net medium="2"/>` em vez de `3` |
| 57 | 1+8+16+32 | o mais parecido com o celular: testar primeiro; se passar, tirar uma peça por vez |

Como saber se passou: o celular que ligou para de mostrar "chamando" e mostra o tempo da ligação correndo; no log de quem
ligou (se for outro Hermes) aparece `remote accepted call`. Testes do XML: `TestAceite_*`
(`internal/voip/signaling/accept_variant_test.go`) e `TestAceitarLigacao_*` (`internal/voip/call/aceite_variante_test.go`).

**Captura de um celular de verdade (05/10 11:38, `docs/ensaios/2026-10-05_1138_ligacao-humana.md`):** o celular manda
`preaccept`, 3 `relaylatency`, mais 3 `relaylatency` quando a pessoa toca em atender e só então o `accept`
(`<audio rate=16000/><net medium="2"/><encopt keygen="2"/>`, **sem `<enc>`**), e depois `mute_v2`. O Hermes manda
`preaccept` e `accept` com `<net medium="3"/>` e um `<enc>`, e nenhum `relaylatency`. As variantes 1 a 7 não cobrem
nenhuma das três diferenças; por isso existem as peças 8 (`relaylatency` antes do accept), 16 (accept sem `<enc>`) e 32
(`medium="2"`).

## 6. Bancada atrapalhando ligação de teste

A bancada (cópia do Hermes na VPS) está ligada ao número **8288**. Se ela estiver numa versão que atende sozinha,
ela ENTRA nas ligações pro 8288 junto com a dona (03/10: o "cliente simulado" falou por cima, cortes, transcrições
sem sentido, e o celular da dona ficou "chamando"). Antes de a dona testar com o 8288: bancada sem aceite
automático. Confira o que está RODANDO, não os arquivos: `curl -s 127.0.0.1:8091/api/version` (build = versão
atual) e `tr '\0' '\n' </proc/$(systemctl show -p MainPID --value hermes-bancada)/environ | grep AUTO_ANSWER_ACEITAR`
(nada, ou `false`). A bancada HERDA o ambiente da produção (`/opt/hermes-bancada/iniciar.sh`): confira o
`hermes-call` do mesmo jeito. O `ops/publicar.sh` só mexe na bancada com `PUBLICAR_COM_BANCADA=1` e faz essas
conferências sozinho (aceite ligado = não atualiza; se o processo novo subir com aceite, a bancada é parada).

## 7. A IA responde antes de a ligação ser aceita

| Quando | Causa | Correção | Teste |
|---|---|---|---|
| 03/10 (bancada) | O agente de voz nasce junto com a ligação (`createCall` → `attachVoiceAgent`) e ouvia todo áudio que chegasse, mesmo com a ligação ainda tocando. Áudio que passa pelo relay antes do aceite virava "fala do cliente" e a IA respondia | 04/10: o agente nasce com a escuta TRAVADA (`HoldUntilAccepted`) e só libera quando a ligação é aceita (`AcceptedNow`, chamado em `wireCall/OnStateChange` quando `AcceptedAt` existe). Áudio de antes do aceite é jogado fora inteiro (nem VAD, nem pré-roll). Log: `voice: ligação aceita, a IA passa a ouvir` com `frames_ignorados_antes` | `TestAceite_IgnoraAudioAntesDoAceite`, `TestAceite_SemTravaOuveNormal` (`internal/voice/aceite_test.go`), `TestSimulador_NadaAntesDoAceite` |

Não mexer: o re-attach numa ligação já aceita (`broadcast.go`, "voiceAgent AUSENTE") não trava (`callAccepted`).

**Chaves SÓ DE BANCADA** (A1, 04/10; `cmd/server/aceite_teste.go`), para o ensaio IA × IA enquanto o aceite do §5 não
é consertado. Nunca na produção (`/saude-local` lista em `chaves_de_teste`):
- `HERMES_VOICE_ESPERA_ACEITE=false`: a IA ouve desde o começo (log WARN `a IA ouve antes do aceite`).
- `HERMES_TESTE_ACEITE_POR_RELAY=true`: na ligação que o Hermes FAZ, relay conectado + ~1 s de áudio do outro lado
  sem accept/reject/terminate = aceita (`internal/voip/call/aceite_presumido.go`; log WARN `aceite PRESUMIDO`).
  Testes: `TestAceitePresumido_*` (`internal/voip/call/aceite_presumido_test.go`).

## 8. Eco da própria IA vira "fala do cliente" / frase interna do Whisper chega na IA

| Quando | Causa | Correção | Teste |
|---|---|---|---|
| 31/07 | O eco da IA volta pela linha ~350 ms depois e era transcrito como se o cliente tivesse falado | Cauda de eco (`gateListen`): logo depois de a IA falar, só passa voz mais forte que o eco | `TestSimulador_EcoNaoViraFala` (eco de viva-voz, 15%, com atraso) |
| 03/10 | No silêncio o Whisper devolve o texto de contexto ("Ligação comercial em português do Brasil.") e a IA respondia a isso | `isBiasPromptEcho` no `stt.go` | `TestSTTDescartaEcoDoContexto`, `TestSimulador_FraseInternaNaoChegaNaIA` |
| 04–05/10 | Com áudio ruim o Whisper INVENTA texto mesmo com language=pt: "Ég komstu hjá hana." (ligação da dona), "En það er ennig þeirra.", "Tudududu…", "Sertu.", "Entendu.", "So where me miss miss per se." (ensaio IA×IA) — e a IA respondia | Filtro de confiança (`internal/voice/stt_confianca.go`): verbose_json com descarte por trecho (no_speech_prob/avg_logprob/compression_ratio) e descarte de texto que não é português (letras ð þ æ ø å ß, outro alfabeto, palavras de outro idioma em metade da fala, sílaba em loop). Tudo descartado = "não entendi", sem resposta. `HERMES_STT_CONFIANCA=false` desliga | `TestSTTConfianca_CasosReaisETextoNormal` (casos reais + falas PT curtas que têm que passar), `TestSTTConfianca_PorTrecho`, `TestSimulador_TranscricaoInventadaNaoChegaNaIA` |

## 9. Tempo de resposta piora sem ninguém perceber

O `TestSimulador_TempoDeResposta` mede, com transcrição 150 ms, IA 250 ms e voz 200 ms, o tempo do fim da fala até a
1ª voz (hoje ~1,1 s; limite 1,6 s). Se passar do limite, alguma etapa voltou a esperar outra sem precisar (ex.: a IA
esperando o "ahã" terminar, a voz sintetizada em série). Não aumente o limite pra passar: ache a etapa.

Duas peças que reduzem o tempo e não podem ser desfeitas sem querer (04/10):
- **Transcrição antecipada** (`internal/voice/stt_antecipado.go`): numa pausa da fala a transcrição já começa;
  no fim de fala, se o áudio é o mesmo, o resultado é aproveitado. Desde 05/10: UMA por fala, na 1ª pausa de
  400 ms (`HERMES_VOICE_STT_ANTECIPADO_PAUSA_MS`; antes saía em toda micro-pausa de 240 ms, 2,6 pedidos por fala e
  429 no Groq), e em recuo de 3 min no servidor quando a transcrição volta 429 (`HERMES_VOICE_STT_ANTECIPADO_RECUO_S`).
  Testes: `TestVAD_AntecipadaUmaPorFala`, `TestSimulador_AntecipadaUmaPorFala`, `TestEarlySTT_RecuoDepoisDe429`. Teste: `TestSimulador_TranscricaoAntecipada`
  (com o fim de fala de 840 ms da produção: ~1,23 s com ela, ~1,73 s sem ela; limite 1,55 s) e
  `TestSimulador_PausaNoMeioDaFraseNaoCortaAFala` (pausa no meio da frase não pode virar fala cortada).
  `HERMES_VOICE_STT_ANTECIPADO=false` desliga.
- **Aquecimento das conexões** (`internal/voice/warm.go`): no aceite da ligação, um HEAD sem chave abre a conexão
  com a transcrição, a voz e a IA. Teste: `TestAceite_AqueceConexoes`. `HERMES_VOICE_AQUECER=false` desliga.
