"""Referência do Fish para PERSONAGEM sem gastar crédito (dona 19/11: "não deve gastar créditos e sim usar Shorts já
feitos com o novo motor; aí vai procurando as vozes reais e trocando").

O fish_lote guarda em colheita\\<id da voz no site>\\ as falas que os Shorts já geraram no Fish (wav + txt). Aqui, com
>= 8 s de fala colhida, monta referencia_fish.wav (falas juntas, 8-14 s) + .txt e sobe pro Drive
(colab_recap/vozes/<voz>/), guardando a anterior como referencia_fish_antiga.*. origem = "colheita:<id>".
Voz com referência ORIGINAL de narrador parceiro (cortado.wav) nunca é trocada.

    python colher_referencias.py            # todas as vozes com colheita suficiente
    python colher_referencias.py <id>       # só uma
"""
import json, subprocess, sys, wave
from pathlib import Path

AQUI = Path(__file__).resolve().parent
R = r"D:\tools\rclone.exe"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
COLHEITA = AQUI / "colheita"
SEM_JANELA = 0x08000000


def _dur(w):
    try:
        with wave.open(str(w), "rb") as f:
            return f.getnframes() / f.getframerate()
    except Exception:  # noqa: BLE001
        return 0


def _nome_da_voz(idf):
    s = json.loads((AQUI / "vozes_site.json").read_text(encoding="utf-8"))
    return next((k for k, v in s.items() if isinstance(v, dict) and v.get("id") == idf), None)


def _origem_atual(voz):
    r = subprocess.run([R, "cat", f"manhwa-drive:colab_recap/vozes/{voz}/referencia_fish.origem"], capture_output=True,
                       text=True, creationflags=SEM_JANELA)
    return r.stdout.strip() if r.returncode == 0 else ""


def montar(idf, log=print):
    voz = _nome_da_voz(idf)
    pasta = COLHEITA / idf
    if not voz or not pasta.exists() or (pasta / "_feito").exists():
        return False
    falas = [(w, _dur(w)) for w in sorted(pasta.glob("*.wav"))]
    falas = [(w, d) for w, d in falas if 1.5 <= d <= 14 and w.with_suffix(".txt").exists()]
    escolha, tot = [], 0.0
    for w, d in sorted(falas, key=lambda x: -x[1]):
        if tot + d <= 14:
            escolha.append(w)
            tot += d
        if tot >= 10:
            break
    if tot < 8:
        return False
    origem = _origem_atual(voz)
    if origem.startswith("original:cortado") or origem.startswith("colheita:"):
        return False  # narrador parceiro (original de verdade) ou já colhida
    out = AQUI / "_colheita_saida" / voz
    out.mkdir(parents=True, exist_ok=True)
    lista = out / "lista.txt"
    lista.write_text("".join(f"file '{w.as_posix()}'\n" for w in escolha), encoding="utf-8")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-ac", "1", "-ar",
                    "44100", "-af", "loudnorm=I=-18:TP=-2", str(out / "referencia_fish.wav")], check=True,
                   creationflags=SEM_JANELA)
    (out / "referencia_fish.txt").write_text(" ".join(w.with_suffix(".txt").read_text(encoding="utf-8").strip()
                                                      for w in escolha), encoding="utf-8")
    (out / "referencia_fish.origem").write_text(f"colheita:{idf}", encoding="utf-8")
    dst = f"manhwa-drive:colab_recap/vozes/{voz}"
    if origem:
        for n in ("wav", "txt", "origem"):
            subprocess.run([R, "copyto", f"{dst}/referencia_fish.{n}", f"{dst}/referencia_fish_antiga.{n}"],
                           capture_output=True, creationflags=SEM_JANELA)
    for n in ("referencia_fish.wav", "referencia_fish.txt", "referencia_fish.origem"):
        subprocess.run([R, "copyto", str(out / n), f"{dst}/{n}"], check=True, creationflags=SEM_JANELA)
    (pasta / "_feito").write_text(voz, encoding="utf-8")
    log(f"[colheita] {voz}: referência nova do Fish ({tot:.1f} s de {len(escolha)} falas), antes '{origem or 'nenhuma'}'")
    return True


if __name__ == "__main__":
    ids = sys.argv[1:] or [p.name for p in COLHEITA.iterdir() if p.is_dir()] if COLHEITA.exists() else []
    for i in ids:
        try:
            montar(i)
        except Exception as e:  # noqa: BLE001
            print(i, "erro", type(e).__name__, e)
