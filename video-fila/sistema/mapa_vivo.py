# D:\sistema\catalogo\mapa_vivo.py   (copia mestre: /mnt/win-bootcamp/claude-central/sistema/mapa_vivo.py)
# OBRA sistema unico - MAPA DO QUE ESTA VIVO. Somente leitura.
# Parte das tarefas LIGADAS do catalogo (sistema.json) e segue: tarefa -> .bat/.ps1/.vbs -> .py -> imports locais e
# scripts chamados por caminho (subprocess) -> ... Tudo que for alcancado = CODIGO VIVO. Arquivo .py nas pastas dos
# projetos que ninguem alcanca e nao foi mexido ha 14 dias = CANDIDATO A MORTO (vai para quarentena, nunca apagado direto).
# Tambem mede, para cada tarefa, quais pacotes externos ela usa e se o Python principal (D:\veo\venv) ja tem todos.
# Saida: D:\sistema\mapa\mapa_vivo.json e D:\sistema\mapa\MAPA_VIVO.md
import ast
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAT = Path(r"D:\video-fila\sistema\sistema.json")
SAIDA = Path(r"D:\sistema\mapa")
PY_PRINCIPAL = r"D:\veo\venv\Scripts\python.exe"
IGNORA_DIR = re.compile(r"\\(venv[^\\]*|\.venv|site-packages|__pycache__|node_modules|\.git|_bak[^\\]*|backup[^\\]*|"
                        r"bak|_backup|estado\\painel_ia|_testes|testes_antigos|_lixo|quarentena)(\\|$)", re.I)
STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
RE_CAMINHO = re.compile(r"[A-Za-z]:\\\\?[^\"'\n\r;|<>*?]+?\.(?:py|bat|ps1|vbs)\b", re.I)
RE_SYSPATH = re.compile(r"sys\.path\.(?:insert\(\s*\d+\s*,|append\()\s*(?:str\()?\s*r?[\"']([^\"']+)[\"']")
RE_PYEXE = re.compile(r"[A-Za-z]:\\[^\"';]*?python[w]?\.exe", re.I)

cat = json.loads(CAT.read_text(encoding="utf-8-sig"))
vivos = {}          # arquivo -> set(projetos)
externos = {}       # tarefa -> set(pacotes externos)
interp = {}         # tarefa -> interpretador
nao_achados = set()


def norm(p):
    return str(Path(p.replace("\\\\", "\\").strip().strip('"'))).lower()


