"""Orquestra o processamento de um video de react: sondagem -> audio -> transcricao -> labios -> cortes -> editorial -> render -> validacao."""
import re
import shutil
import time
from pathlib import Path
from . import probe as P, audio as A, transcribe as T, lips as LIPS, cuts as CUTS, editorial as ED, captions as CAP, render as R
from . import music as MUS, thumb as TH, divider as DV, reactions as RX, emoji as EM, validate as VAL, triggers as TRG, memes as MEM, ideias as ID, hyperframes as HF
from .common import log, save_json, load_json, fmt_t


def slugify(name):
    s = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return s[:60] or "video"


def _cached(path, builder, force=False):
    if path.exists() and not force:
        return load_json(path)
    data = builder()
    save_json(data, path)
    return data


def _asset_file(cfg, key, kind):
    """Procura um SFX (kind='sfx') ou overlay alpha (kind='overlay') pelo nome configurado."""
    name = cfg["sfx"].get(key) if kind == "sfx" else cfg["overlays"].get(key)
    return _asset_by_name(cfg, name, kind)


def _asset_by_name(cfg, name, kind):
    if not name:
        return None
    if kind == "sfx" and not cfg["sfx"].get("enabled"):
        return None
    bases = [Path(cfg["paths"]["assets"]) / ("sfx" if kind == "sfx" else "overlays")]
    lib = cfg["paths"].get("sfx_library" if kind == "sfx" else "overlays_library")
    if lib:
        bases.append(Path(lib))
    exts = (".wav", ".mp3") if kind == "sfx" else (".mov", ".webm", ".mp4")
    for base in bases:
        for cand in [base / name] + [base / f"{name}{e}" for e in exts]:
            if cand.exists():
                return _overlay_cache(cfg, cand) if kind == "overlay" else cand
    return None


def _overlay_cache(cfg, src):
    """Converte o MOV ProRes 4444 (pesado para decodificar) em MOV PNG rgba leve, uma vez, em assets/overlays_cache."""
    src = Path(src)
    cache = Path(cfg["paths"]["assets"]) / "overlays_cache"
    cache.mkdir(parents=True, exist_ok=True)
    dst = cache / (src.stem + ".mov")
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    try:
        from .common import ffmpeg
        ffmpeg(cfg, ["-i", str(src), "-c:v", "png", "-pix_fmt", "rgba", "-an", str(dst)])
        log(f"overlay cache: {src.name} -> {dst.name}")
        return dst
    except Exception as e:  # noqa: BLE001
        log(f"overlay cache falhou ({e}); usando original")
        return src


def _channel(cfg, slug):
    chans = cfg.get("channels") or []
    by = {c["slug"]: c for c in chans}
    ch = by.get(slug) or by.get(cfg.get("default_channel")) or (chans[0] if chans else None)
    if ch:
        return ch
    return {"slug": "default", "name": cfg["channel"]["name"], "handle": cfg["channel"].get("handle", ""), "color": "#FFD700"}


def _copy_ready(cfg, sub, *files):
    ready = cfg["paths"].get("ready")
    if not ready:
        return
    dest = Path(ready) / sub if sub else Path(ready)
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f and Path(f).exists():
            shutil.copy2(f, dest / Path(f).name)


