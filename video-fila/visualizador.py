"""visualizador.py — o x200ma (Celeron N2830, 2 núcleos, 1,8 GB) é o VISUALIZADOR: cada vídeo que vai ao ar no YouTube
abre no Chrome de lá, um por vez, pro dono assistir, dar like e comentar (isso fica com ele: like/comentário automático
é engajamento falso pro YouTube). O x200ma não vê os registros do PC1, então este manda a lista pra ele.

  python visualizador.py enviar    # tarefa VisualizadorX200 (10 em 10 min): vídeos de 6 h atrás até 48 h pra frente
  python visualizador.py instalar  # copia x200ma\\visualizador.py + serviço do usuário lá e liga
  python visualizador.py status    # o que está aberto lá e o que vem
  python visualizador.py pausar | retomar

Fonte: registro de uploads do postador (politica: canal, video_id, publish_at — gravado na hora do upload) + o catálogo
(postagens do YouTube que só ele tem). Acesso: `ssh x200ma` (OpenSSH na 2222 só com chave, ~/.ssh/config).
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
POSTADOR = Path(r"D:\postador-de-videos")
CATALOGO = POSTADOR / "config" / "catalogo_videos.json"
ESTADO = BASE / "estado" / "visualizador.json"
LOGF = BASE / "logs" / "visualizador.log"
HOST = "x200ma"
HOST_LONGOS = "desktop"  # 01/11 dona: longos (tipo "completo") só no desktop; notebook só curtos
REMOTO = "~/visualizador"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe" if Path(r"C:\Program Files\Git\usr\bin\ssh.exe").exists() else "ssh"
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
ATRAS_H, FRENTE_H = 6, 48

SERVICO = """[Unit]
Description=Visualizador dos videos postados (lista vem do PC1)

[Service]
ExecStart=/usr/bin/python3 %h/visualizador/visualizador.py
Restart=always
RestartSec=30

