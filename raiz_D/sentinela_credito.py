#!/usr/bin/env python3
r"""sentinela_credito.py - le cota do CC e Antigravity no OmniRoute e devolve JSON.

Uso:
    python D:\sentinela_credito.py               # estado de AMBOS (CC + Antigravity)
    python D:\sentinela_credito.py --provider cc  # so CC
    python D:\sentinela_credito.py --provider agy # so Antigravity
    python D:\sentinela_credito.py --sessoes      # sessoes Claude Code idle neste PC

Saida: JSON com {provider, contas, com_credito, voltas[], proxima_volta, previsao_texto}
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
SSH_HOST = "hermes-bloqueio"
SESSIONS_DIR = Path(os.path.expanduser("~")) / ".claude-vscode" / "sessions"
STATE_FILE = Path(r"D:\sentinela_credito_state.json")

# Query remota: nao usar .format() — usa $PROVIDER$ com .replace()
# Logica correta:
#   - Pega TODAS as contas ativas (inclusive com rate_limited_until no futuro)
#   - Para Antigravity: exige projectId
#   - Uma conta TEM credito se: (rl ausente ou no passado) E nenhuma janela esgotada
#   - Uma conta VOLTA quando: max(rl, next_reset das janelas esgotadas)
#   - Se so a session esgotou mas weekly OK, volta = next_reset da session
CONSULTA_TEMPLATE = r"""
import json,sqlite3,datetime
db=sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
agora=datetime.datetime.now(datetime.timezone.utc)
agora_s=agora.strftime("%Y-%m-%dT%H:%M:%S")
PROVIDER="$PROVIDER$"
TIPO=PROVIDER
# 09/11: "ag46" = contas Antigravity que ainda tem o Opus 4.6 (e nao ganharam o 5.5)
if TIPO=="ag46": PROVIDER="antigravity"
# 13/11: "fable" = contas cc (mesma cota 5h/semanal) sem o limite proprio do Fable 5.2 (429 nas ultimas 5 h sem 200 depois; medido: dura 4-5 h)
if TIPO=="fable": PROVIDER="claude"

try: isoladas=set(json.load(open("/opt/omniroute/contas_isoladas.json")))
except (OSError, ValueError): isoladas=set()

contas={}
for cid,psd,rl in db.execute("select id,provider_specific_data,rate_limited_until from provider_connections where provider=? and is_active=1",(PROVIDER,)):
    try: p=json.loads(psd or "{}")
    except ValueError: p={}
    if PROVIDER == "antigravity" and not p.get("projectId"):
        continue
    if cid in isoladas:
        continue
    contas[cid]={"rl":rl,"windows":{}}

desde=(agora-datetime.timedelta(hours=3 if TIPO=="ag46" else 12)).strftime("%Y-%m-%dT%H:%M:%S")
# so as janelas do Opus: as do Gemini (mesmas contas do antigravity) nao dizem nada do Opus
# 06/11: Opus 4.6 morreu -> antigravity conta so as contas com o Opus 5.5 (janela claude-opus-5-5-high)
JANELAS={"claude":("session (5h)","weekly (7d)"),"fable":("session (5h)","weekly (7d)"),"antigravity":("claude-opus-5-5-high","claude_gpt_weekly","gpt-oss-120b-medium"),
         "ag46":("claude-opus-4-6-thinking","claude-opus-5-5-high")}[TIPO]
for cid,wk,ex,nr in db.execute("select s.connection_id,s.window_key,s.is_exhausted,s.next_reset_at from quota_snapshots s join (select connection_id,window_key,max(id) mid from quota_snapshots where provider=? and created_at>? group by connection_id,window_key) u on s.id=u.mid",(PROVIDER,desde)):
    if cid in contas and wk in JANELAS:
        contas[cid]["windows"][wk]=(ex,nr)
if TIPO == "antigravity":  # sem a janela do Opus 5.5 = conta nao tem o 5.5: nao conta como credito
    contas={k:v for k,v in contas.items() if "claude-opus-5-5-high" in v["windows"]}
if TIPO == "ag46":  # tem a janela do 4.6 e nao a do 5.5 (quem ganhou o 5.5 perdeu o 4.6)
    contas={k:{**v,"windows":{w:x for w,x in v["windows"].items() if w!="claude-opus-5-5-high"}} for k,v in contas.items()
            if "claude-opus-4-6-thinking" in v["windows"] and "claude-opus-5-5-high" not in v["windows"]}
