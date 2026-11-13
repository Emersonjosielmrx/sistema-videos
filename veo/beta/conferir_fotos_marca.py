#!/usr/bin/env python3
"""conferir_fotos_marca.py - Detecta e move fotos com marca d'agua do Grok/Veo.

O problema (24/10/2026): 298 das 305 fotos em D:\\veo\\fotos\\ tem marca do Grok, desperdicando
63% dos videos gerados (rejeitados pelo limpar_veo.py por marca). Este script:
1. Varre as fotos com o mesmo detector de marca do limpar_veo.py (visao via gateway)
2. Separa: fotos_com_marca.txt e fotos_limpas.txt
3. --mover: move as marcadas para D:\\veo\\fotos_MARCADAS_GROK\\ (quarentena, nao apaga)

Uso (venv do veo): python conferir_fotos_marca.py [--listar|--mover] [--max N]
"""
import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FOTOS = Path(r"D:\veo\fotos")
QUARENTENA = Path(r"D:\veo\fotos_MARCADAS_GROK")
GATEWAY = Path(r"D:\veo\beta\secrets\gateway.json")
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"

_PERG_MARCA = ("Esta imagem e uma foto. Existe nela uma MARCA D'AGUA de texto ou logo de ferramenta de IA, "
               "como 'Grok', 'Veo', 'Sora', 'Midjourney', 'DALL-E' ou outra, em qualquer parte da imagem? "
               'Responda SO com JSON: {"marca": "<nome da marca ou nenhuma>"}')


def marca_ia_foto(foto_path):
    """Nome da marca d'agua de IA na foto ("Grok", "Veo"...) ou None. Usa o mesmo metodo do limpar_veo.py
    (visao via gateway). Levanta se o gateway falhar."""
    gw = json.loads(GATEWAY.read_text(encoding="utf-8"))
    url = gw.get("gateway_url", "http://157.173.207.22:20128").rstrip("/") + "/v1/chat/completions"

    # Le a foto e converte para JPEG se necessario (gateway aceita JPEG)
    ext = foto_path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        img_bytes = foto_path.read_bytes()
    else:
        # Converte PNG/outro para JPEG via ffmpeg
        img_bytes = subprocess.run(
            [FFMPEG, "-v", "error", "-i", str(foto_path), "-f", "image2", "-vcodec", "mjpeg", "-"],
            capture_output=True, creationflags=_SEM_JANELA
        ).stdout

    corpo = {
        "model": "antigravity/gemini-3-flash",
        "max_tokens": 40,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": _PERG_MARCA},
                {"type": "image_url", "image_url": {
                    "url": "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode()
                }}
            ]
        }]
    }

    import urllib.request
    req = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode(),
        headers={
            "Authorization": "Bearer " + gw["gateway_key"],
            "Content-Type": "application/json"
        }
    )
    txt = json.loads(urllib.request.urlopen(req, timeout=60).read())["choices"][0]["message"]["content"]
    achou = re.search(r'"marca"\s*:\s*"([^"]*)"', txt)
    nome = (achou.group(1) if achou else txt).strip()

    if nome and not re.fullmatch(r"(?i)nenhuma|none|nao|não|-", nome):
        return nome
    return None


def listar(max_fotos=0):
    """Varre as fotos e gera fotos_com_marca.txt e fotos_limpas.txt."""
    fotos = sorted(FOTOS.glob("*.jpg")) + sorted(FOTOS.glob("*.jpeg")) + sorted(FOTOS.glob("*.png"))
    print(f"Varrendo {len(fotos)} fotos em {FOTOS}")

    com_marca = []
    limpas = []
    erros = []

    for i, foto in enumerate(fotos, 1):
        if max_fotos and i > max_fotos:
            break

        try:
            marca = marca_ia_foto(foto)
            if marca:
                com_marca.append((foto.name, marca))
                print(f"  [{i}/{len(fotos)}] {foto.name}: MARCA '{marca}'")
            else:
                limpas.append(foto.name)
                print(f"  [{i}/{len(fotos)}] {foto.name}: limpa")
        except Exception as ex:
            erros.append((foto.name, str(ex)[:80]))
            print(f"  [{i}/{len(fotos)}] {foto.name}: ERRO ({str(ex)[:60]})")

    # Grava listas
    FOTOS.parent.joinpath("fotos_com_marca.txt").write_text(
        "\n".join(f"{nome}\t{marca}" for nome, marca in com_marca),
        "utf-8"
    )
    FOTOS.parent.joinpath("fotos_limpas.txt").write_text("\n".join(limpas), "utf-8")
    if erros:
        FOTOS.parent.joinpath("fotos_erro_deteccao.txt").write_text(
            "\n".join(f"{nome}\t{erro}" for nome, erro in erros),
            "utf-8"
        )

    print(f"\nResultado:")
    print(f"  Com marca: {len(com_marca)} ({len(com_marca)*100//len(fotos) if fotos else 0}%)")
    print(f"  Limpas: {len(limpas)} ({len(limpas)*100//len(fotos) if fotos else 0}%)")
    print(f"  Erros: {len(erros)}")
    print(f"\nArquivos gerados:")
    print(f"  {FOTOS.parent / 'fotos_com_marca.txt'}")
    print(f"  {FOTOS.parent / 'fotos_limpas.txt'}")
    if erros:
        print(f"  {FOTOS.parent / 'fotos_erro_deteccao.txt'}")


