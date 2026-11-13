# -*- coding: utf-8 -*-
r"""genspark_pagina.py — modo PÁGINA: fala com o ask_proxy do Genspark por fetch de DENTRO da página logada.

É o "sem robotizar a tela" (no molde do gemini_http, mas o Genspark exige token de reCAPTCHA + Cloudflare, que
só a página real satisfaz). Em vez de digitar no campo e ler o DOM (~45-60 s e vira 0 chars sob carga), aqui a
gente:
  1. abre/reaproveita o Chrome logado da conta (cofre), fica na página do Genspark (grecaptcha carregado);
  2. roda UM evaluate que: acha a site key (do script recaptcha/enterprise.js?render=...), gera o token com
     `grecaptcha.enterprise.execute` (o reCAPTCHA da PRÓPRIA página — sem solver, sem burla), faz o
     `POST /api/agent/ask_proxy` (Cloudflare satisfeito pela página) e lê o SSE até o fim;
  3. parseia o SSE (genspark_api.parse_sse) e devolve o texto.

Mantém o Chrome aberto como "hospedeiro da sessão", mas cada mensagem é uma ida-e-volta de API (segundos), não
automação de tela. Reusa a fila/cota/bloqueio do genspark.py.

Uso:
    from genspark_pagina import perguntar
    print(perguntar("Quanto é 17 x 23?"))                 # 1ª conta pronta
    print(perguntar("oi", conta="conta_exemplo"))             # conta fixa

CLI:
    python genspark_pagina.py "pergunta" [--conta conta_exemplo] [--bruto] [--descobrir]
"""
import os
import queue
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # a própria pasta (portável: desktop, v2)
sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
import genspark as gs  # noqa: E402  (fila/cota/login/driver/seletores já prontos)
import genspark_api as api  # noqa: E402

log = gs.log
PRAZO_S = int(os.environ.get("GENSPARK_PAGINA_PRAZO", "180"))      # teto da chamada fetch+SSE
ACAO = os.environ.get("GENSPARK_RECAPTCHA_ACTION") or (api.ler_recaptcha_cfg().get("action") or "ai_chat")

# ─────────────────────── JS que roda dentro da página ──────────────────────
# Recebe {payload, action, prazoMs}. Devolve {ok, status, sitekey, corpo|erro}. É assíncrono (evaluate aguarda).
_JS_PERGUNTAR = r"""
async (args) => {
  const {payload, action, prazoMs, sitekey: skArg} = args;
  // 1) site key: tenta o script já presente (?render=), senão usa a passada pelo Python
  function acharSitekeyScript() {
    const sc = [...document.querySelectorAll('script[src]')].map(s => s.src)
      .find(u => /recaptcha\/(enterprise|releases|api)\.js/.test(u) && /[?&]render=/.test(u));
    if (sc) { try { return new URL(sc).searchParams.get('render'); } catch(e){} }
    return null;
  }
  const sitekey = acharSitekeyScript() || skArg;
  if (!sitekey) return {ok:false, status:0, erro:'sem sitekey'};
  // 2) garante o enterprise.js carregado (o Genspark só o carrega ao focar o campo; aqui injetamos nós mesmos
  //    — a key é presa ao domínio genspark.ai, e estamos nele; é o reCAPTCHA da própria página, sem solver)
  if (!(window.grecaptcha && window.grecaptcha.enterprise && window.grecaptcha.enterprise.execute)) {
    await new Promise((res) => {
      try {
        if ([...document.querySelectorAll('script[src]')].some(s => /recaptcha\/enterprise\.js/.test(s.src))) { res(); return; }
        const s = document.createElement('script');
        s.src = 'https://www.google.com/recaptcha/enterprise.js?render=' + encodeURIComponent(sitekey);
        s.onload = res; s.onerror = res; document.head.appendChild(s);
      } catch(e){ res(); }
    });
    for (let i=0; i<50 && !(window.grecaptcha && window.grecaptcha.enterprise && window.grecaptcha.enterprise.execute); i++) {
      await new Promise(r => setTimeout(r, 200));
    }
  }
  if (!(window.grecaptcha && window.grecaptcha.enterprise && window.grecaptcha.enterprise.execute))
    return {ok:false, status:0, sitekey, erro:'grecaptcha.enterprise nao carregou'};
  // 3) gera o token pelo reCAPTCHA da propria pagina
  await new Promise((res) => { try { grecaptcha.enterprise.ready(res); } catch(e){ res(); } });
  let token;
  try { token = await grecaptcha.enterprise.execute(sitekey, {action}); }
  catch(e) { return {ok:false, status:0, sitekey, erro:'execute falhou: '+(e&&e.message||e)}; }
  if (!token) return {ok:false, status:0, sitekey, erro:'token vazio'};
  // 3) POST ask_proxy + leitura do SSE
  const body = Object.assign({}, payload, {g_recaptcha_token: token});
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), prazoMs);
  let r;
  try {
    let tz = 'America/Sao_Paulo';
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || tz; } catch(e){}
    r = await fetch('/api/agent/ask_proxy', {
      method:'POST', credentials:'include', signal:ctrl.signal,
      headers:{'Content-Type':'application/json', 'x-timezone': tz, 'x-ask-dedupe': '1'},
      body: JSON.stringify(body),
    });
  } catch(e) { clearTimeout(timer); return {ok:false, status:0, sitekey, erro:'fetch falhou: '+(e&&e.message||e)}; }
  if (!r.ok) {
    let t=''; try { t = await r.text(); } catch(e){}
    clearTimeout(timer);
    return {ok:false, status:r.status, sitekey, erro:(t||'').slice(0,800)};
  }
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  try {
    while (true) { const {done, value} = await reader.read(); if (done) break; buf += dec.decode(value, {stream:true}); }
  } catch(e) { clearTimeout(timer); return {ok: buf.length>0, status:r.status, sitekey, corpo:buf, erro:'stream cortado: '+(e&&e.message||e)}; }
  clearTimeout(timer);
  return {ok:true, status:r.status, sitekey, corpo:buf};
}
"""

