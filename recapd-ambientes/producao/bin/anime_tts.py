"""anime_tts.py — narração TTS pro anime-pipeline.

Módulo pequeno e isolado. Só faz uma coisa: pegar uma frase e gerar o .wav
da narração (voz narradora Thalita Multilingual, keyless via edge-tts). Usa cache: se o
.wav já existe, não regera (protege quota/tempo).

DUAS CAMADAS DE PROTECAO ANTI-BAN:
  1. anime_script.py — suaviza termos de strike ANTES de salvar o roteiro.
  2. anime_tts.py  — SEGUNDA camada: anti-ban TAMBÉM aqui (proteção dupla).
     Se por algum motivo o roteiro gravado contiver termos de risco, o TTS
     não os lê. Gírias virais disponiveis via VIRAL_SLANG=1.
"""
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# viralizador.py vive no mesmo diretório
sys.path.insert(0, str(Path(__file__).resolve().parent))

import anime_formatos
import edge_tts_engine
import narracao_curva
import viralizador

NARRATOR_VOICE = "pt-BR-ThalitaMultilingualNeural"  # Thalita = padrão aprovado; só Antonio proibida (Francisca/Isabella liberadas 16/10)
# ANIME_TTS_VOICE: versões em outra língua (anime_idiomas, 16/10) usam a voz de narrador do canal daquela língua
NARRATOR_VOICE = os.environ.get("ANIME_TTS_VOICE") or NARRATOR_VOICE
_OUTRA = os.environ.get("ANIME_OUTRA_LINGUA") == "1"  # versão em outra língua (anime_idiomas)

