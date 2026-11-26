# D:\sistema\catalogo\quarentena.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/quarentena.py)
# OBRA sistema unico - QUARENTENA do que esta morto, SEM QUEBRAR NADA:
#   a pasta e MOVIDA (mesmo disco = so renomeia, instantaneo) para D:\sistema\quarentena\<caminho original> e no lugar
#   antigo fica uma JUNCAO apontando para la. Fica separada do que vive, mas quem ainda usar continua achando.
#   O registrador de uso (sistema_uso) mostra se algo carregar arquivo de dentro dela -> analisar_uso acusa.
# O que entra:
#   A) pastas-raiz de projetos 'parado' no catalogo que NENHUM arquivo vivo (mapa estatico + uso real) e nenhuma
#      tarefa ligada usa;
#   B) subpastas dentro dos projetos ativos em que TODOS os arquivos estao parados ha 14+ dias, nenhum e vivo, e tem
#      cara de sobra (nome com bak/backup/old/antigo/legado/teste/diag/dev/_tmp, ou so .py mortos).
# Nunca: pasta-raiz de projeto ativo, venv de projeto ativo, pasta com log/estado mexido em 14 dias, juncao, D:\sistema.
#   python quarentena.py                 simula (lista)
#   python quarentena.py --aplicar       move + juncao, grava D:\sistema\quarentena\INDICE.json
#   python quarentena.py --voltar CAMINHO_ORIGINAL | --voltar-todas
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
Q = Path(r"D:\sistema\quarentena")
IND = Q / "INDICE.json"
MAPA = Path(r"D:\sistema\mapa")
CAT = json.loads(Path(r"D:\sistema\catalogo\sistema.json").read_text(encoding="utf-8-sig"))
DIAS = 14
SOBRA = re.compile(r"(^|[_\-. ])(bak|backup|backups|old|legado|teste|testes|test|diag|dev|tmp|temp|"
                   r"copia|scratch|lixo|arquivado|deprecated)([_\-. 0-9]|$)", re.I)
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def e_juncao(p):
    try:
        return bool(os.stat(p, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError:
        return False


def vivos():
    v = set()
    try:
        v |= set(json.loads((MAPA / "mapa_vivo.json").read_text(encoding="utf-8"))["vivos"])
    except (OSError, ValueError, KeyError):
        pass
    for f in MAPA.glob("uso/uso_*.jsonl"):
        for l in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                j = json.loads(l)
            except ValueError:
                continue
            v |= {x.lower() for x in j.get("locais", [])}
            if j.get("main", "").lower().endswith(".py"):
                v.add(j["main"].lower())
            if j.get("cwd"):
                v.add(j["cwd"].lower().rstrip("\\") + "\\")
    return v


def cmds_ligados():
    out = []
    for p in CAT["projetos"].values():
        for d in p.get("tarefas_detalhe", {}).values():
            if d.get("ligada"):
                out.append(d["cmd"].lower())
    return " ".join(out)


def tem_vivo(pasta, V):
    pl = pasta.lower().rstrip("\\") + "\\"
    return any(x.startswith(pl) for x in V)


def mais_novo(pasta, limite):
    """True se tem arquivo mexido depois de 'limite' (para cedo)."""
    for dp, dn, fn in os.walk(pasta):
        dn[:] = [d for d in dn if not e_juncao(os.path.join(dp, d))]
        for f in fn:
            try:
                if os.path.getmtime(os.path.join(dp, f)) > limite:
                    return True
            except OSError:
                pass
    return False


def tamanho(pasta):
    t = 0
    for dp, dn, fn in os.walk(pasta):
        dn[:] = [d for d in dn if not e_juncao(os.path.join(dp, d))]
        for f in fn:
            try:
                t += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return t


def candidatos():
    V, C = vivos(), cmds_ligados()
    limite = time.time() - DIAS * 86400
    raizes_ativas = {x.lower().rstrip("\\") for p in CAT["projetos"].values() if p.get("estado") != "parado"
                     for x in p.get("pastas", []) if re.match(r"^[A-Za-z]:\\", x)}
    out = []
    # A) raiz de projeto parado
    for pid, p in CAT["projetos"].items():
        if p.get("estado") != "parado":
            continue
        for pasta in p.get("pastas", []):
            pl = pasta.lower().rstrip("\\")
            if not re.match(r"^[a-z]:\\[^\\]+$", pl) or not os.path.isdir(pasta) or e_juncao(pasta):
                continue  # so pasta de 1o nivel do disco (as aninhadas podem ser de outro projeto)
            if any(r == pl or r.startswith(pl + "\\") for r in raizes_ativas):
                continue
            if tem_vivo(pasta, V) or pl in C:
                out.append(("PULA", pasta, f"projeto parado {pid}, mas tem uso vivo")); continue
            out.append(("A", pasta, f"projeto parado: {pid}"))
    # B) subpastas de sobra dentro de projetos ativos
    vistos = set()
    for raiz in sorted(raizes_ativas):
        if not os.path.isdir(raiz):
            continue
        for dp, dn, fn in os.walk(raiz):
            if e_juncao(dp):
                dn[:] = []
                continue
            dn[:] = [d for d in dn if not e_juncao(os.path.join(dp, d))
                     and not re.match(r"^(venv.*|\.venv|\.git|__pycache__|node_modules|site-packages)$", d, re.I)]
            for d in list(dn):
                sub = os.path.join(dp, d)
                # NUNCA: perfis de navegador/contas (deslogaria contas), cofre, Remotion/node, git
                if re.search(r"\\(perfis|perfil|profiles?|user data|default|cofre|chrome[^\\]*|remotion|node_modules|\.git|logins?[^\\]*)\\",
                             sub.lower() + "\\"):
                    continue
                if not SOBRA.search(d) or re.search(r"\\(juri|shorts|animes recap|saida|videos?)\\", sub.lower() + "\\"):
                    continue
                dn.remove(d)  # decide aqui; nao desce
                if sub.lower() in vistos:
                    continue
                vistos.add(sub.lower())
                if sub.lower() in raizes_ativas or tem_vivo(sub, V) or sub.lower() in C:
                    continue
                if mais_novo(sub, limite):
                    continue
                out.append(("B", sub, "sobra (nome) + nada vivo + parada há 14+ dias"))
    return out


def ler():
    return json.loads(IND.read_text(encoding="utf-8")) if IND.exists() else []


def salvar(d):
    Q.mkdir(parents=True, exist_ok=True)
    IND.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def mover(orig, motivo, ind):
    dest = Q / orig[3:]
    dest.parent.mkdir(parents=True, exist_ok=True)
    tam = tamanho(orig)
    os.rename(orig, dest)  # mesmo disco: renomeia
    r = subprocess.run(["cmd", "/c", "mklink", "/J", orig, str(dest)], capture_output=True, text=True, encoding="cp850",
                       errors="replace", creationflags=SEM_JANELA)
    if r.returncode != 0:
        os.rename(dest, orig)  # desfaz
        raise RuntimeError("juncao falhou: " + (r.stdout + r.stderr).strip()[:200])
    ind.append({"original": orig, "destino": str(dest), "em": time.strftime("%Y-%m-%dT%H:%M:%S"), "motivo": motivo,
                "mb": round(tam / 1e6, 1)})


def voltar(orig, ind):
    for e in ind:
        if e["original"].lower() == orig.lower() and not e.get("voltou"):
            if e_juncao(orig):
                os.rmdir(orig)
            os.rename(e["destino"], orig)
            e["voltou"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            return True
    return False


a = sys.argv[1:]
if "--voltar-todas" in a:
    ind = ler()
    for e in [e for e in ind if not e.get("voltou")]:
        voltar(e["original"], ind)
    salvar(ind)
elif "--voltar" in a:
    ind = ler()
    print("ok" if voltar(a[a.index("--voltar") + 1], ind) else "nao achei")
    salvar(ind)
else:
    cands = candidatos()
    aplicar = "--aplicar" in a
    ind = ler()
    total = 0
    for tipo, pasta, motivo in cands:
        if tipo == "PULA":
            print(f"PULA  {pasta}  ({motivo})")
            continue
        mb = tamanho(pasta) / 1e6
        total += mb
        if aplicar:
            try:
                mover(pasta, motivo, ind)
                salvar(ind)
                print(f"MOVIDA {tipo} {mb:8.1f} MB  {pasta}")
            except Exception as e:  # noqa: BLE001
                print(f"ERRO   {tipo} {pasta}: {e}")
        else:
            print(f"SIMULA {tipo} {mb:8.1f} MB  {pasta}  ({motivo})")
    print(f"{'movidas' if aplicar else 'candidatas'}: {sum(1 for c in cands if c[0] != 'PULA')} pastas, {total:.0f} MB")
