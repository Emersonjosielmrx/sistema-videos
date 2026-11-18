"""teste rápido: POST /task por HTTP puro (curl_cffi) pela ponte do IP da conta, SEM recaptcha. Prova se dá pra gerar
sem navegador. NÃO faz parte da produção."""
import sys, json, time
from pathlib import Path
sys.path.insert(0, r"D:\logins-google")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import fish_audio as fa

EMAIL = sys.argv[1] if len(sys.argv) > 1 else fa.CONTA_PADRAO
TOKEN = json.loads((AQUI / "capturas" / "localStorage.json").read_text("utf-8"))["token"]
VOZ = fa.VOZ_PADRAO
TEXTO = "Primeiro, temos o tio do pave, aquele que separa tudo que e pave do que nao e pave."

_, ip_n = fa.checar_conta(EMAIL)
porta = fa._subir_ponte(ip_n)
proxy = f"http://127.0.0.1:{porta}"
print("IP ponte N=", ip_n, "porta", porta, "token", TOKEN[:12] + "...")

from curl_cffi import requests as creq
s = creq.Session(impersonate="chrome", proxies={"http": proxy, "https": proxy})
s.headers.update({"Authorization": f"Bearer {TOKEN}", "Origin": "https://fish.audio",
                  "Referer": "https://fish.audio/", "Content-Type": "application/json"})

# 0. confere o IP de saída e o token
try:
    who = s.get("https://api.fish.audio/wallet/" + json.loads(
        (AQUI / "capturas" / "localStorage.json").read_text("utf-8"))["active_workspace_id"] + "/package", timeout=30)
    print("wallet:", who.status_code, who.text[:120])
except Exception as e:
    print("wallet erro:", e)

body = {"type": "tts", "stream": True, "model": VOZ, "latency": "balanced",
        "parameters": {"text": TEXTO, "model_id": VOZ, "format": "mp3", "latency": "balanced",
                       "backend": "drama-3", "normalize": False},
        "format": "mp3", "backend": "drama-3"}

t0 = time.time()
r = s.post("https://api.fish.audio/task", json=body, timeout=120)
dt = round(time.time() - t0, 1)
ct = r.headers.get("content-type", "")
print(f"POST /task SEM recaptcha -> {r.status_code} {ct} {len(r.content)} bytes em {dt}s")
if r.status_code == 200 and ("audio" in ct or "octet" in ct or len(r.content) > 5000):
    out = AQUI / "capturas" / "http_puro_sem_recaptcha.mp3"
    out.write_bytes(r.content)
    print("OK! mp3 salvo em", out)
else:
    print("corpo:", r.text[:500])
