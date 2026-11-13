# HANDOFF - historico completo do projeto ManhwaReact (para o proximo agente)

Escrito em 2026-10-02 (madrugada) ao fim de uma sessao unica de ~14 horas com o usuario (Haylla, susanabergado731671@hotmail.com).
Leia este arquivo primeiro; depois `README.md` (uso), `AUDITORIA.md` (recursos em uso/descartados), `PLANO.md` (pendencias) e `CLAUDE.md` (regras do agente).

---

## 1. O pedido original e como evoluiu

1. **Pedido inicial (manha):** o usuario gravou os 2 primeiros videos de react (`2026-10-01 10-58-04.mp4` e `11-23-15.mp4`, em `D:\downloads`) para um canal novo
   chamado **ManhwaReact** (react de manhwa, mas "nao so manga"; formato Short). Queria uma automacao RPA que deixe os videos "o melhor possivel":
   tirar ruido, cortar pausas e trechos ruins (como "os algoritmos famosos fazem"), adicionar coisas na tela, usar o que ja existe no disco D e em projetos
   open source, nao comecar do zero.
2. **Durante o dia:** "deixe um v1 funcional e o resto planejado" -> depois "pasta para colocar o video + botao no desktop + pasta de prontos" ->
   "tags sem aspas separadas por virgula, titulo com hashtags, descricao maior, usar Groq do hermes para Whisper, zoom na camera quando eu falo,
   gerar thumb sempre, faltam efeitos/trilha/overlays/CTA".
3. **Tarde:** "ja adiciona tudo (visual e som)? Divisorias entre webcam e video, as vezes com nome; videos que ja tem no original nao precisam; verifique
   tudo que pode ser melhorado; deixei varios videos de hoje (16) na pasta; pode usar o Claude do VS Code (proxy, Opus 4.6 e Sonnet 4.5) como fallback;
   quero dividir os videos em canais por tema: cria os canais com foto de perfil, banner, nome, descricao".
4. **Noite:** "nos canais nao tem descricao nem marca d'agua, e as fotos de perfil/banner nao usam minhas fotos (`D:\fotos para videos\fotos`)".
5. "A divisoria ficou horrivel, reta; as que eu vejo sao eletricidade, fogo, nenhuma reta" -> divisoria animada irregular.
6. "Ja aplicou tudo de bom do disco D e do open source? Os prontos nao precisa refazer, mas os proximos tem que ser o melhor possivel."
7. "Trilhas: pode usar `D:\hipercool-materiais\assets` inteiro, memes, imagens de memes, efeitos de som quando certas palavras forem usadas."
8. "Um vigia que analise os videos reagidos e anote formatos que nos mesmos poderiamos fazer (so musica + comentarios, trilha + imagens dos anos 90...)
   num campo de ideias com 'como fazer'."
9. "Ja exploramos todas as possibilidades? HyperFrames do HeyGen, ffmpeg, todas as categorias, melhores coisas baixadas em assets? Analise tudo e veja o que falta."
10. **Este pedido:** documentar tudo na pasta do projeto para outro agente continuar.

Idioma do usuario: portugues do Brasil, escreve rapido com muitos erros de digitacao; responder em portugues, direto, sem floreio.

---

## 2. Estado atual (o que funciona hoje)

