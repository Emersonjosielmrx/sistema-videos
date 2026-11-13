#!/usr/bin/env bash
# run-gemini-v1.sh — Gera versões Gemini (vozes masculinas Gemini TTS) dos 9 capítulos.
# Roda devagar, conforme quota permite. Se esgota, espera 10 min e retenta.
# Usa FORCE_TTS_MALE=1 pra pular cache masculino e forçar Gemini.
# Femininas vêm do cache (edge-tts, já gerado no V1).
set -uo pipefail

PROJECT="/d/hipercool-inferior"
VENV="/d/hipercool-videos/venv/Scripts/python.exe"
TIMING_LOG="$PROJECT/gemini_timing.log"

export PYTHONUTF8=1
export PYTHONUNBUFFERED=1
export GEMINI_TTS_PROXY_ENABLED=1
export FORCE_TTS_MALE=1
export TTS_ENGINE=gemini

CAPS=(01 02 03 04 05 06 07 08 09)

echo "=== Gemini V1 Generation — $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$TIMING_LOG"

for cap in "${CAPS[@]}"; do
    PANELS="$PROJECT/workspace/panels/the-meek-cat-cap${cap}"
    DEST="$PROJECT/workspace/videos/the-meek-cat/cap${cap}/gemini/normal"

    if [ ! -d "$PANELS" ]; then
        echo "[SKIP] cap${cap} — sem painéis" >> "$TIMING_LOG"
        continue
    fi

    # Pular se já existe v1 gemini
    if [ -f "$DEST/v1.mp4" ]; then
        echo "[SKIP] cap${cap} — v1 gemini já existe" >> "$TIMING_LOG"
        continue
    fi

    LOGFILE="$PROJECT/cap${cap}_gemini.log"
    echo "[START] cap${cap} — $(date '+%H:%M:%S')" >> "$TIMING_LOG"
    START_S=$(date +%s)

    # Tenta rodar. Se falhar por quota, vai pro próximo (o pipeline é resiliente)
    "$VENV" "$PROJECT/bin/hiper-pipeline.py" \
        --panels-dir "$PANELS" \
        --titulo "The Meek Cat - Capitulo ${cap}" \
        --max-panels 120 \
        --subtitles --karaoke --skip-notify \
        --output-suffix _NORMAL \
        > "$LOGFILE" 2>&1 || true

    END_S=$(date +%s)
    ELAPSED=$(( END_S - START_S ))
    MINS=$(( ELAPSED / 60 ))

    # Verificar resultado
    if [ -f "$DEST/v1.mp4" ]; then
        SIZE=$(du -h "$DEST/v1.mp4" | cut -f1)
        echo "[DONE] cap${cap} — ${MINS}m — OK (${SIZE})" >> "$TIMING_LOG"
    else
        echo "[FAIL] cap${cap} — ${MINS}m — sem video gerado (quota?)" >> "$TIMING_LOG"
        # Se falhou, provavelmente quota esgotou. Espera 10 min antes do próximo.
        echo "[WAIT] esperando 10 min pra quota respirar..." >> "$TIMING_LOG"
        sleep 600
    fi

    # Cooldown entre capítulos (2 min pra quota respirar)
    sleep 120
done

echo "=== Gemini V1 Fim — $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$TIMING_LOG"
