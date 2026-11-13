"""Métricas públicas do YouTube sem navegador."""
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
        if "," in num:
            clean_num = num.replace(".", "").replace(",", ".")
        elif "." in num:
            clean_num = num.replace(",", "")
        else:
            clean_num = num
        return int(float(clean_num) * {"mil": 1000, "k": 1000, "mi": 10**6, "m": 10**6,
                                       "bi": 10**9, "b": 10**9}[mult])
    return int(re.sub(r"[.,]", "", num))


def resumo_canal(textos):
    """{'inscritos': '3,4 mi de inscritos', 'videos': '812 vídeos', 'views': '...'} -> números"""
    return {k: _numero(v) for k, v in textos.items()}


if __name__ == "__main__":
    testes = {
        "3,4 mi de inscritos": 3400000,
        "2.3M views": 2300000,
        "1,2 mil visualizações": 1200,
        "12.345 visualizações": 12345,
        "1,234 visualizações": 1234,
        "5M": 5000000,
        "10k": 10000,
    }
    for txt, esperado in testes.items():
        res = _numero(txt)
        print(f"'{txt}' -> {res} (esperado: {esperado})")
        assert res == esperado, f"Erro em '{txt}': obtido {res}, esperado {esperado}"
    print("Todos os testes passaram com sucesso!")
