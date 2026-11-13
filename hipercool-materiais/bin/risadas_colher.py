"""risadas_colher.py — BANCO DE RISADAS REAIS de cada narrador (04/11/2026).

Dona 04/11: "áudios originais sim é bom, principalmente risadas, porque a IA não ri direito; se conseguir montar pra
ficar natural, cada narrador tem várias risadas e nenhuma delas é igual a outra".

1. pede ao BAIXADOR do Kaggle (fila manhwa-drive:baixador, mesmo formato do bin\\kaggle_baixar.py; a casa está
   barrada pelo YouTube) o vídeo de origem de cada narrador (amostras_voz\\dataset_narradores\\<voz>\\fonte.txt) — o
   dataset do clone é só 1:00-14:00 e LIMPO (as risadas ficaram de fora: 0 reações em 22/10);
2. acha as risadas no áudio inteiro com o classificador AudioSet (MIT/ast-finetuned-audioset, CPU): classes
   Laughter, Giggle, Snicker, Belly laugh, Chuckle/chortle, Baby laughter fora;
3. corta cada risada (+0,15 s antes/0,25 depois), separa a voz da trilha (audio-separator, UVR) e normaliza;
4. grava models\\rvc\\vozes\\<voz>\\humano\\risadas\\risada_NN.wav + risadas.json (score, duração, origem).
   NÃO entra em vídeo nenhum ainda: a dona ouve a prévia (amostras_voz\\clone2\\humano\\<voz>_risadas.wav) antes.

    python risadas_colher.py pedir            # põe os pedidos na fila do baixador (1 por narrador)
    python risadas_colher.py colher [voz]     # traz o que voltou e extrai as risadas
"""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
DATASET = RAIZ / "amostras_voz" / "dataset_narradores"
VOZES = RAIZ / "models" / "rvc" / "vozes"
PREVIA = RAIZ / "amostras_voz" / "clone2" / "humano"
TMP = Path(r"D:\tmp\risadas")
RCLONE = r"D:\tools\rclone.exe"
FILA = "manhwa-drive:baixador"
SEPARADOR = Path(r"D:\tools\separador\Scripts\audio-separator.exe")
SEM_JANELA = 0x08000000
RISO = ("Laughter", "Giggle", "Snicker", "Belly laugh", "Chuckle, chortle")
LIMIAR = 0.30


def _rc(*a, timeout=600):
    r = subprocess.run([RCLONE, *a], capture_output=True, text=True, timeout=timeout, creationflags=SEM_JANELA)
    if r.returncode:
        raise RuntimeError(r.stderr[-300:])
    return r.stdout


def fontes():
    out = {}
    for d in sorted(DATASET.iterdir()):
        f = d / "fonte.txt"
        m = re.search(r"watch\?v=([\w-]{11})", f.read_text(encoding="utf-8", errors="ignore")) if f.exists() else None
        if m:
            out[d.name] = m.group(1)
    return out


def pedir():
    TMP.mkdir(parents=True, exist_ok=True)
    for voz, vid in fontes().items():
        pid = f"risada_{vid}"
        if (TMP / voz / "source.mp4").exists():
            continue
        p = TMP / f"{pid}.json"
        p.write_text(json.dumps({"id": pid, "url": f"https://www.youtube.com/watch?v={vid}", "max_height": 360,
                                 "legendas": []}), encoding="utf-8")
        _rc("copyto", str(p), f"{FILA}/pedidos/{pid}.json")
        p.unlink()
        print(f"pedido {voz}: {vid}", flush=True)


def _trazer(voz, vid):
    pid = f"risada_{vid}"
    nomes = set(_rc("lsf", f"{FILA}/prontos/{pid}").split()) if pid in _rc("lsf", f"{FILA}/prontos", "--dirs-only") \
        else set()
    if "erro.json" in nomes:
        print(f"{voz}: erro no Kaggle: {_rc('cat', f'{FILA}/prontos/{pid}/erro.json')[:200]}", flush=True)
        return None
    if "ok.json" not in nomes:
        return None
    d = TMP / voz
    d.mkdir(parents=True, exist_ok=True)
    _rc("copy", f"{FILA}/prontos/{pid}", str(d), "--exclude", "ok.json", timeout=1800)
    info = json.loads(_rc("cat", f"{FILA}/prontos/{pid}/ok.json"))
    _rc("purge", f"{FILA}/prontos/{pid}")
    v = d / info["video"]
    if v.exists() and v.name != "source.mp4":
        v.replace(d / "source.mp4")
    return d / "source.mp4"


_MODELO = {}


def _classificador():
    if not _MODELO:
        import os
        os.environ.setdefault("HF_HOME", r"D:\caches\huggingface")
        from transformers import ASTFeatureExtractor, ASTForAudioClassification
        nome = "MIT/ast-finetuned-audioset-10-10-0.4593"
        _MODELO["fe"] = ASTFeatureExtractor.from_pretrained(nome)
        _MODELO["m"] = ASTForAudioClassification.from_pretrained(nome).eval()
        ids = _MODELO["m"].config.label2id
        _MODELO["riso"] = [ids[n] for n in RISO if n in ids]
    return _MODELO


