# -*- coding: utf-8 -*-
"""Gera o fluxo 🏠 Vitrine de Imóveis com IA. Importar com ferramentas/n8n_servidor.py importa imoveis.json"""
import sys
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent / "comum"))
from gera_base import Fluxo, pagina, postgres, ia_http, para_arquivo, switch, grava, IP  # noqa: E402

f = Fluxo("🏠 Vitrine de Imóveis com IA · site de imóveis, painel admin com fotos, anúncio e vídeo por IA, interessados e corretores", tempo_max=600)
COR = "#1E3A8A"
OFICINA = "http://video-oficina:8000/videos/api"

f.nota("""## 🏠 VITRINE DE IMÓVEIS COM IA — comece aqui
Um **site de imóveis** (tipo portal) para corretor ou imobiliária, com **painel administrador** fácil.

**Links:**
• 🆕 Criar a vitrine: `/webhook/imoveis-criar`
• 🔐 Painel: `/webhook/imoveis-painel`
• 🌐 Site público: `/webhook/imoveis?l=<código>` · 🏡 página de cada imóvel: `/webhook/imovel?l=<código>&c=IM101`

**No painel:** 📸 sobe as fotos do celular (arrasta para ordenar, escolhe a capa) · ✨ **a IA olha as fotos e escreve o anúncio** (título, descrição, destaques, características, melhor ordem das fotos e dicas) · 🎬 **gera o vídeo do imóvel** (usa o fluxo *Vídeo de Anúncio com IA*: roteiro, narração, movimento de câmera, preço e música) · 🟢 publica, reserva, marca vendido · 📥 interessados com status (CRM simples) · 👥 corretores com WhatsApp próprio · 📊 visitas e cliques por imóvel.

**Legenda:** 🔔 gatilho · 📤 resposta · 🐘 banco Postgres · 🔀 decisão · 🤖 IA · 🛠️ oficina de vídeo · ⏰ agendado""", [-1300, -600], 760, 600, 6)
f.nota("""## 1️⃣ PÁGINAS 📄
HTML fixo devolvido direto pelo 📤 (abre em menos de 1 s). Tudo o que muda vem da API.""", [-460, -600], 560, 900, 7)
f.nota("""## 2️⃣ API 🔌
🐘 **imv_api(jsonb)**: toda a regra fica no Postgres (login com bcrypt, permissão, imóveis, interessados, contadores).
Uma chamada por pedido, corpo inteiro como parâmetro **$1** (sem SQL injection).
🔀 Quando a resposta pede trabalho extra: ✨ **anúncio** (IA com visão olha as fotos) · 🎬 **vídeo** (manda as fotos para a oficina e pede o vídeo ao fluxo de anúncio) · 💾 **guardar vídeo** (copia o vídeo para a pasta que não expira).""", [160, -600], 1500, 1000, 4)
f.nota("""## 3️⃣ FOTOS 🖼️
As fotos ficam **no banco** (não somem). 🔔 `/webhook/imoveis-img?id=` entrega com cache de 1 dia.""", [-460, 340], 560, 380, 5)
f.nota("""## 4️⃣ FINALIZADOR ⏰
A cada 2 min confere vídeos que ficaram "gerando" (quando o dono fechou o painel antes do fim) e guarda os prontos.""", [160, 440], 1100, 360, 3)

# ── 1. páginas ──
pags = [("Criar vitrine", "imoveis-criar", "cadastro.html"), ("Painel administrador", "imoveis-painel", "painel.html"),
        ("Site da vitrine", "imoveis", "site.html"), ("Página do imóvel", "imovel", "imovel.html")]
for i, (nome, caminho, arq) in enumerate(pags):
    y = -480 + i * 190
    f.liga(f.webhook(f"🔔 {nome}", caminho, [-420, y]), f.responde(f"📤 {nome}", pagina(AQUI / arq, cor=COR), [-160, y]))

# ── 2. API ──
w = f.webhook("🔔 API (POST)", "imoveis-api", [200, -300], metodo="POST")
db = postgres(f, "🐘 imv_api", "SELECT imv_api2($1::jsonb) AS r",
              "={{ JSON.stringify(Object.assign({}, (typeof $json.body === 'object' && $json.body) || {}, { ip: " + IP + " })) }}", [420, -300])