if TIPO == "fable":
    hora=(agora-datetime.timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S")
    for cid,t429 in db.execute("select connection_id,max(timestamp) from usage_history where provider='claude' and model like 'claude-fable%' "
                               "and cast(status as integer)=429 and connection_id is not null and timestamp>? group by 1",(hora,)):
        ok=db.execute("select max(timestamp) from usage_history where connection_id=? and model like 'claude-fable%' "
                      "and cast(status as integer)=200",(cid,)).fetchone()[0]
        if cid in contas and not (ok and ok>t429):
            fim=(datetime.datetime.fromisoformat(t429[:19])+datetime.timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            if not (contas[cid]["rl"] and contas[cid]["rl"][:19]>fim[:19]): contas[cid]["rl"]=fim

com=0; voltas=[]
for c in contas.values():
    rl=c["rl"]
    rl_futuro = bool(rl and rl[:19]>agora_s)
    wins=c["windows"]
    alguma_esgotada = any(v[0] for v in wins.values())
    if not rl_futuro and not alguma_esgotada:
        com+=1
        continue
    # quando volta? max de (rl se futuro, next_reset de cada janela esgotada)
    datas=[]
    if rl_futuro and rl:
        datas.append(rl)
    for wk,(ex,nr) in wins.items():
        if ex and nr:
            datas.append(nr)
    if datas:
        voltas.append(max(datas))

print(json.dumps({"provider":TIPO,"contas":len(contas),"com_credito":com,"voltas":sorted(set(voltas))}))
"""


def consultar(provider):
    query = CONSULTA_TEMPLATE.replace("$PROVIDER$", provider)
    try:
        r = subprocess.run(
            [SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", SSH_HOST, "python3", "-"],
            input=query.encode(), capture_output=True, timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"provider": provider, "erro": f"{type(e).__name__}", "contas": 0, "com_credito": 0, "voltas": []}
    try:
        return json.loads(r.stdout.decode())
    except ValueError:
        return {"provider": provider, "erro": r.stderr.decode(errors="replace")[:300],
                "contas": 0, "com_credito": 0, "voltas": []}


def texto_previsao(p):
    agora = datetime.now().astimezone()
    futuras = sorted(
        t for v in p["voltas"]
        for t in [datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone()]
        if t > agora
    )
    nome = {"claude": "CC (Opus 5.5)", "antigravity": "Antigravity (Opus 5.5)", "fable": "CC (Fable 5.2)"}.get(p["provider"], "Antigravity (Opus 4.6)")
    if p["com_credito"] > 0:
        return f"{nome}: {p['com_credito']} conta(s) com credito", None
    if not futuras:
        return f"{nome}: sem credito e sem previsao de volta", None
    prox = futuras[0]
    if prox.date() == agora.date():
        quando = f"hoje as {prox:%H:%M}"
    elif prox.date() == agora.date() + timedelta(days=1):
        quando = f"amanha as {prox:%H:%M}"
    else:
        quando = f"em {prox:%d/%m} as {prox:%H:%M}"
    em6 = sum(1 for t in futuras if t <= agora + timedelta(hours=6))
    em24 = sum(1 for t in futuras if t <= agora + timedelta(hours=24))
    total = p["contas"]
    return f"{nome}: sem credito. Volta {quando} ({em6} em 6h, {em24} em 24h, de {total})", prox.isoformat()


def sessoes_idle():
    resultado = []
    if not SESSIONS_DIR.exists():
        return resultado
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if s.get("status") == "idle" and s.get("kind") == "interactive" and s.get("messagingSocketPath"):
            resultado.append({
                "name": s.get("name", f.stem),
                "pipe": s["messagingSocketPath"],
                "sessionId": s.get("sessionId"),
                "pid": s.get("pid"),
            })
    return resultado


def carregar_estado():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    return {"cc": {"funcionando": False, "previsao": None},
            "agy": {"funcionando": False, "previsao": None},
            "ultimo_disparo": None}


def salvar_estado(estado):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")
    for tentativa in range(20):
        try:
            os.replace(tmp, STATE_FILE)
            return
        except PermissionError:
            if tentativa == 19:
                raise
            time.sleep(0.1)


def main():
    args = sys.argv[1:]
    if "--sessoes" in args:
        print(json.dumps(sessoes_idle(), indent=2, ensure_ascii=False))
        return

    providers = ["claude", "antigravity"]
    if "--provider" in args:
        idx = args.index("--provider")
        p = args[idx + 1] if idx + 1 < len(args) else "claude"
        providers = [{"cc": "claude", "agy": "antigravity"}.get(p, p)]

    estado = carregar_estado()
    resultados = []

    for prov in providers:
        p = consultar(prov)
        msg, prox = texto_previsao(p)
        p["previsao_texto"] = msg
        p["proxima_volta"] = prox

        chave = "cc" if prov == "claude" else "agy"
        if p["com_credito"] > 0:
            if not estado[chave]["funcionando"]:
                p["acabou_de_voltar"] = True
            estado[chave]["funcionando"] = True
            estado[chave]["previsao"] = None
        else:
            estado[chave]["funcionando"] = False
            estado[chave]["previsao"] = prox

        resultados.append(p)

    # gravar no opus_monitor.json (campo "sentinela")
    om_path = Path(r"D:\opus_monitor.json")
    try:
        om = json.loads(om_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        om = {}
    cc_r = next((r for r in resultados if r["provider"] == "claude"), {})
    agy_r = next((r for r in resultados if r["provider"] == "antigravity"), {})
    om["sentinela"] = {
        "em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "cc": {"com_credito": cc_r.get("com_credito", 0), "proxima_volta": cc_r.get("proxima_volta")},
        "agy": {"com_credito": agy_r.get("com_credito", 0), "proxima_volta": agy_r.get("proxima_volta")},
    }
    tmp = om_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(om, indent=2, ensure_ascii=False), encoding="utf-8")
    for tentativa in range(20):
        try:
            os.replace(tmp, om_path)
            break
        except PermissionError:
            time.sleep(0.1)

    salvar_estado(estado)
    print(json.dumps(resultados, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()