# Design Técnico — Motor de Graus + Paralelismo CPU/GPU

> Detalhamento de implementação da seção 2 do `PLANO_ANIME_DEITADO_V2.md`.
> Ancorado no código real de `bin/anime_segments.py` e `bin/fx_clips.py`.
> NADA implementado ainda. Escrito 2026-07-27.

---

## 1. Diagnóstico do gargalo atual (serial)

`anime_segments.build_segments()` (linhas 49-85) é um loop 100% serial por frase:

```
para cada frase i:
    audio = narrate(frase)          # TTS: rede/CPU leve, ~0.5-1s
    clip_dur = audio_duration()     # ffprobe: instantâneo
    build_clip_from_video(...)      # ffmpeg encode: CPU PESADO, ~2-4s
    global_time += clip_dur
```

Problema: enquanto o ffmpeg encoda o clipe (CPU 100%), a rede/iGPU ficam ociosas. E o TTS do próximo clipe só começa depois. Num vídeo de 1880 frases isso é ~2-4h de CPU serial com iGPU parada o tempo todo.

**Nota de corte:** `cut_at = global_time % src_dur` (linha 60) — o corte do source depende do `global_time` acumulado, que depende da duração do áudio anterior. Isso cria dependência sequencial no CÁLCULO, mas não no ENCODE. Solução: pré-calcular todos os `clip_dur` (fase TTS em lote), depois todos os `cut_at` viram determinísticos → encode pode paralelizar.

---

## 2. Arquitetura V2 em 3 fases

### Fase A — Planejamento (rápido, CPU leve)
1. **TTS em lote** de todas as frases (edge-tts aguenta paralelo N=4-8). Gera todos os `audio_i.wav`.
2. Medir todas as durações → calcular todos os `cut_at` de uma vez (determinístico).
3. **Decisão de efeitos** (Motion Director em camadas):
   - Passo 0 (regra, sem IA): frase curta→efeito fixo; palavra-gatilho dramática (regex "morre|revela|ataca|grita|desperta|destrói")→marca beat pra cutout/freeze.
   - Passo 1 (só o que sobra): LLM classifica mood/efeito.
   - Resultado: `plano[i] = {cut_at, dur, efeito, is_beat, sfx}`. Cacheado por md5.

### Fase B — Render paralelo (satura CPU **e** iGPU)
Dois pools concorrentes alimentados pelo `plano`:
- **pool-encode** (N = nº de cores, satura CPU): `build_clip_from_video` de cada clipe.
- **pool-fx** (satura iGPU + CPU restante): rembg dos frames de beat, depth de stills, upscale.

Enquanto pool-encode processa o clipe N, pool-fx já preparou o recorte do beat N+k. Fila produtor-consumidor. **Meta: nenhuma das duas ociosa.**

### Fase C — Montagem (serial, mas rápido)
`concat_with_xfade` + música + legendas (já existe). Aplicar overlays de efeito EM LOTES (6-100) pra não estourar RAM.

---

## 3. Graus — o que cada nível liga

```python
GRAUS = {
    1: dict(fx_beats=0,   parallax=False, upscale=False, sfx_dens=0.3, ctas=0, tts_workers=8),
    2: dict(fx_beats=0,   parallax=False, upscale=False, sfx_dens=0.6, ctas=1, transicoes="boas"),
    3: dict(fx_beats=12,  parallax=False, upscale=False, sfx_dens=1.0, ctas=1, transicoes="boas", cutout=True),
    4: dict(fx_beats=25,  parallax="stills", upscale="lanczos", sfx_dens=1.0, ctas=2, cutout=True, zoompan=True),
    5: dict(fx_beats=50,  parallax="stills", upscale="ia?",     sfx_dens=1.0, ctas=3, cutout=True, zoompan=True, tier3=True),
}
```

`fx_beats` = quantos beats dramáticos recebem cutout/freeze (limitado pelo custo rembg ~3.8s cada).
Env `ANIME_GRAU=N` lido no início; default 3.

## 4. Botões desktop
- `Grau1.bat` .. `Grau5.bat` na área de trabalho: setam `ANIME_GRAU` e disparam `_pc2_dispatch_deitado.py`.
- Um `.bat` de calibração que roda o MESMO source em 2 graus e reporta tempo×tamanho pra comparação.

## 5. Paralelismo — cuidados na 620
- `tts_workers` limitado (edge-tts é rede; 8 paralelo ok).
- pool-encode = nº de cores (4 no PC2). pool-fx = 1-2 (rembg é RAM-pesado).
- **RAM 11.7GB é o teto real.** Monitorar; se pico, reduzir workers. Nunca rodar rembg de vários frames grandes ao mesmo tempo.
- Fallback universal mantido: qualquer efeito que falhe → clipe base sem efeito, nunca trava.

## 6. Compatibilidade / não-regressão
- Grau 1 == comportamento atual (validação de que não quebramos nada).
- Mudanças isoladas em `build_segments` (fase A/B) e um novo `fx_planner.py`. `concat_with_xfade` intocado.
- Testar cada grau num source curto (5min) antes de soltar em 1h+.

## 7. Pendências de pesquisa (antes de prometer)
- **Upscale IA na 620:** CONFIRMADO INVIÁVEL (2026-07-27). Verificado no venv do PC2: `realesrgan`, `torch`, `onnxruntime` todos MISSING. Real-ESRGAN precisa torch+CUDA → fora. Usar `scale=...:flags=lanczos` (ffmpeg CPU, barato) pra 720p→1080p. NÃO prometer 4K por IA.
- **Nº ótimo de workers** por medição real, não chute.

## 8. PRÉ-REQUISITOS de instalação no venv do PC2 (verificado 2026-07-27)
Estado atual do venv `C:\recapd-e-animes\venv`: **rembg, torch, onnxruntime, cv2, realesrgan TODOS MISSING.**

Implicações por tier:
- **Tier 1 zoompan + transições + loudnorm:** ffmpeg puro → JÁ RODAM, sem instalar nada. **Melhor ponto de partida.**
- **Tier 1 CUTOUT_FX (recorte de personagem):** precisa `pip install rembg` (puxa onnxruntime CPU). Instalar ANTES de ativar cutout. rembg em CPU ~3.8s/frame — ok pra ~12 beats/vídeo.
- **cv2 (crop inteligente/detecção):** `pip install opencv-python-headless` se for usar crop no personagem pro reframe de short.
- **NUNCA instalar torch/realesrgan** — inúteis sem CUDA, só ocupam disco.

**Cuidado:** instalar libs COMPETE por CPU/rede. Fazer quando NÃO houver render ativo.
