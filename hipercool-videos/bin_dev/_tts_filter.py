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
  3. URLs -> "link" ou descarta completamente.
  4. Substitui símbolos comuns por palavras pronunciáveis ou espaço.
  5. Colapsa whitespace e remove pontuação repetida.
"""
import re

# Linhas que provavelmente são código (qualquer uma dessas pistas e a linha é descartada)
CODE_LINE_HINTS = (
    re.compile(r"^\s*(ffmpeg|curl|docker|sudo|brew|pip3?|npm|yarn|git|cd|ls|cat|echo|grep|sed|awk|chmod|python3?|node)\s"),
    re.compile(r"^\s*(import|from|const|let|var|function|def|class|return|if|else|while|for|try|catch|except|async|await)\s"),
    re.compile(r"^\s*[#/]{2,}"),                          # comentários // ou ## etc
    re.compile(r"^\s*[<>{}\[\]]"),                        # começa com tag/bracket
    re.compile(r".+=>.+"),                                # arrow function
    re.compile(r".+;\s*$"),                               # termina com ;
    re.compile(r".+\{\s*$"),                              # bloco abrindo
    re.compile(r"^\s*['\"].*['\"]\s*:\s*"),               # chave JSON
)

# Substituições de símbolos -> palavra/espaço
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
    "->":  " para ",
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
    re.compile(r"\b[A-F0-9]{8,}\b"),                      # hex
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
    text = re.sub(r"`([^`]+)`", r"\1", text)              # inline code -> conteúdo
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)  # headings
    text = re.sub(r"^\s*[->*•·]\s+", "", text, flags=re.MULTILINE)  # bullets

    # 3. Descarta tokens não-pronunciáveis (URLs/emails/IDs longos)
    for pat in DISCARD_TOKENS:
        text = pat.sub(" ", text)

    # 3b. Remove diretivas visuais/sonoras de roteiro (ex.: "(zoom in)",
    # "[CORTE]", "(b-roll: laptop)") que não fazem parte da locução.
    for pat in DIRECTIVE_BLOCKS:
        text = pat.sub(" ", text)

    # 4. Substitui símbolos
    for sym, repl in SYMBOL_MAP.items():
        text = text.replace(sym, repl)

    # 5. Remove qualquer caractere que não seja letra/dígito/pontuação pt-BR/espaço
    text = re.sub(r"[^\w\sáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ,.!?;:'\"()\-—]", " ", text)

    # 6. Normaliza whitespace e pontuação
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([.!?,;:])\1+", r"\1", text)          # !!! -> !
    text = re.sub(r"\s+([.!?,;:])", r"\1", text)          # space antes da pontuação
    text = text.strip(" -—.,;:")

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
