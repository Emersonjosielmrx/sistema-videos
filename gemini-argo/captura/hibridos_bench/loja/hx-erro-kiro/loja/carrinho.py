from loja.precos import aplicar_desconto, FRETE, FRETE_GRATIS_A_PARTIR
from loja.cupons import CUPONS


class Carrinho:
    def __init__(self):
        self.itens = []  # (nome, preco, qtd)
        self.cupom_desconto = 0  # porcentagem de desconto do cupom

    def adicionar(self, nome, preco, qtd=1):
        self.itens.append((nome, preco, qtd))

    def subtotal(self):
        return round(sum(preco * qtd for _, preco, qtd in self.itens), 2)

    def aplicar_cupom(self, codigo):
        codigo_upper = codigo.upper()
        if codigo_upper not in CUPONS:
            raise ValueError(f"Cupom desconhecido: {codigo}")
        self.cupom_desconto = CUPONS[codigo_upper]

    def total(self):
        if not self.itens:
            return 0

        sub = self.subtotal()
        valor_com_desconto = aplicar_desconto(sub, self.cupom_desconto)

        # Adiciona frete se o valor com desconto for menor que o mínimo para frete grátis
        if valor_com_desconto < FRETE_GRATIS_A_PARTIR:
            return round(valor_com_desconto + FRETE, 2)

        return valor_com_desconto
