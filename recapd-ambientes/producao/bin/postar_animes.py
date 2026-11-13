import json
import os
import subprocess
import time
import random
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from viralizador import anti_ban
except Exception:
    def anti_ban(t):
        return t

try:
    import seo_generator
except Exception:
    seo_generator = None

try:
    import studio_extras_anime
except Exception:
    studio_extras_anime = None

# Canais de animes puros / IA em português
CANAIS = [
    "repost canalanimescomia",
    "YouTube inovaremanhwaverseesp"
]

ROOT_DIR = Path("d:/recapd-ambientes/producao")
VIDEOS_DIR = ROOT_DIR / "workspace/anime"
POSTADOS_LOG = ROOT_DIR / "logs/videos_postados.json"
POSTER = "D:/recapd-ambientes/producao/venv/Scripts/python.exe"
YOUTUBE_POSTER = str(Path(__file__).resolve().parent / "youtube_poster.py")

# ── SEO: tags base (24 fixas — otimizadas pra buscas PT-BR de anime recap) ──
TAGS_ANIME_BASE = [
    "anime", "recap anime", "anime recap", "resumo anime",
    "anime recap portugues", "recap anime pt-br", "anime pt-br",
    "resumo de anime", "anime recap completo",
    "isekai", "anime isekai", "anime ação", "anime magia",
    "anime fantasia", "reencarnação anime",
    "recap completo", "resumo completo", "anime dublado",
    "anime em português", "anime legendado",
    "animes 2025", "animes 2026", "anime novo",
    "animê", "anine",
]

HASHTAGS_FIXAS = "#anime #animerecap #recap"
HASHTAGS_ROTATIVAS = [
    "#isekai", "#ação", "#magia", "#reencarnado", "#resumoanime",
    "#animebr", "#animerecapbr", "#manhwa",
]

TEMPLATES_TITULO = [
    "Ele Foi Chamado de LIXO Até Despertar o PODER Mais Forte do Mundo",
    "Ele NASCEU Fraco Mas Se Tornou o Guerreiro MAIS FORTE de Todos",
    "TODOS Riram Dele Até Ele Mostrar Seu Verdadeiro PODER",
    "Garoto REJEITADO Renasceu Com Uma HABILIDADE de Nível DEUS",
    "Ele PERDEU Tudo e Voltou Com o PODER ABSOLUTO",
    "NINGUÉM Acreditava Nele Até Ele Se Tornar INDESTRUTÍVEL",
    "O MAIS FRACO Recebeu Um PODER Secreto e Surpreendeu a Todos",
    "Ele Era DESCARTADO Até Ganhar a SKILL Mais Rara do Mundo",
    "Após Ser TRAÍDO Ele Voltou 1000x MAIS FORTE Para Se Vingar",
    "O Garoto Que TODOS Desprezavam Se Tornou o LORDE Mais Temido",
]


def _extrair_vid_e_titulo(folder_name):
    """Extrai video_id e título original do nome da pasta (formato: VID_slug_titulo)."""
    parts = folder_name.split("_", 1)
    vid = parts[0] if parts else ""
    slug = parts[1] if len(parts) > 1 else folder_name
    titulo_raw = slug.replace("_", " ").strip()
    return vid, titulo_raw


