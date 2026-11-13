# -*- coding: utf-8 -*-
"""🎥 Clipes de vídeo por IA grátis (LTX-Video no Hugging Face, sem chave) — o "Veo grátis", com qualidade menor.
GET /webhook/gratis-clipe (página), POST /webhook/gratis-clipe (responde já com o código e gera depois),
GET /webhook/gratis-clipe-status?id=... (andamento), GET /webhook/gratis-clipe-arquivo?id=..."""
import sys
from pathlib import Path

AQUI = Path(__file__).parent
COMUM = AQUI.parent / "comum"
sys.path.insert(0, str(AQUI.parent))
from n8nlib import Fluxo, js  # noqa: E402

ler = lambda n: (COMUM / n).read_text(encoding="utf-8")  # noqa: E731
f = Fluxo("🎥 Clipes de vídeo IA grátis sem chave (LTX-Video no Hugging Face) — estilo Veo + ou - ok")
f.nota("## 🎥 Clipes de vídeo por IA (grátis)\nAbra **/webhook/gratis-clipe**. Texto → vídeo ou foto → vídeo, 2 a 5 s.\n\n"
       "Motor: **LTX-Video distilled** (Space público do Hugging Face, sem chave). Qualidade abaixo do Veo; a cota "
       "grátis por IP acaba depois de alguns clipes (aí responde \"cota acabou, tente mais tarde\").\n\n"
       "O pedido responde **na hora** com um código e a página consulta **/webhook/gratis-clipe-status?id=...** "
       "até ficar pronto (conexão longa o navegador derrubava). A espera longa fica nos nós HTTP (o Code do n8n "
       "para em 60 s). O MP4 fica no Redis por 7 dias.",
       (-40, -420), 560, 320, 4)
g = f.webhook("🔔 Página dos clipes (GET)", "gratis-clipe", (0, 0))
p = f.codigo("🧩 Monta a página", js(AQUI, "pagina.js", PAGINA=ler("pagina.js")), (240, 0))
rp = f.responde("📤 Entrega a página", "={{ $json.html }}", (480, 0))
f.cadeia(g, p, rp)

# O pedido responde NA HORA com o código; a página consulta o andamento. (Com a conexão aberta até 3 min, o
# navegador às vezes desistia no meio — "Failed to fetch", 499 no proxy — e o clipe pronto se perdia.)
ST = "=gclip:st:{{ $('🧩 Confere o pedido').first().json.id }}"
w = f.webhook("🔔 Pedido de clipe (POST)", "gratis-clipe", (0, 280), "POST")
cf = f.codigo("🧩 Confere o pedido", js(AQUI, "confere.js"), (240, 280))
ok = f.se("🚦 Pedido ok?", "={{ $json.ok }}", (480, 280))
recusa = f.responde_json("📤 Recusa o pedido", "{ ok: false, erro: $json.erro }", (720, 520), status=400)
gerando = f.redis_grava("💾 Andamento: gerando", ST, "={{ JSON.stringify({ etapa: 'gerando' }) }}", (720, 280),
                        validade=604800)
ja = f.responde_json("📤 Responde já com o código", "{ ok: true, id: $('🧩 Confere o pedido').first().json.id, "
                     "status: $('🧩 Confere o pedido').first().json.status }", (960, 280))
pr = f.codigo("🧩 Prepara o pedido", js(AQUI, "prepara.js", TEXTO=ler("texto.js")), (1200, 280))
foto = f.se("🚦 Tem foto?", "={{ $json.tem_foto }}", (1440, 280))
sobe = f.http_envia_arquivo("🌐 Sobe a foto", "https://lightricks-ltx-video-distilled.hf.space/gradio_api/upload", (1680, 200))
monta = f.codigo("🧩 Monta o pedido", js(AQUI, "monta_pedido.js", GRADIO=ler("gradio.js")), (1920, 280))
ok2 = f.se("🚦 Pedido montado?", "={{ $json.ok }}", (2160, 280))
pede = f.http("🌐 Pede o clipe", "={{ $json.url_chamada }}", (2400, 260), metodo="POST",
              corpo_json="={{ JSON.stringify($json.corpo) }}", tempo=30000, nunca_erro=True, continua_no_erro=True)
