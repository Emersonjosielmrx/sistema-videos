# -*- coding: utf-8 -*-
"""Buscas automáticas na OLX com aviso no Telegram (regras da dona, 04/11/2026).

Regras fixas:
  1. Só anúncio COM ENTREGA (filtro OLX opst=2), Brasil inteiro.
  2. Ordena do MENOR preço pra cima (sp=1) e para no teto (max) de cada busca: acima disso não vale a pena.
  3. Abre cada anúncio, lê a descrição e a IA (Gemini pelo OmniRoute) diz se funciona, tem defeito ou é sucata/peças,
     se é mesmo o produto (não capa/peça) e se atende os requisitos da busca (carregador, GB etc.).
  Só avisa o que é o produto, funciona e atende os requisitos. Na dúvida ("incerto"), avisa marcado com ⚠️.

Uso:
  pythonw olx_buscas.py                     -> fica rodando (busca a cada X min + comandos do Telegram)
  python  olx_buscas.py uma-vez             -> roda todas uma vez e sai
  python  olx_buscas.py testar "termo" 150 ["requisitos"]  -> mostra o que acharia e o veredito (não avisa)
  python  olx_buscas.py comando "/add ..."  -> mesmo comando do Telegram pelo terminal
"""
import json, os, re, sys, time, html, threading, traceback, urllib.parse
from datetime import datetime
from pathlib import Path

from curl_cffi import requests as cr

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
BUSCAS = BASE / "buscas.json"
VISTOS = BASE / "estado" / "vistos.json"
LOG = BASE / "estado" / "olx.log"
TRAVA = BASE / "estado" / "rodando.pid"
GERAL = Path(r"D:\postador-de-videos\config\telegram.json")  # reserva: só avisa, sem comandos
OMNI = Path(r"D:\recapd-ambientes\producao\secrets\omniroute.json")
trava_arq = threading.Lock()
trava_busca = threading.Lock()


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    linha = f"{datetime.now():%d/%m %H:%M:%S} {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    try:
        print(linha, flush=True)
    except Exception:
        pass


def ler(p, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return padrao


def gravar(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def cfg():
    c = ler(CONFIG, {})
    c.setdefault("intervalo_min", 5)
    c.setdefault("pausa_entre_buscas_s", 8)
    c.setdefault("pausa_entre_anuncios_s", 2)
    c.setdefault("max_paginas", 5)
    c.setdefault("avisar_incerto", True)
    c.setdefault("modelo_ia", "gemini-fila")
    return c


# ---------------- Telegram ----------------
def bot():
    c = cfg()
    if c.get("bot_token") and c.get("chat_id"):
        return c["bot_token"], str(c["chat_id"]), True
    g = ler(GERAL, {})
    return g.get("bot_token"), str(g.get("chat_id", "")), False


def tg(metodo, dados, timeout=40):
    token, _, _ = bot()
    if not token:
        log("sem bot do Telegram configurado")
        return None
    try:
        j = cr.post(f"https://api.telegram.org/bot{token}/{metodo}", data=dados, timeout=timeout).json()
        if not j.get("ok"):
            log(f"telegram {metodo} erro: {str(j)[:200]}")
        return j
    except Exception as e:
        log(f"telegram {metodo} falhou: {e}")
        return None


def mandar(texto, foto=None):
    _, chat, _ = bot()
    """Devolve o message_id (0 se falhou)."""
    if foto and len(texto) <= 1020:
        j = tg("sendPhoto", {"chat_id": chat, "photo": foto, "caption": texto, "parse_mode": "HTML"})
        if j and j.get("ok"):
            return j["result"]["message_id"]
    j = tg("sendMessage", {"chat_id": chat, "text": texto[:4000], "parse_mode": "HTML",
                           "disable_web_page_preview": "false" if foto else "true"})
    if not (j and j.get("ok")):  # HTML quebrado? manda cru
        j = tg("sendMessage", {"chat_id": chat, "text": re.sub(r"<[^>]+>", "", texto)[:4000]})
    return j["result"]["message_id"] if j and j.get("ok") else 0


AVISOS = BASE / "estado" / "avisos.json"


def registrar_aviso(msg_id, b, a, v):
    with trava_arq:
        d = ler(AVISOS, {})
        d[str(msg_id)] = {"busca": b["id"], "nome": b["nome"], "listId": a["listId"], "titulo": a.get("subject"),
                          "preco": a.get("priceValue"), "url": a.get("url"), "estado": v.get("estado"),
                          "resumo": v.get("resumo"), "itens": v.get("itens"), "alerta": v.get("alerta"),
                          "duvidas": v.get("duvidas"), "quando": datetime.now().strftime("%d/%m %H:%M")}
        if len(d) > 500:
            for k in list(d)[:len(d) - 500]:
                d.pop(k)
        gravar(AVISOS, d)


# ---------------- OLX ----------------
def montar_url(b, pagina=1):
    if b.get("url"):
        u = b["url"]
    else:
        u = f"https://www.olx.com.br/brasil?q={urllib.parse.quote(b['termo'])}"
    p = urllib.parse.urlsplit(u)
    q = dict(urllib.parse.parse_qsl(p.query))
    for k in ("sf", "sp", "o"):
        q.pop(k, None)
    q["opst"] = "2"   # regra 1: só com Entrega
    q["sp"] = "1"     # regra 2: menor preço primeiro
    q["pe"] = str(int(b["max"]))
    if b.get("min"):
        q["ps"] = str(int(b["min"]))
    if pagina > 1:
        q["o"] = str(pagina)
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q), ""))