# Voz clonada dos narradores parceiros (dono 19/10): VOZ_CLONADA=<narrador> + VOZ_CLONADA_BASE=francisca|kokoro|misto.
# A frase sai da voz base e o RVC troca o timbre pelo do parceiro (D:\hipercool-materiais\bin\voz_clonada.py).
# Dono ouvindo as amostras: Francisca + clone = pronúncia perfeita; Kokoro + clone = emoção e fala acelerada
# ("narração de jogo"); Andrew + clone = sotaque de gringo (não usar).
VOZES_PY = Path(r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe")
VOZES_DIR = Path(r"D:\hipercool-materiais\models\rvc\vozes")  # na nuvem o sitecustomize traduz D:\ -> raiz/D
# Kokoro na nuvem (Kaggle): os modelos vêm do pacote (raiz/D/hipercool-materiais/models/kokoro)
_KOKORO_OK = os.name == "nt" or (os.environ.get("KOKORO_NUVEM") == "1" and (
    Path(os.environ.get("RAIZ_WIN", "/kaggle/working/raiz")) / "D/hipercool-materiais/models/kokoro/kokoro-v1.0.onnx").exists())
VOZ_CLONADA_PY = Path(r"D:\hipercool-materiais\bin\voz_clonada.py")
FRANCISCA = "pt-BR-FranciscaNeural"


import re


_ROMANOS = {"II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9,
            "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16,
            "XX": 20}


# 28/10 (dona: "leite de coco" saiu "cocô" = merda): palavra que a voz lê com o acento errado -> grafia que força o
# som certo, SÓ no texto falado (a legenda continua com o roteiro). Acrescente aqui o que aparecer.
_PRONUNCIA = [
    (re.compile(r"\b([Cc])oco(s?)\b"), r"\1ôco\2"),          # coco (fruta), nunca "cocô"
]


_RX_ROMANO_1 = re.compile(
    r"(?i:\b(cap[ií]tulo|cap\.|temporada|parte|volume|vol\.|epis[óo]dio|ato|livro|tomo|s[ée]culo|fase|"
    r"henrique|carlos|lu[ií]s|jo[ãa]o|pedro|afonso|fel?ipe|filipe|jorge|eduardo|guilherme|ricardo|le[ãa]o|pio|bento|"
    r"paulo|alexandre|ivan|fernando|manuel|frederico) )(V|X)\b")


def _pronuncia(t):
    for rx, troca in _PRONUNCIA:
        t = rx.sub(troca, t)
    return t


def _seguro(text):
    t = _pronuncia(viralizador.anti_ban(text))
    t = re.sub(r"(?<=\S )(II|III|IV|VI|VII|VIII|IX|XI|XII|XIII|XIV|XV|XVI|XX)\b",
               lambda m: str(_ROMANOS[m.group(1)]) if m.group(1) in _ROMANOS else m.group(0), t)
    # "V" e "X" sozinhos quase sempre são LETRA ("o X da questão", "Sr. X", "Projeto X", "Rank X" saíam "10"): só
    # viram número depois de capítulo/parte/temporada... ou de nome de rei/papa ("Henrique V", "Capítulo X")
    t = _RX_ROMANO_1.sub(lambda m: m.group(1) + " " + str(_ROMANOS[m.group(2)]), t)
    return viralizador.viralizar(t) if os.environ.get("VIRAL_SLANG") == "1" else t


def clone_ligado():
    return bool(os.environ.get("VOZ_CLONADA"))


def base_da_frase(modo, texto, indice, impactos, total):
    """misto: Kokoro (emoção, acelerado) na abertura e chegando nos impactos (a curva sobe 8%+), Francisca (pronúncia)
    no resto — mesmo timbre, ritmo que muda como o de um narrador humano."""
    if modo != "misto":
        return modo
    return "kokoro" if indice == 0 or narracao_curva.deltas(texto, indice, impactos, total)[0] >= 8 else "francisca"


_PERSONAGENS_COMICOS = {"pica_pau", "chaves", "chaves_chapolin", "chapolin_colorado", "chiquinha", "seu_madruga",
                        "patrick_estrela", "lula_molusco", "seu_sirigueijo_peter_griffin", "patolino", "woody",
                        "buzz_lightyear", "alex_madagascar", "puss_in_boots_gato_de_botas_portuguese_d", "moana",
                        "gretchen", "galvao_bueno", "bulma", "jessie_toy_story", "dino_da_silva_sauro_familia_dinossauro",
                        "baby_familia_dinossauro", "quico", "faustao"}


def _perfil_v2(voz):
    """Clone 2.0 (dono 19/10): perfil de fala do narrador medido no material real (D:\\hipercool-materiais\\bin\\
    clone2.py). Só com VOZ_CLONADA_VERSAO=2; sem perfil = v1."""
    if os.environ.get("VOZ_CLONADA_VERSAO") != "2":
        return None
    arq = Path(r"D:\hipercool-materiais\models\rvc\vozes") / voz / "perfil_v2.json"
    perfil = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None
    frases = ((perfil or {}).get("medido") or {}).get("frases") or 0
    if frases < 8:
        # 29/10 dona: "todos os personagens falando monótono, como se fossem a Moana". Causa medida: 49 dos 65 perfis
        # foram medidos com 0–3 frases (personagens: Moana 3, Walter 1, Pica-Pau 0...) → f0_escala ~1,0 e rate −7 =
        # a entonação chapada da voz base, só o timbre muda. Sem medida confiável = a entonação dos narradores reais
        # mais expressivos (p75 dos 16 bem medidos: f0 1,45, tom_extra 1,54, curva_rate 1,1, ganho 1,15) e, pra
        # personagem (personagem.json / cartoon), um tanto a mais. O EQ medido (timbre) fica.
        personagem = (arq.parent / "personagem.json").exists() or voz in _PERSONAGENS_COMICOS
        f0 = 1.6 if personagem else 1.45
        a = (perfil or {}).get("aplicar") or {}
        a.update(curva_rate=1.25 if personagem else 1.1, curva_ganho=1.3 if personagem else 1.15,
                 tom_extra_st=1.8 if personagem else 1.54, cauda=a.get("cauda", 0.25),
                 cauda_impacto=a.get("cauda_impacto", 0.6))
        a["francisca"] = {**(a.get("francisca") or {"eq": []}), "f0_escala": f0,
                          "rate": max((a.get("francisca") or {}).get("rate", 0), 3 if personagem else 0)}
        a["kokoro"] = {**(a.get("kokoro") or {"eq": []}), "f0_escala": f0,
                       "velocidade": max((a.get("kokoro") or {}).get("velocidade", 1.0), 1.03 if personagem else 1.0)}
        logging.info(f"[clone] {voz}: perfil medido com {frases} frase(s) — entonação expressiva "
                     f"({'personagem' if personagem else 'narrador'}, f0 x{f0})")
    else:
        a = perfil["aplicar"]
    # dono 26/10 ("narrador falando tão devagar"): sem legenda pra medir, o perfil herda a mediana (-7%, x0.87),
    # 12% abaixo da voz normal (+5%). Piso: nenhum clone fala mais devagar que a narração normal.
    a["francisca"]["rate"] = max(a["francisca"]["rate"], narracao_curva.BASE_RATE)
    a["kokoro"]["velocidade"] = max(a["kokoro"]["velocidade"], 0.98)
    return a


def _frase_v2(a, base, texto, indice, impactos, total, chave):
    """Ritmo, pausa, volume e entonação DO NARRADOR em cima da curva de locutor: velocidade base dele, amplitude da
    curva e do volume na medida dele, pausa dele, tom que varia entre frases como o dele, faixa de entonação, EQ e o
    jeito dele de fechar a frase (final_st, na força que o narracao_curva.variacao der pra esta frase)."""
    import hashlib
    dr, dp, dg, _cauda = narracao_curva.deltas(texto, indice, impactos, total)
    dr2 = dr * a["curva_rate"]
    cauda = a["cauda_impacto"] if indice in (impactos or []) else a["cauda"]
    if total is not None and indice == total - 1:
        cauda = max(cauda, 1.5)
    ruido = (int(hashlib.md5(texto.encode("utf-8")).hexdigest(), 16) % 5 - 2) / 4
    tom_extra = int(round(max(-2.0, min(2.0, (dr / narracao_curva.PICO_RATE + ruido) * a["tom_extra_st"]))))
    extra = {"tom_extra": tom_extra, "f0_escala": a[base]["f0_escala"], "eq": a[base]["eq"]}
    v = narracao_curva.variacao(chave, indice, texto, impactos, total)
    extra["index_rate"] = v["index_rate"]
    extra["protect"] = v["protect"]
    extra["volume_envelope"] = v["volume_envelope"]
    if a[base].get("final_st"):
        extra["final_st"] = round(a[base]["final_st"] * v["final_mult"], 2)
    # 29/10 teste T9 (Fable; dona: "quero os vídeos falando mais rápido, um louco como o parceiro kaijime, mas pode
    # ficar ruim em alguns — gera variante e vai testando"): CORTES_FALA_DELTA = pontos % a mais na velocidade da fala
    # (B = +15); vazio/0 = como sempre. Vale para o clone (Edge rate e Kokoro vel), nunca para a voz Edge pura.
    try:
        delta_fala = float(os.environ.get("CORTES_FALA_DELTA") or 0)
    except ValueError:
        delta_fala = 0.0
    if base == "kokoro":
        vel = max(0.75, min(1.6, a["kokoro"]["velocidade"] * (1 + (dr2 + delta_fala) / 100)))
        return extra, f"x{vel:.2f}", None, dg * a["curva_ganho"], cauda, round(vel, 2)
    rate = int(round(max(-40, min(70, a["francisca"]["rate"] + dr2 + delta_fala))))
    return extra, f"{rate:+d}%", f"{dp:+d}Hz", dg * a["curva_ganho"], cauda, None


TRECHOS = Path(r"D:\hipercool-materiais\amostras_voz\trechos_icones")


def _abrir_com_trecho(voz, wav):
    """Personagem com trecho original curto (dono 20/10: "Não contavam com minha astúcia!", risada do Pica-Pau):
    o trecho abre o vídeo antes da 1ª frase; o tempo das palavras da frase anda junto. Falhou = segue sem trecho."""
    try:
        lista = json.loads((TRECHOS / voz / "trechos.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not lista or not wav.exists():
        return None
    t = lista[int(hashlib.md5(str(wav.parent).encode()).hexdigest(), 16) % len(lista)]
    src = TRECHOS / voz / t["arquivo"]
    tmp = wav.with_name(wav.stem + ".trecho.wav")
    fmt = "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo"
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-i", str(wav), "-filter_complex",
                        f"[0:a]{fmt},apad=pad_dur=0.25[a];[1:a]{fmt}[b];[a][b]concat=n=2:v=0:a=1[o]", "-map", "[o]",
                        str(tmp)], check=True, capture_output=True, timeout=60, creationflags=0x08000000)
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                           capture_output=True, text=True, timeout=30, creationflags=0x08000000)
        desloc = float(r.stdout.strip()) + 0.25
        tmp.replace(wav)
    except Exception as e:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        logging.warning(f"[clone] trecho original de {voz} não entrou ({e})")
        return None
    wj = Path(str(wav) + ".words.json")
    try:
        palavras = json.loads(wj.read_text(encoding="utf-8"))
        wj.write_text(json.dumps([[round(a + desloc, 3), round(b + desloc, 3), w] for a, b, w in palavras],
                                 ensure_ascii=False), encoding="utf-8")
    except (OSError, ValueError):
        pass
    logging.info(f"[clone] abre com trecho original de {voz}: '{t.get('frase', '')[:60]}' ({desloc:.1f}s)")
    return f"{t.get('frase', '')} — {t.get('titulo', '')} {t.get('url', '')}"


