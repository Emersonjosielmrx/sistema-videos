# -*- coding: utf-8 -*-
"""Acessórios PS3/PS4/PS5: melhor USADO na OLX (com entrega, funcionando) x NOVO no Mercado Livre (original e genérico).
A dona (04/11/2026): "acessórios que valham a pena — alguns saem mais barato novo no Mercado Livre".
  python pesquisa_acessorios.py          -> roda tudo e grava pesquisa/acessorios.json
"""
import json, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import olx_buscas as o

ITENS = [
    {"id": "ds3", "nome": "Controle PS3 DualShock 3 ORIGINAL Sony", "q": "controle ps3 original", "min": 40,
     "ml": "controle ps3 dualshock 3 original sony"},
    {"id": "ds4", "nome": "Controle PS4 DualShock 4 ORIGINAL Sony", "q": "controle ps4 original", "min": 60,
     "ml": "controle ps4 dualshock 4 original sony"},
    {"id": "dualsense", "nome": "Controle PS5 DualSense ORIGINAL Sony", "q": "dualsense", "min": 120,
     "ml": "controle dualsense ps5 original sony"},
    {"id": "base_ps5", "nome": "Base/estação de carregamento para 2 controles DualSense", "q": "base carregador dualsense",
     "min": 20, "ml": "base carregador controle dualsense ps5"},
    {"id": "hd_1tb", "nome": "HD 2,5 polegadas 1TB (para PS3/PS4)", "q": "hd 1tb notebook 2,5", "min": 50,
     "ml": "hd 1tb 2,5 sata notebook", "cat": "https://www.olx.com.br/informatica?q={q}&opst=2&sp=1&ps={min}"},
    {"id": "ssd_ps5", "nome": "SSD NVMe M.2 1TB compatível com PS5 (com dissipador)", "q": "ssd nvme 1tb ps5",
     "min": 150, "ml": "ssd nvme m.2 1tb ps5 dissipador",
     "cat": "https://www.olx.com.br/informatica?q={q}&opst=2&sp=1&ps={min}"},
    {"id": "headset", "nome": "Headset sem fio Sony Pulse 3D (PS5/PS4)", "q": "pulse 3d", "min": 100,
     "ml": "headset sony pulse 3d"},
]
OLX_CAT = "https://www.olx.com.br/games/acessorios-de-video-game?q={q}&opst=2&sp=1&ps={min}"

TRI = """Títulos de anúncios da OLX (id | preço | título). Procuro: {nome}, o produto inteiro (usado serve).
Descarte peças/botões/molas/carcaças/capas/suportes/adesivos, "compatível"/"paralelo"/"similar" quando pedi ORIGINAL,
lotes de outros itens, conserto, troca.
{lista}
Responda SÓ um JSON: {{"manter": [ids]}}"""

JUL = """Anúncio usado da OLX. Procuro: {nome}.
Título: {titulo} | Preço: {preco}
Descrição: \"\"\"{desc}\"\"\"
Responda SÓ um JSON:
{{"e_o_item": true/false, "original": true/false/null, "funciona": "sim"|"nao"|"incerto",
 "defeitos": "drift, botão falhando, bateria fraca, setores ruins... ou vazio", "qtd": número de unidades no anúncio,
 "preco_real": preço por unidade se diferente, ou null, "resumo": "1 frase"}}"""

ML_PICK = """Resultados do Mercado Livre (n | preço | título | vendedor). Procuro: {nome}.
Escolha: (a) o mais barato que seja NOVO e ORIGINAL de verdade (Sony/marca real, vendedor oficial ou loja confiável,
não "compatível"), (b) o mais barato genérico/compatível que sirva para a mesma função (se existir). Ignore itens que não
são esse produto (outro console, peças, capas).
{lista}
Responda SÓ um JSON: {{"original": n ou null, "generico": n ou null, "obs": "curta"}}"""


