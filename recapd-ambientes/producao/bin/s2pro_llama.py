"""s2pro_llama.py — S2-Pro (Fish Audio, 4B) pelo llama.cpp na GPU do Kaggle (dona 21-22/11).

Por que existe: o S2-Pro é o único dos nossos motores que RI e muda de emoção de verdade, mas pelo fish_speech leva
~130 s/frase. Pelo llama.cpp (GGUF Q8 + codec no mmproj) caiu pra ~13-15 s/frase na mesma T4, mesma qualidade.
É usado em 2 lugares:
  - produção (anime_tts._narrar_s2pro): modo MISTO (XTTS 8 nas frases normais, S2-Pro nas de emoção) e modo PRO
    (S2-Pro em tudo). Liga por longo_override {"s2pro": "misto"|"pro", "s2pro_versao": "2"..}.
  - testes de versão (job_s2pro_versoes.py).

    python s2pro_llama.py lote <lista.json>
lista = [{"texto", "saida", "ref", "reftxt", "tag", "n", "seed", "cps_alvo", "versao"}]; grava wav por item.

Versões (todas com o S2-Pro carregado pelo llama-tts; a 1 e a 2 são as que a dona já ouviu):
  1  limpa: 1 tentativa, referência 15 s, sem etiqueta
  2  (a do longo 82ge) etiqueta de emoção pelo texto + melhor de 2 pelo ritmo (17 letras/s fixo)
     defeito ouvido pela dona 22/11: "voz desanimada e termina toda frase esticando a última letra"
  3  2 + ritmo-alvo MEDIDO na referência do narrador (não 17 fixo) + corta cauda esticada (última sílaba > 1,6x
     a média) — lição do Fish (CPS_REF) e do XTTS (microcortes)
  4  3 + etiqueta [excited]/[confident] nas frases NORMAIS também (narrador real é animado o vídeo todo) + melhor de 3
  5  4 + nota do Whisper no melhor de 3 (corta palavra engolida/inventada) — lição da XTTS 9
  6  5 + referência longa (30 s) com o texto inteiro — lição do Qwen3 (cortar a referência fazia repetir/achatar)
"""
import json, os, re, subprocess, sys, time
from pathlib import Path

LC = Path(os.environ.get("LLAMA_CPP_DIR", "/tmp/llama.cpp"))
GGUF = Path(os.environ.get("S2PRO_GGUF_DIR", "/tmp/gguf/s2pro"))


def log(m):
    print(m, flush=True)


def sh(a, t=3600, cwd=None, env=None):
    return subprocess.run(a, capture_output=True, text=True, timeout=t, cwd=cwd, env=env)



_CACHE_DRIVE = "manhwa-drive:colab_recap/cache/llama_tts_build_sm75.tar.gz"


def _rclone():
    import glob
    cands = glob.glob("/kaggle/tmp/**/rclone", recursive=True) + glob.glob("/kaggle/working/**/rclone", recursive=True)
    rcl = next((x for x in cands if os.access(x, os.X_OK)), None)
    conf = next((c for c in ["/tmp/rclone.conf"] + glob.glob("/kaggle/input/**/rclone.conf", recursive=True)
                 if os.path.isfile(c)), None)
    return (rcl, conf) if rcl and conf else (None, None)


def _cache_baixar():
    """22/11: build pronto do Drive (sm75 = T4). Só vale se o llama-tts roda (--help) — senão cai pra compilação."""
    try:
        rcl, conf = _rclone()
        if not rcl:
            return False
        tmp = Path("/tmp/_llama_cache"); tmp.mkdir(exist_ok=True)
        r = sh([rcl, "--config", conf, "copyto", _CACHE_DRIVE, str(tmp / "b.tar.gz")], 1800)
        if r.returncode or not (tmp / "b.tar.gz").exists():
            return False
        (LC / "build").mkdir(parents=True, exist_ok=True)
        sh(["tar", "-xzf", str(tmp / "b.tar.gz"), "-C", str(LC / "build")], 1800)
        tts = LC / "build" / "bin" / "llama-tts"
        if not tts.exists():
            return False
        os.chmod(tts, 0o755)
        ok = sh([str(tts), "--help"], 120)
        log(f"s2pro: build pronto do Drive rc={ok.returncode}")
        return ok.returncode == 0 or "usage" in ((ok.stdout or "") + (ok.stderr or "")).lower()
    except Exception as e:  # noqa: BLE001
        log(f"s2pro: cache do build falhou ({type(e).__name__})")
        return False


