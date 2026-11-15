# -*- coding: utf-8 -*-
"""Gera o fluxo 📸 INSTAGRAM · Central (Sorteio com vídeo, Gincana nos stories, Menção vira cliente fiel, Instagram vira site)."""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent / "comum"))
from gera_base import Fluxo, pagina, postgres, ia_http, switch, grava, IP  # noqa: E402

f = Fluxo("📸 INSTAGRAM · Central: Sorteio com vídeo, Gincana nos stories, Menção vira cliente fiel e Instagram vira site", tempo_max=300)
COR = "#C13584"
IG = {"instagramAccessTokenApi": {"id": "LWfbyGDT9j3MOBGq", "name": "_lucrocomia_"}}
PG_SORTEIO = {"postgres": {"id": "6xi2NwJjZR2l2zYQ", "name": "209.145.60.53"}}
OFICINA = "http://video-oficina:8000/videos/api"
SEGREDO = (AQUI / ".segredo_eventos").read_text().strip()
PUB = "https://webhookn8n6.inovareinteligenciaartificial.com"


def ig(nome, params, pos, **extra):
    return f.no(nome, "n8n-nodes-instagram-token.instagram", 1, params, pos, IG, onError="continueRegularOutput", **extra)


def sis(t):
    return json.dumps(t, ensure_ascii=False).replace("{", "\\u007b").replace("}", "\\u007d")


def chat(sistema, usuario_expr, tokens=2000, temp=0.5, modelo="antigravity/gemini-3-flash"):
    return ("={{ JSON.stringify({ model: '" + modelo + "', max_tokens: " + str(tokens) + ", temperature: " + str(temp) +
            ", messages: [{ role: 'system', content: " + sis(sistema) + " }, { role: 'user', content: " + usuario_expr + " }] }) }}")


f.nota("""## 📸 CENTRAL DO INSTAGRAM — comece aqui
Quatro ferramentas num painel só: 🔐 `/webhook/insta-painel` (conta + senha).

🎁 **Sorteio com vídeo** — pega os participantes que o fluxo *Sorteio parte 1* já validou (comentou + segue + confirmou no direct), sorteia de forma **verificável** (chave secreta fixada antes, revelada depois) e mostra uma **roleta animada** que vira **vídeo 9:16** para postar. Página pública de transparência.
🕵️ **Gincana nos stories** — pistas com horário; o ⏰ posta a arte da pista no **story** sozinho; inscrição e respostas pelo **direct**; pontos (quem acerta primeiro ganha mais) e ranking público ao vivo.
💜 **Menção vira cliente fiel** — alguém marca a loja no story → o robô responde no direct com agradecimento (✨ IA personaliza) e **cupom único**; o caixa confere o cupom no painel.
🌐 **Instagram vira site** — 🤖 a IA lê os últimos posts (foto + legenda) e monta um site com catálogo, diferenciais, FAQ e botão do WhatsApp.

**Eventos da Meta:** o app só tem 1 endereço de eventos (está no *Sorteio parte 1*). Ele **repassa** cada evento para `/webhook/insta-eventos` (nó 📨 no fim do sorteio), e aqui o 🔀 separa: direct → gincana · menção no story → cupom.

**Legenda:** 🔔 gatilho · 📤 resposta · 🐘 banco · 🔀 decisão · 🤖 IA · 📸 Instagram · 🛠️ oficina · ⏰ agendado""", [-1300, -700], 780, 700, 6)
f.nota("## 1️⃣ PÁGINAS 📄\nPainel, apresentação do sorteio, ranking da gincana e o site. HTML fixo (abre em < 1 s).", [-460, -700], 560, 980, 7)
f.nota("## 2️⃣ API 🔌\n🐘 **ig_api(jsonb)** guarda a regra (login, sorteio verificável, gincana, cupons). O 🔀 manda para o n8n o que precisa de Instagram ou IA.", [160, -700], 1900, 1250, 4)
f.nota("## 3️⃣ EVENTOS DO INSTAGRAM 📨\nRepassados pelo *Sorteio parte 1*. Direct → 🕵️ gincana. Story que marca a loja → 💜 cupom.", [-460, 600], 2520, 560, 5)
f.nota("## 4️⃣ ⏰ PISTA NO STORY\nA cada 5 min: pista que abriu → 🛠️ desenha a arte 1080×1920 → 📸 posta no story.", [-460, 1200], 2520, 420, 3)

