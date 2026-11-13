"""Acesso a LLM com cadeia de fallback: proxy (Opus 4.6 -> Sonnet 4.5 -> Haiku) e Claude Code CLI.

Proxy = o mesmo gateway compativel com a API Anthropic que o Claude do VS Code usa (secrets_proxy.json).
"""
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path
from .common import log
from . import limitador

_proxy_cfg = None
_dead = set()


def extract_json(txt):
    txt = (txt or "").strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, re.S)
    if m:
        txt = m.group(1)
    i = txt.find("{")
    if i < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for j, ch in enumerate(txt[i:], start=i):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(txt[i:j + 1])
                except Exception:
                    return None
    return None


def _proxy(cfg):
    global _proxy_cfg
    if _proxy_cfg is not None:
        return _proxy_cfg
    p = cfg["paths"].get("proxy_secrets")
    if p and Path(p).exists():
        try:
            _proxy_cfg = json.load(open(p, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            log(f"proxy: nao li {p}: {e}")
            _proxy_cfg = {}
    else:
        _proxy_cfg = {}
    return _proxy_cfg


def ask_proxy(cfg, tier, instructions, payload, timeout=240, max_tokens=6000):
    px = _proxy(cfg)
    base = (px.get("base_url") or "").rstrip("/")
    key = px.get("auth_token")
    models = dict(cfg["editorial"].get("models", {}))
    models.update({k: v for k, v in (px.get("models") or {}).items() if v})
    model = models.get(tier)
    if not base or not key or not model or model in _dead:
        return None
    if limitador.restante(f"proxy_{tier}"):  # em pausa: vai direto pro proximo provedor em vez de esperar o timeout
        log(f"proxy {tier}: em pausa pelo limitador ({limitador.restante(f'proxy_{tier}') // 60} min), pulando")
        return None
    body = {"model": model, "max_tokens": max_tokens, "temperature": 0.3, "system": instructions,
            "messages": [{"role": "user", "content": payload}]}
    req = urllib.request.Request(base + "/v1/messages", data=json.dumps(body).encode("utf-8"),
                                 headers={"x-api-key": key, "Authorization": f"Bearer {key}", "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        d = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        msg = str(e)[:160]
        log(f"proxy {tier} ({model}): erro {msg}")
        if "401" in msg or "403" in msg or "404" in msg:
            _dead.add(model)
        else:
            limitador.falhou(f"proxy_{tier}", msg)
        return None
    limitador.ok(f"proxy_{tier}")
    text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    data = extract_json(text)
    if data is None:
        log(f"proxy {tier}: resposta sem JSON: {text[:200]}")
    else:
        log(f"editorial via proxy {tier} ({model})")
    return data


def ask_cli(cfg, instructions, payload, timeout=240):
    cli = cfg["paths"].get("claude_cli")
    if not cli or not os.path.exists(cli):
        return None
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
    env["PYTHONUTF8"] = "1"
    cmd = [cli, "-p", instructions, "--output-format", "text"]
    if cfg["editorial"].get("model"):
        cmd += ["--model", cfg["editorial"]["model"]]
    try:
        res = subprocess.run(cmd, input=payload, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        log("claude cli: timeout")
        return None
    if res.returncode != 0:
        log(f"claude cli: erro {res.returncode}: {(res.stderr or '')[-300:]}")
        return None
    data = extract_json(res.stdout)
    if data is None:
        log(f"claude cli: resposta sem JSON: {res.stdout[:200]}")
    else:
        log("editorial via claude cli")
    return data


def ask_json(cfg, instructions, payload, timeout=None):
    """Percorre editorial.providers (ex.: ["proxy:opus", "proxy:sonnet", "cli"]) ate obter um JSON."""
    timeout = timeout or cfg["editorial"].get("timeout", 240)
    for prov in cfg["editorial"].get("providers", ["cli"]):
        if prov.startswith("proxy:"):
            data = ask_proxy(cfg, prov.split(":", 1)[1], instructions, payload, timeout=timeout)
        elif prov == "cli":
            data = ask_cli(cfg, instructions, payload, timeout=timeout)
        else:
            data = None
        if data is not None:
            return data
    log("editorial: nenhum provedor respondeu")
    return None
