from loja.precos import aplicar_desconto
from loja.carrinho import Carrinho

assert aplicar_desconto(200, 10) == 180.0, aplicar_desconto(200, 10)
k = Carrinho(); k.adicionar("a", 10, 3)
assert k.subtotal() == 30, k.subtotal()
assert k.total() == 45.0, k.total()
k = Carrinho(); k.adicionar("a", 60, 2); k.aplicar_cupom("DEZ")
assert k.total() == 108.0, k.total()
print("TODOS OS TESTES PASSARAM")
