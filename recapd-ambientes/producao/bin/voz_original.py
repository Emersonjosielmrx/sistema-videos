"""voz_original.py — projeto João Lucas Virjão (dona 04/11/2026): recap que MANTÉM a narração original do vídeo (o
narrador parceiro autorizado, ex. @KkVirjao) e só melhora o vídeo ao máximo: legenda cinética MIX em tudo, efeitos
visuais nas palavras fortes (fx_visual), memes (interrupção com som + imagem em tela cheia), trilha por clima com
ducking sob a voz original, borrão só se a fonte tem legenda queimada, 1080p60.

Chamado pelo anime-pipeline.py quando o pedido traz longo_override {"voz_original": true} (o kaggle_trabalhador já
repassa isso em ANIME_LONGO_OVERRIDE). Gera <pasta do source>/final_anime_deitado.mp4, que o trabalhador sobe.
    python voz_original.py <source.mp4> "<titulo>"
Etapas com cache na pasta _vo (rodar de novo retoma). Projeto: D:\\projeto-joao-lucas-virjao\\LEIA_PRIMEIRO.md"""
import hashlib
import json
import logging
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
os.environ.setdefault("ANIME_ORIENT", "landscape")  # fx_assets decide W/H no import
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)
log = logging.info
W, H, FPS = 1920, 1080, 30


def _dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, timeout=60)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _altura(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True, timeout=60)
    try:
        return int(r.stdout.strip().split()[0])
    except (ValueError, IndexError):
        return 0


def _encoder():
    """NVENC na T4 do Kaggle; sem GPU = libx264 (esta passada é intermediária: a legenda reencoda depois)."""
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.2",
                            "-c:v", "h264_nvenc", "-f", "null", "-"], capture_output=True, timeout=60)
        if r.returncode == 0:
            return ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "19", "-b:v", "0"]
    except (OSError, subprocess.SubprocessError):
        pass
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]


# ---------------------------------------------------------------- 0. vídeo CRU: tira pausas/silêncios (corte seco)
def tirar_pausas(video, pasta, ruido_db=-35, minimo_s=0.6, folga_s=0.12):
    """Gravação crua do parceiro: silêncios > minimo_s saem (fica folga_s de cada lado). Um ffmpeg só, uma entrada
    (select/aselect) — sem o concat de N entradas que travou. Menos de 2 s pra tirar = devolve o original."""
    saida = pasta / "sem_pausas.mp4"
    if saida.exists() and saida.stat().st_size > 1_000_000:
        return saida
    import re as _re
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(video), "-vn", "-af",
                        f"silencedetect=noise={ruido_db}dB:d={minimo_s}", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=3600)
    ini = [float(x) for x in _re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    fim = [float(x) for x in _re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    total = _dur(video)
    silencios = [(a + folga_s, b - folga_s) for a, b in zip(ini, fim + [total] * (len(ini) - len(fim)))
                 if b - a - 2 * folga_s > 0.15]
    tirado = sum(b - a for a, b in silencios)
    if tirado < 2.0:
        log(f"[vo] cru: só {tirado:.1f}s de pausa — fica o original")
        return video
    manter, pos = [], 0.0
    for a, b in silencios:
        if a > pos:
            manter.append((pos, a))
        pos = b
    if pos < total:
        manter.append((pos, total))
    expr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in manter)
    (pasta / "pausas.txt").write_text(
        f"[0:v]select='{expr}',setpts=N/FRAME_RATE/TB[v];[0:a]aselect='{expr}',asetpts=N/SR/TB[a]", encoding="utf-8")
    t0 = time.time()
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-filter_complex_script",
                        str(pasta / "pausas.txt"), "-map", "[v]", "-map", "[a]", *_encoder(), "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", str(saida)], capture_output=True, text=True, timeout=4 * 3600)
    if r.returncode != 0 or not saida.exists():
        logging.warning(f"[vo] tirar pausas falhou ({r.stderr[-300:]}) — segue o original")
        return video
    log(f"[vo] cru: {len(silencios)} pausas tiradas ({tirado:.0f}s), {total:.0f}s -> {_dur(saida):.0f}s, "
        f"em {time.time() - t0:.0f}s")
    return saida


