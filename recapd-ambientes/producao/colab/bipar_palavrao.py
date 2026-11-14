r"""bipar_palavrao.py — 13/11: longo reprovado por palavrão (postar_longos._tem_palavrao) é salvo SEM re-render.
Medieval Age parte 4 ("fodas") e 6 ("merdas") estavam reprovadas e a série ficou com buraco.

1. baixa o video.mp4 do Drive (1_youtube_pendente/<pasta>) pra D:\tmp\bipar\
2. acha a frase do pipeline.log (só o trecho com o palavrão) no áudio com faster_whisper (só no áudio, rápido)
3. troca a palavra por bipe (ffmpeg: volume 0 + seno 1 kHz na janela da palavra), vídeo copiado sem re-encode
4. confere com whisper de novo que a palavra sumiu, sobe o vídeo no lugar (o original fica como video_com_palavrao.mp4)
5. tira a ficha de "reprovados" (longos_postados.json) e grava SEM_PALAVRAO.txt na ficha (postar_longos não reprova de
   novo: _tem_palavrao olha esse arquivo)

    python bipar_palavrao.py <nome da ficha em na_nuvem>
BIPAR_SO_TESTE=1 = não sobe nem mexe no estado.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
RCLONE = r"D:\tools\rclone.exe"
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
TMP = Path(r"D:\tmp\bipar")
SEM_JANELA = 0x08000000
from postar_longos import _PALAVRAO  # noqa: E402


def log(m):
    print(m, flush=True)


def _sh(cmd, **k):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          creationflags=SEM_JANELA, **k)


def _achar(wav, inicio_s=0, dur_s=None):
    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(str(wav), language="pt", word_timestamps=True, vad_filter=True)
    achados = []
    for s in segs:
        for w in s.words or []:
            if _PALAVRAO.search(w.word.strip(" .,!?;:")):
                achados.append((round(w.start + inicio_s, 2), round(w.end + inicio_s, 2), w.word.strip()))
    return achados


def _janelas(ficha):
    """13/11: whisper nas 3 h inteiras levou > 1 h em CPU sem terminar. Acha no pipeline.log a fala com o palavrão
    (audio_NNN), soma as durações dos clipes anteriores (build_clip_from_video) = tempo aproximado no vídeo, e devolve
    janelas de ±BIPAR_JANELA_S (padrão 240 s) em volta. Sem estimativa = None (vídeo inteiro)."""
    txt = (ficha / "pipeline.log").read_text(encoding="utf-8", errors="replace").splitlines()
    dur = {}
    # (render paralelo: os clipes não vêm em ordem; o dict guarda o último registro de cada clipe)
    for l in txt:
        m = re.search(r"\[build_clip_from_video\] clipe (\d+) \(landscape\) Start=[\d.]+s Dur=([\d.]+)s", l)
        if m:
            dur[int(m.group(1))] = float(m.group(2))
    alvos = []
    for i, l in enumerate(txt):
        if "text='" in l and _PALAVRAO.search(l):
            for l2 in txt[i + 1:i + 6]:
                m = re.search(r"wrote audio_(\d+)\.wav", l2)
                if m:
                    alvos.append(int(m.group(1)))
                    break
    if not alvos or not dur:
        return None
    meia = float(os.environ.get("BIPAR_JANELA_S", "240"))
    # 13/11 (parte 6: whisper não achou na 1ª janela): a soma dos clipes ignora memes/transições/abertura e o "wrote
    # audio_N" do edge-tts paralelo pode ser da fala vizinha — então a janela vai da estimativa (soma) até o tempo do
    # clipe no ORIGINAL (o vídeo final fica entre os dois), com folga dos dois lados.
    ini_orig = {}
    for l in txt:
        m = re.search(r"\[segments/landscape\] clipe (\d+): corte@([\d.]+)s", l)
        if m:
            ini_orig[int(m.group(1))] = float(m.group(2))
    out = []
    for n in alvos:
        a = sum(dur.get(k, 0) for k in range(n))
        b = ini_orig.get(n, a)
        lo, hi = min(a, b) - meia * 0.5, max(a, b) + meia
        out.append((max(0.0, lo), hi - max(0.0, lo)))
    return out


def main(nome):
    ficha = FICHAS / nome
    d = json.loads((ficha / "nuvem.json").read_text(encoding="utf-8"))
    remoto = d["drive"]
    pasta = TMP / nome[:20]
    pasta.mkdir(parents=True, exist_ok=True)
    v = pasta / "video.mp4"
    if not v.exists() or v.stat().st_size < 1e8:
        log(f"baixando {remoto}")
        r = _sh([RCLONE, "copyto", remoto, str(v), "--transfers", "4"])
        if r.returncode:
            sys.exit(f"rclone falhou: {r.stderr[-300:]}")
    log("procurando o palavrão no áudio (whisper)...")
    achados = []
    for ini, dur in (_janelas(ficha) or [(0.0, None)]):
        wav = pasta / f"audio_{int(ini)}.wav"
        cmd = [FF, "-y", "-ss", f"{ini:.1f}"] + (["-t", f"{dur:.1f}"] if dur else []) + [
            "-i", str(v), "-vn", "-ac", "1", "-ar", "16000", str(wav)]
        _sh(cmd)
        log(f"  janela {ini:.0f}s +{dur or 'tudo'}s")
        achados += _achar(wav, ini)
        wav.unlink(missing_ok=True)
    log(f"achados: {achados}")
    if not achados:
        sys.exit("whisper não achou palavrão — conferir à mão (não mexi em nada)")
    filtros_vol = "+".join(f"between(t,{a - 0.05:.2f},{b + 0.05:.2f})" for a, b, _ in achados)
    bipe = "+".join(f"between(t,{a - 0.05:.2f},{b + 0.05:.2f})" for a, b, _ in achados)
    saida = pasta / "video_bipado.mp4"
    fc = (f"[0:a]volume=enable='{filtros_vol}':volume=0[a0];"
          f"sine=f=1000:sample_rate=48000,volume=0.25,aformat=channel_layouts=stereo,"
          f"volume=enable='not({bipe})':volume=0[b];"
          f"[a0][b]amix=inputs=2:duration=first:normalize=0[a]")
    r = _sh([FF, "-y", "-i", str(v), "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(saida)])
    if r.returncode or not saida.exists():
        sys.exit(f"ffmpeg falhou: {r.stderr[-500:]}")
    # confere: só a janela de cada achado (±3 s) passa no whisper de novo
    wav2 = pasta / "conf.wav"
    sobra = []
    for a, b, _ in achados:
        _sh([FF, "-y", "-ss", f"{max(a - 3, 0):.2f}", "-t", "7", "-i", str(saida), "-vn", "-ac", "1", "-ar", "16000",
             str(wav2)])
        sobra += _achar(wav2, max(a - 3, 0))
    if sobra:
        sys.exit(f"ainda ouvi palavrão depois do bipe: {sobra} — não subi")
    log(f"conferido: bipe em {len(achados)} ponto(s), nada sobrou")
    if os.environ.get("BIPAR_SO_TESTE") == "1":
        return
    base = remoto.rsplit("/", 1)[0]
    r = _sh([RCLONE, "moveto", remoto, f"{base}/video_com_palavrao.mp4"])
    if r.returncode:
        sys.exit(f"rclone (guardar original) falhou: {r.stderr[-300:]}")
    r = _sh([RCLONE, "copyto", str(saida), remoto, "--transfers", "4"])
    if r.returncode:
        sys.exit(f"rclone (subir bipado) falhou: {r.stderr[-300:]}")
    (ficha / "SEM_PALAVRAO.txt").write_text(json.dumps({"bipes": achados}, ensure_ascii=False), encoding="utf-8")
    est_p = AQUI / "longos_postados.json"
    est = json.loads(est_p.read_text(encoding="utf-8"))
    est["reprovados"] = [x for x in est["reprovados"] if x != nome]
    est_p.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in (v, wav2, saida):
        f.unlink(missing_ok=True)
    log(f"pronto: {nome} subiu bipado e saiu dos reprovados")


if __name__ == "__main__":
    main(sys.argv[1])