# ── 1. páginas ──
for i, (nome, cam, arq) in enumerate([("Painel", "insta-painel", "painel.html"), ("Sorteio (apresentação)", "insta-sorteio", "sorteio.html"),
                                      ("Gincana (ranking)", "insta-gincana", "gincana.html"), ("Site do Instagram", "insta-site", "site.html")]):
    y = -580 + i * 210
    f.liga(f.webhook(f"🔔 {nome}", cam, [-420, y]), f.responde(f"📤 {nome}", pagina(AQUI / arq, cor=COR), [-160, y]))

# ── 2. API ──
w = f.webhook("🔔 API (POST)", "insta-api", [200, -380], metodo="POST")
db = postgres(f, "🐘 ig_api", "SELECT ig_api2($1::jsonb) AS r",
              "={{ JSON.stringify(Object.assign({}, (typeof $json.body === 'object' && $json.body) || {}, { ip: " + IP + " })) }}", [420, -380])
sw = switch(f, "🔀 Precisa do Instagram ou da IA?", [
    ("posts", "={{ $json.r && $json.r.ia === 'posts' }}"),
    ("sorteio_buscar", "={{ $json.r && $json.r.ia === 'sorteio_buscar' }}"),
    ("site_gerar", "={{ $json.r && $json.r.ia === 'site_gerar' }}"),
    ("gincana_pistas", "={{ $json.r && $json.r.ia === 'gincana_pistas' }}"),
    ("gincana_encerrar", "={{ $json.r && $json.r.ia === 'gincana_encerrar' }}"),
    ("sorteio_anunciar", "={{ $json.r && $json.r.ia === 'sorteio_anunciar' }}"),
], [640, -380])
f.cadeia(w, db, sw)
f.liga(sw, f.responde_json("📤 Responde", "$json.r || { ok: false, erro: 'Sem resposta do banco' }", [900, -640]), saida=6)
CX = "$('🐘 ig_api').first().json.r.contexto"

# posts (para escolher o do sorteio)
lp = ig("📸 Lista os posts", {"resource": "media", "operation": "listMedia", "returnAll": False, "limit": 24,
                              "mediaFields": ["id", "caption", "media_type", "media_url", "thumbnail_url", "permalink", "timestamp"]}, [900, -500], alwaysOutputData=True)
f.liga(sw, lp, saida=0)
f.liga(lp, f.responde_json("📤 Posts", "{ ok: !!$input.all().filter(i => i.json.id).length, erro: $input.first().json.error ? 'Não consegui ler o Instagram (token?)' : 'Nenhum post', posts: $input.all().map(i => i.json).filter(p => p.id) }", [1120, -500]))

# participantes do sorteio (banco do Sorteio parte 1)
bs = f.no("🐘 Participantes do post", "n8n-nodes-base.postgres", 2.6, {"operation": "executeQuery",
          "query": "SELECT DISTINCT ON (from_user_id) from_username AS u, from_user_id AS id FROM sorteio_participantes WHERE media_id = $1 AND is_following = true "
                   "AND created_at >= coalesce(nullif($2, '')::date, '2000-01-01') AND created_at < coalesce(nullif($3, '')::date, '2100-01-01') + 1 ORDER BY from_user_id, created_at",
          "options": {"queryReplacement": "={{ [" + CX + ".media_id || '0', " + CX + ".de || '', " + CX + ".ate || ''] }}"}},
          [900, -360], PG_SORTEIO, alwaysOutputData=True, onError="continueRegularOutput")
f.liga(sw, bs, saida=1)
f.liga(bs, f.responde_json("📤 Participantes", "{ ok: !$input.first().json.error, erro: $input.first().json.error ? 'Não consegui ler o banco do sorteio' : undefined, participantes: $input.all().map(i => i.json).filter(p => p.u) }", [1120, -360]))

