"""Dona 21/11: "analise todas as formas possíveis de fazer o Drama 3 rodar no Kaggle — comprimindo, dividindo, parte no
Drive". Análise: o oficial (FP8, 37 GB) e os int4 oficiais/da comunidade (GPTQ-Marlin / bsgemm-moe) exigem placa
Ampere (sm80+); a T4 é sm75 -> não rodam. O caminho que sobra: llama.cpp (CUDA roda na T4) + GGUF Q4_K_M (20,6 GB)
do ggml-org, que o llama-tts suporta COM clonagem (--tts-speaker-file + --tts-speaker-text). Os 20,6 GB não cabem numa
T4 (15 GB), mas o Kaggle dá DUAS T4 (2 x 15 GB) e ~30 GB de RAM; e o Drama 3 é MoE (35B no total, só 3B ativos por
palavra) — então dá pra:
  A) dividir entre as 2 GPUs  (-ngl 999 --tensor-split 1,1)
  B) deixar os "especialistas" (experts) do MoE na RAM e o resto na GPU  (--n-cpu-moe N / -ot exps=CPU)
  C) as duas coisas
Este job tenta A, depois B, depois C, mede o tempo de 1 frase em cada e usa o primeiro que der certo pro roteiro todo
(versões limpa e melhor de 2). Também gera o S2-Pro pelo mesmo llama.cpp (cabe numa T4 e deve ser bem mais rápido
que os 100 s/frase do fish_speech). plano.json: {"modelos": ["drama3", "s2pro"]}.
"""
import json, os, re, shutil, subprocess, sys, time
from pathlib import Path

P = Path(sys.argv[1]); S = P / "saida"; S.mkdir(exist_ok=True)
LOG = S / "_log.txt"
LC = Path("/tmp/llama.cpp")


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


def compilar():
    tts = LC / "build" / "bin" / "llama-tts"
    if tts.exists():
        return tts
    if not LC.exists():
        sh(["git", "clone", "-q", "--depth", "1", "https://github.com/ggml-org/llama.cpp.git", str(LC)], 900)
    # 21/11 (1ª tentativa: "cannot find -lCUDA::cuda_driver"): o Kaggle não tem a libcuda de desenvolvimento no
    # caminho do cmake — aponta pro stub do toolkit (o driver de verdade é carregado na hora de rodar)
    stub = next((str(x) for x in Path("/usr/local/cuda/lib64/stubs").glob("libcuda.so")), "")
    os.environ["LIBRARY_PATH"] = "/usr/local/cuda/lib64/stubs:" + os.environ.get("LIBRARY_PATH", "")
    r = sh(["cmake", "-B", "build", "-DGGML_CUDA=ON", "-DCMAKE_CUDA_ARCHITECTURES=75", "-DLLAMA_CURL=OFF",
            "-DCMAKE_BUILD_TYPE=Release", "-DGGML_CUDA_NO_VMM=ON",
            f"-DCUDA_cuda_driver_LIBRARY={stub}" if stub else "-DGGML_CUDA_NO_VMM=ON"], 1800, cwd=str(LC))
    log(f"cmake rc={r.returncode} {r.stderr[-400:]}")
    r = sh(["cmake", "--build", "build", "--config", "Release", "-j", "4", "--target", "llama-tts"], 5400, cwd=str(LC))
    log(f"build rc={r.returncode} {r.stderr[-600:]}")
    return tts if tts.exists() else None


def baixar(repo, padrao):
    d = Path(f"/tmp/gguf/{repo.replace('/', '_')}")
    d.mkdir(parents=True, exist_ok=True)
    r = sh([sys.executable, "-c", "from huggingface_hub import snapshot_download as s; "
            f"print(s({repo!r}, local_dir={str(d)!r}, allow_patterns={padrao!r}))"], 5400)
    arqs = sorted(p for p in d.rglob("*.gguf"))
    log(f"baixar {repo} {padrao}: {[f'{p.name} {p.stat().st_size / 1e9:.1f}GB' for p in arqs]} {r.stderr[-200:]}")
    return arqs


