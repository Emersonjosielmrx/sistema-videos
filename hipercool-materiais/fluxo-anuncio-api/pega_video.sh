#!/bin/bash
# baixa o vídeo de um projeto JSON2Video e tira um mosaico de quadros: pega_video.sh <projeto> <nome>
K=$(cat /d/hipercool-materiais/fluxo-anuncio-api/j2v_chave.txt)
u=$(curl -s -H "x-api-key: $K" "https://api.json2video.com/v2/movies?project=$1" | python -c "import sys,json; m=json.load(sys.stdin)['movie']; print(m.get('url') or ''); import sys as s; s.stderr.write('dur %s %s\n'%(m.get('duration'),m.get('message')))")
[ -n "$u" ] || exit 1
curl -s -o "$2.mp4" "$u"
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$2.mp4")
ffmpeg -v error -y -i "$2.mp4" -vf "fps=8/$d,scale=240:-2,tile=8x1" -frames:v 1 "$2_quadros.jpg"
ffmpeg -hide_banner -i "$2.mp4" -af volumedetect -f null NUL 2>&1 | grep -E "mean_volume|max_volume"
echo "$u"
