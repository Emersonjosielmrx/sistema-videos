# -*- coding: utf-8 -*-
"""Pesquisa única (04/11/2026): notebooks mais baratos POR FAIXA DE RAM (1/2/4/8/16 GB) que funcionam e têm carregador.
Regras da dona: só com entrega; RAM só vale o que a DESCRIÇÃO diz (o filtro/título é só pista); tem que funcionar;
anúncio que diz "sem carregador" = descarta; carregador não informado = fica, marcado "perguntar"; tela quebrada OK.
Não manda Telegram nem mensagem a vendedor. Gera estado/pesquisa_notebooks.json e pesquisa/RESULTADO_NOTEBOOKS.md.

  python pesquisa_notebooks.py lista     -> fase 1: varre a listagem (só páginas de lista)
  python pesquisa_notebooks.py abrir     -> fase 2: abre e julga os candidatos (retomável)
  python pesquisa_notebooks.py relatorio -> fase 3: monta o ranking
"""
import json, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import olx_buscas as o

BASE_URL = "https://www.olx.com.br/informatica/notebooks?opst=2&sp=1&pe={teto}"
TETO = 1000
LISTA = o.BASE / "estado" / "pesq_lista.json"
JULG = o.BASE / "estado" / "pesq_julgados.json"
SAIDA = o.BASE / "pesquisa"
FAIXAS = [1, 2, 4, 8, 16]
POR_FAIXA = 8          # para de abrir pistas de uma faixa quando já tem tantos bons nela
MAX_ABRIR = int(sys.argv[2]) if len(sys.argv) > 2 else 700

LIXO = re.compile(r"^\s*(tela|teclado|carca[çc]a|tampa|bateria|fonte|carregador|placa|cooler|dobradi|cabo|flat|"
                  r"mem[óo]ria|hd\b|ssd|caixa|capa|mochila|bolsa|suporte|base|moldura|touch ?pad|alto.?falante|"
                  r"webcam|pe[çc]as?\b|kit\b|lote\b|conector|jack|bot[ãa]o|processador|ventoinha|dissipador)"
                  r"|retirada de pe[çc]|retirar pe[çc]|p/ ?pe[çc]as|para pe[çc]as|pra pe[çc]as|para reparo|"
                  r"n[ãa]o liga|sucata|somente pe[çc]as|"
                  r"aluguel|conserto de|assist[êe]ncia|formata[çc][ãa]o|troco\b|procuro|compro\b", re.I)


def faixa(gb):
    if not gb:
        return None
    gb = float(gb)
    for f in reversed(FAIXAS):
        if gb >= f:
            return f
    return 1


def pista_ram(a):
    for p in a.get("properties") or []:
        if p.get("label") == "Memória RAM":
            m = re.search(r"(\d+)", p.get("value") or "")
            if m:
                return int(m.group(1))
    m = re.search(r"(\d{1,2})\s?gb\s*(de\s*)?(ram|mem)", a.get("subject") or "", re.I)
    return int(m.group(1)) if m else None


def fase_lista():
    todos, ps, vistos = [], 0, set()
    while True:
        novos_bloco = 0
        for pg in range(1, 101):
            url = BASE_URL.format(teto=TETO) + (f"&ps={ps}" if ps else "") + (f"&o={pg}" if pg > 1 else "")
            try:
                ads = o.baixar_anuncios(url)
            except Exception as e:
                print("erro", pg, e, flush=True)
                time.sleep(20)
                continue
            for a in ads:
                if a["listId"] in vistos:
                    continue
                vistos.add(a["listId"])
                novos_bloco += 1
                todos.append({"listId": a["listId"], "url": a["url"], "titulo": a.get("subject"), "preco": o.preco(a),
                              "priceValue": a.get("priceValue"), "local": a.get("location"),
                              "entrega": (a.get("olxDelivery") or {}).get("enabled"),
                              "props": {p["label"]: p["value"] for p in a.get("properties") or []},
                              "pista_ram": pista_ram(a)})
            if pg % 10 == 0:
                print(f"pág {pg} (ps={ps}): {len(todos)} anúncios, último R$ {todos[-1]['preco']}", flush=True)
            if len(ads) < 40:
                break
            time.sleep(1.5)
        ult = max((x["preco"] or 0) for x in todos)
        if len(ads) < 40 or ult >= TETO or novos_bloco == 0:
            break
        ps = ult  # passou das 100 páginas: recomeça a partir do último preço
    o.gravar(LISTA, todos)
    print("total", len(todos), flush=True)


