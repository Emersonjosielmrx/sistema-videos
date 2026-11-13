# -*- coding: utf-8 -*-
"""publicar.py — põe o Painel de Clientes no ar em https://clientes.opus-sem-limites.com.br (hermes-prod).

    python publicar.py            # tudo: config + chaves, envia, sobe o contêiner, Traefik, log de visitas, cron, teste
    python publicar.py --config   # cliente novo: só refaz clientes.json/chaves e manda (o painel relê sozinho)

O que faz na hermes-prod (PRODUÇÃO do Hermes Call — nada dele é tocado):
  /opt/painel-clientes/servidor  app.py, web/, Dockerfile, docker-compose.yml (contêiner painel-clientes, 127.0.0.1:8098)
  /opt/painel-clientes/servidor/dados  clientes.json, segredos.json (600), painel.db, fontes/
  /opt/traefik-config/dynamic/clientes.yml  rota do subdomínio (DNS coringa *.opus-sem-limites.com.br)
  /etc/nginx/conf.d/painel_visitas.conf + 2º access_log no Precioso e nas landings (ligar_visitas_nginx.py: nginx -t
    antes, desfaz se falhar)
  /etc/cron.d/painel-clientes  coletor_vps.py a cada 5 min (pedidos/WhatsApp da loja e visitas)
No PC1: tarefas do Windows PainelClientes_Coletar (coletor\\coletar_instagram.py a cada 30 min) e
PainelClientes_ColetarHTTP (coletor\\coletar_instagram_http.py a cada 2 h, contas sem API), prioridade 6.
Links de acesso (admin e de cada cliente) ficam em segredos\\LINKS.txt — não vão para log nem para a tela.
"""
import json
import secrets
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import gerar_config

RAIZ = Path(__file__).resolve().parent
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
SCP = r"C:\Program Files\Git\usr\bin\scp.exe"
SERVIDOR = "hermes-prod"
REMOTO = "/opt/painel-clientes/servidor"
URL = "https://clientes.opus-sem-limites.com.br"
CHAVES = RAIZ / "segredos" / "chaves.json"
LINKS = RAIZ / "segredos" / "LINKS.txt"
HERMES_CHAVE = RAIZ / "segredos" / "hermes_chave.txt"
PYTHONW = r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe"
TAREFA = "PainelClientes_Coletar"
TAREFA_HTTP = "PainelClientes_ColetarHTTP"
PYTHONW_VEO = r"D:\veo\venv\Scripts\pythonw.exe"  # tem o curl_cffi/requests que o navegador-sem-navegador usa
SEM_JANELA = 0x08000000

REMOTO_SCRIPT = r"""set -e
cd /opt/painel-clientes/servidor
mkdir -p dados/fontes
chown -R 1000:1000 dados
chmod 600 dados/segredos.json
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi
$DC up -d --build 2>&1 | tail -4
docker restart painel-clientes >/dev/null
cat > /opt/traefik-config/dynamic/clientes.yml <<'EOF'
http:
  routers:
    clientes-http:
      rule: "Host(`clientes.opus-sem-limites.com.br`)"
      service: clientes-svc
      entryPoints:
        - web
    clientes:
      rule: "Host(`clientes.opus-sem-limites.com.br`)"
      service: clientes-svc
      entryPoints:
        - websecure
      tls:
        certResolver: le
  services:
    clientes-svc:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8098/"
EOF
python3 /opt/painel-clientes/servidor/ligar_visitas_nginx.py
cat > /etc/cron.d/painel-clientes <<'EOF'
# Painel de Clientes: pedidos/WhatsApp da loja e visitas dos sites (só leitura) -> /opt/painel-clientes/servidor/dados/fontes
*/5 * * * * root /usr/bin/python3 /opt/painel-clientes/servidor/coletor_vps.py
EOF
chmod 644 /etc/cron.d/painel-clientes
python3 /opt/painel-clientes/servidor/coletor_vps.py --ver
sleep 4
echo "saude local: $(curl -s -m 10 http://127.0.0.1:8098/api/saude)"
"""