# ---------------------------------------------------------------- 1. transcrição com tempo de cada palavra
def transcrever(video, pasta):
    cache = pasta / "frases.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    from fx_subtitles import _strip_lead_punct
    wav = pasta / "_whisper.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                   check=True, timeout=3600)
    import wave
    import numpy as np
    with wave.open(str(wav), "rb") as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    from faster_whisper import WhisperModel
    raiz = str(pasta.resolve().parent.parent / "_modelos_whisper")
    t0, segs, modelo = time.time(), None, None
    try:
        import torch
        gpu = torch.cuda.is_available()
    except Exception:  # noqa: BLE001
        gpu = False
    if gpu:
        try:
            from anime_preparo_longo import _carregar_cuda_libs
            _carregar_cuda_libs()
            # 04/11: 'small' errava muito a gíria do narrador (teste: "estiorrar o piá") e a legenda MIX mostra cada
            # palavra grande — na T4 vai o large-v3 (fp16 cabe nos 15 GB; ~5 min pra 30 min de áudio)
            modelo = os.environ.get("VOZ_ORIGINAL_WHISPER") or "large-v3"
            m = WhisperModel(modelo, device="cuda", compute_type="float16", download_root=raiz)
            segs = list(m.transcribe(audio, language="pt", word_timestamps=True, vad_filter=True)[0])
            modelo += " (GPU)"
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[vo] Whisper na GPU falhou ({type(e).__name__}: {str(e)[:150]}) — CPU")
            segs = None
    if segs is None:
        modelo = "small"
        m = WhisperModel(modelo, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2,
                         download_root=raiz)
        segs = list(m.transcribe(audio, language="pt", word_timestamps=True, vad_filter=True)[0])
    wav.unlink(missing_ok=True)
    frases = []
    for s in segs:
        ps = []
        for w in (s.words or []):
            limpa = _strip_lead_punct((w.word or "").strip())
            if limpa and " " not in limpa:  # mesma limpeza do burn_subtitles_ass: a contagem casa = tempo REAL
                ps.append([limpa, round(float(w.start), 3), round(float(max(w.end, w.start + 0.05)), 3)])
        if ps:
            frases.append({"ini": ps[0][1], "fim": ps[-1][2], "texto": " ".join(p[0] for p in ps), "palavras": ps})
    log(f"[vo] Whisper {modelo}: {len(frases)} frases, {sum(len(f['palavras']) for f in frases)} palavras, "
        f"em {time.time() - t0:.0f}s")
    cache.write_text(json.dumps(frases, ensure_ascii=False), encoding="utf-8")
    return frases


# ---------------------------------------------------------------- 1b. memes/trilhas do PARCEIRO (prioridade)
def _rclone():
    """[binário, --config, arquivo] — no Kaggle o rclone do trabalhador (BASE/rclone + rclone.conf do input)."""
    for p in [Path(os.environ["TRAB_BASE"]) / "rclone"] if os.environ.get("TRAB_BASE") else []:
        if p.exists():
            break
    else:
        p = next((q / "rclone" for q in Path(__file__).resolve().parents if (q / "rclone").is_file()), None)
    if p is None:
        p = shutil.which("rclone") or (r"D:\tools\rclone.exe" if Path(r"D:\tools\rclone.exe").exists() else None)
    if not p:
        return None
    conf = os.environ.get("RCLONE_CONF")
    if not conf and Path("/kaggle/input").exists():
        conf = str(next(Path("/kaggle/input").rglob("rclone.conf"), "") or "")
    return [str(p)] + (["--config", conf] if conf else [])


def baixar_do_parceiro(remoto, destino):
    """Pasta do Drive do parceiro (memes ou trilhas que ELE quer priorizar) -> lista de arquivos locais."""
    if not remoto:
        return []
    rc = _rclone()
    if not rc:
        logging.warning("[vo] sem rclone — memes/trilhas do parceiro ficam de fora")
        return []
    destino.mkdir(parents=True, exist_ok=True)
    subprocess.run(rc + ["copy", remoto, str(destino), "--max-size", "300M"], capture_output=True, timeout=1800)
    return sorted(p for p in destino.rglob("*") if p.is_file())


# ---------------------------------------------------------------- 2. memes (interrupção com som + imagem)
def _sfx_impacto(rnd):
    pastas = [AQUI.parent / "workspace" / "assets" / d for d in ("sfx", "sfx_memes", "sfx_extras")]
    arqs = [p for d in pastas if d.is_dir() for p in d.rglob("*")
            if p.suffix.lower() in (".mp3", ".wav", ".ogg") and any(
                k in p.name.lower() for k in ("whoosh", "swoosh", "impact", "boom", "hit", "punch", "vine"))]
    return rnd.choice(arqs) if arqs else None


VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi")
IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp")


def preparar_memes(frases, pasta, semente, meus=()):
    """[(corte_s, arquivo, duração)] — corte sempre ENTRE duas frases (nunca no meio de uma palavra).
    meus = memes do parceiro (pasta 4 do Drive dele): entram PRIMEIRO, um em cada vaga, sem repetir; acabaram = os
    nossos. Vídeo dele = interrupção com o som dele (até 12 s); imagem = tela cheia rápida com som de impacto."""
    cache = pasta / "memes.json"
    if cache.exists():
        return [tuple(x) for x in json.loads(cache.read_text(encoding="utf-8"))]
    if os.environ.get("VOZ_ORIGINAL_MEMES", "1") == "0":
        return []
    import memes_visuais as mv
    rnd = random.Random(semente)
    textos = [f["texto"] for f in frases]
    inter = mv.escolher_interrupcoes(textos, inicio=4, cada=10, rnd=rnd)
    imgs = mv.escolher_imagens(textos, ocupados=[k for k, _ in inter], inicio=4, cada=8, rnd=rnd)
    fila_meus = [p for p in meus if p.suffix.lower() in VIDEO_EXT + IMG_EXT]
    rnd.shuffle(fila_meus)
    if len(fila_meus) > len(inter) + len(imgs):  # ele mandou muitos: abre mais vagas (1 a cada ~6 frases)
        extra = mv.escolher_imagens(textos, ocupados=[k for k, _ in inter] + [k for k, _ in imgs], inicio=4, cada=6,
                                    rnd=rnd)
        imgs += extra[:len(fila_meus) - len(inter) - len(imgs)]
    out, n_meus = [], 0
    for k, meme, tipo in sorted([(k, m, "clip") for k, m in inter] + [(k, m, "img") for k, m in imgs],
                                key=lambda x: x[0]):
        if k + 1 >= len(frases):
            continue
        corte = round((frases[k]["fim"] + frases[k + 1]["ini"]) / 2, 3)
        arq = pasta / f"meme_{k:04d}.mp4"
        ok = False
        while fila_meus and not ok:  # o do parceiro primeiro
            p = fila_meus.pop(0)
            m = {"file": str(p), "duration": _dur(p)}
            ok = (mv.montar_clip(m, arq, W, H, fps=FPS) if p.suffix.lower() in VIDEO_EXT
                  else mv.montar_imagem(m, arq, W, H, sfx=_sfx_impacto(rnd), fps=FPS))
            n_meus += bool(ok)
        if not ok:
            ok = (mv.montar_clip(meme, arq, W, H, fps=FPS) if tipo == "clip"
                  else mv.montar_imagem(meme, arq, W, H, sfx=_sfx_impacto(rnd), fps=FPS))
        if ok:
            out.append((corte, str(arq), round(_dur(arq), 3)))
    log(f"[vo] memes: {len(inter)} interrupções + {len(imgs)} imagens, {len(out)} montados ({n_meus} do parceiro)")
    cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


