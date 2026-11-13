# -*- coding: utf-8 -*-
"""funil_insta.py — aprendizado do Instagram das empresas (25/10/2026), o mesmo funil do YouTube.

Dono 25/10: "máximo de comentários, visualizações e pessoas procurando os produtos". Cada post (Reel ou carrossel) com
48 h a 21 dias de vida é comparado com a MEDIANA do alcance dos posts do mesmo formato da conta (mín. 4): passou =
vitória (1), igual = meia (0,5), abaixo = 0 — a mesma regra do placar do YouTube (notificar_telegram._vitoria).
Placares comuns (postador\\bin\\placar_titulos.py, _analise\\placar_<nome>.json), 1 contagem por post:
  insta_pautas   grupo "<conta>:reel" / "<conta>:carrossel", item = pauta  -> roteiro_ms/carrossel_ms escolhem a pauta
  insta_formatos grupo "<conta>",                       item = tipo (apresentador, foto_real, video_real, carrossel)
  insta_horarios grupo "<conta>",                       item = faixa de 3 h da publicação
Quem roda: o vigia (MSEnergy_VigiaClientes, a cada 15 min) chama pontuar_dia() 1x por dia. Só leitura na API.
"""
import json
import statistics as st
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CREDS = Path(r"D:\credenciais-canais\instagram_contas.json")
BASE = "https://graph.instagram.com/v21.0"
ESTADO = Path(r"D:\ms-energy\cache\funil_insta.json")
LOG_POSTAGEM = Path(r"D:\ms-energy\videos\postagem_log.json")
PASTAS = [Path(r"D:\ms-energy\videos\shorts_veo"), Path(r"D:\ms-energy\videos\_postados")]
HIST_CARROSSEL = Path(r"D:\ms-energy\cache\historico_carrosseis.json")
JANELA_DIAS = 21
MIN_BASE = 4
FUSO = timedelta(hours=-3)


def _get(path, **params):
    url = path if path.startswith("http") else f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    return json.loads(urllib.request.urlopen(url, timeout=60).read())


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except (OSError, ValueError):
        return padrao


def _vitoria(v, mediana):
    return 1.0 if v > mediana else (0.5 if v == mediana else 0.0)


def _insight(mid, tok, metrica):
    try:
        d = _get(f"{mid}/insights", metric=metrica, access_token=tok)
        return d["data"][0]["values"][0]["value"]
    except Exception:  # noqa: BLE001
        return None


def _pautas_por_post():
    """{(hora_local_iso_min) -> (pauta, tipo)} dos Reels pelo postagem_log + sidecar; {permalink: pauta} dos carrosséis."""
    side = {}
    for pasta in PASTAS:
        for j in pasta.glob("ms_energy_solar_*.json"):
            m = _ler(j, {})
            side[j.stem] = m
    reels = []
    for stem, e in _ler(LOG_POSTAGEM, {}).items():
        try:
            reels.append((datetime.fromisoformat(str(e.get("insta"))[:19]), side.get(stem, {})))
        except (TypeError, ValueError):
            pass
    carross = {h.get("permalink"): h.get("pauta") for h in _ler(HIST_CARROSSEL, []) if h.get("permalink")}
    return reels, carross


def coletar(conta="msenergycap"):
    """Posts da janela com alcance/comentários/salvos/compartilhamentos e a pauta/tipo de cada um."""
    tok = next(c for c in _ler(CREDS, []) if conta in c["name"].lower())["data"]["accessToken"]
    limite = datetime.now(timezone.utc) - timedelta(days=JANELA_DIAS)
    midias, res = [], _get("me/media", fields="id,media_type,media_product_type,timestamp,permalink,comments_count",
                           limit=50, access_token=tok)
    while True:
        midias += res.get("data", [])
        if not res.get("paging", {}).get("next") or (midias and datetime.fromisoformat(
                midias[-1]["timestamp"].replace("+0000", "+00:00")) < limite):
            break
        res = _get(res["paging"]["next"])
    reels, carross = _pautas_por_post()
    posts = []
    for m in midias:
        quando = datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00"))
        if quando < limite:
            continue
        formato = "carrossel" if m.get("media_type") == "CAROUSEL_ALBUM" else (
            "reel" if m.get("media_product_type") == "REELS" else None)
        if not formato:
            continue
        local = quando.replace(tzinfo=None) + FUSO
        pauta, tipo = None, formato
        if formato == "carrossel":
            pauta = carross.get(m.get("permalink"))
        else:
            meta = next((s for t, s in reels if abs((t - local).total_seconds()) < 20 * 60), {})
            pauta = meta.get("pauta")
            tipo = meta.get("tipo_video") or (meta.get("roteiro") or {}).get("tipo") or (
                "ms_v2" if meta.get("pipeline") == "ms_v2" else "antigo")
        posts.append({"id": m["id"], "formato": formato, "tipo": tipo, "pauta": pauta, "link": m.get("permalink"),
                      "hora": local.isoformat(timespec="minutes"),
                      "idade_h": round((datetime.now(timezone.utc) - quando).total_seconds() / 3600, 1),
                      "alcance": _insight(m["id"], tok, "reach") or 0, "comentarios": m.get("comments_count") or 0,
                      "salvos": _insight(m["id"], tok, "saved") or 0, "compart": _insight(m["id"], tok, "shares") or 0})
    return posts


