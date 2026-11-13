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
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# viralizador.py vive no mesmo diretório
sys.path.insert(0, str(Path(__file__).resolve().parent))

import edge_tts_engine
import narracao_curva
import viralizador

NARRATOR_VOICE = "pt-BR-ThalitaMultilingualNeural"  # Francisca PROIBIDA (dono 15/10); Thalita = aprovada
# ANIME_TTS_VOICE: versões em outra língua (anime_idiomas, 16/10) usam a voz de narrador do canal daquela língua
NARRATOR_VOICE = os.environ.get("ANIME_TTS_VOICE") or NARRATOR_VOICE

# Voz clonada dos narradores parceiros (dono 19/10): VOZ_CLONADA=<narrador> + VOZ_CLONADA_BASE=francisca|kokoro|misto.
# A frase sai da voz base e o RVC troca o timbre pelo do parceiro (D:\hipercool-materiais\bin\voz_clonada.py).
# Dono ouvindo as amostras: Francisca + clone = pronúncia perfeita; Kokoro + clone = emoção e fala acelerada
# ("narração de jogo"); Andrew + clone = sotaque de gringo (não usar).
VOZES_PY = Path(r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe")
VOZ_CLONADA_PY = Path(r"D:\hipercool-materiais\bin\voz_clonada.py")
FRANCISCA = "pt-BR-FranciscaNeural"  # o edge_tts_engine ainda troca pela Thalita (trava antiga); com VOZ_CLONADA passa


def _seguro(text):
    t = viralizador.anti_ban(text)
    return viralizador.viralizar(t) if os.environ.get("VIRAL_SLANG") == "1" else t


def clone_ligado():
    return bool(os.environ.get("VOZ_CLONADA"))


def base_da_frase(modo, texto, indice, impactos, total):
    """misto: Kokoro (emoção, acelerado) na abertura e chegando nos impactos (a curva sobe 8%+), Francisca (pronúncia)
    no resto — mesmo timbre, ritmo que muda como o de um narrador humano."""
    if modo != "misto":
        return modo
    return "kokoro" if indice == 0 or narracao_curva.deltas(texto, indice, impactos, total)[0] >= 8 else "francisca"


def _perfil_v2(voz):
    """Clone 2.0 (dono 19/10): perfil de fala do narrador medido no material real (D:\\hipercool-materiais\\bin\\
    clone2.py). Só com VOZ_CLONADA_VERSAO=2; sem perfil = v1."""
    if os.environ.get("VOZ_CLONADA_VERSAO") != "2":
        return None
    arq = Path(r"D:\hipercool-materiais\models\rvc\vozes") / voz / "perfil_v2.json"
    if not arq.exists():
        logging.warning(f"[clone] v2 pedido mas {voz} sem perfil_v2.json — v1")
        return None
    return json.loads(arq.read_text(encoding="utf-8"))["aplicar"]


def _frase_v2(a, base, texto, indice, impactos, total, chave):
    """Ritmo, pausa, volume e entonação DO NARRADOR em cima da curva de locutor: velocidade base dele, amplitude da
    curva e do volume na medida dele, pausa dele, tom que varia entre frases como o dele, faixa de entonação, EQ e o
    jeito dele de fechar a frase (final_st, na força que o narracao_curva.variacao der pra esta frase)."""
    import hashlib
    dr, dp, dg, _cauda = narracao_curva.deltas(texto, indice, impactos, total)
    dr2 = dr * a["curva_rate"]
    cauda = a["cauda_impacto"] if indice in (impactos or []) else a["cauda"]
    ruido = (int(hashlib.md5(texto.encode("utf-8")).hexdigest(), 16) % 5 - 2) / 4
    tom_extra = int(round(max(-2.0, min(2.0, (dr / narracao_curva.PICO_RATE + ruido) * a["tom_extra_st"]))))
    extra = {"tom_extra": tom_extra, "f0_escala": a[base]["f0_escala"], "eq": a[base]["eq"]}
    v = narracao_curva.variacao(chave, indice, texto, impactos, total)
    extra["index_rate"] = v["index_rate"]
    extra["protect"] = v["protect"]
    extra["volume_envelope"] = v["volume_envelope"]
    extra["contour"] = v.get("contour")
    if a[base].get("final_st"):
        extra["final_st"] = round(a[base]["final_st"] * v["final_mult"], 2)
    if base == "kokoro":
        vel = max(0.75, min(1.6, a["kokoro"]["velocidade"] * (1 + dr2 / 100)))
        return extra, f"x{vel:.2f}", None, dg * a["curva_ganho"], cauda, round(vel, 2)
    rate = int(round(max(-40, min(70, a["francisca"]["rate"] + dr2))))
    return extra, f"{rate:+d}%", f"{dp:+d}Hz", dg * a["curva_ganho"], cauda, None


def preparar_clone(lines, audio_dir, impactos):
    """Narra TODAS as frases com a voz clonada antes da montagem (o loop do anime_segments acha os wavs prontos).
    Uma chamada só ao voz_clonada.py lote: o Applio carrega 1x (frase a frase era ~1 min de carga cada).
    Falhou = levanta: vídeo com metade da voz clonada não pode sair."""
    voz, modo = os.environ["VOZ_CLONADA"], os.environ.get("VOZ_CLONADA_BASE", "francisca")
    perfil = _perfil_v2(voz)
    audio_dir = Path(audio_dir)
    bases = audio_dir / "_base_clone"
    bases.mkdir(parents=True, exist_ok=True)
    itens, depois = [], []
    for i, line in enumerate(lines):
        out = audio_dir / f"audio_{i}.wav"
        if out.exists() and out.stat().st_size > 500:
            continue
        texto = _seguro(line)
        base = base_da_frase(modo, texto, i, impactos, len(lines))
        if perfil:
            extra, rate, pitch, ganho, cauda, vel = _frase_v2(perfil, base, texto, i, impactos, len(lines),
                                                              str(audio_dir))
        else:
            rate, pitch, ganho, cauda = narracao_curva.prosodia(texto, i, impactos, len(lines))
            extra, vel = {}, max(0.85, min(1.35, 1 + int(rate.rstrip("%")) / 100))
        sidecar = None
        if base == "kokoro":
            itens.append({"saida": str(out), "tom_base": "1_kokoro", "texto": texto, "velocidade": round(vel, 2),
                          **extra})
        else:
            bruto = bases / f"audio_{i}.wav"
            if not edge_tts_engine.speak(texto, voice=FRANCISCA, out_wav=str(bruto), persona="Narrador",
                                         rate=rate, pitch=pitch, contour=extra.get("contour")):
                raise RuntimeError(f"[clone] edge Francisca falhou na frase {i}")
            itens.append({"saida": str(out), "tom_base": "2_edge_francisca", "entrada": str(bruto), **extra})
            sidecar = Path(str(bruto) + ".words.json")
        depois.append((out, ganho, cauda, sidecar, i, texto))
        logging.info(f"[clone{' v2' if perfil else ''}] frase {i}: {base} {rate}"
                     + (f" tom{extra['tom_extra']:+d}" if extra else "")
                     + (f" fim{extra['final_st']:+.2f}st" if extra.get("final_st") else ""))
    if not itens:
        return
    lista = bases / "lista.json"
    lista.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
    with open(bases / "clone.log", "a", encoding="utf-8") as fh:
        r = subprocess.run([str(VOZES_PY), str(VOZ_CLONADA_PY), "lote", voz, str(lista)], stdout=fh,
                           stderr=subprocess.STDOUT, timeout=4 * 3600, creationflags=0x00004000 | 0x08000000)
    faltam = [str(o) for o, *_ in depois if not o.exists()]
    if r.returncode != 0 or faltam:
        raise RuntimeError(f"[clone] voz_clonada lote rc={r.returncode}, faltam {len(faltam)} (ver {bases / 'clone.log'})")
    for out, ganho, cauda, sidecar, idx, texto in depois:
        if sidecar and sidecar.exists():  # timing por palavra do edge vale: o RVC mantém a duração
            sidecar.replace(Path(str(out) + ".words.json"))
        narracao_curva.pos_processar(out, ganho, cauda)
        narracao_curva.humanizar(out, texto, idx, impactos, len(lines))
    logging.info(f"[clone] {len(itens)} frases com a voz de {voz} ({modo}{', v2' if perfil else ''})")


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
    safe_text = viralizador.anti_ban(text)
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
