# -*- coding: utf-8 -*-
"""intros_voz.py — ABERTURA COM VOZ HUMANA no começo dos compilados 16:9.

Pedido do dono (15/10): o feed do YouTube toca o começo do vídeo longo quando passam o mouse/dedo, e o público
usa isso pra ver se a voz é de IA. Então o compilado abre com uma voz humana (saudação + "deixa o like/se
inscreve" + chamada pra história); cada compilado com uma abertura diferente, medindo qual rende mais.
As vozes são de canais que AUTORIZARAM o uso ao dono (config/intros_voz.json -> autorizados, 15/10/2026).
Regras: nunca o nome do canal/criador; só fala genérica (sem obra, personagem, trama); sem palavrão (anúncio
limitado nos primeiros segundos); uma abertura = um criador só (não mistura vozes); a música do canal sai
(separação de voz, por causa do Content ID) e entra a nossa trilha.

Colheita (o agente que escolhe os trechos usa estes comandos):
  python bin/intros_voz.py colher [@canal ...]        # começo (150 s) + fim (75 s) de 4 vídeos longos por canal
  python bin/intros_voz.py texto @MomoManhwa          # transcrição com tempo de cada trecho baixado
  python bin/intros_voz.py palavras BASE 10 25        # palavra a palavra com tempo numa janela (s)
  python bin/intros_voz.py cortar BASE 1.20 4.85 SAIDA.wav
  python bin/intros_voz.py checar SAIDA.wav --canal @MomoManhwa   # transcreve de novo + nome/palavrão/bordas/música
BASE = caminho sem extensão do trecho baixado (o que o 'texto' mostra), ex.:
  assets/intros_voz/_brutos/momomanhwa/4-p05wF66hw_ini
"""
import datetime
import json
import os
import random
import re
import shutil
import subprocess
import sys
import unicodedata
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log  # noqa: E402

CFG = PROJECT_DIR / "config" / "intros_voz.json"
PASTA = PROJECT_DIR / "assets" / "intros_voz"
BRUTOS = PASTA / "_brutos"
STATS = PROJECT_DIR / "workspace" / "intros_voz_stats.json"  # usos (compilados postados) e vitórias por abertura
SEPARADOR = Path(os.environ.get("HIPER_SEPARADOR", r"D:\tools\separador\Scripts\audio-separator.exe"))
MODELOS_SEP = Path(os.environ.get("HIPER_SEPARADOR_MODELOS", r"D:\tools\separador\modelos"))
# MDX: segundos por pedaço na CPU; o BS-Roformer (melhor no papel) levou 13 min pra 15 s de áudio aqui
MODELO_VOZ = os.environ.get("HIPER_MODELO_VOZ", "UVR-MDX-NET-Voc_FT.onnx")
PRIORIDADE_BAIXA = 0x00004000 if os.name == "nt" else 0  # BELOW_NORMAL: a separação não atrapalha o render
SR = 48000
USOS_PRA_EXPLORAR = 2  # cada abertura vai em pelo menos 2 compilados antes de a escolha seguir só o resultado
CTA_RE = re.compile(r"\b(like|curt[ei]|inscrev|inscri[cç]|sininho|notifica|coment[ae]|compartilh)", re.I)
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
EXT_FONTE = (".webm", ".m4a", ".mp4", ".opus", ".mp3", ".aac")
S_INI, S_FIM = 150, 75  # s baixados do começo e do fim de cada vídeo (saudação/chamada costumam estar aí)
FIM_MAX_H = 8  # vídeo mais longo que isso fica só com o começo (o fim exige baixar o áudio inteiro)


def cfg():
    return json.loads(CFG.read_text(encoding="utf-8"))


def _slug(canal):
    return canal.lstrip("@").lower().replace(".", "_")


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _base(arg):
    """Aceita a base, o arquivo de fonte, o .groq.ogg ou o .groq.json do trecho -> Path da base (sem extensão)."""
    p = Path(arg)
    if not p.is_absolute():
        p = PROJECT_DIR / p
    nome = re.sub(r"(\.groq)?\.(json|ogg)$", "", p.name)
    nome = re.sub(r"\.(webm|m4a|mp4|opus|mp3|aac)$", "", nome)
    return p.with_name(nome)


def _fonte(base):
    for ext in EXT_FONTE:
        if base.with_name(base.name + ext).exists():
            return base.with_name(base.name + ext)
    return None


def _duracao(arq):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True, timeout=30, creationflags=SEM_JANELA)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


# ─── colheita ────────────────────────────────────────────────────────────────
def _yt(args, timeout=240):
    import ytdlp_vez  # COMUM: 1 yt-dlp por vez no PC (rajada bloqueou o IP da casa)
    with ytdlp_vez.vez("hipercool: intros"):
        return subprocess.run(["yt-dlp", "--no-warnings", "--no-playlist", *args], capture_output=True, text=True,
                              timeout=timeout, creationflags=SEM_JANELA)


def _listar(canal, n=15):
    """Vídeos longos (>= 5 min) mais novos do canal: [{id, dur, titulo}]."""
    r = _yt(["--flat-playlist", "-j", "--playlist-end", str(n), f"https://www.youtube.com/{canal}/videos"], 120)
    out = []
    for linha in r.stdout.splitlines():
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if (d.get("duration") or 0) >= 300:
            out.append({"id": d["id"], "dur": float(d["duration"]), "titulo": d.get("title", "")})
    return out


def _limpar(base):
    for p in base.parent.glob(base.name + ".*"):
        p.unlink(missing_ok=True)


def _baixar_ini(vid, base):
    """Começo do vídeo (S_INI s) na melhor qualidade: o ffmpeg só lê o começo do arquivo (segundos)."""
    url = f"https://www.youtube.com/watch?v={vid}"
    for fmt in ("ba[language^=pt]/ba", "251/250/140/249/139/18"):  # 18 = mp4 com vídeo (há vídeo só com ele)
        _limpar(base)
        try:
            r = _yt(["-f", fmt, "-q", "--download-sections", f"*0-{S_INI}", "-o", f"{base}.%(ext)s", url], 90)
        except subprocess.TimeoutExpired:
            continue
        f = _fonte(base)
        if f and _duracao(f) >= 5:
            return True
        if re.search(r"members|private|privado", r.stderr or "", re.I):
            return False
    _limpar(base)
    return False


