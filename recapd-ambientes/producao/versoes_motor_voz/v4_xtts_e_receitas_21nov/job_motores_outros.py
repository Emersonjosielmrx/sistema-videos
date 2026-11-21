"""Dona 20/11 noite: "vamos testar essas aí também, as que não testamos — completos, com todas as versões, da mais
simples à mais completa, com aquele mesmo áudio". Motores fora da Fish nunca testados: Higgs Audio v3, CosyVoice 3,
IndexTTS 2, F5-TTS, XTTS v2. Mesmo roteiro do gol (18 frases), mesmo trecho real do narrador como referência.
Versões (iguais às dos modelos novos da Fish):
  1_limpa                 texto puro, 1 geração
  2_melhor_de_3           texto corrigido (pergunta, sem kkk/"..."), 3 gerações, fica a mais perto do tom/ritmo dele
  3_melhor_de_3_+_emocao  idem com a marcação de emoção do motor (quem não tem: não sai)
  4_tudo                  a 3 (ou a 2) + acelera no código (microcortes + velocidade por frase) + S do "respeito"
Cada motor num ambiente próprio (uv em /tmp/uvbin) e num processo só (o modelo carrega 1x).
plano.json: {"motor": "higgs|cosyvoice|indextts|f5|xtts"}. Saída: saida/<voz>_<motor>_<versão>.wav + _log.txt.
"""
import json, os, re, shutil, subprocess, sys, time
from pathlib import Path

P = Path(sys.argv[1]); S = P / "saida"; S.mkdir(exist_ok=True)
LOG = S / "_log.txt"
UV = "/tmp/uvbin/uv"


