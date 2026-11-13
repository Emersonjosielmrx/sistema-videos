# -*- coding: utf-8 -*-
"""Prova D30 no desktop, TODA local (dona 29/10: "uma conexão copia tudo, a segunda só executa, depois eu vejo"):
abre o Chrome do perfil pelo chrome_conta.py daqui, gera 1 imagem do Flow por HTTP (worker) com --fechar-chrome,
fecha o que sobrar e grava tudo em C:\\postador-worker\\nsn\\saida\\prova_desktop.log. Roda com o python do venv do nsn."""
import subprocess
import sys
import time
from pathlib import Path

NSN = Path(r"C:\postador-worker\nsn")
CC = Path(r"C:\postador-worker\chrome_conta.py")
PY = sys.executable
PERFIL, PORTA = "emersonjosiel2032", "9460"
PROJETO = "https://flow.google.com/project/e5b76757-030f-4018-b83e-5cdd906eb42e"
LOG = NSN / "saida" / "prova_desktop.log"
SAIDA = NSN / "saida" / "prova_img_desktop.png"
PROMPT = NSN / "saida" / "prova_prompt.txt"


def log(m):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {m}\n")


def run(args, timeout):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    log(f"inicio python={PY}")
    t0 = time.time()
    rc, out = run([PY, str(CC), "abrir", PERFIL, PORTA, "about:blank", "--sem-espera"], 300)
    log(f"abrir rc={rc}: {out[-300:]}")
    if "PRONTO" not in out:
        log("FIM: Chrome não abriu")
        return 2
    t_chrome = time.time()
    try:
        rc, out = run([PY, "-X", "utf8", str(NSN / "services" / "veo_flow" / "flow_gerar.py"), "--porta", PORTA,
                       "--projeto", PROJETO, "--nome", PERFIL, "--fechar-chrome", "imagem", "@" + str(PROMPT),
                       str(SAIDA), "--formato", "9:16", "--modelo", "Nano Banana 2.1"], 900)
        log(f"flow_gerar rc={rc}:\n{out[-1500:]}")
    finally:
        rc2, out2 = run([PY, str(CC), "fechar", PORTA], 120)
        log(f"fechar rc={rc2}: {out2[-200:]}")
    tam = SAIDA.stat().st_size if SAIDA.exists() else 0
    log(f"FIM: png={tam} bytes, chrome_aberto_desde_pronto≈{round(time.time() - t_chrome)} s, total={round(time.time() - t0)} s")
    return 0 if tam > 5000 else 1


if __name__ == "__main__":
    sys.exit(main())
