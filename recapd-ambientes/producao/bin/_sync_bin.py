"""_sync_bin.py — roda no PC2 via exec timeout.
Sincroniza arquivos do PC1 (10.8.0.3:8080) via HTTP simples.
"""
import os, json, sys, urllib.request, urllib.error, base64, zipfile, tempfile

PC1_HOST = "10.8.0.3"  # Tailscale IP do PC1
PC1_PORT = 8080
FILES = ["anime_script.py", "anime_tts.py", "anime_discover.py",
         "anime_auto.py", "anime_worker_client.py", "anime_night_shift.py",
         # daemon do PC2: ganhou /disk e /cleanup (transferir+apagar). Precisa
         # sincronizar + REINICIAR o daemon no PC2 pra valer.
         "anime_worker_daemon.py"]

BIN = r"C:\recapd-e-animes\bin"
os.makedirs(BIN, exist_ok=True)

ok_count, fail_count = 0, 0
for fname in FILES:
    url = f"http://{PC1_HOST}:{PC1_PORT}/files/{fname}"
    local = os.path.join(BIN, fname)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read()
        open(local, "wb").write(data)
        print(f"OK  {fname} ({len(data)} bytes)")
        ok_count += 1
    except Exception as e:
        print(f"FAIL {fname}: {e}")
        fail_count += 1

print(f"\nSync: {ok_count} ok, {fail_count} fail")
