# -*- coding: utf-8 -*-
"""Roteiro dos shorts da MS Energy — empresa REAL de energia solar no Para; o objetivo e pedido de orcamento.

Substitui, so no MS Energy, os agentes de meme do Veo (agents.py / llm_client.gerar_prompt_viral): eles inventavam
um cenario sem ver a foto, pediam neon e "choque no 1o segundo" e o video saia da foto em ~1 s; a fala repetia
("vai zerar") e prometia o que a lei nao deixa (analise de 22/10: docs\\ANALISE_CAMPANHA.md).

Tres formatos:
  foto_real    - foto REAL de instalacao do Instagram da empresa como 1o quadro + narracao do proprio Veo
  apresentador - consultor(a) gerado(a) pelo Veo falando para a camera num cenario do Para
  video_real   - (22/10) trechos de VIDEO REAL do Google Fotos da empresa + narradora (video_real_ms.py), sem Veo
"""
import json
import random
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\veo\beta")

HIST = Path(r"D:\ms-energy\cache\historico_roteiros.json")
FOTOS_DIR = Path(r"D:\ms-energy\assets\fotos_instagram")
QUADROS_DIR = FOTOS_DIR / "quadros_916"

EMPRESA = ("MS Energy (solucoes fotovoltaicas), empresa real de energia solar no Para, Brasil, com quase dez anos no "
           "mercado. Atende casas, comercios, industrias e propriedades rurais: projeto, instalacao e manutencao de "
           "sistemas de energia solar. Orcamento gratis pelo WhatsApp que fica no perfil do Instagram @msenergycap.")
CTA_FALADO = "Orçamento grátis com a MS Energy."  # 25/10: mais curto pra fala com resposta caber nos 8 s do Veo
INSTAGRAM = "@msenergycap"

# (id, cenario do apresentador, assunto) — duvidas e motivos reais de quem pensa em instalar
PAUTAS = [
    ("calor_ar", "casa", "No calor do Para o ar-condicionado nao para e a conta sobe; o mesmo sol forte gera energia."),
    ("chuva", "casa", "Chove muito no Para: painel funciona em dia nublado? Gera menos, mas gera; o projeto considera o ano todo."),
    ("noite", "casa", "E de noite? A energia que sobra durante o dia vira credito na conta de luz e e usada depois."),
    ("manutencao", "telhado", "Manutencao e simples: limpeza de vez em quando e revisao; a MS Energy tambem faz a manutencao."),
    ("financiamento", "casa", "Da para financiar o sistema; muita gente troca a conta de luz pela parcela."),
    ("rural", "rural", "No campo: bomba d'agua, irrigacao, resfriador de leite e galpao com energia propria."),
    ("comercio", "comercio", "Comercio e industria gastam mais de dia, justamente quando o sol esta gerando."),
    ("valorizacao", "casa", "Imovel com energia solar fica mais valorizado na hora de vender ou alugar."),
    ("processo", "casa", "Como funciona: visita tecnica, projeto, aprovacao na distribuidora, instalacao e acompanhamento."),
    ("lei_nova", "casa", "Com a lei nova da energia solar ainda vale a pena? A regra mudou, mas gerar a propria energia continua compensando."),
    ("telhado_tipo", "telhado", "Seu telhado serve? Ceramica, fibrocimento, metalico, laje ou ate no chao; a visita tecnica avalia."),
    ("quantas_placas", "casa", "Quantas placas voce precisa? Depende do consumo da sua conta de luz; o orcamento gratis calcula."),
    ("conta_foto", "casa", "Primeiro passo: mandar uma foto da conta de luz no WhatsApp para receber o orcamento gratis."),
    ("aumento_tarifa", "casa", "A tarifa de energia sobe de tempos em tempos; quem gera a propria energia sente muito menos."),
    ("investimento", "casa", "Energia solar e investimento, nao gasto: o sistema se paga com a economia ao longo do tempo."),
    ("monitoramento", "casa", "Da para acompanhar pelo celular quanto o sistema esta gerando."),
    ("experiencia", "telhado", "Quase dez anos instalando energia solar no Para."),
    ("durabilidade", "telhado", "Painel solar dura muitos anos e o equipamento tem garantia de fabrica."),
    ("energia_limpa", "rural", "Energia limpa do sol: menos dependencia da distribuidora e mais tranquilidade."),
    ("empresa_local", "comercio", "Empresa do Para, que conhece o sol, a chuva e os telhados da regiao."),
]