def _get(url):
    for tentativa in range(3):  # 502/503 da OLX acontecem de vez em quando (visto na pesquisa de 04/11)
        r = cr.get(url, impersonate="chrome", timeout=40, headers={"Accept-Language": "pt-BR,pt;q=0.9"})
        if r.status_code == 200:
            return r.text
        if r.status_code < 500:
            break
        time.sleep(10 * (tentativa + 1))
    raise RuntimeError(f"OLX respondeu {r.status_code}")


def ler_fotos(fotos, pergunta, max_fotos=6):
    """Gemini olhando as fotos do anúncio (tela de 'Sobre o sistema', BIOS, etiqueta, tela quebrada...)."""
    import base64
    cont = [{"type": "text", "text": pergunta}]
    for f in fotos[:max_fotos]:
        try:
            b = cr.get(f, timeout=30).content
            cont.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}})
        except Exception:
            pass
    if len(cont) == 1:
        return None
    j = ler(OMNI, {})
    r = cr.post(j["base_url"].rstrip("/") + "/v1/chat/completions", timeout=180,
                headers={"Authorization": "Bearer " + j["api_key"]},
                json={"model": cfg()["modelo_ia"], "temperature": 0.1, "max_tokens": 1200,
                      "messages": [{"role": "user", "content": cont}]})
    txt = r.json()["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0)) if m else None


FOTOS_PROMPT = """Fotos de um anúncio da OLX de: {termo}. A compradora quer saber: {duvidas}
Olhe TODAS as fotos (tela de configuração do sistema, BIOS, etiqueta, caixa, o aparelho ligado, tela quebrada, carregador
na foto). Responda SÓ um JSON:
{{"respostas": "o que as fotos mostram sobre cada dúvida (ou 'não aparece')",
 "aparece_carregador": true/false/null, "aparece_ligado": true/false/null,
 "fotos_de_outra_coisa": true/false (fotos de outros produtos = anúncio de vários itens),
 "alerta": "algo que contradiga o anúncio ou vazio"}}"""


def baixar_anuncios(url):
    t = _get(url)
    pedacos = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)</script>', t, re.S)
    s = "".join(json.loads(c) for c in pedacos)
    ads, dec, i = [], json.JSONDecoder(), 0
    while True:
        i = s.find('{"ads":[', i)
        if i < 0:
            break
        try:
            d, fim = dec.raw_decode(s, i)
            ads += d.get("ads") or []
            i = fim
        except Exception:
            i += 8
    if not ads and "listId" not in s and "totalOfAds" not in s:
        raise RuntimeError("página sem anúncios (OLX mudou o formato ou bloqueou?)")
    vistos, saida = set(), []
    for a in ads:
        if a.get("listId") and a["listId"] not in vistos:
            vistos.add(a["listId"])
            saida.append(a)
    return saida


def detalhe(url):
    """Abre o anúncio: descrição completa, características e dados de entrega."""
    t = _get(url)
    m = re.search(r'<script id="initial-data"[^>]*data-json="([^"]*)"', t)
    if not m:
        raise RuntimeError("anúncio sem initial-data")
    ad = json.loads(html.unescape(m.group(1)))["ad"]
    corpo = re.sub(r"<br\s*/?>", "\n", ad.get("body") or "")
    corpo = html.unescape(re.sub(r"<[^>]+>", "", corpo)).strip()
    props = {p.get("label"): p.get("value") or ", ".join(p.get("values") or []) for p in ad.get("properties") or []}
    dl = ad.get("olxDelivery") or {}
    d = {"descricao": corpo, "props": props,
         "entrega": bool(dl.get("enabled")),
         "frete_gratis_anunciado": bool(dl.get("isSellerPayingForShip")),
         "vendedor": (ad.get("user") or {}).get("name"),
         "fotos": [i.get("original") for i in ad.get("images") or [] if i.get("original")]}
    if d["entrega"]:
        d["frete"] = frete(ad["listId"], ad.get("searchCategoryLevelZero"), ad.get("searchCategoryLevelOne"),
                           ad.get("searchCategoryLevelTwo"), dl.get("weight") or 1)
    return d