def _ler(p, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def garantir_chaves(clientes):
    ch = _ler(CHAVES, {})
    ch.setdefault("admin", secrets.token_urlsafe(24))
    ch.setdefault("sal", secrets.token_hex(16))
    cls = ch.setdefault("clientes", {})
    for c in clientes:
        cls.setdefault(c["id"], secrets.token_urlsafe(18))
    # 30/10 (dona): cliente entra com usuário e senha (a senha é o nome dele); só o hash vai para o servidor
    import hashlib
    logins = ch.setdefault("logins", {})
    for c in clientes:
        if c.get("login"):
            u = str(c["login"]).strip().lower()
            senha = str(c.get("senha") or u).strip().lower()
            logins[u] = {"cliente": c["id"], "sha": hashlib.sha256(f"{ch['sal']}|{senha}".encode()).hexdigest()}
    # 30/10: WhatsApp do cliente ligado no Hermes Call (vídeo postado -> status). A chave de API (hk_...) é criada
    # pela dona no Hermes (Configurações › API do Sistema › API Keys) e colada sozinha em segredos\hermes_chave.txt.
    try:
        hk = HERMES_CHAVE.read_text(encoding="utf-8-sig").strip().splitlines()[0].strip()
    except (OSError, IndexError):
        hk = ""
    if hk:
        ch["hermes_chave"] = hk
    CHAVES.parent.mkdir(parents=True, exist_ok=True)
    CHAVES.write_text(json.dumps(ch, indent=1), encoding="utf-8")
    linhas = ["Painel de Clientes — links de acesso (não compartilhar o de administração)", "",
              f"ADMINISTRAÇÃO (vê todos, cria campanhas e links): {URL}/#k={ch['admin']}", ""]
    for c in clientes:
        if c.get("ativo", True):
            linhas.append(f"{c['nome']} ({c['tipo']}): {URL}/#k={cls[c['id']]}")
    LINKS.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return ch


def rodar(args, entrada=None, timeout=600):
    r = subprocess.run(args, input=entrada, capture_output=True, timeout=timeout, creationflags=SEM_JANELA)
    saida = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
    saida = "\n".join(ln for ln in saida.splitlines() if "post-quantum" not in ln and "store now, decrypt later" not in ln
                      and "openssh.com/pq" not in ln)
    return r.returncode, saida.strip()


def ssh(cmd, entrada=None, timeout=600):
    return rodar([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", SERVIDOR, cmd], entrada, timeout)


def enviar(local, remoto):
    rc, out = rodar([SCP, "-q", "-o", "BatchMode=yes", str(local), f"{SERVIDOR}:{remoto}"], timeout=120)
    if rc != 0:
        raise RuntimeError(f"envio de {local} falhou: {out[-300:]}")


def enviar_config():
    enviar(RAIZ / "config" / "clientes.json", f"{REMOTO}/dados/clientes.json")
    enviar(CHAVES, f"{REMOTO}/dados/segredos.json")
    rc, out = ssh(f"chown 1000:1000 {REMOTO}/dados/clientes.json {REMOTO}/dados/segredos.json && "
                  f"chmod 600 {REMOTO}/dados/segredos.json")
    if rc != 0:
        raise RuntimeError(out)


def _uma_tarefa(nome, python, script, minutos, limite_min):
    rc, _ = rodar(["schtasks", "/query", "/tn", nome])
    criada = rc != 0
    if criada:
        rc, out = rodar(["schtasks", "/create", "/tn", nome, "/tr", f'"{python}" "{script}"', "/sc", "minute",
                         "/mo", str(minutos), "/f"])
        if rc != 0:
            return f"{nome}: FALHOU ao criar: {out[-200:]}"
    # 30/10: o schtasks cria com prioridade 7 (abaixo do normal) e limite de 72 h — com a CPU cheia a coleta
    # arrastava (msenergy levou 7 min). Prioridade 6 e um limite curto (rodada travada não segura a próxima).
    ps = (f"$t = Get-ScheduledTask -TaskName '{nome}'; $t.Settings.Priority = 6; "
          f"$t.Settings.ExecutionTimeLimit = 'PT{limite_min}M'; Set-ScheduledTask -InputObject $t | Out-Null")
    rc, out = rodar(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps])
    ajuste = "prioridade 6" if rc == 0 else f"ajuste FALHOU: {out[-150:]}"
    return f"{nome}: {'criada' if criada else 'já existia'} (a cada {minutos} min, {ajuste})"


def tarefa_windows():
    return "; ".join([
        _uma_tarefa(TAREFA, PYTHONW, RAIZ / "coletor" / "coletar_instagram.py", 30, 25),
        # contas sem API (instagram_http): pela sessão do cofre, pouca leitura (a cada 2 h)
        _uma_tarefa(TAREFA_HTTP, PYTHONW_VEO, RAIZ / "coletor" / "coletar_instagram_http.py", 120, 20),
    ])


def saude(url, tentativas=12):
    for _ in range(tentativas):
        try:
            return json.loads(urllib.request.urlopen(f"{url}/api/saude", timeout=20).read())
        except Exception as e:  # noqa: BLE001 — o certificado novo do Let's Encrypt leva alguns segundos
            erro = e
            time.sleep(10)
    return {"erro": f"{type(erro).__name__}: {erro}"}


def main():
    clientes = gerar_config.gerar()
    garantir_chaves(clientes)
    print(f"config: {sum(1 for c in clientes if c.get('ativo', True))} ativos ({len(clientes)} no total); "
          f"links de acesso em {LINKS}")
    if "--config" in sys.argv:
        enviar_config()
        print("config enviada (o painel relê sozinho)")
        print(tarefa_windows())  # cliente novo com "instagram_http" precisa da tarefa do coletor HTTP
        return
    rc, out = ssh(f"mkdir -p {REMOTO}/web {REMOTO}/dados/fontes")
    if rc != 0:
        raise SystemExit(f"sem acesso à {SERVIDOR}: {out}")
    srv = RAIZ / "servidor"
    for f in ("app.py", "Dockerfile", "docker-compose.yml", "coletor_vps.py", "ligar_visitas_nginx.py"):
        enviar(srv / f, f"{REMOTO}/{f}")
    enviar(srv / "web" / "index.html", f"{REMOTO}/web/index.html")
    enviar_config()
    rc, out = ssh("bash -s", entrada=REMOTO_SCRIPT.encode("utf-8"), timeout=900)
    print(out[-2500:])
    if rc != 0:
        raise SystemExit("a publicação parou com erro (ver acima)")
    print(tarefa_windows())
    print("saúde pública:", saude(URL))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
