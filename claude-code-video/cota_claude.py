"""Gerente de cota das contas Claude pagas (Claude Pro) do OmniRoute — usado pelos DOIS projetos:
  D:\\claude-code-video            (vídeo do zero: só começa com cota DE CERTEZA)
  D:\\claude-code-video-adicional  (motor extra dos projetos: decide antes de cada vídeo se liga)

Fonte: banco do OmniRoute na 157 (ssh hermes-bloqueio, só leitura), provedor 'claude':
  quota_snapshots  janela 'session (5h)' e 'weekly (7d)' -> remaining_percentage, is_exhausted, next_reset_at
  provider_connections  is_active, rate_limited_until (pausa da conta)
Unidade = "pontos": % que sobra numa conta (o que limita é a menor das duas janelas). Livre total = soma das contas.
A sessão de chat do dono usa as MESMAS contas -> sempre fica uma RESERVA que os projetos não tocam.

    python cota_claude.py            mostra a situação (lê na hora)
    python cota_claude.py --json
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONFIG = RAIZ / "config.json"
CACHE = RAIZ / "estado" / "cota.json"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"   # o ssh do Windows trava em tarefa agendada
VALIDADE_CACHE_S = 300

CONSULTA = r'''
import json,sqlite3
db=sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro",uri=True,timeout=30)
contas={}
for cid,nome,ativo,rl in db.execute("select id,name,is_active,rate_limited_until from provider_connections where provider='claude'"):
    contas[cid]={"nome":nome,"ativa":bool(ativo),"pausa_ate":rl,"janelas":{}}
for cid,wk,rp,ex,nr,ca in db.execute("""select s.connection_id,s.window_key,s.remaining_percentage,s.is_exhausted,
    s.next_reset_at,s.created_at from quota_snapshots s join (select connection_id,window_key,max(id) mid from
    quota_snapshots where provider='claude' group by 1,2) u on s.id=u.mid"""):
    if cid in contas: contas[cid]["janelas"][wk]={"resta":rp,"esgotada":bool(ex),"renova":nr,"lido":ca}
print(json.dumps(list(contas.values())))
'''


def config():
    return json.loads(CONFIG.read_text("utf-8"))


def _t(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")) if iso else None


def _ler_omniroute():
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "hermes-bloqueio", "python3", "-"],
                       input=CONSULTA.encode(), capture_output=True, timeout=90)
    return json.loads(r.stdout.decode())


def _janela(j, agora):
    """(pontos que restam, quando volta se está zerada)."""
    if not j:
        return 100.0, None          # sem leitura dessa janela = nunca foi usada
    renova = _t(j.get("renova"))
    if renova and renova <= agora:
        return 100.0, None          # a janela já virou depois da última leitura
    resta = 0.0 if j.get("esgotada") else float(j.get("resta") or 0)
    return resta, (renova if resta <= 0 else None)


def situacao(forcar=False):
    """{livre, contas_com_cota, contas:[...], voltas:[(iso, pontos)], lido_em, erro?}. Cache de 5 min em disco."""
    if not forcar and CACHE.exists():
        try:
            c = json.loads(CACHE.read_text("utf-8"))
            if time.time() - c.get("_ts", 0) < VALIDADE_CACHE_S:
                return c
        except ValueError:
            pass
    agora = datetime.now(timezone.utc)
    try:
        brutas = _ler_omniroute()
    except Exception as e:  # noqa: BLE001
        # sem leitura = sem cota (nunca liga às cegas)
        return {"livre": 0.0, "contas_com_cota": 0, "contas": [], "voltas": [], "erro": f"{type(e).__name__}: {e}"[:200],
                "lido_em": agora.isoformat(timespec="seconds")}
    contas, voltas = [], []
    for c in brutas:
        if not c["ativa"]:
            continue
        s, volta_s = _janela(c["janelas"].get("session (5h)"), agora)
        w, volta_w = _janela(c["janelas"].get("weekly (7d)"), agora)
        pausa = _t(c.get("pausa_ate"))
        pausada = bool(pausa and pausa > agora)
        pontos = 0.0 if pausada else min(s, w)
        # quando volta: a semanal manda; se só a de 5 h zerou, volta na virada dela
        volta = None
        if pontos <= 0:
            datas = [x for x in (volta_w, volta_s, pausa if pausada else None) if x]
            volta = max(datas) if datas else None
            if volta:
                # o que volta: semanal virou -> conta cheia; só a de 5 h virou -> o que sobra da semanal
                volta_pts = 100.0 if volta_w else w
                voltas.append((volta.isoformat(timespec="seconds"), round(volta_pts, 1)))
        contas.append({"nome": c["nome"].split("@")[0], "pontos": round(pontos, 1), "sessao": s, "semana": w,
                       "volta": volta.isoformat(timespec="seconds") if volta else None})
    res = {"livre": round(sum(c["pontos"] for c in contas), 1),
           "contas_com_cota": sum(1 for c in contas if c["pontos"] > 0),
           "contas": sorted(contas, key=lambda c: -c["pontos"]),
           "voltas": sorted(voltas), "lido_em": agora.isoformat(timespec="seconds"), "_ts": time.time()}
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(res, ensure_ascii=False, indent=1), "utf-8")
    return res


def proxima_volta(sit, precisa):
    """Hora (datetime local) em que o livre deve passar de `precisa`, somando as contas que voltam. None = sem previsão."""
    livre = sit["livre"]
    for iso, pts in sit["voltas"]:
        livre += pts
        if livre >= precisa:
            return _t(iso).astimezone()
    return None


def decidir(custo, certeza, forcar=False):
    """{ligar, livre, disponivel, precisa, motivo, volta}. certeza=True exige 1,5x o custo além da reserva."""
    cfg = config()
    sit = situacao(forcar)
    reserva = cfg["reserva_dono"]
    precisa = custo * (cfg["margem_certeza"] if certeza else 1.0)
    disponivel = round(sit["livre"] - reserva, 1)
    ligar = disponivel >= precisa and not sit.get("erro")
    volta = None if ligar else proxima_volta(sit, reserva + precisa)
    if sit.get("erro"):
        motivo = f"sem leitura do OmniRoute ({sit['erro']})"
    elif ligar:
        motivo = f"livre {sit['livre']} - reserva {reserva} = {disponivel} >= {precisa:.0f}"
    else:
        motivo = (f"livre {sit['livre']} - reserva {reserva} = {disponivel} < {precisa:.0f}"
                  + (f"; deve ter cota às {volta:%d/%m %H:%M}" if volta else "; sem previsão de volta"))
    return {"ligar": ligar, "livre": sit["livre"], "disponivel": disponivel, "precisa": precisa, "motivo": motivo,
            "volta": volta.isoformat(timespec="minutes") if volta else None}


def _mostrar(sit):
    print(f"Contas Claude Pro com cota: {sit['contas_com_cota']} — livre {sit['livre']} pontos "
          f"(reserva do dono {config()['reserva_dono']})")
    for c in sit["contas"]:
        volta = f"volta {_t(c['volta']).astimezone():%d/%m %H:%M}" if c["volta"] else ""
        print(f"  {c['nome'][:24]:24} {c['pontos']:5.0f}  (5h {c['sessao']:.0f}% · semana {c['semana']:.0f}%) {volta}")
    if sit.get("erro"):
        print("ERRO:", sit["erro"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    s = situacao(forcar=True)
    if "--json" in sys.argv:
        print(json.dumps(s, ensure_ascii=False, indent=1))
    else:
        _mostrar(s)
        cfg = config()
        print("vídeo do zero:", decidir(cfg["custo_video_zero"], certeza=True)["motivo"])
        print("adicional    :", decidir(cfg["custo_adicional"], certeza=False)["motivo"])
