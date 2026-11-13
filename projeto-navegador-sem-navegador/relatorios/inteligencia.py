# -*- coding: utf-8 -*-
r"""relatorios/inteligencia.py — central diária: cruza os dados reais do YouTube Studio (e do Instagram) de todos os
canais, por HTTP puro, e responde as perguntas que antes não dava para responder:

  1. Qual nicho deu mais inscritos (e views) na semana?
  2. Que estrutura de título tem mais CTR (pergunta, CAIXA ALTA, número, emoji...)? E os 10 títulos campeões.
  3. Quais vídeos zeraram (>48 h no ar e quase nada de views) — candidatos a reeditar ou tirar.
  4. Shorts: quem segurou o público no feed (>=75% ficaram) e quem perdeu (<50%).
  5. Termos de busca reais que trouxeram gente, por nicho (para títulos/tags).
  6. Instagram (com --instagram): Reels por conta com views/curtidas.
  7. TikTok (com --tiktok): só contas com cookie salvo; views da semana, vídeos zerados, legenda "Video", e tempo
     médio/conclusão do melhor vídeo. Conta com 10+ vídeos velhos e zero views no total = "o TikTok não entrega".

Saída: relatorios\saida\inteligencia_<data>.json e relatorios\saida\INTELIGENCIA.md (o mais recente).
Não abre navegador: canal com cookie vencido entra em "sem_login" (renove com `python D:\gemini-argo\youtube_http.py
sync <slug>`), e não derruba os outros.

    python -m relatorios.inteligencia [--dias 7] [--canais slug1,slug2] [--instagram] [--tiktok]
"""
import argparse
import json
import re
import sys
import time
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"D:\gemini-argo")
import youtube_http  # noqa: E402

from core.arquivo import gravar_json, gravar_texto  # noqa: E402
from services.youtube.studio_analytics import StudioAnalytics  # noqa: E402

SAIDA = ROOT / "relatorios" / "saida"
CANAIS = Path(r"D:\postador-de-videos\config\canais.json")
IG_ESTADO = Path(r"D:\postador-de-videos\config\instagram_local.json")


def _sem_navegador(slug):
    raise RuntimeError("cookie vencido (sem_login)")


def _nichos():
    c = json.loads(CANAIS.read_text("utf-8"))["canais"]
    return {v["channel_id"]: (v.get("nicho") or "?", v.get("idioma") or "?") for v in c.values() if v.get("channel_id")}


_EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")


def estrutura(titulo):
    """Traços do título que dá para comparar entre canais."""
    t = re.sub(r"#\w+", "", titulo).strip()
    palavras = [p for p in re.findall(r"[A-Za-zÀ-ú]{3,}", t)]
    caixa = sum(1 for p in palavras if p.isupper()) / max(1, len(palavras))
    return {"pergunta": "?" in t, "caixa_alta": caixa >= 0.3, "numero": bool(re.search(r"\d", t)),
            "emoji": bool(_EMOJI.search(t)), "curto(<45)": len(t) < 45,
            "provocacao": bool(re.search(r"\b(ningu[eé]m|nunca|segredo|ninguem|ningu[eé]m|voc[eê]|por que|porque|"
                                         r"como|chocou|absurdo|mal|incr[ií]vel)\b", t, re.I))}


def coletar_canal(slug, dias, nichos):
    a = StudioAnalytics(slug)
    nicho, idioma = nichos.get(a.cid, ("?", "?"))
    lista = {v["id"]: v for v in a.studio.videos(50)}  # títulos, publicação, privacidade
    porvid = a.videos(dias=dias, limite=50)
    for v in porvid:
        info = lista.get(v["id"], {})
        v.update({"titulo": info.get("titulo", ""), "publicado": info.get("publicado"),
                  "segundos": info.get("segundos"), "views_total": info.get("views")})
    agora = time.time()
    zerados = [{"id": v["id"], "titulo": v["titulo"], "views": v["views"],
                "horas_no_ar": round((agora - v["publicado"]) / 3600)}
               for v in lista.values()
               if v.get("publicado") and v["privacidade"] == "public" and agora - v["publicado"] > 48 * 3600
               and (v.get("views") or 0) < 10]
    return {"slug": slug, "channel_id": a.cid, "nicho": nicho, "idioma": idioma,
            "shorts": a.shorts_vtr(dias), "trafego": a.trafego(dias), "termos": a.termos_busca(dias, 15),
            "videos": porvid, "zerados": zerados[:15]}