def _baixar_fim(vid, base):
    """Fim do vídeo (S_FIM s). Pedir só o trecho do fim faz o ffmpeg ler o arquivo desde o começo (minutos);
    baixar o áudio inteiro leve (opus ~70 kbps, 4 conexões) leva segundos: 2 h = 6 s. Corta e apaga o inteiro.
    Devolve o segundo do vídeo onde o trecho começa, ou None."""
    inteiro = base.with_name(base.name + ".inteiro")
    _limpar(base)
    _limpar(inteiro)
    try:
        _yt(["-f", "250/249/251/wa", "-q", "-N", "4", "-o", f"{inteiro}.%(ext)s",
             f"https://www.youtube.com/watch?v={vid}"], 900)
        f = _fonte(inteiro)
        dur = _duracao(f) if f else 0.0
        if dur < S_FIM + 30:
            return None
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dur - S_FIM:.3f}", "-i", str(f), "-vn", "-c:a", "copy",
                        "-avoid_negative_ts", "make_zero", str(base) + f.suffix],
                       check=True, timeout=120, creationflags=SEM_JANELA)
        return round(dur - S_FIM, 2)
    except (subprocess.SubprocessError, OSError):
        _limpar(base)
        return None
    finally:
        _limpar(inteiro)


def _colher_canal(canal, n=4):
    pasta = BRUTOS / _slug(canal)
    pasta.mkdir(parents=True, exist_ok=True)
    idx = _ler(pasta / "indice.json", {"canal": canal, "videos": []})
    feitos = {v["id"] for v in idx["videos"]}
    if len(idx["videos"]) >= n:
        return idx
    for v in _listar(canal):
        if len(idx["videos"]) >= n:
            break
        if v["id"] in feitos:
            continue
        rel = lambda nome: str((pasta / f"{v['id']}_{nome}").relative_to(PROJECT_DIR).as_posix())  # noqa: E731
        if not _baixar_ini(v["id"], pasta / f"{v['id']}_ini"):
            log(f"  {canal}: {v['id']} não baixou (membros/bloqueado) — próximo")
            continue
        v["partes"] = {"ini": {"base": rel("ini"), "t0_no_video": 0}}
        t0 = _baixar_fim(v["id"], pasta / f"{v['id']}_fim") if v["dur"] <= FIM_MAX_H * 3600 else None
        if t0 is not None:
            v["partes"]["fim"] = {"base": rel("fim"), "t0_no_video": t0}
        idx["videos"].append(v)
        _gravar(pasta / "indice.json", idx)
        log(f"  {canal}: {v['id']} baixado ({len(idx['videos'])}/{n}, partes: {', '.join(v['partes'])})")
    return idx


def transcrever_trecho(base):
    """<base>.groq.json (Whisper pelo groq_api, com palavras). Usa o cache se já existir."""
    js = base.with_name(base.name + ".groq.json")
    if js.exists():
        return _ler(js, None)
    fonte = _fonte(base)
    if not fonte:
        return None
    ogg = base.with_name(base.name + ".groq.ogg")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(fonte), "-vn", "-ac", "1", "-ar", "16000",
                        "-c:a", "libopus", "-b:a", "24k", str(ogg)], check=True, timeout=120, creationflags=SEM_JANELA)
        import groq_api
        j = groq_api.transcrever(ogg, "pt", palavras=True)
    except (subprocess.SubprocessError, OSError) as e:
        log(f"  [!] {base.name}: não deu pra transcrever ({str(e)[:100]})")
        j = None
    finally:
        ogg.unlink(missing_ok=True)
    if j:
        _gravar(js, {"text": j.get("text", ""), "duration": j.get("duration"),
                     "segments": [{k: s.get(k) for k in ("start", "end", "text", "avg_logprob", "no_speech_prob")}
                                  for s in j.get("segments") or []],
                     "words": [{"w": w.get("word", "").strip(), "s": w.get("start"), "e": w.get("end")}
                               for w in j.get("words") or []]})
    return _ler(js, None)


def colher(canais=None, n=4):
    canais = canais or [a["canal"] for a in cfg()["autorizados"]]
    with ThreadPoolExecutor(4) as ex:
        idxs = list(ex.map(lambda c: _colher_canal(c, n), canais))
    bases = [Path(PROJECT_DIR / p["base"]) for idx in idxs for v in idx["videos"] for p in v["partes"].values()]
    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(transcrever_trecho, bases))
    log(f"colheita: {sum(len(i['videos']) for i in idxs)} vídeos de {len(canais)} canais, "
        f"{sum(1 for r in res if r)}/{len(bases)} trechos transcritos")


# ─── leitura pro agente ──────────────────────────────────────────────────────
def texto(canal):
    idx = _ler(BRUTOS / _slug(canal) / "indice.json", None)
    if not idx:
        print(f"{canal}: nada colhido ainda")
        return
    for v in idx["videos"]:
        for nome, p in v["partes"].items():
            base = PROJECT_DIR / p["base"]
            j = transcrever_trecho(base) or {}
            print(f"\n== {p['base']}  ({nome}: {p['t0_no_video']:.0f}s do vídeo de {v['dur'] / 60:.0f} min) "
                  f"| {v['titulo'][:70]}")
            for s in j.get("segments") or []:
                duvida = " (?)" if (s.get("no_speech_prob") or 0) > 0.5 else ""
                print(f"[{s['start']:.2f}-{s['end']:.2f}]{duvida} {s['text'].strip()}")


def palavras(base, t0, t1):
    j = transcrever_trecho(_base(base)) or {}
    for w in j.get("words") or []:
        if t0 <= (w["s"] or 0) <= t1:
            print(f"{w['s']:.2f}-{w['e']:.2f} {w['w']}")


