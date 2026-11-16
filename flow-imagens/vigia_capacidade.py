# -*- coding: utf-8 -*-
"""Vigia da capacidade de imagens do Flow (dona 16/11: "corrija pra que isso não aconteça mais, nem nos testes nem
nos normais").

Causa (16/11): o limite de Chromes de imagem (logs\\capacidade.json) caía pra 1 no PC2/STI/desktop por falha que não
era da máquina, e ficava preso; 413 de 417 pedidos falharam com máquina LIVRE. O gera_imagem foi corrigido, mas
processo antigo que importa o gera_imagem (produto.diario, carrossel_marca, foto_na_hora) segue com o código velho
até reiniciar — e qualquer bug novo pode prender de novo. Este vigia é a rede de segurança:
  a cada 10 min mede cada máquina 1 vez (1 ssh cada, nunca rajada) e, se o limite está abaixo do piso com a máquina
  folgada (CPU <= 60%, RAM livre >= 2 GB), devolve o piso e anota em logs\\vigia_capacidade.log.
Tarefa do Windows VigiaCapacidadeFlow (oculta). VIGIA_CAPACIDADE=0 desliga.
"""
import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, r"D:\postador-de-videos\bin")
LOG = BASE / "logs" / "vigia_capacidade.log"
# piso por máquina (o que ela aguenta folgada; o cap_ok sobe acima disso sozinho)
PISO = {"pc2": 4, "sti": 5, "desktop": 3}
CPU_FOLGA, RAM_FOLGA_MB = 60, 2000


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(time.strftime("%d/%m %H:%M:%S ") + m + "\n")


def main():
    if os.environ.get("VIGIA_CAPACIDADE") == "0":
        return
    import gera_imagem as g
    for maq, piso in PISO.items():
        atual = g.cap_limite(maq)
        if atual >= piso:
            continue
        med = g.medir(maq)
        if not med:
            log(f"{maq}: limite {atual} < {piso}, mas não respondeu — não mexo")
            continue
        if med["cpu"] > CPU_FOLGA or med["ram_mb"] < RAM_FOLGA_MB:
            log(f"{maq}: limite {atual} (cpu {med['cpu']}%, RAM {med['ram_mb']} MB) — ocupada de verdade, fica")
            continue
        try:
            baixou = json.loads(Path(g.CAP_ARQ).read_text("utf-8")).get(maq, {}).get("baixou")
        except (OSError, ValueError):
            baixou = None

        def sobe(e, piso=piso):
            e.update(limite=piso, ok=0, teto=None, teto_ate=0)
            return piso
        g._cap_mexer(maq, sobe)
        log(f"{maq}: limite {atual} -> {piso} (folgada: cpu {med['cpu']}%, RAM {med['ram_mb']} MB); "
            f"quem tinha baixado: {baixou}")
        time.sleep(2)


if __name__ == "__main__":
    main()
