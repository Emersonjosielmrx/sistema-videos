# -*- coding: utf-8 -*-
"""Medicao semanal dos Reels do @msenergycap (novo ms_v2 x antigos) e dos videos do TikTok @energia.solar.da.

Grava docs\\METRICAS_INSTAGRAM.md (tabelas) e cache\\metricas\\<data>.json (historico) e manda um resumo curto no
resumo da rotina do Telegram (portao D:\\video-fila\\avisos.py, sem mensagem na hora). Tarefa MSEnergy_Metricas.
"""
import json
import statistics as st
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

CREDS = Path(r"D:\credenciais-canais\instagram_contas.json")
BASE = "https://graph.instagram.com/v21.0"
LOG_POSTAGEM = Path(r"D:\ms-energy\videos\postagem_log.json")
PASTAS = [Path(r"D:\ms-energy\videos\shorts_veo"), Path(r"D:\ms-energy\videos\_postados")]
DOC = Path(r"D:\ms-energy\docs\METRICAS_INSTAGRAM.md")
HIST = Path(r"D:\ms-energy\cache\metricas")
METRICAS = ["views", "reach", "likes", "comments", "shares", "saved", "ig_reels_avg_watch_time"]
DESDE = "2026-08-25"  # inicio da campanha com IA
FUSO = timedelta(hours=-3)  # Para (UTC-3); o postagem_log grava hora local


def _get(path, **params):
    return json.loads(urllib.request.urlopen(f"{BASE}/{path}?{urllib.parse.urlencode(params)}", timeout=60).read())


def _insights(mid, tok):
    try:
        d = _get(f"{mid}/insights", metric=",".join(METRICAS), access_token=tok)
        return {x["name"]: x["values"][0]["value"] for x in d.get("data", [])}
    except urllib.error.HTTPError:
        out = {}
        for m in METRICAS:  # alguma metrica nao vale para o post: uma a uma
            try:
                d = _get(f"{mid}/insights", metric=m, access_token=tok)
                out[m] = d["data"][0]["values"][0]["value"]
            except Exception:  # noqa: BLE001
                pass
        return out


def _sidecars():
    out = {}
    for pasta in PASTAS:
        for j in pasta.glob("ms_energy_solar_*.json"):
            try:
                out[j.stem] = json.loads(j.read_text("utf-8"))
            except Exception:  # noqa: BLE001
                pass
    return out


def _postados():
    """[(hora_local_do_post, stem)] pelo postagem_log (campo insta)."""
    try:
        log = json.loads(LOG_POSTAGEM.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return []
    res = []
    for stem, e in log.items():
        try:
            res.append((datetime.fromisoformat(str(e.get("insta"))[:19]), stem))
        except (TypeError, ValueError):
            pass
    return res


def coletar():
    contas = json.loads(CREDS.read_text("utf-8"))
    tok = next(c for c in contas if "msenergycap" in c["name"].lower())["data"]["accessToken"]
    perfil = _get("me", fields="username,followers_count,media_count", access_token=tok)
    midias, url = [], (f"{BASE}/me/media?" + urllib.parse.urlencode(
        {"fields": "id,caption,media_type,media_product_type,timestamp,permalink,like_count", "limit": 100,
         "access_token": tok}))
    while url:
        r = json.loads(urllib.request.urlopen(url, timeout=60).read())
        midias += r.get("data", [])
        url = r.get("paging", {}).get("next")
    side, postados = _sidecars(), _postados()
    reels = []
    for m in midias:
        carrossel = m.get("media_type") == "CAROUSEL_ALBUM"  # carrossel_ms.py, desde 22/10
        if (m.get("media_product_type") != "REELS" and not carrossel) or m["timestamp"][:10] < DESDE:
            continue
        local = datetime.strptime(m["timestamp"][:19], "%Y-%m-%dT%H:%M:%S") + FUSO
        stem = next((s for t, s in postados if abs((t - local).total_seconds()) < 20 * 60), None)
        meta = side.get(stem, {}) if stem else {}
        reels.append({"id": m["id"], "data": local.isoformat(timespec="minutes"), "link": m.get("permalink"),
                      "legenda": (m.get("caption") or "").split("\n")[0][:70], "stem": stem,
                      "formato": "carrossel" if carrossel else ("novo" if meta.get("pipeline") == "ms_v2" else "antigo"),
                      "tipo_video": meta.get("tipo_video"), "pauta": meta.get("pauta"),
                      "gancho": meta.get("gancho_tela"), **_insights(m["id"], tok)})
    return perfil, reels


def coletar_tiktok():
    """Le o TikTok Studio da conta do cofre msenergypara (@energia.solar.da): data, descricao, views, curtidas,
    comentarios de cada video. None se nao der (Chrome/login). 22/10: os 5 primeiros videos tinham 0 views."""
    import re
    try:
        sys.path.insert(0, r"D:\logins-google")
        import cofre
        from playwright.sync_api import sync_playwright
        porta, proc = cofre.abrir("msenergypara")
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = br.contexts[0].new_page()
            try:
                pg.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="domcontentloaded")
                pg.wait_for_timeout(12000)
                for _ in range(5):
                    pg.mouse.wheel(0, 4000)
                    pg.wait_for_timeout(1500)
                linhas = [x.strip() for x in pg.inner_text("body").split("\n") if x.strip()]
            finally:
                pg.close()
                cofre.fechar(proc, br, nome="msenergypara")
    except Exception as e:  # noqa: BLE001
        print(f"TikTok nao medido: {type(e).__name__}: {str(e)[:120]}")
        return None

    def num(t):
        t = t.lower().replace(".", "").replace(",", ".")
        mult = 1000 if "mil" in t or t.endswith("k") else (1_000_000 if "mi" in t or t.endswith("m") else 1)
        achado = re.search(r"[\d.]+", t)
        return int(float(achado.group(0)) * mult) if achado else 0

    videos = []
    for i, ln in enumerate(linhas):  # bloco: descricao / "22 de out, 12:13" / privacidade / views / curtidas / coment.
        if re.fullmatch(r"\d{1,2} de \w+\.?,? \d{1,2}:\d{2}", ln) and i + 4 < len(linhas):
            videos.append({"data": ln, "descricao": linhas[i - 1][:90], "privacidade": linhas[i + 1],
                           "views": num(linhas[i + 2]), "curtidas": num(linhas[i + 3]),
                           "comentarios": num(linhas[i + 4]),
                           "formato": "novo" if "chame a MS Energy no WhatsApp" in linhas[i - 1] else "antigo"})
    return videos


