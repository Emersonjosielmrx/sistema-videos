"""clone2.py — CLONE 2.0: o JEITO de falar de cada narrador parceiro, não só o timbre (dono 19/10/2026).

O clone v1 (RVC) copia só o timbre: ritmo, pausas, entonação e palavras vinham da voz base (Francisca/Kokoro) e da
curva de locutor genérica — "gêmeos criados em lugares diferentes" (dono). O 2.0 mede no material REAL de cada um:
  ritmo        velocidade DENTRO da frase, variação da velocidade, pausas (legendas com tempo por palavra, até 40
               vídeos por canal: referencias_narradores\\<canal>\\*.vtt, via hipercool bin\\medir_narradores.py)
  entonação    quanto a voz sobe e desce dentro da frase e de uma frase pra outra (material de treino, pyin)
  volume       quanto o volume muda de uma frase pra outra
  microfone    equalização (espectro médio da voz real × o do clone v1)
  linguagem    conectores, gírias/regionalismos, contrações, bordões, apelidos, tiradas (LLM sobre a análise de
               milhões de palavras das legendas + a transcrição real) -> o roteiro sai escrito no jeito dele
Tudo comparado com as vozes base medidas do MESMO jeito (calibrar). Não dá sem modelo novo: sotaque/fonemas,
ritmo das sílabas dentro da frase, respiração.

Uso:
  venv_vozes:  clone2.py calibrar                 -> amostras_voz\\clone2\\calibracao.json
               clone2.py perfil <voz|todos>       -> models\\rvc\\vozes\\<voz>\\perfil_v2.json
               clone2.py humano <voz|todos>       -> models\\rvc\\vozes\\<voz>\\humano\\ (respirações reais, sala.wav)
                                                     + perfil_v2 aplicar[base]["final_st"] (fim de frase)
  venv recapd: clone2.py linguagem <voz|todos>    -> models\\rvc\\vozes\\<voz>\\linguagem_v2.json
               clone2.py amostra <voz>            -> amostras_voz\\clone2\\comparar_v1_v2\\<voz>_0_original/_1_v1/_2_v2.mp3
Quem usa: recapd bin\\anime_tts.preparar_clone e anime_script (VOZ_CLONADA_VERSAO=2).
"""
import asyncio
import json
import os
import re
import shutil
import statistics as st
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
VOZES = RAIZ / "models" / "rvc" / "vozes"
DATASET = RAIZ / "amostras_voz" / "dataset_narradores"
AMOSTRAS_V1 = RAIZ / "amostras_voz" / "2026-10-18_vozes_clonadas"
REF = RAIZ / "referencias_narradores"
SAIDA = RAIZ / "amostras_voz" / "clone2"
CALIB = SAIDA / "calibracao.json"
RITMO = SAIDA / "ritmo_canais.json"
FFMPEG = str(RAIZ / "bin" / "ffmpeg.exe")
FRANCISCA = "pt-BR-FranciscaNeural"
BANDAS = [63, 125, 250, 500, 1000, 2000, 4000, 8000, 12000]
# história fixa das amostras (v1 lê assim; o v2 reescreve no jeito do narrador)
HISTORIA = ["Durante anos, ele foi chamado de lixo pela própria família.",
            "Ninguém na academia acreditava que aquele garoto magrelo ia chegar a algum lugar.",
            "Mas numa noite chuvosa, voltando do treino, ele encontrou um velho caído no beco.",
            "O velho segurou o braço dele e sussurrou que a vida dele ia mudar a partir daquele momento.",
            "No dia seguinte, quando abriu os olhos, uma janela azul apareceu bem na frente dele.",
            "Sistema ativado. Missão: derrotar o valentão da escola em sete dias.",
            "Ele riu, achando que era sonho, até sentir a força correndo pelo corpo inteiro.",
            "E foi exatamente ali que tudo começou a mudar!"]


def parceiros():
    """[(voz, canal)] na ordem do voz_clonada.PARCEIROS (canal = pasta em referencias_narradores = handle sem @)."""
    texto = (RAIZ / "bin" / "voz_clonada.py").read_text(encoding="utf-8")
    bloco = texto[texto.find("PARCEIROS = ["):texto.find("BASES = [")]
    return re.findall(r'\("(\w+)", "@([^"]+)"\)', bloco)


