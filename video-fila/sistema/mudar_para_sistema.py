# D:\sistema\catalogo\mudar_para_sistema.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/mudar_para_sistema.py)
# OBRA sistema unico - MUDANCA FISICA das pastas vivas para dentro de D:\sistema (pedido da dona 26/11: "pastas limpas").
# Cada pasta-raiz de projeto ativo (D:\<nome>) e MOVIDA (mesmo disco = renomear, instantaneo) para
# D:\sistema\<grupo>\<projeto>\<nome> e no caminho antigo fica uma JUNCAO -> todos os scripts, tarefas e caminhos
# escritos no codigo continuam funcionando. A juncao de "visao" que existia ali vira a pasta real.
# Pasta com arquivo aberto (programa rodando dentro) NAO move (o Windows recusa) -> fica para a proxima rodada.
#   python mudar_para_sistema.py --plano          lista o que move, tamanho, venv dentro, quem usa (nao mexe)
#   python mudar_para_sistema.py --aplicar        move o que estiver livre agora (registro em mapa\mudanca.json)
#   python mudar_para_sistema.py --voltar-todas   desfaz (tira a juncao e volta a pasta)
# A janela completa (pausar postagem/laços, mover, religar) e feita pelo chat com o plano abaixo; este script so move.
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"D:\sistema")
REG = RAIZ / "mapa" / "mudanca.json"
CAT = json.loads((RAIZ / "catalogo" / "sistema.json").read_text(encoding="utf-8-sig"))
GRUPO = {"A-video": "1-VIDEO", "B-postagem": "1-VIDEO", "C-infra": "2-CONTAS-E-IAS",
         "D-central": "3-CENTRAL-E-MAQUINAS", "E-outros": "4-OUTROS-NEGOCIOS"}
SUB = {"A-video": "1-producao", "B-postagem": "2-postagem"}
# nunca mover: raiz do sistema, ferramentas compartilhadas por TODOS, e o que o Windows/outros apontam fixo
NUNCA = {r"d:\sistema", r"d:\tools", r"d:\tmp", r"d:\rodar_oculto.vbs"}
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def e_juncao(p):
    try:
        return bool(os.stat(p, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError:
        return False


def destino(pid, p, pasta):
    if p["categoria"] == "0-base":
        return RAIZ / "0-BASE-COMPARTILHADA" / Path(pasta).name
    base = RAIZ / GRUPO[p["categoria"]]
    if p["categoria"] in SUB:
        base = base / SUB[p["categoria"]]
    nome = pid + ("__PARADO" if p.get("estado") == "parado" else "")
    return base / nome / Path(pasta).name


# 26/11: pastas-BASE usadas por varios projetos (Python principal, material comum, ambiente do recap) -> 0-BASE
BASE_COMP = {r"D:\veo": "veo", r"D:\hipercool-materiais": "hipercool-materiais", r"D:\recapd-ambientes": "recapd-ambientes"}


def candidatos():
    vistos, out = set(), []
    for pasta, nome in BASE_COMP.items():
        if os.path.isdir(pasta) and not e_juncao(pasta):
            out.append(("0-base", {"categoria": "0-base", "estado": "ativo"}, pasta))
            vistos.add(pasta.lower())
    for pid, p in CAT["projetos"].items():
        for pasta in p.get("pastas", []):
            pl = pasta.lower().rstrip("\\")
            if not re.match(r"^[a-z]:\\[^\\]+$", pl) or pl in NUNCA or pl in vistos:
                continue  # so pasta de 1o nivel do D:; aninhadas vao junto com a mae
            vistos.add(pl)
            if not os.path.isdir(pasta) or e_juncao(pasta):
                continue  # ja e juncao (ja movida ou quarentena)
            out.append((pid, p, pasta))
    return out


def plano():
    tot = 0
    print(f"{'pasta':38} {'projeto':16} {'venv dentro':12} destino")
    for pid, p, pasta in candidatos():
        venvs = [d for d in os.listdir(pasta) if re.match(r"^\.?venv", d, re.I)] + \
                [f"{d}\\venv" for d in os.listdir(pasta) if os.path.isdir(os.path.join(pasta, d, "venv"))]
        print(f"{pasta:38} {pid:16} {','.join(venvs)[:12]:12} {destino(pid, p, pasta)}")
        tot += 1
    print(f"{tot} pastas para mover")


def ler():
    return json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else []


def salvar(r):
    REG.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")


def aplicar():
    reg = ler()
    feitas, presas = 0, []
    for pid, p, pasta in candidatos():
        dest = destino(pid, p, pasta)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if e_juncao(dest):
            os.rmdir(dest)  # a juncao de "visao" sai; a pasta real entra no lugar
        try:
            os.rename(pasta, dest)
        except OSError as e:
            presas.append(f"{pasta}: {e.strerror}")
            # repoe a juncao de visao
            subprocess.run(["cmd", "/c", "mklink", "/J", str(dest), pasta], capture_output=True, creationflags=SEM_JANELA)
            continue
        r = subprocess.run(["cmd", "/c", "mklink", "/J", pasta, str(dest)], capture_output=True, text=True,
                           encoding="cp850", errors="replace", creationflags=SEM_JANELA)
        if r.returncode != 0:
            os.rename(dest, pasta)
            presas.append(f"{pasta}: juncao falhou, desfeito")
            continue
        for item in dest.parent.iterdir():  # juncao de visao antiga (nome com _ ) apontando p/ o caminho original
            try:
                if item != dest and e_juncao(item) and os.path.normcase(os.readlink(item)).rstrip("\\").replace("\\\\?\\", "") == os.path.normcase(pasta).rstrip("\\"):
                    os.rmdir(item)
            except OSError:
                pass
        reg.append({"original": pasta, "destino": str(dest), "em": time.strftime("%Y-%m-%dT%H:%M:%S"), "projeto": pid})
        salvar(reg)
        feitas += 1
        print(f"MOVIDA {pasta} -> {dest}")
    print(f"movidas: {feitas} | presas (programa rodando dentro): {len(presas)}")
    for x in presas:
        print("  presa:", x)


def voltar_todas():
    reg = ler()
    for e in reversed(reg):
        if e.get("voltou"):
            continue
        if e_juncao(e["original"]):
            os.rmdir(e["original"])
        os.rename(e["destino"], e["original"])
        e["voltou"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        print("voltou", e["original"])
    salvar(reg)


a = sys.argv[1:]
if "--aplicar" in a:
    aplicar()
elif "--voltar-todas" in a:
    voltar_todas()
else:
    plano()
