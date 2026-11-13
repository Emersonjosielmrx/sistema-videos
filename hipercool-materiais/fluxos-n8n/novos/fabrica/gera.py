# -*- coding: utf-8 -*-
"""🎬 Fábrica de vídeos grátis sem chave: tema → roteiro (Pollinations) → imagens (FLUX/Pollinations) → voz neural
(Bing) → vídeo (16:9 no montador grátis do Hugging Face; 9:16 montado no navegador de quem abre a página).

GET  /webhook/gratis-video              formulário
POST /webhook/gratis-video              começa (responde {ok, link})
GET  /webhook/gratis-video-ver?id=      andamento + resultado (+ montador do navegador)
GET  /webhook/gratis-video-status?id=   status em JSON
GET  /webhook/gratis-video-arquivo?id=  imagens, voz e vídeo (Redis, 3 dias)
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).parent
COMUM = AQUI.parent / "comum"
sys.path.insert(0, str(AQUI.parent))
from n8nlib import Fluxo, js  # noqa: E402

ler = lambda n: (COMUM / n).read_text(encoding="utf-8")  # noqa: E731
CP = "$('🧩 Confere o pedido').first().json"
TTL = 259200  # 3 dias
f = Fluxo("🎬 Fábrica de vídeos grátis sem chave (tema → roteiro → imagens → voz → vídeo)")


def status(nome, etapa, detalhe, pct, pos):
    valor = ("={{ JSON.stringify({ job: %s.job, tema: %s.tema, modo: %s.modo, etapa: '%s', detalhe: %s, pct: %d }) }}"
             % (CP, CP, CP, etapa, json.dumps(detalhe, ensure_ascii=False), pct))
    n = f.redis_grava(nome, "=gv:{{ %s.job }}" % CP, valor, pos, validade=TTL)
    f.nos[-1]["executeOnce"] = True
    return n


f.nota("## 🎬 Fábrica de vídeos grátis\nAbra **/webhook/gratis-video**: tema → roteiro → imagens → voz → vídeo.\n\n"
       "Tudo grátis e sem chave: roteiro na IA do **Pollinations** (1 resposta a cada 30 s por IP), imagens no "
       "**FLUX do Hugging Face** (reserva Pollinations), voz neural do **Bing Tradutor** (só vozes aprovadas), "
       "montagem 16:9 no Space **Tim13ekd/video-ffmpeg** (1280x720) ou 9:16 **no navegador** de quem abre o "
       "resultado (canvas + gravador do próprio navegador).\n\nArquivos e status no Redis por 3 dias. Até 12 vídeos "
       "por hora. O Code do n8n para em 60 s: por isso as imagens vão uma por vez e a montagem espera em nó HTTP.",
       (-60, -520), 640, 400, 4)

# página
g = f.webhook("🔔 Página da fábrica (GET)", "gratis-video", (0, 0))
pg = f.codigo("🧩 Monta a página", js(AQUI, "pagina.js", PAGINA=ler("pagina.js")), (240, 0))
f.cadeia(g, pg, f.responde("📤 Entrega a página", "={{ $json.html }}", (480, 0)))

# pedido
w = f.webhook("🔔 Pedido de vídeo (POST)", "gratis-video", (0, 300), "POST")
cf = f.codigo("🧩 Confere o pedido", js(AQUI, "confere.js"), (240, 300))
ok = f.se("🚦 Pedido ok?", "={{ $json.ok }}", (480, 300))
rec = f.responde_json("📤 Recusa o pedido", "{ ok: false, erro: %s.erro || 'Muitos vídeos nesta hora. Tente daqui a pouco.' }"
                      % CP, (960, 520), status=400)
conta = f.redis_conta("🧮 Conta pedidos da hora", "={{ $json.chave_limite }}", (720, 300))
pode = f.se("🚦 Pode começar?", "={{ Number(Object.values($json)[0]) <= 12 }}", (960, 300))
st0 = status("💾 Status: recebido", "recebido", "Pedido recebido", 5, (1200, 220))
resp = f.responde_json("📤 Responde com o link", "{ ok: true, job: %s.job, link: %s.link }" % (CP, CP), (1440, 220))
st1 = status("💾 Status: roteiro", "roteiro", "A IA grátis está escrevendo o roteiro", 12, (1680, 220))
r1 = f.codigo("🧠 Escreve o roteiro", js(AQUI, "roteiro.js", TEXTO=ler("texto.js"), WIKI=ler("wiki.js")), (1920, 220))
ok1 = f.se("🚦 Roteiro ok?", "={{ $json.ok }}", (2160, 220))
esp = f.espera("⏳ Espera 35 s (limite da IA grátis)", 35, (2400, 420))
r2 = f.codigo("🧠 Escreve o roteiro (2ª tentativa)", js(AQUI, "roteiro.js", TEXTO=ler("texto.js"), WIKI=ler("wiki.js")),
              (2640, 420))
ok2 = f.se("🚦 Roteiro ok? (2ª)", "={{ $json.ok }}", (2880, 420))
esp_rev = f.espera("⏳ Espera 31 s (antes da revisão)", 31, (2400, 60))
rev = f.codigo("🔎 Revisa os fatos", js(AQUI, "revisao.js", TEXTO=ler("texto.js")), (2640, 60))
erro = f.redis_grava("⚠️ Marca erro", "=gv:{{ %s.job }}" % CP,
                     "={{ JSON.stringify({ job: %s.job, tema: %s.tema, etapa: 'erro', erro: String($json.erro || "
                     "'Falha inesperada').slice(0, 300) }) }}" % (CP, CP), (3120, 620), validade=TTL)
f.nos[-1]["executeOnce"] = True
st2 = status("💾 Status: imagens", "imagens", "Gerando as imagens das cenas (uma por vez)", 30, (2640, 140))
cenas = f.codigo("🧩 Separa as cenas", js(AQUI, "cenas.js"), (2880, 140))
laco = f.lote("🔁 Uma cena por vez", (3120, 140))
gi = f.codigo("🖼️ Gera a imagem da cena", js(AQUI, "gera_cena.js", IMAGEM=ler("gradio.js") + ler("imagem.js")), (3360, 300))
saiu = f.se("🚦 Saiu a imagem?", "={{ $json.ok }}", (3600, 300))
gimg = f.redis_grava("💾 Guarda a imagem (3 dias)", "=gvf:{{ $json.job }}-img{{ $json.n }}.{{ $json.ext }}", "={{ $json.b64 }}",
                     (3840, 220), validade=TTL)
res = f.codigo("🧹 Resumo da cena", js(AQUI, "resumo_cena.js"), (4080, 300))
st3 = status("💾 Status: narrando", "narrando", "Narrando com voz neural", 65, (3360, -60))
nar = f.codigo("🎙️ Narra o roteiro", js(AQUI, "narra.js", VOZ=ler("voz.js")), (3360, 60))
okv = f.se("🚦 Saiu a voz?", "={{ $json.ok }}", (3600, 60))
gvoz = f.redis_grava("💾 Guarda a voz (3 dias)", "=gvf:{{ %s.job }}-voz.mp3" % CP, "={{ $json.b64 }}", (3840, -20), validade=TTL)
nuvem = f.se("🚦 Montar na nuvem (16:9)?", "={{ %s.modo === 'nuvem' }}" % CP, (4080, -20))
st4 = status("💾 Status: montando", "montando", "Montando o vídeo no montador grátis do Hugging Face", 80, (4320, -160))
prep = f.codigo("🧩 Prepara os arquivos", js(AQUI, "prepara_arquivos.js"), (4560, -160))
envia = f.http_envia_arquivo("🌐 Sobe os arquivos ao montador", "https://tim13ekd-video-ffmpeg.hf.space/gradio_api/upload",
                             (4800, -160))
sobe = f.codigo("🧩 Monta o pedido da montagem", js(AQUI, "sobe_montador.js", GRADIO=ler("gradio.js")), (5040, -160))
subiu = f.se("🚦 Subiu?", "={{ $json.ok }}", (5280, -160))
pede = f.http("🌐 Pede a montagem", "={{ $json.url_chamada }}", (5520, -240), metodo="POST",
              corpo_json="={{ JSON.stringify($json.corpo) }}", tempo=30000, nunca_erro=True, continua_no_erro=True)
espera = f.http("🌐 Espera a montagem (até 10 min)",
                "={{ $('🧩 Monta o pedido da montagem').first().json.url_chamada }}/{{ $json.event_id || 'sem-evento' }}",
                (5760, -240), formato="text", tempo=600000, nunca_erro=True, continua_no_erro=True)
lv = f.codigo("🧩 Lê o vídeo", js(AQUI, "le_video.js", GRADIO=ler("gradio.js")), (6000, -240))
okvid = f.se("🚦 Saiu o vídeo?", "={{ $json.ok }}", (6240, -240))
gvid = f.redis_grava("💾 Guarda o vídeo (3 dias)", "=gvf:{{ %s.job }}-video.mp4" % CP, "={{ $json.b64 }}", (6480, -320),
                     validade=TTL)
fim = f.codigo("🧩 Resultado final", js(AQUI, "final.js"), (6720, -20))
st5 = f.redis_grava("💾 Status: pronto", "=gv:{{ %s.job }}" % CP, "={{ JSON.stringify($json) }}", (6960, -20), validade=TTL)

f.cadeia(w, cf, ok)
f.liga(ok, conta, 0)
f.liga(ok, rec, 1)
f.liga(conta, pode)
f.liga(pode, st0, 0)
f.liga(pode, rec, 1)
f.cadeia(st0, resp, st1, r1, ok1)
f.liga(ok1, esp_rev, 0)
f.liga(ok1, esp, 1)
f.cadeia(esp, r2, ok2)
f.liga(ok2, esp_rev, 0)
f.liga(ok2, erro, 1)
f.cadeia(esp_rev, rev, st2, cenas, laco)
f.liga(laco, st3, 0)     # terminou o loop: status primeiro, depois a narração com todas as cenas
f.liga(laco, nar, 0)
f.liga(laco, gi, 1)
f.cadeia(gi, saiu)
f.liga(saiu, gimg, 0)
f.liga(saiu, res, 1)
f.cadeia(gimg, res, laco)
f.cadeia(nar, okv)
f.liga(okv, gvoz, 0)
f.liga(okv, erro, 1)
f.cadeia(gvoz, nuvem)
f.liga(nuvem, st4, 0)
f.liga(nuvem, fim, 1)
f.cadeia(st4, prep, envia, sobe, subiu)
f.liga(subiu, pede, 0)
f.liga(subiu, fim, 1)
f.cadeia(pede, espera, lv, okvid)
f.liga(okvid, gvid, 0)
f.liga(okvid, fim, 1)
f.cadeia(gvid, fim, st5)

# andamento / status / arquivos
v = f.webhook("🔔 Página do vídeo (GET)", "gratis-video-ver", (0, 900))
pv = f.codigo("🧩 Monta a página do vídeo", js(AQUI, "ver.js", PAGINA=ler("pagina.js")), (240, 900))
f.cadeia(v, pv, f.responde("📤 Entrega a página do vídeo", "={{ $json.html }}", (480, 900)))
s = f.webhook("🔔 Consulta status (GET)", "gratis-video-status", (0, 1100))
ls = f.redis_le("📖 Lê o status", "=gv:{{ String($json.query.id || '').toLowerCase().replace(/[^a-z0-9]/g, '') }}", "status",
                (240, 1100))
f.cadeia(s, ls, f.responde("📤 Responde o status", "={{ $json.status || JSON.stringify({ etapa: 'desconhecido' }) }}",
                            (480, 1100), tipo="application/json; charset=UTF-8"))
a = f.webhook("🔔 Entrega arquivo (GET)", "gratis-video-arquivo", (0, 1300))
la = f.redis_le("📖 Lê o arquivo", "=gvf:{{ String($json.query.id || '').toLowerCase().replace(/[^a-z0-9.-]/g, '') }}", "dado",
                (240, 1300))
va = f.codigo("🧩 Vira arquivo", js(COMUM, "arquivo.js", GATILHO="🔔 Entrega arquivo (GET)"), (480, 1300))
ex = f.se("🚦 O arquivo existe?", "={{ $json.existe }}", (720, 1300))
f.cadeia(a, la, va, ex)
f.liga(ex, f.responde_arquivo("📤 Entrega o arquivo", (960, 1220), cache="public, max-age=259200"), 0)
f.liga(ex, f.responde("📤 Arquivo não encontrado", "Arquivo não encontrado (os links valem 3 dias).", (960, 1400),
                      tipo="text/plain; charset=UTF-8", status=404), 1)
print(f.grava(AQUI / "fabrica_videos_gratis.json"))
