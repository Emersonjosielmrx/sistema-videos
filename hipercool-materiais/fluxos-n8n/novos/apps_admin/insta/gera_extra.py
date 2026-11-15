# -*- coding: utf-8 -*-
"""Blocos extras da Central (incluídos no fim do gera.py): encerrar gincana com pódio, anunciar sorteio, ⏰ encerramento automático."""

ARTE_JS = """// Arte 1080x1920 do resultado (pódio da gincana ou ganhador do sorteio).
const esc = s => String(s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
return $input.all().map(it => { const r = __R__; const cor = /^#[0-9a-fA-F]{6}$/.test(r.cor) ? r.cor : '#C13584';
  const lista = (r.podio || r.ganhadores || []).map((g, i) => `<div class="l">${['🥇', '🥈', '🥉'][i] || (i + 1) + 'º'} @${esc(g.username || g.u || "jogador")}${g.pontos != null ? ` <small>${g.pontos} pts</small>` : ''}</div>`).join('') || '<div class="l">Ninguém pontuou 😅</div>';
  const titulo = r.podio ? 'RESULTADO DA GINCANA' : 'RESULTADO DO SORTEIO';
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>*{margin:0;box-sizing:border-box}body{width:1080px;height:1920px;font-family:Montserrat,Inter,sans-serif;color:#fff;
  background:linear-gradient(160deg,#1a0b2e,${cor} 60%,#f59e0b);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:100px}
  .t{font-size:46px;font-weight:800;letter-spacing:5px}.s{font-size:58px;font-weight:800;margin:24px 0 10px}.tr{font-size:190px;margin:30px 0}
  .l{font-size:78px;font-weight:800;margin:18px 0}.l small{font-size:40px;opacity:.8}.p{margin-top:60px;font-size:44px;background:rgba(255,255,255,.16);border-radius:30px;padding:26px 40px}
  .f{position:absolute;bottom:110px;font-size:36px;opacity:.85}</style></head><body><div class="t">${titulo}</div><div class="s">${esc(r.titulo)}</div><div class="tr">🏆</div>${lista}
  ${r.premio ? `<div class="p">🎁 ${esc(r.premio)}</div>` : ''}<div class="f">@${esc(r.conta)} · obrigado a todos que participaram! 💜</div></body></html>`;
  const pasta = (r.podio ? 'gincana-' : 'sorteio-') + r.codigo;
  return { json: { ...r, corpo: JSON.stringify({ area: 'eventos', deck: pasta, nome: 'resultado', largura: 1080, altura: 1920, html }) } }; });"""


