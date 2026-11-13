"""Métricas públicas do YouTube sem navegador (trecho)."""
import re
from decimal import Decimal


_MULT = {
    "mil": 10**3,
    "k": 10**3,
    "mi": 10**6,
    "m": 10**6,
    "bi": 10**9,
    "b": 10**9,
}


def _numero(txt):
    """'1,2 mil visualizações' / '3,4 mi de inscritos' / '12.345 visualizações' / '2.3M views' -> int."""
    if not txt:
        return None
    t = txt.lower().replace("\xa0", " ")
    m = re.search(r"(\d[\d.,]*)\s*(?:(mil|mi|bi|k|m|b)\b)?", t)
    if not m:
        return 0 if re.search(r"\b(nenhum|sem)", t) else None
    num, mult = m.group(1), m.group(2)
    if mult:
        # Se houver tanto '.' quanto ',', o último é o separador decimal
        if "." in num and "," in num:
            if num.rfind(",") > num.rfind("."):
                num_clean = num.replace(".", "").replace(",", ".")
            else:
                num_clean = num.replace(",", "")
        else:
            # Com sufixo (ex: '3,4 mi' ou '2.3M'), ',' ou '.' único é separador decimal
            num_clean = num.replace(",", ".")
        return int(Decimal(num_clean) * _MULT[mult])
    return int(re.sub(r"[.,]", "", num))


def resumo_canal(textos):
    """{'inscritos': '3,4 mi de inscritos', 'videos': '812 vídeos', 'views': '...'} -> números"""
    return {k: _numero(v) for k, v in textos.items()}
