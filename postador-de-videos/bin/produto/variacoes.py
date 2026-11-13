"""Agente de VARIAÇÕES dos vídeos de produto (dono 25/10: "vamos variar e ver quais dão mais visualizações; tem que
ter um agente inteligente como o dos cortes que vê as visualizações e vai indo melhor das variações").

Variações (o que muda no vídeo):
  dono_abre_fecha  — o dono abre (bloco 1) e fecha (bloco 3), em cenários diferentes
  dono_mesma_foto  — abre e fecha, as duas cenas da MESMA foto dele
  dono_uma_cena    — o dono só abre
  sem_dono         — só narradora + imagens/conversa

Como aprende (mesmo método do placar_titulos.py: Thompson): cada vídeo postado há >= 48 h é medido (views do Reel
pela API do Instagram); "sucesso" = views >= mediana dos vídeos de produto DAQUELA conta. A variação é sorteada pela
Beta(1+sucessos, 1+fracassos) de cada uma — no começo experimenta todas, depois puxa a que rende mais. Conta pelo
navegador (sem token) ainda não é medida: entra só quando tiver métrica.

    python -m produto.variacoes medir      # atualiza as views (tarefa diária chama antes de produzir)
    python -m produto.variacoes placar     # mostra o placar
"""
import json
import random
import statistics
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

BIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
RAIZ = BIN.parent
PLACAR = RAIZ / "config" / "produto_variacoes.json"
FILA = Path(r"D:\video-fila\produto_fila")

# 26/10 (dono: "formatos diferentes, com 2 Veo3, 3 Veo3 e assim por diante"): veo_broll = blocos com cena comercial
# do Veo SEM o dono; total de Veo = cenas do dono + veo_broll
VARIANTES = {
    "dono_uma_cena": {"com_veo": True, "cenas": [1], "mesma_foto": False},                          # 1 Veo
    "dono_abre_fecha": {"com_veo": True, "cenas": [1, 3], "mesma_foto": False},                     # 2 Veo
    "dono_mesma_foto": {"com_veo": True, "cenas": [1, 3], "mesma_foto": True},                      # 2 Veo
    "dono_e_cena_veo": {"com_veo": True, "cenas": [1], "veo_broll": [3], "mesma_foto": False},      # 2 Veo
    "dono_tres": {"com_veo": True, "cenas": [1, 2, 3], "mesma_foto": False},                        # 3 Veo
    "dono_abre_fecha_veo_meio": {"com_veo": True, "cenas": [1, 3], "veo_broll": [2], "mesma_foto": False},  # 3 Veo
    # 26/10 19:40 (dono: "ficou bom com 2 Veo, podemos fazer com 3 em diante"): Veo atrás dos cartões
    "dono_tres_veo_final": {"com_veo": True, "cenas": [1, 2, 3], "veo_cartao": True, "mesma_foto": False},  # 4 Veo
    "quatro_veo": {"com_veo": True, "cenas": [1, 3], "veo_broll": [2], "veo_cartao": True,
                   "mesma_foto": False},                                                                 # 4 Veo
    "cinco_veo": {"com_veo": True, "cenas": [1, 3], "veo_broll": [2], "veo_cartao": True, "veo_abertura": True,
                  "mesma_foto": False},                                                                  # 5 Veo
    "sem_dono": {"com_veo": False, "cenas": [], "mesma_foto": False},                               # 0 Veo
}


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return padrao


def variante_real(side):
    """O que o vídeo REALMENTE teve (Veo falhou = 'sem_dono' mesmo tendo pedido o dono)."""
    feitas = side.get("cenas_dono_feitas") or []
    broll = side.get("veo_broll_feitos") or []
    extra = set(side.get("veo_extra_feitos") or [])
    for nome, v in VARIANTES.items():  # saiu exatamente como a variação pedia
        pedidos = {x for x, f in (("abertura", "veo_abertura"), ("cartao", "veo_cartao")) if v.get(f)}
        if (sorted(v["cenas"]) == sorted(feitas) and sorted(v.get("veo_broll", [])) == sorted(broll)
                and pedidos == extra
                and bool(v.get("mesma_foto")) == bool(side.get("mesma_foto")) and v["com_veo"] == bool(feitas)):
            return nome
    if not feitas:
        return "sem_dono"
    if len(feitas) >= 2:
        return "dono_mesma_foto" if side.get("mesma_foto") else "dono_abre_fecha"
    return "dono_uma_cena"


