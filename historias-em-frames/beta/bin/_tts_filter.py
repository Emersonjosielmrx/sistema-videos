"""_tts_filter.py — Limpa texto antes do TTS pra não falar código/símbolos.

Problema: o `say` do macOS lê LITERALMENTE coisas como:
  - "asterisco asterisco Locu ção asterisco asterisco dois pontos"
  - "barra barra arroba sa  três menos"
  - URLs lidas char-by-char
  - Trechos de código (curly braces, parênteses, ponto-vírgula)

Solução: passe todo chunk pelo `clean_for_tts(text)` antes de mandar pro `say`.

Estratégia:
  1. Detecta linhas que CLARAMENTE são código (ffmpeg/curl/import/{/[/=>/;) e DESCARTA.
  2. Strip de markdown (**, _, `, #, >, etc).
  3. URLs → "link" ou descarta completamente.
  4. Substitui símbolos comuns por palavras pronunciáveis ou espaço.
  5. Colapsa whitespace e remove pontuação repetida.
"""
import os
import re

# Linhas que provavelmente são código (qualquer uma dessas pistas e a linha é descartada)
CODE_LINE_HINTS = (
    re.compile(r"^\s*(ffmpeg|curl|docker|sudo|brew|pip3?|npm|yarn|git|cd|ls|cat|echo|grep|sed|awk|chmod|python3?|node)\s"),
    # palavra-chave + cara de código na mesma linha. Só a palavra-chave descartava narração inteira que começava com
    # "if", "for", "return", "class"... ("return para casa era o plano dele" sumia)
    re.compile(r"^\s*(import|from|const|let|var|function|def|class|return|if|else|while|for|try|catch|except|async|await)\s"
               r"(?:(?=.*(?:[=(){}\[\]<>;]|:\s*$))|(?=\S+(?:\s+\S+)?\s*$))"),   # ...ou linha de até 3 palavras
    re.compile(r"^\s*[#/]{2,}"),                          # comentários // ou ## etc
    # começa com tag/bracket — menos "[Missão concluída] Recompensa: ..." (janela de sistema de manhwa: é narração;
    # os colchetes saem depois e o texto fica)
    re.compile(r"^\s*(?:[<>{}]|\[(?![A-Za-zÀ-ÿ][^\]\n]{0,60}\]\s*\S)|\](?!\S))"),
    re.compile(r".+=>.+"),                                # arrow function
    re.compile(r".+;\s*$"),                               # termina com ;
    re.compile(r".+\{\s*$"),                              # bloco abrindo
    re.compile(r"^\s*['\"].*['\"]\s*:\s*"),               # chave JSON
)

# Substituições de símbolos → palavra/espaço
SYMBOL_MAP = {
    "&":  " e ",
    "@":  " arroba ",
    "%":  " por cento ",
    "#":  " ",
    "$":  " ",
    "*":  " ",
    "_":  " ",
    "~":  " ",
    "^":  " ",
    "|":  " ",
    "\\": " ",
    "/":  " ",
    "`":  " ",
    "<":  " ",
    ">":  " ",
    "{":  " ",
    "}":  " ",
    "[":  " ",
    "]":  " ",
    "=":  " ",
    "+":  " mais ",
    "©":  " ",
    "®":  " ",
    "™":  " ",
    "→":  " para ",
    "←":  " ",
    "↑":  " ",
    "↓":  " ",
    "•":  " ",
    "·":  " ",
    "—":  " — ",  # mantém em-dash (say faz pausa)
    "–":  " — ",
}

# Tokens que NÃO devem ser pronunciados (jogados fora)
DISCARD_TOKENS = (
    re.compile(r"https?://\S+"),                          # URLs
    re.compile(r"www\.\S+"),
    re.compile(r"\S+@\S+\.\S+"),                          # emails
    re.compile(r"[a-zA-Z0-9_-]{20,}"),                    # tokens/IDs longos
    # hex (id/hash): exige letra E dígito — antes "10000000 de wons" (só dígitos) também sumia
    re.compile(r"\b(?=[A-F0-9]*[A-F])(?=[A-F0-9]*\d)[A-F0-9]{8,}\b"),
    re.compile(r"\$\{[^}]+\}"),                           # ${VAR}
    re.compile(r"\{\{[^}]+\}\}"),                         # {{var}}
)

