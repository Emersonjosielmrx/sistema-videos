"""Montagem final com ffmpeg em 2 passagens:
A) cortes + layout (webcam / emenda irregular / conteudo) + zooms -> base.mp4
B) overlays alpha + divisoria animada + legendas ASS + audio final -> mp4
"""
import hashlib
import os
from pathlib import Path
from .common import ffmpeg, ffpath, log, ffprobe_json
from .audio import loudnorm_two_pass

_CLIPES_DIR = Path(os.environ.get("TEMP") or "C:/Temp") / "mr_clipes"


def _clipe_parado(cfg, img, dur):
    """Imagem parada como clipe .mov curto (qtrle, com alfa). '-loop 1' trava o ffmpeg 8."""
    img = Path(img)
    chave = hashlib.md5(f"{img.resolve()}|{img.stat().st_mtime_ns}".encode()).hexdigest()[:10]
    mov = _CLIPES_DIR / f"{img.stem[:40]}_{chave}_{dur:.2f}.mov"
    if not mov.exists():
        _CLIPES_DIR.mkdir(parents=True, exist_ok=True)
        tmp = mov.with_name(mov.stem + "_tmp.mov")
        n = max(1, int(round(dur * 25)))
        ffmpeg(cfg, ["-i", str(img), "-vf", f"loop=loop={n - 1}:size=1:start=0,fps=25,format=argb",
                     "-frames:v", str(n), "-c:v", "qtrle", str(tmp)], timeout=120)
        os.replace(str(tmp), str(mov))
    return mov



def _concat_graph(keeps, src="0:v", kind="v"):
    lines, labels = [], []
    for i, (a, b) in enumerate(keeps):
        lab = f"{kind}{i}"
        if kind == "v":
            lines.append(f"[{src}]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[{lab}]")
        else:
            lines.append(f"[{src}]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[{lab}]")
        labels.append(f"[{lab}]")
    out = f"{kind}cat"
    if len(keeps) == 1:
        lines[-1] = lines[-1].replace(f"[{labels[0][1:-1]}]", f"[{out}]")
        return lines, out
    lines.append("".join(labels) + f"concat=n={len(keeps)}:v={1 if kind == 'v' else 0}:a={0 if kind == 'v' else 1}[{out}]")
    return lines, out


