import json,re
d=json.load(open('fameswap_det.json',encoding='utf-8'))
for u,tx in d.items():
    subs=re.search(r'(\d[\d,.]+K?)\s*\n\s*Price',tx)
    cat=re.search(r'Category\s*\n\s*(.+)',tx)
    mon='Monetized' in tx
    rev=re.search(r'\$(\d[\d,.]*)\s*\n\s*Monthly Revenue',tx)
    age=re.search(r'([A-Z][a-z]+ \d{4})\s*\n\s*Channel Age',tx)
    sel=re.search(r'Seller\s*\n\s*(.+)',tx)
    esc='Escrow accepted' in tx
    num=u.split('/')[-1].split('-')[0]
    print(f"{num}\t{subs and subs.group(1)}\t{'MON' if mon else ''}\t{rev and rev.group(1)}\t{age and age.group(1)}\t{cat and cat.group(1)}\t{'ESC' if esc else ''}\t{sel and sel.group(1)}")
