# -*- coding: utf-8 -*-
"""fx_acabamento.py — ACABAMENTO FINAL do vídeo (melhorias portadas do D:\\manhwa-react).

════════════════════════════════════════════════════════════════════════════
MAPA (feito pra manutenção rápida / modelo grátis)
════════════════════════════════════════════════════════════════════════════
Roda DEPOIS do concat dos clips (vídeo 720p com voz + SFX de transição) e
entrega o vídeo final 1080x1920. Substitui: legendas em PNG (vários passes),
upscale separado, trilha sem nivelamento e intro/outro de tela parada.

  finalizar(...)                   ORQUESTRA tudo abaixo (é o que o pipeline chama).
  editorial(recap, titulo, cache)  LLM 1x por capítulo (salvo no narration_cache):
        gancho de abertura, palavras de impacto (+emoji) e pergunta do CTA.
  tempos_palavras(...)             tempo REAL de cada palavra do narrador: Groq
        whisper no áudio + alinhamento com o texto conhecido (difflib). Sem Groq,
        divide a fala (já sem o silêncio das pontas) pelo tamanho das palavras.
  planejar_sons(...)               SFX no instante da palavra (gatilhos de
        config/gatilhos_narracao.json + impacto + CTA), com anti-poluição.
  masterizar_audio(...)            trilha nivelada com ducking pela voz + SFX +
        loudness final em 2 passos (-14 LUFS, pico -1). Vídeo copiado.
  montar_ass(...)                  legenda palavra a palavra com pop, gancho,
        selo obra/capítulo, palavra de impacto gigante, barra de progresso,
        marca d'água e CTA — tudo num ASS só (libass).
  passe_final(...)                 UM encode: upscale lanczos + nitidez (cas) +
        punch-in/tremor nas palavras de impacto + emoji + ASS.
  validar(...)                     duração, resolução, LUFS, trechos pretos, áudio x vídeo.
  gerar_capa(...)                  thumbnail 1280x720 estilo manhwa.

Origem no manhwa-react: mr/captions.py, mr/audio.py (loudnorm_two_pass),
mr/render.py (render_audio, ffmpeg_retry, overlays com tpad), mr/music.py,
mr/triggers.py, mr/pipeline.py (_declutter), mr/emoji.py, mr/validate.py,
mr/transcribe.py (Groq), mr/capa.py.

Env: HIPER_ACABAMENTO=0 desliga (fluxo antigo). HIPER_TEMPO_PALAVRA=prop pula o
Groq. HIPER_EDITORIAL_LLM=0 pula o LLM. HIPER_LUFS, HIPER_MUSICA_LUFS,
HIPER_PRESET, HIPER_CRF, HIPER_THREADS, HIPERCOOL_COR (#RRGGBB).
════════════════════════════════════════════════════════════════════════════
"""
import difflib
import hashlib
import json
import os
import random
import re
import subprocess
import time
import unicodedata
from pathlib import Path

from hp_common import PROJECT_DIR, WATERMARK_HANDLE, log

MATERIAIS = Path(os.environ.get("HIPERCOOL_MATERIAIS", r"D:\hipercool-materiais"))
ASSETS = MATERIAIS / "assets"
FONTS_DIR = ASSETS / "fonts"
TRILHAS_DIR = ASSETS / "trilhas"
SFX_DIR = ASSETS / "sfx"
SFX_LIBS = [ASSETS / "sfx", ASSETS / "sfx_foley", ASSETS / "sfx_extras", ASSETS / "sfx_memes"]
GATILHOS_FILE = PROJECT_DIR / "config" / "gatilhos_narracao.json"
EMOJI_DIR = PROJECT_DIR / "workspace" / "cache" / "emoji"
OVERLAYS_ELEMENTAL = ASSETS / "overlays" / "elemental"
OV_CACHE = PROJECT_DIR / "workspace" / "cache" / "overlays"
CLIPES_DIR = PROJECT_DIR / "workspace" / "cache" / "clipes_parados"

OW, OH = 1080, 1920
COR = os.environ.get("HIPERCOOL_COR", "#FFD400")
LUFS_ALVO = float(os.environ.get("HIPER_LUFS", "-14"))
MUSICA_LUFS = float(os.environ.get("HIPER_MUSICA_LUFS", "-28"))
IDIOMA = None  # língua da versão (None = pt); o finalizar() seta. Ver bin/idiomas.py
PRESET = os.environ.get("HIPER_PRESET", "veryfast")
CRF = os.environ.get("HIPER_CRF", "19")
THREADS = os.environ.get("HIPER_THREADS", "4")

CAP_Y = int(OH * 0.70)      # centro da legenda palavra a palavra
HOOK_Y = 330                # topo do gancho
KEY_Y = int(OH * 0.40)      # centro da palavra de impacto
SELO_Y = 150                # selo obra/capítulo
CTA_SEGUNDOS = 3.2
# 16/10, o dono: "o final está terminando enquanto a fala ainda sai". No cap 4 o vídeo (486,70 s) e a
# voz (486,83 s) acabavam juntos. O último quadro fica parado mais este tanto, com a trilha saindo.
RESPIRO_FINAL = float(os.environ.get("HIPER_RESPIRO_FINAL", "1.6"))


# ─── ffmpeg / utilidades ─────────────────────────────────────────────────────
def _run(cmd, timeout=None):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def ffmpeg(args, timeout=3600):
    r = _run(["ffmpeg", "-hide_banner", "-y", "-loglevel", "error", *args], timeout)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:] or f"ffmpeg saiu com {r.returncode}")
    return r


def ffmpeg_retry(args, tries=3, wait=25, timeout=3600):
    """ffmpeg com nova tentativa quando o Windows nega memória (pagefile cheio)."""
    last = None
    for i in range(tries):
        try:
            return ffmpeg(args, timeout)
        except RuntimeError as e:
            last = e
            if not any(k in str(e) for k in ("allocate memory", "get_buffer", "malloc", "external library")):
                raise
            log(f"  ffmpeg: sem memória (tentativa {i + 1}/{tries}); aguardando {wait}s")
            time.sleep(wait)
    light = list(args)
    for i, a in enumerate(light):
        if a == "-preset" and i + 1 < len(light):
            light[i + 1] = "ultrafast"
        if a == "-threads" and i + 1 < len(light):
            light[i + 1] = "1"
    log("  ffmpeg: tentativa final com encoder leve")
    try:
        return ffmpeg(light, timeout)
    except RuntimeError:
        raise last


def duracao(path):
    r = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "csv=p=0", path], 30)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def ffpath(p):
    """Escapa um caminho Windows para uso dentro de um filtro do ffmpeg."""
    s = str(p).replace("\\", "/").replace("'", "")
    return "'" + s.replace(":", "\\:") + "'"


def _norm(t):
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^\w ]+|_", "", t).strip()  # \w: vale pra cirílico/devanágari/tailandês também


def _eh_narrador(persona):
    p = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona or "").strip().lower()
    return p in ("narrador", "narradora", "narrator")


def _ler_json(path):
    """Lê JSON tolerando arquivos antigos gravados em cp1252."""
    raw = Path(path).read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("cp1252"))


# ─── editorial (LLM) ─────────────────────────────────────────────────────────
_IMPACTO_HEUR = ["finalmente", "repente", "nunca", "segredo", "verdade", "beijo", "beijou",
                 "sangue", "morte", "morreu", "traicao", "choque", "chocada", "chocado",
                 "surpresa", "perigo", "medo", "grito", "gritou", "lagrimas", "chorou",
                 "explodiu", "confessou", "revelou", "impossivel", "inacreditavel"]
_EMOJI_HEUR = {"beijo": "💋", "beijou": "💋", "sangue": "🩸", "morte": "💀", "morreu": "💀",
               "medo": "😨", "perigo": "⚠️", "lagrimas": "😢", "chorou": "😢", "explodiu": "💥"}


def _parse_json(txt):
    if not txt:
        return None
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


PROXY_SECRETS = Path(os.environ.get("HIPER_PROXY_SECRETS", r"D:\manhwa-react\secrets_proxy.json"))
PROXY_MODELOS = ["antigravity/claude-opus-4-6-thinking", "kr/claude-sonnet-4.5", "kr/claude-haiku-4.5",
                 # 23/10 (dona: Kiro esgotou): Gemini do Antigravity como reserva no mesmo proxy
                 "agy/gemini-3.8-flash-high", "antigravity/gemini-3-flash"]


