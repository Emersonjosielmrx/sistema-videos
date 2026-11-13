# -*- coding: utf-8 -*-
"""falantes.py — revisa QUEM FALA cada fala do roteiro (persona/gênero) depois do gerar_recap.

Por quê: a visão olha um painel por vez; quando a seta do balão aponta pra fora do quadro (quem fala
não aparece), ela chuta o personagem visível e a voz sai trocada (pergunta dele na voz dela).
Aqui um LLM lê o DIÁLOGO INTEIRO em sequência e só corrige onde a conversa exige (pergunta e
resposta na mesma boca, pessoa falando de si no feminino com voz de homem...). Também uma regra fixa
e segura: "obrigada"/"obrigado", "eu mesma"/"eu mesmo" dizem o gênero de quem fala.

Voltar atrás: HIPER_REVISAR_FALANTES=0 desliga tudo. Toda fala trocada guarda persona_orig/gender_orig
no cache do roteiro; restaurar(locucoes) desfaz. Roda só quando o roteiro é gerado (capítulo novo).

Teste de 14/10 no cap 2 (The Inheritor): o LLM propôs 3 trocas e 2 estavam ERRADAS (deu "Obrigada por
me esperar" pro rapaz) e não achou o erro real ("Ele faleceu, né?" na voz dela). Por isso a parte do
LLM fica DESLIGADA (HIPER_FALANTES_LLM=1 liga pra testar); só a regra fixa das marcas roda.
"""
import json
import os
import re

from hp_common import log

LIGADO = os.environ.get("HIPER_REVISAR_FALANTES", "1") != "0"
LLM_LIGADO = os.environ.get("HIPER_FALANTES_LLM", "0") == "1"
MAX_TROCAS = 0.15  # mais que isso numa revisão = o LLM se perdeu; descarta tudo
NARRADOR = ("narrador", "narradora", "narrator")
_ADJ = (r"(cansad|preocupad|sozinh|nervos|assustad|apaixonad|pront|presunços|envergonhad|confus|ocupad|"
        r"perdid|machucad|chatead|animad|surpres|obrigad)")
_EU = r"\b(?:estou|tô|to|sou|fiquei|estava|me sinto|querer ser)\s+(?:muito\s+|tão\s+|meio\s+|um pouco\s+)?"
MARCA_F = re.compile(rf"\b(obrigada|eu mesma)\b|{_EU}{_ADJ}a\b", re.I)
MARCA_M = re.compile(rf"\b(obrigado|eu mesmo)\b|{_EU}{_ADJ}o\b", re.I)


def _marca(texto):
    """'F'/'M' se a fala marca o gênero de quem fala (1ª pessoa), senão None (ou se marca os dois)."""
    f, m = bool(MARCA_F.search(texto or "")), bool(MARCA_M.search(texto or ""))
    return "F" if f and not m else ("M" if m and not f else None)

SYSTEM = (
    "Você revisa roteiros de recap de manhwa. Cada linha é uma fala com quem fala (persona e gênero M/F). "
    "A visão que montou o roteiro olhou um painel por vez e às vezes errou QUEM FALA quando o balão "
    "aponta para alguém fora do quadro. Leia o diálogo em sequência e corrija SÓ quando a conversa "
    "deixa claro que foi a outra pessoa: pergunta e resposta saindo da mesma boca, alguém respondendo "
    "a si mesmo, pessoa falando de si com gênero errado (obrigada/obrigado, cansada/cansado...), fala "
    "que só faz sentido na boca do outro. Na dúvida, NÃO mude. Falas do Narrador nunca mudam e nenhuma "
    "fala vira Narrador. Use só personagens que já aparecem no roteiro. Não mude o texto.\n"
    'Responda só JSON: {"trocas":[{"i":12,"persona":"Nome","gender":"M","motivo":"curto"}]} '
    '(lista vazia se estiver tudo certo).'
)


def _personagens(locucoes):
    """{nome: gênero} dos personagens (não narrador), com o gênero mais usado pra cada nome."""
    cont = {}
    for l in locucoes:
        p = (l.get("persona") or "").strip()
        if p and p.lower() not in NARRADOR and l.get("gender") in ("M", "F"):
            cont.setdefault(p, {}).setdefault(l["gender"], 0)
            cont[p][l["gender"]] += 1
    return {p: max(g, key=g.get) for p, g in cont.items()}


def _trocar(loc, persona, gender, motivo):
    loc.setdefault("persona_orig", loc.get("persona"))
    loc.setdefault("gender_orig", loc.get("gender"))
    loc["persona"], loc["gender"], loc["_falante_motivo"] = persona, gender, motivo