espera = f.http("🌐 Espera o clipe (até 10 min)",
                "={{ $('🧩 Monta o pedido').first().json.url_chamada }}/{{ $json.event_id || 'sem-evento' }}",
                (2640, 260), formato="text", tempo=600000, nunca_erro=True, continua_no_erro=True)
le = f.codigo("🧩 Lê o resultado", js(AQUI, "le_resultado.js", GRADIO=ler("gradio.js")), (2880, 260))
saiu = f.se("🚦 Saiu o vídeo?", "={{ $json.ok }}", (3120, 260))
guarda = f.redis_grava("💾 Guarda o clipe (7 dias)", "=gclip:{{ $json.id }}.mp4", "={{ $json.b64 }}", (3360, 180),
                       validade=604800)
resp = f.redis_grava("💾 Andamento: pronto", ST,
                     "={{ JSON.stringify({ etapa: 'pronto', url: $('🧩 Lê o resultado').first().json.base + "
                     "'/webhook/gratis-clipe-arquivo?id=' + $('🧩 Lê o resultado').first().json.id + '.mp4', "
                     "bytes: $('🧩 Lê o resultado').first().json.bytes, "
                     "prompt_usado: $('🧩 Lê o resultado').first().json.prompt_usado }) }}", (3600, 180), validade=604800)
# cota: a cota grátis do Hugging Face é por IP; com "cota" a página tenta de novo direto do navegador (IP de quem usa)
erro = f.redis_grava("💾 Andamento: erro", ST, "={{ JSON.stringify({ etapa: 'erro', erro: $json.erro || 'falhou', "
                     "cota: /cota/.test($json.erro || ''), prompt: $('🧩 Prepara o pedido').first().json.prompt, "
                     "prompt_usado: $('🧩 Prepara o pedido').first().json.prompt_usado }) }}",
                     (3360, 400), validade=604800)
f.cadeia(w, cf, ok)
f.liga(ok, gerando, 0)
f.liga(ok, recusa, 1)
f.cadeia(gerando, ja, pr, foto)

st = f.webhook("🔔 Andamento do clipe (GET)", "gratis-clipe-status", (0, 900))
ls = f.redis_le("📖 Lê o andamento", "=gclip:st:{{ String($json.query.id || '').toLowerCase().replace(/[^a-z0-9]/g, '') }}",
                "st", (240, 900))
rs = f.responde("📤 Responde o andamento", "={{ $json.st || JSON.stringify({ etapa: 'desconhecido' }) }}", (480, 900),
                tipo="application/json; charset=UTF-8")
f.cadeia(st, ls, rs)
f.liga(foto, sobe, 0)
f.liga(foto, monta, 1)
f.cadeia(sobe, monta, ok2)
f.liga(ok2, pede, 0)
f.liga(ok2, erro, 1)
f.cadeia(pede, espera, le, saiu)
f.liga(saiu, guarda, 0)
f.liga(saiu, erro, 1)
f.cadeia(guarda, resp)

a = f.webhook("🔔 Entrega o clipe (GET)", "gratis-clipe-arquivo", (0, 640))
lr = f.redis_le("📖 Lê o clipe", "=gclip:{{ String($json.query.id || '').toLowerCase().replace(/[^a-z0-9.-]/g, '') }}",
                "dado", (240, 640))
va = f.codigo("🧩 Vira arquivo", js(COMUM, "arquivo.js", GATILHO="🔔 Entrega o clipe (GET)"), (480, 640))
ex = f.se("🚦 O clipe existe?", "={{ $json.existe }}", (720, 640))
ea = f.responde_arquivo("📤 Entrega o clipe", (960, 560), cache="public, max-age=604800")
nf = f.responde("📤 Clipe não encontrado", "Clipe não encontrado (os links valem 7 dias).", (960, 740),
                tipo="text/plain; charset=UTF-8", status=404)
f.cadeia(a, lr, va, ex)
f.liga(ex, ea, 0)
f.liga(ex, nf, 1)
print(f.grava(AQUI / "clipes_gratis.json"))
