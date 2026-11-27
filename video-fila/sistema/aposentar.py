# D:\sistema\catalogo\aposentar.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/aposentar.py)
# OBRA sistema unico - APOSENTA Pythons (venvs) e projetos que ninguem usa mais. Autorizado pela dona em 26/11 ("faca logo"),
# com a condicao: so quando o USO REAL provar 7 dias sem ninguem. Roda no diario (SistemaUnificacao 06:30).
# Para cada alvo, so age se TODAS forem verdade:
#   - o registrador sistema_uso tem pelo menos 7 dias de dados;
#   - nenhum processo nesses 7 dias rodou COM esse Python (campo "py") nem carregou arquivo de dentro da pasta;
#   - nenhuma tarefa agendada LIGADA cita a pasta; nenhum processo rodando agora cita a pasta;
#   - nenhum .bat/.ps1/.py VIVO (uso real) cita a pasta.
# Acao: arquivar_drive (copia para conta32:arquivo-pc1/obra-26nov, rclone check, so entao remove). Volta: arquivar_drive.py --voltar.
#   python aposentar.py          diz o veredito de cada alvo      python aposentar.py --aplicar
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DIAS = int(os.environ.get("APOSENTAR_DIAS", "7"))  # 27/11: dona mandou adiantar ("faca logo") -> APOSENTAR_DIAS=2
ALVOS = [  # (pasta, o que e) - os 2 que ficam para sempre: D:\veo\venv (principal) e venv_vozes (vozes/GPU)
    (r"D:\hipercool-videos\venv", "Python do hipercool"),
    (r"D:\hipercool-materiais\python\venv", "Python do hipercool-materiais"),
    (r"D:\hipercool-materiais\python\venv_imgutils", "Python de imagem"),
    (r"D:\recapd-ambientes\producao\venv", "Python do recap"),
    (r"D:\manhwa-react\.venv", "Python do ManhwaReact"),
    (r"D:\recap_central_casa\venv", "Python da central casa"),
    (r"D:\tmp\xtts88\venvp", "Python de teste do xtts"),
    (r"D:\historias-em-frames", "projeto Historias em Frames inteiro (4 venvs)"),
]


def real(p):
    try:
        return os.path.realpath(p).lower().rstrip("\\")
    except OSError:
        return p.lower().rstrip("\\")


def dados():
    arqs = sorted(Path(r"D:\sistema\mapa\uso").glob("uso_*.jsonl"))
    regs = []
    for f in arqs[-DIAS:]:
        for l in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                regs.append(json.loads(l))
            except ValueError:
                pass
    return len(arqs), regs


def textos_vivos(regs):
    vivos = {x.lower() for j in regs for x in j.get("locais", []) + [j.get("main", "")] if x.lower().endswith(".py")}
    cat = json.loads(Path(r"D:\sistema\catalogo\sistema.json").read_text(encoding="utf-8-sig"))
    cmds = " ".join(d["cmd"].lower() for p in cat["projetos"].values() for d in p.get("tarefas_detalhe", {}).values() if d.get("ligada"))
    bats = set()
    for c in cmds.split():
        if c.endswith((".bat", ".ps1")):
            bats.add(c.strip('"'))
    txt = ""
    for f in list(vivos) + list(bats):
        try:
            txt += open(f, encoding="utf-8", errors="ignore").read().lower() + "\n"
        except OSError:
            pass
    return cmds, txt


def veredito(pasta, n_dias, regs, cmds, txt, procs):
    if not os.path.exists(pasta):
        return "JA NAO EXISTE"
    if n_dias < DIAS:
        return f"ESPERA ({n_dias}/{DIAS} dias de uso real)"
    pl, pr = pasta.lower().rstrip("\\"), real(pasta)
    for j in regs:
        py = (j.get("py") or "").lower()
        if py.startswith(pl + "\\") or py.startswith(pr + "\\"):
            return f"EM USO (rodou com ele em {j.get('t')}: {j.get('main')})"
        for x in j.get("locais", []):
            if x.lower().startswith(pl + "\\") or x.lower().startswith(pr + "\\"):
                return f"EM USO (carregou {x} em {j.get('t')})"
    if pl in cmds or pr in cmds:
        return "EM USO (tarefa ligada cita)"
    if pl in procs or pr in procs:
        return "EM USO (processo rodando agora)"
    if pl in txt or pr in txt:
        return "EM USO (codigo vivo cita o caminho)"
    m = montado_por_partes(pasta)
    if m:
        return f"EM USO (codigo monta o caminho por partes: {m})"
    return "OK"


def montado_por_partes(pasta):
    """27/11: fila.py faz PY = PROJECT / "venv" / ... (sem o caminho inteiro escrito) -> a checagem de texto nao via.
    Procura o NOME da pasta do venv como texto solto ("venv", 'venv_imgutils', \\venv\\, /venv/) nos .py/.bat/.ps1 do
    projeto dono (pasta-mae do venv e as 2 acima), fora de venvs, sistema2 e backups."""
    nome = os.path.basename(pasta.rstrip("\\"))
    if not re.match(r"^\.?venv", nome, re.I):
        return ""
    pat = re.compile(r"[\"'\\/]" + re.escape(nome) + r"[\"'\\/]", re.I)
    mae = os.path.dirname(pasta.rstrip("\\"))
    raizes = {mae, os.path.dirname(mae)}
    for raiz in raizes:
        if not os.path.isdir(raiz) or len(raiz) <= 3:
            continue
        for dp, dn, fn in os.walk(raiz):
            dn[:] = [d for d in dn if not re.match(r"^(\.?venv.*|site-packages|node_modules|__pycache__|\.git|_?bak.*|_?backup.*)$", d, re.I)]
            for f in fn:
                if not f.lower().endswith((".py", ".bat", ".ps1", ".cmd", ".vbs")) or ".bak" in f.lower():
                    continue
                c = os.path.join(dp, f)
                try:
                    if pat.search(open(c, encoding="utf-8", errors="ignore").read()):
                        return c
                except OSError:
                    pass
    return ""


def main(aplicar):
    n, regs = dados()
    cmds, txt = textos_vivos(regs)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process | %{ $_.CommandLine; $_.ExecutablePath }"],
                       capture_output=True, timeout=180, creationflags=SEM_JANELA)
    procs = r.stdout.decode("utf-8", "replace").lower()
    aprovados = []
    for pasta, oque in ALVOS:
        v = veredito(pasta, n, regs, cmds, txt, procs)
        print(f"{v[:70]:70} {pasta}  ({oque})")
        if v == "OK":
            aprovados.append((pasta, f"aposentado: {oque} (7 dias sem uso real)"))
    if aplicar and aprovados:
        sys.path.insert(0, r"D:\sistema\catalogo")
        import arquivar_drive as ad
        ad.ALVOS = aprovados
        ad.DIAS_PARADA = 0  # a prova aqui e o uso real de 7 dias, nao a data do arquivo
        ad.aplicar(so_plano=False)


main("--aplicar" in sys.argv)
