#!/usr/bin/env python3
r"""Extrai o cookie sessionKey do claude.ai de um perfil do Chrome NORMAL.

Copia o perfil pra uma pasta temporaria e abre um Chrome oculto (nao mexe no Chrome
da dona), conecta por CDP e le os cookies ja descriptografados (o Chrome padrao
descriptografa o v20 normalmente).

Uso:
    python extrair_claude.py "Profile 7"            # imprime o header de cookies do claude.ai
    python extrair_claude.py "Profile 7" --so-sk    # imprime so o sessionKey
"""
import os
import sys
import time
import json
import shutil
import socket
import tempfile
import argparse
import subprocess

sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright

UD = r"C:\Users\SEU_USUARIO\AppData\Local\Google\Chrome\User Data"
PULAR = {"Cache", "Code Cache", "GPUCache", "GraphicsCache", "DawnCache", "DawnGraphiteCache",
         "DawnWebGPUCache", "Service Worker", "Extensions", "Extension State", "IndexedDB",
         "File System", "Local Storage", "Session Storage", "blob_storage", "shared_proto_db",
         "optimization_guide_model_store", "component_crx_cache", "segmentation_platform"}


def _porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _copiar_perfil(prof, destino):
    os.makedirs(destino, exist_ok=True)
    shutil.copy2(os.path.join(UD, "Local State"), os.path.join(destino, "Local State"))
    src = os.path.join(UD, prof)
    dst = os.path.join(destino, prof)
    os.makedirs(dst, exist_ok=True)
    for nome in os.listdir(src):
        if nome in PULAR:
            continue
        s = os.path.join(src, nome)
        d = os.path.join(dst, nome)
        try:
            if os.path.isdir(s):
                shutil.copytree(s, d, ignore=shutil.ignore_patterns(*PULAR), dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        except Exception:
            pass


def extrair(prof, so_sk=False):
    tmp = tempfile.mkdtemp(prefix="clweb_")
    _copiar_perfil(prof, tmp)
    porta = _porta_livre()
    proc = subprocess.Popen(
        [cofre.CHROME, f"--remote-debugging-port={porta}", f"--user-data-dir={tmp}",
         f"--profile-directory={prof}", *cofre.FLAGS, "--window-position=-3000,0", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(40):
            try:
                with socket.create_connection(("127.0.0.1", porta), timeout=0.5):
                    break
            except OSError:
                time.sleep(0.5)
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=30000)
            ctx = br.contexts[0]
            pg = ctx.new_page()
            cdp = ctx.new_cdp_session(pg)
            resp = cdp.send("Network.getAllCookies")
            ck = [c for c in resp["cookies"] if "claude.ai" in c.get("domain", "")]
            sk = next((c["value"] for c in ck if c["name"] == "sessionKey"), "")
            header = "; ".join(f"{c['name']}={c['value']}" for c in ck)
            br.close()
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)
    return sk if so_sk else (sk, header)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("profile")
    p.add_argument("--so-sk", action="store_true")
    a = p.parse_args()
    if a.so_sk:
        print(extrair(a.profile, so_sk=True))
    else:
        sk, header = extrair(a.profile)
        print("sessionKey:", (sk[:25] + "...") if sk else "(VAZIO)")
        print("len(sessionKey):", len(sk))
        print("header claude.ai:", (header[:120] + "...") if header else "(vazio)")