_JS_DESCOBRIR = r"""
() => {
  const sc = [...document.querySelectorAll('script[src]')].map(s => s.src)
    .filter(u => /recaptcha/.test(u));
  const temEnt = !!(window.grecaptcha && window.grecaptcha.enterprise);
  const render = sc.map(u => { try { return new URL(u).searchParams.get('render'); } catch(e){ return null; } }).find(Boolean);
  return {scripts: sc.slice(0,8), temGrecaptchaEnterprise: temEnt, sitekeyPorScript: render || null, url: location.href};
}
"""


def _preparar_pagina(pg, prazo_s):
    """Garante a página no genspark.ai (origem do fetch + do reCAPTCHA). NÃO espera o textarea nem o grecaptcha:
    o enterprise.js é injetado na hora pelo próprio _JS_PERGUNTAR (a site key é conhecida). Só confere a origem."""
    fim = time.time() + prazo_s
    while time.time() < fim:
        u = gs._url(pg)
        if "genspark.ai" in u:
            return pg.evaluate(_JS_DESCOBRIR) or {}
        gs._ir_chat(pg)  # navega (commit) e traz pra frente
        time.sleep(1)
    return gs._url(pg)


def _perguntar_no_pg(pg, prompt, model=None):
    """Roda o fetch ask_proxy DENTRO da página pg (já na origem genspark.ai). Devolve o dict de resultado cru."""
    sitekey = api.sitekey()
    api.salvar_recaptcha_cfg(sitekey, ACAO)  # guarda p/ o modo PURO
    payload = api.corpo_pedido(prompt, model=model)
    return pg.evaluate(_JS_PERGUNTAR, {"payload": payload, "action": ACAO,
                                       "prazoMs": PRAZO_S * 1000, "sitekey": sitekey}) or {}


