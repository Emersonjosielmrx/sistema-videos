# -*- coding: utf-8 -*-
"""coletar_instagram.py — Instagram dos clientes e produtos para o Painel de Clientes (PC1, a cada 30 min).

Só LÊ a API do Instagram (graph.instagram.com; token em D:\\credenciais-canais\\instagram_contas.json, renovado pelo
D:\\postador-de-videos\\bin\\renovar_token_insta.py) — NUNCA responde, curte nem posta (quem responde cliente é o
vigia da MS Energy). Para cada conta de config\\clientes.json manda um POST /api/coleta ao painel
(https://clientes.opus-sem-limites.com.br) com: perfil, números do dia (alcance, toques no link da bio, visitas ao
perfil, visualizações...), posts com métricas e as pessoas que mandaram Direct ou comentaram.
Conta sem token ou com token vencido vai como "erro" (o painel mostra "Instagram não conectado" e o motivo).
30/10: 1x por dia renova (renovar_token_insta.py) o token das contas que responderam, para não vencer em 60 dias.
Contas com "instagram_http" (conta pessoal, sem API) ficam com o coletar_instagram_http.py.

    python coletar_instagram.py              # coleta e manda (tarefa do Windows PainelClientes_Coletar)
    python coletar_instagram.py --ver        # mostra o resumo do que mandaria, sem mandar
    python coletar_instagram.py --painel http://127.0.0.1:8098   # manda para um painel de teste
Só biblioteca padrão. Estado em cache\\coletor_estado.json; log em logs\\coletor.log.
"""
import copy
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "config" / "clientes.json"
CHAVES = RAIZ / "segredos" / "chaves.json"
ESTADO = RAIZ / "cache" / "coletor_estado.json"
LOG = RAIZ / "logs" / "coletor.log"
CREDS = Path(r"D:\credenciais-canais\instagram_contas.json")
RENOVAR = Path(r"D:\postador-de-videos\bin\renovar_token_insta.py")
API = "https://graph.instagram.com/v21.0"
PAINEL = "https://clientes.opus-sem-limites.com.br"
FUSO = timezone(timedelta(hours=-3))
DIAS_HIST = 28  # 1ª coleta: 4 semanas para trás (a API dá no máximo 30 dias de série)
METRICAS_POST = ["views", "reach", "likes", "comments", "shares", "saved"]
MAX_INSIGHTS_POST = 30  # por conta e por rodada (limite de chamadas da API)
MAX_COMENTARIOS = 60


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > 1_000_000:
            LOG.write_text(LOG.read_text(encoding="utf-8", errors="replace")[-200_000:], encoding="utf-8")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def sem_token(s):
    return re.sub(r"(access_token=)[^&\s\"']+", r"\1***", str(s))


class ErroToken(Exception):
    pass


class ErroLimite(Exception):
    pass


def _get(path, tok, **params):
    url = path if path.startswith("http") else f"{API}/{path}?{urllib.parse.urlencode({**params, 'access_token': tok})}"
    try:
        return json.loads(urllib.request.urlopen(url, timeout=60).read())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("error") or {}
        except Exception:  # noqa: BLE001
            err = {}
        cod = err.get("code")
        if cod == 190 or err.get("type") == "OAuthException" and cod in (102, 463, 467):
            raise ErroToken(err.get("message") or "token inválido") from None
        if cod in (4, 17, 32, 613) or e.code == 429:
            raise ErroLimite(err.get("message") or "limite da API") from None
        raise RuntimeError(f"HTTP {e.code}: {sem_token(err.get('message') or '')[:160]}") from None