def blocos(f, sw, ig, postgres, CX, OFICINA, PUB):
    story = lambda nome, url_expr, pos: ig(nome, {"resource": "story", "operation": "createStory", "storyMediaType": "IMAGE", "storyImageUrl": url_expr}, pos)
    desenha = lambda nome, pos: f.http(nome, OFICINA + "/html_png", pos, metodo="POST", corpo_json="={{ $json.corpo }}", tempo=150000, nunca_erro=True, continua_no_erro=True)

    # encerrar gincana pelo painel
    ge = postgres(f, "🐘 Encerra a gincana", "SELECT ig_gincana_encerrar($1::int) AS r", "={{ [" + CX + ".gincana_id] }}", [900, 60])
    f.liga(sw, ge, saida=4)
    ga = f.codigo("🧩 Arte do pódio", ARTE_JS.replace("__R__", "it.json.r"), [1120, 60])
    gp = desenha("🛠️ Oficina desenha o pódio", [1340, 60])
    gs = story("📸 Pódio no story", "=" + PUB + "/videos/arquivo/{{ $json.arquivo }}", [1560, 60])
    gav = f.codigo("🧩 Mensagem para cada jogador", """const r = $('🧩 Arte do pódio').first().json;
const msgs = (r.jogadores || []).map(j => ({ json: { ig_id: j.ig_id, texto: j.pos <= 3 && j.pontos > 0
  ? `🏆 PARABÉNS! Você ficou em ${j.pos}º lugar na gincana "${r.titulo}" com ${j.pontos} pontos!${j.pos == 1 && r.premio ? ' Você ganhou: ' + r.premio + '. Vamos combinar a entrega por aqui. 🎁' : ''}`
  : `🏁 A gincana "${r.titulo}" terminou! Você fez ${j.pontos} pontos e ficou em ${j.pos}º. Obrigado por jogar! 💜` } }));
return msgs.length ? msgs : [{ json: { vazio: true } }];""", [1780, 60])
    gdm = ig("📸 Avisa cada jogador", {"resource": "message", "operation": "sendText", "recipientId": "={{ $json.ig_id }}", "messageText": "={{ $json.texto }}"}, [2000, 60])
    gj = f.codigo("🧩 Conta os avisos", "return [{ json: { n: $input.all().filter(i => !i.json.error && !i.json.vazio).length } }];", [2220, 60])
    gfi = postgres(f, "🐘 Guarda o resultado", "SELECT ig_gincana_final($1::int, $2::jsonb)",
                   "={{ [$('🧩 Arte do pódio').first().json.gincana_id, JSON.stringify({ arte: $('🛠️ Oficina desenha o pódio').first().json.arquivo || '', story: $('📸 Pódio no story').first().json.id || null, avisados: $json.n })] }}", [2440, 60])
    f.cadeia(ge, ga, gp, gs, gav, gdm, gj, gfi)
    f.liga(gfi, f.responde_json("📤 Gincana encerrada", "{ ok: true, arte: '" + PUB + "/videos/arquivo/' + ($('🛠️ Oficina desenha o pódio').first().json.arquivo || ''), story: !!$('📸 Pódio no story').first().json.id, avisados: $('🧩 Conta os avisos').first().json.n }", [2660, 60]))

    # anunciar sorteio: arte → (story) → direct aos ganhadores
    sa = f.codigo("🧩 Arte do ganhador", ARTE_JS.replace("__R__", "it.json.r.contexto"), [900, 220])
    f.liga(sw, sa, saida=5)
    sp = desenha("🛠️ Oficina desenha o ganhador", [1120, 220])
    sst = f.se("🔀 Postar no story?", "={{ $('🧩 Arte do ganhador').first().json.story }}", [1340, 220])
    ss = story("📸 Ganhador no story", "=" + PUB + "/videos/arquivo/{{ $('🛠️ Oficina desenha o ganhador').first().json.arquivo }}", [1560, 160])
    sm = f.codigo("🧩 Avisos aos ganhadores", """const r = $('🧩 Arte do ganhador').first().json;
const out = r.avisar ? (r.ganhadores || []).filter(g => g.id).map(g => ({ json: { ig_id: g.id, texto: `🎉 PARABÉNS, @${g.u}! Você ganhou o sorteio "${r.titulo}"${r.premio ? ': ' + r.premio : ''}! Responda aqui para combinarmos a entrega. 🎁` } })) : [];
return out.length ? out : [{ json: { vazio: true } }];""", [1780, 220])
    sdm = ig("📸 Avisa o ganhador", {"resource": "message", "operation": "sendText", "recipientId": "={{ $json.ig_id }}", "messageText": "={{ $json.texto }}"}, [2000, 220])
    sj = f.codigo("🧩 Conta os avisos do sorteio", "return [{ json: { n: $input.all().filter(i => !i.json.error && !i.json.vazio).length } }];", [2220, 220])
    sg = postgres(f, "🐘 Guarda o anúncio", "SELECT ig_sorteio_anuncio($1, $2::jsonb)",
                  "={{ [$('🧩 Arte do ganhador').first().json.codigo, JSON.stringify({ arte: $('🛠️ Oficina desenha o ganhador').first().json.arquivo || '', story: $('🧩 Arte do ganhador').first().json.story, avisados: $json.n, em: new Date().toISOString() })] }}", [2440, 220])
    f.cadeia(sa, sp, sst)
    f.liga(sst, ss, 0)
    f.liga(sst, sm, 1)
    f.liga(ss, sm)
    f.cadeia(sm, sdm, sj, sg)
    f.liga(sg, f.responde_json("📤 Sorteio anunciado", "{ ok: true, arte: '" + PUB + "/videos/arquivo/' + ($('🛠️ Oficina desenha o ganhador').first().json.arquivo || ''), avisados: $('🧩 Conta os avisos do sorteio').first().json.n }", [2660, 220]))

    # ⏰ encerra sozinho as gincanas cuja última pista fechou
    ag2 = f.agenda("⏰ Encerra gincanas (30 min)", "*/30 * * * *", [-420, 1500])
    ge2 = postgres(f, "🐘 Gincanas para encerrar", "SELECT ig_gincana_encerrar(id) AS r FROM ig_gincanas_a_encerrar() id", "", [-200, 1500], sempre=False)
    ga2 = f.codigo("🧩 Arte do pódio (auto)", ARTE_JS.replace("__R__", "it.json.r"), [20, 1500])
    gp2 = f.http("🛠️ Desenha o pódio (auto)", OFICINA + "/html_png", [240, 1500], metodo="POST", corpo_json="={{ $json.corpo }}", tempo=150000, nunca_erro=True, continua_no_erro=True)
    gs2 = story("📸 Pódio no story (auto)", "=" + PUB + "/videos/arquivo/{{ $json.arquivo }}", [460, 1500])
    gf2 = postgres(f, "🐘 Guarda o resultado (auto)", "SELECT ig_gincana_final($1::int, $2::jsonb)",
                   "={{ [$('🧩 Arte do pódio (auto)').item.json.gincana_id, JSON.stringify({ arte: $('🛠️ Desenha o pódio (auto)').item.json.arquivo || '', story: $json.id || null, auto: true })] }}", [680, 1500])
    f.cadeia(ag2, ge2, ga2, gp2, gs2, gf2)