def _llm_json(prompt):
    """JSON do LLM: proxy compatível com a API Anthropic (o mesmo do manhwa-react /
    Claude do VS Code) e, se falhar, Gemini com poucas tentativas."""
    import urllib.request
    try:
        px = json.loads(PROXY_SECRETS.read_text(encoding="utf-8")) if PROXY_SECRETS.exists() else {}
    except (OSError, json.JSONDecodeError):
        px = {}
    base, key = (px.get("base_url") or "").rstrip("/"), px.get("auth_token")
    modelos = list(dict.fromkeys([m for m in (px.get("models") or {}).values() if m] + PROXY_MODELOS))
    for model in (modelos if base and key else []):
        body = {"model": model, "max_tokens": 2000, "temperature": 0.5,
                "messages": [{"role": "user", "content": prompt}]}
        req = urllib.request.Request(base + "/v1/messages", data=json.dumps(body).encode("utf-8"),
                                     headers={"x-api-key": key, "Authorization": f"Bearer {key}",
                                              "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=180).read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            log(f"  editorial: proxy {model} falhou ({str(e)[:100]})")
            continue
        out = _parse_json("".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text"))
        if out:
            log(f"  editorial: via proxy {model}")
            return out
    try:
        import gemini_llm
        out = _parse_json(gemini_llm.generate_text(prompt, max_tokens=1500, temperature=0.7, max_attempts=4))
        if out:
            log("  editorial: via Gemini")
        return out
    except Exception as e:  # noqa: BLE001
        log(f"  editorial: Gemini falhou ({str(e)[:100]})")
        return None


def _gancho_padrao(recap, titulo):
    base = (recap.get("titulo_video") or titulo or "").split(" - ")[0].split(":")[0]
    return " ".join(base.upper().split()[:6])


def _validar_editorial(ed, locs, recap, titulo):
    ed = ed if isinstance(ed, dict) else {}
    gancho = re.sub(r"\s+", " ", str(ed.get("gancho") or "")).strip().upper()
    if not gancho:
        gancho = _gancho_padrao(recap, titulo)
    gancho = " ".join(gancho.split()[:7])[:48]
    impactos, vistos = [], set()
    for it in ed.get("impactos") or []:
        try:
            idx = int(it.get("fala"))
        except (TypeError, ValueError, AttributeError):
            continue
        if idx in vistos or not (0 <= idx < len(locs)) or not _eh_narrador(locs[idx].get("persona")):
            continue
        palavra = _norm(it.get("palavra", "")).split()
        toks = [_norm(t) for t in (locs[idx].get("text") or "").split()]
        if not palavra or palavra[0] not in toks:
            continue
        impactos.append({"fala": idx, "palavra": palavra[0], "emoji": str(it.get("emoji") or "😳")[:4]})
        vistos.add(idx)
    if not impactos:
        # heurística: palavras fortes nas falas do narrador, espaçadas
        ultimo = -99
        for idx, l in enumerate(locs):
            if not _eh_narrador(l.get("persona")) or idx - ultimo < 8:
                continue
            for t in (l.get("text") or "").split():
                n = _norm(t)
                if n in _IMPACTO_HEUR:
                    impactos.append({"fala": idx, "palavra": n, "emoji": _EMOJI_HEUR.get(n, "😳")})
                    ultimo = idx
                    break
    pergunta = re.sub(r"\s+", " ", str(ed.get("pergunta") or "")).strip().upper()
    if not pergunta:
        pergunta = "E VOCÊ, O QUE FARIA?"
    return {"gancho": gancho, "impactos": sorted(impactos, key=lambda x: x["fala"])[:8],
            "pergunta": " ".join(pergunta.split()[:9])[:60]}


def editorial(recap, titulo, cache_file=None):
    """Gancho + impactos + pergunta do CTA. 1 chamada de LLM por capítulo, salva no cache."""
    if recap.get("_editorial", {}).get("fonte") == "llm":
        return recap["_editorial"]
    locs = recap.get("locucoes", [])
    linhas = [f"{i}: {(l.get('text') or '').strip()}" for i, l in enumerate(locs)
              if _eh_narrador(l.get("persona")) and (l.get("text") or "").strip()]
    ed = None
    if linhas and os.environ.get("HIPER_EDITORIAL_LLM", "1") != "0":
        prompt = (
            "Você é editor de vídeos de recap de manhwa para YouTube em português do Brasil. "
            f"Abaixo estão as falas do NARRADOR do capítulo \"{titulo}\", numeradas.\n"
            "Responda SÓ um JSON, sem texto fora dele:\n"
            '{"gancho": "...", "impactos": [{"fala": 0, "palavra": "...", "emoji": "..."}], "pergunta": "..."}\n'
            "Regras:\n"
            "- gancho: 3 a 6 palavras em MAIÚSCULAS que criam curiosidade nos 3 primeiros segundos "
            "(sem spoiler do final, sem palavrão, sem nada sexual explícito).\n"
            "- impactos: 5 a 8 momentos fortes ESPALHADOS pelo capítulo (virada, revelação, susto, ação). "
            "\"fala\" é o número da fala; \"palavra\" é UMA palavra que aparece EXATAMENTE nessa fala "
            "(a de mais peso dramático); \"emoji\": 1 emoji que combina.\n"
            "- pergunta: pergunta curta (até 8 palavras) para o público responder nos comentários.\n\n"
            "Falas:\n" + "\n".join(linhas)
        )
        ed = _llm_json(prompt)
        if not ed:
            log("  editorial: LLM indisponível -> heurística")
    fonte = "llm" if ed else "heuristica"
    ed = _validar_editorial(ed, locs, recap, titulo)
    ed["fonte"] = fonte
    recap["_editorial"] = ed
    if cache_file and fonte == "llm":  # heurística não vai pro cache: o próximo run tenta o LLM de novo
        try:
            Path(cache_file).write_text(json.dumps(recap, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            log(f"  [!] editorial não salvo no cache: {e}")
    log(f"  editorial: gancho='{ed['gancho']}', {len(ed['impactos'])} impactos, pergunta='{ed['pergunta']}'")
    return ed


# ─── tempo por palavra ───────────────────────────────────────────────────────
def _limites_fala(wav):
    """(início, fim) da fala dentro do wav, sem o silêncio das pontas."""
    total = duracao(wav)
    r = _run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "silencedetect=noise=-38dB:d=0.12",
              "-f", "null", "-"], 60)
    ini, fim = 0.0, total
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", r.stderr)]
    if starts and starts[0] <= 0.05 and ends:
        ini = ends[0]
    if starts and (len(ends) < len(starts) or ends[-1] >= total - 0.05) and starts[-1] > ini:
        fim = starts[-1]
    if fim - ini < 0.3:
        return 0.0, total
    return ini, fim


def _peso(tok):
    return len(_norm(tok)) + 2


def _pausa(tok):
    return 4 if tok.rstrip().endswith((",", ";", ":")) else (6 if tok.rstrip().endswith((".", "!", "?", "…")) else 0)


def _proporcional(toks, s0, s1, seg):
    """Distribui as palavras em [s0, s1] pelo tamanho (pontuação = pausa)."""
    pesos = [_peso(t) + _pausa(t) for t in toks[:-1]] + [_peso(toks[-1])]
    unit = (s1 - s0) / max(1, sum(pesos))
    out, t = [], s0
    for tok, p in zip(toks, pesos):
        out.append({"w": tok, "s": t, "e": t + _peso(tok) * unit, "seg": seg})
        t += p * unit
    return out


def _transcrever_groq(audio_src, tmp_dir, chunk=600.0, overlap=4.0):
    """Whisper-large-v3 no Groq com tempo por palavra (bin/groq_api: rodízio de chaves, sempre pelo proxy
    Webshare; pedaços de 10 min em FLAC, sem perda e com metade da banda do WAV)."""
    import groq_api
    if not groq_api.chaves():
        log("  tempo/palavra: sem chaves Groq")
        return None
    total = duracao(audio_src)
    n = max(1, int(-(-total // chunk)))
    words = []
    for i in range(n):
        a0 = i * chunk
        flac = Path(tmp_dir) / f"_groq_{i}.flac"
        ffmpeg(["-ss", f"{a0:.3f}", "-t", f"{chunk + overlap:.3f}", "-i", audio_src,
                "-vn", "-ac", "1", "-ar", "16000", "-c:a", "flac", flac])
        j = groq_api.transcrever(flac, IDIOMA or "pt")
        flac.unlink(missing_ok=True)
        if j is None:
            return None
        lo = a0 + (overlap / 2 if i > 0 else 0)
        hi = a0 + chunk + overlap / 2 if i < n - 1 else float("inf")
        for w in j.get("words") or []:
            txt = (w.get("word") or "").strip()
            s = a0 + float(w["start"])
            if txt and lo <= s < hi:
                words.append({"w": txt, "s": s, "e": a0 + float(w["end"])})
    words.sort(key=lambda w: w["s"])
    log(f"  tempo/palavra: Groq transcreveu {len(words)} palavras ({n} pedaço(s))")
    return words


def _alinhar(toks, janela, base):
    """Casa as palavras do roteiro com as do whisper; as sem par são interpoladas."""
    a = [_norm(t) for t in toks]
    b = [_norm(w["w"]) for w in janela]
    tempos = [None] * len(toks)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            tempos[blk.a + k] = (janela[blk.b + k]["s"], janela[blk.b + k]["e"])
    if sum(1 for t in tempos if t) < max(2, 0.4 * len(toks)):
        return None
    out = [dict(w) for w in base]
    i = 0
    while i < len(toks):
        if tempos[i]:
            out[i]["s"], out[i]["e"] = tempos[i]
            i += 1
            continue
        j = i
        while j < len(toks) and not tempos[j]:
            j += 1
        left = out[i - 1]["e"] if i > 0 else min(base[i]["s"], tempos[j][0] if j < len(toks) else base[i]["s"])
        right = tempos[j][0] if j < len(toks) else max(base[-1]["e"], left + 0.1)
        span = max(0.05, right - left)
        pesos = [_peso(t) for t in toks[i:j]]
        unit = span / sum(pesos)
        t = left
        for k, p in zip(range(i, j), pesos):
            out[k]["s"], out[k]["e"] = t, t + p * unit
            t += p * unit
        i = j
    for k in range(1, len(out)):  # monotônico
        if out[k]["s"] < out[k - 1]["s"]:
            out[k]["s"] = out[k - 1]["s"]
        out[k]["e"] = max(out[k]["e"], out[k]["s"] + 0.05)
    return out


GROQ_CACHE = PROJECT_DIR / "workspace" / "cache" / "groq"


def _chave_groq(segmentos):
    """Mesmas falas (texto + áudio da voz) nos mesmos tempos = mesma transcrição. O SFX
    sorteado a cada render muda o áudio mixado, mas não as palavras — por isso não entra."""
    h = hashlib.md5()
    for sg in segmentos:
        h.update(f"{sg['ini']:.2f}|{sg.get('atraso', 0.0):.2f}|{sg['texto']}|".encode("utf-8"))
        if sg.get("voz_wav") and Path(sg["voz_wav"]).exists():
            h.update(hashlib.md5(Path(sg["voz_wav"]).read_bytes()).digest())
    return h.hexdigest()


def tempos_palavras(audio_src, segmentos, tmp_dir):
    """segmentos: [{seg, texto, ini, fim, voz_wav, atraso}] (ini/fim = janela global do clip)."""
    groq = None
    if os.environ.get("HIPER_TEMPO_PALAVRA", "groq") == "groq":
        cache_f = GROQ_CACHE / f"{_chave_groq(segmentos)}.json"
        if cache_f.exists():
            groq = json.loads(cache_f.read_text(encoding="utf-8"))
            log(f"  tempo/palavra: Groq [CACHE] ({len(groq)} palavras)")
        else:
            try:
                groq = _transcrever_groq(audio_src, tmp_dir)
            except Exception as e:  # noqa: BLE001
                log(f"  tempo/palavra: Groq falhou ({str(e)[:120]})")
            if groq:
                GROQ_CACHE.mkdir(parents=True, exist_ok=True)
                cache_f.write_text(json.dumps(groq, ensure_ascii=False), encoding="utf-8")
    palavras, n_al = [], 0
    for sg in segmentos:
        toks = sg["texto"].split()
        if not toks:
            continue
        if sg.get("voz_wav") and Path(sg["voz_wav"]).exists():
            a, b = _limites_fala(sg["voz_wav"])
        else:
            a, b = 0.0, sg["fim"] - sg["ini"]
        s0 = sg["ini"] + sg.get("atraso", 0.0) + a
        s1 = min(sg["fim"], sg["ini"] + sg.get("atraso", 0.0) + b)
        base = _proporcional(toks, s0, max(s1, s0 + 0.3), sg["seg"])
        if groq:
            janela = [w for w in groq if sg["ini"] - 0.2 <= w["s"] < sg["fim"] + 0.1]
            al = _alinhar(toks, janela, base) if janela else None
            if al:
                base, n_al = al, n_al + 1
        palavras.extend(base)
    modo = f"Groq alinhado em {n_al}/{len(segmentos)} falas" if groq else "proporcional (sem Groq)"
    log(f"  tempo/palavra: {len(palavras)} palavras, {modo}")
    return palavras


# ─── sons por palavra / impacto ──────────────────────────────────────────────
_sfx_index = None


def _indice_sfx():
    """[(nome normalizado, caminho normalizado, Path)] — o caminho entra no bloqueio
    (ex.: pasta EARRAPE tem versões estouradas de sons com nome inocente)."""
    global _sfx_index
    if _sfx_index is None:
        _sfx_index = [(_norm(p.stem), _norm(" ".join(p.relative_to(lib).parts)), p)
                      for lib in SFX_LIBS if lib.exists() for p in lib.rglob("*")
                      if p.suffix.lower() in (".mp3", ".wav", ".ogg", ".m4a")]
    return _sfx_index


def _achar_som(fragmentos, bloqueio, max_s, rnd):
    """Som cujo nome contém um fragmento (ordem = preferência). Prefere até max_s;
    senão aceita o mais curto (o mixer usa só o começo: corta em 2.6s com fade,
    como o fx_foley já faz com os foleys longos)."""
    idx = _indice_sfx()
    for frag in fragmentos:
        f = _norm(frag)
        cands = [p for n, caminho, p in idx if f and f in n and not any(b in caminho for b in bloqueio)]
        rnd.shuffle(cands)
        durs = [(duracao(p), p) for p in cands[:6]]
        curtos = [p for d, p in durs if 0 < d <= max_s]
        if curtos:
            return curtos[0]
        longos = sorted((d, str(p)) for d, p in durs if d > max_s)
        if longos:
            return Path(longos[0][1])
    return None


def _sfx_impacto(rnd):
    opts = [SFX_DIR / n for n in ("deep_boom.wav", "new_impact_1.wav", "new_impact_2.wav", "impact.wav", "bass_hit.wav")]
    opts = [p for p in opts if p.exists()]
    return rnd.choice(opts) if opts else None


def _overlay_mov(nome):
    """MOV ProRes 4444 do acervo (pesado de decodificar) -> MOV PNG rgba leve, convertido 1x.
    Porte de manhwa-react/mr/pipeline._overlay_cache."""
    src = OVERLAYS_ELEMENTAL / f"{nome}.mov"
    if not src.exists():
        return None
    OV_CACHE.mkdir(parents=True, exist_ok=True)
    dst = OV_CACHE / src.name
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    try:
        ffmpeg(["-i", src, "-c:v", "png", "-pix_fmt", "rgba", "-an", dst], timeout=300)
        log(f"  overlay cache: {src.name}")
        return dst
    except RuntimeError as e:
        log(f"  [!] overlay cache falhou ({str(e)[:80]}); usando original")
        return src


def planejar_retencao(total, impactos_t, cta_ini):
    """Overlays animados de retenção (porte de mr/pipeline.py): "assiste até o fim" quando o
    gancho sai, like em ~45% do vídeo (longe dos impactos) e inscreva-se junto do CTA.
    Retorna (overlays_mov, sons_fixos). y = deslocamento vertical (os MOVs são tela cheia)."""
    ovs, sons = [], []
    imp = [i["t"] for i in impactos_t]
    if total > 35:
        mov = _overlay_mov("fx_watchtoend")
        if mov:
            ovs.append({"t": 3.0, "mov": mov, "dur": duracao(mov), "y": 0})
    if total > 20:
        lt = total * 0.45
        for _ in range(6):
            if all(abs(lt - x) > 3 for x in imp):
                break
            lt += 4.0
        mov = _overlay_mov("fx_likeburst")
        if mov and lt < total - 8:
            ovs.append({"t": lt, "mov": mov, "dur": duracao(mov), "y": -380})  # acima da legenda
            if (SFX_DIR / "page_turn.wav").exists():
                sons.append({"t": lt, "file": SFX_DIR / "page_turn.wav", "gain_db": -12, "prio": 3, "tipo": "like"})
    if cta_ini is not None:
        mov = _overlay_mov("fx_subscribe")
        if mov:
            ovs.append({"t": cta_ini, "mov": mov, "dur": duracao(mov), "y": -430})  # acima da legenda/CTA
        if (SFX_DIR / "magic_sparkle.wav").exists():
            sons.append({"t": cta_ini, "file": SFX_DIR / "magic_sparkle.wav", "gain_db": -9, "prio": 3, "tipo": "cta"})
    return ovs, sons


def planejar_sons(palavras, impactos_t, total, ocupados=(), sem_gatilho=(), fixos=(), seed="x"):
    """Retorna (eventos_sfx, emojis_gatilho). Anti-poluição: 1 som a cada 0.6s, longe dos SFX de corte.
    fixos: sons de evento já posicionados (like, CTA) — entram com prioridade menor."""
    rnd = random.Random(seed)
    eventos, emojis = [], []
    for imp in impactos_t:
        snd = _sfx_impacto(rnd)
        if snd:
            eventos.append({"t": max(0.0, imp["t"] - 0.03), "file": snd, "gain_db": -8, "prio": 1, "tipo": "impacto"})
    tab = {}
    if GATILHOS_FILE.exists():
        try:
            tab = json.loads(GATILHOS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            log(f"  [!] gatilhos_narracao.json inválido: {e}")
    gat = tab.get("gatilhos", [])
    bloqueio = [_norm(b) for b in tab.get("bloqueio_nomes", [])]
    cooldown = float(tab.get("cooldown_s", 6.0))
    max_n = int(tab.get("max_por_video", 10))
    gain = float(tab.get("gain_db", -10))
    max_s = float(tab.get("max_duracao_s", 2.6))
    for g in gat:
        g["_rx"] = re.compile(g["regex"])
    n_gat, ultimo = 0, -99.0
    imp_ts = [i["t"] for i in impactos_t]
    for w in palavras:
        if n_gat >= max_n:
            break
        tok, t = _norm(w["w"]), w["s"]
        if (not tok or t - ultimo < cooldown or t >= total - 1.0
                or any(a <= t <= b for a, b in sem_gatilho) or any(abs(t - x) < 1.5 for x in imp_ts)):
            continue
        for g in gat:
            if not g["_rx"].match(tok):
                continue
            snd = _achar_som(g.get("sons", []), bloqueio, max_s, rnd)
            if snd:
                eventos.append({"t": t, "file": snd, "gain_db": gain, "prio": 2, "tipo": g.get("nome")})
                if g.get("emoji"):
                    emojis.append({"t": t, "emoji": g["emoji"], "grande": False})
                n_gat += 1
                ultimo = t
            break
    eventos.extend(fixos)
    mantidos = []
    for ev in sorted(eventos, key=lambda e: (e["prio"], e["t"])):
        if any(abs(ev["t"] - k["t"]) < 0.6 for k in mantidos):
            continue
        if ev["prio"] > 1 and any(abs(ev["t"] - o) < 0.35 for o in ocupados):
            continue
        mantidos.append(ev)
    mantidos.sort(key=lambda e: e["t"])
    ts = {round(e["t"], 3) for e in mantidos}
    emojis = [e for e in emojis if round(e["t"], 3) in ts]
    tipos = {}
    for e in mantidos:
        tipos[e["tipo"]] = tipos.get(e["tipo"], 0) + 1
    log(f"  sons: {len(mantidos)} eventos ({', '.join(f'{k}={v}' for k, v in tipos.items())})")
    return mantidos, emojis


# ─── áudio: trilha nivelada + ducking + SFX + loudness 2 passos ─────────────
def loudnorm_dois_passos(wav_in, wav_out, alvo=LUFS_ALVO, tp=-1.0, lra=11):
    base = f"loudnorm=I={alvo}:TP={tp}:LRA={lra}"
    r = _run(["ffmpeg", "-hide_banner", "-i", wav_in, "-af", base + ":print_format=json", "-f", "null", "-"], 900)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        log("  [!] loudnorm passo 1 sem medição; aplicando passo único")
        ffmpeg(["-i", wav_in, "-af", base, "-ar", "48000", "-c:a", "pcm_s16le", wav_out])
        return None
    j = json.loads(m.group(0))
    seg = (base + f":measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
           f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    ffmpeg(["-i", wav_in, "-af", seg, "-ar", "48000", "-c:a", "pcm_s16le", wav_out])
    log(f"  loudness: {j['input_i']} LUFS -> {alvo} LUFS (pico {tp} dBTP)")
    return float(j["input_i"])


def masterizar_audio(video_in, out_mp4, musica, sfx, tmp_dir, respiro=0.0):
    """respiro: segundos de áudio a mais depois do fim do vídeo (só trilha); quem estende a imagem é o
    passe_final. Com respiro o mp4 sai com o áudio mais longo que o vídeo, de propósito."""
    tmp_dir = Path(tmp_dir)
    total = duracao(video_in) + max(0.0, respiro)
    pad = f",apad=whole_dur={total:.3f}" if respiro > 0 else ""
    linhas = [f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo{pad}[a0]"]
    inputs = ["-i", video_in]
    mix = ["[a0]"]
    idx = 1
    for ev in sfx:
        inputs += ["-i", ev["file"]]
        ms = int(max(0.0, ev["t"]) * 1000)
        linhas.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:2.6,"
                      f"afade=t=out:st=2.2:d=0.4,volume={ev.get('gain_db', -10)}dB,adelay={ms}|{ms}[s{idx}]")
        mix.append(f"[s{idx}]")
        idx += 1
    if musica and Path(musica).exists():
        inputs += ["-stream_loop", "-1", "-i", musica]
        linhas.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{total:.2f},"
                      f"loudnorm=I={MUSICA_LUFS}:TP=-3:LRA=7,aresample=48000,"
                      f"afade=t=in:d=1.5,afade=t=out:st={max(0.0, total - 3):.2f}:d=3[mus]")
        linhas[0] = f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo{pad},asplit=2[a0][sc]"
        linhas.append("[mus][sc]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500:makeup=1[musd]")
        mix.append("[musd]")
    linhas.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first:dropout_transition=0[amix]")
    script = tmp_dir / "_audio_graph.txt"
    script.write_text(";\n".join(linhas), encoding="utf-8")
    mixed, final = tmp_dir / "_mixed.wav", tmp_dir / "_final.wav"
    ffmpeg([*inputs, "-filter_complex_script", script, "-map", "[amix]", "-ar", "48000", "-ac", "2",
            "-c:a", "pcm_s16le", mixed], timeout=1800)
    antes = loudnorm_dois_passos(mixed, final)
    ffmpeg(["-i", video_in, "-i", final, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", *([] if respiro > 0 else ["-shortest"]), out_mp4],
           timeout=900)
    for f in (mixed, final, script):
        f.unlink(missing_ok=True)
    log(f"  áudio masterizado: {len(sfx)} SFX, trilha={'sim' if musica else 'não'}")
    return antes


# ─── emoji ───────────────────────────────────────────────────────────────────
def emoji_png(emoji, size=220):
    """Emoji colorido em PNG (Segoe UI Emoji). libass não pinta emoji colorido."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    emoji = (emoji or "").strip()
    if not emoji:
        return None
    EMOJI_DIR.mkdir(parents=True, exist_ok=True)
    key = "_".join(f"{ord(c):x}" for c in emoji)[:40]
    p = EMOJI_DIR / f"e_{key}_{size}.png"
    if p.exists():
        return p
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 109)  # só rasteriza em 109px
        im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((size * 0.5, size * 0.4), emoji, font=font, embedded_color=True)
        bbox = im.getbbox()
        if not bbox:
            return None
        im = im.crop(bbox)
        im = im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)
        glow = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.paste((0, 0, 0, 160), (0, 0), im.split()[3])
        glow.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), (20, 24))
        glow.alpha_composite(im, (20, 20))
        glow.save(p)
        return p
    except Exception as e:  # noqa: BLE001
        log(f"  emoji: falhou ({e})")
        return None


# ─── ASS ─────────────────────────────────────────────────────────────────────
def _ts(t):
    t = max(0.0, float(t))
    return f"{int(t // 3600)}:{int((t % 3600) // 60):02d}:{t % 60:05.2f}"


def _esc(txt):
    return str(txt).replace("{", "(").replace("}", ")").replace("\\", "/")


def ass_color(hex_rgb, alpha="00"):
    """'#RRGGBB' -> '&HAABBGGRR'."""
    h = hex_rgb.lstrip("#")
    if len(h) != 6:
        return "&H0000D4FF"
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def _limpa(w):
    w = re.sub(r"^[\"'(\[“”‘’«]+|[\"')\]“”‘’»]+$", "", w.strip())
    return w.upper()


def _blocos(palavras, max_words=3, max_span=1.4, max_gap=0.6, max_chars=18):
    """max_chars: o Cap (110 px, uma linha só, sem quebra) cabe ~18 letras maiúsculas em 1080 px."""
    blocos, cur = [], []
    for w in palavras:
        if cur:
            fim_frase = cur[-1]["w"].rstrip().endswith((".", "!", "?", ",", "…", ";", ":"))
            largo = len(" ".join(x["w"].strip() for x in cur + [w])) > max_chars
            if (len(cur) >= max_words or w["s"] - cur[-1]["e"] > max_gap or w["e"] - cur[0]["s"] > max_span
                    or fim_frase or largo or w["seg"] != cur[-1]["seg"]):
                blocos.append(cur)
                cur = []
        cur.append(w)
    if cur:
        blocos.append(cur)
    return blocos


def _wrap(text, width, max_linhas=3):
    linhas, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > width:
            linhas.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        linhas.append(cur)
    return "\\N".join(linhas[:max_linhas])


def montar_ass(caminho, palavras, total, ed, impactos_t, obra, cap_num, legendas=True):
    hl = ass_color(COR)
    estilos = [
        f"Style: Cap,Montserrat ExtraBold,110,&H00FFFFFF,{hl},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1",
        f"Style: Hook,Luckiest Guy,96,{hl},&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,8,4,8,60,60,0,1",
        "Style: Mark,Montserrat ExtraBold,34,&H55FFFFFF,&H00FFFFFF,&H55000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,9,30,30,30,1",
        "Style: Selo,Montserrat ExtraBold,40,&H00101010,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,4,0,0,0,1",
        f"Style: Bar,Arial,20,{hl},&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        f"Style: Key,Bangers,150,{hl},&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,2,0,1,8,4,5,60,60,0,1",
        "Style: CTA,Luckiest Guy,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,230,1",
    ]
    if IDIOMA:  # alfabetos que as fontes latinas não têm (devanágari, tailandês; cirílico no gancho)
        import idiomas
        info = idiomas.IDIOMAS.get(IDIOMA, {})
        base = info.get("fonte_ass")
        gancho = info.get("fonte_ass_hook") or base
        estilos = [e.replace("Montserrat ExtraBold", base) if base else e for e in estilos]
        estilos = [e.replace("Luckiest Guy", gancho).replace("Bangers", gancho) if gancho else e for e in estilos]
    ev = []
    cta_ini = max(0.0, total - CTA_SEGUNDOS)
    # legenda palavra a palavra (palavra ativa na cor de destaque + pop)
    if legendas and palavras:
        blocos = _blocos(palavras)
        for bi, bl in enumerate(blocos):
            toks = [_limpa(w["w"]) for w in bl]
            prox = blocos[bi + 1][0]["s"] if bi + 1 < len(blocos) else total
            for i, w in enumerate(bl):
                ini = w["s"]
                fim = bl[i + 1]["s"] if i + 1 < len(bl) else min(w["e"] + 0.25, prox, total)
                if fim - ini < 0.05:
                    fim = ini + 0.05
                partes = []
                for j, tok in enumerate(toks):
                    if not tok:
                        continue
                    if j == i:
                        partes.append(f"{{\\c{hl}\\t(0,70,\\fscx113\\fscy113)\\t(70,150,\\fscx100\\fscy100)}}{_esc(tok)}{{\\r}}")
                    else:
                        partes.append(_esc(tok))
                ev.append(f"Dialogue: 2,{_ts(ini)},{_ts(fim)},Cap,,0,0,0,,{{\\an5\\pos({OW // 2},{CAP_Y})}}" + " ".join(partes))
    # gancho nos primeiros segundos
    if ed.get("gancho"):
        hs = min(2.8, max(1.5, total - 1))
        ev.append(f"Dialogue: 3,{_ts(0)},{_ts(hs)},Hook,,0,0,0,,{{\\an8\\pos({OW // 2},{HOOK_Y})\\fscx0\\fscy0"
                  f"\\t(0,160,\\fscx108\\fscy108)\\t(160,240,\\fscx100\\fscy100)\\fad(0,250)}}" + _wrap(_esc(ed["gancho"]), 14, 4))
    # selo do capítulo (entra deslizando, some sozinho). SEM o nome da obra: o dono proibiu o nome em qualquer lugar
    # (15/10, direitos autorais) — antes era "OBRA • CAP. N".
    import idiomas
    selo = idiomas.texto(IDIOMA, "cap", n=cap_num) if cap_num else ""
    if selo:
        try:  # largura real do texto na fonte do estilo Selo (estimar por nº de letras sobrava caixa)
            larg = int(_fonte("Montserrat-ExtraBold.ttf", 40).getlength(selo)) + 48
        except Exception:  # noqa: BLE001
            larg = int(len(selo) * 22 + 48)
        alt = 64
        t0, t1 = 0.3, min(6.0, total)
        ev.append(f"Dialogue: 4,{_ts(t0)},{_ts(t1)},Bar,,0,0,0,,{{\\an7\\move({-larg - 20},{SELO_Y},36,{SELO_Y},0,260)"
                  f"\\fad(0,300)\\p1\\c{hl}}}m 0 0 l {larg} 0 l {larg} {alt} l 0 {alt}{{\\p0}}")
        ev.append(f"Dialogue: 5,{_ts(t0)},{_ts(t1)},Selo,,0,0,0,,{{\\an4\\move({-larg + 4},{SELO_Y + alt // 2},60,"
                  f"{SELO_Y + alt // 2},0,260)\\fad(0,300)}}{selo}")
    # marca d'água
    if WATERMARK_HANDLE:
        ev.append(f"Dialogue: 1,{_ts(0)},{_ts(total)},Mark,,0,0,0,,{{\\an9\\pos({OW - 30},40)}}{_esc(WATERMARK_HANDLE)}")
    # barra de progresso
    h = 10
    rect = f"m 0 0 l {OW} 0 l {OW} {h} l 0 {h}"
    ev.append(f"Dialogue: 0,{_ts(0)},{_ts(total)},Bar,,0,0,0,,{{\\an7\\pos(0,{OH - h})\\p1\\alpha&H99&\\c&H000000&}}{rect}{{\\p0}}")
    ev.append(f"Dialogue: 1,{_ts(0)},{_ts(total)},Bar,,0,0,0,,{{\\an7\\pos(0,{OH - h})\\p1\\fscx0"
              f"\\t(0,{int(total * 1000)},\\fscx100)}}{rect}{{\\p0}}")
    # palavra de impacto gigante
    for imp in impactos_t:
        t = imp["t"]
        txt = _limpa(imp["texto"]).rstrip(".,;:!?…")[:16]  # palavra gigante sem pontuação
        if txt and t < total - 0.5:
            ev.append(f"Dialogue: 6,{_ts(t)},{_ts(min(t + 1.3, total))},Key,,0,0,0,,{{\\an5\\pos({OW // 2},{KEY_Y})"
                      f"\\fscx0\\fscy0\\t(0,110,\\fscx118\\fscy118)\\t(110,190,\\fscx100\\fscy100)\\fad(0,150)}}{_esc(txt)}")
    # CTA por cima do último painel
    if total > 8:
        prox = idiomas.texto(IDIOMA, "segue", n=cap_num + 1) if cap_num else idiomas.texto(IDIOMA, "mais")
        ev.append(f"Dialogue: 7,{_ts(cta_ini)},{_ts(total)},CTA,,0,0,0,,{{\\an2\\fad(200,0)\\fscx90\\fscy90"
                  f"\\t(0,160,\\fscx100\\fscy100)}}{_wrap(_esc(ed.get('pergunta', '')), 22)}\\N{{\\c{hl}}}{prox}")
    header = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {OW}", f"PlayResY: {OH}", "WrapStyle: 2",
              "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
              "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
              "Alignment, MarginL, MarginR, MarginV, Encoding",
              *estilos, "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    Path(caminho).write_text("\n".join(header + ev) + "\n", encoding="utf-8")
    log(f"  legendas ASS: {len(ev)} eventos")
    return caminho


def _posicao_figurinha(video, t, tmp_dir, lado=480):
    """(x, y) da figurinha (tela OWxOH) onde ela não tampa balão no quadro do instante t: o centro se estiver livre
    (até 2% de balão), senão alto/laterais, senão o lugar com menos balão. None se não deu pra ler o quadro."""
    import cv2
    from censura_visual import _mascara_baloes
    q = Path(tmp_dir) / "_quadro_meme.jpg"
    _run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t + 0.3:.2f}", "-i", str(video), "-frames:v", "1",
          "-vf", f"scale={OW}:{OH}", str(q)], 60)
    im = cv2.imread(str(q)) if q.exists() else None
    q.unlink(missing_ok=True)
    if im is None:
        return None
    m = _mascara_baloes(im) > 0
    cands = [((OW - lado) // 2, (OH - lado) // 2 - 160), ((OW - lado) // 2, 260), (40, (OH - lado) // 2 - 160),
             (OW - lado - 40, (OH - lado) // 2 - 160), (40, 260), (OW - lado - 40, 260)]  # nunca na faixa da legenda
    cobre = {c: float(m[c[1]:c[1] + lado, c[0]:c[0] + lado].mean()) for c in cands}
    return next((c for c in cands if cobre[c] <= 0.02), min(cands, key=cobre.get))


def _ass_chamada_sem_censura(ass, tmp_dir, offs, durs, idx_cens, total, idioma=None):
    """Legenda da versão CENSURADA: a do vídeo + chamada no começo de cada trecho censurado pedindo pra comentar
    "SEM CENSURA" (mede quantos querem). Sem link nem site (link pra conteúdo adulto fere a política do YouTube).
    Só pt; no máx. 1 a cada 45 s, fora dos 5 s iniciais e dos 12 s finais (CTA). Sem trecho: a mesma legenda."""
    if idioma or not idx_cens:
        return ass
    trechos = []
    for k in sorted(idx_cens):
        if k >= len(offs):
            continue
        a, b = offs[k], offs[k] + durs[k]
        if trechos and a - trechos[-1][1] < 1.0:
            trechos[-1][1] = b
        else:
            trechos.append([a, b])
    ev, ultimo = [], -99.0
    for a, b in trechos:
        t0 = a + 0.3
        if t0 < 5 or t0 > total - 12 or t0 - ultimo < 45 or b - t0 < 1.5:
            continue
        t1 = min(b, t0 + 3.5)
        ev.append(f"Dialogue: 6,{_ts(t0)},{_ts(t1)},Hook,,0,0,0,,{{\\an8\\pos({OW // 2},300)\\fs64\\fad(150,250)}}"
                  f"CENSURADO PRO YOUTUBE\\N{{\\fs50}}QUER SEM CENSURA? COMENTA \"SEM CENSURA\"")
        ultimo = t0
    if not ev:
        return ass
    out = Path(tmp_dir) / "legendas_cens.ass"
    out.write_text(Path(ass).read_text(encoding="utf-8").rstrip("\n") + "\n" + "\n".join(ev) + "\n", encoding="utf-8")
    log(f"  censurada: chamada 'SEM CENSURA' em {len(ev)} de {len(trechos)} trechos censurados")
    return out


# ─── passe final de vídeo ────────────────────────────────────────────────────
def _enable(janelas):
    return "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in janelas)


def _clipe_parado(img, dur):
    """Imagem parada como clipe .mov curto (qtrle, com alfa), em cache. Entrada '-loop 1 -i imagem' trava o ffmpeg 8
    no passe final (15/10: o cap 8 parava sempre no mesmo quadro, sem usar CPU; o cap 6 ficou 2 h preso); o mesmo
    passe com clipe de vídeo roda normal.

    16/10: a imagem é lida UMA vez e o quadro é repetido pelo filtro `loop`. Com '-loop 1' o ffmpeg relê o
    arquivo a cada quadro, e um meme ruim derruba o capítulo inteiro — foi o que aconteceu com
    'pngtree-angry-emoticon-picture-image_13041600.png', que traz DOIS PNGs colados (2 chunks IEND, 1 entre
    96 memes): ao tentar ler o segundo, o ffmpeg entrava em laço gastando CPU e só parava no timeout de
    5 min, levando junto 44 min de render do cap 2. Lendo uma vez, o mesmo arquivo sai em menos de 1 s."""
    img = Path(img)
    chave = hashlib.md5(f"{img.resolve()}|{img.stat().st_mtime_ns}|v2".encode()).hexdigest()[:10]
    mov = CLIPES_DIR / f"{img.stem[:40]}_{chave}_{dur:.2f}.mov"
    if not mov.exists():
        CLIPES_DIR.mkdir(parents=True, exist_ok=True)
        tmp = mov.with_name(mov.stem + "_tmp.mov")
        n = max(1, int(round(dur * 25)))
        ffmpeg(["-i", img, "-vf", f"loop=loop={n - 1}:size=1:start=0,fps=25,format=argb",
                "-frames:v", str(n), "-c:v", "qtrle", tmp], timeout=120)
        os.replace(tmp, mov)
    return mov


def passe_final(video_in, ass_path, emojis, janelas_zoom, out_mp4, tmp_dir, movs=(), memes=(), respiro=0.0):
    """UM encode: upscale + cas + punch-in/tremor (janelas) + overlays MOV + emoji (pop) + memes + ASS.
    Áudio copiado. respiro: o último quadro fica parado esses segundos (o áudio já vem com a sobra)."""
    parado = f",tpad=stop_mode=clone:stop_duration={respiro:.3f}" if respiro > 0 else ""
    linhas = [f"[0:v]fps=30{parado},scale={OW}:{OH}:flags=lanczos,cas=0.35,setsar=1[up]"]
    cur = "up"
    if janelas_zoom:
        z = 1.12
        zw, zh = int(OW / z) // 2 * 2, int(OH / z) // 2 * 2
        en = _enable(janelas_zoom)
        # tranco visível que some em 0,45 s (cabe na margem do zoom: ~58 px de cada lado)
        tranco = "+".join(f"between(t,{a:.3f},{b:.3f})*max(0,1-(t-{a:.3f})/0.45)" for a, b in janelas_zoom)
        linhas.append(f"[{cur}]split=2[uA][uB]")
        linhas.append(f"[uB]crop={zw}:{zh}:x='{(OW - zw) // 2}+26*sin(t*43)*({tranco})':"
                      f"y='{(OH - zh) // 2}+26*cos(t*37)*({tranco})',scale={OW}:{OH}:flags=bicubic[uZ]")
        linhas.append(f"[uA][uZ]overlay=0:0:enable='{en}'[zz]")
        cur = "zz"
    extra = []
    idx = 1
    for i, m in enumerate(movs):
        # setpts desloca o MOV pro instante certo sem gerar quadros vazios (tpad de tela
        # cheia por minutos pesava); antes de começar e depois do fim o overlay só passa.
        t0 = m["t"]
        extra += ["-i", str(m["mov"])]
        linhas.append(f"[{idx}:v]format=rgba,scale={OW}:{OH},setpts=PTS-STARTPTS+{t0:.3f}/TB[mv{i}]")
        linhas.append(f"[{cur}][mv{i}]overlay=0:{int(m.get('y', 0))}:eof_action=pass:format=auto[om{i}]")
        cur = f"om{i}"
        idx += 1
    n_movs = idx - 1
    for i, e in enumerate(emojis):
        png = emoji_png(e["emoji"])
        if not png:
            continue
        dur = 1.3 if e.get("grande") else 1.1
        w = 230 if e.get("grande") else 150
        x, y = (OW // 2, KEY_Y - 210) if e.get("grande") else (OW - 130, 470)
        t0, t1 = e["t"], e["t"] + dur
        extra += ["-i", str(_clipe_parado(png, dur + 0.5))]
        linhas.append(f"[{idx}:v]format=rgba,scale={w}:-1,tpad=start_duration={t0:.3f}:start_mode=add:color=black@0.0[e{i}]")
        linhas.append(f"[{cur}][e{i}]overlay=x={x - w // 2}:y='{y - w // 2}-30*sin(min((t-{t0:.3f})*8,3.1416))':"
                      f"eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[o{i}]")
        cur = f"o{i}"
        idx += 1
    n_memes = 0
    for mi, meme in enumerate(memes):
        arq = Path(meme["arquivo"])
        if not arq.exists():
            continue
        t0m = meme["t"]
        dur_m = meme.get("dur", 2.0)
        t1m = t0m + dur_m
        # imagem parada precisa repetir o quadro pela duração (sem isso aparecia 1 quadro só): vira clipe .mov
        parada = arq.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".avif")
        try:
            entrada = str(_clipe_parado(arq, dur_m) if parada else arq)
        except Exception as e:  # noqa: BLE001 — figurinha é enfeite: não derruba o capítulo
            # Em 16/10 um meme com dois PNGs colados travou o ffmpeg e levou junto 44 min de render do
            # cap 2. Enfeite que não abre é enfeite a menos, não capítulo perdido.
            log(f"  [!] figurinha {arq.name} pulada: {str(e)[:100]}")
            continue
        extra += ["-i", entrada]
        # figurinha ESTAMPADA no centro, acima da legenda, sem som (o meme com som entra como clip que
        # interrompe o vídeo — fx_memes.escolher_interrupcoes no hiper-pipeline)
        linhas.append(f"[{idx}:v]scale=480:480:force_original_aspect_ratio=decrease,format=rgba,"
                      f"setpts=PTS-STARTPTS+{t0m:.3f}/TB[mf{mi}]")
        # lugar sem balão (_posicao_figurinha, caixa de 480: centraliza dentro dela); sem posição = centro
        mx = f"{meme['x']}+(480-overlay_w)/2" if "x" in meme else "(main_w-overlay_w)/2"
        my = f"{meme['y']}+(480-overlay_h)/2" if "y" in meme else "(main_h-overlay_h)/2-160"
        linhas.append(f"[{cur}][mf{mi}]overlay=x='{mx}':"
                      f"y='{my}-20*sin(min((t-{t0m:.3f})*6,3.1416))':"
                      f"eof_action=pass:enable='between(t,{t0m:.3f},{t1m:.3f})'[omm{mi}]")
        cur = f"omm{mi}"
        idx += 1
        n_memes += 1
    linhas.append(f"[{cur}]ass=filename={ffpath(ass_path)}:fontsdir={ffpath(FONTS_DIR)},format=yuv420p[vout]")
    script = Path(tmp_dir) / "_video_graph.txt"
    script.write_text(";\n".join(linhas), encoding="utf-8")
    base = ["-i", video_in, *extra, "-filter_complex_script", script, "-map", "[vout]", "-map", "0:a"]
    fim = ["-g", "60", "-c:a", "copy", "-movflags", "+faststart", out_mp4]
    x264 = ["-c:v", "libx264", "-preset", PRESET, "-crf", CRF, "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-level", "4.1", "-threads", THREADS]
    # Quick Sync (GPU Intel UHD 620): codifica ~3x mais rápido que o x264 e libera a CPU pros filtros.
    qsv = ["-c:v", "h264_qsv", "-global_quality", CRF, "-preset", "medium", "-profile:v", "high"]
    usar_qsv = os.environ.get("HIPER_QSV", "1") != "0"
    log(f"  passe final: upscale+nitidez, {len(janelas_zoom)} punch-ins, {n_movs} overlays, "
        f"{idx - 1 - n_movs - n_memes} emojis, {n_memes} memes, ASS -> {Path(out_mp4).name} "
        f"[{'Quick Sync' if usar_qsv else 'x264'}]")
    t0 = time.time()
    try:
        if not usar_qsv:
            raise RuntimeError("Quick Sync desligado (HIPER_QSV=0)")
        ffmpeg([*base, *qsv, *fim], timeout=3600)  # normal: 13-20 min
    except (RuntimeError, subprocess.TimeoutExpired) as e:  # travou (cap 6, 15/10: 2 h) -> mesmo passe no x264
        if usar_qsv:
            log(f"  passe final: Quick Sync falhou ({str(e)[:120]}) -> x264")
        ffmpeg_retry([*base, *x264, *fim], timeout=7200)
    log(f"  passe final: {time.time() - t0:.0f} s")
    script.unlink(missing_ok=True)
    return out_mp4


# ─── validação ───────────────────────────────────────────────────────────────
def validar(mp4, esperado=None):
    rel = {"ok": True, "problemas": []}
    r = _run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,duration:format=duration",
              "-of", "json", mp4], 60)
    try:
        info = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "problemas": ["ffprobe falhou"]}
    dur = float(info.get("format", {}).get("duration", 0))
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)
    rel["duracao"] = round(dur, 2)
    if not v or not a:
        rel["problemas"].append("faltando vídeo ou áudio")
    if v and (int(v.get("width", 0)), int(v.get("height", 0))) != (OW, OH):
        rel["problemas"].append(f"resolução {v.get('width')}x{v.get('height')}")
    if v and a:
        dv, da = float(v.get("duration") or dur), float(a.get("duration") or 0)
        rel["audio_vs_video_s"] = round(dv - da, 2)
        if dv - da > 1.5:
            rel["problemas"].append(f"áudio {dv - da:.1f}s menor que o vídeo")
    # Tolerância proporcional (16/10): o passe final sempre entrega alguns décimos a menos que o
    # concat, e em vídeo longo isso vira segundos — cap 1 (-3,1 s), cap 9 (-3,1), cap 11 (-2,6)
    # saíram bons e o cap 3 (-4,1 s em 5,5 min, 1,2%) foi marcado INVÁLIDO por 2,6 s acima do teto
    # fixo. 1,5% ainda pega vídeo truncado de verdade, que é o que esta checagem existe pra achar.
    if esperado and abs(dur - esperado) > max(1.5, esperado * 0.015):
        rel["problemas"].append(f"duração {dur:.1f}s (esperado {esperado:.1f}s)")
    elif esperado and abs(dur - esperado) > 1.5:
        rel.setdefault("avisos", []).append(f"duração {dur:.1f}s, {esperado - dur:+.1f}s do concat")
    r = _run(["ffmpeg", "-hide_banner", "-i", mp4, "-vf", "blackdetect=d=0.6:pix_th=0.10", "-af", "ebur128",
              "-f", "null", "-"], 1800)
    ms = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    if ms:
        rel["lufs"] = float(ms[-1])
        if abs(rel["lufs"] - LUFS_ALVO) > 2.0:
            rel["problemas"].append(f"loudness {rel['lufs']} LUFS")
    pretos = re.findall(r"black_start:(\S+) black_end:(\S+)", r.stderr)
    if pretos:
        rel["trechos_pretos"] = [[float(a), float(b)] for a, b in pretos][:10]
        rel["problemas"].append(f"{len(pretos)} trecho(s) preto(s)")
    rel["ok"] = not rel["problemas"]
    log(f"  validação: {'OK' if rel['ok'] else 'PROBLEMAS: ' + '; '.join(rel['problemas'])} "
        f"(dur {rel.get('duracao')}s, {rel.get('lufs', '?')} LUFS)")
    return rel


def descontar_pretos_da_arte(rel, fronteiras, painel_do_clip, limiar_lum=45):
    """Trecho preto que cai num clip cujo PAINEL já é escuro (noite, fundo preto da arte) não é defeito
    de render: tira do 'problemas'. painel_do_clip(k) -> Path do painel do clip k (ou None)."""
    from PIL import Image, ImageStat
    pretos = (rel or {}).get("trechos_pretos") or []
    if not pretos or not fronteiras:
        return rel
    defeito, arte = [], []
    for a, b in pretos:
        k = max((j for j, o in enumerate(fronteiras) if o <= (a + b) / 2), default=0)
        p = painel_do_clip(k)
        lum = ImageStat.Stat(Image.open(p).convert("L")).mean[0] if p else 255
        (arte if lum < limiar_lum else defeito).append([a, b])
    rel["pretos_da_arte"] = arte
    if not defeito:
        rel["problemas"] = [x for x in rel["problemas"] if "preto" not in x]
        rel["ok"] = not rel["problemas"]
        log(f"  validação: {len(arte)} trecho(s) escuro(s) é a própria arte (painel escuro) — OK")
    return rel


# ─── capa / thumbnail ────────────────────────────────────────────────────────
def _nota_painel(path):
    from PIL import Image, ImageFilter, ImageStat
    import numpy as np
    im = Image.open(path).convert("RGB")
    ratio = im.height / max(1, im.width)
    im.thumbnail((320, 320))
    arr = np.asarray(im).astype("float32")
    rg = arr[..., 0] - arr[..., 1]
    yb = 0.5 * (arr[..., 0] + arr[..., 1]) - arr[..., 2]
    cor = float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2))
    nitidez = ImageStat.Stat(im.convert("L").filter(ImageFilter.FIND_EDGES)).var[0] ** 0.5
    brilho = ImageStat.Stat(im.convert("L")).mean[0]
    nota = cor + 0.6 * nitidez
    if brilho < 45 or brilho > 225:
        nota *= 0.5
    if ratio > 2.4 or ratio < 0.5:
        nota *= 0.6
    return nota


def _pedacos_sem_quebrar_acento(s, n):
    """Corta s em pedaços de ~n caracteres, só antes de letra-base (marca combinante fica com a letra)."""
    out, cur = [], ""
    for c in s:
        if len(cur) >= n and unicodedata.category(c) != "Mn":
            out.append(cur)
            cur = ""
        cur += c
    return out + ([cur] if cur else [])


def _fonte(nome, tam):
    from PIL import ImageFont
    try:
        return ImageFont.truetype(str(FONTS_DIR / nome), tam)
    except OSError:
        return ImageFont.truetype("C:/Windows/Fonts/impact.ttf", tam)


FACE_CASCADE = Path(r"D:\hipercool-materiais\models\lbpcascade_animeface.xml")


def _rosto_unico(p, _c={}):
    """(x, y, w, h) do rosto de anime se o painel tiver EXATAMENTE um (lbpcascade_animeface), senão None."""
    import cv2
    if "c" not in _c:
        _c["c"] = cv2.CascadeClassifier(str(FACE_CASCADE)) if FACE_CASCADE.exists() else None
    if _c["c"] is None:
        return None
    g = cv2.equalizeHist(cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2GRAY))
    f = _c["c"].detectMultiScale(g, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    return tuple(int(v) for v in f[0]) if len(f) == 1 else None


def _escolher_painel_capa(cands):
    """(painel, rosto, recortavel). Prefere painel com UM rosto grande e bonito; recortavel = o personagem
    dá um recorte limpo (uma figura só, 15-55% do painel, encosta em no máx. 1 borda)."""
    import cv2
    import numpy as np
    com_rosto = [(p, r) for p in cands if (r := _rosto_unico(p))]
    if not com_rosto:
        return max(cands, key=_nota_painel), None, False
    p, rosto = max(com_rosto, key=lambda pr: _nota_painel(pr[0]) * (pr[1][3] ** 0.5))
    try:
        import fx_parallax
        ok, frac = fx_parallax.elegivel(p)
        m = (fx_parallax.mascara(p) > 127).astype(np.uint8)
        n, _lab, st, _cen = cv2.connectedComponentsWithStats(m, 8)
        if not (ok and 0.15 <= frac <= 0.55 and n >= 2):
            return p, rosto, False
        maior = int(np.argmax(st[1:, cv2.CC_STAT_AREA])) + 1
        x, y, w, h = st[maior, :4]
        H_, W_ = m.shape
        bordas = (x <= 2) + (y <= 2) + (x + w >= W_ - 2) + (y + h >= H_ - 2)
        return p, rosto, bool(st[maior, cv2.CC_STAT_AREA] >= 0.75 * m.sum() and bordas <= 1)
    except Exception:  # noqa: BLE001
        return p, rosto, False


def _colar_personagem(capa, painel, W, H):
    """Cola o personagem recortado grande à direita, 'saindo' da capa, com luz radial atrás, brilho de
    contorno e sombra. Retorna o x da borda esquerda dele (pra área do texto)."""
    import numpy as np
    from PIL import Image, ImageFilter
    import fx_parallax
    rgb = Image.open(painel).convert("RGB")
    m = fx_parallax.mascara(painel)
    a = Image.fromarray(((m > 110) * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.2))
    bbox = a.getbbox()
    pers = Image.merge("RGBA", (*rgb.split(), a)).crop(bbox)
    esc = min(H * 1.08 / pers.height, W * 0.55 / pers.width)
    pers = pers.resize((int(pers.width * esc), int(pers.height * esc)), Image.LANCZOS)
    x = W - pers.width + int(pers.width * 0.06)
    y = 12
    # luz radial atrás do personagem
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = x + pers.width / 2, y + pers.height * 0.35
    luz = np.clip(1 - np.hypot((xx - cx) / (W * 0.45), (yy - cy) / (H * 0.7)), 0, 1) ** 1.6
    fundo = np.asarray(capa).astype(np.float32)
    amarelo = np.array([255, 214, 90], np.float32)
    fundo = fundo * (1 - 0.45 * luz[..., None]) + amarelo * 0.45 * luz[..., None]
    capa.paste(Image.fromarray(fundo.astype("uint8")))
    alfa = pers.split()[3]
    sombra = Image.new("RGBA", pers.size, (0, 0, 0, 0))
    sombra.putalpha(alfa.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.7)))
    capa.paste(sombra, (x + 14, y + 18), sombra)
    brilho = Image.new("RGBA", pers.size, (255, 255, 255, 0))
    brilho.putalpha(alfa.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(3)))
    capa.paste(brilho, (x, y), brilho)
    capa.paste(pers, (x, y), pers)
    return x


FEMININO_RE = re.compile(r"\b(mulher|mulheres|garota|moça|menina|senhora|professora|namorada|esposa|"
                         r"irmã|mãe|ela|dela|loira|ruiva|morena)\b", re.I)
MASCULINO_RE = re.compile(r"\b(homem|rapaz|garoto|protagonista|ele|dele|jovem|inhyuk)\b", re.I)


def _nudez_cache(painel):
    """Dict 'nudity' do Sightengine JÁ em cache (censura_visual), sem chamar a API. None se não houver."""
    import hashlib
    import censura_visual
    f = censura_visual.CACHE_DIR / f"{hashlib.md5(Path(painel).read_bytes()).hexdigest()}.json"
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d.get("nudity") or None
    except (OSError, ValueError):
        return None


def _nota_sensual(nud):
    """Quanto o painel é 'sensual de capa' (decote, lingerie, biquíni, roupa curta) SEM nada +18. 0 = não serve.
    Lingerie conta (o dono quer o nível do @oporaodacidadela: lingerie/meia-calça em pose), mas qualquer
    sinal de nudez/ato (sexual_activity, sexual_display, erotica) tira o painel."""
    import censura_visual
    if not nud or censura_visual._score_ponderado(nud) >= 0.25:
        return 0.0
    if any(nud.get(k, 0) >= lim for k, lim in (("sexual_activity", .05), ("sexual_display", .10),
                                                ("erotica", .10), ("sextoy", .05))):
        return 0.0
    c = nud.get("suggestive_classes", {}) or {}
    # HIPER_CAPA_LINGERIE_MAX: baixe pra 0.6 se o YouTube começar a restringir idade/anúncio pelas capas
    if c.get("lingerie", 0) > float(os.environ.get("HIPER_CAPA_LINGERIE_MAX", "0.92")) or c.get("male_underwear", 0) > 0.3:
        return 0.0
    return (c.get("cleavage", 0) + 0.9 * c.get("lingerie", 0) + 0.8 * c.get("bikini", 0)
            + 0.5 * c.get("miniskirt", 0) + 0.4 * c.get("minishort", 0))


PROIBIDO_CAPA_RE = re.compile(r"amarrad|vendad|mordaça|algema|corda|coleira|chicote|criança|menor de idade|"
                              r"infantil|choran|machucad|sangue|estupr|força", re.I)
CASAL_RE = re.compile(r"abraç|beij|\bcolo\b|em cima d|sobre ele|deitad|agarr|encost|aproxim|segurando (ela|ele|a mão)",
                      re.I)
CAPA_SEG_DIR = PROJECT_DIR / "workspace" / "cache" / "capa_seguranca"
_PERGUNTA_CAPA = (
    'Imagem de um manhwa. Responda SÓ JSON: {"exposto": true/false (aparece mamilo, aréola, seio nu, genital ou '
    'nádega nua — mesmo desenhado, pequeno ou de relance), "censura": true/false (tem mosaico, borrão ou tarja '
    'cobrindo algo), "sensual": 0-10 (roupa curta, lingerie, biquíni, decote, pose provocante; 0 = nada sensual), '
    '"casal": true/false (um homem e uma mulher juntos e em contato: abraço, beijo, ela no colo ou em cima dele, '
    'ele segurando ela)}')


def _capa_segura(painel):
    """Checagem do painel pra capa pela VISÃO do Gemini (o Sightengine não enxerga nudez em desenho: o mamilo à
    mostra da capa do cap 5 deu erotica 0,19). Cache por md5. None se a checagem falhar — e aí o painel não entra."""
    import hashlib
    import gemini_llm
    b = Path(painel).read_bytes()
    f = CAPA_SEG_DIR / f"{hashlib.md5(b).hexdigest()}.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    try:
        mime = "image/png" if b[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
        txt = gemini_llm.describe_image(b, _PERGUNTA_CAPA, mime=mime, max_tokens=200, temperature=0.1)
        d = json.loads(re.search(r"\{.*\}", txt or "", re.S).group(0))
        d = {"exposto": bool(d.get("exposto")), "censura": bool(d.get("censura")),
             "sensual": float(d.get("sensual") or 0), "casal": bool(d.get("casal"))}
    except Exception:  # noqa: BLE001
        return None
    CAPA_SEG_DIR.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(d), encoding="utf-8")
    return d


def _seguros_capa(cands, info, k=10):
    """[(painel, checagem)] que podem ir pra capa: nada exposto, sem mosaico (checado por visão). Pré-filtro barato
    (sem censura, sem tema proibido; casal e sensual primeiro) pra só os k melhores gastarem a checagem."""
    import censura_visual
    pre = []
    for p in cands:
        i = (info or {}).get(str(p), {})
        nud = _nudez_cache(p)
        if PROIBIDO_CAPA_RE.search(f"{i.get('desc', '')} {i.get('fala', '')}") or \
                (nud and censura_visual._score_ponderado(nud) >= censura_visual.LIMIAR_DUVIDA):
            continue
        fem = FEMININO_RE.search(i.get("desc", "")) or (i.get("genero") == "F" and not _eh_narrador(i.get("persona")))
        nota = _nota_sensual(nud) + (0.6 if CASAL_RE.search(i.get("desc", "")) else 0) + (0.2 if fem else 0)
        if nota > 0:
            pre.append((nota, str(p)))
    out = []
    for _n, p in sorted(pre, reverse=True)[:k]:
        c = _capa_segura(p)
        if c and not c["exposto"] and not c["censura"]:
            out.append((Path(p), c))
    return out


def _sem_marca(painel, tmp_dir):
    """Cópia do painel sem a marca do scan (bin/marca_scan) — painéis antigos ainda têm; os novos já vêm limpos."""
    import cv2
    import marca_scan
    im = cv2.imread(str(painel))
    limpo, achou = marca_scan.limpar(im)
    if not achou:
        return Path(painel)
    out = Path(tmp_dir) / f"_capa_limpo_{Path(painel).name}"
    cv2.imwrite(str(out), limpo, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return out


def _altura_figura(painel, rosto):
    """Altura da figura (pedaço do recorte que contém o rosto) em alturas de rosto: < 3,5 = busto;
    >= 5 = corpo inteiro / 3/4 (dá pra ver a POSE)."""
    import cv2
    import numpy as np
    import fx_parallax
    m = (fx_parallax.mascara(painel) > 127).astype(np.uint8)
    x, y, w, h = (int(v) for v in rosto)
    _n, lab, st, _c = cv2.connectedComponentsWithStats(m, 8)
    k = lab[min(m.shape[0] - 1, y + h // 2), min(m.shape[1] - 1, x + w // 2)]
    if not k:
        return 0.0
    return float(st[k, cv2.CC_STAT_TOP] + st[k, cv2.CC_STAT_HEIGHT] - y) / max(1, h)


def _recorte_rgba(painel):
    """Personagem recortado (RGBA, cortado na caixa) + caixa (x0, y0, x1, y1) no painel."""
    from PIL import Image, ImageFilter
    import fx_parallax
    rgb = Image.open(painel).convert("RGB")
    a = Image.fromarray(((fx_parallax.mascara(painel) > 110) * 255).astype("uint8")).filter(
        ImageFilter.GaussianBlur(1.2))
    bbox = a.getbbox()
    return Image.merge("RGBA", (*rgb.split(), a)).crop(bbox), bbox


def _recorte_limpo(painel, frac_max=0.62):
    """O recorte do personagem é UMA figura (não o painel em retângulo): maior pedaço >= 75% da máscara,
    encosta em no máx. 1 borda, fração do painel razoável."""
    import cv2
    import numpy as np
    import fx_parallax
    ok, frac = fx_parallax.elegivel(painel)
    if not ok or not 0.08 <= frac <= frac_max:
        return False
    m = (fx_parallax.mascara(painel) > 127).astype(np.uint8)
    n, _lab, st, _c = cv2.connectedComponentsWithStats(m, 8)
    if n < 2:
        return False
    k = int(np.argmax(st[1:, cv2.CC_STAT_AREA])) + 1
    x, y, w, h, area = st[k]
    H_, W_ = m.shape
    bordas = (x <= 2) + (y <= 2) + (x + w >= W_ - 2) + (y + h >= H_ - 2)
    solidez = area / max(1, w * h)  # ~0,9+ = o quadro da arte inteiro (margem branca em volta), não uma pessoa
    return bool(area >= 0.75 * m.sum() and bordas <= 1 and solidez <= 0.85)


def _rosto_inteiro(painel, frac_min=0.10):
    """(x, y, w, h) do maior rosto VISÍVEL INTEIRO e dentro do recorte (não cortado no topo/lados do
    painel). Capa sem rosto = foco no corpo, que o YouTube pune; então sem isso o painel não serve."""
    import cv2
    import numpy as np
    import fx_parallax
    m = (fx_parallax.mascara(painel) > 127).astype(np.uint8)
    H_, W_ = m.shape
    _n, lab, st, _c = cv2.connectedComponentsWithStats(m, 8)
    bons = []
    for x, y, w, h, conf in fx_parallax.rostos(painel):
        cx, cy = int(x + w / 2), int(y + h / 2)
        if not (conf >= 0.5 and w / W_ >= frac_min and y > 0.01 * H_ and x > 0 and x + w < W_
                and 0 <= cy < H_ and 0 <= cx < W_ and m[cy, cx]):
            continue
        topo = st[lab[cy, cx], cv2.CC_STAT_TOP]
        if y - topo >= 0.15 * h:  # tem cabelo/testa acima: o rosto não foi cortado pelo quadro da arte
            bons.append((w * h, (x, y, w, h)))
    return max(bons)[1] if bons else None


def _busto(painel, rosto, larg=3.6, acima=1.0, abaixo=4.2):
    """Busto RGBA em volta do rosto: só a figura que contém o rosto (outras pessoas e balões de fala
    saem), cortado numa janela larg x (acima+1+abaixo) rostos com as bordas do corte esfumadas.
    Devolve (imagem, (fx, fy, fw, fh) do rosto dentro dela)."""
    import cv2
    import numpy as np
    from PIL import Image
    import fx_parallax
    from censura_visual import _mascara_baloes
    bgr = cv2.imread(str(painel))
    H_, W_ = bgr.shape[:2]
    m = (fx_parallax.mascara(painel) > 110).astype(np.uint8)
    x, y, w, h = (int(v) for v in rosto)
    _n, lab, _st, _c = cv2.connectedComponentsWithStats(m, 8)
    a = (lab == lab[y + h // 2, x + w // 2]).astype(np.float32)
    a[_mascara_baloes(bgr) > 0] = 0
    a = cv2.GaussianBlur(a, (0, 0), 1.2)
    x0, x1 = max(0, int(x + w / 2 - larg * w / 2)), min(W_, int(x + w / 2 + larg * w / 2))
    y0, y1 = max(0, int(y - acima * h)), min(H_, int(y + h + abaixo * h))
    a, rgb = a[y0:y1, x0:x1], cv2.cvtColor(bgr[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)
    # esfuma só onde a janela CORTOU a figura (lados/baixo), pra não aparecer linha reta
    hh, ww = a.shape
    pena = max(8, int(0.25 * w))
    rampa = lambda n: np.clip(np.arange(n) / pena, 0, 1)  # noqa: E731
    fade = np.ones_like(a)
    if x0 > 0:
        fade *= rampa(ww)[None, :]
    if x1 < W_:
        fade *= rampa(ww)[::-1][None, :]
    if y1 < H_:
        fade *= rampa(hh)[::-1][:, None]
    a = (a * fade * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, a]), "RGBA"), (x - x0, y - y0, w, h)


def _texto_contorno(d, xy, txt, f, cor, borda=8):
    d.text(xy, txt, font=f, fill=cor, stroke_width=borda, stroke_fill=(0, 0, 0))


def _fala_curta(cands, n_max, prefere=("?!", "!?", "?", "!")):
    """A fala mais 'de capa' entre as candidatas: curta, com ?/! — já em MAIÚSCULAS e sem aspas."""
    ok = []
    for t in cands:
        t = re.sub(r"[\"“”'«»]", "", (t or "").strip()).strip(" .…")
        if 2 <= len(t) <= n_max:
            peso = next((k for k, p in enumerate(prefere) if p in t), len(prefere))
            ok.append((peso, len(t), t.upper()))
    return min(ok)[2] if ok else None


def _capa_sensual(cands, info, texto, cap_num, out_jpg, seguras=None):
    """Capa no estilo dos canais de recap que mais clicam (ex.: @oporaodacidadela): mulher recortada
    GRANDE de um painel sensual-mas-seguro, o protagonista REAGINDO do outro lado, fala dela num balão
    amarelo com seta e a reação dele em letras grandes. None se o capítulo não tiver painel que sirva."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
    import fx_parallax
    W, H = 1280, 720
    inf = lambda p: info.get(str(p), {})  # noqa: E731
    mulheres = []
    for p in cands:
        i = inf(p)
        nota = _nota_sensual(_nudez_cache(p))
        fem = FEMININO_RE.search(i.get("desc", "")) or (i.get("genero") == "F" and not _eh_narrador(i.get("persona")))
        if nota < 0.25 or not fem or PROIBIDO_CAPA_RE.search(f"{i.get('desc', '')} {i.get('fala', '')}") or \
                (seguras is not None and str(p) not in seguras):
            continue
        rosto = _rosto_inteiro(p, 0.07)
        if rosto and _recorte_limpo(p, 0.72):
            alt = _altura_figura(p, rosto)
            pose = 1.8 if alt >= 5.0 else (0.7 if alt < 3.5 else 1.0)  # corpo em pose > busto
            mulheres.append((nota * pose, p, rosto, alt))
    if not mulheres:
        return None
    _n, pm, rost_m, alt_m = max(mulheres)
    em_pose = alt_m >= 5.0
    homens = []
    for p in cands:
        i = inf(p)
        if p == pm or (_nudez_cache(p) and _nota_sensual(_nudez_cache(p)) > 0.2):
            continue
        r = fx_parallax.rosto_principal(p)
        masc = (i.get("genero") == "M" and not _eh_narrador(i.get("persona"))) or (
            MASCULINO_RE.search(i.get("desc", "")) and not FEMININO_RE.search(i.get("desc", "")))
        if r and masc:
            reage = effects_engine_reacao(i.get("desc", ""), i.get("fala", ""))
            homens.append((reage, "?" in i.get("fala", "") or "!" in i.get("fala", ""), r[2], p, r))
    ph_ = max(homens)[3:] if homens else None
    if ph_ and seguras is not None:
        chk = _capa_segura(ph_[0])  # o painel dele também pode ter alguém exposto ao fundo
        if not chk or chk["exposto"] or chk["censura"]:
            ph_ = None

    # fundo: a cena DELA bem desfocada, clara e saturada (as capas que clicam são coloridas, não escuras)
    src = Image.open(pm).convert("RGB")
    sc = max(W / src.width, H / src.height)
    fundo = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
    fundo = fundo.crop(((fundo.width - W) // 2, (fundo.height - H) // 2,
                        (fundo.width - W) // 2 + W, (fundo.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(26))
    capa = ImageEnhance.Color(ImageEnhance.Brightness(fundo).enhance(0.9)).enhance(1.5)

    def colar(img, x, y, sombra=True):
        alfa = img.split()[3]
        if sombra:
            s = Image.new("RGBA", img.size, (0, 0, 0, 0))
            s.putalpha(alfa.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55)))
            capa.paste(s, (x + 14, y + 16), s)
        brilho = Image.new("RGBA", img.size, (255, 255, 255, 0))
        brilho.putalpha(alfa.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.GaussianBlur(2)))
        capa.paste(brilho, (x, y), brilho)
        capa.paste(img, (x, y), img)

    # ela: em POSE (corpo até as coxas, ocupando a altura toda) quando o painel mostra o corpo; senão busto
    # grande (rosto com ~22% da largura). Luz rosada atrás e contorno branco.
    if em_pose:
        mulher, (fx_, fy_, fw_, fh_) = _busto(pm, rost_m, larg=4.6, acima=1.0, abaixo=6.2)
        esc = min(1.08 * H / mulher.height, 3.2)
        mulher = mulher.resize((int(mulher.width * esc), int(mulher.height * esc)), Image.LANCZOS)
        rcx, rcy = 0.70 * W, (1.0 + 0.5) * fh_ * esc + 6
    else:
        mulher, (fx_, fy_, fw_, fh_) = _busto(pm, rost_m)
        esc = min(0.22 * W / fw_, 3.2)
        mulher = mulher.resize((int(mulher.width * esc), int(mulher.height * esc)), Image.LANCZOS)
        rcx, rcy = 0.74 * W, 0.33 * H  # onde o rosto dela fica na capa
    xm, ym = int(rcx - (fx_ + fw_ / 2) * esc), int(rcy - (fy_ + fh_ / 2) * esc)
    yy, xx = np.mgrid[0:H, 0:W]
    luz = np.clip(1 - np.hypot((xx - rcx) / (W * 0.38), (yy - rcy) / (H * 0.8)), 0, 1) ** 1.5
    arr = np.asarray(capa).astype(np.float32)
    rosa = np.array([255, 160, 205], np.float32)
    capa = Image.fromarray((arr * (1 - 0.5 * luz[..., None]) + rosa * 0.5 * luz[..., None]).astype("uint8"))
    lado_m = (rcx - fw_ * esc * 0.55, rcy - fh_ * esc * 0.15)  # ponto ao lado do rosto, pra seta

    # ele: busto à esquerda (rosto ~19% da largura) se o recorte dele presta; senão o rosto num quadro
    # branco inclinado. Vai ANTES dela: o cabelo dela cobre a borda reta do recorte dele.
    if ph_:
        p_h, r_h = ph_
        r_int = _rosto_inteiro(p_h, 0.08)
        if r_int and _recorte_limpo(p_h, 0.62):
            # janela estreita: o corte esfumado cai antes da borda reta do quadro da arte
            homem, (hx, hy, hw, hh) = _busto(p_h, r_int, larg=2.6, abaixo=3.4)
            e2 = min(0.19 * W / hw, 3.2)
            homem = homem.resize((int(homem.width * e2), int(homem.height * e2)), Image.LANCZOS)
            colar(homem, int(0.2 * W - (hx + hw / 2) * e2), int(0.36 * H - (hy + hh / 2) * e2))
        else:
            img_h = Image.open(p_h).convert("RGB")
            x, y, w, h = r_h
            lado = int(max(w, h) * 2.0)
            cx, cy = x + w / 2, y + h * 0.55
            q = img_h.crop((int(cx - lado / 2), int(cy - lado / 2), int(cx + lado / 2), int(cy + lado / 2)))
            q = q.resize((400, 400), Image.LANCZOS)
            moldura = Image.new("RGBA", (424, 424), (255, 255, 255, 255))
            moldura.paste(q, (12, 12))
            moldura = moldura.rotate(5, expand=True, resample=Image.BICUBIC)
            capa.paste(moldura, (34, 70), moldura)
    colar(mulher, xm, ym)

    d = ImageDraw.Draw(capa)
    import idiomas
    fonte = {"ru": "Montserrat-ExtraBold.ttf"}.get(IDIOMA) or \
        idiomas.IDIOMAS.get(IDIOMA, {}).get("fonte_png") or "LuckiestGuy-Regular.ttf"
    amarelo = tuple(int(COR.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    # fala dela à esquerda do rosto, com seta amarela até ele
    fala_m = _fala_curta([inf(pm).get("fala")] + [v.get("fala") for v in info.values()
                          if v.get("genero") == "F" and not _eh_narrador(v.get("persona"))], 24)
    if fala_m:
        f = _fonte(fonte, 58)
        fim_x = lado_m[0] - 70
        while d.textlength(fala_m, font=f) > max(260, fim_x - 0.38 * W) and f.size > 34:
            f = _fonte(fonte, f.size - 4)
        tw = d.textlength(fala_m, font=f)
        tx, ty = int(max(0.36 * W, fim_x - tw)), int(max(20, lado_m[1] - 1.6 * f.size))
        ponta = (tx + tw * 0.75, ty + f.size + 12)
        d.line([ponta, lado_m], fill=(0, 0, 0), width=16)
        d.line([ponta, lado_m], fill=amarelo, width=8)
        _texto_contorno(d, (tx, ty), fala_m, f, amarelo, 7)

    # reação dele (ou o gancho) em letras grandes embaixo à esquerda
    falas_h = ([inf(ph_[0]).get("fala")] if ph_ else []) + [v.get("fala") for v in info.values()
                                                             if v.get("genero") == "M" and not _eh_narrador(v.get("persona"))]
    grande = _fala_curta(falas_h, 16) or " ".join((texto or "").upper().split()[:4])
    if grande:
        tam = 108
        while tam > 52:
            f = _fonte(fonte, tam)
            pal, linhas, cur = grande.split(), [], ""
            for w_ in pal:
                tst = (cur + " " + w_).strip()
                if cur and d.textlength(tst, font=f) > W * 0.5:
                    linhas.append(cur)
                    cur = w_
                else:
                    cur = tst
            linhas.append(cur)
            if len(linhas) <= 2:
                break
            tam -= 8
        y = H - 40 - len(linhas) * int(tam * 1.08)
        for ln in linhas:
            _texto_contorno(d, (40, y), ln, f, amarelo, 9)
            y += int(tam * 1.08)
    if cap_num:
        fs = _fonte(idiomas.IDIOMAS.get(IDIOMA, {}).get("fonte_png") or "Montserrat-ExtraBold.ttf", 40)
        sel = idiomas.texto(IDIOMA, "cap", n=cap_num)
        lw = int(d.textlength(sel, font=fs))
        d.rectangle([24, 22, 24 + lw + 32, 22 + 58], fill=amarelo, outline=(0, 0, 0), width=4)
        d.text((40, 28), sel, font=fs, fill=(16, 16, 16))
    capa.convert("RGB").save(out_jpg, quality=92)
    log(f"  capa: {Path(out_jpg).name} (estilo sensual: ela {Path(pm).name}"
        f"{', ele ' + Path(ph_[0]).name if ph_ else ''})")
    return out_jpg


def effects_engine_reacao(desc, fala):
    from fx_detect import is_reacao_panel
    return is_reacao_panel(desc, fala)


def gerar_capa(paineis, texto, cap_num, out_jpg, info=None):
    """Thumbnail 1280x720. Com `info` ({painel: {desc, fala, persona, genero}}) tenta primeiro a capa
    SENSUAL (mulher recortada + protagonista reagindo + falas em amarelo — _capa_sensual); senão:
    fundo borrado + personagem RECORTADO grande (ou o painel) + texto em linhas branco/amarelo."""
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
    import idiomas
    cands = paineis[2:-2] if len(paineis) > 8 else paineis
    if not cands:
        return None
    # 1º: capa REDESENHADA (casal em pose sensual com roupa, estilo das capas que mais clicam) — bin/capa_ia
    if os.environ.get("HIPER_CAPA_IA", "1") != "0":
        try:
            import capa_ia
            fonte_ia = {"ru": "Montserrat-ExtraBold.ttf"}.get(IDIOMA) or \
                idiomas.IDIOMAS.get(IDIOMA, {}).get("fonte_png") or "LuckiestGuy-Regular.ttf"
            selo = idiomas.texto(IDIOMA, "cap", n=cap_num) if cap_num else ""
            roteiro = "\n".join(f"{v.get('persona') or ''}: {v.get('fala') or ''}" for v in (info or {}).values())
            fala = capa_ia.fala_da_capa([v.get("fala") for v in (info or {}).values()
                                         if v.get("genero") == "F" and not _eh_narrador(v.get("persona"))])
            if capa_ia.capas(capa_ia.obra_do_painel(cands[0]), texto, selo, out_jpg, n=3, fonte=fonte_ia,
                             roteiro=roteiro or None, fala=fala, idioma=IDIOMA or "pt",
                             chave=capa_ia.chave_do_painel(cands[0])):
                return out_jpg
        except Exception as e:  # noqa: BLE001
            log(f"  [!] capa IA falhou ({str(e)[:120]}) -> capa de painel")
    # capa de painel: SÓ painéis aprovados na checagem por visão (nada exposto, sem mosaico)
    seguros = [str(p) for p, _c in _seguros_capa(cands, info)] if info else []
    if info and os.environ.get("HIPER_CAPA_SENSUAL", "1") != "0":
        try:
            if _capa_sensual(cands, info, texto, cap_num, out_jpg, seguras=set(seguros)):
                return out_jpg
        except Exception as e:  # noqa: BLE001
            log(f"  [!] capa sensual falhou ({str(e)[:120]}) -> capa normal")
    sem_mulher = [p for p in cands if not FEMININO_RE.search(((info or {}).get(str(p)) or {}).get("desc", ""))
                  and not _nota_sensual(_nudez_cache(p)) and (_nudez_cache(p) or {}).get("none", 0) > 0.8]
    cands = [Path(p) for p in seguros] or sem_mulher
    if not cands:
        log("  [!] capa: nenhum painel seguro — sem capa (melhor que capa com nudez)")
        return None
    try:
        melhor, rosto, com_personagem = _escolher_painel_capa(cands)
        W, H = 1280, 720
        src = Image.open(melhor).convert("RGB")
        sc = max(W / src.width, H / src.height)
        fundo = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
        fundo = fundo.crop(((fundo.width - W) // 2, (fundo.height - H) // 2, (fundo.width - W) // 2 + W,
                            (fundo.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(22))
        capa = ImageEnhance.Brightness(fundo).enhance(0.42 if not com_personagem else 0.32)
        if com_personagem:
            x0 = max(560, _colar_personagem(capa, melhor, W, H))
            d = ImageDraw.Draw(capa)
        else:
            if src.height / src.width > 1.4:  # painel alto: recorta uma faixa (no ROSTO, se achou um)
                ch = int(src.width * 1.4)
                meio = rosto[1] + rosto[3] // 2 if rosto else int(src.height * 0.42)
                top = max(0, min(src.height - ch, meio - ch // 2))
                src = src.crop((0, top, src.width, top + ch))
            ph = H - 40
            pw = int(src.width * ph / src.height)
            painel = src.resize((pw, ph), Image.LANCZOS)
            if pw > 640:
                painel = painel.crop(((pw - 640) // 2, 0, (pw - 640) // 2 + 640, ph))
                pw = 640
            x0 = W - pw - 30
            d = ImageDraw.Draw(capa)
            d.rectangle([x0 - 6, 14, x0 + pw + 5, 14 + ph + 11], fill=(255, 255, 255))
            capa.paste(painel, (x0, 20))
        area = x0 - 70
        palavras = (texto or "").upper().split()
        if IDIOMA == "th":  # tailandês não separa palavras: quebra trechos longos sem soltar acento da letra
            palavras = [p for w in palavras for p in _pedacos_sem_quebrar_acento(w, 9)]
        import idiomas
        fonte_capa = {"ru": "Montserrat-ExtraBold.ttf"}.get(IDIOMA) or \
            idiomas.IDIOMAS.get(IDIOMA, {}).get("fonte_png") or "LuckiestGuy-Regular.ttf"
        tam = 104
        while tam > 48:
            f = _fonte(fonte_capa, tam)
            linhas, cur = [], ""
            for w in palavras:
                tst = (cur + " " + w).strip()
                if cur and d.textlength(tst, font=f) > area:
                    linhas.append(cur)
                    cur = w
                else:
                    cur = tst
            if cur:
                linhas.append(cur)
            if len(linhas) <= 4 and len(linhas) * tam * 1.12 <= H - 200:
                break
            tam -= 6
        amarelo = tuple(int(COR.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        y = (H - 120 - len(linhas) * int(tam * 1.12)) // 2 + 20
        for i, ln in enumerate(linhas):
            d.text((40, y), ln, font=f, fill=(255, 255, 255) if i % 2 == 0 else amarelo,
                   stroke_width=7, stroke_fill=(0, 0, 0))
            y += int(tam * 1.12)
        if cap_num:
            fs = _fonte(idiomas.IDIOMAS.get(IDIOMA, {}).get("fonte_png") or "Montserrat-ExtraBold.ttf", 46)
            sel = idiomas.texto(IDIOMA, "cap", n=cap_num)
            lw = int(d.textlength(sel, font=fs))
            d.rectangle([40, H - 110, 40 + lw + 40, H - 40], fill=amarelo)
            d.text((60, H - 104), sel, font=fs, fill=(16, 16, 16))
        capa.save(out_jpg, quality=92)
        log(f"  capa: {Path(out_jpg).name} (painel {Path(melhor).name})")
        return out_jpg
    except Exception as e:  # noqa: BLE001
        log(f"  [!] capa falhou: {e}")
        return None


# ─── orquestração ────────────────────────────────────────────────────────────
def _obra_e_cap(titulo, panels_dir):
    obra = re.split(r"\s+[—–-]\s+", titulo or "")[0].strip() or Path(panels_dir).name
    m = re.search(r"cap[ií]tulo\s*(\d+)", titulo or "", re.I) or re.search(r"cap(\d+)", Path(panels_dir).name, re.I)
    return obra, (int(m.group(1)) if m else None)


def _impactos_no_tempo(ed, palavras, seg_por_loc):
    out, ultimo = [], -99.0
    for imp in ed.get("impactos", []):
        seg = seg_por_loc.get(imp["fala"])
        if seg is None:
            continue
        cand = [w for w in palavras if w["seg"] == seg and _norm(w["w"]) == imp["palavra"]]
        if not cand or cand[0]["s"] - ultimo < 8.0:
            continue
        out.append({"t": cand[0]["s"], "texto": cand[0]["w"], "emoji": imp.get("emoji")})
        ultimo = cand[0]["s"]
    return out


def finalizar(video_concat, out_mp4, clips, infos, recap, titulo, panels_dir, cache_file,
              paineis, tmp_dir, legendas=True, video_concat_cens=None, out_cens=None, idioma=None,
              capa_info=None, so_censurado=False, clips_censurados=()):
    """Pós-concat completo. infos: 1 dict por clip (tipo, texto, persona, voz_wav, atraso, foley, sfx, loc).
    video_concat_cens/out_cens: mesmos clips com os +18 trocados pela imagem censurada; recebe o
    MESMO áudio masterizado, ASS, emojis e punch-ins do principal (timeline idêntica).
    idioma: versão em outra língua (Groq, textos fixos e fontes — ver idiomas.py); None = pt."""
    global IDIOMA
    IDIOMA = idioma
    import fx_music
    tmp_dir = Path(tmp_dir)
    durs = [duracao(c) for c in clips]
    offs, t = [], 0.0
    for d in durs:
        offs.append(t)
        t += d
    total = duracao(video_concat) or t
    respiro = RESPIRO_FINAL if total > 8 else 0.0
    fim = total + respiro  # o vídeo entregue: a voz acaba em `total`, a imagem e a trilha em `fim`
    obra, cap_num = _obra_e_cap(titulo, panels_dir)

    segmentos, seg_por_loc, ocupados, sem_gat = [], {}, [], []
    for k, (inf, ini, d) in enumerate(zip(infos, offs, durs)):
        if inf.get("sfx"):
            ocupados.append(ini)
        if inf.get("foley"):
            sem_gat.append((ini, ini + inf.get("atraso", 0.0) + 1.2))
        # pt: só o narrador tem legenda (a fala do personagem já está no balão). Outra língua: o balão
        # continua em português, então a fala do personagem também ganha legenda no idioma do vídeo.
        if inf.get("tipo") == "fala" and (idioma or _eh_narrador(inf.get("persona"))) and (inf.get("texto") or "").strip():
            seg_por_loc[inf["loc"]] = k
            segmentos.append({"seg": k, "texto": inf["texto"].strip(), "ini": ini, "fim": ini + d,
                              "voz_wav": inf.get("voz_wav"), "atraso": inf.get("atraso", 0.0)})

    ed = editorial(recap, titulo, cache_file)
    palavras = tempos_palavras(video_concat, segmentos, tmp_dir)
    impactos_t = _impactos_no_tempo(ed, palavras, seg_por_loc)
    if impactos_t:
        log("  impactos: " + ", ".join(f"{i['texto']}@{i['t']:.1f}s" for i in impactos_t))
    cta_ini = max(0.0, fim - CTA_SEGUNDOS) if total > 8 else None
    movs, fixos = planejar_retencao(total, impactos_t, cta_ini)
    sons, emojis = planejar_sons(palavras, impactos_t, total, ocupados, sem_gat, fixos, seed=Path(panels_dir).name)
    emojis += [{"t": i["t"], "emoji": i["emoji"], "grande": True} for i in impactos_t if i.get("emoji")]

    musica = fx_music.compose_dynamic_music(fim, recap.get("locucoes", []), TRILHAS_DIR, tmp_dir)
    masterizado = tmp_dir / "_master.mp4"
    lufs_antes = masterizar_audio(video_concat, masterizado, musica, sons, tmp_dir, respiro=respiro)

    ass = tmp_dir / "legendas.ass"
    montar_ass(ass, palavras, fim, ed, impactos_t, obra, cap_num, legendas=legendas)
    janelas = [[max(0.0, i["t"] - 0.05), i["t"] + 0.9] for i in impactos_t]
    # memes visuais (figurinha + reação)
    memes_lista = []
    try:
        import fx_memes
        memes_cfg = None
        try:
            import json as _json
            _fila_cfg = _json.loads((PROJECT_DIR / "config" / "fila.json").read_text(encoding="utf-8"))
            memes_cfg = _fila_cfg.get("memes")
        except Exception:
            pass
        if not memes_cfg or memes_cfg.get("ligado", True):
            # nenhuma figurinha logo antes/depois de um meme que interrompe o vídeo (clip tipo "meme")
            evitar = [(ini - 6.0, ini + d + 2.0) for inf, ini, d in zip(infos, offs, durs) if inf.get("tipo") == "meme"]
            # 16/10: a 1ª figurinha do cap 10 era o emoji chorando de rir ESTAMPADO sobre a cena de
            # sexo da abertura, contra o clima que o próprio editorial escolheu ("ELE ABRIU A PORTA
            # E..."). Os 10 primeiros segundos decidem a retenção e painel +18 não é piada: ficam fora.
            evitar.append((0.0, 10.0))
            evitar += [(offs[k] - 0.5, offs[k] + durs[k] + 0.5) for k in (clips_censurados or ())
                       if k < len(offs) and k < len(durs)]
            memes_lista = fx_memes.escolher_memes(palavras, total, config=memes_cfg, evitar=evitar)
            for mm in memes_lista:  # figurinha não tampa balão de fala
                pos = _posicao_figurinha(masterizado, mm["t"], tmp_dir)
                if pos:
                    mm["x"], mm["y"] = pos
    except ImportError:
        pass
    # so_censurado (outra língua): o dono só quer a censurada; o passe final do normal (~6 min) não roda
    so_cens = bool(so_censurado and video_concat_cens and out_cens)
    if not so_cens:
        passe_final(masterizado, ass, emojis, janelas, out_mp4, tmp_dir, movs=movs, memes=memes_lista,
                    respiro=respiro)
    cens = None
    if video_concat_cens and out_cens:
        master_cens = tmp_dir / "_master_cens.mp4"
        try:  # falha na censurada não pode derrubar o acabamento do principal
            # sem -shortest: o áudio masterizado tem o respiro a mais, e o passe final estica a imagem
            ffmpeg(["-i", video_concat_cens, "-i", masterizado, "-map", "0:v", "-map", "1:a",
                    "-c", "copy", *([] if respiro > 0 else ["-shortest"]), master_cens], timeout=900)
            ass_cens = _ass_chamada_sem_censura(ass, tmp_dir, offs, durs, clips_censurados, total, idioma)
            passe_final(master_cens, ass_cens, emojis, janelas, out_cens, tmp_dir, movs=movs, memes=memes_lista,
                        respiro=respiro)
            cens = {"arquivo": str(out_cens), "validacao": validar(out_cens, fim)}
        except Exception as e:  # noqa: BLE001
            log(f"  [X] versão censurada falhou no passe final: {str(e)[:300]}")
            Path(out_cens).unlink(missing_ok=True)
        master_cens.unlink(missing_ok=True)
    masterizado.unlink(missing_ok=True)

    rel = None if so_cens else validar(out_mp4, fim)
    capa = None if so_cens else gerar_capa(paineis, ed.get("gancho") or recap.get("titulo_video") or titulo,
                                           cap_num, Path(out_mp4).with_suffix(".capa.jpg"), info=capa_info)
    return {"validacao": rel, "capa": str(capa) if capa else None, "editorial": ed,
            "palavras": len(palavras), "impactos": len(impactos_t), "sfx": len(sons), "overlays": len(movs),
            "lufs_antes_master": lufs_antes, "trilha": (fx_music.ULTIMAS_FAIXAS or [Path(musica).name]) if musica else None,
            "censurado": cens,
            "fronteiras": [round(o, 3) for o in offs], "duracoes": [round(d, 3) for d in durs]}