# Diretivas visuais/sonoras que aparecem em roteiros entre () ou [] e NÃO
# devem ser lidas pelo TTS (ex.: "(zoom in)", "[CORTE]", "(b-roll: laptop)",
# "(música tensa)", "[INSERT B-ROLL HERE]"). Lista de palavras-chave: se
# QUALQUER uma aparecer dentro dos delimitadores, o bloco inteiro é
# descartado. Conservador: NÃO remove "(99% precisão)" ou "(empresa X)".
_DIRECTIVE_KEYWORDS = (
    r"zoom\s*in", r"zoom\s*out", r"close[- ]?up", r"wide\s*shot",
    r"corte", r"cut", r"fade(?:\s*in|\s*out)?", r"dissolve",
    r"b[- ]?roll", r"broll", r"insert", r"overlay",
    r"texto\s+na\s+tela", r"legenda", r"caption",
    r"m[úu]sica", r"sfx", r"som\s+de", r"trilha",
    r"pausa\s+dram[áa]tica", r"silen?cio", r"beat",
    r"pan(?:\s+(?:left|right|esquerda|direita))?",
    r"tilt(?:\s+(?:up|down))?", r"slow[- ]?mo", r"slowmo",
)
_DIRECTIVE_INNER = r"(?:[^()\[\]]{0,80}?\b(?:" + "|".join(_DIRECTIVE_KEYWORDS) + r")\b[^()\[\]]{0,80}?)"
DIRECTIVE_BLOCKS = (
    re.compile(r"\(" + _DIRECTIVE_INNER + r"\)", re.IGNORECASE),
    re.compile(r"\[" + _DIRECTIVE_INNER + r"\]", re.IGNORECASE),
    # Blocos em CAIXA ALTA dentro de [] são quase sempre diretivas de roteiro
    re.compile(r"\[[A-Z][A-Z\s\-:]{2,}\]"),
)


# T2: tags de emoção do roteiro → canônico (porte do REGRAS_TAGS do n8n CENSOR CIRÚRGICO).
# edge-tts NÃO interpreta SSML de emoção, então a tag canônica é só SINAL INTERNO: normalizamos
# e depois o DIRECTIVE_BLOCKS remove do texto falado (opção (a) do doc). normalize_emotion_tags
# devolve (texto_normalizado, lista_de_emoções) — a lista fica disponível p/ futuro (SFX/trilha).
_EMOTION_TAGS = [
    (re.compile(r"\[[^\]]*(risada|rindo|risos)[^\]]*\]", re.IGNORECASE), "[RISO]"),
    (re.compile(r"\[[^\]]*(grit|berr)[^\]]*\]", re.IGNORECASE), "[GRITANDO]"),
    (re.compile(r"\[[^\]]*(chor)[^\]]*\]", re.IGNORECASE), "[CHORANDO]"),
    (re.compile(r"\[[^\]]*(sussurro|baixo)[^\]]*\]", re.IGNORECASE), "[SUSSURRO]"),
    (re.compile(r"\[[^\]]*(medo|assustado)[^\]]*\]", re.IGNORECASE), "[MEDO]"),
    (re.compile(r"\[[^\]]*(feliz|alegre)[^\]]*\]", re.IGNORECASE), "[FELIZ]"),
    (re.compile(r"\[[^\]]*(raiva|furioso)[^\]]*\]", re.IGNORECASE), "[RAIVA]"),
    (re.compile(r"\[[^\]]*(confuso|duvida)[^\]]*\]", re.IGNORECASE), "[CONFUSO]"),
    (re.compile(r"\[[^\]]*serio[^\]]*\]", re.IGNORECASE), "[SERIO]"),
    (re.compile(r"\[[^\]]*ironia[^\]]*\]", re.IGNORECASE), "[IRONICO]"),
    (re.compile(r"\[[^\]]*deboche[^\]]*\]", re.IGNORECASE), "[DEBOCHE]"),
    (re.compile(r"\[[^\]]*surpresa[^\]]*\]", re.IGNORECASE), "[SURPRESO]"),
]


