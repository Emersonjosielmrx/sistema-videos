# ANÁLISE — fluxo n8n "3-cria video pequeno" vs nosso pipeline

> Doc de CONTEXTO (não é tarefa). Fonte: `D:\downloads\fabrica de animes-3-cria video pequeno copy.json`.
> É **1 único nó `code` com 5333 linhas de JS** (256 KB) chamado "aplica efeitos" — maior que
> nosso `effects_engine.py` inteiro. Extraído e analisado em 2026-06-30.
> As tarefas concretas derivadas daqui estão em `TAREFA_4..9_*.md`.

## ⚠️ DIFERENÇA DE FORMATO — LER ANTES DE PORTAR QUALQUER COISA
- O fluxo n8n produz vídeo **HORIZONTAL 16:9 (1280×720 → upscale 1920×1080)**.
- O nosso produz **VERTICAL 9:16 (shorts/TikTok, 720×1280 / 1080×1920)**.
- CONSEQUÊNCIA: os **59 filtros visuais** deles são quase todos "imagem centralizada + fundo
  desfocado preenchendo as laterais" (split bg/fg + boxblur + overlay). Isso existe pra
  preencher o 16:9 com imagem retrato. **NÃO porte os filtros literais** — no nosso 9:16 a
  imagem já preenche. O que se aproveita são as TÉCNICAS, não os filter-strings.
- Portar filter-string direto vai quebrar enquadramento. Sempre adaptar a resolução/proporção.

## ESTRUTURA DO JS (16 classes + catálogos)
| Bloco | Linhas | O que é | Já temos? |
|---|---|---|---|
| GLOBAL_CONFIG | 27-225 | 124 chaves: resolução, perfis de qualidade, áudio pro, legenda, memória, análise | PARCIAL |
| VISUAL_FILTERS (59) | 234-379 | filtros bg-blur 16:9, por "tier de leitura" | N/A (formato) |
| TRANSITIONS (80+) | 384-437 | nomes de xfade (inclui manhwa: hlwind/spiral/glitchmem/hextile) | PARCIAL (~temos xfade) |
| MOVEMENTS (85) | 442-617 | zoompan com `tags`+`priority`+`readability` por categoria | PARCIAL (temos ~zoompan) |
| COLOR/BLUR/VIGNETTE/NOISE/SHARPEN | 622-745 | bancos de filtros sutis | PARCIAL |
| CONTEXTUAL_PATTERNS (15) | 750-878 | regex→effectType (ação/leitura/suspense/romance...) + `forceEffect` | PARCIAL |
| EFFECT_TYPE_MAP | 881-905 | effectType→tags+minReadability (liga contexto a movimento) | NÃO |
| MemorySystem | 910-1006 | histórico das últimas N páginas p/ CONTINUIDADE (grading/direção/ritmo) | **NÃO** ⭐ |
| ContentAnalyzer | 1011-1130 | analisa brilho/contraste/temperatura da imagem via `signalstats` → ajuste adaptativo | **NÃO** ⭐ |
| SubtitleParser | 1343-1500 | parse SRT + ASS (karaokê) | parcial |
| SoundEffectsDetector | 1505-1625 | detecta SFX por palavra na legenda, com timestamp por posição da palavra | PARCIAL ⭐ |
| SoundEffectsMixer | 1627-1805 | mixa trilha de SFX com delays (adelay) | temos outro jeito |
| SOUND_EFFECTS_MAP (148) | 1137-1321 | palavra→arquivos SFX + volume + priority | nosso tem 60 |
| AudioProcessor | 2472-2531 | loudnorm/ducking(sidechain)/compressor/de-esser/afftdn | **TEMOS** ✓ |
| SubtitleProcessor | 2536-2667 | legenda por CONTEXTO (shout/whisper/thought) + outline adaptativo ao fundo | **NÃO** ⭐ |
| ImageProcessor/CommandBuilder/etc | 2710+ | montagem de comando ffmpeg | temos o nosso |

## O QUE JÁ TEMOS (não reimplementar)
- **Áudio pro**: loudnorm I=-16 TP=-1.5, acompressor 3:1, sidechain ducking, fade — tudo em
  `effects_engine.py` (`add_dynamic_music`, ~linha 2689; SFX loudnorm ~618/981). O AudioProcessor
  do n8n é praticamente o que já fizemos. Só conferir se falta de-esser/afftdn (ver TAREFA_8).
- **SFX contextual por texto**: `SFX_CONTEXTUAL_MAP` (~60 keys, linha 474) + `pick_sfx_for_text`.
- **Mood→trilha**: `detect_mood_from_text` + moods.json.
- **Movimento Ken Burns/zoompan**: ~53 usos de zoompan.

## O QUE FALTA E VALE A PENA (vira tarefa) ⭐
1. **MemorySystem (continuidade)** → TAREFA_4. Hoje cada painel sorteia efeito isolado; não há
   memória de "qual grading/direção usei nos últimos 3". Dá saltos visuais. Ganho: coesão.
2. **ContentAnalyzer (análise adaptativa da imagem)** → TAREFA_5. Medir brilho/contraste real
   via `signalstats` e ajustar (clarear cena escura, subir contraste de cena lavada, outline
   da legenda conforme fundo). Ganho: legibilidade + qualidade automática.
3. **Legenda por CONTEXTO** → TAREFA_6. Grito = maior+outline forte; sussurro = itálico menor;
   pensamento = itálico. Hoje a legenda é estática. Ganho: expressividade.
4. **CONTEXTUAL_PATTERNS + EFFECT_TYPE_MAP (movimento por emoção)** → TAREFA_7. Ligar a emoção
   detectada ao TIPO de movimento (suspense→zoom no rosto, ação→shake, leitura→pan lento),
   com `forceEffect` e `minReadability`. Hoje nosso movimento não reage à emoção do texto.
5. **Expandir SFX_CONTEXTUAL_MAP** → TAREFA_8. O n8n tem 148 gatilhos (vs nossos 60); várias
   categorias que não cobrimos (magia/teleporte/level-up/notificação/animais/comédia). Cruzar
   com nossa biblioteca de 385 SFX já baixada.
6. **Perfis de qualidade (draft/standard/high/ultra)** → TAREFA_9. CRF+preset por perfil via env,
   pra teste rápido (draft) vs entrega (high). Pequeno e útil no modo noturno.

## NÃO PORTAR
- Os 59 VISUAL_FILTERS literais (formato 16:9). 
- Watermark/basePath/caminhos `/tmp/youtubevideos` (são do ambiente n8n Linux).
- SoundEffectsMixer (já temos mixagem própria que respeita gap dinâmico e anti-repetição).
