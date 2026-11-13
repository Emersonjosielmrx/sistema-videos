# -*- coding: utf-8 -*-
r"""tools/colher_instagram.py — copia para o nsn (cookies/cofre_ig_<conta>.json) o cookie do Instagram de cada conta que
já está LOGADA no Chrome do cofre (perfil ig_<conta>), uma conta por vez, Chrome escondido (dona 29/10: "o Instagram
tem várias contas, todas com cookies"). Não loga, não posta, não lê nada além da home. Depois disso o monitor
(saude.py), o medir_web e o postar por HTTP funcionam sem Chrome até o cookie vencer.

    python tools\colher_instagram.py            # todas as contas do reuso_plataformas (instagram) sem cookie no nsn
    python tools\colher_instagram.py conta1 ...  # só essas
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401
from core.cofre_cookies import ler, pegar  # noqa: E402

REUSO = Path(r"D:\postador-de-videos\config\reuso_plataformas.json")
if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
def main(a):
    contas = a or sorted((json.loads(REUSO.read_text("utf-8")).get("instagram", {}).get("contas") or {}).keys())
    feitas, falhas = [], []
    for conta in contas:
        perfil = f"ig_{conta}"
        d = ler(perfil)
        if d and any(c.get("name") == "sessionid" for c in d.get("cookies", [])) and not a:
            print(f"{conta}: já tem cookie no nsn", flush=True)
            continue
        try:
            t = time.time()
            d = pegar(perfil, "https://www.instagram.com/")
            ok = any(c.get("name") == "sessionid" for c in (d or {}).get("cookies", []))
            print(f"{conta}: {'ok' if ok else 'SEM sessionid (deslogada no cofre)'} em {time.time() - t:.0f} s", flush=True)
            (feitas if ok else falhas).append(conta)
        except Exception as e:  # noqa: BLE001
            print(f"{conta}: falhou ({type(e).__name__}: {str(e)[:100]})", flush=True)
            falhas.append(conta)
        time.sleep(5)
    print(f"\ncolhidas: {len(feitas)} | sem login/falha: {len(falhas)} {falhas}")


if __name__ == "__main__":
    main(sys.argv[1:])
