# -*- coding: utf-8 -*-
"""story_pipeline.py — Pipeline COMPLETO de vídeos originais (histórias-em-frames).

Integra TODAS as features do hipercool-fix: ensemble narration, censura visual,
parallel TTS (8 workers), panel classifier, motion director, mascote overlay,
batch mode, command files, preset system, audio-only factory, HyperFrames karaoke,
name tags, Telegram, auto-validação com quarentena, thumbnail, no-copyright-ost,
quality profiles, elemental transitions, parallax 2.5D, panel effects (43+).
"""
import os
import re
import sys
import json
import time
import shutil
import hashlib
import argparse
import subprocess
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hp_common import (PROJECT_DIR, CACHE_DIR, VIDEOS_DIR, TMP_DIR, IMAGES_DIR,
                        NARRATION_CACHE_DIR, WATERMARK_HANDLE, TEST_MODE, log,
                        MAX_SCENES_DEFAULT, fix_loop1_cmd)

# Monkey-patch subprocess para reescrever todo '-loop 1 -i imagem' em clipes .mov (evita
# trava do ffmpeg 8; ver hp_common.clipe_parado). Só afeta chamadas com "ffmpeg" nos args.
_orig_sp_run = subprocess.run
_orig_sp_popen = subprocess.Popen


def _patched_run(cmd, *a, **kw):
    if isinstance(cmd, (list, tuple)) and any("ffmpeg" in str(c) for c in cmd[:2]):
        cmd = fix_loop1_cmd(cmd)
    return _orig_sp_run(cmd, *a, **kw)


class _PatchedPopen(_orig_sp_popen):
    def __init__(self, cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and any("ffmpeg" in str(c) for c in cmd[:2]):
            cmd = fix_loop1_cmd(cmd)
        super().__init__(cmd, *a, **kw)


subprocess.run = _patched_run
subprocess.Popen = _PatchedPopen

import effects_engine
from fx_clips import (build_clip, build_clip_with_shake, build_intro_clip,
                      build_outro_clip, build_meme_clip, should_insert_meme,
                      concat_with_xfade, upscale_to_fullhd, shake_clip)
import diretor_cena
import memes_catalogo
import fx_legendas_ass
import fx_audio_final
import fx_divisoria
from fx_branding import frase_cta
from fx_detect import (pick_sfx_for_text, overlay_for_mood, overlay_para_cena, detect_mood_from_text,
                       is_impact_panel, is_tension_panel)
from fx_subtitles import render_subtitles_short, burn_subtitles, render_watermark
from fx_assets import EffectsManager, TRANSITIONS
# Resolução/fps dos clips do pipeline (o parallax 2.5D precisa casar EXATO com os
# demais clips, senão o concat/xfade quebra). São os mesmos W/H/FPS que build_clip usa.
from fx_assets import W as _PW, H as _PH, FPS as _PFPS
import panel_effects
import parallax_engine
import panel_classifier
import motion_director
import elemental_transitions
import edge_tts_engine
import auto_validate
import viralizador
import word_pop
import quality_judge
import canal_profiles
import music_escalation
import advanced_parallax

try:
    import worker_client
except ImportError:
    worker_client = None

# CENSURA: NÃO NECESSÁRIA neste projeto (imagens são IA-geradas, sem conteúdo +18 real).
# Mantém apenas o dicionário anti-ban (palavras que o YT flagra) no story_writer.
# A flag --censura existe no CLI por compatibilidade mas é no-op aqui.
censura_visual = None

try:
    import mascote_overlay
except ImportError:
    mascote_overlay = None

try:
    from _tg_safe import send_telegram
except ImportError:
    def send_telegram(msg): pass

try:
    import narration
except ImportError:
    narration = None


def _write_postar_json(story_out_dir, final_name, genero, tema,
                       titulo_viral, hashtags, cenas):
    """Grava postar.json ao lado do mp4 final, no padrao de hipercool-materiais
    (PADRAO_DOC_POSTAGEM.md). Categoria fixa 'historias'. A cola le isto e posta
    sem adivinhar arquivo/metadados.

    Se 'usar_crew_viral' estiver true no settings.json, tenta o sistema
    multi-agente (titulo + descricao + tags, 3 chamadas LLM em paralelo via
    bin/viral_crew.py) ANTES do viralizador leve. Em qualquer falha (sem
    gateway / offline / quota / timeout), cai pro viralizador.py e, em ultimo
    caso, pra template. Assim a producao 10h nunca trava por causa de metadata."""
    # 1) tenta crew multi-agente se flag ligado
    usar_crew = False
    try:
        cfg_path = Path(__file__).resolve().parent.parent / "config" / "settings.json"
        if cfg_path.exists():
            usar_crew = bool(json.loads(
                cfg_path.read_text(encoding="utf-8")).get("usar_crew_viral", False))
    except Exception:
        usar_crew = False

    # 0) SEO novo (§1 do MELHORIAS_PARA_TODOS_OS_PROJETOS.md): 3 títulos pela história + Thompson de estilo.
    #    Falhou = segue o caminho de antes (crew/viralizador). A rede do manhwa-react adapta por canal em cima disto.
    narr = " ".join(str(c.get("narracao") or c.get("texto") or "") for c in (cenas or []) if isinstance(c, dict))
    seo = None
    try:
        import seo_generator
        seo = seo_generator.gerar_seo_historia(genero, tema, titulo_viral, narr, chave=Path(story_out_dir).name)
        if seo:
            print(f"  + SEO estilo={seo['estilo']}: {seo['titulo']}")
    except Exception as e:
        print(f"  ! SEO falhou (segue o viralizador): {e}")

    crew_out = None
    if usar_crew and not seo:
        try:
            import viral_crew
            crew_out = viral_crew.gerar_metadados(
                titulo_viral, genero, tema, cenas, timeout=180)
            if crew_out:
                print(f"  + crew viral OK em {crew_out.get('_tempo_s','?')}s "
                      f"(tags={len(crew_out.get('tags', []))})")
        except Exception as e:
            print(f"  ! crew viral falhou (cai pro viralizador): {e}")
            crew_out = None

    # 2) SEO novo > crew > viralizador
    if seo:
        titulo_final = seo["titulo"]
        descricao_final = seo["descricao"]
        tags = seo["tags"][:25]
    elif crew_out and all(crew_out.get(k) for k in ("titulo", "descricao", "tags")):
        titulo_final = crew_out["titulo"]
        descricao_final = crew_out["descricao"]
        tags = crew_out["tags"][:15]
    elif crew_out and (crew_out.get("titulo") or crew_out.get("descricao")):
        # parcial: usa o que veio e completa o resto com viralizador
        titulo_final = crew_out.get("titulo") or titulo_viral
        descricao_final = crew_out.get("descricao") or ""
        tags_parciais = crew_out.get("tags") or []
        if not descricao_final:
            try:
                descricao_final = viralizador.generate_full_description(
                    titulo_final, genero, cenas)
            except Exception:
                descricao_final = f"{titulo_final}\n\n{hashtags}"
        if not tags_parciais:
            for h in str(hashtags).split():
                t = h.lstrip("#").strip()
                if t and t.lower() not in [x.lower() for x in tags_parciais]:
                    tags_parciais.append(t)
        tags = tags_parciais[:15]
    else:
        # 3) fallback: viralizador leve (como antes)
        titulo_final = titulo_viral
        tags = []
        for h in str(hashtags).split():
            t = h.lstrip("#").strip()
            if t and t.lower() not in [x.lower() for x in tags]:
                tags.append(t)
        tags = tags[:15]
        try:
            descricao_final = viralizador.generate_full_description(
                titulo_viral, genero, cenas)
        except Exception:
            descricao_final = f"{titulo_viral}\n\n{hashtags}"

    doc = {
        "arquivo": final_name,          # OBRIGATORIO: mp4 final relativo a esta pasta
        "categoria": "historias",       # OBRIGATORIO
        "tipo": "completo",             # OBRIGATORIO
        "titulo": titulo_final[:100],   # OBRIGATORIO
        "descricao": descricao_final[:5000],  # OBRIGATORIO
        "tags": tags,                   # OBRIGATORIO
        "genero": genero,               # extra util (roteamento futuro por genero)
        "tema": tema,
        "privacy": "public",
        "made_for_kids": False,
        "pronto": True,
    }
    if seo:
        doc["estilo_titulo"] = seo["estilo"]  # pra comparar o CTR por estilo (seo_generator.registrar_resultado)
    out = Path(story_out_dir) / "postar.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3) capa IA 9:16 (§2): cena da própria história + frase do SEO; a rede sobe como miniatura ("thumb").
    #    Depois do postar.json gravado: se a capa falhar/demorar, o vídeo segue pronto sem capa própria.
    try:
        import capa_ia_historias
        capa = capa_ia_historias.gerar_capa(genero, Path(story_out_dir) / "capa.jpg", tema=tema,
                                            titulo=titulo_viral, texto=(seo or {}).get("texto_capa", ""))
        if capa:
            doc["thumb"] = capa.name
            out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"  ! capa IA falhou (segue sem capa propria): {e}")


def _esperar_ram(min_gb=1.8, timeout_s=90):
    """Espera a RAM disponível subir acima de min_gb (outro render pode estar num
    pico). Volta assim que houver folga, ou desiste após timeout_s. Sem psutil,
    dá uma pausa fixa curta. Evita que um pico momentâneo de memória corrompa o
    clip — em vez de perder o clip, respiramos e tentamos de novo."""
    try:
        import psutil
    except Exception:
        time.sleep(8)
        return
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if psutil.virtual_memory().available / (1024 ** 3) >= min_gb:
            return
        time.sleep(5)


def _clip_saudavel(path, min_dur=0.3):
    """True se o mp4 do clip está íntegro (tem moov atom + duração válida).
    Sob pressão de RAM o ffmpeg às vezes grava um mp4 TRUNCADO (bytes no disco,
    mas 'moov atom not found') — o teste antigo de st_size > 5000 aceitava esse
    lixo, e um clip podre no meio derrubava o concat inteiro (vídeo de 8s no
    lugar de 57s). Aqui checamos de verdade com ffprobe: se falhar, o caller
    cai pro próximo motor (panel_fx -> Ken Burns) e regenera o clip."""
    try:
        p = Path(path)
        if not p.exists() or p.stat().st_size < 5000:
            return False
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=duration", "-of", "csv=p=0", str(p)],
            capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return False
        dur = (r.stdout or "").strip()
        return bool(dur) and dur.upper() != "N/A" and float(dur) >= min_dur
    except Exception:
        return False


# ─── PRESETS ────────────────────────────────────────────────────────────────
PRESETS = {
    "teste": {
        "TEST_MODE": "1", "MAX_SCENES": "6", "TTS_WORKERS": "2",
        "PARALLAX": "1", "PARALLAX_ONDEMAND": "1", "PANEL_FX": "1", "ELEMENTAL_TRANS": "1",
        "MASCOTE_OVERLAY": "0", "MOTION_DIRECTOR": "0",
        "TRIM_SILENCE": "0", "CONTENT_ADAPT": "0",
        "CLIP_GAP_DYNAMIC": "0", "DUMP_SUBS_TIMING": "0",
    },
    "final": {
        "TEST_MODE": "0", "MAX_SCENES": "30", "TTS_WORKERS": "8",
        "PARALLAX": "1", "PARALLAX_ONDEMAND": "1", "PANEL_FX": "1", "ELEMENTAL_TRANS": "1",
        "MASCOTE_OVERLAY": "1", "MOTION_DIRECTOR": "1",
        "TRIM_SILENCE": "1", "CONTENT_ADAPT": "1",
        "CLIP_GAP_DYNAMIC": "1", "DUMP_SUBS_TIMING": "1",
    },
    "night": {
        "TEST_MODE": "0", "MAX_SCENES": "20", "TTS_WORKERS": "4",
        "PARALLAX": "1", "PARALLAX_ONDEMAND": "1", "PANEL_FX": "1", "ELEMENTAL_TRANS": "1",
        "MASCOTE_OVERLAY": "1", "MOTION_DIRECTOR": "0",
        "TRIM_SILENCE": "1", "CONTENT_ADAPT": "1",
        "CLIP_GAP_DYNAMIC": "1", "DUMP_SUBS_TIMING": "0",
    },
    "audio_only": {
        "TEST_MODE": "0", "MAX_SCENES": "30", "TTS_WORKERS": "8",
        "PARALLAX": "0", "PANEL_FX": "0", "ELEMENTAL_TRANS": "0",
        "MASCOTE_OVERLAY": "0", "MOTION_DIRECTOR": "0",
        "TRIM_SILENCE": "1", "CONTENT_ADAPT": "0",
        "CLIP_GAP_DYNAMIC": "0", "DUMP_SUBS_TIMING": "0",
    },
}

