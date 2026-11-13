"""Kit da marca: tudo o que o vídeo/foto profissional precisa saber de uma conta (cores, nome, produto, fatos
permitidos, narradora, convite, hashtags). Fonte: config\\marcas_instagram.json + produtos.json do Veo.

Regra de contato (produtos.json _meta, 16/10): telefone/WhatsApp/site NUNCA vão para o vídeo nem para a voz;
o convite é "link no perfil" / "chame no direct".
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MARCAS = RAIZ / "config" / "marcas_instagram.json"
PRODUTOS = Path(r"D:\veo\beta\pos_producao\assets\produtos.json")
FONTES = Path(r"D:\hipercool-materiais\assets\fonts")
FONTE_BLACK = str(FONTES / "Montserrat-Black.ttf")
FONTE_XBOLD = str(FONTES / "Montserrat-ExtraBold.ttf")
FONTE_BOLD = str(FONTES / "Montserrat-Bold.ttf") if (FONTES / "Montserrat-Bold.ttf").exists() else FONTE_XBOLD

# edge-tts só tem 3 vozes pt-BR e o Antonio é proibido (memória feedback_vozes). 26/10 19:40 (dono: "o final 'chame
# a gente' está saindo em outra língua"): a Thalita é MULTILÍNGUE — no "direct" ela troca pro inglês — e ainda falha
# ao acaso (NoAudioReceived) -> todas com a Francisca (só português), ritmo diferente por marca
VOZES = {"padrao": ("pt-BR-FranciscaNeural", "+4%"),
         "inovarecom.ia": ("pt-BR-FranciscaNeural", "+6%"),
         "futebolcom.ia2": ("pt-BR-FranciscaNeural", "+8%"),
         "sintetizerisada": ("pt-BR-FranciscaNeural", "+2%")}

# público de cada produto, em palavras de gente (o estrategista escreve pautas para essas pessoas)
PUBLICO = {"hermes_call": "donos de empresa e equipes de vendas que atendem e vendem pelo WhatsApp",
           "cardapio_digital": "donos de restaurante, lanchonete, açaiteria, pizzaria e delivery",
           "agenda_ia": "clínicas, consultórios, salões, barbearias, estúdios e prestadores de serviço que vivem de horário marcado",
           "superchat": "empresas que atendem clientes por WhatsApp, Instagram e Telegram ao mesmo tempo",
           "agente_tarefas": "profissionais e empreendedores com muita tarefa no dia",
           # 26/10: contas novas de 25/10 estavam sem público nem hashtag (legenda saía sem #)
           "disparo_massa": "lojas, infoprodutores e empresas que precisam avisar muitos clientes pelo WhatsApp",
           "follow_up": "vendedores e empresas que perdem cliente que some depois do orçamento",
           "vps_infra": "quem tem sistema, site ou automação e precisa de servidor seguro sem dor de cabeça",
           "fabrica_conteudo": "empresas e profissionais que precisam postar conteúdo e aparecer no Google sem tempo"}

HASHTAGS = {"hermes_call": ["#whatsappbusiness", "#vendas", "#atendimentoaocliente", "#inteligenciaartificial", "#automacao"],
            "cardapio_digital": ["#cardapiodigital", "#delivery", "#restaurante", "#lanchonete", "#gestaoderestaurante"],
            "agenda_ia": ["#agendamentoonline", "#clinica", "#salaodebeleza", "#barbearia", "#inteligenciaartificial"],
            "superchat": ["#atendimentoaocliente", "#crm", "#whatsappbusiness", "#automacao"],
            "agente_tarefas": ["#produtividade", "#inteligenciaartificial", "#automacao"],
            "disparo_massa": ["#whatsappmarketing", "#disparoemmassa", "#vendas", "#automacao", "#marketingdigital"],
            "follow_up": ["#followup", "#vendas", "#whatsappbusiness", "#automacao", "#inteligenciaartificial"],
            "vps_infra": ["#vps", "#servidor", "#hospedagem", "#seguranca", "#tecnologia"],
            "fabrica_conteudo": ["#marketingdeconteudo", "#seo", "#blog", "#automacao", "#inteligenciaartificial"]}


# produtos.json (do Veo, compartilhado) tem nomes sem acento; aqui o nome vai pra tela E pra voz ("Fabrica" lido como
# verbo) -> corrigido só no kit, sem mexer no arquivo dos outros projetos (26/10)
ACENTO = {"Fabrica de Conteudo": "Fábrica de Conteúdo", "Recuperacao de Carrinho": "Recuperação de Carrinho",
          "Landing Page e Comunicacao": "Landing Page e Comunicação", "Gestao de Grupos IA": "Gestão de Grupos IA"}


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return padrao


def rgb(hexa):
    h = (hexa or "#000000").lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _luz(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contas_produto():
    """Contas que vendem um produto do catálogo (as outras são de tema)."""
    return [c for c, m in _ler(MARCAS, {}).get("contas", {}).items() if m.get("produto")]


# 01/11 (dona: "por que não está usando esses estilos nos vídeos de energia solar? cada um é uma variante muito boa"):
# as 3 empresas solares (clientes reais) também saem no Claude Code Video (Remotion). Só fatos que elas mesmas dizem
# (bio/pasta); nunca preço, valor, "zerar" ou garantia. dono_tag = fotos do DONO DELA aprovadas pelo revisor de rosto
# (foto_na_hora) — nunca o Emerson; pasta_reels = onde o postador próprio dela pega o Reel pronto (sidecar legenda_insta).
_FATOS_SOLAR = "Gerar a própria energia com o sol diminui a conta de luz (sem prometer valor, zerar ou garantir)"
SOLARES = {
    "advance_novoestrela": {
        "marca": "Advance Solar", "arroba": "@advance_novoestrela", "cor": "#F59E0B", "apoio": "#0F172A",
        "texto": "#0F172A", "tema": "energia solar em Castanhal-PA", "dono_tag": "advance_clone",
        "pasta_reels": r"D:\ms-energy\videos\reels_advance",
        "publico": "donos de casa, comércio e sítio em Castanhal e região que acham a conta de luz alta",
        "fatos": ["Empresa de energia solar de Castanhal e região, no Pará",
                  "Faz projeto e instalação de energia solar para casa, comércio e campo",
                  # 01/11 (dona): o Luiz é o RESPONSÁVEL pela Advance, não o dono — nunca chamar de dono
                  "O Luiz, responsável pela Advance, acompanha a obra de perto",
                  "Orçamento grátis pelo WhatsApp que fica no perfil do Instagram", _FATOS_SOLAR],
        "hashtags": ["#energiasolar", "#castanhal", "#castanhalpa", "#painelsolar", "#advanceenergiasolar"]},
    "globosolarenergiag": {
        "marca": "Globo Solar", "arroba": "@globosolarenergiag", "cor": "#EA3A21", "apoio": "#1A222D",
        "texto": "#FFFFFF", "tema": "energia solar em Concórdia do Pará", "dono_tag": "globo_clone",
        "pasta_reels": r"D:\ms-energy\videos\reels_globo",
        "publico": "donos de casa, comércio e propriedade rural em Concórdia do Pará e região",
        "fatos": ["Empresa de energia solar em Concórdia do Pará",
                  "Financia e parcela o sistema de energia solar",
                  "Faz projeto e instalação para casa, comércio e campo",
                  "Orçamento pelo WhatsApp que fica no perfil do Instagram", _FATOS_SOLAR],
        "hashtags": ["#energiasolar", "#concordiadopara", "#energiasolarpara", "#painelsolar", "#globosolar"]},
    "msenergycap": {
        "marca": "MS Energy", "arroba": "@msenergycap", "cor": "#C81E37", "apoio": "#111111", "texto": "#FFFFFF",
        "tema": "energia solar no Pará", "dono_tag": "msenergy_clone",
        "pasta_reels": r"D:\ms-energy\videos\shorts_veo",
        "publico": "donos de casa, comércio e propriedade rural no Pará que acham a conta de luz alta",
        "fatos": ["Empresa real de energia solar no Pará, com quase dez anos no mercado",
                  "Atende casas, comércios, indústrias e propriedades rurais",
                  "Faz projeto, instalação e manutenção de sistemas de energia solar",
                  "Orçamento grátis pelo WhatsApp que fica no perfil do Instagram", _FATOS_SOLAR],
        "hashtags": ["#energiasolar", "#energiasolarpara", "#painelsolar", "#contadeluz", "#msenergy"]},
}


def _kit_solar(conta):
    s = SOLARES[conta]
    cor, apoio, texto = rgb(s["cor"]), rgb(s["apoio"]), rgb(s["texto"])
    escuro = apoio if _luz(apoio) < 70 else tuple(int(c * 0.22) for c in cor)
    destaque = cor if _luz(cor) > 60 else apoio
    if _luz(cor) > 150 and _luz(texto) > 150:
        texto = (18, 18, 22)
    convite = "Orçamento pelo WhatsApp do perfil" if conta == "globosolarenergiag" else "Orçamento grátis"
    return {
        "conta": conta, "arroba": s["arroba"], "marca": s["marca"], "tema": s["tema"],
        "cor": cor, "apoio": apoio, "texto": texto, "escuro": escuro, "destaque": destaque, "cor_hex": s["cor"],
        "produto": {"id": "solar_" + conta, "nome": s["marca"], "cta_curto": s["fatos"][0]},
        "produto_id": "solar_" + conta, "nome_produto": s["marca"], "cliente": True, "solar": True,
        "publico": s["publico"], "fatos": s["fatos"], "exemplo_real": None,
        "permitido": [] if conta == "globosolarenergiag" else ["orçamento grátis"],  # Globo não diz "grátis" na bio
        "convite": convite, "convite_voz": f"Peça seu orçamento com a {s['marca']}.",
        "voz": "pt-BR-FranciscaNeural", "ritmo": "+5%", "hashtags": s["hashtags"],
        "dono_tag": s["dono_tag"], "pasta_reels": s["pasta_reels"], "link_pasta": None,
    }


def kit(conta):
    if conta in SOLARES:
        return _kit_solar(conta)
    m = (_ler(MARCAS, {}).get("contas") or {}).get(conta)
    if not m:
        raise KeyError(f"{conta} não está em {MARCAS}")
    prod = next((p for p in _ler(PRODUTOS, {}).get("produtos", []) if p.get("id") == m.get("produto")), None)
    if prod:
        for errado, certo in ACENTO.items():
            prod = {kk: (v.replace(errado, certo) if isinstance(v, str) else v) for kk, v in prod.items()}
    cor, apoio = rgb(m["cor"]), rgb(m.get("apoio", "#111111"))
    # fundo escuro da marca: a cor de apoio se ela já é escura; senão a cor principal bem escurecida
    escuro = apoio if _luz(apoio) < 70 else tuple(int(c * 0.22) for c in cor)
    # cor de destaque legível sobre fundo escuro (karaokê, números): a principal, ou a de apoio se a principal é escura
    destaque = cor if _luz(cor) > 60 else apoio
    # 26/10 (verificadores): "Chame no direct" branco sobre turquesa claro (~1,5:1) -> texto escuro sobre cor clara
    texto = rgb(m.get("texto", "#FFFFFF"))
    if _luz(cor) > 150 and _luz(texto) > 150:
        texto = (18, 18, 22)
    voz, ritmo = VOZES.get(conta, VOZES["padrao"])
    fatos = []
    if prod:
        fatos = [x for x in (prod.get("descricao"), prod.get("cta_curto"), prod.get("cta_longo")) if x]
    if m.get("cliente") and conta == "msenergysolar.pa":
        # 25/10 22h (dono): formato misto no MS Energy = ele no Veo + instalações REAIS + narradora. Cliente real:
        # fatos do roteiro_ms; "orçamento grátis" É fato dele (nos produtos não); arroba real @msenergycap
        return {
            "conta": conta, "arroba": "@msenergycap", "marca": "MS Energy", "tema": m.get("tema"),
            "cor": cor, "apoio": apoio, "texto": texto, "escuro": escuro, "destaque": destaque,
            "cor_hex": m["cor"], "produto": {"id": "ms_energy", "nome": "MS Energy",
                                             "cta_curto": "Energia solar para casa, comércio e campo no Pará"},
            "produto_id": "ms_energy", "nome_produto": "MS Energy", "cliente": True,
            "publico": "donos de casa, comércio e propriedade rural no Pará que acham a conta de luz alta",
            "fatos": ["Empresa real de energia solar no Pará, com quase dez anos no mercado",
                      "Atende casas, comércios, indústrias e propriedades rurais",
                      "Faz projeto, instalação e manutenção de sistemas de energia solar",
                      "Orçamento grátis pelo WhatsApp que fica no perfil do Instagram",
                      "Gerar a própria energia com o sol diminui a conta de luz (sem prometer valor, zerar ou garantir)"],
            "permitido": ["orçamento grátis"], "exemplo_real": None,
            "convite": "Orçamento grátis", "convite_voz": "Peça seu orçamento grátis com a MS Energy.",
            "voz": "pt-BR-FranciscaNeural", "ritmo": "+5%",  # 26/10: Thalita troca de língua (ver VOZES)
            "hashtags": ["#energiasolar", "#energiasolarpara", "#paragominas", "#painelsolar", "#contadeluz"],
            "link_pasta": m.get("link"),
        }
    return {
        "conta": conta, "arroba": "@" + conta, "marca": m["marca"], "tema": m.get("tema"),
        "cor": cor, "apoio": apoio, "texto": texto, "escuro": escuro, "destaque": destaque,
        "cor_hex": m["cor"], "produto": prod, "produto_id": (prod or {}).get("id"),
        "nome_produto": (prod or {}).get("nome") or m["marca"],
        "publico": PUBLICO.get((prod or {}).get("id"), m.get("tema") or ""),
        "fatos": fatos, "exemplo_real": (prod or {}).get("exemplo"),
        # 26/10 (verificadores): o botão dizia "Link no perfil" e a voz "chame no direct" -> mesma ação nos dois
        "convite": "Chame no direct", "convite_voz": "Chame a gente no direct.",
        "voz": voz, "ritmo": ritmo,
        "hashtags": HASHTAGS.get((prod or {}).get("id"), []),
        "link_pasta": m.get("link"),
    }
