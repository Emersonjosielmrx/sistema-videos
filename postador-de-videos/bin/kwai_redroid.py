# -*- coding: utf-8 -*-
r"""kwai_redroid.py — postar no Kwai pelo APP ANDROID rodando no Redroid da VPS hermes-bloqueio (D18 em
D:\hipercool-materiais\tarefas complexas para fable 5.1\FABLE_DECISOES.md). O site do Kwai não tem envio; o app tem.

ANTES DE MUDAR: ler FABLE_DECISOES.md (D18) e D:\postador-de-videos\PLATAFORMAS_NOVAS_PENDENTE.md §1.

Pré-requisitos (uma vez, pela dona, com D:\whatsapp-activator2\vps-redroid\conectar.bat / scrcpy):
  1. instalar o Kwai pela Play Store do Redroid (pacote com.kwai.video);
  2. entrar na conta (Google ou SMS — login é dela).
Depois disso este script faz tudo sozinho, sem janela e sem navegador.

    python bin\kwai_redroid.py --sonda                    # só olha: contêiner, adb, Kwai instalado/logado
    python bin\kwai_redroid.py postar <video.mp4> "legenda"  # publica (exige app logado)

Regras: 1 conta por Redroid; nunca like/view automático; não rodar junto com o manter-vivo.sh do WhatsApp (ele
desliga o contêiner ao terminar); vídeo vertical 9:16 ≤ 3 min.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

SSH_EXE = r"C:\Program Files\Git\usr\bin\ssh.exe" if __import__("os").path.exists(r"C:\Program Files\Git\usr\bin\ssh.exe") else "ssh"  # 29/10 (Fable): sob tarefa agendada o "ssh" do PATH e o OpenSSH do Windows, que trava ate o timeout

sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: F401
except ImportError:
    pass

VPS = "hermes-bloqueio"
KIT = "/opt/vps-redroid"
PACOTE = "com.kwai.video"
if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
def ssh(cmd, timeout=300):
    r = subprocess.run([SSH_EXE, "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=25", VPS, cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


def adb(cmd, timeout=120):
    return ssh(f"adb -s 127.0.0.1:5555 {cmd}", timeout)


def ligar():
    rc, out = ssh(f"cd {KIT} && docker inspect -f '{{{{.State.Running}}}}' redroid 2>/dev/null")
    if "true" not in out:
        print("ligando o Android…", flush=True)
        ssh(f"cd {KIT} && docker compose up -d", 180)
    ssh("adb connect 127.0.0.1:5555", 60)
    for _ in range(60):
        rc, out = adb("shell getprop sys.boot_completed", 30)
        if out.strip().endswith("1"):
            return True
        time.sleep(5)
    return False


def sonda():
    rc, out = ssh("echo ok; docker inspect -f '{{.State.Running}}' redroid 2>/dev/null; free -g | sed -n 2p; df -h / | tail -n1")
    print("VPS:", out.replace("\n", " | ") if rc == 0 else f"sem acesso ({out[:120]})")
    if rc != 0:
        return 2
    if "true" not in out:
        print("Redroid DESLIGADO (o manter-vivo só liga 2×/semana). Para instalar o Kwai: ligar com "
              f"`ssh {VPS} 'cd {KIT} && docker compose up -d'` e abrir o conectar.bat.")
        return 1
    ssh("adb connect 127.0.0.1:5555", 60)
    rc, pk = adb("shell pm list packages", 60)
    tem = PACOTE in pk
    print(f"Kwai instalado: {tem}" + ("" if tem else " → falta instalar pela Play Store (dona)"))
    if tem:
        rc, d = adb(f"shell dumpsys package {PACOTE} | grep -E 'versionName|firstInstallTime'", 60)
        print(" ", d.replace("\n", " | "))
    return 0 if tem else 1


def postar(video, legenda):
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    video = type(video)(_g1080(video)) if not isinstance(video, str) else str(_g1080(video))
    video = Path(video)
    if not video.exists():
        raise SystemExit(f"não existe: {video}")
    if not ligar():
        raise SystemExit("Android não ligou")
    rc, pk = adb("shell pm list packages")
    if PACOTE not in pk:
        raise SystemExit("Kwai não instalado no Redroid (dona: Play Store pelo conectar.bat)")
    remoto = f"/sdcard/Movies/{re.sub(r'[^A-Za-z0-9_.-]', '_', video.name)}"
    subprocess.run(["scp", "-o", "BatchMode=yes", str(video), f"{VPS}:/tmp/kwai_envio.mp4"], check=True, timeout=900)
    adb(f"push /tmp/kwai_envio.mp4 {remoto}", 300)
    adb(f"shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{remoto}")
    adb(f"shell am force-stop {PACOTE}")
    adb(f"shell am start -a android.intent.action.SEND -t video/mp4 --eu android.intent.extra.STREAM file://{remoto} "
        f"--es android.intent.extra.TEXT \"{legenda[:150]}\" -p {PACOTE}")
    time.sleep(12)
    # Toque (com.waa11y) clica por AccessibilityService; o texto do botão varia por idioma do app
    for alvo in ("Publicar", "Postar", "Post", "Próximo", "Avançar"):
        adb(f"shell am startservice -n com.waa11y/.Svc --es acao clicar --es texto {alvo}")
        time.sleep(6)
    rc, tela = adb("exec-out uiautomator dump /dev/tty", 60)
    ok = any(p in tela for p in ("Publicado", "Posted", "Enviando", "Uploading"))
    print("tela confirma publicação:", ok)
    if ok:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import etapas  # noqa: E402
            etapas.registrar(video, "kwai")
        except Exception as e:  # noqa: BLE001
            print("etapas.registrar falhou:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "--sonda":
        sys.exit(sonda())
    if a[0] == "postar" and len(a) >= 2:
        sys.exit(postar(a[1], a[2] if len(a) > 2 else ""))
    print(__doc__)
