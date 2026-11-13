# -*- coding: utf-8 -*-
"""elenco.py — VOZ FIXA POR OBRA E POR PERSONAGEM + motor de voz do português (edge ou Gemini).

Pedido do dono (15/10):
- narrador, protagonista e par principal com voz FIXA na obra (mudam de uma obra pra outra);
- cada personagem com a sua voz, sempre a mesma;
- testar o português só com as vozes edge Multilingual (rápido, sem cota) e variações virtuais delas.

Por que a voz trocava: o registro de vozes do Gemini (workspace/voices-registry.json) é UM SÓ pra todas as obras e
liga a voz ao NOME que a IA escreveu. Quando o roteiro chama o protagonista de "Rapaz" ou "Jovem", ele pegava a voz
daquele nome genérico (de outra obra; "Jovem" era até voz de mulher). Aqui:
  1. normalizar(): apelido conhecido vira o nome oficial; nome genérico ("Rapaz", "Jovem"...) com muitas falas num
     capítulo em que o protagonista (ou o par) não aparece pelo nome vira o protagonista (ou o par);
  2. voz por OBRA (config/elenco/<obra>.json): narrador, protagonista e par têm vozes reservadas; personagem novo
     ganha uma voz livre e fica com ela; figurante genérico usa vozes de figurante (nunca as reservadas).

Motor do português: config/fila.json "tts_motor"; env HIPER_TTS_MOTOR passa por cima.
  "edge"   = tudo no edge (rápido, sem cota) — teste do dono a partir do cap 9 do The Inheritor;
  "misto"  = narrador no edge (70-80% das falas) + personagens no Gemini com voz fixa (~20-30% das falas, poucas
             chamadas -> quase sem limite de cota); personagem não cai pro edge (voz não troca): espera o Gemini;
  "gemini" = tudo no Gemini (como era; ~70 min de voz por capítulo).
Trocar: python bin/elenco.py --motor edge|misto|gemini (ou os botões "VOZ - ..." na pasta Hipercool do desktop).
As outras línguas continuam no idiomas.falar (edge nativo da língua).

PROIBIDAS (dono, 15/10): pt-BR-AntonioNeural (voz masculina ruim), pt-BR-FranciscaNeural (aposentada),
it-IT-IsabellaNeural (italiana, fica com sotaque em português).
"""
import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from hp_common import PROJECT_DIR, log

PASTA = PROJECT_DIR / "config" / "elenco"
TTS_CACHE = PROJECT_DIR / "workspace" / "tts_cache"

PROIBIDAS = {"pt-BR-AntonioNeural", "pt-BR-FranciscaNeural", "it-IT-IsabellaNeural"}
# Multilingual = falam qualquer língua (o dono ouviu as amostras em pt e aprovou em 15/10)
EDGE_F = ["pt-BR-ThalitaMultilingualNeural", "en-US-AvaMultilingualNeural", "en-US-EmmaMultilingualNeural",
          "de-DE-SeraphinaMultilingualNeural", "fr-FR-VivienneMultilingualNeural"]
EDGE_M = ["en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural", "en-AU-WilliamMultilingualNeural",
          "de-DE-FlorianMultilingualNeural", "fr-FR-RemyMultilingualNeural", "it-IT-GiuseppeMultilingualNeural",
          "ko-KR-HyunsuMultilingualNeural"]
# variações virtuais (velocidade, tom): a 1ª é a voz pura. Faixa que ainda soa natural: -8..+15% e -8..+8 Hz.
VARIACOES = [("+0%", "+0Hz"), ("+8%", "+4Hz"), ("-6%", "-4Hz"), ("+12%", "+8Hz"), ("-8%", "-8Hz"),
             ("+4%", "-6Hz"), ("+0%", "+6Hz"), ("+15%", "+2Hz"), ("-4%", "+3Hz"), ("+6%", "-2Hz")]
