"""anime_legenda_fonte.py — o vídeo-fonte tem legenda QUEIMADA? Em que faixa?

Dona 25/10/2026: "se ele não tem legenda não tinha por que ter borrado a tela ... o borrão só deve ir quando há
legenda, e a detecção deve ser boa". Antes: 3 quadros pra IA de visão e, sem um "tem legenda" dela, o rodapé do vídeo
inteiro era borrado — 5 de 6 longos de 21-25/10 saíram borrados sem legenda nenhuma na fonte.

Como decide (só CPU, sem rede): ~100 quadros espalhados pelo vídeo inteiro; em cada um, as LINHAS DE TEXTO
centralizadas (traço de letra: borda forte, altura de linha, muitas hastes lado a lado). Legenda queimada = linha na
MESMA altura em boa parte dos quadros, com texto que MUDA de um quadro pro outro. Balão de mangá/manhwa e texto de cena
aparecem em alturas soltas e não se somam; marca d'água/logo fica parada e é descartada. Na dúvida (presença baixa), a
IA de visão olha quadros onde a linha apareceu; sem resposta dela, NÃO borra.

  detectar(video) -> {"tem": bool, "faixa": [y0, y1] em fração da altura da FONTE | None, "presenca": 0..1, ...}
                     (cache <video>.legenda.json, refeito se o vídeo ou a VERSAO mudar)
"""
import json
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

VERSAO = 1
N_QUADROS = 100
# calibrado 25/10 em 19 fontes reais (9 com legenda, 10 sem: manhwa, gráfico cheio de texto, marca d'água no canto):
# legenda fica centralizada com precisão (desvio mediano <= 1% da largura); balão/texto de cena/gráfico >= 3,6%
PRESENCA_SIM = 0.12    # linha centralizada na mesma faixa em >= 12% dos quadros: legenda (sem perguntar à IA)
PRESENCA_DUVIDA = 0.05  # entre 5% e 12%: a IA de visão decide; abaixo: sem legenda
CENTRO_TOL = 0.03      # centro da linha a até 3% da largura do meio da tela


def _dims(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", str(video)],
                       capture_output=True, text=True, timeout=60)
    d = json.loads(r.stdout)
    return int(d["streams"][0]["width"]), int(d["streams"][0]["height"]), float(d["format"]["duration"])


def _quadro(video, t, w, h):
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                           capture_output=True, timeout=90)
    except subprocess.TimeoutExpired:
        return None
    return np.frombuffer(r.stdout[:w * h], np.uint8).reshape(h, w) if len(r.stdout) >= w * h else None


