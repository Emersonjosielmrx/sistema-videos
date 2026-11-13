r"""publicar_opus.py — publica as landing pages também em <slug>.opus-sem-limites.com.br (DNS coringa -> hermes-prod
62.171.128.241). Vitrine em produtos.opus-sem-limites.com.br. Mesmo padrão do nelson: Traefik do servidor (arquivo em
/opt/traefik-config/dynamic/landings.yml, certificado "le") -> nginx do servidor em 127.0.0.1:8087 (/var/www/landings).
Testa o nginx (nginx -t) ANTES de recarregar: é o servidor de produção do Hermes Call.

    python gerar.py && python publicar_opus.py
"""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
VPS = "hermes-prod"
DOM = "opus-sem-limites.com.br"
PORTA = 8087
HUB = "produtos"
EXTRAS = ["msenergy"]  # páginas fora do conteudo.json (cliente MS Energy: gerar_ms.py, 28/10)

NGINX = r"""map $host $lp_root {
    ~^HUB\.   /var/www/landings/site;
    ~^(?<lp_sub>[a-z0-9-]+)\.  /var/www/landings/site/$lp_sub;
}
server {
    listen 127.0.0.1:PORTA;
    server_name ~\.opus-sem-limites\.com\.br$;
    root $lp_root;
    index index.html;
    location /css/ { alias /var/www/landings/site/css/; expires 7d; }
    location / { try_files $uri $uri/ =404; }
}
""".replace("HUB", HUB).replace("PORTA", str(PORTA))


def traefik(slugs):
    linhas = ["http:", "  routers:"]
    for s in [HUB] + slugs:
        nome = f"lp-{s}"
        linhas += [f"    {nome}-http:", f"      rule: \"Host(`{s}.{DOM}`)\"", "      service: landings-svc",
                   "      entryPoints:", "        - web",
                   f"    {nome}:", f"      rule: \"Host(`{s}.{DOM}`)\"", "      service: landings-svc",
                   "      entryPoints:", "        - websecure", "      tls:", "        certResolver: le"]
    linhas += ["  services:", "    landings-svc:", "      loadBalancer:", "        servers:",
               f"          - url: \"http://127.0.0.1:{PORTA}/\""]
    return "\n".join(linhas) + "\n"


def ssh(cmd, entrada=None):
    r = subprocess.run(["ssh", VPS, cmd], input=entrada, capture_output=True)
    print((r.stdout + r.stderr).decode("utf-8", "replace").strip())
    if r.returncode:
        sys.exit(f"falhou: {cmd[:80]}")


def main():
    slugs = [p["slug"] for p in json.loads((BASE / "conteudo.json").read_text(encoding="utf-8"))["produtos"]]
    slugs += [s for s in EXTRAS if (BASE / "site" / s / "index.html").exists()]
    tar = subprocess.run(["tar", "-C", str(BASE), "-cf", "-", "site"], capture_output=True, check=True).stdout
    ssh("mkdir -p /var/www/landings && rm -rf /var/www/landings/site && tar -C /var/www/landings -xf -", tar)
    ssh("cat > /etc/nginx/sites-available/landings && ln -sf /etc/nginx/sites-available/landings "
        "/etc/nginx/sites-enabled/landings && nginx -t && systemctl reload nginx", NGINX.encode())
    ssh("cat > /opt/traefik-config/dynamic/landings.yml", traefik(slugs).encode())
    print("\n".join(f"https://{s}.{DOM}/" for s in [HUB] + slugs))


if __name__ == "__main__":
    main()
