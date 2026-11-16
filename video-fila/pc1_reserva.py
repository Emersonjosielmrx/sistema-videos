r"""pc1_reserva.py — o PC1 é do VS Code (dona 15/11: "mude todos os pesados e médios para os outros, mas se precisar podem
rodar aqui; mas pra isso todos os outros já devem estar ocupados ao máximo").

pode_pesado() -> (bool, motivo):
  - sem o arquivo estado\pc1_sem_render.on: sempre pode (comportamento antigo);
  - com ele: só pode se TODAS as máquinas de render (OUTRAS, padrão pc2,desktop,sti) estão trabalhando na última medida
    do uso_maquinas.py (estado\uso_maquinas.jsonl, <= 15 min). Máquina sem medida/medida velha conta como LIVRE (não
    libera o PC1 por falta de dado).
Usado por controlador._bloqueio (render) e parceiro_diario.producao. PC1_OUTRAS="pc2,desktop,sti" muda a lista.
"""
import json
import os
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
TRAVA = BASE / "estado" / "pc1_sem_render.on"
USO = BASE / "estado" / "uso_maquinas.jsonl"


def _ultimas():
    ult = {}
    try:
        with open(USO, encoding="utf-8") as f:
            for linha in f.readlines()[-600:]:
                try:
                    r = json.loads(linha)
                    ult[r["m"]] = r
                except (ValueError, KeyError):
                    pass
    except OSError:
        pass
    return ult


def pode_pesado():
    if not TRAVA.exists():
        return True, "trava desligada"
    outras = [x for x in os.environ.get("PC1_OUTRAS", "pc2,desktop,sti").split(",") if x]
    ult, livres = _ultimas(), []
    for h in outras:
        r = ult.get(h)
        try:
            idade = (datetime.now() - datetime.fromisoformat(r["t"])).total_seconds() / 60 if r else 999
        except (ValueError, KeyError):
            idade = 999
        # "trab" do uso_maquinas segue a CPU (PC2 com 2 cortes baixando = trab false); vale também "fazendo" com trabalho
        ocupada = bool(r) and (r.get("trab") or (r.get("fazendo") and r.get("fazendo") != "livre"
                                                and "livre" not in str(r.get("fazendo")).lower()[:6]))
        if idade > 15 or not ocupada:
            livres.append(h)
    if livres:
        return False, f"PC1 reservado ao VS Code — ainda há máquina livre: {', '.join(livres)}"
    return True, f"todas ocupadas ({', '.join(outras)}) — PC1 ajuda"


if __name__ == "__main__":
    print(pode_pesado())
