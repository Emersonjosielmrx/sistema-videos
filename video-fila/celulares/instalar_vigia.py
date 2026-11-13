r"""instalar_vigia.py — põe o vigia_celular.sh (reabre Tailscale/Termux, segura o wake-lock, sobe o sshd) em cada
celular que responder no ssh (12/11, dona: "A2, A3 e Moto G20 ligados, só garanta o script pra ficar abrindo o
Tailscale e o Termux"). Tarefa InstalarVigiaCelulares de 10 em 10 min: celular que ainda não tem = instala; que já
tem = confere o crond vivo (sobe se caiu). 1 ssh por celular, sem rajada.

    python instalar_vigia.py
"""
import subprocess
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SH = (AQUI / "vigia_celular.sh").read_text(encoding="utf-8").replace("\r\n", "\n")
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe" if Path(r"C:\Program Files\Git\usr\bin\ssh.exe").exists() else "ssh"
LOG = AQUI.parent / "estado" / "instalar_vigia.log"
HOSTS = ("s20", "s20ultra", "a3", "g20", "a2")
REMOTO = (
    "command -v crond >/dev/null || (yes | pkg install -y cronie >/dev/null 2>&1); "
    "cat > ~/vigia_celular.sh && chmod +x ~/vigia_celular.sh && "
    "(crontab -l 2>/dev/null | grep -v vigia_celular; echo '* * * * * ~/vigia_celular.sh') | crontab - && "
    "mkdir -p ~/.termux/boot && "
    "printf '#!/data/data/com.termux/files/usr/bin/sh\\ntermux-wake-lock\\nsshd\\ncrond\\n' > ~/.termux/boot/vigia && "
    "chmod +x ~/.termux/boot/vigia && "
    "(grep -q 'pgrep -x crond' ~/.bashrc 2>/dev/null || echo 'pgrep -x crond >/dev/null || crond' >> ~/.bashrc); "
    "(grep -q 'pgrep -x sshd' ~/.bashrc 2>/dev/null || echo 'pgrep -x sshd >/dev/null || sshd' >> ~/.bashrc); "
    "pgrep -x crond >/dev/null || crond; "
    # 12/11 dona ("abrir os apps quando fechar ou de x em x horas"): job do JobScheduler do ANDROID (acorda mesmo com o
    # Termux fechado) a cada 15 min — sobe crond/sshd e reabre Termux e Tailscale (job_reabrir.sh, enviado à parte)
    "test -x ~/job_reabrir.sh && (termux-job-scheduler -p 2>/dev/null | grep -q job_reabrir || "
    "termux-job-scheduler -s ~/job_reabrir.sh --period-ms 900000 --persisted true --job-id 7 >/dev/null 2>&1); "
    "echo OK_VIGIA crond=$(pgrep -x crond) job=$(termux-job-scheduler -p 2>/dev/null | grep -c job_reabrir)"
)
JOB = (AQUI / "job_reabrir.sh").read_text(encoding="utf-8").replace(chr(13), "")


def main():
    for h in HOSTS:
        try:
            subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=12", h,
                            "cat > ~/job_reabrir.sh && chmod +x ~/job_reabrir.sh"], input=JOB.encode(),
                           capture_output=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=12", h, REMOTO], input=SH.encode(),
                               capture_output=True, timeout=300, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            out = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
            linha = next((l for l in out.splitlines() if "OK_VIGIA" in l), out.strip().splitlines()[-1] if out.strip() else "?")
        except Exception as e:  # noqa: BLE001
            linha = f"{type(e).__name__}"
        msg = f"[{datetime.now():%d/%m %H:%M}] {h}: {linha[:120]}"
        print(msg, flush=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")


if __name__ == "__main__":
    main()
