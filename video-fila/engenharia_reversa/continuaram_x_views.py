"""continuaram_x_views.py — Fable 29/10 (ER_01 tarefa 1): separar "foi mostrado e perdeu" de "nem foi mostrado".

O Studio já devolve, por Short, "continuaram assistindo" (= % que não deslizou no feed; metricas_studio.json,
campos continuaram/dur_media/pct_media vindos do retencao_lista do metricas_rede desde 23/10). Cruza isso com as
views de 48–96 h (medidas_48h) e a ficha (postar.json) e responde:
  - os Shorts de 0–10 views TÊM leitura de "continuaram"? (sem leitura/—  = o feed nem mostrou)
  - entre os que têm, "continuaram" separa alto (>=500) de baixo (<10) DENTRO do mesmo canal?
  - duração média assistida x duração do vídeo nos dois grupos.
Só lê arquivos; nada de navegador nem IA.   python D:\video-fila\engenharia_reversa\continuaram_x_views.py [--csv]
"""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
POST = Path(r"D:\postador-de-videos")
AQUI = Path(__file__).resolve().parent
med = json.load(open(POST / "config" / "telegram_estado.json", encoding="utf-8")).get("medidas_48h") or {}
ms = json.load(open(POST / "_analise" / "metricas_studio.json", encoding="utf-8"))
led = {}
for ln in (POST / "logs" / "uploads_ledger.jsonl").read_text("utf-8").splitlines():
    try:
        r = json.loads(ln)
    except ValueError:
        continue
    if r.get("video_id"):
        led[r["video_id"]] = r


def _ficha(r):
    try:
        return json.loads((Path(r["caminho"]).parent / "postar.json").read_text(encoding="utf-8"))
    except (KeyError, OSError, ValueError, TypeError):
        return {}


linhas = []
for vid, m in med.items():
    r = led.get(vid) or {}
    if r.get("projeto") != "parceiro" or r.get("tipo") not in (None, "short") or m.get("views") is None:
        continue
    s = ms.get(vid) or {}
    rl = s.get("ret_lista") or {}
    f = _ficha(r)
    linhas.append({
        "vid": vid, "canal": m.get("canal") or r.get("canal"), "views48": float(m["views"]),
        "continuaram": s.get("continuaram"), "dur_media": s.get("dur_media"), "pct_media": s.get("pct_media"),
        "views_periodo": rl.get("views_periodo"), "lido_ret": bool(rl), "views_total": s.get("views"),
        "nicho": f.get("midia") or "?", "parceiro": f.get("parceiro") or "?", "idioma": f.get("idioma") or "?",
        "dur_video": f.get("duracao") or f.get("dur") or (f.get("video") or {}).get("duracao"),
        "titulo": (f.get("titulo") or m.get("titulo") or "")[:70],
    })

print(f"Shorts de parceiro com views de 48–96 h: {len(linhas)}")
faixa = lambda v: "0" if v == 0 else "1-9" if v < 10 else "10-99" if v < 100 else "100-499" if v < 500 else ">=500"
grupos = defaultdict(list)
for x in linhas:
    grupos[faixa(x["views48"])].append(x)
print("\nfaixa de views (48 h) | n | com leitura de retenção | com 'continuaram' | mediana continuaram | mediana dur_media | mediana pct_media")
for k in ("0", "1-9", "10-99", "100-499", ">=500"):
    g = grupos.get(k, [])
    if not g:
        continue
    cont = [x["continuaram"] for x in g if x["continuaram"] is not None]
    dur = [x["dur_media"] for x in g if x["dur_media"] is not None]
    pct = [x["pct_media"] for x in g if x["pct_media"] is not None]
    f = lambda l, u="": f"{statistics.median(l):.0f}{u}" if l else "—"
    print(f"  {k:<8} {len(g):>4} | {sum(x['lido_ret'] for x in g):>4} | {len(cont):>4} | {f(cont, '%'):>6} | "
          f"{f(dur, 's'):>6} | {f(pct, '%'):>6}")