Pipeline em `D:\manhwa-react` (Python 3.13 em `.venv`, ffmpeg 8.1 em `D:\hipercool-materiais\bin`). Fluxo do usuario:
`1-COLOQUE-AQUI\` -> atalho "ManhwaReact - PROCESSAR" no desktop (`scripts\BOTAO_PROCESSAR.bat`) -> `hipercool-materiais\manhwa-react\shorts\<canal>\`.

Por video (`mr/pipeline.py::process`):
1. `probe.detect_layout`: acha a linha webcam/conteudo, corta a UI lateral do celular e faixas pretas estaticas do video original (logo/titulo).
2. `audio.clean_audio`: highpass -> RNNoise (`arnndn` bd.rnnn) -> de-esser -> compressor -> EQ de presenca. Loudness 2 passos -14 LUFS no final.
3. `transcribe`: Groq whisper-large-v3 (3 chaves em `D:\postador-de-videos\secrets\groq_keys.json`, rodizio) -> fallback faster-whisper local
   (`CT2_USE_MKL=0`). `clean_hallucinations` remove "E. E. E." repetidos.
4. `lips`: MediaPipe FaceLandmarker na webcam -> media |delta| abertura da boca a 15 fps; limiar 0.0014 separa fala do criador do audio do video reagido
   (que vem mono misturado com o mic; nao da para separar por canal). O editorial corrige pelo texto (`speakers`).
5. `cuts`: silencios (-40 dB, >= 0,35 s), vicios ("e...", "hum"), retakes (frase repetida), remocoes do editorial, janela maxima 90 s.
6. `editorial` (`llm.ask_json`: proxy Opus 4.6 -> Sonnet 4.5 -> Claude Code CLI): nota/usable, canal, obra, partes (varios reacts ou melhor janela),
   gancho, titulo (+2 alternativos), descricao, hashtags, 12-20 tags, keywords com emoji, reacoes, memes (ids do catalogo), CTA, comentario fixado,
   mood, musica sim/nao, remocoes, correcao de palavras do Whisper, palavras seguras para monetizacao.
7. `ideias`: vigia de formatos (frames do conteudo + narracao -> Sonnet) alimenta `ideias\IDEIAS.md`.
8. Por parte: `captions.build_ass` (legendas 3 palavras com a ativa na cor do canal, gancho, barra de progresso, obra sobre a emenda, handle no canto),
   zoom na webcam enquanto fala (`render.zoom_plan_speech`), zoom + tremor no conteudo nas keywords, overlays (acervo + HyperFrames + emoji PNG + memes),
   gatilhos de som por palavra (`triggers`), reacoes (`reactions`), trilha (`music`, acervo inteiro menos blocklist; prefere faixas MusicGen se existirem),
   `_declutter` (1 som por 0,6 s, 1 emoji/meme por 0,9 s), `render_audio` (concat + SFX + musica com ducking + loudnorm 2 passos),
   `render_video` em 2 passagens (A: layout com emenda rasgada via alphamerge + divisoria animada em loop; B: overlays + ASS), `thumb`, `validate`
   (duracao, resolucao, loudness, frames pretos -> `pronto=false` no postar.json), copia para `hipercool-materiais\manhwa-react\shorts\<canal>\`.
9. Saidas por video: `<slug>.mp4`, `<slug>_thumb.jpg`, `<slug>_meta.txt` (titulo + alternativos, descricao, tags por virgula, hashtags, comentario fixado),
   `<slug>.postar.json` (formato do postador), `relatorio.md`. Cache em `work\<slug>\` (probe, layout, clean.wav, transcript, lips, silences, editorial, fixes, ideia, partN/edl.json).

Comandos: `process`, `batch`, `watch`, `analyze`, `canais` (kits), `memes` (catalogo por visao), `musica` (MusicGen local), `ideias` (vigia). Bats em `scripts\`.

Resultados do dia: 16 gravacoes -> 19 Shorts prontos (InventoReact 9, CenaReact 7, ManhwaReact 3) + 1 rejeitado (teste de gravacao 13-08-45).
Todos refeitos com a divisoria animada. O video 16-24-50 (Xbox) foi refeito por ultimo como teste de tudo (1 parte de 78 s).

---

## 3. Linha do tempo detalhada (o que fizemos, em ordem)

1. Mapeamento: 4 agentes exploraram o disco D (hipercool-videos, hipercool-materiais, recapd-ambientes, postador-de-videos, historias-em-frames, veo, hermes-call)
   e pesquisaram open source (auto-editor, DeepFilterNet, RNNoise, pycaps, stable-ts, WhisperX, zoompan, GOATVideoEditor, chopify, OpenShorts...).
   Conclusao: nada de jump-cut nem legenda por palavra existia; muito asset reutilizavel (SFX, trilhas, overlays alpha, uploader, loudness 2 passos).
2. Analise dos 2 videos: 720x1280 30 fps, webcam em cima (divisor em 569 e 404 px), UI do celular nas colunas 0-19 e 688-719, audio -28/-34 LUFS,
   ruido de fundo -43 dB (SNR ~17 dB). Teste de denoise: arnndn bd/sh/mp -> -13 dB de ruido com -1 dB na voz; afftdn quase nada. DeepFilterNet nao instala (py3.13).
3. Descoberta: Whisper transcreve tambem a narracao do video reagido; audio e mono misturado. Solucao: movimento labial (MediaPipe) - testado: fala >= 0,0024,
   narracao <= 0,0007 (feature = media |delta| a 15 fps). Depois: arbitragem do Claude pelo texto (ele estava rindo com a boca aberta durante a narracao).
4. v1 do pipeline (probe/audio/transcribe/lips/cuts/editorial/captions/render) com claude CLI (`claude -p`, sem API key, removendo CLAUDECODE do env).
5. Sessao caiu uma vez (tokens); retomada. Problemas de maquina: `mkl_malloc` (-> CT2_USE_MKL=0), PyAV incompativel com faster-whisper (-> soundfile),
   `drawtext` instavel (-> tudo em ASS), caminhos no filtro ffmpeg (-> `ffpath()` com aspas e `\:`).
6. Pastas 1-COLOQUE-AQUI / hipercool-materiais\manhwa-react\shorts, botao no desktop (criar_atalhos.ps1), README, PLANO, memoria do agente.
7. Groq Whisper como principal (1,7 s por video, melhor qualidade), zoom ao falar, thumb, trilha com ducking, overlays fx_impact/fx_subscribe, meta.txt.
   Problema: render falhando com "Cannot allocate memory". Causa: `-itsoffset` em overlays bufferizava frames -> trocado por `tpad` transparente.
8. Pedido de divisoria + canais: faixa reta (banda de 64 px com handle e obra), canais em `config.json > channels` (manhwareact, cenareact, inventoreact),
   kits em `canais\` (Pillow), editorial escolhe canal, pasta por canal em hipercool-materiais\manhwa-react\shorts, proxy do VS Code (`secrets_proxy.json`, lido de
   `%APPDATA%\Code\User\settings.json`: base `http://157.173.207.22:20133`, modelos `antigravity/claude-opus-4-6-thinking`, `kr/claude-sonnet-4.5`, `kr/claude-haiku-4.5`).
   Lote dos 16 videos (1 h). Dois falharam por memoria; "Inteligencia Hostil" tinha faixa preta com logo do canal de origem incluida na webcam.
