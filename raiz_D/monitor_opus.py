#!/usr/bin/env python3
"""
Monitor Opus 5.5 Antigravity (era 4.6 ate 06/11/2026, que morreu) - roda a cada 10 min pelo Task Scheduler (tarefa "MonitorOpus").

Le no OmniRoute (157, por ssh, so leitura) a cota de Opus 5.5 de cada conta do Antigravity:
  - sem credito: manda no Telegram a hora em que volta (de novo so se a previsao mudar);
  - os dados mostram credito: confirma com DOIS testes de resposta de texto real antes de
    avisar que voltou (falso positivo de 18/10/2026: max_tokens=1 nao prova nada).
Nao testa o modelo as cegas. Mensagem "opus" no Telegram: o notificar_telegram.py (unico que le
o bot) chama este script com --comando, que responde na hora.
Avisos saem pelo portao D:\video-fila\avisos.py, com chave por previsao (o portao trataria
"volta as 17:37" e "volta as 18:20" como o mesmo aviso repetido).
"""
import html
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, r"D:\video-fila")
import avisos  # noqa: E402

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# mesma porta e chave do chat do VS Code: o teste ve o que o chat ve
OMNIROUTE_URL = "http://157.173.207.22:20133/v1/messages"
OMNIROUTE_KEY = "<SEGREDO_REMOVIDO>"
MODELO_OPUS = "ag-opus-5-5"
TIMEOUT_S = 120  # 06/11: ag-opus-5-5 pode levar ~60 s quando a 1a conta do combo esta sem cota

# o ssh do Windows trava sem console (tarefa agendada); o do Git funciona
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
ESPERA_APOS_FALHA = timedelta(minutes=30)

# contas utilizaveis = ativas, com projeto (as "Restricted" sem projeto marcam 100% e nunca servem)
# e fora de pausa (rate_limited_until); credito = janela do Opus e a semanal sem esgotar
CONSULTA = r'''
import json,sqlite3,datetime
db=sqlite3.connect("file:/opt/omniroute/data/storage.sqlite?mode=ro", uri=True, timeout=30)
agora=datetime.datetime.now(datetime.timezone.utc)
contas={}
for cid,psd,rl in db.execute("select id,provider_specific_data,rate_limited_until from provider_connections where provider='antigravity' and is_active=1"):
    try: p=json.loads(psd or "{}")
    except ValueError: p={}
    if p.get("projectId") and not (rl and rl[:19]>agora.strftime("%Y-%m-%dT%H:%M:%S")): contas[cid]={}
desde=(agora-datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S")
for cid,wk,ex,nr in db.execute("""select s.connection_id,s.window_key,s.is_exhausted,s.next_reset_at from quota_snapshots s
  join (select connection_id,window_key,max(id) mid from quota_snapshots where provider='antigravity' and created_at>?
        and window_key in ('claude-opus-5-5-high','claude_gpt_weekly','gpt-oss-120b-medium') group by connection_id,window_key) u on s.id=u.mid""",(desde,)):
    if cid in contas: contas[cid][wk]=(ex,nr)
com=0; voltas=[]
for j in contas.values():
    if "claude-opus-5-5-high" not in j: continue
    fim=[v[1] for v in j.values() if v[0] and v[1]]
    if fim: voltas.append(max(fim))
    elif not any(v[0] for v in j.values()): com+=1
print(json.dumps({"contas":len(contas),"com_credito":com,"voltas":sorted(voltas)}))
'''

STATE = Path("D:/opus_monitor.json")
PADRAO = {"funcionando": False, "previsao_avisada": None, "teste_falhou_em": None, "aviso_falha_enviado": False}


def carregar_estado():
    estado = dict(PADRAO)
    if STATE.exists():
        try:
            estado.update(json.loads(STATE.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            pass
    return estado


def salvar_estado(estado):
    # 24/10: troca atômica — a 3ª camada das melhorias (D:\video-fila\camada_opus) lê este arquivo
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(estado, indent=2), encoding="utf-8")
    for tentativa in range(20):  # 24/10: quem está lendo o JSON segura o arquivo no Windows (PermissionError)
        try:
            os.replace(tmp, STATE)
            return
        except PermissionError:
            if tentativa == 19:
                raise
            time.sleep(0.1)


def enviar(msg, chave):
    """msg em HTML do Telegram; chave unica por evento (cada previsao nova tem que sair)."""
    ok = bool(avisos.enviar(msg, "opus-monitor", importante=True, chave=chave))
    print(f"  telegram {'enviado' if ok else 'NAO saiu'}: {msg.splitlines()[0]}")
    return ok


def limpo(texto):
    return html.escape(str(texto), quote=False)


def previsao():
    """Dict {contas, com_credito, voltas[]} lido no OmniRoute, ou None se nao deu para ler."""
    try:
        r = subprocess.run(
            [SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "hermes-bloqueio", "python3", "-"],
            input=CONSULTA.encode(), capture_output=True, timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"  sem dados do OmniRoute: {type(e).__name__}")
        return None
    try:
        return json.loads(r.stdout.decode())
    except ValueError:
        print(f"  sem dados do OmniRoute: {r.stderr.decode(errors='replace')[:200]}")
        return None


def texto_previsao(p):
    """(mensagem, hora da 1a volta em ISO) ou (mensagem, None) se nao ha previsao."""
    agora = datetime.now().astimezone()
    futuras = [t for t in (datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone() for v in p["voltas"])
               if t > agora]
    cab = f"<b>Opus 5.5 Antigravity sem crédito</b> ({agora:%H:%M})"
    if not futuras:
        return f"{cab}\nO gateway não tem previsão de volta para nenhuma conta.", None
    prox = futuras[0]
    if prox.date() == agora.date():
        quando = f"hoje às <b>{prox:%H:%M}</b>"
    elif prox.date() == agora.date() + timedelta(days=1):
        quando = f"amanhã às <b>{prox:%H:%M}</b>"
    else:
        quando = f"em {prox:%d/%m} às <b>{prox:%H:%M}</b>"
    em6 = sum(1 for t in futuras if t <= agora + timedelta(hours=6))
    em24 = sum(1 for t in futuras if t <= agora + timedelta(hours=24))
    return (f"{cab}\nVolta {quando}.\n"
            f"Contas voltando: {em6} em 6 h, {em24} em 24 h (de {p['contas']} que servem)."), prox.isoformat()


def testar(modelo):
    """Retorna (ok, detalhe). ok=True so com 200 e texto nao vazio."""
    try:
        r = requests.post(
            OMNIROUTE_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": OMNIROUTE_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": modelo,
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": "Quanto e 17*23? So o numero."}],
            },
            timeout=TIMEOUT_S,
        )
    except requests.Timeout:
        return False, f"timeout {TIMEOUT_S}s"
    except requests.RequestException as e:
        return False, type(e).__name__

    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"

    try:
        blocos = r.json().get("content", [])
    except ValueError:
        return False, "200 com corpo invalido"

    texto = "".join(b.get("text", "") for b in blocos if b.get("type") == "text").strip()
    if not texto:
        return False, "200 sem texto (falso positivo)"
    return True, texto[:60]