def pontuar(conta="msenergycap", log=print):
    """Registra no placar os posts com >= 48 h ainda não contados. Devolve quantos entraram."""
    if r"D:\postador-de-videos\bin" not in sys.path:
        sys.path.append(r"D:\postador-de-videos\bin")
    import placar_titulos
    estado = _ler(ESTADO, {"pontuados": {}})
    posts = coletar(conta)
    n = 0
    for formato in ("reel", "carrossel"):
        base = sorted(p["alcance"] for p in posts if p["formato"] == formato and p["idade_h"] >= 48)
        if len(base) < MIN_BASE:
            log(f"[funil] {conta} {formato}: {len(base)} post(s) com 48 h (mín. {MIN_BASE}) - espera")
            continue
        med = st.median(base)
        for p in posts:
            if p["formato"] != formato or p["idade_h"] < 48 or p["id"] in estado["pontuados"]:
                continue
            v = _vitoria(p["alcance"], med)
            if p["pauta"]:
                placar_titulos.registrar_item("insta_pautas", f"{conta}:{formato}", p["pauta"], v, f"ig:{p['id']}")
            placar_titulos.registrar_item("insta_formatos", conta, p["tipo"], v, f"igf:{p['id']}")
            h = int(p["hora"][11:13])
            placar_titulos.registrar_item("insta_horarios", conta, f"{h - h % 3:02d}h", v, f"igh:{p['id']}")
            estado["pontuados"][p["id"]] = {**p, "vitoria": v, "mediana": med,
                                            "em": datetime.now().isoformat(timespec="seconds")}
            n += 1
    estado["ultima"] = datetime.now().isoformat(timespec="seconds")
    estado["ultima_lista"] = posts
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(ESTADO)
    log(f"[funil] {conta}: {n} post(s) novos no placar")
    return n


def pontuar_dia(conta="msenergycap", log=print):
    """1x por dia (o vigia roda a cada 15 min)."""
    estado = _ler(ESTADO, {})
    if str(estado.get("ultima", ""))[:10] == datetime.now().strftime("%Y-%m-%d"):
        return 0
    return pontuar(conta, log)


def escolher(candidatas, conta, formato):
    """Entre as pautas candidatas (as mais 'frias' do rodízio), Thompson no placar: pauta que rende sai mais, sem dado
    ainda é testada. candidatas = tuplas (id, ...) do roteiro_ms.PAUTAS."""
    import random
    if r"D:\postador-de-videos\bin" not in sys.path:
        sys.path.append(r"D:\postador-de-videos\bin")
    import placar_titulos
    tx = placar_titulos.taxas("insta_pautas", f"{conta}:{formato}")
    return max(candidatas, key=lambda p: random.betavariate(tx.get(p[0], (0, 0))[1] + 1,
                                                            tx.get(p[0], (0, 0))[0] - tx.get(p[0], (0, 0))[1] + 1))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) > 1 and sys.argv[1] == "ver":
        for p in sorted(coletar(), key=lambda p: p["hora"]):
            print(f"{p['hora']} {p['formato']:9} {str(p['tipo']):12} {str(p['pauta']):14} alcance={p['alcance']:<4} "
                  f"com={p['comentarios']} salvos={p['salvos']} idade={p['idade_h']}h")
    else:
        pontuar()
