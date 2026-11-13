"""postar_animes_ate_bloquear.py — Posta TODOS os pendentes de animes enquanto canais aceitam.

Gera postar.json (título viral PT-BR via LLM) antes de postar.
NUNCA usa o nome original da pasta (que vem em inglês do YouTube fonte).
"""
import json, os, sys, subprocess, re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Adiciona bin/ ao path pra importar gemini_llm
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gemini_llm

CANAIS_MANHWA = [
    "InovareManhwaVerse",
    "inovaremanhwabr",
    "Animescomia",
    "Inovare Manhwa esp",
    "inovare Manhwa french",
    "Inovaremanhwaversehindi",
    "Inovare Manhwa eng",
    "inovaremanhwaverseita",
    "inovare manhwa verse ru",
    "Inovaremanhwaversethai",
    "@Inovaremanhwaversethai",
]
CANAIS_OUTROS = [
    "Inovare inteligência artificial",
    "Inovare com ia",
    "Game of thrones kingsroad brasil",
    "fake News ia",
    "fofos e absurdos",
    "@IAAgora-h3n",
    "@IAAgora-n7h",
    "@UniversoIA-d6s",
    "@IASemLimites-h4b",
    "@CodigoInteligente-n7j",
    "@MenteArtificial-i5r",
]
CANAIS = CANAIS_MANHWA + CANAIS_OUTROS
ROOT = Path(r'D:\recapd-ambientes\producao')
LOG = ROOT / 'logs/videos_postados.json'
POSTER = r'D:\recapd-ambientes\producao\venv\Scripts\python.exe'
YOUTUBE = str(Path(__file__).resolve().parent / "youtube_poster.py")

def _norm(p):
    return str(Path(p).resolve())

def carregar_postados():
    if LOG.exists():
        raw = json.load(open(LOG, encoding='utf-8'))
        return set(_norm(p) for p in raw)
    return set()