# reserva escrita a mao (LLM fora do ar): (fala sem o convite, texto do topo)
RESERVA = {
    "calor_ar": ("Calor do Pará, ar-condicionado ligado e conta alta? O sol pode pagar isso.", "Calor e conta alta?"),
    "chuva": ("Painel solar funciona em dia nublado? Funciona, gera menos, mas gera o ano todo.", "Funciona na chuva?"),
    "noite": ("E de noite? O que sobra de dia vira crédito na sua conta de luz.", "E à noite?"),
    "manutencao": ("Painel solar dá trabalho? A manutenção é simples e a gente cuida disso.", "Dá trabalho?"),
    "financiamento": ("Dá para financiar e trocar a conta de luz pela parcela do seu sistema.", "Dá para financiar?"),
    "rural": ("Bomba d'água, irrigação e galpão funcionando com a energia do sol na sua propriedade.", "Energia solar no campo"),
    "comercio": ("Seu comércio gasta mais de dia, justamente quando o sol está gerando energia.", "Energia para o comércio"),
    "valorizacao": ("Casa com energia solar vale mais na hora de vender ou alugar.", "Sua casa vale mais"),
    "processo": ("Visita técnica, projeto, aprovação, instalação e acompanhamento: a gente faz tudo.", "Como funciona?"),
    "lei_nova": ("Com a lei nova ainda vale a pena? Vale, gerar sua energia continua compensando.", "Ainda vale a pena?"),
    "telhado_tipo": ("Telha cerâmica, metálica, laje ou até no chão: a visita técnica avalia o seu.", "Seu telhado serve?"),
    "quantas_placas": ("Quantas placas você precisa? Depende da sua conta, e a gente calcula para você.", "Quantas placas?"),
    "conta_foto": ("Manda uma foto da sua conta de luz no WhatsApp e a gente calcula seu sistema.", "Primeiro passo"),
    "aumento_tarifa": ("A tarifa de energia sobe sempre, e quem gera a própria energia sente bem menos.", "Cansou dos aumentos?"),
    "investimento": ("Energia solar não é gasto, é investimento que se paga com a economia.", "Gasto ou investimento?"),
    "monitoramento": ("Você acompanha pelo celular quanto o seu sistema está gerando, todo dia.", "Tudo pelo celular"),
    "experiencia": ("Quase dez anos instalando energia solar em casas, comércios e fazendas do Pará.", "Experiência no Pará"),
    "durabilidade": ("Painel solar dura muitos anos e tem garantia de fábrica, sem dor de cabeça.", "Quanto tempo dura?"),
    "energia_limpa": ("Energia limpa do sol, mais tranquilidade e menos dependência da distribuidora.", "Energia do sol"),
    "empresa_local": ("Somos do Pará e conhecemos o sol, a chuva e os telhados daqui.", "Empresa do Pará"),
}

CENARIOS = {
    "casa": ("standing in front of a single-story house with dark blue solar panels on its roof, on a sunny street of a "
             "small town in northern Brazil (Para state), tropical trees, bright natural daylight"),
    "telhado": ("standing on a flat concrete rooftop next to neat rows of dark blue solar panels, wearing a white safety "
                "helmet, bright tropical sun, small town in northern Brazil (Para state) in the background"),
    "rural": ("standing next to rows of ground-mounted solar panels on a farm in Para, Brazil, green pasture and a wooden "
              "fence behind, bright natural daylight"),
    "comercio": ("standing in front of a small commercial building with dark blue solar panels on its roof, on a sunny "
                 "street of a town in northern Brazil (Para state), natural daylight"),
}
PERSONAS = [
    ("A friendly Brazilian solar energy technician in his thirties with short dark hair, wearing a plain solid red "
     "polo shirt with no logo, no text and no print", "He"),
    ("A friendly Brazilian solar energy consultant woman in her thirties with dark hair tied back, wearing a plain "
     "solid red polo shirt with no logo, no text and no print", "She"),
]

HASHTAGS_BASE = ["#energiasolar", "#energiasolarpara", "#para", "#paragominas", "#painelsolar", "#contadeluz",
                 "#energiafotovoltaica", "#msenergy"]
HASHTAGS_PAUTA = {"rural": ["#energiasolarrural", "#agronegocio"], "comercio": ["#energiasolarcomercial"],
                  "energia_limpa": ["#energialimpa"], "financiamento": ["#financiamentosolar"]}

_PROIBIDO = [
    (r"\bzer(a|ar|ou|ada|ado|ando|ar[aá]|o)\b", "promete zerar a conta"),
    (r"r\$\s*0|conta\s+zero|de\s+gra[çc]a", "promete conta zero/de graca"),
    (r"\b(cemig|equatorial|celpa|enel|light|copel|cpfl|energisa|coelba|neoenergia|celesc|cosern)\b", "cita concessionaria"),
    (r"n[aã]o\s+quer(em)?\s+que\s+voc[eê]|segredo|ningu[eé]m\s+(te\s+)?cont|escond", "tom de conspiracao/clickbait"),
    (r"\d", "tem numero"),
    (r"nunca\s+mais\s+pag|pare\s+de\s+pagar|100\s*%", "promessa absoluta"),
    (r"garant(?!ia\s+de\s+f[aá]brica)", "promete garantia de resultado"),
]


# palavras que SO existem com acento: escritas sem ele = texto sem acentuacao (legenda feia, Veo pronuncia errado)
_SEM_ACENTO = (r"\b(nao|voce|voces|tambem|manutencao|instalacao|orcamento|dificil|facil|agua|ate|entao|sao|estao|"
               r"propria|proprio|credito|creditos|tecnica|eletrica|comercio|unico|ultimo|economico|camera|ja|so|"
               r"energetica|solucao|regiao|paineis|util|anuncio|preco)\b")


def _norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def problemas_texto(texto):
    """Lista o que fere as regras de propaganda (vazia = ok). Cita o trecho: sem ele a correção do LLM repetia o erro
    (carrossel de 22/10: 3x "promete garantia de resultado" sem saber qual palavra)."""
    t = (texto or "").lower()
    erros = []
    for padrao, motivo in _PROIBIDO:
        m = re.search(padrao, t)
        if m:
            palavra = re.search(r"\w*" + re.escape(m.group(0)) + r"\w*", t[max(m.start() - 20, 0):m.end() + 20])
            erros.append(f"{motivo} (tire \"{palavra.group(0) if palavra else m.group(0)}\")")
    return erros


def _hist():
    try:
        return json.loads(HIST.read_text("utf-8"))
    except Exception:
        return []


