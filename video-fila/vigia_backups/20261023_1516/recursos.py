# -*- coding: utf-8 -*-
"""recursos.py — CÓDIGO COMUM dos projetos de vídeo: uma versão só de cada módulo que mais de um projeto usa.

Pedido do dono (18/10): "quando eu atualizar um, fique fácil atualizar os outros e vice-versa".
Fonte única: D:\\hipercool-materiais\\comum\\<módulo>.py, registrada em comum\\recursos.json. Cada projeto da lista
guarda uma CÓPIA IDÊNTICA no próprio bin/ — nenhum import muda, e o PC2 e o desktop (que recebem o bin/ por cópia:
hipercool bin/pc2.py, video-fila/pc2_recapd.py, postador bin/workers.py) continuam funcionando. A cópia começa com
uma linha "# COMUM" avisando quem abrir o arquivo.

    python recursos.py                                  painel: comuns, cópias mexidas, o que ainda está separado
    python recursos.py subir x.py --de hipercool         a versão do projeto vira a comum e vai pros outros
    python recursos.py subir x.py --de hipercool --testar   só confere, não grava nada

Antes de trocar a cópia de cada projeto que tem x.py: compila, confere se tudo o que o projeto usa do módulo existe
na versão nova e importa a versão nova no Python do próprio projeto. Falhou num projeto = ele fica com a dele (sai da
lista). Toda cópia substituída vai antes pra comum\\_antigos\\<projeto>\\.
Módulo SEPARADO (versões diferentes): as checagens pegam função faltando, não comportamento perdido. Junte primeiro o
melhor das versões numa cópia (ler as outras) e só então suba com --juntei; sem ele, nada que apague versão própria
de outro projeto é gravado.
"""
import argparse
import ast
import hashlib
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

