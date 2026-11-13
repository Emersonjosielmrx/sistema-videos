PREP = 'from calc import *\n'
CASOS = ['media_movel([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]', 'media_movel([5], 1) == [5.0]', 'media_movel([1, 2, 3], 3) == [2.0]', 'media_movel([1, 2], 3) == []', 'mediana([3, 1, 2]) == 2', 'mediana([4, 1, 3, 2]) == 2.5', 'mediana([10, 20]) == 15', 'mediana([7]) == 7']
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
