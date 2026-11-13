#!/usr/bin/env python3
r"""Extrai cookies das 2 contas de teste e cadastra no OmniRoute via SSH."""
import json
import subprocess
import sys
import os
import time

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\gemini-argo")
from extrair_cookies import extrair

CONTAS = ["emersonjosiel2029", "emersonjosiel2030"]
TOKEN = "<SEGREDO_REMOVIDO>"

contas_json = []
for conta in CONTAS:
    print(f"Extraindo cookies de {conta}...")
    os.system("taskkill /F /IM chrome.exe >NUL 2>&1")
    time.sleep(3)
    cookie = extrair(conta, formato="header")
    contas_json.append({
        "name": f"{conta} Pro",
        "cookie": cookie,
    })
    print(f"  {len(cookie)} chars")
    os.system("taskkill /F /IM chrome.exe >NUL 2>&1")
    time.sleep(2)

local_json = r"D:\gemini-argo\contas_para_cadastrar.json"
with open(local_json, "w", encoding="utf-8") as f:
    json.dump(contas_json, f, ensure_ascii=False)
print(f"\nSalvo em {local_json}")

subprocess.run(["scp", local_json, "hermes-bloqueio:/tmp/gweb_contas.json"], check=True)
subprocess.run(["scp", r"D:\gemini-argo\cadastrar_omniroute.py", "hermes-bloqueio:/tmp/cadastrar_omniroute.py"], check=True)
print("Copiados pra VPS")

r = subprocess.run(
    ["ssh", "hermes-bloqueio", f"python3 /tmp/cadastrar_omniroute.py {TOKEN}"],
    capture_output=True, text=True, timeout=60,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:500])
