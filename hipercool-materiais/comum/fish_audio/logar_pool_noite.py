"""Noite 19/11 (dona: "logue também as contas que faltam"). Tenta o login de cada conta do pool SEM sessão, UMA por vez,
espaçado (10 min entre contas — muitos logins seguidos é o que mais chama atenção), cada uma pelo IP fixo dela.
Usa o login_fish.py (o jeito que funcionou na 1ª e na 2ª conta). Se a tela pedir verificação/captcha, PARA aquela
conta (regra: captcha em conta nova = parar, nunca contornar) e segue para a próxima depois do intervalo.
Logou = sessoes_fish.registrar_conta (rodízio + saldo). Para às 6h40. Log: logar_pool_noite.log"""
import subprocess, sys, time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, r"D:\logins-google")
LOG = AQUI / "logar_pool_noite.log"
PY = r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"
FIM = datetime.now().replace(hour=6, minute=40, second=0)
if FIM < datetime.now():
    FIM = FIM.replace(day=FIM.day + 1)


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(datetime.now().strftime("%H:%M ") + m + "\n")


import pool_fish, creditos  # noqa: E402

feitas = set()
log("=== início")
while datetime.now() < FIM:
    reg = creditos.carregar()
    faltam = [e for e in sorted(pool_fish.pool_atual()) if not (reg.get(e) or {}).get("logado") and e not in feitas]
    if not faltam:
        log("todas tentadas")
        break
    email = faltam[0]
    feitas.add(email)
    # trava: não briga com uma narração em andamento
    import fish_lote
    if not fish_lote._travar(prazo=300):
        log(f"{email}: trava ocupada — tento depois")
        feitas.discard(email)
        time.sleep(300)
        continue
    try:
        r = subprocess.run([PY, "-X", "utf8", str(AQUI / "login_fish.py"), email], capture_output=True, text=True,
                           timeout=420, encoding="utf-8", errors="replace")
        saida = (r.stdout or "").strip().splitlines()[-1:] or [f"rc={r.returncode}"]
        log(f"{email}: {saida[0][:150]}")
        if "LOGADO" in saida[0]:
            try:
                import sessoes_fish
                log(f"{email}: registrar -> {str(sessoes_fish.registrar_conta(email))[:120]}")
            except Exception as e:  # noqa: BLE001
                creditos.marcar(email, logado=True, erro=None)
                log(f"{email}: registrar falhou ({type(e).__name__}) — marcada logada no creditos")
    except subprocess.TimeoutExpired:
        log(f"{email}: login passou de 7 min — desisto desta")
    finally:
        fish_lote._soltar()
    time.sleep(600)
log("=== fim")
