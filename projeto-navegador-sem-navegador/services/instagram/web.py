# -*- coding: utf-8 -*-
r"""services/instagram/web.py — Instagram por HTTP puro com a sessão do Chrome do cofre (perfil ig_<conta>).

Como o site faz (capturado em 28/10 com tools\capturar_pagina.py, arquivo capturas\ig_recenas.jsonl):
POST /api/graphql com doc_id + variables + fb_dtsg + lsd (tirados do HTML da página), cabeçalhos X-IG-App-ID/X-FB-LSD/
X-CSRFToken. Conexão por curl_cffi imitando o Chrome (com `requests` comum o Instagram responde "não logado" ou 429)
e o MESMO User-Agent do Chrome do perfil (core\cofre_cookies.py) — cuidado de "aparelho novo".

Os doc_id mudam quando o Instagram atualiza o site. Quando uma consulta parar (erro ou dado vazio), rode de novo:
    python tools\capturar_pagina.py ig_<conta> capturas\ig_<conta>.jsonl https://www.instagram.com/<conta>/ ^
        https://www.instagram.com/<conta>/reels/ --filtro "graphql|/api/v1/"
e este módulo passa a usar os doc_id novos (lê o .jsonl de captura mais novo).

    python -m services.instagram.web recenas.ia            # perfil + Reels (views/curtidas/comentários)
"""
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.cofre_cookies import pegar, salvar, sessao  # noqa: E402

APP_ID = "936619743392459"


def _modelos():
    """{friendly_name: {campos do formulário}} das capturas (a mais nova vence)."""
    out = {}
    if not (ROOT / "capturas").is_dir():  # 29/10 (Fable, D23): nos notebooks/PC2 vai só o modelos_ig.json (sem cookies)
        return json.loads((ROOT / "modelos_ig.json").read_text("utf-8"))
    arqs = sorted((ROOT / "capturas").glob("ig_*.jsonl"), key=lambda p: p.stat().st_mtime)
    # 30/10: reler os ~25 MB de capturas custava ~7 s em TODO Reel/QUERO/seguir; cache refeito só quando uma muda
    chave = [[a.name, a.stat().st_size, a.stat().st_mtime_ns] for a in arqs]
    cache = ROOT / "capturas" / "_modelos_ig_cache.json"
    try:
        c = json.loads(cache.read_text("utf-8"))
        if c.get("chave") == chave:
            return c["modelos"]
    except (OSError, ValueError, KeyError, AttributeError):
        pass
    for arq in arqs:
        with arq.open(encoding="utf-8", errors="replace") as f:
            linhas = f.readlines()
        for linha in linhas:
            try:  # 30/10: 1 linha cortada (captura interrompida) derrubava TODO post por HTTP da produção
                r = json.loads(linha)
            except ValueError:
                continue
            if not isinstance(r, dict) or not isinstance(r.get("enviado") or "", str):
                continue
            q = {k: v[0] for k, v in urllib.parse.parse_qs(r.get("enviado") or "").items()}
            if q.get("doc_id") and q.get("fb_api_req_friendly_name"):
                out[q["fb_api_req_friendly_name"]] = q
    try:
        from core.arquivo import gravar_json
        gravar_json(cache, {"chave": chave, "modelos": out}, indent=None)
    except OSError:
        pass  # sem cache: só fica mais lento
    return out


