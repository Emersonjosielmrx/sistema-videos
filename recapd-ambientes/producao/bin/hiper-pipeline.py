#!/usr/bin/env python3
"""hiper-pipeline.py — ORQUESTRAÇÃO do pipeline de vídeo hipercool (-fix).

Split 2026-07-04: a lógica pesada foi pra módulos menores —
  narration.py   → narração IA (Claude/Gemini + visão): gerar_recap, descrição, falas, revisão.
  tts_stage.py   → voz + cache: tts_panel, _infer_gender_by_name (edge/gemini por TTS_ENGINE).
  effects_engine → montagem visual (fachada fx_*). hp_common.py → paths + log.
Sobrou aqui: run_pipeline (fluxo), run_batch, main, _burn_webm_overlays.
Backup do monólito: bin/_PRE_PIPESPLIT_hiper-pipeline.py.bak.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _tts_filter import clean_for_tts
if os.environ.get("TTS_ENGINE", "edge") == "gemini":
    import gemini_tts as gemini_tts
else:
    import edge_tts_engine as gemini_tts
import gemini_llm
import _tg_safe
import concurrent.futures
import effects_engine
import tts_cache

try:
    import parallax_engine
except Exception:
    parallax_engine = None

try:
    from PIL import Image
except ImportError:
    print("ERRO: Pillow nao instalado. Rode: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)

# base compartilhada + módulos extraídos
from hp_common import (PROJECT_DIR, CACHE_DIR, VIDEOS_DIR, TMP_DIR,
                       WATERMARK_HANDLE, MAX_PANELS_DEFAULT, TEST_MODE, _ERR_MARKERS, log)
from narration import (gerar_recap, gerar_recap_fusao, _revisar_coerencia,
                       _forcar_falas_personagens, _descrever_paineis_claude)
from tts_stage import tts_panel, _infer_gender_by_name, TTS_CACHE_DIR


# Adiciona bin/ ao path pra importar helpers locais
sys.path.insert(0, str(Path(__file__).resolve().parent))


# Parallax 2.5D (movimento real via depth map). Import tolerante: se faltar
# transformers/torch, PARALLAX simplesmente não ativa (fallback Ken Burns).
try:
    import parallax_engine
except Exception:
    parallax_engine = None


try:
    from PIL import Image
except ImportError:
    print("ERRO: Pillow não instalado. Rode: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)


VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


TMP_DIR.mkdir(parents=True, exist_ok=True)


TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _burn_webm_overlays(video_in, overlays, video_out):
    """Sobrepõe vídeos WebM (legendas HyperFrames) no vídeo principal com timing.

    overlays: lista de {"webm": path, "start": float, "end": float}
    Usa chromakey (fundo preto → transparente) + overlay com enable='between(t,start,end)'.
    """
    if not overlays:
        return False

    # Limitar a 20 overlays simultâneos (ffmpeg tem limite de inputs)
    overlays = overlays[:20]

    inputs = ["-i", str(video_in)]
    for ov in overlays:
        inputs += ["-i", ov["webm"]]

    # Cadeia de overlays: cada WebM é sobreposto na janela de tempo
    # Usar chromakey para remover fundo preto dos WebMs
    parts = []
    cur = "[0:v]"
    for idx, ov in enumerate(overlays, start=1):
        out = f"[vhf{idx}]"
        # Chromakey remove preto, overlay no centro-inferior
        parts.append(
            f"[{idx}:v]chromakey=0x000000:0.15:0.1,scale=1080:1920:force_original_aspect_ratio=decrease[hfov{idx}];"
            f"{cur}[hfov{idx}]overlay=0:0:"
            f"enable='between(t,{ov['start']:.2f},{ov['end']:.2f})'{out}"
        )
        cur = out

    filter_complex = ";".join(parts)
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", cur, "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-g", "30",
        "-c:a", "copy",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=1800)
        return Path(video_out).exists() and Path(video_out).stat().st_size > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log(f"  ✗ burn_webm_overlays falhou: {str(e)[:200]}")
        return False


# ─── Pipeline principal ──────────────────────────────────────────────────────
def run_pipeline(panels_dir, titulo, max_panels=MAX_PANELS_DEFAULT,
                 skip_notify=False, dry_run=False, skip_credits=0, animated=False,
                 start_panel=0, fusao=False, narrator_gender="F", subtitles=False,
                 branding=True, karaoke=False, censura=False, # Argumentos existentes
                 force_llm=False, force_tts=False, no_copyright_ost=False,
                 hyperframes_karaoke=False, output_suffix="", # Novo output_suffix
                 audio_only=False): # FÁBRICA DE ÁUDIO: só TTS (enche cache) e para antes do ffmpeg
    """Executa a pipeline completa a partir de painéis já cortados.

    skip_credits: pula os N primeiros painéis (geralmente créditos/capa/avisos).
    start_panel: offset no início (pra gerar PARTES seguintes do mesmo capítulo).
                 Aplicado DEPOIS dos filtros (créditos/pequenos/brancos), então
                 part 1 = start_panel=0, part 2 = start_panel=55, etc.
    """
    panels_dir = Path(panels_dir)
    exts = {".jpg", ".jpeg", ".png"}
    panel_files = sorted(
        f for f in panels_dir.iterdir()
        if f.suffix.lower() in exts and not f.name.startswith("_")
    )

    if not panel_files:
        log("✗ Nenhum painel encontrado!")
        return None

    # Pular painéis de créditos/capa (geralmente os primeiros são avisos 18+, logos, etc).
    # Default: pula SEMPRE o 1º painel (era a função antiga). Ajustável via env
    # SKIP_PANELS (0 = não pular, 2 = pular dois...). O arg skip_credits explícito,
    # se passado >0, tem prioridade sobre o env.
    if not skip_credits:
        try:
            skip_credits = int(os.environ.get("SKIP_PANELS", "1"))
        except ValueError:
            skip_credits = 1
    if skip_credits and len(panel_files) > skip_credits:
        log(f"  Pulando {skip_credits} painel(is) inicial(is) (créditos/capa)")
        panel_files = panel_files[skip_credits:]

    # Remover último(s) painel(is) de propaganda/créditos de tradutores
    skip_last = int(os.environ.get("SKIP_LAST_PANELS", "1"))
    if skip_last and len(panel_files) > skip_last:
        log(f"  Pulando {skip_last} painel(is) final(is) (propaganda/créditos)")
        panel_files = panel_files[:-skip_last]

    # Filtrar painéis muito pequenos (provavelmente headers/ads/créditos)
    min_panel_height = 300
    panel_files = [f for f in panel_files if Image.open(f).height >= min_panel_height]

    # Filtrar painéis em branco (cortes errados do splitter)
    def _is_blank(path):
        img = Image.open(path).convert("L")
        from PIL import ImageStat
        stat = ImageStat.Stat(img)
        return stat.mean[0] > 248  # quase branco puro
    before = len(panel_files)
    panel_files = [f for f in panel_files if not _is_blank(f)]
    if len(panel_files) < before:
        log(f"  Removidos {before - len(panel_files)} painéis em branco")

    # Offset de início (pra gerar partes seguintes do mesmo capítulo)
    if start_panel > 0:
        total_disp = len(panel_files)
        panel_files = panel_files[start_panel:]
        log(f"  Começando do painel {start_panel} (parte seguinte) — {len(panel_files)} de {total_disp} restantes")

    # Limitar painéis
    if len(panel_files) > max_panels:
        log(f"  {len(panel_files)} painéis → limitando a {max_panels}")
        panel_files = panel_files[:max_panels]

    n = len(panel_files)
    log(f"Pipeline: {titulo} ({n} painéis)")

    if dry_run:
        log("  [DRY-RUN] Mostrando o que seria feito:")
        log(f"  1. Gerar narração ({n} locuções) com visão dos painéis")
        log(f"  2. TTS pra {n} painéis (Gemini 3.1 Flash)")
        log(f"  3. {n} clips Ken Burns → concat → MP4")
        log(f"  4. Notificar Telegram: {'sim' if not skip_notify else 'não'}")
        return None

    # 1. Narração IA (com cache — reusar locuções já geradas)
    narration_cache_dir = PROJECT_DIR / "workspace" / "narration_cache"
    narration_cache_dir.mkdir(parents=True, exist_ok=True)
    slug = panels_dir.name if hasattr(panels_dir, 'name') else Path(panels_dir).name
    # Inclui o offset (e o modo fusão) na chave pra não colidir entre variações
    part_tag = f"_s{start_panel}" if start_panel > 0 else ""
    if fusao:
        part_tag += "_fusao"
    narration_cache_file = narration_cache_dir / f"{slug}{part_tag}_{n}panels.json"

    if narration_cache_file.exists() and not force_llm:
        import json as _json
        recap = _json.loads(narration_cache_file.read_text())
        log(f"  ✓ Narração [CACHE]: {recap.get('titulo_video', titulo)}")
    else:
        recap = None
        if force_llm: log("  ⚠ --force-llm ativo, ignorando cache de narração.")
        # ENSEMBLE (default): N modelos×prompts → auditor (via gateway) lê os balões dos
        # painéis e alinha as falas painel-a-painel, corrigindo o desalinhamento que o
        # Gemini-sozinho causava. Resiliente: cai pro fluxo fusão/2-passos se falhar.
        if os.environ.get("ENSEMBLE_NARRATION", "1") != "0":
            try:
                import narration_ensemble
                log("  [ENSEMBLE] gerando narração (multi-modelo + auditor via gateway)...")

                def _jpeg_loader(p, _max=400, _q=55):
                    """path → bytes JPEG crus (o auditor/visão espera bytes, não base64)."""
                    from io import BytesIO
                    im = Image.open(p).convert("RGB")
                    r = min(_max / max(im.size), 1.0)
                    if r < 1.0:
                        im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
                    b = BytesIO(); im.save(b, format="JPEG", quality=_q)
                    return b.getvalue()

                ens = narration_ensemble.gerar_narracao_ensemble(
                    titulo, panel_files, _jpeg_loader, narrator_gender=narrator_gender)
                if ens:
                    recap = {"titulo_video": titulo, "tags": [], "locucoes": ens,
                             "descriptions": [l.get("cena", "") for l in ens]}
                    log(f"  ✓ [ENSEMBLE] {len(ens)} locuções alinhadas")
                else:
                    log("  [ENSEMBLE] sem resultado → fallback fusão/2-passos")
            except Exception as e:
                log(f"  [ENSEMBLE] erro ({type(e).__name__}: {str(e)[:80]}) → fallback")
        if not recap and fusao:
            # Híbrido: tenta fusão (1 chamada). Se bloquear (conteúdo +18), cai pro 2-passos.
            recap = gerar_recap_fusao(titulo, panel_files, narrator_gender=narrator_gender)
            if not recap:
                log("  Fusão indisponível → fluxo 2-passos (visão neutra + narração)")
        if not recap:
            recap = gerar_recap(titulo, panel_files, narrator_gender=narrator_gender)
        if not recap:
            log("✗ Falha na geração de narração")
            return None
        # Salvar no cache
        import json as _json
        narration_cache_file.write_text(_json.dumps(recap, ensure_ascii=False, indent=2))
        log(f"  ✓ Narração: {recap.get('titulo_video', titulo)} [salvo no cache]")

    locucoes = recap["locucoes"]
    descriptions = recap.get("descriptions", [])

    # 1b. Revisão de coerência narrativa — ajusta conexões entre locuções do narrador.
    # Roda UMA VEZ e salva o resultado no narration_cache (flag _revised). Senão o texto
    # do narrador mudava a cada run → furava o cache de áudio (regerava ~38 falas à toa).
    if not recap.get("_revised"):
        locucoes = _revisar_coerencia(locucoes, titulo)
        recap["locucoes"] = locucoes
        recap["_revised"] = True
        try:
            narration_cache_file.write_text(_json.dumps(recap, ensure_ascii=False, indent=2))
            log("  ✓ Narração revisada salva no cache (estável p/ próximos runs)")
        except Exception as e:
            log(f"  ⚠ não consegui salvar revisão no cache: {e}")

    # 2. TTS + clips (com efeitos visuais do effects_engine)
    clips = []
    clip_texts = []  # texto da narração por clip (pra legendas) — alinhado com clips
    clip_personas = []  # persona por clip (pra name tag) — alinhado com clips
    clip_sensual = []  # bool por clip (pra censura) — alinhado com clips
    _n_parallax = 0; _n_panelfx = 0; _n_mascote = 0  # contadores p/ o resumo de efeitos no fim
    try:  # zera o histograma de efeitos por capítulo (variedade real por vídeo)
        import panel_effects as _pfx0; _pfx0.reset_fx_hist()
    except Exception:
        pass
    # Censura VISUAL na imagem do painel (exodia fosco / blur total do censura_visual.py).
    # Só quando --censura. cens_jobs = painéis +18 detectados → rebuild do clip a partir da
    # imagem censurada, num passo pós-loop. NÃO afeta o vídeo principal (limpo).
    cens_jobs = []
    _cv = None
    if censura:
        try:
            import censura_visual as _cv
        except ImportError:
            _cv = None
        try:
            from censura_manual_override import get_override
        except ImportError:
            get_override = lambda o, c, f: None
            # AVISO CRÍTICO: sem chave Sightengine a detecção +18 cai no NudeNet (fraco em
            # manhwa) → risco de painel explícito VAZAR sem censura. Não postar sem revisar.
            if _cv._pick_key() is None:
                log("  🚨 SIGHTENGINE ESGOTADA (0 chaves) — censura vai usar só NudeNet local (FRACO em manhwa).")
                log("  🚨 RISCO DE VAZAMENTO +18. NÃO POSTE sem revisar; re-renderize quando a chave voltar (reseta/dia) ou adicione chave em secrets/sightengine.json.")
        except Exception as _e:
            log(f"  ⚠ censura_visual indisponível ({_e}); versão censurada será pulada")
            _cv = None
    session_tmp = TMP_DIR / f"session_{int(time.time())}"
    session_tmp.mkdir(parents=True, exist_ok=True)
    efx = effects_engine.EffectsManager()

    def _detectar_cens(panel):
        """Score +18 do painel via censura_visual (Sightengine, cache md5). None se indisponível.
        Mesma detecção 'oficial' usada nos testes que geraram as referências (processar_painel)."""
        if not _cv:
            return None
        try:
            det = _cv.detectar_score(str(panel))
        except Exception:
            return None
        return det[0] if det is not None else None

    def _render_cens_clip(job, panel, out):
        """Reconstrói o clip do painel +18 a partir da IMAGEM já censurada, com os MESMOS
        efeitos/params do clip limpo → duração idêntica (timeline e legendas não deslocam)."""
        p = job["params"]
        if job["kind"] == "flash":
            return effects_engine.build_flash_clip(
                str(panel), str(out), p["i"], efx, duration=p.get("duration", 0.8),
                transition_type=p["transition_type"], sfx_file=p["sfx_file"])
        if p["is_impact"]:
            return effects_engine.build_clip_with_shake(
                str(panel), str(job["wav"]), str(out), p["i"], efx,
                transition_type=p["transition_type"], sfx_file=p["sfx_file"],
                overlay_video=p["overlay_video"], mood=p["clip_mood"])
        if p["is_tension"]:
            return effects_engine.build_clip_with_shake(
                str(panel), str(job["wav"]), str(out), p["i"], efx,
                shake_intensity=5, shake_freq=8,
                transition_type=p["transition_type"], sfx_file=p["sfx_file"],
                overlay_video=p["overlay_video"], mood=p["clip_mood"])
        if p["animated"]:
            return effects_engine.build_clip_animated(
                str(panel), str(job["wav"]), str(out), p["i"], efx,
                transition_type=p["transition_type"], sfx_file=p["sfx_file"])
        return effects_engine.build_clip(
            str(panel), str(job["wav"]), str(out), p["i"], efx,
            transition_type=p["transition_type"], sfx_file=p["sfx_file"],
            overlay_video=p["overlay_video"], mood=p["clip_mood"])

    # Consolidação de falas DESATIVADA — causava painéis vazios
    # for i in range(len(locucoes) - 1):
    #     cur = locucoes[i]
    #     nxt = locucoes[i + 1]
    #     cur_text = (cur.get("text") or "").strip()
    #     cur_persona = (cur.get("persona") or "").lower()
    #     nxt_persona = (nxt.get("persona") or "").lower()
    #     if (cur_persona == nxt_persona
    #         and cur_persona not in ("narrador", "narradora")
    #         and 0 < len(cur_text.split()) < 5):
    #         nxt["text"] = cur_text + " " + (nxt.get("text") or "").strip()
    #         cur["text"] = ""

    # PRÉ-VARREDURA de scores +18 (cache md5, barato) → dá os VIZINHOS p/ a 3a camada
    # (mancha branca apagada pelo autor: detector de pele não pega, mas se o vizinho é +18
    # forte é continuação da cena → censura preventiva). Só na versão censurada.
    _all_scores = []
    if censura and _cv:
        for _pp in panel_files:
            _s = _detectar_cens(_pp)
            _all_scores.append(_s if _s is not None else 0.0)

    def _vizinho_forte(idx):
        vs = [_all_scores[j] for j in range(idx - 2, idx + 3)
              if j != idx and 0 <= j < len(_all_scores)]
        return max(vs) if vs else 0.0

    # ── PRÉ-AQUECIMENTO TTS PARALELO (edge-tts é IO puro, seguro paralelizar) ──
    TTS_WORKERS = int(os.environ.get("TTS_WORKERS", "8"))
    if TTS_WORKERS > 1 and not audio_only:
        def _prefetch_tts(args_tuple):
            idx, loc_item = args_tuple
            text = (loc_item.get("text") or "").strip()
            if not text:
                return
            wav = session_tmp / f"audio_{idx:03d}.wav"
            if wav.exists():
                return
            pl = (loc_item.get("persona") or "narrador").lower()
            g = None if pl in ("narrador", "narradora", "narrator") \
                else (loc_item.get("gender") or _infer_gender_by_name(loc_item.get("persona", "")))
            try:
                tts_panel(text, wav, persona=loc_item.get("persona", "Narrador"),
                          gender=g, sensual=False, force_tts=force_tts)
            except Exception:
                pass

        _tts_jobs = [(i, loc) for i, loc in enumerate(locucoes)
                     if (loc.get("text") or "").strip()]
        if _tts_jobs:
            log(f"  ⚡ Pré-aquecimento TTS: {len(_tts_jobs)} áudios em {TTS_WORKERS} workers...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=TTS_WORKERS) as pool:
                list(pool.map(_prefetch_tts, _tts_jobs))
            _cached = sum(1 for i, _ in _tts_jobs if (session_tmp / f"audio_{i:03d}.wav").exists())
            log(f"  ✓ Pré-aquecimento: {_cached}/{len(_tts_jobs)} WAVs prontos")

    for i, (panel_path, loc) in enumerate(zip(panel_files, locucoes)):
        # Checagem de comandos do painel (skip/pause/stop)
        _cmd_dir = Path(__file__).resolve().parent.parent
        if (_cmd_dir / "COMMAND_STOP.txt").exists():
            log("⏹ STOP recebido — abortando pipeline")
            (_cmd_dir / "COMMAND_STOP.txt").unlink(missing_ok=True)
            return None
        if (_cmd_dir / "COMMAND_SKIP.txt").exists():
            log("⏭ SKIP recebido — pulando capítulo")
            (_cmd_dir / "COMMAND_SKIP.txt").unlink(missing_ok=True)
            return None
        if (_cmd_dir / "COMMAND_PAUSE.txt").exists():
            log("⏸ PAUSE recebido — aguardando retomada...")
            while (_cmd_dir / "COMMAND_PAUSE.txt").exists():
                time.sleep(2)
            log("▶ PAUSE removido — retomando")

        wav_path = session_tmp / f"audio_{i:03d}.wav"
        clip_path = session_tmp / f"clip_{i:03d}.mp4"

        # FÁBRICA DE ÁUDIO (--audio-only): só gera o TTS (enche o cache) e pula
        # TODO o resto (censura/efeitos/clip). A fase de vídeo roda depois, em
        # paralelo, reusando este cache (ffmpeg puro, sem tocar no Gemini).
        if audio_only:
            _txt = loc.get("text", "").strip()
            if _txt:
                _pl = (loc.get("persona") or "narrador").lower()
                _g = None if _pl in ("narrador", "narradora", "narrator") \
                    else (loc.get("gender") or _infer_gender_by_name(loc.get("persona", "")))
                tts_panel(_txt, wav_path, persona=loc.get("persona", "Narrador"),
                          gender=_g, sensual=False, force_tts=force_tts)
            continue

        # Detecção +18 na IMAGEM do painel (só p/ versão censurada; cache md5).
        _cens_score = _detectar_cens(panel_path) if (censura and _cv) else None
        _is_nsfw = _cens_score is not None and _cens_score >= _cv.LIMIAR_DUVIDA
        _cens_tipo = None  # 'branco' → censura ESPECIAL (mancha genital apagada em branco)
        # 3a CAMADA: mancha branca grande (autor apagou) + vizinho +18 forte → censura ESPECIAL branco.
        if censura and _cv and not _is_nsfw:
            try:
                if (_cv.mancha_branca_frac(panel_path) >= 0.05
                        and _vizinho_forte(i) >= _cv.LIMIAR_NSFW):
                    _cens_score = _cv.LIMIAR_DUVIDA
                    _is_nsfw = True
                    _cens_tipo = "branco"
                    log(f"  🔍 3a camada: painel {i} mancha branca + vizinho +18 → censura ESPECIAL branco")
            except Exception:
                pass

        # Determinar transição e SFX
        transition_type, sfx_file = effects_engine.get_transition_and_sfx(i, descriptions)

        # SFX contextual: se o texto menciona keyword específica, usar SFX adequado.
        # Passa a descrição do painel → o gateway veta SFX que não cabe na cena.
        _desc_sfx = descriptions[i] if i < len(descriptions) else ""
        contextual_sfx, contextual_vol = effects_engine.pick_sfx_for_text(loc.get("text", ""), desc=_desc_sfx)
        if contextual_sfx:
            sfx_file = contextual_sfx

        # Detectar momento sensual/+18
        desc_for_sensual = descriptions[i] if i < len(descriptions) else ""
        # REGRA FIRME: NINGUÉM sussurra. Voz sensual ELIMINADA completamente.
        # Nem narrador, nem personagem masculino, nem feminino.
        is_sensual = False

        text_to_narrate = loc.get("text", "").strip()

        if not text_to_narrate:
            # Painel SEM NARRAÇÃO INTENCIONAL: clip rápido SEM SFX de transição
            log(f"  ⚡ Painel {i} sem narração, gerando clip rápido (sem SFX)")
            ok_flash = effects_engine.build_flash_clip(panel_path, clip_path, i, efx, duration=0.8,
                                                       transition_type=transition_type, sfx_file=None) # << SFX=None
            if ok_flash:
                clips.append(clip_path)
                clip_texts.append("")
                clip_personas.append("")
                clip_sensual.append(is_sensual)
                if _is_nsfw:
                    cens_jobs.append({"clip": clip_path, "panel": panel_path, "wav": wav_path,
                                      "score": _cens_score, "kind": "flash", "tipo": _cens_tipo,
                                      "params": {"i": i, "duration": 0.8,
                                                 "transition_type": transition_type, "sfx_file": None}})
            continue # Próximo painel

        # Painel COM NARRAÇÃO: tentar TTS
        # REGRA FIRME: Narrador SEMPRE usa a mesma voz (gender=None → Kore).
        # Ignorar gender do LLM para manter consistência.
        persona_lower = (loc.get("persona") or "narrador").lower()
        tts_gender = None if persona_lower in ("narrador", "narradora", "narrator") else loc.get("gender")
        # Persona sem gênero do LLM → infere pelo nome (evita voz errada). Só p/ personagem.
        if tts_gender is None and persona_lower not in ("narrador", "narradora", "narrator"):
            tts_gender = _infer_gender_by_name(loc.get("persona", ""))
        ok = tts_panel(text_to_narrate, wav_path,
                       persona=loc.get("persona", "Narrador"),
                       gender=tts_gender,
                       sensual=is_sensual,
                       force_tts=force_tts)

        if not ok:
            # Painel com narração ESPERADA, mas TTS FALHOU: clip rápido COM SFX (indica erro)
            log(f"  ⚠ TTS falhou pra painel {i} (mas tinha narração), gerando clip rápido (com SFX)")
            ok_flash = effects_engine.build_flash_clip(panel_path, clip_path, i, efx, duration=0.8,
                                                       transition_type=transition_type, sfx_file=sfx_file) # << SFX normal
            if ok_flash:
                clips.append(clip_path)
                clip_texts.append("")
                clip_personas.append("")
                clip_sensual.append(is_sensual)
                if _is_nsfw:
                    cens_jobs.append({"clip": clip_path, "panel": panel_path, "wav": wav_path,
                                      "score": _cens_score, "kind": "flash", "tipo": _cens_tipo,
                                      "params": {"i": i, "duration": 0.8,
                                                 "transition_type": transition_type, "sfx_file": sfx_file}})
            continue # Próximo painel

        # Se chegou aqui, TTS foi OK e tinha narração.

        # Enhancement de áudio DESATIVADO — degradava qualidade do edge-tts
        # effects_engine.enhance_narration_audio(wav_path)

        # Delay entre requests TTS (só se não veio do cache)
        # edge-tts é grátis e ilimitado — sem delay necessário
        vgender = "F" if gemini_tts._is_female(gemini_tts.voice_for_persona(loc.get('persona', 'Narrador'), gender=loc.get('gender'), kind='hipercool')) else "M"
        if not tts_cache.lookup_premium_first(TTS_CACHE_DIR, clean_for_tts(loc['text']), gemini_tts.voice_for_persona(loc.get('persona', 'Narrador'), gender=loc.get('gender'), kind='hipercool'), vgender):
            time.sleep(0.3)
        else:
            time.sleep(0.1)

        # Clip com efeitos (movimentos variados + cor + vinheta)
        # Detectar impacto/tensão pra aplicar camera shake
        desc = descriptions[i] if i < len(descriptions) else ""
        is_impact = effects_engine.is_impact_panel(desc)
        is_tension = effects_engine.is_tension_panel(desc)
        clip_mood = effects_engine.detect_mood_from_text(text_to_narrate)

        # Overlay atmosférico (chuva/neve/faíscas/pétalas) — reimplementado com colorkey
        overlay_video = effects_engine.overlay_for_mood(clip_mood)

        tag = "  [SHAKE]" if is_impact else ("  [TENSION]" if is_tension else "")
        ov_tag = "  [speedlines]" if (is_impact and overlay_video) else (
            f"  [{effects_engine.MOOD_OVERLAY.get(clip_mood, '')}]" if overlay_video else "")
        sfx_name = Path(sfx_file).name if sfx_file else "nenhum"
        trans_name = transition_type or "corte_seco"
        persona_name = loc.get("persona", "?")
        voice_used = gemini_tts.voice_for_persona(persona_name, gender=loc.get("gender"), kind="hipercool")
        log(f"  Clip {i+1}/{n}{tag}{ov_tag} | painel={Path(panel_path).name} voz={voice_used} trans={trans_name} sfx={sfx_name} persona={persona_name}")

        ok = False
        # PARALLAX 2.5D (movimento real via depth) — PRIORIDADE (é o "corta o personagem e ele se
        # mexe"). Usa os depth maps cacheados; se não houver e PARALLAX_ONDEMAND=1, gera na hora.
        # Pula texto/plano. Se NÃO aplicar (inelegível/sem cache), cai no PANEL_FX abaixo.
        if not ok and parallax_engine is not None and os.environ.get("PARALLAX", "0") == "1":
            force = os.environ.get("PARALLAX_FORCE", "0") == "1"
            ondemand = os.environ.get("PARALLAX_ONDEMAND", "0") == "1"
            engine_final = os.environ.get("TTS_ENGINE", "edge") in ("gemini", "eleven")
            try:
                _md5 = parallax_engine._md5_file(panel_path)
                _cached = (parallax_engine._MF_CACHE / f"{_md5}.png").exists()
            except Exception:
                _cached = False
            quer_parallax = force or _cached or ondemand or (engine_final and censura)
            if quer_parallax and not _is_nsfw:
                try:
                    import panel_classifier as _pcl
                    if not _pcl.vale_parallax(panel_path):
                        quer_parallax = False
                except Exception:
                    pass
            else:
                quer_parallax = False
            if quer_parallax:
                terror_mode = os.environ.get("PARALLAX_TERROR", "0") == "1"
                ok = parallax_engine.build_parallax_clip(
                    panel_path, wav_path, clip_path,
                    W=effects_engine.W, H=effects_engine.H, fps=effects_engine.FPS,
                    terror=terror_mode)
                if ok:
                    _n_parallax += 1
                    log(f"  🌊 parallax 2.5D: painel {i}")
                else:
                    log("  ⚠ parallax falhou → fallback PANEL_FX/Ken Burns")

        # PANEL_FX (T15): efeito que MEXE NO PAINEL guiado pela narração (facezoom, freezeimpact...) —
        # FALLBACK do parallax. Decisão vem do worker (motion_director) se houver; senão keyword.
        # Salvaguardas: nunca em +18 (_is_nsfw) nem em texto/plano. Fallback total → Ken Burns.
        if not ok and os.environ.get("PANEL_FX", "0") == "1":
            try:
                import panel_effects as _pfx
                _tp = False
                try:
                    import panel_classifier as _pcl2
                    _tp = not _pcl2.vale_parallax(panel_path)
                except Exception:
                    _tp = False
                _fx = None
                # 1) decisão pré-fabricada pelo worker (motion_director), keyless no render
                try:
                    import motion_director as _md
                    # tem_balao = a IMAGEM tem balão de fala (não a narração!). Sem detector
                    # confiável de balão, passar False — senão TODO painel narrado caía em
                    # dollypush pelo pré-filtro, matando a variedade. Roteamento fica com o
                    # pick_effect (keyword+histograma) que distribui bem.
                    _dec = _md.decidir_efeito(panel_path, texto=text_to_narrate,
                                              is_sensual=_is_nsfw, tem_balao=False)
                    if _dec and _dec.get("efeito"):
                        _fx = _dec["efeito"]
                except Exception:
                    pass
                # 2) senão, roteia por keyword na hora
                if not _fx:
                    _fx = _pfx.pick_effect(text_to_narrate, is_sensual=_is_nsfw,
                                           is_texto_plano=_tp, img_path=panel_path)
                # próximo painel (só usado por efeitos de transição do Grupo C/F)
                _img2 = panel_files[i + 1] if (i + 1) < len(panel_files) else None
                if _fx and _pfx.build_effect_clip(panel_path, wav_path, clip_path, _fx, img2=_img2):
                    ok = True
                    _n_panelfx += 1
                    log(f"  🎬 painel-fx: {_fx}")
            except Exception:
                pass

        if ok:
            pass  # panel-fx ou parallax já montou o clip
        elif is_impact:
            ok = effects_engine.build_clip_with_shake(panel_path, wav_path, clip_path, i, efx,
                                                      transition_type=transition_type, sfx_file=sfx_file,
                                                      overlay_video=overlay_video, mood=clip_mood)
        elif is_tension:
            # Shake suave em tensão (intensidade menor)
            ok = effects_engine.build_clip_with_shake(
                panel_path, wav_path, clip_path, i, efx,
                shake_intensity=5, shake_freq=8,
                transition_type=transition_type, sfx_file=sfx_file,
                overlay_video=overlay_video, mood=clip_mood)
        elif animated:
            ok = effects_engine.build_clip_animated(panel_path, wav_path, clip_path, i, efx,
                                                    transition_type=transition_type, sfx_file=sfx_file)
        else:
            ok = effects_engine.build_clip(panel_path, wav_path, clip_path, i, efx,
                                           transition_type=transition_type, sfx_file=sfx_file,
                                           overlay_video=overlay_video, mood=clip_mood)
        if ok:
            clips.append(clip_path)
            clip_texts.append(loc.get("text", ""))
            clip_personas.append(loc.get("persona", ""))
            clip_sensual.append(is_sensual)
            if _is_nsfw:
                cens_jobs.append({"clip": clip_path, "panel": panel_path, "wav": wav_path,
                                  "score": _cens_score, "kind": "full", "tipo": _cens_tipo,
                                  "params": {"i": i, "is_impact": is_impact, "is_tension": is_tension,
                                             "animated": animated, "transition_type": transition_type,
                                             "sfx_file": sfx_file, "overlay_video": overlay_video,
                                             "clip_mood": clip_mood}})

            # Meme inteligente: insere meme com SFX entre clips.
            # ⚠️ MEMES=0 desliga os cards de meme FULL-SCREEN (fundo preto) que a usuária não
            # quer no meio do vídeo. Os CTA pequenos (like/subscribe) NÃO dependem disto — vêm
            # dos overlays alpha do elemental_transitions (ELEMENTAL_TRANS=1), por cima do painel.
            clip_text = loc.get("text", "")
            clip_mood = effects_engine.detect_mood_from_text(clip_text) if clip_text else "neutral_chill"
            if os.environ.get("MEMES", "1") == "1" and effects_engine.should_insert_meme(i, clip_mood):
                meme_path = session_tmp / f"meme_{i:03d}.mp4"
                if effects_engine.build_meme_clip(meme_path):
                    clips.append(meme_path)
                    clip_texts.append("")
                    clip_personas.append("")
                    clip_sensual.append(False)
                    log(f"  🎭 Meme inserido após clip {i+1}")
            # Vídeo de transição (respiro visual entre cenas). Desligável via
            # env TRANSITION_VIDEOS=0. É um clip curto re-encodado que entra no
            # concat simples — não mexe no xfade (que já corrompeu áudio no passado).
            elif os.environ.get("TRANSITION_VIDEOS", "1") != "0" \
                    and effects_engine.should_insert_transition(i):
                trans_path = session_tmp / f"trans_{i:03d}.mp4"
                if effects_engine.build_transition_clip(trans_path):
                    clips.append(trans_path)
                    clip_texts.append("")
                    clip_personas.append("")
                    clip_sensual.append(False)
                    log(f"  🎬 Transição inserida após clip {i+1}")
        else:
            log(f"  ⚠ Clip {i} falhou, pulando")

    # FÁBRICA DE ÁUDIO: terminou de encher o cache de TTS deste cap. Grava o
    # marcador em disco (NÃO no log) e PARA — a fábrica de vídeo detecta por
    # este arquivo e renderiza depois, em paralelo, reusando o cache.
    if audio_only:
        state_dir = PROJECT_DIR / "workspace" / "factory_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        marker = state_dir / f"{panels_dir.name}.audio_ready"
        marker.write_text(f"{datetime.now().isoformat()} n={len(panel_files)}\n", encoding="utf-8")
        log(f"  ✓ ÁUDIO PRONTO (TTS no cache). Marcador: {marker.name}")
        return "AUDIO_ONLY_DONE"

    if not clips:
        log("✗ Nenhum clip gerado!")
        return None

    # 2b. Intro hook + outro CTA (branding) — opcional
    if branding:
        intro_path = session_tmp / "_intro.mp4"
        title_card = recap.get("titulo_video", titulo)
        if effects_engine.build_intro_clip(title_card, panel_files[0], intro_path,
                                           sfx_file=effects_engine.SFX_DIR / "riser.wav"):
            clips.insert(0, intro_path)
            clip_texts.insert(0, "")
            clip_personas.insert(0, "")
            clip_sensual.insert(0, False)
            log("  ✓ Intro adicionado")
        outro_path = session_tmp / "_outro.mp4"
        if effects_engine.build_outro_clip(outro_path,
                                           sfx_file=effects_engine.SFX_DIR / "bass_hit.wav"):
            clips.append(outro_path)
            clip_texts.append("")
            clip_personas.append("")
            clip_sensual.append(False)
            log("  ✓ Outro (CTA) adicionado")

    # 2c. Censura VISUAL na imagem (exodia fosco = leve, blur total 251 = forte) — reconstrói
    # SÓ os clips +18 a partir do painel censurado. clips_cens = clips com os +18 trocados;
    # mesmos params → duração idêntica → timeline igual → a censurada reusa as MESMAS legendas.
    clips_cens = list(clips)
    _n_cens = 0
    if censura and cens_jobs and _cv:
        log(f"  Censura visual: processando {len(cens_jobs)} painéis +18 (exodia/blur na imagem)...")
        for job in cens_jobs:
            try:
                cpanel = session_tmp / (Path(job["panel"]).stem + "_cens.jpg")
                niv = _cv.censurar_imagem(str(job["panel"]), str(cpanel), job["score"], tipo=job.get("tipo"))
                if niv in (None, "intacto") or not Path(cpanel).exists():
                    continue
                cclip = Path(str(job["clip"])[:-4] + "_cens.mp4")
                if _render_cens_clip(job, cpanel, cclip) and Path(cclip).exists():
                    try:
                        clips_cens[clips_cens.index(job["clip"])] = cclip
                        _n_cens += 1
                        log(f"    ✓ {Path(job['panel']).name} → {niv} (score={job['score']:.2f})")
                    except ValueError:
                        pass
            except Exception as _e:
                log(f"    ⚠ falha ao censurar {Path(job['panel']).name}: {_e}")
        log(f"  ✓ Censura visual: {_n_cens}/{len(cens_jobs)} painéis censurados na imagem")

    # 3. Concat com transições (xfade entre clips)
    slug = re.sub(r"[^a-z0-9]+", "-", titulo.lower().strip())[:60]
    ts = datetime.now().strftime("%Y%m%d_%H%M")

    # Convenção: o vídeo mais recente SEMPRE tem o output_suffix e depois "_ULTIMO" no nome.
    # Rebaixa os "_ULTIMO" anteriores do mesmo slug (remove a marca + renomeia meta).
    for prev in VIDEOS_DIR.glob(f"hipercool_{slug}_*{output_suffix}_ULTIMO.mp4"):
        demoted = prev.with_name(prev.name.replace("_ULTIMO", ""))
        prev.rename(demoted)
        prev_meta = prev.with_suffix(".meta.json")
        if prev_meta.exists():
            prev_meta.rename(demoted.with_suffix(".meta.json"))

    out_name = f"hipercool_{slug}_{ts}{output_suffix}_ULTIMO.mp4"
    out_mp4 = VIDEOS_DIR / out_name
    out_cens = None  # preenchido no bloco 3d se houver censura; usado no pós-passo de organização

    log(f"  Concatenando {len(clips)} clips com transições + SFX...")
    _use_xfade = os.environ.get("XFADE_TRANSITIONS", "1") != "0"
    if _use_xfade and hasattr(effects_engine, "concat_with_xfade"):
        ok = effects_engine.concat_with_xfade(clips, out_mp4, descriptions=descriptions)
    else:
        ok = effects_engine.concat_with_transitions(clips, out_mp4, descriptions=descriptions)
    if not ok:
        log("✗ Concat falhou!")
        return None

    # 3a-bis. TRANSIÇÕES ELEMENTAIS (fogo/água/gelo/... nos cortes). Flag ELEMENTAL_TRANS=1.
    # Usa clip_texts como descrição da cena (a narração). Áudio=copy (não mexe no sync).
    # Pula painéis +18. Fallback total: erro → vídeo mantido.
    if os.environ.get("ELEMENTAL_TRANS", "0") == "1":
        try:
            import elemental_transitions as _elem
            _abs = list(getattr(effects_engine, "_CLIP_ABS_STARTS", []) or [])
            if len(_abs) == len(clip_texts):
                _sens_idx = [i for i, s in enumerate(clip_sensual) if s]
                _picks = _elem.pick_transitions(clip_texts, _abs, sensual=_sens_idx)
                if _picks:
                    _elem_out = out_mp4.with_name(out_mp4.stem + "_elem.mp4")
                    if _elem.apply(out_mp4, _elem_out, _picks):
                        out_mp4.unlink()
                        _elem_out.rename(out_mp4)
                        log(f"  ✓ {len(_picks)} transições elementais aplicadas")
                    else:
                        log("  ⚠ transições elementais falharam (vídeo mantido)")
                else:
                    log("  ℹ nenhuma cena elemental detectada")
            else:
                log(f"  ⚠ offsets indisponíveis p/ elementais ({len(_abs)} vs {len(clip_texts)})")
        except Exception as _e:
            log(f"  ⚠ transições elementais erro: {_e} (vídeo mantido)")

    # 3a-ter. MASCOTE garota-propaganda (TAREFA 14). Overlay alpha reagindo à narração do
    # NARRADOR (love/cry/shock/...), variando a POSE conforme a emoção. Flag MASCOTE_OVERLAY=1.
    # Parcimônia (máx MASCOTE_MAX). Áudio=copy. Fallback total.
    if os.environ.get("MASCOTE_OVERLAY", "0") == "1":
        try:
            import mascote_overlay as _masc
            _abs_m = list(getattr(effects_engine, "_CLIP_ABS_STARTS", []) or [])
            if len(_abs_m) == len(clip_texts):
                _sens_m = [i for i, s in enumerate(clip_sensual) if s]
                _ev = _masc.pick_eventos(clip_texts, clip_personas, _abs_m, sensual=_sens_m)
                if _ev:
                    _m_out = out_mp4.with_name(out_mp4.stem + "_masc.mp4")
                    if _masc.overlay_mascote(out_mp4, _m_out, _ev):
                        out_mp4.unlink()
                        _m_out.rename(out_mp4)
                        _n_mascote = len(_ev)
                        log(f"  ✓ mascote: {len(_ev)} aparições ({', '.join(e['pose'] for e in _ev)})")
                    else:
                        log("  ⚠ mascote falhou (vídeo mantido)")
                else:
                    log("  ℹ nenhuma cena p/ mascote")
            else:
                log(f"  ⚠ offsets indisponíveis p/ mascote ({len(_abs_m)} vs {len(clip_texts)})")
        except Exception as _e:
            log(f"  ⚠ mascote erro: {_e} (vídeo mantido)")

    # 3b. Adicionar trilha sonora dinâmica (muda conforme clima)
    trilhas_dir = PROJECT_DIR / "workspace" / "assets" / "trilhas"
    if trilhas_dir.exists() and (trilhas_dir / "moods.json").exists():
        log("  Adicionando trilha dinâmica...")
        out_with_music = out_mp4.with_name(out_mp4.stem + "_music.mp4")
        effects_engine.add_dynamic_music(
            out_mp4, recap.get("locucoes", []), out_with_music,
            trilhas_dir, music_volume=0.18, no_copyright=no_copyright_ost
        )
        if out_with_music.exists() and out_with_music.stat().st_size > 0:
            out_mp4.unlink()
            out_with_music.rename(out_mp4)
            log("  ✓ Trilha dinâmica adicionada")
    else:
        # Fallback: trilha única
        trilha_path = PROJECT_DIR / "workspace" / "assets" / "trilha.mp3"
        if trilha_path.exists():
            log("  Adicionando trilha sonora...")
            out_with_music = out_mp4.with_name(out_mp4.stem + "_music.mp4")
            effects_engine.add_background_music(out_mp4, trilha_path, out_with_music,
                                                music_volume=0.08)
            if out_with_music.exists() and out_with_music.stat().st_size > 0:
                out_mp4.unlink()
                out_with_music.rename(out_mp4)
                log("  ✓ Trilha adicionada")

    # 3c. Legendas queimadas estilo Shorts (Ponto F) — opcional via --subtitles
    subs = []  # hoisted: a versão censurada reusa exatamente estas legendas (timeline idêntica)
    if subtitles and clip_texts and TEST_MODE < 2:
        log("  Gerando legendas (estilo Shorts)...")
        # Duração real de cada clip → timing cumulativo das legendas
        entries = []
        total_clip_dur = 0.0
        for clip, txt in zip(clips, clip_texts):
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(clip)],
                    capture_output=True, text=True, timeout=10)
                dur = float(r.stdout.strip())
            except Exception:
                dur = 3.0
            entries.append((txt, dur))
            total_clip_dur += dur

        # Medir duração real do vídeo concatenado (que pode ser menor por causa do xfade)
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(out_mp4)],
                capture_output=True, text=True, timeout=10)
            real_video_dur = float(r.stdout.strip())
        except Exception:
            real_video_dur = total_clip_dur

        # Fator de compressão temporal (xfade encurta o vídeo)
        time_scale = real_video_dur / total_clip_dur if total_clip_dur > 0 else 1.0

        # Filtrar legendas: só narrador/narradora (falas de personagens já
        # estão nos balões do manhwa, legenda é redundante e tampa)
        narrator_entries = []
        t_cursor = 0.0
        for (txt, dur), persona in zip(entries, clip_personas):
            start = t_cursor * time_scale
            t_cursor += dur
            pclean = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona or "").strip().lower()
            if pclean in ("narrador", "narradora") and txt.strip():
                narrator_entries.append((txt, dur * time_scale, start))

        if narrator_entries:
            # Karaokê (palavra ativa amarela) ou estáticas (brancas)
            if hyperframes_karaoke:
                # MODO HYPERFRAMES: renderiza via Playwright/GSAP
                import render_karaoke
                log(f"  Karaokê HyperFrames (Playwright+GSAP)...")
                subs = []
                for idx, (txt, dur, start) in enumerate(narrator_entries):
                    webm_path = session_tmp / f"_hfk_{idx:03d}.webm"
                    result = render_karaoke.render_karaoke(
                        txt, str(webm_path), duration=dur,
                        width=1080, height=1920, font_size=65, stroke=8)
                    if result and Path(result).exists():
                        # Converter WebM → overlay no vídeo principal
                        # O WebM do Playwright não tem canal alpha real (fundo sólido)
                        # Então usamos a mesma abordagem de overlay com timing
                        subs.append({"webm": str(result), "start": start,
                                     "end": start + dur})
                # Se tiver WebMs, sobrepor via ffmpeg (filter_complex com movie+overlay)
                if subs:
                    log(f"  Queimando {len(subs)} overlays karaokê HyperFrames...")
                    out_hfk = out_mp4.with_name(out_mp4.stem + "_hfk.mp4")
                    _burn_webm_overlays(out_mp4, subs, out_hfk)
                    if out_hfk.exists() and out_hfk.stat().st_size > 0:
                        out_mp4.unlink()
                        out_hfk.rename(out_mp4)
                        log(f"  ✓ Karaokê HyperFrames queimado ({len(subs)} frases)")
                    else:
                        log("  ⚠ HyperFrames karaokê falhou, mantendo vídeo sem karaokê")
                else:
                    log("  ⚠ Nenhum WebM de karaokê gerado")
                # O karaokê HyperFrames já foi queimado no vídeo (overlays webm).
                # Zera subs pra que name tags + watermark (PNG) sigam num burn_subtitles
                # limpo — senão os dicts {"webm":...} causam KeyError 'png'.
                subs = []
            elif karaoke:
                # Legenda dinâmica estilo Shorts (1-2 palavras por vez) por padrão.
                # Desligável com SUB_SHORT=0 (volta ao karaokê de frase inteira).
                if os.environ.get("SUB_SHORT", "1") != "0":
                    subs = effects_engine.render_subtitles_short(
                        [(txt, dur) for txt, dur, _ in narrator_entries], session_tmp,
                        offsets=[s for _, _, s in narrator_entries])
                    log(f"  Legenda curta (1-2 palavras): {len(subs)} cards")
                else:
                    subs = effects_engine.render_subtitles_progressive(
                        [(txt, dur) for txt, dur, _ in narrator_entries], session_tmp,
                        offsets=[s for _, _, s in narrator_entries])
                    log(f"  Karaokê: {len(subs)} PNGs gerados (limite 150)")
            else:
                subs = effects_engine.render_subtitles(
                    [(txt, dur) for txt, dur, _ in narrator_entries], session_tmp,
                    offsets=[s for _, _, s in narrator_entries])
        else:
            subs = []

        # Name tags: nome do personagem que fala (acima da legenda).
        # DESATIVADO por padrão (v6+): as personas vinham GENÉRICAS (Homem/Mulher/Colega)
        # e apareciam na tela como se fossem legenda — era pra ser info interna.
        # Reative com SHOW_NAME_TAGS=1 (idealmente só quando houver nomes reais).
        t_cursor = 0.0
        for (txt, dur), persona in zip(entries, clip_personas):
            if os.environ.get("SHOW_NAME_TAGS", "0") != "1":
                break
            start = t_cursor
            t_cursor += dur
            pclean = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona or "").strip()
            if (pclean and txt.strip()
                    and pclean.lower() not in ("narrador", "narradora", "narrator", "personagem")):
                npng = session_tmp / f"_name_{int(start*100):05d}.png"
                res = effects_engine.render_name_tag(pclean, npng)
                if res:
                    _, nx, ny = res
                    subs.append({"png": str(npng), "x": nx, "y": ny,
                                 "start": start, "end": min(start + dur, start + 1.8)})
        # Watermark do canal (fixo no topo) junto com as legendas
        if branding:
            total_dur = sum(d for _, d in entries)
            wm = effects_engine.render_watermark(WATERMARK_HANDLE, session_tmp, total_dur)
            if wm:
                subs.append(wm)
        out_subs = out_mp4.with_name(out_mp4.stem + "_subs.mp4")
        if subs and effects_engine.burn_subtitles(out_mp4, subs, out_subs):
            out_mp4.unlink()
            out_subs.rename(out_mp4)
            log(f"  ✓ Legendas + watermark queimados")
        else:
            log("  ⚠ Falha ao queimar legendas (mantendo vídeo sem legenda)")
        # (limpeza dos PNGs de legenda movida pro fim: a versão censurada reusa estas subs)

        # DEBUG opcional (DUMP_SUBS_TIMING=1): sidecar <video>.timing.txt com
        # clip → tempo real (pós-xfade) → persona → painel → texto. É a base do
        # fluxo de diagnóstico de desync do _LEIA_FLUXO (seção 0).
        if os.environ.get("DUMP_SUBS_TIMING") == "1":
            try:
                dbg = out_mp4.with_suffix(".timing.txt")
                with open(dbg, "w", encoding="utf-8") as _f:
                    _f.write(f"n_clips={len(entries)} total_clip_dur={total_clip_dur:.2f} "
                             f"real_video_dur={real_video_dur:.2f} time_scale={time_scale:.4f}\n")
                    _tc = 0.0
                    for _i, ((_txt, _dur), _persona) in enumerate(zip(entries, clip_personas)):
                        _st = _tc * time_scale
                        _tc += _dur
                        _pn = Path(clips[_i]).name if _i < len(clips) else "?"
                        _f.write(f"clip{_i:02d} start={_st:7.2f} dur={_dur:5.2f} "
                                 f"[{(_persona or '')[:16]:16}] {_pn} :: {(_txt or '')[:50]}\n")
                log(f"  [debug] timing dump → {dbg.name}")
            except Exception as _e:
                log(f"  ⚠ dump timing falhou: {_e}")

    # 3c-bis. Upscale 720p → 1080p (Full HD de entrega)
    # O principal NÃO upscala por padrão: só a CENSURADA é postada (e ela upscala
    # sozinha, ver 3d). Poupa tempo/CPU. Force com UPSCALE_MAIN=1 se precisar do
    # principal em 1080p. TEST_MODE >= 1 também pula.
    if TEST_MODE < 1 and os.environ.get("UPSCALE_MAIN", "0") == "1":
        log("  Upscalando 720p → 1080p (principal, UPSCALE_MAIN=1)...")
        upscaled = out_mp4.with_name(out_mp4.stem + "_hd.mp4")
        if effects_engine.upscale_to_fullhd(out_mp4, upscaled):
            out_mp4.unlink()
            upscaled.rename(out_mp4)
            log(f"  ✓ Upscale 720→1080p feito")
        else:
            log("  ⚠ Upscale falhou (mantendo 720p)")
    else:
        log("  Principal mantido em 720p (só a censurada upscala p/ 1080p)")

    # 📊 RESUMO DE EFEITOS — mostra o que REALMENTE saiu, sem precisar assistir o vídeo.
    # Se algo esperado deu 0, avisa alto (causa comum de "não vi diferença").
    log(f"  📊 Efeitos: parallax={_n_parallax} · panel-fx={_n_panelfx} · "
        f"mascote={_n_mascote} · memes={getattr(effects_engine, '_memes_inseridos', 0)}")
    try:  # histograma de efeitos de painel — valida VARIEDADE (se 1 domina >50%, roteamento concentrado)
        import panel_effects as _pfxh
        _h = _pfxh.fx_hist()
        if _h:
            _top = sorted(_h.items(), key=lambda x: -x[1])
            log("  📊 Painel-fx (histograma): " + " · ".join(f"{k}={v}" for k, v in _top))
            _tot = sum(_h.values())
            if _tot and _top[0][1] / _tot > 0.5:
                log(f"  ⚠ 1 efeito domina >50% ({_top[0][0]}) — variedade baixa, revisar roteamento")
    except Exception:
        pass
    if os.environ.get("PARALLAX") == "1" and _n_parallax == 0:
        log("  ⚠ PARALLAX=1 mas 0 painéis com parallax → depth não cacheado; ligue PARALLAX_ONDEMAND=1 (ou rode o worker de depth)")
    if os.environ.get("MASCOTE_OVERLAY") == "1" and _n_mascote == 0:
        log("  ⚠ MASCOTE_OVERLAY=1 mas 0 aparições → confira as poses em workspace/assets/overlays/elemental/fx_mascot_*.mov")

    size_mb = out_mp4.stat().st_size / (1024 * 1024)
    log(f"  ✓ Vídeo final: {out_mp4.name} ({size_mb:.1f} MB)")

    # 3d. Versão CENSURADA pra Shorts — censura VISUAL na imagem (exodia fosco / blur total).
    # Monta a partir de clips_cens (só os +18 trocados pela imagem censurada). Timeline idêntica
    # ao principal → reusa a MESMA trilha e as MESMAS legendas (subs).
    if censura and _n_cens > 0:
        log(f"  Gerando versão censurada ({_n_cens} painéis +18 com exodia/blur na imagem)...")
        out_cens = out_mp4.with_name(out_mp4.stem.replace("_ULTIMO", "") + "_CENSURADO_ULTIMO.mp4")
        # a) concat (mesma lógica do principal)
        if _use_xfade and hasattr(effects_engine, "concat_with_xfade"):
            ok_c = effects_engine.concat_with_xfade(clips_cens, out_cens, descriptions=descriptions)
        else:
            ok_c = effects_engine.concat_with_transitions(clips_cens, out_cens, descriptions=descriptions)
        if ok_c and out_cens.exists():
            # b) trilha dinâmica (mesma do principal)
            _trilhas_dir = PROJECT_DIR / "workspace" / "assets" / "trilhas"
            if _trilhas_dir.exists() and (_trilhas_dir / "moods.json").exists():
                _cm = out_cens.with_name(out_cens.stem + "_music.mp4")
                effects_engine.add_dynamic_music(out_cens, recap.get("locucoes", []), _cm,
                                                 _trilhas_dir, music_volume=0.18, no_copyright=no_copyright_ost)
                if _cm.exists() and _cm.stat().st_size > 0:
                    out_cens.unlink(); _cm.rename(out_cens)
            # c) legendas — reusa as MESMAS do principal (timeline idêntica)
            if subs:
                _cs = out_cens.with_name(out_cens.stem + "_subs.mp4")
                if effects_engine.burn_subtitles(out_cens, subs, _cs) and _cs.exists():
                    out_cens.unlink(); _cs.rename(out_cens)
            # d) upscale 720p → 1080p (entrega Full HD)
            if TEST_MODE < 1:
                _cu = out_cens.with_name(out_cens.stem + "_hd.mp4")
                if effects_engine.upscale_to_fullhd(out_cens, _cu) and _cu.exists():
                    out_cens.unlink(); _cu.rename(out_cens)
            log(f"  ✓ Versão censurada: {out_cens.name}")
        else:
            log("  ⚠ Falha ao concatenar versão censurada")
    elif censura and cens_jobs:
        log(f"  ⚠ Censura: {len(cens_jobs)} painéis +18 detectados mas nenhum clip censurado gerado")
    elif censura:
        log("  (Censura: nenhum painel +18 detectado neste capítulo)")

    # Limpeza dos PNGs de legenda (após a censurada reusar as subs)
    for s in subs:
        try:
            Path(s.get("png", "")).unlink()
        except Exception:
            pass

    # Thumbnail via IA (opt-in GEN_THUMBNAIL=1). Gera capa pra postagem via gateway.
    if os.environ.get("GEN_THUMBNAIL", "0") == "1":
        try:
            import omniroute_image
            cap_match = re.search(r"cap[_-]?(\d+)", titulo, re.I)
            cap_num = int(cap_match.group(1)) if cap_match else 1
            obra_slug = re.sub(r"[^a-z0-9]+", "-", titulo.lower().strip())[:40]
            thumb = omniroute_image.generate_thumbnail(titulo, obra_slug, cap_num)
            if thumb:
                import shutil
                thumb_dest = out_mp4.parent / "thumbnail.png"
                shutil.copy2(thumb, thumb_dest)
                log(f"  ✓ thumbnail salva: {thumb_dest}")
        except Exception as e:
            log(f"  ⚠ thumbnail falhou: {e}")

    # Salvar meta
    meta = {
        "titulo": titulo,
        "titulo_video": recap.get("titulo_video", titulo),
        "tags": recap.get("tags", []),
        "panels_count": len(clips),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file": out_name,
        "size_mb": round(size_mb, 1),
        "quality_profile": os.environ.get("QUALITY_PROFILE", "standard"),
        "tts_engine": os.environ.get("TTS_ENGINE", "edge"),
        "features": {
            "subtitles": subtitles,
            "karaoke": karaoke,
            "audio_enhancement": True,
            "viral_filters": True,
            "sfx_contextual": True,
            "foley_direct": True,
            "overlays_atmospheric": True,
        },
    }
    meta_path = out_mp4.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    # 4. Notify
    if not skip_notify:
        log("  Enviando pro Telegram...")
        caption = (
            f"🎬 {_tg_safe.b(recap.get('titulo_video', titulo))}\n"
            f"📊 {len(clips)} painéis | {size_mb:.1f} MB\n"
            f"🏷 {', '.join(recap.get('tags', [])[:5])}"
        )
        _tg_safe.send_video(str(out_mp4), caption=caption)

    # Cleanup tmp
    try:
        import shutil
        shutil.rmtree(session_tmp)
    except Exception:
        pass

    # 4. Auto-validação (roda sempre, só loga — desativável com AUTO_VALIDATE=0)
    if os.environ.get("AUTO_VALIDATE", "1") == "1":
        try:
            import importlib.util
            validate_path = Path(__file__).resolve().parent / "auto-validate.py"
            if validate_path.exists():
                spec = importlib.util.spec_from_file_location("auto_validate", validate_path)
                av = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(av)
                result = av.validate(str(out_mp4))
                if result["status"] == "OK":
                    log(f"  ✅ Auto-validação: APROVADO")
                else:
                    log(f"  ⚠️ Auto-validação: {len(result['problemas'])} problema(s)")
                    for p in result["problemas"]:
                        log(f"     - {p}")
                    # Quarentena: problemas graves → mover pra pasta separada
                    grave = any("dessincronizado" in p or "silencioso" in p or "tela preta" in p
                               for p in result["problemas"])
                    if grave:
                        quarentena_dir = VIDEOS_DIR / "_quarentena"
                        quarentena_dir.mkdir(exist_ok=True)
                        dest = quarentena_dir / out_mp4.name
                        out_mp4.rename(dest)
                        log(f"  🚫 Vídeo movido pra quarentena: {dest.name}")
                        out_mp4 = dest
        except Exception as e:
            log(f"  ⚠ Auto-validação falhou: {e}")

    # 5. ORGANIZAÇÃO EM PASTAS — videos/<obra>/capNN/{engine}/normal/vN.mp4 + censored/vN.mp4
    # Convenção oficial (ver landscape-compiler.py / hyperframes-from-normal.py):
    #   normal (limpo) fica sob o ENGINE (edge|gemini) porque muda com a voz;
    #   censored fica no nível do cap (é derivada, uma por cap).
    # Pós-passo NÃO-destrutivo: move os arquivos flat já prontos pra estrutura.
    # Fallback total: qualquer erro → mantém os arquivos flat (não perde vídeo).
    try:
        obra = re.sub(r"[^a-z0-9]+", "-", (Path(panels_dir).name)).strip("-")
        obra = re.sub(r"-cap\d+.*$", "", obra) or slug  # "regressed-warriors-cap03" → "regressed-warriors"
        _m = re.search(r"cap[_-]?(\d+)", Path(panels_dir).name, re.I)
        cap_key = f"cap{int(_m.group(1)):02d}" if _m else "cap00"
        engine = os.environ.get("TTS_ENGINE", "edge")
        if engine not in ("edge", "gemini", "eleven"):
            engine = "edge"

        cap_dir = VIDEOS_DIR / obra / cap_key
        norm_dir = cap_dir / engine / "normal"
        norm_dir.mkdir(parents=True, exist_ok=True)

        def _next_v(d):
            existing = [int(m.group(1)) for p in d.glob("v*.mp4")
                        if (m := re.match(r"v(\d+)\.mp4$", p.name))]
            return f"v{(max(existing) + 1) if existing else 1}.mp4"

        # principal (limpo) → <obra>/capNN/<engine>/normal/vN.mp4
        if out_mp4 and Path(out_mp4).exists():
            vname = _next_v(norm_dir)
            dest = norm_dir / vname
            import shutil as _sh
            _sh.move(str(out_mp4), str(dest))
            _meta = Path(out_mp4).with_suffix(".meta.json")
            if _meta.exists():
                _sh.move(str(_meta), str(dest.with_suffix(".meta.json")))
            log(f"  📁 normal → {obra}/{cap_key}/{engine}/normal/{vname}")
            out_mp4 = dest

        # censurada → <obra>/capNN/censored/vN.mp4 (nível do cap)
        if out_cens and Path(out_cens).exists():
            cens_dir = cap_dir / "censored"
            cens_dir.mkdir(parents=True, exist_ok=True)
            cvname = _next_v(cens_dir)
            cdest = cens_dir / cvname
            import shutil as _sh
            _sh.move(str(out_cens), str(cdest))
            log(f"  📁 censored → {obra}/{cap_key}/censored/{cvname}")
    except Exception as e:
        log(f"  ⚠ organização em pastas falhou (arquivos mantidos flat): {e}")

    return out_mp4


def run_batch(urls, args):
    """Processa vários capítulos em sequência (Ponto K), com retomada.

    Salva progresso em workspace/batch_progress.json. URLs já concluídas com
    sucesso são puladas em execuções seguintes (retoma após queda). Uma falha
    num capítulo NÃO interrompe o lote — registra e segue pro próximo.
    """
    import importlib.util
    fetcher_path = Path(__file__).resolve().parent / "hiper-fetcher.py"
    spec = importlib.util.spec_from_file_location("hiper_fetcher", fetcher_path)
    hiper_fetcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hiper_fetcher)

    progress_file = PROJECT_DIR / "workspace" / "batch_progress.json"
    try:
        progress = json.loads(progress_file.read_text()) if progress_file.exists() else {}
    except Exception:
        progress = {}

    total = len(urls)
    log(f"═══ LOTE: {total} capítulos ═══")
    done, failed, skipped = 0, 0, 0

    for idx, url in enumerate(urls, start=1):
        if progress.get(url, {}).get("status") == "done":
            log(f"[{idx}/{total}] ⏭  já concluído, pulando: {url}")
            skipped += 1
            continue

        slug = hiper_fetcher.slugify(url.split("/")[-1] or url.split("/")[-2] or "chapter")
        # Título por capítulo: base + sufixo do slug (ex: "... cap 3")
        cap_titulo = f"{args.titulo} — {slug}" if total > 1 else args.titulo
        log(f"[{idx}/{total}] ▶ {url}")

        try:
            panels = hiper_fetcher.fetch_chapter(url, slug, headed=args.headed)
            if not panels:
                raise RuntimeError("scrape retornou vazio")

            result = run_pipeline(
                panels, cap_titulo,
                max_panels=args.max_panels,
                skip_notify=args.skip_notify,
                dry_run=args.dry_run,
                animated=args.animated,
                start_panel=args.start_panel,
                fusao=args.fusao,
                narrator_gender=args.narrator_gender,
                subtitles=args.subtitles,
                branding=args.branding,
                karaoke=args.karaoke,
                censura=args.censura,
                force_llm=args.force_llm,
                force_tts=args.force_tts, no_copyright_ost=args.no_copyright_ost,
                hyperframes_karaoke=args.hyperframes_karaoke,
                output_suffix=args.output_suffix,
                audio_only=args.audio_only,
            )
            if result:
                progress[url] = {"status": "done", "file": str(result),
                                 "at": datetime.now(timezone.utc).isoformat()}
                done += 1
                log(f"[{idx}/{total}] ✓ pronto: {Path(result).name}")
            else:
                raise RuntimeError("pipeline retornou None")
        except Exception as e:
            progress[url] = {"status": "failed", "error": str(e),
                             "at": datetime.now(timezone.utc).isoformat()}
            failed += 1
            log(f"[{idx}/{total}] ✗ falhou: {e}")

        # Salva progresso após CADA capítulo (retomável)
        try:
            progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2))
        except Exception:
            pass

    log(f"═══ LOTE FIM: {done} ok, {failed} falhas, {skipped} pulados ═══")
    if failed:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Pipeline de vídeo hipercool")
    parser.add_argument("--url", help="URL do capítulo (scrape + pipeline)")
    parser.add_argument("--slug", help="Slug de capítulo já no cache")
    parser.add_argument("--panels-dir", help="Diretório com painéis já cortados")
    parser.add_argument("--titulo", "-t", required=True, help="Título do manhwa/capítulo")
    parser.add_argument("--max-panels", type=int, default=MAX_PANELS_DEFAULT,
                        help=f"Máximo de painéis (default: {MAX_PANELS_DEFAULT})")
    parser.add_argument("--start-panel", type=int, default=0,
                        help="Offset de início (parte 2+ do capítulo; ex: 55)")
    parser.add_argument("--skip-notify", action="store_true",
                        help="Não enviar notificação Telegram")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria feito sem executar")
    parser.add_argument("--animated", action="store_true",
                        help="Usa modo animado (breathing/parallax) nos painéis")
    parser.add_argument("--fusao", action="store_true",
                        help="TESTE: funde visão+narração numa só chamada Gemini")
    parser.add_argument("--narrator-gender", choices=["M", "F"], default="F",
                        help="Gênero da narradora off (default F)")
    parser.add_argument("--subtitles", action="store_true",
                        help="Queima legendas estilo Shorts no vídeo")
    parser.add_argument("--karaoke", action="store_true",
                        help="Legendas progressivas (palavra ativa destacada). Requer --subtitles")
    parser.add_argument("--no-branding", dest="branding", action="store_false",
                        help="Desliga intro/outro (CTA inscreva-se)")
    parser.add_argument("--censura", action="store_true",
                        help="Gera também versão censurada (mosaico nos painéis +18) pra Shorts")
    parser.add_argument("--headed", action="store_true",
                        help="Browser visível (se usar --url)")
    # Ponto K: lote multi-capítulo
    parser.add_argument("--urls", nargs="+", metavar="URL",
                        help="Lote: várias URLs de capítulos processadas em sequência")
    parser.add_argument("--batch-file", metavar="ARQUIVO",
                        help="Lote: arquivo de texto com 1 URL por linha (# = comentário)")
    # Flags de rebuild/cache
    parser.add_argument("--force-llm", action="store_true",
                        help="Ignora narration_cache, força nova geração de narração via LLM")
    parser.add_argument("--force-tts", action="store_true",
                        help="Ignora tts_cache, força nova geração de áudio TTS")
    parser.add_argument("--no-copyright-ost", action="store_true", help="Usa apenas OSTs marcadas sem copyright risk (p/ monetizacao segura YT)")
    parser.add_argument("--hyperframes-karaoke", action="store_true",
                        help="Usa render_karaoke.py (Playwright) para legendas HyperFrames")
    parser.add_argument("--output-suffix", default="",
                        help="Sufixo no nome do vídeo final (ex: _NORMAL, _HYPERFRAMES)")
    parser.add_argument("--audio-only", action="store_true",
                        help="Só gera narração+TTS (enche os caches) e PARA antes do ffmpeg. Fase serial da fábrica de áudio.")
    parser.add_argument("--preset", choices=["teste", "final", "night"],
                        help="Liga TODAS as flags de efeito de uma vez (parallax, panel-fx, mascote, "
                             "elemental...) — evita setar 15 env vars à mão. teste=720p rápido; "
                             "final/night=1080p. Env explícito ainda tem prioridade.")

    args = parser.parse_args()

    # --preset: liga o CONJUNTO certo de flags de efeito de uma vez (senão o agente esquece alguma
    # e o vídeo sai "sem diferença"). Env explícito setado antes AINDA ganha (setdefault).
    if getattr(args, "preset", None):
        _fx = {"PANEL_FX": "1", "PARALLAX": "1", "PARALLAX_ONDEMAND": "1",
               "MASCOTE_OVERLAY": "1", "MASCOTE_MAX": "5", "ELEMENTAL_TRANS": "1",
               "CONTENT_ADAPT": "1", "SUB_CONTEXT": "1", "CONTEXT_MOTION": "1",
               "TRIM_SILENCE": "1", "SFX_MODE": "gap", "CLIP_GAP_DYNAMIC": "1",
               "DUMP_SUBS_TIMING": "1"}
        if args.preset == "teste":
            _fx["TEST_MODE"] = "1"        # 720p, pula upscale (iteração rápida)
        else:                            # final / night
            _fx["UPSCALE_MAIN"] = "1"     # principal também em 1080p
        for _k, _v in _fx.items():
            os.environ.setdefault(_k, _v)
        global TEST_MODE                 # foi lido no import → re-aplica se o preset mexeu
        TEST_MODE = int(os.environ.get("TEST_MODE", "0"))
        print(f"  [preset={args.preset}] flags de efeito ligadas (parallax/panel-fx/mascote/elemental)")

    # Contexto pro log de erros estruturado (logs/errors.jsonl sabe de qual cap veio)
    try:
        os.environ["_HIPER_TITULO"] = args.titulo or ""
    except Exception:
        pass

    # ── Modo LOTE (Ponto K) ────────────────────────────────────────────────
    batch_urls = []
    if args.urls:
        batch_urls = list(args.urls)
    elif args.batch_file:
        bf = Path(args.batch_file)
        if not bf.is_file():
            print(f"ERRO: batch-file '{bf}' não existe", file=sys.stderr)
            sys.exit(1)
        for line in bf.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                batch_urls.append(line)

    if batch_urls:
        run_batch(batch_urls, args)
        return

    # Determinar source dos painéis
    panels_dir = None

    if args.panels_dir:
        panels_dir = Path(args.panels_dir)
        if not panels_dir.is_dir():
            print(f"ERRO: {panels_dir} não existe", file=sys.stderr)
            sys.exit(1)

    elif args.slug:
        cache_path = CACHE_DIR / args.slug
        if not cache_path.is_dir():
            print(f"ERRO: slug '{args.slug}' não encontrado no cache", file=sys.stderr)
            sys.exit(1)
        panels_dir = cache_path

    elif args.url:
        # Importar fetcher (mesmo diretório bin/)
        import importlib.util
        fetcher_path = Path(__file__).resolve().parent / "hiper-fetcher.py"
        spec = importlib.util.spec_from_file_location("hiper_fetcher", fetcher_path)
        hiper_fetcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hiper_fetcher)

        slug = args.slug or hiper_fetcher.slugify(args.url.split("/")[-1] or "chapter")
        result = hiper_fetcher.fetch_chapter(args.url, slug, headed=args.headed)
        if not result:
            print("ERRO: Falha ao baixar capítulo", file=sys.stderr)
            sys.exit(1)
        panels_dir = result

    else:
        print("ERRO: forneça --url, --slug, ou --panels-dir", file=sys.stderr)
        sys.exit(1)

    result = run_pipeline(
        panels_dir, args.titulo,
        max_panels=args.max_panels,
        skip_notify=args.skip_notify,
        dry_run=args.dry_run,
        animated=args.animated,
        start_panel=args.start_panel,
        fusao=args.fusao,
        narrator_gender=args.narrator_gender,
        subtitles=args.subtitles,
        branding=args.branding,
        karaoke=args.karaoke,
        censura=args.censura,
        force_llm=args.force_llm,
        force_tts=args.force_tts, no_copyright_ost=args.no_copyright_ost,
        hyperframes_karaoke=args.hyperframes_karaoke,
        output_suffix=args.output_suffix,
        audio_only=args.audio_only,
    )

    if result:
        print(f"\n✓ Vídeo pronto: {result}")
    elif not args.dry_run:
        print("\n✗ Pipeline falhou.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