def process(cfg, video, use_llm=None, keep_all=False, force=False, dry_run=False, out_dir=None, only_parts=None, forcar_repetido=False):
    t0 = time.time()
    video = Path(video)
    slug = slugify(video.stem)
    work = Path(cfg["paths"]["work"]) / slug
    work.mkdir(parents=True, exist_ok=True)
    out_root = Path(out_dir or cfg["paths"]["output"]) / slug
    out_root.mkdir(parents=True, exist_ok=True)
    use_llm = cfg["editorial"]["use_llm"] if use_llm is None else use_llm
    C = cfg["cuts"]
    O = cfg["overlays"]
    log(f"=== {video.name} -> {out_root}")

    # 1. sondagem e layout
    info = _cached(work / "probe.json", lambda: P.probe(cfg, video), force)
    layout = _cached(work / "layout.json", lambda: P.detect_layout(cfg, video), force)
    plan = P.plan_output_layout(cfg, layout)
    save_json(plan, work / "plan.json")
    dur = info["duration"]

    # 2. audio limpo
    raw_wav, clean_wav = work / "raw.wav", work / "clean.wav"
    if force or not clean_wav.exists():
        A.extract_wav(cfg, video, raw_wav)
        A.clean_audio(cfg, raw_wav, clean_wav)
        log("audio: ruido reduzido (RNNoise) + de-esser + compressor")

    # 3. transcricao (Groq -> fallback local)
    tx = _cached(work / "transcript.json", lambda: T.transcribe(cfg, clean_wav), force)
    words, segments = tx["words"], tx["segments"]
    for s in segments:
        s["words"] = [w for w in words if s["start"] - 0.01 <= w["s"] <= s["end"] + 0.01]

    # 3b. memoria de videos ja feitos: o mesmo video reagido gravado de novo nao e renderizado outra vez
    from . import memoria as MEMO  # (MEM ja e o modulo de memes)
    hashes = None
    try:
        hashes = _cached(work / "hashes.json", lambda: MEMO.hashes_quadros(cfg, video, layout["content"]), force)
    except Exception as e:  # noqa: BLE001
        log(f"memoria: impressao visual falhou ({e})")
    if not forcar_repetido and not only_parts:
        dup = (MEMO.repetido(cfg, slug, hashes) if hashes else None) or MEMO.repetido_texto(cfg, slug, words)
        if dup:
            anterior, frac = dup
            log(f"REPETIDO: mesmo video reagido que {anterior.get('arquivo')} ({anterior.get('canal')}, {frac:.0%} igual) - "
                "nao renderizado (use --forcar-repetido para fazer mesmo assim)")
            summary = {"video": str(video), "duration": dur, "status": "repetido", "repetido_de": anterior.get("slug"), "semelhanca": round(frac, 3),
                       "channel": anterior.get("canal"), "outputs": []}
            save_json(summary, work / "summary.json")
            MEMO.registrar(cfg, slug, video, dur, "repetido", canal=anterior.get("canal"), assunto=f"repete {anterior.get('slug')}", hashes=hashes)
            return summary

    # 4. quem fala: labios
    series = None
    if layout["has_webcam"]:
        series = _cached(work / "lips.json", lambda: LIPS.mouth_series(cfg, video, layout["webcam"]), force)
        series = [tuple(x) for x in series]
        thr = LIPS.tag_words(cfg, series, words, segments)
    else:
        for w in words:
            w["speaker"] = "creator"
        for s in segments:
            s["speaker"] = "creator"
        thr = None

    # 4b. video base preparado (manhwareact.py base): a narracao em comum diz o que e conteudo e o que e o criador
    base_info = None
    try:
        from . import base as BASE
        achado = BASE.achar_base(cfg, words)
        if achado:
            BASE.marcar_narracao(words, segments, achado[2]["words"])
            base_info = {"id": achado[1].get("id"), "titulo": achado[1].get("titulo"), "canal": achado[1].get("canal"),
                         "url": achado[1].get("url"), "overlap": round(achado[3], 3)}
    except Exception as e:  # noqa: BLE001
        log(f"base: comparacao falhou ({e})")

    # 5. silencios
    sil = _cached(work / "silences.json", lambda: A.detect_silences(cfg, clean_wav, C["silence_db"], C["min_silence"]), force)
    gaps = CUTS.long_silences(sil, C["split_silence"])

    # 6. editorial (LLM)
    ed = None
    ed_path = work / "editorial.json"
    if use_llm:
        if ed_path.exists() and not force:
            ed = load_json(ed_path)
        else:
            log("editorial: consultando LLM...")
            ed = ED.analyze(cfg, segments, dur, gaps, base=base_info)
            if ed:
                save_json(ed, ed_path)
        if ed:
            ED.apply_speakers(ed, segments, words)
        if ed and cfg["editorial"].get("fix_transcript"):
            fix_path = work / "fixes.json"
            if fix_path.exists() and not force:
                for k, v in load_json(fix_path).items():
                    i = int(k)
                    if i < len(words):
                        words[i]["w_orig"] = words[i]["w"]
                        words[i]["w"] = v
            else:
                ED.fix_words(cfg, words, ed.get("topic", ""))
                save_json({str(i): w["w"] for i, w in enumerate(words) if "w_orig" in w}, fix_path)
    if ed is None:
        ed = {"usable": True, "score": None, "reason": "editorial desativado ou indisponivel", "topic": "", "channel": None, "work": None,
              "parts": [{"start": 0.0, "end": dur}], "remove": []}
        for p in ed["parts"]:
            p.update(ED.fallback_meta(cfg, segments, p))
    if (cfg.get("forcar") or {}).get("canal"):  # ex.: aula do dono vai sempre para o canal de aulas (mr/temas.py)
        ed["channel"] = cfg["forcar"]["canal"]
    channel = _channel(cfg, ed.get("channel"))
    log(f"canal: {channel['name']} ({channel['slug']})")
    # divisoria animada + emenda irregular (por canal)
    seam = None
    Dcfg = cfg.get("divider", {})
    if plan.get("seam", {}).get("overlap") and plan.get("webcam"):
        style = channel.get("divider") or (Dcfg.get("per_channel") or {}).get(channel["slug"]) or Dcfg.get("style", "electric")
        try:
            dv_path, dv_h = DV.divider_asset(cfg, style, channel.get("color", "#FFD700"))
            mask = DV.seam_mask(cfg, plan["content"]["scale"][1], plan["seam"]["overlap"], Dcfg.get("edge", "tear"), seed=7)
            seam = {"mask": str(mask), "overlap": plan["seam"]["overlap"], "y": plan["divider_out"], "divider": str(dv_path) if dv_path else None,
                    "divider_h": dv_h, "opacity": float(Dcfg.get("opacity", 1.0)), "style": style}
            plan["seam"]["mask"] = str(mask)
            log(f"divisoria: {style} ({channel.get('color')}), borda {Dcfg.get('edge', 'tear')}")
        except Exception as e:  # noqa: BLE001
            log(f"divisoria indisponivel ({e}); seguindo sem efeito")
            seam = None

    # vigia de formatos: o que o video reagido ensina que nos mesmos podemos produzir
    idea_path = work / "ideia.json"
    if cfg.get("ideas", {}).get("enabled", True) and use_llm and (force or not idea_path.exists()):
        try:
            idea = ID.analyze_idea(cfg, video, layout, segments, ed)
            if idea:
                save_json(idea, idea_path)
                ID.save_idea(cfg, idea)
        except Exception as e:  # noqa: BLE001
            log(f"ideias: falhou ({e})")
    summary = {"video": str(video), "duration": dur, "layout": layout, "lip_threshold": thr, "engine": tx.get("engine"), "editorial": ed, "base": base_info,
               "channel": channel["slug"], "outputs": []}
    if not keep_all and (ed.get("usable") is False or (ed.get("score") is not None and ed["score"] < cfg["editorial"]["min_score"])):
        log(f"REJEITADO pelo editorial (score={ed.get('score')}): {ed.get('reason')}")
        summary["status"] = "rejected"
        _write_report(cfg, out_root, summary, segments)
        save_json(summary, work / "summary.json")
        MEMO.registrar(cfg, slug, video, dur, "rejected", canal=channel["slug"], assunto=ed.get("topic"), hashes=hashes)
        return summary

    # 7. por parte (limpa saidas antigas desta origem: o numero de partes pode ter mudado)
    n_parts = len(ed["parts"])
    serie = n_parts > 1 and not ed.get("highlights")  # partes em sequencia (1/2, 2/2) x destaques independentes
    if ed.get("highlights") and cfg["paths"].get("ready_cortes"):
        # cortes de um react grande: pasta propria, separada dos Shorts de gravacoes curtas e do video inteiro
        cfg = dict(cfg, paths=dict(cfg["paths"], ready=cfg["paths"]["ready_cortes"]))
    if not dry_run and not only_parts:  # so as partes pedidas: nao apaga as que ja estao prontas
        for old_f in list(out_root.glob(f"{slug}*.mp4")) + list(out_root.glob(f"{slug}*.json")) + list(out_root.glob(f"{slug}*.txt")) + list(out_root.glob(f"{slug}*.jpg")):
            old_f.unlink(missing_ok=True)
        ready = cfg["paths"].get("ready")
        if ready:
            for sub in Path(ready).glob("*/"):
                for old_f in list(sub.glob(f"{slug}*")):
                    old_f.unlink(missing_ok=True)
    for pi, part in enumerate(ed["parts"]):
        if only_parts and (pi + 1) not in only_parts:
            continue
        pa, pb = part["start"], part["end"]
        tag = f"_p{pi+1}" if n_parts > 1 else ""
        pw = work / f"part{pi+1}"
        pw.mkdir(exist_ok=True)
        removes = [r for r in ed.get("remove", []) if pa <= r["start"] < pb]
        extra = [(r["start"], r["end"]) for r in removes]
        keeps = CUTS.plan(cfg, dur, sil, words, segments, extra, part=(pa, pb))
        if not keeps:
            log(f"parte {pi+1}: nada para manter, pulando")
            continue
        if cfg["editorial"].get("trim_to_max", True):
            keeps = CUTS.trim_keeps(keeps, float(cfg["output"]["max_duration"]))
        tl = CUTS.Timeline(keeps)
        creator_words = [w for w in words if w.get("speaker") != "content" and not w.get("filler")]
        rw = tl.remap_words(creator_words)
        meta = {k: part.get(k) for k in ("hook", "title", "description", "hashtags", "tags", "cta", "mood", "music", "pinned_comment", "title_alternatives")}
        if not meta.get("title"):
            meta.update(ED.fallback_meta(cfg, segments, part))
        meta["work"] = ed.get("work")
        meta["channel"] = channel["slug"]
        keywords = [{"t": tl.map(float(k["t"])), "text": k["text"], "emoji": k.get("emoji")} for k in part.get("keywords", []) if tl.inside(float(k["t"]))]
        part_label = f"PARTE {pi+1}/{n_parts}" if serie else None
        ass_txt = CAP.build_ass(cfg, rw, tl.duration, plan, meta, keywords, channel=channel, part_label=part_label)
        ass_path = pw / "captions.ass"
        ass_path.write_text(ass_txt, encoding="utf-8")
        # zoom na webcam (enquanto fala) e no conteudo (keywords)
        if O.get("punch_in"):
            if O.get("zoom_mode", "speech") == "speech":
                zoom = R.zoom_plan_speech(rw, tl.duration)
            else:
                chunk_starts = [ch[0]["s"] for ch in CAP.chunk_words(rw, cfg["captions"]["max_words"], cfg["captions"]["max_chunk_seconds"])]
                zoom = R.zoom_plan(tl.segment_starts(), chunk_starts, tl.duration)
        else:
            zoom = []
        czoom = [[max(0.0, k["t"] - 0.05), min(tl.duration, k["t"] + 1.1)] for k in keywords] if O.get("content_zoom") else []
        # sfx + overlays
        sfx, overlays = [], []
        hook_sfx = _asset_file(cfg, "hook", "sfx")
        if hook_sfx and meta.get("hook") and O.get("hook"):
            sfx.append({"t": 0.0, "file": hook_sfx})
        key_sfx = _asset_file(cfg, "keyword", "sfx")
        key_ov = _asset_file(cfg, "keyword_overlay", "overlay") if O.get("keywords") else None
        key_ov_dur = R.media_duration(cfg, key_ov) if key_ov else 0
        for k in keywords:
            if key_sfx and O.get("keywords"):
                sfx.append({"t": k["t"], "file": key_sfx})
            if key_ov:
                overlays.append({"t": max(0.0, k["t"] - 0.1), "file": key_ov, "dur": key_ov_dur})
            if O.get("emoji_keywords") and k.get("emoji"):
                png = EM.emoji_png(cfg, k["emoji"])
                if png:
                    key_y = plan["content"]["out_y"] + int((cfg["output"]["height"] - plan["content"]["out_y"]) * 0.45) - 150
                    overlays.append({"t": k["t"], "file": png, "dur": 1.3, "png": True, "x": cfg["output"]["width"] // 2, "y": key_y, "w": 190})
        # reacoes do criador: overlay + emoji + som de meme
        if O.get("reactions"):
            r_ov, r_sfx = RX.plan_reactions(cfg, part.get("reactions", []), tl, lambda n: _asset_by_name(cfg, n, "overlay"),
                                            lambda e: EM.emoji_png(cfg, e), tl.duration, seed=slug + tag, channel_slug=channel["slug"])
            overlays += r_ov
            sfx += r_sfx
        # gatilhos de som por palavra falada
        if O.get("word_triggers"):
            t_sfx, t_ov = TRG.plan_word_triggers(cfg, creator_words, tl, tl.duration, lambda e: EM.emoji_png(cfg, e), seed=slug + tag)
            sfx += t_sfx
            overlays += t_ov
        # foley: som da cena pelas palavras do video reagido (mr/foley.py)
        if O.get("foley"):
            from . import foley as FOL
            sfx += FOL.plan_foley(cfg, [w for w in words if w.get("speaker") == "content"], tl, tl.duration)
        # memes escolhidos pelo editorial (imagem ou video do acervo)
        if O.get("memes") and part.get("memes"):
            items, _ = MEM.catalog_for_prompt(cfg)
            by_id = {it["id"]: it for it in items}
            m_ov, m_sfx = MEM.plan_memes(cfg, part.get("memes"), by_id, tl, tl.duration, plan)
            overlays += m_ov
            sfx += m_sfx
        # "assista ate o fim" no inicio
        hf_on = cfg.get("hyperframes", {}).get("enabled", True)
        if tl.duration > 35:
            wte_hf = _hf(cfg, "watch_to_end", "ASSISTE ATÉ O FIM 👀", channel.get("color"), dur=1.8, w=1080, h=200) if hf_on else None
            if wte_hf:
                y_w = plan["content"]["out_y"] + int(plan.get("seam", {}).get("overlap") or 0) + 40
                overlays.append({"t": float(O.get("watchtoend_at", 2.8)), "file": wte_hf[0], "dur": wte_hf[1], "clip": True, "x": 0, "y": y_w})
            else:
                wte = _asset_file(cfg, "watchtoend_overlay", "overlay")
                if wte:
                    overlays.append({"t": float(O.get("watchtoend_at", 2.8)), "file": wte, "dur": R.media_duration(cfg, wte)})
        # numeros falados em destaque (ex.: "20 mil", "300 reais")
        if hf_on and O.get("big_numbers", True):
            for nb in _numbers(creator_words, tl, tl.duration)[:2]:
                hfn = _hf(cfg, "big_number", nb["text"], channel.get("color"), sub=nb["sub"], dur=1.8, w=1080, h=420, size=170)
                if hfn:
                    overlays.append({"t": nb["t"], "file": hfn[0], "dur": hfn[1], "clip": True, "x": 0, "y": plan["content"]["out_y"] + 120})
        # mascara de corte: glitch rapido nos cortes feitos pelo editorial (nao nos silencios)
        cm = _asset_file(cfg, "cut_mask_overlay", "overlay")
        if cm and removes:
            cm_d = R.media_duration(cfg, cm)
            for r in removes:
                tcut = tl.map(r["end"])
                if 0.5 < tcut < tl.duration - 0.5:
                    overlays.append({"t": max(0.0, tcut - cm_d / 2), "file": cm, "dur": cm_d})
        # like no meio
        like_ov = _asset_file(cfg, "like_overlay", "overlay")
        if like_ov and tl.duration > 20:
            lt = tl.duration * float(O.get("like_at", 0.45))
            if all(abs(lt - k["t"]) > 3 for k in keywords):
                overlays.append({"t": lt, "file": like_ov, "dur": R.media_duration(cfg, like_ov)})
                like_sfx = _asset_file(cfg, "like", "sfx")
                if like_sfx:
                    sfx.append({"t": lt, "file": like_sfx})
        # CTA final: "parte 2" se houver continuacao; senao alterna inscreva-se / comenta
        if O.get("cta") and tl.duration > 8:
            ct = max(0.0, tl.duration - O["cta_seconds"])
            cta_ev = None
            if serie and pi < n_parts - 1:
                hp = _hf(cfg, "part_badge", f"PARTE {pi+2}", channel.get("color"), sub="NO PERFIL", dur=2.2, w=1080, h=360) if hf_on else None
                if hp:
                    cta_ev = {"t": ct, "file": hp[0], "dur": hp[1], "clip": True, "x": 0, "y": cfg["output"]["height"] - 560}
                else:
                    cta_ov = _asset_file(cfg, "part2_overlay", "overlay") or _asset_file(cfg, "cta_overlay", "overlay")
                    cta_ev = {"t": ct, "file": cta_ov, "dur": R.media_duration(cfg, cta_ov)} if cta_ov else None
            else:
                use_comment = (sum(ord(c) for c in slug) % 2 == 1)
                if use_comment and hf_on and meta.get("pinned_comment"):
                    hq = _hf(cfg, "cta_question", meta["pinned_comment"][:70], channel.get("color"), dur=O["cta_seconds"] + 0.3, w=1080, h=520)
                    if hq:
                        cta_ev = {"t": ct, "file": hq[0], "dur": hq[1], "clip": True, "x": 0, "y": cfg["output"]["height"] - 760}
                if cta_ev is None:
                    alt = _asset_file(cfg, "comment_overlay", "overlay")
                    cta_ov = alt if (alt and use_comment) else _asset_file(cfg, "cta_overlay", "overlay")
                    cta_ev = {"t": ct, "file": cta_ov, "dur": R.media_duration(cfg, cta_ov)} if cta_ov else None
            if cta_ev:
                overlays.append(cta_ev)
                cta_sfx = _asset_file(cfg, "cta", "sfx")
                if cta_sfx:
                    sfx.append({"t": ct, "file": cta_sfx})
        sfx, overlays = _declutter(sfx, overlays)
        # musica
        music = None
        M = cfg["music"]
        if M.get("enabled") and (meta.get("music", True) or not M.get("respect_editorial", True)):
            music = MUS.pick_track(cfg, meta.get("mood") or M.get("default_mood"), seed=slug + tag)
        edl = {"part": [pa, pb], "keeps": keeps, "duration_out": tl.duration, "zoom": zoom, "content_zoom": czoom, "keywords": keywords,
               "sfx": [{"t": s["t"], "file": str(s["file"])} for s in sfx],
               "overlays": [{"t": o["t"], "file": str(o["file"]), "dur": o["dur"], "png": bool(o.get("png")), "video": bool(o.get("video"))} for o in overlays],
               "music": str(music) if music else None, "meta": meta, "channel": channel["slug"], "seam": seam, "words": rw}
        save_json(edl, pw / "edl.json")
        out_mp4 = out_root / f"{slug}{tag}.mp4"
        if dry_run:
            log(f"dry-run: parte {pi+1} -> {out_mp4.name} ({tl.duration:.1f}s, {len(keeps)} trechos, {len(zoom)} zooms, {len(overlays)} overlays, "
                f"{len(sfx)} sfx, musica={'sim' if music else 'nao'}, canal={channel['slug']})")
            summary["outputs"].append({"file": str(out_mp4), "duration": tl.duration, "dry_run": True, "meta": meta})
            continue
        final_wav = pw / "final.wav"
        R.render_audio(cfg, clean_wav, keeps, final_wav, sfx, music=music)
        R.render_video(cfg, video, final_wav, keeps, plan, ass_path, out_mp4, zoom, overlays, content_zoom=czoom, seam=seam)
        postar = _write_postar(cfg, out_root, out_mp4, meta, pi, n_parts if serie else 1, channel)
        meta_txt = _write_meta_txt(out_root, out_mp4, meta, channel)
        thumb = None
        if cfg.get("thumb", {}).get("enabled", True):
            try:  # capa no estilo manhwa/anime (mr/capa.py); a thumb antiga fica de reserva
                from . import capa as CAPA
                thumb = CAPA.capa_short(cfg, video, layout, pa, pb, meta.get("hook") or "", channel.get("color"),
                                        out_root / f"{slug}{tag}_thumb.jpg", work=work, duracao=dur)
            except Exception as e:  # noqa: BLE001
                log(f"capa nova falhou ({e}); usando a thumb antiga")
            if not thumb:
                t_best = TH.best_time(series, keeps, creator_words) if series else (keeps[len(keeps) // 2][0] + 0.5)
                thumb = TH.make_thumb(cfg, video, t_best, plan, meta.get("hook") or "", out_root / f"{slug}{tag}_thumb.jpg",
                                      handle=channel.get("handle"), color=channel.get("color"))
        val = None
        if cfg.get("validate", {}).get("enabled", True):
            val = VAL.validate_output(cfg, out_mp4, expected_duration=tl.duration, lufs_target=float(cfg["audio"]["target_lufs"]))
            VAL.mark_postar(postar, val["ok"], val["problems"])
            if val["ok"] and cfg["validate"].get("cleanup", True):
                VAL.cleanup_work(pw)
        _copy_ready(cfg, channel["slug"], out_mp4, postar, meta_txt, thumb)
        summary["outputs"].append({"file": str(out_mp4), "duration": tl.duration, "keeps": len(keeps), "meta": meta, "thumb": str(thumb) if thumb else None,
                                   "music": str(music) if music else None, "removed_pct": round(100 * (1 - tl.duration / max(0.01, pb - pa)), 1),
                                   "validation": val})
        log(f"OK parte {pi+1}: {out_mp4} ({tl.duration:.1f}s)")

    summary["status"] = "done"
    summary["elapsed_s"] = round(time.time() - t0, 1)
    _write_report(cfg, out_root, summary, segments)
    save_json(summary, work / "summary.json")
    if not dry_run:
        MEMO.registrar(cfg, slug, video, dur, "done", canal=channel["slug"], saidas=[Path(o["file"]).name for o in summary["outputs"]],
                      assunto=ed.get("topic") or ed.get("work"), hashes=hashes)
    if summary["outputs"] and not dry_run and cfg["paths"].get("ready"):
        dest = Path(cfg["paths"]["ready"]) / channel["slug"]
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out_root / "relatorio.md", dest / f"{slug}_relatorio.md")
    log(f"concluido em {summary['elapsed_s']}s")
    return summary


def _hf(cfg, template, text, color, **kw):
    try:
        return HF.render(cfg, template, text, color=color or "#FFD700", **kw)
    except Exception as e:  # noqa: BLE001
        log(f"hyperframes indisponivel ({str(e)[:80]})")
        return None


_NUM_WORDS = {"mil": "MIL", "milhao": "MILHÃO", "milhoes": "MILHÕES", "bilhao": "BILHÃO", "bilhoes": "BILHÕES"}
_UNITS = {"reais": "REAIS", "real": "REAIS", "dolares": "DÓLARES", "anos": "ANOS", "km": "KM", "metros": "METROS", "quilos": "QUILOS", "kg": "KG",
          "horas": "HORAS", "dias": "DIAS", "vezes": "VEZES", "por cento": "%", "graus": "GRAUS", "litros": "LITROS", "cavalos": "CAVALOS", "polegadas": "POLEGADAS"}


def _numbers(words, timeline, duration, cooldown=6.0):
    """Detecta numeros falados (digitos ou 'X mil') seguidos de unidade e devolve [{t, text, sub}] no timeline cortado."""
    import re
    import unicodedata
    out = []
    last = -99.0
    def norm(x):
        x = unicodedata.normalize("NFKD", x.lower())
        return "".join(c for c in x if not unicodedata.combining(c)).strip(".,!?")
    for i, w in enumerate(words):
        tok = norm(w["w"])
        m = re.match(r"^(r\$)?(\d{1,3}(?:[.,]\d{3})*|\d+)(?:[.,](\d+))?(%|k)?$", tok)
        if not m or not timeline.inside(w["s"]):
            continue
        t = timeline.map(w["s"])
        if t - last < cooldown or t >= duration - 2:
            continue
        num = tok.upper().replace("R$", "").replace("K", " MIL")
        sub = ""
        nxt = norm(words[i + 1]["w"]) if i + 1 < len(words) else ""
        nxt2 = norm(words[i + 2]["w"]) if i + 2 < len(words) else ""
        if nxt in _NUM_WORDS:
            num = f"{num} {_NUM_WORDS[nxt]}"
            if nxt2 in _UNITS:
                sub = _UNITS[nxt2]
        elif nxt in _UNITS:
            sub = _UNITS[nxt]
        if tok.startswith("r$") or sub == "REAIS":
            num = "R$ " + num.replace("R$", "").strip()
            sub = ""
        if len(num) > 14:
            continue
        try:
            val = float(re.sub(r"[^\d.]", "", m.group(2).replace(".", "").replace(",", ".")) or 0)
        except Exception:
            val = 0
        if val < 10 and not sub and "MIL" not in num and "R$" not in num:
            continue
        out.append({"t": t, "text": num, "sub": sub})
        last = t
    return out


def _declutter(sfx, overlays, win_sfx=0.6, win_png=0.9):
    """Evita poluicao: no maximo um som por janela (fixos tem prioridade) e um emoji/meme por janela."""
    fixed = {"whoosh.wav", "like.wav", "cta.wav"}
    pri = lambda e: 0 if Path(str(e["file"])).name in fixed else (1 if e.get("gain_db") is not None else 2)
    kept = []
    for e in sorted(sfx, key=lambda e: (e["t"], pri(e))):
        if any(abs(e["t"] - k["t"]) < win_sfx for k in kept) and pri(e) > 0:
            continue
        kept.append(e)
    kept_ov = []
    for o in sorted(overlays, key=lambda o: o["t"]):
        if (o.get("png") or o.get("video")) and any((k.get("png") or k.get("video")) and abs(o["t"] - k["t"]) < win_png for k in kept_ov):
            continue
        kept_ov.append(o)
    if len(kept) < len(sfx) or len(kept_ov) < len(overlays):
        log(f"limpeza: sfx {len(sfx)}->{len(kept)}, overlays {len(overlays)}->{len(kept_ov)}")
    return kept, kept_ov


def _tags_text(meta):
    return ", ".join(dict.fromkeys(t.strip() for t in (meta.get("tags") or []) if t.strip()))


def _write_postar(cfg, out_root, mp4, meta, pi, n, channel):
    tags = [t for t in (meta.get("tags") or []) if t]
    doc = {"arquivo": mp4.name, "categoria": "react", "tipo": "short", "titulo": (meta.get("title") or "")[:100],
           "descricao": meta.get("description") or "", "tags": tags, "tags_texto": _tags_text(meta),
           "hashtags": meta.get("hashtags") or [], "thumb": mp4.stem + "_thumb.jpg",
           "comentario_fixado": meta.get("pinned_comment") or "", "titulos_alternativos": meta.get("title_alternatives") or [],
           "canais": [channel["name"]], "canal_slug": channel["slug"], "parte": (pi + 1) if n > 1 else None, "total_partes": n if n > 1 else None,
           "publish_at": None, "privacy": "private", "made_for_kids": False, "pronto": True}
    if (cfg.get("forcar") or {}).get("canal"):  # a rede nao muda o canal nem reescreve o texto
        doc.update({"canal_fixo": channel["slug"], "manter_texto": True})
    p = out_root / (mp4.stem + ".postar.json")
    save_json(doc, p)
    return p


def _write_meta_txt(out_root, mp4, meta, channel):
    """Texto pronto para colar no YouTube: titulo, descricao e tags separadas por virgula (sem aspas)."""
    p = out_root / (mp4.stem + "_meta.txt")
    alts = meta.get("title_alternatives") or []
    lines = [f"CANAL: {channel['name']} ({channel.get('handle', '')})", "", "TITULO:", meta.get("title") or "", ""]
    if alts:
        lines += ["TITULOS ALTERNATIVOS (teste A/B):"] + [f"- {a}" for a in alts] + [""]
    lines += ["DESCRICAO:", meta.get("description") or "", "", "TAGS:", _tags_text(meta), "", "HASHTAGS:", " ".join(meta.get("hashtags") or []), "",
              "COMENTARIO FIXADO:", meta.get("pinned_comment") or "", "", "GANCHO:", meta.get("hook") or "", "",
              "OBRA/FONTE:", meta.get("work") or "", "", "CTA:", meta.get("cta") or ""]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _write_report(cfg, out_root, summary, segments):
    ed = summary["editorial"]
    lines = [f"# Relatorio - {Path(summary['video']).name}", "",
             f"- Duracao original: {summary['duration']:.1f}s", f"- Status: {summary.get('status')}", f"- Canal: {summary.get('channel')}",
             f"- Transcricao: {summary.get('engine')}",
             f"- Editorial: score={ed.get('score')} usable={ed.get('usable')} - {ed.get('reason')}", f"- Assunto: {ed.get('topic')} | Obra: {ed.get('work')}", ""]
    for o in summary["outputs"]:
        m = o["meta"]
        v = o.get("validation") or {}
        lines += [f"## {Path(o['file']).name} ({o['duration']:.1f}s, {o.get('removed_pct', 0)}% cortado)", "",
                  f"- Gancho: **{m.get('hook')}**", f"- Titulo: {m.get('title')}", f"- Alternativas: {' | '.join(m.get('title_alternatives') or [])}",
                  f"- Descricao: {m.get('description')}", f"- Tags: {_tags_text(m)}", f"- Hashtags: {' '.join(m.get('hashtags') or [])}",
                  f"- Comentario fixado: {m.get('pinned_comment')}", f"- CTA: {m.get('cta')}",
                  f"- Mood/musica: {m.get('mood')} / {Path(o['music']).name if o.get('music') else 'sem trilha'}", f"- Thumb: {Path(o['thumb']).name if o.get('thumb') else '-'}",
                  f"- Validacao: {'OK' if v.get('ok', True) else 'PROBLEMAS: ' + '; '.join(v.get('problems', []))} (LUFS {v.get('lufs')})", ""]
    if ed.get("remove"):
        lines += ["## Trechos removidos pelo editorial", ""] + [f"- {fmt_t(r['start'])}-{fmt_t(r['end'])}: {r['why']}" for r in ed["remove"]] + [""]
    lines += ["## Transcricao (CRIADOR = legendado; CONTEUDO = audio do video reagido)", ""]
    lines += [f"- [{fmt_t(s['start'])}] **{s.get('speaker', '?')}**: {s['text']}" for s in segments]
    (out_root / "relatorio.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
