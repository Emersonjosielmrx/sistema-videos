#!/usr/bin/env python3
"""hiper-pipeline.py — Pipeline principal de vídeo hipercool.

Fluxo completo: scrape → split painéis → narração IA → TTS → Ken Burns → concat → notify

Uso:
    # Pipeline completa a partir de URL
    python bin/hiper-pipeline.py --url <chapter_url> --titulo "Manhwa cap X"

    # A partir de cache já baixado
    python bin/hiper-pipeline.py --slug nome --titulo "..."

    # A partir de painéis já cortados
    python bin/hiper-pipeline.py --panels-dir workspace/panels/x/ --titulo "..."

    # Opções:
    #   --max-panels 12       (padrão 12)
    #   --skip-notify         (não manda Telegram)
    #   --dry-run
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Adiciona bin/ ao path pra importar helpers locais
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _tts_filter import clean_for_tts
import edge_tts_engine as gemini_tts
import gemini_llm
import _tg_safe
import effects_engine
import tts_cache  # cache de áudio por similaridade (modo híbrido) — ver PENDENCIAS_CACHE_AUDIO_E_TTS.md

try:
    from PIL import Image
except ImportError:
    print("ERRO: Pillow não instalado. Rode: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)

PROJECT_DIR = Path(__file__).resolve().parent.parent
# ┌─────────────────────────────────────────────────────────────────────────┐
# │ ATENÇÃO — MATERIAIS COMPARTILHADOS (migração de 2026-06-28)               │
# │ As pastas workspace/{assets,tts_cache,narration_cache,panels,videos} e   │
# │ material/tts_cache NÃO são pastas reais: são JUNCTIONS que apontam para   │
# │ D:\hipercool-materiais\ (pasta única compartilhada por todos os projetos  │
# │ hipercool). Trilhas, SFX, overlays, caches de voz e vídeos prontos ficam  │
# │ TODOS lá. Só o código (bin/) é separado por projeto.                      │
# │                                                                            │
# │ SE ALGO SUMIR / "FileNotFound" em assets/trilhas/cache: a junction pode   │
# │ ter quebrado. Confira com: `dir workspace\assets` (deve listar o conteúdo │
# │ de D:\hipercool-materiais\assets). Recriar junction (PowerShell):         │
# │   New-Item -ItemType Junction -Path workspace\assets `                    │
# │            -Target D:\hipercool-materiais\assets                          │
# │ As pastas reais antigas foram preservadas como *_premove (não apagadas).  │
# └─────────────────────────────────────────────────────────────────────────┘
CACHE_DIR = PROJECT_DIR / "workspace" / "cache"
VIDEOS_DIR = PROJECT_DIR / "workspace" / "videos"
TMP_DIR = PROJECT_DIR / "workspace" / "tmp"
# Handle do canal pro watermark (configurável via env)
WATERMARK_HANDLE = os.environ.get("HIPERCOOL_WATERMARK", "@InovareManhwaVerse")
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

MAX_PANELS_DEFAULT = 50


# MODO TESTE (env TEST_MODE):
#   0 = produção (tudo ativado, qualidade máxima)
#   1 = teste rápido (pula upscale)
#   2 = teste ultra-rápido (pula upscale + legendas/karaokê)
#   3 = teste com cache total (usa cache visão+TTS, pula upscale+legendas — mais rápido possível)
#   4 = modo autônomo/noturno (gera TUDO + análise frame-a-frame + auto-validate + regera se falhar)
TEST_MODE = int(os.environ.get("TEST_MODE", "0"))


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


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


# ─── Pós-processamento: forçar falas de personagens ──────────────────────────

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


# ─── TTS com cache (reaproveitamento de falas) ────────────────────────────────
TTS_CACHE_DIR = PROJECT_DIR / "material" / "tts_cache"
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _tts_cache_key(text, voice):
    """Gera hash único pra texto+voz."""
    import hashlib
    key = f"{voice}:{text.strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _voice_context(persona, text):
    """Detecta contexto da fala pra efeito de áudio (Ponto L)."""
    blob = f"{persona or ''} {text or ''}".lower()
    if any(k in blob for k in ["(pensando)", "pensando", "pensamento", "internamente",
                               "na mente", "em pensamento", "voz interior", "pensa consigo"]):
        return "thought"
    if any(k in blob for k in ["(telefone)", "telefone", "celular", "ligação", "ligacao",
                               "no telefone", "pelo telefone", "(rádio)", "(radio)",
                               "walkie", "interfone"]):
        return "phone"
    return None


def _apply_voice_context(wav_path, persona, text):
    """Aplica filtro de áudio conforme o contexto: eco (pensamento) / banda (telefone)."""
    ctx = _voice_context(persona, text)
    if not ctx:
        return
    af = {
        # eco suave + brilho reduzido = pensamento/voz interior
        "thought": "aecho=0.8:0.88:55|95:0.35|0.2,lowpass=f=7500",
        # banda estreita estilo telefone/rádio
        "phone": "highpass=f=500,lowpass=f=2700,volume=1.35",
    }[ctx]
    wav_path = Path(wav_path)
    tmp = wav_path.with_suffix(".fx.wav")
    try:
        subprocess.run(["ffmpeg", "-y", "-i", str(wav_path), "-af", af, str(tmp)],
                       check=True, capture_output=True, timeout=30)
        tmp.replace(wav_path)
        log(f"  🎚️ voz [{ctx}] aplicada")
    except Exception:
        if tmp.exists():
            tmp.unlink()


def tts_panel(text, wav_path, persona="Narrador", gender=None, sensual=False, force_tts=False):
    """Gera áudio TTS pra um painel. Usa cache pra reusar falas já geradas.

    sensual=True prefixa uma instrução de estilo sedutora/sussurrada (obra +18).
    O texto enviado (com ou sem prefixo) é o que define a chave de cache, então
    as versões sensual e normal são cacheadas separadamente.

    Inclui retry com rotação de voz: se a voz de personagem falha, tenta Kore (neutro).
    """
    import shutil
    cleaned = clean_for_tts(text)
    if not cleaned or len(cleaned) < 2:
        log(f"  ⚠ Texto muito curto após limpeza, pulando TTS: {text[:40]}")
        return False

    # Vozes do personagem e narrador (fallback)
    voice = gemini_tts.voice_for_persona(persona, gender=gender, kind="hipercool")
    fallback_voice = "Kore"  # Voz padrão do narrador como fallback

    # Momentos sensuais: prefixar diretiva de estilo
    tts_text = (gemini_tts.SENSUAL_STYLE_PREFIX + cleaned) if sensual else cleaned

    for attempt, (current_persona, current_voice) in enumerate([
        (persona, voice),
        ("Narrador", fallback_voice) # Segunda tentativa: voz neutra
    ]):
        # Cache híbrido por similaridade (bin/tts_cache.py): mesma voz reusa o texto
        # normalizado; frases curtas/comuns reusam por gênero (nunca cruza gênero).
        # O gênero vem da PRÓPRIA voz (consistência); lookup tenta chave nova → antiga (compat).
        vgender = "F" if gemini_tts._is_female(current_voice) else "M"
        # Lookup PREMIUM-FIRST: se a mesma fala (mesmo gênero) já existe gravada
        # em voz premium (Gemini/ElevenLabs), reusa ela mesmo no modo edge — voz
        # melhor de graça. Senão, usa o cache da própria voz. Gênero nunca cruza.
        found = tts_cache.lookup_premium_first(TTS_CACHE_DIR, tts_text, current_voice, vgender)
        if found and not force_tts:
            shutil.copy2(found, wav_path)
            log(f"  TTS: {current_persona} ({current_voice}){' [SENSUAL]' if sensual else ''} — [CACHE] {cleaned[:50]}...")
            _apply_voice_context(wav_path, persona, text)
            return True

        log(f"  TTS: {current_persona} ({current_voice}){' [SENSUAL]' if sensual else ''} — {cleaned[:50]}...")
        ok = gemini_tts.speak(tts_text, voice=current_voice, out_wav=wav_path)

        if ok and Path(wav_path).exists():
            shutil.copy2(wav_path, tts_cache.store_path(TTS_CACHE_DIR, tts_text, current_voice, vgender))
            _apply_voice_context(wav_path, persona, text)
            return True

        if attempt == 0:
            log(f"  ⚠ TTS falhou com voz '{current_voice}', tentando fallback '{fallback_voice}'...")
            time.sleep(1)  # Pequena pausa antes do retry

    log(f"  ⚠ TTS falhou EM AMBAS as vozes ({voice} e {fallback_voice})")
    return False

# ─── Video Assembly (usa effects_engine) ─────────────────────────────────────
# O effects_engine.py porta os efeitos do n8n (60 filtros visuais, 80+ transições,
# 85 movimentos, trilha sonora com ducking). Ver bin/_reference_n8n_effects.js.


def _burn_webm_overlays(video_in, overlays, video_out):
    """Sobrepõe vídeos WebM (legendas HyperFrames) no vídeo principal com timing.

    overlays: lista de {"webm": path, "start": float, "end": float}
    Usa chromakey (fundo preto → transparente) + overlay com enable='between(t,start,end)'.
    """
    if not overlays:
        return False

    # Limitar a 20 overlays simultâneos (ffmpeg tem limite de inputs)
    overlays = overlays[:20]

    inputs = ["-i", str(video_in)]
    for ov in overlays:
        inputs += ["-i", ov["webm"]]

    # Cadeia de overlays: cada WebM é sobreposto na janela de tempo
    # Usar chromakey para remover fundo preto dos WebMs
    parts = []
    cur = "[0:v]"
    for idx, ov in enumerate(overlays, start=1):
        out = f"[vhf{idx}]"
        # Chromakey remove preto, overlay no centro-inferior
        parts.append(
            f"[{idx}:v]chromakey=0x000000:0.15:0.1,scale=1080:1920:force_original_aspect_ratio=decrease[hfov{idx}];"
            f"{cur}[hfov{idx}]overlay=0:0:"
            f"enable='between(t,{ov['start']:.2f},{ov['end']:.2f})'{out}"
        )
        cur = out

    filter_complex = ";".join(parts)
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", cur, "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-g", "30",
        "-c:a", "copy",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=1800)
        return Path(video_out).exists() and Path(video_out).stat().st_size > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log(f"  ✗ burn_webm_overlays falhou: {str(e)[:200]}")
        return False



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


# ─── Pipeline principal ──────────────────────────────────────────────────────
def run_pipeline(panels_dir, titulo, max_panels=MAX_PANELS_DEFAULT,
                 skip_notify=False, dry_run=False, skip_credits=0, animated=False,
                 start_panel=0, fusao=False, narrator_gender="F", subtitles=False,
                 branding=True, karaoke=False, censura=False, # Argumentos existentes
                 force_llm=False, force_tts=False,
                 hyperframes_karaoke=False, output_suffix=""): # Novo output_suffix
    """Executa a pipeline completa a partir de painéis já cortados.

    skip_credits: pula os N primeiros painéis (geralmente créditos/capa/avisos).
    start_panel: offset no início (pra gerar PARTES seguintes do mesmo capítulo).
                 Aplicado DEPOIS dos filtros (créditos/pequenos/brancos), então
                 part 1 = start_panel=0, part 2 = start_panel=55, etc.
    """
    panels_dir = Path(panels_dir)
    exts = {".jpg", ".jpeg", ".png"}
    panel_files = sorted(
        f for f in panels_dir.iterdir()
        if f.suffix.lower() in exts and not f.name.startswith("_")
    )

    if not panel_files:
        log("✗ Nenhum painel encontrado!")
        return None

    # Pular painéis de créditos/capa (geralmente os primeiros são avisos 18+, logos, etc).
    # Default: pula SEMPRE o 1º painel (era a função antiga). Ajustável via env
    # SKIP_PANELS (0 = não pular, 2 = pular dois...). O arg skip_credits explícito,
    # se passado >0, tem prioridade sobre o env.
    if not skip_credits:
        try:
            skip_credits = int(os.environ.get("SKIP_PANELS", "1"))
        except ValueError:
            skip_credits = 1
    if skip_credits and len(panel_files) > skip_credits:
        log(f"  Pulando {skip_credits} painel(is) inicial(is) (créditos/capa)")
        panel_files = panel_files[skip_credits:]

    # Filtrar painéis muito pequenos (provavelmente headers/ads/créditos)
    min_panel_height = 300
    panel_files = [f for f in panel_files if Image.open(f).height >= min_panel_height]

    # Filtrar painéis em branco (cortes errados do splitter)
    def _is_blank(path):
        img = Image.open(path).convert("L")
        from PIL import ImageStat
        stat = ImageStat.Stat(img)
        return stat.mean[0] > 248  # quase branco puro
    before = len(panel_files)
    panel_files = [f for f in panel_files if not _is_blank(f)]
    if len(panel_files) < before:
        log(f"  Removidos {before - len(panel_files)} painéis em branco")

    # Offset de início (pra gerar partes seguintes do mesmo capítulo)
    if start_panel > 0:
        total_disp = len(panel_files)
        panel_files = panel_files[start_panel:]
        log(f"  Começando do painel {start_panel} (parte seguinte) — {len(panel_files)} de {total_disp} restantes")

    # Limitar painéis
    if len(panel_files) > max_panels:
        log(f"  {len(panel_files)} painéis → limitando a {max_panels}")
        panel_files = panel_files[:max_panels]

    n = len(panel_files)
    log(f"Pipeline: {titulo} ({n} painéis)")

    if dry_run:
        log("  [DRY-RUN] Mostrando o que seria feito:")
        log(f"  1. Gerar narração ({n} locuções) com visão dos painéis")
        log(f"  2. TTS pra {n} painéis (Gemini 3.1 Flash)")
        log(f"  3. {n} clips Ken Burns → concat → MP4")
        log(f"  4. Notificar Telegram: {'sim' if not skip_notify else 'não'}")
        return None

    # 1. Narração IA (com cache — reusar locuções já geradas)
    narration_cache_dir = PROJECT_DIR / "workspace" / "narration_cache"
    narration_cache_dir.mkdir(parents=True, exist_ok=True)
    slug = panels_dir.name if hasattr(panels_dir, 'name') else Path(panels_dir).name
    # Inclui o offset (e o modo fusão) na chave pra não colidir entre variações
    part_tag = f"_s{start_panel}" if start_panel > 0 else ""
    if fusao:
        part_tag += "_fusao"
    narration_cache_file = narration_cache_dir / f"{slug}{part_tag}_{n}panels.json"

    if narration_cache_file.exists() and not force_llm:
        import json as _json
        recap = _json.loads(narration_cache_file.read_text())
        log(f"  ✓ Narração [CACHE]: {recap.get('titulo_video', titulo)}")
    else:
        recap = None
        if force_llm: log("  ⚠ --force-llm ativo, ignorando cache de narração.")
        if fusao:
            # Híbrido: tenta fusão (1 chamada). Se bloquear (conteúdo +18), cai pro 2-passos.
            recap = gerar_recap_fusao(titulo, panel_files, narrator_gender=narrator_gender)
            if not recap:
                log("  Fusão indisponível → fluxo 2-passos (visão neutra + narração)")
        if not recap:
            recap = gerar_recap(titulo, panel_files, narrator_gender=narrator_gender)
        if not recap:
            log("✗ Falha na geração de narração")
            return None
        # Salvar no cache
        import json as _json
        narration_cache_file.write_text(_json.dumps(recap, ensure_ascii=False, indent=2))
        log(f"  ✓ Narração: {recap.get('titulo_video', titulo)} [salvo no cache]")

    locucoes = recap["locucoes"]
    descriptions = recap.get("descriptions", [])

    # 1b. Revisão de coerência narrativa — ajusta conexões entre locuções do narrador.
    # Roda UMA VEZ e salva o resultado no narration_cache (flag _revised). Senão o texto
    # do narrador mudava a cada run → furava o cache de áudio (regerava ~38 falas à toa).
    if not recap.get("_revised"):
        locucoes = _revisar_coerencia(locucoes, titulo)
        recap["locucoes"] = locucoes
        recap["_revised"] = True
        try:
            narration_cache_file.write_text(_json.dumps(recap, ensure_ascii=False, indent=2))
            log("  ✓ Narração revisada salva no cache (estável p/ próximos runs)")
        except Exception as e:
            log(f"  ⚠ não consegui salvar revisão no cache: {e}")

    # 2. TTS + clips (com efeitos visuais do effects_engine)
    clips = []
    clip_texts = []  # texto da narração por clip (pra legendas) — alinhado com clips
    clip_personas = []  # persona por clip (pra name tag) — alinhado com clips
    clip_sensual = []  # bool por clip (pra censura) — alinhado com clips
    # Censura VISUAL na imagem do painel (exodia fosco / blur total do censura_visual.py).
    # Só quando --censura. cens_jobs = painéis +18 detectados → rebuild do clip a partir da
    # imagem censurada, num passo pós-loop. NÃO afeta o vídeo principal (limpo).
    cens_jobs = []
    _cv = None
    if censura:
        try:
            import censura_visual as _cv
        except Exception as _e:
            log(f"  ⚠ censura_visual indisponível ({_e}); versão censurada será pulada")
            _cv = None
    session_tmp = TMP_DIR / f"session_{int(time.time())}"
    session_tmp.mkdir(parents=True, exist_ok=True)
    efx = effects_engine.EffectsManager()

    def _detectar_cens(panel):
        """Score +18 do painel via censura_visual (Sightengine, cache md5). None se indisponível.
        Mesma detecção 'oficial' usada nos testes que geraram as referências (processar_painel)."""
        if not _cv:
            return None
        try:
            det = _cv.detectar_score(str(panel))
        except Exception:
            return None
        return det[0] if det is not None else None

    def _render_cens_clip(job, panel, out):
        """Reconstrói o clip do painel +18 a partir da IMAGEM já censurada, com os MESMOS
        efeitos/params do clip limpo → duração idêntica (timeline e legendas não deslocam)."""
        p = job["params"]
        if job["kind"] == "flash":
            return effects_engine.build_flash_clip(
                str(panel), str(out), p["i"], efx, duration=p.get("duration", 0.8),
                transition_type=p["transition_type"], sfx_file=p["sfx_file"])
        if p["is_impact"]:
            return effects_engine.build_clip_with_shake(
                str(panel), str(job["wav"]), str(out), p["i"], efx,
                transition_type=p["transition_type"], sfx_file=p["sfx_file"],
                overlay_video=p["overlay_video"], mood=p["clip_mood"])
        if p["is_tension"]:
            return effects_engine.build_clip_with_shake(
                str(panel), str(job["wav"]), str(out), p["i"], efx,
                shake_intensity=5, shake_freq=8,
                transition_type=p["transition_type"], sfx_file=p["sfx_file"],
                overlay_video=p["overlay_video"], mood=p["clip_mood"])
        if p["animated"]:
            return effects_engine.build_clip_animated(
                str(panel), str(job["wav"]), str(out), p["i"], efx,
                transition_type=p["transition_type"], sfx_file=p["sfx_file"])
        return effects_engine.build_clip(
            str(panel), str(job["wav"]), str(out), p["i"], efx,
            transition_type=p["transition_type"], sfx_file=p["sfx_file"],
            overlay_video=p["overlay_video"], mood=p["clip_mood"])

    # Consolidação de falas DESATIVADA — causava painéis vazios
    # for i in range(len(locucoes) - 1):
    #     cur = locucoes[i]
    #     nxt = locucoes[i + 1]
    #     cur_text = (cur.get("text") or "").strip()
    #     cur_persona = (cur.get("persona") or "").lower()
    #     nxt_persona = (nxt.get("persona") or "").lower()
    #     if (cur_persona == nxt_persona
    #         and cur_persona not in ("narrador", "narradora")
    #         and 0 < len(cur_text.split()) < 5):
    #         nxt["text"] = cur_text + " " + (nxt.get("text") or "").strip()
    #         cur["text"] = ""

    for i, (panel_path, loc) in enumerate(zip(panel_files, locucoes)):
        wav_path = session_tmp / f"audio_{i:03d}.wav"
        clip_path = session_tmp / f"clip_{i:03d}.mp4"

        # Detecção +18 na IMAGEM do painel (só p/ versão censurada; cache md5).
        _cens_score = _detectar_cens(panel_path) if (censura and _cv) else None
        _is_nsfw = _cens_score is not None and _cens_score >= _cv.LIMIAR_DUVIDA

        # Determinar transição e SFX
        transition_type, sfx_file = effects_engine.get_transition_and_sfx(i, descriptions)

        # SFX contextual: se o texto menciona keyword específica, usar SFX adequado
        contextual_sfx, contextual_vol = effects_engine.pick_sfx_for_text(loc.get("text", ""))
        if contextual_sfx:
            sfx_file = contextual_sfx

        # Detectar momento sensual/+18
        desc_for_sensual = descriptions[i] if i < len(descriptions) else ""
        # REGRA FIRME: NINGUÉM sussurra. Voz sensual ELIMINADA completamente.
        # Nem narrador, nem personagem masculino, nem feminino.
        is_sensual = False

        text_to_narrate = loc.get("text", "").strip()

        if not text_to_narrate:
            # Painel SEM NARRAÇÃO INTENCIONAL: clip rápido SEM SFX de transição
            log(f"  ⚡ Painel {i} sem narração, gerando clip rápido (sem SFX)")
            ok_flash = effects_engine.build_flash_clip(panel_path, clip_path, i, efx, duration=0.8,
                                                       transition_type=transition_type, sfx_file=None) # << SFX=None
            if ok_flash:
                clips.append(clip_path)
                clip_texts.append("")
                clip_personas.append("")
                clip_sensual.append(is_sensual)
                if _is_nsfw:
                    cens_jobs.append({"clip": clip_path, "panel": panel_path, "wav": wav_path,
                                      "score": _cens_score, "kind": "flash",
                                      "params": {"i": i, "duration": 0.8,
                                                 "transition_type": transition_type, "sfx_file": None}})
            continue # Próximo painel

        # Painel COM NARRAÇÃO: tentar TTS
        # REGRA FIRME: Narrador SEMPRE usa a mesma voz (gender=None → Kore).
        # Ignorar gender do LLM para manter consistência.
        persona_lower = (loc.get("persona") or "narrador").lower()
        tts_gender = None if persona_lower in ("narrador", "narradora", "narrator") else loc.get("gender")
        ok = tts_panel(text_to_narrate, wav_path,
                       persona=loc.get("persona", "Narrador"),
                       gender=tts_gender,
                       sensual=is_sensual,
                       force_tts=force_tts)

        if not ok:
            # Painel com narração ESPERADA, mas TTS FALHOU: clip rápido COM SFX (indica erro)
            log(f"  ⚠ TTS falhou pra painel {i} (mas tinha narração), gerando clip rápido (com SFX)")
            ok_flash = effects_engine.build_flash_clip(panel_path, clip_path, i, efx, duration=0.8,
                                                       transition_type=transition_type, sfx_file=sfx_file) # << SFX normal
            if ok_flash:
                clips.append(clip_path)
                clip_texts.append("")
                clip_personas.append("")
                clip_sensual.append(is_sensual)
                if _is_nsfw:
                    cens_jobs.append({"clip": clip_path, "panel": panel_path, "wav": wav_path,
                                      "score": _cens_score, "kind": "flash",
                                      "params": {"i": i, "duration": 0.8,
                                                 "transition_type": transition_type, "sfx_file": sfx_file}})
            continue # Próximo painel

        # Se chegou aqui, TTS foi OK e tinha narração.

        # Enhancement de áudio DESATIVADO — degradava qualidade do edge-tts
        # effects_engine.enhance_narration_audio(wav_path)

        # Delay entre requests TTS (só se não veio do cache)
        # A cada 10 painéis TTS reais, pausa 10s extras pra evitar quota em lote
        if not (TTS_CACHE_DIR / f"{_tts_cache_key(clean_for_tts(loc['text']), gemini_tts.voice_for_persona(loc.get('persona', 'Narrador'), gender=loc.get('gender'), kind='hipercool'))}.wav").exists():
            time.sleep(3.0)
        else:
            time.sleep(0.3)  # Breath mesmo em cache pra não sobrecarregar ffmpeg

        # Clip com efeitos (movimentos variados + cor + vinheta)
        # Detectar impacto/tensão pra aplicar camera shake
        desc = descriptions[i] if i < len(descriptions) else ""
        is_impact = effects_engine.is_impact_panel(desc)
        is_tension = effects_engine.is_tension_panel(desc)
        clip_mood = effects_engine.detect_mood_from_text(text_to_narrate)

        # Overlay atmosférico (chuva/neve/faíscas/pétalas) — reimplementado com colorkey
        overlay_video = effects_engine.overlay_for_mood(clip_mood)

        tag = "  [SHAKE]" if is_impact else ("  [TENSION]" if is_tension else "")
        ov_tag = "  [speedlines]" if (is_impact and overlay_video) else (
            f"  [{effects_engine.MOOD_OVERLAY.get(clip_mood, '')}]" if overlay_video else "")
        sfx_name = Path(sfx_file).name if sfx_file else "nenhum"
        trans_name = transition_type or "corte_seco"
        persona_name = loc.get("persona", "?")
        voice_used = gemini_tts.voice_for_persona(persona_name, gender=loc.get("gender"), kind="hipercool")
        log(f"  Clip {i+1}/{n}{tag}{ov_tag} | painel={Path(panel_path).name} voz={voice_used} trans={trans_name} sfx={sfx_name} persona={persona_name}")
        if is_impact:
            ok = effects_engine.build_clip_with_shake(panel_path, wav_path, clip_path, i, efx,
                                                      transition_type=transition_type, sfx_file=sfx_file,
                                                      overlay_video=overlay_video, mood=clip_mood)
        elif is_tension:
            # Shake suave em tensão (intensidade menor)
            ok = effects_engine.build_clip_with_shake(
                panel_path, wav_path, clip_path, i, efx,
                shake_intensity=5, shake_freq=8,
                transition_type=transition_type, sfx_file=sfx_file,
                overlay_video=overlay_video, mood=clip_mood)
        elif animated:
            ok = effects_engine.build_clip_animated(panel_path, wav_path, clip_path, i, efx,
                                                    transition_type=transition_type, sfx_file=sfx_file)
        else:
            ok = effects_engine.build_clip(panel_path, wav_path, clip_path, i, efx,
                                           transition_type=transition_type, sfx_file=sfx_file,
                                           overlay_video=overlay_video, mood=clip_mood)
        if ok:
            clips.append(clip_path)
            clip_texts.append(loc.get("text", ""))
            clip_personas.append(loc.get("persona", ""))
            clip_sensual.append(is_sensual)
            if _is_nsfw:
                cens_jobs.append({"clip": clip_path, "panel": panel_path, "wav": wav_path,
                                  "score": _cens_score, "kind": "full",
                                  "params": {"i": i, "is_impact": is_impact, "is_tension": is_tension,
                                             "animated": animated, "transition_type": transition_type,
                                             "sfx_file": sfx_file, "overlay_video": overlay_video,
                                             "clip_mood": clip_mood}})

            # Meme inteligente: insere meme com SFX entre clips
            clip_text = loc.get("text", "")
            clip_mood = effects_engine.detect_mood_from_text(clip_text) if clip_text else "neutral_chill"
            if effects_engine.should_insert_meme(i, clip_mood):
                meme_path = session_tmp / f"meme_{i:03d}.mp4"
                if effects_engine.build_meme_clip(meme_path):
                    clips.append(meme_path)
                    clip_texts.append("")
                    clip_personas.append("")
                    clip_sensual.append(False)
                    log(f"  🎭 Meme inserido após clip {i+1}")
            # Vídeo de transição (respiro visual entre cenas). Desligável via
            # env TRANSITION_VIDEOS=0. É um clip curto re-encodado que entra no
            # concat simples — não mexe no xfade (que já corrompeu áudio no passado).
            elif os.environ.get("TRANSITION_VIDEOS", "1") != "0" \
                    and effects_engine.should_insert_transition(i):
                trans_path = session_tmp / f"trans_{i:03d}.mp4"
                if effects_engine.build_transition_clip(trans_path):
                    clips.append(trans_path)
                    clip_texts.append("")
                    clip_personas.append("")
                    clip_sensual.append(False)
                    log(f"  🎬 Transição inserida após clip {i+1}")
        else:
            log(f"  ⚠ Clip {i} falhou, pulando")

    if not clips:
        log("✗ Nenhum clip gerado!")
        return None

    # 2b. Intro hook + outro CTA (branding) — opcional
    if branding:
        intro_path = session_tmp / "_intro.mp4"
        title_card = recap.get("titulo_video", titulo)
        if effects_engine.build_intro_clip(title_card, panel_files[0], intro_path,
                                           sfx_file=effects_engine.SFX_DIR / "riser.wav"):
            clips.insert(0, intro_path)
            clip_texts.insert(0, "")
            clip_personas.insert(0, "")
            clip_sensual.insert(0, False)
            log("  ✓ Intro adicionado")
        outro_path = session_tmp / "_outro.mp4"
        if effects_engine.build_outro_clip(outro_path,
                                           sfx_file=effects_engine.SFX_DIR / "bass_hit.wav"):
            clips.append(outro_path)
            clip_texts.append("")
            clip_personas.append("")
            clip_sensual.append(False)
            log("  ✓ Outro (CTA) adicionado")

    # 2c. Censura VISUAL na imagem (exodia fosco = leve, blur total 251 = forte) — reconstrói
    # SÓ os clips +18 a partir do painel censurado. clips_cens = clips com os +18 trocados;
    # mesmos params → duração idêntica → timeline igual → a censurada reusa as MESMAS legendas.
    clips_cens = list(clips)
    _n_cens = 0
    if censura and cens_jobs and _cv:
        log(f"  Censura visual: processando {len(cens_jobs)} painéis +18 (exodia/blur na imagem)...")
        for job in cens_jobs:
            try:
                cpanel = session_tmp / (Path(job["panel"]).stem + "_cens.jpg")
                niv = _cv.censurar_imagem(str(job["panel"]), str(cpanel), job["score"])
                if niv in (None, "intacto") or not Path(cpanel).exists():
                    continue
                cclip = Path(str(job["clip"])[:-4] + "_cens.mp4")
                if _render_cens_clip(job, cpanel, cclip) and Path(cclip).exists():
                    try:
                        clips_cens[clips_cens.index(job["clip"])] = cclip
                        _n_cens += 1
                        log(f"    ✓ {Path(job['panel']).name} → {niv} (score={job['score']:.2f})")
                    except ValueError:
                        pass
            except Exception as _e:
                log(f"    ⚠ falha ao censurar {Path(job['panel']).name}: {_e}")
        log(f"  ✓ Censura visual: {_n_cens}/{len(cens_jobs)} painéis censurados na imagem")

    # 3. Concat com transições (xfade entre clips)
    slug = re.sub(r"[^a-z0-9]+", "-", titulo.lower().strip())[:60]
    ts = datetime.now().strftime("%Y%m%d_%H%M")

    # Convenção: o vídeo mais recente SEMPRE tem o output_suffix e depois "_ULTIMO" no nome.
    # Rebaixa os "_ULTIMO" anteriores do mesmo slug (remove a marca + renomeia meta).
    for prev in VIDEOS_DIR.glob(f"hipercool_{slug}_*{output_suffix}_ULTIMO.mp4"):
        demoted = prev.with_name(prev.name.replace("_ULTIMO", ""))
        prev.rename(demoted)
        prev_meta = prev.with_suffix(".meta.json")
        if prev_meta.exists():
            prev_meta.rename(demoted.with_suffix(".meta.json"))

    out_name = f"hipercool_{slug}_{ts}{output_suffix}_ULTIMO.mp4"
    out_mp4 = VIDEOS_DIR / out_name

    log(f"  Concatenando {len(clips)} clips com transições + SFX...")
    _use_xfade = os.environ.get("XFADE_TRANSITIONS", "1") != "0"
    if _use_xfade and hasattr(effects_engine, "concat_with_xfade"):
        ok = effects_engine.concat_with_xfade(clips, out_mp4, descriptions=descriptions)
    else:
        ok = effects_engine.concat_with_transitions(clips, out_mp4, descriptions=descriptions)
    if not ok:
        log("✗ Concat falhou!")
        return None

    # 3b. Adicionar trilha sonora dinâmica (muda conforme clima)
    trilhas_dir = PROJECT_DIR / "workspace" / "assets" / "trilhas"
    if trilhas_dir.exists() and (trilhas_dir / "moods.json").exists():
        log("  Adicionando trilha dinâmica...")
        out_with_music = out_mp4.with_name(out_mp4.stem + "_music.mp4")
        effects_engine.add_dynamic_music(
            out_mp4, recap.get("locucoes", []), out_with_music,
            trilhas_dir, music_volume=0.18
        )
        if out_with_music.exists() and out_with_music.stat().st_size > 0:
            out_mp4.unlink()
            out_with_music.rename(out_mp4)
            log("  ✓ Trilha dinâmica adicionada")
    else:
        # Fallback: trilha única
        trilha_path = PROJECT_DIR / "workspace" / "assets" / "trilha.mp3"
        if trilha_path.exists():
            log("  Adicionando trilha sonora...")
            out_with_music = out_mp4.with_name(out_mp4.stem + "_music.mp4")
            effects_engine.add_background_music(out_mp4, trilha_path, out_with_music,
                                                music_volume=0.08)
            if out_with_music.exists() and out_with_music.stat().st_size > 0:
                out_mp4.unlink()
                out_with_music.rename(out_mp4)
                log("  ✓ Trilha adicionada")

    # 3c. Legendas queimadas estilo Shorts (Ponto F) — opcional via --subtitles
    subs = []  # hoisted: a versão censurada reusa exatamente estas legendas (timeline idêntica)
    if subtitles and clip_texts and TEST_MODE < 2:
        log("  Gerando legendas (estilo Shorts)...")
        # Duração real de cada clip → timing cumulativo das legendas
        entries = []
        total_clip_dur = 0.0
        for clip, txt in zip(clips, clip_texts):
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(clip)],
                    capture_output=True, text=True, timeout=10)
                dur = float(r.stdout.strip())
            except Exception:
                dur = 3.0
            entries.append((txt, dur))
            total_clip_dur += dur

        # Medir duração real do vídeo concatenado (que pode ser menor por causa do xfade)
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(out_mp4)],
                capture_output=True, text=True, timeout=10)
            real_video_dur = float(r.stdout.strip())
        except Exception:
            real_video_dur = total_clip_dur

        # Fator de compressão temporal (xfade encurta o vídeo)
        time_scale = real_video_dur / total_clip_dur if total_clip_dur > 0 else 1.0

        # Filtrar legendas: só narrador/narradora (falas de personagens já
        # estão nos balões do manhwa, legenda é redundante e tampa)
        narrator_entries = []
        t_cursor = 0.0
        for (txt, dur), persona in zip(entries, clip_personas):
            start = t_cursor * time_scale
            t_cursor += dur
            pclean = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona or "").strip().lower()
            if pclean in ("narrador", "narradora") and txt.strip():
                narrator_entries.append((txt, dur * time_scale, start))

        if narrator_entries:
            # Karaokê (palavra ativa amarela) ou estáticas (brancas)
            if hyperframes_karaoke:
                # MODO HYPERFRAMES: renderiza via Playwright/GSAP
                import render_karaoke
                log(f"  Karaokê HyperFrames (Playwright+GSAP)...")
                subs = []
                for idx, (txt, dur, start) in enumerate(narrator_entries):
                    webm_path = session_tmp / f"_hfk_{idx:03d}.webm"
                    result = render_karaoke.render_karaoke(
                        txt, str(webm_path), duration=dur,
                        width=1080, height=1920, font_size=65, stroke=8)
                    if result and Path(result).exists():
                        # Converter WebM → overlay no vídeo principal
                        # O WebM do Playwright não tem canal alpha real (fundo sólido)
                        # Então usamos a mesma abordagem de overlay com timing
                        subs.append({"webm": str(result), "start": start,
                                     "end": start + dur})
                # Se tiver WebMs, sobrepor via ffmpeg (filter_complex com movie+overlay)
                if subs:
                    log(f"  Queimando {len(subs)} overlays karaokê HyperFrames...")
                    out_hfk = out_mp4.with_name(out_mp4.stem + "_hfk.mp4")
                    _burn_webm_overlays(out_mp4, subs, out_hfk)
                    if out_hfk.exists() and out_hfk.stat().st_size > 0:
                        out_mp4.unlink()
                        out_hfk.rename(out_mp4)
                        log(f"  ✓ Karaokê HyperFrames queimado ({len(subs)} frases)")
                    else:
                        log("  ⚠ HyperFrames karaokê falhou, mantendo vídeo sem karaokê")
                else:
                    log("  ⚠ Nenhum WebM de karaokê gerado")
                # O karaokê HyperFrames já foi queimado no vídeo (overlays webm).
                # Zera subs pra que name tags + watermark (PNG) sigam num burn_subtitles
                # limpo — senão os dicts {"webm":...} causam KeyError 'png'.
                subs = []
            elif karaoke:
                # Legenda dinâmica estilo Shorts (1-2 palavras por vez) por padrão.
                # Desligável com SUB_SHORT=0 (volta ao karaokê de frase inteira).
                if os.environ.get("SUB_SHORT", "1") != "0":
                    subs = effects_engine.render_subtitles_short(
                        [(txt, dur) for txt, dur, _ in narrator_entries], session_tmp,
                        offsets=[s for _, _, s in narrator_entries])
                    log(f"  Legenda curta (1-2 palavras): {len(subs)} cards")
                else:
                    subs = effects_engine.render_subtitles_progressive(
                        [(txt, dur) for txt, dur, _ in narrator_entries], session_tmp,
                        offsets=[s for _, _, s in narrator_entries])
                    log(f"  Karaokê: {len(subs)} PNGs gerados (limite 150)")
            else:
                subs = effects_engine.render_subtitles(
                    [(txt, dur) for txt, dur, _ in narrator_entries], session_tmp,
                    offsets=[s for _, _, s in narrator_entries])
        else:
            subs = []

        # Name tags: nome do personagem que fala (acima da legenda).
        # DESATIVADO por padrão (v6+): as personas vinham GENÉRICAS (Homem/Mulher/Colega)
        # e apareciam na tela como se fossem legenda — era pra ser info interna.
        # Reative com SHOW_NAME_TAGS=1 (idealmente só quando houver nomes reais).
        t_cursor = 0.0
        for (txt, dur), persona in zip(entries, clip_personas):
            if os.environ.get("SHOW_NAME_TAGS", "0") != "1":
                break
            start = t_cursor
            t_cursor += dur
            pclean = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona or "").strip()
            if (pclean and txt.strip()
                    and pclean.lower() not in ("narrador", "narradora", "narrator", "personagem")):
                npng = session_tmp / f"_name_{int(start*100):05d}.png"
                res = effects_engine.render_name_tag(pclean, npng)
                if res:
                    _, nx, ny = res
                    subs.append({"png": str(npng), "x": nx, "y": ny,
                                 "start": start, "end": min(start + dur, start + 1.8)})
        # Watermark do canal (fixo no topo) junto com as legendas
        if branding:
            total_dur = sum(d for _, d in entries)
            wm = effects_engine.render_watermark(WATERMARK_HANDLE, session_tmp, total_dur)
            if wm:
                subs.append(wm)
        out_subs = out_mp4.with_name(out_mp4.stem + "_subs.mp4")
        if subs and effects_engine.burn_subtitles(out_mp4, subs, out_subs):
            out_mp4.unlink()
            out_subs.rename(out_mp4)
            log(f"  ✓ Legendas + watermark queimados")
        else:
            log("  ⚠ Falha ao queimar legendas (mantendo vídeo sem legenda)")
        # (limpeza dos PNGs de legenda movida pro fim: a versão censurada reusa estas subs)

    # 3c-bis. Upscale 720p → 1080p (Full HD de entrega)
    # MODO TESTE: TEST_MODE >= 1 pula upscale pra acelerar iteração
    if TEST_MODE < 1:
        log("  Upscalando 720p → 1080p...")
        upscaled = out_mp4.with_name(out_mp4.stem + "_hd.mp4")
        if effects_engine.upscale_to_fullhd(out_mp4, upscaled):
            out_mp4.unlink()
            upscaled.rename(out_mp4)
            log(f"  ✓ Upscale 720→1080p feito")
        else:
            log("  ⚠ Upscale falhou (mantendo 720p)")
    else:
        log("  [TEST_MODE] Upscale pulado (720p)")

    size_mb = out_mp4.stat().st_size / (1024 * 1024)
    log(f"  ✓ Vídeo final: {out_mp4.name} ({size_mb:.1f} MB)")

    # 3d. Versão CENSURADA pra Shorts — censura VISUAL na imagem (exodia fosco / blur total).
    # Monta a partir de clips_cens (só os +18 trocados pela imagem censurada). Timeline idêntica
    # ao principal → reusa a MESMA trilha e as MESMAS legendas (subs).
    if censura and _n_cens > 0:
        log(f"  Gerando versão censurada ({_n_cens} painéis +18 com exodia/blur na imagem)...")
        out_cens = out_mp4.with_name(out_mp4.stem.replace("_ULTIMO", "") + "_CENSURADO_ULTIMO.mp4")
        # a) concat (mesma lógica do principal)
        if _use_xfade and hasattr(effects_engine, "concat_with_xfade"):
            ok_c = effects_engine.concat_with_xfade(clips_cens, out_cens, descriptions=descriptions)
        else:
            ok_c = effects_engine.concat_with_transitions(clips_cens, out_cens, descriptions=descriptions)
        if ok_c and out_cens.exists():
            # b) trilha dinâmica (mesma do principal)
            _trilhas_dir = PROJECT_DIR / "workspace" / "assets" / "trilhas"
            if _trilhas_dir.exists() and (_trilhas_dir / "moods.json").exists():
                _cm = out_cens.with_name(out_cens.stem + "_music.mp4")
                effects_engine.add_dynamic_music(out_cens, recap.get("locucoes", []), _cm,
                                                 _trilhas_dir, music_volume=0.18)
                if _cm.exists() and _cm.stat().st_size > 0:
                    out_cens.unlink(); _cm.rename(out_cens)
            # c) legendas — reusa as MESMAS do principal (timeline idêntica)
            if subs:
                _cs = out_cens.with_name(out_cens.stem + "_subs.mp4")
                if effects_engine.burn_subtitles(out_cens, subs, _cs) and _cs.exists():
                    out_cens.unlink(); _cs.rename(out_cens)
            # d) upscale 720p → 1080p (entrega Full HD)
            if TEST_MODE < 1:
                _cu = out_cens.with_name(out_cens.stem + "_hd.mp4")
                if effects_engine.upscale_to_fullhd(out_cens, _cu) and _cu.exists():
                    out_cens.unlink(); _cu.rename(out_cens)
            log(f"  ✓ Versão censurada: {out_cens.name}")
        else:
            log("  ⚠ Falha ao concatenar versão censurada")
    elif censura and cens_jobs:
        log(f"  ⚠ Censura: {len(cens_jobs)} painéis +18 detectados mas nenhum clip censurado gerado")
    elif censura:
        log("  (Censura: nenhum painel +18 detectado neste capítulo)")

    # Limpeza dos PNGs de legenda (após a censurada reusar as subs)
    for s in subs:
        try:
            Path(s.get("png", "")).unlink()
        except Exception:
            pass

    # Salvar meta
    meta = {
        "titulo": titulo,
        "titulo_video": recap.get("titulo_video", titulo),
        "tags": recap.get("tags", []),
        "panels_count": len(clips),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file": out_name,
        "size_mb": round(size_mb, 1),
        "quality_profile": os.environ.get("QUALITY_PROFILE", "standard"),
        "tts_engine": os.environ.get("TTS_ENGINE", "edge"),
        "features": {
            "subtitles": subtitles,
            "karaoke": karaoke,
            "audio_enhancement": True,
            "viral_filters": True,
            "sfx_contextual": True,
            "foley_direct": True,
            "overlays_atmospheric": True,
        },
    }
    meta_path = out_mp4.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    # 4. Notify
    if not skip_notify:
        log("  Enviando pro Telegram...")
        caption = (
            f"🎬 {_tg_safe.b(recap.get('titulo_video', titulo))}\n"
            f"📊 {len(clips)} painéis | {size_mb:.1f} MB\n"
            f"🏷 {', '.join(recap.get('tags', [])[:5])}"
        )
        _tg_safe.send_video(str(out_mp4), caption=caption)

    # Cleanup tmp
    try:
        import shutil
        shutil.rmtree(session_tmp)
    except Exception:
        pass

    # 4. Auto-validação (roda sempre, só loga — desativável com AUTO_VALIDATE=0)
    if os.environ.get("AUTO_VALIDATE", "1") == "1":
        try:
            import importlib.util
            validate_path = Path(__file__).resolve().parent / "auto-validate.py"
            if validate_path.exists():
                spec = importlib.util.spec_from_file_location("auto_validate", validate_path)
                av = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(av)
                result = av.validate(str(out_mp4))
                if result["status"] == "OK":
                    log(f"  ✅ Auto-validação: APROVADO")
                else:
                    log(f"  ⚠️ Auto-validação: {len(result['problemas'])} problema(s)")
                    for p in result["problemas"]:
                        log(f"     - {p}")
                    # Quarentena: problemas graves → mover pra pasta separada
                    grave = any("dessincronizado" in p or "silencioso" in p or "tela preta" in p
                               for p in result["problemas"])
                    if grave:
                        quarentena_dir = VIDEOS_DIR / "_quarentena"
                        quarentena_dir.mkdir(exist_ok=True)
                        dest = quarentena_dir / out_mp4.name
                        out_mp4.rename(dest)
                        log(f"  🚫 Vídeo movido pra quarentena: {dest.name}")
                        out_mp4 = dest
        except Exception as e:
            log(f"  ⚠ Auto-validação falhou: {e}")

    return out_mp4


def run_batch(urls, args):
    """Processa vários capítulos em sequência (Ponto K), com retomada.

    Salva progresso em workspace/batch_progress.json. URLs já concluídas com
    sucesso são puladas em execuções seguintes (retoma após queda). Uma falha
    num capítulo NÃO interrompe o lote — registra e segue pro próximo.
    """
    import importlib.util
    fetcher_path = Path(__file__).resolve().parent / "hiper-fetcher.py"
    spec = importlib.util.spec_from_file_location("hiper_fetcher", fetcher_path)
    hiper_fetcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hiper_fetcher)

    progress_file = PROJECT_DIR / "workspace" / "batch_progress.json"
    try:
        progress = json.loads(progress_file.read_text()) if progress_file.exists() else {}
    except Exception:
        progress = {}

    total = len(urls)
    log(f"═══ LOTE: {total} capítulos ═══")
    done, failed, skipped = 0, 0, 0

    for idx, url in enumerate(urls, start=1):
        if progress.get(url, {}).get("status") == "done":
            log(f"[{idx}/{total}] ⏭  já concluído, pulando: {url}")
            skipped += 1
            continue

        slug = hiper_fetcher.slugify(url.split("/")[-1] or url.split("/")[-2] or "chapter")
        # Título por capítulo: base + sufixo do slug (ex: "... cap 3")
        cap_titulo = f"{args.titulo} — {slug}" if total > 1 else args.titulo
        log(f"[{idx}/{total}] ▶ {url}")

        try:
            panels = hiper_fetcher.fetch_chapter(url, slug, headed=args.headed)
            if not panels:
                raise RuntimeError("scrape retornou vazio")

            result = run_pipeline(
                panels, cap_titulo,
                max_panels=args.max_panels,
                skip_notify=args.skip_notify,
                dry_run=args.dry_run,
                animated=args.animated,
                start_panel=args.start_panel,
                fusao=args.fusao,
                narrator_gender=args.narrator_gender,
                subtitles=args.subtitles,
                branding=args.branding,
                karaoke=args.karaoke,
                censura=args.censura,
                force_llm=args.force_llm,
                force_tts=args.force_tts,
                hyperframes_karaoke=args.hyperframes_karaoke,
                output_suffix=args.output_suffix,
            )
            if result:
                progress[url] = {"status": "done", "file": str(result),
                                 "at": datetime.now(timezone.utc).isoformat()}
                done += 1
                log(f"[{idx}/{total}] ✓ pronto: {Path(result).name}")
            else:
                raise RuntimeError("pipeline retornou None")
        except Exception as e:
            progress[url] = {"status": "failed", "error": str(e),
                             "at": datetime.now(timezone.utc).isoformat()}
            failed += 1
            log(f"[{idx}/{total}] ✗ falhou: {e}")

        # Salva progresso após CADA capítulo (retomável)
        try:
            progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2))
        except Exception:
            pass

    log(f"═══ LOTE FIM: {done} ok, {failed} falhas, {skipped} pulados ═══")
    if failed:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Pipeline de vídeo hipercool")
    parser.add_argument("--url", help="URL do capítulo (scrape + pipeline)")
    parser.add_argument("--slug", help="Slug de capítulo já no cache")
    parser.add_argument("--panels-dir", help="Diretório com painéis já cortados")
    parser.add_argument("--titulo", "-t", required=True, help="Título do manhwa/capítulo")
    parser.add_argument("--max-panels", type=int, default=MAX_PANELS_DEFAULT,
                        help=f"Máximo de painéis (default: {MAX_PANELS_DEFAULT})")
    parser.add_argument("--start-panel", type=int, default=0,
                        help="Offset de início (parte 2+ do capítulo; ex: 55)")
    parser.add_argument("--skip-notify", action="store_true",
                        help="Não enviar notificação Telegram")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria feito sem executar")
    parser.add_argument("--animated", action="store_true",
                        help="Usa modo animado (breathing/parallax) nos painéis")
    parser.add_argument("--fusao", action="store_true",
                        help="TESTE: funde visão+narração numa só chamada Gemini")
    parser.add_argument("--narrator-gender", choices=["M", "F"], default="F",
                        help="Gênero da narradora off (default F)")
    parser.add_argument("--subtitles", action="store_true",
                        help="Queima legendas estilo Shorts no vídeo")
    parser.add_argument("--karaoke", action="store_true",
                        help="Legendas progressivas (palavra ativa destacada). Requer --subtitles")
    parser.add_argument("--no-branding", dest="branding", action="store_false",
                        help="Desliga intro/outro (CTA inscreva-se)")
    parser.add_argument("--censura", action="store_true",
                        help="Gera também versão censurada (mosaico nos painéis +18) pra Shorts")
    parser.add_argument("--headed", action="store_true",
                        help="Browser visível (se usar --url)")
    # Ponto K: lote multi-capítulo
    parser.add_argument("--urls", nargs="+", metavar="URL",
                        help="Lote: várias URLs de capítulos processadas em sequência")
    parser.add_argument("--batch-file", metavar="ARQUIVO",
                        help="Lote: arquivo de texto com 1 URL por linha (# = comentário)")
    # Flags de rebuild/cache
    parser.add_argument("--force-llm", action="store_true",
                        help="Ignora narration_cache, força nova geração de narração via LLM")
    parser.add_argument("--force-tts", action="store_true",
                        help="Ignora tts_cache, força nova geração de áudio TTS")
    parser.add_argument("--hyperframes-karaoke", action="store_true",
                        help="Usa render_karaoke.py (Playwright) para legendas HyperFrames")
    parser.add_argument("--output-suffix", default="",
                        help="Sufixo no nome do vídeo final (ex: _NORMAL, _HYPERFRAMES)")

    args = parser.parse_args()

    # ── Modo LOTE (Ponto K) ────────────────────────────────────────────────
    batch_urls = []
    if args.urls:
        batch_urls = list(args.urls)
    elif args.batch_file:
        bf = Path(args.batch_file)
        if not bf.is_file():
            print(f"ERRO: batch-file '{bf}' não existe", file=sys.stderr)
            sys.exit(1)
        for line in bf.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                batch_urls.append(line)

    if batch_urls:
        run_batch(batch_urls, args)
        return

    # Determinar source dos painéis
    panels_dir = None

    if args.panels_dir:
        panels_dir = Path(args.panels_dir)
        if not panels_dir.is_dir():
            print(f"ERRO: {panels_dir} não existe", file=sys.stderr)
            sys.exit(1)

    elif args.slug:
        cache_path = CACHE_DIR / args.slug
        if not cache_path.is_dir():
            print(f"ERRO: slug '{args.slug}' não encontrado no cache", file=sys.stderr)
            sys.exit(1)
        panels_dir = cache_path

    elif args.url:
        # Importar fetcher (mesmo diretório bin/)
        import importlib.util
        fetcher_path = Path(__file__).resolve().parent / "hiper-fetcher.py"
        spec = importlib.util.spec_from_file_location("hiper_fetcher", fetcher_path)
        hiper_fetcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hiper_fetcher)

        slug = args.slug or hiper_fetcher.slugify(args.url.split("/")[-1] or "chapter")
        result = hiper_fetcher.fetch_chapter(args.url, slug, headed=args.headed)
        if not result:
            print("ERRO: Falha ao baixar capítulo", file=sys.stderr)
            sys.exit(1)
        panels_dir = result

    else:
        print("ERRO: forneça --url, --slug, ou --panels-dir", file=sys.stderr)
        sys.exit(1)

    result = run_pipeline(
        panels_dir, args.titulo,
        max_panels=args.max_panels,
        skip_notify=args.skip_notify,
        dry_run=args.dry_run,
        animated=args.animated,
        start_panel=args.start_panel,
        fusao=args.fusao,
        narrator_gender=args.narrator_gender,
        subtitles=args.subtitles,
        branding=args.branding,
        karaoke=args.karaoke,
        censura=args.censura,
        force_llm=args.force_llm,
        force_tts=args.force_tts,
        hyperframes_karaoke=args.hyperframes_karaoke,
        output_suffix=args.output_suffix,
    )

    if result:
        print(f"\n✓ Vídeo pronto: {result}")
    elif not args.dry_run:
        print("\n✗ Pipeline falhou.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

