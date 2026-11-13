# -*- coding: utf-8 -*-
"""Pesquisa de mercado genérica na OLX (generaliza pesquisa_notebooks.py, que deu certo em 04/11/2026).

Cada PERFIL diz: onde buscar (URL da categoria + termo), teto, o que a IA extrai de cada anúncio e como agrupar/ranquear.
Fases (retomáveis; estado em estado/pm_<perfil>_*.json):
  python pesquisa_mercado.py <perfil> lista          varre a listagem (só páginas de lista, com entrega, menor preço primeiro)
  python pesquisa_mercado.py <perfil> abrir [N]      corte por título + triagem IA + abre e julga até N anúncios
  python pesquisa_mercado.py <perfil> verificar [N]  fotos + preço real nos N melhores
  python pesquisa_mercado.py <perfil> relatorio      gera pesquisa/<perfil>.md
Regras fixas da dona: só com entrega, Brasil todo, ler a DESCRIÇÃO (filtro do vendedor é só pista), tem que funcionar,
preço isca (preço do anúncio ≠ preço do item) é descartado.
"""
import json, re, sys, time
from concurrent.futures import ThreadPoolExecutor

import olx_buscas as o

SAIDA = o.BASE / "pesquisa"

LIXO_COMUM = (r"retirada de pe[çc]|retirar pe[çc]|p/ ?pe[çc]as|para pe[çc]as|pra pe[çc]as|para reparo|n[ãa]o liga|"
              r"sucata|somente pe[çc]as|aluguel|alugo|loca[çc][ãa]o|conserto|assist[êe]ncia|manuten[çc][ãa]o|"
              r"troco\b|procuro|compro\b|^\s*caixa\b|caixa vazia|somente a caixa|s[óo] a caixa")

CONSOLE_JSON = """ "e_o_console": true/false (false se for só jogo, controle, acessório, caixa, peça, outro console),
 "funciona": "sim" | "nao" | "incerto",
 "modelo": "ex.: PS3 Fat CECHA01 / Slim CECH-2501 / Super Slim CECH-4001; PS5 Fat CFI-1014A / Slim CFI-2014 / Pro; null",
 "versao": "disco" | "digital" | null,
 "desbloqueio": "CFW" | "HEN" | "GoldHEN" | "jailbreak" | "destravado (sem dizer qual)" | "travado" | "nao_informado",
 "firmware": "versão do sistema dita no anúncio ou nas fotos (ex.: 4.92, 3.55, 4.03, 7.61) ou null",
 "armazenamento": "ex.: 500GB, 1TB, HD 2TB externo, ou null",
 "controles": número de controles inclusos (0 se diz que não vem; null se não diz),
 "controle_original": true/false/null,
 "jogos": "jogos inclusos (físicos/instalados) resumido ou vazio",
 "cabos": "sim" | "nao" | "nao_informado",
 "defeitos": "defeitos declarados (leitor, YLOD, superaquecendo, HDMI, controle drift...) ou vazio",
 "preco_real": número ou null (preço DESTE console segundo a descrição, se diferente do anúncio),
 "resumo": "1 frase com o que importa citando o vendedor" """

PERFIS = {
    "ps3": {
        "url": "https://www.olx.com.br/games/consoles-de-video-game?q=ps3&opst=2&sp=1&pe={teto}",
        "teto": 1000,
        "o_que": "console PlayStation 3 (PS3) inteiro",
        "lixo": r"^\s*(controle|manete|jogo|jogos|cabo|fonte|hd\b|leitor|placa|carca[çc]a|cooler|volante|move|"
                r"headset|fone|suporte|case|capa|dualshock|carregador)",
        "triagem_extra": "Descarte PS2, PS4, PS5, PSP, Xbox e jogos/controles avulsos.",
        "json": CONSOLE_JSON,
        "contexto": "Para PS3: CFW só em modelos que aceitam (Fat e Slim até CECH-25xx; 30xx só se vier com firmware "
                    "≤3.56); Super Slim (CECH-4xxx) e demais aceitam só HEN. HEN roda em qualquer PS3 no firmware "
                    "oficial atual, então 'travado' pode ser desbloqueado em casa com HEN.",
        "grupo": lambda v: ("destravado" if v.get("desbloqueio") not in ("travado", "nao_informado", None)
                            else "travado/não diz"),
    },
    "ps5": {
        "url": "https://www.olx.com.br/games/consoles-de-video-game?q=ps5&opst=2&sp=1&pe={teto}",
        "teto": 4500,
        "o_que": "console PlayStation 5 (PS5) inteiro",
        "lixo": r"^\s*(controle|manete|jogo|jogos|cabo|fonte|ssd|leitor|placa|carca[çc]a|cooler|volante|"
                r"headset|fone|pulse|suporte|base|dock|case|capa|dualsense|carregador|tampa|faceplate|skin|"
                r"adesivo)",
        "triagem_extra": "Descarte PS4, PS3, Xbox, Switch, PS5 só em foto/caixa, jogos/controles/acessórios avulsos.",
        "json": CONSOLE_JSON,
        "contexto": "Para PS5 o que importa para destravar é a VERSÃO DO FIRMWARE: quanto mais baixa, melhor. "
                    "Anote exatamente a versão dita (ex.: 4.03, 7.61, 10.01) ou que aparece nas fotos.",
        "grupo": lambda v: v.get("versao") or "?",
    },
}


