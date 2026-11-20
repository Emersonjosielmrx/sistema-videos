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
    # 20/11 dona: sub-vozes do narrador (risada, piada, agudo, personagem, metralhadora, mulher, tensão) — carrega
    # TODAS as referencia_fish_<sub>.wav que a voz tiver (a anime_tts escolhe por frase em "ref").
    por_clima = {"": refs}
    for w in sorted(pv.glob("referencia_fish_*.wav")):
        suf = w.stem.replace("referencia_fish", "")
        # 20/11: era "t" — sobrescrevia o t = time.time() e o "FISH carga" dava TypeError (Path - float): o processo
        # morria antes da 1ª frase e o longo de teste kxohroSbgS8 saiu com 0/558 no Fish
        w_txt = w.with_suffix(".txt")
        if suf.endswith("antiga") or not w_txt.exists():
            continue
        por_clima[suf] = [ServeReferenceAudio(audio=w.read_bytes(), text=w_txt.read_text(encoding="utf-8").strip())]
    # 20/11: "todas as sub-vozes juntas" (versão 12) foi aprovada em TODOS os tipos ouvidos -> "_todas" = todas as
    # sub-vozes da voz como referência (reserva de quem não tem a sub-voz específica da frase)
    subs_ = [v[0] for k, v in por_clima.items() if k and k not in ("_antiga",)]
    if len(subs_) >= 3:
        por_clima["_todas"] = subs_
    print(f"FISH referências: {sorted(k or 'normal' for k in por_clima)}", flush=True)
    # 20/11 (estudo 3, mesmas frases x real): narrador que varia muito (Momo/Mike/KkVirjão) fica mais perto do real com
    # temperatura/top_p 0,85 (Mike: desvio de tom 5,69 x 5,73 real; com 0,7 = 5,40). Estáveis seguem 0,7.
    # FISH_SOLTO=<valor> força; "fish_solto" no personagem.json da voz também.
    solto_pad = {"momo": 0.85, "mike": 0.85, "kkvirjao": 0.85}
    SOLTO = solto_pad.get(pv.name, 0.7)
    try:
        SOLTO = float(json.loads((pv / "personagem.json").read_text(encoding="utf-8")).get("fish_solto", SOLTO))
    except (OSError, ValueError):
        pass
    if os.environ.get("FISH_SOLTO"):
        SOLTO = float(os.environ["FISH_SOLTO"])
    print(f"FISH temperatura/top_p {SOLTO}", flush=True)

    def gera(txt, suf=""):
        # 20/11 dona (amostras por tipo, KkVirjão): "as mesmas técnicas em tipos de áudio diferentes funcionam e em
        # outros se invertem — as variações só valem pra aqueles trechos". Temperatura POR SUB-VOZ conforme o que ela
        # aprovou: irritado e metralhadora = solta (aprovou 07 "mais solta"); agudo = normal (só aprovou 05/09/12/14).
        TEMP_SUB = {"_irritado": 0.95, "_metralhadora": 0.95, "_agudo": 0.85}
        t_ = min(1.0, TEMP_SUB.get(suf, SOLTO))
        # 20/11 dona (KkVirjão "mulher"): a sub-voz mulher SOZINHA foi quase toda reprovada; aprovadas só as MISTAS
        # (normal+mulher, mulher+piada, todas juntas). Sub-vozes em SUB_SO_MISTA nunca vão sozinhas: vão com a normal.
        # 20/11 (Mike "agudo"): sozinha "começa com a voz dele e depois muda, ou fica lenta" — aprovou só normal,
        # mista, sub+piada e todas juntas. Por voz: {voz: sub-vozes que só vão misturadas com a normal}
        SO_MISTA_POR_VOZ = {"kkvirjao": {"_mulher"}, "mike": {"_mulher", "_agudo"}}
        SUB_SO_MISTA = SO_MISTA_POR_VOZ.get(pv.name, {"_mulher"})
        r_ = por_clima.get(suf) or refs
        if suf in SUB_SO_MISTA and suf in por_clima:
            r_ = refs + por_clima[suf]
        # 20/11 (teste gol4, dona): "falta homogeneidade — as ligadas parecem vários áudios emendados, até de pessoas
        # diferentes; na frase isolada acerta, quando junta não combina" ("na hora que começou a briga pareceu outra
        # voz"). Cada frase com uma sub-voz SOZINHA muda o timbre. Agora toda sub-voz vai JUNTO da referência normal
        # (a âncora da voz, sempre a 1ª) — o jeito muda, a pessoa fica a mesma. FISH_SUB_SOZINHA=1 volta ao antigo.
        elif suf and os.environ.get("FISH_SUB_SOZINHA") != "1":
            r_ = refs + [x for x in (por_clima.get(suf) or []) if x not in refs]
        req = ServeTTSRequest(text=txt, references=r_, reference_id=None,
                              max_new_tokens=1024, chunk_length=200,
                              top_p=t_, repetition_penalty=1.2, temperature=t_, format="wav")
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
