# D:\sistema\catalogo\limpar_scripts.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/limpar_scripts.py)
# OBRA sistema unico - LIMPEZA SCRIPT POR SCRIPT (ideia da dona 27/11): D:\sistema fica so com o codigo VALIDO;
# o resto vai para D:\sistema2\<MESMO caminho relativo>. Equivale a "renomear sistema->sistema2 e trazer de volta so os
# validos", mas ao contrario (tira os mortos), entao NADA para e nenhum script precisa ser editado: os vivos nao saem do lugar.
# So CODIGO sai (.py .bat .ps1 .vbs .cmd .sh). Dados, json, videos, venvs, node_modules, segredos: nao mexe.
# Um script e VALIDO (fica) se qualquer uma for verdade:
#   1) rodou/foi importado de verdade (registrador sistema_uso, todos os dias registrados);
#   2) qualquer tarefa agendada (ligada OU desligada) cita ele; ou algum processo rodando agora cita;
#   3) e citado (nome do arquivo ou nome do modulo) por um script valido -> fecho repetido ate parar de crescer;
#   4) foi mexido nos ultimos DIAS_NOVO dias (em desenvolvimento);
#   5) e hardlink do codigo comum, __init__.py, ou esta em catalogo/comum/mapa.
# Mudar = os.rename no mesmo disco (instantaneo). Registro: D:\sistema\mapa\limpeza_scripts.json.
# REDE DE SEGURANCA (--rede, tarefa RedeLimpeza a cada 10 min): se um log recente ou tarefa reclamar de arquivo/modulo
# que foi para sistema2, ele VOLTA sozinho na hora (e fica marcado "voltou" para nunca mais sair).
#   python limpar_scripts.py              simula (lista e conta)
#   python limpar_scripts.py --aplicar    muda os mortos para D:\sistema2
#   python limpar_scripts.py --rede       rede de seguranca (devolve o que fez falta)
#   python limpar_scripts.py --voltar NOME_OU_CAMINHO   devolve um     --voltar-tudo   devolve todos
#   python limpar_scripts.py --drive      (27/11, pedido da dona) copia D:\sistema2 para o Drive (conta32:arquivo-pc1/
#       sistema2-scripts-mortos/<mesmo caminho>), confere com rclone check, escreve o INDICE (mapa\SCRIPTS_NO_DRIVE.md,
#       tambem no Drive) e, para quem esta ha DIAS_LOCAL dias fora SEM ter feito falta, tira a copia do PC1 (fica so no Drive).
#       --voltar/--rede trazem do Drive quando a copia local ja saiu. Roda no diario 06:30.
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = r"D:\sistema"
DEST = r"D:\sistema2"
REG = Path(r"D:\sistema\mapa\limpeza_scripts.json")
LOG = Path(r"D:\sistema\mapa\limpeza_scripts.log")
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
RCLONE = r"D:\tools\rclone.exe"
DRIVE = "conta32:arquivo-pc1/sistema2-scripts-mortos"
INDICE = Path(r"D:\sistema\mapa\SCRIPTS_NO_DRIVE.md")
DIAS_LOCAL = int(os.environ.get("LIMPEZA_DIAS_LOCAL", "7"))
EXT = (".py", ".pyw", ".bat", ".ps1", ".vbs", ".cmd", ".sh")
DIAS_NOVO = int(os.environ.get("LIMPEZA_DIAS_NOVO", "14"))
PULA_DIR = re.compile(r"^(venv[^\\]*|\.venv|site-packages|node_modules|__pycache__|\.git|catalogo|comum|mapa|"
                      r"quarentena|secrets|perfis|cofre)$", re.I)
TOKEN = re.compile(r"[A-Za-z_][\w\-]*(?:\.(?:py|pyw|bat|ps1|vbs|cmd|sh))?", re.I)


def norm(p):
    try:
        return os.path.normcase(os.path.realpath(p))
    except (OSError, ValueError):
        return os.path.normcase(p)