def _resultado(res, bruto_arq=None):
    """Interpreta o dict do _JS_PERGUNTAR: devolve o texto ou levanta SemCota/RuntimeError."""
    res = res or {}
    corpo = res.get("corpo") or ""
    if bruto_arq and corpo:
        try:
            open(bruto_arq, "w", encoding="utf-8").write(corpo)
        except Exception:  # noqa: BLE001
            pass
    if not res.get("ok"):
        erro = res.get("erro") or f"status {res.get('status')}"
        if gs._tem_paywall((corpo + " " + str(erro)).lower()):
            raise gs.SemCota("paywall do Genspark no ask_proxy")
        raise RuntimeError(f"ask_proxy: {str(erro)[:200]}")
    texto, eventos = api.parse_sse(corpo)
    tipo = api.classificar(corpo)  # aviso do Genspark (crédito acabou / sem Opus) não é resposta do modelo
    if tipo == "sem_credito":
        raise gs.SemCota("créditos do dia acabaram nesta conta (página)")
    if tipo == "sem_opus":
        raise gs.SemCota("sem Opus 5.5 no grátis nesta conta (página)")
    if not texto:
        raise RuntimeError(f"resposta vazia (eventos={len(eventos)}; use --bruto para inspecionar)")
    return texto


def _uma_pagina(apelido, prompt, model=None, bruto_arq=None):
    """FRIO: abre/reaproveita o Chrome, garante login, manda a pergunta por fetch e devolve o texto (ou levanta).
    Fecha o Chrome ao fim. Custo fixo ~11 s + ~6 s da chamada. Para o caminho rápido, veja perguntar_quente."""
    from playwright.sync_api import sync_playwright
    with gs._lock_conta(apelido):
        porta, proc = cofre.abrir(apelido, url="about:blank")
        br = None
        try:
            with sync_playwright() as pw:
                br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=45000)
                pg = gs._pagina(br.contexts[0])
                _preparar_pagina(pg, gs.ESPERA_SPA)
                if gs._sessao(pg) == "":
                    gs.marcar_logado(apelido, False, "is_login: sem sessão (visitante)")
                    raise gs.NaoLogado(f"{apelido} não está logada no Genspark")
                return _resultado(_perguntar_no_pg(pg, prompt, model=model), bruto_arq)
        finally:
            cofre.fechar(proc, br, apelido)


# ─────────────────────── modo QUENTE (página persistente) ──────────────────
# Mantém o Chrome+página vivos por conta: o custo fixo (~11 s) é pago 1 vez e cada mensagem vira só a chamada de
# API (~6 s), como o argon. Cada conta tem um WORKER (thread dona dos objetos do Playwright — a API sync não é
# thread-safe; as threads do servidor só enfileiram jobs). Evicta por ociosidade (RAM!) e por limite de quentes.
_WORKERS = {}                      # conta -> _Worker
_WORKERS_LOCK = threading.Lock()
MAX_QUENTES = int(os.environ.get("GENSPARK_QUENTES", "2"))                 # quantas páginas quentes ao mesmo tempo (RAM!)
OCIO_MIN = int(os.environ.get("GENSPARK_QUENTE_OCIO_MIN", "20"))           # fecha a página quente após tanto ócio