def _mediana(v):
    v = [x for x in v if x is not None]
    return round(st.median(v), 3) if v else None


def _lim(x, a, b):
    return max(a, min(b, x))


# ─── ritmo (legendas) ─────────────────────────────────────────────────────────
def _ritmo_palavras(pal):
    """Do [(t, palavra)]: velocidade dentro da frase (IOI <= 0,45 s), pausas (> 0,45 s) e variação em janelas de 10 s."""
    ts = [t for t, _ in pal]
    ioi = [b - a for a, b in zip(ts, ts[1:]) if 0 < b - a <= 4.0]
    curtos = [x for x in ioi if x <= 0.45]
    pausas = sorted(x for x in ioi if x > 0.45)
    if len(curtos) < 20:
        return None
    fala_min = sum(ioi) / 60
    janelas, ini, n = [], ts[0], 0
    for a, b in zip(ts, ts[1:]):
        if b - a > 4.0:
            ini, n = b, 0
            continue
        n += 1
        if b - ini >= 10:
            janelas.append(n * 60 / (b - ini))
            ini, n = b, 0
    return {"art_ppm": 60 / st.mean(curtos), "ppm": len(ioi) / fala_min,
            "ppm_cv": st.pstdev(janelas) / st.mean(janelas) if len(janelas) > 3 else None,
            "pausa_mediana_s": st.median(pausas) if pausas else None,
            "pausa_p90_s": pausas[int(len(pausas) * 0.9)] if len(pausas) > 5 else None,
            "pausas_min": len(pausas) / fala_min}


def ritmo_canais():
    """Ritmo de todos os canais com legenda (cache em ritmo_canais.json)."""
    if RITMO.exists():
        return json.loads(RITMO.read_text(encoding="utf-8"))
    sys.path.insert(0, r"D:\hipercool-videos\bin")
    from medir_narradores import palavras_vtt
    out = {}
    for _voz, canal in parceiros():
        pasta = REF / canal
        if not pasta.is_dir():
            continue
        vistos, ms = set(), []
        for v in sorted(pasta.glob("*.vtt")):
            if v.name[:11] in vistos or len(vistos) >= 40:
                continue
            vistos.add(v.name[:11])
            m = _ritmo_palavras(palavras_vtt(v))
            if m:
                ms.append(m)
        if ms:
            out[canal] = {"videos": len(ms), **{k: _mediana([m[k] for m in ms]) for k in ms[0]}}
            print(f"ritmo {canal}: {out[canal]}", flush=True)
    SAIDA.mkdir(parents=True, exist_ok=True)
    RITMO.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


# ─── acústica ─────────────────────────────────────────────────────────────────
def _entonacao_volume(wavs):
    """Faixa de entonação (semitons) dentro da frase e entre frases + variação do volume (dB) entre frases."""
    import librosa
    import numpy as np
    intra, medianas, vols = [], [], []
    for w in wavs:
        y, sr = librosa.load(str(w), sr=16000, mono=True, duration=8)
        if len(y) < sr:
            continue
        f0, voz, _ = librosa.pyin(y, fmin=60, fmax=450, sr=sr, frame_length=1024, hop_length=320)
        f = f0[voz & ~np.isnan(f0)]
        if len(f) < 20:
            continue
        intra.append(float(np.std(12 * np.log2(f / np.median(f)))))
        medianas.append(float(np.median(f)))
        rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=320)[0]
        db = 20 * np.log10(rms + 1e-9)
        vols.append(float(np.mean(db[db > db.max() - 30])))
    inter = float(np.std(12 * np.log2(np.array(medianas) / np.median(medianas)))) if len(medianas) > 3 else None
    return {"intra_st": _mediana(intra), "inter_st": round(inter, 3) if inter else None,
            "volume_std_db": round(float(np.std(vols)), 2) if len(vols) > 3 else None, "frases": len(intra)}


