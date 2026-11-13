# -*- coding: utf-8 -*-
r"""tools/colher_notebooks.py — adianta a 1ª colheita dos cookies do Instagram NAS máquinas (D23: cada PC usa os
próprios cookies, nunca saem dele). Sem isso o HTTP de lá só liga depois de um post pelo Chrome de lá.
Respeita a vez da máquina (um navegador por vez: telão, Veo, login) e abre 1 conta por vez.

    python tools\colher_notebooks.py [maquina ...]
"""
import json
import sys

sys.path.insert(0, r"D:\postador-de-videos\bin")
import maquina_remota as mr  # noqa: E402

REUSO = r"D:\postador-de-videos\config\reuso_plataformas.json"


def main():
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    alvo = sys.argv[1:] or ["x200ma", "acer", "pc2"]
    contas = json.load(open(REUSO, encoding="utf-8"))["instagram"]["contas"]
    for m in alvo:
        rem = mr.Remoto(m)
        if not rem.vivo():
            print(m, "fora do ar")
            continue
        vez = mr.reservado(m)
        if vez:
            print(m, f"com a vez de '{vez}': pula")
            continue
        mr.ocupar(m, "colher nsn", 15)
        try:
            for nome, r in contas.items():
                if m not in (r.get("maquina") or []) or r.get("sem_http"):
                    continue
                perfil = (r.get("cofre") or f"ig_{nome}").lower()
                try:  # 30/10: erro numa conta (ssh, Chrome) não pula as outras da máquina
                    if rem.nsn_tem_cookie(perfil):
                        print(m, nome, "já tem cookie")
                        continue
                    # renova a vez a cada conta: com muitas contas a reserva de 15 min vencia no meio e o Veo abria
                    # outro Chrome junto (regra: um navegador por vez)
                    if mr.reservado(m, "colher nsn"):  # outro pegou a vez (reserva venceu): para esta máquina
                        print(m, f"perdeu a vez para '{mr.reservado(m, 'colher nsn')}': para aqui")
                        break
                    mr.ocupar(m, "colher nsn", 15)
                    try:
                        rem.abrir(r.get("perfil_remoto") or perfil, url="https://www.instagram.com/")
                        print(m, nome, "colhido" if rem.nsn_colher(perfil) else "NÃO colheu (deslogado lá?)")
                    finally:
                        rem.fechar()
                except Exception as e:  # noqa: BLE001
                    print(m, nome, f"erro: {type(e).__name__}: {str(e)[:120]}")
        finally:
            mr.liberar(m, "colher nsn")


if __name__ == "__main__":
    main()