class _Worker(threading.Thread):
    def __init__(self, conta):
        super().__init__(daemon=True, name=f"gs-quente-{conta}")
        self.conta = conta
        self.fila = queue.Queue()
        self.pronto = threading.Event()
        self.erro_init = None
        self.ultimo = time.time()
        self._parar = False

    def run(self):
        from playwright.sync_api import sync_playwright
        porta = proc = br = pw = None
        try:
            porta, proc = cofre.abrir(self.conta, url="about:blank")
            pw = sync_playwright().start()
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=45000)
            pg = gs._pagina(br.contexts[0])
            _preparar_pagina(pg, gs.ESPERA_SPA)
            if gs._sessao(pg) == "":
                gs.marcar_logado(self.conta, False, "is_login: sem sessão (visitante)")
                raise gs.NaoLogado(f"{self.conta} não está logada no Genspark")
            self.pronto.set()
            while not self._parar:
                try:
                    job = self.fila.get(timeout=30)
                except queue.Empty:
                    if time.time() - self.ultimo > OCIO_MIN * 60:
                        log.info("quente %s: ocioso %d min, encerro (libera RAM)", self.conta, OCIO_MIN)
                        break
                    continue
                if job is None:
                    break
                prompt, model, caixa, ev = job
                try:
                    caixa["res"] = _perguntar_no_pg(pg, prompt, model=model)
                except Exception as e:  # noqa: BLE001
                    caixa["exc"] = e
                finally:
                    self.ultimo = time.time()
                    ev.set()
        except Exception as e:  # noqa: BLE001
            self.erro_init = e
            self.pronto.set()
        finally:
            try:
                cofre.fechar(proc, br, self.conta)
            except Exception:  # noqa: BLE001
                pass
            try:
                if pw:
                    pw.stop()
            except Exception:  # noqa: BLE001
                pass
            with _WORKERS_LOCK:
                if _WORKERS.get(self.conta) is self:
                    del _WORKERS[self.conta]

    def perguntar(self, prompt, model=None, prazo=None):
        caixa, ev = {}, threading.Event()
        self.fila.put((prompt, model, caixa, ev))
        if not ev.wait(timeout=(prazo or PRAZO_S) + 30):
            raise RuntimeError(f"worker quente {self.conta} não respondeu a tempo")
        if "exc" in caixa:
            raise caixa["exc"]
        return caixa.get("res") or {}

    def parar(self):
        self._parar = True
        self.fila.put(None)


def _worker(conta):
    """Worker quente da conta (cria sob demanda; evicta o mais ocioso se passar de MAX_QUENTES)."""
    with _WORKERS_LOCK:
        w = _WORKERS.get(conta)
        if w and w.is_alive():
            return w
        vivos = [x for x in _WORKERS.values() if x.is_alive()]
        if len(vivos) >= MAX_QUENTES:
            lru = min(vivos, key=lambda x: x.ultimo)
            log.info("quente: limite %d atingido, encerro o mais ocioso (%s)", MAX_QUENTES, lru.conta)
            lru.parar()
        w = _Worker(conta)
        _WORKERS[conta] = w
        w.start()
    if not w.pronto.wait(timeout=gs.ESPERA_SPA + 25):
        raise RuntimeError(f"worker quente {conta} não ficou pronto")
    if w.erro_init:
        raise w.erro_init
    return w


def perguntar_quente(prompt, conta=None, tentativas=6, model=None):
    """Como perguntar(), mas com página PERSISTENTE por conta (rápido, ~6 s/msg). Ideal pro servidor/VS Code.
    Usa a 1ª conta pronta da fila (ou conta fixa). Devolve o texto ou None."""
    erros, ignorar, erro_final = 0, set(), None
    while erros < tentativas:
        try:
            apelido = conta or gs.proxima_conta(ignorar)
        except RuntimeError as e:
            log.warning("sem conta pronta no Genspark (quente): %s", e)
            return None
        t0 = time.time()
        try:
            res = _worker(apelido).perguntar(prompt, model=model)
            resp = _resultado(res)
            if resp and resp.strip():
                gs.marcar_uso(apelido, sucesso=True, segundos=time.time() - t0)
                log.info("OK(quente) %s %.1fs %d chars", apelido, time.time() - t0, len(resp))
                return resp
            gs.marcar_uso(apelido, sucesso=False, erro_msg="resposta vazia")
            erro_final = "resposta vazia"
            erros += 1
        except gs.SemCota as e:
            log.warning("%s: %s — próxima conta", apelido, e)
            gs.marcar_sem_cota(apelido)
            ignorar.add(apelido)
            erro_final = str(e)
            if conta:
                break
        except gs.NaoLogado as e:
            log.warning("%s: %s", apelido, e)
            ignorar.add(apelido)
            erro_final = str(e)
            if conta:
                break
        except Exception as e:  # noqa: BLE001
            log.error("%s(quente): %s", apelido, str(e)[:150])
            gs.marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            ignorar.add(apelido)
            erro_final = str(e)
            erros += 1
            if conta:
                break
        finally:
            if not conta:
                gs.soltar(apelido)
    log.error("Todas as tentativas falharam (quente): %s", erro_final)
    return None


