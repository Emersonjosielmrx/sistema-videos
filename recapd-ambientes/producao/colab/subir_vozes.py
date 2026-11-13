"""subir_vozes.py — sobe as vozes clonadas do teste de narradores pro cache do Drive (manhwa-drive:colab_recap/vozes/<voz>),
uma de cada vez, separado do alimentador (dona 26/10: "pode usar várias ou todas de uma vez"; são ~10 GB pela internet
de casa, ~8 h). Anota em vozes_no_drive.json cada voz que subiu inteira; o cliente.enviar só manda a rodada do teste
quando TODAS as vozes dela estão lá.

    python subir_vozes.py      # as vozes da "ordem" de teste_narradores.json
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path
import sys as _sys
if _sys.platform == "win32":  # dona 26/10: rclone/ssh/scp/python filhos SEM janela na tela (PC1 e PC2)
    for _p in (r"D:\hipercool-materiais\comum", r"C:\hipercool-materiais\comum"):
        if Path(_p, "sem_janela.py").exists():
            _sys.path.append(_p)
            import sem_janela  # noqa: F401,E402
            break

AQUI = Path(__file__).resolve().parent
RCLONE = r"D:\tools\rclone.exe"
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
FEITAS = AQUI / "vozes_no_drive.json"
TESTE = AQUI / "teste_narradores.json"
LOG = AQUI / "subir_vozes.log"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {msg}\n")


def main():
    feitas = set(json.loads(FEITAS.read_text(encoding="utf-8"))) if FEITAS.exists() else set()
    for v in json.loads(TESTE.read_text(encoding="utf-8")).get("ordem", []):
        if v in feitas or not (VOZES / v / f"{v}.pth").exists():
            continue
        r = subprocess.run([RCLONE, "copy", str(VOZES / v), f"manhwa-drive:colab_recap/vozes/{v}",
                            "--include", "*.{pth,index,txt,json}", "--transfers", "2"], capture_output=True, text=True)
        if r.returncode == 0:
            feitas.add(v)
            FEITAS.write_text(json.dumps(sorted(feitas), ensure_ascii=False), encoding="utf-8")
            log(f"{v} no Drive ({len(feitas)} vozes)")
        else:
            log(f"{v} falhou: {r.stderr.strip()[-200:]}")
    log("fim")


if __name__ == "__main__":
    main()
