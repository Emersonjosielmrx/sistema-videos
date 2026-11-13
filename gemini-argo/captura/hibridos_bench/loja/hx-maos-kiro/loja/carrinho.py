from loja.cupons import CUPONS
from loja.precos import FRETE, FRETE_GRATIS_A_PARTIR, aplicar_desconto


class Carrinho:
    def __init__(self):
        self.itens = []  # (nome, preco, qtd)
        self.desconto_pct = 0

    def adicionar(self, nome, preco, qtd=1):
        self.itens.append((nome, preco, qtd))

    def aplicar_cupom(self, codigo):
        chave = codigo.upper()
        if chave not in CUPONS:
            raise ValueError(f"Cupom desconhecido: {codigo}")
        self.desconto_pct = CUPONS[chave]

    def subtotal(self):
        return round(sum(preco * qtd for _, preco, qtd in self.itens), 2)

    def total(self):
        if not self.itens:
            return 0
        valor = aplicar_desconto(self.subtotal(), self.desconto_pct)
        if valor < FRETE_GRATIS_A_PARTIR:
            valor = round(valor + FRETE, 2)
        return valor
