r"""compilar_serie.py — compilado de uma série de longos (12/11, dona: "posta a parte 1, aí posta o compilado parte 1 e 2;
postou a 3, posta o compilado 1-2-3; é só cortar os resumos e deixar só o primeiro — faz mais sentido do que a pessoa
ir procurando as partes").

Junta as partes JÁ RENDERIZADAS (vídeo do Drive, 1_youtube_pendente/<ficha>/video.mp4) em ordem, SEM reencodar
(concat -c copy): a 1ª parte inteira, das seguintes corta o resumo de abertura (do início até resumo_fim). Onde termina o
resumo: resumo_fim.json da ficha (pipeline 12/11) ou, nas partes antigas, o capítulo/segundo indicado no CORTES manual.
Tempo: sem reencodar = só cópia de disco (~1-2 min por hora de vídeo) + download/upload. O vídeo final fica em
D:\hipercool-materiais\_longos_postar\COMPILADO_<serie>_1-N\final_anime_deitado.mp4 pra o postar_longos subir.

    python compilar_serie.py he_got_into_the_medieval_age            # mostra o plano (partes, cortes, duração)
    python compilar_serie.py he_got_into_the_medieval_age --fazer    # baixa, corta, junta
"""
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
SAIDA = Path(r"D:\hipercool-materiais\_longos_postar")
RCLONE = r"D:\tools\rclone.exe"
DRIVE = "manhwa-drive:videos-backup/anime/1_youtube_pendente"
RESUMO_PADRAO_S = 45.0  # partes antigas sem resumo_fim.json: o resumo tem 6 frases (~35-60 s)

sys.path.insert(0, str(AQUI))
import postar_longos as pl  # noqa: E402


def partes(serie):
    out = {}
    for d in FICHAS.iterdir():
        primeira = d.name.startswith("SNhb31ZuuFA") and serie == "he_got_into_the_medieval_age"
        if d.is_dir() and (pl._serie(d.name) == serie or primeira) and (d / "nuvem.json").exists():
            n = pl._parte(d.name)
            if n == 999 and d.name.startswith("SNhb31ZuuFA"):  # a 1ª ficha da série veio sem número (é a 1-2)
                n = 1
            if n < 999:
                out[n] = d
    return dict(sorted(out.items()))


def dur(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True, timeout=120)
    return float(r.stdout.strip() or 0)


def corte(ficha):
    j = ficha / "resumo_fim.json"
    if j.exists():
        return float(json.loads(j.read_text(encoding="utf-8"))["resumo_fim_s"]), "resumo_fim.json"
    log = ficha / "pipeline.log"
    if log.exists():
        # partes antigas: soma a duração dos clipes do resumo (0..N-1, a ÚLTIMA medida de cada um no log) + respiro
        # de 0,5 s entre clipes + 2 memes de resumo (~2,5 s cada, config longo.json resumo.memes)
        t = log.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"resumo de abertura: (\d+) frases", t)
        if m:
            n = int(m.group(1))
            durs = {}
            for k, d in re.findall(r"clipe (\d+) \(landscape\) Start=[\d.]+s Dur=([\d.]+)s", t):
                if int(k) < n:
                    durs[int(k)] = float(d)
            if len(durs) == n:
                return round(sum(durs.values()) + 0.5 * n + 2 * 2.5, 1), f"medido no log ({n} frases)"
        return RESUMO_PADRAO_S, "padrão (sem resumo_fim)"
    return 0.0, "sem resumo"


def main(serie, fazer, ate=None):
    ps = partes(serie)
    if ate:
        ps = {n: d for n, d in ps.items() if n <= ate}
    print(f"série {serie}: partes {list(ps)}")
    plano = []
    for i, (n, d) in enumerate(ps.items()):
        c, de = (0.0, "1ª parte inteira") if i == 0 else corte(d)
        plano.append((n, d, c, de))
        print(f"  parte {n}: corta os primeiros {c:.0f} s ({de})")
    if not fazer:
        return
    pasta = SAIDA / f"COMPILADO_{serie}_1-{max(ps)}"
    pasta.mkdir(parents=True, exist_ok=True)
    lista = []
    for n, d, c, _ in plano:
        bruto = pasta / f"p{n:02d}.mp4"
        if not bruto.exists():
            subprocess.run([RCLONE, "copyto", f"{DRIVE}/{d.name}/video.mp4", str(bruto)], check=True)
        if c > 0:
            cortado = pasta / f"p{n:02d}_sem_resumo.mp4"
            # -ss depois do -i + -c copy: corta no keyframe seguinte (sem reencodar); erro de < 2 s é aceitável
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(bruto), "-ss", f"{c:.2f}", "-c", "copy",
                            "-avoid_negative_ts", "make_zero", str(cortado)], check=True)
            bruto.unlink()
            bruto = cortado
        lista.append(bruto)
    txt = pasta / "lista.txt"
    txt.write_text("".join(f"file '{p.as_posix()}'\n" for p in lista), encoding="utf-8")
    final = pasta / "final_anime_deitado.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(txt), "-c", "copy",
                    "-movflags", "+faststart", str(final)], check=True)
    for p in lista:
        p.unlink(missing_ok=True)
    print(f"pronto: {final} ({dur(final) / 3600:.1f} h)")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    ate = next((int(x.split("=")[1]) for x in sys.argv if x.startswith("--ate=")), None)
    main(a[0] if a else "he_got_into_the_medieval_age", "--fazer" in sys.argv, ate)