def frete(list_id, cat0, cat1, cat2, peso):
    """Frete REAL até o CEP da dona (API da própria OLX, a mesma do 'Calcule o frete' do anúncio).
    A dona (04/11): todo anúncio tem frete — até o 'frete grátis' sai pago no Norte; comparar sempre pelo TOTAL.
    Devolve o mais barato entre as opções de envio (ignora 'Retirar'), ou None se a OLX não cotou."""
    cep = cfg().get("cep", "68625016")
    try:
        r = cr.post("https://apigw.olx.com.br/delivery/quote", impersonate="chrome", timeout=30,
                    headers={"Origin": "https://www.olx.com.br", "Referer": "https://www.olx.com.br/"},
                    json={"zipCode": cep, "listId": int(list_id), "searchCategoryLevelZero": cat0,
                          "searchCategoryLevelOne": cat1, "searchCategoryLevelTwo": cat2, "weight": peso})
        ops = [op for op in r.json().get("deliveryOptions") or [] if op.get("type") != "IN_HANDS"]
        precos = [op["price"]["raw"] for op in ops if isinstance((op.get("price") or {}).get("raw"), (int, float))]
        return min(precos) if precos else None
    except Exception as e:
        log(f"frete {list_id} falhou: {str(e)[:80]}")
        return None


def total(preco_item, det):
    """Preço do item + frete real (se a OLX não cotou, soma uma estimativa conservadora)."""
    f = det.get("frete") if det else None
    return (preco_item or 0) + (f if isinstance(f, (int, float)) else cfg().get("frete_estimado", 50))


def preco(a):
    v = re.sub(r"[^\d]", "", (a.get("priceValue") or a.get("price") or "").split(",")[0])
    return int(v) if v else None


def filtro_rapido(a, b):
    tit = (a.get("subject") or "").lower()
    for w in b.get("sem") or []:
        if w.strip() and w.strip().lower() in tit:
            return False
    p = preco(a)
    if p is None or p > int(b["max"]):
        return False
    if b.get("min") and p < int(b["min"]):
        return False
    if not (a.get("olxDelivery") or {}).get("enabled", True):
        return False
    return True


# ---------------- IA ----------------
PROMPT = """Você analisa anúncios de produtos USADOS da OLX para uma compradora que quer o mais barato que FUNCIONE.
Produto procurado: {termo}
Regras DESTA busca (valem acima do padrão; podem endurecer ou afrouxar, ex.: aceitar tela quebrada se funcionar):
{req}
Padrão quando nenhuma regra fala do assunto: tem que ser o produto e funcionar; defeito ou sucata = não aprovar.

Anúncio:
Título: {titulo}
Preço: {preco}
Características: {props}
Descrição do vendedor:
\"\"\"{desc}\"\"\"

Responda SÓ um JSON:
{{"e_o_produto": true/false (false se for capa, peça avulsa, caixa, acessório, outro modelo, troca, "procuro"),
 "estado": "funciona" | "defeito" | "sucata" | "incerto",
 "atende_requisitos": true/false/null (null se o anúncio não diz),
 "itens": "o que vem junto e dados pedidos nos requisitos (ex.: carregador sim, 128GB, bateria 85%)",
 "resumo": "1 frase curta com o que importa, citando o vendedor quando ajuda (ex.: 'diz: tudo funcionando, só marcas de uso')",
 "alerta": "pegadinhas: tela trincada, conta bloqueada (iCloud/Google), sem teste, só liga, bateria ruim, etc. ou vazio",
 "preco_real": número ou null (preço DESTE produto segundo a descrição; difere do preço do anúncio quando o anúncio
               tem vários itens, preço simbólico/"sinal"/"a partir de", ou "valor real R$ X"; null se igual),
 "aprovar": true/false (seguindo as regras desta busca e o padrão; "incerto" sem regra contra = true),
 "motivo": "por que aprovou/reprovou, citando a regra quando for o caso",
 "duvidas": "o que perguntar ao vendedor (o que as regras pedem e o anúncio não diz) ou vazio"}}
Regras: "defeito" = qualquer problema declarado (não liga, tela quebrada, placa, bloqueado, falha). "sucata" = peças/retirada
de peças/não funciona/no estado. "funciona" só se o anúncio diz ou deixa claro que funciona. Condição "Com defeito ou avarias"
nas características = defeito. Sem informação suficiente = "incerto"."""


def ia(prompt, max_tokens=800):
    """Texto -> JSON. Ordem pedida pela dona (04/11): Sonnet 5.5 web (rende melhor) -> Argon (reserva; cota pequena)
    -> Gemini Flash (nunca deixa parar). Imagem NÃO passa aqui: ler_fotos usa o Gemini, que enxerga."""
    j = ler(OMNI, {})
    erro = None
    for modelo in cfg().get("modelos_texto", ["sonnet-fila", "gemini/gemini-4-argon", "gemini-fila"]):
        try:
            r = cr.post(j["base_url"].rstrip("/") + "/v1/chat/completions", timeout=120,
                        headers={"Authorization": "Bearer " + j["api_key"]},
                        json={"model": modelo, "temperature": 0.1, "max_tokens": max_tokens,
                              "messages": [{"role": "user", "content": prompt}]})
            txt = r.json()["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", txt, re.S)
            return json.loads(m.group(0))
        except Exception as e:
            erro = e
            log(f"ia {modelo} falhou: {str(e)[:120]}")
    raise RuntimeError(f"todas as IAs falharam: {erro}")


