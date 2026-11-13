"""climas_voz.py — a MESMA voz clonada muda o jeito conforme o clima de cada trecho do vídeo (dono 20/10/2026).

Dono: "a ideia é termos variações da mesma voz no mesmo vídeo pra parecer que o narrador mudou... não usar uma ou
outra e sim todos os tipos possíveis de variações". Narrador humano muda a voz na parte engraçada, na luta (acelera
como gol de futebol), no terror, na fala do vilão — sem deixar de ser a mesma pessoa. O RVC mantém o timbre; aqui
muda base, velocidade, tom (relativo à voz natural), faixa de entonação, volume, pausa, EQ e eco.

Doses testadas em D:\\hipercool-materiais\\teste_vozes_base\\variacoes (gerar_variacoes.py, medidas com RMVPE) e
análise em teste_vozes_base\\VARIACOES_POR_MOMENTO.md. Mulher nunca desce abaixo de 165 Hz (no teste do "antonio"
a voz feminina caiu pra ~80 Hz, faixa de homem, e o dono disse que não combinou).

Segurança: qualquer falha aqui = frase sai como antes (clima "normal" = nenhuma mudança). VOZ_CLIMAS=0 desliga.
"""
import json
import logging
import math
import os
import re
import subprocess
from pathlib import Path

VOZES_RVC = Path(r"D:\hipercool-materiais\models\rvc\vozes")
PISO_MULHER_HZ = 165.0
PISO_HOMEM_HZ = 60.0
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# base: None = a do modo atual (rodízio francisca/kokoro/misto) | rate: % somado | st: semitons (homem, mulher) em
# relação à voz natural | f0: multiplica a faixa de entonação | final: fim de frase (st) | db: volume | pausa: s a
# mais depois da frase | eq: [[Hz, dB]] somado ao do narrador | eco: None/leve/sala
CLIMAS = {
    "normal":    dict(base=None, rate=0, st=(0, 0), f0=1.00, final=None, db=0.0, pausa=0.0, eq=[], eco=None),
    # 01/11 dona: o comentário pessoal do narrador (ironia/opinião, anime_script._COMENTARIO_NARRADOR) sai num tom
    # próprio — mais calmo e de conversa, como quem pausa a leitura pra falar com o amigo; pausa depois pra voltar
    "comentario": dict(base="francisca", rate=-6, st=(0, 0), f0=0.92, final=-0.3, db=0.0, pausa=0.35,
                       eq=[[250, 1.0], [2500, 1.0]], eco=None),
    "engracado": dict(base="francisca", rate=8, st=(0, 0), f0=1.25, final=None, db=1.0, pausa=0.0,
                      eq=[[3000, 2.0]], eco=None),
    # 29/10 dona: "baixar muito a voz" e "eco deixa a voz distante como se estivesse num estúdio, atrapalha" —
    # db zerado (volume não muda) e eco tirado de tudo
    "tensao":    dict(base="francisca", rate=-8, st=(-1, -1), f0=0.80, final=-0.5, db=0.0, pausa=0.20,
                      eq=[[6000, -2.0]], eco=None),
    "terror":    dict(base="francisca", rate=-16, st=(-2, -2), f0=0.65, final=-1.0, db=0.0, pausa=0.45,
                      eq=[[180, 1.5], [5000, -3.0], [10000, -5.0]], eco=None),
    "vilao":     dict(base="francisca", rate=-12, st=(-8, -3), f0=0.75, final=-1.2, db=1.0, pausa=0.30,
                      eq=[[140, 2.5], [3000, -1.0]], eco=None),
    "acao":      dict(base="kokoro", rate=0, st=(0, 0), f0=1.15, final=None, db=0.0, pausa=-0.10,
                      eq=[[2500, 1.5]], eco=None),
    "epico":     dict(base="francisca", rate=-6, st=(-1, -1), f0=1.10, final=-0.5, db=2.0, pausa=0.35,
                      eq=[[120, 1.5]], eco=None),
    "triste":    dict(base="francisca", rate=-10, st=(-1, -1), f0=0.85, final=-1.5, db=0.0, pausa=0.30,
                      eq=[[8000, -2.0]], eco=None),
}
ACAO_VEL = (1.00, 1.30)    # luta: cada frase seguida mais rápida (curva quadrática, dispara no fim = o "gol")
ACAO_DB = (0.0, 4.0)
ECO = {"leve": "aecho=0.8:0.6:35|60:0.15|0.10", "sala": "aecho=0.8:0.7:60|110:0.18|0.12"}

