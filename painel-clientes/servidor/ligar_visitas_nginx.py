#!/usr/bin/env python3
"""ligar_visitas_nginx.py — liga o log de visitas que o Painel de Clientes lê (hermes-prod, root; rodado pelo publicar.py).

Cria /etc/nginx/conf.d/painel_visitas.conf (formato com host e IP real que o Traefik passa) e acrescenta, nos sites
do Precioso e das landings, um 2º access_log (o log de sempre continua igual). Faz cópia antes, roda `nginx -t` e, se
falhar, desfaz tudo e sai com erro — o nginx em produção nunca recarrega com configuração quebrada. Idempotente.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

CONF = Path("/etc/nginx/conf.d/painel_visitas.conf")
FORMATO = ("log_format painel_visitas '$time_iso8601\\t$host\\t$http_x_forwarded_for\\t$request_method\\t$request_uri\\t"
           "$status\\t$http_referer\\t$http_user_agent';\n")
SITES = {"/etc/nginx/sites-enabled/precioso": "listen 127.0.0.1:8086;",
         "/etc/nginx/sites-enabled/landings": "listen 127.0.0.1:8087;"}
BACKUP = Path("/opt/painel-clientes/backup_nginx")


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    marca = time.strftime("%Y%m%d_%H%M%S")
    feitos = []  # (arquivo, cópia ou None se era novo)
    if not CONF.exists():
        CONF.write_text("# Painel de Clientes (/opt/painel-clientes): visitas por site com host e IP real\n" + FORMATO)
        feitos.append((CONF, None))
    for link, ancora in SITES.items():
        if not os.path.exists(link):
            print(f"pulado (não existe): {link}")
            continue
        real = Path(os.path.realpath(link))
        txt = real.read_text()
        if "painel_visitas" in txt:
            continue
        if ancora not in txt:
            print(f"pulado (sem '{ancora}'): {real}")
            continue
        copia = BACKUP / f"{real.name}.{marca}"
        shutil.copy2(real, copia)
        feitos.append((real, copia))
        linhas, novo = txt.split("\n"), []
        posto = False
        for ln in linhas:
            novo.append(ln)
            if not posto and ancora in ln:
                rec = ln[: len(ln) - len(ln.lstrip())]
                novo += [f"{rec}access_log /var/log/nginx/access.log;",
                         f"{rec}access_log /var/log/nginx/painel_visitas.log painel_visitas;"]
                posto = True
        real.write_text("\n".join(novo))
    if not feitos:
        print("log de visitas já estava ligado")
        return 0
    t = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    if t.returncode != 0:
        for arq, copia in feitos:
            if copia is None:
                arq.unlink(missing_ok=True)
            else:
                shutil.copy2(copia, arq)
        print("nginx -t FALHOU, tudo desfeito:\n" + t.stderr[-800:])
        return 1
    subprocess.run(["systemctl", "reload", "nginx"], check=True)
    print("log de visitas ligado: " + ", ".join(str(a) for a, _ in feitos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