def registrar(roteiro, stem):
    h = _hist()
    h.append({"data": datetime.now().isoformat(timespec="seconds"), "stem": stem, "tipo": roteiro["tipo"],
              "pauta": roteiro["pauta"], "fala": roteiro["fala"], "foto": roteiro.get("foto"),
              "clipes": roteiro.get("clipes"), "estilo": roteiro.get("estilo"), "cenas": roteiro.get("cenas")})
    HIST.parent.mkdir(parents=True, exist_ok=True)
    HIST.write_text(json.dumps(h[-200:], ensure_ascii=False, indent=1), "utf-8")


def escolher_pauta(evitar=(), formato="reel", hist=None):
    """Entre as 5 pautas mais 'frias' (rodízio: nada repete em seguida), a que mais rende no Instagram (25/10: funil,
    bin\\funil_insta.py — Thompson no placar insta_pautas; sem dado ainda = sorteio, como antes)."""
    usadas = {}
    for i, item in enumerate(_hist() if hist is None else hist):
        usadas[item.get("pauta")] = i
    candidatas = sorted((p for p in PAUTAS if p[0] not in evitar), key=lambda p: usadas.get(p[0], -1))[:5]
    try:
        import funil_insta
        return funil_insta.escolher(candidatas, "msenergycap", formato)
    except Exception:  # noqa: BLE001
        return random.choice(candidatas)


def fotos_boas(com_reprovadas=False):
    """Fotos reais do Instagram aprovadas pela visao: sem texto/telefone, sem rosto (nao fazer cliente real 'falar'),
    nitidas e mostrando energia solar. 29/10 (dona): sem painel torto nem reparo de instalacao ruim dos outros
    (revisar_instalacao.py grava "instalacao"; reprovada sai daqui)."""
    try:
        ind = json.loads((FOTOS_DIR / "indice.json").read_text("utf-8"))
    except Exception:
        return []
    boas = []
    for nome, it in ind.items():
        v = it.get("visao") or {}
        # equipamento (inversor) tem marca escrita no aparelho, que o Veo deforma
        if (v.get("boa_para_video") and v.get("foto_real") and not v.get("telefone_ou_link")
                and v.get("texto_sobreposto") == "nenhum" and int(v.get("rostos") or 0) == 0
                and int(v.get("qualidade") or 0) >= 6 and v.get("mostra") != "equipamento"
                and (com_reprovadas or (it.get("instalacao") or {}).get("ok", True))
                and (FOTOS_DIR / nome).exists()):
            boas.append((nome, it))
    return boas


def _aerea(item):
    d = ((item.get("visao") or {}).get("descricao_en") or "").lower()
    return any(p in d for p in ("aerial", "drone", "overhead"))


def escolher_foto(evitar=()):
    """Foto usada ha mais tempo (sorteio entre as 6 mais 'frias') que ainda rende um quadro 9:16 decente.
    Foto de drone vai por ultimo: o Veo a trata como filmagem de drone e sai voando (testes de 22/10)."""
    boas = [b for b in fotos_boas() if b[0] not in evitar]
    usadas = {}
    for i, item in enumerate(_hist()):
        if item.get("foto"):
            usadas[item["foto"]] = i
    boas.sort(key=lambda b: (_aerea(b[1]), usadas.get(b[0], -1)))
    while boas:
        escolhida = random.choice(boas[:6])
        if quadro_916(escolhida[0], float((escolhida[1].get("visao") or {}).get("foco_x") or 0.5)):
            return escolhida
        boas.remove(escolhida)
    return None


def _aparar_bordas(im):
    """Tira faixas pretas que ja vem na foto (print de video): linhas/colunas da borda quase pretas e lisas."""
    import numpy as np
    a = np.asarray(im.convert("L"), dtype=float)
    linhas = [(r.mean() > 16 or r.std() > 10) for r in a]
    colunas = [(c.mean() > 16 or c.std() > 10) for c in a.T]
    if not any(linhas) or not any(colunas):
        return im
    y0, y1 = linhas.index(True), len(linhas) - linhas[::-1].index(True)
    x0, x1 = colunas.index(True), len(colunas) - colunas[::-1].index(True)
    return im.crop((x0, y0, x1, y1))


def quadro_916(nome, foco_x=0.5):
    """Recorta a foto para 9:16 (720x1280) em volta do assunto: foto fora de 9:16 virava faixa preta no Veo.
    None se o recorte ficaria pequeno demais (ampliar mais de ~2,2x borra)."""
    from PIL import Image
    QUADROS_DIR.mkdir(parents=True, exist_ok=True)
    out = QUADROS_DIR / (Path(nome).stem + "_916.jpg")
    if out.exists():
        return out
    im = _aparar_bordas(Image.open(FOTOS_DIR / nome).convert("RGB"))
    w, h = im.size
    if w / h > 9 / 16:
        nw = int(h * 9 / 16)
        x0 = int(min(max(foco_x * w - nw / 2, 0), w - nw))
        im = im.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w * 16 / 9)
        y0 = (h - nh) // 2
        im = im.crop((0, y0, w, y0 + nh))
    if im.size[0] < 330:
        return None
    im.resize((720, 1280), Image.LANCZOS).save(out, quality=95)
    return out