def _proteger_cauda_bruto(wav):
    """Adiciona margem curta ao bruto antes do RVC para evitar corte do último fonema na janela STFT."""
    wav = Path(wav)
    if not wav.exists() or wav.stat().st_size < 500:
        return
    tmp = wav.with_name(wav.stem + ".pad.wav")
    flags = 0x08000000 if os.name == "nt" else 0
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", "apad=pad_dur=0.4", str(tmp)],
                       check=True, capture_output=True, timeout=30, creationflags=flags)
        tmp.replace(wav)
    except Exception:  # noqa: BLE001
        tmp.unlink(missing_ok=True)


def _aplicar_margem_final(wav, margem=None, fade=0.5):
    """Garante margem (padding) com fade-out no áudio da última frase (fechamento/encerramento).
    Evita truncamento do último fonema, permite Whisper transcrever a palavra inteira
    e mantém movimento (Ken Burns) do último painel até o fim do vídeo."""
    wav = Path(wav)
    if not wav.exists() or wav.stat().st_size < 500:
        return
    tag = wav.with_name(wav.stem + ".margem_ok")
    if tag.exists():
        return
    if margem is None:
        try:
            margem = float(os.environ.get("ANIME_TTS_MARGEM_FINAL", "2.0"))
        except ValueError:
            margem = 2.0
    flags = 0x08000000 if os.name == "nt" else 0
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                           capture_output=True, text=True, timeout=30, creationflags=flags)
        dur = float(r.stdout.strip())
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[anime_tts] ffprobe falhou em {wav.name} ({e})")
        return
    fade_dur = min(fade, margem / 2)
    fade_start = max(0.0, dur + margem - fade_dur)
    fmt = "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo"
    filtros = f"{fmt},apad=pad_dur={margem:.3f},afade=t=out:st={fade_start:.3f}:d={fade_dur:.3f}"
    tmp = wav.with_name(wav.stem + ".margem.wav")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", filtros, str(tmp)],
                       check=True, capture_output=True, timeout=60, creationflags=flags)
        tmp.replace(wav)
        try:
            tag.write_text("1", encoding="utf-8")
        except OSError:
            pass
        logging.info(f"[anime_tts] margem final aplicada em {wav.name}: +{margem:.1f}s (fade {fade_dur:.1f}s, total {dur + margem:.1f}s)")
    except Exception as e:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        logging.warning(f"[anime_tts] margem final falhou em {wav.name} ({e})")


