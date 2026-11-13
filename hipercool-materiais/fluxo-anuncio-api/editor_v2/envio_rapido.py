"""Envio rápido do vídeo nas cópias V2/V3/V4 (02/11): o cliente via "falha de conexão" porque o navegador dele
desiste do pedido que demora alguns segundos sem resposta (traefik 499; só o 🧩 Confere o vídeo levava 3,6 s num vídeo
de 2 MB, e a página levava até 3,5 s no 🧾 Monta a página). Agora:
- a página é entregue direto pelo 📤 (sem nó de código) — sai na hora;
- a página cria o código do vídeo (12 letras hex) e manda junto; o n8n responde "chegou" logo que recebe e guarda o
  vídeo no armazenamento do ffmpeg depois; a página pergunta o andamento em /<rota>-video-status?id=;
- se a conexão cair, a página confere o andamento e manda de novo sozinha (até 5 vezes); o botão Editar também tenta 3x.
Usado por gera_versoes.py: aplica(w, nivel)."""
import re, json, uuid

PAGINA_ENVIA = r"""  function novoId() { var a = new Uint8Array(6); window.crypto.getRandomValues(a); return Array.prototype.map.call(a, function (b) { return ('0' + b.toString(16)).slice(-2); }).join(''); }
  var envioAtual = null;
  function envia(arq) {
    if (arq.size > 120e6) { el('#info').textContent = '⚠️ Vídeo maior que 120 MB.'; return; }
    el('#prev').src = URL.createObjectURL(arq); el('#prev').hidden = false;
    var id = novoId(), vez = 0, meu = {}; envioAtual = meu;
    enviando = true; VIDEO = ''; el('#barra').hidden = false; el('#barra i').style.width = '0%'; el('#info').textContent = 'Enviando…';
    var fim = function (ok, msg) { if (envioAtual !== meu) return; enviando = false;
      el('#info').innerHTML = ok ? '<span class="ok">✅ Vídeo pronto para editar</span> (' + Math.max(1, Math.round(arq.size / 1e6)) + ' MB)' : '';
      if (!ok) el('#info').textContent = '⚠️ ' + msg; if (ok) VIDEO = id; };
    // a conexão caiu: antes de mandar de novo, confere se o vídeo já tinha chegado
    var caiu = function (motivo) { if (envioAtual !== meu) return;
      if (++vez >= 5) return fim(false, motivo + '. Confira a internet e escolha o vídeo de novo.');
      el('#info').textContent = '⚠️ ' + motivo + ' — tentando de novo (' + (vez + 1) + '/5)…';
      setTimeout(function () { andamento(0, true); }, 1500 * vez); };
    var manda = function () { if (envioAtual !== meu) return;
      var fd = new FormData(); fd.append('video', arq, arq.name || 'video.mp4');
      var x = new XMLHttpRequest(); x.open('POST', '__ROTA__-video?id=' + id);
      x.upload.onprogress = function (e) { if (e.lengthComputable && envioAtual === meu) { var p = Math.round(e.loaded / e.total * 100); el('#barra i').style.width = p + '%'; el('#info').textContent = 'Enviando ' + p + '%' + (p === 100 ? ' · guardando…' : ''); } };
      x.onload = function () { var r = {}; try { r = JSON.parse(x.responseText); } catch (e) {}
        if (x.status === 200 && r.ok) andamento(0, false);
        else if (x.status >= 500 || !x.status) caiu('o servidor não respondeu');
        else fim(false, r.erro || 'não deu para enviar'); };
      x.onerror = function () { caiu('a conexão caiu'); };
      x.onabort = x.onerror;
      x.send(fd); };
    // o n8n guarda o vídeo no armazenamento do ffmpeg na nuvem (alguns segundos): pergunta até ficar pronto
    var andamento = function (n, conferindo) { if (envioAtual !== meu) return;
      fetch('__ROTA__-video-status?id=' + id, { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (r) {
        if (envioAtual !== meu) return;
        if (r.pronto) return fim(true);
        if (r.erro) return fim(false, r.erro);
        if (conferindo) return manda();
        el('#info').textContent = 'Guardando o vídeo…';
        if (n < 90) setTimeout(function () { andamento(n + 1, false); }, 2000); else fim(false, 'demorou demais para guardar o vídeo; escolha de novo');
      }).catch(function () { if (conferindo) return manda(); if (n < 90) setTimeout(function () { andamento(n + 1, false); }, 3000); else fim(false, 'a conexão caiu'); }); };
    manda();
  }
"""


