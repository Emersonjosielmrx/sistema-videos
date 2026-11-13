# Catálogo de efeitos para o veo (intro / vídeo / transições / propaganda / outro)

Todos CPU-only (ffmpeg), sem gastar crédito. Overlays = arquivos `.mov` com canal alpha
1080x1920 (escalados pro tamanho do vídeo) em `D:\hipercool-materiais\assets\overlays\elemental`.
Módulo que aplica: `montagem.py` (punch/overlay/transição) + `efeitos_imagem.py` (foto).

═══════════════════════════════════════════════════════════════════
## GRUPO 1 — TRANSIÇÕES COMPLEXAS (o "entre elas": vídeo→propaganda, etc.)
═══════════════════════════════════════════════════════════════════

### 1A. Transições ELEMENTAIS (overlay .mov na emenda — as mais "uau")
| nome | arquivo | dur | vibe |
|---|---|---|---|
| fogo   | trans_fire.mov  | 0.9s | explosão de fogo cobre a troca |
| gelo   | trans_ice.mov   | 1.0s | congela/estilhaça |
| rasgo  | trans_tear.mov  | 0.7s | rasga a tela (papel) |
| água   | trans_water.mov | 1.0s | onda/respingo |

### 1B. Transições GEOMÉTRICAS (xfade nativo ffmpeg — sem asset, encaixe perfeito)
- **Deslize:** slideleft, slideright, slideup, slidedown
- **Cortina:** wipeleft, wiperight, wipeup, wipedown
- **Círculo:** circleopen, circleclose, circlecrop
- **Diagonal:** diagtl, diagtr, diagbl, diagbr
- **Cobre/Revela:** coverleft/right/up/down, revealleft/right/up/down
- **Fatia:** hlslice, hrslice, vuslice, vdslice
- **Aperto:** squeezeh, squeezev
- **Artística:** pixelize, radial, dissolve, distance, pagetear
- **Suave:** smoothleft/right/up/down, fade, fadeblack, fadewhite
- **Impacto:** punch, snap, rewind, zoomin, fadefast

═══════════════════════════════════════════════════════════════════
## GRUPO 2 — EFEITOS DE IMPACTO / OVERLAY (sobre o vídeo em movimento)
═══════════════════════════════════════════════════════════════════

### 2A. Impacto/energia (curtos, pra gancho e pontuação) ⭐ os que você citou
| nome | arquivo | dur |
|---|---|---|
| raio       | fx_lightning.mov | 0.7s |
| fogo       | fx_fire_v2.mov   | 1.6s |
| olhos de fogo | fx_fireeyes.mov | 1.6s |
| glitch     | fx_glitch.mov    | 0.6s |
| chiado TV  | fx_tvoff.mov     | 0.8s |
| shockwave  | fx_shockwave.mov | 0.6s |
| estilhaço  | fx_shatter.mov   | 1.0s |
| impacto    | fx_impact.mov    | 0.9s |
| zoom punch | fx_zoompunch.mov | 0.8s |
| radial zoom| fx_radialzoom.mov| 0.8s |
| speedlines | fx_speedlines.mov| 0.8s |
| desintegra | fx_disintegrate.mov | 0.9s |
| tremor     | fx_quake.mov     | 1.0s |
| explosão numérica | fx_bignumber.mov | 1.8s |

### 2B. Cinematográfico/atmosfera
| nome | arquivo | dur |
|---|---|---|
| portal     | fx_portal.mov   | 1.4s |
| godrays (raios de luz) | fx_godrays.mov | 1.6s |
| divino     | fx_divine.mov   | 1.4s |
| spotlight  | fx_spotlight.mov| 1.7s |
| cinebars (barras cinema) | fx_cinebars.mov | 0.9s |
| flashback  | fx_flashback.mov| 1.4s |
| daydream   | fx_daydream.mov | 2.0s |
| neon       | fx_neon.mov     | 1.5s |
| bokeh      | fx_bokeh.mov    | 1.5s |
| fumaça     | fx_smoke.mov    | 0.9s |
| noite estrelada | fx_nightsky.mov | 1.6s |

### 2C. Partículas/ambiente (cobrem a tela)
chuva (fx_rain), neve (fx_snow), folhas (fx_leaves), pétalas (fx_petals),
vento (fx_wind), bolhas (fx_bubbles), confete (fx_confetti), fogos (fx_fireworks),
sparkle (fx_sparkle), starburst (fx_starburst), emoji rain (fx_emojirain).

### 2D. Emoção/reação (anime style)
raiva (fx_anger), sangue (fx_blood), blush (fx_blush), coração (fx_hearts/fx_heartbeat),
gota de suor (fx_sweatdrop), exclamação (fx_exclaim), interrogação (fx_question),
onomatopeia (fx_onomatopeia), grito (fx_shoutscale), versus (fx_versus).

### 2E. Mascote (garota-propaganda, 15 poses) — ótimo pra propaganda
fx_mascot + _angry/_cheer/_cry/_laugh/_love/_point/_popcorn/_shock/_shy/_sleepy/
_surprise/_think/_thumbsup (todos ~1.8s).

### 2F. Social/CTA (pra propaganda e fim de vídeo)
subscribe (fx_subscribe), like burst (fx_likeburst), share (fx_share),
notify/sino (fx_notify), seguir seta (fx_followarrow), watch to end (fx_watchtoend),
CTA link bio (fx_ctalinkbio), comentário (fx_comment), salvar (fx_save),
lower third (fx_lowerthird), status window (fx_statuswindow), siren alert (fx_sirenalert).

### 2G. Legenda animada (se um dia quiser texto com efeito)
fx_cap_* (14 estilos): neon, gold, glowsweep, pumpbeat, scalepunch, shake, slideup,
typeline, underline, wave, zoomdrop, bounce, boxhi, flip3d, blurin (2.6-3.0s cada).

═══════════════════════════════════════════════════════════════════
## GRUPO 3 — MOVIMENTO DE CÂMERA (crop animado no vídeo / zoompan na foto)
═══════════════════════════════════════════════════════════════════

### 3A. No VÍDEO do Veo (montagem.punch_gancho — crop animado, pontual)
- **punch-in** — zoom rápido de impacto 1.0→1.12 no gancho (0-1.5s). ⭐ recomendado
- (zoom contínuo é possível mas embrulha o movimento do Veo — usar com parcimônia)

### 3B. Na FOTO estática (efeitos_imagem — 8 estilos, ~8s)
zoom_in, zoom_out, pan_right, pan_left, pan_up, pan_down, dynamic_tilt (2.5D fake),
punch_in. + banco enorme de zoompan cinematográficos no historias-em-frames
(dolly, orbit, handheld, whipzoom, crashzoom) portáveis se quiser mais variedade.

═══════════════════════════════════════════════════════════════════
## RECEITA SUGERIDA (fluxo do vídeo veo, do começo ao fim)
═══════════════════════════════════════════════════════════════════
1. **INTRO** (0s): overlay de abertura — chiado TV / glitch / portal / raio
2. **GANCHO** (0-1.5s): punch_gancho no vídeo + overlay de impacto (raio/shockwave)
3. **CLÍMAX** (meio): overlay pontual (fogo / speedlines / godrays) no beat forte
4. **TRANSIÇÃO** (fim do vídeo → propaganda): trans_fire/ice/tear/water
5. **PROPAGANDA**: card com Ken Burns (efeitos_imagem) + mascote + CTA social (subscribe/like)
6. **OUTRO** (fim): watch-to-end / subscribe / fade

Rotação anti-repetição: variar o efeito por canal/vídeo pra não ficar sempre igual.
