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

    def _tem_repeticao(txt):
        import re as _re
        pal = _re.findall(r"\w+", txt.lower())
        return any(pal[k] == pal[k + 1] for k in range(len(pal) - 1))

    def gera(txt, suf=""):
        # 20/11 dona (amostras por tipo, KkVirjão): "as mesmas técnicas em tipos de áudio diferentes funcionam e em
        # outros se invertem — as variações só valem pra aqueles trechos". Temperatura POR SUB-VOZ conforme o que ela
        # aprovou: irritado e metralhadora = solta (aprovou 07 "mais solta"); agudo = normal (só aprovou 05/09/12/14).
        TEMP_SUB = {"_irritado": 0.95, "_metralhadora": 0.95, "_agudo": 0.85}
        # 20/11 noite (caça de defeitos: "voz esquisita, distorcida, sons estranhos"): temperatura >= 0,9 com top_p
        # igual solta demais o Fish. Teto 0,85 e top_p fixo 0,8 (FISH_TEMP_LIVRE=1 volta ao de antes)
        if os.environ.get("FISH_TEMP_LIVRE") != "1":
            TEMP_SUB = {k: min(v, 0.85) for k, v in TEMP_SUB.items()}
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
                              top_p=(t_ if os.environ.get("FISH_TEMP_LIVRE") == "1" else min(t_, 0.8)),
                              # "não, não, não" / "vai, vai": penalidade de repetição alta faz a 2ª/3ª sair estranha
                              repetition_penalty=(1.1 if _tem_repeticao(txt) else 1.2), temperature=t_, format="wav")
        for r in eng.inference(req):
            if r.code == "final":
                return r.audio
            if r.code == "error":
                raise RuntimeError(str(r.error))

    gera("Olá.")  # aquecimento
    print(f"FISH carga {time.time() - t:.1f}s", flush=True)

    def _f0(a, sr):
        """mediana do tom (Hz) — cepstro simples, só pra comparar tentativas da mesma frase"""
        x = a[:: max(1, sr // 16000)].astype(np.float32)
        out = []
        for i in range(0, len(x) - 1024, 320):
            fr = x[i:i + 1024] * np.hanning(1024)
            if np.sqrt((fr ** 2).mean()) < 0.02:
                continue
            c = np.abs(np.fft.irfft(np.log(np.abs(np.fft.rfft(fr, 4096)) + 1e-9)))
            out.append(16000 / (40 + np.argmax(c[40:228])))
        return float(np.median(out)) if len(out) >= 5 else 0.0

    # 20/11 noite (caça de defeitos, 3 rodadas da MESMA frase): o Fish sorteia o tom a cada geração — a mesma frase saiu
    # de -4 a +12 st do normal do narrador (é o "engrossa/afina de repente"). Melhor de N: gera N tentativas e fica com
    # a mais perto do tom do narrador (medido na própria referência) e com duração plausível pro texto.
    # FISH_TENTATIVAS=1 volta ao de antes.
    N_TENT = int(os.environ.get("FISH_TENTATIVAS", "3") or 1)
    # o "normal" do narrador = mediana do tom das frases JÁ aceitas neste vídeo (o tom da referência medido igual não
    # bate: no teste o Mike deu 195 Hz na referência x 116 Hz nas frases). Até ter 3 aceitas, vale a mediana das
    # tentativas da própria frase (a tentativa fora da curva perde).
    aceitas = []
    cps_aceitas = []
    try:
        import soundfile as _sf
        _info = _sf.info(str(ref))
        CPS_REF = len(ref_txt) / max(_info.duration, 1.0)
    except Exception:  # noqa: BLE001
        CPS_REF = 0.0
    print(f"FISH melhor de {N_TENT} por frase (tom mais perto do normal do narrador); ritmo da referência "
          f"{CPS_REF:.0f} letras/s", flush=True)

    def gera_melhor(txt, suf):
        tent = []
        for k in range(N_TENT):
            sr_, a_ = gera(txt, suf)
            a_ = np.asarray(a_).squeeze()
            cps = len(txt) / max(len(a_) / sr_, 0.1)
            tent.append((sr_, a_, _f0(a_, sr_), cps))
            alvo = float(np.median(aceitas)) if len(aceitas) >= 3 else 0.0
            if alvo and tent[-1][2]:
                st0 = abs(12 * np.log2(tent[-1][2] / alvo))
                _cref = float(np.median(cps_aceitas)) if len(cps_aceitas) >= 3 else CPS_REF
                cps_ok = (abs(cps / _cref - 1) <= 0.2) if _cref else True
                if st0 <= 1.5 and 8 <= cps <= 26 and cps_ok:  # já boa: não gasta mais tempo
                    break
        alvo = float(np.median(aceitas)) if len(aceitas) >= 3 else float(np.median([t_[2] for t_ in tent if t_[2]] or [0]))
        # 20/11 noite (dona: "no A2v2 ele falou 'levou 1, 2 e uma faca' — nenhum outro tem essa parte"): o Fish INVENTA
        # palavras às vezes. Palavra inventada = frase mais longa que o texto pede -> letras/s bem abaixo do ritmo das
        # frases já aceitas. Penaliza quem sai do ritmo normal do narrador neste vídeo (±30%).
        # 20/11 noite (dona: "o início do Mike no A2v3/A4v3 está estranho"): a 1ª frase saiu com 11 s pra ~110 letras
        # (metade do ritmo dele) — no começo ainda não há frases aceitas e as 3 tentativas podiam estar todas lentas.
        # Antes de ter 3 aceitas, o ritmo-alvo é o da própria referência (letras do texto ÷ duração do trecho real).
        cps_alvo = (float(np.median(cps_aceitas)) if len(cps_aceitas) >= 3
                    else (CPS_REF or float(np.median([t_[3] for t_ in tent]))))

        def pena(t_):
            st_ = abs(12 * np.log2(t_[2] / alvo)) if t_[2] and alvo else 6.0
            fora = abs(t_[3] / cps_alvo - 1) if cps_alvo else 0.0
            # tom longe do normal + velocidade absurda (engoliu/repetiu) + ritmo fora do dele (inventou/engoliu palavra)
            return st_ + (0 if 8 <= t_[3] <= 26 else 4) + (8 * (fora - 0.3) if fora > 0.3 else 0)
        melhor = min(tent, key=pena)
        if melhor[2]:
            aceitas.append(melhor[2])
        cps_aceitas.append(melhor[3])
        print(f"FISH melhor de {len(tent)}: {pena(melhor):.1f} de penalidade, {melhor[3]:.0f} letras/s", flush=True)
        return melhor[0], melhor[1]

    ok = 0
    for it in itens:
        if Path(it["saida"]).exists():
            ok += 1
            continue
        t0 = time.time()
        try:
            sr, a = gera_melhor(it["texto"], it.get("ref", ""))
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
