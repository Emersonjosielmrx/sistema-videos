# 01/11/2026 (dona): imagem pelo modelo do Google (antigravity/gemini-3.1-flash-image no OmniRoute 157) CONTA POR CONTA,
# do mesmo jeito do monitor do Opus 4.6: a conta que esgota fica de fora com a hora em que volta; nessa hora o vigia
# (tarefa GoogleImagemVigia, a cada 10 min) manda UMA imagem de teste; funcionou = volta pra fila de uso.
#
# Por que: o OmniRoute tenta só 6 contas por pedido, sempre as mesmas (prioridade 1, 5, 6, 7, 8, 9), e devolve 429
# "exhausted" mesmo com ~76 contas a 100% da cota de imagem (prova 01/11 15h: call_logs + quota_snapshots). O
# cabeçalho x-omniroute-connection escolhe a conta: conta com cota gerou em 19 s, a esgotada deu "reset after 2h39m".
#
# Uso:  from google_imagem import gerar ; gerar(prompt, saida, size="1792x1024", aspect="16:9") -> (ok, detalhe)
#       python google_imagem.py --vigia      (testa as contas cuja volta já passou; atualiza a lista)
#       python google_imagem.py --estado     (resumo: na fila / esperando / próxima volta)
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ESTADO = Path(r"D:\flow-imagens\logs\google_contas.json")
LOG = Path(r"D:\flow-imagens\logs\google_imagem.log")
MODELO = "antigravity/gemini-3.1-flash-image"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
LISTA_VALE = timedelta(hours=2)        # relê as contas no OmniRoute a cada 2 h
ESPERA_SEM_PREVISAO = timedelta(hours=1)
MAX_CONTAS_POR_PEDIDO = 8              # erro que não é cota (recusa, "sem imagem") não é culpa da conta

# contas que servem: ativas, com projeto, fora de pausa; ordem = mais cota de imagem primeiro
CONSULTA = r'''
import json,sqlite3,datetime
db=sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
agora=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
cota={}
for cid,rp,ex,nr in db.execute("""select s.connection_id,s.remaining_percentage,s.is_exhausted,s.next_reset_at from quota_snapshots s
  join (select connection_id,max(id) mid from quota_snapshots where provider='antigravity' and window_key='gemini-3.1-flash-image'
  group by connection_id) u on s.id=u.mid"""):
    cota[cid]=(rp,ex,nr)
out=[]
for cid,email,psd,rl in db.execute("select id,email,provider_specific_data,rate_limited_until from provider_connections where provider='antigravity' and is_active=1"):
    try: p=json.loads(psd or "{}")
    except ValueError: p={}
    if not p.get("projectId") or (rl and rl[:19]>agora): continue
    rp,ex,nr=cota.get(cid,(None,0,None))
    out.append({"id":cid,"email":email,"cota":rp,"esgotada":bool(ex),"volta":nr if ex else None})
print(json.dumps(out))
'''


def _log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")


def _agora():
    return datetime.now(timezone.utc)


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"contas": {}, "lista_em": None}


def _gravar(e):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    # 02/11: um .tmp por processo/thread — com 4 threads (google_capas) uma levava o .tmp da outra (FileNotFoundError)
    import threading
    tmp = ESTADO.with_suffix(f".{os.getpid()}_{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(e, indent=1, ensure_ascii=False), encoding="utf-8")
    for _ in range(20):
        try:
            os.replace(tmp, ESTADO)
            return
        except PermissionError:
            time.sleep(0.1)


def _gateway():
    sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
    import capa_ia_anime as c
    return c._gateway()


def atualizar_lista(e, forcar=False):
    """Lê as contas no OmniRoute (ssh, só leitura). Conta nova entra na fila; a que o OmniRoute diz esgotada fica
    esperando a volta dele. Conta que já marcamos esperando NÃO volta só porque o painel diz que tem cota (o painel
    estava com 100% em contas que davam 429): só volta pelo teste."""
    if not forcar and e.get("lista_em") and _agora() - datetime.fromisoformat(e["lista_em"]) < LISTA_VALE:
        return e
    try:
        r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "hermes-bloqueio", "python3", "-"],
                           input=CONSULTA.encode(), capture_output=True, timeout=90, creationflags=0x08000000)
        lista = json.loads(r.stdout.decode())
    except (OSError, subprocess.TimeoutExpired, ValueError) as ex:
        _log(f"lista: não li o OmniRoute ({type(ex).__name__}); sigo com a anterior")
        return e
    vivas = {c["id"] for c in lista}
    for c in lista:
        atual = e["contas"].get(c["id"])
        if atual is None:
            atual = e["contas"][c["id"]] = {"email": c["email"], "status": "fila", "volta": None, "ok": 0, "falhas": 0}
            if c["esgotada"] and c["volta"]:
                atual.update(status="esperando", volta=c["volta"].replace("Z", "+00:00"))
        atual["cota_painel"] = c["cota"]
    for cid in list(e["contas"]):
        if cid not in vivas:
            del e["contas"][cid]  # desativada/pausada no OmniRoute
    e["lista_em"] = _agora().isoformat()
    return e


