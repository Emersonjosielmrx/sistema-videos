#!/usr/bin/env bash
# rebuild-no-ai.sh — Remonta vídeos usando APENAS o cache (narração + TTS já gerados).
# Adiciona SFX e trilha sonora que faltavam. ZERO chamadas a Gemini.
# Uso: ./rebuild-no-ai.sh [cap_inicio] [cap_fim]
#   ex: ./rebuild-no-ai.sh 01 09
set -uo pipefail

PROJECT="/d/hipercool-inferior"
VENV="/d/hipercool-videos/venv/Scripts/python.exe"

export PYTHONUTF8=1
export PYTHONUNBUFFERED=1
export TTS_ENGINE=edge
# DESABILITAR qualquer chamada Gemini
export GEMINI_TTS_PROXY_ENABLED=0
export FORCE_TTS_MALE=0

CAP_START="${1:-01}"
CAP_END="${2:-09}"
CAPS=(01 02 03 04 05 06 07 08 09)

echo "=== REBUILD NO-AI — $(date '+%Y-%m-%d %H:%M:%S') ==="
echo "Usando: narration_cache + tts_cache + assets (SFX/trilha)"
echo "Gemini: DESATIVADO"
echo ""

for cap in "${CAPS[@]}"; do
    if [[ "$cap" < "$CAP_START" || "$cap" > "$CAP_END" ]]; then
        continue
    fi

    PANELS="$PROJECT/workspace/panels/the-meek-cat-cap${cap}"
    DEST="$PROJECT/workspace/videos/the-meek-cat/cap${cap}/edge/normal"

    if [ ! -d "$PANELS" ]; then
        echo "[SKIP] cap${cap} — sem painéis"
        continue
    fi

    # Remover v1 anterior (vai regerar com SFX/trilha)
    if [ -f "$DEST/v1.mp4" ]; then
        mv "$DEST/v1.mp4" "$DEST/v1_sem_sfx.mp4.bak"
    fi

    LOGFILE="$PROJECT/cap${cap}_rebuild.log"
    echo "[START] cap${cap} — $(date '+%H:%M:%S')"
    START_S=$(date +%s)

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
    SECS=$(( ELAPSED % 60 ))

    # Verificar resultado
    NEWVID=$(find "$DEST" -name "v*.mp4" -newer "$LOGFILE" 2>/dev/null | head -1)
    if [ -z "$NEWVID" ]; then
        NEWVID=$(find "$DEST" -name "v*.mp4" 2>/dev/null | sort | tail -1)
    fi

    if [ -n "$NEWVID" ] && [ -f "$NEWVID" ]; then
        SIZE=$(du -h "$NEWVID" | cut -f1)
        echo "[DONE] cap${cap} — ${MINS}m${SECS}s — OK (${SIZE})"
        # Limpar backup se deu certo
        rm -f "$DEST/v1_sem_sfx.mp4.bak"
    else
        echo "[FAIL] cap${cap} — ${MINS}m${SECS}s — FALHOU"
        # Restaurar backup
        if [ -f "$DEST/v1_sem_sfx.mp4.bak" ]; then
            mv "$DEST/v1_sem_sfx.mp4.bak" "$DEST/v1.mp4"
        fi
    fi
done

echo ""
echo "=== REBUILD COMPLETO — $(date '+%Y-%m-%d %H:%M:%S') ==="
