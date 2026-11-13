# -*- coding: utf-8 -*-
r"""baixar_trilhas.py — baixa trilhas do YouTube pra pasta de AVALIAÇÃO do dono (não entra no vídeo sozinho).

  python bin/baixar_trilhas.py "phonk brasileiro" "cornfield chase"   # 1º resultado de cada busca
  python bin/baixar_trilhas.py --lista config/trilhas_buscar.txt      # uma busca por linha (# = comentário)
  python bin/baixar_trilhas.py --n 3 "funk slowed em alta"            # 3 resultados da busca

Vai pra D:\hipercool-materiais\_curadoria\_a_aprovar\trilhas\<data>\ em mp3 192k, nome = título.
Pula vídeo com mais de 8 min (mix/compilado) e o que já foi baixado (arquivo .baixados.txt).
Se o YouTube bloquear (429/"sign in"/bot), tenta de novo por um proxy de secrets/proxies.txt.
Aprovou? Mova o mp3 pra assets/trilhas/prioritarias/ (e, se quiser, ponha o clima em
prioritarias/climas.json); a partir daí ela toca com prioridade (fx_music).
"""
import argparse
import random
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
MATERIAIS = Path(r"D:\hipercool-materiais")
DESTINO = MATERIAIS / "_curadoria" / "_a_aprovar" / "trilhas"
PROXIES = PROJECT / "secrets" / "proxies.txt"
BLOQUEIO = re.compile(r"429|sign in|confirm you.re not a bot|unable to download webpage|timed out|403", re.I)


def _proxies():
    try:
        linhas = PROXIES.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    # linha = "http://<USUARIO>:<SEGREDO_REMOVIDO>@host:porta   # comentário" -> só o 1º pedaço
    return [p.split()[0] for p in linhas if p.strip() and not p.lstrip().startswith("#")]


def _yt(args, proxy=None):
    cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--ffmpeg-location", str(MATERIAIS / "bin"), *args]
    if proxy:
        cmd += ["--proxy", proxy]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)


def baixar(busca, pasta, n=1):
    """Baixa os n primeiros resultados da busca. Devolve a lista de títulos baixados."""
    arquivo_log = pasta / ".baixados.txt"
    args = [f"ytsearch{n}:{busca}", "-x", "--audio-format", "mp3", "--audio-quality", "192K",
            "--match-filter", "duration < 480 & !is_live", "--download-archive", str(arquivo_log),
            "-o", str(pasta / "%(title).80s [%(id)s].%(ext)s"), "--print", "after_move:%(title)s"]
    r = _yt(args)
    if r.returncode != 0 and BLOQUEIO.search(r.stderr):
        for proxy in random.sample(_proxies(), min(3, len(_proxies()))):
            r = _yt(args, proxy)
            if r.returncode == 0 or not BLOQUEIO.search(r.stderr):
                break
    if r.returncode != 0:
        print(f"  [!] {busca}: {r.stderr.strip().splitlines()[-1][:160] if r.stderr.strip() else 'falhou'}")
    return [t for t in r.stdout.splitlines() if t.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("buscas", nargs="*")
    ap.add_argument("--lista", help="arquivo com uma busca por linha")
    ap.add_argument("--n", type=int, default=1, help="resultados por busca")
    ap.add_argument("--pasta", default=str(DESTINO / date.today().isoformat()))
    a = ap.parse_args()
    buscas = list(a.buscas)
    if a.lista:
        buscas += [l.strip() for l in Path(a.lista).read_text(encoding="utf-8").splitlines()
                   if l.strip() and not l.lstrip().startswith("#")]
    pasta = Path(a.pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    total = 0
    for b in buscas:
        titulos = baixar(b, pasta, a.n)
        total += len(titulos)
        for t in titulos:
            print(f"  ok  {b}  ->  {t}")
    print(f"{total} trilha(s) nova(s) em {pasta}")


if __name__ == "__main__":
    main()
