PREP = 'import json, os, subprocess, sys\nfrom app.tempo import formatar\nfrom app.agrupar import por_canal\ndef rodar(*a):\n    return subprocess.run([sys.executable, "relatorio.py", "videos.csv", *a], capture_output=True, text=True, encoding="utf-8",\n                          errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8")).stdout\nESPERADO = {"anime": {"videos": 2, "segundos": 4059}, "curiosidades": {"videos": 1, "segundos": 600},\n            "manhwa": {"videos": 3, "segundos": 4500}}\n'
CASOS = ["formatar(59) == '0:59'", "formatar(600) == '10:00'", "formatar(3600) == '1:00:00'", "formatar(3725) == '1:02:05'", "formatar(7322) == '2:02:02'", "por_canal([{'canal': 'Manhwa', 'segundos': 10}, {'canal': ' manhwa ', 'segundos': 5}]) == {'manhwa': {'videos': 2, 'segundos': 15}}", "json.loads(rodar('--json')) == ESPERADO", "'manhwa: 3 vídeos, 1:15:00' in rodar()", "'anime: 2 vídeos, 1:07:39' in rodar()", "rodar().count('manhwa') == 1"]
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
