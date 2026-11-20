"""Até quantas Páginas VALE A PENA num perfil (dona 20/11/2026: "observar não só até quanto o Facebook deixa criar
Páginas, mas até quantas vale a pena no mesmo perfil — no TikTok, muitas postagens pelo mesmo IP = não veicula, fica em
0; no Facebook não dá pra fugir disso porque o mesmo perfil gerencia várias, então não adianta proxy por Página").

Ideia: um perfil = uma saída fixa (Webshare rnprmtfo-58 no emersonjosiel02). O que pode cair é o ALCANCE de cada
Reel conforme o perfil soma Páginas/posts. Então mede, a cada medição do fb_medir (logs/fb_views.jsonl):
  - views por Reel com 24-72 h, separado por "lote" de Páginas (ordem de criação: 1-5, 6-10, ...);
  - a mediana dos Reels NOVOS (últimos 3 dias) x a mediana da 1ª semana do perfil.
Regra (trava no fb_criar_fila): se a mediana dos Reels novos cair abaixo de QUEDA (40%) da referência com >= 15 Reels
medidos, o perfil está saturando -> PARA de criar Páginas (marca 'saturado' no estado da fila) e avisa.
Relatório: FACEBOOK_SATURACAO.md.

    python fb_saturacao.py          # roda depois do fb_medir (tarefa FacebookInteligencia)
"""
import json, os, statistics, sys
from datetime import datetime, timedelta
from pathlib import Path

BIN = Path(__file__).resolve().parent
CFG = BIN.parent / "config" / "facebook_paginas.json"
VIEWS = BIN.parent / "logs" / "fb_views.jsonl"
REG = BIN.parent / "logs" / "facebook_paginas.json"
EST = BIN.parent / "logs" / "fb_fila_estado.json"
MD = BIN.parent / "FACEBOOK_SATURACAO.md"
QUEDA = 0.40
MIN_REELS = 15


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return padrao


def analisar():
    cfg = _ler(CFG, {})
    pags = cfg.get("paginas", {})
    # 1ª vez que cada reel apareceu + views na última medição
    visto, ultimo = {}, {}
    if VIEWS.exists():
        for linha in VIEWS.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(linha)
            except Exception:
                continue
            for x in r.get("reels", []):
                if x.get("views") is None:
                    continue
                k = (r["pagina"], x["id"])
                visto.setdefault(k, r["quando"])
                ultimo[k] = (r["quando"], x["views"])
    agora = datetime.now()
    por_conta = {}
    for (pag, rid), primeira in visto.items():
        conta = (pags.get(pag) or {}).get("conta")
        if not conta or (pags.get(pag) or {}).get("pausada"):
            continue
        quando, v = ultimo[(pag, rid)]
        idade_h = (datetime.fromisoformat(quando[:19]) - datetime.fromisoformat(primeira[:19])).total_seconds() / 3600
        por_conta.setdefault(conta, []).append({"pagina": pag, "id": rid, "desde": primeira, "views": v, "idade_h": idade_h})
    out = {}
    for conta, reels in por_conta.items():
        ordem = sorted({r["pagina"] for r in reels}, key=lambda p: min(x["desde"] for x in reels if x["pagina"] == p))
        lote = {p: i // 5 + 1 for i, p in enumerate(ordem)}
        inicio = min(r["desde"] for r in reels)
        ref = [r["views"] for r in reels if r["desde"] < (datetime.fromisoformat(inicio[:19]) + timedelta(days=7)).isoformat()]
        novos = [r["views"] for r in reels if r["desde"] >= (agora - timedelta(days=3)).isoformat()]
        mref = statistics.median(ref) if ref else None
        mnov = statistics.median(novos) if novos else None
        saturando = bool(mref and mnov is not None and len(novos) >= MIN_REELS and len(ref) >= MIN_REELS
                         and (agora - datetime.fromisoformat(inicio[:19])) > timedelta(days=7) and mnov < QUEDA * mref)
        por_lote = {}
        for r in reels:
            por_lote.setdefault(lote[r["pagina"]], []).append(r["views"])
        out[conta] = {"paginas": len(ordem), "reels": len(reels), "mediana_1a_semana": mref, "mediana_3_dias": mnov,
                      "n_novos": len(novos), "saturando": saturando,
                      "por_lote": {f"Páginas {5 * (l - 1) + 1}-{5 * l}": (round(statistics.median(v)), len(v))
                                   for l, v in sorted(por_lote.items())}}
    return out


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    res = analisar()
    linhas = ["# Saturação do perfil no Facebook (fb_saturacao.py)", "",
              f"Atualizado {datetime.now():%d/%m %H:%M}. Regra: mediana de views dos Reels dos últimos 3 dias < "
              f"{int(QUEDA * 100)}% da 1ª semana (com >= {MIN_REELS} Reels nos dois) = perfil saturando -> para de criar Páginas.", ""]
    est = _ler(EST, {})
    for conta, r in res.items():
        linhas += [f"## {conta}", f"- Páginas ativas: {r['paginas']} | Reels medidos: {r['reels']}",
                   f"- Mediana 1ª semana: {r['mediana_1a_semana']} | últimos 3 dias: {r['mediana_3_dias']} ({r['n_novos']} Reels)",
                   f"- **{'SATURANDO — criação parada' if r['saturando'] else 'ok'}**", "",
                   "| Lote de Páginas (ordem de criação) | Mediana de views por Reel | Reels |", "|---|---|---|"]
        linhas += [f"| {k} | {v[0]} | {v[1]} |" for k, v in r["por_lote"].items()] + [""]
        c = est.setdefault("contas", {}).setdefault(conta, {})
        if r["saturando"] and not c.get("saturado"):
            c["saturado"] = datetime.now().isoformat(timespec="seconds")
            try:
                sys.path.insert(0, r"D:\video-fila")
                import avisos
                avisos.enviar(f"Facebook: perfil {conta} saturando (Reels novos {r['mediana_3_dias']} views x "
                              f"{r['mediana_1a_semana']} na 1ª semana, {r['paginas']} Páginas) — criação de Páginas parada",
                              "facebook_paginas", importante=True)
            except Exception:
                pass
        elif not r["saturando"] and c.get("saturado"):
            c.pop("saturado")
        print(conta, r)
    tmp = EST.with_suffix(".sat.tmp")
    tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, EST)
    MD.write_text("\n".join(linhas), encoding="utf-8")


if __name__ == "__main__":
    main()
