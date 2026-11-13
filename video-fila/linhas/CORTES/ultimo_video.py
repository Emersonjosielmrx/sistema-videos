# -*- coding: utf-8 -*-
"""ultimo_video.py — pasta com o ÚLTIMO Short feito, sempre atualizada (dono 26/10/2026: "deixe uma pasta sempre com o
último vídeo feito aberta pra eu ver; se eu estiver no PC posso dar minhas opiniões").

D:\\video-fila\\linhas\\CORTES\\ULTIMO_VIDEO\\: ultimo.mp4 (+ anterior_1/2.mp4), INFO.txt e OPINIOES.txt (o dono
escreve; a linha CORTES lê a cada ciclo). Vídeo por hard link (mesmo disco D:): não ocupa espaço a mais.
Tarefa agendada Cortes_UltimoVideo, a cada 5 min.
"""
import json
import os
from datetime import datetime
from pathlib import Path

SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")
PASTA = Path(r"D:\hipercool-materiais\CORTES_ULTIMO_VIDEO")  # 27/10: dono não achava em linhas\CORTES (vídeo pra ver = hipercool-materiais)
ESTADO = PASTA / ".atual.json"
OPINIOES = PASTA / "OPINIOES.txt"


def _ultimo():
    cands = [p for p in SHORTS.glob("*/video.mp4") if not p.parent.name.startswith("_")]
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def _ligar(origem, destino):
    destino.unlink(missing_ok=True)
    try:
        os.link(origem, destino)
    except OSError:
        import shutil
        shutil.copy2(origem, destino)


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    if not OPINIOES.exists():
        OPINIOES.write_text("Escreva aqui o que achou do vídeo (uma linha por vídeo, com a data). A linha CORTES lê a "
                            "cada ciclo e responde no DECISOES.md.\n\n", encoding="utf-8")
    v = _ultimo()
    if not v:
        return
    try:
        atual = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        atual = {}
    if atual.get("pasta") == v.parent.name:
        return
    for i in (2, 1):  # o anterior desce uma posição
        de = PASTA / ("ultimo.mp4" if i == 1 else f"anterior_{i - 1}.mp4")
        if de.exists():
            _ligar(de, PASTA / f"anterior_{i}.mp4")
    _ligar(v, PASTA / "ultimo.mp4")
    try:
        pj = json.loads((v.parent / "postar.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pj = {}
    info = [f"Pasta: {v.parent}", f"Feito em: {datetime.fromtimestamp(v.stat().st_mtime):%d/%m %H:%M}",
            f"Canal: {pj.get('canal', '?')}  |  nicho: {pj.get('midia', '?')}  |  parceiro: {pj.get('parceiro', '?')}",
            f"Título: {pj.get('titulo', '?')}", f"Fonte: {pj.get('fonte', '?')}",
            "", "Anteriores: anterior_1.mp4 (o de antes), anterior_2.mp4.",
            "Opiniões: escreva no OPINIOES.txt desta pasta."]
    (PASTA / "INFO.txt").write_text("\n".join(info) + "\n", encoding="utf-8")
    ESTADO.write_text(json.dumps({"pasta": v.parent.name, "quando": datetime.now().isoformat(timespec="seconds")}),
                      encoding="utf-8")


if __name__ == "__main__":
    main()
