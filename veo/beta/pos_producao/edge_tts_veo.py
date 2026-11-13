# -*- coding: utf-8 -*-
"""Adaptacao do edge_tts_engine.py pra projeto Veo.

Mantem a mesma API (speak, voice_for_persona, VOICES_*), mas:
- PROJECT_DIR aponta pra D:\\veo\\beta
- SECRETS em D:\\veo\\beta\\pos_producao\\secrets
- VOICES_REGISTRY em D:\\veo\\beta\\pos_producao\\workspace\\voices-registry.json (autocria)
- Sem suporte a mascote/VFX (historias-em-frames specific)
"""

import asyncio
import os
import subprocess
import sys
import time
import json
import argparse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent  # D:\veo\beta
SECRETS = PROJECT_DIR / "pos_producao" / "secrets"
PROXY_LIST_FILE = SECRETS / "proxies.txt"

# ---------------------------------------------------------------------------
# VOZES (16/10/2026, item IM-03 de D:\veo\docs\PLANO_MELHORIAS_VEO.md)
# A dona proibiu em 15/10, para QUALQUER projeto: pt-BR-AntonioNeural (masculina
# ruim), pt-BR-FranciscaNeural (aposentada) e it-IT-IsabellaNeural (sotaque em
# portugues). Este modulo usava Francisca e Antonio como padrao.
# As aprovadas sao as edge Multilingual (falam qualquer lingua; a dona ouviu as
# amostras em portugues e aprovou). Listas copiadas de
# D:\hipercool-videos\bin\elenco.py (PROIBIDAS, EDGE_F, EDGE_M, VARIACOES).
# ---------------------------------------------------------------------------
PROIBIDAS = {"pt-BR-AntonioNeural", "pt-BR-FranciscaNeural", "it-IT-IsabellaNeural"}

VOICES_FEMALE = [
    "pt-BR-ThalitaMultilingualNeural", "en-US-AvaMultilingualNeural",
    "en-US-EmmaMultilingualNeural", "de-DE-SeraphinaMultilingualNeural",
    "fr-FR-VivienneMultilingualNeural",
]
VOICES_MALE = [
    "en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural",
    "en-AU-WilliamMultilingualNeural", "de-DE-FlorianMultilingualNeural",
    "fr-FR-RemyMultilingualNeural", "it-IT-GiuseppeMultilingualNeural",
    "ko-KR-HyunsuMultilingualNeural",
]
# Thalita e Andrew sao as preferidas da dona para pt-BR.
NARRATOR_VOICES = {"veo": "pt-BR-ThalitaMultilingualNeural",
                   "veo_m": "en-US-AndrewMultilingualNeural"}
VOICES_PREBUILT = VOICES_FEMALE + VOICES_MALE

VOICES_REGISTRY = PROJECT_DIR / "pos_producao" / "workspace" / "voices-registry.json"

# Variacoes virtuais (velocidade, tom): a 1a e a voz pura. Faixa que ainda soa
# natural: -8..+15% e -8..+8 Hz. Cada voz x 10 variacoes = muitas vozes distintas.
VARIACOES = [("+0%", "+0Hz"), ("+8%", "+4Hz"), ("-6%", "-4Hz"), ("+12%", "+8Hz"),
             ("-8%", "-8Hz"), ("+4%", "-6Hz"), ("+0%", "+6Hz"), ("+15%", "+2Hz"),
             ("-4%", "+3Hz"), ("+6%", "-2Hz")]


def _apelido(voz: str) -> str:
    """'en-US-AndrewMultilingualNeural' -> 'andrew'."""
    try:
        return voz.split("-")[2].replace("Multilingual", "").replace("Neural", "").lower()
    except IndexError:
        return voz.lower()


# Banco nomeado (voz + variacao), montado das listas aprovadas.
VIRTUAL_VOICES = {}
for _v in VOICES_PREBUILT:
    for _i, (_rate, _pitch) in enumerate(VARIACOES):
        VIRTUAL_VOICES[f"{_apelido(_v)}_{_i}"] = {"voice": _v, "rate": _rate, "pitch": _pitch}

_NARRATOR_PROFILE = {"voice": NARRATOR_VOICES["veo"], "rate": "+5%", "pitch": "+0Hz"}


