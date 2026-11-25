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
import re
import shutil
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
    # 22/11 dona (vídeo misto): "debaixo do braço" saiu "brasonom" no S2-Pro — "rasso" força o som "bra-sso"
    (re.compile(r"\b([Bb])ra[çc]o(s?)\b"), r"\1rasso\2"),
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


MISTURA_TETO_S = float(os.environ.get("ANIME_MISTURA_TETO_S", "50"))  # máx. de fala seguida na mesma base
_SEGUIDA = {"base": None, "s": 0.0}
PIPER_OK = Path(r"D:\hipercool-materiais\models\piper\pt_BR-cadu-medium.onnx")


def _voz_modo():
    """Modo da voz deste vídeo: VOZ_MODO manda; senão o padrão da máquina (18/11): "kitten_tudo" onde o Kitten 2 está
    pronto (GPU do Kaggle: KITTEN_NUVEM=1 + tom_4_kitten do narrador), senão "p3" (Piper instalado) e, por último,
    "p1". Nunca volta à base única sozinho."""
    if os.environ.get("ANIME_MISTURA") == "0":
        return "p0"
    m = (os.environ.get("VOZ_MODO") or ("kitten_tudo" if _kitten_pronto() else "p3")).strip().lower()
    if m == "kitten_tudo" and not (_kitten_pronto() and clone_ligado()):
        m = "p3"
    if m == "p3" and not (_piper_pronto() and clone_ligado()):
        return "p1"
    return m


def _kitten_pronto():
    """18/11 (dona: "vamos começar com o padrão"): Kitten 2 com a voz pronta "Portuguese", só onde o kaggle_trabalhador
    montou o venv dele (GPU) e ligou KITTEN_NUVEM=1, e com o tom do clone do narrador já calculado (tom_4_kitten.txt,
    sobe com a voz). Sem GPU o Kitten leva ~30 min por frase: nos PCs nunca."""
    voz = os.environ.get("VOZ_CLONADA")
    if os.name == "nt" or os.environ.get("KITTEN_NUVEM") != "1" or not voz:
        return False
    return (VOZES_DIR / Path(voz).name / "tom_4_kitten.txt").exists()


_PIPER_CACHE = {}


def _piper_pronto():
    voz = os.environ.get("VOZ_CLONADA")
    if not voz:
        return False
    voz = Path(voz).name
    if os.name != "nt":
        # 18/11: nuvem (Kaggle) e STI — o voz_clonada_nuvem gera o Piper; precisa do modelo no pacote, do tom do
        # narrador já calculado (tom_3_piper.txt, sobe junto com a voz) e do pacote piper no Python do clone
        # mesmo caminho que o sitecustomize dá ao D:\ (Kaggle: /kaggle/working/raiz/D; STI: RAIZ_WIN=$HOME -> ~/D)
        modelo = Path(os.environ.get("RAIZ_WIN", "/kaggle/working/raiz")) / "D/hipercool-materiais/models/piper/pt_BR-cadu-medium.onnx"
        tom = VOZES_DIR / voz / "tom_3_piper.txt"
        if not (modelo.exists() and tom.exists()):
            return False
        py = os.environ.get("VOZES_PY_NUVEM") or sys.executable
        if py not in _PIPER_CACHE:
            try:
                _PIPER_CACHE[py] = subprocess.run([py, "-c", "import piper"], capture_output=True,
                                                  timeout=60).returncode == 0
            except Exception:  # noqa: BLE001
                _PIPER_CACHE[py] = False
        return _PIPER_CACHE[py]
    base_amostra = Path(r"D:\hipercool-materiais\amostras_voz\2026-10-18_vozes_clonadas\_bases\3_piper.wav")
    return PIPER_OK.exists() and base_amostra.exists() and (VOZES_DIR / voz / f"{voz}.pth").exists()


def _base_p3(texto, indice, impactos, total):
    """Revezamento das 3 bases rápidas (teste de ouvido 17-18/11: a v4/P2 com Kokoro, Francisca e Piper ganhou da
    base única). Kokoro na subida pro clímax e nos impactos (o "gol"); fora disso Francisca e Piper revezam por
    VIRADA: a base só muda depois de MISTURA_TETO_S de fala seguida (padrão 50 s; no Short, ~1 troca), e a ordem
    da próxima é fixa por hash do texto (refazer dá o mesmo áudio). Gancho (frase 0) = Kokoro."""
    import hashlib
    if indice == 0:
        _SEGUIDA.update(base=None, s=0.0, calma=None)
    sobe = indice == 0 or indice in (impactos or []) or narracao_curva.deltas(texto, indice, impactos, total)[0] >= 8
    dur = len(texto.split()) / 2.6
    if sobe:
        base = "kokoro"
    else:
        calma = _SEGUIDA.get("calma")
        if calma is None:
            calma = "francisca" if int(hashlib.md5(texto.encode("utf-8")).hexdigest(), 16) % 2 else "piper"
        elif _SEGUIDA["base"] == calma and _SEGUIDA["s"] >= MISTURA_TETO_S:
            calma = "piper" if calma == "francisca" else "francisca"
        _SEGUIDA["calma"] = calma
        base = calma
    _SEGUIDA["s"] = _SEGUIDA["s"] + dur if base == _SEGUIDA["base"] else dur
    _SEGUIDA["base"] = base
    return base


def base_da_frase(modo, texto, indice, impactos, total):
    """misto: Kokoro (emoção, acelerado) na abertura e chegando nos impactos (a curva sobe 8%+), Francisca (pronúncia)
    no resto — mesmo timbre, ritmo que muda como o de um narrador humano.
    15/11 (dona + revisão do outro agente: dos últimos 400 vídeos só 6 misturaram; no misto a Francisca ficava 86% da
    fala e até 33,7 min seguidos): com ANIME_MISTURA=1 todo vídeo mistura, e nenhuma base passa de MISTURA_TETO_S
    seguidos — passou, a próxima frase vai pra outra base. Sem a chave = exatamente como antes."""
    # 18/11 dona (teste de ouvido P0..P5): o p0 (uma base no vídeo inteiro) sai de cena. Modos de voz (VOZ_MODO):
    #   "p3" (padrão sem GPU) = revezamento Kokoro / Francisca / Piper, troca na virada (teto de tempo), Kokoro na
    #       subida pro clímax; "kitten_tudo" (só onde há GPU) e o "p3" com Kitten ficam pro lado da nuvem;
    #   "p1" = o misto de antes (Kokoro no gancho/subidas, Francisca no resto) — reserva se a produção apertar.
    #   VOZ_MODO=p0 (ou ANIME_MISTURA=0) volta à base única sorteada por vídeo.
    vm = _voz_modo()
    if vm == "kitten_tudo":
        return "kitten"
    if vm == "p3":
        return _base_p3(texto, indice, impactos, total)
    if vm == "p1":
        modo = "misto"
    if os.environ.get("ANIME_MISTURA") == "1":
        modo = "misto"
    if modo != "misto":
        return modo
    base = "kokoro" if indice == 0 or narracao_curva.deltas(texto, indice, impactos, total)[0] >= 8 else "francisca"
    if os.environ.get("ANIME_MISTURA") == "1":
        if indice == 0:
            _SEGUIDA.update(base=None, s=0.0)
        if base == _SEGUIDA["base"] and _SEGUIDA["s"] >= MISTURA_TETO_S:
            base = "kokoro" if base == "francisca" else "francisca"
        dur = len(texto.split()) / 2.6  # ~2,6 palavras/s (mesma conta do _duracao_sa)
        _SEGUIDA["s"] = _SEGUIDA["s"] + dur if base == _SEGUIDA["base"] else dur
        _SEGUIDA["base"] = base
    return base


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
    # 18/11: o Piper (3ª base do p3) não tem medida própria no perfil do narrador — usa a do Kokoro (as duas são
    # bases geradas no lote, com velocidade em vez do "rate" do edge, e o mesmo tom natural ~130 Hz)
    perfil_base = "kokoro" if base in ("piper", "kitten") else base
    dr, dp, dg, _cauda = narracao_curva.deltas(texto, indice, impactos, total)
    dr2 = dr * a["curva_rate"]
    cauda = a["cauda_impacto"] if indice in (impactos or []) else a["cauda"]
    if total is not None and indice == total - 1:
        cauda = max(cauda, 1.5)
    ruido = (int(hashlib.md5(texto.encode("utf-8")).hexdigest(), 16) % 5 - 2) / 4
    tom_extra = int(round(max(-2.0, min(2.0, (dr / narracao_curva.PICO_RATE + ruido) * a["tom_extra_st"]))))
    extra = {"tom_extra": tom_extra, "f0_escala": a[perfil_base]["f0_escala"], "eq": a[perfil_base]["eq"]}
    v = narracao_curva.variacao(chave, indice, texto, impactos, total)
    extra["index_rate"] = v["index_rate"]
    extra["protect"] = v["protect"]
    extra["volume_envelope"] = v["volume_envelope"]
    if a[perfil_base].get("final_st"):
        extra["final_st"] = round(a[perfil_base]["final_st"] * v["final_mult"], 2)
    # 29/10 teste T9 (Fable; dona: "quero os vídeos falando mais rápido, um louco como o parceiro kaijime, mas pode
    # ficar ruim em alguns — gera variante e vai testando"): CORTES_FALA_DELTA = pontos % a mais na velocidade da fala
    # (B = +15); vazio/0 = como sempre. Vale para o clone (Edge rate e Kokoro vel), nunca para a voz Edge pura.
    try:
        delta_fala = float(os.environ.get("CORTES_FALA_DELTA") or 0)
    except ValueError:
        delta_fala = 0.0
    if base in ("kokoro", "piper", "kitten"):
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
    tag = wav.with_name(wav.stem + ".pad_ok")
    if tag.exists():
        return
    tmp = wav.with_name(wav.stem + ".pad.wav")
    flags = 0x08000000 if os.name == "nt" else 0
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", "apad=pad_dur=0.4", str(tmp)],
                       check=True, capture_output=True, timeout=30, creationflags=flags)
        for tentativa in range(3):
            try:
                tmp.replace(wav)
                break
            except OSError:
                if tentativa == 2:
                    raise
                time.sleep(0.1)
        try:
            tag.write_text("1", encoding="utf-8")
        except OSError:
            pass
        logging.info(f"[anime_tts] cauda protegida no bruto: {wav.name} (+0.4s)")
    except Exception as e:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        logging.warning(f"[anime_tts] proteger cauda bruto falhou em {wav.name} ({e})")


def _aplicar_margem_final(wav, margem=None, fade=0.5):
    """Garante margem (padding) com fade-out no áudio da última frase (fechamento/encerramento).
    Evita truncamento do último fonema, permite Whisper transcrever a palavra inteira
    e mantém movimento (Ken Burns) do último painel até o fim do vídeo."""
    wav = Path(wav)
    if not wav.exists() or wav.stat().st_size < 500:
        return
    tag = wav.with_name(wav.stem + ".margem_ok")
    if tag.exists() and tag.stat().st_mtime >= wav.stat().st_mtime:
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
        if r.returncode != 0 or not r.stdout.strip():
            logging.warning(f"[anime_tts] ffprobe falhou em {wav.name}: rc={r.returncode}")
            return
        dur = float(r.stdout.strip().splitlines()[0])
        r_ch = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=channels", "-of", "csv=p=0", str(wav)],
                              capture_output=True, text=True, timeout=30, creationflags=flags)
        ch = int(r_ch.stdout.strip().splitlines()[0]) if r_ch.returncode == 0 and r_ch.stdout.strip() else 1
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[anime_tts] ffprobe falhou em {wav.name} ({e})")
        return
    fade_dur = min(fade, margem / 2)
    fade_start = max(0.0, dur + margem - fade_dur)
    layout = "stereo" if ch == 2 else "mono"
    fmt = f"aformat=sample_fmts=s16:sample_rates=44100:channel_layouts={layout}"
    filtros = f"{fmt},apad=pad_dur={margem:.3f},afade=t=out:st={fade_start:.3f}:d={fade_dur:.3f}"
    tmp = wav.with_name(wav.stem + ".margem.wav")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", filtros, "-c:a", "pcm_s16le", str(tmp)],
                       check=True, capture_output=True, timeout=60, creationflags=flags)
        for tentativa in range(3):
            try:
                tmp.replace(wav)
                break
            except OSError:
                if tentativa == 2:
                    raise
                time.sleep(0.1)
        try:
            tag.write_text("1", encoding="utf-8")
        except OSError:
            pass
        logging.info(f"[anime_tts] margem final aplicada em {wav.name}: +{margem:.1f}s (fade {fade_dur:.1f}s, total {dur + margem:.1f}s, {layout})")
    except Exception as e:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        logging.warning(f"[anime_tts] margem final falhou em {wav.name} ({e})")


aplicar_margem_final = _aplicar_margem_final
proteger_cauda_bruto = _proteger_cauda_bruto


def motor_antigo():
    """20/11 dona: "não descartar como era feita a narração antes do novo motor — ela era boa, deu trabalho pra
    ajustar; a nova se imagina ficar melhor mas não é certeza, então deve ser versionado; se não der certo, é só
    voltar ao motor antigo". MOTOR_VOZ=antigo (variável) OU config/motor_voz.json {"motor": "antigo"} desliga TODO o
    Fish (Kaggle, site, sub-vozes, gol, S do respeito) e a narração volta ao motor anterior (Kitten 2/RVC na GPU, p3
    com as técnicas nos PCs) — o caminho antigo continua inteiro no código. Versões guardadas em
    producao\\versoes_motor_voz\\ (v1 = antes do Fish, commit 1370e236 de 18/11; v2 = Fish 20/11)."""
    v = (os.environ.get("MOTOR_VOZ") or "").strip().lower()
    if not v:
        try:
            v = str(json.loads((Path(__file__).resolve().parent.parent / "config" / "motor_voz.json")
                               .read_text(encoding="utf-8")).get("motor", "")).strip().lower()
        except (OSError, ValueError):
            v = ""
    return v in ("antigo", "rvc", "p3", "kitten", "v1")


def _fish_nuvem_pronto():
    """19/11 dona ("a partir de agora o Fish vai ser o padrão; os longos são feitos no Kaggle"): Fish Speech na GPU
    do Kaggle. Só onde o kaggle_trabalhador montou o ambiente (FISH_NUVEM=1 + FISH_VENV) e o narrador tem trecho
    ORIGINAL de referência (referencia_fish.wav/.txt na pasta da voz). Sem isso = segue Kitten/p3 como antes."""
    if motor_antigo():
        return False
    return _pasta_fish() is not None


def _pasta_fish(voz=None):
    """19/11 dona: "no Kaggle tem que ser sempre o motor novo; p3 só fora do Kaggle e sem crédito no site". Pasta com
    a referência do Fish: a da própria voz; sem ela (ou sem voz escolhida) a do nicho — narrador do Chris, Neymar no
    esporte — para o Short NUNCA cair no Kitten/p3 no Kaggle. None = fora do Kaggle / Fish não instalado."""
    if os.name == "nt" or os.environ.get("FISH_NUVEM") != "1" or _OUTRA:
        return None
    voz = voz if voz is not None else (os.environ.get("VOZ_CLONADA") or "")
    nicho = (os.environ.get("NICHO_CLONE") or os.environ.get("PARCEIRO_TIPO") or "").lower()
    reserva = "neymar" if nicho in ("esportes", "futebol", "esporte") else "narrador_chris"
    for nome in ([Path(voz).name] if voz else []) + [reserva, "narrador_chris"]:
        pv = VOZES_DIR / nome
        if (pv / "referencia_fish.wav").exists() and (pv / "referencia_fish.txt").exists():
            return pv
    return None


def _acabamento_fish(out, voz):
    """19/11 (análise das técnicas p/ o Fish): o Fish já vem com ritmo, respiração e entonação reais do narrador, então
    humanizar/curva/climas/RVC ficam FORA (soam artificiais por cima ou tiram a voz do narrador). Entram só:
    pos_processar (nivela -20 LUFS e corta cauda de silêncio — sem isso as frases mudam de volume) e o efeito próprio
    da voz (cadastro do narrador). O sidecar .words.json não muda de tempo (pos_processar só corta o FIM)."""
    try:
        narracao_curva.pos_processar(out, 0.0)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[fish] nivelar {Path(out).name} falhou ({e})")
    try:
        anime_formatos.aplicar_efeito_voz(voz, out)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[fish] efeito da voz em {Path(out).name} falhou ({e})")
    try:
        if os.environ.get("FISH_ACELERA_NO_CODIGO") != "1":  # 20/11: o tom mexido por cima soma com a aceleração
            _fim_que_sobe(out, voz)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[fish] fim que sobe em {Path(out).name} falhou ({e})")


# 20/11 dona: "o motor antigo era mais agudo nos finais e por isso parecia mais com o original" (Mike, Momo). Medido:
# Mike real sobe o fim em 50-67% das frases; Fish base 28%; subindo +1,5 st nos 0,42 s antes de cada pausa -> 50%.
# Por narrador em FISH_FIM_ST (padrão abaixo) ou "fish_fim_st" no personagem.json da voz. FISH_FIM=0 desliga.
FISH_FIM_ST = {"mike": 1.5, "momo": 0.8, "kkvirjao": 1.0}


