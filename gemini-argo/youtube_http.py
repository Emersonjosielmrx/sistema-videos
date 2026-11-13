#!/usr/bin/env python3
r"""youtube_http.py — dados do YouTube por HTTP puro, sem navegador.

Público (sem login): inscritos, views totais e views dos últimos vídeos/Shorts via youtubei/v1/browse.
Studio (com login): views/tempo/inscritos dos últimos N dias, impressões e CTR por vídeo, lista de vídeos
com agendados, privacidade, reivindicação de terceiros e monetização. Usa os cookies .youtube.com da conta
(pegos 1× pelo cofre com `sync`) + SAPISIDHASH; os cookies se renovam a cada chamada.

    python youtube_http.py UCRrz2BKdhCzy1-nAAs2E8bg        # público, 1 canal
    python youtube_http.py --todos                         # público, todos do canais.json
    python youtube_http.py sync <slug|--todos>             # abre o cofre 1× e guarda cookies do YouTube
    python youtube_http.py studio <slug|--todos> [dias]    # analytics + vídeos do Studio (padrão 28 dias)
"""
import hashlib
import json
import re
import sys
import time
from decimal import Decimal
from pathlib import Path

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
CONTEXTO = {"client": {"clientName": "WEB", "clientVersion": "2.20251020.01.00", "hl": "pt", "gl": "BR"}}
API = "https://www.youtube.com/youtubei/v1/browse?prettyPrint=false"
ABAS = {"videos": "EgZ2aWRlb3PyBgQKAjoA", "shorts": "EgZzaG9ydHPyBgUKA5oBAA%3D%3D", "sobre": None}
CANAIS = Path(r"D:\postador-de-videos\config\canais.json")

_s = requests.Session()
_s.headers.update({"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9", "Origin": "https://www.youtube.com"})


def _numero(txt):
    """'1,2 mil visualizações' / '3,4 mi de inscritos' / '12.345 visualizações' -> int."""
    if not txt:
        return None
    t = txt.lower().replace("\xa0", " ")
    m = re.search(r"(\d[\d.,]*)\s*(mil|mi|bi|k|m|b)?(?![a-zà-ú])", t)
    if not m:
        return 0 if re.search(r"\b(nenhum|sem)", t) else None
    num, mult = m.group(1), m.group(2)
    if mult:  # Decimal: float faria 4,1 mi virar 4099999
        return int(Decimal(num.replace(",", ".")) * {"mil": 1000, "k": 1000, "mi": 10**6, "m": 10**6,
                                                      "bi": 10**9, "b": 10**9}[mult])
    return int(re.sub(r"[.,]", "", num))


def _browse(channel_id, params=None):
    corpo = {"context": CONTEXTO, "browseId": channel_id}
    if params:
        corpo["params"] = params.replace("%3D", "=")
    r = _s.post(API, json=corpo, timeout=30)
    r.raise_for_status()
    return r.json()


