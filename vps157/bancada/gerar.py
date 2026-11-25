"""Bancada dos ajudantes (24/11): gera os arquivos das tarefas e o gabarito calculado (nao depende de modelo)."""
import csv
import json
import random
import re
from pathlib import Path

AQUI = Path(__file__).parent
random.seed(2411)

# T1: bug de limite (off-by-one)
(AQUI / "t1_media.py").write_text('''def media_movel(valores, janela):
    """Media de cada janela de `janela` itens seguidos."""
    saida = []
    for i in range(len(valores) - janela):
        bloco = valores[i:i + janela]
        saida.append(sum(bloco) / janela)
    return saida


if __name__ == "__main__":
    print(media_movel([1, 2, 3, 4, 5], 2))  # esperado: [1.5, 2.5, 3.5, 4.5]
''', encoding="utf-8")

# T2: conta em CSV
linhas = []
for i in range(1, 241):
    linhas.append({"id": i, "canal": random.choice(["Noturno", "Verse", "3D", "Solar"]),
                   "status": random.choice(["postado", "postado", "falhou", "agendado"]),
                   "views": random.randint(0, 9000)})
with open(AQUI / "t2_videos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "canal", "status", "views"])
    w.writeheader()
    w.writerows(linhas)
t2 = sum(r["views"] for r in linhas if r["canal"] == "Verse" and r["status"] == "postado")

# T3: chave que nao existe (pegadinha)
(AQUI / "t3_config.json").write_text(json.dumps({"fila": {"max_contas": 41, "pausa_min": 20},
                                                 "vigia": {"limite_mb": 3200}}, indent=2), encoding="utf-8")

# T4: log com erros
erros = (["429 rate limited"] * 37 + ["502 empty content"] * 23 + ["503 circuit open"] * 31 +
         ["401 token revoked"] * 4)
random.shuffle(erros)
with open(AQUI / "t4_gateway.log", "w", encoding="utf-8") as f:
    for i, e in enumerate(erros):
        f.write(f"2026-11-23T{10 + i // 60:02d}:{i % 60:02d}:00Z ERROR conta={i % 7} {e}\n")
        if i % 3 == 0:
            f.write(f"2026-11-23T{10 + i // 60:02d}:{i % 60:02d}:30Z INFO ok conta={i % 7}\n")

# T5: argumentos trocados entre arquivos
(AQUI / "t5_util.py").write_text('''def pausar(conta, minutos, motivo):
    return f"{conta} pausada {minutos} min: {motivo}"
''', encoding="utf-8")
(AQUI / "t5_main.py").write_text('''from t5_util import pausar


def tratar_erro(conta, status):
    if status == 429:
        return pausar(conta, "limite", 20)
    return None


print(tratar_erro("conta7", 429))  # esperado: "conta7 pausada 20 min: limite"
''', encoding="utf-8")

# T6: regex (precisa rodar ou raciocinar com cuidado)
padrao = r"^(cw|claude-web)/claude-sonnet-\d+(-\d+)?$"
nomes = ["cw/claude-sonnet-5-5", "claude-web/claude-sonnet-5", "cc/claude-sonnet-5-5", "cw/claude-sonnet-5-5-high",
         "claude-web/claude-sonnet-4-5", "cw/claude-opus-5-5"]
t6 = [n for n in nomes if re.match(padrao, n)]

tarefas = f"""BANCADA DE AJUDANTES — 6 tarefas. Os arquivos estão em D:\\vps157\\bancada\\. Responda TODAS.
T1. O arquivo t1_media.py devia imprimir [1.5, 2.5, 3.5, 4.5]. Qual é o defeito e qual é a linha corrigida exata?
T2. No t2_videos.csv, qual é a soma da coluna views das linhas com canal "Verse" E status "postado"? (número exato)
T3. No t3_config.json, qual é o valor de vigia.pausa_max?
T4. No t4_gateway.log, qual erro aparece mais vezes nas linhas ERROR, e quantas vezes? Dê também o total de linhas ERROR.
T5. t5_main.py devia imprimir "conta7 pausada 20 min: limite". Qual é o defeito (arquivo e linha) e a linha corrigida?
T6. Quais destes nomes casam com o regex {padrao} ? {nomes}
Responda numerado T1..T6, uma resposta curta por tarefa."""
(AQUI / "TAREFAS.txt").write_text(tarefas, encoding="utf-8")
gab = {
    "T1": "range(len(valores) - janela + 1) — o laço perde a última janela (linha 4)",
    "T2": t2,
    "T3": "não existe (vigia só tem limite_mb)",
    "T4": {"mais": "429 rate limited", "vezes": 37, "total_error": len(erros)},
    "T5": 't5_main.py linha 6: argumentos trocados -> return pausar(conta, 20, "limite")',
    "T6": t6,
}
(AQUI / "GABARITO.json").write_text(json.dumps(gab, ensure_ascii=False, indent=2), encoding="utf-8")
print(tarefas)
print(json.dumps(gab, ensure_ascii=False, indent=2))
