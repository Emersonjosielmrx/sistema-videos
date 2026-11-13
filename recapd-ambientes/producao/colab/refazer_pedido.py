"""29/10 (dona: "então faça" — refazer o Simples Pastor com as correções): copia um pedido da fila pra um id NOVO que
fica em 1º na ordem (o trabalhador pega o 1º livre por nome), com os narradores escolhidos pelos GRUPOS de agora
(cliente._narradores_por_grupo), dentro do Drive (sem subir o vídeo de novo). O pedido antigo sai da fila.
    python refazer_pedido.py <pid_antigo> <pid_novo>"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cliente  # noqa: E402

RC = r"D:\tools\rclone.exe"
FILA, SRC = cliente.FILA, cliente.FILA_SRC
antigo, novo = sys.argv[1], sys.argv[2]


def rc(*a, entrada=None):
    r = subprocess.run([RC, *a], input=entrada, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit(f"rclone {a[0]} falhou: {r.stderr[-300:]}")
    return r.stdout


pedido = json.loads(rc("cat", f"{FILA}/{antigo}/pedido.json"))
t, vozes = cliente._teste_narradores()
pedido.update(vozes_lista=vozes, voz_clonada=vozes[0], refeito_de=antigo,
              teste_narradores=f"vídeo {len(t.get('videos', [])) + 1} do revezamento (grupos 29/10)")
rc("copyto", f"{SRC}/{antigo}/source.mp4", f"{SRC}/{novo}/source.mp4")
for nome in ("intro_cortada.json",):
    if nome in rc("lsf", f"{FILA}/{antigo}"):
        rc("copyto", f"{FILA}/{antigo}/{nome}", f"{FILA}/{novo}/{nome}")
rc("rcat", f"{FILA}/{novo}/pedido.json", entrada=json.dumps(pedido, ensure_ascii=False))
t.setdefault("videos", []).append({"pid": novo, "vozes": vozes})
cliente.TESTE_NARRADORES.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
rc("purge", f"{FILA}/{antigo}")
rc("purge", f"{SRC}/{antigo}")
print("novo pedido:", novo, "| narradores:", ", ".join(vozes))
