# -*- coding: utf-8 -*-
r"""services/veo_flow/flow_gerar.py — GERAR no Google Flow por HTTP; o Chrome só fabrica o token do reCAPTCHA.

Como (28/10, provado ao vivo na mundosolar):
  * O Flow troca grecaptcha.enterprise.execute por uma armadilha ("extension_hijack_detected") quando o reCAPTCHA fica
    pronto (função TVa do JS) e guarda o original só para ele. Token de chamada de fora = PUBLIC_ERROR_UNUSUAL_ACTIVITY.
  * A ARMADILHA abaixo (Page.addScriptToEvaluateOnNewDocument) pega o execute original no instante em que o TVa vai
    travá-lo (Object.defineProperty). Com ele o token sai em ~0,4 s, sem digitar nada, e o StreamChat por HTTP puro é
    ACEITO.
  * Estender vídeo: o agente recusa; vai pelo RPC direto fZytfe (ver estender()).
  * Token vale UMA vez (o 2º uso volta UNUSUAL_ACTIVITY): um token por pedido.
  * O Playwright trava 5 min no connect_over_cdp do Chrome 156 (alvos "browser_ui"): a aba é falada por websocket
    direto (core\cdp_aba.py).

Fluxo de cada pedido: CreateSession (conversa) -> StreamChat (agente do Flow; ferramentas generate_image/
generate_video/...) -> lê o fluxo até o fim -> media_id de cada resultado "success" -> link assinado -> baixa.
A MESMA conversa aceita correção ("troque o fundo...") — passe conversa= no pedir().

    python -m services.veo_flow.flow_gerar mundosolar imagem "A red apple on a white table" saida.png [--formato 9:16]
    python -m services.veo_flow.flow_gerar mundosolar video "A drone shot over a solar farm" saida.mp4 [--formato 16:9]
    python -m services.veo_flow.flow_gerar mundosolar motion "woman (her face, curly red hair and green sweater)" \
        saida.mp4 --imagem pessoa.jpg \
        --video movimentos.mp4 [--formato 9:16] [--fundo imagem|video]   # MOTION SYNC (MOTION_SYNC.md)
    python -m services.veo_flow.flow_gerar mundosolar colher        # só grava cookies/flow_mundosolar.json (saúde)
    from services.veo_flow.flow_gerar import FlowGerador
    with FlowGerador("mundosolar") as fg: fg.imagem("...", "a.png", refs=["foto.jpg"])

MODO WORKER (29/10, D30 em FABLE_DECISOES.md) — roda NOS NOTEBOOKS / PC2 dentro do nsn_worker, sem o Veo instalado:
o PC1 abre o Chrome do perfil lá (chrome_conta.py, porta 9460), manda este comando por ssh e recebe o mp4 de volta.
O Chrome só serve para o token; com --fechar-chrome ele é fechado assim que o Flow aceita o pedido (os minutos da
geração são HTTP puro, 0 RAM de Chrome). O prompt pode vir de um arquivo ("@caminho") porque o cmd do PC2 estraga
acento. Saída com marcadores lidos pelo PC1 (maquina_remota.Remoto.nsn_flow_video):
    FLOW_CREDITOS saldo=N | FLOW_SEM_CREDITO saldo=N | FLOW_LOGIN | FLOW_PEDIDO_OK conversa=... segundos=N
    FLOW_CHROME_SOLTO chrome_s=N | FLOW_OK <arquivo> bytes=N | FLOW_RECUSADO <motivo> | FLOW_ERRO <motivo>

    python3 -m services.veo_flow.flow_gerar --porta 9460 --projeto <url ou id> --nome <perfil> [--fechar-chrome] \
        video @prompt.txt saida.mp4 [--formato 9:16] [--modelo "Veo 3.1 - Fast"] [--imagem-inicial foto.jpg]
"""
import base64
import json
import mimetypes
import os
import random
import re
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ─── disjuntor (12/11, dona: "o Flow perde muito tempo e dá muita falha, principalmente em imagens") ──────────────
# Medido 12/11: 583 pedidos de imagem por HTTP, ~2% saíram; o resto voltou VAZIO em ~3 s ("o agente não entregou
# mídia": a chamada StreamChat não bate com o Flow novo, de agente) e cada um ainda custava ~77 s de abrir/token antes —
# 875 min de máquina num dia. Agora: 8 respostas vazias seguidas = HTTP pausado 60 min pra TODO mundo (vai direto pelo
# Chrome); depois tenta de novo sozinho; qualquer mídia entregue fecha. FLOW_HTTP_DISJUNTOR=0 desliga.
DISJUNTOR = ROOT / "logs" / "flow_http_disjuntor.json"
DISJUNTOR_FALHAS, DISJUNTOR_MIN = 8, 60


def disjuntor_aberto():
    if os.environ.get("FLOW_HTTP_DISJUNTOR", "1") == "0":
        return ""
    try:
        d = json.loads(DISJUNTOR.read_text("utf-8"))
    except (OSError, ValueError):
        return ""
    ate = float(d.get("aberto_ate") or 0)
    return f"{d.get('falhas', 0)} vazias seguidas, volta {time.strftime('%H:%M', time.localtime(ate))}" if ate > time.time() else ""


def disjuntor_registrar(ok):
    try:
        try:
            d = json.loads(DISJUNTOR.read_text("utf-8"))
        except (OSError, ValueError):
            d = {}
        if ok:
            d = {"falhas": 0, "aberto_ate": 0, "ultimo_ok": time.strftime("%d/%m %H:%M")}
        else:
            d["falhas"] = int(d.get("falhas", 0)) + 1
            if d["falhas"] >= DISJUNTOR_FALHAS and float(d.get("aberto_ate") or 0) <= time.time():
                d["aberto_ate"] = time.time() + DISJUNTOR_MIN * 60
                d["abriu_em"] = time.strftime("%d/%m %H:%M")
        DISJUNTOR.parent.mkdir(parents=True, exist_ok=True)
        DISJUNTOR.write_text(json.dumps(d), "utf-8")
    except OSError:
        pass