def _fim_que_sobe(wav, voz):
    if os.environ.get("FISH_FIM", "1") == "0" or not voz:
        return
    nome = Path(voz).name
    st = FISH_FIM_ST.get(nome)
    try:
        st = json.loads((VOZES_DIR / nome / "personagem.json").read_text(encoding="utf-8")).get("fish_fim_st", st)
    except (OSError, ValueError):
        pass
    if not st:
        return
    wav = Path(wav)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                             capture_output=True, text=True).stdout or 0)
    if d < 1.2:
        return
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(wav), "-af", "silencedetect=noise=-35dB:d=0.18", "-f", "null",
                        "-"], capture_output=True, text=True)
    pausas = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    fins = [t for t in pausas if t > 0.8] + [d]
    k = 2 ** (float(st) / 12)
    cortes, ult = [], 0.0
    for t in fins:
        a = max(ult, t - 0.42)
        if a - ult > 0.05:
            cortes.append((ult, a, False))
        if t - a > 0.1:
            cortes.append((a, t, True))
        ult = t
    if d - ult > 0.05:
        cortes.append((ult, d, False))
    if not any(c[2] for c in cortes):
        return
    fc = ""
    for n, (a, b, sobe) in enumerate(cortes):
        fc += f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS"
        if sobe:
            fc += f",asetrate=44100*{k:.5f},aresample=44100,atempo={1 / k:.5f}"
        fc += f"[c{n}];"
    fc += "".join(f"[c{n}]" for n in range(len(cortes))) + f"concat=n={len(cortes)}:v=0:a=1[o]"
    tmp = wav.with_name(wav.stem + ".fim.wav")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-filter_complex", fc, "-map", "[o]", "-ar",
                        "44100", "-ac", "2", str(tmp)], capture_output=True)
    if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
        os.replace(tmp, wav)


def _fala_rindo(wav, ini_s, fim_s, st=8.0, risadinha=None):
    """20/11 dona (Mike "personagem", 4-6 s do original): "ele não só ri, ele fala a palavra RINDO — dá uma risadinha
    no 4 s e segue falando 'o prota virou eunuco' rindo e mais agudo; todos fazem isso". Medido no original: risadinha
    314 Hz e a fala rindo 308 Hz contra 132-203 Hz da fala normal (≈ +7 a +9 st), com o tom segurado. Aqui: a risadinha
    REAL do narrador (risada_real/*.wav ou o arquivo dado) entra antes e o trecho [ini_s, fim_s] sobe `st` semitons
    (mesma duração). Usado na palavra-chave da piada sobre desgraça/vergonha alheia. FISH_FALA_RINDO=0 desliga."""
    if os.environ.get("FISH_FALA_RINDO", "1") == "0":
        return False
    wav = Path(wav)
    k = 2 ** (st / 12)
    entradas = ["-i", str(wav)]
    fc = (f"[0:a]atrim=0:{ini_s:.3f},asetpts=PTS-STARTPTS[a];"
          f"[0:a]atrim={ini_s:.3f}:{fim_s:.3f},asetpts=PTS-STARTPTS,asetrate=44100*{k:.5f},aresample=44100,"
          f"atempo={1 / k:.5f},vibrato=f=6:d=0.15[b];"
          f"[0:a]atrim={fim_s:.3f},asetpts=PTS-STARTPTS[c];")
    if risadinha and Path(risadinha).exists():
        entradas += ["-i", str(risadinha)]
        fc += "[1:a]aresample=44100,aformat=channel_layouts=mono,afade=t=out:st=0.4:d=0.15[r];"
        fc += "[a][r][b][c]concat=n=4:v=0:a=1[o]"
    else:
        fc += "[a][b][c]concat=n=3:v=0:a=1[o]"
    tmp = wav.with_name(wav.stem + ".rindo.wav")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", fc, "-map", "[o]", "-ar", "44100",
                        "-ac", "2", str(tmp)], capture_output=True)
    if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
        os.replace(tmp, wav)
        return True
    return False


# fecho grosso por narrador (semitons no último pedaço): Mike = -4,5 (o exemplo que a dona aprovou); o resto -2,0
# 20/11 noite (dona, Q do Mike): "na hora do 'só olhando pra mim' ele engrossou a voz tanto que ficou ROBÓTICA" e
# "o 'levanta, menino'" — -4,5 st por cima do RVC passa do ponto. -2,5 e só no FIM (última palavra).
FECHO_GROSSO_ST = {"mike": -2.5}


def _desfecho_gol(wav, tipo, voz=None):
    """20/11 dona (Mike "metralhadora"): as boas "terminaram AGUDAS e rápidas no final" (gol) ou "lentas no final mas
    ENGROSSARAM a voz — o Mike faz isso, é como a falha do gol"; reprovou as que ficam "iguais do começo ao fim".
    Medido nas aprovadas: gol +2 a +4,5 st no fim; falha -1,3 a -1,7 st (voz mais grossa); +6,7 st foi exagero.
    20/11 (Mike "risada" 12 e "tensão"): "a finalização mais grossa — o Mike faz muito, temos que usar muito pra
    finalização de frases"; "fica bom o final da frase ser lento, cada passo dele no final, e até engrossar a voz".
    Medido no exemplo dela: -4,5 st no fim. tipo "grosso" = fecho grosso do narrador (tensão/falha).
    Muda o tom só do ÚLTIMO pedaço (último 1 s, depois da última pausa) — o resto da frase fica igual."""
    # 20/11 (teste gol4, KkVirjão): o "nãooo" da falha "ficou estranho, parecendo um carro acelerando" — mudar o tom
    # do fim em quem NÃO engrossa a voz (KkVirjão/Momo) soa artificial. Falha muda o tom só em quem tem fecho grosso
    # medido (Mike); nos outros fica só a fala natural do Fish.
    nome = Path(voz).name if voz else ""
    if tipo in ("falha", "grosso") and nome not in FECHO_GROSSO_ST:
        return
    grosso = FECHO_GROSSO_ST.get(nome, -2.0)
    # 20/11 dona: "um pequeno troço na hora da luta, parecendo uma FITA quando acelerava muito" — era o tom +3 st do
    # gol (asetrate) por cima da aceleração. O gol agora é só velocidade (FISH_GOL_TOM=1 volta o tom).
    st = {"gol": 3.0 if os.environ.get("FISH_GOL_TOM") == "1" else None, "falha": grosso, "grosso": grosso}.get(tipo)
    if st is None or os.environ.get("FISH_GOL", "1") == "0":
        return
    # 20/11 noite (Q3 do Mike: "o 'levanta, menino' engrossou a voz muito, ainda tem o robô no fim da palavra"):
    # no Kitten o tom já passou pelo RVC — engrossar por cima soa robótico. Lá o fecho é só a última palavra mais
    # lenta (o RVC recebe o fim mais grave pelo final_st do tipo, sem asetrate).
    if _SUB_KITTEN.get("_ligado"):
        st = 0.0
    lento = 0.92 if tipo in ("falha", "grosso") else 1.0  # o fecho grosso vem também mais lento ("cada passo dele")
    wav = Path(wav)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                             capture_output=True, text=True).stdout or 0)
    if d < 1.0:
        return
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(wav), "-af", "silencedetect=noise=-35dB:d=0.18", "-f", "null",
                        "-"], capture_output=True, text=True)
    pausas = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr) if float(x) < d - 0.4]
    # 20/11 noite: o fecho grosso só na ÚLTIMA palavra (~0,6 s); o gol/falha seguem no último trecho (~1 s)
    janela = 0.6 if tipo in ("grosso", "falha") else 1.1
    ini = max([d - janela] + [p for p in pausas if p > d - 2.0])
    k = 2 ** (st / 12)
    fc = (f"[0:a]atrim=0:{ini:.3f},asetpts=PTS-STARTPTS[a];"
          f"[0:a]atrim={ini:.3f},asetpts=PTS-STARTPTS,asetrate=44100*{k:.5f},aresample=44100,"
          f"atempo={lento / k:.5f}[b];"
          f"[a][b]acrossfade=d=0.05[o]")
    tmp = wav.with_name(wav.stem + ".desf.wav")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-filter_complex", fc, "-map", "[o]", "-ar",
                        "44100", "-ac", "2", str(tmp)], capture_output=True)
    if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
        os.replace(tmp, wav)


_SUB_RISO =re.compile(r"(?i)\b(k{3,}|ha(ha)+|he(he)+|rs(rs)+|risos?|riu|rindo|gargalh\w*)\b")
_SUB_MULHER = re.compile(r"(?i)\b(peito\w*|gostos\w*|del[ií]cia|bunda|seio\w*|sexy|safad\w*|tes[aã]o|novinha\w*|"
                         r"gatinha|maravilhosa|respeito|mina\w*)\b")
# 20/11 dona (ouvindo kkvirjao/risada 4_SUB_risada_mais_solta): "essas com grito no final subindo são muito boas,
# ele faz isso quando está chateado, tipo 'eu não aguento isso' — tem que usar". Era a sub-voz "_risada" (que na
# verdade não tinha risada): virou "_irritado".
_SUB_IRRITADO = re.compile(r"(?i)(n[aã]o aguento|que [oó]dio|absurdo|rid[ií]culo|pelo amor de deus|"
                           r"que palha[cç]ada|t[aá] de brincadeira|n[aã]o [eé] poss[ií]vel|que raiva|"
                           # 20/11: "chega" sozinho pegava "chega em casa"/"chega a professora" (virava irritado)
                           r"vai se \w+|cansei|chega[!.]|\baf+\b|!!)")
_SUB_PERSON = re.compile(r"(?i)(\b(ele|ela) (fala|disse|diz|grita|responde|pergunta)\b.*[:\"“]|[\"“].{6,}[\"”])")
# ordem de reserva: sub-voz que a voz não tem -> a próxima da lista -> normal
_SUB_RESERVA = {"_irritado": ["_agudo", "_piada"], "_risada": ["_irritado", "_piada", "_agudo"], "_mulher": ["_piada", "_agudo"], "_personagem": ["_agudo", "_piada"],
                "_metralhadora": ["_agudo", "_tensao"], "_piada": ["_agudo"], "_agudo": ["_piada"],
                "_tensao": []}


def _impactos_do(audio_dir):
    """Frases de impacto do vídeo (anime_segments grava _impactos.json ao lado da fonte = pasta acima do audio_cache)."""
    for p in (Path(audio_dir).parent / "_impactos.json", Path(audio_dir) / "_impactos.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            return d.get("impactos", d) if isinstance(d, dict) else d
        except (OSError, ValueError):
            continue
    return []


_LENTA = [
    # (fator, padrão) — o 1º que bater manda
    (0.88, re.compile(r"(?i)(você acha mesmo|acha mesmo que|ah,? claro|claro que (não|sim)|parabéns|que (gênio|esperto|"
                      r"inteligente)|olha só quem|grande coisa|nossa,? que medo|tá bom,? então|uau,? que|sério mesmo)")),
    (0.90, re.compile(r"(?i)\b(ele|ela) (fala|diz|disse|responde|grita|pergunta)\b[^.]*[:\"“]")),  # fala do personagem
    (0.90, re.compile(r"(?i)(coitad\w*|tadinh\w*|pobre (coitad|garot|menin)|que dó|que pena)")),     # pena/lamento
    # 20/11 dona (KkVirjão "tensão"): "tensão NÃO pode ser devagar, exceto quando tiver uma piada (um 'né')" — aprovou
    # as soltas/rápidas e não as contidas. A regra de suspense (-8%) saiu; tensão segue a curva (acelera).
    (0.93, re.compile(r"(?i)^(pois é|e foi isso|simples assim|é isso aí|fazer o quê)\b")),            # constatação seca
    # 20/11 dona (KkVirjão "piada"): "nem aprovei todos pois todos ficaram bons — a piada combina com a parte dela ser
    # devagar, seja onde for". Piada/comentário/duplo sentido = mais devagar
    (0.90, re.compile(r"(?i)(com todo res+[\s.\-…]*peito|com todo respeito|macet\w*|do jeito gostoso|eu faria esse|"
                      r"você faria|não é isso que (vocês|cês) (tão|estão) pensando|em batalha,? (gente|galera)|"
                      r"particulares?,? hein|só olhando o)")),                                          # duplo sentido
    (0.92, re.compile(r"(?i)\b(mano|rapaz|meu compadre|cara|gente|galera),? (olha|imagina|sério|pelo amor)|"
                      r"\b(kkk|rsrs|haha)|\b(mentira|zoeira|brincadeira)\b|tá\?$|né\?$")),                 # piada/comentário
]


def _frase_lenta(texto):
    """Fator < 1 se a frase pede fala mais lenta (deboche, fala de personagem, pena, suspense, constatação)."""
    for f, p in _LENTA:
        if p.search(texto or ""):
            return f
    return None


_GOL_CTX = {}  # {i: ("sobe"|"gol"|"falha", posição, tamanho da sequência)} — preenchido por _marcar_gol
_GOL_SIM = re.compile(r"(?i)\b(acert\w*|derrot\w*|venc\w*|conseg\w*|finalmente|destr[oó]i\w*|nocaute\w*|"
                      r"esmag\w*|ganh\w*|isso[!,]|toma[!,]|vitória|matou o|acabou com o)\b")
_GOL_NAO = re.compile(r"(?i)\b(é atingid\w*|foi atingid\w*|morr\w*|caiu|cai no chão|falh\w*|perd\w*|errou|"
                      r"sangr\w*|não,? não|derrubad\w*|ferid\w*|esfaquead\w*|desmai\w*)\b")


def _marcar_gol(lines, climas):
    """Acha as sequências de tensão/ação (≥ 3 frases seguidas) e marca a posição de cada frase; a frase depois da
    sequência (ou a última dela) é o desfecho: gol (o bom acerta/vence) ou falha (o bom é atingido/morre)."""
    _GOL_CTX.clear()
    if not climas:
        return
    alvo = {"tensao", "acao", "epico", "vilao", "terror"}
    i, n = 0, len(lines)
    while i < n:
        if climas[i] in alvo:
            j = i
            while j + 1 < n and climas[j + 1] in alvo:
                j += 1
            # 20/11 (teste gol4): a briga inteira virou 1 sequência e o gol do MEIO ("acerta um soco... isso!") se
            # perdeu — desfecho no meio corta a sequência: marca gol/falha ali e a aceleração recomeça depois
            k0 = i
            for k in range(i + 2, j):
                t = _seguro(lines[k])
                tipo = "falha" if _GOL_NAO.search(t) else ("gol" if _GOL_SIM.search(t) else None)
                if tipo and k - k0 >= 2:
                    for m in range(k0, k):
                        _GOL_CTX[m] = ("sobe", m - k0, k - k0 + 1)
                    _GOL_CTX[k] = (tipo, 0, k - k0 + 1)
                    k0 = k + 1
            i = k0
            if j - i + 1 >= 3:
                tam = j - i + 1
                for k in range(i, j + 1):
                    _GOL_CTX[k] = ("sobe", k - i, tam)
                for d in (j, j + 1):  # desfecho: última da sequência ou a seguinte
                    if d < n:
                        t = _seguro(lines[d])
                        if _GOL_NAO.search(t):
                            _GOL_CTX[d] = ("falha", 0, tam)
                            break
                        if _GOL_SIM.search(t):
                            _GOL_CTX[d] = ("gol", 0, tam)
                            break
            i = j + 1
        else:
            i += 1
    # 20/11 (Mike tensão): frase de tensão FORA da corrida pro gol fecha lenta e com a voz engrossando
    for k in range(n):
        t_ = _seguro(lines[k])
        # 20/11 noite (Q do Mike: "só olhando pra mim?" engrossou até ficar robótica): fala de personagem e pergunta
        # não levam o fecho grosso — é a voz DELE fechando a narração, não a do personagem
        if (k not in _GOL_CTX and climas[k] in ("tensao", "terror", "vilao") and not t_.rstrip().endswith("?")
                and not _SUB_PERSON.search(t_)):
            _GOL_CTX[k] = ("grosso", 0, 0)


def _ritmo_fish(wav, voz, texto, i, impactos, n):
    """20/11 dona: "os narradores originais às vezes aceleram e às vezes diminuem — tem que fazer tudo isso no clone";
    "a dublagem antiga era mais dinâmica e rápida (a IA usou várias técnicas pra aproximar do original); as que saíram
    nos longos são lentas". O Fish já vem na velocidade NATURAL do narrador (medido: Momo novo 227 ppm x 221 real),
    então aqui entra só a VARIAÇÃO da curva do locutor (narracao_curva: clímax/impacto acelera, "..."/tensão
    desacelera), na amplitude do narrador (perfil_v2 curva_rate) — sem a base +10% do clone (deixaria rápido demais).
    atempo muda a velocidade sem mudar o tom. FISH_RITMO=0 desliga; FISH_RITMO_ESCALA ajusta a força (padrão 1)."""
    if os.environ.get("FISH_RITMO", "1") == "0":
        return
    try:
        dr, _dp, _dg, _cauda = narracao_curva.deltas(texto, i, impactos or [], n)
    except Exception:  # noqa: BLE001
        return
    escala = float(os.environ.get("FISH_RITMO_ESCALA", "1") or 1)
    try:
        perfil = _perfil_v2(voz) if voz else None
        escala *= float((perfil or {}).get("curva_rate", 1.0))
    except Exception:  # noqa: BLE001
        pass
    fator = max(0.88, min(1.25, 1 + dr * escala / 100))
    # 20/11 dona (KkVirjão "personagem", aprovou de 161 a 310 ppm): "deboche fica bem com palavras lentas; nesse caso
    # as lentas ficaram até melhores que as rápidas — analise quais pra encaixar as lentas". A velocidade depende do
    # CONTEÚDO: deboche/ironia, fala de vilão arrogante, suspense/revelação, pena e constatação seca = MAIS LENTA
    # (até -15%); ação, clímax e desabafo seguem a curva (acelera). Só reprovou a lenta demais (86 ppm) -> piso 0,85.
    lenta = _frase_lenta(texto)
    if lenta:
        # 20/11 (teste gol4, KkVirjão): "teve uma hora que ficou tão lento que pareceu retardado" — o Fish já fala
        # devagar na piada; o lento soma: piso 0,92 na frase toda (o lento de verdade é só no FIM do deboche)
        fator = max(0.92, min(fator, 1.0) * (1 - (1 - lenta) * 0.6))
    # 20/11 dona — ACELERAÇÃO DO GOL: "tensão não pode ser devagar; vão acelerando como um narrador de futebol que vai
    # aproximando a bola do gol, falando mais rápido, mais emocionante; e tem um desfecho pra quando é gol e outro pra
    # quando é falha (Mike: quando o bom acerta comemora; quando o bom é atingido ou morre: 'não, não, galera!', fica
    # triste)". Numa sequência de frases de tensão/ação, cada uma mais rápida que a anterior (até +30%, curva que
    # dispara no fim); no desfecho, comemoração = rápida; falha = cai (mais lenta). FISH_GOL=0 desliga.
    gol = _GOL_CTX.get(i)
    if gol and os.environ.get("FISH_GOL", "1") != "0":
        tipo, k, nseq = gol
        if tipo == "sobe" and not lenta:
            f_ = (k / max(1, nseq - 1)) ** 2
            fator = max(fator, 1.0 + 0.30 * f_)
        elif tipo == "gol":
            fator = max(fator, 1.22)
        elif tipo == "falha":
            fator = min(fator, 0.95)
    if abs(fator - 1) < 0.02:
        return
    wav = Path(wav)
    tmp = wav.with_name(wav.stem + ".ritmo.wav")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", f"atempo={fator:.3f}", str(tmp)],
                       capture_output=True)
    if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
        os.replace(tmp, wav)
        wj = Path(str(wav) + ".words.json")  # tempos das palavras acompanham a nova velocidade
        if wj.exists():
            try:
                ws = json.loads(wj.read_text(encoding="utf-8"))
                wj.write_text(json.dumps([[round(a / fator, 3), round(b / fator, 3), *r_] for a, b, *r_ in ws],
                                         ensure_ascii=False), encoding="utf-8")
            except (OSError, ValueError, TypeError):
                pass