TRIAGEM_NB = """Abaixo, títulos de anúncios da categoria Notebooks na OLX (id | preço | título).
Marque os que vendem UM NOTEBOOK/NETBOOK/MACBOOK INTEIRO (pode ser usado, velho, com tela quebrada).
Descarte: peça avulsa, carcaça, tela, teclado, bateria, fonte, caixa, acessório, tablet, celular, PC de mesa, aluguel,
serviço, troca, "não liga", "para peças", "sucata", lote de peças.
{lista}
Responda SÓ um JSON: {{"manter": [ids]}}"""

JULGA_NB = """Analise este anúncio de NOTEBOOK usado na OLX. A compradora quer notebooks baratos que FUNCIONEM para rodar
tarefas de vídeo (ffmpeg, scripts). Tela quebrada/riscada, bateria viciada, teclado com tecla falhando são aceitáveis
SE o notebook liga e funciona (pode usar monitor/teclado externo). A RAM e o processador valem pelo que a DESCRIÇÃO e o
título dizem; as "características" do filtro foram preenchidas pelo vendedor e às vezes estão erradas (use só se o texto
não falar nada, e diga a fonte).

Título: {titulo}
Preço: {preco}
Características (filtro): {props}
Descrição:
\"\"\"{desc}\"\"\"

Responda SÓ um JSON:
{{"e_notebook": true/false (false se peça/acessório/outro aparelho),
 "funciona": "sim" | "nao" | "incerto",
 "ram_gb": número ou null, "ram_fonte": "descricao" | "titulo" | "filtro" | "nenhuma",
 "cpu": "modelo do processador como dito (ex.: Core i5-3210M, Celeron N4020, Core 2 Duo T6600) ou null",
 "cpu_fonte": "descricao" | "titulo" | "filtro" | "nenhuma",
 "cpu_nota": 0-10 (desempenho p/ vídeo: Atom/Celeron antigo/Core2=1-2, Celeron N4xxx/Pentium=2-3, i3 1ª-3ª=3,
             i5 1ª-3ª=4, i5/i7 4ª-7ª=5-6, i5/i7 8ª+ ou Ryzen 5/7=7-9, Apple M1+=8; null se desconhecido),
 "armazenamento": "ex.: SSD 240GB / HD 500GB / sem HD / null",
 "carregador": "sim" | "nao" | "nao_informado",
 "tela": "ok" | "quebrada/manchada" | "nao_informado",
 "defeitos": "defeitos declarados ou vazio",
 "resumo": "1 frase com o que importa citando o vendedor"}}"""


def julgar_nb(item):
    try:
        time.sleep(1.5)
        det = o.detalhe(item["url"])
    except Exception as e:
        return item["listId"], {"erro": str(e)[:100]}
    if not det["entrega"]:
        return item["listId"], {"sem_entrega": True}
    props = "; ".join(f"{k}: {v}" for k, v in det["props"].items() if k and v)
    p = JULGA_NB.format(titulo=item["titulo"], preco=item["priceValue"], props=props, desc=det["descricao"][:3500])
    for _ in range(3):
        try:
            v = o.ia(p)
            if "funciona" in v:
                v["fotos"] = det["fotos"][:1]
                return item["listId"], v
        except Exception as e:
            time.sleep(4)
    return item["listId"], {"erro": "IA"}


def bom(v):
    """Promissor: notebook inteiro, não diz que não funciona, não diz que vem sem carregador."""
    return bool(v.get("e_notebook") and v.get("funciona") in ("sim", "incerto") and v.get("carregador") != "nao")


def confirmado(v):
    """O próprio anúncio diz que funciona e diz a RAM no texto (não só no filtro)."""
    return bool(bom(v) and v.get("funciona") == "sim" and v.get("ram_fonte") in ("descricao", "titulo", "fotos")
                and v.get("ram_gb"))


