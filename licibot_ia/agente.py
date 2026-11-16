"""
LiciBot-IA · agente.py — assistente do painel.

Responde perguntas sobre o sistema e sobre as licitações, consultando o banco por ferramentas e lendo páginas
oficiais. Usa SÓ os modelos grátis da cadeia (ai_analyzer.MODELOS_GRATIS): nunca o Opus pago.

Ferramentas:
  buscar_licitacoes   filtros (UF, valor, sobra, carteira, tipo, CNAE, prazo, texto) → lista com link do PNCP
  ver_licitacao       tudo de uma licitação (análise, itens, riscos, exigências, contas)
  resumo_numeros      contagens e somas por carteira/UF/tipo/situação
  simular             roda o simulador de investimento com os parâmetros pedidos
  ler_pagina          lê o texto de uma página (só domínios oficiais/confiáveis), para citar a fonte
Não existe busca livre na web: nenhum buscador grátis funcionou a partir da VPS (11/11 e 15/11).
"""

from __future__ import annotations

import json
import logging
import re
import time
from html import unescape
from typing import Any

import anthropic
import httpx

import database as db
from ai_analyzer import MODELOS_GRATIS, cadeia_atual
from config import (BASE, CNAES_DENILDO, CNAES_MEI, GAVETA_TIPO, LLM_API_KEY, NOSSA_CIDADE, NOSSA_UF,
                    normalizar)

log = logging.getLogger("licibot.agente")

DOMINIOS_LEITURA = ("pncp.gov.br", "gov.br", "planalto.gov.br", "ibge.gov.br", "concla.ibge.gov.br",
                    "receita.fazenda.gov.br", "in.gov.br", "tcu.gov.br", "sebrae.com.br",
                    "compras.gov.br", "portaldecompraspublicas.com.br", "bllcompras.com", "licitanet.com.br")
MAX_PASSOS = 6
LIMITE_LISTA = 25

# ═════════════════════════════════════════════════════════════════════════════
# ferramentas
# ═════════════════════════════════════════════════════════════════════════════

FERRAMENTAS = [
    {"name": "buscar_licitacoes",
     "description": "Busca licitações no banco do LiciBot com filtros combináveis. Devolve até 25, já ordenadas, "
                    "com número, objeto, órgão, UF, carteira, nota, valores e link do PNCP. Use para qualquer "
                    "pergunta do tipo 'quais', 'mostre', 'tem alguma', 'as melhores'.",
     "input_schema": {"type": "object", "properties": {
         "texto": {"type": "string", "description": "palavras no objeto/órgão/município (ex.: 'uniforme')"},
         "ufs": {"type": "array", "items": {"type": "string"}, "description": "siglas, ex.: ['GO','DF']"},
         "carteiras": {"type": "array", "items": {"type": "string", "enum": ["MEI", "CPF", "DENILDO", "DESCARTADO"]}},
         "tipos": {"type": "array", "items": {"type": "string", "enum": ["produto", "servico", "obra"]}},
         "cnaes": {"type": "array", "items": {"type": "string"}, "description": "códigos CNAE, ex.: ['4781-4/00']"},
         "valor_min": {"type": "number"}, "valor_max": {"type": "number"},
         "sobra_min": {"type": "number", "description": "quanto sobra no bolso, mínimo (R$)"},
         "investe_max": {"type": "number", "description": "custo para entregar, máximo (R$)"},
         "nota_min": {"type": "number"},
         "fecha_em_dias": {"type": "number", "description": "só as que fecham em até N dias"},
         "situacao": {"type": "string", "enum": ["abertas", "todas", "encerradas", "fila"],
                      "description": "padrão: abertas e já analisadas"},
         "ordenar": {"type": "string", "enum": ["nota", "sobra", "prazo", "valor"], "description": "padrão: nota"}},
         "additionalProperties": False}},
    {"name": "ver_licitacao",
     "description": "Mostra tudo de uma licitação pelo número de controle do PNCP: análise da IA, contas, "
                    "exigências, riscos, itens e documentos lidos.",
     "input_schema": {"type": "object", "properties": {"numero": {"type": "string"}}, "required": ["numero"],
                      "additionalProperties": False}},
    {"name": "resumo_numeros",
     "description": "Números gerais: quantas licitações por situação, carteira, UF ou tipo, e somas de valor e "
                    "sobra. Use para 'quantas', 'quanto no total', 'qual estado tem mais'.",
     "input_schema": {"type": "object", "properties": {
         "agrupar_por": {"type": "string", "enum": ["carteira", "uf", "tipo", "situacao", "cnae"]},
         "so_abertas": {"type": "boolean"}}, "required": ["agrupar_por"], "additionalProperties": False}},
    {"name": "simular",
     "description": "Simula quanto renderia investir R$ X disputando no automático (o robô dá o próprio lance). "
                    "Devolve lucro pessimista/esperado/se ganhar todas, quantas disputa e em quantos dias recebe.",
     "input_schema": {"type": "object", "properties": {
         "capital": {"type": "number"}, "margem_min_pct": {"type": "number"}, "dias": {"type": "number"},
         "carteiras": {"type": "array", "items": {"type": "string", "enum": ["MEI", "CPF", "DENILDO"]}},
         "tipos": {"type": "array", "items": {"type": "string", "enum": ["produto", "servico", "obra"]}}},
         "required": ["capital"], "additionalProperties": False}},
    {"name": "ler_pagina",
     "description": "Lê o texto de uma página para citar a fonte. Só aceita sites oficiais e de compras públicas "
                    "(pncp.gov.br, gov.br, planalto.gov.br, ibge.gov.br, sebrae etc.). Use o link do PNCP da "
                    "licitação ou o endereço oficial de uma lei/norma.",
     "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"],
                      "additionalProperties": False}},
]

