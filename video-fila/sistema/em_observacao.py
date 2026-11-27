# gera D:\sistema\mapa\EM_OBSERVACAO_lista.md - lista completa (so leitura) do que esta em observacao
import json, os, re, sys, time
sys.argv = ["x"]
src = open(r"D:\sistema\catalogo\limpar_scripts.py", encoding="utf-8").read().split("\na = sys.argv[1:]")[0]
exec(src)
codigos, vivo, mortos, motivo, dias = classificar()
grupos = {}
for c in codigos:
    m = motivo.get(c, "MORTO (sai na limpeza das 06:30)")
    if m.startswith("mexido"):
        m = "mexido nos ultimos 14 dias"
    grupos.setdefault(m, []).append(c)
L = ["# Lista completa do que esta EM OBSERVACAO (gerada " + time.strftime("%d/%m/%Y %H:%M") + ")", "",
     "Resumo e regras: D:\\sistema\\EM_OBSERVACAO.md. Esta lista e gerada de novo pelo diario 06:30.", "",
     "## Scripts que FICAM SO POR PRECAUCAO (sem prova de uso real)", ""]
for g in ("mexido nos ultimos 14 dias", "citado por valido"):
    L += [f"### {g}: {len(grupos.get(g, []))} scripts", ""]
    por = {}
    for c in grupos.get(g, []):
        k = "\\".join(os.path.relpath(c, RAIZ).split("\\")[:3])
        por.setdefault(k, []).append(os.path.relpath(c, RAIZ))
    for k, v in sorted(por.items(), key=lambda x: -len(x[1])):
        L.append(f"- **{k}** ({len(v)})")
        for x in sorted(v):
            L.append(f"  - {x}")
    L.append("")
L += ["## Scripts com PROVA de uso (ficam)", ""]
for g in ("rodou (uso real)", "tarefa/processo", "codigo comum", "__init__", "pasta de notebook"):
    L.append(f"- {g}: {len(grupos.get(g, []))}")
L += ["", f"## Mortos que ainda vao sair: {len(mortos)}", ""] + [f"- {os.path.relpath(m, RAIZ)}" for m in mortos]
n = json.load(open(r"D:\sistema\mapa\nao_codigo_27nov.json", encoding="utf-8"))
L += ["", "## Arquivos que NAO sao codigo (levantamento 27/11)", "", "| tipo | arquivos | GB |", "|---|---|---|"]
for t, (q, b) in sorted(n["tot"].items(), key=lambda x: -x[1][1]):
    L.append(f"| {t} | {q} | {b/1e9:.2f} |")
L += ["", "### Candidatos a lixo (14+ dias sem mexer)", "", "| motivo | arquivos | GB |", "|---|---|---|"]
for t, (q, b) in sorted(n["cand"].items(), key=lambda x: -x[1][1]):
    L.append(f"| {t} | {q} | {b/1e9:.2f} |")
L += ["", "### Onde estao os candidatos", "", "| pasta | arquivos | GB |", "|---|---|---|"]
for t, (q, b) in sorted(n["pastas"].items(), key=lambda x: -x[1][1])[:40]:
    L.append(f"| {t} | {q} | {b/1e9:.2f} |")
open(r"D:\sistema\mapa\EM_OBSERVACAO_lista.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("ok", {k: len(v) for k, v in grupos.items()}, "| linhas:", len(L))
