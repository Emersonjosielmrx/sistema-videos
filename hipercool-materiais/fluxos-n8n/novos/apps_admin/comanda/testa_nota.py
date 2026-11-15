# Gera a imagem de um cupom de compra fictício e testa a leitura da nota pela IA.
import base64, io, json, sys, time, urllib.request
from PIL import Image, ImageDraw, ImageFont
BASE = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
LOJA, SENHA = sys.argv[1], sys.argv[2]
linhas = ["ATACADAO DISTRIBUIDORA", "CUPOM FISCAL", "-" * 34, "PAO BRIOCHE PCT 6UN   4 PCT  38,40", "QUEIJO MUSSARELA FAT KG 1,5  59,85",
          "REFRIG COCA LATA 350 FARDO12 2  79,80", "BATATA PALITO CONG 2KG  3  71,70", "CEBOLA KG  2,000  9,98", "-" * 34, "TOTAL R$ 259,73"]
img = Image.new("RGB", (620, 60 + 34 * len(linhas)), "white")
d = ImageDraw.Draw(img)
try:
    fonte = ImageFont.truetype("consola.ttf", 22)
except Exception:
    fonte = ImageFont.load_default()
for i, l in enumerate(linhas):
    d.text((24, 24 + i * 34), l, fill="black", font=fonte)
buf = io.BytesIO(); img.save(buf, "JPEG", quality=88)


def api(acao, **dd):
    req = urllib.request.Request(BASE + "/comanda-api", data=json.dumps({"acao": acao, **dd}).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


tok = api("login", loja=LOJA, login="dono", senha=SENHA)["token"]
t = time.time()
r = api("ia_nota", token=tok, b64=base64.b64encode(buf.getvalue()).decode())
print(f"{time.time() - t:.1f}s", r.get("ok"), r.get("erro"))
print(r.get("resultado", "")[:1500])