def preparar_clone(lines, audio_dir, impactos, so=None, abertura=True):
    """Narra TODAS as frases com a voz clonada antes da montagem (o loop do anime_segments acha os wavs prontos).
    Uma chamada só ao voz_clonada.py lote: o Applio carrega 1x (frase a frase era ~1 min de carga cada).
    Falhou = levanta: vídeo com metade da voz clonada não pode sair."""
    voz, modo = os.environ["VOZ_CLONADA"], os.environ.get("VOZ_CLONADA_BASE", "francisca")
    perfil = _perfil_v2(voz)
    audio_dir = Path(audio_dir)
    bases = audio_dir / "_base_clone"
    bases.mkdir(parents=True, exist_ok=True)
    itens, depois, resumo = [], [], []
    pedidos_edge = []  # 04/11: (futuro, i, voz) dos pedidos ao Edge em paralelo
    climas = None
    try:  # dono 20/10: a mesma voz muda de jeito conforme o clima do trecho (climas_voz.py); falhou = como antes
        import climas_voz
        climas = climas_voz.escolher([_seguro(x) for x in lines], audio_dir)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[clone] climas desligados neste vídeo ({type(e).__name__}: {str(e)[:80]})")
    for i, line in enumerate(lines):
        if so is not None and i not in so:  # revezamento (26/10): esta chamada narra só o bloco desta voz
            continue
        out = audio_dir / f"audio_{i}.wav"
        if out.exists() and out.stat().st_size > 500:
            continue
        texto = _seguro(line)
        aj = None
        if climas:
            try:
                aj = climas_voz.ajustes(voz, climas, i)
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[clone] clima da frase {i} falhou ({e}) — normal")
        base = (aj or {}).get("base") or base_da_frase(modo, texto, i, impactos, len(lines))
        if base == "kokoro" and not _KOKORO_OK:  # 26/10 (dona: "as vozes clonadas dos Cortes"): só sem o modelo
            base = "francisca"
        # 28/10: outra língua = base Edge da língua (Kokoro aqui é pt). ANIME_OUTRA_LINGUA, NÃO ANIME_TTS_VOICE: o
        # parceiro em pt também põe ANIME_TTS_VOICE (narradores do nicho, Emma/Andrew) e o pt saía com base gringa
        if _OUTRA:
            base = "francisca"
        if perfil:
            extra, rate, pitch, ganho, cauda, vel = _frase_v2(perfil, base, texto, i, impactos, len(lines),
                                                              str(audio_dir))
        else:
            rate, pitch, ganho, cauda = narracao_curva.prosodia(texto, i, impactos, len(lines))
            extra, vel = {}, max(0.85, min(1.35, 1 + int(rate.rstrip("%")) / 100))
        eco = None
        if aj and aj["clima"] != "normal":
            try:
                ex = dict(extra)
                if aj["clima"] != "engracado":
                    # clima forte manda: a curva de gol (impactos) não acelera o vilão nem freia a luta
                    rate_base = perfil["francisca"]["rate"] if perfil else narracao_curva.BASE_RATE
                    vel = perfil["kokoro"]["velocidade"] if perfil else 1.0
                    rate, ganho, ex["tom_extra"] = f"{int(rate_base):+d}%", 0.0, 0
                ex["tom_extra"] = int(ex.get("tom_extra", 0)) + aj["st"]
                ex["f0_escala"] = round(float(ex.get("f0_escala", 1.0)) * aj["f0"], 3)
                if aj["final"] is not None:
                    ex["final_st"] = aj["final"]
                ex["eq"] = climas_voz.juntar_eq(ex.get("eq"), aj["eq"])
                if base == "kokoro":
                    vel = round(max(0.75, min(1.6, (vel or 1.0) * aj["vel"])), 2)
                else:
                    rate = f"{int(round(max(-40, min(70, int(str(rate).rstrip('%')) + aj['rate'])))):+d}%"
                extra, ganho, cauda, eco = ex, ganho + aj["db"], max(0.05, cauda + aj["pausa"]), aj["eco"]
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[clone] ajuste do clima na frase {i} falhou ({e}) — normal")
        if os.environ.get("VOZ_CLONADA_CONFIG") == "2":  # timbre forte (anime_voz_clonada.CONFIGS)
            extra = {**extra, "index_rate": 0.8, "protect": 0.33, "volume_envelope": 0.8}
        resumo.append({"i": i, "base": base, "rate": rate if base != "kokoro" else f"x{vel}", "clima": (aj or {}).get("clima", "normal"),
                       "tom_extra": int(extra.get("tom_extra", 0)), "index_rate": extra.get("index_rate", 0.5),
                       "protect": extra.get("protect", 0.33), "volume_envelope": extra.get("volume_envelope", 1.0),
                       "texto": texto})
        sidecar = None
        if base == "kokoro":
            itens.append({"saida": str(out), "tom_base": "1_kokoro", "texto": texto, "velocidade": round(vel, 2),
                          **extra})
        else:
            bruto = bases / f"audio_{i}.wav"
            # sem contour: o edge grátis recusa (No audio was received) e o vigia achou que a Microsoft bloqueou a voz (20/10)
            voz_base = NARRATOR_VOICE if _OUTRA else FRANCISCA  # 28/10: outra língua = Edge da língua + clone
            # 04/11 dona (item 5, "faça"): o Edge era 1 frase por vez (923 x ~2,6 s = 41 min no waaQ, só esperando a
            # rede). Os parâmetros de cada frase continuam calculados AQUI, em ordem; só o pedido ao Edge vai pra
            # ANIME_EDGE_PARALELO (4) ao mesmo tempo. Mesmo texto/voz/rate/pitch = mesmo áudio. Falhou = levanta no fim.
            if _EDGE_POOL["ex"] is None:
                from concurrent.futures import ThreadPoolExecutor as _TPE
                _EDGE_POOL["ex"] = _TPE(max_workers=max(1, int(os.environ.get("ANIME_EDGE_PARALELO", "4") or 4)))
            pedidos_edge.append((_EDGE_POOL["ex"].submit(edge_tts_engine.speak, texto, voice=voz_base,
                                                         out_wav=str(bruto), persona="Narrador", rate=rate,
                                                         pitch=pitch), i, voz_base))
            itens.append({"saida": str(out), "tom_base": "2_edge_francisca", "entrada": str(bruto), **extra})
            sidecar = Path(str(bruto) + ".words.json")
        depois.append((out, ganho, cauda, sidecar, i, texto, eco))
        logging.info(f"[clone{' v2' if perfil else ''}] frase {i}: {(aj or {}).get('clima', 'normal')} {base} {rate}"
                     + (f" tom{extra.get('tom_extra', 0):+d}" if extra else "")
                     + (f" fim{extra['final_st']:+.2f}st" if extra.get("final_st") else ""))
    for fut, i, voz_base in pedidos_edge:  # 04/11: espera os Edge em paralelo; 1 falhou = mesmo erro de antes
        try:
            ok_edge = fut.result()
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"[clone] edge {voz_base} falhou na frase {i} ({type(e).__name__}: {e})") from e
        if not ok_edge:
            raise RuntimeError(f"[clone] edge {voz_base} falhou na frase {i}")
    if not itens:
        return
    lista = bases / "lista.json"
    lista.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
    # 22/10 (R2 + dono 13:40: "o vídeo não pode estragar por consumo — desacelera sozinho, sem erro; e o vídeo
    # tem prioridade sobre o resto"): espera ter ~3 GB de RAM livre (até 45 min, dormindo — devagar, nunca erro)
    # antes do lote; se mesmo assim falhar, UMA nova tentativa (o que já saiu fica, o lote refaz só o que falta).
    try:
        import psutil
        inicio_espera = time.time()
        while psutil.virtual_memory().available < 1 * 1024 ** 3 and time.time() - inicio_espera < 45 * 60:
            logging.info(f"[clone] RAM baixa ({psutil.virtual_memory().available / 1024 ** 3:.1f} GB livre) — "
                         "esperando 60 s antes do lote (o vídeo espera, não estraga)")
            time.sleep(60)
    except ImportError:
        pass
    for tentativa in (1, 2):
        with open(bases / "clone.log", "a", encoding="utf-8") as fh:
            # prioridade NORMAL (0x20; era BELOW_NORMAL 0x4000): o clone É o vídeo — não pode apanhar de
            # trabalho de fundo (treino/separador). Não usamos ABOVE: o render do hipercool também é vídeo.
            if os.name == "nt":
                r = subprocess.run([str(VOZES_PY), str(VOZ_CLONADA_PY), "lote", voz, str(lista)], stdout=fh,
                                   stderr=subprocess.STDOUT, timeout=4 * 3600, creationflags=0x00000020 | 0x08000000)
            else:  # 25/10: Kaggle com GPU (recap longo) — o mesmo lote, Applio no ambiente próprio (VOZES_PY_NUVEM)
                r = subprocess.run([os.environ.get("VOZES_PY_NUVEM", sys.executable),
                                    str(Path(__file__).with_name("voz_clonada_nuvem.py")), "lote", voz, str(lista)],
                                   stdout=fh, stderr=subprocess.STDOUT, timeout=6 * 3600)
        faltam = [str(o) for o, *_ in depois if not o.exists()]
        if r.returncode == 0 and not faltam:
            break
        if tentativa == 1:
            logging.warning(f"[clone] lote rc={r.returncode}, faltam {len(faltam)} — 1 nova tentativa em 90 s")
            time.sleep(90)
    if r.returncode != 0 or faltam:
        raise RuntimeError(f"[clone] voz_clonada lote rc={r.returncode}, faltam {len(faltam)} (ver {bases / 'clone.log'})")
    for out, ganho, cauda, sidecar, idx, texto, eco in depois:
        if sidecar and sidecar.exists():  # timing por palavra do edge vale: o RVC mantém a duração
            sidecar.replace(Path(str(out) + ".words.json"))
        narracao_curva.pos_processar(out, ganho, cauda)
        narracao_curva.humanizar(out, texto, idx, impactos, len(lines))
        anime_formatos.aplicar_efeito_voz(voz, out)  # efeito próprio da voz (ex.: tremido da Aracy), do cadastro dela
        if eco:
            climas_voz.aplicar_eco(out, eco)
    import anime_script  # dono 26/10: dorama/filme = o protagonista narra; a fala real do personagem quebraria isso
    # abertura=False: frase solta no meio do vídeo (cortes_produto), sem a fala real do personagem na frente
    trecho = None if (anime_script.primeira_pessoa() or not abertura or (so is not None and 0 not in so)
                      or _OUTRA) \
        else _abrir_com_trecho(voz, audio_dir / "audio_0.wav")
    if trecho:
        resumo.insert(0, {"i": "abertura", "base": "trecho ORIGINAL", "rate": "", "texto": trecho})
    if os.environ.get("VOZ_CLONADA_RESUMO"):
        try:
            Path(os.environ["VOZ_CLONADA_RESUMO"]).write_text(json.dumps(resumo, ensure_ascii=False), encoding="utf-8")
        except OSError as e:
            logging.warning(f"[clone] resumo não gravado ({e})")
    logging.info(f"[clone] {len(itens)} frases com a voz de {voz} ({modo}{', v2' if perfil else ''}, "
                 f"config {os.environ.get('VOZ_CLONADA_CONFIG', '1')})")