def coletar_instagram():
    from services.instagram.web import InstagramWeb
    est = json.loads(IG_ESTADO.read_text("utf-8"))
    out = []
    for conta, v in est.items():
        if not isinstance(v, dict) or not str(v.get("resultado", "")).startswith("logado"):
            continue
        try:
            ig = InstagramWeb(conta, v.get("cofre"))
            out.append({"conta": conta, "perfil": ig.perfil_info(), "reels": ig.reels(quantos=12)})
        except Exception as e:  # noqa: BLE001
            out.append({"conta": conta, "erro": str(e)[:160]})
        time.sleep(8)  # devagar: várias contas no mesmo IP
    return out


def coletar_tiktok(dias):
    """Contas do TikTok que já têm cookie salvo (core\\cofre_cookies): resumo da semana, vídeos e o detalhe do melhor."""
    from core.cofre_cookies import ler
    from services.tiktok.studio import REUSO, TikTokStudio
    out = []
    agora = time.time()
    for conta, r in json.loads(REUSO.read_text("utf-8"))["tiktok"]["contas"].items():
        ck = ler(r["cofre"]) if r.get("cofre") else None
        if not ck or not any("tiktok" in c["domain"] for c in ck["cookies"]):
            continue
        try:
            t = TikTokStudio(conta, navegador=False)
            vids = t.videos(100)
            velhos = [v for v in vids if agora - v["quando"] > 48 * 3600]
            top = max(vids, key=lambda v: v["views"]) if vids else None
            out.append({"conta": conta, "arroba": t.arroba, "resumo": t.conta_resumo(dias), "n_videos": len(vids),
                        "views_videos": sum(v["views"] for v in vids),
                        "zerados_48h": sum(1 for v in velhos if v["views"] == 0), "velhos_48h": len(velhos),
                        "sem_legenda": sum(1 for v in vids if (v["legenda"] or "").strip().lower() in ("", "video")),
                        "melhor": dict(t.video(top["id"]), link=top["link"], retencao=None) if top and top["views"] else None})
        except Exception as e:  # noqa: BLE001
            if "sem_login" not in str(e):
                out.append({"conta": conta, "erro": f"{type(e).__name__}: {str(e)[:160]}"})
            continue
        print(f"tiktok {conta:24} ok", flush=True)
        time.sleep(5)
    return out


def gravar_contas_tiktok(tt):
    """relatorios\\saida\\contas_tiktok.json: o painel :8790 (aba Contas + problemas) destaca as mortas por ele.
    Morta = 10+ vídeos com mais de 48 h e nenhuma view somando todos (o TikTok não entrega)."""
    contas = {}
    for c in tt:
        if "erro" in c:
            continue
        contas[c["conta"]] = {"arroba": c["arroba"], "seguidores": c["resumo"]["seguidores"],
                              "views_7d": sum(x or 0 for x in c["resumo"]["views_dia"]), "videos": c["n_videos"],
                              "views_videos": c["views_videos"], "zerados_48h": c["zerados_48h"],
                              "velhos_48h": c["velhos_48h"], "sem_legenda": c["sem_legenda"],
                              "morta": c["velhos_48h"] >= 10 and c["views_videos"] == 0}
    SAIDA.mkdir(parents=True, exist_ok=True)
    gravar_json(SAIDA / "contas_tiktok.json",  # atômico: o painel :8790 lê este arquivo a qualquer hora
                {"quando": datetime.now().isoformat(timespec="seconds"), "contas": contas})


