# -*- coding: utf-8 -*-
"""narration.py — NARRAÇÃO via IA (Claude + visão dos painéis).

════════════════════════════════════════════════════════════════════════════
MAPA (feito pra manutenção rápida / modelo grátis)
════════════════════════════════════════════════════════════════════════════
Este módulo transforma IMAGENS de painéis em TEXTO de narração. É a etapa cara
(gasta token de IA), então o pipeline salva o resultado em cache e só chama
isto uma vez por capítulo.

Funções que outros arquivos usam (as "públicas"):
  gerar_recap(titulo, paineis, narrator_gender)  -> gera a narração completa
        (lista de locuções: narrador + falas de personagem). É a porta principal.
  gerar_recap_fusao(...)                          -> variante 1-chamada (visão +
        narração juntas); cai pro fluxo 2-passos se o conteúdo +18 bloquear.
  _revisar_coerencia(locucoes, titulo)            -> 2ª passada que costura as
        falas do narrador (evita repetição/salto). Roda 1× e salva no cache.

Helpers internos (prefixo _, só usados aqui dentro):
  _descrever_paineis_claude  descreve cada painel (visão).
  _sanitize_desc/_extract_effect_tag/_log_missing_effect  limpeza + tags de efeito.
  _jpeg_bytes/_image_to_base64  reduzem a imagem pra caber no token da IA.
  _claude_create_retry  retry com backoff (Claude fica instável / 429 / 529).

Depende só de: gemini_llm (cliente IA) + hp_common (PROJECT_DIR, log).
NÃO importa o pipeline nem effects_engine -> sem risco de import circular.
Se for mexer no ESTILO da narração, é aqui (prompts em gerar_recap).
════════════════════════════════════════════════════════════════════════════
"""
import json
import random
import re
import unicodedata
import time
from datetime import datetime, timezone
from pathlib import Path
from io import BytesIO

from PIL import Image

import gemini_llm
from hp_common import PROJECT_DIR, log


# ─── Narração IA (com visão dos painéis) ─────────────────────────────────────
def _load_env():
    """Carrega .env do projeto."""
    env_path = PROJECT_DIR / ".env"
    env_vars = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
    return env_vars


def _image_to_base64(img_path, max_size=800):
    """Reduz imagem e converte pra base64 pra enviar pro Claude."""
    import base64
    from io import BytesIO
    img = Image.open(img_path)
    # Reduzir pra não estourar tokens — max 800px no maior lado
    ratio = min(max_size / max(img.size), 1.0)
    if ratio < 1.0:
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _claude_create_retry(client, max_retries=7, **kwargs):
    """Chama client.messages.create com retry + backoff exponencial.

    Tenta de novo em erros transitórios da Anthropic: 529 (overloaded),
    429 (rate limit) e 500/503. Conteúdo +18 às vezes precisa de várias
    tentativas — o usuário liberou retries generosos.
    """
    delay = 4.0
    last_err = None
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            retryable = any(s in msg for s in
                            ("529", "overload", "429", "rate", "500", "503",
                             "timeout", "connection", "temporarily"))
            if retryable and attempt < max_retries - 1:
                log(f"    ⏳ Claude instável (tentativa {attempt+1}/{max_retries}), aguardando {delay:.0f}s...")
                time.sleep(delay)
                delay = min(delay * 1.7, 45)
                continue
            raise
    raise last_err


_TERMOS_18 = re.compile(r"(?i)(sexu|eroti|adulto|nudez|seios?\b|nua\b|pelad|hentai|pornogr|excita|provoca\w*\s*(sexu|corpo)|insinua\w*\s*sexu|sensual|voluptu|libidin|lasciv|obscen|decot|lingeri|calcinha|sutiã|biquini|peito|seio|bund|coxa\w*\s*expost|explicit|sexual\w*|naked|breast|nippl|panties|underwear|cleavag|strip\w*\s*(teas|cloth)|seduc|intimate\w*\s*scene|body\s*expos|revealing|suggestiv)")
_RECUSA = ("can't", "cannot", "i'm not able", "not appropriate", "sexually", "unable to",
           "não posso descrever", "não posso ajudar", "nao posso descrever", "nao posso ajudar")
_ASPAS = re.compile(r'(\"[^\"]*\"|"[^"]*"|\'[^\']{3,}\')')

_DIC_SEGURO = None
def _carregar_dicionario():
    global _DIC_SEGURO
    if _DIC_SEGURO is not None:
        return _DIC_SEGURO
    p = PROJECT_DIR / "config" / "dicionario_seguro.json"
    try:
        _DIC_SEGURO = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _DIC_SEGURO = {}
    return _DIC_SEGURO

def _sanitizar_narrador(locucoes):
    dic = _carregar_dicionario()
    proibidas = dic.get("proibidas", {})
    if not proibidas:
        return locucoes
    padroes = sorted(proibidas.keys(), key=len, reverse=True)
    regex = re.compile(r"\b(" + "|".join(re.escape(p) for p in padroes) + r")\b", re.IGNORECASE)
    def _sub(m):
        palavra = m.group(0).lower()
        alts = proibidas.get(palavra, [])
        return random.choice(alts) if alts else m.group(0)
    for loc in locucoes:
        p = (loc.get("persona") or "").strip().lower()
        if p in ("narrador", "narradora", "narrator"):
            loc["text"] = regex.sub(_sub, loc.get("text", ""))
    return locucoes


_SOM = re.compile(
    # formas que já existiam
    r"h+[aeiu]*n*g*h*|a+h+|o+h+|e+h+|u+g+h*|h?u+m+|h+m+|n+u+n+g+"
    # 16/10: faltavam os gemidos que o scan mais usa e o edge soletrava letra por letra
    # ("ene-ene-gê-agá" no clímax). Casos reais: cap09 idx 45 'Ngh-', 47 'Aangh... Hngh!!',
    # 77 'Uungh!', 79 'Nngh', 99 'Nnnngh!!'; cap10 idx 36 'UNGH..!'; cap09 76 'Hmph!'.
    r"|[aeiou]+n+g+h*"      # ungh, aangh, uungh
    r"|n+[aeiou]*n*g+h*"    # ngh, nngh, nugh, nnnngh
    r"|h+m+p*h*"            # hm, hmm, hmph
    r"|k+y+a+h*"            # 'KYAH!?' (cap08 82, cap07 29, cap11 88) — faltava o h final
    r"|[aeiou]+h*n+g+h*"    # ahng, aangh, aaahng (o grito mais comum do scan)
    r"|u+w+a+h*|e+k+|a+r+f+|u+f+a*|p+u+a+h*|a+c+k+|[aeiou]+p+"
    r"|p+f+t*|t+s+c*|s+h+|g+r+|z+z+"
)
# Anotação de cena que o scan deixa no balão: '(sorriso)', '(suspira)'. O edge LÊ isso
# ("abre parênteses sorriso") — cap09 idx 85 era '싱긋 (sorriso)'.
_ANOTACAO = re.compile(r"[\(\[]\s*[^\)\]]{1,28}\s*[\)\]]")
# Como palavra portuguesa pode terminar. 'ahng', 'kyah', 'arf', 'uff' não terminam assim:
# é onomatopeia. Guardado sem acento (a comparação passa por _sem_acento).
_VOGAIS = set("aeiouyáàâãéêíóôõúü")


def _latina(c):
    """Letra do alfabeto latino (inclui os acentos do vietnamita, 1E00-1EFF)."""
    o = ord(c)
    return o < 0x250 or 0x1E00 <= o <= 0x1EFF


def limpar_para_tts(texto):
    """Tira anotação entre parênteses do balão. O que sobra é o que a voz deve ler."""
    return re.sub(r"\s{2,}", " ", _ANOTACAO.sub(" ", texto or "")).strip(" -–—,;")


def _eh_som(w):
    """Uma palavra só: é onomatopeia/gemido, não palavra de verdade?

    Regras (as duas últimas entraram em 16/10):
      1. bate com _SOM, antes ou depois de colapsar letra repetida 3x+
         ('Nnnngh' -> 'ngh', 'Kyaaahhh' -> 'kyah');
      2. não é alfabeto latino ('흐으으으' sobrando do scan): nenhuma voz lê isso;
      3. não tem NENHUMA vogal ('ngh', 'nngh', 'hmph', 'kkkkk') — palavra tem.
    O colapso existe pra 'De noooooovo!!!' (regressed-warriors cap27 idx 16) continuar FALA:
    colapsado vira 'novo'. E NÃO existe regra de "termina em letra estranha": ela
    transformava 'SR. INHYUK...' (cap06 idx 17) e nomes coreanos em gemido.
    """
    w2 = re.sub(r"(.)\1{2,}", r"\1", w)
    if _SOM.fullmatch(w) or _SOM.fullmatch(w2):
        return True
    if not all(_latina(c) for c in w2):
        return True
    return not any(c in _VOGAIS for c in w2)


def _so_som(texto):
    """Fala sem nenhuma palavra de verdade: gemido, grito, onomatopeia, reticências ou '?'."""
    palavras = re.findall(r"[^\W\d_]+", limpar_para_tts(texto).lower(), re.UNICODE)
    return not [w for w in palavras if len(w) >= 3 and not _eh_som(w)]


def _sons_para_narrador(locucoes, descriptions, npapel, ng):
    """Fala de personagem que é só som ('Hnngh', 'UGH', '?') vira narração do que acontece: o TTS lendo
    o som fica ruim e o balão já mostra. O prompt pede isso, mas o modelo nem sempre obedece."""
    idx = [i for i, l in enumerate(locucoes)
           if (l.get("persona") or "").strip().lower() not in ("narrador", "narradora", "narrator")
           and _so_som(l.get("text"))]
    if not idx or not descriptions:
        return
    def fala(i):
        return locucoes[i].get("text", "") if 0 <= i < len(locucoes) else ""
    itens = "\n".join(f'{i + 1}: cena: {descriptions[i] if i < len(descriptions) else ""} | antes: "{fala(i - 1)}"'
                      f' | depois: "{fala(i + 1)}"' for i in idx)
    pedido = ("Nestes painéis o balão é só som (gemido, grito, onomatopeia). Escreva a locução do narrador pra "
              "cada um: o que está acontecendo e por que importa, 10-25 palavras, ligando com a fala de antes e a "
              "de depois. Conte a ação e a emoção; não fale do som nem da pontuação em si. "
              'Devolva SÓ JSON {"<número do painel>": "texto"}.\n\n' + itens)
    sistema = (f"Você é {npapel} brasileiro(a) de canal de recap de manhwa: conta a história no presente, com "
               "fatos concretos e reação curta, sem frase pronta.")
    try:
        txt = gemini_llm.generate_text(pedido, system=sistema, max_tokens=2048, temperature=0.8, max_attempts=3)
        novos = json.loads(re.sub(r"^```json\s*|\s*```$", "", (txt or "").strip()))
    except (ValueError, TypeError):
        novos = None
    if not isinstance(novos, dict):
        # A chamada inteira falhou (cota, 503, JSON quebrado): deixa como estava. Silenciar tudo
        # aqui apagava DEZENAS de falas de uma vez e o resultado ia pro narration_cache — o
        # capítulo ficaria mudo nesses painéis também nas próximas renderizações, e a tradução
        # das línguas quebra quando acha texto vazio no meio da lista.
        log(f"  [!] falas só de som: reescrita falhou, {len(idx)} fala(s) ficaram como estavam")
        return
    trocadas = mudas = 0
    for i in idx:
        t = str(novos.get(str(i + 1)) or "").strip()
        if t:
            locucoes[i].update(persona="Narrador", gender=ng, text=t)
            trocadas += 1
        else:
            # 16/10: antes a fala ficava com o personagem e o edge SOLETRAVA o gemido
            # ("ene-ene-gê-agá" na transcrição Groq do cap 9). Melhor painel mudo: o
            # pipeline já trata text vazio como "painel sem narração intencional"
            # (clip rápido, sem SFX) e o balão continua na tela.
            locucoes[i].update(text="", _mudo="gemido sem reescrita")
            mudas += 1
    log(f"  falas só de som -> narrador: {trocadas}/{len(idx)}" + (f" ({mudas} mudas)" if mudas else ""))


