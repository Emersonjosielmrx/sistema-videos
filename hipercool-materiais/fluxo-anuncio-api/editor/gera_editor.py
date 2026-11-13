"""Gera o fluxo "Editor de Reels com IA": a pessoa envia um vídeo já gravado e recebe um Reel no estilo do nosso
vídeo de produto do Instagram (gancho no topo, tópicos numerados, legenda karaokê, barra de progresso, cartão final,
trilha com ducking, -14 LUFS), com os cortes de pausas e de vícios feitos pelo tempo de cada palavra.
Serviços: Very Good FFmpeg (ffmpeg na nuvem), Deepgram (transcrição), roteador de IA (visão + texto), Redis.
Uso: python gera_editor.py  -> fluxo_editor.json"""
import json, uuid
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
URLS = dict(l.split() for l in (RAIZ / "urls.txt").read_text().splitlines() if len(l.split()) == 2)
TRILHAS = {n: URLS[f"trilhas/{n}.mp3"] for n in ("animado", "calmo", "chill", "elegante", "emocional", "latino", "tropical", "urgente")}
EXEMPLO = URLS["editor/bruto_exemplo.mp4"]
REDIS = {"redis": {"id": "TgnZ028ccZYrorGM", "name": "Redis redis2 (landing pages)"}}
VGF = {"httpHeaderAuth": {"id": (RAIZ / "v3" / "cred_id.txt").read_text().strip(), "name": "Very Good FFmpeg (Bearer)"}}
DG = {"httpHeaderAuth": {"id": (AQUI / "cred_dg.txt").read_text().strip(), "name": "Deepgram (Token)"}}
IA = {"openAiApi": {"id": "9L3A8W0GrI5kEyTG", "name": "roteador 20128 (rápido)"}}
IA_URL = "http://157.173.207.22:20128/v1/chat/completions"
CABECA_JSON = {"entries": [{"name": "Content-Type", "value": "application/json; charset=UTF-8"}, {"name": "Cache-Control", "value": "no-store"}]}
CABECA_HTML = {"entries": [{"name": "Content-Type", "value": "text/html; charset=UTF-8"}, {"name": "Cache-Control", "value": "no-store"}, {"name": "X-Robots-Tag", "value": "noindex"}]}

nos, con = [], {}


def js(nome):
    return (AQUI / nome).read_text(encoding="utf-8").strip() + "\n"


def no(nome, tipo, versao, x, y, params, **extra):
    nos.append({"parameters": params, "name": nome, "type": "n8n-nodes-base." + tipo, "typeVersion": versao, "position": [x, y],
                "id": str(uuid.uuid4()), **extra})
    return nome


def liga(de, para, saida=0):
    m = con.setdefault(de, {}).setdefault("main", [])
    while len(m) <= saida:
        m.append([])
    m[saida].append({"node": para, "type": "main", "index": 0})


def code(nome, x, y, arq, erro=False):
    return no(nome, "code", 2, x, y, {"jsCode": js(arq)}, **({"onError": "continueErrorOutput"} if erro else {}))


def se(nome, x, y, expr):
    return no(nome, "if", 2.2, x, y, {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
        "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ " + expr + " }}", "rightValue": "", "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
        "combinator": "and"}, "options": {}})


def status(nome, x, y, etapa, detalhe):
    return no(nome, "redis", 1, x, y, {"operation": "set", "key": "=edr:{{ $('🧩 Confere o pedido').first().json.job }}",
        "value": "={{ JSON.stringify({ job: $('🧩 Confere o pedido').first().json.job, etapa: '" + etapa + "', detalhe: " + detalhe +
                 ", dados: { titulo: $('🧩 Confere o pedido').first().json.dados.titulo } }) }}",
        "keyType": "string", "expire": True, "ttl": 259200}, credentials=REDIS)


def http(nome, x, y, params, cred=None, erro="continueErrorOutput", tentativas=2):
    extra = {"onError": erro} if erro else {}
    if tentativas > 1:
        extra.update(retryOnFail=True, maxTries=tentativas, waitBetweenTries=3000)
    if cred:
        extra["credentials"] = cred
        params = {"authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth", **params}
    return no(nome, "httpRequest", 4.2, x, y, params, **extra)