FORTE = re.compile(r"\b(i5|i7|i9|ryzen|8 ?gb|12 ?gb|16 ?gb|32 ?gb|ssd|macbook|thinkpad|latitude|elitebook|vostro|"
                   r"probook|gamer|nitro|ideapad 3|aspire 5)\b", re.I)


def fase_abrir():
    todos = o.ler(LISTA, [])
    julg = o.ler(JULG, {})
    # corte local + triagem por título (em lotes)
    cand = [x for x in todos if x["preco"] and x["preco"] >= 40 and not LIXO.search(x["titulo"] or "")
            and x.get("entrega") is not False]
    triados = julg.setdefault("_triagem", {})
    falta = [x for x in cand if str(x["listId"]) not in triados]
    for i in range(0, len(falta), 60):
        lote = falta[i:i + 60]
        lista = "\n".join(f"{x['listId']} | {x['priceValue']} | {x['titulo']}" for x in lote)
        try:
            manter = {str(k) for k in o.ia(TRIAGEM_NB.format(lista=lista), max_tokens=4000).get("manter", [])}
        except Exception as e:
            print("triagem falhou, mantém lote", e, flush=True)
            manter = {str(x["listId"]) for x in lote}
        for x in lote:
            triados[str(x["listId"])] = str(x["listId"]) in manter
        o.gravar(JULG, julg)
        print(f"triagem {min(i + 60, len(falta))}/{len(falta)}", flush=True)
    cand = [x for x in cand if triados.get(str(x["listId"]))]
    cand.sort(key=lambda x: x["preco"])
    print(f"{len(todos)} na lista -> {len(cand)} notebooks inteiros pelo título", flush=True)

    def bons_por_faixa():
        c = {f: 0 for f in FAIXAS}
        for k, v in julg.items():
            if k.startswith("_") or not isinstance(v, dict) or not confirmado(v):
                continue
            f = faixa(v.get("ram_gb"))
            if f:
                c[f] += 1
        return c

    abertos = sum(1 for k in julg if not k.startswith("_"))
    fila = []
    for x in cand:
        if str(x["listId"]) in julg:
            continue
        fila.append(x)
    i = 0
    with ThreadPoolExecutor(3) as ex:
        while i < len(fila) and abertos < MAX_ABRIR:
            c = bons_por_faixa()
            lote = []
            while i < len(fila) and len(lote) < 9:
                x = fila[i]; i += 1
                f = faixa(x.get("pista_ram"))
                if f and c.get(f, 0) >= POR_FAIXA:
                    continue  # faixa da pista já cheia de achados mais baratos
                baixas_cheias = all(c[k] >= POR_FAIXA for k in (1, 2, 4))
                if baixas_cheias and not ((f and f >= 8) or FORTE.search(x["titulo"] or "")):
                    continue  # já temos os fracos; agora só vale abrir o que tem pista de 8GB+/CPU boa
                lote.append(x)
            for lid, v in ex.map(julgar_nb, lote):
                item = next(x for x in lote if x["listId"] == lid)
                v.update({"titulo": item["titulo"], "preco": item["preco"], "url": item["url"], "local": item["local"],
                          "pista_ram": item.get("pista_ram")})
                julg[str(lid)] = v
            abertos += len(lote)
            o.gravar(JULG, julg)
            print(f"abertos {abertos} | R$ {lote[-1]['preco'] if lote else '-'} | bons por faixa {bons_por_faixa()}",
                  flush=True)
            if all(n >= POR_FAIXA for n in bons_por_faixa().values()):
                break


VERIF = """Anúncio de NOTEBOOK usado na OLX. Preço do anúncio: {preco}. Título: {titulo}
Descrição: \"\"\"{desc}\"\"\"
Olhe também as FOTOS. Responda SÓ um JSON:
{{"preco_real": número (preço DESTE notebook segundo a descrição; difere quando o anúncio tem vários itens, preço simbólico,
               "sinal", "a partir de"),
 "ram_gb_fotos": número ou null (se aparecer em tela de sistema/BIOS/etiqueta), "cpu_fotos": "texto ou null",
 "aparece_ligado": true/false/null, "aparece_carregador": true/false/null,
 "fotos_de_outra_coisa": true/false, "tela_quebrada_na_foto": true/false/null,
 "obs": "contradições entre fotos e texto, ou vazio"}}"""


