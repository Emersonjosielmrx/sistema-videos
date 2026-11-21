"""xtts_nuvem.py — narração pelo XTTS v2 (Coqui, fork idiap `coqui-tts`) na GPU do Kaggle (ou CPU), num processo só.

Dona 21/11 (teste do gol, comparação de motores): "o XTTS é muito mais natural que o Kitten e erra muito menos que o
Fish" — versões aprovadas: xtts2_4 e xtts2_6 ("iguais ao meu ouvido"; a 5 foi a inferior). Este é o gerador; o
pós (microcortes, velocidade por frase, cadência, gol, S do respeito) fica no anime_tts._narrar_xtts.

    python xtts_nuvem.py lote <lista.json>
lista = [{"texto", "saida", "refs": [wav...], "temp", "n": tentativas, "seed"}]; grava wav 24 kHz mono por item.
O que corrige (achado nos testes de 20-21/11):
  - fala "ponto": tira ponto final/reticências/dois-pontos/aspas e gera SENTENÇA POR SENTENÇA (texto longo também o
    fazia repetir palavra, "aulas, aulas"), juntando com 0,18 s;
  - melhor de N: N tentativas e fica com a de ritmo (letras/s) e tom mais perto do normal das frases já aceitas.
"""
import json, os, re, sys, time
from pathlib import Path


def limpa(t):
    t = t.replace("…", ",").replace("...", ",").replace(":", ",").replace(";", ",")
    t = re.sub(r"[\"“”‘’]", "", t)
    t = re.sub(r",\s*,", ",", t)
    return t.strip(" ,")


def _f0(a, sr):
    import numpy as np
    x = a[:: max(1, sr // 16000)].astype(np.float32)
    out = []
    for i in range(0, len(x) - 1024, 320):
        fr = x[i:i + 1024] * np.hanning(1024)
        if np.sqrt((fr ** 2).mean()) < 0.02:
            continue
        c = np.abs(np.fft.irfft(np.log(np.abs(np.fft.rfft(fr, 4096)) + 1e-9)))
        out.append(16000 / (40 + np.argmax(c[40:228])))
    return float(np.median(out)) if len(out) >= 5 else 0.0


def lote(lista_json):
    import numpy as np, soundfile as sf, torch
    os.environ["COQUI_TOS_AGREED"] = "1"
    from TTS.api import TTS
    itens = json.loads(Path(lista_json).read_text(encoding="utf-8"))
    t = time.time()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(dev)
    m = tts.synthesizer.tts_model
    print(f"XTTS carga {time.time() - t:.1f}s ({dev})", flush=True)
    lat, f0_ok, cps_ok, ok = {}, [], [], 0
    for it in itens:
        if Path(it["saida"]).exists():
            ok += 1
            continue
        t0 = time.time()
        try:
            refs = tuple(it["refs"])
            if refs not in lat:
                lat[refs] = m.get_conditioning_latents(audio_path=list(refs))
            gpt, spk = lat[refs]
            partes = [re.sub(r"\.$", "", x).strip() for x in re.split(r"(?<=[.!?])\s+", limpa(it["texto"]))
                      if x.strip()]
            if it.get("frase_inteira"):  # versão 4: a frase toda de uma vez (só sem ponto)
                partes = [re.sub(r"\.(?=\s|$)", ",", limpa(it["texto"])).strip(" ,")]
            tent = []
            for k in range(int(it.get("n", 1))):
                torch.manual_seed(int(it.get("seed", 42)) + k)
                audio = []
                for j, frase in enumerate(partes):
                    o = m.inference(frase, "pt", gpt, spk, temperature=float(it.get("temp", 0.6)), top_p=0.8,
                                    top_k=40, repetition_penalty=10.0, length_penalty=1.0, speed=1.0,
                                    enable_text_splitting=False)
                    audio.append(np.asarray(o["wav"], dtype=np.float32))
                    if j < len(partes) - 1:
                        audio.append(np.zeros(int(24000 * 0.18), np.float32))
                a = np.concatenate(audio)
                tent.append((a, _f0(a, 24000), len(it["texto"]) / max(len(a) / 24000, 0.1)))
            if len(tent) > 1:
                alvo = float(np.median(f0_ok)) if len(f0_ok) >= 3 else float(np.median([x[1] for x in tent if x[1]] or [0]))
                calvo = float(np.median(cps_ok)) if len(cps_ok) >= 3 else float(np.median([x[2] for x in tent]))

                def pena(x):
                    st = abs(12 * np.log2(x[1] / alvo)) if x[1] and alvo else 6.0
                    fora = abs(x[2] / calvo - 1) if calvo else 0
                    return st + (8 * (fora - 0.3) if fora > 0.3 else 0)
                melhor = min(tent, key=pena)
            else:
                melhor = tent[0]
            if melhor[1]:
                f0_ok.append(melhor[1])
            cps_ok.append(melhor[2])
            tmp = it["saida"] + ".tmp.wav"
            sf.write(tmp, melhor[0], 24000)
            os.replace(tmp, it["saida"])
            ok += 1
            print(f"XTTS ok {time.time() - t0:.1f}s {it['saida']}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"XTTS erro {type(e).__name__}: {str(e)[:200]} {it['saida']}", flush=True)
    print(f"XTTS fim {ok}/{len(itens)}", flush=True)
    return 0 if ok == len(itens) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["lote"]:
        sys.exit(lote(sys.argv[2]))
    print(__doc__)
    sys.exit(1)
