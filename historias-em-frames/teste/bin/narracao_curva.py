# COMUM — fonte única: D:\hipercool-materiais\comum\narracao_curva.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir narracao_curva.py --de <projeto>
"""narracao_curva.py — narração com cara de locutor (curva de clímax), copiada e adaptada do hipercool.

Origem: D:\\hipercool-videos\\bin\\elenco.py (curva_climax / prosodia / _pos_processar, 16/10) e
docs/VOZ_E_NARRACAO_PENDENTE.md. O dono, ouvindo o hipercool: "a voz de IA é muito estável: mesma velocidade,
todas no mesmo volume" e "eles vão acelerando conforme vai chegando ao clímax, como narração de futebol".
Pedido de 17/10: "implementa na sua criação também". Para o narrador do recap de anime e do parceiro:
  - curva: as frases de IMPACTO (os "gols", escolhidas 1x por vídeo) — chegando nelas a voz acelera e sobe o
    volume (curva quadrática: devagar no começo, dispara no fim); nas seguintes cai, que é o respiro (sem a queda o
    vídeo inteiro vira grito e cansa igual ao volume constante). O tom quase não sobe: no hipercool +6 Hz no clímax
    saiu "fina e aguda" (dono) — quem carrega a emoção é a velocidade e o volume. Doses = 3ª dose do hipercool;
  - pontuação da frase: grito ("!!" ou CAIXA ALTA com "!") mais rápido e +3 dB; reticência mais devagar;
  - variação pequena e fixa por frase (±3% de velocidade, ±1 dB) pra nenhuma sair igual à vizinha;
  - cada frase nivelada a -20 LUFS + o ganho da curva (o master final continua -14) e sem a cauda de silêncio do
    edge (~1 s depois da fala): fica 0,25 s de respiro — 0,6 s depois de um impacto, a pausa do "gol".
ANIME_PROSODIA=0 desliga (volta a voz plana de antes). ANIME_IMPACTOS="3,9" fixa os impactos (anime_idiomas passa
os da versão pt: mesma ordem de frases).
"""
import hashlib
import json
import logging
import math
import os
import random
import re
import shutil
import subprocess
from pathlib import Path

BASE_RATE = 5          # % do perfil de narrador do edge_tts_engine (_NARRATOR_PROFILE: +5%)
PICO_RATE = 18         # % a mais na frase do impacto
PICO_PITCH = 1         # Hz a mais no impacto (quase nada, de propósito)
PICO_GANHO_DB = 4.0    # dB a mais no impacto
RESPIRO_RATE = -12
RESPIRO_PITCH = -4
RESPIRO_GANHO_DB = -3.0
GRITO_RATE, GRITO_PITCH, GRITO_GANHO_DB = 10, 6, 3.0
ARRASTO_RATE = -8
ALVO_LUFS = -20.0
CAUDA_S, CAUDA_IMPACTO_S = 0.25, 0.6
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def ligado():
    return os.environ.get("NARRACAO_CURVA", os.environ.get("ANIME_PROSODIA", "1")) != "0"


def _doses(n):
    """(falas de subida, falas de respiro): no Short (até 20 frases) a curva é mais curta que no capítulo."""
    return (4, 2) if (n or 0) <= 20 else (7, 3)


def curva_climax(indice, impactos, n):
    """(delta de velocidade %, delta de tom Hz, delta de ganho dB) pela posição da frase na curva."""
    if not impactos or indice is None:
        return 0, 0, 0.0
    subida, respiro = _doses(n)
    faltam = [k - indice for k in impactos if 0 <= k - indice <= subida]
    # adaptado do hipercool (17/10), pro Short em que os impactos ficam perto: impacto é sempre pico (lá o
    # respiro vinha antes e o 2º de 2 impactos colados saía MAIS LENTO), e a frase logo antes de um impacto
    # embala mesmo dentro do respiro do anterior (senão ia de -12% direto pra +18%)
    if (indice not in impactos and any(0 < indice - k <= respiro for k in impactos)
            and not (faltam and min(faltam) <= 1)):
        return RESPIRO_RATE, RESPIRO_PITCH, RESPIRO_GANHO_DB
    if not faltam:
        return 0, 0, 0.0
    f = (subida - min(faltam)) / subida  # 0 longe -> 1 no impacto
    f = f * f                            # cresce devagar e dispara no fim, como locutor de futebol
    return int(round(PICO_RATE * f)), int(round(PICO_PITCH * f)), round(PICO_GANHO_DB * f, 2)


def deltas(texto, indice, impactos, n):
    """(delta de velocidade %, delta de tom Hz, ganho dB, cauda s) desta frase: curva + pontuação + variação."""
    dr, dp, dg = curva_climax(indice, impactos, n)
    letras = [c for c in texto if c.isalpha()]
    caixa_alta = len(letras) >= 3 and sum(c.isupper() for c in letras) / len(letras) >= 0.8
    if "!!" in texto or (caixa_alta and "!" in texto):
        dr, dp, dg = dr + GRITO_RATE, dp + GRITO_PITCH, dg + GRITO_GANHO_DB
    elif "..." in texto or "…" in texto:
        dr += ARRASTO_RATE
    h = int(hashlib.md5(texto.encode("utf-8")).hexdigest(), 16)  # fixo por frase: refazer dá o mesmo áudio
    dr += h % 7 - 3
    dg += ((h >> 8) % 21 - 10) / 10
    cauda = CAUDA_IMPACTO_S if indice in (impactos or []) else CAUDA_S
    return dr, dp, round(dg, 2), cauda


