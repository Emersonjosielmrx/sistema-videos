"""
Redes Sociais crosspost — gera conteúdo adaptado por plataforma e agenda posts.
Funciona 100% offline (gera queue local de posts pendentes).
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

SOCIAL_DIR = Path(__file__).resolve().parent
STATUS_FILE = SOCIAL_DIR / "social_status.json"
QUEUE_FILE = SOCIAL_DIR / "post_queue.json"
TEMPLATES_DIR = SOCIAL_DIR / "templates"

PLATFORMS = {
    "youtube": {"url": "https://studio.youtube.com", "type": "video", "max_title": 100, "max_desc": 5000},
    "blogger": {"url": "https://www.blogger.com", "type": "text", "max_title": 150, "max_body": 10000},
    "google_business": {"url": "https://business.google.com", "type": "post", "max_text": 1500},
}

CONTENT_CATEGORIES = {
    "manhwa_recap": {
        "templates": [
            {"title": "{obra} — {tipo} ÉPICO que NINGUÉM esperava!", "hashtags": "#manhwa #webtoon #recap #anime"},
            {"title": "A VERDADE sobre {personagem} em {obra}", "hashtags": "#manhwa #anime #plot #teoria"},
            {"title": "{obra}: esse capítulo MUDOU TUDO", "hashtags": "#recap #manhwa #webtoon #anime"},
            {"title": "O VERDADEIRO poder de {personagem}!", "hashtags": "#manhwa #power #webtoon"},
            {"title": "NINGUÉM previu isso em {obra}!", "hashtags": "#manhwa #anime #recap #spoiler"},
        ],
        "seo_keywords": ["manhwa recap", "webtoon recap", "anime recap", "recap manhwa br", "resumo manhwa"],
    },
    "curiosidades": {
        "templates": [
            {"title": "{n} fatos INSANOS sobre {tema} que você NÃO sabia!", "hashtags": "#curiosidades #fatos #brasil"},
            {"title": "A ciência por trás de {tema}", "hashtags": "#ciência #curiosidade #educação"},
            {"title": "Por que {tema}? A resposta vai te CHOCAR", "hashtags": "#fatos #curiosidades #mundo"},
        ],
        "seo_keywords": ["curiosidades", "fatos curiosos", "voce sabia", "fatos incríveis"],
    },
    "terror": {
        "templates": [
            {"title": "A história REAL de {tema} — NUNCA durma sozinho!", "hashtags": "#terror #medo #historias #horror"},
            {"title": "{tema}: o caso mais ASSUSTADOR de todos", "hashtags": "#terror #casoreal #medo"},
            {"title": "Os vizinhos NÃO sabiam o que tinha no {local}", "hashtags": "#terror #crime #medo #horror"},
        ],
        "seo_keywords": ["histórias de terror", "casos reais terror", "medo", "creepypasta br"],
    },
}

BLOGGER_TEMPLATES = {
    "manhwa_recap": """
<h2>{title}</h2>
<p>{intro}</p>
<a href="{video_url}" target="_blank">
  <img src="{thumbnail}" alt="{title}" style="max-width:100%"/>
</a>
<p>{description}</p>
<h3>O que aconteceu:</h3>
<ul>{bullet_points}</ul>
<p><strong>Assista o vídeo completo:</strong> <a href="{video_url}">{title}</a></p>
<p>{hashtags}</p>
""",
    "generic": """