def perguntar(prompt, conta=None, tentativas=6, model=None, bruto_arq=None):
    """Igual ao genspark.perguntar, mas pelo ask_proxy (modo PÁGINA, FRIO: abre e fecha o Chrome por chamada).
    1ª conta pronta da fila (ou conta fixa). Devolve o texto, ou None se todas falharem."""
    erros, ignorar, erro_final = 0, set(), None
    while erros < tentativas:
        try:
            apelido = conta or gs.proxima_conta(ignorar)
        except RuntimeError as e:
            log.warning("sem conta pronta no Genspark (página): %s", e)
            return None
        t0 = time.time()
        try:
            resp = _uma_pagina(apelido, prompt, model=model, bruto_arq=bruto_arq)
            if resp and resp.strip():
                gs.marcar_uso(apelido, sucesso=True, segundos=time.time() - t0)
                log.info("OK(página) %s %.1fs %d chars", apelido, time.time() - t0, len(resp))
                return resp
            gs.marcar_uso(apelido, sucesso=False, erro_msg="resposta vazia")
            erro_final = "resposta vazia"
            erros += 1
        except gs.SemCota as e:
            log.warning("%s: %s — próxima conta", apelido, e)
            gs.marcar_sem_cota(apelido)
            ignorar.add(apelido)
            erro_final = str(e)
            if conta:
                break
        except gs.NaoLogado as e:
            log.warning("%s: %s", apelido, e)
            ignorar.add(apelido)
            erro_final = str(e)
            if conta:
                break
        except Exception as e:  # noqa: BLE001
            log.error("%s(página): %s", apelido, str(e)[:150])
            gs.marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            ignorar.add(apelido)
            erro_final = str(e)
            erros += 1
            if conta:
                break
        finally:
            if not conta:
                gs.soltar(apelido)
    log.error("Todas as tentativas falharam (página): %s", erro_final)
    return None


def _descobrir(conta):
    """Abre a conta e imprime o que a página mostra do reCAPTCHA (site key, grecaptcha, scripts)."""
    from playwright.sync_api import sync_playwright
    porta, proc = cofre.abrir(conta, url="about:blank")
    br = None
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=45000)
            pg = gs._pagina(br.contexts[0])
            info = _preparar_pagina(pg, gs.ESPERA_SPA)
            import json as _j
            print(_j.dumps(info, ensure_ascii=False, indent=1) if isinstance(info, dict) else str(info))
            print("is_login:", gs._sessao(pg))
            if info.get("sitekeyPorScript"):
                api.salvar_recaptcha_cfg(info["sitekeyPorScript"], ACAO)
                print("Salvo em", api.RECAPTCHA_CFG)
    finally:
        cofre.fechar(proc, br, conta)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Genspark pelo ask_proxy (modo PÁGINA, sem robotizar a tela)")
    p.add_argument("pergunta", nargs="*")
    p.add_argument("--conta")
    p.add_argument("--bruto", action="store_true", help="salva o SSE cru em captura/ask_proxy_bruto.txt")
    p.add_argument("--descobrir", action="store_true", help="só investiga o reCAPTCHA da página")
    p.add_argument("--quente", action="store_true", help="usa a página persistente (rápido); repete p/ cada pergunta separada por ' || '")
    a = p.parse_args()
    if a.descobrir:
        _descobrir(a.conta or "conta_exemplo")
        return
    if not a.pergunta:
        p.print_help()
        return
    pergunta = " ".join(a.pergunta)
    if a.quente:
        # permite várias perguntas numa linha (separadas por ' || ') para medir o ganho da página quente
        for q in [x.strip() for x in pergunta.split("||") if x.strip()]:
            t0 = time.time()
            r = perguntar_quente(q, conta=a.conta)
            print(f">> {q}\n{r}\n[{time.time()-t0:.1f}s]\n", flush=True)
        return
    bruto = str(api.BASE / "captura" / "ask_proxy_bruto.txt") if a.bruto else None
    t0 = time.time()
    r = perguntar(pergunta, conta=a.conta, bruto_arq=bruto)
    if r:
        print(r)
        print(f"\n[{time.time()-t0:.1f}s]", file=sys.stderr)
    else:
        print("ERRO: sem resposta", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