sys.path.insert(0, str(ROOT))
from core.arquivo import gravar_json  # noqa: E402
from core.cdp_aba import Aba  # noqa: E402
from services.veo_flow.flow_http import BASE, FlowHTTP  # noqa: E402

VEO = r"D:\veo\beta"
LOG = ROOT / "logs" / "flow_gerar.jsonl"
COOKIES = ROOT / "cookies"
CREDITO_MINIMO = int(os.environ.get("VEO_CREDITO_MINIMO", "20"))  # Veo 3.1 Fast custa ~20 (creditos_contas.py)
CHAT = (BASE + "/_/AiSandboxAngularFrontend/data/google.internal.labs.aisandbox.proto.flow.agent.v1."
        "FlowCreationAgentService/StreamChat")
# 29/10: a versão nova do reCAPTCHA (NhfdZHzre166o...) quebra com getter/setter em window.grecaptcha (o execute nunca
# nasce e a aba trava). O TVa do Flow faz Object.defineProperty(enterprise, "execute", armadilha): pega o original ali.
ARMADILHA = r"""(() => {
  const dp = Object.defineProperty;
  const defineProperty = function defineProperty(o, p, d) {
    try {
      if (p === 'execute' && o && typeof o.execute === 'function' && typeof o.ready === 'function' && !window.__nsnOrig)
        window.__nsnOrig = o.execute.bind(o);
    } catch (e) {}
    return dp(o, p, d);
  };
  defineProperty.toString = () => 'function defineProperty() { [native code] }';
  Object.defineProperty = defineProperty;
})();"""


OK = ("success", "queued", "pending", "running", "in_progress")
# Motion Sync (MOTION_SYNC.md). O prompt curto e natural; o longo de proibições do MotionFlow AI só foi testado
# junto com o vídeo recém-enviado (a causa real das falhas, ver motion()) e não é usado.
MOTION_PROMPT = ("Edit: the person in the video becomes the {quem} from the reference image, doing exactly the same "
                 "movements, gestures, expressions and timing as in the video. {fundo}")
MOTION_ESPERA_S = int(os.environ.get("FLOW_MOTION_ESPERA_S", "120"))  # vídeo enviado precisa "assentar" no Flow
MOTION_FUNDO = {"imagem": "Use the background and lighting of the reference image.",
                "video": "Keep the background of the video."}


class Recusado(RuntimeError):
    """O Flow recusou o pedido (UNUSUAL_ACTIVITY, política, sem crédito...)."""


class PedeLogin(RuntimeError):
    """Fábrica de tokens: a conta abriu no login do Google (deslogada do Flow)."""


def _valor(v):
    """[null, null, "txt"] / [null, 12] / [null, null, null, true] -> o primeiro que não é None."""
    if isinstance(v, list):
        return next((x for x in v if x is not None), None)
    return v


def _ferramentas(no, out):
    """Acha [nome, nome, [[[chave, valor]...]]] (chamada ou resultado de ferramenta do agente) em qualquer nível."""
    if isinstance(no, list):
        if (len(no) >= 3 and isinstance(no[0], str) and no[0] == no[1] and isinstance(no[2], list)
                and no[2] and isinstance(no[2][0], list)):
            try:
                out.append({"ferramenta": no[0], **{k: _valor(v) for k, v in no[2][0]}})
                return
            except (TypeError, ValueError):
                pass
        for x in no:
            _ferramentas(x, out)


def ler_fluxo(txt):
    """Texto do StreamChat -> {"ferramentas": [...], "texto": resposta escrita, "recusa": código ou None}."""
    ferr, partes, recusa = [], [], None
    for linha in txt.splitlines():
        if not linha.startswith('[["wrb.fr"'):
            continue
        try:  # 30/10: uma linha cortada no fim do stream derrubava o pedido JÁ aceito (créditos gastos, mídia perdida)
            bloco = json.loads(linha)[0]
            if bloco[2] is None:
                recusa = json.dumps(bloco[5] if len(bloco) > 5 else bloco)[:300]
                continue
            d = json.loads(bloco[2])
        except (ValueError, IndexError, TypeError):
            continue
        _ferramentas(d, ferr)
        for m in re.finditer(r'\["text",\[null,null,"((?:[^"\\]|\\.)*)"\]\]', bloco[2]):
            partes.append(json.loads(f'"{m.group(1)}"'))
    return {"ferramentas": ferr, "texto": "".join(partes), "recusa": recusa}