def _cache_subir():
    try:
        rcl, conf = _rclone()
        if not rcl:
            return
        tmp = Path("/tmp/_llama_cache"); tmp.mkdir(exist_ok=True)
        sh(["tar", "-czf", str(tmp / "b.tar.gz"), "-C", str(LC / "build"), "bin"], 1800)
        r = sh([rcl, "--config", conf, "copyto", str(tmp / "b.tar.gz"), _CACHE_DRIVE], 3600)
        log(f"s2pro: build subido pro Drive rc={r.returncode}")
    except Exception as e:  # noqa: BLE001
        log(f"s2pro: não subiu o cache do build ({type(e).__name__})")


def compilar():
    """llama-tts com CUDA pra T4 (sm75). 1x por sessão (~30 min). Devolve o caminho ou None."""
    tts = LC / "build" / "bin" / "llama-tts"
    if tts.exists():
        return tts
    if _cache_baixar() and tts.exists():
        return tts
    if not LC.exists():
        sh(["git", "clone", "-q", "--depth", "1", "https://github.com/ggml-org/llama.cpp.git", str(LC)], 900)
    # 21/11: o Kaggle não tem a libcuda de desenvolvimento -> stub do toolkit (o driver real carrega na hora de rodar)
    stub = next((str(x) for x in Path("/usr/local/cuda/lib64/stubs").glob("libcuda.so")), "")
    os.environ["LIBRARY_PATH"] = "/usr/local/cuda/lib64/stubs:" + os.environ.get("LIBRARY_PATH", "")
    r = sh(["cmake", "-B", "build", "-DGGML_CUDA=ON", "-DCMAKE_CUDA_ARCHITECTURES=75", "-DLLAMA_CURL=OFF",
            "-DCMAKE_BUILD_TYPE=Release", "-DGGML_CUDA_NO_VMM=ON"]
           + ([f"-DCUDA_cuda_driver_LIBRARY={stub}"] if stub else []), 1800, cwd=str(LC))
    log(f"s2pro: cmake rc={r.returncode} {r.stderr[-300:]}")
    r = sh(["cmake", "--build", "build", "--config", "Release", "-j", "4", "--target", "llama-tts"], 5400, cwd=str(LC))
    log(f"s2pro: build rc={r.returncode} {r.stderr[-300:]}")
    if tts.exists():
        _cache_subir()
    return tts if tts.exists() else None


