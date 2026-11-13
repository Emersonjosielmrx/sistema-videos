#!/usr/bin/env bash
# Re-render (12/10) dos Shorts que ficaram com faixa preta embaixo: refaz so o layout (probe com corte ate 45%) e o render.
# Transcricao, editorial (canal/titulos) e ideias vem do cache de work/<slug>/. Um render por vez.
cd /d/manhwa-react || exit 1
export PYTHONUTF8=1
SRC="D:/downloads/7-20261012T124003Z-1-001/7"
for nome in "2026-10-07 12-03-29" "2026-10-07 13-57-58" "2026-10-07 15-48-37" "2026-10-07 15-50-45"; do
    slug=$(echo "$nome" | tr ' -' '__')
    rm -f "work/$slug/layout.json" "work/$slug/hashes.json"
    echo "=== $nome"
    .venv/Scripts/python.exe manhwareact.py process "$SRC/$nome.mp4" 2>&1 | grep -E "layout:|OK parte|ERRO|REPETIDO|Traceback|Error|concluido"
done