# 31/10 (dona: "não quero só perguntas, mas vídeos criativos também, 'vem pra X empresa solar' de forma criativa em
# ambientes inusitados; temos que ter todos os tipos e formatos e ir usando os que têm mais resultado"): ESTILO do Reel
# do apresentador/clone. Cada conta escolhe pelo placar insta_estilos (Thompson; sem dado = testa), placar_estilos.py
# conta as vitórias. (instrução para o LLM, pergunta no gancho?, cenários do estilo ou None = o da pauta)
ESTILOS = {
    "pergunta": ("Estilo PERGUNTA E RESPOSTA: a fala abre com a dúvida do cliente e responde em seguida.", True, None),
    "criativo": ("Estilo CRIATIVO E BEM-HUMORADO: a pessoa está num lugar inusitado e brinca com isso, ligando a cena à "
                 "energia do sol e chamando para a empresa (ex. do TOM, não copie: 'Até aqui na rede da praia o sol "
                 "trabalha pra mim. Bora gerar energia na sua casa também?'). Leve, simpático, sem exagero, sem "
                 "pergunta sem resposta. Cite a cena na fala.", False,
                 ["rede", "rio", "cozinha", "acai", "futebol", "praia", "feira"]),
    "dica": ("Estilo DICA RÁPIDA: uma dica prática e verdadeira sobre energia solar, dita com segurança, em tom de quem "
             "ensina um amigo. Nada de pergunta.", False, None),
    "mito": ("Estilo MITO OU VERDADE: a fala começa com 'Mito ou verdade:' + uma crença comum sobre energia solar e "
             "responde logo, explicando em poucas palavras.", True, None),
    "chamada": ("Estilo CHAMADA DIRETA: fala animada e confiante convidando quem está cansado da conta de luz alta a "
                "conhecer a empresa, com um motivo concreto (projeto feito para a casa, instalação caprichada, "
                "financiamento). Nada de pergunta no fim.", False, None),
    "historia": ("Estilo MINI-HISTÓRIA: em primeira pessoa, uma situação do dia a dia de um cliente típico (sem nome "
                 "real, sem números) que mudou depois do sistema solar, contada em duas frases com começo e fim.",
                 False, None),
    "comparacao": ("Estilo ANTES E DEPOIS: a fala compara a vida antes (conta alta, medo de ligar o ar) e depois de "
                   "gerar a própria energia, sem números nem promessa de conta zerada.", False,
                   ["cozinha", "rede", "feira"]),
    "erro": ("Estilo ERRO COMUM: aponta um erro que muita gente comete ao instalar energia solar (escolher só pelo "
             "preço, telhado sem avaliação, instalador sem visita) e diz o que fazer certo.", False, None),
    # 06/11 dona (referencias-instagram.zip, modelos M3/M4/M11 do plano de posts dos perfis de solar que mais engajam)
    "como_funciona": ("Estilo COMO FUNCIONA EM 20 SEGUNDOS: explica o caminho da energia em ordem — sol na placa, "
                      "inversor, a casa usa na hora, o que sobra vira crédito na conta para a noite. Simples, como "
                      "para um vizinho, sem números e sem prometer conta zerada.", False, None),
    "falta_luz": ("Estilo VERDADE QUE POUCA GENTE CONTA: explica que sistema sem bateria desliga quando falta luz "
                  "na rua (é segurança de quem trabalha na rede) e que, para ter luz na queda, precisa de bateria. "
                  "Honesto, sem vender bateria se a empresa não vende.", True, None),
    "conta_zera": ("Estilo MITO OU VERDADE: 'Mito ou verdade: a conta de luz zera com energia solar?' — responde que "
                   "não zera (taxas como a iluminação pública continuam) e que o que cai é a energia que a pessoa "
                   "pagava.", True, None),
}
CENARIOS.update({
    "rede": ("relaxing in a hammock on a wooden veranda by a river in Para, Brazil, a small house with solar panels on "
             "the roof right behind, warm afternoon sun"),
    "rio": ("standing on a small wooden riverboat on a wide calm river in the Amazon region of Para, Brazil, riverside "
            "houses with solar panels on their roofs in the background, bright daylight"),
    "cozinha": ("standing in a simple bright home kitchen in northern Brazil, an air conditioner on the wall and a "
                "fridge behind, a window showing solar panels on the neighbour's roof, natural light"),
    "acai": ("standing at a colourful street açaí stand in a town of Para, Brazil, holding a bowl of açaí, small shops "
             "with solar panels on their roofs behind, sunny day"),
    "futebol": ("standing on a dirt football field of a small town in Para, Brazil, holding a football under one arm, "
                "a clubhouse with solar panels on its roof behind, golden late-afternoon sun"),
    "praia": ("standing on a river beach with white sand in Para, Brazil, a beach kiosk with solar panels on its thatched "
              "roof behind, bright sun"),
    "feira": ("standing in a lively open-air street market in a town of Para, Brazil, fruit stalls around, market roofs "
              "with solar panels behind, bright daylight"),
})


CONTAS_SOLARES = ("advance_novoestrela", "globosolarenergiag", "msenergycap")


def escolher_estilo(conta=None):
    """Thompson no placar insta_estilos: estilo que rende sai mais; sem dado ainda é testado. Nunca o mesmo estilo 3x
    seguidas. 31/10 (dona: "usar o conhecimento de uma na outra"): a conta soma o que aprendeu com metade do peso do
    que as outras 2 empresas solares aprenderam (conta nova já começa sabendo o que rende nas outras)."""
    conta = conta or INSTAGRAM.lstrip("@")
    ult = [h.get("estilo") for h in _hist()[-2:]]
    cands = [e for e in ESTILOS if not (len(ult) == 2 and ult[0] == ult[1] == e)]
    try:
        if r"D:\postador-de-videos\bin" not in sys.path:
            sys.path.append(r"D:\postador-de-videos\bin")
        import placar_titulos
        soma = {}
        for c in set(CONTAS_SOLARES) | {conta}:
            peso = 1.0 if c == conta else 0.5
            for e, (t, v) in placar_titulos.taxas("insta_estilos", c).items():
                a = soma.setdefault(e, [0.0, 0.0])
                a[0] += t * peso
                a[1] += v * peso
        return max(cands, key=lambda e: random.betavariate(soma.get(e, (0, 0))[1] + 1,
                                                           soma.get(e, (0, 0))[0] - soma.get(e, (0, 0))[1] + 1))
    except Exception:  # noqa: BLE001
        return random.choice(cands)


