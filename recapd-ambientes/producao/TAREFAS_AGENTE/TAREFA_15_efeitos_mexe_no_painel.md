# TAREFA 15 — Efeitos que MEXEM NO PAINEL (catálogo grande)

> ✅✅ TODOS OS 46 APROVADOS pela usuária (2026-07-01) após ver as 5 demos (grupos A–E). Pode implementar TODOS.

> Aprovado pela usuária (2026-06-30): NÃO são overlays decorativos por cima — são efeitos que
> transformam a PRÓPRIA imagem do painel (zoom, recorte, máscara, camadas). Esse é "o caminho".
> Encaixar conforme o efeito: uns como TRANSIÇÃO (entre quadros), outros DENTRO do quadro (durante a fala).
> REGRA: nada de P&B / mudar cores (rejeitado). Movimento/recorte/máscara/tempo, sim.

## Estado dos protótipos — ✅ TODOS OS 46 PROTOTIPADOS (2026-06-30/07-01)
- Protótipos validados (standalone ffmpeg) em `_testes/proto_<nome>.mp4`. Frame-cobaia: `_testes/_frames/painel_teste*.png`.
- Recorte de personagem: `rembg` (já no venv) gera PNG alpha em ~3.8s/frame. Ex.: `_frames/painel_teste_cut.png`.
- DEPTH REAL: `bin/parallax_engine.py::get_depth(img,(W,H))` (Depth-Anything V2 Small, CPU, cacheado).
  Ex. gerado: `_frames/painel_teste_depth.png`. As 3 camadas near/mid/far em `_frames/L_{near,mid,far}.png`.
- Comandos ffmpeg EXATOS de cada efeito: ver `_testes/COMANDOS_PROTOTIPOS.sh` (copiar/adaptar por painel).
- Demos por grupo (abertas p/ aprovação): `_testes/DEMO_{A,B,C,D,E}_*_20260630.mp4`.
- Grupo E (texto) é HyperFrames (HTML→MOV alpha) em `D:\hipercool-hyperframes\compositions\fx_{wordstrike,typewriter,shoutscale,wordpop}.html`; MOV já em `elemental/`.

## ⚠️ Notas técnicas (build de ffmpeg local)
- `drawtext` SEGFAULTA (freetype quebrado) — não usar p/ rótulo; texto via HyperFrames overlay.
- `boxblur eval=frame` e expr dinâmica em `lenscorrection` NÃO aceitos → animar via `sendcmd` ou `zoompan`.
- Imagem estática precisa de `-loop 1 -t N` na entrada (senão overlay/sendcmd geram 1 frame só).
- `zoompan` com `-loop`: cada frame de entrada vira `d` frames → usar 1 frame de entrada + `-t`.

---

## A) ZOOM / CÂMERA (a imagem se move) — usar como movimento DENTRO do quadro
| nome | tem proto? | encaixe | o básico |
|---|---|---|---|
| facezoom | ✅ | dentro | zoom suave no rosto/terço superior |
| dollypush | ✅ | dentro | câmera anda pra dentro lento (drama) |
| whipzoom | ✅ | transição | chicote rápido pro detalhe + motion blur |
| pulsezoom | ✅ | dentro | micro-zoom pulsante (tensão/batida) |
| rackfocus | ✅ | dentro | foco viaja nítido→desfoque→nítido (gblur via sendcmd) |
| dollyzoom | ✅ | dentro | vertigo: zoom in + "afasta" (escala dupla) |
| orbit | ✅ | dentro | leve giro/pan circular ao redor do centro |
| panLR / panUP | ✅ | dentro | varredura horizontal/vertical (revela a cena) |
| handheld | ✅ | dentro | micro-tremor de câmera na mão (documental) |
| breathing | ✅ | dentro | zoom respirando bem leve (loop calmo) |
| snapzoom | ✅ | transição | 2-3 zooms em degrau (snap) sincronizados a batida |
| kenburns-diag | ✅ | dentro | pan diagonal + zoom (clássico, falta o diagonal) |