def analisar(canais, dias):
    por_nicho = defaultdict(lambda: {"inscritos": 0, "views": 0, "canais": 0})
    for c in canais:
        n = por_nicho[c["nicho"]]
        n["canais"] += 1
        n["inscritos"] += sum(v["inscritos"] or 0 for v in c["videos"])
        n["views"] += sum(v["views"] or 0 for v in c["videos"])
    todos = [dict(v, canal=c["slug"], nicho=c["nicho"]) for c in canais for v in c["videos"]]
    # CTR só de quem teve impressão de miniatura de verdade (Shorts no feed quase não têm)
    com_ctr = [v for v in todos if (v.get("impressoes") or 0) >= 100 and v.get("ctr") is not None and v["titulo"]]
    tracos = defaultdict(lambda: [0.0, 0])  # traço -> [soma ctr*impr, soma impr]
    for v in com_ctr:
        for k, sim in estrutura(v["titulo"]).items():
            chave = f"{k}={'sim' if sim else 'nao'}"
            tracos[chave][0] += v["ctr"] * v["impressoes"]
            tracos[chave][1] += v["impressoes"]
    ctr_tracos = {k: round(s / i, 2) for k, (s, i) in sorted(tracos.items()) if i}
    shorts = [v for v in todos if (v.get("shorts_impressoes") or 0) >= 50 and v.get("shorts_ficaram_pct") is not None]
    termos = defaultdict(lambda: defaultdict(int))
    for c in canais:
        for t in c["termos"]:
            termos[c["nicho"]][t["termo"]] += t["views"] or 0
    return {
        "nichos": dict(sorted(por_nicho.items(), key=lambda x: -x[1]["inscritos"])),
        "ctr_por_traco": ctr_tracos,
        "titulos_campeoes": sorted(com_ctr, key=lambda v: -v["ctr"])[:10],
        "shorts_seguraram": sorted([v for v in shorts if v["shorts_ficaram_pct"] >= 75],
                                   key=lambda v: -v["shorts_ficaram_pct"])[:10],
        "shorts_perderam": sorted([v for v in shorts if v["shorts_ficaram_pct"] < 50],
                                  key=lambda v: v["shorts_ficaram_pct"])[:10],
        "zerados": [dict(z, canal=c["slug"]) for c in canais for z in c["zerados"]],
        "termos_por_nicho": {n: sorted(d.items(), key=lambda x: -x[1])[:10] for n, d in termos.items()},
        "melhor_canal_shorts": sorted([{"canal": c["slug"], **c["shorts"]} for c in canais
                                       if (c["shorts"]["impressoes_feed"] or 0) >= 100],
                                      key=lambda x: -(x["ficaram_pct"] or 0))[:10],
    }


def markdown(rel):
    a, d = rel["analise"], rel["dias"]
    L = [f"# Central de inteligência — {rel['quando']} (últimos {d} dias)", "",
         f"Canais lidos: {len(rel['canais'])} · sem login: {', '.join(rel['sem_login']) or 'nenhum'} · "
         f"com erro: {', '.join(e['slug'] for e in rel['erros']) or 'nenhum'}", "",
         "## 1. Nicho que mais deu inscritos", "", "| Nicho | Inscritos | Views | Canais |", "|---|---:|---:|---:|"]
    L += [f"| {n} | {v['inscritos']} | {v['views']} | {v['canais']} |" for n, v in a["nichos"].items()]
    L += ["", "## 2. CTR por estrutura de título (vídeos com 100+ impressões)", "",
          "| Traço | CTR médio % |", "|---|---:|"]
    L += [f"| {k} | {v} |" for k, v in a["ctr_por_traco"].items()]
    L += ["", "**Títulos campeões de CTR:**", ""]
    L += [f"- {v['ctr']}% · {v['impressoes']} impr · {v['canal']} · {v['titulo']}" for v in a["titulos_campeoes"]]
    L += ["", "## 3. Vídeos zerados (>48 h, menos de 10 views) — reeditar ou tirar", ""]
    L += [f"- {z['canal']} · {z['views']} views em {z['horas_no_ar']} h · {z['titulo']} (https://youtu.be/{z['id']})"
          for z in a["zerados"][:40]] or ["- nenhum"]
    L += ["", "## 4. Shorts: quem segurou o feed (>=75% ficaram) e quem perdeu (<50%)", ""]
    L += [f"- ✅ {v['shorts_ficaram_pct']}% de {v['shorts_impressoes']} · {v['canal']} · {v['titulo']}"
          for v in a["shorts_seguraram"]]
    L += [f"- ❌ {v['shorts_ficaram_pct']}% de {v['shorts_impressoes']} · {v['canal']} · {v['titulo']}"
          for v in a["shorts_perderam"]]
    L += ["", "**Canais que mais seguram no feed dos Shorts:** " + ", ".join(
        f"{x['canal']} {x['ficaram_pct']}%" for x in a["melhor_canal_shorts"]), "",
          "## 5. Termos de busca reais por nicho", ""]
    for n, ts in a["termos_por_nicho"].items():
        if ts:
            L.append(f"- **{n}**: " + ", ".join(f"{t} ({v})" for t, v in ts))
    if rel.get("instagram"):
        L += ["", "## 6. Instagram (Reels)", "", "| Conta | Seguidores | Views 12 últimos | Melhor Reel |",
              "|---|---:|---:|---|"]
        for c in rel["instagram"]:
            if "erro" in c:
                L.append(f"| {c['conta']} | erro: {c['erro'][:60]} | | |")
                continue
            rs = c["reels"]
            top = max(rs, key=lambda r: r["views"] or 0) if rs else {}
            L.append(f"| {c['conta']} | {c['perfil'].get('seguidores')} | {sum(r['views'] or 0 for r in rs)} | "
                     f"{top.get('views')} views https://www.instagram.com/reel/{top.get('codigo')}/ |")
    if rel.get("tiktok"):
        tt = rel["tiktok"]
        L += ["", "## 7. TikTok", "",
              "| Conta | Seguidores | Views 7 dias | Vídeos | Zerados (>48 h) | Legenda \"Video\" | Melhor vídeo |",
              "|---|---:|---:|---:|---:|---:|---|"]
        for c in tt:
            if "erro" in c:
                L.append(f"| {c['conta']} | erro: {c['erro'][:60]} | | | | | |")
                continue
            m = c["melhor"]
            melhor = (f"{m['views']} views, {m['tempo_medio_s']} s de {m['duracao_s']} s, conclusão "
                      f"{round((m['conclusao'] or 0) * 100, 1)}% {m['link']}") if m else "—"
            L.append(f"| {c['conta']} (@{c['arroba']}) | {c['resumo']['seguidores']} | "
                     f"{sum(x or 0 for x in c['resumo']['views_dia'])} | {c['n_videos']} | "
                     f"{c['zerados_48h']}/{c['velhos_48h']} | {c['sem_legenda']} | {melhor} |")
        mortas = [c for c in tt if "erro" not in c and c["velhos_48h"] >= 10 and c["views_videos"] == 0]
        if mortas:
            L += ["", "**Contas sem nenhuma view em nenhum vídeo (o TikTok não está entregando):** " +
                  ", ".join(f"{c['conta']} ({c['n_videos']} vídeos)" for c in mortas)]
    return "\n".join(L) + "\n"


