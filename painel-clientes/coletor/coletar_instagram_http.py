# -*- coding: utf-8 -*-
r"""coletar_instagram_http.py — métricas do Instagram para o Painel de Clientes nas contas SEM token da API (conta
pessoal, ex.: @advance_novoestrela). Lê pela sessão do Chrome do cofre, por HTTP, como o próprio site
(D:\projeto-navegador-sem-navegador services\instagram\web.py). Só LÊ.

Manda o mesmo formato do coletar_instagram.py (POST /api/coleta): perfil (seguidores, posts), posts (curtidas,
comentários, visualizações dos Reels), comentários recentes e Direct (quem mandou mensagem) como contatos.
Pouca leitura por rodada (o Instagram limitou a conta em 30/10 depois de muitas leituras seguidas): 1 consulta de
posts, 1 de Reels, comentários só dos posts que ganharam comentário novo (máx. 5), 1 da caixa do Direct.
Clientes com "instagram_http": true em config\clientes_manuais.json. Tarefa PainelClientes_ColetarHTTP (a cada 2 h).

    D:\veo\venv\Scripts\python.exe coletar_instagram_http.py [--ver]
"""
import copy
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NSN = Path(r"D:\projeto-navegador-sem-navegador")
sys.path.insert(0, str(NSN))
CONFIG = RAIZ / "config" / "clientes.json"
CHAVES = RAIZ / "segredos" / "chaves.json"
ESTADO = RAIZ / "cache" / "coletor_http_estado.json"
LOG = RAIZ / "logs" / "coletor_http.log"
PAINEL = "https://clientes.opus-sem-limites.com.br"
MAX_COMENTARIOS = 5
HORAS_ATE_AVISAR = 6  # falha seguida por mais que isso aparece no painel como "não conectado" (com o motivo)
TIPOS = {"reel": "reels", "video": "vídeo"}  # mesmos nomes do coletor da API (o filtro da tabela de posts junta)


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    if sys.stdout:  # pythonw (tarefa do Windows) não tem tela
        print(linha, flush=True)
    try:
        LOG.parent.mkdir(exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > 1_000_000:
            LOG.write_text(LOG.read_text(encoding="utf-8", errors="replace")[-200_000:], encoding="utf-8")
        with LOG.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _iso(ts):
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000") if ts else None


def _capa(md):
    """Miniatura do post (a menor imagem com 240+ px de largura; o painel mostra pequeno)."""
    cands = ((md.get("image_versions2") or {}).get("candidates") or [])
    if not cands and md.get("carousel_media"):
        cands = ((md["carousel_media"][0].get("image_versions2") or {}).get("candidates") or [])
    boas = sorted((c for c in cands if c.get("url")), key=lambda c: c.get("width") or 0)
    return next((c["url"] for c in boas if (c.get("width") or 0) >= 240), boas[-1]["url"] if boas else None)


def _posts_e_reels(ig, n_posts=50, n_reels=30):
    """As mesmas 2 consultas do ig.posts()/ig.reels() (services\\instagram\\web.py), lendo também a miniatura."""
    tipos = {1: "foto", 2: "vídeo", 8: "carrossel"}
    m = ig.modelos["PolarisProfilePostsQuery"]
    d = ig.graphql("PolarisProfilePostsQuery", ig._variaveis(m, username=ig.conta, count=n_posts))
    conn = next((x for x in d.values() if isinstance(x, dict) and "edges" in x), {})
    posts = [{"codigo": x.get("code"), "id": x.get("pk") or x.get("id"), "quando": x.get("taken_at"),
              "tipo": "reels" if x.get("product_type") == "clips" else tipos.get(x.get("media_type"), "post"),
              "curtidas": x.get("like_count"), "comentarios": x.get("comment_count"), "capa": _capa(x),
              "legenda": ((x.get("caption") or {}).get("text") or "")[:120]}
             for x in (e.get("node", {}) for e in conn.get("edges", []))]
    time.sleep(6)
    m = ig.modelos["PolarisProfileReelsTabContentQuery"]
    d = ig.graphql("PolarisProfileReelsTabContentQuery",
                   ig._variaveis(m, target_user_id=ig.uid, user_id=ig.uid, page_size=n_reels))
    conn = next((x.get("clips_connection") for x in d.values() if isinstance(x, dict) and "clips_connection" in x),
                None) or next((x for x in d.values() if isinstance(x, dict) and "edges" in x), {})
    reels = []
    for e in conn.get("edges", []):
        md = e.get("node", {}).get("media", {})
        reels.append({"codigo": md.get("code"), "id": md.get("pk") or md.get("id"), "views": md.get("play_count"),
                      "curtidas": md.get("like_count"), "comentarios": md.get("comment_count"),
                      "quando": md.get("taken_at"), "capa": _capa(md),
                      "legenda": ((md.get("caption") or {}).get("text") or "")[:120]})
    return posts, reels


def coletar(cliente, conta, est):
    from services.instagram.postar import InstagramPostar
    ig = InstagramPostar(conta)
    eu = conta.lower()
    posts = {}
    lidos_posts, lidos_reels = _posts_e_reels(ig)
    for p in lidos_posts:
        posts[p["codigo"]] = {"id": str(p["id"]), "em": _iso(p["quando"]), "tipo": TIPOS.get(p["tipo"], p["tipo"]),
                              "legenda": (p["legenda"] or "").split("\n")[0][:200],
                              "link": f"https://www.instagram.com/p/{p['codigo']}/", "capa": p.get("capa"),
                              "curtidas": p["curtidas"], "comentarios": p["comentarios"]}
    for r in lidos_reels:
        alvo = posts.setdefault(r["codigo"], {"id": str(r["id"]), "em": _iso(r["quando"]), "tipo": "reels",
                                              "legenda": (r["legenda"] or "").split("\n")[0][:200],
                                              "link": f"https://www.instagram.com/reel/{r['codigo']}/"})
        alvo.update(tipo="reels", visualizacoes=r.get("views"), curtidas=r.get("curtidas"),
                    comentarios=r.get("comentarios"), link=f"https://www.instagram.com/reel/{r['codigo']}/",
                    capa=alvo.get("capa") or r.get("capa"))
    eventos = []
    vistos = est.setdefault("n_com", {})
    n = 0
    for cod, p in posts.items():
        if (p.get("comentarios") or 0) and vistos.get(cod) != p["comentarios"] and n < MAX_COMENTARIOS:
            n += 1
            time.sleep(5)
            try:
                for c in ig.comentarios(cod)[1]:
                    quem = str(c.get("usuario") or c.get("username") or "").lower().lstrip("@")
                    if not quem or quem == eu:
                        continue
                    eventos.append({"canal": "ig_comentario", "ext_id": str(c.get("id") or f"{cod}:{quem}"),
                                    "pessoa": "ig:" + quem, "nome": "@" + quem, "contato": "@" + quem,
                                    "em": _iso(c.get("quando")) if isinstance(c.get("quando"), (int, float)) else c.get("quando"),
                                    "texto": str(c.get("texto") or "")[:300], "ref": p["link"]})
                vistos[cod] = p["comentarios"]
            except Exception as e:  # noqa: BLE001
                log(f"  comentários de {cod}: {type(e).__name__}: {str(e)[:120]}")
    respondidos = []
    time.sleep(6)
    try:
        r = ig.s.get("https://www.instagram.com/api/v1/direct_v2/inbox/?persistentBadging=true&folder=&limit=20",
                     headers=ig._hd(), timeout=40)
        for th in (r.json().get("inbox") or {}).get("threads") or []:
            outros = [u for u in th.get("users") or [] if (u.get("username") or "").lower() != eu]
            if not outros:
                continue
            quem = outros[0]["username"].lower()
            for it in th.get("items") or []:
                if str(it.get("user_id")) != str(ig.uid):
                    eventos.append({"canal": "ig_dm", "ext_id": str(it.get("item_id")), "pessoa": "ig:" + quem,
                                    "nome": "@" + quem, "contato": "@" + quem,
                                    "em": _iso(int(it.get("timestamp", 0)) // 1_000_000),
                                    "texto": str(it.get("text") or "(foto, áudio ou anexo)")[:300],
                                    "ref": "https://www.instagram.com/direct/inbox/"})
            itens = th.get("items") or []
            if itens:
                respondidos.append({"conta": quem, "respondido": str(itens[0].get("user_id")) == str(ig.uid)})
    except Exception as e:  # noqa: BLE001
        log(f"  Direct: {type(e).__name__}: {str(e)[:120]}")
    perfil = {"posts": len(posts)}
    try:
        time.sleep(5)
        info = ig.perfil_info()
        perfil = {"seguidores": info.get("seguidores"), "posts": info.get("posts")}
    except Exception as e:  # noqa: BLE001
        log(f"  perfil: {type(e).__name__}: {str(e)[:120]}")
    return {"cliente": cliente, "conta": conta, "perfil": perfil, "dias": [], "posts": list(posts.values()),
            "eventos": eventos, "respondidos": respondidos}


def mandar(chave, dados):
    req = urllib.request.Request(f"{PAINEL}/api/coleta", data=json.dumps(dados, ensure_ascii=False).encode(),
                                 headers={"Content-Type": "application/json", "X-Chave": chave,
                                          "User-Agent": "painel-clientes-coletor-http/1"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def main():
    ver = "--ver" in sys.argv
    chave = (_ler(CHAVES, {}) or {}).get("admin")
    manuais = {c["id"]: c for c in (_ler(RAIZ / "config" / "clientes_manuais.json", {}).get("clientes") or [])}
    estado = _ler(ESTADO, {})
    for cl in _ler(CONFIG, {}).get("clientes") or []:
        if not cl.get("ativo", True) or not (manuais.get(cl["id"]) or {}).get("instagram_http"):
            continue
        for conta in cl.get("instagram") or []:
            conta = conta.lstrip("@").lower()
            k = f"{cl['id']}:{conta}"
            antes = copy.deepcopy(estado.get(k) or {})  # volta a este se o painel não receber
            est = estado.setdefault(k, {})
            try:
                dados = coletar(cl["id"], conta, est)
            except Exception as e:  # noqa: BLE001
                log(f"{cl['id']} @{conta}: falhou {type(e).__name__}: {str(e)[:200]}")
                # 1 falha (limite passageiro do Instagram) não muda nada; falhando há horas, o painel mostra o motivo
                if not ver and chave and time.time() - est.get("ok_t", 0) > HORAS_ATE_AVISAR * 3600:
                    try:
                        mandar(chave, {"cliente": cl["id"], "conta": conta,
                                       "erro": f"leitura do Instagram pela sessão falhou: {str(e)[:150]}"})
                    except Exception as e2:  # noqa: BLE001
                        log(f"  painel não recebeu o aviso ({type(e2).__name__})")
                continue
            resumo = (f"{dados['perfil']} | {len(dados['posts'])} posts | "
                      f"{sum(p.get('visualizacoes') or 0 for p in dados['posts'])} visualizações | "
                      f"{sum(p.get('curtidas') or 0 for p in dados['posts'])} curtidas | {len(dados['eventos'])} contatos")
            if ver:
                log(f"[ver] {cl['id']} @{conta}: {resumo}")
                continue
            try:
                log(f"{cl['id']} @{conta}: {resumo} -> painel {mandar(chave, dados)}")
            except Exception as e:  # noqa: BLE001 — painel fora do ar: os comentários são lidos de novo na próxima
                log(f"{cl['id']} @{conta}: painel não recebeu ({type(e).__name__}: {str(e)[:160]})")
                estado[k] = antes
                continue
            est["ok_t"] = time.time()
            ESTADO.parent.mkdir(exist_ok=True)
            ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