9. Correcoes: faixas pretas estaticas do original detectadas e cortadas (`_block` com tolerancia de 14 linhas); alucinacoes do Whisper removidas (Malcolm passou);
   deteccao de layout sem empilhar frames (memoria); render em 2 passagens com poucas threads + `ffmpeg_retry` (espera 25 s x3 e cai para ultrafast/1 thread).
   Causa raiz da memoria: pagefile FIXO em 4096 MB, gerenciamento automatico desligado, 100% usado (commit ~16 GB entre Chrome, VS Code, Antigravity IDE,
   varias sessoes do Claude, scripts do trader_binance). Recomendado ao usuario (3x): colocar "gerenciado pelo sistema" ou 16 GB. Ainda nao foi feito.
10. Kits com as fotos do usuario (`Fotos minhas retrato`, indices 19/13/29 escolhidos de uma folha de contato), marca d'agua 150x150, descricao.txt, palavras_chave.txt.
11. Divisoria animada (`mr/divider.py`): emenda rasgada (mascara PNG + alphamerge, sobreposicao 56 px) + efeito em loop gerado por codigo na cor do canal:
    electric (raio), fire (linguas de chama; a 1a versao era uma barra lisa e foi refeita), glitch. Obra centralizada na emenda, handle no canto.
    Os 19 Shorts foram refeitos com ela (duas rodadas por causa do fogo).