# ---------------------------------------------------------------- 3. base: original + memes + cor + borrão da legenda
def montar_base(video, memes, pasta):
    base = pasta / "base.mp4"
    if base.exists() and base.stat().st_size > 1_000_000:
        return base
    faixa = None
    try:
        import anime_legenda_fonte
        det = anime_legenda_fonte.detectar(video)
        if det.get("tem") and det.get("faixa"):
            y0, y1 = det["faixa"]
            faixa = (max(0.0, y0 - 0.012), min(1.0, y1 + 0.012))
            log(f"[vo] fonte com legenda queimada em {faixa} — borrão só nessa faixa")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[vo] detecção de legenda falhou ({type(e).__name__}) — sem borrão")
    # 04/11: um ffmpeg só com N entradas + concat TRAVOU (0% de CPU, teste no PC1). Agora cada trecho é codificado
    # sozinho com os MESMOS parâmetros (vídeo idêntico + PCM em .mkv) e o concat demuxer junta copiando o vídeo; o
    # áudio vira AAC uma vez só no fim (sem estalo nas emendas).
    total = _dur(video)
    cortes = [0.0] + [c for c, _a, _d in memes] + [total]
    enc = _encoder()
    vf_orig = (f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
               f"setsar=1,eq=saturation=1.10:contrast=1.03,unsharp=5:5:0.4")
    if faixa:
        y0, y1 = faixa
        vf_orig = (f"{vf_orig},split[o][c];[c]crop=iw:ih*{y1 - y0:.4f}:0:ih*{y0:.4f},boxblur=22:3[b];"
                   f"[o][b]overlay=0:H*{y0:.4f}")
    vf_meme = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    comum = ["-pix_fmt", "yuv420p", "-video_track_timescale", "90000", "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2"]

    def _cod(entrada, vf, saida, ini=None, fim_=None):
        nonlocal enc
        if saida.exists() and saida.stat().st_size > 1000:
            return
        pre = (["-ss", f"{ini:.3f}", "-to", f"{fim_:.3f}"] if ini is not None else [])
        for _ in range(2):
            cmd = ["ffmpeg", "-y", "-v", "error", *pre, "-i", str(entrada), "-filter_complex", f"[0:v]{vf}[v]",
                   "-map", "[v]", "-map", "0:a:0", *enc, "-g", "60", *comum, str(saida)]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=3 * 3600)
            if r.returncode == 0 and saida.exists():
                return
            if "nvenc" in enc[1]:
                logging.warning(f"[vo] NVENC falhou ({r.stderr[-200:]}) — libx264 daqui pra frente")
                enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]
                continue
            break
        raise RuntimeError(f"trecho {saida.name} falhou: {r.stderr[-600:]}")

    t0 = time.time()
    lista = []
    for i in range(len(cortes) - 1):
        pedaco = pasta / f"p{i:03d}_orig.mkv"
        _cod(video, vf_orig, pedaco, cortes[i], cortes[i + 1])
        lista.append(pedaco)
        if i < len(memes):
            pm = pasta / f"p{i:03d}_meme.mkv"
            _cod(memes[i][1], vf_meme, pm)
            lista.append(pm)
    txt = pasta / "lista.txt"
    txt.write_text("".join(f"file '{p.as_posix()}'\n" for p in lista), encoding="utf-8")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(txt), "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(base)],
                       capture_output=True, text=True, timeout=3600)
    if r.returncode != 0 or not base.exists():
        raise RuntimeError(f"base (concat) falhou: {r.stderr[-800:]}")
    # mapa (início no original -> início na base) pela duração REAL de cada trecho (o fps arredonda uns ms por emenda;
    # somado em 40 memes desalinharia a legenda)
    mapa, pos = [], 0.0
    for p in lista:
        if p.name.endswith("_orig.mkv"):
            mapa.append([cortes[int(p.name[1:4])], pos])
        pos += _dur(p)
    (pasta / "mapa.json").write_text(json.dumps(mapa), encoding="utf-8")
    for p in lista:
        p.unlink(missing_ok=True)
    log(f"[vo] base ({len(lista)} trechos, {len(memes)} memes) em {time.time() - t0:.0f}s: {_dur(base):.0f}s "
        f"(original {total:.0f}s + memes {sum(d for _c, _a, d in memes):.0f}s)")
    return base


