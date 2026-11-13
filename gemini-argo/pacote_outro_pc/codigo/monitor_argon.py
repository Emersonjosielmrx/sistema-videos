#!/usr/bin/env python3
r"""
Monitor do Argon (Gemini 4 Argon pelo gemini_http) - roda a cada 10 min pelo Task Scheduler (tarefa "MonitorArgon"),
no molde do D:\monitor_opus.py.

Lê a fila de contas (D:\gemini-argo\contas_argon.json, só leitura):
  - TODAS sem cota: manda no Telegram a hora em que a 1ª volta (de novo só se a previsão mudar). A hora é a
    que o Google informa na resposta (gemini_http._RE_VOLTA); sem ela, a espera estimada da fila.
  - havia ficado sem cota e agora há conta pronta: confirma com DOIS pedidos reais ao Argon (o gemini_http confere
    que quem respondeu foi o "4 Argon", não o Flash-Lite) antes de avisar que voltou.
Mensagem "argon" no Telegram: o notificar_telegram.py (único que lê o bot) chama este script com --comando.
Avisos pelo portão D:\video-fila\avisos.py, com chave por previsão.
"""
import io
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, r"D:\video-fila")
sys.path.insert(0, r"D:\gemini-argo")
import avisos  # noqa: E402

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CONTAS = Path(r"D:\gemini-argo\contas_argon.json")
STATE = Path(r"D:\gemini-argo\monitor_argon.json")
PADRAO = {"funcionando": None, "previsao_avisada": None, "teste_falhou_em": None}
ESPERA_APOS_FALHA = timedelta(minutes=30)


def carregar_estado():
    estado = dict(PADRAO)
    if STATE.exists():
        try:
            estado.update(json.loads(STATE.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            pass
    return estado


def salvar_estado(estado):
    tmp = STATE.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")
    for tentativa in range(20):
        try:
            os.replace(tmp, STATE)
            return
        except PermissionError:
            time.sleep(0.1 * (tentativa + 1))


def enviar(msg, chave):
    ok = bool(avisos.enviar(msg, "argon-monitor", importante=True, chave=chave))
    print(f"  telegram {'enviado' if ok else 'NAO saiu'}: {msg.splitlines()[0]}")
    return ok


def previsao():
    """{contas, prontas, voltas[]} a partir da fila de contas."""
    dados = json.loads(CONTAS.read_text(encoding="utf-8"))
    agora = datetime.now().isoformat()
    contas = dados.get("contas", [])
    prontas = [c for c in contas if not c.get("bloqueada") and not (c.get("sem_cota_ate") and c["sem_cota_ate"] > agora)]
    pendentes = sorted((c for c in contas if c.get("sem_cota_ate") and c["sem_cota_ate"] > agora),
                       key=lambda c: c["sem_cota_ate"])
    return {"contas": len(contas), "prontas": len(prontas), "voltas": [c["sem_cota_ate"] for c in pendentes],
            "exata": bool(pendentes and pendentes[0].get("volta_exata"))}


def texto_previsao(p):
    agora = datetime.now()
    cab = f"<b>Argon sem cota</b> ({agora:%H:%M}) — as {p['contas']} contas Pro estão sem cota agora"
    if not p["voltas"]:
        return f"{cab}.\nSem previsão de volta.", None
    prox = datetime.fromisoformat(p["voltas"][0])
    quando = f"hoje às <b>{prox:%H:%M}</b>" if prox.date() == agora.date() else f"em {prox:%d/%m} às <b>{prox:%H:%M}</b>"
    em1 = sum(1 for v in p["voltas"] if datetime.fromisoformat(v) <= agora + timedelta(hours=1))
    origem = "hora informada pelo Google" if p.get("exata") else "estimativa: o Google não informou a hora"
    return (f"{cab}.\nA 1ª volta {quando} ({origem}).\n"
            f"Voltando em 1 h: {em1}. Enquanto isso os pipelines usam o Gemini 3.8."), prox.isoformat(timespec="minutes")


def confirmar():
    """Dois pedidos reais ao Argon; ok só se os dois vierem do "4 Argon" com texto."""
    import gemini_http
    for i in range(2):
        try:
            r = gemini_http.perguntar("Quanto é 17*23? Responda só o número.")
        except Exception as e:  # noqa: BLE001 — fila vazia de novo, rede...
            return False, str(e)[:120]
        if not r or not r.strip():
            return False, "resposta vazia"
        if i == 0:
            time.sleep(10)
    return True, r.strip()[:40]


def verificar(estado, p, origem):
    agora = datetime.now()
    hora = f"{agora:%H:%M}"
    if p["prontas"] > 0:
        if estado.get("funcionando") is None and origem == "auto":
            estado.update(funcionando=True)  # 1ª execução: só registra, sem aviso
            return
        if estado.get("funcionando") and origem == "auto":
            return
        falhou = estado.get("teste_falhou_em")
        if origem == "auto" and falhou and agora - datetime.fromisoformat(falhou) < ESPERA_APOS_FALHA:
            print("  há conta pronta, mas o teste falhou há pouco; espera")
            return
        ok, detalhe = confirmar()
        if ok:
            if not estado.get("funcionando") or origem == "comando":
                enviar(f"<b>ARGON FUNCIONANDO</b> ({hora})\n\nConfirmado em 2 respostas do 4 Argon.\n"
                       f"Contas prontas na fila: {p['prontas']} de {p['contas']}.",
                       f"argon-voltou:{agora.isoformat()}")
            estado.update(funcionando=True, teste_falhou_em=None, previsao_avisada=None)
            return
        print(f"  conta pronta na fila, mas o teste falhou: {detalhe}")
        estado.update(teste_falhou_em=agora.isoformat())
        if origem == "comando":
            enviar(f"<b>Argon</b> ({hora}): {p['prontas']} conta(s) prontas na fila, mas o teste falhou "
                   f"({detalhe}). Testo de novo em 30 min.", f"argon-falhou:{agora.isoformat()}")
        return
    estado["funcionando"] = False
    msg, prox = texto_previsao(p)
    print(f"  sem cota; 1ª volta estimada {prox}")
    if origem == "comando":
        if enviar(msg, f"argon-comando:{agora.isoformat()}"):
            estado["previsao_avisada"] = prox
        return
    avisada = estado.get("previsao_avisada")
    # a estimativa se ajusta a cada nova tentativa; só repete se a anterior já passou ou mudou mais de 30 min
    mudou = not avisada or not prox or abs((datetime.fromisoformat(prox) - datetime.fromisoformat(avisada))
                                           .total_seconds()) > 1800 or datetime.fromisoformat(avisada) < agora
    if mudou and enviar(msg, f"argon-previsao:{prox}"):
        estado["previsao_avisada"] = prox


def main():
    origem = "comando" if "--comando" in sys.argv else "auto"
    print(f"[{datetime.now():%H:%M:%S}] monitor argon ({origem})")
    estado = carregar_estado()
    try:
        p = previsao()
    except (OSError, ValueError) as e:
        print(f"  não li a fila de contas: {e}")
        if origem == "comando":
            enviar("Não consegui ler a fila de contas do Argon agora.", f"argon-comando-sem-dados:{datetime.now()}")
        return
    estado["leitura"] = {"em": datetime.now().isoformat(timespec="seconds"), **p}
    verificar(estado, p, origem)
    salvar_estado(estado)
    print("  fim")


if __name__ == "__main__":
    main()
