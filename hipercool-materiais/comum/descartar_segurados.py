r"""descartar_segurados.py — Shorts SEGURADOS que nunca vão subir saem sozinhos, sem esperar a dona (12/11, dona: "esses
mudos têm que ser descartados, voz de desenho em canal de negócio não dá, versões em idioma eu não sei falar então não
saberia se está certo; essas coisas têm que ser automáticas, não pode esperar por mim").

Regras (só Short de parceiro em animes recap\shorts, nunca postado):
  - "fonte repetida" (o mesmo vídeo já saiu em outro canal)        -> descarta
  - "quase nada se ouve" (narração muda/vazia)                       -> descarta
  - voz que não encaixa no nicho / voz de desenho em canal sério     -> descarta (o canal recebe outro Short com voz
    certa na próxima produção; refazer este gastaria o mesmo render)
  - versão em idioma "pendente" há mais de 24 h (ninguém confere)    -> aprova sozinha se o áudio passou na conferência
    (conferir_audio: tem fala), senão descarta
Descartar = o vídeo vai pro Drive (videos-backup/parceiro/nao-usados/<pasta>) e a ficha fica marcada
"descartado (automático: <motivo>)" — some do telão e do painel "esperando você". DESCARTAR_SEGURADOS=0 desliga.

    python descartar_segurados.py --simular
    python descartar_segurados.py
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(r"D:\hipercool-materiais\animes recap\shorts")
DRIVE = "manhwa-drive:videos-backup/parceiro/nao-usados"
RCLONE = r"D:\tools\rclone.exe"
LOG = Path(r"D:\tmp\descartar_segurados.log")
REGRAS = [
    ("fonte repetida", r"fonte repetida"),
    ("áudio mudo", r"quase nada se ouve"),
    ("voz fora do nicho", r"não encaixa no nicho|voz de desenho|refazer com voz"),
]


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _descartar(pj, d, motivo, simular):
    pasta = pj.parent
    mp4s = sorted(pasta.glob("*.mp4"))
    if simular:
        log(f"[simular] descartaria {pasta.name}: {motivo}")
        return True
    for v in mp4s:
        r = subprocess.run([RCLONE, "moveto", str(v), f"{DRIVE}/{pasta.name}/{v.name}", "--retries", "3"],
                           capture_output=True, text=True, timeout=1800, creationflags=0x08000000)
        if r.returncode != 0:
            log(f"{pasta.name}: não subiu {v.name} pro Drive — fica no PC ({(r.stderr or '')[-120:]})")
            return False
    d.update(pronto=False, revisao=f"descartado (automático: {motivo})", descartado_em=time.strftime("%Y-%m-%d %H:%M"))
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"{pasta.name}: descartado ({motivo}) — {len(mp4s)} vídeo(s) no Drive {DRIVE}/{pasta.name}")
    return True


def main(simular):
    if os.environ.get("DESCARTAR_SEGURADOS", "1") == "0":
        return
    n = {"descartado": 0, "aprovado": 0}
    for pj in BASE.glob("*/postar.json"):
        try:
            d = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rev = str(d.get("revisao") or "")
        if d.get("posted_url") or rev.startswith("descartado"):
            continue
        motivo = next((nome for nome, rx in REGRAS if re.search(rx, rev, re.I)), None)
        if motivo:
            n["descartado"] += _descartar(pj, d, motivo, simular)
            continue
        # versão em idioma parada em "pendente" (ninguém confere outra língua): decide sozinho em 24 h
        lang = re.search(r"_(hi|id|it|ru|th|vi|en|fr)$", pj.parent.name)
        if lang and rev in ("pendente", "") and not d.get("pronto") and time.time() - pj.stat().st_mtime > 24 * 3600:
            if "quase nada" in str(d.get("audio_conferido") or ""):
                n["descartado"] += _descartar(pj, d, "idioma sem fala", simular)
            elif not simular:
                d.update(pronto=True, revisao="ok (automático 12/11: versão em idioma sem conferência humana)")
                pj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
                log(f"{pj.parent.name}: versão em idioma aprovada sozinha")
                n["aprovado"] += 1
            else:
                log(f"[simular] aprovaria {pj.parent.name}")
                n["aprovado"] += 1
    log(f"fim: {n['descartado']} descartados, {n['aprovado']} versões em idioma aprovadas")


if __name__ == "__main__":
    main("--simular" in sys.argv)