TRIAGEM = """Produto procurado na OLX: {termo}
Regras da busca: {req}
Abaixo, títulos de anúncios (id | preço | título). Marque só os que vendem O APARELHO/PRODUTO PRINCIPAL procurado
(mesmo usado, com defeito ou incompleto). Descarte: jogo/mídia, controle/manete avulso, capa, película, caixa vazia,
cabo, carregador, fonte, peça avulsa, camisa/brinde, outro modelo/geração claramente diferente, aluguel, serviço,
conserto, troca ("troco", "procuro"). Título vago ("vendo", "videogame", "celular") = mantenha.
{lista}
Responda SÓ um JSON: {{"manter": [ids]}}"""


def triagem(ads, b):
    """Corte barato pelos títulos (1 chamada para a página toda). Falhou = mantém todos."""
    if not ads:
        return set()
    lista = "\n".join(f"{a['listId']} | {a.get('priceValue')} | {a.get('subject')}" for a in ads)
    for tentativa in range(2):
        try:
            r = ia(TRIAGEM.format(termo=b.get("termo") or b["nome"], lista=lista,
                                  req="; ".join(regras(b)) or "(nenhuma)"), max_tokens=4000)
            return {str(x) for x in r.get("manter", [])}
        except Exception as e:
            log(f"triagem falhou ({tentativa + 1}/2): {e}")
    return {str(a["listId"]) for a in ads}


def julgar(a, b, det):
    props = "; ".join(f"{k}: {v}" for k, v in det["props"].items() if k and v)
    p = PROMPT.format(termo=b.get("termo") or b["nome"],
                      req="\n".join(f"- {r}" for r in regras(b)) or "- (nenhuma)",
                      titulo=a.get("subject"), preco=a.get("priceValue"), props=props,
                      desc=det["descricao"][:3500])
    for tentativa in range(3):
        try:
            v = ia(p)
            if v.get("estado") in ("funciona", "defeito", "sucata", "incerto"):
                return v
        except Exception as e:
            log(f"IA falhou ({tentativa + 1}/3): {e}")
            time.sleep(5)
    return None


def regras(b):
    r = b.get("regras") or []
    return [r] if isinstance(r, str) else list(r)


def aprovado(v, b):
    if not v or not v.get("e_o_produto"):
        return False
    if v["estado"] == "incerto" and not cfg()["avisar_incerto"]:
        return False
    pr = v.get("preco_real")
    if isinstance(pr, (int, float)) and pr > int(b["max"]):
        return False  # preço isca: o produto custa mais que o teto (ex.: anúncio de mudança com vários itens)
    return bool(v.get("aprovar"))


def texto_anuncio(a, b, det, v):
    icone = {"funciona": "✅", "incerto": "⚠️ INCERTO", "defeito": "🛠 DEFEITO"}.get(v["estado"], "")
    antigo = f" <s>{html.escape(a['oldPrice'])}</s>" if a.get("oldPrice") else ""
    linhas = [f"🔔 <b>{html.escape(b['nome'])}</b> (teto R$ {b['max']})",
              f"<b>{html.escape(a.get('subject', ''))}</b>",
              (f"💰 <b>{html.escape(a.get('priceValue') or '')}</b>{antigo} + frete "
               + (f"R$ {v['frete']:.2f}".replace(".", ",") if isinstance(v.get("frete"), (int, float)) else "~R$ 50 (estimado)")
               + f" = <b>R$ {v.get('total', 0):.0f}</b> até Paragominas · 📍 {html.escape(a.get('location') or '')}"),
              f"{icone} {html.escape(v.get('resumo') or '')}"]
    if v.get("itens"):
        linhas.append(f"📦 {html.escape(v['itens'])}")
    if v.get("fotos_info"):
        linhas.append(f"📷 {html.escape(str(v['fotos_info'])[:250])}")
    if isinstance(v.get("preco_real"), (int, float)):
        linhas.append(f"⚠️ preço real deste item pela descrição: R$ {v['preco_real']}")
    if v.get("atende_requisitos") is None and b.get("regras"):
        linhas.append("❔ anúncio não diz se atende os requisitos — pergunte ao vendedor")
    if v.get("alerta"):
        linhas.append(f"⚠️ {html.escape(v['alerta'])}")
    linhas.append(f'<a href="{a.get("url")}">Abrir na OLX</a>')
    return "\n".join(linhas)


