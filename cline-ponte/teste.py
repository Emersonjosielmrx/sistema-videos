"""Teste da ponte: raciocinio + ferramenta, devolve o raciocinio no 2o turno, e cache de prompt.
Uso: python -I teste.py [url]   (padrao http://127.0.0.1:20160)"""
import json
import sys
import urllib.error
import urllib.request

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:20160") + "/v1/messages"
CHAVE = json.load(open(__file__.rsplit("\\", 1)[0] + "\\config.json", encoding="utf-8"))["chaves"][0]
FERR = [{"name": "get_weather", "description": "get weather", "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}]
SISTEMA = [{"type": "text", "text": "You are a helpful assistant. " + ("Reference text for caching. " * 900), "cache_control": {"type": "ephemeral"}}]


def pedir(corpo):
    corpo = {"model": "cline-opus-5-5", "stream": True, **corpo}
    req = urllib.request.Request(URL, json.dumps(corpo).encode(), {"content-type": "application/json", "x-api-key": CHAVE})
    blocos, uso, parada = {}, {}, None
    try:
        r = urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        open(__file__.rsplit("\\", 1)[0] + "\\vps\\corpo_falhou.json", "w").write(json.dumps(corpo))
        raise SystemExit(f"ERRO HTTP {e.code}: {e.read()[:800]!r}")
    with r:
        for linha in r:
            linha = linha.decode().strip()
            if not linha.startswith("data:"):
                continue
            e = json.loads(linha[5:])
            t = e["type"]
            if t == "content_block_start":
                blocos[e["index"]] = dict(e["content_block"], _j="")
            elif t == "content_block_delta":
                b, d = blocos[e["index"]], e["delta"]
                if d["type"] == "text_delta": b["text"] += d["text"]
                elif d["type"] == "thinking_delta": b["thinking"] += d["thinking"]
                elif d["type"] == "signature_delta": b["signature"] += d["signature"]
                elif d["type"] == "input_json_delta": b["_j"] += d["partial_json"]
            elif t == "message_delta":
                uso, parada = e["usage"], e["delta"]["stop_reason"]
            elif t == "error":
                raise SystemExit("ERRO: " + json.dumps(e))
    out = []
    for i in sorted(blocos):
        b = blocos[i]
        if b["type"] == "tool_use":
            b["input"] = json.loads(b["_j"] or "{}")
        b.pop("_j")
        if b["type"] == "text" and not b["text"]:
            continue
        out.append(b)
    return out, uso, parada


msgs = [{"role": "user", "content": "Think step by step about which city is the capital of France, then call get_weather for it."}]
c1, u1, p1 = pedir({"max_tokens": 4000, "system": SISTEMA, "tools": FERR, "thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}, "messages": msgs})
print("turno 1:", p1, [b["type"] for b in c1], "uso", u1)
tool = next(b for b in c1 if b["type"] == "tool_use")
msgs += [{"role": "assistant", "content": c1},
         {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool["id"], "content": "22C sunny"}]}]
c2, u2, p2 = pedir({"max_tokens": 4000, "system": SISTEMA, "tools": FERR, "thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}, "messages": msgs})
print("turno 2:", p2, [b["type"] for b in c2], "uso", u2)
print("resposta:", " ".join(b.get("text", "") for b in c2 if b["type"] == "text")[:200])
print("CACHE OK" if u2.get("cache_read_input_tokens", 0) > 0 else "sem leitura de cache")