def render_audio(cfg, clean_wav, keeps, out_wav, sfx_events=(), music=None):
    """Corta o audio limpo, mistura SFX (e musica opcional com ducking) e normaliza em 2 passos."""
    work = Path(out_wav).parent
    lines, acat = _concat_graph(keeps, "0:a", "a")
    inputs = ["-i", str(clean_wav)]
    mix_labels = [f"[{acat}]"]
    idx = 1
    S = cfg["sfx"]
    for ev in sfx_events:
        inputs += ["-i", str(ev["file"])]
        ms = int(ev["t"] * 1000)
        gain = ev.get("gain_db", S["gain_db"])
        corte = f"atrim=0:{ev['dur']:.2f},afade=t=out:st={max(0.1, ev['dur'] - 0.4):.2f}:d=0.4," if ev.get("dur") else ""
        lines.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,{corte}volume={gain}dB,adelay={ms}|{ms}[sfx{idx}]")
        mix_labels.append(f"[sfx{idx}]")
        idx += 1
    if music and cfg["music"].get("enabled"):
        M = cfg["music"]
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        lines.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I={M['lufs']}:TP=-3:LRA=7,afade=t=in:d=1.5[mus]")
        if M.get("duck", True):
            lines.append(f"[{acat}]asplit=2[voice][sc]")
            lines.append("[mus][sc]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500:makeup=1[musd]")
            mix_labels[0] = "[voice]"
            mix_labels.append("[musd]")
        else:
            mix_labels.append("[mus]")
        idx += 1
    if len(mix_labels) > 1:
        lines.append("".join(mix_labels) + f"amix=inputs={len(mix_labels)}:normalize=0:duration=first[amix]")
        final = "amix"
    else:
        final = acat
    script = work / "audio_graph.txt"
    script.write_text(";\n".join(lines), encoding="utf-8")
    mixed = work / "mixed.wav"
    ffmpeg(cfg, [*inputs, "-filter_complex_script", str(script), "-map", f"[{final}]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(mixed)])
    loudnorm_two_pass(cfg, mixed, out_wav)
    return out_wav


def _enable(segments):
    return "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in segments)


def ffmpeg_retry(cfg, args, tries=3, wait=25):
    """ffmpeg com nova tentativa quando o Windows nega memoria (pagefile cheio por outros programas)."""
    import time
    last = None
    for i in range(tries):
        try:
            return ffmpeg(cfg, args)
        except RuntimeError as e:
            last = e
            msg = str(e)
            if not any(k in msg for k in ("allocate memory", "get_buffer", "malloc", "external library")):
                raise
            log(f"ffmpeg: sem memoria (tentativa {i+1}/{tries}); aguardando {wait}s")
            time.sleep(wait)
    light = list(args)
    for i, a in enumerate(light):
        if a == "-preset" and i + 1 < len(light):
            light[i + 1] = "ultrafast"
        if a == "-x264-params" and i + 1 < len(light):
            light[i + 1] = "rc-lookahead=0:sync-lookahead=0:threads=1"
        if a == "-threads" and i + 1 < len(light):
            light[i + 1] = "1"
    log("ffmpeg: tentativa final com encoder leve (veryfast)")
    try:
        return ffmpeg(cfg, light)
    except RuntimeError:
        raise last


def media_duration(cfg, path):
    try:
        return float(ffprobe_json(cfg, path)["format"]["duration"])
    except Exception:  # noqa: BLE001
        return 1.0


def render_video(cfg, src_video, final_wav, keeps, plan, ass_path, out_mp4, zoom_segments=(), overlay_events=(), content_zoom=(),
                 band_color="0x15151c", seam=None):
    """zoom_segments: [[a, b, nivel 1|2], ...] na webcam; content_zoom: [[a, b], ...] no conteudo;
    overlay_events: [{"t", "file" (mov alpha 1080x1920), "dur"}]; seam: {"mask", "overlap", "y", "divider", "divider_h", "opacity"}."""
    OW, OH = cfg["output"]["width"], cfg["output"]["height"]
    O = cfg["overlays"]
    fps = cfg["output"]["fps"]
    Z1, Z2 = float(O.get("punch_in_zoom", 1.10)), float(O.get("punch_in_zoom2", 1.18))
    work = Path(ass_path).parent
    lines, vcat = _concat_graph(keeps, "0:v", "v")
    fonts = ffpath(Path(cfg["paths"]["assets"]) / "fonts")
    cc = plan["content"]["crop"]
    cs = plan["content"]["scale"]
    total = sum(b - a for a, b in keeps)
    z1 = [[a, b] for a, b, lv in zoom_segments if lv == 1]
    z2 = [[a, b] for a, b, lv in zoom_segments if lv == 2]
    grade = (O.get("webcam_grade") or "").strip()
    seam = seam or {}
    overlap = int(seam.get("overlap") or 0)
    extra_a = []
    if plan.get("webcam"):
        wc = plan["webcam"]["crop"]
        wh = plan["webcam"]["out_h"]
        lines.append(f"[{vcat}]split=2[vw][vc]")
        pre = ",".join(x for x in [O.get("webcam_denoise", ""), grade] if x)
        sharp = O.get("sharpen", "")
        lines.append(f"[vw]crop={wc[2]}:{wc[3]}:{wc[0]}:{wc[1]}{',' + pre if pre else ''},split=3[wA][wB][wC]")
        lines.append(f"[wA]scale={OW}:{wh}:flags=lanczos{',' + sharp if sharp else ''}[zA]")
        cur = "zA"
        for lab, Z, segs, src in (("zB", Z1, z1, "wB"), ("zC", Z2, z2, "wC")):
            zw, zh = int(wc[2] / Z) // 2 * 2, int(wc[3] / Z) // 2 * 2
            zx, zy = (wc[2] - zw) // 2, int((wc[3] - zh) * 0.3)
            lines.append(f"[{src}]crop={zw}:{zh}:{zx}:{zy},scale={OW}:{wh}:flags=lanczos{',' + sharp if sharp else ''}[{lab}]")
            if segs and O.get("punch_in", True):
                nxt = cur + lab
                lines.append(f"[{cur}][{lab}]overlay=0:0:enable='{_enable(segs)}'[{nxt}]")
                cur = nxt
            else:
                lines.append(f"[{lab}]nullsink")
        lines.append(f"[{cur}]null[web]")
        lines.append(f"[vc]crop={cc[2]}:{cc[3]}:{cc[0]}:{cc[1]},scale={cs[0]}:{cs[1]}:flags=lanczos{',' + sharp if sharp else ''}[c0]")
        cz = [[a, b] for a, b in content_zoom]
        if cz and O.get("content_zoom"):
            Zc = float(O["content_zoom"])
            zw, zh = int(cs[0] / Zc) // 2 * 2, int(cs[1] / Zc) // 2 * 2
            sh = int(O.get("shake_px", 10))
            en = _enable(cz)
            lines.append("[c0]split=2[cA][cB]")
            # zoom + tremor (x/y oscilam so durante as janelas)
            lines.append(f"[cB]crop={zw}:{zh}:x='{(cs[0] - zw) // 2}+{sh}*sin(t*43)*({en})':y='{(cs[1] - zh) // 2}+{sh}*cos(t*37)*({en})',scale={cs[0]}:{cs[1]}:flags=lanczos[cZ]")
            lines.append(f"[cA][cZ]overlay=0:0:enable='{en}'[cont]")
        else:
            lines.append("[c0]null[cont]")
        band = plan.get("band") or {}
        if overlap > 0 and seam.get("mask"):
            # emenda irregular: conteudo (com mascara rasgada) sobre a webcam
            mask_mov = _clipe_parado(cfg, seam["mask"], total + 1)
            extra_a = ["-i", str(mask_mov)]
            lines.append(f"[web]pad={OW}:{OH}:0:0:color=black[webfull]")
            lines.append(f"[1:v]format=gray,scale={cs[0]}:{cs[1]}[mask]")
            lines.append("[cont]format=rgba[c_rgba]")
            lines.append("[c_rgba][mask]alphamerge[c_a]")
            lines.append(f"[webfull][c_a]overlay=0:{wh - overlap}:format=auto:shortest=1[stack]")
        elif band.get("h"):
            lines.append(f"color=c={band_color}:s={OW}x{band['h']}:r={fps}:d={total + 2:.2f}[band]")
            lines.append("[web][band][cont]vstack=inputs=3:shortest=1[stack]")
        else:
            lines.append("[web][cont]vstack=inputs=2:shortest=1[stack]")
    else:
        lines.append(f"[{vcat}]crop={cc[2]}:{cc[3]}:{cc[0]}:{cc[1]},scale={cs[0]}:{cs[1]}:flags=lanczos[stack]")
    Oc = cfg["output"]
    low = ["-filter_threads", "1", "-filter_complex_threads", "1"]
    vig = O.get("vignette", "")
    lines.append(f"[stack]{vig + ',' if vig else ''}format=yuv420p[vbase]")
    script_a = work / "video_graph_a.txt"
    script_a.write_text(";\n".join(lines), encoding="utf-8")
    base_mp4 = work / "base.mp4"
    log(f"render A: layout ({len(keeps)} trechos, {len(zoom_segments)} zooms cam, {len(content_zoom)} zooms conteudo, emenda={'rasgada' if overlap else 'reta'})")
    ffmpeg_retry(cfg, ["-threads", "2", "-i", str(src_video), *extra_a, *low, "-filter_complex_script", str(script_a), "-map", "[vbase]", "-an", "-r", str(fps),
                       "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", "-threads", "2",
                       "-x264-params", "rc-lookahead=10:sync-lookahead=0", str(base_mp4)])
    # Passo B: divisoria animada + overlays alpha + legendas ASS + audio final
    lines_b = []
    extra_inputs = []
    cur = "0:v"
    idx = 2
    if seam.get("divider") and plan.get("webcam"):
        extra_inputs += ["-stream_loop", "-1", "-threads", "1", "-i", str(seam["divider"])]
        dh = int(seam.get("divider_h") or 160)
        op = float(seam.get("opacity", 1.0))
        y = int(plan["webcam"]["out_h"] - dh / 2)
        lines_b.append(f"[{idx}:v]format=yuva420p{',colorchannelmixer=aa=' + str(op) if op < 1 else ''}[dv]")
        lines_b.append(f"[{cur}][dv]overlay=0:{y}:shortest=1:format=auto[dvs]")
        cur = "dvs"
        idx += 1
    for i, ev in enumerate(overlay_events):
        nxt = f"ovs{i}"
        if ev.get("png"):
            # imagem estatica (emoji) com pop de escala: entra, cresce e some
            x, y = int(ev.get("x", OW // 2)), int(ev.get("y", OH // 2))
            t0, t1 = ev["t"], ev["t"] + ev["dur"]
            emoji_mov = _clipe_parado(cfg, ev["file"], ev["dur"] + 0.5)
            extra_inputs += ["-i", str(emoji_mov)]
            w = int(ev.get("w", 220))
            lines_b.append(f"[{idx}:v]format=rgba,scale={w}:-1,tpad=start_duration={t0:.3f}:start_mode=add:color=black@0.0[png{i}]")
            lines_b.append(f"[{cur}][png{i}]overlay=x={x - w // 2}:y='{y - w // 2}-30*sin(min((t-{t0:.3f})*8,3.1416))':eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[{nxt}]")
        elif ev.get("video"):
            # video de meme escalado (sem alpha), com borda arredondada simulada por leve sombra; entra com pop
            x, y = int(ev.get("x", OW // 2)), int(ev.get("y", OH // 2))
            w = int(ev.get("w", 600)) // 2 * 2
            t0, t1 = ev["t"], ev["t"] + ev["dur"]
            extra_inputs += ["-threads", "1", "-i", str(ev["file"])]
            lines_b.append(f"[{idx}:v]scale={w}:-2:flags=bicubic,format=yuva420p,tpad=start_duration={t0:.3f}:start_mode=add:color=black@0.0[mv{i}]")
            lines_b.append(f"[{cur}][mv{i}]overlay=x={x - w // 2}:y='{y}-20*sin(min((t-{t0:.3f})*8,3.1416))':eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[{nxt}]")
        elif ev.get("clip"):
            # clipe alpha menor que o quadro (hyperframes), posicionado em x,y
            x, y = int(ev.get("x", 0)), int(ev.get("y", 0))
            extra_inputs += ["-threads", "1", "-i", str(ev["file"])]
            lines_b.append(f"[{idx}:v]format=yuva420p,tpad=start_duration={ev['t']:.3f}:start_mode=add:color=black@0.0[hf{i}]")
            lines_b.append(f"[{cur}][hf{i}]overlay={x}:{y}:eof_action=pass:enable='between(t,{ev['t']:.3f},{ev['t'] + ev['dur']:.3f})'[{nxt}]")
        else:
            extra_inputs += ["-threads", "1", "-i", str(ev["file"])]
            lines_b.append(f"[{idx}:v]format=yuva420p,scale={OW}:{OH},tpad=start_duration={ev['t']:.3f}:start_mode=add:color=black@0.0[ov{i}]")
            lines_b.append(f"[{cur}][ov{i}]overlay=0:0:eof_action=pass:enable='between(t,{ev['t']:.3f},{ev['t'] + ev['dur']:.3f})'[{nxt}]")
        cur = nxt
        idx += 1
    lines_b.append(f"[{cur}]ass={ffpath(ass_path)}:fontsdir={fonts},format=yuv420p[vout]")
    script_b = work / "video_graph_b.txt"
    script_b.write_text(";\n".join(lines_b), encoding="utf-8")
    args = ["-threads", "2", "-i", str(base_mp4), "-i", str(final_wav), *extra_inputs, *low, "-filter_complex_script", str(script_b),
            "-map", "[vout]", "-map", "1:a", "-r", str(fps),
            "-c:v", "libx264", "-preset", Oc["preset"], "-crf", str(Oc["crf"]), "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
            "-threads", str(Oc.get("threads", 2)), "-x264-params", f"rc-lookahead={Oc.get('lookahead', 20)}:sync-lookahead=0",
            "-c:a", "aac", "-b:a", Oc["audio_bitrate"], "-ar", "48000", "-movflags", "+faststart", "-shortest", str(out_mp4)]
    log(f"render B: {Path(out_mp4).name} (divisoria={'sim' if seam.get('divider') else 'nao'}, {len(overlay_events)} overlays + legendas)")
    ffmpeg_retry(cfg, args)
    try:
        base_mp4.unlink()
    except OSError:
        pass
    return out_mp4


def zoom_plan_speech(words, duration, gap=0.6, min_len=0.5, alt_every=4.0):
    """Zoom na webcam enquanto o criador fala, alternando dois niveis. Retorna [[a, b, nivel], ...]."""
    regions = []
    for w in words:
        if regions and w["s"] - regions[-1][1] <= gap:
            regions[-1][1] = max(regions[-1][1], w["e"])
        else:
            regions.append([w["s"], w["e"]])
    out = []
    level = 1
    for a, b in regions:
        if b - a < min_len:
            continue
        t = a
        while t < b:
            e = min(b, t + alt_every)
            out.append([round(t, 3), round(min(e + 0.15, duration), 3), level])
            level = 2 if level == 1 else 1
            t = e
    return out


def zoom_plan(cut_starts, chunk_starts, duration, min_hold=3.5):
    """Modo antigo: alterna punch-in a cada corte / inicio de frase."""
    cut_set = set(round(s, 3) for s in cut_starts)
    bounds = sorted(set(list(cut_set) + [round(c, 3) for c in chunk_starts]))
    segs = []
    state = False
    last_toggle = 0.0
    cur_start = 0.0
    for b in bounds:
        if b <= 0.05 or b >= duration - 0.3:
            continue
        if b in cut_set or (b - last_toggle) >= min_hold:
            if state:
                segs.append([cur_start, b, 1])
            state = not state
            cur_start = b
            last_toggle = b
    if state:
        segs.append([cur_start, duration, 1])
    return segs
