# -*- coding: utf-8 -*-
r"""proxy_celular.py — o celular (Redmi A3, Tailscale 100.87.168.9, Termux sshd :8022) vira proxy SOCKS5 do PC1 em
127.0.0.1:18210, por `ssh -D`. O que sai por ele sai pela internet DO CELULAR: com chip de dados (Wi-Fi desligado) é IP
de operadora, residencial/móvel de verdade e diferente do de casa; só no Wi-Fi é o mesmo IP de casa (aí não serve de
teste e `vivo()` diz não). Pedido da dona 29/10: "ponha pra usar o celular como proxy pra testarmos nos canais mortos".

ANTES DE MUDAR: ler D20 em D:\hipercool-materiais\tarefas complexas para fable 5.1\FABLE_DECISOES.md.

    python bin\proxy_celular.py --vez      # tarefa ProxyCelular (a cada 5 min): sobe/mantém o túnel e mede a saída
    python bin\proxy_celular.py --status   # o que está gravado em config\proxy_celular.json

Quem usa: proxy_tiktok (PAC "celular.pac" -> SOCKS5 127.0.0.1:18210) e postar_tiktok_auto (contas em
config\proxy_celular.json "contas_teste"). Sem túnel vivo tudo segue como antes (Webshare ou internet de casa).
Limite diário de MB em "mb_dia" (chip pré-pago): passou, `vivo()` diz não até o dia virar.
"""
import json
import os
import socket
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

SSH_EXE = r"C:\Program Files\Git\usr\bin\ssh.exe" if __import__("os").path.exists(r"C:\Program Files\Git\usr\bin\ssh.exe") else "ssh"  # 29/10 (Fable): sob tarefa agendada o "ssh" do PATH e o OpenSSH do Windows, que trava ate o timeout

sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: F401
except ImportError:
    pass

CELULAR = os.environ.get("PROXY_CELULAR_HOST", "100.87.168.9")
PORTA_SSH = int(os.environ.get("PROXY_CELULAR_SSH", "8022"))
PORTA_SOCKS = 18210
CFG = Path(r"D:\postador-de-videos\config\proxy_celular.json")
CURL = r"C:\Windows\System32\curl.exe"
PADRAO = {"contas_teste": [], "mb_dia": 300, "aceitar_igual_casa": False}


def _ler():
    try:
        d = json.loads(CFG.read_text("utf-8"))
    except (OSError, ValueError):
        d = {}
    return {**PADRAO, **d}


def _gravar(d):
    CFG.parent.mkdir(parents=True, exist_ok=True)
    CFG.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")


def _porta_aberta(host, p, t=4):
    try:
        socket.create_connection((host, p), timeout=t).close()
        return True
    except OSError:
        return False


