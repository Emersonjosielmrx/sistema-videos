# -*- coding: utf-8 -*-
"""
Rajada massiva simultanea APENAS na conta cleusacunhssanto@outlook.com
usando 496 workers (4x mais chamadas) com saídas fixas -1 a -10 e rotação dinâmica,
maximizando o número de IPs de saída simultâneos sem passar pelo IP da VPS nem pelo IP local.
"""
import base64
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

EMAIL_ALVO = "cleusacunhssanto@outlook.com"
PROXIES_TXT = r"D:\postador-de-videos\secrets\proxies.txt"
WEBSHARE_JSON = r"D:\video-fila\estado\webshare.json"


def carregar_proxies_expandidos(alvo_total=496):
    """
    Carrega todas as contas Webshare com estado=='ok' e gera:
    1. Saídas fixas -1 a -10 para cada conta (270 endpoints com IPs fixos distintos)
    2. Saídas -rotate iteradas para atingir o alvo de chamadas simultâneas (496 workers = 4x o anterior)
    """
    with open(WEBSHARE_JSON, "r", encoding="utf-8") as f:
        ws = json.load(f)

    contas_ok = {item["conta"] for item in ws.get("contas", []) if item.get("estado") == "ok"}

    urls_base = {}
    with open(PROXIES_TXT, "r", encoding="utf-8") as f:
        for linha in f:
            u = linha.strip()
            if not u or "@" not in u:
                continue
            cred = u.split("://", 1)[1].split("@", 1)[0]
            conta = cred.split(":", 1)[0].replace("-rotate", "")
            if conta in contas_ok and conta not in urls_base:
                urls_base[conta] = u

    lista = []
    # 1. Adiciona todas as saídas fixas -1 a -10 de cada conta
    for conta, base_url in urls_base.items():
        for i in range(1, 11):
            lista.append({
                "conta_ws": f"{conta}-{i}",
                "proxy_url": base_url.replace("-rotate", f"-{i}"),
            })

    # 2. Adiciona saídas -rotate até atingir alvo_total
    passo = 1
    while len(lista) < alvo_total:
        for conta, base_url in urls_base.items():
            lista.append({
                "conta_ws": f"{conta}-rot#{passo}",
                "proxy_url": base_url,
            })
            if len(lista) >= alvo_total:
                break
        passo += 1

    return lista


def achar_ssh():
    git_ssh = r"C:\Program Files\Git\usr\bin\ssh.exe"
    if os.path.exists(git_ssh):
        return git_ssh
    return "ssh"


def obter_token_cleusa():
    ssh_bin = achar_ssh()
    sql = "SELECT access_token, expires_at FROM provider_connections WHERE provider='claude' AND email='cleusacunhssanto@outlook.com';"
    r_sql = subprocess.run(
        [ssh_bin, "-n", "-T", "hermes-bloqueio", f'sqlite3 /opt/omniroute/data/storage.sqlite "{sql}"'],
        capture_output=True,
        text=True,
        check=True,
    )
    linha = [l.strip() for l in r_sql.stdout.splitlines() if "|" in l][0]
    enc, exp = linha.split("|", 1)
    js_code = (
        "const fs=require('fs'),crypto=require('crypto');\n"
        "const env=fs.readFileSync('/app/data/server.env','utf8');\n"
        "const v=env.split(String.fromCharCode(10)).find(l=>l.trim().startsWith('STORAGE_ENCRYPTION_KEY=')).split('=').slice(1).join('=').trim().replace(/^[\"'](.*)[\"']$/,'$1');\n"
        "const key=crypto.scryptSync(v,'omniroute-field-encryption-v1',32);\n"
        "const enc=process.env.TK_ENC;\n"
        "const[iv,d,tag]=enc.slice(7).split(':');\n"
        "const c=crypto.createDecipheriv('aes-256-gcm',key,Buffer.from(iv,'hex'),{authTagLength:16});\n"
        "c.setAuthTag(Buffer.from(tag,'hex'));\n"
        "process.stdout.write(c.update(d,'hex','utf8')+c.final('utf8'));\n"
    )
    b64 = base64.b64encode(js_code.encode("utf-8")).decode("ascii")
    cmd_node = f"echo {b64} | base64 -d | docker exec -i -e TK_ENC='{enc}' omniroute node -"
    r_dec = subprocess.run(
        [ssh_bin, "-n", "-T", "hermes-bloqueio", cmd_node],
        capture_output=True,
        text=True,
        check=True,
    )
    return r_dec.stdout.strip(), exp


