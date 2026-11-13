"""CORTES automáticos de vídeo real (dono 25/10: "usando projetos como cortes e Veo"): de cada vídeo do material da
marca sai a lista de trechos bons para Reels, conferidos por visão. Genérico: quem chama passa a pergunta e o
critério (MS Energy: D:\\ms-energy\\bin\\cortes_ms.py).

  1. triagem — 1 quadro do meio do vídeo: nada a ver com a marca = o vídeo inteiro sai (vídeo de família etc.)
  2. cenas   — cortes de cena pelo ffmpeg (select=scene), em resolução baixa (rápido)
  3. janelas — trechos de 3 a 6,5 s dentro de cada cena (cena longa rende até 3 janelas)
  4. visão   — 3 quadros por janela (15 %, 50 %, 85 %); só entra se os 3 passarem no critério
"""
import base64
import json
import re
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
GATEWAY = Path(r"D:\veo\beta\secrets\gateway.json")
JANELA_MIN, JANELA_MAX = 3.0, 6.5
LIMIAR_CENA = 0.32


def info(video):
    """(duração, largura, altura) ou None."""
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", str(video)],
                       capture_output=True, text=True, timeout=60)
    try:
        j = json.loads(r.stdout)
        s = j["streams"][0]
        return float(j["format"]["duration"]), int(s["width"]), int(s["height"])
    except Exception:  # noqa: BLE001
        return None


def quadro(video, t, largura=640):
    return subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf",
                           f"scale={largura}:-2", "-f", "image2", "-vcodec", "mjpeg", "-"],
                          capture_output=True, timeout=90).stdout


def cenas(video, dur):
    """Instantes de corte de cena (s)."""
    r = subprocess.run([FF, "-hide_banner", "-i", str(video), "-an", "-vf",
                        f"scale=320:-2,select='gt(scene,{LIMIAR_CENA})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    cortes = sorted({round(float(m), 2) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)})
    return [0.0] + [c for c in cortes if 0.5 < c < dur - 0.5] + [dur]


def janelas(limites):
    """Trechos de 3–6,5 s dentro de cada cena (folga de 0,3 s nas bordas para não pegar o corte)."""
    out = []
    for a, b in zip(limites, limites[1:]):
        ini, fim = a + 0.3, b - 0.3
        while fim - ini >= JANELA_MIN and len([j for j in out if j[0] >= a]) < 3:
            f = min(ini + JANELA_MAX, fim)
            out.append((round(ini, 2), round(f, 2)))
            ini = f + 0.5
    return out


def visao(jpeg, pergunta, modelo="antigravity/gemini-3-flash"):
    gw = json.loads(GATEWAY.read_text("utf-8"))
    corpo = {"model": modelo, "max_tokens": 400, "temperature": 0.1, "messages": [{"role": "user", "content": [
        {"type": "text", "text": pergunta},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()}}]}]}
    erro = None
    for _ in range(2):
        try:
            req = urllib.request.Request(gw["gateway_url"].rstrip("/") + "/v1/chat/completions",
                                         data=json.dumps(corpo).encode(),
                                         headers={"Authorization": "Bearer " + gw["gateway_key"],
                                                  "Content-Type": "application/json"})
            txt = json.loads(urllib.request.urlopen(req, timeout=90).read())["choices"][0]["message"]["content"]
            return json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
        except Exception as e:  # noqa: BLE001
            erro = f"{type(e).__name__}: {str(e)[:80]}"
    return {"_erro": erro}


def cortar(video, pergunta, aprova, triagem, min_lado=480, workers=4, log=print):
    """Trechos aprovados de um vídeo: [{"inicio", "fim", "visao": [3 respostas]}]. `triagem(resp)` decide se o
    vídeo merece ser cortado (1 quadro); `aprova(resp)` decide cada quadro das janelas."""
    inf = info(video)
    if not inf:
        return {"status": "ilegível", "trechos": []}
    dur, w, h = inf
    if min(w, h) < min_lado:
        return {"status": f"resolução {w}x{h} < {min_lado}", "trechos": []}
    if dur < JANELA_MIN + 0.6:
        return {"status": "curto demais", "trechos": []}
    t0 = visao(quadro(video, dur * 0.5), pergunta)
    if "_erro" in t0:
        return {"status": f"visão indisponível ({t0['_erro']})", "trechos": [], "tentar_de_novo": True}
    if not triagem(t0):
        return {"status": "triagem: não é material da marca", "trechos": [], "triagem": t0}
    js = janelas(cenas(video, dur))
    if not js:
        return {"status": "sem cena longa o bastante", "trechos": []}
    pedidos = [(i, ini + (fim - ini) * f) for i, (ini, fim) in enumerate(js) for f in (0.15, 0.5, 0.85)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        resps = list(ex.map(lambda p: visao(quadro(video, p[1]), pergunta), pedidos))
    trechos = []
    for i, (ini, fim) in enumerate(js):
        rs = resps[i * 3:i * 3 + 3]
        if any("_erro" in r for r in rs):
            continue
        if all(aprova(r) for r in rs):
            trechos.append({"inicio": ini, "fim": fim, "visao": rs})
    return {"status": f"{len(trechos)}/{len(js)} janelas aprovadas", "trechos": trechos, "duracao": dur,
            "resolucao": f"{w}x{h}"}