sw = switch(f, "🔀 Precisa de trabalho extra?", [
    ("anuncio", "={{ $json.r && $json.r.ia === 'anuncio' }}"),
    ("video_gerar", "={{ $json.r && $json.r.ia === 'video_gerar' }}"),
    ("video_guardar", "={{ $json.r && $json.r.ia === 'video_guardar' }}"),
    ("insta_legenda", "={{ $json.r && $json.r.ia === 'insta_legenda' }}"),
    ("insta_postar", "={{ $json.r && $json.r.ia === 'insta_postar' }}"),
], [640, -300])
f.cadeia(w, db, sw)
f.liga(sw, f.responde_json("📤 Responde", "$json.r || { ok: false, erro: 'Sem resposta do banco' }", [900, -520]), saida=5)

# ✨ anúncio pela IA com visão
SIS = ("Você é um corretor de imóveis experiente e copywriter. Recebe fotos (numeradas a partir de 0), dados e anotações do corretor. "
       "Escreva o anúncio em português do Brasil, vendedor mas HONESTO: só afirme o que aparece nas fotos ou foi dito. Nada de 'imperdível', 'oportunidade única' ou exageros. "
       "Devolva SOMENTE JSON: {\"titulo\":\"até 80 caracteres, com tipo, 1-2 diferenciais e o bairro se houver\","
       "\"descricao\":\"3 parágrafos curtos: impressão geral; ambientes na ordem de uma visita; localização/estilo de vida e chamada para visita\","
       "\"destaques\":[\"3 a 6 frases curtas\"],\"caracteristicas\":[\"itens curtos como Piscina, Churrasqueira, Armários planejados\"],"
       "\"tipo\":\"casa|apartamento|sobrado|cobertura|terreno|comercial|sala|galpao|chacara\",\"quartos\":0,\"suites\":0,\"banheiros\":0,\"vagas\":0,"
       "\"ordem_fotos\":[índices na melhor ordem para vender: fachada ou sala mais bonita primeiro, depois a sequência de uma visita],"
       "\"legendas\":{\"0\":\"legenda curta da foto 0\"},\"avisos\":[\"dicas sobre as fotos: escura, torta, com bagunça, falta foto de cozinha/banheiro etc.\"]}. "
       "NÚMEROS: quartos, suítes, banheiros e vagas = 0 sempre que não estiver ESCRITO nos dados/anotações. Uma foto de um quarto não prova que só existe 1 quarto: nesse caso devolva 0. Nunca contradiga as anotações do corretor (se ele disse 2 vagas, são 2).")
C = "$('🐘 imv_api').first().json.r.contexto"
corpo_anuncio = ("={{ JSON.stringify({ model: 'antigravity/gemini-3-flash', max_tokens: 3500, temperature: 0.4, messages: [{ role: 'system', content: "
                 + __import__('json').dumps(SIS, ensure_ascii=False).replace("{", "\\u007b").replace("}", "\\u007d")
                 + " }, { role: 'user', content: [{ type: 'text', text: 'Imobiliária: ' + " + C + ".loja + ' (' + (" + C + ".cidade || '') + ')\\nDados já preenchidos: ' + JSON.stringify(" + C + ".dados || {}) + '\\nAnotações do corretor: ' + (" + C + ".notas || '(nenhuma)') + '\\nFotos: ' + " + C + ".miniaturas.length }]"
                 ".concat(" + C + ".miniaturas.map((b, i) => [{ type: 'text', text: 'FOTO ' + i }, { type: 'image_url', image_url: { url: 'data:image/jpeg;base64,' + b } }]).flat()) }] }) }}")
ia = ia_http(f, "🤖 IA escreve o anúncio", corpo_anuncio, [900, -380], tempo=150000)
f.liga(sw, ia, saida=0)
f.liga(ia, f.responde_json("📤 Anúncio pronto", "$json.choices && $json.choices[0] ? { ok: true, resultado: String($json.choices[0].message.content || '') } : { ok: false, erro: 'A IA não respondeu agora. Tente de novo.' }", [1140, -380]))

# 🎬 gerar o vídeo: fotos do banco → oficina → fluxo do Vídeo de Anúncio
V = "$('🐘 imv_api').first().json.r.contexto"
ofc = f.http("🛠️ Oficina recebe as fotos", OFICINA + "/fotos_b64", [900, -230], metodo="POST",
             corpo_json="={{ JSON.stringify({ fotos: " + V + ".fotos }) }}", tempo=120000, nunca_erro=True, continua_no_erro=True)
pede = f.http("🎬 Pede o vídeo ao fluxo de anúncio", "={{ $('🔔 API (POST)').first().json.webhookUrl.split('/webhook/')[0] }}/webhook/anuncio-video", [1120, -230], metodo="POST",
              corpo_json="={{ JSON.stringify(Object.assign({}, " + V + ".pedido, { fotos: $json.ids || [] })) }}", tempo=60000, nunca_erro=True, continua_no_erro=True)
