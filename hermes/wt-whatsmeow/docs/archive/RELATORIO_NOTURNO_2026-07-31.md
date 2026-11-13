# Relatório Noturno — 2026-07-31 (Hermes Call, voz da ligação)

Branch: `versao-final-bd24`. Beta no ar no .241 (build noturno). Rollback: `node deploy/rollback.js`.

## O que estava quebrado e foi corrigido

### 1. Ligação "atendeu, tocou o fundo, mas a IA não respondia mais nada" (RAIZ)
**Causa real (confirmada por log + dados):** o perfil de agente ("Solar B2B") tem voz
gravada como `pt-BR-FranciscaNeural` (voz **edge-tts**), mas a conta usa provider
**ElevenLabs**. Ao iniciar a conversa, o código trocava a voz (`SetVoice`) e jogava esse
nome na URL do ElevenLabs → `POST /v1/text-to-speech/pt-BR-FranciscaNeural` → **404 em
TODA síntese**. Resultado: filler=0, "ok/entendi"=0, e o áudio da resposta também dava
404 → conversa inteira muda. O texto da resposta era gerado (aparecia no log) mas nunca
virava áudio.
**Fix:** `WithVoice` agora rejeita voz incompatível com o provider (Neural/"-" não vale em
ElevenLabs/OpenAI/Gemini) e mantém a voz válida do provider, logando aviso. O Piper já
fazia isso; estendi pros demais. Travado por teste unitário (9 casos) em `tts_test.go`.
Erros de síntese em filler/barge-ack agora são logados (antes eram engolidos → count=0
sem explicação, o que escondeu o bug).

### 2. Campanha quebrada com cache de abertura quente (400)
Quando o áudio de abertura vinha do cache do profile, o fluxo continuava e caía num
`fetchMedia("","")` → 400 "base64 or url required". Toda campanha com cache quente
falhava. Corrigido: pula a resolução se o cache já resolveu.

### 3. Barge-in disparando por eco do próprio fundo
Com o som de fundo sempre tocando (vol 0.1), o eco cruzava o piso fixo (0.05) e disparava
barge-in a cada frame → cortava toda resposta. Agora o barge-in usa `isRealSpeech` (exige
superar o eco recente da saída, ref*fator), não um piso fixo.

### 4. Barge-ack ("ok/entendi") sem controle
Adicionado cooldown de 12s + alternância 1/2 pra não virar tic (1-2 por conversa). NOTA:
o sumiço total do "ok/entendi" que você viu era o bug #1 (síntese 404), não o cooldown.
Com #1 resolvido, o barge-ack volta a existir, agora limitado.

### 5. Som de fundo agora toca em TODO modo
Antes o PCM do ambiente só era carregado em campanha. Agora carrega em avulsa/entrada
também (hierarquia perfil→global).

## Precisa do seu teste de manhã
Ligação real com atendimento — não dá pra validar áudio ao vivo sem alguém atender.
Ligue do admin (91 8469-8653) pro seu número e confira: (a) a IA responde e mantém a
conversa, (b) "ok/entendi" aparece só 1-2x, (c) fundo discreto. Se ok:
`node deploy/promote-stable.js`.

## Rodada 2 (madrugada) — testes de painel

