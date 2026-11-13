"""Testa o editor de ponta a ponta: python teste_editor.py [arquivo.mp4 | exemplo]"""
import json, os, subprocess, sys, time, urllib.request, urllib.error

B = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
ROTA = os.environ.get("EDITOR_ROTA", "editor-reel")  # editor-reel-v2 / editor-reel-v3 para as cópias
arq = sys.argv[1] if len(sys.argv) > 1 else "exemplo"
if arq == "exemplo":
    vid = "exemplo"
else:
    r = subprocess.run(["curl", "-s", "-m", "600", "-F", f"video=@{arq};type=video/mp4", f"{B}/" + ROTA + "-video"], capture_output=True, text=True)
    print("envio:", r.stdout[:300], flush=True)
    vid = json.loads(r.stdout)["id"]
corpo = {"video": vid, "tipo": "imovel", "marca": "Vista Alta Imóveis", "titulo": "Apartamento 3 quartos com varanda gourmet",
         "detalhes": "3 quartos (1 suíte), sala ampla, varanda gourmet com churrasqueira e vista para a cidade.",
         "instagram": "@vistaalta.imoveis", "trilha": "auto", "cortar_pausas": True, "cortar_vicios": True, "legendas": True, "cartao_final": True}
if len(sys.argv) > 2:  # dados do negócio num .json (marca, titulo, detalhes, instagram, tipo, cor...)
    corpo.update(json.load(open(sys.argv[2], encoding="utf-8")))


def chama(url, dados=None):
    req = urllib.request.Request(url, data=json.dumps(dados).encode() if dados else None, method="POST" if dados else "GET", headers={"Content-Type": "text/plain"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")


r = chama(f"{B}/" + ROTA + "", corpo)
print("pedido:", r, flush=True)
if not r.get("ok"):
    sys.exit(1)
job = r["link"].split("job=")[1]
t0, ult = time.time(), None
while time.time() - t0 < 900:
    time.sleep(6)
    s = chama(f"{B}/{ROTA}-status?job={job}")
    linha = (s.get("etapa"), s.get("detalhe") or s.get("erro"))
    if linha != ult:
        print(int(time.time() - t0), "s", linha, flush=True)
        ult = linha
    if s.get("etapa") in ("pronto", "erro"):
        print(json.dumps(s, ensure_ascii=False, indent=1)[:2500])
        break
