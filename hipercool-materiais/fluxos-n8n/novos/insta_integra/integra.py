# -*- coding: utf-8 -*-
r"""D:\hipercool-materiais\fluxos-n8n\novos\insta_integra\integra.py

Liga os 2 fluxos de Instagram do n8n6:
  📈 Relatório do Perfil (Zj1EwQeAGBTwpShB) = DIAGNÓSTICO  → grava ig:diagnostico (30 dias) no Redis redis2
  📅 30 Dias de Posts   (Cy1QZOsj5WimgWnC) = PRODUÇÃO     → lê ig:diagnostico e planeja/escreve o mês em cima dele

    python integra.py              só gera novo_<id>.json ao lado (não mexe no servidor)
    python integra.py --publicar   gera e envia (PUT + ativa) os dois fluxos
Parte SEMPRE de original_<id>.json (baixado por baixa.py antes da mudança): rodar de novo não duplica nada.
"""
import copy
import json
import sys
import uuid
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REDIS = {"redis": {"id": "TgnZ028ccZYrorGM", "name": "Redis redis2 (landing pages)"}}
DIAG, P30 = "Zj1EwQeAGBTwpShB", "Cy1QZOsj5WimgWnC"
js = lambda nome: (AQUI / "js" / nome).read_text(encoding="utf-8")


def carrega(wid):
    return json.loads((AQUI / f"original_{wid}.json").read_text(encoding="utf-8"))


def no(w, nome):
    for n in w["nodes"]:
        if n["name"] == nome:
            return n
    raise SystemExit(f"nó não encontrado: {nome}")


def troca(texto, velho, novo, vezes=1):
    assert texto.count(velho) == vezes, f"trecho achado {texto.count(velho)}x (esperado {vezes}): {velho[:80]!r}"
    return texto.replace(velho, novo)


def novo_no(w, nome, tipo, versao, parametros, pos, credenciais=None, **extra):
    assert all(n["name"] != nome for n in w["nodes"]), f"nó repetido: {nome}"
    n = {"parameters": parametros, "id": str(uuid.uuid5(uuid.NAMESPACE_URL, w["id"] + "|" + nome)), "name": nome,
         "type": tipo, "typeVersion": versao, "position": list(pos)}
    if credenciais:
        n["credentials"] = credenciais
    n.update(extra)
    w["nodes"].append(n)
    return nome


def liga(w, a, b, saida=0):
    saidas = w["connections"].setdefault(a, {"main": []})["main"]
    while len(saidas) <= saida:
        saidas.append([])
    saidas[saida].append({"node": b, "type": "main", "index": 0})


def desliga(w, a, b):
    for saida in w["connections"].get(a, {}).get("main", []):
        saida[:] = [d for d in saida if d["node"] != b]


