"""falas_ia.py — escolhe pela IA as falas GENÉRICAS de cada narrador (04/11/2026; dona: "inserir o máximo de falas
originais dos narradores que sejam genéricas — jargões, piadas que servem pra todos").

As regras de palavra-chave do falas_narradores.py acharam só 6 falas nas 2h23 do Porão. Aqui o Gemini 3.8 (o mesmo
claude_client dos roteiros) lê a transcrição em blocos e marca cada trecho que serve em QUALQUER recap: bordão,
piada/expressão que não depende da história, reação, transição, cumprimento, pedido de inscrição, despedida.
Grava genericos.json na VPS; o falas_narradores.py corta essa lista (junto com as regras).

    python falas_ia.py <voz> [<voz> ...]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import claude_client  # noqa: E402

VPS = "hermes-staging"
REMOTO = "/opt/narradores/dados"
TMP = Path(r"D:\tmp\falas_ia")
BLOCO = 120

PEDIDO = """Abaixo, trechos numerados da fala de um narrador brasileiro de recap de manhwa/anime no YouTube.
Marque SÓ os trechos GENÉRICOS — que poderiam entrar em QUALQUER outro vídeo de recap dele sem soar estranho, porque
NÃO falam da história, de personagem, nome, poder ou acontecimento específico. Exemplos de genérico: bordão,
cumprimento ("salve rapaziada"), pedido de inscrição/like/comentário, despedida, reação solta ("caraca, que isso",
"meu Deus do céu"), risada, piada ou comentário que serve pra qualquer cena ("esse cara não tem limite", "olha a
cara dele kkk"), transição ("bora pro próximo capítulo", "mas calma que piora"). Trecho que cita qualquer coisa da
história NÃO é genérico.
Responda SÓ JSON: [{"n": <número>, "cat": "saudacao|inscricao|despedida|reacao|risada|piada|bordao|transicao",
"nota": <1-10, quão bom e engraçado/marcante pra reusar>}]. Lista vazia se nenhum.

"""


def escolher(voz):
    TMP.mkdir(parents=True, exist_ok=True)
    local = TMP / f"{voz}_transcricao.json"
    subprocess.run(["scp", "-q", f"{VPS}:{REMOTO}/{voz}/transcricao.json", str(local)], check=True, timeout=300)
    trans = json.loads(local.read_text(encoding="utf-8"))
    escolhidos = []
    for b in range(0, len(trans), BLOCO):
        bloco = trans[b:b + BLOCO]
        txt = "\n".join(f"{b + i}: {s['texto']}" for i, s in enumerate(bloco) if s["fim"] - s["ini"] <= 8)
        try:
            resp = claude_client.generate_text(PEDIDO + txt, max_tokens=3000, temperature=0.2, timeout=300)
            m = re.search(r"\[.*\]", resp or "", re.S)
            lista = json.loads(m.group(0)) if m else []
        except Exception as e:  # noqa: BLE001
            print(f"  bloco {b}: falhou ({type(e).__name__})", flush=True)
            continue
        for x in lista:
            try:
                n = int(x["n"])
            except (KeyError, ValueError, TypeError):
                continue
            if 0 <= n < len(trans):
                s = trans[n]
                escolhidos.append({"cat": str(x.get("cat", "bordao")), "nota": x.get("nota"), "ini": s["ini"],
                                   "fim": s["fim"], "texto": s["texto"]})
        print(f"  {voz}: bloco {b // BLOCO + 1}/{(len(trans) + BLOCO - 1) // BLOCO} — {len(escolhidos)} até agora",
              flush=True)
    saida = TMP / f"{voz}_genericos.json"
    saida.write_text(json.dumps(escolhidos, ensure_ascii=False, indent=1), encoding="utf-8")
    subprocess.run(["scp", "-q", str(saida), f"{VPS}:{REMOTO}/{voz}/genericos.json"], check=True, timeout=300)
    cats = {}
    for x in escolhidos:
        cats[x["cat"]] = cats.get(x["cat"], 0) + 1
    print(f"{voz}: {len(escolhidos)} falas genéricas {cats}", flush=True)


if __name__ == "__main__":
    for v in sys.argv[1:]:
        escolher(v)