def _conta_7dias():
    """25/10: alcance, visualizações, cliques no link do perfil (o WhatsApp), comentários... da CONTA nos 7 dias.
    {} se a API recusar."""
    try:
        contas = json.loads(CREDS.read_text("utf-8"))
        tok = next(c for c in contas if "msenergycap" in c["name"].lower())["data"]["accessToken"]
        agora = datetime.now()
        d = _get("me/insights", metric="reach,views,profile_links_taps,accounts_engaged,comments,shares,saves",
                 period="day", metric_type="total_value", since=int((agora - timedelta(days=7)).timestamp()),
                 until=int(agora.timestamp()), access_token=tok)
        return {x["name"]: (x.get("total_value") or {}).get("value") for x in d.get("data", [])}
    except Exception:  # noqa: BLE001
        return {}


def _resumo_grupo(lst):
    if not lst:
        return None
    v = [r.get("views") or 0 for r in lst]
    w = [r.get("ig_reels_avg_watch_time") or 0 for r in lst if r.get("ig_reels_avg_watch_time")]
    soma = lambda k: sum(r.get(k) or 0 for r in lst)  # noqa: E731
    return {"n": len(lst), "views_mediana": st.median(v), "views_media": round(st.mean(v), 1), "views_max": max(v),
            "assistido_s": round(st.median(w) / 1000, 1) if w else 0, "curtidas": soma("likes"),
            "comentarios": soma("comments"), "compartilhamentos": soma("shares"), "salvos": soma("saved")}


