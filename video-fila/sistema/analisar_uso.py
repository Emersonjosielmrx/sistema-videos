# D:\sistema\catalogo\analisar_uso.py   (copia mestre: /mnt/win-bootcamp/claude-central/sistema/analisar_uso.py)
# OBRA sistema unico - cruza o USO REAL (D:\sistema\mapa\uso\uso_*.jsonl, gravado pelo sistema_uso em cada Python)
# com o catalogo e o mapa estatico (mapa_vivo.json). Somente leitura. Tarefa SistemaUnificacao (diaria 06:30).
# Responde automaticamente:
#   1) o que esta VIVO de verdade (carregado por algum processo nos ultimos N dias) e por projeto;
#   2) o que esta MORTO (nas pastas dos projetos, nem o mapa estatico alcanca nem foi carregado, sem mexer ha 14 dias);
#   3) para cada tarefa: quais pacotes ela usou de verdade e se o Python principal (D:\veo\venv) ja tem todos
#      -> pronta para trocar de Python | falta pacote X | so manual (usa navegador: playwright/selenium/uiautomator2).
# Saida: D:\sistema\mapa\RELATORIO_UNIFICACAO.md e unificacao.json. Uma linha resumo para a ronda: --ronda
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAPA = Path(r"D:\sistema\mapa")
CAT = json.loads(Path(r"D:\sistema\catalogo\sistema.json").read_text(encoding="utf-8-sig"))
PRINCIPAL = r"d:\veo\venv\scripts"
MANUAL = {"playwright", "selenium", "undetected_chromedriver", "uiautomator2", "patchright", "nodriver", "pyautogui"}
DIAS = int(os.environ.get("USO_DIAS", "7"))

# ---- 1) uso real ----
linhas = []
for f in sorted(MAPA.glob("uso/uso_*.jsonl"))[-DIAS:]:
    for l in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            linhas.append(json.loads(l))
        except ValueError:
            pass
dias_com_dado = len(sorted(MAPA.glob("uso/uso_*.jsonl"))[-DIAS:])
carregados = set()
por_main = {}
for j in linhas:
    for a in j.get("locais", []):
        carregados.add(a.lower().removesuffix("c") if a.lower().endswith(".pyc") else a.lower())
    m = (j.get("main") or "").lower()
    if m.endswith(".py"):
        carregados.add(m)
        d = por_main.setdefault(m, {"py": set(), "ext": set(), "vezes": 0})
        d["py"].add((j.get("py") or "").lower())
        d["ext"].update(j.get("externos", []))
        d["vezes"] += 1