def achar(wav16):
    """[(ini, fim, score)] das janelas de 1 s (passo 0,5 s) com risada; janelas vizinhas viram 1 trecho."""
    import numpy as np
    import soundfile as sf
    import torch
    x, sr = sf.read(str(wav16), dtype="float32")
    M = _classificador()
    jan, passo, achados = sr, sr // 2, []
    lote, pos = [], []
    for i in range(0, max(1, len(x) - jan), passo):
        lote.append(x[i:i + jan]); pos.append(i / sr)
        if len(lote) == 32 or i + passo >= len(x) - jan:
            f = M["fe"](lote, sampling_rate=sr, return_tensors="pt")
            with torch.no_grad():
                p = torch.sigmoid(M["m"](**f).logits)[:, M["riso"]].max(dim=1).values.numpy()
            achados += [(t, float(s)) for t, s in zip(pos, p) if s >= LIMIAR]
            lote, pos = [], []
    trechos = []
    for t, s in achados:
        if trechos and t <= trechos[-1][1] + 0.1:
            trechos[-1] = (trechos[-1][0], t + 1.0, max(trechos[-1][2], s))
        else:
            trechos.append((t, t + 1.0, s))
    return [(a, b, s) for a, b, s in trechos if 0.4 <= b - a <= 4.0]


def colher(so=None):
    for voz, vid in fontes().items():
        if so and voz != so:
            continue
        src = TMP / voz / "source.mp4"
        if not src.exists():
            src = _trazer(voz, vid)
            if not src:
                print(f"{voz}: ainda não voltou do baixador", flush=True)
                continue
        wav = TMP / voz / "a16.wav"
        if not wav.exists():
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                           check=True, creationflags=SEM_JANELA)
        t0 = time.time()
        trechos = sorted(achar(wav), key=lambda x: -x[2])[:25]
        print(f"{voz}: {len(trechos)} risadas candidatas em {time.time() - t0:.0f} s", flush=True)
        destino = VOZES / voz / "humano" / "risadas"
        if destino.exists():
            shutil.rmtree(destino)
        destino.mkdir(parents=True)
        lista = []
        for n, (a, b, s) in enumerate(sorted(trechos), 1):
            bruto = TMP / voz / f"r{n:02d}.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0, a - 0.15):.2f}", "-t", f"{b - a + 0.4:.2f}",
                            "-i", str(src), "-vn", "-ac", "1", "-ar", "44100", str(bruto)], check=True,
                           creationflags=SEM_JANELA)
            voz_wav = bruto
            if SEPARADOR.exists():  # tira a música de fundo, fica só a risada
                sep = TMP / voz / f"sep{n:02d}"
                subprocess.run([str(SEPARADOR), str(bruto), "--output_dir", str(sep), "--single_stem", "Vocals",
                                "--output_format", "WAV"], capture_output=True, creationflags=SEM_JANELA, timeout=600)
                achou = next(iter(sep.glob("*Vocals*.wav")), None)
                if achou:
                    voz_wav = achou
            final = destino / f"risada_{n:02d}.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(voz_wav), "-af",
                            "afade=t=in:d=0.05,areverse,afade=t=in:d=0.12,areverse,loudnorm=I=-20:TP=-2",
                            "-ar", "44100", "-ac", "1", str(final)], check=True, creationflags=SEM_JANELA)
            lista.append({"arquivo": final.name, "score": round(s, 2), "dur": round(b - a + 0.4, 2),
                          "origem": f"https://youtu.be/{vid}?t={int(a)}"})
        (destino.parent / "risadas.json").write_text(json.dumps(
            {"gerado": time.strftime("%d/%m %H:%M"), "fonte": vid, "aprovado": False, "risadas": lista},
            ensure_ascii=False, indent=1), encoding="utf-8")
        if lista:  # prévia pra dona ouvir: todas emendadas com 0,6 s de pausa
            PREVIA.mkdir(parents=True, exist_ok=True)
            txt = TMP / voz / "previa.txt"
            sil = TMP / "sil.wav"
            if not sil.exists():
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t",
                                "0.6", str(sil)], check=True, creationflags=SEM_JANELA)
            txt.write_text("".join(f"file '{(destino / x['arquivo']).as_posix()}'\nfile '{sil.as_posix()}'\n"
                                   for x in lista), encoding="utf-8")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(txt),
                            str(PREVIA / f"{voz}_risadas.wav")], check=True, creationflags=SEM_JANELA)
        print(f"{voz}: {len(lista)} risadas em {destino}", flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "pedir":
        pedir()
    elif a and a[0] == "colher":
        colher(a[1] if len(a) > 1 else None)
    else:
        print(__doc__)
