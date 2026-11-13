#!/usr/bin/env python3
"""postagem_meta.py — Gera TÍTULO, DESCRIÇÃO e TAGS virais (com anti-ban) pro YouTube.

Usado por montar-fila.py (constrói a fila de postagem) e serve de referência.
Duas famílias: SHORT (vídeo cortado vertical) e COMPLETO (capítulo inteiro).

Anti-ban: troca termos que dão strike no YouTube ANTES de virar título/descrição.
"""
import re

# ---- Anti-ban (mesma lógica do viralizador, aplicada em título/descrição) ----
_ANTI_BAN = [
    (r"18\s*\+", "conteúdo maduro"),
    (r"hentai|ecchi|porn[oô]", "anime de cultura"),
    (r"nudes|nudez|\bpelad[oa]\b|\bnua\b", "sem roupa"),
    (r"\bsexo\b|coito", "o momento"),
    (r"mamilos|tetas|peitos", "comissão"),
    (r"bunda|raba|nádegas", "traseiro"),
    (r"\bpinto\b|\bpau\b|\brola\b|p[eê]nis|piroca", "instrumento"),
    (r"buceta|vagina|xereca|ppk|xana", "flor"),
    (r"orgasmo", "clímax"),
    (r"assassin\w+|\bmatar\b|\bmorte\b|\bmorreu\b", "desviver"),
    (r"sangue", "suco de tomate"),
    (r"suicídio|se matar", "ir de base"),
]
_ANTI_BAN_C = [(re.compile(p, re.IGNORECASE), s) for p, s in _ANTI_BAN]

# ---- Ganchos virais rotativos (por parte/capítulo) ----
HOOKS = [
    "ELE FEZ O QUÊ?! 😱",
    "ISSO É INSANO 🔥",
    "NÃO ACREDITO NO QUE ACONTECEU 😭",
    "TODO MUNDO ESTÁ FALANDO DESSE MANHWA 👀",
    "POR QUE NINGUÉM ME CONTOU SOBRE ISSO 🤯",
    "O FINAL DESSE CAP VAI TE CHOCAR 💀",
    "ESSE MANHWA É VICIANTE 🫀",
    "EU PRECISEI PAUSAR AQUI 😤",
    "A CENA MAIS INSANA DO MANHWA 🔥",
    "NÃO ERA PRA GOSTAR TANTO ASSIM 😭",
]

TAGS_BASE = [
    "manhwa", "manhwabr", "recap manhwa", "manhwa recap", "webtoon",
    "romance coreano", "drama coreano", "shorts", "manhwa shorts",
    "anime br", "mangá recap", "manhwa brasil", "manhwa portugues",
    "webtoon br", "coreia", "manhwa em português",
]


def anti_ban(texto):
    for rgx, sub in _ANTI_BAN_C:
        texto = rgx.sub(sub, texto)
    return texto


def _slug(obra):
    return re.sub(r"[^a-zA-Z0-9]", "", obra)


# ---------------------- SHORT ----------------------
def titulo_short(obra, cap, parte, total):
    if parte == total:
        base = f"COMO TERMINA ESSE CAPÍTULO?! 🤯 | {obra.upper()} Cap.{cap} Pt.{parte}/{total} #shorts"
    else:
        hook = HOOKS[(cap + parte) % len(HOOKS)]
        base = f"{hook} | {obra.upper()} Cap.{cap} Pt.{parte}/{total} #shorts"
    return anti_ban(base[:100])


def descricao_short(obra, cap, parte, total):
    if parte < total:
        continua = f"➡️ PARTE {parte + 1} NO MEU PERFIL! Segue pra não perder!"
    else:
        continua = "✅ FIM DO CAPÍTULO! Próximo cap em breve no perfil."
    desc = (
        f"📖 {obra} — Capítulo {cap}, Parte {parte} de {total}\n"
        f"{continua}\n\n"
        f"🔥 Segue o perfil pra não perder nenhuma parte!\n"
        f"💬 Comenta o que achou dessa cena!\n"
        f"❤️ Deixa o like se ficou viciado!\n\n"
        f"#{_slug(obra)} #manhwa #manhwabr #recap #webtoon #shorts #animebrasil #romancecoreano"
    )
    return anti_ban(desc[:5000])


# ---------------------- COMPLETO ----------------------
def titulo_completo(obra, cap):
    base = f"{obra.upper()} Cap.{cap} COMPLETO 🔥 Recap Manhwa Dublado PT-BR"
    return anti_ban(base[:100])


def descricao_completo(obra, cap):
    desc = (
        f"📖 {obra} — Capítulo {cap} COMPLETO (recap narrado em português)\n\n"
        f"Assista ao capítulo inteiro desse manhwa coreano de romance e drama, "
        f"com narração dublada e legendas.\n\n"
        f"🔔 INSCREVA-SE e ative o sininho pra não perder os próximos capítulos!\n"
        f"💬 Comenta o que achou!\n"
        f"❤️ Deixa o like!\n\n"
        f"#{_slug(obra)} #manhwa #manhwabr #recap #webtoon #animebrasil "
        f"#romancecoreano #dramacoreano #mangarecap"
    )
    return anti_ban(desc[:5000])


def tags(obra, cap):
    t = list(TAGS_BASE) + [
        obra, f"{obra} cap {cap}", f"{obra} capitulo {cap}",
        _slug(obra), f"cap {cap}", f"capitulo {cap}", "recap completo",
    ]
    return list(dict.fromkeys(t))[:30]


if __name__ == "__main__":
    print("SHORT titulo:", titulo_short("The Meek Cat", 2, 1, 6))
    print("SHORT desc  :", descricao_short("The Meek Cat", 2, 1, 6)[:80], "...")
    print("FULL titulo :", titulo_completo("The Meek Cat", 2))
    print("TAGS        :", tags("The Meek Cat", 2)[:6], "...")
