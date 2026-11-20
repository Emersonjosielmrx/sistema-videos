"""Fish Speech 1.5 na GPU do Kaggle — narração no jeito de falar do PRÓPRIO narrador (dona 19/11: "a partir de agora
ele vai ser o padrão; os longos são feitos no Kaggle"). Copia timbre + ritmo + pausas da referencia_fish.wav do
narrador (trecho ORIGINAL de ~10 s, nunca um clone: copiar cópia perde qualidade) -> SEM RVC por cima.

Roda no ambiente próprio que o kaggle_trabalhador monta (FISH_VENV, Python 3.11 + torch/torchaudio 2.4.1 travados —
o fish-speech 1.5 quebra com torchaudio 2.9+, medido 19/11). Chamado pelo anime_tts no modo "fish_tudo":

    python fish_nuvem.py lote <pasta_da_voz> <lista.json>     # lista = [{"texto", "saida"}]; grava wav 44,1 kHz mono

Medido no Kaggle (T4) em 19/11: carga 14,5 s 1x; cada fala ~7 s (1,7 s por segundo de áudio)."""
import json, sys, time
from pathlib import Path

FS = Path("/tmp/fish-speech")
CK = FS / "checkpoints" / "fish-speech-1.5"


def lote(pasta_voz, lista_json):
    import numpy as np, soundfile as sf, torch
    sys.path.insert(0, str(FS))
    import os
    os.chdir(FS)
    from fish_speech.inference_engine import TTSInferenceEngine
    from fish_speech.models.text2semantic.inference import launch_thread_safe_queue
    from fish_speech.models.vqgan.inference import load_model as load_decoder_model
    from fish_speech.utils.schema import ServeTTSRequest, ServeReferenceAudio
    pv = Path(pasta_voz)
    ref = pv / "referencia_fish.wav"
    ref_txt = (pv / "referencia_fish.txt").read_text(encoding="utf-8").strip()
    itens = json.loads(Path(lista_json).read_text(encoding="utf-8"))
    t = time.time()
    prec = torch.half
    llama = launch_thread_safe_queue(checkpoint_path=str(CK), device="cuda", precision=prec, compile=False)
    dec = load_decoder_model(config_name="firefly_gan_vq",
                             checkpoint_path=str(CK / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"), device="cuda")
    eng = TTSInferenceEngine(llama_queue=llama, decoder_model=dec, compile=False, precision=prec)
    # 19/11 dona ("é proposital estarem tão baixos?"): as referências vinham de -30 a -18 dB (momo -30). Nivela a cópia
    # usada aqui em -16 LUFS — referência baixa faz o Fish copiar a fala "longe/fraca".
    try:
        import subprocess as _sp
        niv = Path("/tmp") / f"ref_niv_{pv.name}.wav"
        if _sp.run(["ffmpeg", "-v", "error", "-y", "-i", str(ref), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "44100", "-ac", "1", str(niv)], capture_output=True).returncode == 0 and niv.exists():
            ref = niv
    except Exception:  # noqa: BLE001
        pass
    refs = [ServeReferenceAudio(audio=ref.read_bytes(), text=ref_txt)]
    # 19/11 dona ("momo e mike falam de muitas maneiras no mesmo vídeo, principalmente nas piadas e comentários"):
    # referência por jeito de falar (referencias_por_clima.py). Item com "ref": "_piada"/"_tensao" usa a dele.
    por_clima = {"": refs}
    for suf in ("_piada", "_tensao"):
        w, t = pv / f"referencia_fish{suf}.wav", pv / f"referencia_fish{suf}.txt"
        if w.exists() and t.exists():
            por_clima[suf] = [ServeReferenceAudio(audio=w.read_bytes(), text=t.read_text(encoding="utf-8").strip())]
    print(f"FISH referências: {sorted(k or 'normal' for k in por_clima)}", flush=True)

    def gera(txt, suf=""):
        req = ServeTTSRequest(text=txt, references=por_clima.get(suf) or refs, reference_id=None,
                              max_new_tokens=1024, chunk_length=200,
                              top_p=0.7, repetition_penalty=1.2, temperature=0.7, format="wav")
        for r in eng.inference(req):
            if r.code == "final":
                return r.audio
            if r.code == "error":
                raise RuntimeError(str(r.error))

    gera("Olá.")  # aquecimento
    print(f"FISH carga {time.time() - t:.1f}s", flush=True)
    ok = 0
    for it in itens:
        if Path(it["saida"]).exists():
            ok += 1
            continue
        t0 = time.time()
        try:
            sr, a = gera(it["texto"], it.get("ref", ""))
            a = np.asarray(a).squeeze()
            # 19/11 (revisão): grava num .tmp e renomeia — processo morto no meio não deixa wav parcial "pronto"
            tmp = it["saida"] + ".tmp.wav"
            sf.write(tmp, a, sr)
            os.replace(tmp, it["saida"])
            ok += 1
            print(f"FISH ok {time.time() - t0:.1f}s {it['saida']}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"FISH erro {type(e).__name__}: {str(e)[:200]} {it['saida']}", flush=True)
    print(f"FISH fim {ok}/{len(itens)}", flush=True)
    return 0 if ok == len(itens) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["lote"]:
        sys.exit(lote(sys.argv[2], sys.argv[3]))
