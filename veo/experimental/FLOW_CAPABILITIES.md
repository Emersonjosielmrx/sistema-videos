# Google Flow — Mapa Completo de Capacidades

## Modelos Disponíveis

### Text-to-Video (T2V)
| Model Key | Label | Notas |
|---|---|---|
| `veo_1_5_t2v` | VEO 1.5 | Legado |
| `veo_2_0_t2v` | Veo 2 | Qualidade base |
| `veo_2_0_distilled_t2v` | Veo 2 - Fast Mode | Rápido, menor qualidade |
| `veo_3_0_t2v` | Veo 3 | COM ÁUDIO, alta qualidade |
| `veo_3` | Veo 3 (genérico) | Key alternativa |
| **`veo_3_1_t2v_fast_portrait`** | **Veo 3.1 - Fast** | **MODELO ATUAL (selecionado na conta fabrica)** |

### Image-to-Video (I2V)
| Model Key | Label | Notas |
|---|---|---|
| `veo_1_5_i2v` | VEO 1.5 | Legado |
| `veo_2_0_i2v` | Veo 2 | Base |
| `veo_2_0_distilled_i2v` | Veo 2 - Fast Mode | Rápido |
| `veo_2_0_i2v_loop` | Veo 2 Loop | Gera loop contínuo! |
| `veo_2_1_distilled_i2v` | Veo 2.1 - Fast Mode | |
| `veo_2_1_i2v_distilled_9fps` | Veo 2.1 - Fast Mode (9fps) | Menor framerate |
| `veo_3_i2v_fast` | Veo 3 Fast I2V | |
| `veo_3_1_i2v_fast` | Veo 3.1 Fast I2V | |
| `veo_test_i2v_distilled` | (teste interno) | |

### Especiais
| Model Key | Notas |
|---|---|
| `veo_2_1_fast_d_15_with_start_image_and_end_image_interpolation` | Interpolação entre 2 imagens! |
| `veo_2_with_g1_plan` | Veo 2 com plano G1 (tier) |

### Gemini Omni Flash (NOVO — mais capaz)
- "Create and edit videos from any input reference — real or generated"
- "Leap forward in world understanding, multimodality, conversational editing"
- Suporta edição conversacional de vídeo
- Frames for Omni Flash "coming soon" — por enquanto usar Veo 3.1 lite

## Modos de Geração
| Modo | Descrição |
|---|---|
| `TEXT_TO_VIDEO` | Prompt de texto → vídeo |
| `IMAGE_TO_VIDEO` | Imagem + prompt → vídeo (animação) |
| `VIDEO_TO_VIDEO` | Vídeo + prompt → vídeo editado |
| `REFERENCE_TO_VIDEO` | Referência (imagem/vídeo) → vídeo novo |
| `EDIT_VIDEO` | Edição conversacional |
| `VIDEO_EXTENSION` | Estender duração de vídeo existente |

## Aspect Ratios
- `LANDSCAPE` (16:9 — 1920x1080)
- `PORTRAIT` (9:16 — 1080x1920)

## Durações
- `4S` — 4 segundos
- `6S` — 6 segundos (padrão)
- `8S` — 8 segundos
- `10S` — 10 segundos

## Features Especiais
- **Characters** — Criar personagens com look, voz e personalidade. Referenciar via @tag
- **Flow Agent** — Agente criativo: brainstorming, prompting, batch editing
- **Audio** — Veo 3+ gera vídeo COM áudio. Toggle "Retornar vídeos sem áudio" nas settings
- **Loop** — veo_2_0_i2v_loop gera vídeo em loop contínuo
- **Interpolação** — veo_2_1 interpola entre imagem inicial e final

## Tools/Applets (processamento)
### Vídeo
Grid Architect, DepthWarp 4D, Image Editor, Video Sketch, Transition Machine,
Shader Effects, Type Overlays, pixelBento, Poster Designer, Weirdcore,
Video Resizer, Stringout Creator, Video Granulator, Datamosh, 3D Model Visualizer

### Imagem
Simple Sketch, Scene Explorer, Mockup, Shot Explorer, Mask Magic, Converge

### Criativo
Character X-Ray, Style Writer, Storyboard Studio, Prompt Tree, Story Sketch

### Experimental
Frame Deconstructor, Blob Tracking, Scout360, Ribbit, Whisk, Pose Text, 3D Face Swap

## Conta Atual
- Email: fabricadeautomacoesia@gmail.com
- Créditos: 970
- Tier: PAYGATE_TIER_ONE / G1_TIER1 / SERVICE_TIER_INTERMEDIATE
- Modelo selecionado: veo_3_1_t2v_fast_portrait

## COMO O FLOW REALMENTE FUNCIONA (descoberto 2026-07-01) — CRÍTICO
O Flow NÃO tem dropdown de modelo na UI. É um **AGENTE CONVERSACIONAL**:
- Endpoint: `https://aisandbox-pa.googleapis.com/v1/flowCreationAgent/sessions/{sessionId}` (GET pega histórico)
- O prompt vai como `userMessage.userPrompt.parts[{text}]`
- O agente **PENSA** (thinkingEvent) e **DECIDE** modelo/modo/formato a partir do texto do prompt:
  - "walking slowly"/"cinematic" → ele escolhe VÍDEO (não imagem)
  - "I've confirmed the default video model is Omni Flash" (ou Veo 3.1 lite)
  - Se prompt não indica movimento → ele gera 4 IMAGENS
- `agentMode`: `AGENT_MODE_PLANNING` = pede confirmação ("Confirmar antes de gerar = Sempre" nas settings)
  - Mudar pra **"Nunca"** → gera e gasta créditos automaticamente (sem clique extra)

### Controles reais da UI
| Elemento | Seletor | Função |
|---|---|---|
| Caixa de prompt | `[contenteditable='true']` (1º) | escreve o prompt |
| Botão Criar/Gerar | `button` com texto `arrow_forward` | submete |
| Botão Configurações | `button` com texto `tune` + `Configurações` | abre painel |
| Adicionar mídia | `button` com texto `add` + `Adicionar mídia` | upload img/vídeo (i2v) |

### Painel de Configurações (radio buttons, ordem por posição y)
- **Confirmar antes de gerar**: Sempre / Nunca
- **Padrão de geração de IMAGENS**: aspect 16:9,4:3,1:1,3:4,9:16 + upscale 1x,x2,x3,x4
- **Padrão de geração de VÍDEO**: aspect **16:9 / 9:16** + duração **1x,x2,x3,x4**

### Como forçar modelo/áudio/formato (via automação)
1. **Formato/duração**: abrir Configurações (`tune`), clicar radio 9:16 e duração desejada.
2. **Modelo + áudio**: incluir no PROMPT: "generate an 8-second video WITH audio using Veo 3.1..."
   (o agente respeita override explícito no texto). Veo 3.1 já traz áudio por padrão.
3. **Confirmação**: setar "Nunca" uma vez → gerações seguintes são automáticas.
4. **Image-to-video**: clicar "Adicionar mídia", subir imagem, depois escrever prompt de animação.
