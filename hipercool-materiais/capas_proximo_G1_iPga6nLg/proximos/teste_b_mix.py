# Teste da capa B nova (dona 01/11 23h): pose do banco b_pool MISTURADA com harém + corpo da 3ª ref.
#   python teste_b_mix.py <id> <pose_do_pool> [...]   -> teste_b_mix\<id>_<pose>.png
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import capa_ia_anime as c  # noqa: E402
import capa_longo_v2 as v2  # noqa: E402

AQUI = Path(__file__).parent
OUT = AQUI / "teste_b_mix"
OUT.mkdir(exist_ok=True)


def um(vid, ref, ficha, pose):
    saida = OUT / f"{vid}_{pose}.png"
    v2.pose_b = lambda s, p=pose: p  # força a pose do teste
    prompt = v2.montar_b(ficha, vid)
    refs = [str(v2.POSES_B_POOL / f"{pose}.png"), str(v2.CORPO_REF)]
    r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\flow-imagens\gera_imagem.py", prompt, str(saida),
                        "--ref", str(ref), *refs, "--formato", "16:9", "--quantidade", "1",
                        "--maquinas", "desktop,x200ma,acer,pc2", "--max-contas", "6"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5400,
                       creationflags=0x08000000)
    (OUT / f"{vid}_{pose}.log").write_text(prompt + "\n---\n" + r.stdout[-3000:], encoding="utf-8")
    print(pose, "OK" if saida.exists() else "FALHOU", flush=True)


if __name__ == "__main__":
    vid, poses = sys.argv[1], sys.argv[2:]
    url = f"https://youtu.be/{vid}"
    ref = c._capa_do_parceiro(url)
    ficha = c._ficha_v2(ref, "", "16:9")
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda p: um(vid, ref, ficha, p), poses))

