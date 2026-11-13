r"""Abre uma por uma as contas deslogadas DESTE PC (PC1) no cofre, visível, para a dona logar.
Espera o Chrome fechar antes de abrir a próxima. Roda oculto (pythonw ou sem janela).

  python logar_deslogadas_pc1.py          # abre todas em sequência
  python logar_deslogadas_pc1.py --so youtube   # só YouTube
  python logar_deslogadas_pc1.py --so flow      # só Flow
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cofre

# ── contas que precisam logar neste PC (levantadas em 03/11 20h) ──

# YouTube: confirmados sem login (prioridade)
YT = [
    ("rezaulkarimul355", "mundoquenaoexiste — deslogado de verdade"),
    ("inovaremanhwaversehindi", "inovare_hindi — sem login"),
    ("emersonjosiel2027", "historiasemframes — perfil não logado"),
    ("emersonjosiel2031", "fiodameada — conta logada sem permissão no canal"),
]

# Flow: cookies vencidos neste PC (pc1 / sem sufixo no saude.json)
FLOW = [
    ("emersonjosiel2027", "Flow pc1 — preso desde 29/10"),
    ("fabiovideoseducativos", "Flow pc1 — preso desde 31/10"),
    ("emersonjosiel649", "Flow pc1 — preso desde 31/10"),
    ("inovaremanhwabr", "Flow pc1 — preso desde 31/10"),
    ("canalalucinaai", "Flow pc1"),
    ("fabricadeautomacoes0", "Flow pc1 — fabricadeautomacoes"),
    ("seebotsia", "Flow pc1"),
    ("emerson2030", "Flow pc1 — emersonjosiel2030"),  # no saude aparece sem o prefixo
    ("mundosolar1995", "Flow pc1 — mundosolar"),
    ("inovaremanhwaverseesp", "Flow pc1"),
    ("jogoscomia", "Flow pc1 — jogoscomia2"),
]

# Google Fotos
FOTOS = [
    ("aulacomia", "Google Fotos — pediu login 29/10"),
    ("aulasrevolution", "Google Fotos — pediu login 29/10"),
    ("canalanimescomia", "Google Fotos — pediu login 29/10"),
    ("fabricadeautomacoesia", "Google Fotos — pediu login 29/10"),
]

# Telão
TELAO = [
    ("contapessoal", "Telão x200ma deslogado (401 desde 01/11)"),
]

# 03/11 22h: cofre.checar() de verdade — só estas 9 estão com o Google morto neste PC (as outras deram vivo)
MORTAS = [
    ("filmescomia1", "Google morto (checar 03/11)"),
    ("fabricadeautomacoesia", "Google morto (checar 03/11)"),
    ("filmescomia00", "Google morto (checar 03/11)"),
    ("emersonjosiel03", "Google morto — pasta estava com a 02 logada"),
    ("andreluizdias384", "Google morto (checar 03/11)"),
    ("emersonjosiel2028", "Google morto (checar 03/11)"),
    ("inovaremanhwaverse3", "Google morto (checar 03/11)"),
    ("inovaremanhwaverse4", "Google morto (checar 03/11)"),
    ("revolutionemerson7", "Google morto (checar 03/11)"),
]

TODAS = MORTAS

LOG = Path(__file__).resolve().parent / "logar_deslogadas_pc1.log"


def _log(msg):
    from datetime import datetime
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def main():
    filtro = None
    if "--so" in sys.argv:
        idx = sys.argv.index("--so")
        filtro = sys.argv[idx + 1].lower() if idx + 1 < len(sys.argv) else None

    if filtro == "youtube":
        lista = YT
    elif filtro == "flow":
        lista = FLOW
    elif filtro == "fotos":
        lista = FOTOS
    else:
        lista = TODAS

    _log(f"=== Início: {len(lista)} contas para logar (filtro={filtro}) ===")

    # desduplicar (emersonjosiel2027 aparece em YT e Flow)
    vistos = set()
    dedup = []
    for conta, motivo in lista:
        if conta not in vistos:
            vistos.add(conta)
            dedup.append((conta, motivo))

    for i, (conta, motivo) in enumerate(dedup, 1):
        _log(f"[{i}/{len(dedup)}] Abrindo {conta} — {motivo}")
        try:
            porta, proc = cofre.abrir(conta, url="https://accounts.google.com/", visivel=True)
        except Exception as e:
            _log(f"  ERRO ao abrir: {e}")
            continue

        if proc is None:
            _log(f"  Já estava aberto (porta {porta}). Pulando.")
            continue

        _log(f"  Chrome aberto na porta {porta}. Esperando você logar e fechar...")
        proc.wait()
        cofre.fechar(None, None, conta)
        _log(f"  Fechou. Próxima em 3 s...")
        time.sleep(3)

    _log("=== Fim ===")


if __name__ == "__main__":
    main()
