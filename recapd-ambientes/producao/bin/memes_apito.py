r"""memes_apito.py — 11/11 dona (Medieval parte 9): "o primeiro meme é horrível, com piiiii que deixa a gente surdo e por
muito tempo". Acha os memes com APITO (tom puro contínuo e alto, tipo censura/zumbido) e com volume estourado, pra
sairem do sorteio. Resultado em workspace/assets/memes_img/memes_proibidos_som.json (lido por fx_detect.meme_proibido).

Critério (por janela de 0,25 s, só nas janelas altas): a energia concentrada num pico estreito do espectro (>60% num
tom, 'tonalidade') por >= 0,6 s seguidos = apito; ou média de volume > -9 dBFS = estourado.

    python memes_apito.py           # mede tudo e grava
    python memes_apito.py --ver     # só mostra
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

PASTA = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "memes_img" / "memes"
SAIDA = PASTA.parent / "memes_proibidos_som.json"
SR = 22050


def audio(p):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                       capture_output=True, timeout=120)
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def medir(p):
    a = audio(p)
    if a.size < SR // 2:
        return None
    jan = SR // 4
    tons, seguidos, maior = [], 0, 0
    rms_db = 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
    for i in range(0, a.size - jan, jan):
        x = a[i:i + jan]
        r = np.sqrt(np.mean(x ** 2))
        if r < 0.05:  # janela baixa: não é apito
            seguidos = 0
            continue
        esp = np.abs(np.fft.rfft(x * np.hanning(jan))) ** 2
        k = int(np.argmax(esp))
        f = k * SR / jan
        perto = esp[max(0, k - 3):k + 4].sum() / (esp.sum() + 1e-12)
        if perto > 0.6 and 400 < f < 6000:
            seguidos += 1
            maior = max(maior, seguidos)
            tons.append(round(f))
        else:
            seguidos = 0
    apito_s = maior * 0.25
    return {"apito_s": apito_s, "freq": int(np.median(tons)) if tons else 0, "rms_db": round(float(rms_db), 1),
            "dur": round(a.size / SR, 1)}


def main(gravar):
    ruins = {}
    for p in sorted(PASTA.glob("*.mp4")):
        try:
            m = medir(p)
        except Exception as e:  # noqa: BLE001
            print(f"{p.name}: erro {type(e).__name__}")
            continue
        if not m:
            continue
        motivo = []
        if m["apito_s"] >= 0.6:
            motivo.append(f"apito {m['apito_s']:.1f}s em {m['freq']} Hz")
        if m["rms_db"] > -9:
            motivo.append(f"volume estourado {m['rms_db']} dBFS")
        if motivo:
            ruins[p.name] = {"motivo": ", ".join(motivo), **m}
            print(f"RUIM {p.name}: {', '.join(motivo)} (dur {m['dur']}s)")
    print(f"{len(ruins)} memes com apito/volume estourado")
    if gravar:
        SAIDA.write_text(json.dumps(ruins, ensure_ascii=False, indent=1), encoding="utf-8")
        print("gravado", SAIDA)


if __name__ == "__main__":
    main("--ver" not in sys.argv)
