"""Agentes do conteúdo PROFISSIONAL de produto (dono 25/10: "os agentes têm que ser diferentes" dos de entretenimento).

- estrategista: banco de pautas do produto (dor real, objeção, como funciona, caso de uso, pergunta frequente,
  antes/depois), guardado em config\\produto_pautas\\<conta>.json e renovado quando as pautas acabam.
- roteirista + diretor de arte: gancho fixo no topo, pergunta de cliente (cartão de abertura), 3 blocos com rótulo
  numerado, fala da narradora e o visual de cada bloco (imagem do Flow, conversa de WhatsApp animada ou cena do Veo).
- revisor de conformidade: regra fixa (número, preço, garantia, concorrente, absolutos, acento) + revisor por LLM que
  compara cada frase com os FATOS do produto (os modelos inventam "sem taxas" sozinhos — teste de 25/10).

Tom: consultor experiente falando com o dono do negócio. Calmo, claro, concreto. Não é meme, não é "choque".
"""
import json
import random
import re
import unicodedata
import urllib.request
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PAUTAS_DIR = RAIZ / "config" / "produto_pautas"
HIST = RAIZ / "config" / "produto_historico.json"
GATEWAY = Path(r"D:\veo\beta\secrets\gateway.json")
# 25/10: tiered respondeu em 3,5 s com texto bom; gemini-3-flash é a reserva rápida; por fim o llm_client do Veo
MODELOS = ("antigravity/gemini-3.8-flash-tiered", "antigravity/gemini-3-flash", "gemini/gemini-3.5-flash")

TIPOS_PAUTA = ("dor", "objecao", "como_funciona", "caso_de_uso", "pergunta_frequente", "antes_depois")


# ───────────────────────────── LLM ─────────────────────────────

def llm(system, user, max_tokens=1800, temperatura=0.7):
    erros = []
    gw = json.loads(GATEWAY.read_text("utf-8"))
    for modelo in MODELOS:
        try:
            corpo = {"model": modelo, "max_tokens": max_tokens, "temperature": temperatura,
                     "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            req = urllib.request.Request(gw["gateway_url"].rstrip("/") + "/v1/chat/completions",
                                         data=json.dumps(corpo).encode(),
                                         headers={"Authorization": "Bearer " + gw["gateway_key"],
                                                  "Content-Type": "application/json"})
            txt = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]["content"]
            if txt and txt.strip():
                return txt
        except Exception as e:  # noqa: BLE001
            erros.append(f"{modelo}: {type(e).__name__} {str(e)[:80]}")
    import sys
    sys.path.insert(0, r"D:\veo\beta")
    try:
        from llm_client import _call_gemini_native
        return _call_gemini_native(system, user, max_tokens=max_tokens, temperatura=temperatura)
    except Exception as e:  # noqa: BLE001
        erros.append(f"llm_client: {type(e).__name__} {str(e)[:80]}")
    raise RuntimeError("nenhum modelo respondeu: " + " | ".join(erros))


def _json(txt):
    m = re.search(r"[\[{].*[\]}]", txt or "", re.S)
    if not m:
        raise ValueError("resposta sem JSON")
    return json.loads(m.group(0))


# ───────────────────────────── regras ─────────────────────────────

_PROIBIDO = [
    (r"\d", "tem número (proibido: nada de número, preço, prazo ou porcentagem)"),
    (r"garant(?!ia\s+de\s+f[aá]brica)", "promete garantia de resultado"),
    (r"\bzer(a|ar|ou|ada|ado|ando)\b|de\s+gra[çc]a|\bgr[aá]tis\b|\bgratuit", "fala em zerar/grátis (não é fato do produto)"),
    (r"sem\s+taxa|taxa\s+zero|sem\s+mensalidade|sem\s+custo|mais\s+barat|economi[zc]", "fala de preço/economia que não é fato do produto"),
    (r"segredo|ningu[eé]m\s+(te\s+)?cont|n[aã]o\s+querem\s+que|escond", "tom de clickbait/conspiração"),
    # 25/10: "Perfeito!" numa conversa é só interjeição (reprovou 2 roteiros bons) -> fora da lista
    (r"nunca\s+mais|100\s*%|para\s+sempre|infal[ií]vel|milagr|sem\s+erro|todos\s+os\s+seus\s+clientes",
     "promessa absoluta"),
    (r"\b(ifood|rappi|aiqfome|uber\s*eats|anota\s*a[ií]|goomer|calendly|doctoralia|zenvia|take\s*blip|chatgpt|openai)\b",
     "cita concorrente/plataforma de terceiros"),
    (r"https?://|www\.|\.com|@\w|whats\s*app\s*\(|\(\s*\d", "contato/site/arroba na fala (regra: só 'link no perfil')"),
    (r"\b(cemig|equatorial|celpa|enel|light|copel|cpfl|energisa|coelba|neoenergia|celesc|cosern)\b",
     "cita concessionária (regra do MS Energy)"),
]

