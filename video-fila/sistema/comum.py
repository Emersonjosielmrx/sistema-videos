# D:\sistema\catalogo\comum.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/comum.py)
# OBRA sistema unico - CODIGO COMUM. Arquivos .py IDENTICOS (mesmo nome e mesmo conteudo) espalhados pelas pastas dos
# projetos ativos viram UM arquivo so: D:\sistema\comum\<nome> e cada copia vira HARDLINK dele (mesmo arquivo no disco,
# varios caminhos). Nenhum import muda; consertou num lugar = consertou em todos.
# Cuidado conhecido: editor que salva "trocando o arquivo" quebra o vinculo daquela copia -> --conferir acusa
# (vira copia solta de novo) e --aplicar religa se o conteudo voltou a ser igual.
#   python comum.py               simula      python comum.py --aplicar      python comum.py --conferir
# Indice: D:\sistema\comum\INDICE.json (nome -> md5, copias). Volta: as copias continuam la (so o vinculo some ao editar).
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
COMUM = Path(r"D:\sistema\comum")
IND = COMUM / "INDICE.json"
CAT = json.loads(Path(r"D:\sistema\catalogo\sistema.json").read_text(encoding="utf-8-sig"))
FORA = re.compile(r"\\(venv[^\\]*|\.venv|site-packages|__pycache__|node_modules|\.git|quarentena|painel_ia|"
                  r"_?bak[^\\]*|_?backup[^\\]*|perfis|cofre|remotion|"
                  # COPIAS CONGELADAS DE PROPOSITO (versoes, fotos, pedidos com data, benchmarks): nunca vincular
                  r"_?snapshots?[^\\]*|_?estavel[^\\]*|versoes?[^\\]*|_versao[^\\]*|caixa|captura|hibridos[^\\]*|"
                  r"[^\\]*bench[^\\]*|\d{8}_\d{4,6}[^\\]*|trabalhos|referencias|testes?|_testes)(\\|$)", re.I)


def e_juncao(p):
    try:
        return bool(os.stat(p, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError:
        return False


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def varrer():
    raizes = sorted({x.rstrip("\\") for p in CAT["projetos"].values() if p.get("estado") != "parado"
                     for x in p.get("pastas", []) if re.match(r"^[Dd]:\\", x) and os.path.isdir(x)})
    # 26/11: pastas de projeto PARADO (e o que estiver dentro delas) ficam fora, mesmo dentro de outra raiz
    parados = [os.path.normcase(os.path.realpath(x)) for p in CAT["projetos"].values() if p.get("estado") == "parado"
               for x in p.get("pastas", []) if re.match(r"^[Dd]:\\", x) and os.path.exists(x)]
    grupos, vistos, vistos_ino = {}, set(), set()
    for raiz in raizes:
        for dp, dn, fn in os.walk(raiz):
            rdp = os.path.normcase(os.path.realpath(dp))
            if rdp.startswith(os.path.normcase(r"d:\sistema\comum")):
                dn[:] = []
                continue
            if any(rdp == x or rdp.startswith(x + "\\") for x in parados) or "__parado" in rdp:
                dn[:] = []
                continue
            if FORA.search(dp + "\\") or e_juncao(dp):
                dn[:] = []
                continue
            dn[:] = [d for d in dn if not e_juncao(os.path.join(dp, d)) and not FORA.search("\\" + d + "\\")]
            for f in fn:
                if not f.endswith(".py") or f in ("__init__.py", "sitecustomize.py"):
                    continue
                a = os.path.join(dp, f)
                k = os.path.normcase(os.path.realpath(a))  # 26/11: depois da mudanca a mesma pasta tem 2 nomes
                if k in vistos:
                    continue
                vistos.add(k)
                try:
                    st = os.stat(a)
                    ident = (st.st_dev, st.st_ino)  # 26/11: hardlink = MESMO arquivo -> conta 1 vez
                    if ident in vistos_ino:
                        continue
                    vistos_ino.add(ident)
                    grupos.setdefault((f, md5(a)), []).append(a)
                except OSError:
                    pass
    # so compartilha o que esta em 2+ PROJETOS diferentes (1o nivel do disco): codigo comum de verdade
    def topo(x):  # projeto de verdade = 1o nivel do caminho ORIGINAL (D:\\<projeto>), nao o nome dentro de D:\\sistema
        r = os.path.realpath(x).lower()
        partes = r.split("\\")
        if len(partes) > 4 and partes[1] == "sistema":
            return partes[4] if partes[2].startswith("1-") else partes[3]
        return partes[1]
    return {k: v for k, v in grupos.items() if len(v) > 1 and len({topo(x) for x in v}) > 1}


def mesmo_arquivo(a, b):
    try:
        sa, sb = os.stat(a), os.stat(b)
        return (sa.st_ino, sa.st_dev) == (sb.st_ino, sb.st_dev)
    except OSError:
        return False


def aplicar(grupos):
    COMUM.mkdir(parents=True, exist_ok=True)
    ind = json.loads(IND.read_text(encoding="utf-8")) if IND.exists() else {}
    nomes_usados = {}
    ligados = 0
    for (nome, h), copias in sorted(grupos.items()):
        # mesmo nome com conteudos diferentes em grupos distintos -> sufixo com o hash
        alvo = COMUM / nome
        if alvo.exists() and md5(alvo) != h:
            alvo = COMUM / f"{nome[:-3]}__{h[:6]}.py"
        if not alvo.exists():
            os.link(copias[0], alvo)
        for c in copias:
            if mesmo_arquivo(c, alvo):
                continue
            tmp = c + ".tmp_vinculo"
            if os.path.exists(tmp):
                os.remove(tmp)
            os.link(alvo, tmp)
            os.replace(tmp, c)  # troca atomica: o caminho antigo agora e o MESMO arquivo do comum
            ligados += 1
        ind[alvo.name] = {"md5": h, "copias": copias, "em": time.strftime("%Y-%m-%dT%H:%M:%S")}
    IND.write_text(json.dumps(ind, ensure_ascii=False, indent=1), encoding="utf-8")
    return ligados


def conferir():
    if not IND.exists():
        print("[COMUM] ainda sem indice")
        return
    ind = json.loads(IND.read_text(encoding="utf-8"))
    soltas = []
    for nome, e in ind.items():
        for c in e["copias"]:
            if os.path.exists(c) and not mesmo_arquivo(c, COMUM / nome):
                soltas.append(c)
    print(f"[COMUM] {len(ind)} arquivos compartilhados, {sum(len(e['copias']) for e in ind.values())} caminhos ligados"
          f" | vinculos quebrados: {len(soltas)}")
    for s in soltas[:15]:
        print(f"  !! copia virou arquivo solto (alguem editou so ela): {s}")


a = sys.argv[1:]
if "--conferir" in a:
    conferir()
else:
    g = varrer()
    n = sum(len(v) for v in g.values())
    print(f"grupos de copias identicas: {len(g)} ({n} arquivos; {n - len(g)} copias a mais)")
    for (nome, h), v in sorted(g.items(), key=lambda x: -len(x[1]))[:40]:
        print(f"  {len(v)}x {nome}: " + " | ".join(x[3:60] for x in v[:4]))
    if "--aplicar" in a:
        print(f"vinculados agora: {aplicar(g)}")
        conferir()
