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


_WM = []


def _whisper():
    if not _WM:
        try:
            from faster_whisper import WhisperModel
            try:
                _WM.append(WhisperModel("small", device="cuda", compute_type="float16"))
            except Exception:  # noqa: BLE001
                _WM.append(WhisperModel("small", device="cpu", compute_type="int8"))
        except Exception:  # noqa: BLE001
            _WM.append(None)
    return _WM[0]


def _wer(texto, a):
    import numpy as np, unicodedata
    def norm(t):
        t = unicodedata.normalize("NFKD", t.lower()); t = "".join(c for c in t if not unicodedata.combining(c))
        return re.findall(r"[a-z0-9]+", t)
    try:
        x = a[::3].astype(np.float32)  # 24 kHz -> 8 kHz? não: Whisper quer 16 kHz
        import scipy.signal as ss
        x = ss.resample_poly(a.astype(np.float32), 2, 3)
        segs, _ = _whisper().transcribe(x, language="pt")
        h = norm(" ".join(sg.text for sg in segs)); r = norm(texto)
        d = np.zeros((len(r) + 1, len(h) + 1), int); d[:, 0] = range(len(r) + 1); d[0, :] = range(len(h) + 1)
        for i in range(1, len(r) + 1):
            for j in range(1, len(h) + 1):
                d[i, j] = min(d[i-1, j] + 1, d[i, j-1] + 1, d[i-1, j-1] + (r[i-1] != h[j-1]))
        return d[len(r), len(h)] / max(1, len(r))
    except Exception:  # noqa: BLE001
        return 0.0


