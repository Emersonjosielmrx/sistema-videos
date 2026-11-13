#!/usr/bin/env python3
"""Rodada dificil: respostas exatas, correcao automatica pela ultima linha 'RESPOSTA: ...'."""
import io
import json
import re
import sys
import time
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
TOKEN = "<SEGREDO_REMOVIDO>"
FIM = "\n\nTermine com uma linha final no formato exato: RESPOSTA: <valor>"

PERGUNTAS = [
    ("CONTAGEM", "Quantos inteiros de 1 a 1000 NAO sao divisiveis por 2, nem por 3, nem por 5?", ["266"]),
    ("ALGORITMO", "Com moedas de valores 1, 5 e 11 (quantidade ilimitada), qual o MENOR numero de moedas para formar exatamente 15? E para 30? Responda os dois numeros separados por virgula.", ["3,6", "3, 6"]),
    ("PROBABILIDADE", "Monty Hall com 4 portas: 1 carro e 3 bodes. Voce escolhe uma porta. O apresentador, que sabe onde esta o carro, abre uma das outras portas que tem bode. Voce entao troca para uma das 2 portas fechadas restantes escolhida ao acaso. Qual a probabilidade de ganhar o carro? De a fracao irredutivel.", ["3/8"]),
    ("LETRAS", "Quantas letras 'r' existem na frase: desenvolvedor de software barreira", ["5"]),
    ("CALENDARIO", "Se 1 de janeiro de 2027 e uma sexta-feira, que dia da semana sera 1 de marco de 2027?", ["segunda"]),
    ("CODIGO", "Em Python, qual e a saida exata de: print([i*j for i in range(3) for j in range(i)])", ["[0, 0, 2]"]),
]

MODELOS = [
    ("Argon (HTTP)", "http://127.0.0.1:20141/v1/chat/completions", "gemini-4-argon"),
    ("Opus 5.5", "http://157.173.207.22:20128/v1/chat/completions", "cc/claude-opus-5-5"),
    ("Kiro Sonnet 4.5", "http://157.173.207.22:20128/v1/chat/completions", "kr/claude-sonnet-4.5"),
    ("Gemini 3.8 Flash", "http://157.173.207.22:20128/v1/chat/completions", "agy/gemini-3.8-flash-high"),
]


def chamar(url, modelo, pergunta):
    corpo = {"model": modelo, "messages": [{"role": "user", "content": pergunta + FIM}], "max_tokens": 6000}
    t0 = time.time()
    try:
        r = requests.post(url, json=corpo, timeout=400, headers={"Authorization": f"Bearer {TOKEN}"})
        if r.status_code != 200:
            return time.time() - t0, f"ERRO HTTP {r.status_code}: {r.text[:150]}"
        return time.time() - t0, r.json()["choices"][0]["message"]["content"] or ""
    except Exception as e:
        return time.time() - t0, f"ERRO: {e}"


def resposta_final(txt):
    achados = re.findall(r"RESPOSTA:\s*(.+)", txt.replace("*", ""))
    return achados[-1].strip() if achados else txt.strip()[-60:]


placar = {}
saida = {}
for nome, url, mid in MODELOS:
    print(f"\n===== {nome} =====")
    acertos, tempos, saida[nome] = 0, [], []
    for cat, q, gabs in PERGUNTAS:
        dt, txt = chamar(url, mid, q)
        final = resposta_final(txt)
        ok = any(g.lower() in final.lower().replace("\\", "") for g in gabs)
        acertos += ok
        tempos.append(dt)
        saida[nome].append({"cat": cat, "tempo": dt, "final": final, "texto": txt})
        print(f"  [{cat:13}] {dt:5.1f}s {'OK  ' if ok else 'ERRO'} | {final[:70]}")
    placar[nome] = (acertos, sum(tempos) / len(tempos))
    print(f"  -> {acertos}/{len(PERGUNTAS)} certas, media {placar[nome][1]:.1f}s")

json.dump(saida, open(r"D:\gemini-argo\captura\benchmark2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n===== PLACAR =====")
for nome, (a, t) in sorted(placar.items(), key=lambda x: (-x[1][0], x[1][1])):
    print(f"  {nome:18} {a}/{len(PERGUNTAS)}  media {t:.1f}s")