# site: posts → IA → salva
lp2 = ig("📸 Lê os posts para o site", {"resource": "media", "operation": "listMedia", "returnAll": False, "limit": 30,
                                       "mediaFields": ["id", "caption", "media_type", "media_url", "thumbnail_url", "permalink", "timestamp"]}, [900, -220], alwaysOutputData=True)
SIS_SITE = ("Você cria sites de negócios a partir do Instagram. Recebe a lista de posts (legenda + número da imagem). Descubra o que o perfil vende/oferece, "
            "o tom de voz e monte o conteúdo de um site de uma página em português do Brasil. Use SOMENTE o que está nas legendas: preço só se aparecer escrito; "
            "não invente produtos, endereço nem telefone. Devolva SOMENTE JSON: {\"nome\":\"\",\"titulo\":\"frase forte para o topo (até 60)\",\"subtitulo\":\"até 140\","
            "\"sobre\":\"2-3 frases\",\"cidade\":\"se aparecer\",\"cta\":\"texto do botão (até 24)\",\"cta_mensagem\":\"mensagem que o cliente manda no WhatsApp\","
            "\"titulo_catalogo\":\"ex.: Nossos produtos / Serviços\",\"diferenciais\":[{\"icone\":\"1 emoji\",\"titulo\":\"\",\"texto\":\"\"}],"
            "\"produtos\":[{\"nome\":\"\",\"descricao\":\"até 100\",\"preco\":\"como estiver escrito, ex.: R$ 49,90 (ou vazio)\",\"categoria\":\"\",\"post\":número_do_post}],"
            "\"faq\":[{\"pergunta\":\"\",\"resposta\":\"\"}]}. 3 a 4 diferenciais, até 24 produtos (um por post de produto), 3 a 5 FAQs baseadas em dúvidas comuns do ramo e no que as legendas dizem.")
mon = f.codigo("🧩 Monta o pedido do site", """// Junta as legendas dos posts numa lista numerada para a IA.
const posts = $input.all().map(i => i.json).filter(p => p.id);
if (!posts.length) return [{ json: { vazio: true } }];
const lista = posts.map((p, i) => `POST ${i} (${p.media_type}${p.timestamp ? ', ' + p.timestamp.slice(0, 10) : ''}): ${String(p.caption || '(sem legenda)').replace(/\\s+/g, ' ').slice(0, 600)}`).join('\\n');
return [{ json: { vazio: false, posts, lista } }];""", [1120, -220])
ias = ia_http(f, "🤖 IA monta o site", chat(SIS_SITE, "'Perfil: @' + " + CX + ".slug + ' (' + " + CX + ".nome + ')\\n\\n' + $json.lista", tokens=6000, temp=0.4), [1340, -220], tempo=150000)
fin = f.codigo("🧩 Junta site e fotos", """const c = $('🐘 ig_api').first().json.r.contexto, m = $('🧩 Monta o pedido do site').first().json;
if (m.vazio) return [{ json: { ok: false, erro: 'Não achei posts no Instagram (ou o token venceu).' } }];
let s = null; const t = String(($json.choices && $json.choices[0] && $json.choices[0].message.content) || '');
try { s = JSON.parse(t.replace(/^\\s*```(?:json)?/i, '').replace(/```\\s*$/, '').trim()); } catch (e) { const a = t.indexOf('{'), b = t.lastIndexOf('}'); try { s = JSON.parse(t.slice(a, b + 1)); } catch (e2) {} }
if (!s) return [{ json: { ok: false, erro: 'A IA não respondeu no formato. Tente de novo.' } }];
const img = p => p && (p.media_type === 'VIDEO' ? p.thumbnail_url : p.media_url) || '';
s.produtos = (s.produtos || []).map(x => ({ ...x, img: img(m.posts[Number(x.post)]), link: (m.posts[Number(x.post)] || {}).permalink || '' })).filter(x => x.nome);
s.galeria = m.posts.slice(0, 12).map(p => ({ img: img(p), link: p.permalink })).filter(g => g.img);
s.cor = c.cor; s.nome = s.nome || c.nome;
return [{ json: { ok: true, conta_id: c.conta_id, dados: JSON.stringify(s), produtos: s.produtos.length } }];""", [1560, -220])
sv = postgres(f, "🐘 Salva o site", "SELECT ig_site_salvar($1::int, $2::jsonb)", "={{ [$json.conta_id || 0, $json.dados || '{}'] }}", [1780, -220])
ok_site = f.se("🔀 Site ok?", "={{ $('🧩 Junta site e fotos').first().json.ok }}", [2000, -220])
f.cadeia(lp2, mon, ias, fin, sv, ok_site)
f.liga(sw, lp2, saida=2)
f.liga(ok_site, f.responde_json("📤 Site pronto", "{ ok: true, produtos: $('🧩 Junta site e fotos').first().json.produtos }", [2220, -280]), 0)
f.liga(ok_site, f.responde_json("📤 Site falhou", "{ ok: false, erro: $('🧩 Junta site e fotos').first().json.erro }", [2220, -160]), 1)

