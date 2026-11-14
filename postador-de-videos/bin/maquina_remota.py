"""maquina_remota.py — posta usando o Chrome dos NOTEBOOKS (X200MA e Acer), comandado daqui (dono, 22/10/2026: "usa o
X200MA pra postagens, pouca CPU, mais navegador"; "os 2 de uma vez: se precisar do outro já usamos, ou dividimos").

Nos notebooks só roda o Chrome da conta (~/postador-worker/chrome_conta.py, 1 conta por vez em cada um). Tudo que
decide (o que postar, limites, horário, ledger, avisos) continua NESTE PC: youtube_web_poster.py / postar_tiktok_auto.py
ligam no Chrome de lá por túnel ssh e mandam o vídeo pelo mesmo ssh. Canal/conta ativado nos dois: usa o que estiver
LIVRE; os dois ocupados (ou fora do ar) = posta por este PC como antes. Passo a passo pra dona: docs\\NETBOOKS_POSTAGEM.md

PERFIL = a parte do e-mail antes do @ (o mesmo nome do cofre). Um login serve pro YouTube e pro TikTok desse e-mail.

    python bin\\maquina_remota.py estado                   # os 2 notebooks: Chrome aberto, perfis, RAM livre
    python bin\\maquina_remota.py contas                   # todos os e-mails: onde já está logado e ativo
    python bin\\maquina_remota.py proxima                  # o próximo e-mail a logar
    python bin\\maquina_remota.py logar <perfil>           # abre o Chrome desse perfil NA TELA dos 2 notebooks
    python bin\\maquina_remota.py ativar <perfil>          # confere o login nos 2 e liga o que estiver logado
    python bin\\maquina_remota.py desativar <perfil>       # volta a postar só por este PC
    python bin\\maquina_remota.py checar <perfil> [maquina]
    python bin\\maquina_remota.py instalar                 # copia/atualiza o chrome_conta.py nos notebooks
    python bin\\maquina_remota.py instalar-nsn [maq]       # atualiza o nsn_worker (Reel + Flow por HTTP) nas máquinas
    python bin\\maquina_remota.py colher-flow <perfil> [maq]  # cookies Google do perfil p/ a saúde do Flow HTTP (lá)
    python bin\\maquina_remota.py saude-flow [maq]         # quem está logado no Flow em cada máquina (HTTP, sem Chrome)
    python bin\\maquina_remota.py preparar-chrome acer --dona-autorizou   # instala o Chrome sem sudo (baixa do Google)
"""
import json
import os
import re
import shlex
import socket
import subprocess
import tempfile
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
SEM_JANELA = 0x08000000
BIN = Path(__file__).resolve().parent
ROOT = BIN.parent
# ordem = preferência (o X200MA primeiro: o Acer é o telão principal e é mais fraco)
MAQUINAS = {"x200ma": {"ssh": "emerson@100.87.195.108", "porta": 9460,
                       "porta_ssh": 2222},  # 24/10: a 22 virou Tailscale SSH (pede login no navegador); a 2222 é o sshd
            "acer": {"ssh": "emerson-ia@100.98.55.125", "porta": 9460, "lento": True},  # Atom: Studio estoura o tempo
            # i5, 16 GB (12/11 conferido: 15,9 GB), Mint Xfce — 2ª faixa: Veo/Flow em paralelo ao login de TikTok
            "sti": {"ssh": "emerson-sti-st@100.98.49.0", "porta": 9460, "faixa_extra": 9461},
            # 13/11 dona ("adicione no sistema o HP Pavilion; abre as contas pra eu ir logando"): AMD Turion II N530
            # (2 núcleos, 2010), 8 GB, Mint 22.3, Chrome instalado. Lento (render 8x mais lento que o PC1): "lento"
            # como o Acer — Studio com mais tempo.
            "hp": {"ssh": "emerson-hp-pavili@100.123.69.41", "porta": 9460, "lento": True},
            # 14/11 dona: netbook Asus Eee PC 1015BX (AMD C-60, 1,5 GB) — só navegador (render não aguentou); login das
            # contas só depois das 8h (dona). "lento" como o Acer.
            "asus": {"ssh": "emerson-asus-eepc@100.122.115.57", "porta": 9460, "lento": True},
            # 23/10 (dona): o DESKTOP também posta, só quando NÃO está gravando (OBS) nem em chamada (mic/câmera) —
            # quem confere é o chrome_conta.py de lá ("OCUPADO gravando"); entra na conta só depois do `ativar`
            # 30/10 (D39): puxar_http = arquivos vão/voltam por HTTP temporário do PC1 (o sshd do desktop derruba scp)
            "desktop": {"ssh": "desktop", "porta": 9460, "win": True, "puxar_http": True},
            # 23/10 (dona): o PC2 também, "deixe pronto pra quando eu for logar" — sem conta ativada não recebe nada
            # (as tentativas só passam por máquina ativada na conta). Ele renderiza o anime: fica atrás dos notebooks.
            "pc2": {"ssh": "pc2", "porta": 9460, "win": True, "lento": True,
                    # 26/10: no ssh do PC2 não há "python" no PATH e o usuário do ssh não enxerga o AppData do
                    # Python313 da tela; o do pgAdmin é 3.13 e basta (o chrome_conta só usa biblioteca padrão)
                    "python": r'"C:\Program Files\PostgreSQL\16\pgAdmin 4\python\python.exe"'}}
SCRIPT_WIN = r"C:\postador-worker\chrome_conta.py"
# 04/11: máquinas onde o chrome_conta.py NOVO (--proxy-n) ainda não foi instalado — nada de Chrome pelo proxy lá. O PC2
# é do hipercool (dona: não mexer nos workers de lá) até ela liberar.
SEM_PROXY_REMOTO = {"pc2"}
# dona 27/10; o PC1 é sempre o último (None). 28/10 (dona): desktop = a máquina MAIS LIVRE -> primeiro (nos horários
# da câmera, maquinas.AGENDA_CAMERA, o maquina_livre já tira ele)
ORDEM_NAVEGADOR = {"desktop": -1, "x200ma": 0, "acer": 1, "sti": 1, "hp": 1, "asus": 1, "pc2": 2}
SCRIPT = "~/postador-worker/chrome_conta.py"
LOG = ROOT / "logs" / "maquina_remota.log"
LOGINS = ROOT / "config" / "netbooks_logins.json"
CHROME_DEB = "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"


def _q(s, win=False):
    """Aspas pro shell remoto. Windows: aspas DUPLAS (o ssh do PC2 cai no cmd, que não entende as simples do
    shlex.quote — URL com ? ou & quebrava; no desktop, PowerShell, as duplas também valem)."""
    return '"' + str(s).replace('"', '') + '"' if win else shlex.quote(str(s))


def log(m):
    linha = f"[{time.strftime('%d/%m %H:%M:%S')}] {m}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


PC1_TAILSCALE = "100.118.234.102"  # as máquinas puxam/sobem arquivos daqui (_HttpTemp)


class _HttpTemp:
    """Servidor HTTP temporário na Tailscale do PC1, só com a pasta `pasta` (30/10, D39: o sshd do desktop derruba scp
    e comando grande; comando curto passa). Porta escolhida pelo sistema; aceita_put = recebe o arquivo de volta."""

    def __init__(self, pasta, aceita_put=False):
        import functools
        import http.server
        import socketserver
        import threading
        pasta = Path(pasta)

        class H(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a):  # sob pythonw não há stderr
                pass

            def do_PUT(self):
                if not aceita_put:
                    self.send_error(403)
                    return
                nome = "".join(c if c.isalnum() or c in "._-" else "_" for c in Path(self.path).name) or "volta.bin"
                resto = int(self.headers.get("Content-Length") or 0)
                with open(pasta / nome, "wb") as f:
                    while resto > 0:
                        b = self.rfile.read(min(resto, 1 << 20))
                        if not b:
                            break
                        f.write(b)
                        resto -= len(b)
                self.send_response(201)
                self.send_header("Content-Length", "0")
                self.end_headers()

        socketserver.TCPServer.allow_reuse_address = True
        self.srv = socketserver.ThreadingTCPServer((PC1_TAILSCALE, 0), functools.partial(H, directory=str(pasta)))
        self.url = f"http://{PC1_TAILSCALE}:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def fechar(self):
        self.srv.shutdown()
        self.srv.server_close()


_KAGGLE_CACHE = {"t": 0, "nomes": set()}


