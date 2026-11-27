# D:\sistema\catalogo\juncoes.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/juncoes.py)
# OBRA sistema unico - CONSERTA JUNCOES QUEBRADAS (27/11/2026).
# Causa do achado: quarentena.py troca pasta morta por JUNCAO -> D:\sistema\quarentena\...; depois o arquivar_drive levou
# a propria D:\sistema\quarentena para o Drive e removeu do PC1 -> as juncoes ficaram apontando para o nada. Programa que
# faz mkdir(exist_ok=True) nessa pasta quebra (FileExistsError, WinError 183): HipercoolPostagem parou assim.
# Conserto: juncao quebrada que aponta para dentro de D:\sistema\quarentena ou D:\sistema2 vira PASTA VAZIA de verdade
# (o conteudo antigo esta no Drive: conta32:arquivo-pc1/obra-26nov/sistema/quarentena/...). Juncao que aponta para outro
# lugar so e listada (nao mexe). Registro: D:\sistema\mapa\juncoes_consertadas.json
#   python juncoes.py            lista as quebradas (nao mexe)
#   python juncoes.py --aplicar  conserta
import json
import os
import re
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REG = Path(r"D:\sistema\mapa\juncoes_consertadas.json")
CONSERTAVEL = re.compile(r"^(\\\\\?\\)?D:\\sistema\\(quarentena|sistema2)\\|^(\\\\\?\\)?D:\\sistema2\\", re.I)
PULA = re.compile(r"^(venv[^\\]*|\.venv|node_modules|site-packages|__pycache__|\.git)$", re.I)


def e_juncao(p):
    try:
        return bool(os.stat(p, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError:
        return False


def alvo(p):
    try:
        return os.readlink(p)
    except OSError:
        return "?"


def quebradas():
    raizes = [r"D:\sistema"] + [os.path.join("D:\\", d) for d in os.listdir("D:\\")
                                if os.path.isdir(os.path.join("D:\\", d)) and not e_juncao(os.path.join("D:\\", d))
                                and d.lower() not in ("sistema", "sistema2", "$recycle.bin", "system volume information")]
    out, vistos = [], set()
    for raiz in raizes:
        for dp, dn, fn in os.walk(raiz):
            fica = []
            for d in dn:
                p = os.path.join(dp, d)
                if e_juncao(p):
                    if not os.path.exists(p):
                        k = os.path.normcase(os.path.join(os.path.realpath(dp), d))
                        if k not in vistos:
                            vistos.add(k)
                            out.append((p, alvo(p)))
                elif not PULA.match(d):
                    fica.append(d)
            dn[:] = fica
    return out


def main(fazer):
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else []
    q = quebradas()
    feitas = 0
    for p, a in q:
        ok = bool(CONSERTAVEL.search(a))
        print(f"{'CONSERTA' if ok else 'so lista'}  {p}  ->  {a}")
        if not (fazer and ok):
            continue
        if os.path.exists(p):  # outro caminho da mesma pasta ja consertou
            continue
        os.rmdir(p)      # tira so o PONTEIRO quebrado (o alvo nao existe mais; nada de dado e apagado)
        os.makedirs(p)   # pasta vazia de verdade no lugar
        reg.append({"pasta": p, "apontava": a, "em": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "conteudo_antigo": "Drive conta32:arquivo-pc1/obra-26nov/sistema/quarentena (ver mapa\\arquivados.json)"})
        feitas += 1
    if fazer:
        REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"quebradas: {len(q)} | consertadas agora: {feitas}")


main("--aplicar" in sys.argv)