def _buscar_meta_original(vid):
    """Tenta pegar título, descrição e tags do vídeo original via yt-dlp."""
    if not vid or len(vid) < 8:
        return None
    url = f"https://www.youtube.com/watch?v={vid}"
    try:
        proc = subprocess.run(
            ["yt-dlp", "--skip-download", "--no-warnings", "-q",
             "--print", "%(title)s\x1f%(description)s\x1f%(tags)s", url],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        parts = proc.stdout.strip().split("\x1f", 2)
        if len(parts) < 3:
            return None
        tags_raw = parts[2].strip()
        if tags_raw.startswith("["):
            import ast
            try:
                tag_list = ast.literal_eval(tags_raw)
            except Exception:
                tag_list = [t.strip().strip("'\"") for t in tags_raw.strip("[]").split(",") if t.strip()]
        else:
            tag_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
        return {
            "title": parts[0].strip(),
            "description": parts[1].strip()[:500],
            "tags": tag_list[:15],
        }
    except Exception as e:
        print(f"  yt-dlp meta falhou: {e}")
        return None


def _gerar_titulo_viral(titulo_slug, meta_original, is_short, pacote_seo=None):
    """Gera título viral adaptado. Usa pacote SEO se fornecido, senão fallback pra template fixo."""
    # Usa título do pacote SEO se fornecido
    if pacote_seo and pacote_seo.get("titulo"):
        return anti_ban(pacote_seo["titulo"])

    # Fallback: modelo fixo (templates)
    titulo_base = ""
    if meta_original and meta_original.get("title"):
        orig = meta_original["title"]
        titulo_base = orig
        for rem in ["[Eng Sub]", "[EN Sub]", "(Eng Sub)", "Full Episode",
                     "Recap", "Manhwa", "Manga", "Episode", "Chapter",
                     "1080p", "720p", "HD"]:
            titulo_base = titulo_base.replace(rem, "").replace(rem.lower(), "")
        titulo_base = re.sub(r"\s+", " ", titulo_base).strip(" -|")
    if not titulo_base or len(titulo_base) < 10:
        titulo_base = titulo_slug.title() if len(titulo_slug) > 10 else random.choice(TEMPLATES_TITULO)

    sufixo = " - Recap Anime"
    if is_short:
        sufixo = " #shorts #anime"

    titulo = titulo_base
    if len(titulo + sufixo) > 100:
        titulo = titulo[: 100 - len(sufixo) - 2] + ".."
    titulo = titulo + sufixo
    return anti_ban(titulo)


def _gerar_tags(meta_original, pacote_seo=None):
    """Gera lista de até 30 tags. Usa pacote SEO se disponível, senão mescla base + original."""
    if pacote_seo and pacote_seo.get("tags"):
        return pacote_seo["tags"][:30]

    # Fallback: modelo fixo
    tags = list(TAGS_ANIME_BASE)
    if meta_original and meta_original.get("tags"):
        for t in meta_original["tags"]:
            t_lower = t.lower().strip()
            if t_lower and t_lower not in [x.lower() for x in tags] and len(t_lower) < 40:
                tags.append(anti_ban(t_lower))
    return list(dict.fromkeys(tags))[:30]


def _gerar_descricao(titulo_slug, meta_original, is_short, pacote_seo=None):
    """Gera descrição rica. Usa pacote SEO se disponível, senão sinopse + CTA + hashtags."""
    if pacote_seo and pacote_seo.get("descricao") and not is_short:
        return anti_ban(pacote_seo["descricao"])

    # Fallback: modelo fixo
    sinopse = ""
    if meta_original and meta_original.get("description"):
        desc_orig = meta_original["description"]
        linhas = [l.strip() for l in desc_orig.split("\n") if l.strip()]
        linhas_uteis = [l for l in linhas if len(l) > 20 and not l.startswith("http") and not l.startswith("#")]
        if linhas_uteis:
            sinopse = " ".join(linhas_uteis[:3])[:300]
    if not sinopse:
        sinopse = f"Um recap incrível de {titulo_slug[:60]}. Não perca esse anime épico!"

    sinopse = anti_ban(sinopse)

    hashtags_extra = " ".join(random.sample(HASHTAGS_ROTATIVAS, min(2, len(HASHTAGS_ROTATIVAS))))

    if is_short:
        desc = (
            f"{sinopse}\n\n"
            f"Nome da obra: nos comentários 📌\n\n"
            f"🔔 INSCREVA-SE para mais recaps!\n"
            f"💬 Comenta o que achou!\n"
            f"❤️ Deixa o LIKE!\n\n"
            f"{HASHTAGS_FIXAS} {hashtags_extra} #shorts"
        )
    else:
        tags_bloco = ", ".join(TAGS_ANIME_BASE[:20])
        desc = (
            f"{sinopse}\n\n"
            f"Nome da obra: nos comentários 📌\n\n"
            f"⏱ Capítulos:\n"
            f"00:00 — Introdução\n\n"
            f"🔔 INSCREVA-SE e ative o sininho para mais recaps!\n"
            f"💬 Comenta o que achou!\n"
            f"❤️ Deixa o LIKE se curtiu!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 TAG:\n"
            f"{tags_bloco}\n\n"
            f"{HASHTAGS_FIXAS} {hashtags_extra}"
        )
    return desc[:5000]

def carregar_postados():
    if Path(POSTADOS_LOG).exists():
        with open(POSTADOS_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def arquivar(video_path):
    """Move o vídeo recem-postado pra <raiz>/postados/anime/... pra nao misturar com originais.
    Depois, apaga a pasta de origem inteira (com roteiro.txt, clipes_landscape/, source.mp4, ...)
    pra nao acumular pasta vazia/lixo no workspace. Exceção: se o destino da pasta original
    NAF for workspace/anime (ex: postar direto de /d/downloads/agendar), NAO apaga.
    """
    import shutil
    p = str(video_path)
    pasta_origem = Path(p).parent
    # Só apaga a pasta de origem se ela estiver dentro de workspace/anime
    em_workspace_anime = False
    try:
        rel = pasta_origem.relative_to(VIDEOS_DIR)
        em_workspace_anime = True
    except ValueError:
        rel = None
    # Move o mp4
    try:
        rel_full = Path(p).relative_to(ROOT_DIR)
    except ValueError:
        return
    # destino central unico de todos os postados (categoria animes)
    dest = Path(r"D:\hipercool-materiais\_postados\animes") / Path(*rel_full.parts[1:])
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        try: Path(p).unlink()
        except: pass
    else:
        try: shutil.move(p, str(dest))
        except: pass
    # Apaga pasta de origem (só workspace/anime) — depois de mover o mp4
    if em_workspace_anime:
        try:
            shutil.rmtree(pasta_origem)
        except Exception as e:
            print(f"      ! nao foi possivel apagar pasta de origem: {e}")

def salvar_postado(video_path):
    postados = carregar_postados()
    postados.append(str(video_path))
    Path(POSTADOS_LOG).parent.mkdir(exist_ok=True, parents=True)
    with open(POSTADOS_LOG, "w", encoding="utf-8") as f:
        json.dump(postados, f, indent=4)
    arquivar(video_path)

def listar_videos_prontos():
    prontos = []
    for nome in ("final_anime_short.mp4", "final_anime_deitado.mp4", "final_anime_deitado_ads.mp4"):
        for path in VIDEOS_DIR.rglob(nome):
            if path.parent != VIDEOS_DIR:
                prontos.append(path)
    by_folder = {}
    for p in prontos:
        key = str(p.parent)
        if key not in by_folder:
            by_folder[key] = p
        else:
            existing = by_folder[key]
            if "ads" in p.name and "ads" not in existing.name:
                by_folder[key] = p
            elif "short" in p.name and "short" not in existing.name:
                by_folder[key] = p
    return list(by_folder.values())

def postar_video(video_path, canal):
    folder_name = video_path.parent.name
    vid, titulo_slug = _extrair_vid_e_titulo(folder_name)
    if len(titulo_slug) < 5:
        titulo_slug = "Resumo Animado"

    is_short = "short" in video_path.name

    print(f"  Buscando metadata do original ({vid})...")
    meta_original = _buscar_meta_original(vid)
    if meta_original:
        print(f"  Original: {meta_original['title'][:60]}")
    else:
        print(f"  Sem metadata do original, usando template viral")

    # Tenta gerar pacote SEO completo (§1 MELHORIAS)
    pacote_seo = None
    if seo_generator and meta_original and not is_short:
        try:
            pacote_seo = seo_generator.gerar_seo_anime(
                meta_original.get("title", ""),
                meta_original.get("description", "")[:500],
                meta_original.get("tags", [])[:15],
                vid
            )
            if pacote_seo:
                print(f"  ✓ Pacote SEO gerado (estilo={pacote_seo.get('estilo', '?')})")
        except Exception as e:
            print(f"  ⚠ SEO generator falhou: {e}")

    titulo = _gerar_titulo_viral(titulo_slug, meta_original, is_short, pacote_seo)
    tags_list = _gerar_tags(meta_original, pacote_seo)
    tags = ",".join(tags_list)
    descricao = _gerar_descricao(titulo_slug, meta_original, is_short, pacote_seo)

    print(f"Postando {video_path.name}")
    print(f"  Título: {titulo}")
    print(f"  Tags: {len(tags_list)} tags")
    print(f"  Canal: {canal}")

    cmd = [
        POSTER,
        YOUTUBE_POSTER,
        "--video", str(video_path),
        "--titulo", titulo,
        "--descricao", descricao,
        "--tags", tags,
        "--canal", canal
    ] 
    
    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if "Video id" in proc.stdout or "Upload resumable concluido!" in proc.stdout or "id" in proc.stdout.lower() or proc.returncode == 0:
            print(f"Sucesso. STDOUT: {proc.stdout}")
            salvar_postado(video_path)

            # Registra extras no Studio (§3 MELHORIAS) — roda depois com studio_extras_anime.py
            if studio_extras_anime:
                try:
                    import re
                    m = re.search(r"Video id[:\s]+([A-Za-z0-9_-]{11})", proc.stdout)
                    if m:
                        url = f"https://www.youtube.com/watch?v={m.group(1)}"
                        studio_extras_anime.adicionar_extras(video_path, url, canal, meta_original)
                except Exception as e:
                    print(f"  ⚠ Falha ao registrar extras: {e}")

            return True
        elif "uploadLimitExceeded" in proc.stderr or "uploadLimitExceeded" in proc.stdout:
            print(f"Limite de upload atingido no canal '{canal}'. Pulando este vídeo.")
            return False  # não salva —下次 tenta o próximo canal
        else:
            print(f"Falha na postagem:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
            return False
    except Exception as e:
        print(f"Erro ao executar youtube_poster: {e}")
        return False

def main():
    prontos = set(listar_videos_prontos())
    postados = set(Path(p) for p in carregar_postados())

    nao_postados = list(prontos - postados)

    if not nao_postados:
        print("Nenhum vídeo novo para postar.")
        return

    nao_postados.sort(key=lambda x: str(x))

    # Rotaciona canais
    idx_canal = len(postados) % len(CANAIS)
    canal_alvo = CANAIS[idx_canal]

    video_alvo = nao_postados[0]

    print(f"Encontrados {len(nao_postados)} vídeos novos do recaps de animes. Postando 1 short agora...")

    if postar_video(video_alvo, canal_alvo):
        print("Finalizado com sucesso. Próxima rodada postará o próximo.")
    else:
        # Canal bloqueou — tenta o próximo canal
        proximo_idx = (idx_canal + 1) % len(CANAIS)
        canal_backup = CANAIS[proximo_idx]
        print(f"Tentando canal backup: {canal_backup}...")
        if postar_video(video_alvo, canal_backup):
            print("Sucesso no canal backup.")
        else:
            # Ambos falharam — NÃO marca como postado (tenta de novo na próxima rodada)
            print("Ambos canais bloqueados. Aguardando reset de quota.")

if __name__ == "__main__":
    main()
