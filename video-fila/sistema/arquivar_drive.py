# D:\sistema\catalogo\arquivar_drive.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/arquivar_drive.py)
# OBRA sistema unico - LIMPEZA PARA O DRIVE com verificacao (pedido da dona 26/11: "va limpando o lixo, mandando pro Drive
# depois de verificar que realmente nao precisa"). Nada e apagado sem antes:
#   1) checar que NADA vivo usa a pasta (uso real do sistema_uso + mapa estatico + tarefas ligadas + processos agora);
#   2) copiar para conta32:arquivo-pc1/obra-26nov/<caminho> (Drive com 2,4 TB livres);
#   3) rclone check --one-way (todo arquivo do PC1 tem que existir igual no Drive);
#   4) so entao tirar do PC1 (vai para a LIXEIRA do Windows? nao: remove; o Drive E a copia, e o Drive tem lixeira de 30 dias).
# Registro: D:\sistema\mapa\arquivados.json (origem, destino no Drive, tamanho, data, motivo). Volta: arquivar_drive.py --voltar ORIGEM
#   python arquivar_drive.py --plano            lista candidatos e o veredito (nao mexe)
#   python arquivar_drive.py --aplicar          arquiva os aprovados da lista ALVOS
#   python arquivar_drive.py --voltar ORIGEM    baixa de volta do Drive
import json
import os
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RCLONE = r"D:\tools\rclone.exe"
DRIVE = "conta32:arquivo-pc1/obra-26nov"
REG = Path(r"D:\sistema\mapa\arquivados.json")
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DIAS_PARADA = 14

# (pasta, motivo). So entra aqui o que foi conferido como sobra; o --plano ainda checa uso antes de mexer.
ALVOS = [
    (r"D:\sistema\quarentena", "quarentena da obra: backups/testes/diag/tmp com 14+ dias sem uso e projetos parados (trader voltou)"),
    (r"D:\_recuperacao de HD", "recuperacao de HD de outubro"),
    (r"D:\SteamLibrary", "biblioteca Steam vazia"),
    (r"D:\AUDITORIA_MELHORIAS_20261015", "auditoria de 15/10"),
    (r"D:\tmp_hfsweep", "teste de 15/10"),
    (r"D:\tmp_revisao_censura", "teste de 20/10"),
    (r"D:\projeto-navegador-sem-navegador_backup_20261030", "backup de 30/10 do NSN"),
    (r"D:\opus-gratis-copia-desktop", "copia antiga (vale o opus-gratis-v2-desktop)"),
    (r"D:\opus-gratis-desktop", "versao antiga (vale o opus-gratis-v2-desktop)"),
    (r"D:\opus-gratis", "versao antiga (vale o opus-gratis-v2-desktop)"),
    (r"D:\_pacote_outro_pc", "pacote de instalacao de 16/10"),
    (r"D:\pacote_build", "build de 12/11"),
    (r"D:\claude-code-video-adicional", "sobra de 26/10"),
    (r"D:\hipercool-producao", "producao antiga do hipercool (25/10)"),
    (r"D:\hipercool-motionframes", "teste de 09/10"),
    (r"D:\temp", "temporario de 09/11"),
    (r"D:\d", "pasta solta de 04/11"),
    (r"D:\caches\reel_insta.mp4", "teste de 27/10"),
    (r"D:\caches\reel_frames", "teste de 27/10"),
    (r"D:\caches\yt_tmp", "temporario de 25/10"),
    (r"D:\caches\go-mod", "cache Go de 06/11 (nenhum projeto Go roda)"),
    (r"D:\tmp\t_pesq", "teste de 18/11"),
    (r"D:\tmp\t_tubescrape", "teste de 15/11"),
    (r"D:\tmp\narr", "teste de 14/10"),
    (r"D:\tmp\sons_descartados", "sons descartados 22/11"),
    (r"D:\tmp\sons_antigos_rotulo_errado", "sons com rotulo errado 22/11"),
    (r"D:\tmp\lemo.tgz", "pacote de 24/11"),
    (r"D:\tmp\last30days.tgz", "pacote de 24/11"),
]


