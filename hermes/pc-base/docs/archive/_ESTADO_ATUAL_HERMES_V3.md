# Estado atual — Hermes Call v3 (2026-07-11)

## Feito e VALIDADO no ar
- **Fix chamada não tocava (DDD 91):** `normalizePhone` inseria 9 extra. Novo `(*Session).resolveCallPeer` (messaging.go) consulta `IsOnWhatsApp` e usa o JID real. Em 6 call sites (broadcast, masscall, httpapi doStartCall, telegram, aiagent, external_api). Dona ouviu o áudio → OK.
- **Biblioteca de áudios por conta:** audio_library.go (tabela audio_library, bytes BYTEA por user_id). Endpoints GET/POST /api/audios, GET/DELETE /api/audios/{id}. Broadcast aceita `audio_id` (reusa) e `save_audio_as` (salva). VALIDADO: CRUD + audio_id + persiste após redeploy.
- **UI painel (MassCallPage):** 3º modo "Áudios salvos" (lista+preview+deletar) + checkbox "salvar na biblioteca". Servido no painel (bundle contém as strings).
- **Bot Telegram principal (Hermes_call_bot):** comandos `/audios`, `/salvar <nome>`, `/tocar <n> <número>`. Deployado.
- **Comercial padrão:** Gemini voz Sulafat, ~40s, salvo na biblioteca como "Comercial Hermes (Sulafat)".

## Codado, NÃO deployado ainda (aguardando OK da dona pro rebuild)
- **Gerar áudio a partir de TEXTO (edge-tts) e ligar tocando** — pedido da dona 2026-07-11.
  - `cmd/server/telegram.go`: comando `/falar <número> <texto>` (liga na hora) ou `/falar <texto>` (guarda pendente → manda número depois / `/massa`). Helper `synthOgg` usa `voice.NewTTSClient(...).SynthesizeToOgg` (não depende de voiceSvc, que é nil sem STT). Reusa `doCallWithAudio`/`pendingAudio`. Help de /start e /ajuda atualizados.
  - `cmd/server/broadcast.go`: `broadcastRequest` ganhou `tts_message` + `tts_voice`; `handleBroadcast` sintetiza por edge-tts quando só vem texto. Mime salvo = audio/ogg.
  - Falta: rebuild na VPS (reinicia serviço ~1min) + `docker service update --force`. Não deployado por causa da regra "não parar serviço sem confirmação".

## Deploy
- Build na VPS: `_deploy_v3_retry.py` (keepalive + upload base64). SEMPRE seguir com `docker service update --force --image <sha>` (Swarm+latest não recria sozinho).
- Imagem atual: e4ccfec2 (server+client). Estável (Running).

## Falta teste da dona (só ela consegue)
- Comandos /audios /salvar /tocar no chat do Telegram principal (não dá pra simular por fora — HTTP 409, o server consome o polling).
- Tour guiado no browser (driver.js) — código compila e é servido, falta clicar pelos passos.

## Monitor (bot NOVO @Claude_code_emerso_nchat_bot, token 8740184682:...)
- `_monitor_bot.py send/poll/chatid` + cron a cada 3 min. Aguardando /start da dona pra capturar o chat_id.
- Esse bot é SÓ pra conversar com o Claude — NÃO é do sistema Hermes.

## Números
- 559185685106 (dona, DDD 91) — testar aqui. Internet instável (cai no meio, não é bug).
- 73988840045 (DDD 73) — não é da dona, dá no-answer.

## Codado em 2026-07-15 (Refactoring)
- **Integração de Webhooks Globais**: `webhook.go`. Suporte robusto para envio condicional multiplataforma com 4 canais (`webhook`, `telegram`, `whatsapp`, `app`). Fallback para rotinas HTTPS assíncronas `fire-and-forget` pra não engargalar o sistema e adição da `WebhookQueue` nativa.
- **Trial Expiration (10H)**: Trava para uso ilimitado grátis. A `auth_handlers.go` expulsa `403 Forbidden` mas **DEVOLVE O TOKEN** p/ permitir a `LoginScreen.tsx` (modificada para capturar `data.error === "trial_expired"`) renderizar a sessão para o usuário pagar / fazer upgrade. Tipado globalmente em `auth.User.TrialExpired()`. 
- **O‍mniRoute Proxy fix**: As tags de fallback falhavam recebendo `400 Invalid Model` (Gemini-3 Pro no proxy Antigravity não operava por estar antigo). Tag do proxy mapeada internamente no roteamento HTTPS pra resolver o problema sem necessidade de mudar as request no core de todos os arquivos.

## Metas Pendentes (Próximos Passos P0)
- **Dash e UI de Campanhas**: Implementar listagem e agregados (Métricas) no Painel Frontend.
- **Onboarding e Tour Guiado (driver.js)**: Integrar os passos nos tooltips já que o código compila na versão Client local.
- **Build / Deploy na VPS**: O código refatorado que está aqui (com a feature TTS e Trial) precisa da sua aprovação e que execute `docker service update --force --image <sha>` para ir ao ar oficial quando sentir segurança.