## B) TEMPO / IMPACTO (mexe na velocidade/estado da imagem)
| nome | tem proto? | encaixe | o básico |
|---|---|---|---|
| freezeimpact | ✅ | dentro | zoom-punch + congela + flash (golpe anime) |
| shockwave | ✅ | transição | onda elástica de zoom a partir do centro |
| speedlines-zoom | ✅ | dentro | zoom rápido + linhas de velocidade radiais |
| stutter | ✅ | transição | trava-destrava (frame hold staccato) na batida |
| rewind | ✅ | transição | mini-retrocesso (reverse curto) p/ flashback |
| slowmo-in | ✅ | dentro | desacelera entrando no momento-chave |
| double-take | ✅ | dentro | zoom, volta, zoom de novo (reação surpresa) |
| heartbeat-zoom | ✅ | dentro | 2 pulsos rápidos de zoom (susto/medo) |

## C) MÁSCARA / CORTE GEOMÉTRICO (a tela se reorganiza) — quase tudo TRANSIÇÃO
| nome | tem proto? | encaixe | o básico |
|---|---|---|---|
| irisclose | ✅ | transição | fecha em círculo apertando no centro |
| splitreveal | ✅ | transição | tela racha ao meio, próximo painel atrás |
| mangaslide | ✅ | transição | painel desliza por cima (virar página) |
| comicgrid | ✅ | transição | divide em 4 quadrinhos entrando + fecha no centro |
| irisopen | ✅ | transição | abre do círculo (inverso do irisclose) |
| wipe-diag | ✅ | transição | corte diagonal estilo mangá |
| barn-door | ✅ | transição | abre/fecha como cortina dos 2 lados |
| panel-shatter | ✅ | transição | painel quebra em cacos (já temos shatter overlay; aqui é a IMAGEM quebrando) |
| clock-wipe | ✅ | transição | varredura radial tipo relógio |
| blinds | ✅ | transição | persianas/tiras horizontais trocam a imagem |
| zoom-transition | ✅ | transição | zoom estoura até branco → próximo painel (luma) |
| spin-blur | ✅ | transição | gira+borra saindo, entra o próximo |
| page-curl | ✅ | transição | canto da página enrola (curl) — pode precisar HyperFrames |

## D) RECORTE DE PERSONAGEM + CAMADAS (rembg + parallax) — ⭐ o caminho preferido
| nome | tem proto? | encaixe | o básico |
|---|---|---|---|
| parallaxcut | ✅ | dentro | fundo zoom lento desfocado, personagem desliza em velocidade diferente |
| popout | ✅ | dentro/transição | personagem cresce e salta pra fora, fundo recua e desfoca |
| ghosttrail | ✅ | dentro | personagem deixa eco/rastro ao mover |
| parallax-3layer | ✅ | dentro | frente/meio/fundo em 3 velocidades (usar parallax_engine) |
| bg-blur-focus | ✅ | dentro | só o fundo desfoca, personagem nítido (profundidade) |
| char-slidein | ✅ | transição | personagem entra deslizando sobre o novo fundo |
| char-bounce | ✅ | dentro | recorte com micro-bounce/squash (vida/cômico) |
| float | ✅ | dentro | recorte flutua suave (idle, respiração) |
| depth-dolly | ✅ | dentro | câmera "atravessa" as camadas (push com paralaxe) |
| shadow-lift | ✅ | dentro | personagem ganha sombra projetada e descola do fundo |
| duplicate-clones | ✅ | dentro | 2-3 cópias do recorte em fileira (multidão/poder) |
| spotlight-cut | ✅ | dentro | escurece fundo, só o recorte do personagem fica iluminado |

