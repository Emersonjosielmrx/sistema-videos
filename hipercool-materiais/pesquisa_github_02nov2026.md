# Pesquisa de bibliotecas no GitHub para melhorar vídeos (02/11/2026)

Pedido da dona: analisar e pesquisar a fundo bibliotecas e outras coisas do GitHub que ainda não usamos, para vídeos
longos, Shorts, cortes, recap, Veo e Remotion.

Este arquivo é só PESQUISA. Nada foi instalado, nada foi alterado em código de produção, nada foi testado em vídeo real.
Quem for implantar um item segue `D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md` e, para longos,
`D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md`.

## Estado desta pesquisa

- 3 subagentes foram disparados em segundo plano. 2 de pesquisa terminaram (seções B e B2). Falta o inventário do que
  já está instalado nas pastas (gemini-ajudante); quando chegar, acrescentar aqui sem apagar nada.
- Revisão cruzada (conselho de modelos: mandar este documento para o sonnet-ajudante apontar erros com prova): PENDENTE.

## O que já temos (conferido nos arquivos em 02/11)

- Remotion 4.0.538 em `D:\claude-code-video\remotion\package.json`: cli, google-fonts, media-utils, shapes, transitions,
  paths, noise, three, @react-three/fiber, three 0.169.0. Usa efeitos.tsx, karaoke.tsx, vivo.tsx, tres.tsx.
- O package.json de `D:\postador-de-videos\remotion` tem exatamente o mesmo conteúdo (nome e versões iguais).
- Análise anterior (28/10): `D:\hipercool-materiais\novas_tecnologias_analise.md` (Hypit, GSAP, Three.js, PixiJS).
- Lista de melhorias dos longos: `D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md` (L-05, L-06, L-07, L-09, L-10, L-12
  implantados em 01/11 e esperando o 1º longo real; L-08 e L-11 ainda a fazer).
- Candidatos do estudo dos parceiros: `PARA_IMPLEMENTAR.md` tinha 0 aprovados e 710 grupos candidatos em 02/11 01:23.
  Os candidatos de legenda com brilho/glow e de texto "derretendo" combinam com `@remotion/skia` (seção A).

## Correção de erros da minha mensagem anterior (nomes errados de repositório)

| Eu escrevi | Correto |
|---|---|
| raghavachary/magi | ragavsachdeva/magi |
| Requested/kumiko | njean42/kumiko |
| jorgenring/color-matcher | hahnec/color-matcher |

Além disso, escrevi "DepthFlow ~3k+ estrelas" de memória; o subagente informou 1.575. Não conferi nenhum dos dois.

## A. Pacotes oficiais do Remotion que NÃO estão no package.json (citados por mim, de memória, não conferidos)

Instalar todos na MESMA versão 4.0.538 do restante.

- `@remotion/layout-utils` (fitText, measureText): ajusta o tamanho da fonte para o texto caber na caixa.
- `@remotion/motion-blur` (Trail, CameraMotionBlur): borrão de movimento em zoom/entrada rápida.
- `@remotion/lottie`: ícones animados em JSON do LottieFiles.
- `@remotion/skia`: shaders 2D, glow, sombra, texto líquido. Atende os candidatos de glow e de texto derretendo.
- `@remotion/captions` (createTikTokStyleCaptions): agrupa words.json em páginas de legenda.

Cuidado: a licença do Remotion é própria (empresa grande paga). Conferir se o nosso uso se enquadra antes de ampliar.

## B. Resultado do subagente de pesquisa (GitHub), com os nomes de endereço já corrigidos

Estrelas e datas de "último push" abaixo foram INFORMADAS pelo subagente ("via API do GitHub em 02/11"). Não conferi.
Os links no texto bruto dele vieram quebrados; os abaixo foram refeitos por mim a partir do padrão usuário/repositório.

### B1. Manhwa e recap longo

| Repositório | O que faz | Onde entraria | Estrelas informadas |
|---|---|---|---|
| https://github.com/ragavsachdeva/magi | detecta quadros, personagens, balões e quem fala; ordem de leitura | fatiar tira vertical de webtoon sem cortar rosto/balão | 476 |
| https://github.com/njean42/kumiko | extrai quadros de página com calhas definidas (OpenCV) | só página de mangá tradicional, não webtoon contínuo | 205 |
| https://github.com/VoxelCubes/PanelCleaner | limpa texto de página de mangá/manhwa em lote (CLI) | remoção de texto/legenda sem borrão | 489 |
| https://github.com/dmMaze/comic-text-detector | detecta texto e SFX com máscara exata | entrada para o inpainting | 389 |
| https://github.com/dmMaze/BallonsTranslator | detecção + OCR + inpainting (LaMa/AOT) | módulos importáveis em Python | 5.257 |
| https://github.com/zyddnys/manga-image-translator | remoção de texto em lote com LaMa | capítulos inteiros | 10.564 |
| https://github.com/Sanster/IOPaint | servidor/CLI de inpainting (LaMa e outros) | chamada HTTP para apagar marca d'água/balão | 23.297 |
| https://github.com/BrokenSource/DepthFlow | parallax 2.5D por profundidade, em shader | cena de impacto e 1º minuto dos longos (L-06) | 1.575 |
| https://github.com/apple/ml-depth-pro | mapa de profundidade com borda nítida | alimentar o DepthFlow no lugar do mapa atual | 5.773 |
| https://github.com/SkyTNT/anime-segmentation | recorte de personagem 2D (ISNet) | separar herói e fundo para parallax em 2 camadas | 855 |
| https://github.com/ZhengPeng7/BiRefNet | segmentação de alta resolução (há pesos para anime) | recorte de cabelo/espada sem serrilhado | 4.352 |

