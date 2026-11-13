"""
LiciBot-IA · comparar_modelos.py
Roda outro modelo (ex.: Gemini) nos editais que o Opus JÁ analisou e compara, sem gravar nada nos editais.
    venv/bin/python comparar_modelos.py --modelo gemini-fila --n 30
Saída: comparacao_<modelo>.json (bruto) e o resumo no terminal.
"""

import argparse
import hashlib
import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import database as db
from ai_analyzer import AnaliseFalhou, analisar
from config import normalizar

BASE = Path(__file__).resolve().parent


def amostra(n: int, semente: int) -> list[dict]:
    """Mistura de carteiras do Opus: metade MEI, um quarto descartadas, o resto CPF/solar (o que houver)."""
    with db.conexao() as c:
        por = {}
        for cart in ("MEI", "DESCARTADO", "AMIGO_SOLAR", "CPF"):
            por[cart] = [dict(r) for r in c.execute(
                "SELECT * FROM editais WHERE status='analisado' AND carteira=? AND json_ia IS NOT NULL "
                "AND modelo_ia LIKE 'claude-opus%'", (cart,))]
    rnd = random.Random(semente)
    quer = {"MEI": n // 2, "DESCARTADO": n // 4, "AMIGO_SOLAR": n // 8, "CPF": n // 8}
    escolha = []
    for cart, q in quer.items():
        escolha += rnd.sample(por[cart], min(q, len(por[cart])))
    resto = [e for v in por.values() for e in v if e not in escolha]
    escolha += rnd.sample(resto, min(n - len(escolha), len(resto)))
    return escolha


def rodar(modelo: str, editais: list[dict], paralelo: int, prompt: str) -> list[dict]:
    descontos = db.descontos_historicos()

    def um(e):
        t = time.time()
        try:
            r = analisar(e, db.itens_de(e["numero_controle"]), descontos, modelo=modelo, prompt=prompt)
            return {"n": e["numero_controle"], "ok": True, "seg": round(time.time() - t, 1), **r}
        except AnaliseFalhou as err:
            return {"n": e["numero_controle"], "ok": False, "seg": round(time.time() - t, 1), "erro": str(err)}
        except Exception as err:
            return {"n": e["numero_controle"], "ok": False, "seg": round(time.time() - t, 1),
                    "erro": f"{type(err).__name__}: {err}"}

    with ThreadPoolExecutor(paralelo) as ex:
        return list(ex.map(um, editais))


_PARADAS = set("de da do das dos e o a os as em no na nos nas para por com sem ao aos um uma que se ou é não mais até "
               "após sobre pelo pela entre como edital item itens prazo".split())


def _termos(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9%]{4,}", normalizar(s)) if w not in _PARADAS}


def cobertura(gabarito: list, outro: list) -> float | None:
    """Fração dos itens do Opus que aparecem no outro (>= 35% das palavras-chave em algum item do outro)."""
    gab = [_termos(g) for g in (gabarito or []) if g]
    out = [_termos(o) for o in (outro or []) if o]
    if not gab:
        return None
    achou = sum(1 for g in gab if g and any(len(g & o) / len(g) >= 0.35 for o in out))
    return achou / len(gab)


def _equilibrar(eds: list[dict], n: int, semente: int) -> list[dict]:
    """Mesma proporção de carteiras do Opus que amostra() (metade MEI, 1/4 descartadas, resto solar/CPF)."""
    rnd = random.Random(semente)
    por = {}
    for e in eds:
        por.setdefault(e["carteira"], []).append(e)
    quer = {"MEI": n // 2, "DESCARTADO": n // 4, "AMIGO_SOLAR": n // 8, "CPF": n // 8}
    out = []
    for cart, q in quer.items():
        out += rnd.sample(por.get(cart, []), min(q, len(por.get(cart, []))))
    resto = [e for e in eds if e not in out]
    return out + rnd.sample(resto, min(n - len(out), len(resto)))


def comparar(opus: dict, outro: dict) -> dict:
    io = json.loads(opus["json_ia"])
    oo = json.loads(outro["json_ia"])
    return {
        "n": opus["numero_controle"],
        "objeto": (opus["objeto_compra"] or "")[:140],
        "opus_carteira": opus["carteira"], "outro_carteira": outro["carteira"],
        "mesma_carteira": opus["carteira"] == outro["carteira"],
        "mesmo_lado": (opus["carteira"] == "DESCARTADO") == (outro["carteira"] == "DESCARTADO"),
        "opus_viab": opus["score_viabilidade"], "outro_viab": outro["score_viabilidade"],
        "opus_nota": opus["nota_final"], "outro_nota": outro["nota_final"],
        "opus_presencial": bool(io.get("exige_presencial")), "outro_presencial": bool(oo.get("exige_presencial")),
        "opus_pf": io.get("aceita_pessoa_fisica"), "outro_pf": oo.get("aceita_pessoa_fisica"),
        "opus_cnae": opus["cnae_sugerido"], "outro_cnae": outro["cnae_sugerido"],
        "opus_n_exig": len(io.get("exigencias_habilitacao") or []), "outro_n_exig": len(oo.get("exigencias_habilitacao") or []),
        "opus_n_riscos": len(io.get("riscos") or []), "outro_n_riscos": len(oo.get("riscos") or []),
        "opus_resumo": opus["resumo_ia"], "outro_resumo": outro["resumo_ia"],
        "opus_riscos": io.get("riscos"), "outro_riscos": oo.get("riscos"),
        "opus_exig": io.get("exigencias_habilitacao"), "outro_exig": oo.get("exigencias_habilitacao"),
        "cob_riscos": cobertura(io.get("riscos"), oo.get("riscos")),
        "cob_exig": cobertura(io.get("exigencias_habilitacao"), oo.get("exigencias_habilitacao")),
        "dif_viab": abs((opus["score_viabilidade"] or 0) - (outro["score_viabilidade"] or 0)),
        "opus_tokens": opus["tokens_ia"], "outro_tokens": outro["tokens_ia"],
        "outro_seg": outro["seg"], "outro_modelo": outro["modelo_ia"],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--modelo", default="gemini-fila")
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--paralelo", type=int, default=3)
    p.add_argument("--semente", type=int, default=11)
    p.add_argument("--prompt", default="v1")
    p.add_argument("--grupo", choices=["ajuste", "prova"], default="prova",
                   help="ajuste = editais para mexer no prompt; prova = outros editais, só para medir")
    a = p.parse_args()

    # os dois grupos nunca se misturam: ajuste = número de controle com hash par, prova = ímpar
    eds = [e for e in amostra(10_000, a.semente)
           if (int(hashlib.md5(e["numero_controle"].encode()).hexdigest(), 16) % 2 == 0) == (a.grupo == "ajuste")]
    eds = _equilibrar(eds, a.n, a.semente)
    print(f"{len(eds)} editais ({a.grupo}) já analisados pelo Opus; rodando {a.modelo} prompt {a.prompt} "
          f"({a.paralelo} por vez)...", flush=True)
    t = time.time()
    res = rodar(a.modelo, eds, a.paralelo, a.prompt)
    por_n = {e["numero_controle"]: e for e in eds}
    falhas = [r for r in res if not r["ok"]]
    linhas = [comparar(por_n[r["n"]], r) for r in res if r["ok"]]

    saida = BASE / f"comparacao_{a.modelo.replace('/', '_')}_{a.prompt}_{a.grupo}.json"
    saida.write_text(json.dumps({"modelo": a.modelo, "linhas": linhas, "falhas": falhas,
                                 "duracao_s": round(time.time() - t)}, ensure_ascii=False, indent=1, default=str),
                     encoding="utf-8")

    ok = len(linhas)
    print(f"\n=== {a.modelo}: {ok}/{len(res)} responderam no formato ({len(falhas)} falhas) em {time.time() - t:.0f} s")
    for f in falhas[:5]:
        print("  falha:", f["n"], f["erro"][:150])
    if not ok:
        return
    pct = lambda k: f"{100 * sum(l[k] for l in linhas) / ok:.0f}%"
    med = lambda k: sum((l[k] or 0) for l in linhas) / ok
    print(f"mesma carteira que o Opus: {pct('mesma_carteira')}   |   mesma decisão vale/descarta: {pct('mesmo_lado')}")
    print(f"viabilidade média  Opus {med('opus_viab'):.0f}  x  {med('outro_viab'):.0f}")
    print(f"nota final média   Opus {med('opus_nota'):.0f}  x  {med('outro_nota'):.0f}")
    def media_cob(k):
        v = [l[k] for l in linhas if l[k] is not None]
        return f"{100 * sum(v) / len(v):.0f}%" if v else "—"
    print(f"riscos do Opus que ele também achou: {media_cob('cob_riscos')}   |   exigências: {media_cob('cob_exig')}"
          f"   |   diferença média de viabilidade: {med('dif_viab'):.0f} pontos")
    print(f"exigências listadas Opus {med('opus_n_exig'):.1f}  x  {med('outro_n_exig'):.1f}   |   "
          f"riscos Opus {med('opus_n_riscos'):.1f}  x  {med('outro_n_riscos'):.1f}")
    print(f"tokens por edital  Opus {med('opus_tokens'):.0f}  x  {med('outro_tokens'):.0f}   |   "
          f"tempo {med('outro_seg'):.0f} s ({linhas[0]['outro_modelo']})")
    print("\nDivergências (Opus → outro):")
    for l in linhas:
        if not l["mesma_carteira"]:
            print(f"  {l['opus_carteira']:>11} → {l['outro_carteira']:<11} {l['objeto'][:90]}")
    print(f"\nDetalhe completo em {saida}")


if __name__ == "__main__":
    main()
