"""Confere o acesso pela API (Graph) das Páginas de UMA conta, SEM postar nada (regra: nada de post de teste em Página real).
Sempre pela saída fixa da conta (fish_audio._subir_ponte; recusa Kaggle), nunca pela casa.
O JSON de /me/accounts vem pelo stdin e o app id/segredo pelas variáveis FB_APP_ID / FB_APP_SECRET:
NADA disso é gravado em disco e nenhum token é impresso.

    python fb_api_checar.py <email_cofre> < accounts.json
"""
import sys, json, os
from pathlib import Path
sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
import requests
import fish_audio

G = "https://graph.facebook.com/v21.0"
CFG = Path(r"D:\postador-de-videos\config\facebook_paginas.json")
PRECISA = ("pages_manage_posts", "pages_read_engagement", "pages_show_list")


def main():
    email = sys.argv[1]
    paginas = json.load(sys.stdin)["data"]
    app_id, segredo = os.environ.get("FB_APP_ID"), os.environ.get("FB_APP_SECRET")
    _, n = fish_audio.checar_conta(email)  # recusa conta do Kaggle; exige IP próprio
    porta = fish_audio._subir_ponte(n)
    s = requests.Session()
    s.proxies = {"http": f"http://127.0.0.1:{porta}", "https": f"http://127.0.0.1:{porta}"}
    print("saida IP:", s.get("https://api.ipify.org", timeout=30).text, f"(rnprmtfo-{n})", flush=True)
    app_tok = f"{app_id}|{segredo}" if app_id and segredo else None

    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    do_cfg = {p["asset_id"]: p["nome"] for p in cfg["paginas"].values() if p["conta"] == "emersonjosiel02"}
    vistos = set()
    for p in paginas:
        tok, pid = p["access_token"], p["id"]
        vistos.add(pid)
        print(f"\n== {p['name']} ({pid})", flush=True)
        r = s.get(f"{G}/{pid}", params={"access_token": tok, "fields": "id,name,fan_count,followers_count"}, timeout=40).json()
        print("  leitura da Página:", json.dumps(r, ensure_ascii=False)[:200])
        print("  tarefas:", ",".join(p.get("tasks", [])))
        if app_tok:
            d = s.get(f"{G}/debug_token", params={"input_token": tok, "access_token": app_tok}, timeout=40).json()
            d = d.get("data") or d
            exp = d.get("expires_at")
            print("  token: válido =", d.get("is_valid"), "| tipo =", d.get("type"), "| expira =",
                  "NUNCA" if exp == 0 else exp, "| app_id =", d.get("app_id"),
                  "| erro =", (d.get("error") or {}).get("message"))
            esc = set(d.get("scopes") or [])
            print("  permissões:", sorted(esc))
            falta = [x for x in PRECISA if x not in esc]
            print("  faltam p/ postar Reel:", falta or "nenhuma")
        rr = s.get(f"{G}/{pid}/video_reels", params={"access_token": tok, "limit": 3, "fields": "id,created_time"},
                   timeout=40).json()
        if "error" in rr:
            print("  ler Reels da Página: ERRO", rr["error"].get("message"))
        else:
            print("  ler Reels da Página: ok,", len(rr.get("data", [])), "reel(s) vistos")
    faltam = {k: v for k, v in do_cfg.items() if k not in vistos}
    print("\nPáginas da conta que NÃO vieram nesta resposta:", faltam or "nenhuma")


if __name__ == "__main__":
    main()