def _volta_do_erro(texto):
    """'Your quota will reset after 2h39m24s.' -> datetime; sem previsão = +1 h."""
    m = re.search(r"reset after\s+(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?", texto or "")
    if m and any(m.groups()):
        h, mi, s = (int(x or 0) for x in m.groups())
        return _agora() + timedelta(hours=h, minutes=mi, seconds=s + 60)
    return _agora() + ESPERA_SEM_PREVISAO


def _pedir(cid, prompt, size, aspect, timeout=240):
    """(codigo, b64 ou None, texto do erro). codigo: 'ok', 'cota', 'outro'."""
    base, tok = _gateway()
    corpo = {"model": MODELO, "prompt": prompt, "n": 1, "response_format": "b64_json"}
    if size:
        corpo["size"] = size
    if aspect:
        corpo["aspect_ratio"] = aspect
    req = urllib.request.Request(base + "/v1/images/generations", data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok,
                                          "x-omniroute-connection": cid})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = ((json.loads(r.read()).get("data") or [{}])[0]).get("b64_json")
    except urllib.error.HTTPError as ex:
        txt = ex.read().decode("utf-8", "replace")[:300]
        if ex.code == 429 or "exhausted" in txt.lower() or "quota" in txt.lower():
            return "cota", None, txt
        return "outro", None, f"HTTP {ex.code} {txt[:150]}"
    except Exception as ex:  # noqa: BLE001
        return "outro", None, f"{type(ex).__name__} {str(ex)[:150]}"
    return ("ok", b, "") if b else ("outro", None, "sem imagem")


def _esgotou(e, cid, txt):
    v = _volta_do_erro(txt)
    c = e["contas"][cid]
    c.update(status="esperando", volta=v.isoformat())
    _log(f"{c['email']}: esgotou, volta {v.astimezone():%d/%m %H:%M} -> teste agendado")


def na_fila(e):
    return [cid for cid, c in e["contas"].items() if c["status"] == "fila"]


def gerar(prompt, saida, size="1792x1024", aspect="16:9"):
    """Gera com a próxima conta da fila. Cota acabou nela = sai da fila com a hora da volta e tenta a seguinte.
    Devolve (ok, detalhe). Sem nenhuma conta na fila = (False, 'sem conta com cota ...')."""
    e = atualizar_lista(_ler())
    tentadas, outros = 0, []
    # menos usada primeiro, pra espalhar o gasto
    for cid in sorted(na_fila(e), key=lambda k: e["contas"][k].get("ok", 0)):
        if tentadas >= MAX_CONTAS_POR_PEDIDO:
            break
        tentadas += 1
        cod, b, txt = _pedir(cid, prompt, size, aspect)
        c = e["contas"][cid]
        if cod == "ok":
            Path(saida).parent.mkdir(parents=True, exist_ok=True)
            Path(saida).write_bytes(base64.b64decode(b))
            c["ok"] = c.get("ok", 0) + 1
            _gravar(e)
            return True, f"Google ({c['email']})"
        if cod == "cota":
            _esgotou(e, cid, txt)
            _gravar(e)
            continue
        outros.append(txt[:60])
        if len(outros) >= 3:  # 3 contas dando o mesmo "sem imagem"/recusa = é o prompt, não a conta
            break
    _gravar(e)
    proxima = min((c["volta"] for c in e["contas"].values() if c["status"] == "esperando" and c["volta"]),
                  default=None)
    if outros:
        return False, f"Google recusou/sem imagem ({outros[-1]})"
    return False, f"sem conta com cota (próxima volta {proxima})"


def vigia():
    """Conta cuja volta já passou: 1 imagem de teste. Funcionou = fila; 429 = nova hora de volta."""
    e = atualizar_lista(_ler(), forcar=True)
    agora = _agora()
    vencidas = [cid for cid, c in e["contas"].items()
                if c["status"] == "esperando" and c.get("volta") and datetime.fromisoformat(c["volta"]) <= agora]
    for cid in vencidas:
        c = e["contas"][cid]
        cod, b, txt = _pedir(cid, "a red apple on a wooden table, simple photo", None, None, timeout=120)
        if cod == "ok":
            c.update(status="fila", volta=None, falhas=0)
            _log(f"{c['email']}: teste OK -> voltou pra fila")
        elif cod == "cota":
            _esgotou(e, cid, txt)
        else:
            c["falhas"] = c.get("falhas", 0) + 1
            c["volta"] = (agora + timedelta(minutes=30)).isoformat()
            _log(f"{c['email']}: teste falhou ({txt[:80]}), tento em 30 min")
        _gravar(e)
    _gravar(e)
    return resumo(e)


def resumo(e=None):
    e = e or _ler()
    fila = na_fila(e)
    esp = sorted(c["volta"] for c in e["contas"].values() if c["status"] == "esperando" and c.get("volta"))
    prox = datetime.fromisoformat(esp[0]).astimezone().strftime("%d/%m %H:%M") if esp else "-"
    return f"Google imagem: {len(fila)} contas na fila, {len(esp)} esperando (próxima volta {prox})"


if __name__ == "__main__":
    if "--vigia" in sys.argv:
        r = vigia()
        _log(r)
        print(r)
    else:
        print(resumo(atualizar_lista(_ler())))