def salvar_postado(p):
    s = carregar_postados(); s.add(_norm(p))
    LOG.parent.mkdir(parents=True, exist_ok=True)
    json.dump(sorted(s), open(LOG, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    arquivar(p)
def arquivar(video_path):
    import shutil
    p = str(video_path)
    try:
        rel = Path(p).relative_to(ROOT)
    except ValueError:
        return
    dest = ROOT / 'postados' / 'anime' / Path(*rel.parts[1:])
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        try: Path(p).unlink()
        except: pass
    else:
        try: shutil.move(p, str(dest))
        except: pass
def is_quota_err(out, err):
    text = (out or '') + (err or '')
    return any(k in text for k in ['uploadLimitExceeded', 'rateLimitExceeded', 'quotaExceeded'])

# ─── Geração de título/descrição via LLM ─────────────────────────────────────

_PROMPT_TITULO = """Você é um especialista em YouTube SEO para vídeos de anime/animação em PORTUGUÊS BRASILEIRO.

Dado o resumo abaixo de um recap de anime/animação, gere metadados para postagem no YouTube.

REGRAS OBRIGATÓRIAS:
- Título DEVE ser em PORTUGUÊS BRASILEIRO
- NUNCA usar o nome real do anime/obra (copyright)
- Título deve ser VIRAL: curiosidade, ganchos emocionais, superação
- Usar emojis estratégicos (1-2 no máximo)
- Título entre 40 e 80 caracteres
- Descrição com 2-3 frases + CTA + hashtags genéricas
- Tags relevantes ao gênero (sem nome da obra)

Responda SOMENTE com JSON válido, sem markdown:
{{"titulo": "...", "descricao": "...", "tags": ["tag1", "tag2", ...]}}

RESUMO DO VÍDEO (primeiras linhas do roteiro):
"""

_PROMPT_TITULO_SHORT = """Você é um especialista em YouTube Shorts SEO para anime/animação em PORTUGUÊS BRASILEIRO.

Dado o resumo abaixo, gere metadados para um SHORT (vídeo curto vertical).

REGRAS:
- Título em PORTUGUÊS BRASILEIRO, VIRAL, curto (max 60 chars)
- NUNCA usar o nome real do anime/obra
- Incluir #shorts no final do título
- Tags com #anime #shorts obrigatório
- Descrição curta (1-2 frases)

Responda SOMENTE com JSON válido, sem markdown:
{{"titulo": "...", "descricao": "...", "tags": ["tag1", "tag2", ...]}}

RESUMO:
"""

def _extrair_resumo(video_path, max_linhas=15):
    """Lê as primeiras linhas do roteiro.txt da pasta do vídeo."""
    roteiro = video_path.parent / "roteiro.txt"
    if not roteiro.exists():
        return None
    try:
        lines = roteiro.read_text(encoding='utf-8', errors='replace').strip().splitlines()
        return "\n".join(lines[:max_linhas])
    except:
        return None

def _parse_llm_json(text):
    """Extrai JSON de resposta LLM (que pode vir com ```json ... ```)."""
    if not text:
        return None
    text = text.strip()
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        text = m.group(1)
    elif text.startswith('{'):
        pass
    else:
        m2 = re.search(r'\{.*\}', text, re.DOTALL)
        if m2:
            text = m2.group(0)
        else:
            return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

_TITULOS_FALLBACK = [
    "Ele Foi Humilhado Por Ser o Mais Fraco... Até Despertar!",
    "Todos Riram Dele... Até Descobrirem Seu Verdadeiro Poder 🔥",
    "O Mais Fraco Se Tornou o Mais Temido de Todos",
    "Ninguém Acreditava Nele... Até Esse Momento Épico",
    "De Zero a Lenda: A Jornada Mais Insana do Anime",
    "Ele Fingiu Ser Fraco e Surpreendeu a Todos 💀",
    "A Maior Reviravolta Que Você Vai Ver Hoje",
    "Esse Recap Vai Te Deixar Sem Palavras 🔥",
    "O Poder Escondido Que Ninguém Esperava",
    "Quando o Mais Fraco Se Torna Invencível",
    "A Cena Que Fez Todo Mundo Chorar 😭",
    "Esse Anime é Mais Brutal do Que Você Imagina",
]
_fallback_idx = 0

def gerar_postar_json(video_path):
    """Gera postar.json com título/descrição/tags via LLM. Retorna dict ou None."""
    pj_path = video_path.parent / "postar.json"

    if pj_path.exists():
        try:
            data = json.loads(pj_path.read_text(encoding='utf-8'))
            if data.get("titulo") and data.get("pronto"):
                return data
        except:
            pass

    is_short = "short" in video_path.name
    resumo = _extrair_resumo(video_path)

    titulo, descricao, tags = None, None, None

    if resumo:
        prompt = (_PROMPT_TITULO_SHORT if is_short else _PROMPT_TITULO) + resumo
        try:
            resp = gemini_llm.generate_text(prompt, max_tokens=512, temperature=0.9)
            parsed = _parse_llm_json(resp)
            if parsed:
                titulo = parsed.get("titulo", "")
                descricao = parsed.get("descricao", "")
                tags = parsed.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",")]
        except Exception as e:
            print(f"   LLM falhou: {e}")

    if not titulo or len(titulo) < 10:
        global _fallback_idx
        titulo = _TITULOS_FALLBACK[_fallback_idx % len(_TITULOS_FALLBACK)]
        _fallback_idx += 1
        if is_short:
            titulo = titulo[:55] + " #shorts"

    if not descricao:
        descricao = (
            "Inscreva-se para mais resumos de animes e animações incríveis!\n\n"
            "#anime #recap #otaku #animação #resumo"
        )

    if not tags:
        tags = ["anime", "recap", "resumo", "otaku", "animação", "ia", "portugues"]

    if is_short and "#shorts" not in titulo.lower():
        titulo = titulo[:55] + " #shorts"

    if len(titulo) > 100:
        titulo = titulo[:97] + "..."

    tags = [t.strip().lstrip("#") for t in tags if t.strip()][:15]

    data = {
        "arquivo": video_path.name,
        "categoria": "anime",
        "tipo": "short" if is_short else "completo",
        "titulo": titulo,
        "descricao": descricao,
        "tags": tags,
        "pronto": True,
        "_fonte_caption": "llm" if resumo else "fallback",
    }

    try:
        pj_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"   📝 postar.json gerado: \"{titulo}\"")
    except Exception as e:
        print(f"   ⚠ Erro gravando postar.json: {e}")

    return data