def switch(regras, modelo):
    """Switch com saída nomeada por valor de $json.acao (copia o formato do switch que já funciona no servidor)."""
    base = modelo["parameters"]["rules"]["values"][0]
    valores = []
    for r in regras:
        v = copy.deepcopy(base)
        c = v["conditions"]["conditions"][0]
        c["id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, "acao|" + r))
        c["rightValue"] = r
        v["outputKey"] = r
        valores.append(v)
    return {"rules": {"values": valores}, "options": {}}


# ════════════════════════════ 📈 DIAGNÓSTICO ════════════════════════════
def diagnostico():
    w = carrega(DIAG)
    # 1) desloca para a direita o que vem depois de "Lê os últimos 30 posts" (abre espaço para o novo nó)
    for nome in ("Calcula métricas do perfil", "Estrategista de Instagram", "Cérebro do estrategista", "Junta a análise",
                 "Salva o relatório (6 h)", "Desliga a trava"):
        no(w, nome)["position"][0] += 240
    no(w, "Desliga a trava")["position"][0] += 240

    # 2) lê os calendários de 30 dias (para saber quais posts vieram de lá) — uma vez só, mesmo com 30 posts chegando
    cal = novo_no(w, "🗂️ Lê os calendários de 30 dias", "n8n-nodes-base.redis", 1,
                  {"operation": "keys", "keyPattern": "p30cal:*"}, (1280, 864), REDIS,
                  executeOnce=True, alwaysOutputData=True)
    desliga(w, "Lê os últimos 30 posts", "Calcula métricas do perfil")
    liga(w, "Lê os últimos 30 posts", cal)
    liga(w, cal, "Calcula métricas do perfil")
    no(w, "Calcula métricas do perfil")["parameters"]["jsCode"] = js("diag_calcula.js")
    no(w, "Junta a análise")["parameters"]["jsCode"] = js("diag_junta.js")

    # 3) a IA passa a devolver também o "plano de ação" que o 30 Dias usa
    ag = no(w, "Estrategista de Instagram")["parameters"]["options"]
    sm = ag["systemMessage"]
    sm = troca(sm, "- nota_saude de 0 a 100.\n",
               "- nota_saude de 0 a 100.\n\n"
               "PLANO PARA O PRÓXIMO MÊS (o fluxo \"30 Dias de Posts\" usa estes campos para escrever os posts)\n"
               "- mix_formatos: quantos dos 30 dias para cada formato (carrossel, post, reels). Soma 30, mínimo 4 e máximo 16 de cada (reels são só roteiro: o dono precisa gravar). "
               "Dê mais dias ao formato que rende mais nos números; com pouco histórico, fique perto de 12/10/8.\n"
               "- hora_sugerida: \"HH:MM\" (horário de Brasília) para publicar. Use melhor_hora_exata se existir; senão, o meio da melhor faixa.\n"
               "- pilares_que_funcionam: temas/assuntos que deram mais interação (pelas legendas dos melhores posts e, se houver, por_pilar do calendário).\n"
               "- evitar: o que derrubou o engajamento (pelos piores posts).\n"
               "- regras_para_legenda: 3 a 6 regras práticas para quem vai escrever (tamanho da legenda pelos números de legendas curtas x longas, tipo de gancho na 1ª linha, chamada para ação).\n"
               "- Se posts_do_calendario_30_dias.posts > 0, compare os posts do calendário com os outros e diga isso no resumo.\n")
    sm = troca(sm, '"ideias":[{"formato":"Carrossel|Reels|Foto","titulo":"","gancho":"","por_que":""}]}',
               '"ideias":[{"formato":"Carrossel|Reels|Foto","titulo":"","gancho":"","por_que":""}],'
               '"mix_formatos":{"carrossel":12,"post":10,"reels":8},"hora_sugerida":"11:00","pilares_que_funcionam":[""],'
               '"evitar":[""],"regras_para_legenda":[""]}')
    ag["systemMessage"] = sm
    no(w, "Cérebro do estrategista")["parameters"]["options"]["maxTokens"] = 6000

    # 4) guarda o diagnóstico enxuto por 30 dias (o 30 Dias de Posts lê daqui)
    g = novo_no(w, "💾 Guarda o diagnóstico (30 dias)", "n8n-nodes-base.redis", 1,
                {"operation": "set", "key": "ig:diagnostico", "value": "={{ $('Junta a análise').first().json.diagnostico }}",
                 "keyType": "string", "expire": True, "ttl": 2592000}, (2560, 864), REDIS)
    desliga(w, "Salva o relatório (6 h)", "Desliga a trava")
    liga(w, "Salva o relatório (6 h)", g)
    liga(w, g, "Desliga a trava")

    # 5) página: cartão "Plano para o próximo mês" + botão que abre o 30 Dias já com o diagnóstico ligado
    mt = no(w, "Monta o relatório")["parameters"]
    c = mt["jsCode"]
    c = troca(c, "const top = (R.top || [])",
              "const PL = R.plano || {}, MX = PL.mix_formatos || {}, CA = R.calendario || {};\n"
              "const NOMEF = { carrossel: '🎠 Carrossel', post: '📷 Post', reels: '🎬 Reels' };\n"
              "const blocoPlano = `<div class=\"card c12 plano\"><h2>📅 Plano para o próximo mês</h2>"
              "<p class=\"mu\">O fluxo <b>30 Dias de Posts</b> usa este diagnóstico: escolhe quantos posts de cada formato, o melhor horário e corrige o que está em “O que melhorar”.</p>"
              "<div class=\"mix\">${['carrossel', 'post', 'reels'].map(f => `<span class=\"tag\">${NOMEF[f]}: <b>${MX[f] || 0}</b> dias</span>`).join('')}"
              "${PL.hora_sugerida ? `<span class=\"tag\">⏰ publicar às <b>${esc(PL.hora_sugerida)}</b></span>` : ''}</div>"
              "${CA.posts ? `<h3>📊 Posts que vieram do calendário de 30 dias</h3><p class=\"mu\">${CA.posts} post${CA.posts === 1 ? '' : 's'} do calendário: média de <b>${dec(CA.media_calendario)}</b> interações x <b>${dec(CA.media_outros)}</b> dos outros posts.</p>${barras(CA.por_pilar || [], 'posts')}` : ''}"
              "<a class=\"btn cta\" href=\"posts30?diag=1\">📅 Criar 30 dias de posts com base neste diagnóstico</a></div>`;\n"
              "const top = (R.top || [])")
    c = troca(c, "${blocoIA}\n", "${blocoIA}\n${blocoPlano}\n")
    c = troca(c, "#tip{position:fixed",
              ".plano{border-left:4px solid var(--bom)}.mix{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.mix .tag{font-size:13px;padding:5px 11px}"
              ".btn.cta{margin:14px 0 0;background:var(--s1);color:#fff;border:0;font-size:15px;padding:11px 16px}\n#tip{position:fixed")
    mt["jsCode"] = c

    # 6) notas
    n = no(w, "Nota · Gerar")["parameters"]
    n["width"] = 1960
    n["content"] = troca(n["content"], "💾 **Junta a análise** → **Salva o relatório (6 h)** → 🔓 **Desliga a trava**.",
                         "🗂️ **Lê os calendários de 30 dias**: marca quais posts vieram do fluxo 📅 30 Dias de Posts e mede qual **pilar** rende mais.\n"
                         "💾 **Junta a análise** → **Salva o relatório (6 h)** → 💾 **Guarda o diagnóstico (30 dias)** (chave `ig:diagnostico`) → 🔓 **Desliga a trava**.\n"
                         "🔗 O 📅 **30 Dias de Posts** lê `ig:diagnostico` para planejar o mês (formatos, horário, o que melhorar, regras de legenda).")
    n = no(w, "Nota · Comece aqui")["parameters"]
    n["height"] = 760
    n["content"] += ("\n\n## 🔗 TRABALHA JUNTO COM O 📅 30 DIAS DE POSTS\n"
                     "🔎 Este é o **diagnóstico**; o 📅 30 Dias é a **produção**. No fim do relatório tem o botão **📅 Criar 30 dias de posts com base neste diagnóstico**.\n"
                     "🔁 Ciclo: diagnóstico ➜ mês planejado para corrigir o que está fraco ➜ posts publicados ➜ o próximo diagnóstico mede se melhorou (por pilar).")
    return w


# ════════════════════════════ 📅 30 DIAS DE POSTS ════════════════════════════
def producao(modelo_switch):
    w = carrega(P30)

    # 1) formulário: opção "usar o diagnóstico" (já vem marcada quando chega pelo botão do relatório: ?diag=1)
    f = no(w, "📤 Entrega o formulário")["parameters"]
    h = f["responseBody"]
    h = troca(h, "@media(max-width:560px)",
              ".diag{margin-top:18px;border:1px dashed var(--pri);border-radius:14px;padding:12px 14px}"
              ".diag .chk{display:flex;gap:10px;align-items:flex-start;margin-top:6px}.diag .chk input{width:auto;margin-top:5px}"
              ".diag .chk small{display:block}\n@media(max-width:560px)")
    h = troca(h, '  <p class="erro" id="erro" role="alert"></p>',
              '  <div class="diag"><label class="chk"><input type="checkbox" id="diag"><span>🔎 Usar o diagnóstico do Instagram'
              '<small>A IA lê o 📈 Relatório do Perfil (da conta conectada ao n8n) e planeja o mês para corrigir o que está fraco. '
              'Se estiver velho, faz um novo sozinha (até 2 minutos a mais).</small></span></label>'
              '<label class="chk"><input type="checkbox" id="hora_diag" checked><span>⏰ Publicar no melhor horário do diagnóstico'
              '<small>Troca o horário acima pelo horário em que o perfil tem mais interação.</small></span></label></div>\n'
              '  <p class="erro" id="erro" role="alert"></p>')
    h = troca(h, "    d.estilo = el('input[name=estilo]:checked').value;",
              "    d.estilo = el('input[name=estilo]:checked').value; d.diag = el('#diag').checked; d.hora_diag = el('#hora_diag').checked;")
    h = troca(h, "  el('#exemplo').addEventListener",
              "  if (new URLSearchParams(location.search).get('diag') === '1') el('#diag').checked = true;\n  el('#exemplo').addEventListener")
    f["responseBody"] = h

    # 2) confere o pedido: guarda a escolha e o endereço do n8n (para chamar o relatório)
    c = no(w, "🧩 Confere o pedido")["parameters"]
    s = c["jsCode"]
    s = troca(s, "const erros = [];",
              "const usar_diag = b.diag === true || b.diag === 'true' || b.diag === '1';\n"
              "const hora_diag = usar_diag && b.hora_diag !== false && b.hora_diag !== 'false';\n"
              "const erros = [];")
    s = troca(s, "auto: false, pilares: [], dias: [] };",
              "auto: false, pilares: [], dias: [], diagnostico: usar_diag ? { status: 'buscando' } : null };")
    s = troca(s, "chave_limite: '<SEGREDO_REMOVIDO>'", "usar_diag, hora_diag, base, chave_limite: '<SEGREDO_REMOVIDO>'")
    c["jsCode"] = s

    # 3) novos nós do diagnóstico entre "Responde com o link" e a Estrategista
    no(w, "🤖 Estrategista")["position"] = [448, 2400]
    no(w, "🧠 Cérebro da estrategista")["position"] = [448, 2624]
    no(w, "🛟 Reserva · Cérebro da estrategista")["position"] = [448, 2800]
    le = novo_no(w, "📖 Lê o diagnóstico", "n8n-nodes-base.redis", 1,
                 {"operation": "get", "propertyName": "diag", "key": "ig:diagnostico", "keyType": "string", "options": {}},
                 (112, 1792), REDIS, alwaysOutputData=True)
    serve = novo_no(w, "🧩 O diagnóstico serve?", "n8n-nodes-base.code", 2, {"jsCode": js("p30_serve.js")}, (112, 1984))
    sw = novo_no(w, "🔀 E o diagnóstico?", "n8n-nodes-base.switch", modelo_switch["typeVersion"],
                 switch(["pronto", "pedir", "esperar", "sem"], modelo_switch), (112, 2176))
    pede = novo_no(w, "🌐 Pede um diagnóstico novo", "n8n-nodes-base.httpRequest", 4.2,
                   {"url": "={{ $json.url }}", "options": {"timeout": 30000, "response": {"response": {"responseFormat": "text", "neverError": True}}}},
                   (416, 2080), onError="continueRegularOutput")
    espera = novo_no(w, "⏳ Espera 25 segundos", "n8n-nodes-base.wait", 1.1, {"amount": 25}, (416, 1856),
                     webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, P30 + "|espera|diag")))
    prep = novo_no(w, "🧩 Prepara o diagnóstico", "n8n-nodes-base.code", 2, {"jsCode": js("p30_prepara.js")}, (112, 2400))
    desliga(w, "📤 Responde com o link", "🤖 Estrategista")
    liga(w, "📤 Responde com o link", le)
    liga(w, le, serve)
    liga(w, serve, sw)
    liga(w, sw, prep, 0)      # pronto
    liga(w, sw, pede, 1)      # pedir
    liga(w, sw, espera, 2)    # esperar
    liga(w, sw, prep, 3)      # sem
    liga(w, pede, espera)
    liga(w, espera, le)
    liga(w, prep, "🤖 Estrategista")

    # 4) Estrategista recebe o diagnóstico e explica cada dia (motivo)
    e = no(w, "🤖 Estrategista")["parameters"]
    e["text"] = troca(e["text"], "+ $('🧩 Confere o pedido').first().json.inicio }}",
                      "+ $('🧩 Confere o pedido').first().json.inicio + ($('🧩 Prepara o diagnóstico').first().json.texto ? "
                      "'\\n\\nDIAGNÓSTICO DO INSTAGRAM (planeje o mês para corrigir o que está fraco):\\n' + $('🧩 Prepara o diagnóstico').first().json.texto : '') }}")
    sm = e["options"]["systemMessage"]
    sm = troca(sm, "- Use SÓ produtos, preços e ofertas informados. Português do Brasil com acentos.\n",
               "- Use SÓ produtos, preços e ofertas informados. Português do Brasil com acentos.\n"
               "- motivo de cada dia: até 120 caracteres dizendo por que o post está ali.\n\n"
               "SE VIER \"DIAGNÓSTICO DO INSTAGRAM\"\n"
               "- Use EXATAMENTE a quantidade de cada formato de mix_formatos_obrigatorio (soma 30), sem 3 iguais seguidos. Isso vale no lugar da regra de 12/10/8.\n"
               "- Cada item de o_que_melhorar precisa ser atacado em pelo menos 3 dias, e o motivo desses dias diz qual item ele corrige.\n"
               "- Prefira os pilares/temas de pilares_que_funcionam e os assuntos dos top5. Não repita o que está em evitar.\n"
               "- Adapte as ideias do diagnóstico ao negócio e use nos 10 primeiros dias.\n"
               "- Se a frequencia sugerida for menor que 1 por dia, mantenha 30 dias mesmo assim (o dono escolhe quais aprovar).\n")
    sm = troca(sm, '"tema":"","objetivo":"atrair"}', '"tema":"","objetivo":"atrair","motivo":""}')
    e["options"]["systemMessage"] = sm
    no(w, "🧠 Cérebro da estrategista")["parameters"]["options"]["maxTokens"] = 8000

    no(w, "🧩 Organiza o plano")["parameters"]["jsCode"] = js("p30_organiza.js")

    # 5) Redatora segue as regras de legenda do diagnóstico e o motivo de cada dia
    rd = no(w, "🤖 Redatora")["parameters"]
    rd["text"] = troca(rd["text"], "+ JSON.stringify($json.dias, null, 1) }}",
                       "+ JSON.stringify($json.dias, null, 1) + ($('🧩 Prepara o diagnóstico').first().json.redacao ? "
                       "'\\n\\nREGRAS DO DIAGNÓSTICO DO INSTAGRAM (siga ao escrever):\\n' + $('🧩 Prepara o diagnóstico').first().json.redacao : '') }}")
    regra = ("- FIEL: não invente preço, desconto, prazo ou produto que não esteja nos dados do negócio.\n")
    extra = ("- Se o dia tiver motivo, o post precisa cumprir esse motivo.\n"
             "- Se vierem REGRAS DO DIAGNÓSTICO, elas valem mais que as regras de tamanho acima.\n")
    for nome in ("🤖 Redatora", "🤖 Redatora (refazer)"):
        o = no(w, nome)["parameters"]["options"]
        o["systemMessage"] = troca(o["systemMessage"], regra, regra + extra)
    rf = no(w, "🤖 Redatora (refazer)")["parameters"]
    rf["text"] = troca(rf["text"], "objetivo: $json.post.objetivo,", "objetivo: $json.post.objetivo, motivo: $json.post.motivo || '',")
    rf["text"] = troca(rf["text"], "+ ($json.pedido || 'uma versão diferente e mais forte') }}",
                       "+ ($json.pedido || 'uma versão diferente e mais forte') + ($json.regras_diag ? "
                       "'\\n\\nREGRAS DO DIAGNÓSTICO DO INSTAGRAM (siga ao escrever):\\n' + $json.regras_diag : '') }}")
    ca = no(w, "🧩 Confere a ação")["parameters"]
    ca["jsCode"] = troca(ca["jsCode"], "post: d, negocio: cal.negocio } }];",
                         "post: d, negocio: cal.negocio, regras_diag: (cal.diagnostico && cal.diagnostico.redacao) || '' } }];")

    # 6) página do calendário: cartão do diagnóstico no topo + "por que este post" em cada dia
    pg = no(w, "📤 Entrega a página")["parameters"]
    p = pg["responseBody"]
    p = troca(p, "</style>",
              ".diagc{background:var(--sup);border:1px dashed var(--borda);border-radius:14px;padding:12px 14px;margin-top:14px;font-size:14px}"
              ".diagc ul{margin:6px 0 6px 20px}.diagc small{color:var(--tx2)}</style>")
    p = troca(p, '<div class="ctrl" id="ctrl" hidden>', '<div class="diagc" id="diagc" hidden></div>\n<div class="ctrl" id="ctrl" hidden>')
    p = troca(p, "    el('#barra-wrap').hidden = CAL.status === 'pronto';\n",
              "    el('#barra-wrap').hidden = CAL.status === 'pronto';\n"
              "    var DG = CAL.diagnostico; el('#diagc').hidden = !DG;\n"
              "    if (DG) el('#diagc').innerHTML = DG.status === 'buscando' ? '🔎 Lendo o diagnóstico do Instagram (se estiver velho, a IA faz um novo: até 2 minutos)…'\n"
              "      : DG.status === 'sem' ? '⚠️ ' + esc(DG.aviso)\n"
              "      : '<b>🔎 Mês planejado em cima do diagnóstico de @' + esc(DG.usuario) + '</b> (' + new Date(DG.geradoEm).toLocaleDateString('pt-BR')"
              " + (DG.nota_saude != null ? ' · nota ' + DG.nota_saude + ' de 100' : '') + ')'\n"
              "        + (DG.o_que_melhorar && DG.o_que_melhorar.length ? '<ul>' + DG.o_que_melhorar.map(function (x) { return '<li>🔧 ' + esc(x) + '</li>'; }).join('') + '</ul>' : '')\n"
              "        + '<small>Formatos do mês: 🎠 ' + DG.mix_formatos.carrossel + ' · 📷 ' + DG.mix_formatos.post + ' · 🎬 ' + DG.mix_formatos.reels"
              " + (DG.hora_sugerida ? ' · ⏰ melhor horário ' + esc(DG.hora_sugerida) : '') + (DG.aviso ? ' · ' + esc(DG.aviso) : '') + '</small>';\n")
    p = troca(p, "ESTADO[d.estado] + '</span></p>'\n      + (d.erro ?",
              "ESTADO[d.estado] + '</span></p>'\n      + (d.motivo ? '<p class=\"msg\">🎯 Por que este post: ' + esc(d.motivo) + '</p>' : '')\n      + (d.erro ?")
    pg["responseBody"] = p

    # 7) notas
    n = no(w, "Nota · Coluna 1")["parameters"]
    n["height"] = 3000
    n["content"] += ("\n\n## 🔎 DIAGNÓSTICO DO INSTAGRAM (opcional)\n"
                     "Quando o dono marca **Usar o diagnóstico** (ou chega pelo botão do 📈 Relatório do Perfil):\n"
                     "📖 **Lê o diagnóstico** (`ig:diagnostico`, gravado pelo Relatório) ➜ 🧩 **O diagnóstico serve?** (tem até 7 dias e é da mesma conta?)\n"
                     "🔀 **pronto** ➜ usa · **pedir** ➜ 🌐 chama o Relatório para fazer um novo ➜ ⏳ espera 25 s e lê de novo (até ~2,5 min) · **sem** ➜ segue sem\n"
                     "🧩 **Prepara o diagnóstico** ➜ a 🤖 Estrategista usa a mistura de formatos, os pontos a melhorar e as ideias; a 🤖 Redatora segue as regras de legenda.\n"
                     "🎯 Cada dia ganha um **motivo** (aparece no calendário) e o horário vira o melhor horário do diagnóstico.")
    n = no(w, "Nota · Comece aqui")["parameters"]
    n["height"] = max(n.get("height") or 955, 1000)
    n["content"] = troca(n["content"], "## 🧠 Os 2 cérebros",
                         "## 🔗 Trabalha junto com o 📈 Relatório do Perfil\n"
                         "O Relatório é o **diagnóstico**; este fluxo é a **produção**. Marque **🔎 Usar o diagnóstico** no formulário: o mês é planejado para corrigir o que está fraco no perfil.\n\n"
                         "## 🧠 Os 2 cérebros")
    return w


