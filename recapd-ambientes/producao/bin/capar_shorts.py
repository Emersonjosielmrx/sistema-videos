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
QUADRO_REAL = ("dorama", "filme_sem_voz", "fatos")  # capa com quadros do próprio vídeo (D:/fabrica-poses)


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
        # 15/11 dona ("podemos testar em produção"): dorama/filme/fatos ganham capa de QUADRO REAL (sem IA de rosto)
        midias = ("anime", "manhwa") + (QUADRO_REAL if os.environ.get("CAPA_QUADRO_REAL", "1") != "0" else ())
        if (j.get("midia") not in midias or j.get("thumb") or j.get("capa_no_inicio")
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
    cmd = [FFMPEG, "-y", "-v", "error", "-i", str(video), "-loop", "1", "-t", str(seg), "-i", str(capa),
           "-filter_complex", filtro, "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset",
           "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(tmp)]
    # 15/11 dona ("PC1 livre pro VS Code; passar a conversão pros outros"): o re-encode vai pra um celular livre
    # (celulares.rodar_ffmpeg); celular fora/ocupado = roda aqui como antes. CAPAR_NO_CELULAR=0 desliga.
    feito = False
    if os.environ.get("CAPAR_NO_CELULAR", "1") != "0":
        try:
            sys.path.insert(0, r"D:\video-fila")
            import celulares
            feito = bool(celulares.rodar_ffmpeg(cmd, timeout=900, rotulo=f"capa {video.parent.name[:30]}"))
        except Exception:  # noqa: BLE001
            feito = False
    if feito:
        r = subprocess.CompletedProcess(cmd, 0, "", "")
    else:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900, creationflags=SEM)
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


def capar_quadro_real(d, j):
    """15/11 (teste em produção liberado pela dona): capa = quadros reais do próprio Short em 1 de 4 molduras (tweet,
    split, reddit, zap), sorteada. Nada de rosto por IA (atores reais). Original em video_sem_capa.mp4."""
    import random
    if r"D:/fabrica-poses" not in sys.path:
        sys.path.append(r"D:/fabrica-poses")
    import capa_quadro_real as cq
    from PIL import Image
    video = d / "video_sem_capa.mp4" if (d / "video_sem_capa.mp4").exists() else d / "video.mp4"
    qs = cq.escolher_quadros(video, d / "_capa_quadros", n=2)
    if not qs:
        log(f"{d.name}: sem quadro bom pra capa")
        return False
    q1, q2 = (cq._cima(Image.open(q).convert("RGB")) for q in (qs[0], qs[-1]))
    txt = cq.gancho(j.get("titulo", ""), d)
    estilo = random.choice(["tweet", "split", "reddit", "zap"])
    capa = d / "capa_quadro.jpg"
    if estilo == "tweet":
        cq.tweet(q1, txt, capa, cq.TIPO.get(j.get("midia"), ("fofoca", "@fofoca")))
    elif estilo == "split":
        cq.split(q1, q2, txt, capa)
    else:
        getattr(cq, estilo)(q1, txt, capa)
    seg = float(os.environ.get("CAPA_1O_QUADRO_S", "0.5"))
    capa_no_inicio(d / "video.mp4", capa, seg)
    j = json.loads((d / "postar.json").read_text("utf-8"))
    if j.get("posted_url") or j.get("timeout_em"):
        shutil.move(str(d / "video_sem_capa.mp4"), str(d / "video.mp4"))
        return False
    j.update(thumb=capa.name, capa_pose=f"quadro_{estilo}", capa_no_inicio=seg,
             capa_shorts_em=datetime.now().isoformat("T", "minutes"))
    (d / "postar.json").write_text(json.dumps(j, ensure_ascii=False, indent=2), "utf-8")
    log(f"{d.name}: capa de QUADRO REAL ({estilo}, '{txt}')")
    return True


def capar(d, j):
    if j.get("midia") in QUADRO_REAL:
        return capar_quadro_real(d, j)
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
    out = None
    # 15/11 dona (aprovou os de Spy x Family): anime com casal ADULTO conhecido -> 1º a capa "print do próprio
    # episódio", feita com quadros reais deste Short (capa_print_anime). Não saiu = capa antiga. CAPA_PRINT_ANIME=0 desliga.
    try:
        import capa_print_anime
        out = capa_print_anime.gerar(d, j, str(capa))
    except Exception as e:  # noqa: BLE001
        log(f"{d.name}: capa print do anime falhou ({type(e).__name__}: {str(e)[:120]}) — capa antiga")
    if not out:
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


KIT3D = Path(r"D:\hipercool-materiais\historias-em-frames")


def capar_3d():
    """16/11 dona ("aplique no 3D tudo que os outros já usam"): Shorts 3D (fichas 3d-*) já vêm com capa.png do próprio
    kit — vai como 1º quadro (CAPA_1O_QUADRO_S), igual aos de parceiro, antes de postar. CAPAR_3D=0 desliga."""
    if os.environ.get("CAPAR_3D", "1") == "0" or not KIT3D.is_dir():
        return 0
    n = 0
    for pj in KIT3D.glob("3d-*/postar.json"):
        d = pj.parent
        try:
            j = json.loads(pj.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        video = d / (j.get("arquivo") or "video.mp4")
        capa = next((d / c for c in ("capa.png", "capa.jpg") if (d / c).exists()), None)
        if (not video.exists() or not capa or j.get("capa_no_inicio") or j.get("posted_url")
                or not j.get("pronto") or time.time() - video.stat().st_mtime < 180):
            continue
        try:
            seg = float(os.environ.get("CAPA_1O_QUADRO_S", "0.5"))
            # capa_no_inicio trabalha com "video.mp4" + "video_sem_capa.mp4": usa o nome real do 3D por cópia
            tmp = d / "video.mp4"
            if tmp.exists() and tmp != video:
                continue
            # 16/11: a aprovação da rede é por tamanho do arquivo — a capa muda o tamanho e o Short caía em
            # "esperando aprovação" (geladeira aprovada pela dona ficou parada). Guarda o status e regrava depois.
            status_antes = None
            try:
                if r"D:\postador-de-videos\bin" not in sys.path:
                    sys.path.append(r"D:\postador-de-videos\bin")
                import politica
                status_antes = politica.status_aprovacao(video)
            except Exception:  # noqa: BLE001
                politica = None
            video.rename(tmp)
            try:
                capa_no_inicio(tmp, capa, seg)
            finally:
                tmp.rename(video)
            if politica and status_antes == "aprovado" and os.environ.get("CAPAR_3D_MANTEM_APROV", "1") != "0":
                politica.marcar_aprovacao(video, "aprovado", "kit3d: aprovado antes da capa no 1º quadro (capar_3d)")
            j = json.loads(pj.read_text("utf-8"))
            if j.get("posted_url"):
                log(f"{d.name}: postado durante a capa — desfaço")
                sem = d / "video_sem_capa.mp4"
                if sem.exists():
                    shutil.move(str(sem), str(video))
                continue
            j.update(capa_no_inicio=seg, thumb=capa.name, capa_shorts_em=datetime.now().isoformat("T", "minutes"))
            pj.write_text(json.dumps(j, ensure_ascii=False, indent=2), "utf-8")
            log(f"{d.name}: capa do kit 3D no 1º quadro")
            n += 1
        except Exception as e:  # noqa: BLE001
            log(f"[!] {d.name} (3D): {type(e).__name__}: {str(e)[:200]}")
    return n


def main():
    if os.environ.get("CAPAR_SHORTS") == "0":
        return
    trava = LOG.with_suffix(".lock")
    if trava.exists() and time.time() - trava.stat().st_mtime < 3600:
        return
    trava.write_text(str(os.getpid()))
    try:
        feitos = 0
        cand = candidatos()
        # 15/11: teste do quadro real limitado a CAPA_QUADRO_REAL_POR_RODADA (2) pra não tomar a vez dos de anime
        qr = [c for c in cand if c[1].get("midia") in QUADRO_REAL][:int(os.environ.get("CAPA_QUADRO_REAL_POR_RODADA", "2"))]
        ia = [c for c in cand if c[1].get("midia") not in QUADRO_REAL][:int(os.environ.get("CAPAR_POR_RODADA", "4"))]
        for d, j in ia + qr:
            try:
                feitos += capar(d, j)
            except Exception as e:  # noqa: BLE001
                log(f"[!] {d.name}: {type(e).__name__}: {str(e)[:200]}")
        feitos += capar_3d()
        log(f"rodada: {feitos} Short(s) com capa IA")
    finally:
        trava.unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