def conta_kaggle_viva(perfil):
    """12/11 (3º banimento: animescomia — conta do Kaggle com IP fixo rnprmtfo-49, mas o Chrome dela abria todo dia no
    pc2/x200ma/desktop/sti/acer pela internet de casa: Flow, YouTube, TikTok). Conta Google VIVA do pool do Kaggle (ou
    reservada no cofre com kaggle_proxy) nunca abre Chrome nas máquinas remotas sem proxy. CHROME_REMOTO_KAGGLE=1 desliga."""
    if os.environ.get("CHROME_REMOTO_KAGGLE") == "1":
        return False
    if time.time() - _KAGGLE_CACHE["t"] > 120:
        nomes = set()
        try:
            pool = json.loads(Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json").read_text(encoding="utf-8"))
            for c in pool.get("contas", []):
                if not c.get("banida") and c.get("ativa", True) is not False:
                    nomes |= {str(c.get("cofre") or "").split("@")[0].lower(), str(c.get("username") or "").lower()}
            reg = json.loads(Path(r"D:\logins-google\cofre\contas.json").read_text(encoding="utf-8")).get("contas", {})
            nomes |= {e.split("@")[0].lower() for e, d in reg.items() if isinstance(d, dict) and d.get("kaggle_proxy")}
        except (OSError, ValueError):
            pass
        nomes.discard("")
        _KAGGLE_CACHE.update(t=time.time(), nomes=nomes)
    p = str(perfil or "").replace("\\", "/").rstrip("/").split("/")[-1].split("@")[0].lower()
    return p in _KAGGLE_CACHE["nomes"]


class Remoto:
    """Chrome de uma conta num notebook, visto daqui como http://127.0.0.1:<porta_local>."""

    def __init__(self, nome="x200ma"):
        self.nome = nome
        self.alvo = MAQUINAS[nome]["ssh"]
        self.porta = MAQUINAS[nome]["porta"]
        self.win = bool(MAQUINAS[nome].get("win"))
        self.run = f"{MAQUINAS[nome].get('python', 'python')} {SCRIPT_WIN}" if self.win else f"python3 {SCRIPT}"
        self.tunel = None
        self.porta_local = None
        self.home = None
        self.aberto = False
        self.aberto_em = None  # quando o Chrome de lá ficou pronto (mede o tempo de Chrome aberto no Flow HTTP)
        p = MAQUINAS[nome].get("porta_ssh")
        self.opts = ["-o", f"Port={p}"] if p else []

    def _ssh(self, comando, entrada=None, timeout=60):
        args = [SSH, "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=15",
                "-o", "ServerAliveCountMax=8",  # 24/10: x200ma abrindo Chrome fica >45 s sem responder e o SSH caía
                *self.opts, self.alvo,
                comando]
        if hasattr(entrada, "read"):
            return subprocess.run(args, stdin=entrada, capture_output=True, timeout=timeout, creationflags=SEM_JANELA)
        return subprocess.run(args, input=entrada, capture_output=True, timeout=timeout, creationflags=SEM_JANELA)

    @staticmethod
    def _txt(r):
        return ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")

    def vivo(self):
        try:
            # powershell explícito: o ssh do PC2 cai no cmd, que não entende o if do PowerShell
            teste = (f'powershell -NoProfile -Command "if (Test-Path {SCRIPT_WIN}) {{ \'OK\' }}"' if self.win
                     else f"test -f {SCRIPT} && echo OK")
            return b"OK" in (self._ssh(teste, timeout=25).stdout or b"")
        except subprocess.TimeoutExpired:
            return False

    def _abrir_tunel_proxy(self, n):
        """04/11 (dona: TikTok das máquinas pelo proxy da conta, nunca 2 contas no IP de casa): túnel SSH REVERSO — lá,
        127.0.0.1:18200 (PAC) e 127.0.0.1:18200+n (IP Webshare n) chegam no proxy_tiktok DESTE PC. O chrome_conta de lá
        confere que os dois respondem antes de abrir; sem eles, recusa."""
        self.tunel_proxy = subprocess.Popen(
            [SSH, "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "-o", "ServerAliveInterval=15", "-N",
             "-R", "18200:127.0.0.1:18200", "-R", f"{18200 + int(n)}:127.0.0.1:{18200 + int(n)}", *self.opts, self.alvo],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=SEM_JANELA)
        time.sleep(4)  # o ssh sobe e registra os encaminhamentos lá

    def abrir(self, perfil, url="about:blank", comando="abrir", sem_espera=False, espera_s=960, tunel=True, proxy_n=None):
        if conta_kaggle_viva(perfil):  # com proxy_n também: o Webshare N é OUTRO IP, não o rnprmtfo fixo do Kaggle
            raise RuntimeError(f"{self.nome}: {perfil} é conta VIVA do Kaggle — não abre Chrome fora do IP fixo dela "
                               "(3º banimento 12/11: animescomia). Só no PC1 pela ponte rnprmtfo dela.")
        return self._abrir(perfil, url, comando, sem_espera, espera_s, tunel, proxy_n)

    def _abrir(self, perfil, url="about:blank", comando="abrir", sem_espera=False, espera_s=960, tunel=True, proxy_n=None):
        """Abre o Chrome do perfil lá e o túnel aqui. Devolve a porta LOCAL (use como se o Chrome fosse deste PC).
        tunel=False (30/10, D38): só o Chrome lá, para quem roda NA máquina (colher.py, worker do nsn) — o túnel era um
        ssh a mais que caía no desktop e deixava o Chrome aberto ("túnel até o Chrome não abriu", 03:43). Devolve None.
        proxy_n (04/11): o Chrome de lá sai pelo IP Webshare n desta conta (túnel reverso). Sem a confirmação PROXY_OK
        de lá (script velho, túnel fora) = fecha e falha — nunca posta pelo IP de casa."""
        extra = " --sem-espera" if sem_espera else ""
        if proxy_n is not None:
            self._abrir_tunel_proxy(proxy_n)
            extra += f" --proxy-n={int(proxy_n)}"
        r = self._ssh(f"{self.run} {comando} {_q(perfil, self.win)} {self.porta} {_q(url, self.win)}{extra}",
                      timeout=espera_s)
        saida = self._txt(r)
        if proxy_n is not None and f"PROXY_OK {int(proxy_n)}" not in saida:
            if "PRONTO" in saida:  # abriu sem confirmar o proxy (script antigo lá): fecha já, antes de qualquer acesso
                self.aberto = True
                self.fechar()
            else:
                self._fechar_tunel_proxy()
            raise RuntimeError(f"{self.nome}: Chrome sem confirmação do proxy {proxy_n} — não posto por lá "
                               f"({' '.join(saida.split())[-120:]})")
        if "PRONTO" not in saida:
            self._fechar_tunel_proxy()
            raise RuntimeError(f"{self.nome}: {' '.join(saida.split())[-200:] or 'sem resposta'}")
        self.aberto = True
        self.aberto_em = time.time()
        if "HOME=" in saida:
            self.home = saida.split("HOME=")[1].split()[0]
        if not tunel:
            log(f"{self.nome}: Chrome de {perfil} pronto (sem túnel)")
            return None
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.porta_local = s.getsockname()[1]
        self.tunel = subprocess.Popen([SSH, "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "-o", "ExitOnForwardFailure=yes", "-o",
                                       "ServerAliveInterval=15", "-N", "-L",
                                       f"{self.porta_local}:127.0.0.1:{self.porta}", *self.opts, self.alvo],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=SEM_JANELA)
        for _ in range(40):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.porta_local}/json/version", timeout=3)
                log(f"{self.nome}: Chrome de {perfil} pronto (porta local {self.porta_local})")
                return self.porta_local
            except Exception:  # noqa: BLE001
                if self.tunel.poll() is not None:
                    break
                time.sleep(0.5)
        self.fechar()
        raise RuntimeError(f"{self.nome}: túnel até o Chrome não abriu")

    def _ps_enc(self, script, timeout=120):
        """PowerShell por -EncodedCommand (vale no cmd do PC2 e no PowerShell do desktop; sem aspas para estragar)."""
        import base64
        script = "$ProgressPreference = 'SilentlyContinue'; " + script  # sem a barra de progresso o download voa
        return self._ssh("powershell -NoProfile -EncodedCommand " + base64.b64encode(script.encode("utf-16-le")).decode(),
                         timeout=timeout)

    def _enviar_http(self, p, destino_win):
        """O Windows PUXA o arquivo de um HTTP temporário do PC1 (30/10, D39: o desktop derruba scp; o Veo perdia o
        Chrome aberto lá porque a foto de referência não chegava)."""
        tmp = Path(tempfile.mkdtemp(prefix="enviar_http_"))
        try:
            nome = "a" + p.suffix.lower()
            try:
                os.link(p, tmp / nome)
            except OSError:
                import shutil
                shutil.copy2(p, tmp / nome)
            srv = _HttpTemp(tmp)
            try:
                r = self._ps_enc("New-Item -ItemType Directory -Force C:\\postador-worker\\entrada | Out-Null; "
                                 f"Invoke-WebRequest -UseBasicParsing -TimeoutSec 900 '{srv.url}/{nome}' -OutFile '{destino_win}'; "
                                 f"'TAM=' + (Get-Item '{destino_win}').Length", timeout=600 + p.stat().st_size / 1e6)
            finally:
                srv.fechar()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
        if f"TAM={p.stat().st_size}" not in self._txt(r):
            raise RuntimeError(f"{self.nome}: envio de {p.name} por HTTP falhou ({' '.join(self._txt(r).split())[-120:]})")
        log(f"{self.nome}: {p.name} enviado por HTTP ({p.stat().st_size // 1024} KB)")
        return destino_win

    def _enviar_win(self, p, nome):
        destino = f"C:/postador-worker/entrada/{int(time.time())}_{nome}"
        if MAQUINAS[self.nome].get("puxar_http"):
            return self._enviar_http(p, destino.replace("/", "\\"))
        # powershell explícito: o ssh do desktop cai no PowerShell e o do PC2 no cmd (23/10)
        self._ssh('powershell -NoProfile -Command "New-Item -ItemType Directory -Force C:\\postador-worker\\entrada'
                  ' | Out-Null"', timeout=30)
        r = subprocess.run([SSH.replace("ssh.exe", "scp.exe"), "-q", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", str(p),
                            f"{self.alvo}:{destino}"], capture_output=True, timeout=600 + p.stat().st_size / 1e6,
                           creationflags=SEM_JANELA)
        if r.returncode != 0:
            log(f"{self.nome}: scp de {p.name} falhou ({' '.join(self._txt(r).split())[-80:]}) — tento por HTTP")
            return self._enviar_http(p, destino.replace("/", "\\"))
        return destino.replace("/", "\\")

    def enviar(self, arquivo):
        """Manda o arquivo pelo ssh pra ~/postador-worker/entrada e devolve o caminho LÁ (o Chrome lê do disco dele)."""
        p = Path(arquivo)
        nome = "".join(c if c.isalnum() or c in "._-" else "_" for c in p.name)[-120:]
        if self.win:
            return self._enviar_win(p, nome)
        destino = f"postador-worker/entrada/{int(time.time())}_{nome}"
        tam = p.stat().st_size
        with open(p, "rb") as f:  # medido 22/10: ~8 MB/s; folga de 10 min + 1 s por MB
            r = self._ssh(f"mkdir -p ~/postador-worker/entrada && cat > ~/{destino} && stat -c %s ~/{destino}",
                          entrada=f, timeout=600 + tam / 1e6)
        if r.returncode != 0 or str(tam) not in self._txt(r):
            raise RuntimeError(f"{self.nome}: envio de {p.name} incompleto ({' '.join(self._txt(r).split())[-120:]})")
        return f"{self.home or '/home/' + self.alvo.split('@')[0]}/{destino}"

    def ceder_veo(self):
        """Notebook ocupado pelo Flow/Veo (até ~33 min por vídeo) cede pro login/conferência da dona: fecha aquele
        Chrome (o Veo refaz o vídeo noutra rodada). Postagem nunca é fechada. True = estava com o Veo e foi fechado."""
        try:
            est = json.loads(self._txt(self._ssh(f"{self.run} estado", timeout=30)).strip().splitlines()[-1])
        except (ValueError, IndexError, Exception):  # noqa: BLE001
            return False
        ab = est.get("aberto") or {}
        if not ab or ab.get("login"):
            return False
        abas = self._txt(self._ssh(f"curl -s localhost:{ab.get('porta')}/json", timeout=30))
        if "flow.google.com" not in abas and "labs.google" not in abas:
            return False
        print(f"{self.nome}: Veo/Flow de {ab.get('perfil')} ocupando — fecho pra dona", flush=True)
        try:  # dona 23/10: fechado pro login = "não feito" — o Veo lê isto e refaz noutra máquina sem castigar a conta
            VEO_CEDIDO.write_text(json.dumps({"maquina": self.nome, "perfil": ab.get("perfil"), "ts": time.time()}),
                                  encoding="utf-8")
        except OSError:
            pass
        self._ssh(f"{self.run} fechar 0; {self.run} fechar {ab.get('porta')}", timeout=60)
        time.sleep(10)  # o Chrome fechado ainda está saindo
        return True

    def fechar(self):
        if self.tunel:
            self.tunel.terminate()
            try:
                self.tunel.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.tunel.kill()
            self.tunel = None
        if self.aberto:
            try:
                self._ssh(f"{self.run} fechar {self.porta}", timeout=60)
            except subprocess.TimeoutExpired:
                pass
            self.aberto = False
        self._fechar_tunel_proxy()  # depois do Chrome: sem o túnel o Chrome de lá falha, nunca cai no IP de casa

    def _fechar_tunel_proxy(self):
        t = getattr(self, "tunel_proxy", None)
        if t:
            t.terminate()
            try:
                t.wait(timeout=10)
            except subprocess.TimeoutExpired:
                t.kill()
            self.tunel_proxy = None


    # ───── nsn na máquina (29/10, Fable D23): o postador-sem-navegador roda LÁ com os cookies de LÁ ─────
    @property
    def nsn_dir(self):
        return "C:/postador-worker/nsn" if self.win else "~/postador-worker/nsn"

    def nsn_win_pronto(self):
        try:
            r = self._ssh(f'powershell -NoProfile -Command "if (Test-Path {NSN_WIN_PY}) {{ \'OK\' }}"', timeout=25)
            return b"OK" in (r.stdout or b"")
        except subprocess.TimeoutExpired:
            return False

    def nsn_tem_cookie(self, perfil):
        """A máquina já colheu o cookie desse perfil (cookies/cofre_<perfil>.json com sessionid)?"""
        if self.win:  # 29/10: PC2 com worker próprio (venv em C:\postador-worker\nsn)
            try:
                r = self._ssh(f'findstr /m sessionid "{NSN_WIN}\\cookies\\cofre_{perfil}.json"', timeout=25)
                return b"cofre_" in (r.stdout or b"")
            except subprocess.TimeoutExpired:
                return False
        try:
            r = self._ssh(f"grep -q '\"sessionid\"' {self.nsn_dir}/cookies/cofre_{perfil}.json && echo TEM", timeout=25)
            return b"TEM" in (r.stdout or b"")
        except subprocess.TimeoutExpired:
            return False

    def nsn_colher(self, perfil, url="https://www.instagram.com/"):
        """Com o Chrome do perfil aberto LÁ (abrir), manda a máquina gravar os próprios cookies (nunca saem dela)."""
        try:
            if self.win:
                # 29/10 (D38b): pelo caminho, sem `cd /d … &&` (o ssh do desktop é PowerShell e lá isso não roda; o colher.py
                # acha cookies\ pelo próprio __file__). Vale igual no cmd do PC2.
                r = self._ssh(f'{NSN_WIN_PY} "{NSN_WIN}\\colher.py" {_q(perfil, True)} {self.porta} {_q(url, True)}',
                              timeout=90)
            else:
                r = self._ssh(f"cd {self.nsn_dir} && python3 colher.py {_q(perfil, False)} {self.porta} {_q(url, False)}",
                              timeout=90)
            ok = b"COLHIDO" in (r.stdout or b"")
            log(f"{self.nome}: colher {perfil}: {' '.join(self._txt(r).split())[-160:]}")
            return ok
        except subprocess.TimeoutExpired:
            return False

    def _nsn_reel_win(self, conta, arquivo, legenda):
        """PC2: igual ao Linux, mas a legenda vai num arquivo UTF-8 (o cmd do ssh estraga acento e emoji)."""
        p = Path(arquivo)
        enviados = []
        try:
            info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                                              "-select_streams", "v:0", "-of", "json", str(p)], capture_output=True,
                                             text=True, creationflags=SEM_JANELA, timeout=60).stdout)
            meta = {"w": info["streams"][0]["width"], "h": info["streams"][0]["height"], "dur": float(info["format"]["duration"])}
            tmp = Path(tempfile.gettempdir()) / f"nsn_{int(time.time())}"
            capa, metaf, legf = tmp.with_suffix(".capa.jpg"), tmp.with_suffix(".meta.json"), tmp.with_suffix(".legenda.txt")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(p), "-frames:v", "1", "-q:v", "3", str(capa)],
                           check=True, creationflags=SEM_JANELA, timeout=120)
            metaf.write_text(json.dumps(meta), encoding="utf-8")
            legf.write_text(legenda, encoding="utf-8")
            remoto = self.enviar(p)
            enviados = [remoto]
            for local, sufixo in ((capa, ".capa.jpg"), (metaf, ".meta.json")):
                rr = self.enviar(local)
                self._ssh(f'move /y "{rr}" "{remoto}{sufixo}"', timeout=30)
                enviados.append(remoto + sufixo)
                local.unlink(missing_ok=True)
            leg_r = self.enviar(legf)
            enviados.append(leg_r)
            legf.unlink(missing_ok=True)
            # 30/10 (D39): pelo caminho (o postar.py põe a raiz no sys.path), sem `cd /d … &&`, que não roda no PowerShell
            # do desktop; no cmd do PC2 é o mesmo comando (provado: chega no main() lá)
            r = self._ssh(f'{NSN_WIN_PY} -X utf8 "{NSN_WIN}\\services\\instagram\\postar.py" reel {_q(conta, True)} '
                          f'"{remoto}" "@{leg_r}"', timeout=1200)
            saida = " ".join(self._txt(r).split())
            # 29/10 18:55: só URL de verdade. Um traceback do worker traz a LINHA DE CÓDIGO 'print("reel ok:", ...)' e o
            # teste antigo ("reel ok:" in saida) dava "postado" para 6 Reels que NÃO saíram (sintetizerisada, jornalcomia)
            m = re.search(r"reel ok: (https://www\.instagram\.com/reel/[A-Za-z0-9_-]+/)", saida)
            if m:
                log(f"{self.nome}: Reel por HTTP ({conta}) -> {m.group(1)}")
                return True, "nsn:" + self.nome
            erro = next((l for l in reversed(saida.splitlines()) if l.strip() and not l.strip().startswith(("^", "~"))), saida)
            return False, f"nsn {self.nome}: {erro.strip()[-220:]}"
        except subprocess.TimeoutExpired:
            return False, f"nsn {self.nome}: estourou o tempo"
        except Exception as e:  # noqa: BLE001
            return False, f"nsn {self.nome}: {type(e).__name__}: {str(e)[:120]}"
        finally:
            for x in enviados:
                try:
                    self._ssh(f'del /q "{x}"', timeout=30)
                except subprocess.TimeoutExpired:
                    pass

    def nsn_reel(self, conta, arquivo, legenda):
        """Reel por HTTP NA máquina: manda vídeo + capa + medidas (ffmpeg daqui; o Acer não tem) e roda o postar lá.
        Devolve (ok, msg). Não ocupa o Chrome da máquina (vale mesmo com o telão passando vídeo)."""
        if self.win:
            return self._nsn_reel_win(conta, arquivo, legenda)
        p = Path(arquivo)
        try:
            info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                                              "-select_streams", "v:0", "-of", "json", str(p)], capture_output=True,
                                             text=True, creationflags=SEM_JANELA, timeout=60).stdout)
            meta = {"w": info["streams"][0]["width"], "h": info["streams"][0]["height"], "dur": float(info["format"]["duration"])}
            capa = Path(tempfile.gettempdir()) / f"capa_{int(time.time())}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(p), "-frames:v", "1", "-q:v", "3", str(capa)],
                           check=True, creationflags=SEM_JANELA, timeout=120)
            metaf = capa.with_suffix(".json")
            metaf.write_text(json.dumps(meta), encoding="utf-8")
            remoto = self.enviar(p)
            capa_r = self.enviar(capa)
            meta_r = self.enviar(metaf)
            capa.unlink(missing_ok=True)
            metaf.unlink(missing_ok=True)
            self._ssh(f"mv {_q(capa_r, False)} {_q(remoto + '.capa.jpg', False)} && mv {_q(meta_r, False)} {_q(remoto + '.meta.json', False)}",
                      timeout=30)
            r = self._ssh(f"cd {self.nsn_dir} && python3 -X utf8 -m services.instagram.postar reel {_q(conta, False)} "
                          f"{_q(remoto, False)} {_q(legenda, False)}", timeout=1200)
            saida = " ".join(self._txt(r).split())
            self._ssh(f"rm -f {_q(remoto, False)} {_q(remoto + '.capa.jpg', False)} {_q(remoto + '.meta.json', False)}", timeout=30)
            # 29/10 18:55: só URL de verdade. Um traceback do worker traz a LINHA DE CÓDIGO 'print("reel ok:", ...)' e o
            # teste antigo ("reel ok:" in saida) dava "postado" para 6 Reels que NÃO saíram (sintetizerisada, jornalcomia)
            m = re.search(r"reel ok: (https://www\.instagram\.com/reel/[A-Za-z0-9_-]+/)", saida)
            if m:
                log(f"{self.nome}: Reel por HTTP ({conta}) -> {m.group(1)}")
                return True, "nsn:" + self.nome
            erro = next((l for l in reversed(saida.splitlines()) if l.strip() and not l.strip().startswith(("^", "~"))), saida)
            return False, f"nsn {self.nome}: {erro.strip()[-220:]}"
        except subprocess.TimeoutExpired:
            return False, f"nsn {self.nome}: estourou o tempo"
        except Exception as e:  # noqa: BLE001
            return False, f"nsn {self.nome}: {type(e).__name__}: {str(e)[:120]}"

    # ───── Flow/Veo por HTTP na máquina (29/10, Fable D30): o Chrome de lá só fabrica o token do reCAPTCHA ─────
    @property
    def _nsn_py(self):
        return f"{NSN_WIN_PY} -X utf8" if self.win else "python3 -X utf8"

    def _nsn_script(self, modulo):
        """Comando do python do worker rodando o módulo PELO CAMINHO (os módulos do veo_flow põem a raiz no sys.path):
        vale no cmd (PC2), no PowerShell (desktop: `cd /d … &&` não existe lá, 29/10) e no bash dos notebooks."""
        rel = modulo.replace(".", "/") + ".py"
        if self.win:
            return f'{self._nsn_py} "{NSN_WIN}\\{rel.replace("/", chr(92))}"'
        return f"{self._nsn_py} {self.nsn_dir}/{rel}"

    def receber(self, remoto, local):
        """Traz um arquivo de lá (scp). `remoto` com barras normais (o OpenSSH do Windows aceita C:/...)."""
        if self.win and MAQUINAS[self.nome].get("puxar_http"):
            return self._receber_http(remoto, local)
        p = MAQUINAS[self.nome].get("porta_ssh")
        r = subprocess.run([SSH.replace("ssh.exe", "scp.exe"), "-q", "-r", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR",
                            *(["-P", str(p)] if p else []), f"{self.alvo}:{remoto}", str(local)],
                           capture_output=True, timeout=900, creationflags=SEM_JANELA)
        if r.returncode != 0 or not Path(local).exists():
            if self.win:
                log(f"{self.nome}: scp de volta falhou ({' '.join(self._txt(r).split())[-80:]}) — tento por HTTP")
                return self._receber_http(remoto, local)
            raise RuntimeError(f"{self.nome}: não trouxe {remoto} ({self._txt(r)[-120:]})")
        return Path(local)

    def _receber_http(self, remoto, local):
        """30/10 (D39): o Windows SOBE o arquivo (pasta = tar de lá) para um HTTP temporário do PC1 que aceita PUT."""
        import shutil
        import tarfile
        local = Path(local)
        tmp = Path(tempfile.mkdtemp(prefix="receber_http_"))
        rw = str(remoto).replace("/", "\\")
        try:
            srv = _HttpTemp(tmp, aceita_put=True)
            try:
                r = self._ps_enc(
                    f"$r = '{rw}'; $d = Test-Path $r -PathType Container; "
                    "if ($d) { $f = Join-Path $env:TEMP ('rec_' + [guid]::NewGuid().ToString('N') + '.tar'); "
                    "tar -cf $f -C (Split-Path $r) (Split-Path $r -Leaf) } else { $f = $r }; "
                    f"Invoke-WebRequest -UseBasicParsing -TimeoutSec 900 -Method Put -InFile $f -Uri '{srv.url}/volta.bin' | Out-Null; "
                    "if ($d) { Remove-Item $f -Force }; 'SUBIU ' + [int]$d", timeout=1200)
            finally:
                srv.fechar()
            saida = self._txt(r)
            arq = tmp / "volta.bin"
            if "SUBIU" not in saida or not arq.exists():
                raise RuntimeError(f"{self.nome}: não trouxe {remoto} por HTTP ({' '.join(saida.split())[-120:]})")
            if "SUBIU 1" in saida:  # pasta: extrai e põe no lugar de `local`, como o scp -r faria
                with tarfile.open(arq) as t:
                    t.extractall(tmp / "x")
                shutil.move(str(next((tmp / "x").iterdir())), str(local))
            else:
                local.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(arq), str(local))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        log(f"{self.nome}: {Path(remoto).name} trazido por HTTP")
        return local

    def nsn_flow_pronto(self):
        """A máquina tem o worker com o Flow (instalar-nsn depois de 29/10)?"""
        try:
            if self.win:
                r = self._ssh(f'powershell -NoProfile -Command "if (Test-Path {NSN_WIN}\\services\\veo_flow\\flow_gerar.py) '
                              f"{{ 'OK' }}\"", timeout=25)
            else:
                r = self._ssh(f"test -f {self.nsn_dir}/services/veo_flow/flow_gerar.py && echo OK", timeout=25)
            return b"OK" in (r.stdout or b"")
        except subprocess.TimeoutExpired:
            return False

    def nsn_tem_google(self, perfil):
        """A máquina já colheu o cookie GOOGLE desse perfil (SID em cookies/cofre_<perfil>.json)?"""
        try:
            r = self._ssh(f"{self._nsn_script('services.veo_flow.saude_flow')} --tem {_q(perfil, self.win)}",
                          timeout=40)
            return b"TEM" in (r.stdout or b"")
        except subprocess.TimeoutExpired:
            return False

    def nsn_flow_saude(self):
        """Flow logado em quais perfis desta máquina? (HTTP lá, com os cookies de lá; 1 ssh por máquina). Lista de
        {"perfil", "vivo", "creditos", "ms", "obs", "colhido"}."""
        out = []
        try:
            r = self._ssh(self._nsn_script("services.veo_flow.saude_flow"), timeout=240)
        except subprocess.TimeoutExpired:
            return out
        for linha in self._txt(r).splitlines():
            if linha.startswith("{"):
                try:
                    out.append(json.loads(linha))
                except ValueError:
                    pass
        return out

    def nsn_run(self, modulo, args, enviar=(), receber=(), timeout=900, log_fn=log):
        """29/10 (D31, dona: "tudo isso tem que rodar em todos os notebooks e PCs"): roda QUALQUER módulo do worker LÁ,
        com os cookies de lá, como `python <modulo>.py <args>`. Os argumentos vão num JSON UTF-8 (runpy + sys.argv): nada
        de aspas do cmd/PowerShell/bash estragando acento. `enviar`: caminhos locais que aparecem em args — vão por ssh e
        o arg vira o caminho de lá. `receber`: caminhos locais que aparecem em args — viram <nsn>/saida/... lá e voltam
        por scp no fim (arquivo ou pasta). Devolve (rc, saida_texto)."""
        args = [str(a) for a in args]
        mandados, trazer = [], []
        try:
            for loc in enviar:
                loc = str(loc)
                if loc in args and Path(loc).is_file():
                    rem = self.enviar(loc)
                    mandados.append(rem)
                    args = [rem if a == loc else ("@" + rem if a == "@" + loc else a) for a in args]
            base = f"{NSN_WIN}\\saida" if self.win else f"{self.home or '/home/' + self.alvo.split('@')[0]}/postador-worker/nsn/saida"
            for loc in receber:
                loc = str(loc)
                nome = "".join(c if c.isalnum() or c in "._-" else "_" for c in Path(loc).name)[-80:]
                rem = f"{base}\\{int(time.time())}_{nome}" if self.win else f"{base}/{int(time.time())}_{nome}"
                args = [rem if a == loc else a for a in args]
                trazer.append((rem, loc))
            af = Path(tempfile.gettempdir()) / f"nsn_args_{int(time.time() * 1000)}.json"
            script_rem = (f"{NSN_WIN}/{modulo.replace('.', '/')}.py" if self.win
                          else f"{self.home or '/home/' + self.alvo.split('@')[0]}/postador-worker/nsn/{modulo.replace('.', '/')}.py")
            af.write_text(json.dumps([script_rem] + args, ensure_ascii=False), encoding="utf-8")
            args_rem = self.enviar(af)
            af.unlink(missing_ok=True)
            mandados.append(args_rem)
            a_r, s_r = args_rem.replace("\\", "/"), script_rem.replace("\\", "/")
            cmd = (f"{self._nsn_py} -c \"import sys,json,runpy; sys.argv=json.load(open('{a_r}',encoding='utf-8')); "
                   f"sys.path.insert(0,'{s_r.rsplit('/', 1)[0]}'); runpy.run_path('{s_r}', run_name='__main__')\"")
            r = self._ssh(cmd, timeout=timeout)
            saida = self._txt(r)
            for rem, loc in trazer:
                try:
                    Path(loc).parent.mkdir(parents=True, exist_ok=True)
                    self.receber(rem.replace("\\", "/"), loc)
                    mandados.append(rem)
                except Exception as e:  # noqa: BLE001
                    saida += f"\n[nsn_run] não trouxe {rem}: {e}"
            log_fn(f"{self.nome}: nsn {modulo} rc={r.returncode}: {' '.join(saida.split())[-160:]}")
            return r.returncode, saida
        except subprocess.TimeoutExpired:
            return 124, f"nsn {self.nome}: estourou o tempo ({timeout} s)"
        finally:
            for x in mandados:
                try:
                    self._ssh(f'powershell -NoProfile -Command "Remove-Item -Recurse -Force \'{x}\' -ErrorAction SilentlyContinue"'
                              if self.win else f"rm -rf {_q(x, False)}", timeout=30)
                except subprocess.TimeoutExpired:
                    pass

    def nsn_flow_video(self, perfil, projeto, prompt, saida_local, formato="9:16", modelo="Veo 3.1 - Fast", imagem=None,
                       fechar_chrome=True, timeout=1800, log_fn=log):
        """Gera o vídeo do Veo por HTTP NA máquina: o Chrome do perfil já está aberto lá (abrir/tentativas) e serve só
        para o token do reCAPTCHA; com fechar_chrome ele é fechado assim que o Flow aceita o pedido. Prompt e foto vão
        por ssh; o mp4 volta por scp. Devolve dict: ok, msg, pediu (o Flow já recebeu o pedido = crédito gasto),
        sem_credito, login, chrome_s (segundos de Chrome aberto medidos daqui), segundos (do pedido)."""
        return self._nsn_flow("video", perfil, projeto, prompt, saida_local, formato, modelo, imagem=imagem,
                              fechar_chrome=fechar_chrome, timeout=timeout, log_fn=log_fn)

    def nsn_flow_imagem(self, perfil, projeto, prompt, saida_local, refs=(), formato="9:16", modelo="Nano Banana 2.1",
                        fechar_chrome=True, timeout=900, log_fn=log, fabrica=None):
        """Imagem do Flow (Nano Banana) por HTTP NA máquina, mesmo caminho do vídeo; refs = fotos de referência daqui
        (vão por ssh e o worker as sobe no projeto). 1 imagem por pedido. fabrica = perfil do Chrome QUENTE da fábrica
        de tokens de lá (02/11, fabrica_tokens.py): não abre nem fecha Chrome, só pede token."""
        return self._nsn_flow("imagem", perfil, projeto, prompt, saida_local, formato, modelo, refs=refs,
                              fechar_chrome=fechar_chrome, timeout=timeout, log_fn=log_fn, fabrica=fabrica)

    def nsn_flow_video_2fases(self, perfil, projeto, prompt, saida_local, formato="9:16", modelo="Veo 3.1 - Fast",
                              imagem=None, soltar=None, timeout=1800, log_fn=log):
        """29/10 (D31, dona: "deixe as máquinas produzindo ao máximo"): 1ª fase = token + pedido (Chrome ~40 s) e o worker
        fecha o Chrome; `soltar()` é chamado aqui (o Veo libera a vez da máquina) e a 2ª fase baixa o mp4 SEM Chrome, com
        os cookies colhidos lá — a máquina fica livre para outra conta/post enquanto o Flow renderiza."""
        res = self._nsn_flow("video-pedir", perfil, projeto, prompt, saida_local, formato, modelo, imagem=imagem,
                             fechar_chrome=True, timeout=900, log_fn=log_fn)
        if not res.get("midias"):
            return res
        if soltar:
            try:
                soltar()
            except Exception as e:  # noqa: BLE001
                log_fn(f"{self.nome}: não soltei a vez ({e})")
        q = lambda s: _q(s, self.win)  # noqa: E731
        nome = "".join(c if c.isalnum() or c in "._-" else "_" for c in Path(saida_local).name)[-80:]
        base = f"{NSN_WIN}\\saida" if self.win else f"{self.home or '/home/' + self.alvo.split('@')[0]}/postador-worker/nsn/saida"
        saida_r = f"{base}\\{int(time.time())}_{nome}" if self.win else f"{base}/{int(time.time())}_{nome}"
        t0 = time.time()
        try:
            # 30/10 (D40): a 2ª fase só baixa (o crédito já foi gasto na 1ª). 05:00 no desktop: pedido aceito e a 2ª fase
            # caiu no ssh (Connection reset) = vídeo pago e perdido. Falha de ssh/rede tenta de novo (3×, 20 s).
            for tentativa in range(3):
                try:
                    r = self._ssh(f"{self._nsn_script('services.veo_flow.flow_gerar')} --porta {self.porta} "
                                  f"--projeto {q(projeto)} --nome {q(perfil)} baixar {q(res['midias'][0])} {q(saida_r)}",
                                  timeout=timeout)
                    saida = self._txt(r)
                    if "FLOW_OK" in saida:
                        self.receber(saida_r.replace("\\", "/"), saida_local)
                        tam = Path(saida_local).stat().st_size
                        res["ok"] = tam >= 100_000
                        res["msg"] = f"nsn:{self.nome} {tam // 1024} KB (2 fases)" if res["ok"] else f"mp4 veio com {tam} bytes"
                    else:
                        res["msg"] = f"nsn {self.nome}: {' '.join(saida.split())[-200:]}"
                except subprocess.TimeoutExpired:
                    res["msg"] = f"nsn {self.nome}: 2ª fase estourou o tempo"
                except Exception as e:  # noqa: BLE001
                    res["msg"] = f"nsn {self.nome}: {type(e).__name__}: {str(e)[:150]}"
                rede = any(s in res["msg"] for s in ("Connection reset", "Connection closed", "não trouxe",
                                                      "sem resposta")) or res["msg"].rstrip().endswith(":")
                if res["ok"] or not rede or tentativa == 2:
                    break
                log(f"{self.nome}: 2ª fase caiu no ssh ({res['msg'][-80:]}) — tento de novo ({tentativa + 2}/3)")
                time.sleep(20)
        finally:
            try:
                self._ssh(f'powershell -NoProfile -Command "Remove-Item -Force \'{saida_r}\' -ErrorAction SilentlyContinue"'
                          if self.win else f"rm -f {_q(saida_r, False)}", timeout=30)
            except subprocess.TimeoutExpired:
                pass
        res["total_s"] = (res.get("total_s") or 0) + round(time.time() - t0)
        log(f"{self.nome}: Flow por HTTP video 2ª fase ({perfil}): {'ok' if res['ok'] else res['msg'][:160]} total={res['total_s']} s")
        return res

    def _nsn_flow(self, tipo, perfil, projeto, prompt, saida_local, formato, modelo, imagem=None, refs=(),
                  fechar_chrome=True, timeout=1800, log_fn=log, fabrica=None):
        res = {"ok": False, "msg": "", "pediu": False, "sem_credito": False, "login": False, "chrome_s": None,
               "segundos": None, "saldo": None, "midias": []}
        if conta_kaggle_viva(perfil):  # 12/11: conta viva do Kaggle nunca no Flow por IP de casa (3º banimento)
            res["msg"] = f"FLOW_RECUSADO {perfil}: conta viva do Kaggle — fora do Flow pela internet de casa"
            return res
        minimo = 100_000 if tipo == "video" else 5_000
        enviados = []
        t0 = time.time()
        try:
            pf = Path(tempfile.gettempdir()) / f"flow_prompt_{int(time.time())}.txt"
            pf.write_text(prompt, encoding="utf-8")
            prompt_r = self.enviar(pf)
            pf.unlink(missing_ok=True)
            enviados.append(prompt_r)
            img_r = None
            if imagem and Path(imagem).exists():
                img_r = self.enviar(imagem)
                enviados.append(img_r)
            refs_r = []
            for ref in refs or ():
                if Path(ref).exists():
                    refs_r.append(self.enviar(ref))
                    enviados.append(refs_r[-1])
            nome = "".join(c if c.isalnum() or c in "._-" else "_" for c in Path(saida_local).name)[-80:]
            if self.win:
                saida_r = f"{NSN_WIN}\\saida\\{int(time.time())}_{nome}"
                # powershell explícito: vale no cmd (PC2) e no PowerShell (desktop)
                self._ssh(f'powershell -NoProfile -Command "New-Item -ItemType Directory -Force \'{NSN_WIN}\\saida\' | Out-Null"',
                          timeout=30)
            else:
                saida_r = f"{self.home or '/home/' + self.alvo.split('@')[0]}/postador-worker/nsn/saida/{int(time.time())}_{nome}"
                self._ssh("mkdir -p ~/postador-worker/nsn/saida", timeout=30)
            q = lambda s: _q(s, self.win)  # noqa: E731
            onde = (f"--fabrica 9399 --perfil {q(fabrica)}" if fabrica else
                    f"--porta {self.porta}{' --fechar-chrome' if fechar_chrome else ''}")
            cmd = (f"{self._nsn_script('services.veo_flow.flow_gerar')} {onde} "
                   f"--projeto {q(projeto)} --nome {q(perfil)} "
                   f"{tipo} {q('@' + prompt_r)} {q(saida_r)} --formato {q(formato)} --modelo {q(modelo)}"
                   + (f" --imagem-inicial {q(img_r)}" if img_r else "")
                   + "".join(f" --ref {q(x)}" for x in refs_r))
            t_ssh = time.time()
            r = self._ssh(cmd, timeout=timeout)
            saida = self._txt(r)
            for linha in saida.splitlines():
                l = linha.strip()
                if l.startswith("FLOW_CREDITOS"):
                    res["saldo"] = l.split("saldo=")[1].split()[0]
                elif l.startswith("FLOW_SEM_CREDITO"):
                    res["sem_credito"] = True
                elif l.startswith("FLOW_LOGIN"):
                    res["login"] = True
                elif l.startswith("FLOW_PEDIDO_OK"):
                    res["pediu"] = True
                    res["segundos"] = int(l.split("segundos=")[1].split()[0])
                elif l.startswith("FLOW_CHROME_SOLTO"):
                    # Chrome aberto = desde o "pronto" do abrir até o worker soltá-lo (chrome_s conta do início do worker)
                    res["chrome_s"] = round((t_ssh - (self.aberto_em or t_ssh)) + int(l.split("chrome_s=")[1].split()[0]))
                elif l.startswith("FLOW_RECUSADO") or l.startswith("FLOW_ERRO"):
                    res["msg"] = l[:300]
                elif l.startswith("FLOW_MIDIAS"):  # 1ª fase do vídeo em 2 fases: ids pedidos
                    res["midias"] = [x for x in l.split(" ", 1)[1].split(",") if x]
                elif l.startswith("FLOW_OK"):
                    res["ok"] = True
            # 12/11: alimenta o disjuntor do HTTP do Flow no PC1 (vazio = conta; mídia entregue = fecha)
            try:
                nsn = str(ROOT.parent / "projeto-navegador-sem-navegador")
                if nsn not in sys.path:
                    sys.path.append(nsn)
                from services.veo_flow import flow_gerar as _fg
                if res.get("ok") or res.get("pediu"):
                    _fg.disjuntor_registrar(True)
                elif "não entregou mídia" in str(res.get("msg") or ""):
                    _fg.disjuntor_registrar(False)
            except Exception:  # noqa: BLE001
                pass
            if res["ok"]:
                self.receber(saida_r.replace("\\", "/"), saida_local)
                tam = Path(saida_local).stat().st_size
                if tam < minimo:
                    res["ok"], res["msg"] = False, f"arquivo veio com {tam} bytes"
                else:
                    res["msg"] = f"nsn:{self.nome} {tam // 1024} KB"
                enviados.append(saida_r)
            elif res["midias"]:
                res["msg"] = f"pedido aceito ({len(res['midias'])} mídia): 2ª fase baixa"
            elif not res["msg"]:
                res["msg"] = f"nsn {self.nome}: {' '.join(saida.split())[-200:] or 'sem resposta'}"
        except subprocess.TimeoutExpired:
            res["msg"] = f"nsn {self.nome}: estourou o tempo ({timeout} s)"
        except Exception as e:  # noqa: BLE001
            res["msg"] = f"nsn {self.nome}: {type(e).__name__}: {str(e)[:150]}"
        finally:
            for x in enviados:
                try:
                    self._ssh(f'powershell -NoProfile -Command "Remove-Item -Force \'{x}\' -ErrorAction SilentlyContinue"'
                              if self.win else f"rm -f {_q(x, False)}", timeout=30)
                except subprocess.TimeoutExpired:
                    pass
        res["total_s"] = round(time.time() - t0)
        linha = (f"{self.nome}: Flow por HTTP {tipo} ({perfil}): {'ok' if res['ok'] else res['msg'][:160]}"
                 f"{' chrome=' + str(res['chrome_s']) + ' s' if res['chrome_s'] is not None else ''} total={res['total_s']} s")
        log(linha)  # sempre no maquina_remota.log: a aba "Sem navegador" do painel lê "Flow por HTTP" daqui
        if log_fn is not log:
            log_fn(linha)
        return res


