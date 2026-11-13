# -*- coding: utf-8 -*-
r"""services/veo_flow/flow_http.py — Google Flow (flow.google.com) por HTTP puro: o que NÃO precisa de reCAPTCHA.

Mapeado em 28/10 (JS do site → `capturas/flow_rpcs.json`, id → Serviço.Método). Tudo vai para
`/_/AiSandboxAngularFrontend/data/batchexecute` com `at`/`f.sid`/`bl` do HTML e cabeçalho X-Same-Domain: 1.
Testado na seebotsia: créditos, modelos e status, conteúdo do projeto (130 itens), link assinado de download de cada
mídia (CDN flow-content.google, baixa sem cookie), criar/listar conversas do agente.

GERAR (imagem/vídeo/estender/editar) pede token reCAPTCHA Enterprise e ainda não passa por fora da tela — ver
PLANO_00h40.md "Onde parou". Até lá a geração continua pelo gera_auto/gera_imagem, e este módulo serve para o resto
(saldo de todas as contas sem abrir o Flow, baixar o que foi gerado, conferir o projeto).

    python -m services.veo_flow.flow_http 9250          # usa os cookies do Chrome aberto nessa porta (só lê)
    from services.veo_flow.flow_http import FlowHTTP
    f = FlowHTTP.da_porta(9250); f.creditos(); f.baixar(media_id, "saida.mp4")
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://flow.google.com"


class FlowHTTP:
    def __init__(self, cookies, projeto=None):
        """cookies: lista [{name, value, domain, path}] (Network.getAllCookies ou cookies/flow_<conta>.json)."""
        from curl_cffi import requests as creq
        self.s = creq.Session(impersonate="chrome")
        for c in cookies:
            if c["domain"].lstrip(".").endswith("google.com"):
                self.s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c.get("path", "/"))
        h = self.s.get(BASE + "/", timeout=30).text
        achar = lambda k: (re.search(r'"%s":"([^"]*)"' % k, h) or [None, None])[1]  # noqa: E731
        self.at, self.sid, self.bl = achar("SNlM0e"), achar("FdrFJe"), achar("cfb2h")
        if not self.at:
            raise RuntimeError("Flow não reconheceu o login (cookies vencidos)")
        self.projeto = projeto

    @classmethod
    def da_porta(cls, porta, salvar_em=None):
        """Lê os cookies do Chrome aberto na porta CDP (não navega, não clica) e o projeto da aba do Flow."""
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pags = [x for c in b.contexts for x in c.pages]
            pg = next((x for x in pags if "flow.google" in x.url), pags[0])
            ck = pg.context.new_cdp_session(pg).send("Network.getAllCookies")["cookies"]
            m = re.search(r"/project/([0-9a-f-]{36})", pg.url)
        ck = [{k: c[k] for k in ("name", "value", "domain", "path")} for c in ck if "google" in c["domain"]]
        if salvar_em:
            Path(salvar_em).write_text(json.dumps(ck, indent=1), "utf-8")
        return cls(ck, m.group(1) if m else None)

    def rpc(self, rid, payload, origem=None):
        """Uma chamada batchexecute; devolve o JSON decodificado (None = o servidor recusou, ver .ultimo_erro)."""
        r = self.s.post(BASE + "/_/AiSandboxAngularFrontend/data/batchexecute",
                        params={"rpcids": rid, "source-path": origem or (f"/project/{self.projeto}" if self.projeto else "/"),
                                "bl": self.bl, "f.sid": self.sid, "hl": "en", "_reqid": "1234", "rt": "c"},
                        data={"f.req": json.dumps([[[rid, json.dumps(payload), None, "generic"]]]), "at": self.at},
                        headers={"X-Same-Domain": "1", "Origin": BASE, "Referer": BASE + "/"}, timeout=60)
        self.ultimo_erro = None
        for linha in r.text.splitlines():
            if linha.startswith('[["wrb.fr"'):
                try:
                    bloco = json.loads(linha)[0]
                    if bloco[2] is None:
                        self.ultimo_erro = bloco[5] if len(bloco) > 5 else bloco
                        return None
                    return json.loads(bloco[2])
                except (ValueError, IndexError, TypeError) as ex:  # resposta cortada: vira recusa, não traceback
                    self.ultimo_erro = f"resposta ilegível ({type(ex).__name__}): {linha[:160]}"
                    return None
        self.ultimo_erro = f"HTTP {r.status_code}: {r.text[:200]}"
        return None

    @property
    def _p(self):
        if not self.projeto:
            raise RuntimeError("sem projeto (abra pela porta de uma aba do Flow ou passe projeto=)")
        return f"projects/{self.projeto}"

    # ───────── leituras ─────────

    def creditos(self):
        """Saldo de créditos do Flow (1º número do GetCredits)."""
        d = self.rpc("nzlxg", [])
        return d[0] if d else None

    def modelos(self):
        """{chave_do_modelo: nome} — o que a conta pode usar (veo_3_1_extend..., i2v, portrait/landscape...)."""
        d = (self.rpc("HTrJv", []) or [[]])[0]  # [null, null, [padrões por tipo], [[chave, [nome]], ...], ...]
        return {m[0]: (m[1] or [""])[0] for bloco in d if isinstance(bloco, list) for m in bloco
                if isinstance(m, list) and len(m) == 2 and isinstance(m[0], str) and isinstance(m[1], list)}

    def status_modelos(self):
        return {k: v for k, v in (self.rpc("yBhWQ", []) or [[]])[0]}

    def conteudo(self):
        """Itens do projeto: [{id, tipo}] (tipo 1 = mídia, 3 = voz)."""
        d = self.rpc("Zzl0ze", [self._p]) or [None] * 4
        return [{"id": x[0], "tipo": x[1], "nome": x[2]} for x in (d[3] or [])]

    def midias(self, ids):
        """Link assinado do CDN de cada mídia (vale ~horas; baixa sem cookie)."""
        d = self.rpc("Iyc41d", [list(ids)]) or []
        out = {}
        for item in json.loads(json.dumps(d)):  # achata: procura os links flow-content em qualquer profundidade
            txt = json.dumps(item)
            mid = re.search(r'"([0-9a-f]{8}-[0-9a-f-]{27})"', txt)
            url = re.search(r'"(https://flow-content\.google/[^"]+)"', txt)
            if mid and url:
                out[mid.group(1)] = url.group(1)
        if not out:  # formato aninhado diferente: varre tudo
            txt = json.dumps(d)
            for mid, url in re.findall(r'"([0-9a-f]{8}-[0-9a-f-]{27})".{0,400}?"(https://flow-content\.google/[^"]+)"', txt):
                out.setdefault(mid, url)
        txt = json.dumps(d)
        for mid in out:  # vídeo traz a miniatura (/image/) E o vídeo (/video/): o vídeo vence
            v = re.search(r'"(https://flow-content\.google/video/%s\?[^"]+)"' % re.escape(mid), txt)
            if v:
                out[mid] = v.group(1)
        return out

    def falha_geracao(self, media_id):
        """BatchCheckMediaGenerationStatus (iFxMud): texto do erro se a geração FALHOU, senão None. 01/11: o Motion
        Sync falhou no servidor ("Generation job finished with state: FAILED", código 13) e a mídia nunca virou
        arquivo — o Iyc41d só dizia "Media not found" e o baixar esperava os 15 min inteiros."""
        d = self.rpc("iFxMud", [[media_id]])
        m = re.search(r'"(Generation job finished with state: (?!SUCCE)[A-Z_]+[^"]*|PUBLIC_ERROR_[A-Z_]+|[A-Z_]+_BLOCKED)"',
                      json.dumps(d or []))
        return m.group(1) if m else None

    def baixar(self, media_id, destino):
        url = self.midias([media_id]).get(media_id)
        if not url:
            raise RuntimeError(f"sem link para {media_id}: {self.ultimo_erro}")
        r = self.s.get(url, timeout=300)
        r.raise_for_status()
        if not r.content:
            raise RuntimeError(f"{media_id}: download veio vazio")
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        # 30/10: tmp + replace — o Veo/gera_imagem pegam o arquivo pelo nome final; meio arquivo não pode aparecer lá
        tmp = destino.with_name(destino.name + ".parcial")
        tmp.write_bytes(r.content)
        tmp.replace(destino)
        return destino, r.headers.get("content-type"), len(r.content)

    def subir_video(self, caminho, corte=None):
        """Envia um vídeo para o projeto (base do Motion Sync / editar vídeo). Devolve o media_id.
        Upload "Scotty" retomável do JS (SCOTTY_UPLOADER_FACTORY, capturas/flow_js_s1.js @2044496): POST start ->
        X-Goog-Upload-URL -> POST "upload, finalize". Não pede reCAPTCHA: o X-Framework-Xsrf-Token é o mesmo `at`.
        corte=(ini_s, fim_s): o Flow corta no servidor (x-trim-start/x-trim-end em ms), como o recorte da tela."""
        import mimetypes
        import urllib.parse
        p = Path(caminho)
        dados = p.read_bytes()
        mime = mimetypes.guess_type(p.name)[0] or "video/mp4"
        h = {"X-Framework-Xsrf-Token": self.at, "Slug": urllib.parse.quote(p.name), "Origin": BASE,
             "Referer": f"{BASE}/project/{self.projeto}"}
        if corte:
            h["x-trim-start"], h["x-trim-end"] = str(round(corte[0] * 1000)), str(round(corte[1] * 1000))
        r = self.s.post(f"{BASE}/upload/v1/flow/upload/video/{self.projeto}", timeout=60, headers={
            **h, "X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(len(dados)), "X-Goog-Upload-Header-Content-Type": mime})
        url = r.headers.get("X-Goog-Upload-URL") or r.headers.get("x-goog-upload-url")
        if not url:
            raise RuntimeError(f"upload de {p.name} sem X-Goog-Upload-URL (HTTP {r.status_code}: {r.text[:200]})")
        r = self.s.post(url, data=dados, timeout=600, headers={
            **h, "X-Goog-Upload-Command": "upload, finalize", "X-Goog-Upload-Offset": "0", "Content-Type": mime})
        if r.status_code != 200:
            raise RuntimeError(f"upload de {p.name}: HTTP {r.status_code}: {r.text[:300]}")
        try:
            d = r.json()
        except ValueError:
            raise RuntimeError(f"upload de {p.name}: resposta não é JSON: {r.text[:300]}")
        mid = d.get("mediaId") or ((d.get("media") or {}).get("name") or "").split("/")[-1]
        if not mid:
            raise RuntimeError(f"upload de {p.name} sem mediaId: {json.dumps(d)[:300]}")
        return mid

    # ───────── agente (conversas) ─────────

    def criar_conversa(self):
        d = self.rpc("csbIsb", [self._p])
        return d[0][0] if d else None

    def conversas(self):
        d = self.rpc("mrlkwd", [self._p]) or [[]]
        return [{"id": x[0], "titulo": (x[1] or [None])[0]} for x in d[0]]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    arg = sys.argv[1]
    if arg.isdigit():
        f = FlowHTTP.da_porta(int(arg))
    else:  # arquivo de cookies + id do projeto
        f = FlowHTTP(json.loads(Path(arg).read_text("utf-8")), sys.argv[2])
    itens = f.conteudo()
    mids = [i["id"] for i in itens if i["tipo"] == 1][:2]
    print(json.dumps({"projeto": f.projeto, "creditos": f.creditos(), "status_modelos": f.status_modelos(),
                      "n_modelos": len(f.modelos()), "itens": len(itens), "conversas": f.conversas()[:3],
                      "links": f.midias(mids)}, ensure_ascii=False, indent=1)[:2500])
    if mids:
        print(f.baixar(mids[0], ROOT / "capturas" / "flow_baixado_teste.bin"))


if __name__ == "__main__":
    main()
