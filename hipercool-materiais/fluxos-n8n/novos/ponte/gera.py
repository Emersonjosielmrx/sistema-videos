# -*- coding: utf-8 -*-
"""🌉 Ponte PC ↔ n8n (sem chave e sem abrir porta no PC): o n8n guarda pedidos numa fila no Redis; o trabalhador do PC
(D:\\hipercool-materiais\\fluxos-n8n\\ponte-pc\\trabalhador.py) busca, faz com o que já existe no PC e devolve.

GET  /webhook/ponte-pc                  página (PC online?, mandar pedido, acompanhar)
POST /webhook/ponte-pc/pedido           {acao, dados} + cabeçalho X-Ponte-Token → {id, status_url}
GET  /webhook/ponte-pc/proximo          (o PC) próximo pedido da fila
POST /webhook/ponte-pc/resultado        (o PC) resultado + arquivo opcional (até ~15 MB)
GET  /webhook/ponte-pc/status?id=       situação do pedido
GET  /webhook/ponte-pc/arquivo?id=      arquivo devolvido pelo PC (7 dias)

O token fica em ..\\..\\ponte-pc\\config.json (criado aqui na 1ª vez; o trabalhador lê o mesmo arquivo).
"""
import json
import secrets
import sys
from pathlib import Path

AQUI = Path(__file__).parent
COMUM = AQUI.parent / "comum"
PONTE_PC = AQUI.parents[1] / "ponte-pc"
sys.path.insert(0, str(AQUI.parent))
from n8nlib import REDIS, Fluxo, js  # noqa: E402

ler = lambda n: (COMUM / n).read_text(encoding="utf-8")  # noqa: E731
PONTE_PC.mkdir(exist_ok=True)
cfg_arq = PONTE_PC / "config.json"
cfg = json.loads(cfg_arq.read_text(encoding="utf-8")) if cfg_arq.exists() else {}
cfg.setdefault("n8n", "https://n8n6.inovareinteligenciaartificial.com")
cfg.setdefault("token", secrets.token_hex(16))
cfg.setdefault("maquina", "pc1")
cfg.setdefault("intervalo_s", 20)
cfg.setdefault("acoes_liberadas", ["saude", "imagem_flow", "montar_video", "guardar_para_postar"])
cfg_arq.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
ACOES = {"saude": "Saúde do PC (memória, disco, hora)",
         "imagem_flow": "Imagem no Google Flow / Nano Banana (contas do PC, 0 crédito)",
         "montar_video": "Montar vídeo no ffmpeg do PC (filme da fábrica grátis: vertical ou deitado)",
         "guardar_para_postar": "Guardar vídeo na caixa de saída do PC (os postadores postam com aprovação)"}
T = {"TOKEN": json.dumps(cfg["token"]), "ACOES": json.dumps(ACOES, ensure_ascii=False)}

f = Fluxo("🌉 Ponte PC ↔ n8n (fila para os geradores e postadores do PC, sem chave)")
f.nota("## 🌉 Ponte PC ↔ n8n\nO n8n não alcança o PC (e não deve: nada de porta aberta). Então o PC é que pergunta: o "
       "trabalhador do PC busca o próximo pedido a cada 20 s em **/webhook/ponte-pc/proximo**, faz com o que já existe "
       "lá (Flow/Nano Banana, ffmpeg, caixa de saída dos postadores) e devolve em **/resultado**.\n\nLigar no PC: "
       "`D:\\hipercool-materiais\\fluxos-n8n\\ponte-pc\\LIGAR_PONTE.bat`. Token: `ponte-pc\\config.json`.\n\n"
       "Nada é postado daqui: \"guardar_para_postar\" só deixa o vídeo na caixa de saída para aprovação.",
       (-60, -420), 620, 320, 4)

# página
pg = f.webhook("🔔 Página da ponte (GET)", "ponte-pc", (0, 0))
lv = f.redis_le("📖 Lê o sinal do PC", "ponte:visto", "visto", (240, 0))
mp = f.codigo("🧩 Monta a página", js(AQUI, "pagina.js", PAGINA=ler("pagina.js"), **T), (480, 0))
f.cadeia(pg, lv, mp, f.responde("📤 Entrega a página", "={{ $json.html }}", (720, 0)))

# pedido
pw = f.webhook("🔔 Pedido para o PC (POST)", "ponte-pc/pedido", (0, 260), "POST")
pc = f.codigo("🧩 Confere o pedido", js(AQUI, "pedido.js", **T), (240, 260))
pok = f.se("🚦 Pedido ok?", "={{ $json.ok }}", (480, 260))
gs = f.redis_grava("💾 Status: na fila", "=ponte:job:{{ $json.id }}", "={{ $json.status }}", (720, 180), validade=604800)
fila = f.no("📥 Põe na fila", "n8n-nodes-base.redis", 1,
            {"operation": "push", "list": "ponte:fila", "messageData": "={{ $('🧩 Confere o pedido').first().json.pedido }}",
             "tail": True}, (960, 180), REDIS)
pr = f.responde_json("📤 Responde com o id", "{ ok: true, id: $('🧩 Confere o pedido').first().json.id, "
                     "status_url: $('🧩 Confere o pedido').first().json.status_url }", (1200, 180))
