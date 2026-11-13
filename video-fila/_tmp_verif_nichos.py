import json, subprocess, sys, time
c = json.load(open(r"D:\video-fila\estado\candidatos_nichos.json", encoding="utf-8"))
# espera a verificação anterior (lista do Argon) terminar, pra não rodar 2 juntas
for _ in range(120):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", "@(Get-CimInstance Win32_Process | ? { $_.CommandLine -like '*verificar_canais_youtube.py @Ilustrada*' }).Count"], capture_output=True, text=True, creationflags=0x08000000)
    if (r.stdout or "0").strip() in ("0", ""):
        break
    time.sleep(15)
for nicho, hs in c.items():
    with open(rf"D:\video-fila\estado\verif_{nicho}.txt", "w", encoding="utf-8") as f:
        subprocess.run([sys.executable, r"D:\video-fila\verificar_canais_youtube.py", *hs], stdout=f, stderr=subprocess.STDOUT,
                       creationflags=0x08000000)
print("ok")
