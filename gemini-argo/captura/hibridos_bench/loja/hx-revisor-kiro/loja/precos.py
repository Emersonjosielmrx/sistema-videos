FRETE = 15.0
FRETE_GRATIS_A_PARTIR = 100.0


def aplicar_desconto(preco, pct):
    """Preço depois de tirar pct por cento, arredondado em 2 casas."""
    return round(preco - (preco * pct / 100), 2)
