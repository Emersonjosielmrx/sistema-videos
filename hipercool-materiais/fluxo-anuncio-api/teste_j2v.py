"""Teste direto da API JSON2Video: 2 fotos com zoom/pan, voz Azure pt-BR por cena, legenda e trilha.
Uso: python teste_j2v.py [arquivo_movie.json]"""
import json, sys, time, urllib.request, urllib.error

CHAVE = open(r"D:\hipercool-materiais\fluxo-anuncio-api\j2v_chave.txt").read().strip()
API = "https://api.json2video.com/v2/movies"


def chama(metodo, url, corpo=None):
    req = urllib.request.Request(url, method=metodo, data=json.dumps(corpo).encode() if corpo else None,
                                 headers={"x-api-key": CHAVE, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


if len(sys.argv) > 1:
    movie = json.load(open(sys.argv[1], encoding="utf-8"))
else:
    voz = {"type": "voice", "model": "azure", "voice": "pt-BR-ThalitaMultilingualNeural"}
    movie = {
        "resolution": "custom", "width": 1080, "height": 1920, "quality": "high",
        "scenes": [
            {"elements": [{"type": "image", "src": "https://files.catbox.moe/lofjjm.jpg", "zoom": 3, "duration": -2},
                          {**voz, "text": "Apartamento de três quartos com varanda gourmet e vista para a cidade."}]},
            {"elements": [{"type": "image", "src": "https://files.catbox.moe/zs3gzu.jpg", "zoom": -3, "pan": "left", "duration": -2},
                          {**voz, "text": "Chame no WhatsApp e agende sua visita hoje!"}]},
        ],
        "elements": [
            {"type": "audio", "src": "https://files.catbox.moe/yb6h1l.mp3", "volume": 0.15, "duration": -2},
            {"type": "subtitles", "language": "pt", "settings": {"style": "classic-progressive", "font-size": 80, "position": "bottom-center"}},
        ],
    }
st, r = chama("POST", API, movie)
print("criar:", st, r)
if not r.get("project"):
    sys.exit(1)
proj = r["project"]
for i in range(90):
    time.sleep(8)
    st, r = chama("GET", f"{API}?project={proj}")
    m = r.get("movie") or {}
    print(i, st, m.get("status"), m.get("message", "")[:150], flush=True)
    if m.get("status") in ("done", "error"):
        print(json.dumps(m, ensure_ascii=False)[:1500])
        break