_COLS = ("numero_controle, objeto_compra, razao_social, uf, municipio, carteira, status, gaveta, nota_final, "
         "valor_estimado, margem_estimada, custo_estimado, data_encerramento, cnae_sugerido, link_pncp, decisao")


def _abertas() -> str:
    return "data_encerramento > datetime('now','localtime')"


def buscar_licitacoes(a: dict[str, Any]) -> dict[str, Any]:
    cond, args = [], []
    sit = a.get("situacao") or "abertas"
    if sit == "abertas":
        cond.append(f"status='analisado' AND {_abertas()}")
        if not a.get("carteiras"):
            cond.append("carteira!='DESCARTADO'")
    elif sit == "encerradas":
        cond.append(f"NOT ({_abertas()})")
    elif sit == "fila":
        cond.append(f"status IN ('novo','enriquecido') AND {_abertas()}")
    if a.get("texto"):
        for palavra in normalizar(a["texto"]).split()[:6]:
            cond.append("(lower(objeto_compra) LIKE ? OR lower(razao_social) LIKE ? OR lower(municipio) LIKE ?)")
            args += [f"%{palavra}%"] * 3
    for campo, chave in (("uf", "ufs"), ("carteira", "carteiras"), ("cnae_sugerido", "cnaes")):
        if a.get(chave):
            cond.append(f"{campo} IN ({','.join('?' * len(a[chave]))})")
            args += [str(x).upper() if chave == "ufs" else str(x) for x in a[chave]]
    if a.get("tipos"):
        gavs = [g for g, t in GAVETA_TIPO.items() if t in a["tipos"]]
        cond.append(f"gaveta IN ({','.join('?' * len(gavs))})")
        args += gavs
    for campo, chave, op in (("valor_estimado", "valor_min", ">="), ("valor_estimado", "valor_max", "<="),
                             ("margem_estimada", "sobra_min", ">="), ("custo_estimado", "investe_max", "<="),
                             ("nota_final", "nota_min", ">=")):
        if a.get(chave) is not None:
            cond.append(f"coalesce({campo},0) {op} ?")
            args.append(float(a[chave]))
    if a.get("fecha_em_dias"):
        cond.append("data_encerramento <= datetime('now','localtime', ?)")
        args.append(f"+{int(a['fecha_em_dias'])} days")
    ordem = {"sobra": "margem_estimada DESC", "prazo": "data_encerramento", "valor": "valor_estimado DESC"}.get(
        a.get("ordenar") or "", "nota_final DESC")
    where = " AND ".join(cond) or "1=1"
    with db.conexao() as c:
        total = c.execute(f"SELECT count(*) FROM editais WHERE {where}", args).fetchone()[0]
        rows = [dict(r) for r in c.execute(
            f"SELECT {_COLS} FROM editais WHERE {where} ORDER BY {ordem} LIMIT {LIMITE_LISTA}", args)]
    for r in rows:
        r["objeto_compra"] = (r["objeto_compra"] or "")[:160]
        r["tipo"] = GAVETA_TIPO.get(r.pop("gaveta"), "servico")
    saida = {"total_encontradas": total, "mostrando": len(rows), "licitacoes": rows}
    if not total:
        saida["aviso"] = ("Nenhuma encontrada com esses filtros. Não repita a mesma busca com outras palavras mais "
                          "de 1 vez: diga à pessoa que não há agora e sugira afrouxar filtros ou olhar a fila. "
                          "A busca do comércio do Denildo (roupas, uniformes, material elétrico, calçados, "
                          "brinquedos...) começou em 15/11: essas licitações aparecem depois das próximas varreduras.")
    return saida