GEMINI_F = ["Leda", "Aoede", "Zephyr", "Achernar", "Despina", "Erinome", "Pulcherrima", "Sulafat", "Vindemiatrix"]
GEMINI_M = ["Sadachbia", "Charon", "Puck", "Fenrir", "Orus", "Gacrux", "Iapetus", "Algenib", "Algieba", "Achird"]
NARRADOR = ("narrador", "narradora", "narrator", "voz off", "voz_off", "")
GENERICOS = {"rapaz", "garota", "garoto", "homem", "mulher", "menina", "menino", "desconhecido", "desconhecida",
             "personagem", "alguém", "alguem", "voz", "estranho", "estranha", "jovem", "moça", "moca", "velhote",
             "velho", "velha", "senhor", "senhora", "pessoa", "ela", "ele", "cara", "figura", "homem 1", "homem 2",
             "mulher 1", "mulher 2", "mulher desconhecida", "homem desconhecido", "rapaz desconhecido"}
MOTORES = ("edge", "misto", "gemini")
MIN_FALAS_PROTAGONISTA = 4  # genérico com pelo menos isso num capítulo sem o nome do protagonista = ele


def motor():
    m = os.environ.get("HIPER_TTS_MOTOR", "").strip().lower()
    if not m:
        try:
            m = json.loads((PROJECT_DIR / "config" / "fila.json").read_text(encoding="utf-8")).get("tts_motor", "")
        except (OSError, ValueError):
            m = ""
    return m if m in MOTORES else "gemini"


def obra_de(pasta_paineis):
    """'.../panels/the-inheritor-cap09' -> 'the-inheritor'."""
    return re.sub(r"-cap\d+$", "", Path(pasta_paineis).name)


def _limpo(persona):
    return re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona or "").strip()


def _e_generico(nome):
    n = _limpo(nome).lower()
    return n in GENERICOS or re.sub(r"\s+\d+$", "", n) in GENERICOS


def virtuais(genero):
    """Todas as vozes virtuais do gênero: primeiro cada voz base pura, depois as variações (base x tom/velocidade)."""
    bases = EDGE_F if genero == "F" else EDGE_M
    return [{"voice": b, "rate": r, "pitch": p} for r, p in VARIACOES for b in bases if b not in PROIBIDAS]


def _arq(obra):
    return PASTA / f"{obra}.json"


def _gravar(obra, el):
    PASTA.mkdir(parents=True, exist_ok=True)
    _arq(obra).write_text(json.dumps(el, ensure_ascii=False, indent=1), encoding="utf-8")


def _n(nome):
    return int(hashlib.md5(nome.encode("utf-8")).hexdigest(), 16)


def carregar(obra):
    """Elenco da obra (cria na 1ª vez: narrador sorteado pela obra, protagonista/par pelos roteiros já feitos)."""
    p = _arq(obra)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            log(f"  [!] elenco {p.name} ilegível — recriando")
    h = _n(obra)
    g = "F" if h % 2 else "M"
    el = {"_leia": ("Vozes fixas desta obra (bin/elenco.py). Pode editar à mão: edge = {voice, rate, pitch} "
                    "(vozes em EDGE_F/EDGE_M; PROIBIDAS: Antonio, Francisca, Isabella); gemini = nome da voz. "
                    "papel: protagonista | par | personagem | figurante. apelidos = outros nomes que a IA usa."),
          "obra": obra,
          "narrador": {"genero": g, "edge": {**virtuais(g)[h % len(EDGE_F if g == 'F' else EDGE_M)], "rate": "+5%"},
                       "gemini": "Kore" if g == "F" else "Charon"},
          "personagens": {}}
    try:  # protagonista e par = os 2 nomes com mais falas nos roteiros já feitos (um de cada gênero)
        from narration import personagens_anteriores
        conhecidos = personagens_anteriores(obra, 9999)
    except Exception:  # noqa: BLE001
        conhecidos = []
    for papel, gen in (("protagonista", "M"), ("par", "F")):
        c = next((c for c in conhecidos if c[1] == gen), None)
        if c:
            el["personagens"][c[0]] = {"papel": papel, "genero": gen, "apelidos": []}
    _gravar(obra, el)
    log(f"  elenco novo de {obra}: narrador {el['narrador']['edge']['voice']}, "
        f"{', '.join(f'{k} ({v['papel']})' for k, v in el['personagens'].items()) or 'sem protagonista ainda'}")
    return el


