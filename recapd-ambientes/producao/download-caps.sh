#!/usr/bin/env bash
# download-caps.sh — Baixa e corta capítulos novos do tiamanhwa.com
# Uso: ./download-caps.sh 10 20  (baixa caps 10 a 20)
set -uo pipefail

PROJECT="/d/hipercool-inferior"
VENV="/d/hipercool-videos/venv/Scripts/python.exe"
export PYTHONUTF8=1

CAP_START="${1:-10}"
CAP_END="${2:-20}"

echo "=== DOWNLOAD + CORTE CAPS ${CAP_START}-${CAP_END} ==="
echo "Site: tiamanhwa.com/manhwa/the-meek-cat/"

for cap in $(seq $CAP_START $CAP_END); do
    CAP_PADDED=$(printf "%02d" $cap)
    PANELS_DIR="$PROJECT/workspace/panels/the-meek-cat-cap${CAP_PADDED}"

    if [ -d "$PANELS_DIR" ] && [ "$(ls $PANELS_DIR/*.jpg 2>/dev/null | wc -l)" -gt 5 ]; then
        echo "[SKIP] cap${CAP_PADDED} — já tem $(ls $PANELS_DIR/*.jpg | wc -l) painéis"
        continue
    fi

    URL="https://tiamanhwa.com/manhwa/the-meek-cat/capitulo-${cap}/"
    echo "[START] cap${CAP_PADDED} — $URL"

    # Baixar e cortar
    "$VENV" "$PROJECT/bin/hiper-pipeline.py" --url "$URL" --titulo "The Meek Cat - Capitulo ${cap}" --dry-run 2>&1 | tail -5

    # Verificar resultado
    if [ -d "$PANELS_DIR" ]; then
        COUNT=$(ls "$PANELS_DIR"/*.jpg 2>/dev/null | wc -l)
        echo "[DONE] cap${CAP_PADDED} — $COUNT painéis cortados"
    else
        echo "[FAIL] cap${CAP_PADDED} — sem painéis"
    fi
done

echo "=== DOWNLOAD COMPLETO ==="