def e_juncao(p):
    try:
        return bool(os.stat(p, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError:
        return False


def todos_codigos():
    out = []
    for dp, dn, fn in os.walk(RAIZ):
        dn[:] = [d for d in dn if not PULA_DIR.match(d) and not e_juncao(os.path.join(dp, d))]
        for f in fn:
            if f.lower().endswith(EXT) and ".bak" not in f.lower():
                out.append(os.path.join(dp, f))
    return out


def ps(cmd, t=240):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=t,
                       creationflags=SEM_JANELA)
    return r.stdout.decode("utf-8", "replace")


def evidencias():
    usados, dias = set(), 0
    for f in sorted(Path(r"D:\sistema\mapa\uso").glob("uso_*.jsonl")):
        dias += 1
        for l in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                j = json.loads(l)
            except ValueError:
                continue
            for a in j.get("locais", []) + [j.get("main") or ""]:
                if a:
                    usados.add(a)
    usados = {norm(a) for a in usados}
    tarefas = ps("[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-ScheduledTask | %{ $_.Actions | "
                 "%{ $_.Execute + ' ' + $_.Arguments + ' ' + $_.WorkingDirectory } }")
    procs = ps("[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-CimInstance Win32_Process | %{ $_.CommandLine }")
    # atalhos (.lnk) da area de trabalho / menu iniciar / inicializar: botoes que a dona clica a mao
    lnk = ps("[Console]::OutputEncoding=[Text.Encoding]::UTF8; $w=New-Object -ComObject WScript.Shell; "
             "$d=@([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('CommonDesktopDirectory'),"
             "[Environment]::GetFolderPath('StartMenu'),[Environment]::GetFolderPath('CommonStartMenu'),"
             "[Environment]::GetFolderPath('Startup')); Get-ChildItem $d -Recurse -Filter *.lnk -ErrorAction "
             "SilentlyContinue | %{ $s=$w.CreateShortcut($_.FullName); $s.TargetPath + ' ' + $s.Arguments }")
    return usados, dias, (tarefas + "\n" + procs + "\n" + lnk)


def ler_txt(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as fh:
            return fh.read(2_000_000)
    except OSError:
        return ""


def classificar():
    codigos = todos_codigos()
    usados, dias, cmds = evidencias()
    cmds_l = cmds.lower()
    # caminhos citados nas tarefas/processos tambem pelo caminho antigo (D:\video-fila\...) -> realpath
    citados = {norm(m) for m in re.findall(r"[A-Za-z]:\\[^\"'\r\n]*?\.(?:py|pyw|bat|ps1|vbs|cmd|sh)\b", cmds, re.I)}
    agora = time.time()
    vivo, motivo = set(), {}
    # pastas de notebook (Kaggle/Colab) sobem INTEIRAS: tudo dentro de pasta com kernel-metadata.json fica
    kernels = set()
    for c in codigos:
        d = os.path.dirname(c)
        if d not in kernels and os.path.exists(os.path.join(d, "kernel-metadata.json")):
            kernels.add(d)
    for c in codigos:
        n = os.path.normcase(c)
        m = None
        if os.path.dirname(c) in kernels:
            m = "pasta de notebook"
        elif n in usados:
            m = "rodou (uso real)"
        elif n in citados or n in cmds_l:
            m = "tarefa/processo"
        elif os.path.basename(c).lower() == "__init__.py":
            m = "__init__"
        else:
            try:
                st = os.stat(c)
                if st.st_nlink > 1:
                    m = "codigo comum"
                elif agora - st.st_mtime < DIAS_NOVO * 86400:
                    m = f"mexido ha {(agora - st.st_mtime) / 86400:.0f}d"
            except OSError:
                m = "erro ao ler (fica)"
        if m:
            vivo.add(c)
            motivo[c] = m
    # fecho: tudo que um valido cita (nome do arquivo ou do modulo) tambem e valido
    tokens = set()
    novos = list(vivo)
    while novos:
        for v in novos:
            tokens |= {t.lower() for t in TOKEN.findall(ler_txt(v))}
        tokens |= {t.lower() for t in TOKEN.findall(cmds)}
        novos = []
        for c in codigos:
            if c in vivo:
                continue
            b = os.path.basename(c).lower()
            if b in tokens or os.path.splitext(b)[0] in tokens:
                vivo.add(c)
                motivo[c] = "citado por valido"
                novos.append(c)
    mortos = [c for c in codigos if c not in vivo]
    return codigos, vivo, mortos, motivo, dias


def ler():
    return json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}


def salvar(d):
    REG.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def logar(s):
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + s + "\n")


def destino(c):
    return os.path.join(DEST, os.path.relpath(c, RAIZ))


def mover(a, b):
    os.makedirs(os.path.dirname(b), exist_ok=True)
    os.rename(a, b)