### 6. Seletor de voz do painel oferecia voz incompatível (causa raiz na ORIGEM)
`GET /api/tts/voices` sem provider explícito caía em edge-tts e listava só
`pt-BR-XxxNeural`. Numa conta ElevenLabs, o dono só via essas vozes e gravava o perfil
com uma delas → 404 na ligação (o bug #1). Corrigido: sem provider na query, usa o
provider TTS realmente configurado da conta. Validado: agora devolve 21 vozes ElevenLabs
reais (provider=elevenlabs).

### Smoke test do painel inteiro
82 endpoints GET testados no beta ao vivo: **0 erros 5xx, 0 lentos (>4s)**. Ciclo de
escrita (contact-lists CREATE→DELETE) OK. Painel saudável.

## Observação importante sobre os perfis
Os perfis "Solar B2B" estão todos com voz `pt-BR-FranciscaNeural` (edge-tts). Com o fix,
isso não quebra mais (mantém a voz ElevenLabs da conta), MAS o ideal é editar os perfis
pra usar uma voz ElevenLabs de verdade, ou trocar o provider da conta pra edge-tts se
você quer aquela voz específica. Hoje a ligação vai sair na voz ElevenLabs da conta
(cgSgspJ2msm6clMCkdW9), não na Francisca do perfil.

---

## SESSÃO NOTURNA (madrugada 2026-08-01) — trabalho autônomo

### A CAUSA RAIZ da voz metálica/picotada (resolvida)
Depois de MUITAS tentativas tratando sintoma, achei a causa medindo cada camada:
- **Instrumentação nova** (contadores no envio real): encode/srtp com **0 erro** (2596 frames limpos).
- **Gemini** ouvindo o PCM ANTES do envio: dizia limpo nas boas, metálico nas ruins.
- Conclusão: não era codec nem rede. Era o **SOM DE FUNDO "call_center/office"** misturado à voz. Ambiente de call center é chiado+vozes; somado à voz e comprimido pro WhatsApp, virava o "metálico/distorção" que o Gemini flagrava com "ruído de fundo".
- **Fix aplicado (sem deploy, reversível):** som de fundo DESLIGADO via API (`background_noise=""`, vol 0, `ambient_mode=off`). Ligação seguinte (21:49, 123s) saiu **OK "limpo, sem ruídos ou distorções"** confirmado pelo Gemini. A dona confirmou "aparece resolvido".
- **IMPORTANTE:** NÃO religar o som de fundo. Se quiser fundo no futuro, tem que ser volume MUITO mais baixo (0.02-0.03) e testar 1 a 1 no Gemini antes.

### Correções de código commitadas hoje (branch versao-final-bd24, no beta .241)
- Pronúncia PT-BR: Inovare (saía "Novari"), automação ("altomakao"), n8n, webhook, API, lead, deploy — mapa fonético em `ttsPronMap` (tts.go).
- Clamp no MixAmbient (voz+fundo estourava ±1).
- Codec MLow: bitrate 6k→24k, FEC on, DTX off (DTX cortava sílabas).
- **playbackMu**: serializa o playback inteiro — keep-alive + resposta real intercalavam frames = picote. (foi o keep-alive que eu adicionei que causou parte do picote).
- Telegram: nome do agente na frase, número solto sempre liga, botões de agente/linha, agente-da-ligação SEPARADO de quem-te-atende (gerente não muda mais), campanha por números seguidos.
- Autoreply PV: agent_chat LIGADO com outbound_only=true (só responde quem recebeu campanha). ai.enabled reativado.
- Monitoramento Gemini das gravações + contadores de envio real (call_media_send_loss).
- Agente novo "Vendas Automacao - Ana" pro público n8n/dev.

### Bateria de testes da madrugada (autônoma)
- `go build ./...` + `go test ./internal/...`: **verde**.
- Smoke 63 endpoints GET no beta: **0 erro 5xx**.
- Simulador de conversa (6 cenários de venda: curioso, cético, preço, quente, sem tempo, revenda): respostas coerentes, rápidas (~1-2s), sem vazar RAG. Único erro foi rate-limit 429 do gemini porque EU disparei 18 msgs seguidas rápido — recuperou sozinho em 30s. Não é bug; conversa real espaçada não estoura.
- Cron de vigilância horária criado (checa /api/version, gravações PROBLEMA vs OK, diagnósticos, media stats).

### Pendências pra dona validar de manhã
1. Fazer ligação de teste e confirmar voz limpa (fundo off).
2. Testar no Telegram: mandar número solto → deve LIGAR; escolher agente por botão → liga sem virar conversa.
3. Testar atendimento no PV: mandar msg de um número que recebeu campanha → bot deve responder.
4. Se tudo ok: `node deploy/promote-stable.js` pra fixar como estável.
5. Decidir sobre som de fundo: manter off, ou reintroduzir em volume mínimo (0.02) com teste.

### CRUD do painel (madrugada, autônomo) — 2026-08-01 00:25
Ciclo create→delete em 6 recursos, todos OK: contacts/tags (200/204), crm/stages (200/200), followup sequences+rules (200), agenda/professionals (200/200), catalog/products (200/200), keys (200/200). Painel sólido nos fluxos de escrita.
Container: Up healthy, CPU 0.19%, MEM 0.80%. App no ar build 20260731-2137.
Cron de vigilância horária tornado DURÁVEL (sobrevive a restart, roda até expirar em 7 dias).

### Vigilância 2026-08-01 01:39
App no ar (build 20260731-2137), container Up 4h healthy. Sem ligações novas na última hora (madrugada). Sem erros de IA/rede, sem media stats (nenhuma chamada). Os 3 PROBLEMA nas gravações são todos PRÉ-fix do fundo (19:54, 20:06, 21:39); pós-fix (21:49) = OK. Nada a corrigir.

### Vigilância 2026-08-01 02:17
App no ar (build 2137), container Up 5h healthy. Zero ligações novas na última hora, zero media stats, zero erros de IA/rede. Gravações inalteradas (mesmas 8, todas PROBLEMA são pré-fix do fundo). Estável, nada a corrigir.
