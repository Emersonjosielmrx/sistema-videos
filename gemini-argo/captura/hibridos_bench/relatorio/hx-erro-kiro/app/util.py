def limpar_titulo(t):
    return " ".join(t.split())


def plural(n, palavra):
    return f"{n} {palavra}" + ("" if n == 1 else "s")