_RISO_TXT = re.compile(r"(?i)(?:\b(?:k{2,}|(?:ha){2,}h?|(?:he){2,}h?|(?:hu){2,}|rs(?:rs)+)\b|[(\[]\s*risos?\s*[)\]])[\s,!.]*")
_LETRA_REPETIDA = re.compile(r"([A-Za-zÀ-ÿ])\1{2,}")


def _texto_fish(t):
    """20/11 dona (ouvindo as amostras): (1) "kkkk" no texto = "risada de robô tentando rir; a nossa risada de verdade
    não é assim" -> o Fish nunca recebe kkk/haha/rsrs (a risada real entra depois, cortada do próprio narrador);
    (2) vogal alongada é humana, mas uma ficou "alongada acima do que um humano faria, ficaria sem ar" -> letra
    repetida no máximo 2x ("nãooooo" -> "nãoo"). Devolve (texto, tinha_risada)."""
    tinha = bool(_RISO_TXT.search(t))
    t = _RISO_TXT.sub("", t)
    t = _LETRA_REPETIDA.sub(lambda m: m.group(1) * 2, t)
    t = _duplo_sentido_fala(t)
    t = _pergunta_ao_publico(t)
    # 20/11 (revisão de defeitos): "..." solto no meio o Fish trata de jeito imprevisível (silêncio longo, sílaba
    # repetida). No Fish a pausa vem do ponto final ("! E vocês..." já dá a pausa)
    t = re.sub(r"\s*(?:\.\.\.|…)\s*(?=[A-ZÀ-Ú])", " ", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" ,")
    return (t or "Olha isso."), tinha


def _pergunta_ao_publico(t):
    """20/11 dona (todas as versões da comparação): "a piada 'vocês fariam' está errada — é mais ou menos assim: 'Eu
    faria esse acordo! ... E vocês, fariam esse acordo?' — não está perguntando nem dando espaço pra pessoa pensar, e a
    afirmação de que ele faria também não está legal". Afirmação dele = exclamação (convicção); pausa ("...") pro
    público pensar; a pergunta repete o objeto ("esse acordo") e fica sozinha no fim. Vale pro Fish e pro Kitten."""
    m = re.search(r"(?i)\b(eu (?:faria|fazia|aceitaria|toparia|pegaria|iria)\b[^.?!,]{0,40}?)\s*[,.]?\s*"
                  r"(?:e |mas )?(você|vocês|cês|tu),?\s*(faria|fariam|aceitaria|aceitariam|toparia|topariam|"
                  r"pegaria|pegariam|iria|iriam)\b[^.?!]{0,30}\?\s*$", t)
    if m:
        afirm = m.group(1).strip()
        obj = re.sub(r"(?i)^eu \w+\s*", "", afirm).strip()  # "esse acordo"
        quem = "vocês" if m.group(2).lower() in ("vocês", "cês") else m.group(2).lower()
        return (t[:m.start()] + afirm[0].upper() + afirm[1:] + "! ... E " + quem + ", " + m.group(3).lower()
                + (" " + obj if obj else "") + "?")
    # pergunta curta pro público no fim, sem a afirmação antes: vira frase própria, com pausa antes
    return re.sub(r"(?i),\s*((?:e |mas )?(?:você|vocês|cês|tu|o senhor|a galera)\b[^.?!,]{0,40}\?)\s*$",
                  lambda m_: "... " + m_.group(1)[0].upper() + m_.group(1)[1:], t)


# 20/11 dona (KkVirjão, sub-voz mulher): "respeito dito normal é só respeito mesmo; mas quando se fala 'ressss-peito'
# com o S alongado ou uma pequena separação do 'res' pro 'peito', está se falando dos peitos dela". O duplo sentido
# está na PRONÚNCIA: só no contexto da piada ("com todo respeito" falando de mulher/corpo), o texto que vai pro Fish
# vira "ressss... peito" (S alongado de propósito + micro-pausa). Fora desse contexto, "respeito" fica normal.
# Exceção ao limite de letra repetida (é proposital e curto). FISH_DUPLO_SENTIDO=0 desliga.
_CTX_CORPO = re.compile(r"(?i)\b(gostos\w*|del[ií]cia|corpo|curvas?|bunda|peit\w*|seio\w*|decote|mulher(ão|aço)?|"
                        r"mina|gata|gatinha|novinha|bonit\w+|linda|maravilhos\w*|sexy|safad\w*|biquíni|academia|"
                        # 20/11: o _seguro troca "gostosa" por "atraente" — o S do respeito nunca disparava (dona:
                        # "o S estendido do respeito está errado em todas as versões")
                        r"atraente\w*|professora|enfermeira|sensual\w*|charmos\w*)\b")
_RESPEITO = re.compile(r"(?i)\b(com (todo|o maior|muito) )?(r)(espeito)\b")


def _duplo_sentido_fala(t):
    """20/11: o texto vai NORMAL pro Fish (a dona reprovou "resss... peito": deixava a frase toda lenta ou abobalhada);
    só marca que a frase tem a piada — o S é esticado DEPOIS no áudio (_esticar_s_respeito).
    20/11 (2): o roteiro escreve "RES-peito"/"RESSS-peito" quando é piada -> o Fish lê "respeito" normal."""
    return _RES_PEITO.sub("respeito", t)


_RES_PEITO = re.compile(r"(?i)res+[\s.\-…]*peito")


_RESPEITO_FEITOS = []  # índices das frases em que o S do respeito já foi esticado neste vídeo


def _tem_respeito_piada(t, i=None):
    """21/11 dona: "o S do respeito está sendo usado excessivamente — só na primeira vez que a personagem aparece".
    Mesmo que o roteiro traga vários "com todo respeito", o S esticado só sai no 1º e depois de no mínimo 150 frases
    do último (proxy de "personagem nova"); os outros ficam "respeito" normal."""
    if not _tem_respeito_piada_base(t, i):
        return False
    if i is not None:
        if _RESPEITO_FEITOS and (i in _RESPEITO_FEITOS):
            return True
        if any(abs(i - j) < 150 for j in _RESPEITO_FEITOS):
            return False
        _RESPEITO_FEITOS.append(i)
    return True


def _tem_respeito_piada_base(t, i=None):
    if os.environ.get("FISH_DUPLO_SENTIDO", "1") == "0":
        return False
    marcado = bool(re.search(r"RES+[\s.\-…]*[Pp]eito", t or ""))  # o roteiro marcou a piada (RES-peito)
    # 23/11 dona: o roteiro pôs "Com todo RESSS-peito" num TAPA — só vale com beleza/corpo/aparência na frase
    _sem_resp = re.sub(r"(?i)res+[\s.\-…]*peito", " ", t or "")  # o "peito" do próprio RES-peito não conta
    if marcado and not (_CTX_CORPO.search(_sem_resp) or re.search(
            r"(?i)\b(bonit|lind|gat[ao]|charm|sexy|vestid|decote|curva|corpo|beleza|maravilh|deus[ao]|musa|"
            r"rainha|figura|ampulheta|elegante|deslumbr)", _sem_resp)):
        marcado = False
    # 23/11: o gatilho visual escolheu esta frase (1ª aparição de mulher bonita) — legenda fica "respeito" normal
    marcado = marcado or (i is not None and str(i) in os.environ.get("RESPEITO_PIADA", "").split(",")
                          and bool(re.search(r"(?i)\bcom todo respeito\b", t or "")))
    if marcado or (bool(_CTX_CORPO.search(t or ""))
                   and bool(re.search(r"(?i)\bcom (todo|o maior|muito) respeito\b", t or ""))):
        return True
    # 20/11: a IMAGEM daquela cena foi marcada sensual (gatilho_visual -> GATILHO_SENSUAL) e a frase tem "respeito"
    # 22/11 dona: "o respeito com S alongado foi usado fora do contexto — é trocadilho pros SEIOS, não respeito de
    # verdade". Pela imagem só vale com "com todo/o maior respeito" (a forma da piada), nunca "respeita"/"respeitar".
    sens = {x for x in os.environ.get("GATILHO_SENSUAL", "").split(",") if x}
    # 23/11 (3ª): a cena sensual agora chega MARCADA (RES-peito, gatilho_visual) — sem marcador não estica
    return (False and i is not None and str(i) in sens and bool(_CTX_CORPO.search(t or ""))
            and bool(re.search(r"(?i)\bcom (todo|o maior|muito) respeito\b", t or "")))


def _esticar_s_respeito(wav, alvo_s=0.45, texto=None, enfase=None):
    """20/11 dona aprovou: "C_S_bem_alongado_0.45s — é isso que precisamos". Frase em velocidade NORMAL; só o S de
    "respeito" (o chiado entre "re" e "peito") é esticado pra ~0,45 s, mantendo o chiado (atempo, sem mudar o resto).
    Acha a palavra pelos tempos do Whisper (.words.json, ou mede aqui) e o S pela energia aguda (> 4 kHz)."""
    try:
        import numpy as np
        wav = Path(wav)
        sr = 44100
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                             capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
        # onde está "respeito": words.json (tempo real das palavras) ou Whisper rápido
        ini = fim = None
        wj = Path(str(wav) + ".words.json")
        palavras = json.loads(wj.read_text(encoding="utf-8")) if wj.exists() else None
        if not palavras:
            try:
                try:
                    from faster_whisper import WhisperModel
                except ImportError:
                    # 20/11 (prova do S: 5 de 6 frases esticaram o S errado — sem Whisper, a posição pelo texto erra):
                    # instala o faster-whisper numa pasta própria (1x por sessão) e tenta de novo
                    alvo = "/tmp/pkgs_whisper" if os.name != "nt" else str(Path(os.environ.get("TEMP", "."))
                                                                             / "pkgs_whisper")
                    if alvo not in sys.path:
                        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--target", alvo,
                                        "faster-whisper"], capture_output=True, timeout=900)
                        sys.path.insert(0, alvo)
                    from faster_whisper import WhisperModel
                dev = "cuda" if os.environ.get("FISH_NUVEM") == "1" else "cpu"
                try:
                    m = WhisperModel("small", device=dev, compute_type="float16" if dev == "cuda" else "int8")
                except Exception:  # noqa: BLE001 — Kaggle sem libcublas: a CPU dá conta de 1 frase
                    m = WhisperModel("small", device="cpu", compute_type="int8")
                # 20/11 (bug achado pela dona: esticou o S do "simplesmente"): a[::2] dava 22 kHz lido como 16 kHz e
                # os tempos saíam 38% atrasados. O Whisper recebe 16 kHz de verdade, convertido pelo ffmpeg.
                raw16 = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "s16le", "-ac", "1", "-ar",
                                        "16000", "-"], capture_output=True).stdout
                a16 = np.frombuffer(raw16, np.int16).astype(np.float32) / 32768.0
                try:
                    segs, _ = m.transcribe(a16, language="pt", word_timestamps=True)
                    palavras = [[w.start, w.end, w.word] for s in segs for w in (s.words or [])]
                except RuntimeError:
                    # 20/11 (v3: "sem Whisper (RuntimeError)"): na GPU do Kaggle o modelo carrega mas a libcublas
                    # falha na hora de transcrever — refaz na CPU (1 frase é rápido)
                    m = WhisperModel("small", device="cpu", compute_type="int8")
                    segs, _ = m.transcribe(a16, language="pt", word_timestamps=True)
                    palavras = [[w.start, w.end, w.word] for s in segs for w in (s.words or [])]
            except Exception as e:  # noqa: BLE001
                logging.info(f"[fish S] sem Whisper ({type(e).__name__}) — acho o 'respeito' pela posição no texto")
                palavras = []
        for p0, p1, w in palavras:
            if re.search(r"(?i)resp", str(w)):
                ini, fim = float(p0), float(p1)
                break
        if ini is None and texto:
            # 20/11 (teste gol4: o "respeito" do KkVirjão saiu SEM o S esticado — no Kaggle não tinha Whisper e a
            # função desistia calada): estima pela posição da palavra no texto (fala sem as pausas) ± 0,6 s
            pos = texto.lower().find("respeit")
            if pos >= 0:
                env = np.abs(a[:len(a) // 256 * 256]).reshape(-1, 256).mean(1)
                ativos = np.where(env > 0.01)[0]
                if len(ativos):
                    t0, t1 = ativos[0] * 256 / sr, ativos[-1] * 256 / sr
                    c = t0 + (t1 - t0) * pos / max(1, len(texto))
                    # janela curta em volta da posição ("re" antes, "peito" depois): o S fica no começo da palavra
                    ini, fim = max(0.0, c - 0.25), min(len(a) / sr, c + 0.45)
        if ini is None:
            logging.info(f"[fish S] {wav.name}: não achei o 'respeito'")
            return False
        seg = a[int(ini * sr):int(fim * sr)]
        hop, win = int(0.005 * sr), int(0.02 * sr)
        hf = []
        for i in range(0, max(0, len(seg) - win), hop):
            fr = seg[i:i + win] * np.hanning(win)
            sp = np.abs(np.fft.rfft(fr))
            f = np.fft.rfftfreq(win, 1 / sr)
            hf.append(sp[f > 4000].sum() / (sp.sum() + 1e-9))
        hf = np.array(hf)
        # 20/11 (dona: "o S estendido do respeito está errado em TODAS as versões"): o chiado do Kitten/RVC é mais fraco
        # que o do Fish (nunca passava de 0,3 e a função desistia calada). Limiar relativo à própria palavra.
        if len(hf) < 5:
            logging.info(f"[fish S] {wav.name}: palavra curta demais")
            return False
        lim_hf = max(0.12, min(0.3, float(np.percentile(hf, 70))))
        idx = np.where(hf >= lim_hf)[0]
        if not len(idx):
            logging.info(f"[fish S] {wav.name}: não achei o chiado do S (máx {hf.max():.2f})")
            return False
        blocos, cur = [], [idx[0]]
        for k in idx[1:]:
            if k == cur[-1] + 1:
                cur.append(k)
            else:
                blocos.append(cur)
                cur = [k]
        blocos.append(cur)
        # o S de "re-S-peito" fica na 1ª parte da palavra: só vale bloco que começa nos primeiros 60% dela
        lim = int(len(hf) * 0.6)
        blocos = [b_ for b_ in blocos if b_[0] <= lim] or blocos
        b = max(blocos, key=len)
        s0, s1 = ini + b[0] * 0.005, ini + b[-1] * 0.005 + 0.02
        d = s1 - s0
        en = (enfase or "s").lower()
        if en != "s":
            # 21/11 tarde (dona: "os narradores não só alongam o S, dão ênfase no respeito — falam mais alto o RES, ou
            # no final o peito"): s = só o S (aprovado 20/11); res = RES mais alto e +1 semitom; peito = "peito" caindo
            # 1,5 semitom e segurado; tudo = os três; separado = RES alto + pausinha + peito caindo, sem esticar o S
            if _enfase_respeito(wav, ini, fim, s0, s1, alvo_s if en != "separado" else d, en):
                Path(str(wav) + ".words.json").unlink(missing_ok=True)
                logging.info(f"[xtts] 'respeito' com ênfase {en}")
                return True
        if d <= 0.02 or d >= alvo_s:
            logging.info(f"[fish S] {wav.name}: S com {d:.2f}s — não estico")
            return False
        f, cad = d / alvo_s, []
        while f < 0.5:
            cad.append("atempo=0.5")
            f /= 0.5
        cad.append(f"atempo={f:.4f}")
        fc = (f"[0:a]atrim=0:{s0:.3f},asetpts=PTS-STARTPTS[a];"
              f"[0:a]atrim={s0:.3f}:{s1:.3f},asetpts=PTS-STARTPTS,{','.join(cad)},afade=t=in:d=0.02,"
              f"afade=t=out:st={max(0, alvo_s - 0.03):.3f}:d=0.03[s];"
              f"[0:a]atrim={s1:.3f},asetpts=PTS-STARTPTS[b];[a][s][b]concat=n=3:v=0:a=1[o]")
        tmp = wav.with_name(wav.stem + ".s.wav")
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-filter_complex", fc, "-map", "[o]",
                            "-ar", str(sr), "-ac", "2", str(tmp)], capture_output=True)
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
            os.replace(tmp, wav)
            extra = alvo_s - d  # palavras depois do S andam junto
            if wj.exists() and palavras:
                wj.write_text(json.dumps([[round(p0 + (extra if p0 >= s1 else 0), 3),
                                           round(p1 + (extra if p1 >= s1 else 0), 3), w] for p0, p1, w in palavras],
                                         ensure_ascii=False), encoding="utf-8")
            logging.info(f"[fish] 'respeito' com S alongado ({d:.2f}s -> {alvo_s:.2f}s)")
            return True
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[fish] esticar S falhou ({type(e).__name__}: {str(e)[:100]})")
    return False


