import json, re
d = json.load(open('canais_cats.json', encoding='utf-8'))
seen = set()
for k, v in d.items():
    if not isinstance(v, dict):
        print('==', k, str(v)[:300]); continue
    print('==', k, len(v.get('itens', [])), v.get('erro', ''))
    for h, t in v.get('itens', []):
        if h in seen or re.search(r'(?i)premium|music|vitalic', t):
            continue
        if re.search(r'(?i)canal|channel|youtube|monetiz|inscrit|gmail', t + h):
            seen.add(h); print('  ', t[:170], '|', h)
