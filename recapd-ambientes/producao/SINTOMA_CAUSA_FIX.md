# 🔧 SINTOMA → CAUSA → FIX (auto-atendimento)

Antes de investigar do zero, procure o sintoma aqui. Rode `bin/doctor.py` primeiro (raio-x).

| Sintoma | Causa provável | Fix |
|---|---|---|
| **"Rodei mas não vi diferença"** (efeitos) | Flags de efeito desligadas | Rode com `--preset teste` (liga tudo). O log no fim mostra `📊 Efeitos: parallax=X panel-fx=Y...` — se der 0, tem pista. |
| **Parallax não aparece** (`parallax=0` no resumo) | Depth não cacheado p/ esses painéis (o cache é por md5 do arquivo) | Ligue `PARALLAX_ONDEMAND=1` (gera o depth na hora + cacheia). `doctor.py --cap <cap>` mostra a cobertura. |
| `ModuleNotFoundError: numpy/torch/cv2` | Python errado (system em vez do venv) | Use **`D:\hipercool-videos\venv\Scripts\python.exe`** sempre. |
| **Mascote só 1 pose** | Faltam os .mov das poses no projeto | Copie de `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_*.mov` p/ `workspace/assets/overlays/elemental/`. |
| **Card cinza/LIKE full-screen no meio** | Vídeos em `overlays/transitions/` (entram como clip entre painéis) | Apague os indesejados de `workspace/assets/overlays/transitions/`. O CTA pequeno (canto) é do `elemental_transitions`, esse fica. |
| **Censura vazou** (painel +18 passou) | Score abaixo do limiar OU detecção não rodou | Confira `censura_visual.detectar_score(painel)`. Limiares em `censura_visual.py` (`CENSURA_LIMIAR_*`). NÃO é bug de tarja — a censura é na imagem (exodia/blur). |
| **Legenda dessincronizada** | Drift de timing | Rode com `DUMP_SUBS_TIMING=1` → gera `<video>.timing.txt` (mapeia clip↔tempo↔painel). |
| **ffmpeg crash "código 1"** no split-shorts | Corte degenerado ou stream ruim | Agora ele **loga o stderr** e pula só aquele short. Veja o stderr no log da parte. |
| **Editei e não surtiu efeito** | Editou a cópia errada (`bin/_SNAPSHOT_*`/`_VERSAO_*`) ou outro dir (`-inferior`, `-BOM`...) | Edite só `bin/*.py` da raiz do `-fix`. Snapshots ficam em `bin/_snapshots/`. |
| **Gastou token Gemini à toa** | Cache não bateu (título/nº de painéis mudou) OU `--force-llm`/`--force-tts` | Use o MESMO `--titulo` e pasta. Narração/censura/TTS vêm do cache. Ver `workspace/CACHES_LEIA.md`. |
| **Vídeo saiu 720p (queria 1080p)** | `TEST_MODE=1` (ou `--preset teste`) pula upscale | Use `--preset final` (1080p). |
| **Confuso com muitos handoffs** | Docs antigos de coisas já feitas | Leia só `LEIA_PRIMEIRO.md`. O resto está em `_HANDOFFS_FEITOS/` (histórico). |

## Ferramentas de diagnóstico
- `bin/doctor.py [--cap <slug>]` — raio-x (pasta, python, ffmpeg, caches, depth, assets, flags, últimos vídeos).
- `bin/smoketest.py [--cap <slug>]` — testa a cadeia de render (censura/efeitos/parallax) em ~1 min, sem LLM/TTS.
- `run_cap.bat <pasta> "<titulo>" <teste|final>` — render de 1 capítulo com tudo ligado certo.
