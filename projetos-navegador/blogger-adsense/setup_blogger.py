"""
Blogger + AdSense — automação COMPLETA do Blogger v3 + monetização.

Operações disponíveis:
  - criar_blog(conta, nicho)            → cria blog via UI
  - listar_blogs(conta)                 → lista blogs da conta
  - publicar_post(conta, blog, post)    → publica post (UI ou API)
  - publicar_post_api(blog_id, key, p)  → publica via Blogger API v3
  - listar_posts(conta, blog)           → lista posts de um blog
  - editar_post(conta, blog, id, novo)  → edita post existente
  - deletar_post(conta, blog, id)       → remove post
  - aplicar_adsense(conta, blog)        → inicia solicitação AdSense
  - status_adsense(conta)               → verifica status da conta AdSense
  - gerar_conteudo(nicho)               → pega post do banco local (offline)
  - popular_blogs(conta)                → publica 1 post em cada nicho

CLI:
  python setup_blogger.py                              → dry run
  python setup_blogger.py --live
  python setup_blogger.py --acao listar_blogs --conta X
  python setup_blogger.py --acao publicar --conta X --blog "Curiosidades Tech" --nicho curiosidades-tech
"""
import json
import sys
import time
import random
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

BLOG_DIR = Path(__file__).resolve().parent
STATUS_FILE = BLOG_DIR / "blog_status.json"
HISTORICO = BLOG_DIR / "historico_blogger.jsonl"
BLOGGER_URL = "https://www.blogger.com"

BLOG_NICHES = [
    {"slug": "curiosidades-tech", "title": "Curiosidades Tech", "desc": "Fatos curiosos sobre tecnologia"},
    {"slug": "frases-motivacionais", "title": "Frases do Dia", "desc": "Frases motivacionais diárias"},
    {"slug": "receitas-faceis", "title": "Receitas Rápidas", "desc": "Receitas fáceis em 5 minutos"},
    {"slug": "dicas-saude", "title": "Dicas de Saúde", "desc": "Dicas simples para viver melhor"},
    {"slug": "mundo-animal", "title": "Mundo Animal", "desc": "Curiosidades sobre animais"},
]

SAMPLE_POSTS = {
    "curiosidades-tech": [
        {"title": "O primeiro bug de computador era literal", "content": "<p>Em 1947, engenheiros encontraram uma mariposa presa no relé do Harvard Mark II. Eles colaram o inseto no log e escreveram 'First actual case of bug being found'. Daí nasceu o termo 'bug' na programação.</p><p>A mariposa original está no Museu Nacional de História Americana do Smithsonian.</p>"},
        {"title": "WiFi não significa nada", "content": "<p>Muita gente acha que WiFi é abreviação de 'Wireless Fidelity', mas na verdade não significa nada. O nome foi criado pela empresa de marketing Interbrand como uma alternativa mais fácil ao nome técnico IEEE 802.11b.</p>"},
        {"title": "O primeiro site ainda está no ar", "content": "<p>O primeiro website do mundo, criado por Tim Berners-Lee em 1991 no CERN, ainda pode ser acessado. Era uma página simples explicando o que era a World Wide Web e como usar um navegador.</p>"},
    ],
    "frases-motivacionais": [
        {"title": "Comece antes de estar pronto", "content": "<p>'O segredo de ir em frente é começar.' — Mark Twain</p><p>Não espere o momento perfeito. A perfeição é inimiga do progresso. Dê o primeiro passo mesmo tremendo.</p>"},
        {"title": "Fracasso é feedback", "content": "<p>'Eu não falhei. Apenas encontrei 10.000 maneiras que não funcionam.' — Thomas Edison</p><p>Cada erro é um dado novo. Acumule dados suficientes e o próximo passo fica óbvio.</p>"},
    ],
    "receitas-faceis": [
        {"title": "Omelete gourmet em 3 minutos", "content": "<p>Bata 3 ovos com sal e pimenta. Aqueça manteiga na frigideira em fogo médio. Despeje os ovos e espere 30 segundos sem mexer. Adicione queijo e ervas. Dobre e sirva.</p><p><strong>Dica:</strong> O segredo é não mexer demais — deixe o fundo firmar antes de dobrar.</p>"},
    ],
    "dicas-saude": [
        {"title": "Beba água ao acordar", "content": "<p>Depois de 7-8 horas dormindo, seu corpo está desidratado. Um copo d'água ao acordar ativa o metabolismo, melhora a digestão e ajuda o cérebro a funcionar melhor logo pela manhã.</p>"},
    ],
    "mundo-animal": [
        {"title": "Polvos têm 3 corações", "content": "<p>Dois corações bombeiam sangue para as brânquias, enquanto o terceiro bomba para o resto do corpo. Curiosamente, o coração principal PARA de bater quando o polvo nada — por isso eles preferem rastejar.</p>"},
    ],
}


