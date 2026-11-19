# -*- coding: utf-8 -*-
"""Celulares para o sistema do YouTube (19/11/2026): lê estado/pm_celular_julgados.json (pesquisa_mercado.py celular)
e gera pesquisa/CELULARES.md com 2 listas: por preço total (faixas até 100/150/200/300) e "mais vale a pena".
Regras da dona: Android >= 11 (depuração Wi-Fi), funcionando, touch ok, tela dá pra ver (rachada serve),
sem conta Google presa, frete REAL até Paragominas, total < R$ 300."""
import json, re, sys, time

import olx_buscas as o

TETO = 300
FAIXAS = [(100, "até R$ 100"), (150, "R$ 101 a 150"), (200, "R$ 151 a 200"), (300, "R$ 201 a 300")]

# força aproximada do processador por modelo (0-10); o resto cai no padrão 4
FORTE = [(r"a7[0-9]|a5[0-9]|s\d|note 1[0-9]|note [89] pro|poco|g8[0-9]|g7[0-9]|g6[0-9]|edge|one vision|one action|"
          r"m3[0-9]|m5[0-9]|k6[0-9]", 7),
         (r"a3[0-9]|a2[0-9]|g9|g2[0-9]|g3[0-9]|g5[0-9]|redmi 9|redmi 10|note 8|note 9|m2[0-9]", 5),
         (r"a1[0-9]|a0[0-9]|e[0-9]|e1[0-9]|e2[0-9]|e3[0-9]|redmi a|core|k4|k5", 3)]


def forca(modelo):
    m = (modelo or "").lower()
    for pad, n in FORTE:
        if re.search(pad, m):
            return n
    return 4


def itens():
    j = o.ler(o.BASE / "estado" / "pm_celular_julgados.json", {})
    out = []
    for k, v in j.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        if not (v.get("e_o_produto") and v.get("funciona") == "sim"):
            continue
        if v.get("conta_google_bloqueada") is True or v.get("tela") == "inutilizável" or v.get("touch") == "falhando":
            continue
        a = v.get("android") or v.get("android_estimado")
        try:
            a = float(a)
        except (TypeError, ValueError):
            continue
        if a < 11 or not isinstance(v.get("frete"), (int, float)):
            continue
        pr = v["preco_real"] if isinstance(v.get("preco_real"), (int, float)) and v["preco_real"] > 0 else v["preco"]
        tot = round(pr + v["frete"])
        if tot >= TETO:
            continue
        txt = f"{v.get('outros_defeitos') or ''} {v.get('resumo') or ''}".lower()
        if v.get("bateria") == "estufada" or re.search(r"wi-?fi n[ãa]o|sem wi-?fi|wi-?fi com defeito|defeito no wi-?fi", txt):
            continue  # Wi-Fi é obrigatório (ADB sem fio); bateria estufada na tomada 24 h = risco
        defs = [x for x in (v.get("tela") if v.get("tela") not in ("ok", "nao_informado") else "",
                            "bateria " + v["bateria"] if v.get("bateria") not in ("ok", "nao_informado", None) else "",
                            (v.get("outros_defeitos") or "").strip()) if x]
        ram = v.get("ram_gb") if isinstance(v.get("ram_gb"), (int, float)) else None
        pontos = forca(v.get("marca_modelo")) + min(ram or 2, 6) + (a - 10) * 0.7 - 0.8 * len(defs)
        if v.get("bateria") == "estufada":
            pontos -= 3
        out.append(dict(v, pr=pr, tot=tot, a=a, ram=ram, defs="; ".join(defs) or "nada declarado",
                        pontos=round(pontos, 1), cb=round(pontos / tot * 100, 2)))
    return out


def lin(v, n=None):
    a = f"{v['a']:g}" + ("" if v.get("android") else "*")
    return (f"| {'' if n is None else str(n) + ' | '}R$ {v['tot']:.0f} | {v['pr']:.0f} + {v['frete']:.0f} | "
            f"{(v.get('marca_modelo') or '?')[:40]} | {a} | {v['ram'] or '?'} GB | {v['defs'][:70]} | {v['url']} |")


def relatorio():
    it = itens()
    L = [f"# Celulares Android para o sistema do YouTube — {time.strftime('%d/%m/%Y')}",
         "Total = preço + frete REAL até Paragominas, abaixo de R$ 300. Android 11+ (depuração Wi-Fi, Termux, "
         "Tailscale), funcionando, touch ok, sem conta Google presa; tela rachada serve se dá pra ver.",
         "Android com * = estimado pelo modelo (o anúncio não diz) — confirmar com o vendedor.", ""]
    cab = "| Total | Preço + frete | Celular | Android | RAM | Defeitos | Link |\n|---|---|---|---|---|---|---|"
    L.append("## Lista por preço")
    ant = 0
    for lim, nome in FAIXAS:
        g = sorted([v for v in it if ant < v["tot"] <= lim], key=lambda v: v["tot"])
        L.append(f"\n### {nome}" + ("" if g else " — nenhum"))
        if g:
            L += [cab] + [lin(v) for v in g]
        ant = lim
    L.append("\n## Os que mais valem a pena (força do celular + RAM + Android − defeitos, por real gasto)")
    L.append("| # | Total | Preço + frete | Celular | Android | RAM | Defeitos | Link |\n|---|---|---|---|---|---|---|---|")
    for n, v in enumerate(sorted(it, key=lambda v: -v["cb"])[:20], 1):
        L.append(lin(v, n))
    (o.BASE / "pesquisa" / "CELULARES.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    relatorio()