# ─── revezamento de narradores (dona 26/10: "vídeos de manhwa são grandes: um narrador passa a bola pro outro de um
# jeito engraçado"; "produzir logo esse misto pra escolher quais narradores não servem pra manhwa") ─────────────────
_PASSAGENS = [
    "Valeu, {a}, pode ir tomar sua água que daqui eu assumo. Aqui é {b}!",
    "{a} já falou demais, me passa esse microfone! Quem continua agora é {b}.",
    "Opa, troca de turno! {a} saiu pro lanche e eu, {b}, fico com a melhor parte.",
    "Calma, {a}, deixa o resto comigo, {b}, que essa parte é a minha especialidade.",
    "E direto do banco de reservas, entra {b} no lugar de {a}! Segura que agora esquenta.",
    "Obrigado, {a}, mas a partir daqui a história é minha. {b} na área!",
]


# Dona 26/10: narrador PARCEIRO (voz de canal real) nunca é chamado pelo nome na troca; só PERSONAGEM (Kratos, Naruto...)
_PASSAGENS_SEM_NOME = [
    "Valeu, parceiro, pode ir tomar sua água que daqui eu assumo!",
    "Já falou demais, me passa esse microfone que agora é comigo.",
    "Opa, troca de turno! Vai lá pro lanche que eu fico com a melhor parte.",
    "Calma, deixa o resto comigo que essa parte é a minha especialidade.",
    "E direto do banco de reservas, entra um narrador novo! Segura que agora esquenta.",
    "Obrigado, meu chapa, mas a partir daqui a história é minha.",
]


def eh_personagem(voz):
    """True se a voz é de PERSONAGEM (personagem.json ou linguagem_v2 tipo personagem); False = narrador parceiro."""
    if (VOZES_DIR / voz / "personagem.json").exists():
        return True
    try:
        return json.loads((VOZES_DIR / voz / "linguagem_v2.json").read_text(encoding="utf-8")).get("tipo") == "personagem"
    except (OSError, ValueError):
        return False


def nome_voz(voz):
    """Nome que a legenda e a passagem usam pra voz (formatos_voz.json nome_legenda; senão o nome da pasta)."""
    try:
        import anime_formatos
        n = str(anime_formatos.config().get("vozes", {}).get(voz, {}).get("nome_legenda") or "").strip()
        if n:
            return n
    except Exception:  # noqa: BLE001
        pass
    return voz.replace("_", " ").title()