def _ltas(path):
    """Espectro médio da fala (dB) por banda de oitava, a 32 kHz (taxa do modelo RVC)."""
    import librosa
    import numpy as np
    from scipy import signal
    y, sr = librosa.load(str(path), sr=32000, mono=True, duration=240)
    trechos = librosa.effects.split(y, top_db=35)
    y = np.concatenate([y[a:b] for a, b in trechos]) if len(trechos) else y
    f, p = signal.welch(y, sr, nperseg=4096)
    out = []
    for c in BANDAS:
        m = (f >= c / 2 ** 0.5) & (f < min(c * 2 ** 0.5, sr / 2 - 1))
        out.append(10 * np.log10(p[m].mean() + 1e-12))
    return np.array(out)


def _eq(real, clone):
    """[[Hz, dB]] que leva o espectro do clone v1 pro da voz real (normalizado no miolo 250–4k, ±6 dB, grave até +3)."""
    d = real - clone
    d = d - d[2:7].mean()
    return [[c, round(float(_lim(g, -6, 3 if c < 100 else 6)), 1)] for c, g in zip(BANDAS, d)]


def _sintetizar_frases(base, pasta):
    """As frases de calibração (falas reais de 6 narradores) com a voz base, 1 wav por frase."""
    sys.path.insert(0, str(RAIZ / "bin"))
    import voz_clonada
    pasta.mkdir(parents=True, exist_ok=True)
    wavs = []
    for i, texto in enumerate(_frases_calibracao()):
        w = pasta / f"{i:02d}.wav"
        if not w.exists():
            voz_clonada._base_tts(base, texto, w)
        wavs.append(w)
    return wavs


def _frases_calibracao():
    frases = []
    for voz, _c in parceiros()[:6]:
        linhas = (DATASET / voz / "metadata.csv").read_text(encoding="utf-8").splitlines()
        frases += [linhas[k].split("|")[1] for k in (3, 10) if len(linhas) > k]
    return frases


async def _edge_palavras(texto, mp3):
    import edge_tts
    pal = []
    with open(mp3, "wb") as f:
        async for ch in edge_tts.Communicate(texto, FRANCISCA, boundary="WordBoundary").stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                pal.append((ch["offset"] / 1e7, ch["text"]))
    return pal


def _fala_s(path):
    import librosa
    y, sr = librosa.load(str(path), sr=16000, mono=True)
    return sum(b - a for a, b in librosa.effects.split(y, top_db=35)) / sr