def _regra_fixa(locucoes, nomes):
    """Marca de gênero em 1ª pessoa contra o gênero da voz -> o personagem do outro gênero que está
    falando por perto (±6 falas), se houver exatamente um."""
    n = 0
    for k, l in enumerate(locucoes):
        p = (l.get("persona") or "").lower()
        if p in NARRADOR:
            continue
        quer = _marca(l.get("text", ""))
        if not quer or l.get("gender") == quer:
            continue
        perto = {(x.get("persona") or "").strip() for x in locucoes[max(0, k - 6):k + 7]}
        cands = [c for c in perto if nomes.get(c) == quer]
        if len(cands) == 1:
            _trocar(l, cands[0], quer, f"marca de gênero: {quer}")
            n += 1
    return n


def _pedir_llm(texto):
    try:
        import claude_client
        r = claude_client.perguntar(texto, system=SYSTEM, max_tokens=3000, temperature=0.2)
        if r:
            return r
    except Exception as e:  # noqa: BLE001
        log(f"  [falantes] Claude falhou ({str(e)[:80]})")
    try:
        import gemini_llm
        return gemini_llm.generate_text(texto, system=SYSTEM, max_tokens=3000, temperature=0.2, max_attempts=3)
    except Exception as e:  # noqa: BLE001
        log(f"  [falantes] Gemini falhou ({str(e)[:80]})")
        return None


def revisar(locucoes, descriptions=()):
    """Corrige persona/gênero no lugar (lista de locuções do gerar_recap). Retorna nº de trocas."""
    if not LIGADO or not locucoes:
        return 0
    nomes = _personagens(locucoes)
    if len(nomes) < 2:
        return 0
    validas = _revisar_llm(locucoes, descriptions, nomes) if LLM_LIGADO else []
    for k, p, g, motivo in validas:
        log(f"  [falantes] {k}: {locucoes[k].get('persona')} -> {p} ({motivo}) | {locucoes[k].get('text', '')[:50]}")
        _trocar(locucoes[k], p, g, motivo)
    n_fixa = _regra_fixa(locucoes, nomes)
    log(f"  [falantes] revisão: {len(validas)} troca(s) pelo diálogo (LLM {'ligado' if LLM_LIGADO else 'desligado'})"
        f" + {n_fixa} pela marca de gênero")
    return len(validas) + n_fixa


def _revisar_llm(locucoes, descriptions, nomes):
    """[(i, persona, gênero, motivo)] das trocas que o LLM propôs e passaram nas checagens."""
    linhas = []
    for k, l in enumerate(locucoes):
        cena = (descriptions[k] if k < len(descriptions) else "")[:90]
        linhas.append(f"{k} | {l.get('persona')} ({l.get('gender')}) | {l.get('text', '')}"
                      + (f" | cena: {cena}" if cena else ""))
    texto = ("Personagens: " + ", ".join(f"{p} ({g})" for p, g in nomes.items())
             + "\n\nRoteiro (índice | quem fala | fala | cena):\n" + "\n".join(linhas))
    trocas = []
    resp = _pedir_llm(texto)
    if resp:
        m = re.search(r"\{.*\}", resp, re.S)
        try:
            trocas = json.loads(m.group(0)).get("trocas", []) if m else []
        except (ValueError, AttributeError):
            trocas = []
    validas = []
    for t in trocas:
        try:
            k = int(t["i"])
        except (KeyError, TypeError, ValueError):
            continue
        p, g = str(t.get("persona", "")).strip(), t.get("gender")
        if (0 <= k < len(locucoes) and p in nomes and g == nomes[p]
                and (locucoes[k].get("persona") or "").lower() not in NARRADOR
                and p != locucoes[k].get("persona")
                and _marca(locucoes[k].get("text", "")) in (None, g)):  # nunca contra "obrigada/obrigado"
            validas.append((k, p, g, str(t.get("motivo", ""))[:80]))
    falas = sum(1 for l in locucoes if (l.get("persona") or "").lower() not in NARRADOR)
    if len(validas) > MAX_TROCAS * max(1, falas):
        log(f"  [falantes] LLM quis trocar {len(validas)} de {falas} falas — demais, descartado")
        return []
    return validas


def restaurar(locucoes):
    """Desfaz a revisão (volta persona/gênero originais)."""
    for l in locucoes:
        if "persona_orig" in l:
            l["persona"], l["gender"] = l.pop("persona_orig"), l.pop("gender_orig")
            l.pop("_falante_motivo", None)
    return locucoes
