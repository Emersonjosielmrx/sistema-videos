#!/usr/bin/env python3
r"""Compara a versao nova (HTTP, porta 20141) com a atual (navegador, porta 20140).

Manda as mesmas perguntas nos dois proxies e mede tempo, tamanho e sucesso.
"""
import json
import time
import requests

PERGUNTAS = [
    "Responda em uma frase: o que e fotossintese?",
    "Liste 3 linguagens de programacao, so os nomes.",
]

PROXIES = [
    ("NOVA (HTTP, sem navegador)", "http://127.0.0.1:20141/v1/chat/completions"),
    ("ATUAL (navegador)", "http://127.0.0.1:20140/v1/chat/completions"),
]


def chamar(url, pergunta):
    corpo = {"model": "gemini-4-argon", "messages": [{"role": "user", "content": pergunta}]}
    t0 = time.time()
    try:
        r = requests.post(url, json=corpo, timeout=180)
        dt = time.time() - t0
        if r.status_code != 200:
            return dt, None, f"HTTP {r.status_code}: {r.text[:120]}"
        txt = r.json()["choices"][0]["message"]["content"]
        return dt, txt, None
    except Exception as e:
        return time.time() - t0, None, str(e)


for nome, url in PROXIES:
    print(f"\n{'='*60}\n{nome}\n{'='*60}")
    tempos = []
    for p in PERGUNTAS:
        dt, txt, err = chamar(url, p)
        tempos.append(dt)
        if err:
            print(f"  [{dt:5.1f}s] ERRO: {err}")
        else:
            prev = txt.replace(chr(10), " ")[:80]
            print(f"  [{dt:5.1f}s] {len(txt):4d} chars | {prev}")
    print(f"  -> media {sum(tempos)/len(tempos):.1f}s")