def _sessao_expirada(page):
    return "accounts.google.com" in page.url or "signin" in page.url.lower()


def _log(acao, conta, detalhes):
    with open(HISTORICO, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "acao": acao, "conta": conta, "detalhes": detalhes}, ensure_ascii=False) + "\n")


def load_status():
    if STATUS_FILE.exists():
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    return {"blogs_created": {}, "posts_published": {}, "adsense_applied": {}, "last_run": None}


def save_status(status):
    status["last_run"] = datetime.now(timezone.utc).isoformat()
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")


def criar_blog(conta, niche):
    """Cria um blog via interface do Blogger."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{BLOGGER_URL}/blog/create", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada", "conta": conta}

            title_input = page.query_selector('input[aria-label*="Title"], input[name="title"], input[type="text"]')
            if title_input:
                title_input.fill(niche["title"])
                time.sleep(1)
                next_btn = page.query_selector('button:has-text("Next"), button:has-text("Avançar")')
                if next_btn:
                    next_btn.click()
                    time.sleep(2)

            url_input = page.query_selector('input[aria-label*="Address"], input[name="address"]')
            if url_input:
                slug = niche["slug"].replace("-", "") + str(random.randint(100, 999))
                url_input.fill(slug)
                time.sleep(1)
                save_btn = page.query_selector('button:has-text("Save"), button:has-text("Salvar"), button:has-text("Create")')
                if save_btn:
                    save_btn.click()
                    time.sleep(3)

            save_session(context, conta)
            _log("criar_blog", conta, niche["slug"])
            return {"sucesso": True, "conta": conta, "nicho": niche["slug"]}
    except Exception as e:
        return {"sucesso": False, "erro": str(e), "conta": conta}


def listar_blogs(conta):
    """Lista blogs da conta."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(BLOGGER_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"conta": conta, "blogs": [], "erro": "sessao_expirada"}

            blogs = []
            for el in page.query_selector_all('[class*="blog-name"], a[href*="blogID"], [role="listitem"]'):
                t = el.inner_text().strip().split("\n")[0]
                if t and len(t) < 100:
                    blogs.append(t)
            save_session(context, conta)
            return {"conta": conta, "blogs": list(dict.fromkeys(blogs))}
    except Exception as e:
        return {"conta": conta, "blogs": [], "erro": str(e)}


def publicar_post(conta, nome_blog, post_data):
    """Publica um post via UI do Blogger."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(BLOGGER_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            novo = page.query_selector('a[href*="createpost"], button:has-text("New post"), button:has-text("Nova postagem")')
            if novo:
                novo.click()
                time.sleep(4)

            titulo = page.query_selector('input[aria-label*="Title"], input[placeholder*="Title"], input[placeholder*="Título"]')
            if titulo:
                titulo.fill(post_data["title"])
                time.sleep(1)

            corpo = page.query_selector('iframe.editor, div[contenteditable="true"], body[contenteditable]')
            if corpo:
                corpo.click()
                page.keyboard.type(post_data.get("content", "")[:5000])
                time.sleep(1)

            publish = page.query_selector('button:has-text("Publish"), button:has-text("Publicar")')
            if publish:
                publish.click()
                time.sleep(2)
                confirm = page.query_selector('button:has-text("Confirm"), button:has-text("Publicar")')
                if confirm:
                    confirm.click()
                    time.sleep(3)

            save_session(context, conta)
            _log("publicar_post", conta, {"blog": nome_blog, "titulo": post_data["title"]})
            return {"sucesso": True, "blog": nome_blog, "titulo": post_data["title"]}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def publicar_post_api(blog_id, api_key, post_data):
    """Publica post via Blogger API v3 (precisa de API key/OAuth válida)."""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?key={api_key}"
    payload = json.dumps({"kind": "blogger#post", "title": post_data["title"],
                          "content": post_data["content"]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"erro": str(e)}


def listar_posts(conta, nome_blog):
    """Lista posts de um blog."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(BLOGGER_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"conta": conta, "posts": [], "erro": "sessao_expirada"}

            posts_link = page.query_selector('a[href*="posts"], :has-text("Posts")')
            if posts_link:
                posts_link.click()
                time.sleep(4)
            posts = []
            for el in page.query_selector_all('[class*="post-title"], tr, [role="row"]'):
                t = el.inner_text().strip().split("\n")[0]
                if t and len(t) < 150:
                    posts.append(t)
            save_session(context, conta)
            return {"conta": conta, "blog": nome_blog, "posts": posts[:50]}
    except Exception as e:
        return {"conta": conta, "posts": [], "erro": str(e)}


