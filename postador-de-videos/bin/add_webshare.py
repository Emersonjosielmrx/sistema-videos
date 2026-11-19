r"""add_webshare.py — põe contas NOVAS da Webshare (grátis, 1 GB/mês) no rodízio do TikTok/Instagram (dona 19/11: "faça o
que der enquanto eu faço mais contas"; 71 de 72 contas sem banda -> 77 erros de TikTok no dia).

    python add_webshare.py USUARIO:SENHA [USUARIO:SENHA ...]
    python add_webshare.py --arquivo novas.txt        # 1 por linha: USUARIO:SENHA  ou  a linha inteira do painel
                                                      #   (http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80)
    python add_webshare.py --status                   # quantas contas no pool, quantas com banda agora

O que faz com cada conta: (1) testa 1 CONNECT pelo IP 1 (200 = tem banda; 402 = sem banda; 407 = senha errada — não
entra); (2) grava em secrets\proxies.txt ANTES das últimas RESERVA_GROQ linhas (essas são do Groq e não mudam);
(3) reinicia o repassador proxy_tiktok (ele só lê o pool ao subir). Backup do proxies.txt antes. Não mostra senha.
Conta repetida é ignorada. Só fala com p.webshare.io pela internet de casa — é o login DA WEBSHARE, não conta Google.
"""
import base64
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proxy_tiktok as px  # noqa: E402

RX = re.compile(r"^(?:https?://)?([A-Za-z0-9_]+?)(?:-rotate|-\d+)?:([^@\s]+)(?:@p\.webshare\.io(?::80)?)?$")


def _ler(arg):
    m = RX.match(arg.strip())
    return (m.group(1), m.group(2)) if m else None


def testar(user, senha, n=1):
    """Status HTTP do CONNECT pelo IP n (200 ok, 402 sem banda, 407 senha errada, 0 sem resposta)."""
    try:
        s = socket.create_connection(px.UPSTREAM, timeout=20)
        auth = base64.b64encode(f"{user}-{n}:{senha}".encode()).decode()
        s.sendall(f"CONNECT www.tiktok.com:443 HTTP/1.1\r\nHost: www.tiktok.com:443\r\n"
                  f"Proxy-Authorization: Basic {auth}\r\n\r\n".encode())
        s.settimeout(30)
        r = s.recv(200)
        s.close()
        return int(r.split()[1])
    except (OSError, IndexError, ValueError):
        return 0


def _reiniciar_repassador():
    ps = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'proxy_tiktok.py' -and "
          "$_.CommandLine -notmatch 'add_webshare' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, creationflags=0x08000000)
    time.sleep(2)
    return px.garantir()


def status():
    pool = px.credenciais()
    px._ler_estado()
    agora = datetime.now().isoformat(timespec="minutes")
    vivas = [u for u, _s in pool if px._estado["mortas"].get(u, {}).get("ate", "") <= agora]
    print(f"pool TikTok/IG: {len(pool)} contas | sem marca de 'sem banda' agora: {len(vivas)}")


def main():
    if "--status" in sys.argv:
        return status()
    args = sys.argv[1:]
    if "--arquivo" in args:
        i = args.index("--arquivo")
        linhas = Path(args[i + 1]).read_text(encoding="utf-8").splitlines()
        args = args[:i] + linhas + args[i + 2:]
    novas = [c for c in (_ler(a) for a in args if a.strip() and not a.startswith("--")) if c]
    if not novas:
        print(__doc__)
        return 1
    linhas = px.PROXIES.read_text(encoding="utf-8").splitlines()
    ja = {m.group(1) for m in (RX.match(l.strip()) for l in linhas) if m}
    entra, falas = [], []
    for user, senha in novas:
        if user in ja:
            falas.append(f"{user[:4]}…: já estava no pool")
            continue
        st = testar(user, senha)
        if st == 407:
            falas.append(f"{user[:4]}…: senha recusada (407) — NÃO entrou")
            continue
        entra.append(f"http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80")
        ja.add(user)
        falas.append(f"{user[:4]}…: {'OK com banda' if st == 200 else f'entrou (teste deu {st})'}")
    for f in falas:
        print(f)
    if not entra:
        print("nada novo para gravar")
        return 0
    bak = px.PROXIES.with_name(f"proxies.txt.bkp_{datetime.now():%Y%m%d_%H%M}")
    shutil.copy2(px.PROXIES, bak)
    corte = max(0, len(linhas) - px.RESERVA_GROQ)  # as últimas RESERVA_GROQ ficam com o Groq
    novo = linhas[:corte] + entra + linhas[corte:]
    px.PROXIES.write_text("\n".join(novo) + "\n", encoding="utf-8")
    print(f"gravadas {len(entra)} conta(s) (backup {bak.name}); reiniciando o repassador...")
    print("repassador no ar" if _reiniciar_repassador() else "ATENÇÃO: repassador não subiu")
    status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
