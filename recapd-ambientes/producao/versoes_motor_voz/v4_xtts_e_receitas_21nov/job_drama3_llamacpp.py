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
    r = sh(["cmake", "-B", "build", "-DGGML_CUDA=ON", "-DCMAKE_CUDA_ARCHITECTURES=75", "-DLLAMA_CURL=ON",
            "-DCMAKE_BUILD_TYPE=Release"], 1800, cwd=str(LC))
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
    cmd = [str(tts), "-m", str(modelo[0]), "-p", texto, "--output", str(saida), "--tts-speaker-file", str(ref),
           "--tts-speaker-text", reftxt, "--seed", str(seed)] + extras
    for m in modelo[1:]:  # codec/vocoder separado, se o repositório tiver
        cmd += ["-mv", str(m)]
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
    plano = json.loads((P / "plano.json").read_text(encoding="utf-8"))
    roteiros = json.loads((P / "roteiros.json").read_text(encoding="utf-8"))
    b, c = _rclone()
    vz = P / "vozes"
    vozes = [v for v in roteiros if not v.startswith("_")]
    for v in vozes:
        sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/vozes/{v}", str(vz / v), "--include",
            "referencia_fish.*"], 900)
    sh([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub[hf_transfer]"], 900)
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    log(sh(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv"]).stdout.strip())
    log(sh(["free", "-g"]).stdout.strip())
    tts = compilar()
    if not tts:
        log("llama.cpp não compilou — FIM")
        sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1", str(S / "video.mp4")])
        return
    alvos = {"drama3": ("ggml-org/drama-3-GGUF", ["*Q4_K_M*", "*codec*", "*decoder*", "*vocoder*", "*mmproj*"]),
             "s2pro": ("ggml-org/s2-pro-GGUF", ["*Q8_0*", "*codec*", "*decoder*", "*vocoder*", "*mmproj*"])}
    # A) 2 GPUs  B) experts na RAM  C) as duas
    jeitos = [("A_duas_GPUs", ["-ngl", "999", "--tensor-split", "1,1"]),
              ("B_experts_na_RAM", ["-ngl", "999", "--n-cpu-moe", "40"]),
              ("C_duas_GPUs_e_experts_na_RAM", ["-ngl", "999", "--tensor-split", "1,1", "--n-cpu-moe", "20"]),
              ("D_so_uma_GPU", ["-ngl", "999"])]
    for nome in plano.get("modelos", ["drama3"]):
        repo, pad = alvos[nome]
        arqs = baixar(repo, pad)
        if not arqs:
            continue
        principal = max(arqs, key=lambda p: p.stat().st_size)
        modelo = [principal] + [p for p in arqs if p != principal]
        voz0 = vozes[0]
        ref = vz / voz0 / "referencia_fish.wav"
        ref15 = vz / voz0 / "ref15.wav"
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(ref), "-t", "15", "-ac", "1", "-ar", "24000", str(ref15)])
        reftxt = (vz / voz0 / "referencia_fish.txt").read_text(encoding="utf-8").strip()
        escolhido = None
        for jn, ex in jeitos:
            ok, dt, saida = falar(tts, modelo, ex, roteiros[voz0][1], ref15, reftxt, P / f"prova_{nome}_{jn}.wav", 1)
            log(f"{nome} {jn}: {'OK' if ok else 'falhou'} em {dt:.0f}s {'' if ok else saida[-400:]}")
            if ok:
                escolhido = ex
                break
        if not escolhido:
            continue
        for voz in vozes:
            ref = vz / voz / "referencia_fish.wav"
            ref15 = vz / voz / "ref15.wav"
            sh(["ffmpeg", "-v", "error", "-y", "-i", str(ref), "-t", "15", "-ac", "1", "-ar", "24000", str(ref15)])
            reftxt = (vz / voz / "referencia_fish.txt").read_text(encoding="utf-8").strip()
            for versao, tent in (("1_limpa", 1), ("2_melhor_de_2", 2)):
                ws = []
                for i, t in enumerate(roteiros[voz]):
                    best = None
                    for k in range(tent):
                        w = P / "trab" / f"{voz}_{nome}_{versao}_{i:02d}_{k}.wav"
                        w.parent.mkdir(parents=True, exist_ok=True)
                        ok, dt, _ = falar(tts, modelo, escolhido, t, ref15, reftxt, w, 42 + k)
                        if ok:
                            d = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                          "csv=p=0", str(w)]).stdout or 0)
                            cps = len(t) / max(d, 0.1)
                            pena = abs(cps - 17)  # ritmo normal de narração ~17 letras/s
                            if best is None or pena < best[0]:
                                best = (pena, w)
                    if best:
                        ws.append(best[1])
                log(f"{voz} {nome} {versao}: {len(ws)}/18 frases")
                if ws:
                    juntar(ws, S / f"{voz}_{nome}_llamacpp_{versao}.wav")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1", str(S / "video.mp4")])
    log("FIM")


if __name__ == "__main__":
    main()