def ver_licitacao(a: dict[str, Any]) -> dict[str, Any]:
    e = db.buscar(a["numero"].strip())
    if not e:
        return {"erro": "não achei essa licitação no banco"}
    e.pop("texto_docs", None)
    try:
        ia = json.loads(e.pop("json_ia") or "null") or {}
    except ValueError:
        ia = {}
    itens = db.itens_de(e["numero_controle"])
    return {**{k: e[k] for k in ("numero_controle", "objeto_compra", "razao_social", "uf", "municipio",
                                  "modalidade_nome", "carteira", "status", "nota_final", "score_viabilidade",
                                  "score_pagador", "valor_estimado", "valor_lance", "custo_estimado",
                                  "margem_estimada", "liquido_mei", "liquido_cpf", "data_encerramento",
                                  "exclusivo_me_epp", "cnae_sugerido", "resumo_ia", "exigencias", "riscos",
                                  "docs_lidos", "link_pncp", "link_sistema", "decisao", "anotacao")},
            "motivo_descarte": ia.get("motivo_descarte"), "itens_que_atendemos": ia.get("itens_que_atendemos"),
            "itens": [{k: i[k] for k in ("numero_item", "descricao", "quantidade", "unidade", "valor_unitario",
                                         "valor_total", "tipo_beneficio_nome")} for i in itens[:40]],
            "qtd_itens": len(itens)}


def resumo_numeros(a: dict[str, Any]) -> dict[str, Any]:
    campo = {"carteira": "carteira", "uf": "uf", "situacao": "status", "cnae": "cnae_sugerido",
             "tipo": "gaveta"}[a["agrupar_por"]]
    where = f"WHERE status='analisado' AND {_abertas()}" if a.get("so_abertas", True) else ""
    with db.conexao() as c:
        rows = [dict(r) for r in c.execute(
            f"SELECT {campo} grupo, count(*) qtd, round(sum(coalesce(valor_estimado,0))) valor, "
            f"round(sum(coalesce(margem_estimada,0))) sobra FROM editais {where} GROUP BY {campo} "
            f"ORDER BY qtd DESC LIMIT 40")]
    if a["agrupar_por"] == "tipo":
        for r in rows:
            r["grupo"] = GAVETA_TIPO.get(r["grupo"], r["grupo"])
    return {"agrupado_por": a["agrupar_por"], "so_abertas": a.get("so_abertas", True), "grupos": rows}


def simular(a: dict[str, Any]) -> dict[str, Any]:
    import simulador
    p = simulador.Parametros(capital=float(a["capital"]))
    if a.get("margem_min_pct") is not None:
        p.margem_min = float(a["margem_min_pct"]) / 100
    if a.get("dias"):
        p.dias = int(a["dias"])
    if a.get("carteiras"):
        p.carteiras = tuple(a["carteiras"])
    if a.get("tipos"):
        p.tipos = tuple(a["tipos"])
    r = simulador.para_json(simulador.simular(p))
    top = sorted(r["escolhidas"], key=lambda o: -o["lucro_esperado"])[:8]
    return {"resumo": r["resumo"], "parametros": r["parametros"],
            "principais": [{k: o[k] for k in ("objeto", "uf", "custo", "lance_robo", "lucro", "chance",
                                              "lucro_esperado", "link")} for o in top]}


