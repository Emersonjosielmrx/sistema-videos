"""QWEN3 no lugar do S2-Pro (dona 21/11: "se sair bom consertado, faz o mesmo trabalho 3x mais rápido") — base: "o S2-Pro é muito melhor (primeiro modelo que vi rir), mas lento — divide em 2 ou 3 sessões um vídeo
maior". O S2-Pro no teste levou ~130 s/frase porque o CLI CARREGAVA o modelo de 5B a cada frase. Aqui o modelo carrega
1x (TTSInferenceEngine do fish_speech novo; se a API não existir, cai pro CLI com --compile desligado). Cada sessão
narra um PEDAÇO do roteiro (plano: inicio, fim) e sobe os audio_i.wav pro Drive em
manhwa-drive:colab_recap/s2pro_longo/<vid>/audio/. Várias contas em paralelo = o longo inteiro numa noite.
Receita da versão aprovada (momo_S2pro_4_tudo): texto corrigido + tags de emoção + melhor de 2 (tom/ritmo) — o pós
(microcortes, velocidade por frase, S do respeito) é feito na montagem do longo.
"""
import json, os, re, shutil, subprocess, sys, time
from pathlib import Path

P = Path(sys.argv[1]); S = P / "saida"; S.mkdir(exist_ok=True)
LOG = S / "_log.txt"
FS = Path("/tmp/fish-novo"); FV = Path("/tmp/venvs_voz/fish_novo")


def log(m):
    print(m, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")


def sh(a, t=3600, cwd=None):
    return subprocess.run(a, capture_output=True, text=True, timeout=t, cwd=cwd)


def _rclone():
    import glob
    cands = [str(P.resolve().parents[2] / "rclone")] + glob.glob("/kaggle/tmp/**/rclone", recursive=True)
    bins = [p for p in cands if os.path.isfile(p) and os.access(p, os.X_OK)]
    confs = [c for c in ["/tmp/rclone.conf"] + glob.glob("/kaggle/input/**/rclone.conf", recursive=True)
             if os.path.isfile(c)]
    return (bins[0], confs[0]) if bins and confs else (None, None)


def instalar():
    uv = "/tmp/uvbin/uv"
    if not os.path.exists(uv):
        sh(["bash", "-c", "mkdir -p /tmp/uvbin && (curl -LsSf https://astral.sh/uv/install.sh | "
            "env UV_INSTALL_DIR=/tmp/uvbin UV_NO_MODIFY_PATH=1 sh)"], 900)
    v = Path("/tmp/venvs_voz/qwen3"); py = v / "bin" / "python"
    if not py.exists():
        sh([uv, "venv", "--python", "3.11", str(v)], 900)
        sh([uv, "pip", "install", "--python", str(py), "torch==2.5.1", "torchaudio==2.5.1"], 3600)
        sh([uv, "pip", "install", "--python", str(py), "qwen-tts", "soundfile"], 3600)
    return str(py), None


GERA = r'''
import json, os, sys, time
import soundfile as sf, torch
from qwen_tts import Qwen3TTSModel
ck, ref, reftxt, tarefas = sys.argv[1], sys.argv[2], open(sys.argv[3], encoding="utf-8").read().strip(), json.load(open(sys.argv[4], encoding="utf-8"))
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cuda:0", dtype=torch.float16)
print("Qwen3 carregado", flush=True)
for t in tarefas:
    if os.path.exists(t["saida"]): continue
    t0 = time.time()
    try:
        torch.manual_seed(t["seed"])
        kw = {"max_new_tokens": max(200, int(len(t["texto"]) * 6)), "repetition_penalty": 1.15}
        if t.get("emo"): kw["instruct"] = t["emo"]
        wavs = None
        for tent in (kw, {"max_new_tokens": kw["max_new_tokens"]}, {}):
            try:
                wavs, sr = m.generate_voice_clone(text=t["texto"], language="Portuguese", ref_audio=ref, ref_text=reftxt, **tent)
                break
            except TypeError:
                continue
        sf.write(t["saida"], wavs[0], sr)
        print(f"ok {time.time() - t0:.1f}s", t["saida"], flush=True)
    except Exception as e:
        print("ERRO", t["saida"], repr(e)[:300], flush=True)
'''


def main():
    plano = json.loads((P / "plano.json").read_text(encoding="utf-8"))
    voz, vid, ini, fim = plano["voz"], plano["vid"], plano["inicio"], plano["fim"]
    linhas = (P / "roteiro.txt").read_text(encoding="utf-8").splitlines()
    b, c = _rclone()
    base = P / "prod"
    for parte in ("bin", "config"):
        sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/raiz/D/recapd-ambientes/producao/{parte}",
            str(base / parte)], 1800)
    sys.path.insert(0, str(base / "bin"))
    import logging
    logging.basicConfig(level=logging.INFO, filename=str(S / "_anime_tts.log"))
    import anime_tts
    vz = P / "vozes" / voz
    sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/vozes/{voz}", str(vz), "--include", "referencia_fish.*"], 900)
    py, ck = instalar()
    ref15 = P / "ref15.wav"
    # 21/11: referência INTEIRA — cortada em 15 s com o texto inteiro, o Qwen "lia" o resto do texto (repetia frases)
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(vz / "referencia_fish.wav"), "-ac", "1", "-ar", "24000", str(ref15)])
    EMO = [(r"(?i)\b(isso|acert|derrub|venc)", "[excited]"), (r"(?i)(n[aã]o, n[aã]o|morr|levanta)", "[sad]"),
           (r"(?i)(brincadeira|mentira|kkk|haha|respeito|gostos|safad)", "[laughing]"),
           (r"(?i)(n[aã]o aguento|que raiva)", "[frustrated]"), (r"(?i)(ataca|desvia|golpe|soco|luta|avan)", "[excited]")]
    out = P / "audio"; out.mkdir(exist_ok=True)
    tarefas = []
    for i in range(ini, min(fim, len(linhas))):
        t = anime_tts._texto_fish(anime_tts._seguro(linhas[i]))[0]
        emo = next((m_ for p_, m_ in EMO if re.search(p_, t)), "")
        for k in range(2):  # melhor de 2
            tarefas.append({"texto": t, "emo": emo, "seed": 42 + k, "saida": str(out / f"audio_{i}_t{k}.wav"), "i": i})
    tj = P / "tarefas.json"; tj.write_text(json.dumps(tarefas, ensure_ascii=False), encoding="utf-8")
    (P / "gera.py").write_text(GERA, encoding="utf-8")
    t0 = time.time()
    # sobe o que já saiu de 20 em 20 min (a sessão pode acabar antes)
    proc = subprocess.Popen([py, str(P / "gera.py"), "-", str(ref15), str(vz / "referencia_fish.txt"), str(tj)],
                            stdout=open(S / "_gera.log", "w"), stderr=subprocess.STDOUT)
    dest = f"manhwa-drive:colab_recap/qwen3_longo/{vid}_{voz}/audio"
    while proc.poll() is None:
        time.sleep(1200)
        escolher_e_subir(out, ini, fim, b, c, dest)
        log(f"parcial: {len(list(out.glob('audio_*_t1.wav')))} frases em {time.time() - t0:.0f}s")
    escolher_e_subir(out, ini, fim, b, c, dest)
    log(f"gera rc={proc.returncode} {(S / '_gera.log').read_text(errors='ignore')[-1200:]}")
    log(f"{voz} {ini}-{fim}: {len(list(out.glob('audio_*_t0.wav')))} frases em {time.time() - t0:.0f}s")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1", str(S / "video.mp4")])
    log("FIM")