### B2. Cortes e Shorts

| Repositório | O que faz | Onde entraria | Estrelas informadas |
|---|---|---|---|
| https://github.com/Junhua-Liao/LR-ASD | quem está falando no vídeo (leve, evolução do Light-ASD) | reenquadrar 16:9 para 9:16 seguindo quem fala | 148 |
| https://github.com/Junhua-Liao/Light-ASD | idem, versão anterior | idem | 192 |
| https://github.com/TaoRuijie/TalkNet-ASD | idem, mais antigo | idem | 514 |
| https://github.com/sieve-community/fast-asd | ASD empacotado para produção | idem | 87 |
| https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator | pipeline de referência de corte vertical | só como leitura de código (suavização de câmera) | 5.721 |
| https://github.com/modelscope/FunASR (SenseVoice) e https://github.com/ddlBoJack/emotion2vec | emoção e eventos no áudio (riso, grito, aplauso) | achar o pico de emoção para escolher corte | não informado de forma confiável |
| https://github.com/WyattBlue/auto-editor | corta silêncio e trecho parado | cortes e microcortes | não informado de forma confiável |
| https://github.com/ClipsAI/clipsai | segmenta por tópico e reenquadra 9:16 | cortes de podcast/live | 559 |
| https://github.com/transitive-bullshit/ffmpeg-gl-transition | filtro de FFmpeg que roda transições GLSL | exige FFmpeg compilado com OpenGL; trabalhoso no Windows | 721 |
| https://github.com/gl-transitions/gl-transitions | catálogo de ~100 transições em shader | usar via moderngl em Python, sem recompilar FFmpeg | não informado |

### B3. Emendar clipes do Veo sem corte seco

| Repositório | O que faz | Estrelas informadas |
|---|---|---|
| https://github.com/hahnec/color-matcher | iguala a cor de um clipe ao anterior (Reinhard, MKL, hm-mkl-hm), roda em CPU, `pip install color-matcher` | 678 |
| https://github.com/hzwer/Practical-RIFE | gera 4 a 8 frames intermediários entre o último frame do clipe A e o primeiro do B | 1.034 |
| https://github.com/nihui/rife-ncnn-vulkan | RIFE em binário Vulkan, sem PyTorch | não informado de forma confiável |

## C. Itens que EU citei de memória e que o subagente não confirmou (conferir antes de qualquer decisão)

- https://github.com/deepghs/imgutils: detecção de rosto/cabeça/texto/censura em imagem 2D, ONNX em CPU.
- https://github.com/soCzech/TransNetV2: detecção de troca de cena mais robusta que diferença de pixel.
- https://github.com/spotify/pedalboard: compressor, limiter, reverb em Python, para narração e ducking de trilha.
- https://github.com/hkchengrex/MMAudio: gera som sincronizado com o vídeo (efeitos de impacto).
- https://github.com/bloc97/Anime4K: upscale de traço de anime/manhwa para atender a regra de 1080p mínimo.
- https://github.com/xinntao/Real-CUGAN: upscale de anime.

## D. Avisos antes de instalar qualquer coisa (válidos para todos os itens acima)

1. **Máquina sem GPU.** O PC1 roda só em CPU (regras do projeto: render do longo só em GPU, voz clonada em CPU a ~5x a
   duração). DepthFlow, RIFE ncnn-vulkan, MMAudio, Depth Pro e BiRefNet pedem GPU/OpenGL/Vulkan. Provável destino:
   Kaggle (GPU) ou notebooks. No PC1, os que cabem são color-matcher, pedalboard, imgutils, LR-ASD/Light-ASD e os pacotes
   do Remotion.
2. **Licenças NÃO conferidas.** Suspeitas (não verificadas): Ultralytics YOLO e Pedalboard têm licença copyleft forte; o
   DepthFlow pode ser AGPL; o Magi pode ter restrição de uso comercial. Ler a licença de cada repositório antes de
   usar em produção.
