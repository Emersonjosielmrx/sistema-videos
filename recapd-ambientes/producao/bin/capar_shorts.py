# -*- coding: utf-8 -*-
r"""capar_shorts.py — capa de IA "que faz clicar" nos Shorts de anime/manhwa (dona 14/11: "pode testar várias coisas
que chamem a atenção pra pessoa clicar: capas estilo dos longos, beijos e amassos fake etc. — faça o máximo de teste
de capas nesse estilo pros Shorts").

Contexto: 68 de 95 Shorts de anime/manhwa de 13-14/11 saíram com capa = quadro do vídeo (postar.json sem "thumb"). E no
Short o YouTube NÃO aceita miniatura enviada pelo Studio: a capa que aparece é um quadro do vídeo. Então:
  1) gera a capa IA 9:16 (capa_ia_anime.gerar_capa; 1ª tentativa = pose de ROMANCE FAKE — beijo, quase-beijo, kabedon,
     abraço por trás, no colo, acordou na cama — POSES_ANIME.FAKE_ROMANCE; o placar de capas decide quais rendem);
  2) cola a capa como 1º quadro do vídeo (CAPA_1O_QUADRO_S, padrão 0,5 s; o áudio entra depois dela) — o original fica
     em video_sem_capa.mp4. postar.json ganha thumb/capa_pose/capa_no_inicio.

Só pasta pronta, de anime/manhwa, sem thumb, ainda não postada (sem posted_url/timeout_em), parada há >= 3 min (não
está sendo escrita) e sem a trava do postador. Até CAPAR_POR_RODADA (4) por passada, do mais novo pro mais velho.
Tarefa CaparShorts (15/15 min, oculta). Desligar: CAPAR_SHORTS=0. Log: logs\capar_shorts.log
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")
LOG = BIN.parent / "logs" / "capar_shorts.log"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe" if Path(r"D:\hipercool-materiais\bin\ffmpeg.exe").exists() else "ffmpeg"
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe") if FFMPEG.endswith(".exe") else "ffprobe"
SEM = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")
    if sys.stdout:
        try:
            print(linha, flush=True)
        except (OSError, ValueError):
            pass


def candidatos():
    out = []
    for d in SHORTS.iterdir():
        p = d / "postar.json"
        if not d.is_dir() or not p.exists() or not (d / "video.mp4").exists():
            continue
        try:
            j = json.loads(p.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        if (j.get("midia") not in ("anime", "manhwa") or j.get("thumb") or j.get("capa_no_inicio")
                or j.get("posted_url") or j.get("timeout_em") or not j.get("pronto") or j.get("tipo") != "short"):
            continue
        if (d / "_NO_DRIVE.txt").exists():  # 14/11: vídeo no Drive (estoque do mês) — capa só quando voltar
            continue
        if time.time() - (d / "video.mp4").stat().st_mtime < 180 or list(d.glob("*.lock")):
            continue
        out.append((d.stat().st_mtime, d, j))
    return [(d, j) for _, d, j in sorted(out, key=lambda t: -t[0])]


def _dims(v):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate", "-of", "json", str(v)], capture_output=True, text=True,
                       timeout=60, creationflags=SEM)
    s = json.loads(r.stdout)["streams"][0]
    return s["width"], s["height"], s.get("r_frame_rate", "30/1")


def capa_no_inicio(video, capa, seg):
    """Novo vídeo = [capa parada por `seg` s] + vídeo original (áudio do original atrasado `seg` s)."""
    w, h, fps = _dims(video)
    tmp = video.with_name("video_capa_tmp.mp4")
    filtro = (f"[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps},"
              f"format=yuv420p,trim=duration={seg}[c];[0:v]setsar=1,fps={fps},format=yuv420p[v];"
              f"[c][v]concat=n=2:v=1:a=0[vo];[0:a]adelay={int(seg * 1000)}:all=1[ao]")
    r = subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(video), "-loop", "1", "-t", str(seg), "-i", str(capa),
                        "-filter_complex", filtro, "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset",
                        "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(tmp)],
                       capture_output=True, text=True, timeout=900, creationflags=SEM)
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 100_000:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg falhou: {r.stderr[-200:]}")
    w2, h2, _ = _dims(tmp)
    if (w2, h2) != (w, h):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"medida mudou {w}x{h} -> {w2}x{h2}")
    orig = video.with_name("video_sem_capa.mp4")
    if not orig.exists():
        shutil.move(str(video), str(orig))
    shutil.move(str(tmp), str(video))


def capar(d, j):
    import capa_ia_anime
    capa = d / "capa_ia.jpg"
    texto = ""
    try:
        texto = json.loads((d / "metadata.json").read_text("utf-8")).get("thumb_texto") or ""
    except (OSError, ValueError):
        pass
    if not texto:  # sem thumb_texto: 3 primeiras palavras em MAIÚSCULA do título viram a frase da capa
        mai = [w for w in (j.get("titulo") or "").split() if w.isupper() and len(w) > 1]
        texto = " ".join(mai[:3]) + ("?" if mai else "")
    out = capa_ia_anime.gerar_capa(j.get("obra") or "sem-obra", j.get("cap") or 1, str(capa), texto=texto,
                                   cena=j.get("titulo", ""), protagonista="", formato="9:16")
    if not out:
        log(f"{d.name}: capa IA não saiu (todas as poses reprovadas) — segue com o quadro do vídeo")
        return False
    pose = ""
    try:
        pose = json.loads(Path(out).with_suffix(".capa.json").read_text("utf-8")).get("pose", "")
    except (OSError, ValueError):
        pass
    seg = float(os.environ.get("CAPA_1O_QUADRO_S", "0.5"))
    capa_no_inicio(d / "video.mp4", Path(out), seg)
    j = json.loads((d / "postar.json").read_text("utf-8"))  # relê: o postador pode ter mexido
    if j.get("posted_url") or j.get("timeout_em"):
        log(f"{d.name}: foi postado durante a capa — desfaço")
        shutil.move(str(d / "video_sem_capa.mp4"), str(d / "video.mp4"))
        return False
    j.update(thumb=Path(out).name, capa_pose=pose, capa_no_inicio=seg, capa_shorts_em=datetime.now().isoformat("T", "minutes"))
    (d / "postar.json").write_text(json.dumps(j, ensure_ascii=False, indent=2), "utf-8")
    log(f"{d.name}: capa IA no 1º quadro (pose {pose}, texto '{texto}')")
    return True


def main():
    if os.environ.get("CAPAR_SHORTS") == "0":
        return
    trava = LOG.with_suffix(".lock")
    if trava.exists() and time.time() - trava.stat().st_mtime < 3600:
        return
    trava.write_text(str(os.getpid()))
    try:
        feitos = 0
        for d, j in candidatos()[:int(os.environ.get("CAPAR_POR_RODADA", "4"))]:
            try:
                feitos += capar(d, j)
            except Exception as e:  # noqa: BLE001
                log(f"[!] {d.name}: {type(e).__name__}: {str(e)[:200]}")
        log(f"rodada: {feitos} Short(s) com capa IA")
    finally:
        trava.unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
