# TAREFA 17 — Legenda cinética estilizada (17 estilos, liga/desliga + estilo fixo)

STATUS: [ ] pendente — ✅ APROVADO pela usuária (2026-07-01). Estilos prontos, faltam integrar.
PRIORIDADE: média. Frente independente dos efeitos de painel (T15/T16).

## A IDEIA (aprovada)
A legenda do narrador pode virar LEGENDA CINÉTICA (estilo TikTok/CapCut): as palavras animam
no ritmo da fala. A usuária aprovou e pediu: MÁXIMO de estilos + um BOOLEAN pra ligar/desligar +
poder FIXAR um estilo (trocar de estilo a cada frase fica esquisito → default = 1 estilo fixo por vídeo).

## O QUE JÁ EXISTE (reusar)
- 17 estilos prontos como composition HyperFrames (HTML→MOV alpha), em D:\hipercool-hyperframes\compositions\
  fx_{karaoke,wordbyword,cap_boxhi,cap_bounce,cap_slideup,cap_neon,cap_scalepunch,cap_shake,cap_wave,
  cap_flip3d,cap_blurin,cap_gold,cap_underline,cap_typeline,cap_zoomdrop,cap_pumpbeat,cap_glowsweep}.html
  → MOV já renderizados e copiados p/ workspace/assets/overlays/elemental/fx_<estilo>.mov
- Cada HTML aceita o texto real via HyperFrames --variables {"texto":"FRASE DO NARRADOR"}.
  (o MOV em elemental/ é só amostra com texto default; na integração renderiza-se por frase com o texto certo).
- bin/render_karaoke.py já existe (flag hyperframes_karaoke em hiper-pipeline.py:1517) — MESMO padrão de
  chamar HyperFrames e sobrepor. Base pra estender.
- effects_engine.py: render_subtitles / render_subtitles_progressive / render_subtitles_short + burn_subtitles.
  O relógio é effects_engine._CLIP_ABS_STARTS (mesmo das legendas atuais) — a legenda cinética PENDURA aqui.

## O QUE FAZER
1. Config nova (env/args), com DEFAULT seguro:
   - `CINEMATIC_SUBS=0|1` (boolean liga/desliga; default 0 = legenda normal atual).
   - `CINEMATIC_SUB_STYLE=<nome>` (fixa 1 estilo p/ o vídeo inteiro; default ex. "karaoke").
   - Opcional `CINEMATIC_SUB_ROTATE=0|1` (se 1, alterna estilos — mas AVISO: a usuária achou que trocar
     muito fica esquisito → manter 0 por default).
2. Quando CINEMATIC_SUBS=1: em vez de burn_subtitles normal, para cada frase do narrador renderizar a
   composition do estilo escolhido com --variables {"texto": <frase>} e sobrepor no tempo da frase,
   usando o MESMO relógio _CLIP_ABS_STARTS (sincronia perfeita com o áudio, igual às legendas atuais).
   Reaproveitar a lógica de render_karaoke.py (é o mesmo mecanismo HyperFrames→overlay).
3. Cache: legenda cinética por (estilo + md5 do texto da frase) → não re-renderizar frases repetidas.
4. Fallback: HyperFrames indisponível/erro → cai na legenda normal (burn_subtitles). Nunca travar/quebrar.

## CATÁLOGO DE ESTILOS (o que cada um faz)
| estilo | descrição |
|---|---|
| karaoke | palavra ativa acende amarelo + cresce (TikTok clássico) |
| wordbyword | palavras sobem e assentam uma a uma |
| cap_boxhi | palavra ativa ganha caixa rosa (highlight) |
| cap_bounce | palavras caem quicando |
| cap_slideup | deslizam de baixo |
| cap_neon | brilho neon ciano |
| cap_scalepunch | estouram do zero (punch) |
| cap_shake | entram tremendo |
| cap_wave | sobem em onda |
| cap_flip3d | giram em 3D |
| cap_blurin | surgem desfocadas e focam |
| cap_gold | dourado premium |
| cap_underline | sublinhado amarelo na palavra ativa |
| cap_typeline | aparecem tipo digitação |
| cap_zoomdrop | despencam de grandes p/ pequenas |
| cap_pumpbeat | pulsam na batida |
| cap_glowsweep | brilho varre palavra a palavra |

## REGRAS
- Legenda é APENAS do narrador (regra do projeto). Personagens têm balões, não legenda cinética.
- Sincronia é sagrada: pendurar em _CLIP_ABS_STARTS; validar que a legenda cobre a duração da fala.
- Persistir renders (cache por estilo+texto). Nunca re-renderizar frase já feita.
- Trabalhar LOCAL; validar com ffprobe; registrar em logs/night-shift.md.

## VALIDAR
- Self-test: render de 3-4 frases num estilo fixo, conferir sincronia com o áudio e legibilidade.
- Cap curto com CINEMATIC_SUBS=1 CINEMATIC_SUB_STYLE=karaoke ponta a ponta.
- Demo de referência dos 17 estilos: _testes/DEMO_5_estilos_legenda_17_20260701.mp4