LUGAR_PT = {"rede": "numa rede de varanda na beira do rio", "rio": "num barquinho no rio", "cozinha": "na cozinha de casa",
            "acai": "numa barraca de açaí", "futebol": "num campinho de futebol", "praia": "numa praia de rio",
            "feira": "numa feira de rua"}


def _pedir_llm(pauta, tipo, falas_usadas, correcao="", estilo=None, lugar=None):
    from llm_client import _call_gemini_native
    # pedido ACENTUADO: escrito sem acento, o LLM devolveu "A manutencao e dificil? E simples" (22/10) -> legenda e
    # pronuncia erradas
    formato = {"foto_real": "foto real de uma instalação feita pela empresa, com narração em off",
               "video_real": "vídeo REAL de instalações e manutenção feitas pela empresa, com narração em off"}.get(
        tipo, "um(a) consultor(a) da empresa falando direto para a câmera")
    system = ("Você escreve roteiros de Reels/TikTok de 8 segundos para uma empresa REAL de energia solar. O objetivo é "
              "gerar pedidos de orçamento (clientes) com confiança e clareza. Não é meme. Escreva sempre em português "
              "do Brasil com acentuação correta (ã, ç, é, ó...). Responda SÓ JSON válido.")
    usadas = "\n".join(f"- {f}" for f in falas_usadas[-30:]) or "- (nenhuma)"
    user = f"""Empresa: {EMPRESA}
Assunto deste vídeo (só a ideia; NÃO copie estas palavras): {pauta[2]}
Formato: {formato}

Regras obrigatórias:
- Português do Brasil falado, natural, educado e confiante, COM acentuação correta. Nada de gritos, caretas ou "choque".
- NÃO prometer conta zerada, "zerar", R$ 0 ou "de graça". NÃO usar números, porcentagens, preços, prazos ou anos.
- NÃO citar nome de distribuidora/concessionária. NÃO usar "segredo", "não querem que você saiba", "ninguém te conta".
- NÃO prometer "garantir" economia ou resultado.
- A primeira frase já toca numa dúvida ou dor real de quem pensa em instalar energia solar.
- "fala": de {_min_palavras(tipo)} a {_max_palavras(tipo)} palavras NO TOTAL (conte!), SEM convite no final (o convite é colocado depois).
  {"Estrutura: 1) a dúvida em uma frase curta; 2) a RESPOSTA clara, com dois fatos simples e verdadeiros que explicam; 3) uma conclusão que fecha o assunto. Exemplo só da ESTRUTURA (não copie): 'Painel solar funciona em dia nublado? Funciona sim. As placas aproveitam a luz que passa pelas nuvens e o projeto já considera os meses de chuva do Pará. No fim do ano, a geração compensa.'" if tipo == "video_real" else "Uma ou duas frases curtas. Se fizer pergunta, a própria fala RESPONDE logo em seguida. Exemplo só do TAMANHO: 'Funciona na chuva? Funciona, e gera o ano todo.'"}
- A fala NUNCA termina em pergunta: quem assiste precisa da resposta e da conclusão.
- "gancho_tela": de 2 a 5 palavras para aparecer escrito no topo do vídeo ({"termina com ?" if estilo and ESTILOS[estilo][1] else "SEM ponto de interrogação" if estilo else "pode ser pergunta"}).
- "legenda": 2 ou 3 linhas curtas para o Instagram, útil e honesta sobre a pauta. SEM convite no final e SEM
  hashtags (os dois são colocados depois). No máximo 2 emojis.
- "titulo": até 60 caracteres, descritivo.
{("ESTILO DESTE VÍDEO (obrigatório): " + ESTILOS[estilo][0]) if estilo else ""}{(" A pessoa está " + LUGAR_PT.get(lugar, lugar) + ": cite isso na fala.") if lugar else ""}
Falas já usadas (NÃO repita nem parafraseie de perto):
{usadas}
{correcao}
Responda SÓ: {{"fala": "...", "gancho_tela": "...", "legenda": "...", "titulo": "..."}}"""
    txt = _call_gemini_native(system, user, max_tokens=900, temperatura=0.8)
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0))


def _max_palavras(tipo):
    """Clipe do Veo tem 8 s (fala + convite cabem com 12 palavras). 25/10 (dono: "muito curtos, sem conclusão, fazem
    pergunta sem responder; por que curtos se podem ser bem maiores?"): o video_real não tem limite do Veo -> até 45
    palavras (~20-25 s), com pergunta, resposta e conclusão."""
    return 45 if tipo == "video_real" else 15  # 25/10: com a resposta na fala, 12 não cabia (LLM caía na reserva 3x)


def _min_palavras(tipo):
    return 25 if tipo == "video_real" else 6


