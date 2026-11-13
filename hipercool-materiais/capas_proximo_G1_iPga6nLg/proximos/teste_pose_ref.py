# Ideia da dona 01/11: Flow com a capa do parceiro (personagens) + capa do hipercool (pose) e SEM descrever a pose -
# o Flow copia a pose que já existe. python teste_pose_ref.py <id> <pose> [<pose>...]  -> teste_pose\<id>_<pose>.png
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from gerar_todos import OBRAS, ROUPA, SEGURO, FIM, MAQ, AQUI

POSES_B = Path(r"D:\hipercool-materiais\capas_poses_ref\b")
POSES_A = Path(r"D:\hipercool-materiais\capas_poses_ref")
OUT = AQUI / "teste_pose"
OUT.mkdir(exist_ok=True)


def roupa(q, f):
    return (f"{q}, wearing ONLY a tiny triangle bikini top and a tiny string bikini bottom - {f} - the theme is ONLY "
            f"the fabric pattern and small accessories; belly, waist, hips and thighs bare (NO skirt, NO shirt)")


def prompt(vid):
    o = OBRAS[vid]
    q, f = o["mulheres"][0]
    lugar = o["cenas"]["B"].split(":", 1)[-1]
    return (
        "Redraw the SECOND reference image as a brand-new 16:9 anime thumbnail with EXACTLY the same pose, body "
        "positions, camera angle, close framing and composition - the same two people doing exactly the same thing, "
        "same sizes in the frame. Only swap who they are: the man becomes the hero of the FIRST reference. "
        f"{o['heroi']} The woman becomes {roupa(q, f)}. Her body stays exactly as voluptuous as the woman in the "
        "SECOND reference (same very large breasts, same wide hips). Do NOT copy the SECOND reference's clothes, "
        f"text or background. Background: {lugar} {ROUPA} {SEGURO} {FIM}")


def pose_arq(nome):
    for d in (POSES_B, POSES_A):
        if (d / f"{nome}.png").exists():
            return d / f"{nome}.png"
    raise SystemExit(f"pose não existe: {nome}")


def um(vid, pose):
    saida = OUT / f"{vid}_{pose}.png"
    p = prompt(vid)
    r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\flow-imagens\gera_imagem.py", p, str(saida),
                        "--ref", str(AQUI / f"parceiro_{vid}.jpg"), str(pose_arq(pose)), "--formato", "16:9",
                        "--quantidade", "1", "--maquinas", MAQ, "--max-contas", "6"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5400,
                       creationflags=0x08000000)
    (OUT / f"{vid}_{pose}.log").write_text(p + "\n---\n" + r.stdout[-3000:] + "\n---\n" + r.stderr[-3000:],
                                          encoding="utf-8")
    print(pose, "OK" if saida.exists() else "FALHOU", flush=True)


if __name__ == "__main__":
    vid, poses = sys.argv[1], sys.argv[2:]
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(lambda p: um(vid, p), poses))