def ler(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def caminhos_no_texto(txt, base):
    out = []
    for m in RE_CAMINHO.findall(txt):
        out.append(m.replace("\\\\", "\\"))
    # "python algo.py" relativo dentro de .bat/.ps1
    for m in re.findall(r"(?:python[w]?(?:\.exe)?\"?\s+(?:-[-\w]+\s+)*)([\w\-./\\]+\.py)", txt, re.I):
        if not re.match(r"^[A-Za-z]:", m):
            out.append(str(Path(base) / m))
    return out


def modulos_locais(py, arvore, txt):
    base = Path(py).parent
    dirs = [base, base.parent] + [Path(m) for m in RE_SYSPATH.findall(txt) if re.match(r"^[A-Za-z]:", m)]
    achados, ext = [], set()
    for no in ast.walk(arvore):
        nomes = []
        if isinstance(no, ast.Import):
            nomes = [a.name for a in no.names]
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            nomes = [no.module]
        elif isinstance(no, ast.ImportFrom) and no.level > 0:
            for a in no.names:
                cand = base / ((no.module or "").replace(".", "\\")) / f"{a.name}.py"
                if cand.exists():
                    achados.append(str(cand))
            continue
        for n in nomes:
            topo = n.split(".")[0]
            local = None
            for d in dirs:
                c1, c2 = d / (n.replace(".", "\\") + ".py"), d / n.replace(".", "\\") / "__init__.py"
                c3 = d / (topo + ".py")
                for c in (c1, c2, c3):
                    if c.exists():
                        local = c
                        break
                if local:
                    break
            if local:
                achados.append(str(local))
            elif topo not in STDLIB:
                ext.add(topo)
    return achados, ext


def seguir(arq, proj, tarefa, profundidade=0):
    a = norm(arq)
    if profundidade > 12:
        return
    if not os.path.exists(a):
        nao_achados.add(a)
        return
    ja = a in vivos
    vivos.setdefault(a, set()).add(proj)
    if ja:
        if a.endswith(".py") and a in EXT_POR_ARQ:
            externos.setdefault(tarefa, set()).update(EXT_POR_ARQ[a])
        return
    txt = ler(a)
    if a.endswith(".py"):
        try:
            arv = ast.parse(txt)
        except SyntaxError:
            arv = ast.parse("")
        locais, ext = modulos_locais(a, arv, txt)
        EXT_POR_ARQ[a] = ext
        externos.setdefault(tarefa, set()).update(ext)
        for l in locais:
            seguir(l, proj, tarefa, profundidade + 1)
    for c in caminhos_no_texto(txt, Path(a).parent):
        if c.lower().endswith((".py", ".bat", ".ps1", ".vbs")) and "rodar_oculto" not in c.lower():
            seguir(c, proj, tarefa, profundidade + 1)


EXT_POR_ARQ = {}
for pid, p in cat["projetos"].items():
    for nome, det in p.get("tarefas_detalhe", {}).items():
        if not det.get("ligada") or p.get("estado") == "parado":
            continue
        cmd = det["cmd"]
        pys = [x for x in RE_PYEXE.findall(cmd)]
        interp[nome] = pys[-1].lower() if pys else ""
        for c in caminhos_no_texto(cmd, "D:\\"):
            if "rodar_oculto" in c.lower() or re.search(r"python[w]?\.exe", c, re.I):
                continue
            seguir(c, pid, nome)
        # tarefa sem caminho absoluto (ex.: "pythonw.exe capas_rodizio.py" com pasta de trabalho)
        if not caminhos_no_texto(cmd, "D:\\"):
            for m in re.findall(r"([\w\-]+\.py)", cmd):
                for pasta in p.get("pastas", []):
                    cand = Path(pasta) / m
                    if cand.exists():
                        seguir(str(cand), pid, nome)

# ---- candidatos a morto: .py nas pastas dos projetos, fora do vivo, sem mexer ha 14 dias ----
agora = time.time()
pastas = sorted({norm(x) for p in cat["projetos"].values() for x in p.get("pastas", []) if re.match(r"^[a-z]:\\", x, re.I)})
mortos, recentes = [], []
for raiz in pastas:
    for dp, dn, fn in os.walk(raiz):
        if IGNORA_DIR.search(dp + "\\"):
            dn[:] = []
            continue
        dn[:] = [d for d in dn if not IGNORA_DIR.search(f"\\{d}\\")]
        for f in fn:
            if not f.lower().endswith(".py"):
                continue
            a = norm(os.path.join(dp, f))
            if a in vivos:
                continue
            try:
                st = os.stat(a)
            except OSError:
                continue
            idade = (agora - st.st_mtime) / 86400
            (mortos if idade > 14 else recentes).append((a, round(idade), st.st_size))

# ---- Python principal tem os pacotes de cada tarefa? ----
todos_ext = sorted({e for s in externos.values() for e in s})
tem = {}
if todos_ext:
    prog = ("import importlib.util,json,sys\n"
            "print(json.dumps({m: importlib.util.find_spec(m) is not None for m in json.loads(sys.argv[1])}))")
    try:
        r = subprocess.run([PY_PRINCIPAL, "-c", prog, json.dumps(todos_ext)], capture_output=True, text=True, timeout=300,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        tem = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:  # noqa: BLE001
        print("aviso: nao consegui testar o python principal:", e)
compat = {}
for t, ext in externos.items():
    faltam = sorted(e for e in ext if not tem.get(e, False))
    compat[t] = {"interp": interp.get(t, ""), "externos": sorted(ext), "faltam_no_principal": faltam,
                 "ja_no_principal": interp.get(t, "").startswith(r"d:\veo\venv"),
                 "pode_trocar": (not faltam) and not interp.get(t, "").startswith(r"d:\veo\venv")}

SAIDA.mkdir(parents=True, exist_ok=True)
res = {"gerado": time.strftime("%Y-%m-%d %H:%M"), "vivos": {k: sorted(v) for k, v in sorted(vivos.items())},
       "mortos": mortos, "recentes_fora_do_mapa": recentes, "nao_achados": sorted(nao_achados), "python": compat}
(SAIDA / "mapa_vivo.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

tam = lambda l: sum(x[2] for x in l) / 1e6
interps = {}
for t, c in compat.items():
    interps.setdefault(c["interp"] or "(sem python / bat)", []).append(t)
md = [f"# MAPA DO QUE ESTÁ VIVO — {res['gerado']}", "",
      f"- **Código vivo** (alcançado a partir das tarefas ligadas): **{len(vivos)} arquivos**",
      f"- **Candidatos a morto** (.py nas pastas dos projetos, ninguém chama, sem mexer há 14+ dias): **{len(mortos)} arquivos, {tam(mortos):.1f} MB**",
      f"- Fora do mapa mas mexidos nos últimos 14 dias (NÃO mexer — podem ser chamados por chat/manual): {len(recentes)}",
      f"- Caminhos citados que não existem mais: {len(nao_achados)}", "",
      "## Python por tarefa", "| Interpretador | Tarefas | Podem ir pro principal já | Faltam pacotes |", "|---|---:|---:|---|"]
for i, ts in sorted(interps.items(), key=lambda x: -len(x[1])):
    pode = [t for t in ts if compat[t]["pode_trocar"]]
    falta = sorted({f for t in ts for f in compat[t]["faltam_no_principal"]})
    md.append(f"| `{i}` | {len(ts)} | {len(pode)} | {', '.join(falta[:12])} |")
md += ["", "## Candidatos a morto por pasta (top 25)", "| Pasta | Arquivos | MB |", "|---|---:|---:|"]
porpasta = {}
for a, idade, s in mortos:
    k = "\\".join(a.split("\\")[:3])
    porpasta.setdefault(k, [0, 0])
    porpasta[k][0] += 1
    porpasta[k][1] += s
for k, (n, s) in sorted(porpasta.items(), key=lambda x: -x[1][0])[:25]:
    md.append(f"| {k} | {n} | {s / 1e6:.1f} |")
(SAIDA / "MAPA_VIVO.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md))