def nota(nome, x, y, w, h, cor, texto):
    nos.append({"parameters": {"content": texto, "height": h, "width": w, "color": cor}, "name": nome, "type": "n8n-nodes-base.stickyNote",
                "typeVersion": 1, "position": [x, y], "id": str(uuid.uuid4())})


# ── 0. páginas ───────────────────────────────────────────────────────────────────────────────────────────────────
html_form = (AQUI / "pagina_form.html").read_text(encoding="utf-8").replace("__EXEMPLO__", EXEMPLO)
no("🔔 Página do editor (GET)", "webhook", 2, 0, 0, {"path": "editor-reel", "responseMode": "responseNode", "options": {}}, webhookId=str(uuid.uuid4()))
code_form = "// Entrega a página: a pessoa escolhe o vídeo, ele sobe para o n8n (que repassa ao armazenamento do ffmpeg na nuvem)\n" \
            "// e depois manda o pedido com os dados.\nreturn [{ json: { html: " + json.dumps(html_form, ensure_ascii=False) + " } }];\n"
no("🧾 Monta a página", "code", 2, 300, 0, {"jsCode": code_form})
no("📤 Entrega a página", "respondToWebhook", 1.1, 600, 0, {"respondWith": "text", "responseBody": "={{ $json.html }}", "options": {"responseHeaders": CABECA_HTML}})
liga("🔔 Página do editor (GET)", "🧾 Monta a página")
liga("🧾 Monta a página", "📤 Entrega a página")

html_ver = (AQUI / "pagina_ver.html").read_text(encoding="utf-8")
no("🔔 Página de andamento (GET)", "webhook", 2, 0, 220, {"path": "editor-reel-ver", "responseMode": "responseNode", "options": {}}, webhookId=str(uuid.uuid4()))
no("📤 Entrega o andamento", "respondToWebhook", 1.1, 300, 220, {"respondWith": "text", "responseBody": html_ver, "options": {"responseHeaders": CABECA_HTML}})
liga("🔔 Página de andamento (GET)", "📤 Entrega o andamento")

no("🔔 Consulta status (GET)", "webhook", 2, 0, 440, {"path": "editor-reel-status", "responseMode": "responseNode", "options": {}}, webhookId=str(uuid.uuid4()))
no("📖 Lê o status", "redis", 1, 300, 440, {"operation": "get", "propertyName": "status", "key": "=edr:{{ String($json.query.job || '').replace(/[^a-z0-9]/g, '') }}",
                                           "keyType": "string", "options": {}}, credentials=REDIS, alwaysOutputData=True)
no("📤 Responde o status", "respondToWebhook", 1.1, 600, 440, {"respondWith": "text",
   "responseBody": "={{ $json.status || JSON.stringify({ etapa: 'recebido', detalhe: 'Começando…' }) }}", "options": {"responseHeaders": CABECA_JSON}})
liga("🔔 Consulta status (GET)", "📖 Lê o status")
liga("📖 Lê o status", "📤 Responde o status")

# envio do vídeo: n8n recebe ➜ pede um lugar no armazenamento do ffmpeg ➜ sobe (PUT) ➜ guarda o endereço no Redis (1 h)
Y = 700
no("🔔 Recebe o vídeo (POST)", "webhook", 2, 0, Y, {"httpMethod": "POST", "path": "editor-reel-video", "responseMode": "responseNode",
   "options": {"binaryPropertyName": "video"}}, webhookId=str(uuid.uuid4()))
code("🧩 Confere o vídeo", 300, Y, "confere_video.js")
se("🚦 Vídeo ok?", 600, Y, "$json.ok")
http("🎬 Very Good FFmpeg: pede um lugar", 900, Y - 120, {"method": "POST", "url": "https://verygoodffmpeg.com/api/tmp-file",
     "options": {"response": {"response": {"neverError": True}}, "timeout": 60000}}, cred=VGF, erro="continueRegularOutput")
