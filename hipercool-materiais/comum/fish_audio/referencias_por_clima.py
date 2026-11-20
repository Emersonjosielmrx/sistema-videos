"""Dona 19/11: "não fica melhor colocar um longo maior? alguns só falam num padrão, mas momo e mike falam de muitas
maneiras diferentes no mesmo vídeo, principalmente nas piadas e comentários".

Para cada narrador parceiro, junta frases REAIS dele (dataset_narradores/<voz>/wavs + metadata.csv) por jeito de falar
(climas_voz._heuristica) e monta até 3 referências de 15-25 s:
    referencia_fish.wav/.txt          = narração normal (substitui a de 10 s: mais longa = Fish pega mais do estilo)
    referencia_fish_piada.wav/.txt    = comentário/piada (engracado)
    referencia_fish_tensao.wav/.txt   = tensão/ação/vilão/épico
O fish_nuvem escolhe por frase a referência do clima dela (sem a do clima = a normal). A antiga vai para
referencia_fish_antiga.*. Sobe para colab_recap/vozes/<voz>/.
    python referencias_por_clima.py [voz ...] [--sobe]
"""
import csv, json, re, subprocess, sys, wave
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import climas_voz  # noqa: E402

DS = Path(r"D:\hipercool-materiais\amostras_voz\dataset_narradores")
OUT = Path(r"D:\hipercool-materiais\amostras_voz\referencias_por_clima")
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
R = r"D:\tools\rclone.exe"
SEM = 0x08000000
GRUPO = {"normal": "", "comentario": "_piada", "engracado": "_piada", "tensao": "_tensao", "acao": "_tensao",
         "vilao": "_tensao", "epico": "_tensao", "terror": "_tensao", "triste": ""}
ALVO = (15.0, 25.0)


def _dur(w):
    with wave.open(str(w), "rb") as f:
        return f.getnframes() / f.getframerate()


def frases(voz):
    meta = DS / voz / "metadata.csv"
    if not meta.exists():
        return []
    out = []
    for row in csv.reader(meta.open(encoding="utf-8"), delimiter="|"):
        if len(row) < 2:
            continue
        w = DS / voz / "wavs" / f"{row[0]}.wav"
        if w.exists():
            try:
                out.append((w, row[1].strip(), _dur(w)))
            except (wave.Error, EOFError):
                pass
    return out


def montar(voz, sobe=False):
    fs = frases(voz)
    if len(fs) < 4:
        print(voz, "sem dataset suficiente")
        return {}
    climas = climas_voz._heuristica([t for _, t, _ in fs])
    grupos = {}
    for (w, t, d), c in zip(fs, climas):
        if climas_voz.eh_comentario(t):
            c = "comentario"
        grupos.setdefault(GRUPO.get(c, ""), []).append((w, t, d))
    pasta = OUT / voz
    pasta.mkdir(parents=True, exist_ok=True)
    feitos = {}
    for suf, lst in grupos.items():
        escolha, tot = [], 0.0
        for w, t, d in sorted(lst, key=lambda x: -x[2]):  # frases mais longas = fala mais contínua
            if d > ALVO[1] or tot + d > ALVO[1]:
                continue
            escolha.append((w, t))
            tot += d
            if tot >= ALVO[0]:
                break
        if tot < (ALVO[0] if suf == "" else 8.0):  # clima extra pode ser menor; a normal precisa de 15 s
            continue
        lista = pasta / f"lista{suf}.txt"
        lista.write_text("".join(f"file '{w.as_posix()}'\n" for w, _ in escolha), encoding="utf-8")
        dst = pasta / f"referencia_fish{suf}.wav"
        subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-ac", "1", "-ar",
                        "44100", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(dst)], check=True, creationflags=SEM)
        (pasta / f"referencia_fish{suf}.txt").write_text(" ".join(t for _, t in escolha), encoding="utf-8")
        lista.unlink()
        feitos[suf or "_normal"] = round(tot, 1)
    (pasta / "referencia_fish.origem").write_text("original:dataset_narradores (por clima 19/11)", encoding="utf-8")
    print(voz, feitos, flush=True)
    if sobe and "_normal" in feitos:
        dst = f"manhwa-drive:colab_recap/vozes/{voz}"
        for n in ("wav", "txt", "origem"):
            subprocess.run([R, "copyto", f"{dst}/referencia_fish.{n}", f"{dst}/referencia_fish_antiga.{n}"],
                           capture_output=True, creationflags=SEM)
        for f in pasta.glob("referencia_fish*"):
            subprocess.run([R, "copyto", str(f), f"{dst}/{f.name}"], check=True, creationflags=SEM)
    return feitos


if __name__ == "__main__":
    a = sys.argv[1:]
    sobe = "--sobe" in a
    vozes = [x for x in a if x != "--sobe"] or sorted(p.name for p in DS.iterdir() if p.is_dir())
    res = {v: montar(v, sobe) for v in vozes}
    (OUT / "_resumo.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