[Install]
WantedBy=default.target
"""


def log(msg):
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(linha, flush=True)
    LOGF.parent.mkdir(parents=True, exist_ok=True)
    with LOGF.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def ssh(cmd, entrada=None, timeout=60):
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST, cmd], input=entrada,
                       capture_output=True, timeout=timeout, creationflags=_SEM_JANELA)
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace"), (r.stderr or b"").decode("utf-8", "replace")


def _dt(s):
    if not s:
        return None
    d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return d if d.tzinfo else d.astimezone()


def montar():
    agora = datetime.now(timezone.utc)
    ini, fim = agora - timedelta(hours=ATRAS_H), agora + timedelta(hours=FRENTE_H)
    vids = {}

    def por(vid, quando, canal, projeto, tipo):
        if vid and quando and ini <= quando <= fim:
            vids[vid] = {"id": vid, "quando": quando.astimezone(timezone.utc).isoformat(timespec="seconds"),
                         "canal": (canal or "").removeprefix("YouTube ").strip() or None, "projeto": projeto, "tipo": tipo}

    try:
        cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cat = {}
    for v in cat.get("videos", []):
        for p in v.get("postagens", []):
            if p.get("plataforma") == "youtube":
                por(p.get("id"), _dt(p.get("quando")), p.get("conta"), v.get("projeto"), None)
    sys.path.insert(0, str(POSTADOR / "bin"))
    import politica  # registro do upload: vence o catálogo (mais novo e com tipo)
    for r in politica._ler_ledger():
        por(r.get("video_id"), _dt(r.get("publish_at")) or _dt(r.get("ts")), r.get("canal"), r.get("projeto"), r.get("tipo"))
    return sorted(vids.values(), key=lambda x: x["quando"])


def _gravar(dados):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ESTADO)


def _desk(cmd, entrada=None, timeout=60):
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST_LONGOS, cmd], input=entrada,
                       capture_output=True, timeout=timeout, creationflags=_SEM_JANELA)
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace"), (r.stderr or b"").decode("utf-8", "replace")


def enviar_longos(longos):
    """01/11 dona: longos só no DESKTOP (Windows, D:\\visualizador\\fila.json lido pelo desktop\\visualizador_win.py)."""
    corpo = json.dumps({"gerado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "videos": longos},
                       ensure_ascii=False).encode("utf-8")
    try:
        rc, out, err = _desk("$t=[Console]::In.ReadToEnd(); New-Item -ItemType Directory -Force D:\\visualizador "
                             "| Out-Null; [IO.File]::WriteAllText('D:\\visualizador\\fila.json', $t, "
                             "(New-Object Text.UTF8Encoding $false)); 'ENVIADO'; "
                             "Get-Content D:\\visualizador\\estado.json -Raw -ErrorAction SilentlyContinue", entrada=corpo)
    except subprocess.TimeoutExpired:
        rc, out, err = -1, "", "timeout"
    ok = "ENVIADO" in out  # o PowerShell remoto sai com 1 se o estado.json ainda não existe — não é falha
    log(f"enviar longos (desktop): {'ok' if ok else 'FALHOU'} — {len(longos)} longo(s)"
        + ("" if ok else f" | {(err.strip() or out.strip())[-200:]}"))
    return ok


def enviar():
    todos = montar()
    longos = [v for v in todos if v.get("tipo") == "completo"]
    videos = [v for v in todos if v.get("tipo") != "completo"]  # x200ma (notebook): só curtos
    enviar_longos(longos)
    corpo = json.dumps({"gerado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "videos": videos},
                       ensure_ascii=False).encode("utf-8")
    try:
        rc, out, err = ssh(f"mkdir -p {REMOTO} && cat > {REMOTO}/fila.json.tmp && mv {REMOTO}/fila.json.tmp "
                           f"{REMOTO}/fila.json && echo ENVIADO && (cat {REMOTO}/estado.json 2>/dev/null || true)", entrada=corpo)
    except subprocess.TimeoutExpired:
        rc, out, err = -1, "", "timeout"
    ok = rc == 0 and out.startswith("ENVIADO")
    remoto = {}
    if ok:
        try:
            remoto = json.loads(out.split("\n", 1)[1] or "{}")
        except ValueError:
            pass
    _gravar({"ultimo_envio": datetime.now().isoformat(timespec="seconds"), "ok": ok, "videos": len(videos),
             "erro": None if ok else (err.strip() or out.strip())[-300:], "x200ma": remoto})
    log(f"enviar: {'ok' if ok else 'FALHOU'} — {len(videos)} vídeo(s) na lista"
        + (f" | lá: {remoto.get('situacao')}" if ok else f" | {(err.strip() or out.strip())[-200:]}"))
    return ok


def instalar():
    script = (BASE / "x200ma" / "visualizador.py").read_bytes()
    passos = [
        (f"mkdir -p {REMOTO} ~/.config/systemd/user && cat > {REMOTO}/visualizador.py", script),
        ("cat > ~/.config/systemd/user/visualizador.service", SERVICO.encode("utf-8")),
        ("export XDG_RUNTIME_DIR=/run/user/$(id -u); systemctl --user daemon-reload && "
         "systemctl --user enable visualizador >/dev/null 2>&1; systemctl --user restart visualizador && sleep 3 && "
         "systemctl --user is-active visualizador", None),
    ]
    for cmd, entrada in passos:
        rc, out, err = ssh(cmd, entrada=entrada)
        if rc != 0:
            print(f"FALHOU: {cmd[:60]}... {err.strip() or out.strip()}")
            return False
    print("serviço:", out.strip())
    return enviar()


def status():
    rc, out, err = ssh(f"cat {REMOTO}/estado.json; echo; export XDG_RUNTIME_DIR=/run/user/$(id -u); "
                       f"systemctl --user is-active visualizador; ls {REMOTO}/PAUSADO 2>/dev/null; tail -5 {REMOTO}/visualizador.log")
    print(out.strip() if rc == 0 else f"x200ma não respondeu: {err.strip()}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    acao = sys.argv[1] if len(sys.argv) > 1 else "status"
    if acao == "enviar":
        sys.exit(0 if enviar() else 1)
    if acao == "instalar":
        sys.exit(0 if instalar() else 1)
    if acao in ("pausar", "retomar"):
        rc, _out, err = ssh(f"touch {REMOTO}/PAUSADO" if acao == "pausar" else f"rm -f {REMOTO}/PAUSADO")
        print(f"{acao}: {'ok' if rc == 0 else err.strip()}")
        sys.exit(rc)
    status()


if __name__ == "__main__":
    main()
