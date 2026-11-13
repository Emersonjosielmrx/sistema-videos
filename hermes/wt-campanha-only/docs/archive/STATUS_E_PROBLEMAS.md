# Inovare Hermes Call - Status e Problemas Conhecidos

## Deploy
- URL: https://hermes.inovareinteligenciaartificial.com
- API Key: InovareHermesCall2026SecretKey
- Stack: hermes_call (Docker Swarm)
- Imagem: inovare/hermes-call:latest
- Source: /opt/inovare-hermes-call

## Servicos ativos (confirmado 2026-07-05)
- WhatsApp sessao conectada (numero 559192438288, pareado via QR)
- Telegram bot: @Emerson_Hermes_call_bot (token 8825293273:AAF...)
- AI Agent: provider openai, model antigravity/gemini-2.5-flash-lite, base_url http://157.173.207.22:20128
- Voice Service: STT Groq (whisper-large-v3), TTS edge-tts (pt-BR-FranciscaNeural)
- Voice Agent: auto-attach em chamadas (VAD + STT + AI + TTS + playback)

## PROBLEMA PRINCIPAL: Chamadas nao tocam no destinatario

### Sintoma
- Call offer e enviado com sucesso (logs confirmam)
- WhatsApp retorna device-list VAZIO no usync query
- Destinatario nunca recebe a ligacao (nao toca)
- Acontece com TODOS os numeros testados (5591984698653, 5591985685106)
- Mesmo apos trocar mensagens de texto entre os numeros

### Diagnostico nos logs
O usync query retorna device-list vazio:
```
[WA/Recv] usync result -> devices -> device-list/ (VAZIO)
```
Isso significa que o servidor WhatsApp nao reconhece dispositivos de chamada para o destinatario.

### Causa raiz provavel
O numero 559192438288 foi pareado como DISPOSITIVO LINKED (secondary device, via QR code
em "Dispositivos conectados" do WhatsApp). Chamadas VoIP no WhatsApp multi-device
NAO sao suportadas em dispositivos linked - apenas o dispositivo principal (celular)
pode iniciar/receber chamadas.

O whatsmeow (lib Go usada) envia o call offer mas o servidor WhatsApp nao entrega
porque reconhece que quem esta iniciando e um dispositivo secundario.

### Possiveis solucoes
1. Registrar como dispositivo principal - usar um chip/numero dedicado exclusivo
   pro Hermes (conectar como celular, nao como dispositivo linked). Isso desconecta
   o WhatsApp do celular fisico desse numero.
2. Usar numero virtual (chip dedicado) - comprar um chip so pro bot, ativar
   WhatsApp nele como principal, e parear no Hermes.
3. Aguardar atualizacao do whatsmeow - a lib pode implementar chamadas via
   dispositivo linked no futuro.
4. Investigar issues no GitHub: https://github.com/tulir/whatsmeow/issues (buscar "call", "voip")

### Nota sobre mensagens vs chamadas
Mensagens de texto/midia FUNCIONAM perfeitamente via dispositivo linked.
O problema e EXCLUSIVO de chamadas VoIP.

## Funcionalidades que FUNCIONAM

### Telegram Bot (testado e confirmado)
- Recebe audios e transcreve automaticamente via Whisper (Groq)
- Processa texto com AI (Gemini via proxy)
- Responde em texto + audio (edge-tts, voz feminina PT-BR)
- Comandos: /start, /ligar, /sessoes, /status, /desligar, /ajuda

### Voice AI Pipeline (implementado, pendente de teste em chamada real)
- VAD: detecta fala/silencio em frames de 60ms
- STT: Groq Whisper API (whisper-large-v3, PT-BR)
- AI: Gemini via proxy OmniRoute
- TTS: edge-tts (pt-BR-FranciscaNeural) + ffmpeg -> PCM 16kHz
- Playback: 960 samples/frame, 60ms pacing, com barge-in
- Auto-attach em toda chamada criada

### API Externa para agentes
- POST /api/agent/call - iniciar ligacao
- POST /api/agent/hangup - encerrar
- GET /api/agent/status - status do sistema
- GET /api/agent/connect - info de conexao pra agentes externos

## Env vars configuradas no servico
- WACALLS_PUBLIC_IP=209.145.60.53
- WACALLS_UDP_PORT=50000
- WACALLS_MAX_CALLS=8
- WACALLS_API_KEY=<removido — ver cofre/VPS>
- WACALLS_PG_URL=postgres://hermescall:<removido — ver cofre/VPS>@hermes_postgres:5432/hermescall?sslmode=disable
- HERMES_TELEGRAM_TOKEN=<removido — ver cofre/VPS>
- HERMES_AI_PROVIDER=openai
- HERMES_AI_MODEL=antigravity/gemini-2.5-flash-lite
- HERMES_AI_API_KEY=<removido — ver cofre/VPS>
- HERMES_AI_BASE_URL=http://157.173.207.22:20128
- HERMES_STT_PROVIDER=groq
- HERMES_STT_API_KEY=<removido — ver cofre/VPS>
- HERMES_TTS_VOICE=pt-BR-FranciscaNeural

## Arquitetura dos arquivos (source em /opt/inovare-hermes-call)

cmd/server/
- main.go - entrypoint, env vars, flag parsing
- server.go - struct server, newServer
- session.go - Session, wireCall, createCall, attachVoiceAgent
- sessionmanager.go - SessionManager (field srv)
- callregistry.go - activeCall (cm, bridge, browserOpus, voiceAgent)
- httpapi.go - HTTP routes, CORS, auth middleware
- telegram.go - TelegramBot (text + voice messages)
- aiagent.go - AIAgent multi-provider LLM
- external_api.go - REST API pra agentes externos
- voiceservice.go - VoiceService (STT + TTS + attach agent)
- voice_helpers.go - sendTelegramVoice, decodeJSON

internal/voice/
- vad.go - Voice Activity Detection (energy-based)
- stt.go - Whisper STT client (Groq/OpenAI)
- tts.go - Edge-TTS subprocess + ffmpeg
- voiceagent.go - Orquestrador in-call (VAD->STT->AI->TTS->playback)

internal/voip/
- call/ - CallManager, audio pipeline, SRTP
- media/ - Codecs (MLow Opus), RTP, resample
- core/ - Types, VoipSocket interface
- signaling/ - WhatsApp call signaling
- transport/ - SCTP relay, STUN

deploy/
- docker-compose.swarm.yml - Stack Swarm com Traefik
- upload_and_build.py - Script SFTP + build (rodar do Windows)

## Como rebuildar
No Windows (precisa paramiko):
```
cd D:\inovare-hermes-call
python deploy/upload_and_build.py
```

Ou manualmente na VPS:
```
cd /opt/inovare-hermes-call
docker build --no-cache -t inovare/hermes-call:latest .
docker service update --image inovare/hermes-call:latest --force hermes_call_hermes-call
```

## Logs uteis
```bash
# Container ID
docker ps --filter name=hermes_call_hermes -q

# Logs sem debug (so INFO/WARN/ERROR)
docker logs $(docker ps --filter name=hermes_call_hermes -q) 2>&1 | grep -v DEBUG

# Logs de chamada
docker logs $(docker ps --filter name=hermes_call_hermes -q) 2>&1 | grep -i call

# Logs de voice/telegram
docker logs $(docker ps --filter name=hermes_call_hermes -q) 2>&1 | grep -iE "voice|telegram|transcri"
```
