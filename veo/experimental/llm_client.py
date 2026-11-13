# -*- coding: utf-8 -*-
"""Cliente LLM barato para gerar falas virais.

Suporta:
- Google Gemini nativo (gemini-2.5-flash-lite) — com rotacao automatica de chaves
  Carrega chaves de <raiz>/secrets/gemini_keys.json (D:\veo\secrets)
- OpenAI-compat (LM Studio/Ollama/OpenRouter) — via LLM_BASE_URL
- Auto-detecta pela URL: se termina em /v1 usa OpenAI-compat, senao Gemini

Variaveis de ambiente:
  LLM_BASE_URL     - URL do endpoint. Se termina em /v1, usa OpenAI-compat.
                     Se vazio (default), usa Gemini nativo do Google.
  LLM_API_KEY      - chave de API. Se vazio, tenta ler de secrets/gemini_keys.json
  LLM_MODEL        - modelo (default: gemini-2.5-flash-lite)
  LLM_TIMEOUT      - timeout em segundos (default: 30)
  LLM_DISABLED     - 1 = desliga (so fallback)

Se LLM falhar (timeout, 429, 5xx), faz fallback para lista estatica.
"""
import os
import json
import time
import logging
import urllib.request
import urllib.error

log = logging.getLogger("llm_client")

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").strip()
LLM_API_KEY = os.environ.get("LLM_API_KEY", os.environ.get("GOOGLE_API_KEY", "")).strip()
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-flash-lite-latest")
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "30"))
LLM_DISABLED = os.environ.get("LLM_DISABLED", "0") == "1"

# Independente: secrets fica em <raiz>/secrets (raiz = pai da pasta do ambiente).
# Override por env VEO_SECRETS_JSON. SEM fallback pra hipercool — o projeto
# tem que rodar mesmo que qualquer outra pasta seja apagada.
_BASE = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(_BASE)  # D:\veo
SECRETS_JSON = os.environ.get(
    "VEO_SECRETS_JSON",
    os.path.join(_RAIZ, "secrets", "gemini_keys.json"))
# URL do Google AI Studio (mesma para todas as chaves Gemini)
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def is_openai_compat() -> bool:
    """Detecta se a URL e OpenAI-compativel (termina em /v1)."""
    return LLM_BASE_URL.endswith("/v1") or "/v1/" in LLM_BASE_URL


# ---------------------------------------------------------------------------
# Carregamento e rotacao de chaves Gemini
# ---------------------------------------------------------------------------
_gemini_keys_cache = None
_gemini_key_index = 0


