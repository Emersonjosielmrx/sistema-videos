#!/usr/bin/env python3
"""Técnicas de áudio pra voz de IA soar humana (lista do dono, 17/10/2026). Tudo atrás de chave.

Chaves em config/fila.json -> "voz_humana" (narration.voz_humana). Desligadas até o dono ouvir as
amostras (bin/amostras_voz.py). O diagnóstico dele: "a voz de IA é muito estável: mesma velocidade
entre palavras, sem arrasto, todas no mesmo volume".

  ritmo_por_pedaco  (ideia 8)  fala do narrador gravada em pedaços (pela pontuação), cada um numa
                               velocidade um pouco diferente, e colada com micro-pausas variadas.
  gemini_nos_picos  (ideia 11) as falas do narrador coladas no clímax vão pro Gemini TTS com instrução
                               de estilo (empolgação de quem conta fofoca); o resto fica no edge.
  pausa_variavel    (ideia 14) silêncio DEPOIS da fala que segue a curva: curto na subida, pausa de
                               suspense logo antes do impacto, longo no respiro.
  respiracao        (ideia 13) respiração real (assets/respiracoes, tirada das vozes humanas autorizadas)
                               ANTES de algumas falas: depois do impacto e antes de fala longa.

Tudo devolve/escreve wav 24 kHz mono, igual ao que o elenco já entrega pro clip.
"""
import hashlib
import json
import random
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log  # noqa: E402

SR = 24000
RESPIRACOES = PROJECT_DIR / "assets" / "respiracoes"
NARRADOR = ("narrador", "narradora", "narrator")
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Instrução de estilo do Gemini: ele lê a diretiva como estilo e não fala em voz alta (gemini_tts:
# SENSUAL_STYLE_PREFIX usa o mesmo mecanismo). Tom NÃO sobe: o dono reprovou voz "fina e aguda".
ESTILO_PICO = ("Narre como youtuber brasileiro contando a parte mais chocante de uma história pra um "
               "amigo: empolgado, acelerando, com ênfase nas palavras fortes, voz firme e grave, sem "
               "afinar: ")


def _rnd(*partes):
    """Sorteio estável por fala: a mesma fala sempre recebe a mesma pausa/respiração (cache não fura)."""
    return random.Random(hashlib.md5("|".join(map(str, partes)).encode()).hexdigest())


def _ff(args, timeout=120):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, args)], check=True, timeout=timeout,
                   capture_output=True, creationflags=_SEM_JANELA)


def duracao(wav):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                       capture_output=True, text=True, timeout=30, creationflags=_SEM_JANELA)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _eh_narrador(persona):
    return (persona or "").strip().lower() in NARRADOR


def posicao(indice, impactos):
    """'impacto' | 'antes' (1 fala antes) | 'subida' (2-4 antes) | 'respiro' (1-3 depois) | 'normal'."""
    if indice is None or not impactos:
        return "normal"
    if indice in impactos:
        return "impacto"
    if any(0 < indice - k <= 3 for k in impactos):
        return "respiro"
    falta = min((k - indice for k in impactos if k > indice), default=99)
    if falta == 1:
        return "antes"
    if falta <= 4:
        return "subida"
    return "normal"


# ─── ideia 14: pausa variável ────────────────────────────────────────────────
def pausa_depois(indice, impactos, texto=""):
    """Segundos de silêncio depois da fala. Humano não tem intervalo fixo: corre na subida, segura antes
    da revelação e respira depois dela."""
    # Medido em 17/10 (bin/medir_narradores.py, 11 canais x 40 vídeos): os humanos têm 0,2-1,4 pausas
    # de 1 s+ por minuto (cortam na edição); o nosso cap 5 tinha 5,8. Então quase tudo ENCURTA — o
    # silêncio longo fica só logo antes do impacto (~7 por capítulo, dentro da conta deles).
    r = _rnd("pausa", indice, texto)
    pos = posicao(indice, impactos)
    if pos == "antes":
        return r.uniform(0.55, 0.75)   # suspense: o silêncio antes do impacto
    if pos == "subida":
        return r.uniform(0.04, 0.12)   # atropelando, chegando no clímax
    if pos == "impacto":
        return r.uniform(0.4, 0.55)    # deixa o impacto bater
    if pos == "respiro":
        return r.uniform(0.3, 0.45)
    t = texto.rstrip()
    if t.endswith("?"):
        return r.uniform(0.3, 0.45)    # pergunta pede um respiro pra resposta
    return r.uniform(0.1, 0.3)


# ─── ideia 13: respiração ────────────────────────────────────────────────────
def _banco():
    try:
        return [RESPIRACOES / i["arquivo"] for i in json.loads((RESPIRACOES / "indice.json").read_text(encoding="utf-8"))
                if (RESPIRACOES / i["arquivo"]).exists()]
    except (OSError, ValueError):
        return []


def respiracao_antes(indice, impactos, texto, persona):
    """Arquivo de respiração pra pôr ANTES da fala, ou None. Só no narrador (a voz que conduz), e com
    moderação: as referências medidas em 17/10 quase não deixam respiração audível (cortam na edição)."""
    if not _eh_narrador(persona):
        return None
    banco = _banco()
    if not banco:
        return None
    r = _rnd("resp", indice, texto)
    pos = posicao(indice, impactos)
    longa = len((texto or "").split()) >= 18
    chance = 0.85 if pos == "respiro" and indice - 1 in (impactos or []) else (0.45 if longa else 0.12)
    if pos in ("subida", "antes"):
        chance = 0.0  # na corrida pro clímax não se para pra respirar
    return r.choice(banco) if r.random() < chance else None


# ─── ideia 8: ritmo por pedaço ───────────────────────────────────────────────
_CORTE = re.compile(r"(?<=[,;:!?…—])\s+|(?<=\.)\s+(?=[A-ZÀ-Ú])")


