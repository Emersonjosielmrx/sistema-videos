import json, re
d = json.load(open('canais_busca.json', encoding='utf-8'))
rows = []
for i in d['accs']:
    t = i.get('titulo', '')
    if i.get('estoque') in ('0', None) or 'youtube' not in t.lower():
        continue
    m = re.search(r'Price per pc from \$([\d,]+)', t)
    p = float(m.group(1).replace(',', '.')) if m else 99
    ano = re.search(r'Registration date ([^.]+?)\.', t)
    rows.append((p, i['estoque'], ano.group(1) if ano else '?', t[:200], i['url']))
for r in sorted(rows):
    print(r[0], '|', r[1], '|', r[2], '|', r[3][14:150])
    print('   ', r[4])
print('== basefy_links', type(d['basefy_links']), len(d['basefy_links']))
bl = d['basefy_links']
it = bl.items() if isinstance(bl, dict) else bl
seen = set()
for x in it:
    s = json.dumps(x, ensure_ascii=False)
    for h, t in re.findall(r'"(https://basefy\.io/p/[^"]+)",\s*"([^"]*)"', s):
        if h in seen or 'premium' in t.lower():
            continue
        if re.search(r'(?i)canal|youtube|monetiz|inscrit', t + h):
            seen.add(h); print('  B', t[:160], '|', h)
print('== accs_paginas', str(d['accs_paginas'])[:500])