def escolher_e_subir(out, ini, fim, b, c, dest):
    """melhor de 2 por ritmo (letras/s mais perto da mediana das frases) e sobe audio_i.wav escolhido"""
    import statistics
    cps = {}
    for w in out.glob("audio_*_t*.wav"):
        try:
            d = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(w)]).stdout)
            cps[w] = d
        except ValueError:
            pass
    if not cps:
        return
    for i in range(ini, fim):
        ts = [w for w in (out / f"audio_{i}_t0.wav", out / f"audio_{i}_t1.wav") if w in cps]
        if len(ts) < 2 and not (out / f"audio_{i}_t1.wav").exists() and (out / f"audio_{i}_t0.wav").exists():
            continue  # ainda gerando a 2ª
        if not ts:
            continue
        med = statistics.median(cps.values())
        esc = min(ts, key=lambda w: abs(cps[w] - med * 0 - cps[w]) if len(ts) == 1 else abs(cps[w] - statistics.median([cps[x] for x in ts])))
        # com 2 tentativas: fica a de duração menor quando a outra passa de 1,3x (inventou/arrastou)
        if len(ts) == 2:
            a, b2 = cps[ts[0]], cps[ts[1]]
            esc = ts[0] if a <= b2 * 1.3 and (b2 > a * 1.3 or a <= b2) else ts[1]
        fin = out / f"audio_{i}.wav"
        if not fin.exists():
            shutil.copy(esc, fin)
    sh([b, "--config", c, "copy", str(out), dest, "--include", "audio_*[0-9].wav"], 1800)


if __name__ == "__main__":
    main()
