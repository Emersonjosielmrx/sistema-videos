PREP = 'from loja.precos import aplicar_desconto\nfrom loja.carrinho import Carrinho\ndef c(*itens, cupom=None):\n    k = Carrinho()\n    for it in itens: k.adicionar(*it)\n    if cupom: k.aplicar_cupom(cupom)\n    return k\ndef erro(f):\n    try: f()\n    except ValueError: return True\n    return False\n'
CASOS = ['aplicar_desconto(200, 10) == 180.0', 'aplicar_desconto(19.99, 0) == 19.99', 'aplicar_desconto(50, 100) == 0.0', "c(('a', 10, 3)).subtotal() == 30", "c(('a', 10, 3), ('b', 2.5, 2)).subtotal() == 35.0", "c(('a', 10, 3)).total() == 45.0", "c(('a', 50, 2)).total() == 100.0", "c(('a', 60, 2), cupom='DEZ').total() == 108.0", "c(('a', 100, 1), cupom='vinte').total() == 95.0", 'c().total() == 0', "erro(lambda: c(('a', 1, 1), cupom='XYZ'))", "c(('a', 33.33, 3), cupom='DEZ').total() == 104.99"]
import ast, json, sys, traceback
sys.path.insert(0, ".")
ns = {}
try:
    exec(compile(PREP, "prep", "exec"), ns)
except Exception:
    print(json.dumps({"ok": 0, "falhas": ["prep: " + traceback.format_exc()[-300:]]})); sys.exit()
ok, falhas = 0, []
for c in CASOS:
    try:
        if eval(c, ns): ok += 1
        else: falhas.append(c)
    except Exception as e:
        falhas.append(c + " -> " + type(e).__name__ + ": " + str(e)[:100])
print(json.dumps({"ok": ok, "falhas": falhas}, ensure_ascii=False))