_PIADA_CONTADA = re.compile(r"(?i)(\bhein\b|kkk|mentira|brincadeira|zoeira|t[oô] (zoando|brincando)|particulares|\beu (faria|fazia|aceitaria|toparia|"
                            r"pegaria)\b|com todo respeito)")


def _risada_do_narrador(voz, i):
    """21/11 v12: uma risadinha REAL do narrador (risada_real/*.wav) pra entrar antes do "Eu faria" (a manha)."""
    pasta = VOZES_DIR / Path(voz).name / "risada_real"
    lst = sorted(pasta.glob("*.wav")) if pasta.is_dir() else []
    curtas = []
    for w in lst:
        try:
            d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                      str(w)], capture_output=True, text=True).stdout or 0)
        except Exception:  # noqa: BLE001
            d = 0
        if 0.5 <= d <= 1.3:  # risadinha, não gargalhada
            curtas.append(w)
    lst = curtas or lst
    return str(lst[i % len(lst)]) if lst else ""


def _risada_real(voz, wav):
    """Põe uma risada REAL do narrador (risada_real/*.wav na pasta da voz, cortada dos vídeos dele) no começo da frase
    que tinha kkk. Sem risada cortada = a frase fica sem risada (melhor que a de robô). FISH_RISADA_REAL=0 desliga."""
    if os.environ.get("FISH_RISADA_REAL", "1") == "0" or not voz:
        return False
    pasta = VOZES_DIR / Path(voz).name / "risada_real"
    lst = sorted(pasta.glob("*.wav")) if pasta.is_dir() else []
    if not lst:
        return False
    import hashlib
    ris = lst[int(hashlib.md5(str(wav).encode()).hexdigest(), 16) % len(lst)]
    wav = Path(wav)
    tmp = wav.with_name(wav.stem + ".ris.wav")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ris), "-i", str(wav), "-filter_complex",
                        # 20/11: estéreo como o resto das frases (mono juntado com estéreo tocava 2x rápido)
                        "[0:a]aresample=44100,aformat=channel_layouts=stereo,apad=pad_dur=0.12[a];"
                        "[1:a]aresample=44100,aformat=channel_layouts=stereo[b];[a][b]concat=n=2:v=0:a=1[o]",
                        "-map", "[o]", str(tmp)], capture_output=True)
    if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
        os.replace(tmp, wav)
        return True
    tmp.unlink(missing_ok=True)
    return False


def _subvoz_por_frase(lines, audio_dir, pv, tem=None):
    """20/11 dona ("pegar vários momentos do narrador como sub-vozes: Mike rindo, Momo fazendo piada mais agudo,
    falando das mulheres, fazendo vozes de personagem, metralhadora"): escolhe por frase a referência do Fish que
    combina com ela (referencia_fish_<sub>.wav na pasta da voz). Sem a sub-voz = a reserva dela; sem nenhuma = normal.
    Antes (19/11) só piada/tensão — e essa parte tinha se perdido no anime_tts do longo Momo/Mike. FISH_CLIMAS=0 desliga."""
    if os.environ.get("FISH_CLIMAS", "1") == "0":
        return {}
    if tem is None:  # 20/11: o Kitten passa os tipos da tabela medida (não tem referencia_fish_*.wav)
        tem = {p.stem.replace("referencia_fish", "") for p in Path(pv).glob("referencia_fish_*.wav")
               if not p.stem.endswith("antiga")}
    if not tem:
        return {}
    climas = None
    try:
        import climas_voz
        climas = climas_voz.escolher([_seguro(x) for x in lines], audio_dir)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[fish nuvem] climas indisponíveis ({type(e).__name__}) — só pelo texto")
    por_clima = {"comentario": "_piada", "engracado": "_piada", "tensao": "_tensao", "vilao": "_tensao",
                 "terror": "_tensao", "triste": "_tensao", "epico": "_agudo", "acao": "_metralhadora"}
    out = {}
    for i, line in enumerate(lines):
        t = _seguro(line)
        if _SUB_IRRITADO.search(t):
            quer = "_irritado"
        elif _SUB_RISO.search(t):
            quer = "_risada"
        elif _SUB_MULHER.search(t):
            quer = "_mulher"
        elif _SUB_PERSON.search(t):
            quer = "_personagem"
        else:
            quer = por_clima.get(climas[i] if climas and i < len(climas) else "normal", "")
        if not quer:
            continue
        for s in [quer] + _SUB_RESERVA.get(quer, []):
            if s in tem:
                out[i] = s
                break
        else:
            # 20/11: sem a sub-voz da frase = "todas as sub-vozes juntas" (aprovada em todos os tipos ouvidos), não a
            # normal (que saiu lenta). O fish_nuvem monta "_todas" quando a voz tem >= 3 sub-vozes.
            if len(tem) >= 3:
                out[i] = "_todas"
    return out


XTTS_VENV = Path(os.environ.get("XTTS_VENV_DIR", "/tmp/venvs_voz/xtts"))



# 21/11 tarde (dona: "regra de sempre reorganizar pra usar as duas placas, de forma que reduza o tempo pra tudo, desde
# teste a produção de Shorts e longos — claro, quando já houver duas coisas simultâneas rodando, uma em cada placa, aí
# já está sendo aproveitado o máximo"). Um lote de voz (XTTS, Fish, RVC) é dividido ao meio entre a placa deste
# trabalho e a OUTRA, só quando a outra está LIVRE (pouca memória usada e parada). Ocupada = 1 placa, como antes.
# Item que faltar depois do paralelo é refeito na placa própria. DUAS_PLACAS=0 desliga.
def _placas_para_lote(env=None):
    """Placas físicas que este lote pode usar: [a minha] ou [a minha, a outra livre]. [None] = não mexe na variável."""
    env = env or os.environ
    cvd = str(env.get("CUDA_VISIBLE_DEVICES", "")).strip()
    minha = cvd if cvd.isdigit() else "0"
    sozinha = [cvd] if cvd else [None]
    if env.get("DUAS_PLACAS") == "0" or os.name == "nt" or (cvd and not cvd.isdigit()):
        return sozinha
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used,utilization.gpu",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=60)
        placas = {}
        for ln in r.stdout.strip().splitlines():
            a = [x.strip() for x in ln.split(",")]
            placas[a[0]] = (float(a[1]), float(a[2]))
    except Exception:  # noqa: BLE001
        return sozinha
    outras = [g for g, (mem, uso) in placas.items() if g != minha and mem < 1500 and uso < 15]
    if not outras:
        return sozinha
    trava = Path(f"/tmp/_placa_emprestada_{outras[0]}")
    try:  # outro lote acabou de pegar a outra placa emprestada (ainda não aparece no nvidia-smi)
        if trava.exists() and time.time() - trava.stat().st_mtime < 180:
            return sozinha
        trava.write_text(str(os.getpid()))
    except OSError:
        pass
    return [minha, outras[0]]


def _lote_em_placas(argv, itens, pasta, nome, timeout, env=None, pronto=None):
    """Roda `argv + [lista.json]` com os itens; divide entre 2 placas se a outra estiver livre. `pronto(item)` diz se
    o item saiu (padrão: Path(item["saida"]) existe). Log junto em <pasta>/_<nome>.log. Devolve as placas usadas."""
    pasta = Path(pasta)
    env = dict(env or os.environ)
    pronto = pronto or (lambda it: Path(it["saida"]).exists())

    def ok(it):
        try:
            return pronto(it)
        except OSError:
            return False
    placas = _placas_para_lote(env) if len(itens) >= 6 else ([env["CUDA_VISIBLE_DEVICES"]]
                                                             if env.get("CUDA_VISIBLE_DEVICES") else [None])

    def rodar(sub, placa, sufixo):
        lj = pasta / f"_{nome}{sufixo}.json"
        lj.write_text(json.dumps(sub, ensure_ascii=False), encoding="utf-8")
        e = dict(env)
        if placa is not None:
            e["CUDA_VISIBLE_DEVICES"] = str(placa)
        fh = open(pasta / f"_{nome}{sufixo}.log" if sufixo else pasta / f"_{nome}.log", "a", encoding="utf-8")
        return subprocess.Popen(list(argv) + [str(lj)], stdout=fh, stderr=subprocess.STDOUT, env=e), fh

    t_fim = time.time() + timeout
    if len(placas) >= 2:
        logging.info(f"[placas] {nome}: {len(itens)} itens divididos entre as placas {placas}")
        procs = [rodar(itens[k::2], placas[k], f"_g{k}") for k in range(2)]
        for pr, fh in procs:
            try:
                pr.wait(timeout=max(60, t_fim - time.time()))
            except subprocess.TimeoutExpired:
                pr.kill()
            fh.close()
        with open(pasta / f"_{nome}.log", "a", encoding="utf-8") as fh:
            for k in range(2):
                fh.write((pasta / f"_{nome}_g{k}.log").read_text(encoding="utf-8", errors="ignore"))
        try:
            Path(f"/tmp/_placa_emprestada_{placas[1]}").unlink()
        except OSError:
            pass
        falta = [it for it in itens if not ok(it)]
        if not falta or time.time() > t_fim:
            return placas
        logging.warning(f"[placas] {nome}: {len(falta)} itens faltaram no paralelo — refaço na placa própria")
        itens, placas = falta, placas[:1]
    pr, fh = rodar(itens, placas[0], "")
    try:
        pr.wait(timeout=max(60, t_fim - time.time()))
    except subprocess.TimeoutExpired:
        pr.kill()
        logging.warning(f"[placas] {nome}: passou do tempo — uso o que já saiu")
    fh.close()
    return placas


# 22/11: mistura XTTS 8 + S2-Pro. Frases de emoção = onde o XTTS não faz o que o narrador real faz (rir, explodir,
# lamentar). Ordem: a 1ª regra que casa define a etiqueta do S2-Pro.
_S2_EMO = [(re.compile(r"(?i)(kkk|haha|rsrs|brincadeira|mentira|zoeira|piada|com todo respeito|particulares|\bhein\b|"
                       r"safad|danad|cen[aá]rio|eu (faria|fazia|aceitaria|toparia))"), "[laughing]"),
           (re.compile(r"(?i)(\bgol\b|isso!|acert|derrub|venc|explod|incr[ií]vel|absurd|que isso|meu deus|caramba|"
                       r"finalmente|conseguiu|olha isso)"), "[excited]"),
           (re.compile(r"(?i)(n[aã]o, n[aã]o|morr|chor|perdeu|acabou pra|triste|sozinh|nunca mais|adeus)"), "[sad]"),
           (re.compile(r"(?i)(de repente|socorro|cuidado|corre|sangue|monstro|assustad|grit)"), "[shocked]")]



_UN = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze", "treze",
       "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
_DZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
_CT = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos",
       "novecentos"]