def olx(item):
    url = item.get("cat", OLX_CAT).format(q=quote(item["q"]), min=item["min"])
    ads = []
    for pg in range(1, 4):
        try:
            ads += o.baixar_anuncios(url + (f"&o={pg}" if pg > 1 else ""))
        except Exception as e:
            print("olx", e)
        time.sleep(1.5)
    ads = [a for a in ads if o.preco(a)]
    lista = "\n".join(f"{a['listId']} | {a.get('priceValue')} | {a.get('subject')}" for a in ads[:150])
    try:
        manter = {str(x) for x in o.ia(TRI.format(nome=item["nome"], lista=lista), max_tokens=4000).get("manter", [])}
    except Exception:
        manter = {str(a["listId"]) for a in ads}
    cand = sorted([a for a in ads if str(a["listId"]) in manter], key=o.preco)[:14]

    def jul(a):
        try:
            time.sleep(1.2)
            d = o.detalhe(a["url"])
            v = o.ia(JUL.format(nome=item["nome"], titulo=a.get("subject"), preco=a.get("priceValue"),
                                desc=d["descricao"][:2500]))
            v.update({"preco": o.preco(a), "titulo": a.get("subject"), "url": a["url"], "local": a.get("location")})
            return v
        except Exception as e:
            return None
    with ThreadPoolExecutor(3) as ex:
        res = [r for r in ex.map(jul, cand) if r]
    bons = [r for r in res if r.get("e_o_item") and r.get("funciona") == "sim" and r.get("original") is not False
            and not (r.get("defeitos") or "").strip()]
    for r in bons:
        if isinstance(r.get("preco_real"), (int, float)) and r["preco_real"] > 0:
            r["preco"] = r["preco_real"]
    return sorted(bons, key=lambda r: r["preco"])[:3], len(ads)


JS_ML = r"""() => Array.from(document.querySelectorAll('.poly-card')).slice(0,30).map(e => {
  const t = e.querySelector('.poly-component__title');
  const cur = e.querySelector('.poly-price__current .andes-money-amount__fraction');
  const cents = e.querySelector('.poly-price__current .andes-money-amount__cents');
  const v = e.querySelector('.poly-component__seller');
  return {t: t && t.innerText, href: t && t.href, p: cur ? parseFloat(cur.innerText.replace(/\./g,'') + '.' + (cents ? cents.innerText : '0')) : null,
          v: v && v.innerText};
})"""


def ml(pg, item):
    pg.goto("https://lista.mercadolivre.com.br/" + quote(item["ml"].replace(" ", "-")) + "_ITEM*CONDITION_2230284",
            wait_until="load")
    pg.wait_for_timeout(5000)
    cards = [c for c in pg.evaluate(JS_ML) if c.get("p") and c.get("t")]
    lista = "\n".join(f"{i} | R$ {c['p']} | {c['t']} | {c.get('v') or ''}" for i, c in enumerate(cards))
    try:
        r = o.ia(ML_PICK.format(nome=item["nome"], lista=lista), max_tokens=600)
    except Exception:
        r = {}
    out = {}
    for k in ("original", "generico"):
        n = r.get(k)
        if isinstance(n, int) and 0 <= n < len(cards):
            c = cards[n]
            out[k] = {"preco": c["p"], "titulo": c["t"], "url": (c["href"] or "").split("#")[0], "vendedor": c.get("v")}
    out["obs"] = r.get("obs")
    return out


def main():
    import olx_chat
    res = {}
    with ThreadPoolExecutor(2) as ex:
        futs = {it["id"]: ex.submit(olx, it) for it in ITENS}
    for it in ITENS:
        bons, total = futs[it["id"]].result()
        res[it["id"]] = {"nome": it["nome"], "olx": bons, "olx_total": total}
        print(it["id"], "OLX:", [(b["preco"], b["titulo"][:30]) for b in bons], flush=True)
    with olx_chat.navegador() as pg:
        for it in ITENS:
            try:
                res[it["id"]]["ml"] = ml(pg, it)
            except Exception as e:
                res[it["id"]]["ml"] = {"erro": str(e)[:80]}
            print(it["id"], "ML:", json.dumps(res[it["id"]]["ml"], ensure_ascii=False)[:200], flush=True)
    o.gravar(o.BASE / "pesquisa" / "acessorios.json", res)


if __name__ == "__main__":
    main()