# pistas pela IA
SIS_G = ("Você cria gincanas de Instagram para lojas. Crie pistas curtas e divertidas (enigmas, charadas, 'complete a frase') sobre o tema dado, "
         "com resposta de UMA ou DUAS palavras, fácil de digitar e sem ambiguidade. Devolva SOMENTE JSON: {\"pistas\":[{\"pista\":\"\",\"resposta\":\"\"}]}")
ig_p = ia_http(f, "🤖 IA cria as pistas", chat(SIS_G, "'Tema: ' + " + CX + ".tema + '\\nQuantidade: ' + (" + CX + ".quantas || 3)", tokens=1200, temp=0.9), [900, -80], tempo=90000)
f.liga(sw, ig_p, saida=3)
f.liga(ig_p, f.responde_json("📤 Pistas", "$json.choices && $json.choices[0] ? { ok: true, resultado: String($json.choices[0].message.content || '') } : { ok: false, erro: 'A IA não respondeu agora.' }", [1120, -80]))

# ── 3. eventos repassados pelo Sorteio parte 1 ──
ev = f.webhook("🔔 Evento do Instagram (repassado)", "insta-eventos", [-420, 760], metodo="POST")
f.liga(ev, f.responde_json("📤 Recebido", "{ ok: true }", [-200, 640]))
nrm = f.codigo("🧩 Separa o evento", """// O Sorteio parte 1 repassa o item do Instagram Trigger. Menção no story chega como MENSAGEM com anexo story_mention.
const b = (typeof $json.body === 'object' && $json.body) || {};
const e = b.evento || b;
if (b.segredo !== '__SEGREDO__') return [];
const anexos = Array.isArray(e.attachments) ? e.attachments : [];
const story = anexos.find(a => a && a.type === 'story_mention');
const conta = String(e.recipientId || e.entryId || '');
if (e.isEcho || !e.senderId || e.senderId === conta) return [];
if (story) return [{ json: { tipo: 'mencao', conta, remetente: String(e.senderId), midia: (story.payload && story.payload.url) || '' } }];
if (e.eventType === 'message' && e.text) return [{ json: { tipo: 'dm', conta, remetente: String(e.senderId), texto: String(e.text).slice(0, 200) } }];
return [];""".replace('__SEGREDO__', SEGREDO), [-200, 860])
f.liga(ev, nrm)
sw2 = switch(f, "🔀 Que evento é?", [("dm", "={{ $json.tipo === 'dm' }}"), ("mencao", "={{ $json.tipo === 'mencao' }}")], [0, 860])
f.liga(nrm, sw2)
# gincana pelo direct
pfg = ig("📸 Quem é o jogador?", {"resource": "user", "operation": "getProfile", "userId": "={{ $json.remetente }}", "fields": ["username"]}, [220, 700], alwaysOutputData=True)
gdm = postgres(f, "🐘 Gincana confere", "SELECT ig_gincana_dm($1, $2, $3, $4) AS r",
               "={{ [$('🧩 Separa o evento').item.json.conta, $('🧩 Separa o evento').item.json.remetente, $json.username || '', $('🧩 Separa o evento').item.json.texto] }}", [440, 700])
