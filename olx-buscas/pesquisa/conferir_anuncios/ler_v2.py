import json, re
d = json.load(open('canais_v2.json', encoding='utf-8'))
seen = set()
for u, v in d.items():
    if 'erro' in v:
        print('==', u, 'ERRO', v['erro'][:120]); continue
    if 'basefy' not in u:
        print('==', u, '->', v['final'], '|', v['titulo'])
        print('   TEXTO:', v['texto'][:1500].replace('\n', ' '))
        continue
    for h, t in v['links']:
        if '/p/' not in h or h in seen:
            continue
        if re.search(r'(?i)premium|music|curtida|views|visualiza|seguidores|pack|acervo|steam|roteiro|downloader|baixador|bot', t):
            continue
        if re.search(r'(?i)canal|channel|youtube|monetiz|inscrit', t + h):
            seen.add(h); print('  B', t[:170], '|', h)