def _limpar_anotacoes(locucoes):
    """Tira '(sorriso)', '(impacto)' do texto das falas antes do TTS (o edge lia os parênteses).
    Fala que vira vazia depois disso fica muda — o painel entra como clip rápido."""
    n = 0
    for loc in locucoes:
        t = loc.get("text") or ""
        limpo = limpar_para_tts(t)
        if limpo != t.strip():
            loc["text"] = limpo
            n += 1
    if n:
        log(f"  anotações entre parênteses tiradas de {n} fala(s)")


# ─── narracao-07: balão partido em vários painéis ────────────────────────────
_CONTINUA = re.compile(r"[\s.,\-–—?!…]*(\.\.\.|…|[,\-–—])[\s.,\-–—?!…]*$")


def _junta_com(anterior):
    """Fecha o pedaço do balão que continua no painel seguinte: tudo que for reticência/
    traço/vírgula no fim vira um '...' só (a pausa que o TTS precisa)."""
    m = _CONTINUA.search(anterior)
    if not m:
        return anterior.rstrip()
    return anterior[:m.start()].rstrip() + "..."


def _juntar_balao_partido(locucoes, max_pedacos=4, max_palavras=28):
    """Balão continuado que o modelo transcreveu como uma fala por painel vira UMA fala.

    Cap 10 locuções 72-75 (Noh Yeseul): 'P-PERAI... ?', 'VOCÊ DISSE QUE...', 'ERA PRA GENTE...',
    'COMPRAR ROUPA...' = 4 clips seguidos de 1,87 s sobre painéis de corredor vazio. O
    espectador ouve a frase quebrada com silêncio no meio. Agora a frase inteira sai no 1º
    painel e os seguintes ficam mudos (o pipeline faz clip rápido e o balão continua na tela).
    Só junta pedaço curto (<=5 palavras) do MESMO personagem em painéis seguidos.
    """
    def pedaco(l):
        t = (l.get("text") or "").strip()
        pers = (l.get("persona") or "").strip()
        return (t, pers) if t and pers.lower() not in ("narrador", "narradora", "narrator") else (None, None)

    juntadas = i = 0
    while i < len(locucoes):
        t, pers = pedaco(locucoes[i])
        if not t or len(t.split()) > 5:
            i += 1
            continue
        grupo = [i]
        while len(grupo) < max_pedacos and grupo[-1] + 1 < len(locucoes):
            k = grupo[-1] + 1
            tk, pk = pedaco(locucoes[k])
            ant = (locucoes[grupo[-1]].get("text") or "").strip()
            # só continua se o pedaço anterior estava "em aberto" (reticência/traço/vírgula).
            # O "ou era curtíssimo (<=3 palavras)" que havia aqui juntava fala COMPLETA: duas
            # respostas secas do mesmo personagem em painéis seguidos ("Sim." / "Entendi.")
            # viravam uma só e o segundo painel ficava mudo à toa. Balão partido de verdade
            # sempre deixa a marca de frase em aberto.
            if not tk or pk != pers or len(tk.split()) > 5 or not _CONTINUA.search(ant):
                break
            grupo.append(k)
        if len(grupo) < 2:
            i += 1
            continue
        pedacos = [(locucoes[k].get("text") or "").strip() for k in grupo]
        texto = " ".join([_junta_com(p) for p in pedacos[:-1]] + [pedacos[-1]])
        if len(texto.split()) > max_palavras:
            i += 1
            continue
        locucoes[grupo[0]]["text"] = texto
        for k in grupo[1:]:
            locucoes[k].update(text="", _mudo=f"balão juntado na locução {grupo[0]}")
        juntadas += len(grupo) - 1
        i = grupo[-1] + 1
    if juntadas:
        log(f"  balão partido juntado: {juntadas} painel(is) ficaram mudos")
    return juntadas


# ─── narracao-04: narrador dublando o desenho ────────────────────────────────
# O painel é só recurso gráfico (balão de efeito, linhas de velocidade, logo) e o narrador LÊ
# o recurso: 'até um balão de libido surge flutuando' (cap10 #6), 'com as linhas de velocidade
# na tela' (#10), 'Rola um close no rosto dela' (#33), 'Aí aparece o logo do site' (cap01 #20),
# 'surge o título da nossa obra na tela' (cap08 #4). 29% das falas do narrador no cap 10.
_META_DESENHO = re.compile(
    r"\bbal(ão|ões|ao|oes)\b|linhas? de velocidade|\bclose[- ]?up\b|\bclose\b|a c[âa]mera"
    r"|\bo foco\b|o foco (fecha|vai)|foco em |\blogo (do|da)\b|logotipo|t[íi]tulo (da|do) "
    r"|s[íi]mbolos? de|onomatopeia|efeitos? gr[áa]ficos?|\bno quadro\b|\bpainel\b|\bquadrinho"
    r"|\bna tela\b|letreiro|\bQR code\b", re.I)
# 17/10 (ideia 7, voz humana): o narrador do cap 5 ainda falava como câmera de documentário — "Aí a
# cena exibe toda a exaustão", "A tela fica totalmente preta", "a paisagem externa mostra a fachada",
# "a cena destaca a posição" (5 de 81 falas). Narrador humano conta a HISTÓRIA. Atrás da chave
# voz_humana.sem_camera (config/fila.json), desligada até o dono aprovar.
_META_CAMERA = re.compile(
    r"\b(a|na|da|essa|esta) (cena|tela|imagem|paisagem|sequ[êe]ncia|vis[ãa]o)\b[^.!?]{0,25}?"
    r"\b(mostra|exibe|destaca|revela|apresenta|foca|fica (toda |totalmente )?(preta|escura|branca))"
    r"|\b(a )?tela (fica|escurece|apaga)|\bo enquadramento\b|\bo plano (fecha|abre)\b"
    r"|\bfora d[oa] (quadro|tela|cena)\b", re.I)


def voz_humana(chave):
    """Chave do bloco "voz_humana" de config/fila.json (tudo desligado até o dono ouvir as amostras)."""
    try:
        cfg = json.loads((Path(__file__).resolve().parent.parent / "config" / "fila.json").read_text(encoding="utf-8"))
        return bool((cfg.get("voz_humana") or {}).get(chave, False))
    except (OSError, ValueError):
        return False


def _eh_meta(texto):
    return bool(_META_DESENHO.search(texto) or (voz_humana("sem_camera") and _META_CAMERA.search(texto)))


MULETAS_CFG = Path(__file__).resolve().parent.parent / "config" / "muletas_narradores.json"


def temperar_muletas(locucoes, indices, npapel):
    """Ideia 3 (17/10): põe nas falas do NARRADOR as muletas e o jeito de falar com quem assiste dos
    narradores humanos de referência, na DOSE que eles usam (medida em bin/medir_narradores.py, gravada
    em config/muletas_narradores.json). Chave voz_humana.muletas. UMA chamada; falha = fica o original."""
    if not voz_humana("muletas"):
        return 0
    try:
        cfg = json.loads(MULETAS_CFG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    alvos = [i for i in indices if 0 <= i < len(locucoes)
             and (locucoes[i].get("persona") or "").strip().lower() in ("narrador", "narradora", "narrator")]
    if not alvos:
        return 0
    itens = [f'{i + 1}: "{locucoes[i].get("text", "")}"' for i in alvos]
    pedido = ("Estas são falas do narrador de um recap de manhwa, em sequência. Elas soam como texto lido. "
              "Reescreva pra soar como os narradores brasileiros do YouTube FALAM, mudando o mínimo:\n"
              f"- Muletas que eles usam de verdade (escolha, não use todas): {', '.join(cfg.get('muletas', []))}.\n"
              f"- Dose: no máximo {cfg.get('max_por_10_falas', 4)} muletas a cada 10 falas; NUNCA a mesma duas vezes.\n"
              f"- Fale com quem assiste em 1 ou 2 falas ({', '.join(cfg.get('com_quem_assiste', []))}).\n"
              f"- Use MENOS (nosso texto abusa, os humanos quase não usam): {', '.join(cfg.get('evitar', []))}.\n"
              "- Fala de personagem contada pelo narrador vira discurso indireto como eles fazem: "
              "'ele fala que...', 'ela pergunta se...'.\n"
              "- Frases de tamanhos diferentes: pode quebrar uma longa em duas curtas.\n"
              "- Mesmos fatos, mesma ordem, nada sexual a mais. Não comece fala por interjeição solta.\n"
              'Devolva SÓ JSON {"<número>": "texto"} com TODAS as falas.\n\n' + "\n".join(itens))
    sistema = f"Você é {npapel} brasileiro(a) de canal de recap de manhwa no YouTube, falando, não lendo."
    try:
        txt = gemini_llm.generate_text(pedido, system=sistema, max_tokens=3072, temperature=0.8, max_attempts=3)
        novos = json.loads(re.sub(r"^```json\s*|\s*```$", "", (txt or "").strip()))
    except (ValueError, TypeError):
        return 0
    n = 0
    for i in alvos:
        t = str((novos or {}).get(str(i + 1)) or "").strip()
        if t and 0.6 <= len(t.split()) / max(1, len((locucoes[i].get("text") or "").split())) <= 1.6 \
                and not _eh_meta(t):
            locucoes[i]["text"] = t
            n += 1
    log(f"  muletas: {n}/{len(alvos)} falas do narrador temperadas")
    return n


def falas_meta_desenho(locucoes):
    """[índices] das falas do NARRADOR que descrevem o desenho em vez de contar a história."""
    return [i for i, l in enumerate(locucoes)
            if (l.get("persona") or "").strip().lower() in ("narrador", "narradora", "narrator")
            and _eh_meta(l.get("text") or "")]


# ─── narracao-11: bordão repetido e piada do prompt saindo literal ───────────
# O prompt já pede "no máx 2-3 por capítulo" e "não repetir o mesmo molde mais de 2x", mas
# nada conferia: cap06 'rapaz' 7x, cap10 'a gente' 7x e 'porém' 5x, cap11 'nisso' 6x.
_BORDOES = {
    "rapaz do céu": 1, "meu deus do céu": 1, "pelo amor de deus": 1, "dá uma olhada": 2,
    "que isso": 2, "caramba": 2, "rapaz": 3, "nosso garoto": 3, "a gente": 3,
    "porém": 3, "nisso": 3, "imagina só": 2, "o cara": 4, "a moça": 4,
}
# Exemplos que o prompt dá como ESTILO e o modelo copia letra por letra (cap06 e cap11).
_PIADAS_DO_PROMPT = ("no lugar dele já", "f pro ", "esse cara não aprende", "o maluco deitou",
                     "nome desgraçado", "fica meio sem graça", "taco o gamer",
                     "e o trouxa já tá machucado")


def excessos_de_estilo(locucoes):
    """{índice: [motivos]} das falas do narrador que passam do limite de bordão ou copiam
    uma piada literal do prompt. Determinístico: não chama IA, serve de medida e de alvo."""
    idx = [i for i, l in enumerate(locucoes)
           if (l.get("persona") or "").strip().lower() in ("narrador", "narradora", "narrator")]
    fora = {}
    for termo, limite in _BORDOES.items():
        rx = re.compile(r"\b" + re.escape(termo) + r"\b", re.I)
        vistos = 0
        for i in idx:
            if not rx.search(locucoes[i].get("text") or ""):
                continue
            vistos += 1
            if vistos > limite:
                fora.setdefault(i, []).append(f"'{termo}' {vistos}ª vez (limite {limite})")
    for i in idx:
        baixo = (locucoes[i].get("text") or "").lower()
        for piada in _PIADAS_DO_PROMPT:
            if piada in baixo:
                fora.setdefault(i, []).append(f"piada do prompt literal: '{piada.strip()}'")
    return fora


_STOP_CONF = set("""a o e as os um uma uns umas de da do das dos que em no na nos nas por para pra
pro com se ele ela eles elas isso esse essa este esta aquele aquela nao mas mais como ao aos ja ta foi ser
ter tem so eu tu voce voces lhe me te seu sua seus suas dele dela era esta estava muito bem ai entao ate
tambem ou quando porque pois sobre ainda depois vai vao fazer faz sim nao ola oi hein hum ah oh eh uh""".split())


def _nucleo(texto):
    """Palavras que carregam sentido no texto (sem acento, 4+ letras, fora das vazias)."""
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z]{4,}", t) if w not in _STOP_CONF}