def normalize_emotion_tags(text):
    """Colapsa variações de tag de emoção pro canônico. Retorna (texto, emocoes_detectadas)."""
    emocoes = []
    if not text:
        return text, emocoes
    for rgx, canon in _EMOTION_TAGS:
        if rgx.search(text):
            emocoes.append(canon.strip("[]"))
            text = rgx.sub(canon, text)
    return text, emocoes


def is_code_line(line):
    """True se a linha tem cheiro forte de código."""
    s = line.strip()
    if not s:
        return False
    for pat in CODE_LINE_HINTS:
        if pat.search(s):
            return True
    # Heurística de densidade: linhas com >25% caracteres não-alfanuméricos e
    # com pelo menos uns símbolos clássicos de código
    nonalpha = sum(1 for c in s if not c.isalnum() and not c.isspace() and c not in "áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ,.!?;:'\"-—()")
    if len(s) > 20 and nonalpha / len(s) > 0.25 and any(c in s for c in "{};=<>|&"):
        return True
    return False


# Portuguesify: substituições de pronúncia de termos estrangeiros/manhwa
# Edge-TTS em pt-BR lê nomes coreanos/japoneses/ingleses de forma estranha
PORTUGUESIFY_MAP = {
    # Nomes coreanos comuns (pronúncia fonetizada)
    "hyuk": "hiúque", "joon": "djun", "min-hyuk": "min-hiúque",
    "seung": "sung", "yeol": "iól", "na-yul": "na-iúl",
    "ji-woo": "dji-ú", "hye": "rrié", "jin": "djin",
    "oppa": "ôpa", "unnie": "uni", "noona": "nuna",
    "sunbae": "sunbé", "hoobae": "rubé",
    # Termos manhwa/anime
    "manhwa": "manrrua", "manga": "mangá", "anime": "animê",
    "isekai": "issekai", "otaku": "otácu", "sensei": "senssei",
    "senpai": "senpai", "chan": "tchan", "kun": "cun", "sama": "samá",
    # Inglês comum no texto
    "level up": "lévéu ap", "skill": "esquíu", "status": "stétus",
    "power": "páuer", "quest": "quést", "boss": "bóss",
    "hunter": "rânter", "dungeon": "dândjon", "rank": "rênque",
    "guild": "guíud", "party": "párti", "healer": "ríler",
    "tank": "tânque", "buff": "bâf", "nerf": "nârf",
    "the": "dê", "my": "mái",
    # Onomatopeias que TTS lê errado
    "kkk": "", "haha": "rá rá", "hehe": "ré ré",
    "hmm": "hum", "tsk": "tsc", "pfft": "",
}


def _portuguesify(text):
    """Substitui termos estrangeiros por versão fonética pt-BR."""
    for original, fonetizado in PORTUGUESIFY_MAP.items():
        text = re.sub(r'\b' + re.escape(original) + r'\b', fonetizado, text, flags=re.IGNORECASE)
    return text


_SIGLAS = frozenset(
    "NPC HP MP XP SP TV RPG PVP PVE PC CD DVD GPS DPS FPS MMR MMO MMORPG SS SSS SSR SR UR GM CG DJ MC KG KM CM MM ML GB "
    "MB TB HD SSD LED PDF SMS CPF CNPJ RG CLT PM PF BBB DF RJ SP MG RS SC PR CNH DNS PH PSG NBA NFL KPI CRM QR WC".split())


