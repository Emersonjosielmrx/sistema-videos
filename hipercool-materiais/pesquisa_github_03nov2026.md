# Pesquisa GitHub de melhorias nos vídeos — 03/11/2026 (retomável)

Pedido da dona: busca completa no GitHub com os sub-agentes; depois ampliou para: voz clonada mais rápida,
narração mais humana, efeitos modernos (além dos V-01..V-17), Remotion/FFmpeg novos, desempenho com GPU do Kaggle,
viralização por projeto e inteligência no melhorador (funil do que dá certo).

Não repetir o que já está em `pesquisa_github_02nov2026.md` (magi, DepthFlow, RIFE, CUGAN, gl-transitions,
auto-editor, TransNetV2, pedalboard, MMAudio, color-matcher etc.).

## Frentes (9 ajudantes, sem Opus)
| # | Frente | Ajudante | Status |
|---|--------|----------|--------|
| 1 | Áudio, voz, trilha (repos) | argon-pesquisa | rodando |
| 2 | Visual/edição (repos) | gemini-pro-pesquisa | rodando |
| 3 | Retenção, capa, SEO | argon-pesquisa | rodando |
| 4 | Anime/manhwa + controle de qualidade | gemini-pro-pesquisa | rodando |
| 5 | Voz clonada rápida + narração humana | argon-pesquisa | rodando |
| 6 | Efeitos modernos FFmpeg/GLSL/Remotion (V-13..V-17 + novos) | gemini-pro-pesquisa | rodando |
| 7 | Desempenho / GPU Kaggle / NVENC / QSV | argon-pesquisa | rodando |
| 8 | Viralização + melhorador que aprende | gemini-pro-pesquisa | rodando |
| 9 | Diagnóstico local: melhorador e voz clonada | sonnet-ajudante | rodando |

| 10 | Roteiro e storytelling (recap, gancho, humor, cliffhanger) | gemini-pro-pesquisa | rodando |
| 11 | Legenda: alinhamento palavra a palavra + tipografia | argon-pesquisa | rodando |
| 12 | Trilha, batida e efeitos sonoros (beat-sync, CC0, humor) | gemini-pro-pesquisa | rodando |
| 13 | Capa + geração de imagem open (FLUX/SDXL anime, personagem consistente) | argon-pesquisa | rodando |
| 14 | Mascote, avatar falante, apresentador de produto | gemini-pro-pesquisa | rodando |
| 15 | Localização/dublagem multilíngue | argon-pesquisa | rodando |
| 16 | Longos: estrutura, capítulos, compilados, cortes→Shorts | gemini-pro-pesquisa | rodando |
| 17 | Distribuição: algoritmos TikTok/Insta/Kwai/YT 2026, metadados | argon-pesquisa | rodando |
| 18 | Direitos/políticas: pré-checagem, conteúdo reutilizado/inautêntico, rótulo IA | gemini-pro-pesquisa | rodando |
| 19 | Orquestração: fila entre PCs+Kaggle, cache, monitoramento | argon-pesquisa | rodando |
| 20 | Formatos por nicho: comédia/comentários, histórias, produto local | gemini-pro-pesquisa | rodando |

Depois: revisão cruzada (um modelo confere o outro) e lista final priorizada.

## Achados
(preencher conforme chegam)

ATENÇÃO: frentes 6 e 8 (gemini-pro-pesquisa) voltaram SEM abrir a web (0 ferramentas, de memória). Links precisam
de conferência antes de implantar.

### 9 — Diagnóstico LOCAL (gemini-ajudante, fatos com caminho; análise minha)
Melhorador — JÁ TEMOS mais do que a pesquisa supôs:
- A/B de verdade: `recapd\bin\variantes.py` (braço por md5) + `placar_variantes.py` (P(braço>A) >= 0,95 com
  metricas_studio), `colab\cliente.py:265` (A/B nos longos via experimento.json), `linhas\LONGOS\AB_RESULTADOS.md`,
  `comum\placar_titulos.py` (CTR vs mediana do canal), `engenharia_reversa\prever_retencao.py` (prevê retenção
  antes do upload), `melhorador_central.py` (usa continuaram/% assistido/impressões/CTR/ret_meio/ret_fim do Studio).
