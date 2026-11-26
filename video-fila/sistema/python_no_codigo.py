# D:\sistema\catalogo\python_no_codigo.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/python_no_codigo.py)
# OBRA sistema unico - troca o caminho de Python ANTIGO escrito DENTRO dos programas vivos pelo Python principal
# (D:\veo\venv\Scripts\python[w].exe), com as mesmas garantias do trocar_python.py:
#   - so em arquivo VIVO (uso real ou tarefa ligada) e que ainda nao foi trocado;
#   - so se TODOS os pacotes que esse programa usou de verdade existem no principal (uso real);
#   - nunca em programa que usa navegador (playwright/selenium/uiautomator2...) - ficam no Python deles;
#   - copia <arquivo>.bak_obra_pycodigo antes; py_compile depois (se quebrar, volta na hora);
#   - registro em D:\sistema\mapa\python_codigo.json (arquivo, linhas trocadas); --voltar-todas desfaz.
#   python python_no_codigo.py            simula      --aplicar      --voltar-todas
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REG = Path(r"D:\sistema\mapa\python_codigo.json")
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
NOVO = {"python.exe": r"D:\veo\venv\Scripts\python.exe", "pythonw.exe": r"D:\veo\venv\Scripts\pythonw.exe"}
VELHOS = re.compile(r"(C:\\+Users\\+Haylla\\+AppData\\+Local\\+Programs\\+Python\\+Python313|"
                    r"D:\\+hipercool-videos\\+venv\\+Scripts|D:\\+hipercool-materiais\\+python\\+venv\\+Scripts|"
                    r"D:\\+recapd-ambientes\\+producao\\+venv\\+Scripts|D:\\+manhwa-react\\+\.venv\\+Scripts)"
                    r"(\\+)(python[w]?\.exe)", re.I)
MANUAL = {"playwright", "selenium", "undetected_chromedriver", "uiautomator2", "patchright", "nodriver", "pyautogui"}
PASTAS = [r"D:\video-fila", r"D:\postador-de-videos\bin", r"D:\projeto celular sub controle",
          r"D:\projeto celular sub controle\canal_pronto", r"D:\recapd-ambientes\producao\bin",
          r"D:\recapd-ambientes\producao\colab", r"D:\hipercool-materiais\comum", r"D:\ms-energy\bin", r"D:\gemini-argo",
          r"D:\opus-gratis-v2-desktop", r"D:\limpeza_c", r"D:\manhwa-react\scripts", r"D:\sonnet web"]


def uso():
    vivos, pac = set(), {}
    for f in sorted(Path(r"D:\sistema\mapa\uso").glob("uso_*.jsonl"))[-7:]:
        for l in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                j = json.loads(l)
            except ValueError:
                continue
            ext = {e for e in j.get("externos", []) if not e.endswith("__mypyc") and not e.startswith("_")}
            for a in j.get("locais", []) + [j.get("main", "")]:
                a = a.lower()
                if a.endswith(".py"):
                    vivos.add(a)
                    pac.setdefault(a, set()).update(ext)
    return vivos, pac


def principal_tem(pacotes):
    if not pacotes:
        return {}
    prog = ("import importlib.util,json,sys\n"
            "def ok(m):\n    try:\n        return importlib.util.find_spec(m) is not None\n    except Exception:\n        return False\n"
            "print(json.dumps({m: ok(m) for m in json.loads(sys.argv[1])}))")
    r = subprocess.run([NOVO["python.exe"], "-c", prog, json.dumps(sorted(pacotes))], capture_output=True, text=True,
                       timeout=300, creationflags=SEM_JANELA, env={**os.environ, "SISTEMA_USO": "0"})
    return json.loads(r.stdout.strip().splitlines()[-1])


def candidatos():
    vivos, pac = uso()
    cat = json.loads(Path(r"D:\sistema\catalogo\sistema.json").read_text(encoding="utf-8-sig"))
    cmds = " ".join(d["cmd"].lower() for p in cat["projetos"].values() for d in p.get("tarefas_detalhe", {}).values() if d.get("ligada"))
    out = []
    for pasta in PASTAS:
        try:
            nomes = os.listdir(pasta)
        except OSError:
            continue
        for n in nomes:
            f = os.path.join(pasta, n)
            if not n.lower().endswith((".py", ".bat")) or not os.path.isfile(f):
                continue
            fl = f.lower()
            vivo = fl in vivos or os.path.realpath(f).lower() in vivos or fl in cmds
            if not vivo:
                continue
            try:
                txt = open(f, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if not VELHOS.search(txt):
                continue
            # pacotes: o do proprio arquivo e os dos .py que ele chama (para .bat)
            chamados = {fl} | {x.lower() for x in re.findall(r"[A-Za-z]:\\[^\"'\r\n]+?\.py", txt)}
            p = set().union(*(pac.get(c, set()) for c in chamados))
            out.append((f, txt, p, chamados))
    return out


def ler():
    return json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}


def salvar(d):
    REG.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def aplicar(fazer):
    d = ler()
    cands = candidatos()
    tem = principal_tem(set().union(*(c[2] for c in cands)) if cands else set())
    feitos = 0
    so = [x.lower() for x in sys.argv[sys.argv.index("--so") + 1].split(",")] if "--so" in sys.argv else None
    for f, txt, pac, chamados in cands:
        if f in d and d[f].get("estado") == "trocado":
            continue
        if so and not any(x in f.lower() for x in so):
            continue
        if pac & MANUAL:
            print(f"NAVEGADOR (fica)     {f}  [{', '.join(sorted(pac & MANUAL))}]")
            continue
        sem_uso = [c for c in chamados if c.endswith(".py") and c not in {k for k in chamados if pac}]
        faltam = sorted(k for k in pac if not tem.get(k))
        if faltam:
            print(f"FALTA NO PRINCIPAL   {f}  {faltam[:5]}")
            continue
        n = len(VELHOS.findall(txt))
        if not fazer:
            print(f"PRONTO ({n} linha(s))  {f}")
            continue
        bak = f + ".bak_obra_pycodigo"
        if not os.path.exists(bak):
            shutil.copy2(f, bak)
        novo = VELHOS.sub(lambda m: NOVO[m.group(3).lower()].replace("\\", m.group(2)), txt)
        Path(f).write_text(novo, encoding="utf-8", errors="replace")
        if f.lower().endswith(".py"):
            try:
                py_compile.compile(f, doraise=True)
            except py_compile.PyCompileError as e:
                shutil.copy2(bak, f)
                print(f"QUEBROU, voltei      {f}: {str(e)[:120]}")
                continue
        d[f] = {"estado": "trocado", "linhas": n, "em": time.strftime("%Y-%m-%dT%H:%M:%S"), "bak": bak}
        salvar(d)
        feitos += 1
        print(f"TROCADO ({n})         {f}")
    print(f"trocados agora: {feitos}")


def voltar_todas():
    d = ler()
    for f, r in d.items():
        if r.get("estado") == "trocado" and os.path.exists(r["bak"]):
            shutil.copy2(r["bak"], f)
            r["estado"] = "voltou"
            print("voltou", f)
    salvar(d)


a = sys.argv[1:]
if "--voltar-todas" in a:
    voltar_todas()
else:
    aplicar("--aplicar" in a)
