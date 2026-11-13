# -*- coding: utf-8 -*-
r"""services/youtube/studio_analytics.py — dados do YouTube Studio que a Data API não dá, por HTTP puro.

Usa a sessão do D:\gemini-argo\youtube_http.Studio (cookies .youtube.com do cofre + SAPISIDHASH; ressincroniza sozinha
pelo cofre se o login cair) e a API de consulta do próprio Studio (`yta_web/join`), descoberta no JS do Studio em 28/10:
consulta = dimensões + métricas + filtros ("restricts") + período. Testado ao vivo no animescomia e no manhwanoturno.

    Shorts: "viram x pularam" (SHORTS_FEED_IMPRESSIONS_VTR) do canal e de cada Short
    Retenção segundo a segundo (AUDIENCE_INDEX 0..100 x AUDIENCE_WATCH_RELATIVE) + os pontos onde o público mais sai
    % médio assistido, duração média, CTR da miniatura por vídeo
    Origem do tráfego (Feed dos Shorts, Pesquisa, Sugeridos...) e os termos de busca reais (YT_SEARCH.<termo>)

    python -m services.youtube.studio_analytics animescomia            # resumo do canal (28 dias)
    python -m services.youtube.studio_analytics animescomia --video ID # retenção e quedas de 1 vídeo
"""
import datetime
import json
import sys

sys.path.insert(0, r"D:\gemini-argo")
import youtube_http  # noqa: E402

ORDEM_DESC = "ANALYTICS_ORDER_DIRECTION_DESC"


def _dia(d):
    return int(d.strftime("%Y%m%d"))


