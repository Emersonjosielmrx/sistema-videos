# -*- coding: utf-8 -*-
"""
Dispara requisicoes simultaneas para as 2 contas cc alvo:
  - claralealdacru@outlook.com
  - cleusacunhssanto@outlook.com
Cada requisicao sai obrigatoriamente por um proxy Webshare com IP de saida distinto,
sem jamais passar pelo IP da VPS 157 nem pelo IP local sem proxy.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

CONTAS_ALVO = [
    "claralealdacru@outlook.com",
    "cleusacunhssanto@outlook.com",
]

PROXIES_TXT = r"D:\postador-de-videos\secrets\proxies.txt"
WEBSHARE_JSON = r"D:\video-fila\estado\webshare.json"


def carregar_proxies_ips_unicos():
    """Cruza webshare.json (estado == ok) com proxies.txt e seleciona 1 proxy por IP unico."""
    with open(WEBSHARE_JSON, "r", encoding="utf-8") as f:
        ws = json.load(f)

    urls_por_conta = {}
    with open(PROXIES_TXT, "r", encoding="utf-8") as f:
        for linha in f:
            u = linha.strip()
            if not u or "@" not in u:
                continue
            # http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80
            cred = u.split("://", 1)[1].split("@", 1)[0]
            conta = cred.split(":", 1)[0].replace("-rotate", "")
            urls_por_conta.setdefault(conta, []).append(u)

    escolhidos = []
    ips_vistos = set()
    contas_usadas = {}
    for item in ws.get("contas", []):
        if item.get("estado") == "ok" and item.get("ip"):
            ip = item["ip"]
            conta = item["conta"]
            if ip not in ips_vistos and conta in urls_por_conta:
                idx_u = contas_usadas.get(conta, 0)
                lista_u = urls_por_conta[conta]
                proxy_url = lista_u[idx_u] if idx_u < len(lista_u) else lista_u[0]
                contas_usadas[conta] = idx_u + 1
                ips_vistos.add(ip)
                escolhidos.append({
                    "conta_ws": conta,
                    "ip_esperado": ip,
                    "proxy_url": proxy_url,
                })
    return escolhidos


def obter_tokens_vps():
    """Le e descriptografa apenas os tokens das 2 contas alvo no SQLite da VPS 157 (sem chamadas externas)."""
    sql = "SELECT email, access_token, expires_at FROM provider_connections WHERE provider='claude' AND email IN ('claralealdacru@outlook.com','cleusacunhssanto@outlook.com');"
    r_sql = subprocess.run(
        ["ssh", "hermes-bloqueio", f'sqlite3 /opt/omniroute/data/storage.sqlite "{sql}"'],
        capture_output=True,
        text=True,
        check=True,
    )
    linhas = [l.strip() for l in r_sql.stdout.splitlines() if "|" in l]
    js_code = (
        "const fs=require('fs'),crypto=require('crypto');\n"
        "const env=fs.readFileSync('/app/data/server.env','utf8');\n"
        "const v=env.split('\\n').find(l=>l.trim().startsWith('STORAGE_ENCRYPTION_KEY=')).split('=').slice(1).join('=').trim().replace(/^[\"'](.*)[\"']$/,'$1');\n"
        "const key=crypto.scryptSync(v,'omniroute-field-encryption-v1',32);\n"
        "const enc=process.env.TK_ENC;\n"
        "const[iv,d,tag]=enc.slice(7).split(':');\n"
        "const c=crypto.createDecipheriv('aes-256-gcm',key,Buffer.from(iv,'hex'),{authTagLength:16});\n"
        "c.setAuthTag(Buffer.from(tag,'hex'));\n"
        "process.stdout.write(c.update(d,'hex','utf8')+c.final('utf8'));\n"
    )
    out = {}
    for l in linhas:
        em, enc, exp = l.split("|", 2)
        r_dec = subprocess.run(
            ["ssh", "hermes-bloqueio", f"docker exec -i -e TK_ENC='{enc}' omniroute node -"],
            input=js_code,
            capture_output=True,
            text=True,
            check=True,
        )
        out[em] = {"token": r_dec.stdout.strip(), "expires_at": exp}
    return out


def disparar_uma(email, token, proxy_info, idx):
    proxy_url = proxy_info["proxy_url"]
    proxies = {"http": proxy_url, "https": proxy_url}
    headers_base = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "claude-code/2.1.32",
        "anthropic-beta": "claude-code-20250219,oauth-2025-04-20,interleaved-thinking-2025-05-14",
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    res = {
        "idx": idx,
        "email": email,
        "conta_ws": proxy_info["conta_ws"],
        "ip_esperado": proxy_info["ip_esperado"],
    }
    try:
        # 1. Confirma o IP de saida real do proxy (garante que nao sai pelo PC1 nem VPS)
        r_ip = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=12)
        ip_real = r_ip.json().get("ip", "?")
        res["ip_real"] = ip_real

        # 2. Faz chamada em /api/oauth/usage e /v1/messages?beta=true pelo mesmo proxy
        r_u = requests.get(
            "https://api.anthropic.com/api/oauth/usage",
            headers=headers_base,
            proxies=proxies,
            timeout=15,
        )
        res["usage_status"] = r_u.status_code
        res["usage_body"] = r_u.text[:200]

        body_msg = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "ping"}],
        }
        r_m = requests.post(
            "https://api.anthropic.com/v1/messages?beta=true",
            headers=headers_base,
            json=body_msg,
            proxies=proxies,
            timeout=20,
        )
        res["msg_status"] = r_m.status_code
        res["msg_body"] = r_m.text[:240]
    except Exception as e:
        res["erro"] = str(e)[:200]
    return res


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "dry"
    proxies = carregar_proxies_ips_unicos()
    print(f"Proxies com IPs unicos carregados: {len(proxies)}")
    for i, p in enumerate(proxies, 1):
        print(f"  [{i:02d}] conta_ws={p['conta_ws']} | ip={p['ip_esperado']}")

    tokens = obter_tokens_vps()
    print("\nContas alvo carregadas do SQLite da VPS 157:")
    for em in CONTAS_ALVO:
        info = tokens.get(em)
        if info:
            tk = info["token"]
            print(f"  - {em}: token={tk[:18]}... (len={len(tk)}) | expires_at={info['expires_at']}")
        else:
            print(f"  - {em}: NAO ENCONTRADA!")

    if modo != "disparar":
        print("\n[MODO PREVIEW/DRY] Nenhuma requisicao foi enviada para a Anthropic. Passe 'disparar' para executar.")
        return

    tarefas = []
    with ThreadPoolExecutor(max_workers=len(proxies) * 2) as ex:
        for em in CONTAS_ALVO:
            tk = tokens[em]["token"]
            for idx, p in enumerate(proxies, 1):
                tarefas.append(ex.submit(disparar_uma, em, tk, p, idx))

        for fut in as_completed(tarefas):
            r = fut.result()
            print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
