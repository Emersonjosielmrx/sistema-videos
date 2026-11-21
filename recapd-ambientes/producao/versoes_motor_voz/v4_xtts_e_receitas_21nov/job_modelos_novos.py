"""Dona 20/11 noite: "agora vamos testar os novos modelos também, com os Kaggles". O nosso Fish é o 1.5 (2024); a
Fish lançou depois OpenAudio S1-mini (0,5B), S2-Pro (5B, mar/2026) e Drama 3 (35B MoE). Aqui: o mesmo roteiro do gol
(18 frases) com o mesmo trecho real do narrador como referência, em:
  N1_S1mini            S1-mini, texto puro
  N2_S1mini_emocao     S1-mini com marcadores de emoção por tipo de frase ((excited) no gol, (laughing) na piada...)
  N3_S2pro             S2-Pro (--half, T4 sem bf16), texto puro
  N4_S2pro_emocao      S2-Pro com tags [excited] [laughing] [sad] [whisper]...
Sem pós nenhum (pra ouvir o modelo cru). Cada frase gerada 1x; junta com 0,35 s entre elas.
Saída: saida/<voz>_<N>.wav + _log.txt + video.mp4. Modelo que não instala/não cabe = registra o erro e segue.
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
    r = subprocess.run(a, capture_output=True, text=True, timeout=t, cwd=cwd)
    return r


def _rclone():
    import glob
    cands = [str(P.resolve().parents[2] / "rclone")] + glob.glob("/kaggle/tmp/**/rclone", recursive=True)
    bins = [p for p in cands if os.path.isfile(p) and os.access(p, os.X_OK)]
    confs = [c for c in ["/tmp/rclone.conf"] + glob.glob("/kaggle/input/**/rclone.conf", recursive=True)
             if os.path.isfile(c)]
    return (bins[0], confs[0]) if bins and confs else (None, None)


def instalar():
    py = FV / "bin" / "python"
    if not FS.exists():
        r = sh(["git", "clone", "-q", "--depth", "1", "https://github.com/fishaudio/fish-speech.git", str(FS)], 900)
        log(f"clone main rc={r.returncode} {r.stderr[-200:]}")
    if not py.exists():
        sh(["bash", "-c", "apt-get update -qq && apt-get install -y -qq portaudio19-dev libsox-dev ffmpeg"], 900)
        # 20/11 (1ª rodada: "uv not found" — o python do job é o do Applio): uv solto em /tmp/uvbin
        uv = "/tmp/uvbin/uv"
        if not os.path.exists(uv):
            sh(["bash", "-c", "mkdir -p /tmp/uvbin && pip install -q --target /tmp/uvpkg uv && "
                "cp $(find /tmp/uvpkg -name uv -type f -path '*bin*' | head -1) /tmp/uvbin/uv && chmod +x /tmp/uvbin/uv "
                "|| (curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/tmp/uvbin sh)"], 900)
        log(f"uv: {os.path.exists(uv)}")
        r = sh([uv, "venv", "--python", "3.12", str(FV)], 900)
        if r.returncode:
            sh([uv, "venv", "--python", "3.11", str(FV)], 900)
        r = sh([uv, "pip", "install", "--python", str(py), "-e", str(FS) + "[cu126]", "huggingface_hub"], 3600)
        if r.returncode:
            r = sh([uv, "pip", "install", "--python", str(py), "-e", str(FS), "huggingface_hub"], 3600)
        log(f"pip fish novo rc={r.returncode} {r.stderr[-400:]}")
    v = sh([str(py), "-c", "import torch,fish_speech;print(torch.__version__, torch.cuda.is_available())"], 300)
    log(f"fish novo: {v.stdout.strip()} {v.stderr[-300:]}")
    return str(py)


def baixar(py, repo, nome):
    ck = FS / "checkpoints" / nome
    if not any(ck.glob("*")):
        r = sh([py, "-c", f"from huggingface_hub import snapshot_download as d; d('{repo}', local_dir={str(ck)!r})"],
               3600)
        log(f"baixar {repo} rc={r.returncode} {r.stderr[-300:]}")
    log(f"{nome}: {sorted(p.name for p in ck.glob('*'))[:12]}")
    return ck


EMO_S1 = [(r"(?i)\b(isso|acert|derrub|venc)", "(excited)"), (r"(?i)(n[aã]o, n[aã]o|morr|levanta)", "(sad)"),
          (r"(?i)(kkk|haha|brincadeira|mentira|particulares|cen[aá]rio|respeito)", "(amused)"),
          (r"(?i)(n[aã]o aguento)", "(frustrated)"), (r"(?i)(ataca|desvia|abaixa|gira|segura|avan)", "(excited)")]
EMO_S2 = [(r"(?i)\b(isso|acert|derrub|venc)", "[excited]"), (r"(?i)(n[aã]o, n[aã]o|morr|levanta)", "[sad]"),
          (r"(?i)(brincadeira|mentira|particulares|cen[aá]rio|respeito)", "[laughing]"),
          (r"(?i)(n[aã]o aguento)", "[frustrated]"), (r"(?i)(ataca|desvia|abaixa|gira|segura|avan)", "[excited]")]


def com_emocao(t, tabela):
    for p, m in tabela:
        if re.search(p, t):
            return f"{m} {t}"
    return t


def gerar(py, ck, ref_wav, ref_txt, linhas, saida_dir, s2, tentativas=1):
    aceitas = []
    """pipeline da doc (speech.fish.audio/inference): codec da referência -> text2semantic -> codec decode"""
    saida_dir.mkdir(parents=True, exist_ok=True)
    codec = next((p for p in ck.glob("*.pth") if "codec" in p.name or "firefly" in p.name or "decoder" in p.name), None)
    if not codec:
        log(f"  sem codec em {ck}")
        return []
    enc = sh([py, "fish_speech/models/dac/inference.py", "-i", str(ref_wav), "--checkpoint-path", str(codec)],
             1800, cwd=str(FS))
    npy = FS / "fake.npy"
    if not npy.exists() and (FS / "output" / "fake.npy").exists():
        npy = FS / "output" / "fake.npy"
    if not npy.exists():
        log(f"  codec da referência falhou: {(enc.stdout + enc.stderr)[-600:]}")
        return []
    ref_npy = saida_dir / "ref.npy"
    shutil.move(str(npy), ref_npy)
    out = []
    for i, t in enumerate(linhas):
        for f in FS.glob("temp/codes_*.npy"):
            f.unlink()
        for f in FS.glob("codes_*.npy"):
            f.unlink()
        tent = []
        for k in range(tentativas):
            for f in list(FS.glob("output/codes_*.npy")) + list(FS.glob("temp/codes_*.npy")) + list(FS.glob("codes_*.npy")):
                f.unlink()
            cmd = [py, "fish_speech/models/text2semantic/inference.py", "--text", t, "--prompt-text", ref_txt,
                   "--prompt-tokens", str(ref_npy), "--checkpoint-path", str(ck), "--half", "--seed", str(42 + k)]
            r = sh(cmd, 900, cwd=str(FS))
            codes = sorted(FS.glob("output/codes_*.npy")) + sorted(FS.glob("temp/codes_*.npy")) + sorted(FS.glob("codes_*.npy"))
            if not codes:
                log(f"  frase {i}: text2semantic falhou: {(r.stdout + r.stderr)[-500:]}")
                break
            d = sh([py, "fish_speech/models/dac/inference.py", "-i", str(codes[0]), "--checkpoint-path", str(codec)],
                   900, cwd=str(FS))
            w = FS / "fake.wav"
            if not w.exists() and (FS / "output" / "fake.wav").exists():
                w = FS / "output" / "fake.wav"
            if not w.exists():
                log(f"  frase {i}: decode falhou {(d.stdout + d.stderr)[-300:]}")
                break
            dst = saida_dir / f"audio_{i:02d}_t{k}.wav"
            shutil.move(str(w), dst)
            tent.append(dst)
        if not tent:
            continue
        final = saida_dir / f"audio_{i:02d}.wav"
        shutil.copy(escolher(tent, t, aceitas), final)
        out.append(final)
    return out


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
    f0 = float(np.median(out)) if len(out) >= 5 else 0.0
    return f0, len(texto) / max(len(a) / 16000, 0.1)


def escolher(tent, texto, aceitas):
    """melhor de N (regra do fish_nuvem de produção): tom perto do normal do narrador neste vídeo + ritmo dele"""
    import numpy as np
    med = [(_f0_cps(w, texto), w) for w in tent]
    if len(aceitas) >= 3:
        alvo = float(np.median([m[0][0] for m in aceitas]))
        calvo = float(np.median([m[0][1] for m in aceitas]))
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


def posprocessar(ws, linhas):
    if not ws:
        return
    """as correções que funcionaram no Fish 1.5: microcortes + velocidade por frase (metade da força, como no Fish) +
    S do "respeito". Sem mexer no tom (tom mexido virou "fita"/"esquilo")."""
    import climas_voz
    anime_tts._marcar_gol(linhas, climas_voz.escolher([anime_tts._seguro(x) for x in linhas], str(ws[0].parent)))
    for i, w in enumerate(ws):
        try:
            anime_tts.narracao_curva.pos_processar(w, 0.0)
            anime_tts.narracao_curva.microcortes(w)
            kv = 1 + (anime_tts._vel_por_frase(anime_tts._seguro(linhas[i]), i) - 1) * 0.5
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
    lst = dst.with_suffix(".txt")
    sil = dst.with_name("_sil.wav")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.35", "-c:a",
        "pcm_s16le", str(sil)])
    nws = []
    for w in ws:
        n = w.with_name(w.stem + "_n.wav")
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(n)])
        nws.append(n)
    lst.write_text("".join(f"file '{w}'\nfile '{sil}'\n" for w in nws))
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-af", "loudnorm=I=-16:TP=-1.5",
        "-ar", "44100", "-ac", "1", str(dst)])


def main():
    roteiros = json.loads((P / "roteiros.json").read_text(encoding="utf-8"))
    b, c = _rclone()
    vz = P / "vozes"
    vozes = [v for v in roteiros if not v.startswith("_")]
    for v in vozes:
        sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/vozes/{v}", str(vz / v), "--include",
            "referencia_fish.*"], 900)
    base = P / "prod"
    for parte in ("bin", "config"):
        sh([b, "--config", c, "copy", f"manhwa-drive:colab_recap/raiz/D/recapd-ambientes/producao/{parte}",
            str(base / parte)], 1800)
    sys.path.insert(0, str(base / "bin"))
    import logging
    logging.basicConfig(level=logging.INFO, filename=str(S / "_anime_tts.log"))
    global anime_tts
    import anime_tts
    py = instalar()
    modelos = [("S1mini", "fishaudio/openaudio-s1-mini", "openaudio-s1-mini", EMO_S1),
               ("S2pro", "fishaudio/s2-pro", "s2-pro", EMO_S2),
               # 20/11 dona: "quero também com o Drama 3". 35B MoE (3B ativos): o peso inteiro não cabe na T4 —
               # tenta; se não couber, o log diz e segue
               ("Drama3", "fishaudio/drama-3-int4", "drama-3-int4", EMO_S2)]  # o cheio (36B) estourou a T4
    for tag, repo, nome, emo in modelos:
        try:
            ck = baixar(py, repo, nome)
        except Exception as e:  # noqa: BLE001
            log(f"{tag}: não baixou {e}")
            continue
        for voz in vozes:
            ref = vz / voz / "referencia_fish.wav"
            ref_txt = (vz / voz / "referencia_fish.txt").read_text(encoding="utf-8").strip()
            linhas = roteiros[voz]
            # 20/11 dona: "uma versão limpa e outras com as variações que fizemos — as que ficaram melhores"
            txt = [anime_tts._texto_fish(anime_tts._seguro(t))[0] for t in linhas]
            com = [com_emocao(t, emo) for t in txt]
            gerado = {}
            N3 = 2 if tag == "S2pro" else 3  # S2-Pro leva ~100 s por frase na T4
            for nome_v, ls, tent, pos in (("1_limpa", linhas, 1, False), ("2_melhor_de_3", txt, N3, False),
                                          ("3_melhor_de_3_+_emocao", com, N3, False),
                                          ("4_tudo_(melhor_de_3_+_emocao_+_acelera_no_codigo_+_S)", com, N3, True)):
                t0 = time.time()
                chave = (tuple(ls), tent)
                if chave not in gerado:
                    gerado[chave] = gerar(py, ck, ref, ref_txt, ls, P / "trab" / f"{voz}_{tag}_{nome_v[:1]}", tag != "S1mini", tent)
                ws = []
                for w in gerado[chave]:  # cópia: o pós da 4 não mexe nas frases da 3
                    c_ = w.with_name(w.stem + f"_v{nome_v[:1]}.wav")
                    shutil.copy(w, c_)
                    ws.append(c_)
                if pos:
                    posprocessar(ws, linhas)
                log(f"{voz} {tag} {nome_v}: {len(ws)}/{len(ls)} frases em {time.time() - t0:.0f}s")
                if ws:
                    juntar(ws, S / f"{voz}_{tag}_{nome_v}.wav")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1", str(S / "video.mp4")])
    log("FIM")


if __name__ == "__main__":
    main()