# ---------------- busca ----------------
def rodar_busca(b, vistos, avisar=True, mostrar=False):
    chave = str(b["id"])
    ja = vistos.setdefault(chave, {})
    avisados = 0
    from concurrent.futures import ThreadPoolExecutor

    def abrir_e_julgar(a):
        try:
            time.sleep(cfg()["pausa_entre_anuncios_s"])
            det = detalhe(a["url"])
        except Exception as e:
            log(f"[{b['nome']}] não abriu {a['url']}: {e}")
            return a, None, None
        if not det["entrega"]:
            return a, det, {"estado": "sem entrega"}
        v = julgar(a, b, det)
        if v and v.get("e_o_produto") and v.get("aprovar") and (v.get("duvidas") or "").strip():
            try:  # o texto não respondeu: as fotos às vezes respondem (tela do sistema, carregador na foto)
                f = ler_fotos(det["fotos"], FOTOS_PROMPT.format(termo=b.get("termo") or b["nome"],
                                                                duvidas=v["duvidas"]))
                if f:
                    v["fotos_info"] = f.get("respostas")
                    if f.get("fotos_de_outra_coisa"):
                        v["alerta"] = ((v.get("alerta") or "") + " | fotos de outros itens: anúncio de vários produtos,"
                                       " confira o preço deste").strip(" |")
                    if f.get("alerta"):
                        v["alerta"] = ((v.get("alerta") or "") + " | fotos: " + f["alerta"]).strip(" |")
            except Exception as e:
                log(f"fotos falhou: {e}")
        return a, det, v

    for pg in range(1, int(cfg()["max_paginas"]) + 1):
        ads = baixar_anuncios(montar_url(b, pg))
        passou_teto = False
        cand = []
        for a in ads:
            lid, p = str(a["listId"]), preco(a)
            if p is not None and p > int(b["max"]):
                passou_teto = True
                continue
            antigo = ja.get(lid)
            if antigo and (antigo.get("preco") == p or not antigo.get("ok_menos_preco")):
                continue  # já julgado (e preço igual) — não repete IA nem aviso
            if not filtro_rapido(a, b):
                ja[lid] = {"preco": p, "v": "filtro"}
                continue
            cand.append(a)
        manter = triagem(cand, b)
        abrir = []
        for a in cand:
            if str(a["listId"]) in manter:
                abrir.append(a)
            else:
                ja[str(a["listId"])] = {"preco": preco(a), "v": "triagem", "tit": (a.get("subject") or "")[:60]}
                if mostrar:
                    print(f"  corta {a.get('priceValue'):>9} (título) {a.get('subject')}", flush=True)
        with ThreadPoolExecutor(3) as ex:
            resultados = list(ex.map(abrir_e_julgar, abrir))
        for a, det, v in resultados:
            lid, p = str(a["listId"]), preco(a)
            antigo = ja.get(lid)
            if v is None:
                continue  # não abriu ou IA fora: tenta de novo na próxima rodada
            if v["estado"] == "sem entrega":
                ja[lid] = {"preco": p, "v": "sem entrega"}
                continue
            ok = aprovado(v, b)
            pr_item = v.get("preco_real") if isinstance(v.get("preco_real"), (int, float)) else p
            v["frete"] = det.get("frete")
            v["total"] = total(pr_item, det)
            if ok and v["total"] > int(b["max"]) * (1 + cfg().get("folga_frete", 0.0)):
                ok = False  # dona 04/11: o teto vale pelo TOTAL com frete até Paragominas
                v["motivo"] = f"com frete passa do teto (R$ {v['total']:.0f})"
            ja[lid] = {"preco": p, "v": v["estado"], "produto": v.get("e_o_produto"), "ok": ok,
                       "ok_menos_preco": ok, "tit": (a.get("subject") or "")[:60]}
            if mostrar:
                print(f"  {'AVISA' if ok else 'pula '} {a.get('priceValue'):>9} {v['estado']:9} "
                      f"prod={v.get('e_o_produto')} req={v.get('atende_requisitos')}  {a.get('subject')}\n"
                      f"         {v.get('resumo')} | {v.get('itens')} | {v.get('alerta')} | {v.get('motivo')}",
                      flush=True)
            if ok and antigo and antigo.get("ok") and (antigo.get("preco") or 0) <= (p or 0):
                continue  # já avisado por preço igual/menor
            if ok and avisar:
                if antigo and antigo.get("ok"):
                    v["resumo"] = f"BAIXOU de R$ {antigo.get('preco')} · " + (v.get("resumo") or "")
                mid = mandar(texto_anuncio(a, b, det, v), (det["fotos"] or [None])[0])
                if mid:
                    registrar_aviso(mid, b, a, v)
                avisados += 1
                if not (antigo and antigo.get("ok")):
                    try:
                        import olx_chat
                        olx_chat.enfileirar(b, a, v)
                    except Exception as e:
                        log(f"enfileirar chat falhou: {e}")
                time.sleep(1.2)
        if passou_teto or len(ads) < 40:
            break
        time.sleep(3)
    if len(ja) > 5000:
        for k in list(ja)[:len(ja) - 5000]:
            ja.pop(k)
    if avisados:
        log(f"[{b['nome']}] {avisados} avisados")
    return avisados


