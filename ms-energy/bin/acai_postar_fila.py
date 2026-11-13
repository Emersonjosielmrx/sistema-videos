# -*- coding: utf-8 -*-
r"""acai_postar_fila.py — posta 1 item da fila_para_postar do açaí (carrossel_<id>_C ou arquivado_<id>) e registra
no histórico (log + .txt da pasta de prints). Dona 05/11 13h: paleta C escolhida; "vá postando enquanto gera".
    D:\veo\venv\Scripts\python.exe acai_postar_fila.py <pasta>
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\ms-energy\bin")
import acai  # noqa: E402

HIST = Path(r"D:\ms-energy\assets\acai\prints_perfil\HISTORICO_DO_QUE_FOI_FEITO.txt")


def legenda_final(leg):
    """05/11 dona: TODA legenda/comentário com os 2 endereços e os 2 números (rodapé único do acai_design)."""
    import acai_design
    corpo = leg.split("\n📲")[0].split("\n📍")[0].strip()
    tags = next((ln for ln in reversed(leg.strip().splitlines()) if ln.strip().startswith("#")), acai.HASHTAGS)
    return f"{corpo}\n\n{acai_design.RODAPE_LEG}\n\n{tags}"


def postar(pasta):
    pasta = Path(pasta)
    leg = legenda_final((pasta / "legenda.txt").read_text("utf-8"))
    ig = acai._postar()
    if (pasta / "reel.mp4").exists():
        code = ig.reel(str(pasta / "reel.mp4"), leg)
        link, tipo = f"https://www.instagram.com/reel/{code}/", "reel"
    else:
        imgs = sorted(pasta.glob("*.jpg"), key=lambda p: int(p.stem) if p.stem.isdigit() else 99)
        code = ig.carrossel([str(i) for i in imgs], leg)
        link, tipo = f"https://www.instagram.com/p/{code}/", "carrossel"
    (pasta / "postado.json").write_text(json.dumps({"link": link, "em": datetime.now().isoformat(timespec="seconds")}),
                                        "utf-8")
    acai.log(f"PUBLICADO {tipo} {pasta.name}: {link}")
    with HIST.open("a", encoding="utf-8") as f:
        f.write(f" {datetime.now():%H:%M}  PUBLICADO {tipo} ({pasta.name}, paleta C) — {link}\n")
    print(link)
    return link


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    postar(sys.argv[1])