# ─── recorte e checagem ──────────────────────────────────────────────────────
def cortar(base, ini, fim, saida, folga=0.08):
    """Recorte cru (com a música do canal) [ini-folga, fim+folga] em wav 48 kHz mono, com fade curto."""
    fonte = _fonte(_base(base))
    if not fonte:
        raise SystemExit(f"fonte não encontrada: {base}")
    a, dur = max(0.0, ini - folga), (fim - ini) + 2 * folga
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", str(fonte), "-vn",
                    "-af", f"afade=t=in:d=0.015,afade=t=out:st={max(0.0, dur - 0.03):.3f}:d=0.03",
                    "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(saida)],
                   check=True, timeout=60, creationflags=SEM_JANELA)
    return saida


def _pcm(arq, sr=16000):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                       capture_output=True, timeout=60, creationflags=SEM_JANELA)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def _db(x):
    return round(float(20 * np.log10(max(1e-9, float(np.sqrt(np.mean(x * x)))))), 1) if len(x) else -120.0


def _termos(texto_, lista):
    t = " " + re.sub(r"[^a-z0-9 ]+", " ", _sem_acento(texto_)) + " "
    return [x for x in lista if f" {re.sub(r'[^a-z0-9 ]+', ' ', _sem_acento(x)).strip()} " in t]


def checar(clip, canal=None):
    """Transcreve o recorte de novo e mede: nome do criador, palavrão, palavra cortada na borda, música/ruído
    nas pausas (antes da separação de voz), pico. Grava <clip>.checagem.json e devolve o dict."""
    import groq_api
    clip = Path(clip)
    j = groq_api.transcrever(clip, "pt", palavras=True) or {}
    ws = [{"w": w.get("word", "").strip(), "s": w.get("start") or 0.0, "e": w.get("end") or 0.0}
          for w in j.get("words") or []]
    x, sr = _pcm(clip), 16000
    dur = len(x) / sr
    fala = np.concatenate([x[int(w["s"] * sr):int(w["e"] * sr)] for w in ws]) if ws else x
    pausas = [x[int((a["e"] + 0.03) * sr):int((b["s"] - 0.03) * sr)] for a, b in zip(ws, ws[1:]) if b["s"] - a["e"] >= 0.15]
    rf = _db(fala)
    c = cfg()
    nomes = [n for a in c["autorizados"] if not canal or a["canal"].lower() == canal.lower() for n in a["nomes"]]
    txt = j.get("text", "").strip()
    out = {"clip": str(clip), "texto": txt, "duracao": round(dur, 2),
           "palavras": [(w["w"], round(w["s"], 2), round(w["e"], 2)) for w in ws],
           "nomes_ditos": _termos(txt, nomes), "palavroes": _termos(txt, c.get("palavroes", [])),
           "fala_db": rf, "pico_db": _db(np.array([np.abs(x).max()])) if len(x) else -120.0,
           "pausas_db": _db(np.concatenate(pausas)) if pausas else None,
           "borda_ini_rel_db": round(_db(x[:int(0.04 * sr)]) - rf, 1),
           "borda_fim_rel_db": round(_db(x[-int(0.04 * sr):]) - rf, 1),
           "1a_palavra_comeca_em": round(ws[0]["s"], 2) if ws else None,
           "ultima_palavra_termina_em": round(ws[-1]["e"], 2) if ws else None}
    out["leitura"] = ("borda_*_rel_db perto de 0 = corte no meio do som; pausas_db perto de fala_db = música/ruído "
                      "de fundo forte (sai na separação de voz do 'montar')")
    _gravar(clip.with_suffix(".checagem.json"), out)
    return out


# ─── montagem: voz separada, cortada no silêncio, nivelada ───────────────────
def separar_voz(entrada, saida):
    """Só a voz (a música do canal sai: Content ID e trilha nossa por baixo), wav 48 kHz mono."""
    tmpd = Path(saida).with_name(f"_sep_{Path(saida).stem}")
    shutil.rmtree(tmpd, ignore_errors=True)
    tmpd.mkdir(parents=True)
    try:
        r = subprocess.run([str(SEPARADOR), str(entrada), "-m", MODELO_VOZ, "--model_file_dir", str(MODELOS_SEP),
                            "--output_dir", str(tmpd), "--output_format", "WAV", "--single_stem", "Vocals"],
                           capture_output=True, text=True, timeout=1800,
                           creationflags=SEM_JANELA | PRIORIDADE_BAIXA)
        achados = sorted(tmpd.glob("*.wav"))
        if not achados:
            raise RuntimeError(f"separação de voz falhou: {((r.stderr or '') + (r.stdout or ''))[-300:]}")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(achados[0]), "-ac", "1", "-ar", str(SR),
                        "-c:a", "pcm_s16le", str(saida)], check=True, timeout=60, creationflags=SEM_JANELA)
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    return Path(saida)


def _env_db(x, sr, passo=0.01):
    n = max(1, int(passo * sr))
    k = len(x) // n
    if k == 0:
        return np.array([-120.0])
    return 20 * np.log10(np.sqrt(np.mean(x[:k * n].reshape(k, n) ** 2, axis=1)) + 1e-9)


def _bordas_exatas(x, sr, ini, fim):
    """(a, b) em s: onde a fala começa e acaba de verdade na voz já separada, perto de ini/fim (o Whisper erra
    ~0,1-0,3 s). Corta no silêncio entre as palavras; sem silêncio, no ponto de menor energia."""
    fr = 0.01
    env = _env_db(x, sr, fr)
    n = len(env)
    i0, i1 = int(ini / fr), max(int(ini / fr) + 1, int(fim / fr))
    lim = max(-55.0, float(np.percentile(env[i0:i1], 90)) - 30.0)
    quieto = env < lim
    a0, a1 = max(0, int((ini - 0.4) / fr)), min(n - 2, int((ini + 0.15) / fr))
    subidas = [j for j in range(a0, a1 + 1) if quieto[j] and not quieto[j + 1]]
    if subidas:
        j = min(subidas, key=lambda j: abs((j + 1) * fr - ini))
        a = max(0.0, (j + 1) * fr - 0.04)
    elif quieto[a0:a1 + 1].all():
        a = max(0.0, ini - 0.05)
    else:
        a = (a0 + int(np.argmin(env[a0:a1 + 1]))) * fr
    b0, b1 = max(0, int((fim - 0.15) / fr)), min(n - 2, int((fim + 0.5) / fr))
    descidas = [j for j in range(b0, b1 + 1) if not quieto[j] and quieto[j + 1:j + 7].all()]
    if descidas:
        j = descidas[0]
        prox = next((k for k in range(j + 1, n) if not quieto[k]), n)
        b = min((j + 1) * fr + 0.06, prox * fr - 0.02)
    else:
        b = (b0 + int(np.argmin(env[b0:b1 + 1]))) * fr
    return a, max(b, a + 0.2)


