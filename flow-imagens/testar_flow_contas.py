# Testa se as contas abrem o Flow na fÃ¡brica de tokens de uma mÃ¡quina (200 = logada no Flow, 401 = pede login).
#   python testar_flow_contas.py desktop conta1,conta2,...
import json
import subprocess
import sys
import urllib.parse

maq, contas = sys.argv[1], sys.argv[2].split(",")
proj = json.load(open(r"D:\veo\beta\logs\flow_projetos.json", encoding="utf-8"))
for c in contas:
    url = proj.get(c) or ""
    if "/project/" not in url:
        print(f"{c}: sem projeto salvo")
        continue
    q = urllib.parse.urlencode({"perfil": c.lower(), "projeto": url})
    ps = (f"try {{ $r = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:9399/sessao?{q}' -TimeoutSec 200; "
          f"'200 ' + $r.Content.Length }} catch {{ [string]$_.Exception.Response.StatusCode.value__ + ' ' + $_.ErrorDetails.Message }}")
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", maq, f'powershell -NoProfile -Command "{ps}"'],
                       capture_output=True, text=True, errors="replace", timeout=260, creationflags=0x08000000)
    out = (r.stdout or r.stderr).strip().splitlines()
    print(f"{c}: {out[-1][:200] if out else '?'}", flush=True)

