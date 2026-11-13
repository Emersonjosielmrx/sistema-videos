#!/usr/bin/env python3
"""notificar_telegram.py - avisos dos canais do YouTube no Telegram (config/telegram.json).

A tarefa NotificarTelegram roda a cada 5 min (pythonw, sem janela). Cada rodada:
  - posta no YouTube as respostas que o dono escreveu no Telegram (marcando a msg do comentario) e confirma;
  - auto-resposta (config auto_resposta): comentario recente sem resposta do dono em X h -> a IA responde como ele;
  - a cada ~30 min: comentarios novos (com traducao se nao for portugues), inscritos novos e videos que
    passaram de 5.000 views (a marca de 1.000 só fica anotada desde 23/10);
  - a cada ~30 min tambem: o que foi postado (YouTube de todos os projetos, TikTok, Instagram, MS Energy), filas
    vazias/acabando (onde produzir mais) e contas deslogadas (TikTok/Instagram);
  - 1x por dia, a partir das 08:00: resumo com o ranking de views das ultimas 24 h (canais e videos) e as filas.
Manual: --resumo (forca o resumo), --retroativo (comentarios sem resposta das ultimas 3 semanas), --responder.
Estado em config/telegram_estado.json; log em logs/telegram.log.
"""
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout:
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import youtube_poster as yp  # noqa: E402
import metas_canal  # noqa: E402

ROOT = BIN.parent
CFG = json.loads((ROOT / "config" / "telegram.json").read_text("utf-8"))
AVISOS = CFG.get("notificar", {})
REDE = json.loads((ROOT / "config" / "rede_canais.json").read_text("utf-8"))
CREDS = {c["id"]: c for c in json.loads(Path(r"D:\credenciais-canais\youtube_canais.json").read_text("utf-8"))}
ESTADO = ROOT / "config" / "telegram_estado.json"
LOG = ROOT / "logs" / "telegram.log"
API_YT = "https://www.googleapis.com/youtube/v3"
CANAIS = [c for c in REDE["canais"] if c.get("status") != "suspenso"]
PROPRIOS = {c["yt_id"] for c in REDE["canais"] if c.get("yt_id")} | {"UCiPlcsKHRQK9ZmbdvzDF0DQ", "UCTLn9GymqU0AJ4pPUizRuzA"}
# 31/10 (dona: "filtrar os meus comentários feitos na minha conta pessoal e mandar só os de pessoas de verdade"): o
# filtro só pelo ID do canal deixava passar a conta pessoal do telão (@Fabricadeautomacoesia: 17 de 17 avisos dela em
# vídeos que o telão comentou) — agora também pelo @ (canais da rede + config/comentarios_proprios.json)
PROPRIOS_ARQ = ROOT / "config" / "comentarios_proprios.json"
PROPRIOS_AT = {c["handle"].lower() for c in REDE["canais"] if c.get("handle")}
try:
    _pa = json.loads(PROPRIOS_ARQ.read_text("utf-8-sig"))
    PROPRIOS |= set(_pa.get("canal_ids", []))
    PROPRIOS_AT |= {h.lower() for h in _pa.get("handles", [])}
except (OSError, ValueError):
    pass
# 31/10 (dona: "o bot de comentários só recebeu 2 mensagens, cai tudo no principal"): comentário sai no bot de
# comentários e a resposta da dona é lida lá (mapa_respostas com chave "com:<message_id>")
try:
    BOT_COMENT = json.loads((ROOT / "config" / "telegram_bots.json").read_text("utf-8-sig"))["comentarios"]["bot_token"]
except (OSError, ValueError, KeyError):
    BOT_COMENT = None


def proprio(sn):
    """True se o comentário (snippet do topLevelComment) é de canal/conta nossa ou da conta pessoal da dona."""
    return ((sn.get("authorChannelId") or {}).get("value") in PROPRIOS
            or (sn.get("authorDisplayName") or "").lower() in PROPRIOS_AT)
MONITOR_MIN = 28
LONGOS = ("completo", "longo", "compilado")  # tipo no uploads_ledger.jsonl
# 31/10: título que o YouTube devolve (a pasta do vídeo é limpa depois de postar e o aviso saía "video.mp4")
TITULOS = {}
COMENTARIOS_STUDIO = ROOT / "config" / "comentarios_pelo_studio.json"  # sem_token.py lê esses pelo Studio
HORA_RESUMO = 8
MARCO_VIEWS = 1000
MARCO2_VIEWS = 5000  # A MARCA agora (dona 23/10: "põe 5 em todos os lugares"): mil ficou comum; 10 mil quase ninguém
AVISA_MIL = False    # o aviso/telão de 1.000 parou (o de 5.000 ficou no lugar); True volta
# ESCADA de marcos (dona 23/10: "podemos criar mais de uma meta, como a de 10, e vamos subindo com o tempo"). Pra subir a
# régua: acrescentar/tirar degraus aqui. O 1º degrau é o que o telão e as métricas tratam como "a marca" (MARCO2_VIEWS).
MARCOS = [5000, 10000, 25000, 50000, 100000, 250000, 500000, 1000000]
_PISO_CACHE = {}


def _piso_auto(dados):
    """09/11 (dona: "metas inteligentes auto ajustáveis, tanto pra adicionar quanto remover"): o 1º degrau que avisa
    é o menor que até ~10% dos vídeos recentes alcançam. Muitos vídeos passando de 5 mil -> piso sobe pra 10/25 mil;
    poucos -> volta pra 5 mil. Desligar: METAS_VIEWS_AUTO=0 (avisa todos os degraus)."""
    if __import__("os").environ.get("METAS_VIEWS_AUTO", "1") == "0":
        return 0
    if "piso" in _PISO_CACHE:
        return _PISO_CACHE["piso"]
    views = sorted((v["views"] for d in dados for v in d.get("videos", [])), reverse=True)
    piso = MARCOS[0]
    if len(views) >= 20:
        p90 = views[max(0, len(views) // 10 - 1)]  # o que os 10% melhores fazem
        piso = max([MARCOS[0]] + [m for m in MARCOS if m <= p90])
    _PISO_CACHE["piso"] = piso
    return piso
MARCO_EMOJI = {5000: "🔥", 10000: "🚀", 25000: "💎", 50000: "👑", 100000: "🏆"}


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M}] {msg}"
    print(linha)
    try:
        if LOG.exists() and LOG.stat().st_size > 500_000:
            LOG.replace(LOG.with_suffix(".log.old"))
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def e(x):
    return html.escape(str(x), quote=False)


def n(x):
    return f"{x:,}".replace(",", ".")


