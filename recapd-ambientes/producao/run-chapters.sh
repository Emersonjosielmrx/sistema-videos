#!/usr/bin/env bash
# run-chapters.sh — Roda capítulos sequencialmente no hipercool-inferior.
# Mede o tempo de cada e salva num log de timing.
# Uso: ./run-chapters.sh [cap_inicio] [cap_fim]
#   ex: ./run-chapters.sh 01 09
set -euo pipefail

PROJECT="/d/hipercool-inferior"
VENV="/d/hipercool-videos/venv/Scripts/python.exe"
TIMING_LOG="$PROJECT/timing.log"
export PYTHONUTF8=1
export GEMINI_TTS_PROXY_ENABLED=1

CAP_START="${1:-01}"
CAP_END="${2:-09}"

CAPS=(01 05 06 07 08 09)

echo "=== Hipercool Inferior — Batch Run ===" >> "$TIMING_LOG"
echo "Inicio: $(date '+%Y-%m-%d %H:%M:%S')" >> "$TIMING_LOG"

for cap in "${CAPS[@]}"; do
    # Pular caps fora do range
    if [[ "$cap" < "$CAP_START" || "$cap" > "$CAP_END" ]]; then
        continue
    fi

    PANELS="$PROJECT/workspace/panels/the-meek-cat-cap${cap}"
    if [ ! -d "$PANELS" ]; then
        echo "[SKIP] cap${cap} — sem painéis" >> "$TIMING_LOG"
        continue
    fi

    LOGFILE="$PROJECT/cap${cap}_run.log"
    echo "[START] cap${cap} — $(date '+%H:%M:%S')" >> "$TIMING_LOG"
    START_S=$(date +%s)

    "$VENV" "$PROJECT/bin/hiper-pipeline.py" \
        --panels-dir "$PANELS" \
        --titulo "The Meek Cat — Capítulo ${cap}" \
        --max-panels 120 \
        --subtitles --karaoke --skip-notify \
        --output-suffix _NORMAL \
        > "$LOGFILE" 2>&1 || true

    END_S=$(date +%s)
    ELAPSED=$(( END_S - START_S ))
    MINS=$(( ELAPSED / 60 ))
    SECS=$(( ELAPSED % 60 ))

    # Verificar se gerou vídeo
    VIDEO=$(find "$PROJECT/workspace/videos" -name "*cap${cap}*NORMAL*" -newer "$LOGFILE" 2>/dev/null | head -1)
    if [ -n "$VIDEO" ]; then
        STATUS="OK"
        SIZE=$(du -h "$VIDEO" | cut -f1)
    else
        STATUS="FALHOU"
        SIZE="-"
    fi

    echo "[DONE] cap${cap} — ${MINS}m${SECS}s — ${STATUS} (${SIZE})" >> "$TIMING_LOG"

    # Cooldown entre capítulos (2 min pra quota respirar)
    if [[ "$cap" != "$CAP_END" ]]; then
        echo "[WAIT] cooldown 120s entre capítulos..." >> "$TIMING_LOG"
        sleep 120
    fi
done

echo "Fim: $(date '+%Y-%m-%d %H:%M:%S')" >> "$TIMING_LOG"
echo "===================================" >> "$TIMING_LOG"
