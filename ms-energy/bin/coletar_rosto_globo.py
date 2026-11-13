# -*- coding: utf-8 -*-
r"""Fotos-base do CLONE do dono da Globo Solar (dona 31/10/2026: "esse é o dono da Globo, colete as fotos dele no insta
e faça o avatar dele pra fazer as postagens de clone").

Referência: a foto que a dona mandou (assets\globo\referencia\dono_foto_enviada.png). Lê os posts do
@globosolarenergiag (só leitura, poucas páginas), baixa imagens e vídeos dos Reels, tira quadros, acha os rostos com o
mesmo detector/reconhecedor do foto_na_hora (YuNet + SFace) e guarda só os que batem com a referência (cosseno >= 0,50),
recortados em retrato, nos mais nítidos e variados. Saída: assets\globo\clone_bases\dono_base_N.jpg (+ _candidatos).
    D:\veo\venv\Scripts\python.exe coletar_rosto_globo.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, r"D:\veo\beta")
sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
import foto_na_hora as fh  # noqa: E402
from services.instagram.web import InstagramWeb  # noqa: E402

CONTA = "globosolarenergiag"
RAIZ = Path(r"D:\ms-energy\assets\globo")
REF = RAIZ / "referencia" / "dono_foto_enviada.png"
BRUTO = RAIZ / "instagram_midia"
SAIDA = RAIZ / "clone_bases"
CAND = SAIDA / "_candidatos"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
LIMIAR = 0.50
PAGINAS = 4


def midias(ig):
    m = ig.modelos["PolarisProfilePostsQuery"]
    v = ig._variaveis(m, username=CONTA, count=12)
    out, depois = [], None
    for _ in range(PAGINAS):
        if depois:
            v["after"] = depois
        d = ig.graphql("PolarisProfilePostsQuery", v)
        conn = next((x for x in d.values() if isinstance(x, dict) and "edges" in x), {})
        for e in conn.get("edges", []):
            n = e.get("node", {})
            for i, f in enumerate(n.get("carousel_media") or [n]):
                vids = f.get("video_versions") or []
                imgs = (f.get("image_versions2") or {}).get("candidates") or []
                if vids:
                    out.append((f"{n.get('code')}_{i}.mp4", vids[0]["url"]))
                elif imgs:
                    c = max(imgs, key=lambda c: (c.get("width") or 0) * (c.get("height") or 0))
                    out.append((f"{n.get('code')}_{i}.jpg", c["url"]))
        pi = conn.get("page_info") or {}
        depois = pi.get("end_cursor")
        if not pi.get("has_next_page") or not depois:
            break
        time.sleep(4)
    return out


def quadros(arq):
    """Imagens (BGR) a analisar: a foto, ou 1 quadro a cada 1,5 s do vídeo (até 40)."""
    if arq.suffix == ".jpg":
        return [(arq.stem, fh._ler(str(arq)))]
    pasta = BRUTO / "_q" / arq.stem
    pasta.mkdir(parents=True, exist_ok=True)
    if not any(pasta.iterdir()):
        subprocess.run([FFMPEG, "-v", "error", "-i", str(arq), "-vf", "fps=1/1.5", "-frames:v", "40",
                        str(pasta / "q_%03d.jpg")], timeout=300, creationflags=0x08000000)
    return [(f"{arq.stem}_{p.stem}", fh._ler(str(p))) for p in sorted(pasta.glob("q_*.jpg"))]


def nitidez(img):
    return float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())


def recorte(img, caixa):
    """Retrato 4:5 com o rosto no terço de cima (cabeça + ombros)."""
    h, w = img.shape[:2]
    x, y, bw, bh = caixa
    lado = int(bh * 3.2)
    cw, ch = int(lado * 0.8), lado
    cx, cy = x + bw // 2, y + bh // 2
    x0, y0 = max(0, cx - cw // 2), max(0, cy - int(ch * 0.35))
    x1, y1 = min(w, x0 + cw), min(h, y0 + ch)
    return img[y0:y1, x0:x1]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ref = fh.rostos(str(REF))
    if not ref:
        print("ERRO: nenhum rosto na foto de referência")
        return 1
    emb_ref = ref[0][0]
    BRUTO.mkdir(parents=True, exist_ok=True)
    CAND.mkdir(parents=True, exist_ok=True)
    ig = InstagramWeb(CONTA)
    lista = midias(ig)
    print(f"mídias no perfil (até {PAGINAS} páginas): {len(lista)}")
    for nome, url in lista:
        dst = BRUTO / nome
        if dst.exists():
            continue
        r = ig.s.get(url, timeout=120)
        if r.status_code == 200:
            dst.write_bytes(r.content)
        time.sleep(1)
    achados = []
    for arq in sorted(BRUTO.glob("*.*")):
        if arq.suffix not in (".jpg", ".mp4"):
            continue
        for nome, img in quadros(arq):
            for emb, area, caixa, giro in fh.rostos(img):
                if caixa[3] < 90:  # rosto pequeno demais para servir de base
                    continue
                nota = float(emb_ref @ emb)
                if nota >= LIMIAR:
                    rec = recorte(img, caixa)
                    achados.append({"nome": nome, "post": arq.stem.split("_")[0], "nota": nota, "giro": giro,
                                    "alt": caixa[3], "nitidez": nitidez(rec), "emb": emb, "img": rec})
    print(f"rostos do dono achados: {len(achados)} em {len({a['post'] for a in achados})} post(s)")
    # mais nítidos e variados: no máximo 2 por post e nada quase idêntico ao já escolhido
    achados.sort(key=lambda a: (a["nota"] * 2 + min(a["nitidez"], 400) / 400 + min(a["alt"], 400) / 400), reverse=True)
    escolhidos, por_post = [], {}
    for a in achados:
        if por_post.get(a["post"], 0) >= 2:
            continue
        if any(float(a["emb"] @ e["emb"]) > 0.93 for e in escolhidos):
            continue
        escolhidos.append(a)
        por_post[a["post"]] = por_post.get(a["post"], 0) + 1
        if len(escolhidos) >= 10:
            break
    for p in CAND.glob("*.jpg"):
        p.unlink()
    for i, a in enumerate(escolhidos, 1):
        cv2.imencode(".jpg", a["img"], [cv2.IMWRITE_JPEG_QUALITY, 95])[1].tofile(str(CAND / f"cand_{i:02d}.jpg"))
        print(f"cand_{i:02d}: {a['nome']} nota={a['nota']:.2f} giro={a['giro']:.2f} rosto={a['alt']}px "
              f"nitidez={a['nitidez']:.0f}")
    (CAND / "_lista.json").write_text(json.dumps([{k: v for k, v in a.items() if k not in ("emb", "img")}
                                                  for a in escolhidos], ensure_ascii=False, indent=1), "utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