class StudioAnalytics:
    def __init__(self, slug):
        self.studio = youtube_http.Studio(slug)
        self.cid = self.studio.channel_id

    def _periodo(self, dias):
        if not dias:
            return {"unboundedRange": {}}
        hoje = datetime.date.today()
        return {"dateIdRange": {"inclusiveStart": _dia(hoje - datetime.timedelta(days=dias)), "exclusiveEnd": _dia(hoje)}}

    def consulta(self, dimensoes, metricas, filtros=None, dias=28, limite=50, ordem=None):
        """Uma consulta crua do Studio. filtros = {"VIDEO": [ids], "TRAFFIC_SOURCE_TYPE": ["YT_SEARCH"], ...}; o canal
        entra sempre (dimensão USER — "CHANNEL" o servidor recusa). Devolve [{dim: valor, métrica: valor}]."""
        restr = [{"dimension": {"type": "USER"}, "inValues": [self.cid]}]
        restr += [{"dimension": {"type": k}, "inValues": list(v)} for k, v in (filtros or {}).items()]
        ordens = [{"metric": {"type": ordem or metricas[0]}, "direction": ORDEM_DESC}] if dimensoes and ordem is not False else []
        q = {"dimensions": [{"type": d} for d in dimensoes], "metrics": [{"type": m} for m in metricas],
             "restricts": restr, "orders": ordens, "timeRange": self._periodo(dias),
             "limit": {"pageSize": limite, "pageOffset": 0}, "currency": "USD", "returnDataInNewFormat": True}
        d = self.studio._post("yta_web/join", {"nodes": [{"key": "Q", "value": {"query": q}}], "connectors": []})
        try:
            tab = d["results"][0]["value"].get("resultTable", {})
        except (KeyError, IndexError, TypeError, AttributeError):  # canal sem dado no período / formato novo
            raise RuntimeError(f"yta_web/join sem resultTable: {str(d)[:200]}") from None
        colunas = {}
        for c in tab.get("dimensionColumns", []):
            vals = next((x["values"] for k, x in c.items() if isinstance(x, dict) and "values" in x), [])
            colunas[c["dimension"]["type"]] = vals
        for c in tab.get("metricColumns", []):
            vals = next((x["values"] for k, x in c.items() if k != "metric" and isinstance(x, dict) and "values" in x), [])
            colunas[c["metric"]["type"]] = vals
        n = max((len(v) for v in colunas.values()), default=0)
        return [{k: (v[i] if i < len(v) else None) for k, v in colunas.items()} for i in range(n)]

    # ───────── canal ─────────

    def shorts_vtr(self, dias=28):
        """Canal: impressões no feed dos Shorts e % que ficou assistindo (o resto pulou)."""
        r = self.consulta([], ["SHORTS_FEED_IMPRESSIONS", "SHORTS_FEED_IMPRESSIONS_VTR"], dias=dias)
        r = r[0] if r else {}
        return {"impressoes_feed": r.get("SHORTS_FEED_IMPRESSIONS"), "ficaram_pct": r.get("SHORTS_FEED_IMPRESSIONS_VTR")}

    def trafego(self, dias=28):
        """Views e horas por origem (SHORTS, YT_SEARCH, RELATED_VIDEO, SUBSCRIBER, EXT_URL...)."""
        # .get: o Studio omite a coluna da métrica que o canal não tem (ex.: canal sem Shorts) — antes era KeyError
        return [{"origem": r.get("TRAFFIC_SOURCE_TYPE"), "views": r.get("EXTERNAL_VIEWS"),
                 "horas": round((r.get("EXTERNAL_WATCH_TIME") or 0) / 3.6e6, 2)}
                for r in self.consulta(["TRAFFIC_SOURCE_TYPE"], ["EXTERNAL_VIEWS", "EXTERNAL_WATCH_TIME"], dias=dias)]

    def termos_busca(self, dias=28, limite=50, video=None):
        """Termos que as pessoas digitaram no YouTube e que trouxeram views (do canal ou de 1 vídeo)."""
        f = {"TRAFFIC_SOURCE_TYPE": ["YT_SEARCH"]}
        if video:
            f["VIDEO"] = [video]
        return [{"termo": (r.get("TRAFFIC_SOURCE_DETAIL") or "").split(".", 1)[-1], "views": r.get("EXTERNAL_VIEWS")}
                for r in self.consulta(["TRAFFIC_SOURCE_DETAIL"], ["EXTERNAL_VIEWS"], f, dias, limite)]

    def videos(self, dias=28, limite=50):
        """Por vídeo: views, % médio assistido, duração média, impressões e CTR da miniatura, Shorts: % que ficou."""
        mets = ["EXTERNAL_VIEWS", "AVERAGE_WATCH_PERCENTAGE", "AVERAGE_WATCH_TIME", "VIDEO_THUMBNAIL_IMPRESSIONS",
                "VIDEO_THUMBNAIL_IMPRESSIONS_VTR", "SHORTS_FEED_IMPRESSIONS", "SHORTS_FEED_IMPRESSIONS_VTR",
                "SUBSCRIBERS_NET_CHANGE"]
        return [{"id": r.get("VIDEO"), "views": r.get("EXTERNAL_VIEWS"), "pct_assistido": r.get("AVERAGE_WATCH_PERCENTAGE"),
                 "duracao_media_s": round((r.get("AVERAGE_WATCH_TIME") or 0) / 1000, 1),
                 "impressoes": r.get("VIDEO_THUMBNAIL_IMPRESSIONS"), "ctr": r.get("VIDEO_THUMBNAIL_IMPRESSIONS_VTR"),
                 "shorts_impressoes": r.get("SHORTS_FEED_IMPRESSIONS"),
                 "shorts_ficaram_pct": r.get("SHORTS_FEED_IMPRESSIONS_VTR"), "inscritos": r.get("SUBSCRIBERS_NET_CHANGE")}
                for r in self.consulta(["VIDEO"], mets, dias=dias, limite=limite)]

    # ───────── 1 vídeo ─────────

    def retencao(self, video, duracao_s=None):
        """Curva de retenção: 101 pontos (0..100% do vídeo), cada um = % das views que ainda assistia ali (>100 no
        começo = gente voltando). Com duracao_s, cada ponto ganha o segundo. Mais `quedas`: os 5 trechos com maior perda
        (é isso que a IA de roteiro deve cortar). Vídeo novo ou com poucas views volta vazio (o Studio ainda não tem)."""
        linhas = self.consulta(["AUDIENCE_INDEX"], ["AUDIENCE_WATCH_RELATIVE", "AUDIENCE_RELATIVE"],
                               {"VIDEO": [video]}, dias=0, limite=300, ordem=False)
        curva = [{"pos_pct": r["AUDIENCE_INDEX"], "ficou_pct": r.get("AUDIENCE_WATCH_RELATIVE"),
                  "vs_outros": r.get("AUDIENCE_RELATIVE")} for r in linhas if r.get("AUDIENCE_INDEX") is not None]
        curva.sort(key=lambda p: p["pos_pct"])
        if duracao_s:
            for p in curva:
                p["segundo"] = round(p["pos_pct"] / 100 * duracao_s, 1)
        quedas = [{"de": a, "ate": b, "perdeu": round((a["ficou_pct"] or 0) - (b["ficou_pct"] or 0), 2)}
                  for a, b in zip(curva, curva[1:])]
        quedas = sorted(quedas, key=lambda q: -q["perdeu"])[:5]
        return {"video": video, "curva": curva,
                "quedas": [{"pos_pct": q["de"]["pos_pct"], "segundo": q["de"].get("segundo"), "perdeu_pct": q["perdeu"]}
                           for q in quedas],
                "fim_pct": curva[-1]["ficou_pct"] if curva else None}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    slug = sys.argv[1]
    a = StudioAnalytics(slug)
    if "--video" in sys.argv:
        vid = sys.argv[sys.argv.index("--video") + 1]
        print(json.dumps({**a.retencao(vid), "termos_busca": a.termos_busca(video=vid, limite=15)}, ensure_ascii=False,
                         indent=1))
        return
    print(json.dumps({"shorts": a.shorts_vtr(), "trafego": a.trafego(), "termos_busca": a.termos_busca(limite=20),
                      "videos": a.videos(limite=10)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
