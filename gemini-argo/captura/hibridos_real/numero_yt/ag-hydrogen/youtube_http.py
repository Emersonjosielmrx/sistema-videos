"""Métricas públicas do YouTube sem navegador (trecho)."""
from decimal import Decimal
import re

_MULTIPLICADORES = {
    "mil": 1000,
    "k": 1000,
    "mi": 10**6,
    "milhão": 10**6,
    "milhões": 10**6,
    "milhao": 10**6,
    "milhoes": 10**6,
    "m": 10**6,
    "bi": 10**9,
    "bilhão": 10**9,
    "bilhões": 10**9,
    "bilhao": 10**9,
    "bilhoes": 10**9,
    "b": 10**9,
}

_MULT_PT = {"mil", "mi", "milhão", "milhões", "milhao", "milhoes", "bi", "bilhão", "bilhões", "bilhao", "bilhoes"}


def _normalizar_decimal(num, mult):
    if "." in num and "," in num:
        dec_sep = "." if num.rfind(".") > num.rfind(",") else ","
        mil_sep = "," if dec_sep == "." else "."
        if num.count(dec_sep) == 1:
            return num.replace(mil_sep, "").replace(dec_sep, ".")
        return re.sub(r"[.,]", "", num)

    sep = "." if "." in num else ("," if "," in num else None)
    if not sep:
        return num
    if num.count(sep) > 1:
        return num.replace(sep, "")

    inteiro, frac = num.split(sep)
    if len(frac) != 3 or inteiro == "0":
        return num.replace(sep, ".")

    # 3 dígitos após separador único: '.' é milhar em PT e decimal em EN; ',' é o inverso
    sep_decimal_esperado = "," if mult in _MULT_PT else "."
    if sep == sep_decimal_esperado:
        return num.replace(sep, ".")
    return num.replace(sep, "")


def _numero(txt):
    """'1,2 mil visualizações' / '3,4 mi de inscritos' / '12.345 visualizações' / '2.3M views' -> int."""
    if not txt:
        return None
    t = txt.lower().replace("\xa0", " ")
    m = re.search(r"(\d+(?:[.,]\d+)*)(?:\s*(milh(?:ão|ões|ao|oes)|bilh(?:ão|ões|ao|oes)|mil|mi|bi|k|m|b)\b)?", t)
    if not m:
        return 0 if re.search(r"\b(nenhum|sem)", t) else None
    num, mult = m.group(1), m.group(2)
    if mult:
        return int(Decimal(_normalizar_decimal(num, mult)) * _MULTIPLICADORES[mult])
    return int(re.sub(r"[.,]", "", num))


def resumo_canal(textos):
    """{'inscritos': '3,4 mi de inscritos', 'videos': '812 vídeos', 'views': '...'} -> números"""
    return {k: _numero(v) for k, v in textos.items()}
