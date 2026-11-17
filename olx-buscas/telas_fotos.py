# -*- coding: utf-8 -*-
"""Monitor/TV (14/11/2026): pega os N mais baratos de cada tamanho já julgados por pesquisa_mercado.py (perfis monitor
e tv), olha as FOTOS com o Gemini (a tela é usável? quanto defeito?), recalcula o frete que faltou e grava
pesquisa/telas_fotos.json. Depois `python telas_fotos.py relatorio` monta pesquisa/MONITORES_TVS.md com
lista 1 (mais baratos usáveis) e lista 2 (defeito mínimo) por tamanho, ordenados pelo total (preço + frete)."""
import json, sys, time
from concurrent.futures import ThreadPoolExecutor

import olx_buscas as o

SAIDA = o.BASE / "pesquisa" / "telas_fotos.json"
N = 25
FAIXAS = [(17.9, "até 17\""), (19.9, "18-19\""), (22.9, "20-22\""), (24.9, "23-24\""), (29.9, "26-29\""),
          (34.9, "32\""), (42.9, "39-42\""), (49.9, "43-49\""), (55.9, "50-55\""), (999, "58\" ou mais")]
TUBO = ("tubo", "crt")

FOTO = """Fotos de um anúncio da OLX: {tipo} de {pol} polegadas. Título: {titulo}
O vendedor diz sobre a tela: "{defeito}"
A compradora vai usar como tela de computador/TV e aceita poucas linhas ou alguma mancha. Olhe TODAS as fotos,
principalmente as que mostram a tela LIGADA. Regras:
- Se NENHUMA foto mostra a tela ligada (todas apagadas, sem luz), usavel = false.
- Tela acesa com fundo uniforme (cinza/azul/roxo de "sem sinal") conta como ligada: julgue pelas linhas e manchas.
- Usável = a MAIOR PARTE da tela (uns 70% ou mais) mostra imagem limpa. Faixa estragada só numa borda, algumas listras
  verticais finas, mancha/vazamento num canto = usável (nota 5-7 conforme o tamanho do estrago).
- NÃO usável (nota ≤ 3): tela toda preta sem nada visível, imagem tremida/duplicada/embaralhada na tela inteira,
  metade ou mais sem imagem, listras cobrindo a maior parte.
- Nota 8-9 só se o defeito é pequeno: 1-2 linhas finas ou uma mancha pequena.
Responda SÓ um JSON:
{{"aparece_ligada": true/false (alguma foto mostra imagem na tela),
 "tubo": true/false (é TV/monitor de tubo CRT, caixa funda),
 "defeito_visto": "o que se vê na tela ligada: linhas (quantas, onde), manchas (tamanho), trincas... ou 'nenhum'",
 "nota": 0-10 (10 = tela perfeita; 8-9 = mancha/linha pequena que quase não atrapalha; 5-7 = defeito visível mas dá
         para usar; 1-4 = atrapalha muito; 0 = inutilizável ou trincada),
 "usavel": true/false,
 "contradiz": "algo nas fotos que contradiga o anúncio (outro tamanho, tela apagada, foto de internet) ou vazio"}}"""


def faixa(p):
    for lim, nome in FAIXAS:
        if p <= lim:
            return nome


def candidatos():
    out = []
    for perfil in ("monitor", "tv"):
        j = o.ler(o.BASE / "estado" / f"pm_{perfil}_julgados.json", {})
        for k, v in j.items():
            if k.startswith("_") or not isinstance(v, dict):
                continue
            if not (v.get("e_o_produto") and v.get("funciona") == "sim" and v.get("aceitavel") and v.get("fotos")):
                continue
            try:
                pol = float(v.get("polegadas"))
            except (TypeError, ValueError):
                continue
            txt = f"{v.get('titulo')} {v.get('resumo')}".lower()
            if any(t in txt for t in TUBO):
                continue
            pr = v["preco_real"] if isinstance(v.get("preco_real"), (int, float)) and v["preco_real"] > 0 else v["preco"]
            out.append(dict(v, id=k, perfil=perfil, pol=pol, pr=pr, faixa=faixa(pol)))
    return out


def olhar(v):
    r = {}
    if not isinstance(v.get("frete"), (int, float)):
        try:
            time.sleep(1)
            d = o.detalhe(v["url"])
            r["frete"] = d.get("frete")
            v["fotos"] = d["fotos"][:8] or v["fotos"]
        except Exception as e:
            return {"erro": str(e)[:80]}
    defeito = "; ".join(x for x in (v.get("defeitos_tela"), v.get("outros_defeitos")) if x) or "nada"
    for _ in range(2):
        try:
            f = o.ler_fotos(v["fotos"], FOTO.format(tipo=v.get("tipo") or v["perfil"], pol=v["pol"],
                                                    titulo=v.get("titulo"), defeito=defeito), max_fotos=8)
            if f and "nota" in f:
                r["foto"] = f
                break
        except Exception:
            time.sleep(5)
    return r


