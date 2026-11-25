r"""Gera os dados do painel de visualizações do Facebook (dona 23/11/2026: "relatório completo por página, por vídeo
e geral, atualizando sozinho e quando eu pedir, no painel com gráficos").

Só LÊ arquivos locais (não fala com o Facebook): logs\fb_views.jsonl (medições), config\facebook_paginas.json
(páginas/contas), logs\facebook_paginas.json (postados/erros). Escreve D:\video-fila\painel_web\fb_views.json,
que a página painel_web\facebook.html desenha. A medição em si é do services.facebook.medir (HTTP, saída fixa
de cada conta), chamada pelo cron_fb_painel.bat (tarefa PainelFacebookViews, de hora em hora).
"""
import json
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(r"D:\postador-de-videos")
VIEWS = RAIZ / "logs" / "fb_views.jsonl"
CFG = RAIZ / "config" / "facebook_paginas.json"
REG = RAIZ / "logs" / "facebook_paginas.json"
SAIDA = Path(r"D:\video-fila\painel_web\fb_views.json")


def _ler_jsonl(p):
    out = []
    if not p.exists():
        return out
    for linha in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(linha))
        except ValueError:
            pass
    return out


def _dias(a, b):
    try:
        return max((datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 86400, 0)
    except ValueError:
        return 0


def montar():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    paginas_cfg = cfg.get("paginas", {})
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}
    postados, erros = reg.get("postados", {}), reg.get("erros", {})
    medicoes = _ler_jsonl(VIEWS)
    agora = datetime.now().isoformat(timespec="seconds")

    por_pag = {}
    for r in medicoes:
        # 25/11: o campo "views" da API bate com a medição HTTP (Bicho 1231 x 1232) e é mais novo — vale igual
        if r.get("reels"):
            por_pag.setdefault(r["pagina"], []).append(r)

    # 1ª vez que cada reel apareceu (para "views por dia de vida")
    primeira_vista = {}
    for r in medicoes:
        for x in r.get("reels") or []:
            primeira_vista.setdefault(x["id"], r["quando"])

    # 25/11: id do Reel -> "api" (o postador pela API grava o video_id); o resto é Chrome
    via_por_id = {str(e.get("video_id")): e.get("via", "chrome") for ps in postados.values() for e in ps
                  if isinstance(e, dict) and e.get("video_id")}
    paginas, videos, serie_geral = [], [], {}
    for chave, p in paginas_cfg.items():
        rs = por_pag.get(chave, [])
        ult = rs[-1] if rs else None
        reels = ult["reels"] if ult else []
        total = sum(x["views"] for x in reels)
        # série: última medição de cada dia (soma de views da página)
        dia = {}
        for r in rs:
            dia[r["quando"][:10]] = sum(x["views"] for x in r["reels"])
        for d, v in dia.items():
            serie_geral.setdefault(d, {})[chave] = v
        # ganho nas últimas ~24 h
        ganho24 = None
        if ult:
            ant = next((r for r in reversed(rs) if _dias(r["quando"], ult["quando"]) >= 0.9), None)
            if ant:
                ganho24 = total - sum(x["views"] for x in ant["reels"])
        lista_post = postados.get(chave, []) or []
        lista_err = erros.get(chave, []) or []
        primeiro = min((e.get("quando", "") for e in lista_post if isinstance(e, dict)), default="")
        idade = _dias(primeiro, agora) if primeiro else 0
        esperado = int(round(idade * (p.get("por_dia") or 3)))
        paginas.append({
            "chave": chave, "nome": p.get("nome", chave), "conta": p.get("conta"), "pausada": bool(p.get("pausada")),
            "seguidores": (ult or {}).get("seguidores") or 0, "reels": len(reels), "views": total,
            "media": round(total / len(reels)) if reels else 0, "ganho24": ganho24,
            "postados": len(lista_post), "erros": len(lista_err), "esperado": esperado,
            "idade_dias": round(idade, 1), "medido": (ult or {}).get("quando"),
            "serie": sorted(dia.items()),
        })
        for x in reels:
            nasc = primeira_vista.get(x["id"], ult["quando"])
            vida = max(_dias(nasc, ult["quando"]), 0.5)
            videos.append({"id": x["id"], "pagina": p.get("nome", chave), "chave": chave, "views": x["views"],
                           "visto_desde": nasc, "por_dia": round(x["views"] / vida),
                           "via": via_por_id.get(x["id"], "chrome")})

    paginas.sort(key=lambda d: d["views"], reverse=True)
    videos.sort(key=lambda d: d["views"], reverse=True)
    geral = [{"dia": d, "views": sum(v.values())} for d, v in sorted(serie_geral.items())]
    dados = {
        "gerado": agora,
        "ultima_medicao": max((r["quando"] for r in medicoes), default=None),
        "totais": {"views": sum(p["views"] for p in paginas), "reels": len(videos),
                   "paginas": sum(1 for p in paginas if not p["pausada"]),
                   "seguidores": sum(p["seguidores"] for p in paginas),
                   "postados": sum(p["postados"] for p in paginas), "erros": sum(p["erros"] for p in paginas)},
        "geral": geral, "paginas": paginas, "videos": videos,
    }
    tmp = SAIDA.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    tmp.replace(SAIDA)
    return dados


if __name__ == "__main__":
    d = montar()
    t = d["totais"]
    print(f"painel FB: {t['views']} views | {t['reels']} reels | {t['paginas']} páginas -> {SAIDA}")
    sys.exit(0)
