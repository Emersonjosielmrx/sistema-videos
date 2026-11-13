#!/usr/bin/env python3
"""vigia_mutuo.py — cada máquina viva confere as outras e avisa no Telegram quem caiu (dono, 22/10/2026: "manda no
Telegram PC1 sem sinal, ou melhor: qualquer um que ficar off, o que estiver de pé avisa dos outros").

Roda no PC1 (D:\\video-fila\\vitrine.py --rodar, a cada 2 min) e nos notebooks (thread do ~/vitrine/player.py).
Quem está online vem do `tailscale status --json` (todas têm). Só UMA avisa: a primeira viva na ORDEM; as outras ficam
quietas. Caiu = offline por 6 min seguidos; avisa uma vez e de novo quando voltar. Os notebooks também veem o PC1
"ligado mas parado" (o painel.json não chega há 15 min). Só biblioteca padrão.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

VIGIADAS = {"PC1": "100.118.234.102", "PC2": "100.125.7.77", "Acer": "100.98.55.125", "X200MA": "100.87.195.108"}
ORDEM = ["PC1", "X200MA", "Acer"]  # quem avisa: a primeira viva desta lista
MIN_OFF_S = 6 * 60  # telão: a partir daqui a máquina aparece como fora (só na tela, sem Telegram)
# 01/11 (dona: "aviso de desligamento sem sinal e volta dos PCs e desktop só podem chegar se tiver mais de uma hora"):
# o Telegram só sai com a máquina fora há 1 h sem voltar; o "voltou" só sai se a queda foi avisada
AVISO_TELEGRAM_S = 60 * 60
PC1_PARADO_S = 15 * 60
# dona 23/10: PC fora = PRIORIDADE em todos os bots, repetida enquanto não voltar (o PC2 tem um vigia que reinicia a
# placa Wi-Fi sozinho, D:\video-fila\pc2; se mesmo assim passar de 6 min, é com ela)
PRIORIDADE = {"PC2"}  # dona 23/10: "o PC1 não tem esse problema, só o 2" (o resto segue o aviso normal)
REPETIR_S = 3 * 60 * 60  # 01/11: repetia a cada 30 min; com o aviso só após 1 h, o lembrete passa a cada 3 h
# o vigia do PC2 confere a rede a cada 10 min e reinicia a placa em ~2 min: só avisa se passar disso
MIN_OFF_MAQ = {"PC2": 15 * 60}
WINDOWS = os.name == "nt"
PASTA = Path(r"D:\video-fila\estado") if WINDOWS else Path.home() / "vitrine"
ESTADO = PASTA / "vigia_mutuo.json"
TS_EXE = r"C:\Program Files\Tailscale\tailscale.exe" if WINDOWS else (shutil.which("tailscale") or "tailscale")


# 29/10 (Fable; dona: "aparece muito 'desconectado' mesmo com as máquinas trabalhando"): o "Online" da Tailscale fica
# false para máquina ociosa ("idle") ou sem conexão direta, e o `tailscale status` do PC1 estourava 30 s (44x em 29/10).
# Agora a prova é uma porta TCP real de cada máquina (ssh/painel): respondeu = ligada, aconteça o que for com a Tailscale.
PORTAS = {"PC1": 8790, "PC2": 22, "Acer": 22, "X200MA": 2222}


def _tcp(ip, porta, t=4):
    import socket
    try:
        socket.create_connection((ip, porta), timeout=t).close()
        return True
    except OSError:
        return False


def _online():
    """{ip: True/False}: porta TCP da máquina responde OU a Tailscale diz Online (a própria máquina conta como online).
    Tailscale travada/sem resposta = só a porta decide (nunca marca ninguém como fora por falha do próprio teste)."""
    out = {}
    try:
        r = subprocess.run([TS_EXE, "status", "--json"], capture_output=True, text=True, timeout=20,
                           creationflags=0x08000000 if WINDOWS else 0)
        d = json.loads(r.stdout)
        for p in list((d.get("Peer") or {}).values()) + [dict(d.get("Self") or {}, Online=True)]:
            for ip in p.get("TailscaleIPs") or []:
                out[ip] = bool(p.get("Online"))
    except Exception:  # noqa: BLE001 — Tailscale muda, trava ou não existe: a porta decide
        pass
    for nome, ip in VIGIADAS.items():
        if not out.get(ip) and _tcp(ip, PORTAS.get(nome, 22)):
            out[ip] = True
    return out


def _enviar(texto, prioridade=False):
    if WINDOWS:  # no PC1: pelo portão único dos avisos (D:\video-fila\avisos.py)
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            if prioridade:
                return avisos.prioridade(texto, "vigia mútuo") > 0
            avisos.enviar(texto, "vigia mútuo", importante=True)
            return True
        except Exception:  # noqa: BLE001
            return False
    try:
        cfg = json.loads((PASTA / "telegram.json").read_text(encoding="utf-8"))
        dados = urllib.parse.urlencode({"chat_id": cfg["chat_id"], "text": texto}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage", data=dados, timeout=20)
        return True
    except Exception:  # noqa: BLE001
        return False


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _placa_pc2():
    """Na volta do PC2: o que o vigia da placa (C:\\pc2-rede\\estado.json) fez na última queda. '' se não deu pra ler."""
    if not WINDOWS:
        return ""
    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "pc2",
                            "type C:\\pc2-rede\\estado.json"], capture_output=True, timeout=40,
                           creationflags=0x08000000)
        e = json.loads(r.stdout.decode("utf-8-sig", errors="replace"))
        h = (e.get("historico") or [])[-1:]
        if not h:
            return ""
        h = h[0]
        return (f" O vigia da placa reiniciou o Wi-Fi {h.get('reinicios', 0)}x; a conexão voltou depois de "
                f"{h.get('minutos')} min." if h.get("reinicios") else "")
    except Exception:  # noqa: BLE001
        return ""


def passada(eu):
    agora = time.time()
    on = _online()
    vivo = {n: on.get(ip, False) for n, ip in VIGIADAS.items()}
    vivo[eu] = True
    # PC1 ligado mas o sistema parado: só os notebooks sabem (o painel.json que o PC1 manda parou de chegar)
    if not WINDOWS and vivo.get("PC1"):
        try:
            idade = agora - (PASTA / "painel.json").stat().st_mtime
            if idade > PC1_PARADO_S:
                vivo["PC1 (sistema de vídeos)"] = False
            else:
                vivo["PC1 (sistema de vídeos)"] = True
        except OSError:
            pass
    est = _ler()
    off_desde, avisado = est.setdefault("off_desde", {}), est.setdefault("avisado", {})
    # revisão 23/10: PC1 ligado mas com o sistema parado NÃO serve pra avisar (era sempre ele o escolhido e ninguém
    # avisava nem o próprio travamento nem a queda dos notebooks)
    pode_avisar = dict(vivo)
    if vivo.get("PC1 (sistema de vídeos)") is False:
        pode_avisar["PC1"] = False
    quem_avisa = next((n for n in ORDEM if pode_avisar.get(n)), eu)
    msgs = []
    for nome, ok in vivo.items():
        if ok:
            off_desde.pop(nome, None)
            a = avisado.pop(nome, None)
            # "voltou" sai de quem avisou a queda; se quem avisou também caiu, sai de quem avisa agora (revisão 23/10)
            if isinstance(a, dict) and (a.get("enviei") or (quem_avisa == eu and not pode_avisar.get(a.get("por", "")))):
                msgs.append((f"✅ {nome} VOLTOU (visto pelo {eu})." + (_placa_pc2() if nome == "PC2" else ""),
                             nome, nome in PRIORIDADE))
            continue
        desde = off_desde.setdefault(nome, agora)
        if agora - desde < max(AVISO_TELEGRAM_S, MIN_OFF_MAQ.get(nome, MIN_OFF_S)):
            continue
        a = avisado.get(nome)
        # máquina de PRIORIDADE ainda fora: repete a cada 30 min (só quem mandou o 1º aviso repete)
        repetir = (isinstance(a, dict) and a.get("enviei") and nome in PRIORIDADE and quem_avisa == eu
                   and agora - a.get("t", agora) >= REPETIR_S)
        if a and not repetir:
            continue
        if quem_avisa == eu:
            minutos = int((agora - desde) // 60)
            dica = (" Está ligado, mas parou de mandar os dados do telão: o controlador pode ter travado." if "sistema" in nome
                    else " O vigia da placa Wi-Fi já tentou reiniciar sozinho e não resolveu: desative e ative a placa de "
                         "rede dele (ou reinicie o PC2)." if nome == "PC2"
                    else " Confira se está ligado e com internet.")
            msgs.append((f"🔴 {nome} {'AINDA ' if repetir else ''}SEM SINAL há {minutos} min (visto pelo {eu})." + dica,
                         nome, nome in PRIORIDADE))
            avisado[nome] = {"t": agora, "enviei": True, "por": eu}
        else:
            avisado[nome] = {"t": agora, "enviei": False, "por": quem_avisa}  # outra máquina avisa (e avisa a volta)
    for m, quem, prio in msgs:
        try:
            ok = _enviar(m, prio)
        except Exception:  # noqa: BLE001
            ok = False
        if not ok and isinstance(avisado.get(quem), dict) and avisado[quem].get("t") == agora:
            avisado.pop(quem)  # não saiu: desmarca pra tentar de novo na próxima passada (revisão 23/10)
    est["eu"], est["em"], est["vivos"] = eu, agora, vivo
    # pro telão (vitrine_painel): quem está fora há 6+ min
    est["fora"] = {n: int((agora - t) // 60) for n, t in off_desde.items() if agora - t >= MIN_OFF_MAQ.get(n, MIN_OFF_S)}
    msgs = [m for m, _q, _p in msgs]
    PASTA.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(est, ensure_ascii=False), encoding="utf-8")
    return msgs


def laco(eu, a_cada_s=120):
    while True:
        try:
            passada(eu)
        except Exception:  # noqa: BLE001
            pass
        time.sleep(a_cada_s)


if __name__ == "__main__":
    print(passada(sys.argv[1] if len(sys.argv) > 1 else "PC1"))