def mover():
    """Move as fotos com marca (de fotos_com_marca.txt) para quarentena."""
    lista = FOTOS.parent / "fotos_com_marca.txt"
    if not lista.exists():
        print(f"ERRO: {lista} nao existe. Rode primeiro: python conferir_fotos_marca.py --listar")
        return

    linhas = lista.read_text("utf-8").strip().split("\n")
    fotos_marcadas = [linha.split("\t")[0] for linha in linhas if linha.strip()]

    if not fotos_marcadas:
        print("Nenhuma foto marcada para mover.")
        return

    QUARENTENA.mkdir(parents=True, exist_ok=True)
    movidas = 0

    for nome in fotos_marcadas:
        src = FOTOS / nome
        if not src.exists():
            print(f"  AVISO: {nome} nao existe mais em {FOTOS}")
            continue

        dst = QUARENTENA / nome
        if dst.exists():
            print(f"  AVISO: {nome} ja existe em quarentena, pulando")
            continue

        shutil.move(str(src), str(dst))
        movidas += 1
        print(f"  Movida: {nome}")

    print(f"\nMovidas {movidas} fotos para {QUARENTENA}")
    print(f"Restaram em {FOTOS}: {len(list(FOTOS.glob('*.jpg')) + list(FOTOS.glob('*.jpeg')) + list(FOTOS.glob('*.png')))} fotos")


def mover_rapido():
    """Move fotos 'image*.jpg' (antigas, com marca do Grok) para quarentena. Baseado na evidencia:
    86% dos temas geraram videos com marca, e essas 278 fotos antigas (vs 18 novas com GUID) sao a fonte."""
    fotos_antigas = sorted(FOTOS.glob("image*.jpg")) + sorted(FOTOS.glob("image*.jpeg")) + sorted(FOTOS.glob("image*.png"))

    if not fotos_antigas:
        print("Nenhuma foto 'image*' encontrada.")
        return

    print(f"Movendo {len(fotos_antigas)} fotos 'image*' para quarentena...")
    QUARENTENA.mkdir(parents=True, exist_ok=True)
    movidas = 0

    for src in fotos_antigas:
        dst = QUARENTENA / src.name
        if dst.exists():
            print(f"  AVISO: {src.name} ja existe em quarentena, pulando")
            continue

        shutil.move(str(src), str(dst))
        movidas += 1
        if movidas <= 10 or movidas % 50 == 0:
            print(f"  [{movidas}/{len(fotos_antigas)}] Movida: {src.name}")

    restantes = len(list(FOTOS.glob('*.jpg')) + list(FOTOS.glob('*.jpeg')) + list(FOTOS.glob('*.png')))
    print(f"\nMovidas {movidas} fotos para {QUARENTENA}")
    print(f"Restaram em {FOTOS}: {restantes} fotos")

    # Gera lista do que foi movido
    lista_movidas = FOTOS.parent / "fotos_movidas_quarentena.txt"
    lista_movidas.write_text("\n".join(p.name for p in sorted(QUARENTENA.glob("*"))), "utf-8")
    print(f"Lista das fotos em quarentena: {lista_movidas}")


def main():
    ap = argparse.ArgumentParser(description="Detecta e move fotos com marca d'agua do Grok/Veo")
    ap.add_argument("--listar", action="store_true", help="varre fotos e gera listas")
    ap.add_argument("--mover", action="store_true", help="move fotos marcadas para quarentena")
    ap.add_argument("--mover-rapido", action="store_true", help="move fotos 'image*' (antigas) para quarentena")
    ap.add_argument("--max", type=int, default=0, help="limita numero de fotos a processar (teste)")
    a = ap.parse_args()

    if a.mover_rapido:
        mover_rapido()
    elif a.mover:
        mover()
    elif a.listar:
        listar(a.max)
    else:
        print("Uso: python conferir_fotos_marca.py [--listar|--mover|--mover-rapido] [--max N]")
        print("  --listar: varre fotos e gera fotos_com_marca.txt e fotos_limpas.txt")
        print("  --mover: move fotos marcadas para D:\\veo\\fotos_MARCADAS_GROK\\")
        print("  --mover-rapido: move fotos 'image*' (antigas, com marca) para quarentena")


if __name__ == "__main__":
    main()
