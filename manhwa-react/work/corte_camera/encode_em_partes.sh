#!/usr/bin/env bash
# Corta so a camera (linhas 0-401 do camera_isolada) e amplia p/ 1920x1080, em 4 pedacos de video (refaz o pedaco que falhar),
# junta sem reprocessar e poe o audio original copiado.
SRC="/d/downloads/6-20261006T155330Z-1-001/Nova pasta/2026-10-06_parte1_camera_isolada.mp4"
OUT="/d/downloads/6-20261006T155330Z-1-001/Nova pasta/2026-10-06_parte1_SO_CAMERA_1080p.mp4"
W="/d/manhwa-react/work/corte_camera"
VF="crop=714:402:3:0,scale=1920:1080:flags=lanczos,setsar=1,format=nv12"
CORTES=(0 1015 2030 3045 99999)
: > "$W/lista.txt"
for i in 0 1 2 3; do
  A=${CORTES[$i]}; B=${CORTES[$((i+1))]}; SEG="$W/seg_$i.mp4"
  for tent in 1 2 3; do
    if [ -s "$SEG.ok" ]; then break; fi
    echo "pedaco $i ($A-$B s) tentativa $tent"
    if ffmpeg -v error -y -ss "$A" -to "$B" -i "$SRC" -an -vf "$VF" -c:v h264_qsv -preset slow -global_quality 21 \
         -look_ahead 1 "$SEG"; then
      echo ok > "$SEG.ok"
    else
      echo "pedaco $i falhou"; sleep 20
    fi
  done
  [ -s "$SEG.ok" ] || { echo "ERRO: pedaco $i nao saiu"; exit 1; }
  echo "file '$SEG'" >> "$W/lista.txt"
done
ffmpeg -v error -y -f concat -safe 0 -i "$W/lista.txt" -c copy "$W/video_junto.mp4" || exit 1
ffmpeg -v error -y -i "$W/video_junto.mp4" -i "$SRC" -map 0:v:0 -map 1:a:0 -c copy -shortest -movflags +faststart "$OUT" || exit 1
ffprobe -v error -show_entries format=duration,size:stream=codec_type,width,height -of compact "$OUT"
echo PRONTO
