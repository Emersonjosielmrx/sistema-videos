"""Avaliação POR ETAPA (26/10, dono): qual modelo é melhor em cada etapa, para misturar — ou, se um ganhar em
tudo, usar só ele. Desempate: custo (grátis > crédito mensal > cota paga do Claude Pro).

  roteiro  mesmo pedido (Cardápio) -> regras checadas por código + nota ÀS CEGAS do juiz (Opus 5.5)
  visao    folha com defeito CONHECIDO (1º vídeo, revisao_1: texto em cima do rosto na cena 3) tem que reprovar e
           apontar a cena 3; folha limpa (revisao_2, aprovada e conferida a olho) não pode dar alarme falso
  editar   vídeos do comparar_modelos.py -> folha de 8 quadros de cada um com nota ÀS CEGAS do juiz

    python comparar_etapas.py roteiro visao     (rápido, pode rodar junto com a comparação de edição)
    python comparar_etapas.py editar            (depois que o comparar_modelos.py terminar)
    python comparar_etapas.py resultado
Tudo em estado/avaliacao_etapas.json.
"""
import json
import random
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gerar  # noqa: E402
import motor  # noqa: E402

PADRAO = "cc/claude-opus-5-5"
MODELOS = [PADRAO, "antigravity/gemini-3.8-flash-tiered", "kr/claude-sonnet-4.5", "antigravity/claude-opus-4-6-thinking"]
CUSTO = {PADRAO: "cota paga (Claude Pro)", "antigravity/gemini-3.8-flash-tiered": "grátis",
         "kr/claude-sonnet-4.5": "crédito mensal (Kiro)", "antigravity/claude-opus-4-6-thinking": "grátis (pouca cota)"}
ORDEM_CUSTO = {"grátis": 0, "grátis (pouca cota)": 1, "crédito mensal (Kiro)": 2, "cota paga (Claude Pro)": 3}
ARQ = gerar.RAIZ / "estado" / "avaliacao_etapas.json"
PASTA = gerar.RAIZ / "_avaliacao"
PRIMEIRO = gerar.TRABALHOS / "futebolcom_ia2_20261025_180110"     # vídeo molde com o defeito conhecido


def _ler():
    return json.loads(ARQ.read_text("utf-8")) if ARQ.exists() else {}


def _gravar(d):
    ARQ.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")


def _chamar(prompt, pasta, etapa, modelo, **kw):
    ini = time.time()
    try:
        r = motor.chamar_json(prompt, pasta, "avaliacao", etapa, modelo=None if modelo == PADRAO else modelo, **kw)
        return r, round(time.time() - ini, 1), None
    except Exception as e:  # noqa: BLE001
        return None, round(time.time() - ini, 1), f"{type(e).__name__}: {str(e)[:200]}"


# ───────────────────────────── roteiro ─────────────────────────────

def regras_roteiro(r):
    """Lista de violações (vazia = passou)."""
    if not r:
        return ["sem resposta"]
    v = []
    cenas = r.get("cenas") or []
    if len(cenas) != 4:
        v.append(f"{len(cenas)} cenas (pedido: 4)")
    for i, c in enumerate(cenas, 1):
        for campo in ("fala", "texto_tela", "prompt_en", "efeito"):
            if not c.get(campo):
                v.append(f"cena {i} sem {campo}")
        fala, tela = c.get("fala", ""), c.get("texto_tela", "")
        if len(fala.split()) > 22:
            v.append(f"cena {i}: fala com {len(fala.split())} palavras")
        if not 2 <= len(tela.split()) <= 4:
            v.append(f"cena {i}: texto_tela com {len(tela.split())} palavras")
        if re.search(r"\d", fala + " " + tela):
            v.append(f"cena {i}: número na fala/tela")
        if re.search(r"@|www|http|\.com|whats\s*\d|\(\d{2}\)", fala + " " + tela, re.I):
            v.append(f"cena {i}: contato/link")
    if not r.get("titulo"):
        v.append("sem título")
    return v


