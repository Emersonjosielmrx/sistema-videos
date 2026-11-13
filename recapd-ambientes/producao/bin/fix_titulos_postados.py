"""fix_titulos_postados.py — Corrige títulos em inglês de vídeos já postados.

Usa YouTube Data API videos.update pra trocar título/descrição/tags
dos 6 vídeos que foram postados com títulos em inglês por engano.
"""
import json, os, sys, re, time
import urllib.request, urllib.error, urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gemini_llm

CREDS_FILE = Path(r"D:\credenciais-canais\youtube_canais.json")
TOKEN_URL = "<SEGREDO_REMOVIDO>"

VIDEOS_CORRIGIR = [
    {
        "video_id": "Bxa9hzCd7v4",
        "canal": "InovareManhwaVerse",
        "folder": "7X-WbtJhojk_He_was_Bullied_As_the_Weakest_E_Rank_Hun",
        "is_short": False,
    },
    {
        "video_id": "466ayOSkDUU",
        "canal": "InovareManhwaVerse",
        "folder": "X5r9llgHfqo_Elemental_Explained_By_An_Asian",
        "is_short": False,
    },
    {
        "video_id": "hfNnr04NA_s",
        "canal": "InovareManhwaVerse",
        "folder": "may2s9j4RLk_The_myth_behind_the_Chinese_zodiac___Meg",
        "is_short": False,
    },
    {
        "video_id": "CUcypy3HVD0",
        "canal": "InovareManhwaVerse",
        "folder": "yI7eqsXSoWU_CYBERPUNK__EDGERUNNERS_IS_RUTHLESS",
        "is_short": False,
    },
    {
        "video_id": "1UHPL9Zkml0",
        "canal": "Inovare inteligência artificial",
        "folder": "0h1eoBeR4Jk_Book_of_Ruth_Summary__A_Complete_Animate",
        "is_short": True,
    },
    {
        "video_id": "s2bRYe71-Wo",
        "canal": "Inovare inteligência artificial",
        "folder": "26EivpCPHnQ_Three_Kingdoms___OverSimplified",
        "is_short": True,
    },
]

ANIME_DIR = Path(r"D:\recapd-ambientes\producao\workspace\anime")

_PROMPT = """Você é um especialista em YouTube SEO para vídeos de anime/animação em PORTUGUÊS BRASILEIRO.

Dado o resumo abaixo de um recap de anime/animação, gere metadados para postagem no YouTube.

REGRAS OBRIGATÓRIAS:
- Título DEVE ser em PORTUGUÊS BRASILEIRO
- NUNCA usar o nome real do anime/obra (copyright)
- Título deve ser VIRAL: curiosidade, ganchos emocionais, superação
- Usar emojis estratégicos (1-2 no máximo)
- Título entre 40 e 80 caracteres
- Descrição com 2-3 frases + CTA + hashtags genéricas
- Tags relevantes ao gênero (sem nome da obra)
{extra}

Responda SOMENTE com JSON válido, sem markdown:
{{"titulo": "...", "descricao": "...", "tags": ["tag1", "tag2", ...]}}

RESUMO DO VÍDEO (primeiras linhas do roteiro):
{resumo}"""

_TITULOS_FALLBACK = [
    "Ele Foi Humilhado Por Ser o Mais Fraco... Até Despertar! 🔥",
    "Todos Riram Dele... Até Descobrirem Seu Verdadeiro Poder",
    "A Cena Mais Épica Que Você Vai Ver Hoje 💀",
    "A Maior Reviravolta Desse Anime Te Deixa Sem Palavras",
    "Ninguém Acreditava Nele... Até Esse Momento",
    "Esse Recap Vai Te Surpreender do Início ao Fim 🔥",
]

def _load_canais():
    return json.loads(CREDS_FILE.read_text(encoding="utf-8"))

def _find_canal(canais, nome):
    for c in canais:
        if c["nome"].strip().lower() == nome.strip().lower():
            return c
    for c in canais:
        if nome.strip().lower() in c["nome"].strip().lower():
            return c
    return None

def refresh_access_token(canal):
    data = urllib.parse.urlencode({
        "client_id": canal["clientId"],
        "client_secret": canal["clientSecret"],
        "refresh_token": canal["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]

def update_video(video_id, titulo, descricao, tags, token, category_id="24"):
    """YouTube Data API: videos.update (snippet)."""
    url = "https://www.googleapis.com/youtube/v3/videos?part=snippet"
    body = {
        "id": video_id,
        "snippet": {
            "title": titulo[:100],
            "description": descricao[:5000],
            "tags": tags[:15] if isinstance(tags, list) else [t.strip() for t in tags.split(",")][:15],
            "categoryId": category_id,
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PUT", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def _parse_llm_json(text):
    if not text:
        return None
    text = text.strip()
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        text = m.group(1)
    elif not text.startswith('{'):
        m2 = re.search(r'\{.*\}', text, re.DOTALL)
        if m2:
            text = m2.group(0)
        else:
            return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

def gerar_titulo_llm(folder, is_short):
    roteiro_path = ANIME_DIR / folder / "roteiro.txt"
    if not roteiro_path.exists():
        return None
    lines = roteiro_path.read_text(encoding='utf-8', errors='replace').strip().splitlines()
    resumo = "\n".join(lines[:15])
    extra = '- Incluir #shorts no final do título\n- Título max 60 chars' if is_short else ''
    prompt = _PROMPT.format(resumo=resumo, extra=extra)
    resp = gemini_llm.generate_text(prompt, max_tokens=512, temperature=0.9)
    parsed = _parse_llm_json(resp)
    if parsed and parsed.get("titulo"):
        return parsed
    return None

def main():
    canais = _load_canais()
    tokens_cache = {}
    fb_idx = 0

    for i, v in enumerate(VIDEOS_CORRIGIR):
        print(f"\n[{i+1}/{len(VIDEOS_CORRIGIR)}] {v['video_id']} ({v['canal']}) — {v['folder'][:50]}")

        meta = gerar_titulo_llm(v["folder"], v["is_short"])
        if meta:
            titulo = meta["titulo"]
            descricao = meta.get("descricao", "")
            tags = meta.get("tags", ["anime", "recap"])
            print(f"   LLM: \"{titulo}\"")
        else:
            titulo = _TITULOS_FALLBACK[fb_idx % len(_TITULOS_FALLBACK)]
            fb_idx += 1
            if v["is_short"]:
                titulo = titulo[:55] + " #shorts"
            descricao = "Inscreva-se para mais resumos incríveis!\n\n#anime #recap #otaku"
            tags = ["anime", "recap", "resumo", "otaku", "animação"]
            print(f"   Fallback: \"{titulo}\"")

        if v["is_short"] and "#shorts" not in titulo.lower():
            titulo = titulo[:55] + " #shorts"

        canal_nome = v["canal"]
        if canal_nome not in tokens_cache:
            canal_obj = _find_canal(canais, canal_nome)
            if not canal_obj:
                print(f"   ERRO: canal '{canal_nome}' não encontrado!")
                continue
            tokens_cache[canal_nome] = refresh_access_token(canal_obj)

        token = tokens_cache[canal_nome]
        try:
            result = update_video(v["video_id"], titulo, descricao, tags, token)
            new_title = result.get("snippet", {}).get("title", "?")
            print(f"   ✓ Atualizado: \"{new_title}\"")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            print(f"   ERRO HTTP {e.code}: {body[:200]}")
        except Exception as e:
            print(f"   ERRO: {e}")

        time.sleep(1)

    print("\n=== CONCLUÍDO ===")

if __name__ == '__main__':
    main()