no("🧩 Junta o vídeo e o lugar", "code", 2, 1050, Y - 240, {"jsCode":
   "// O pedido de lugar devolve só o endereço: aqui o vídeo (binário) volta para o item, junto com o endereço de envio.\n"
   "const r = ($input.first().json || {}).data || {};\n"
   "if (!r.upload_url) return [{ json: { semLugar: true } }];\n"
   "return [{ json: { upload_url: r.upload_url, download_url: r.download_url }, binary: $('🧩 Confere o vídeo').first().binary }];\n"})
http("🌐 Sobe o vídeo", 1200, Y - 120, {"method": "PUT", "url": "={{ $json.upload_url }}", "sendBody": True, "contentType": "binaryData",
     "inputDataFieldName": "video", "options": {"timeout": 600000}}, erro="continueRegularOutput", tentativas=1)
code("🧩 Lê o envio", 1500, Y - 120, "le_tmp.js")
se("🚦 Subiu?", 1650, Y - 120, "$json.ok")
no("💾 Guarda o endereço (1 hora)", "redis", 1, 1800, Y - 120, {"operation": "set", "key": "=edr:video:{{ $json.id }}", "value": "={{ $json.url }}",
   "keyType": "string", "expire": True, "ttl": 3500}, credentials=REDIS)
no("📤 Responde o envio", "respondToWebhook", 1.1, 2100, Y, {"respondWith": "text",
   "responseBody": "={{ JSON.stringify($('🧩 Confere o vídeo').first().json.ok && $('🧩 Lê o envio').isExecuted && $('🧩 Lê o envio').first().json.ok ? { ok: true, id: $('🧩 Lê o envio').first().json.id } : { ok: false, erro: ($('🧩 Lê o envio').isExecuted ? $('🧩 Lê o envio').first().json.erro : $('🧩 Confere o vídeo').first().json.erro) || 'Não deu para enviar.' }) }}",
   "options": {"responseCode": "={{ $('🧩 Confere o vídeo').first().json.ok && $('🧩 Lê o envio').isExecuted && $('🧩 Lê o envio').first().json.ok ? 200 : 400 }}", "responseHeaders": CABECA_JSON}})
liga("🔔 Recebe o vídeo (POST)", "🧩 Confere o vídeo")
liga("🧩 Confere o vídeo", "🚦 Vídeo ok?")
liga("🚦 Vídeo ok?", "🎬 Very Good FFmpeg: pede um lugar", 0)
liga("🚦 Vídeo ok?", "📤 Responde o envio", 1)
liga("🎬 Very Good FFmpeg: pede um lugar", "🧩 Junta o vídeo e o lugar")
liga("🧩 Junta o vídeo e o lugar", "🌐 Sobe o vídeo")
liga("🌐 Sobe o vídeo", "🧩 Lê o envio")
liga("🧩 Lê o envio", "🚦 Subiu?")
liga("🚦 Subiu?", "💾 Guarda o endereço (1 hora)", 0)
liga("🚦 Subiu?", "📤 Responde o envio", 1)
liga("💾 Guarda o endereço (1 hora)", "📤 Responde o envio")

# entrega dos arquivos que o ffmpeg na nuvem lê pelo endereço do n8n (trilhas e o .ass dos textos)
Y = 1000
no("🔔 Entrega um arquivo (GET)", "webhook", 2, 0, Y, {"path": "editor-reel-arquivo", "responseMode": "responseNode", "options": {}}, webhookId=str(uuid.uuid4()))
no("📖 Lê o arquivo", "redis", 1, 300, Y, {"operation": "get", "propertyName": "arquivo",
   "key": "=edr:arq:{{ String($json.query.id || '').replace(/[^a-z0-9.-]/g, '') }}", "keyType": "string", "options": {}}, credentials=REDIS, alwaysOutputData=True)