def _ler(p, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _salvar(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _unix(d):
    return int(datetime.combine(d, datetime.min.time(), FUSO).timestamp())


def _iso(ts):
    """Hora da API ('2026-10-24T07:00:00+0000') -> datetime UTC."""
    return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def dias_do_perfil(tok, est):
    """Números por dia: alcance e seguidores novos (série) + visitas ao perfil, toques no link, contas engajadas,
    interações e visualizações (total do dia). Dia já fechado (mais de 2 dias atrás) não é pedido de novo."""
    hoje = datetime.now(FUSO).date()
    feitos = set(est.setdefault("dias_ok", []))
    pedir = [hoje - timedelta(days=i) for i in range(DIAS_HIST)]
    pedir = [d for d in pedir if d.isoformat() not in feitos]
    if not pedir:
        return []
    out = {d.isoformat(): {"dia": d.isoformat()} for d in pedir}
    ini, fim = min(pedir), max(pedir)
    # série diária: o dia da API termina às 07:00 UTC (meia-noite no Pacífico) — vale para a data anterior
    for metrica, campo in (("reach", "alcance"), ("follower_count", "novos_seguidores")):
        try:
            r = _get("me/insights", tok, metric=metrica, period="day", since=_unix(ini - timedelta(days=1)),
                     until=min(_unix(fim + timedelta(days=1)), int(time.time())))
            for v in (r.get("data") or [{}])[0].get("values", []):
                d = (_iso(v["end_time"]) - timedelta(days=1)).date().isoformat()
                if d in out:
                    out[d][campo] = v.get("value")
        except (ErroToken, ErroLimite):
            raise
        except Exception as e:  # noqa: BLE001 — follower_count só existe para contas com 100+ seguidores
            log(f"  série {metrica}: {e}")
    total = {"profile_views": "visitas_perfil", "website_clicks": "toques_link", "accounts_engaged": "contas_engajadas",
             "total_interactions": "interacoes", "views": "visualizacoes"}
    for d in sorted(pedir):
        try:
            r = _get("me/insights", tok, metric=",".join(total), period="day", metric_type="total_value",
                     since=_unix(d), until=min(_unix(d + timedelta(days=1)), int(time.time())))
            for x in r.get("data") or []:
                if x.get("name") in total:
                    out[d.isoformat()][total[x["name"]]] = (x.get("total_value") or {}).get("value")
        except (ErroToken, ErroLimite):
            raise
        except Exception as e:  # noqa: BLE001
            log(f"  dia {d}: {e}")
            continue
        if d < hoje - timedelta(days=2):
            feitos.add(d.isoformat())
    est["dias_ok"] = sorted(feitos)[-120:]
    return list(out.values())


def _insights_post(mid, tok, ruins):
    pedir = [m for m in METRICAS_POST if m not in ruins]
    try:
        r = _get(f"{mid}/insights", tok, metric=",".join(pedir))
        return {x["name"]: (x.get("values") or [{}])[0].get("value") for x in r.get("data") or []}
    except (ErroToken, ErroLimite):
        raise
    except Exception:  # noqa: BLE001 — alguma métrica não vale para esse tipo de post: uma a uma
        out = {}
        for m in pedir:
            try:
                r = _get(f"{mid}/insights", tok, metric=m)
                out[m] = r["data"][0]["values"][0]["value"]
            except (ErroToken, ErroLimite):
                raise
            except Exception:  # noqa: BLE001
                ruins.add(m)
        return out


def posts_e_comentarios(tok, est, eu):
    midias, url = [], None
    r = _get("me/media", tok, fields="id,caption,media_type,media_product_type,timestamp,permalink,like_count,"
                                     "comments_count,thumbnail_url,media_url", limit=50)
    for _ in range(4):  # até 200 posts
        midias += r.get("data") or []
        url = (r.get("paging") or {}).get("next")
        if not url:
            break
        r = _get(url, tok)
    st_posts = est.setdefault("posts", {})
    agora = time.time()
    limite_90 = datetime.now(timezone.utc) - timedelta(days=90)
    posts, eventos, n_ins, n_com = [], [], 0, 0
    for m in midias:
        quando = _iso(m["timestamp"])
        tipo = "reels" if m.get("media_product_type") == "REELS" else {
            "CAROUSEL_ALBUM": "carrossel", "IMAGE": "foto", "VIDEO": "vídeo"}.get(m.get("media_type"), "post")
        sp = st_posts.setdefault(m["id"], {})
        p = {"id": m["id"], "em": m["timestamp"], "tipo": tipo, "legenda": (m.get("caption") or "").split("\n")[0][:200],
             "link": m.get("permalink"), "curtidas": m.get("like_count"), "comentarios": m.get("comments_count"),
             # miniatura para o painel (link do próprio Instagram; vence em alguns dias, mas é renovado a cada rodada)
             "capa": m.get("thumbnail_url") or (m.get("media_url") if m.get("media_type") != "VIDEO" else None)}
        if quando >= limite_90 and agora - sp.get("t", 0) > 6 * 3600 and n_ins < MAX_INSIGHTS_POST:
            ruins = set(sp.get("ruins") or [])
            ins = _insights_post(m["id"], tok, ruins)
            n_ins += 1
            sp.update(t=agora, ruins=sorted(ruins), ins=ins)
        ins = sp.get("ins") or {}
        p.update(visualizacoes=ins.get("views"), alcance=ins.get("reach"), compartilhamentos=ins.get("shares"),
                 salvos=ins.get("saved"))
        if ins.get("likes") is not None:
            p["curtidas"] = ins["likes"]
        posts.append(p)
        n = m.get("comments_count") or 0
        if n and sp.get("n_com") != n and n_com < MAX_COMENTARIOS:
            n_com += 1
            cs = _get(f"{m['id']}/comments", tok, fields="id,text,timestamp,from{id,username},username", limit=50)
            for c in cs.get("data") or []:
                quem = ((c.get("from") or {}).get("username") or c.get("username") or "").lower()
                if not quem or quem == eu:
                    continue
                eventos.append({"canal": "ig_comentario", "ext_id": c["id"], "pessoa": "ig:" + quem, "nome": "@" + quem,
                                "contato": "@" + quem, "em": c.get("timestamp"), "texto": (c.get("text") or "")[:300],
                                "ref": m.get("permalink") or ""})
            sp["n_com"] = n
    return posts, eventos


def conversas(tok, est, eu):
    """Direct: quem mandou mensagem (cada mensagem recebida é um contato) e se a empresa respondeu por último."""
    corte = est.get("dm_ate")
    eventos, respondidos = [], []
    r = _get("me/conversations", tok, platform="instagram",
             fields="id,updated_time,participants,messages.limit(30){id,created_time,from,message}", limit=25)
    mais_nova = corte
    parar = False
    for _ in range(8):
        for cv in r.get("data") or []:
            upd = cv.get("updated_time") or ""
            if corte and upd and upd < corte:
                parar = True
                break
            mais_nova = max(mais_nova or "", upd)
            outros = [p for p in ((cv.get("participants") or {}).get("data") or []) if (p.get("username") or "").lower() != eu]
            if not outros:
                continue
            quem = (outros[0].get("username") or "").lower()
            msgs = (cv.get("messages") or {}).get("data") or []  # mais nova primeiro
            for msg in msgs:
                de = ((msg.get("from") or {}).get("username") or "").lower()
                if de and de != eu:
                    eventos.append({"canal": "ig_dm", "ext_id": msg["id"], "pessoa": "ig:" + quem, "nome": "@" + quem,
                                    "contato": "@" + quem, "em": msg.get("created_time"),
                                    "texto": (msg.get("message") or "(foto, áudio ou anexo)")[:300],
                                    "ref": "https://www.instagram.com/direct/inbox/"})
            if msgs:
                ultimo = ((msgs[0].get("from") or {}).get("username") or "").lower()
                respondidos.append({"conta": quem, "respondido": ultimo == eu})
        url = (r.get("paging") or {}).get("next")
        if parar or not url:
            break
        r = _get(url, tok)
    if mais_nova:
        # próxima rodada só olha o que mudou (com 1 dia de folga)
        est["dm_ate"] = (_iso(mais_nova) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+0000")
    return eventos, respondidos


def coletar_conta(cliente, conta, tok, est):
    perfil = _get("me", tok, fields="username,followers_count,media_count")
    eu = (perfil.get("username") or conta).lower()
    if eu != conta.lower():
        return {"cliente": cliente, "conta": conta, "erro": f"o token é de outra conta (@{eu})"}
    dias = dias_do_perfil(tok, est)
    posts, ev_com = posts_e_comentarios(tok, est, eu)
    ev_dm, resp = conversas(tok, est, eu)
    return {"cliente": cliente, "conta": conta, "perfil": {"seguidores": perfil.get("followers_count"),
                                                           "posts": perfil.get("media_count")},
            "dias": dias, "posts": posts, "eventos": ev_com + ev_dm, "respondidos": resp}


def mandar(painel, chave, dados):
    req = urllib.request.Request(f"{painel.rstrip('/')}/api/coleta", data=json.dumps(dados, ensure_ascii=False).encode(),
                                 headers={"Content-Type": "application/json", "X-Chave": chave,
                                          "User-Agent": "painel-clientes-coletor/1"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def main():
    global ESTADO
    ver = "--ver" in sys.argv
    painel = sys.argv[sys.argv.index("--painel") + 1] if "--painel" in sys.argv else PAINEL
    if painel != PAINEL:  # painel de teste: estado próprio (senão os dias "feitos" no teste faltariam no de verdade)
        ESTADO = ESTADO.with_name("coletor_estado_teste.json")
    clientes = (_ler(CONFIG, {}).get("clientes") or [])
    chave = (_ler(CHAVES, {}) or {}).get("admin")
    if not chave and not ver:
        log("sem chave de admin em segredos\\chaves.json — rode o publicar.py primeiro")
        return
    tokens = {}
    for c in _ler(CREDS, []):
        nome = str(c.get("name") or "").lower().replace("instagram", "").strip()
        tok = (c.get("data") or {}).get("accessToken")
        if nome and tok:
            tokens[nome] = tok
    estado = _ler(ESTADO, {})
    vivas = set()  # contas cujo token respondeu nesta rodada (entram na renovação do token)
    for cl in clientes:
        # conta lida pela sessão (coletar_instagram_http.py): mandar "sem acesso à API" aqui apagaria o status bom dela
        if not cl.get("ativo", True) or cl.get("instagram_http"):
            continue
        for conta in cl.get("instagram") or []:
            conta = conta.lstrip("@").lower()
            k = f"{cl['id']}:{conta}"
            antes = copy.deepcopy(estado.get(k) or {})  # volta a este se a coleta ou o envio falhar
            est = estado.setdefault(k, {})
            tok = tokens.get(conta)
            t0 = time.time()
            if not tok:
                dados = {"cliente": cl["id"], "conta": conta,
                         "erro": "sem acesso à API desta conta (falta conectar o Instagram ao app)"}
            else:
                try:
                    dados = coletar_conta(cl["id"], conta, tok, est)
                except ErroToken as e:
                    dados = {"cliente": cl["id"], "conta": conta,
                             "erro": f"acesso do Instagram vencido: renovar o token ({sem_token(e)[:120]})"}
                except ErroLimite as e:
                    log(f"@{conta}: limite da API, fica para a próxima rodada ({e})")
                    estado[k] = antes
                    continue
                except Exception as e:  # noqa: BLE001
                    log(f"@{conta}: falhou {type(e).__name__}: {sem_token(e)[:200]}")
                    estado[k] = antes
                    continue
            resumo = (dados.get("erro") or f"{len(dados.get('dias') or [])} dias, {len(dados.get('posts') or [])} posts, "
                      f"{len(dados.get('eventos') or [])} contatos lidos")
            if ver:
                log(f"[ver] {cl['id']} @{conta}: {resumo}")
                continue
            if not dados.get("erro"):
                vivas.add(conta)
            try:
                r = mandar(painel, chave, dados)
                log(f"{cl['id']} @{conta}: {resumo} -> painel {r} ({time.time() - t0:.0f} s)")
            except Exception as e:  # noqa: BLE001
                log(f"{cl['id']} @{conta}: painel não recebeu ({type(e).__name__}: {str(e)[:160]})")
                estado[k] = antes  # os dias "feitos" só valem se o painel recebeu
                continue
            _salvar(ESTADO, estado)
    if not ver and painel == PAINEL and vivas:
        renovar_tokens(sorted(vivas), estado)


def renovar_tokens(contas, estado):
    """Token do Instagram vence em 60 dias se ninguém renovar (foi assim que os dos produtos morreram em 24/10).
    1x por dia passa as contas que responderam pelo renovar_token_insta.py (ele só renova o que tem 7+ dias, copia o
    arquivo antes e grava de forma atômica)."""
    hoje = datetime.now(FUSO).date().isoformat()
    if estado.get("_tokens_conferidos_em") == hoje or not RENOVAR.exists():
        return
    try:
        import importlib.util
        import io
        from contextlib import redirect_stdout
        spec = importlib.util.spec_from_file_location("renovar_token_insta", RENOVAR)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        saida = io.StringIO()
        with redirect_stdout(saida):
            mod.renovar(contas)
        for ln in saida.getvalue().splitlines():
            if ln.strip():
                log(f"token: {sem_token(ln)[:200]}")
        estado["_tokens_conferidos_em"] = hoje
        _salvar(ESTADO, estado)
    except Exception as e:  # noqa: BLE001 — renovar é bônus: nunca derruba a coleta
        log(f"renovar tokens: {type(e).__name__}: {sem_token(e)[:200]}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