def coletar():
    feitos = o.ler(SAIDA, {})
    cand = candidatos()
    alvo = []
    for nome in {c["faixa"] for c in cand}:
        g = sorted([c for c in cand if c["faixa"] == nome], key=lambda c: c["pr"])[:N]
        alvo += [c for c in g if c["id"] not in feitos]
    print("olhando fotos de", len(alvo), flush=True)
    with ThreadPoolExecutor(3) as ex:
        for i, (v, r) in enumerate(zip(alvo, ex.map(olhar, alvo)), 1):
            feitos[v["id"]] = dict(v, **r)
            if i % 10 == 0:
                o.gravar(SAIDA, feitos)
                print(i, flush=True)
    o.gravar(SAIDA, feitos)


def conferir():
    """Reabre os que estão aprovados: anúncio saiu do ar = 'vendido'; atualiza frete e preço."""
    feitos = o.ler(SAIDA, {})
    alvo = [v for v in feitos.values() if (v.get("foto") or {}).get("aparece_ligada") and not v.get("vendido")]
    print("conferindo", len(alvo), flush=True)

    def um(v):
        time.sleep(1)
        try:
            d = o.detalhe(v["url"])
            v["frete"] = d.get("frete") if d["entrega"] else None
        except Exception as e:
            if "410" in str(e) or "404" in str(e):
                v["vendido"] = True
        return v
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(um, alvo))
    o.gravar(SAIDA, feitos)
    print("saíram do ar", sum(1 for v in alvo if v.get("vendido")), flush=True)


def relatorio():
    feitos = o.ler(SAIDA, {})
    itens = []
    for v in feitos.values():
        if v.get("vendido"):
            continue
        f = v.get("foto") or {}
        if not f or not f.get("aparece_ligada") or (f.get("nota") or 0) < 4 or f.get("tubo"):
            continue
        if not isinstance(v.get("frete"), (int, float)):
            continue  # sem envio cotado para Paragominas (OLX só oferece "Retirar")
        v["faixa"] = faixa(v["pol"])
        v["est"] = False
        v["fr"] = v["frete"]
        v["tot"] = v["pr"] + v["fr"]
        itens.append(v)
    L = [f"# Monitores e TVs baratos com entrega — atualizado em {time.strftime('%d/%m/%Y')}",
         "Total = preço + frete REAL até Paragominas (só entra quem a OLX envia para lá; 'só retirar' sai). "
         "Fotos olhadas pela IA.",
         "Lista 1 = os mais baratos com a tela ACESA na foto (sai quem só tem foto apagada ou tela inútil). "
         "Lista 2 = defeito mínimo (nota ≥ 8). Nota 0-10 dada pelo Gemini olhando as fotos; ⚠️ = o Gemini "
         "achou que não dá para usar (confira a foto).", ""]
    cab = "| Total | Preço | Frete | Pol | Tipo | O que se vê na tela (fotos) | Nota | Link |\n|---|---|---|---|---|---|---|---|"

    def lin(v):
        f = v["foto"]
        return (f"| R$ {v['tot']:.0f} | {v['pr']} | {v['fr']:.0f}{'*' if v['est'] else ''} | {v['pol']:g} | "
                f"{v.get('tipo') or v['perfil']} | {str(f.get('defeito_visto'))[:90]} | {f.get('nota')}"
                f"{'' if f.get('usavel') else ' ⚠️'} | "
                f"[abrir]({v['url']}) |")
    for _, nome in reversed(FAIXAS):
        g = sorted([v for v in itens if v["faixa"] == nome], key=lambda v: v["tot"])
        if not g:
            continue
        L.append(f"## {nome}")
        L += ["**Lista 1 — mais baratos usáveis**", cab] + [lin(v) for v in g[:6]]
        t2 = [v for v in g if (v["foto"].get("nota") or 0) >= 8][:5]
        L += ["", "**Lista 2 — defeito mínimo**"] + ([cab] + [lin(v) for v in t2] if t2 else ["nenhum achado"]) + [""]
    (o.BASE / "pesquisa" / "MONITORES_TVS.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    {"coletar": coletar, "conferir": conferir, "relatorio": relatorio}[sys.argv[1]]()