class FlowGerador:
    """Uma conta do Flow. No PC1: sessão do D:\\veo\\beta\\contas.py (abre o Chrome dela e segura a trava da porta).
    Modo worker (porta= e url=): o Chrome do perfil JÁ está aberto nessa porta (chrome_conta.py); nada do Veo é lido
    e o Chrome não é fechado no fim (quem abriu fecha) — só com soltar_apos_pedido, logo que o Flow aceita o pedido."""

    def __init__(self, sessao, log=print, porta=None, url=None, soltar_apos_pedido=False, fechar_chrome=None,
                 fabrica=None, perfil=None):
        self.sessao, self.log = sessao, log
        self.aba = None
        self.abri = False
        # 02/11 (dona: "deixando fabricando os tokens"): fabrica = endereço do fabrica_tokens.py desta máquina; o Chrome
        # quente da conta (perfil) fica lá, aberto, e daqui só se pede cookies e token — nada de abrir/fechar Chrome
        self.fabrica, self.perfil = fabrica, (perfil or sessao).lower()
        self.worker = porta is not None or fabrica is not None
        self.soltar_apos_pedido = soltar_apos_pedido
        self.fechar_chrome = fechar_chrome  # função sem argumentos que fecha o Chrome local (modo worker)
        self.t_inicio = time.time()
        if fabrica:
            self.porta, self.g, self.trava = None, None, None
            self.url = url if "/project/" in (url or "") else f"{BASE}/project/{url}"
            return
        if self.worker:
            self.porta = int(porta)
            self.url = url if "/project/" in (url or "") else f"{BASE}/project/{url}"
            self.g, self.trava = None, None
            return
        sys.path.insert(0, VEO)
        sys.path.insert(0, r"D:\flow-imagens")
        from filelock import FileLock
        import gera_imagem
        self.g, self.porta = gera_imagem._conta_ctx(sessao)
        self.url = self.g._load_proj_map().get(sessao)
        if not self.url or "/project/" not in self.url:
            raise RuntimeError(f"{sessao}: sem projeto salvo no proj_map do Veo")
        self.trava = FileLock(os.path.join(VEO, "logs", f".cdp_lock_{self.porta}"), timeout=600)

    def __enter__(self):
        if self.fabrica:
            d = self._fab("sessao", projeto=self.url)
            todos = d["cookies"]
            ck = [c for c in todos if "google" in c["domain"]]
            self.f = FlowHTTP(ck, self.url.split("/project/")[1].split("?")[0])
            self.colher(ck, todos)
            return self
        if self.trava:
            self.trava.acquire()
        try:
            if self.worker:
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{self.porta}/json/version", timeout=5)
                except Exception as e:  # noqa: BLE001
                    raise RuntimeError(f"{self.sessao}: Chrome não está aberto na porta {self.porta} ({e})")
            else:
                os.environ["FLOW_JANELA_OCULTA"] = "1"  # 29/10: o Chrome do token fica fora da tela (gera_auto)
                self.abri = self.g._ensure_chrome_running(self.porta, self.log) == "novo"
            self.aba = Aba.da_porta(self.porta, nova="about:blank")
            self.aba.chamar("Page.enable")
            self.aba.chamar("Page.addScriptToEvaluateOnNewDocument", {"source": ARMADILHA})
            self.aba.chamar("Page.navigate", {"url": self.url})
            for _ in range(90):
                time.sleep(1)
                # reserva: sem o TVa (chave de recurso do Flow), o execute público ainda é o original
                if self.aba.js("""(() => { const e = window.grecaptcha && grecaptcha.enterprise;
                    if (!window.__nsnOrig && e && typeof e.execute === 'function' && typeof e.ready === 'function'
                        && !/extension_hijack/.test(String(e.execute))) window.__nsnOrig = e.execute.bind(e);
                    return !!(window.__nsnOrig && window.WIZ_global_data); })()"""):
                    break
            else:
                raise RuntimeError(f"{self.sessao}: reCAPTCHA não carregou na aba do Flow ({self.aba.js('location.href')})")
            if "accounts.google" in (self.aba.js("location.href") or ""):
                raise RuntimeError(f"{self.sessao}: Flow pediu login")
            todos = [{k: c[k] for k in ("name", "value", "domain", "path")}
                     for c in self.aba.chamar("Network.getAllCookies")["cookies"]]
            ck = [c for c in todos if "google" in c["domain"]]
            self.f = FlowHTTP(ck, self.url.split("/project/")[1].split("?")[0])
            self.colher(ck, todos)
            return self
        except Exception:
            self.__exit__()
            raise

    def _fab(self, rota, timeout=200, **q):
        """Pedido à fábrica de tokens. Fora do ar = FabricaFora (o PC1 volta pro caminho antigo); login = FLOW_LOGIN."""
        import urllib.error
        import urllib.parse
        url = f"{self.fabrica}/{rota}?" + urllib.parse.urlencode({"perfil": self.perfil, **q})
        try:
            return json.loads(urllib.request.urlopen(url, timeout=timeout).read())
        except urllib.error.HTTPError as e:
            erro = json.loads(e.read() or b"{}").get("erro") or f"HTTP {e.code}"
            if e.code == 401:
                raise PedeLogin(erro)
            raise RuntimeError(f"fábrica: {erro}")
        except (ConnectionRefusedError, urllib.error.URLError) as e:
            if isinstance(getattr(e, "reason", e), ConnectionRefusedError) or isinstance(e, ConnectionRefusedError):
                raise ConnectionError(f"FabricaFora: {e}")
            raise RuntimeError(f"fábrica: {e}")
        except OSError as e:  # tempo esgotado etc.: a fábrica está no ar, essa conta é que demorou
            raise RuntimeError(f"fábrica demorou: {e}")

    def colher(self, cookies, todos=None):
        """Renova os cookies da saúde a cada geração, sem Chrome a mais. PC1: cookies/flow_<conta>.json (o que
        tools\\saude.py testa; 29/10 a saúde dizia "cookies vencidos" para a seebotsia porque o arquivo era de dias
        atrás, não o login). Worker: cookies/cofre_<perfil>.json no formato do colher.py (saude_flow.py lê de lá)."""
        try:
            COOKIES.mkdir(exist_ok=True)
            if self.worker:
                arq = COOKIES / f"cofre_{self.sessao}.json"
                ua = (self.aba.chamar("Browser.getVersion")["userAgent"].replace("HeadlessChrome", "Chrome")
                      if self.aba else None)
                d = {"perfil": self.sessao, "ua": ua, "quando": time.strftime("%Y-%m-%d %H:%M"), "maquina": "local",
                     "cookies": todos or cookies}
            else:
                arq = COOKIES / f"flow_{self.sessao}.json"
                d = cookies
            gravar_json(arq, d)
        except Exception as e:  # noqa: BLE001
            self.log(f"[flow] não gravei os cookies da saúde ({e})")

    def soltar_chrome(self):
        """Modo worker: o token já foi usado, o resto é HTTP — fecha a aba e o Chrome (libera a RAM do notebook)."""
        if self.aba:
            try:
                self.aba.fechar(fechar_aba=True)
            except Exception:  # noqa: BLE001
                pass
            self.aba = None
        if self.fechar_chrome:
            try:
                self.fechar_chrome()
            except Exception as e:  # noqa: BLE001
                self.log(f"[flow] não fechei o Chrome ({e})")
            self.fechar_chrome = None
        seg = round(time.time() - self.t_inicio)
        self.log(f"FLOW_CHROME_SOLTO chrome_s={seg}")
        return seg

    def __exit__(self, *_):
        try:
            if self.aba:
                self.aba.fechar(fechar_aba=True)
        except Exception:  # noqa: BLE001
            pass
        self.aba = None
        try:
            if self.abri:
                self.abri = False
                self.g.fechar_chrome(self.porta, self.log)
        finally:  # 30/10: erro ao fechar o Chrome não pode deixar a trava da porta presa (o Veo esperaria 10 min)
            if self.trava and self.trava.is_locked:
                self.trava.release()

    # ───────── token, upload, conversa ─────────

    def token(self, acao="CHAT_GENERATION"):
        if self.fabrica:
            return self._fab("token", timeout=200, acao=acao)["token"]
        if not self.aba:
            raise RuntimeError("Chrome já foi solto: não há como fabricar outro token")
        self.aba.chamar("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": random.randint(100, 1100),
                                                     "y": random.randint(100, 700)})
        try:
            t = self.aba.js(f"window.__nsnOrig(WIZ_global_data.xZbWve, {{action: '{acao}'}})", timeout=60)
        except TimeoutError:  # 28/10: 1 vez o reCAPTCHA ficou >60 s sem responder; na 2ª veio
            t = self.aba.js(f"window.__nsnOrig(WIZ_global_data.xZbWve, {{action: '{acao}'}})", timeout=90)
        if not t:
            raise RuntimeError("reCAPTCHA não devolveu token")
        return t

    def subir_imagem(self, caminho):
        """Envia uma foto para o projeto (vira referência do agente). Devolve o media_id."""
        p = Path(caminho)
        mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
        pl = [[None, 22, None, None, None, self.f.projeto, None, None, None, None, [self.token("UPLOAD_IMAGE"), 1]],
              base64.b64encode(p.read_bytes()).decode(), mime, 1, None, None, None, None, p.name, None,
              str(uuid.uuid4()).upper(), str(uuid.uuid4()).upper()]
        d = self.f.rpc("maseQ", pl)
        if d is None:
            raise Recusado(f"upload de {p.name} recusado: {self.f.ultimo_erro}")
        mid = re.search(r'"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"', json.dumps(d))
        return mid.group(1) if mid else None

    def pedir(self, texto, conversa=None, espera_s=900):
        """Uma mensagem ao agente do Flow. Devolve {conversa, ferramentas, texto, midias:[{media_id, nome, ...}]}."""
        aberto = disjuntor_aberto()
        if aberto:
            raise Recusado(f"{self.sessao}: HTTP do Flow em pausa ({aberto}) — vai direto pelo Chrome")
        try:
            res = self._pedir(texto, conversa, espera_s)
        except Recusado as e:
            if "não entregou mídia" in str(e):
                disjuntor_registrar(False)
            raise
        disjuntor_registrar(True)
        return res

    def _pedir(self, texto, conversa=None, espera_s=900):
        conversa = conversa or self.f.criar_conversa()
        if not conversa:
            raise Recusado(f"{self.sessao}: o Flow não criou a conversa ({self.f.ultimo_erro})")
        inner =[conversa, [[[[texto]]]], [f"projects/{self.f.projeto}", None, [self.token(), 1], None, None, 1]]
        t0 = time.time()
        r = self.f.s.post(CHAT, params={"bl": self.f.bl, "f.sid": self.f.sid, "hl": "en",
                                        "_reqid": str(random.randint(100000, 9999999)), "rt": "c"},
                          data={"f.req": json.dumps([None, json.dumps(inner)]), "at": self.f.at}, timeout=espera_s,
                          stream=True, headers={"X-Same-Domain": "1", "Origin": BASE, "Referer": BASE + "/",
                                                "content-type": "application/x-www-form-urlencoded;charset=utf-8",
                                                "x-client-deadline-ms": str(espera_s * 1000)})
        # 30/10: junta os bytes e decodifica 1 vez — decodificar pedaço a pedaço quebrava acento/emoji partido entre
        # dois pedaços (virava "�" no texto e no JSON das ferramentas)
        try:
            txt = b"".join(r.iter_content(chunk_size=65536)).decode("utf-8", "replace")
        finally:
            r.close()
        if r.status_code != 200 and '[["wrb.fr"' not in txt:
            raise Recusado(f"{self.sessao}: StreamChat HTTP {r.status_code}: {txt[:200]}")
        res = ler_fluxo(txt)
        res.update(conversa=conversa, segundos=round(time.time() - t0))
        vistos = {}
        for x in res["ferramentas"]:  # o bloco final repete os resultados; vídeo volta "queued" (assíncrono)
            if x.get("media_id") and x.get("status") in OK:
                vistos.setdefault(x["media_id"], x)
        res["midias"] = list(vistos.values())
        falhas = [x for x in res["ferramentas"] if x.get("status") and x.get("status") not in OK]
        self._log({"conversa": conversa, "pedido": texto[:300], "segundos": res["segundos"], "recusa": res["recusa"],
                   "midias": [m["media_id"] for m in res["midias"]], "falhas": falhas[:3], "texto": res["texto"][:300]})
        if res["recusa"]:
            raise Recusado(f"{self.sessao}: {res['recusa']}")
        if not res["midias"]:
            (ROOT / "logs").mkdir(exist_ok=True)
            (ROOT / "logs" / f"flow_sem_midia_{conversa}.txt").write_text(txt, "utf-8")
            raise Recusado(f"{self.sessao}: o agente não entregou mídia ({falhas[:1] or res['texto'][-300:]})")
        return res

    def _log(self, reg):
        LOG.parent.mkdir(exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "conta": self.sessao, **reg},
                               ensure_ascii=False) + "\n")

    def baixar(self, res, destinos, video=False, espera_s=900):
        """Espera o link assinado existir (imagem: segundos; vídeo "queued": minutos) e baixa. video=True: só aceita
        video/* (na fila o item já tem a miniatura /image/, que não serve)."""
        out = []
        for m, d in zip(res["midias"], destinos):
            fim = time.time() + espera_s
            while True:
                try:
                    arq, tipo, _ = self.f.baixar(m["media_id"], d)
                    if not video or (tipo or "").startswith("video"):
                        out.append(arq)
                        break
                    Path(arq).unlink(missing_ok=True)
                    erro = "só a miniatura por enquanto"
                except Exception as ex:  # noqa: BLE001 — 30/10: queda de rede no meio da espera (minutos) não
                    erro = f"{type(ex).__name__}: {str(ex)[:120]}"  # pode jogar fora um vídeo já pago
                    try:
                        falha = self.f.falha_geracao(m["media_id"])
                    except Exception:  # noqa: BLE001
                        falha = None
                    if falha:
                        raise Recusado(f"{m['media_id']}: {falha}")
                if time.time() > fim:
                    raise RuntimeError(f"{m['media_id']} sem o arquivo pronto depois de {espera_s} s "
                                       f"({m.get('status')}; último: {erro})")
                time.sleep(10)
        return out

    # ───────── pedidos prontos ─────────

    def imagem_beluga(self, prompt, saida, refs=(), formato="9:16", modelo="Nano Banana 2.1"):
        """12/11: o pedido NOVO da tela do Flow (capturado em capturas\\passivo_flow_20261112.jsonl, RPC ogiZ0b
        "BELUGA") — geração direta, sem o agente/StreamChat (que volta vazio desde ~11/11). Resposta síncrona: o id da
        mídia e o link flow-content da imagem. Referências: sobem pro projeto antes (maseQ), como a tela faz.
        Devolve {"arquivos": [...], "midias": [...], "segundos": n}. FLOW_BELUGA=0 = usa o caminho antigo."""
        t0 = time.time()
        for i, r in enumerate(refs or ()):
            try:
                self.subir_imagem(r)
            except Recusado as e:
                if i == 0:
                    raise
                print(f"FLOW_REF_RECUSADA {Path(r).name} ({str(e)[-60:]})", flush=True)
        texto = (f"Generate 1 still image (NOT a video) with {modelo}, aspect ratio {formato}"
                 + (", using the attached image(s) as reference" if refs else "") + f". {prompt}")
        ctx = [None, 22, None, None, None, self.f.projeto, None, None, None, None,
               [self.token(os.environ.get("FLOW_BELUGA_ACAO", "IMAGE_GENERATION")), 1]]
        # índices 4 e 14 do item: na captura (16:9) eram 3 e 4; FLOW_BELUGA_I4/I14 deixam testar o formato
        # 12/11 testado no STI: índice 4 = formato (1 = 1:1 1024², 2 = 9:16 768x1376, 3 = 16:9 1376x768, 4 = 3:4 896x1200)
        i4 = int(os.environ.get("FLOW_BELUGA_I4") or {"1:1": 1, "9:16": 2, "16:9": 3, "3:4": 4}.get(formato, 2))
        # 12/11 testado: índice 14 = 4 (como na tela com fotos anexadas) puxa mídias antigas do projeto como referência
        # (saiu um "robô amarelo" de outra geração num painel solar); 1 = só o texto (maçã limpa). Sem refs = 1.
        i14 = int(os.environ.get("FLOW_BELUGA_I14") or (4 if refs else 1))
        item = [None, None, None, random.randint(10 ** 8, 2 ** 31 - 1), i4, "BELUGA", None, ctx, [[[texto]]],
                None, None, None, str(uuid.uuid4()).upper(), str(uuid.uuid4()).upper(), i14]
        d = self.f.rpc("ogiZ0b", [None, [item], 1, ctx, [str(uuid.uuid4()).upper()]])
        if d is None:
            raise Recusado(f"{self.sessao}: BELUGA recusou ({self.f.ultimo_erro})")
        txt = json.dumps(d)
        rec = re.search(r'"(PUBLIC_ERROR_[A-Z_]+|[A-Z_]+_BLOCKED)"', txt)
        if rec:
            raise Recusado(f"{self.sessao}: {rec.group(1)}")
        mids = list(dict.fromkeys(re.findall(r'flow-content\.google/image/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                                             r'[0-9a-f]{4}-[0-9a-f]{12})', txt)))
        self._log({"via": "beluga", "pedido": texto[:300], "midias": mids, "segundos": round(time.time() - t0)})
        if not mids:
            (ROOT / "logs").mkdir(exist_ok=True)
            (ROOT / "logs" / f"flow_beluga_sem_midia_{int(time.time())}.txt").write_text(txt[:20000], "utf-8")
            raise Recusado(f"{self.sessao}: BELUGA não devolveu imagem ({txt[:200]})")
        res = {"midias": [{"media_id": m} for m in mids[:1]], "segundos": round(time.time() - t0)}
        if self.soltar_apos_pedido:
            self.soltar_chrome()
        res["arquivos"] = self.baixar(res, [Path(saida)])
        disjuntor_registrar(True)
        return res

    def imagem(self, prompt, saida, refs=(), formato="9:16", modelo="Nano Banana 2.1", quantidade=1, conversa=None):
        if quantidade == 1 and os.environ.get("FLOW_BELUGA", "1") != "0":
            return self.imagem_beluga(prompt, saida, refs=refs, formato=formato, modelo=modelo)
        # 02/11: o Flow passou a recusar o upload de algumas referências de pose/corpo ("upload recusado [3]") e a
        # imagem toda caía. Só a 1ª (a capa do parceiro = o protagonista) é obrigatória; a recusada sai e segue.
        ids = []
        for i, r in enumerate(refs):
            try:
                ids.append(self.subir_imagem(r))
            except Recusado as e:
                if i == 0:
                    raise
                print(f"FLOW_REF_RECUSADA {Path(r).name} ({str(e)[-60:]})", flush=True)
        pedido = (f"Generate {quantidade} still image{'s' if quantidade > 1 else ''} (NOT a video) with {modelo}, "
                  f"aspect ratio {formato}"
                  + (f", using the uploaded image(s) {', '.join(i for i in ids if i)} as reference" if refs else "")
                  + f". {prompt}")
        res = self.pedir(pedido, conversa)
        if self.soltar_apos_pedido:
            self.soltar_chrome()
        base = Path(saida)
        destinos = [base] + [base.with_name(f"{base.stem}_{i + 2}{base.suffix}") for i in range(quantidade - 1)]
        res["arquivos"] = self.baixar(res, destinos)
        return res

    def video(self, prompt, saida, formato="9:16", modelo="Veo 3.1 - Fast", imagem_inicial=None, imagem_final=None,
              conversa=None):
        """Texto->vídeo; com imagem_inicial = imagem->vídeo; com as duas = quadro inicial + final (antes/depois)."""
        partes = []
        if imagem_inicial:
            partes.append(f"use the uploaded image {self.subir_imagem(imagem_inicial)} as the FIRST frame")
        if imagem_final:
            partes.append(f"use the uploaded image {self.subir_imagem(imagem_final)} as the LAST frame")
        pedido = (f"Generate 1 video with {modelo}, aspect ratio {formato}" + (", " + ", ".join(partes) if partes else "")
                  + f". {prompt}")
        res = self.pedir(pedido, conversa)
        self.log(f"FLOW_PEDIDO_OK conversa={res['conversa']} segundos={res['segundos']}")
        if self.soltar_apos_pedido:
            self.soltar_chrome()
        res["arquivos"] = self.baixar(res, [Path(saida)], video=True)
        return res

    def motion(self, imagem, video_base, saida, quem="", prompt="", formato="9:16", modelo="Omni Flash", max_s=10,
               fundo="imagem", upscale=True, conversa=None):
        """MOTION SYNC (01/11, ideia do vídeo youtu.be/OoMpgOJFTCw): a pessoa da IMAGEM repete os movimentos do VÍDEO.
        IMAGEM = APARÊNCIA (rosto, cabelo, roupa, cenário); VÍDEO = SÓ MOVIMENTO (gestos, ritmo, timing).
        Por dentro é a ferramenta generate_video_edit_video do agente (case "EDIT_VIDEO" do JS: vídeo base + imagens
        de referência). O vídeo sobe pelo upload Scotty (flow_http.subir_video), cortado no servidor em max_s.
        Recusas conhecidas: erro 60 = "Editing uploaded videos isn't available in your region"; vídeo base COM ÁUDIO =
        PUBLIC_ERROR_SPEECH_EDIT / SPEECH_EDIT_BLOCKED (01/11) — por isso o vídeo sobe sem áudio e cortado em max_s.
        Vídeo parado (foto com zoom) também FALHA. CAUSA DAS 7 FALHAS DE 01/11: pedir logo após enviar o vídeo
        (o Flow ainda processa e a geração volta "state: FAILED", código 13, sem cobrar); o mesmo pedido com o vídeo
        já assentado passa (teste J). Por isso espera o link /video/ existir e MOTION_ESPERA_S desde o envio.
        quem = descrição opcional em inglês ("woman (curly red hair, green sweater)"); vazio = "person". fundo="imagem" (cenário da foto) ou "video" (cenário do vídeo).
        Custa 20 créditos (falha não cobra). O Omni devolve 720p: upscale=True leva a 1080 (regra: nada < 1080p)."""
        dur = _duracao(video_base)
        base = Path(saida).with_name(Path(saida).stem + "_base_mudo.mp4")
        # sem recodificar quando cabe (o que passou nos testes H/I foi "-an -c:v copy"); só corta recodificando
        video_args = ["-c:v", "copy"] if dur and dur <= max_s else ["-t", str(max_s), "-c:v", "libx264", "-crf", "18",
                                                                     "-pix_fmt", "yuv420p"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video_base), "-an", *video_args, str(base)],
                       check=True, timeout=300, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            vid = self.f.subir_video(base)
        finally:
            base.unlink(missing_ok=True)
        t_envio = time.time()
        img = self.subir_imagem(imagem)
        while time.time() - t_envio < max(MOTION_ESPERA_S, 30) or "/video/" not in self.f.midias([vid]).get(vid, ""):
            if time.time() - t_envio > 900:
                raise RuntimeError(f"vídeo base {vid} não ficou pronto no Flow em 15 min")
            time.sleep(10)
        self.log(f"[motion] vídeo base {vid} ({dur and round(dur, 1)} s) + imagem {img}")
        pedido = (f"Use the generate_video_edit_video tool with {modelo}, aspect ratio {formato}. Base video: {vid}. "
                  f"Reference image: {img}. " + MOTION_PROMPT.format(quem=quem or "person", fundo=MOTION_FUNDO[fundo])
                  + (f" {prompt}" if prompt else ""))
        res = self.pedir(pedido, conversa)
        res.update(video_base=vid, imagem=img)
        self.log(f"FLOW_PEDIDO_OK conversa={res['conversa']} segundos={res['segundos']}")
        if self.soltar_apos_pedido:
            self.soltar_chrome()
        res["arquivos"] = self.baixar(res, [Path(saida)], video=True)
        if upscale:
            _para_1080(Path(saida))
        return res

    def estender(self, media_id, prompt, saida, formato="9:16", modelo=None, juntar=False, espera_s=900):
        """Continua um vídeo do projeto (o último quadro vira o 1º do trecho novo; ~7 s, 20 créditos).
        O agente do chat RECUSA estender (out/2026): vai pelo RPC fZytfe montado como o case "EXTEND_VIDEO" do JS
        (capturas/flow_js_s1.js @2052241). O vídeo precisa da cena dele (workflow) nos metadados; seed vai como TEXTO
        (número dá erro [3]). Provado 29/10 na mundosolar: 1a4631c3 -> fc6cf307 (testes_flow_http/estender_comparar.png).
        juntar=True: saida = original + trecho novo (ffmpeg, sem recodificar)."""
        reg = self.f.rpc("Iyc41d", [[media_id]])
        try:
            cena = reg[0][0][0][2]
        except (TypeError, IndexError):
            raise RuntimeError(f"{media_id}: vídeo não achado no projeto ({json.dumps(reg)[:200]})")
        retrato = formato == "9:16"
        modelo = modelo or ("veo_3_1_extend_fast_portrait" if retrato else "veo_3_1_extend_fast_landscape")
        req = [[None, media_id], [None, None, [[[prompt]]]], modelo, 1 if retrato else 2, None,
               [None, cena, None, None, str(random.randint(1, 2147483646))]]
        ctx = [None, 22, None, None, None, self.f.projeto, None, None, None, None, [self.token("VIDEO_GENERATION"), 1]]
        d = self.f.rpc("fZytfe", [[req], ctx, [str(uuid.uuid4())]])
        self._log({"estender": media_id, "pedido": prompt[:300], "modelo": modelo, "recusa": self.f.ultimo_erro,
                   "resposta": json.dumps(d)[:500] if d is not None else None})
        if d is None:
            raise Recusado(f"{self.sessao}: estender {media_id} recusado: {self.f.ultimo_erro}")
        # a resposta traz a cena, um id de etapa (não é mídia) e o id do vídeo novo: fica o que vira mídia
        candidatos = list(dict.fromkeys(x for x in re.findall(
            r'"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"', json.dumps(d))
            if x not in (media_id, cena, self.f.projeto)))
        novo = None
        for _ in range(12):
            novo = next((c for c in candidatos if "Media not found" not in json.dumps(self.f.rpc("Iyc41d", [[c]]))),
                        None)
            if novo:
                break
            time.sleep(10)
        if not novo:
            raise RuntimeError(f"estender {media_id}: nenhum id da resposta virou mídia ({candidatos})")
        res = {"media_id": novo, "cena": cena, "modelo": modelo, "midias": [{"media_id": novo, "status": "queued"}]}
        if not juntar:
            res["arquivos"] = self.baixar(res, [Path(saida)], video=True, espera_s=espera_s)
            return res
        saida = Path(saida)
        a, b = saida.with_name(saida.stem + "_orig.mp4"), saida.with_name(saida.stem + "_novo.mp4")
        self.f.baixar(media_id, a)
        self.baixar(res, [b], video=True, espera_s=espera_s)
        lista = saida.with_name(saida.stem + "_lista.txt")
        lista.write_text(f"file '{a.as_posix()}'\nfile '{b.as_posix()}'\n", "utf-8")
        import subprocess
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
                        str(saida)], check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for x in (a, b, lista):
            x.unlink(missing_ok=True)
        res["arquivos"] = [saida]
        return res

    def corrigir(self, res_anterior, pedido, saida):
        """Correção na MESMA conversa ("troque o fundo por dia ensolarado"); saída .mp4 = espera vídeo."""
        res = self.pedir(pedido, res_anterior["conversa"])
        res["arquivos"] = self.baixar(res, [Path(saida)], video=Path(saida).suffix.lower() in (".mp4", ".mov"))
        return res