code_arq = ("// Entrega pelo endereço do próprio n8n: as trilhas (trilha-elegante...) e o arquivo de textos (.ass) de cada edição.\n"
            "// O ffmpeg na nuvem baixa daqui (o catbox derruba downloads de servidores na nuvem).\n"
            "const TRILHAS = " + json.dumps(TRILHAS) + ";\n"
            "const id = String($('🔔 Entrega um arquivo (GET)').first().json.query.id || '');\n"
            "const tr = /^trilha-([a-z]+)$/.exec(id);\n"
            "if (tr && TRILHAS[tr[1]]) {\n"
            "  const d = await this.helpers.httpRequest({ url: TRILHAS[tr[1]], encoding: 'arraybuffer', timeout: 60000 });\n"
            "  return [{ json: { existe: true }, binary: { data: await this.helpers.prepareBinaryData(Buffer.from(d), id + '.mp3', 'audio/mpeg') } }];\n"
            "}\n"
            "if (id === 'exemplo.mp4') {   // o vídeo de exemplo também passa por aqui\n"
            "  const d = await this.helpers.httpRequest({ url: " + json.dumps(EXEMPLO) + ", encoding: 'arraybuffer', timeout: 60000 });\n"
            "  return [{ json: { existe: true }, binary: { data: await this.helpers.prepareBinaryData(Buffer.from(d), id, 'video/mp4') } }];\n"
            "}\n"
            "const b64 =String($input.first().json.arquivo || '');\n"
            "if (!/^textos-[a-z0-9]{6,40}\\.ass$/.test(id) || !b64) return [{ json: { existe: false } }];\n"
            "return [{ json: { existe: true }, binary: { data: await this.helpers.prepareBinaryData(Buffer.from(b64, 'base64'), id, 'text/plain') } }];\n")
no("🧩 Vira arquivo", "code", 2, 600, Y, {"jsCode": code_arq})
se("🚦 Existe?", 900, Y, "$json.existe")
no("📤 Entrega o arquivo", "respondToWebhook", 1.1, 1200, Y - 80, {"respondWith": "binary", "options": {}})
no("📤 Não encontrado", "respondToWebhook", 1.1, 1200, Y + 80, {"respondWith": "text", "responseBody": "não encontrado", "options": {"responseCode": 404}})
liga("🔔 Entrega um arquivo (GET)", "📖 Lê o arquivo")
liga("📖 Lê o arquivo", "🧩 Vira arquivo")
liga("🧩 Vira arquivo", "🚦 Existe?")
liga("🚦 Existe?", "📤 Entrega o arquivo", 0)
liga("🚦 Existe?", "📤 Não encontrado", 1)

# ── 1. pedido ────────────────────────────────────────────────────────────────────────────────────────────────────
Y = 1400
no("🔔 Pedido de edição (POST)", "webhook", 2, 0, Y, {"httpMethod": "POST", "path": "editor-reel", "responseMode": "responseNode", "options": {}}, webhookId=str(uuid.uuid4()))
code("🧩 Confere o pedido", 300, Y, "confere_pedido.js")
no("🧮 Conta pedidos da hora", "redis", 1, 600, Y, {"operation": "incr", "key": "={{ $json.chave_limite }}", "expire": True, "ttl": 3600}, credentials=REDIS)
se("🚦 Pode começar?", 900, Y, "$('🧩 Confere o pedido').first().json.valido && Number(Object.values($json)[0]) <= 30")
no("📤 Recusa o pedido", "respondToWebhook", 1.1, 1200, Y + 160, {"respondWith": "text",
   "responseBody": "={{ JSON.stringify({ ok: false, erros: $('🧩 Confere o pedido').first().json.valido ? ['Muitas edições nesta hora. Tente daqui a pouco.'] : $('🧩 Confere o pedido').first().json.erros }) }}",
   "options": {"responseCode": 400, "responseHeaders": CABECA_JSON}})
status("💾 Status: recebido", 1200, Y, "recebido", "'Pedido conferido'")
no("📤 Responde com o link", "respondToWebhook", 1.1, 1500, Y, {"respondWith": "text",
   "responseBody": "={{ JSON.stringify({ ok: true, link: $('🧩 Confere o pedido').first().json.link }) }}", "options": {"responseHeaders": CABECA_JSON}})
no("📖 Lê o endereço do vídeo", "redis", 1, 1800, Y, {"operation": "get", "propertyName": "url",
   "key": "=edr:video:{{ $('🧩 Confere o pedido').first().json.video_id || 'nenhum' }}", "keyType": "string", "options": {}}, credentials=REDIS, alwaysOutputData=True)