3. **Nada no disco C.** Instalar tudo em `D:\hipercool-materiais` (pip, modelos, cache). Nunca mover `python\venv`.
4. **Uma conexão/script por vez** nas máquinas remotas.
5. **Teste real antes de ligar:** qualquer item entra desligado (env/config), testado num vídeo real com backup, e só
   então ligado.

## B2. Segunda pesquisa (gemini-pro-pesquisa, chegou depois): o que ela CONFERIU de verdade

Ela consultou a API do GitHub (14 repositórios antes de bater no limite), o PyPI e o Hugging Face. O resto ela marcou
como "de memória". Dados conferidos por ela:

| Repositório | Estrelas | Último push | Observação |
|---|---|---|---|
| DepthAnything/Depth-Anything-V2 | 9.079 | 2026-03-24 | só o Small é Apache-2.0; Base/Large/Giant = uso NÃO comercial |
| BrokenSource/DepthFlow | 1.575 | 2026-10-28 | PyPI `depthflow` 1.0.1 (bate com a 1ª pesquisa) |
| facebookresearch/sam2 | 20.090 | 2026-05-30 | segmentação, GPU |
| SkyTNT/anime-segmentation | 855 | 2025-05-21 | bate com a 1ª pesquisa; ONNX em CPU |
| ogkalu2/comic-translate | 2.996 | 2026-10-26 | aplicativo, não biblioteca |
| njean42/kumiko | 205 | 2024-12-22 | bate com a 1ª pesquisa |
| m-bain/whisperX | 24.997 | 2026-10-22 | palavra a palavra |
| jianfch/stable-ts | 2.281 | 2026-05-30 | `align()` casa o roteiro já conhecido com o áudio do TTS |
| remotion-dev/remotion | 69.813 | 2026-11-01 | (a 1ª pesquisa disse ~21k: errado) |
| Breakthrough/PySceneDetect | 5.313 | 2026-11-02 | troca de cena em CPU |
| soCzech/TransNetV2 | 1.072 | 2023-12-04 | parado desde 2023 |
| sniklaus/3d-ken-burns | 1.579 | 2026-06-01 | exige CUDA; DepthFlow é mais prático |
| Hugging Face `ragavsachdeva/magiv2` | 10.759 downloads | — | Magi v2 existe e é usado |
| Hugging Face `mosesb/best-comic-panel-detection` | 23.797 downloads | — | detector YOLO de quadros, roda em CPU |
| Hugging Face `hexgrad/Kokoro-82M` | 11,2 mi downloads | — | já usamos Kokoro (words.json) |

### Divergências entre as duas pesquisas (o que muda a decisão)

1. **Detecção de quem fala (LR-ASD, Light-ASD, TalkNet) NÃO serve para anime.** São treinados em rosto real
   (segundo a 2ª pesquisa, de memória, mas faz sentido: o modelo lê o movimento da boca de gente). Servem só para
   cortes de série com atores e podcast. Para anime: detector de rosto de anime (`deepghs` / `dghs-imgutils`, não
   conferido) + cálculo do recorte 9:16 por conta própria.
2. **pycaps:** o PyPI aponta para `joeblackwaslike/pycaps`; de memória o conhecido é `francozanardi/pycaps`. Não decidido.
3. **Upscale (Real-CUGAN/Real-ESRGAN ncnn-vulkan, Anime4K):** precisam de placa com Vulkan (a integrada pode servir);
   CPU pura não. Anime4K é feito para player, não para lote.
4. **Licenças de pesos (de memória, conferir):** AudioCraft, F5-TTS e Fish Speech são de uso não comercial; MMAudio
   provável. DepthFlow AGPL (com opção comercial), Ultralytics AGPL, pedalboard GPL.
5. `gyoridavid/short-video-maker` (Remotion + Kokoro + Whisper): a leitura falhou; existência não confirmada.

Para fechar as lacunas sem limite de consultas: `gh api repos/DONO/REPO --jq '[.stargazers_count,.pushed_at,.license.spdx_id,.archived]'`.

## E. Ordem sugerida (refeita depois da 2ª pesquisa)

1. color-matcher nas emendas de clipe do Veo: CPU, uma linha de pip, resultado visível.
2. Pacotes Remotion (layout-utils, motion-blur, captions, skia): sem GPU, na mesma pilha, resolvem texto estourando,
   movimento duro e legenda sem brilho. Conferir antes a licença do Remotion (empresa grande paga).
3. stable-ts `align()` para casar o roteiro com a narração: CPU, pode corrigir legenda adiantada/atrasada nos clones.
4. Detector de quadros (YOLO `mosesb/best-comic-panel-detection` em CPU ou Magi v2 em GPU) + remoção de texto
   (PanelCleaner/comic-text-detector) no manhwa: depende de teste em capítulo real e da licença (YOLO = AGPL).
