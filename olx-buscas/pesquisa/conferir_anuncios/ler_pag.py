import json, re
d = json.load(open('pagamentos.json', encoding='utf-8'))
for u, v in d.items():
    tx = v.get('texto', v.get('erro', ''))
    print('=====', u, '->', v.get('final'))
    if 'basefy' in u:
        for kw in ('Pix', 'PIX', 'cartão', 'Cartão', 'boleto', 'USDT', 'R$', 'vendas', 'Entrega', 'Garantia', 'canal', 'YouTube', 'Youtube'):
            for m in re.finditer(re.escape(kw), tx):
                s = tx[max(0, m.start()-80):m.end()+120].replace('\n', ' ')
                print('  [', kw, ']', s)
                break
    else:
        hits = [m.start() for m in re.finditer(r'(?i)card|visa|mastercard|crypto|usdt|bitcoin|payment|paypal|pix|stripe|wire|bank', tx)]
        printed = -1000
        for h in hits:
            if h - printed > 250:
                print('  ...', tx[max(0, h-120):h+200].replace('\n', ' '))
                printed = h
        if not hits:
            print('  TEXTO:', tx[:600].replace('\n', ' '))
