"""Medidor da cota das contas Claude (rota cc/, onde roda o Opus 5.5) no OmniRoute — SÓ LÊ (24/10, plano Opus 5.5).

Lê por ssh (host "hermes-bloqueio", sqlite em modo somente leitura, igual ao D:\\monitor_opus.py) a última leitura de
cada conta Claude ativa nas janelas "session (5h)" e "weekly (7d)" e grava estado\\cota_claude.json:
  contas, com_cota (sessão e semana sem esgotar), semana_pct_total (soma do que sobra na semana, em "contas"),
  quase_vencendo (contas com >= QUASE_PCT da semana sobrando que renovam em <= QUASE_H: token que vai se perder),
  proxima_volta, leitura_em.
Uso: python cota_claude.py [--seco]  (--seco: só imprime, não grava)
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ESTADO = BASE / "estado" / "cota_claude.json"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
QUASE_PCT = 30   # sobra de pelo menos 30% da semana...
QUASE_H = 24     # ...que renova em até 24 h = vale ligar o ASSUMIR (aviso; quem liga é a dona)
VELHA_H = 6      # leitura de conta mais velha que isso não conta

CONSULTA = r'''
import json,sqlite3,datetime
db=sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
agora=datetime.datetime.now(datetime.timezone.utc)
desde=(agora-datetime.timedelta(hours=%d)).strftime("%%Y-%%m-%%dT%%H:%%M:%%S")
ativas={r[0] for r in db.execute("select id from provider_connections where provider='claude' and is_active=1")}
out={}
for cid,wk,pct,ex,nr,em in db.execute("""select s.connection_id,s.window_key,s.remaining_percentage,s.is_exhausted,
  s.next_reset_at,s.created_at from quota_snapshots s join (select connection_id,window_key,max(id) mid
  from quota_snapshots where provider='claude' and created_at>? group by connection_id,window_key) u on s.id=u.mid""",(desde,)):
    if cid in ativas:
        out.setdefault(cid,{})[wk]={"pct":pct,"esgotada":bool(ex),"renova":nr,"em":em}
print(json.dumps({"ativas":len(ativas),"contas":out}))
''' % VELHA_H


def ler():
    """Dict bruto do OmniRoute ou None."""
    try:
        r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "hermes-bloqueio", "python3", "-"],
                           input=CONSULTA.encode(), capture_output=True, timeout=90)
        return json.loads(r.stdout.decode())
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def resumir(bruto, agora=None):
    agora = agora or datetime.now(timezone.utc)
    contas = bruto.get("contas") or {}
    com, quase, soma, voltas = 0, 0, 0.0, []
    for jan in contas.values():
        s, w = jan.get("session (5h)") or {}, jan.get("weekly (7d)") or {}
        livre_s = s and not s.get("esgotada") and float(s.get("pct") or 0) > 0
        livre_w = w and not w.get("esgotada") and float(w.get("pct") or 0) > 0
        if livre_s and livre_w:
            com += 1
        if livre_w:
            soma += float(w["pct"]) / 100
            try:
                renova = datetime.fromisoformat(str(w["renova"]).replace("Z", "+00:00"))
                if float(w["pct"]) >= QUASE_PCT and renova - agora <= timedelta(hours=QUASE_H):
                    quase += 1
            except (TypeError, ValueError):
                pass
        for j in (s, w):
            if j.get("esgotada") and j.get("renova"):
                voltas.append(str(j["renova"]))
    futuras = sorted(v for v in voltas if v > agora.strftime("%Y-%m-%dT%H:%M:%S"))
    return {"leitura_em": datetime.now().astimezone().isoformat(timespec="seconds"), "ativas": bruto.get("ativas"),
            "contas_lidas": len(contas), "com_cota": com, "semana_contas_livres": round(soma, 2),
            "quase_vencendo": quase, "proxima_volta": futuras[0] if futuras else None}


def gravar(res):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(res, indent=1), encoding="utf-8")
    os.replace(tmp, ESTADO)


def atual(max_min=30):
    """O que foi gravado, se tiver no máximo max_min minutos (senão None = conta como sem cota)."""
    try:
        d = json.loads(ESTADO.read_text(encoding="utf-8"))
        idade = (datetime.now().astimezone() - datetime.fromisoformat(d["leitura_em"])).total_seconds() / 60
        return d if idade <= max_min else None
    except (OSError, ValueError, KeyError):
        return None


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    b = ler()
    if b is None:
        print("sem dados do OmniRoute")
        sys.exit(1)
    r = resumir(b)
    if "--seco" not in sys.argv:
        gravar(r)
    print(json.dumps(r, ensure_ascii=False))
