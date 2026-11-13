def media_movel(valores, janela):
    """Média móvel simples: uma média para cada posição onde a janela inteira cabe."""
    saida = []
    for i in range(len(valores) - janela + 1):
        saida.append(sum(valores[i:i + janela]) / janela)
    return saida


def mediana(valores):
    v = sorted(valores)
    meio = len(v) // 2
    if len(v) % 2:
        return v[meio]
    return (v[meio] + v[meio - 1]) / 2
