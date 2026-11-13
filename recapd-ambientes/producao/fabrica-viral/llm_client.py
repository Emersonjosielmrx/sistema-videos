# -*- coding: utf-8 -*-
"""Cliente LLM via proxy OpenAI-compatible."""
import json
import urllib.request
import time
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_MODEL_FAST


def chat(messages, model=None, max_tokens=4096, temperature=0.7):
    """Chama o proxy LLM. Retorna o texto da resposta."""
    model = model or LLM_MODEL
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{LLM_BASE_URL}/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[llm] erro: {e}")
        return None


def chat_fast(messages, max_tokens=2048, temperature=0.7):
    """Usa modelo rapido/barato."""
    return chat(messages, model=LLM_MODEL_FAST, max_tokens=max_tokens, temperature=temperature)


def chat_json(messages, model=None, max_tokens=4096):
    """Chama LLM esperando JSON na resposta. Tenta parsear."""
    raw = chat(messages, model=model, max_tokens=max_tokens, temperature=0.3)
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(lines)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Tenta achar JSON no meio do texto
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
        # Tenta array
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
    return raw
