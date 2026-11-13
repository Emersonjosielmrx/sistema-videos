# Auditoria completa - o que esta em uso, o que ficou de fora e o que falta (2026-10-01, noite)

## 1. ffmpeg (build gyan 8.1 "essentials") - filtros em uso

| Area | Filtros | Uso |
|---|---|---|
| Audio limpeza | highpass, arnndn (RNNoise bd.rnnn), deesser, acompressor, highshelf + equalizer (presenca de voz) | mic + audio do conteudo (mono misturado) |
| Loudness | loudnorm 2 passos (-14 LUFS, TP -1), ebur128 (validacao) | mix final |
| Mix | atrim/asetpts/concat, adelay, volume, amix normalize=0, sidechaincompress (ducking da trilha), aformat, afade, stream_loop | SFX, memes, trilha |
| Video corte/layout | trim/setpts/concat, crop, scale lanczos, split, overlay enable=between(), vstack, pad, alphamerge (borda rasgada), color | layout webcam/conteudo |
| Zoom/tremor | crop com x/y em funcao de t (sin/cos) + overlay enable | webcam ao falar, conteudo nas keywords |
| Acabamento | hqdn3d (ruido da webcam), eq (contraste/saturacao), cas (nitidez pos-upscale), vignette leve | passo A |
| Overlays | tpad (deslocar clipes alpha sem estourar memoria), format=yuva420p, overlay eof_action=pass, -loop 1 (PNG), -stream_loop -1 (divisoria) | passo B |
| Texto | ass (libass) com fontes locais via fontsdir | legendas, gancho, barra, obra |
| Deteccao | silencedetect, blackdetect, ebur128, astats | cortes, validacao |

Disponiveis e avaliados, mas nao usados de proposito: `xfade` (cortes secos sao o padrao dos reacts; o glitch mascara os cortes do editorial),
`zoompan` (zoom por crop+overlay e mais leve), `minterpolate` (slow motion caro em CPU), `deshake`/`vidstab` (webcam fixa), `drawtext` (instavel nesta build),
`nlmeans` (lento), `speechnorm`/`dynaudnorm` (o compressor + loudnorm ja fazem), `whisper` (nao existe nesta build), NVENC (sem GPU).

## 2. HyperFrames (HTML/CSS -> video alpha pelo Chromium)

- O acervo so tinha os MOVs ja renderizados (116 em `overlays/elemental`); a pasta de composicoes HTML nao existe mais no disco.
- Reimplementado em `mr/hyperframes.py` com Playwright (instalado no venv, Chromium ja estava em cache): 5 composicoes com texto e cor do canal:
  `cta_question` (pergunta do comentario fixado), `big_number` (numero falado, ex. "20 MIL REAIS"), `part_badge` ("PARTE 2 NO PERFIL"),
  `watch_to_end`, `lower_third` (obra + handle). Tempo controlado pela Web Animations API (captura deterministica, offline, fontes locais).
- Em uso no pipeline: watch_to_end (cor do canal), part_badge, cta_question (quando ha pergunta), big_number (ate 2 por video). `lower_third` fica disponivel.

## 3. Acervo `D:\hipercool-materiais\assets` - cobertura

| Pasta | Itens | Em uso |
|---|---|---|
| overlays/elemental | 116 MOV alpha | impact, likeburst, subscribe, comment, part2 (fallback), watchtoend (fallback), glitch, hearts, confetti, exclaim, question, anger, sweatdrop, emojirain, speedlines, blush, powerup. Fora: fx_mascot_* (mascote de outro canal), fx_cap_* (legendas ja feitas em ASS), versus/countup/bignumber/statuswindow (substituidos por HyperFrames dinamico), trans_* (uso previsto entre partes), cinebars/flashback/timeskip (sem gatilho semantico ainda) |
| overlays/transitions | so o _MAP.json (os MP4 de light leak nao estao no disco) | - |
| overlays raiz/scaled720 | sparks, speedlines, rain, snow, petals (fundo preto, blend screen) | nao (candidato: sparks na emenda) |
| sfx | 64 | whoosh (gancho), snap (keyword), page_turn (like), magic_sparkle (CTA), busca dos gatilhos |
| sfx_memes | 650 categorizados | reacoes (comedia/impacto/suspense/romance/tristeza) + 24 gatilhos de palavra |
| sfx_extras | 751 | busca dos gatilhos |
| sfx_foley | 33 + categories.json | nao (foley e para narracao; em react nao faz sentido) |
| sfx_prioridade | 5 | nao |
| trilhas | 329 + moods.json + blocklist (165) | acervo inteiro menos blocklist; `_musicgen_cache` esta vazio |
| memes_img | 126 videos + 125 imagens | catalogo por visao (239 ok) escolhido pelo editorial |
| mascote / mascote_mov | 15 + 14 | nao (identidade de outro canal) |
| cta_frases.json | frases de CTA do canal antigo | nao (o editorial escreve o CTA e a pergunta) |
| fontes | nenhuma no acervo | baixadas: Montserrat ExtraBold/Black, Luckiest Guy, Bangers; emoji colorido via Segoe UI Emoji do Windows |

## 4. Modelos e binarios baixados em `assets/`

- `models/bd.rnnn, sh.rnnn, mp.rnnn, lq.rnnn, cb.rnnn` (RNNoise) - usa `bd` (voz + risadas).
- `models/face_landmarker.task` (MediaPipe) - labios e recorte de rosto nos kits.
- Whisper local `small` (recapd) e `medium` (`models/`) como fallback do Groq.
- Chromium (Playwright) no cache do usuario.
- Nao instalaveis no Python 3.13: DeepFilterNet, resemble-enhance (e DeepFilterNet trataria o audio do conteudo como ruido).

## 5. Categorias cobertas

- Canais: manhwareact, cenareact, inventoreact (novos: adicionar em `channels` e rodar `canais`).
- Moods de trilha: tense_dramatic, sad_emotional, romantic_sexy, funny_lighthearted, neutral_chill, calm_chill.
- Reacoes: laugh, shock, love, angry, question, hype, cringe (variante anime para ManhwaReact: speedlines, blush, anger, sweatdrop, powerup).
- Gatilhos de palavra: choque, que_isso, falha, vitoria, dinheiro, sus, finish, wasted, triste, ruim, wow, tensao, piada, dor, velocidade, magica, noticia, peido, foto, soco, vidro, tiro, sono, nope.
- Numeros falados: digitos + mil/milhao + unidade (reais, anos, km, %...).
- Memes: 8 categorias de som; imagens/videos por descricao livre.

## 6. O que ainda falta (ordem de valor)

1. Trilhas originais com MusicGen local (`recapd-ambientes/producao/bin/musicgen_local.py`, musicgen-small, ~2 min por faixa de 30 s na CPU): gerar um pool
   de 6 moods x 5 faixas numa noite e marcar como `source_id: musicgen` (zero risco de Content ID). O cache atual esta vazio.
2. Light leaks/transicoes: os MP4 do `_MAP.json` nao existem; baixar um pacote livre (Pexels/Pixabay "light leak") ou gerar por codigo como a divisoria.
3. `fx_cinebars` em momentos dramaticos e `trans_*` entre partes (precisa de gatilho semantico do editorial: "dramatic": [t]).
4. Legendas com fundo/caixa por canal (estilo CapCut) como opcao em `captions.style`.
5. Vigia de formatos -> fabricador de Shorts faceless (reaproveitar historias-em-frames).
6. Pagefile do Windows (fixo em 4 GB e cheio): e o unico gargalo real de tempo hoje.
