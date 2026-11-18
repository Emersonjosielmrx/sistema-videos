"""fish_http.py — Fish Audio por HTTP puro (sem navegador no caminho da geração), no molde do gemini-argo e do
projeto-navegador-sem-navegador. Prova em 18/11/2026: POST /task com stream devolve o MP3 direto em ~4,6 s.

COMO FUNCIONA (igual ao Flow):
- O Chrome entra SÓ como "fábrica de token": aberto uma vez na página da voz, pela ponte do IP da conta, ele
  (a) dá o `token` Bearer e o `workspace` do localStorage e (b) fabrica o reCAPTCHA Enterprise por pedido
  (grecaptcha.enterprise.execute, ~0,4 s). A API do Fish exige "reCAPTCHA Enterprise" no POST /task — sem token dá
  400 (medido). O siteKey é 6LfR4RwqAAAAAEvptRw9zohw7HeDU6NCqtAnJk1i.
- A GERAÇÃO é HTTP puro (curl_cffi impersonate=chrome) pela ponte do IP fixo da conta (nunca a casa), com o Bearer.
  POST https://api.fish.audio/task  {type:tts, stream:true, model, parameters:{text,...}, recaptcha:<token>} -> MP3.
- Leitura de saldo é HTTP puro, sem token: GET /wallet/<workspace>/package -> {total, balance}.

Regras herdadas do COMO_OPERAR.md: conta nunca do Kaggle (checar_conta recusa); conta tem de estar no pool do Fish
(fish_proxy = rnprmtfo-N); 1 crédito por caractere; sem rodízio de contas grátis para somar cota.

    from fish_http import FishHTTP
    f = FishHTTP(email)           # sobe a ponte do IP e o Chrome quente da conta
    f.saldo()                     # (restantes, total) — HTTP puro
    f.gerar("Uma fala.", "saida.mp3")
    f.fechar()                    # fecha o Chrome quente

CLI:
    python fish_http.py "Primeira fala." "Segunda fala." -o PASTA
    python fish_http.py -f roteiro.txt -o PASTA --voz <id> --conta <email>
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import fish_audio as fa  # reusa dividir(), checar_conta(), _subir_ponte(), CONTA_PADRAO, VOZ_PADRAO, MAX_CHARS

SITEKEY = "6LfR4RwqAAAAAEvptRw9zohw7HeDU6NCqtAnJk1i"
API = "https://api.fish.audio"
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"

# JS que fabrica um token reCAPTCHA Enterprise novo (um por geração; o token vale uma vez)
_JS_TOKEN = """([sk, action]) => new Promise((res, rej) => {
    const g = (window.grecaptcha && window.grecaptcha.enterprise) || window.grecaptcha;
    if (!g || !g.execute) return rej('sem grecaptcha');
    g.ready(() => g.execute(sk, {action}).then(res).catch(e => rej(String(e))));
})"""

# lê token Bearer e workspace do localStorage da página logada
_JS_SESSAO = """() => ({token: localStorage.getItem('token'),
                        workspace: localStorage.getItem('active_workspace_id') || localStorage.getItem('active_team_id')})"""


class SemCredito(RuntimeError):
    pass


class PrecisaLogin(RuntimeError):
    pass


class FishHTTP:
    def __init__(self, email=None, voz=None):
        self.email = (email or fa.CONTA_PADRAO).lower()
        self.voz = voz or fa.VOZ_PADRAO
        _, self.ip_n = fa.checar_conta(self.email)            # recusa Kaggle / fora do pool
        self.porta_proxy = fa._subir_ponte(self.ip_n)         # saída fixa do IP da conta
        self._proxy = f"http://127.0.0.1:{self.porta_proxy}"
        self._pw = self._br = self._pg = self._proc = None
        self.token = self.workspace = None
        from curl_cffi import requests as creq
        self.s = creq.Session(impersonate="chrome",
                              proxies={"http": self._proxy, "https": self._proxy})
        self.s.headers.update({"Origin": "https://fish.audio", "Referer": "https://fish.audio/",
                               "Content-Type": "application/json"})
        self._abrir_chrome()

    # ---------- Chrome quente (fábrica de token + sessão) ----------
    def _abrir_chrome(self):
        import cofre
        self._cofre = cofre
        self.porta, self._proc = cofre.abrir(self.email, extra=(f"--proxy-server=127.0.0.1:{self.porta_proxy}",))
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._br = self._pw.chromium.connect_over_cdp(f"http://127.0.0.1:{self.porta}")
        ctx = self._br.contexts[0]
        pg = next((x for x in ctx.pages if "fish.audio" in x.url), None)
        if pg is None:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        self._pg = pg
        # SEMPRE na página da voz: o reCAPTCHA Enterprise só é carregado na rota text-to-speech (na billing não há).
        if "text-to-speech" not in pg.url or "/auth" in pg.url:
            pg.goto(f"https://fish.audio/pt/app/text-to-speech/?modelId={self.voz}",
                    wait_until="domcontentloaded", timeout=90000)
            time.sleep(6)
        if "/auth" in pg.url or "Iniciar sessão" in (pg.inner_text("body")[:3000]):
            raise PrecisaLogin(f"{self.email} deslogada no Fish — logar pelo cofre (COMO_OPERAR.md, passo 1)")
        ses = pg.evaluate(_JS_SESSAO)
        self.token = ses.get("token")
        self.workspace = ses.get("workspace")
        if not self.token:
            raise PrecisaLogin(f"{self.email}: sem token de sessão (deslogada?)")
        self.s.headers["Authorization"] = f"Bearer {self.token}"
        self._esperar_grecaptcha()

    def _esperar_grecaptcha(self, prazo=30):
        """O grecaptcha.enterprise carrega de forma assíncrona depois da página. Espera ficar pronto."""
        fim = time.time() + prazo
        while time.time() < fim:
            pronto = self._pg.evaluate("() => { const g=(window.grecaptcha&&window.grecaptcha.enterprise)||"
                                       "window.grecaptcha; return !!(g && g.execute); }")
            if pronto:
                return True
            time.sleep(1)
        raise RuntimeError(f"{self.email}: grecaptcha Enterprise não carregou em {prazo}s na página da voz")

    def _token_recaptcha(self, action="tts"):
        return self._pg.evaluate(_JS_TOKEN, [SITEKEY, action])

    # ---------- HTTP puro ----------
    def saldo(self):
        """(restantes, total) — HTTP puro, sem gastar nada."""
        if not self.workspace:
            return None
        r = self.s.get(f"{API}/wallet/{self.workspace}/package", timeout=30)
        if r.status_code != 200:
            return None
        d = r.json()
        return d.get("balance"), d.get("total")

    def gerar(self, texto, destino):
        """Gera UMA fala (até ~500 chars no grátis) e grava o MP3 em `destino`. Devolve os bytes."""
        tok = self._token_recaptcha()
        body = {"type": "tts", "stream": True, "model": self.voz, "latency": "balanced",
                "parameters": {"text": texto, "model_id": self.voz, "format": "mp3", "latency": "balanced",
                               "backend": "drama-3", "normalize": False},
                "recaptcha": tok, "format": "mp3", "backend": "drama-3"}
        r = self.s.post(f"{API}/task", json=body, timeout=120)
        ct = r.headers.get("content-type", "")
        if r.status_code == 402 or (r.status_code == 400 and "credit" in r.text.lower()):
            raise SemCredito(f"{self.email}: sem crédito ({r.text[:120]})")
        if r.status_code != 200 or not ("audio" in ct or "octet" in ct or len(r.content) > 5000):
            raise RuntimeError(f"POST /task {r.status_code} {ct}: {r.text[:200]}")
        Path(destino).write_bytes(r.content)
        return r.content

    def fechar(self):
        for f in (lambda: self._pw and self._pw.stop(),
                  lambda: self._cofre.fechar(self._proc, nome=self.email)):
            try:
                f()
            except Exception:  # noqa: BLE001
                pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()


def gerar_roteiro(falas, saida, email=None, voz=None, juntar=True):
    """Gera uma lista de falas (corta as longas em frases) e devolve o relatório. Áudios em saida/fala_NN.mp3."""
    import creditos
    pedacos = [p for f in falas for p in fa.dividir(f)]
    if not pedacos:
        raise SystemExit("nenhuma fala")
    out = Path(saida)
    out.mkdir(parents=True, exist_ok=True)
    rel = {"conta": (email or fa.CONTA_PADRAO).lower(), "voz": voz or fa.VOZ_PADRAO, "falas": []}
    f = FishHTTP(email, voz)
    rel["conta"] = f.email
    try:
        sal = f.saldo()
        print(f"conta {f.email} | IP N={f.ip_n} | saldo {sal}", flush=True)
        for i, txt in enumerate(pedacos):
            destino = out / f"fala_{i:02d}.mp3"
            t0 = time.time()
            ok, erro = False, None
            try:
                f.gerar(txt, destino)
                ok = True
                creditos.gastar(f.email, len(txt))
            except SemCredito as e:
                erro = str(e)
                print("PAROU:", erro, flush=True)
                rel["falas"].append({"i": i, "texto": txt, "chars": len(txt), "ok": False, "erro": erro})
                break
            except Exception as e:  # noqa: BLE001
                erro = str(e)[:200]
            dt = round(time.time() - t0, 1)
            rel["falas"].append({"i": i, "texto": txt, "chars": len(txt), "gerar_s": dt, "ok": ok, "erro": erro})
            print(f"fala {i}: {'OK' if ok else 'FALHOU'} em {dt}s | {txt[:60]}", flush=True)
    finally:
        f.fechar()
        (out / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")

    partes = sorted(out.glob("fala_[0-9][0-9].mp3"))
    if juntar and partes:
        lista = out / "_lista.txt"
        lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                        "-af", "apad=pad_dur=0.25", str(out / "fish_tudo.mp3")], check=False)
        lista.unlink()
    ok = [x for x in rel["falas"] if x["ok"]]
    print(f"PRONTO: {len(ok)}/{len(pedacos)} falas em {out}", flush=True)
    return rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("falas", nargs="*")
    ap.add_argument("-f", "--arquivo")
    ap.add_argument("-o", "--saida", required=True)
    ap.add_argument("--voz", default=fa.VOZ_PADRAO)
    ap.add_argument("--conta", default=fa.CONTA_PADRAO)
    a = ap.parse_args()
    falas = list(a.falas)
    if a.arquivo:
        falas += [l.strip() for l in Path(a.arquivo).read_text(encoding="utf-8").splitlines() if l.strip()]
    gerar_roteiro(falas, a.saida, email=a.conta, voz=a.voz)


if __name__ == "__main__":
    main()
