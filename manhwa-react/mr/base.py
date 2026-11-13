"""Video base de um react (o video original que o criador assiste na gravacao).

Preparar o base antes da gravacao chegar permite, no react:
- trocar a captura de tela pelo original em qualidade cheia (sincronizado pelo audio);
- saber o que e narracao do video e o que e fala do criador (a transcricao do base e a narracao);
- cortar/escolher momentos pelas mudancas de cena (paineis do manhwa).

Saidas em bases/<id>/: base.mp4, base.info.json, base.jpg/webp, audio16k.wav, transcript.json, cenas.json, base.json (resumo).
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from .common import log, load_json, save_json, ffprobe_json, run


def _bases_dir(cfg):
    return Path(cfg["paths"].get("bases", Path(cfg["paths"]["work"]).parent / "bases"))


def _video_id(fonte):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", fonte)
    return m.group(1) if m else re.sub(r"[^\w-]+", "_", Path(fonte).stem)[:40]


def baixar(cfg, url, pasta):
    """yt-dlp do venv do projeto (versao nova + node para o desafio JS do YouTube); H.264 ate 1080p."""
    mp4 = pasta / "base.mp4"
    if mp4.exists():
        return mp4
    ff = str(Path(cfg["paths"]["ffmpeg"]).parent)
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--js-runtimes", "node", "--ffmpeg-location", ff,
           "-f", "bestvideo[height<=1080][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio",
           "--merge-output-format", "mp4", "--write-info-json", "--write-thumbnail", "-o", str(pasta / "base.%(ext)s"), url]
    log(f"base: baixando {url}")
    from . import ytdlp_vez  # COMUM: 1 yt-dlp por vez no PC (rajada bloqueou o IP da casa)
    with ytdlp_vez.vez("react: base"):
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0 or not mp4.exists():
        raise RuntimeError(f"download falhou: {(res.stderr or res.stdout)[-600:]}")
    return mp4


def cenas(cfg, mp4, limiar=0.2):
    """Mudancas de cena (scdet) em versao reduzida a 5 fps: lista de (tempo, score)."""
    res = run([cfg["paths"]["ffmpeg"], "-hide_banner", "-nostats", "-threads", "2", "-i", str(mp4), "-an",
               "-vf", f"fps=5,scale=320:-2,scdet=threshold={limiar * 100:.0f}", "-f", "null", "-"], check=False)
    out = [{"t": float(t), "score": float(s)} for s, t in re.findall(r"lavfi\.scd\.score:\s*([\d.]+),\s*lavfi\.scd\.time:\s*([\d.]+)", res.stderr)]
    if not out:  # formato alternativo do log do scdet
        out = [{"t": float(t), "score": float(s)} for t, s in re.findall(r"scd\.time[:=]\s*([\d.]+).*?scd\.score[:=]\s*([\d.]+)", res.stderr)]
    return out


def _norm(w):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(w).lower())
    return re.sub(r"[^a-z0-9]+", "", "".join(c for c in t if not unicodedata.combining(c)))


def _trigramas(words):
    ws = [_norm(w["w"]) for w in words]
    return {tuple(ws[i:i + 3]) for i in range(len(ws) - 2) if all(ws[i:i + 3])}


def achar_base(cfg, words, min_overlap=0.12):
    """Qual video base preparado aparece nesta gravacao: o que tem mais narracao em comum (trigramas de palavras).
    Retorna (pasta, resumo, transcricao, overlap) ou None."""
    rec = _trigramas(words)
    if not rec:
        return None
    best = None
    for tp in _bases_dir(cfg).glob("*/transcript.json"):
        tx = load_json(tp)
        ov = len(rec & _trigramas(tx["words"])) / len(rec)
        if best is None or ov > best[3]:
            resumo = load_json(tp.parent / "base.json") if (tp.parent / "base.json").exists() else {"id": tp.parent.name}
            best = (tp.parent, resumo, tx, ov)
    if best and best[3] >= min_overlap:
        log(f"base: gravacao reage a '{best[1].get('titulo') or best[1]['id']}' ({best[3]:.0%} dos trigramas batem)")
        return best
    return None


def marcar_narracao(words, segments, base_words, janela=3):
    """speaker por palavra: 'content' quando a palavra faz parte da narracao do base (trigrama em comum, suavizado
    numa janela de +-janela palavras), 'creator' no resto. Segmento = maioria das palavras."""
    bt = _trigramas(base_words)
    ws = [_norm(w["w"]) for w in words]
    hit = [False] * len(words)
    for i in range(len(ws) - 2):
        if tuple(ws[i:i + 3]) in bt:
            hit[i] = hit[i + 1] = hit[i + 2] = True
    for i, w in enumerate(words):
        win = hit[max(0, i - janela):i + janela + 1]
        w["speaker"] = "content" if sum(win) * 2 > len(win) else "creator"
    for s in segments:
        votes = [w["speaker"] for w in words if s["start"] - 0.01 <= w["s"] <= s["end"] + 0.01]
        if votes:
            s["speaker"] = "content" if votes.count("content") * 2 > len(votes) else "creator"
    n_c = sum(1 for w in words if w["speaker"] == "creator")
    log(f"base: fala do criador = {n_c}/{len(words)} palavras (resto e narracao do video base)")


def preparar(cfg, fonte, refazer=False):
    from . import transcribe as T
    vid = _video_id(fonte)
    pasta = _bases_dir(cfg) / vid
    pasta.mkdir(parents=True, exist_ok=True)
    mp4 = baixar(cfg, fonte, pasta) if re.match(r"https?://", fonte) else Path(fonte)
    info = load_json(pasta / "base.info.json") if (pasta / "base.info.json").exists() else {}
    pr = ffprobe_json(cfg, mp4)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    dur = float(pr["format"]["duration"])

    wav = pasta / "audio16k.wav"
    if refazer or not wav.exists():
        log("base: extraindo audio 16 kHz mono")
        run([cfg["paths"]["ffmpeg"], "-hide_banner", "-y", "-loglevel", "error", "-i", str(mp4), "-vn", "-ac", "1", "-ar", "16000",
             "-c:a", "pcm_s16le", str(wav)])

    tx_path = pasta / "transcript.json"
    if refazer or not tx_path.exists():
        log("base: transcrevendo a narracao do video base")
        save_json(T.transcribe(cfg, wav), tx_path)
    tx = load_json(tx_path)

    cenas_path = pasta / "cenas.json"
    if refazer or not cenas_path.exists():
        log("base: detectando mudancas de cena (alguns minutos)")
        save_json(cenas(cfg, mp4), cenas_path)
    sc = load_json(cenas_path)

    resumo = {"id": vid, "fonte": fonte, "arquivo": str(mp4), "titulo": info.get("title"), "canal": info.get("channel"),
              "url": info.get("webpage_url") or (fonte if fonte.startswith("http") else None),
              "duracao": round(dur, 2), "largura": int(v["width"]), "altura": int(v["height"]),
              "fps": v.get("r_frame_rate"), "palavras_narracao": len(tx["words"]), "cenas": len(sc),
              "descricao": (info.get("description") or "")[:1500], "tags": info.get("tags") or []}
    save_json(resumo, pasta / "base.json")
    log(f"base pronta: {resumo['titulo']} | {dur / 60:.1f} min {resumo['largura']}x{resumo['altura']} | "
        f"{resumo['palavras_narracao']} palavras de narracao | {resumo['cenas']} cortes de cena -> {pasta}")
    return resumo
