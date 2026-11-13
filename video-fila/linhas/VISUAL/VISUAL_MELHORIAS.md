# VISUAL — efeitos, transições e ritmo dos edits: A FAZER x JÁ FEITO (dona, 01/11/2026)

> "A ideia não é analisar textos, narrações ou tags, e sim visualmente os efeitos, transições, tudo visualmente, cada
> detalhe." Vale pra LONGOS e CURTOS e vem NA FRENTE das outras análises.

Mesma regra da lista dos longos (`D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md`): antes de implantar um `V-xx`,
`grep` do ID no código (achou = já feito, não refazer); implantou = `# V-xx` no código + mover pra JÁ FEITO (arquivo,
como desliga, como testou, com print/quadro do resultado). Achado novo só entra se não estiver em nenhuma das 3 listas.
Fechar a resposta com "Visual: X feitos, Y descartados, Z deixados".

Fonte: `D:\video-fila\linhas\VISUAL\referencias\<id>\VISUAL.md` (um por vídeo, com a decupagem em blocos.json).
Canais: `canais.json` (Noctryxae, Kuroroox, GOJO神, Dr1zzy). Análise: `visual.py` (tarefa EngenhariaReversaVisual).

## A FAZER
Evidência: T = Toji (lynJABr10N4, 1,28 mi), S = Sukuna (8Fyb0LXw1BU, 682k) — ambos Noctryxae. Ritmo dos dois: ~2,4–2,8
cortes/s no meio, ~1/s no fim; quase todo corte/punch cai no bumbo ou na caixa da música. O que cresce no clímax não é
o número de cortes: é a PILHA de efeitos por corte.


Confirmações do Sung Jin Woo (J, 63 s, Kuroroox — outro canal, mesmo padrão): V-01 4×, V-02 3×, V-07 3×, V-09 3×,
V-08 2×, V-05 2×, V-06 1×, V-03 1×; cortes caem na batida. Variação: "micro punch" 100→112% em 3 quadros, sem shake
nem RGB, nas batidas fracas (o combo completo V-01 fica só nas fortes).


Confirmações do MHA (M, 103 s): V-01 6×, V-02 6×, V-07 4×, V-05 3×, V-09 3×, V-06 3×, V-03 2× (2 quadros ANTES do
impacto). Ritmo: 2,4 cortes/s na subida, 3,2 no drop; bumbo = V-01, caixa = corte seco/whip, tempo fraco = micro punch.
4 vídeos de 2 canais diferentes repetem o mesmo kit: é padrão do gênero, não estilo de 1 editor.

(Os 12 do kit dos edits estão em JÁ FEITO. Achado novo entra aqui com o próximo ID livre.)

02/11 ~20h — 19 de 49 edits decupados (Noctryxae + Kuroroox). Contagem nos blocos.json: V-01 40×, V-07 28×, V-12 27×,
V-09 26×, V-08 24×, V-11 23×, V-02 22×, V-03 17×, V-05 14×, V-04 13×, V-06 12×, V-10 10× — o kit se confirma em todos.
(V-13 a V-17 implementados em 03/11 e movidos para JÁ FEITO abaixo.)

Visto 1× e deixado de lado por enquanto (não é do gênero ou é estilo de um vídeo só): fisheye/CRT/scanlines e slide de
jogos (Yuta/Minecraft, vídeo-paródia), grão de filme 35 mm, texto atrás do personagem com máscara de profundidade
(aJpPf7slzGc@40,2 — exige recorte do personagem), raios elétricos sobre a boca, meme colado com borda branca.