def avaliar_roteiro():
    d = _ler()
    k = gerar.kit_mod.kit("futebolcom.ia2")
    p = PASTA / "roteiro"
    p.mkdir(parents=True, exist_ok=True)
    for m in MODELOS:
        r, seg, erro = _chamar(gerar.prompt_roteiro(k), p, "roteiro", m, max_turnos=2)
        d.setdefault("roteiro", {})[m] = {"roteiro": r, "segundos": seg, "erro": erro, "violacoes": regras_roteiro(r)}
        gerar.log(f"[avaliação roteiro] {m}: {seg}s, violações {d['roteiro'][m]['violacoes'] or 'nenhuma'}")
        _gravar(d)
    # juiz às cegas
    vivos = [m for m in MODELOS if d["roteiro"][m]["roteiro"]]
    random.shuffle(vivos)
    letras = {chr(65 + i): m for i, m in enumerate(vivos)}
    textos = "\n\n".join(f"=== ROTEIRO {L} ===\n" + json.dumps(d["roteiro"][m]["roteiro"], ensure_ascii=False, indent=1)
                         for L, m in letras.items())
    juiz, _, erro = _chamar(f"""Você é diretor de criação de uma agência. Dê nota 1-10 a cada roteiro de anúncio
Reels (20-30 s) do produto Cardápio Digital para donos de restaurante. Critérios: gancho forte nos 3 primeiros
segundos, clareza do benefício, ritmo falado natural em pt-BR, texto de tela curto e forte, fotos pedidas que
sustentam a cena, zero exagero/invenção. Seja duro e diferencie.

{textos}

Responda SÓ JSON: {{"notas": {{"A": 0, ...}}, "motivo": {{"A": "uma frase", ...}}}}""", p, "juiz_roteiro", PADRAO,
                         max_turnos=1)
    for L, m in letras.items():
        d["roteiro"][m]["nota_juiz"] = (juiz or {}).get("notas", {}).get(L)
        d["roteiro"][m]["motivo_juiz"] = (juiz or {}).get("motivo", {}).get(L)
    d["roteiro_juiz_erro"] = erro
    _gravar(d)


# ───────────────────────────── visão / revisão ─────────────────────────────

def avaliar_visao():
    d = _ler()
    t = gerar.Trabalho(PRIMEIRO)
    resumo = "\n".join(f"- cena {i + 1}: texto \"{c['texto_tela']}\"" for i, c in enumerate(t.e["roteiro"]["cenas"]))
    p = PASTA / "visao"
    p.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PRIMEIRO / "revisao_1.jpg", p / "folha_a.jpg")     # defeito conhecido: cena 3
    shutil.copy2(PRIMEIRO / "revisao_2.jpg", p / "folha_b.jpg")     # limpa
    for m in MODELOS:
        res = {}
        for folha, esperado in (("folha_a.jpg", "defeito"), ("folha_b.jpg", "limpa")):
            r, seg, erro = _chamar(gerar.prompt_revisao(folha, resumo), p, "visao", m, max_turnos=4)
            texto = json.dumps(r or {}, ensure_ascii=False).lower()
            cenas_apontadas = {a.get("cena") for a in (r or {}).get("ajustes") or [] if isinstance(a, dict)}
            if esperado == "defeito":
                acertou = bool(r) and not r.get("aprovado") and (3 in cenas_apontadas or "cena 3" in texto)
            else:
                acertou = bool(r) and (bool(r.get("aprovado")) or int(r.get("nota") or 0) >= 7)
            res[esperado] = {"acertou": acertou, "nota": (r or {}).get("nota"), "aprovado": (r or {}).get("aprovado"),
                             "cenas_apontadas": sorted(x for x in cenas_apontadas if x), "comentario":
                             (r or {}).get("comentario"), "segundos": seg, "erro": erro}
        d.setdefault("visao", {})[m] = res
        gerar.log(f"[avaliação visão] {m}: defeito {'ACHOU' if res['defeito']['acertou'] else 'errou'}, "
                  f"limpa {'ok' if res['limpa']['acertou'] else 'ALARME FALSO/erro'}")
        _gravar(d)