_MARCA_SCAN = re.compile(
    r"blackout|comics?\.com|\.com\b|\.net\b|discord|patreon|scan|fansub|acesso antecipado|"
    r"lan[çc]ado primeiro|leia em|melhor qualidade|tradu[çc][ãa]o|revis[ãa]o por|cap[íi]tulo \d+ em",
    re.I)


def _textos_do_painel(descricao):
    """Tudo que a leitura transcreveu entre aspas, menos onomatopeia e pontuação solta."""
    achados = re.findall(r'"([^"]{2,})"', descricao or "")
    return [t.strip() for t in achados
            if len(t.strip()) >= 3 and not _SOM.fullmatch(t.strip().lower().strip(".!?~- "))
            and not _MARCA_SCAN.search(t)]   # propaganda do scan não é fala do manhwa


def falas_perdidas(locucoes, descriptions, minimo=0.34):
    """[(i, [falas que ficaram de fora])] — painel cuja locução não cobre o texto lido ali.

    Existe porque a leitura e o roteiro perdiam fala sem avisar ninguém. Caso real medido no cap 1
    de The Inheritor: o painel 41 traz as caixas "HAN SIHYUN...", "AQUELA MULHER FOI" e "O MEU
    PRIMEIRO AMOR." e o roteiro saiu "ele lembra do seu primeiro amor" — o NOME da personagem
    central nunca foi dito no vídeo. Quem assiste não estranha; quem leu a obra vê o buraco.

    A comparação é por palavra-núcleo, não literal: a locução parafraseia de propósito. Fica de
    fora quando menos de `minimo` das palavras da fala aparece, ou quando um NOME PRÓPRIO do texto
    não aparece em nenhum lugar da locução (nome é o que mais faz falta)."""
    perdidas, deslocadas = [], 0

    def cobre(f, j):
        """A locução j diz o que está escrito em f?"""
        if not (0 <= j < len(locucoes)):
            return False
        alvo = _nucleo(locucoes[j].get("text", "")) | _nucleo(locucoes[j].get("persona", ""))
        nuc = _nucleo(f)
        nomes = {_nucleo(p).pop() for p in re.findall(r"\b[A-ZÀ-Ú][a-zà-ú]{3,}", f) if _nucleo(p)}
        if nomes:
            return bool(nomes & alvo)
        if not nuc:
            return True   # fala só com palavra curta ("SIM.", "AH...") — não dá pra avaliar, não acusa
        return len(nuc & alvo) / len(nuc) >= minimo

    for i, _loc in enumerate(locucoes):
        if i >= len(descriptions or []):
            break
        falas = _textos_do_painel(descriptions[i])
        if not falas:
            continue
        fora = []
        for f in falas:
            if cobre(f, i):
                continue
            # a mesma fala saindo no painel vizinho é DESLOCAMENTO, não sumiço: mandar reescrever
            # duplicaria a fala no vídeo. Medido no cap 7: "NÃO QUER ME MOSTRAR?" está no painel 13
            # e saiu na locução do 15.
            if any(cobre(f, j) for j in (i - 2, i - 1, i + 1, i + 2)):
                deslocadas += 1
                continue
            fora.append(f)
        if fora:
            perdidas.append((i, fora))
    if deslocadas and locucoes:
        log(f"  falas: {deslocadas} saíram num painel vizinho (atraso de 1-2 painéis)")
    return perdidas


# Som que a voz do edge erra quando abre a locução: palavra comprida ou com nasal/dígrafo logo de
# cara. Medido com o dono em 16/10 ouvindo as amostras — "Herança?!" sai torto nas três vozes.
_ABRE_DIFICIL = re.compile(r"^[\"'\s]*[A-Za-zÀ-ú]*(?:ç|ã|õ|â|ê|ô|lh|nh|rr|ss)[A-Za-zÀ-ú]*\b", re.I)


def falas_curtas_arriscadas(locucoes, max_palavras=4):
    """[i] das falas de PERSONAGEM curtas que começam pela palavra difícil.

    Fala de 1 a 4 palavras cujo primeiro termo é comprido (7+ letras) ou tem som difícil: a voz
    entra sem contexto e erra justamente essa palavra. Não acusa fala simples e curta
    ("Sim.", "Vamos!"), que sai bem."""
    risco = []
    for i, l in enumerate(locucoes):
        if (l.get("persona") or "").lower() in ("narrador", "narradora", "narrator"):
            continue
        t = (l.get("text") or "").strip()
        palavras = [re.sub(r"[^\wÀ-ú]", "", p) for p in t.split()]
        palavras = [p for p in palavras if p]
        if not palavras or len(palavras) > max_palavras:
            continue
        # Interjeição de uma palavra curta ("Sim.", "Opa!", "Ei!") sai bem — é som simples e comum.
        # Qualquer outra fala curta é risco: o dono ouviu "Herança?!" E "O que...?" saírem tortas, e
        # a segunda abre com uma palavra de 1 letra. Não é o tamanho da 1ª palavra, é a locução
        # inteira ser curta demais pra voz pegar embalo.
        if len(palavras) == 1 and len(palavras[0]) <= 4:
            continue
        if len(palavras) <= 2 or len(max(palavras, key=len)) >= 5:
            risco.append(i)
    return risco


_INTERJEICAO = {"ah", "ahh", "oh", "ohh", "hum", "hm", "hmm", "eh", "uh", "hã", "ué", "ai", "ui", "nnh", "hnnh", "ugh"}


def _primeira_palavra(texto):
    for p in (texto or "").split():
        p = re.sub(r"[^\wÀ-ú]", "", p)
        if p:
            return p
    return ""


def falas_longas_arriscadas(locucoes, max_palavras=4):
    """[i] das falas de PERSONAGEM longas (5+ palavras) que abrem numa palavra que a voz erra.

    16/10, cap 4 aos 7m30: "Obrigada... obrigada por me dar uma ordem!" (12 palavras) saiu
    americanizado. O tamanho da fala não salva: a voz entra sem embalo do mesmo jeito, e erra a
    PRIMEIRA palavra quando ela é comprida (7+ letras) ou tem nasal/dígrafo (5+ letras: "Então",
    "Nossa"). "Não", "Eu", "Mas" saem bem e ficam."""
    risco = []
    for i, l in enumerate(locucoes):
        if (l.get("persona") or "").lower() in ("narrador", "narradora", "narrator"):
            continue
        t = (l.get("text") or "").strip()
        if len(t.split()) <= max_palavras:
            continue  # curta: é com falas_curtas_arriscadas
        p = _primeira_palavra(t)
        if len(p) >= 7 or (len(p) >= 5 and _ABRE_DIFICIL.match(p)):
            risco.append(i)
    return risco


def _dar_corpo_as_falas_curtas(locucoes, descriptions, npapel, ng):
    """UMA chamada que reescreve as falas de risco pra não abrirem na palavra difícil: as curtas
    ganham corpo, as longas ganham só uma abertura antes da 1ª palavra."""
    curtas = set(falas_curtas_arriscadas(locucoes))
    alvos = sorted(curtas | set(falas_longas_arriscadas(locucoes)))[:30]
    if not alvos:
        return 0
    itens = []
    for i in alvos:
        cena = (descriptions[i] if descriptions and i < len(descriptions) else "")[:160]
        tipo = "CURTA" if i in curtas else "LONGA"
        itens.append(f'{i + 1} [{tipo}]: "{locucoes[i].get("text", "")}" | quem fala: '
                     f'{locucoes[i].get("persona", "")} | cena: {cena}')
    pedido = ("Estas falas de personagem COMEÇAM por uma palavra que a voz do vídeo erra quando é a "
              "primeira da fala. Reescreva cada uma mantendo o sentido e o tom, mas com uma abertura "
              "curta e natural ANTES dessa palavra. Regras:\n"
              "- Continua sendo a fala DELE, em 1ª pessoa — não vire narração.\n"
              "- A abertura é palavra de verdade (\"Como assim\", \"Espera\", \"Eu\", \"Sério\", "
              "\"Olha\", \"Pera\"). PROIBIDO abrir com interjeição (Ah, Oh, Hum, Eh, Ué): a voz erra "
              "do mesmo jeito. Reticência ou repetir a palavra também NÃO resolvem.\n"
              "- Varie: não use a mesma abertura em duas falas desta lista.\n"
              "- [CURTA]: 4 a 12 palavras. Fala de gente, não de livro. Exemplos: \"Herança?!\" -> "
              "\"Como assim, herança?\"; \"Do meu pai?\" -> \"Espera, isso era do meu pai?\"; "
              "\"O que...?\" -> \"Peraí, do que você tá falando?\".\n"
              "- [LONGA]: o resto da fala fica IGUAL; só entram 1 a 3 palavras na frente. Exemplo: "
              "\"Obrigada... obrigada por me dar uma ordem!\" -> \"Eu... muito obrigada por me dar "
              "uma ordem!\".\n"
              'Devolva SÓ JSON {"<número>": "texto"}.\n\n' + "\n".join(itens))
    sistema = (f"Você escreve as falas de personagens num recap de manhwa narrado em pt-BR por "
               f"um(a) {npapel}. Escreve como as pessoas falam.")
    try:
        txt = gemini_llm.generate_text(pedido, system=sistema, max_tokens=2048, temperature=0.7,
                                       max_attempts=3)
        novos = json.loads(re.sub(r"^```json\s*|\s*```$", "", (txt or "").strip()))
    except (ValueError, TypeError):
        novos = None
    if not isinstance(novos, dict):
        log(f"  [!] {len(alvos)} falas de abertura difícil ficaram como estavam (reescrita falhou)")
        return 0
    n = 0
    for i in alvos:
        t = str(novos.get(str(i + 1)) or "").strip()
        nova = [{"persona": locucoes[i].get("persona"), "text": t}]
        if falas_curtas_arriscadas(nova) or falas_longas_arriscadas(nova):
            continue  # a reescrita ainda abre na palavra difícil
        if _primeira_palavra(t).lower() in _INTERJEICAO:
            continue  # "Ah, obrigada..." — interjeição não dá embalo (testado com o dono em 16/10)
        n_orig = len((locucoes[i].get("text") or "").split())
        cabe = (3 <= len(t.split()) <= 16) if i in curtas else (n_orig < len(t.split()) <= n_orig + 4)
        if cabe:
            locucoes[i]["text"] = t
            n += 1
    log(f"  falas de abertura difícil: {len(alvos)} ({len(curtas)} curtas), {n} reescritas")
    return n


