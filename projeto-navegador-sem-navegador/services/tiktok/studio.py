# -*- coding: utf-8 -*-
r"""services/tiktok/studio.py — analytics do TikTok Studio por HTTP puro (cookies do Chrome do cofre).

Capturado em 28/10 (capturas\tiktok_filmenoturno.jsonl e tiktok_video.jsonl, tools\capturar_pagina.py) e testado na
filmenoturno sem abrir Chrome:
  GET  /tiktokstudio/api/web/user                     -> userId + tt-csrf-token
  GET  /aweme/v2/data/insight/?type_requests=[...]    -> métricas da conta e de cada vídeo (sem X-Bogus/msToken)
  POST /tiktok/creator/manage/item_list/v1/           -> todos os vídeos com views/curtidas (a tela assina; sem
                                                          assinatura o servidor aceitou igual)
IP: cada conta do TikTok sai por um IP fixo da Webshare (D:\postador-de-videos\bin\proxy_tiktok.py); este módulo usa o
mesmo repassador local (127.0.0.1:18200+N), menos as contas "sem_proxy", que saem pela internet de casa como sempre.

    python -m services.tiktok.studio filmenoturno            # conta + vídeos + detalhe dos 3 com mais views
    python -m services.tiktok.studio --cookies-todos         # 1x: cookie de todas as contas (Chrome, 1 por vez)
    from services.tiktok.studio import TikTokStudio
    t = TikTokStudio("filmenoturno"); t.conta_resumo(); t.videos(); t.video(item_id)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.cofre_cookies import ler, pegar, salvar, sessao  # noqa: E402

B = "https://www.tiktok.com"
REUSO = Path(r"D:\postador-de-videos\config\reuso_plataformas.json")
COMUM = {"locale": "pt-BR", "aid": "1988", "priority_region": "BR", "region": "BR", "tz_name": "America/Sao_Paulo",
         "app_name": "tiktok_creator_center", "app_language": "pt-BR", "device_platform": "web_pc",
         "channel": "tiktok_web", "os": "win", "tz_offset": "-10800"}
POR_VIDEO = ["video_info", "item_search_terms", "video_traffic_source_percent_realtime", "video_retention_rate_realtime",
             "video_view_realtime", "video_total_duration_realtime", "video_per_duration_realtime",
             "video_finish_rate_realtime", "video_new_followers", "video_vv_history_7d",
             "video_viewer_new_viewer_percent", "video_viewer_follower_percent", "video_viewer_age_percent_realtime",
             "video_viewer_gender_percent_realtime", "video_viewer_location_percent_realtime"]


def _contas():
    return json.loads(REUSO.read_text("utf-8"))["tiktok"]


def _proxy(conta):
    """Flags/endereço do IP fixo da conta (None = internet de casa), igual ao postar_tiktok_auto.abrir_conta."""
    cfg = _contas()
    r = cfg["contas"][conta]
    if not cfg.get("proxy_webshare") or r.get("sem_proxy"):
        return None
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import proxy_tiktok
    n = proxy_tiktok.ip_da_conta(conta)
    if not (proxy_tiktok.garantir() and proxy_tiktok.pronto(n)):
        raise RuntimeError(f"{conta}: IP {n} da Webshare sem túnel agora; não leio pela internet de casa")
    return n, proxy_tiktok.flags(n), f"http://127.0.0.1:{proxy_tiktok.porta(n)}"


def _chrome_aberto(perfil):
    sys.path.insert(0, r"D:\logins-google")
    import cofre
    _, e = cofre.conta(perfil)
    return cofre._cdp_vivo(e["porta"]) or bool(cofre.porta_aberta(Path(e["pasta"])))


def _json(r, onde):
    """JSON da resposta; página de bloqueio (WAF/captcha em HTML) vira RuntimeError legível, não JSONDecodeError."""
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError(f"{onde}: resposta não é JSON (HTTP {r.status_code}): {r.text[:160]!r}") from None
    if not isinstance(d, dict):
        raise RuntimeError(f"{onde}: resposta inesperada: {str(d)[:160]}")
    return d


def _valor(x):
    """Desembrulha {status, value} e {value: {status, value}} do insight; status != 0 = sem dado (None)."""
    if not isinstance(x, dict):
        return x
    if "status" in x:
        if x["status"] != 0:
            return None
        return _valor(x["value"]) if "value" in x else {k: v for k, v in x.items() if k != "status"}
    return _valor(x["value"]) if "value" in x else x


class TikTokStudio:
    def __init__(self, conta, navegador=True):
        """navegador=False: nunca abre o Chrome do cofre (sem cookie ou cookie vencido = RuntimeError "sem_login")."""
        self.conta = conta
        self.perfil = _contas()["contas"][conta]["cofre"]
        px = _proxy(conta)

        def renovar():
            if not navegador:
                raise RuntimeError(f"{conta}: sem_login (cookie do TikTok ausente/vencido no cofre {self.perfil})")
            if px and _chrome_aberto(self.perfil):  # Chrome já aberto não recebe as flags do proxy
                raise RuntimeError(f"{conta}: Chrome do cofre já aberto sem o proxy da conta; tente depois")
            pegar(self.perfil, B + "/tiktokstudio", espera=10, extra=px[1] if px else ())

        novo = ler(self.perfil) is None or not any("tiktok" in c["domain"] for c in ler(self.perfil)["cookies"])
        if novo:
            renovar()
        self._abrir(px)
        u = self._user()
        if not u.get("userId") and not novo:
            renovar()  # cookie velho: renova 1x
            self._abrir(px)
            u = self._user()
        if not u.get("userId"):
            raise RuntimeError(f"{conta}: TikTok não reconheceu o login (cofre {self.perfil})")
        self.uid, self.csrf = u["userId"], u.get("tt-csrf-token")
        base = (u.get("userBaseInfo") or {}).get("UserProfile", {}).get("UserBase", {})
        self.arroba, self.nome = base.get("UniqId"), base.get("NickName")

    def _abrir(self, px):
        self.s = sessao(self.perfil, ["tiktok.com"], chrome_tls=True)
        if px:
            self.s.proxies = {"http": px[2], "https": px[2]}

    def _user(self):
        r = self.s.get(B + "/tiktokstudio/api/web/user", params={"needIsVerified": "true", "needProfileBio": "true"},
                       headers={"Referer": B + "/tiktokstudio"}, timeout=40)
        u = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if str(u.get("userId") or "0") == "0":  # deslogado responde userId "0" + "user not found"
            u.pop("userId", None)
        return u

    def _hd(self):
        return {"agw-js-conv": "str", "tt-csrf-token": self.csrf or "", "Referer": B + "/tiktokstudio/analytics",
                "Accept": "application/json, text/plain, */*"}

    def insight(self, pedidos):
        """Chamada crua do insight: pedidos = [{"insigh_type": ..., ...}] (a grafia "insigh" é a do site)."""
        r = self.s.get(B + "/aweme/v2/data/insight/", headers=self._hd(), timeout=60,
                       params={**COMUM, "type_requests": json.dumps(pedidos, separators=(",", ":"))})
        d = _json(r, "insight")
        if d.get("status_code") != 0:
            raise RuntimeError(f"insight recusado: {str(d)[:200]}")
        salvar(self.s)
        return d

    # ───────── conta ─────────

    def conta_resumo(self, dias=7):
        """Seguidores, views/perfil/curtidas/compartilhamentos por dia, origem do tráfego e termos de busca."""
        p = [{"insigh_type": t, "days": dias, "end_days": 1} for t in
             ("vv_history", "pv_history", "like_history", "comment_history", "share_history", "follower_num_history",
              "reached_audience_history", "vv_traffic_source")]
        d = self.insight(p + [{"insigh_type": "follower_num"}])
        # unique_viewer_num oscila no servidor ({"status": 2} na mesma chamada que antes deu 2147, 28/10): pode vir None
        d.update({k: v for k, v in self.insight([{"insigh_type": "unique_viewer_num", "range": 1},
                                                 {"insigh_type": "user_search_terms", "range": 1}]).items()
                  if v is not None})
        serie = lambda k: [_valor(x) for x in (d.get(k) or [])]  # noqa: E731
        return {"conta": self.conta, "arroba": self.arroba, "seguidores": _valor(d.get("follower_num")),
                "espectadores_unicos": _valor(d.get("unique_viewer_num")), "dias": dias,
                "views_dia": serie("vv_history"), "visitas_perfil_dia": serie("pv_history"),
                "curtidas_dia": serie("like_history"), "comentarios_dia": serie("comment_history"),
                "compartilhamentos_dia": serie("share_history"), "seguidores_dia": serie("follower_num_history"),
                "alcance_dia": serie("reached_audience_history"),
                "trafego": {x["key"]: x["value"] for x in (_valor(d.get("video_page_percent")) or [])},
                "termos_busca": {x["key"]: x["value"] for x in (_valor(d.get("user_search_terms")) or [])}}

    def videos(self, quantos=200):
        """Todos os vídeos postados (mais novo primeiro): id, data, duração, views, curtidas, comentários, compart."""
        out, cursor = [], 0
        while len(out) < quantos:
            corpo = {"cursor": cursor, "size": 50, "query": {"sort_orders": [{"field_name": "post_time", "order": 2}],
                                                            "conditions": [], "is_recent_posts": False}}
            r = self.s.post(B + "/tiktok/creator/manage/item_list/v1/", params=COMUM, timeout=60,
                            headers={**self._hd(), "Content-Type": "application/json"}, data=json.dumps(corpo))
            d = _json(r, "item_list")
            itens = d.get("item_list") or []
            for x in itens:
                out.append({"id": x["item_id"], "quando": int(x.get("post_time") or x.get("create_time") or 0),
                            "duracao_s": round((x.get("duration") or 0) / 1000, 1), "legenda": x.get("desc"),
                            "views": int(x.get("play_count") or 0), "curtidas": int(x.get("like_count") or 0),
                            "comentarios": int(x.get("comment_count") or 0),
                            "compartilhamentos": int(x.get("share_count") or 0),
                            "salvos": int(x.get("favorite_count") or 0), "status": x.get("status"),
                            "link": f"https://www.tiktok.com/@{self.arroba}/video/{x['item_id']}"})
            novo_cursor = d.get("cursor") or cursor + 50
            # 30/10: has_more sem itens ou com o mesmo cursor = laço infinito (a tarefa NSN_Inteligencia travava)
            if not d.get("has_more") or not itens or novo_cursor == cursor:
                break
            cursor = novo_cursor
        return out[:quantos]

    # ───────── vídeo ─────────

    def video(self, item_id):
        """Tempo médio assistido, taxa de conclusão, retenção segundo a segundo, origem do tráfego, termos de busca,
        público (novos x recorrentes, idade, gênero, cidade) de um vídeo."""
        d = self.insight([{"insigh_type": t, "aweme_id": str(item_id)} for t in POR_VIDEO])
        info = d.get("video_info") or {}
        st = info.get("statistics") or {}
        ret = (_valor(d.get("video_retention_rate_realtime")) or {})
        ret = ret.get("list") if isinstance(ret, dict) else ret
        loc = _valor(d.get("video_viewer_location_percent_realtime")) or {}
        return {"id": str(item_id), "legenda": info.get("desc"),
                "duracao_s": round(((info.get("video") or {}).get("duration") or 0) / 1000, 1),
                "views": st.get("play_count"), "curtidas": st.get("digg_count"), "comentarios": st.get("comment_count"),
                "compartilhamentos": st.get("share_count"), "salvos": st.get("collect_count"),
                "tempo_medio_s": _valor(d.get("video_per_duration_realtime")),
                "conclusao": _valor(d.get("video_finish_rate_realtime")),
                "tempo_total_s": _valor(d.get("video_total_duration_realtime")),
                "novos_seguidores": _valor(d.get("video_new_followers")),
                "retencao": [(int(p["timestamp"]) / 1000, p["value"]) for p in (ret or [])],
                "trafego": {x["key"]: x["value"] for x in (_valor(d.get("video_traffic_source_percent_realtime")) or [])},
                "termos_busca": {x["key"]: x["value"] for x in (_valor(d.get("item_search_terms")) or [])},
                "espectadores_novos": _valor(d.get("video_viewer_new_viewer_percent")),
                "de_seguidores": _valor(d.get("video_viewer_follower_percent")),
                "idade": {x["key"]: x["value"] for x in (_valor(d.get("video_viewer_age_percent_realtime")) or [])},
                "genero": {x["key"]: x["value"] for x in (_valor(d.get("video_viewer_gender_percent_realtime")) or [])},
                "paises": {x.get("country_name"): x.get("country_vv_percent") for x in (loc.get("country_percent_list") or [])}
                if isinstance(loc, dict) else {},
                "cidades": {x["key"]: x["value"] for p in (loc.get("country_percent_list") or [])[:1]
                            for x in (p.get("city_percent_list") or [])} if isinstance(loc, dict) else {},
                "views_7d": [_valor(x) for x in (d.get("video_vv_history_7d") or [])]}


def cookies_todos():
    """Único passo com Chrome, 1 conta por vez: pega o cookie do TikTok de quem ainda não tem (ou venceu), com o proxy
    da conta. Pula conta com Chrome já aberto (postando). Resultado em logs\\tiktok_cookies.jsonl."""
    import time
    log = ROOT / "logs" / "tiktok_cookies.jsonl"
    for conta, r in _contas()["contas"].items():
        if not r.get("cofre"):
            continue
        try:
            TikTokStudio(conta, navegador=False)
            res = "ja_tinha"
        except Exception:  # noqa: BLE001
            try:
                if _chrome_aberto(r["cofre"]):
                    res = "pulada: Chrome aberto"
                else:
                    t = TikTokStudio(conta)
                    res = f"ok @{t.arroba}"
            except Exception as e:  # noqa: BLE001
                res = f"erro: {str(e)[:150]}"
        print(f"{conta:28} {res}", flush=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"quando": time.strftime("%Y-%m-%d %H:%M"), "conta": conta, "res": res},
                               ensure_ascii=False) + "\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.argv[1] == "--cookies-todos":
        return cookies_todos()
    t = TikTokStudio(sys.argv[1])
    vids = t.videos()
    top = sorted(vids, key=lambda v: -v["views"])[:3]
    det = [t.video(v["id"]) for v in top]
    for x in det:
        x["retencao"] = x["retencao"][:6] + [("...", len(x["retencao"]))]
    print(json.dumps({"resumo": t.conta_resumo(), "n_videos": len(vids), "videos": vids[:5], "top3": det},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