def main():
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=7)
    ap.add_argument("--canais")
    ap.add_argument("--instagram", action="store_true")
    ap.add_argument("--tiktok", action="store_true")
    ap.add_argument("--com-navegador", action="store_true", help="deixa ressincronizar cookie vencido pelo cofre")
    a = ap.parse_args()
    if not a.com_navegador:
        youtube_http.sincronizar = _sem_navegador
    slugs = a.canais.split(",") if a.canais else list(youtube_http._mapa())
    nichos = _nichos()
    rel = {"quando": datetime.now().strftime("%Y-%m-%d %H:%M"), "dias": a.dias, "canais": [], "sem_login": [],
           "erros": []}
    for slug in slugs:
        t0 = time.time()
        try:
            rel["canais"].append(coletar_canal(slug, a.dias, nichos))
            print(f"{slug:24} ok ({time.time() - t0:.1f}s)", flush=True)
        except Exception as e:  # noqa: BLE001
            if "sem_login" in str(e) or "não reconheceu" in str(e):
                rel["sem_login"].append(slug)
            else:
                rel["erros"].append({"slug": slug, "erro": f"{type(e).__name__}: {str(e)[:200]}",
                                     "onde": traceback.format_exc()[-400:]})
            print(f"{slug:24} {type(e).__name__}: {str(e)[:100]}", flush=True)
    if a.instagram:
        rel["instagram"] = coletar_instagram()
    if a.tiktok:
        rel["tiktok"] = coletar_tiktok(a.dias)
        gravar_contas_tiktok(rel["tiktok"])
    rel["analise"] = analisar(rel["canais"], a.dias)
    SAIDA.mkdir(parents=True, exist_ok=True)
    gravar_json(SAIDA / f"inteligencia_{datetime.now():%Y%m%d}.json", rel)
    gravar_texto(SAIDA / "INTELIGENCIA.md", markdown(rel))
    print(f"\nok: {len(rel['canais'])} canais, {len(rel['sem_login'])} sem login, {len(rel['erros'])} erros -> "
          f"{SAIDA / 'INTELIGENCIA.md'}")


if __name__ == "__main__":
    main()