<h2>{title}</h2>
<p>{body}</p>
<p>{hashtags}</p>
""",
}


def generate_post_variants(category, variables):
    """Gera variantes de post pra cada plataforma a partir de um template."""
    cat = CONTENT_CATEGORIES.get(category, CONTENT_CATEGORIES["manhwa_recap"])
    posts = []

    for template in cat["templates"]:
        title = template["title"]
        for k, v in variables.items():
            title = title.replace(f"{{{k}}}", str(v))

        posts.append({
            "category": category,
            "title": title,
            "hashtags": template["hashtags"],
            "seo_keywords": cat["seo_keywords"],
            "variants": {
                "youtube": {
                    "title": title[:100],
                    "description": f"{title}\n\n{template['hashtags']}\n\nInscreva-se e ative o sino!",
                },
                "blogger": {
                    "title": title,
                    "html": BLOGGER_TEMPLATES.get(category, BLOGGER_TEMPLATES["generic"]).format(
                        title=title, body="", intro="", video_url="", thumbnail="",
                        description=title, bullet_points="", hashtags=template["hashtags"],
                    ),
                },
                "google_business": {
                    "text": f"{title} {template['hashtags']}",
                },
            },
        })
    return posts


def load_queue():
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    return {"pending": [], "posted": [], "failed": []}


def save_queue(queue):
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")


def add_to_queue(posts, scheduled_at=None):
    """Adiciona posts à fila de postagem."""
    queue = load_queue()
    base_time = scheduled_at or datetime.now(timezone.utc)

    for i, post in enumerate(posts):
        entry = {
            "id": f"post_{int(base_time.timestamp())}_{i}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scheduled_at": (base_time + timedelta(hours=i * 4)).isoformat(),
            "post": post,
            "status": "pending",
        }
        queue["pending"].append(entry)

    save_queue(queue)
    return len(posts)


def setup_crosspost(dry_run=True):
    """Setup do crosspost + geração de conteúdo de exemplo."""
    print(f"[Redes Sociais Crosspost] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    manhwa_posts = generate_post_variants("manhwa_recap", {
        "obra": "The Meek Cat", "tipo": "plot twist", "personagem": "MC",
    })
    terror_posts = generate_post_variants("terror", {
        "tema": "a criança do porão", "local": "sótão",
    })
    curiosidade_posts = generate_post_variants("curiosidades", {
        "n": "7", "tema": "buracos negros",
    })

    all_posts = manhwa_posts + terror_posts + curiosidade_posts
    added = add_to_queue(all_posts)

    templates_export = {cat: data["templates"] for cat, data in CONTENT_CATEGORIES.items()}
    (TEMPLATES_DIR / "content_templates.json").write_text(
        json.dumps(templates_export, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    status = {
        "platforms": list(PLATFORMS.keys()),
        "categories": list(CONTENT_CATEGORIES.keys()),
        "templates_count": sum(len(d["templates"]) for d in CONTENT_CATEGORIES.values()),
        "queue_pending": added,
        "accounts_assigned": {},
        "last_run": datetime.now(timezone.utc).isoformat(),
    }

    accounts = list(ACCOUNTS.keys())
    for i, (platform, info) in enumerate(PLATFORMS.items()):
        assigned = accounts[i % len(accounts)]
        status["accounts_assigned"][platform] = assigned
        print(f"  {platform}: {assigned} ({info['url']})")

    print(f"\n  Templates: {status['templates_count']} em {len(CONTENT_CATEGORIES)} categorias")
    print(f"  Posts na fila: {added}")

    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStatus salvo em {STATUS_FILE}")

    if dry_run:
        print("\n[DRY RUN] Crosspost configurado. Use --live pra postar.")
    return status


def postar_blogger(conta, titulo, html):
    """Publica um post no Blogger da conta (browser real)."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto("https://www.blogger.com", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}
            novo = page.query_selector('a[href*="createpost"], button:has-text("New post"), button:has-text("Nova postagem")')
            if novo:
                novo.click()
                time.sleep(4)
            titulo_el = page.query_selector('input[aria-label*="Title"], input[placeholder*="Título"]')
            if titulo_el:
                titulo_el.fill(titulo)
                time.sleep(1)
            corpo = page.query_selector('div[contenteditable="true"], body[contenteditable]')
            if corpo:
                corpo.click()
                page.keyboard.type(html[:5000])
            pub = page.query_selector('button:has-text("Publish"), button:has-text("Publicar")')
            if pub:
                pub.click()
                time.sleep(2)
                confirm = page.query_selector('button:has-text("Confirm"), button:has-text("Publicar")')
                if confirm:
                    confirm.click()
                    time.sleep(3)
            save_session(context, conta)
            return {"sucesso": True, "plataforma": "blogger", "titulo": titulo}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def postar_google_business(conta, texto):
    """Publica um post no perfil Google Business (browser real)."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto("https://business.google.com/posts", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}
            editor = page.query_selector('div[contenteditable="true"], textarea')
            if editor:
                editor.click()
                editor.type(texto[:1500], delay=15)
                pub = page.query_selector('button:has-text("Publish"), button:has-text("Publicar")')
                if pub:
                    pub.click()
                    time.sleep(3)
                save_session(context, conta)
                return {"sucesso": True, "plataforma": "google_business", "texto": texto[:50]}
            return {"sucesso": False, "erro": "editor não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def processar_fila(dry_run=True, max_posts=5):
    """Processa a fila de posts pendentes que já venceram o horário agendado."""
    queue = load_queue()
    agora = datetime.now(timezone.utc)
    accounts = list(ACCOUNTS.keys())
    processados = []

    ainda_pendentes = []
    for entry in queue["pending"]:
        if len(processados) >= max_posts:
            ainda_pendentes.append(entry)
            continue
        agendado = datetime.fromisoformat(entry["scheduled_at"])
        if agendado > agora:
            ainda_pendentes.append(entry)
            continue

        post = entry["post"]
        conta = accounts[len(processados) % len(accounts)]

        if dry_run:
            processados.append({"id": entry["id"], "dry_run": True, "conta": conta})
            entry["status"] = "dry_run"
            ainda_pendentes.append(entry)
            continue

        variante = post["variants"].get("blogger", {})
        r = postar_blogger(conta, variante.get("title", post["title"]), variante.get("html", ""))
        entry["status"] = "posted" if r.get("sucesso") else "failed"
        entry["resultado"] = r
        if r.get("sucesso"):
            queue["posted"].append(entry)
        else:
            queue["failed"].append(entry)
        processados.append({"id": entry["id"], "sucesso": r.get("sucesso"), "conta": conta})

    queue["pending"] = ainda_pendentes
    save_queue(queue)
    return {"processados": len(processados), "detalhes": processados,
            "restam_pendentes": len(ainda_pendentes)}


if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--live" not in args
    if "--processar" in args:
        if dry:
            print("Modo DRY RUN — processaria fila\n")
        r = processar_fila(dry_run=dry)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        if dry:
            print("Modo DRY RUN\n")
        setup_crosspost(dry_run=dry)
