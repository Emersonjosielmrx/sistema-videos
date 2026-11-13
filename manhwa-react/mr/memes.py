"""Memes em imagem/video do acervo (memes_img): catalogo com descricao por visao (LLM), escolha pelo editorial e plano de overlay + som."""
import base64
import json
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from .common import log, ffprobe_json, ffmpeg

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
VID_EXT = {".mp4", ".gif", ".webm", ".mov"}

DESC_PROMPT = ("Descreva este meme em portugues do Brasil para um editor de videos de react escolher quando usa-lo. Responda SOMENTE um JSON: "
               '{"desc": "o que aparece e a emocao/uso em ate 15 palavras", "tags": ["3 a 6 tags curtas: emocao, situacao"], '
               '"uso": "quando usar (ex.: quando algo da errado, quando o criador fica chocado)", "ok": true}. '
               '"ok": false se for impróprio para YouTube (nudez, violencia explicita, palavrao escrito, simbolo ofensivo) ou se nao for um meme utilizavel.')


def _catalog_path(cfg):
    return Path(cfg["paths"]["assets"]) / "memes_catalogo.json"


def _lib(cfg):
    return Path(cfg["paths"].get("memes_library", ""))


def _all_files(cfg):
    lib = _lib(cfg)
    out = []
    if not lib.exists():
        return out
    for p in sorted(lib.rglob("*")):
        if p.is_file() and p.suffix.lower() in IMG_EXT | VID_EXT:
            out.append(p)
    return out


def _thumb_jpeg(cfg, p, size=512):
    """JPEG pequeno (bytes) do meme: imagem direta ou frame do meio do video/gif."""
    tmp = Path(tempfile.gettempdir()) / f"mr_meme_{abs(hash(str(p)))}.jpg"
    if p.suffix.lower() in VID_EXT:
        try:
            d = float(ffprobe_json(cfg, p)["format"].get("duration", 1.0))
        except Exception:  # noqa: BLE001
            d = 1.0
        subprocess.run([cfg["paths"]["ffmpeg"], "-y", "-loglevel", "error", "-ss", f"{min(d * 0.4, 3.0):.2f}", "-i", str(p), "-frames:v", "1",
                        "-vf", f"scale={size}:-2", str(tmp)], check=False)
    else:
        subprocess.run([cfg["paths"]["ffmpeg"], "-y", "-loglevel", "error", "-i", str(p), "-frames:v", "1", "-vf", f"scale={size}:-2", str(tmp)], check=False)
    if not tmp.exists():
        return None
    b = tmp.read_bytes()
    tmp.unlink(missing_ok=True)
    return b