def _strip_onomatopoeia(text):
    """Remove onomatopeias/balbucio que o LLM às vezes transcreve dos balões como
    se fossem fala (ex: 'DING DONG', 'POP', 'BAAARF', 'SS SSP', 'AAA NNG', 'EUP').
    Conservador: só remove tokens que CLARAMENTE não são palavras pt-BR — caixa
    alta com estrutura não-silábica, consoantes repetidas, ou vogal esticada.
    Mantém siglas reais (até 3 letras maiúsculas isoladas viram contexto duvidoso,
    então só removemos quando o token tem o padrão de ruído)."""
    if not text:
        return text

    # lista explícita de onomatopeias comuns em manhwa (case-insensitive, palavra inteira)
    # Barulho que nunca é palavra nem nome: sai sempre. (?<![\w-]) / (?![\w-]): não corta pedaço de nome com hífen.
    SEMPRE = (r"ding[\s-]?dong|tlim|toc[\s-]?toc|bip|thump|thud|swoosh|whoosh|vrum|vroom|screech|"
              r"barf|baaa+rf|bleh|blergh|ugh+|argh+|grr+|hmph|tsk|achoo|atchim|burp|huff|zzz+|"
              r"nng+|eup|erp|urp|glup|nhe+|hng+|unf+|aff")
    text = re.sub(rf"(?<![\w-])({SEMPRE})(?![\w-])[!.,]*", " ", text, flags=re.IGNORECASE)
    # Estes também são PALAVRA ou NOME de personagem (Dong, Bang, Ann, Ang, Tum; "o boom", "um click", "um crash",
    # "K-pop"): antes saíam sempre e a narração/legenda ficava "Kang -su entrou", "Com um o portal abriu". Agora só
    # saem quando são claramente barulho de balão: em CAIXA ALTA ("BANG") ou seguidos de "!" ("Bang! A porta caiu").
    AMBIGUO = (r"dong|knock|slam|bang|boom|pow|pop|beep|tum|tec|click|clack|crash|splash|gulp|sniff|gasp|puff|hic|"
               r"ang|ann+|arg")

    def _barulho(m):
        tok = m.group(1)
        return " " if (len(tok) > 1 and tok.isupper()) or m.group(2).startswith("!") else m.group(0)
    text = re.sub(rf"(?<![\w-])({AMBIGUO})(?![\w-])([!.,]*)", _barulho, text, flags=re.IGNORECASE)

    def _is_noise(tok):
        core = re.sub(r"[^A-Za-zÀ-ÿ]", "", tok)
        if len(core) < 2:
            return False
        # sigla de verdade (sem vogal, em maiúscula) não é barulho: antes "O NPC entregou a missão" virava "O entregou
        # a missão", "caçador rank SSS" perdia o SSS, "O HP dele caiu e o MP zerou" virava "O dele caiu e o zerou"
        if core in _SIGLAS:
            return False
        # precisa estar majoritariamente em CAIXA ALTA pra ser candidato a ruído
        uppers = sum(1 for c in core if c.isupper())
        if uppers < len(core) * 0.8:
            return False
        low = core.lower()
        vowels = sum(1 for c in low if c in "aeiouáéíóúâêôãõ")
        # sem vogal nenhuma (SS, SSP, NNG, NRX, NGX) → ruído
        if vowels == 0:
            return True
        # vogal esticada (AAA, EEEE, OOOO) ou consoante esticada → ruído
        if re.search(r"(.)\1{2,}", low):
            return True
        # bloco de consoantes longo sem formar sílaba (SSP, BRF) → ruído
        if re.search(r"[bcdfghjklmnpqrstvwxyz]{3,}", low) and vowels <= 1 and len(core) <= 5:
            return True
        return False

    kept = []
    for tok in text.split():
        if _is_noise(tok):
            continue
        kept.append(tok)
    return " ".join(kept)