cod_job = f.codigo("🧩 Lê o trabalho", """// O fluxo de anúncio responde {ok, link: '.../anuncio-video-ver?job=...'}: guarda o job no imóvel.
const c = $('🐘 imv_api').first().json.r.contexto;
const r = $input.first().json || {};
const m = String(r.link || '').match(/job=([a-z0-9-]+)/);
if (!r.ok || !m) return [{ json: { ok: false, erro: (r.erros && r.erros.join(' ')) || r.erro || 'Não consegui pedir o vídeo agora. Tente de novo.', id: c.id, salvar: JSON.stringify({ status: 'erro', erro: 'falha ao pedir' }) } }];
return [{ json: { ok: true, job: m[1], id: c.id, salvar: JSON.stringify({ status: 'gerando', job: m[1] }) } }];""", [1340, -230])
marca = postgres(f, "🐘 Marca 'gerando'", "SELECT imv_video_status($1::int, $2::jsonb) AS r", "={{ [$json.id, $json.salvar] }}", [1560, -230])
f.cadeia(ofc, pede, cod_job, marca)
f.liga(sw, ofc, saida=1)
f.liga(marca, f.responde_json("📤 Vídeo pedido", "{ ok: $('🧩 Lê o trabalho').first().json.ok, job: $('🧩 Lê o trabalho').first().json.job, erro: $('🧩 Lê o trabalho').first().json.erro }", [1780, -230]))

# 💾 guardar o vídeo pronto (pasta que não expira)
G = "$('🐘 imv_api').first().json.r.contexto"
gv = f.http("🛠️ Guarda o vídeo para sempre", OFICINA + "/guardar_video", [900, -80], metodo="POST",
            corpo_json="={{ JSON.stringify({ job: " + G + ".job, pasta: " + G + ".pasta }) }}", tempo=120000, nunca_erro=True, continua_no_erro=True)
cg = f.codigo("🧩 Monta o vídeo do imóvel", """const c = $('🐘 imv_api').first().json.r.contexto;
const g = $input.first().json || {};
if (!g.video) return [{ json: { ok: false, id: c.id, salvar: JSON.stringify({ status: 'erro', job: c.job, erro: 'vídeo não encontrado na oficina' }) } }];
return [{ json: { ok: true, id: c.id, salvar: JSON.stringify({ status: 'pronto', job: c.job, url: g.video || g.video_musica, musica: g.video_musica || null, capa: g.capa || null, pagina: c.pagina || null }) } }];""", [1120, -80])
gm = postgres(f, "🐘 Grava o vídeo no imóvel", "SELECT imv_video_status($1::int, $2::jsonb) AS r", "={{ [$json.id, $json.salvar] }}", [1340, -80])
f.cadeia(gv, cg, gm)
f.liga(sw, gv, saida=2)
f.liga(gm, f.responde_json("📤 Vídeo guardado", "{ ok: $('🧩 Monta o vídeo do imóvel').first().json.ok, erro: $('🧩 Monta o vídeo do imóvel').first().json.ok ? undefined : 'O vídeo não ficou pronto. Gere de novo.' }", [1560, -80]))

# ── 3. fotos ──
wi = f.webhook("🔔 Foto (GET)", "imoveis-img", [-420, 480])
li = postgres(f, "🐘 Lê a foto", "SELECT mime, b64 FROM imv_img($1)", "={{ String($json.query.id || '').replace(/[^0-9a-f-]/g, '').slice(0, 36) || '0' }}", [-200, 480])
ex = f.se("🔀 Achou?", "={{ !!$json.b64 }}", [0, 480])
ar = para_arquivo(f, "🧩 Vira arquivo", "b64", "={{ $json.mime }}", [200, 420])
f.cadeia(wi, li, ex)
f.liga(ex, ar, 0)
f.liga(ar, f.responde_arquivo("📤 Entrega a foto", [400, 420], cache="public, max-age=604800, immutable"))
f.liga(ex, f.responde("📤 Sem foto", "não encontrada", [200, 580], tipo="text/plain; charset=UTF-8", status=404), 1)

# ── 4. finalizador ──
ag = f.agenda("⏰ A cada 2 minutos", "*/2 * * * *", [200, 580])
pend = postgres(f, "🐘 Vídeos pendentes", "SELECT * FROM imv_videos_pendentes()", "", [420, 580], sempre=False)
st = f.http("🌐 Pergunta o andamento", "=https://webhookn8n6.inovareinteligenciaartificial.com/webhook/anuncio-video-status?job={{ $json.job }}", [640, 580], nunca_erro=True, continua_no_erro=True, tempo=20000)
fz = f.codigo("🧩 Terminou?", """// Junta cada imóvel pendente com o andamento do vídeo dele.
const pend = $('🐘 Vídeos pendentes').all().map(i => i.json);
return $input.all().map((it, k) => ({ json: { ...pend[k], s: it.json || {} } }))
  .filter(x => x.s.etapa === 'pronto' || x.s.etapa === 'erro')
  .map(x => ({ json: { id: x.id, job: x.job, pasta: x.pasta, pagina: x.s.pagina || x.pagina || '', erro: x.s.etapa === 'erro' ? String(x.s.erro || 'falhou').slice(0, 200) : '' } }));""", [860, 580])