def _gravar_wav(arq, x, sr=SR):
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(arq), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(y.tobytes())


def _nivelar(y, alvo_db=-20.0):
    """Ganho pela fala (quadros acima do ruído), pico no máx. -1 dBFS: os pedaços ficam no mesmo volume."""
    env = _env_db(y, SR)
    fala = env[env > max(-55.0, float(env.max()) - 30)]
    rms = 10 ** (float(np.mean(fala)) / 20) if len(fala) else 0.05
    y = y * min(10 ** (15 / 20), 10 ** (alvo_db / 20) / max(rms, 1e-6))
    pico = float(np.abs(y).max()) if len(y) else 0.0
    return y * (0.89 / pico) if pico > 0.89 else y


def _alinhar(esperado, ws):
    """Palavras do texto conferido com o tempo do Whisper, que erra palavra de gíria ('os guri' -> 'Estamos good').
    Palavra casada pega o tempo dela; as sem par dividem o espaço entre as vizinhas."""
    import difflib
    alvo = esperado.split()
    if not alvo or not ws:
        return []
    norm = lambda w: re.sub(r"[^a-z0-9]", "", _sem_acento(w))  # noqa: E731
    sm = difflib.SequenceMatcher(a=[norm(w) for w in alvo], b=[norm(w[0]) for w in ws], autojunk=False)
    tempo = [None] * len(alvo)
    for bl in sm.get_matching_blocks():
        for k in range(bl.size):
            tempo[bl.a + k] = (ws[bl.b + k][1], ws[bl.b + k][2])
    k = 0
    while k < len(alvo):
        if tempo[k] is not None:
            k += 1
            continue
        j = k
        while j < len(alvo) and tempo[j] is None:
            j += 1
        a = tempo[k - 1][1] if k > 0 else ws[0][1]
        b = tempo[j][0] if j < len(alvo) else ws[-1][2]
        passo = max(0.0, b - a) / (j - k)
        for m in range(k, j):
            tempo[m] = (a + passo * (m - k), a + passo * (m - k + 1))
        k = j
    return [(w, round(s, 2), round(e, 2)) for w, (s, e) in zip(alvo, tempo)]


def montar(id_, canal, pecas, pausa=0.24, texto=None):
    """pecas = [(base, ini, fim)] em ordem, todas do MESMO criador -> assets/intros_voz/<id>.wav (voz separada,
    cortada no silêncio, nivelada, com pausa natural entre os pedaços) + registro em config/intros_voz.json.
    texto = o que a fala diz (conferido); a legenda usa ele com o tempo do Whisper."""
    tmp = PASTA / "_tmp" / id_
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    partes = []
    for k, (base, ini, fim) in enumerate(pecas):
        fonte = _fonte(_base(base))
        if not fonte:
            raise SystemExit(f"fonte não encontrada: {base}")
        a = max(0.0, ini - 1.0)
        bruto = tmp / f"p{k}_bruto.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{fim + 1.0 - a:.3f}", "-i",
                        str(fonte), "-vn", "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le", str(bruto)],
                       check=True, timeout=60, creationflags=SEM_JANELA)
        x = _pcm(separar_voz(bruto, tmp / f"p{k}_voz.wav"), SR)
        s, e = _bordas_exatas(x, SR, ini - a, fim - a)
        y = x[int(s * SR):int(e * SR)].copy()
        nf_in, nf_out = int(0.008 * SR), int(0.025 * SR)
        y[:nf_in] *= np.linspace(0, 1, nf_in)
        y[-nf_out:] *= np.linspace(1, 0, nf_out)
        partes.append(_nivelar(y))
    gap = np.zeros(int(pausa * SR), np.float32)
    voz = np.concatenate([p for k, parte in enumerate(partes) for p in ((gap, parte) if k else (parte,))])
    PASTA.mkdir(parents=True, exist_ok=True)
    out = PASTA / f"{id_}.wav"
    _gravar_wav(out, voz)
    import groq_api
    j = groq_api.transcrever(out, "pt", palavras=True) or {}
    ouvidas = [(w.get("word", "").strip(), round(w.get("start") or 0, 2), round(w.get("end") or 0, 2))
               for w in j.get("words") or []]
    ouvido = (j.get("text") or "").strip()
    reg = {"id": id_, "canal": canal, "arquivo": out.name, "texto": texto or ouvido, "texto_ouvido": ouvido,
           "palavras": _alinhar(texto, ouvidas) if texto else ouvidas,
           "duracao": round(len(voz) / SR, 2), "pecas": [[str(b), round(i, 2), round(f, 2)] for b, i, f in pecas],
           "modelo_voz": MODELO_VOZ, "ativa": True, "montada_em": datetime.date.today().isoformat()}
    c = cfg()
    c["intros"] = [i for i in c.get("intros", []) if i.get("id") != id_] + [reg]
    CFG.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    log(f"  abertura {id_} ({canal}, {reg['duracao']:.1f} s): {reg['texto']}")
    return reg


# ─── rodízio e medição ───────────────────────────────────────────────────────
def ativas():
    """Aberturas usáveis. Só entra a que tem a legenda conferida ("texto_ouvido" = o montar recebeu o texto certo;
    o Whisper sozinho erra gíria: 'os guri' -> 'Estamos good')."""
    return [i for i in cfg().get("intros", []) if i.get("ativa", True) and "texto_ouvido" in i
            and (PASTA / i["arquivo"]).exists()]


