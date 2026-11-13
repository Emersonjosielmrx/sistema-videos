# -*- coding: utf-8 -*-
"""narration.py — NARRAÇÃO via IA (Claude/Gemini + visão dos painéis). Split da -fix.

Transforma IMAGENS de painéis em TEXTO de narração (etapa cara → cacheada).
Públicas: gerar_recap, gerar_recap_fusao, _revisar_coerencia, _forcar_falas_personagens,
_descrever_paineis_claude. Depende de gemini_llm + hp_common. Não importa o pipeline.
"""
import json
import re
import time
import base64
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path

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


def _sanitize_desc(line):
    """Limpa uma linha de descrição (numeração, termos +18, recusas)."""
    line = re.sub(r"^\d+[\.\)]\s*", "", (line or "").strip())
    line = re.sub(r"(?i)(sexu|eroti|adulto|nudez|seios?\b|nua\b|pelad|hentai|pornogr|excita|provoca\w*\s*(sexu|corpo)|insinua\w*\s*sexu|sensual|voluptu|libidin|lasciv|obscen|decot|lingeri|calcinha|sutiã|biquini|peito|seio|bund|coxa\w*\s*expost|explicit|sexual\w*|naked|breast|nippl|panties|underwear|cleavag|strip\w*\s*(teas|cloth)|seduc|intimate\w*\s*scene|body\s*expos|revealing|suggestiv)", "cena intensa", line)
    line = re.sub(r"(?i)\[?(nsfw|adult|18\+|mature|explicit)\]?", "", line)
    if any(x in line.lower() for x in ["can't", "cannot", "i'm not able", "i can't",
                                       "not appropriate", "sexually", "desculpe",
                                       "não posso", "nao posso", "unable to"]):
        line = "Cena do manhwa"
    return line.strip()


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