- Buracos: (1) `aprendizado.py` só estuda vídeos (parceiros) com Claude+Gemini e gera ideia; não fecha o ciclo com
  métrica (ideia aplicada nunca é medida depois); (2) 726 grupos de candidatos parados e só 2 aprovados; (3) o A/B
  existe só no recapd (Cortes) e nos longos — hipercool/historias/comentários/produtos não sorteiam braço;
  (4) A/B fixo com P>=0,95 demora: Thompson (bandit) gastaria menos vídeo no braço ruim; (5) não há juiz calibrado
  (nota do VLM vs views reais) nem ligação "ideia aplicada -> braço de teste".
- Próximo passo natural: toda ideia aprovada do aprendizado vira BRAÇO no variantes.py (comum a todos os projetos)
  e o placar decide; trocar o critério fixo por Thompson.
Voz clonada:
- Fluxo: edge Francisca/Andrew ou Kokoro (ONNX) -> RVC (Applio). PC1 CPU: ~2-4x a duração do áudio (~19x com o PC
  a 100%) — `hipercool-materiais\bin\voz_clonada.py:26`. Kaggle em lote: `recapd\bin\voz_clonada_nuvem.py`.
- Emoção: `recapd\bin\climas_voz.py` já tem 9 climas (rate, tom, f0, pausa, EQ, eco). Falta: respiração,
  não-verbais (risada/suspiro), ênfase por PALAVRA, prosódia marcada pelo LLM frase a frase.
- Regra existente (clone2\PROGRESSO.md:71): "nada que aumente o tempo de produção".
- Caminho mais promissor p/ velocidade: TTS que já clona em 1 passo (sem RVC) em lote na T4 — pesquisar na rodada.
Efeitos: V-01..V-12 FEITOS; V-13..V-17 A FAZER (`video-fila\linhas\VISUAL\VISUAL_MELHORIAS.md`) — receitas na seção 6.

### 8 — Melhorador que aprende (de memória, conferir links)
- Métrica-alvo: "viewed vs swiped" (Shorts) / retenção 30 s (longo) em 72 h, ÷ mediana do canal (últimos 20).
- Bandit Thompson por RECEITA (tipo de gancho, faixa de duração, estilo de legenda) por nicho; 20% exploração;
  libs: fidelity/mabwiser, vowpal_wabbit; zr-obp p/ avaliar com histórico.
- GBM (LightGBM) + SHAP sobre features objetivas; modelo hierárquico por canal (bambi/statsmodels mixedlm).
- Juiz Gemini com rubrica 1-5 com âncoras, justificativa antes da nota; CALIBRAR: acurácia em pares mesmo canal/
  semana (>60%) + Spearman (>0,2) + isotônica; revalidar a cada 4 semanas. DOVER/VideoScore = só defeito técnico.
- DSPy/GEPA, TextGrad, OPRO: otimizar prompt de roteiro/título contra o juiz calibrado (não contra views cruas).
- Coleta: CSV do Studio por conta pela saída dela (regra do IP!); yt-dlp público p/ parceiros (campo heatmap).
- Shorts: views mudaram de contagem em 31/03/2025 -> não comparar com antes.
- Arquitetura 7 passos: coletor -> features -> rótulo 72h -> GBM+SHAP semanal -> juiz calibrado -> bandit de
  receitas + DSPy -> funil (vence 3 ciclos = padrão; perde = aposenta).

### 6 — Efeitos (de memória, testar filtros)
- V-13 ondulação: shockwave GLSL (pixi-filters ShockwaveFilter / pmndrs postprocessing) ou ffmpeg displace com mapa
  geq em 270x480 ampliado (barato). V-14 dupla exposição: BiRefNet/rembg + blend screen 0,6 em P&B. V-15 espada:
  xfade custom diagonal com linha branca (simples) ou shader gl-transitions com metades se separando; Remotion
  @remotion/paths. V-16 diagonal: clip-path no Remotion ou máscara geq+alphamerge. V-17 olho: bbox dos olhos
  (Gemini / hysts/anime-face-detector) no painel ORIGINAL, 0,10-0,15 s, flash 1-2 quadros + "ting".
