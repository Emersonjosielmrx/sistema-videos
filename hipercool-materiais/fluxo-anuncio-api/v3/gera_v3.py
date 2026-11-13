"""Gera a V3 do "Vídeo de Anúncio com IA": igual à V1 (fotos no Redis, wsrv.nl, 6 IAs), mas a voz é do Google Tradutor
e o vídeo é um comando ffmpeg rodado na nuvem pelo Very Good FFmpeg (grátis sem cartão, sem marca d'água).
Lê ../v1/fluxo_v1.json (rode antes o gera_v1.py) e grava fluxo_v3.json. Uso: python gera_v3.py <id_credencial_vgf>"""
import copy, json, re, sys, uuid
from pathlib import Path

AQUI = Path(__file__).parent
CRED = {"httpHeaderAuth": {"id": sys.argv[1] if len(sys.argv) > 1 else "SemCredencial001", "name": "Very Good FFmpeg (Bearer)"}}
t = (AQUI.parent / "v1" / "fluxo_v1.json").read_text(encoding="utf-8")
t = re.sub(r"anuncio-j2v/(\$\{[a-z]+\}|C[ÓO]DIGO)/anuncio-video", r"anuncio-ff/\1/anuncio-ffmpeg", t)
t = t.replace('":id/anuncio-video"', '":id/anuncio-ffmpeg"').replace("`:id/anuncio-video`", "`:id/anuncio-ffmpeg`")
t = t.replace('"webhookId": "anuncio-j2v"', '"webhookId": "anuncio-ff"')
t = t.replace("anuncio-video-j2v", "anuncio-video-ff").replace("anvj2v", "anvff")
t = t.replace("VERSÃO JSON2VIDEO", "VERSÃO FFMPEG NA NUVEM").replace("JSON2Video", "Very Good FFmpeg")
w = json.loads(t)
w["id"] = "AnuncioFfmpegV3x"
w["name"] = "Vídeo de Anúncio com IA · ffmpeg na nuvem + voz Google (sem marca d'água) - V3"
nos = {n["name"]: n for n in w["nodes"]}
con = w["connections"]
for n in w["nodes"]:
    n["id"] = str(uuid.uuid4())
    if "webhookId" in n and n["webhookId"] != "anuncio-ff":
        n["webhookId"] = str(uuid.uuid4())


def js(nome):
    return (AQUI / nome).read_text(encoding="utf-8").strip() + "\n"


def no(nome, tipo, versao, pos, params, **extra):
    n = {"parameters": params, "name": nome, "type": tipo, "typeVersion": versao, "position": pos, "id": str(uuid.uuid4()), **extra}
    w["nodes"].append(n)
    nos[nome] = n


def apaga(nome):
    w["nodes"].remove(nos.pop(nome))
    con.pop(nome, None)
    for saidas in con.values():
        for lista in saidas.get("main", []):
            lista[:] = [c for c in lista if c["node"] != nome]


def liga(de, para, saida=0):
    m = con.setdefault(de, {}).setdefault("main", [])
    while len(m) <= saida:
        m.append([])
    m[saida].append({"node": para, "type": "main", "index": 0})


def renomeia(velho, novo):
    n = nos.pop(velho)
    n["name"] = novo
    nos[novo] = n
    if velho in con:
        con[novo] = con.pop(velho)
    for saidas in con.values():
        for lista in saidas.get("main", []):
            for c in lista:
                if c["node"] == velho:
                    c["node"] = novo


REDIS = copy.deepcopy(nos["💾 Guarda o anúncio"]["credentials"])
MONTA, CRIA = "🧩 Monta o filme (Very Good FFmpeg)", "🎬 Very Good FFmpeg: cria o vídeo"
x, y = nos[MONTA]["position"]

# ── narração pelo Google ➜ vozes no Redis ➜ medidas ─────────────────────────────────────────────────────────────
con["💾 Status: narrando"] = {"main": [[]]}
no("🧩 Narra as falas (Google)", "n8n-nodes-base.code", 2, [x + 320, y - 220], {"jsCode": js("narra_falas.js")}, onError="continueErrorOutput")
no("💾 Guarda as vozes (1 dia)", "n8n-nodes-base.redis", 1, [x, y - 220], {
    "operation": "set", "key": "=anvff:foto:{{ $json.id }}", "value": "={{ $json.b64 }}", "keyType": "string", "expire": True, "ttl": 86400}, credentials=copy.deepcopy(REDIS))
no("🧩 Mede as vozes", "n8n-nodes-base.code", 2, [x - 320, y - 220], {"jsCode": js("mede_vozes.js")})
liga("💾 Status: narrando", "🧩 Narra as falas (Google)")
liga("🧩 Narra as falas (Google)", "💾 Guarda as vozes (1 dia)", 0)
liga("🧩 Narra as falas (Google)", "⚠️ Marca erro", 1)
liga("💾 Guarda as vozes (1 dia)", "🧩 Mede as vozes")