def _achar(obj, chave):
    """Todos os valores de `chave` em qualquer profundidade."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == chave:
                yield v
            yield from _achar(v, chave)
    elif isinstance(obj, list):
        for v in obj:
            yield from _achar(v, chave)


def _texto(v):
    if isinstance(v, dict):
        if "simpleText" in v:
            return v["simpleText"]
        if "runs" in v:
            return "".join(r.get("text", "") for r in v["runs"])
        if "content" in v:
            return v["content"]
    return v if isinstance(v, str) else ""


def videos(channel_id, aba="videos"):
    """Últimos vídeos (aba 'videos') ou Shorts (aba 'shorts'): [{id, titulo, views, quando}]."""
    d = _browse(channel_id, ABAS[aba])
    saida = []
    for v in _achar(d, "videoRenderer"):
        saida.append({"id": v.get("videoId"), "titulo": _texto(v.get("title")),
                      "views": _numero(_texto(v.get("viewCountText"))),
                      "quando": _texto(v.get("publishedTimeText"))})
    for v in _achar(d, "shortsLockupViewModel"):
        vid = (v.get("onTap", {}).get("innertubeCommand", {}).get("reelWatchEndpoint", {}).get("videoId"))
        ov = v.get("overlayMetadata", {})
        saida.append({"id": vid, "titulo": ov.get("primaryText", {}).get("content", ""),
                      "views": _numero(ov.get("secondaryText", {}).get("content", "")), "quando": ""})
    return saida


def canal(channel_id):
    """Resumo público do canal: nome, inscritos, nº de vídeos, views totais, últimos vídeos e Shorts."""
    d = _browse(channel_id)
    meta = next(_achar(d, "channelMetadataRenderer"), {})
    cab = json.dumps(next(_achar(d, "pageHeaderViewModel"), {}), ensure_ascii=False)
    insc = re.search(r'"content":\s*"([^"]*inscrit[^"]*)"', cab)
    nvid = re.search(r'"content":\s*"([^"]*v[íi]deos?)"', cab)
    res = {"channel_id": channel_id, "nome": meta.get("title"),
           "inscritos": _numero(insc.group(1)) if insc else None,
           "videos_no_canal": _numero(nvid.group(1)) if nvid else None}
    res["views_total"] = _views_total(d)
    res["ultimos_videos"] = videos(channel_id, "videos")[:10]
    res["ultimos_shorts"] = videos(channel_id, "shorts")[:10]
    return res


def _views_total(d):
    """Views totais ficam no painel 'Sobre' (aboutChannelViewModel), que vem por continuação."""
    tokens = [c.get("token") for c in _achar(d, "continuationCommand") if isinstance(c, dict)]
    for t in tokens:
        r = _s.post(API, json={"context": CONTEXTO, "continuation": t}, timeout=30)
        if r.ok:
            sobre = next(_achar(r.json(), "aboutChannelViewModel"), None)
            if sobre:
                return _numero(sobre.get("viewCountText"))
    return None


# ───────────────────────────── Studio (com login) ─────────────────────────────

STUDIO = "https://studio.youtube.com"
MAPA = Path(r"D:\postador-de-videos\config\youtube_navegador.json")
COOKIES_DIR = Path(r"D:\gemini-argo\cookies_youtube")
COOKIES_DIR.mkdir(exist_ok=True)
PERIODOS = {7: "ANALYTICS_TIME_PERIOD_TYPE_WEEK", 28: "ANALYTICS_TIME_PERIOD_TYPE_FOUR_WEEKS",
            90: "ANALYTICS_TIME_PERIOD_TYPE_QUARTER", 365: "ANALYTICS_TIME_PERIOD_TYPE_YEAR",
            0: "ANALYTICS_TIME_PERIOD_TYPE_LIFETIME"}


def _mapa():
    m = json.loads(MAPA.read_text("utf-8"))
    return m.get("canais", m)


def _email(slug):
    return _mapa()[slug]["email"]


# 13/11: o YouTube parou de entregar o cookie SAPISID em .youtube.com pra várias contas (vem só __Secure-3PAPISID /
# __Secure-1PAPISID, mesmo valor) e o código dizia "conta deslogada no cofre" com o Studio ABERTO no painel do canal:
# 68 envios do dia caíram pro Chrome dos notebooks por isso. Qualquer um dos três serve pra assinar.
# YT_SO_SAPISID=1 volta a exigir o nome antigo.
_SAP_NOMES = (("SAPISID", "SAPISIDHASH"), ("__Secure-1PAPISID", "SAPISID1PHASH"), ("__Secure-3PAPISID", "SAPISID3PHASH"))


def tem_sapisid(ck):
    """ck = dict de cookies (ou jar do requests). True se dá pra assinar."""
    if __import__("os").environ.get("YT_SO_SAPISID") == "1":
        return bool(ck.get("SAPISID"))
    return any(ck.get(n) for n, _h in _SAP_NOMES)


def autorizacao(ck, origem=None):
    """Cabeçalho Authorization. O valor do SAPISID, do __Secure-1PAPISID e do __Secure-3PAPISID é o mesmo; conferido
    13/11 no inovaremanhwabr (só tinha o 3P): "SAPISID3PHASH" sozinho = 401; "SAPISIDHASH" com o valor do 3P = 200.
    Manda os três rótulos com o valor que existir (é o que o Studio do navegador faz)."""
    origem = origem or STUDIO
    v = None
    for nome, _r in _SAP_NOMES:
        try:
            v = ck.get(nome)
        except Exception:  # noqa: BLE001 — jar com o mesmo cookie em 2 domínios
            v = next((c.value for c in ck if c.name == nome), None)
        if v or __import__("os").environ.get("YT_SO_SAPISID") == "1":
            break
    ts = int(time.time())
    h = hashlib.sha1(f"{ts} {v} {origem}".encode()).hexdigest()
    return " ".join(f"{rot} {ts}_{h}" for _n, rot in _SAP_NOMES)


def sincronizar(slug):
    """Única etapa com navegador: abre o perfil da conta no cofre, entra no Studio e guarda os cookies .youtube.com."""
    sys.path.insert(0, r"D:\logins-google")
    sys.path.insert(0, r"D:\postador-de-videos\bin\netbooks")
    import chrome_conta
    import cofre
    from playwright.sync_api import sync_playwright
    email = _email(slug)
    chrome_conta._liberar_ram()
    porta, proc = cofre.abrir(email, url="about:blank", visivel=False)
    br = None
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = br.contexts[0]
            pg = ctx.new_page()
            pg.goto(STUDIO, wait_until="domcontentloaded", timeout=90000)
            time.sleep(6)
            todos = ctx.new_cdp_session(pg).send("Network.getAllCookies")["cookies"]
            pg.close()
    finally:
        cofre.fechar(proc, br, email)
    ck = {c["name"]: c["value"] for c in todos if c.get("domain", "").endswith("youtube.com")}
    if not tem_sapisid(ck):
        raise RuntimeError(f"{slug}: sem SAPISID (conta deslogada no cofre?)")
    (COOKIES_DIR / f"{slug}.json").write_text(json.dumps(ck, indent=1), "utf-8")
    return len(ck)


class Studio:
    """Sessão HTTP no Studio de 1 canal. Pega chave/versão/canal do HTML e assina cada chamada com SAPISIDHASH."""

    def __init__(self, slug):
        self.slug = slug
        self.arq = COOKIES_DIR / f"{slug}.json"
        try:
            html = self._entrar() if self.arq.exists() else ""
        except ValueError:  # 30/10: arquivo de cookies cortado no meio da gravação = trata como vencido
            html = ""
        cid = re.search(r'"CHANNEL_ID":"([^"]+)', html)
        if not cid:  # sem cookies ou vencidos (o Chrome do cofre gira o login): pega de novo e tenta 1×
            sincronizar(slug)
            html = self._entrar()
            cid = re.search(r'"CHANNEL_ID":"([^"]+)', html)
            if not cid:
                raise RuntimeError(f"{slug}: Studio não reconheceu o login nem depois de ressincronizar")
        self.channel_id = cid.group(1)
        versao = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)', html)
        chave = re.search(r'"INNERTUBE_API_KEY":"([^"]+)', html)
        if not (versao and chave):
            raise RuntimeError(f"{slug}: a página do Studio veio sem INNERTUBE_* (tela de consentimento?)")
        self.versao, self.chave = versao.group(1), chave.group(1)

    def _entrar(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        # 30/10: com domínio; o update(dict) criava cookies sem domínio e o Set-Cookie do Studio (.youtube.com) virava
        # uma 2ª cópia de cada um (as duas iam no pedido; SAPISID duplicado = CookieConflictError)
        for k, v in json.loads(self.arq.read_text("utf-8")).items():
            self.s.cookies.set(k, v, domain=".youtube.com", path="/")
        return self.s.get(STUDIO + "/", timeout=30).text

    def _gravar_cookies(self):
        """Gravação atômica: tarefa morta no meio da escrita deixava o JSON cortado e o canal falhando até sync à mão."""
        d = {}
        for c in self.s.cookies:
            if c.domain.endswith("youtube.com") or c.name not in d:
                d[c.name] = c.value
        tmp = self.arq.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, indent=1), "utf-8")
        tmp.replace(self.arq)

    def _post(self, rota, corpo):
        hd = {"Authorization": autorizacao(self.s.cookies),
              "X-Origin": STUDIO, "Origin": STUDIO, "x-goog-authuser": "0"}
        corpo["context"] = {"client": {"clientName": 62, "clientVersion": self.versao, "hl": "pt", "gl": "BR"}}
        r = self.s.post(f"{STUDIO}/youtubei/v1/{rota}?alt=json&key={self.chave}", json=corpo, headers=hd, timeout=40)
        r.raise_for_status()
        self._gravar_cookies()  # cookies renovados
        return r.json()

    def videos(self, quantos=30):
        """Últimos uploads: privacidade, agendamento, views/likes/comentários, engaged views, reivindicação, monetização."""
        mask = {"videoId": True, "title": True, "privacy": True, "timePublishedSeconds": True, "lengthSeconds": True,
                "scheduledPublishingDetails": {"all": True}, "publicMetrics": {"all": True},
                "privateMetrics": {"all": True}, "claimDetails": {"all": True}, "monetization": {"all": True},
                "allRestrictions": {"all": True}}
        d = self._post("creator/list_creator_videos", {
            "filter": {"and": {"operands": [{"channelIdIs": {"value": self.channel_id}},
                                            {"videoOriginIs": {"value": "VIDEO_ORIGIN_UPLOAD"}}]}},
            "order": "VIDEO_ORDER_DISPLAY_TIME_DESC", "pageSize": quantos, "mask": mask})
        saida = []
        for v in d.get("videos", []):
            pm, pv = v.get("publicMetrics", {}), v.get("privateMetrics", {})
            ag = (v.get("scheduledPublishingDetails", {}).get("scheduledPublishings") or [{}])[0]
            saida.append({
                "id": v["videoId"], "titulo": v.get("title", ""),
                "privacidade": v.get("privacy", "").replace("VIDEO_PRIVACY_", "").lower(),
                "publicado": int(v.get("timePublishedSeconds", 0)) or None,
                "agendado_para": int(ag["scheduledTimeSeconds"]) if ag.get("scheduledTimeSeconds") else None,
                "segundos": int(v.get("lengthSeconds", 0)),
                "views": int(pm.get("externalViewCount", 0)), "likes": int(pm.get("likeCount", 0)),
                "comentarios": int(pm.get("commentCount", 0)), "engaged_views": int(pv.get("engagedViewCount", 0)),
                "reivindicado": v.get("claimDetails", {}).get("videoHasThirdPartyClaim", False),
                "restricao": v.get("allRestrictions", {}).get("summary", {}).get("severity", "").replace(
                    "VIDEO_RESTRICTIONS_SEVERITY_", "").lower(),
                "monetizacao": v.get("monetization", {}).get("adMonetization", {}).get("effectiveStatus", "")
                .replace("VIDEO_MONETIZING_STATUS_", "").lower()})
        return saida

    def analytics(self, dias=28, top=15):
        """Totais do período (views, horas, inscritos, impressões, CTR, duração média) + top vídeos com impressões/CTR."""
        if dias not in PERIODOS:
            raise ValueError(f"período {dias} dias não existe no Studio; use {', '.join(map(str, PERIODOS))}")
        tela ={"entity": {"channelId": self.channel_id}, "timePeriod": {"timePeriodType": PERIODOS[dias]},
                "currency": "USD", "timeZoneOffsetSecs": -10800}
        grupos = [["EXTERNAL_VIEWS", "EXTERNAL_WATCH_TIME", "SUBSCRIBERS_NET_CHANGE"],
                  ["VIDEO_THUMBNAIL_IMPRESSIONS", "VIDEO_THUMBNAIL_IMPRESSIONS_VTR", "AVERAGE_WATCH_TIME"]]
        colunas = ["EXTERNAL_VIEWS", "VIDEO_THUMBNAIL_IMPRESSIONS", "VIDEO_THUMBNAIL_IMPRESSIONS_VTR", "AVERAGE_WATCH_TIME"]
        cartoes = [{"keyMetricCardConfig": {"timePeriod": {}, "metricTabConfigs": [{"metric": m} for m in g]},
                    "failureMode": "ANALYTICS_CARD_FAILURE_MODE_HIDE"} for g in grupos]
        cartoes.append({"tableCardConfig": {"dimension": "VIDEO", "metrics": colunas, "maxRowCount": top,
                                            "order": "ANALYTICS_TABLE_CARD_ORDER_TOP_METRIC"},
                        "failureMode": "ANALYTICS_CARD_FAILURE_MODE_HIDE"})
        d = self._post("yta_web/get_cards", {"screenConfig": tela, "cardConfigs": cartoes})
        totais, titulos, tabela = {}, {}, []
        for card in d.get("cards", []):
            for aba in card.get("keyMetricCardData", {}).get("keyMetricTabs", []):
                pc = aba.get("primaryContent", {})
                totais[pc.get("metric")] = pc.get("total")
            for v in card.get("sideEntities", {}).get("videos", []):
                titulos[v["entityData"]["videoId"]] = v["entityData"].get("title", "")
            dados = card.get("tableCardData", {}).get("mainTableData")
            if dados:
                ids = dados["dimensionColumns"][0]["strings"]["values"]
                cols = {}
                for c in dados["metricColumns"]:
                    vals = next((x["values"] for k, x in c.items() if k != "metric" and isinstance(x, dict)
                                 and "values" in x), [])
                    cols[c["metric"]["type"]] = vals
                for i, vid in enumerate(ids):
                    tabela.append({"id": vid, **{m: (cols.get(m) or [None] * len(ids))[i] for m in colunas}})
        for linha in tabela:
            linha["titulo"] = titulos.get(linha["id"], "")
        return {"dias": dias or "tudo", "views": totais.get("EXTERNAL_VIEWS"),
                "horas_assistidas": round((totais.get("EXTERNAL_WATCH_TIME") or 0) / 3.6e6, 1),
                "inscritos_ganhos": totais.get("SUBSCRIBERS_NET_CHANGE"),
                "impressoes": totais.get("VIDEO_THUMBNAIL_IMPRESSIONS"),
                "ctr": totais.get("VIDEO_THUMBNAIL_IMPRESSIONS_VTR"),
                "duracao_media_s": round((totais.get("AVERAGE_WATCH_TIME") or 0) / 1000, 1),
                "top_videos": tabela}


def _slugs(arg):
    return list(_mapa()) if arg == "--todos" else [arg]


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "sync":
        for slug in _slugs(sys.argv[2]):
            try:
                print(f"{slug:24} ok ({sincronizar(slug)} cookies)")
            except Exception as e:
                print(f"{slug:24} ERRO {e}")
        return
    if len(sys.argv) > 2 and sys.argv[1] == "studio":
        dias = int(sys.argv[3]) if len(sys.argv) > 3 else 28
        varios = sys.argv[2] == "--todos"
        for slug in _slugs(sys.argv[2]):
            try:
                st = Studio(slug)
                a = st.analytics(dias)
                if varios:
                    print(f"{slug:24} views={a['views']!s:>7} horas={a['horas_assistidas']!s:>6} "
                          f"insc={a['inscritos_ganhos']!s:>4} impr={a['impressoes']!s:>7} ctr={a['ctr']}")
                else:
                    print(json.dumps({"analytics": a, "videos": st.videos()}, ensure_ascii=False, indent=1))
            except Exception as e:
                print(f"{slug:24} ERRO {str(e)[:120]}")
        return
    if "--todos" in sys.argv:
        cfg = json.loads(CANAIS.read_text("utf-8"))["canais"]
        ids = [(k, c["channel_id"]) for k, c in cfg.items() if c.get("channel_id")]
        for slug, cid in ids:
            try:
                c = canal(cid)
                soma_s = sum(v["views"] or 0 for v in c["ultimos_shorts"])
                print(f"{slug:28} insc={c['inscritos']!s:>8}  views={c['views_total']!s:>10}  "
                      f"vídeos={c['videos_no_canal']!s:>5}  10 últimos Shorts={soma_s}")
            except Exception as e:
                print(f"{slug:28} ERRO {e}")
        return
    print(json.dumps(canal(sys.argv[1]), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
