"""Mede views dos Reels e seguidores de cada Página do Facebook (dona 20/11/2026: "adaptar todo o sistema de
inteligência pro Facebook também"). Lê a aba Reels da Página no Chrome da conta, SEMPRE pela saída fixa dela
(fb_contas.abrir confere o proxy); 1 Chrome por conta, as Páginas da mesma conta em sequência (é a mesma conta).

Grava logs/fb_views.jsonl (1 linha por Página por medição: seguidores + views de cada reel visível) e
FACEBOOK_VISUALIZACOES.md (ranking com ganho desde a medição anterior). A escada (fb_escada.py) lê o jsonl.

    python fb_medir.py              # todas as Páginas (tarefa FacebookMedir)
    python fb_medir.py anime_noturno
"""
import json, re, sys, time
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import fb_contas  # noqa: E402

CFG = BIN.parent / "config" / "facebook_paginas.json"
OUT = BIN.parent / "logs" / "fb_views.jsonl"
MD = BIN.parent / "FACEBOOK_VISUALIZACOES.md"


def _num(t):
    """'1,2 mil' / '3,4 mi' / '904' / '1.234' -> int"""
    t = (t or "").strip().casefold().replace("\xa0", " ")
    m = re.match(r"([\d.,]+)\s*(mil|mi|k|m)?", t)
    if not m:
        return None
    n, suf = m.group(1), m.group(2)
    if suf:
        n = float(n.replace(".", "").replace(",", "."))
        return int(n * (1000 if suf in ("mil", "k") else 1_000_000))
    return int(n.replace(".", "").replace(",", ""))


def medir_pagina(ctx, pag):
    pg = ctx.new_page()
    pg.set_viewport_size({"width": 1366, "height": 1600})
    try:
        pg.goto(f"https://www.facebook.com/profile.php?id={pag['id']}&sk=reels_tab", wait_until="domcontentloaded",
                timeout=120000)
        time.sleep(12)
        for _ in range(4):  # rola para carregar mais reels
            pg.mouse.wheel(0, 2500); time.sleep(2.5)
        corpo = pg.inner_text("body")
        m = re.search(r"([\d.,]+\s*(?:mil|mi)?)\s+seguidor", corpo)
        seg = _num(m.group(1)) if m else None
        reels = {}
        for a in pg.query_selector_all("a[href*='/reel/']"):
            href = (a.get_attribute("href") or "").split("?")[0]
            rid = re.search(r"/reel/(\d+)", href)
            if not rid:
                continue
            v = _num((a.inner_text() or "").strip().split("\n")[-1])
            if v is not None:
                reels[rid.group(1)] = v
        return {"seguidores": seg, "reels": [{"id": k, "views": v} for k, v in reels.items()]}
    finally:
        pg.close()


def relatorio():
    linhas = [json.loads(x) for x in OUT.read_text(encoding="utf-8").splitlines() if x.strip()]
    por = {}
    for r in linhas:
        por.setdefault(r["pagina"], []).append(r)
    tab = []
    for chave, rs in por.items():
        a = rs[-1]
        soma = sum(x["views"] for x in a["reels"])
        ant = sum(x["views"] for x in rs[-2]["reels"]) if len(rs) > 1 else 0
        tab.append((soma, f"| {a['nome']} | {a['seguidores'] if a['seguidores'] is not None else '?'} | {len(a['reels'])} | "
                          f"{soma} | {soma - ant:+d} | {a['quando'][:16].replace('T', ' ')} |"))
    MD.write_text("# Visualizações das Páginas do Facebook (fb_medir.py)\n\n"
                  "| Página | Seguidores | Reels | Views (soma) | Ganho desde a anterior | Medido |\n|---|---|---|---|---|---|\n"
                  + "\n".join(t for _, t in sorted(tab, reverse=True)) + "\n", encoding="utf-8")


def main():
    from playwright.sync_api import sync_playwright
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    so = sys.argv[1:]
    pags = {k: p for k, p in cfg["paginas"].items() if (not so or k in so) and not p.get("pausada")}
    por_conta = {}
    for k, p in pags.items():
        por_conta.setdefault(p["conta"], []).append(k)
    for conta, chaves in por_conta.items():  # uma conta por vez, cada uma na saída dela
        porta, proc = fb_contas.abrir(conta)
        try:
            with sync_playwright() as pw:
                ctx = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
                for k in chaves:
                    try:
                        r = medir_pagina(ctx, pags[k])
                    except Exception as e:  # noqa: BLE001
                        print(f"[{k}] falhou: {str(e)[:150]}"); continue
                    r.update(pagina=k, nome=pags[k]["nome"], quando=datetime.now().isoformat(timespec="seconds"))
                    with open(OUT, "a", encoding="utf-8") as f:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                    print(f"[{pags[k]['nome']}] seguidores {r['seguidores']} | reels {len(r['reels'])} | "
                          f"views {sum(x['views'] for x in r['reels'])}", flush=True)
        finally:
            fb_contas.fechar(proc)
    if OUT.exists():
        relatorio()
        import fb_escada
        for k in pags:
            fb_escada.marcar_estagnacao(k)


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