def clean_for_tts(text):
    """Recebe texto bruto (uma locução). Devolve texto limpo pronto pro `say`.
    Pode retornar string vazia se nada sobrou — caller deve pular esse chunk.
    """
    if not text:
        return ""

    # 1. Linha por linha — descarta linhas que parecem código
    kept = []
    for ln in text.splitlines():
        if is_code_line(ln):
            continue
        kept.append(ln)
    text = " ".join(kept)

    # 2. Remove markdown
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)        # bold
    text = re.sub(r"\*([^*]+)\*", r"\1", text)            # italic
    text = re.sub(r"`([^`]+)`", r"\1", text)              # inline code → conteúdo
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)  # headings
    text = re.sub(r"^\s*[->*•·]\s+", "", text, flags=re.MULTILINE)  # bullets

    # 3. Descarta tokens não-pronunciáveis (URLs/emails/IDs longos)
    for pat in DISCARD_TOKENS:
        text = pat.sub(" ", text)

    # 3b. Remove diretivas visuais/sonoras de roteiro (ex.: "(zoom in)",
    # "[CORTE]", "(b-roll: laptop)") que não fazem parte da locução.
    # T2: ANTES, normaliza tags de emoção pro canônico ([RISO]/[MEDO]...). Como ficam em
    # CAIXA ALTA dentro de [], o DIRECTIVE_BLOCKS abaixo as remove do texto FALADO (opção a).
    text, _emocoes = normalize_emotion_tags(text)
    for pat in DIRECTIVE_BLOCKS:
        text = pat.sub(" ", text)

    # 4. Substitui símbolos
    for sym, repl in SYMBOL_MAP.items():
        text = text.replace(sym, repl)

    # 5. Remove qualquer caractere que não seja letra/dígito/pontuação pt-BR/espaço
    text = re.sub(r"[^\w\sáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ,.!?;:'\"()\-—]", " ", text)

    # 5b. Portuguesify — pronúncia correta de nomes/termos estrangeiros comuns em manhwa
    text = _portuguesify(text)

    # 5c. Remove onomatopeias/balbucio que vazaram dos balões como "fala"
    text = _strip_onomatopoeia(text)

    # 6. Normaliza whitespace e pontuação
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([.!?,;:])\1+", r"\1", text)          # !!! → !
    text = re.sub(r"\s+([.!?,;:])", r"\1", text)          # space antes da pontuação
    text = text.strip(" -—.,;:")

    # T1: viralizador — anti-ban SEMPRE (suaviza termos de strike); gírias só com VIRAL_SLANG=1.
    # Áudio e legenda passam por aqui, então batem. Fallback total se o módulo falhar.
    try:
        import viralizador
        text = viralizador.anti_ban(text)
        if os.environ.get("VIRAL_SLANG") == "1":
            text = viralizador.viralizar(text)
    except Exception:
        pass

    return text


def clean_chunks(chunks, min_len=8, max_len=400):
    """Aplica clean_for_tts em uma lista; descarta os que ficam curtos demais."""
    out = []
    for c in chunks:
        cleaned = clean_for_tts(c)
        if min_len <= len(cleaned) <= max_len:
            out.append(cleaned)
    return out


# ─────────── self-test ───────────
if __name__ == "__main__":
    samples = [
        '**Locução:** "Hoje vamos automatizar o n8n com IA"',
        'ffmpeg -y -i input.mp4 -filter_complex "[1:a]showwaves=s=1080x300:mode=cline" out.mp4',
        'Conecte sua API em https://api.exemplo.com/v1/webhook?token=abc123xyz789def456 — fácil!',
        'function setup() { const x = 10; return x * 2; }',
        '> ## Passo 3: configure o webhook',
        'O agente lê o JSON {chat_id: 7911} e envia pro fluxo principal.',
        '',
        '   ',
        # Diretivas visuais que NÃO devem ser lidas:
        'Olha esse advogado (zoom in) ele economizou 20 horas por semana',
        '(close-up) Olha bem nos olhos dele',
        '[ZOOM IN] Veja só esse resultado',
        '(b-roll: pessoa digitando) Enquanto isso, o sistema processa',
        '(música tensa) E o concorrente perdia',
        'Veja [INSERT B-ROLL HERE] como o fluxo funciona',
        # Parênteses LEGÍTIMOS que devem ser mantidos:
        'A IA responde em segundos (99% precisão)',
        'O dono da empresa (Pedro) ficou impressionado',
    ]
    for s in samples:
        print("IN :", repr(s[:80]))
        print("OUT:", repr(clean_for_tts(s)))
        print()