def arq(perfil, nome):
    return o.BASE / "estado" / f"pm_{perfil}_{nome}.json"


def fase_lista(perfil):
    P = PERFIS[perfil]
    base = P["url"].format(teto=P["teto"])
    todos, vistos, ps = [], set(), 0
    while True:
        novos = 0
        ads = []
        for pg in range(1, 101):
            url = base + (f"&ps={ps}" if ps else "") + (f"&o={pg}" if pg > 1 else "")
            try:
                ads = o.baixar_anuncios(url)
            except Exception as e:
                print("erro", pg, e, flush=True)
                continue
            for a in ads:
                if a["listId"] in vistos:
                    continue
                vistos.add(a["listId"])
                novos += 1
                todos.append({"listId": a["listId"], "url": a["url"], "titulo": a.get("subject"), "preco": o.preco(a),
                              "priceValue": a.get("priceValue"), "local": a.get("location"),
                              "entrega": (a.get("olxDelivery") or {}).get("enabled"),
                              "props": {p["label"]: p["value"] for p in a.get("properties") or []}})
            if pg % 10 == 0:
                print(f"pág {pg}: {len(todos)} anúncios, último R$ {todos[-1]['preco']}", flush=True)
            if len(ads) < 40:
                break
            time.sleep(1.5)
        ult = max([(x["preco"] or 0) for x in todos] + [0])
        if len(ads) < 40 or ult >= P["teto"] or novos == 0:
            break
        ps = ult
    o.gravar(arq(perfil, "lista"), todos)
    print("total", len(todos), flush=True)


TRIAGEM = """Títulos de anúncios da OLX (id | preço | título). Procuro: {o_que}.
Marque só os que vendem esse produto INTEIRO (pode ser usado, com defeito leve, com ou sem acessórios).
Descarte: peça/acessório/jogo avulso, caixa vazia, outro produto, aluguel, serviço, troca, "procuro". {extra}
{lista}
Responda SÓ um JSON: {{"manter": [ids]}}"""

JULGA = """Analise este anúncio usado da OLX. Procuro: {o_que}. Só serve se FUNCIONAR.
{contexto}
O filtro/características foi preenchido pelo vendedor e pode estar errado: vale o que a descrição e o título dizem.
Título: {titulo}
Preço: {preco}
Características (filtro): {props}
Descrição:
\"\"\"{desc}\"\"\"
Responda SÓ um JSON:
{{{json}}}"""


def _julgar(P, item):
    try:
        time.sleep(1.5)
        det = o.detalhe(item["url"])
    except Exception as e:
        return {"erro": str(e)[:100]}
    if not det["entrega"]:
        return {"sem_entrega": True}
    props = "; ".join(f"{k}: {v}" for k, v in det["props"].items() if k and v)
    p = JULGA.format(o_que=P["o_que"], contexto=P.get("contexto", ""), titulo=item["titulo"], preco=item["priceValue"],
                     props=props, desc=det["descricao"][:3500], json=P["json"])
    for _ in range(3):
        try:
            v = o.ia(p, max_tokens=1500)
            if "funciona" in v:
                v["fotos"] = det["fotos"][:8]
                return v
        except Exception:
            time.sleep(4)
    return {"erro": "IA"}


def eh_item(v):
    return bool(v.get("e_o_console", v.get("e_o_produto")) and v.get("funciona") in ("sim", "incerto"))


