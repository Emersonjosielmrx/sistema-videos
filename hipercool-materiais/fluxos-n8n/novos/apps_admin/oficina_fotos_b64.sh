set -e
cd /opt/video-oficina
cp app.py app.py.antes-fotos-b64
python3 /tmp/oficina_fotos_b64.py
python3 -c "import ast;ast.parse(open('app.py').read())"
NOVA=video-oficina:30
docker build -q -t $NOVA . > /tmp/oficina_build.log 2>&1 || { cp app.py.antes-fotos-b64 app.py; tail -20 /tmp/oficina_build.log; exit 1; }
docker service update --image $NOVA --detach=false video-oficina 2>&1 | tail -2
sleep 8
C=$(docker ps -q -f name=video-oficina)
docker exec $C curl -s localhost:8000/videos/saude
echo
docker exec $C grep -c fotos_b64 /app/app.py
