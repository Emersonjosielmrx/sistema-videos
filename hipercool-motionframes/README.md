# MotionFrames — worker de background do hipercool

Projeto IRMÃO do `D:\hipercool-hyperframes`. Enquanto o HyperFrames faz overlays/efeitos
alpha (HTML→MP4), o **MotionFrames** é o **WORKER** que adianta, em background e com a
máquina ociosa, as duas etapas CARAS do render — tudo LOCAL, em CPU:

1. **Depth do parallax 2.5D** — movimento real (câmera entrando na cena) via depth estimation.
2. **Decisão de efeito** (desde 2026-07-03) — qual dos **121 efeitos** aplicar em cada painel,
   pré-decidido e cacheado (motion_director da -fix, triagem por **Haiku** = keyless de Gemini,
   não compete com a quota que a narração dos vídeos usa). Cache em
   `D:\hipercool-inferior-fix\workspace\motion_direction_cache\<md5>.json`.

Assim o render final fica rápido e sem gastar IA na hora: só consome os caches prontos.
O `depth_prefetch.py` faz as DUAS coisas no mesmo loop (use `--no-efeito` p/ só depth).
Cron religado 2026-07-03 (:23 de cada hora, `--limit 60`, sessão-only, auto-expira em 7 dias).

## O que é parallax 2.5D
Estima a profundidade de cada painel (depth map), separa em camadas (fundo/meio/personagem)
e move cada camada em velocidade diferente → sensação de câmera entrando numa cena 3D. É o
teto de "movimento real" que CPU Intel entrega com qualidade. Substitui o Ken Burns falso
(zoom/respiração) do hipercool. Aprovado visualmente pela usuária em 2026-06-30.

## Estrutura
```
engine/parallax_core.py    # gera o CLIP de parallax (depth + 3 camadas + crop animado ffmpeg)
engine/depth_prefetch.py   # BATCH: gera depth maps de todos os caps em background (cron)
cache/depth/<md5>.png      # cache de depth por md5 do conteúdo da imagem (a etapa CARA)
logs/depth_prefetch.log    # log do batch
_testes/                   # comparativos
```

## Por que cachear só o DEPTH
O depth (~20s/painel, Depth-Anything-V2-Small em CPU) é a parte cara e **independe da duração**
do clip. O clip de parallax em si (ffmpeg, ~3s) é barato e sai na hora de gerar o vídeo com a
duração certa do áudio. Pré-fabricar o depth = adiantar 90% do custo sem precisar saber a
duração. Cache por md5 do CONTEÚDO → painel idêntico em obras diferentes = 1 depth só.

## Volume (2026-06-30)
~13.200 painéis em 181 caps já baixados. A ~20s/painel = ~69h de depth — por isso roda em
BACKGROUND, fatiado, aproveitando a máquina ociosa.

## Educado com a máquina
`depth_prefetch.py` checa `tasklist` e **pula a rodada se houver ffmpeg ativo** (render do
hipercool) — nunca compete por CPU. Re-checa a cada painel; se um render começa no meio, para
e retoma depois. Idempotente (pula o que já está no cache). Ctrl-C seguro.

## Comandos
```bash
# batch completo (background)
cd /d/hipercool-motionframes
PYTHONUTF8=1 /d/hipercool-videos/venv/Scripts/python.exe engine/depth_prefetch.py

# fatia p/ cron (para após 80 novos)
... engine/depth_prefetch.py --limit 80
# só uma obra
... engine/depth_prefetch.py --obra taming-noona
# ignora ffmpeg (forçar)
... engine/depth_prefetch.py --ignore-ffmpeg
```

## Cron ativo
Sessão-only, a cada hora (:23), `--limit 80`. Retoma o prefetch quando a máquina está ociosa.
Auto-expira em 7 dias (limite do scheduler). Recriar depois se preciso.

## Integração com o hipercool (PENDENTE — outro agente)
Plano completo: `D:\hipercool-inferior-fix\PLANO_AGENTE_PARALLAX_MOVIMENTO_REAL.md`.
Resumo: o `hiper-pipeline.py` (montagem do clip ~linha 1170-1184) consome este cache de depth.
Aplica SÓ na versão final postada (gemini+voz masc+censura); prévia edge reusa cache se houver,
senão Ken Burns. Implementar DEPOIS da censura (mesmo arquivo do pipeline).

## Dependências (já instaladas no venv D:\hipercool-videos)
transformers 5.12, torch 2.12 (CPU), Pillow, numpy. Modelo baixado no 1º uso (~100MB, cacheado
pelo HuggingFace). `PYTHONUTF8=1` obrigatório (console Windows é cp1252).