def log(m):
    print(m, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")


def sh(a, t=3600, cwd=None, env=None):
    return subprocess.run(a, capture_output=True, text=True, timeout=t, cwd=cwd, env=env)


def _rclone():
    import glob
    cands = [str(P.resolve().parents[2] / "rclone")] + glob.glob("/kaggle/tmp/**/rclone", recursive=True)
    bins = [p for p in cands if os.path.isfile(p) and os.access(p, os.X_OK)]
    confs = [c for c in ["/tmp/rclone.conf"] + glob.glob("/kaggle/input/**/rclone.conf", recursive=True)
             if os.path.isfile(c)]
    return (bins[0], confs[0]) if bins and confs else (None, None)


def uv():
    if not os.path.exists(UV):
        sh(["bash", "-c", "mkdir -p /tmp/uvbin && (curl -LsSf https://astral.sh/uv/install.sh | "
            "env UV_INSTALL_DIR=/tmp/uvbin UV_NO_MODIFY_PATH=1 sh) || (pip install -q --target /tmp/uvpkg uv && "
            "cp $(find /tmp/uvpkg -name uv -type f -path '*bin*' | head -1) /tmp/uvbin/uv && chmod +x /tmp/uvbin/uv)"],
           900)
    log(f"uv: {os.path.exists(UV)}")


def venv(nome, pyver):
    v = Path(f"/tmp/venvs_voz/{nome}")
    py = v / "bin" / "python"
    if not py.exists():
        r = sh([UV, "venv", "--python", pyver, str(v)], 900)
        log(f"venv {nome} py{pyver} rc={r.returncode} {r.stderr[-200:]}")
    return str(py)


def pip(py, *pk, t=3600):
    r = sh([UV, "pip", "install", "--python", py, *pk], t)
    log(f"pip {' '.join(pk)[:80]} rc={r.returncode} {r.stderr[-300:] if r.returncode else ''}")
    return r.returncode == 0


# ---------- emoção: 4 categorias por frase, cada motor escreve do seu jeito ----------
CAT = [(r"(?i)\b(isso|acert|derrub|venc)", "anima"), (r"(?i)(n[aã]o, n[aã]o|morr|levanta)", "triste"),
       (r"(?i)(brincadeira|mentira|particulares|cen[aá]rio|respeito)", "ri"), (r"(?i)(n[aã]o aguento)", "frustra"),
       (r"(?i)(ataca|desvia|abaixa|gira|segura|avan)", "anima")]


def categoria(t):
    for p, c in CAT:
        if re.search(p, t):
            return c
    return ""


EMO = {
    "higgs": {"anima": "<|emotion:enthusiasm|>", "triste": "<|emotion:sadness|>", "ri": "<|emotion:amusement|>",
              "frustra": "<|emotion:anger|>"},
    "cosyvoice": {"anima": "Please speak with great excitement.", "triste": "Please speak sadly.",
                  "ri": "Please speak in an amused, joking way.", "frustra": "Please speak frustrated."},
    "indextts": {"anima": "muito empolgado", "triste": "triste", "ri": "achando graça, rindo", "frustra": "irritado"},
}

# ---------- workers: um processo por motor, lê tarefas [{texto, emo, seed, saida}] ----------
W_F5 = r'''
import json, sys, torch
from f5_tts.api import F5TTS
ref, reftxt, tarefas = sys.argv[1], open(sys.argv[2], encoding="utf-8").read().strip(), json.load(open(sys.argv[3], encoding="utf-8"))
# 20/11: F5-TTS afinado em pt-BR pela comunidade (firstpixel/F5-TTS-pt-br, 7 mil downloads); o base não fala português
from huggingface_hub import hf_hub_download
ck = hf_hub_download("firstpixel/F5-TTS-pt-br", "pt-br/model_last.safetensors")
m = F5TTS(ckpt_file=ck)
for t in tarefas:
    try:
        # o modelo pede texto minúsculo (o afinamento foi feito assim)
        m.infer(ref_file=ref, ref_text=reftxt.lower(), gen_text=t["texto"].lower(), file_wave=t["saida"], seed=t["seed"])
        print("ok", t["saida"], flush=True)
    except Exception as e:
        print("ERRO", t["saida"], e, flush=True)
'''
W_XTTS = r'''
import json, os, sys, torch
os.environ["COQUI_TOS_AGREED"] = "1"
from TTS.api import TTS
ref, tarefas = sys.argv[1], json.load(open(sys.argv[3], encoding="utf-8"))
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")
import re
def limpa(t):
    # 20/11 dona: "o XTTS não estava ruim, só que ele FALA os pontos". O XTTS lê pontuação solta em voz alta
    # (ponto final no fim de cada pedaço, "...", aspas, dois-pontos). Tira o ponto final, troca "..." e ":" por vírgula
    # e tira aspas; "!" e "?" ficam (dão entonação).
    t = t.replace("…", ",").replace("...", ",").replace(":", ",").replace(";", ",")
    t = re.sub(r"[\"“”‘’]", "", t)
    t = re.sub(r"\.(?=\s|$)", ",", t).strip(" ,")
    t = re.sub(r",\s*,", ",", t)
    return t
for t in tarefas:
    try:
        torch.manual_seed(t["seed"])
        tts.tts_to_file(text=limpa(t["texto"]), speaker_wav=ref, language="pt", file_path=t["saida"],
                        enable_text_splitting=False)
        print("ok", t["saida"], flush=True)
    except Exception as e:
        print("ERRO", t["saida"], e, flush=True)
'''

W_XTTS2 = r"""
import json, os, re, sys, torch, numpy as np, soundfile as sf
os.environ["COQUI_TOS_AGREED"] = "1"
from TTS.api import TTS
tarefas = json.load(open(sys.argv[3], encoding="utf-8"))
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")
m = tts.synthesizer.tts_model
def limpa(t):
    t = t.replace("…", ",").replace("...", ",").replace(":", ",").replace(";", ",")
    t = re.sub(r"[\"“”‘’]", "", t)
    t = re.sub(r",\s*,", ",", t)
    return t.strip(" ,")
lat = {}
for t in tarefas:
    try:
        torch.manual_seed(t["seed"])
        refs = tuple(t["refs"])
        if refs not in lat:
            lat[refs] = m.get_conditioning_latents(audio_path=list(refs))
        gpt, spk = lat[refs]
        # 21/11 dona (XTTS): "fica falando 'ponto' toda hora" e "repete a palavra 'aulas'": o XTTS degrada em texto
        # longo e lê o ponto final. Gera SENTENÇA por sentença (sem o ponto), junta com pausa curta.
        partes = [x for x in re.split(r"(?<=[.!?])\s+", limpa(t["texto"])) if x.strip()]
        audio = []
        for k, frase in enumerate(partes):
            frase = re.sub(r"\.$", "", frase).strip()
            o = m.inference(frase, "pt", gpt, spk, temperature=t.get("temp", 0.6), top_p=0.8, top_k=40,
                            repetition_penalty=10.0, length_penalty=1.0, speed=t.get("vel", 1.0),
                            enable_text_splitting=False)
            audio.append(np.asarray(o["wav"], dtype=np.float32))
            if k < len(partes) - 1:
                audio.append(np.zeros(int(24000 * 0.18), np.float32))
        sf.write(t["saida"], np.concatenate(audio), 24000)
        print("ok", t["saida"], flush=True)
    except Exception as e:
        print("ERRO", t["saida"], repr(e)[:300], flush=True)
"""

W_INDEX = r'''
import json, os, sys, torch
os.chdir("/tmp/index-tts"); sys.path.insert(0, "/tmp/index-tts")
from indextts.infer_v2 import IndexTTS2
ref, tarefas = sys.argv[1], json.load(open(sys.argv[3], encoding="utf-8"))
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints", use_fp16=True)
for t in tarefas:
    try:
        torch.manual_seed(t["seed"])
        kw = dict(emo_text=t["emo"], use_emo_text=True, emo_alpha=0.6) if t["emo"] else {}
        tts.infer(spk_audio_prompt=ref, text=t["texto"], output_path=t["saida"], **kw)
        print("ok", t["saida"], flush=True)
    except Exception as e:
        print("ERRO", t["saida"], e, flush=True)
'''
W_COSY = r'''
import json, os, sys, torch, torchaudio
CV = "/tmp/CosyVoice"; sys.path.insert(0, CV); sys.path.insert(0, CV + "/third_party/Matcha-TTS"); os.chdir(CV)
ref, reftxt, tarefas = sys.argv[1], open(sys.argv[2], encoding="utf-8").read().strip(), json.load(open(sys.argv[3], encoding="utf-8"))
md = "pretrained_models/Fun-CosyVoice3-0.5B"
try:
    from cosyvoice.cli.cosyvoice import AutoModel
    cv = AutoModel(model_dir=md)
except Exception:
    from cosyvoice.cli.cosyvoice import CosyVoice3
    cv = CosyVoice3(md)
for t in tarefas:
    try:
        torch.manual_seed(t["seed"])
        inst = (t["emo"] + " ") if t["emo"] else ""
        pt = "You are a helpful assistant. " + inst + "<|endofprompt|>" + reftxt
        partes = [o["tts_speech"] for o in cv.inference_zero_shot(t["texto"], pt, ref, stream=False)]
        torchaudio.save(t["saida"], torch.cat(partes, dim=1), cv.sample_rate)
        print("ok", t["saida"], flush=True)
    except Exception as e:
        print("ERRO", t["saida"], repr(e)[:300], flush=True)
'''
W_HIGGS = r'''
import base64, json, os, subprocess, sys, time, urllib.request
ref, reftxt, tarefas = sys.argv[1], open(sys.argv[2], encoding="utf-8").read().strip(), json.load(open(sys.argv[3], encoding="utf-8"))
srv = subprocess.Popen(["sgl-omni", "serve", "--model-path", "bosonai/higgs-audio-v3-tts-4b", "--dtype", "float16",
                        "--allowed-local-media-path", os.path.dirname(ref), "--port", "8000"],
                       stdout=open("/tmp/higgs_srv.log", "w"), stderr=subprocess.STDOUT)
for _ in range(180):
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5); break
    except Exception:
        if srv.poll() is not None: break
        time.sleep(10)
print("SERVIDOR_HIGGS", srv.poll(), open("/tmp/higgs_srv.log").read()[-3000:], flush=True)
if srv.poll() is not None:
    sys.exit(1)
for t in tarefas:
    try:
        body = {"model": "bosonai/higgs-audio-v3-tts-4b", "voice": "default", "input": (t["emo"] or "") + t["texto"],
                "references": [{"audio_path": ref, "text": reftxt}], "temperature": 0.7, "top_k": 50,
                "max_new_tokens": 1024, "seed": t["seed"], "response_format": "wav"}
        req = urllib.request.Request("http://127.0.0.1:8000/v1/audio/speech", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        dados = urllib.request.urlopen(req, timeout=600).read()
        if dados[:4] != b"RIFF":
            try: dados = base64.b64decode(json.loads(dados)["audio"])
            except Exception: pass
        open(t["saida"], "wb").write(dados)
        print("ok", t["saida"], flush=True)
    except Exception as e:
        print("ERRO", t["saida"], repr(e)[:300], flush=True)
srv.terminate()
'''


def preparar(motor):
    """instala o motor e devolve (python, script do worker, tem_emoção)"""
    uv()
    sh(["bash", "-c", "apt-get update -qq && apt-get install -y -qq ffmpeg sox libsox-dev portaudio19-dev"], 900)
    if motor == "f5":
        py = venv("f5", "3.11")
        pip(py, "f5-tts", "soundfile", "huggingface_hub")
        return py, W_F5, False
    if motor == "xtts2":
        py = venv("xtts", "3.11")
        pip(py, "torch==2.5.1", "torchaudio==2.5.1", t=3600)
        pip(py, "coqui-tts", "soundfile", "transformers<4.50")
        return py, W_XTTS2, False
    if motor == "xtts":
        py = venv("xtts", "3.11")
        pip(py, "torch==2.5.1", "torchaudio==2.5.1", t=3600)
        pip(py, "coqui-tts", "soundfile", "transformers<4.50")
        return py, W_XTTS, False
    if motor == "indextts":
        if not Path("/tmp/index-tts").exists():
            sh(["git", "clone", "-q", "--depth", "1", "https://github.com/index-tts/index-tts.git", "/tmp/index-tts"], 900)
            sh(["bash", "-c", "cd /tmp/index-tts && git lfs install && git lfs pull"], 900)
        py = venv("indextts", "3.10")
        pip(py, "-e", "/tmp/index-tts", "huggingface_hub", t=5400)
        if not Path("/tmp/index-tts/checkpoints/config.yaml").exists():
            r = sh([py, "-c", "from huggingface_hub import snapshot_download as d; "
                    "d('IndexTeam/IndexTTS-2', local_dir='/tmp/index-tts/checkpoints')"], 3600)
            log(f"pesos IndexTTS-2 rc={r.returncode} {r.stderr[-200:]}")
        return py, W_INDEX, True
    if motor == "cosyvoice":
        if not Path("/tmp/CosyVoice").exists():
            sh(["git", "clone", "-q", "--recursive", "https://github.com/FunAudioLLM/CosyVoice.git", "/tmp/CosyVoice"],
               1800)
        py = venv("cosyvoice", "3.10")
        # o requirements traz coisas de treino (deepspeed/tensorrt) que quebram: tira e instala o resto
        req = Path("/tmp/CosyVoice/requirements.txt")
        linhas = [l for l in req.read_text().splitlines() if l.strip() and not re.match(
            r"(?i)(deepspeed|tensorrt|onnxruntime-gpu|--extra-index|-i |gradio|fastapi|uvicorn)", l.strip())]
        Path("/tmp/cosy_req.txt").write_text("\n".join(linhas))
        pip(py, "-r", "/tmp/cosy_req.txt", "onnxruntime", "modelscope", t=5400)
        md = Path("/tmp/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B")
        if not md.exists():
            r = sh([py, "-c", "from modelscope import snapshot_download as d; "
                    f"d('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', local_dir='{md}')"], 3600)
            log(f"pesos CosyVoice3 rc={r.returncode} {r.stderr[-200:]}")
        return py, W_COSY, True
    if motor == "higgs":
        py = venv("higgs", "3.11")
        if not pip(py, "sglang-omni", t=5400):
            sh(["git", "clone", "-q", "--depth", "1", "https://github.com/sgl-project/sglang-omni.git", "/tmp/sglang-omni"],
               900)
            pip(py, "-e", "/tmp/sglang-omni", t=5400)
        os.environ["PATH"] = str(Path(py).parent) + ":" + os.environ["PATH"]
        return py, W_HIGGS, True
    raise ValueError(motor)


def _f0_cps(w, texto):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(w), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    out = []
    for i in range(0, len(a) - 1024, 320):
        fr = a[i:i + 1024] * np.hanning(1024)
        if np.sqrt((fr ** 2).mean()) < 0.02:
            continue
        c = np.abs(np.fft.irfft(np.log(np.abs(np.fft.rfft(fr, 4096)) + 1e-9)))
        out.append(16000 / (40 + np.argmax(c[40:228])))
    return (float(np.median(out)) if len(out) >= 5 else 0.0), len(texto) / max(len(a) / 16000, 0.1)


def escolher(tent, texto, aceitas):
    import numpy as np
    med = [(_f0_cps(w, texto), w) for w in tent]
    if len(aceitas) >= 3:
        alvo, calvo = float(np.median([m[0][0] for m in aceitas])), float(np.median([m[0][1] for m in aceitas]))
    else:
        alvo = float(np.median([m[0][0] for m in med if m[0][0]] or [0]))
        calvo = float(np.median([m[0][1] for m in med]))

    def pena(m):
        f, cps = m[0]
        st = abs(12 * np.log2(f / alvo)) if f and alvo else 6.0
        fora = abs(cps / calvo - 1) if calvo else 0
        return st + (0 if 8 <= cps <= 26 else 4) + (8 * (fora - 0.3) if fora > 0.3 else 0)
    m = min(med, key=pena)
    aceitas.append(m)
    return m[1]


def posprocessar(ws, linhas, forca=0.5, cadencia=False):
    if not ws:
        return
    import climas_voz
    anime_tts._marcar_gol(linhas, climas_voz.escolher([anime_tts._seguro(x) for x in linhas], str(ws[0].parent)))
    for i, w in enumerate(ws):
        try:
            anime_tts.narracao_curva.pos_processar(w, 0.0)
            anime_tts.narracao_curva.microcortes(w)
            if cadencia:
                anime_tts._cadencia_quebrada(w)
            kv = 1 + (anime_tts._vel_por_frase(anime_tts._seguro(linhas[i]), i) - 1) * forca
            if anime_tts._frase_lenta(linhas[i]):
                kv = min(kv, 1.04)
            tmp = w.with_name(w.stem + ".kv.wav")
            if abs(kv - 1) > 0.01 and sh(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-af", f"atempo={kv:.3f}",
                                          str(tmp)]).returncode == 0:
                os.replace(tmp, w)
            if anime_tts._tem_respeito_piada(anime_tts._seguro(linhas[i]), i):
                anime_tts._esticar_s_respeito(w, texto=anime_tts._seguro(linhas[i]))
        except Exception as e:  # noqa: BLE001
            log(f"  pós frase {i}: {type(e).__name__} {e}")