gv2 = f.http("🛠️ Guarda o vídeo", OFICINA + "/guardar_video", [1080, 580], metodo="POST",
             corpo_json="={{ JSON.stringify({ job: $json.job, pasta: $json.pasta }) }}", tempo=120000, nunca_erro=True, continua_no_erro=True)
cg2 = f.codigo("🧩 Resultado", """return $input.all().map((it, k) => { const x = $('🧩 Terminou?').all()[k].json, g = it.json || {};
  const ok = !x.erro && g.video;
  return { json: { id: x.id, salvar: JSON.stringify(ok ? { status: 'pronto', job: x.job, url: g.video || g.video_musica, musica: g.video_musica || null, capa: g.capa || null, pagina: x.pagina || null } : { status: 'erro', job: x.job, erro: x.erro || 'vídeo não encontrado' }) } }; });""", [1300, 580])
gm2 = postgres(f, "🐘 Grava no imóvel", "SELECT imv_video_status($1::int, $2::jsonb) AS r", "={{ [$json.id, $json.salvar] }}", [1520, 580])
f.cadeia(ag, pend, st, fz, gv2, cg2, gm2)

SIS_L = ("Você é social media de imobiliária. Escreva a LEGENDA de um Reel do imóvel, em português do Brasil: 1ª linha = gancho forte (até 70 caracteres, com emoji); "
         "depois 3 a 5 destaques em linhas com emoji; preço; localização (bairro/cidade); chamada para ação (\"chama no direct\" ou WhatsApp); CRECI se houver; "
         "no fim 8 a 12 hashtags (tipo de imóvel + bairro + cidade + compra/aluguel). Honesta: só o que está nos dados. Sem markdown, sem aspas. Até 1800 caracteres.")
CL = "$('🐘 imv_api').first().json.r.contexto"
il = ia_http(f, "🤖 IA escreve a legenda", "={{ JSON.stringify({ model: 'antigravity/gemini-3-flash', max_tokens: 1500, temperature: 0.7, messages: [{ role: 'system', content: "
             + __import__('json').dumps(SIS_L, ensure_ascii=False).replace("{", "\\u007b").replace("}", "\\u007d") + " }, { role: 'user', content: JSON.stringify(Object.assign({}, " + CL + ", { video: undefined, token: undefined, legenda: undefined })) }] }) }}", [900, 60], tempo=90000)
f.liga(sw, il, saida=3)
f.liga(il, f.responde_json("📤 Legenda", "$json.choices && $json.choices[0] ? { ok: true, resultado: String($json.choices[0].message.content || '').trim() } : { ok: false, erro: 'A IA não respondeu agora.' }", [1120, 60]))
rl = f.no("📸 Publica o Reel", "n8n-nodes-instagram-token.instagram", 1, {"resource": "post", "operation": "createReel",
          "reelVideoUrl": "=https://webhookn8n6.inovareinteligenciaartificial.com/videos/arquivo/{{ " + CL + ".video }}", "reelCaption": "={{ " + CL + ".legenda }}"},
          [900, 200], {"instagramAccessTokenApi": {"id": "LWfbyGDT9j3MOBGq", "name": "_lucrocomia_"}}, onError="continueRegularOutput")
gp = postgres(f, "🐘 Guarda o post", "SELECT imv_api2($1::jsonb) AS r",
              "={{ JSON.stringify({ acao: 'insta_salvar', token: " + CL + ".token, id: " + CL + ".id, legenda: " + CL + ".legenda, post: $json.id || '' }) }}", [1120, 200])
f.liga(sw, rl, saida=4)
f.cadeia(rl, gp)
f.liga(gp, f.responde_json("📤 Reel publicado", "$('📸 Publica o Reel').first().json.id ? { ok: true, id: $('📸 Publica o Reel').first().json.id, link: $('📸 Publica o Reel').first().json.permalink || '' } : { ok: false, erro: 'O Instagram recusou: ' + String($('📸 Publica o Reel').first().json.error || 'sem resposta').slice(0, 200) }", [1340, 200]))

grava(f, AQUI, "imoveis.json")