def _validar(r, tipo=None):
    erros = []
    fala, gancho = (r.get("fala") or "").strip(), (r.get("gancho_tela") or "").strip()
    n = len(fala.split())
    if not _min_palavras(tipo) <= n <= _max_palavras(tipo) + 1:
        erros.append(f"a fala tem {n} palavras: precisa ter de {_min_palavras(tipo)} a {_max_palavras(tipo)}")
    if fala.rstrip().endswith("?"):  # 25/10: pergunta sem resposta deixa o video sem conclusao
        erros.append("a fala termina em pergunta: responda a pergunta na propria fala, com uma conclusao clara")
    if not 1 <= len(gancho.split()) <= 6:
        erros.append("gancho_tela precisa de 2 a 5 palavras")
    for campo in ("fala", "gancho_tela", "legenda", "titulo"):
        for p in problemas_texto(r.get(campo, "")):
            erros.append(f"{campo}: {p}")
    if not (r.get("legenda") or "").strip():
        erros.append("legenda vazia")
    for campo in ("fala", "gancho_tela", "legenda"):
        sem = sorted(set(re.findall(_SEM_ACENTO, (r.get(campo) or "").lower())))
        if sem:
            erros.append(f"{campo} sem acento ({', '.join(sem)}): escreva com acentuação correta")
    return erros


def _revisar(fala, assunto, tipo="video"):
    """Revisor: ao encurtar, o LLM ja escreveu "seu ar-condicionado gera muita energia" (teste 22/10). (ok, problema);
    se o revisor cair, aceita (nao trava a producao).
    10/11: os 3 carrosseis chamavam com o texto de TODOS os slides e o revisor lia "fala de um video de 8 segundos" ->
    reprovava por tamanho ("80 palavras pra 8 s"): MS e Advance sem carrossel das 18h. tipo="carrossel" = texto dos
    slides de um post de fotos (tamanho nao importa)."""
    from llm_client import _call_gemini_native
    system = "Voce revisa textos de propaganda de uma empresa de energia solar. Responda SO JSON valido."
    cabeca = ('Texto dos slides de um carrossel do Instagram (post de fotos, sem narracao; o TAMANHO do texto nao e '
              'problema): "' if tipo == "carrossel" else 'Fala de um video de 8 segundos: "')
    user = (f'{cabeca}{fala}"\nAssunto do post: {assunto}\n'
            "A fala esta CORRETA tecnicamente (energia solar, eletricidade, conta de luz), faz sentido, e portugues do "
            "Brasil natural e combina com o assunto? Reprove frase sem sentido (ex.: \"o ar-condicionado gera "
            'energia"), informacao errada, promessa exagerada ou erro de portugues. Responda: {"ok": true ou false, '
            '"problema": "..."}')
    try:
        txt = _call_gemini_native(system, user, max_tokens=200, temperatura=0.1)
        j = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
        return bool(j.get("ok")), str(j.get("problema") or "")
    except Exception:  # noqa: BLE001
        return True, ""


def _repetida(fala, falas_usadas):
    from difflib import SequenceMatcher
    a = " ".join(_norm(fala))
    return any(SequenceMatcher(None, a, " ".join(_norm(f))).ratio() > 0.75 for f in falas_usadas[-60:])


def prompt_foto(descricao_en, fala_final):
    # 22/10 (testes reais): com "slow push-in" e ate com "almost static" o Veo sobrevoou o telhado e inventou placas
    # (foto de drone vira filmagem de drone) -> tripe travado, camera parada
    return (f"Keep this exact shot from the first frame to the last: {descricao_en.strip().rstrip('.')}. "
            "Use the uploaded photo as BOTH the first frame and the last frame: the video starts and ends exactly on "
            "this image. "
            "Static locked-off tripod shot: the camera does not move at all, no zoom, no pan, no drone movement. Do "
            "not reveal new areas, do not add or remove solar panels. Only subtle natural motion: sunlight glinting on "
            "the solar panels, clouds drifting, "
            "leaves swaying. Same place, same framing, same lighting and colors as the photo for the whole video. One "
            "single continuous shot: no cuts, no transitions, no scene change, no new objects, no people appearing. "
            "Voice-over by a warm, friendly off-screen Brazilian male narrator. "
            f'The narrator says in Brazilian Portuguese: "{fala_final}" Only this line is spoken. Soft natural ambient '
            "sound, no music. No subtitles, no captions, no on-screen text, no logos, no watermarks. 9:16 vertical "
            "portrait.")


def prompt_apresentador(cenario, persona, fala_final):
    pessoa, pronome = persona
    # 22/10: "vertical smartphone framing" fez o Veo desenhar a barra de status do celular (bateria/Wi-Fi) no topo
    # 22/10: com a descricao colada antes dos dois-pontos ("speaks calmly ... in Brazilian Portuguese:") o Veo leu a
    # instrucao em voz alta ("Um homem fala com calma...") -> descricao numa frase, fala no formato simples 'diz: "..."'
    return (f"{pessoa}, {CENARIOS[cenario]}. Medium close-up, vertical 9:16 framing, shot on a professional cinema "
            f"camera, realistic documentary style, true-to-life colors, full-frame image with no interface elements. "
            f"{pronome} has a calm, confident and friendly manner and looks straight into the camera. "
            f'{pronome} says in Brazilian Portuguese: "{fala_final}" Only this line is spoken. Natural hand gestures. '
            "One single continuous shot: no cuts, no scene changes. Ambient outdoor sound, no music. No subtitles, no "
            "captions, no on-screen text, no logos, no watermarks. 9:16 vertical portrait.")