def editar_post(conta, nome_blog, titulo_post, novo_conteudo):
    """Edita um post existente pelo título."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(BLOGGER_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            link = page.query_selector(f'a:has-text("{titulo_post}")')
            if not link:
                return {"sucesso": False, "erro": f"post '{titulo_post}' não encontrado"}
            link.click()
            time.sleep(4)
            corpo = page.query_selector('div[contenteditable="true"], body[contenteditable]')
            if corpo:
                corpo.click()
                page.keyboard.press("Control+a")
                page.keyboard.type(novo_conteudo[:5000])
                time.sleep(1)
                update = page.query_selector('button:has-text("Update"), button:has-text("Atualizar"), button:has-text("Publish")')
                if update:
                    update.click()
                    time.sleep(3)
            save_session(context, conta)
            _log("editar_post", conta, {"blog": nome_blog, "titulo": titulo_post})
            return {"sucesso": True, "blog": nome_blog, "titulo": titulo_post}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def deletar_post(conta, nome_blog, titulo_post):
    """Remove um post pelo título."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(BLOGGER_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            row = page.query_selector(f'tr:has-text("{titulo_post}"), [role="row"]:has-text("{titulo_post}")')
            if row:
                del_btn = row.query_selector('button[aria-label*="Delete"], button[aria-label*="Excluir"]')
                if del_btn:
                    del_btn.click()
                    time.sleep(1)
                    confirm = page.query_selector('button:has-text("Delete"), button:has-text("Excluir")')
                    if confirm:
                        confirm.click()
                        time.sleep(2)
                        save_session(context, conta)
                        _log("deletar_post", conta, {"blog": nome_blog, "titulo": titulo_post})
                        return {"sucesso": True, "titulo": titulo_post}
            return {"sucesso": False, "erro": f"post '{titulo_post}' não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def aplicar_adsense(conta, nome_blog):
    """Inicia a solicitação AdSense pra um blog."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto("https://www.google.com/adsense/new/u/0/pub/sign-up", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            estado = "formulario_aberto" if page.query_selector('input, form') else "indefinido"
            save_session(context, conta)
            _log("aplicar_adsense", conta, nome_blog)
            return {"sucesso": True, "conta": conta, "blog": nome_blog, "estado": estado,
                    "nota": "solicitação AdSense requer preenchimento manual de dados fiscais"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def status_adsense(conta):
    """Verifica status da conta AdSense."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto("https://www.google.com/adsense/new/u/0/pub/home", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"conta": conta, "erro": "sessao_expirada"}
            texto = ""
            el = page.query_selector('[class*="status"], [class*="alert"], main')
            if el:
                texto = el.inner_text().strip()[:300]
            save_session(context, conta)
            return {"conta": conta, "status_adsense": texto or "sem info"}
    except Exception as e:
        return {"conta": conta, "erro": str(e)}


def gerar_conteudo(nicho_slug):
    """Pega um post do banco local (offline)."""
    posts = SAMPLE_POSTS.get(nicho_slug, [])
    return random.choice(posts) if posts else None


def popular_blogs(conta):
    """Publica 1 post em cada nicho."""
    resultados = []
    for niche in BLOG_NICHES:
        post = gerar_conteudo(niche["slug"])
        if post:
            r = publicar_post(conta, niche["title"], post)
            resultados.append({"nicho": niche["slug"], "sucesso": r.get("sucesso", False)})
            if r.get("erro") == "sessao_expirada":
                break
    return {"conta": conta, "resultados": resultados}


FUNCIONALIDADES = {
    "criar_blog":   {"func": criar_blog,        "desc": "Cria blog via UI"},
    "listar_blogs": {"func": listar_blogs,      "desc": "Lista blogs da conta"},
    "publicar":     {"func": publicar_post,     "desc": "Publica post"},
    "listar_posts": {"func": listar_posts,      "desc": "Lista posts de um blog"},
    "editar":       {"func": editar_post,       "desc": "Edita post existente"},
    "deletar":      {"func": deletar_post,      "desc": "Remove post"},
    "adsense":      {"func": aplicar_adsense,   "desc": "Solicita AdSense"},
    "status_adsense":{"func": status_adsense,   "desc": "Status da conta AdSense"},
    "popular":      {"func": popular_blogs,     "desc": "Publica 1 post por nicho"},
}


def run_blogger_setup(dry_run=True):
    status = load_status()
    print(f"[Blogger + AdSense] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Blogs criados: {len(status['blogs_created'])} | Funcionalidades: {', '.join(FUNCIONALIDADES.keys())}")

    accounts = list(ACCOUNTS.keys())
    for i, niche in enumerate(BLOG_NICHES):
        conta = accounts[i % len(accounts)]
        key = f"{conta}_{niche['slug']}"
        if key in status["blogs_created"]:
            print(f"  Blog {niche['title']} ({conta}) já existe, pulando.")
            continue
        if dry_run:
            print(f"  [DRY RUN] criaria blog '{niche['title']}' em {conta}")
            status["blogs_created"][key] = {"niche": niche["slug"], "account": conta,
                                            "created_at": datetime.now(timezone.utc).isoformat(), "dry_run": True}
        else:
            print(f"  Criando '{niche['title']}' em {conta}...")
            r = criar_blog(conta, niche)
            if r.get("sucesso"):
                status["blogs_created"][key] = {"niche": niche["slug"], "account": conta,
                                                "created_at": datetime.now(timezone.utc).isoformat()}
                print("    OK")
            else:
                print(f"    ERRO: {r.get('erro')}")

    save_status(status)
    print(f"\nStatus salvo em {STATUS_FILE}")
    return status


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--acao" in args:
        acao = args[args.index("--acao") + 1]
        conta = args[args.index("--conta") + 1] if "--conta" in args else "fabrica"
        blog = args[args.index("--blog") + 1] if "--blog" in args else ""
        if acao == "listar_blogs":
            r = listar_blogs(conta)
        elif acao == "criar_blog":
            nicho = args[args.index("--nicho") + 1] if "--nicho" in args else "curiosidades-tech"
            niche = next((n for n in BLOG_NICHES if n["slug"] == nicho), BLOG_NICHES[0])
            r = criar_blog(conta, niche)
        elif acao == "publicar":
            nicho = args[args.index("--nicho") + 1] if "--nicho" in args else "curiosidades-tech"
            post = gerar_conteudo(nicho)
            r = publicar_post(conta, blog, post) if post else {"erro": "nicho sem conteúdo"}
        elif acao == "listar_posts":
            r = listar_posts(conta, blog)
        elif acao == "editar":
            r = editar_post(conta, blog, args[args.index("--titulo") + 1], args[args.index("--conteudo") + 1])
        elif acao == "deletar":
            r = deletar_post(conta, blog, args[args.index("--titulo") + 1])
        elif acao == "adsense":
            r = aplicar_adsense(conta, blog)
        elif acao == "status_adsense":
            r = status_adsense(conta)
        elif acao == "popular":
            r = popular_blogs(conta)
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        dry = "--live" not in args
        if dry:
            print("Modo DRY RUN\n")
        run_blogger_setup(dry_run=dry)