def rodar_todas():
    if not trava_busca.acquire(blocking=False):
        return 0
    try:
        with trava_arq:
            buscas = [b for b in ler(BUSCAS, []) if b.get("ativa", True)]
        falhas = 0
        for b in buscas:
            erro = None
            with trava_arq:
                vistos = ler(VISTOS, {})
            try:
                rodar_busca(b, vistos)
            except Exception as e:
                falhas += 1
                erro = str(e)
                log(f"[{b['nome']}] erro: {e}")
            with trava_arq:
                atual = ler(VISTOS, {})
                atual[str(b["id"])] = vistos.get(str(b["id"]), {})
                gravar(VISTOS, atual)
                todas = ler(BUSCAS, [])
                for x in todas:
                    if x["id"] == b["id"]:
                        x["ultima"] = datetime.now().strftime("%d/%m %H:%M")
                        x["erro"] = erro
                gravar(BUSCAS, todas)
            time.sleep(cfg()["pausa_entre_buscas_s"])
        return falhas
    finally:
        trava_busca.release()


# ---------------- comandos ----------------
def nova_busca(texto):
    partes = [p.strip() for p in texto.split("|")]
    b = {"ativa": True}
    if partes[0].startswith("http"):
        b["url"] = partes[0]
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(partes[0]).query))
        b["termo"] = q.get("q") or urllib.parse.urlsplit(partes[0]).path.strip("/").split("/")[-1]
    else:
        b["termo"] = partes[0]
    b["nome"] = b["termo"]
    for p in partes[1:]:
        k, _, v = p.partition(" ")
        k, v = k.lower().strip(), v.strip()
        if k in ("max", "min", "teto"):
            b["max" if k == "teto" else k] = int(re.sub(r"[^\d]", "", v))
        elif k in ("regras", "requisitos", "precisa"):
            b["regras"] = [f"precisa: {x.strip()}" for x in v.split(",") if x.strip()]
        elif k == "sem":
            b["sem"] = [w.strip() for w in v.split(",") if w.strip()]
        elif k == "nome":
            b["nome"] = v
        elif k == "defeito":
            b.setdefault("regras", []).append("aceita com defeito, desde que a função principal funcione")
    if not b.get("max"):
        raise ValueError("falta o teto: | max 150")
    with trava_arq:
        todas = ler(BUSCAS, [])
        b["id"] = max([x["id"] for x in todas] + [0]) + 1
        todas.append(b)
        gravar(BUSCAS, todas)
    return b


def descrever(b):
    extra = [f"até R$ {b['max']}"]
    if b.get("min"):
        extra.append(f"desde R$ {b['min']}")
    if regras(b):
        extra.append("regras: " + "; ".join(regras(b)))
    if b.get("sem"):
        extra.append("sem " + ", ".join(b["sem"]))
    v = ler(VISTOS, {}).get(str(b["id"]), {})
    bons = sorted((x["preco"] for x in v.values() if x.get("ok") and x.get("preco")))
    if bons:
        extra.append(f"{len(bons)} bons achados, mais barato R$ {bons[0]}")
    st = "✅" if b.get("ativa", True) else "⏸"
    err = f"\n   ⚠️ {html.escape(b['erro'][:80])}" if b.get("erro") else ""
    return (f"{st} <b>{b['id']}</b> — {html.escape(b['nome'])} · {html.escape(' · '.join(extra))}"
            f"  <i>{b.get('ultima', 'ainda não rodou')}</i>{err}")


AJUDA = ("<b>Buscas na OLX</b> (sempre com entrega, Brasil todo, do mais barato até o teto)\n"
         "/add carregador notebook dell | max 60 | precisa original, 19.5V | sem fonte universal\n"
         "/add &lt;link da OLX com categoria/filtros&gt; | max 150\n"
         "  opções: max (obrigatório), min, precisa (o que tem que ter), sem (palavras no título), "
         "defeito (aceita com defeito), nome\n"
         "/lista — buscas e achados\n/del N · /pausar N · /ligar N\n/agora — rodar já")


def tratar(cmd):
    c, _, resto = cmd.strip().partition(" ")
    c = c.split("@")[0].lower()
    if c in ("/start", "/ajuda", "/help"):
        return AJUDA
    if c == "/add":
        if not resto.strip():
            return AJUDA
        b = nova_busca(resto)
        threading.Thread(target=rodar_todas, daemon=True).start()
        return "Busca criada, rodando agora:\n" + descrever(b)
    if c == "/lista":
        return "\n".join(descrever(b) for b in ler(BUSCAS, [])) or "Nenhuma busca. Use /add"
    if c in ("/del", "/pausar", "/ligar"):
        try:
            n = int(resto.strip())
        except ValueError:
            return f"Use {c} NÚMERO (veja /lista)"
        with trava_arq:
            todas = ler(BUSCAS, [])
            alvo = [b for b in todas if b["id"] == n]
            if not alvo:
                return "Não achei essa busca."
            if c == "/del":
                todas = [b for b in todas if b["id"] != n]
                v = ler(VISTOS, {}); v.pop(str(n), None); gravar(VISTOS, v)
            else:
                alvo[0]["ativa"] = (c == "/ligar")
            gravar(BUSCAS, todas)
        return {"/del": "Apagada.", "/pausar": "Pausada.", "/ligar": "Ligada."}[c]
    if c == "/agora":
        threading.Thread(target=rodar_todas, daemon=True).start()
        return "Rodando todas agora..."
    return None


