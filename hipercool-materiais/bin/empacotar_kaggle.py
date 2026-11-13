"""Zip com o voz.wav de cada narrador que tem material e ainda nao tem modelo, para subir como dataset no Kaggle
(amostras_voz\\kaggle_treino_rvc.ipynb treina tudo o que estiver no dataset). O kaggle_rpa.py usa a funcao empacotar.

Uso: python empacotar_kaggle.py  ->  D:\\hipercool-materiais\\amostras_voz\\vozes_narradores.zip
"""
import zipfile
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
DATASET = RAIZ / "amostras_voz" / "dataset_narradores"
VOZES = RAIZ / "models" / "rvc" / "vozes"
SAIDA = RAIZ / "amostras_voz" / "vozes_narradores.zip"


def esperando_treino():
    """Material completo (metadata.csv so existe depois do voz.wav final) e sem modelo."""
    return sorted(d.name for d in DATASET.iterdir()
                  if (d / "metadata.csv").exists() and (d / "voz.wav").exists()
                  and not (VOZES / d.name / f"{d.name}.pth").exists())


def empacotar(vozes):
    with zipfile.ZipFile(SAIDA, "w", zipfile.ZIP_STORED) as zf:
        for voz in vozes:
            zf.write(DATASET / voz / "voz.wav", f"{voz}/voz.wav")
    return SAIDA


if __name__ == "__main__":
    vozes = esperando_treino()
    if not vozes:
        raise SystemExit("nenhuma voz com material esperando treino")
    empacotar(vozes)
    print(f"{SAIDA} ({SAIDA.stat().st_size / 1e6:.0f} MB): {', '.join(vozes)}")
