from loja.precos import aplicar_desconto


class Carrinho:
    def __init__(self):
        self.itens = []  # (nome, preco, qtd)

    def adicionar(self, nome, preco, qtd=1):
        self.itens.append((nome, preco, qtd))

    def subtotal(self):
        return round(sum(preco for _, preco, _ in self.itens), 2)

    def total(self):
        return self.subtotal()