def verificar_um(v):
    try:
        det = o.detalhe(v["url"])
    except Exception as e:
        return {"erro_verif": str(e)[:80]}
    r = o.ler_fotos(det["fotos"], VERIF.format(preco=v["preco"], titulo=v["titulo"], desc=det["descricao"][:3000]),
                    max_fotos=6)
    return r or {"erro_verif": "IA"}


def fase_verificar():
    """Fotos + preço real nos 60 melhores (confirmados e promissores)."""
    julg = o.ler(JULG, {})
    itens = [(k, v) for k, v in julg.items() if not k.startswith("_") and isinstance(v, dict) and bom(v)
             and v.get("funciona") == "sim" and "verif" not in v]
    for k, v in itens:
        v["_cb"] = pontos(v) / max(v["preco"], 1)
    alvo = sorted(itens, key=lambda kv: -kv[1]["_cb"])[:60]
    # e os 5 mais baratos de cada faixa, para o quadro por faixa não ter isca
    for f in FAIXAS:
        alvo += sorted([kv for kv in itens if faixa(kv[1].get("ram_gb")) == f], key=lambda kv: kv[1]["preco"])[:6]
    vistos = set()
    alvo = [kv for kv in alvo if not (kv[0] in vistos or vistos.add(kv[0]))]
    print("verificando", len(alvo), flush=True)
    with ThreadPoolExecutor(3) as ex:
        for (k, v), r in zip(alvo, ex.map(lambda kv: verificar_um(kv[1]), alvo)):
            v.pop("_cb", None)
            v["verif"] = r
            print(k, v["preco"], (v["titulo"] or "")[:40], "->", json.dumps(r, ensure_ascii=False)[:200], flush=True)
            o.gravar(JULG, julg)


def preco_efetivo(v):
    pr = (v.get("verif") or {}).get("preco_real")
    return pr if isinstance(pr, (int, float)) and pr > 0 else v["preco"]


def pontos(v):
    """Nota de utilidade p/ vídeo: processador pesa mais, RAM soma, SSD ajuda."""
    cpu = v.get("cpu_nota") if isinstance(v.get("cpu_nota"), (int, float)) else 2
    ram = float(v.get("ram_gb") or 2)
    ssd = 1 if "ssd" in str(v.get("armazenamento") or "").lower() else 0
    return cpu * 1.0 + min(ram, 16) ** 0.5 * 1.5 + ssd


