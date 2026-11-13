# -*- coding: utf-8 -*-
"""Medidor diario de visualizacoes do TikTok (dono 22/10/2026: "faz um medidor de visualizacoes pra TikTok uma vez por
dia"). Le o perfil publico de cada conta do postador com @ conhecido (config/reuso_plataformas.json, "TikTok @x" no
_obs) + MS Energy, pelo navegador LOGADO do cofre msenergypara (sem login o TikTok nao mostra a grade e pede captcha).

Grava logs/tiktok_views/<data>.json (a cada conta, retomavel), TIKTOK_VISUALIZACOES.md (ganho do dia, contas zeradas)
e manda um resumo curto no resumo da rotina do Telegram. Tarefa TikTok_MedirViews (todo dia 07:23, sem janela).
Varredura de 22/10: 16 contas com views, 32 com TODOS os videos em 0 (contas novas), 2 nao abriram.
"""
import json
import random
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
REUSO = BASE / "config" / "reuso_plataformas.json"
DIR = BASE / "logs" / "tiktok_views"
DOC = BASE / "TIKTOK_VISUALIZACOES.md"
EXTRAS = {"msenergypara (MS Energy)": "energia.solar.da"}
# Leitura da grade JA carregada (nenhuma rolagem/clique/pagina a mais). 23/10: "pv" = [id do video, views] dos mesmos
# cartoes, para o placar de 48 h do notificar_telegram (_placar_tiktok) ligar cada video a ficha postar.json.
JS_GRADE = """() => {
    const t = s => { const e = document.querySelector(s); return e ? e.innerText : null; };
    const as = [...document.querySelectorAll('a[href*="/video/"]')];
    const v = as.map(a => { const e = a.querySelector('[data-e2e="video-views"]'); return e ? e.innerText : null; });
    const pv = as.map(a => { const m = (a.getAttribute('href') || '').match(/\\/video\\/(\\d+)/);
        const e = a.querySelector('[data-e2e="video-views"]'); return (m && e) ? [m[1], e.innerText] : null; })
        .filter(x => x);
    return {seg: t('[data-e2e="followers-count"]'), curt: t('[data-e2e="likes-count"]'), v: v, pv: pv,
            titulo: document.title}; }"""


def contas():
    cfg = json.loads(REUSO.read_text("utf-8"))["tiktok"]["contas"]
    com, sem = {}, []
    for nome, c in cfg.items():
        achado = re.search(r"TikTok\s+@([\w.]+)", json.dumps(c, ensure_ascii=False))
        if achado:
            com[nome] = achado.group(1)
        else:
            sem.append(nome)
    com.update(EXTRAS)
    return com, sem


def num(t):
    t = (t or "").strip().lower().replace(",", ".")
    mult = 1000 if t.endswith("k") or "mil" in t else (1_000_000 if t.endswith("m") or "mi" in t else 1)
    achado = re.search(r"[\d.]+", t)
    try:
        return int(float(achado.group(0)) * mult) if achado else 0
    except ValueError:
        return 0


def medir(saida):
    feito = json.loads(saida.read_text("utf-8")) if saida.exists() else {}
    alvos, _ = contas()
    if not set(alvos) <= set(feito):  # dia completo = "medir agora" do painel: mede tudo de novo, trocando conta a
        alvos = {k: v for k, v in alvos.items() if k not in feito}  # conta (a tabela do painel nao fica pela metade)
    if not alvos:
        return feito
    porta, proc = cofre.abrir("msenergypara")
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()
        try:
            for nome, h in alvos.items():
                try:
                    pg.goto(f"https://www.tiktok.com/@{h}", wait_until="domcontentloaded")
                    pg.wait_for_timeout(7000)
                    for _ in range(5):  # a grade carrega ~24 videos por vez
                        pg.mouse.wheel(0, 3000)
                        pg.wait_for_timeout(1500)
                    d = pg.evaluate(JS_GRADE)
                except Exception as e:  # noqa: BLE001
                    d = {"seg": None, "curt": None, "v": [], "titulo": f"erro {type(e).__name__}"}
                vs = [num(x) for x in d["v"] if x is not None]
                feito[nome] = {"handle": h, "seguidores": num(d["seg"]), "curtidas": num(d["curt"]),
                               "videos": len(vs), "views": sum(vs), "views_max": max(vs) if vs else 0,
                               "zerados": sum(1 for x in vs if x == 0),
                               "abriu": len(vs) > 0 and "Make Your Day" not in (d["titulo"] or ""),
                               "lido_em": datetime.now().astimezone().isoformat(timespec="minutes"),
                               "por_video": {i: num(x) for i, x in (d.get("pv") or [])}}
                saida.write_text(json.dumps(feito, ensure_ascii=False, indent=1), "utf-8")
                pg.wait_for_timeout(random.randint(3000, 6000))
        finally:
            pg.close()
            cofre.fechar(proc, br, nome="msenergypara")
    return feito


