"""Capas dos canais de referência da dona (30/10): pelo feed público de cada canal (RSS: últimos 15 vídeos com views,
sem yt-dlp, 1 pedido por canal) baixa as capas dos mais vistos e monta uma folha por canal pra estudar.
Saída: D:\\hipercool-materiais\\engenharia_reversa\\capas_referencia\\<canal>\\ (feed.json, <id>.jpg, _folha.jpg).

    python capas_referencia.py [--top 4]
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SAIDA = Path(r"D:\hipercool-materiais\engenharia_reversa\capas_referencia")
# dona 30/10: "zeni, porão, doinsuka, debox, the king h, noi manhwa, manhwa trigger; e o AmericanNickas: as frases e
# como ele cola as frases"
CANAIS = {
    "zenimanwhasrecap": "UCvQdWLm2xVn7GLBE4HCWfaw", "oporaodacidadela": "UCHB79PoT2ZHRONRJjDHBASA",
    "Doinsuka": "UCjc2Ej-dZofUjJ-1TQYKwjQ", "deboxkkj": "UC6DfHPseI3hdCuzxQv3DP_g",
    "TheKingH05": "UCWLSTLaFPGP5qOF3asBCP0A", "NoiManhwa": "UClhsv2mQpKxgN2SreRf2sXg",
    "Manhwatriggerr": "UCgZdMdU3AtxNIjV_buQArlA", "AmericanNickas": "UC_IKjwwAWNdo1k2fQV_mQBA",
}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def feed(cid):
    xml = _get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}").decode("utf-8", "replace")
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        vid = re.search(r"<yt:videoId>([^<]+)", e)
        tit = re.search(r"<title>([^<]*)", e)
        v = re.search(r'views="(\d+)"', e)
        pub = re.search(r"<published>([^<]+)", e)
        if vid:
            out.append({"id": vid.group(1), "titulo": (tit.group(1) if tit else "").replace("&amp;", "&"),
                        "views": int(v.group(1)) if v else 0, "publicado": pub.group(1) if pub else ""})
    return out


def capa(vid, destino):
    if destino.exists() and destino.stat().st_size > 5000:
        return True
    for nome in ("maxresdefault", "sddefault", "hqdefault"):
        try:
            b = _get(f"https://i.ytimg.com/vi/{vid}/{nome}.jpg")
            if len(b) > 5000:
                destino.write_bytes(b)
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


def folha(pasta, itens):
    from PIL import Image, ImageDraw, ImageFont
    ims = [(i, Image.open(pasta / f"{i['id']}.jpg").convert("RGB").resize((640, 360))) for i in itens
           if (pasta / f"{i['id']}.jpg").exists()]
    if not ims:
        return None
    cols = 2
    W, H = 640 * cols, 400 * ((len(ims) + cols - 1) // cols)
    f = Image.new("RGB", (W, H), (20, 20, 20))
    d = ImageDraw.Draw(f)
    try:
        fonte = ImageFont.truetype(r"D:\hipercool-materiais\assets\fonts\Montserrat-ExtraBold.ttf", 20)
    except OSError:
        fonte = ImageFont.load_default()
    for k, (i, im) in enumerate(ims):
        x, y = 640 * (k % cols), 400 * (k // cols)
        f.paste(im, (x, y))
        d.text((x + 8, y + 366), f"{i['views']:,} views · {i['titulo'][:48]}", font=fonte, fill=(255, 255, 255))
    out = pasta / "_folha.jpg"
    f.save(out, quality=85)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=4)
    a = ap.parse_args()
    for nome, cid in CANAIS.items():
        pasta = SAIDA / nome
        pasta.mkdir(parents=True, exist_ok=True)
        try:
            itens = feed(cid)
        except Exception as e:  # noqa: BLE001
            print(f"{nome}: feed falhou ({type(e).__name__}: {e})")
            continue
        (pasta / "feed.json").write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
        top = sorted(itens, key=lambda i: -i["views"])[:a.top]
        for i in top:
            capa(i["id"], pasta / f"{i['id']}.jpg")
        print(f"{nome}: {len(itens)} vídeos no feed, top {[i['views'] for i in top]} -> {folha(pasta, top)}")
        time.sleep(2)


if __name__ == "__main__":
    main()
