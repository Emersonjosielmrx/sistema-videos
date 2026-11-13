# 02/11 04h50: por que a B do Ferreiro sai VESTIDA hoje e a da tarde de 01/11 saía de biquíni?
#   1) prompt da TARDE igual (gerar_todos.montar B) com as referências de hoje
#   2) prompt de AGORA (capa_longo_v2.montar_b) com as MULHERES da tarde (escritas à mão, fora da capa original)
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import capa_longo_v2 as v2  # noqa: E402
import gerar_todos as gt  # noqa: E402

AQUI = Path(__file__).parent
OUT = AQUI / "teste_b_mix"
VID = "ssMbrCz0fhE"
PARC = AQUI / f"parceiro_{VID}.jpg"
POSE = "dona_colo_de_frente"


def gerar(nome, prompt, refs):
    saida = OUT / f"{nome}.png"
    r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\flow-imagens\gera_imagem.py", prompt, str(saida),
                        "--ref", str(PARC), *map(str, refs), "--formato", "16:9", "--quantidade", "1",
                        "--maquinas", "desktop,x200ma,acer,pc2", "--max-contas", "6"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600,
                       creationflags=0x08000000)
    (OUT / f"{nome}.log").write_text(prompt + "\n---\n" + r.stdout[-2500:], encoding="utf-8")
    print(nome, "OK" if saida.exists() else "FALHOU", flush=True)


tarde = gt.montar(VID, "B")
ficha = {"heroi": gt.OBRAS[VID]["heroi"].replace("Keep the SAME main character as the FIRST reference: ", ""),
         "mulheres": [{"quem": q, "fantasia": f} for q, f in gt.OBRAS[VID]["mulheres"][:-1]],
         "maria": gt.OBRAS[VID]["mulheres"][-1][1],
         "cenas": {k: f"x: {v}" for k, v in gt.OBRAS[VID]["cenas"].items()}}
v2.pose_b = lambda s: POSE
agora_mulheres_tarde = v2.montar_b(ficha, VID)
with ThreadPoolExecutor(2) as ex:
    list(ex.map(lambda t: gerar(*t), [
        ("X1_prompt_tarde", tarde, [v2.POSES_DIR / f"{gt.pose_de(VID, 'B')}.png", v2.CORPO_REF]),
        ("X2_agora_mulheres_tarde", agora_mulheres_tarde, [v2.POSES_B_POOL / f"{POSE}.png", v2.CORPO_REF]),
    ]))