## JÁ FEITO
| ID | Efeito | Onde está no código | Desliga | Data / quem |
|---|---|---|---|---|
| V-01 | Combo de impacto (flash 2 quadros + zoom 1→1,22 em 0,07 s voltando em 0,2 s + shake que decai + rgbashift 0,15 s) na palavra pesada, cartão alerta/triunfo, ênfase criativa | `recapd-ambientes\producao\bin\fx_visual.py` (filtro), chamado em `fx_subtitles.burn_subtitles_ass` depois do upscale 1080p e antes da legenda | `ANIME_FX_VISUAL=0` | 01/11, chat dos longos. Teste: `D:\tmp_logs\cartoes_teste\fx_grade.jpg` |
| V-03 | Negativo de 2 quadros antes de palavra de revelação (revelou, verdade, traição, segredo...) | fx_visual.py (`_REVELA`) | idem | 01/11 |
| V-04 | Gancho em 3 degraus 100→120→140% (0,13 s / 0,27 s) com flash entre eles | fx_visual.py | idem | 01/11, conferido no quadro 0,2 s / 0,33 s |
| V-05 | Letterbox 10% por 2,1 s na tensão (cartão alerta, "de repente", perigo...) abrindo com flash | fx_visual.py (barra fixa com enable; o drawbox não anima altura por quadro, e a versão com t deixou o vídeo preto) | idem | 01/11, conferido no quadro 20,4 s / 22 s |
| V-08 | Grade esmagada `eq=contrast=1.35:saturation=1.3` por 2,5 s junto da tensão | fx_visual.py | idem | 01/11 |
| V-02 | Flash branco de 2 quadros no lugar do fade na troca de cena (início de cada frase), no máx. 1 a cada 12 s, longe dos outros efeitos | fx_visual.py (`troca`, cenas = offsets das frases em fx_subtitles) | `ANIME_FX_V02=0` | 01/11 noite; PREVIA4 0:12 / 0:26 / 0:41 |
| V-06 | Speed ramp no despertar: zoom +3% em 1,2 s e dispara +18% nos últimos 0,27 s, voltando em 0,25 s | fx_visual.py (zexp, `poder`) | `ANIME_FX_V06=0` | 01/11 noite; PREVIA4 0:38 |
| V-07 | Glow pulsante na palavra de poder (despertou/aura/olhos...): os claros do quadro viram bloom em screen SÓ na luminância (`format=yuv420p` antes; c1/c2 normal opacidade 1). 1º teste: quadro roxo/verde | fx_visual.py | `ANIME_FX_V07=0` | 01/11 noite; medido por cor média + glow_grade.jpg, PREVIA4 0:38 |
| V-10 | Glitch RGB 0,15 s na entrada do cartão de SISTEMA + som curto glitch_sistema.wav (0,4 s cortado do GLITCH SOUND EFFECTS, em assets/sfx) | fx_visual.py (`sistema` das marcas do anime_cartoes) + fx_detect.pick_sfx_for_text | `ANIME_FX_V10=0` / `ANIME_SFX_GLITCH=0` | 01/11 noite; PREVIA4 1:12 |
| V-11 | Brasas subindo (geq, sem arquivo: vai igual pro Kaggle), soma na luminância 0,9, 3 s, no despertar e no triunfo. 1º teste: pontos de 3 px invisíveis → 7 px + halo | fx_visual.py | `ANIME_FX_V11=0` | 01/11 noite; brasa_zoom.jpg, PREVIA4 0:38 |
| V-12 | Micro punch 100→106% (0,07 s sobe, 0,13 s volta) nas palavras pesadas; o V-01 cheio ficou SÓ no golpe decisivo (golpe/esmagou/destruiu/derrotou/venceu + cartão triunfo), 1 a cada >= 20 s (antes toda palavra pesada ganhava o combo) | fx_visual.py (`_GOLPE`, `micro`) | `ANIME_FX_V12=0` | 01/11 noite; PREVIA4 0:19 / 0:31 / 0:46 |
| — | Bug achado no teste: `negate:enable` (V-03) quebrava a passada INTEIRA no ffmpeg 8 e a legenda MIX caía no PNG antigo (Shorts saíam sem MIX). Agora `negate=enable` + 2ª tentativa sem os efeitos | fx_visual.py / fx_subtitles.burn_subtitles_ass | — | 01/11 noite; Short 1080x1920 60 fps com MIX |
| V-09 | Blur direcional de transição | já existia: xfade `hblur` em `bin\fx_clips.py:932` (whip pan) | — | anterior |
| V-13 | Ondulação de calor/energia (warp ripple sutil: `geq` senoidal amplitude 6 + `displace=edge=smear` por 0,40 s) logo depois do V-01 (+0,12 s) e junto do V-07 | `fx_visual.py` (`ondula`) | `ANIME_FX_V13=0` | 03/11; teste: `D:\tmp_logs\teste_fx_v13_v17\v13_ondula.jpg` |
| V-14 | Dupla exposição em memória, morte ou promessa (`_MEMORIA` ampliado + `tmix=frames=18` a ~30% + `gblur=sigma=1.5` por 1,2 s) | `fx_visual.py` (`memoria`) | `ANIME_FX_V14=0` / `ANIME_FX_MEMORIA=0` | 03/11; teste: `D:\tmp_logs\teste_fx_v13_v17\v14_memoria.jpg` |
| V-15 | Corte mascarado seguindo o golpe (`_CORTE_GOLPE`: feixe diagonal luminoso em `geq` usando `T` + `gblur` + `blend=c0_mode=screen` em 0,22 s) | `fx_visual.py` (`slash`) | `ANIME_FX_V15=0` | 03/11; teste: `D:\tmp_logs\teste_fx_v13_v17\v15_slash.jpg` |
| V-16 | Tela dividida na diagonal no confronto (`_CONFRONTO`: linha diagonal branca em `geq` + `blend=c0_mode=screen` + `eq=contrast=1.22:saturation=1.20` por 1,2 s) | `fx_visual.py` (`confronto`) | `ANIME_FX_V16=0` | 03/11; teste: `D:\tmp_logs\teste_fx_v13_v17\v16_confronto.jpg` |
| V-17 | Micro-corte de 4 quadros (0,13 s) para detalhe/olho antes do golpe decisivo (t - 0,15 s: zoom 1,38x na altura dos olhos + tarjas pretas de 18% em cima e embaixo) | `fx_visual.py` (`olho`) | `ANIME_FX_V17=0` | 03/11; teste: `D:\tmp_logs\teste_fx_v13_v17\v17_olho.jpg` |
| V-18 | Tipografia cinética na legenda MIX: 5 entradas novas além do pop — queda (`\move` de cima + fade), deslize (`\move` lateral), estica (squash & stretch `\fscx165\fscy60`→90/115→100), desfoque (`\blur10`+alpha→nítido), giro 3D (`\fry55`+80%→0) — por palavra, casando com o peso no modo "inteligente" (forte: estica/pop; médio: queda/giro3d; leve: deslize/desfoque), sorteada no "livre", nunca igual à anterior; caixa/sublinhado só entradas paradas. Ideia do iart-ai/motion-skills (nada instalado). 1º teste: giro a 85° a perspectiva do libass aumentava e cortava na borda → 55° + 80% | `recapd-ambientes\producao\bin\legenda_mix.py` (`ENTRADAS`, `_entrada_tags`, `_adesivo(entrada=)`) | `ANIME_LEGENDA_ENTRADAS=0` | 04/11; teste: ASS real renderizado no libass sobre quadro de Short, quadros a +0/+0,04/+0,08/+0,20 s de cada entrada (todas animam, nada corta) |

## DESCARTADO
| Ideia | Por quê |
|---|---|
