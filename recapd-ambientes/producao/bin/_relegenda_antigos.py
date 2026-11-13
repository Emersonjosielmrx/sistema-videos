r"""_relegenda_antigos.py — re-legenda os vídeos que saíram SEM legenda (catch-up).

Roda NO PC2. Varre os workdirs (%TEMP%\anime_worker_* e C:\recapd-e-animes\saida\*)
que ainda tenham _semlegenda_*.mp4 + roteiro + audio_cache e, SEM re-render:
  1. borra a faixa da legenda QUEIMADA da fonte no _semlegenda (detecção por visão
     Gemini; fallback = faixa fixa no rodapé);
  2. reconstrói entries + word_times (timing real) dos sidecars .words.json;
  3. queima a nova legenda PT via libass (1 passada);
  4. salva como final_anime_deitado.mp4 no próprio workdir.

Se o temp de algum já foi limpo, registra e segue (a dona autorizou esse fallback).

Uso:  python _relegenda_antigos.py [dir1 dir2 ...]
Sem args, varre os locais padrão.
"""
import os
import sys
import glob
import shutil
import logging
import tempfile
import subprocess
from pathlib import Path

os.environ.setdefault("ANIME_ORIENT", "landscape")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("ANIME_SUB_ENGINE", "ass")  # libass: 1 passada
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))


def _find_workdirs(argv):
    if argv:
        return [Path(a) for a in argv]
    cands = []
    tmp = Path(tempfile.gettempdir())
    cands += glob.glob(str(tmp / "anime_worker_*"))
    cands += glob.glob(r"C:\recapd-e-animes\saida\*")
    cands += glob.glob(str(BIN.parent / "workspace" / "anime" / "*"))
    return [Path(c) for c in cands if Path(c).is_dir()]


def _pick_semlegenda(wd):
    for name in ("_semlegenda_landscape.mp4", "_semlegenda_music_landscape.mp4"):
        p = wd / name
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def _pick_roteiro(wd):
    for name in ("roteiro.txt", "roteiro_v2.txt", "script.txt"):
        p = wd / name
        if p.exists():
            return p
    return None


def _blur_band(video_in, video_out, y_frac, h_frac):
    """Borra SÓ a faixa [y_frac, y_frac+h_frac] no vídeo inteiro (1 passada).
    Mesmo idioma crop→boxblur→eq→overlay usado por clipe em fx_clips."""
    vf = (
        f"[0:v]split=2[base][band];"
        f"[band]crop=iw:ih*{h_frac}:0:ih*{y_frac},gblur=sigma=20,"
        f"eq=brightness=0.10:saturation=0.55[bl];"
        f"[base][bl]overlay=0:H*{y_frac}[vout]"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(video_in),
        "-filter_complex", vf, "-map", "[vout]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "copy", "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=7200)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.error(f"[relegenda] blur falhou: {e}")
        return False
    return Path(video_out).exists() and Path(video_out).stat().st_size > 0