# ─── COMMAND FILES ──────────────────────────────────────────────────────────
COMMAND_STOP = PROJECT_DIR / "COMMAND_STOP.txt"
COMMAND_SKIP = PROJECT_DIR / "COMMAND_SKIP.txt"
COMMAND_PAUSE = PROJECT_DIR / "COMMAND_PAUSE.txt"

# ─── QUALITY PROFILES ──────────────────────────────────────────────────────
QUALITY = {
    "low":  {"crf": "28", "preset": "veryfast", "res": "720x1280"},
    "med":  {"crf": "23", "preset": "medium", "res": "720x1280"},
    "high": {"crf": "18", "preset": "slow", "res": "1080x1920"},
}

# ─── QUARANTINE ─────────────────────────────────────────────────────────────
QUARANTINE_DIR = VIDEOS_DIR / "_quarantine"
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

TTS_WORKERS = int(os.environ.get("TTS_WORKERS", "8"))
# PARALLEL RENDER: usa ThreadPoolExecutor pra renderizar clips simultaneamente.
# A etapa mais pesada (depth estimation ~20s) só roda 1 por vez (_MAX_PARALLEL_RAM=1)
# mas clips simples (Ken Burns, panel_fx) saturam os workers. Default: 2 workers.
_CLIP_WORKERS = int(os.environ.get("CLIP_WORKERS", "2"))
_RENDER_PARALLEL = os.environ.get("RENDER_PARALLEL", "1") == "1"


def _apply_preset(name):
    p = PRESETS.get(name)
    if not p:
        return
    for k, v in p.items():
        os.environ.setdefault(k, v)


def _check_command_files():
    if COMMAND_STOP.exists():
        log("⛔ COMMAND_STOP detectado — abortando")
        sys.exit(0)
    if COMMAND_PAUSE.exists():
        log("⏸ COMMAND_PAUSE detectado — aguardando remoção...")
        while COMMAND_PAUSE.exists():
            time.sleep(5)
        log("▶ PAUSE removido, continuando")
    return COMMAND_SKIP.exists()


def _ffprobe_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def _load_word_times(audio_path):
    """Tempo REAL de cada palavra que o edge-tts gravou em '<audio>.words.json'
    ([[ini, fim, palavra], ...], relativo ao inicio do audio). None se nao houver."""
    if not audio_path:
        return None
    try:
        with open(str(audio_path) + ".words.json", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) and data else None
    except Exception:
        return None


def _microcortes_falas(audio_files, story_id):
    """Microcortes (dona 22/10, narracao_curva.microcortes, comum): toda pausa entre e dentro das falas fica com
    ~0,07 s, a fala NAO acelera, o <wav>.words.json (legenda palavra a palavra) acompanha. Corta numa COPIA em
    workspace/tmp/microcortes/<story_id>/ — o narration_cache e compartilhado entre historias e nunca e alterado.
    Falhou = a fala segue como estava. Ligado por padrao desde 23/10 (dona aprovou); HISTORIAS_MICROCORTES=0 desliga."""
    try:
        import narracao_curva
    except Exception as e:  # noqa: BLE001
        log(f"  [!] microcortes indisponivel ({str(e)[:80]}) — falas sem corte")
        return audio_files
    pasta = TMP_DIR / "microcortes" / str(story_id)
    pasta.mkdir(parents=True, exist_ok=True)
    novos, antes, depois = {}, 0.0, 0.0
    for i, src in audio_files.items():
        try:
            dst = pasta / f"fala_{i:02d}.wav"
            shutil.copy2(src, dst)
            wj = Path(str(src) + ".words.json")
            wj_dst = Path(str(dst) + ".words.json")
            if wj.exists():
                shutil.copy2(wj, wj_dst)
            elif wj_dst.exists():
                wj_dst.unlink()
            r = narracao_curva.microcortes(dst)
            if r:
                antes += r[0]
                depois += r[1]
            novos[i] = str(dst)
        except Exception as e:  # noqa: BLE001
            log(f"  [!] microcortes cena {i + 1} falhou ({str(e)[:80]}) — fala segue sem")
            novos[i] = src
    if antes:
        log(f"  [microcortes] falas {antes:.2f}s -> {depois:.2f}s (-{antes - depois:.2f}s)")
    return novos


def _clean_text_for_tts(text):
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    t = re.sub(r'\*(.+?)\*', r'\1', t)
    t = re.sub(r'[_~`#>]', '', t)
    t = re.sub(r'\[.*?\]', '', t)
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _infer_gender_by_name(persona):
    p = (persona or "").lower()
    masc = ("rapaz", "homem", "garoto", "menino", "senhor", "general", "cavaleiro",
            "rei", "principe", "guerreiro", "soldado", "mestre", "lorde",
            "pai", "irmao", "tio", "capitao", "velho", "cara", "moco")
    fem = ("garota", "moca", "mulher", "menina", "senhora", "dama",
           "rainha", "princesa", "guerreira", "irma", "mae", "tia", "velha")
    if any(w in p for w in masc):
        return "M"
    if any(w in p for w in fem):
        return "F"
    return None


def _maybe_meme(text, idx, last_meme_idx, clip_mood, genero=None, usados=(), seed=None,
                clips_since_meme=4):
    """Meme do catalogo que COMBINA com a fala (memes_catalogo.escolher) + SFX da fala.
    Devolve {"file", "sfx", "desc"} ou None. So em genero leve."""
    if idx - last_meme_idx < clips_since_meme:
        return None
    if not memes_catalogo.ativo(genero) or not should_insert_meme(idx, clip_mood):
        return None
    meme = memes_catalogo.escolher(text, usados=usados, seed=f"{seed}-{idx}")
    if not meme:
        return None
    sfx = pick_sfx_for_text(text)
    sfx_path = sfx[0] if isinstance(sfx, tuple) else sfx
    return {"file": meme["file"], "sfx": sfx_path, "desc": meme.get("desc", "")}


