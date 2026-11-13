"""Dona 26/10: cópia pra ela ACOMPANHAR os recaps longos, em D:\\hipercool-materiais\\recap-longos-prontos. Os vídeos de
verdade ficam no manhwa-drive (videos-backup/anime/1_youtube_pendente) aguardando postagem; no PC ficam só 2 cópias:
o PRÓXIMO a postar (o mais antigo ainda no Drive) e o ÚLTIMO feito. O resto é apagado do PC só depois de conferir que
o original está no Drive com o mesmo tamanho. Abre o Explorer na pasta no fim.

    python abrir_prontos.py
"""
import json
import subprocess
from pathlib import Path
import sys as _sys
if _sys.platform == "win32":  # dona 26/10: rclone/ssh/scp/python filhos SEM janela na tela (PC1 e PC2)
    for _p in (r"D:\hipercool-materiais\comum", r"C:\hipercool-materiais\comum"):
        if Path(_p, "sem_janela.py").exists():
            _sys.path.append(_p)
            import sem_janela  # noqa: F401,E402
            break

RCLONE = r"D:\tools\rclone.exe"
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
PASTA = Path(r"D:\hipercool-materiais\recap-longos-prontos")
DESDE = "2026-10-25 14:00"  # antes disso = longos sem as melhorias


def _tam_drive(remoto):
    r = subprocess.run([RCLONE, "lsjson", remoto], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)[0]["Size"] if r.returncode == 0 else None
    except (ValueError, IndexError, KeyError):
        return None


def main():
    PASTA.mkdir(exist_ok=True)
    longos = []
    for nj in FICHAS.glob("*/nuvem.json"):
        d = json.loads(nj.read_text(encoding="utf-8"))
        if d.get("formato") == "deitado" and d.get("feito_em", "") >= DESDE:
            nome = f"{d['feito_em'][:16].replace(':', 'h').replace(' ', '_')}_{nj.parent.name[:60]}.mp4"
            longos.append((d["feito_em"], nome, d["drive"]))
    longos.sort()
    try:  # já postado ou reprovado (postar_longos.py) não é mais "o próximo a postar"
        est = json.loads((Path(__file__).with_name("longos_postados.json")).read_text(encoding="utf-8"))
        fora = {p["nome"] for p in est.get("postados", [])} | set(est.get("reprovados", []))
    except (OSError, ValueError):
        fora = set()
    no_drive = [x for x in longos if not any(x[1].endswith(f + ".mp4") for f in fora) and _tam_drive(x[2])]
    manter = {x[1]: x for x in (no_drive[:1] + longos[-1:])}  # próximo a postar + último feito
    for nome, (_, _, remoto) in manter.items():
        alvo = PASTA / nome
        if not alvo.exists():
            subprocess.run([RCLONE, "copyto", remoto, str(alvo)], capture_output=True)
    por_nome = {x[1]: x for x in longos}
    for f in PASTA.glob("*.mp4"):
        if f.name in manter:
            continue
        info = por_nome.get(f.name)
        if info and _tam_drive(info[2]) == f.stat().st_size:
            f.unlink()
        else:
            print(f"mantido (original não conferido no Drive): {f.name}")
    print("no PC:", ", ".join(sorted(manter)) or "nada")
    subprocess.Popen(["explorer", str(PASTA)])


if __name__ == "__main__":
    main()