def absoluto(dr, dp, base_rate=BASE_RATE, base_pitch=0):
    """rate "+N%" e pitch "+NHz" do edge a partir do perfil da voz + os deltas (com os limites do hipercool)."""
    def _num(v):
        try:
            return int(str(v).rstrip("%Hz") or 0)
        except ValueError:
            return 0
    rate = max(-20, min(25, _num(base_rate) + dr))
    pitch = max(-25, min(25, _num(base_pitch) + dp))
    return f"{rate:+d}%", f"{pitch:+d}Hz"


def prosodia(texto, indice, impactos, n, base_rate=BASE_RATE, base_pitch=0):
    """(rate "+N%", pitch "+NHz", ganho dB, cauda s) desta frase pro edge."""
    dr, dp, dg, cauda = deltas(texto, indice, impactos, n)
    rate, pitch = absoluto(dr, dp, base_rate, base_pitch)
    return rate, pitch, dg, cauda


# ─── escolha dos impactos (1x por vídeo) ────────────────────────────────────────────────────
_GATILHO = re.compile(r"\b(mas|só que|porém|de repente|finalmente|revel|descobr|verdade|nunca|ninguém|tudo mud|"
                      r"inacredit|choc|surpre|beij|morr|mat[aoe]u|poder|segredo|grit|explod|atac|confess|"
                      r"desaparec|traí|traiç|virou|acord)\w*", re.I)


def _quantos(n):
    return 1 if n <= 6 else 2 if n <= 20 else max(2, min(8, round(n / 12)))


def _heuristica(linhas, k):
    """Reserva do LLM: exclamação, palavra de virada e o trecho do clímax (55-92% do vídeo) pesam; a 1ª frase não
    (o gancho já está na tela)."""
    n = len(linhas)
    notas = []
    for i, t in enumerate(linhas):
        s = 2.0 * ("!" in t) + 0.5 * ("?" in t) + 1.2 * len(_GATILHO.findall(t))
        pos = i / max(1, n - 1)
        s += 1.5 if 0.55 <= pos <= 0.92 else 0.0
        s += 1.0 if i == n - 1 else 0.0
        s -= 1.0 if i == 0 else 0.0
        notas.append((s, i))
    escolhidos = []
    for _s, i in sorted(notas, key=lambda x: (-x[0], -x[1])):
        if all(abs(i - j) >= 3 for j in escolhidos):
            escolhidos.append(i)
        if len(escolhidos) >= k:
            break
    return sorted(escolhidos)


def _pelo_llm(linhas, k):
    numeradas = "\n".join(f"{i}: {t}" for i, t in enumerate(linhas))
    prompt = (f"Abaixo estão as {len(linhas)} frases da narração de um vídeo de resumo (manhwa/anime), numeradas "
              f"a partir de 0. Escolha as {k} frases de IMPACTO: os momentos mais fortes (virada, revelação, susto, "
              "confissão, o clímax, ou a frase final que deixa curiosidade) — como os gols numa narração de "
              "futebol: a voz do narrador acelera chegando nelas. Espalhe pelo vídeo e não escolha a frase 0. "
              f"Responda SÓ um JSON: lista com {k} números, em ordem crescente.\n\n{numeradas}")
    import inspect
    import claude_client
    # o claude_client do historias não tem timeout (o do recapd tem): passa só onde existe
    kw = {"timeout": 60} if "timeout" in inspect.signature(claude_client.generate_text).parameters else {}
    txt = claude_client.generate_text(prompt, max_tokens=60, temperature=0.2, **kw) or ""
    m = re.search(r"\[[\d,\s]*\]", txt)
    lst = sorted({int(x) for x in json.loads(m.group(0))}) if m else []
    if lst and all(0 <= x < len(linhas) for x in lst) and len(lst) <= k + 1:
        return lst
    return None


def escolher_impactos(linhas, cache=None):
    """Índices (base 0) das frases de impacto. ANIME_IMPACTOS manda; senão o cache do vídeo; senão o LLM (1 chamada);
    senão a heurística."""
    n = len(linhas)
    fixo = os.environ.get("ANIME_IMPACTOS", "").strip()
    if fixo:
        lst = sorted({int(x) for x in re.findall(r"\d+", fixo) if int(x) < n})
        if lst:
            return lst
    chave = hashlib.md5("\n".join(linhas).encode("utf-8")).hexdigest()
    if cache and Path(cache).is_file():
        try:
            d = json.loads(Path(cache).read_text(encoding="utf-8"))
            if d.get("chave") == chave:
                return d["impactos"]
        except (OSError, ValueError, KeyError):
            pass
    k = _quantos(n)
    origem, lst = "llm", None
    try:
        lst = _pelo_llm(linhas, k)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[curva] LLM dos impactos falhou ({type(e).__name__}) — heurística")
    if not lst:
        origem, lst = "heuristica", _heuristica(linhas, k)
    logging.info(f"[curva] impactos ({origem}): {lst} de {n} frases")
    if cache:
        try:
            Path(cache).write_text(json.dumps({"chave": chave, "impactos": lst, "origem": origem}), encoding="utf-8")
        except OSError:
            pass
    return lst