def _reburn_one(wd):
    sem = _pick_semlegenda(wd)
    roteiro = _pick_roteiro(wd)
    audio = wd / "audio_cache"
    clips = wd / "clipes_landscape"
    if not sem or not roteiro or not audio.is_dir():
        logging.warning(f"[relegenda] {wd.name}: faltando peças "
                        f"(sem={bool(sem)} roteiro={bool(roteiro)} audio={audio.is_dir()}) — pulando")
        return False

    from anime_captions import burn_captions
    from anime_probe import audio_duration
    import json as _json

    with open(roteiro, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    # Reconstrói entries + word_times como build_segments: só frases com wav válido.
    entries, word_times = [], []
    for i, line in enumerate(lines):
        wav = audio / f"audio_{i}.wav"
        clip = clips / f"clip_{i}.mp4"
        # aceita mesmo sem o clip (o vídeo concatenado já existe); exige o wav.
        if not wav.exists():
            continue
        dur = audio_duration(str(wav))
        if dur <= 0:
            continue
        wt = None
        try:
            wj = Path(str(wav) + ".words.json")
            if wj.exists():
                data = _json.loads(wj.read_text(encoding="utf-8"))
                if isinstance(data, list) and data:
                    wt = data
        except Exception:
            pass
        entries.append((line, dur))
        word_times.append(wt)

    if not entries:
        logging.warning(f"[relegenda] {wd.name}: 0 entries reconstruídas — pulando")
        return False
    logging.info(f"[relegenda] {wd.name}: {len(entries)} entries "
                 f"({sum(1 for w in word_times if w)} com timing real)")

    # 1) Blur da legenda antiga no _semlegenda (detecção por visão, fallback fixo).
    blurred = wd / "_semlegenda_blurred.mp4"
    band = None
    if os.environ.get("ANIME_HARDSUB_DETECT", "1").strip() != "0":
        try:
            from anime_hardsub_detect import detect_hardsub_band
            band = detect_hardsub_band(str(sem))
        except Exception as e:
            logging.warning(f"[relegenda] detecção falhou: {e}")
    if not band:
        band = (0.84, 0.16)  # fallback: faixa fixa no rodapé
        logging.info(f"[relegenda] {wd.name}: usando faixa fixa {band}")
    base_video = sem
    if _blur_band(sem, blurred, band[0], band[1]):
        base_video = blurred
    else:
        logging.warning(f"[relegenda] {wd.name}: blur falhou — legenda por cima do original")

    # 2) Legenda nova via libass (offsets=None; drift já assado no _semlegenda).
    final = wd / "final_anime_deitado.mp4"
    ok = burn_captions(str(base_video), entries, str(final), orient="landscape",
                       word_times=word_times, offsets=None)
    try:
        if blurred.exists():
            blurred.unlink()
    except Exception:
        pass
    if not ok:
        logging.error(f"[relegenda] {wd.name}: burn_captions falhou")
        return False
    logging.info(f"[relegenda] {wd.name}: PRONTO -> {final}")
    return True


SAIDA = Path(r"C:\recapd-e-animes\saida")


def _archive_and_cleanup(wd):
    """Copia o final_anime_deitado.mp4 pra saida\\orphan_<id>_<data>\\ (pasta ESTÁVEL,
    fora do %TEMP%) e, só se a cópia bateu byte-a-byte, APAGA o workdir temp inteiro.
    Assim nada fica preso no temp depois de transferido (regra da dona)."""
    import datetime
    src = wd / "final_anime_deitado.mp4"
    if not src.exists() or src.stat().st_size == 0:
        logging.warning(f"[relegenda] {wd.name}: sem final pra arquivar")
        return False
    wid = wd.name.replace("anime_worker_", "")
    # reusa a pasta orphan_<id>_* existente, senão cria com a data de hoje
    existing = list(SAIDA.glob(f"orphan_{wid}_*"))
    if existing:
        dst_dir = existing[0]
    else:
        stamp = datetime.datetime.now().strftime("%Y%m%d")
        dst_dir = SAIDA / f"orphan_{wid}_{stamp}"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / "final_anime_deitado.mp4"
    try:
        shutil.copy2(str(src), str(dst))
    except Exception as e:
        logging.error(f"[relegenda] {wd.name}: falha copiando pra saida: {e}")
        return False
    if not dst.exists() or dst.stat().st_size != src.stat().st_size:
        logging.error(f"[relegenda] {wd.name}: tamanho divergente pós-cópia — temp mantido")
        return False
    logging.info(f"[relegenda] {wd.name}: arquivado -> {dst} "
                 f"({dst.stat().st_size // (1024*1024)}MB)")
    try:
        shutil.rmtree(str(wd), ignore_errors=True)
        logging.info(f"[relegenda] {wd.name}: temp APAGADO (transferido)")
    except Exception as e:
        logging.warning(f"[relegenda] {wd.name}: falha apagando temp: {e}")
    return True


def main():
    wds = _find_workdirs(sys.argv[1:])
    if not wds:
        logging.info("[relegenda] nenhum workdir candidato encontrado")
        return
    # ANIME_RELEGENDA_ARCHIVE=0 desliga o arquivamento+limpeza automáticos.
    do_archive = os.environ.get("ANIME_RELEGENDA_ARCHIVE", "1").strip() != "0"
    ok = 0
    for wd in wds:
        try:
            if _reburn_one(wd):
                ok += 1
                if do_archive:
                    _archive_and_cleanup(wd)
        except Exception as e:
            logging.error(f"[relegenda] {wd}: erro {e}")
    logging.info(f"[relegenda] concluído: {ok}/{len(wds)} re-legendados")


if __name__ == "__main__":
    main()
