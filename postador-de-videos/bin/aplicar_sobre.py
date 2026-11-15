"""aplicar_sobre.py — aplica o "Sobre" (config/sobre_canais.json) canal por canal, pelo Studio no Chrome do cofre do
PRÓPRIO canal (youtube_studio_extras --sobre). Um por vez, com pausa de 2-4 min entre eles; já aplicado = pula.
Estado: logs/sobre_aplicado.json. Dona 14/11.
    python bin\\aplicar_sobre.py            # todos que faltam
    python bin\\aplicar_sobre.py <canal>    # só esse
"""
import json
import random
import sys
import tempfile
import time
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import youtube_studio_extras as yse  # noqa: E402

CFG = BIN.parent / "config" / "sobre_canais.json"
EST = BIN.parent / "logs" / "sobre_aplicado.json"


def main(alvos):
    textos = {k: v for k, v in json.loads(CFG.read_text("utf-8")).items() if not k.startswith("_")}
    est = json.loads(EST.read_text("utf-8")) if EST.exists() else {}
    for canal in (alvos or list(textos)):
        if est.get(canal) == "ok" and not alvos:
            continue
        arq = Path(tempfile.gettempdir()) / f"sobre_{canal}.txt"
        arq.write_text(textos[canal], encoding="utf-8")
        r = yse.rodar(canal, timeout=900) if False else None  # (rodar não tem --sobre; chama direto abaixo)
        import subprocess
        p = subprocess.run([sys.executable, str(BIN / "youtube_studio_extras.py"), "--canal", canal, "--sobre", str(arq)],
                           capture_output=True, text=True, timeout=900, encoding="utf-8", errors="replace")
        import re
        m = re.search(r"^RESULTADO: (\{.*\})\s*$", p.stdout or "", re.M)
        res = (json.loads(m.group(1)).get("sobre") if m else (p.stderr or p.stdout or "")[-200:]) or "?"
        est[canal] = res
        EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")
        print(f"{canal}: {res}", flush=True)
        time.sleep(random.randint(120, 240))


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