PEDIDO_CLONE = (
    "Photorealistic vertical 9:16 photo of THE SAME PERSON from the reference photos. ABSOLUTE PRIORITY: keep the face "
    "100% identical to the references - same face shape, eyes, nose, mouth, hair, skin tone (glasses only if the "
    "references have them). Do not beautify, age or change the face in any way. The person is a solar energy "
    "professional wearing a plain solid red polo shirt with no logo, no text and no print, {cenario}. Medium close-up "
    "from chest up, looking straight at the camera, friendly confident expression, natural daylight, realistic "
    "documentary photo. No text, no letters, no logos, no watermark, no other people.")


def _clone(cenario, fala_final, log=print):
    """25/10 (dono: "por que não está usando fotos base e criando novas para o tema como faz o Veo normal? todo cliente
    tem que ter uma subpasta na pasta do Drive pra colocar suas fotos base para seus clones"): com >= 3 fotos com rosto
    em empresas/<conta>/fotos_base (Drive), a foto do apresentador é criada NA HORA no cenário da pauta (Flow +
    revisor de rosto do D:\\veo\\beta\\foto_na_hora.py contra essas bases). (caminho_da_foto, pasta_das_bases) ou None
    (pasta vazia/Flow falhou = apresentador gerado pelo Veo, como antes). MS_CLONE=0 desliga."""
    import os
    if os.environ.get("MS_CLONE", "1") == "0":
        return None
    try:
        if r"D:\postador-de-videos\bin" not in sys.path:
            sys.path.append(r"D:\postador-de-videos\bin")
        import legenda_empresa
        import pastas_empresas
        import foto_na_hora
        conta_drive = legenda_empresa.carregar("msenergycap").get("pasta_drive") or "msenergysolar.pa"
        pasta, de_quem = pastas_empresas.clone_bases(conta_drive, log)
        n = foto_na_hora.bases_com_rosto(pasta) if pasta else 0
        if n < 3:
            # 25/10 17h (dono): "todos os produtos têm que usar EU como personagem nos vídeos do Veo 3", e isso vale
            # TAMBÉM para o MS Energy (mudou a regra de 22/10). Sem fotos-base da empresa = o DONO apresenta.
            log(f"  [CLONE] empresas/{conta_drive}/fotos_base com {n} foto(s) com rosto: apresentador = o dono")
            pasta = None
        foto_na_hora.usar_bases(pasta)
        if pasta is None:
            pasta = foto_na_hora.BASES_DIR
        f = None
        for rodada in range(3):  # 25/10 19h: contas do Flow ocupadas pelo Veo -> teste do clone saiu sem foto em segundos
            f = foto_na_hora.gerar(CENARIOS[cenario], fala_final, tag="msenergy_clone",
                                   pedido=PEDIDO_CLONE.format(cenario=CENARIOS[cenario]))
            if f or rodada == 2:
                break
            aprovadas = [rg.get("arquivo") for rg in foto_na_hora._registros()
                         if rg.get("aprovada") and rg.get("tag") == "msenergy_clone" and rg.get("arquivo")
                         and Path(rg["arquivo"]).exists() and rg.get("cenario") == CENARIOS[cenario]]
            if aprovadas:  # foto dele JÁ aprovada (rosto conferido) neste mesmo cenário
                f = aprovadas[-1]
                log(f"  [CLONE] Flow sem conta livre — uso a foto já aprovada {Path(f).name}")
                break
            log("  [CLONE] Flow sem conta livre agora — espero 4 min e tento de novo")
            import time
            time.sleep(240)
        if f:
            log(f"  [CLONE] foto do apresentador da empresa no cenário '{cenario}': {Path(f).name}")
            return f, str(pasta)
        log("  [CLONE] nenhuma foto passou no revisor de rosto: apresentador gerado")
    except Exception as e:  # noqa: BLE001
        log(f"  [CLONE] falhou ({type(e).__name__}: {str(e)[:120]}): apresentador gerado")
    return None


def prompt_clone(fala_final):
    """Image-to-video a partir da foto do clone: mesma pessoa, roupa e lugar do 1o quadro (fala no formato simples
    'says: "..."': com a descrição antes dos dois-pontos o Veo já leu a instrução em voz alta, 22/10)."""
    return ("Keep the exact person, face, clothes and place from the first frame for the whole video. Medium close-up, "
            "shot on a professional cinema camera, realistic documentary style, true-to-life colors, the camera stays "
            "still. The person looks straight into the camera with a calm, confident and friendly manner. "
            f'The person says in Brazilian Portuguese: "{fala_final}" Only this line is spoken. Natural hand gestures. '
            "One single continuous shot: no cuts, no scene changes, the face never changes. Ambient outdoor sound, no "
            "music. No subtitles, no captions, no on-screen text, no logos, no watermarks. 9:16 vertical portrait.")


def legendas_finais(legenda, pauta_id):
    # 25/10: legenda nova (postador bin\legenda_empresa.py): 1a linha com "energia solar" + Pará, pergunta, "Comente
    # SOL" (o vigia responde no Direct), local e 5 hashtags. Antes: frase morna + rodapé fixo, 0 comentário em 10 posts.
    try:
        if r"D:\postador-de-videos\bin" not in sys.path:
            sys.path.append(r"D:\postador-de-videos\bin")  # no FIM do sys.path (memoria 23/10)
        import legenda_empresa
        insta, tiktok, tags = legenda_empresa.montar("msenergycap", legenda, pauta_id)
        if insta and "Comente" in insta:
            return insta, tiktok, tags
    except Exception as e:  # noqa: BLE001  (legenda nunca derruba a geracao: cai no formato antigo)
        print(f"  [ROTEIRO] legenda nova falhou ({type(e).__name__}: {e}) - formato antigo")
    tags = HASHTAGS_BASE + HASHTAGS_PAUTA.get(pauta_id, [])
    insta = (f"{legenda.strip()}\n\n"
             f"📲 Orçamento grátis pelo WhatsApp: link no perfil {INSTAGRAM}\n"
             "🏠 Casas • 🏪 Comércios • 🌾 Propriedades rurais — Pará\n\n" + " ".join(tags))
    primeira = legenda.strip().split("\n")[0]
    tiktok = (f"{primeira}\n📲 Orçamento grátis: chame a MS Energy no WhatsApp (perfil do Instagram {INSTAGRAM}) "
              + " ".join(tags[:5]))
    return insta, tiktok, tags