# ─── pós-processamento do wav da frase ──────────────────────────────────────────────────────
def pos_processar(wav, ganho_db=0.0, cauda_s=CAUDA_S):
    """No lugar: corta a cauda de silêncio (deixa `cauda_s`) e nivela a -20 LUFS + `ganho_db`. Ganho fixo medido
    (não loudnorm dinâmico) pra não bombear em frase curta; 1 dB de folga do 0 dBFS. Falhou = wav fica como veio."""
    wav = Path(wav)
    trim = f"areverse,silenceremove=start_periods=1:start_silence={cauda_s}:start_threshold=-45dB,areverse"
    tmp = wav.with_name(wav.stem + ".curva.wav")
    try:
        r = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(wav), "-af",
                            trim + ",ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
                           capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace",
                           creationflags=SEM_JANELA)
        err = r.stderr or ""
        m = re.search(r"I:\s*(-?[\d.]+) LUFS", err)
        ganho = ganho_db + (ALVO_LUFS - float(m.group(1)) if m and float(m.group(1)) > -60 else 0.0)
        ganho = max(-12.0, min(12.0, ganho))
        pico = re.search(r"Peak:\s*(-?[\d.]+) dBFS", err)
        if pico:
            ganho = min(ganho, -1.0 - float(pico.group(1)))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", f"{trim},volume={ganho:+.1f}dB",
                        "-ar", "44100", "-ac", "2", str(tmp)], check=True, timeout=60, creationflags=SEM_JANELA)
        shutil.move(str(tmp), str(wav))
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[curva] nivelamento falhou ({str(e)[:80]}) — wav como veio")
        tmp.unlink(missing_ok=True)


# ─── microcortes (22/10): OBRIGATÓRIOS em toda fala gerada ─────────────────────────────────────
# Dono 22/10: "o que é muito usado nos Shorts é cortar as pausas entre as falas — são microcortes, em vez de acelerar
# a fala". Todo silêncio maior que GAP_MICROCORTE (a cauda que o pos_processar deixa, a pausa que o humanizar põe antes
# do impacto, vírgula, reticências, o começo mudo do TTS) fica com GAP_MICROCORTE: metade no fim de um trecho falado,
# metade no começo do outro, com o som original das pontas e crossfade curto. A FALA NÃO ACELERA. Respiração e efeito
# não são silêncio (ficam). Como o clip dura o que o áudio dura, o vídeo encurta junto; o <wav>.words.json acompanha.
GAP_MICROCORTE = 0.07       # s de silêncio que sobra em cada pausa (env NARRACAO_GAP_MICROCORTE, 0,03–0,3)
LIMIAR_SILENCIO_DB = -45.0  # o mesmo do corte de cauda: a fala chega nivelada a -20 LUFS