code("🧩 Pega o vídeo", 2100, Y, "pega_video.js", erro=True)
liga("🔔 Pedido de edição (POST)", "🧩 Confere o pedido")
liga("🧩 Confere o pedido", "🧮 Conta pedidos da hora")
liga("🧮 Conta pedidos da hora", "🚦 Pode começar?")
liga("🚦 Pode começar?", "💾 Status: recebido", 0)
liga("🚦 Pode começar?", "📤 Recusa o pedido", 1)
liga("💾 Status: recebido", "📤 Responde com o link")
liga("📤 Responde com o link", "📖 Lê o endereço do vídeo")
liga("📖 Lê o endereço do vídeo", "🧩 Pega o vídeo")

# ── 2. ouvir: áudio + quadro (ffmpeg na nuvem) ➜ Deepgram ─────────────────────────────────────────────────────────
Y = 1700
status("💾 Status: ouvindo", 0, Y, "ouvindo", "'Separando o áudio do vídeo'")
code("🧩 Pede áudio e quadro", 300, Y, "medidas.js")
http("🎬 Very Good FFmpeg: separa o áudio", 600, Y, {"method": "POST", "url": "https://verygoodffmpeg.com/api/ffmpeg", "sendBody": True, "specifyBody": "json",
     "jsonBody": "={{ $json.corpo }}", "options": {"response": {"response": {"neverError": True}}, "timeout": 60000}}, cred=VGF)
no("⏳ Espera 5 segundos", "wait", 1.1, 900, Y, {"amount": 5}, webhookId=str(uuid.uuid4()))
http("🎬 Very Good FFmpeg: separou?", 1200, Y, {"url": "=https://verygoodffmpeg.com/api/jobs/{{ $('🎬 Very Good FFmpeg: separa o áudio').first().json.data.id }}",
     "options": {"response": {"response": {"neverError": True}}, "timeout": 60000}}, cred=VGF, erro="continueRegularOutput")
se("🚦 Separou?", 1500, Y, "!['queued', 'running'].includes(($json.data || {}).status)")
code("🧩 Lê a extração", 1800, Y, "le_extracao.js", erro=True)
http("🌐 Baixa o áudio", 2100, Y, {"url": "={{ $json.audio }}", "options": {"response": {"response": {"responseFormat": "file"}}, "timeout": 120000}})
http("🎧 Deepgram: transcreve", 2400, Y, {"method": "POST", "url": "https://api.deepgram.com/v1/listen?model=nova-3&language=pt-BR&punctuate=true&filler_words=true",
     "sendBody": True, "contentType": "binaryData", "inputDataFieldName": "data", "options": {"timeout": 300000}}, cred=DG)
liga("🧩 Pega o vídeo", "💾 Status: ouvindo", 0)
liga("💾 Status: ouvindo", "🧩 Pede áudio e quadro")
liga("🧩 Pede áudio e quadro", "🎬 Very Good FFmpeg: separa o áudio")
liga("🎬 Very Good FFmpeg: separa o áudio", "⏳ Espera 5 segundos", 0)
liga("⏳ Espera 5 segundos", "🎬 Very Good FFmpeg: separou?")
liga("🎬 Very Good FFmpeg: separou?", "🚦 Separou?")
liga("🚦 Separou?", "🧩 Lê a extração", 0)
liga("🚦 Separou?", "⏳ Espera 5 segundos", 1)
liga("🧩 Lê a extração", "🌐 Baixa o áudio", 0)
liga("🌐 Baixa o áudio", "🎧 Deepgram: transcreve", 0)

# ── 3. direção pela IA ───────────────────────────────────────────────────────────────────────────────────────────
Y = 2000
status("💾 Status: direção", 0, Y, "direcao", "'Ouvi ' + (((($('🎧 Deepgram: transcreve').first().json.results || {}).channels || [{}])[0].alternatives || [{}])[0].words || []).length + ' palavras'")
code("🧩 Prepara o pedido à IA", 300, Y, "prepara_ia.js")
no("🧠 IA diretora", "httpRequest", 4.2, 600, Y, {"method": "POST", "url": IA_URL, "authentication": "predefinedCredentialType", "nodeCredentialType": "openAiApi",
   "sendBody": True, "specifyBody": "json", "jsonBody": "={{ $json.corpo }}", "options": {"timeout": 180000}},
   credentials=IA, onError="continueRegularOutput", retryOnFail=True, maxTries=2, waitBetweenTries=5000)