def escolher(obra, lugar="abertura", evitar_canal=None):
    """Fala do próximo compilado pro `lugar` ("abertura" = começo; "meio" = chamada de like numa troca de capítulo,
    campo "lugar" de cada fala em config/intros_voz.json, padrão abertura). Primeiro todas rodam (a menos postada vai;
    cada uma USOS_PRA_EXPLORAR vezes), depois Thompson pelas vitórias. Nunca o mesmo criador da última postada nesse
    lugar nem o `evitar_canal` (o da abertura do mesmo vídeo). A semente depende só do histórico: a escolha não muda
    entre uma remontagem e outra, só depois de postar."""
    lista = [i for i in ativas() if i.get("lugar", "abertura") == lugar]
    if not lista:
        return None
    st = _ler(STATS, {})
    usos, vit = st.get("usos", {}), st.get("vitorias", {})
    hist = [h for h in st.get("historico", []) if h.get("lugar", "abertura") == lugar]
    evitar = {hist[-1].get("canal") if hist else None, evitar_canal}
    cands = [i for i in lista if i["canal"] not in evitar] or lista
    menor = min(usos.get(i["id"], 0) for i in cands)
    if menor < USOS_PRA_EXPLORAR:
        cands = [i for i in cands if usos.get(i["id"], 0) == menor]
    rnd = random.Random(f"{obra}|{len(hist)}" if lugar == "abertura" else f"{obra}|{lugar}|{len(hist)}")
    return max(cands, key=lambda i: rnd.betavariate(1 + vit.get(i["id"], 0),
                                                     1 + max(0, usos.get(i["id"], 0) - vit.get(i["id"], 0))))


def registrar_uso(id_, obra, url=None):
    """Compilado com esta fala foi POSTADO (chamado pelo postar_hipercool.postar_longo)."""
    st = _ler(STATS, {})
    st.setdefault("usos", {})[id_] = st.get("usos", {}).get(id_, 0) + 1
    reg = next((i for i in cfg().get("intros", []) if i["id"] == id_), {})
    st.setdefault("historico", []).append({"id": id_, "canal": reg.get("canal"), "lugar": reg.get("lugar", "abertura"),
                                           "obra": obra, "url": url,
                                           "quando": datetime.datetime.now().isoformat(timespec="minutes")})
    _gravar(STATS, st)


def registrar_resultado(id_, venceu):
    """Resultado do compilado (ex.: retenção aos 30 s acima da mediana do canal) — alimenta a escolha."""
    st = _ler(STATS, {})
    if venceu:
        st.setdefault("vitorias", {})[id_] = st.get("vitorias", {}).get(id_, 0) + 1
    _gravar(STATS, st)


# ─── vídeo da abertura (mesmo formato dos capNN do longo) ────────────────────
def _rgba(im):
    a = np.asarray(im.convert("RGBA"))
    import cv2
    return cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2BGR), a[..., 3].astype(np.float32) / 255


def _colar(fr, bgr, alfa, cx, cy, esc=1.0):
    import cv2
    if esc != 1.0:
        w, h = max(1, int(bgr.shape[1] * esc)), max(1, int(bgr.shape[0] * esc))
        bgr, alfa = cv2.resize(bgr, (w, h)), cv2.resize(alfa, (w, h))
    h, w = bgr.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(fr.shape[1], x0 + w), min(fr.shape[0], y0 + h)
    if xa >= xb or ya >= yb:
        return
    s, a = bgr[ya - y0:yb - y0, xa - x0:xb - x0], alfa[ya - y0:yb - y0, xa - x0:xb - x0, None]
    fr[ya:yb, xa:xb] = (s * a + fr[ya:yb, xa:xb] * (1 - a)).astype(np.uint8)