def confirmar(modelo):
    """Dupla confirmacao: so conta como voltou se dois testes seguidos passarem."""
    ok, detalhe = testar(modelo)
    if not ok:
        return False, detalhe
    time.sleep(20)
    ok2, detalhe2 = testar(modelo)
    if not ok2:
        return False, f"instavel (1o ok, 2o: {detalhe2})"
    return True, detalhe2


def verificar(estado, p, origem):
    agora = datetime.now().astimezone()
    hora = agora.strftime("%H:%M")

    if p["com_credito"] > 0:
        if origem == "auto":
            if estado["funcionando"]:
                return
            falhou = estado.get("teste_falhou_em")
            if falhou and agora - datetime.fromisoformat(falhou) < ESPERA_APOS_FALHA:
                print("  dados mostram credito; teste falhou ha pouco, espera")
                return
        if origem == "comando":
            enviar(f"Os dados mostram {p['com_credito']} conta(s) com crédito. Testando Opus 5.5 Antigravity...",
                   f"opus-comando-testando:{agora.isoformat()}")
        ok, detalhe = confirmar(MODELO_OPUS)
        if ok:
            if not estado["funcionando"] or origem == "comando":
                enviar(f"<b>OPUS 5.5 ANTIGRAVITY FUNCIONANDO</b> ({hora})\n\nConfirmado em 2 testes.\n"
                       f"Contas com crédito: {p['com_credito']}\nResposta: {limpo(detalhe)}",
                       f"opus-voltou:{agora.isoformat()}")
            estado.update(funcionando=True, teste_falhou_em=None, aviso_falha_enviado=False, previsao_avisada=None)
            return
        print(f"  dados mostram credito, mas o teste falhou: {detalhe}")
        estado.update(funcionando=False, teste_falhou_em=agora.isoformat())
        if origem == "comando" or not estado.get("aviso_falha_enviado"):
            enviar(f"<b>Opus 5.5 Antigravity</b> ({hora}): o gateway mostra {p['com_credito']} conta(s) com crédito, "
                   f"mas o teste falhou ({limpo(detalhe)}). Testo de novo em 30 min.",
                   f"opus-falhou:{agora.isoformat()}")
            estado["aviso_falha_enviado"] = True
        return

    estado.update(funcionando=False, teste_falhou_em=None, aviso_falha_enviado=False)
    msg, prox = texto_previsao(p)
    print(f"  sem credito; volta {prox}")
    if origem == "comando":
        if enviar(msg, f"opus-comando:{agora.isoformat()}"):
            estado["previsao_avisada"] = prox
    elif estado.get("previsao_avisada") != prox:
        if enviar(msg, f"opus-previsao:{prox}"):
            estado["previsao_avisada"] = prox


def main():
    origem = "comando" if "--comando" in sys.argv else "auto"
    print(f"[{datetime.now():%H:%M:%S}] monitor ({origem})")
    estado = carregar_estado()
    p = previsao()
    if p is None:
        if origem == "comando":
            enviar("Não consegui ler a cota do Opus no gateway agora. Tento de novo em 10 min.",
                   f"opus-comando-sem-dados:{datetime.now().isoformat()}")
    else:
        # 24/10: a 3ª camada das melhorias só roda com leitura fresca e com_credito >= 3 (pedido da dona)
        agora = datetime.now().astimezone()
        futuras = sorted(v for v in p.get("voltas") or []
                         if datetime.fromisoformat(v.replace("Z", "+00:00")) > agora)
        estado["leitura"] = {"em": agora.isoformat(timespec="seconds"), "contas": p.get("contas"),
                             "com_credito": p.get("com_credito"), "proxima_volta": futuras[0] if futuras else None}
        verificar(estado, p, origem)
    salvar_estado(estado)
    print("  fim")


if __name__ == "__main__":
    main()
