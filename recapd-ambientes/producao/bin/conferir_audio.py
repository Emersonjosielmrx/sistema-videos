"""conferir_audio.py — OUVE o Short pronto antes de subir (dona 23/10/2026, depois do mushishi: a narração era a
mensagem de erro do Gemini e só foi pega porque ela viu).

Transcreve o áudio do vídeo da ficha (Groq, o mesmo de monitor_bordoes/anime_testes) e SEGURA quando:
  - quase nada se ouve (narração vazia/muda) pro tamanho do vídeo;
  - a fala tem cara de erro/recusa da IA (anime_script.resposta_de_erro);
  - vídeo em português falado em inglês;
  - roteiro conhecido e quase nada dele aparece no que se ouve.
Não deu pra conferir (Groq fora, sem ffmpeg) = NÃO segura (a conferência nunca para a postagem).
O resultado fica no postar.json ("conferido_audio") — cada vídeo é ouvido uma vez.

    python bin\\conferir_audio.py <pasta da ficha>      # mostra o veredito sem mudar nada
"""
import difflib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
SEM_JANELA = 0x08000000
INGLES = set("the and you that this with what was for are have they but not his her she him from there their "
             "just like know when then because would could should".split())


def _palavras(t):
    t = unicodedata.normalize("NFKD", str(t or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def _duracao(video):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True, timeout=60, creationflags=SEM_JANELA)
        return float(r.stdout.strip())
    except Exception:  # noqa: BLE001
        return 0.0


def _roteiro(ficha, d):
    """Roteiro que devia ser narrado (pasta de trabalho do metadata.json), ou None."""
    try:
        m = json.loads((ficha / "metadata.json").read_text(encoding="utf-8"))
        work = Path(((m.get("video") or {}).get("path")) or "").parent
        rot = work / "roteiro.txt"
        if rot.exists() and d.get("idioma", "pt") == "pt":
            return rot.read_text(encoding="utf-8")
    except (OSError, ValueError):
        pass
    return None


def _tem_som(audio):
    """True = há som de verdade; False = mudo (volume médio < -50 dB ou 90%+ do tempo em silêncio); None = não medi."""
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(audio), "-af",
                            "volumedetect,silencedetect=noise=-45dB:d=0.5", "-vn", "-f", "null", "-"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                           creationflags=SEM_JANELA)
        m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stderr or "")
        if not m:
            return None
        if float(m.group(1)) < -50:
            return False
        mudo = sum(float(x) for x in re.findall(r"silence_duration:\s*([\d.]+)", r.stderr or ""))
        dur = _duracao(audio)
        return not (dur > 0 and mudo / dur >= 0.9)
    except Exception:  # noqa: BLE001
        return None


def _whisper_local(audio):
    """Transcrição pelo Whisper do próprio PC (o mesmo _whisper_sub.py do anime_fetch, modelo tiny) — reserva de quando
    o Groq está fora. '' se não deu."""
    try:
        r = subprocess.run([sys.executable, str(BIN / "_whisper_sub.py"), str(audio), "tiny"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=600, creationflags=SEM_JANELA)
        return (r.stdout or "").splitlines()[0].strip() if r.returncode == 0 and (r.stdout or "").strip() else ""
    except Exception:  # noqa: BLE001
        return ""


def ouvir(ficha):
    """{"ok": True|False|None, "motivo", "ouvido", ...}. None = não deu pra conferir."""
    ficha = Path(ficha)
    d = json.loads((ficha / "postar.json").read_text(encoding="utf-8"))
    video = ficha / (d.get("arquivo") or "video.mp4")
    if not video.exists():
        return {"ok": None, "motivo": "vídeo não está no PC"}
    mp3 = ficha / "_ouvir.mp3"
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k",
                        str(mp3)], check=True, timeout=180, creationflags=SEM_JANELA)
        import monitor_bordoes
        ouvido = monitor_bordoes._transcrever(mp3) or ""
        # 13/11: TRANSCRIÇÃO VAZIA NÃO É VÍDEO MUDO. Com o Groq fora ("Organization has been restricted", proxy fora)
        # a transcrição volta vazia e a regra abaixo lia "0 palavras = quase nada se ouve": 25 Shorts prontos segurados
        # só em 13/11 (53 em 2 semanas) e depois descartados pro Drive pelo descartar_segurados. Conferido num deles
        # (sem-obra-ec501f): volume -17 dB, 0 s de silêncio, narração inteira. Zero palavra só vale como "mudo" se o
        # ÁUDIO for mudo de verdade (medido pelo ffmpeg); com som, tenta o Whisper local e, sem ele, NÃO segura.
        if not _palavras(ouvido):
            som = _tem_som(mp3)
            if som is not False:
                local = _whisper_local(mp3)
                if _palavras(local):
                    ouvido = local
                else:
                    return {"ok": None, "motivo": "transcrição vazia com som no vídeo (Groq fora?) — não conferi",
                            "tem_som": som}
    except Exception as e:  # noqa: BLE001
        return {"ok": None, "motivo": f"não conferi ({type(e).__name__})"}
    finally:
        mp3.unlink(missing_ok=True)
    dur = _duracao(video)
    pal = _palavras(ouvido)
    motivos = []
    if dur >= 15 and len(pal) < max(8, dur * 0.6):  # narração normal: 2+ palavras/s; aqui menos de 0,6/s
        motivos.append(f"quase nada se ouve ({len(pal)} palavras em {dur:.0f} s)")
    try:
        import anime_script
        if anime_script.resposta_de_erro(ouvido):
            motivos.append("a fala tem cara de erro/recusa da IA")
    except Exception:  # noqa: BLE001
        pass
    if d.get("idioma", "pt") == "pt" and len(pal) >= 15 and sum(p in INGLES for p in pal) / len(pal) > 0.12:
        motivos.append("vídeo em português com fala em inglês")
    rot = _roteiro(ficha, d)
    if rot and len(pal) >= 8:
        a = _palavras(rot)
        sem = sum(m.size for m in difflib.SequenceMatcher(None, a, pal, autojunk=False).get_matching_blocks()) / max(1, len(a))
        if sem < 0.30:
            motivos.append(f"só {sem:.0%} do roteiro aparece no que se ouve")
    if not pal and not motivos:
        return {"ok": None, "motivo": "transcrição vazia (Groq fora?)"}
    return {"ok": not motivos, "motivo": "; ".join(motivos), "ouvido": ouvido[:300], "palavras": len(pal),
            "duracao_s": round(dur)}


def antes_de_subir(ficha, log=print):
    """True = pode subir. Ouve 1 vez por vídeo (resultado no postar.json); ruim = segura (pronto=False) e avisa."""
    ficha = Path(ficha)
    pj = ficha / "postar.json"
    d = json.loads(pj.read_text(encoding="utf-8"))
    if (d.get("conferido_audio") or {}).get("ok") is True:
        return True
    r = ouvir(ficha)
    d = json.loads(pj.read_text(encoding="utf-8"))  # relê: pode ter mudado enquanto transcrevia
    d["conferido_audio"] = r
    if r.get("ok") is False:
        d["pronto"] = False
        d["revisao"] = f"segurado: áudio conferido antes de subir — {r['motivo']}"
        log(f"{ficha.name}: SEGURADO pela conferência do áudio — {r['motivo']}")
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar(f"Short segurado antes de subir ({ficha.name}): {r['motivo']}. Ouvido: «{r['ouvido'][:150]}»",
                          "conferência do áudio", importante=True)
        except Exception:  # noqa: BLE001
            pass
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return r.get("ok") is not False


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(ouvir(sys.argv[1]), ensure_ascii=False, indent=1))
