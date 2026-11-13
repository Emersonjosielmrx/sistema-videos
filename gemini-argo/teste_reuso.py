# -*- coding: utf-8 -*-
"""Teste do reuso de conversa no gemini_http_proxy (porta de teste 20142). Turno 2 só acerta o número se o Gemini
continuou a mesma conversa (o texto do turno 2 não traz o número)."""
import json
import sys
import time
import urllib.request

PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 20142
URL = f"http://127.0.0.1:{PORTA}/v1/chat/completions"


def pedir(msgs):
    t = time.time()
    b = json.dumps({"model": "gemini-4-argon", "stream": False, "messages": msgs}).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(URL, data=b, headers={"Content-Type": "application/json"}),
                                          timeout=600).read())
    return r["choices"][0]["message"]["content"].strip(), time.time() - t


for _ in range(30):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/health", timeout=3)
        break
    except Exception:  # noqa: BLE001
        time.sleep(1)

sistema = {"role": "system", "content": "Você é um assistente de teste. Responda curto. " + ("Regra de contexto. " * 400)}
m1 = [sistema, {"role": "user", "content": "Guarde o número secreto 4817. Responda só: OK"}]
r1, t1 = pedir(m1)
print(f"turno 1 ({t1:.0f}s): {r1[:80]}")
m2 = m1 + [{"role": "assistant", "content": r1},
           {"role": "user", "content": "Qual é o número secreto que pedi pra guardar? Responda só o número."}]
r2, t2 = pedir(m2)
print(f"turno 2 ({t2:.0f}s): {r2[:80]}")
cota = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/cota", timeout=10).read())
print("reuso:", cota.get("reuso"))
print("RESULTADO:", "REUSO OK" if "4817" in r2 and (cota.get("reuso") or {}).get("acertos", 0) >= 1 else "FALHOU")