## E) TEXTO QUE É O EFEITO (sincronizado com legenda/áudio)
| nome | tem proto? | encaixe | o básico |
|---|---|---|---|
| word-strike | ✅ | legenda | ⭐ palavra proibida aparece sendo RISCADA → troca pela permitida (a falada). EXIGE sincronia perfeita com a legenda (pendurar em `_CLIP_ABS_STARTS`, mesmo relógio). Aproveitar a substituição de censura que já existe. |
| typewriter | ✅ | dentro | frase digitada char-a-char (suspense) |
| shout-scale | ✅ | dentro | palavra cresce até encher a tela quando grita |
| word-pop | ✅ | dentro | palavra-chave salta em cima do ponto da fala |

---

## Como entregar pro implementador (sem mexer no .py agora)
1. Cada efeito = um builder ffmpeg standalone (entrada: painel PNG [+ recorte alpha]; saída: clipe).
2. Os de RECORTE chamam `rembg` 1x por painel (cachear o PNG alpha por painel; é caro).
3. Encaixe sugerido na coluna "encaixe": `transição` entra no lugar do xfade entre clips;
   `dentro` substitui/soma ao zoompan do clip; `legenda` casa no relógio das legendas.
4. Roteamento por contexto (igual elemental_transitions): keyword/emoção → efeito. Ex.:
   "olhou/encarou"→facezoom, "de repente"→freezeimpact, "lembrou"→rewind, troca de cena→mangaslide.
5. NÃO repetir o mesmo efeito em quadros consecutivos (regra do projeto p/ SFX, vale aqui).
6. Validar SEMPRE com ffprobe (dur/alpha). Notas técnicas do build acima são obrigatórias.

## Demos já geradas p/ a usuária aprovar (em _testes/)
- `PAINEL_11efeitos_demo_20260630.mp4` (grupos A/B/C)
- `PAINEL_camadas_recorte_demo_20260630.mp4` (grupo D: parallaxcut, popout, ghosttrail)
- `CAT_NOVA_7efeitos_demo_20260630.mp4` (overlays leva anterior — contexto)

---

## LEVA 2 (2026-07-01) — grupos D+/F/G/I/J/K — ✅ APROVADOS pela usuária (2026-07-01)
> VEREDITO: TODOS aprovados. D+ é a família DESTAQUE (implementar com prioridade).
> ⚠️ EXCEÇÃO grupo F (multi-painel): ATRAPALHA A LEITURA → usar SÓ em momentos muito específicos
>   SEM BALÕES de fala. Regra de roteamento: nunca disparar F em clip que tenha balão/texto no painel.
> 44 efeitos novos. Protos em `_testes/proto_<nome>.mp4`. Demos: `_testes/DEMO_{Dplus1,Dplus2,F,G,I,J,K}_*.mp4`.
> Reusam: recorte rembg (`_frames/painel_teste_cut.png` + `painel_teste2_cut.png`), depth (`L_{near,mid,far}.png`),
> overlays de partícula já em `elemental/` (fx_snow/godrays/leaves/smoke/petals/sparkle/bokeh).

### D+ RECORTE (24) — ⭐ família preferida
Movimento: charwalk, charapproach, charretreat, charturn, charlean, charorbit
Física: falldrop, shakefear, launchout, risehero, squashjump, impactrecoil  (= cobre o grupo H)
Multi-char: twocharface, crowdclone, swapfocus, ganglineup
Profundidade(depth): dofpull, fogbehind, particlesdepth, bgslidedepth
Destaque: outlineglow, freezechar, popframe, doubleexpose

### F MULTI-PAINEL (5): splitscreen2, gridmontage, pipinset, filmstrip, stackcascade
### G CINEMA (4): letterboxin, aspectpunch, tiltdutch, crashzoomout
### I ATMOSFERA/DEPTH (3): fogdepth, lightraysdepth, snowdepth  (partícula ATRÁS e/ou À FRENTE do recorte)
### J REVELAÇÃO (4): spotlightsearch, scratchreveal, pixelresolve, crackreveal
### K RITMO/ÁUDIO (4): beatpump, flashcut, shakeonhit, strobeaccent
> K é MOCK (batida ~2/s fixa). Na integração, plugar no BPM real da trilha (ver moods.json/análise de áudio).