def _views(media_id, tok):
    url = "https://graph.instagram.com/v21.0/" + str(media_id) + "/insights?" + urllib.parse.urlencode(
        {"metric": "views", "access_token": tok})
    try:
        d = json.loads(urllib.request.urlopen(url, timeout=60).read())
        return int(d["data"][0]["values"][0]["value"])
    except Exception:  # noqa: BLE001
        return None


def medir(log=print):
    """Views dos vídeos de produto postados há >= 48 h (contas com token). Grava no placar."""
    import catalogo
    import instagram_poster as ig
    creds = {c.get("name", "").lower().replace("instagram", "").strip(): c for c in ig.carregar_contas()}
    placar = _ler(PLACAR, {"videos": {}})
    limite = (datetime.now() - timedelta(hours=48)).isoformat()
    novos = 0
    for p in catalogo._ler(catalogo.INSTA_AUTO, []):
        if p.get("tipo") != "produto" or str(p.get("timestamp", "")) > limite:
            continue
        mid = str(p.get("media_id") or "")
        if not mid.isdigit():
            continue  # postado pelo navegador: sem id para medir
        tok = ((creds.get(p.get("account")) or {}).get("data") or {}).get("accessToken")
        side = _ler(FILA / p["account"] / "_postados" / Path(p["file"]).with_suffix(".json").name, {})
        if not tok or not side:
            continue
        v = _views(mid, tok)
        if v is None:
            continue
        placar["videos"][mid] = {"conta": p["account"], "arquivo": p["file"], "variante": variante_real(side),
                                 "views": v, "medido": datetime.now().isoformat(timespec="minutes")}
        novos += 1
    PLACAR.write_text(json.dumps(placar, ensure_ascii=False, indent=1), "utf-8")
    log(f"[variações] {novos} vídeo(s) medidos | no placar: {len(placar['videos'])}")
    try:  # 29/10 (Fable, PRODUTOS item 1): contas sem token = leitura dos Reels pelo cofre (produto/medir_web.py)
        from produto import medir_web
        placar = medir_web.medir(placar, log)
    except Exception as e:  # noqa: BLE001
        log(f"[variações] medir_web falhou ({type(e).__name__}: {str(e)[:120]})")
    return placar


def contagem(placar=None):
    """{variante: [sucessos, fracassos]} — sucesso = views >= mediana da própria conta."""
    placar = placar or _ler(PLACAR, {"videos": {}})
    por_conta = {}
    for v in placar["videos"].values():
        por_conta.setdefault(v["conta"], []).append(v)
    c = {k: [0, 0] for k in VARIANTES}
    for vids in por_conta.values():
        if len(vids) < 2:
            continue
        med = statistics.median(x["views"] for x in vids)
        for x in vids:
            if x["variante"] in c:
                c[x["variante"]][0 if x["views"] >= med else 1] += 1
    return c


def escolher(conta=None, log=print):
    """Variação do próximo vídeo por Thompson (Beta(1+s, 1+f))."""
    from produto import ajustes  # 27/10: o melhorador pode desligar variação ou dar peso (gosto do dono, ex.: "2+ Veo")
    fora = set(ajustes.valor("variantes_desligadas") or [])
    pesos = ajustes.valor("pesos_variantes") or {}
    c = {k: v for k, v in contagem().items() if k not in fora and k in VARIANTES} or contagem()
    sorteio = {k: random.betavariate(1 + s, 1 + f) * float(pesos.get(k, 1.0)) for k, (s, f) in c.items()}
    v = max(sorteio, key=sorteio.get)
    log(f"[variações] {conta or ''}: {v} (placar s/f: {c})")
    return v


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "placar"
    if cmd == "medir":
        medir()
    for k, (s, f) in contagem().items():
        print(f"{k:16} sucessos {s:3}  fracassos {f:3}")
