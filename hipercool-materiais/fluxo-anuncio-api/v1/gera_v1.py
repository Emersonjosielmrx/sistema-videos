"""Gera a V1 do "Vídeo de Anúncio com IA" sem a oficina: JSON2Video + catbox.moe + wsrv.nl.
Lê ../original.json (export do n8n6) e grava fluxo_v1.json. Rodar de novo sempre que mudar um .js desta pasta."""
import copy, json, re, sys, uuid
from pathlib import Path

AQUI = Path(__file__).parent
ORIG = json.loads((AQUI.parent / "original.json").read_text(encoding="utf-8"))
ORIG = ORIG[0] if isinstance(ORIG, list) else ORIG
CRED_J2V = {"httpHeaderAuth": {"id": sys.argv[1] if len(sys.argv) > 1 else "J2vChaveAulas001", "name": "JSON2Video (x-api-key)"}}
URLS = dict(l.split() for l in (AQUI.parent / "urls.txt").read_text().splitlines() if len(l.split()) == 2)

w = copy.deepcopy(ORIG)
w["id"] = "AnuncioJ2vV1x001"
w["name"] = "Vídeo de Anúncio com IA · JSON2Video (sem servidor de vídeo) - V1"
w["active"] = False
for k in ("versionId", "activeVersionId", "updatedAt", "createdAt", "shared", "tags", "pinData", "staticData", "meta", "triggerCount", "isArchived", "description"):
    w.pop(k, None)
nos = {n["name"]: n for n in w["nodes"]}
con = w["connections"]


def js(nome):
    return (AQUI / nome).read_text(encoding="utf-8").strip() + "\n"


def troca(nome, campo, velho, novo, conta=1):
    p = nos[nome]["parameters"]
    if p[campo].count(velho) != conta:
        raise SystemExit(f"{nome}: esperava {conta}x {velho[:70]!r}, achei {p[campo].count(velho)}")
    p[campo] = p[campo].replace(velho, novo)


def no(nome, tipo, versao, pos, params, **extra):
    n = {"parameters": params, "name": nome, "type": tipo, "typeVersion": versao, "position": pos, "id": str(uuid.uuid4()), **extra}
    w["nodes"].append(n)
    nos[nome] = n
    return n


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


def desliga_tudo(de):
    con.pop(de, None)


def pos(nome, dx=0, dy=0):
    x, y = nos[nome]["position"]
    return [x + dx, y + dy]


# ── 1. endereços próprios (não brigam com o original, que continua no ar) ──────────────────────────────────────────
for n in w["nodes"]:
    if n["type"] == "n8n-nodes-base.webhook":
        n["webhookId"] = "anuncio-j2v" if n["webhookId"] == "anuncio" else str(uuid.uuid4())
    elif "webhookId" in n:
        n["webhookId"] = str(uuid.uuid4())
    n["id"] = str(uuid.uuid4())
    t = json.dumps(n["parameters"], ensure_ascii=False)
    t = re.sub(r"anuncio-video(?!-j2v)(-ver|-status)?", r"anuncio-video-j2v\1", t)
    # a página pública vira /webhook/anuncio-j2v/<id>/anuncio-video: o n8n acusa conflito quando o caminho dinâmico
    # (":id/pagina", ":id/ver"...) já existe em outro fluxo, mesmo com outro webhookId
    t = re.sub(r"webhook/anuncio/(\$\{[a-z]+\}|C[ÓO]DIGO)/pagina", r"webhook/anuncio-j2v/\1/anuncio-video", t)
    t = t.replace('"path": ":id/pagina"', '"path": ":id/anuncio-video"').replace("(o caminho `:id/pagina`", "(o caminho `:id/anuncio-video`")
    n["parameters"] = json.loads(t)

