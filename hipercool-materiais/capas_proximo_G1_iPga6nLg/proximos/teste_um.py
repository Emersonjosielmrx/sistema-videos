# Teste rápido de prompt: python teste_um.py <id> <letra> [flow] -> teste\<id>_<letra>_<gerador>.png
import subprocess
import sys
from pathlib import Path

sys.path.append(r"D:\flow-imagens")
import google_imagem  # noqa: E402
from gerar_google import sem_ref  # noqa: E402
from gerar_todos import AQUI, CORPO_REF, POSES_DIR, TODOS, pose_de  # noqa: E402

vid, letra = sys.argv[1], sys.argv[2]
flow = "flow" in sys.argv[3:]
saida = AQUI / "teste" / f"{vid}_{letra}_{'flow' if flow else 'google'}.png"
saida.parent.mkdir(exist_ok=True)
if flow:
    r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\flow-imagens\gera_imagem.py", TODOS[vid][letra], str(saida),
                        "--ref", str(AQUI / f"parceiro_{vid}.jpg"), str(POSES_DIR / f"{pose_de(vid, letra)}.png"),
                        str(CORPO_REF), "--formato", "16:9", "--quantidade", "1", "--maquinas", "pc1,desktop,x200ma,acer",
                        "--max-contas", "6"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=1800, creationflags=0x08000000)
    print(saida.exists(), r.stdout[-300:])
else:
    print(google_imagem.gerar(sem_ref(TODOS[vid][letra]), saida))
