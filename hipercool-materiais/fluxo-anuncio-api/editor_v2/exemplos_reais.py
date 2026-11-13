"""V5 (02/11): cópia da V4 MIX em que os vídeos de exemplo são os vídeos REAIS das solares (Advance e Globo) no lugar do
apartamento. Os vídeos ficam no Redis (chave <pre>arq:exemplo-advance.mp4 / exemplo-globo.mp4, base64, sem validade —
o catbox parou de aceitar envios) e passam pelo /<rota>-arquivo, igual às trilhas.
Subir os vídeos: python sobe_exemplos.py. Usado por gera_versoes.py: aplica(w, nivel)."""
import json
from pathlib import Path

AMOSTRA = Path(__file__).parent.parent / "editor" / "amostra"
EXEMPLOS = {
    "advance": {"rotulo": "☀️ Exemplo: Advance Solar", "info": "rapaz mostrando a instalação no telhado, 39 s",
                "dados": json.loads((AMOSTRA / "dados_advance.json").read_text(encoding="utf-8"))},
    "globo": {"rotulo": "⭐ Exemplo: Globo Solar", "info": "depoimento de cliente, 30 s",
              "dados": json.loads((AMOSTRA / "dados_globo.json").read_text(encoding="utf-8"))},
}
# V6+ (03/11): + 3 vídeos CRUS de verdade (pessoa falando, pausas e vícios, sem legenda/logo/trilha), para a diferença
# entre o antes e o depois ficar nítida. Entrevistas do AG JORNALISMO no YouTube, licença Creative Commons CC BY
# (crédito no texto do botão e no nome do negócio). Cortados em videos_prontos\crus\corta_crus.py (sem o nome na tela).
CRED = "AG Jornalismo (YouTube, CC BY)"
CRUS = {
    # vídeo que a dona mandou (D:\downloads\Video teste.mp4, 03/11): primeiros 80,7 s, cortado numa pausa
    "teste": {"rotulo": "🎥 Cru: Luis (WordPress x Astro)", "info": "vídeo cru da dona, 81 s, falando sem cortes, com 'não é' e 'é é'",
              "dados": {"tipo": "servico", "marca": "Criação de sites", "titulo": "Por que trocar o WordPress pelo fluxo com Astro e Skills",
                        "detalhes": "O Luis conta a experiência dele: quem já tem um fluxo no WordPress pode continuar, mas quem vai fazer o primeiro site hoje ganha muito mais com o Astro (sem servidor, sem penca de plug-in), e com Skills ele monta tudo na hora que quiser.", "instagram": ""}},
    "caue": {"rotulo": "🎙️ Cru: Cauê (muitos 'tipo')", "info": "vídeo cru, 73 s, cheio de 'tipo', 'assim' e pausas · " + CRED,
             "dados": {"tipo": "outro", "marca": "AG Jornalismo", "titulo": "Cauê Ueda conta como foi o workshop sobre o centro de São Paulo",
                       "detalhes": "Entrevista com Cauê Ueda, do Coletivo Baixo Centro, sobre um workshop de projeto para o centro de São Paulo que esqueceu as pessoas que moram lá.", "instagram": ""}},
    "alderon": {"rotulo": "🎙️ Cru: Alderon (muitos 'não é')", "info": "vídeo cru, 75 s, cheio de 'não é' e pausas · " + CRED,
                "dados": {"tipo": "outro", "marca": "AG Jornalismo", "titulo": "Alderon Costa fala sobre participação popular no centro de SP",
                          "detalhes": "Entrevista com Alderon Costa, da Rede Rua, sobre a falta de participação popular de verdade nos projetos para o centro de São Paulo.", "instagram": ""}},
    "luciana": {"rotulo": "🎙️ Cru: Luciana (urbanista)", "info": "vídeo cru, 86 s, entrevista sem edição · " + CRED,
                "dados": {"tipo": "outro", "marca": "AG Jornalismo", "titulo": "Urbanista Luciana Itikawa critica projeto que exclui ambulantes",
                          "detalhes": "Entrevista com a urbanista Luciana Itikawa: o desenho urbano não resolve questões sociais; são as questões sociais que devem pautar o projeto.", "instagram": ""}},
}


