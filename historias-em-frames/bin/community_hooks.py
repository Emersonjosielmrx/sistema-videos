# -*- coding: utf-8 -*-
"""community_hooks.py - Hooks de engajamento (perguntas, polls, pin comments).

Gera conteudo interativo contextual baseado no roteiro:
- Hook visual no meio do video (pergunta overlay)
- Poll pra descricao do YouTube
- Pin comment pra fixar
- Hook de abertura pra Shorts (teaser impactante)
"""
import os
import sys
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log

HOOK_TEMPLATES = {
    "superacao": [
        "Voce teria coragem de fazer isso?",
        "Ja passou por algo parecido?",
        "Achou que ele ia desistir?",
        "O que voce faria no lugar dele?",
    ],
    "terror": [
        "Voce abriria a porta?",
        "Ja sentiu isso de madrugada?",
        "Voce ficaria ou fugiria?",
        "O que tem atras de voce agora?",
    ],
    "misterio": [
        "Ja descobriu quem fez?",
        "Qual e a sua teoria?",
        "Voce percebeu a pista?",
        "Acertou o culpado?",
    ],
    "romance": [
        "Voce perdoaria?",
        "Ja se apaixonou assim?",
        "Ele deveria ter ido atras dela?",
        "Qual final voce queria?",
    ],
    "comedia": [
        "Ja aconteceu com voce?",
        "Qual foi a pior gafe que voce ja passou?",
        "Voce riria ou choraria?",
        "Quem aqui ja fez isso?",
    ],
    "motivacional": [
        "O que te impede hoje?",
        "Voce esta pronto pra mudar?",
        "Qual desculpa voce vai parar de usar?",
        "Comenta seu objetivo aqui embaixo.",
    ],
    "drama": [
        "Voce faria a mesma escolha?",
        "Ele estava certo ou errado?",
        "O que voce sacrificaria?",
        "Ja passou por uma decisao assim?",
    ],
    "fantasia": [
        "Qual poder voce escolheria?",
        "Voce confiaria nele?",
        "Como voce derrotaria o vilao?",
        "Qual personagem voce seria?",
    ],
}

POLL_TEMPLATES = {
    "superacao": {"pergunta": "Voce acredita que qualquer pessoa pode mudar de vida?", "opcoes": ["Sim, com esforco", "Depende das circunstancias", "Quase impossivel"]},
    "terror": {"pergunta": "O que voce faria?", "opcoes": ["Fugiria", "Investigaria", "Chamaria a policia"]},
    "misterio": {"pergunta": "Quem voce acha que e o culpado?", "opcoes": ["O amigo proximo", "O estranho", "Ninguem esperava"]},
    "romance": {"pergunta": "Qual final voce prefere?", "opcoes": ["Ficam juntos", "Seguem caminhos separados", "Final aberto"]},
}


def generate_mid_hook(cenas, genero="superacao", position_frac=0.5):
    """Gera texto de hook pra inserir no meio do video.

    Args:
        cenas: lista de cenas do roteiro
        genero: genero da historia
        position_frac: onde inserir (0.5 = metade)

    Returns:
        dict com texto, posicao (indice da cena), duracao
    """
    templates = HOOK_TEMPLATES.get(genero, HOOK_TEMPLATES["superacao"])
    n_cenas = len(cenas)
    pos_idx = int(n_cenas * position_frac)

    text_hash = hashlib.md5("".join(c.get("texto", "")[:20] for c in cenas).encode()).hexdigest()
    hook_idx = int(text_hash[:4], 16) % len(templates)

    return {
        "texto": templates[hook_idx],
        "position_idx": pos_idx,
        "duration_s": 2.5,
        "style": "bold_overlay",
    }


def generate_shorts_hook(cenas, genero="superacao"):
    """Gera hook de abertura pra Shorts (2s de teaser).

    Seleciona a frase mais impactante do roteiro pra usar como gancho.
    """
    best_text = ""
    best_score = 0

    POWER_WORDS = ("nunca", "morte", "sangue", "segredo", "mentira", "traiu",
                   "destruiu", "impossivel", "chocante", "inacreditavel",
                   "ninguem", "jamais", "perigo", "verdade", "revelou")

    for cena in cenas:
        texto = cena.get("texto", "")
        score = sum(1 for w in POWER_WORDS if w in texto.lower())
        if "!" in texto:
            score += 1
        if "?" in texto:
            score += 0.5
        if len(texto) < 60:
            score += 1
        if score > best_score:
            best_score = score
            best_text = texto

    if not best_text and cenas:
        best_text = cenas[0].get("texto", "Voce nao vai acreditar...")

    if len(best_text) > 80:
        best_text = best_text[:77] + "..."

    return {
        "hook_text": best_text.upper(),
        "duration_s": 2.0,
        "transition": "... 10 minutos antes ...",
    }


def generate_poll(genero="superacao", cenas=None):
    """Gera poll pra descricao do YouTube."""
    base = POLL_TEMPLATES.get(genero, POLL_TEMPLATES["superacao"])
    opcoes_str = "\n".join(f"{chr(65+i)}) {o}" for i, o in enumerate(base["opcoes"]))
    return {
        "pergunta": base["pergunta"],
        "opcoes": base["opcoes"],
        "format_youtube": f"ENQUETE: {base['pergunta']}\n{opcoes_str}",
    }


def generate_pin_comment(cenas, genero="superacao"):
    """Gera texto do comentario fixado."""
    templates = HOOK_TEMPLATES.get(genero, HOOK_TEMPLATES["superacao"])
    text_hash = hashlib.md5("".join(c.get("texto", "")[:10] for c in cenas).encode()).hexdigest()
    idx = int(text_hash[:4], 16) % len(templates)
    base = templates[idx]
    return f"{base} Comenta aqui embaixo! (fixado pelo canal)"
