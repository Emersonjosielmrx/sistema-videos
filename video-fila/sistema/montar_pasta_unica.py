# D:\sistema\catalogo\montar_pasta_unica.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/montar_pasta_unica.py)
# OBRA sistema unico - monta D:\sistema\projetos\<categoria>\<projeto>\ a partir do CATALOGO, com JUNCOES (mklink /J)
# para as pastas reais. Nada e movido nem copiado: os caminhos antigos continuam funcionando e D:\sistema mostra
# TUDO o que esta vivo num lugar so. Projeto "parado" no catalogo vai para D:\sistema\parados\. Idempotente (roda de novo
# = so acrescenta o que falta e tira juncao de projeto que saiu do catalogo). Nunca apaga pasta real (rmdir de juncao
# remove so o atalho).
import json
import os
import re
import subprocess
import sys
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(r"D:\sistema")
CAT = json.loads(Path(r"D:\video-fila\sistema\sistema.json").read_text(encoding="utf-8-sig"))
NOMES_CAT = {"A-video": "A-video-producao", "B-postagem": "B-postagem", "C-infra": "C-contas-e-ias",
             "D-central": "D-central-e-maquinas", "E-outros": "E-outros-negocios"}


def e_juncao(p):
    try:
        return bool(os.stat(p, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError:
        return False


def juncao(link, alvo):
    if os.path.exists(link) or e_juncao(link):
        return "ja"
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(alvo)], capture_output=True, text=True, encoding="cp850", errors="replace",
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return "ok" if r.returncode == 0 else f"ERRO {r.stdout.strip()} {r.stderr.strip()}"


criados, erros, esperados = 0, [], set()
for pid, p in CAT["projetos"].items():
    grupo = "parados" if p.get("estado") == "parado" else "projetos"
    base = RAIZ / grupo / NOMES_CAT.get(p["categoria"], p["categoria"]) / pid
    base.mkdir(parents=True, exist_ok=True)
    esperados.add(str(base).lower())
    for pasta in p.get("pastas", []):
        if not re.match(r"^[A-Za-z]:\\", pasta) or not Path(pasta).exists():
            continue
        nome = re.sub(r"[^\w\-]+", "_", pasta[3:]).strip("_") or "raiz"
        link = base / nome
        esperados.add(str(link).lower())
        r = juncao(link, pasta)
        if r == "ok":
            criados += 1
        elif r.startswith("ERRO"):
            erros.append(f"{link}: {r}")
    leia = base / "_PROJETO.txt"
    linhas = [f"{pid} - {p['nome']}", f"estado: {p.get('estado', 'ativo')} | categoria: {p['categoria']}",
              f"chat dono: {p.get('chat_dono', '-')} | doc: {p.get('doc', '-')}", "", "tarefas agendadas no PC1:"]
    linhas += [f"  - {t} ({'ligada' if p.get('tarefas_detalhe', {}).get(t, {}).get('ligada') else 'desligada'})" for t in p.get("tarefas", [])]
    if p.get("servicos_fora"):
        linhas += ["", "roda fora do PC1:"] + [f"  - {s}" for s in p["servicos_fora"]]
    if p.get("obs"):
        linhas += ["", "obs: " + p["obs"]]
    linhas += ["", "(gerado de D:\\sistema\\catalogo\\sistema.json por montar_pasta_unica.py - nao editar)"]
    leia.write_text("\r\n".join(linhas), encoding="utf-8")

# tira juncoes de projeto que saiu do catalogo / mudou de estado (so juncoes; pasta real nunca)
removidos = 0
for grupo in ("projetos", "parados"):
    for cat_dir in (RAIZ / grupo).glob("*"):
        for proj in cat_dir.glob("*"):
            for item in proj.iterdir():
                if e_juncao(item) and str(item).lower() not in esperados:
                    os.rmdir(item)
                    removidos += 1
            if str(proj).lower() not in esperados and not any(e_juncao(x) for x in proj.iterdir()):
                for f in proj.glob("_PROJETO.txt"):
                    f.unlink()
                try:
                    proj.rmdir()
                except OSError:
                    pass

print(f"juncoes criadas: {criados} | removidas: {removidos} | erros: {len(erros)}")
for e in erros:
    print("  ", e)
