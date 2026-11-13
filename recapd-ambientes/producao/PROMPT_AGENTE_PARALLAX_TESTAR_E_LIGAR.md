# PROMPT PRO AGENTE — testar e ligar o PARALLAX (vídeo em movimento) no hipercool

> Cole pro agente que vai dar sequência. O parallax JÁ foi implementado no pipeline (módulo +
> integração + snapshot). Falta TESTAR no pipeline completo, calibrar o visual e ligar nos
> vídeos finais. Trabalhe em `D:\hipercool-inferior-fix`.

## Estado atual (JÁ FEITO — não refazer)
- **`bin/parallax_engine.py`** (NOVO, md5 `ecf799720c963784cb80b733b7b28126`): movimento real
  2.5D via depth map (Depth-Anything-V2, CPU). 3 camadas por profundidade + crop animado ffmpeg.
  Reusa o cache de depth do MotionFrames (`D:\hipercool-motionframes\cache\depth\<md5>.png`).
  Fallback total: falhou → retorna False. Já testado isolado: gera clip 720x1280, áudio sync
  exato (dur 3.00s), usa cache (~5s/clip com depth pronto, ~20s sem).
- **`bin/hiper-pipeline.py`**: integrado na montagem do clip (~linha 1175). Import tolerante
  na linha 45 (`import parallax_engine`). Ramo `if ok: pass / elif is_impact / ...` — o parallax
  tenta primeiro, se falha cai no Ken Burns. ⚠️ Outro agente editou este arquivo depois; a
  integração do parallax sobreviveu (confirmado: 12 refs, sintaxe OK), mas SEMPRE rode
  `md5sum bin/hiper-pipeline.py` e `python -c "import ast;ast.parse(open('bin/hiper-pipeline.py',encoding='utf-8').read())"` antes de editar.
- Snapshots: `bin/_VERSAO_CORRENTE_20260630_parallax/` e pré-edição `bin/_PRE_PARALLAX_20260630_1707/`.
- Doc atualizada: seção parallax no `_VERSAO_CORRENTE_LEIA.md`.

## Flags de controle
- `PARALLAX=1` liga (default OFF = pipeline intacto, Ken Burns de sempre).
- Gate automático: só atua na versão FINAL (`TTS_ENGINE=gemini` ou `eleven` + `--censura`), OU se
  o painel já tem depth no cache (prévia edge reusa de graça), OU `PARALLAX_FORCE=1` (sempre, teste).
- `PARALLAX_TERROR=1`: adiciona atmosfera (vinheta/grão/tom frio) — p/ canal de terror.
- `MOTIONFRAMES_DEPTH_CACHE`: override do dir de cache de depth.

## SUA TAREFA

### 1. Testar no pipeline COMPLETO (cero quota — reusa cache)
Só rode se a máquina estiver OCIOSA (`tasklist | findstr ffmpeg` vazio); senão aguarde, há
render da usuária rodando quase sempre. Rode em background, sem bloquear:
```
cd /d/hipercool-inferior-fix
PARALLAX=1 PARALLAX_FORCE=1 CLIP_GAP_DYNAMIC=1 XFADE_BATCH=8 SUB_SHORT=1 TEST_MODE=1 \
  PYTHONUTF8=1 GEMINI_TTS_PROXY_ENABLED=0 TTS_ENGINE=edge ENSEMBLE_NARRATION=0 \
  /d/hipercool-videos/venv/Scripts/python.exe bin/hiper-pipeline.py \
  --panels-dir workspace/panels/perverts-daily-life-cap01 --titulo "Teste Parallax" \
  --max-panels 12 --subtitles --skip-notify --output-suffix _PARALLAXTEST > parallaxtest.log 2>&1
```
(Há um cron de hora em hora que já tenta isso — confira se `parallaxtest.log` já existe.)

### 2. Validar
- ffprobe: áudio NÃO pode ficar >5s menor que vídeo (regra do projeto). Duração coerente.
- `grep "fallback Ken Burns" parallaxtest.log`: se TODOS os clips caíram no fallback, o parallax
  não atuou — investigue (transformers instalado? cache acessível? erro no log `[parallax]`).
- `grep "\[parallax\]" parallaxtest.log`: deve mostrar "clip ... usa cache" ou tempos de depth.
- Abra o MP4 (`workspace/videos/...`) e cheque VISUALMENTE: movimento natural, sem tremor/
  artefato nas bordas das camadas, profundidade perceptível. Reporte o caminho pra usuária ver.

### 3. Calibrar o visual (se a usuária pedir)
No `parallax_engine.py`, função `build_parallax_clip`:
- `speed = [0.5, 1.1, 2.0]` — velocidade de drift por camada (far/mid/near). Maior = mais
  movimento. Se ficar "tremido" ou enjoativo, REDUZIR.
- Limiares das 3 camadas `[(far,0,0.4),(mid,0.4,0.7),(near,0.7,1.01)]` — ajustar se a separação
  fundo/personagem ficar ruim em certos painéis.
- O `GaussianBlur(6)` nas máscaras suaviza a borda entre camadas (evita recorte duro).

### 4. Ligar nos vídeos finais (decisão da usuária)
Quando aprovado: o parallax deve entrar na versão FINAL postada (Gemini + voz masc + censura).
O gate já faz isso automaticamente com `PARALLAX=1` (sem FORCE). Confirme com a usuária ANTES
de ligar por padrão em produção. A prévia edge reusa depth do cache se houver, senão Ken Burns
(rápido) — esse é o comportamento desejado.

## Contexto de hardware (importante)
3 máquinas Intel SEM GPU. Depth roda em CPU (~20s/painel sem cache). Por isso existe o projeto
**MotionFrames** (`D:\hipercool-motionframes`) que pré-gera os depths em BACKGROUND (cron +
batch `depth_prefetch.py`) aproveitando a máquina ociosa, e o PC2 (192.168.18.7:8771) pode
ajudar. O pipeline consome esse cache. NÃO tente rodar depth de 13k painéis na hora de gerar —
conte com o cache pré-fabricado; sem cache, o parallax gera na hora só os painéis daquele vídeo.

## Regras do projeto
- Confirme cópia certa: `grep -c render_subtitles_short bin/hiper-pipeline.py` > 0.
- NÃO competir com render ativo (sempre cheque ffmpeg antes de rodar pipeline).
- Fallback total já garante que nada quebra; mas valide com ffprobe antes de dizer "pronto".
- Trabalhar local; commit/push e publicação só com confirmação da usuária.
- Após aprovado: congelar snapshot datado novo + atualizar `_VERSAO_CORRENTE_LEIA.md`.