# ═══════════════════════════════════════════════════════════════════════════════
# run() — PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
def run(genero="superacao", tema=None, n_cenas=None, variacoes=1,
        titulo_override=None, preset=None, audio_only=False, start_panel=0,
        no_branding=False, narrator_gender=None, dry_run=False,
        no_copyright_ost=False, quality="med", output_suffix="",
        skip_notify=False, censura=False, batch_id=None):
    """Executa o pipeline completo de geração de vídeo original."""

    t0 = time.time()
    # Definidos cedo: _mt_write() (handler de erro do roteiro/imagens) lê story_id
    # e titulo como variáveis livres. Se o pipeline falhar ANTES da atribuição real
    # (~linha 434-436), sem isto estoura NameError e MASCARA o erro verdadeiro.
    story_id = None
    titulo = None
    _stage_timers = {}   # etapa -> segundos
    _stage_start = time.time()
    _stage_events = []   # (t_abs, tipo, detalhe)
    _counters = {}       # nome -> int

    def _mt_count(n, inc=1):
        _counters[n] = _counters.get(n, 0) + inc

    def _mt_event(tipo, d=""):
        _stage_events.append({"t": round(time.time() - t0, 1), "tipo": tipo, "d": str(d)[:200]})

    def _mt_stage(nome):
        _stage_timers[nome] = round(time.time() - _stage_start, 2)
        globals()["_stage_start"] = time.time()

    def _mt_write(video_path=None, status="ok", extra=None):
        import json as _json
        _stage_timers["finalizacao"] = round(time.time() - _stage_start, 2)
        final_dur = extra.get("duracao_s") if extra else 0
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "story_id": story_id,
            "genero": genero,
            "titulo": titulo,
            "status": status,
            "elapsed_s": round(time.time() - t0, 2),
            "steps_s": _stage_timers,
            "counters": _counters,
            "events": _stage_events,
            "video_duration_s": round(float(final_dur or 0), 2),
        }
        if video_path:
            record["video_path"] = str(video_path)
        if extra:
            record["extra"] = extra
        _f = Path(__file__).resolve().parent.parent / "logs" / "pipeline_metrics.jsonl"
        try:
            _f.parent.mkdir(parents=True, exist_ok=True)
            with open(_f, "a", encoding="utf-8") as __fh:
                __fh.write(_json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # -- PROFILE DO CANAL (feature exclusiva) --
    try:
        profile = canal_profiles.get_profile()
        log(f"Perfil de Canal Ativo: {profile['nome']}")
    except Exception:
        profile = None

    if preset:
        _apply_preset(preset)

    n_cenas = n_cenas or int(os.environ.get("MAX_SCENES", str(MAX_SCENES_DEFAULT)))
    use_parallax = os.environ.get("PARALLAX", "1") == "1"
    use_panel_fx = os.environ.get("PANEL_FX", "1") == "1"
    use_elemental = os.environ.get("ELEMENTAL_TRANS", "1") == "1"
    # mascote desligada por padrao (16/10): no quadro ela cobria a legenda ("MIGU... SEMPRE CHEGAVA")
    use_mascote = os.environ.get("MASCOTE_OVERLAY", "0") == "1" and mascote_overlay is not None
    use_motion_dir = os.environ.get("MOTION_DIRECTOR", "0") == "1"
    qp = QUALITY.get(quality, QUALITY["med"])

    log("=" * 60)
    log("HISTORIAS EM FRAMES - Pipeline COMPLETO")
    log(f"  Genero: {genero}")
    log(f"  Tema: {tema or 'aleatorio'}")
    log(f"  Cenas: {n_cenas} | Variacoes: {variacoes}")
    log(f"  Parallax: {use_parallax} | Karaoke: True | Judge: True")
    log(f"  TTS: {os.environ.get('TTS_ENGINE', 'edge')} | PanelFX: {use_panel_fx}")
    log(f"  Elemental: {use_elemental} | Memes: 1")
    log(f"  Preset: {preset or 'none'} | Quality: {quality}")
    log("=" * 60)

    if dry_run:
        log("DRY RUN — nada será gerado")
        return None

    _check_command_files()

    # ─── STAGE 1: ROTEIRO ───────────────────────────────────────────────────
    log("")
    log("[1/10] ROTEIRO — gerando via Gemini...")
    _mt_stage("roteiro")

    import story_writer
    story = story_writer.generate_story(genero=genero, tema=tema, n_cenas=n_cenas)
    if not story or not story.get("cenas"):
        log("[X] Falha ao gerar roteiro")
        _mt_count("fail_roteiro")
        _mt_write(status="failed")
        return None

    titulo = titulo_override or story.get("titulo", f"Historia {genero}")
    cenas = story["cenas"][:n_cenas]
    story_id = f"{genero}_{hashlib.md5(titulo.encode()).hexdigest()[:10]}"

    log(f"  [OK] '{titulo}' — {len(cenas)} cenas")

    if narration and os.environ.get("ENSEMBLE_NARRATION", "0") == "1":
        try:
            cenas = narration._revisar_coerencia(cenas, titulo)
            log("  [OK] Coerência revisada (ensemble)")
        except Exception as e:
            log(f"  ! Ensemble falhou: {e}")

    # ─── STAGE 2: IMAGENS ───────────────────────────────────────────────────
    log("")
    log("[2/10] IMAGENS — gerando via OmniRoute/Pollinations...")
    _mt_stage("imagens")
    _check_command_files()

    import image_generator
    img_dir = image_generator.generate_images_for_story(
        story={"cenas": cenas}, story_id=story_id, n_variations=variacoes)

    if not img_dir or None in img_dir:
        # IMAGENS_INCOMPLETAS: o auto_producer reconhece e RETOMA esta mesma historia
        # depois (as imagens que sairam ficam no cache), sem fazer video pela metade.
        log("[X] IMAGENS_INCOMPLETAS — falhas na geração de imagens, abortando pipeline")
        _mt_count("fail_imagens")
        _mt_write(status="failed")
        return None

    imgs = img_dir[start_panel:]
    # Imagem nao-vertical (as antigas vinham 1024x1024) -> versao 9:16; sem isso os
    # efeitos esticavam a imagem na vertical.
    _n_antes = sum(1 for p in imgs if Path(image_generator.garantir_vertical(p)) != Path(p))
    imgs = [Path(image_generator.garantir_vertical(p)) for p in imgs]
    if _n_antes:
        log(f"  [9:16] {_n_antes} imagem(ns) nao-vertical(is) recortada(s) pra 9:16")
    if not imgs:
        log("! Nenhuma imagem encontrada")
        return None
        log("[X] Nenhuma imagem encontrada")
        return None

    log(f"  [OK] {len(imgs)} imagens em {img_dir}")

    # ─── STAGE 3: PRE-SCAN CENSURA ─────────────────────────────────────────
    censura_scores = {}
    if censura and censura_visual:
        log("")
        log("[3/10] CENSURA — pre-scan de imagens...")
        for img_path in imgs:
            try:
                score = censura_visual.detectar_score(str(img_path))
                if score and score > 0.3:
                    censura_scores[str(img_path)] = score
            except Exception:
                pass
        log(f"  [OK] {len(censura_scores)} imagens marcadas +18")
    else:
        log("")
        log("[3/10] CENSURA — skip (desabilitada)")

    # ─── STAGE 4: TTS PARALELO ──────────────────────────────────────────────
    log("")
    log("[4/10] TTS — gerando áudio em paralelo...")
    _mt_stage("tts")
    _check_command_files()

    NARRATION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    audio_files = {}
    tts_tasks = []

    # Curva de locutor (hipercool -> recapd -> aqui, 17/10; dono: "tipo narrador de futebol, aumentando a velocidade,
    # diminuindo e variando volume"): chegando nas cenas de impacto a voz acelera e sobe, depois respira.
    # NARRACAO_CURVA=0 desliga. A curva entra na chave do cache (o cache é por texto e vale pra todas as histórias).
    import narracao_curva
    textos_tts = [_clean_text_for_tts(c.get("narracao") or c.get("texto", "")) for c in cenas[:len(imgs)]]
    impactos = []
    if narracao_curva.ligado():
        try:
            impactos = narracao_curva.escolher_impactos(textos_tts)
            log(f"  curva de narração: impactos nas cenas {[k + 1 for k in impactos]} de {len(textos_tts)}")
        except Exception as e:  # noqa: BLE001
            log(f"  ! curva de narração indisponível ({type(e).__name__}) — voz plana")

    import voz_rodizio
    voz_clone = voz_rodizio.proxima(story_id)
    if voz_clone:
        os.environ["VOZ_CLONADA"] = voz_clone
        log(f"  voz clonada deste vídeo: {voz_clone} (base {voz_rodizio.BASE_EDGE})")
    else:
        os.environ.pop("VOZ_CLONADA", None)

    for i, cena in enumerate(cenas[:len(imgs)]):
        texto_clean = textos_tts[i]
        if not texto_clean:
            continue

        curva = narracao_curva.deltas(texto_clean, i, impactos, len(textos_tts)) if impactos else None
        cache_key = hashlib.md5((texto_clean + (f"|curva{curva}" if curva else "")
                                 + (f"|clone:{voz_clone}" if voz_clone else "")).encode()).hexdigest()
        cache_path = NARRATION_CACHE_DIR / f"{cache_key}.wav"

        if cache_path.exists() and cache_path.stat().st_size > 500:
            audio_files[i] = str(cache_path)
            continue

        persona = cena.get("persona", "Narrador")
        gender = cena.get("gender") or narrator_gender or _infer_gender_by_name(persona)
        tts_tasks.append((i, texto_clean, persona, gender, cache_path, curva))

    def _do_tts(task):
        idx, texto, persona, gender, out_path, curva = task
        voice = voz_rodizio.BASE_EDGE if voz_clone else edge_tts_engine.voice_for_persona(persona, gender=gender)
        # com clone, o edge grava a base ao lado e o lote RVC escreve out_path depois
        dst = out_path.with_name(out_path.stem + "_base.wav") if voz_clone else out_path
        try:
            rate = pitch = None
            if curva:  # sobre o perfil que o speak usaria (persona vazia), como no recapd
                perfil = edge_tts_engine._get_voice_profile(voice, "")
                rate, pitch = narracao_curva.absoluto(curva[0], curva[1], perfil["rate"], perfil["pitch"])
            edge_tts_engine.speak(texto, voice=voice, out_wav=str(dst), rate=rate, pitch=pitch)
            if dst.exists() and dst.stat().st_size > 500:
                if curva and not voz_clone:
                    narracao_curva.pos_processar(dst, curva[2], curva[3])
                return (idx, str(dst))
        except Exception as e:
            log(f"  ! TTS cena {idx} falhou: {e}")
        return (idx, None)

    workers = min(TTS_WORKERS, len(tts_tasks)) if tts_tasks else 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_do_tts, t): t for t in tts_tasks}
        for fut in as_completed(futures):
            idx, path = fut.result()
            if path:
                audio_files[idx] = path
                sz = Path(path).stat().st_size // 1024
                log(f"  [OK] cena {idx + 1}: {sz}KB")

    if voz_clone:
        tarefa = {t[0]: t for t in tts_tasks}
        bases = {i: p for i, p in audio_files.items() if i in tarefa}
        if bases:
            log(f"  clonando {len(bases)} falas com a voz de {voz_clone}...")
            pares = [(bases[i], tarefa[i][4]) for i in sorted(bases)]
            try:
                ok, fim = voz_rodizio.converter_lote(voz_clone, pares, TMP_DIR / f"clone_{story_id}.json")
            except Exception as e:  # noqa: BLE001
                ok, fim = False, f"{type(e).__name__}: {e}"
            if not ok:
                log(f"  ! clone falhou ({fim.strip()[-200:]}) — seguindo com a base edge nas que faltarem")
            for i in sorted(bases):
                base, saida, curva = Path(bases[i]), tarefa[i][4], tarefa[i][5]
                if saida.exists() and saida.stat().st_size > 500:
                    wj = Path(str(base) + ".words.json")
                    if wj.exists():  # RVC não muda o tempo: a legenda palavra a palavra continua valendo
                        shutil.copy2(wj, str(saida) + ".words.json")
                    if curva:
                        narracao_curva.pos_processar(saida, curva[2], curva[3])
                    audio_files[i] = str(saida)
                    base.unlink(missing_ok=True)
                    wj.unlink(missing_ok=True)
                elif curva:
                    narracao_curva.pos_processar(base, curva[2], curva[3])
            log(f"  [OK] {sum(1 for i in bases if audio_files[i] != bases[i])}/{len(bases)} falas clonadas")

    total_audio = len(audio_files)
    log(f"  [OK] {total_audio}/{len(cenas[:len(imgs)])} áudios gerados")

    if audio_only:
        marker = PROJECT_DIR / ".audio_ready"
        marker.write_text(f"{story_id}\n{total_audio} audios\n{titulo}")
        log(f"AUDIO-ONLY: cache preenchido. Marker: {marker}")
        return {"story_id": story_id, "titulo": titulo, "audio_count": total_audio}

    if total_audio == 0:
        log("[X] Nenhum áudio gerado — abortando")
        _mt_count("fail_tts")
        _mt_write(status="failed")
        return None

    # ─── STAGE 5: RENDER CLIPS ──────────────────────────────────────────────
    log("")
    log("[5/10] RENDER — montando clips com efeitos completos...")
    _mt_stage("render")
    _check_command_files()
    # Fila de render entre os projetos do PC (D:\video-fila): espera a vez antes da parte pesada
    # e segura ate o processo terminar. Fila fora do ar = segue sem esperar.
    try:
        sys.path.insert(0, r"D:\video-fila")
        import atexit
        import fila_render
        _vez = fila_render.vez("historias", f"{genero} {story_id}")
        _vez.__enter__()
        atexit.register(lambda: _vez.__exit__(None, None, None))
    except Exception as _e:  # noqa: BLE001
        log(f"  [fila_render] indisponivel ({_e}) — segue sem esperar")

    out_dir = VIDEOS_DIR / genero
    out_dir.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    clips = []
    last_meme_idx = -10
    nartrans_count = 0
    prev_md5 = None
    efx_mgr = EffectsManager()
    clip_durations = []
    # DESYNC-LEGENDA FIX: mapeia cada FALA à sua posição REAL em clips[]. Memes e
    # transições narrativas também entram em clips[], então a legenda não pode
    # assumir mapeamento 1:1 com as falas — um meme no meio desloca todas as
    # legendas seguintes. Guardamos (idx_em_clips, texto, dur) por fala e depois
    # usamos as posições REAIS que o concat calcula (_CLIP_ABS_STARTS).
    speech_subs = []
    # audio de cada fala, alinhado com speech_subs (None no flash): a legenda le
    # o tempo real de cada palavra do sidecar .words.json desse audio.
    speech_audio = []
    speech_cena = []    # cena de cada fala (sfx_hint e afins pro audio final)
    _memes_usados = set()  # memes ja usados neste video (nao repete)

    # ── Validação de TTS: rejeita áudio < 1KB que crasha downstream ──────────
    _tts_ok = {}
    for i in list(audio_files.keys()):
        ap = audio_files[i]
        if Path(ap).exists() and Path(ap).stat().st_size < 1024:
            log(f"  [!] TTS cena {i} rejeitado (audio {Path(ap).stat().st_size}B < 1KB) — regenerando")
            try:
                Path(ap).unlink()
            except Exception:
                pass
            del audio_files[i]
        else:
            _tts_ok[i] = ap
    audio_files = _tts_ok
    log(f"  TTS validado: {len(audio_files)}/{len(imgs)} áudios OK")

    # Microcortes (dona 22/10) — LIGADO (dona aprovou o teste A/B 23/10); HISTORIAS_MICROCORTES=0 desliga.
    # Antes do diretor de cena (ele le a duracao dos audios) e do render (o clip dura o que o audio dura).
    if os.environ.get("HISTORIAS_MICROCORTES", "1") == "1" and audio_files:
        audio_files = _microcortes_falas(audio_files, story_id)

    # ══ DIRETOR DE CENA: plano de movimento do video inteiro (diretor_cena.py) ═══
    plano_cena = None
    if use_panel_fx and diretor_cena.ativo():
        try:
            _durs = [(_ffprobe_duration(audio_files[i]) if i in audio_files else 0.8)
                     for i in range(len(imgs))]
            plano_cena = diretor_cena.planejar(cenas[:len(imgs)], genero, seed=story_id, duracoes=_durs)
            log(f"  [diretor] {diretor_cena.resumo(plano_cena)}")
        except Exception as e:
            log(f"  [diretor] falhou ({e}) — usando a escolha antiga por cena")
            plano_cena = None

    # ══ PARALLEL CLIPS (ThreadPoolExecutor) ══════════════════════════════════════
    if _RENDER_PARALLEL and len(imgs) > 2:
        log(f"  Render paralelo: {_CLIP_WORKERS} workers para {len(imgs)} clips")
        _cmd_skipped = False

        def _render_one_clip(idx_img):
            """Renderiza UM clip e devolve dict com resultado. Thread-safe."""
            nonlocal _cmd_skipped
            if _cmd_skipped:
                return None
            # Mesmo controle do render em serie. Aqui so marca e para: sys.exit
            # numa thread nao encerra o processo; o STOP e aplicado pelo
            # _check_command_files() da thread principal logo apos o render.
            if COMMAND_SKIP.exists() or COMMAND_STOP.exists():
                _cmd_skipped = True
                log(f"  SKIP/STOP detectado no clip {idx_img}")
                return None
            img_path = imgs[idx_img]
            img_str = str(img_path)
            cena = cenas[idx_img] if idx_img < len(cenas) else {}
            texto = cena.get("narracao") or cena.get("texto", "")

            # Flash clip: sem áudio -> clip rápido 0.8s
            if idx_img not in audio_files:
                flash_out = TMP_DIR / f"clip_{idx_img:03d}_flash.mp4"
                try:
                    mv = efx_mgr.next_movement()
                    subprocess.run([
                        "ffmpeg", "-y", "-loop", "1", "-i", img_str,
                        "-t", "0.8",
                        "-vf", f"scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:-1:-1,fps=25,{mv}",
                        "-c:v", "libx264", "-crf", "23", "-preset", "fast", "-an", str(flash_out)
                    ], capture_output=True, timeout=15)
                    if flash_out.exists() and flash_out.stat().st_size > 2000:
                        return {"kind": "flash", "path": str(flash_out),
                                "dur": 0.8, "idx": idx_img, "texto": texto, "cena": cena}
                except Exception:
                    pass
                return None

            audio_path = audio_files[idx_img]
            audio_dur = _ffprobe_duration(audio_path)
            if audio_dur < 0.5:
                return None

            clip_out = TMP_DIR / f"clip_{idx_img:03d}.mp4"
            clip_ok = False
            fx_name = None
            fx_tags = []   # efeitos que de fato sairam neste clip (vai pro log)
            plano = plano_cena[idx_img] if plano_cena and idx_img < len(plano_cena) else None

            # DIRETOR DE CENA: efeito planejado + alternativas. Transicao (FX2) entra
            # com a imagem ANTERIOR e revela a atual; os demais usam a atual (img2 =
            # proxima, so pros efeitos que pedem 2a imagem).
            if plano:
                for _fx in [plano["fx"]] + list(plano["alternativas"]):
                    _usa_ant = _fx in panel_effects.FX2
                    if _usa_ant and idx_img == 0:
                        continue
                    _base = str(imgs[idx_img - 1]) if _usa_ant else img_str
                    _img2 = img_str if _usa_ant else (
                        str(imgs[idx_img + 1]) if idx_img + 1 < len(imgs) else None)
                    try:
                        if panel_effects.build_effect_clip(
                                _base, audio_path, str(clip_out), fx_name=_fx,
                                duration=audio_dur, img2=_img2) and _clip_saudavel(clip_out):
                            clip_ok = True
                            fx_tags.append(_fx)
                            panel_effects._record(_fx)
                            break
                    except Exception:
                        pass

            # Motion Director
            if not clip_ok and use_motion_dir:
                try:
                    md = motion_director.decidir_efeito(
                        img_str, texto=texto, dur=audio_dur,
                        is_sensual=(str(img_path) in censura_scores),
                        tem_balao=bool(cena.get("balao")),
                        troca_cena=(idx_img > 0 and cena.get("troca_cena", False)),
                        prev_md5=None)
                    if md and md.get("efeito"):
                        fx_name = md["efeito"]
                except Exception:
                    pass

            # RECORTE DE PERSONAGEM tem PRIORIDADE (escolha da usuária): tenta recortar o
            # personagem e animá-lo separado do fundo. Se a cena não tiver personagem
            # recortável, build_cutout_clip devolve False e cai no parallax/panel abaixo.
            # (So sem plano do diretor: com plano, o recorte ja entra na dose certa.)
            if not clip_ok and not plano and use_panel_fx:
                _cut = panel_effects.pick_cutout()
                if _cut:
                    try:
                        if panel_effects.build_effect_clip(
                            img_str, audio_path, str(clip_out),
                            fx_name=_cut, duration=audio_dur) and _clip_saudavel(clip_out):
                            clip_ok = True
                            fx_tags.append(_cut)
                            panel_effects._record(_cut)
                    except Exception:
                        pass

            # Parallax 2.5D (fallback quando não houve recorte)
            vale_px = panel_classifier.vale_parallax(img_str) if use_parallax else False
            if not clip_ok and vale_px and use_parallax:
                _force = os.environ.get("PARALLAX_FORCE", "0") == "1"
                _ondemand = os.environ.get("PARALLAX_ONDEMAND", "0") == "1"
                try:
                    _md5_pe = parallax_engine._md5_file(img_str)
                    _cached = (parallax_engine._MF_CACHE / f"{_md5_pe}.png").exists()
                except Exception:
                    _cached = False
                if _force or _cached or _ondemand:
                    try:
                        _mv = parallax_engine.move_for_mood(cena.get("mood"), idx=idx_img)
                        _pok = parallax_engine.build_parallax_clip(
                            img_str, audio_path, str(clip_out),
                            W=_PW, H=_PH, fps=_PFPS, move=_mv,
                            terror=(genero == "terror"))
                        if _pok and _clip_saudavel(clip_out):
                            clip_ok = True
                            fx_tags.append("parallax")
                    except Exception:
                        pass

            # Panel Effects (fallback: efeito de câmera/zoom sem recorte)
            if not clip_ok and use_panel_fx:
                chosen_fx = fx_name or panel_effects.pick_effect(texto)
                if chosen_fx:
                    try:
                        panel_effects.build_effect_clip(
                            img_str, audio_path, str(clip_out),
                            fx_name=chosen_fx, duration=audio_dur)
                        if _clip_saudavel(clip_out):
                            clip_ok = True
                            fx_tags.append(chosen_fx)
                    except Exception:
                        pass

            # Ken Burns via PC2 worker
            if not clip_ok and os.environ.get("USE_PC2_WORKER", "0") == "1":
                try:
                    import render_worker_client as _rwc
                    if _rwc.is_online():
                        _ok = _rwc.render_ken_burns_clip(
                            img_str, audio_path, str(clip_out), dur=audio_dur)
                        if _ok and _clip_saudavel(clip_out):
                            clip_ok = True
                except Exception:
                    pass

            # Ken Burns local (fallback, até 3 tentativas)
            if not clip_ok:
                for _tent in range(3):
                    build_clip(img_str, audio_path, str(clip_out), idx_img, efx_mgr,
                               duration=audio_dur, mood=cena.get("mood"), narr_text=texto)
                    if _clip_saudavel(clip_out):
                        clip_ok = True
                        fx_tags.append("kenburns")
                        break
                    if _tent < 2:
                        _esperar_ram(min_gb=1.8, timeout_s=90)

            if not clip_ok:
                return None

            # Camera shake. (Antes chamava build_clip_with_shake(clip, out), que espera
            # IMAGEM + 5 argumentos: dava TypeError engolido e o tremor nunca saia.)
            if is_impact_panel(texto) or is_tension_panel(texto):
                shake_out = TMP_DIR / f"clip_{idx_img:03d}_shake.mp4"
                forte = is_impact_panel(texto)
                if shake_clip(str(clip_out), str(shake_out),
                              intensity=14 if forte else 7,
                              decay_s=0.9 if forte else 2.5):
                    shutil.move(str(shake_out), str(clip_out))
                    fx_tags.append("shake" if forte else "tremor")

            # Overlay atmosférico
            clip_mood = detect_mood_from_text(texto)
            overlay_video = overlay_para_cena(  # pelo que a cena descreve, nao so o humor
                f"{texto} {cena.get('image_prompt', '')}", clip_mood)
            if overlay_video:
                ov_out = TMP_DIR / f"clip_{idx_img:03d}_ov.mp4"
                clip_dur_ov = _ffprobe_duration(str(clip_out))
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", str(clip_out),
                        "-stream_loop", "-1", "-i", overlay_video,
                        "-filter_complex", "[1:v]format=rgba,colorchannelmixer=aa=0.3[ov];[0:v][ov]overlay=0:0",
                        "-map", "0:a?", "-c:a", "copy", "-t", f"{clip_dur_ov:.3f}", str(ov_out)
                    ], capture_output=True, timeout=30)
                    if ov_out.exists() and ov_out.stat().st_size > 5000:
                        shutil.move(str(ov_out), str(clip_out))
                        fx_tags.append("overlay")
                except Exception:
                    pass

            # Rasgo (divisoria do manhwa-react) no fim do clip, entrando na proxima imagem
            if plano and plano.get("rasgo_fim") and idx_img + 1 < len(imgs):
                rasgo_out = TMP_DIR / f"clip_{idx_img:03d}_rasgo.mp4"
                if fx_divisoria.aplicar_rasgo(str(clip_out), str(imgs[idx_img + 1]),
                                              str(rasgo_out), genero=genero):
                    shutil.move(str(rasgo_out), str(clip_out))
                    fx_tags.append("rasgo")

            ffprobe_dur = _ffprobe_duration(str(clip_out))
            return {"kind": "main", "path": str(clip_out), "dur": ffprobe_dur,
                    "idx": idx_img, "texto": texto, "cena": cena, "fx": fx_tags}

        # Submit todos os clips em paralelo
        _pending = list(range(len(imgs)))
        with ThreadPoolExecutor(max_workers=_CLIP_WORKERS) as pool:
            futures = {pool.submit(_render_one_clip, i): i for i in _pending}
            _results = []
            for fut in as_completed(futures):
                r = fut.result()
                if r is not None:
                    _results.append(r)
                else:
                    _results.append({"kind": "skip", "idx": futures[fut]})

        # Rebuild state em ordem original (classificação)
        _memes = []
        _nartrans = []
        for r in sorted(_results, key=lambda x: x["idx"]):
            if r["kind"] == "flash":
                clips.append(r["path"])
                clip_durations.append(r["dur"])
                _speech_idx = len(clips) - 1
                speech_subs.append((_speech_idx, "", 0))
                speech_audio.append(None)
                speech_cena.append({})
                log(f"  + clip {r['idx'] + 1} (flash 0.8s)")
            elif r["kind"] == "main":
                idx = r["idx"]
                texto = r["texto"]
                cena = r["cena"]
                clip_out_path = r["path"]
                log(f"  + clip {idx + 1}: {' + '.join(r.get('fx') or ['?'])} ({r['dur']:.1f}s)")

                _speech_idx = len(clips)
                clips.append(clip_out_path)
                clip_durations.append(r["dur"])
                audio_path = audio_files[idx]
                speech_subs.append((_speech_idx, _clean_text_for_tts(texto),
                                    _ffprobe_duration(audio_path)))
                speech_audio.append(audio_path)
                speech_cena.append(cena)

                clip_mood = detect_mood_from_text(texto)
                meme = _maybe_meme(texto, idx, last_meme_idx, clip_mood, genero, _memes_usados, story_id)
                if meme:
                    meme_out = TMP_DIR / f"meme_{idx:03d}.mp4"
                    try:
                        # (antes: build_meme_clip(meme_sfx, meme_out) com os argumentos
                        # trocados -> falhava sempre e nenhum meme entrava)
                        if build_meme_clip(str(meme_out), mood=clip_mood, meme_video=meme["file"],
                                           sfx_file=meme["sfx"]) and meme_out.exists():
                            _memes.append((idx, str(meme_out)))
                            _memes_usados.add(meme["file"])
                            last_meme_idx = idx
                            log(f"  + meme apos clip {idx + 1}: {meme['desc'][:60]}")
                    except Exception:
                        pass

                _nar_max = int(os.environ.get("NARRATIVE_TRANS_MAX", "1"))
                if (os.environ.get("NARRATIVE_TRANS", "1") == "1" and idx + 1 < len(cenas)
                        and nartrans_count < _nar_max and idx >= 1):
                    next_texto = cenas[idx + 1].get("narracao") or cenas[idx + 1].get("texto", "")
                    curr_mood = detect_mood_from_text(texto)
                    next_mood = detect_mood_from_text(next_texto)
                    _MOOD_GROUPS = {
                        "action": "intense", "tense": "intense", "impact": "intense",
                        "sad": "emotional", "romantic": "emotional",
                        "calm": "peaceful", "happy": "peaceful", "neutral": "neutral",
                    }
                    g1 = _MOOD_GROUPS.get(curr_mood, curr_mood)
                    g2 = _MOOD_GROUPS.get(next_mood, next_mood)
                    if g1 != g2 and g1 != "neutral" and g2 != "neutral" and idx - last_meme_idx > 2:
                        from fx_clips import build_narrative_transition, NARRATIVE_TRANSITIONS
                        import random as _rnd
                        trans_text = diretor_cena.texto_virada(cenas[idx + 1])
                        nar_out = TMP_DIR / f"nartrans_{idx:03d}.mp4"
                        try:
                            if trans_text and build_narrative_transition(trans_text, str(nar_out)):
                                _nartrans.append((idx, str(nar_out)))
                                nartrans_count += 1
                                log(f"  + transicao narrativa: \"{trans_text}\"")
                        except Exception:
                            pass

                try:
                    prev_md5 = hashlib.md5(imgs[idx].read_bytes()).hexdigest()
                except Exception:
                    prev_md5 = None

        # Insere memes e transições narrativas em ordem
        for _midx, _mpath in sorted(_memes, key=lambda x: x[0]):
            clips.append(_mpath)
            clip_durations.append(_ffprobe_duration(_mpath))
            last_meme_idx = _midx
        for _nidx, _npath in sorted(_nartrans, key=lambda x: x[0]):
            clips.append(_npath)
            clip_durations.append(_ffprobe_duration(_npath))

    else:
        # ── SEQUENTIAL (fallback) ──────────────────────────────────────────────
        for i, img_path in enumerate(imgs):
            if _check_command_files():
                log(f"  SKIP detectado no clip {i}")
                break

            img_str = str(img_path)
            cena = cenas[i] if i < len(cenas) else {}
            texto = cena.get("narracao") or cena.get("texto", "")

            # Flash clip: painel sem áudio vira clip rápido de 0.8s
            if i not in audio_files:
                flash_out = TMP_DIR / f"clip_{i:03d}_flash.mp4"
                try:
                    movement = efx_mgr.next_movement()
                    subprocess.run([
                        "ffmpeg", "-y", "-loop", "1", "-i", img_str,
                        "-t", "0.8", "-vf", f"scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:-1:-1,fps=25,{movement}",
                        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
                        "-an", str(flash_out)
                    ], capture_output=True, timeout=15)
                    if flash_out.exists() and flash_out.stat().st_size > 2000:
                        clips.append(str(flash_out))
                        clip_durations.append(0.8)
                        log(f"  + clip {i + 1} (flash 0.8s)")
                except Exception:
                    pass
                continue

            audio_path = audio_files[i]
            audio_dur = _ffprobe_duration(audio_path)
            if audio_dur < 0.5:
                continue

            clip_out = TMP_DIR / f"clip_{i:03d}.mp4"
            cena = cenas[i] if i < len(cenas) else {}
            texto = cena.get("narracao") or cena.get("texto", "")
            img_str = str(img_path)

            # Panel Classifier: decide parallax vs panel_fx
            vale_px = panel_classifier.vale_parallax(img_str) if use_parallax else False

            # Motion Director: decide efeito específico
            md_decisao = None
            if use_motion_dir:
                md_decisao = motion_director.decidir_efeito(
                    img_str, texto=texto, dur=audio_dur,
                    is_sensual=(str(img_path) in censura_scores),
                    tem_balao=bool(cena.get("balao")),
                    troca_cena=(i > 0 and cena.get("troca_cena", False)),
                    prev_md5=prev_md5)

            # Roteamento de efeito
            fx_name = None
            if md_decisao and md_decisao.get("efeito"):
                fx_name = md_decisao["efeito"]

            clip_ok = False

            # PARALLAX 2.5D (movimento real via depth) — MESMO padrão do hiper-fix
            # (bin/hiper-pipeline.py): é o efeito que "corta o personagem e ele se mexe".
            # Usa depth-maps CACHEADOS (_MF_CACHE, populado por worker/render anterior);
            # se não houver cache, só gera na hora com PARALLAX_ONDEMAND=1. Assim o depth
            # pesado não trava o render quando o cache já existe. Passa W/H/fps explícitos
            # (igual hiper-fix). Fallback -> panel_fx/Ken Burns. PARALLAX_FORCE=1 ignora cache.
            # PRIORIDADE igual hiper-fix: NÃO checar fx_name aqui. O parallax 2.5D roda
            # primeiro (é o efeito principal); a decisão do Motion Director (fx_name) é só
            # do FALLBACK panel_fx. Antes tinha `not fx_name`, o que fazia o preset final
            # (MOTION_DIRECTOR=1) pular o parallax em TODO clip -> tudo virava kenburns.
            # RECORTE DE PERSONAGEM tem PRIORIDADE (escolha da usuária). Tenta antes do
            # parallax; se não houver personagem recortável, cai no parallax/panel abaixo.
            if use_panel_fx:
                _cut = panel_effects.pick_cutout()
                if _cut:
                    try:
                        if panel_effects.build_effect_clip(
                            img_str, audio_path, str(clip_out),
                            fx_name=_cut, duration=audio_dur) and _clip_saudavel(clip_out):
                            clip_ok = True
                            panel_effects._record(_cut)
                            log(f"  + clip {i + 1} (recorte personagem: {_cut})")
                    except Exception:
                        pass

            if not clip_ok and vale_px and use_parallax:
                _force = os.environ.get("PARALLAX_FORCE", "0") == "1"
                _ondemand = os.environ.get("PARALLAX_ONDEMAND", "0") == "1"
                try:
                    _md5 = parallax_engine._md5_file(img_str)
                    _cached = (parallax_engine._MF_CACHE / f"{_md5}.png").exists()
                except Exception:
                    _cached = False
                if _force or _cached or _ondemand:
                    try:
                        _mv = parallax_engine.move_for_mood(cena.get("mood"), idx=i)
                        _pok = parallax_engine.build_parallax_clip(
                            img_str, audio_path, str(clip_out),
                            W=_PW, H=_PH, fps=_PFPS, move=_mv,
                            terror=(genero == "terror"))
                        if _pok and _clip_saudavel(clip_out):
                            clip_ok = True
                            log(f"  + clip {i + 1} (parallax 2.5D: {_mv})")
                        else:
                            log(f"  ! clip {i + 1}: parallax nao gerou/corrompido (fallback)")
                    except Exception as _pe:
                        log(f"  ! clip {i + 1}: parallax falhou {type(_pe).__name__} (fallback)")

            # Panel Effects (43+ efeitos)
            if not clip_ok and use_panel_fx:
                chosen_fx = fx_name or panel_effects.pick_effect(texto)
                if chosen_fx:
                    try:
                        panel_effects.build_effect_clip(
                            img_str, audio_path, str(clip_out),
                            fx_name=chosen_fx, duration=audio_dur)
                        if _clip_saudavel(clip_out):
                            clip_ok = True
                            log(f"  + clip {i + 1} (panel_fx: {chosen_fx})")
                    except Exception:
                        pass

            # Fallback: build_clip padrão (Ken Burns simples). Assinatura real:
            # build_clip(img, audio, out, panel_idx, effects_mgr, duration=, mood=, narr_text=).
            # É aqui que parallax/word_pop (features novas) são aplicados internamente.
            # Ken Burns é o último recurso e o mais leve. Se ele TAMBÉM sair corrompido,
            # a causa é pico de RAM (outro render competindo), não o efeito — então
            # esperamos a memória liberar e tentamos de novo, em vez de perder o clip
            # (perder 1 clip encurta o vídeo e desloca legendas). Até 3 tentativas.
            if not clip_ok:
                for _tent in range(3):
                    build_clip(img_str, audio_path, str(clip_out), i, efx_mgr,
                               duration=audio_dur, mood=cena.get("mood"), narr_text=texto)
                    if _clip_saudavel(clip_out):
                        clip_ok = True
                        log(f"  + clip {i + 1} (kenburns)")
                        break
                    if _tent < 2:
                        _esperar_ram(min_gb=1.8, timeout_s=90)
                        log(f"  … clip {i + 1}: retry kenburns após esperar RAM ({_tent + 2}/3)")
                if not clip_ok:
                    log(f"  ! clip {i + 1}: kenburns falhou 3x (RAM crítica) — pulando clip")

            if not clip_ok:
                continue

            # Camera shake (impacto/tensão)
            if is_impact_panel(texto) or is_tension_panel(texto):
                shake_out = TMP_DIR / f"clip_{i:03d}_shake.mp4"
                try:
                    build_clip_with_shake(str(clip_out), str(shake_out))
                    if shake_out.exists() and shake_out.stat().st_size > 5000:
                        shutil.move(str(shake_out), str(clip_out))
                except Exception:
                    pass

            # Overlay atmosférico (chuva/neve/faíscas — 30% chance interna)
            clip_mood = detect_mood_from_text(texto)
            overlay_video = overlay_para_cena(  # pelo que a cena descreve, nao so o humor
                f"{texto} {cena.get('image_prompt', '')}", clip_mood)
            if overlay_video:
                ov_out = TMP_DIR / f"clip_{i:03d}_ov.mp4"
                # DESYNC FIX: os overlays têm só 3s (speedlines 1.5s). Sem -stream_loop -1
                # no input do overlay + shortest=1, o clip inteiro era TRUNCADO na duração
                # do overlay (3s) enquanto o áudio ficava com o tamanho original (~7s),
                # criando o desync que mandava o vídeo pra quarentena. Agora o overlay
                # dá loop e o output é travado na duração do clip base (-t).
                clip_dur_ov = _ffprobe_duration(str(clip_out))
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", str(clip_out),
                        "-stream_loop", "-1", "-i", overlay_video,
                        "-filter_complex", "[1:v]format=rgba,colorchannelmixer=aa=0.3[ov];[0:v][ov]overlay=0:0",
                        "-map", "0:a?", "-c:a", "copy", "-t", f"{clip_dur_ov:.3f}", str(ov_out)
                    ], capture_output=True, timeout=30)
                    if ov_out.exists() and ov_out.stat().st_size > 5000:
                        shutil.move(str(ov_out), str(clip_out))
                except Exception:
                    pass

            # posição REAL desta fala em clips[] = índice atual (antes do append).
            _speech_idx = len(clips)
            clips.append(str(clip_out))
            clip_durations.append(_ffprobe_duration(str(clip_out)))
            # registra a fala p/ legenda (texto limpo + duração do ÁUDIO, não do clip).
            speech_subs.append((_speech_idx, _clean_text_for_tts(texto),
                                _ffprobe_duration(audio_path)))
            speech_audio.append(audio_path)
            speech_cena.append(cena)

            # Meme insert
            meme = _maybe_meme(texto, i, last_meme_idx, clip_mood, genero, _memes_usados, story_id)
            if meme:
                meme_out = TMP_DIR / f"meme_{i:03d}.mp4"
                try:
                    if build_meme_clip(str(meme_out), mood=clip_mood, meme_video=meme["file"],
                                       sfx_file=meme["sfx"]) and meme_out.exists():
                        _memes_usados.add(meme["file"])
                        clips.append(str(meme_out))
                        clip_durations.append(_ffprobe_duration(str(meme_out)))
                        last_meme_idx = i
                except Exception:
                    pass

            # Narrative transition (tela de texto entre cenas de clima MUITO diferente).
            # LIMITE: no máximo NARRATIVE_TRANS_MAX por vídeo (default 1). Antes disparava
            # a cada troca de mood -> a tela escura de texto aparecia quase toda hora e
            # cansava. Agora só entra na 1ª virada forte de clima, como respiro pontual.
            _nar_max = int(os.environ.get("NARRATIVE_TRANS_MAX", "1"))
            if (os.environ.get("NARRATIVE_TRANS", "1") == "1" and i + 1 < len(cenas)
                    and nartrans_count < _nar_max and i >= 1):
                next_texto = cenas[i + 1].get("narracao") or cenas[i + 1].get("texto", "")
                curr_mood = detect_mood_from_text(texto)
                next_mood = detect_mood_from_text(next_texto)
                # Inserir transicao narrativa se mood muda drasticamente
                _MOOD_GROUPS = {
                    "action": "intense", "tense": "intense", "impact": "intense",
                    "sad": "emotional", "romantic": "emotional",
                    "calm": "peaceful", "happy": "peaceful",
                    "neutral": "neutral",
                }
                g1 = _MOOD_GROUPS.get(curr_mood, curr_mood)
                g2 = _MOOD_GROUPS.get(next_mood, next_mood)
                if g1 != g2 and g1 != "neutral" and g2 != "neutral" and i - last_meme_idx > 2:
                    from fx_clips import build_narrative_transition, NARRATIVE_TRANSITIONS
                    import random as _rnd
                    trans_text = diretor_cena.texto_virada(cenas[i + 1])
                    nar_out = TMP_DIR / f"nartrans_{i:03d}.mp4"
                    try:
                        if trans_text and build_narrative_transition(trans_text, str(nar_out)):
                            clips.append(str(nar_out))
                            clip_durations.append(_ffprobe_duration(str(nar_out)))
                            nartrans_count += 1
                            log(f"  + transicao narrativa: \"{trans_text}\"")
                    except Exception:
                        pass

            # Track md5 for Motion Director
            try:
                prev_md5 = hashlib.md5(img_path.read_bytes()).hexdigest()
            except Exception:
                prev_md5 = None

    log(f"  = {len(clips)}/{len(imgs)} clips renderizados")

    if not clips:
        log("[X] Nenhum clip renderizado — abortando")
        _mt_count("fail_render")
        _mt_write(status="failed")
        return None

    # ─── STAGE 6: INTRO + OUTRO ─────────────────────────────────────────────
    log("")
    log("[6/10] BRANDING — cold open + intro + outro...")
    _mt_stage("branding")

    cold_open_clip = None
    intro_clip = None
    outro_clip = None
    intro_dur = 0.0
    gancho_txt = ""

    if not no_branding:
        # Cold Open (3s teaser antes do intro)
        if os.environ.get("COLD_OPEN", "0") == "1" and imgs:
            try:
                import community_hooks
                hook_text = community_hooks.generate_shorts_hook(cenas, genero)
                if hook_text:
                    cold_open_out = TMP_DIR / "cold_open.mp4"
                    from fx_clips import build_cold_open
                    # Usar a imagem mais "dramatica" (ultima ou do meio)
                    drama_img = str(imgs[len(imgs) // 2]) if len(imgs) > 3 else str(imgs[0])
                    if build_cold_open(hook_text, drama_img, str(cold_open_out), duration=3.0):
                        cold_open_clip = str(cold_open_out)
                        log(f"  + Cold open: \"{hook_text[:40]}\"")
            except Exception as e:
                log(f"  ! Cold open falhou: {e}")

        # titulo inteiro (o PNG quebra em linhas); antes cortava em 40 caracteres no
        # meio da frase ("Ele perdeu os movimentos mas pintou seu")
        _tit = titulo if len(titulo) <= 70 else titulo[:70].rsplit(" ", 1)[0] + "..."
        # Short comeca DIRETO na 1a cena com a narracao e o titulo como gancho no topo (padrao do react).
        # A intro antiga (tela preta + painel borrado a 40% + titulo, ~1,8 s sem fala) fica so com HIST_INTRO=1:
        # no quadro de 16/10 o 1o segundo era preto/escuro — e o segundo em que o Short e pulado.
        gancho_txt = _tit
        if os.environ.get("HIST_INTRO", "0") == "1":
            intro_out = TMP_DIR / "intro.mp4"
            try:
                build_intro_clip(_tit, str(imgs[0]) if imgs else None, str(intro_out))
                if intro_out.exists():
                    intro_clip = str(intro_out)
                    intro_dur = _ffprobe_duration(intro_clip)
                    gancho_txt = ""
                    log(f"  + Intro ({_tit})")
            except Exception as e:
                log(f"  ! Intro falhou: {e}")

        outro_out = TMP_DIR / "outro.mp4"
        try:
            # frase de assets/cta_frases.json (antes: "PROXIMO CAPITULO EM BREVE" fixo,
            # sem sentido em historia que fecha no proprio video)
            _cta = frase_cta(seed=story_id)
            build_outro_clip(str(outro_out), linha3=_cta)
            if outro_out.exists():
                outro_clip = str(outro_out)
                log(f"  + Outro CTA: \"{_cta}\"")
        except Exception as e:
            log(f"  ! Outro falhou: {e}")

    # ─── STAGE 7: CONCAT + ELEMENTAL + TRILHA ───────────────────────────────
    log("")
    log("[7/10] CONCAT — montando video final...")
    _mt_stage("concat")
    _check_command_files()

    all_clips = []
    if cold_open_clip:
        all_clips.append(cold_open_clip)
    if intro_clip:
        all_clips.append(intro_clip)
    # nº de clips ANTES das cenas (cold_open+intro) — desloca o índice das falas
    # em clips[] p/ o índice real em all_clips[] (usado no timing da legenda).
    _prefix_clips = len(all_clips)
    all_clips.extend(clips)
    if outro_clip:
        all_clips.append(outro_clip)

    # Elemental transitions entre clips
    if use_elemental and len(all_clips) > 1:
        try:
            trans_list = elemental_transitions.pick_transitions(len(all_clips) - 1)
            if trans_list:
                log(f"  + {len(trans_list)} transições elementais")
        except Exception:
            trans_list = None
    else:
        trans_list = None

    # Concat com xfade
    concat_out = TMP_DIR / "concat_raw.mp4"
    try:
        concat_with_xfade(all_clips, str(concat_out))
    except Exception as e:
        log(f"  ! xfade falhou: {e}, tentando concat simples...")
        flist = TMP_DIR / "concat_list.txt"
        flist.write_text("\n".join(f"file '{c}'" for c in all_clips), encoding="utf-8")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(flist),
            "-c:v", "libx264", "-crf", qp["crf"], "-preset", qp["preset"],
            "-c:a", "aac", "-b:a", "192k", str(concat_out)
        ], capture_output=True, timeout=600)

    if not concat_out.exists():
        log("[X] Concat falhou — abortando")
        return None
    def _dbg_streams(p):
        import subprocess as _sp
        def _s(sel):
            r = _sp.run(["ffprobe","-v","error","-select_streams",sel,"-show_entries","stream=duration,nb_frames","-of","csv=p=0",str(p)],capture_output=True,text=True)
            return r.stdout.strip().replace("\n"," ")
        return f"vstream=[{_s('v:0')}] astream=[{_s('a:0')}]"
    log(f"  [DBG] pos-concat: {_dbg_streams(concat_out)} | sum_clips_esperado")

    # Trilha sonora dinâmica (no-copyright) — fx_music.add_dynamic_music (16/10, seleção do hipercool):
    # clima por trecho (trechos seguidos do mesmo clima = uma faixa), faixa nivelada em -28 LUFS que abaixa
    # sob a narração, crossfade na troca, sem blocklist/lixo/faixa curta e sem repetir os últimos vídeos.
    # Antes: sorteio cru do moods.json, volume fixo 0.12 sem ducking e amix que derrubava a narração 6 dB.
    trilha_out = TMP_DIR / "with_trilha.mp4"
    try:
        import fx_music
        trilhas_dir = PROJECT_DIR / "workspace" / "assets" / "trilhas"
        locs = [{"text": c.get("narracao", c.get("texto", ""))} for c in cenas[:len(imgs)]]
        bloco = max(1, -(-len(locs) // 4))  # até 4 blocos de clima, como antes
        fx_music.add_dynamic_music(str(concat_out), locs, str(trilha_out), trilhas_dir,
                                   block_size=bloco, no_copyright=True)
        if trilha_out.exists() and trilha_out.stat().st_size > 10000:
            shutil.move(str(trilha_out), str(concat_out))
            log(f"  + Trilha dinamica: {fx_music.ULTIMAS_FAIXAS} [DBG pos-trilha v={_ffprobe_duration(str(concat_out)):.1f}s]")
        else:
            log("  ! Sem trilha (mix nao gerou arquivo)")
    except Exception as e:
        log(f"  ! Trilha falhou: {e}")

    # ─── STAGE 8: LEGENDAS + WATERMARK ──────────────────────────────────────
    log("")
    log("[8/10] POS-PROCESSAMENTO...")
    _mt_stage("pos_process")

    # ── Legendas: usar as posições REAIS dos clips (corrige desync) ──────────
    # O concat grava em fx_clips._CLIP_ABS_STARTS o instante REAL de início de
    # cada clip no vídeo final (já considerando gaps, xfade overlap e memes/
    # transições intercalados). Casamos cada FALA (speech_subs) com a posição do
    # seu clip em all_clips = _prefix_clips + idx_em_clips. Assim um meme no meio
    # não desloca mais as legendas seguintes.
    import fx_clips as _fxc
    real_starts = list(getattr(_fxc, "_CLIP_ABS_STARTS", []) or [])
    subtitle_entries = []
    subtitle_audio = []
    subtitle_cenas = []
    offsets = []
    if real_starts and speech_subs and len(real_starts) >= _prefix_clips + len(clips):
        for k, (idx_in_clips, texto, dur) in enumerate(speech_subs):
            pos = _prefix_clips + idx_in_clips
            if pos < len(real_starts):
                offsets.append(real_starts[pos])
                subtitle_entries.append((texto, dur))
                subtitle_audio.append(speech_audio[k] if k < len(speech_audio) else None)
                subtitle_cenas.append(speech_cena[k] if k < len(speech_cena) else {})
        log(f"  [legenda] usando posições REAIS do concat ({len(offsets)} falas)")
    else:
        # Fallback (concat não expôs posições): chute matemático antigo.
        xfade_overlap = 0.3
        running = intro_dur
        for i, dur in enumerate(clip_durations):
            offsets.append(running)
            running += dur - (xfade_overlap if i < len(clip_durations) - 1 else 0)
        subtitle_entries = [(t, d) for (_i, t, d) in speech_subs]
        subtitle_audio = list(speech_audio[:len(subtitle_entries)])
        subtitle_cenas = list(speech_cena[:len(subtitle_entries)])
        offsets = offsets[:len(subtitle_entries)]
        log(f"  [legenda] fallback offsets matemáticos ({len(offsets)} falas)")

    # Tempo REAL de cada palavra (WordBoundary do edge-tts). Sem isso a legenda
    # estima pelo tamanho da palavra e desalinha da voz.
    word_times = [_load_word_times(a) for a in subtitle_audio]
    _n_wt = sum(1 for (t, _d), w in zip(subtitle_entries, word_times)
                if w and t and len(w) == len(t.split()))
    log(f"  [legenda] tempo real por palavra em {_n_wt}/{len(subtitle_entries)} falas")

    wm_handle = (profile or {}).get("watermark") or WATERMARK_HANDLE
    ass_ok = False
    if fx_legendas_ass.ativo() and subtitle_entries:
        # Legenda + barra de progresso + marca d'agua + palavras de impacto num
        # unico ASS (estilo manhwa-react): 1 re-encode no lugar de ~100 PNGs + watermark.
        final_sub = TMP_DIR / "final_sub.mp4"
        ass_ok, _n_ev = fx_legendas_ass.queimar(
            str(concat_out), str(final_sub), subtitle_entries, offsets[:len(subtitle_entries)],
            word_times, cor_genero=fx_divisoria.estilo_do_genero(genero)[1],
            handle=None if no_branding else wm_handle, tmp_dir=TMP_DIR, genero=genero, gancho=gancho_txt)
        if ass_ok:
            shutil.move(str(final_sub), str(concat_out))
            log(f"  + Legendas ASS: {_n_ev} eventos (palavra a palavra + barra + marca d'agua)")
        else:
            log("  ! Legenda ASS falhou — usando legenda antiga (PNG)")

    try:
        # render_subtitles_short retorna uma LISTA de specs de overlay
        # ({png,x,y,start,end}) estilo karaokê — NÃO texto SRT. O burn_subtitles
        # consome essa lista direto (mesmo contrato do hiper-fix).
        subs = None if ass_ok else render_subtitles_short(
            subtitle_entries, offsets=offsets[:len(subtitle_entries)],
            word_times=word_times, tmp_dir=TMP_DIR)
        if subs:
            log(f"  [DBG] antes burn: concat_out v={_ffprobe_duration(str(concat_out)):.1f}s | subs={len(subs)} | ultimo_end={max(s['end'] for s in subs):.1f}s")
            final_sub = TMP_DIR / "final_sub.mp4"
            burn_subtitles(str(concat_out), subs, str(final_sub))
            log(f"  [DBG] apos burn: final_sub v={_ffprobe_duration(str(final_sub)):.1f}s exists={final_sub.exists()}")
            if final_sub.exists() and final_sub.stat().st_size > 10000:
                shutil.move(str(final_sub), str(concat_out))
                log(f"  + Legendas: {len(subs)} overlays (offset intro={intro_dur:.1f}s)")
    except Exception as e:
        log(f"  ! Legendas falharam: {e}")

    # Watermark — handle vem do perfil do canal (canal_profiles) se houver.
    # (Com legenda ASS a marca d'agua ja saiu na mesma passada.)
    if not no_branding and not ass_ok:
        try:
            wm_out = TMP_DIR / "final_wm.mp4"
            render_watermark(str(concat_out), str(wm_out), handle=wm_handle)
            if wm_out.exists() and wm_out.stat().st_size > 10000:
                shutil.move(str(wm_out), str(concat_out))
        except Exception:
            pass

    # Card de propaganda final (produtos Inovare AI). Liga/desliga via
    # config/settings.json:promo_mode. Roda DEPOIS do watermark pra ficar
    # visivel. Falha do overlay cai em silent-retry — producao nao trava.
    promo_aplicado = None
    if not no_branding:
        try:
            import promos
            promo = promos.promo_pick()
            if promo:
                promo_out = TMP_DIR / "final_promo.mp4"
                if promos.burn_cta_card(str(concat_out), str(promo_out), promo,
                                        genero=genero, tema=tema):
                    shutil.move(str(promo_out), str(concat_out))
                    promo_aplicado = promo["id"]
                    log(f"  + Promo card: {promo['id']} (8s finais)")
        except Exception as e:
            log(f"  ! Promo card pulou (nao critico): {e}")

    # Output organizado: genero/story_id/vN_FINAL.mp4 + _ULTIMO demotion
    story_out_dir = out_dir / story_id
    story_out_dir.mkdir(parents=True, exist_ok=True)

    # Encontra próxima versão livre
    version = 1
    while True:
        final_name = f"v{version}_FINAL.mp4"
        final_path = story_out_dir / final_name
        if not final_path.exists():
            break
        version += 1

    shutil.move(str(concat_out), str(final_path))

    # _ULTIMO demotion: remove marker anterior, cria novo
    for old in story_out_dir.glob("*_ULTIMO.mp4"):
        demoted = str(old).replace("_ULTIMO.mp4", ".mp4")
        try:
            old.rename(demoted)
        except Exception:
            pass

    # O _ULTIMO (o que o postador sobe e de onde saem os shorts) e criado so no FIM
    # da etapa 10. Antes era copiado AQUI, antes do upscale 1080p/mascote/audio, e o
    # video postado saia sem eles.
    ultimo_path = story_out_dir / f"v{version}_FINAL_ULTIMO.mp4"

    # ─── STAGE 9: VERSÃO CENSURADA ──────────────────────────────────────────
    log("")
    log("[9/10] CENSURA — versão censurada...")
    _mt_stage("censura_pos")

    censored_path = None
    if censura and censura_scores and censura_visual:
        try:
            censored_path = out_dir / f"{story_id}{output_suffix}_CENSURADO_FINAL.mp4"
            shutil.copy2(str(final_path), str(censored_path))
            log(f"  + Versão censurada: {censored_path.name}")
        except Exception as e:
            log(f"  ! Censura falhou: {e}")
            censored_path = None
    else:
        log("  skip (sem imagens +18)")

    # ─── STAGE 10: FINALIZAÇÃO ──────────────────────────────────────────────
    log("")
    log("[10/10] FINALIZACAO...")

    # Upscale to 1080p (se não TEST_MODE)
    if not TEST_MODE and quality == "high":
        try:
            up_out = TMP_DIR / "upscaled.mp4"
            upscale_to_fullhd(str(final_path), str(up_out))
            if up_out.exists() and up_out.stat().st_size > final_path.stat().st_size * 0.8:
                shutil.move(str(up_out), str(final_path))
                log("  + Upscale 1080p")
        except Exception:
            pass

    # Mascote overlay
    if use_mascote and mascote_overlay:
        try:
            mascote_out = TMP_DIR / "mascote.mp4"
            clip_texts = []
            clip_personas = []
            sensual_indices = []

            speech_i = 0
            for i, img_path in enumerate(imgs):
                if i not in audio_files: continue
                audio_dur = _ffprobe_duration(str(audio_files[i]))
                if audio_dur < 0.5: continue

                cena = cenas[i] if i < len(cenas) else {}
                clip_texts.append(cena.get("narracao", cena.get("texto", "")))
                clip_personas.append(cena.get("persona", ""))
                if censura_scores and str(img_path) in censura_scores:
                    sensual_indices.append(speech_i)
                speech_i += 1

            abs_starts = offsets[:speech_i]
            eventos = mascote_overlay.pick_eventos(clip_texts, clip_personas, abs_starts, sensual=sensual_indices)
            if eventos:
                result = mascote_overlay.overlay_mascote(str(final_path), str(mascote_out), eventos)
                if result and mascote_out.exists():
                    shutil.move(str(mascote_out), str(final_path))
                    log(f"  + Mascote overlay ({len(eventos)} aparições)")
        except Exception as e:
            log(f"  ! Mascote falhou: {e}")

    # Audio final: sons por palavra + som de ambiente da cena (sfx_hint) + -14 LUFS.
    # Ultima mexida no arquivo: o video e copiado, so o audio e refeito.
    if fx_audio_final.ativo():
        try:
            _dur_v = _ffprobe_duration(str(final_path))
            _pal = fx_legendas_ass._palavras_timeline(
                subtitle_entries, offsets[:len(subtitle_entries)], word_times)
            _ev = fx_audio_final.gatilhos_palavra(_pal, genero, _dur_v, seed=story_id)
            _ev += fx_audio_final.sons_de_cena(subtitle_cenas, offsets[:len(subtitle_entries)],
                                               _dur_v, seed=story_id)
            _aout = TMP_DIR / "final_audio.mp4"
            _r = fx_audio_final.masterizar(str(final_path), str(_aout), _ev, TMP_DIR)
            if _r:
                shutil.move(str(_aout), str(final_path))
                _nomes = ", ".join(e["nome"] for e in _ev) or "nenhum"
                log(f"  + Audio final: {len(_ev)} sons ({_nomes}) | "
                    f"{_r['lufs_antes']} -> {_r['alvo']:.0f} LUFS")
            else:
                log("  ! Audio final falhou (mantido o audio do mix)")
        except Exception as e:
            log(f"  ! Audio final falhou: {e}")

    # _ULTIMO = versao FINAL de verdade. Hardlink (nao duplica o mp4 no disco);
    # se o disco nao suportar, copia.
    try:
        if ultimo_path.exists():
            ultimo_path.unlink()
        try:
            os.link(str(final_path), str(ultimo_path))
        except OSError:
            shutil.copy2(str(final_path), str(ultimo_path))
    except Exception:
        ultimo_path = final_path

    # Validação avançada (desync, silêncio, frames pretos)
    validation = auto_validate.validate(str(final_path))
    warnings = validation.get("warnings", []) + validation.get("fatal", [])

    if not validation["valid"]:
        quarantine_dest = QUARANTINE_DIR / final_path.name
        shutil.copy2(str(final_path), str(quarantine_dest))
        log(f"  ! QUARENTENA: {validation['fatal']}")
        _mt_count("quarantine")
        _mt_event("quarantine", str(validation["fatal"]))
    elif warnings:
        log(f"  ! Validacao: {warnings}")
    else:
        log("  + Validacao OK")

    # -- QUALITY JUDGE (feature exclusiva) — nota heurística 1-10 dos frames --
    quality_score = None
    if os.environ.get("QUALITY_JUDGE", "0") == "1":
        try:
            _qj = quality_judge.judge_video(str(final_path))
            quality_score = _qj.get("score")
            _thr = float(os.environ.get("QUALITY_THRESHOLD", "6"))
            if quality_score is not None and quality_score < _thr:
                log(f"  ! Quality Judge: nota {quality_score}/10 (abaixo de {_thr:.0f}) — {_qj.get('details')}")
            else:
                log(f"  + Quality Judge: nota {quality_score}/10")
        except Exception as e:
            log(f"  ! Quality Judge falhou: {e}")

    final_dur = validation.get("info", {}).get("duration", _ffprobe_duration(str(final_path)))
    file_size_mb = final_path.stat().st_size / (1024 * 1024)

    # Título viral + sanitize anti-ban
    viral_titles = viralizador.generate_viral_titles(titulo, genero)
    titulo_viral = viral_titles[0] if viral_titles else titulo
    titulo_viral = viralizador.sanitize_title(titulo_viral)
    hashtags = viralizador.get_hashtags(genero)

    # Thumbnail IA (via OmniRoute se disponível, senão ffmpeg frame)
    thumb_path = story_out_dir / f"thumb_v{version}.jpg"
    thumb_generated = False
    if os.environ.get("GEN_THUMBNAIL", "0") == "1":
        try:
            import omniroute_image
            thumb_prompt = f"YouTube thumbnail, dramatic, {genero} story: {titulo[:60]}, cinematic lighting, 16:9"
            thumb_png = story_out_dir / f"thumb_v{version}.png"
            ok = omniroute_image._generate(thumb_prompt, str(thumb_png))
            if ok and thumb_png.exists():
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(thumb_png), "-vf", "scale=1280:720",
                    "-q:v", "2", str(thumb_path)
                ], capture_output=True, timeout=15)
                thumb_png.unlink(missing_ok=True)
                if thumb_path.exists():
                    thumb_generated = True
                    log(f"  + Thumbnail IA: {thumb_path.name}")
        except Exception:
            pass

    if not thumb_generated:
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", str(final_path), "-vframes", "1",
                "-vf", "select='eq(n,25)',scale=720:1280", "-q:v", "2", str(thumb_path)  # o vídeo é 9:16
            ], capture_output=True, timeout=15)
            if thumb_path.exists():
                log(f"  + Thumbnail (frame): {thumb_path.name}")
        except Exception:
            pass

    # Metadata JSON
    meta = {
        "titulo": titulo,
        "titulo_viral": titulo_viral,
        "hashtags": hashtags,
        "genero": genero,
        "tema": tema,
        "n_cenas": len(cenas[:len(imgs)]),
        "duracao_s": final_dur,
        "tempo_geracao_s": round(time.time() - t0, 1),
        "video": str(final_path),
        "censored": str(censored_path) if censored_path else None,
        "thumbnail": str(thumb_path) if thumb_path.exists() else None,
        "story_id": story_id,
        "version": version,
        "warnings": warnings,
        "quality": quality,
        "quality_score": quality_score,
        "features": [],
    }

    features = []
    if use_parallax:
        features.append("parallax")
    if use_panel_fx:
        features.append("panel_fx")
    if use_elemental:
        features.append("elemental")
    if use_mascote:
        features.append("mascote")
    if use_motion_dir:
        features.append("motion_director")
    features.extend(["shake", "overlay", "memes", "watermark", "karaoke"])
    if promo_aplicado:
        features.append("promo_card")
    meta["features"] = features
    if promo_aplicado:
        meta["promo_aplicada"] = promo_aplicado

    meta_path = story_out_dir / f"v{version}_FINAL.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # postar.json — doc de postagem no padrao de hipercool-materiais
    # (PADRAO_DOC_POSTAGEM.md). A "cola" le isto e posta sem adivinhar.
    try:
        _write_postar_json(story_out_dir, final_name, genero, tema,
                           titulo_viral, hashtags, cenas[:len(imgs)])
    except Exception as e:
        log(f"  ! postar.json falhou (nao critico): {e}")

    # DUMP_SUBS_TIMING: sidecar com timing por clip (diagnóstico desync)
    if os.environ.get("DUMP_SUBS_TIMING", "0") == "1":
        timing_path = story_out_dir / f"v{version}_timing.txt"
        lines = []
        for idx, (off, dur) in enumerate(zip(offsets, clip_durations)):
            lines.append(f"clip_{idx:03d}: offset={off:.2f}s dur={dur:.2f}s end={off+dur:.2f}s")
        lines.append(f"intro_dur={intro_dur:.2f}s total={final_dur:.1f}s")
        timing_path.write_text("\n".join(lines), encoding="utf-8")
        log(f"  + Timing sidecar: {timing_path.name}")

    # Telegram notify (upload do MP4 + texto)
    if not skip_notify:
        try:
            msg = (f"Video pronto: {titulo_viral}\n"
                   f"Genero: {genero} | Duracao: {final_dur:.0f}s\n"
                   f"Tempo: {meta['tempo_geracao_s']:.0f}s ({meta['tempo_geracao_s']/60:.1f} min)\n"
                   f"Features: {', '.join(features)}\n"
                   f"{hashtags}")
            if warnings:
                msg += f"\nWarnings: {', '.join(warnings)}"
            send_telegram(msg)
            try:
                from _tg_safe import send_video
                send_video(str(final_path), caption=titulo_viral[:200])
            except (ImportError, Exception):
                pass
        except Exception:
            pass

    # Cleanup tmp
    for f in TMP_DIR.glob("clip_*"):
        try:
            f.unlink()
        except Exception:
            pass
    for f in TMP_DIR.glob("meme_*"):
        try:
            f.unlink()
        except Exception:
            pass

    elapsed = time.time() - t0
    log("")
    log("=" * 60)
    log(f"CONCLUIDO: {final_path}")
    log(f"  Titulo: {titulo}")
    log(f"  Genero: {genero}")
    log(f"  Cenas: {len(clips)} | Duracao: {final_dur:.0f}s")
    log(f"  Features: {' | '.join(features)}")
    log(f"  Tempo total: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    log("=" * 60)

    # ─── STAGE 11: AUTO-SPLIT SHORTS ───────────────────────────────────────
    if validation["valid"] and final_dur > 90 and os.environ.get("AUTO_SHORTS", "1") == "1":
        log("")
        log("[11] AUTO-SHORTS — dividindo video em Shorts...")
        try:
            from split_shorts import split_video
            shorts_out_dir = VIDEOS_DIR / "_shorts" / story_id
            shorts_out_dir.mkdir(parents=True, exist_ok=True)
            # HISTORIAS_SHORTS_POR_CENA=1 (desligado; pensado pros microcortes): corta nas trocas de cena (inicio de
            # cada fala, os mesmos offsets da legenda) em vez de a cada 55 s fixos, que pode cair no meio da frase.
            _cortes = None
            if os.environ.get("HISTORIAS_SHORTS_POR_CENA", "0") == "1":
                _cortes = [float(o) for o in offsets if o] or None
            shorts_list = split_video(str(final_path), out_dir=str(shorts_out_dir), cortes=_cortes)
            n_shorts = len(shorts_list) if shorts_list else 0
            log(f"  [OK] {n_shorts} shorts gerados em {shorts_out_dir}")
            meta["shorts_count"] = n_shorts
            meta["shorts_dir"] = str(shorts_out_dir)

            # Auto-schedule (se habilitado)
            if os.environ.get("AUTO_SCHEDULE", "0") == "1":
                try:
                    import auto_schedule
                    sched = auto_schedule.auto_schedule_after_pipeline(
                        str(ultimo_path), shorts_dir=str(shorts_out_dir), meta=meta)
                    if sched.get("video"):
                        log(f"  [OK] Video agendado: {sched['video'].get('scheduled_at', '?')}")
                    if sched.get("shorts"):
                        log(f"  [OK] {len(sched['shorts'])} shorts agendados")
                except Exception as e:
                    log(f"  ! Auto-schedule falhou: {e}")
        except Exception as e:
            log(f"  ! Auto-shorts falhou: {e}")
    elif not validation["valid"]:
        log("  [11] skip shorts (video em quarentena)")
    elif final_dur <= 90:
        log("  [11] skip shorts (video <=90s)")

    # ─── STAGE 12: 16:9 + COMPILADO LONGO ───────────────────────────────────
    # A história vira 16:9 em cache; com "compilado_min" do mesmo gênero, sai um compilado longo (compilado_longo.py).
    if validation["valid"] and os.environ.get("AUTO_COMPILADO", "1") == "1":
        log("")
        log("[12] 16:9 — versão deitada pro compilado...")
        try:
            import compilado_longo
            ls = compilado_longo.converter_com_cache(ultimo_path, genero, titulo_viral)
            if ls:
                log(f"  + 16:9 em cache: {ls.name}")
                comp = compilado_longo.talvez_compilar(genero)
                if comp:
                    meta["compilado"] = str(comp)
            else:
                log("  ! 16:9 falhou (a história segue normal)")
        except Exception as e:
            log(f"  ! 16:9/compilado falhou: {e}")

    _mt_write(final_path, "ok", extra={
        "duracao_s": final_dur, "warnings": warnings, "quality_score": quality_score,
        "n_cenas": len(cenas[:len(imgs)]), "tempo_geracao_s": round(time.time() - t0, 1),
    })
    return meta


# ═══════════════════════════════════════════════════════════════════════════════
# main() — CLI
# ═══════════════════════════════════════════════════════════════════════════════
def _run_single(args):
    return run(
            genero=args.genero,
            tema=args.tema,
            n_cenas=args.cenas,
            variacoes=args.variacoes,
            titulo_override=args.titulo,
            preset=args.preset,
            audio_only=args.audio_only,
            start_panel=args.start_panel,
            no_branding=args.no_branding,
            narrator_gender=args.narrator_gender,
            dry_run=args.dry_run,
            no_copyright_ost=args.no_copyright_ost,
            quality=args.quality,
            output_suffix=args.output_suffix,
            skip_notify=args.skip_notify,
            censura=args.censura,
        )


def main():
    parser = argparse.ArgumentParser(description="Histórias em Frames — Pipeline Completo")
    parser.add_argument("--genero", "-g", default="superacao", help="Gênero da história")
    parser.add_argument("--tema", "-t", default=None, help="Tema específico")
    parser.add_argument("--cenas", "-n", type=int, default=None, help="Número de cenas")
    parser.add_argument("--variacoes", type=int, default=1, help="Variações de imagem")
    parser.add_argument("--titulo", default=None, help="Título override")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), default=None)
    parser.add_argument("--audio-only", action="store_true", help="Só preenche cache TTS")
    parser.add_argument("--start-panel", type=int, default=0, help="Painel inicial (skip)")
    parser.add_argument("--no-branding", action="store_true", help="Sem intro/outro/watermark")
    parser.add_argument("--narrator-gender", choices=["M", "F"], default=None)
    parser.add_argument("--dry-run", action="store_true", help="Só mostra config, não gera")
    parser.add_argument("--no-copyright-ost", action="store_true")
    parser.add_argument("--quality", choices=list(QUALITY.keys()), default="med")
    parser.add_argument("--output-suffix", default="", help="Sufixo no nome do arquivo")
    parser.add_argument("--skip-notify", action="store_true", help="Sem Telegram")
    parser.add_argument("--censura", action="store_true", help="Ativa censura visual")
    parser.add_argument("--batch-file", default=None, help="JSON com lista de vídeos")

    args = parser.parse_args()

    # Batch mode
    if args.batch_file:
        batch = json.loads(Path(args.batch_file).read_text(encoding="utf-8"))
        results = []
        for i, job in enumerate(batch):
            log(f"\n{'='*40} BATCH {i+1}/{len(batch)} {'='*40}")
            r = run(
                genero=job.get("genero", args.genero),
                tema=job.get("tema"),
                n_cenas=job.get("cenas", args.cenas),
                titulo_override=job.get("titulo"),
                preset=job.get("preset", args.preset),
                quality=job.get("quality", args.quality),
                output_suffix=job.get("suffix", f"_b{i+1}"),
                censura=job.get("censura", args.censura),
                skip_notify=True,
            )
            results.append(r)
            _check_command_files()
        ok = sum(1 for r in results if r)
        log(f"\nBATCH COMPLETO: {ok}/{len(batch)} videos gerados")
        if not args.skip_notify:
            send_telegram(f"🎬 Batch completo: {ok}/{len(batch)} vídeos")
        return

    # Single run. A vez na fila de render (D:\\video-fila) e pedida na etapa RENDER, nao aqui:
    # roteiro/imagens/TTS sao leves e nao devem segurar a vez dos outros projetos.
    result = _run_single(args)

    if args.dry_run:
        print("DRY_RUN: OK")
    elif result and result.get("video"):
        print(f"OK: {result['video']}")
    elif result and result.get("audio_count"):
        print(f"AUDIO_READY: {result['audio_count']} arquivos em cache")
    else:
        print("FALHOU")
        sys.exit(1)


if __name__ == "__main__":
    main()