def falar(tts, modelo, extras, texto, ref, reftxt, saida, seed, t=900):
    if "drama" in str(modelo[0]).lower() and not texto.startswith("<|speaker"):
        texto = "<|speaker:0|> " + texto
    cmd = [str(tts), "-m", str(modelo[0]), "-p", texto, "--output", str(saida), "--tts-speaker-file", str(ref),
           "--tts-speaker-text", reftxt, "--seed", str(seed)] + extras
    for m in modelo[1:]:  # 21/11: o codec vem no mmproj (-mm), doc do llama.cpp
        if "mmproj" in m.name:
            cmd += ["-mm", str(m)]
    cmd += ["-n", "1000"]
    t0 = time.time()
    r = sh(cmd, t)
    return Path(saida).exists() and Path(saida).stat().st_size > 2000, time.time() - t0, (r.stdout + r.stderr)[-800:]


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
    """21/11: longo S2-Pro em pedaços pelo llama.cpp (o caminho que funcionou: ~13 s/frase)."""
    plano = json.loads((P / "plano.json").read_text(encoding="utf-8"))
    voz, vid, ini, fim = plano["voz"], plano["vid"], plano["inicio"], plano["fim"]
    linhas = (P / "roteiro.txt").read_text(encoding="utf-8").splitlines()
    b, c = _rclone()
    base = P / "prod"
    for parte in ("bin", "config"):
        sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/raiz/D/recapd-ambientes/producao/{parte}",
            str(base / parte)], 1800)
    sys.path.insert(0, str(base / "bin"))
    import anime_tts
    vz = P / "vozes" / voz
    sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/vozes/{voz}", str(vz), "--include", "referencia_fish.*"], 900)
    sh([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub[hf_transfer]"], 900)
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    tts = compilar()
    if not tts:
        log("llama.cpp não compilou"); return
    arqs = baixar("ggml-org/s2-pro-GGUF", ["*Q8_0*", "*mmproj*"])
    principal = max(arqs, key=lambda p: p.stat().st_size)
    modelo = [principal] + [p for p in arqs if p != principal]
    ref15 = P / "ref15.wav"
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(vz / "referencia_fish.wav"), "-t", "15", "-ac", "1", "-ar", "24000", str(ref15)])
    tt = (vz / "referencia_fish.txt").read_text(encoding="utf-8").split()
    import wave
    with wave.open(str(vz / "referencia_fish.wav")) as f_:
        dtot = f_.getnframes() / f_.getframerate()
    reftxt = " ".join(tt[:max(4, int(len(tt) * min(1.0, 15 / dtot)))])
    EMO = [(r"(?i)(isso|acert|derrub|venc)", "[excited]"), (r"(?i)(n[aã]o, n[aã]o|morr|levanta)", "[sad]"),
           (r"(?i)(brincadeira|mentira|respeito|gostos|safad)", "[laughing]"), (r"(?i)(ataca|golpe|soco|luta)", "[excited]")]
    out = P / "audio"; out.mkdir(exist_ok=True)
    dest = f"manhwa-drive:colab_recap/s2pro_longo/{vid}_{voz}/audio"
    t0 = time.time(); feitos = 0
    for i in range(ini, min(fim, len(linhas))):
        t = anime_tts._texto_fish(anime_tts._seguro(linhas[i]))[0]
        tag = next((m_ for p_, m_ in EMO if re.search(p_, t)), "")
        best = None
        for k in range(2):
            w = out / f"audio_{i}_t{k}.wav"
            ok, dt, _ = falar(tts, modelo, ["-ngl", "999", "--tensor-split", "1,1"], (tag + " " + t).strip(), ref15,
                              reftxt, w, 42 + k)
            if ok:
                d = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(w)]).stdout or 0)
                pena = abs(len(t) / max(d, 0.1) - 17)
                if best is None or pena < best[0]:
                    best = (pena, w)
        if best:
            shutil.copy(best[1], out / f"audio_{i}.wav"); feitos += 1
        if feitos and feitos % 15 == 0:
            sh([b, "--config", c, "copy", str(out), dest, "--include", "audio_*[0-9].wav"], 1800)
    sh([b, "--config", c, "copy", str(out), dest, "--include", "audio_*[0-9].wav"], 1800)
    log(f"{voz} {ini}-{fim}: {feitos} frases em {time.time() - t0:.0f}s")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1", str(S / "video.mp4")])
    log("FIM")


if __name__ == "__main__":
    main()
