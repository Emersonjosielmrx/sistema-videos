# -*- coding: utf-8 -*-
r"""services/veo_flow/saude_flow.py — o Flow está logado NESTA máquina? (roda no nsn_worker dos notebooks/PC2; D30)

Lê cookies/cofre_<perfil>.json (colhidos pelo colher.py do Chrome LOCAL; nunca saem daqui) e, para cada perfil com
cookie do Google (SID), faz 1 GET em flow.google.com por HTTP (sem Chrome) e lê os créditos. Imprime 1 JSON por linha:
    {"perfil": "x", "vivo": true, "creditos": 1200, "ms": 800, "obs": ""}
O PC1 (tools\saude.py) chama isto 1 vez por máquina e mostra na aba "Sem navegador (HTTP)" como flow <perfil>@<maquina>.

    python3 -m services.veo_flow.saude_flow            # todos os perfis com cookie Google
    python3 -m services.veo_flow.saude_flow --tem X    # só diz TEM/NAO: o perfil X tem cookie Google colhido?
    python3 -m services.veo_flow.saude_flow X Y        # só esses perfis
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
COOKIES = ROOT / "cookies"


def _cofre(perfil):
    try:
        return json.loads((COOKIES / f"cofre_{perfil}.json").read_text("utf-8"))
    except (OSError, ValueError):
        return None


def tem_google(perfil):
    d = _cofre(perfil)
    return bool(d) and any(c.get("name") in ("SID", "__Secure-1PSID") and "google.com" in c.get("domain", "")
                           for c in d.get("cookies", []))


def perfis_google():
    return sorted(p.stem[6:] for p in COOKIES.glob("cofre_*.json") if tem_google(p.stem[6:]))


def testar(perfil):
    from services.veo_flow.flow_http import FlowHTTP
    t0 = time.time()
    d = _cofre(perfil)
    if not d:
        return {"perfil": perfil, "vivo": None, "obs": "sem cookie colhido"}
    if not tem_google(perfil):
        return {"perfil": perfil, "vivo": None, "obs": "cookie sem Google (não testável)"}
    try:
        f = FlowHTTP(d["cookies"])
    except Exception as e:  # noqa: BLE001
        return {"perfil": perfil, "vivo": False, "ms": round((time.time() - t0) * 1000), "obs": str(e)[:120],
                "colhido": d.get("quando")}
    try:
        cr = f.creditos()
    except Exception:  # noqa: BLE001
        cr = None
    return {"perfil": perfil, "vivo": True, "creditos": cr, "ms": round((time.time() - t0) * 1000),
            "obs": f"créditos {cr}" if cr is not None else "logado (créditos não lidos)", "colhido": d.get("quando")}


def perfis_instagram():
    """cofre_ig_<conta>.json com sessionid (colhidos aqui)."""
    out = []
    for p in sorted(COOKIES.glob("cofre_ig_*.json")):
        d = _cofre(p.stem[6:])
        if d and any(c.get("name") == "sessionid" for c in d.get("cookies", [])):
            out.append(p.stem[6:])
    return out


def testar_instagram(perfil):
    """29/10 (D31): o mesmo teste do tools\\saude.py (PC1), com os cookies DESTA máquina. perfil = ig_<conta>."""
    import re
    from core.cofre_cookies import sessao
    conta = perfil[3:]
    t0 = time.time()
    d = _cofre(perfil)
    try:
        s = sessao(perfil, ["instagram.com"], chrome_tls=True)
        r = s.get(f"https://www.instagram.com/{conta}/", timeout=30)
    except Exception as e:  # noqa: BLE001
        return {"perfil": perfil, "servico": "instagram", "vivo": False, "obs": f"{type(e).__name__}: {str(e)[:100]}",
                "ms": round((time.time() - t0) * 1000), "colhido": (d or {}).get("quando")}
    ms = round((time.time() - t0) * 1000)
    if r.status_code == 429:
        vivo, obs = None, "429 (não conta como morto)"
    elif "not-logged-in" in r.text[:3000] or "/accounts/login" in str(r.url):
        vivo, obs = False, "deslogado"
    elif re.search(r'"dtsg":\{"token":"|"DTSGInitialData"', r.text):
        vivo, obs = True, ""
    else:
        vivo, obs = False, f"sem DTSG (HTTP {r.status_code})"
    return {"perfil": perfil, "servico": "instagram", "vivo": vivo, "obs": obs, "ms": ms, "colhido": (d or {}).get("quando")}


def main(a):
    if "--tem" in a:
        print("TEM" if tem_google(a[a.index("--tem") + 1]) else "NAO")
        return 0
    if "--instagram" in a:  # só o Instagram desta máquina
        for p in perfis_instagram():
            print(json.dumps(testar_instagram(p), ensure_ascii=False), flush=True)
            time.sleep(1.5)
        return 0
    for p in a or perfis_google():
        print(json.dumps({"servico": "flow", **testar(p)}, ensure_ascii=False), flush=True)
        time.sleep(0.5)
    if not a:  # rodada completa: Flow + Instagram desta máquina
        for p in perfis_instagram():
            print(json.dumps(testar_instagram(p), ensure_ascii=False), flush=True)
            time.sleep(1.5)
    return 0


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