class InstagramWeb:
    def __init__(self, conta, perfil_cofre=None):
        self.conta = conta
        self.perfil = perfil_cofre or f"ig_{conta}"
        self.s = sessao(self.perfil, ["instagram.com"], url="https://www.instagram.com/", chrome_tls=True)
        self._usar_proxy()
        self.modelos = _modelos()
        self._tokens()

    def _usar_proxy(self):
        """12/11 (dona: "use os 10 IPs grátis, melhor que todos pelo mesmo IP de casa"): IG_PROXY=http://127.0.0.1:<porta>
        (ponte do IP fixo Webshare da conta, postador/bin/proxy_tiktok.py) — a sessão HTTP sai por ele. Sem a env =
        como antes (IP de casa)."""
        px = os.environ.get("IG_PROXY")
        if px:
            self.s.proxies = {"http": px, "https": px}

    def _tokens(self, pagina=None):
        h = self.s.get(pagina or f"https://www.instagram.com/{self.conta}/", timeout=30).text
        dtsg = re.search(r'"DTSGInitialData",\[\],\{"token":"([^"]+)"', h) or re.search(r'"dtsg":\{"token":"([^"]+)"', h)
        lsd = re.search(r'"LSD",\[\],\{"token":"([^"]+)"', h)
        if not dtsg or "not-logged-in" in h[:2000]:
            # cookie velho: o Chrome do cofre renova a sessão; pega de novo 1x
            pegar(self.perfil, "https://www.instagram.com/")
            self.s = sessao(self.perfil, ["instagram.com"], chrome_tls=True)
            self._usar_proxy()
            h = self.s.get(f"https://www.instagram.com/{self.conta}/", timeout=30).text
            dtsg = re.search(r'"DTSGInitialData",\[\],\{"token":"([^"]+)"', h)
            lsd = re.search(r'"LSD",\[\],\{"token":"([^"]+)"', h)
            if not dtsg:
                raise RuntimeError(f"{self.conta}: Instagram não reconheceu o login (logar pelo instagram_local.py)")
        self.dtsg, self.lsd = dtsg.group(1), lsd.group(1) if lsd else ""
        self.uid = self.s.cookies.get("ds_user_id")
        # 13/11: versão do site (o navegador manda X-Instagram-AJAX=<rev> e __rev; o configure_to_clips passou a recusar
        # com 1357001 "Entre para continuar" desde 06/11 sem esses campos)
        rev = re.search(r'"client_revision":(\d+)', h) or re.search(r'"__spin_r":(\d+)', h) or re.search(r'"rev":(\d+)', h)
        self.rev = rev.group(1) if rev else "1"
        claim = re.search(r'"claim":"([^"]+)"', h)
        self.claim = claim.group(1) if claim else ""

    def graphql(self, nome, variaveis):
        """Uma consulta GraphQL do site pelo nome (o doc_id vem da captura)."""
        m = self.modelos.get(nome)
        if not m:
            raise KeyError(f"consulta {nome} não capturada ainda (rode tools\\capturar_pagina.py)")
        corpo = {k: m[k] for k in ("av", "__a", "__comet_req", "doc_id", "fb_api_caller_class",
                                   "fb_api_req_friendly_name", "server_timestamps") if k in m}
        corpo.update({"__user": "0", "av": self.uid or m.get("av", ""), "fb_dtsg": self.dtsg, "lsd": self.lsd,
                      "variables": json.dumps(variaveis, separators=(",", ":"))})
        hd = {"X-IG-App-ID": APP_ID, "X-FB-LSD": self.lsd, "X-CSRFToken": self.s.cookies.get("csrftoken") or "",
              "X-ASBD-ID": "359341", "X-FB-Friendly-Name": nome, "Origin": "https://www.instagram.com",
              "Referer": f"https://www.instagram.com/{self.conta}/",
              "Content-Type": "application/x-www-form-urlencoded"}
        r = self.s.post("https://www.instagram.com/api/graphql", data=corpo, headers=hd, timeout=40)
        r.raise_for_status()
        txt = r.text
        if txt.startswith("for (;;);"):  # 29/10: erro do site vem assim ({"__ar":1,"error":1357031,"errorSummary":...})
            d = json.loads(txt[9:])
            raise RuntimeError(f"{nome}: Instagram recusou ({d.get('error')}: {d.get('errorSummary')}) — conta "
                               f"{self.conta} restrita/checkpoint? (abra o Instagram nela)")
        try:
            d = json.loads(txt)
        except ValueError:  # página de login/desafio em HTML no lugar do JSON
            raise RuntimeError(f"{nome}: resposta não é JSON (HTTP {r.status_code}): {txt[:160]!r}") from None
        if d.get("errors") and not d.get("data"):
            raise RuntimeError(f"{nome}: {str(d['errors'])[:200]}")
        salvar(self.s)
        return d.get("data", {})

    @staticmethod
    def _variaveis(m, **troca):
        v = json.loads(m.get("variables") or "{}")
        for k, x in troca.items():
            if k in v:
                v[k] = x
            if isinstance(v.get("data"), dict) and k in v["data"]:
                v["data"][k] = x
        return v

    # ───────── leitura ─────────

    def perfil_info(self, uid=None):
        """Seguidores, seguindo, nº de posts, bio, link, conta profissional."""
        m = self.modelos["PolarisProfilePageContentQuery"]
        d = self.graphql("PolarisProfilePageContentQuery", self._variaveis(m, id=uid or self.uid))
        u = next((v for v in d.values() if isinstance(v, dict) and "username" in v), {})
        return {"usuario": u.get("username"), "id": u.get("pk") or u.get("id"), "seguidores": u.get("follower_count"),
                "seguindo": u.get("following_count"), "posts": u.get("media_count"), "bio": u.get("biography"),
                "link": (u.get("bio_links") or [{}])[0].get("url") if u.get("bio_links") else u.get("external_url"),
                "profissional": u.get("is_business") or u.get("is_professional_account"),
                "categoria": u.get("category"),
                "ultimo_story": u.get("latest_reel_media")}  # epoch do Story mais recente (0/None = sem Story ativo)

    def reels(self, uid=None, quantos=12):
        """Reels do perfil: código, views (play_count), curtidas, comentários, data, legenda."""
        m = self.modelos["PolarisProfileReelsTabContentQuery"]
        alvo = uid or self.uid
        v = self._variaveis(m, target_user_id=alvo, user_id=alvo, page_size=quantos)
        d = self.graphql("PolarisProfileReelsTabContentQuery", v)
        conn = next((x.get("clips_connection") for x in d.values() if isinstance(x, dict) and "clips_connection" in x),
                    None) or next((x for x in d.values() if isinstance(x, dict) and "edges" in x), {})
        out = []
        for e in conn.get("edges", []):
            md = e.get("node", {}).get("media", {})
            out.append({"codigo": md.get("code"), "id": md.get("pk") or md.get("id"), "views": md.get("play_count"),
                        "curtidas": md.get("like_count"), "comentarios": md.get("comment_count"),
                        "quando": md.get("taken_at"),
                        "legenda": ((md.get("caption") or {}).get("text") or "")[:120]})
        return out

    def posts(self, quantos=12):
        """Posts do feed (fotos, carrossel e Reels): tipo, curtidas, comentários (o feed não traz views)."""
        m = self.modelos["PolarisProfilePostsQuery"]
        v = self._variaveis(m, username=self.conta, count=quantos)
        d = self.graphql("PolarisProfilePostsQuery", v)
        conn = next((x for x in d.values() if isinstance(x, dict) and "edges" in x), {})
        tipos = {1: "foto", 2: "video", 8: "carrossel"}
        return [{"codigo": n.get("code"), "id": n.get("pk") or n.get("id"),
                 "tipo": "reel" if n.get("product_type") == "clips" else tipos.get(n.get("media_type"), n.get("media_type")),
                 "curtidas": n.get("like_count"), "comentarios": n.get("comment_count"), "quando": n.get("taken_at"),
                 "legenda": ((n.get("caption") or {}).get("text") or "")[:120]}
                for n in (e.get("node", {}) for e in conn.get("edges", []))]

    def saiu(self, legenda_trecho, horas=24):
        """Confere se um post saiu de verdade: procura um post recente cuja legenda contém o trecho."""
        limite = time.time() - horas * 3600
        t = legenda_trecho.lower()[:60]
        return next((p for p in self.posts(12) if (p["quando"] or 0) >= limite and t in p["legenda"].lower()), None)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from core.maquinas import ou_remoto  # 29/10 (D31): conta logada só numa máquina -> lê de lá (JSON igual)
    if ou_remoto(f"ig_{sys.argv[1]}", "services.instagram.web") is not None:
        return
    ig = InstagramWeb(sys.argv[1])
    print(json.dumps({"perfil": ig.perfil_info(), "reels": ig.reels(), "posts": ig.posts()[:5]}, ensure_ascii=False,
                     indent=1))


if __name__ == "__main__":
    main()
