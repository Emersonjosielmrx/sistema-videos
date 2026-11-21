# Auditoria de falhas silenciosas — 20/11/2026

Pedido da dona: "isso já está assim há uma semana, não pode acontecer; tinha que ser consertado automaticamente pelo
vigia; se o conserto não funcionar, passar com urgência para o chat; analisar quantos processos têm esse tipo de erro".

Método: varredura de ~290 logs (D:\ms-energy, D:\postador-de-videos, D:\video-fila, recap, veo, hipercool, Fish, Flow)
dos últimos 3 dias. Os logs com muito erro e pouco ou nenhum sucesso foram conferidos um a um.

## REAIS (estavam quebrados sem ninguém saber)
| Processo | Desde | Causa | Situação |
|---|---|---|---|
| Carrossel Advance Solar | 13/11 | Instagram responde 200 VAZIO ao configure_sidecar; o fallback pelo Chrome só pegava "spam" | ✅ CONSERTADO e confirmado (13:33, perfil 241→242) |
| Carrossel Globo Solar | 13/11 | mesma causa (usa o mesmo postar) | conserto aplicado; posta às 14:51 (espera os 90 min após o Reel) |
| Shorts no PC2 (parceiro) | 16/11 | anime_discover.py e landscape_filters.py CORROMPIDOS no PC2 (bytes nulos) — todo Short morria em 1 s | ✅ CONSERTADO (cópia boa do PC1, import ok, pausa tirada) |
| Longo de teste da voz nova (Fish) | 20/11 | fish_nuvem.py: variável `t` sobrescrita → TypeError antes da 1ª frase; 0/558 frases no Fish | ✅ CONSERTADO + erro do Fish agora vai pro pipeline.log; refazendo |
| Baixador do YouTube | 19/11 | 1º pedido da fila (Short FustIdhmD00) barrava todo baixador e cada um parava 1-12 h | ✅ CONSERTADO (pedido pro fim; Mike/iki baixaram em 1 min) |
| rclone da hermes-staging | ? | token do Drive expirado (invalid_grant) — banco de falas não rodava | ✅ CONSERTADO (conf da prod) |
| Bot do Telegram "producao" | 12/11 | Telegram responde 502 até no getMe — bot com problema do lado do Telegram | 🙋 DONA: conferir no @BotFather |

## FALSOS ALARMES (o processo funciona; o log só não tinha a palavra procurada)
reagendar_nobre (12 feitos hoje de manhã), instagram_auto (postou 4+4 hoje; "PROXY FORA" = espera a próxima rodada),
antecipar_agendados (sucesso termina em ": ok"), checar_canais (usa " OK "), produto_videos (147 [OK]),
metricas_rede (HTTP 401 cai pro Chrome, que lê), vitrine/painel (timeouts do painel do PC2).

## A OLHAR (ruído conhecido, não param produção)
fabrica_fish (token falha em contas específicas: emersonjosiel2026 313x, msenergypara 118x — a fábrica segue com as
outras), gemini-tts (modelo desativado desde 15/10 — trocado), sinais_shorts/aprendizado (Traceback a investigar).

## O QUE MUDOU PARA NÃO REPETIR
- `vigilancia.med_sem_sucesso` + `config_processos_vigiados.json`: cada processo tem prazo máximo sem sucesso. Passou =
  🚨 URGENTE no Telegram NA HORA + caso aberto pro conserto automático. Desliga: VIGIA_SEM_SUCESSO=0.
- `relatorio_ronda.py`: a ronda abre com "🚨 PROCESSOS PARADOS — consertar AGORA" (o chat da ronda conserta na hora).
- Processo novo = 1 linha no config (log, palavra de sucesso, horas).

## Rodada das 21h (relatório completo)
| Processo | Situação | O que fiz |
|---|---|---|
| Disco D | 196 KB livres (100%) | apaguei a cópia local do longo QwY2 (3,1 GB, conferido igual no Drive) + prints de teste; Shorts da reserva (motor antigo) indo pro Drive (8 GB, confere tamanho antes de apagar) |
| Gemini sem navegador (imagem/vídeo) | 0 ok desde 05:12 (12% no dia); Gemini responde "Are you signed in? I can search for images, but can't create any" em TODAS as contas — a rota HTTP chega como deslogada pra geração de mídia (mudança do lado do Google ~05-06h) | o Flow cobre (153 imagens hoje). Precisa capturar o pedido novo do site (chat "navegador sem navegador", fechado) |
| Longo Vilão 2 (4,6 GB) | travou 2x no Whisper e marcou 2 contas como "ruim" | tirado da fila (_fila_parados) |
| STI (máquina) | fora do ar (ssh sem resposta) | dona: ver se está ligada |
| Bot Telegram "producao" | 502 no getMe | dona: @BotFather |
| Melhorador dos longos | 43 falhas = modelos principais sem cota (429); a reserva Gemini aplicou 2 consertos hoje | funciona; só lento |
| Instagram contas de vídeo | 0 desde 07h | NORMAL: regra da dona 14/11 (só 5 contas de foco, máx 2/dia) — já bateram o limite |
