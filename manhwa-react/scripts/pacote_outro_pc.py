"""Monta o pacote para rodar o manhwa-react em outro PC (onde o dono grava) e sobe para o Google Drive.

Zips com caminho a partir de D:\\ (extraidos em D:\\ recriam tudo no mesmo lugar, sem mexer no config.json):
  manhwa-react.zip  codigo, config, docs, assets, modelos do whisper, canais, bases, caches pequenos do work/
  hub-assets.zip    ffmpeg/ffprobe, sfx, trilhas, memes, sfx_extras, sfx_memes, lista de copyright
  hub-overlays.zip  assets\\overlays\\elemental
  fotos.zip         retratos usados nas capas
  postador.zip      codigo e config do postador (a rede le politica/rede_canais); chega com a POSTAGEM DESLIGADA
  segredos.zip      proxy de IA, chaves Groq e omniroute
Fica de fora: .venv (o INSTALAR.ps1 refaz pelo requirements.txt), output/, video/audio do work/, a fila de postagem e
os logins: postar continua so neste PC ate a virada (ver LEIA-ME-OUTRO-PC.txt).

--etapas (16/10): so a atualizacao "videos dos 2 PCs no mesmo Drive, por etapa" (etapas.zip, sem senha: o outro PC
entra no Drive pelo navegador; ver pacote_outro_pc/LEIA-ME-ETAPAS.txt), para o outro PC que ja tem o pacote completo.

Uso: python scripts/pacote_outro_pc.py [--sem-subir] [--etapas]
"""
import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RCLONE = r"D:\tools\rclone.exe"
DRIVE = "manhwa-drive:pacote-outro-pc"
D = Path("D:\\")
MR = D / "manhwa-react"
HUB = D / "hipercool-materiais"
POSTADOR = D / "postador-de-videos"
TEXTO_WORK = {".json", ".jsonl", ".txt", ".ass", ".md"}
PULAR_DIRS = {".venv", "__pycache__", ".git", "output", "1-COLOQUE-AQUI", "rede_marca"}


def _arquivos(raiz, filtro=lambda f: True):
    for f in sorted(Path(raiz).rglob("*")):
        rel = f.relative_to(raiz).parts
        if f.is_file() and not PULAR_DIRS.intersection(rel) and ".bkp" not in f.name and filtro(f):
            yield f


def _manhwa_react(f):
    if f.name in ("secrets_proxy.json",) or f.suffix == ".pyc":
        return False
    rel = f.relative_to(MR).parts
    return rel[0] != "work" or f.suffix.lower() in TEXTO_WORK  # do work/ so os caches pequenos (editorial, transcricao)


def _postador(f):
    rel = f.relative_to(POSTADOR).parts
    return (rel[0] == "bin" and not rel[1].startswith("_")) or (rel[0] == "config" and f.suffix == ".json") \
        or f.name == "LEIA.txt"