def _jpeg_bytes(panel_path, max_side=400, quality=55):
    """Reduz o painel e retorna bytes JPEG (pra visão Gemini)."""
    from io import BytesIO
    img = Image.open(panel_path)
    ratio = min(max_side / max(img.size), 1.0)
    if ratio < 1.0:
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _descrever_paineis_claude(panel_paths):
    """Descreve os painéis via Gemini Vision (proxy do Claude está fora).

    Envia em batches de 5 imagens; se o batch vier incompleto, refaz individual.
    safetySettings=BLOCK_NONE no gemini_llm ajuda com conteúdo +18.
    """
    BATCH_PROMPT = ("Descreva cada cena de quadrinhos em 1 frase curta (max 15 palavras). "
                    "Foque APENAS em: ações, expressões faciais, cenário e diálogos visíveis. "
                    "OBRIGATÓRIO: Se houver QUALQUER texto em BALÃO DE FALA, TRANSCREVA TODO o texto "
                    "entre aspas e indique quem fala (ex: 'Garota diz: \"Eu te odeio!\" com raiva'). "
                    "Se houver ONOMATOPEIA visual (BOOM, CRASH, BAM, etc), mencione também. "
                    "NÃO ignore textos nos balões — eles são ESSENCIAIS pra narração. "
                    "NÃO mencione roupas, corpo, aparência física, nudez ou conteúdo adulto. "
                    "Apenas AÇÃO e EMOÇÃO. Se uma cena tiver conteúdo adulto, descreva apenas "
                    "como 'Cena intensa entre personagens'.\n"
                    "Ao final de CADA descrição, adicione entre colchetes o efeito visual ideal: "
                    "[shake] para impacto/luta, [pulse] para nervosismo/tensão, "
                    "[zoom_slow] para momentos calmos, [zoom_fast] para surpresa, "
                    "[pan_down] para revelação, [static] para diálogo normal. "
                    "Exemplo: 'Ele desfere um soco poderoso [shake]'\n"
                    "Responda numerado (1. 2. 3. ...):")
    IND_PROMPT = ("Descreva esta cena de quadrinhos em 1 frase curta (max 15 palavras). "
                  "Foque em ações, expressões e cenário. "
                  "OBRIGATÓRIO: Se houver QUALQUER texto em BALÃO DE FALA, TRANSCREVA TODO o texto "
                  "entre aspas e diga quem fala. Onomatopeias visuais (BOOM, BAM) também. "
                  "Se for conteúdo adulto, descreva "
                  "apenas como 'Cena intensa entre personagens'.\n"
                  "Ao final, adicione entre colchetes o efeito visual ideal: "
                  "[shake] impacto, [pulse] tensão, [zoom_slow] calmo, "
                  "[zoom_fast] surpresa, [pan_down] revelação, [static] diálogo.")

    descriptions = []
    batch_size = 5
    total = len(panel_paths)

    for batch_start in range(0, total, batch_size):
        batch = panel_paths[batch_start:batch_start + batch_size]
        imgs = [_jpeg_bytes(p) for p in batch]

        text = gemini_llm.describe_images(imgs, BATCH_PROMPT, max_tokens=600)
        batch_descs = []
        if text:
            for line in text.splitlines():
                s = _sanitize_desc(line)
                if s:
                    clean_s, effect_tag = _extract_effect_tag(s)
                    batch_descs.append(clean_s)
                    _log_missing_effect(effect_tag, clean_s)

        # Batch incompleto → processa cada painel individualmente
        if len(batch_descs) < len(batch):
            log(f"  ⚠ Visão batch {batch_start} incompleta ({len(batch_descs)}/{len(batch)}), individual...")
            batch_descs = []
            for p, imgb in zip(batch, imgs):
                t = gemini_llm.describe_image(imgb, IND_PROMPT, max_tokens=150)
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
        log("  ✗ [FUSÃO] bloqueada/indisponível (provável conteúdo sensível)")
        return None
    text = re.sub(r"^```json\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        log(f"  ✗ [FUSÃO] JSON inválido: {e}")
        return None
    locucoes = data.get("locucoes", [])
    while len(locucoes) < n:
        locucoes.append({"persona": "Narrador", "gender": ng,
                         "text": "E a história continua...", "cena": ""})
    locucoes = locucoes[:n]
    data["locucoes"] = locucoes
    data["descriptions"] = [_sanitize_desc(l.get("cena", "")) for l in locucoes]
    log(f"  ✓ [FUSÃO] Roteiro: {data.get('titulo_video', titulo)}")
    return data


def gerar_recap(titulo, panel_paths, narrator_gender="F"):
    """Gera narração: Gemini descreve painéis → Gemini narra com base nas descrições."""
    n_paineis = len(panel_paths)
    ng = "M" if (narrator_gender or "F").upper() == "M" else "F"
    npapel = "narrador" if ng == "M" else "narradora"

    # Passo 1: Descrever painéis com Gemini Vision (proxy do Claude está fora)
    log(f"  Descrevendo {n_paineis} painéis via Gemini Vision...")
    descriptions = _descrever_paineis_claude(panel_paths)

    system = (
        f"Voce e um(a) {npapel} brasileiro(a) de canal de recap de manhwa/webtoon. "
        "Estilo: envolvente, dramatico, com humor leve e carisma. "
        "Use girias brasileiras, mantenha o ouvinte grudado.\n\n"
        "REGRAS DE LOCUÇÃO:\n"
        "- Cada locucao: 1-2 frases curtas (8-25 palavras)\n"
        "- PELO MENOS 40% das locuções DEVEM ser de PERSONAGENS (não do narrador)\n"
        "- Se um personagem está visível e parece estar falando, a locução DELE deve ser dita por ELE\n"
        "- NUNCA use 'Personagem' como nome — use nomes reais (ex: Min-Hyuk, Yeol-Mae, Chef)\n"
        "- NUNCA use rótulos genéricos como 'Visitante', 'Rapaz', 'Mulher', 'Pessoa', 'Aluno'.\n"
        "  Use o NOME do personagem. Se o nome ainda não apareceu, use uma descrição\n"
        "  ESTÁVEL e consistente (ex: 'Garota de cabelo rosa') e REPITA exatamente a\n"
        "  mesma em todas as falas dela — nunca troque o rótulo do mesmo personagem.\n"
        "- NUNCA narre 'Fulano disse X' — em vez disso, faça FULANO dizer X diretamente\n\n"
        "GÊNERO (CRÍTICO — define a voz; errar = mulher com voz de homem):\n"
        "- Infira o gênero pelo contexto: pronomes (ela/ele), aparência descrita,\n"
        "  como os outros personagens se referem à pessoa, e o conteúdo da fala.\n"
        "- O MESMO personagem tem SEMPRE o mesmo gender em todas as falas (consistência).\n"
        "- Na dúvida entre M e F, escolha F (a protagonista de manhwa romântico costuma ser mulher).\n\n"
        "EXEMPLO (painel com balão de fala):\n"
        '  ❌ ERRADO: {"persona": "Narrador", "gender": "F", "text": "Min-Hyuk pergunta se ela está bem"}\n'
        '  ✅ CERTO:  {"persona": "Min-Hyuk", "gender": "M", "text": "Você está bem? Me preocupou."}\n\n'
        "EXEMPLO (painel sem balão, só ação):\n"
        '  ✅ CERTO:  {"persona": "Narrador", "gender": "F", "text": "O clima entre os dois ficou tenso."}\n\n'
        "Tom: dramatico e envolvente. Reaja as cenas com emoção, "
        "use cliffhangers, mantenha tensao narrativa. "
        "Foque nas EMOÇÕES e RELAÇÕES entre personagens, não descreva aparência física.\n\n"
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
        log(f"  ✓ Descreveu {len(descriptions)} painéis")
        for i, d in enumerate(descriptions[:3]):
            log(f"    {i+1}: {d[:60]}")
        desc_text = "\n".join(f"Painel {i+1}: {d}" for i, d in enumerate(descriptions))
        user = (
            f"Manhwa: {titulo}\n\n"
            f"Descrições visuais dos {n_paineis} painéis:\n{desc_text}\n\n"
            f"IMPORTANTE: Narre baseado APENAS no que está descrito em cada painel. "
            f"Não invente cenas que não estão nas descrições. "
            f"Gere a narração dramática para CADA painel."
        )
    else:
        # Narração cega (fallback — não deveria chegar aqui)
        log(f"  ⚠ Visão indisponível — narração sequencial sem visão")
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
        # Nível 3: narração SEM descrições (fallback total)
        "FALLBACK_SEM_DESCRICOES",
    ]

    for level in range(len(CENSURA_LEVELS)):
        if CENSURA_LEVELS[level] == "FALLBACK_SEM_DESCRICOES":
            # Último recurso: narrar sem descrições visuais
            log(f"  ⚠ Retry nível {level}: narração SEM descrições (fallback)")
            sanitized_user = (
                f"Manhwa: {titulo}\n"
                f"Numero de paineis: {n_paineis}\n\n"
                f"Este é um manhwa de romance/drama coreano. "
                f"Personagens principais: Joon (homem jovem, tímido, protagonista), "
                f"Noona (mulher mais velha, confiante, provocadora), "
                f"Amigo (homem, cômico, conselheiro do Joon).\n\n"
                f"Gere {n_paineis} locucoes alternando entre:\n"
                f"- Narrador (off, gender F) — faz a ponte entre cenas com drama\n"
                f"- Joon (persona='Joon', gender M) — falas dele, tímido e nervoso\n"
                f"- Noona (persona='Noona', gender F) — falas dela, provocadora\n"
                f"- Amigo (persona='Amigo', gender M) — comentários cômicos\n\n"
                f"Proporção ideal: ~40% Narrador, ~25% Joon, ~25% Noona, ~10% Amigo.\n"
                f"Comece com gancho forte, desenvolva tensão emocional, "
                f"termine com cliffhanger. Cada locução: 1-2 frases curtas (8-25 palavras)."
            )
        else:
            sanitized_user = user
            if CENSURA_LEVELS[level]:
                sanitized_user = re.sub(CENSURA_LEVELS[level], "personagem", sanitized_user)
                if level > 0:
                    log(f"  ⚠ Retry nível {level} de censura...")

        log(f"  Chamando Gemini pra {n_paineis} locuções...")
        text = gemini_llm.generate_text(
            sanitized_user, system=system, max_tokens=8192, temperature=1.0)

        if not text:
            if level < len(CENSURA_LEVELS) - 1:
                log(f"  ✗ Nível {level}: Gemini não retornou narração, próximo nível...")
                continue
            else:
                log(f"  ✗ Gemini não retornou narração após {len(CENSURA_LEVELS)} tentativas")
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
                log(f"  ✗ Nível {level} falhou (recusa ou JSON inválido), tentando próximo nível...")
                continue
            else:
                log(f"  ✗ JSON inválido do Gemini após {len(CENSURA_LEVELS)} tentativas: {e}")
                log(f"  Resposta: {text[:500]}")
                return None

    locucoes = data.get("locucoes", [])
    if len(locucoes) != n_paineis:
        log(f"  ⚠ Claude gerou {len(locucoes)} locuções, esperava {n_paineis}. Ajustando...")
        while len(locucoes) < n_paineis:
            locucoes.append({"persona": "Narrador", "gender": "F",
                            "text": "E a história continua..."})
        locucoes = locucoes[:n_paineis]
        data["locucoes"] = locucoes

    # Pós-processamento: forçar pelo menos 30% de personagens
    locucoes = _forcar_falas_personagens(locucoes, descriptions, n_paineis)
    data["locucoes"] = locucoes

    # Salvar descrições visuais no recap (usadas pra detectar impacto/shake/sfx)
    if descriptions:
        data["descriptions"] = descriptions[:n_paineis]

    return data


# Pool de nomes de personagens do manhwa "The Meek Cat" + gêneros
_PERSONAGENS_POOL = [
    ("Min-Hyuk", "M"), ("Yeol-Mae", "F"), ("Chef", "M"),
    ("Garota Bonita", "F"), ("Desconhecida", "F"), ("Desconhecido", "M"),
    ("Mulher do Balcão", "F"), ("Cliente", "M"), ("Colega", "F"),
    ("Garoto", "M"), ("Amigo", "M"), ("Noona", "F"),
]


# Palavras que indicam que o painel pode ter diálogo/fala
_FALA_KEYWORDS = [
    "diz", "fala", "pergunta", "responde", "grita", "sussurra",
    "exclama", "pede", "fala", "conversa", "comenta", "sugere",
    "diz", "\"", "pergunta", "dialoga", "falam", "dizem",
]


def _forcar_falas_personagens(locucoes, descriptions, n_paineis):
    """Garante que pelo menos 30% das locuções sejam de personagens.

    Se o LLM não gerou personagens suficientes, converte algumas locuções
    do narrador para personagens, escolhendo painéis que têm indícios de diálogo.
    """
    import random as _rd

    # Contar proporção atual
    n_personagens = sum(1 for l in locucoes
                        if l.get("persona", "").lower() not in ("narrador", "narradora"))
    if n_personagens >= max(3, n_paineis * 0.3):
        log(f"  ✓ Já tem {n_personagens} locuções de personagens ({n_personagens*100//n_paineis}%)")
        return locucoes

    # Precisa de mais personagens
    alvo = max(3, int(n_paineis * 0.35))
    precisamos = alvo - n_personagens
    log(f"  ⚠ Personagens: {n_personagens}/{alvo} necessários. Adicionando {precisamos}...")

    # Identificar painéis com indícios de fala (pela descrição) que são Narrador
    candidatos = []
    for i, loc in enumerate(locucoes):
        if loc.get("persona", "").lower() in ("narrador", "narradora"):
            desc = descriptions[i] if i < len(descriptions) else ""
            # Pontuar por indícios de fala
            score = sum(1 for kw in _FALA_KEYWORDS if kw in desc.lower())
            if score > 0:
                candidatos.append((i, score))

    # Ordenar por score (maior chance de fala primeiro) e pegar os melhores
    candidatos.sort(key=lambda x: -x[1])
    selecionados = [idx for idx, _ in candidatos[:precisamos]]

    # Se não tiver candidatos suficientes, pegar aleatórios
    if len(selecionados) < precisamos:
        extras = [i for i in range(n_paineis) if i not in selecionados
                  and locucoes[i].get("persona", "").lower() in ("narrador", "narradora")]
        _rd.shuffle(extras)
        selecionados.extend(extras[:precisamos - len(selecionados)])

    # Atribuir personagens
    for idx in selecionados:
        # Escolher persona não repetindo consecutivamente
        ultima_persona = locucoes[idx - 1].get("persona", "") if idx > 0 else ""
        pool = [p for p in _PERSONAGENS_POOL if p[0] != ultima_persona]
        if not pool:
            pool = _PERSONAGENS_POOL
        nome, genero = _rd.choice(pool)
        loc = locucoes[idx]
        texto_original = loc.get("text", "")
        # Transformar texto de narrador para fala direta do personagem
        # Remove "ele/ela" e transforma em primeira pessoa
        if genero == "M":
            loc["text"] = _rd.choice([
                f"{texto_original}",
                f"Sério? {texto_original.lower()}",
                f"{texto_original} — penso eu.",
                f"Poxa, {texto_original.lower()}",
            ])
        else:
            loc["text"] = _rd.choice([
                f"{texto_original}",
                f"Mas {texto_original.lower()}",
                f"{texto_original} — falo com doçura.",
                f"Ah, {texto_original.lower()}",
            ])
        loc["persona"] = nome
        loc["gender"] = genero

    n_final = sum(1 for l in locucoes
                  if l.get("persona", "").lower() not in ("narrador", "narradora"))
    log(f"  ✓ Personagens ajustados: {n_final}/{n_paineis} ({n_final*100//n_paineis}%)")
    return locucoes


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
        log("  ⚠ Revisão de coerência falhou, mantendo original")
        return locucoes

    # Parse do resultado — espera formato "1. texto\n2. texto\n..."
    revised_lines = []
    for line in result.strip().splitlines():
        line = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
        if line:
            revised_lines.append(line)

    if len(revised_lines) != len(narrator_texts):
        log(f"  ⚠ Revisão retornou {len(revised_lines)} falas (esperava {len(narrator_texts)}), mantendo original")
        return locucoes

    # Substituir apenas as locuções do narrador revisadas
    for idx, new_text in zip(narrator_indices, revised_lines):
        locucoes[idx]["text"] = new_text

    log(f"  ✓ Coerência revisada ({len(revised_lines)} falas do narrador ajustadas)")
    return locucoes