def _num_pt(n):
    """22/11 v13 (dona: o modelo não sabe contar): número inteiro por extenso em português (até 999 999)."""
    if n < 20:
        return _UN[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _DZ[d] + (" e " + _UN[u] if u else "")
    if n == 100:
        return "cem"
    if n < 1000:
        c, r = divmod(n, 100)
        return _CT[c] + (" e " + _num_pt(r) if r else "")
    m, r = divmod(n, 1000)
    pre = "mil" if m == 1 else _num_pt(m) + " mil"
    return pre + ((" e " if (r < 100 or r % 100 == 0) else " ") + _num_pt(r) if r else "")


def _numeros_por_extenso(t):
    return re.sub(r"(?<![\w.,])\d{1,6}(?![\w.,]\d)", lambda m: _num_pt(int(m.group(0))), t)


def _s2_tags_v13(texto, est, i):
    """22/11 v13: tags do S2-Pro DENTRO da frase, onde encaixam. Risada com intervalo mínimo (não é o coringa),
    reação no máximo de 2 em 2 frases, e tom animado nas frases normais (o modelo soava triste/obrigado)."""
    t = _numeros_por_extenso(texto)
    pre = ""
    gap_riso = i - est.get("riso", -99) >= 3
    gap_rea = i - est.get("rea", -99) >= 2
    if re.search(r"(?i)\bhein\b", t) and gap_riso and not re.search(r"(?i)hein\s*\?!?\s*(\.{2,}|…)?\s*$", t):
        t = re.sub(r"(?i)\b(hein)([.!?]?)", r"[emphasis] \1\2 [chuckle]", t, count=1)
        est["riso"] = i
    if re.search(r"(?i)com todo respeito", t):
        t = re.sub(r"(?i)(com todo respeito)", r"[laughing tone] \1 [short pause]", t, count=1)
        est["riso"] = i
    if re.match(r"(?i)\s*(brincadeira|mentira|zoeira|t[oô] zoando|t[oô] brincando)", t):
        # 23/11 dona: a VIRADA da piada é contada rindo, não lida — sem trava de intervalo (é o momento dela)
        pre = "[laughing] [excited tone] " if os.environ.get("PIADA_CONTADA", "1") != "0" else "[laughing] "
        est["riso"] = i
    elif re.search(r"(?i)hein\s*\?!?\s*(\.{2,}|…)?\s*$", t) and os.environ.get("PIADA_CONTADA", "1") != "0":
        # a provocação antes da virada: ênfase no fim e uma pausa curta (o "tempo" da piada)
        t = re.sub(r"(?i)(hein\s*\?!?)", r"[emphasis] \1 [short pause]", t, count=1)
    if re.search(r"(?i)\bcoitad", t) and gap_rea and not pre:
        pre = "[sigh] "
        est["rea"] = i
    if re.search(r"(?i)(isso,? \w+,? isso|\bgol\b|acert\w+ em cheio)", t):
        pre = "[shouting] "
    elif re.search(r"(?i)(parte pra cima|de repente|do nada|treme|avan[cç]a)", t) and gap_rea and not pre:
        pre = "[excited] " if os.environ.get("S2PRO_INHALE") != "1" else "[inhale] "  # 22/11 dona: som de suspiro cortado entre frases — sem [inhale]
        est["rea"] = i
    if re.search(r"(?i)n[aã]o, n[aã]o", t):
        pre = "[sad] "
    if re.search(r"(?i)(sussurr|segredo|ningu[eé]m (pode|sabe))", t):
        pre = "[whisper] "
    if not pre and not re.search(r"\[", t):
        est["n"] = est.get("n", 0) + 1
        if est["n"] % 2 == 0:
            pre = "[excited tone] "
    return (pre + t).strip()



def _s2pro_modo():
    if os.environ.get("S2PRO") == "0" or _OUTRA:
        return None, "2"
    if str(_xtts_versao() or "").startswith("88") and os.environ.get("XTTS88_COM_S2PRO") != "1":
        return None, "2"  # 25/11: XTTS 88 = um motor só (o treinado); misto com S2-Pro soaria "duas pessoas"
    try:
        ovr = json.loads(os.environ.get("ANIME_LONGO_OVERRIDE") or "{}")
    except ValueError:
        ovr = {}
    # 23/11 dona: padrão = misto XTTS 8 + S2-Pro 13 (config/motor_voz.json); o S2-Pro só onde tem placa (Kaggle)
    try:
        cfg = json.loads((Path(__file__).resolve().parent.parent / "config" / "motor_voz.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {}
    m = str(os.environ.get("S2PRO_MODO") or ovr.get("s2pro") or cfg.get("s2pro") or "").strip().lower()
    v = str(os.environ.get("S2PRO_VERSAO") or ovr.get("s2pro_versao") or cfg.get("s2pro_versao") or "13").strip()
    if m and not os.environ.get("S2PRO_MODO") and not ovr.get("s2pro") and (os.name == "nt" or not Path("/kaggle").exists()):
        m = ""  # PC local sem placa: S2-Pro leva ~190 s/frase — fica só o XTTS 8
    return (m if m in ("misto", "pro") else None), v


def _narrar_s2pro(lines, audio_dir, so=None):
    """22/11: S2-Pro pelo llama.cpp (bin/s2pro_llama.py). Nunca levanta; o que não sair fica pro XTTS."""
    modo, versao = _s2pro_modo()
    if not modo:
        return
    try:
        pv = _pasta_fish()
        ref = pv / "referencia_fish.wav"
        txt = pv / "referencia_fish.txt"
        if not ref.exists() or not txt.exists():
            logging.warning(f"[s2pro] {pv.name} sem trecho real — tudo no XTTS")
            return
        ad = Path(audio_dir)
        dur_ref = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                        str(ref)], capture_output=True, text=True).stdout or 0) or 15.0
        seg = 30 if versao in ("6", "10", "12", "13") else 15
        r_ = ad / f"_s2pro_ref{seg}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ref), "-t", str(seg), "-ac", "1", "-ar", "24000",
                        str(r_)], capture_output=True)
        palavras = txt.read_text(encoding="utf-8").split()
        reftxt = " ".join(palavras[:max(4, int(len(palavras) * min(1.0, seg / dur_ref)))])
        cps_ref = len(" ".join(palavras)) / max(dur_ref, 1.0)
        itens, n_emo = [], 0
        _EST13 = {}
        # 22/11 dona ("nesses vídeos temos que usar bastante risada, piada e as coisas novas que só o S2-Pro faz"):
        # na v13 o misto manda pro S2-Pro também as frases com reação/risada/intensidade das tags novas, teto 40%
        # 24/11 dona ("implemente para as próximas obrigatoriamente saírem com as melhorias"): a réplica cega mostrou o
        # S2-Pro 13 imitando melhor que o XTTS 8 também nas frases NORMAIS (comentário/explicação/leitura) -> teto 70%
        # e as frases sem emoção também entram (uma sim, uma não, pra misturar os dois motores ao longo do vídeo).
        # S2PRO_TETO=0.40 + S2PRO_SO_EMOCAO=1 voltam ao de antes.
        _teto_s2 = float(os.environ.get("S2PRO_TETO", "0.70"))
        _so_emo = os.environ.get("S2PRO_SO_EMOCAO") == "1"
        teto = max(1, int(len(lines) * (_teto_s2 if versao == "13" else 0.25))) if modo == "misto" else len(lines)
        for i, line in enumerate(lines):
            if so is not None and i not in so:
                continue
            out = ad / f"audio_{i}.wav"
            if out.exists() and out.stat().st_size > 500:
                continue
            texto, _riso = _texto_fish(_seguro(line))
            if not texto.strip():
                continue
            tag = next((t_ for rx, t_ in _S2_EMO if rx.search(texto)), "")
            if modo == "misto" and not tag and versao == "13" and "[" in _s2_tags_v13(texto, {}, 999):
                tag = "[excited]"  # 22/11: casou só com as tags novas (reação/risada/intensidade) — vai pro S2-Pro
            if modo == "misto" and not tag and versao == "13" and not _so_emo and i % 2 == 0:
                tag = "[excited tone]"  # 24/11: frase normal também vai pro S2-Pro (alternada), tom animado da v13
            if modo == "misto" and not tag:
                continue
            if modo == "misto" and n_emo >= teto:
                continue
            if not tag and versao in ("4", "5", "6", "12"):
                tag = "[excited]" if i % 3 == 0 else "[confident]"
            n_emo += 1
            v1 = versao == "1"
            ref_i, txt_i = str(r_), reftxt
            if versao in ("7", "8", "9", "10", "11", "12", "13") and tag:
                # 22/11 v7+: referência do TIPO da frase (trecho real do narrador rindo/fazendo piada/tenso...)
                tipo = {"[laughing]": ("_risada", "_piada"), "[excited]": ("_agudo", "_metralhadora"),
                        "[sad]": ("_tensao",), "[shocked]": ("_tensao", "_irritado")}.get(tag, ())
                if re.search(r"(?i)(gostos|atraente|professora|mulher|respeito)", texto):
                    tipo = ("_mulher",) + tuple(tipo)
                for x in tipo:
                    if (pv / f"referencia_fish{x}.wav").exists() and (pv / f"referencia_fish{x}.txt").exists():
                        rx_ = ad / f"_s2pro_ref15{x}.wav"
                        if not rx_.exists():
                            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pv / f"referencia_fish{x}.wav"),
                                            "-t", "15", "-ac", "1", "-ar", "24000", str(rx_)], capture_output=True)
                        ref_i = str(rx_)
                        txt_i = (pv / f"referencia_fish{x}.txt").read_text(encoding="utf-8").strip()
                        break
            # 22/11 v8+: pergunta retórica = 2 pedaços gerados separados (afirmação! / E vocês...?) com pausa
            partes = None
            if versao in ("8", "9", "10", "11", "12", "13"):
                mq = re.search(r"^(.*?[!.])\s+((?:E |Mas )?(?:vocês|você|cês|tu)\b[^?]*\?)\s*$", texto)
                if mq:
                    partes = [mq.group(1).strip(), mq.group(2).strip()]
            itens.append({"texto": texto, "saida": str(ad / f"audio_{i}.s2pro_bruto.wav"), "i": i, "ref": ref_i,
                          "reftxt": txt_i, "tag": "" if v1 else tag, "partes": partes,
                          "n": 1 if v1 else (2 if versao in ("2", "3", "7", "8", "11") else 3), "seed": 42,
                          "cps_alvo": 17 if versao in ("1", "2") else round(cps_ref, 1),
                          "whisper": versao in ("5", "6", "9", "10"), "versao": versao,
                          "texto_tags": _s2_tags_v13(texto, _EST13, i) if versao == "13" else ""})
        if not itens:
            return
        lista = ad / "_s2pro.json"
        lista.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
        t0 = time.time()
        # 22/11: compila o llama.cpp e baixa o modelo UMA vez antes de dividir nas 2 placas (senão os 2 processos
        # compilam/baixam juntos na mesma pasta e um quebra o outro)
        prep = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, %r); import s2pro_llama as s; "
                               "t = s.compilar(); m = s.baixar(); print('PREP', bool(t), bool(m))"
                               % str(Path(__file__).parent)], capture_output=True, text=True, timeout=3 * 3600)
        if "PREP True True" not in (prep.stdout or ""):
            logging.warning(f"[s2pro] llama.cpp/modelo não ficou pronto — tudo no XTTS {(prep.stdout + prep.stderr)[-300:]}")
            return
        logging.info(f"[s2pro] llama.cpp + modelo prontos em {time.time() - t0:.0f}s")
        _lote_em_placas([sys.executable, str(Path(__file__).with_name("s2pro_llama.py")), "lote"], itens, ad, "s2pro",
                        8 * 3600)
        feitos = []
        for it in itens:
            bruto = Path(it["saida"])
            if not bruto.exists():
                continue
            out = ad / f"audio_{it['i']}.wav"
            if subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-ac", "2", "-ar", "44100", str(out)],
                              capture_output=True).returncode != 0:
                continue
            bruto.unlink(missing_ok=True)
            feitos.append(it["i"])
            try:
                # 23/11 (revisão): grito sai mais alto e sussurro/suspiro mais baixo (antes tudo -20 LUFS: a variação de
                # intensidade sumia). S2PRO_GANHO_TAG=0 desliga.
                _tt = it.get("texto_tags") or ""
                _g = 0.0
                if os.environ.get("S2PRO_GANHO_TAG", "1") != "0":
                    _g = next((v for k, v in (("[shouting]", 3.0), ("[laughing", 1.0), ("[excited", 1.0),
                                              ("[whisper", -5.0), ("[sad]", -2.0), ("[sigh]", -2.0)) if k in _tt), 0.0)
                narracao_curva.pos_processar(out, _g)
                # 22/11 v11: corte mais agressivo; 23/11: 1 passada (a 2ª não fazia nada) e respiração/riso/suspiro
                # das tags não é mais tratado como silêncio (-45 dB em vez de -38)
                if versao in ("11", "12", "13"):
                    # 24/11 dona ("cortando o finalzinho das frases"): 0,04 -> 0,06 s e -38 -> -45 dB (-50 com riso/suspiro)
                    _lim = "-50" if any(k in _tt for k in ("[sigh]", "[chuckle]", "[laughing", "[whisper")) else "-45"
                    narracao_curva.microcortes(out, float(os.environ.get("S2PRO_GAP", "0.06")),
                                               limiar_db=float(os.environ.get("S2PRO_LIMIAR_DB", _lim)))
                else:
                    narracao_curva.microcortes(out)
                if _tem_respeito_piada(_seguro(lines[it["i"]]), it["i"]):
                    _esticar_s_respeito(out, texto=_seguro(lines[it["i"]]), enfase="tudo")
                if os.environ.get("XTTS_FIM_SOBE", "1") == "1" and pv.name in FISH_FIM_ST:  # 24/11: ligado (venceu no teste cego v3)
                    _fim_que_sobe(out, pv.name)  # 24/11: fim que sobe (aprovado no Fish) também no S2-Pro — em TESTE
                if it["i"] == len(lines) - 1:
                    _aplicar_margem_final(out)
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[s2pro] pós da frase {it['i']} falhou ({type(e).__name__})")
        if feitos and _xtts_rvc():
            _rvc_por_cima_do_fish(audio_dir, feitos, pv.name)
        if feitos:
            (ad / "_s2pro_feitas.json").write_text(json.dumps(sorted(feitos)), encoding="utf-8")
        logging.info(f"[s2pro] modo {modo} v{versao}: {len(feitos)}/{len(itens)} frases em {time.time() - t0:.0f}s "
                     f"(de {len(lines)}); o resto no XTTS")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[s2pro] falhou ({type(e).__name__}: {str(e)[:150]}) — tudo no XTTS")