### Notas técnicas LEVA 2 (somam às anteriores)
- `gblur ... eval=frame` NÃO aceito neste build → animar blur via `sendcmd` (ver _dof_bg.cmd/_sf_a/_px.cmd).
- `hstack` exige `fps=25` + mesma dur em todas as entradas (usar split, não re-loop).
- Efeitos com overlay .mov herdam a dur do overlay (~1.5s) → loopar o overlay na integração.
- Comandos exatos desta leva: adicionar ao `_testes/COMANDOS_PROTOTIPOS.sh` (mesma estrutura de funções).

## LEVA 3 (2026-07-01) — D++ (6) — ✅ APROVADOS
Novas sub-famílias do recorte (não repetem leva 1/2). Builders Dp_* no COMANDOS_PROTOTIPOS.sh.
- parallaxtilt: fundo inclina/gira, personagem firme (câmera girando o cenário)
- breathcut: personagem "respira" (micro-escala) sobre fundo nítido
- pushincut: fundo desfoca+recua, personagem cresce p/ câmera (impacto emocional)
- sliderevealcut: personagem entra deslizando ENQUANTO o fundo troca de painel (transição c/ pessoa)
- heartbeatcut: personagem pulsa + fundo escurece na batida (susto)
- tiltshiftcut: fundo desfoca topo/base, personagem nítido no meio (miniatura/foco)
Demo: _testes/DEMO_Dplus3_recorte_novos_20260701.mp4

## LEVA 4 (2026-07-01) — famílias NOVAS L/N/O/P (14) — ✅ APROVADAS
Mecânica inédita (não repetem A–K/D+). SEM cor/P&B. Builders L_*/N_*/O_*/P_* no COMANDOS_PROTOTIPOS.sh.
- L WARP (4): ripple, heathaze, underwater, bulge — deformam a geometria (geq/lenscorrection via sendcmd)
- N ESPELHO (3): waterreflection, mirrorsplit, kaleidoscope — reflexo/simetria (split+flip+stack)
- O 3D/PERSPECTIVA (4): cardflip, perspectivetilt, perspectiveswing, dooropen — perspective/scale animado
- P DESINTEGRAÇÃO (3): dispersion, pixeldissolve, graindissolve — pixel vira partícula (noise/gblur via sendcmd)
> NOTA: graindissolve gera arquivo pesado (granulado); dispersion é genérico — ambos melhoram com
>   partículas de verdade via HyperFrames se quiser refinar. Os outros 12 estão sólidos.
> Demos: DEMO_{L_warp,N_espelho,O_3d_perspectiva,P_desintegracao}_20260701.mp4

## LEVA 5 (2026-07-01) — R/U/T/M/Q (16) — ✅ APROVADAS
Builders R_*/U_*/T_*/M_*/Q_* no COMANDOS_PROTOTIPOS.sh.
- R BORDA (3): vignettepulse, frameclosein, borderglow — foco por moldura/vinheta
- U ROTAÇÃO (3): rollcw, spinin, tumbletransition — giro/roll (tumble é transição)
- T ECHO/RASTRO (3): echotrail, motionsmear, strobetrail — eco do painel inteiro em movimento
- M LUZ (4): lightsweep, lightningflash, glowpulse, spotlightfollow — ⚠️ MEXEM EM BRILHO (aprovado mesmo assim)
- Q GLITCH (3): shakeglitch, scanlines, blockglitch — ⚠️ MEXEM EM TEXTURA (aprovado; não vira P&B/cor)
> ESGOTAMENTO: com esta leva, o espaço de mecânicas DISTINTAS acabou. Novos efeitos daqui = combinações
>   das famílias existentes (ex: warp+luz, recorte+glitch), não mecânica inédita.
> Demos: DEMO_{R_moldura,U_rotacao,T_echo_rastro,M_luz,Q_glitch}_20260701.mp4
