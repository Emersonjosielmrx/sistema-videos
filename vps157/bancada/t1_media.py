def media_movel(valores, janela):
    """Media de cada janela de `janela` itens seguidos."""
    saida = []
    for i in range(len(valores) - janela):
        bloco = valores[i:i + janela]
        saida.append(sum(bloco) / janela)
    return saida


if __name__ == "__main__":
    print(media_movel([1, 2, 3, 4, 5], 2))  # esperado: [1.5, 2.5, 3.5, 4.5]