# dentro do mesmo canal: alto (>=500) x baixo (<10), só quem tem 'continuaram'
print("\nDENTRO do mesmo canal (só vídeos com 'continuaram' lido): canal | n alto / n baixo | continuaram alto x baixo | dur_media alto x baixo")
por_canal = defaultdict(lambda: {"alto": [], "baixo": []})
for x in linhas:
    if x["continuaram"] is None:
        continue
    if x["views48"] >= 500:
        por_canal[x["canal"]]["alto"].append(x)
    elif x["views48"] < 10:
        por_canal[x["canal"]]["baixo"].append(x)
pares_c, pares_d = [], []
for c, g in sorted(por_canal.items(), key=lambda kv: -(len(kv[1]["alto"]) + len(kv[1]["baixo"]))):
    a, b = g["alto"], g["baixo"]
    if not a or not b:
        continue
    ca, cb = statistics.median(x["continuaram"] for x in a), statistics.median(x["continuaram"] for x in b)
    da, db = statistics.median(x["dur_media"] or 0 for x in a), statistics.median(x["dur_media"] or 0 for x in b)
    pares_c.append((ca, cb))
    pares_d.append((da, db))
    print(f"  {str(c)[:24]:<24} {len(a):>2} / {len(b):<2} | {ca:>5.0f}% x {cb:>5.0f}% | {da:>4.0f}s x {db:>4.0f}s")
if pares_c:
    print(f"  canais com os dois grupos: {len(pares_c)}; alto > baixo em continuaram: {sum(a > b for a, b in pares_c)}; "
          f"em dur_media: {sum(a > b for a, b in pares_d)}")

# views_periodo (4 semanas, da própria tabela do Studio) x views de 48 h: baixo que "cresceu depois"?
cres = [x for x in linhas if x["views_periodo"] and x["views48"] < 10 and x["views_periodo"] >= 100]
print(f"\nShorts com <10 views em 48 h que depois passaram de 100 (views_periodo da tabela): {len(cres)}")
for x in sorted(cres, key=lambda x: -x["views_periodo"])[:8]:
    print(f"  {x['views48']:>3.0f} -> {x['views_periodo']:>6.0f}  {x['canal']:<20} {x['titulo']}")

# continuaram x views (todos com dado, e com >= 20 views_periodo pra ter amostra)
with_c = [x for x in linhas if x["continuaram"] is not None and (x["views_periodo"] or 0) >= 20]
if len(with_c) >= 10:
    xs = [x["continuaram"] for x in with_c]
    ys = [x["views48"] for x in with_c]
    # correlação de postos (Spearman) à mão
    def postos(l):
        o = sorted(range(len(l)), key=lambda i: l[i])
        p = [0.0] * len(l)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and l[o[j + 1]] == l[o[i]]:
                j += 1
            for k in o[i:j + 1]:
                p[k] = (i + j) / 2 + 1
            i = j + 1
        return p
    px, py = postos(xs), postos(ys)
    mx, my = statistics.mean(px), statistics.mean(py)
    num = sum((a - mx) * (b - my) for a, b in zip(px, py))
    den = (sum((a - mx) ** 2 for a in px) * sum((b - my) ** 2 for b in py)) ** 0.5
    print(f"\nSpearman continuaram x views48 (n={len(with_c)}, views_periodo>=20): {num / den if den else 0:+.2f}")
    # por tercil de continuaram
    s = sorted(with_c, key=lambda x: x["continuaram"])
    t = len(s) // 3
    for nome, parte in (("continuaram baixo", s[:t]), ("médio", s[t:2 * t]), ("alto", s[2 * t:])):
        v = [x["views48"] for x in parte]
        c = [x["continuaram"] for x in parte]
        print(f"  {nome:<18} n={len(parte):>3} continuaram {min(c):.0f}–{max(c):.0f}% | views48 mediana {statistics.median(v):.0f} "
              f"| >=500: {sum(x >= 500 for x in v) / len(v):.0%}")

if "--csv" in sys.argv:
    import csv
    with open(AQUI / "continuaram_x_views.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print(f"\ncsv: {AQUI / 'continuaram_x_views.csv'}")
