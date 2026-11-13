# ManhwaReact - estado atual e plano do que falta

Atualizado em 2026-10-01 (noite).

## Feito e testado

- Layout automatico (webcam / faixa divisoria / conteudo), saida 1080x1920 30 fps, corte da UI do celular.
- Audio: RNNoise, highpass, de-esser, compressor, loudness 2 passos -14 LUFS; trilha por mood com ducking (pool seguro) quando o editorial libera.
- Transcricao: Groq whisper-large-v3 (3 chaves em rodizio) -> fallback faster-whisper local.
- Quem fala: labios (MediaPipe) + correcao do editorial pelo texto.
- Editorial: proxy Opus 4.6 -> Sonnet 4.5 -> Claude Code CLI. Devolve nota, canal, obra, janela de ate 90 s, gancho, titulo com hashtags,
  descricao longa, 12-20 tags, keywords, CTA, mood, musica sim/nao, remocoes, partes e correcao de palavras.
- Tela: legendas palavra a palavra na cor do canal, gancho, faixa divisoria (handle + obra + "PARTE x/n"), barra de progresso, keywords com
  linhas de impacto e zoom no conteudo, zoom na webcam enquanto fala (1.10x/1.18x), "deixa o like" em 45%, "INSCREVA-SE" no fim, SFX em tudo.