def pedacos(texto, minimo=3):
    """Divide a fala pela pontuação, juntando pedaço com menos de `minimo` palavras ao vizinho
    (pedaço de 1-2 palavras abre em palavra solta, que é justamente o que a voz erra)."""
    brutos = [p.strip() for p in _CORTE.split(texto or "") if p.strip()]
    out = []
    for p in brutos:
        if out and (len(out[-1].split()) < minimo or len(p.split()) < minimo):
            out[-1] = f"{out[-1]} {p}"
        else:
            out.append(p)
    return out


def _deslocar_rate(v, delta):
    try:
        base = int(str(v.get("rate", "+0%")).rstrip("%") or 0)
    except ValueError:
        base = 0
    return {**v, "rate": f"{max(-20, min(25, base + delta)):+d}%"}


def falar_em_pedacos(obra, texto, wav, persona, genero, indice=None, impactos=None, lang="pt", extra_rate=0):
    """Grava a fala em pedaços com velocidades diferentes. False = não deu (quem chama grava inteiro)."""
    import elenco
    ps = pedacos(texto)
    if len(ps) < 2:
        return False
    v, _g = elenco.voz(obra, persona, genero)
    v = _deslocar_rate(v, extra_rate)
    r = _rnd("pedaco", indice, texto)
    tmp = Path(wav).with_suffix("")
    partes = []
    try:
        for k, p in enumerate(ps):
            # 1º pedaço mais calmo, meio acelera, último segura: é o desenho de quem conta história
            base = -4 if k == 0 else (5 if k < len(ps) - 1 else -2)
            vk = _deslocar_rate(v, base + r.randint(-3, 3))
            w = Path(f"{tmp}_p{k}.wav")
            if not elenco.falar_edge(p, w, vk, f"{persona} pedaço {k + 1}", obra=obra, lang=lang,
                                     indice=indice, impactos=impactos):
                return False
            partes.append(w)
        filtros, entradas = [], []
        for k, w in enumerate(partes):
            entradas += ["-i", w]
            gap = r.uniform(0.05, 0.16) if k < len(partes) - 1 else 0.0
            filtros.append(f"[{k}:a]aresample={SR},apad=pad_dur={gap:.3f}[p{k}]")
        filtros.append("".join(f"[p{k}]" for k in range(len(partes))) + f"concat=n={len(partes)}:v=0:a=1[o]")
        _ff([*entradas, "-filter_complex", ";".join(filtros), "-map", "[o]", "-ar", SR, "-ac", 1, wav])
        return True
    except Exception as e:  # noqa: BLE001
        log(f"  [!] ritmo por pedaço falhou ({str(e)[:80]}) — fala inteira")
        return False
    finally:
        for w in partes:
            w.unlink(missing_ok=True)


# ─── ideia 11: Gemini com estilo nos picos ───────────────────────────────────
def eh_pico(indice, impactos):
    return posicao(indice, impactos) in ("impacto", "antes", "subida")


def falar_gemini_estilo(obra, texto, wav, persona, genero):
    """Fala do pico no Gemini TTS com instrução de estilo, na voz Gemini fixa do personagem.
    Sempre pelo proxy (GEMINI_TTS_PROXY_ENABLED=1, decisão do dono 15/10). False = não deu."""
    import os
    os.environ.setdefault("GEMINI_TTS_PROXY_ENABLED", "1")
    import elenco
    import gemini_tts
    _v, voz_g = elenco.voz(obra, persona, genero)
    bruto = Path(wav).with_suffix(".gem.wav")
    try:
        falado = elenco.aplicar_pronuncia(elenco.texto_para_voz(texto), obra)
        if not gemini_tts.speak(ESTILO_PICO + falado, voice=voz_g, out_wav=str(bruto), max_attempts=6):
            return False
        elenco._pos_processar(bruto, wav, 0.0)  # mesmo corte de cauda e nível das outras falas
        return True
    except Exception as e:  # noqa: BLE001
        log(f"  [!] Gemini no pico falhou ({str(e)[:80]}) — fica o edge")
        return False
    finally:
        bruto.unlink(missing_ok=True)


# ─── montagem da fala com pausa/respiração ───────────────────────────────────
def vestir(wav, indice, impactos, texto, persona, pausa=True, respirar=True):
    """Reescreve `wav` com respiração antes e pausa variável depois (o clip dura o wav). Devolve dict
    do que entrou. Falha = wav fica como estava."""
    resp = respiracao_antes(indice, impactos, texto, persona) if respirar else None
    seg = pausa_depois(indice, impactos, texto) if pausa else 0.0
    if not resp and seg <= 0:
        return {}
    tmp = Path(wav).with_suffix(".vest.wav")
    try:
        if resp:
            # respiração ~14 dB abaixo da fala, e 60 ms de silêncio entre ela e a voz
            filtro = (f"[1:a]aresample={SR},volume=-6dB,apad=pad_dur=0.06[r];[0:a]aresample={SR}[v];"
                      f"[r][v]concat=n=2:v=0:a=1,apad=pad_dur={seg:.3f}[o]")
            _ff(["-i", wav, "-i", resp, "-filter_complex", filtro, "-map", "[o]", "-ar", SR, "-ac", 1, tmp])
        else:
            _ff(["-i", wav, "-af", f"aresample={SR},apad=pad_dur={seg:.3f}", "-ar", SR, "-ac", 1, tmp])
        tmp.replace(wav)
        return {"respiracao": Path(resp).name if resp else None, "pausa": round(seg, 2)}
    except Exception as e:  # noqa: BLE001
        log(f"  [!] pausa/respiração falhou ({str(e)[:80]})")
        tmp.unlink(missing_ok=True)
        return {}