def _com_narrador(voz, fn):
    """Roda fn() com o 'narrador da vez' = voz (o anime_script lê o jeito dele pelo VOZ_CLONADA + versão 2)."""
    antes = {k: os.environ.get(k) for k in ("VOZ_CLONADA", "VOZ_CLONADA_VERSAO")}
    os.environ.update(VOZ_CLONADA=voz, VOZ_CLONADA_VERSAO="2")
    try:
        return fn()
    finally:
        for k, v in antes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


_ARGON = {"falhou": False}
_EDGE_POOL = {"ex": None}  # 04/11: pedidos ao Edge em paralelo (preparar_clone)
GEMINI_TEXTO = os.environ.get("GEMINI_TEXTO_VIDEO", "antigravity/gemini-3.8-flash-tiered")


def _criativo(prompt, max_tokens, temperature, timeout, curto=False):
    """Dona 27/10: Argon puro (proxy :20133, mesma chave do OmniRoute) SÓ no texto CURTO (passagem de vez: ~1 min, 9
    por vídeo) — no texto longo (jeito do narrador, 40 linhas) ele levava 1–5 min por bloco e somava 1 h+ no vídeo.
    Demorou (> 90 s) ou falhou = o resto do vídeo vai pro Gemini 3.8 (Argon trava se martelar; 4 GPUs chamam juntas).
    Texto longo = Gemini 3.8 direto. TEXTO_VIDEO_MODELO troca o modelo curto (vazio = só Gemini)."""
    import claude_client
    modelo = os.environ.get("TEXTO_VIDEO_MODELO", "gemini-4-argon")
    if curto and modelo and not _ARGON["falhou"]:
        try:
            import urllib.request
            cfg = claude_client._load_cfg()
            base = os.environ.get("ARGON_BASE_URL", "http://157.173.207.22:20133")
            req = urllib.request.Request(base + "/v1/messages", data=json.dumps(
                {"model": modelo, "max_tokens": max_tokens, "temperature": temperature,
                 "messages": [{"role": "user", "content": prompt}]}).encode("utf-8"),
                headers={"content-type": "application/json", "x-api-key": cfg["key"],
                         "anthropic-version": "2023-06-01"})
            # 27/10: nas passagens medidas o Argon levou 17–83 s; 120 s deixa ele trabalhar sem somar muito (9 por vídeo)
            # 03/11 (dona aprovou "ir direto pro 3.8 quando o Argon recusar"): o timeout do urlopen vale por leitura,
            # não pelo total — a fila do Argon segurou a 1ª chamada 9,5 min (waaQ, 429 no fim) e 6 min (xshd). Teto
            # REAL de 90 s no relógio; passou = o resto do vídeo vai pro Gemini 3.8 (como já dizia a regra de 27/10).
            import concurrent.futures as _cf

            def _chamar():
                with urllib.request.urlopen(req, timeout=60) as r:
                    return "".join(p.get("text", "") for p in json.loads(r.read().decode("utf-8")).get("content", [])
                                   if p.get("type") == "text").strip()
            _ex = _cf.ThreadPoolExecutor(max_workers=1)
            try:
                txt = _ex.submit(_chamar).result(timeout=float(os.environ.get("ARGON_TETO_S", "90")))
            except _cf.TimeoutError:
                raise TimeoutError("Argon passou de 90 s no total")
            finally:
                _ex.shutdown(wait=False)
            if txt and "encountering an error" not in txt:
                return txt
            raise RuntimeError(f"resposta vazia/erro: {txt[:80]!r}")
        except Exception as e:  # noqa: BLE001
            _ARGON["falhou"] = True
            logging.warning(f"[revezamento] {modelo} falhou ({type(e).__name__}: {str(e)[:120]}) — resto no Gemini 3.8")
    # 27/10 (dona: "3º fallback se o 3.8 antigravity acabar ou demorar"): 3.8 por 2 rotas e o Gemini 3 de antes.
    # Gemini Pro grátis não respondia (429 cooling down / timeout) — fica fora até voltar. Quem demorar mais que o
    # limite ou falhar sai do resto do vídeo. Uma tentativa por modelo (o _post repetia 3x = 3x o tempo).
    for m in (GEMINI_TEXTO, "agy/gemini-3.8-flash-high", None):
        if m in _ARGON.setdefault("fora", set()):
            continue
        t0 = time.time()
        txt = claude_client._post([{"role": "user", "content": prompt}], max_tokens=max_tokens,
                                  temperature=temperature, model=m, timeout=timeout, max_retries=1)
        if txt:
            return txt
        if m:
            _ARGON["fora"].add(m)
            logging.warning(f"[revezamento] {m} falhou/demorou ({time.time() - t0:.0f} s) — próximo modelo")
    return None


def _no_jeito(voz, linhas):
    """Dona 26/10 ("cada um tem um jeito de narrar"): reescreve o bloco no jeito DESTE narrador (linguagem_v2 dele),
    linha a linha — mesma quantidade e mesmos fatos (a linha i continua no segundo do original que ela narra)."""
    import anime_script
    import claude_client
    if not claude_client.is_available():
        return linhas
    jeito = _com_narrador(voz, lambda: anime_script._jeito_do_narrador(gancho=True))
    if not jeito:
        return linhas
    saida = []
    for ini in range(0, len(linhas), 40):
        parte = linhas[ini:ini + 40]
        prompt = ("Reescreva CADA linha numerada abaixo no jeito deste narrador de recap de manhwa. Regras: a MESMA "
                  f"quantidade de linhas ({len(parte)}), na mesma ordem, formato 'N| texto'; os mesmos fatos (não "
                  "invente nem tire acontecimento); tamanho parecido (no máximo 30% mais longa); português falado; SEM palavrão (o YouTube desmonetiza)."
                  + jeito + "\n\n" + "\n".join(f"{j + 1}| {t}" for j, t in enumerate(parte)))
        try:
            resp = _criativo(prompt, max_tokens=4000, temperature=0.7, timeout=240) or ""
            novas = {}
            for l in resp.splitlines():
                m = re.match(r"\s*(\d+)\s*[|)\-.:]\s*(.+)", l)
                if m:
                    novas[int(m.group(1))] = m.group(2).strip()
            saida += [novas.get(j + 1) or t for j, t in enumerate(parte)] if len(novas) >= len(parte) * 0.9 else parte
        except Exception as e:  # noqa: BLE001 — sem o jeito dele, fica o texto do roteiro
            logging.warning(f"[revezamento] jeito de {voz} falhou ({type(e).__name__}) — texto original")
            saida += parte
    return saida


