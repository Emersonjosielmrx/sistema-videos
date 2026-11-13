"""tts_cache.py — Cache de áudio TTS com reuso por SIMILARIDADE (modo híbrido).

NÃO está plugado no pipeline ainda — é um módulo isolado, pronto pra ser
integrado em gemini_tts.py / hiper-pipeline.py DEPOIS que o run atual terminar
(plugar mexe nos arquivos que o pipeline em execução recarrega → tem que esperar).

Regras (decisão do usuário):
  • MESMA VOZ sempre reusa quando o texto normalizado é igual (preserva a
    identidade de cada personagem).
  • Frases CURTAS/COMUNS (saudações, interjeições) reusam por GÊNERO — qualquer
    voz feminina reaproveita áudio feminino do mesmo texto, idem masculino.
  • Gênero NUNCA cruza: áudio de mulher só pra mulher, de homem só pra homem
    (o gênero está embutido na chave dos dois modos).
  • Normalização forte: ignora pontuação, acento, caixa e espaços repetidos —
    "O que foi, hein?" == "o que foi hein".

Compatibilidade: lookup() também tenta a CHAVE ANTIGA (voz:texto.strip().lower())
pra reaproveitar os .wav já gravados sem regerar nada.
"""
import hashlib
import re
import unicodedata

# Frases curtas/comuns que podem reusar por gênero (além do limite de palavras).
# Mantidas normalizadas (sem acento/pontuação, minúsculas).
COMMON_PHRASES = {
    "oi", "ola", "ei", "opa", "alo", "bom dia", "boa tarde", "boa noite",
    "obrigado", "obrigada", "valeu", "de nada", "com licenca", "desculpa",
    "desculpe", "sim", "nao", "claro", "talvez", "o que", "o que foi",
    "como assim", "serio", "verdade", "entendi", "ata", "ham", "hein",
    "hum", "ahn", "nossa", "caramba", "socorro", "espera", "calma",
    "para", "vamos", "tchau", "ate logo", "ate mais", "por favor",
    "que isso", "meu deus", "ai meu deus", "nao acredito",
}

# Frases com até este nº de palavras (após normalizar) contam como "curtas".
SHORT_WORD_LIMIT = 3


