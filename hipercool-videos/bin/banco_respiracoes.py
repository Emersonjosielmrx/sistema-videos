#!/usr/bin/env python3
"""Banco de RESPIRAÇÕES reais, tiradas da voz humana dos narradores que autorizaram (17/10/2026).

Ideia 13 da lista de voz humana: voz de IA não respira, e é um dos sinais que o ouvido pega primeiro.
Fonte: assets/intros_voz/*.wav — as aberturas dos 15 canais que autorizaram o uso da voz (15/10), já
separadas da música pelo audio-separator. Elas ficam só como respiração (sem nenhuma palavra), então
não se ouve a voz de ninguém no nosso vídeo.

Como acha: o Groq dá o tempo de cada palavra; o intervalo entre duas palavras com 0,22 a 1,2 s que tem
energia ACIMA do ruído e ABAIXO da fala é candidato a respiração. Corta com fade, nivela e grava em
assets/respiracoes/. Depois confere: o Groq não pode achar palavra nenhuma no recorte.

    python bin/banco_respiracoes.py
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log  # noqa: E402

FONTE = PROJECT_DIR / "assets" / "intros_voz"
DESTINO = PROJECT_DIR / "assets" / "respiracoes"
SR = 24000
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _ler(wav):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, timeout=120, creationflags=_SEM_JANELA)
    return np.frombuffer(r.stdout, dtype=np.float32)


def _db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


def _gravar(x, path):
    n = int(0.03 * SR)
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    x *= 10 ** ((-30 - _db(x)) / 20)  # todas no mesmo nível; o mixer ajusta depois
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s16le", str(path)], input=x.astype(np.float32).tobytes(), check=True,
                   timeout=60, creationflags=_SEM_JANELA)


HOP = int(0.025 * SR)


def _zcr(x):
    return float(np.mean(np.abs(np.diff(np.sign(x))) > 0))


def candidatos(x):
    """[(ini_s, fim_s, db, zcr)] dos vales com cara de respiração.

    17/10: o 1º jeito (intervalo entre palavras do Groq) achou ZERO — o Whisper cola as palavras e
    esses narradores EDITAM cortando as pausas (há -180 dB, silêncio digital, nos cortes). Respiração
    sobra como vale curto de -26 a -48 dB entre trechos de fala. O que separa ar de vogal é o ruído:
    respiração cruza o zero muito mais vezes (zcr alto)."""
    db = np.array([_db(x[i:i + HOP]) for i in range(0, len(x) - HOP, HOP)])
    out, i = [], 0
    while i < len(db):
        if -48 <= db[i] <= -26:
            j = i
            while j < len(db) and -48 <= db[j] <= -24:
                j += 1
            ini, fim = i * HOP / SR, j * HOP / SR
            antes = db[max(0, i - 4):i]
            depois = db[j:j + 4]
            if 0.15 <= fim - ini <= 0.8 and len(antes) and len(depois) and antes.max() > -22 and depois.max() > -22:
                seg = x[i * HOP:j * HOP]
                z = _zcr(seg)
                if z > 0.18:
                    out.append((ini, fim, float(_db(seg)), z))
            i = j
        else:
            i += 1
    return out


def main():
    import groq_api
    DESTINO.mkdir(parents=True, exist_ok=True)
    indice = []
    for wav in sorted(FONTE.glob("*.wav")):
        x = _ler(wav)
        if not len(x):
            continue
        k = 0
        for ini, fim, d, z in candidatos(x):
            k += 1
            nome = f"{wav.stem}_{k}.wav"
            _gravar(x[int(ini * SR):int(fim * SR)], DESTINO / nome)
            indice.append({"arquivo": nome, "dur": round(fim - ini, 2), "db": round(d, 1), "zcr": round(z, 3)})
        log(f"  {wav.name}: {k} candidatas")
    # conferência: recorte com palavra dentro não é respiração
    bons = []
    for it in indice:
        j = groq_api.transcrever(DESTINO / it["arquivo"], "pt", palavras=False) or {}
        txt = (j.get("text") or "").strip()
        if len(txt.split()) >= 2:
            (DESTINO / it["arquivo"]).unlink(missing_ok=True)
            log(f"  fora: {it['arquivo']} tinha fala ({txt[:40]})")
        else:
            bons.append(it)
    (DESTINO / "indice.json").write_text(json.dumps(bons, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"banco: {len(bons)} respirações em {DESTINO}")


if __name__ == "__main__":
    main()