tem = f.se("🔀 Responder?", "={{ $json.r && $json.r.acao === 'responder' }}", [660, 700])
dm1 = ig("📸 Responde no direct", {"resource": "message", "operation": "sendText", "recipientId": "={{ $('🧩 Separa o evento').item.json.remetente }}",
                                   "messageText": "={{ $json.r.texto }}"}, [880, 640])
f.cadeia(pfg, gdm, tem)
f.liga(sw2, pfg, saida=0)
f.liga(tem, dm1, 0)
# menção → perfil (nome) → cupom → IA (opcional) → direct
pf = ig("📸 Quem marcou?", {"resource": "user", "operation": "getProfile", "userId": "={{ $json.remetente }}", "fields": ["name", "username"]}, [220, 980], alwaysOutputData=True)
mn = postgres(f, "🐘 Registra a menção", "SELECT ig_mencao_nova($1, $2, $3, 'story', $4) AS r",
              "={{ [$('🧩 Separa o evento').item.json.conta, $('🧩 Separa o evento').item.json.remetente, $json.username || '', $('🧩 Separa o evento').item.json.midia] }}", [440, 980])
sw3 = switch(f, "🔀 Cupom ou só obrigado?", [("cupom", "={{ $json.r && $json.r.acao === 'cupom' }}"), ("agradecer", "={{ $json.r && $json.r.acao === 'agradecer' }}")], [660, 980])
SIS_M = ("Você é a voz de uma loja no Instagram. Escreva UMA mensagem curta de direct (até 320 caracteres) agradecendo a pessoa por marcar a loja no story. "
         "Se houver imagem do story, cite com carinho algo que aparece nela (sem inventar). Siga o modelo do dono no tom. Inclua obrigatoriamente o cupom e o presente "
         "exatamente como recebidos, e a validade. 1 ou 2 emojis. Sem aspas, sem markdown.")
iam = ia_http(f, "🤖 IA personaliza o agradecimento",
              "={{ JSON.stringify({ model: 'antigravity/gemini-3-flash', max_tokens: 400, temperature: 0.8, messages: [{ role: 'system', content: " + sis(SIS_M) + " }, { role: 'user', content: "
              "[{ type: 'text', text: 'Loja: ' + $json.r.loja + '\\nNome: ' + $json.r.nome + '\\nCupom: ' + $json.r.cupom + '\\nPresente: ' + $json.r.desconto + '\\nValidade: ' + $json.r.validade + ' dias\\nModelo do dono: ' + $json.r.modelo }]"
              ".concat($('🧩 Separa o evento').item.json.midia && $json.r.usar_ia ? [{ type: 'image_url', image_url: { url: $('🧩 Separa o evento').item.json.midia } }] : []) }] }) }}",
              [880, 920], tempo=60000)
txt = f.codigo("🧩 Texto final", """// Se a IA falhar (ou estiver desligada), usa o modelo do dono com as variáveis trocadas.
return $input.all().map((it, k) => {
  const r = $('🐘 Registra a menção').all()[k].json.r;
  const ia = it.json.choices && it.json.choices[0] && String(it.json.choices[0].message.content || '').trim();
  const modelo = String(r.modelo).replace(/\\{nome\\}/g, r.nome).replace(/\\{cupom\\}/g, r.cupom).replace(/\\{desconto\\}/g, r.desconto).replace(/\\{validade\\}/g, r.validade + ' dias');
  let texto = r.usar_ia && ia && ia.includes(r.cupom) ? ia : modelo;
  if (!texto.includes(r.cupom)) texto += `\\n🎁 Cupom: ${r.cupom}`;
  if (!texto.toLowerCase().includes(String(r.desconto).toLowerCase().slice(0, 6))) texto += `\\n✨ Vale ${r.desconto} por ${r.validade} dias.`;
  return { json: { id: r.id, texto } };
});""", [1100, 920])
dm2 = ig("📸 Manda o cupom no direct", {"resource": "message", "operation": "sendText", "recipientId": "={{ $('🧩 Separa o evento').item.json.remetente }}", "messageText": "={{ $json.texto }}"}, [1320, 920])
reg = postgres(f, "🐘 Marca enviado", "SELECT ig_mencao_enviada($1::int, $2, $3)",
               "={{ [$('🧩 Texto final').item.json.id, $('🧩 Texto final').item.json.texto, $json.error ? String($json.error.message || $json.error).slice(0, 200) : ($json.message_id || $json.id || $json.recipient_id ? '' : 'sem confirmação do Instagram')] }}", [1540, 920])