- Saida por canal em `hipercool-materiais\manhwa-react\shorts\<canal>\`: mp4, thumb, meta.txt (tags por virgula), postar.json, relatorio.
- Canais: `config.json > channels` (manhwareact, cenareact, inventoreact) e kits em `canais\<slug>\` (perfil.png, banner.png, canal.md, canal.json).

## Auditoria do acervo e das pesquisas (2026-10-01, noite) - o que foi aplicado

- Acervo `overlays/elemental`: fx_impact (keywords), fx_likeburst, fx_subscribe, fx_comment, fx_part2, fx_watchtoend, fx_glitch (mascara de corte),
  fx_hearts / fx_confetti / fx_exclaim / fx_question / fx_anger / fx_sweatdrop / fx_emojirain (reacoes). Nao usados de proposito: fx_mascot_* (mascote de
  outro canal), fx_cap_* (estilos de legenda ja cobertos pelo ASS), fx_versus/fx_countup/fx_bignumber/fx_statuswindow (sem uso em react).
- `sfx_memes` (650 sons categorizados): som de meme por tipo de reacao (-9 dB), no maximo 3 por video.
- `sfx`: whoosh (gancho), snap (keyword), page_turn (like), magic_sparkle (CTA).
- Trilhas: pool seguro (mixkit + prioritarias) com ducking; blocklist de copyright respeitada.
- Pesquisa open source: legendas estilo Hormozi (ASS palavra a palavra), emoji colorido via PNG (limitacao do libass), zoom/punch-in e tremor,
  barra de progresso, gancho nos 2 s, CTA no fim, loudness -14 LUFS, RNNoise, Groq Whisper com tempo por palavra, limpeza de alucinacoes,
  divisoria irregular animada, validacao de saida, titulo A/B, comentario fixado, palavras seguras para monetizacao.
- Descartado: auto-editor (cortes proprios), DeepFilterNet (sem wheel py3.13), resemble-enhance, pycaps (precisa Chromium), WhisperX (Groq ja da tempo por palavra),
  reframe por rosto (webcam ja centralizada), B-roll (nao e react).

## Acervo completo em uso (2026-10-01, tarde da noite)

- Trilhas: `music.safe_only=false` (acervo inteiro menos a blocklist; prioritarias/favoritas primeiro).
- Memes: `memes_img` (126 videos curtos + 125 imagens) descritos por visao (`manhwareact.py memes`, Haiku via proxy) em `assets/memes_catalogo.json`;
  o editorial recebe o catalogo e escolhe ate 2 por video; imagem = pop de 2,2 s, video = ate 4 s com o audio do meme.
- Gatilhos de palavra: `assets/gatilhos_palavras.json` (24 gatilhos editaveis, cooldown 5 s, max 6 por video, nomes vulgares bloqueados).
- sfx_extras e sfx_foley entram na busca de sons dos gatilhos.

## Vigia de formatos (2026-10-01, noite)

- `mr/ideias.py` + comando `ideias`: analisa o video reagido (frames + narracao) e alimenta `ideias/IDEIAS.md`. Rodou nos 16 videos de hoje: 12 formatos replicaveis
  (tour de produto com musica, recap de anime com legendas, jogo de adivinhacao com pausas, noticia tech com fotos, parodia animada...).
- Proximo passo natural: um "fabricador" que pega uma ideia do quadro e gera o Short sozinho (roteiro LLM + TTS + imagens IA/fotos + trilha + legendas),
  reaproveitando `historias-em-frames` e `recapd-ambientes` que ja fazem videos faceless.

## Auditoria final de recursos (2026-10-01, madrugada) - ver AUDITORIA.md

- HyperFrames caseiro (Playwright + Chromium): cta_question, big_number, part_badge, watch_to_end, lower_third com texto/cor dinamicos.
- Acabamento ffmpeg: hqdn3d + eq + cas na webcam, cas no conteudo, vinheta; EQ de presenca na voz.
- Reacoes com variante anime no ManhwaReact (speedlines, blush, anger, sweatdrop, powerup); numeros falados em destaque.
- Faltando (valor): pool de trilhas originais com MusicGen local; light leaks (arquivos nao existem no disco); cinebars/transicoes com gatilho do editorial.

## Modo "lateral" - camera no canto + video base deitado (pedido 2026-10-02)

Pedido: react de manhwa longo (base https://youtu.be/3tMxBPYp6WE, 52 min, 16:9) com a webcam no canto superior direito.
O pipeline atual NAO cobre esse formato: ele espera gravacao em pe (webcam em cima, conteudo embaixo), Shorts de ate 90 s.

Pronto (2026-10-02):
- `manhwareact.py base <link|arquivo>` (`mr/base.py`): baixa o base (yt-dlp novo no .venv + node; H.264 1080p), audio 16 kHz,
  transcricao da narracao (Groq em pedacos de 10 min), cortes de cena (scdet). Saida em `bases/<id>/`.
- `transcribe_groq` agora divide audio longo em pedacos (limite de 25 MB do Groq) - vale para gravacoes longas tambem.

Feito em 2026-10-02 (manha), testado no 1o react grande real (31 min, 1920x1080):
- Layout PiP automatico (`probe._detect_pip`): moldura da janela = linha continua parada nos dois lados; acertou [1314,2,1918,346]
  no real e a janela com margem do teste sintetico. Manual: `layout.pip = [x0,y0,x1,y1]` em fracao. Recorte do Short desvia da janela.
- Base x gravacao pela narracao em comum (`base.achar_base` + `marcar_narracao`): fala do criador = o que nao e narracao do base.
- `manhwareact.py grande <video>`: video INTEIRO (stream copiado, audio -14 LUFS sem RNNoise) + titulo/descricao com credito ao
  original e capitulos + thumb 1280x720 -> `hipercool-materiais\manhwa-react\grandes\<canal>\`; depois os cortes (editorial em modo destaques,
  3 a 8 Shorts independentes, sem selo "parte 2") -> `hipercool-materiais\manhwa-react\cortes\<canal>\`. O `batch` faz isso sozinho p/ gravacao deitada > 4 min.

Falta (ordem):
1. (feito) Layout PiP.
2. Sincronia gravacao x base por audio (correlacao em janelas): mapa tempo-da-gravacao -> tempo-do-base, com pausas e pulos.
   Com isso: trocar a captura de tela pelo base original em 1080p e saber o que e narracao (palavra que bate com a transcricao
   do base) e o que e fala do criador (o resto) - resolve o "audio mono misturado" de vez.
3. Saida deitada 1920x1080 (video longo): legenda so da fala do criador, zoom/realce da webcam quando ele fala, cortes de tempo
   morto, capitulos na descricao, thumb com rosto + painel do manhwa. Render longo = rodar de noite (maquina fraca).
4. Shorts tirados do react longo (melhores reacoes) no formato em pe ja existente (conteudo + webcam em cima).
5. Dica de gravacao (OBS): mic numa faixa de audio separada (Configuracoes > Saida > Gravacao > faixas 1 e 2;
   Propriedades avancadas de audio: mic so na faixa 2). Com a voz separada, a fala do criador sai limpa sem adivinhacao.

## Pendencias (prioridade)

1. **Criar os canais no YouTube** (acao sua) com os kits de `canais\` e gerar o token OAuth de cada um (`D:\credenciais-canais\relogin_canal.py`),
   registrando em `youtube_canais.json` com o nome exato (ManhwaReact, CenaReact, InventoReact). Depois: `mr/publish.py` sobre
   `D:\postador-de-videos\bin\youtube_poster.py::upload()` lendo `postar.json` (private + publish_at) e `thumbnails.set`. 1-2 uploads/dia por canal, aprovacao humana.
2. **Trilhas livres**: baixar pacote da YouTube Audio Library/Pixabay para `trilhas\` e registrar em `moods.json` com `source_id` "yal-..." (hoje o pool seguro e pequeno).
3. **Novos canais conforme aparecerem temas** (ex.: games/retro, humor/animacao caseira, esportes). Basta adicionar em `channels` e rodar `scripts\canais.bat`.
4. **Varios reacts numa gravacao**: `parts` existe mas so testado com 1 parte por arquivo. Gravar teste com 2-3 reacts seguidos.
5. **Deteccao de divisoria/nome ja presente no video original** (para nao duplicar): hoje a faixa e sempre adicionada; opcao `band.enabled=false` por video via editorial ("band": false).
6. **Mascote/reacoes extras** do acervo (`fx_mascot_*`, `fx_exclaim`, `fx_question`) em momentos de surpresa/pergunta; transicoes `trans_*` entre partes.
7. **Emoji colorido** nas legendas/gancho (libass nao renderiza): PNG via Pillow + Segoe UI Emoji.
8. **Quem fala - 3a camada**: embedding de voz (resemblyzer/pyannote) por segmento.
9. **Turno noturno**: agendar `scripts\vigiar.bat` (Task Scheduler) e `/status-noturno` lendo `hipercool-materiais\manhwa-react\shorts`.
10. **Validacao automatica** (duracao, sync, loudness, legenda fora da tela) marcando `pronto=false` quando falhar; limpeza de `work\` (raw.wav/mixed.wav).

## Divisoria animada (2026-10-01, noite)

- A faixa reta saiu. A emenda entre webcam e conteudo agora e uma borda rasgada (mascara `assets/dividers/mask_*.png`, estilos tear/zigzag/wave)
  com um efeito animado em loop por cima, gerado por codigo na cor do canal (`mr/divider.py`): `electric` (raio), `fire` (chamas) e `glitch`.
  Estilo por canal em `config.json > divider.per_channel` (ManhwaReact e InventoReact = electric, CenaReact = fire). Altura 160 px, sobreposicao 56 px.
- O nome da obra fica centralizado sobre a emenda; o handle vai para o canto superior direito.
- Fogo = linguas de chama esparsas subindo da emenda (30 linguas animadas + brasa), nao uma barra lisa. Todos os 19 Shorts de 2026-10-01 foram refeitos com a divisoria nova.
- Ideias ainda nao feitas: usar os clipes do acervo como camada extra (`sparks.mp4` com blend screen, `fx_lightning.mov`/`trans_tear.mov` girados 90 graus),
  estilo "agua"/"gelo" (trans_water/trans_ice), e deixar o editorial escolher o estilo pelo clima do video.

## Ajustes feitos no fim do dia (2026-10-01)

- Faixas pretas estaticas do video original (logo/titulo do canal de origem, em cima ou embaixo do conteudo) sao detectadas e cortadas; so a nossa faixa fica.
- Alucinacoes do Whisper sobre musica/ruido ("E. E. E." repetido) sao removidas antes do editorial (`transcribe.clean_hallucinations`).
- Render em 2 passagens (layout -> overlays+legendas) com poucas threads e nova tentativa automatica quando o Windows nega memoria.
  Causa raiz: pagefile FIXO em 4096 MB (gerenciamento automatico desligado) e 100% usado; commit total ~16 GB entre Chrome, VS Code,
  Antigravity IDE, varias sessoes do Claude e os scripts do trader_binance. Recomendado: marcar "Tamanho gerenciado pelo sistema" ou 16 GB
  em Sistema > Configuracoes avancadas > Desempenho > Memoria virtual (precisa reiniciar).
- Kits de canal agora usam suas fotos (`paths.photos_dir`, campo `photo` por canal), com `marca_dagua.png` 150x150, `descricao.txt` e `palavras_chave.txt`.

## Decisoes tecnicas

- `drawtext` instavel nesta build do ffmpeg: todo texto via ASS. Overlays alpha ProRes 4444 via `tpad` transparente + `overlay=eof_action=pass` (sem `-itsoffset`, que estourava memoria).
- `CT2_USE_MKL=0` obrigatorio para o whisper local nesta maquina. x264 com `-threads 4` e `rc-lookahead=25` para caber na memoria.
- DeepFilterNet nao instala no Python 3.13; RNNoise (`arnndn`) ficou bom.
- Audio do video reagido vem mono junto com o mic: separacao por canal nao funciona; por isso labios + LLM.
- PyAV instalado e incompativel com `faster_whisper.decode_audio`: wav lido com soundfile.
- Groq devolve palavras sem pontuacao e segmentos grosseiros; palavras tem tempo preciso (usado nas legendas).
- Proxy LLM: `secrets_proxy.json` (copiado das settings do VS Code; nao versionar).
