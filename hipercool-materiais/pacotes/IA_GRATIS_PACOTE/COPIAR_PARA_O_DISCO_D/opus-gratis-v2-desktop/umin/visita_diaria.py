# -*- coding: utf-8 -*-
r"""visita_diaria.py — resgata a "Daily Visit" do 1min.ai (15.000 créditos/dia) da conta de teste.

O 1min dá 15 mil créditos por dia só por abrir o site logado (o dia vira à meia-noite de Los Angeles = 4h/5h aqui).
Este script abre o Chrome da conta pelo cofre e entra em app.1min.ai/free-credits por uma janela própria (cdp.mjs).
Se a sessão do site caiu, ele reloga com o Google. Depois lê o saldo da tela, acerta a base do umin.py (que passa a
dar o saldo exato) e fecha só o que abriu. Grava uma linha por execução em visitas.jsonl.
  python visita_diaria.py             # visita agora
  python visita_diaria.py --agendar   # (re)cria a tarefa "1min visita diaria" (todo dia 06:10, prioridade 6)
Tirar a tarefa:  schtasks /Delete /TN "1min visita diaria" /F
"""
import json
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import umin  # noqa: E402

CONTA = "sua_conta@gmail.com"
URL = "https://app.1min.ai/free-credits"
LOG = AQUI / "visitas.jsonl"
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
SEM_JANELA = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW: a tarefa das 6h não pisca console
TAREFA = "1min visita diaria"


def cdp(porta, *args, timeout=200):
    r = subprocess.run([NODE, str(AQUI / "cdp.mjs"), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, cwd=AQUI, creationflags=SEM_JANELA,
                       env={**os.environ, "CDP_PORTA": str(porta)})
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def estado_login(porta):
    _, out = cdp(porta, "jsf", str(AQUI / "js" / "login.js"))
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"logado": False, "erro": out[-300:]}


def relogar(porta, conta=CONTA):
    """Log In -> Log in with Google -> popup do Google -> clica a conta (o popup fecha sozinho quando termina)."""
    cdp(porta, "clicar", "Log In", "4")
    _, out = cdp(porta, "clicar", "Log in with Google", "8")
    if "ERRO" in out:  # o "Log In" do topo às vezes não abre o quadro pelo texto: tenta pela posição do botão
        cdp(porta, "clicarxy", "1128", "33", "4")
        cdp(porta, "clicar", "Log in with Google", "8")
    cod, _ = cdp(porta, "usar", "accounts.google.com")
    if cod == 0:
        cdp(porta, "clicar", conta, "8")
    cdp(porta, "voltar")
    cdp(porta, "ir", URL, "10")


def calibrar(saldo, conta=CONTA):
    """31/10: com o rodízio, acerta a conta no umin_contas.json (base = saldo da TELA + usado). O saldo da tela é o real:
    conta também as respostas vazias que o 1min cobra e o crédito da visita."""
    contas = umin._contas()
    achou = False
    for c in contas:
        if c.get("email", c["apelido"]).lower() == conta.lower() or c["apelido"].lower() == conta.lower():
            c["base"] = saldo + (c.get("usado") or 0)
            if saldo >= umin.CUSTO_MIN:
                c["sem_cota_ate"] = None
            c["visto_em"] = datetime.now().isoformat(timespec="minutes")
            achou = True
    if achou:
        umin._gravar_contas(contas)
    st = umin._estado()  # compat: estado antigo de conta única (conta_exemplo)
    if conta == CONTA and "usado" in st:
        st["base"] = saldo + st["usado"]
        umin._gravar_estado(st)


def visitar(conta=CONTA):
    res = {"em": datetime.now().isoformat(timespec="seconds"), "conta": conta}
    porta, proc = cofre.abrir(conta)
    res["chrome"] = "aberto por mim" if proc else "já estava aberto"
    try:
        cdp(porta, "ir", URL, "10")
        st = estado_login(porta)
        if not st.get("logado"):
            res["relogou"] = True
            relogar(porta, conta)
            st = estado_login(porta)
        res["logado"] = bool(st.get("logado"))
        if st.get("creditos"):
            res["saldo"] = int(str(st["creditos"]).replace(",", "").replace(".", ""))
            calibrar(res["saldo"], conta)
    finally:
        cdp(porta, "fechar")
        if proc:  # fomos nós que abrimos: fecha gravando os cookies (senão o login do site some de novo)
            cdp(porta, "encerrar")
            cofre.fechar(proc, nome=conta)
    return res


def contas_do_rodizio():
    """Todas as contas do umin_contas.json que têm chave + a conta_exemplo."""
    vistos, lista = set(), []
    for c in umin._contas():
        email = c.get("email") or (c["apelido"] if "@" in c["apelido"] else c["apelido"] + "@gmail.com")
        if c.get("chave") and email.lower() not in vistos:
            vistos.add(email.lower())
            lista.append(email)
    if CONTA.lower() not in vistos:
        lista.insert(0, CONTA)
    return lista


def agendar():
    pyw = Path(sys.executable).with_name("pythonw.exe")
    ps = (f"$a = New-ScheduledTaskAction -Execute '{pyw}' -Argument '\"{AQUI / 'visita_diaria.py'}\"' -WorkingDirectory '{AQUI}';"
          "$t = New-ScheduledTaskTrigger -Daily -At 06:10;"
          "$s = New-ScheduledTaskSettingsSet -Priority 6 -ExecutionTimeLimit (New-TimeSpan -Hours 2) -StartWhenAvailable"
          " -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries;"
          f"Register-ScheduledTask -TaskName '{TAREFA}' -Action $a -Trigger $t -Settings $s -Force"
          f" -Description 'Resgata os 15 mil creditos/dia do 1min.ai (conta conta_exemplo). {AQUI}\\visita_diaria.py' | Out-Null;"
          f"(Get-ScheduledTask -TaskName '{TAREFA}').State")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=120)
    print((r.stdout + r.stderr).strip() or "sem saída")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--agendar" in sys.argv:
        agendar()
        raise SystemExit
    # 31/10: visita TODAS as contas do rodízio, uma por vez (1 Chrome por vez — RAM). Uma só: visita_diaria.py a@x.com
    alvos = [a for a in sys.argv[1:] if "@" in a] or contas_do_rodizio()
    for conta in alvos:
        try:
            r = visitar(conta)
        except Exception as e:  # noqa: BLE001  (pela tarefa não há console: o erro vai para o visitas.jsonl)
            r = {"em": datetime.now().isoformat(timespec="seconds"), "conta": conta, "erro": f"{type(e).__name__}: {e}",
                 "onde": traceback.format_exc().splitlines()[-3:]}
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(json.dumps(r, ensure_ascii=False), flush=True)
