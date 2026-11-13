"""Título x views DENTRO do mesmo parceiro (29/10). Usa só as listas que o Cortes já guardou
(workspace\\cache\\discover_canal, --flat-playlist), sem yt-dlp. Para cada parceiro: 10% de cima x 10% de baixo
por views; compara traços do título. Grava titulos_parceiros.json."""
import json, math, re, statistics, sys
from collections import defaultdict
from pathlib import Path
if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
CACHE = Path(r"D:\recapd-ambientes\producao\workspace\cache\discover_canal")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")


def tracos(t):
    base = re.sub(r"#\S+", "", t).strip()
    letras = [c for c in base if c.isalpha()]
    pal = base.split()
    return {
        "chars": len(base),
        "palavras": len(pal),
        "% maiúsculas": sum(c.isupper() for c in letras) / max(1, len(letras)),
        "palavra TODA maiúscula": sum(1 for p in pal if len(p) > 2 and p.isupper()),
        "tem ?": "?" in base,
        "tem !": "!" in base,
        "tem emoji": bool(EMOJI.search(t)),
        "tem número": bool(re.search(r"\d", base)),
        "hashtags": len(re.findall(r"#\S+", t)),
        "começa com pergunta": bool(re.match(r"(?i)(por ?que|como|o que|quem|qual|você|voce|why|how|what|who|did you)", base)),
        "você/you": bool(re.search(r"(?i)\b(você|voce|vc|you|your)\b", base)),
        "ele/ela/he/she": bool(re.search(r"(?i)\b(ele|ela|he|she|this guy|this girl|esse cara)\b", base)),
        "parte N": bool(re.search(r"(?i)\b(part|parte)\.?\s*\d", t)),
    }


por = {}
for f in CACHE.glob("*.json"):
    try:
        itens = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        continue
    itens = [i for i in itens if i.get("views")]
    if len(itens) < 30:
        continue
    url = itens[0].get("parceiro") or f.stem
    nome = re.sub(r".*/@([^/]+).*", r"\1", url)
    por[nome] = itens
print(f"parceiros com >= 30 Shorts: {len(por)} | Shorts: {sum(len(v) for v in por.values())}")

# diferença média (cima - baixo) de cada traço, parceiro a parceiro; conta em quantos parceiros vai pro mesmo lado
dif = defaultdict(list)
resumo = {}
for nome, itens in por.items():
    itens.sort(key=lambda i: -i["views"])
    k = max(3, len(itens) // 10)
    cima, baixo = itens[:k], itens[-k:]
    resumo[nome] = {"n": len(itens), "mediana": statistics.median(i["views"] for i in itens),
                    "corte_cima": cima[-1]["views"], "corte_baixo": baixo[0]["views"],
                    "exemplos_cima": [i["title"][:90] for i in cima[:3]], "exemplos_baixo": [i["title"][:90] for i in baixo[:3]]}
    tc = [tracos(i["title"]) for i in cima]
    tb = [tracos(i["title"]) for i in baixo]
    for chave in tc[0]:
        a = statistics.mean(float(x[chave]) for x in tc)
        b = statistics.mean(float(x[chave]) for x in tb)
        dif[chave].append((a, b))

print("\ntraço | média nos 10% de cima | nos 10% de baixo | parceiros em que cima > baixo / cima < baixo")
saida = {}
for chave, pares in dif.items():
    a = statistics.mean(p[0] for p in pares)
    b = statistics.mean(p[1] for p in pares)
    mais = sum(p[0] > p[1] + 1e-9 for p in pares)
    menos = sum(p[0] < p[1] - 1e-9 for p in pares)
    saida[chave] = {"cima": round(a, 3), "baixo": round(b, 3), "parceiros_cima_maior": mais, "parceiros_cima_menor": menos}
    print(f"  {chave:<24} {a:>8.2f} | {b:>8.2f} | {mais:>3} / {menos:<3}")
(AQUI / "titulos_parceiros.json").write_text(json.dumps({"tracos": saida, "parceiros": resumo}, ensure_ascii=False,
                                                         indent=1), encoding="utf-8")
print("\nmaior distância de views (cima/baixo) por parceiro:")
for nome, r in sorted(resumo.items(), key=lambda kv: -kv[1]["mediana"])[:12]:
    print(f"  {nome:<22} n {r['n']:>4} med {r['mediana']:>10,.0f} | 10% cima >= {r['corte_cima']:>11,} | 10% baixo <= {r['corte_baixo']:>9,}")