5. DepthFlow + Depth Anything V2 SMALL (o único comercial) nas cenas de impacto: só com GPU (Kaggle).
6. Recorte 9:16 que segue rosto: só para série com atores (LR-ASD); para anime, detector de rosto de anime.
7. pedalboard na narração: depende de resolver a licença primeiro.

## F. Instalado e testado em 02/11 (madrugada, PC1: i5-8365U + Intel UHD 620, sem GPU dedicada)

Vídeos de teste (todos 1080x1920) em `D:\hipercool-materiais\testes_github_02nov\`; scripts em `_scripts\`.
NADA foi ligado na produção. Cada item abaixo entra desligado e só depois do OK da dona.

| Vídeo | O que compara | Resultado | Custo no PC1 |
|---|---|---|---|
| 01_veo_emenda_seco_x_colormatcher_rife | corte seco x color-matcher (MKL, peso caindo em 1,5 s) + RIFE v4.6 (6 quadros de morph) | cor de B puxada para A sem "piscar"; morph funciona, mas o quadro do meio borra quando as cenas são muito diferentes: serve para clipes de pose parecida | color-matcher ~8 s/quadro em 1080x1920 (lento: fazer em resolução menor e aplicar a matriz); RIFE ~60 s/quadro na Vulkan da Intel |
| 02_manhwa_parallax_atual_x_depthflow | 2.5D atual (`clips_2p5d`, sai em 720p) x DepthFlow dolly/orbital/círculo em painel ampliado pelo Real-CUGAN | DepthFlow move a cena inteira em 3D contínuo, traço nítido em 1080p | ~25 s por clipe de 4 s; o processo NÃO fecha sozinho no fim (ficou pendurado; precisa matar ou rodar em subprocesso com timeout) |
| 03_upscale_painel_lanczos_x_realcugan | lanczos + cas (fx_acabamento) x Real-CUGAN 2x num painel 720p | Real-CUGAN: linha preta limpa, sem halo | ~67 s por imagem 720x1280: ok para painel/capa, inviável para vídeo inteiro no PC1 |
| 04_transicoes_gl_transitions | 7 shaders: CrossZoom, Dreamy, GlitchDisplace, GlitchMemories, InvertedPageCurl, WaterDrop, ZoomInCircles | todos funcionam pelo moderngl, sem recompilar ffmpeg | 7 transições em 67 s |
| 05_remotion_fittext_motionblur_legenda | fitText, zoom chicote sem/com CameraMotionBlur, createTikTokStyleCaptions | os 3 funcionam; fitText encolhe demais frase longa (usar com quebra de linha) | render 14 s em ~4 min |

Instalado:
- venv central (`python\venv`): color-matcher 0.6.0, moderngl 5.13.0, depthflow 1.0.1 (+ shaderflow, glfw, imgui-bundle…).
  Nenhuma versão existente mudou (pip --dry-run conferido antes).
- `D:\claude-code-video\remotion`: @remotion/layout-utils, motion-blur, lottie, captions 4.0.538 (backup em
  package.json.bak_02nov e package-lock.json.bak_02nov). O lottie foi instalado mas não testado.
- Binários em `testes_github_02nov\_ferramentas`: rife-ncnn-vulkan 20221029, realcugan-ncnn-vulkan 20220728, 7 shaders.

Armadilhas achadas:
- **rife-ncnn-vulkan no Windows pt-BR lê `-s` com vírgula** (`0,5`); com ponto dá "invalid timestep".
- DepthFlow não fecha o processo depois do render (ver acima).
- (CORRIGIDO) Os clipes 2.5D do cache (`clips_2p5d`) são 720x1280 de propósito: o hipercool renderiza em 720p e
  amplia o vídeo final para 1080x1920 (fx_clips.upscale_to_fullhd / fx_acabamento). O vídeo entregue respeita 1080p.
- Integração em todos os projetos (pedido da dona depois dos testes): ver `testes_github_02nov\PROGRESSO_INTEGRACAO.md`.
- Licenças ainda NÃO conferidas (API do GitHub bloqueou por limite). Antes de produção: DepthFlow (AGPL?), RIFE/CUGAN (MIT?).

Não feito nesta rodada: pesquisa extra (no Opus não se usa subagente; ficaria para um chat no Argon/Sonnet),
MMAudio, LR-ASD, Magi, PanelCleaner, pedalboard (precisam de GPU, licença ou teste em capítulo real).

## G. Licenças CONFERIDAS do que já entrou em produção (02/11 ~08h, chat dos longos)

Lidas do metadado do pacote instalado (venv central) e dos arquivos LICENSE (a API do GitHub estava no limite).

| Item | Licença | O que isso quer dizer pra nós |
|---|---|---|
| depthflow 1.0.1 + shaderflow | AGPL-3.0 | usar internamente pra GERAR vídeo não obriga nada sobre o vídeo; só obriga abrir o código se distribuirmos o programa ou oferecermos ele como serviço a terceiros |
| color-matcher 0.6.0 | GPL-3.0 | mesma coisa: uso interno ok; não embutir em programa que vamos distribuir |
| moderngl 5.13.0 | MIT | livre |
| rife-ncnn-vulkan | MIT (LICENSE no binário) | livre (pesos do RIFE: não conferido) |
| realcugan-ncnn-vulkan | MIT (LICENSE no binário) | livre (pesos da Bilibili: não conferido) |
| gl-transitions | MIT | livre |

Transições em shader no KAGGLE (02/11, chat dos longos): os .glsl não subiam e o moderngl não era instalado — no Kaggle caía
no xfade sem avisar. Agora: montar_pacote sobe tools\gl-transitions; kaggle_trabalhador instala moderngl; realce_visual
abre o contexto por EGL no Linux sem tela.

## H. Segunda rodada de pesquisa (02/11 manhã, chat dos longos) — frentes que a 1ª não cobriu

Disparadas em paralelo (conselho de modelos): (1) áudio e ritmo — cortes na batida, música/SFX com licença comercial,
narração com emoção, mixagem; (2) mascote falando por lip-sync a partir da FOTO (no lugar de gerar cada fala no Veo) +
detector de rosto de ANIME + upscale de vídeo de anime; (3) edição viral — pacotes da comunidade Remotion, legenda
viral em Python, LUTs/grão, pipelines estilo Opus Clip, continuidade de clipes do Veo. Resultados abaixo quando chegarem.
Dona (02/11): "todas são ideias boas, só tem que ver se o que está já não é melhor, como a legenda MIX — se tiver melhor,
blz; tudo que achar que dá pra melhorar, põe os agentes pra pesquisar profundamente". +3 frentes: (4) legenda — existe
algo MELHOR que a MIX? (texto atrás do personagem, emoji animado, estilo Hormozi/Submagic); (5) retenção/views — prever
CTR da capa, achar trecho chato, escolher trecho pra Short, SEO; (6) render mais rápido e bonito — NVENC na T4, filtros na
GPU, upscale de anime em vídeo, subir em 1440p pro YouTube usar VP9/AV1.
REGRA de cada achado: comparar com o que já temos; só entra se for comprovadamente melhor.

### H1. Áudio e ritmo (argon-pesquisa, 02/11 ~08h40; ele diz que CONFERIU 24 repos na API/PyPI/HF — eu não reconferi)
ARMADILHAS de licença (parecem livres no GitHub, os PESOS não são): madmom (pesos CC-BY-NC-SA), MMAudio (pesos CC-BY-NC),
ThinkSound (README proíbe uso comercial), FoleyCrafter (base auffusion CC-BY-NC-SA), XTTS-v2 (CPML não comercial),
YuE2 (CC-BY-NC; a v1 é Apache). essentia = AGPL; Seed-VC, pedalboard, matchering = GPL (uso interno ok).
| Frente | Melhor achado | Licença código/pesos | Onde roda | Comparado ao que temos |
|---|---|---|---|---|
| Corte na batida | CPJKU/beat_this (ISMIR 2024) e mir-aidj/all-in-one (`allin1`: beats, downbeats, BPM e seções intro/refrão/drop) | MIT / MIT | CPU (~15-20 s/música no i5) | hoje NÃO detectamos batida: corte/zoom cai no início da frase |
| Música sem Content ID | ace-step/ACE-Step (3.5B) e ASLP-lab/DiffRhythm (até 4m45) | Apache / Apache | GPU 8 GB (Kaggle T4) | hoje trilha de banco "free" (que também é reivindicada — memória feedback_anti_bloqueio) |
| Música/SFX curtos | Stability-AI/stable-audio-tools (open-1.0 e open-small) | MIT / Community (grátis < US$1 mi/ano) | GPU (small em CPU) | — |
| SFX de banco | MTG/freesound-python filtrando CC0 | MIT / CC0 | CPU | hoje SFX baixados à mão |
| SFX a partir do vídeo | Tencent-Hunyuan/HunyuanVideo-Foley XL (8 GB c/ offload) ou SimianLuo/Diff-Foley | Apache / Hunyuan Community (grátis < 100 mi MAU, vale no Brasil) ; Diff-Foley MIT | GPU (Kaggle) | hoje SFX por palavra-chave (fx_detect) |
| Narração com emoção | resemble-ai/chatterbox + checkpoint ResembleAI/Chatterbox-Multilingual-pt-br (500M) | MIT / MIT | GPU (aceita CPU) | usar como VOZ BASE antes do RVC (hoje base = edge/kokoro): RVC copia a entonação da base -> emoção real mantendo o timbre clonado |
| idem | canopyai/Orpheus-TTS (tags <laugh> <sigh>, checkpoint PT) | Apache / Apache | GPU | idem |
| Clone leve | myshell-ai/OpenVoice V2 | MIT / MIT | CPU | figurantes sem treinar RVC |
| Mixagem | pyloudnorm, slhck/ffmpeg-normalize (2 passadas lineares), dasp-pytorch, ducking com scipy (look-ahead 50 ms só em 300 Hz-4 kHz) | MIT / Apache / BSD | CPU | hoje: master -14 LUFS em 2 passadas (master_loudness) + _ganho_voz; ducking por faixa de frequência NÃO temos |
Top 5 dele: (1) Chatterbox pt-br como base do RVC; (2) ducking seletivo + normalização linear; (3) allin1/beat_this
pra cortar na batida; (4) ACE-Step/DiffRhythm = trilha própria sem Content ID; (5) HunyuanVideo-Foley/Diff-Foley.

### H3. Edição viral, Remotion e Veo (argon-pesquisa, 02/11 ~08h45; diz CONFERIDO na API/npm/PyPI — não reconferi)
Confirmações: pycaps CERTO = francozanardi/pycaps (MIT, 230★; o `pycaps` do PyPI é outra coisa: libcap do Linux — instalar
via git). gyoridavid/short-video-maker EXISTE (MIT, 1.458★: Remotion + Kokoro + Whisper.cpp + MCP).
| Frente | Achado | Licença | Comparado ao que temos |
|---|---|---|---|
| Remotion oficial ainda não instalado | @remotion/skia (shaders SkSL, glow/bloom real, aberração, displacement), @remotion/light-leaks (vazamento de luz em transição), @remotion/animated-emoji (Noto), @remotion/rive | skia/emoji MIT; light-leaks/rive Remotion License | só pra linha Remotion (claude-code-video/produto) |
| Remotion comunidade | av/remotion-bits (AnimatedText, TypeWriter, Particles, Scene3D), stefanwittwer/remotion-animated, reactvideoeditor/remotion-templates | MIT | idem |
| Legenda viral | francozanardi/pycaps (HTML/CSS via Playwright), unconv/captacity, nicolaigaina/ai-video-captions (6 presets Hormozi/MrBeast...) | MIT | ATENÇÃO: a MIX (libass) roda na MESMA passada do ffmpeg a custo ~0; pycaps renderiza HTML quadro a quadro (muito mais lento num longo de 1-2 h). Só pro que o libass não faz (backdrop-filter, gradiente real) — esperar o resultado da frente "legenda" (H4) antes de decidir |
| Cor de cinema | colour-science (LUT .cube) + ray-cast/lut (.cube prontos) + ffmpeg lut3d; ComfyUI-Darkroom (161 películas, halation — SEM licença explícita: não usar o código), Filmimic (GPL-2.0) | BSD/MIT | hoje: eq/curvas próprias. lut3d no ffmpeg = 1 filtro, custo baixo |
| Clipping (ler código) | SamurAIGPT/AI-Youtube-Shorts-Generator (MIT), jipraks/yt-short-clipper (MIT, crop 9:16 com histerese), auto-editor (domínio público: corta silêncio+cena parada), clipsai (MIT, segmentação por assunto), OpenMontage (AGPL, 700 skills de edição), MoneyPrinterTurbo, ShortGPT | MIT/Unlicense/AGPL | melhores_cortes escolhe por LLM; auto-editor útil pra achar tempo morto no longo |
| Veo: emendar/estender | Wan-Video/Wan2.2 e 2.1 FLF2V (ponte entre último quadro A e 1º de B), lllyasviel/FramePack (estende com 6 GB) | Apache-2.0 | hoje: color-matcher + RIFE (RIFE borra quando as cenas são diferentes — FLF2V gera de verdade). GPU (Kaggle) |
| Veo: upscale realista | OpenImagingLab/FlashVSR (CVPR 2026, 1 passo), ByteDance-Seed/SeedVR2, NJU-PCALab/STAR (sem licença) | Apache-2.0 | Real-CUGAN é pra traço de anime; Veo de produto é foto-realista |
| Veo: estabilizar | rfonod/stabilo, vidstab | MIT | — |
Top 5 dele: (1) @remotion/skia + remotion-bits; (2) pycaps; (3) FlashVSR; (4) Wan2.2 FLF2V + FramePack; (5) LUT/halation.

### H2. Mascote falando + análise de anime (gemini-pro-pesquisa, 02/11 ~08h50; diz CONFERIDO na API GH/HF — não reconferi)
MASCOTE (hoje cada fala = 1 geração no Veo: cara, cota, lenta):
| Achado | Anime? | Kaggle T4 | Licença código/pesos | Veredito |
|---|---|---|---|---|
| antgroup/echomimic_v3 (Flash-Pro 1.3B, base Wan2.1) | sim, SEM máscara facial humana | 12 GB, ~8-15 s por s de vídeo | Apache / Apache | MELHOR a partir de 1 PNG (cabeça+expressão+boca); saída RGB -> anime-segmentation devolve o alfa |
| antgroup/echomimic_v2 (accelerated) | sim, meio-corpo + mãos | 12-16 GB, ~20-30 s/s | Apache / Apache | gestos de mão |
| TMElyralab/MuseTalk v1.5 | só boca (inpainting 256x256) | 4 GB, ~20-30 fps | MIT / MIT (README libera comercial) | MAIS RÁPIDO em lote: prepara 1 loop da Maria (as gravações do Veo que já temos!) e anima a boca com qualquer áudio; o alfa do loop fica intacto |
| Descartar | Sonic (CC-BY-NC), Wav2Lip (não comercial), THA3/4 (pesos NC), Hallo2/3 (CodeFormer NC/CogVideoX, pesado), LivePortrait (video-driven, não áudio; modo animal NC), MEMO/FantasyTalking (lentos demais) |
ANÁLISE DE ANIME:
| Uso | Achado | Licença | Onde roda | Comparado ao que temos |
|---|---|---|---|---|
| rosto/cabeça de anime | deepghs/imgutils (`pip install dghs-imgutils`: detect_faces, detect_heads) | MIT / MIT | CPU ONNX ~10-25 ms/quadro | YuNet não pega desenho: hoje a legenda MIX NÃO desvia do rosto e o corte 9:16 é no centro |
| idem | Fuyucchi/yolov8_animeface | AGPL | CPU ~15 ms | alternativa |
| upscale vídeo anime | bloc97/Anime4K via ffmpeg libplacebo (200-500 fps na T4) | MIT | GPU (Kaggle) | hoje spline+unsharp na passada da legenda |
| idem | Real-ESRGAN realesr-animevideov3 (~25-45 fps T4) | BSD-3 | GPU | idem; APISR tem aviso "academic only" no README (evitar) |
| quadros de webtoon | mosesb/best-comic-panel-detection (YOLOv12x, fatiar a tira em 800x1600 com sobreposição) | pesos Apache; lib ultralytics AGPL | CPU 0,3-0,6 s/img | — |
| quem fala cada balão | ragavsachdeva/magi v2/v3 | AGPL | GPU | elenco fixo de vozes por personagem no manhwa |

### H5. Views e retenção (argon-pesquisa, 02/11 ~09h; diz CONFERIDO — não reconferi; estudos via OpenAlex/arXiv/WebFetch)
- CTR de capa: NÃO existe modelo aberto confiável treinado em CTR real do YouTube (os que existem têm 0-2★). O que dá:
  estética/preferência (deepghs/imgutils anime_aesthetic MIT CPU; HPSv2 Apache; ImageReward Apache; PickScore MIT) +
  VLM vendo a capa em 160x90 (tamanho do celular) pra FILTRAR antes do teste A/B do Studio — não substitui o A/B.
- Momento chato no longo: modelos de highlight (UniVTG, QD-DETR, lighthouse) foram treinados em vídeo real, transferem
  mal pra painel de manhwa. Melhor: PySceneDetect (BSD, CPU) como AUDITOR (acusa > 5 s sem troca de imagem/zoom) +
  silero-vad (MIT, CPU: densidade de fala por minuto) + librosa (variação de entonação plana > 45 s) + auto-editor.
  Comparado ao que temos: o L-06/_desprender já força troca a cada ~60% da fala; um auditor no vídeo PRONTO pegaria o que
  escapou. Barato (CPU) — candidato forte.
- Shorts a partir do longo: cruzar pico de emoção do TEXTO (já fazemos no melhores_cortes por LLM) com pico de ENERGIA da
  narração (RMS/entonação) — não fazemos a parte do áudio. Ligar o Short ao longo pelo "Vídeo relacionado" do Studio
  (o youtube_studio_extras tem --relacionado; conferir se o postar_longos/cortes usa).
- Estudos (fonte nos links do relatório): Shorts com AVD 50-60 s tiveram média de 4,1 mi de views (VidIQ); 35 bi de
  views (Buffer): picos em 13 s e 60 s; perda entre 3 e 8 s mata o alcance (OSF 2026, "The Second Decision"): do 4º
  segundo em diante tem que vir a 1ª consequência do gancho, nada de "tudo começou quando"; capa que promete algo que
  não aparece cedo derruba retenção (arXiv 2607.23739): a cena da capa tem que aparecer nos primeiros 15-30 s.
  ATENÇÃO: o memória "Regras Shorts" e o teste T8 (curto x longo) já mediram: 60 s+ chegavam a 1.500 views em 0 de 34
  (anime_auto, comentário de 30/10) — os dados do NOSSO canal valem mais que a média geral; não mudar a duração sem A/B.
- SEO grátis: suggestqueries.google.com (autocomplete do YouTube, hl=pt gl=br) — ele testou ao vivo; pytrends arquivado.
Top 5 dele: (1) ponte dos segundos 3-10 + Short 52-58 s + loop; (2) auditor anti-tédio; (3) Shorts por pico de texto +
energia da voz; (4) seletor de capas antes do A/B; (5) autocomplete no prompt do título.

### H6. Render mais rápido e bonito (argon-pesquisa, 02/11 ~09h10; leu o NOSSO código e fontes da NVIDIA/FFmpeg/YouTube)
CONFERIDO POR MIM no código (02/11 09h15): fx_clips.py:1990 Depth-Anything com device=-1 (CPU mesmo no Kaggle com T4);
fx_clips.py:1626 detector de rosto ONNX só CPUExecutionProvider; TODO encode é libx264 (CPU) — clipes, concat, legenda;
os ~800 clipes saem 1 por vez (sem ThreadPool no anime_segments). Diagnóstico dele: a T4 hoje só trabalha no Applio.
| Mudança | Ganho estimado (dele, não medido) | Risco |
|---|---|---|
| h264_nvenc na T4 (clipes: -preset p2 -rc constqp -qp 19; final: -preset p6 -tune hq -rc vbr -cq 20 -b:v 0 -multipass qres -spatial-aq 1 -temporal-aq 1 -bf 2 -b_ref_mode middle) | encode 7-10x; -90 a -140 min por longo | sem -b:v 0 o cq vira 2 Mbps; T4 = sessões ilimitadas (placa de datacenter) |
| clipes em paralelo (4 workers) | -60 a -110 min | disco/RAM do Kaggle |
| passada final em 4 fatias (-ss/-to -copyts ... setpts=PTS-STARTPTS) + concat -c copy | legenda single-thread 3,5x | libass é single-thread: é o gargalo da passada final |
| fx_visual ANTES do upscale (720p) e legenda depois | -55% de CPU dos efeitos | ATENÇÃO: hoje fx_visual está DEPOIS do scale de propósito (frames 1080 com os W/H do fx_visual); mudar exige refazer W,H=1280x720 no filtro |
| upscale: Anime4K via libplacebo (Vulkan) OU lanczos+cas=0.5 no lugar de spline+unsharp | sem halo branco no traço | libplacebo precisa Vulkan no Kaggle (não garantido); lanczos+cas funciona em qualquer ffmpeg |
| Depth-Anything e detector de rosto na GPU quando houver (device=0 / CUDAExecutionProvider) | 2.5D e rosto 15x | nenhum (cai pra CPU sozinho) |
| subir em 2560x1440 | YouTube usa VP9/AV1 com bitrate maior (tabela oficial: 1080p60 12 Mbps x 1440p60 24 Mbps) | arquivo ~40% maior; só viável com NVENC |
| música + loudnorm só no áudio (não regravar o vídeo de 1 GB 2x) | -35 min, menos disco | — |
Top 5 dele: (1) NVENC; (2) clipes em paralelo + fatias na passada final; (3) fx_visual em 720p + áudio separado;
(4) Anime4K ou lanczos+cas; (5) 1440p + GPU no Depth/rosto. Estimativa dele: longo de 3-5 h -> 35-55 min (não medido).

### H4. Legenda: existe algo melhor que a MIX? (gemini-pro-pesquisa, 02/11 ~09h15)
VEREDITO: NÃO. Nenhum repositório aberto tem desenho diferente por palavra (5 desenhos por peso), nem sincronia pelo
tempo real do TTS (WordBoundary); todos usam 1 estilo por vídeo + tempo do Whisper. Trocar a base por pycaps (HTML via
Chromium: lento e pesado em RAM), captacity, Capite ou templates Remotion = RETROCESSO em custo e variedade.
O que os produtos comerciais têm e nós não — vale acrescentar:
1. DESVIO DO ROSTO (prioridade alta): detector de anime (deepghs/imgutils, H2) 1x por imagem; posição da MIX evita a caixa.
2. Emoji/ícone por palavra-chave (PNG Twemoji/Noto via overlay; conferir licença) + SFX curto no pop da palavra pesada.
3. Texto ATRÁS do personagem só em cenas de destaque: SkyTNT/anime-segmentation (Apache) -> máscara -> alphamerge por
   cima do vídeo legendado. Custa GPU/inferência; piloto em 20 quadros antes.
Outros: pseudo-3D dá com \frx\fry no libass (ganho pequeno); PyonFX (LGPL, repo certo CoffeeStraw/PyonFX) é a mesma área
que já fazemos à mão. Estudo de retenção sobre legenda: nenhum confirmável — medir com A/B no nosso canal.

## Aprendizado (obrigação do LEIA_ANTES_DE_MELHORAR)

Esta rodada foi só pesquisa. 0 aplicados, 0 reprovados, 710 candidatos deixados (nenhuma melhoria de código foi feita).
