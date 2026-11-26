r"""D:\recapd-ambientes\producao\colab\logar_colab_contas.py (PC1) — 26/11 noite.
Abre, UMA POR VEZ e VISÍVEL, as contas Google liberadas para o Colab (LIVRES do abrir_colab_teste.py), cada uma pelo
IP fixo dela (ponte_proxy_fixo.py N -> 127.0.0.1:183NN; nunca pela internet de casa), já na tela de login com volta
para o Colab. A dona digita a senha, confere que o Colab abriu e FECHA o Chrome; aí abre a próxima.

- Conta com Chrome já aberto (CDP vivo, ex.: solarmundo195 em uso por outro projeto) = PULA, não fecha à força
  (foi o _fechar_porta que derrubou a filmescomia1 em 26/11).
- Enquanto o Chrome está aberto, lê as abas pelo CDP (/json, sem Playwright) a cada 3 s; ao fechar grava no log se a
  última aba estava no Colab (logada) ou ainda no accounts.google.com (não logou).
- TEM que rodar na sessão interativa (tarefa agendada InteractiveToken, usuário Haylla), NUNCA por ssh: Chrome aberto
  pelo OpenSSH apaga os cookies (memória cofre-nunca-via-ssh).

Uso:  pythonw logar_colab_contas.py [apelido ...]     (sem argumentos = as 9, menos as abertas)
Log:  D:\recapd-ambientes\producao\colab\logar_colab_contas.log
Para: criar D:\recapd-ambientes\producao\colab\logar_colab_PARAR (não abre a próxima)
"""
import json
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

AQUI = Path(__file__).resolve().parent
LOG = AQUI / "logar_colab_contas.log"
PARAR = AQUI / "logar_colab_PARAR"
LIVRES = {"filmescomia1": 27, "fabricadeautomacoes0": 25, "fabricadeautomacoesia": 26, "inovaremanhwaverseesp": 31,
          "jogoscomia": 34, "jornalcomia": 35, "solarmundo195": 71, "vendeafiliados3": 5, "entrevistacomia": 23}
URL = "https://accounts.google.com/ServiceLogin?continue=https%3A%2F%2Fcolab.research.google.com%2F"


def log(m):
    linha = f"{datetime.now():%d/%m %H:%M:%S} {m}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    if sys.stdout:
        print(linha, flush=True)


def ponte(n):
    porta = 18300 + n

    def viva():
        try:
            socket.create_connection(("127.0.0.1", porta), timeout=2).close()
            return True
        except OSError:
            return False
    if not viva():
        subprocess.Popen([sys.executable, str(AQUI / "ponte_proxy_fixo.py"), str(n), str(porta)],
                         creationflags=0x08000000)
        for _ in range(20):
            time.sleep(1)
            if viva():
                break
        else:
            raise RuntimeError(f"ponte do rnprmtfo-{n} não subiu — não abro pela internet de casa")
    return porta


def abas(porta):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/json", timeout=3) as r:
            return [a.get("url", "") for a in json.loads(r.read()) if a.get("type") == "page"]
    except Exception:  # noqa: BLE001
        return None


def estado(urls):
    if not urls:
        return "sem abas lidas"
    if any("colab.research.google.com" in u for u in urls):
        return "LOGADA (Colab abriu)"
    if any("accounts.google.com" in u for u in urls):
        return "NAO LOGOU (parou no login do Google)"
    return "incerto: " + " | ".join(u[:80] for u in urls)


def main(lista):
    PARAR.unlink(missing_ok=True)
    log(f"=== início: {len(lista)} contas: {', '.join(lista)} ===")
    resumo = []
    for i, apelido in enumerate(lista, 1):
        if PARAR.exists():
            log("PARAR encontrado — fim")
            break
        if apelido not in LIVRES:
            log(f"[{i}] {apelido}: não está nas LIVRES — pulei")
            continue
        n = LIVRES[apelido]
        try:
            _, e = cofre.conta(apelido)
            if cofre._cdp_vivo(e["porta"]):
                log(f"[{i}] {apelido}: Chrome já aberto (porta {e['porta']}, outro projeto?) — pulei, não fecho à força")
                resumo.append((apelido, "pulada (aberta)"))
                continue
            pp = ponte(n)
            flags = [f"--proxy-server=http://127.0.0.1:{pp}", "--proxy-bypass-list=<-loopback>",
                     "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
            porta, proc = cofre.abrir(apelido, url=URL, visivel=True, extra=flags)
        except Exception as ex:  # noqa: BLE001
            log(f"[{i}] {apelido}: ERRO ao abrir: {type(ex).__name__}: {ex}")
            resumo.append((apelido, "erro ao abrir"))
            continue
        if proc is None:
            log(f"[{i}] {apelido}: já aberta em outra porta — pulei")
            resumo.append((apelido, "pulada (aberta)"))
            continue
        log(f"[{i}/{len(lista)}] {apelido}: Chrome aberto (porta {porta}, rnprmtfo-{n}). Esperando logar e fechar...")
        ultimas = None
        while proc.poll() is None:
            u = abas(porta)
            if u:
                ultimas = u
            time.sleep(3)
        st = estado(ultimas)
        log(f"[{i}] {apelido}: fechou — {st}")
        resumo.append((apelido, st))
        try:
            cofre.fechar(proc, None, apelido)
            cofre._marcar(f"{apelido}@gmail.com", colab_login=st, colab_login_em=datetime.now().isoformat(timespec="minutes"))
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3)
    log("=== fim === " + "; ".join(f"{a}: {s}" for a, s in resumo))


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:] or list(LIVRES))