- Novos por impacto: impact frame P&B invertido (2-3 quadros), speed ramp por easing, RGB split pulsante
  (rgbashift nas batidas), BEAT-SYNC automático (beat_this/librosa -> JSON dispara efeitos), bloom, shake por
  ruído (@remotion/noise), speed lines de mangá pré-geradas com alfa, freeze-frame com contorno estilo JoJo
  (SAM 2), light leaks, lens flare, halftone, ink reveal, afterimage (lagfun/tmix), grain, letterbox dinâmico,
  LUT por cena, câmera 3D em camadas (SAM2+inpaint+@remotion/three, Depth-Anything-V2).
- Libs: BrokenSource/ShaderFlow (mesmo autor do DepthFlow), pmndrs/postprocessing, pixijs/filters (MIT).
  Shadertoy padrão = CC BY-NC-SA (NÃO comercial).

### 14 — Mascote / avatar falante (de memória, conferir)
- T4 = Turing: sem bf16/fp8/FlashAttn2; repos base Wan esperam bf16 -> usar GGUF/int8 (fp16 pode dar NaN).
- Mascote: facebookresearch/AnimatedDrawings (CPU, segundos; andar/acenar por BVH) + pkhungurn/talking-head-anime-4
  (rosto por parâmetros, emoção por trecho, boca pelo volume) ou rig Inochi2D (BSD, livre) / padrão Open-LLM-VTuber
  (tag de emoção -> expressão). Live2D SDK = proprietário.
- Apresentador pt-BR: TMElyralab/MuseTalk 1.5 (MIT, ~6-8 GB, ~15-40 s por 10 s na T4) sobre loop curto;
  LatentSync 1.5 (Apache, melhor dente, 3-8 min/10 s); InfiniteTalk/MultiTalk (Apache, corpo+gesto, só lote GGUF
  480p, 20-60 min/10 s). LivePortrait: pesos InsightFace NÃO comerciais.
- Clipes reaproveitáveis da mascote: Wan2.2 TI2V-5B GGUF (8-25 min/5 s) ou Wan2.2-Animate com vídeo-guia; poses
  novas consistentes com Qwen-Image-Edit (Apache). FLUX Kontext dev = não comercial. Inviáveis na T4: Hallo3,
  FantasyTalking, Wan S2V 14B; Sonic = não comercial.

