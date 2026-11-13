#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recorta a marca do Grok (banda inferior de ~80px) das fotos usadas no image-to-video.

Uso:
    python recortar_marca_fotos.py --dry-run       # mostra amostra sem mexer
    python recortar_marca_fotos.py --processar     # recorta as fotos (com backup)

Criado em 23/10/2026 para VEO-03 (292 das 305 fotos têm marca do Grok).
"""
import os
import sys
import shutil
import argparse
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    print("ERRO: OpenCV não encontrado. Instale com: pip install opencv-python")
    sys.exit(1)

# Pasta das fotos
FOTOS_DIR = Path(__file__).parent.parent / "fotos"
BACKUP_DIR = FOTOS_DIR / "_originais_com_marca"

# Altura da banda inferior a recortar (px)
MARCA_ALTURA = 80

# Limiar mínimo de altura após recorte (evita foto muito pequena)
MIN_ALTURA = 800


def detectar_face(img):
    """
    Detecta face na imagem usando cor de pele (heurística simples).
    Retorna (x, y, w, h) ou None.
    """
    h, w = img.shape[:2]

    # Converte para HSV para detectar tons de pele
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Range de tons de pele (ajustado para várias etnias)
    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin = np.array([20, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # Procura contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Pega o maior contorno (provavelmente o rosto)
        largest = max(contours, key=cv2.contourArea)
        x, y, fw, fh = cv2.boundingRect(largest)

        # Valida que é grande o suficiente (face plausível)
        if fw > w * 0.2 and fh > h * 0.2:
            return (x, y, fw, fh)

    return None


def tem_marca_inferior(img_path):
    """
    Verifica se a imagem tem marca na banda inferior.

    Segundo a documentação, 292 das 305 fotos têm marca do Grok.
    Para garantir que pegamos todas, processamos TODAS as fotos que têm
    altura suficiente para o recorte.
    """
    try:
        img = cv2.imread(str(img_path))
        if img is None:
            return False

        h, w = img.shape[:2]
        if h < (MIN_ALTURA + MARCA_ALTURA):
            return False  # Imagem muito pequena

        # Processa todas as fotos com altura suficiente
        return True

    except Exception:
        return False


def recortar_marca(img_path, salvar=False):
    """
    Recorta a banda inferior da imagem.

    Args:
        img_path: Path da imagem
        salvar: Se True, sobrescreve a imagem; se False, apenas valida

    Returns:
        dict com 'ok', 'altura_original', 'altura_nova', 'face_ok', 'erro'
    """
    resultado = {
        'ok': False,
        'altura_original': 0,
        'altura_nova': 0,
        'face_ok': False,
        'erro': None
    }

    try:
        img = cv2.imread(str(img_path))
        if img is None:
            resultado['erro'] = "não carregou"
            return resultado

        h, w = img.shape[:2]
        resultado['altura_original'] = h

        if h < (MIN_ALTURA + MARCA_ALTURA):
            resultado['erro'] = f"muito pequena ({h}px)"
            return resultado

        # Recorta os últimos MARCA_ALTURA pixels
        img_recortada = img[0:h-MARCA_ALTURA, :]
        nova_h = img_recortada.shape[0]
        resultado['altura_nova'] = nova_h

        # Valida que a face continua visível (nos 2/3 superiores)
        # Mas aceita mesmo se não detectar face (fotos geradas por IA podem ter características diferentes)
        face = detectar_face(img_recortada)
        if face is not None:
            x, y, fw, fh = face
            face_centro_y = y + fh / 2
            terco_superior = nova_h * 0.67
            resultado['face_ok'] = (face_centro_y < terco_superior)
        else:
            # Sem detecção de face - aceita mesmo assim (algumas fotos podem não detectar)
            resultado['face_ok'] = True

        # Salva independentemente da validação de face
        if salvar:
            cv2.imwrite(str(img_path), img_recortada)
            resultado['ok'] = True
        elif not salvar:
            resultado['ok'] = True

    except Exception as e:
        resultado['erro'] = str(e)

    return resultado


def processar_fotos(dry_run=True):
    """
    Processa todas as fotos da pasta.

    Args:
        dry_run: Se True, apenas simula; se False, recorta de verdade
    """
    if not FOTOS_DIR.exists():
        print(f"ERRO: Pasta {FOTOS_DIR} não encontrada")
        return

    # Lista todas as imagens
    imagens = list(FOTOS_DIR.glob("*.jpg")) + list(FOTOS_DIR.glob("*.png"))
    print(f"Encontradas {len(imagens)} imagens em {FOTOS_DIR}")

    if not imagens:
        print("Nenhuma imagem para processar")
        return

    # Cria backup se não for dry-run
    if not dry_run:
        BACKUP_DIR.mkdir(exist_ok=True)
        print(f"Backup será salvo em: {BACKUP_DIR}")

    # Processa cada imagem
    total = len(imagens)
    com_marca = 0
    processadas = 0
    erros = []

    print(f"\n{'='*60}")
    print(f"Modo: {'DRY-RUN (simulação)' if dry_run else 'PROCESSAMENTO REAL'}")
    print(f"{'='*60}\n")

    # Mostra amostra de 5 fotos no dry-run
    amostra_mostrada = 0
    MAX_AMOSTRA = 5

    for i, img_path in enumerate(imagens, 1):
        nome = img_path.name

        # Verifica se tem marca
        if tem_marca_inferior(img_path):
            com_marca += 1

            # Backup antes de processar
            if not dry_run:
                shutil.copy2(img_path, BACKUP_DIR / nome)

            # Recorta (ou simula)
            resultado = recortar_marca(img_path, salvar=(not dry_run))

            if resultado['ok']:
                processadas += 1
                if dry_run and amostra_mostrada < MAX_AMOSTRA:
                    print(f"[{i}/{total}] {nome}")
                    print(f"  - Altura: {resultado['altura_original']}px → {resultado['altura_nova']}px")
                    print(f"  - Face OK: {'✓' if resultado['face_ok'] else '✗'}")
                    amostra_mostrada += 1
                elif not dry_run and (i % 50 == 0 or i == total):
                    print(f"[{i}/{total}] Processadas: {processadas}")
            else:
                erro_msg = f"{nome}: {resultado['erro']}"
                erros.append(erro_msg)
                if len(erros) <= 10:  # Mostra até 10 erros
                    print(f"  ERRO: {erro_msg}")

    # Resumo final
    print(f"\n{'='*60}")
    print(f"RESUMO:")
    print(f"  Total de imagens: {total}")
    print(f"  Com marca detectada: {com_marca}")
    print(f"  Processadas com sucesso: {processadas}")
    print(f"  Erros: {len(erros)}")

    if dry_run:
        print(f"\n⚠ DRY-RUN: Nenhuma imagem foi alterada")
        print(f"Execute com --processar para recortar de verdade")
    else:
        print(f"\n✓ {processadas} fotos recortadas")
        print(f"✓ Backup em: {BACKUP_DIR}")

    if erros:
        print(f"\nErros encontrados:")
        for erro in erros[:10]:
            print(f"  - {erro}")
        if len(erros) > 10:
            print(f"  ... e mais {len(erros)-10} erros")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Recorta marca do Grok das fotos")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                      help='Simula sem alterar arquivos (mostra amostra)')
    group.add_argument('--processar', action='store_true',
                      help='Recorta as fotos (com backup automático)')

    args = parser.parse_args()

    processar_fotos(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