def fase_relatorio():
    julg = o.ler(JULG, {})
    itens = [v for k, v in julg.items() if not k.startswith("_") and isinstance(v, dict) and bom(v)]
    isca = 0
    for v in itens:
        vf = v.get("verif") or {}
        if vf.get("ram_gb_fotos") and v.get("ram_fonte") not in ("descricao", "titulo"):
            v["ram_gb"], v["ram_fonte"] = vf["ram_gb_fotos"], "fotos"
        if vf.get("aparece_carregador") and v.get("carregador") == "nao_informado":
            v["carregador"] = "foto"
        v["preco_anuncio"] = v["preco"]
        v["preco"] = preco_efetivo(v)
    antes = len(itens)
    itens = [v for v in itens if v["preco"] <= TETO]
    isca = antes - len(itens)
    for v in itens:
        v["faixa"] = faixa(v.get("ram_gb"))
        v["pontos"] = round(pontos(v), 1)
        v["custo_beneficio"] = round(v["pontos"] / max(v["preco"], 1) * 100, 2)
        v["confianca"] = ("alta" if v.get("funciona") == "sim" and v.get("carregador") == "sim"
                          and v.get("ram_fonte") in ("descricao", "titulo") else "perguntar")
    SAIDA.mkdir(exist_ok=True)
    o.gravar(SAIDA / "pesquisa_notebooks.json", itens)
    abertos = sum(1 for k in julg if not k.startswith("_"))
    conf = [v for v in itens if confirmado(v)]
    linhas = [f"# Notebooks baratos que funcionam — pesquisa de {time.strftime('%d/%m/%Y %H:%M')}",
              f"Com entrega, Brasil todo, até R$ {TETO}. Anúncios abertos e lidos: {abertos}. "
              f"Confirmados: {len(conf)} (o anúncio diz que funciona e diz a RAM no texto). "
              f"Promissores a perguntar: {len(itens) - len(conf)}.",
              "Descartados: peça/sucata/não liga, ou o anúncio diz que vem SEM carregador. Tela quebrada é aceita.",
              f"Preço isca (anúncio barato, mas o notebook custa mais que R$ {TETO} na descrição): {isca} removidos.",
              "Verificado 📷 = fotos e preço real conferidos pela IA.", ""]

    def lin(v):
        perg = []
        if v.get("carregador") == "nao_informado":
            perg.append("carregador?")
        if v.get("funciona") == "incerto":
            perg.append("funciona?")
        if v.get("ram_fonte") in ("filtro", "nenhuma"):
            perg.append("RAM?")
        vf = v.get("verif") or {}
        marca = " 📷" if vf and "erro_verif" not in vf else ""
        if vf.get("obs"):
            perg.append("obs: " + str(vf["obs"])[:60])
        preco_txt = f"R$ {v['preco']}" + (f" (anúncio R$ {v['preco_anuncio']})" if v["preco"] != v["preco_anuncio"] else "")
        return (f"| {preco_txt}{marca} | {v.get('ram_gb') or '?'} GB ({v.get('ram_fonte')}) | {v.get('cpu') or '?'} "
                f"| {v.get('armazenamento') or '?'} | {v.get('tela')} | {', '.join(perg) or 'ok'} "
                f"| [{(v['titulo'] or '')[:45]}]({v['url']}) |")

    cab = "| Preço | RAM | Processador | Disco | Tela | Perguntar | Anúncio |\n|---|---|---|---|---|---|---|"
    cab_rk = ("| # | Pontos por R$100 | Preço | RAM | Processador | Disco | Tela | Perguntar | Anúncio |\n"
              "|---|---|---|---|---|---|---|---|---|")
    linhas.append("## 1. Menor preço por faixa de RAM (confirmados)")
    for f in reversed(FAIXAS):
        g = sorted([v for v in conf if v["faixa"] == f], key=lambda v: v["preco"])[:5]
        linhas.append(f"\n### {f} GB" + ("" if g else f" — nenhum confirmado até R$ {TETO}"))
        if g:
            linhas += [cab] + [lin(v) for v in g]
    linhas.append("\n## 2. Ranking para VÍDEO (confirmados, processador i5 2ª geração ou melhor), melhor custo-benefício primeiro")
    linhas.append("Pontos = processador (0-10) + RAM + SSD; ranking = pontos por R$ 100. Atom/Celeron/Core2 ficam fora "
                  "(baratos mas não aguentam render).\n")
    linhas.append(cab_rk)
    uteis = [v for v in conf if isinstance(v.get("cpu_nota"), (int, float)) and v["cpu_nota"] >= 4]
    for n, v in enumerate(sorted(uteis, key=lambda v: -v["custo_beneficio"])[:30], 1):
        linhas.append(f"| {n} | {v['custo_beneficio']} " + lin(v))
    prom = [v for v in itens if not confirmado(v) and v.get("funciona") == "sim"]
    linhas.append("\n## 3. Promissores: dizem que funcionam, mas falta confirmar RAM/carregador (perguntar)")
    linhas.append(cab_rk)
    for n, v in enumerate(sorted(prom, key=lambda v: -v["custo_beneficio"])[:20], 1):
        linhas.append(f"| {n} | {v['custo_beneficio']} " + lin(v))
    (SAIDA / "RESULTADO_NOTEBOOKS.md").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))


if __name__ == "__main__":
    {"lista": fase_lista, "abrir": fase_abrir, "verificar": fase_verificar, "relatorio": fase_relatorio}[sys.argv[1]]()
