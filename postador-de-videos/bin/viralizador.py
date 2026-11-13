"""viralizador.py — reescreve a NARRAÇÃO falada antes do TTS (T1, porte do CENSOR CIRÚRGICO n8n).

Duas camadas:
  anti_ban(texto)  — SEMPRE on: suaviza termos que dão strike no YouTube, sem mudar o sentido.
  viralizar(texto) — flag VIRAL_SLANG=1: gírias gen-z SEGURAS e pontuais (não mexe em
                     pronome/sujeito; as agressivas do n8n foram deixadas de fora de propósito).

Fonte da verdade: nó CENSOR CIRÚRGICO de fabrica-de-animes-1. Regex case-insensitive.
Aplicado em _tts_filter.clean_for_tts → áudio e legenda batem (ambos passam aqui).
"""
import os
import re

# (regex, substituição) — anti-ban. Ordem: específico antes de genérico.
_ANTI_BAN = [
    (r"18\s*(\+|mais)", "conteúdo maduro"),
    (r"hentai|ecchi|porn[oô]", "anime de cultura"),
    (r"proibid[oa] para menores", "exclusivo para adultos"),
    (r"estupr[oa]|abus[oa] sexual", "forçar a barra"),
    (r"incesto", "tabu familiar"),
    (r"nudes|nudez|pelad[oa]|\bnua\b", "sem roupa"),
    (r"fanservice", "agrado visual"),
    (r"boquete", "serviço especial"),
    (r"\bsexo\b|coito", "o momento íntimo"),
    (r"transar|trepar", "ficar junto"),
    (r"foder", "amar intensamente"),
    (r"gozar|ejacula[rçã]", "finalizar"),
    (r"buceta|vagina|xereca|ppk|xana", "flor"),
    (r"\bpinto\b|\bpau\b|\brola\b|p[eê]nis|piroca", "instrumento"),
    (r"mamilos|tetas|peitos", "comissão de frente"),
    (r"bunda|raba|nádegas", "traseiro"),
    (r"orgasmo", "clímax"),
    (r"masturba", "amor próprio"),
    (r"suic[íi]dio|se matar", "ir de base"),
    (r"assassin\w*|\bmat(ar|ou|aram|ando|a)\b|\bmorrer\b|\bmorreu\b|\bmort[oa]s?\b", "desviver"),
    (r"degola[rçã]|decapita[rçã]", "perder a cabeça"),
    (r"sangue", "suco de tomate"),
    (r"sangra[r]", "vazar suco"),
    (r"tortura[r]", "interrogação intensa"),
    (r"escrav[oa]|escravidão", "servo"),
    (r"drogas|cocaína|heroína|maconha", "aditivos proibidos"),
    (r"pedófil[oa]|pedofilia", "criminoso"),
    (r"traficante", "comerciante ilegal"),
    (r"caralho", "caramba"),
    (r"porra", "poxa"),
    (r"\bputa\b", "dama"),
    (r"merda", "droga"),
]

# (regex, substituição) — gírias virais SEGURAS (não mexem em pronome/sujeito).
_VIRAL = [
    (r"\bestudar\b|\bestudo\b", "upar"),
    (r"\bprova\b|\bteste\b", "o boss final"),
    (r"\bchefe\b|\bpatrão\b|\bpatrao\b", "o admin"),
    (r"\bdinheiro\b|\bsalário\b|\bsalario\b", "o gold"),
    (r"\btrabalho\b|\bemprego\b", "o grind"),
    (r"\bincrível\b|\bincrivel\b", "insano"),
    (r"\bvergonha\b", "cringe"),
    (r"\braiva\b|\bfúria\b|\bfuria\b", "tiltou"),
    (r"\bvenceu\b|\bganhou\b", "solou"),
    (r"\bperdeu\b", "foi de base"),
]

_ANTI_BAN_C = [(re.compile(r, re.IGNORECASE), s) for r, s in _ANTI_BAN]
_VIRAL_C = [(re.compile(r, re.IGNORECASE), s) for r, s in _VIRAL]


def anti_ban(texto):
    """Suaviza termos de strike. SEMPRE aplicado. Não muda o sentido da história."""
    if not texto:
        return texto
    for rgx, sub in _ANTI_BAN_C:
        texto = rgx.sub(sub, texto)
    return texto


def viralizar(texto):
    """Gírias gen-z seguras. Só com VIRAL_SLANG=1 (decisão do caller)."""
    if not texto:
        return texto
    for rgx, sub in _VIRAL_C:
        texto = rgx.sub(sub, texto)
    return texto


if __name__ == "__main__":
    casos = [
        "ele matou o vilão e saiu muito sangue",
        "cena de nudez proibida para menores",
        "ele vai estudar pra prova e ganhar dinheiro",
        "que porra é essa, caralho",
    ]
    for c in casos:
        ab = anti_ban(c)
        vr = viralizar(ab)
        print(f"IN : {c}")
        print(f"AB : {ab}")
        print(f"VIR: {vr}\n")