dm3 = ig("📸 Só agradece", {"resource": "message", "operation": "sendText", "recipientId": "={{ $('🧩 Separa o evento').item.json.remetente }}", "messageText": "={{ $json.r.texto }}"}, [880, 1060])
f.cadeia(pf, mn, sw3)
f.liga(sw2, pf, saida=1)
f.liga(sw3, iam, 0)
f.cadeia(iam, txt, dm2, reg)
f.liga(sw3, dm3, 1)

# ── 4. pista no story ──
ag = f.agenda("⏰ A cada 5 minutos", "*/5 * * * *", [-420, 1320])
pend = postgres(f, "🐘 Pistas que abriram", "SELECT * FROM ig_gincana_a_publicar()", "", [-200, 1320], sempre=False)
arte = f.codigo("🧩 Desenha a arte da pista", """// HTML 1080x1920 da pista (vira JPG na oficina).
const esc = s => String(s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
return $input.all().map(it => { const e = it.json; const cor = /^#[0-9a-fA-F]{6}$/.test(e.cor) ? e.cor : '#C13584';
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>*{margin:0;box-sizing:border-box}body{width:1080px;height:1920px;font-family:Montserrat,Inter,sans-serif;color:#fff;
  background:linear-gradient(160deg,#1a0b2e,${cor} 65%,#f59e0b);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:110px}
  .t{font-size:44px;font-weight:800;letter-spacing:6px;opacity:.9}.n{font-size:150px;margin:30px 0 10px}.h{font-size:58px;font-weight:800;margin-bottom:50px}
  .p{font-size:66px;font-weight:800;line-height:1.2;background:rgba(255,255,255,.14);border:3px solid rgba(255,255,255,.4);border-radius:40px;padding:60px 50px}
  .c{margin-top:70px;font-size:44px;font-weight:700}.c b{background:#fff;color:#111;padding:6px 22px;border-radius:16px}.f{position:absolute;bottom:120px;font-size:34px;opacity:.85}</style></head>
  <body><div class="t">GINCANA · ${esc(e.titulo).toUpperCase()}</div><div class="n">🕵️</div><div class="h">PISTA ${e.ordem} DE ${e.total}</div><div class="p">${esc(e.pista)}</div>
  <div class="c">Responda no DIRECT 📩<br><br>Ainda não joga? Mande <b>${esc(e.palavra)}</b></div>${e.premio ? `<div class="f">🏆 Prêmio: ${esc(e.premio)}</div>` : ''}</body></html>`;
  return { json: { ...e, corpo: JSON.stringify({ area: 'eventos', deck: 'gincana-' + e.codigo, nome: 'pista-' + e.ordem, largura: 1080, altura: 1920, html }) } }; });""", [20, 1320])
png = f.http("🛠️ Oficina desenha (1080×1920)", OFICINA + "/html_png", [240, 1320], metodo="POST", corpo_json="={{ $json.corpo }}", tempo=150000, nunca_erro=True, continua_no_erro=True)
st = ig("📸 Posta no story", {"resource": "story", "operation": "createStory", "storyMediaType": "IMAGE",
                              "storyImageUrl": "=" + PUB + "/videos/arquivo/{{ $json.arquivo }}"}, [460, 1320])
mk = postgres(f, "🐘 Marca a pista como postada", "SELECT ig_gincana_marcar($1::int, $2::jsonb)",
              "={{ [$('🧩 Desenha a arte da pista').item.json.etapa_id, JSON.stringify({ arquivo: $('🛠️ Oficina desenha (1080×1920)').item.json.arquivo || '', story: $json.id || null, erro: $json.error ? String($json.error.message || $json.error).slice(0, 200) : null })] }}", [680, 1320])
f.cadeia(ag, pend, arte, png, st, mk)

from gera_extra import blocos
blocos(f, sw, ig, postgres, CX, OFICINA, PUB)
out = grava(f, AQUI, "insta.json")