def _lista(maquinas):
    if not maquinas:
        return []
    if isinstance(maquinas, str):
        maquinas = [maquinas]
    return [m for m in maquinas if m in MAQUINAS]


USO = ROOT / "config" / "netbooks_uso.json"


def _ler_uso():
    try:
        return json.loads(USO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _marcar_uso(nome):
    try:
        d = _ler_uso()
        d[nome] = time.time()
        USO.write_text(json.dumps(d), encoding="utf-8")
    except OSError:
        pass


RESERVADOS = ROOT / "config" / "notebooks_reservados.json"
VEO_CEDIDO = Path(r"D:\veo\beta\logs\veo_cedido_login.json")  # ceder_veo grava; cron_gerar_video_llm lê e apaga


def reservado(nome, quem=None):
    """Motivo (str) se a máquina está com a VEZ de outro ("um navegador por vez", dona 23/10); "" se livre ou se a vez
    é de `quem`. O mesmo arquivo que o Veo (cadeia_veo), o telão (vitrine/player) e o tiktok_notebooks respeitam."""
    try:
        r = json.loads(RESERVADOS.read_text(encoding="utf-8")).get(nome) or {}
        if float(r.get("ate", 0)) > time.time() and (not quem or r.get("por") != quem):
            return str(r.get("por") or "reservado")
    except (OSError, ValueError, TypeError):
        pass
    return ""


def ocupar(nome, motivo, minutos):
    """Dá a vez da máquina pra `motivo` por `minutos` (ex.: "login manual", 30). Quem vier depois espera ou vai pro
    outro PC; o telão mostra só o painel (e nada, se o motivo tem "login")."""
    pol = _politica()
    d = pol.ler_json(RESERVADOS, {})
    d[nome] = {"por": motivo, "ate": time.time() + float(minutos) * 60, "desde": time.time()}
    pol.gravar_json(RESERVADOS, d)
    log(f"vez de {nome}: {motivo} por {minutos} min")


def liberar(nome, quem=None):
    pol = _politica()
    d = pol.ler_json(RESERVADOS, {})
    if nome in d and (not quem or d[nome].get("por") == quem):
        d.pop(nome)
        pol.gravar_json(RESERVADOS, d)
        log(f"vez de {nome}: liberada")


def exibindo(nome):
    """O telão (D:\\video-fila\\vitrine\\player.py) está passando vídeo nesse notebook ou acabou de passar (fila
    andando)? Dona 24/10: "estava exibindo no Acer e entrou o Flow imagem do nada" — um navegador por vez: quem chega
    vai pro próximo notebook/PC1. ~/vitrine/TOCANDO (durante o vídeo; velho de 15 min não vale) ou ~/vitrine/TOCOU
    (fim do último, < 2 min). Sem resposta = não está (o vivo() decide)."""
    if MAQUINAS.get(nome, {}).get("win"):
        return False  # desktop/PC2 não tocam vídeo do telão
    try:
        r = Remoto(nome)
        t = r._txt(r._ssh("a=$(date +%s); for f in TOCANDO:900 TOCOU:120; do p=~/vitrine/${f%%:*}; "
                          "[ -f $p ] && [ $(( a - $(stat -c %Y $p) )) -lt ${f##*:} ] && echo EXIBINDO; done; echo FIM",
                          timeout=25))
        return "EXIBINDO" in t
    except Exception:  # noqa: BLE001
        return False


def tentativas(maquinas, perfil, url="about:blank", log_fn=log, proxy_n=None):
    """Ordem de tentativa (dona 23/10: "se a conta existir logada nos notebooks usa neles; deu erro faz no outro; deu
    erro a 2ª vez ou a conta não existe lá, faz no PC1"): rende um Remoto aberto em cada notebook da conta (pula o que
    estiver fora/ocupado/sem RAM) e por fim None = este PC. Quem chama tenta a operação; deu certo, para (feche o
    gerador com .close()); deu erro, pede o próximo. O Chrome do notebook é fechado ao passar pro próximo."""
    # dona 23/10: "as tarefas distribuídas, um entra de failback do outro e o PC entra como failback dos 2": começa
    # pelo notebook que está há MAIS tempo sem trabalhar
    uso = _ler_uso()
    # 27/10 (dona): ORDEM FIXA notebooks -> PC2 -> desktop -> PC1 (este). Antes era "lento por último" e o desktop
    # (não lento) passava na frente do Acer e do PC2. Entre os notebooks o Acer (Atom) segue depois do X200MA.
    # 28/10 (dona): desktop agora vai PRIMEIRO (ORDEM_NAVEGADOR), fora dos horários da câmera.
    for nome in (sorted(_lista(maquinas), key=lambda m: (ORDEM_NAVEGADOR.get(m, 9), uso.get(m, 0)))
                 if perfil else []):
        # 24/10: a vez do PRÓPRIO chamador não bloqueia (o cron do Veo reserva o notebook como "veo" e o worker do Veo
        # pulava a máquina reservada pra ele: 18 contas descartadas em 40 s). Quem chama diz quem é em MAQUINA_VEZ_DE.
        vez = reservado(nome, os.environ.get("MAQUINA_VEZ_DE") or None)
        porta_extra = None
        # 12/11 (dona: "pode usar o STI ao máximo, i5 e 16 GB, suporta muitos Chromes"): máquina com 2ª FAIXA
        # (MAQUINAS[...]["faixa_extra"]) não para pelo login AUTOMÁTICO de TikTok — abre um 2º Chrome na porta extra
        # (o chrome_conta tem ocupante próprio pras portas 9461–9479). Login manual da dona continua barrando.
        if (vez and MAQUINAS[nome].get("faixa_extra") and "tiktok" in vez.lower() and "manual" not in vez.lower()
                and os.environ.get("MAQUINA_SEM_FAIXA_EXTRA") != "1"):
            porta_extra = MAQUINAS[nome]["faixa_extra"]
            log_fn(f"  {nome} com '{vez}': uso a 2ª faixa (porta {porta_extra})")
            vez = ""
        if vez:  # 23/10 (dona): um navegador por vez — com a vez de outro (Veo, login...), vai pro próximo/PC1
            log_fn(f"  {nome} está com a vez de '{vez}': vai pro próximo")
            continue
        if _camera_agendada(nome):
            log_fn(f"  {nome}: {_camera_agendada(nome)}: vai pro próximo")
            continue
        if exibindo(nome):
            log_fn(f"  {nome} está exibindo vídeo no telão: vai pro próximo")
            continue
        if proxy_n is not None and nome in SEM_PROXY_REMOTO:
            log_fn(f"  {nome}: sem o Chrome pelo proxy lá ainda — vai pro próximo")
            continue
        r = Remoto(nome)
        if porta_extra:
            r.porta = porta_extra
        if not r.vivo():
            log_fn(f"  {nome} não respondeu")
            continue
        try:
            r.abrir(perfil, url, sem_espera=True, proxy_n=proxy_n)
        except Exception as e:  # noqa: BLE001
            log_fn(f"  {e}")
            r.fechar()
            continue
        _marcar_uso(nome)
        try:
            yield r
        finally:
            r.fechar()
    yield None


def tentar(maquinas, perfil, url="about:blank", log_fn=log):
    """Remoto aberto no primeiro notebook LIVRE da lista, ou None (todos fora/ocupados/sem RAM): quem chama posta por
    este PC como sempre (regra da casa: nunca sem postagem)."""
    if not perfil:
        return None
    for nome in _lista(maquinas):
        vez = reservado(nome, os.environ.get("MAQUINA_VEZ_DE") or None)  # 24/10: a vez do próprio chamador não bloqueia
        if vez:  # 23/10 (dona): um navegador por vez
            log_fn(f"  {nome} está com a vez de '{vez}'")
            continue
        if exibindo(nome):
            log_fn(f"  {nome} está exibindo vídeo no telão")
            continue
        r = Remoto(nome)
        if not r.vivo():
            log_fn(f"  {nome} não respondeu")
            continue
        try:
            r.abrir(perfil, url, sem_espera=True)
            return r
        except Exception as e:  # noqa: BLE001
            log_fn(f"  {e}")
            r.fechar()
    if _lista(maquinas):
        log_fn("  nenhum notebook livre: posta por este PC")
    return None


def abrir_url_notebook(maquinas, url, log_fn=log):
    """Abre a URL no navegador do primeiro notebook vivo (sem túnel, sem bloquear). Retorna o nome ou None."""
    cmd = (f"eval $(systemctl --user show-environment 2>/dev/null | grep -E '^DISPLAY=') 2>/dev/null; "
           f"export DISPLAY=${{DISPLAY:-:0}}; xdg-open {shlex.quote(url)} &")
    for nome in _lista(maquinas):
        r = Remoto(nome)
        if not r.vivo():
            continue
        try:
            r._ssh(cmd, timeout=15)
            log_fn(f"{nome}: abriu {url} na tela")
            return nome
        except Exception:  # noqa: BLE001
            continue
    return None


# ─────────────────────────── contas / logins ───────────────────────────────
def _politica():
    sys.path.insert(0, str(BIN))
    import politica
    return politica


def _logins():
    # 28/10: devolver {} quando a leitura falhava (Acesso negado no meio do os.replace de outro processo) fazia o
    # próximo gravador regravar o arquivo só com a linha dele — às 14:45 sumiram os logins de todos os notebooks e
    # o Veo ficou sem máquina. Arquivo que existe e não lê: tenta de novo; persistindo, erro (nunca {}).
    for _ in range(20):
        try:
            return json.loads(LOGINS.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            time.sleep(0.25)
    return json.loads(LOGINS.read_text(encoding="utf-8"))


def _mapa_perfis():
    """perfil -> {'email', 'youtube': [slugs], 'tiktok': [contas]} a partir das configs do postador."""
    pol = _politica()
    yt = pol.ler_json(pol.CONFIG_DIR / "youtube_navegador.json", {"canais": {}}).get("canais", {})
    tt = (pol.ler_json(pol.CONFIG_DIR / "reuso_plataformas.json", {}).get("tiktok") or {}).get("contas", {})
    out = {}
    for slug, e in yt.items():
        if not e.get("email") or not e.get("usar"):
            continue
        p = e["email"].split("@")[0].lower()
        out.setdefault(p, {"email": e["email"], "youtube": [], "tiktok": []})["youtube"].append(slug)
    for conta, r in tt.items():
        p = (r.get("cofre") or "").lower()
        if p:
            out.setdefault(p, {"email": None, "youtube": [], "tiktok": []})["tiktok"].append(conta)
    ig = (pol.ler_json(pol.CONFIG_DIR / "reuso_plataformas.json", {}).get("instagram") or {}).get("contas", {})
    for conta, r in ig.items():  # Instagram: perfil próprio do cofre (ig_<conta>), login do Instagram, não do Google
        p = (r.get("cofre") or f"ig_{conta}").lower()
        out.setdefault(p, {"email": None, "youtube": [], "tiktok": []}).setdefault("instagram", []).append(conta)
    for info in out.values():
        info.setdefault("instagram", [])
    # recap de parceiros é a prioridade da dona: os e-mails dos canais dele vêm primeiro na fila de logar
    parceiro = _canais_parceiro()
    eh = lambda info: any(any(s.replace("_", "").startswith(c) or c.startswith(s.replace("_", ""))  # noqa: E731
                              for c in parceiro) for s in info["youtube"])
    return dict(sorted(out.items(), key=lambda kv: (not eh(kv[1]), not kv[1]["youtube"])))


# Flow bloqueado na conta (flow.google.com/age-restricted, D:\veo\beta\contas.py): login vale pro YouTube, não pro Flow
FLOW_BLOQUEADAS = {"emersonjosiel2029", "inovaremanhwaversehindi"}  # hindi: visto 23/10 16:35 no x200ma
# 26/10 (dono: "o PC2 também nas tarefas dos notebooks: Veo, imagens..."): o PC2 entra (é "lento" = depois dos notebooks)
FLOW_FORA_DAS_MAQUINAS = set()


FLOW_IDADE = ROOT / "config" / "flow_idade.json"


def flow_idade_bloquear(perfil, horas=6, maquina=None):
    """04/11 dona: "a verificação de idade é da CONTA, não do PC". Medido nos logs (04/11): no DESKTOP as ~53 contas
    pediram idade; no x200ma/acer só 3 (manhwaverse ita/hindi/viet). Então guarda CONTA+MÁQUINA: a conta sai só
    daquela máquina; se 3+ contas diferentes pedirem na mesma máquina no prazo, é a máquina (IP/região) e ela sai."""
    try:
        d = json.loads(FLOW_IDADE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    agora = time.time()
    d = {k: v for k, v in d.items() if v > agora}
    d[f"{(perfil or '').lower()}@{maquina or '*'}"] = agora + horas * 3600
    FLOW_IDADE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _flow_idade():
    try:
        agora = time.time()
        return {k: v for k, v in json.loads(FLOW_IDADE.read_text(encoding="utf-8")).items() if v > agora}
    except (OSError, ValueError):
        return {}


def flow_idade_maquina_fora(maq):
    """3+ contas diferentes pediram idade nessa máquina dentro do prazo = problema da máquina."""
    return len({k.split("@")[0] for k in _flow_idade() if k.endswith("@" + maq)}) >= 3


def flow_idade_bloqueada(perfil, maquina=None):
    d, p = _flow_idade(), (perfil or "").lower()
    return f"{p}@*" in d or p in d or (maquina is not None and f"{p}@{maquina}" in d)


def maquinas_flow(perfil):
    """Máquinas onde o Flow (Veo vídeo/imagem) dessa conta pode rodar: as ativadas pelo `ativar` (`_flow`) + TODAS
    onde o Google da conta está logado (youtube=true no conferido: um login Google serve pro Flow também). Dono 23/10:
    "use o Veo em todas as contas que temos (TikTok e YouTube)"."""
    p = (perfil or "").lower()
    if p in FLOW_BLOQUEADAS or flow_idade_bloqueada(p):
        return []
    dados = _logins()
    achadas = set((dados.get("_flow") or {}).get(p, []))
    for maq, info in (dados.get(p) or {}).items():
        # 28/10: "google" também (o monitor do PC2 anota google=logado com youtube=None: 56 perfis ficavam fora do Flow)
        if isinstance(info, dict) and (info.get("youtube") or info.get("google")):
            achadas.add(maq)
    return [m for m in MAQUINAS if m in achadas and m not in FLOW_FORA_DAS_MAQUINAS
            and not flow_idade_bloqueada(p, m) and not flow_idade_maquina_fora(m)]


def contas_flow():
    """Todos os perfis com o Flow utilizável em alguma máquina (ordem do arquivo de logins)."""
    return [p for p in _logins() if not p.startswith("_") and maquinas_flow(p)]


_LIVRE_CACHE = {}


def _camera_agendada(nome):
    """28/10 (dona): horário fixo da câmera no desktop (D:\\video-fila\\maquinas.py AGENDA_CAMERA) -> texto, senão None."""
    if nome != "desktop":
        return None
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.append(r"D:\video-fila")
        import maquinas
        return maquinas.camera_agendada()
    except ImportError:
        return None


def maquina_livre(nome, cache_s=60):
    """A máquina responde e não está com outro Chrome aberto (1 conta por vez)? Lido pelo `estado` do chrome_conta,
    guardado 60 s (o Veo pergunta a cada escolha de conta)."""
    if "login" in reservado(nome).lower():  # 23/10 (dona): login aberto = nem Veo nem nada até terminar
        return False
    if _camera_agendada(nome):
        return False
    agora = time.time()
    if nome in _LIVRE_CACHE and agora - _LIVRE_CACHE[nome][0] < cache_s:
        return _LIVRE_CACHE[nome][1]
    livre = False
    try:
        r = Remoto(nome)
        txt = r._txt(r._ssh(f"{r.run} estado", timeout=20))
        j = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        livre = not j.get("aberto") and bool(j.get("chrome"))
        # 13/11 (dona: "x200ma parado há horas"): um Chrome de conta ficou aberto 20+ min sem ninguém usando e a
        # máquina contava como ocupada. Aberto há mais de CHROME_ESQUECIDO_MIN (25) sem login em curso e sem nenhum
        # processo daqui pedindo = esquecido: fecha (liberar) e a máquina volta. CHROME_ESQUECIDO_MIN=0 desliga.
        ab = j.get("aberto") or {}
        lim = float(os.environ.get("CHROME_ESQUECIDO_MIN", "25"))
        if ab and lim and not ab.get("login") and time.time() - float(ab.get("desde") or time.time()) > lim * 60:
            r._ssh(f"{r.run} liberar", timeout=40)
            r._ssh(f"pkill -f 'postador-worker/perfis/{ab.get('perfil', 'X_NADA_X')}'", timeout=20)
            livre = bool(j.get("chrome"))
    except Exception:  # noqa: BLE001
        livre = False
    _LIVRE_CACHE[nome] = (agora, livre)
    return livre


def _canais_parceiro():
    try:
        t = Path(r"D:\recapd-ambientes\producao\config\parceiro.json").read_text(encoding="utf-8")
        return {s.replace("_", "") for s in re.findall(r'"novo_(\w+)"', t)}
    except OSError:
        return set()


def _com_chrome():
    """Notebooks ligados e com Chrome (o Acer só depois do preparar-chrome)."""
    ok = []
    for nome in MAQUINAS:
        r = Remoto(nome)
        try:
            s = r._txt(r._ssh(f"{r.run} estado", timeout=90 if r.win else 25))
            if '"chrome": null' not in s and '"chrome"' in s:
                ok.append(nome)
        except subprocess.TimeoutExpired:
            pass
    return ok


def checar(perfil, nome="x200ma"):
    """Abre o perfil lá e só OLHA se o YouTube Studio e o TikTok Studio abrem logados. Grava em netbooks_logins.json."""
    from playwright.sync_api import sync_playwright
    r = Remoto(nome)
    res = {}
    try:
        r.ceder_veo()
        porta = r.abrir(perfil, sem_espera=True)
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = br.contexts[0].new_page()
            for rede, url in (("youtube", "https://studio.youtube.com"),
                              ("tiktok", "https://www.tiktok.com/tiktokstudio/upload"),
                              ("instagram", "https://www.instagram.com/")):
                try:
                    pg.goto(url, timeout=120000)
                    pg.wait_for_timeout(10000)
                    u = pg.url
                    m = re.search(r"/channel/(UC[\w-]{20,})", u)
                    # 23/10: a página precisa ser DAQUELA rede — se o goto não navegou, a URL ainda era a do Studio e o
                    # TikTok saía "logado" sem a dona ter entrado nele
                    dominio = {"youtube": "youtube.com", "tiktok": "tiktok.com", "instagram": "instagram.com"}[rede]
                    logado = dominio in u and "accounts.google.com" not in u and "login" not in u.lower()
                    if rede == "instagram":  # a home do Instagram deslogada mostra o formulário de entrar na própria URL
                        logado = logado and not pg.locator("input[name=username], input[name=email]").count()
                    if rede == "tiktok":  # deslogado o TikTok Studio mostra o botão de entrar em vez do envio
                        logado = logado and not pg.get_by_text(re.compile(r"^\s*(Entrar|Log in|Fazer login)\s*$")).count()
                    # 23/10: a página sozinha enganava (Instagram "logado" em 17 perfis sem nenhuma sessão; TikTok ativado
                    # onde não havia). Prova = o cookie de sessão da rede no perfil (só o nome; o valor não é lido)
                    if rede in ("tiktok", "instagram"):
                        logado = logado and any(c["name"] == "sessionid" and c["value"]
                                                for c in br.contexts[0].cookies(f"https://www.{dominio}"))
                    res[rede] = {"logado": logado, "canal": m.group(1) if m else None}
                except Exception as e:  # noqa: BLE001
                    res[rede] = {"logado": False, "erro": str(e)[:100]}
            # Google sozinho (conta só de TikTok não tem canal no YouTube): cookie de sessão do Google
            res["google"] = {"logado": any(c["name"] in ("SID", "__Secure-1PSID") and c["value"]
                                           for c in br.contexts[0].cookies("https://accounts.google.com"))}
            pg.close()
            br.close()
    except Exception as e:  # noqa: BLE001
        res = {"erro": str(e)[:200]}
    finally:
        r.fechar()
    if "erro" not in res:
        dados = _logins()
        dados.setdefault(perfil, {})[nome] = {"youtube": res["youtube"]["logado"], "tiktok": res["tiktok"]["logado"],
                                              "instagram": res["instagram"]["logado"],
                                              "google": res["google"]["logado"],
                                              "em": datetime.now().isoformat(timespec="minutes")}
        _politica().gravar_json(LOGINS, dados)
    print(f"{nome}: {json.dumps(res, ensure_ascii=False)}")
    return res


def _gravar_ativacao(perfil, maq_yt, maq_tt, maq_ig=()):
    pol = _politica()
    info = _mapa_perfis().get(perfil, {"youtube": [], "tiktok": [], "instagram": []})
    feito = []
    for arq, chaves, maqs, pegar in (
            (pol.CONFIG_DIR / "youtube_navegador.json", info["youtube"], maq_yt, lambda d: d.get("canais", {})),
            (pol.CONFIG_DIR / "reuso_plataformas.json", info["tiktok"], maq_tt,
             lambda d: (d.get("tiktok") or {}).get("contas", {})),
            (pol.CONFIG_DIR / "reuso_plataformas.json", info["instagram"], list(maq_ig),
             lambda d: (d.get("instagram") or {}).get("contas", {}))):
        if not chaves:
            continue
        dados = pol.ler_json(arq, {})
        for k in chaves:
            e = pegar(dados).get(k)
            if e is None:
                continue
            if maqs:
                e["maquina"], e["perfil_remoto"] = list(maqs), perfil
            else:
                e.pop("maquina", None)
                e.pop("perfil_remoto", None)
            feito.append(f"{k}: {', '.join(maqs) if maqs else 'só este PC'}")
        bkp = arq.with_name(arq.name + time.strftime(".bkp_%Y%m%d_%H%M%S"))
        bkp.write_bytes(arq.read_bytes())
        pol.gravar_json(arq, dados)
    for f in feito:
        log(f"ativação {perfil} -> {f}")
    return feito


def ativar(perfil):
    perfil = perfil.lower()
    if perfil not in _mapa_perfis():
        print(f"'{perfil}' não é perfil conhecido. Veja: python bin\\maquina_remota.py contas")
        return 1
    for nome in MAQUINAS:  # 23/10: o login acabou — solta a vez que o logar() pegou
        liberar(nome, quem=f"login {perfil}")
    maq_yt, maq_tt, maq_ig, maq_google = [], [], [], []
    antes = _logins().get(perfil, {})
    for nome in _com_chrome():
        res = checar(perfil, nome)
        if "erro" in res:  # não deu pra conferir (notebook ocupado/fora): vale o último resultado, não desativa
            ult = antes.get(nome) or {}
            print(f"{nome}: não conferi agora — mantenho o último resultado ({ult.get('em', 'nenhum')})")
            res = {r: {"logado": bool(ult.get(r))} for r in ("youtube", "tiktok", "instagram", "google")}
        if (res.get("google") or {}).get("logado"):
            # dona 23/10: ela loga só o Google; o TikTok entra depois, em lote, pelo tiktok_notebooks.py
            maq_google.append(nome)
        if (res.get("youtube") or {}).get("logado"):
            maq_yt.append(nome)
        if (res.get("tiktok") or {}).get("logado"):
            maq_tt.append(nome)
        if (res.get("instagram") or {}).get("logado"):
            maq_ig.append(nome)
    feito = _gravar_ativacao(perfil, maq_yt, maq_tt, maq_ig)
    # Flow (Veo) usa o MESMO login Google: ativado junto com o YouTube (dono: "os projetos que usam navegador podem
    # usar os mesmos cookies" — aqui o mesmo PERFIL logado no notebook, sem copiar cookie)
    dados = _logins()
    dados.setdefault("_flow", {})[perfil] = list(maq_yt)
    _politica().gravar_json(LOGINS, dados)
    if maq_yt:
        feito.append(f"Flow/Veo ({perfil}): {', '.join(maq_yt)}")
    if maq_google and not (maq_tt or maq_ig):
        feito.append(f"Google ({perfil}): {', '.join(maq_google)} — TikTok entra no lote do tiktok_notebooks.py")
    if not (maq_yt or maq_tt or maq_ig or maq_google):
        print(f"NÃO ATIVOU: {perfil} não está logado em nenhum notebook. Rode: python bin\\maquina_remota.py logar {perfil}")
        return 2
    print("ATIVADO:\n  " + "\n  ".join(feito))
    return 0


def contas():
    mapa, logins = _mapa_perfis(), _logins()
    pol = _politica()
    yt = pol.ler_json(pol.CONFIG_DIR / "youtube_navegador.json", {"canais": {}}).get("canais", {})
    print(f"{'#':>2} {'PERFIL':32} {'YOUTUBE':28} {'TIKTOK':4} LOGADO (yt/tt) | ATIVO")
    for i, (p, info) in enumerate(mapa.items(), 1):
        lg = " ".join(f"{m}:{'S' if v.get('youtube') else '-'}/{'S' if v.get('tiktok') else '-'}"
                      for m, v in logins.get(p, {}).items()) or "nenhum"
        ativo = sorted({m for s in info["youtube"] for m in _lista(yt.get(s, {}).get("maquina"))})
        print(f"{i:>2} {p:32} {','.join(info['youtube'])[:28]:28} {len(info['tiktok']):>4} {lg} | "
              f"{','.join(ativo) or '-'}")


def proxima():
    """Primeiro perfil (YouTube primeiro, na ordem do mapa) ainda sem login conferido em algum notebook com Chrome."""
    com = _com_chrome()
    if not com:
        print("Nenhum notebook ligado com Chrome agora (veja: python bin\\maquina_remota.py estado).")
        return None
    logins = _logins()
    for p, info in _mapa_perfis().items():
        rede = "youtube" if info["youtube"] else "tiktok" if info["tiktok"] else "instagram"
        falta = [m for m in com if not (logins.get(p, {}).get(m) or {}).get(rede)]
        if falta:
            print(f"PRÓXIMO: {p}  (e-mail {info['email'] or p + '@gmail.com'}; YouTube: {', '.join(info['youtube']) or '-'};"
                  f" TikTok: {', '.join(info['tiktok']) or '-'}) — falta em: {', '.join(falta)}")
            print(f"  1) python bin\\maquina_remota.py logar {p}\n  2) a dona entra na conta nos notebooks\n"
                  f"  3) python bin\\maquina_remota.py ativar {p}")
            return p
    print("Todos os perfis já estão logados nos notebooks com Chrome.")
    return None


def logar(perfil, maquinas=None):
    """Abre o Chrome do perfil NA TELA de cada notebook (ao mesmo tempo) pra dona entrar na conta. Sem senha daqui."""
    perfil = perfil.lower()
    insta = perfil.startswith("ig_")  # perfil do Instagram: login do próprio Instagram, não do Google
    url = "https://www.instagram.com/accounts/login/" if insta else "https://accounts.google.com"
    for nome in _lista(maquinas) or list(MAQUINAS):
        r = Remoto(nome)  # sem túnel nem porta de controle: com ela o Google recusa o login
        ocupar(nome, f"login {perfil}", 45)  # 23/10: um navegador por vez — telão e Veo esperam
        try:
            r.ceder_veo()  # dona 23/10: Veo ocupando o notebook sai na hora (refaz noutra máquina na próxima rodada)
            s = r._txt(r._ssh(f"{r.run} logar {_q(perfil, r.win)} 0 {_q(url, r.win)}", timeout=60))
            print(f"{nome}: " + ("Chrome de '%s' aberto na tela" % perfil if "PRONTO_LOGIN" in s
                                 else "não abriu (" + " ".join(s.split())[-160:] + ")"))
            if "PRONTO_LOGIN" in s and not insta and not r.win:
                # dona 23/10: o e-mail entra sozinho (pelo teclado da tela, sem porta de controle); a senha é dela
                time.sleep(12)
                email = (_mapa_perfis().get(perfil) or {}).get("email") or f"{perfil}@gmail.com"
                t = r._txt(r._ssh(f"python3 ~/postador-worker/teclado.py {_q(email, r.win)} --enter", timeout=60))
                print(f"{nome}: e-mail " + ("digitado" if "DIGITADO" in t else "não digitado: " + t[-100:]))
        except subprocess.TimeoutExpired:
            print(f"{nome}: não respondeu")
    print(("Em cada notebook: entre na conta do Instagram." if insta else
           "Em cada notebook: digite a senha do Google (o TikTok entra depois, em lote).") +
          f"\nFeche as janelas e rode: python bin\\maquina_remota.py ativar {perfil}")


def instalar():
    codigo = (BIN / "netbooks" / "chrome_conta.py").read_bytes().replace(b"\r\n", b"\n")
    for nome in MAQUINAS:
        r = Remoto(nome)
        if r.win:
            try:
                r._ssh('powershell -NoProfile -Command "New-Item -ItemType Directory -Force '
                       'C:\\postador-worker\\perfis,C:\\postador-worker\\entrada | Out-Null"', timeout=30)
                subprocess.run([SSH.replace("ssh.exe", "scp.exe"), "-q", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR",
                                str(BIN / "netbooks" / "chrome_conta.py"), f"{r.alvo}:C:/postador-worker/chrome_conta.py"],
                               capture_output=True, timeout=120, creationflags=SEM_JANELA)
                print(f"{nome}: {r._txt(r._ssh(f'{r.run} estado', timeout=60)).strip()[-300:]}")
            except subprocess.TimeoutExpired:
                print(f"{nome}: não respondeu")
            continue
        try:
            s = r._ssh(f"mkdir -p ~/postador-worker/perfis ~/postador-worker/entrada && cat > {SCRIPT} && "
                       f"python3 {SCRIPT} estado", entrada=codigo)
            print(f"{nome}: {r._txt(s).strip()}")
        except subprocess.TimeoutExpired:
            print(f"{nome}: não respondeu")


def preparar_chrome(nome, autorizado=False):
    """Chrome no notebook SEM sudo: baixa o .deb oficial do Google e extrai em ~/.local/chrome (não instala no sistema,
    não mexe no Firefox). Baixar programa precisa da autorização da dona: sem --dona-autorizou só mostra o plano."""
    if not autorizado:
        print(f"Vai baixar {CHROME_DEB} (~110 MB, Google oficial) no {nome} e extrair em ~/.local/chrome.\n"
              f"Só rode com a autorização da dona: python bin\\maquina_remota.py preparar-chrome {nome} --dona-autorizou")
        return 1
    r = Remoto(nome)
    cmd = (f"set -e; t=$(mktemp -d); (wget -q -O $t/c.deb {CHROME_DEB} || curl -fsSL -o $t/c.deb {CHROME_DEB}); "
           "rm -rf ~/.local/chrome; mkdir -p ~/.local/chrome; dpkg-deb -x $t/c.deb ~/.local/chrome; rm -rf $t; "
           "~/.local/chrome/opt/google/chrome/chrome --version; "
           "cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null || echo 0")
    s = r._ssh(cmd, timeout=1800)
    print(f"{nome}: {r._txt(s).strip()}")
    log(f"preparar-chrome {nome}: rc={s.returncode}")
    return s.returncode


NSN = Path(r"D:\projeto-navegador-sem-navegador")


NSN_WIN = r"C:\postador-worker\nsn"
NSN_WIN_PY = NSN_WIN + r"\venv\Scripts\python.exe"  # venv próprio (29/10): não usa nem mexe no Python do hipercool


def _instalar_nsn_win(r, tgz):
    """Windows (PC2): scp do pacote, tar do próprio Windows, preserva cookies\\ e venv\\ de lá. O venv é criado uma vez
    (python do usuário + curl_cffi/websocket-client/requests)."""
    if not r.nsn_win_pronto():
        print(f"{r.nome}: sem o venv do nsn ({NSN_WIN_PY}) — criar antes (ver PLANO_00h40.md)")
        return
    try:
        subprocess.run([SSH.replace("ssh.exe", "scp.exe"), "-q", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", str(tgz),
                        f"{r.alvo}:C:/postador-worker/nsn_worker.tgz"], check=True, capture_output=True, timeout=300,
                       creationflags=SEM_JANELA)
        ps = (r"Set-Location C:\postador-worker; tar -xzf nsn_worker.tgz; "
              r"robocopy nsn_worker C:\postador-worker\nsn /E /XD cookies venv saida /NFL /NDL /NJH /NJS | Out-Null; "
              r"Remove-Item -Recurse -Force nsn_worker, nsn_worker.tgz; Set-Location C:\postador-worker\nsn; "
              r"New-Item -ItemType Directory -Force saida | Out-Null; "
              r"& .\venv\Scripts\python.exe -c 'import services.instagram.postar, services.veo_flow.flow_gerar, os; print(''nsn ok'', len(os.listdir(''cookies'')), ''cookies'')'")
        out = r._ssh('powershell -NoProfile -Command "' + ps + '"', timeout=180)
        print(f"{r.nome}: {' '.join(r._txt(out).split())[-200:]}")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        print(f"{r.nome}: instalação falhou ({type(e).__name__})")


FLOW_URL = "https://labs.google/fx/pt/tools/flow"


def colher_flow(perfil, maquinas=None):
    """29/10 (D30): grava NA máquina os cookies Google do perfil (cookies/cofre_<perfil>.json de lá) para a saúde do Flow
    por HTTP (saude_flow.py). Abre o Chrome do perfil lá só o tempo do colher (respeita a vez da máquina: 1 Chrome por
    vez). Na produção isto acontece sozinho a cada vídeo gerado por HTTP (flow_gerar.FlowGerador.colher)."""
    perfil = perfil.lower()
    alvo = _lista(maquinas) or maquinas_flow(perfil)
    for nome in alvo:
        r = Remoto(nome)
        # 30/10 (D38b): no desktop (ssh que cai) cada conexão a mais é uma chance de falhar — o abrir já responde se a
        # máquina não está lá. A vez de OUTRO trabalho (o Veo reserva as máquinas a cada 12 min) não barra: o
        # chrome_conta já garante 1 Chrome por vez (OCUPADO na hora); só login aberto pela dona barra.
        if not MAQUINAS[nome].get("puxar_http") and not r.vivo():
            print(f"{nome}: não respondeu")
            continue
        if "login" in reservado(nome).lower():
            print(f"{nome}: com a vez de '{reservado(nome)}' — pulei")
            continue
        try:
            r.abrir(perfil, FLOW_URL, sem_espera=True, tunel=False)  # o colher roda LÁ: túnel não serve pra nada
            ok = r.nsn_colher(perfil, FLOW_URL)
            print(f"{nome}: {'colhido' if ok else 'NÃO colheu'} {perfil}")
        except Exception as e:  # noqa: BLE001
            print(f"{nome}: {type(e).__name__}: {str(e)[:120]}")
        finally:
            r.fechar()
    return 0


def instalar_nsn(maquinas=None):
    """29/10 (D23): empacota o worker do nsn (tools\\empacotar_worker.py: código + modelos, SEM cookies) e atualiza
    ~/postador-worker/nsn nas máquinas Linux, preservando a pasta cookies/ de lá. Windows (PC2/desktop): robocopy
    preservando cookies\\ e venv\\ (o venv é criado uma vez à mão). Desde 29/10 (D30) o pacote leva o Flow/Veo por HTTP."""
    import tarfile
    subprocess.run([sys.executable, "-X", "utf8", str(NSN / "tools" / "empacotar_worker.py")], check=True, cwd=str(NSN),
                   creationflags=SEM_JANELA, timeout=120)
    tgz = Path(tempfile.gettempdir()) / "nsn_worker.tgz"
    with tarfile.open(tgz, "w:gz") as t:
        t.add(NSN / "dist" / "nsn_worker", arcname="nsn_worker")
    for nome in _lista(maquinas) or list(MAQUINAS):
        r = Remoto(nome)
        if r.win:
            _instalar_nsn_win(r, tgz)
            continue
        try:
            with open(tgz, "rb") as f:
                r._ssh("cat > ~/nsn_worker.tgz", entrada=f, timeout=120)
            out = r._ssh("mkdir -p ~/postador-worker && cd ~/postador-worker && tar -xzf ~/nsn_worker.tgz && "
                         "mkdir -p nsn/cookies nsn/saida && cp -rn nsn/cookies/. nsn_worker/cookies/ 2>/dev/null; "
                         "cp -rn nsn/saida/. nsn_worker/saida/ 2>/dev/null; rm -rf nsn && "
                         "mv nsn_worker nsn && rm ~/nsn_worker.tgz && cd nsn && python3 -c \"import curl_cffi, websocket; "
                         "import services.instagram.postar, services.veo_flow.flow_gerar; "
                         "print('nsn ok', len(__import__('os').listdir('cookies')), 'cookies')\"",
                         timeout=120)
            print(f"{nome}: {' '.join(r._txt(out).split())[-200:]}")
        except subprocess.TimeoutExpired:
            print(f"{nome}: não respondeu")
    tgz.unlink(missing_ok=True)
    return 0


def main(a):
    if not a:
        print(__doc__)
        return 1
    cmd, resto = a[0], a[1:]
    if cmd == "instalar":
        return instalar()
    if cmd == "instalar-nsn":  # instalar-nsn [maquina ...]
        return instalar_nsn(resto)
    if cmd == "colher-flow" and resto:  # colher-flow <perfil> [maquina ...]: cookies Google p/ a saúde do Flow HTTP
        return colher_flow(resto[0], resto[1:])
    if cmd == "saude-flow":  # saude-flow [maquina ...]: quem está logado no Flow em cada máquina (HTTP lá)
        for nome in _lista(resto) or list(MAQUINAS):
            r = Remoto(nome)
            if not r.vivo():
                print(f"{nome}: não respondeu")
                continue
            for it in r.nsn_flow_saude():
                print(f"{nome:<8} {it['perfil']:<30} {'vivo' if it.get('vivo') else ('?' if it.get('vivo') is None else 'MORTO'):<6} {it.get('obs', '')}")
        return 0
    if cmd == "ocupar" and len(resto) >= 2:  # ocupar <maq> "<motivo>" [minutos=30]
        ocupar(resto[0], resto[1], float(resto[2]) if len(resto) > 2 else 30)
        return 0
    if cmd == "liberar" and resto:
        liberar(resto[0])
        return 0
    if cmd == "vez":  # quem está com a vez de cada máquina
        for nome in MAQUINAS:
            print(f"{nome}: {reservado(nome) or 'livre'}")
        return 0
    if cmd == "estado":
        for nome in MAQUINAS:
            r = Remoto(nome)
            try:
                print(f"{nome}: {r._txt(r._ssh(f'{r.run} estado', timeout=25)).strip()}")
            except subprocess.TimeoutExpired:
                print(f"{nome}: não respondeu")
        return 0
    if cmd == "contas":
        return contas()
    if cmd == "proxima":
        proxima()
        return 0
    if cmd == "logar" and resto:
        return logar(resto[0], resto[1:])
    if cmd == "checar" and resto:
        for nome in _lista(resto[1:]) or _com_chrome():
            checar(resto[0].lower(), nome)
        return 0
    if cmd == "ativar" and resto:
        return ativar(resto[0])
    if cmd == "desativar" and resto:
        _gravar_ativacao(resto[0].lower(), [], [], [])
        dados = _logins()
        (dados.get("_flow") or {}).pop(resto[0].lower(), None)
        _politica().gravar_json(LOGINS, dados)
        return 0
    if cmd == "preparar-chrome" and resto:
        return preparar_chrome(resto[0], "--dona-autorizou" in resto)
    print(__doc__)
    return 1


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]) or 0)
