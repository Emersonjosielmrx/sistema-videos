"""Saúde do Facebook antes de cada rodada — conserta sozinho o que hoje só se resolvia com alguém olhando (23/11/2026,
dona: "todos acompanhados pelo vigia pra manter tudo funcionando e não precisando do chat; quero fechar e saber que
tudo vai receber postagem").

1) Ponte de proxy da conta (127.0.0.1:185NN -> Webshare rnprmtfo-NN): se não responde, mata o dono da porta e sobe
   de novo (23/11 as 2 pontes penduraram e nada postou das 12h às 15h). Nunca troca a saída e nunca cai para a casa.
2) Trava logs/fb_postando_<conta>.lock cujo processo já morreu: apaga (23/11 travas mortas seguraram contas livres).
3) livre(conta): False se a conta já tem rodada viva (nunca 2 rodadas na mesma conta).

    python fb_saude.py            # confere e conserta todas as contas com Páginas ativas
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BIN = Path(__file__).resolve().parent
LOGS = BIN.parent / "logs"
CFG = BIN.parent / "config" / "facebook_paginas.json"
PONTE = r"D:\recapd-ambientes\producao\colab\ponte_proxy_fixo.py"
PYW = r"D:\veo\venv\Scripts\pythonw.exe"
SEM_JANELA = 0x08000000


def _pid_vivo(pid):
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {int(pid)}", "/NH"], capture_output=True,
                             timeout=30, creationflags=SEM_JANELA).stdout
        out = (out or b"").decode("latin-1", errors="ignore")
        return str(int(pid)) in out
    except Exception:  # noqa: BLE001
        return True  # na dúvida, não apaga trava de ninguém


def trava(conta):
    """(pid, quando) da trava viva da conta, ou None. Trava de processo morto é apagada aqui."""
    f = LOGS / f"fb_postando_{conta}.lock"
    if not f.exists():
        return None
    try:
        pid, quando = f.read_text(encoding="utf-8").strip().split("|", 1)
    except (OSError, ValueError):
        return None
    if _pid_vivo(pid):
        return pid, quando
    try:
        f.unlink()
        print(f"[saude] {conta}: trava de processo morto ({pid}) apagada", flush=True)
    except OSError:
        pass
    return None


def livre(conta):
    """Livre para a RODADA DE POSTAGEM: sem trava, ou com trava da CRIAÇÃO de Página (a postagem vai só pela API)."""
    t = trava(conta)
    if t is None:
        return True
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(t[0])}').CommandLine"],
                             capture_output=True, timeout=60, creationflags=SEM_JANELA).stdout
        return "fb_criar_fila" in (out or b"").decode("latin-1", errors="ignore")
    except Exception:  # noqa: BLE001
        return False


def _ponte_ok(porta):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": f"http://127.0.0.1:{porta}"}))
    for _ in range(2):
        try:
            return op.open("http://api.ipify.org", timeout=20).status == 200
        except Exception:  # noqa: BLE001
            time.sleep(3)
    return False


def _dono_da_porta(porta):
    # 24/11: netstat sai em cp850/cp1252; com PYTHONUTF8=1 o text=True quebrava (stdout=None) e a ponte não religava
    out = subprocess.run(["netstat", "-ano"], capture_output=True, timeout=30, creationflags=SEM_JANELA).stdout
    out = (out or b"").decode("latin-1", errors="ignore")
    for linha in out.splitlines():
        p = linha.split()
        if len(p) >= 5 and p[1] == f"127.0.0.1:{porta}" and p[3] == "LISTENING":
            return p[4]
    return None


def ponte(conta, saida):
    """Garante a ponte da saída fixa da conta (rnprmtfo-NN -> porta 18500+NN). True = respondendo."""
    if not str(saida).startswith("rnprmtfo-"):
        return True  # casa (msenergypara) não usa ponte
    n = int(str(saida).split("-")[1])
    porta = 18500 + n
    if _ponte_ok(porta):
        return True
    pid = _dono_da_porta(porta)
    if pid:
        subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, creationflags=SEM_JANELA)
        time.sleep(2)
    subprocess.Popen([PYW, PONTE, str(n), str(porta)], creationflags=SEM_JANELA, close_fds=True)
    for _ in range(10):
        time.sleep(2)
        if _ponte_ok(porta):
            print(f"[saude] {conta}: ponte {saida} (porta {porta}) estava caída — religada", flush=True)
            _avisar(f"Facebook: a ponte {saida} da conta {conta} tinha caído e foi religada sozinha.", importante=False)
            return True
    print(f"[saude] {conta}: ponte {saida} NÃO voltou — conta fica fora desta rodada", flush=True)
    _avisar(f"Facebook: a ponte {saida} da conta {conta} caiu e não voltou. A conta fica sem postar até voltar.",
            importante=True)
    return False


def _avisar(msg, importante):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(msg, "facebook-saude", importante=importante)
    except Exception:  # noqa: BLE001
        pass


def contas_ativas():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    ativas = {p["conta"] for p in cfg["paginas"].values() if not p.get("pausada")} - {"msenergypara"}
    return {c: cfg["contas"][c] for c in sorted(ativas)}


def conferir():
    """{conta: pronta?} — ponte ok e sem rodada viva."""
    out = {}
    for conta, c in contas_ativas().items():
        ok = ponte(conta, c.get("saida"))
        out[conta] = ok and livre(conta)
        print(f"[saude] {conta}: ponte {'ok' if ok else 'CAÍDA'} | {'livre' if livre(conta) else 'rodada no ar'}", flush=True)
    return out


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    conferir()