# ── 2. página do formulário: as fotos sobem pelo próprio n8n para o catbox.moe (sem passe, sem oficina) ──────────
p = nos["🔐 Gera o passe de envio"]["parameters"]
linhas = p["jsCode"].split("\n")
i = next(k for k, l in enumerate(linhas) if l.startswith("const PAGINA = "))
html = json.loads(linhas[i][len("const PAGINA = "):].rstrip(";"))
TRILHAS = {n: URLS[f"trilhas/{n}.mp3"] for n in ("animado", "calmo", "chill", "elegante", "emocional", "latino", "tropical", "urgente")}
EX = {"apartamento": [URLS[f"exemplos/apartamento/{n}.jpg"] for n in range(1, 6)],
      "hamburguer": [URLS[f"exemplos/hamburguer/{n}.jpg"] for n in range(1, 5)]}
velho_envia = html[html.index("  function envia(arq, aoTerminar, aoProgresso) {"):html.index("  function fila(arqs) {")]
novo_envia = """  // a foto vai em JPEG de até 2048 px (o logo em PNG de até 800 px, para manter o fundo transparente): sobe rápido e
  // ocupa pouco no Redis; se o navegador não abrir o arquivo, vai o original
  function encolhe(arq, logo, pronto) {
    var img = new Image(), u = URL.createObjectURL(arq), lado = logo ? 800 : 2048;
    img.onload = function () {
      var r = Math.min(1, lado / Math.max(img.naturalWidth, img.naturalHeight)), c = document.createElement('canvas');
      c.width = Math.round(img.naturalWidth * r); c.height = Math.round(img.naturalHeight * r);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height); URL.revokeObjectURL(u);
      c.toBlob(function (b) { pronto(b || arq, b ? (logo ? '.png' : '.jpg') : ''); }, logo ? 'image/png' : 'image/jpeg', 0.88);
    };
    img.onerror = function () { URL.revokeObjectURL(u); pronto(arq, ''); };
    img.src = u;
  }
  function envia(arq, aoTerminar, aoProgresso, logo) {
    encolhe(arq, !!logo, function (arquivo, ext) {
      var nome = ext ? String(arq.name || 'foto').replace(/\\.[^.]+$/, '') + ext : (arq.name || 'foto.jpg');
      var fd = new FormData(); fd.append('arquivo', arquivo, nome);
      var x = new XMLHttpRequest(); x.open('POST', 'anuncio-video-j2v-foto');  // o n8n guarda a foto (Redis, 30 dias) e devolve o código
      x.upload.onprogress = function (e) { if (e.lengthComputable && aoProgresso) aoProgresso(Math.round(e.loaded / e.total * 100)); };
      x.onload = function () { var r = {}; try { r = JSON.parse(x.responseText); } catch (e) {} aoTerminar(x.status === 200 && r.ok ? null : (r.erro || 'não deu para enviar'), r); };
      x.onerror = function () { aoTerminar('falha de conexão'); };
      x.send(fd);
    });
  }
"""
html = html.replace(velho_envia, novo_envia)
for velho, novo in [
    ("  var PASSE = '__PASSE__';\n", "  var EXURL = " + json.dumps(EX) + ";\n"),
    ("url: '/videos/arquivo/exemplos/fotos/' + e.pasta + '/' + n + '.jpg' }", "url: EXURL[e.pasta][n - 1] }"),
    ("    envia(a, function (erro, r) {\n", "    envia(a, function (erro, r) {\n"),
    ("el('#logo-info').textContent = r.transparente ? '✅ fundo transparente' : '✅ pronto';", "el('#logo-info').textContent = '✅ pronto';"),
]:
    if html.count(velho) != 1:
        raise SystemExit(f"página: não achei {velho[:60]!r}")
    html = html.replace(velho, novo)
html = html.replace("\n    });\n  });\n  el('#logo-tira')", "\n    }, null, true);\n  });\n  el('#logo-tira')")
assert "}, null, true);" in html and "PASSE" not in html and "/videos/" not in html
p["jsCode"] = ("// Entrega a página do formulário. Cada foto é reduzida no navegador (JPEG até 2048 px) e sobe para o próprio n8n\n"
               "// (webhook anuncio-video-j2v-foto), que guarda no Redis por 30 dias e devolve o código da foto.\n"
               "const PAGINA = " + json.dumps(html, ensure_ascii=False) + ";\n"
               "return [{ json: { html: PAGINA } }];\n")