def data_utc(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def hora_local(iso):
    try:
        return data_utc(iso).astimezone().strftime("%d/%m %H:%M")
    except ValueError:
        return iso[:16]


def idade(iso):
    h = (datetime.now(timezone.utc) - data_utc(iso)).total_seconds() / 3600
    return f"{h:.0f} h" if h < 48 else f"{h / 24:.0f} dias"


def carregar_estado():
    return json.loads(ESTADO.read_text("utf-8")) if ESTADO.exists() else {}


def salvar_estado(est):
    est["comentarios_vistos"] = est.get("comentarios_vistos", [])[-2000:]
    if len(est.get("titulos") or {}) > 4000:
        est["titulos"] = dict(list(est["titulos"].items())[-4000:])
    mapa = est.get("mapa_respostas", {})
    if len(mapa) > 2000:
        est["mapa_respostas"] = dict(sorted(mapa.items(), key=lambda kv: int(kv[0].removeprefix("com:")))[-1500:])
    conv = est.get("conversas", {})
    if len(conv) > 600:
        est["conversas"] = dict(sorted(conv.items(), key=lambda kv: kv[1].get("ate", ""))[-400:])
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(ESTADO)


# --- Telegram ---

def tg(metodo, dados, token=None):
    url = f"https://api.telegram.org/bot{token or CFG['bot_token']}/{metodo}"
    corpo = json.dumps(dados).encode("utf-8")
    for tentativa in range(3):
        try:
            req = urllib.request.Request(url, corpo, {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as ex:
            if ex.code == 429:
                time.sleep(5 * (tentativa + 1))
                continue
            log(f"Telegram {metodo}: HTTP {ex.code} {ex.read()[:200]!r}")
            return None
        except Exception as ex:  # noqa: BLE001
            log(f"Telegram {metodo}: {ex}")
            return None
    return None


def avisar(texto, origem, importante=False, chave=None):
    """Pelo portão único (D:\\video-fila\\avisos.py, dono 19/10): repetido não sai, rotina vai pro resumo 3x/dia.
    Comentário e resposta continuam no enviar() direto: a resposta ao YouTube precisa do message_id do bot geral."""
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import avisos
        return avisos.enviar(texto, origem, importante=importante, chave=chave)
    except Exception as ex:  # noqa: BLE001
        log(f"portão de avisos fora ({ex}); mando direto")
        return enviar(texto)


def enviar(texto, responder_a=None, coment=False):
    """coment=True: no bot de comentários (se não houver, no geral)."""
    if not CFG.get("ativo"):
        return None
    dados = {"chat_id": CFG["chat_id"], "text": texto, "parse_mode": "HTML", "disable_web_page_preview": True}
    if responder_a:
        dados["reply_parameters"] = {"message_id": responder_a, "allow_sending_without_reply": True}
    r = tg("sendMessage", dados, BOT_COMENT if coment else None)
    return r["result"]["message_id"] if r and r.get("ok") else None


def traduzir(texto):
    if len(texto.strip()) < 3:
        return None
    url = ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=pt&dt=t&q="
           + urllib.parse.quote(texto[:500]))
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            d = json.loads(r.read())
    except Exception:  # noqa: BLE001
        return None
    if str(d[2] if len(d) > 2 else "").startswith("pt"):
        return None
    trad = "".join(p[0] for p in d[0] if p and p[0]).strip()
    return trad if trad and trad != texto.strip() else None


# --- YouTube ---

def yt(tok, caminho, corpo=None):
    hdr = {"Authorization": f"Bearer {tok}"}
    dados = None
    if corpo is not None:
        dados = json.dumps(corpo).encode("utf-8")
        hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{API_YT}/{caminho}", dados, hdr)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def token(canal):
    for cid in canal.get("creds", []):
        c = CREDS.get(cid)
        if c and c.get("refresh_token"):
            try:
                return yp.refresh_access_token(c), cid
            except Exception:  # noqa: BLE001
                pass
    return None, None


def coletar(canal, estado, comentarios):
    """3 unidades de cota por canal: channels + videos + commentThreads (playlistItems so quando muda o nº de videos)."""
    tok, cred_id = token(canal)
    if not tok:
        return None
    ch = yt(tok, "channels?part=statistics,contentDetails&mine=true")["items"][0]
    s = ch["statistics"]
    cache = estado.setdefault("videos_canal", {})
    c = cache.get(canal["slug"])
    if not c or c["n"] != s.get("videoCount"):
        up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        itens = yt(tok, f"playlistItems?part=contentDetails&maxResults=50&playlistId={up}").get("items", [])
        c = cache[canal["slug"]] = {"n": s.get("videoCount"), "ids": [i["contentDetails"]["videoId"] for i in itens]}
    videos = []
    if c["ids"]:
        for v in yt(tok, f"videos?part=snippet,statistics,status&id={','.join(c['ids'])}").get("items", []):
            videos.append({"id": v["id"], "titulo": v["snippet"]["title"], "pub": v["snippet"]["publishedAt"],
                           "views": int(v["statistics"].get("viewCount", 0)),
                           "privacy": (v.get("status") or {}).get("privacyStatus")})
    threads = []
    pelo_studio = _ler_json(COMENTARIOS_STUDIO, [])
    if comentarios and cred_id not in pelo_studio:
        try:
            threads = yt(tok, f"commentThreads?part=snippet&allThreadsRelatedToChannelId={ch['id']}"
                              "&maxResults=20&order=time").get("items", [])
        except urllib.error.HTTPError as ex:
            log(f"{canal['nome']}: comentarios HTTP {ex.code}")
            if ex.code == 403:  # 23/10: a autorização não deixa ler comentário -> o sem_token lê pelo Studio
                COMENTARIOS_STUDIO.write_text(json.dumps(pelo_studio + [cred_id], indent=1), encoding="utf-8")
                log(f"{canal['nome']}: comentários passam a ser lidos pelo Studio (sem_token.py)")
    return {"canal": canal, "cred_id": cred_id, "ch_id": ch["id"], "subs": int(s.get("subscriberCount", 0)),
            "views": int(s.get("viewCount", 0)), "videos": videos, "threads": threads}


def coletar_todos(estado, comentarios):
    dados = []
    for canal in CANAIS:
        try:
            d = coletar(canal, estado, comentarios)
            if d:
                dados.append(d)
        except urllib.error.HTTPError as ex:
            log(f"{canal['nome']}: HTTP {ex.code}")
        except Exception as ex:  # noqa: BLE001
            log(f"{canal['nome']}: {ex}")
    return dados


# --- Comentarios ---

def notificar_comentario(estado, canal, cred_id, t):
    c = t["snippet"]["topLevelComment"]["snippet"]
    autor = c.get("authorDisplayName", "?")
    texto = (c.get("textOriginal") or "")[:600]
    video_id = t["snippet"].get("videoId", "")
    trad = traduzir(texto)
    linhas = [f"<b>{e(canal['nome'])}</b>", f"De: {e(autor)}", e(texto)]
    if trad:
        linhas.append(f"<i>[Tradução]: {e(trad)}</i>")
    linhas.append(f"<a href='https://youtu.be/{video_id}'>Vídeo</a> | {hora_local(c.get('publishedAt', ''))}")
    linhas.append("<code>Para responder: marque esta msg e digite a resposta</code>")
    msg_id = enviar("\n".join(linhas), coment=True)
    if msg_id:
        estado.setdefault("mapa_respostas", {})[("com:" if BOT_COMENT else "") + str(msg_id)] = {
            "comment_id": t["snippet"]["topLevelComment"]["id"], "cred_id": cred_id, "canal": canal["nome"],
            "video_id": video_id, "autor": autor, "ts": datetime.now(timezone.utc).isoformat(timespec="minutes")}
    return msg_id


CONVERSA_DIAS = 3     # segue a conversa por até 3 dias depois da última resposta do canal
CONVERSA_TURNOS = 4   # no máx. 4 respostas nossas por conversa (não vira papo infinito com robô)
CONVERSA_POR_RODADA = 40  # 1 unidade de cota cada (comments?parentId)


def _respostas_do_fio(tok, comment_id):
    """Respostas dentro do fio (ordem de data), via comments?parentId — o commentThreads só traz o comentário de cima."""
    itens, pagina = [], ""
    for _ in range(3):
        d = yt(tok, f"comments?part=snippet&parentId={comment_id}&maxResults=100&textFormat=plainText"
                    + (f"&pageToken={pagina}" if pagina else ""))
        itens += d.get("items", [])
        pagina = d.get("nextPageToken")
        if not pagina:
            break
    return sorted(itens, key=lambda c: c["snippet"].get("publishedAt", ""))


def _nossa(sn):
    """Resposta do próprio canal do vídeo (ou de conta nossa)."""
    return proprio(sn) or (sn.get("authorChannelId") or {}).get("value") == sn.get("channelId")


def seguir_conversas(estado):
    """02/11 dona: "ela só responde uma; a resposta da resposta ela não responde". O monitor lia só o comentário de cima
    (commentThreads) e a auto-resposta pulava o fio que já tinha resposta do canal. Agora: fio que o canal respondeu
    (Telegram ou auto) nos últimos CONVERSA_DIAS é relido; resposta NOVA de outra pessoa depois da nossa vira aviso no
    Telegram ("resposta à sua resposta", dá pra responder marcando) e entra na auto-resposta com a conversa inteira."""
    mapa = estado.setdefault("mapa_respostas", {})
    conv = estado.setdefault("conversas", {})
    agora = datetime.now(timezone.utc)
    for m in mapa.values():  # fio respondido entra na lista de conversas seguidas
        if m.get("respondido") and m.get("comment_id") and m["comment_id"] not in conv:
            conv[m["comment_id"]] = {"cred_id": m["cred_id"], "canal": m["canal"], "video_id": m.get("video_id", ""),
                                     "ate": m["respondido"], "turnos": 1}
    vivas = sorted(((cid, c) for cid, c in conv.items() if not c.get("fim")
                    and agora - data_utc(c["ate"]) < timedelta(days=CONVERSA_DIAS)),
                   key=lambda kv: kv[1]["ate"], reverse=True)[:CONVERSA_POR_RODADA]
    toks, novas = {}, 0
    for cid, c in vivas:
        try:
            if c["cred_id"] not in toks:
                toks[c["cred_id"]] = yp.refresh_access_token(CREDS[c["cred_id"]])
            fio = _respostas_do_fio(toks[c["cred_id"]], cid)
        except urllib.error.HTTPError as ex:
            if ex.code in (403, 404):
                c["fim"] = f"HTTP {ex.code}"
            continue
        except Exception as ex:  # noqa: BLE001
            log(f"conversa {c['canal']}: {ex}")
            continue
        nossas = [r for r in fio if _nossa(r["snippet"])]
        c["turnos"] = max(1, len(nossas))
        if nossas:  # a dona pode ter respondido pelo Studio: a régua anda junto
            ult_nossa = data_utc(nossas[-1]["snippet"]["publishedAt"])
            if ult_nossa > data_utc(c["ate"]):
                c["ate"] = ult_nossa.isoformat(timespec="seconds")
        delas = [r for r in fio if not _nossa(r["snippet"])
                 and data_utc(r["snippet"]["publishedAt"]) > data_utc(c["ate"])]
        if not delas:
            continue
        ult = delas[-1]  # várias seguidas = responde a última, com as outras no contexto
        s = ult["snippet"]
        c["ate"] = data_utc(s["publishedAt"]).isoformat(timespec="seconds")
        if c["turnos"] >= CONVERSA_TURNOS:
            c["fim"] = "turnos"
            continue
        autor = s.get("authorDisplayName", "?")
        texto = (s.get("textOriginal") or "")[:600]
        linhas = [f"<b>{e(c['canal'])}</b> — <b>respondeu à sua resposta</b>", f"De: {e(autor)}", e(texto)]
        trad = traduzir(texto)
        if trad:
            linhas.append(f"<i>[Tradução]: {e(trad)}</i>")
        linhas.append(f"<a href='https://youtu.be/{c['video_id']}'>Vídeo</a> | {hora_local(s.get('publishedAt', ''))}")
        linhas.append("<code>Para responder: marque esta msg e digite a resposta</code>")
        msg_id = enviar("\n".join(linhas), coment=True)
        if msg_id:
            mapa[("com:" if BOT_COMENT else "") + str(msg_id)] = {
                "comment_id": cid, "reply_id": ult["id"], "cred_id": c["cred_id"], "canal": c["canal"],
                "video_id": c["video_id"], "autor": autor, "ts": agora.isoformat(timespec="minutes")}
            novas += 1
            time.sleep(0.4)
    if vivas:
        log(f"conversas: {len(vivas)} fio(s) relido(s), {novas} resposta(s) nova(s) à nossa resposta")


def _marco_telao(v, canal):
    """22/10 (dono): o telão mostra os marcos de views com botão pra abrir o vídeo — o aviso do Telegram perde o link."""
    try:
        with open(ROOT / "logs" / "marcos_views.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "video_id": v["id"],
                                "canal": canal.get("nome"), "titulo": v.get("titulo"), "views": v.get("views")},
                               ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def monitorar(estado, dados):
    vistos_l = estado.setdefault("comentarios_vistos", [])
    vistos = set(vistos_l)
    insc = estado.setdefault("inscritos", {})
    primeira_mil = "mil_views" not in estado
    mil = set(estado.setdefault("mil_views", []))
    # 23/10 (dona: "muitos vídeos dão mais de mil; quero subir a régua, mas não tanto a ponto de não ter nenhum"): 2º
    # marco em MARCO2_VIEWS (5 mil). Medido no dia: 54 vídeos passaram de mil, 9 de 5 mil, 1 entre 2 e 10 mil.
    # 23/10 (dona: "não precisamos ficar só com 5 mil, podemos criar mais de uma meta como a de 10 ou outras e vamos
    # subindo com o tempo"): ESCADA de marcos (MARCOS). Cada degrau avisa 1x por vídeo; se um vídeo pula vários de uma
    # vez, sai só o aviso do maior. Degrau novo na lista: os vídeos que já passavam dele vão numa lista única.
    est_m = estado.setdefault("marcos_views", {})
    if "5000" not in est_m and "cinco_mil_views" in estado:  # 1ª versão (só 5 mil) -> escada
        est_m["5000"] = estado.pop("cinco_mil_views")
    novos_degraus = {m for m in MARCOS if str(m) not in est_m}
    passou = {m: set(est_m.setdefault(str(m), [])) for m in MARCOS}
    ja_marcos = []
    ja_passavam, coments, caminhos = [], 0, None
    primeiro_rel = "views_nivel" not in estado
    for d in dados:
        canal, slug = d["canal"], d["canal"]["slug"]
        if AVISOS.get("comentarios"):
            for t in reversed(d["threads"]):
                if t["id"] in vistos:
                    continue
                nosso = proprio(t["snippet"]["topLevelComment"]["snippet"])
                if nosso or notificar_comentario(estado, canal, d["cred_id"], t):
                    vistos.add(t["id"])
                    vistos_l.append(t["id"])
                    coments += not nosso
                    time.sleep(0.4)
        # 08/11 (dona: "agregar inscritos pra uma quantidade x em x tempo como as metas de views; metas inteligentes
        # auto ajustáveis"): era 1 Telegram por inscrito (364 em 7 dias). Agora só quando o canal cruza um DEGRAU de
        # inscritos — degrau automático pelo tamanho do canal (passo = 10% do total arredondado: 64 -> de 10 em 10,
        # 1.200 -> de 100 em 100). Desligar: INSCRITOS_DEGRAU=0 (volta ao aviso por inscrito).
        # 10/11 (dona: "metas com base na média daquele canal e não fixas como 10 em 10; quero saber quando algo está
        # melhor do que de fato deveria"): ganho de inscritos de HOJE contra o ganho médio por dia do canal (7 dias).
        # Avisa em 2x, 4x, 8x... o normal, 1x por nível por dia. Desligar: METAS_RELATIVAS=0 (volta ao degrau fixo).
        if metas_canal.LIGADO:
            serie = estado.setdefault("inscritos_dia", {}).setdefault(slug, {})
            base, ganho, normal = metas_canal.inscritos_hoje(slug, d["subs"], serie)
            metas_canal.anotar(serie, d["subs"])
            k = metas_canal.nivel(ganho, normal, metas_canal.NIVEIS_INSCRITOS, metas_canal.MIN_GANHO_INSCRITOS)
            niv = estado.setdefault("inscritos_nivel", {})
            hoje = datetime.now().date().isoformat()
            ja = niv.get(slug, {}).get("k", 0) if niv.get(slug, {}).get("dia") == hoje else 0
            if AVISOS.get("inscritos") and base is not None and k > ja:
                normal_txt = (f"+{metas_canal.n(normal)} por dia (média de 7 dias)" if normal is not None
                              else "canal ainda sem média de 7 dias")
                avisar(f"👥 <b>Inscritos: {metas_canal.n(base)} → {metas_canal.n(d['subs'])} "
                       f"(+{metas_canal.n(ganho)} hoje, {metas_canal.vezes(ganho, normal)} o normal)</b>\n"
                       f"Canal: {e(canal['nome'])}\n"
                       f"Normal do canal: {normal_txt}\n"
                       f"E-mail: {e(_email(CREDS.get(d['cred_id'])) or '?')}",
                       "inscritos", importante=True, chave=f"inscritos:{slug}:{hoje}:{k}")
            if k > ja:
                niv[slug] = {"dia": hoje, "k": k}
        elif AVISOS.get("inscritos") and slug in insc and d["subs"] > insc[slug]:
            antes, agora = insc[slug], d["subs"]
            if __import__("os").environ.get("INSCRITOS_DEGRAU", "1") == "0":
                passo = 1
            else:  # ~10% do total: 64 -> 10, 640 -> 10, 1.200 -> 100, 25.000 -> 1.000
                passo = max(10, 10 ** max(1, len(str(max(antes, 1))) - 2))
            if agora // passo > antes // passo:
                meta = (agora // passo) * passo
                avisar(f"🎉 <b>Meta de inscritos: {n(meta)}</b>\nCanal: {e(canal['nome'])}\n"
                       f"E-mail: {e(_email(CREDS.get(d['cred_id'])) or '?')}\n"
                       f"Total agora: {n(agora)} · próxima meta: {n(meta + passo)}",
                       "inscritos", importante=True, chave=f"inscritos:{slug}:{meta}")
        insc[slug] = d["subs"]
        tit = estado.setdefault("titulos", {})
        tit.update({v["id"]: v["titulo"] for v in d["videos"]})
        TITULOS.update(tit)
        mediana = None
        acima = []
        for v in d["videos"]:
            atingidos = [m for m in MARCOS if v["views"] >= m and v["id"] not in passou[m]]
            if atingidos:
                for m in atingidos:
                    passou[m].add(v["id"])
                topo = max(atingidos)
                if metas_canal.LIGADO:  # 10/11: views avisam pelo normal do canal (bloco abaixo), não pela escada fixa
                    pass
                elif topo in novos_degraus:  # degrau que acabou de entrar na escada: vai na lista, sem aviso avulso
                    ja_marcos.append((v, canal, topo))
                elif topo < _piso_auto(dados):  # 09/11: meta automática — abaixo do piso só fica anotado
                    pass
                elif AVISOS.get("mil_views"):
                    if caminhos is None:
                        caminhos = _caminho_por_id()
                    avisar("\n".join([f"{MARCO_EMOJI.get(topo, '🔥')} <b>{n(topo)} views!</b>",
                                      f"Canal: {e(canal['nome'])}",
                                      f"E-mail: {e(_email(CREDS.get(d['cred_id'])) or '?')}",
                                      f"Vídeo: {e(v['titulo'])}"]
                                     + _linhas_video(_video(caminhos.get(v["id"])), f"https://youtu.be/{v['id']}")
                                     + [f"Agora: {n(v['views'])} views · publicado há {idade(v['pub'])}"]),
                           "mil views", importante=True, chave=f"marco{topo}:{v['id']}")
                    _marco_telao(v, canal)
            if metas_canal.LIGADO and AVISOS.get("mil_views"):
                # 10/11: vídeo acima do normal DO CANAL (mediana dos vídeos com 2+ dias): 3x, 10x, 30x, 100x
                if mediana is None:
                    mediana = metas_canal.mediana_views(d["videos"]) or 0
                k = metas_canal.nivel(v["views"], mediana, metas_canal.NIVEIS_VIEWS, metas_canal.MIN_VIEWS)
                vniv = estado.setdefault("views_nivel", {})
                if mediana and k > vniv.get(v["id"], 0):
                    primeira_vez = v["id"] not in vniv
                    vniv[v["id"]] = k
                    # 1ª rodada com a regra nova: vídeo velho que já estava acima não vira aviso em massa
                    if not (primeiro_rel and primeira_vez):
                        acima.append((v, k))  # 11/11: 1 aviso por canal (abaixo), não 1 por vídeo
            if v["views"] < MARCO_VIEWS or v["id"] in mil:
                continue
            mil.add(v["id"])  # 23/10 (dona: "põe 5 mil em todos os lugares"): o de mil só fica anotado, não avisa
            if primeira_mil:
                ja_passavam.append((v, canal))
            elif AVISOS.get("mil_views") and AVISA_MIL:
                if caminhos is None:
                    caminhos = _caminho_por_id()
                avisar("\n".join([f"👀 <b>{n(MARCO_VIEWS)} views!</b>", f"Canal: {e(canal['nome'])}",
                                  f"E-mail: {e(_email(CREDS.get(d['cred_id'])) or '?')}",
                                  f"Vídeo: {e(v['titulo'])}"]
                                 + _linhas_video(_video(caminhos.get(v["id"])), f"https://youtu.be/{v['id']}")
                                 + [f"Agora: {n(v['views'])} views · publicado há {idade(v['pub'])}"]), "mil views")
                _marco_telao(v, canal)
        if acima:
            # 11/11 (dona: "5 avisos do mesmo canal de metas de visualização, só precisava da última"): 1 mensagem
            # por canal e rodada — o melhor vídeo completo em cima, os outros numa linha cada
            acima.sort(key=lambda x: -x[0]["views"])
            v, _k = acima[0]
            if caminhos is None:
                caminhos = _caminho_por_id()
            outros = [f"• {n(o['views'])} ({metas_canal.vezes(o['views'], mediana)}) — "
                      f"<a href='https://youtu.be/{o['id']}'>{e(o['titulo'][:60])}</a>" for o, _ in acima[1:8]]
            avisar("\n".join([f"📈 <b>{n(v['views'])} views — {metas_canal.vezes(v['views'], mediana)} o normal do canal</b>"
                              + (f" · +{len(acima) - 1} vídeo(s) também acima" if len(acima) > 1 else ""),
                              f"Canal: {e(canal['nome'])} (normal: {n(int(mediana))} views por vídeo)",
                              f"Vídeo: {e(v['titulo'])}"]
                             + _linhas_video(_video(caminhos.get(v["id"])), f"https://youtu.be/{v['id']}")
                             + [f"Publicado há {idade(v['pub'])}"]
                             + (["", "Também acima do normal:"] + outros if outros else [])
                             + [f"E-mail: {e(_email(CREDS.get(d['cred_id'])) or '?')}"]),
                   "mil views", importante=True, chave="rel:" + ",".join(f"{o['id']}{k}" for o, k in acima))
            for o, _k2 in acima:
                _marco_telao(o, canal)
    estado["mil_views"] = sorted(mil)
    for m in MARCOS:
        est_m[str(m)] = sorted(passou[m])
    if ja_marcos and AVISOS.get("mil_views"):
        ja_marcos.sort(key=lambda x: -x[0]["views"])
        enviar(f"<b>🔥 Escada de marcos de views: {', '.join(n(m) for m in MARCOS)}</b>\nVídeos que já tinham "
               "passado (daqui pra frente chega um aviso a cada degrau novo de cada vídeo):\n\n"
               + "\n".join(f"{n(v['views'])} ({n(t)}+) - <a href='https://youtu.be/{v['id']}'>{e(v['titulo'][:60])}</a> "
                           f"({e(c['nome'])})" for v, c, t in ja_marcos[:30]))
    if ja_passavam and AVISOS.get("mil_views") and AVISA_MIL:
        ja_passavam.sort(key=lambda x: -x[0]["views"])
        linhas = [f"{n(v['views'])} - <a href='https://youtu.be/{v['id']}'>{e(v['titulo'][:60])}</a> ({e(c['nome'])})"
                  for v, c in ja_passavam[:30]]
        enviar(f"<b>Vídeos que já tinham passado de {n(MARCO_VIEWS)} views</b>\n"
               "(daqui pra frente chega um aviso a cada vídeo novo que passar)\n\n" + "\n".join(linhas))
    log(f"monitor: {len(dados)} canais, {coments} comentario(s) novo(s)")


def retroativo(estado, semanas=3):
    vistos_l = estado.setdefault("comentarios_vistos", [])
    vistos = set(vistos_l)
    limite = datetime.now(timezone.utc) - timedelta(weeks=semanas)
    total = 0
    for canal in CANAIS:
        tok, cred_id = token(canal)
        if not tok:
            continue
        try:
            ch_id = yt(tok, "channels?part=id&mine=true")["items"][0]["id"]
            pagina, achados = "", []
            while True:
                d = yt(tok, f"commentThreads?part=snippet&allThreadsRelatedToChannelId={ch_id}&maxResults=100"
                            f"&order=time{'&pageToken=' + pagina if pagina else ''}")
                antigos = False
                for t in d.get("items", []):
                    c = t["snippet"]["topLevelComment"]["snippet"]
                    if data_utc(c.get("publishedAt", "")) < limite:
                        antigos = True
                        break
                    if (t["id"] not in vistos and not proprio(c)
                            and not t["snippet"].get("totalReplyCount")):
                        achados.append(t)
                pagina = d.get("nextPageToken")
                if antigos or not pagina:
                    break
            for t in reversed(achados):
                if notificar_comentario(estado, canal, cred_id, t):
                    vistos.add(t["id"])
                    vistos_l.append(t["id"])
                    total += 1
                    time.sleep(0.4)
            if achados:
                log(f"retroativo {canal['nome']}: {len(achados)} sem resposta")
        except urllib.error.HTTPError as ex:
            log(f"retroativo {canal['nome']}: HTTP {ex.code}")
        except Exception as ex:  # noqa: BLE001
            log(f"retroativo {canal['nome']}: {ex}")
    log(f"retroativo: {total} comentario(s) enviados")


VIGIA_FILA = Path(r"D:\hipercool-videos\workspace\vigia_perguntas.jsonl")
VIGIA_SCRIPT = Path(r"D:\hipercool-videos\bin\vigia_telegram.py")
MONITOR_OPUS = r"D:\monitor_opus.py"
MONITOR_OPUS_PY = r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe"
MONITOR_ARGON = r"D:\gemini-argo\monitor_argon.py"  # 27/10: "argon" no Telegram = cota do Argon agora
CREDITO_55 = r"D:\gemini-argo\credito_opus55.py"  # 27/10: "5.5" = crédito do Opus 5.5 (contas CC)
# 27/10 (dona: "ponha os 3 no bot opus"): comandos de crédito, lidos no bot geral E no bot do Opus; a resposta sai no
# bot do Opus (avisos.py: opus-monitor/argon-monitor -> bot "opus")
COMANDOS_CREDITO = {"opus": ["46"], "4.6": ["46"], "opus 4.6": ["46"], "5.5": ["55"], "opus 5.5": ["55"],
                    "argon": ["argon"], "creditos": ["46", "55", "argon"], "créditos": ["46", "55", "argon"],
                    "credito": ["46", "55", "argon"], "crédito": ["46", "55", "argon"]}


def _encaminhar_vigia(texto, message_id, resposta_a_texto=None, bot=None):
    """Grava a mensagem do dono na fila do vigia e dispara o processamento. bot: chave do telegram_bots.json por onde
    a resposta volta (01/11: "plantao"); None = bot geral."""
    import subprocess
    item = {"texto": texto, "message_id": message_id, "bot": bot,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if resposta_a_texto:
        item["contexto_reply"] = resposta_a_texto[:500]
    VIGIA_FILA.parent.mkdir(parents=True, exist_ok=True)
    with open(VIGIA_FILA, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    log(f"vigia: encaminhado '{texto[:80]}' (mid={message_id})")
    try:
        subprocess.Popen(
            [r"D:\hipercool-videos\venv\Scripts\python.exe", "-X", "utf8", str(VIGIA_SCRIPT), "--fila"],
            cwd=r"D:\hipercool-videos", creationflags=0x08000000,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:  # noqa: BLE001
        log(f"vigia: falha ao disparar: {ex}")


def _aprendizado_responder(message_id, texto):
    """True se a mensagem respondida era de um achado do D:\\video-fila\\aprendizado.py (aprova/reprova lá)."""
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.append(r"D:\video-fila")
        import aprendizado
        return aprendizado.responder(message_id, texto)
    except Exception as ex:  # noqa: BLE001
        log(f"aprendizado: resposta não tratada ({type(ex).__name__}: {ex})")
        return False


def _responder_aprendizado(estado):
    """21/10: os achados saem no bot de aprendizado (config/telegram_bots.json); o SIM/NÃO do dono chega nele."""
    try:
        b = json.loads((ROOT / "config" / "telegram_bots.json").read_text("utf-8"))["aprendizado"]
        url = f"https://api.telegram.org/bot{b['bot_token']}/getUpdates"
        corpo = json.dumps({"offset": estado.get("tg_update_id_aprendizado", 0), "timeout": 0,
                            "allowed_updates": ["message"]}).encode("utf-8")
        with urllib.request.urlopen(urllib.request.Request(url, corpo, {"Content-Type": "application/json"}),
                                    timeout=40) as r:
            res = json.loads(r.read())
    except Exception as ex:  # noqa: BLE001
        log(f"bot do aprendizado: {type(ex).__name__}: {str(ex)[:120]}")
        return
    for upd in res.get("result") or []:
        estado["tg_update_id_aprendizado"] = upd["update_id"] + 1
        msg = upd.get("message") or {}
        orig, texto = msg.get("reply_to_message"), (msg.get("text") or "").strip()
        if orig and texto and msg.get("chat", {}).get("id") == CFG["chat_id"]:
            _aprendizado_responder(orig["message_id"], texto)


def _comando_credito(texto):
    """True se o texto é comando de crédito; dispara quem responde (no bot do Opus): D:\\monitor_opus.py (Opus 4.6),
    credito_opus55.py (Opus 5.5) e monitor_argon.py (Argon)."""
    import subprocess  # 27/10: o bloco antigo do "opus" usava subprocess sem importar (o comando nunca disparava)
    alvos = COMANDOS_CREDITO.get(texto.lower().strip())
    if not alvos:
        return False
    cmds = {"46": [MONITOR_OPUS_PY, MONITOR_OPUS, "--comando"],
            "55": [MONITOR_OPUS_PY, "-X", "utf8", CREDITO_55],
            "argon": [MONITOR_OPUS_PY, "-X", "utf8", MONITOR_ARGON, "--comando"]}
    for a in alvos:
        try:
            subprocess.Popen(cmds[a], creationflags=0x08000000, cwd=r"D:\gemini-argo" if a != "46" else None,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as ex:  # noqa: BLE001
            log(f"comando de crédito {a}: falha ao disparar: {ex}")
    return True


def _responder_plantao(estado):
    """01/11 (dona: "funcionário de plantão: quero poder falar com ele, perguntar, e que ele me mande o que está
    fazendo, como no chat"): mensagem no bot do plantão vai pro agente (vigia_telegram) e a resposta e os passos voltam
    pelo próprio bot do plantão."""
    try:
        b = json.loads((ROOT / "config" / "telegram_bots.json").read_text("utf-8-sig"))["plantao"]
        url = f"https://api.telegram.org/bot{b['bot_token']}/getUpdates"
        corpo = json.dumps({"offset": estado.get("tg_update_id_plantao", 0), "timeout": 0,
                            "allowed_updates": ["message"]}).encode("utf-8")
        with urllib.request.urlopen(urllib.request.Request(url, corpo, {"Content-Type": "application/json"}),
                                    timeout=40) as r:
            res = json.loads(r.read())
    except Exception as ex:  # noqa: BLE001
        log(f"bot do plantão: {type(ex).__name__}: {str(ex)[:120]}")
        return
    for upd in res.get("result") or []:
        estado["tg_update_id_plantao"] = upd["update_id"] + 1
        msg = upd.get("message") or {}
        texto = (msg.get("text") or "").strip()
        if texto and msg.get("chat", {}).get("id") == CFG["chat_id"]:
            orig = msg.get("reply_to_message") or {}
            _encaminhar_vigia(texto, msg.get("message_id"), resposta_a_texto=(orig.get("text") or "")[:500] or None,
                              bot="plantao")


def _responder_opus(estado):
    """27/10: o bot do Opus também aceita os comandos de crédito (ninguém mais lê esse bot: o
    monitor_opus_telegram.py está desativado desde 23/10)."""
    try:
        b = json.loads((ROOT / "config" / "telegram_bots.json").read_text("utf-8"))["opus"]
        url = f"https://api.telegram.org/bot{b['bot_token']}/getUpdates"
        corpo = json.dumps({"offset": estado.get("tg_update_id_opus", 0), "timeout": 0,
                            "allowed_updates": ["message"]}).encode("utf-8")
        with urllib.request.urlopen(urllib.request.Request(url, corpo, {"Content-Type": "application/json"}),
                                    timeout=40) as r:
            res = json.loads(r.read())
    except Exception as ex:  # noqa: BLE001
        log(f"bot do opus: {type(ex).__name__}: {str(ex)[:120]}")
        return
    for upd in res.get("result") or []:
        estado["tg_update_id_opus"] = upd["update_id"] + 1
        msg = upd.get("message") or {}
        texto = (msg.get("text") or "").strip()
        if texto and msg.get("chat", {}).get("id") == CFG["chat_id"]:
            _comando_credito(texto)


def responder(estado):
    _responder_aprendizado(estado)
    _responder_opus(estado)
    # 01/11: o plantão tem tarefa própria (D:\video-fila\plantao.py, PlantaoTelegram, 1 min) — esta rodada travou 40 min
    # no Drive e a mensagem da dona ficou sem resposta; dois lendo o mesmo bot roubariam mensagens um do outro
    _responder_bot(estado, None, "tg_update_id", "")
    if BOT_COMENT:
        _responder_bot(estado, BOT_COMENT, "tg_update_id_comentarios", "com:")


def _responder_bot(estado, token, chave_offset, prefixo):
    """Lê as mensagens da dona num bot (geral ou de comentários): resposta a comentário vai pro YouTube."""
    coment = bool(prefixo)
    r = tg("getUpdates", {"offset": estado.get(chave_offset, 0), "timeout": 0, "allowed_updates": ["message"]}, token)
    if not r or not r.get("ok"):
        return
    mapa = estado.setdefault("mapa_respostas", {})
    for upd in r["result"]:
        estado[chave_offset] = upd["update_id"] + 1
        msg = upd.get("message") or {}
        orig = msg.get("reply_to_message")
        texto = (msg.get("text") or "").strip()
        if msg.get("chat", {}).get("id") != CFG["chat_id"] or not texto:
            continue
        if not orig and _comando_credito(texto):  # opus / 5.5 / argon / creditos
            continue
        if not orig:
            _encaminhar_vigia(texto, msg.get("message_id"))
            continue
        info = mapa.get(prefixo + str(orig["message_id"]))
        if not info and not coment and _aprendizado_responder(orig["message_id"], texto):
            continue  # resposta (SIM/NÃO) a um achado do aprendizado dos parceiros
        if not info:
            _encaminhar_vigia(texto, msg.get("message_id"),
                              resposta_a_texto=(orig.get("text") or "")[:500])
            continue
        try:
            tok = yp.refresh_access_token(CREDS[info["cred_id"]])
            yt(tok, "comments?part=snippet", {"snippet": {"parentId": info["comment_id"], "textOriginal": texto}})
        except urllib.error.HTTPError as ex:
            erro = ex.read()[:300].decode("utf-8", "replace")
            enviar(f"<b>Não consegui responder</b> em {e(info['canal'])}: HTTP {ex.code}\n{e(erro)}",
                   responder_a=orig["message_id"], coment=coment)
            log(f"resposta falhou em {info['canal']}: HTTP {ex.code} {erro[:150]}")
            continue
        except Exception as ex:  # noqa: BLE001
            enviar(f"<b>Não consegui responder</b> em {e(info['canal'])}: {e(ex)}", responder_a=orig["message_id"], coment=coment)
            log(f"resposta falhou em {info['canal']}: {ex}")
            continue
        info["respondido"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
        salvar_estado(estado)
        enviar(f"<b>Respondido no YouTube</b> ({e(info['canal'])}) para {e(info['autor'])}:\n{e(texto)}",
               responder_a=orig["message_id"], coment=coment)
        log(f"respondido em {info['canal']} para {info['autor']}")


# --- Auto-resposta (quando o dono nao responde em X horas) ---

INSTRUCOES_IA = """Voce responde comentarios do YouTube no lugar do dono do canal, como se fosse ele mesmo digitando no celular.
- Responda no MESMO idioma do comentario (portugues = portugues do Brasil bem informal).
- Curto: 1 ou 2 frases (ate ~250 caracteres). Tom de gente: simpatico, leve, natural, nada de cara de atendimento.
- SEMPRE termine pedindo, de um jeito natural, para a pessoa COMPARTILHAR o video (mandar pra um amigo, pro grupo,
  marcar quem precisa ver...). Varie a frase a cada resposta, sem soar robotico, no mesmo idioma do comentario.
- A fonte principal e o video (titulo e descricao). Use isso quando ajudar; nunca invente fatos, nomes, datas ou promessas
  (ex.: nao prometa data do proximo capitulo; pode dizer que vem mais). Se nao souber a resposta, responda de leve sem chutar.
- Nunca diga nem insinue que e IA, assistente, bot ou resposta automatica. Sem hashtags, links ou @mencoes;
  nao peca inscricao toda hora. No maximo 1 emoji, se combinar.
- Siga as regras_do_canal, se houver.
- responder=false para spam, golpe, link suspeito, ofensa pesada, conteudo sexual ou texto sem sentido.
- Se vier "conversa" (a pessoa respondeu a resposta do canal; e_o_canal=true sao as falas do canal): responda a ULTIMA
  fala dela continuando o papo, coerente com o que o canal ja disse, sem repetir a resposta anterior.
  responder=false se ela so encerrou (ex.: "valeu", "kkk", emoji sozinho) e nao precisa de mais nada.
Devolva so JSON: {"responder": true, "resposta": "texto"}"""


def gerar_resposta(tok, info):
    """Devolve (situacao, texto): ok | ja_respondido | proprio | antigo | apagado | ia_nao | ia_falhou."""
    ar = CFG.get("auto_resposta", {})
    th = yt(tok, f"commentThreads?part=snippet,replies&id={info['comment_id']}").get("items", [])
    if not th:
        return "apagado", None
    s = th[0]["snippet"]
    top = s["topLevelComment"]["snippet"]
    conversa = None
    if info.get("reply_id"):
        # 02/11: resposta à NOSSA resposta (seguir_conversas) — responde a última fala dela com a conversa toda
        fio = _respostas_do_fio(tok, info["comment_id"])
        alvo = next((r for r in fio if r["id"] == info["reply_id"]), None)
        if not alvo:
            return "apagado", None
        t_alvo = alvo["snippet"]["publishedAt"]
        if any(_nossa(r["snippet"]) and r["snippet"]["publishedAt"] > t_alvo for r in fio):
            return "ja_respondido", None
        if datetime.now(timezone.utc) - data_utc(t_alvo) > timedelta(hours=ar.get("idade_max_h", 72)):
            return "antigo", None
        conversa = [{"autor": top.get("authorDisplayName"), "texto": top.get("textOriginal"), "e_o_canal": False}]
        conversa += [{"autor": r["snippet"].get("authorDisplayName"), "texto": r["snippet"].get("textOriginal"),
                      "e_o_canal": _nossa(r["snippet"])} for r in fio if r["snippet"]["publishedAt"] <= t_alvo]
        top = alvo["snippet"]
    else:
        if any(r["snippet"].get("authorChannelId", {}).get("value") == s.get("channelId")
               for r in th[0].get("replies", {}).get("comments", [])):
            return "ja_respondido", None
        if proprio(top):
            return "proprio", None
        if datetime.now(timezone.utc) - data_utc(top["publishedAt"]) > timedelta(hours=ar.get("idade_max_h", 72)):
            return "antigo", None
    vids = yt(tok, f"videos?part=snippet&id={info['video_id']}").get("items", [])
    vs = vids[0]["snippet"] if vids else {}
    canal = next((c for c in CANAIS if c["nome"] == info["canal"]), {})
    payload = json.dumps({"canal": info["canal"], "nicho": canal.get("nicho"), "jeito_de_falar": canal.get("persona"),
                          "regras_do_canal": canal.get("regras"),
                          "video": {"titulo": vs.get("title"), "descricao": (vs.get("description") or "")[:1500]},
                          "comentario": {"autor": top.get("authorDisplayName"), "texto": top.get("textOriginal")},
                          **({"conversa": conversa[-12:]} if conversa else {})},
                         ensure_ascii=False)
    sys.path.insert(0, r"D:\manhwa-react")
    from mr import llm
    mr_cfg = json.loads(Path(r"D:\manhwa-react\config.json").read_text("utf-8"))
    cfg = {"paths": mr_cfg["paths"], "editorial": {**mr_cfg["editorial"], "providers": ["proxy:sonnet", "proxy:haiku"]}}
    d = llm.ask_json(cfg, INSTRUCOES_IA, payload, timeout=90)
    if d is None:
        return "ia_falhou", None
    texto = (d.get("resposta") or "").strip()
    return ("ok", texto) if d.get("responder") and texto else ("ia_nao", None)


def auto_responder(estado):
    ar = CFG.get("auto_resposta", {})
    if not ar.get("ativo"):
        return
    agora = datetime.now(timezone.utc)
    hoje = datetime.now().date().isoformat()
    cont = estado.setdefault("auto_dia", {})
    if cont.get("dia") != hoje:
        cont.update({"dia": hoje, "n": 0})
    # 03/11 dona: "2 minutos em vez de 2 h" — 'minutos' (se existir) vale no lugar de 'horas'
    espera = timedelta(minutes=ar["minutos"]) if "minutos" in ar else timedelta(hours=ar.get("horas", 2))
    pendentes = sorted(((k, m) for k, m in estado.get("mapa_respostas", {}).items()
                        if not m.get("respondido") and not m.get("auto_fim") and m.get("tentativas", 0) < 3
                        and agora - data_utc(m["ts"]) >= espera), key=lambda kv: kv[1]["ts"], reverse=True)
    for k, m in pendentes[:5]:
        if cont["n"] >= ar.get("max_dia", 30):
            break
        try:
            tok = yp.refresh_access_token(CREDS[m["cred_id"]])
            situacao, texto = gerar_resposta(tok, m)
            if situacao == "ok":
                yt(tok, "comments?part=snippet", {"snippet": {"parentId": m["comment_id"], "textOriginal": texto}})
        except Exception as ex:  # noqa: BLE001
            situacao, texto = "erro", None
            log(f"auto-resposta {m['canal']}: {ex}")
        if situacao in ("ia_falhou", "erro"):
            m["tentativas"] = m.get("tentativas", 0) + 1
            continue
        m["auto_fim"] = situacao
        if situacao == "ok":
            m["respondido"] = agora.isoformat(timespec="minutes")
            cont["n"] += 1
            prazo = f"{ar['minutos']} min" if "minutos" in ar else f"{ar.get('horas', 2)} h"
            enviar(f"<b>Auto-resposta</b> ({e(m['canal'])}) - você não respondeu em {prazo}:\n{e(texto)}",
                   responder_a=int(k.removeprefix("com:")), coment=k.startswith("com:"))
        log(f"auto-resposta {m['canal']} ({m['autor']}): {situacao}")
        salvar_estado(estado)


# --- Postagens de todos os projetos, filas e contas deslogadas ---

LOGS = ROOT / "logs"
MS_LOG = Path(r"D:\ms-energy\videos\postagem_log.json")
MS_DIRS = [Path(r"D:\ms-energy\videos\shorts_veo"), Path(r"D:\ms-energy\videos\_postados")]
REDE_SEM = ROOT / "_analise" / "rede_sem_video.json"
# 22/10: cada log aceita VÁRIOS padrões [(regex, msg), ...] — antes era 1 por arquivo (dict não repete chave)
ALERTAS_LOG = {LOGS / "tiktok_auto.log": [(r"DESLOGADO: (\S+)", "TikTok @{} deslogado: logar a conta no Chrome do TikTok")],
               LOGS / "instagram_auto.log": [(r"(\S+): login do Instagram vencido", "Instagram @{}: login/token vencido")],
               # BX-07 (16/10) + VEO-04 (22/10): sonda diaria das contas Google do Veo (deslogada E sem credito)
               Path(r"D:\veo\beta\logs\sonda_contas_veo.log"): [
                   (r"DESLOGADA: (\S+)", "Conta Google do Veo {0} deslogada: python D:\\logins-google\\cofre.py logar {0}"),
                   (r"SEM CREDITO: (\S+(?: \(renova [^)]*\))?)",
                    "Veo/Flow sem credito: {0} — o MS Energy gasta as mesmas contas de madrugada")],
               # P02 (22/10): canal preso no "limite diario de envios" do YouTube ficava MUDO — o ForjaReact passou
               # 4 dias sem upload (199 tentativas) e ninguem soube. O nome do canal pode ter espaco.
               Path(r"D:\recapd-ambientes\producao\logs\parceiro_postar.log"): [(
                   r"\] ([^:\r\n]+): esperando passar o limite de uploads",
                   "YouTube {}: preso no LIMITE DIARIO de envios — abrir o Studio do canal e fazer a verificacao unica (ou esperar 24 h)")],
               Path(r"D:\recapd-ambientes\producao\logs\parceiro_postar_auto.log"): [(
                   r"\] ([^:\r\n]+): esperando passar o limite de uploads",
                   "YouTube {}: preso no LIMITE DIARIO de envios — abrir o Studio do canal e fazer a verificacao unica (ou esperar 24 h)")]}


def _ler_json(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except (OSError, ValueError):
        return padrao


def _quando(ts):
    d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return d if d.tzinfo else d.astimezone()


def _email(canal_ou_cred):
    """E-mail da conta Google do canal (dono 22/10: métricas com canal e e-mail)."""
    if isinstance(canal_ou_cred, dict) and canal_ou_cred.get("email"):
        return canal_ou_cred["email"]
    nome = str(canal_ou_cred or "").strip().lower()
    return next((c.get("email") for c in CREDS.values() if str(c.get("nome", "")).strip().lower() == nome), None)


def _video(caminho):
    """Título, narrador e original pelo postar.json da pasta do vídeo (dono 22/10)."""
    try:
        d = json.loads((Path(caminho).parent / "postar.json").read_text("utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    narrador = d.get("narrador") or (" + ".join(d["elenco"]) if d.get("elenco") else None) or d.get("parceiro")
    if narrador and d.get("voz_base"):
        narrador += f" (voz {d['voz_base']})"
    if d.get("teste_voz") and d["teste_voz"] != "solo":  # 23/10: Short do teste gradual (anime_testes)
        narrador = f"{narrador} — TESTE {d['teste_voz']}"
    return {"titulo": d.get("titulo"), "narrador": narrador, "original": d.get("fonte")}


def _linhas_video(info, link=None):
    out = []
    if info.get("narrador"):
        out.append(f"🎙 Narrador: {e(info['narrador'])}")
    if link:
        out.append(f"🔗 Link: {link}")
    if info.get("original"):
        out.append(f"🎞 Original: {e(info['original'])}")
    return out


def _caminho_por_id():
    out = {}
    ledger = LOGS / "uploads_ledger.jsonl"
    for ln in (ledger.read_text("utf-8", errors="replace").splitlines() if ledger.exists() else []):
        try:
            r = json.loads(ln)
            out[r["video_id"]] = r["caminho"]
        except (ValueError, KeyError, TypeError):
            continue
    return out


def postagens_novas(desde):
    """(quando, rede, conta, título, link) de cada vídeo postado depois de `desde`."""
    itens = []
    ledger = LOGS / "uploads_ledger.jsonl"
    linhas = ledger.read_text("utf-8").splitlines()[-500:] if ledger.exists() else []
    for ln in linhas:
        try:
            r = json.loads(ln)
            q = _quando(r["ts"])
        except (ValueError, KeyError):
            continue
        if q > desde:
            titulo = (_video(r.get("caminho")).get("titulo") or r.get("titulo") or TITULOS.get(r.get("video_id"))
                      or r.get("arquivo") or "?")
            abre = f" (abre {hora_local(r['publish_at'])})" if r.get("publish_at") else ""
            itens.append((q, "YouTube", r.get("canal") or "?", titulo[:70] + abre, f"https://youtu.be/{r.get('video_id')}",
                          r.get("tipo") in LONGOS, FORMATOS.get((r.get("tipo"), r.get("projeto")))
                          or FORMATOS.get((r.get("tipo"), None)) or r.get("tipo") or "?"))
    for p, plat in ((LOGS / "tiktok_auto_posted.json", "TikTok"), (LOGS / "instagram_auto_posted.json", "Instagram")):
        for r in _ler_json(p, [])[-300:]:
            try:
                q = _quando(r["timestamp"])
            except (ValueError, KeyError):
                continue
            if q > desde:
                itens.append((q, plat, f"@{r.get('account')}", _video(r.get("path")).get("titulo") or r.get("file"), None,
                              False, "vídeo curto"))
    for nome, r in _ler_json(MS_LOG, {}).items():
        for campo, rot in (("insta", "feed"), ("stories", "stories"), ("fb", "Facebook")):
            try:
                q = _quando(r[campo])
            except (ValueError, KeyError, TypeError):
                continue
            if q > desde:
                itens.append((q, "MS Energy", f"@msenergycap {rot}", nome, None, False, rot))
    return sorted(itens, key=lambda x: x[0])


FORMATOS = {("short", "parceiro"): "Short parceiro", ("short", "hipercool"): "Short manhwa",
            ("short", "manhwa-react"): "Short react", ("veo", None): "Veo", ("completo", None): "longo",
            ("longo", None): "longo", ("compilado", None): "longo"}


def _formatos(vids):
    """'3 Short parceiro + 1 Veo' a partir do formato de cada vídeo (último campo da tupla)."""
    from collections import Counter
    c = Counter(v[-1] for v in vids)
    return " + ".join(f"{n} {f}" for f, n in c.most_common())


def avisar_postagens(estado):
    """Uma lista por resumo (9h/14h/21h), montada logo antes dele. 23/10 (dono): a lista de 28 em 28 min enchia o
    resumo e só as 8 últimas cabiam ("... e mais N"). YouTube: título + link de cada vídeo (narrador e original vêm
    no aviso "No ar agora"); TikTok, Instagram e MS Energy: quantos por conta."""
    agora = datetime.now(timezone.utc)
    desde = _quando(estado.get("postagens_desde") or agora.isoformat())
    TITULOS.update(estado.get("titulos") or {})
    itens = postagens_novas(desde)
    estado["postagens_desde"] = agora.isoformat(timespec="seconds")
    if not itens:
        return
    por_rede, longos = {}, []
    for _q, rede, conta, titulo, link, longo, formato in itens:
        if longo:
            longos.append((_q, conta, titulo, link))
            continue
        por_rede.setdefault(rede, {}).setdefault(conta, []).append((_q, titulo, link, formato))
    partes = [f"<b>Postagens</b> desde {desde.astimezone():%d/%m %H:%M} ({len(itens)} no total)"]
    # 01/11 tarde (dona: "relatório com quantos vídeos cada canal postou e de qual forma; longo ainda não apareceu,
    # se teve me aparece"): longos SEMPRE aparecem (mesmo zero) e cada canal diz os formatos
    if not longos:
        partes.append("\n🎥 Vídeos longos: nenhum neste período")
    # 01/11 (dona): longos com mensagem única e marca
    if longos:
        partes.append(f"\n🎥🎥 <b>VÍDEOS LONGOS ({len(longos)})</b> 🎥🎥")
        for q, conta, titulo, link in longos:
            partes.append(f"⭐ {q.astimezone():%H:%M} <b>{e(conta)}</b>: <a href='{link}'>{e(titulo)}</a>")
    # 01/11 (dona): Shorts agrupados por canal com hora
    yt = por_rede.pop("YouTube", {})
    if yt:
        n_yt = sum(len(v) for v in yt.values())
        partes.append(f"\n📱 <b>YouTube Shorts ({n_yt})</b>")
        for conta, vids in sorted(yt.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            partes.append(f"<b>{e(conta)}</b>: {len(vids)} — {e(_formatos(vids))} — "
                          + ", ".join(f"{q.astimezone():%H:%M}" for q, *_r in vids))
    # 01/11 (dona): TikTok e Instagram com marca e hora+canal agrupados
    for rede, emoji, marca in [("TikTok", "🎵", "TikTok"), ("Instagram", "📸", "Instagram"),
                                ("MS Energy", "☀️", "MS Energy")]:
        contas = por_rede.pop(rede, {})
        if not contas:
            continue
        n = sum(len(v) for v in contas.values())
        partes.append(f"\n{emoji} <b>{marca} ({n})</b>")
        for conta, vids in sorted(contas.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            horas = ", ".join(f"{q.astimezone():%H:%M}" for q, *_r in vids)
            partes.append(f"- {e(conta)}: {len(vids)} — {horas}")
    # redes desconhecidas (futuras)
    for rede, contas in por_rede.items():
        n = sum(len(v) for v in contas.values())
        partes.append(f"\n<b>{rede} ({n})</b>")
        for conta, vids in sorted(contas.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            partes.append(f"- {e(conta)}: {len(vids)}")
    avisar("\n".join(partes), "postagens")
    log(f"postagens: {len(itens)} avisada(s)")


def filas_atuais():
    """nome -> (quantos ainda pra postar, limite de 'baixa', onde produzir mais)."""
    out = {}
    ms = _ler_json(MS_LOG, {})
    vids = {p.stem for d in MS_DIRS if d.exists() for p in d.glob("*.mp4")}
    falta = sum(1 for v in vids if not (ms.get(v) or {}).get("insta") or not (ms.get(v) or {}).get("stories"))
    out["MS Energy - Instagram @msenergycap"] = (falta, 5, "gerar mais shorts em D:\\ms-energy (bin\\gerar_short_veo.py)")
    import catalogo
    from collections import Counter
    reuso = catalogo._ler(catalogo.REUSO, {})
    for plat in ("tiktok", "instagram"):
        cfg = reuso.get(plat) or {}
        cont = Counter(v["conta_reuso"] for v in catalogo.disponiveis(plat))
        limite = 3 * cfg.get("max_por_conta_dia", 2)
        for conta in cfg.get("contas", {}):
            out[f"{plat.capitalize()} @{conta}"] = (cont.get(conta, 0), limite,
                                                    "reuso do catálogo: falta vídeo já postado no YouTube no tema dessa conta")
    sem = _ler_json(REDE_SEM, {})
    if sem.get("em") and datetime.now(timezone.utc) - _quando(sem["em"]) < timedelta(hours=26):
        for c in CANAIS:
            if c.get("status") == "ativo":
                vazio = c["slug"] in (sem.get("canais") or {})
                out[f"YouTube rede {c['nome']}"] = (0 if vazio else 1, 0, f"gravar/produzir: {(c.get('nicho') or '')[:90]}")
    return out


def checar_filas(estado):
    antes = estado.setdefault("filas", {})
    avisos, rede = [], []
    for nome, (n, limite, dica) in filas_atuais().items():
        nivel = "vazia" if n == 0 else "baixa" if n <= limite else "ok"
        if nivel != "ok" and nivel != (antes.get(nome) or {}).get("nivel"):
            if nome.startswith("YouTube rede "):
                rede.append(nome[len("YouTube rede "):])
            else:
                avisos.append(f"- <b>{'ACABOU' if nivel == 'vazia' else 'acabando'}</b> {e(nome)}: {n} vídeo(s). {e(dica)}")
        antes[nome] = {"nivel": nivel, "n": n}
    if rede:
        avisos.append(f"- <b>Rede de react sem vídeo</b> (gravar mais react no nicho de cada um): {e(', '.join(rede))}")
    if avisos:
        avisar("<b>Filas de postagem</b>\n" + "\n".join(avisos), "filas de postagem")
        log(f"filas: {len(avisos)} aviso(s)")


def checar_logs(estado):
    import re
    pos = estado.setdefault("log_pos", {})
    vistos = estado.setdefault("alertas_conta", {})
    abertas = estado.setdefault("contas_abertas", {})  # 23/10 (dono: saber quando consertou)
    hoje = datetime.now().date()
    avisos = []
    for p, padroes in ALERTAS_LOG.items():
        if not p.exists():
            continue
        tam = p.stat().st_size
        ini = pos.get(str(p), max(0, tam - 20000))
        if ini > tam:
            ini = 0
        with open(p, "rb") as f:
            f.seek(ini)
            novo = f.read().decode("utf-8", "replace")
        pos[str(p)] = tam
        for padrao, msg in padroes:
            for conta in set(re.findall(padrao, novo)):
                chave = f"{p.stem}:{conta}"
                ult = vistos.get(chave)
                if not ult or (hoje - datetime.fromisoformat(ult).date()).days >= 7:
                    avisos.append("- " + e(msg.format(conta)))
                    vistos[chave] = hoje.isoformat()
                    abertas[chave] = {"conta": conta, "log": p.stem,
                                      "desde": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    avisos = list(dict.fromkeys(avisos))  # 01/11: parceiro_postar.log e _auto.log davam a mesma linha 2x
    if avisos:
        avisar("<b>Contas com problema</b>\n" + "\n".join(avisos), "contas com problema", importante=True)
    voltaram = []
    for chave, a in list(abertas.items()):
        r = _conta_voltou(a)
        if r is None:
            continue
        del abertas[chave]
        vistos.pop(chave, None)  # se cair de novo, avisa na hora
        if r:
            voltaram.append(f"- {e(a['conta'])}")
    voltaram = list(dict.fromkeys(voltaram))
    if voltaram:  # 01/11 (dona: "se voltarem não precisa notificar"): só no resumo
        avisar("✅ <b>Contas que voltaram a postar</b>\n" + "\n".join(voltaram), "contas com problema", importante=False)


def _conta_voltou(a):
    """True = a conta postou depois do aviso; False = desisto de esperar (7 dias); None = ainda não."""
    desde = _quando(a["desde"])
    if a["log"].startswith("tiktok_auto") or a["log"].startswith("instagram_auto"):
        arq = LOGS / ("tiktok_auto_posted.json" if a["log"].startswith("tiktok") else "instagram_auto_posted.json")
        for r in _ler_json(arq, [])[-500:]:
            try:
                if r.get("account") == a["conta"] and _quando(r["timestamp"]) > desde:
                    return True
            except (ValueError, KeyError):
                continue
    elif a["log"].startswith("parceiro_postar"):
        ledger = LOGS / "uploads_ledger.jsonl"
        for ln in (ledger.read_text("utf-8", errors="replace").splitlines()[-500:] if ledger.exists() else []):
            try:
                r = json.loads(ln)
                if (r.get("canal") or "").strip() == a["conta"].strip() and _quando(r["ts"]) > desde:
                    return True
            except (ValueError, KeyError):
                continue
    return False if datetime.now(timezone.utc) - desde > timedelta(days=7) else None


# Ritmo de upload (item AB-10 de D:\veo\docs\PLANO_MELHORIAS_VEO.md, 16/10): em 16/10 o Veo subiu 8 por canal no
# InventoReact e no ManhwaReact (10 em 16 min), o YouTube cortou (uploadLimitExceeded) e o react do dono nao subiu -
# ninguem foi avisado. Avisa 1 vez por ocorrencia; NAO cria PARADO.json sozinho (parar tudo e decisao do dono).
RITMO_MAX_DIA = 5        # normal hoje: 3 do Veo (veo_rampa) + 1 react nos canais do Veo; 6-8 foi onde o YouTube cortou
RITMO_RAJADA = 3         # uploads do mesmo canal dentro de 1 h
PISO_POLITICA = {"max_uploads_por_canal_dia": 4, "max_uploads_total_dia": 20, "intervalo_min_horas_mesmo_canal": 1}
LOG_REDE = Path(r"D:\manhwa-react\logs")


def checar_ritmo(estado):
    import re
    import politica
    hoje = datetime.now().date()
    r = estado.setdefault("ritmo", {})
    if r.get("dia") != hoje.isoformat():
        r.clear()
        r["dia"] = hoje.isoformat()
    vistos = set(r.setdefault("avisados", []))
    avisos = []

    def avisa(chave, txt):
        if chave not in vistos:
            vistos.add(chave)
            avisos.append("- " + txt)

    # retirado do ar depois de agendado (rede: "tirar e repor") libera o horario; o upload continua contando na cota
    retirados = _ler_json(Path(r"D:\manhwa-react\work\rede_retirados.json"), {})
    por_canal = {}
    for reg in politica._ler_ledger():
        ts = politica._dt(reg.get("ts"))
        if ts and ts.astimezone().date() == hoje:
            pub = None if reg.get("video_id") in retirados else politica._dt(reg.get("publish_at"))
            por_canal.setdefault(reg.get("canal") or "?", []).append((ts, pub))
    for canal, ups in por_canal.items():
        ups.sort(key=lambda x: x[0])
        if len(ups) > RITMO_MAX_DIA:
            avisa(f"dia:{canal}:{len(ups) // 3}", f"<b>{e(canal)}</b>: {len(ups)} uploads hoje (normal: até {RITMO_MAX_DIA})")
        for i in range(len(ups) - RITMO_RAJADA + 1):
            if ups[i + RITMO_RAJADA - 1][0] - ups[i][0] < timedelta(hours=1):
                avisa(f"rajada:{canal}", f"<b>{e(canal)}</b>: rajada de {RITMO_RAJADA}+ uploads em menos de 1 h "
                                         f"(desde {ups[i][0].astimezone():%H:%M})")
                break
        pubs = sorted(p for _, p in ups if p)
        for a, b in zip(pubs, pubs[1:]):
            if b - a < timedelta(hours=1):
                avisa(f"perto:{canal}:{a.isoformat()}", f"<b>{e(canal)}</b>: 2 vídeos publicam com menos de 1 h de "
                                                         f"diferença ({a.astimezone():%d/%m %H:%M} e {b.astimezone():%H:%M})")
    log_rede = LOG_REDE / f"rede_{hoje:%Y%m%d}.log"
    if log_rede.exists():
        erros = {}
        for canal, status in re.findall(r"rede: ([^:\n]+?): \S+ nao subiu \((limite|cota|morto|suspenso|parado)",
                                        log_rede.read_text(encoding="utf-8", errors="replace")):
            erros.setdefault(status, set()).add(canal.strip())
        for status, canais in erros.items():
            avisa(f"erro:{status}:{','.join(sorted(canais))}",
                  f"YouTube recusou upload (<b>{status}</b>) em: {e(', '.join(sorted(canais)))}"
                  + (" — <b>2+ canais no mesmo dia</b>: avaliar parar tudo (PARADO.json)" if len(canais) >= 2 else ""))
    # 16/10 (noite, dono): postar por API e proibido (tudo pelo navegador). Upload de hoje com script youtube_poster.py
    # no ledger = erro: avisa por canal.
    if politica.politica().get("proibido_postar_por_api"):
        for reg in politica._ler_ledger():
            ts = politica._dt(reg.get("ts"))
            if ts and ts.astimezone().date() == hoje and str(reg.get("script") or "").startswith("youtube_poster"):
                avisa(f"api:{reg.get('canal')}", f"<b>{e(reg.get('canal') or '?')}</b>: upload pela API (proibido) — pôr o "
                                                 "canal no navegador (config/youtube_navegador.json)")
    pol = politica.politica()
    # o piso vem do proprio politica.PISO (None = sem piso, ex.: o total coletivo saiu em 16/10 por ordem do dono)
    piso = {k: v for k, v in getattr(politica, "PISO", PISO_POLITICA).items() if v is not None}
    fora = [f"{k}={pol.get(k)} (piso {v})" for k, v in piso.items()
            if pol.get(k) is not None and ((k.startswith("max") and (not pol[k] or pol[k] > v))
                                           or (k.startswith("intervalo") and pol[k] < v))]
    if fora:
        avisa("politica:" + ";".join(fora), "Política de postagem acima do piso de segurança: " + e(", ".join(fora)))
    r["avisados"] = sorted(vistos)
    if avisos:
        avisar("<b>Ritmo de postagem</b>\n" + "\n".join(avisos), "ritmo de postagem", importante=True)
        log(f"ritmo: {len(avisos)} aviso(s)")


def avisos_projetos(estado):
    for f in (checar_filas, checar_logs, checar_ritmo):
        try:
            f(estado)
        except Exception as ex:  # noqa: BLE001
            log(f"{f.__name__}: {ex}")


# --- Aprendizado ENTRE projetos (15/10): views em 48 h de todos os canais -> _analise/aprendizado_global.json ---
# Lido pelo agente de cada canal da rede (D:\manhwa-react\mr\rede.py: memoria_rede) e disponivel para os outros projetos.

APREND_GLOBAL = ROOT / "_analise" / "aprendizado_global.json"
PUBLICADOS_REDE = Path(r"D:\hipercool-materiais\_postados\react\publicados.json")
METRICAS_STUDIO = ROOT / "_analise" / "metricas_studio.json"  # metricas_rede.py: inclui os canais sem token (Noturnos)
ORIGEM_PROJETO = {"hipercool": "recap hipercool", "parceiro": "parceiro"}
PRIMEIRA_MAX_H = 96


def _origens():
    """video_id -> origem (react / recap hipercool / historias / veo limpo / script) pelo registro da rede e pelo ledger."""
    import re
    nomes = {"react": "react", "historias": "historias", "veo": "veo limpo", "completo": "react completo"}
    out = {v["video_id"]: nomes.get(v.get("fonte") or "react", v.get("fonte"))
           for v in _ler_json(PUBLICADOS_REDE, {}).values() if isinstance(v, dict) and v.get("video_id")}
    ledger = LOGS / "uploads_ledger.jsonl"
    for ln in ledger.read_text("utf-8").splitlines() if ledger.exists() else []:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        vid, arq = r.get("video_id"), str(r.get("arquivo") or "")
        if not vid:
            continue
        if r.get("projeto") and vid not in out:  # ledger com projeto/tipo (desde 18/10): origem certa
            p, t = r["projeto"], r.get("tipo")
            out[vid] = ORIGEM_PROJETO.get(p) or nomes.get(t or "react", t or p)
            continue
        if arq.startswith("hipercool_") or re.search(r"_cap\d+_parte\d+|_caps\d+-\d+", arq):
            out[vid] = "recap hipercool"
        else:
            out.setdefault(vid, r.get("script") or "outro")
    return out


def _placar_dimensoes(xs):
    """({"projeto/tipo": [views]}, {"idioma": [views]}) das medidas: projeto/tipo vêm do ledger (desde 18/10), idioma
    do cadastro único (canal -> idioma)."""
    try:
        cad = json.loads((ROOT / "config" / "canais.json").read_text("utf-8")).get("canais", {})
    except (OSError, ValueError):
        cad = {}
    idioma_do = {k: x.get("idioma") for k, x in cad.items()}
    idioma_do.update({x.get("slug"): x.get("idioma") for x in cad.values() if x.get("slug")})
    pt = {}
    ledger = LOGS / "uploads_ledger.jsonl"
    for ln in ledger.read_text("utf-8").splitlines() if ledger.exists() else []:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("video_id") and r.get("projeto"):
            pt[r["video_id"]] = f"{r['projeto']}/{r.get('tipo') or '?'}"
    por_pt, por_id = {}, {}
    for vid, m in xs:
        por_pt.setdefault(pt.get(vid, "sem registro"), []).append(m["views"])
        if idioma_do.get(m["canal"]):
            por_id.setdefault(idioma_do[m["canal"]], []).append(m["views"])
    return por_pt, por_id


_PALAVRAS_FORA = {"shorts", "manhwa", "anime", "para", "mais", "como", "depois", "quando", "todos", "todas",
                  "este", "esta", "esse", "essa", "pelo", "pela", "entre", "sobre", "ainda", "mesmo", "parte",
                  "with", "that", "this", "from", "dele", "dela", "deles", "minha", "meu", "voce", "você"}


def _palavras_titulo(t):
    """Palavras 'de conteúdo' do título (≥4 letras, sem stopword/hashtag), até 12 — pro placar de palavras."""
    t = re.sub(r"#\S+", " ", str(t or "").casefold())
    vistas, out = set(), []
    for p in re.findall(r"[a-záéíóúâêôãõç]{4,}", t):
        if p not in _PALAVRAS_FORA and p not in vistas:
            vistas.add(p)
            out.append(p)
    return out[:12]


def _vitoria(views, mediana):
    """23/10 (dona): empate com a mediana vale meia vitória — 1.0 acima, 0.5 igual, 0.0 abaixo (YouTube e TikTok)."""
    return 1.0 if views > mediana else (0.5 if views == mediana else 0.0)


def _placar_titulos(med, corte):
    """Estilo de título de todo projeto (20/10): vídeo medido em 48 h cuja ficha postar.json (ao lado do arquivo do
    ledger) tem estilo_titulo -> vitória se as views passam da mediana do mesmo canal (mín. 4 medidas no canal).
    Cada vídeo conta 1 vez (placar_titulos.registrar). Hipercool registra o dele por CTR (metricas.py)."""
    import placar_titulos
    ledger = LOGS / "uploads_ledger.jsonl"
    led = {}
    for ln in ledger.read_text("utf-8").splitlines() if ledger.exists() else []:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("video_id") and r.get("caminho"):
            led[r["video_id"]] = r
    try:
        cad = json.loads((ROOT / "config" / "canais.json").read_text("utf-8")).get("canais", {})
    except (OSError, ValueError):
        cad = {}
    idioma_do = {x.get("slug"): x.get("idioma") for x in cad.values() if x.get("slug")}
    por_canal = {}
    for m in med.values():
        if data_utc(m["pub"]) >= corte:
            por_canal.setdefault(m["canal"], []).append(m["views"])
    for vid, m in med.items():
        if (m.get("titulo_reg") and m.get("placar2")) or vid not in led:
            continue
        vs = sorted(por_canal.get(m["canal"], []))
        if len(vs) < 4:
            continue  # pouca amostra no canal: tenta de novo nas próximas rodadas
        venceu = _vitoria(m["views"], vs[len(vs) // 2])
        projeto = led[vid].get("projeto", "")
        pasta = Path(led[vid]["caminho"]).parent
        try:
            ficha = json.loads((pasta / "postar.json").read_text("utf-8"))
        except (OSError, ValueError):
            ficha = {}
        estilo = ficha.get("estilo_titulo")
        if estilo and not m.get("titulo_reg"):
            placar_titulos.registrar(estilo, venceu, projeto=projeto, idioma=idioma_do.get(m["canal"]) or "",
                                     video_id=vid)
        m["titulo_reg"] = estilo or "sem estilo"
        # 21/10: a mesma vitória vale pra FONTE do parceiro (parceiro_diario escolhe a fonte) e pra pose da capa IA
        if projeto == "parceiro" and ficha.get("parceiro"):
            placar_titulos.registrar_item("fontes", "parceiro", ficha["parceiro"], venceu, vid)
        # 22/10 (dono: "o nicho de cada canal é o funil que decide"): vitória do NICHO (tipo do conteúdo) NESTE canal —
        # o parceiro_diario._nicho_do_canal escolhe por isso (vídeo de mangá pode render mais num canal de dorama)
        if projeto == "parceiro" and ficha.get("midia") and led[vid].get("canal_id"):
            placar_titulos.registrar_item("nicho_canal", led[vid]["canal_id"], ficha["midia"], venceu, vid)
        # 31/10: as views de 48 h são da capa A (a que subiu como miniatura); as capas B/C do teste A/B só aprendem
        # pelo vencedor do Studio (capa_ia_anime.registrar_vencedora_ab, placar "capas_ab"). Antes B e C ganhavam a
        # vitória da A sem ninguém ter visto.
        cj = pasta / "capa.capa.json"
        try:
            pose = json.loads(cj.read_text("utf-8")).get("pose")
        except (OSError, ValueError):
            pose = None
        if pose:
            placar_titulos.registrar_item("capas", projeto or "?", pose, venceu, vid)
        # 22/10 (funil, dono: "pegar as tags e títulos que funcionaram e usar mais"): a mesma vitória alimenta
        # a VARIANTE da capa (A/B/C), o NARRADOR do clone e as PALAVRAS/TAGS do título — o seo_generator lê
        # esses placares e prefere o que rendeu. Multi-itens vão sem video_id (o placar2 já garante 1 passada).
        if ficha.get("capa_variante"):
            placar_titulos.registrar_item("capas_variante", projeto or "?",
                                          str(ficha["capa_variante"]).split(":")[0], venceu, vid)
        if ficha.get("narrador"):
            placar_titulos.registrar_item("narradores", ficha.get("midia") or projeto or "?",
                                          ficha["narrador"], venceu, vid)
        if ficha.get("voz_base"):  # base do clone (francisca/kokoro/trecho) também entra no funil
            placar_titulos.registrar_item("voz_base", projeto or "?", str(ficha["voz_base"]), venceu, vid)
        # 23/10 teste gradual (dona: "quem se sair bem aparece mais"): "solo" = controle; "formato:x"/"voz:y" = em teste.
        # O recapd bin/anime_testes.sortear lê este placar (Thompson + promovido/pausado contra o solo)
        if ficha.get("teste_voz"):
            placar_titulos.registrar_item("testes_voz", "parceiro", str(ficha["teste_voz"]), venceu, vid)
        # 28/10: testes A/B dos Cortes (linhas\CORTES\TESTES.md T2-T7) — o postar.json gravava a versão e ninguém
        # cruzava com as views. Só quem tem a chave (vídeo feito depois do teste existir); vazio = versão A.
        for _k in ("cobertura", "legenda_estilo", "gancho_meio", "gancho_remotion", "fx_choque", "mascote",
                   "texto_modelo", "curto", "fala_rapida"):  # curto = T8, fala_rapida = T9 (29/10, Fable)
            if _k in ficha:
                placar_titulos.registrar_item("cortes_testes", _k, str(ficha[_k] or "A"), venceu)
        for p in _palavras_titulo(ficha.get("titulo") or m.get("titulo")):
            placar_titulos.registrar_item("palavras", projeto or "?", p, venceu)
        for tg in (ficha.get("tags") or [])[:12]:
            tg = str(tg).casefold().strip()
            if 3 <= len(tg) <= 60:
                placar_titulos.registrar_item("tags", projeto or "?", tg, venceu)
        try:  # 22/10 (funil, dono: "horários que é comum dar mais visualizações"): faixa de 3 h da publicação
            h = _quando(m["pub"]).astimezone().hour
            placar_titulos.registrar_item("horarios", projeto or "?", f"{h - h % 3:02d}h", venceu)
        except Exception:  # noqa: BLE001
            pass
        m["placar2"] = 1


VEO_FOTO_POR_CLIPE = Path(r"D:\veo\beta\logs\veo_foto_por_clipe.json")


def _placar_veo(med, corte):
    """24/10 (dono: "o Veo tem que passar pelo sistema de rampa de melhorias do YouTube dando preferência ao mais
    viral"): o Veo sobe tudo numa pasta só (rede_marca), então a ficha postar.json não serve; o TEMA vem do nome do
    arquivo (veo_<tema15>_<AAAAMMDD_HHMMSS>__<canal>.mp4). Vitória = views em 48 h > mediana do canal (mín. 4), igual
    ao _placar_titulos. Placares: veo_temas (o cron do Veo sorteia o tema por Thompson; a rede prefere o clipe do tema
    vencedor) e veo_foto ("na_hora" x "antiga": mede se a foto no cenário rende mais). Marca próprio (veo_reg), então
    os Veo já medidos antes desta função também entram."""
    import placar_titulos
    led = {}
    ledger = LOGS / "uploads_ledger.jsonl"
    for ln in ledger.read_text("utf-8").splitlines() if ledger.exists() else []:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("video_id") and str(r.get("arquivo") or "").startswith("veo_"):
            led[r["video_id"]] = r
    fotos = _ler_json(VEO_FOTO_POR_CLIPE, {})
    por_canal = {}
    for m in med.values():
        if data_utc(m["pub"]) >= corte:
            por_canal.setdefault(m["canal"], []).append(m["views"])
    for vid, m in med.items():
        if m.get("veo_reg") or vid not in led:
            continue
        vs = sorted(por_canal.get(m["canal"], []))
        if len(vs) < 4:
            continue
        venceu = _vitoria(m["views"], vs[len(vs) // 2])
        achado = re.match(r"veo_(.+?)_(\d{8}_\d{6})", led[vid]["arquivo"])
        if achado:
            tema, clipe = achado.group(1), f"{achado.group(1)}_{achado.group(2)}"
            placar_titulos.registrar_item("veo_temas", "veo", tema, venceu, vid)
            ficha = fotos.get(clipe, "antiga")
            ficha = ficha if isinstance(ficha, dict) else {"foto": ficha}  # 24/10: era só a foto (str)
            placar_titulos.registrar_item("veo_foto", "veo", ficha.get("foto", "antiga"), venceu, vid)
            if ficha.get("fonte"):  # prompt novo do agente x réplica de fórmula x cache: qual viraliza mais
                placar_titulos.registrar_item("veo_fonte", "veo", ficha["fonte"], venceu, vid)
            if ficha.get("nota"):  # a nota do crítico prevê views? (calibra o crítico)
                placar_titulos.registrar_item("veo_nota_critico", "veo", ficha["nota"], venceu, vid)
        # palavras do título do Veo num grupo SÓ dele (no _placar_titulos elas se misturam com o react do manhwa-react);
        # a rede (mr/rede.py _palavras_buscadas_veo) põe as vencedoras na frente do autocompletar
        for p in _palavras_titulo(m.get("titulo")):
            placar_titulos.registrar_item("palavras", "veo", p, venceu)
            if achado:  # por tema também: palavra que vende em "vendas" não serve pra "cassetadas"
                placar_titulos.registrar_item("palavras", f"veo:{achado.group(1)}", p, venceu)
        m["veo_reg"] = 1


TIKTOK_VIEWS = LOGS / "tiktok_views"
TIKTOK_POSTADOS = LOGS / "tiktok_auto_posted.json"


def _placar_tiktok(estado, agora):
    """23/10 (dona: o funil aprende com as duas plataformas): 1a leitura de cada vídeo do TikTok entre 48 e 96 h. As
    views vêm do medir_tiktok.py (1x/dia, "por_video" da grade que ele já lê). Hora de criação = id >> 32 (segundos
    unix); casa com logs/tiktok_auto_posted.json (mesma conta, até 20 min, 1 envio por vídeo) -> path -> postar.json.
    Vitória = views > mediana da MESMA conta TikTok (mín. 4 medidas e mediana > 0: conta zerada não vira vitória).
    Chave "tt:<id>": o vídeo conta 1 vez e não se mistura com o YouTube. Itens do VÍDEO (fonte, narrador, voz, teste de
    voz) vão no mesmo grupo do YouTube (medida separada do mesmo item); horário e nicho por conta em grupo do TikTok.
    Título/palavras/tags/capa NÃO entram: a legenda do TikTok é a do catalogo.legenda_reuso, não o título da ficha."""
    import placar_titulos
    med = estado.setdefault("medidas_48h_tiktok", {})
    por_conta = {}
    for r in _ler_json(TIKTOK_POSTADOS, []):
        try:
            por_conta.setdefault(r["account"], []).append((_quando(r["timestamp"]).timestamp(), r))
        except (KeyError, TypeError, ValueError):
            continue
    usados = {m.get("envio") for m in med.values()}
    for arq in sorted(TIKTOK_VIEWS.glob("*.json"))[-5:]:  # mais antigo primeiro: fica a 1a leitura na janela
        for conta, c in _ler_json(arq, {}).items():
            if not isinstance(c, dict) or not c.get("abriu") or not c.get("lido_em"):
                continue
            lido = _quando(c["lido_em"]).timestamp()
            for i, views in (c.get("por_video") or {}).items():
                chave = f"tt:{i}"
                try:
                    criado = int(i) >> 32
                except ValueError:
                    continue
                idade = (lido - criado) / 3600
                if chave in med or not 48 <= idade <= 96:
                    continue
                cand = sorted((abs(t - criado), t, r) for t, r in por_conta.get(conta, [])
                              if abs(t - criado) <= 1200 and f"{conta}|{t:.0f}" not in usados)
                m = {"conta": conta, "views": int(views), "idade_h": round(idade, 1),
                     "pub": datetime.fromtimestamp(criado, timezone.utc).isoformat(timespec="minutes")}
                if cand:
                    _, t, r = cand[0]
                    m.update(envio=f"{conta}|{t:.0f}", path=r.get("path"), projeto=r.get("tipo") or "")
                    usados.add(m["envio"])
                med[chave] = m
    for k in [k for k, m in med.items() if agora - data_utc(m["pub"]) > timedelta(days=45)]:
        del med[k]
    corte = agora - timedelta(days=30)
    base = {}
    for m in med.values():
        if data_utc(m["pub"]) >= corte:
            base.setdefault(m["conta"], []).append(m["views"])
    # 24/10 (funil do Veo): o tema vem do nome (tema_AAAAMMDD_HHMMSS[_COMPLETO]; o catálogo registra o caminho do
    # COMPLETO mas sobe a versão limpa de mesmo nome). Mesmo placar do YouTube (item do vídeo), chave tt: própria; marca
    # própria (veo_reg) pra os já medidos antes desta função também entrarem
    for chave, m in med.items():
        if m.get("veo_reg") or m.get("projeto") != "veo" or not m.get("path"):
            continue
        vs = sorted(base.get(m["conta"], []))
        if len(vs) < 4 or vs[len(vs) // 2] <= 0:
            continue
        tema_veo = re.match(r"(?:veo_)?(.+?)_\d{8}_\d{6}", Path(m["path"]).stem)
        if tema_veo:
            placar_titulos.registrar_item("veo_temas", "veo", tema_veo.group(1)[:15],
                                          _vitoria(m["views"], vs[len(vs) // 2]), chave)
        m["veo_reg"] = 1
    for chave, m in med.items():
        if m.get("placar") or not m.get("path"):
            continue
        vs = sorted(base.get(m["conta"], []))
        if len(vs) < 4 or vs[len(vs) // 2] <= 0:
            continue  # pouca amostra ou conta zerada: tenta de novo nas próximas rodadas
        venceu = _vitoria(m["views"], vs[len(vs) // 2])
        projeto = m.get("projeto") or ""
        ficha = _ler_json(Path(m["path"]).parent / "postar.json", {})
        if projeto == "parceiro" and ficha.get("parceiro"):
            placar_titulos.registrar_item("fontes", "parceiro", ficha["parceiro"], venceu, chave)
        if projeto == "parceiro" and ficha.get("midia"):
            placar_titulos.registrar_item("nicho_canal", f"tiktok:{m['conta']}", ficha["midia"], venceu, chave)
        if ficha.get("narrador"):
            placar_titulos.registrar_item("narradores", ficha.get("midia") or projeto or "?",
                                          ficha["narrador"], venceu, chave)
        if ficha.get("voz_base"):
            placar_titulos.registrar_item("voz_base", projeto or "?", str(ficha["voz_base"]), venceu, chave)
        if ficha.get("teste_voz"):
            placar_titulos.registrar_item("testes_voz", "parceiro", str(ficha["teste_voz"]), venceu, chave)
        h = _quando(m["pub"]).astimezone().hour
        placar_titulos.registrar_item("horarios", f"{projeto or '?'}/tiktok", f"{h - h % 3:02d}h", venceu, chave)
        m["placar"], m["venceu"] = 1, venceu


def medir_48h(estado, dados):
    """1a leitura de cada video PUBLICO entre 48 e 96 h de publicado (a rodada e a cada ~30 min). Guarda 45 dias."""
    med = estado.setdefault("medidas_48h", {})
    agora = datetime.now(timezone.utc)
    orig = None
    for d in dados:
        for v in d["videos"]:
            if v["id"] in med or v.get("privacy") != "public":
                continue
            h = (agora - data_utc(v["pub"])).total_seconds() / 3600
            if 48 <= h <= 96:
                orig = _origens() if orig is None else orig
                med[v["id"]] = {"canal": d["canal"]["slug"], "titulo": v["titulo"], "pub": v["pub"], "views": v["views"],
                                "idade_h": round(h, 1), "origem": orig.get(v["id"], "sem registro")}
    # canais sem token de API (os Noturnos, que só postam pelo navegador): views lidas no Studio pelo metricas_rede
    for vid, m in _ler_json(METRICAS_STUDIO, {}).items():
        if vid in med or not isinstance(m, dict) or not m.get("so_primeira") or m.get("erro") or m.get("views") is None:
            continue
        idade = m.get("idade_h") or 0
        if not 48 <= idade <= PRIMEIRA_MAX_H or not m.get("lido_em"):
            continue
        orig = _origens() if orig is None else orig
        pub = (datetime.fromisoformat(m["lido_em"]) - timedelta(hours=idade)).astimezone(timezone.utc)
        med[vid] = {"canal": m.get("canal_slug"), "titulo": m.get("titulo", ""), "views": int(m["views"]),
                    "pub": pub.isoformat(timespec="minutes"), "idade_h": idade, "origem": orig.get(vid, "sem registro"),
                    "fonte_medida": "studio"}
    for k in [k for k, m in med.items() if agora - data_utc(m["pub"]) > timedelta(days=45)]:
        del med[k]
    try:  # 23/10: TikTok no mesmo critério de 48 h (nunca derruba a medição do YouTube)
        _placar_tiktok(estado, agora)
    except Exception as e:  # noqa: BLE001
        print(f"placar do TikTok: {type(e).__name__}: {e}")
    corte = agora - timedelta(days=30)
    xs = [m for m in med.values() if data_utc(m["pub"]) >= corte]
    if not xs:
        return

    def resumo_views(vs):
        vs = sorted(vs)
        return {"n": len(vs), "mediana": vs[len(vs) // 2], "p75": vs[(3 * len(vs)) // 4],
                "pct_1000": round(100 * sum(v >= 1000 for v in vs) / len(vs)),  # a rampa de canais ainda usa este
                "pct_5000": round(100 * sum(v >= MARCO2_VIEWS for v in vs) / len(vs))}  # 23/10: a marca agora é 5 mil

    por_origem, por_canal = {}, {}
    for m in xs:
        por_origem.setdefault(m["origem"], []).append(m["views"])
        por_canal.setdefault(m["canal"], []).append(m["views"])
    campos = ("titulo", "canal", "origem", "views", "pub")
    ordem = sorted(xs, key=lambda m: -m["views"])
    por_proj_tipo, por_idioma = _placar_dimensoes([(v, m) for v, m in med.items() if data_utc(m["pub"]) >= corte])
    try:
        _placar_titulos(med, corte)
    except Exception as e:  # noqa: BLE001  (placar de título nunca derruba a medição)
        print(f"placar de títulos: {type(e).__name__}: {e}")
    try:
        _placar_veo(med, corte)
    except Exception as e:  # noqa: BLE001
        print(f"placar do Veo: {type(e).__name__}: {e}")
    try:  # 22/10 (rampa, dono: canal desbloqueado e rendendo posta 4, 5+): avalia os degraus 1x por dia
        import rampa_canais
        est_r = rampa_canais._ler()
        if est_r.get("_avaliado_em") != agora.date().isoformat():
            est_r["_avaliado_em"] = agora.date().isoformat()
            rampa_canais._gravar(est_r)
            for ch, de, para, mo in rampa_canais.rodar():
                print(f"rampa: {ch}: {de} -> {para}/dia ({mo})")
    except Exception as e:  # noqa: BLE001
        print(f"rampa de canais: {type(e).__name__}: {e}")
    out = {"_leia": "PLACAR COMUM (18/10): views de cada video em 48 h (1a leitura entre 48 e 96 h), todos os canais e "
                    "projetos, ultimos 30 dias, por origem, canal, projeto/tipo (ledger) e idioma (cadastro canais.json). "
                    "Gerado por D:/postador-de-videos/bin/notificar_telegram.py (medir_48h). Lido por mr/rede.py "
                    "(memoria_rede) e pela fila do hipercool (ordem das línguas: a que dá view vai primeiro).",
           "atualizado": agora.isoformat(timespec="minutes"), "janela_dias": 30,
           "por_origem": {k: resumo_views(v) for k, v in por_origem.items()},
           "por_canal": {k: resumo_views(v) for k, v in por_canal.items()},
           "por_projeto_tipo": {k: resumo_views(v) for k, v in por_proj_tipo.items()},
           "por_idioma": {k: resumo_views(v) for k, v in por_idioma.items()},
           "top": [{c: m[c] for c in campos} for m in ordem[:15]],
           "piores": [{c: m[c] for c in campos} for m in ordem[::-1][:10]]}
    APREND_GLOBAL.parent.mkdir(parents=True, exist_ok=True)
    tmp = APREND_GLOBAL.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(APREND_GLOBAL)


# --- Resumo diario ---

def gravar_base(estado, dados):
    base = estado.get("base_dia") or {"canais": {}, "videos": {}}
    for d in dados:
        base["canais"][d["canal"]["slug"]] = {"views": d["views"], "subs": d["subs"]}
        for v in d["videos"]:
            base["videos"][v["id"]] = v["views"]
    base["ts"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    estado["base_dia"] = base


def resumo(estado, dados):
    base = estado.get("base_dia")
    hoje = datetime.now().strftime("%d/%m/%Y")
    if not base:
        gravar_base(estado, dados)
        enviar(f"<b>Resumo {hoje}</b>\nPrimeira medição gravada; o ranking de views começa no próximo resumo.")
        return
    desde = data_utc(base["ts"])
    canais, videos = [], []
    for d in dados:
        bc = base["canais"].get(d["canal"]["slug"])
        canais.append((d["views"] - bc["views"] if bc else 0, d["subs"] - bc["subs"] if bc else 0, d))
        for v in d["videos"]:
            antes = base["videos"].get(v["id"])
            if antes is None:
                if data_utc(v["pub"]) < desde:
                    continue
                antes = 0
            if v["views"] > antes:
                videos.append((v["views"] - antes, v, d["canal"]))
    canais.sort(key=lambda x: -x[0])
    videos.sort(key=lambda x: -x[0])
    tab = [f"{i:>2} {e(d['canal']['nome'][:20]):<20} {'+' + n(dv):>7} {n(d['subs']):>5}{f' (+{ds})' if ds > 0 else ''}"
           for i, (dv, ds, d) in enumerate(canais, 1)]
    top = [f"{i}. <b>+{n(g)}</b> <a href='https://youtu.be/{v['id']}'>{e(v['titulo'][:60])}</a> ({e(c['nome'])})"
           for i, (g, v, c) in enumerate(videos[:10], 1)]
    horas = (datetime.now(timezone.utc) - desde).total_seconds() / 3600
    msg = (f"<b>Resumo {hoje}</b> - últimas {horas:.0f} h (desde {desde.astimezone():%d/%m %H:%M})\n"
           f"Views: +{n(sum(x[0] for x in canais))} | Inscritos novos: +{sum(x[1] for x in canais if x[1] > 0)}\n\n"
           f"<b>Vídeos que mais cresceram</b>\n{chr(10).join(top) or 'nenhum vídeo ganhou views'}\n\n"
           f"<b>Canais</b> (views no período | inscritos)\n<pre>{chr(10).join(tab)}</pre>")
    filas = [f"- {e(k)}: {v['n']} ({v['nivel']})" for k, v in (estado.get("filas") or {}).items() if v.get("nivel") != "ok"]
    if filas:
        msg += "\n\n<b>Filas vazias ou acabando</b>\n" + "\n".join(filas)
    enviar(msg)
    gravar_base(estado, dados)
    log(f"resumo enviado: {len(canais)} canais, {len(videos)} videos com views")


def avisar_no_ar(estado):
    """Dono 21/10: "quero ver os vídeos quando ficarem públicos" -> cada vídeo agendado que acabou de abrir vai pro
    Telegram (bot de postagem) com título e link. Só os que abriram nas últimas 6 h; 1 aviso por vídeo.
    01/11 (dona): longo = 1 mensagem própria, marcada e com som; Shorts = 1 mensagem por canal, agrupados."""
    sys.path.insert(0, r"D:\video-fila")
    import avisos as portao
    vistos = estado.setdefault("no_ar_avisados", [])
    agora = datetime.now().astimezone()
    shorts, longos = {}, []
    for l in (ROOT / "logs" / "uploads_ledger.jsonl").read_text("utf-8", errors="replace").splitlines():
        try:
            r = json.loads(l)
            pub = datetime.fromisoformat((r.get("publish_at") or "").replace("Z", "+00:00"))
        except ValueError:
            continue
        vid = r.get("video_id")
        if not vid or vid in vistos or not (agora - timedelta(hours=6) <= pub <= agora):
            continue
        info = _video(r.get("caminho"))
        titulo = info.get("titulo") or (estado.get("titulos") or {}).get(vid) or ""
        if r.get("tipo") in LONGOS:
            longos.append((r, info, vid, titulo))
        else:
            shorts.setdefault(r.get("canal") or "?", []).append((pub, vid, titulo, info))
        vistos.append(vid)
    for r, info, vid, titulo in longos:
        portao.enviar("\n".join(["🎥🎥 <b>VÍDEO LONGO NO AR</b> 🎥🎥", f"Canal: {e(r.get('canal') or '?')}",
                                 f"Vídeo: {e(titulo)}"] + _linhas_video(info, f"https://youtu.be/{vid}")),
                      "no ar longo", importante=True, chave=f"no_ar:{vid}")
    # 01/11 tarde (dona: "continua chegando individual; agrupamento por canal na mensagem de relatório"): Short não
    # avisa mais na hora — entra só no relatório (avisar_postagens, 9/14/21h), agrupado por canal
    if shorts:
        log(f"no ar: {sum(len(v) for v in shorts.values())} Short(s) em {len(shorts)} canal(is) — só no relatório")
    estado["no_ar_avisados"] = vistos[-2000:]


def main():
    args = sys.argv[1:]
    estado = carregar_estado()
    if "--retroativo" in args:
        retroativo(estado)
        salvar_estado(estado)
        return
    responder(estado)
    salvar_estado(estado)
    if "--responder" in args:
        return
    auto_responder(estado)
    try:
        avisar_no_ar(estado)
    except Exception as ex:  # noqa: BLE001
        log(f"aviso de vídeo no ar falhou: {type(ex).__name__}: {ex}")
    salvar_estado(estado)
    agora = datetime.now()
    ult = estado.get("ultimo_monitor")
    fazer_monitor = "--resumo" not in args and (
        not ult or agora - datetime.fromisoformat(ult) >= timedelta(minutes=MONITOR_MIN))
    fazer_resumo = AVISOS.get("resumo_diario") and (
        "--resumo" in args or (agora.hour >= HORA_RESUMO and estado.get("ultimo_resumo") != agora.date().isoformat()))
    if not (fazer_monitor or fazer_resumo):
        return
    dados = coletar_todos(estado, comentarios=fazer_monitor)
    if fazer_monitor and AVISOS.get("comentarios"):
        try:
            seguir_conversas(estado)
            salvar_estado(estado)
        except Exception as ex:  # noqa: BLE001 — conversa nunca derruba o monitor
            log(f"seguir_conversas: {type(ex).__name__}: {ex}")
    if fazer_resumo:
        resumo(estado, dados)
        estado["ultimo_resumo"] = agora.date().isoformat()
    try:  # resumo da rotina do portão de avisos (9h, 14h e 21h), de todos os projetos
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        if avisos.resumo_devido():
            try:
                avisar_postagens(estado)
            except Exception as ex:  # noqa: BLE001
                log(f"avisar_postagens: {ex}")
        n_res = avisos.despachar_resumo()
        if n_res:
            log(f"resumo da rotina: {n_res} aviso(s)")
    except Exception as ex:  # noqa: BLE001
        log(f"resumo da rotina: {ex}")
    if fazer_monitor:
        monitorar(estado, dados)
        avisos_projetos(estado)
        try:
            medir_48h(estado, dados)
        except Exception as ex:  # noqa: BLE001
            log(f"medir_48h: {ex}")
        estado["ultimo_monitor"] = agora.isoformat(timespec="minutes")
    if "base_dia" not in estado:
        gravar_base(estado, dados)
    salvar_estado(estado)


if __name__ == "__main__":
    main()
