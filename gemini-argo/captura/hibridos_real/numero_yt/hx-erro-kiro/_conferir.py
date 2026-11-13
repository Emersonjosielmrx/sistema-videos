PREP = 'from youtube_http import _numero as n, resumo_canal\n'
CASOS = ["n('3,4 mi de inscritos') == 3400000", "n('4,1 mi de inscritos') == 4100000", "n('2.3M views') == 2300000", "n('1.5K views') == 1500", "n('1,2 mil visualizações') == 1200", "n('10 mil visualizações') == 10000", "n('12.345 visualizações') == 12345", "n('1.234.567 views') == 1234567", "n('812 vídeos') == 812", "n('1,2 bi de visualizações') == 1200000000", "n('Nenhuma visualização') == 0", "n('Sem visualizações') == 0", "n('') is None", "n('2 meses atrás') == 2", "resumo_canal({'inscritos': '3,4 mi de inscritos', 'videos': '812 vídeos'}) == {'inscritos': 3400000, 'videos': 812}"]
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