def publica(wid, w):
        sys.path.insert(0, r"D:\hipercool-materiais\fluxos-n8n\ferramentas")
        from n8n_servidor import api, CONFIG_OK
        ok = tuple(CONFIG_OK) + ("binaryMode",)  # binaryMode: manter como está (o 30 Dias desenha imagens)
        corpo = {"name": w["name"], "nodes": w["nodes"], "connections": w["connections"],
                 "settings": {k: v for k, v in (w.get("settings") or {}).items() if k in ok}}
        st, r = api("PUT", f"/workflows/{wid}", corpo)
        print("PUT", wid, st, r.get("message", ""))
        if st == 400 and "settings" in str(r.get("message", "")):
            corpo["settings"].pop("binaryMode", None)
            st, r = api("PUT", f"/workflows/{wid}", corpo)
            print("PUT sem binaryMode", wid, st, r.get("message", ""))
        if st >= 300:
            raise SystemExit(2)
        st2, r2 = api("POST", f"/workflows/{wid}/activate")
        print("ativar", wid, st2, r2.get("active"), r2.get("message", ""))


if __name__ == "__main__":
    d = diagnostico()
    p = producao(no(carrega(DIAG), "Qual caminho?"))
    for wid, w in ((DIAG, d), (P30, p)):
        (AQUI / f"novo_{wid}.json").write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
        print("gerado", wid, len(w["nodes"]), "nós")
    if "--publicar" in sys.argv:
        publica(DIAG, d)
        publica(P30, p)
