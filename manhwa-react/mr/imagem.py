"""Geracao de imagem por IA: Google Flow / Nano Banana 2.1 (D:\\flow-imagens\\cliente.py, desde 22/10/2026) e, se ele
nao entregar, o gateway OmniRoute (antigravity/gemini-3.1-flash-image, o mesmo do historias-em-frames).

So texto -> imagem: o gateway ignora imagem de referencia para esse modelo (testado em 2026-10-02: pedir "esta foto em
preto e branco" devolveu outra foto). Por isso rosto real entra por composicao (Pillow), nunca pedindo ao modelo.
A chave e lida do arquivo do historias-em-frames (paths.omniroute_secrets) - nada copiado para ca.
"""
import base64
import hashlib
import io
import json
import time
from pathlib import Path
from .common import log

TAMANHOS = {"16:9": "1792x1024", "1:1": "1024x1024", "9:16": "1024x1792", "4:3": "1344x1024", "3:4": "1024x1344"}
NEGATIVO = " No text, no letters, no words, no logos, no watermark, no signature."


def _gateway(cfg):
    p = Path(cfg["paths"].get("omniroute_secrets", "D:/historias-em-frames/secrets/omniroute.json"))
    j = json.loads(p.read_text(encoding="utf-8"))
    return j["base_url"].rstrip("/"), j["api_key"]


def gerar(cfg, prompt, aspect="16:9", out=None, sem_texto=True, tentativas=2):
    """Gera uma imagem e devolve o caminho (PNG). Cache por prompt+aspecto em assets/ai_cache."""
    import requests
    from PIL import Image
    texto = prompt.strip() + (NEGATIVO if sem_texto else "")
    chave = hashlib.md5(f"{texto}|{aspect}".encode()).hexdigest()[:16]
    cache = Path(cfg["paths"]["assets"]) / "ai_cache" / f"{chave}.png"
    if not cache.exists():
        # 22/10 (dono: "nos lugares dos geradores de imagem coloque esse sistema"): 1o o Google Flow / Nano Banana 2.1
        # (D:\flow-imagens, contas do Veo); nao entregou (ou PC sem Flow / FLOW_IMAGEM=0) = gateway como antes
        try:
            import sys
            sys.path.insert(0, r"D:\flow-imagens")
            import cliente as _flow
            if _flow.gerar(texto, cache, formato=aspect, log=log):
                log(f"imagem IA (Flow): {cache.name} ({aspect}) <- {prompt[:60]}")
        except Exception as e:  # noqa: BLE001
            log(f"imagem IA: Flow falhou ({e})")
    if not cache.exists():
        base, key = _gateway(cfg)
        modelo = cfg.get("imagem", {}).get("modelo", "antigravity/gemini-3.1-flash-image")
        corpo = {"model": modelo, "prompt": texto, "n": 1, "response_format": "b64_json",
                 "size": TAMANHOS.get(aspect, "1024x1024"), "aspect_ratio": aspect}
        for t in range(tentativas):
            try:
                r = requests.post(base + "/v1/images/generations", headers={"Authorization": "Bearer " + key}, json=corpo, timeout=180)
                d = (r.json().get("data") or [{}])[0] if r.status_code == 200 else {}
                if d.get("b64_json"):
                    cache.parent.mkdir(parents=True, exist_ok=True)
                    Image.open(io.BytesIO(base64.b64decode(d["b64_json"]))).convert("RGB").save(cache)
                    log(f"imagem IA: {cache.name} ({aspect}) <- {prompt[:60]}")
                    break
                log(f"imagem IA: HTTP {r.status_code} {r.text[:160]}")
            except Exception as e:  # noqa: BLE001
                log(f"imagem IA: falhou ({e})")
            time.sleep(4 * (t + 1))
    if not cache.exists():
        return None
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(cache.read_bytes())
        return Path(out)
    return cache
