# 01/11 dona: as 7 capas (A-G) dos 8 vídeos pelo modelo de imagem do Google (Antigravity/OmniRoute). Ele NÃO recebe
# imagem de referência: serve quando o protagonista pode ser genérico, pros testes D/E/F/G e pra comparar as A/B/C com
# as do Flow (gerar_todos.py). Saída: brutas_google\<obra>\<letra>.png (reprovadas da dona em <obra>\reprovadas\).
# Conta por conta: D:\flow-imagens\google_imagem.py (esgotou = espera a volta e o vigia testa). Nenhuma conta com
# cota ou o Google não entregou = o Flow faz a mesma capa (dona 01/11), mesmo nome; quem gerou fica no gerador.log.
# Roda: python gerar_google.py [id ...]
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.append(r"D:\flow-imagens")
import google_imagem  # noqa: E402
from gerar_todos import NOMES, TODOS, pasta, proibido, registrar  # noqa: E402

AQUI = Path(__file__).parent
OUT = AQUI / "brutas_google"
OUT.mkdir(exist_ok=True)


def sem_ref(p):
    """Os prompts do Flow citam a capa do parceiro como 1ª referência; aqui não há referência."""
    import re
    p = re.sub(r"Use the FIRST reference only for .*?nothing else\.", "", p)
    p = p.replace(" - the SAME body proportions as the woman in the THIRD reference", "")
    p = p.replace("like the woman in the THIRD reference", "")
    return (p.replace("Recreate and IMPROVE the FIRST reference (a YouTube manhwa thumbnail) as a brand-new", "A brand-new")
             .replace("Keep the SAME main character as the FIRST reference:", "The main character:"))


def flow(vid, letra, prompt, saida, motivo):
    try:
        subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\flow-imagens\gera_imagem.py", prompt, str(saida),
                        "--ref", str(AQUI / f"parceiro_{vid}.jpg"), "--formato", "16:9", "--quantidade", "1",
                        "--maquinas", "pc1,desktop,x200ma,acer", "--max-contas", "6"],
                       capture_output=True, timeout=1800, creationflags=0x08000000)
    except subprocess.TimeoutExpired:
        return f"{NOMES[vid]} {letra}: Google falhou ({motivo}) e o Flow passou de 30 min"
    if not saida.exists():
        return f"{NOMES[vid]} {letra}: Google falhou ({motivo}) e o Flow também"
    registrar(OUT, vid, letra, "flow", prompt)
    with open(OUT / "gerador.log", "a", encoding="utf-8") as f:
        f.write(f"{saida.parent.name}\\{saida.name}\tFLOW (Google: {motivo})\n")
    return f"{NOMES[vid]} {letra}: OK pelo Flow (Google: {motivo})"


def um(vid, letra, prompt):
    saida = pasta(OUT, vid) / f"{letra}.png"
    if saida.exists():
        return f"{NOMES[vid]} {letra} já existe"
    if proibido(OUT, vid, letra, sem_ref(prompt)) or proibido(OUT, vid, letra, prompt):
        return f"{NOMES[vid]} {letra}: prompt já reprovado, não gero de novo"
    ok, det = google_imagem.gerar(sem_ref(prompt), saida)
    if ok:
        registrar(OUT, vid, letra, "google", sem_ref(prompt))
        return f"{NOMES[vid]} {letra}: OK ({det})"
    return flow(vid, letra, prompt, saida, det[:60])


if __name__ == "__main__":
    ids = sys.argv[1:] or list(TODOS)
    tarefas = [(v, l, p) for v in ids for l, p in TODOS[v].items()]
    with ThreadPoolExecutor(3) as ex:
        for r in ex.map(lambda t: um(*t), tarefas):
            print(r, flush=True)