COMUM = Path(r"D:\hipercool-materiais\comum")
REGISTRO = COMUM / "recursos.json"
ANTIGOS = COMUM / "_antigos"
# projeto: (pasta dos módulos, raiz do import, prefixo do import, python do projeto)
PROJETOS = {
    "hipercool": (r"D:\hipercool-videos\bin", r"D:\hipercool-videos\bin", "",
                  r"D:\hipercool-videos\venv\Scripts\python.exe"),
    "historias": (r"D:\historias-em-frames\bin", r"D:\historias-em-frames\bin", "",
                  r"D:\historias-em-frames\venv\Scripts\python.exe"),
    "manhwa-react": (r"D:\manhwa-react\mr", r"D:\manhwa-react", "mr.", r"D:\manhwa-react\.venv\Scripts\python.exe"),
    "recapd": (r"D:\recapd-ambientes\producao\bin", r"D:\recapd-ambientes\producao\bin", "",
               r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"),
    "postador": (r"D:\postador-de-videos\bin", r"D:\postador-de-videos\bin", "", sys.executable),
    "veo": (r"D:\veo\beta", r"D:\veo\beta", "", r"D:\veo\venv\Scripts\python.exe"),
}
NAO_COMUM = {"hp_common.py", "config.py"}  # configuração de cada projeto: mesmo nome, conteúdo próprio de propósito
PASTAS_FORA = {"venv", ".venv", "__pycache__", "node_modules", "work", "workspace", "assets", "logs", "videos",
               "output", "cache", ".git", "site-packages"}
MARCA = "# COMUM — fonte única:"
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _hash(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def _ler_registro():
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_registro(r):
    COMUM.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRO.with_suffix(".tmp")
    tmp.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(REGISTRO)


def _copia(projeto, nome):
    return Path(PROJETOS[projeto][0]) / nome


def _com_cabecalho(texto, nome):
    if MARCA in texto[:800]:
        return texto
    fim = "\r\n" if "\r\n" in texto else "\n"
    linhas = texto.splitlines(keepends=True)
    i = 0
    while i < min(2, len(linhas)) and (linhas[i].startswith("#!") or re.match(r"#.*coding[:=]", linhas[i])):
        i += 1
    cab = (f"{MARCA} D:\\hipercool-materiais\\comum\\{nome}. Mudou esta cópia? "
           f"python D:\\hipercool-materiais\\bin\\recursos.py subir {nome} --de <projeto>{fim}")
    return "".join(linhas[:i]) + cab + "".join(linhas[i:])


def _nomes_definidos(texto):
    """Nomes de nível de módulo (inclusive dentro de if/try do topo). None = não dá pra saber (import *, __getattr__)."""
    nomes = set()

    def varrer(corpo):
        for n in corpo:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nomes.add(n.name)
            elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for alvo in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                    nomes.update(x.id for x in ast.walk(alvo) if isinstance(x, ast.Name))
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    if a.name == "*":
                        raise LookupError
                    nomes.add(a.asname or a.name.split(".")[0])
            elif isinstance(n, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                for campo in ("body", "orelse", "finalbody"):
                    varrer(getattr(n, campo, []))
                for h in getattr(n, "handlers", []):
                    varrer(h.body)
    try:
        varrer(ast.parse(texto).body)
    except LookupError:
        return None
    return None if "__getattr__" in nomes else nomes


def _nomes_usados(projeto, nome):
    """O que o código do projeto usa do módulo: 'from x import a, b' e 'x.a'."""
    _pasta, raiz, prefixo, _py = PROJETOS[projeto]
    mod = nome[:-3]
    pad_from = re.compile(rf"^\s*from\s+(?:{re.escape(prefixo)}|\.)?{re.escape(mod)}\s+import\s+(\([^)]*\)|[^\n]+)",
                          re.M)
    pad_attr = re.compile(rf"(?<![\w.]){re.escape(mod)}\.([A-Za-z_]\w*)")
    usados = set()
    for dp, dn, fn in os.walk(raiz):
        dn[:] = [d for d in dn if d not in PASTAS_FORA and not d.startswith(("_", "venv"))]
        for f in fn:
            if not f.endswith(".py") or f == nome or f.startswith("_"):
                continue
            t = Path(dp, f).read_text(encoding="utf-8", errors="replace")
            if mod not in t:
                continue
            for m in pad_from.finditer(t):
                for parte in re.sub(r"#[^\n]*", "", m.group(1)).strip("()").replace("\n", ",").split(","):
                    n = parte.strip().split(" as ")[0].strip()
                    if n.isidentifier():
                        usados.add(n)
            usados.update(pad_attr.findall(t))
    return usados - {"py", "pyc"}  # "x.py" escrito em texto/log não é uso do módulo


def _importa(projeto, nome, arquivo):
    """Importa a versão nova (arquivo temporário) no Python do projeto, como se estivesse no lugar da cópia dele.
    Script com hífen (split-shorts.py) não é importado por ninguém, só executado: fica só a compilação."""
    if not nome[:-3].isidentifier():
        return None
    _pasta, raiz, prefixo, py = PROJETOS[projeto]
    py = py if Path(py).exists() else sys.executable
    nome_mod = prefixo + nome[:-3]
    codigo = (f"import sys, importlib.util; sys.path.insert(0, {raiz!r}); "
              + (f"import {prefixo[:-1]}; " if prefixo else "")
              + f"s = importlib.util.spec_from_file_location({nome_mod!r}, {str(arquivo)!r}); "
              "m = importlib.util.module_from_spec(s); sys.modules[s.name] = m; s.loader.exec_module(m)")
    try:
        r = subprocess.run([py, "-c", codigo], cwd=raiz, capture_output=True, timeout=180,
                           env={**os.environ, "PYTHONUTF8": "1"}, creationflags=_SEM_JANELA)
    except subprocess.TimeoutExpired:
        return "importar passou de 3 min"
    if r.returncode:
        linhas = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
        return "não importa: " + (linhas[-1][:200] if linhas else f"código {r.returncode}")
    return None


def subir(nome, de, testar=False, juntei=False):
    reg = _ler_registro()
    origem = _copia(de, nome)
    if not origem.exists():
        print(f"{de} não tem {origem}")
        return 1
    if nome in reg and (COMUM / nome).exists():
        h = _hash(COMUM / nome)
        outros = [p for p in reg[nome]["projetos"] if p != de and _copia(p, nome).exists()
                  and _hash(_copia(p, nome)) != h]
        if outros:
            print(f"{nome} também foi mudado em: {', '.join(outros)}. Junte as mudanças numa cópia só e suba essa "
                  "(senão a outra mudança se perde).")
            return 1
    texto = _com_cabecalho(origem.read_bytes().decode("utf-8"), nome)
    alvos = sorted({p for p in PROJETOS if _copia(p, nome).exists()} | set(reg.get(nome, {}).get("projetos", [])))

    tmpdir = Path(tempfile.mkdtemp(prefix="recursos_"))
    tmp = tmpdir / nome
    tmp.write_bytes(texto.encode("utf-8"))
    try:
        try:
            py_compile.compile(str(tmp), doraise=True)
        except py_compile.PyCompileError as e:
            print(f"a versão de {de} não compila: {e.msg[:300]}")
            return 1
        definidos = _nomes_definidos(texto)
        aceitos, recusados = [], {}
        for p in alvos:
            falta = sorted(_nomes_usados(p, nome) - definidos) if definidos is not None else []
            erro = ("usa o que a versão nova não tem: " + ", ".join(falta[:8])) if falta else _importa(p, nome, tmp)
            if erro:
                recusados[p] = erro
            else:
                aceitos.append(p)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"{nome} (versão de {de}):")
    for p in alvos:
        print(f"  {p:13s} " + ("ok" if p in aceitos else "FICA COM A DELE — " + recusados[p]))
    if de in recusados:
        print(f"nada gravado: a versão não funciona nem no próprio {de}")
        return 1
    # versão PRÓPRIA = cópia que não é a comum atual; trocar sem juntar perde o que ela tinha de melhor
    na_lista = reg.get(nome, {}).get("projetos", [])
    original = origem.read_bytes()
    proprias = [p for p in aceitos if p != de and p not in na_lista
                and _copia(p, nome).read_bytes() not in (original, texto.encode("utf-8"))]
    if proprias:
        print(f"ATENÇÃO: {', '.join(proprias)} têm versão própria de {nome} e vão perdê-la (fica em comum\\_antigos). "
              f"Se a versão de {de} já junta o que elas têm de bom, rode de novo com --juntei.")
    if testar:
        print("(--testar: nada gravado)")
        return 0
    if proprias and not juntei:
        return 1

    COMUM.mkdir(parents=True, exist_ok=True)
    (COMUM / nome).write_bytes(texto.encode("utf-8"))
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    for p in aceitos:
        destino = _copia(p, nome)
        if destino.exists() and destino.read_bytes() != texto.encode("utf-8"):
            (ANTIGOS / p).mkdir(parents=True, exist_ok=True)
            (ANTIGOS / p / f"{nome}.{carimbo}").write_bytes(destino.read_bytes())
        destino.write_bytes(texto.encode("utf-8"))
    reg[nome] = {"projetos": aceitos, "de": de, "em": datetime.now().isoformat(timespec="seconds")}
    _gravar_registro(reg)
    print(f"gravado: comum\\{nome} + cópia em {', '.join(aceitos)}")
    return 0


def painel():
    reg = _ler_registro()
    print(f"COMUM ({COMUM}) — uma versão só, cópia idêntica em cada projeto da lista:")
    for nome, info in sorted(reg.items()):
        h = _hash(COMUM / nome)
        avisos = []
        for p in info["projetos"]:
            c = _copia(p, nome)
            if not c.exists():
                avisos.append(f"{p}: cópia SUMIU")
            elif _hash(c) != h:
                avisos.append(f"{p}: MUDOU lá -> recursos.py subir {nome} --de {p}")
        for p in PROJETOS:
            if p not in info["projetos"] and _copia(p, nome).exists():
                avisos.append(f"{p}: tem versão PRÓPRIA, fora do comum (não passou nas checagens ou nunca entrou)")
        print(f"  {nome:30s} {', '.join(info['projetos'])}" + ("" if not avisos else "\n      " + "\n      ".join(avisos)))
    if not reg:
        print("  (nenhum ainda)")

    por_nome = {}
    for p, (pasta, *_resto) in PROJETOS.items():
        for f in Path(pasta).glob("*.py"):
            if not f.name.startswith(("_", "test_")) and f.name not in reg and f.name not in NAO_COMUM:
                por_nome.setdefault(f.name, {})[p] = f
    separados = {n: d for n, d in por_nome.items() if len(d) > 1}
    iguais = sorted(n for n, d in separados.items() if len({_hash(f) for f in d.values()}) == 1)
    print(f"\nIGUAIS em 2+ projetos, ainda fora do comum ({len(iguais)}) — entram com: recursos.py subir <x.py> --de <um deles>")
    for n in iguais:
        print(f"  {n:30s} {', '.join(separados[n])}")
    diferentes = sorted((n for n in separados if n not in iguais),
                        key=lambda n: (-len(separados[n]), n))
    print(f"\nSEPARADOS — mesmo nome, versões diferentes ({len(diferentes)}). Juntar o melhor numa cópia e subir dela:")
    for n in diferentes:
        d = separados[n]
        versoes = len({_hash(f) for f in d.values()})
        nova = max(d, key=lambda p: d[p].stat().st_mtime)
        quando = datetime.fromtimestamp(d[nova].stat().st_mtime).strftime("%d/%m")
        print(f"  {n:30s} {len(d)} projetos, {versoes} versões; mais nova: {nova} ({quando}) | {', '.join(d)}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="código comum dos projetos de vídeo")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("subir", help="a versão de um projeto vira a comum e vai pros outros projetos que têm o módulo")
    s.add_argument("nome", help="arquivo, ex.: sem_janela.py")
    s.add_argument("--de", required=True, choices=list(PROJETOS))
    s.add_argument("--testar", action="store_true", help="só confere, não grava")
    s.add_argument("--juntei", action="store_true",
                   help="a versão já junta o melhor das outras: pode trocar as versões próprias dos outros projetos")
    a = ap.parse_args()
    if a.cmd == "subir":
        sys.exit(subir(a.nome if a.nome.endswith(".py") else a.nome + ".py", a.de, a.testar, a.juntei))
    painel()


if __name__ == "__main__":
    main()