def baixar():
    """GGUF Q8 do S2-Pro + mmproj (codec). Devolve [modelo, mmproj] ou []."""
    GGUF.mkdir(parents=True, exist_ok=True)
    arqs = sorted(GGUF.rglob("*.gguf"))
    if len(arqs) < 2:
        sh([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub[hf_transfer]"], 900)
        env = {**os.environ, "HF_HUB_ENABLE_HF_TRANSFER": "1"}
        r = sh([sys.executable, "-c", "from huggingface_hub import snapshot_download as s; "
                f"s('ggml-org/s2-pro-GGUF', local_dir={str(GGUF)!r}, allow_patterns=['*Q8_0*', '*mmproj*'])"],
               5400, env=env)
        if r.returncode:  # sem hf_transfer: baixa normal
            sh([sys.executable, "-c", "from huggingface_hub import snapshot_download as s; "
                f"s('ggml-org/s2-pro-GGUF', local_dir={str(GGUF)!r}, allow_patterns=['*Q8_0*', '*mmproj*'])"],
               5400, env={**os.environ, "HF_HUB_ENABLE_HF_TRANSFER": "0"})
        arqs = sorted(GGUF.rglob("*.gguf"))
    if not arqs:
        return []
    pr = max((a for a in arqs if "mmproj" not in a.name), key=lambda p: p.stat().st_size, default=None)
    mm = next((a for a in arqs if "mmproj" in a.name), None)
    return [pr, mm] if pr and mm else []


def falar(tts, modelo, texto, ref, reftxt, saida, seed, extras=None, t=900):
    cmd = [str(tts), "-m", str(modelo[0]), "-mm", str(modelo[1]), "-p", texto, "--output", str(saida),
           "--tts-speaker-file", str(ref), "--tts-speaker-text", reftxt, "--seed", str(seed), "-ngl", "999",
           "-n", "1500"] + list(extras or [])
    t0 = time.time()
    try:
        r = sh(cmd, t)
        out = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"
    ok = Path(saida).exists() and Path(saida).stat().st_size > 2000
    return ok, time.time() - t0, out[-600:]


def _expressividade(a, sr):
    """22/11 v13: variação da energia (desvio/média em janelas de 50 ms, só trechos com voz) — voz reta/triste dá pouco."""
    import numpy as np
    win = int(0.05 * sr)
    if len(a) < win * 10:
        return 0.0
    env = np.array([np.sqrt(np.mean(a[k:k + win] ** 2)) for k in range(0, len(a) - win, win)])
    env = env[env > 0.25 * np.percentile(env, 80)]
    return float(np.std(env) / (np.mean(env) + 1e-9)) if len(env) > 5 else 0.0


def _ler(w):
    import numpy as np, soundfile as sf
    a, sr = sf.read(str(w), dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    return a, sr


def _cauda_esticada(a, sr):
    """22/11 (dona: "termina toda frase estendendo a última letra"): mede a energia em janelas de 20 ms; a última
    'ilha' de voz antes do silêncio final é a última sílaba. Se ela durar mais que 1,6x a média das sílabas, corta
    o excesso com fade. Devolve (áudio, segundos cortados)."""
    import numpy as np
    win = int(0.02 * sr)
    if len(a) < win * 20:
        return a, 0.0
    env = np.array([np.sqrt(np.mean(a[i:i + win] ** 2)) for i in range(0, len(a) - win, win)])
    lim = max(0.02, float(np.percentile(env, 70)) * 0.25)
    voz = env > lim
    # ilhas de voz (sílabas aproximadas)
    ilhas, ini = [], None
    for k, v in enumerate(voz):
        if v and ini is None:
            ini = k
        elif not v and ini is not None:
            if k - ini >= 3:
                ilhas.append((ini, k))
            ini = None
    if ini is not None:
        ilhas.append((ini, len(voz)))
    if len(ilhas) < 4:
        return a, 0.0
    durs = [b - x for x, b in ilhas[:-1]]
    media = float(np.median(durs))
    x0, x1 = ilhas[-1]
    if (x1 - x0) <= 1.6 * media or (x1 - x0) * 0.02 < 0.25:
        return a, 0.0
    novo_fim = x0 + int(1.3 * media)
    corte = (x1 - novo_fim) * 0.02
    fim_amostra = novo_fim * win
    b = a[:fim_amostra].copy()
    fade = min(len(b), int(0.06 * sr))
    b[-fade:] *= np.linspace(1, 0, fade)
    return np.concatenate([b, np.zeros(int(0.15 * sr), np.float32)]), corte


_WM = []


def _wer(texto, w):
    try:
        import numpy as np, unicodedata
        if not _WM:
            from faster_whisper import WhisperModel
            try:
                _WM.append(WhisperModel("small", device="cuda", compute_type="float16"))
            except Exception:  # noqa: BLE001
                _WM.append(WhisperModel("small", device="cpu", compute_type="int8"))

        def norm(t):
            t = unicodedata.normalize("NFKD", t.lower()); t = "".join(c for c in t if not unicodedata.combining(c))
            return re.findall(r"[a-z0-9]+", t)
        segs, _ = _WM[0].transcribe(str(w), language="pt")
        h, r = norm(" ".join(s.text for s in segs)), norm(texto)
        d = np.zeros((len(r) + 1, len(h) + 1), int); d[:, 0] = range(len(r) + 1); d[0, :] = range(len(h) + 1)
        for i in range(1, len(r) + 1):
            for j in range(1, len(h) + 1):
                d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
        return d[len(r), len(h)] / max(1, len(r))
    except Exception:  # noqa: BLE001
        return 0.0


def lote(lista_json):
    import numpy as np, soundfile as sf
    itens = json.loads(Path(lista_json).read_text(encoding="utf-8"))
    tts = compilar()
    if not tts:
        log("S2PRO FALHOU: llama.cpp não compilou"); return 1
    modelo = baixar()
    if not modelo:
        log("S2PRO FALHOU: modelo não baixou"); return 1
    ok_n = 0
    for it in itens:
        if Path(it["saida"]).exists():
            ok_n += 1
            continue
        t0 = time.time()
        texto = ((it.get("tag") or "") + " " + (it.get("texto_tags") or it["texto"])).strip()
        if it.get("texto_tags"):
            texto = it["texto_tags"]  # v13: as tags já vão dentro da frase
        cand = []
        if it.get("partes"):
            # 22/11 v8+: pergunta retórica — afirmação e pergunta geradas separadas, 0,55 s de pausa entre elas
            pedacos = []
            for j, pt in enumerate(it["partes"]):
                wj = Path(it["saida"] + f".p{j}.wav")
                tg = (it.get("tag") or "") if j == 0 else "[curious]"
                ok, dt, _ = falar(tts, modelo, (tg + " " + pt).strip(), it["ref"], it["reftxt"], wj, int(it.get("seed", 42)))
                if ok:
                    a, sr = _ler(wj)
                    a, _c = _cauda_esticada(a, sr)
                    pedacos.append((a, sr))
                    wj.unlink(missing_ok=True)
            if len(pedacos) == len(it["partes"]):
                import numpy as np
                sr = pedacos[0][1]
                juntos = np.concatenate([pedacos[0][0], np.zeros(int(0.55 * sr), np.float32), pedacos[1][0]])
                sf.write(it["saida"], juntos, sr)
                ok_n += 1
                log(f"S2PRO ok {time.time() - t0:.1f}s pergunta_retorica {Path(it['saida']).name}")
                continue
        for k in range(int(it.get("n", 1))):
            w = Path(it["saida"] + f".t{k}.wav")
            ok, dt, saida = falar(tts, modelo, texto, it["ref"], it["reftxt"], w, int(it.get("seed", 42)) + k)
            if not ok:
                log(f"S2PRO tentativa falhou {Path(it['saida']).name}: {saida[-200:]}")
                continue
            a, sr = _ler(w)
            corte = 0.0
            if str(it.get("versao", "2")) not in ("1", "2"):
                a, corte = _cauda_esticada(a, sr)
                sf.write(str(w), a, sr)
            cps = len(it["texto"]) / max(len(a) / sr, 0.1)
            pena = abs(cps - float(it.get("cps_alvo") or 17)) / max(1.0, float(it.get("cps_alvo") or 17))
            if it.get("whisper"):
                pena += 2 * _wer(it["texto"], w)
            if str(it.get("versao")) == "13":
                pena -= 0.4 * _expressividade(a, sr)  # v13: prefere a tentativa mais animada (variação de energia)
            cand.append((pena, w, corte))
        if cand:
            pena, w, corte = min(cand, key=lambda x: x[0])
            os.replace(w, it["saida"])
            for _, w2, _ in cand:
                Path(w2).unlink(missing_ok=True)
            ok_n += 1
            log(f"S2PRO ok {time.time() - t0:.1f}s n={len(cand)} cauda_cortada={corte:.2f}s {Path(it['saida']).name}")
    log(f"S2PRO fim {ok_n}/{len(itens)}")
    return 0 if ok_n == len(itens) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["lote"]:
        sys.exit(lote(sys.argv[2]))
    print(__doc__)
    sys.exit(1)