code("🧩 Lê a direção", 900, Y, "le_direcao.js")
liga("🎧 Deepgram: transcreve", "💾 Status: direção", 0)
liga("💾 Status: direção", "🧩 Prepara o pedido à IA")
liga("🧩 Prepara o pedido à IA", "🧠 IA diretora")
liga("🧠 IA diretora", "🧩 Lê a direção")

# ── 4. edição: monta o comando ➜ textos no Redis ➜ ffmpeg na nuvem ➜ laço ────────────────────────────────────────
Y = 2300
code("🧩 Monta a edição", 0, Y, "monta_edicao.js", erro=True)
status("💾 Status: montando", 300, Y, "montando", "'Cortei ' + $('🧩 Monta a edição').first().json.original + ' s para ' + $('🧩 Monta a edição').first().json.total + ' s'")
no("💾 Guarda os textos (1 dia)", "redis", 1, 600, Y, {"operation": "set", "key": "=edr:arq:textos-{{ $('🧩 Pega o vídeo').first().json.job }}.ass",
   "value": "={{ $('🧩 Monta a edição').first().json.textos }}", "keyType": "string", "expire": True, "ttl": 86400}, credentials=REDIS)
http("🎬 Very Good FFmpeg: edita", 900, Y, {"method": "POST", "url": "https://verygoodffmpeg.com/api/ffmpeg", "sendBody": True, "specifyBody": "json",
     "jsonBody": "={{ $('🧩 Monta a edição').first().json.corpo }}", "options": {"response": {"response": {"neverError": True}}, "timeout": 60000}}, cred=VGF)
no("🧩 Guarda o trabalho", "code", 2, 1200, Y, {"jsCode": "// Guarda o código do trabalho que o ffmpeg na nuvem aceitou.\n"
   "const r = $input.first().json || {};\nif (!(r.data && r.data.id)) throw new Error('O ffmpeg na nuvem recusou a edição: ' + String(r.message || r.errorCode || 'sem resposta').slice(0, 240));\n"
   "return [{ json: { id: r.data.id, inicio: Date.now() } }];\n"}, onError="continueErrorOutput")
no("⏳ Espera 8 segundos", "wait", 1.1, 1500, Y, {"amount": 8}, webhookId=str(uuid.uuid4()))
http("🎬 Very Good FFmpeg: como está?", 1800, Y, {"url": "=https://verygoodffmpeg.com/api/jobs/{{ $('🧩 Guarda o trabalho').first().json.id }}",
     "options": {"response": {"response": {"neverError": True}}, "timeout": 60000}}, cred=VGF, erro="continueRegularOutput")
code("🧩 Atualiza o andamento", 2100, Y, "atualiza_andamento.js")
no("💾 Status: progresso", "redis", 1, 2400, Y, {"operation": "set", "key": "=edr:{{ $('🧩 Pega o vídeo').first().json.job }}",
   "value": "={{ $json.status }}", "keyType": "string", "expire": True, "ttl": 259200}, credentials=REDIS)
se("🚦 Terminou?", 2700, Y, "$('🧩 Atualiza o andamento').first().json.terminou")
code("🎉 Resultado final", 3000, Y, "resultado.js")
no("💾 Status: pronto", "redis", 1, 3300, Y, {"operation": "set", "key": "=edr:{{ $('🧩 Pega o vídeo').first().json.job }}",
   "value": "={{ $json.status }}", "keyType": "string", "expire": True, "ttl": 259200}, credentials=REDIS)
liga("🧩 Lê a direção", "🧩 Monta a edição")
liga("🧩 Monta a edição", "💾 Status: montando", 0)
liga("💾 Status: montando", "💾 Guarda os textos (1 dia)")
liga("💾 Guarda os textos (1 dia)", "🎬 Very Good FFmpeg: edita")
liga("🎬 Very Good FFmpeg: edita", "🧩 Guarda o trabalho", 0)
liga("🧩 Guarda o trabalho", "⏳ Espera 8 segundos", 0)
liga("⏳ Espera 8 segundos", "🎬 Very Good FFmpeg: como está?")
liga("🎬 Very Good FFmpeg: como está?", "🧩 Atualiza o andamento")
liga("🧩 Atualiza o andamento", "💾 Status: progresso")
liga("💾 Status: progresso", "🚦 Terminou?")
liga("🚦 Terminou?", "🎉 Resultado final", 0)
liga("🚦 Terminou?", "⏳ Espera 8 segundos", 1)
liga("🎉 Resultado final", "💾 Status: pronto")