def aplicar(fazer):
    codigos, vivo, mortos, motivo, dias = classificar()
    reg = ler()
    voltaram = {k.lower() for k, v in reg.items() if v.get("estado") == "voltou"}
    mortos = [m for m in mortos if m.lower() not in voltaram]
    cont = {}
    for m in motivo.values():
        k = m if not m.startswith("mexido") else "mexido recente"
        cont[k] = cont.get(k, 0) + 1
    print(f"dias de uso real registrados: {dias}")
    print(f"scripts em D:\\sistema: {len(codigos)} | validos: {len(vivo)} | mortos: {len(mortos)}")
    for k, v in sorted(cont.items(), key=lambda x: -x[1]):
        print(f"   fica por {k}: {v}")
    por_pasta = {}
    for m in mortos:
        p = os.path.relpath(m, RAIZ).split("\\")
        por_pasta.setdefault("\\".join(p[:3]), []).append(m)
    for p, l in sorted(por_pasta.items(), key=lambda x: -len(x[1]))[:40]:
        print(f"   {len(l):5} mortos em {p}")
    if not fazer:
        return
    feitos = 0
    for m in mortos:
        d = destino(m)
        if os.path.exists(d):
            d = d + f".dup{int(time.time())}"
        try:
            mover(m, d)
        except OSError as e:
            print(f"   nao movi {m}: {e}")
            continue
        reg[m] = {"estado": "em_sistema2", "para": d, "em": time.strftime("%Y-%m-%dT%H:%M:%S")}
        feitos += 1
    salvar(reg)
    logar(f"aplicar: {feitos} scripts mortos -> {DEST}")
    print(f"movidos para {DEST}: {feitos}")