def listar_prontos():
    prontos = []
    anime_dir = ROOT / 'workspace/anime'
    for nome in ("final_anime_deitado_ads.mp4", "final_anime_short.mp4", "final_anime_deitado.mp4"):
        for p in anime_dir.rglob(nome):
            if p.parent != anime_dir:
                prontos.append(p)
    resultado = []
    ads_folders = set(str(p.parent) for p in prontos if "ads" in p.name)
    for p in prontos:
        if p.name == "final_anime_deitado.mp4" and str(p.parent) in ads_folders:
            continue
        resultado.append(p)
    return resultado

def postar(video_path, canal, meta):
    """Posta usando metadados do postar.json (meta dict)."""
    titulo = meta["titulo"]
    descricao = meta.get("descricao", "")
    tags = ",".join(meta.get("tags", ["anime", "recap"]))

    cmd = [POSTER, YOUTUBE, '--video', str(video_path), '--titulo', titulo,
           '--descricao', descricao, '--tags', tags, '--canal', canal]
    env = os.environ.copy(); env['PYTHONUTF8'] = '1'
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=180)

def _canais_para(video):
    """Grandes (deitado/ads) -> manhwa primeiro; shorts -> outros primeiro."""
    is_short = "short" in video.name
    if is_short:
        return CANAIS_OUTROS + CANAIS_MANHWA
    return CANAIS_MANHWA + CANAIS_OUTROS

def _tentar_postar(video, lista_canais, canais_bloqueados, meta):
    """Tenta postar no primeiro canal disponível da lista. Retorna (ok, canal_ou_None)."""
    for canal in lista_canais:
        if canal in canais_bloqueados:
            continue
        try:
            proc = postar(video, canal, meta)
        except Exception as e:
            print(f"   EXC em '{canal}': {e}")
            continue
        out = proc.stdout or ''; err = proc.stderr or ''
        if proc.returncode == 0 and ('Video id' in out or 'youtu.be' in out):
            print(f"   OK [{canal}]: {out.strip()[:120]}")
            return True, canal
        elif is_quota_err(out, err):
            print(f"   LIMITE em '{canal}'.")
            canais_bloqueados.add(canal)
        else:
            print(f"   ERRO em '{canal}': {(err or out).strip()[:200]}")
    return False, None

def main():
    postados = carregar_postados()
    prontos = listar_prontos()
    pendentes = [p for p in prontos if _norm(p) not in postados]
    grandes = [p for p in pendentes if "short" not in p.name]
    shorts = [p for p in pendentes if "short" in p.name]
    grandes.sort(key=str); shorts.sort(key=str)
    pendentes = grandes + shorts
    print(f"Total prontos: {len(prontos)} | ja postados: {len(postados)} | pendentes: {len(pendentes)} (grandes: {len(grandes)}, shorts: {len(shorts)})")
    if not pendentes:
        print("Nada a postar.")
        return
    sucessos = 0; falhas = 0
    limite_atingido = False
    canais_bloqueados = set()
    for i, video in enumerate(pendentes):
        if len(canais_bloqueados) >= len(CANAIS):
            print(f"Todos os canais bloqueados. Saindo."); limite_atingido = True; break
        lista = _canais_para(video)
        tipo = "SHORT" if "short" in video.name else "GRANDE"
        print(f"\n[{i+1}/{len(pendentes)}] ({tipo}) {video.name} <- {video.parent.name}")

        meta = gerar_postar_json(video)
        if not meta:
            print(f"   ⚠ Sem metadados, pulando.")
            falhas += 1
            continue

        ok, canal = _tentar_postar(video, lista, canais_bloqueados, meta)
        if ok:
            salvar_postado(video); sucessos += 1
        else:
            falhas += 1
    print(f"\n=== RESUMO ===")
    print(f"Sucessos: {sucessos}")
    print(f"Falhas: {falhas}")
    print(f"Limite atingido: {limite_atingido}")
    print(f"Canais bloqueados: {sorted(canais_bloqueados)}")

if __name__ == '__main__':
    main()
