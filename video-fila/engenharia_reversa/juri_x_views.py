"""juri_x_views.py — Fable 29/10 (CORTES_05): a nota do júri dos Cortes prevê views / retenção real?
Liga `D:\\video-fila\\linhas\\CORTES\\evolucao.jsonl` (id = pasta do vídeo, nota e notas por dimensão, movimento
medido) ao ledger (caminho → video_id) e daí a medidas_48h (views 48–96 h) e metricas_studio (continuaram,
pct_media, views_periodo, impressoes). Só lê arquivos.   python D:\\video-fila\\engenharia_reversa\\juri_x_views.py
"""
import json
import statistics
import sys
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
POST = Path(r"D:\postador-de-videos")
EVO = Path(r"D:\video-fila\linhas\CORTES\evolucao.jsonl")
med = json.load(open(POST / "config" / "telegram_estado.json", encoding="utf-8")).get("medidas_48h") or {}
ms = json.load(open(POST / "_analise" / "metricas_studio.json", encoding="utf-8"))
por_pasta = {}
for ln in (POST / "logs" / "uploads_ledger.jsonl").read_text("utf-8").splitlines():
    try:
        r = json.loads(ln)
    except ValueError:
        continue
    if r.get("video_id") and r.get("caminho"):
        por_pasta.setdefault(Path(r["caminho"]).parent.name, []).append(r)  # a mesma pasta vai a mais de um canal
juri = {}
for ln in EVO.read_text("utf-8").splitlines():
    try:
        j = json.loads(ln)
    except ValueError:
        continue
    if j.get("nota") is not None:  # só as linhas com júri (1 em 4); as outras têm só movimento
        juri[j["id"]] = j

linhas = []
for pid, j in juri.items():
    rs = por_pasta.get(pid) or []
    if not rs:
        continue
    # prefere a postagem já medida (48 h) ou com retenção; senão a 1ª
    r = next((x for x in rs if x["video_id"] in med), None) or next((x for x in rs if x["video_id"] in ms), rs[0])
    vid = r["video_id"]
    m, s = med.get(vid) or {}, ms.get(vid) or {}
    rl = s.get("ret_lista") or {}
    linhas.append({"id": pid, "vid": vid, "canal": m.get("canal") or r.get("canal"), "nota": j["nota"],
                   **{f"n_{k}": v for k, v in (j.get("notas") or {}).items()}, "graves": j.get("graves"),
                   "mov_med": statistics.median(j["mov"]) if j.get("mov") else None, "dur": j.get("dur"),
                   "views48": m.get("views"), "continuaram": s.get("continuaram"), "pct_media": s.get("pct_media"),
                   "views_periodo": rl.get("views_periodo"), "impressoes": s.get("impressoes")})
print(f"vídeos com júri: {len(juri)} | achados no ledger: {len(linhas)} | com views 48 h: "
      f"{sum(x['views48'] is not None for x in linhas)} | com retenção: {sum(x['continuaram'] is not None for x in linhas)}")


def spearman(xs, ys):
    def postos(l):
        o = sorted(range(len(l)), key=lambda i: l[i])
        p, i = [0.0] * len(l), 0
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
    n = sum((a - mx) * (b - my) for a, b in zip(px, py))
    d = (sum((a - mx) ** 2 for a in px) * sum((b - my) ** 2 for b in py)) ** 0.5
    return n / d if d else 0.0


def bloco(titulo, alvo, filtro=lambda x: True):
    g = [x for x in linhas if x.get(alvo) is not None and filtro(x)]
    if len(g) < 6:
        print(f"\n{titulo}: só {len(g)} vídeo(s), sem conclusão")
        return
    print(f"\n{titulo} (n={len(g)}): Spearman de cada nota com {alvo}")
    for k in ("nota", "n_legibilidade", "n_movimento", "n_historia", "n_retencao", "graves", "mov_med", "dur"):
        pares = [(x[k], x[alvo]) for x in g if x.get(k) is not None]
        if len(pares) >= 6:
            print(f"  {k:<16} {spearman([a for a, _ in pares], [b for _, b in pares]):+.2f}  (n {len(pares)})")
    s = sorted(g, key=lambda x: x["nota"])
    t = len(s) // 3
    for nome, parte in (("nota baixa", s[:t]), ("média", s[t:2 * t]), ("alta", s[2 * t:])):
        v = [x[alvo] for x in parte]
        if v:
            print(f"  {nome:<10} notas {min(x['nota'] for x in parte):.1f}–{max(x['nota'] for x in parte):.1f} "
                  f"| {alvo} mediana {statistics.median(v):.0f} | ≥500: {sum(x >= 500 for x in v)}/{len(v)}")


bloco("JÚRI × VIEWS 48 h (todos)", "views48")
bloco("JÚRI × VIEWS 48 h (só quem recebeu o lote: views_periodo ≥ 20)", "views48",
      lambda x: (x.get("views_periodo") or 0) >= 20)
bloco("JÚRI × CONTINUARAM (só lote)", "continuaram", lambda x: (x.get("views_periodo") or 0) >= 20)
bloco("JÚRI × % ASSISTIDO (só lote)", "pct_media", lambda x: (x.get("views_periodo") or 0) >= 20)
print("\nlista (nota | views48 | continuaram | pct | canal | id):")
for x in sorted(linhas, key=lambda x: -(x["views48"] or -1))[:15]:
    print(f"  {x['nota']:.2f} | {x['views48'] if x['views48'] is not None else '—':>5} | "
          f"{x['continuaram'] or '—':>5} | {x['pct_media'] or '—':>5} | {str(x['canal'])[:18]:<18} {x['id']}")