def montar(dest):
    req = MR / "requirements.txt"
    freeze = subprocess.run(["uv", "pip", "freeze", "--python", str(MR / ".venv" / "Scripts" / "python.exe")],
                            capture_output=True, text=True, check=True).stdout
    req.write_text("--extra-index-url https://download.pytorch.org/whl/cpu\n" + freeze, encoding="utf-8")
    grupos = {
        "manhwa-react.zip": list(_arquivos(MR, _manhwa_react)),
        "hub-assets.zip": [f for p in ("bin", "assets/memes_img", "assets/trilhas", "assets/sfx_extras", "assets/sfx",
                                       "assets/sfx_memes") for f in _arquivos(HUB / p)]
                          + [HUB / "assets" / "sfx_memes_categorized.json", HUB / "_curadoria" / "copyright_blocklist.json"],
        "hub-overlays.zip": list(_arquivos(HUB / "assets" / "overlays" / "elemental")),
        "fotos.zip": [f for p in ("Fotos minhas retrato", "fotos retrato novo para videos/epocas")
                      for f in _arquivos(D / "fotos para videos" / "fotos" / p)],
        "postador.zip": list(_arquivos(POSTADOR, _postador)),
        "segredos.zip": [MR / "secrets_proxy.json", POSTADOR / "secrets" / "groq_keys.json",
                         D / "historias-em-frames" / "secrets" / "omniroute.json"],
    }
    dest.mkdir(parents=True, exist_ok=True)
    for nome, arqs in grupos.items():
        with zipfile.ZipFile(dest / nome, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
            for f in arqs:
                z.write(f, f.relative_to(D).as_posix())
            if nome == "manhwa-react.zip":
                z.writestr("manhwa-react/1-COLOQUE-AQUI/", "")
            if nome == "postador.zip":  # nada posta deste PC ate a virada (o historico de uploads esta no PC principal)
                z.writestr("postador-de-videos/config/POSTAGEM_DESLIGADA.json", json.dumps(
                    {"desligada_em": datetime.now().isoformat(timespec="seconds"),
                     "motivo": "pacote do outro PC: a postagem roda so no PC principal ate a virada (LEIA-ME-OUTRO-PC.txt)"},
                    ensure_ascii=False, indent=1))
        print(f"{nome:18} {len(arqs):5} arquivos {(dest / nome).stat().st_size / 1e9:6.2f} GB", flush=True)
    for extra in ("INSTALAR.ps1", "LEIA-ME-OUTRO-PC.txt"):
        shutil.copy2(RAIZ / "scripts" / "pacote_outro_pc" / extra, dest / extra)


ETAPAS = [POSTADOR / "bin" / "etapas.py", POSTADOR / "bin" / "catalogo.py", POSTADOR / "config" / "etapas.json",
          MR / "scripts" / "backup_drive.py", MR / "scripts" / "backup_drive.bat", D / "tools" / "rclone.exe",
          D / "rodar_oculto.vbs"]


def montar_etapas(dest):
    """Atualizacao pequena: so os arquivos das etapas no Drive + o rclone (o login do Drive e feito la)."""
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest / "etapas.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in ETAPAS:
            z.write(f, f.relative_to(D).as_posix())
    for extra in ("INSTALAR-ETAPAS.ps1", "LEIA-ME-ETAPAS.txt"):
        shutil.copy2(RAIZ / "scripts" / "pacote_outro_pc" / extra, dest / extra)
    for f in sorted(dest.iterdir()):
        print(f"{f.name:22} {f.stat().st_size / 1e6:8.1f} MB", flush=True)


def subir(dest):
    alvo = f"{DRIVE}/{dest.name}"
    r = subprocess.run([RCLONE, "copy", str(dest), alvo, "--drive-chunk-size", "64M", "--transfers", "2", "--retries", "5",
                        "--timeout", "120s", "--contimeout", "30s", "--stats", "1m", "--stats-one-line", "-v"])
    if r.returncode:
        sys.exit(f"upload terminou com erro {r.returncode}; rode de novo (o rclone so manda o que falta)")
    if subprocess.run([RCLONE, "check", str(dest), alvo, "--size-only", "--one-way"]).returncode:
        sys.exit("o Drive nao bateu com o pacote local; rode de novo")
    pastas = json.loads(subprocess.run([RCLONE, "lsjson", DRIVE, "--dirs-only"], capture_output=True, text=True).stdout)
    pid = next(p["ID"] for p in pastas if p["Name"] == dest.name)
    print(f"\nNO DRIVE: https://drive.google.com/drive/folders/{pid}  (abre so logado na conta dona do Drive)")
    shutil.rmtree(dest)  # conferido no Drive: a copia local era so para subir


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="pacote do manhwa-react para outro PC, no Google Drive")
    ap.add_argument("--sem-subir", action="store_true", help="so monta os zips em D:\\_pacote_outro_pc")
    ap.add_argument("--etapas", action="store_true", help="so a atualizacao das etapas no Drive (pacote pequeno)")
    args = ap.parse_args()
    dest = D / "_pacote_outro_pc" / (datetime.now().strftime("%Y-%m-%d") + ("-etapas" if args.etapas else ""))
    (montar_etapas if args.etapas else montar)(dest)
    if not args.sem_subir:
        subir(dest)


if __name__ == "__main__":
    main()