def _xtts_versao():
    """21/11 dona: o XTTS vira o motor principal. config/motor_voz.json {"motor": "xtts", "xtts_versao": "6"} ou
    MOTOR_VOZ=xtts + XTTS_VERSAO (4, 5, 6 ou "tercos" = o vídeo dividido em 3 partes: 4 / 5 / 6, pra ela comparar
    num longo). Devolve a versão ou None (XTTS desligado)."""
    v = (os.environ.get("MOTOR_VOZ") or "").strip().lower()
    cfg = {}
    try:
        cfg = json.loads((Path(__file__).resolve().parent.parent / "config" / "motor_voz.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    try:  # 21/11: o pedido do longo pode ligar sozinho (longo_override {"motor_voz": "xtts", "xtts_versao": ...})
        ovr = json.loads(os.environ.get("ANIME_LONGO_OVERRIDE") or "{}")
    except ValueError:
        ovr = {}
    if not v:
        v = str(ovr.get("motor_voz") or cfg.get("motor", "")).strip().lower()
    if v != "xtts":
        return None
    # 21/11 tarde (dona): "não vamos usar a XTTS 9, apenas a 8" — 8 vira o padrão (6/7/8 iguais pra ela; a 8 tem a
    # pior frase melhor no auditor). Pedido "9" vira 8.
    v_ = str(os.environ.get("XTTS_VERSAO") or ovr.get("xtts_versao") or cfg.get("xtts_versao") or "8").strip().lower()
    return "8" if v_ == "9" else v_


def _audio_pronto_do_drive(audio_dir, lines=None):
    """21/11 dona (S2-Pro/Qwen3: "divide em sessões"): a voz do longo foi gerada antes, em pedaços paralelos, e está no
    Drive (longo_override "audio_pronto": "manhwa-drive:colab_recap/qwen3_longo/<vid>_<voz>/audio"). Copia os
    audio_<i>.wav pro audio_cache; o preparar_clone pula as frases que já têm áudio e faz o resto (XTTS/Fish/Kitten).
    Pós aplicado aqui: microcortes + velocidade por frase (metade) + S do respeito, e RVC do narrador por cima."""
    try:
        ovr = json.loads(os.environ.get("ANIME_LONGO_OVERRIDE") or "{}")
    except ValueError:
        return
    src = ovr.get("audio_pronto")
    if not src:
        return
    import glob
    rcl = next((x for x in glob.glob("/kaggle/tmp/**/rclone", recursive=True) + glob.glob("/kaggle/working/**/rclone",
                                                                                          recursive=True)
                if os.access(x, os.X_OK)), None)
    conf = next((c for c in ["/tmp/rclone.conf"] + glob.glob("/kaggle/input/**/rclone.conf", recursive=True)
                 if os.path.isfile(c)), None)
    if not rcl or not conf:
        logging.warning("[audio pronto] sem rclone — narra do zero")
        return
    ad = Path(audio_dir)
    tmp = ad / "_audio_pronto"
    tmp.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([rcl, "--config", conf, "copy", src, str(tmp), "--include", "audio_*", "--include",
                        "roteiro_audio.txt"], capture_output=True, text=True, timeout=3600)
    # 22/11 (82ge: legenda não batia com a voz): casa pelo TEXTO — índice do áudio -> índice da frase no vídeo
    mapa = None
    if lines:
        ref_txt = tmp / "roteiro_audio.txt"
        if not ref_txt.exists():
            subprocess.run([rcl, "--config", conf, "copyto", src.rstrip("/").rsplit("/", 1)[0] + "/roteiro.txt",
                            str(ref_txt)], capture_output=True, timeout=600)
        if not ref_txt.exists():
            for cand in (ad.parent / "roteiro.txt", ad.parent.parent / "roteiro.txt"):
                if cand.exists():
                    shutil.copy(cand, ref_txt)
                    break
        if ref_txt.exists():
            def _nt(x):
                return re.sub(r"\W+", " ", str(x).lower()).strip()
            gerados = ref_txt.read_text(encoding="utf-8").splitlines()
            livres = {}
            for j, t_ in enumerate(gerados):
                livres.setdefault(_nt(t_), []).append(j)
            mapa = {}
            for k, t_ in enumerate(lines):
                fila = livres.get(_nt(t_))
                if fila:
                    mapa[fila.pop(0)] = k
            logging.info(f"[audio pronto] casado pelo texto: {len(mapa)}/{len(lines)} frases do vídeo têm áudio pronto "
                         f"({len(gerados)} gerados); o resto vai pro XTTS")
        else:
            logging.warning("[audio pronto] sem roteiro_audio.txt nem roteiro.txt — casando por número (pode desalinhar)")
    n = 0
    feitos = []
    # 21/11 noite (dona: "XTTS 8 misturado com o S2-Pro — o mais custo-benefício"): "audio_pronto_so" = lista das
    # frases que vêm do áudio pronto (as de emoção feitas no S2-Pro); o resto o XTTS narra. Sem a chave = todas.
    so_ = ovr.get("audio_pronto_so")
    so_ = {int(x) for x in so_} if isinstance(so_, list) else None
    for w in tmp.glob("audio_*.wav"):
        m = re.fullmatch(r"audio_(\d+)\.wav", w.name)
        if not m:
            continue
        i = int(m.group(1))
        if so_ is not None and i not in so_:
            continue
        if mapa is not None:  # 22/11: índice do áudio gerado -> índice da frase no vídeo (pelo texto)
            if i not in mapa:
                continue
            i = mapa[i]
        out = ad / f"audio_{i}.wav"
        if out.exists():
            continue
        if subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-ac", "2", "-ar", "44100", str(out)],
                          capture_output=True).returncode == 0:
            feitos.append(i)
            n += 1
    logging.info(f"[audio pronto] {n} frases vieram de {src} (rc={r.returncode})")
    for i in feitos:
        out = ad / f"audio_{i}.wav"
        try:
            narracao_curva.pos_processar(out, 0.0)
            narracao_curva.microcortes(out)
        except Exception:  # noqa: BLE001
            pass
    if feitos and _xtts_rvc():
        pv = _pasta_fish()
        _rvc_por_cima_do_fish(audio_dir, feitos, pv.name)


def _xtts_rvc():
    """21/11 dona (ouviu xtts6 + RVC): "melhorou muito com o RVC — os próximos longos devem rodar com ele". Padrão LIGADO
    no XTTS (voz clonada do narrador por cima, firma o timbre); XTTS_RVC=0 ou longo_override "xtts_rvc": false desliga."""
    if os.environ.get("XTTS_RVC") in ("0", "1"):
        return os.environ["XTTS_RVC"] == "1"
    try:
        ovr = json.loads(os.environ.get("ANIME_LONGO_OVERRIDE") or "{}")
    except ValueError:
        ovr = {}
    return bool(ovr.get("xtts_rvc", True))


def _xtts_pronto():
    """Monta o ambiente do XTTS 1x por máquina (torch 2.5.1 + coqui-tts num venv próprio; ~4 min no Kaggle).
    Falhou = False e a narração segue no Fish/Kitten como antes."""
    py = XTTS_VENV / "bin" / "python"
    if os.name == "nt":
        py = XTTS_VENV / "Scripts" / "python.exe"
    try:
        if not py.exists():
            if os.name == "nt":
                return False  # nos PCs: venv montado à mão (ver versoes_motor_voz/LEIA.md)
            uv = "/tmp/uvbin/uv"
            if not os.path.exists(uv):
                subprocess.run(["bash", "-c", "mkdir -p /tmp/uvbin && (curl -LsSf https://astral.sh/uv/install.sh | "
                                "env UV_INSTALL_DIR=/tmp/uvbin UV_NO_MODIFY_PATH=1 sh)"], capture_output=True, timeout=900)
            subprocess.run([uv, "venv", "--python", "3.11", str(XTTS_VENV)], capture_output=True, timeout=900)
            subprocess.run([uv, "pip", "install", "--python", str(py), "torch==2.5.1", "torchaudio==2.5.1"],
                           capture_output=True, timeout=3600)
            subprocess.run([uv, "pip", "install", "--python", str(py), "coqui-tts", "soundfile", "transformers<4.50"],
                           capture_output=True, timeout=3600)
        # 21/11 tarde: DeepSpeed (XTTS_DEEPSPEED=1) — acelerador oficial do XTTS; só instala quando pedido
        if os.environ.get("XTTS_DEEPSPEED") == "1" and subprocess.run([str(py), "-c", "import deepspeed"],
                                                                      capture_output=True, timeout=300).returncode:
            subprocess.run(["/tmp/uvbin/uv", "pip", "install", "--python", str(py), "deepspeed==0.16.4", "ninja"],
                           capture_output=True, timeout=2400)
        # 21/11 v9: Whisper dentro do melhor de 3 (instala junto; se já existia o venv, instala só isso)
        if subprocess.run([str(py), "-c", "import faster_whisper, scipy"], capture_output=True, timeout=300).returncode:
            subprocess.run(["/tmp/uvbin/uv", "pip", "install", "--python", str(py), "faster-whisper", "scipy"],
                           capture_output=True, timeout=1800)
        return subprocess.run([str(py), "-c", "from TTS.api import TTS"], capture_output=True,
                              timeout=600).returncode == 0
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[xtts] ambiente não montou ({type(e).__name__}: {e})")
        return False


def _narrar_xtts(lines, audio_dir, so=None):
    """21/11: narra pelo XTTS v2 (bin/xtts_nuvem.py). Versões (testes do gol 20-21/11):
      4 = frase inteira sem ponto + melhor de 3 + microcortes + velocidade por frase (metade) + S do respeito
      5 = frase a frase + referência normal+sub-voz do tipo + melhor de 3 + pós da 4 com velocidade 0,8
      6 = a 5 + cadência quebrada do Q3 (a escolhida pela dona; "4 e 6 iguais ao meu ouvido")
    Cada audio_i.wav pronto fica e o resto do preparar_clone pula. Nunca levanta."""
    versao = _xtts_versao()
    if not versao or _OUTRA:
        return
    if versao.startswith("88"):
        # 25/11 dona: nomes PROVISÓRIOS = "88-2".."88-6" (receitas do teste OUVIR_POR_FRASE); "88" sozinho = a OFICIAL
        # (hoje = 88-4 até a dona escolher). Cada receita só liga as chaves que não vieram de fora (setdefault).
        _rec = {"88-2": {"XTTS_RVC": "0", "XTTS_SEM_VEL": "1", "XTTS_SEM_CADENCIA": "1", "XTTS_TENTATIVAS": "1"},
                "88-3": {"XTTS_RVC": "0", "XTTS_SEM_VEL": "1", "XTTS_SEM_CADENCIA": "1"},
                "88-4": {"XTTS_RVC": "1"},
                "88-5": {"XTTS_RVC": "0", "XTTS_SEM_VEL": "1", "XTTS_SEM_CADENCIA": "1", "XTTS_TENTATIVAS": "1",
                         "XTTS_REF_SO_TIPO": "1"},
                "88-6": {"XTTS_RVC": "1", "XTTS_REF_SO_TIPO": "1"}}
        _oficial = os.environ.get("XTTS88_OFICIAL", "88-4")
        for k_, v_ in _rec.get(versao if versao in _rec else _oficial, {}).items():
            os.environ.setdefault(k_, v_)
        logging.info(f"[xtts88] receita {versao if versao in _rec else versao + ' (oficial = ' + _oficial + ')'}")
        versao = "88"
    if versao == "88":
        # 25/11 dona: XTTS 88 = XTTS 8 + modelo TREINADO do narrador (vozes/<voz>/xtts_ft/model.pth). Sem treino
        # NÃO vira XTTS 8 escondido: avisa alto, grava marca e deixa a frase pro próximo motor.
        _v88 = os.environ.get("VOZ_CLONADA") or ""
        _ck88 = VOZES_DIR / Path(_v88).name / "xtts_ft"
        if not (_v88 and (_ck88 / "model.pth").exists()):
            logging.error(f"[xtts88] {_v88 or 'sem narrador'} NÃO tem modelo treinado em {_ck88} — "
                          "XTTS 88 exige treino do narrador; treine a voz antes (job_xtts_finetune.py)")
            try:
                (Path(audio_dir) / "_XTTS88_SEM_TREINO.json").write_text(
                    json.dumps({"voz": _v88, "esperado": str(_ck88)}), encoding="utf-8")
            except OSError:
                pass
            return
        os.environ["XTTS_CKPT"] = str(_ck88)
        versao = "8"  # mesma receita do 8 (receita 4/5/6 final entra aqui depois da escolha da dona)
    if not _xtts_pronto():
        logging.warning("[xtts] sem ambiente — narração segue no Fish/Kitten")
        return
    try:
        voz = os.environ.get("VOZ_CLONADA") or ""
        pv = _pasta_fish()
        ref = pv / "referencia_fish.wav"
        if not ref.exists():
            logging.warning(f"[xtts] {pv.name} sem trecho real — segue no Fish/Kitten")
            return
        ad = Path(audio_dir)
        ref15 = ad / "_xtts_ref15.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ref), "-t", "15", "-ac", "1", "-ar", "24000",
                        str(ref15)], capture_output=True)
        tipos = {p.stem.replace("referencia_fish", "") for p in pv.glob("referencia_fish_*.wav")
                 if "antiga" not in p.stem}
        subs = _subvoz_por_frase(lines, audio_dir, None, tem=tipos)
        try:
            import climas_voz
            _marcar_gol(lines, climas_voz.escolher([_seguro(x) for x in lines], audio_dir))
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[xtts] gol desligado ({type(e).__name__})")
        n = len(lines)

        def versao_da(i):
            if versao == "tercos":  # o vídeo em 3 partes: 4 / 5 / 6
                return "4" if i < n / 3 else ("5" if i < 2 * n / 3 else "6")
            return versao
        itens = []
        for i, line in enumerate(lines):
            if so is not None and i not in so:
                continue
            out = ad / f"audio_{i}.wav"
            if out.exists() and out.stat().st_size > 500:
                continue
            texto, _riso = _texto_fish(_seguro(line))
            vi = versao_da(i)
            refs = [str(ref15)]
            sub = subs.get(i, "")
            if vi in ("7", "8", "8b", "9", "10", "11", "12"):
                # 21/11 v7: o XTTS só ouvia 15 s. Agora: o trecho normal INTEIRO + até 2 trechos reais de outros jeitos
                # dele (o do tipo da frase primeiro), 12 s cada — timbre e jeito mais firmes (ANALISE_MELHORAR_XTTS)
                refs = [str(ad / "_xtts_ref_inteira.wav")]
                if not Path(refs[0]).exists():
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ref), "-t", "30", "-ac", "1", "-ar",
                                    "24000", refs[0]], capture_output=True)
                extras = ([sub] if sub and sub != "_todas" else []) + [x for x in ("_piada", "_agudo", "_tensao")
                                                                      if x != sub]
                if vi in ("8", "12") and _PIADA_CONTADA.search(texto):  # 23/11: a 8 (padrão) também
                    # 21/11 v12 (dona: "as piadas têm que parecer contadas, não lidas"): frase de piada ouve primeiro
                    # o trecho REAL dele rindo/fazendo piada
                    extras = ["_risada", "_piada"] + [x for x in extras if x not in ("_risada", "_piada")]
                for x in extras:
                    if len(refs) >= 3:
                        break
                    if (pv / f"referencia_fish{x}.wav").exists():
                        s12 = ad / f"_xtts_ref12{x}.wav"
                        if not s12.exists():
                            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pv / f"referencia_fish{x}.wav"),
                                            "-t", "12", "-ac", "1", "-ar", "24000", str(s12)], capture_output=True)
                        refs.append(str(s12))
                # 25/11 dona (teste do XTTS fine-tunado): XTTS_REF_SO_TIPO=1 -> a frase ouve SÓ o trecho real do tipo
                # dela (sem os 30 s da normal nem as extras). XTTS_TIPO_FORCADO="i:_piada,j:_mulher" fixa o tipo (teste).
                if os.environ.get("XTTS_REF_SO_TIPO") == "1":
                    forc = dict(x.split(":", 1) for x in (os.environ.get("XTTS_TIPO_FORCADO") or "").split(",") if ":" in x)
                    tp = forc.get(str(i)) or (sub if sub and sub != "_todas" else "")
                    if tp and (pv / f"referencia_fish{tp}.wav").exists():
                        s12 = ad / f"_xtts_ref12{tp}.wav"
                        if not s12.exists():
                            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pv / f"referencia_fish{tp}.wav"),
                                            "-t", "12", "-ac", "1", "-ar", "24000", str(s12)], capture_output=True)
                        refs = [str(s12)]
            elif vi in ("5", "6") and sub and sub != "_todas" and (pv / f"referencia_fish{sub}.wav").exists():
                s15 = ad / f"_xtts_ref15{sub}.wav"
                if not s15.exists():
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pv / f"referencia_fish{sub}.wav"), "-t",
                                    "15", "-ac", "1", "-ar", "24000", str(s15)], capture_output=True)
                refs.append(str(s15))
            itens.append({"texto": texto, "saida": str(ad / f"audio_{i}.xtts_bruto.wav"), "i": i, "refs": refs,
                          "temp": float(os.environ.get("XTTS_TEMP") or (0.6 if vi in ("5", "6", "7", "8", "8b", "9", "10", "11", "12") else 0.75)),
                          "cadencia_real": vi in ("8", "8b", "9", "10", "11", "12") and os.environ.get("XTTS_SEM_CADENCIA") != "1",
                          "whisper": vi == "9",
                          "pergunta_publico": vi in ("8", "11", "12"), "manha": vi == "12",  # 8 = 8b + pergunta retórica do 11
                          "risada": _risada_do_narrador(pv.name, i) if vi == "12" else "", "n": int(os.environ.get("XTTS_TENTATIVAS", "3")),
                          "frase_inteira": vi == "4", "v": vi})
        if not itens:
            return
        lista = ad / "_xtts.json"
        lista.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
        py = XTTS_VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        t0 = time.time()
        # 21/11 tarde: as 2 placas quando a outra está livre (_lote_em_placas); XTTS_DUAS_GPUS=0 desliga só aqui
        env_x = {**os.environ, **({"DUAS_PLACAS": "0"} if os.environ.get("XTTS_DUAS_GPUS") == "0" else {})}
        _lote_em_placas([str(py), str(Path(__file__).with_name("xtts_nuvem.py")), "lote"], itens, ad, "xtts",
                        6 * 3600, env=env_x)
        feitos = []
        for it in itens:
            bruto = Path(it["saida"])
            if not bruto.exists():
                continue
            out = ad / f"audio_{it['i']}.wav"
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-ac", "2", "-ar", "44100", str(out)],
                               capture_output=True)
            bruto.unlink(missing_ok=True)
            if r.returncode != 0:
                out.unlink(missing_ok=True)
                continue
            feitos.append(it["i"])
            i, vi = it["i"], it["v"]
            try:
                narracao_curva.pos_processar(out, 0.0)
                if vi in ("6", "7"):  # v8/v9: a cadência vem por sentença no próprio XTTS
                    _cadencia_quebrada(out)
                narracao_curva.microcortes(out)
                forca = 0.5 if vi == "4" else 0.8
                if os.environ.get("XTTS_SEM_VEL") == "1":  # 25/11: XTTS fine-tunado já tem o ritmo do narrador
                    forca = 0.0
                kv = 1 + (_vel_por_frase(_seguro(lines[i]), i) - 1) * forca
                if _frase_lenta(lines[i]):
                    kv = min(kv, 1.04)
                tmp = out.with_name(out.stem + ".kv.wav")
                if abs(kv - 1) > 0.01 and subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-af",
                                                          f"atempo={kv:.3f}", "-ac", "2", str(tmp)],
                                                         capture_output=True).returncode == 0:
                    os.replace(tmp, out)
                if _tem_respeito_piada(_seguro(lines[i]), i):
                    # 21/11 v10+: além do S, a ênfase do narrador real ("RES" mais alto, "peito" caindo)
                    _esticar_s_respeito(out, texto=_seguro(lines[i]), enfase=(os.environ.get("XTTS_RESPEITO_ENFASE")
                                        or "tudo") if vi in ("8", "10", "11", "12") else None)  # 8 = 8b + ênfase do respeito do 10
                if os.environ.get("XTTS_FIM_SOBE", "1") == "1" and pv.name in FISH_FIM_ST:  # 24/11: ligado (venceu no teste cego v3)
                    _fim_que_sobe(out, pv.name)  # 24/11: fim que sobe (aprovado no Fish) também no XTTS — em TESTE
                if os.environ.get("XTTS_RVC") == "1":
                    pass  # RVC por cima: ver _rvc_por_cima_do_fish (teste à parte, dona 21/11)
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[xtts] pós da frase {i} falhou ({type(e).__name__}: {e})")
            if i == len(lines) - 1:
                _aplicar_margem_final(out)
        if feitos and _xtts_rvc():
            _rvc_por_cima_do_fish(audio_dir, feitos, pv.name)
        if feitos:
            (ad / "_voz_online.json").write_text(json.dumps(
                {"motor": f"xtts_v{versao}", "frases": sorted(feitos), "total": len(itens)}), encoding="utf-8")
        try:  # 24/11: prova de QUAL referência foi usada (dona: "tem certeza que tem as melhorias das réplicas?")
            logging.info("[xtts] referências: " + ", ".join(
                f"{q.name}={q.stat().st_size}B" for q in sorted(pv.glob("referencia_fish*.wav"))))
        except Exception:  # noqa: BLE001
            pass
        logging.info(f"[xtts] {len(feitos)}/{len(itens)} frases em {time.time() - t0:.0f}s (versão {versao}, "
                     f"narrador {pv.name}); o resto no Fish/Kitten")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[xtts] falhou ({type(e).__name__}: {str(e)[:150]}) — segue no Fish/Kitten")


def _narrar_fish_nuvem(lines, audio_dir, so=None):
    """Narra pelo Fish Speech na GPU (bin/fish_nuvem.py, num processo só: o motor carrega 1x). Cada audio_i.wav que
    sai fica pronto (sem RVC — o Fish já é a voz do narrador) e o laço do preparar_clone pula. Nunca levanta."""
    if not _fish_nuvem_pronto():
        return
    try:
        voz = os.environ.get("VOZ_CLONADA") or ""
        pv = _pasta_fish()
        if pv.name != Path(voz).name:
            logging.info(f"[fish nuvem] {voz or 'sem narrador'} sem referência do Fish — narra com {pv.name} "
                         "(no Kaggle é sempre o motor novo)")
        subs = _subvoz_por_frase(lines, audio_dir, pv)
        try:  # 20/11: aceleração do gol (sequências de tensão/ação aceleram até o desfecho)
            import climas_voz
            _marcar_gol(lines, climas_voz.escolher([_seguro(x) for x in lines], audio_dir))
            if _GOL_CTX:
                logging.info(f"[fish nuvem] aceleração do gol: {sum(1 for v in _GOL_CTX.values() if v[0] == 'sobe')} "
                             f"frases subindo, {sum(1 for v in _GOL_CTX.values() if v[0] == 'gol')} gol(s), "
                             f"{sum(1 for v in _GOL_CTX.values() if v[0] == 'falha')} falha(s)")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[fish nuvem] aceleração do gol pulada ({type(e).__name__})")
        # 20/11 dona (R resolveu a velocidade): "o Fish se atrapalha ao acelerar por ele e sai estranho; acelerando
        # pelo código resolveu — fazer o A com as acelerações feitas pelo código e não no Fish". FISH_ACELERA_NO_CODIGO=1:
        # frases da corrida do gol / ação / metralhadora / agudo / irritado são GERADAS calmas (referência normal) e a
        # velocidade entra depois (microcortes + velocidade por frase, como o Kitten do R).
        if os.environ.get("FISH_ACELERA_NO_CODIGO") == "1":
            rapidas = {"_metralhadora", "_agudo", "_irritado", "_tensao"}
            calmos = [i for i in list(subs) if subs[i] in rapidas or (_GOL_CTX.get(i) or ("",))[0] in
                      ("sobe", "gol", "falha", "grosso")]
            for i in calmos:
                subs.pop(i, None)
            for i, g in _GOL_CTX.items():
                if g[0] in ("sobe", "gol", "falha", "grosso"):
                    subs.pop(i, None)
            logging.info(f"[fish nuvem] acelera no código: {len(calmos)} frases geradas calmas (ref normal)")
        itens = []
        for i, line in enumerate(lines):
            if so is not None and i not in so:
                continue
            out = Path(audio_dir) / f"audio_{i}.wav"
            if out.exists() and out.stat().st_size > 500:
                continue
            texto, riso = _texto_fish(_seguro(line))
            # 20/11 MISTURA por tipo: o Fish só narra as frases em que ser humano pesa mais (piada, risada, mulher,
            # personagem, irritado, desfecho do gol); o resto fica pro Kitten (estável), que vem depois no preparar_clone
            if os.environ.get("MISTURA_MODO") == "por_tipo" and not _frase_do_fish(i, subs, _seguro(line), riso):
                continue
            if texto.strip():
                itens.append({"texto": texto, "saida": str(Path(audio_dir) / f"audio_{i}.fish_bruto.wav"), "i": i,
                              "ref": subs.get(i, ""), "riso": riso})
        if not itens:
            return
        if subs:
            from collections import Counter
            logging.info(f"[fish nuvem] sub-vozes de {pv.name}: "
                         f"{dict(Counter(it['ref'] or 'normal' for it in itens))}")
        lista = Path(audio_dir) / "_fish_nuvem.json"
        lista.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
        t0 = time.time()
        # 21/11 tarde: 2 placas quando a outra está livre (estourou o tempo = aproveita o que já saiu)
        _lote_em_placas([os.environ["FISH_VENV"], str(Path(__file__).with_name("fish_nuvem.py")), "lote", str(pv)],
                        itens, audio_dir, "fish_nuvem", 3 * 3600)
        # 20/11 (longo de teste saiu com 0 Fish e o erro ficou só no _fish_nuvem.log, que não volta do Kaggle): sem
        # nenhuma frase pronta, o fim do log do Fish vai pro pipeline.log
        if not any(Path(it["saida"]).exists() for it in itens):
            try:
                cauda = (Path(audio_dir) / "_fish_nuvem.log").read_text(encoding="utf-8", errors="ignore")[-1500:]
                logging.error("[fish nuvem] NENHUMA frase saiu — fim do log do Fish: " + cauda.replace("\n", " | "))
            except OSError:
                pass
        feitos = []
        for it in itens:
            bruto = Path(it["saida"])
            if not bruto.exists():
                continue
            out = Path(audio_dir) / f"audio_{it['i']}.wav"
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-ac", "1", "-ar", "44100", str(out)],
                               capture_output=True)
            bruto.unlink(missing_ok=True)
            if r.returncode != 0:  # 19/11 (revisão): wav truncado não pode passar por pronto no laço do p3
                out.unlink(missing_ok=True)
            if r.returncode == 0 and out.exists():
                feitos.append(it["i"])
                _acabamento_fish(out, voz)
                if os.environ.get("FISH_ACELERA_NO_CODIGO") == "1":
                    # mesma receita do Kitten no R: microcortes + velocidade por frase (gol rápido, piada devagar)
                    try:
                        narracao_curva.microcortes(out)
                        # 20/11 noite (dona: A2 do Mike "muito rápido"; Momo "um pouco rápido"): o Fish já fala na
                        # velocidade natural do narrador (mais rápido que o Kitten) — leva só METADE da aceleração
                        kv = 1 + (_vel_por_frase(it["texto"], it["i"]) - 1) * float(
                            os.environ.get("FISH_ACELERA_FORCA", "0.5"))
                        _lento = _frase_lenta(it["texto"])
                        if _lento:
                            kv = min(kv, 1.04)
                        tmp = out.with_name(out.stem + ".kv.wav")
                        if abs(kv - 1) > 0.01 and subprocess.run(
                                ["ffmpeg", "-v", "error", "-y", "-i", str(out), "-af", f"atempo={kv:.3f}", str(tmp)],
                                capture_output=True).returncode == 0:
                            os.replace(tmp, out)
                    except Exception as e:  # noqa: BLE001
                        logging.warning(f"[fish nuvem] acelerar no código falhou ({type(e).__name__})")
                else:
                    _ritmo_fish(out, Path(pv).name, it["texto"], it["i"], _impactos_do(audio_dir), len(lines))
                g_ = _GOL_CTX.get(it["i"])  # 20/11: desfecho do gol — fim agudo (gol) ou voz engrossando (falha)
                if g_ and (g_[0] in ("gol", "falha") or (g_[0] == "grosso" and pv.name in FECHO_GROSSO_ST)):
                    _desfecho_gol(out, g_[0], pv.name)
                if _tem_respeito_piada(it["texto"], it["i"]):  # 20/11: S de "respeito" esticado (0,45 s), resto normal
                    _esticar_s_respeito(out, texto=it["texto"])
                if it.get("riso"):  # 20/11: frase tinha kkk -> risada REAL do narrador na frente (nunca a de robô)
                    _risada_real(Path(pv).name, out)
                if it["i"] == len(lines) - 1:
                    _aplicar_margem_final(out)
        if feitos and os.environ.get("MISTURA_MODO") == "vigia":
            feitos = _vigiar_fish(audio_dir, feitos, pv.name)
        # 20/11 (revisão): os 3 passos repetiam microcortes e ritmo já feitos no "acelera no código" (efeito em dobro)
        if feitos and os.environ.get("FISH_PASSOS3") == "1" and os.environ.get("FISH_ACELERA_NO_CODIGO") != "1":
            _passos_antigos_no_fish(audio_dir, feitos, itens, lines)
        if feitos and os.environ.get("FISH_RVC") == "1":
            _rvc_por_cima_do_fish(audio_dir, feitos, pv.name)
        if feitos:
            (Path(audio_dir) / "_voz_online.json").write_text(json.dumps(
                {"motor": "fish_nuvem", "frases": sorted(feitos), "total": len(itens)}), encoding="utf-8")
        logging.info(f"[fish nuvem] {len(feitos)}/{len(itens)} frases em {time.time() - t0:.0f}s "
                     f"(narrador {pv.name}); o resto no {_voz_modo()}")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[fish nuvem] falhou ({type(e).__name__}: {str(e)[:150]}) — tudo no {_voz_modo()}")