def fase_abrir(perfil, max_abrir=1500):
    P = PERFIS[perfil]
    todos = o.ler(arq(perfil, "lista"), [])
    julg = o.ler(arq(perfil, "julgados"), {})
    lixo = re.compile(LIXO_COMUM + "|" + P.get("lixo", r"$^"), re.I)
    cand = [x for x in todos if x["preco"] and x["preco"] >= 30 and not lixo.search(x["titulo"] or "")
            and x.get("entrega") is not False]
    tri = julg.setdefault("_triagem", {})
    falta = [x for x in cand if str(x["listId"]) not in tri]
    for i in range(0, len(falta), 60):
        lote = falta[i:i + 60]
        lista = "\n".join(f"{x['listId']} | {x['priceValue']} | {x['titulo']}" for x in lote)
        manter = None
        for _ in range(2):
            try:
                manter = {str(k) for k in o.ia(TRIAGEM.format(o_que=P["o_que"], extra=P.get("triagem_extra", ""),
                                                              lista=lista), max_tokens=4000).get("manter", [])}
                break
            except Exception as e:
                print("triagem falhou", e, flush=True)
        if manter is None:
            manter = {str(x["listId"]) for x in lote}
        for x in lote:
            tri[str(x["listId"])] = str(x["listId"]) in manter
        o.gravar(arq(perfil, "julgados"), julg)
        print(f"triagem {min(i + 60, len(falta))}/{len(falta)}", flush=True)
    cand = sorted([x for x in cand if tri.get(str(x["listId"]))], key=lambda x: x["preco"])
    fila = [x for x in cand if str(x["listId"]) not in julg]
    print(f"{len(todos)} na lista -> {len(cand)} pelo título; faltam abrir {len(fila)}", flush=True)
    abertos = sum(1 for k in julg if not k.startswith("_"))
    with ThreadPoolExecutor(3) as ex:
        for i in range(0, len(fila), 9):
            if abertos >= max_abrir:
                break
            lote = fila[i:i + 9]
            for item, v in zip(lote, ex.map(lambda it: _julgar(P, it), lote)):
                v.update({"titulo": item["titulo"], "preco": item["preco"], "url": item["url"], "local": item["local"]})
                julg[str(item["listId"])] = v
            abertos += len(lote)
            o.gravar(arq(perfil, "julgados"), julg)
            bons = sum(1 for k, v in julg.items() if not k.startswith("_") and isinstance(v, dict) and eh_item(v))
            print(f"abertos {abertos} | R$ {lote[-1]['preco']} | bons {bons}", flush=True)


VERIF = """Fotos e descrição de um anúncio da OLX de: {o_que}. Preço do anúncio: {preco}. Título: {titulo}
Descrição: \"\"\"{desc}\"\"\"
{contexto}
Olhe TODAS as fotos (tela de Informações do sistema / versão do software, console ligado, controles, cabos, defeitos).
Responda SÓ um JSON:
{{"preco_real": número (preço deste item pela descrição),
 "firmware_fotos": "versão do sistema que aparece em alguma foto ou null",
 "modelo_fotos": "modelo/etiqueta que aparece (ex.: CECH-2501A, CFI-1014A) ou null",
 "aparece_ligado": true/false/null, "controles_na_foto": número ou null,
 "fotos_de_outra_coisa": true/false, "obs": "contradições entre fotos e texto, ou vazio"}}"""


def fase_verificar(perfil, n=60):
    P = PERFIS[perfil]
    julg = o.ler(arq(perfil, "julgados"), {})
    itens = [(k, v) for k, v in julg.items() if not k.startswith("_") and isinstance(v, dict) and eh_item(v)
             and "verif" not in v and v.get("funciona") == "sim"]
    alvo = sorted(itens, key=lambda kv: kv[1]["preco"])[:n]
    print("verificando", len(alvo), flush=True)

    def um(kv):
        v = kv[1]
        try:
            det = o.detalhe(v["url"])
            return o.ler_fotos(det["fotos"], VERIF.format(o_que=P["o_que"], preco=v["preco"], titulo=v["titulo"],
                                                          desc=det["descricao"][:3000],
                                                          contexto=P.get("contexto", "")), max_fotos=8) or {"erro": "IA"}
        except Exception as e:
            return {"erro": str(e)[:80]}
    with ThreadPoolExecutor(3) as ex:
        for (k, v), r in zip(alvo, ex.map(um, alvo)):
            v["verif"] = r
            print(k, v["preco"], (v["titulo"] or "")[:40], "->", json.dumps(r, ensure_ascii=False)[:160], flush=True)
            o.gravar(arq(perfil, "julgados"), julg)


def itens_finais(perfil):
    julg = o.ler(arq(perfil, "julgados"), {})
    P = PERFIS[perfil]
    out = []
    for k, v in julg.items():
        if k.startswith("_") or not isinstance(v, dict) or not eh_item(v):
            continue
        vf = v.get("verif") or {}
        pr = vf.get("preco_real") or v.get("preco_real")
        v["preco_anuncio"] = v["preco"]
        if isinstance(pr, (int, float)) and pr > 0:
            v["preco"] = pr
        if v["preco"] > P["teto"]:
            continue
        if vf.get("firmware_fotos") and not v.get("firmware"):
            v["firmware"], v["firmware_fonte"] = vf["firmware_fotos"], "foto"
        v["grupo"] = P["grupo"](v)
        out.append(v)
    return out


if __name__ == "__main__":
    perfil, fase = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else None
    if fase == "lista":
        fase_lista(perfil)
    elif fase == "abrir":
        fase_abrir(perfil, n or 1500)
    elif fase == "verificar":
        fase_verificar(perfil, n or 60)
    elif fase == "itens":
        print(json.dumps(itens_finais(perfil), ensure_ascii=False, indent=1))