# ── o filme: comando ffmpeg ➜ textos no Redis ➜ cria (uma vez só) ─────────────────────────────────────────────────
con.pop("🧩 Mede as vozes", None)
liga("🧩 Mede as vozes", MONTA)
nos[MONTA]["parameters"]["jsCode"] = js("monta_ffmpeg.js")
nos[MONTA]["onError"] = "continueErrorOutput"
con[MONTA] = {"main": [[]]}
no("🧩 Separa os textos", "n8n-nodes-base.code", 2, [x, y + 220], {"jsCode": js("separa_textos.js")})
no("💾 Guarda os textos (1 dia)", "n8n-nodes-base.redis", 1, [x - 320, y + 220], {
    "operation": "set", "key": "=anvff:foto:{{ $json.id }}", "value": "={{ $json.b64 }}", "keyType": "string", "expire": True, "ttl": 86400}, credentials=copy.deepcopy(REDIS))
liga(MONTA, "🧩 Separa os textos", 0)
liga(MONTA, "⚠️ Marca erro", 1)
liga("🧩 Separa os textos", "💾 Guarda os textos (1 dia)")
con["💾 Guarda os textos (1 dia)"] = {"main": [[{"node": CRIA, "type": "main", "index": 0}]]}
c = nos[CRIA]
c["parameters"]["url"] = "https://verygoodffmpeg.com/api/ffmpeg"
c["parameters"]["jsonBody"] = "={{ $('" + MONTA + "').first().json.corpo }}"
c["credentials"] = CRED
c["executeOnce"] = True          # chegam 2 itens (os 2 textos): o vídeo é pedido uma vez só
nos["🧩 Guarda os projetos"]["parameters"]["jsCode"] = js("guarda_projetos.js")

# ── andamento: um pedido só (o trabalho tem as 3 saídas) ────────────────────────────────────────────────────────
apaga("🎬 Very Good FFmpeg: como está o só música?")
renomeia("🎬 Very Good FFmpeg: como está o narrado?", "🎬 Very Good FFmpeg: como está?")
st = nos["🎬 Very Good FFmpeg: como está?"]
st["parameters"]["url"] = "=https://verygoodffmpeg.com/api/jobs/{{ $('🧩 Guarda os projetos').first().json.id }}"
st["credentials"] = CRED
con["🎬 Very Good FFmpeg: como está?"] = {"main": [[{"node": "🧩 Atualiza o andamento", "type": "main", "index": 0}]]}
nos["🧩 Atualiza o andamento"]["parameters"]["jsCode"] = js("atualiza_andamento.js")
s = nos["💾 Status: narrando"]["parameters"]
s["value"] = s["value"].replace("'Mandando para a Very Good FFmpeg · voz '", "'Narrando com a voz do Google · trilha '").replace(
    " + $('🧩 Confere o pedido').first().json.op.voz.split('-')[2].replace(/Multilingual|Neural/g, '') + ' · trilha '", "")

# ── notas ─────────────────────────────────────────────────────────────────────────────────────────────────────────
for nome, texto in json.loads((AQUI / "notas.json").read_text(encoding="utf-8")).items():
    nos[nome]["parameters"]["content"] = texto
cq = nos["Nota · Comece aqui"]["parameters"]
cq["content"] = cq["content"].replace(
    "🎬 **Very Good FFmpeg** (API na internet): narra, dá movimento às fotos, escreve na tela, põe legenda e trilha e devolve o MP4",
    "🎙️ **Google Tradutor** narra (grátis, sem chave) · 🎬 **Very Good FFmpeg** (ffmpeg na nuvem, sem cartão) dá movimento às fotos, escreve na tela, põe legenda e trilha e devolve o MP4 **sem marca d'água**").replace(
    "a chave grátis da Very Good FFmpeg", "a chave grátis do Very Good FFmpeg")

# ── conferências ──────────────────────────────────────────────────────────────────────────────────────────────────
tudo = json.dumps(w, ensure_ascii=False)
for proibido in ("json2video", "j2v", "video-oficina", "/videos/", "só música?"):
    assert proibido not in tudo.lower(), proibido
for de, saidas in con.items():
    assert de in nos, de
    for lista in saidas.get("main", []):
        for c2 in lista:
            assert c2["node"] in nos, (de, c2["node"])
for n in w["nodes"]:
    for ref in re.findall(r"\$\('([^']+)'\)", json.dumps(n["parameters"], ensure_ascii=False)):
        assert ref in nos, (n["name"], ref)
(AQUI / "fluxo_v3.json").write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok:", len(w["nodes"]), "nós")