def e_juncao(p):
    try:
        return bool(os.stat(p, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError:
        return False


def info(p):
    tam, novo = 0, 0
    if os.path.isfile(p):
        st = os.stat(p)
        return st.st_size, st.st_mtime
    for dp, dn, fn in os.walk(p):
        dn[:] = [d for d in dn if not e_juncao(os.path.join(dp, d))]
        for f in fn:
            try:
                st = os.stat(os.path.join(dp, f))
                tam += st.st_size
                novo = max(novo, st.st_mtime)
            except OSError:
                pass
    return tam, novo


def usos():
    v = set()
    for f in Path(r"D:\sistema\mapa\uso").glob("uso_*.jsonl"):
        for l in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                j = json.loads(l)
            except ValueError:
                continue
            for a in j.get("locais", []) + [j.get("main", ""), (j.get("cwd") or "") + "\\"]:
                v.add(a.lower())
    try:
        v |= set(json.loads(Path(r"D:\sistema\mapa\mapa_vivo.json").read_text(encoding="utf-8"))["vivos"])
    except (OSError, ValueError, KeyError):
        pass
    cat = json.loads(Path(r"D:\sistema\catalogo\sistema.json").read_text(encoding="utf-8-sig"))
    cmds = " ".join(d["cmd"].lower() for p in cat["projetos"].values() for d in p.get("tarefas_detalhe", {}).values() if d.get("ligada"))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process | %{ $_.CommandLine }"],
                       capture_output=True, timeout=120, creationflags=SEM_JANELA)
    procs = r.stdout.decode("utf-8", "replace").lower()
    return v, cmds, procs


def veredito(p, V, cmds, procs):
    pl = p.lower().rstrip("\\")
    if not os.path.exists(p):
        return "NAO EXISTE", 0
    tam, novo = info(p)
    if any(x.startswith(pl + "\\") or x == pl for x in V):
        return "EM USO (uso real/mapa)", tam
    if pl in cmds:
        return "EM USO (tarefa ligada)", tam
    if pl in procs:
        return "EM USO (processo rodando)", tam
    if p.lower() != r"d:\sistema\quarentena" and novo and time.time() - novo < DIAS_PARADA * 86400:
        return f"MEXIDA ha {(time.time() - novo) / 86400:.0f} dias", tam
    return "OK", tam


def rc(*a, timeout=7200):
    r = subprocess.run([RCLONE, *a], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, creationflags=SEM_JANELA)
    return r.returncode, (r.stdout + r.stderr)[-600:]


def ler():
    return json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else []


def salvar(r):
    REG.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")


def remover(p):
    if os.path.isfile(p):
        os.remove(p)
        return
    import shutil
    def onerr(f, x, _):
        os.chmod(x, 0o666)
        f(x)
    shutil.rmtree(p, onerror=onerr)


def aplicar(so_plano):
    V, cmds, procs = usos()
    reg = ler()
    total = livre = 0
    for p, motivo in ALVOS:
        v, tam = veredito(p, V, cmds, procs)
        total += tam
        print(f"{v:28} {tam / 1e6:9.1f} MB  {p}  ({motivo})")
        if so_plano or v != "OK":
            continue
        dest = f"{DRIVE}/{p[3:].replace(chr(92), '/')}"
        if os.path.isfile(p):
            c, out = rc("copyto", p, dest, "--retries", "5")
            ok = c == 0 and rc("check", os.path.dirname(p), os.path.dirname(dest), "--one-way", "--include",
                                os.path.basename(p))[0] == 0
        else:
            c, out = rc("copy", p, dest, "--transfers", "8", "--retries", "5", "--copy-links")
            ok = c == 0 and rc("check", p, dest, "--one-way", "--copy-links")[0] == 0
        if not ok:
            print(f"   !! copia/conferencia falhou, NAO removi: {out[-200:]}")
            continue
        remover(p)
        reg.append({"origem": p, "drive": dest, "mb": round(tam / 1e6, 1), "em": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "motivo": motivo})
        salvar(reg)
        livre += tam
        print(f"   ARQUIVADA no Drive e conferida -> removida do PC1")
    print(f"candidatos: {total / 1e9:.2f} GB | liberado agora: {livre / 1e9:.2f} GB")


def voltar(orig):
    for e in ler():
        if e["origem"].lower() == orig.lower():
            c, out = rc("copy", e["drive"], orig, "--transfers", "8")
            print("ok" if c == 0 else out)
            return
    print("nao achei no registro")


a = sys.argv[1:]
if "--voltar" in a:
    voltar(a[a.index("--voltar") + 1])
else:
    aplicar(so_plano="--aplicar" not in a)
