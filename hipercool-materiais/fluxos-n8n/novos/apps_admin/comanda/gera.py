# -*- coding: utf-8 -*-
"""Gera o fluxo 🍽️ Comanda de Mesa com IA (painel admin completo). Importar com ferramentas/n8n_servidor.py importa comanda.json"""
import sys
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent / "comum"))
from gera_base import Fluxo, pagina, postgres, ia_http, para_arquivo, switch, grava, IP  # noqa: E402

f = Fluxo("🍽️ Comanda de Mesa com IA · QR na mesa, cozinha, caixa, estoque, produtos com foto, equipe e relatórios", tempo_max=300)
COR = "#C2410C"

# ── notas (padrão das aulas: moldura por etapa + emoji por tipo) ──
f.nota("""## 🍽️ COMANDA DE MESA COM IA — comece aqui
Sistema completo para **bar, restaurante e lanchonete**, com **painel administrador** de verdade.

**Links (troque pelo seu domínio):**
• 🆕 Criar o sistema: `/webhook/comanda`
• 🔐 Painel (dono, caixa, garçom, cozinha): `/webhook/comanda-painel`
• 📱 Cardápio da mesa: `/webhook/comanda-mesa?l=<código>&m=<mesa>&t=<assinatura>` (o painel imprime os QR)

**O que o painel faz:** 🍽️ mapa das mesas ao vivo · 👨‍🍳 tela da cozinha/bar · 💰 caixa (abertura, sangria, fechamento com diferença) · 📋 produtos com foto, adicionais e "esgotado" em 1 toque · 📦 estoque com ficha técnica (baixa sozinho a cada venda) · 📊 relatórios e curva ABC · 👥 equipe com permissões e registro de quem fez o quê · ⚙️ Pix, cores, logo e QR das mesas.

**IA (roteador):** ✨ importa o cardápio colado · ✨ escreve a descrição do prato · 📸 lê a foto da nota fiscal e dá entrada no estoque · 📊 analisa as vendas.

**Legenda:** 🔔 gatilho · 📤 resposta · 🐘 banco Postgres · 🔀 decisão · 🤖 IA · 🧩 código""", [-1300, -560], 760, 560, 6)
f.nota("""## 1️⃣ PÁGINAS 📄
Cada página é um HTML fixo devolvido direto pelo 📤 (resposta em menos de 1 s).
A página conversa com a API (etapa 2) por `fetch`. Nada de dado fica no HTML.""", [-460, -560], 560, 700, 7)
f.nota("""## 2️⃣ API 🔌 (toda ação do painel e da mesa)
🐘 **cmd_api(jsonb)** é uma função dentro do Postgres que guarda **toda a regra de negócio**: login com senha criptografada (bcrypt), permissão por papel, comanda, caixa, estoque, relatórios.
O n8n faz **uma única chamada** por pedido, com o corpo inteiro como parâmetro **$1** (nunca colado no SQL → sem SQL injection).
🔀 Se a resposta pedir IA (`ia`), o fluxo chama o 🤖 e devolve o texto; senão responde direto.""", [160, -560], 1200, 700, 4)
f.nota("""## 3️⃣ IMAGENS 🖼️
As fotos dos produtos e o logo ficam **no próprio banco** (não somem).
🔔 `/webhook/comanda-img?id=...` lê a foto e devolve com cache de 1 dia.""", [-460, 220], 560, 420, 5)
f.nota("""## 🗄️ O BANCO (Postgres `apps_aulas`)
Tabelas `cmd_*`: loja, usuario, sessao, categoria, produto, imagem, insumo, ficha, mov_estoque, comanda, item, caixa, caixa_mov, chamado, atividade.
O arquivo `comanda/schema.sql` cria tudo (pode rodar de novo sem perder dados).""", [160, 220], 600, 300, 3)

# ── 1. páginas ──
pags = [("Página de cadastro", "comanda", "cadastro.html"), ("Painel administrador", "comanda-painel", "painel.html"), ("Cardápio da mesa", "comanda-mesa", "mesa.html")]
for i, (nome, caminho, arq) in enumerate(pags):
    y = -440 + i * 190
    w = f.webhook(f"🔔 {nome}", caminho, [-420, y])
    r = f.responde(f"📤 {nome}", pagina(AQUI / arq, cor=COR), [-160, y])
    f.liga(w, r)

# ── 2. API ──
w = f.webhook("🔔 API (POST)", "comanda-api", [200, -260], metodo="POST")
db = postgres(f, "🐘 cmd_api", "SELECT cmd_api($1::jsonb) AS r",
              "={{ JSON.stringify(Object.assign({}, (typeof $json.body === 'object' && $json.body) || {}, { ip: " + IP + " })) }}", [420, -260])
sw = switch(f, "🔀 Precisa de IA?", [
    ("descricao", "={{ $json.r && $json.r.ia === 'descricao' }}"),
    ("importar", "={{ $json.r && $json.r.ia === 'importar' }}"),
    ("nota", "={{ $json.r && $json.r.ia === 'nota' }}"),
    ("analise", "={{ $json.r && $json.r.ia === 'analise' }}"),
], [640, -260])
resp = f.responde_json("📤 Responde", "$json.r || { ok: false, erro: 'Sem resposta do banco' }", [880, -460])
f.cadeia(w, db, sw)
f.liga(sw, resp, saida=4)