# ── erro: qualquer saída de erro grava o motivo e a página mostra ────────────────────────────────────────────────
no("⚠️ Marca erro", "redis", 1, 3300, 1700, {"operation": "set", "key": "=edr:{{ $('🧩 Confere o pedido').first().json.job }}",
   "value": "={{ JSON.stringify({ job: $('🧩 Confere o pedido').first().json.job, etapa: 'erro', erro: String($json.erro || ($json.error && ($json.error.message || $json.error.description || $json.error)) || $json.message || 'Falha inesperada').slice(0, 300) }) }}",
   "keyType": "string", "expire": True, "ttl": 259200}, credentials=REDIS)
for de in ("🧩 Pega o vídeo", "🎬 Very Good FFmpeg: separa o áudio", "🧩 Lê a extração", "🌐 Baixa o áudio", "🎧 Deepgram: transcreve",
           "🧩 Monta a edição", "🎬 Very Good FFmpeg: edita", "🧩 Guarda o trabalho"):
    liga(de, "⚠️ Marca erro", 1)

# ── notas ────────────────────────────────────────────────────────────────────────────────────────────────────────
nota("Nota · Comece aqui", -1400, -60, 1280, 1180, 6,
"""# ✂️ EDITOR DE REELS COM IA (VÍDEO GRAVADO → REEL PRONTO)

🎯 **O que faz:** a pessoa manda o vídeo que **gravou falando** do produto/serviço (celular, até 1min30) e recebe um **Reel pronto para o Instagram**, no mesmo estilo dos nossos vídeos de produto:
✂️ **corta as pausas** (silêncio maior que meio segundo) e os **vícios** ("né", "é", "ãh", "tipo"...) pelo tempo exato de cada palavra
🔝 **frase de impacto** fixa no topo, na cor da marca · 🔢 **tópicos numerados** que entram quando o assunto muda
💬 **legenda karaokê**: 3 palavras por vez e a palavra falada **acesa** na cor da marca
📏 **barrinha de progresso** no topo · 🎬 zoom leve alternado a cada corte (cara de edição) · 📱 vídeo deitado vira em pé com fundo desfocado
🏷️ **cartão final**: marca, chamada ("Agende sua visita"), @ e "Link no perfil"
🎵 **trilha** que **abaixa** quando a pessoa fala · 🔊 som no padrão do Instagram (**-14 LUFS**)
📣 **legenda do post** pronta, com hashtags

## ▶️ COMO USAR
1️⃣ Abra **/webhook/editor-reel** · 2️⃣ envie o vídeo (ou **🎬 Usar vídeo de exemplo**) · 3️⃣ diga o que é ➜ **✂️ Editar o meu Reel** · 4️⃣ em ~2 min baixe o vídeo e copie a legenda

## 🧰 ANTES DE USAR NO SEU n8n
1️⃣ **Very Good FFmpeg** (ffmpeg na nuvem, **sem marca d'água**): conta grátis em **verygoodffmpeg.com** (entra com Google, **sem cartão**, 2 GB grátis ≈ 100 edições) ➜ **Create API key** ➜ credencial **Header Auth**: nome `Authorization`, valor `Bearer ` + a chave ➜ escolha nos nodes 🎬.
2️⃣ **Deepgram** (ouve cada palavra): conta grátis em **deepgram.com** (Google, **sem cartão**, US$ 200 de crédito ≈ 45 mil minutos) ➜ **Create API key** ➜ credencial **Header Auth**: nome `Authorization`, valor `Token ` + a chave ➜ escolha no node 🎧.
3️⃣ **IA**: no node 🧠 **IA diretora** troque o endereço por `https://api.openai.com/v1/chat/completions` e escolha a SUA credencial OpenAI; no 🧩 **Prepara o pedido à IA** troque o `model` por um com visão (ex.: `gpt-4o-mini`). ⚠️ Não deixe o endereço que veio: suas chaves e os vídeos dos clientes iriam para o servidor de outra pessoa.
4️⃣ **Redis**: credencial Redis (Redis Cloud tem plano grátis) em todos os 📖 e 💾.
5️⃣ O n8n precisa abrir pela internet em **https** e aceitar envio de até ~120 MB (`N8N_PAYLOAD_SIZE_MAX`). **Ative o fluxo** (Active/Publish).

## 🔎 LEGENDA DOS ÍCONES
🔔 recebe um pedido · 📤 responde · 🧩 código · 🚦 decisão · 📖 lê do Redis · 💾 grava no Redis · 🧮 soma · 🎬 ffmpeg na nuvem · 🎧 transcrição · 🧠 IA · 🌐 baixa/sobe arquivo · ⏳ espera""")
nota("Nota · Páginas e envio", -60, -100, 2300, 1260, 7,
"""## 0️⃣ PÁGINAS E ENVIO DO VÍDEO 📄
🔔 **Página do editor** (/webhook/editor-reel): o formulário · 🔔 **Página de andamento** (/webhook/editor-reel-ver?job=...) · 🔔 **Consulta status** lê do Redis.
📤 **Envio**: o navegador manda o vídeo para 🔔 **Recebe o vídeo** ➜ 🎬 **pede um lugar** no armazenamento do ffmpeg na nuvem (vale **1 hora**) ➜ 🌐 **sobe** ➜ 💾 guarda o endereço no Redis ➜ devolve o código do vídeo.
📂 🔔 **Entrega um arquivo** (/webhook/editor-reel-arquivo?id=...): o ffmpeg na nuvem baixa daqui a **trilha** e o arquivo de **textos** (.ass) de cada edição.""")
nota("Nota · Etapas", -60, 1300, 3600, 1340, 4,
"""## 1️⃣ PEDIDO ➜ 2️⃣ OUVIR ➜ 3️⃣ DIREÇÃO ➜ 4️⃣ EDIÇÃO 🔁
1️⃣ 🧩 **Confere o pedido** (no máximo 30 por hora) ➜ responde o link da página de andamento ➜ 🧩 **Pega o vídeo** (o enviado ou o exemplo).
2️⃣ 🎬 **separa o áudio** e tira um **quadro** do vídeo (ffmpeg na nuvem) ➜ 🎧 **Deepgram** devolve **cada palavra com o tempo** e marca os vícios ("né", "é").
3️⃣ 🧠 **IA diretora** lê a fala numerada e olha o quadro: escreve a **frase do topo**, os **tópicos** (com a palavra em que cada um começa), a **chamada** do cartão, a **cor**, a **trilha** e a **legenda do post**.
4️⃣ 🧩 **Monta a edição**: calcula os cortes (pausas e vícios), o novo tempo de cada palavra, escreve os textos (.ass) e UM comando **ffmpeg** ➜ 🎬 **edita** na nuvem ➜ 🔁 laço de 8 s até ficar pronto ➜ 🎉 **Resultado**: vídeo (link vale **7 dias**), capa, o que foi cortado e a legenda do post.
⚠️ Qualquer falha vai para 💾 **Marca erro** e aparece na página.""")

w = {"name": "Editor de Reels com IA · vídeo gravado → Reel pronto (cortes, legenda karaokê, topo, cartão) - ok", "nodes": nos, "connections": con,
     "settings": {"executionOrder": "v1", "saveManualExecutions": True, "executionTimeout": 1500}}
nomes = {n["name"] for n in nos}
assert len(nomes) == len(nos), "nome repetido"
import re
for de, s in con.items():
    assert de in nomes, de
    for lista in s["main"]:
        for c in lista:
            assert c["node"] in nomes, (de, c["node"])
for n in nos:
    for ref in re.findall(r"\$\('([^']+)'\)", json.dumps(n["parameters"], ensure_ascii=False)):
        assert ref in nomes, (n["name"], ref)
(AQUI / "fluxo_editor.json").write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok:", len(nos), "nós")