def main():
    DIR.mkdir(parents=True, exist_ok=True)
    hoje = date.today().isoformat()
    atual = medir(DIR / f"{hoje}.json")
    anteriores = sorted(p for p in DIR.glob("*.json") if p.stem < hoje)
    antes = json.loads(anteriores[-1].read_text("utf-8")) if anteriores else {}
    _, sem_arroba = contas()
    for nome, r in atual.items():
        r["ganho"] = r["views"] - antes[nome]["views"] if nome in antes else None
    abriram = {k: v for k, v in atual.items() if v["abriu"]}
    zeradas = sorted(k for k, v in abriram.items() if v["views"] == 0)
    total = sum(v["views"] for v in abriram.values())
    ganho = sum(v["ganho"] or 0 for v in abriram.values()) if antes else None

    linhas = [f"# TikTok — visualizações por conta ({datetime.now():%d/%m/%Y %H:%M})", "",
              f"{len(atual)} contas lidas | {total} views no total" + (f" | **{ganho:+d} desde {anteriores[-1].stem}**"
                                                                      if antes else "") +
              f" | {len(zeradas)} com todos os vídeos em 0 | {len(atual) - len(abriram)} não abriram", "",
              "| Conta (cofre) | @ | seguidores | vídeos | views | ganho | maior vídeo | vídeos em 0 |",
              "|---|---|---|---|---|---|---|---|"]
    for nome, r in sorted(atual.items(), key=lambda kv: -kv[1]["views"]):
        g = "" if r["ganho"] is None else f"{r['ganho']:+d}"
        linhas.append(f"| {nome} | @{r['handle']} | {r['seguidores']} | {r['videos']} | {r['views']} | {g} | "
                      f"{r['views_max']} | {r['zerados']} |" + ("" if r["abriu"] else " não abriu |"))
    if sem_arroba:
        linhas += ["", "Sem @ anotado em `config/reuso_plataformas.json` (não medidas): " + ", ".join(sem_arroba)]
    DOC.write_text("\n".join(linhas) + "\n", "utf-8")
    print("\n".join(linhas[:4]))

    top = sorted((kv for kv in abriram.items() if (kv[1]["ganho"] or 0) > 0), key=lambda kv: -kv[1]["ganho"])[:3]
    texto = (f"TikTok ({len(atual)} contas): {total} views" + (f" ({ganho:+d} em 24 h)" if antes else "")
             + f"; {len(zeradas)} contas com tudo em 0")
    if top:
        texto += "; mais cresceram: " + ", ".join(f"@{r['handle']} {r['ganho']:+d}" for _, r in top)
    nao = [r["handle"] for r in atual.values() if not r["abriu"]]
    if nao:
        texto += "; não abriram: " + ", ".join("@" + h for h in nao)
    texto += ". Detalhes: D:\\postador-de-videos\\TIKTOK_VISUALIZACOES.md"
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "tiktok-views", importante=False)
    except Exception as e:  # noqa: BLE001
        print(f"aviso no Telegram falhou: {type(e).__name__}: {e}")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
