# -*- coding: utf-8 -*-
"""📊 Radar dos canais (YouTube público, sem login e sem chave): inscritos, vídeos, views dos 15 últimos, quem cresceu,
vídeo zerado e canal parado. Todo dia 07:20 e no botão.

GET  /webhook/gratis-radar            painel
POST /webhook/gratis-radar-atualizar  lê agora
GET  /webhook/gratis-radar-dados      último retrato em JSON (para outros fluxos)

A lista de canais vem de D:\\postador-de-videos\\config\\rede_canais.json (só nome, @, id e status; nada de credencial).
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).parent
COMUM = AQUI.parent / "comum"
sys.path.insert(0, str(AQUI.parent))
from n8nlib import Fluxo, js  # noqa: E402

ler = lambda n: (COMUM / n).read_text(encoding="utf-8")  # noqa: E731
REDE = Path(r"D:\postador-de-videos\config\rede_canais.json")
canais = []
if REDE.exists():
    for c in json.loads(REDE.read_text(encoding="utf-8")).get("canais", []):
        if c.get("yt_id"):
            canais.append({k: c.get(k, "") for k in ("slug", "nome", "handle", "yt_id", "status")})
if not canais:  # exemplo para quem importar sem o arquivo do postador
    canais = [{"slug": "youtube", "nome": "YouTube Brasil", "handle": "@YouTubeBrasil", "yt_id": "UCBR8-60-B28hp2BmDPdntcQ", "status": "ativo"}]

f = Fluxo("📊 Radar dos canais grátis sem chave (YouTube público: inscritos, views, zerados)")
f.settings["timezone"] = "America/Sao_Paulo"
f.nota("## 📊 Radar dos canais\nPainel em **/webhook/gratis-radar**. Lê todo dia às 7h20 (e no botão) os canais da lista "
       "do nó ⚙️ (vem do rede_canais.json do postador; edite à vontade).\n\nSem login e sem chave: RSS público do canal "
       "(15 vídeos mais novos com visualizações) e a página pública do canal (inscritos e nº de vídeos). Guarda um "
       "retrato por dia no Redis (120 dias) e compara com o anterior: quem ganhou views, vídeo zerado depois de 48 h, "
       "canal sem vídeo há 3 dias.", (-60, -440), 600, 320, 4)
ag = f.agenda("⏰ Todo dia 7h20", "20 7 * * *", (0, 0))
at = f.webhook("🔔 Atualizar agora (POST)", "gratis-radar-atualizar", (0, 200), "POST")
ra = f.responde_json("📤 Responde: lendo", "{ ok: true, msg: 'Lendo os canais; recarregue o painel em 1 a 2 minutos.' }", (240, 200))
le_ant = f.redis_le("📖 Lê o retrato anterior", "radar:ultimo", "retrato", (480, 100))
f.nos[-1]["executeOnce"] = True
lista = f.codigo("⚙️ Lista de canais (edite aqui)", "// Canais lidos pelo radar (público: nome, @ e id do canal).\n"
                 "const CANAIS = " + json.dumps(canais, ensure_ascii=False, indent=1) + ";\n"
                 "return CANAIS.map(c => ({ json: c }));", (720, 100))
laco = f.lote("🔁 Um canal por vez", (960, 100))
lc = f.codigo("🔎 Lê o canal", js(AQUI, "le_canal.js"), (1200, 220))
cmp_ = f.codigo("🧩 Compara com a leitura anterior", js(AQUI, "compara.js"), (1200, 0))
g1 = f.redis_grava("💾 Guarda o retrato", "radar:ultimo", "={{ $json.retrato }}", (1440, 0))
g2 = f.redis_grava("💾 Guarda o dia (120 dias)", "=radar:{{ $('🧩 Compara com a leitura anterior').first().json.dia }}",
                   "={{ $('🧩 Compara com a leitura anterior').first().json.retrato }}", (1680, 0), validade=120 * 86400)
f.liga(ag, le_ant)
f.cadeia(at, ra, le_ant)
f.cadeia(le_ant, lista, laco)
f.liga(laco, cmp_, 0)
f.liga(laco, lc, 1)
f.liga(lc, laco)
f.cadeia(cmp_, g1, g2)

p = f.webhook("🔔 Painel (GET)", "gratis-radar", (0, 520))
lp = f.redis_le("📖 Lê o retrato", "radar:ultimo", "retrato", (240, 520))
pp = f.codigo("🧩 Desenha o painel", js(AQUI, "painel.js", PAGINA=ler("pagina.js")), (480, 520))
f.cadeia(p, lp, pp, f.responde("📤 Entrega o painel", "={{ $json.html }}", (720, 520)))
dd = f.webhook("🔔 Dados (GET)", "gratis-radar-dados", (0, 720))
ld = f.redis_le("📖 Lê o retrato (dados)", "radar:ultimo", "retrato", (240, 720))
f.cadeia(dd, ld, f.responde("📤 Entrega os dados", "={{ $json.retrato || '{}' }}", (480, 720),
                            tipo="application/json; charset=UTF-8"))
print(f.grava(AQUI / "radar_canais_gratis.json"), len(canais), "canais")