def _describe(cfg, jpeg_bytes, model_tier="haiku"):
    from .llm import _proxy, extract_json
    px = _proxy(cfg)
    base = (px.get("base_url") or "").rstrip("/")
    key = px.get("auth_token")
    models = dict(cfg["editorial"].get("models", {}))
    models.update({k: v for k, v in (px.get("models") or {}).items() if v})
    model = models.get(model_tier) or models.get("sonnet")
    if not base or not key or not model:
        return None
    body = {"model": model, "max_tokens": 300, "temperature": 0.2,
            "messages": [{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(jpeg_bytes).decode()}},
                {"type": "text", "text": DESC_PROMPT}]}]}
    req = urllib.request.Request(base + "/v1/messages", data=json.dumps(body).encode("utf-8"),
                                 headers={"x-api-key": key, "Authorization": f"Bearer {key}", "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=120)
        d = json.loads(r.read().decode("utf-8"))
        text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
        return extract_json(text)
    except Exception as e:  # noqa: BLE001
        log(f"memes: descricao falhou ({str(e)[:100]})")
        return None


def build_catalog(cfg, limit=None, tier="haiku"):
    """Descreve cada meme uma vez (cache em assets/memes_catalogo.json)."""
    path = _catalog_path(cfg)
    cat = json.load(open(path, encoding="utf-8")) if path.exists() else {}
    files = _all_files(cfg)
    todo = [p for p in files if str(p) not in cat]
    if limit:
        todo = todo[:limit]
    log(f"memes: {len(files)} arquivos, {len(todo)} para descrever")
    for i, p in enumerate(todo):
        entry = {"file": str(p), "kind": "video" if p.suffix.lower() in VID_EXT else "image"}
        if entry["kind"] == "video":
            try:
                entry["duration"] = round(float(ffprobe_json(cfg, p)["format"].get("duration", 0)), 2)
                entry["has_audio"] = any(s["codec_type"] == "audio" for s in ffprobe_json(cfg, p)["streams"])
            except Exception:  # noqa: BLE001
                entry["duration"], entry["has_audio"] = 0, False
        jb = _thumb_jpeg(cfg, p)
        d = _describe(cfg, jb, tier) if jb else None
        if d:
            entry.update({"desc": str(d.get("desc", ""))[:160], "tags": [str(t)[:30] for t in (d.get("tags") or [])][:6],
                          "uso": str(d.get("uso", ""))[:160], "ok": bool(d.get("ok", True))})
        else:
            entry.update({"desc": "", "tags": [], "uso": "", "ok": False})
        cat[str(p)] = entry
        if (i + 1) % 10 == 0:
            json.dump(cat, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            log(f"memes: {i + 1}/{len(todo)} descritos")
    json.dump(cat, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for e in cat.values() if e.get("ok"))
    log(f"memes: catalogo com {len(cat)} itens ({ok} aprovados)")
    return cat


def load_catalog(cfg):
    path = _catalog_path(cfg)
    if not path.exists():
        return {}
    return json.load(open(path, encoding="utf-8"))


def catalog_for_prompt(cfg, max_items=160):
    """Lista compacta [id] desc (tags) para o editorial escolher."""
    cat = load_catalog(cfg)
    items = []
    for i, (f, e) in enumerate(cat.items()):
        if not e.get("ok") or not e.get("desc"):
            continue
        if e.get("kind") == "video" and (e.get("duration") or 0) > 8:
            continue
        items.append({"id": i, "file": f, "desc": e["desc"], "tags": e.get("tags", []), "kind": e.get("kind"), "duration": e.get("duration", 0),
                      "has_audio": e.get("has_audio", False)})
    items = items[:max_items]
    text = "\n".join(f"[{it['id']}] {'VIDEO ' if it['kind'] == 'video' else ''}{it['desc']} ({', '.join(it['tags'])})" for it in items)
    return items, text


def _meme_audio(cfg, p, max_s):
    """Extrai o audio do meme em wav (48k estereo) limitado a max_s. None se nao tiver audio."""
    out = Path(cfg["paths"]["assets"]) / "memes_audio" / (Path(p).stem + ".wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        return out
    res = subprocess.run([cfg["paths"]["ffmpeg"], "-y", "-loglevel", "error", "-i", str(p), "-vn", "-t", f"{max_s:.2f}", "-ac", "2", "-ar", "48000", str(out)], check=False)
    return out if (res.returncode == 0 and out.exists()) else None


def _como_png(cfg, p):
    """.avif/.webp nao abrem com -loop 1 no ffmpeg desta maquina: converte uma vez para PNG (cache em assets/memes_png)."""
    if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
        return p
    dst = Path(cfg["paths"]["assets"]) / "memes_png" / (p.stem + ".png")
    if dst.exists():
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
        Image.open(p).convert("RGBA").save(dst)
        return dst
    except Exception:  # noqa: BLE001
        try:
            ffmpeg(cfg, ["-y", "-i", str(p), "-frames:v", "1", str(dst)])
            return dst if dst.exists() else None
        except Exception as e:  # noqa: BLE001
            log(f"memes: {p.name} nao converteu para PNG ({e}) - pulado")
            return None


def plan_memes(cfg, choices, items_by_id, timeline, duration, plan):
    """choices: [{"t": seg_original, "id": int}] -> overlays (png/video) e sfx (audio do meme)."""
    O = cfg["overlays"]
    OW = cfg["output"]["width"]
    overlays, sfx = [], []
    w = int(OW * float(O.get("meme_width_pct", 0.62)))
    content_top = plan["content"]["out_y"] + plan["seam"]["overlap"] if plan.get("seam") else plan["content"]["out_y"]
    y = content_top + 60
    used = 0
    for ch in choices or []:
        if used >= int(O.get("memes_max", 2)):
            break
        try:
            t0 = float(ch["t"])
            it = items_by_id[int(ch["id"])]
        except Exception:
            continue
        if not timeline.inside(t0):
            continue
        t = timeline.map(t0)
        if t >= duration - 1.5:
            continue
        p = Path(it["file"])
        if it["kind"] == "video":
            d = min(float(it.get("duration") or 2.0), float(O.get("meme_video_max_s", 4.0)))
            overlays.append({"t": t, "file": p, "dur": d, "video": True, "x": OW // 2, "y": y, "w": w})
            if it.get("has_audio") and cfg["sfx"].get("enabled"):
                wav = _meme_audio(cfg, p, d)
                if wav:
                    sfx.append({"t": t, "file": wav, "gain_db": float(cfg["sfx"].get("meme_gain_db", -9))})
        else:
            p = _como_png(cfg, p)
            if not p:
                continue
            overlays.append({"t": t, "file": p, "dur": float(O.get("meme_seconds", 2.2)), "png": True, "x": OW // 2, "y": y + w // 3, "w": w})
        used += 1
    if used:
        log(f"memes: {used} inserido(s)")
    return overlays, sfx