_TIPOS_DO_FISH = {"_piada", "_risada", "_mulher", "_personagem", "_irritado"}


def _frase_do_fish(i, subs, texto, riso):
    """20/11 dona: "a mistura dos 2 no MESMO áudio, aproveitando cada um" (Kitten: estável, menos erro, mas cadência de
    leitura; Fish: mais humano, mas erra e faz sons estranhos). Fish onde o humano faz mais diferença: piada,
    risada, mulher (duplo sentido), fala de personagem, irritado e o desfecho do gol ("isso!" / "não, não, galera!")."""
    if riso or subs.get(i) in _TIPOS_DO_FISH:
        return True
    # 20/11 dona (L): "erra na hora da briga — talvez o Fish não lide bem com acelerar; melhor acelerar como no Kitten,
    # cortando e aumentando a velocidade no código e não na geração". MISTURA_GOL_NO_FISH=0: gol/falha vão pro Kitten.
    if os.environ.get("MISTURA_GOL_NO_FISH", "1") == "0":
        return False
    g = _GOL_CTX.get(i)
    return bool(g and g[0] in ("gol", "falha"))


def _vigiar_fish(audio_dir, feitos, voz):
    """20/11 MISTURA "vigia": o Fish narra tudo e cada frase é MEDIDA; a que saiu estranha (tom fora do normal do
    narrador: engrossou/afinou demais; velocidade absurda; som cortado) é apagada e o Kitten refaz só ela.
    Medido contra a mediana das próprias frases do vídeo (o normal do Fish NESTE narrador)."""
    import numpy as np
    med = {}
    for i in feitos:
        w = Path(audio_dir) / f"audio_{i}.wav"
        try:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(w), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                                 capture_output=True).stdout
            a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
            f0 = []
            for k in range(0, len(a) - 1024, 320):
                fr = a[k:k + 1024] * np.hanning(1024)
                if np.sqrt(np.mean(fr ** 2)) < 0.02:
                    continue
                c = np.abs(np.fft.irfft(np.log(np.abs(np.fft.rfft(fr, 4096)) + 1e-9)))
                f0.append(16000 / (40 + np.argmax(c[40:228])))
            if len(f0) >= 8:
                f0 = np.array(f0)
                med[i] = (float(np.median(f0)), float(np.std(12 * np.log2(f0 / np.median(f0)))), len(a) / 16000)
        except Exception:  # noqa: BLE001
            pass
    if len(med) < 4:
        return feitos
    base = float(np.median([m[0] for m in med.values()]))
    var = float(np.median([m[1] for m in med.values()]))
    tira = []
    for i, (f, dv, d) in med.items():
        st = 12 * np.log2(f / base)
        if abs(st) > float(os.environ.get("MISTURA_VIGIA_ST", "3.0")) or dv > var * 1.8 or d < 0.4:
            tira.append(i)
    for i in tira:
        (Path(audio_dir) / f"audio_{i}.wav").unlink(missing_ok=True)
    logging.info(f"[mistura vigia] {voz}: {len(tira)}/{len(feitos)} frases do Fish saíram estranhas (tom/variação) "
                 f"-> o Kitten refaz: {sorted(tira)}")
    return [i for i in feitos if i not in tira]


def _passos_antigos_no_fish(audio_dir, feitos, itens, lines):
    """20/11 dona ("um terceiro com esses 3 passos"): as 3 técnicas do motor antigo que faltam no Fish —
    (1) microcortes (pausa interna longa vira curta, sem acelerar a fala); (2) tom que varia entre frases (±1,5 st,
    sorteio fixo pelo texto — quebra o "tudo igual"; com FISH_RVC o tom vai pro RVC, sem mexer no timbre aqui);
    (3) ritmo dentro da frase (alonga a última palavra e a de antes da vírgula; precisa do .words.json).
    FISH_PASSOS3=1 liga (teste)."""
    import hashlib
    txt = {it["i"]: it["texto"] for it in itens}
    for i in feitos:
        w = Path(audio_dir) / f"audio_{i}.wav"
        try:
            narracao_curva.microcortes(w)
        except Exception as e:  # noqa: BLE001
            logging.info(f"[fish passos] microcortes {w.name}: {e}")
        h = int(hashlib.md5(txt.get(i, "").encode("utf-8")).hexdigest(), 16)
        _FISH_TOM[i] = ((h % 7) - 3) * 0.5  # -1,5 .. +1,5 st
        wj = Path(str(w) + ".words.json")
        if wj.exists():
            try:
                pal = [(float(a), float(b), str(x)) for a, b, x in json.loads(wj.read_text(encoding="utf-8"))]
                import wave
                with wave.open(str(w)) as f_:
                    dur = f_.getnframes() / f_.getframerate()
                segs = narracao_curva._plano_ritmo(pal, txt.get(i, ""), dur, 0.12)
                if segs:
                    fc = "".join(f"[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,atempo={max(0.5, tp):.4f}[s{n}];"
                                 for n, (a, b, tp) in enumerate(segs))
                    fc += "".join(f"[s{n}]" for n in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[o]"
                    tmp = w.with_name(w.stem + ".rit.wav")
                    if subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-filter_complex", fc, "-map",
                                       "[o]", str(tmp)], capture_output=True).returncode == 0:
                        os.replace(tmp, w)
            except Exception as e:  # noqa: BLE001
                logging.info(f"[fish passos] ritmo {w.name}: {e}")
        if os.environ.get("FISH_RVC") != "1" and _FISH_TOM[i]:
            k = 2 ** (_FISH_TOM[i] / 12)
            tmp = w.with_name(w.stem + ".tom.wav")
            if subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-af",
                               f"asetrate=44100*{k:.5f},aresample=44100,atempo={1 / k:.5f}", str(tmp)],
                              capture_output=True).returncode == 0:
                os.replace(tmp, w)
    logging.info(f"[fish passos] microcortes + tom entre frases + ritmo em {len(feitos)} frases")


_FISH_TOM = {}


def _rvc_por_cima_do_fish(audio_dir, feitos, voz):
    import shutil
    """20/11 dona (comparação A/B/C: Fish "engrossa ou afina demais, parece que distorceu"; Kitten "muito igual"):
    une os dois — o Fish dá o JEITO de falar e o RVC do narrador (o mesmo do motor antigo) passa por cima e firma o
    TIMBRE. O Fish já sai no tom do narrador: o tom do RVC é zerado (cancela o tom da base). Precisa do Applio
    (VOZES_PY_NUVEM) e do .pth da voz. Falhou = fica o Fish como estava. FISH_RVC=1 liga (teste)."""
    try:
        pv = VOZES_DIR / voz
        if not (pv / f"{voz}.pth").exists() or not os.environ.get("VOZES_PY_NUVEM"):
            logging.info(f"[fish+rvc] sem .pth de {voz} ou sem Applio — fica só o Fish")
            return
        tf = pv / "tom_2_edge_francisca.txt"
        tom_fr = int(tf.read_text().strip()) if tf.exists() else 0
        d = Path(audio_dir) / "_fish_antes_rvc"
        d.mkdir(exist_ok=True)
        itens = []
        for i in feitos:
            w = Path(audio_dir) / f"audio_{i}.wav"
            src = d / w.name
            shutil.copy(w, src)
            itens.append({"saida": str(w), "entrada": str(src), "texto": "", "tom_base": "2_edge_francisca",
                          "tom_extra": -tom_fr + int(round(_FISH_TOM.get(i, 0))), "protect": 0.45, "index_rate": 0.6,
                          "volume_envelope": 1.0})
        lj = d / "lista.json"
        lj.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
        # 21/11 tarde: 2 placas quando a outra está livre
        _lote_em_placas([os.environ["VOZES_PY_NUVEM"], str(Path(__file__).with_name("voz_clonada_nuvem.py")), "lote",
                         voz], itens, d, "rvc", 3 * 3600, env={**os.environ, "VOZES_DIR": str(VOZES_DIR)},
                        pronto=lambda it: Path(it["saida"]).stat().st_mtime > Path(it["entrada"]).stat().st_mtime)
        ok = sum(1 for i in feitos if (Path(audio_dir) / f"audio_{i}.wav").stat().st_mtime >
                 (d / f"audio_{i}.wav").stat().st_mtime)
        cauda = ""
        if ok < len(feitos) and (d / "_rvc.log").exists():
            cauda = (d / "_rvc.log").read_text(encoding="utf-8", errors="ignore")[-300:]
        logging.info(f"[fish+rvc] {ok}/{len(feitos)} frases com o RVC de {voz} por cima {cauda}")
        for i in feitos:  # o RVC sai no volume dele: nivela de novo como o resto
            try:
                narracao_curva.pos_processar(Path(audio_dir) / f"audio_{i}.wav", 0.0)
            except Exception:  # noqa: BLE001
                pass
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[fish+rvc] falhou ({type(e).__name__}: {str(e)[:150]}) — fica só o Fish")


def _narrar_online(lines, audio_dir, so=None):
    """18/11 dona: "quando for Shorts, priorizar gerar o áudio online e aí monta; se não houver créditos usa o mesmo p3
    com técnicas". VOZ_ONLINE=fish (ligado só no pedido de Short) -> narra pelo Fish Audio (voz do narrador do Chris,
    comum/fish_audio/fish_lote.py, conta escolhida pelo creditos.json, IP fixo de cada conta). Cada audio_i.wav que
    sai online fica pronto e o laço do preparar_clone pula (já pulava wav existente); o resto segue no p3. Nunca
    levanta. Personagem com voz própria (mascote/falas) não passa aqui: só as frases desta chamada (so)."""
    if os.environ.get("VOZ_ONLINE", "").strip().lower() != "fish" or _OUTRA or motor_antigo():
        return
    try:
        sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
        import fish_lote
        # 19/11: QUEM fala. Narrador do vídeo (so=None, ou VOZ_CLONADA = narrador escolhido) -> voz do nicho (Chris /
        # Neymar no esporte). Fala de PERSONAGEM (_falas_personagem / revezamento põe VOZ_CLONADA=<personagem>) -> a
        # voz DELE no site (vozes_site.json); personagem sem voz no site = não narra online (segue no RVC dele) —
        # antes a fala do Goku sairia na voz do narrador do Chris.
        voz_site = None
        quem = (os.environ.get("VOZ_CLONADA") or "").strip()
        narrador = (os.environ.get("VOZ_ONLINE_NARRADOR") or "").strip()
        if so is not None and quem and quem != narrador:
            try:
                mapa = json.loads(Path(r"D:\hipercool-materiais\comum\fish_audio\vozes_site.json").read_text(
                    encoding="utf-8"))
                voz_site = (mapa.get(Path(quem).name) or {}).get("id")
            except (OSError, ValueError):
                voz_site = None
            if not voz_site:
                return
        ped = []
        for i, line in enumerate(lines):
            if so is not None and i not in so:
                continue
            out = Path(audio_dir) / f"audio_{i}.wav"
            if out.exists() and out.stat().st_size > 500:
                continue
            texto = _seguro(line)
            if texto.strip():
                ped.append((i, texto, str(out)))
        if not ped:
            return
        feitos = fish_lote.gerar(ped, log=lambda m: logging.info(m), voz=voz_site)
        if feitos:
            for i in feitos:  # nivela + efeito da voz; mesma cauda/margem das outras bases na última frase
                _acabamento_fish(Path(audio_dir) / f"audio_{i}.wav", os.environ.get("VOZ_CLONADA") or "")
                if i == len(lines) - 1:
                    _aplicar_margem_final(Path(audio_dir) / f"audio_{i}.wav")
            (Path(audio_dir) / "_voz_online.json").write_text(json.dumps(
                {"motor": "fish", "frases": sorted(feitos), "total": len(ped)}), encoding="utf-8")
        logging.info(f"[online] Fish: {len(feitos)}/{len(ped)} frases; o resto no {_voz_modo()}")
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[online] Fish falhou ({type(e).__name__}: {str(e)[:120]}) — tudo no {_voz_modo()}")