def _carregar_chaves_gemini() -> list:
    """Carrega chaves Gemini do arquivo secrets/gemini_keys.json.

    Formato esperado: lista de objetos {token, status, fila}.
    Retorna apenas as chaves com status=ok, ordenadas por fila (menor primeiro).
    """
    global _gemini_keys_cache
    if _gemini_keys_cache is not None:
        return _gemini_keys_cache

    if not os.path.exists(SECRETS_JSON):
        log.warning(f"[llm] secrets nao encontrado: {SECRETS_JSON}")
        _gemini_keys_cache = []
        return _gemini_keys_cache

    try:
        with open(SECRETS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Filtra so chaves ok e ordena por fila (menor = mais livre)
        ok = [k for k in data if k.get("status") == "ok" and k.get("token")]
        ok.sort(key=lambda k: k.get("fila", 999))
        _gemini_keys_cache = [k["token"] for k in ok]
        log.info(f"[llm] {len(_gemini_keys_cache)} chaves Gemini carregadas")
        return _gemini_keys_cache
    except Exception as e:
        log.warning(f"[llm] erro ao carregar secrets: {e}")
        _gemini_keys_cache = []
        return _gemini_keys_cache


def _pegar_proxima_chave() -> str:
    """Pega a proxima chave Gemini disponivel (round-robin por fila)."""
    global _gemini_key_index
    keys = _carregar_chaves_gemini()
    if not keys:
        return ""
    key = keys[_gemini_key_index % len(keys)]
    _gemini_key_index += 1
    return key


# ---------------------------------------------------------------------------
# Chamadas HTTP
# ---------------------------------------------------------------------------
def _call_gemini_native(system: str, user: str, max_tentativas: int = 8) -> str:
    """Chama Gemini nativo via HTTP. Rotaciona chaves em caso de 429."""
    chaves_tentadas = set()
    last_err = None

    for tentativa in range(max_tentativas):
        # Se LLM_API_KEY foi passada via env, usa ela primeiro
        if LLM_API_KEY and LLM_API_KEY not in chaves_tentadas:
            api_key = LLM_API_KEY
        else:
            # Tenta proxima chave disponivel
            tentativas_rotacao = 0
            while tentativas_rotacao < 20:
                api_key = _pegar_proxima_chave()
                if not api_key:
                    break
                if api_key not in chaves_tentadas:
                    break
                tentativas_rotacao += 1
            if not api_key or api_key in chaves_tentadas:
                raise RuntimeError("nenhuma chave Gemini disponivel")

        chaves_tentadas.add(api_key)
        url = f"{GEMINI_BASE_URL}/{LLM_MODEL}:generateContent?key={api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "systemInstruction": {"parts": [{"text": system}]},
            "generationConfig": {
                "temperature": 0.9,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 120,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return body["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            last_err = f"HTTP {e.code}: {err_body[:200]}"
            # 429 (rate limit), 401, 403, 500 -> tenta proxima chave
            if e.code in (429, 401, 403, 500, 503):
                # Se for 403 e a msg for PERMISSION_DENIED, a chave esta morta — tenta proxima
                if e.code == 403 and "PERMISSION_DENIED" in err_body:
                    log.info(f"[llm] chave {api_key[:10]}... morta (403), pulando")
                    continue
                # 429 rate limit - tenta proxima
                if e.code == 429:
                    log.info(f"[llm] chave {api_key[:10]}... rate limit (429), rotacionando")
                    time.sleep(0.5)
                    continue
                # outros (401, 500, 503) - tenta proxima tambem
                log.info(f"[llm] chave {api_key[:10]}... falhou ({e.code}), rotacionando")
                time.sleep(0.3)
                continue
            # 400 (bad request) -> nao adianta rotacionar
            raise RuntimeError(last_err)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            continue

    raise RuntimeError(f"todas {max_tentativas} tentativas falharam: {last_err}")


def _call_openai_compat(system: str, user: str) -> str:
    """Chama API OpenAI-compativel (LM Studio/Ollama/OpenRouter)."""
    url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.9,
        "max_tokens": 120,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Funcoes publicas
# ---------------------------------------------------------------------------
def _tem_chave() -> bool:
    """Verifica se ha pelo menos uma chave disponivel (env ou arquivo)."""
    if LLM_API_KEY:
        return True
    if is_openai_compat():
        return bool(LLM_API_KEY)
    return bool(_carregar_chaves_gemini())


def gerar_fala_viral(canal_nome: str, tema: str, exemplos: list = None) -> str:
    """Gera uma fala viral curta em pt-BR para um canal/tema.

    Args:
        canal_nome: nome do canal (ex: "Dicas Financeiras")
        tema: categoria/tema (ex: "Educacao Financeira")
        exemplos: lista de falas anteriores para evitar repeticao

    Returns:
        String com a fala (sem aspas), ~5-15 palavras.

    Raises:
        Exception se a LLM falhar (caller faz fallback).
    """
    if LLM_DISABLED or not _tem_chave():
        raise RuntimeError("LLM_DISABLED ou sem chave disponivel")

    system = (
        "Voce cria falas curtas em portugues brasileiro para videos curtos (TikTok/Reels/Shorts). "
        "Responda APENAS com a fala, sem aspas, sem markdown, sem prefixo. "
        "Maximo 12 palavras. Tom viral, provocativo, gera curiosidade. "
        "NUNCA repita falas que ja foram usadas. Cada fala deve ser unica."
    )

    exemplos_txt = ""
    if exemplos:
        ultimas = exemplos[-10:]
        exemplos_txt = "\n\nFalas ja usadas (NAO repita):\n" + "\n".join(f"- {f}" for f in ultimas)

    user = (
        f"Canal: {canal_nome}\n"
        f"Tema: {tema}\n"
        f"Crie 1 fala viral curta (max 12 palavras) sobre esse tema. "
        f"Tom: gancho forte nos primeiros 2 segundos, brasileiro natural. "
        f"Sem hashtag, sem emoji, sem aspas. So a frase pronta pra falar."
        f"{exemplos_txt}"
    )

    if is_openai_compat():
        return _call_openai_compat(system, user)
    return _call_gemini_native(system, user)


def gerar_prompt_viral(canal_nome: str, tema: str, fala: str, exemplos_cenarios: list = None) -> str:
    """Gera um cenario/camera_description otimizado para viralizar (em ingles)."""
    if LLM_DISABLED or not _tem_chave():
        raise RuntimeError("LLM_DISABLED ou sem chave disponivel")

    system = (
        "Voce cria descricoes de cenario em INGLES para o Veo 3.1 gerar videos verticais (9:16). "
        "Responda APENAS com 1 frase em ingles, max 25 palavras, descrevendo pessoa + acao + visual. "
        "Estilo: viral TikTok, dinamico, cores vibrantes, lighting chamativo. "
        "Sempre vertical (vertical portrait). NUNCA repita cenarios anteriores."
    )

    exemplos_txt = ""
    if exemplos_cenarios:
        ultimos = exemplos_cenarios[-8:]
        exemplos_txt = "\n\nCenarios ja usados (NAO repita):\n" + "\n".join(f"- {c}" for c in ultimos)

    user = (
        f"Canal: {canal_nome}\n"
        f"Tema: {tema}\n"
        f"Fala que sera dita: '{fala}'\n\n"
        f"Crie 1 descricao de cenario viral em INGLES, max 25 palavras, "
        f"formato: Person [doing X] in [Y setting]. [Visual style]. 9:16 vertical.\n"
        f"So a frase em ingles, sem markdown, sem aspas."
        f"{exemplos_txt}"
    )

    if is_openai_compat():
        return _call_openai_compat(system, user)
    return _call_gemini_native(system, user)


def gerar_fala_viral_i18n(canal_nome: str, tema: str, lang: str = "en", exemplos: list = None) -> str:
    """FASE 16: Gera fala viral em outro idioma (en/es/fr)."""
    if LLM_DISABLED or not _tem_chave():
        raise RuntimeError("LLM_DISABLED ou sem chave disponivel")

    dicas = {
        "en": "max 8 words, 'You won't believe', 'This is insane', 'Wait for it'",
        "es": "max 12 palabras, 'No vas a creer', 'Esto es una locura', 'Mira esto'",
        "fr": "max 12 mots, 'Tu ne vas pas en revenir', 'C'est dingue'",
        "de": "max 10 Wörter, 'Das glaubst du nicht', 'Warte mal'",
    }
    dica = dicas.get(lang, dicas.get("en"))

    system = (
        f"Voce cria falas VIRAIS para TikTok/Reels/Shorts em {lang}. "
        f"Responda APENAS com 1 frase em {lang}, {dica}. "
        f"GANCHO forte nos 1.5 primeiros segundos. NUNCA repita falas. "
        f"Regras: nao use jargao, max 1 virgula, max 1 exclamacao."
    )

    exemplos_txt = ""
    if exemplos:
        ultimos = exemplos[-8:]
        exemplos_txt = f"\n\nFalas ja usadas (NAO repita):\n" + "\n".join(f"- {e}" for e in ultimos)

    user = (
        f"Canal: {canal_nome}\n"
        f"Tema: {tema}\n"
        f"Idioma: {lang}\n\n"
        f"Crie 1 fala VIRAIS em {lang} (sem aspas, sem markdown):"
        f"{exemplos_txt}"
    )

    if is_openai_compat():
        return _call_openai_compat(system, user)
    return _call_gemini_native(system, user)


def gerar_prompt_viral_i18n(canal_nome: str, tema: str, fala: str, lang: str = "en",
                             exemplos_cenarios: list = None) -> str:
    """FASE 16: Gera cenario em ingles com fala em outro idioma."""
    if LLM_DISABLED or not _tem_chave():
        raise RuntimeError("LLM_DISABLED ou sem chave disponivel")

    system = (
        "Voce cria descricoes de cenario em INGLES para o Veo 3.1 gerar videos verticais (9:16). "
        "Responda APENAS com 1 frase em ingles, max 25 palavras, descrevendo pessoa + acao + visual. "
        "Estilo: viral TikTok, dinamico, cores vibrantes, lighting chamativo. "
        "Sempre vertical (vertical portrait). NUNCA repita cenarios anteriores."
    )

    exemplos_txt = ""
    if exemplos_cenarios:
        ultimos = exemplos_cenarios[-8:]
        exemplos_txt = "\n\nCenarios ja usados (NAO repita):\n" + "\n".join(f"- {c}" for c in ultimos)

    user = (
        f"Canal: {canal_nome}\n"
        f"Tema: {tema}\n"
        f"Fala em {lang}: '{fala}'\n\n"
        f"Cenario cinematografico em INGLES, max 25 palavras: "
        f"Person [doing X] in [Y setting]. [Visual style]. They speak in {lang}: '{fala}'. 9:16 vertical.\n"
        f"So a frase em ingles, sem markdown, sem aspas."
        f"{exemplos_txt}"
    )

    if is_openai_compat():
        return _call_openai_compat(system, user)
    return _call_gemini_native(system, user)


# ---------------------------------------------------------------------------
# Wrapper de classe (compat): varios call sites usam LLMClient().send(prompt).
# Antes essa classe NAO existia e o import quebrava (caindo em fallback).
# Ela e um adaptador fino sobre as funcoes _call_* deste modulo.
# ---------------------------------------------------------------------------
class LLMClient:
    """Cliente LLM generico. Uso: LLMClient().send("prompt", max_tokens=300).

    send() manda o texto como 'user' com um system generico. Reaproveita a
    rotacao de chaves / OpenAI-compat ja implementada nas funcoes _call_*.
    """
    def __init__(self, system: str = None):
        self.system = system or (
            "Voce e um assistente util. Responda de forma direta e no formato pedido."
        )

    def send(self, prompt: str, max_tokens: int = 300) -> str:
        if LLM_DISABLED or not _tem_chave():
            raise RuntimeError("LLM_DISABLED ou sem chave disponivel")
        # max_tokens fica implicito na generationConfig das funcoes _call_*;
        # mantido na assinatura por compatibilidade com os call sites.
        if is_openai_compat():
            return _call_openai_compat(self.system, prompt)
        return _call_gemini_native(self.system, prompt)


# ---------------------------------------------------------------------------
# Teste e debug
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"LLM_BASE_URL    = {LLM_BASE_URL!r}")
    print(f"LLM_MODEL       = {LLM_MODEL!r}")
    print(f"LLM_DISABLED    = {LLM_DISABLED}")
    print(f"is_openai_compat= {is_openai_compat()}")

    chaves = _carregar_chaves_gemini()
    print(f"chaves Gemini disponiveis: {len(chaves)}")

    if not LLM_DISABLED and _tem_chave():
        try:
            fala = gerar_fala_viral("Dicas Financeiras", "Educacao Financeira",
                                    exemplos=["O segredo dos ricos", "Pare de perder dinheiro"])
            print(f"\nFala gerada: {fala!r}")
            cenario = gerar_prompt_viral("Dicas Financeiras", "Educacao Financeira", fala)
            print(f"Cenario: {cenario!r}")
        except Exception as e:
            print(f"\n[erro LLM] {type(e).__name__}: {e}")
    else:
        print("\n(LLM nao configurada)")