def _achar(el, persona):
    """Nome oficial do personagem (match exato, apelido ou token de nome em comum), ou None."""
    p = _limpo(persona)
    pl = p.lower()
    for nome, d in el["personagens"].items():
        if pl == nome.lower() or pl in (a.lower() for a in d.get("apelidos", [])):
            return nome
    if _e_generico(p):
        return None
    toks = {t for t in re.split(r"[^a-zA-ZÀ-ÿ]+", pl) if len(t) >= 3}
    for nome, d in el["personagens"].items():
        if d.get("papel") == "figurante":
            continue
        if toks & {t for t in re.split(r"[^a-zA-ZÀ-ÿ]+", nome.lower()) if len(t) >= 3}:
            return nome
    return None


def normalizar(obra, locucoes):
    """Troca apelidos pelo nome oficial e genérico pelo protagonista/par quando é claramente ele/ela (ver topo).
    Devolve uma lista NOVA (não mexe no cache do roteiro); a fala trocada guarda persona_orig."""
    el = carregar(obra)
    out = [dict(l) for l in locucoes]
    presentes = {}
    for l in out:
        nome = _achar(el, l.get("persona") or "")
        if nome:
            presentes[nome] = presentes.get(nome, 0) + 1
    contagem = {}
    for l in out:
        p = _limpo(l.get("persona") or "")
        if p.lower() not in NARRADOR and _e_generico(p):
            contagem[(p.lower(), l.get("gender"))] = contagem.get((p.lower(), l.get("gender")), 0) + 1
    trocas = {}
    for papel in ("protagonista", "par"):
        nome = next((n for n, d in el["personagens"].items() if d.get("papel") == papel), None)
        if not nome or presentes.get(nome):
            continue
        gen = el["personagens"][nome]["genero"]
        cands = sorted(((c, k) for k, c in contagem.items() if k[1] == gen and c >= MIN_FALAS_PROTAGONISTA
                        and k[0] not in trocas), reverse=True)
        if cands:
            trocas[cands[0][1][0]] = nome
    n_troca = 0
    for l in out:
        p = _limpo(l.get("persona") or "")
        if p.lower() in NARRADOR:
            continue
        nome = trocas.get(p.lower()) if _e_generico(p) else _achar(el, p)
        if nome and nome != l.get("persona"):
            l["persona_orig"], l["persona"] = l.get("persona"), nome
            l["gender"] = el["personagens"][nome].get("genero", l.get("gender"))
            n_troca += 1
    if trocas:
        log(f"  elenco: genérico vira principal neste capítulo: {trocas}")
    if n_troca:
        log(f"  elenco: {n_troca} fala(s) com o nome oficial do personagem")
    return out


def _reservadas(el, campo):
    vs = [json.dumps(el["narrador"].get(campo), sort_keys=True)]
    for d in el["personagens"].values():
        if d.get(campo):
            vs.append(json.dumps(d[campo], sort_keys=True))
    return set(vs)


def voz(obra, persona, genero):
    """(voz edge {voice, rate, pitch}, voz gemini) fixas do personagem nesta obra (atribui e grava se for novo)."""
    el = carregar(obra)
    p = _limpo(persona)
    if p.lower() in NARRADOR:
        return el["narrador"]["edge"], el["narrador"].get("gemini", "Kore")
    nome = _achar(el, p)
    if not nome:
        nome = p if not _e_generico(p) else f"{p.lower()}|{(genero or 'M').upper()[:1]}"
        el["personagens"][nome] = {"papel": "figurante" if _e_generico(p) else "personagem",
                                   "genero": (genero or "M").upper()[:1], "apelidos": []}
    d = el["personagens"][nome]
    g = "F" if str(d.get("genero") or genero or "M").upper().startswith("F") else "M"
    mudou = False
    if not d.get("edge"):
        usadas = _reservadas(el, "edge")
        # base do narrador, do protagonista e do par é EXCLUSIVA: ninguém mais usa nem variação dela (soaria igual)
        exclusivas = {el["narrador"].get("edge", {}).get("voice")} | {
            x["edge"]["voice"] for x in el["personagens"].values()
            if x.get("papel") in ("protagonista", "par") and x.get("edge")}
        pool = [v for v in virtuais(g) if v["voice"] not in exclusivas]
        if d.get("papel") in ("protagonista", "par"):  # principais: voz pura (sem variação), a melhor livre
            pool = [v for v in pool if v["rate"] == "+0%" and v["pitch"] == "+0Hz"]
        elif d.get("papel") == "figurante":  # figurante: só variações (as vozes puras ficam pros personagens com nome)
            pool = [v for v in pool if not (v["rate"] == "+0%" and v["pitch"] == "+0Hz")]
        livres = [v for v in pool if json.dumps(v, sort_keys=True) not in usadas] or pool
        d["edge"] = livres[0] if d.get("papel") != "figurante" else livres[_n(nome) % len(livres)]
        mudou = True
    if not d.get("gemini"):
        pool = GEMINI_F if g == "F" else GEMINI_M
        usadas = {x.get("gemini") for x in el["personagens"].values()} | {el["narrador"].get("gemini")}
        livres = [v for v in pool if v not in usadas] or pool
        d["gemini"] = livres[0] if d.get("papel") != "figurante" else livres[_n(nome) % len(livres)]
        mudou = True
    if mudou:
        _gravar(obra, el)
        log(f"  elenco {obra}: {nome} -> edge {d['edge']['voice']} {d['edge']['rate']} {d['edge']['pitch']} | gemini {d['gemini']}")
    return d["edge"], d["gemini"]