# palavras que SÓ existem com acento (sem ele = texto sem acentuação: legenda feia e narradora pronuncia errado)
_SEM_ACENTO = (r"\b(nao|voce|voces|tambem|ate|ja|so|entao|sao|estao|horario|horarios|cardapio|cardapios|automatico|"
               r"automatica|rapido|rapida|facil|dificil|negocio|negocios|ligacao|ligacoes|clinica|clinicas|salao|"
               r"servico|servicos|conteudo|duvida|duvidas|proprio|propria|informacao|informacoes|unico|unica|"
               r"ultimo|ultima|agil|possivel|necessario|historico|numero|numeros|area|varios|varias|tambem|ninguem|"
               r"alguem|voce|preco|precos|pagina|maquina|atencao|solucao|situacao|organizacao|confirmacao|"
               r"marcacao)\b")


_HORARIO = re.compile(r"\b\d{1,2}\s*h\s*(\d{2})?\b|\b\d{1,2}:\d{2}\b|\b\d{1,2}/\d{1,2}\b", re.I)


def _horas_dos_fatos(kit):
    """Números de HORAS que são fato do produto ("24h" no Hermes Call/Agenda IA): podem ser ditos. Preço não
    ("a partir de 199" está nos fatos da Agenda IA, mas preço muda e não vai para o vídeo)."""
    return {m for f in (kit or {}).get("fatos", []) for m in re.findall(r"(\d+)\s*(?:h\b|horas)", f.lower())}


def problemas(texto, kit=None):
    t = (texto or "").lower()
    for n in _horas_dos_fatos(kit):  # 25/10: "24 horas" é fato do Hermes Call e foi barrado como número
        t = re.sub(rf"\b{n}\s*(h\b|horas)", "horas", t)
    for frase in (kit or {}).get("permitido", []):  # fato do cliente (MS Energy: "orçamento grátis")
        t = t.replace(frase, "orçamento")
    erros = []
    for padrao, motivo in _PROIBIDO:
        m = re.search(padrao, t)
        if m:
            trecho = t[max(m.start() - 15, 0):m.end() + 15].strip()
            erros.append(f"{motivo} (trecho: \"{trecho}\")")
    sem = sorted(set(re.findall(_SEM_ACENTO, t)))
    if sem:
        erros.append(f"sem acento ({', '.join(sem)}): escreva com acentuação correta")
    return erros