def exemplos(nivel):
    return {**EXEMPLOS, **(CRUS if nivel >= 6 else {})}


def aplica(w, nivel):
    rota = f"editor-reel-v{nivel}"
    nos = {n["name"]: n for n in w["nodes"]}
    EXEMPLOS = exemplos(nivel)
    nomes = "|".join(EXEMPLOS)

    # ── página: 2 botões de exemplo com os dados de cada empresa ──
    pg = nos["📤 Entrega a página"]["parameters"]
    h = pg["responseBody"]
    botao = '<div><button class="btn sec" type="button" id="ex">🎬 Usar vídeo de exemplo</button></div>'
    assert h.count(botao) == 1
    h = h.replace(botao, '<div class="exs">' + "".join(
        f'<button class="btn sec" type="button" data-ex="{k}">{e["rotulo"]}</button>' for k, e in EXEMPLOS.items()) + "</div>")
    a = h.index("  el('#ex').addEventListener('click', function () {")
    b = h.index("  });\n", h.index("el('#detalhes').value", a)) + len("  });\n")
    dados = {k: {"info": e["info"], **{c: e["dados"].get(c, "") for c in ("tipo", "marca", "titulo", "detalhes", "instagram")}} for k, e in EXEMPLOS.items()}
    h = h[:a] + (
        "  var EXEMPLOS = " + json.dumps(dados, ensure_ascii=False) + ";\n"
        "  Array.prototype.forEach.call(document.querySelectorAll('[data-ex]'), function (bt) { bt.addEventListener('click', function () {\n"
        "    var k = bt.getAttribute('data-ex'), d = EXEMPLOS[k]; envioAtual = null; enviando = false;\n"
        f"    VIDEO = 'exemplo-' + k; el('#prev').src = '{rota}-arquivo?id=exemplo-' + k + '.mp4'; el('#prev').hidden = false; el('#barra').hidden = true;\n"
        "    el('#info').innerHTML = '<span class=\"ok\">✅ Vídeo real de exemplo</span> (' + d.info + ')';\n"
        "    el('#tipo').value = d.tipo; el('#marca').value = d.marca; el('#titulo').value = d.titulo;\n"
        "    el('#instagram').value = d.instagram ? '@' + d.instagram : ''; el('#detalhes').value = d.detalhes;\n"
        "  }); });\n") + h[b:]
    h = h.replace("</style>", ".exs{display:flex;gap:8px;flex-wrap:wrap}.exs .btn{flex:1 1 180px}</style>", 1)
    pg["responseBody"] = h

    # ── pedido: aceita exemplo-advance / exemplo-globo ──
    c = nos["🧩 Confere o pedido"]["parameters"]
    v = c["jsCode"]
    antes = "(b.video === 'exemplo' ? 'exemplo' : '')"
    assert v.count(antes) == 1
    v = v.replace(antes, f"(/^exemplo-({nomes})$/.test(String(b.video || '')) ? String(b.video) : '')")
    antes = f"exemplo: video === 'exemplo' ? `${{base}}/webhook/{rota}-arquivo?id=exemplo.mp4` : '',"
    assert v.count(antes) == 1, "linha do exemplo no Confere o pedido mudou"
    c["jsCode"] = v.replace(antes, f"exemplo: video.startsWith('exemplo-') ? `${{base}}/webhook/{rota}-arquivo?id=${{video}}.mp4` : '',   // vídeos reais das solares, guardados no Redis")

    # ── entrega do arquivo: os 2 vídeos vêm do Redis ──
    c = nos["🧩 Vira arquivo"]["parameters"]
    v = c["jsCode"]
    antes = "const b64 =String($input.first().json.arquivo || '');\n"
    assert v.count(antes) == 1
    c["jsCode"] = v.replace(antes, antes +
        f"if (/^exemplo-({nomes})\\.mp4$/.test(id)) {{   // vídeos reais de exemplo, guardados no Redis\n"
        "  if (!b64) return [{ json: { existe: false } }];\n"
        "  return [{ json: { existe: true }, binary: { data: await this.helpers.prepareBinaryData(Buffer.from(b64, 'base64'), id, 'video/mp4') } }];\n"
        "}\n")
    return w
