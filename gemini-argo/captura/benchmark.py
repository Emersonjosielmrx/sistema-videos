#!/usr/bin/env python3
r"""Teste de capacidade: Argon vs Kiro Sonnet vs Gemini 3.8 Flash.

Manda as mesmas perguntas para os 3 modelos e compara qualidade + tempo.
"""
import json
import time
import requests

PERGUNTAS = [
    {
        "cat": "RACIOCINIO",
        "q": "Um caracol sobe 3 metros por dia e escorrega 2 metros por noite. O poço tem 10 metros. Em quantos dias ele sai? Explique passo a passo.",
        "gabarito": "8 dias",
    },
    {
        "cat": "CODIGO",
        "q": "Escreva uma função Python que recebe uma lista de inteiros e retorna o segundo maior elemento sem usar sort, set ou bibliotecas. Trate listas com menos de 2 elementos distintos.",
        "gabarito": "segundo_maior([3,1,4,1,5,9]) = 5",
    },
    {
        "cat": "LOGICA",
        "q": "Tenho 3 caixas: uma só com maçãs, uma só com laranjas, uma com ambas. Todas as etiquetas estão ERRADAS. Tiro UMA fruta da caixa 'Ambas'. Saiu maçã. Qual é o conteúdo correto de cada caixa?",
        "gabarito": "'Ambas'=Maçãs, 'Maçãs'=Ambas, 'Laranjas'=Laranjas -> errado. Correto: 'Ambas'=Maçãs, 'Laranjas'=Ambas, 'Maçãs'=Laranjas",
    },
    {
        "cat": "CONHECIMENTO",
        "q": "Explique em 3 frases a diferença entre TCP e UDP, e dê um exemplo prático de quando usar cada um.",
        "gabarito": "TCP=confiável/ordenado (web, email), UDP=rápido/sem garantia (jogos, streaming, DNS)",
    },
    {
        "cat": "CRIATIVIDADE",
        "q": "Crie um micro-conto de terror em exatamente 3 frases (nem mais, nem menos). Deve ter início, meio e fim.",
        "gabarito": "(subjetivo - avaliar qualidade)",
    },
    {
        "cat": "MATEMATICA",
        "q": "Qual é a integral de x*ln(x) dx? Mostre a resolução por partes.",
        "gabarito": "(x²/2)ln(x) - x²/4 + C",
    },
]

MODELOS = [
    ("Argon (HTTP)", "http://127.0.0.1:20141/v1/chat/completions", "gemini-4-argon"),
    ("Kiro Sonnet 4.5", "http://157.173.207.22:20128/v1/chat/completions", "kr/claude-sonnet-4.5"),
    ("Gemini 3.8 Flash", "http://157.173.207.22:20128/v1/chat/completions", "agy/gemini-3.8-flash-high"),
]

TOKEN = "<SEGREDO_REMOVIDO>"


def chamar(url, modelo, pergunta):
    corpo = {
        "model": modelo,
        "messages": [{"role": "user", "content": pergunta}],
        "max_tokens": 1500,
    }
    t0 = time.time()
    try:
        r = requests.post(url, json=corpo, timeout=300,
                          headers={"Authorization": f"Bearer {TOKEN}",
                                   "Content-Type": "application/json"},
                          verify=False)
        dt = time.time() - t0
        if r.status_code != 200:
            return dt, f"ERRO HTTP {r.status_code}: {r.text[:200]}"
        d = r.json()
        if "choices" in d:
            return dt, d["choices"][0]["message"]["content"]
        elif "content" in d:
            return dt, d["content"][0]["text"]
        else:
            return dt, json.dumps(d)[:500]
    except Exception as e:
        return time.time() - t0, f"ERRO: {e}"


import urllib3
urllib3.disable_warnings()

import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

resultados = {}
for nome_modelo, url, modelo_id in MODELOS:
    print(f"\n{'='*70}")
    print(f"  {nome_modelo}")
    print(f"{'='*70}")
    resultados[nome_modelo] = {"tempos": [], "respostas": []}
    for p in PERGUNTAS:
        dt, resp = chamar(url, modelo_id, p["q"])
        resultados[nome_modelo]["tempos"].append(dt)
        resultados[nome_modelo]["respostas"].append(resp)
        preview = resp.replace("\n", " ")[:120] if not resp.startswith("ERRO") else resp[:120]
        print(f"  [{p['cat']:12}] {dt:5.1f}s | {preview}")
    media = sum(resultados[nome_modelo]["tempos"]) / len(resultados[nome_modelo]["tempos"])
    print(f"  -> media {media:.1f}s")

# Salvar completo
with open(r"D:\gemini-argo\captura\benchmark.json", "w", encoding="utf-8") as f:
    json.dump({"perguntas": PERGUNTAS, "resultados": {
        k: {"tempos": v["tempos"], "respostas": v["respostas"]} for k, v in resultados.items()
    }}, f, ensure_ascii=False, indent=1)

print("\n\nRespostas salvas em D:\\gemini-argo\\captura\\benchmark.json")
print("Para comparar a qualidade, leia o arquivo.")