def _selo(texto_, cor, emoji=None):
    """Botão vermelho/azul tipo 'INSCREVA-SE' (PIL RGBA)."""
    from PIL import Image, ImageDraw
    import fx_acabamento
    f = fx_acabamento._fonte("LuckiestGuy-Regular.ttf", 66)
    tw = ImageDraw.Draw(Image.new("RGB", (8, 8))).textlength(texto_, font=f)
    em = None
    if emoji:
        p = fx_acabamento.emoji_png(emoji, 96)
        em = Image.open(p).convert("RGBA") if p else None
    w, h = int(tw + 76 + (em.width - 10 if em else 0)), 112
    im = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, w + 5, h + 5], radius=h // 2, fill=(*cor, 255), outline=(255, 255, 255, 255), width=6)
    x = 40
    if em:
        im.alpha_composite(em, (14, (h + 12 - em.height) // 2))
        x = em.width
    d.text((x, 26), texto_, font=f, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    return _rgba(im)


def _legenda(palavras_, atual, W):
    """Grupo de palavras centralizado; a que está sendo dita em amarelo."""
    from PIL import Image, ImageDraw
    import fx_acabamento
    f = fx_acabamento._fonte("Montserrat-ExtraBold.ttf", 76)
    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    esp = d0.textlength(" ", font=f)
    larg = [d0.textlength(w.upper(), font=f) for w in palavras_]
    tot = sum(larg) + esp * (len(palavras_) - 1)
    im = Image.new("RGBA", (int(min(tot, W * 0.92)) + 40, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 20 + max(0, (im.width - 40 - tot) / 2)
    for k, (w, lw) in enumerate(zip(palavras_, larg)):
        d.text((x, 14), w.upper(), font=f, fill=(255, 212, 0) if k == atual else (255, 255, 255),
               stroke_width=7, stroke_fill=(0, 0, 0))
        x += lw + esp
    return _rgba(im)


def _grupos(palavras_, maximo=4):
    out, cur = [], []
    for w, s, e in palavras_:
        cur.append((w, s, e))
        if len(cur) >= maximo or re.search(r"[.!?,]$", w):
            out.append(cur)
            cur = []
    return out + ([cur] if cur else [])


# memes animados (gif/mp4 do catálogo do fx_memes), SEM som, enchendo a tela enquanto o criador fala (dono, 15/10:
# "o começo fica estático"). Tags do catálogo por momento da fala; nada negativo.
MEME_TAGS = {"saudacao": {"felicidade", "alegria", "diversão", "reação positiva", "fofo", "wholesome", "positivo", "riso"},
             "like": {"aprovação", "ok", "positivo", "satisfação", "sucesso", "confiança", "cool"},
             "bora": {"atitude", "cool", "confiança", "vitória", "eureka", "diversão", "sucesso"}}
MEME_FORA = {"humor negro", "dark humor", "humor sombrio", "tristeza", "choro", "raiva", "desaprovação", "decepção",
             "medo", "pânico", "desespero", "frustração", "rejeição", "fracasso", "julgamento", "desdém", "crítica",
             "caos", "loucura", "cansaço", "desânimo", "sarcasmo", "ironia", "constrangimento", "incômodo",
             "desconforto", "susto", "choque", "reação extrema", "drama", "nojo", "morte"}
# descrição do catálogo: fora o que parece choro/tristeza ou não tem imagem (confete transparente) ou é "desinteressado"
MEME_DESC_FORA = re.compile(r"chor|lágrim|confete|indiferen|desinteress|trist|raiva|medo|nojo|sangue|mort|arma", re.I)
MEME_DESC_LIKE = re.compile(r"positivo|polegar|\bok\b|aprova", re.I)  # no pedido de like, joinha primeiro
SAUDACAO_RE = re.compile(r"\b(salve|fala|e a[ií]|galera|rapaziada|pessoal|manos?|molecada|guri)\b", re.I)
BORA_RE = re.compile(r"\b(bora|vamo|vamos|vambora|come[cç]ar|hist[oó]ria|obra|aproveita|descobrir|dali|dale)\b", re.I)
MEME_CAIXA = (1300, 650)  # tamanho máximo do meme na tela (entre o selo do topo e a legenda)
MEME_CENTRO_Y = 528


def _momento(texto_):
    if CTA_RE.search(texto_):
        return "like"
    if BORA_RE.search(texto_) and not SAUDACAO_RE.search(texto_):
        return "bora"
    return "saudacao"


def _vagas_meme(grupos, total, ini=0.45, minimo=2.2):
    """[(t0, t1, momento)]: a tela troca de meme a cada ~2-3 s, sempre no começo de um pedaço da fala."""
    cortes = [ini]
    for g in grupos[1:]:
        if g[0][1] - cortes[-1] >= minimo and total - 0.35 - g[0][1] >= 1.2:
            cortes.append(g[0][1])
    vagas = []
    for k, t0 in enumerate(cortes):
        t1 = cortes[k + 1] if k + 1 < len(cortes) else total - 0.35
        texto_ = " ".join(w for g in grupos for w, s, _e in g if t0 - 0.05 <= s < t1)
        vagas.append((t0, t1, _momento(texto_)))
    return vagas


def _memes_pra(vagas, semente):
    """Um meme animado por vaga, do catálogo, sem repetir; [] se não houver catálogo (fica só a capa)."""
    try:
        import fx_memes
        cat = fx_memes._carregar()
    except Exception:  # noqa: BLE001
        return []
    anim = [m for m in cat if Path(m["file"]).suffix.lower() in (".gif", ".mp4") and m.get("duration", 0) >= 0.6
            and not {t.lower() for t in m.get("tags", [])} & MEME_FORA and not MEME_DESC_FORA.search(m.get("desc", ""))]
    rnd, usados, out = random.Random(semente), set(), []
    for _t0, _t1, mom in vagas:
        cands = [m for m in anim if m["file"] not in usados and {t.lower() for t in m.get("tags", [])} & MEME_TAGS[mom]]
        if mom == "like":
            cands = [m for m in cands if MEME_DESC_LIKE.search(m.get("desc", ""))] or cands
        if not cands:
            return []
        m = rnd.choice(sorted(cands, key=lambda x: x["file"]))
        usados.add(m["file"])
        out.append(m["file"])
    return out


class _Meme:
    """Quadros do meme (gif/mp4) sem som, no tamanho da caixa, em loop até `dur`, lidos um a um (pouca memória)."""

    def __init__(self, arq, dur, fps):
        arq = Path(arq)
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(arq)], capture_output=True, text=True, timeout=30,
                           creationflags=SEM_JANELA)
        w, h = (int(x) for x in r.stdout.strip().splitlines()[0].split(",")[:2])
        s = min(MEME_CAIXA[0] / w, MEME_CAIXA[1] / h)
        self.w, self.h = max(2, int(w * s) // 2 * 2), max(2, int(h * s) // 2 * 2)
        laco = ["-ignore_loop", "0"] if arq.suffix.lower() == ".gif" else ["-stream_loop", "-1"]
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", *laco, "-i", str(arq), "-t", f"{dur + 0.2:.3f}", "-an",
                                   "-vf", f"fps={fps},scale={self.w}:{self.h}:flags=lanczos", "-f", "rawvideo",
                                   "-pix_fmt", "bgra", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  creationflags=SEM_JANELA)
        self.n, self.ult = self.w * self.h * 4, None

    def quadro(self):
        b = self.p.stdout.read(self.n)
        if len(b) == self.n:
            a = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 4)
            self.ult = (np.ascontiguousarray(a[..., :3]), a[..., 3].astype(np.float32) / 255)
        return self.ult

    def fechar(self):
        try:
            self.p.kill()
            self.p.wait(timeout=10)
        except Exception:  # noqa: BLE001
            pass


def segmento(intro, fundo_jpg, saida, W=1920, H=1080, fps=30, enc=None, semente=None):
    """Trecho de vídeo da fala: começa na capa (a prévia do feed continua a imagem da miniatura), que em ~0,5 s vira
    fundo desfocado com MEMES ANIMADOS sem som trocando junto com a fala + legenda palavra a palavra + selo
    INSCREVA-SE/LIKE quando a voz pede + nossa trilha com ducking + whoosh no fim; termina no preto (o capítulo
    começa do preto). Mesmo formato dos capNN.mp4 (h264 + AAC 48 kHz estéreo) pra emendar sem re-encode.
    semente: varia os memes (padrão: o id da fala)."""
    import cv2
    import fx_acabamento
    import fx_music
    saida = Path(saida)
    tmp = saida.with_name(f"_tmp_{saida.stem}")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    atraso = 0.12
    voz = PASTA / intro["arquivo"]
    total = round(_duracao(voz) + atraso + 0.75, 2)
    nar = tmp / "_voz.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(voz), "-af",
                    f"adelay={int(atraso * 1000)},apad,atrim=0:{total:.3f}", "-ac", "1", "-ar", str(SR), str(nar)],
                   check=True, timeout=60, creationflags=SEM_JANELA)
    img = cv2.imread(str(fundo_jpg))
    Z = 1.07
    sc = max(W * Z / img.shape[1], H * Z / img.shape[0])
    grande = cv2.resize(img, (int(img.shape[1] * sc) + 2, int(img.shape[0] * sc) + 2), interpolation=cv2.INTER_AREA)
    gy, gx = (grande.shape[0] - int(H * Z)) // 2, (grande.shape[1] - int(W * Z)) // 2
    grande = grande[gy:gy + int(H * Z), gx:gx + int(W * Z)]
    desfocada = (cv2.GaussianBlur(grande, (0, 0), 18) * 0.45).astype(np.uint8)
    sombra = np.ones((H, W, 1), np.float32)
    sombra[int(H * 0.55):, :, 0] = np.linspace(1.0, 0.45, H - int(H * 0.55))[:, None]
    pal = [(w, s + atraso, e + atraso) for w, s, e in intro.get("palavras") or []]
    grupos = _grupos(pal)
    vagas = _vagas_meme(grupos, total) if grupos else []
    memes = _memes_pra(vagas, semente or intro.get("id", ""))
    vagas = vagas if memes else []
    meme_atual, k_atual = None, -1
    selos, vistos = [], set()
    for w, s, _e in pal:
        m = CTA_RE.search(w)
        if not m:
            continue
        tipo = "inscricao" if re.match(r"inscr|sininho|notifica", m.group(1), re.I) else (
            "comentario" if re.match(r"coment|compartilh", m.group(1), re.I) else "like")
        if tipo in vistos:
            continue
        vistos.add(tipo)
        bgr, alfa = {"inscricao": lambda: _selo("INSCREVA-SE", (225, 25, 35), "🔔"),
                     "like": lambda: _selo("DEIXA O LIKE", (25, 110, 235), "👍"),
                     "comentario": lambda: _selo("COMENTA AÍ", (20, 150, 70), "💬")}[tipo]()
        selos.append((s, bgr, alfa))
    cache_leg = {}
    bruto = tmp / "_bruto.mp4"
    enc = enc or ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p"]
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                             "-r", str(fps), "-i", "-", "-i", str(nar), *enc, "-c:a", "aac", "-b:a", "192k",
                             "-ar", str(SR), "-ac", "2", "-shortest", str(bruto)],
                            stdin=subprocess.PIPE, creationflags=SEM_JANELA)
    xs_selo = {1: [W / 2], 2: [W / 2 - 330, W / 2 + 330], 3: [W / 2 - 560, W / 2, W / 2 + 560]}.get(len(selos), [])
    try:
        nfr = int(round(total * fps))
        for f in range(nfr):
            t = f / fps
            p = t / total
            z = 1.0 + (Z - 1.0) * (p * p * (3 - 2 * p))
            cw, ch = int(W * Z / z), int(H * Z / z)
            y0, x0 = (grande.shape[0] - ch) // 2, (grande.shape[1] - cw) // 2
            fr = cv2.resize(grande[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)
            mistura = min(1.0, max(0.0, (t - 0.3) / 0.4)) if vagas else 0.0  # capa nítida -> fundo dos memes
            if mistura > 0:
                fd = cv2.resize(desfocada[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)
                fr = cv2.addWeighted(fd, mistura, fr, 1 - mistura, 0) if mistura < 1 else fd
            fr = (fr * sombra).astype(np.uint8)
            k = next((k for k, (t0, t1, _m) in enumerate(vagas) if t0 <= t < t1), -1)
            if k != k_atual:
                if meme_atual:
                    meme_atual.fechar()
                meme_atual, k_atual = None, k
                if k >= 0:
                    try:
                        meme_atual = _Meme(memes[k], vagas[k][1] - vagas[k][0], fps)
                    except Exception as e:  # noqa: BLE001
                        log(f"  [!] meme {Path(memes[k]).name} não abriu ({str(e)[:80]})")
            q = meme_atual.quadro() if meme_atual else None
            if q:
                e_ = min(1.0, (t - vagas[k][0]) / 0.22)
                esc = 0.6 + 0.48 * e_ if e_ < 0.85 else 1.08 - 0.08 * (e_ - 0.85) / 0.15
                bgr_m, alfa_m = q  # parte transparente do GIF fica escura (não vira caixa branca)
                placa = (bgr_m * alfa_m[..., None] + 18 * (1 - alfa_m[..., None])).astype(np.uint8)
                borda = np.full((placa.shape[0] + 16, placa.shape[1] + 16, 3), 255, np.uint8)
                _colar(fr, borda, np.ones(borda.shape[:2], np.float32), W / 2, MEME_CENTRO_Y, esc)
                _colar(fr, placa, np.ones(placa.shape[:2], np.float32), W / 2, MEME_CENTRO_Y, esc)
            for gi, g in enumerate(grupos):
                fim_g = grupos[gi + 1][0][1] if gi + 1 < len(grupos) else g[-1][2] + 0.5
                if g[0][1] <= t < fim_g:
                    atual = max([k for k, (_w, s, _e) in enumerate(g) if s <= t] or [0])
                    if (gi, atual) not in cache_leg:
                        cache_leg[(gi, atual)] = _legenda([w for w, _s, _e in g], atual, W)
                    bgr, alfa = cache_leg[(gi, atual)]
                    _colar(fr, bgr, alfa, W / 2, H - 150)
            for j, (s, bgr, alfa) in enumerate(selos):
                if t >= s:
                    e = min(1.0, (t - s) / 0.28)
                    esc = 0.5 + 0.62 * e if e < 0.8 else 1.12 - 0.12 * (e - 0.8) / 0.2
                    _colar(fr, bgr, alfa, xs_selo[j], 120, esc)
            sobra = total - t
            if sobra < 0.35:
                fr = (fr * max(0.0, sobra / 0.35)).astype(np.uint8)
            proc.stdin.write(fr.tobytes())
    finally:
        if meme_atual:
            meme_atual.fechar()
        proc.stdin.close()
        proc.wait(timeout=600)
    if proc.returncode != 0 or not bruto.exists():
        raise RuntimeError("encode da abertura falhou")
    musica = fx_music.compose_dynamic_music(total, [], fx_acabamento.TRILHAS_DIR, tmp)
    whoosh = fx_acabamento.SFX_DIR / "whoosh_cinematic_01.wav"
    sfx = [{"file": str(whoosh), "t": max(0.0, total - 0.75), "gain_db": -14}] if whoosh.exists() else []
    fx_acabamento.masterizar_audio(bruto, saida, musica, sfx, tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    return saida


def _formato(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,codec_name,profile,width,height,pix_fmt,r_frame_rate,time_base,sample_rate,"
                        "channels", "-of", "json", str(mp4)], capture_output=True, text=True, timeout=30,
                       creationflags=SEM_JANELA)
    try:
        return sorted((json.loads(r.stdout).get("streams") or []), key=lambda s: s.get("codec_type", ""))
    except ValueError:
        return []


def para_compilado(obra, cap1_mp4, capa_jpg, pasta, enc, W=1920, H=1080, fps=30, lugar="abertura", evitar_canal=None):
    """Fala do próximo compilado (pt) pro `lugar` ("abertura" ou "meio"): {id, canal, texto, dur, mp4} ou None.
    Fundo = capa do compilado (a prévia do feed continua a imagem da capa); sem capa, um quadro do capítulo 1.
    Formato igual ao capítulo 1, senão None (a emenda sem re-encode exige)."""
    intro = escolher(obra, lugar, evitar_canal)
    if not intro:
        return None
    pasta = Path(pasta)
    tem_capa = bool(capa_jpg) and Path(capa_jpg).is_file()
    fundo = Path(capa_jpg) if tem_capa else pasta / "_abertura_fundo.jpg"
    if not tem_capa:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "4", "-i", str(cap1_mp4), "-frames:v", "1",
                        str(fundo)], check=True, timeout=60, creationflags=SEM_JANELA)
    mp4 = pasta / f"_abertura_{lugar}_{intro['id']}.mp4"
    n_hist = len(_ler(STATS, {}).get("historico", []))
    segmento(intro, fundo, mp4, W, H, fps, enc, semente=f"{intro['id']}|{obra}|{n_hist}")  # memes variam por vídeo
    if _formato(mp4) != _formato(cap1_mp4):
        log(f"  [!] fala {intro['id']} ({lugar}) saiu em formato diferente do capítulo 1 — fica de fora")
        mp4.unlink(missing_ok=True)
        return None
    return {"id": intro["id"], "canal": intro["canal"], "texto": intro["texto"], "dur": _duracao(mp4), "mp4": mp4}


