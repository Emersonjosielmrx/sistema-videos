# ManhwaReact - RPA de pos-producao para Shorts de react (rede de canais)

> Para continuar o trabalho: leia `HANDOFF.md` (historico completo, decisoes, o que falhou, pendencias), depois `AUDITORIA.md` e `PLANO.md`.

Transforma uma gravacao bruta (OBS: webcam em cima + video reagido embaixo) em um Short pronto para postar:

1. **Layout** - detecta sozinho a linha entre webcam e conteudo, corta a UI lateral do celular e as faixas pretas com logo/titulo que ja vem
   no video original, e remonta em 1080x1920 (webcam / faixa do canal / conteudo).
2. **Audio** - reducao de ruido (RNNoise), de-esser, compressor e loudness em 2 passos para -14 LUFS (padrao YouTube).
3. **Transcricao** - Groq `whisper-large-v3` (chaves de `D:\postador-de-videos\secrets\groq_keys.json`, ~2 s por video, rotacao de chaves);
   se falhar, faster-whisper local (`small` por padrao, `medium` ja baixado).
4. **Quem fala** - MediaPipe le o movimento da boca na webcam e o Claude confirma pelo texto: so a SUA fala vira legenda; a narracao do video reagido e ignorada.
5. **Cortes** - remove silencios (jump cut), vicios ("e...", "hum"), retakes (frase repetida) e trechos que o editorial mandar tirar.
6. **Editorial (LLM)** - proxy Opus 4.6 -> Sonnet 4.5 -> Claude Code CLI. Devolve: nota, **canal** (por tema), obra/fonte (vai na faixa), janela de ate 90 s,
   gancho, titulo (com hashtags), descricao (3-5 linhas + 10-15 hashtags), 12-20 tags, palavras de impacto, CTA, mood da trilha, trechos a remover,
   divisao em varios Shorts se voce gravou varios reacts seguidos, correcao do Whisper.
7. **Tela** - legendas palavra-a-palavra (palavra ativa na cor do canal, com pop), gancho nos 2,6 s iniciais, **divisoria animada e irregular**
   entre webcam e video (borda rasgada + raio/fogo/glitch na cor do canal, nome da obra e "PARTE x/n" sobre ela, handle no canto), barra de progresso, palavras de impacto grandes com linhas de impacto
   e **zoom no conteudo** com tremor de camera, **emoji colorido** por keyword, **zoom na webcam enquanto voce fala** (1.10x / 1.18x por frase),
   **reacoes** marcadas pelo editorial (risada, choque, amor, raiva, duvida, hype, vergonha) com overlay do acervo + emoji + som de meme,
   **memes do acervo** (imagem ou video de `memes_img`, descritos por visao em `assets/memes_catalogo.json`; o editorial escolhe ate 2 pelo contexto),
   "ASSISTE ATE O FIM" aos 2,8 s, glitch rapido mascarando os cortes do editorial, "DEIXA O LIKE" em 45% do video, CTA final animado
   ("INSCREVA-SE" / "COMENTA O QUE ACHOU" alternando; "PARTE 2 NO PERFIL" quando ha continuacao) e SFX em cada evento.
8. **Audio final** - trilha de fundo por mood com ducking (acervo inteiro de `trilhas/`, fora a blocklist de copyright; `music.safe_only` para restringir),
   **gatilhos de som por palavra** (`assets/gatilhos_palavras.json`: "caramba" -> vine boom, "errou" -> Windows error, "dinheiro" -> caixa registradora...),
   sons de meme nas reacoes, loudness -14 LUFS.
9. **Validacao** - duracao, resolucao, loudness (-14 LUFS +-2) e frames pretos; se falhar, `pronto=false` no postar.json. Intermediarios pesados sao apagados.
10. **Saida** - em `output/<video>/` e copiado para `hipercool-materiais\manhwa-react\shorts/<canal>/`: `<video>.mp4`, `<video>_thumb.jpg` (frame mais expressivo + gancho),
   `<video>_meta.txt` (titulo + 2 alternativos para teste A/B, descricao, tags separadas por virgula, comentario fixado - pronto pra colar), `<video>.postar.json` (postador) e `<video>_relatorio.md`.

## Uso rapido (botao)

