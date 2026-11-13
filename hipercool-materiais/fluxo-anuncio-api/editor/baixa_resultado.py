# Baixa o vídeo editado, a capa e a legenda do post de um trabalho do editor. python baixa_resultado.py <job> <pasta>
import json, os, sys, urllib.request
from pathlib import Path

ROTA = os.environ.get("EDITOR_ROTA", "editor-reel")  # editor-reel-v2 / editor-reel-v3 para as cópias
job, pasta = sys.argv[1], Path(sys.argv[2])
pasta.mkdir(parents=True, exist_ok=True)
s = json.loads(urllib.request.urlopen(
    "https://webhookn8n6.inovareinteligenciaartificial.com/webhook/" + ROTA + "-status?job=" + job, timeout=60).read())
nome = sys.argv[3] if len(sys.argv) > 3 else "2_EDITADO"   # nome do arquivo (sem extensão)
for chave, arq in (("video", nome + ".mp4"), ("capa", "capa_" + nome + ".jpg")):
    (pasta / arq).write_bytes(urllib.request.urlopen(s[chave], timeout=300).read())
(pasta / ("legenda_do_post_" + nome + ".txt")).write_text(s.get("legenda_post", ""), encoding="utf-8")
print("ok", [p.name for p in pasta.iterdir()])