# ---------------------------------------------------------------- principal
def main():
    video = Path(sys.argv[1]).resolve()
    titulo = sys.argv[2] if len(sys.argv) > 2 else video.parent.name
    pasta = video.parent / "_vo"
    pasta.mkdir(exist_ok=True)
    final = video.parent / "final_anime_deitado.mp4"
    t0 = time.time()
    log(f"[vo] VOZ ORIGINAL: {titulo} ({_dur(video):.0f}s)")

    try:
        ovr = json.loads(os.environ.get("ANIME_LONGO_OVERRIDE") or "{}")
    except ValueError:
        ovr = {}
    ovr = ovr if isinstance(ovr, dict) else {}
    if ovr.get("cru"):  # gravação crua: corte seco das pausas antes de tudo
        video = tirar_pausas(video, pasta)
    frases = transcrever(video, pasta)
    if len(frases) < 5:
        log("[vo] transcrição quase vazia — vídeo não sai")
        return 1
    semente = int(hashlib.md5(titulo.encode("utf-8")).hexdigest()[:8], 16)
    meus_memes = baixar_do_parceiro(ovr.get("memes_drive"), pasta / "_memes_parceiro")
    minhas_trilhas = [p for p in baixar_do_parceiro(ovr.get("trilhas_drive"), pasta / "_trilhas_parceiro")
                      if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac")]
    if meus_memes or minhas_trilhas:
        log(f"[vo] do parceiro: {len(meus_memes)} memes, {len(minhas_trilhas)} trilhas (prioridade)")
    memes = preparar_memes(frases, pasta, semente, meus_memes)
    base = montar_base(video, memes, pasta)

    try:
        mapa = json.loads((pasta / "mapa.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        mapa = None

    def desloca(t):  # tempo no original -> tempo na base (memes inseridos antes de t empurram)
        if mapa:
            ini_o, ini_b = max((m for m in mapa if m[0] <= t + 1e-6), key=lambda m: m[0], default=mapa[0])
            return ini_b + (t - ini_o)
        return t + sum(d for c, _a, d in memes if c <= t)

    entries = [(f["texto"], f["fim"] - f["ini"]) for f in frases]
    offsets = [desloca(f["ini"]) for f in frases]
    word_times = [[[p[1] - f["ini"], p[2] - f["ini"], p[0]] for p in f["palavras"]] for f in frases]

    # 1) trilha na BASE (só áudio, vídeo copiado) — assim os cortes pra Shorts já saem com música
    com_trilha = pasta / "base_trilha.mp4"
    if not (com_trilha.exists() and com_trilha.stat().st_size > 1_000_000):
        trilhas = AQUI.parent / "workspace" / "assets" / "trilhas"
        import effects_engine
        if minhas_trilhas:  # as do parceiro, em sequência (embaralhadas), niveladas e abaixando sob a voz
            try:
                random.Random(semente).shuffle(minhas_trilhas)
                lista_t = pasta / "trilhas.txt"
                lista_t.write_text("".join(f"file '{p.as_posix()}'\n" for p in minhas_trilhas), encoding="utf-8")
                junta = pasta / "trilha_parceiro.m4a"
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista_t),
                                "-vn", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", str(junta)],
                               check=True, timeout=1800)
                effects_engine.add_background_music(base, junta, com_trilha, music_volume=0.10, duck=True)
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[vo] trilha do parceiro falhou ({type(e).__name__}: {e}) — vai a nossa")
                com_trilha.unlink(missing_ok=True)
        if not com_trilha.exists() and (trilhas / "moods.json").exists():
            effects_engine.add_dynamic_music(base, [{"text": f["texto"]} for f in frases], com_trilha, trilhas,
                                             music_volume=0.10, no_copyright=True)
    if com_trilha.exists() and com_trilha.stat().st_size > 1_000_000:
        base.unlink(missing_ok=True)
        base = com_trilha
    else:
        logging.warning("[vo] trilha não entrou — segue sem trilha")

    # 2) cortes pra Shorts (pastas do parceiro): os melhores trechos viram 9:16 com legenda MIX própria em pé
    # (melhores_cortes, o mesmo dos longos), da base SEM legenda. O trabalhador sobe cortes_longo/.
    if ovr.get("cortes") or ovr.get("so_cortes"):
        try:
            import melhores_cortes
            _cfg0 = melhores_cortes._cfg
            melhores_cortes._cfg = lambda: {**_cfg0(), "ligado": True, "max": int(ovr.get("cortes_max") or 8)}
            t2 = time.time()
            feitos = melhores_cortes.gerar(str(base), [f["texto"] for f in frases], offsets, final.parent,
                                           word_times=word_times)
            log(f"[vo] cortes pra Shorts: {len(feitos or [])} em {time.time() - t2:.0f}s")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[vo] cortes falharam ({type(e).__name__}: {e}) — sai só o vídeo editado")

    # 3) legenda MIX no vídeo INTEIRO (regra da dona 01/11) + efeitos + 1080p60. "só cortes" = pula (mais rápido)
    if ovr.get("so_cortes"):
        shutil.move(str(base), str(final))
    else:
        os.environ["ANIME_LEGENDA_CRIATIVA_S"] = os.environ.get("VOZ_ORIGINAL_MIX_ATE_S") or "100000"
        os.environ.setdefault("ANIME_PRESET_LEGENDA", "veryfast")
        import fx_subtitles
        t1 = time.time()
        if not fx_subtitles.burn_subtitles_ass(str(base), entries, str(final), word_times=word_times,
                                               offsets=offsets):
            log("[vo] legenda falhou — vídeo não sai")
            return 1
        log(f"[vo] legenda MIX + efeitos em {time.time() - t1:.0f}s")
        base.unlink(missing_ok=True)

    alt = _altura(final)
    if alt < 1080:
        log(f"[vo] ERRO: saiu {alt}p (< 1080p)")
        return 1
    log(f"[vo] PRONTO {final.name}: {_dur(final):.0f}s, {alt}p, em {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