def ler_pagina(a: dict[str, Any]) -> dict[str, Any]:
    url = a["url"].strip()
    dominio = re.sub(r"^https?://", "", url).split("/")[0].lower()
    if not any(dominio == d or dominio.endswith("." + d) for d in DOMINIOS_LEITURA):
        return {"erro": f"só leio sites oficiais/de compras públicas; {dominio} não está na lista"}
    try:
        r = httpx.get(url, timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 LiciBot"})
        r.raise_for_status()
    except httpx.HTTPError as err:
        return {"erro": f"não consegui abrir: {type(err).__name__}"}
    texto = r.text
    if "html" in r.headers.get("content-type", ""):
        texto = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", texto, flags=re.S | re.I)
        texto = unescape(re.sub(r"<[^>]+>", " ", texto))
    texto = re.sub(r"\s+", " ", texto).strip()
    return {"url": str(r.url), "texto": texto[:12_000], "cortado": len(texto) > 12_000}


def explicar_cnae(a: dict[str, Any]) -> dict[str, Any]:
    """O IBGE bloqueia robô (Cloudflare) e a API dele não responde da VPS: a descrição vem da lista do sistema
    e o link oficial é para a pessoa abrir no navegador dela."""
    cod = re.sub(r"\D", "", a["codigo"])
    fmt = f"{cod[:4]}-{cod[4]}/{cod[5:7]}" if len(cod) == 7 else a["codigo"]
    quem = [nome for nome, lista in (("MEI", CNAES_MEI), ("DENILDO", CNAES_DENILDO)) if fmt in lista]
    desc = CNAES_DENILDO.get(fmt) or CNAES_MEI.get(fmt)
    return {"codigo": fmt, "descricao": desc or "não está nas listas do sistema (MEI e Denildo)",
            "de_quem": quem or ["nenhuma carteira"],
            "link_oficial": f"https://concla.ibge.gov.br/busca-online-cnae.html?subclasse={cod}&tipo=cnae&versao=10&view=subclasse",
            "obs": "o site do IBGE só abre no navegador da pessoa (bloqueia robô); passe o link para ela conferir"}


FERRAMENTAS.append(
    {"name": "explicar_cnae",
     "description": "Explica um código CNAE (atividade da empresa): descrição, se é do MEI ou do Denildo, e o link "
                    "oficial do IBGE para a pessoa conferir. Use em vez de ler_pagina para CNAE.",
     "input_schema": {"type": "object", "properties": {"codigo": {"type": "string", "description": "ex.: 4781-4/00"}},
                      "required": ["codigo"], "additionalProperties": False}})

EXECUTORES = {"buscar_licitacoes": buscar_licitacoes, "ver_licitacao": ver_licitacao,
              "resumo_numeros": resumo_numeros, "simular": simular, "ler_pagina": ler_pagina,
              "explicar_cnae": explicar_cnae}


# ═════════════════════════════════════════════════════════════════════════════
# conversa
# ═════════════════════════════════════════════════════════════════════════════

def _sistema() -> str:
    try:
        manual = (BASE / "LEIA_PRIMEIRO.md").read_text(encoding="utf-8")[:9000]
    except OSError:
        manual = ""
    with db.conexao() as c:
        n = c.execute(f"SELECT count(*) FROM editais WHERE status='analisado' AND carteira!='DESCARTADO' "
                      f"AND {_abertas()}").fetchone()[0]
    return f"""Você é o assistente do LiciBot, um robô que acha licitações públicas (compras do governo no PNCP) \
para uma pessoa de {NOSSA_CIDADE}/{NOSSA_UF}. Quem pergunta pode ser leigo no assunto: responda em português \
simples, curto e direto, explicando termo técnico na primeira vez que aparecer (ex.: "pregão = disputa de preço \
pela internet"). Hoje há {n} oportunidades abertas e analisadas.

Carteiras (quem disputa): MEI (a dona, serviços com IA e produtos de informática, teto R$ 81 mil/ano), CPF \
(pessoa física, serviços intelectuais), DENILDO (o parceiro com CNPJ: energia solar, instalações, e venda de \
material elétrico, roupas/uniformes, calçados, brinquedos, cama-mesa-banho, armarinho, brindes/troféus). \
CNAEs do MEI: {json.dumps(CNAES_MEI, ensure_ascii=False)}. CNAEs do Denildo: {json.dumps(CNAES_DENILDO, ensure_ascii=False)}.

Regras:
- Para qualquer pergunta sobre licitações, USE as ferramentas; nunca invente licitação, número ou valor.
- Sempre que citar uma licitação, coloque o link do PNCP dela (campo link_pncp) em formato markdown [texto](link).
- Valores em reais no formato R$ 12.345. Datas dd/mm.
- Quando a pergunta for geral (lei, imposto, CNAE) e não houver fonte no banco: se souber o endereço oficial, \
use ler_pagina e cite o link; se não, responda do seu conhecimento e diga claramente "isso é do meu \
conhecimento, confira na fonte oficial". Nunca invente link.
- "Sobra" = quanto fica no bolso depois de custos e impostos (estimativa). "Nota" = 0 a 100, o quanto vale a pena.
- Estimativas (sobra, chance, simulação) são para decidir, não promessa: diga isso quando falar de dinheiro.
- Não altere nada: você só consulta.

Manual do sistema (para explicar como funciona):
{manual}"""


def perguntar(historico: list[dict[str, Any]]) -> dict[str, Any]:
    """historico = [{"role": "user"|"assistant", "content": "texto"}, ...] (só texto, vindo do painel).
    Devolve {"resposta": str, "modelo": str, "ferramentas": [nomes usados]}."""
    msgs = [{"role": m["role"], "content": str(m["content"])[:4000]} for m in historico[-12:]
            if m.get("role") in ("user", "assistant") and m.get("content")]
    if not msgs or msgs[-1]["role"] != "user":
        raise ValueError("a última mensagem tem que ser sua")
    sistema = _sistema()
    usadas: list[str] = []
    erros = []
    for modelo in cadeia_atual():
        info = MODELOS_GRATIS[modelo]
        cli = anthropic.Anthropic(base_url=info["base"], api_key=LLM_API_KEY or "sem-chave",
                                  timeout=min(info["prazo"], 120), max_retries=0)
        conversa = list(msgs)
        try:
            for passo in range(MAX_PASSOS + 1):
                ultimo = passo == MAX_PASSOS
                extra = {} if ultimo else {"tools": FERRAMENTAS}
                if ultimo:   # chega de consultar: responde com o que já tem
                    conversa.append({"role": "user", "content": "Pare de consultar e responda agora com o que já "
                                     "descobriu, de forma clara para a pessoa (inclua os links que tiver)."})
                r = cli.messages.create(model=modelo, max_tokens=2500, system=sistema, messages=conversa, **extra)
                chamadas = [b for b in r.content if b.type == "tool_use"]
                if not chamadas:
                    texto = "".join(b.text for b in r.content if b.type == "text").strip()
                    if not texto:
                        raise ValueError("resposta vazia")
                    return {"resposta": texto, "modelo": info["nome"], "ferramentas": usadas}
                conversa.append({"role": "assistant", "content": [b.model_dump() for b in r.content]})
                resultados = []
                for ch in chamadas:
                    usadas.append(ch.name)
                    try:
                        saida = EXECUTORES[ch.name](dict(ch.input or {}))
                    except Exception as err:          # ferramenta com argumento ruim: devolve o erro ao modelo
                        saida = {"erro": f"{type(err).__name__}: {err}"[:300]}
                    resultados.append({"type": "tool_result", "tool_use_id": ch.id,
                                       "content": json.dumps(saida, ensure_ascii=False, default=str)[:30_000]})
                conversa.append({"role": "user", "content": resultados})
            return {"resposta": "Precisei de passos demais para responder. Tente uma pergunta mais direta.",
                    "modelo": info["nome"], "ferramentas": usadas}
        except (anthropic.APIError, ValueError, KeyError) as err:
            erros.append(f"{info['nome']}: {type(err).__name__}")
            log.info("agente: %s falhou (%s); tentando o próximo", info["nome"], err)
            continue
    return {"resposta": "Nenhum modelo grátis respondeu agora (" + "; ".join(erros) + "). Tente de novo em alguns "
                        "minutos.", "modelo": "", "ferramentas": usadas}


if __name__ == "__main__":
    import sys
    t = time.time()
    print(json.dumps(perguntar([{"role": "user", "content": " ".join(sys.argv[1:]) or "Quais as 3 melhores em GO?"}]),
                     ensure_ascii=False, indent=2))
    print(f"{time.time() - t:.0f} s")
