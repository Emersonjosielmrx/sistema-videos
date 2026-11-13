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
import re
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
_ASPAS = re.compile(r"(\"[^\"]*\"|“[^”]*”|'[^']{3,}')")


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
    BATCH_PROMPT = ("Descreva cada cena de quadrinhos: a AÇÃO em 1 frase curta (max 15 palavras) e, "
                    "se houver BALÃO DE FALA, o texto COMPLETO de cada balão entre aspas duplas, palavra "
                    "por palavra, sem resumir, cortar nem suavizar (palavrões e palavras fortes como "
                    "'escrava' ficam como estão), dizendo quem fala; se a seta do balão aponta pra fora "
                    "do quadro, diga 'alguém fora do quadro diz' (ex: 'Garota diz: \"Eu te odeio!\" com raiva'). "
                    "NÃO mencione roupas, corpo, aparência física ou nudez. Se a cena tiver conteúdo "
                    "adulto, descreva a ação só como 'cena intensa', mas transcreva os balões mesmo assim.\n"
                    "Ao final de CADA descrição, adicione entre colchetes o efeito visual ideal: "
                    "[shake] para impacto/luta, [pulse] para nervosismo/tensão, "
                    "[zoom_slow] para momentos calmos, [zoom_fast] para surpresa, "
                    "[pan_down] para revelação, [static] para diálogo normal. "
                    "Exemplo: 'Ele desfere um soco poderoso [shake]'\n"
                    "Responda numerado (1. 2. 3. ...):")
    IND_PROMPT = ("Descreva esta cena de quadrinhos: a ação em 1 frase curta (max 15 palavras) e, se "
                  "houver BALÃO DE FALA, o texto COMPLETO do balão entre aspas duplas, sem resumir nem "
                  "suavizar, dizendo quem fala (ou 'alguém fora do quadro' se a seta aponta pra fora). "
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
        batch_descs = []
        if text:
            for line in text.splitlines():
                s = _sanitize_desc(line)
                if s:
                    clean_s, effect_tag = _extract_effect_tag(s)
                    batch_descs.append(clean_s)
                    _log_missing_effect(effect_tag, clean_s)

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
    """[(nome, gênero, nº de falas)] dos personagens com NOME dos capítulos anteriores da obra (lidos
    dos roteiros em cache, só pt). A voz é escolhida pelo nome (gemini_tts.voice_for_persona): se o
    protagonista vira "Rapaz" num capítulo, ele troca de voz."""
    cont = {}
    pasta = PROJECT_DIR / "workspace" / "narration_cache"
    for f in pasta.glob(f"{obra}-cap*panels.json"):
        m = re.match(rf"^{re.escape(obra)}-cap(\d+)_", f.name)
        if not m or int(m.group(1)) >= cap:
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


def gerar_recap(titulo, panel_paths, narrator_gender="F", conhecidos=None):
    """Gera narração: Gemini descreve painéis -> Gemini narra com base nas descrições.
    conhecidos: personagens_anteriores() da obra — nomes/gêneros que o roteiro deve reaproveitar."""
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
        "- Locução do narrador: 1-2 frases curtas (8-25 palavras)\n"
        "- Painel com BALÃO (texto entre aspas na descrição): a fala do personagem é o texto do balão, "
        "quase literal (só ajuste pra soar natural em pt-BR), SEM cortar no meio e SEM suavizar palavras "
        "fortes (escrava, matar, palavrão ficam); pode passar de 25 palavras se o balão for longo\n"
        "- 'alguém fora do quadro diz' = a fala é de quem conversa com o personagem visível, não dele\n"
        "- PELO MENOS 40% das locuções DEVEM ser de PERSONAGENS (não do narrador)\n"
        "- Se um personagem está visível e parece estar falando, a locução DELE deve ser dita por ELE\n"
        "- NUNCA use 'Personagem' como nome — use nomes reais (ex: Min-Hyuk, Yeol-Mae, Chef)\n"
        "- NUNCA narre 'Fulano disse X' — em vez disso, faça FULANO dizer X diretamente\n\n"
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

    # Antes havia um "forçar 30% de personagens" que dava fala do narrador a nomes sorteados de outra
    # obra (gênero aleatório = voz trocada). Agora só avisa.
    n_pers = sum(1 for l in locucoes if l.get("persona", "").lower() not in ("narrador", "narradora"))
    log(f"  [{'OK' if n_pers >= n_paineis * 0.3 else '!'}] {n_pers} locuções de personagens "
        f"({n_pers * 100 // max(1, n_paineis)}%)")

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