SIS_DESC = ("Você é copywriter de cardápio. Escreva UMA descrição curta (até 140 caracteres) que dê água na boca, em português do Brasil, "
            "sem inventar ingrediente que não foi dito (se não disserem, descreva de forma genérica e honesta). Sem aspas, sem emoji, sem markdown.")
SIS_IMP = ("Você organiza cardápios. Recebe o texto colado pelo dono (bagunçado) e devolve SOMENTE JSON: "
           '{"categorias":[{"nome":"","icone":"(1 emoji)","destino":"cozinha|bar|nenhum","itens":[{"nome":"","descricao":"","preco":0}]}]}. '
           "Bebidas vão para o bar; itens prontos (sobremesa de vitrine, embalados) podem ser nenhum. Preço em número (32.5). "
           "Corrija erros de digitação. Não invente itens nem preços. Descrição curta só se o texto der informação.")
SIS_NOTA = ("Você lê fotos de nota fiscal ou cupom de compra de restaurante. Devolva SOMENTE JSON: "
            '{"itens":[{"descricao_nota":"texto como está na nota","nome":"nome simples do insumo","unidade":"un|kg|g|L|ml|cx|pct","qtd":0,"custo":0,"insumo_id":0}]}. '
            "custo = valor TOTAL pago pela linha. Se a quantidade for em caixa/fardo, converta para a unidade de uso quando estiver claro (ex.: fardo com 12 latas = 12 un). "
            "insumo_id = id do insumo da lista que for o MESMO produto (0 se nenhum). Não invente linhas que não estão na foto.")
SIS_ANA = ("Você é consultor de restaurantes. Recebe os números de um período e escreve uma análise curta e prática em português do Brasil, "
           "para o dono (leigo): 1) como foi o período em 2 frases; 2) 3 a 5 ações concretas para vender mais ou gastar menos, citando produtos, horários e números reais "
           "(curva ABC, margem, cancelamentos, ticket, horários fracos); 3) um alerta se houver algo estranho (muito cancelamento, margem baixa, diferença de caixa). "
           "Sem markdown, use emojis no início dos tópicos. Não invente números.")


def chat(sistema, usuario_expr, modelo="antigravity/gemini-3-flash", tokens=1500, temp=0.4):
    import json as _j
    s = _j.dumps(sistema, ensure_ascii=False).replace("{", "\\u007b").replace("}", "\\u007d")
    return ("={{ JSON.stringify({ model: '" + modelo + "', max_tokens: " + str(tokens) + ", temperature: " + str(temp) +
            ", messages: [{ role: 'system', content: " + s + " }, { role: 'user', content: " + usuario_expr + " }] }) }}")


C = "$('🐘 cmd_api').first().json.r.contexto"
ias = [
    ("descricao", "🤖 Descrição do prato", chat(SIS_DESC, "'Restaurante: ' + " + C + ".loja + ' (' + " + C + ".tipo + ')\\nPrato: ' + " + C + ".nome + '\\nCategoria: ' + " + C + ".categoria + '\\nO que o dono disse: ' + (" + C + ".ingredientes || '(nada)')", tokens=300, temp=0.8)),
    ("importar", "🤖 Organiza o cardápio", chat(SIS_IMP, "'Tipo: ' + " + C + ".tipo + '\\n\\nTEXTO:\\n' + " + C + ".texto", tokens=8000, temp=0.1)),
    ("nota", "🤖 Lê a nota fiscal", chat(SIS_NOTA, "[{ type: 'text', text: 'Insumos já cadastrados: ' + JSON.stringify(" + C + ".insumos) }, { type: 'image_url', image_url: { url: 'data:image/jpeg;base64,' + " + C + ".b64 } }]", tokens=3000, temp=0.1)),
    ("analise", "🤖 Analisa as vendas", chat(SIS_ANA, "JSON.stringify(Object.assign({}, " + C + ", { por_dia: undefined }))", tokens=1200, temp=0.5)),
]
for i, (_, nome, corpo) in enumerate(ias):
    y = -320 + i * 150
    n = ia_http(f, nome, corpo, [880, y], tempo=90000)
    r = f.responde_json("📤 " + nome[2:], "$json.choices && $json.choices[0] ? { ok: true, resultado: String($json.choices[0].message.content || '').trim() } : { ok: false, erro: 'A IA não respondeu agora. Tente de novo em instantes.' }", [1120, y])
    f.liga(sw, n, saida=i)
    f.liga(n, r)

# ── 3. imagens ──
wi = f.webhook("🔔 Imagem (GET)", "comanda-img", [-420, 360])
li = postgres(f, "🐘 Lê a imagem", "SELECT mime, b64 FROM cmd_img($1)", "={{ String($json.query.id || '').replace(/[^0-9a-f-]/g, '').slice(0, 36) || '0' }}", [-200, 360])
ex = f.se("🔀 Achou?", "={{ !!$json.b64 }}", [0, 360])
ar = para_arquivo(f, "🧩 Vira arquivo", "b64", "={{ $json.mime }}", [200, 300])
ri = f.responde_arquivo("📤 Entrega a imagem", [400, 300])
nf = f.responde("📤 Sem imagem", "não encontrada", [200, 440], tipo="text/plain; charset=UTF-8", status=404)
f.cadeia(wi, li, ex)
f.liga(ex, ar, 0)
f.liga(ex, nf, 1)
f.liga(ar, ri)

grava(f, AQUI, "comanda.json")