pe = f.responde_json("📤 Recusa o pedido", "{ ok: false, erro: $json.erro }", (720, 360), status=400)
f.cadeia(pw, pc, pok)
f.liga(pok, gs, 0)
f.liga(pok, pe, 1)
f.cadeia(gs, fila, pr)

# o PC pergunta
qw = f.webhook("🔔 O PC pede trabalho (GET)", "ponte-pc/proximo", (0, 560))
qc = f.codigo("🧩 Confere o PC", js(AQUI, "confere_pc.js", **T), (240, 560))
qok = f.se("🚦 Token certo?", "={{ $json.ok }}", (480, 560))
qv = f.redis_grava("💾 Sinal do PC (online)", "ponte:visto", "={{ $json.visto }}", (720, 480), validade=86400)
qp = f.no("📤 Tira da fila", "n8n-nodes-base.redis", 1,
          {"operation": "pop", "list": "ponte:fila", "tail": False, "propertyName": "pedido", "options": {}}, (960, 480), REDIS,
          alwaysOutputData=True)
qe = f.codigo("🧩 Entrega o trabalho", js(AQUI, "entrega_trabalho.js"), (1200, 480))
qtem = f.se("🚦 Tem trabalho?", "={{ !$json.vazio }}", (1440, 480))
qs = f.redis_grava("💾 Status: no PC", "=ponte:job:{{ $json.id }}", "={{ $json.status }}", (1680, 400), validade=604800)
qr = f.responde("📤 Responde o trabalho", "={{ $('🧩 Entrega o trabalho').first().json.resposta }}", (1920, 480),
                tipo="application/json; charset=UTF-8")
qn = f.responde_json("📤 Token errado", "{ ok: false, erro: 'token da ponte errado' }", (720, 660), status=401)
f.cadeia(qw, qc, qok)
f.liga(qok, qv, 0)
f.liga(qok, qn, 1)
f.cadeia(qv, qp, qe, qtem)
f.liga(qtem, qs, 0)
f.liga(qtem, qr, 1)
f.liga(qs, qr)

# o PC devolve
rw = f.webhook("🔔 O PC devolve (POST)", "ponte-pc/resultado", (0, 860), "POST")
rc = f.codigo("🧩 Confere o resultado", js(AQUI, "resultado.js", **T), (240, 860))
rok = f.se("🚦 Resultado ok?", "={{ $json.ok }}", (480, 860))
rarq = f.se("🚦 Veio arquivo?", "={{ $json.tem_arquivo }}", (720, 780))
rga = f.redis_grava("💾 Guarda o arquivo (7 dias)", "=ponte:arq:{{ $json.nome }}", "={{ $json.b64 }}", (960, 700),
                    validade=604800)
rgs = f.redis_grava("💾 Status final", "=ponte:job:{{ $('🧩 Confere o resultado').first().json.id }}",
                    "={{ $('🧩 Confere o resultado').first().json.status }}", (1200, 780), validade=604800)
rr = f.responde_json("📤 Responde ok", "{ ok: true }", (1440, 780))
rn = f.responde_json("📤 Recusa o resultado", "{ ok: false, erro: $json.erro }", (720, 960), status=400)
f.cadeia(rw, rc, rok)
f.liga(rok, rarq, 0)
f.liga(rok, rn, 1)
f.liga(rarq, rga, 0)
f.liga(rarq, rgs, 1)
f.cadeia(rga, rgs, rr)

# status e arquivo
sw = f.webhook("🔔 Status do pedido (GET)", "ponte-pc/status", (0, 1160))
sl = f.redis_le("📖 Lê o status", "=ponte:job:{{ String($json.query.id || '').toLowerCase().replace(/[^a-z0-9]/g, '') }}",
                "status", (240, 1160))
f.cadeia(sw, sl, f.responde("📤 Responde o status", "={{ $json.status || JSON.stringify({ etapa: 'desconhecido' }) }}",
                             (480, 1160), tipo="application/json; charset=UTF-8"))
aw = f.webhook("🔔 Arquivo do PC (GET)", "ponte-pc/arquivo", (0, 1360))
al = f.redis_le("📖 Lê o arquivo", "=ponte:arq:{{ String($json.query.id || '').toLowerCase().replace(/[^a-z0-9.-]/g, '') }}",
                "dado", (240, 1360))
av = f.codigo("🧩 Vira arquivo", js(COMUM, "arquivo.js", GATILHO="🔔 Arquivo do PC (GET)"), (480, 1360))
ax = f.se("🚦 O arquivo existe?", "={{ $json.existe }}", (720, 1360))
f.cadeia(aw, al, av, ax)
f.liga(ax, f.responde_arquivo("📤 Entrega o arquivo", (960, 1280), cache="public, max-age=604800"), 0)
f.liga(ax, f.responde("📤 Arquivo não encontrado", "Arquivo não encontrado (valem 7 dias).", (960, 1460),
                      tipo="text/plain; charset=UTF-8", status=404), 1)
print(f.grava(AQUI / "ponte_pc.json"))