### 4 — Anime/manhwa + qualidade (CONFIRMADO na API do GitHub 03/11)
1. QwenLM/Qwen3-VL (Apache, 20k★) — entender página e gerar roteiro do recap; 2B/4B ou quantizado na T4.
2. YaoFANGUK/video-subtitle-remover (Apache, 13,6k★, jun/2026) — tira legenda queimada/marca de texto, pronto.
3. sczhou/ProPainter (licença a conferir, provável NÃO comercial) — inpaint de vídeo.
4. notAI-tech/NudeNet (AGPL, CPU ONNX) — caixa de nudez p/ mosaico só no trecho.
5. m-bain/whisperX (BSD) — tempo por palavra / conferir sincronia.  6. smacke/ffsubsync (MIT, CPU) — corrige
   deslocamento legenda-áudio.  7. intro-skipper (GPL, C#) — só a técnica de achar abertura/encerramento por
   impressão de áudio entre episódios.  9. acoustid/chromaprint — impressão de áudio (pré-checar música).
10. Netflix/vmaf — perda de qualidade no upscale.  11. PaddleOCR (Apache) — máscara de texto queimado.
12. DiffuEraser (Apache, GPU pesada).  Evitar (sem licença): manga-colorization-v2, MiniMax-Remover.
DOVER parado desde 2024. ffmpeg blackdetect/freezedetect já resolvem quadro preto/congelado.

### 17 — Distribuição (de memória, conferir fontes)
- MAIOR RISCO: YouTube "conteúdo inautêntico" (15/07/2025) pega canais automáticos de modelo repetido -> variar
  estrutura/abertura/ritmo/narração entre canais; comentário próprio no recap.
- Shorts: ler "viewed vs swiped away" por canal; final emenda no começo (loop); views contam replay desde 31/03/2025.
- 3-5 hashtags; tags quase sem peso; palavra buscada no título + 2 primeiras linhas.
- Tradução automática de título do YT: preencher tradução manual nos multilíngues; marcar idioma padrão certo.
- Test & Compare só nos longos (miniatura; título a conferir). "Related video" liga Short -> longo (funil).
- Reels: envios por DM pesam muito -> fechar com frase "manda pra um amigo"; Trial Reels em conta nova.
- TikTok = busca: palavra no texto na tela no 1º segundo; Creator Rewards exige > 1 min.
- Rótulo de IA obrigatório (YT/TikTok/Meta) quando voz clonada/cena parecer real.
- Comentário fixado com pergunta "A ou B?" (pelo navegador). Facebook/Kwai/Dailymotion = alcance, não receita.
### 12 — Trilha, batida, SFX (de memória, conferir licenças dos PESOS)
- Pilha: CPJKU/beat_this (batida+downbeat, CPU) -> ACE-Step (Apache, trilha própria = mata reivindicação; testar
  na T4 sem bf16) -> CLAP (LAION Apache / msclap MIT) escolhe música e SFX por texto do clima -> SFX CC0
  (Freesound CC0, Kenney, Sonniss GDC) -> FFmpeg sidechaincompress + loudnorm 2 passadas (-14 LUFS, -1 dBTP).
- allin1 = segmentos (refrão/drop) p/ cortar a luta no drop (Kaggle). librosa = fallback CPU.
- NÃO comercial: MusicGen (pesos CC-BY-NC), madmom (modelos NC), Essentia models (NC); BBC SFX; REVISAR licença
  dos pesos do MMAudio que já usamos!
- Stable Audio Open (Community License, grátis < US$1M). YouTube Audio Library = pool manual rápido sem claim.
- SFX por evento: PySceneDetect (corte->whoosh), fluxo óptico (golpe->impacto), whisper+LLM (piada->risada).
- Duração: PyMusicLooper (MIT) + corte no compasso + crossfade; rubberband p/ esticar.

### 16 — Longos (de memória; cruzar com LONGOS_MELHORIAS.md antes de aplicar)
- Capítulos direto do ROTEIRO (0:00, >= 3, >= 10 s, título com palavra buscada); sem roteiro: whisper + TextTiling.
- Onde a retenção cai: CSV de retenção do Studio (ou OAuth só leitura) + deepcharles/ruptures -> cruzar com a cena.
- Cortar Shorts nos picos do HEATMAP do yt-dlp do próprio longo após 1-2 semanas (sem rajada).
- Checagem antes de subir: PySceneDetect + librosa = nenhum trecho de 2-3 min sem mudança.
- Short cortado termina em tensão + "related video" p/ o longo; tela final p/ próximo episódio; playlist em ordem.
- Mid-roll só em fim de arco. Cold open 10-15 s com o melhor momento; recap interno no começo de cada arco.

### 20 — Formatos por nicho (de memória, fraco)
- Comédia: comentário como CARD na tela enquanto o personagem lê (RedditVideoMakerBot); chat-story (balões de
  WhatsApp + "digitando…" + som) fácil no Remotion; ritmo: pausa 0,3-0,5 s antes do remate, nada parado > 2-3 s;
  dupla "sério x caos" nas vozes. Esqueleto: gyoridavid/short-video-maker (Remotion+Kokoro+whisper.cpp).
- Histórias: ficha fixa por personagem (texto + 1-2 refs) em todo prompt; troca de imagem a cada 3-5 s; loop no fim.
- Solar: conta R$X->R$Y em tela cheia, obra do dia (timelapse/drone), depoimento UGC, carrossel "fio B / payback /
  Lei 14.300 / Equatorial Pará" — números só com o cliente confirmando.
- Mistérios/tech: mapa + linha do tempo animados, "mas tem um detalhe…" a cada 60-90 s.

- Agendadores Postiz/Mixpost quebram nossas regras (API + mesmo IP); copiar só ideias (jitter, limite, chave geral).