def checar_voz(voz: str) -> str:
    """Levanta se a voz estiver na lista proibida pela dona. Devolve a propria voz."""
    if voz in PROIBIDAS:
        raise ValueError(
            f"voz proibida pela dona: {voz} (ver IM-03 em D:\\veo\\docs\\PLANO_MELHORIAS_VEO.md). "
            f"Use uma das aprovadas: {', '.join(VOICES_PREBUILT)}")
    return voz

PROXY_LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
VOICES_REGISTRY.parent.mkdir(parents=True, exist_ok=True)


def _load_proxies():
    """Carrega lista de proxies do arquivo (Webshare). Cada linha: user:pass@host:port."""
    if not PROXY_LIST_FILE.exists():
        return []
    out = []
    for linha in PROXY_LIST_FILE.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            out.append(linha)
    return out


async def _speak_edge(text, voice_cfg, out_mp3, proxies, max_tries=3):
    """Fala o texto via edge-tts. Tenta direto, depois com proxy."""
    import edge_tts

    voice = voice_cfg["voice"]
    rate = voice_cfg.get("rate", "+0%")
    pitch = voice_cfg.get("pitch", "+0Hz")

    last_err = None
    tries = [(None, "direto")] + [(p, f"proxy[{i}]") for i, p in enumerate(proxies[:max_tries - 1])]
    for proxy, label in tries[:max_tries]:
        try:
            if proxy:
                # edge-tts nao tem suporte direto a proxy — usamos SOCKS via PySocks
                # (Pillow de edge-tts sai por winsound/HttpClient). Workaround:
                # definir proxy via env pra ser pego pelo aiohttp subjacente.
                os.environ["HTTPS_PROXY"] = f"http://{proxy}"
                os.environ["HTTP_PROXY"] = f"http://{proxy}"
            else:
                os.environ.pop("HTTPS_PROXY", None)
                os.environ.pop("HTTP_PROXY", None)

            communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
            await communicate.save(str(out_mp3))

            if out_mp3.exists() and out_mp3.stat().st_size > 1000:
                return True, label
        except Exception as e:
            last_err = e
            continue
    return False, str(last_err)


VOZ_PADRAO = "thalita_0"  # era "francisca_normal" (voz proibida pela dona)


def speak(text, voice_name=VOZ_PADRAO, out_mp3=None, max_tries=3):
    """Sincrono: fala o texto e salva em out_mp3. Retorna (ok, label).

    Nome de voz desconhecido cai no narrador padrao (Thalita). Voz proibida
    levanta ValueError: nao ha fallback silencioso para ela."""
    if out_mp3 is None:
        raise ValueError("out_mp3 obrigatorio")
    out_mp3 = Path(out_mp3)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)

    cfg = VIRTUAL_VOICES.get(voice_name) or _NARRATOR_PROFILE
    checar_voz(cfg["voice"])
    proxies = _load_proxies()
    return asyncio.run(_speak_edge(text, cfg, out_mp3, proxies, max_tries))


def voz_estavel(chave: str, feminina: bool = True) -> str:
    """Voz fixa por chave (produto, personagem...), escolhida por md5.

    Regra da dona: a mesma chave sempre com a mesma voz, e nunca sorteio por
    hash() do Python, que muda a cada execucao."""
    import hashlib
    pool = VOICES_FEMALE if feminina else VOICES_MALE
    n = int(hashlib.md5((chave or "x").encode("utf-8")).hexdigest(), 16)
    voz = pool[n % len(pool)]
    var = n % len(VARIACOES)
    return f"{_apelido(voz)}_{var}"


def voice_for_persona(persona):
    """Mapeia 'narrador' | 'homem' | 'mulher' -> voice_name padrao (aprovado)."""
    p = (persona or "narrador").lower()
    if "hom" in p or "man" in p or "masc" in p:
        return "andrew_0"
    return VOZ_PADRAO


# CLI pra gerar 1 audio rapido: python edge_tts_veo.py "texto" out.mp3 [voz]
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('uso: edge_tts_veo.py "texto" out.mp3 [voz]')
        print(f"vozes: {', '.join(sorted(VIRTUAL_VOICES)[:6])} ... ({len(VIRTUAL_VOICES)} no total)")
        sys.exit(1)
    text = sys.argv[1]
    out = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else VOZ_PADRAO
    ok, label = speak(text, voice, out)
    print(f"ok={ok} label={label} voz={VIRTUAL_VOICES.get(voice, _NARRATOR_PROFILE)['voice']} -> {out}")