def _tracos(g):
    """Traço CLARO e fino mais claro que a vizinhança (top-hat): letra de legenda (branca/colorida, com contorno ou
    sombra). Texto escuro em papel claro (balão de manhwa) e áreas claras largas ficam de fora."""
    w = g.shape[1]
    k = max(7, w // 70) | 1
    th = cv2.morphologyEx(g, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    return ((th > 55) & (g > 150)).astype(np.uint8)


def _linhas(g):
    """[(y0, y1, x0, x1), ...] das linhas de texto claro do quadro (cinza, ~640 px)."""
    h, w = g.shape
    tr = _tracos(g)
    m = cv2.morphologyEx(tr, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (max(7, w // 45), 1)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3)))
    _n, _lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    out = []
    for x, y, bw, bh, _area in st[1:]:
        if not (0.018 * h <= bh <= 0.10 * h) or bw < 0.04 * w or bw < 1.6 * bh or bw > 0.95 * w:
            continue
        caixa = tr[y:y + bh, x:x + bw]
        if not 0.08 <= float(caixa.mean()) <= 0.65:
            continue
        # letra = várias hastes lado a lado
        trans = max(int(np.count_nonzero(np.diff(caixa[int(bh * f)].astype(np.int8)) == 1)) for f in (0.35, 0.5, 0.65))
        if trans < 0.6 * bw / bh:
            continue
        out.append((int(y), int(y + bh), int(x), int(x + bw)))
    return out


def _centralizadas(linhas, w):
    return [l for l in linhas if abs((l[2] + l[3]) / 2 - w / 2) <= CENTRO_TOL * w]


def _faixas(por_quadro, h, n=3):
    """Até n faixas [(presença, [b0, b1] px)], da altura onde mais quadros têm linha centralizada pra menos."""
    acum = np.zeros(h)
    for ls in por_quadro:
        mk = np.zeros(h, bool)
        for y0, y1, _x0, _x1 in ls:
            mk[y0:y1] = True
        acum += mk
    out = []
    for _ in range(n):
        pico = int(np.argmax(acum))
        topo = float(acum[pico])
        if topo <= 0:
            break
        b0 = b1 = pico
        while b0 > 0 and acum[b0 - 1] >= 0.3 * topo:
            b0 -= 1
        while b1 < h - 1 and acum[b1 + 1] >= 0.3 * topo:
            b1 += 1
        out.append((topo / max(1, len(por_quadro)), [b0, b1 + 1]))
        acum[b0:b1 + 1] = 0
    return out


def _muda(quadros, por_quadro, faixa, w):
    """Texto da faixa muda entre os quadros? (legenda muda; logo/marca fica igual). Mediana da semelhança (IoU das
    bordas da faixa) entre quadros com linha ali — perto de 1 = parado."""
    b0, b1 = faixa
    mascaras = []
    for g, ls in zip(quadros, por_quadro):
        if any(y0 < b1 and y1 > b0 for y0, y1, _x0, _x1 in ls):
            mascaras.append(_tracos(g)[b0:b1, int(w * 0.15):int(w * 0.85)] > 0)
    if len(mascaras) < 3:
        return True, None
    sims = []
    for a, b in zip(mascaras, mascaras[1:]):
        uniao = np.count_nonzero(a | b)
        sims.append(np.count_nonzero(a & b) / uniao if uniao else 1.0)
    med = float(np.median(sims))
    return med < 0.55, round(med, 3)


def _visao_confirma(video, tempos, faixa_frac):
    """IA de visão olhando até 3 quadros em que a linha apareceu: True/False, ou None se não respondeu."""
    try:
        import tempfile
        import claude_client
        from claude_client import _img_block, is_refusal
    except Exception as e:  # noqa: BLE001
        logging.info(f"[legenda-fonte] visão indisponível ({type(e).__name__})")
        return None
    pasta = Path(tempfile.mkdtemp(prefix="legfonte_"))
    try:
        conteudo = []
        for k, t in enumerate(tempos[:3]):
            jpg = pasta / f"q{k}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-q:v", "3", str(jpg)], capture_output=True, timeout=90)
            if jpg.exists() and jpg.stat().st_size > 500:
                conteudo += [{"type": "text", "text": f"Imagem {k + 1}:"}, _img_block(jpg.read_bytes(), mime="image/jpeg")]
        if not conteudo:
            return None
        conteudo.append({"type": "text", "text": (
            "Cada imagem é um quadro de um vídeo. Responda se há LEGENDA QUEIMADA (texto de tradução/fala sobreposto ao "
            f"vídeo, em faixa horizontal, sempre na mesma altura) entre {faixa_frac[0]:.0%} e {faixa_frac[1]:.0%} da "
            "altura (0% = topo). NÃO conta: balão de fala de mangá/manhwa/quadrinho, placa ou texto que faz parte do "
            "desenho, logo/marca d'água do canal, título fixo. Responda só JSON: "
            '{"legenda": true|false, "quadros_com_legenda": N}')})
        resp = claude_client._post([{"role": "user", "content": conteudo}], max_tokens=120, temperature=0.0)
        if not resp or is_refusal(resp):
            return None
        import re
        m = re.search(r"\{.*\}", str(resp), re.S)
        if not m:
            return None
        d = json.loads(m.group(0))
        return bool(d.get("legenda")) and int(d.get("quadros_com_legenda") or 0) >= 2
    except Exception as e:  # noqa: BLE001
        logging.info(f"[legenda-fonte] visão falhou ({type(e).__name__}: {e})")
        return None
    finally:
        for p in pasta.glob("*"):
            p.unlink(missing_ok=True)
        pasta.rmdir()


def detectar(video, usar_visao=True):
    video = Path(video)
    cache = video.with_name(video.stem + ".legenda.json")
    try:
        d = json.loads(cache.read_text(encoding="utf-8"))
        if d.get("versao") == VERSAO and d.get("tamanho") == video.stat().st_size:
            return d
    except (OSError, ValueError):
        pass
    W, H, dur = _dims(video)
    w = 640 if W >= H else 360
    h = int(round(H * w / W / 2)) * 2
    ini, fim = dur * 0.03, dur * 0.97
    n = max(12, min(N_QUADROS, int((fim - ini) / 2)))
    tempos = [ini + (fim - ini) * (k + 0.5) / n for k in range(n)]
    with ThreadPoolExecutor(4) as ex:
        quadros = list(ex.map(lambda t: _quadro(video, t, w, h), tempos))
    ok = [(t, g) for t, g in zip(tempos, quadros) if g is not None]
    res = {"versao": VERSAO, "tamanho": video.stat().st_size, "tem": False, "faixa": None, "presenca": 0.0,
           "quadros": len(ok), "metodo": "local"}
    if len(ok) < 8:
        logging.warning(f"[legenda-fonte] só {len(ok)} quadros lidos — sem legenda (não borra)")
        res["motivo"] = "quadros insuficientes"
        return res
    _decidir(res, video, [t for t, _ in ok], [g for _, g in ok], usar_visao)
    try:
        cache.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    logging.info(f"[legenda-fonte] {'TEM' if res['tem'] else 'sem'} legenda | faixa {res['faixa']} | presença "
                 f"{res['presenca']:.0%} em {res['quadros']} quadros | {res.get('motivo')}")
    return res


def _decidir(res, video, tempos, quadros, usar_visao=True):
    h, w = quadros[0].shape
    todas = [_linhas(g) for g in quadros]
    res["linhas_por_quadro"] = round(float(np.mean([len(t) for t in todas])), 1)
    if res["linhas_por_quadro"] > 10:  # gráfico/lista/documento: texto pra todo lado (fontes com legenda: <= 7)
        res["motivo"] = "tela cheia de texto (gráfico/lista), não é legenda"
        return []
    por_quadro = [_centralizadas(ls, w) for ls in todas]
    # a faixa mais repetida pode ser um título fixo do canal (parado): aí vale a próxima
    pres, faixa, paradas = 0.0, None, []
    for p, f in _faixas(por_quadro, h, n=5):
        if p < PRESENCA_DUVIDA:
            break
        if (f[1] - f[0]) > 0.2 * h:
            continue
        muda, sim = _muda(quadros, por_quadro, f, w)
        if not muda:
            paradas.append([round(f[0] / h, 3), round(f[1] / h, 3)])
            continue
        if faixa is None:
            pres, faixa = p, list(f)
            res["semelhanca"] = sim
        elif p >= 0.4 * pres and min(abs(f[0] - faixa[1]), abs(faixa[0] - f[1])) <= 0.08 * h \
                and max(f[1], faixa[1]) - min(f[0], faixa[0]) <= 0.24 * h:
            # legenda em 2 alturas (cena com tarja preta x tela cheia, 1 x 2 linhas): cobre as duas
            faixa = [min(f[0], faixa[0]), max(f[1], faixa[1])]
    if paradas:
        res["texto_parado"] = paradas  # logo/marca/título fixo: não é legenda, não borra
    res["presenca"] = round(pres, 3)
    if not faixa:
        res["motivo"] = "sem linha de texto que muda repetida na mesma altura"
    else:
        res["faixa_px"] = faixa
        res["altura"] = round((faixa[1] - faixa[0]) / h, 3)
        frac = [round(faixa[0] / h, 4), round(faixa[1] / h, 4)]
        if pres >= PRESENCA_SIM:
            res.update(tem=True, faixa=frac, motivo="linha de texto na mesma altura, mudando")
        else:
            com = [t for t, ls in zip(tempos, por_quadro) if any(y0 < faixa[1] and y1 > faixa[0] for y0, y1, _a, _b in ls)]
            v = _visao_confirma(video, [com[len(com) // 4], com[len(com) // 2], com[3 * len(com) // 4]], frac) \
                if usar_visao and len(com) >= 3 else None
            res["visao"] = v
            res["metodo"] = "local+visao"
            if v:
                res.update(tem=True, faixa=frac, motivo="presença baixa, visão confirmou")
            else:
                res["motivo"] = "presença baixa e a visão não confirmou" if v is False else "presença baixa, sem visão: não borra"
    return por_quadro


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for v in (a for a in sys.argv[1:] if not a.startswith("--")):
        print(v, json.dumps(detectar(v, usar_visao="--sem-visao" not in sys.argv), ensure_ascii=False))