def _guia(voz):
    try:
        return json.loads((VOZES_DIR / voz / "linguagem_v2.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _passagem(a, b, antes, depois, k):
    """Dona 26/10 ("a troca tem que ser criativa, não pode só mudar a voz"): cena curta de troca escrita pela IA pro
    momento da história — quem SAI fecha (na voz dele) e quem ENTRA responde (na dele), cada um no seu jeito, podendo se
    provocar. Falhou = uma das passagens prontas (_PASSAGENS)."""
    import claude_client
    na, nb = nome_voz(a), nome_voz(b)
    pa, pb = eh_personagem(a), eh_personagem(b)
    if pa and pb:
        reserva = ("", _PASSAGENS[(k - 1) % len(_PASSAGENS)].format(a=na, b=nb))
    else:
        reserva = ("", _PASSAGENS_SEM_NOME[(k - 1) % len(_PASSAGENS_SEM_NOME)])
    regra_nome = (f"Nomes: {'o que SAI pode ser chamado de ' + na if pa else 'o que SAI é um narrador parceiro: NUNCA diga o nome dele'}; "
                  f"{'o que ENTRA pode se apresentar como ' + nb if pb else 'o que ENTRA é um narrador parceiro: NUNCA diga o nome dele'}"
                  ". Sem nome, chame de 'parceiro', 'meu chapa', 'colega' etc.")
    if not claude_client.is_available():
        return reserva
    ga, gb = _guia(a), _guia(b)
    prompt = (f"Num recap longo de manhwa, vários narradores se revezam. Agora o narrador A passa a vez pro narrador B.\n"
              f"A: {ga.get('resumo', '')} Tom: {ga.get('tom', '')}. Jeito de zoar: {ga.get('tiradas', '')}\n"
              f"B: {gb.get('resumo', '')} Tom: {gb.get('tom', '')}. Jeito de zoar: {gb.get('tiradas', '')}\n"
              f"O que A acabou de contar: {' '.join(antes[-3:])}\n"
              f"O que B vai contar agora (vem LOGO DEPOIS da fala dele — não repita nem resuma isso): {' '.join(depois[:3])}\n"
              f"{regra_nome}\n\n"
              "Escreva a troca: 'sai' = a última fala de quem SAI (fecha o trecho comentando o que aconteceu e passa a vez) "
              "e 'entra' = a primeira de quem ENTRA (responde/provoca de um jeito curto e esquenta o que vem, SEM contar "
              "o fato da próxima frase). "
              "Engraçada, criativa e do momento da história — nunca genérica tipo 'agora é minha vez'. Cada uma com "
              "no máximo 25 palavras, português falado, cada um no SEU jeito, SEM palavrão (o YouTube desmonetiza). "
              "Responda só o JSON "
              '{"sai": "...", "entra": "..."}')
    try:
        resp = _criativo(prompt, max_tokens=400, temperature=0.9, timeout=120, curto=True) or ""
        d = json.loads(re.search(r"\{.*\}", resp, re.S).group(0))
        sai, entra = str(d.get("sai", "")).strip(), str(d.get("entra", "")).strip()
        if entra and len(sai.split()) <= 35 and len(entra.split()) <= 35:
            return sai, entra
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[revezamento] passagem {na}->{nb} falhou ({type(e).__name__}) — passagem pronta")
    return reserva


def _inicios_blocos(n, k):
    """Índice da 1ª linha de cada bloco. Dona 31/10: o principal saía depois de ~1 min (CCJQvNP-23Y) — agora o 1º
    bloco tem no mínimo REVEZ_PRIMEIRO_FRAC do vídeo (35%) e nunca menos que o resumo + REVEZ_PRIMEIRO linhas;
    o resto é dividido em partes iguais entre os outros."""
    if k <= 1 or n <= k:
        return [min(b, n) for b in range(k)]
    try:
        n_res = int(os.environ.get("ANIME_RESUMO_N") or 0)
    except ValueError:
        n_res = 0
    frac = float(os.environ.get("REVEZ_PRIMEIRO_FRAC", "0.35") or 0.35)
    s0 = max(frac * n, n / k, float(os.environ.get("REVEZ_PRIMEIRO", "12") or 12) + max(0, n_res))
    s0 = min(s0, n - (k - 1))
    passo = (n - s0) / (k - 1)
    return [0] + [min(n - (k - b), round(s0 + passo * (b - 1))) for b in range(1, k)]


def _lista_env(nome, padrao):
    return {v.strip() for v in (os.environ.get(nome, padrao) or "").split(",") if v.strip()}


# Dona 31/10: Galvão (chiado demais), Chaves e afins = só participação especial curta, nunca narrador do bloco
PARTICIPACAO_PADRAO = "galvao_bueno,chaves,chaves_chapolin,chapolin_colorado,seu_madruga,chiquinha,pica_pau,gretchen"
# graves demais pra narrar (Kratos) — nunca narram o longo
PROIBIDAS_PADRAO = "kratos_god_of_war_2018,kratos_ascension,patrick_estrela,capitao_nascimento,ei_nerd"


def _separar_vozes(vozes):
    """(principais, especiais). Máx. REVEZ_MAX principais (trocas ~4-6, nunca >10) e 2 participações especiais."""
    esp_set = _lista_env("ANIME_PARTICIPACAO", PARTICIPACAO_PADRAO)
    proib = _lista_env("ANIME_NARRA_PROIBIDA", PROIBIDAS_PADRAO)
    vozes = [v for v in dict.fromkeys(vozes) if v not in proib] or list(vozes[:1])
    principais = [v for v in vozes if v not in esp_set][:int(os.environ.get("REVEZ_MAX", "5") or 5)]
    especiais = [v for v in vozes if v in esp_set][:2]
    if not principais:  # só sobrou especial: 1 narra (nunca o Galvão, chiado) e as outras ficam fora
        principais, especiais = sorted(vozes, key=lambda v: v == "galvao_bueno")[:1], []
    return principais, especiais


def _janelas_especiais(n, ini_b, especiais, tam):
    """[(início, fim, voz)] de cada participação especial: no meio de um bloco principal (longe das trocas), na 2ª
    metade do vídeo, espalhadas."""
    out = []
    for j, voz in enumerate(especiais):
        alvo = int(n * (0.5 + 0.35 * (j + 1) / (len(especiais) + 1)))
        if any(abs(alvo - i) < tam + 3 for i in ini_b[1:]):
            alvo = min(n - tam - 3, alvo + 2 * tam + 6)
        if 3 <= alvo and alvo + tam <= n - 3 and all(abs(alvo - a) > 2 * tam for a, _, _ in out):
            out.append((alvo, alvo + tam, voz))
    return out


def revezar(lines, vozes):
    """(linhas, dono de cada linha). Blocos seguidos dos narradores principais (o 1º com ≥35% do vídeo,
    _inicios_blocos) + participações especiais curtas (REVEZ_ESPECIAL_LINHAS=3 frases) que entram e saem no meio de
    um bloco; cada trecho no jeito do narrador dele e, na troca, a cena de passagem."""
    n = len(lines)
    vozes, especiais = _separar_vozes(vozes)
    k = len(vozes)
    ini_b = _inicios_blocos(n, k)
    fim_b = ini_b[1:] + [n]
    dono = [None] * n
    for b in range(k):
        for i in range(ini_b[b], fim_b[b]):
            dono[i] = vozes[b]
    janelas = _janelas_especiais(n, ini_b, especiais, int(os.environ.get("REVEZ_ESPECIAL_LINHAS", "3") or 3))
    for a, z, voz in janelas:
        for i in range(a, z):
            dono[i] = voz
    logging.info(f"[revezamento] principais={vozes} blocos={ini_b} especiais={[(a, z, v) for a, z, v in janelas]}")
    novas = list(lines)
    i = 0
    while i < n:  # cada trecho seguido do mesmo dono no jeito dele
        z = i
        while z < n and dono[z] == dono[i]:
            z += 1
        novas[i:z] = _no_jeito(dono[i], novas[i:z])
        i = z
    # 27/10: a IA soltou "caralho" numa passagem (Dragon/KwdN) mesmo com "SEM palavrão" no prompt — filtro de verdade
    try:
        from viralizador import anti_ban
    except Exception:  # noqa: BLE001
        def anti_ban(t):
            return t
    novas = [anti_ban(t) for t in novas]
    trocas = [i for i in range(1, n) if dono[i] != dono[i - 1]]
    for b, i in enumerate(trocas, 1):
        ini_a = max([0] + [t for t in trocas if t < i])
        fim_d = min([n] + [t for t in trocas if t > i])
        sai, entra = _passagem(dono[i - 1], dono[i], novas[ini_a:i], novas[i:fim_d], b)
        sai, entra = anti_ban(sai), anti_ban(entra)
        if sai:
            novas[i - 1] = f"{novas[i - 1]} {sai}"
        novas[i] = f"{entra} {novas[i]}"
        logging.info(f"[revezamento] {nome_voz(dono[i - 1])} -> {nome_voz(dono[i])}: '{sai}' / '{entra}'")
    return novas, dono


def preparar_revezamento(lines, dono, audio_dir, impactos):
    """Cada voz narra o bloco dela (o Applio troca de modelo entre os blocos). Falhou uma = levanta (como o solo)."""
    antes = os.environ.get("VOZ_CLONADA")
    try:
        for voz in dict.fromkeys(dono):
            os.environ["VOZ_CLONADA"] = voz
            preparar_clone(lines, audio_dir, impactos, so={i for i, d in enumerate(dono) if d == voz})
    finally:
        if antes is not None:
            os.environ["VOZ_CLONADA"] = antes


def narrate(text, out_wav, indice=None, impactos=None, total=None):
    """Gera (ou reusa) a narração de uma frase.

    Retorna o Path do .wav em caso de sucesso, ou None se o TTS falhar.
    Cache: se out_wav já existe, retorna direto sem chamar o TTS.

    Duas camadas anti-ban: o texto ja passa por anime_script.anti_ban() antes
    de chegar aqui, mas esta funcao aplica mais uma vez por seguranca.

    indice/impactos/total: posição da frase no vídeo e as frases de impacto — a curva de locutor
    (narracao_curva, do hipercool, 17/10): acelera e sobe chegando no impacto, respira depois.
    Sem indice, a voz sai plana como antes.
    """
    out_wav = Path(out_wav)

    if out_wav.exists() and out_wav.stat().st_size > 500:
        return out_wav

    # ── SEGUNDA CAMADA anti-ban: garante que nenhum termo de risco chegue ao TTS ──
    safe_text = _pronuncia(viralizador.anti_ban(text))
    if os.environ.get("VIRAL_SLANG") == "1":
        safe_text = viralizador.viralizar(safe_text)

    rate = pitch = None
    ganho, cauda = 0.0, None
    if indice is not None and narracao_curva.ligado():
        rate, pitch, ganho, cauda = narracao_curva.prosodia(safe_text, indice, impactos, total)
    ok = edge_tts_engine.speak(safe_text, voice=NARRATOR_VOICE,
                               out_wav=str(out_wav), persona="Narrador", rate=rate, pitch=pitch)
    if not ok:
        logging.error(f"[anime_tts] TTS falhou: {text[:60]!r}")
        return None
    if cauda is not None:
        narracao_curva.pos_processar(out_wav, ganho, cauda)
        narracao_curva.humanizar(out_wav, safe_text, indice, impactos, total)
        logging.info(f"[curva] frase {indice}: {rate} {pitch} {ganho:+.1f} dB")

    return out_wav