# ───────────────────────────── edição ─────────────────────────────

def avaliar_editar():
    sys.path.append(r"D:\claude-code-video-adicional")
    import adicional
    d = _ler()
    comp = json.loads((gerar.RAIZ / "estado" / "comparacao.json").read_text("utf-8"))
    videos = {PADRAO: str(gerar.SAIDA / "futebolcom.ia2" / "futebolcom_ia2_20261025_231549.mp4")}
    for m, x in comp.items():
        if x.get("saida"):
            videos[m] = x["saida"]
    p = PASTA / "editar"
    p.mkdir(parents=True, exist_ok=True)
    ordem = list(videos)
    random.shuffle(ordem)
    letras = {}
    for i, m in enumerate(ordem):
        L = chr(65 + i)
        letras[L] = m
        shutil.move(str(adicional.folha_quadros(videos[m])), p / f"video_{L}.jpg")
    lista = ", ".join(f"video_{L}.jpg" for L in letras)
    juiz, _, erro = _chamar(f"""Use Read para OLHAR {lista} (pasta atual). Cada folha tem 8 quadros, em ordem, de um
anúncio Reels do MESMO produto com o MESMO roteiro e narração — só o editor muda. Dê nota 1-10 de motion design
profissional: riqueza e intenção dos elementos gráficos (telas, cards, ícones), texto legível e dentro da tela,
nada quebrado/sobreposto, cenas vazias, coerência com a marca, nível de agência. Seja duro e diferencie.
Responda SÓ JSON: {{"notas": {{"A": 0, ...}}, "motivo": {{"A": "uma frase", ...}}}}""", p, "juiz_editar", PADRAO,
                            max_turnos=len(letras) + 2)
    d["editar"] = {m: {**comp.get(m, {"status": "pronto", "minutos": 44.4}), "video": videos[m],
                       "nota_juiz": (juiz or {}).get("notas", {}).get(L),
                       "motivo_juiz": (juiz or {}).get("motivo", {}).get(L)} for L, m in letras.items()}
    for m in MODELOS:
        if m not in videos:
            d["editar"][m] = {**comp.get(m, {}), "nota_juiz": 0, "motivo_juiz": "não entregou vídeo"}
    d["editar_juiz_erro"] = erro
    _gravar(d)


# ───────────────────────────── resultado ─────────────────────────────

def pontos(d, etapa, m):
    x = (d.get(etapa) or {}).get(m)
    if not x:
        return None
    if etapa == "roteiro":
        return (x.get("nota_juiz") or 0) - 2 * len(x.get("violacoes") or [])
    if etapa == "visao":
        return 5 * bool(x["defeito"]["acertou"]) + 5 * bool(x["limpa"]["acertou"])
    return x.get("nota_juiz") or 0


def resultado():
    d = _ler()
    etapas = [e for e in ("roteiro", "visao", "editar") if d.get(e)]
    print(f"{'modelo':40} " + " ".join(f"{e:>8}" for e in etapas) + "   custo")
    for m in MODELOS:
        print(f"{m:40} " + " ".join(f"{(pontos(d, e, m) if pontos(d, e, m) is not None else '-'):>8}" for e in etapas)
              + f"   {CUSTO[m]}")
    escolha = {}
    for e in etapas:
        cand = [m for m in MODELOS if pontos(d, e, m) is not None]
        escolha[e] = max(cand, key=lambda m: (pontos(d, e, m), -ORDEM_CUSTO[CUSTO[m]]))
    unico = len(set(escolha.values())) == 1
    print("\nmelhor por etapa:", json.dumps(escolha, indent=1))
    print("UM MODELO GANHOU EM TUDO -> usar só ele" if unico else "misturar: cada etapa com o seu melhor")
    d["escolha"] = escolha
    _gravar(d)
    return escolha


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for a in sys.argv[1:] or ["resultado"]:
        {"roteiro": avaliar_roteiro, "visao": avaliar_visao, "editar": avaliar_editar, "resultado": resultado}[a]()
