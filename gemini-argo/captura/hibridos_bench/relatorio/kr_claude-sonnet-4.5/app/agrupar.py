def por_canal(videos):
    """{canal: {"videos": n, "segundos": total}}"""
    saida = {}
    for v in videos:
        d = saida.setdefault(v["canal"], {"videos": 0, "segundos": 0})
        d["videos"] += 1
        d["segundos"] += v["segundos"]
    return saida