def falar_edge(texto, wav_path, v, rotulo=""):
    """wav 24 kHz mono com a voz edge v={voice, rate, pitch}; cache por voz+texto. True/False."""
    import edge_tts
    if v["voice"] in PROIBIDAS:
        raise ValueError(f"voz proibida pelo dono: {v['voice']}")
    texto = (texto or "").strip()
    chave = hashlib.sha256(f"edge:{v['voice']}:{v['rate']}:{v['pitch']}:{texto}".encode()).hexdigest()[:16]
    cache = TTS_CACHE / f"{chave}.wav"
    if cache.exists():
        log(f"  TTS[edge]: {rotulo} ({v['voice'].split('-')[2]}) — [CACHE] {texto[:50]}...")
    else:
        mp3 = cache.with_suffix(".mp3")
        for tent in range(4):
            try:
                asyncio.run(edge_tts.Communicate(texto, v["voice"], rate=v["rate"], pitch=v["pitch"]).save(str(mp3)))
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ar", "24000", "-ac", "1", str(cache)],
                               check=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                break
            except Exception as e:  # noqa: BLE001
                log(f"  [!] edge {v['voice']} falhou ({tent + 1}/4): {str(e)[:100]}")
                time.sleep(3 * (tent + 1))
            finally:
                mp3.unlink(missing_ok=True)
        if not cache.exists():
            return False
        log(f"  TTS[edge]: {rotulo} ({v['voice'].split('-')[2]} {v['rate']} {v['pitch']}) — {texto[:50]}...")
    shutil.copy2(cache, wav_path)
    return True


def usa_gemini(persona):
    """Esta fala vai pro Gemini no motor atual? (misto: só personagem; narrador fica no edge)."""
    m = motor()
    return m == "gemini" or (m == "misto" and _limpo(persona).lower() not in NARRADOR)


def falar(obra, texto, wav_path, persona, genero, force_tts=False):
    """Fala em português pelo motor configurado, com a voz fixa do personagem na obra."""
    v_edge, v_gem = voz(obra, persona, genero)
    if not usa_gemini(persona):
        return falar_edge(texto, wav_path, v_edge, persona or "Narrador")
    from tts_stage import tts_panel
    return tts_panel(texto, wav_path, persona=persona or "Narrador", gender=genero, voz=v_gem, force_tts=force_tts)


def trocar_motor(novo):
    """Grava o motor do português em config/fila.json (vale do próximo capítulo em diante)."""
    if novo not in MOTORES:
        raise SystemExit(f"motor inválido: {novo} (use {', '.join(MOTORES)})")
    p = PROJECT_DIR / "config" / "fila.json"
    c = json.loads(p.read_text(encoding="utf-8"))
    c["tts_motor"] = novo
    p.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    return novo


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Voz do português: motor e elenco fixo por obra")
    ap.add_argument("--motor", choices=MOTORES, help="troca o motor (vale do próximo capítulo em diante)")
    a = ap.parse_args()
    if a.motor:
        trocar_motor(a.motor)
    explica = {"edge": "TUDO no edge (rápido, sem limite)",
               "misto": "narrador no edge + personagens no Gemini (voz fixa de cada um)",
               "gemini": "TUDO no Gemini (como era, mais lento)"}
    print(f"Voz do português agora: {motor().upper()} = {explica[motor()]}")
    print("Vale a partir do próximo capítulo que renderizar.")
