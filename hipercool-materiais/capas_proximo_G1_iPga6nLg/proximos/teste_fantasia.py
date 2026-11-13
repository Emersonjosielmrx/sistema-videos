# 02/11 05h30: com a ficha real do Ferreiro (mesmo cabelo + fantasia do MESMO tema da roupa da capa original:
# ferreira/cavaleira/empregada) o Flow desenha a roupa original. V1 = sem o nome do tema; V2 = sem tema e sem os
# acessórios que viram roupa (avental, ombreira, braçadeira, tiara).
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import capa_ia_anime as c  # noqa: E402
import capa_longo_v2 as v2  # noqa: E402

AQUI = Path(__file__).parent
OUT = AQUI / "teste_b_mix"
VID, POSE = "ssMbrCz0fhE", "dona_colo_de_frente"
ROUPA_ACESS = r"apron|pauldron|bracer|wristguard|gauntlet|headband|armor|vest|collar|sleeve|glove"


def sem_tema(f):
    return re.sub(r"^[A-Z][A-Z \-]*BIKINI\s*(for the mascot girl)?\s*:\s*", "", f).strip()


def sem_acess(f):
    partes = [p.strip() for p in sem_tema(f).split(",")]
    return ", ".join([partes[0]] + [p for p in partes[1:] if not re.search(ROUPA_ACESS, p, re.I)])


def gerar(nome, prompt):
    saida = OUT / f"{nome}.png"
    refs = [v2.POSES_B_POOL / f"{POSE}.png", v2.CORPO_REF]
    r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\flow-imagens\gera_imagem.py", prompt, str(saida),
                        "--ref", str(ref), *map(str, refs), "--formato", "16:9", "--quantidade", "1",
                        "--maquinas", "desktop,x200ma,acer,pc2", "--max-contas", "6"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600,
                       creationflags=0x08000000)
    (OUT / f"{nome}.log").write_text(prompt + "\n---\n" + r.stdout[-2500:], encoding="utf-8")
    print(nome, "OK" if saida.exists() else "FALHOU", flush=True)


ref = c._capa_do_parceiro(f"https://youtu.be/{VID}")
ficha = c._ficha_v2(ref, "", "16:9")
v2.pose_b = lambda s: POSE
f1 = dict(ficha, mulheres=[dict(m, fantasia=sem_tema(m["fantasia"])) for m in ficha["mulheres"]],
          maria=sem_tema(ficha["maria"]))
f2 = dict(ficha, mulheres=[dict(m, fantasia=sem_acess(m["fantasia"])) for m in ficha["mulheres"]],
          maria=sem_acess(ficha["maria"]))
print([m["fantasia"] for m in f1["mulheres"]], [m["fantasia"] for m in f2["mulheres"]], flush=True)
with ThreadPoolExecutor(2) as ex:
    list(ex.map(lambda t: gerar(*t), [("V1_sem_tema", v2.montar_b(f1, VID)),
                                      ("V2_sem_tema_sem_acess", v2.montar_b(f2, VID))]))