# ---------------- assistente (Sonnet) ----------------
HIST = BASE / "estado" / "conversa.json"
PROMPT_ASSIST = """Você é o assistente de compras da dona no Telegram. Um robô vigia a OLX (sempre com entrega, Brasil todo,
do menor preço até o teto) e a IA aprova anúncios seguindo as REGRAS de cada busca. A dona fala com você em português
informal, com erros de digitação. Entenda o que ela quer e devolva ações.

Buscas atuais (JSON):
{buscas}

{ref}
Conversa recente:
{hist}

Mensagem da dona: \"\"\"{msg}\"\"\"

Responda SÓ um JSON:
{{"acoes": [ ... ], "resposta": "texto curto e direto pra ela (confirme o que mudou; pergunte se faltar algo essencial)"}}
Ações possíveis:
 {{"tipo":"regra_add","busca":ID,"texto":"regra clara e autossuficiente, ex.: 'rejeitar se a tela estiver quebrada ou trincada'"}}
 {{"tipo":"regra_del","busca":ID,"indice":N}}   (índice na lista regras, começando em 0)
 {{"tipo":"teto","busca":ID,"valor":N}}  {{"tipo":"minimo","busca":ID,"valor":N}}
 {{"tipo":"sem_add","busca":ID,"palavras":["..."]}}   (palavras no TÍTULO que descartam)
 {{"tipo":"nova_busca","termo":"...","max":N,"regras":["..."],"sem":["..."]}}
 {{"tipo":"pausar"|"ligar"|"apagar","busca":ID}}
 {{"tipo":"rodar_agora"}}
IMPORTANTE sobre "sem": é corte cego pelo título, ANTES de ler o anúncio. Só use quando ela pedir explicitamente para
descartar uma palavra do título. NUNCA invente palavras que aparecem em anúncios bons (controle, carregador, tela, fonte,
bateria, jogo, defeito...). Para o resto, use regras (a IA lê o anúncio inteiro). Em nova_busca, "sem" = [] salvo pedido.
Não crie regras que ela não pediu além do padrão (o padrão já descarta peça/sucata/defeito e o que não é o produto).
Regras: se ela responde a um aviso, a busca é a do aviso. Regra vale só para aquela busca, a menos que ela diga "todas".
Se ela disser que algo é aceitável (ex.: "nesse pode vir quebrado se funcionar"), crie regra que AFROUXA o padrão.
Nova busca sem teto: não crie, pergunte o teto. Nada a fazer = "acoes": []."""


def _sonnet(prompt):
    j = ler(OMNI, {})
    for modelo in (cfg().get("modelo_assistente", "sonnet-fila"), "gemini/gemini-4-argon", cfg()["modelo_ia"]):
        try:
            r = cr.post(j["base_url"].rstrip("/") + "/v1/chat/completions", timeout=120,
                        headers={"Authorization": "Bearer " + j["api_key"]},
                        json={"model": modelo, "temperature": 0.2, "max_tokens": 1500,
                              "messages": [{"role": "user", "content": prompt}]})
            txt = r.json()["choices"][0]["message"]["content"]
            return json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
        except Exception as e:
            log(f"assistente {modelo} falhou: {e}")
    return None


def aplicar(ac):
    t = ac.get("tipo")
    if t == "rodar_agora":
        threading.Thread(target=rodar_todas, daemon=True).start()
        return "rodando agora"
    if t == "nova_busca":
        b = {"ativa": True, "termo": ac["termo"], "nome": ac["termo"], "max": int(ac["max"]),
             "regras": ac.get("regras") or [], "sem": ac.get("sem") or []}
        with trava_arq:
            todas = ler(BUSCAS, [])
            b["id"] = max([x["id"] for x in todas] + [0]) + 1
            todas.append(b)
            gravar(BUSCAS, todas)
        threading.Thread(target=rodar_todas, daemon=True).start()
        return f"nova busca {b['id']}"
    with trava_arq:
        todas = ler(BUSCAS, [])
        b = next((x for x in todas if x["id"] == int(ac.get("busca", -1))), None)
        if not b:
            return f"busca {ac.get('busca')} não existe"
        b["regras"] = regras(b)
        if t == "regra_add":
            b["regras"].append(ac["texto"])
        elif t == "regra_del":
            b["regras"].pop(int(ac["indice"]))
        elif t == "teto":
            b["max"] = int(ac["valor"])
        elif t == "minimo":
            b["min"] = int(ac["valor"])
        elif t == "sem_add":
            b["sem"] = list(dict.fromkeys((b.get("sem") or []) + ac["palavras"]))
        elif t in ("pausar", "ligar"):
            b["ativa"] = t == "ligar"
        elif t == "apagar":
            todas = [x for x in todas if x is not b]
        gravar(BUSCAS, todas)
    return f"{t} em {ac.get('busca')}"