def emenda_ok(mp4, t):
    """Decodifica a emenda abertura -> capítulo 1: erro de decodificação = não usar a abertura."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t - 1.5):.2f}", "-t", "4", "-i", str(mp4),
                        "-f", "null", "-"], capture_output=True, text=True, timeout=180, creationflags=SEM_JANELA)
    return r.returncode == 0 and not (r.stderr or "").strip()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="abertura com voz humana: colheita, recorte e checagem")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("colher")
    s.add_argument("canais", nargs="*")
    s.add_argument("--n", type=int, default=4)
    s = sub.add_parser("texto")
    s.add_argument("canal")
    s = sub.add_parser("palavras")
    s.add_argument("base")
    s.add_argument("t0", type=float)
    s.add_argument("t1", type=float)
    s = sub.add_parser("cortar")
    s.add_argument("base")
    s.add_argument("ini", type=float)
    s.add_argument("fim", type=float)
    s.add_argument("saida")
    s = sub.add_parser("checar")
    s.add_argument("clip")
    s.add_argument("--canal")
    s = sub.add_parser("montar", help="ID @canal BASE:INI:FIM [BASE:INI:FIM ...] (pedaços do mesmo criador)")
    s.add_argument("id")
    s.add_argument("canal")
    s.add_argument("pecas", nargs="+")
    s.add_argument("--pausa", type=float, default=0.24)
    s.add_argument("--texto", help="o que a fala diz (conferido); vira a legenda, com o tempo do Whisper")
    s = sub.add_parser("previa", help="vídeo da abertura sobre uma capa, pra ouvir/ver antes de usar")
    s.add_argument("id")
    s.add_argument("--fundo", help="jpg de fundo (padrão: a capa do compilado mais novo)")
    s.add_argument("--saida")
    sub.add_parser("lista")
    a = ap.parse_args()
    if a.cmd == "colher":
        colher(a.canais or None, a.n)
    elif a.cmd == "texto":
        texto(a.canal)
    elif a.cmd == "palavras":
        palavras(a.base, a.t0, a.t1)
    elif a.cmd == "cortar":
        print(cortar(a.base, a.ini, a.fim, a.saida))
    elif a.cmd == "checar":
        print(json.dumps(checar(a.clip, a.canal), ensure_ascii=False, indent=1))
    elif a.cmd == "montar":
        pecas = [(b, float(i), float(f)) for b, i, f in (p.rsplit(":", 2) for p in a.pecas)]
        print(json.dumps(montar(a.id, a.canal, pecas, a.pausa, a.texto), ensure_ascii=False, indent=1))
    elif a.cmd == "previa":
        intro = next((i for i in cfg().get("intros", []) if i["id"] == a.id), None)
        if not intro:
            raise SystemExit(f"abertura {a.id} não está em config/intros_voz.json")
        capas = sorted((PROJECT_DIR / "workspace" / "videos" / "longo").glob("*/*_caps*.capa.jpg"),
                       key=lambda p: p.stat().st_mtime)
        fundo = a.fundo or (capas[-1] if capas else None)
        if not fundo:
            raise SystemExit("sem capa de compilado: passe --fundo")
        print(segmento(intro, fundo, a.saida or PASTA / "_previas" / f"{a.id}.mp4"))
    elif a.cmd == "lista":
        st = _ler(STATS, {})
        for i in cfg().get("intros", []):
            print(f"{'ATIVA ' if i.get('ativa', True) else 'off   '} {i['id']:<22} {i['canal']:<20} "
                  f"{i['duracao']:>4.1f}s usos={st.get('usos', {}).get(i['id'], 0)} "
                  f"vit={st.get('vitorias', {}).get(i['id'], 0)} | {i['texto']}")