def _completar_falas_perdidas(locucoes, descriptions, npapel, ng):
    """UMA chamada que reescreve as locuções que deixaram fala de fora. Falha = fica o original.

    Fala pesada não é pulada: o prompt manda dizer com palavra segura ou, se não der, o narrador
    conta o que acontece — foi o que o dono pediu em 16/10."""
    perdidas = falas_perdidas(locucoes, descriptions)
    if not perdidas:
        return 0
    dic = _carregar_dicionario().get("proibidas", {})
    trocas = ", ".join(f"{k}->{v[0]}" for k, v in list(dic.items())[:14] if v)
    itens = []
    for i, fora in perdidas[:40]:          # teto por chamada: o resto fica pro log
        itens.append(f'{i + 1}: locução atual "{locucoes[i].get("text", "")}" | '
                     f'ficou de fora: {" / ".join(chr(34) + f + chr(34) for f in fora[:4])} | '
                     f'cena: {(descriptions[i] or "")[:220]}')
    pedido = ("Nestas locuções de um recap de manhwa ficou texto do quadrinho de FORA. Reescreva cada "
              "uma cobrindo TUDO o que ficou de fora, sem perder o que já estava lá. Regras:\n"
              "- Se as falas que faltam são do MESMO personagem, deixe tudo na boca dele, quase "
              "literal — não troque pra narrador, que o vídeo já tem narrador demais.\n"
              "- Só use discurso indireto ('fala que', 'pergunta se') quando as falas forem de "
              "pessoas diferentes ou vierem de caixa de narração.\n"
              "- NOME PRÓPRIO que aparece no texto TEM de ser dito.\n"
              "- Fala pesada demais pro YouTube: diga o mesmo com palavra segura "
              f"({trocas}); se nem assim der, CONTE o que está acontecendo sem repetir as palavras. "
              "Nunca pule.\n"
              "- 12-32 palavras, presente, sem citar desenho/balão/quadro.\n"
              "- Não comece a fala pela palavra principal sozinha: a voz erra a primeira palavra da locução. Ponha uma abertura curta antes ('Como assim, ___?', 'Espera, ___').\n"
              'Devolva SÓ JSON {"<número>": "texto"}.\n\n' + "\n".join(itens))
    sistema = (f"Você é {npapel} brasileiro(a) de canal de recap de manhwa: conta a história inteira, "
               "sem deixar fala de fora, no presente e com fatos concretos.")
    try:
        txt = gemini_llm.generate_text(pedido, system=sistema, max_tokens=4096, temperature=0.7, max_attempts=3)
        novos = json.loads(re.sub(r"^```json\s*|\s*```$", "", (txt or "").strip()))
    except (ValueError, TypeError):
        novos = None
    if not isinstance(novos, dict):
        log(f"  [!] {len(perdidas)} painéis com fala de fora ficaram como estavam (reescrita falhou)")
        return 0
    n = 0
    for i, _fora in perdidas:
        t = str(novos.get(str(i + 1)) or "").strip()
        if len(t.split()) >= 8 and not _META_DESENHO.search(t):
            locucoes[i]["text"] = t
            n += 1
    sobrou = falas_perdidas(locucoes, descriptions)
    log(f"  falas: {len(perdidas)} painéis tinham texto de fora, {n} reescritos, "
        f"{len(sobrou)} ainda incompletos")
    return n


def _reescrever_narrador_fraco(locucoes, descriptions, npapel, ng):
    """UMA chamada que reescreve as falas do narrador que dublam o desenho (narracao-04) e as
    que estouram o bordão/copiam a piada do prompt (narracao-11). Falha = fica o original."""
    meta = set(falas_meta_desenho(locucoes))
    excesso = excessos_de_estilo(locucoes)
    alvos = sorted(meta | set(excesso))
    if not alvos:
        return 0
    def desc(i):
        return descriptions[i] if descriptions and i < len(descriptions) else ""
    def vizinha(i):
        return (locucoes[i].get("text", "") if 0 <= i < len(locucoes) else "")[:90]
    itens = []
    for i in alvos:
        motivos = []
        if i in meta:
            motivos.append("narra o DESENHO (balão/linhas/close/logo/título/câmera, 'a cena mostra', "
                           "'a tela fica preta') em vez da história")
        motivos += excesso.get(i, [])
        itens.append(f'{i + 1}: "{locucoes[i].get("text", "")}" | problema: {"; ".join(motivos)}'
                     f' | cena: {desc(i)} | antes: "{vizinha(i - 1)}" | depois: "{vizinha(i + 1)}"')
    pedido = ("Reescreva SÓ estas locuções do narrador de um recap de manhwa. Regras:\n"
              "- PROIBIDO citar o desenho: balão, linhas de velocidade, close, foco, câmera, logo, "
              "título, quadro, painel, 'na tela'. Painel que é só efeito gráfico = continue a "
              "história (o que o personagem sente ou decide por causa daquilo).\n"
              "- Não repita o bordão apontado: troque por outra forma de dizer.\n"
              "- 10-25 palavras, presente, fato concreto, ligando com a fala de antes e a de depois.\n"
              'Devolva SÓ JSON {"<número>": "texto"}.\n\n' + "\n".join(itens))
    sistema = (f"Você é {npapel} brasileiro(a) de canal de recap de manhwa: conta a história no presente, "
               "com fatos concretos e reação curta, sem frase pronta e sem falar do desenho.")
    try:
        txt = gemini_llm.generate_text(pedido, system=sistema, max_tokens=3072, temperature=0.8, max_attempts=3)
        novos = json.loads(re.sub(r"^```json\s*|\s*```$", "", (txt or "").strip()))
    except (ValueError, TypeError):
        novos = None
    if not isinstance(novos, dict):
        log(f"  [!] {len(alvos)} falas de narrador fracas ficaram como estavam (reescrita falhou)")
        return 0
    n = 0
    for i in alvos:
        t = str(novos.get(str(i + 1)) or "").strip()
        if len(t.split()) >= 6 and not _eh_meta(t):
            locucoes[i]["text"] = t
            n += 1
    log(f"  narrador: {n}/{len(alvos)} falas reescritas ({len(meta)} dublavam o desenho, "
        f"{len(excesso)} repetiam bordão/piada)")
    return n


_GANCHO_FIM = re.compile(r"\?|será que|o problema|resta saber|próximo capítulo|vem aí|vem por aí", re.I)


def _personagens(locucoes, conhecidos):
    """[(nome, gênero)] dos personagens com nome: os da obra (conhecidos) ou, sem eles, os deste capítulo."""
    if conhecidos:
        return [(n, g) for n, g, _c in conhecidos[:4]]
    cont = {}
    for l in locucoes:
        p = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", l.get("persona") or "").strip()
        if p and p.lower() not in ("narrador", "narradora", "narrator") and p.lower() not in _GENERICOS:
            cont.setdefault(p, [0, l.get("gender") or "?"])[0] += 1
    return [(p, g) for p, (_c, g) in sorted(cont.items(), key=lambda x: -x[1][0])[:4]]


def _abertura_e_fim(locucoes, descriptions, npapel, ng, conhecidos=None, titulo="", abertura_txt="", fechamento_txt=""):
    """1ª locução = narrador apresentando o protagonista e a situação; última = narrador com gancho. O prompt pede,
    mas o modelo abria descrevendo o céu ou com fala solta de personagem e fechava em fala solta ("Herança?!")."""
    if len(locucoes) < 3:
        return
    pers = _personagens(locucoes, conhecidos)
    eh_narr = lambda l: (l.get("persona") or "").strip().lower() in ("narrador", "narradora", "narrator")  # noqa: E731
    desc = lambda i: descriptions[i] if descriptions and 0 <= i < len(descriptions) else ""  # noqa: E731
    l0, lf = locucoes[0], locucoes[-1]
    cita_nome = any(n.split()[0].lower() in l0.get("text", "").lower() for n, _g in pers[:2])
    abrir = not eh_narr(l0) or (pers and not cita_nome)
    fechar = not eh_narr(lf) or not _GANCHO_FIM.search(lf.get("text", ""))
    if not (abrir or fechar):
        return
    lista = ", ".join(f"{n} ({'homem' if g == 'M' else 'mulher' if g == 'F' else '?'})" for n, g in pers)
    partes = []
    if abrir:
        partes.append(f'"abertura" (painel 1): NO MÁXIMO 2 frases curtas (15-30 palavras): quem é o protagonista da obra '
                      f"e em que situação ele está + o conflito do capítulo, já entrando na cena. Nada de descrever "
                      f"cenário/céu, nada de 'olá'/'galera'. Cena: {desc(0)} | fala original ({l0.get('persona')}): "
                      f"\"{l0.get('text', '')}\" | próximas cenas: {' / '.join(desc(i) for i in range(1, 6))}"
                      + (f" | fórmula deste capítulo (use a forma, não copie o exemplo): {abertura_txt}" if abertura_txt else ""))
    if fechar:
        partes.append(f'"final" (último painel): cliffhanger + especulação concreta do que vem ("será que...", "o problema '
                      f'é que..."), 15-30 palavras. Cena: {desc(len(locucoes) - 1)} | fala original ({lf.get("persona")}): '
                      f"\"{lf.get('text', '')}\" | cenas antes: {' / '.join(desc(i) for i in range(len(locucoes) - 4, len(locucoes) - 1))}"
                      + (f" | jeito de fechar deste capítulo (use a forma, sem pedir like): {fechamento_txt}" if fechamento_txt else ""))
    pedido = (f"Reescreva estas locuções do narrador de um recap de manhwa ({titulo or 'capítulo'}). Personagens "
              f"(use o gênero certo de cada um): {lista or 'veja as cenas'}. Se a fala original é de personagem e "
              "importa, use ela dentro da narração (entre aspas ou 'ele fala que...'). Presente, fatos concretos, "
              "tom de conversa, sem frase pronta.\n- " + "\n- ".join(partes) +
              '\nDevolva SÓ JSON {"abertura": "...", "final": "..."} (só as chaves pedidas).')
    sistema = (f"Você é {npapel} brasileiro(a) de canal de recap de manhwa: conta a história pra quem nunca leu, "
               "com fatos concretos e opinião rápida.")
    try:
        txt = gemini_llm.generate_text(pedido, system=sistema, max_tokens=1024, temperature=0.8, max_attempts=3)
        novos = json.loads(re.sub(r"^```json\s*|\s*```$", "", (txt or "").strip()))
    except (ValueError, TypeError):
        novos = None
    if not isinstance(novos, dict):
        log("  [!] abertura/final: reescrita falhou, ficam os originais")
        return
    for chave, loc, pedir in (("abertura", l0, abrir), ("final", lf, fechar)):
        t = str(novos.get(chave) or "").strip()
        if pedir and len(t.split()) >= 6:
            loc.update(persona="Narrador", gender=ng, text=t)
            log(f"  {chave} reescrita pelo narrador: {t[:90]}")


def _sanitize_desc(line):
    """Limpa uma linha de descrição (numeração, termos +18, recusas). O texto TRANSCRITO do balão (entre
    aspas) fica intacto: trocar palavra dentro da fala cortava/estragava a fala no vídeo, e um balão com
    "desculpe"/"não posso" fazia a linha inteira virar "Cena do manhwa"."""
    line = re.sub(r"^\d+[\.\)]\s*", "", (line or "").strip())
    partes = _ASPAS.split(line)  # índices ímpares = trechos entre aspas
    fora = " ".join(p for k, p in enumerate(partes) if k % 2 == 0).lower()
    if any(x in fora for x in _RECUSA):
        return "Cena do manhwa"
    partes = [p if k % 2 else re.sub(r"(?i)\[?(nsfw|adult|18\+|mature|explicit)\]?", "",
                                     _TERMOS_18.sub("cena intensa", p))
              for k, p in enumerate(partes)]
    return "".join(partes).strip()


