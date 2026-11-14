#!/bin/bash
# sti_short.sh — roda UM Short de parceiro no notebook STI (Linux Mint), 13/11/2026.
# Instalado em ~/recapd-sti/sti_short.sh pelo D:\video-fila\disparar_sti.py. O PC1 escolhe o canal e a fonte, baixa o
# vídeo e manda pra ~/recapd-sti/workspace/anime/<id>_<slug>/ (source.mp4 + cand.json [+ legenda]); este script só monta.
#   sti_short.sh <id> <fonte_url> <handle> <canal> <tipo>
# Sai: ~/recapd-sti/logs/sti_short_<id>.log e, no fim (certo ou errado), ~/recapd-sti/logs/sti_short_<id>.fim com o rc.
ID="$1"; FONTE="$2"; HANDLE="$3"; CANAL="$4"; TIPO="$5"
BASE="$HOME/recapd-sti"
LOG="$BASE/logs/sti_short_$ID.log"
mkdir -p "$BASE/logs"
rm -f "$BASE/logs/sti_short_$ID.fim"
cd "$BASE/bin" || { echo 9 > "$BASE/logs/sti_short_$ID.fim"; exit 9; }
: > "$BASE/workspace/anime/_feitos_short_attempted.txt"
export PATH="$HOME/bin:$PATH" PYTHONPATH=. PYTHONUTF8=1 PYTHONIOENCODING=utf-8
export SEM_YTDLP=1 ANIME_IDIOMAS= ANIME_MAX_CPU_PCT=0 CELULARES=0
export PARCEIRO_HANDLE="$HANDLE" PARCEIRO_CANAL="$CANAL" PARCEIRO_TIPO="$TIPO"
# no Linux o clone de voz usa o caminho "nuvem" do anime_tts (voz_clonada_nuvem.py) com o Applio local
export APPLIO_DIR="$HOME/hipercool-materiais/tools/applio" RAIZ_WIN="$HOME"
export VOZES_PY_NUVEM="$HOME/hipercool-materiais/python/venv_vozes/bin/python"
# 13/11: o STI desligava por calor (99-100 C com o Short usando os 4 nucleos). O Short fica em STI_NUCLEOS nucleos
# (padrao 2: 0-1) e o ffmpeg em 2 threads; mais lento, mas a maquina nao cai. STI_NUCLEOS=4 volta ao antigo.
# 13/11 21:50: "0-1" eram os 2 nucleos FISICOS inteiros (i5-2430M: pares 0,2 e 1,3) e a maquina ia a 100 C igual.
# Agora UM nucleo fisico (STI_CPUS, padrao "0,2") e prioridade minima; "0-3" volta a usar tudo.
CPUS="${STI_CPUS:-0,2}"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 FFMPEG_THREADS=2
nice -n 15 taskset -c "$CPUS" timeout 7200 "$HOME/hipercool-materiais/python/venv_vozes/bin/python" -X utf8 anime_auto.py \
    --modo short --fonte "$FONTE" --engine local --limit 1 --top 5 --id "$ID" > "$LOG" 2>&1
RC=$?
echo "$RC" > "$BASE/logs/sti_short_$ID.fim"
exit $RC