12. Auditoria 1: reacoes (overlay + emoji + som de meme), emoji colorido por keyword (Pillow + Segoe UI Emoji), tremor no conteudo, "assista ate o fim",
    glitch nos cortes do editorial, "parte 2"/"comenta", titulos alternativos, comentario fixado, validacao + limpeza, palavras seguras.
13. Acervo inteiro: trilhas sem restricao (menos blocklist), catalogo de memes por visao (Haiku, 251 itens, 239 ok), gatilhos de palavra (24),
    memes em imagem/video escolhidos pelo editorial com audio do meme, declutter.
14. Vigia de formatos (`mr/ideias.py`): rodou nos 16 videos -> 12 formatos replicaveis em `ideias\IDEIAS.md`.
15. Auditoria 2: HyperFrames caseiro (Playwright + Chromium, fontes via file://), acabamento ffmpeg (hqdn3d, cas, vignette, EQ), reacoes anime no ManhwaReact,
    numeros falados em destaque, comando `musica` (MusicGen local via venv do recapd), limpeza de saidas antigas quando o numero de partes muda,
    gatilho "dor" sem "ai", numeros so >= 10 ou com unidade. `AUDITORIA.md` escrito.

---

## 4. O que tentamos e NAO funcionou / descartamos (nao repetir)

| Tentativa | Resultado | O que fazer em vez disso |
|---|---|---|
| DeepFilterNet (pip) | sem wheel para Python 3.13; e trataria o audio do conteudo como ruido | RNNoise `arnndn` bd.rnnn (ja em uso); binario Rust `deep-filter.exe` so se separar o mic |
| resemble-enhance, pycaps, WhisperX | nao instalam no 3.13 / precisam Chromium+venv 3.12 / redundante com Groq | Groq word timestamps + ASS proprio |
| auto-editor (pip 29.3.1) | e um stub; a versao real e binario Nim | cortes proprios em `mr/cuts.py` |
| Separar voz do criador por canal L/R | audio do conteudo tambem e mono (side/mid ~0,03) | labios + LLM |
| Correlacao audio x boca por segmento | ruidosa (0,4 em narracao do conteudo) | media |delta| da boca a 15 fps + LLM |
| `drawtext` do ffmpeg | instavel nesta build (gyan essentials) | ASS/libass e HyperFrames |
| `-itsoffset` nos overlays | bufferiza o video inteiro -> "Cannot allocate memory" | `tpad=start_duration=T:color=black@0` |
| ProRes 4444 direto no overlay | decodificacao pesada em memoria | cache em MOV png rgba (`assets/overlays_cache`) |
| x264 preset medium, threads 4 | falha de malloc com o pagefile cheio | veryfast crf 17, threads 2, `ffmpeg_retry` |
| faster-whisper medium local | 206 s para 52 s de audio (vs 25 s small, 2 s Groq) | Groq; medium fica como fallback opcional (`--whisper medium`) |
| `-loop 1` PNG com `enable` sem tpad | ok, mantido para PNG | - |
| Faixa reta com handle/obra | usuario odiou ("horrivel, nenhuma e reta") | divisoria irregular animada (`mr/divider.py`) |
| Fogo v1 (ruido denso) | virou barra lisa amarela | linguas de chama esparsas (30 linguas + brasa) |
| Mascote fx_mascot_* | e a mascote do canal antigo (Inovare) | nao usar |
| Pool "seguro" de trilhas (mixkit) | so 4 faixas; usuario liberou o acervo inteiro | `music.safe_only=false` + blocklist; MusicGen local para originais |
| Fontes do acervo | nao existem | Montserrat/Luckiest Guy/Bangers baixadas em `assets/fonts` |
| Light leaks `overlays/transitions` | so o `_MAP.json` existe, os MP4 nao | gerar por codigo ou baixar pacote livre |
| Playwright `set_content` com fontes file:// | fontes nao carregam (origem about:blank) | gravar HTML em disco e `page.goto(file://)` |

---

## 5. O que NAO foi feito (pendencias) - detalhes em PLANO.md

1. **Upload/agendamento - FEITO em 2026-10-02, falta so o token.** `mr/publish.py` + comandos `aprovar` e `publicar` (ver secao 9).
   Os canais ja existem e estao em `youtube_canais.json` (ids `novo_mente_artificial_i5r`=ManhwaReact, `novo_universo_ia_d6s`=CenaReact,
   `novo_ia_agora_h3n`=InventoReact; renomeados de @MenteArtificial-i5r/@UniversoIA-d6s/@IAAgora-h3n). Os tokens estao MORTOS: cada canal tem
   projeto OAuth proprio (65933226849 / 555230777815 / 597747825947) que estava em modo "Em teste" (token dura 7 dias). Conserto: usuario publica
   o app (Google Auth Platform > Publico-alvo > Publicar app) e roda `D:\credenciais-canais\relogin_url.py "<Nome>"` (cliente Web, redirect
   `http://localhost` porta 80; `relogin_canal.py` usa porta aleatoria e daria redirect_uri_mismatch). Em 2026-10-02 o console mostrava um aviso de
   "possivel violacao da politica de uso aceitavel" em um dos projetos - checar qual.
1b. **Modo lateral (webcam no canto + base deitado, react longo)**: pedido em 2026-10-02 - ver PLANO.md secao "Modo lateral".
   Ja existe `manhwareact.py base <link>` (bases/<id>/: base.mp4, transcricao da narracao, cenas), layout PiP automatico,
   `manhwareact.py grande <video>` (video inteiro -> hipercool-materiais\manhwa-react\grandes + cortes -> hipercool-materiais\manhwa-react\cortes). Pastas separadas a pedido do usuario:
   hipercool-materiais\manhwa-react\shorts = Shorts de gravacoes curtas; hipercool-materiais\manhwa-react\cortes = Shorts tirados de react grande; hipercool-materiais\manhwa-react\grandes = video inteiro.
   Falta: trocar a captura pelo base em 1080p (sincronia por tempo) e postar video longo (publish.py so faz Shorts).
2. **Pagefile**: pedir de novo. Enquanto estiver em 4 GB, cada render leva 4-11 min e as vezes falha mesmo com retry.
3. **Trilhas originais**: rodar `scripts\gerar_trilhas.bat` numa noite (MusicGen-small, ~2 min/faixa, baixa 500 MB na 1a vez). O picker ja prefere `assets/music_generated`.
4. **Fabricador de Shorts faceless** a partir de `ideias\IDEIAS.md` (reaproveitar `D:\historias-em-frames` e `D:\recapd-ambientes`).
5. Light leaks, `fx_cinebars`/`trans_*` com gatilho semantico do editorial, legendas com caixa (estilo CapCut) por canal, emoji colorido direto no ASS (libass nao faz),
   3a camada de "quem fala" (embedding de voz), turno noturno agendado (`scripts\vigiar.bat` no Task Scheduler), teste real de gravacao com 2-3 reacts seguidos.
6. Novos canais conforme surgirem temas (ex.: games retro, humor/animacao caseira): adicionar em `channels`, rodar `scripts\canais.bat`.

---

## 6. Armadilhas do ambiente (leia antes de rodar qualquer coisa)

- Use SEMPRE `D:\manhwa-react\.venv\Scripts\python.exe` com `PYTHONUTF8=1` (console cp1252 quebra com emoji). Nao usar o venv de `D:\hipercool-videos`.
- No Git Bash, `python` resolve para venvs diferentes dependendo do cwd; use caminho absoluto.
- Heredocs no Bash com aspas simples dentro falharam varias vezes nesta sessao; para escrever arquivos grandes use a ferramenta Write.
- Caminhos dentro de filtros ffmpeg: `mr.common.ffpath()` (aspas + `\:`). Caminhos de modelo RNNoise idem.
- `CT2_USE_MKL=0` antes de importar faster_whisper (ja em `mr/transcribe.py`). Se mesmo assim der "mkl_malloc", e memoria da maquina.
- Memoria: sempre 1 render por vez; nunca rodar lote + outra coisa pesada em paralelo. `ffmpeg_retry` cuida de falhas pontuais.
- Groq: chaves em `D:\postador-de-videos\secrets\groq_keys.json` (campo `token`); limite de 25 MB por arquivo (enviamos wav mono 16 kHz).
- Proxy LLM: `D:\manhwa-react\secrets_proxy.json` (nao versionar; gerado a partir das settings do VS Code). Modelos: opus = antigravity/claude-opus-4-6-thinking,
  sonnet = kr/claude-sonnet-4.5, haiku = kr/claude-haiku-4.5. Lista completa em `GET /v1/models` (1063 modelos).
- Claude Code CLI (ultimo fallback): `C:\Users\Haylla\.vscode\extensions\anthropic.claude-code-2.1.285-win32-x64\resources\native-binary\claude.exe` com `CLAUDECODE` removido do env.
- O cache `work\<slug>\` e por etapa: apagar `editorial.json`+`fixes.json` para refazer o editorial; `layout.json` para refazer layout; `--force` refaz tudo.
- `work\state.json` controla o `batch`/`watch` (nao reprocessa arquivo com mesmo mtime e status done/rejected).
- Chromium do Playwright esta em `%LOCALAPPDATA%\ms-playwright` (chromium-1243); `uv pip install playwright` no venv ja funcionou sem baixar browser.
- Overlays do acervo sao ProRes 4444 em `D:\hipercool-materiais\assets\overlays\elemental` -> cache png rgba em `assets\overlays_cache` (feito na 1a vez).
- Groq devolve segmentos grosseiros (ex.: 30-50 s) mas palavras precisas; use as palavras.

---

## 7. Mapa de arquivos

```
D:\manhwa-react\
  manhwareact.py        CLI (analyze|process|batch|watch|canais|memes|musica|ideias)
  config.json           TODA a configuracao (paths, canais, cortes, legendas, overlays, divisoria, musica, editorial, hyperframes, ideias, validate)
  secrets_proxy.json    proxy LLM (nao versionar)
  mr/                   common, probe, audio, transcribe, lips, cuts, editorial, llm, captions, render, divider, hyperframes, emoji, reactions,
                        triggers, memes, music, musicgen, thumb, validate, ideias, channels, pipeline
  assets/               fonts, models (rnnn + face_landmarker), sfx (whoosh/pop/like/cta), dividers (mov+mask gerados), hyperframes (cache),
                        emoji (png), overlays_cache (png rgba), memes_catalogo.json, memes_audio, gatilhos_palavras.json, music_generated (vazio)
  canais/<slug>/        perfil.png, banner.png, marca_dagua.png, descricao.txt, palavras_chave.txt, canal.md, canal.json
  ideias/               IDEIAS.md + ideias.json (vigia de formatos)
  1-COLOQUE-AQUI/  hipercool-materiais\manhwa-react\shorts/<canal>/  output/<slug>/  work/<slug>/  models/ (whisper medium)
  scripts/              BOTAO_PROCESSAR.bat, processar.bat, lote.bat, vigiar.bat, canais.bat, gerar_trilhas.bat, criar_atalhos.ps1
  README.md  PLANO.md  AUDITORIA.md  CLAUDE.md  HANDOFF.md (este)
```

Videos-fonte do dia: `D:\downloads\drive-download-20261001T201616Z-1-001\*.mp4` (16). Memoria do agente: `C:\Users\Haylla\.claude\projects\d--\memory\`.

---

## 8. Como continuar (roteiro para o proximo agente)

1. Confirmar com o usuario se o pagefile foi alterado (`wmic pagefile get AllocatedBaseSize,CurrentUsage`). Se nao, pedir de novo; e o maior ganho de tempo.
2. Teste rapido de sanidade (3-4 min): `scripts\processar.bat "D:\downloads\drive-download-20261001T201616Z-1-001\2026-10-01 16-19-51.mp4" --force`
   e conferir `hipercool-materiais\manhwa-react\shorts\inventoreact\2026_10_01_16_19_51.mp4` (abra frames com ffmpeg -ss; o usuario avalia pelo visual).
3. Se o usuario mandar videos novos: eles vao para `1-COLOQUE-AQUI` e ele clica no botao; ou `scripts\lote.bat <pasta>`.
4. Ao mexer no visual, valide com frames extraidos (`ffmpeg -ss T -i out.mp4 -frames:v 1 x.png`) e mostre ao usuario; ele reage ao que ve.
5. Nao refazer videos ja prontos sem pedido; melhorias valem para os proximos.
6. Postagem: `python manhwareact.py publicar --situacao` mostra token/fila/aprovados/postados por canal (ver secao 9).
7. Para o fabricador faceless: comecar pelos formatos de maior potencial em `ideias\IDEIAS.md` ("tour de produto so com musica", "recap de cena de anime com legendas").

---

## 9. Postagem no YouTube (ligada ao postador em 2026-10-02)

- `mr/publish.py` usa `D:\postador-de-videos\bin\politica.py` e chama o `youtube_poster.py` (CLI) via `politica.postar_youtube(..., projeto="manhwa-react")`:
  vale a politica do postador inteira (parada geral, token morto/suspenso, cota, aprovacao humana em `config\aprovacoes.json`, intervalo de 2 h, ledger).
- Os 3 canais estao em `D:\postador-de-videos\config\canais_reservados.json` (projeto `manhwa-react`): ficam fora dos pools do postar_tudo_hoje /
  postar_pos_final / agendar_vo3, e o youtube_poster recusa upload neles sem `--projeto manhwa-react`.
- Config: `config.json > publish` (max 2/canal/dia, horarios 12:00 e 19:00 + jitter de 20 min por video, thumbnail, comentario) e
  `channels[].youtube_id` (id no youtube_canais.json).
- Fluxo: `aprovar` (abre cada video, a/r/p/s; `--tudo` aprova todos) -> `publicar` (upload private + publishAt no proximo slot, thumbnails.set,
  move mp4/json/meta/thumb para `hipercool-materiais\_postados\react\<canal>\`, registro em `hipercool-materiais\_postados\react\publicados.json`) -> na rodada seguinte depois de publicar,
  posta o `comentario_fixado` como comentario do canal (a API nao fixa). `--simular` mostra o plano; `--situacao` o resumo.
- Automatico: etapa 2b do `D:\postador-de-videos\bin\postar_tudo_auto.bat` (tarefa PostadorDeVideos, 06:40), log em
  `D:\postador-de-videos\logs\manhwa_react_AAAAMMDD.log`. Botao no desktop "ManhwaReact - APROVAR E POSTAR" (`scripts\BOTAO_APROVAR_E_POSTAR.bat`).
- Backups do que foi alterado no postador: `D:\postador-de-videos\_backup_2026-10-02\`, `youtube_canais.json.bkp_20261002`, `config.json.bkp_20261002`.

---

## 10. Capas novas, canais novos e imagem por IA (2026-10-02, tarde)

- **Capas** (`mr/capa.py`, ligado no pipeline e no `grande`; `manhwareact.py capas` refaz as dos videos prontos sem re-renderizar):
  amostras do trecho -> folha numerada -> LLM com visao escolhe o quadro mais forte e o foco do rosto do personagem;
  marca d'agua do canal reagido detectada (parada na maioria dos quadros, faixa de cima/baixo) e cortada fora;
  painel nitido separado do fundo borrado pela borda vertical reta; rosto do criador no momento de boca mais aberta COM rosto
  detectado (MediaPipe) num circulo com brilho na cor do canal; texto em linhas equilibradas (branco/amarelo, contorno).
  Short 1080x1920 (fundo = quadro desfocado, personagem inteiro em cima) e grande 1280x720 (painel nitido no centro).
- **Imagem por IA** (`mr/imagem.py`): gateway OmniRoute do historias-em-frames (`antigravity/gemini-3.1-flash-image`, chave lida de
  `D:/historias-em-frames/secrets/omniroute.json`, nada copiado). So texto->imagem: o gateway IGNORA imagem de referencia
  (testado: "esta foto em preto e branco" devolveu outra foto) e `/v1/images/edits` nao existe para antigravity.
  Por isso o rosto real do usuario entra sempre por composicao (Pillow). Cache em `assets/ai_cache/`.
- **Canais novos** (kits em `canais/<slug>/`, arte de fundo por IA + foto real; @ conferidos livres em 2026-10-02):
  CartuchoReact (games retro/consoles), ForjaReact (forja/oficios), PassaporteReact (culturas/lugares) -> entraram em
  `config.json > channels` (o editorial ja manda videos para eles; nicho do InventoReact foi estreitado).
  Mundo Que Nao Existe (videos do projeto D:/veo) e Fio da Meada (D:/historias-em-frames) -> `config.json > channels_outros`
  (so kit, o editorial NAO usa). Fotos: `D:/fotos para videos/fotos` (evitar as de "jornal": marca Globo; heroi com Batman/Jedi: marcas).
- `process --partes N` renderiza so as partes pedidas sem apagar as outras.
- 2026-10-02 (fim da tarde): **PassaporteReact descartado** (o usuario ja tinha um canal para o tema) -> `config.json > channels_descartados`;
  culturas/povos voltam para o InventoReact. Videos redistribuidos (editorial.json `channel` trocado + re-render, `channel_anterior` guardado):
  16_24_50 e 16_40_55 -> cartuchoreact; 16_37_51 (2 partes) e 17_51_13 -> forjareact. Os 5 do CenaReact que sumiram de hipercool-materiais\manhwa-react\shorts
  (16_15_50, 16_20_54, 16_27_53) foram apagados pelo usuario no Explorer (lixeira, 13:11) - provavelmente postados a mao.
- 2026-10-02 (noite): **saida final mudou para `D:\hipercool-materiais\manhwa-react\`** (pedido do usuario: em hipercool-materiais cada projeto coloca os videos gerados): `shorts\<canal>`, `cortes\<canal>`, `grandes\<canal>`; postados em `hipercool-materiais\_postados\react\<canal>`. As pastas 2-PRONTOS* foram movidas para la; `output\` e `work\` continuam no projeto (intermediarios).

## 11. Memoria de videos ja feitos (2026-10-02, noite) - `mr/memoria.py`, `work/memoria_videos.json`

- Pedido do usuario: "tem que existir uma memoria de quais videos ja foram feitos pra nao repetir" (ele baixa pastas do Drive que
  repetem gravacoes ja processadas, e apaga as pastas de downloads depois).
- `batch` pula o que ja foi feito: mesma impressao do arquivo (sha1 de 2 MB do inicio + fim + tamanho) ou mesmo nome de gravacao com a
  mesma duracao (+-0,6 s). Fica `ja_feito` no state.json.
- `process` (depois da transcricao) para antes de renderizar se for o MESMO VIDEO REAGIDO gravado de novo: impressao visual (dHash do centro
  do conteudo, 1 quadro/0,5 s, gravacao x gravacao) ou fala em comum (trigramas >= 30%). Status `repetido`. `--forcar-repetido` ignora.
- As 22 gravacoes antigas foram registradas por `manhwareact.py memoria --preencher`; como os originais foram apagados, a impressao visual
  delas veio dos Shorts finais (`hashes_origem: saida`) e NAO e usada na comparacao visual (nao bate com gravacao); vale nome+duracao e fala.
- Calibracao: fala em comum entre videos diferentes <= 5%; os dois de espada (16_37_51 e 17_51_13) sao videos DIFERENTES (0% visual).
- `batch --max N` processa no maximo N por rodada (o limite de tarefa em segundo plano e 2 h; ~10 min por video).