nos["🔐 Gera o passe de envio"]["name"] = "🧾 Monta a página do formulário"
nos["🧾 Monta a página do formulário"] = nos.pop("🔐 Gera o passe de envio")
con["🧾 Monta a página do formulário"] = con.pop("🔐 Gera o passe de envio")
for saidas in con.values():
    for lista in saidas.get("main", []):
        for c in lista:
            if c["node"] == "🔐 Gera o passe de envio":
                c["node"] = "🧾 Monta a página do formulário"

# webhooks que recebem cada foto (guarda no Redis por 30 dias) e que entregam a foto pelo endereço público
REDIS = copy.deepcopy(nos["💾 Guarda o anúncio"]["credentials"])
SE_OK = lambda campo: {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                       "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ $json." + campo + " }}", "rightValue": "", "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                       "combinator": "and"}, "options": {}}
CABECA_JSON = {"entries": [{"name": "Content-Type", "value": "application/json; charset=UTF-8"}, {"name": "Cache-Control", "value": "no-store"}]}
base = pos("🔔 Página do anúncio (GET)", 0, -700)
no("🔔 Recebe a foto (POST)", "n8n-nodes-base.webhook", 2, base, {"httpMethod": "POST", "path": "anuncio-video-j2v-foto", "responseMode": "responseNode", "options": {}}, webhookId=str(uuid.uuid4()))
no("🧩 Confere a foto", "n8n-nodes-base.code", 2, [base[0] + 320, base[1]], {"jsCode": js("confere_foto.js")})
no("🚦 Foto ok?", "n8n-nodes-base.if", 2.2, [base[0] + 640, base[1]], SE_OK("ok"))
no("💾 Guarda a foto (30 dias)", "n8n-nodes-base.redis", 1, [base[0] + 960, base[1] - 120], {
    "operation": "set", "key": "=anvj2v:foto:{{ $json.id }}", "value": "={{ $json.b64 }}", "keyType": "string", "expire": True, "ttl": 2592000}, credentials=copy.deepcopy(REDIS))
no("📤 Responde a foto", "n8n-nodes-base.respondToWebhook", 1.1, [base[0] + 1280, base[1]], {
    "respondWith": "text", "responseBody": "={{ JSON.stringify($('🧩 Confere a foto').first().json.ok ? { ok: true, id: $('🧩 Confere a foto').first().json.id } : { ok: false, erro: $('🧩 Confere a foto').first().json.erro }) }}",
    "options": {"responseCode": "={{ $('🧩 Confere a foto').first().json.ok ? 200 : 400 }}", "responseHeaders": CABECA_JSON}})
liga("🔔 Recebe a foto (POST)", "🧩 Confere a foto")
liga("🧩 Confere a foto", "🚦 Foto ok?")
liga("🚦 Foto ok?", "💾 Guarda a foto (30 dias)", 0)
liga("🚦 Foto ok?", "📤 Responde a foto", 1)
liga("💾 Guarda a foto (30 dias)", "📤 Responde a foto")
b2 = [base[0], base[1] + 300]
no("🔔 Entrega a foto (GET)", "n8n-nodes-base.webhook", 2, b2, {"path": "anuncio-video-j2v-arquivo", "responseMode": "responseNode", "options": {}}, webhookId=str(uuid.uuid4()))
no("📖 Lê a foto", "n8n-nodes-base.redis", 1, [b2[0] + 320, b2[1]], {
    "operation": "get", "propertyName": "foto", "key": "=anvj2v:foto:{{ String($json.query.id || '').replace(/[^a-z0-9.-]/g, '') }}", "keyType": "string", "options": {}}, credentials=copy.deepcopy(REDIS))
no("🧩 Vira arquivo", "n8n-nodes-base.code", 2, [b2[0] + 640, b2[1]], {"jsCode": js("entrega_foto.js").replace("__EXEMPLOS__", json.dumps(EX)).replace("__TRILHAS__", json.dumps(TRILHAS))})
no("🚦 A foto existe?", "n8n-nodes-base.if", 2.2, [b2[0] + 960, b2[1]], SE_OK("existe"))
no("📤 Entrega a imagem", "n8n-nodes-base.respondToWebhook", 1.1, [b2[0] + 1280, b2[1] - 100], {
    "respondWith": "binary", "options": {"responseHeaders": {"entries": [{"name": "Cache-Control", "value": "public, max-age=86400"}]}}})
no("📤 Foto não encontrada", "n8n-nodes-base.respondToWebhook", 1.1, [b2[0] + 1280, b2[1] + 100], {
    "respondWith": "text", "responseBody": "foto não encontrada (passou de 30 dias?)", "options": {"responseCode": 404}})
liga("🔔 Entrega a foto (GET)", "📖 Lê a foto")
liga("📖 Lê a foto", "🧩 Vira arquivo")
liga("🧩 Vira arquivo", "🚦 A foto existe?")
liga("🚦 A foto existe?", "📤 Entrega a imagem", 0)
liga("🚦 A foto existe?", "📤 Foto não encontrada", 1)

# ── 3. pedido: as fotos agora são endereços públicos (ou os exemplos, que viram endereços) ─────────────────────────
troca("🧩 Confere o pedido", "jsCode", "const ID_FOTO = /^([a-f0-9]{12}\\.(jpg|png)|exemplo-[a-z0-9]{3,30}-\\d{1,2})$/;",
      "const ID_FOTO = /^([a-f0-9]{12}\\.(jpg|png|webp)|exemplo-[a-z0-9]{3,30}-\\d{1,2})$/;\n"
      "// todas as fotos passam pelo endereço do próprio n8n (webhook anuncio-video-j2v-arquivo): as enviadas pela página\n"
      "// ficam no Redis e as de exemplo o n8n busca no catbox.moe (o wsrv.nl nem sempre alcança o catbox)")
troca("🧩 Confere o pedido", "jsCode", "const base = String(", "const base0 = String(")
troca("🧩 Confere o pedido", "jsCode", "const logo = /^[a-f0-9]{12}\\.(jpg|png)$/.test(String(b.logo || '')) ? String(b.logo) : '';",
      "const logoId = /^[a-f0-9]{12}\\.(jpg|png|webp)$/.test(String(b.logo || '')) ? String(b.logo) : '';")
troca("🧩 Confere o pedido", "jsCode", "valido: erros.length === 0, erros, job, anuncio, fotos, logo,",
      "valido: erros.length === 0, erros, job, anuncio, fotos: fotos.map(paraUrl), logo: logoId ? paraUrl(logoId) : '', arquivo,")
troca("🧩 Confere o pedido", "jsCode", "return [{ json: {\n  valido:",
      "const base = base0;\n"
      "const arquivo = `${base}/webhook/anuncio-video-j2v-arquivo?id=`;\n"
      "const paraUrl = f => arquivo + f;\n"
      "return [{ json: {\n  valido:")
troca("🧩 Confere o pedido", "jsCode", ", publico: `${base}/videos/arquivo`", "")
troca("🧩 Confere o pedido", "jsCode", "chave_limite: '<SEGREDO_REMOVIDO>'", "chave_limite: '<SEGREDO_REMOVIDO>'")

# ── 4. a IA olha as fotos: miniaturas e medidas pelo wsrv.nl (em vez da oficina) ─────────────────────────────────
x, y = nos["🛠️ Oficina: prepara as fotos"]["position"]
apaga("🛠️ Oficina: prepara as fotos")
no("🧩 Lista as fotos", "n8n-nodes-base.code", 2, [x + 160, y - 160], {"jsCode": "// Uma linha por foto, para medir e baixar a miniatura de cada uma.\nreturn $('🧩 Confere o pedido').first().json.fotos.map((url, i) => ({ json: { i, url } }));\n"})
no("🌐 Mede a foto (wsrv.nl)", "n8n-nodes-base.httpRequest", 4.2, [x - 160, y - 160], {
    "url": "=https://wsrv.nl/?url={{ encodeURIComponent($json.url) }}&output=json", "options": {"response": {"response": {"neverError": True}}, "timeout": 60000}},
    onError="continueRegularOutput", retryOnFail=True, maxTries=2, waitBetweenTries=2000)
no("🌐 Baixa a miniatura (wsrv.nl)", "n8n-nodes-base.httpRequest", 4.2, [x - 160, y + 160], {
    "url": "=https://wsrv.nl/?url={{ encodeURIComponent($('🧩 Lista as fotos').item.json.url) }}&w=512&h=512&fit=inside&output=jpg&q=72",
    "options": {"response": {"response": {"responseFormat": "file"}}, "timeout": 60000}},
    onError="continueRegularOutput", retryOnFail=True, maxTries=2, waitBetweenTries=2000)
nos["🧩 Prepara as fotos para a IA"]["parameters"]["jsCode"] = js("prepara_fotos_ia.js")
nos["🧩 Prepara as fotos para a IA"]["onError"] = "continueErrorOutput"
desliga_tudo("💾 Status: olhando as fotos")
liga("💾 Status: olhando as fotos", "🧩 Lista as fotos")
liga("🧩 Lista as fotos", "🌐 Mede a foto (wsrv.nl)")
liga("🌐 Mede a foto (wsrv.nl)", "🌐 Baixa a miniatura (wsrv.nl)")
liga("🌐 Baixa a miniatura (wsrv.nl)", "🧩 Prepara as fotos para a IA")
liga("🧩 Prepara as fotos para a IA", "⚠️ Marca erro", 1)
troca("💾 Status: olhando as fotos", "value", "'Medindo e mostrando '", "'Mostrando '")
troca("🧩 Lê o que a IA viu", "jsCode", "$('🛠️ Oficina: prepara as fotos').first().json", "$('🧩 Prepara as fotos para a IA').first().json")
troca("🧩 Lê o que a IA viu", "jsCode", "const medidos = [f.brilho < 55 ? 'escura (medido)' : '', f.nitidez < 120 ? 'pouco nítida (medido)' : ''];",
      "const medidos = [];  // sem medir brilho/nitidez: a IA com visão avisa foto escura ou tremida em \"problemas\"")
troca("🧩 Junta tudo", "jsCode", "monta o que vai para a oficina (narração e montagem).", "deixa tudo pronto para montar o filme na JSON2Video.")

# ── 5. narração + montagem + andamento: JSON2Video ────────────────────────────────────────────────────────────────
xn, yn = nos["🛠️ Oficina: narra o anúncio"]["position"]
xm, ym = nos["🛠️ Oficina: monta o anúncio"]["position"]
xc, yc = nos["🛠️ Oficina: como está?"]["position"]
for velho in ("🛠️ Oficina: narra o anúncio", "🧩 Monta o pedido de montagem", "🚦 Narração ok?", "🛠️ Oficina: monta o anúncio", "🛠️ Oficina: como está?"):
    apaga(velho)
troca("💾 Status: narrando", "value", "detalhe: 'Voz '", "detalhe: 'Mandando para a JSON2Video · voz '")
no("🧩 Monta o filme (JSON2Video)", "n8n-nodes-base.code", 2, [xn, yn], {"jsCode": js("monta_filme.js")})
no("🎬 JSON2Video: cria o vídeo", "n8n-nodes-base.httpRequest", 4.2, [xn - 320, yn], {
    "method": "POST", "url": "https://api.json2video.com/v2/movies", "authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth",
    "sendBody": True, "specifyBody": "json", "jsonBody": "={{ $json.corpo }}", "options": {"response": {"response": {"neverError": True}}, "timeout": 60000}},
    credentials=CRED_J2V, onError="continueErrorOutput", retryOnFail=True, maxTries=3, waitBetweenTries=3000)
no("🧩 Guarda os projetos", "n8n-nodes-base.code", 2, [xm, ym], {"jsCode": js("guarda_projetos.js")}, onError="continueErrorOutput")
for nome, campo, dx in (("🎬 JSON2Video: como está o narrado?", "narrado", 0), ("🎬 JSON2Video: como está o só música?", "musica", -320)):
    no(nome, "n8n-nodes-base.httpRequest", 4.2, [xc + dx, yc], {
        "url": "=https://api.json2video.com/v2/movies?project={{ $('🧩 Guarda os projetos').first().json." + campo + " || $('🧩 Guarda os projetos').first().json.narrado }}",
        "authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth",
        "options": {"response": {"response": {"neverError": True}}, "timeout": 60000}}, credentials=CRED_J2V, onError="continueRegularOutput")
nos["🧩 Atualiza o andamento"]["parameters"]["jsCode"] = js("atualiza_andamento.js")
nos["🧩 Atualiza o andamento"]["position"] = [xc - 640, yc]
nos["⏳ Espera 6 segundos"]["parameters"]["amount"] = 8
nos["⏳ Espera 6 segundos"]["name"] = "⏳ Espera 8 segundos"
nos["⏳ Espera 8 segundos"] = nos.pop("⏳ Espera 6 segundos")
con["⏳ Espera 8 segundos"] = con.pop("⏳ Espera 6 segundos")
for saidas in con.values():
    for lista in saidas.get("main", []):
        for c in lista:
            if c["node"] == "⏳ Espera 6 segundos":
                c["node"] = "⏳ Espera 8 segundos"
desliga_tudo("💾 Status: narrando")
liga("💾 Status: narrando", "🧩 Monta o filme (JSON2Video)")
liga("🧩 Monta o filme (JSON2Video)", "🎬 JSON2Video: cria o vídeo")
liga("🎬 JSON2Video: cria o vídeo", "🧩 Guarda os projetos", 0)
liga("🎬 JSON2Video: cria o vídeo", "⚠️ Marca erro", 1)
liga("🧩 Guarda os projetos", "⏳ Espera 8 segundos", 0)
liga("🧩 Guarda os projetos", "⚠️ Marca erro", 1)
desliga_tudo("⏳ Espera 8 segundos")
liga("⏳ Espera 8 segundos", "🎬 JSON2Video: como está o narrado?")
liga("🎬 JSON2Video: como está o narrado?", "🎬 JSON2Video: como está o só música?")
liga("🎬 JSON2Video: como está o só música?", "🧩 Atualiza o andamento")

# ── 6. página pública: a capa vai para o Redis (30 dias, prévia no WhatsApp); os vídeos ficam na JSON2Video (7 dias) ─
xg, yg = nos["🛠️ Oficina: guarda a página"]["position"]
apaga("🛠️ Oficina: guarda a página")
no("🌐 Baixa a capa", "n8n-nodes-base.httpRequest", 4.2, [xg, yg], {
    "url": "={{ $('🧩 Atualiza o andamento').first().json.capa }}", "options": {"response": {"response": {"responseFormat": "file"}}, "timeout": 120000}},
    onError="continueRegularOutput", retryOnFail=True, maxTries=2, waitBetweenTries=3000)
no("🧩 Prepara a capa", "n8n-nodes-base.code", 2, [xg + 320, yg + 200], {"jsCode": js("guarda_capa.js")})
no("💾 Guarda a capa (30 dias)", "n8n-nodes-base.redis", 1, [xg + 640, yg + 200], {
    "operation": "set", "key": "=anvj2v:foto:{{ $json.ok ? $json.id : 'sem-capa' }}", "value": "={{ $json.b64 || '' }}", "keyType": "string", "expire": True, "ttl": 2592000},
    credentials=copy.deepcopy(REDIS), onError="continueRegularOutput")
nos["🧩 Prepara a página"]["parameters"]["jsCode"] = js("prepara_pagina.js")
troca("📤 Entrega o andamento", "responseBody", "Os vídeos ficam para baixar por 48 horas.", "Baixe os vídeos: o link vale 7 dias.")
nos["🎉 Resultado final"]["parameters"]["jsCode"] = js("resultado_final.js")
# "Ficou pronto?" sim -> guarda arquivos -> página (o "não" segue para o Resultado final, que grava o erro)
m = con["🚦 Ficou pronto?"]["main"]
m[0] = [{"node": "🌐 Baixa a capa", "type": "main", "index": 0}]
liga("🌐 Baixa a capa", "🧩 Prepara a capa")
liga("🧩 Prepara a capa", "💾 Guarda a capa (30 dias)")
liga("💾 Guarda a capa (30 dias)", "🧩 Prepara a página")

# ── 7. notas para quem vai usar ──────────────────────────────────────────────────────────────────────────────────
NOTAS = json.loads((AQUI / "notas.json").read_text(encoding="utf-8"))
for nome, texto in NOTAS.items():
    nos[nome]["parameters"]["content"] = texto
troca("Nota · Comece aqui", "content", "# 🎬 VÍDEO DE ANÚNCIO COM IA (FOTOS → REELS NARRADO)", "# 🎬 VÍDEO DE ANÚNCIO COM IA (FOTOS → REELS NARRADO) · VERSÃO JSON2VIDEO")
troca("Nota · Comece aqui", "content",
      "🛠️ **Oficina de vídeo** (serviço à parte, com ffmpeg): mede as fotos, narra, dá movimento, escreve na tela, mistura a trilha e guarda a página\n🔑 **Precisa de:** credencial do roteador de IA (tipo OpenAI), Redis e a oficina rodando",
      "🎬 **JSON2Video** (API na internet): narra, dá movimento às fotos, escreve na tela, põe legenda e trilha e devolve o MP4 · 💾 as fotos ficam no seu **Redis** · 🌐 **wsrv.nl** faz as miniaturas\n🔑 **Precisa de:** uma IA compatível com OpenAI, Redis e a chave grátis da JSON2Video (veja a nota 🎬 QUEM FAZ O VÍDEO). **Não precisa de servidor de vídeo.**")
troca("Nota · Comece aqui", "content", "🛠️ oficina de vídeo · ", "🎬 JSON2Video · ")
troca("Nota · Comece aqui", "content", "## ▶️ COMO USAR (pela página)",
      "## 🧰 ANTES DE USAR NO SEU n8n\n"
      "1️⃣ **IA**: nos 6 nodes 🧠 e nos 6 🛟 escolha a SUA credencial OpenAI (ou de um roteador compatível) e, em **Model**, um modelo que ela tenha (ex.: `gpt-4o-mini`). No node 👀 **IA olha as fotos** troque o endereço por `https://api.openai.com/v1/chat/completions`, escolha a mesma credencial e, no 🧩 **Prepara as fotos para a IA**, troque o `model` por um modelo com visão (ex.: `gpt-4o-mini`). ⚠️ Não deixe o endereço que veio no fluxo: suas chaves e as fotos dos clientes iriam para o servidor de outra pessoa.\n"
      "2️⃣ **Redis**: crie uma credencial Redis (Redis Cloud tem plano grátis) e escolha ela em todos os nodes 📖 e 💾.\n"
      "3️⃣ **Endereço público**: o seu n8n precisa abrir pela internet em **https** (a API de vídeo e o wsrv.nl baixam as fotos por ele). n8n local no PC não funciona; em servidor próprio, configure `WEBHOOK_URL`.\n"
      "4️⃣ **Ative o fluxo** (botão **Active/Publish** lá em cima): sem isso as páginas dão erro 404.\n"
      "5️⃣ Se algum node 🧩 der erro `crypto is not defined`, o seu n8n precisa liberar o módulo: variável `NODE_FUNCTION_ALLOW_BUILTIN=crypto`.\n\n"
      "## ▶️ COMO USAR (pela página)")
# ── conferências: nada aponta para a oficina, toda ligação vai para um nó que existe ──────────────────────────────
tudo = json.dumps(w, ensure_ascii=False)
for proibido in ("video-oficina", "/videos/", "Oficina:", "__PASSE__", "Gera o passe"):
    if proibido in tudo:
        raise SystemExit(f"sobrou referência: {proibido}")
for de, saidas in con.items():
    assert de in nos, de
    for lista in saidas.get("main", []):
        for c in lista:
            assert c["node"] in nos, (de, c["node"])
for n in w["nodes"]:
    if n["type"] == "n8n-nodes-base.code":
        for ref in re.findall(r"\$\('([^']+)'\)", n["parameters"]["jsCode"]):
            assert ref in nos, (n["name"], ref)
    for ref in re.findall(r"\$\('([^']+)'\)", json.dumps(n["parameters"], ensure_ascii=False)):
        assert ref in nos, (n["name"], ref)
(AQUI / "fluxo_v1.json").write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok:", len(w["nodes"]), "nós,", sum(len(l) for s in con.values() for l in s.get("main", [])), "ligações")
