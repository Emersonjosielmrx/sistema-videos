# -*- coding: utf-8 -*-
r"""sincronizar_pool_kaggle.py — traz o kaggle_pool.json da central (hermes-prod) pro PC1 (16/11).

Por quê: a trava do IP fixo (D:\logins-google\cofre._ip_fixo_kaggle -> saida_kaggle) lê o pool do PC1, que estava parado
em 13/11 e NÃO conhecia as contas ligadas depois (rezaulkarimul355 = dona do MundoQueNaoExiste, murilodoctor192 = canal
"fofos e absurdos" + TikTok). Sem a trava, o YouTube/TikTok dessas contas sairia pela internet de casa enquanto o Kaggle
sai pelo rnprmtfo-N = mesma conta em 2 IPs = o padrão do 3º banimento (14/11).

Copia só o que a trava precisa (cofre, username, proxy_fixo, verificada, banida, pausada, papel) — o TOKEN fica só na VPS.
Contas que somem do pool da VPS continuam aqui (a trava barra a mais, nunca a menos). Tarefa SincronizarPoolKaggle
(30/30 min, oculta). Desligar: SINCRONIZAR_POOL_KAGGLE=0.
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOCAL = Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json")
CAMPOS = ("cofre", "username", "proxy_fixo", "verificada", "banida", "pausada", "papel", "saida", "ativa", "nota")


def main():
    if os.environ.get("SINCRONIZAR_POOL_KAGGLE", "1") == "0":
        return 0
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", "hermes-prod",
                        "cat /opt/recap_central/kaggle_pool.json"], capture_output=True, text=True, encoding="utf-8",
                       timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0 or not r.stdout.strip():
        print("não li o pool da VPS:", (r.stderr or "")[-200:])
        return 1
    vps = json.loads(r.stdout)
    try:
        loc = json.loads(LOCAL.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        loc = {"contas": []}
    por_user = {c.get("username"): c for c in loc.get("contas", []) if c.get("username")}
    for c in vps.get("contas", []):
        enxuto = {k: c[k] for k in CAMPOS if k in c}
        por_user[c.get("username")] = {**{k: v for k, v in por_user.get(c.get("username"), {}).items()
                                          if k not in ("token", "key")}, **enxuto}
    novo = {k: v for k, v in vps.items() if k != "contas"}
    novo["contas"] = list(por_user.values())
    novo["_sincronizado"] = f"{datetime.now():%Y-%m-%d %H:%M} da hermes-prod (sem tokens) — sincronizar_pool_kaggle.py"
    if LOCAL.exists():
        shutil.copy(LOCAL, LOCAL.with_suffix(".json.bak_sync"))
    tmp = LOCAL.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(LOCAL)
    print(f"pool sincronizado: {len(novo['contas'])} contas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