def strip_accents(s: str) -> str:
    """Remove acentos/diacríticos (á→a, ç→c)."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_text(text: str) -> str:
    """Normaliza pra comparação: minúsculas, sem acento, sem pontuação, espaço único."""
    if not text:
        return ""
    t = strip_accents(text.lower())
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)  # tira pontuação
    t = re.sub(r"_", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_short_common(normalized: str) -> bool:
    """True se a fala é curta o suficiente (ou comum) pra reuso por gênero."""
    if not normalized:
        return False
    if normalized in COMMON_PHRASES:
        return True
    return len(normalized.split()) <= SHORT_WORD_LIMIT


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def primary_key(text: str, voice: str, gender: str) -> str:
    """Chave nova (híbrida).
    • curta/comum  → reuso por GÊNERO:  G:<gender>:<texto_normalizado>
    • caso normal  → reuso por VOZ:     V:<voice>:<texto_normalizado>
    O gênero está nas duas, então áudio de mulher nunca vai pra homem.
    """
    norm = normalize_text(text)
    g = (gender or "M").upper()[:1]
    if is_short_common(norm):
        return _h(f"G:{g}:{norm}")
    return _h(f"V:{voice}:{norm}")


def legacy_key(text: str, voice: str) -> str:
    """Chave ANTIGA usada hoje no pipeline (pra não perder o cache já gravado)."""
    return _h(f"{voice}:{text.strip().lower()}")


def candidate_keys(text: str, voice: str, gender: str) -> list:
    """Ordem de tentativa no lookup: chave nova → chave antiga (compat)."""
    return [primary_key(text, voice, gender), legacy_key(text, voice)]


def lookup(cache_dir, text: str, voice: str, gender: str):
    """Retorna o Path do .wav cacheado (nova ou antiga chave) ou None.
    `cache_dir` é um pathlib.Path."""
    for k in candidate_keys(text, voice, gender):
        p = cache_dir / f"{k}.wav"
        if p.exists():
            return p
    return None


# ── Preferência por voz PREMIUM no reuso (Gemini + ElevenLabs) ───────────────
# Regra do usuário: voz premium é melhor; se a MESMA fala (mesmo GÊNERO) já está
# gravada numa voz premium, reusa a premium mesmo no modo edge (voz melhor de
# graça, inclusive em produção do projeto "inferior"). As vozes masculinas do
# edge servem só pra teste. Gênero NUNCA cruza (a chave carrega o gênero).
PREMIUM_VOICES_F = ["Kore", "Achernar", "Despina", "Sulafat", "Vindemiatrix",
                    "Aoede", "Erinome", "Leda", "Zephyr", "Pulcherrima"]
PREMIUM_VOICES_M = ["Charon", "Puck", "Fenrir", "Orus", "Gacrux",
                    "Iapetus", "Algenib", "Algieba", "Achird", "Sadachbia"]


def _is_edge_voice(voice: str) -> bool:
    """True se a voz é do edge-tts (grátis). Premium = Gemini/ElevenLabs."""
    return bool(voice) and voice.startswith("pt-BR-")


def lookup_premium_first(cache_dir, text: str, voice: str, gender: str):
    """Lookup que PREFERE uma gravação premium já existente do mesmo texto+gênero.

    1) Se a voz pedida é edge (grátis), procura primeiro se já existe a fala em
       alguma voz premium (Gemini/ElevenLabs) do MESMO gênero — e reusa essa.
    2) Senão, cai no lookup normal (mesma voz → chave antiga).
    Nunca cruza gênero. Para frases curtas/comuns a chave já é por gênero, então
    o reuso acontece naturalmente; isto cobre o reuso premium das falas LONGAS."""
    g = (gender or "M").upper()[:1]
    if _is_edge_voice(voice):
        pool = PREMIUM_VOICES_F if g == "F" else PREMIUM_VOICES_M
        for pv in pool:
            p = cache_dir / f"{primary_key(text, pv, g)}.wav"
            if p.exists():
                return p
    return lookup(cache_dir, text, voice, gender)


def store_path(cache_dir, text: str, voice: str, gender: str):
    """Onde GRAVAR um áudio novo (sempre na chave nova/híbrida)."""
    return cache_dir / f"{primary_key(text, voice, gender)}.wav"


# ── Autoteste (roda sem API): python bin/tts_cache.py ────────────────────────
if __name__ == "__main__":
    ok = 0; fail = 0
    def check(cond, msg):
        global ok, fail
        if cond: ok += 1
        else: fail += 1; print("  ✗", msg)

    # normalização ignora pontuação/acento/caixa/espaço
    check(normalize_text("O que foi, hein?") == normalize_text("o que foi hein"),
          "pontuacao/caixa deviam normalizar igual")
    check(normalize_text("Olá   amigo!!") == "ola amigo", "acento+espaco+pontuacao")

    # frase curta/comum → mesma chave pra vozes diferentes do MESMO gênero
    k_ach = primary_key("Bom dia!", "Achernar", "F")
    k_des = primary_key("bom dia", "Despina", "F")
    check(k_ach == k_des, "saudacao curta: mulheres diferentes deviam compartilhar")

    # mas NUNCA cruza gênero
    k_homem = primary_key("Bom dia!", "Charon", "M")
    check(k_ach != k_homem, "genero diferente NAO pode compartilhar")

    # fala longa → reuso só por voz (personagens diferentes NÃO compartilham)
    long_a = primary_key("Eu nunca imaginei que voce faria algo assim comigo", "Achernar", "F")
    long_b = primary_key("Eu nunca imaginei que voce faria algo assim comigo", "Despina", "F")
    check(long_a != long_b, "fala longa: vozes diferentes NAO compartilham")
    # mesma voz, fala longa, só pontuação diferente → reusa
    long_c = primary_key("eu nunca imaginei que voce faria algo assim comigo.", "Achernar", "F")
    check(long_a == long_c, "mesma voz + pontuacao diferente deviam reusar")

    print(f"\nAUTOTESTE tts_cache: {ok} ok, {fail} falhas")
    raise SystemExit(1 if fail else 0)