def assistente(m):
    texto = m.get("text") or m.get("caption") or ""
    ref = ""
    resp_a = m.get("reply_to_message")
    if resp_a:
        av = ler(AVISOS, {}).get(str(resp_a["message_id"]))
        ref = ("Ela está RESPONDENDO a este aviso: " + json.dumps(av, ensure_ascii=False) if av else
               "Ela respondeu a esta mensagem do robô: " + (resp_a.get("text") or resp_a.get("caption") or "")[:800])
    else:
        ult = list(ler(AVISOS, {}).values())[-3:]
        if ult:
            ref = "Últimos avisos enviados (caso ela fale de um sem responder): " + json.dumps(ult, ensure_ascii=False)
    hist = ler(HIST, [])
    buscas = [{k: b.get(k) for k in ("id", "nome", "termo", "max", "min", "regras", "sem", "ativa")}
              for b in ler(BUSCAS, [])]
    r = _sonnet(PROMPT_ASSIST.format(buscas=json.dumps(buscas, ensure_ascii=False), ref=ref,
                                     hist="\n".join(hist[-12:]) or "(nenhuma)", msg=texto))
    if not r:
        return "Não consegui falar com a IA agora. Tente de novo em instantes ou use /ajuda."
    feitos = []
    for ac in r.get("acoes") or []:
        try:
            feitos.append(aplicar(ac))
        except Exception as e:
            feitos.append(f"erro em {ac.get('tipo')}: {e}")
    log(f"assistente: {texto[:80]!r} -> {feitos}")
    resposta = r.get("resposta") or "Feito."
    hist += [f"dona: {texto}", f"você: {resposta} {feitos if feitos else ''}"]
    gravar(HIST, hist[-30:])
    return html.escape(resposta)


def escutar_telegram():
    _, chat, proprio = bot()
    if not proprio:
        log("sem bot próprio em config.json: só avisos, comandos desligados")
        return
    off = None
    while True:
        j = tg("getUpdates", {"timeout": 30, **({"offset": off} if off else {})}, timeout=45)
        if not j or not j.get("ok"):
            time.sleep(10)
            continue
        for u in j["result"]:
            off = u["update_id"] + 1
            m = u.get("message") or {}
            if str(m.get("chat", {}).get("id")) != chat:
                log(f"mensagem de chat desconhecido {m.get('chat', {}).get('id')} "
                    f"({m.get('from', {}).get('first_name')}): {str(m.get('text'))[:40]}")
                continue  # só a dona manda
            try:
                txt = (m.get("text") or "").strip()
                if txt.startswith("/"):
                    resp = tratar(txt)
                elif txt:
                    tg("sendChatAction", {"chat_id": chat, "action": "typing"})
                    resp = assistente(m)
                else:
                    resp = None
            except Exception as e:
                resp = f"Erro: {html.escape(str(e))}"
            if resp:
                mandar(resp)


# ---------------- principal ----------------
def ja_rodando():
    try:
        pid = int(TRAVA.read_text())
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if h:
            codigo = ctypes.c_ulong()
            ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(codigo))
            buf = ctypes.create_unicode_buffer(520)
            n = ctypes.c_ulong(520)
            ctypes.windll.kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
            ctypes.windll.kernel32.CloseHandle(h)
            # PID reaproveitado pelo Windows não conta: tem que ser um python
            return codigo.value == 259 and pid != os.getpid() and "python" in buf.value.lower()
    except Exception:
        pass
    return False


def principal():
    if ja_rodando():
        return
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    TRAVA.write_text(str(os.getpid()))
    log("iniciado")
    threading.Thread(target=escutar_telegram, daemon=True).start()

    def laco_chat():
        import olx_chat
        while True:
            time.sleep(60)
            try:
                olx_chat.ciclo()
            except Exception as e:
                log(f"chat: {e}")
            time.sleep(int(cfg().get("chat_ciclo_min", 10)) * 60)
    threading.Thread(target=laco_chat, daemon=True).start()
    erros_seguidos = 0
    while True:
        try:
            falhas = rodar_todas()
            n = len([b for b in ler(BUSCAS, []) if b.get("ativa", True)])
            erros_seguidos = erros_seguidos + 1 if (n and falhas == n) else 0
            if erros_seguidos == 3:
                mandar("⚠️ OLX falhou em todas as buscas 3 vezes seguidas. Veja estado\\olx.log")
        except Exception:
            log(traceback.format_exc())
        time.sleep(cfg()["intervalo_min"] * 60)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "uma-vez":
        rodar_todas()
    elif arg == "testar":
        b = {"id": 0, "nome": "teste", "termo": sys.argv[2], "max": int(sys.argv[3]),
             "regras": sys.argv[4] if len(sys.argv) > 4 else ""}
        print(montar_url(b))
        rodar_busca(b, {}, avisar=False, mostrar=True)
    elif arg == "comando":
        print(tratar(" ".join(sys.argv[2:])))
    else:
        principal()