def devolver(chave, motivo):
    reg = ler()
    n = 0
    for orig, e in reg.items():
        if e.get("estado") not in ("em_sistema2", "so_no_drive"):
            continue
        if chave == "*" or chave.lower() == orig.lower() or chave.lower() == os.path.basename(orig).lower() \
                or chave.lower() == os.path.splitext(os.path.basename(orig))[0].lower():
            try:
                if e.get("estado") == "so_no_drive":  # copia local ja saiu: traz do Drive
                    os.makedirs(os.path.dirname(orig), exist_ok=True)
                    r = subprocess.run([RCLONE, "copyto", e["drive"], orig, "--retries", "3"], capture_output=True,
                                       timeout=600, creationflags=SEM_JANELA)
                    if r.returncode or not os.path.exists(orig):
                        raise OSError("rclone falhou: " + r.stderr.decode("utf-8", "replace")[-200:])
                else:
                    mover(e["para"], orig)
            except OSError as x:
                print(f"nao voltou {orig}: {x}")
                continue
            e["estado"] = "voltou"
            e["voltou_em"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            e["motivo_volta"] = motivo
            n += 1
            logar(f"VOLTOU {orig} ({motivo})")
            print("voltou", orig)
    salvar(reg)
    return n


ERRO = re.compile(r"(can't open file|No such file|Errno 2|No module named|not recognized|reconhecido|cannot find|"
                  r"nao pode|não pode|ModuleNotFoundError|ImportError|FileNotFoundError)", re.I)


def rede():
    reg = ler()
    fora = {o: e for o, e in reg.items() if e.get("estado") in ("em_sistema2", "so_no_drive")}
    if not fora:
        return
    nomes = {}
    for o in fora:
        b = os.path.basename(o).lower()
        nomes[b] = o
        nomes.setdefault(os.path.splitext(b)[0], o)
    desde = time.time() - 1800
    achados = set()
    for dp, dn, fn in os.walk(RAIZ):
        dn[:] = [d for d in dn if not re.match(r"^(venv[^\\]*|\.venv|site-packages|node_modules|__pycache__|\.git)$",
                                                d, re.I) and not e_juncao(os.path.join(dp, d))]
        for f in fn:
            if not f.lower().endswith((".log", ".txt", ".err", ".out")):
                continue
            p = os.path.join(dp, f)
            try:
                if os.stat(p).st_mtime < desde:
                    continue
                with open(p, "rb") as fh:
                    fh.seek(max(0, os.path.getsize(p) - 65536))
                    txt = fh.read().decode("utf-8", "ignore")
            except OSError:
                continue
            for linha in txt.splitlines():
                if not ERRO.search(linha):
                    continue
                for t in TOKEN.findall(linha):
                    if t.lower() in nomes:
                        achados.add(nomes[t.lower()])
    # tarefa que falhou com "arquivo nao encontrado" (0x80070002 = 2147942402) e cita um script movido
    t = ps("[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-ScheduledTask | ?{ $_.State -ne 'Disabled' } | %{ "
           "$i = $_ | Get-ScheduledTaskInfo; if ($i.LastTaskResult -eq 2147942402 -or $i.LastTaskResult -eq 1 -or "
           "$i.LastTaskResult -eq 2) { $_.Actions | %{ $_.Execute + ' ' + $_.Arguments } } }", t=180)
    for tok in TOKEN.findall(t):
        if tok.lower() in nomes and tok.lower().endswith(EXT):
            achados.add(nomes[tok.lower()])
    for o in achados:
        devolver(o, "rede: fez falta (log/tarefa reclamou)")


def rc(*args, timeout=3600):
    r = subprocess.run([RCLONE, *args], capture_output=True, timeout=timeout, creationflags=SEM_JANELA)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")[-400:]


def para_drive():
    reg = ler()
    if not os.path.isdir(DEST):
        print("sem D:\\sistema2")
        return
    c, out = rc("copy", DEST, DRIVE, "--transfers", "8", "--retries", "5")
    if c:
        print("!! copia para o Drive falhou, nada saiu do PC1:", out)
        logar("drive: copia FALHOU")
        return
    c, out = rc("check", DEST, DRIVE, "--one-way")
    if c:
        print("!! conferencia falhou, nada saiu do PC1:", out)
        logar("drive: check FALHOU")
        return
    agora = time.time()
    novos = tirados = 0
    for orig, e in reg.items():
        if e.get("estado") != "em_sistema2":
            continue
        if "drive" not in e:
            e["drive"] = DRIVE + "/" + os.path.relpath(e["para"], DEST).replace("\\", "/")
            e["no_drive_em"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            novos += 1
        desde = time.mktime(time.strptime(e["em"], "%Y-%m-%dT%H:%M:%S"))
        if agora - desde >= DIAS_LOCAL * 86400 and os.path.exists(e["para"]):
            os.remove(e["para"])  # Drive conferido acima (check --one-way) = a copia esta la igual
            e["estado"] = "so_no_drive"
            e["saiu_do_pc1_em"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            tirados += 1
    salvar(reg)
    # indice legivel: onde cada script estava e onde esta no Drive
    linhas = ["# Scripts mortos guardados no Drive (obra sistema unico)", "",
              f"Atualizado {time.strftime('%d/%m/%Y %H:%M')}. Drive: `{DRIVE}` (conta32). Cada script fica no MESMO caminho "
              "que tinha dentro de D:\\sistema.", "",
              "Trazer de volta: `D:\\veo\\venv\\Scripts\\python.exe D:\\sistema\\catalogo\\limpar_scripts.py --voltar NOME`"
              " (ou --voltar-tudo). A tarefa RedeLimpeza devolve sozinha o que um log/tarefa reclamar.", "",
              "| estado | caminho original | saiu em |", "|---|---|---|"]
    for orig, e in sorted(reg.items()):
        linhas.append(f"| {e.get('estado')} | {orig} | {e.get('em', '')[:10]} |")
    INDICE.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    rc("copyto", str(INDICE), DRIVE + "/SCRIPTS_NO_DRIVE.md")
    logar(f"drive: {novos} novos no Drive (conferido), {tirados} sairam do PC1 (>{DIAS_LOCAL} dias sem fazer falta)")
    print(f"no Drive e conferido: {sum(1 for e in reg.values() if 'drive' in e)} | novos agora: {novos} | "
          f"sairam do PC1 agora: {tirados} | indice: {INDICE}")


a = sys.argv[1:]
if "--drive" in a:
    para_drive()
elif "--rede" in a:
    rede()
elif "--voltar-lista" in a:  # arquivo com 1 nome (ou caminho) por linha; motivo opcional em --motivo "..."
    mot = a[a.index("--motivo") + 1] if "--motivo" in a else "lista"
    for nome in Path(a[a.index("--voltar-lista") + 1]).read_text(encoding="utf-8").split("\n"):
        if nome.strip():
            devolver(nome.strip(), mot)
elif "--voltar-tudo" in a:
    devolver("*", "voltar-tudo")
elif "--voltar" in a:
    devolver(a[a.index("--voltar") + 1], "manual")
else:
    aplicar("--aplicar" in a)