def calibrar():
    """Mede as vozes base do mesmo jeito que os narradores (velocidade dentro da frase, entonação, volume)."""
    pasta = SAIDA / "_calib"
    pasta.mkdir(parents=True, exist_ok=True)
    texto = " ".join(_frases_calibracao())
    mp3 = pasta / "francisca_tudo.mp3"
    pal = asyncio.run(_edge_palavras(texto, mp3))
    rf = _ritmo_palavras(pal)
    sys.path.insert(0, str(RAIZ / "bin"))
    import voz_clonada
    kwav = pasta / "kokoro_tudo.wav"
    voz_clonada._base_tts("kokoro:pm_alex", texto, kwav)
    art_k = rf["art_ppm"] * _fala_s(mp3) / _fala_s(kwav)  # mesmo texto: mais tempo de fala = mais devagar
    cal = {"gerado": f"{datetime.now():%d/%m %H:%M}",
           "francisca": {"art_ppm": round(rf["art_ppm"], 1), **_entonacao_volume(
               _sintetizar_frases(f"edge:{FRANCISCA}", pasta / "francisca"))},
           "kokoro": {"art_ppm": round(art_k, 1), **_entonacao_volume(
               _sintetizar_frases("kokoro:pm_alex", pasta / "kokoro"))}}
    CALIB.write_text(json.dumps(cal, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(cal, ensure_ascii=False), flush=True)
    return cal


def perfil(voz, canal, ritmos, cal):
    """perfil_v2.json: o que foi medido + "aplicar" (o que o anime_tts usa)."""
    linhas = [l.split("|")[0] for l in (DATASET / voz / "metadata.csv").read_text(encoding="utf-8").splitlines() if l]
    passo = max(1, len(linhas) // 24)
    wavs = [DATASET / voz / "wavs" / f"{i}.wav" for i in linhas[::passo][:24]]
    ac = _entonacao_volume([w for w in wavs if w.exists()])
    rit = ritmos.get(canal)
    todos = list(ritmos.values())
    ref = {k: _mediana([r.get(k) for r in todos]) for k in ("art_ppm", "ppm_cv", "pausa_mediana_s", "pausa_p90_s")}
    r = rit or ref  # sem legenda (PieRecaps): ritmo médio dos outros
    # volume: referência = mediana dos narradores já medidos (perfis gravados) ou o próprio
    vols = [json.loads(p.read_text(encoding="utf-8"))["medido"]["volume_std_db"] for p in VOZES.glob("*/perfil_v2.json")]
    ref_vol = _mediana([v for v in vols if v] + [ac["volume_std_db"]])
    aplicar = {"curva_rate": round(_lim((r["ppm_cv"] or ref["ppm_cv"]) / ref["ppm_cv"], 0.6, 1.8), 2),
               "curva_ganho": round(_lim(ac["volume_std_db"] / ref_vol, 0.6, 1.6), 2) if ac["volume_std_db"] else 1.0,
               "cauda": round(_lim(0.25 * r["pausa_mediana_s"] / ref["pausa_mediana_s"], 0.12, 0.6), 2),
               "cauda_impacto": round(_lim(0.6 * r["pausa_p90_s"] / ref["pausa_p90_s"], 0.3, 1.2), 2)}
    inter_base = st.mean([cal[b]["inter_st"] for b in ("francisca", "kokoro")])
    aplicar["tom_extra_st"] = round(_lim(max(0.0, (ac["inter_st"] or 0) ** 2 - inter_base ** 2) ** 0.5, 0, 2), 2)
    real = _ltas(DATASET / voz / "voz.wav")
    for base, amostra in (("francisca", "2_edge_francisca"), ("kokoro", "1_kokoro")):
        b = {"f0_escala": round(_lim(ac["intra_st"] / cal[base]["intra_st"], 0.6, 1.8), 2)}
        mp3 = AMOSTRAS_V1 / f"{voz}_{amostra}.mp3"
        b["eq"] = _eq(real, _ltas(mp3)) if mp3.exists() else []
        if base == "francisca":
            b["rate"] = int(round(_lim((r["art_ppm"] / cal[base]["art_ppm"] - 1) * 100, -30, 50)))
        else:
            b["velocidade"] = round(_lim(r["art_ppm"] / cal[base]["art_ppm"], 0.8, 1.5), 2)
        aplicar[base] = b
    out = {"versao": 2, "voz": voz, "canal": canal, "gerado": f"{datetime.now():%d/%m %H:%M}",
           "medido": {"ritmo": rit, "ritmo_sem_legenda": rit is None, **ac}, "referencia": ref, "aplicar": aplicar}
    (VOZES / voz / "perfil_v2.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"perfil {voz}: {json.dumps(aplicar, ensure_ascii=False)}", flush=True)
    return out


# ─── humano (20/10): respiração real, fundo da sala e fim de frase do narrador ────────────────────
HUMANO = SAIDA / "humano"  # prévias pro dono ouvir (<voz>_respiracoes.wav)
SR_H, HOP_H = 16000, 160  # quadros de 10 ms


def _lufs(path):
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.findall(r"I:\s*(-?[\d.]+) LUFS", r.stderr or "")
    return float(m[-1]) if m else None


_RMVPE = []


def _tom(y):
    """Tom por quadro de 10 ms (0 = sem voz) com o RMVPE do Applio — o mesmo que o clone usa. O pyin (piso 60 Hz)
    lia lixo no fim grave das frases (teste 20/10: -8 st pedidos apareciam como 0)."""
    if not _RMVPE:
        applio = RAIZ / "tools" / "applio"
        os.environ.setdefault("APPLIO_CONFIG_DIR", str(applio / "config_local"))
        os.chdir(applio)
        sys.path.insert(0, str(applio))
        from rvc.lib.predictors.f0 import RMVPE
        _RMVPE.append(RMVPE(device="cpu", sample_rate=SR_H, hop_size=HOP_H))
    return _RMVPE[0].get_f0(y, filter_radius=0.03)


FINAL_MIN_TRECHOS = 15  # menos que isso (narrador que corta as pausas na edição) = não aplica


def _final_st(y, sr):
    """Quanto o tom vai no fim de cada trecho falado (antes de pausa >= 0,12 s): mediana(último 20% com voz) -
    mediana(resto), em semitons. Mediana dos trechos."""
    import numpy as np
    f0 = _tom(y)
    deltas, trecho, mudo = [], [], 0
    for f in f0:
        if f > 0:
            trecho.append(f)
            mudo = 0
            continue
        mudo += 1
        if mudo == 12 and len(trecho) >= 50:
            st_ = 12 * np.log2(np.array(trecho) / np.median(trecho))
            k = int(len(st_) * 0.8)
            deltas.append(float(np.median(st_[k:]) - np.median(st_[:k])))
        if mudo >= 12:
            trecho = []
    if len(trecho) >= 50:
        st_ = 12 * np.log2(np.array(trecho) / np.median(trecho))
        k = int(len(st_) * 0.8)
        deltas.append(float(np.median(st_[k:]) - np.median(st_[:k])))
    return (round(st.median(deltas), 2) if deltas else None), len(deltas)


def _final_bases():
    """Fim de frase da Francisca e do Kokoro, nas frases de calibração (guardado no calibracao.json)."""
    import librosa
    import numpy as np
    cal = json.loads(CALIB.read_text(encoding="utf-8"))
    for base in ("francisca", "kokoro"):
        cal[base].pop("final_st", None)  # medida antiga com pyin
        if "final_st_rmvpe" in cal[base]:
            continue
        ys = [librosa.load(str(w), sr=SR_H, mono=True)[0] for w in sorted((SAIDA / "_calib" / base).glob("*.wav"))]
        pausa = np.zeros(int(0.4 * SR_H), dtype=np.float32)
        cal[base]["final_st_rmvpe"] = _final_st(np.concatenate([np.concatenate([y, pausa]) for y in ys]), SR_H)[0]
        CALIB.write_text(json.dumps(cal, ensure_ascii=False, indent=1), encoding="utf-8")
    return cal


def _runs(mask, tolera=2):
    """[(ini, fim)] dos trechos True (buracos de até `tolera` quadros não quebram)."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if not mask[i]:
            i += 1
            continue
        j = i
        while j < n and (mask[j] or mask[j + 1:j + 1 + tolera].any()):
            j += 1
        out.append((i, j))
        i = j
    return out


def humano(voz):
    """models\\rvc\\vozes\\<voz>\\humano\\: respiracao_NN.wav (respirações reais, recortadas do voz.wav) e sala.wav
    (fundo da sala/microfone), já no volume de uma fala a -20 LUFS (o nível que o pos_processar deixa a frase);
    humano.json; perfil_v2.json aplicar[base]["final_st"] = fim de frase dele - o da base."""
    import librosa
    import numpy as np
    import soundfile as sf
    src = DATASET / voz / "voz.wav"
    pasta = VOZES / voz / "humano"
    pasta.mkdir(parents=True, exist_ok=True)
    ganho = -20.0 - (_lufs(src) or -20.0)
    bruto, sr0 = sf.read(str(src), dtype="float32", always_2d=True)
    bruto = bruto.mean(axis=1)
    y = librosa.resample(bruto, orig_sr=sr0, target_sr=SR_H)
    db = 20 * np.log10(librosa.feature.rms(y=y, frame_length=400, hop_length=HOP_H)[0] + 1e-10)
    cen = librosa.feature.spectral_centroid(y=y, sr=SR_H, n_fft=512, hop_length=HOP_H)[0]
    n = min(len(db), len(cen))
    db, cen = db[:n], cen[:n]
    piso = float(np.percentile(db, 3))
    fala = float(np.percentile(db[db > piso + 20], 60)) if (db > piso + 20).any() else float(np.median(db))
    q = HOP_H / SR_H
    # respirações: baixa (10+ dB abaixo da fala), acima do fundo, ruído no meio do espectro, 0,15–0,6 s, sem voz
    # (pyin só nas candidatas) e com fala logo depois (é a inspiração antes de falar)
    cand = (db > piso + 8) & (db < fala - 10) & (cen > 300) & (cen < 3200)
    achadas = []
    for a, b in _runs(cand):
        d = (b - a) * q
        if not 0.15 <= d <= 0.6 or not (db[b:b + 20] > fala - 6).any():
            continue
        if (_tom(y[max(0, a - 10) * HOP_H:(b + 10) * HOP_H])[10:-10] > 0).mean() > 0.2:
            continue
        achadas.append((a * q, d, float(np.median(db[a:b])) - fala))
    achadas.sort(key=lambda r: abs(r[1] - 0.3))
    for velho in pasta.glob("respiracao_*.wav"):
        velho.unlink()
    resp, previa = [], []
    for k, (t, d, rel) in enumerate(achadas[:16]):
        i0, i1 = int(max(0, t - 0.02) * sr0), int((t + d + 0.03) * sr0)
        trecho = bruto[i0:i1] * 10 ** (ganho / 20)
        f_in, f_out = int(0.015 * sr0), int(0.04 * sr0)
        trecho[:f_in] *= np.linspace(0, 1, f_in)
        trecho[-f_out:] *= np.linspace(1, 0, f_out)
        arq = pasta / f"respiracao_{k:02d}.wav"
        sf.write(str(arq), trecho, sr0, subtype="PCM_16")
        resp.append({"arq": arq.name, "dur": round(d + 0.05, 3), "rel_db": round(rel, 1), "t": round(t, 2)})
        previa += [trecho, np.zeros(int(0.7 * sr0), dtype=np.float32)]
    # fundo da sala: os quadros mais quietos (sem fala), emendados até 3 s
    sala, total = [], 0
    for a, b in _runs(db <= piso + 3, tolera=0):
        if b - a < 5:
            continue
        pedaco = bruto[int(a * q * sr0):int(b * q * sr0)].copy()
        fd = min(len(pedaco) // 4, int(0.005 * sr0))
        if fd:
            pedaco[:fd] *= np.linspace(0, 1, fd)
            pedaco[-fd:] *= np.linspace(1, 0, fd)
        sala.append(pedaco)
        total += len(pedaco)
        if total >= 3 * sr0:
            break
    sala_db = None
    (pasta / "sala.wav").unlink(missing_ok=True)
    if total >= 0.5 * sr0:
        s = np.concatenate(sala) * 10 ** (ganho / 20)
        sala_db = round(float(20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-10)), 1)
        if sala_db > -85:
            sf.write(str(pasta / "sala.wav"), s, sr0, subtype="PCM_16")
        else:
            sala_db = None
    final, trechos = _final_st(y, SR_H)
    if trechos < FINAL_MIN_TRECHOS:
        final = None
    info = {"gerado": f"{datetime.now():%d/%m %H:%M}", "ganho_db": round(ganho, 1), "fala_db": round(fala, 1),
            "piso_db": round(piso, 1), "respiracoes": resp, "sala_db": sala_db, "final_st": final,
            "final_trechos": trechos}
    (pasta / "humano.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    if previa:
        HUMANO.mkdir(parents=True, exist_ok=True)
        sf.write(str(HUMANO / f"{voz}_respiracoes.wav"), np.concatenate(previa), sr0, subtype="PCM_16")
    arq_perfil = VOZES / voz / "perfil_v2.json"
    if arq_perfil.exists():
        cal = _final_bases()
        perf = json.loads(arq_perfil.read_text(encoding="utf-8"))
        perf["medido"]["final_st"] = final
        for base in ("francisca", "kokoro"):
            if base not in perf["aplicar"]:
                continue
            perf["aplicar"][base].pop("final_st", None)
            if final is not None and cal[base].get("final_st_rmvpe") is not None:
                perf["aplicar"][base]["final_st"] = round(_lim(final - cal[base]["final_st_rmvpe"], -3, 2), 2)
        arq_perfil.write_text(json.dumps(perf, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"humano {voz}: {len(resp)} respirações, sala {sala_db} dB, fim de frase {final} st ({trechos} trechos)",
          flush=True)
    return info


# ─── linguagem (LLM; roda no venv do recapd) ──────────────────────────────────
PROMPT_LINGUAGEM = """Monte o GUIA DE ESTILO de um narrador brasileiro de recap de manhwa/anime, para outro roteirista
escrever NO JEITO DELE (copiando o jeito, nunca o texto). Use SÓ o material abaixo: estatísticas de milhões de palavras
das legendas dele e trechos reais transcritos da fala dele.

Responda SÓ um JSON com estas chaves:
"<SEGREDO_REMOVIDO>" (2 frases: como ele narra), "tom" (ex.: debochado, empolgado, sério, didático),
"abertura" (como ele começa a história num vídeo curto: 1 frase-molde SEM nome de canal; "" se não tem padrão),
"conectores" (até 6 mais típicos DELE), "fala_com_publico" (até 5), "interjeicoes" (até 6),
"girias_regionais" (gírias, regionalismos e palavrões leves que ele usa DE VERDADE no material; [] se não usa),
"contracoes" (formas faladas que ele usa: "tá", "pra", "cê", "né"...), "apelidos_protagonista" (até 5),
"bordoes" (até 6 expressões que ele repete), "tiradas" (1 frase: como ele comenta/zoa a cena),
"frases_reais" (5 frases curtas DELE copiadas do material que mostram bem o jeito),
"tamanho_frase" ("curtas" | "médias" | "longas"), "pessoa" (ex.: "3ª pessoa no presente, fala com o público"),
"evitar" (até 5 coisas que ele NÃO faz).
Sem CTA (inscreva-se, like, sininho), sem nome de canal, sem palavras de violência explícita.

ESTATÍSTICAS DAS LEGENDAS:
{stats}

ANÁLISE ANTERIOR:
{analise}

FALA REAL TRANSCRITA:
{fala}
"""


# palavrão pesado e piada de orientação sexual derrubam o anúncio no YouTube: saem do guia (zoeira leve fica)
PESADO = re.compile(r"\b(caralho|porra|putaria|puta|put[oa]s|foda|fod[ea]\w*|merda|buceta|cu|viad\w*|veado\w*|"
                    r"bosta|cacete|piroca|rola|gay)\b", re.I)


def limpar_guia(guia):
    for k, v in guia.items():
        if isinstance(v, list):
            guia[k] = [x for x in v if not PESADO.search(str(x))]
        elif isinstance(v, str) and k in ("abertura",) and PESADO.search(v):
            guia[k] = ""
    return guia


def linguagem(voz, canal):
    sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
    import claude_client
    stats = ""
    arq = REF / "_medidas" / f"{canal}_linguagem.txt"
    if arq.exists():
        stats = arq.read_text(encoding="utf-8").split("### Contexto de palavras proibidas")[0][:9000]
    analise = ""
    md = (REF / "ANALISE_LINGUAGEM.md").read_text(encoding="utf-8")
    m = re.search(rf"^#{{2,3}} [^\n]*{re.escape(canal)}[^\n]*\n(.*?)(?=^#{{2,3}} )", md, re.M | re.S | re.I)
    if m:
        analise = m.group(0)[:4000]
    fala = "\n".join(l.split("|")[1] for l in (DATASET / voz / "metadata.csv").read_text(encoding="utf-8").splitlines()[:45]
                     if "|" in l)
    resp = claude_client.generate_text(PROMPT_LINGUAGEM.format(stats=stats or "(sem)", analise=analise or "(sem)",
                                                               fala=fala), max_tokens=2000, temperature=0.3, timeout=240)
    j = re.search(r"\{.*\}", resp or "", re.S)
    guia = limpar_guia(json.loads(j.group(0)))
    guia.update(voz=voz, canal=canal, gerado=f"{datetime.now():%d/%m %H:%M}")
    (VOZES / voz / "linguagem_v2.json").write_text(json.dumps(guia, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"linguagem {voz}: {guia.get('resumo', '')[:160]}", flush=True)


# ─── amostras comparativas (venv do recapd: usa o anime_tts de verdade) ──────
def _juntar(pasta, n, mp3):
    lista = pasta / "lista.txt"
    lista.write_text("".join(f"file 'audio_{i}.wav'\n" for i in range(n) if (pasta / f"audio_{i}.wav").exists()),
                     encoding="ascii")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-ac", "1",
                    "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3)], check=True)


COMPARAR = SAIDA / "comparar_v1_v2"  # só as amostras pro dono ouvir


def amostra(voz):
    """<voz>_0_original (voz real) | _1_v1 (história fixa, clone v1 misto) | _2_v2 (a mesma história reescrita no
    jeito dele + ritmo/pausa/entonação/volume/EQ dele, misto) + _2_v2_texto.txt."""
    import os
    sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
    os.environ.update(VOZ_CLONADA=voz, VOZ_CLONADA_BASE="misto", ROTEIRO_CACHE="0", PARCEIRO_TIPO="manhwa")
    import anime_tts
    import narracao_curva
    tmp = SAIDA / "_tmp" / voz
    shutil.rmtree(tmp, ignore_errors=True)
    COMPARAR.mkdir(parents=True, exist_ok=True)
    # gera _0_original.mp3 se não existir (pode ter sido apagado)
    orig = AMOSTRAS_V1 / f"{voz}_0_original.mp3"
    if not orig.exists():
        from voz_clonada import _mp3
        _mp3(DATASET / voz / "voz.wav", orig, dur=15)
    shutil.copy2(orig, COMPARAR / f"{voz}_0_original.mp3")
    os.environ.pop("VOZ_CLONADA_VERSAO", None)
    imp = narracao_curva._heuristica(HISTORIA, narracao_curva._quantos(len(HISTORIA)))
    anime_tts.preparar_clone(HISTORIA, tmp / "v1", imp)
    _juntar(tmp / "v1", len(HISTORIA), COMPARAR / f"{voz}_1_v1.mp3")
    os.environ["VOZ_CLONADA_VERSAO"] = "2"
    import anime_script
    linhas = anime_script.rewrite("\n".join(HISTORIA), target_lines=len(HISTORIA)) or HISTORIA
    (COMPARAR / f"{voz}_2_v2_texto.txt").write_text("\n".join(linhas), encoding="utf-8")
    imp = narracao_curva._heuristica(linhas, narracao_curva._quantos(len(linhas)))
    anime_tts.preparar_clone(linhas, tmp / "v2", imp)
    _juntar(tmp / "v2", len(linhas), COMPARAR / f"{voz}_2_v2.mp3")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"amostras {voz}: {COMPARAR}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd, alvo = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "todos")
    lista = [(v, c) for v, c in parceiros() if alvo in ("todos", v) and (VOZES / v / f"{v}.pth").exists()]
    if cmd == "calibrar":
        calibrar()
    elif cmd == "perfil":
        cal = json.loads(CALIB.read_text(encoding="utf-8")) if CALIB.exists() else calibrar()
        rit = ritmo_canais()
        for v, c in lista:
            perfil(v, c, rit, cal)
    elif cmd == "linguagem":
        for v, c in lista:
            try:
                linguagem(v, c)
            except Exception as e:  # noqa: BLE001
                print(f"linguagem {v} FALHOU: {e}", flush=True)
    elif cmd == "amostra":
        amostra(alvo)
    elif cmd == "humano":  # venv_vozes, prioridade mínima (não atrasa o clone da produção)
        import psutil
        psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
        for v, _c in lista:
            try:
                humano(v)
            except Exception as e:  # noqa: BLE001
                print(f"humano {v} FALHOU: {type(e).__name__}: {e}", flush=True)
    elif cmd == "comparar":  # venv recapd: perfis que faltam + amostras de todos (porao e kkvirjao primeiro)
        if any(not (VOZES / v / "perfil_v2.json").exists() for v, _c in lista):
            subprocess.run([str(RAIZ / "python" / "venv_vozes" / "Scripts" / "python.exe"), "-u", __file__, "perfil",
                            alvo], check=True)
        feitos = 0
        for v, _c in sorted(lista, key=lambda vc: (vc[0] != "porao", vc[0] != "kkvirjao")):
            if (COMPARAR / f"{v}_2_v2.mp3").exists():
                continue
            try:
                amostra(v)
            except Exception as e:  # noqa: BLE001
                print(f"amostra {v} FALHOU: {type(e).__name__}: {e}", flush=True)
                continue
            feitos += 1
            if feitos == 1:  # dono: "abre só elas numa pasta separada"
                subprocess.Popen(["explorer", str(COMPARAR)])
    else:
        sys.exit(__doc__)