def microcortes(wav, gap_s=None):
    """No lugar. Devolve (duração antes, depois) ou None (nada a cortar ou falhou: wav e words.json como vieram)."""
    wav = Path(wav)
    try:
        gap = float(gap_s if gap_s is not None else os.environ.get("NARRACAO_GAP_MICROCORTE") or GAP_MICROCORTE)
    except ValueError:
        gap = GAP_MICROCORTE
    gap = max(0.03, min(0.3, gap))
    tmp = wav.with_name(wav.stem + ".cortes.wav")
    try:
        import wave
        import numpy as np
        with wave.open(str(wav)) as f:
            sr, ch, sw, n = f.getframerate(), f.getnchannels(), f.getsampwidth(), f.getnframes()
            bruto = f.readframes(n)
        if sw != 2 or n < sr // 10:
            return None
        y = np.frombuffer(bruto, dtype="<i2").reshape(-1, ch).astype(np.float32)
        quadro = max(1, sr // 100)  # 10 ms
        nq = len(y) // quadro
        mono = y[:nq * quadro].mean(axis=1) / 32768
        db = 10 * np.log10((mono.reshape(nq, quadro) ** 2).mean(axis=1) + 1e-12)
        som = db > LIMIAR_SILENCIO_DB
        bordas = np.flatnonzero(np.diff(np.concatenate([[0], som.astype(np.int8), [0]])))
        trechos = [(a * quadro, min(len(y), b * quadro)) for a, b in zip(bordas[::2], bordas[1::2]) if b - a >= 2]
        if not trechos:
            return None
        meio, xf = int(gap * sr / 2), max(1, int(0.006 * sr))
        pecas, ini = [], max(0, trechos[0][0] - meio)
        for (_a1, b1), (a2, _b2) in zip(trechos, trechos[1:]):
            if a2 - b1 > 2 * meio + 2 * xf:
                pecas.append((ini, b1 + meio + xf))
                ini = a2 - meio - xf
        pecas.append((ini, min(len(y), trechos[-1][1] + meio)))
        out, mapa = y[pecas[0][0]:pecas[0][1]], [(pecas[0][0], pecas[0][1], 0)]
        for a, b in pecas[1:]:
            p = y[a:b]
            f = min(xf, len(out), len(p))
            rampa = np.linspace(0, 1, f, dtype=np.float32)[:, None]
            mapa.append((a, b, len(out) - f))
            out = np.concatenate([out[:len(out) - f], out[len(out) - f:] * (1 - rampa) + p[:f] * rampa, p[f:]])
        f = min(xf, len(out) // 2)
        if f:
            out[:f] *= np.linspace(0, 1, f, dtype=np.float32)[:, None]
            out[len(out) - f:] *= np.linspace(1, 0, f, dtype=np.float32)[:, None]
        dur0, dur1 = len(y) / sr, len(out) / sr
        if dur0 - dur1 < 0.02 or dur1 < 0.3 * dur0:
            return None
        with wave.open(str(tmp), "wb") as f:
            f.setnchannels(ch)
            f.setsampwidth(2)
            f.setframerate(sr)
            f.writeframes(np.clip(np.round(out), -32768, 32767).astype("<i2").tobytes())
        shutil.move(str(tmp), str(wav))
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[microcortes] {wav.name} falhou ({str(e)[:80]}) — wav como veio")
        tmp.unlink(missing_ok=True)
        return None

    def novo(t):
        s = t * sr
        for a, b, n0 in mapa:
            if s < a:
                return n0 / sr  # caiu num silêncio cortado: vai pro começo do trecho seguinte
            if s <= b:
                return (n0 + s - a) / sr
        return dur1

    wj = Path(str(wav) + ".words.json")
    if wj.exists():
        try:
            palavras = json.loads(wj.read_text(encoding="utf-8"))
            wj.write_text(json.dumps([[round(min(dur1, novo(float(a))), 3), round(min(dur1, novo(float(b))), 3), w]
                                      for a, b, w in palavras], ensure_ascii=False), encoding="utf-8")
        except (OSError, ValueError, TypeError) as e:
            logging.warning(f"[microcortes] {wj.name} não acompanhou ({str(e)[:60]})")
    logging.info(f"[microcortes] {wav.name}: {dur0:.2f}s -> {dur1:.2f}s ({len(pecas) - 1} cortes)")
    return dur0, dur1


# ─── humanizar (20/10): pausa, respiração, ênfase, ritmo, fundo da sala, de-esser — e VARIAÇÃO ─────
# Dono 20/10: "não pode ser igual do começo ao fim... mudar conforme a situação, ou com x tempo, ligando umas coisas
# desligando outras, valores diferentes". variacao() decide frase a frase pela situação (abertura, subida pro impacto,
# impacto, respiro depois dele, pergunta, grito, frase final), pelo TRECHO do vídeo (3–7 frases; cada trecho liga e
# desliga recursos e sorteia valores) e por uma onda lenta de energia. Sorteio fixo por vídeo: refazer dá o mesmo.
# Com VOZ_CLONADA: respirações reais e fundo da sala do narrador (hipercool-materiais bin\clone2.py humano).
VOZES_RVC = Path(r"D:\hipercool-materiais\models\rvc\vozes")
_FMT = "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo"
_HIST = {}    # por vídeo (pasta dos áudios): o que cada frase recebeu, pra vizinha não repetir
_BANCOS = {}
_ENFASE_PALAVRAS = re.compile(
    r"\b(sistema|poder|forc[aç]|segredo|verdade|morr\w*|mat[aoe]\w*|revel\w*|trai[çc]\w*|"
    r"beij\w*|amaldi[çc]\w*|rei|imperador|deus|drag[aã]o|monstro|boss|level|rank|despert\w*|"
    r"evolu[çc]\w*|transform\w*|destrui\w*|invenc[ií]vel|lend[aá]ri\w*|absurd\w*|"
    r"inacredit[aá]vel|imposs[ií]vel|choqu\w*|explo[sd]\w*|impacto)\b", re.I)


def _sorteio(*partes):
    return random.Random(int(hashlib.md5("|".join(map(str, partes)).encode("utf-8")).hexdigest(), 16))


def _trecho(chave, indice):
    """O jeito do trecho (3–7 frases) em que a frase cai: o que fica ligado e com que força."""
    r = _sorteio(chave, "trechos")
    ini = 0
    while True:
        n = r.randint(3, 7)
        t = {"id": ini,
             "respira": r.random() > 0.15, "respira_p": r.uniform(0.3, 0.75), "respira_db": r.uniform(-4, 2),
             "pausa": r.random() > 0.25, "pausa_mult": r.uniform(0.7, 1.4),
             "enfase": r.random() > 0.2, "enfase_db": r.uniform(1.5, 4.0),
             "ritmo": r.random() > 0.2, "ritmo_amp": r.uniform(0.5, 1.5),
             "final_mult": r.uniform(0.6, 1.3), "sala_db": r.uniform(-3, 3), "deesser": r.uniform(0.15, 0.4)}  # >0,5 abafa (-6 dB nos agudos)
        if indice < ini + n:
            return t
        ini += n


def variacao(chave, indice, texto, impactos, total):
    """Como ESTA frase sai (0 = desligado). chave = pasta dos áudios do vídeo. Quem usa: humanizar e o anime_tts
    (final_mult, o fim de frase que vai pro clone)."""
    t = _trecho(chave, indice)
    r = _sorteio(chave, indice, texto)
    impactos, total = impactos or [], max(1, total or 1)
    subida, respiro = _doses(total)
    impacto = indice in impactos
    na_subida = not impacto and any(0 < k - indice <= subida for k in impactos)
    pos_impacto = not impacto and any(0 < indice - k <= respiro for k in impactos)
    pergunta, grito, final, n = texto.rstrip().endswith("?"), "!" in texto, indice == total - 1, len(texto)
    o = _sorteio(chave, "onda")
    energia = math.sin(o.uniform(0, 2 * math.pi) + 2 * math.pi * o.uniform(0.7, 1.8) * indice / total)
    p = t["respira_p"] if t["respira"] else 0.0
    p *= 1.3 if n >= 60 else 0.3 if n < 25 else 1.0
    p *= 1.2 if na_subida else 1.0
    if pos_impacto:
        p = max(p, 0.7)   # depois do "gol" o narrador puxa o ar
    if final:
        p = max(p, 0.5)
    p *= 1 - 0.25 * energia  # elétrico respira menos
    voz = os.environ.get("VOZ_CLONADA")
    banco = _banco(voz)
    n_resp = banco.get("n_resp", -1)
    if n_resp >= 0:
        p *= min(1.0, n_resp / 16)
    pausa = 0.0
    if impacto:
        pausa = r.uniform(0.38, 0.6) * t["pausa_mult"]
    elif t["pausa"] and _GATILHO.search(texto):
        pausa = r.uniform(0.12, 0.22) if na_subida else r.uniform(0.22, 0.4) * t["pausa_mult"]
    elif final and r.random() < 0.6:
        pausa = r.uniform(0.25, 0.45)
    pausa *= 1 - 0.3 * max(0.0, energia)
    enfase = t["enfase_db"] if (t["enfase"] or impacto or indice == 0) else 0.0
    if enfase:
        enfase += (1.0 if impacto or grito else 0.0) + 0.5 * energia + r.uniform(-0.5, 0.5)
    amp = t["ritmo_amp"] if t["ritmo"] else 0.0
    if impacto:
        amp = max(amp, 1.0) * 1.2
    amp *= (1.15 if na_subida else 1.0) * r.uniform(0.85, 1.15) if n >= 25 else 0.0
    fm = t["final_mult"]
    fm = 0.0 if pergunta else fm * 0.4 if na_subida else fm * 1.3 if (impacto or final) else fm
    idx_rate = 0.65 + 0.15 * energia if (impacto or grito) else 0.5 + 0.05 * energia if na_subida else 0.38 + r.uniform(-0.03, 0.03)
    prot = 0.22 if (impacto or grito) else 0.28 if na_subida else 0.38 + r.uniform(-0.03, 0.03)
    vol_env = 0.7 + 0.1 * (1 - abs(energia)) + r.uniform(-0.05, 0.05)
    ct_mid = int(round(r.uniform(-3, 3) + 5 * energia))
    ct_end = int(round(r.uniform(-5, -1) if (impacto or grito) else r.uniform(-2, 2)))
    contour = f"(0%,+0Hz)(25%,{ct_mid:+d}Hz)(75%,{ct_mid:+d}Hz)(100%,{ct_end:+d}Hz)"
    return {"trecho": t["id"], "energia": round(energia, 2), "respira_p": round(min(0.9, p), 2),
            "respira_db": round(t["respira_db"] + (1.5 if pos_impacto else 0.0) + r.uniform(-1.5, 1.5), 1),
            "pausa_s": round(min(0.8, pausa), 3), "enfase_db": round(max(0.0, enfase), 1),
            "ritmo_amp": round(amp, 2), "final_mult": round(fm, 2),
            "sala_db": round(t["sala_db"] + 0.8 * energia, 1), "deesser": round(t["deesser"], 2),
            "index_rate": round(max(0.3, min(0.85, idx_rate)), 2),
            "protect": round(max(0.15, min(0.45, prot)), 2),
            "volume_envelope": round(max(0.6, min(0.9, vol_env)), 2),
            "contour": contour}


def _banco(voz):
    """Respirações reais e fundo da sala do narrador ({} sem material)."""
    if not voz:
        return {}
    if voz not in _BANCOS:
        pasta = VOZES_RVC / voz / "humano"
        try:
            info = json.loads((pasta / "humano.json").read_text(encoding="utf-8"))
            resp = [(pasta / x["arq"], x["dur"]) for x in info.get("respiracoes", []) if (pasta / x["arq"]).exists()]
            _BANCOS[voz] = {"resp": resp, "sala": pasta / "sala.wav" if (pasta / "sala.wav").exists() else None,
                            "n_resp": len(info.get("respiracoes", []))}
        except (OSError, ValueError, KeyError):
            _BANCOS[voz] = {}
        try:  # 22/10 (R5): reações REAIS do narrador (reacoes_colheita / reacoes_reais) — só valem com reacoes_ligadas()
            import wave
            reac = []
            for x in json.loads((pasta / "reacoes.json").read_text(encoding="utf-8")).get("reacoes") or []:
                arq = pasta / x["arq"]
                if arq.exists():
                    with wave.open(str(arq)) as w:
                        reac.append((arq, w.getnframes() / w.getframerate(), x.get("texto", "")))
            if reac:
                _BANCOS[voz]["reac"] = reac
        except (OSError, ValueError, KeyError, EOFError):
            pass
    return _BANCOS[voz]


REACOES_CFG = Path(r"D:\hipercool-materiais\comum\reacoes.json")


def reacoes_ligadas():
    """Reações reais entre frases (22/10, R5): DESLIGADO até o dono aprovar a amostra. Liga: NARRACAO_REACOES=1 (teste)
    ou D:\\hipercool-materiais\\comum\\reacoes.json {"ligado": true} (produção inteira)."""
    v = os.environ.get("NARRACAO_REACOES")
    if v is not None:
        return v == "1"
    try:
        return bool(json.loads(REACOES_CFG.read_text(encoding="utf-8")).get("ligado"))
    except (OSError, ValueError):
        return False


def _plano_ritmo(palavras, texto, dur, amp):
    """[(ini, fim, tempo)] cobrindo o wav inteiro: alonga a última palavra, a de antes da vírgula e a palavra forte;
    acelera o resto na mesma medida (a frase fica com a mesma duração). [] = sem mexer."""
    if amp <= 0 or len(palavras) < 4:
        return []
    toks = re.findall(r"\w+(?:[-']\w+)*[,;:]?", texto)
    virgula = [x[-1] in ",;:" for x in toks] if len(toks) == len(palavras) else [False] * len(palavras)
    fat = []
    for i, (s, e, w) in enumerate(palavras):
        f = 1 - 0.07 * amp if i == len(palavras) - 1 else 1 - 0.05 * amp if virgula[i] else 1.0
        if _ENFASE_PALAVRAS.search(w):
            f = min(f, 1 - 0.06 * amp)
        fat.append(f)
    extra = sum((e - s) * (1 / f - 1) for (s, e, _w), f in zip(palavras, fat) if f < 1)
    resto = sum(e - s for (s, e, _w), f in zip(palavras, fat) if f >= 1)
    rapido = min(1 + 0.08 * amp, resto / (resto - extra)) if resto - extra > 0.2 else 1.0
    fat = [f if f < 1 else rapido for f in fat]
    bordas = [0.0, max(0.0, palavras[0][0] - 0.01)]
    bordas += [(palavras[i][1] + palavras[i + 1][0]) / 2 for i in range(len(palavras) - 1)]
    bordas += [min(dur, palavras[-1][1] + 0.02), dur]
    tempos = [1.0] + fat + [1.0]
    segs = []
    for (a, b), tp in zip(zip(bordas, bordas[1:]), tempos):
        if b - a < 0.005:
            continue
        if segs and (abs(segs[-1][2] - tp) < 1e-3 or b - a < 0.03):
            segs[-1][1] = b
        else:
            segs.append([a, b, tp])
    if any(b <= a for a, b, _tp in segs) or abs(segs[-1][1] - dur) > 0.01:
        return []
    return [tuple(x) for x in segs] if len(segs) > 1 else []


# 22/10 (dono: "o Mike estica 'faaala galerinha' — dá pra replicar? escrever 'faaala' o TTS soletra a-a-a"):
# o alongamento é no ÁUDIO — atempo estica a vogal sem repetir letra, e o tom sobe e DESCE dentro da palavra
# (asetrate compensado), como locutor de verdade. Só na SAUDAÇÃO da 1ª frase, uma vez por vídeo.
_ALONGAVEIS = re.compile(r"^(fala+|salve|bora|opa+|eai|ei|galera|galerinha|cambada|rapaziada|meu[s]?)$", re.I)


def _alongar_abertura(wav, palavras, texto):
    """Estica a vogal da 1ª palavra de saudação (~1,7x, com glide de tom +0,5st -> -0,7st) e corrige o
    words.json. Devolve (palavras_novas, dur_nova) ou None (não se aplica/falhou — fica tudo como estava)."""
    if not palavras:
        return None
    a, b, w0 = palavras[0]
    if not _ALONGAVEIS.match(re.sub(r"[^\wà-ü]+", "", w0 or "")) or b - a < 0.12:
        return None
    import wave as _wave
    try:
        with _wave.open(str(wav)) as f:
            sr, ch, dur0 = f.getframerate(), f.getnchannels(), f.getnframes() / f.getframerate()
    except Exception:  # noqa: BLE001
        return None
    n0 = a + 0.25 * (b - a)            # núcleo da vogal: miolo da palavra
    n1 = min(a + 0.85 * (b - a), dur0)
    meio = (n0 + n1) / 2
    fator = 2.1                         # 2,1x mais longa (dono 22/10: "geralmente é mais longo") — "faaala", não "fa-a-a-la"
    f_cima, f_baixo = 2 ** (0.5 / 12), 2 ** (-0.7 / 12)  # sobe ~0,5 st na 1ª metade, desce ~0,7 st no fim
    fades = "afade=t=in:d=0.004,areverse,afade=t=in:d=0.004,areverse"

    def fatia(nome, ini, fim, pitch=None):
        c = f"[0:a]atrim=start={ini:.4f}:end={fim:.4f},asetpts=PTS-STARTPTS"
        if pitch:
            c += (f",asetrate={sr}*{pitch:.5f},aresample={sr},atempo={max(0.5, (1 / fator) / pitch):.4f}"
                  f",{fades}")
        return c + f"[{nome}]"

    fc = [fatia("p0", 0.0, n0), fatia("na", n0, meio, f_cima), fatia("nb", meio, n1, f_baixo),
          fatia("p1", n1, dur0), "[p0][na][nb][p1]concat=n=4:v=0:a=1[fim]"]
    tmp = Path(str(wav) + ".alonga.wav")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-filter_complex", ";".join(fc),
                        "-map", "[fim]", "-ar", str(sr), "-ac", str(ch), str(tmp)],
                       check=True, timeout=60, capture_output=True, creationflags=SEM_JANELA)
        with _wave.open(str(tmp)) as f:
            dur1 = f.getnframes() / f.getframerate()
        if not (dur0 < dur1 < dur0 + 2):
            raise RuntimeError(f"duração estranha ({dur0:.2f} -> {dur1:.2f})")
        shutil.move(str(tmp), str(wav))
    except Exception as e:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        logging.info(f"[alongar] não deu ({str(e)[:80]}) — fala segue normal")
        return None
    delta = dur1 - dur0
    novas = [(a, b + delta, w0)] + [(x + delta, y + delta, w) for x, y, w in palavras[1:]]
    try:
        Path(str(wav) + ".words.json").write_text(
            json.dumps([[round(x, 3), round(y, 3), w] for x, y, w in novas], ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    logging.info(f"[alongar] '{w0}' esticada ({dur0:.2f}s -> {dur1:.2f}s, glide de tom na vogal)")
    return novas, dur1


def humanizar(wav, texto, indice, impactos, total):
    """Depois do pos_processar, no lugar: de-esser (clone), ênfase nas palavras fortes, ritmo dentro da frase,
    pausa e respiração antes, fundo da sala por baixo, crossfade e vibrato (jitter) — o quanto de cada um vem do
    variacao(). Mexeu na duração = o <wav>.words.json (legenda) acompanha. Falhou = wav e words.json ficam como vieram."""
    if not ligado() or indice is None:
        return
    wav = Path(wav)
    if not wav.exists():
        return
    chave = str(wav.parent)
    v = variacao(chave, indice, texto, impactos, total)
    hist = _HIST.setdefault(chave, {})
    ant1, ant2 = hist.get(indice - 1, {}), hist.get(indice - 2, {})
    r = _sorteio(chave, indice, "decide")
    respira = (indice > 0 and not (ant1.get("respira") and ant2.get("respira"))
               and r.random() < v["respira_p"] * (0.45 if ant1.get("respira") else 1.0))
    pausa = v["pausa_s"] if indice > 0 and not (ant1.get("pausa") and indice not in (impactos or [])) else 0.0
    voz = os.environ.get("VOZ_CLONADA")
    banco = _banco(voz)
    wj = Path(str(wav) + ".words.json")
    try:
        palavras = [(float(a), float(b), str(w)) for a, b, w in json.loads(wj.read_text(encoding="utf-8"))]
    except (OSError, ValueError, TypeError):
        palavras = []
    try:
        import wave
        with wave.open(str(wav)) as w:
            dur = w.getnframes() / w.getframerate()
    except Exception:  # noqa: BLE001
        dur, palavras = 0.0, []
    if indice == 0 and dur and palavras:  # 22/10: "faaala galerinha" — estica a vogal da saudação (ver _alongar_abertura)
        novo = _alongar_abertura(wav, palavras, texto)
        if novo:
            palavras, dur = novo
    segs = _plano_ritmo(palavras, texto, dur, v["ritmo_amp"]) if dur else []
    # 22/10 (dono viu no @PieRecaps): o tique de ACELERAR o fim da frase fica SÓ na voz do próprio pie (é o
    # jeito REAL dele; dar o tique dele pra outro narrador descaracterizaria o outro — dono 14:05: "não sei se
    # é ênfase, e não é no fim de CADA frase"). Suave (1,12-1,18x) e em ~60% das frases, sorteio fixo por frase.
    # Tique de OUTROS narradores: medir do material real deles (perfil_v2) antes de aplicar — não inventar.
    if voz and "pie" in voz.lower() and dur > 1.2 and len(palavras) >= 3:
        import hashlib as _hl
        hv = int(_hl.md5(voz.encode()).hexdigest(), 16)
        if _sorteio(chave, indice, "fim_acelera").random() < 0.6:
            ini_fim = palavras[-2][0]
            acel = 1.12 + (hv % 7) / 100
            if segs:
                segs = [(a, b, tp * (acel if a >= ini_fim - 0.05 else 1.0)) for a, b, tp in segs]
            else:
                segs = [(0.0, ini_fim, 1.0), (ini_fim, dur, acel)]
    fortes = [(a, b) for a, b, w in palavras if b > a and _ENFASE_PALAVRAS.search(w)] if v["enfase_db"] else []

    ins, fc, n_in = ["-i", str(wav)], [], 1
    cadeia = f"[0:a]{_FMT}"
    if voz and v["deesser"]:
        cadeia += f",deesser=i={v['deesser']}"
    vib_f = r.uniform(4.0, 7.0)
    vib_d = r.uniform(0.08, 0.18)
    if voz:
        cadeia += f",vibrato=f={vib_f:.1f}:d={vib_d:.2f}"
    if fortes:
        k = 10 ** (v["enfase_db"] / 20) - 1
        cadeia += ",volume='1" + "".join(f"+{k:.4f}*between(t,{a:.3f},{b:.3f})" for a, b in fortes) + "':eval=frame"
    if segs:
        fc.append(cadeia + f",asplit={len(segs)}" + "".join(f"[s{i}]" for i in range(len(segs))))
        for i, (a, b, tp) in enumerate(segs):
            nd = (b - a) / tp
            fc.append(f"[s{i}]atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS"
                      + (f",atempo={tp:.4f}" if abs(tp - 1) > 1e-3 else "")
                      + f",afade=t=in:d=0.004,afade=t=out:st={max(0.0, nd - 0.004):.4f}:d=0.004[r{i}]")
        fc.append("".join(f"[r{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[fala]")
    else:
        fc.append(cadeia + "[fala]")
    prefixo, antes_s, resp_i, reac_i = [], 0.0, None, None
    if pausa:
        fc.append(f"anullsrc=r=44100:cl=stereo,atrim=duration={pausa:.3f},{_FMT}[pz]")
        prefixo.append("[pz]")
        antes_s += pausa
    # 22/10 (R5, dono: "o próprio personagem/narrador reagindo"): logo DEPOIS de uma frase de impacto, uma reação REAL
    # dele ("caraca", "nossa", risada) antes da próxima fala; no máximo 2 por vídeo, sem repetir; no lugar da respiração
    usadas_reac = [h.get("reac_i") for h in hist.values() if h.get("reac_i") is not None]
    reacoes = banco.get("reac") or []
    if (reacoes_ligadas() and reacoes and indice > 0 and (indice - 1) in (impactos or []) and len(usadas_reac) < 2
            and r.random() < 0.6):
        livres = [i for i in range(len(reacoes)) if i not in usadas_reac]
        if livres:
            reac_i = r.choice(livres)
            arq, d, _txt = reacoes[reac_i]
            ins += ["-i", str(arq)]
            fc.append(f"[{n_in}:a]{_FMT}[rc]")
            n_in += 1
            gap = r.uniform(0.12, 0.22)
            fc.append(f"anullsrc=r=44100:cl=stereo,atrim=duration={gap:.3f},{_FMT}[rg]")
            prefixo += ["[rc]", "[rg]"]
            antes_s += d + gap
            respira = False
    if respira:
        usadas = [hist.get(indice - k, {}).get("resp_i") for k in range(1, 5)]
        reais = banco.get("resp", [])
        livres = [i for i in range(len(reais)) if i not in usadas] if len(reais) >= 4 else []
        if livres:  # respiração de verdade do narrador, sem repetir as últimas
            resp_i = r.choice(livres)
            arq, d = banco["resp"][resp_i]
            ins += ["-i", str(arq)]
            fc.append(f"[{n_in}:a]{_FMT},volume={v['respira_db']:+.1f}dB[rp]")
        else:  # sintética, cada uma de um jeito
            d = r.uniform(0.18, 0.32)
            ins += ["-f", "lavfi", "-i", f"anoisesrc=d={d:.3f}:c={r.choice(['pink', 'brown'])}:r=44100"]
            fc.append(f"[{n_in}:a]{_FMT},highpass=f={r.uniform(150, 350):.0f},lowpass=f={r.uniform(1600, 3000):.0f},"
                      f"afade=t=in:d={d * r.uniform(0.25, 0.45):.3f},afade=t=out:st={d * 0.55:.3f}:d={d * 0.45:.3f},"
                      f"volume={-32 + v['respira_db']:.1f}dB[rp]")
        n_in += 1
        prefixo.append("[rp]")
        antes_s += d
    saida = "fala"
    if prefixo:
        fc.append("".join(prefixo) + f"[fala]concat=n={len(prefixo) + 1}:v=0:a=1[voz]")
        saida = "voz"
    if banco.get("sala"):
        ins += ["-stream_loop", "-1", "-i", str(banco["sala"])]
        fc.append(f"[{n_in}:a]{_FMT},volume={v['sala_db']:+.1f}dB[sl]")
        fc.append(f"[{saida}][sl]amix=inputs=2:duration=first:normalize=0[xf0]")
        saida = "xf0"
    if saida == "fala" and cadeia == f"[0:a]{_FMT}" and not segs:
        hist[indice] = {"respira": False, "pausa": False}
        return
    xf_in = 0.015 if indice > 0 else 0.0
    xf_out = 0.03
    # 20/10: afade out sem st= começa no 0 e emudecia a frase inteira depois de 30 ms (vídeos sem voz das 06:39 às
    # 10:10), e afade in com d=0 vira 1 s. Fade-out pelo avesso (não precisa da duração); fade-in só se tiver.
    fc.append(f"[{saida}]" + (f"afade=t=in:d={xf_in:.3f}," if xf_in else "")
              + f"areverse,afade=t=in:d={xf_out:.3f}:curve=par,areverse[fim]")
    saida = "fim"
    tmp = wav.with_name(wav.stem + ".humano.wav")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fc), "-map", f"[{saida}]",
                        "-ar", "44100", "-ac", "2", str(tmp)], check=True, timeout=90, capture_output=True,
                       creationflags=SEM_JANELA)
        vd = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(tmp), "-af", "volumedetect", "-f", "null",
                             "-"], capture_output=True, timeout=60, creationflags=SEM_JANELA)
        media = re.search(rb"mean_volume: (-?[\d.]+) dB", vd.stderr or b"")
        if not media or float(media.group(1)) < -40:
            raise RuntimeError(f"saiu muda (média {media.group(1).decode() if media else '?'} dB)")
        shutil.move(str(tmp), str(wav))
    except Exception as e:  # noqa: BLE001
        err = getattr(e, "stderr", b"") or b""
        logging.warning(f"[humanizar] frase {indice} falhou ({str(e)[:60]} {err.decode('utf-8', 'replace')[-160:]})"
                        " — wav como veio")
        tmp.unlink(missing_ok=True)
        hist[indice] = {"respira": False, "pausa": False}
        return
    if palavras and (segs or antes_s):
        def novo(t):
            acum = 0.0
            for a, b, tp in segs or [(0.0, dur, 1.0)]:
                if t <= b:
                    return acum + (max(t, a) - a) / tp
                acum += (b - a) / tp
            return acum
        wj.write_text(json.dumps([[round(antes_s + novo(a), 3), round(antes_s + novo(b), 3), w]
                                  for a, b, w in palavras], ensure_ascii=False), encoding="utf-8")
    hist[indice] = {"respira": respira, "pausa": bool(pausa), "resp_i": resp_i, "reac_i": reac_i}
    if reac_i is not None:
        logging.info(f"[humanizar] frase {indice}: reação real '{reacoes[reac_i][2]}' antes da fala (depois do impacto)")
    logging.info(f"[humanizar] frase {indice}: trecho {v['trecho']} energia {v['energia']:+.2f} | "
                 f"pausa {pausa:.2f}s | respira {'real#' + str(resp_i) if resp_i is not None else ('sint' if respira else 'não')}"
                 f" | ênfase {v['enfase_db'] if fortes else 0}dB×{len(fortes)} | ritmo {v['ritmo_amp'] if segs else 0}"
                 f" ({len(segs)} partes) | sala {v['sala_db'] if banco.get('sala') else '-'} | "
                 f"deesser {v['deesser'] if voz else '-'} | ir{v['index_rate']} pr{v['protect']} ve{v['volume_envelope']}"
                 f" | vib {vib_f:.0f}Hz×{vib_d:.0%} | xf {xf_in}/{xf_out}s")