def disparar_worker(token, proxy_info, idx):
    proxy_url = proxy_info["proxy_url"]
    proxies = {"http": proxy_url, "https": proxy_url}
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "claude-code/2.1.32",
        "anthropic-beta": "claude-code-20250219,oauth-2025-04-20,interleaved-thinking-2025-05-14",
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "close",
    }
    out = {"idx": idx, "conta_ws": proxy_info["conta_ws"]}

    # 0. Resolucao do IP de saida (rapida com fallback para icanhazip)
    try:
        r_ip = requests.get("http://api.ipify.org?format=json", headers={"Connection": "close"}, proxies=proxies, timeout=5)
        if r_ip.status_code == 200:
            out["ip"] = r_ip.json().get("ip")
    except Exception:
        try:
            r_ip2 = requests.get("http://icanhazip.com", headers={"Connection": "close"}, proxies=proxies, timeout=5)
            if r_ip2.status_code == 200 and r_ip2.text.strip():
                out["ip"] = r_ip2.text.strip()
        except Exception as e:
            out["erro_ip"] = str(e)[:60]

    # 1. /api/oauth/usage
    try:
        ru = requests.get("https://api.anthropic.com/api/oauth/usage", headers=headers, proxies=proxies, timeout=12)
        out["usage"] = ru.status_code
        if ru.status_code not in (200, 429):
            out["usage_err"] = ru.text[:180]
    except Exception as e:
        out["usage_err"] = str(e)[:120]

    # 2. /v1/models
    try:
        rmod = requests.get("https://api.anthropic.com/v1/models", headers=headers, proxies=proxies, timeout=12)
        out["models"] = rmod.status_code
        if rmod.status_code not in (200, 429):
            out["models_err"] = rmod.text[:180]
    except Exception as e:
        out["models_err"] = str(e)[:120]

    # 3. /v1/messages/count_tokens?beta=true
    try:
        body_ct = {
            "model": "claude-sonnet-5-5",
            "messages": [{"role": "user", "content": f"ping test {idx}"}],
        }
        rct = requests.post("https://api.anthropic.com/v1/messages/count_tokens?beta=true", headers=headers, json=body_ct, proxies=proxies, timeout=12)
        out["count_tokens"] = rct.status_code
        if rct.status_code not in (200, 429):
            out["ct_err"] = rct.text[:180]
    except Exception as e:
        out["ct_err"] = str(e)[:120]

    # 4. /v1/messages?beta=true
    try:
        body_msg = {
            "model": "claude-sonnet-5-5",
            "max_tokens": 8,
            "messages": [{"role": "user", "content": f"hi {idx}"}],
        }
        rmsg = requests.post("https://api.anthropic.com/v1/messages?beta=true", headers=headers, json=body_msg, proxies=proxies, timeout=15)
        out["msg"] = rmsg.status_code
        if rmsg.status_code not in (200, 429):
            out["msg_err"] = rmsg.text[:180]
    except Exception as e:
        out["msg_err"] = str(e)[:120]

    return out


def main():
    proxies = carregar_proxies_expandidos(alvo_total=496)
    token, exp = obter_token_cleusa()
    print(f"Alvo UNICO: {EMAIL_ALVO} | token={token[:18]}... | expires_at={exp}")
    print(f"Total de workers simultaneos via proxy: {len(proxies)} (4 chamadas cada = {len(proxies)*4} requisicoes na Anthropic)")

    ips_unicos = set()
    status_usage = {}
    status_models = {}
    status_ct = {}
    status_msg = {}
    amostras_anomalias = []

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=124) as ex:
        futs = [ex.submit(disparar_worker, token, p, i) for i, p in enumerate(proxies, 1)]
        for fut in as_completed(futs):
            r = fut.result()
            if "ip" in r and r["ip"]:
                ips_unicos.add(r["ip"])
            for k, d in [("usage", status_usage), ("models", status_models), ("count_tokens", status_ct), ("msg", status_msg)]:
                if k in r:
                    st = r[k]
                    d[st] = d.get(st, 0) + 1
            if any(r.get(k) in (401, 403) for k in ("usage", "models", "count_tokens", "msg")):
                if len(amostras_anomalias) < 8:
                    amostras_anomalias.append(r)

    dt = time.time() - t0
    print(f"\nConcluido em {dt:.1f}s | IPs de saida distintos confirmados: {len(ips_unicos)} -> {sorted(ips_unicos)}")
    print(f"Resumo /api/oauth/usage          : {status_usage}")
    print(f"Resumo /v1/models                : {status_models}")
    print(f"Resumo /v1/messages/count_tokens : {status_ct}")
    print(f"Resumo /v1/messages              : {status_msg}")
    if amostras_anomalias:
        print("\nAmostras de 401/403 detectadas:")
        for a in amostras_anomalias:
            print(" ", json.dumps(a, ensure_ascii=False))


if __name__ == "__main__":
    main()