def lote(lista_json):
    import numpy as np, soundfile as sf, torch
    os.environ["COQUI_TOS_AGREED"] = "1"
    from TTS.api import TTS
    itens = json.loads(Path(lista_json).read_text(encoding="utf-8"))
    t = time.time()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(dev)
    m = tts.synthesizer.tts_model
    # 24/11 noite: XTTS_CKPT=<pasta com model.pth do fine-tune do narrador> troca só os pesos do GPT/decoder pelos do
    # fine-tune (mesmo config/vocab do base). Sem a variável = modelo base de sempre. Falhou = segue no base.
    ck = os.environ.get("XTTS_CKPT")
    if ck and (Path(ck) / "model.pth").exists():
        try:
            sd = torch.load(str(Path(ck) / "model.pth"), map_location=dev, weights_only=False)
            sd = sd.get("model", sd)
            # 25/11: o checkpoint do treino (GPTTrainer) guarda as chaves com o prefixo "xtts." e leva o dvae/mel junto;
            # sem tirar o prefixo o strict=False não carregava NADA (silencioso).
            if hasattr(m, "get_compatible_checkpoint_state_dict"):
                sd = m.get_compatible_checkpoint_state_dict(str(Path(ck) / "model.pth"))
            else:
                sd = {k[5:] if k.startswith("xtts.") else k: v for k, v in sd.items()
                      if not k.startswith(("dvae.", "torch_mel_spectrogram", "xtts.dvae.", "xtts.torch_mel_spectrogram"))}
            meu = set(m.state_dict())
            casou = len(meu & set(sd))
            faltou, sobrou = m.load_state_dict(sd, strict=False)
            print(f"XTTS_CKPT {ck} carregado: {casou}/{len(meu)} camadas do modelo trocadas "
                  f"(faltou {len(faltou)}, sobrou {len(sobrou)})", flush=True)
            if casou < len(meu) * 0.5:
                raise RuntimeError(f"só {casou} camadas casaram — checkpoint incompatível")
        except Exception as e:  # noqa: BLE001
            print(f"XTTS_CKPT falhou ({type(e).__name__}: {str(e)[:120]}) — recarrega o base", flush=True)
            tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(dev)  # pesos meio carregados = descarta
            m = tts.synthesizer.tts_model
    # 21/11 tarde (dona: "veja o acelerador DeepSpeed, quanto pode acelerar e se não perde qualidade"): XTTS_DEEPSPEED=1
    # troca o GPT do XTTS pelo kernel de inferência do DeepSpeed (o acelerador oficial do Coqui). Falhou = segue normal.
    if os.environ.get("XTTS_DEEPSPEED") == "1" and dev == "cuda":
        try:
            m.gpt.init_gpt_for_inference(kv_cache=True, use_deepspeed=True)
            print("XTTS DeepSpeed LIGADO", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"XTTS DeepSpeed falhou ({type(e).__name__}: {str(e)[:300]}) — segue normal", flush=True)
    # 22/11 (dona: "precisamos acelerar todos os modelos"): XTTS_FP16=1 = meia precisão na placa (não compila nada,
    # vale nas 2 placas). Falhou = segue em fp32.
    if os.environ.get("XTTS_FP16") == "1" and dev == "cuda":
        try:
            m.half()
            print("XTTS fp16 LIGADO", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"XTTS fp16 falhou ({type(e).__name__}: {str(e)[:200]}) — segue fp32", flush=True)
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
            if os.environ.get("XTTS_FP16") == "1" and dev == "cuda":  # 23/11: latentes na mesma precisão do modelo
                gpt, spk = gpt.half(), spk.half()
            partes = [re.sub(r"\.$", "", x).strip() for x in re.split(r"(?<=[.!?])\s+", limpa(it["texto"]))
                      if x.strip()]
            if it.get("frase_inteira"):  # versão 4: a frase toda de uma vez (só sem ponto)
                partes = [re.sub(r"\.(?=\s|$)", ",", limpa(it["texto"])).strip(" ,")]
            tent = []
            for k in range(int(it.get("n", 1))):
                torch.manual_seed(int(it.get("seed", 42)) + k)
                audio = []
                for j, frase in enumerate(partes):
                    # v8 (21/11, estudo dos narradores reais): cadência POR SENTENÇA — piada/comentário mais rápido
                    # (narradores reais: +10 a +20%), última sentença da fala um pouco mais lenta, pausa curta
                    vel = 1.0
                    if it.get("cadencia_real"):
                        if re.search(r"(?i)(kkk|mentira|brincadeira|hein|né\?|tá\?|particulares|cen[aá]rio|respeito)",
                                     frase):
                            vel = 1.12
                        elif j == len(partes) - 1 and len(partes) > 1:
                            vel = 0.95
                    # 21/11 v11 (dona: "'vocês fariam esse acordo' ainda não parece pergunta retórica"): medido nos
                    # narradores reais (segs.json): pergunta sai ~10-15% MAIS RÁPIDA que a narração e o fim quase
                    # reto (não sobe muito). Então: pausa pro público pensar ANTES ("E vocês"), pergunta +8%.
                    publico = it.get("pergunta_publico") and re.match(r"(?i)^(e |mas )?(vocês|você|cês|tu)\b", frase)
                    eu_faria = re.match(r"(?i)^eu (faria|fazia|aceitaria|toparia|pegaria)\b", frase)
                    if publico:
                        vel = 1.08
                    elif eu_faria and it.get("pergunta_publico"):
                        vel = 1.0  # a afirmação dele: convicção, sem segurar
                    if j > 0 and (publico or (eu_faria and it.get("manha"))):
                        # troca a pausa curta da sentença anterior por uma maior (o "tempo" da piada)
                        if audio and not audio[-1].any():
                            audio.pop()
                        audio.append(np.zeros(int(24000 * (0.55 if publico else 0.30)), np.float32))
                        if eu_faria and it.get("manha") and it.get("risada"):
                            # 21/11 v12: a manha — risadinha REAL dele antes do "Eu faria"
                            try:
                                rw, rsr = sf.read(it["risada"], dtype="float32")
                                rw = rw.mean(1) if rw.ndim > 1 else rw
                                rw = np.interp(np.arange(0, len(rw), rsr / 24000), np.arange(len(rw)), rw)
                                ref_rms = float(np.sqrt(np.mean(np.concatenate([a_ for a_ in audio if a_.any()] or
                                                                                [rw]) ** 2)) or 0.05)
                                rw = rw * (0.8 * ref_rms / (float(np.sqrt(np.mean(rw ** 2))) or 1))
                                audio += [rw.astype(np.float32), np.zeros(int(24000 * 0.08), np.float32)]
                            except Exception as e:  # noqa: BLE001
                                print(f"XTTS risada falhou {e}", flush=True)
                    o = m.inference(frase, "pt", gpt, spk, temperature=float(it.get("temp", 0.6)), top_p=float(os.environ.get("XTTS_TOP_P", "0.8")),
                                    top_k=40, repetition_penalty=10.0, length_penalty=1.0, speed=vel,
                                    enable_text_splitting=False)
                    audio.append(np.asarray(o["wav"], dtype=np.float32))
                    if j < len(partes) - 1:
                        audio.append(np.zeros(int(24000 * (0.12 if it.get("cadencia_real") else 0.18)), np.float32))
                a = np.concatenate(audio)
                tent.append((a, _f0(a, 24000), len(it["texto"]) / max(len(a) / 24000, 0.1)))
            if len(tent) > 1:
                alvo = float(np.median(f0_ok)) if len(f0_ok) >= 3 else float(np.median([x[1] for x in tent if x[1]] or [0]))
                calvo = float(np.median(cps_ok)) if len(cps_ok) >= 3 else float(np.median([x[2] for x in tent]))

                def pena(x):
                    st = abs(12 * np.log2(x[1] / alvo)) if x[1] and alvo else 6.0
                    fora = abs(x[2] / calvo - 1) if calvo else 0
                    return st + (8 * (fora - 0.3) if fora > 0.3 else 0)
                if it.get("whisper") and _whisper() is not None:
                    # v9: a nota do Whisper (palavras certas) pesa junto — corta a tentativa que engoliu/inventou
                    def pena2(x):
                        return pena(x) + 10 * _wer(it["texto"], x[0])
                    melhor = min(tent, key=pena2)
                else:
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