def _extract_effect_tag(desc):
    """Extrai a tag de efeito sugerida pelo Gemini Vision da descrição.

    Retorna (descrição_limpa, tag_efeito). Tag pode ser:
    shake, pulse, zoom_slow, zoom_fast, pan_down, static, ou None.
    """
    match = re.search(r"\[(\w+)\]\s*$", desc)
    if match:
        tag = match.group(1).lower()
        clean_desc = desc[:match.start()].strip()
        return clean_desc, tag
    return desc, None


# Efeitos sugeridos pela IA que a pipeline suporta atualmente
SUPPORTED_EFFECTS = {"shake", "pulse", "zoom_slow", "zoom_fast", "pan_down", "static"}


# Lista de efeitos desejados mas não implementados (a popular com o tempo)
_MISSING_EFFECTS_LOG = PROJECT_DIR / "workspace" / "missing_effects.json"


def _log_missing_effect(effect_tag, description):
    """Registra efeitos desejados pela IA que ainda não temos implementados."""
    if effect_tag in SUPPORTED_EFFECTS or not effect_tag:
        return
    import json as _json
    existing = []
    if _MISSING_EFFECTS_LOG.exists():
        try:
            existing = _json.loads(_MISSING_EFFECTS_LOG.read_text())
        except Exception:
            existing = []
    # Evitar duplicatas
    if not any(e.get("effect") == effect_tag for e in existing):
        existing.append({"effect": effect_tag, "example_desc": description[:80],
                         "added": datetime.now(timezone.utc).isoformat()})
        _MISSING_EFFECTS_LOG.write_text(_json.dumps(existing, ensure_ascii=False, indent=2))


def _jpeg_bytes(panel_path, max_side=1024, quality=80):
    """Reduz o painel e retorna bytes JPEG (pra visão). Com 400 px / q55 a letra do balão ficava
    ilegível e a transcrição saía cortada ou chutada."""
    from io import BytesIO
    img = Image.open(panel_path)
    ratio = min(max_side / max(img.size), 1.0)
    if ratio < 1.0:
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _claude_proxy(texto, imagens=(), system=None, max_tokens=1500):
    """Reserva quando o Gemini falha (cota/bloqueio): Claude via claude_client (Sonnet do Kiro,
    depois Opus do proxy do manhwa-react). Aceita imagens. None se falhar."""
    import claude_client
    out = claude_client.perguntar(texto, imagens, system=system, max_tokens=max_tokens, temperature=0.7)
    if out:
        log("    [reserva] respondido via Claude (proxy)")
    return out


def _descrever_paineis_claude(panel_paths):
    """Descreve os painéis via Gemini Vision (proxy do Claude está fora).

    Envia em batches de 5 imagens; se o batch vier incompleto, refaz individual.
    safetySettings=BLOCK_NONE no gemini_llm ajuda com conteúdo +18.
    """
    # TODO texto da página, não só balão de fala: em manhwa a CAIXA DE NARRAÇÃO retangular carrega o
    # fio da história, e o modelo descrevia em vez de transcrever. Medido no cap 1 de The Inheritor:
    # as caixas "HAN SIHYUN... / AQUELA MULHER FOI / O MEU PRIMEIRO AMOR." (painel 41) viraram
    # "Narrador introduz o nome e o primeiro amor" — o nome da personagem central nunca foi dito no
    # vídeo, e quem leu a obra vê o buraco.
    BATCH_PROMPT = ("Descreva cada cena de quadrinhos: a AÇÃO em 1 frase curta (max 15 palavras) e "
                    "TRANSCREVA TODO TEXTO ESCRITO que aparecer, palavra por palavra, entre aspas duplas, "
                    "sem resumir, cortar nem suavizar (palavrões e palavras fortes como 'escrava' ficam "
                    "como estão). Conta como texto: balão de fala, balão de pensamento (contorno de nuvem "
                    "ou tracejado), CAIXA DE NARRAÇÃO retangular, legenda, placa, tela de celular e "
                    "mensagem. NUNCA diga só que 'há uma narração' ou 'o texto apresenta o personagem' — "
                    "escreva o que está escrito. Diga o tipo e quem fala: 'Garota diz: \"Eu te odeio!\"', "
                    "'caixa de narração: \"Han Sihyun...\"', 'pensamento dele: \"Será que é ela?\"'; se a "
                    "seta do balão aponta pra fora do quadro, diga 'alguém fora do quadro diz'. "
                    "NÃO transcreva marca d'água nem propaganda do site que digitalizou (nome de scan, endereço .com/.net, 'leia em', 'acesso antecipado', Discord, Patreon, número de página, crédito de tradução): isso não é da história e não pode entrar na narração — diga só 'marca do site'. Se o painel não tiver texto da história, escreva 'sem texto'. "
                    "NÃO mencione roupas, corpo, aparência física ou nudez. Se a cena tiver conteúdo "
                    "adulto, descreva a ação só como 'cena intensa', mas transcreva os balões mesmo assim.\n"
                    "Ao final de CADA descrição, adicione entre colchetes o efeito visual ideal: "
                    "[shake] para impacto/luta, [pulse] para nervosismo/tensão, "
                    "[zoom_slow] para momentos calmos, [zoom_fast] para surpresa, "
                    "[pan_down] para revelação, [static] para diálogo normal. "
                    "Exemplo: 'Ele desfere um soco poderoso [shake]'\n"
                    "Responda numerado (1. 2. 3. ...):")
    IND_PROMPT = ("Descreva esta cena de quadrinhos: a ação em 1 frase curta (max 15 palavras) e "
                  "TRANSCREVA TODO TEXTO ESCRITO entre aspas duplas, palavra por palavra, sem resumir "
                  "nem suavizar — balão de fala, balão de pensamento, CAIXA DE NARRAÇÃO retangular, "
                  "legenda, placa, tela de celular —, dizendo o tipo e quem fala (ou 'alguém fora do "
                  "quadro' se a seta aponta pra fora). NUNCA descreva o texto em vez de transcrever. "
                  "NÃO transcreva marca d'água nem propaganda do site que digitalizou (nome de scan, endereço .com, 'leia em', Discord, Patreon, crédito de tradução): diga só 'marca do site'. Sem texto da história: escreva 'sem texto'. "
                  "Se for conteúdo adulto, descreva a ação só como 'cena intensa', mas transcreva o balão.\n"
                  "Ao final, adicione entre colchetes o efeito visual ideal: "
                  "[shake] impacto, [pulse] tensão, [zoom_slow] calmo, "
                  "[zoom_fast] surpresa, [pan_down] revelação, [static] diálogo.")

    descriptions = []
    batch_size = 5
    total = len(panel_paths)

    for batch_start in range(0, total, batch_size):
        batch = panel_paths[batch_start:batch_start + batch_size]
        imgs = [_jpeg_bytes(p) for p in batch]

        text = gemini_llm.describe_images(imgs, BATCH_PROMPT, max_tokens=1500, max_attempts=4)
        if not text:
            text = _claude_proxy(BATCH_PROMPT, imgs, max_tokens=1800)
        # O número que o modelo escreve manda, não a ordem das linhas: ele às vezes quebra uma
        # descrição em duas linhas e, pela ordem, todo o resto do lote andava um painel.
        por_numero = {}
        if text:
            atual = None
            for line in text.splitlines():
                m = re.match(r"\s*(\d{1,2})\s*[.):-]\s*(.+)", line)
                if m and 1 <= int(m.group(1)) <= len(batch):
                    atual = int(m.group(1)) - 1
                    resto = m.group(2)
                elif atual is None:
                    continue
                else:
                    resto = line        # continuação da descrição anterior
                s = _sanitize_desc(resto)
                if s:
                    por_numero[atual] = (por_numero.get(atual, "") + " " + s).strip()
        batch_descs = []
        if len(por_numero) == len(batch):
            for i in range(len(batch)):
                clean_s, effect_tag = _extract_effect_tag(por_numero[i])
                batch_descs.append(clean_s)
                _log_missing_effect(effect_tag, clean_s)
        elif por_numero:
            log(f"  [!] visão batch {batch_start}: {len(por_numero)}/{len(batch)} numerados — "
                f"refazendo individual pra não desalinhar")

        # Batch incompleto -> processa cada painel individualmente
        if len(batch_descs) < len(batch):
            log(f"  [!] Visão batch {batch_start} incompleta ({len(batch_descs)}/{len(batch)}), individual...")
            batch_descs = []
            for p, imgb in zip(batch, imgs):
                t = gemini_llm.describe_image(imgb, IND_PROMPT, max_tokens=400)
                s = _sanitize_desc(t) if t else "Cena do manhwa"
                clean_s, effect_tag = _extract_effect_tag(s)
                batch_descs.append(clean_s)
                _log_missing_effect(effect_tag, clean_s)

        descriptions.extend(batch_descs[:len(batch)])
        log(f"  visão {min(batch_start + batch_size, total)}/{total}")

    while len(descriptions) < len(panel_paths):
        descriptions.append("Continuação da cena")
    return descriptions[:len(panel_paths)]


