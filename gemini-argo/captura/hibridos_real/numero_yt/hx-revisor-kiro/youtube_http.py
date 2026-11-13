"""Métricas públicas do YouTube sem navegador (trecho)."""
import re


def _numero(txt):
    """'1,2 mil visualizações' / '3,4 mi de inscritos' / '12.345 visualizações' / '2.3M views' -> int."""
    if not txt:
        return None
    t = txt.lower().replace("\xa0", " ")
    m = re.search(r"([\d.,]+)\s*(mil|mi|bi|k|m|b)?", t)
    if not m:
        return 0 if re.search(r"\b(nenhum|sem)", t) else None
    num, mult = m.group(1), m.group(2)
    if mult:
        # Com multiplicador: determina o separador decimal pelo contexto
        # Se tem vírgula e ponto, ou só vírgula com até 3 dígitos depois → vírgula é decimal (pt-BR)
        # Se tem só ponto com até 3 dígitos depois → ponto é decimal (en)
        if "," in num and "." in num:
            # Formato misto: o último é decimal (ex: 1.234,5 ou 1,234.5)
            if num.rindex(",") > num.rindex("."):
                # vírgula depois: formato pt-BR (1.234,5)
                num_float = num.replace(".", "").replace(",", ".")
            else:
                # ponto depois: formato en (1,234.5)
                num_float = num.replace(",", "")
        elif "," in num:
            # Só vírgula: se tem poucos dígitos depois, é decimal (3,4 mi)
            parts = num.split(",")
            if len(parts) == 2 and len(parts[1]) <= 3 and len(parts[0]) <= 3:
                num_float = num.replace(",", ".")
            else:
                num_float = num.replace(",", "")
        elif "." in num:
            # Só ponto: se tem poucos dígitos depois, é decimal (2.3M)
            parts = num.split(".")
            if len(parts) == 2 and len(parts[1]) <= 3 and len(parts[0]) <= 3:
                num_float = num  # já está com ponto decimal
            else:
                num_float = num.replace(".", "")
        else:
            num_float = num
        return int(float(num_float) * {"mil": 1000, "k": 1000, "mi": 10**6, "m": 10**6,
                                       "bi": 10**9, "b": 10**9}[mult])
    return int(re.sub(r"[.,]", "", num))


def resumo_canal(textos):
    """{'inscritos': '3,4 mi de inscritos', 'videos': '812 vídeos', 'views': '...'} -> números"""
    return {k: _numero(v) for k, v in textos.items()}