def _no(w, nome, tipo, versao, pos, params, nivel, **extra):
    n = {"parameters": params, "name": nome, "type": "n8n-nodes-base." + tipo, "typeVersion": versao, "position": pos,
         "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"editor-v{nivel}|{nome}")), **extra}
    if tipo == "webhook":
        n["webhookId"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"editor-v{nivel}|webhook|{nome}"))
    w["nodes"].append(n)


def _liga(w, de, para, saida=0):
    m = w["connections"].setdefault(de, {}).setdefault("main", [])
    while len(m) <= saida:
        m.append([])
    m[saida] = [c for c in m[saida] if c["node"] != para] + [{"node": para, "type": "main", "index": 0}]


def aplica(w, nivel):
    rota = f"editor-reel-v{nivel}"
    pre = f"ed{nivel}:"
    nos = {n["name"]: n for n in w["nodes"]}
    redis = next(n["credentials"] for n in w["nodes"] if n["type"] == "n8n-nodes-base.redis")
    cab_json = nos["📤 Responde o status"]["parameters"]["options"]["responseHeaders"]

    # ── página entregue direto (sem nó de código) ──
    codigo = nos["🧾 Monta a página"]["parameters"]["jsCode"]
    html = json.loads(codigo[codigo.index("html: ") + 6: codigo.rindex(" } }];")])
    html, k = re.subn(r"  function envia\(arq\) \{.*?\n    x\.send\(fd\);\n  \}\n", lambda m: PAGINA_ENVIA.replace("__ROTA__", rota), html, flags=re.S)
    assert k == 1, "envia() da página não encontrado"
    antes = f"    fetch('{rota}', {{ method: 'POST'"
    assert html.count(antes) == 1
    html = html.replace(antes, f"    (function pede(n) {{ fetch('{rota}', {{ method: 'POST'")
    pega = "    }).catch(function () { el('#erro').textContent = 'Falha de conexão.'; bt.disabled = false; bt.textContent = '✂️ Editar o meu Reel'; });"
    assert html.count(pega) == 1
    html = html.replace(pega, "    }).catch(function () { if (n < 3) { bt.textContent = 'A conexão caiu, tentando de novo…'; setTimeout(function () { pede(n + 1); }, 2000); return; }\n"
                              "      el('#erro').textContent = 'Falha de conexão. Confira a internet e tente de novo.'; bt.disabled = false; bt.textContent = '✂️ Editar o meu Reel'; }); })(0);")
    nos["📤 Entrega a página"]["parameters"]["responseBody"] = html
    w["nodes"] = [n for n in w["nodes"] if n["name"] != "🧾 Monta a página"]
    w["connections"].pop("🧾 Monta a página", None)
    w["connections"]["🔔 Página do editor (GET)"] = {"main": [[{"node": "📤 Entrega a página", "type": "main", "index": 0}]]}
    nos["📤 Entrega a página"]["position"] = [300, 0]

    # ── envio: responde "chegou" na hora e guarda o vídeo depois ──
    ID = "$('🔔 Recebe o vídeo (POST)').first().json.query.id"
    OK_ID = f"/^[a-f0-9]{{12}}$/.test(String({ID} || ''))"
    w["nodes"] = [n for n in w["nodes"] if n["name"] != "📤 Responde o envio"]
    w["connections"].pop("📤 Responde o envio", None)
    for de in list(w["connections"]):
        for saida in w["connections"][de].get("main", []):
            saida[:] = [c for c in saida if c["node"] != "📤 Responde o envio"]
    _no(w, "📤 Responde já: o vídeo chegou", "respondToWebhook", 1.1, [220, 820], {"respondWith": "text",
        "responseBody": f"={{{{ JSON.stringify({OK_ID} ? {{ ok: true, id: {ID} }} : {{ ok: false, erro: 'Atualize a página (F5) e envie de novo.' }}) }}}}",
        "options": {"responseCode": f"={{{{ {OK_ID} ? 200 : 400 }}}}", "responseHeaders": cab_json}}, nivel)
    _no(w, "🚦 Tem o código do vídeo?", "if", 2.2, [440, 820], {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
        "conditions": [{"id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"editor-v{nivel}|cond-id")), "leftValue": f"={{{{ {OK_ID} }}}}", "rightValue": "",
                        "operator": {"type": "boolean", "operation": "true", "singleValue": True}}], "combinator": "and"}, "options": {}}, nivel)
    w["connections"]["🔔 Recebe o vídeo (POST)"] = {"main": [[{"node": "📤 Responde já: o vídeo chegou", "type": "main", "index": 0}]]}
    _liga(w, "📤 Responde já: o vídeo chegou", "🚦 Tem o código do vídeo?")
    _liga(w, "🚦 Tem o código do vídeo?", "🧩 Confere o vídeo")
    for nome, dx in (("🧩 Confere o vídeo", 360), ("🚦 Vídeo ok?", 360)):
        nos[nome]["position"] = [nos[nome]["position"][0] + dx, nos[nome]["position"][1]]
    for nome in ("🎬 Very Good FFmpeg: pede um lugar", "🧩 Junta o vídeo e o lugar", "🌐 Sobe o vídeo", "🧩 Lê o envio", "🚦 Subiu?", "💾 Guarda o endereço (1 hora)"):
        nos[nome]["position"] = [nos[nome]["position"][0] + 360, nos[nome]["position"][1]]
    nos["💾 Guarda o endereço (1 hora)"]["parameters"]["key"] = f"={pre}video:{{{{ {ID} }}}}"
    _no(w, "💾 Guarda o erro do envio", "redis", 1, [2160, 820], {"operation": "set", "key": f"={pre}videoerro:{{{{ {ID} }}}}",
        "value": "={{ $json.erro || 'Não deu para enviar. Tente de novo.' }}", "keyType": "string", "expire": True, "ttl": 3500}, nivel, credentials=redis)
    _liga(w, "🚦 Vídeo ok?", "💾 Guarda o erro do envio", 1)
    _liga(w, "🚦 Subiu?", "💾 Guarda o erro do envio", 1)
    # 03/11: vídeo de 83 MB derrubava o 🧩 Confere o vídeo (getBinaryDataBuffer põe o arquivo inteiro na memória do
    # runner: "Node execution failed") e a página ficava em "Guardando…". Agora o tamanho vem do content-length do
    # envio (sem ler o arquivo) e, se o nó cair mesmo assim, o erro vai para o Redis e a página avisa.
    cv = nos["🧩 Confere o vídeo"]
    antes = "const buf = await this.helpers.getBinaryDataBuffer(0, chave);\nif (buf.length > 120e6)"
    assert cv["parameters"]["jsCode"].count(antes) == 1
    cv["parameters"]["jsCode"] = (cv["parameters"]["jsCode"]
        .replace(antes, "// tamanho pelo cabeçalho do envio: ler o arquivo inteiro derrubava a memória do n8n com vídeo grande\n"
                        "const tam = Number(($('🔔 Recebe o vídeo (POST)').first().json.headers || {})['content-length']) || 0;\nif (tam > 120e6)")
        .replace("tamanho: buf.length,", "tamanho: tam,"))
    assert "buf." not in cv["parameters"]["jsCode"]
    cv["onError"] = "continueErrorOutput"
    w["connections"]["🧩 Confere o vídeo"]["main"].append([{"node": "💾 Guarda o erro do envio", "type": "main", "index": 0}])
    ge = next(n for n in w["nodes"] if n["name"] == "💾 Guarda o erro do envio")
    ge["parameters"]["value"] = "={{ $json.erro || ($json.error ? 'Não deu para guardar o vídeo agora. Tente de novo; se repetir, envie um vídeo menor (até 120 MB).' : 'Não deu para enviar. Tente de novo.') }}"

    # ── andamento do envio (a página pergunta até ficar pronto) ──
    Q = "String($('🔔 Andamento do envio (GET)').first().json.query.id || '').replace(/[^a-f0-9]/g, '').slice(0, 12)"
    _no(w, "🔔 Andamento do envio (GET)", "webhook", 2, [0, 1060], {"path": f"{rota}-video-status", "responseMode": "responseNode", "options": {}}, nivel)
    _no(w, "📖 Lê o endereço do envio", "redis", 1, [300, 1060], {"operation": "get", "propertyName": "url", "key": f"={pre}video:{{{{ {Q} }}}}",
        "keyType": "string", "options": {}}, nivel, credentials=redis, alwaysOutputData=True)
    _no(w, "📖 Lê o erro do envio", "redis", 1, [600, 1060], {"operation": "get", "propertyName": "erro", "key": f"={pre}videoerro:{{{{ {Q} }}}}",
        "keyType": "string", "options": {}}, nivel, credentials=redis, alwaysOutputData=True)
    _no(w, "📤 Responde o andamento do envio", "respondToWebhook", 1.1, [900, 1060], {"respondWith": "text",
        "responseBody": "={{ JSON.stringify({ pronto: !!$('📖 Lê o endereço do envio').first().json.url, erro: $json.erro || '' }) }}",
        "options": {"responseHeaders": cab_json}}, nivel)
    _liga(w, "🔔 Andamento do envio (GET)", "📖 Lê o endereço do envio")
    _liga(w, "📖 Lê o endereço do envio", "📖 Lê o erro do envio")
    _liga(w, "📖 Lê o erro do envio", "📤 Responde o andamento do envio")
    return w
