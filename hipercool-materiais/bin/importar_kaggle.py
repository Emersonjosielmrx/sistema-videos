"""Poe os modelos treinados no Kaggle (modelos_rvc.zip) em models\\rvc\\vozes e inicia a fila, que gera as amostras.

Uso: python importar_kaggle.py <modelos_rvc.zip>

O f0.txt (tom medio do narrador) e calculado aqui, com o venv_vozes, a partir do voz.wav do dataset: no kernel do
Kaggle o librosa quebra (numpy trocado pelo %pip) e o lote de 18/10 perdeu os .pth assim.
O .pth entra por ultimo: e ele que marca "modelo pronto" para a fila e o vigia.
"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
VOZES = RAIZ / "models" / "rvc" / "vozes"
DATASET = RAIZ / "amostras_voz" / "dataset_narradores"
PY_VOZES = RAIZ / "python" / "venv_vozes" / "Scripts" / "python.exe"


def tom_medio(voz):
    codigo = (f"import sys; sys.path.insert(0, {str(RAIZ / 'bin')!r}); import voz_clonada; "
              f"print(voz_clonada.tom_medio({str(DATASET / voz / 'voz.wav')!r}))")
    r = subprocess.run([str(PY_VOZES), "-c", codigo], capture_output=True, text=True, check=True)
    return float(r.stdout.strip().splitlines()[-1])


with zipfile.ZipFile(sys.argv[1]) as zf:
    arquivos = []
    for info in zf.infolist():
        partes = Path(info.filename).parts
        if not info.is_dir() and len(partes) == 3 and partes[0] == "vozes":
            arquivos.append((info, VOZES / partes[1] / partes[2]))
    arquivos.sort(key=lambda a: a[1].suffix == ".pth")
    for info, destino in arquivos:
        destino.parent.mkdir(parents=True, exist_ok=True)
        if destino.suffix == ".pth" and not (destino.parent / "f0.txt").exists():
            voz = destino.parent.name
            try:
                (destino.parent / "f0.txt").write_text(f"{tom_medio(voz):.1f}\n", encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                print(f"{voz}: f0 FALHOU, modelo nao importado: {e}")
                continue
        with zf.open(info) as src, open(destino, "wb") as dst:
            shutil.copyfileobj(src, dst)

for d in sorted(VOZES.iterdir()):
    completo = all((d / n).exists() for n in (f"{d.name}.pth", f"{d.name}.index", "f0.txt"))
    print(f"{d.name}: {'ok' if completo else 'INCOMPLETO'}")

# se a fila ja estiver rodando a tarefa nao abre outra; quando ela terminar, o vigia relanca (modelo sem amostra)
subprocess.run(["powershell", "-NoProfile", "-Command", "Start-ScheduledTask VozClonadaFila"], check=True)
print("fila iniciada: gera as amostras de quem tem modelo")