def main():
    hoje = datetime.now()
    perfil, reels = coletar()
    novos = [r for r in reels if r["formato"] == "novo"]
    antigos = [r for r in reels if r["formato"] == "antigo"]
    carrosseis = [r for r in reels if r["formato"] == "carrossel"]  # 25/10: antes nunca entravam no relatorio
    g_novo, g_antigo, g_carr = _resumo_grupo(novos), _resumo_grupo(antigos), _resumo_grupo(carrosseis)
    conta7 = _conta_7dias()
    HIST.mkdir(parents=True, exist_ok=True)
    anteriores = sorted(HIST.glob("*.json"))
    seg_antes = json.loads(anteriores[-1].read_text("utf-8"))["perfil"].get("followers_count") if anteriores else None
    (HIST / f"{hoje:%Y-%m-%d}.json").write_text(json.dumps(
        {"perfil": perfil, "novo": g_novo, "antigo": g_antigo, "reels": reels}, ensure_ascii=False, indent=1), "utf-8")

    por_pauta = {}
    for r in novos:
        por_pauta.setdefault(f"{r['pauta']} ({r['tipo_video']})", []).append(r)
    linhas = [f"# Métricas do Instagram @msenergycap — {hoje:%d/%m/%Y %H:%M}", "",
              f"Seguidores: **{perfil.get('followers_count')}**"
              + (f" ({perfil.get('followers_count') - seg_antes:+d} desde a medição anterior)" if seg_antes else ""),
              "", "| Formato | Reels | views (mediana / média / máx) | assistido (mediana) | curtidas | coment. | "
              "compart. | salvos |", "|---|---|---|---|---|---|---|---|"]
    if conta7:
        linhas[3:3] = ["", f"Conta nos últimos 7 dias: alcance **{conta7.get('reach')}**, visualizações "
                           f"{conta7.get('views')}, **cliques no link (WhatsApp) {conta7.get('profile_links_taps')}**, "
                           f"comentários {conta7.get('comments')}, salvos {conta7.get('saves')}, "
                           f"compartilhamentos {conta7.get('shares')}, contas engajadas {conta7.get('accounts_engaged')}"]
    for nome, g in (("novo (ms_v2, desde 22/10)", g_novo), ("carrossel (desde 22/10)", g_carr),
                    ("antigo (25/08–21/10)", g_antigo)):
        if g:
            linhas.append(f"| {nome} | {g['n']} | {g['views_mediana']} / {g['views_media']} / {g['views_max']} | "
                          f"{g['assistido_s']} s | {g['curtidas']} | {g['comentarios']} | {g['compartilhamentos']} | "
                          f"{g['salvos']} |")
    if por_pauta:
        linhas += ["", "## Formato novo por pauta (qual assunto rende)", "", "| Pauta | Reels | views (média) | "
                   "assistido (média) | curtidas | salvos |", "|---|---|---|---|---|---|"]
        for k, lst in sorted(por_pauta.items(), key=lambda kv: -st.mean([r.get("views") or 0 for r in kv[1]])):
            w = [r.get("ig_reels_avg_watch_time") or 0 for r in lst]
            linhas.append(f"| {k} | {len(lst)} | {round(st.mean([r.get('views') or 0 for r in lst]), 1)} | "
                          f"{round(st.mean(w) / 1000, 1)} s | {sum(r.get('likes') or 0 for r in lst)} | "
                          f"{sum(r.get('saved') or 0 for r in lst)} |")
        linhas += ["", "## Reels novos", "", "| Data | Gancho | views | assistido | curtidas | link |",
                   "|---|---|---|---|---|---|"]
        for r in sorted(novos, key=lambda r: r["data"], reverse=True):
            linhas.append(f"| {r['data'][:16]} | {r['gancho']} | {r.get('views')} | "
                          f"{round((r.get('ig_reels_avg_watch_time') or 0) / 1000, 1)} s | {r.get('likes')} | {r['link']} |")
    tiktok = coletar_tiktok()
    if tiktok is not None:
        tk_views = sum(v["views"] for v in tiktok)
        linhas += ["", f"## TikTok @energia.solar.da — {len(tiktok)} vídeos, {tk_views} views no total", ""]
        if tiktok and tk_views == 0:
            linhas.append("**Atenção: nenhum vídeo teve visualização — o TikTok não está entregando a conta "
                          "(ver status da conta no app e o selo \"conteúdo gerado por IA\").**")
            linhas.append("")
        linhas += ["| Data | Formato | Descrição | views | curtidas | coment. |", "|---|---|---|---|---|---|"]
        for v in tiktok:
            linhas.append(f"| {v['data']} | {v['formato']} | {v['descricao'][:60]} | {v['views']} | {v['curtidas']} | "
                          f"{v['comentarios']} |")
        (HIST / f"{hoje:%Y-%m-%d}.json").write_text(json.dumps(
            {"perfil": perfil, "novo": g_novo, "antigo": g_antigo, "reels": reels, "tiktok": tiktok},
            ensure_ascii=False, indent=1), "utf-8")
    DOC.write_text("\n".join(linhas) + "\n", "utf-8")
    print("\n".join(linhas))

    texto = (f"MS Energy — Instagram @msenergycap: {perfil.get('followers_count')} seguidores"
             + (f" ({perfil.get('followers_count') - seg_antes:+d})" if seg_antes else "") + ". ")
    if g_novo:
        melhor = max(novos, key=lambda r: r.get("views") or 0)
        texto += (f"Formato novo: {g_novo['n']} Reels, mediana {g_novo['views_mediana']} views, assistido "
                  f"{g_novo['assistido_s']} s, {g_novo['curtidas']} curtidas, {g_novo['salvos']} salvos. "
                  f"Melhor: \"{melhor['gancho']}\" ({melhor.get('views')} views). ")
    if g_carr:
        texto += f"Carrosséis: {g_carr['n']}, mediana {g_carr['views_mediana']} views. "
    if conta7:
        texto += (f"7 dias: alcance {conta7.get('reach')}, {conta7.get('profile_links_taps')} clique(s) no WhatsApp, "
                  f"{conta7.get('comments')} comentário(s). ")
    if g_antigo:
        texto += f"Antigos: mediana {g_antigo['views_mediana']} views, {g_antigo['assistido_s']} s. "
    if tiktok is not None:
        texto += f"TikTok: {len(tiktok)} vídeos, {sum(v['views'] for v in tiktok)} views"
        texto += " (ATENÇÃO: nenhuma visualização — conta não está sendo entregue). " if tiktok and not any(
            v["views"] for v in tiktok) else ". "
    texto += "Detalhes: D:\\ms-energy\\docs\\METRICAS_INSTAGRAM.md"
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "msenergy-metricas", importante=False)
    except Exception as e:  # noqa: BLE001
        print(f"aviso no Telegram falhou: {type(e).__name__}: {e}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