_PALAVRAS = {
    "acao": r"\b(lut\w*|golpe\w*|soc\w*|chut\w*|espad\w*|ataq\w*|atac\w*|desvi\w*|pul\w*|avan[cç]\w*|acert\w*|"
            r"explod\w*|explos\w*|batalh\w*|investi\w*|corta\w*|cortou|derrub\w*|arremess\w*|dispar\w*|socou)\b",
    "terror": r"\b(medo|sombr\w*|escur\w*|sangue|cad[aá]ver\w*|assombr\w*|sussurr\w*|arrepi\w*|horr\w*|"
              r"fantasma\w*|maldi[cç]\w*|gelou|congel\w*|tremend\w*|respira\w*|criatura\w*)\b",
    "tensao": r"\b(de repente|sil[eê]ncio|cuidado|perigo\w*|estranh\w*|algo|suspeit\w*|nervos\w*|tens\w*|"
              r"ningu[eé]m sabia|naquela noite)\b",
    "vilao": r"\b(vingan[cç]a|destruir|esmagar|vou te matar|vai morrer|ningu[eé]m vai|meu dom[ií]nio|tolo|verme|"
             r"inseto|riu de forma|sorriso maligno|ajoelh\w*)\b",
    "triste": r"\b(chor\w*|l[aá]grim\w*|morreu|perdeu|sozinh\w*|saudade|despedi\w*|luto|enterr\w*|dor\b|"
              r"nunca mais|sofr\w*)\b",
    "epico": r"\b(sistema|despert\w*|rank|n[ií]vel|lend[aá]ri\w*|evolu\w*|invenc[ií]vel|poder supremo|"
             r"transform\w*|janela azul|habilidade|revel\w*)\b",
    "engracado": r"\b(kkk\w*|haha\w*|rid[ií]cul\w*|vergonh\w*|burr\w*|pat[eé]tic\w*|piada|zoei\w*|"
                 r"tadinho|coitad\w*|mico|vacilo\w*|rapaz|mano|parece piada|pelo amor de deus)\b",
}


def ligado():
    return os.environ.get("VOZ_CLIMAS", "1") != "0"


def _heuristica(linhas):
    climas = []
    for t in linhas:
        tl = t.lower()
        notas = {c: len(re.findall(p, tl)) for c, p in _PALAVRAS.items()}
        if '"' in t or "“" in t or "—" in t[:3]:
            notas["vilao"] += 1 if notas["vilao"] or re.search(r"\b(matar|morrer|meu|minha)\b", tl) else 0
        melhor = max(notas, key=lambda c: notas[c])
        climas.append(melhor if notas[melhor] > 0 else "normal")
    return climas


def _pelo_llm(linhas):
    numeradas = "\n".join(f"{i}: {t}" for i, t in enumerate(linhas))
    nomes = ", ".join(c for c in CLIMAS if c != "comentario")  # comentário é marcado pela abertura, não pelo LLM
    prompt = (f"Abaixo estão as {len(linhas)} frases da narração de um vídeo de resumo (manhwa/anime), numeradas a "
              "partir de 0. Um narrador humano muda o JEITO da voz conforme o clima de cada trecho, sem deixar de ser "
              f"ele. Para cada frase escolha UM clima desta lista: {nomes}. normal = narração comum; engracado = "
              "parte cômica/zoeira; tensao = suspense, algo vai acontecer; terror = medo, horror; vilao = fala ou "
              "ameaça de um vilão/personagem maligno; acao = luta, perseguição, golpes (a voz acelera); epico = "
              "revelação, poder despertando, vitória; triste = perda, choro. Use VÁRIOS climas diferentes ao longo "
              "do vídeo quando o texto permitir, em trechos de 1 a 5 frases. Responda SÓ um JSON: lista com "
              f"{len(linhas)} nomes de clima, na ordem das frases.\n\n{numeradas}")
    import claude_client
    txt = claude_client.generate_text(prompt, max_tokens=40 + 8 * len(linhas), temperature=0.2, timeout=90) or ""
    m = re.search(r"\[[^\]]*\]", txt, re.S)
    lst = json.loads(m.group(0)) if m else []
    lst = [str(x).strip().lower().replace("ç", "c").replace("ã", "a").replace("é", "e") for x in lst]
    if len(lst) == len(linhas) and all(x in CLIMAS for x in lst):
        return lst
    return None


# aberturas que o roteiro usa no comentário pessoal do narrador (anime_script._COMENTARIO_NARRADOR) — a frase que
# começa assim é o narrador falando por ele, não a história
ABRE_COMENTARIO = re.compile(r"^\s*(cá entre nós|ca entre nos|e olha a ironia|olha a ironia|sinceramente|vamos combinar|"
                             r"convenhamos|pra mim|na boa|confesso|imagina só|imagina so|repara que|aqui entre nós|"
                             r"detalhe:|olha só que ironia|eu, hein)\b", re.I)


