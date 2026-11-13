import re

with open("D:/recapd-ambientes/producao/bin/anime_discover.py", "r", encoding="utf-8") as f:
    codigo = f.read()

# Precisamos dropar qualquer coisa que for 16:9 DE IMEDIATO no modo Short, sem fallback de reframe para lixo!
func_nova = """
    verticais = []
    horizontais = []
    for r in pool:
        if len(verticais) >= top:
            break 
        ar = _aspect_ratio_remote(r["url"])
        if ar is None:
            logging.info(f"[discover_shorts] orientação indefinida (mantido): {r['title'][:50]}")
            r["aspect_ratio"] = None
            verticais.append(r)
            continue
        if ar < ratio_max:
            logging.info(f"[discover_shorts] VERTICAL prioritário (ar={ar:.2f}): {r['title'][:50]}")
            r["aspect_ratio"] = ar
            verticais.append(r)
        else:
            logging.info(f"[discover_shorts] DESCARTADO candidato horizontal que invadiu os shorts (ar={ar:.2f}): {r['title'][:50]}")
            
    # Retorna APENAS os verticais encontrados! O fallback burro para horizontal estragava o pipeline
    return verticais[:top]
"""

codigo = re.sub(r'    verticais = \[.*return final_pool\[:top\]', func_nova, codigo, flags=re.DOTALL)

with open("D:/recapd-ambientes/producao/bin/anime_discover.py", "w", encoding="utf-8") as f:
    f.write(codigo)