def juntar(ws, dst):
    sil = dst.with_name("_sil.wav")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.35", "-c:a",
        "pcm_s16le", str(sil)])
    nws = []
    for w in ws:
        n = w.with_name(w.stem + "_n.wav")
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(n)])
        nws.append(n)
    lst = dst.with_suffix(".txt")
    lst.write_text("".join(f"file '{w}'\nfile '{sil}'\n" for w in nws))
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-af", "loudnorm=I=-16:TP=-1.5",
        "-ar", "44100", "-ac", "1", str(dst)])
    lst.unlink(missing_ok=True)


def main():
    global anime_tts
    plano = json.loads((P / "plano.json").read_text(encoding="utf-8"))
    motor = plano["motor"]
    roteiros = json.loads((P / "roteiros.json").read_text(encoding="utf-8"))
    b, c = _rclone()
    base = P / "prod"
    for parte in ("bin", "config"):
        sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/raiz/D/recapd-ambientes/producao/{parte}",
            str(base / parte)], 1800)
    sys.path.insert(0, str(base / "bin"))
    import logging
    logging.basicConfig(level=logging.INFO, filename=str(S / "_anime_tts.log"))
    import anime_tts
    vz = P / "vozes"
    vozes = [v for v in roteiros if not v.startswith("_")]
    for v in vozes:
        sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/vozes/{v}", str(vz / v), "--include",
            "referencia_fish*"], 900)
    try:
        py, worker, tem_emo = preparar(motor)
    except Exception as e:  # noqa: BLE001
        log(f"{motor}: não instalou — {type(e).__name__}: {e}")
        sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1", str(S / "video.mp4")])
        return
    wpath = P / f"worker_{motor}.py"
    wpath.write_text(worker, encoding="utf-8")
    for voz in vozes:
        ref = vz / voz / "referencia_fish.wav"
        # referência mono 24 kHz e no máx. 15 s (F5/XTTS/IndexTTS cortam ou estouram com referência longa)
        ref15 = vz / voz / "ref_15s.wav"
        lim = 9 if motor == "f5" else 15
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(ref), "-t", str(lim), "-ac", "1", "-ar", "24000", str(ref15)])
        reftxt = vz / voz / "referencia_fish.txt"
        if lim < 15:  # texto da referência cortado na mesma proporção (o F5 precisa do texto do trecho)
            import wave as _w
            with _w.open(str(ref)) as _f:
                dtot = _f.getnframes() / _f.getframerate()
            tt = reftxt.read_text(encoding="utf-8").split()
            cort = vz / voz / "ref_txt_corte.txt"
            cort.write_text(" ".join(tt[:max(4, int(len(tt) * min(1.0, lim / dtot)))]), encoding="utf-8")
            reftxt = cort
        linhas = roteiros[voz]
        txt = [anime_tts._texto_fish(anime_tts._seguro(t))[0] for t in linhas]
        emo = [EMO.get(motor, {}).get(categoria(t), "") for t in linhas]
        versoes = [("1_limpa", linhas, [""] * 18, 1, False), ("2_melhor_de_3", txt, [""] * 18, 3, False)]
        if motor == "xtts2":
            # emoção do XTTS = a REFERÊNCIA: normal + o trecho real dele do tipo da frase (piada/agudo/tensão...),
            # escolhido pelas mesmas regras do Fish (anime_tts._subvoz_por_frase)
            tipos = {p_.stem.replace("referencia_fish", "") for p_ in (vz / voz).glob("referencia_fish_*.wav")
                     if "antiga" not in p_.stem}
            import climas_voz
            climas_voz.escolher = climas_voz.escolher  # usa o LLM se tiver; senão só pelo texto
            subs = anime_tts._subvoz_por_frase([anime_tts._seguro(x) for x in linhas], str(vz / voz), None, tem=tipos)
            emo = [subs.get(i, "") if subs.get(i, "") != "_todas" else "" for i in range(len(linhas))]
            versoes = [("5_XTTS_melhorado_(sem_ponto_+_frase_a_frase_+_tipo_+_melhor_de_3)", txt, emo, 3, True),
                       ("6_XTTS_melhorado_+_CADENCIA_do_Q3", txt, emo, 3, "cad")]
        if tem_emo:
            versoes += [("3_melhor_de_3_+_emocao", txt, emo, 3, False),
                        ("4_tudo_(melhor_de_3_+_emocao_+_acelera_no_codigo_+_S)", txt, emo, 3, True)]
        else:
            versoes += [("4_tudo_(melhor_de_3_+_acelera_no_codigo_+_S)", txt, [""] * 18, 3, True)]
        # uma rodada só no motor: todas as tarefas de todas as versões (as iguais não repetem)
        trab = P / "trab" / voz
        trab.mkdir(parents=True, exist_ok=True)
        tarefas, mapa = [], {}
        for nome, ls, em, tent, _pos in versoes:
            for i, t in enumerate(ls):
                for k in range(tent):
                    chave = (t, em[i], k)
                    if chave not in mapa:
                        out = trab / f"t{len(mapa):04d}.wav"
                        mapa[chave] = out
                        ta = {"texto": t, "emo": em[i], "seed": 42 + k, "saida": str(out)}
                        if motor == "xtts2":
                            refs = [str(ref15)]
                            if em[i] and (vz / voz / f"referencia_fish{em[i]}.wav").exists():
                                sub15 = vz / voz / f"ref15{em[i]}.wav"
                                if not sub15.exists():
                                    sh(["ffmpeg", "-v", "error", "-y", "-i", str(vz / voz / f"referencia_fish{em[i]}.wav"),
                                        "-t", "15", "-ac", "1", "-ar", "24000", str(sub15)])
                                refs.append(str(sub15))
                            ta.update(refs=refs, temp=0.6)
                        tarefas.append(ta)
        tj = trab / "tarefas.json"
        tj.write_text(json.dumps(tarefas, ensure_ascii=False), encoding="utf-8")
        t0 = time.time()
        r = sh([py, str(wpath), str(ref15), str(reftxt), str(tj)], 6 * 3600)
        okn = sum(1 for t in tarefas if Path(t["saida"]).exists())
        log(f"{voz} {motor}: {okn}/{len(tarefas)} gerações em {time.time() - t0:.0f}s")
        if okn == 0:
            out_ = r.stdout + r.stderr
            i_ = out_.find("SERVIDOR_HIGGS")
            log(f"  saída do motor: {(out_[i_:i_ + 3000] if i_ >= 0 else out_[:1500] + ' ... ' + out_[-1500:])}")
            continue
        for nome, ls, em, tent, pos in versoes:
            aceitas, ws = [], []
            for i, t in enumerate(ls):
                tent_ws = [mapa[(t, em[i], k)] for k in range(tent) if mapa[(t, em[i], k)].exists()]
                if not tent_ws:
                    continue
                esc = escolher(tent_ws, t, aceitas) if len(tent_ws) > 1 else tent_ws[0]
                dst = trab / f"{nome[:1]}_{i:02d}.wav"
                shutil.copy(esc, dst)
                ws.append(dst)
            if pos and ws:
                posprocessar(ws, linhas, forca=(0.8 if motor == "xtts2" else 0.5), cadencia=(pos == "cad"))
            log(f"{voz} {motor} {nome}: {len(ws)}/18 frases")
            if ws:
                juntar(ws, S / f"{voz}_{motor}_{nome}.wav")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1", str(S / "video.mp4")])
    log("FIM")


if __name__ == "__main__":
    main()