def _curl(args, t=15):
    try:
        r = subprocess.run([CURL, "-s", "--max-time", str(t), *args], capture_output=True, text=True, timeout=t + 5)
        return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _subir_tunel():
    if _porta_aberta("127.0.0.1", PORTA_SOCKS, 1):
        return True
    if not _porta_aberta(CELULAR, PORTA_SSH, 5):
        return False
    cmd = [SSH_EXE, "-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=20",
           "-o", "ServerAliveCountMax=3", "-o", "ConnectTimeout=15", "-o", "StrictHostKeyChecking=accept-new",
           "-o", "LogLevel=ERROR", "-p", str(PORTA_SSH), "-D", f"127.0.0.1:{PORTA_SOCKS}", CELULAR]
    subprocess.Popen(cmd, creationflags=0x00000008 | 0x00000200 | 0x08000000, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(20):
        time.sleep(0.5)
        if _porta_aberta("127.0.0.1", PORTA_SOCKS, 1):
            return True
    return False


def medir():
    """Mede a saída do túnel e grava o estado. Devolve o estado."""
    c = _ler()
    est = c.get("estado") or {}
    agora = datetime.now().isoformat(timespec="seconds")
    tunel = _subir_tunel()
    novo = {"atualizado": agora, "celular_alcancavel": _porta_aberta(CELULAR, PORTA_SSH, 4), "tunel": tunel}
    if tunel:
        ip = _curl(["--socks5-hostname", f"127.0.0.1:{PORTA_SOCKS}", "https://api.ipify.org"])
        casa = _curl(["https://api.ipify.org"])
        novo.update({"ip": ip or None, "ip_casa": casa or None, "igual_casa": bool(ip) and ip == casa})
        if ip and ip != est.get("ip"):
            info = _curl(["--socks5-hostname", f"127.0.0.1:{PORTA_SOCKS}",
                          f"http://ip-api.com/json/{ip}?fields=isp,org,mobile,countryCode,city"])
            try:
                j = json.loads(info)
                novo.update({"operadora": j.get("isp") or j.get("org"), "movel": j.get("mobile"),
                             "pais": j.get("countryCode"), "cidade": j.get("city")})
            except ValueError:
                pass
        else:
            for k in ("operadora", "movel", "pais", "cidade"):
                if k in est:
                    novo[k] = est[k]
        if not ip:
            novo["tunel"] = False
    hoje = str(date.today())
    uso = c.get("uso_mb") or {}
    novo["mb_hoje"] = round(uso.get(hoje, 0), 1)
    c["estado"] = novo
    c["uso_mb"] = {d: v for d, v in uso.items() if d >= hoje[:8] + "01" or d == hoje}
    _gravar(c)
    return novo


def somar_mb(mb):
    c = _ler()
    uso = c.setdefault("uso_mb", {})
    uso[str(date.today())] = round(uso.get(str(date.today()), 0) + mb, 1)
    _gravar(c)


def vivo(conta=None):
    """True = dá para mandar esta conta pelo celular agora: túnel medido há < 15 min, saída diferente da de casa (ou
    aceitar_igual_casa), MB do dia não estourado e, se conta vier, ela está em contas_teste."""
    c = _ler()
    e = c.get("estado") or {}
    try:
        idade = (datetime.now() - datetime.fromisoformat(e.get("atualizado"))).total_seconds()
    except (TypeError, ValueError):
        return False
    if idade > 900 or not e.get("tunel") or not e.get("ip"):
        return False
    if e.get("igual_casa") and not c.get("aceitar_igual_casa"):
        return False
    if (c.get("uso_mb") or {}).get(str(date.today()), 0) >= c.get("mb_dia", 300):
        return False
    return conta is None or conta in (c.get("contas_teste") or [])


def placar():
    """Monitor do teste (dona 29/10: "monitoramento pra ver se está dando certo"): posts do TikTok desde o início do
    teste separados por caminho (celular × webshare/casa), cruzados com as views de 48 h que o notificar_telegram mede
    (telegram_estado.medidas_48h_tiktok, por caminho do arquivo). Dá certo = os posts pelo celular saem do 0."""
    import statistics
    c = _ler()
    inicio = c.get("inicio_teste") or "2026-10-29"
    try:
        posts = json.loads(Path(r"D:\postador-de-videos\logs\tiktok_auto_posted.json").read_text("utf-8"))
    except (OSError, ValueError):
        posts = []
    if not isinstance(posts, list):
        posts = []
    try:
        med = (json.loads(Path(r"D:\postador-de-videos\config\telegram_estado.json").read_text("utf-8"))
               .get("medidas_48h_tiktok") or {})
    except (OSError, ValueError):
        med = {}
    por_arquivo = {}
    for m in med.values():
        if m.get("path"):
            por_arquivo[str(m["path"]).lower()] = m
    grupos = {"celular": [], "outros": []}
    por_conta = {}
    hoje = str(date.today())
    hoje_celular = 0
    for p in posts:
        if (p.get("timestamp") or "") < inicio:
            continue
        via = p.get("via") or "casa"
        g = "celular" if via == "celular" else "outros"
        m = por_arquivo.get(str(p.get("path") or "").lower())
        item = {"conta": p.get("account"), "arquivo": p.get("file"), "quando": p.get("timestamp"), "via": via,
                "views48": (m or {}).get("views"), "medido": m is not None}
        grupos[g].append(item)
        pc = por_conta.setdefault(p.get("account"), {"posts": 0, "celular": 0, "medidos": 0, "com_view": 0, "views": 0})
        pc["posts"] += 1
        pc["celular"] += via == "celular"
        if m is not None:
            pc["medidos"] += 1
            pc["com_view"] += (m.get("views") or 0) > 0
            pc["views"] += m.get("views") or 0
        if via == "celular" and (p.get("timestamp") or "").startswith(hoje):
            hoje_celular += 1

    def resumo(lst):
        med_ = [x["views48"] for x in lst if x["medido"]]
        return {"posts": len(lst), "medidos": len(med_), "com_view": sum(1 for v in med_ if (v or 0) > 0),
                "pct_com_view": round(100 * sum(1 for v in med_ if (v or 0) > 0) / len(med_)) if med_ else None,
                "mediana_views": statistics.median(med_) if med_ else None, "total_views": sum(v or 0 for v in med_)}
    e = c.get("estado") or {}
    return {"inicio_teste": inicio, "estado": e, "vivo_agora": vivo(), "contas_teste": c.get("contas_teste") or [],
            "hoje_pelo_celular": hoje_celular, "mb_hoje": e.get("mb_hoje"), "mb_dia": c.get("mb_dia"),
            "celular": resumo(grupos["celular"]), "outros": resumo(grupos["outros"]),
            "por_conta": por_conta, "ultimos_celular": sorted(grupos["celular"], key=lambda x: x["quando"] or "")[-30:]}


def flags():
    return [f"--proxy-server=socks5://127.0.0.1:{PORTA_SOCKS}", "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1",
            "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]


def main(a):
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--placar" in a:
        print(json.dumps(placar(), ensure_ascii=False, indent=1))
        return 0
    if "--status" in a:
        c = _ler()
        print(json.dumps({"estado": c.get("estado"), "contas_teste": c.get("contas_teste"), "mb_dia": c.get("mb_dia"),
                          "vivo_agora": vivo()}, ensure_ascii=False, indent=1))
        return 0
    e = medir()
    print(json.dumps(e, ensure_ascii=False))
    return 0  # celular fora não é erro da tarefa (o estado fica no json; antes devolvia 1 e a tarefa parecia quebrada)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