def _duracao(video):
    """Segundos do vídeo (ffprobe); None se não der para ler."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True, timeout=60,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return float(r.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _para_1080(video):
    """Leva o vídeo a 1080 no lado menor (lanczos), no lugar; já >= 1080 fica como está."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True, timeout=60,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    w, h = (int(x) for x in r.stdout.strip().split(",")[:2])
    if min(w, h) >= 1080:
        return
    esc = "scale=1080:-2:flags=lanczos" if w < h else "scale=-2:1080:flags=lanczos"
    tmp = video.with_name(video.stem + "_1080.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", esc, "-c:v", "libx264", "-crf", "17",
                    "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", str(tmp)], check=True, timeout=600,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    tmp.replace(video)


def _opcao(a, nome, padrao=None):
    return a[a.index(nome) + 1] if nome in a else padrao


def _texto(prompt):
    """'@arquivo' = o prompt está no arquivo (UTF-8): o cmd do ssh do PC2 estraga acento/emoji na linha de comando."""
    return Path(prompt[1:]).read_text("utf-8").strip() if prompt.startswith("@") else prompt


def fechar_chrome_local(porta):
    """Modo worker: fecha o Chrome da conta pelo chrome_conta.py desta máquina (SIGTERM = grava os cookies)."""
    cc = Path(r"C:\postador-worker\chrome_conta.py") if os.name == "nt" else Path.home() / "postador-worker" / "chrome_conta.py"
    if not cc.exists():
        raise RuntimeError(f"sem {cc}")
    subprocess.run([sys.executable, str(cc), "fechar", str(porta)], capture_output=True, timeout=120,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def baixar_sem_chrome(nome, projeto, media_id, saida, espera_s=900):
    """2ª fase (D31, 29/10): baixa um vídeo já pedido, SEM Chrome, com os cookies colhidos na 1ª fase
    (cookies/cofre_<nome>.json). A máquina fica livre entre as duas fases."""
    d = json.loads((COOKIES / f"cofre_{nome}.json").read_text("utf-8"))
    proj = projeto.split("/project/")[1].split("?")[0] if "/project/" in projeto else projeto
    f = FlowHTTP([c for c in d["cookies"] if "google" in c["domain"]], proj)
    fim = time.time() + espera_s
    while True:
        try:
            arq, tipo, _ = f.baixar(media_id, saida)
            if (tipo or "").startswith("video"):
                return Path(arq)
            Path(arq).unlink(missing_ok=True)
            erro = "só a miniatura por enquanto"
        except Exception as ex:  # noqa: BLE001 — rede caiu no meio: tenta de novo até o prazo
            erro = f"{type(ex).__name__}: {str(ex)[:120]}"
        if time.time() > fim:
            raise RuntimeError(f"{media_id} sem o arquivo pronto depois de {espera_s} s (último: {erro})")
        time.sleep(10)


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if "baixar" in a:  # --porta X --projeto P --nome N baixar <media_id> <saida>  (sem Chrome; 2ª fase)
        i = a.index("baixar")
        try:
            arq = baixar_sem_chrome(_opcao(a, "--nome"), _opcao(a, "--projeto"), a[i + 1], a[i + 2])
        except Exception as e:  # noqa: BLE001
            print(f"FLOW_ERRO {type(e).__name__}: {str(e)[:300]}")
            return 1
        print(f"FLOW_OK {arq} bytes={arq.stat().st_size}")
        return 0
    formato = _opcao(a, "--formato", "9:16")
    modelo = _opcao(a, "--modelo")
    refs = [a[i + 1] for i, x in enumerate(a) if x == "--ref"]
    porta, projeto = _opcao(a, "--porta"), _opcao(a, "--projeto")
    sem_valor = {"--fechar-chrome"}
    pos = [x for i, x in enumerate(a) if not x.startswith("--")
           and (i == 0 or not a[i - 1].startswith("--") or a[i - 1] in sem_valor)]
    fabrica = _opcao(a, "--fabrica")
    if fabrica:  # 02/11: Chrome quente da fábrica de tokens desta máquina (fabrica_tokens.py)
        tipo, prompt, saida = pos[:3]
        fabrica = fabrica if fabrica.startswith("http") else f"http://127.0.0.1:{fabrica}"
        fg = FlowGerador(_opcao(a, "--nome", "fabrica"), url=projeto, fabrica=fabrica, perfil=_opcao(a, "--perfil"))
        porta = "fabrica"
    elif porta:  # modo worker
        tipo, prompt, saida = pos[:3]
        fg = FlowGerador(_opcao(a, "--nome", f"porta{porta}"), porta=porta, url=projeto, soltar_apos_pedido="--fechar-chrome" in a,
                         fechar_chrome=(lambda: fechar_chrome_local(porta)) if "--fechar-chrome" in a else None)
    else:
        sessao, tipo = pos[:2]
        if tipo == "colher":
            with FlowGerador(sessao) as fg:
                print(f"COLHIDO {sessao} créditos={fg.f.creditos()} -> {COOKIES / ('flow_' + sessao + '.json')}")
            return 0
        prompt, saida = pos[2:4]
        fg = FlowGerador(sessao)
    prompt = _texto(prompt)
    try:
        with fg:
            if fg.aba and "accounts.google" in (fg.aba.js("location.href") or ""):
                print("FLOW_LOGIN")
                return 6
            saldo = fg.f.creditos()
            print(f"FLOW_CREDITOS saldo={saldo}")
            if saldo is not None and saldo < CREDITO_MINIMO and tipo in ("video", "motion"):
                print(f"FLOW_SEM_CREDITO saldo={saldo}")
                return 2
            if tipo == "imagem":
                res = fg.imagem(prompt, saida, refs=refs, formato=formato, **({"modelo": modelo} if modelo else {}))
            elif tipo == "motion":  # prompt = QUEM está na imagem, em inglês (ver motion())
                res = fg.motion(_opcao(a, "--imagem"), _opcao(a, "--video"), saida, quem=prompt, formato=formato,
                                fundo=_opcao(a, "--fundo", "imagem"), **({"modelo": modelo} if modelo else {}))
            elif tipo == "video-pedir":  # 1ª fase: só pede; o PC1 solta a máquina e baixa depois (baixar)
                img = _opcao(a, "--imagem-inicial")
                partes = [f"use the uploaded image {fg.subir_imagem(img)} as the FIRST frame"] if img else []
                pedido = (f"Generate 1 video with {modelo or 'Veo 3.1 - Fast'}, aspect ratio {formato}"
                          + (", " + ", ".join(partes) if partes else "") + f". {prompt}")
                res = fg.pedir(pedido)
                print(f"FLOW_PEDIDO_OK conversa={res['conversa']} segundos={res['segundos']}")
                fg.soltar_chrome()
                print("FLOW_MIDIAS " + ",".join(m["media_id"] for m in res["midias"]))
                return 0
            else:
                res = fg.video(prompt, saida, formato=formato, imagem_inicial=_opcao(a, "--imagem-inicial"),
                               imagem_final=_opcao(a, "--imagem-final"), **({"modelo": modelo} if modelo else {}))
    except Recusado as e:
        print(f"FLOW_RECUSADO {str(e)[:300]}")
        return 3
    except PedeLogin:  # fábrica: o Flow pediu login nessa conta
        print("FLOW_LOGIN")
        return 6
    except Exception as e:  # noqa: BLE001
        print(f"FLOW_ERRO {type(e).__name__}: {str(e)[:300]}")
        return 1
    arq = Path(res["arquivos"][0])
    print(f"FLOW_OK {arq} bytes={arq.stat().st_size if arq.exists() else 0}")
    if not porta:
        print(json.dumps({k: (str(v) if k == "arquivos" else v) for k, v in res.items() if k != "ferramentas"},
                         ensure_ascii=False, indent=1)[:1500])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