# ---- 2) morto = fora do mapa estatico E nunca carregado E sem mexer ha 14 dias ----
try:
    estat = json.loads((MAPA / "mapa_vivo.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    estat = {"vivos": {}, "mortos": []}
vivos_estat = set(estat.get("vivos", {}))
mortos = [m for m in estat.get("mortos", []) if m[0] not in carregados and m[0] not in vivos_estat]
vivo_so_em_uso = sorted(a for a in carregados if a not in vivos_estat and a.endswith(".py"))

# ---- 3) python por tarefa (pelo uso real) ----
tem = {}
todos = sorted({e for d in por_main.values() for e in d["ext"]})
if todos:
    prog = ("import importlib.util,json,sys\n"
            "def ok(m):\n"
            "    try:\n        return importlib.util.find_spec(m) is not None\n"
            "    except Exception:\n        return False\n"
            "print(json.dumps({m: ok(m) for m in json.loads(sys.argv[1])}))")
    try:
        r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", "-c", prog, json.dumps(todos)], capture_output=True,
                           text=True, timeout=300, env={**os.environ, "SISTEMA_USO": "0"},
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        tem = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        pass
tarefas = []
for pid, p in CAT["projetos"].items():
    for nome, det in p.get("tarefas_detalhe", {}).items():
        if not det.get("ligada"):
            continue
        cmd = det["cmd"].lower().replace('"', "")
        usos = [(m, d) for m, d in por_main.items() if m in cmd]
        if not usos:
            tarefas.append({"tarefa": nome, "projeto": pid, "situacao": "sem uso registrado ainda"})
            continue
        py = set().union(*(d["py"] for _, d in usos))
        ext = {e for e in set().union(*(d["ext"] for _, d in usos)) if not e.endswith("__mypyc") and not e.startswith("_")}
        no_principal = all(x.startswith(PRINCIPAL) for x in py)
        faltam = sorted(e for e in ext if not tem.get(e, False))
        if no_principal:
            sit = "ja no principal"
        elif ext & MANUAL:
            sit = "so manual (navegador: " + ", ".join(sorted(ext & MANUAL)) + ")"
        elif faltam:
            sit = "falta no principal: " + ", ".join(faltam[:8])
        else:
            sit = "PRONTA para trocar"
        tarefas.append({"tarefa": nome, "projeto": pid, "situacao": sit, "py": sorted(py), "externos": sorted(ext)})

cont = {}
for t in tarefas:
    k = t["situacao"].split(":")[0].split(" (")[0]
    cont[k] = cont.get(k, 0) + 1
res = {"gerado": time.strftime("%Y-%m-%d %H:%M"), "dias_de_uso": dias_com_dado, "processos_registrados": len(linhas),
       "vivos_reais": len(carregados), "vivo_so_em_uso": vivo_so_em_uso, "mortos": mortos, "tarefas": tarefas, "contagem": cont}
(MAPA / "unificacao.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

# quarentena: algo carregou arquivo de pasta que foi para a quarentena? (caminho antigo continua valendo pela juncao)
em_q = []
try:
    qi = json.loads(Path(r"D:\sistema\quarentena\INDICE.json").read_text(encoding="utf-8"))
    origs = [(e["original"].lower().rstrip("\\") + "\\", e["em"]) for e in qi if not e.get("voltou")]
    for j in linhas:
        for a in j.get("locais", []) + [j.get("main", "")]:
            for o, em in origs:
                if a.lower().startswith(o) and j.get("t", "") > em.replace("T", " "):
                    em_q.append(a)
except (OSError, ValueError):
    pass
res["quarentena_em_uso"] = sorted(set(em_q))

if "--ronda" in sys.argv:
    for a in sorted(set(em_q))[:10]:
        print(f"  !! QUARENTENA EM USO (voltar com quarentena.py --voltar): {a}")
    print(f"[UNIFICACAO] {dias_com_dado} dia(s) de uso real, {len(linhas)} processos | vivos reais {len(carregados)} |"
          f" mortos candidatos {len(mortos)} | python: " + ", ".join(f"{k} {v}" for k, v in sorted(cont.items())))
    sys.exit(0)

md = [f"# RELATÓRIO DE UNIFICAÇÃO — {res['gerado']}", "",
      f"Base: **{dias_com_dado} dia(s)** de uso real ({len(linhas)} processos Python registrados) + mapa estático.",
      "**Só confiar na lista de mortos com 3+ dias de uso real.**", "",
      f"- Arquivos .py carregados de verdade: **{len(carregados)}** (destes, {len(vivo_so_em_uso)} o mapa estático não enxergava)",
      f"- Candidatos a morto (fora do mapa, nunca carregados, sem mexer há 14 dias): **{len(mortos)}**", "",
      "## Python único — situação por tarefa", "| Situação | Tarefas |", "|---|---:|"]
md += [f"| {k} | {v} |" for k, v in sorted(cont.items(), key=lambda x: -x[1])]
md += ["", "### Prontas para trocar para D:\\veo\\venv", ""]
md += [f"- {t['tarefa']} ({t['projeto']}) — hoje: {', '.join(t['py'])}" for t in tarefas if t["situacao"] == "PRONTA para trocar"] or ["- (nenhuma ainda)"]
md += ["", "### Faltam pacotes no principal", ""]
md += [f"- {t['tarefa']}: {t['situacao']}" for t in tarefas if t["situacao"].startswith("falta")] or ["- (nenhuma)"]
(MAPA / "RELATORIO_UNIFICACAO.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md[:30]))
