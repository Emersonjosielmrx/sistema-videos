"""Dona 21/11: "veja se OUVE os áudios antes de botar pra eu ouvir". Auditor automático na GPU: pra cada narração
contínua (wav) da pasta, mede antes de ela ouvir:
  - texto: Whisper large-v3 transcreve e compara com o roteiro (palavras faltando = engoliu; sobrando = inventou) ->
    % de acerto (WER invertido) e as frases com problema
  - voz: semelhança (ECAPA) com o trecho real do narrador, em janelas de 3 s -> média e o pior trecho
    ("virou outra pessoa"/voz esquisita = janela com semelhança baixa)
  - tom: f0 por janela -> saltos bruscos (engrossa/afina de repente)
  - ritmo: letras por segundo; silêncio longo; corte/estouro
Entrada: auditar/*.wav + roteiros.json + vozes/<voz>/referencia_fish.wav. Saída: saida/AUDITORIA.md + auditoria.json.
"""
import json, os, re, subprocess, sys, time
from pathlib import Path

P = Path(sys.argv[1]); S = P / "saida"; S.mkdir(exist_ok=True)
LOG = S / "_log.txt"
PK = "/tmp/pkgs_auditor"


def log(m):
    print(m, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")


def sh(a, t=3600):
    return subprocess.run(a, capture_output=True, text=True, timeout=t)


def _rclone():
    import glob
    cands = [str(P.resolve().parents[2] / "rclone")] + glob.glob("/kaggle/tmp/**/rclone", recursive=True)
    bins = [p for p in cands if os.path.isfile(p) and os.access(p, os.X_OK)]
    confs = [c for c in ["/tmp/rclone.conf"] + glob.glob("/kaggle/input/**/rclone.conf", recursive=True)
             if os.path.isfile(c)]
    return (bins[0], confs[0]) if bins and confs else (None, None)


AUD = r'''
import json, re, subprocess, sys, unicodedata
import numpy as np, torch
from faster_whisper import WhisperModel
from speechbrain.inference.speaker import EncoderClassifier
SR = 16000
def ler(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
def norm(t):
    t = unicodedata.normalize("NFKD", t.lower()); t = "".join(c for c in t if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", t)
def wer(ref, hip):
    r, h = norm(ref), norm(hip)
    d = np.zeros((len(r) + 1, len(h) + 1), int); d[:, 0] = range(len(r) + 1); d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i-1, j] + 1, d[i, j-1] + 1, d[i-1, j-1] + (r[i-1] != h[j-1]))
    return d[len(r), len(h)] / max(1, len(r))
import glob, ctypes
for so in glob.glob("/tmp/pkgs_auditor/nvidia/*/lib/*.so*"):  # libcublas/cudnn do pip (o Kaggle não acha a do sistema)
    try: ctypes.CDLL(so)
    except OSError: pass
try:
    wm = WhisperModel("large-v3", device="cuda", compute_type="float16")
    list(wm.transcribe(np.zeros(16000, np.float32), language="pt")[0])
    print("whisper na GPU", flush=True)
except Exception as e:
    print("whisper na CPU:", repr(e)[:200], flush=True)
    wm = WhisperModel("medium", device="cpu", compute_type="int8")
enc = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb", savedir="/tmp/ecapa", run_opts={"device": "cuda" if torch.cuda.is_available() else "cpu"})
def emb(x):
    e = enc.encode_batch(torch.from_numpy(x).unsqueeze(0)).squeeze().detach().cpu().numpy(); return e / (np.linalg.norm(e) + 1e-9)
tarefas = json.load(open(sys.argv[1], encoding="utf-8")); out = []
anc = {}
for t in tarefas:
    a = ler(t["wav"])
    if t["voz"] not in anc:
        anc[t["voz"]] = emb(ler(t["ref"])[:SR * 20])
    segs, _ = wm.transcribe(a, language="pt")
    txt = " ".join(s.text for s in segs)
    roteiro = " ".join(t["linhas"])
    w = wer(roteiro, txt)
    # semelhança da voz por janela de 3 s
    sims = []
    for i in range(0, len(a) - SR * 3, SR * 3):
        x = a[i:i + SR * 3]
        if np.sqrt((x ** 2).mean()) < 0.01: continue
        sims.append(float(np.dot(emb(x), anc[t["voz"]])))
    # tom por janela de 1 s: saltos
    f0 = []
    for i in range(0, len(a) - SR, SR // 2):
        x = a[i:i + SR]; v = []
        for k in range(0, len(x) - 1024, 320):
            fr = x[k:k + 1024] * np.hanning(1024)
            if np.sqrt((fr ** 2).mean()) < 0.02: continue
            c = np.abs(np.fft.irfft(np.log(np.abs(np.fft.rfft(fr, 4096)) + 1e-9)))
            v.append(16000 / (40 + np.argmax(c[40:228])))
        f0.append(float(np.median(v)) if len(v) >= 5 else 0)
    f0v = np.array([x for x in f0 if x])
    med = float(np.median(f0v)) if len(f0v) else 0
    fora = [round(i * 0.5, 1) for i, x in enumerate(f0) if x and med and abs(12 * np.log2(x / med)) > 5]
    env = np.abs(a[:len(a) // 160 * 160]).reshape(-1, 160).mean(1)
    sil, cur = 0, 0
    for v in env < 0.006:
        cur = cur + 1 if v else 0; sil = max(sil, cur)
    n_ponto = len(re.findall(r"(?i)\bponto\b", txt)) - len(re.findall(r"(?i)\bponto\b", roteiro))
    out.append({"pontos_falados": max(0, n_ponto), "arquivo": t["nome"], "voz": t["voz"], "dur_s": round(len(a) / SR, 1), "acerto_texto": round(100 * (1 - w)),
                "voz_media": round(float(np.mean(sims)), 3) if sims else 0, "voz_pior": round(float(np.min(sims)), 3) if sims else 0,
                "voz_pior_em_s": (int(np.argmin(sims)) * 3) if sims else 0,
                "tom_fora_de_5st_em_s": fora[:12], "silencio_max_s": round(sil * 0.01, 2),
                "clip": int((np.abs(a) > 0.99).sum()), "transcricao": txt[:1200]})
    print("ok", t["nome"], out[-1]["acerto_texto"], out[-1]["voz_media"], flush=True)
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
'''


def main():
    roteiros = json.loads((P / "roteiros.json").read_text(encoding="utf-8"))
    b, c = _rclone()
    vz = P / "vozes"
    for v in roteiros:
        if not v.startswith("_"):
            sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/vozes/{v}", str(vz / v), "--include",
                "referencia_fish.wav"], 900)
    os.environ["PYTHONPATH"] = PK
    for pk in ("faster-whisper", "speechbrain", "nvidia-cublas-cu12", "nvidia-cudnn-cu12==9.*"):
        r = sh([sys.executable, "-m", "pip", "install", "-q", "--target", PK, pk], 2400)
        log(f"pip {pk} rc={r.returncode}")
    tarefas = []
    for w in sorted((P / "auditar").glob("*.wav")):
        voz = w.name.split("_")[0]
        if voz in roteiros:
            tarefas.append({"wav": str(w), "nome": w.name, "voz": voz, "ref": str(vz / voz / "referencia_fish.wav"),
                            "linhas": roteiros[voz]})
    (P / "tarefas.json").write_text(json.dumps(tarefas, ensure_ascii=False), encoding="utf-8")
    (P / "aud.py").write_text(AUD, encoding="utf-8")
    r = sh([sys.executable, str(P / "aud.py"), str(P / "tarefas.json"), str(S / "auditoria.json")], 6 * 3600)
    log(f"auditor rc={r.returncode} {r.stderr[-1500:]}")
    if (S / "auditoria.json").exists():
        A = json.loads((S / "auditoria.json").read_text(encoding="utf-8"))
        md = ["# Auditoria automática (texto, voz, tom)", "",
              "| arquivo | dur | texto certo | falou 'ponto' | voz (média/pior) | pior trecho em | tom fora (s) | silêncio máx |",
              "|---|---:|---:|---:|---|---:|---|---:|"]
        for x in sorted(A, key=lambda x: (x["voz"], -x["acerto_texto"])):
            md.append(f"| {x['arquivo']} | {x['dur_s']} | {x['acerto_texto']}% | {x.get('pontos_falados', 0)} | {x['voz_media']}/{x['voz_pior']} | "
                      f"{x['voz_pior_em_s']} s | {x['tom_fora_de_5st_em_s'][:6]} | {x['silencio_max_s']} |")
        (S / "AUDITORIA.md").write_text("\n".join(md), encoding="utf-8")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1", str(S / "video.mp4")])
    log("FIM")


if __name__ == "__main__":
    main()