1. Jogue o video bruto em `D:\manhwa-react\1-COLOQUE-AQUI\` (atalho "ManhwaReact - COLOQUE AQUI" na area de trabalho).
2. Clique em **"ManhwaReact - PROCESSAR"** na area de trabalho (roda `scripts\BOTAO_PROCESSAR.bat`).
3. O video pronto, o `*.postar.json` e o `*_relatorio.md` aparecem em `D:\hipercool-materiais\manhwa-react\shorts\` (atalho "ManhwaReact - PRONTOS").
   Videos ja processados nao sao refeitos (controle em `work\state.json`); para refazer, apague a entrada la ou use `--force`.

## Uso pela linha de comando

```bat
scripts\processar.bat "D:\downloads\2026-10-01 10-58-04.mp4"
scripts\lote.bat                    :: processa tudo que estiver em inbox\
scripts\vigiar.bat                  :: fica vigiando inbox\ e processa o que chegar
```

Ou direto:

```bat
.venv\Scripts\python manhwareact.py memes            :: (uma vez) descreve os memes do acervo com visao e monta o catalogo
.venv\Scripts\python manhwareact.py musica --por-mood 4 :: gera trilhas originais com MusicGen local (scripts\gerar_trilhas.bat; demora, rodar a noite)
.venv\Scripts\python manhwareact.py ideias <pasta>   :: vigia de formatos sobre videos ja processados
.venv\Scripts\python manhwareact.py process "video.mp4" [--no-llm] [--keep-all] [--force] [--dry-run] [--whisper medium] [--preset veryfast] [--music]
.venv\Scripts\python manhwareact.py analyze "video.mp4"
.venv\Scripts\python manhwareact.py batch  [pasta]
.venv\Scripts\python manhwareact.py watch  [pasta] --interval 30
```

- `--dry-run` faz tudo menos renderizar (gera `work/<video>/part1/edl.json` e `captions.ass` para conferir).
- `--no-llm` nao chama o Claude (gancho/titulo por heuristica).
- `--keep-all` renderiza mesmo que o editorial reprove (nota < `editorial.min_score`).
- `--force` ignora o cache em `work/`.

## Pastas

| Pasta | O que tem |
|---|---|
| `inbox/` | jogue aqui as gravacoes brutas (o `watch`/`batch` processa) |
| `output/<video>/` | mp4 final, `relatorio.md`, `*.postar.json` |
| `work/<video>/` | cache: `clean.wav`, `transcript.json`, `lips.json`, `silences.json`, `editorial.json`, `fixes.json`, `partN/edl.json`, `captions.ass` |
| `assets/fonts` | Montserrat ExtraBold/Black, Luckiest Guy, Bangers (licencas abertas) |
| `assets/models` | `bd.rnnn` etc. (RNNoise) e `face_landmarker.task` (MediaPipe) |
| `assets/sfx` | `whoosh.wav` (gancho), `pop.wav` (keywords) - copiados de `D:\hipercool-materiais\assets\sfx` |
| `models/` | cache do faster-whisper (`small` vem de `D:\recapd-ambientes\producao\models`) |

## Config (`config.json`)

- `channel` - nome, handle (marca d'agua), nicho (vai no prompt do editorial).
- `layout.webcam_bottom_trim` - corta 10% de baixo da webcam (notebook) para dar mais espaco ao conteudo.
- `audio.denoise_model` - `bd` (voz + risadas, padrao), `sh` (narracao), `mp`/`lq` (ruido pesado). `target_lufs` -14.
- `cuts` - `silence_db` -40, `min_silence` 0.35 s, margens 0.12/0.20 s, `pause_keep` 0.18 s, `split_silence` 2.5 s (candidato a separar reacts).
- `lips.threshold` 0.0014 - acima = voce falando (testado: sua fala >= 0.0024, narracao do conteudo <= 0.0007).
- `captions` - fonte, tamanho, 3 palavras por bloco, cor do destaque (`&H0000D7FF` = amarelo), `y_offset_from_divider` -120 (sobre o notebook).
- `overlays` - gancho, marca d'agua, barra, CTA, keywords, punch-in (1.08x).
- `editorial.use_llm` - usa o Claude Code CLI (`claude -p`), sem precisar de API key. `min_score` 5.
- `transcribe.engine` - `groq` (padrao) ou `local`. `paths.groq_keys` aponta para o json de chaves.
- `music` - `enabled` true, `lufs` -30, `safe_only` true (so mixkit/prioritarias), `respect_editorial` true (o Claude desliga a trilha quando o video reagido ja tem musica/narracao).
- `divider` - `style` (electric|fire|glitch|none), `per_channel`, `height` 160, `overlap` 56, `edge` (tear|zigzag|wave|flat). Assets gerados em `assets/dividers/`.
- `overlays.zoom_mode` - `speech` (zoom enquanto fala) ou `cuts` (alterna a cada corte). `cta_overlay`/`keyword_overlay` - nomes de MOVs em `D:\hipercool-materiais\assets\overlays\elemental`.
- `thumb` - fonte/tamanho do gancho e zoom da webcam na thumb.

## Publicar

O `*.postar.json` segue o padrao de `D:\hipercool-materiais\_postados\PADRAO_DOC_POSTAGEM.md` com `canais: ["ManhwaReact"]` e `privacy: private`.
O canal **ManhwaReact ainda nao esta cadastrado** em `D:\credenciais-canais\youtube_canais.json`; e preciso rodar o relogin
(`D:\credenciais-canais\relogin_canal.py`) uma vez para gerar o refresh token. Depois disso o `D:\postador-de-videos\bin\youtube_poster.py`
consegue subir. Dica: os outros canais foram suspensos por postagem automatica em massa; mantenha aprovacao humana e poucos uploads por dia.

## Stack

Python 3.13 (`.venv`), ffmpeg 8.1 (`D:\hipercool-materiais\bin`), faster-whisper, MediaPipe, OpenCV, libass. Tudo roda em CPU.

## HyperFrames (texto animado dinamico)

`mr/hyperframes.py` renderiza composicoes HTML/CSS pelo Chromium (Playwright) em MOV com alpha, com texto e cor do canal: pergunta do comentario
fixado no fim do video, numero falado em destaque ("20 MIL REAIS"), selo "PARTE 2 NO PERFIL", "ASSISTE ATE O FIM" e lower third da obra.
Cache em `assets/hyperframes/`. Novas composicoes: adicionar um template em `TEMPLATES` (CSS keyframes; o tempo e controlado pela Web Animations API).

## Acabamento de imagem e voz

Webcam: `hqdn3d` (ruido), `eq` (contraste/saturacao), `cas` (nitidez apos o upscale 720->1080). Conteudo: `cas`. Quadro: vinheta leve.
Voz: RNNoise -> de-esser -> compressor -> `highshelf` +2 dB em 4,5 kHz (presenca) e -1,5 dB em 250 Hz (abafado). Tudo em `config.json > overlays/audio`.
A lista completa do que esta em uso, descartado e pendente esta em `AUDITORIA.md`.

## Vigia de formatos (quadro de ideias)

A cada video processado, o vigia olha 4 frames do CONTEUDO reagido + a narracao dele e responde: que formato e esse, da para produzirmos
sem gravar (so trilha + imagens, leitura de comentarios, ranking com narracao IA...), como fazer com os recursos do disco D, esforco, potencial
e um exemplo de roteiro. Tudo vai para `ideias\IDEIAS.md` (ordenado por potencial) e `ideias\ideias.json`.
`python manhwareact.py ideias <pasta>` roda sobre videos ja processados; `ideas.tier` escolhe o modelo (sonnet por padrao).

## Canais (rede)

Os canais ficam em `config.json > channels` (slug, nome, handle, cor, nicho, descricao, palavras-chave). O editorial escolhe o canal de cada video
pelo tema e o resultado vai para `hipercool-materiais\manhwa-react\shorts\<slug>\`. `scripts\canais.bat` (ou `python manhwareact.py canais`) gera em `canais\<slug>\`:
`perfil.png` (800x800 com a sua foto), `banner.png` (2560x1440), `marca_dagua.png` (150x150), `descricao.txt`, `palavras_chave.txt`,
`canal.md` (checklist) e `canal.json`. As fotos vem de `paths.photos_dir` (campo `photo` de cada canal = indice ou caminho).

| slug | canal | tema |
|---|---|---|
| manhwareact | ManhwaReact (@ManhwaReact) | anime, manhwa, manga, animacoes |
| cenareact | CenaReact (@CenaReact) | filmes, series, cenas iconicas |
| inventoreact | InventoReact (@InventoReact) | inventos, gadgets, tecnologia, construcao, oficios, curiosidades |

Para criar mais canais: adicione em `channels`, rode `scripts\canais.bat` e pronto; o editorial passa a considerar o novo tema.

## LLM

`editorial.providers`: `["proxy:opus", "proxy:sonnet", "cli"]`. O proxy e o mesmo do Claude do VS Code (`secrets_proxy.json`, gerado a partir das
settings; nao versionar). Modelos em `editorial.models`. O Claude Code CLI fica como ultimo recurso.
