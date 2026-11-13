"""Métricas públicas do YouTube sem navegador (trecho)."""
import re


def _numero(txt):
    """'1,2 mil visualizações' / '3,4 mi de inscritos' / '12.345 visualizações' / '2.3M views' -> int."""
    if not txt:
        return None
    t = txt.lower().replace("\xa0", " ")
    # Aceita multiplicador sem número (ex: 'mil' sozinho = 1 mil)
    m = re.search(r"([\d.,]+)?\s*(mil|mi|bi|k|m|b)", t)
    if not m:
        # Se não tem multiplicador, tenta só o número
        m_num = re.search(r"[\d.,]+", t)
        if m_num:
            return int(re.sub(r"[.,]", "", m_num.group()))
        return 0 if re.search(r"\b(nenhum|sem)", t) else None

    num, mult = m.group(1), m.group(2)
    if not num:
        num = "1"  # 'mil' sozinho = 1000

    # Detecta formato: se tem vírgula, assume pt-BR (vírgula=decimal, ponto=milhar)
    # senão assume EN (ponto=decimal)
    if "," in num:
        # Formato pt-BR: 3,4 mi → 3.4
        num_float = float(num.replace(".", "").replace(",", "."))
    else:
        # Formato EN: 2.3M → 2.3, ou sem decimal: 23M → 23
        num_float = float(num)

    multiplicadores = {"mil": 1000, "k": 1000, "mi": 10**6, "m": 10**6, "bi": 10**9, "b": 10**9}
    return int(num_float * multiplicadores[mult])


def resumo_canal(textos):
    """{'inscritos': '3,4 mi de inscritos', 'videos': '812 vídeos', 'views': '...'} -> números"""
    return {k: _numero(v) for k, v in textos.items()}