def preparar_clone(lines, audio_dir, impactos, so=None, abertura=True):
    """Narra TODAS as frases com a voz clonada antes da montagem (o loop do anime_segments acha os wavs prontos).
    Uma chamada só ao voz_clonada.py lote: o Applio carrega 1x (frase a frase era ~1 min de carga cada).
    Falhou = levanta: vídeo com metade da voz clonada não pode sair."""
    voz, modo = os.environ["VOZ_CLONADA"], os.environ.get("VOZ_CLONADA_BASE", "francisca")
    _SEGUIDA.update(base=None, s=0.0, calma=None)  # 18/11: revezamento do p3 começa limpo em cada chamada
    perfil = _perfil_v2(voz)
    audio_dir = Path(audio_dir)
    # 19/11 dona — ordem da voz: Fish Speech na GPU (Kaggle, narrador com trecho original) -> Fish online (Short no
    # PC1, conta com crédito) -> o modo de sempre (Kitten no Kaggle / p3 com mistura nos PCs). Cada um só narra o que
    # ainda não tem audio_i.wav; o que falhar segue para o próximo.
    _audio_pronto_do_drive(audio_dir, lines)  # 21/11: voz gerada antes (Qwen3/S2-Pro); 22/11: casa pelo TEXTO
    _narrar_s2pro(lines, audio_dir, so)  # 22/11: S2-Pro (misto = só emoção / pro = tudo) antes do XTTS
    _narrar_xtts(lines, audio_dir, so)  # 21/11: XTTS (motor_voz.json "motor": "xtts") vem antes do Fish
    _narrar_fish_nuvem(lines, audio_dir, so)
    _narrar_online(lines, audio_dir, so)
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
    try:
        _preparar_subvoz_kitten(lines, audio_dir, voz)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[kitten sub] desligado neste vídeo ({type(e).__name__}: {e})")
        _SUB_KITTEN.clear()
    for i, line in enumerate(lines):
        if so is not None and i not in so:  # revezamento (26/10): esta chamada narra só o bloco desta voz
            continue
        out = audio_dir / f"audio_{i}.wav"
        if out.exists() and out.stat().st_size > 500:
            if i == len(lines) - 1:
                _aplicar_margem_final(out)
            continue
        texto = _seguro(line)
        if not motor_antigo() or _SUB_KITTEN.get("_ligado"):
            texto = _pergunta_ao_publico(texto)  # 20/11: "Eu faria esse acordo! ... E vocês, fariam esse acordo?"
        aj = None
        if climas:
            try:
                aj = climas_voz.ajustes(voz, climas, i)
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[clone] clima da frase {i} falhou ({e}) — normal")
        # 18/11: no p3 quem escolhe a base é o revezamento (o clima continua mudando tom, ritmo e pausa da frase);
        # antes o clima trocava a base sozinho (tensão/épico -> Francisca, ação -> Kokoro)
        if _voz_modo() in ("p3", "kitten_tudo"):
            base = base_da_frase(modo, texto, i, impactos, len(lines))
        else:
            base = (aj or {}).get("base") or base_da_frase(modo, texto, i, impactos, len(lines))
        if base == "kokoro" and not _KOKORO_OK:  # 26/10 (dona: "as vozes clonadas dos Cortes"): só sem o modelo
            base = "francisca"
        if base == "kitten" and not _kitten_pronto():
            base = "kokoro" if _KOKORO_OK else "francisca"
        if base == "piper" and not _piper_pronto():
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
            if i == len(lines) - 1:
                cauda = max(cauda or 0.25, 1.5)
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
                if base in ("kokoro", "piper", "kitten"):
                    vel = round(max(0.75, min(1.6, (vel or 1.0) * aj["vel"])), 2)
                else:
                    rate = f"{int(round(max(-40, min(70, int(str(rate).rstrip('%')) + aj['rate'])))):+d}%"
                extra, ganho, cauda, eco = ex, ganho + aj["db"], max(0.05, cauda + aj["pausa"]), aj["eco"]
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[clone] ajuste do clima na frase {i} falhou ({e}) — normal")
        sub_k = _SUB_KITTEN.get(i)
        if sub_k:  # 20/11: sub-voz no motor antigo = o jeito do tipo MEDIDO nas falas reais (somado ao da frase)
            extra = dict(extra)
            extra["tom_extra"] = int(extra.get("tom_extra", 0)) + int(sub_k.get("tom_extra", 0))
            extra["f0_escala"] = round(float(extra.get("f0_escala", 1.0)) * float(sub_k.get("f0_escala", 1.0)), 3)
            extra["final_st"] = round(float(extra.get("final_st", 0) or 0) + float(sub_k.get("final_st", 0)), 2)
            if base in ("kokoro", "piper", "kitten"):
                vel = round(max(0.8, min(1.4, (vel or 1.0) * float(sub_k.get("velocidade", 1.0)))), 2)
        if os.environ.get("VOZ_CLONADA_CONFIG") == "2":  # timbre forte (anime_voz_clonada.CONFIGS)
            extra = {**extra, "index_rate": 0.8, "protect": 0.33, "volume_envelope": 0.8}
        resumo.append({"i": i, "base": base, "rate": rate if base not in ("kokoro", "piper", "kitten") else f"x{vel}", "clima": (aj or {}).get("clima", "normal"),
                       "tom_extra": int(extra.get("tom_extra", 0)), "index_rate": extra.get("index_rate", 0.5),
                       "protect": extra.get("protect", 0.33), "volume_envelope": extra.get("volume_envelope", 1.0),
                       "texto": texto})
        sidecar = None
        if base == "kokoro":
            itens.append({"saida": str(out), "tom_base": "1_kokoro", "texto": texto, "velocidade": round(vel, 2),
                          **extra})
        elif base == "kitten":  # 18/11: kitten_tudo — o voz_clonada_nuvem gera todas de uma vez (voz "Portuguese")
            itens.append({"saida": str(out), "tom_base": "4_kitten", "motor": "kitten", "texto": texto,
                          "velocidade": round(vel or 1.0, 2), **extra})
        elif base == "piper":  # 18/11: 3ª base do p3, gerada no lote como o Kokoro (voz_clonada._piper)
            itens.append({"saida": str(out), "tom_base": "3_piper", "motor": "piper", "texto": texto,
                          "velocidade": round(vel or 1.0, 2), **extra})
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
        _proteger_cauda_bruto(bases / f"audio_{i}.wav")
    for it in itens:
        if "entrada" in it and Path(it["entrada"]).exists():
            _proteger_cauda_bruto(it["entrada"])
    if not itens:
        # 19/11 (revisão): com o Fish narrando TUDO, itens fica vazio — antes saía aqui e pulava a abertura com o
        # trecho ORIGINAL do personagem e o resumo. Agora só pula o lote do RVC e segue para o fim.
        if any((audio_dir / f"audio_{i}.wav").exists() for i in range(len(lines))
               if so is None or i in so):
            _fechar_clone(lines, audio_dir, so, abertura, voz, resumo, itens, modo, perfil)
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
        if _SUB_KITTEN.get("_ligado"):  # 20/11: o que fizemos no Fish, agora no Kitten (mesmas funções)
            try:
                # só o ritmo pelo CONTEÚDO e o gol: a curva do locutor o motor antigo já aplicou (escala 0 = sem repetir)
                _esc = os.environ.get("FISH_RITMO_ESCALA")
                os.environ["FISH_RITMO_ESCALA"] = "0"
                try:
                    _ritmo_fish(out, Path(voz).name, texto, idx, impactos, len(lines))
                finally:
                    if _esc is None:
                        os.environ.pop("FISH_RITMO_ESCALA", None)
                    else:
                        os.environ["FISH_RITMO_ESCALA"] = _esc
                g_ = _GOL_CTX.get(idx)
                if g_ and (g_[0] in ("gol", "falha") or (g_[0] == "grosso" and Path(voz).name in FECHO_GROSSO_ST)):
                    _desfecho_gol(out, g_[0], Path(voz).name)
                if _tem_respeito_piada(texto, idx):
                    _esticar_s_respeito(out, texto=texto)
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[kitten sub] pós da frase {idx} falhou ({type(e).__name__}: {e})")
            # 20/11 dona (ouvindo F x G): "de toda forma têm que ter aqueles microcortes e talvez ser mais rápidos".
            # KITTEN_MICROCORTES=1 encurta as pausas dentro da frase; KITTEN_VEL=<fator> acelera a frase inteira
            # (atempo: muda a velocidade sem mudar o tom)
            try:
                if os.environ.get("KITTEN_CADENCIA") == "1":
                    _cadencia_quebrada(out)
                if os.environ.get("KITTEN_MICROCORTES") == "1":
                    narracao_curva.microcortes(out)
                kv_ = os.environ.get("KITTEN_VEL", "1") or "1"
                kv = _vel_por_frase(texto, idx) if kv_ == "auto" else float(kv_)
                # 20/11 noite (dona, Q: "tem que reduzir a velocidade dela um pouco"): KITTEN_VEL_FORCA < 1 suaviza
                kv = 1 + (kv - 1) * float(os.environ.get("KITTEN_VEL_FORCA", "1") or 1)
                if abs(kv - 1) > 0.01:
                    tmp = out.with_name(out.stem + ".kv.wav")
                    if subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-af", f"atempo={kv:.3f}",
                                       str(tmp)], capture_output=True).returncode == 0:
                        os.replace(tmp, out)
                        wj = Path(str(out) + ".words.json")
                        if wj.exists():
                            ws = json.loads(wj.read_text(encoding="utf-8"))
                            wj.write_text(json.dumps([[round(a / kv, 3), round(b / kv, 3), *r_] for a, b, *r_ in ws],
                                                     ensure_ascii=False), encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[kitten sub] microcortes/velocidade da frase {idx} falhou ({type(e).__name__}: {e})")
        if idx == len(lines) - 1:
            _aplicar_margem_final(out)
    _fechar_clone(lines, audio_dir, so, abertura, voz, resumo, itens, modo, perfil)


def _enfase_respeito(wav, ini, fim, s0, s1, alvo_s, en):
    """Monta re | S | peito com ênfase (ver _esticar_s_respeito). Falhou = False (aí fica só o S)."""
    try:
        sr = 44100
        fmt = f"aformat=sample_fmts=fltp:sample_rates={sr}:channel_layouts=stereo"

        def tom(st_):
            r_ = 2 ** (st_ / 12)
            return f"asetrate={sr * r_:.0f},aresample={sr},atempo={1 / r_:.4f}"
        d = s1 - s0
        w0 = max(0.02, min(ini, s0 - 0.04))
        w1 = max(s1 + 0.08, fim)
        re_f = f",volume=1.5,{tom(1.0)}" if en in ("res", "tudo", "separado") else ""
        pe_f = f",volume=1.2,{tom(-1.5)},atempo=0.92" if en in ("peito", "tudo", "separado") else ""
        s_f = ",volume=1.3" if en in ("res", "tudo") else ""
        cad = []
        if alvo_s > d + 0.02:
            f = d / alvo_s
            while f < 0.5:
                cad.append("atempo=0.5")
                f /= 0.5
            cad.append(f"atempo={f:.4f}")
        s_chain = ("," + ",".join(cad)) if cad else ""
        dur_s = max(d, alvo_s)
        pausa = f"aevalsrc=0|0:d=0.15:s={sr},{fmt}[z];" if en == "separado" else ""
        fc = (f"[0:a]atrim=0:{w0:.3f},asetpts=PTS-STARTPTS,{fmt}[a0];"
              f"[0:a]atrim={w0:.3f}:{s0:.3f},asetpts=PTS-STARTPTS{re_f},{fmt}[a1];"
              f"[0:a]atrim={s0:.3f}:{s1:.3f},asetpts=PTS-STARTPTS{s_chain}{s_f},afade=t=in:d=0.02,"
              f"afade=t=out:st={max(0, dur_s - 0.03):.3f}:d=0.03,{fmt}[s];" + pausa +
              f"[0:a]atrim={s1:.3f}:{w1:.3f},asetpts=PTS-STARTPTS{pe_f},{fmt}[b1];"
              f"[0:a]atrim={w1:.3f},asetpts=PTS-STARTPTS,{fmt}[b2];"
              f"[a0][a1][s]{'[z]' if pausa else ''}[b1][b2]concat=n={6 if pausa else 5}:v=0:a=1[o]")
        wav = Path(wav)
        tmp = wav.with_name(wav.stem + ".enf.wav")
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-filter_complex", fc, "-map", "[o]",
                            "-ar", str(sr), "-ac", "2", str(tmp)], capture_output=True, text=True)
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
            os.replace(tmp, wav)
            return True
        logging.info(f"[xtts] ênfase do respeito falhou: {r.stderr[-200:]}")
        tmp.unlink(missing_ok=True)
    except Exception as e:  # noqa: BLE001
        logging.info(f"[xtts] ênfase do respeito falhou ({type(e).__name__}: {e})")
    return False


def _cadencia_quebrada(w):
    """20/11 dona (Kitten isolado: a K7 "cadência" e as com p3 ficaram melhores; "o problema do Kitten é a cadência,
    parece que está lendo"): os pedaços da frase entre as pausas vão em velocidades diferentes — o 1º normal, os do
    meio mais rápidos (1,10-1,18), o último segurado (0,92) — e a pausa entre eles curta (fala, não leitura).
    KITTEN_CADENCIA=1 liga."""
    w = Path(w)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(w)],
                             capture_output=True, text=True).stdout or 0)
    if d < 1.2:
        return
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(w), "-af", "silencedetect=noise=-38dB:d=0.12", "-f", "null",
                        "-"], capture_output=True, text=True)
    ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    pecas, ini = [], 0.0
    for a, b in zip(ss, se):
        if a - ini > 0.25 and b < d - 0.05:
            pecas.append((ini, a))
            ini = b
    pecas.append((ini, d))
    if len(pecas) < 2:
        pecas = [(0.0, d * 0.55), (d * 0.55, d)]
    n = len(pecas)
    vel = ([1.0] + [1.10 + 0.04 * (k % 3) for k in range(1, n - 1)] + [0.92]) if n > 2 else [1.12, 0.94]
    fc, partes = "", []
    for k, ((a, b), v) in enumerate(zip(pecas, vel)):
        fc += f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,atempo={v:.3f},aformat=channel_layouts=stereo[p{k}];"
        partes.append(f"[p{k}]")
        if k < n - 1:
            fc += f"aevalsrc=0|0:d=0.09:s=44100[z{k}];"  # estéreo como os pedaços
            partes.append(f"[z{k}]")
    fc += "".join(partes) + f"concat=n={len(partes)}:v=0:a=1[o]"
    tmp = w.with_name(w.stem + ".cad.wav")
    if subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-filter_complex", fc, "-map", "[o]", "-ar",
                       "44100", "-ac", "2", str(tmp)], capture_output=True).returncode == 0 and tmp.exists():
        os.replace(tmp, w)
        Path(str(w) + ".words.json").unlink(missing_ok=True)  # tempos mudaram por pedaço: a legenda remede


def _vel_por_frase(texto, idx):
    """20/11 dona (J +10% e K +18% ficaram melhores): "a velocidade não precisa ser fixa — mais lenta quando for melhor
    e mais rápida quando for melhor, como o gol". Base +14% (entre J e K); corrida pro gol vai subindo até +30%;
    gol +28%; metralhadora/ação +22%; falha, deboche, piada (fim lento já aplicado) e pena ficam perto do normal."""
    g = _GOL_CTX.get(idx)
    sub = _SUB_KITTEN.get(idx) or {}
    v = 1.14
    if g and g[0] == "sobe":
        v = 1.14 + 0.16 * (g[1] / max(1, g[2] - 1))
    elif g and g[0] == "gol":
        v = 1.28
    elif g and g[0] in ("falha", "grosso"):
        v = 1.02
    elif sub.get("velocidade", 1) >= 1.2:  # metralhadora / risada medida rápida
        v = 1.22
    elif _frase_lenta(texto):
        v = 1.04
    return v


_SUB_KITTEN = {}  # {i: parâmetros da sub-voz medida} + "_ligado" — preenchido por _preparar_subvoz_kitten


def _preparar_subvoz_kitten(lines, audio_dir, voz):
    """20/11 dona: "o que pedi era SÓ o Kitten — ajustando ele como fizemos no Fish (sub-vozes, mulher, metralhadora,
    piada, risada...), olhando as melhores e vendo se na hora de juntar ele sai homogêneo; refazer todo o trabalho que
    fizemos no Fish, só que no Kitten". O Kitten não copia jeito de ninguém: a sub-voz vira PARÂMETROS medidos nas falas
    reais do narrador (config/subvozes_kitten.json: tom, melodia, fim da frase, velocidade de cada tipo em relação ao
    normal dele). A escolha do tipo por frase é a MESMA do Fish (_subvoz_por_frase); depois do RVC entram as mesmas
    técnicas do Fish (ritmo pelo conteúdo, aceleração do gol, fecho grosso, S do respeito). KITTEN_SUBVOZ=1 liga."""
    _SUB_KITTEN.clear()
    _GOL_CTX.clear()
    if os.environ.get("KITTEN_SUBVOZ") != "1":
        return
    nome = Path(voz).name
    try:
        tab = json.loads((Path(__file__).resolve().parents[1] / "config" / "subvozes_kitten.json")
                         .read_text(encoding="utf-8")).get(nome) or {}
    except (OSError, ValueError):
        tab = {}
    forca = float(os.environ.get("KITTEN_SUBVOZ_FORCA", "1") or 1)

    subs = _subvoz_por_frase(lines, audio_dir, None, tem={k for k in tab if k.startswith("_") and k != "_normal"})
    subs = {i: s_ for i, s_ in subs.items() if s_ != "_todas"}  # "todas juntas" é coisa do Fish
    for i, s in subs.items():
        p = tab.get(s)
        if not p:
            continue
        _SUB_KITTEN[i] = {"tom_extra": round(p.get("tom_extra", 0) * forca),
                          "f0_escala": round(1 + (p.get("f0_escala", 1.0) - 1) * forca, 3),
                          "final_st": round(p.get("final_st", 0.0) * forca, 2),
                          "velocidade": round(1 + (p.get("velocidade", 1.0) - 1) * forca, 3)}
        # 20/11 dona (teste K: K9/K10 entre as melhores = tom da voz intacto): KITTEN_SUBVOZ_TOM=0 não mexe no tom nem
        # na melodia; KITTEN_SUBVOZ_FIM=0 também não mexe no fim da frase (K9). Só a velocidade do tipo fica.
        if os.environ.get("KITTEN_SUBVOZ_TOM") == "0":
            _SUB_KITTEN[i].update(tom_extra=0, f0_escala=1.0)
        if os.environ.get("KITTEN_SUBVOZ_FIM") == "0":
            _SUB_KITTEN[i]["final_st"] = 0.0
        _SUB_KITTEN[i]["velocidade"] = max(1.0, _SUB_KITTEN[i]["velocidade"])  # o tipo nunca deixa mais lento
    try:
        import climas_voz
        _marcar_gol(lines, climas_voz.escolher([_seguro(x) for x in lines], audio_dir))
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[kitten sub] gol desligado ({type(e).__name__})")
    _SUB_KITTEN["_ligado"] = True
    logging.info(f"[kitten sub] {nome}: {len(subs)} frases com sub-voz medida "
                 f"({sorted(set(subs.values()))}), força {forca}")


def _fechar_clone(lines, audio_dir, so, abertura, voz, resumo, itens, modo, perfil):
    """Fim do preparar_clone: margem final, abertura com o trecho ORIGINAL do personagem e o resumo. Separado em
    19/11 para o caminho do Fish (que não passa pelo lote do RVC) também ter a abertura."""
    audio_dir = Path(audio_dir)
    if lines and (so is None or (len(lines) - 1) in so):
        _aplicar_margem_final(audio_dir / f"audio_{len(lines) - 1}.wav")
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
GEMINI_TEXTO = os.environ.get("GEMINI_TEXTO_VIDEO", "antigravity/gemini-3-flash")


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
    for m in (GEMINI_TEXTO, None):
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
    if lines:
        _aplicar_margem_final(Path(audio_dir) / f"audio_{len(lines) - 1}.wav")


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
        if indice is not None and total is not None and indice == total - 1:
            _aplicar_margem_final(out_wav)
        return out_wav

    # ── SEGUNDA CAMADA anti-ban: garante que nenhum termo de risco chegue ao TTS ──
    safe_text = _pronuncia(viralizador.anti_ban(text))
    if os.environ.get("VIRAL_SLANG") == "1":
        safe_text = viralizador.viralizar(safe_text)

    rate = pitch = None
    ganho, cauda = 0.0, None
    if indice is not None and narracao_curva.ligado():
        rate, pitch, ganho, cauda = narracao_curva.prosodia(safe_text, indice, impactos, total)
        if total is not None and indice == total - 1:
            cauda = max(cauda or 0.25, 1.5)
    ok = edge_tts_engine.speak(safe_text, voice=NARRATOR_VOICE,
                               out_wav=str(out_wav), persona="Narrador", rate=rate, pitch=pitch)
    if not ok:
        logging.error(f"[anime_tts] TTS falhou: {text[:60]!r}")
        return None
    if cauda is not None:
        narracao_curva.pos_processar(out_wav, ganho, cauda)
        narracao_curva.humanizar(out_wav, safe_text, indice, impactos, total)
        logging.info(f"[curva] frase {indice}: {rate} {pitch} {ganho:+.1f} dB")
    if indice is not None and total is not None and indice == total - 1:
        _aplicar_margem_final(out_wav)

    return out_wav
