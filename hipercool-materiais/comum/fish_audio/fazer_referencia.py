"""Gera referencia_fish.wav + referencia_fish.txt (o que o Fish Speech copia: timbre + jeito de falar) a partir de uma
fala ORIGINAL do narrador/personagem (dona 19/11: "baixar o máximo de áudios originais; usar principalmente os dos
narradores"). Escolhe o melhor trecho de 8-14 s: frases inteiras, só fala (Whisper, português), sem silêncio longo.

    python fazer_referencia.py <audio_original> <saida_pasta> [--sobe <voz>]   # --sobe = copia p/ Drive vozes/<voz>
    python fazer_referencia.py --site <id_fish> <voz> [--sobe]                  # base vinda do SITE (marcada _SITE)

A referência "do site" (voz pública do Fish gerada online) é só PONTE até achar o original: fica marcada
(referencia_fish.origem = "site:<id>") para ser trocada depois pelo áudio original.
"""
import json, subprocess, sys
from pathlib import Path

FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
R = r"D:\tools\rclone.exe"
TEXTO_SITE = ("Olha só que história incrível. Ninguém esperava o que ia acontecer depois. "
              "E foi exatamente aí que tudo mudou, de um jeito que ninguém conseguia acreditar.")


def melhor_trecho(audio, alvo_min=8.0, alvo_max=14.0, janela_s=120):
    """19/11: só os primeiros `janela_s` (4 min de áudio inteiro estourou a RAM do PC1: mkl_malloc). Para achar 10 s
    bons, 2 min bastam."""
    import tempfile
    from faster_whisper import WhisperModel
    curto = Path(tempfile.gettempdir()) / f"_ref_{Path(audio).stem}.wav"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(audio), "-t", str(janela_s), "-ac", "1", "-ar", "16000",
                    str(curto)], check=True)
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2)
    segs, info = m.transcribe(str(curto), language="pt", vad_filter=True)
    segs = list(segs)
    curto.unlink(missing_ok=True)
    segs = [s for s in segs if s.text.strip() and s.avg_logprob > -0.8]
    melhor = None
    for i in range(len(segs)):
        ini, txt, j = segs[i].start, [], i
        while j < len(segs) and segs[j].end - ini <= alvo_max:
            if j > i and segs[j].start - segs[j - 1].end > 0.8:  # pausa longa = outra pessoa / corte
                break
            txt.append(segs[j].text.strip())
            fim = segs[j].end
            j += 1
            dur = fim - ini
            if dur >= alvo_min:
                nota = sum(s.avg_logprob for s in segs[i:j]) / (j - i)
                if melhor is None or nota > melhor[0]:
                    melhor = (nota, ini, fim, " ".join(txt))
    return melhor


def gravar(audio, ini, fim, texto, pasta, origem):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", f"{max(0, ini - 0.1):.2f}", "-to", f"{fim + 0.2:.2f}", "-i",
                    str(audio), "-ac", "1", "-ar", "44100", "-af", "loudnorm=I=-18:TP=-2", str(pasta / "referencia_fish.wav")],
                   check=True)
    (pasta / "referencia_fish.txt").write_text(texto, encoding="utf-8")
    (pasta / "referencia_fish.origem").write_text(origem, encoding="utf-8")


def subir(pasta, voz):
    for n in ("referencia_fish.wav", "referencia_fish.txt", "referencia_fish.origem"):
        subprocess.run([R, "copyto", str(Path(pasta) / n), f"manhwa-drive:colab_recap/vozes/{voz}/{n}"], check=True)


def texto_do_personagem(voz):
    """Fala no jeito do próprio personagem (vozes_novas_ab.P / falas_kitten_extra) — o Fish copia melhor o jeito dele
    com uma fala dele do que com texto neutro. Sem fala cadastrada = texto neutro de narrador."""
    try:
        s = open(r"D:\tmp\vozes_novas_ab.py", encoding="utf-8").read()
        a = s.index("P = {")
        P = {k: v[3] for k, v in eval(s[a + 4:s.index("\n}\n", a) + 2]).items()}  # noqa: S307 (arquivo nosso)
        sys.path.insert(0, r"D:\tmp")
        import falas_kitten_extra
        P.update(falas_kitten_extra.F)
        t = P.get(voz) or P.get(voz.rsplit("_", 1)[0])
        if t and len(t) > 60:
            return t[:300]
    except Exception:  # noqa: BLE001
        pass
    return TEXTO_SITE


def do_site(id_fish, voz, pasta):
    """Gera ~12 s com a voz pública do site (fish_lote, conta do pool) e usa como referência — PONTE até o original."""
    sys.path.insert(0, str(Path(__file__).parent))
    import fish_http
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    mp3 = pasta / "_site.mp3"
    texto = texto_do_personagem(voz)
    feitos = fish_http.gerar_frases([(0, texto, str(mp3))], voz=id_fish, log=print)
    if not feitos:
        return False
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", "-af",
                    "loudnorm=I=-18:TP=-2", str(pasta / "referencia_fish.wav")], check=True)
    mp3.unlink(missing_ok=True)
    (pasta / "referencia_fish.txt").write_text(texto, encoding="utf-8")
    (pasta / "referencia_fish.origem").write_text(f"site:{id_fish}", encoding="utf-8")
    return True


if __name__ == "__main__":
    a = sys.argv[1:]
    sobe = "--sobe" in a
    a = [x for x in a if x != "--sobe"]
    if a[0] == "--site":
        idf, voz = a[1], a[2]
        pasta = Path(r"D:\tmp\referencias_fish") / voz
        ok = do_site(idf, voz, pasta)
        print(voz, "site", "OK" if ok else "FALHOU")
        if ok and sobe:
            subir(pasta, voz)
    else:
        audio, pasta = Path(a[0]), Path(a[1])
        voz = a[2] if len(a) > 2 else pasta.name
        r = melhor_trecho(audio)
        if not r:
            print(voz, "sem trecho bom")
            sys.exit(1)
        nota, ini, fim, texto = r
        gravar(audio, ini, fim, texto, pasta, f"original:{audio.name}")
        print(f"{voz}: {fim - ini:.1f}s (nota {nota:.2f}) | {texto[:90]}")
        if sobe:
            subir(pasta, voz)
