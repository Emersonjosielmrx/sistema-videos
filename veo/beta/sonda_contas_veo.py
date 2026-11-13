#!/usr/bin/env python3
"""sonda_contas_veo.py - as contas Google do Veo ainda estao logadas? (item BX-07 de D:\\veo\\docs\\PLANO_MELHORIAS_VEO.md)

Antes a conta so "caia" quando o Flow falhava no meio de uma geracao (exit 3/7). Aqui, 1x por dia e SEM gerar nada:
para cada sessao de contas.py, acha a conta do cofre pela juncao do perfil (chrome_gen_<x> -> cofre\\perfis\\<y>) e
roda o checar do cofre (D:\\logins-google\\cofre.py: abre o Chrome, myaccount.google.com, fecha).
  - morta: cooldown de 24 h em logs\\sessoes_status.json (o gerador pula a conta) + linha "DESLOGADA: <apelido>" no log,
    que o notificar_telegram transforma em aviso;
  - viva: tira o cooldown que ESTA sonda tinha posto.
Sessao com o Chrome aberto (gerando agora) fica para a proxima. Roda no ciclo das 06:40 (postar_tudo_auto.bat).
"""
import datetime
import importlib.util
import json
import os
import socket
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import contas  # noqa: E402

COFRE = Path(r"D:\logins-google\cofre.py")
STATUS = BASE / "logs" / "sessoes_status.json"
LOG = BASE / "logs" / "sonda_contas_veo.log"
MOTIVO = "deslogada (sonda_contas_veo)"


def log(msg):
    linha = f"[{datetime.datetime.now():%d/%m %H:%M}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def porta_aberta(porta):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", int(porta))) == 0


def main():
    spec = importlib.util.spec_from_file_location("cofre", COFRE)
    cofre = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cofre)
    por_pasta = {os.path.normcase(str(e.get("pasta"))): (email, e) for email, e in cofre._ler()["contas"].items()}
    st = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
    for s in contas.SESSOES:
        perfil = BASE / s["profile"]
        try:
            alvo = os.path.normcase(os.path.realpath(perfil))
        except OSError:
            alvo = ""
        email, e = por_pasta.get(alvo, (None, None))
        if not email:
            log(f"{s['session']}: perfil {perfil.name} nao aponta para conta do cofre - pulado")
            continue
        if porta_aberta(s["port"]):
            log(f"{s['session']}: Chrome aberto (gerando agora) - fica para a proxima")
            continue
        cofre.checar(e["apelido"])
        estado = (cofre._ler()["contas"].get(email) or {}).get("google", "?")
        info = st.setdefault(s["session"], {})
        if estado == "morto":
            info.update(cooldown_until=(datetime.datetime.now() + datetime.timedelta(hours=24)).isoformat(timespec="seconds"),
                        last_motivo=MOTIVO)
            log(f"DESLOGADA: {e['apelido']} (sessao {s['session']}) -> python D:\\logins-google\\cofre.py logar {e['apelido']}")
        else:
            if info.get("last_motivo") == MOTIVO:
                info.pop("cooldown_until", None)
                info.pop("last_motivo", None)
            log(f"{s['session']}: {estado}")
    STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    # 22/10 (VEO-04): a sonda só dizia vivo/morto — conta SEM CRÉDITO (o MS Energy gasta as mesmas contas de
    # madrugada) ficava muda. "SEM CREDITO:" vira aviso no Telegram (padrão novo no notificar_telegram).
    sem = [(nome, i) for nome, i in st.items() if isinstance(i, dict) and i.get("status") == "EXHAUSTED"]
    for nome, i in sem:
        log(f"SEM CREDITO: {nome} (renova {str(i.get('creditos_renova_em', '?'))[5:16]}; "
            f"motivo: {i.get('last_motivo', '?')})")
    if sem and len(sem) >= len([s for s in contas.SESSOES]):
        log("SEM CREDITO: TODAS as contas do Flow estao esgotadas - o Veo nao gera ate renovar")


if __name__ == "__main__":
    main()
