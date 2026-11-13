def por_canal(videos):
    """{canal: {"videos": n, "segundos": total}}"""
    saida = {}
    for v in videos:
        canal = v["canal"].strip().lower()
        d = saida.setdefault(canal, {"videos": 0, "segundos": 0})
        d["videos"] += 1
        d["segundos"] += v["segundos"]
    return saida
