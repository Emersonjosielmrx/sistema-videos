"""Gera a V2 do "Vídeo de Anúncio com IA": igual à V1 (fotos no Redis, wsrv.nl, 6 IAs), mas o vídeo é feito pelo Shotstack.
Lê ../v1/fluxo_v1.json (rode antes o gera_v1.py) e grava fluxo_v2.json. Uso: python gera_v2.py <id_credencial_shotstack>"""
import json, re, sys, uuid
from pathlib import Path

AQUI = Path(__file__).parent
CRED = {"httpHeaderAuth": {"id": sys.argv[1] if len(sys.argv) > 1 else "SemCredencial001", "name": "Shotstack (x-api-key)"}}
t = (AQUI.parent / "v1" / "fluxo_v1.json").read_text(encoding="utf-8")

# endereços e chaves próprios (a V1 continua no ar ao lado)
t = re.sub(r"anuncio-j2v/(\$\{[a-z]+\}|C[ÓO]DIGO)/anuncio-video", r"anuncio-ss/\1/anuncio-shotstack", t)
t = t.replace('":id/anuncio-video"', '":id/anuncio-shotstack"').replace("`:id/anuncio-video`", "`:id/anuncio-shotstack`")
t = t.replace('"webhookId": "anuncio-j2v"', '"webhookId": "anuncio-ss"')
t = t.replace("anuncio-video-j2v", "anuncio-video-ss").replace("anvj2v", "anvss")
t = t.replace("JSON2Video", "Shotstack").replace("VERSÃO JSON2VIDEO", "VERSÃO SHOTSTACK")
t = t.replace("Baixe os vídeos: o link vale 7 dias.", "Os vídeos ficam guardados no Shotstack.")
w = json.loads(t)
w["id"] = "AnuncioShotstV2x"
w["name"] = "Vídeo de Anúncio com IA · Shotstack (sem servidor de vídeo) - V2"
nos = {n["name"]: n for n in w["nodes"]}
for n in w["nodes"]:
    n["id"] = str(uuid.uuid4())
    if "webhookId" in n and n["webhookId"] != "anuncio-ss":
        n["webhookId"] = str(uuid.uuid4())


def js(nome):
    return (AQUI / nome).read_text(encoding="utf-8").strip() + "\n"


nos["🧩 Monta o filme (Shotstack)"]["parameters"]["jsCode"] = js("monta_filme.js")
nos["🧩 Guarda os projetos"]["parameters"]["jsCode"] = js("guarda_projetos.js")
nos["🧩 Atualiza o andamento"]["parameters"]["jsCode"] = js("atualiza_andamento.js")
cria = nos["🎬 Shotstack: cria o vídeo"]
cria["parameters"]["url"] = "=https://api.shotstack.io/edit/{{ $json.ambiente }}/render"
cria["credentials"] = CRED
for nome, campo in (("🎬 Shotstack: como está o narrado?", "narrado"), ("🎬 Shotstack: como está o só música?", "musica")):
    nos[nome]["parameters"]["url"] = ("=https://api.shotstack.io/edit/{{ $('🧩 Guarda os projetos').first().json.ambiente }}/render/"
                                      "{{ $('🧩 Guarda os projetos').first().json." + campo + " || $('🧩 Guarda os projetos').first().json.narrado }}")
    nos[nome]["credentials"] = CRED

NOTAS = json.loads((AQUI / "notas.json").read_text(encoding="utf-8"))
for nome, texto in NOTAS.items():
    nos[nome]["parameters"]["content"] = texto
c = nos["Nota · Comece aqui"]["parameters"]
c["content"] = c["content"].replace("VERSÃO Shotstack", "VERSÃO SHOTSTACK").replace(
    "🎬 **Shotstack** (API na internet): narra, dá movimento às fotos, escreve na tela, põe legenda e trilha e devolve o MP4",
    "🎬 **Shotstack** (API na internet): narra com voz ElevenLabs, dá movimento às fotos, escreve na tela, põe legenda e trilha e guarda o MP4 para sempre no CDN dele")

tudo = json.dumps(w, ensure_ascii=False)
for proibido in ("json2video", "j2v", "video-oficina", "/videos/"):
    assert proibido not in tudo.lower(), proibido
for n in w["nodes"]:
    for ref in re.findall(r"\$\('([^']+)'\)", json.dumps(n["parameters"], ensure_ascii=False)):
        assert ref in nos, (n["name"], ref)
(AQUI / "fluxo_v2.json").write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok:", len(w["nodes"]), "nós")