def _norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def _hist():
    try:
        return json.loads(HIST.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return []


def registrar(conta, roteiro, arquivo, formato):
    h = _hist()
    h.append({"conta": conta, "data": datetime.now().isoformat(timespec="seconds"), "pauta": roteiro.get("pauta_id"),
              "gancho": roteiro.get("gancho_tela"), "falas": [b["fala"] for b in roteiro.get("blocos", [])],
              "arquivo": str(arquivo), "formato": formato})
    HIST.write_text(json.dumps(h[-1000:], ensure_ascii=False, indent=1), "utf-8")


# ───────────────────────────── estrategista ─────────────────────────────

_SYS_ESTRATEGISTA = (
    "Você é estrategista de conteúdo de uma empresa brasileira de software para pequenos negócios. Cria pautas de "
    "Reels e carrosséis que geram CLIENTES (pedidos de demonstração), não entretenimento. Cada pauta parte de uma "
    "situação real e específica do dia a dia do público. Português do Brasil com acentuação correta. Responda SÓ JSON.")


def _pedir_pautas(kit, ja, n=20):
    fatos = "\n".join(f"- {f}" for f in kit["fatos"]) or "- (sem fatos cadastrados)"
    user = f"""Produto: {kit['nome_produto']} (Instagram {kit['arroba']})
Público: {kit['publico']}
FATOS do produto (a ÚNICA fonte do que o produto faz; não invente recurso, preço, prazo nem número):
{fatos}

Crie {n} pautas diferentes entre si, misturando estes tipos: {', '.join(TIPOS_PAUTA)}.
Cada pauta: "id" (curto, sem espaço), "tipo", "ideia" (1 frase: a situação real + como o produto ajuda, dentro dos
FATOS), "pergunta_cliente" (uma pergunta curta e realista que o dono do negócio faria, sem número).
Evite pautas parecidas com estas já usadas: {ja[-30:]}
Responda SÓ: {{"pautas": [{{"id": "...", "tipo": "...", "ideia": "...", "pergunta_cliente": "..."}}]}}"""
    return _json(llm(_SYS_ESTRATEGISTA, user, max_tokens=3000, temperatura=0.9)).get("pautas") or []


def pautas(kit, log=print):
    """Banco de pautas da conta (cria/renova quando faltam pautas frias)."""
    PAUTAS_DIR.mkdir(parents=True, exist_ok=True)
    arq = PAUTAS_DIR / f"{kit['conta']}.json"
    banco = json.loads(arq.read_text("utf-8")) if arq.exists() else {"pautas": []}
    usadas = {h.get("pauta") for h in _hist() if h.get("conta") == kit["conta"]}
    frias = [p for p in banco["pautas"] if p["id"] not in usadas]
    if len(frias) < 4:
        try:
            novas = _pedir_pautas(kit, [p["ideia"] for p in banco["pautas"]])
        except Exception as e:  # noqa: BLE001
            log(f"  [estrategista] falhou ({e}); sigo com o banco atual")
            novas = []
        ids = {p["id"] for p in banco["pautas"]}
        boas = 0
        for p in novas:
            if not isinstance(p, dict) or not p.get("ideia"):
                continue
            graves = [e for e in problemas(p["ideia"] + " " + (p.get("pergunta_cliente") or ""))
                      if "acento" not in e]
            if graves:  # pauta que já nasce com número/preço/concorrente contamina o roteiro
                continue
            pid = re.sub(r"\W+", "_", _norm(p.get("id") or p["ideia"])[:30]).strip("_") or f"p{len(ids)}"
            while pid in ids:
                pid += "_b"
            ids.add(pid)
            banco["pautas"].append({"id": pid, "tipo": p.get("tipo", "dor"), "ideia": p["ideia"].strip(),
                                    "pergunta_cliente": (p.get("pergunta_cliente") or "").strip(),
                                    "criada": datetime.now().isoformat(timespec="seconds")})
            boas += 1
        arq.write_text(json.dumps(banco, ensure_ascii=False, indent=1), "utf-8")
        log(f"  [estrategista] {boas} pautas novas para {kit['conta']} (banco: {len(banco['pautas'])})")
    return banco["pautas"]


def escolher_pauta(kit, log=print):
    """A pauta usada há mais tempo (sorteio entre as 5 mais frias), variando o tipo em relação à última."""
    todas = pautas(kit, log)
    ordem = {}
    ultimo_tipo = None
    for i, h in enumerate(_hist()):
        if h.get("conta") == kit["conta"]:
            ordem[h.get("pauta")] = i
            ultimo_tipo = next((p["tipo"] for p in todas if p["id"] == h.get("pauta")), ultimo_tipo)
    cand = sorted(todas, key=lambda p: (ordem.get(p["id"], -1), p["tipo"] == ultimo_tipo))[:5]
    return random.choice(cand)


# ───────────────────────────── roteirista + diretor de arte ─────────────────────────────

_SYS_ROTEIRISTA = (
    "Você é roteirista e diretor de arte de vídeos COMERCIAIS curtos (Reels de 20 a 30 segundos) para uma empresa "
    "brasileira de software. Estilo: comercial profissional e confiável, como um consultor experiente falando com o "
    "dono do negócio. Calmo, claro, concreto, frases curtas. NÃO é meme: sem gritos, sem gíria forçada, sem 'choque', "
    "sem exagero. Português do Brasil com acentuação correta. Responda SÓ JSON válido.")


REGRAS_APRENDIDAS = Path(__file__).resolve().parents[2] / "config" / "produto_regras_roteiro.md"


def _regras_aprendidas():
    """Regras que o MELHORADOR (produto\\melhorador.py) escreveu a partir das notas do júri e da opinião do dono."""
    try:
        t = REGRAS_APRENDIDAS.read_text("utf-8").strip()
    except OSError:
        return ""
    return f"REGRAS APRENDIDAS NOS VÍDEOS ANTERIORES (siga):\n{t[:2500]}" if t else ""


def _pedir_roteiro(kit, pauta, falas_usadas, correcao, com_veo, cenas=(1,), broll=()):
    fatos = "\n".join(f"- {f}" for f in kit["fatos"]) or "- (sem fatos)"
    visuais = '"imagem" (foto ilustrativa gerada) ou "conversa" (conversa de WhatsApp animada mostrando o produto)'
    if broll:  # 26/10 (dono: "formatos diferentes, com 2 Veo3, 3 Veo3..."): cena comercial do Veo sem o dono
        visuais += (f' ou "veo" (cena comercial filmada pelo Veo, SEM fala, mostrando o negócio do público; '
                    f'OBRIGATÓRIO no(s) bloco(s) {list(broll)}; use "prompt_en")')
    if kit.get("cliente"):  # 25/10 22h (dono): cliente real (MS Energy) = instalações REAIS + narradora
        visuais = ('"real" (vídeo/foto REAL de instalação feita pela empresa; diga em "real_tema" qual: '
                   'placas_no_telhado | usina_no_solo | equipe_instalando | estrutura | inversor | drone). '
                   'Todo bloco que não for o dono é "real" (NÃO use conversa nem imagem)')
    if com_veo:
        # 25/10 (dono): "todos os produtos têm que usar EU como personagem nos vídeos do Veo 3" (avatar das fotos dele)
        # 25/10 18:40 (dono: "ficou ótimo, podemos encaixar mais Veos ao longo do vídeo"): ele abre e/ou fecha,
        # conforme a variação escolhida pelo agente de variações (variacoes.py)
        onde = " E ".join({1: "no bloco 1 (abre: a dor do cliente)", 2: "no bloco 2 (explica como funciona)",
                           3: "no bloco 3 (fecha: o resultado para o negócio)"}[n] for n in cenas)
        visuais += (f' ou "apresentador" (O DONO da empresa — um homem de óculos — filmado falando para a câmera; '
                    f'OBRIGATÓRIO {onde}; nos outros blocos NÃO use apresentador. A fala dele tem de 10 a 18 '
                    'palavras, na primeira pessoa; e "cenario_en": onde ele está, em inglês, ligado ao público, ex.: '
                    + ('"standing on a sunny rooftop next to newly installed solar panels in Pará, Brazil")'
                       if kit.get("cliente") else  # 27/10: o exemplo do restaurante pôs o dono numa padaria no MS
                       '"standing at the counter of a small Brazilian restaurant")'))
    user = f"""Produto: {kit['nome_produto']} — Instagram {kit['arroba']}
Público: {kit['publico']}
FATOS do produto (tudo que o vídeo afirmar sobre o produto tem que estar aqui; não invente recurso, preço, prazo,
número, integração, "sem taxa", "grátis" (só se estiver nos FATOS) nem resultado; não cite concessionária):
{fatos}
Pauta: [{pauta['tipo']}] {pauta['ideia']}
Pergunta de cliente sugerida: {pauta.get('pergunta_cliente')}

Monte o vídeo:
- "gancho_tela": 2 a 6 palavras que ficam fixas no topo do vídeo inteiro (o assunto, pode ser pergunta).
- "pergunta_cliente": a pergunta real que abre o vídeo num cartão, até 12 palavras, sem número. É o GANCHO dos 2
  primeiros segundos: fale da DOR ou do desejo do dono do negócio ("Cliente some depois do orçamento?", "Perdendo
  pedido no WhatsApp?"), nunca uma pergunta técnica de "como configuro" (26/10: o diretor reprovou esse gancho).
- "blocos": EXATAMENTE 3, nesta ordem lógica: o problema/situação → como o {kit['nome_produto']} resolve → o resultado
  para o negócio. Cada bloco:
    "rotulo": 1 a 3 palavras para o tópico numerado (ex.: "O problema", "Como funciona", "O resultado"),
    "fala": o que a narradora diz, de 9 a 22 palavras, uma ideia só, frases curtas e naturais,
    "visual": {visuais},
    "prompt_en": se visual = imagem ou veo: a cena em INGLÊS, fotografia comercial realista de pequeno negócio
       brasileiro ligado ao público, luz bonita, sem texto/letras/logos/telas legíveis, pessoas de costas ou de lado
       (sem close de rosto), ex.: "a busy small Brazilian restaurant counter at night, warm light, cinematic",
    "destaques": em TODO bloco que não for conversa (o dono/Veo que falhar vira foto e usa eles): 2 trechos CURTOS
       (2 a 4 palavras cada) copiados da PRÓPRIA fala, na ordem em que são ditos, com o benefício/ação mais forte
       (ex.: fala "ele responde sozinho e marca o horário" -> ["responde sozinho", "marca o horário"]); aparecem na
       tela na hora em que a fala é dita,
    "conversa": se visual = conversa — E TAMBÉM no bloco 2 quando ele for veo (reserva: se o Veo falhar, a tela mostra
       a conversa) —: 3 a 6 mensagens [{{"de": "cliente" ou "empresa", "texto": "..."}}], curtas, mostrando o produto
       funcionando de um jeito plausível pelos FATOS (sem preço, sem telefone, sem link escrito).
  {'Os blocos sem o dono são "real" (instalação de verdade), com "real_tema".' if kit.get("cliente") else ('Nos blocos livres (sem dono e sem veo), use pelo menos um "conversa"; se o bloco 2 (como funciona) estiver livre, ELE é a "conversa" (o produto funcionando).' if _livres(cenas if com_veo else (), broll) else 'Todos os blocos já têm visual definido acima.')}
- "legenda": 2 ou 3 linhas para o Instagram, útil e honesta, sem hashtags, no máximo 2 emojis, SEM @, site, telefone
  ou "direct do @..." (para chamar, só "link no perfil").
- "titulo": até 60 caracteres.
Falas já usadas nesta conta (não repita nem parafraseie): {falas_usadas[-25:]}
{_regras_aprendidas()}
{correcao}
Responda SÓ: {{"gancho_tela": "...", "pergunta_cliente": "...", "blocos": [{{"rotulo": "...", "fala": "...", "visual": "...", "prompt_en": "...", "cenario_en": "...", "real_tema": "...", "destaques": [], "conversa": []}}], "legenda": "...", "titulo": "..."}}"""
    global _argon_falhou
    if MODELO_ROTEIRO and not _argon_falhou:
        try:
            r = _json(llm_roteiro(_SYS_ROTEIRISTA, user, max_tokens=2200))
            r["modelo_roteiro"] = MODELO_ROTEIRO
            return r
        except Exception:  # noqa: BLE001 - 27/10: 1 timeout do Argon = 10 min; não repete nas 4 tentativas
            _argon_falhou = True
    r = _json(llm(_SYS_ROTEIRISTA, user, max_tokens=2200, temperatura=0.75))
    r["modelo_roteiro"] = MODELOS[0] + (" (Argon falhou)" if MODELO_ROTEIRO else "")
    return r


# 27/10 (dono: "mude o Gemini 3.8 pelo Argon e meça a diferença"): só quem ESCREVE o roteiro vira Argon; o revisor de
# fatos e o júri seguem no Gemini 3.8 para a régua ser a mesma. O Argon só existe no proxy :20133 e só pelo /v1/messages.
MODELO_ROTEIRO = "gemini-4-argon"
_argon_falhou = False
LAPIDAR_CFG = RAIZ / "config" / "produto_lapidar.json"


def llm_roteiro(system, user, max_tokens=2200):
    c = json.loads(LAPIDAR_CFG.read_text("utf-8"))
    corpo = {"model": MODELO_ROTEIRO, "max_tokens": max(max_tokens, 4000), "system": system,
             "messages": [{"role": "user", "content": user}]}
    req = urllib.request.Request(c["gateway"].rstrip("/") + "/v1/messages", data=json.dumps(corpo).encode(),
                                 headers={"x-api-key": c["chave"], "Authorization": "Bearer " + c["chave"],
                                          "content-type": "application/json", "anthropic-version": "2023-06-01"})
    d = json.loads(urllib.request.urlopen(req, timeout=c.get("argon_prazo_roteiro_s", 180)).read())
    txt = "".join(b.get("text", "") for b in d.get("content", []))
    if not txt.strip():
        raise RuntimeError("Argon sem texto")
    return txt


def _livres(cenas, broll):
    """Blocos (1..3) que não são do dono nem cena do Veo."""
    return [n for n in (1, 2, 3) if n not in set(cenas) | set(broll)]


def _validar(r, com_veo, kit=None, cenas=(1,), broll=()):
    erros = []
    blocos = r.get("blocos") or []
    if len(blocos) != 3:
        return ["precisa de exatamente 3 blocos"]
    if not 1 <= len((r.get("gancho_tela") or "").split()) <= 7:
        erros.append("gancho_tela com 2 a 6 palavras")
    if not 3 <= len((r.get("pergunta_cliente") or "").split()) <= 14:
        erros.append("pergunta_cliente com até 12 palavras")
    tipos = [b.get("visual") for b in blocos]
    cliente = bool((kit or {}).get("cliente"))
    if cliente:  # MS Energy: blocos sem o dono = instalação real
        for i, b in enumerate(blocos, 1):
            if b.get("visual") not in ("real", "apresentador"):
                erros.append(f"bloco {i}: visual tem de ser 'real' (instalação da empresa) ou 'apresentador'")
            if b.get("visual") == "real" and b.get("real_tema") not in (
                    "placas_no_telhado", "usina_no_solo", "equipe_instalando", "estrutura", "inversor", "drone"):
                erros.append(f"bloco {i}: real_tema inválido")
    elif 2 in _livres(cenas if com_veo else (), broll) and tipos[1] != "conversa":
        # 28/10 (diretor Disparo/Follow-up: "explica o produto e a tela mostra foto de banco/sala vazia"): o bloco
        # "como funciona" livre MOSTRA o produto funcionando
        erros.append("o bloco 2 (como funciona) tem de ter visual 'conversa' (o produto funcionando na tela)")
    elif "conversa" not in tipos and _livres(cenas if com_veo else (), broll):
        erros.append("falta um bloco com visual 'conversa'")
    for n in broll:
        if blocos[n - 1].get("visual") != "veo":
            erros.append(f"o bloco {n} tem de ter visual 'veo' (cena comercial do Veo, com prompt_en)")
    if not cliente and "imagem" not in tipos and "veo" not in tipos and "apresentador" not in tipos:
        erros.append("falta um bloco com visual 'imagem'")
    if com_veo:  # 25/10: o dono abre e/ou fecha (cenas da variação) — avatar dele no Veo
        for n in [c - 1 for c in cenas]:
            b = blocos[n]
            if b.get("visual") != "apresentador":
                erros.append(f"o bloco {n + 1} tem de ter visual 'apresentador' (o dono falando para a câmera)")
            elif not 8 <= len((b.get("fala") or "").split()) <= 19:
                erros.append(f"bloco {n + 1} (apresentador): fala de 10 a 18 palavras (cabe em 8 s de vídeo)")
            if len((b.get("cenario_en") or "").split()) < 4:
                erros.append(f"bloco {n + 1}: falta 'cenario_en' (onde o dono está, em inglês)")
    if (tipos.count("apresentador") > (len(cenas) if com_veo else 0)) or tipos.count("veo") > len(broll):
        erros.append(f"'apresentador' só nos blocos {cenas}" if com_veo else "não use 'apresentador' neste vídeo")
    tipos = ["imagem" if t == "apresentador" else t for t in tipos]  # para a regra de "pelo menos uma imagem"
    for i, b in enumerate(blocos, 1):
        n = len((b.get("fala") or "").split())
        if not 7 <= n <= 24:
            erros.append(f"bloco {i}: a fala tem {n} palavras (use de 9 a 22)")
        if b.get("visual") in ("imagem", "veo") and len((b.get("prompt_en") or "").split()) < 6:
            erros.append(f"bloco {i}: prompt_en curto demais")
        if b.get("visual") == "conversa" or b.get("conversa"):  # 28/10: a conversa de reserva do Veo também
            conv = b.get("conversa") or []
            if not 3 <= len(conv) <= 7 or not all(isinstance(c, dict) and c.get("texto") for c in conv):
                erros.append(f"bloco {i}: conversa precisa de 3 a 6 mensagens")
            for c in conv:
                # 25/10: horário de exemplo ("15h", "15h30", "9:00") é natural numa demonstração de agendamento
                # (não é promessa); preço/porcentagem/prazo continuam proibidos
                texto = _HORARIO.sub(" horário ", c.get("texto", ""))
                for p in problemas(texto, kit):
                    erros.append(f"bloco {i} conversa: {p}")
                # 28/10 (júri Hermes Call: "Alò"): acento grave só existe no "à"
                if re.search(r"[èìòùÈÌÒÙ]", c.get("texto", "")):
                    erros.append(f"bloco {i} conversa: acento errado em \"{c.get('texto', '')[:40]}\" (use ô/ó, é/ê...)")
        if not 1 <= len((b.get("rotulo") or "").split()) <= 4:
            erros.append(f"bloco {i}: rótulo de 1 a 3 palavras")
    for campo in ("gancho_tela", "pergunta_cliente", "legenda", "titulo"):
        for p in problemas(r.get(campo, ""), kit):
            erros.append(f"{campo}: {p}")
    for i, b in enumerate(blocos, 1):
        for p in problemas(b.get("fala", ""), kit):
            erros.append(f"bloco {i} fala: {p}")
    return erros


def revisor(kit, r):
    """Revisor de conformidade por LLM: cada afirmação sobre o produto precisa estar nos FATOS. (ok, problema).
    Se o revisor cair, reprova (vídeo de cliente: melhor não postar do que postar mentira)."""
    fatos = "\n".join(f"- {f}" for f in kit["fatos"])
    texto = "\n".join([f"Topo: {r.get('gancho_tela')}", f"Pergunta: {r.get('pergunta_cliente')}"] +
                      [f"Fala {i}: {b['fala']}" + (f" | Conversa: {json.dumps(b.get('conversa'), ensure_ascii=False)}"
                                                    if b.get("conversa") else "")
                       for i, b in enumerate(r["blocos"], 1)] + [f"Legenda: {r.get('legenda')}"])
    user = (f"Produto: {kit['nome_produto']}\nFATOS confirmados do produto:\n{fatos}\n\nTexto de um anúncio:\n{texto}\n\n"
            "Reprove se: alguma frase afirma recurso, preço, prazo, número, integração, economia ou resultado que NÃO "
            "está nos FATOS; promete o que não dá para garantir; tem erro de português ou frase sem sentido; o tom é "
            "de meme/exagerado; a conversa mostra algo impossível para o produto. Afirmações genéricas sobre o "
            "problema do cliente (ex.: 'no horário de pico o WhatsApp lota') são permitidas. "
            'Responda SÓ: {"ok": true ou false, "problema": "qual frase e por quê"}')
    erro = None
    for _ in range(3):  # 25/10: 1 resposta sem JSON reprovou um roteiro bom -> tenta de novo antes de desistir
        try:
            j = _json(llm("Você é revisor jurídico-comercial de anúncios. Seja rigoroso e objetivo. Responda SÓ JSON.",
                          user, max_tokens=500, temperatura=0.1))
            if "ok" in j:
                return bool(j.get("ok")), str(j.get("problema") or "")
            erro = "resposta sem o campo ok"
        except Exception as e:  # noqa: BLE001
            erro = f"{type(e).__name__}: {str(e)[:60]}"
    return False, f"revisor indisponível ({erro})"


def destaques_validos(b, kit):
    """28/10 (júri em todos os vídeos: foto "parada"/"slide", tela desligada da fala): trechos da fala que entram na
    tela quando são ditos. Só palavras que ESTÃO na fala, na ordem (o revisor de fatos já aprovou a fala, então não
    entra afirmação nova). Errado = some (não reprova o roteiro)."""
    fala = _norm(b.get("fala", "")).split()
    bons = []
    for d in (b.get("destaques") or [])[:3]:
        if not isinstance(d, str):
            continue
        ps = _norm(d).split()
        if not 2 <= len(ps) <= 4 or len(d) > 30 or problemas(d, kit):
            continue
        achou = next((i for i in range(len(fala) - len(ps) + 1) if fala[i:i + len(ps)] == ps), None)
        if achou is None or (bons and achou <= bons[-1][1]):
            continue
        bons.append((d.strip().rstrip(".,!?"), achou))
    return [d for d, _ in bons[:2]]


def roteiro(kit, com_veo=False, log=print, cenas=(1,), broll=()):
    """Roteiro aprovado (regra + revisor) ou None. Até 4 tentativas, cada uma corrigindo a anterior."""
    global _argon_falhou
    _argon_falhou = False
    t0 = datetime.now()
    falas_usadas = [f for h in _hist() if h.get("conta") == kit["conta"] for f in h.get("falas", [])]
    pauta = escolher_pauta(kit, log)
    log(f"  [roteirista] pauta {pauta['id']} ({pauta['tipo']}): {pauta['ideia'][:110]}")
    correcao = ""
    for tentativa in range(4):
        try:
            r = _pedir_roteiro(kit, pauta, falas_usadas, correcao, com_veo, cenas, broll)
        except Exception as e:  # noqa: BLE001
            log(f"  [roteirista] LLM falhou: {str(e)[:120]}")
            continue
        # 28/10: a conversa de RESERVA (bloco que não é conversa) não pode derrubar o roteiro (Hermes 21:47: revisor
        # reprovou só por ela, 2 vídeos perdidos) -> aprova sem ela e confere ela depois; reprovada = sai
        reservas = {i: b.pop("conversa") for i, b in enumerate(r.get("blocos") or [])
                    if isinstance(b, dict) and b.get("visual") != "conversa" and b.get("conversa")}
        erros = _validar(r, com_veo, kit, cenas, broll)
        if not erros:
            todas = " ".join(_norm(b["fala"]) for b in r["blocos"])
            # 28/10 (Hermes: 3 de 4 tentativas caíram aqui sem saber em quê): diz QUAL bloco e com QUAL fala antiga
            par = next(((i, f) for i, b in enumerate(r["blocos"], 1) for f in falas_usadas[-90:]
                        if SequenceMatcher(None, _norm(b["fala"]), _norm(f)).ratio() > 0.72), None)
            if par:
                erros = [f"a fala do bloco {par[0]} ficou parecida demais com uma já usada (\"{par[1][:90]}\"): "
                         "mude o ângulo (outra situação do público, outro exemplo), não só as palavras"]
            elif len(todas.split()) > 64:
                erros = ["as 3 falas somadas passam de 60 palavras (o vídeo ficaria longo)"]
        if not erros:
            ok, prob = revisor(kit, r)
            if not ok:
                erros = [f"revisor: {prob[:220]}"]
        if not erros and reservas:
            for i, conv in reservas.items():
                r["blocos"][i]["conversa"] = conv
            e_res = _validar(r, com_veo, kit, cenas, broll)
            ok_res, prob_res = (False, "; ".join(e_res)) if e_res else revisor(kit, r)
            if not ok_res:
                for i in reservas:
                    r["blocos"][i].pop("conversa", None)
                log(f"  [roteirista] conversa de reserva descartada: {prob_res[:160]}")
        if not erros:
            r["pauta_id"], r["pauta_tipo"] = pauta["id"], pauta["tipo"]
            r["tempo_roteiro_s"], r["tentativas_roteiro"] = round((datetime.now() - t0).total_seconds()), tentativa + 1
            for b in r["blocos"]:
                b["fala"] = b["fala"].strip()
                if not b["fala"].endswith((".", "!", "?")):
                    b["fala"] += "."
                b["destaques"] = destaques_validos(b, kit)
            log(f"  [roteirista] aprovado na tentativa {tentativa + 1}: '{r['gancho_tela']}'")
            return r
        log(f"  [roteirista] tentativa {tentativa + 1} reprovada: {'; '.join(erros)[:260]}")
        correcao = "CORRIJA a resposta anterior. Problemas: " + "; ".join(erros)[:900]
    return None


def legenda_final(kit, r):
    tags = " ".join(kit["hashtags"][:6])
    extra = "link no perfil" if "direct" in kit["convite"].lower() else "fale com a gente no direct"
    return f"{r['legenda'].strip()}\n\n👉 {kit['convite']} • {extra}\n\n{tags}".strip()
