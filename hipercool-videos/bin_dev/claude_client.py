# -*- coding: utf-8 -*-
"""claude_client.py — Claude via proxy compatível com a API Anthropic (texto e imagem).

Ordem: 1) secrets/claude_proxy.json (proxy do Claude Code, kr/claude-sonnet-4.5 — pedido do dono
2026-10-13); 2) D:\\manhwa-react\\secrets_proxy.json (Opus do antigravity). None se tudo falhar —
quem chama sempre tem um caminho sem Claude.
"""
import base64
import json
import re
import urllib.request
from pathlib import Path

from hp_common import PROJECT_DIR, log

SECRETS = [PROJECT_DIR / "secrets" / "claude_proxy.json", Path(r"D:\manhwa-react\secrets_proxy.json")]
_endpoints = None


def _carregar():
    """[(base_url, chave, [modelos])] dos arquivos que existirem."""
    global _endpoints
    if _endpoints is None:
        _endpoints = []
        for f in SECRETS:
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            base, key = (d.get("base_url") or "").rstrip("/"), d.get("auth_token")
            modelos = [d.get("modelo")] + list((d.get("models") or {}).values())
            modelos = [m for m in dict.fromkeys(modelos) if m]
            if base and key and modelos:
                _endpoints.append((base, key, modelos))
    return _endpoints


def is_available():
    return bool(_carregar())


def fast_model():
    """Modelo pros helpers: o Sonnet do Kiro (melhor que o Haiku, mesmo proxy)."""
    eps = _carregar()
    return eps[0][2][0] if eps else None


def _img_block(image_bytes, mime="image/jpeg"):
    return {"type": "image", "source": {"type": "base64", "media_type": mime,
                                        "data": base64.b64encode(image_bytes).decode()}}


def _extract_json(texto):
    if not texto:
        return None
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip())
    for cand in (t, t[t.find("{"):t.rfind("}") + 1], t[t.find("["):t.rfind("]") + 1]):
        try:
            return json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def _post(messages, model=None, max_tokens=1500, temperature=0.5, system=None, timeout=300, so=None):
    """Texto da resposta ou None. Tenta o modelo pedido e depois os de cada endpoint.
    so=[...]: tenta SÓ esses modelos (ex.: os Gemini do proxy), sem cair no Claude."""
    for base, key, modelos in _carregar():
        lista = list(so) if so else list(dict.fromkeys(([model] if model else []) + modelos))
        for m in lista:
            body = {"model": m, "max_tokens": max_tokens, "temperature": temperature, "messages": messages}
            if system:
                body["system"] = system
            req = urllib.request.Request(base + "/v1/messages", data=json.dumps(body).encode("utf-8"),
                                         headers={"x-api-key": key, "Authorization": f"Bearer {key}",
                                                  "anthropic-version": "2023-06-01",
                                                  "content-type": "application/json"})
            try:
                d = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8"))
            except Exception as e:  # noqa: BLE001
                log(f"    claude {m} falhou ({str(e)[:80]})")
                continue
            out = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text").strip()
            if out:
                return out
    return None


def perguntar(texto, imagens=(), system=None, max_tokens=1500, temperature=0.5, so=None):
    """Atalho: texto (+ imagens jpeg em bytes) -> resposta em texto, ou None."""
    conteudo = [_img_block(b) for b in imagens] + [{"type": "text", "text": texto}]
    return _post([{"role": "user", "content": conteudo}], max_tokens=max_tokens,
                 temperature=temperature, system=system, so=so)


# Gemini servidos pelo MESMO proxy (testados 2026-10-13 com imagem: 2-7 s, sem 429). Reforçam as chaves
# diretas do gemini_llm e são o principal na localização da censura (caixas mais precisas).
GEMINI_PROXY = ["antigravity/gemini-3-flash", "antigravity/gemini-3.1-flash-lite",
                "antigravity/gemini-3.5-flash-lite", "antigravity/gemini-3.8-flash-tiered"]


def gemini(texto, imagens=(), system=None, max_tokens=2048, temperature=0.7):
    """Gemini via proxy (formato Anthropic). None se nenhum responder."""
    return perguntar(texto, imagens, system=system, max_tokens=max_tokens, temperature=temperature,
                     so=GEMINI_PROXY)