def gerar_recap_fusao(titulo, panel_paths, narrator_gender="F"):
    """FUSÃO (teste): Gemini olha os painéis e gera o roteiro direto, numa só chamada.

    Combina visão + narração (em vez de 2 passos). Pede um campo 'cena' por painel
    pra manter a detecção de efeitos (impacto/tensão/sensual) funcionando.
    """
    n = len(panel_paths)
    ng = "M" if (narrator_gender or "F").upper() == "M" else "F"
    system = (
        "Voce e uma narradora brasileira de canal de recap de manhwa/webtoon. "
        "Estilo: envolvente, dramatico, com humor leve e carisma. Use girias brasileiras.\n\n"
        "Voce vai VER os paineis na ordem. Para CADA painel gere UMA locucao (1-2 frases, "
        "8-25 palavras). Se o painel tiver um BALÃO DE FALA, a locução DEVE ser do "
        "PERSONAGEM falando o texto do balão. Se não tiver balão, ou se o balão for "
        "genérico (ex: 'Ugh', 'Ah'), use Narrador (off). "
        "Use o NOME do personagem quando der pra inferir; gender 'M' ou 'F'. "
        f"Para narracao off use persona='Narrador', gender='{ng}'.\n\n"
        "Inclua tambem um campo 'cena' com 3-8 palavras descrevendo acao/clima do painel "
        "(ex: 'beijo intenso no quarto', 'soco com impacto', 'olhar tenso'). "
        "NAO descreva nudez/corpo; para conteudo adulto use 'cena intensa'.\n\n"
        "Saida JSON estrita (sem markdown):\n"
        '{"titulo_video":"...","tags":["..."],"locucoes":['
        '{"painel":1,"persona":"Narrador","gender":"F","text":"...","cena":"..."}]}\n'
        f"TOTAL de locucoes DEVE ser EXATAMENTE {n} (uma por painel, na ordem)."
    )
    user = (f"Manhwa: {titulo}. {n} paineis na ordem abaixo. "
            f"Olhe cada um e gere o roteiro dramatico completo em JSON.")
    imgs = [_jpeg_bytes(p) for p in panel_paths]
    log(f"  [FUSÃO] Gemini lendo {n} painéis + gerando roteiro numa só chamada...")
    # max_attempts baixo: se bloquear (conteúdo +18), falha rápido pra cair no 2-passos
    text = gemini_llm.generate_from_images(imgs, user, system=system,
                                           max_tokens=8192, max_attempts=3)
    if not text:
        log("  [X] [FUSÃO] bloqueada/indisponível (provável conteúdo sensível)")
        return None
    text = re.sub(r"^```json\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        log(f"  [X] [FUSÃO] JSON inválido: {e}")
        return None
    locucoes = data.get("locucoes", [])
    while len(locucoes) < n:
        locucoes.append({"persona": "Narrador", "gender": ng,
                         "text": "E a história continua...", "cena": ""})
    locucoes = locucoes[:n]
    data["locucoes"] = locucoes
    data["descriptions"] = [_sanitize_desc(l.get("cena", "")) for l in locucoes]
    log(f"  [OK] [FUSÃO] Roteiro: {data.get('titulo_video', titulo)}")
    return data


_GENERICOS = {"rapaz", "garota", "garoto", "homem", "mulher", "menina", "menino", "desconhecido",
              "desconhecida", "personagem", "alguém", "alguem", "voz", "estranho", "estranha"}


def personagens_anteriores(obra, cap):
    """[(nome, gênero, nº de falas)] dos personagens com NOME dos capítulos da obra já roteirizados (lidos
    dos roteiros em cache, só pt). A voz é escolhida pelo nome (gemini_tts.voice_for_persona): se o
    protagonista vira "Rapaz" num capítulo, ele troca de voz. Capítulo refeito (--force-llm) também lê
    os seguintes e o próprio roteiro antigo, pra não trocar nome."""
    cont = {}
    pasta = PROJECT_DIR / "workspace" / "narration_cache"
    for f in pasta.glob(f"{obra}-cap*panels.json"):
        m = re.match(rf"^{re.escape(obra)}-cap(\d+)_", f.name)
        if not m:
            continue
        try:
            locs = json.loads(f.read_text(encoding="utf-8")).get("locucoes", [])
        except (OSError, ValueError):
            continue
        for l in locs:
            p = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", l.get("persona") or "").strip()
            if not p or p.lower() in ("narrador", "narradora", "narrator") or p.lower() in _GENERICOS:
                continue
            c = cont.setdefault(p, {"M": 0, "F": 0})
            if l.get("gender") in ("M", "F"):
                c[l["gender"]] += 1
    return sorted(((p, "F" if c["F"] > c["M"] else "M", c["F"] + c["M"]) for p, c in cont.items()),
                  key=lambda x: -x[2])


# --- Repertorio do narrador (config/repertorio_narrador.json, 16/10) -----------------
# Veio do estudo dos canais de referencia: 663 videos, 18,3 milhoes de palavras. O prompt antes
# trazia uma lista FIXA de piadas prontas, e o modelo repetia as mesmas em todo capitulo. Agora
# sorteia MOLDES (com variavel) e nao repete os dos dois capitulos anteriores da mesma obra.
_REPERTORIO = None
_REP_USADO = PROJECT_DIR / "logs" / "repertorio_usado.json"


def _carregar_repertorio():
    global _REPERTORIO
    if _REPERTORIO is not None:
        return _REPERTORIO
    p = PROJECT_DIR / "config" / "repertorio_narrador.json"
    try:
        _REPERTORIO = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _REPERTORIO = {}
    return _REPERTORIO


def _obra_chave(titulo):
    """'The Inheritor — Capítulo 16' -> 'The Inheritor'. Até 18/10 o estado era gravado com o título do capítulo,
    a chave mudava a cada capítulo e o 'não repetir dos 2 anteriores' nunca bloqueava nada."""
    return re.split(r"\s+[—–-]\s+Cap[íi]tulo\b", titulo or "", flags=re.I)[0].strip() or (titulo or "")


def _sortear_repertorio(obra, quantos=3):
    """(texto pro prompt, ids sorteados) — moldes de piada que nao sairam nos 2 capitulos anteriores."""
    moldes = _carregar_repertorio().get("moldes_piada") or []
    if not moldes:
        return "", []
    try:
        estado = json.loads(_REP_USADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        estado = {}
    bloqueados = set((estado.get(_obra_chave(obra)) or {}).get("ultimos_moldes") or [])
    urna = [m for m in moldes if m.get("id") not in bloqueados] or list(moldes)
    random.shuffle(urna)
    escolhidos = urna[:quantos]
    linhas = []
    for m in escolhidos:
        travas = "; ".join(m.get("travas") or [])
        linhas.append('  * %s | MOLDE: %s | como o nicho faz: "%s"%s'
                      % (m.get("nome", ""), m.get("molde", ""), m.get("exemplo_real", ""),
                         (" | NUNCA: " + travas) if travas else ""))
    return "\n".join(linhas), [m.get("id") for m in escolhidos if m.get("id")]


def _mais_usados(secao, campo, limite):
    """Entradas de um bloco tema -> lista do repertório, das mais usadas pras menos."""
    itens = []
    for tema, lista in (secao or {}).items():
        if tema.startswith("_") or not isinstance(lista, list):
            continue
        for t in lista:
            if isinstance(t, dict) and t.get(campo):
                itens.append((t.get("ocorrencias") or 0, t[campo]))
    itens.sort(reverse=True)
    return [t for _n, t in itens[:limite]]


def _vocabulario_do_nicho(limite=18):
    """Jargão, apelidos e o que NÃO falar — tudo com contagem real por trás (ver o JSON)."""
    rep = _carregar_repertorio()
    linhas = []
    jarg = _mais_usados(rep.get("jargao"), "termo", limite)
    if jarg:
        linhas.append("- MOLDES DE JARGÃO do nicho (encaixe quando a cena pedir): " + " | ".join(jarg) + ".")
    apel = _mais_usados(rep.get("apelidos"), "apelido", 12)
    if apel:
        linhas.append("- APELIDOS que o público usa (medidos nos canais): " + ", ".join(apel) + ".")
    evitar = [n["item"] for n in (rep.get("nao_usar") or [])
              if isinstance(n, dict) and n.get("item")]
    if evitar:
        linhas.append("- NÃO use nada disto (o público não fala assim): " + ", ".join(evitar) + ".")
    return ("\n".join(linhas) + "\n") if linhas else ""


def _sortear_formula(secao, obra, chave, aceita):
    """(texto pro prompt, id) de 1 fórmula de abertura/fechamento do repertório (18/10) que não saiu
    nos 2 capítulos anteriores da obra."""
    formulas = [f for f in ((_carregar_repertorio().get(secao) or {}).get("formulas") or [])
                if isinstance(f, dict) and f.get("id") and aceita(f)]
    if not formulas:
        return "", None
    try:
        estado = json.loads(_REP_USADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        estado = {}
    bloqueados = set((estado.get(_obra_chave(obra)) or {}).get(chave) or [])
    f = random.choice([f for f in formulas if f["id"] not in bloqueados] or formulas)
    return f'{f.get("molde", "")} (como o nicho faz: "{f.get("exemplo_real", "")}")', f["id"]


def _proibido_roteiro_automatico():
    """Linha do PROIBIDO com as marcas de roteiro automático medidas nos canais sem personalidade."""
    itens = [i["item"] for i in ((_carregar_repertorio().get("roteiro_automatico_proibido") or {}).get("itens") or [])
             if isinstance(i, dict) and i.get("item")]
    return ("- Cara de roteiro automático (o que os canais sem personalidade fazem): " + "; ".join(itens) + ".\n"
            if itens else "")


def _gravar_repertorio_usado(obra, ids, abertura=None, fechamento=None, cta=None):
    """Fecha o capitulo guardando os moldes (janela dos 2 ultimos) e a abertura/fechamento/CTA usados."""
    if not (ids or abertura or fechamento or cta):
        return
    try:
        estado = json.loads(_REP_USADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        estado = {}
    atual = estado.setdefault(_obra_chave(obra), {})
    if ids:
        atual["ultimos_moldes"] = (list(ids) + (atual.get("ultimos_moldes") or []))[:6]
    for chave, fid in (("ultimas_aberturas", abertura), ("ultimos_fechamentos", fechamento), ("ultimos_ctas", cta)):
        if fid:
            atual[chave] = ([fid] + (atual.get(chave) or []))[:2]
    try:
        _REP_USADO.parent.mkdir(parents=True, exist_ok=True)
        _REP_USADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


_CTA_PALAVRA = re.compile(r"\b(like|curt[ei]|inscrev|inscri[cç]|coment)", re.I)


def gerar_cta_fim(recap, titulo):
    """Pedido de like/comentário falado que vai DEPOIS do capítulo pronto (fim do vertical e fim do compilado),
    nunca dentro da narração: o capítulo entra inteiro no compilado e o pedido se repetiria a cada ~5 min.
    Fica em recap["_cta_fim"] pro re-render e o compilado usarem o mesmo texto (e a mesma voz em cache).
    {"id", "texto"} ou None."""
    if (recap.get("_cta_fim") or {}).get("texto"):
        return recap["_cta_fim"]
    formula, fid = _sortear_formula("fechamentos", titulo, "ultimos_ctas",
                                    lambda f: f.get("onde") == "fim_do_video" and not f.get("promessa"))
    if not formula:
        return None
    locs = recap.get("locucoes") or []
    fim = " / ".join(f"{l.get('persona', '')}: {l.get('text', '')}" for l in locs[-4:])
    cenas = " / ".join((recap.get("descriptions") or [])[-3:])
    pedido = ("O capítulo de um recap de manhwa acabou de terminar no gancho. Escreva a fala do NARRADOR que vem "
              f"logo depois, pedindo like, inscrição ou comentário com humor, neste jeito: {formula}.\n"
              f"Últimas falas do capítulo: {fim}\nÚltimas cenas: {cenas}\n"
              "Regras: 1 ou 2 frases, 12 a 35 palavras, português falado ('tá', 'pra'); amarre no que ACONTECEU na "
              "história ou na situação do prota (enrascada, plano, segredo, vilão) — NUNCA em corpo, roupa, toque, "
              "provocação ou clima de pegação, nem com duplo sentido (o canal levou advertência por isso); não "
              "prometa nada que dependa de like (a próxima parte sai de qualquer jeito); sem palavrão; não repita a "
              'fala do gancho. Devolva SÓ JSON {"texto": "..."}.')
    try:
        txt = gemini_llm.generate_text(pedido, system="Você é narrador(a) brasileiro(a) de canal de recap de manhwa.",
                                       max_tokens=512, temperature=0.9, max_attempts=3)
        texto = str(json.loads(re.sub(r"^```json\s*|\s*```$", "", (txt or "").strip())).get("texto") or "").strip()
    except (ValueError, TypeError, AttributeError):
        texto = ""
    if not (8 <= len(texto.split()) <= 45 and _CTA_PALAVRA.search(texto)):
        log(f"  [!] CTA do fim: a IA não devolveu uma fala válida ({texto[:80]!r}) — vídeo sem ele")
        return None
    texto = _sanitizar_narrador([{"persona": "Narrador", "text": texto}])[0]["text"]
    recap["_cta_fim"] = {"id": fid, "texto": texto}
    _gravar_repertorio_usado(titulo, [], cta=fid)
    log(f"  CTA do fim ({fid}): {texto}")
    return recap["_cta_fim"]


def gerar_recap(titulo, panel_paths, narrator_gender="F", conhecidos=None):
    """Gera narração: Gemini descreve painéis -> Gemini narra com base nas descrições.
    conhecidos: personagens_anteriores() da obra — nomes/gêneros que o roteiro deve reaproveitar."""
    n_paineis = len(panel_paths)
    ng = "M" if (narrator_gender or "F").upper() == "M" else "F"
    npapel = "narrador" if ng == "M" else "narradora"
    moldes_txt, moldes_ids = _sortear_repertorio(titulo, quantos=8)
    vocab_txt = _vocabulario_do_nicho()
    abertura_txt, abertura_id = _sortear_formula("aberturas", titulo, "ultimas_aberturas",
                                                 lambda f: f.get("no_capitulo", True))
    fechamento_txt, fechamento_id = _sortear_formula("fechamentos", titulo, "ultimos_fechamentos",
                                                     lambda f: f.get("onde") == "fala_final")

    # Passo 1: Descrever painéis com Gemini Vision (proxy do Claude está fora)
    log(f"  Descrevendo {n_paineis} painéis via Gemini Vision...")
    descriptions = _descrever_paineis_claude(panel_paths)

    system = (
        f"Voce e um(a) {npapel} brasileiro(a) de canal de recap de manhwa/webtoon. Você CONTA A HISTÓRIA "
        "pra quem nunca leu, como quem assiste junto com um amigo: fatos concretos da cena + opinião rápida.\n\n"
        "COMO OS MAIORES CANAIS BR DO NICHO NARRAM (medido em 332 vídeos, 10M de palavras):\n"
        "- Recontam no PRESENTE, encadeando fatos: quem faz o quê, com quem e por quê. "
        "Toda locução do narrador traz PELO MENOS UM fato da trama.\n"
        "- Conversa comum → DISCURSO INDIRETO. Moldes que mais aparecem (use e varie): "
        "'fala que', 'pergunta se ele realmente...', 'fala que pelo visto...', 'diz que tá tudo...', "
        "'fala para ele parar', 'nosso garoto fala/diz', 'dizendo que'. "
        "Sempre encaixe o contexto que o balão não dá.\n"
        "- Conectivos que dão ritmo (por frequência): porém (nº1, o preferido), então, aí, nisso, "
        "só que, de repente, até que. Combos: 'porém de repente', 'porém bem nessa hora', "
        "'porém nosso garoto'.\n"
        "- Apelido no lugar do nome genérico: escolha um da lista medida mais abaixo, pelo tom da "
        "cena, e MANTENHA o mesmo apelido pro mesmo personagem o capítulo inteiro.\n"
        "- Reação curta DENTRO da frase com o fato, nunca sozinha: rapaz (2,3/mil — a principal), "
        "rapaz do céu, meu deus do céu, pelo amor de deus, que isso, caramba, nossa. "
        "Use no máx 2-3 por capítulo e varie.\n"
        "- HUMOR E OPINIÃO: o público ama quando o narrador opina rápido como se estivesse assistindo junto. "
        "Exemplos reais: 'pelo amor de deus, eu taco o gamer do cara', 'esse cara não aprende', "
        "'eu no lugar dele já tinha corrido', 'nome desgraçado', 'fica meio sem graça', "
        "'o maluco deitou', 'F pro cara', '...e o trouxa já tá machucado, filho'. "
        "Solte 8 a 12 por capítulo, sempre grudadas no fato, nunca como frase solta. O dono pediu o "
        "MÁXIMO em 16/10: os canais que a gente copia temperam quase toda locução. Os exemplos acima "
        "mostram o ESTILO: crie as suas pra cena; no máximo 1 delas literal por capítulo.\n"
        "- **TEMPERO CONSTANTE (ordem do dono, 16/10).** Os canais de referência não guardam o jeitão "
        "pra uma piada de vez em quando: eles temperam o tempo todo. Em TODA locução do narrador que "
        "der, use pelo menos UM destes três: o APELIDO no lugar do nome, um MOLDE DE JARGÃO do nicho, "
        "ou a REAÇÃO curta dentro da frase do fato. Isso não conta como piada — é o jeito de falar. "
        "A piada montada continua à parte, 8 a 12 por capítulo.\n"
        + (f"- MOLDES DE PIADA SORTEADOS PRA ESTE CAPÍTULO (use 1 a 2, encaixando na cena; NÃO copie "
           f"o exemplo, ele só mostra a forma; use 8 a 12 piadas no capítulo, espalhadas):\n"
           f"{moldes_txt}\n" if moldes_txt else "")
        + vocab_txt +
        "- Bordões que dão naturalidade (use sem forçar): 'dá uma olhada', 'toma um susto', "
        "'cai no chão', 'olha para trás', 'pra todo lado', 'abre a porta', "
        "'no final das contas', 'há muito tempo'.\n"
        "- Fale com o espectador: 'cara' (muito frequente), 'imagina só', 'você', "
        "'percebe', 'tá ligado'. Tom de conversa, sem exagerar.\n"
        "- Tom informal natural: prefira 'tá' a 'está', 'pro' a 'para o', 'pra' a 'para', "
        "'num' a 'em um'. Fale como brasileiro fala, não como escreve.\n\n"
        "QUEM FALA O QUÊ (ordem do dono, 16/10, depois de ver o vídeo pronto):\n"
        "- **Balão de fala é do PERSONAGEM, sempre.** Se o painel tem balão, a locução é da pessoa "
        "que fala, com o texto do balão quase literal — só ajuste o mínimo pra soar natural falado "
        "em pt-BR. Várias falas do MESMO personagem no painel viram uma locução dele só.\n"
        "- **O narrador tem o trabalho dele**, que não é repetir fala: dar o contexto que o balão "
        "não dá, emendar as cenas, soltar a piada, usar o jargão do nicho e comentar como quem "
        "assiste junto. É o que ele já faz bem — só não pode tomar o lugar dos personagens.\n"
        "- O narrador fica com o painel quando: NÃO há balão; só há caixa de narração; as falas são "
        "de pessoas DIFERENTES no mesmo painel (ele conta e cita a mais marcante); ou o balão é só "
        "gemido, grito ou onomatopeia.\n"
        "- **Nunca comece o capítulo com mais de 2 locuções seguidas de narrador.** No cap 2 as 8 "
        "primeiras eram todas dele e a primeira voz de personagem só apareceu no 9º painel — o "
        "público desiste antes de conhecer os personagens.\n"
        "- Na dúvida entre narrador e personagem, é PERSONAGEM.\n"
        "- **Fala curta precisa de corpo, e não pode COMEÇAR pela palavra principal.** A voz entra "
        "sem embalo e erra a primeira palavra da locução: 'Herança?!' sai torto, 'Como assim, "
        "herança?' sai certo (testado em 3 vozes em 16/10). Então balão de 1 a 3 palavras vira uma "
        "fala inteira, com uma abertura curta e natural ANTES da palavra que importa: 'Espera, do "
        "meu pai?', 'Como assim, herança?', 'Peraí, o que você disse?'. Continua sendo a fala dele, "
        "só que falada como gente fala.\n"
        "- Palavra simples e sozinha ('Sim.', 'Obrigada.', 'Vamos!') pode ficar como está: o "
        "problema é só com palavra comprida ou de som difícil no começo.\n\n"
        "NENHUMA FALA PODE SUMIR (regra do dono, 16/10):\n"
        "- A locução do painel tem de cobrir TODO o texto que a leitura transcreveu dele. Painel com "
        "três caixas de narração e dois balões vira UMA locução que encadeia os cinco, em ordem — não "
        "escolha um e descarte o resto.\n"
        "- NOME PRÓPRIO que aparece no texto tem de ser dito na locução daquele painel. É assim que o "
        "público aprende quem é quem; sem isso a história fica com buraco pra quem leu a obra.\n"
        "- Fala pesada demais pro YouTube (sexo explícito, palavrão forte): NÃO pule — diga o mesmo com "
        "as palavras seguras da lista de troca, ou, se nem assim der, o narrador CONTA o que está "
        "acontecendo ali ('ela diz uma coisa que ele não esperava ouvir'). O espectador tem de "
        "entender a cena de qualquer jeito.\n"
        "- Só pode ficar de fora o que não é fala da história: onomatopeia desenhada, número de "
        "página, e TUDO que seja do site que digitalizou (nome do scan, endereço, 'leia em', "
        "acesso antecipado, Discord, Patreon, crédito de tradução). Essa parte é PROIBIDA na "
        "narração: é propaganda de terceiro dentro do nosso vídeo. Se o painel só tiver isso, o "
        "narrador conta o que se vê na arte.\n\n"
        "QUEM FALA EM CADA PAINEL (uma locução por painel):\n"
        "- Balão com fala marcante e curta (revelação, ameaça, confissão, piada; até ~15 palavras): o PERSONAGEM "
        "fala, com o texto do balão quase literal (só ajuste pra soar natural em pt-BR), sem suavizar palavras "
        "fortes (escrava, matar, palavrão ficam).\n"
        "- Balão de conversa comum: continua sendo o PERSONAGEM falando. Só vira resumo do narrador quando o balão é explicação longa demais pra caber em 25 palavras.\n"
        "- Balão só com gemido, grito, onomatopeia, reticências ou '?' (ex.: 'Hnngh', 'Haa', 'UGH', '...!!!', "
        "'?'): o NARRADOR conta o que está acontecendo. Isso NUNCA vai na boca do personagem.\n"
        "- CAIXA DE NARRAÇÃO retangular (ou pensamento): é a voz de dentro da história — vai pro "
        "NARRADOR, com o conteúdo inteiro, inclusive nomes. Não vire isso em descrição vaga.\n"
        "- Painel sem texto nenhum: narrador conta o que se vê e por que importa.\n"
        "- 'alguém fora do quadro diz' = a fala é de quem conversa com o personagem visível, não dele.\n"
        "- NUNCA use 'Personagem' como nome — use nomes reais (ex: Min-Hyuk, Yeol-Mae, Chef).\n\n"
        "PROIBIDO (é enchimento e o público percebe):\n"
        "- Frase que serviria pra qualquer cena: 'dá pra cortar o clima com uma faca', 'vocês não estão prontos', "
        "'o pior ainda tá por vir', 'o silêncio tá gritando', 'a tensão subiu pra cem por cento', "
        "'as coisas vão ficar feias'.\n"
        "- Repetir a mesma interjeição ou o mesmo molde de frase mais de 2 vezes no capítulo.\n"
        "- Abrir com 'olá', 'salve' ou 'galera'.\n"
        "- Narrador descrevendo aparência física ('ela é linda', 'ele é musculoso').\n"
        + _proibido_roteiro_automatico() +
        "\nCOMEÇO E FIM:\n"
        "- Locução 1 (narrador): situa quem chegou agora em 1-2 frases (quem é o protagonista e em que situação "
        "ele está) e já entra na cena. Pode usar premissa ('imagina só, um cara que...').\n"
        + (f"  FÓRMULA DE ABERTURA SORTEADA PRA ESTE CAPÍTULO (use a forma, não copie o exemplo): {abertura_txt}. "
           + ("É o 1º capítulo da obra: pode contar a premissa desde o começo.\n" if not conhecidos else
              "Não é o 1º capítulo: a fórmula situa o ponto ATUAL da história, sem recontar do começo.\n")
           if abertura_txt else "") +
        "- Última locução: cliffhanger + especulação concreta sobre o que vem ('será que...', "
        "'o problema é que...').\n"
        + (f"  JEITO DE FECHAR SORTEADO PRA ESTE CAPÍTULO (use a forma, não copie o exemplo; termine SEMPRE com "
           f"pergunta ou especulação): {fechamento_txt}.\n" if fechamento_txt else "") +
        "- Nada de pedir like, inscrição ou comentário na fala: o fim do vídeo já mostra isso na tela, e o "
        "capítulo entra inteiro no compilado (o pedido se repetiria a cada capítulo).\n\n"
        "EXEMPLOS (cena inventada, só pra mostrar o molde — não copie as frases):\n"
        '  ❌ {"persona": "Narrador", "gender": "F", "text": "Caramba, o clima ficou pesado demais agora!"}\n'
        '  ✅ {"persona": "Narrador", "gender": "F", "text": "Nisso, o guarda pergunta se ele tem passe da '
        'guilda, só que o nosso garoto entrou escondido e não tem passe nenhum."}\n'
        '  ✅ {"persona": "Kang Dae", "gender": "M", "text": "Fui eu que destruí o portão."}\n'
        '  ✅ {"persona": "Narrador", "gender": "F", "text": "Rapaz do céu, o cara acabou de confessar pro chefe '
        'da guarda. Pelo amor de deus, eu no lugar dele já tava correndo."}\n'
        '  ✅ {"persona": "Narrador", "gender": "F", "text": "Porém de repente o velhote dá uma olhada pro '
        'lado e toma um susto — a moça tá ali parada ouvindo tudo."}\n\n'
        "Locução do narrador: 1-2 frases (10-28 palavras). Evite palavras que geram demonetização na voz do "
        "narrador (morte→'fim', sangue→'vermelho', arma→'lâmina', escravo→'servo', suicídio→'ato extremo'); "
        "falas de personagem ficam como estão.\n"
        "Tom: envolvente, com humor natural e personalidade. Foque nas EMOÇÕES, MOTIVOS e RELAÇÕES entre "
        "personagens, não descreva aparência física.\n\n"
        "Saida JSON estrita (sem markdown, sem ```json):\n"
        '{\n'
        '  "titulo_video": "...",\n'
        '  "tags": ["...", "..."],\n'
        '  "locucoes": [\n'
        '    {"painel": 1, "persona": "Narrador", "gender": "F", "text": "..."},\n'
        '    {"painel": 2, "persona": "Min-Hyuk", "gender": "M", "text": "..."}\n'
        '  ]\n'
        '}\n'
        f"TOTAL de locucoes DEVE ser EXATAMENTE {n_paineis} (uma por painel)."
    )

    if descriptions:
        # Com descrições visuais reais
        log(f"  [OK] Descreveu {len(descriptions)} painéis")
        for i, d in enumerate(descriptions[:3]):
            log(f"    {i+1}: {d[:60]}")
        desc_text = "\n".join(f"Painel {i+1}: {d}" for i, d in enumerate(descriptions))
        ficha = ""
        if conhecidos:
            ficha = ("Personagens já conhecidos desta obra (capítulos anteriores): "
                     + ", ".join(f"{p} ({g}, {n} falas)" for p, g, n in conhecidos[:12])
                     + ". Quando a cena mostrar um deles, use EXATAMENTE esse nome e gênero (o protagonista "
                       "é o que mais fala; nada de 'Rapaz', 'Garota', 'Homem' ou 'Mulher' pra quem já tem nome). "
                       "Personagem novo sem nome no balão: dê um apelido curto e mantenha o mesmo nas "
                       "próximas falas.\n\n")
        user = (
            f"Manhwa: {titulo}\n\n"
            f"{ficha}"
            f"Descrições visuais dos {n_paineis} painéis:\n{desc_text}\n\n"
            f"IMPORTANTE: Narre baseado APENAS no que está descrito em cada painel. "
            f"Não invente cenas que não estão nas descrições. "
            f"Gere a narração dramática para CADA painel."
        )
    else:
        # Narração cega (fallback — não deveria chegar aqui)
        log(f"  [!] Visão indisponível — narração sequencial sem visão")
        user = (
            f"Manhwa: {titulo}\n"
            f"Numero de paineis: {n_paineis}\n\n"
            f"Gere {n_paineis} locucoes pra recap de manhwa. "
            f"Conte uma história envolvente que evolui painel a painel. "
            f"Comece com gancho forte, desenvolva tensão no meio, "
            f"termine com cliffhanger pro próximo capítulo. "
            f"Misture narradora com falas de personagens."
        )

    # Sistema de retry com censura progressiva
    # Se o Claude recusar (resposta sem JSON), sanitiza mais e tenta de novo
    CENSURA_LEVELS = [
        # Nível 0: sanitização base (remove nudez/sexo explícito das descrições)
        r"(?i)(nu[da]?\b|nua?\b|pelad[oa]\w*|sem\s*roupa|corpo\s*expost\w*|seio\w*|peito\w*\s*expost|banheiro|chuveiro|toalha\s*enrolad|lingerie|calcinha|sutiã|cueca|underwear|naked|nude|shower|bath|towel\s*only|breast|undress)",
        # Nível 1: substituir termos provocativos
        r"(?i)(provocan\w*|insinua\w*|tent\w*\s*seduz|seduz\w*|sedu[çc]\w*|voluptu\w*|íntim\w*|intimid\w*|corpo\s*expost|roupa\s*(curt|apert)|decot|mini.?saia|sensual\w*|erótic\w*|excitad\w*)",
        # Nível 2: genérico total — substituir qualquer menção de aparência
        r"(?i)(bonit\w*|atraent\w*|linda|gata|gostosa|tesão|hot|quente|sexy|charm\w*|encant\w*|magnífic\w*|deslumbrant\w*|corpo\w*|curva\w*|perna\w*|cintura|quadril)",
        # (não há mais nível "sem descrições": inventava história com personagens de outra obra;
        # melhor falhar e a fila tentar de novo depois)
    ]

    for level in range(len(CENSURA_LEVELS)):
        sanitized_user = user
        if CENSURA_LEVELS[level]:
            # fala transcrita (entre aspas) fica intacta, menos no último nível: "Vou pro banheiro"
            # virava "Vou pro personagem" no vídeo
            if level < len(CENSURA_LEVELS) - 1:
                partes = _ASPAS.split(sanitized_user)
                sanitized_user = "".join(p if k % 2 else re.sub(CENSURA_LEVELS[level], "personagem", p)
                                         for k, p in enumerate(partes))
            else:
                sanitized_user = re.sub(CENSURA_LEVELS[level], "personagem", sanitized_user)
            if level > 0:
                log(f"  [!] Retry nível {level} de censura...")

        log(f"  Chamando Gemini pra {n_paineis} locuções...")
        text = gemini_llm.generate_text(
            sanitized_user, system=system, max_tokens=8192, temperature=1.0, max_attempts=6)
        if not text:
            text = _claude_proxy(sanitized_user, system=system, max_tokens=8192)

        if not text:
            if level < len(CENSURA_LEVELS) - 1:
                log(f"  [X] Nível {level}: Gemini não retornou narração, próximo nível...")
                continue
            else:
                log(f"  [X] Gemini não retornou narração após {len(CENSURA_LEVELS)} tentativas")
                return None

        text = text.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        try:
            data = json.loads(text)
            # Sucesso!
            break
        except json.JSONDecodeError as e:
            if level < len(CENSURA_LEVELS) - 1:
                log(f"  [X] Nível {level} falhou (recusa ou JSON inválido), tentando próximo nível...")
                continue
            else:
                log(f"  [X] JSON inválido do Gemini após {len(CENSURA_LEVELS)} tentativas: {e}")
                log(f"  Resposta: {text[:500]}")
                return None

    locucoes = data.get("locucoes", [])
    if len(locucoes) != n_paineis:
        log(f"  [!] Claude gerou {len(locucoes)} locuções, esperava {n_paineis}. Ajustando...")
        while len(locucoes) < n_paineis:
            locucoes.append({"persona": "Narrador", "gender": "F",
                            "text": "E a história continua..."})
        locucoes = locucoes[:n_paineis]
        data["locucoes"] = locucoes

    _sons_para_narrador(locucoes, descriptions, npapel, ng)
    # 16/10: estas três estavam escritas e NUNCA eram chamadas — o narrador seguia dublando o
    # desenho (29% das falas do cap 10), o balão partido seguia virando 4 clips de 1,87 s e o
    # bordão seguia repetindo 7 vezes no mesmo capítulo.
    _limpar_anotacoes(locucoes)       # "(sorriso)" fora do texto que vai pro TTS
    _juntar_balao_partido(locucoes)   # balão continuado vira UMA fala
    _abertura_e_fim(locucoes, descriptions, npapel, ng, conhecidos, titulo, abertura_txt, fechamento_txt)
    _reescrever_narrador_fraco(locucoes, descriptions, npapel, ng)  # depois da abertura, pra não refazê-la
    _completar_falas_perdidas(locucoes, descriptions, npapel, ng)  # nenhuma fala do manhwa some
    _dar_corpo_as_falas_curtas(locucoes, descriptions, npapel, ng)  # a voz erra a 1ª palavra da fala
    _gravar_repertorio_usado(titulo, moldes_ids, abertura_id, fechamento_id)  # o próximo capítulo sorteia outros
    # Antes havia um "forçar 30% de personagens" que dava fala do narrador a nomes sorteados de outra
    # obra (gênero aleatório = voz trocada). Agora só avisa.
    n_pers = sum(1 for l in locucoes if l.get("persona", "").lower() not in ("narrador", "narradora"))
    log(f"  [{'OK' if n_pers >= n_paineis * 0.3 else '!'}] {n_pers} locuções de personagens "
        f"({n_pers * 100 // max(1, n_paineis)}%)")

    _sanitizar_narrador(locucoes)

    # Salvar descrições visuais no recap (usadas pra detectar impacto/shake/sfx)
    if descriptions:
        data["descriptions"] = descriptions[:n_paineis]

    return data




def _revisar_coerencia(locucoes, titulo):
    """Revisão de coerência: ajusta as locuções do narrador para fluírem como história contínua.

    Pega APENAS as locuções do narrador, envia pro LLM pedindo pequenos ajustes de
    conexão (sem mudar o conteúdo), e substitui de volta na lista original.
    Mantém locuções de personagens intactas.
    """
    narrator_indices = []
    narrator_texts = []
    for i, loc in enumerate(locucoes):
        p = loc.get("persona", "").strip().lower()
        if p in ("narrador", "narradora"):
            narrator_indices.append(i)
            narrator_texts.append(loc.get("text", ""))

    if len(narrator_texts) < 5:
        return locucoes  # Muito poucas, não vale a pena

    # Montar o texto numerado para revisão
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(narrator_texts))

    system = (
        "Você é um revisor de roteiro de narração para vídeos de recap de manhwa. "
        "Recebeu as falas do narrador numeradas. Sua tarefa é fazer PEQUENOS ajustes "
        "para que fluam como uma história contínua e coesa. Regras:\n"
        "- NÃO mude o conteúdo/significado das falas.\n"
        "- Apenas ajuste conectores, transições e referências entre frases consecutivas.\n"
        "- Mantenha o tom dramático e envolvente.\n"
        "- Mantenha o tamanho similar (8-25 palavras por fala).\n"
        "- Retorne APENAS as falas numeradas revisadas no mesmo formato (1. texto\\n2. texto...).\n"
        "- NÃO adicione nem remova falas. O total DEVE ser o mesmo."
    )
    user = (
        f"Manhwa: {titulo}\n\n"
        f"Falas do narrador ({len(narrator_texts)} no total):\n{numbered}\n\n"
        "Revise para coerência e fluidez entre uma fala e outra. Responda APENAS as falas numeradas."
    )

    log("  Revisando coerência narrativa...")
    result = gemini_llm.generate_text(user, system=system, max_tokens=4096, temperature=0.5)

    if not result:
        log("  [!] Revisão de coerência falhou, mantendo original")
        return locucoes

    # Parse do resultado — espera formato "1. texto\n2. texto\n..."
    revised_lines = []
    for line in result.strip().splitlines():
        line = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
        if line:
            revised_lines.append(line)

    if len(revised_lines) != len(narrator_texts):
        log(f"  [!] Revisão retornou {len(revised_lines)} falas (esperava {len(narrator_texts)}), mantendo original")
        return locucoes

    # Substituir apenas as locuções do narrador revisadas
    for idx, new_text in zip(narrator_indices, revised_lines):
        locucoes[idx]["text"] = new_text

    log(f"  [OK] Coerência revisada ({len(revised_lines)} falas do narrador ajustadas)")
    return locucoes