def gerar(tipo, foto=None, log=print):
    """Roteiro completo. foto = (nome, item_do_indice) para foto_real. Nunca levanta: sem LLM usa a reserva."""
    falas_usadas = [h.get("fala", "") for h in _hist()]
    # video_real: os clipes sao telhados da cidade — pauta do campo nao combina com a imagem
    pauta = escolher_pauta(evitar=("rural",) if tipo == "video_real" else ())
    estilo = escolher_estilo() if tipo not in ("foto_real", "video_real") else None
    lugares = random.sample(ESTILOS[estilo][2], 3) if estilo and ESTILOS[estilo][2] else None
    r, correcao = None, ""
    for tentativa in range(3):
        try:
            cand = _pedir_llm(pauta, tipo, falas_usadas, correcao, estilo, lugares[0] if lugares else None)
        except Exception as e:  # noqa: BLE001
            log(f"  [ROTEIRO] LLM falhou ({type(e).__name__}: {str(e)[:80]})")
            continue
        erros = _validar(cand, tipo)
        g = (cand.get("gancho_tela") or "").strip()
        if estilo and not ESTILOS[estilo][1] and g.endswith("?"):
            erros.append("gancho_tela deste estilo NÃO é pergunta (tire o ponto de interrogação)")
        if not erros and _repetida(cand["fala"], falas_usadas):
            erros = ["a fala ficou parecida demais com uma ja usada"]
        if not erros:
            ok_rev, problema = _revisar(cand["fala"], pauta[2])
            if not ok_rev:
                erros = [f"revisor: {problema[:120]}"]
        if not erros:
            r = cand
            break
        log(f"  [ROTEIRO] tentativa {tentativa + 1} reprovada: {'; '.join(erros)[:160]} | fala: {cand.get('fala')}")
        correcao = (f"CORRIJA a resposta anterior (fala: \"{cand.get('fala')}\"): " + "; ".join(erros)
                    + f". Se for tamanho, reescreva a MESMA ideia com no máximo {_max_palavras(tipo)} palavras, com "
                    "acentuação correta.")
    fonte = "llm"
    if r is None:
        fala, gancho = RESERVA[pauta[0]]
        r = {"fala": fala, "gancho_tela": gancho, "titulo": gancho,
             "legenda": f"{gancho}\n{fala}"}
        fonte = "reserva"
    fala = r["fala"].strip()
    if not fala.endswith((".", "!", "?")):
        fala += "."
    fala_final = f"{fala} {CTA_FALADO}"
    out = {"tipo": tipo, "pauta": pauta[0], "assunto": pauta[2], "fala": fala, "fala_final": fala_final,
           "gancho_tela": r["gancho_tela"].strip(), "titulo": r.get("titulo", "").strip()[:80], "fonte": fonte}
    quadro = None
    if tipo == "foto_real" and foto:
        quadro = quadro_916(foto[0], float((foto[1].get("visao") or {}).get("foco_x") or 0.5))
    if quadro:
        nome, item = foto
        v = item.get("visao") or {}
        out["foto"] = nome
        out["foto_permalink"] = item.get("permalink")
        out["quadro"] = str(quadro)
        out["prompt_veo"] = prompt_foto(v.get("descricao_en") or "a house with solar panels on the roof", fala_final)
    elif tipo == "video_real":  # sem Veo: clipes reais + narradora (video_real_ms.py)
        out["prompt_veo"] = None
    else:
        cenario = pauta[1]
        if lugares:  # criativo: lugar inusitado (1º, citado na fala) e os outros para as outras cenas
            cenario, out["cenarios_extra"] = lugares[0], lugares[1:]
        if estilo:
            out["estilo"] = estilo
        persona = PERSONAS[len(_hist()) % len(PERSONAS)]
        out["tipo"] = "apresentador"
        out["cenario"] = cenario
        out["persona"] = persona[1]
        out["prompt_veo"] = prompt_apresentador(cenario, persona, fala_final)
        clone = _clone(cenario, fala_final, log)
        if clone:  # 25/10: rosto da empresa (fotos_base no Drive) em vez de uma pessoa inventada a cada vídeo
            out["quadro"], out["clone_bases"] = clone
            out["persona"] = "clone"
            out["prompt_veo"] = prompt_clone(fala_final)
    out["legenda_insta"], out["legenda_tiktok"], out["hashtags"] = legendas_finais(r["legenda"], pauta[0])
    if "Comente" in out["legenda_insta"]:
        out["legenda_versao"] = 2  # legenda_empresa.relegendar nao refaz
    log(f"  [ROTEIRO] {out['tipo']} | pauta={out['pauta']} | fonte={fonte} | fala: {fala_final}")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tipo = sys.argv[1] if len(sys.argv) > 1 else "apresentador"
    f = escolher_foto() if tipo == "foto_real" else None
    print(json.dumps(gerar(tipo, f), ensure_ascii=False, indent=1))
