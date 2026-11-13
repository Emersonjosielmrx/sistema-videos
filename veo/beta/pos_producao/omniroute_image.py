# -*- coding: utf-8 -*-
"""omniroute_image.py — geracao de imagem IA pro veo (fundo de CTA/propaganda).

Portado do historias-em-frames (bin/omniroute_image.py). Mesma chain gratuita:
  1) OmniRoute image-gen combo (Gemini Flash Image 3.1 -> FLUX schnell -> ...)
  2) Pollinations (fallback keyless, requer User-Agent)

Exposto como `_generate(prompt, out_path) -> bool` porque cta_card.py chama
exatamente isso. Cache fica a cargo de quem chama (cta_card ja cacheia por hash).

Circuit-breaker: se tudo falhar, marca _exhausted por 5 min pra nao travar o
pipeline com timeouts repetidos (o card cai no gradiente liso enquanto isso).
"""
import base64
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

def _seg_gateway():
    """Le key/url do gateway de secrets/gateway.json (gitignored). Sem literal."""
    import os as _os
    cfg = {}
    try:
        _p = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                           "secrets", "gateway.json")
        cfg = json.loads(open(_p, encoding="utf-8").read())
    except Exception:
        cfg = {}
    return cfg

_SEG = _seg_gateway()
import os as _os_env
_GW_BASE = _os_env.environ.get("LLM_GATEWAY_URL",
                               _SEG.get("gateway_url", "http://157.173.207.22:20128")).rstrip("/")
_GW_KEY = _os_env.environ.get("LLM_GATEWAY_KEY", _SEG.get("gateway_key", "")).strip()
OMNIROUTE_URL = f"{_GW_BASE}/v1/images/generations"
OMNIROUTE_KEY = f"Bearer {_GW_KEY}"
MODELS = [
    "antigravity/gemini-3.1-flash-image",
    "together/google/flash-image-3.1-lite",
    "together/black-forest-labs/FLUX.1-schnell",
]

_exhausted = False
_exhausted_at = 0.0
_RETRY_INTERVAL = 300


def _log(msg):
    print(f"[omniroute_image] {msg}", flush=True)


_ultima_fonte = None  # "gemini"/"flux"/"pollinations"/None — qual backend deu a ultima img


def _generate(prompt, out_path, premium_only=False) -> bool:
    """Gera uma imagem pro prompt e grava em out_path. True se conseguiu.

    premium_only=True: NAO usa o fallback Pollinations. Serve pro health-check
    saber a verdade (se o Gemini/FLUX estao mesmo funcionando).
    """
    global _exhausted, _exhausted_at, _ultima_fonte
    out_path = Path(out_path)
    if _exhausted and (time.time() - _exhausted_at) < _RETRY_INTERVAL and not premium_only:
        return False
    _exhausted = False

    for mi, model in enumerate(MODELS):
        # o 1o modelo (Gemini) da a melhor imagem: se tomar 429 (rate limit),
        # vale esperar e re-tentar antes de cair pros piores. 402 (sem saldo)
        # nao adianta insistir -> pula direto.
        tentativas = 3 if mi == 0 else 1
        for t in range(tentativas):
            try:
                body = json.dumps({
                    "model": model, "prompt": prompt, "n": 1,
                    "response_format": "b64_json",
                }).encode()
                req = urllib.request.Request(
                    OMNIROUTE_URL, data=body,
                    headers={"Content-Type": "application/json",
                             "Authorization": OMNIROUTE_KEY})
                resp = urllib.request.urlopen(req, timeout=120)
                data = json.loads(resp.read())
                img_list = data.get("data", [])
                img_b64 = img_list[0].get("b64_json") if img_list else None
                if not img_b64:
                    break
                img_bytes = base64.b64decode(img_b64)
                if len(img_bytes) < 1000:
                    break
                out_path.write_bytes(img_bytes)
                _ultima_fonte = "gemini" if mi == 0 else model.split("/")[-1]
                _log(f"ok {out_path.name} ({len(img_bytes)//1024}KB) [{model.split('/')[-1]}]")
                return True
            except urllib.error.HTTPError as e:
                # 429 no Gemini: backoff e re-tenta. 402/outros: pula modelo.
                if e.code == 429 and t < tentativas - 1:
                    time.sleep(3 * (t + 1))
                    continue
                _log(f"! {model.split('/')[-1]}: HTTP {e.code}")
                break
            except Exception as e:
                _log(f"! {model.split('/')[-1]}: {str(e)[:80]}")
                break

    # health-check quer so a verdade dos premium: nao usa Pollinations
    if premium_only:
        _ultima_fonte = None
        return False

    # Google Flow / Nano Banana 2.1 (D:\flow-imagens, dono 22/10: "nos lugares dos geradores de imagem coloque esse
    # sistema"): antes do Pollinations, que e a pior imagem. FLOW_IMAGEM=0 desliga; depois de uma falha fica 30 min fora.
    try:
        import sys as _sys
        _sys.path.insert(0, r"D:\flow-imagens")
        import cliente as _flow
        if _flow.gerar(prompt, out_path, formato="9:16", log=_log):
            _ultima_fonte = "flow"
            return True
    except Exception as e:
        _log(f"! flow: {str(e)[:80]}")

    # Fallback: Pollinations (gratis, requer User-Agent de browser)
    try:
        encoded = urllib.request.quote(prompt[:500])
        poll_url = (f"https://image.pollinations.ai/prompt/{encoded}"
                    f"?width=1080&height=1920&nologo=true")
        poll_req = urllib.request.Request(poll_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36"})
        resp = urllib.request.urlopen(poll_req, timeout=90)
        img_bytes = resp.read()
        if len(img_bytes) > 5000:
            out_path.write_bytes(img_bytes)
            _ultima_fonte = "pollinations"
            _log(f"ok {out_path.name} ({len(img_bytes)//1024}KB) [pollinations]")
            return True
    except Exception as e:
        _log(f"! pollinations: {str(e)[:80]}")

    _ultima_fonte = None
    _exhausted = True
    _exhausted_at = time.time()
    return False


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "tmp" / "_teste_imggen.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    ok = _generate(
        "Vertical 1080x1920 premium abstract cinematic background, emerald green "
        "palette, soft neon glow, bokeh, no text, no logos", out)
    print("OK" if ok else "FALHOU", "->", out)