def eh_comentario(frase):
    return bool(ABRE_COMENTARIO.match(frase or ""))


def escolher(linhas, cache_dir):
    """Clima de cada frase (lista); o comentário pessoal do narrador sempre sai no clima 'comentario'."""
    climas = _escolher(linhas, cache_dir)
    try:
        return ["comentario" if eh_comentario(t) else c for t, c in zip(linhas, climas)]
    except Exception:  # noqa: BLE001
        return climas


def _escolher(linhas, cache_dir):
    """Clima de cada frase (lista). Cache por vídeo; LLM (1 chamada) com reserva por palavra-chave; falhou = normal."""
    n = len(linhas)
    if not ligado() or not n:
        return ["normal"] * n
    cache = Path(cache_dir) / "_climas_voz.json"
    import hashlib
    chave = hashlib.md5("\n".join(linhas).encode("utf-8")).hexdigest()
    try:
        d = json.loads(cache.read_text(encoding="utf-8"))
        if d.get("linhas") == chave and len(d.get("climas", [])) == n:
            return d["climas"]
    except (OSError, ValueError):
        pass
    origem, climas = "llm", None
    try:
        climas = _pelo_llm(linhas)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[climas] LLM falhou ({type(e).__name__}) — palavra-chave")
    if not climas:
        origem = "palavra-chave"
        try:
            climas = _heuristica(linhas)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[climas] heurística falhou ({e}) — tudo normal")
            climas = ["normal"] * n
    try:
        cache.write_text(json.dumps({"linhas": chave, "climas": climas, "origem": origem}, ensure_ascii=False),
                         encoding="utf-8")
    except OSError:
        pass
    contagem = {c: climas.count(c) for c in CLIMAS if climas.count(c)}
    logging.info(f"[climas] ({origem}) {contagem}")
    return climas


def _natural_hz(voz):
    try:
        return float((VOZES_RVC / voz / "f0.txt").read_text().strip())
    except (OSError, ValueError):
        return None


def semitons(voz, clima):
    """Semitons a somar no clone pra este clima; mulher não desce abaixo de 165 Hz, homem de 60 Hz."""
    c = CLIMAS[clima]
    nat = _natural_hz(voz)
    if not nat:
        return 0
    mulher = nat >= PISO_MULHER_HZ
    st = c["st"][1 if mulher else 0]
    alvo = nat * 2 ** (st / 12)
    alvo = max(alvo, PISO_MULHER_HZ if mulher else PISO_HOMEM_HZ)
    return int(round(12 * math.log2(alvo / nat)))


def _run_acao(climas, i):
    """(posição na sequência de luta, tamanho da sequência)."""
    ini = i
    while ini > 0 and climas[ini - 1] == "acao":
        ini -= 1
    fim = i
    while fim + 1 < len(climas) and climas[fim + 1] == "acao":
        fim += 1
    return i - ini, fim - ini + 1


def ajustes(voz, climas, i):
    """O que o clima da frase i muda: dict com base, rate (%), vel (fator Kokoro), st, f0 (fator), final, db, pausa,
    eq, eco. Normal = nada muda."""
    clima = climas[i] if 0 <= i < len(climas) and climas[i] in CLIMAS else "normal"
    c = CLIMAS[clima]
    a = {"clima": clima, "base": c["base"], "rate": c["rate"], "vel": 1 + c["rate"] / 100, "st": semitons(voz, clima),
         "f0": c["f0"], "final": c["final"], "db": c["db"], "pausa": c["pausa"], "eq": c["eq"], "eco": c["eco"]}
    if clima == "acao":
        k, n = _run_acao(climas, i)
        f = (k / (n - 1)) ** 2 if n > 1 else 1.0
        a["vel"] = ACAO_VEL[0] + (ACAO_VEL[1] - ACAO_VEL[0]) * f
        a["rate"] = int(round((a["vel"] - 1) * 100))
        a["db"] = ACAO_DB[0] + (ACAO_DB[1] - ACAO_DB[0]) * f
        if k == n - 1:  # o "gol": +1 st e respiro depois
            a["st"] += 1
            a["pausa"] = 0.45
    return a


def juntar_eq(base, extra):
    d = {}
    for lst in (base or [], extra or []):
        for f, g in lst:
            d[float(f)] = round(d.get(float(f), 0.0) + float(g), 2)
    return [[f, g] for f, g in sorted(d.items())]


def aplicar_eco(wav, eco):
    """31/10 REGRA da dona: voz com eco ("falando de longe") é proibida em todo vídeo, curto ou longo — não faz nada."""
    return

