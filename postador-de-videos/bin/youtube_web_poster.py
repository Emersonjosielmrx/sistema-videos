#!/usr/bin/env python3
"""youtube_web_poster.py — posta no YouTube PELO NAVEGADOR (YouTube Studio), sem a Data API.

Mesmo jeito do tiktok_cdp_poster.py: abre o Chrome REAL com um perfil dedicado já logado na conta do canal
(D:\\logins-google\\chrome-profiles\\<perfil>), liga o Playwright por fora (CDP) e faz o upload no Studio como uma
pessoa faria: arquivo, título, descrição, "não é para crianças", tags, conteúdo alterado (IA), visibilidade ou
agendamento. Mesmos argumentos e mesma última linha "STATUS: <status> <info>" do youtube_poster.py, então
politica.postar_youtube troca um pelo outro (canal a canal, ver config/youtube_navegador.json "usar").

A política vale igual: parada geral, canal bloqueado, cota do dia, aprovação humana, intervalo entre vídeos.

Mapa canal -> perfil/porta/ID do canal: config/youtube_navegador.json (montado com --montar-mapa).

Uso:
    python bin/youtube_web_poster.py --montar-mapa                  # cria/atualiza o mapa (lê IDs dos canais)
    python bin/youtube_web_poster.py --checar [--canal X]           # perfil abre o Studio logado no canal certo?
    python bin/youtube_web_poster.py --logar <slug>                 # abre o Chrome do perfil p/ você logar à mão
    python bin/youtube_web_poster.py --video X.mp4 --titulo "..." --descricao "..." --tags "a,b" --canal <id|nome>
        [--privacy public|private|unlisted] [--publish-at RFC3339] [--sintetico] [--projeto manhwa-react]
        [--ensaio]   # faz tudo e PARA antes do botão final (fica rascunho; imprime o ID p/ apagar)
        [--maiores-18]  # marca "restringir a maiores de 18" (canal com "maiores_18": true no mapa marca sempre)

Restrição de idade: canal com "maiores_18": true em config/youtube_navegador.json sobe TODO vídeo com Público >
Restrição de idade (avançado) > "Sim, restringir a maiores de 18". Se não conseguir marcar, não sobe.

Agendamento: o Studio só aceita horário em passos de 15 min; o horário pedido é arredondado PARA CIMA e o
horário real vai no ledger/STATUS.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import politica  # noqa: E402

MAPA_FILE = politica.CONFIG_DIR / "youtube_navegador.json"
PERFIS_DIR = Path(r"D:\logins-google\chrome-profiles")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SHOTS = politica.ROOT / "logs" / "yt_web"
_CONTA = None  # (slug, nome) do canal desta execução — _canal_e_mapa grava, _shot usa na trava_conta (05/11)
LOCK = politica.ROOT / "logs" / "yt_web.lock"
PORTA_BASE = 9400
REMOTO = None  # maquina_remota.Remoto quando o canal posta pelo Chrome de outra máquina (X200MA)
FINAL_CLICADO = False  # o botão final (Agendar/Publicar) já foi clicado nesta tentativa
ARQUIVO_ENVIADO = False  # o vídeo já foi escolhido no Studio nesta tentativa (falha = 1 rascunho)
EXIT_OK, EXIT_USO, EXIT_FALHA, EXIT_BLOQUEADO = 0, 1, 2, 5
STATUS_BLOQUEIO = {"parado": "parado", "canal_bloqueado": "morto", "cota_diaria": "cota",
                   "nao_aprovado": "nao_aprovado", "reservado": "reservado", "limite": "limite",
                   "advertencias": "advertencias"}
MESES_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


class Falha(Exception):
    def __init__(self, status, msg):
        super().__init__(msg)
        self.status = status


def _fim(status, info="", code=EXIT_OK):
    print(f"STATUS: {status} {info}".rstrip(), flush=True)
    sys.exit(code)


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


# ─────────────────────────── mapa canal -> perfil ──────────────────────────
def ler_mapa():
    return politica.ler_json(MAPA_FILE, {"canais": {}})


def entrada_do_cred(cred_id, mapa=None):
    """Entrada do mapa (por slug da rede) para um id de credencial (aliases do mesmo canal contam)."""
    mapa = mapa or ler_mapa()
    for slug, e in mapa.get("canais", {}).items():
        if cred_id in e.get("creds", []):
            return slug, e
    return None, None


def usar_navegador(cred_id):
    _, e = entrada_do_cred(cred_id)
    return bool(e and e.get("usar"))


def montar_mapa():
    """Cria/atualiza config/youtube_navegador.json: para cada canal ativo da rede, o e-mail da conta, o perfil
    dedicado do Chrome (pasta com o nome do e-mail, se existir), uma porta fixa e o ID do canal (UC...). O ID é
    lido UMA vez pela API (leitura, 1 unidade); depois o poster não usa API. Preserva "usar" e ajustes manuais."""
    sys.path.insert(0, str(politica.BIN))
    import youtube_poster as yp  # só para ler o ID do canal
    mapa = ler_mapa()
    canais = mapa.setdefault("canais", {})
    creds = {c["id"]: c for c in politica.carregar_creds()}
    perfis = {p.name.casefold(): p.name for p in PERFIS_DIR.iterdir() if p.is_dir()}
    usadas = {e.get("porta") for e in canais.values()}
    for i, ch in enumerate(politica.rede().get("canais", [])):
        if ch.get("status") != "ativo":
            continue
        slug = ch["slug"]
        e = canais.setdefault(slug, {"usar": False})
        e["nome"], e["handle"], e["creds"] = ch["nome"], ch.get("handle"), ch.get("creds", [])
        cred = next((creds[c] for c in e["creds"] if c in creds), None)
        e["email"] = (cred or {}).get("email")
        if not e.get("perfil"):
            pre = (e["email"] or "").split("@")[0].casefold()
            e["perfil"] = perfis.get(pre) or f"yt_{slug}"
        e["perfil_existe"] = (PERFIS_DIR / e["perfil"]).is_dir()
        if not e.get("porta"):
            p = PORTA_BASE + i
            while p in usadas:
                p += 1
            e["porta"] = p
            usadas.add(p)
        if not e.get("channel_id") and cred:
            try:
                tok = yp.refresh_access_token(cred)
                req = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=id&mine=true",
                                             headers={"Authorization": f"Bearer {tok}"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    e["channel_id"] = json.loads(r.read())["items"][0]["id"]
            except Exception as ex:  # noqa: BLE001
                print(f"  {slug}: sem ID do canal ({str(ex)[:80]}) - preencha channel_id à mão")
        print(f"  {slug:22} {str(e.get('channel_id')):26} perfil={e['perfil']:34} "
              f"{'ok' if e['perfil_existe'] else 'FALTA LOGAR (--logar ' + slug + ')'}  usar={e['usar']}")
    mapa["_leia"] = ("usar=true faz politica.postar_youtube subir esse canal pelo navegador (youtube_web_poster.py) "
                     "em vez da API. perfil = pasta em D:/logins-google/chrome-profiles; porta CDP fixa por canal.")
    politica.gravar_json(MAPA_FILE, mapa)
    print(f"mapa gravado: {MAPA_FILE}")


# ─────────────────────────── Chrome ────────────────────────────────────────
def _cdp_vivo(porta):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=2)
        return True
    except Exception:  # noqa: BLE001
        return False


def _cofre():
    """Cofre de logins (D:/logins-google/cofre.py): 1 perfil por conta, compartilhado entre os projetos."""
    if r"D:\logins-google" not in sys.path:
        sys.path.insert(0, r"D:\logins-google")
    import cofre
    return cofre


def _proxy_da_conta_kaggle(email):
    """12/11 (dona: as contas novas são "do canal E do Kaggle; o Kaggle acessa com proxy"): a regra do 2º banimento
    (09/11) é a MESMA conta Google aparecer em 2 IPs (proxy no Kaggle + casa no Flow/YouTube). Conta que está no pool do
    Kaggle com proxy_fixo (rnprmtfo-N) abre o Chrome do YouTube pela ponte desse MESMO IP — a conta só existe num IP.
    Ponte fora = Falha (nunca posta pela casa). Conta fora do pool = [] (como antes)."""
    import json
    import socket
    try:
        pool = json.loads(Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json").read_text("utf-8"))
    except (OSError, ValueError):
        return []
    c = next((x for x in pool.get("contas", []) if str(x.get("cofre") or "").lower() == email.lower()), None)
    if not c or not c.get("proxy_fixo") or "rnprmtfo-" not in c["proxy_fixo"]:
        return []
    n = int(c["proxy_fixo"].split("rnprmtfo-", 1)[1].split(":", 1)[0])
    porta = 18300 + n
    try:
        socket.create_connection(("127.0.0.1", porta), timeout=2).close()
    except OSError:
        subprocess.Popen([sys.executable, r"D:\recapd-ambientes\producao\colab\ponte_proxy_fixo.py", str(n), str(porta)],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for _ in range(20):
            time.sleep(1)
            try:
                socket.create_connection(("127.0.0.1", porta), timeout=2).close()
                break
            except OSError:
                continue
        else:
            raise Falha("erro", f"ponte do proxy rnprmtfo-{n} de {email} não subiu — não posto pela internet de casa")
    log(f"  {email}: conta do Kaggle — YouTube pelo MESMO IP fixo (rnprmtfo-{n})")
    return [f"--proxy-server=http://127.0.0.1:{porta}", "--proxy-bypass-list=<-loopback>",
            "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]


def abrir_conta(e, url="about:blank", visivel=False):
    """Abre (ou entra no já aberto) o Chrome da conta do canal pelo cofre; atualiza e['porta'] com a porta real.
    Conta fora do cofre: usa perfil/porta antigos do mapa."""
    cf = _cofre()
    try:
        email, c = cf.conta(e.get("email") or "")
    except KeyError:
        return abrir_chrome(e["perfil"], e["porta"], url, visivel)
    if not Path(c["pasta"]).exists():
        raise Falha("morto", f"conta {email} sem login no cofre (python D:\\logins-google\\cofre.py logar {c['apelido']})")
    extra = _proxy_da_conta_kaggle(email)  # 12/11: conta do Kaggle com canal sai SÓ pelo IP fixo dela (o mesmo do Kaggle)
    porta, proc = cf.abrir(email, url, visivel, extra=extra)
    e["porta"], e["perfil"] = porta, c["pasta"]
    return proc


def abrir_chrome(perfil, porta, url="about:blank", visivel=False):
    """Abre o Chrome real no perfil dedicado com CDP. Devolve o processo (None se já estava aberto)."""
    if _cdp_vivo(porta):
        return None
    pasta = PERFIS_DIR / perfil
    pasta.mkdir(parents=True, exist_ok=True)
    pos = "--window-position=60,40" if visivel else "--window-position=-2000,0"
    proc = subprocess.Popen([CHROME, f"--remote-debugging-port={porta}", f"--user-data-dir={pasta}",
                             "--no-first-run", "--no-default-browser-check", "--remote-allow-origins=*",
                             "--window-size=1280,900", pos, "--disable-background-timer-throttling",
                             "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows", url])
    for _ in range(40):
        if _cdp_vivo(porta):
            return proc
        time.sleep(0.5)
    raise Falha("erro", f"Chrome não abriu a porta {porta}")


def soltar(br, proc):
    """Desconecta do Chrome. Se fomos NÓS que abrimos, fecha pelo CDP (fechamento normal grava os cookies: o Google
    renova os de sessão e perder a renovação desloga o perfil com o tempo). Chrome aberto por outro fica aberto."""
    try:
        if proc:
            br.new_browser_cdp_session().send("Browser.close")
    except Exception:  # noqa: BLE001
        pass
    try:
        br.close()
    except Exception:  # noqa: BLE001
        pass


def fechar_chrome(proc, e=None):
    """Garantia: espera o Chrome que abrimos fechar (soltar já pediu); se não fechar em 15 s, mata. Depois limpa o
    cache do perfil se passou do limite do cofre (perfil leve; login fica)."""
    if not proc:
        return
    try:
        proc.wait(timeout=15)
    except Exception:  # noqa: BLE001
        try:
            proc.terminate()
            proc.wait(timeout=15)
        except Exception:  # noqa: BLE001
            pass
    if e and e.get("perfil"):
        try:
            cf = _cofre()
            pasta = Path(e["perfil"])
            if pasta.is_absolute() and cf._tamanho(pasta) / 1e6 > cf.LIMITE_CACHE_MB:
                cf.limpar_pasta(pasta)
        except Exception:  # noqa: BLE001
            pass


def _pid_vivo(pid):
    """Windows: o processo ainda existe? (os.kill(pid, 0) no Windows MATA o processo — não usar)."""
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    except Exception:  # noqa: BLE001  (sem como saber: trata como vivo)
        return True


class Trava:
    """Um upload pelo navegador por vez (vários Chromes subindo juntos derrubam a máquina). 21/10: grava o PID de quem
    pegou; se esse processo morreu (morto por prazo, queda) a trava é solta na hora — antes ficava presa até 3 h e
    parou a postagem de 09:24 a 10:54.
    22/10: trava por MÁQUINA — o upload pelo X200MA não espera o deste PC (cada um só tem um Chrome por vez)."""
    def __init__(self, arquivo=None):
        self.lock = arquivo or LOCK

    def _minha_vez(self):
        """02/11 (Comédia Noturna perdeu 4 vezes seguidas): a trava não tinha ordem — quem tentava no segundo em que
        ela soltava ganhava. Agora fila de senhas: cada um grava <chegada>_<pid> em <trava>_fila/; só a senha mais
        antiga de processo VIVO tenta pegar a trava (senha de processo morto é apagada)."""
        vivas = []
        for s in sorted(self.fila.glob("*_*")):
            pid = s.name.split("_")[-1]
            if pid.isdigit() and (pid == str(os.getpid()) or _pid_vivo(pid)):
                vivas.append(s)
            else:
                s.unlink(missing_ok=True)
        return not vivas or vivas[0] == self.senha

    def __enter__(self):
        LOCK = self.lock  # noqa: N806
        self.fila = LOCK.parent / (LOCK.stem + "_fila")
        self.fila.mkdir(parents=True, exist_ok=True)
        self.senha = self.fila / f"{time.time_ns()}_{os.getpid()}"
        self.senha.touch()
        try:
            return self._esperar(LOCK)
        finally:
            self.senha.unlink(missing_ok=True)

    def _esperar(self, LOCK):  # noqa: N803
        # 05/11: a postagem de longos em paralelo esperava só 40 min a vez do PC1 e desistia, jogando fora o
        # download (5-7 GB) e a preparação. YT_TRAVA_ESPERA_MIN (postar_longos põe 240); sem ela, 40 como antes.
        espera_min = float(os.environ.get("YT_TRAVA_ESPERA_MIN", "40"))
        for _ in range(int(espera_min * 6)):
            if not self._minha_vez():
                time.sleep(10)
                continue
            try:
                self.fd = open(LOCK, "x")
                self.fd.write(f"{os.getpid()} {datetime.now().isoformat(timespec='seconds')}")
                self.fd.flush()
                return self
            except FileExistsError:
                try:
                    dono = LOCK.read_text(encoding="utf-8", errors="replace").split()
                    morto = bool(dono) and dono[0].isdigit() and not _pid_vivo(dono[0])
                    if not morto and not (dono and dono[0].isdigit()):
                        # trava sem PID (versão antiga do código): dono vivo tem o arquivo ABERTO e o Windows não deixa
                        # renomear; renomeou = ninguém segura (órfã) -> solta
                        tmp = LOCK.with_suffix(".teste")
                        os.rename(LOCK, tmp)
                        os.rename(tmp, LOCK)
                        morto = time.time() - LOCK.stat().st_mtime > 60
                except OSError:
                    morto = False
                try:
                    idade = time.time() - LOCK.stat().st_mtime
                    velha = idade > 3 * 3600
                except OSError:  # o dono soltou a trava entre o "existe" e o stat: tenta pegar de novo
                    continue
                # 02/11: o metricas_rede travou (node do Playwright parado, 0 CPU) segurando a trava 10 h — nenhum
                # upload nem troca de visibilidade andou (dona esperando o vídeo abrir). Dono vivo há > 2 h que NÃO é
                # upload (metricas/extras) = travado: mata a árvore dele e solta. Upload de longo (1080p) fica até 3 h.
                if not morto and not velha and idade > 2 * 3600 and dono and dono[0].isdigit():
                    try:
                        cmdl = subprocess.run(["powershell", "-NoProfile", "-Command",
                                               f"(Get-CimInstance Win32_Process -Filter 'ProcessId={dono[0]}').CommandLine"],
                                              capture_output=True, text=True, timeout=30,
                                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
                        if "youtube_web_poster" not in cmdl:
                            subprocess.run(["taskkill", "/PID", dono[0], "/T", "/F"], capture_output=True, timeout=30,
                                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                            morto = True
                    except Exception:  # noqa: BLE001
                        pass
                if morto or velha:
                    try:
                        LOCK.unlink(missing_ok=True)
                        continue
                    except OSError:  # arquivo aberto = o dono está vivo (Windows não deixa apagar): espera
                        pass
                time.sleep(10)
        raise Falha("erro", f"outro upload pelo navegador está travando há {espera_min:.0f} min")

    def __exit__(self, *a):
        self.fd.close()
        self.lock.unlink(missing_ok=True)


# ─────────────────────────── Studio ────────────────────────────────────────
def _shot(pg, nome):
    SHOTS.mkdir(parents=True, exist_ok=True)
    p = SHOTS / f"{datetime.now():%Y%m%d_%H%M%S}_{nome}.png"
    try:
        pg.screenshot(path=str(p))
    except Exception:  # noqa: BLE001
        return None
    if _CONTA and re.search(r"falh|bloqueio|sem_|nao_|TRAVADO|erro", nome):
        try:  # 05/11: print de falha = confere se é tela de punição do YouTube e trava o canal (trava_conta.py)
            import trava_conta
            trava_conta.ver_tela(pg, _CONTA[0], _CONTA[1], p)
        except Exception:  # noqa: BLE001
            pass
    return p


def pedindo_login(pg):
    """Na página do Google com campo de e-mail/senha ou escolha de conta = sessão morta de verdade."""
    if "accounts.google.com" not in pg.url:
        return False
    try:
        return pg.locator("input[type=email], input[type=password], #identifierId, [data-identifier]").first.is_visible()
    except Exception:  # noqa: BLE001
        return False


def esperar_assentar(pg, maximo_s=35):
    """Espera os redirecionamentos acabarem. Sessão parada passa rápido por accounts.google.com para renovar e
    volta sozinha: olhar a URL cedo demais dá 'deslogado' falso (aconteceu em 12/10 com 9 perfis vivos)."""
    ultimo, desde = None, time.time()
    fim = time.time() + maximo_s
    while time.time() < fim:
        if pedindo_login(pg):
            return "login"
        if pg.url != ultimo:
            ultimo, desde = pg.url, time.time()
        elif "accounts.google.com" not in pg.url and time.time() - desde >= 4:
            return "ok"
        time.sleep(1)
    return "login" if pedindo_login(pg) or "accounts.google.com" in pg.url else "ok"


SEM_PERMISSAO = re.compile(r"não tem permissão para acessar|don'?t have permission to access|do not have permission", re.I)


def _nome_canal(pg):
    """Nome do canal que o Studio mostra em 'Seu canal' (vazio se nao achou)."""
    try:
        m = re.search(r"(?:Seu canal|Your channel)\s*\n\s*(.+)", pg.locator("body").inner_text(timeout=5000))
    except Exception:  # noqa: BLE001
        return ""
    return m.group(1).strip() if m else ""


def _abrir_studio(pg, channel_id, caminho=""):
    url = f"https://studio.youtube.com/channel/{channel_id}{caminho}"
    pg.goto(url, wait_until="domcontentloaded", timeout=90000)
    if esperar_assentar(pg) == "login":
        raise Falha("morto", "perfil do navegador não está logado (rode --logar)")
    pg.wait_for_timeout(2000)
    if channel_id not in pg.url:
        raise Falha("erro", f"a conta logada não abre o canal {channel_id} (url={pg.url[:120]})")
    if "/copyright/interstitial" in pg.url:  # advertencia de direitos autorais: o Studio nao sai dessa pagina
        raise Falha("erro", "o Studio está parado no aviso de advertência de direitos autorais: o dono precisa abrir o "
                            "Studio do canal, ler/fechar o aviso (e fazer o Curso de direitos autorais)")
    # a URL com o id NAO basta: conta sem acesso ao canal fica na mesma URL com a pagina "voce nao tem permissao" (13/10)
    fim = time.time() + 15
    while time.time() < fim:
        try:
            corpo = pg.locator("body").inner_text(timeout=5000)
        except Exception:  # noqa: BLE001
            corpo = ""
        if SEM_PERMISSAO.search(corpo):
            raise Falha("morto", f"a conta logada não tem permissão no canal {channel_id} (logar a conta dona do canal)")
        if re.search(r"Seu canal|Your channel", corpo) or pg.locator("ytcp-uploads-dialog").count():
            return
        pg.wait_for_timeout(1000)


def _idioma(pg):
    lang = ""
    for _ in range(10):  # o Studio ainda pode estar redirecionando
        try:
            pg.wait_for_load_state("domcontentloaded")
            lang = (pg.evaluate("document.documentElement.lang") or "").lower()
            break
        except Exception:  # noqa: BLE001
            pg.wait_for_timeout(1500)
    return "pt" if lang.startswith("pt") else "en" if lang.startswith("en") else lang


def _escrever(pg, seletor, texto):
    caixa = pg.locator(seletor).first
    caixa.wait_for(state="visible", timeout=60000)
    caixa.click()
    pg.keyboard.press("Control+A")
    pg.keyboard.press("Delete")
    pg.keyboard.insert_text(texto)
    pg.wait_for_timeout(600)


def _clicar_se_existe(pg, seletor, timeout=4000):
    loc = pg.locator(seletor).first
    try:
        loc.wait_for(state="visible", timeout=timeout)
    except Exception:  # noqa: BLE001
        return False
    loc.click()
    pg.wait_for_timeout(500)
    return True


def _texto_dialogo(pg):
    try:
        return pg.locator("ytcp-uploads-dialog").first.inner_text(timeout=3000)
    except Exception:  # noqa: BLE001
        return ""


def _fechar_sugestoes(pg):
    """22/10: em contas com "Hashtags sugeridas" a lista (#shorts, #shortsfeed...) abre POR CIMA da caixa do título e o
    clique no título ficava bloqueado 30 s (TimeoutError) com o arquivo já enviado: cada tentativa deixava mais um envio
    privado no canal e gastava o limite diário da conta (ForjaReact: 126 tentativas do mesmo vídeo em 18-22/10).
    01:26 do mesmo dia: a lista do "#shorts" do TÍTULO abriu ao lado da descrição; o clique no título passava e a lista
    continuava aberta, tampando o próximo clique. Por isso o 1º clique é sempre no cabeçalho do diálogo (texto parado,
    fora das duas caixas), que fecha a lista do título e a da descrição; depois o mesmo clique no título de antes."""
    titulo = pg.locator("#title-textarea").first
    try:
        b = pg.locator("ytcp-uploads-dialog tp-yt-paper-dialog, ytcp-uploads-dialog #dialog").first.bounding_box(timeout=3000)
        if b:
            pg.mouse.click(b["x"] + 24, b["y"] + 24)
            pg.wait_for_timeout(500)
    except Exception:  # noqa: BLE001 — sem o cabeçalho: segue pro clique no título
        pass
    try:
        titulo.click(timeout=5000)
        return
    except Exception:  # noqa: BLE001 — lista de hashtags ainda por cima do título
        pass
    _shot(pg, "hashtag_por_cima")
    pg.keyboard.press("Escape")  # com a lista aberta o Escape só fecha a lista
    pg.wait_for_timeout(600)
    titulo.click(timeout=10000)


def _video_id(pg):
    hrefs = pg.eval_on_selector_all(
        "ytcp-uploads-dialog a[href]", "els => els.map(e => e.href)") or []
    for h in hrefs:
        m = re.search(r"(?:youtu\.be/|/shorts/|watch\?v=|/video/)([\w-]{11})", h)
        if m:
            return m.group(1)
    return None


def _marcado(pg, seletor):
    return _loc_marcado(pg.locator(seletor).first)


def _loc_marcado(loc):
    try:
        return (loc.get_attribute("aria-checked", timeout=2000) == "true"
                or loc.get_attribute("checked", timeout=2000) is not None)
    except Exception:  # noqa: BLE001
        return None


def _so_texto(s):
    return re.sub(r"\s+", " ", s or "").strip()


IDADE_ABRIR = re.compile(r"restri[cç][aã]o de idade|age restriction", re.I)
IDADE_SIM = re.compile(r"^\s*(sim|yes)\b.*(maiores de 18|over 18|18 anos|18\+)", re.I | re.S)


def _radio_maiores_18(pg):
    """Opção 'Sim, restringir meu vídeo a espectadores maiores de 18 anos': pelo name do Studio e, se o name
    mudar, pelo texto da opção."""
    por_nome = pg.locator("[name=VIDEO_AGE_RESTRICTION_SELF]").first
    if por_nome.count():
        return por_nome
    return pg.locator("tp-yt-paper-radio-button, [role=radio]").filter(has_text=IDADE_SIM).first


def _abrir_secao_idade(pg, espera_s=8):
    """Clica no primeiro 'Restrição de idade (avançado)' VISÍVEL (o mesmo texto pode estar em ajuda escondida)."""
    fim = time.time() + espera_s
    while time.time() < fim:
        for cand in pg.get_by_text(IDADE_ABRIR).all():
            try:
                if cand.is_visible():
                    cand.scroll_into_view_if_needed()
                    cand.click()
                    pg.wait_for_timeout(1000)
                    return True
            except Exception:  # noqa: BLE001
                continue
        pg.wait_for_timeout(500)
    return False


def _marcar_maiores_18(pg):
    """Público > Restrição de idade (avançado) > Sim. A seção vem fechada: abre pelo texto do botão (só se a opção
    ainda não aparece, senão o clique fecharia). Não ficou marcado = Falha: canal +18 nunca sobe sem a restrição."""
    radio = _radio_maiores_18(pg)
    if not (radio.count() and radio.is_visible()):
        _abrir_secao_idade(pg)
        radio = _radio_maiores_18(pg)
    try:
        radio.wait_for(state="visible", timeout=8000)
        radio.scroll_into_view_if_needed()
        radio.click()
        pg.wait_for_timeout(600)
    except Exception as ex:  # noqa: BLE001
        _shot(pg, "erro_maiores_18")
        raise Falha("erro", f"não achei 'restringir a maiores de 18' no Studio ({type(ex).__name__})")
    if not _loc_marcado(radio):
        _shot(pg, "erro_maiores_18")
        raise Falha("erro", "'restringir a maiores de 18' não ficou marcado")
    log("  restrição de idade: maiores de 18 marcada")


def _conferir_detalhes(pg, titulo, descricao, sintetico, n_tags, maiores_18=False):
    """Lê de volta o que ficou no formulário. Título/descrição/crianças/idade errados = falha (não sobe torto)."""
    tit = pg.locator("#title-textarea #textbox").first.inner_text()
    if _so_texto(tit) != _so_texto(titulo):
        raise Falha("erro", f"título ficou diferente no Studio: '{tit[:60]}'")
    if descricao:
        desc = pg.locator("#description-textarea #textbox").first.inner_text()
        if _so_texto(desc)[:200] != _so_texto(descricao[:5000])[:200]:
            raise Falha("erro", f"descrição ficou diferente no Studio: '{desc[:60]}'")
    if not _marcado(pg, "[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]"):
        raise Falha("erro", "'Não é conteúdo para crianças' não ficou marcado")
    if maiores_18 and not _loc_marcado(_radio_maiores_18(pg)):
        raise Falha("erro", "'restringir a maiores de 18' não ficou marcado")
    alvo_ia = f"[name=VIDEO_HAS_ALTERED_CONTENT_{'YES' if sintetico else 'NO'}]"
    if sintetico is not None and _marcado(pg, alvo_ia) is False:
        # AB-05 (16/10): video SINTETICO sem a declaracao de IA nao sobe - era a unica conferencia que so avisava. O
        # YouTube exige a divulgacao de conteudo realista gerado (pessoa, voz). Tenta marcar 1 vez mais antes de falhar.
        _clicar_se_existe(pg, alvo_ia, 4000)
        if sintetico and _marcado(pg, alvo_ia) is False:
            raise Falha("erro", "a opção 'conteúdo alterado (IA)' não ficou marcada - não sobe sem a declaração")
        if not sintetico:
            log("  aviso: a opção de conteúdo alterado (IA) não ficou marcada")
    if n_tags:
        chips = pg.locator("#tags-container ytcp-chip, ytcp-free-text-chip-bar ytcp-chip").count()
        if chips < n_tags:
            log(f"  aviso: só {chips} de {n_tags} tags viraram etiqueta")


PARADO_MIN = float(os.environ.get("YT_UPLOAD_PARADO_MIN", "15"))  # envio sem avançar a % por tanto tempo = travado
PRINT_CADA_MIN = 20  # print de acompanhamento durante o envio


def _dialogo_visivel(pg):
    """Texto do aviso/janela que estiver na frente (o que a dona viu no notebook em 04/11)."""
    try:
        d = pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible, [role=dialog]:visible, "
                       "ytcp-confirmation-dialog:visible").first
        if d.count():
            return re.sub(r"\s+", " ", d.inner_text(timeout=3000)).strip()[:300]
    except Exception:  # noqa: BLE001
        pass
    return ""


def _avisar_envio_parado(texto, print_):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(f"🧊 Envio do YouTube TRAVADO: {texto}\nPrint: {print_ or '(não saiu)'}", "postagem",
                      importante=True, html_ok=False)
    except Exception:  # noqa: BLE001
        pass


ENVIOS_LOG = politica.ROOT / "logs" / "envios_por_maquina.jsonl"


def _registrar_envio(slug, maquina, video, seg, resultado, tipo=None):
    """04/11 dona ("tem que ter um histórico de tempo de postagem por PC"): 1 linha por TENTATIVA de envio — máquina,
    MB, minutos, Mbit/s e como terminou. `python youtube_web_poster.py --tempos` resume por máquina."""
    try:
        mb = round(Path(video).stat().st_size / 1e6)
    except OSError:
        mb = None
    try:
        with open(ENVIOS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"em": datetime.now().isoformat("T", "minutes"), "canal": slug, "maquina": maquina,
                                "tipo": tipo, "mb": mb, "min": round(seg / 60, 1),
                                "mbps": round(mb * 8 / seg, 2) if mb and seg > 30 else None,
                                "resultado": resultado}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def resumo_tempos(dias=7):
    from collections import defaultdict
    lim = (datetime.now() - __import__("datetime").timedelta(days=dias)).isoformat("T", "minutes")
    por = defaultdict(list)
    try:
        for l in ENVIOS_LOG.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            if r["em"] >= lim:
                por[r["maquina"]].append(r)
    except (OSError, ValueError):
        pass
    print(f"Envios dos últimos {dias} dias por máquina:")
    for m, rs in sorted(por.items()):
        ok = [r for r in rs if r["resultado"] == "ok"]
        vel = sorted(r["mbps"] for r in ok if r.get("mbps"))
        print(f"  {m:8} {len(rs):3} tentativas, {len(ok):3} ok, {len(rs) - len(ok):3} falhas | velocidade mediana "
              f"{vel[len(vel) // 2] if vel else '-'} Mbit/s | longos ok: "
              + ", ".join(f"{r['mb']} MB em {r['min']} min" for r in ok if (r.get("mb") or 0) > 500)[:200])


def _esperar_upload(pg, timeout_s):
    """Espera o arquivo terminar de subir (o Studio deixa salvar antes, mas fechar a aba no meio cancela).
    04/11 dona: "fui lá e fechei uma aba que parecia travada; tinha um aviso estranho na tela e você considerou que
    estava subindo, mas não estava — tem que ter vigilância por print". O Manhwa Noturno ficou 4h48 "subindo" no Acer
    sem subir. Agora: print a cada PRINT_CADA_MIN; a % sem andar por PARADO_MIN (ou página sem resposta) = print +
    texto do aviso na frente + Telegram e Falha("erro"), que manda pra próxima máquina (notebook -> PC1)."""
    fim = time.time() + timeout_s
    ultimo = ""
    pct_ult, mudou, print_ult = None, time.time(), time.time()
    while time.time() < fim:
        try:
            txt = pg.locator("ytcp-video-upload-progress").first.inner_text(timeout=3000)
        except Exception:  # noqa: BLE001
            txt = ""
        if txt != ultimo:
            log(f"  progresso: {txt.strip()[:80]}")
            ultimo = txt
        baixo = txt.lower()
        if re.search(r"limit|limite", baixo):
            raise Falha("limite", "Studio: limite diário de uploads da conta")
        enviando = re.search(r"\d+\s?%", baixo) and re.search(r"upload|carreg|envi", baixo)
        if txt and not enviando:
            return txt.strip()
        m = re.search(r"(\d+)\s?%", baixo)
        pct = int(m.group(1)) if m else None
        if pct is not None and pct != pct_ult:
            pct_ult, mudou = pct, time.time()
        if time.time() - print_ult > PRINT_CADA_MIN * 60:
            p = _shot(pg, f"envio_{pct_ult if pct_ult is not None else 'x'}pct")
            log(f"  vigia: {pct_ult}% — print {p}")
            print_ult = time.time()
        parado = (time.time() - mudou) / 60
        if parado > PARADO_MIN:
            p = _shot(pg, "envio_TRAVADO")
            aviso = _dialogo_visivel(pg)
            msg = (f"envio parado em {pct_ult if pct_ult is not None else '?'}% há {parado:.0f} min"
                   f"{' no ' + REMOTO.nome if REMOTO else ' no PC1'}" + (f" — aviso na tela: {aviso}" if aviso else ""))
            log(f"  vigia: {msg} (print {p})")
            _avisar_envio_parado(msg, p)
            raise Falha("erro", msg)
        time.sleep(5)
    raise Falha("timeout", f"upload não terminou em {timeout_s}s")


def _duracao_video(path):
    """Duração em segundos (ffprobe); 0 se não deu pra medir (aí vale a margem de Short)."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except (ValueError, OSError, subprocess.SubprocessError):
        return 0.0


def _alvo_15min(dt):
    """Arredonda para cima em passos de 15 min (o Studio só agenda assim)."""
    dt = dt.astimezone().replace(second=0, microsecond=0)
    resto = dt.minute % 15
    return dt + timedelta(minutes=(15 - resto) % 15)


def _fmt_data(dt, lang):
    if lang == "pt":
        return f"{dt.day} de {MESES_PT[dt.month - 1]}. de {dt.year}"
    return f"{MESES_EN[dt.month - 1]} {dt.day}, {dt.year}"


def _fmt_hora(dt, lang):
    if lang == "pt":
        return f"{dt:%H:%M}"
    h = dt.hour % 12 or 12
    return f"{h}:{dt:%M} {'AM' if dt.hour < 12 else 'PM'}"


def _agendar(pg, alvo, lang):
    if lang not in ("pt", "en"):
        raise Falha("erro", f"idioma do Studio '{lang}' sem formato de data (só pt/en)")
    if not _clicar_se_existe(pg, "#second-container-expand-button", 8000):
        raise Falha("erro", "não achei o botão Agendar no passo Visibilidade")
    pg.locator("#datepicker-trigger").first.click()
    pg.wait_for_timeout(800)
    data = pg.locator("ytcp-date-picker tp-yt-paper-input input, ytcp-date-picker input").first
    data.wait_for(state="visible", timeout=10000)
    data.click()
    data.fill(_fmt_data(alvo, lang))
    data.press("Enter")
    pg.wait_for_timeout(800)
    hora = pg.locator("#time-of-day-container input").first
    hora.wait_for(state="visible", timeout=10000)
    hora.click()
    hora.fill(_fmt_hora(alvo, lang))
    hora.press("Enter")
    pg.wait_for_timeout(800)
    lido = hora.input_value()
    if re.sub(r"\s+", "", lido).lower() != re.sub(r"\s+", "", _fmt_hora(alvo, lang)).lower():  # Studio usa U+202F
        raise Falha("erro", f"Studio não aceitou o horário {_fmt_hora(alvo, lang)} (ficou '{lido}')")


def _escolher_arquivo(pg, entrada, video):
    """Coloca o video no <input type=file> passando so o CAMINHO (CDP DOM.setFileInputFiles): o Chrome le do disco.
    Com connect_over_cdp o Playwright trata o Chrome como remoto e set_input_files TRANSFERE o arquivo pela conexao:
    acima de 50 MB recusa e de 30-50 MB estoura o timeout (falhas de 12/10 em CenaReact/eng/ita)."""
    caminho = REMOTO.enviar(video) if REMOTO else str(Path(video).resolve())  # Chrome de outra máquina: lê o disco DELA
    entrada.evaluate("el => { window.__mr_entrada_arquivo = el; }")
    cdp = pg.context.new_cdp_session(pg)
    try:
        obj = cdp.send("Runtime.evaluate", {"expression": "window.__mr_entrada_arquivo"})["result"]["objectId"]
        cdp.send("DOM.setFileInputFiles", {"files": [caminho], "objectId": obj})
    finally:
        cdp.detach()


def _fechar_aviso_publico(pg, espera_ms=3000):
    """1a publicacao publica do canal pelo Studio: aviso "Lembre-se de que todos podem ver o conteudo publico" com Ok.
    Aberto, ele trava o botao Publicar e o video fica salvo como privado (13/10, hindi)."""
    aviso = pg.locator("tp-yt-paper-dialog, ytcp-dialog, [role=dialog]").filter(
        has_text=re.compile(r"todos podem ver o conte|everyone can see", re.I)).last
    try:
        aviso.wait_for(state="visible", timeout=espera_ms)
        aviso.locator("ytcp-button, button").filter(has_text=re.compile(r"^\s*(ok|entendi|got it)\s*$", re.I)).first.click()
    except Exception:  # noqa: BLE001  (nao apareceu: segue)
        return False
    pg.wait_for_timeout(800)
    log("  aviso de 1a publicacao publica fechado (Ok)")
    return True


def _capa(pg, arquivo):
    """Capa personalizada (Miniatura > Enviar arquivo). Nunca derruba o upload: falhou, o video sobe sem capa."""
    p = Path(arquivo)
    if not p.is_file():
        return f"aviso: {p.name} nao existe; sobe sem capa"
    if p.stat().st_size > 2_000_000:
        return f"aviso: {p.name} tem {p.stat().st_size / 1e6:.1f} MB (o Studio aceita ate 2 MB); sobe sem capa"
    try:
        entrada = pg.locator("ytcp-thumbnail-uploader input#file-loader").first
        entrada.wait_for(state="attached", timeout=15000)
        _escolher_arquivo(pg, entrada, p)
        pg.wait_for_timeout(4000)
        txt = pg.locator("ytcp-video-custom-still-editor").first.inner_text(timeout=3000).lower()
        _shot(pg, "capa")
        if "verifi" in txt:
            return "aviso: o canal precisa ser verificado (telefone) para ter capa personalizada; sobe sem capa"
        return f"enviada ({p.name})"
    except Exception as ex:  # noqa: BLE001
        _shot(pg, "capa_falhou")
        return f"aviso: nao consegui por a capa ({type(ex).__name__}: {str(ex)[:80]}); sobe sem capa"


def _playlist(pg, nome):
    """Poe o video na playlist `nome`, criando se nao existir. Confere pelo texto do seletor (mostra as escolhidas).
    Nunca derruba o upload: falhou, o video sobe sem playlist."""
    gatilho = pg.locator("ytcp-video-metadata-playlists ytcp-text-dropdown-trigger").first
    dlg = pg.locator("ytcp-playlist-dialog").first

    def abrir():
        gatilho.click()
        dlg.locator(".done-button").first.wait_for(state="visible", timeout=10000)
        pg.wait_for_timeout(1000)

    def concluir():
        dlg.locator(".done-button").first.click()
        pg.wait_for_timeout(1500)
        return gatilho.inner_text(timeout=3000)

    try:
        abrir()
        item = dlg.get_by_text(nome, exact=True).first
        if item.count():
            item.click()
        else:  # Criar playlist > Nova playlist > titulo > Criar (a nova ja vem marcada)
            dlg.locator(".new-playlist-button").first.click()
            pg.locator("tp-yt-paper-item:has-text('Nova playlist'), tp-yt-paper-item:has-text('New playlist')").first.click()
            form = pg.locator("ytcp-playlist-creation-dialog").first
            caixa = form.locator("#textbox").first
            caixa.wait_for(state="visible", timeout=10000)
            caixa.click()
            pg.keyboard.insert_text(nome[:150])
            form.locator("#create-button").first.click()
            pg.wait_for_timeout(3000)
            log(f"  playlist '{nome}' criada")
        escolhidas = concluir()
        if nome.lower() not in escolhidas.lower():  # criada mas nao marcada: marca e conclui de novo
            abrir()
            dlg.get_by_text(nome, exact=True).first.click()
            escolhidas = concluir()
        _shot(pg, "playlist")
        return "ok" if nome.lower() in escolhidas.lower() else f"aviso: nao ficou marcada (seletor mostra '{escolhidas.strip()[:60]}')"
    except Exception as ex:  # noqa: BLE001
        _shot(pg, "playlist_falhou")
        for _ in range(3):  # fecha o que ficou aberto para o upload seguir
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(400)
        return f"aviso: nao consegui por na playlist ({type(ex).__name__}: {str(ex)[:80]}); sobe sem playlist"


def subir(pg, channel_id, video, titulo, descricao, tags, privacy, alvo, sintetico, ensaio, timeout_s, capa=None,
          playlist=None, maiores_18=False):
    _abrir_studio(pg, channel_id, "/videos/upload?d=ud")
    lang = _idioma(pg)
    log(f"Studio aberto ({lang}); enviando {Path(video).name}")
    entrada = pg.locator("ytcp-uploads-dialog input[type=file], input[type=file]").first
    entrada.wait_for(state="attached", timeout=60000)
    _escolher_arquivo(pg, entrada, video)
    global ARQUIVO_ENVIADO
    ARQUIVO_ENVIADO = True  # daqui em diante uma falha deixa rascunho no Studio
    pg.locator("#title-textarea #textbox").first.wait_for(state="visible", timeout=120000)
    pg.wait_for_timeout(2500)
    txt = _texto_dialogo(pg).lower()
    if "daily upload limit" in txt or "limite diário" in txt:
        raise Falha("limite", "Studio: limite diário de uploads da conta")

    _escrever(pg, "#title-textarea #textbox", titulo[:100])
    if descricao:
        _escrever(pg, "#description-textarea #textbox", descricao[:5000])
    _fechar_sugestoes(pg)  # fecha a sugestão de hashtag aberta pelo título/descrição
    if capa:
        log(f"  capa: {_capa(pg, capa)}")
    if playlist:
        log(f"  playlist: {_playlist(pg, playlist)}")
    if not _clicar_se_existe(pg, "[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]", 15000):
        raise Falha("erro", "não achei 'Não é conteúdo para crianças'")
    _clicar_se_existe(pg, "ytcp-video-metadata-editor #toggle-button, #toggle-button", 5000)  # Mostrar mais
    pg.wait_for_timeout(1000)
    if sintetico is not None:
        _clicar_se_existe(pg, f"[name=VIDEO_HAS_ALTERED_CONTENT_{'YES' if sintetico else 'NO'}]", 4000)
    # 23/10: o Studio conta as ASPAS que põe em volta da tag com espaço (limite 500). Contando só as vírgulas, 28 tags
    # de 470 viravam 518 -> campo vermelho, "Avançar" travado: Esporte/Fio da Meada/Manhwa Noturno/ManhwaReact sem
    # subir das 02:03 às 03:46 ("não cheguei no passo Visibilidade" a cada rodada).
    lista_tags = []
    for t in (x.strip() for x in tags.split(",")):
        if t and sum(len(x) + (2 if " " in x else 0) for x in lista_tags + [t]) + len(lista_tags) <= 480:
            lista_tags.append(t)
    if lista_tags:
        caixa = pg.locator("#tags-container input, ytcp-free-text-chip-bar input").first
        try:
            caixa.wait_for(state="visible", timeout=8000)
            caixa.click()
            for t in lista_tags:  # digitado de verdade: a vírgula é o que vira etiqueta no Studio
                caixa.press_sequentially(t + ",", delay=15)
            pg.wait_for_timeout(500)
        except Exception:  # noqa: BLE001
            log("  aviso: campo de tags não apareceu; segue sem tags")
    if maiores_18:
        _marcar_maiores_18(pg)
    vid = _video_id(pg)
    _conferir_detalhes(pg, titulo[:100], descricao, sintetico, len(lista_tags), maiores_18)
    log(f"  detalhes preenchidos e conferidos (video id {vid})")
    _shot(pg, "1_detalhes")

    for _ in range(4):  # Elementos do vídeo -> Verificações -> Visibilidade
        if pg.locator("#privacy-radios").first.is_visible():
            break
        pg.locator("#next-button").first.click()
        pg.wait_for_timeout(2500)
    if not pg.locator("#privacy-radios").first.is_visible():
        _shot(pg, "erro_visibilidade")
        raise Falha("erro", "não cheguei no passo Visibilidade")

    if alvo:
        _agendar(pg, alvo, lang)
    else:
        nome = {"public": "PUBLIC", "unlisted": "UNLISTED", "private": "PRIVATE"}[privacy]
        if not _clicar_se_existe(pg, f"#privacy-radios [name={nome}]", 8000):
            raise Falha("erro", f"não achei a opção {nome}")
    _fechar_aviso_publico(pg)
    vid = vid or _video_id(pg)
    _shot(pg, "2_visibilidade")
    if not vid:
        raise Falha("erro", "não consegui ler o ID do vídeo no Studio")
    if ensaio:
        log("ENSAIO: parei antes do botão final (o vídeo ficou como RASCUNHO no Studio)")
        return vid, "ensaio"

    _esperar_upload(pg, timeout_s)
    # 21/10 (dono): o bloqueio que não prejudica o canal é o do vídeo PROGRAMADO, pego pela verificação de direitos
    # antes de abrir. Publicação imediata (abre em < 30 min) espera a verificação terminar (até 6 min) — nunca abre
    # sem checar. O rodapé ("Verificações concluídas. Nenhum problema…") vai pro logs/checagem_direitos.jsonl.
    rodape, t_chk = _rodape_checagem(pg), time.time()
    try:
        imediato = alvo is None or (alvo - datetime.now(alvo.tzinfo)) < timedelta(minutes=30)
    except Exception:  # noqa: BLE001
        imediato = True
    while imediato and rodape and not re.search(r"conclu|complete|encontrad|found", rodape, re.I) \
            and time.time() - t_chk < 360:
        pg.wait_for_timeout(15000)
        rodape = _rodape_checagem(pg)
    espera_chk = round(time.time() - t_chk)
    _fechar_aviso_publico(pg, 1000)
    global FINAL_CLICADO
    FINAL_CLICADO = True  # daqui pra frente o vídeo existe (agendado/publicado): erro NÃO pode reenviar em outra máquina
    pg.locator("#done-button").first.click()
    for _ in range(60):  # confirmação: "Vídeo publicado/agendado" ou "ainda processando"
        pg.wait_for_timeout(2000)
        if _fechar_aviso_publico(pg, 300):
            _clicar_se_existe(pg, "#done-button", 2000)  # o aviso segurou o Publicar: clica de novo
        if pg.locator("ytcp-video-share-dialog, ytcp-uploads-still-processing-dialog, ytcp-prechecks-warning-dialog"
                      ).first.is_visible():
            break
    checando = pg.locator("ytcp-prechecks-warning-dialog").first.is_visible()
    if checando:
        # aviso de verificação de direitos ainda rodando: confirma publicar mesmo assim
        _clicar_se_existe(pg, "ytcp-prechecks-warning-dialog #primary-action-button", 5000)
        pg.wait_for_timeout(4000)
    _shot(pg, "3_final")
    _anotar_checagem(vid, checando, alvo, rodape, espera_chk)
    return vid, "ok"


def _rodape_checagem(pg):
    """Linha de status da verificação no rodapé da janela de upload ("Verificações concluídas. Nenhum problema foi
    encontrado." / "Verificando…" / direitos encontrados); "" se não achou."""
    try:
        t = pg.locator("ytcp-uploads-dialog").first.inner_text(timeout=5000)
    except Exception:  # noqa: BLE001
        return ""
    achados = re.findall(r"[^\n]*(?:[Vv]erifica|[Cc]heck)[^\n]*", t)
    achados = [x.strip() for x in achados if len(x.strip()) > 12 and x.strip() not in ("Verificações", "Checks")]
    return achados[-1] if achados else ""


CHECAGEM_LOG = politica.ROOT / "logs" / "checagem_direitos.jsonl"


def _anotar_checagem(vid, checando, alvo, rodape="", espera=0):
    """Dado pra margem mínima do agendamento (dono 21/10: "quanto tempo mínimo no programado pro aviso aparecer?"):
    rodapé da verificação de direitos na hora de agendar, quanto esperou por ela (imediato) e se ainda rodava. O
    avisos_studio cruza com a hora em que o "Bloqueado" apareceu. Nunca derruba o upload."""
    try:
        with open(CHECAGEM_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "video": vid,
                                 "rodape": rodape, "esperou_s": espera,
                                 "direitos_no_upload": bool(re.search(r"direitos autorais|copyright", rodape or "",
                                                                      re.I)),
                                 "checagem_rodando_ao_agendar": bool(checando),
                                 "abre": alvo.isoformat(timespec="minutes") if hasattr(alvo, "isoformat") else alvo},
                                ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _canal_e_mapa(nome_ou_id):
    canal, err = politica.achar_canal(nome_ou_id or "")
    if not canal:
        raise Falha("erro", err)
    slug, e = entrada_do_cred(canal["id"])
    if not e:
        raise Falha("erro", f"canal '{canal['nome'].strip()}' não está em {MAPA_FILE.name} (rode --montar-mapa)")
    if not e.get("channel_id"):
        raise Falha("erro", f"{slug}: falta channel_id no mapa")
    global _CONTA
    _CONTA = (slug, (canal.get("nome") or slug).strip())
    try:  # 05/11: canal removido / com strike / "Muitos avisos" = nenhuma automação (trava_conta.py)
        import trava_conta
        motivo = trava_conta.checar(slug)
    except Exception:  # noqa: BLE001
        motivo = None
    if motivo:
        raise Falha("morto", f"TRAVADO pelo YouTube ({motivo}) — {slug} não é tocado por nenhum robô")
    return canal, slug, e


def checar(nome=None):
    from playwright.sync_api import sync_playwright
    mapa = ler_mapa()
    alvos = mapa.get("canais", {}).items()
    if nome:
        _, slug, _e = _canal_e_mapa(nome)
        alvos = [(slug, _e)]
    for slug, e in alvos:
        proc = None
        try:
            proc = abrir_conta(e)
            with sync_playwright() as p:
                br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{e['porta']}")
                pg = br.contexts[0].new_page()
                try:
                    _abrir_studio(pg, e["channel_id"])
                    print(f"  {slug:22} OK  logado e abre o canal '{_nome_canal(pg) or '?'}' ({_idioma(pg)})"
                          + ("  [sobe restrito a maiores de 18]" if e.get("maiores_18") else ""))
                except Falha as f:
                    print(f"  {slug:22} {f.status.upper()}  {f}")
                    _shot(pg, f"checar_{slug}")
                except Exception as ex:  # noqa: BLE001
                    print(f"  {slug:22} ERRO  {type(ex).__name__}: {str(ex)[:100]}")
                    _shot(pg, f"checar_{slug}")
                pg.close()
                soltar(br, proc)
        except Falha as f:
            print(f"  {slug:22} ERRO {f}")
        finally:
            fechar_chrome(proc, e)


def logar(slug):
    e = ler_mapa().get("canais", {}).get(slug)
    if not e:
        print(f"slug '{slug}' não está no mapa (rode --montar-mapa)")
        return
    if e.get("email"):  # login novo vai para o cofre (D:/logins-google/cofre/perfis/<conta>), servindo a todos os projetos
        _cofre().logar(e["email"])
    else:
        abrir_chrome(e["perfil"], e["porta"], "https://accounts.google.com", visivel=True)
    print(f"Chrome aberto (conta {e.get('email')}). Entre na conta e depois")
    print(f"abra studio.youtube.com no MESMO Chrome para conferir o canal {e.get('nome')}. Pode fechar quando terminar.")


NSN = Path(r"D:\projeto-navegador-sem-navegador")


def _log_http(m):
    with open(Path(__file__).resolve().parents[1] / "logs" / "youtube_http.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {m}" + chr(10))


def _subir_http(slug, e, a, alvo, maiores_18):
    """29/10 (dona: "faça" — implantar o navegador sem navegador): sobe por HTTP sem abrir Chrome
    (D:\\projeto-navegador-sem-navegador\\services\\youtube\\upload_http.py, provado 29/10 na gamenoturno). Só no caso
    simples e AGENDADO; maiores de 18, ensaio ou não-público vão pelo Chrome (o HTTP ainda não marca essas opções).
    Playlist e selo sintético vão por HTTP (29/10, provados relendo o vídeo). Capa vai junto (melhor esforço; canal sem telefone não aceita capa nem pelo
    Chrome). Sem token/cookies vivos o Enviador colhe os dois numa visita escondida ao Studio (upload_http.colher_sessao).
    Devolve o videoId ou None (aí segue o Chrome como antes)."""
    mapa = ler_mapa()
    motivos = [n for n, v in (("sem horário", not alvo), ("ensaio", a.ensaio), ("maiores de 18", maiores_18),
                              (f"privacy={a.privacy}", a.privacy != "public"),
                              ("desligado no mapa", not mapa.get("postar_http", True)), ("sem_http", e.get("sem_http"))) if v]
    if motivos:
        _log_http(f"{slug}: pulou o HTTP ({', '.join(motivos)}) -> Chrome")
        return None
    try:
        if str(NSN) not in sys.path:
            sys.path.append(str(NSN))  # no fim (regra 23/10: pasta de outro projeto nunca na frente)
        from services.youtube.upload_http import Enviador
        tags = []
        for t in (x.strip() for x in (a.tags or "").split(",")):  # mesmo limite do Studio (aspas contam, 500)
            if t and sum(len(x) + (2 if " " in x else 0) for x in tags + [t]) + len(tags) <= 480:
                tags.append(t)
        vid = Enviador(slug).enviar(a.video, a.titulo, descricao=a.descricao, tags=tags, agendar=int(alvo.timestamp()),
                                    short=_duracao_video(a.video) <= 180, capa=a.thumbnail, playlist=a.playlist,
                                    sintetico=True if a.sintetico else None)
        log(f"{slug}: subiu por HTTP (sem Chrome) -> {vid}, agendado {alvo:%d/%m %H:%M}")
        _log_http(f"{slug}: subiu por HTTP (sem Chrome) -> {vid}, agendado {alvo:%d/%m %H:%M}")
        return vid
    except Exception as ex:  # noqa: BLE001 — qualquer erro: segue o Chrome (nunca sem postagem)
        if politica.eh_advertencias(str(ex)):
            msg = "uploads bloqueados por muitos avisos das diretrizes da comunidade"
            log(f"{slug}: HTTP recusado ({msg}); não tenta pelo Chrome")
            _log_http(f"{slug}: HTTP recusado ({msg}); não tenta pelo Chrome")
            raise Falha("advertencias", msg)
        if type(ex).__name__ == "LimiteDiario":  # 01/11: limite diário da conta; o Chrome bate no MESMO limite
            msg = "limite diário de envios do YouTube (muitos envios em 24 h; 12/11: vale mesmo com telefone verificado); não tenta pelo Chrome"
            log(f"{slug}: HTTP recusado ({msg})")
            _log_http(f"{slug}: HTTP recusado ({msg})")
            raise Falha("limite", msg)
        log(f"{slug}: HTTP não subiu ({type(ex).__name__}: {str(ex)[:160]}) -> Chrome")
        _log_http(f"{slug}: HTTP não subiu ({type(ex).__name__}: {str(ex)[:300]}) -> Chrome")
        return None


def main():
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--video")
    ap.add_argument("--titulo")
    ap.add_argument("--descricao", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--canal")
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    ap.add_argument("--publish-at", default=None)
    ap.add_argument("--categoria", default=None, help="ignorado no navegador (fica a categoria padrão do canal)")
    ap.add_argument("--idioma", default=None, help="ignorado no navegador")
    ap.add_argument("--sintetico", action="store_true")
    ap.add_argument("--projeto", default=None)
    ap.add_argument("--tipo", default=None, help="short/completo/compilado/react/veo... (só pro ledger)")
    ap.add_argument("--ensaio", action="store_true", help="preenche tudo e para antes do botão final")
    ap.add_argument("--thumbnail", default=None, help="capa jpg/png ate 2 MB (falhou: sobe sem capa)")
    ap.add_argument("--playlist", default=None, help="nome da playlist; cria se nao existir (falhou: sobe sem playlist)")
    ap.add_argument("--maiores-18", action="store_true",
                    help="restringe a maiores de 18 (canal com maiores_18=true no mapa ja restringe sempre)")
    ap.add_argument("--montar-mapa", action="store_true")
    ap.add_argument("--checar", action="store_true")
    ap.add_argument("--logar", metavar="SLUG")
    ap.add_argument("--tempos", nargs="?", const=7, type=int, metavar="DIAS",
                    help="resumo do tempo de envio por máquina (logs/envios_por_maquina.jsonl)")
    a = ap.parse_args()

    if a.tempos:
        return resumo_tempos(a.tempos)

    if a.montar_mapa:
        return montar_mapa()
    if a.logar:
        return logar(a.logar)
    if a.checar:
        try:
            return checar(a.canal)
        except Falha as f:
            _fim(f.status, str(f), EXIT_FALHA)

    if not a.video or not a.titulo:
        _fim("erro", "faltou --video/--titulo", EXIT_USO)
    if not Path(a.video).is_file():
        _fim("erro", "arquivo não existe", EXIT_USO)
    if not a.ensaio:  # 31/10 REGRA da dona: nada sobe com menos de 1080p (qualquer projeto que chame direto)
        try:
            a.video = str(politica.garantir_1080(a.video))
        except Exception as e1080:  # noqa: BLE001
            _fim("erro", f"vídeo abaixo de 1080p e o upscale falhou ({str(e1080)[:150]}) — não sobe", EXIT_FALHA)
    try:
        canal, slug, e = _canal_e_mapa(a.canal)
    except Falha as f:
        _fim(f.status, str(f), EXIT_USO)

    bloqueio = politica.checar_upload(canal, a.video, a.projeto, a.tipo)
    if bloqueio and not a.ensaio:
        codigo, msg = bloqueio
        print(f"BLOQUEADO [{codigo}]: {msg}", file=sys.stderr)
        _fim(STATUS_BLOQUEIO.get(codigo, codigo), msg, EXIT_BLOQUEADO)

    alvo = None
    if a.publish_at or a.privacy == "public":  # público SEMPRE agendado (10+ min): nunca abre na hora
        alvo = _alvo_15min(politica.horario_obrigatorio(canal, a.publish_at, a.projeto, a.tipo))
        # 21/10 (dono: "10 min basta?"): medido no rodapé do upload — "Verificação 1% … 10 minutos restantes" na hora
        # de agendar um Short. A verificação de direitos tem que acabar ANTES de abrir (aí o bloqueio é do vídeo
        # programado e não pesa no canal): margem a partir de agora (o upload ainda vai levar minutos) de 25 min no
        # Short e 25 min + a duração no vídeo longo.
        dur = _duracao_video(a.video)
        margem = timedelta(minutes=25 + (dur / 60 if dur > 180 else 0))
        minimo = _alvo_15min(datetime.now().astimezone() + margem)
        if alvo < minimo:
            log(f"{slug}: abre {minimo:%d/%m %H:%M} em vez de {alvo:%H:%M} — a verificação de direitos precisa acabar "
                f"antes (margem {margem.seconds // 60} min, vídeo de {dur / 60:.1f} min)")
            alvo = minimo
    mb = Path(a.video).stat().st_size / 1e6
    timeout_s = int(600 + 3 * mb)
    maiores_18 = a.maiores_18 or bool(e.get("maiores_18"))
    if maiores_18:
        log(f"{slug}: vídeo vai restrito a maiores de 18")

    global REMOTO, FINAL_CLICADO, ARQUIVO_ENVIADO
    from playwright.sync_api import sync_playwright

    def _uma_vez(ev, proc):
        with sync_playwright() as p:
            try:  # revisão 23/10: sem isto o túnel caído virava traceback e não tentava a próxima máquina
                br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{ev['porta']}")
                pg = br.contexts[0].new_page()
            except Exception as ex:  # noqa: BLE001
                raise Falha("erro", f"não conectei no Chrome ({type(ex).__name__}: {str(ex)[:120]})")
            pg.set_default_timeout(30000)
            try:
                return subir(pg, ev["channel_id"], a.video, a.titulo, a.descricao, a.tags, a.privacy, alvo,
                             True if a.sintetico else None, a.ensaio, timeout_s, a.thumbnail, a.playlist, maiores_18)
            except Falha:
                _shot(pg, f"falha_{slug}")
                raise
            except Exception as ex:  # noqa: BLE001  (seletor mudou, timeout do Playwright...)
                s = _shot(pg, f"falha_{slug}")
                txt = _texto_dialogo(pg).lower()
                if "daily upload limit" in txt or "limite diário" in txt:  # 22/10: o limite aparece no meio do envio
                    raise Falha("limite", "Studio: limite diário de uploads da conta")
                if politica.eh_advertencias(txt):
                    raise Falha("advertencias", "Studio: uploads bloqueados por muitos avisos das diretrizes da comunidade")
                raise Falha("erro", f"{type(ex).__name__}: {str(ex)[:160]} (print: {s})")
            finally:
                try:
                    pg.close()
                except Exception:  # noqa: BLE001
                    pass
                soltar(br, proc)

    try:
        vid = _subir_http(slug, e, a, alvo, maiores_18)
    except Falha as f:
        _fim(f.status, str(f), EXIT_FALHA)
    if vid:
        publish_at = politica.rfc3339(alvo)
        politica.registrar_upload(canal, vid, a.video, publish_at, projeto=a.projeto, tipo=a.tipo)
        print(f"AGENDADO: https://youtu.be/{vid}  (canal: {canal['nome'].strip()}, http) → publica {publish_at}")
        _fim("ok", f"https://youtu.be/{vid}")

    # 23/10 (dona): conta logada nos notebooks sobe por eles; erro num = tenta o outro; erro de novo (ou conta fora
    # dos notebooks) = este PC. Limite diário/canal bloqueado não troca de máquina (é da conta, não do PC).
    maq = e.get("maquina")
    # 04/11 dona ("o PC1 não roda só o upload, várias coisas competem; lá ele pode fazer com prioridade — é um caso de
    # testar"): YT_MAQUINA=desktop manda SÓ ESTE envio pelo Chrome daquela máquina (conta já logada lá: dona 28/10
    # logou todas no desktop — netbooks_logins.json). Falhou lá = este PC, como sempre.
    if os.environ.get("YT_MAQUINA"):
        perfil_r = e.get("perfil_remoto") or str(e.get("email") or "").split("@")[0].lower()
        if perfil_r:
            maq = [os.environ["YT_MAQUINA"]]
            e = dict(e, perfil_remoto=perfil_r)
            log(f"{slug}: teste de envio pelo {maq[0]} (YT_MAQUINA)")
    vid = st = ultimo = None
    if maq:
        import maquina_remota
        ordem = maquina_remota.tentativas(maq, e.get("perfil_remoto"), log_fn=log)
    else:
        ordem = iter([None])
    pular_notebooks = False
    try:
        for rem in ordem:
            if rem and pular_notebooks:
                continue  # já deixou um rascunho num notebook: a 2ª tentativa vai direto pro PC1 (máx. 1 rascunho a mais)
            REMOTO, proc, FINAL_CLICADO, ARQUIVO_ENVIADO = rem, None, False, False
            t_maq, res_maq = time.time(), "erro"
            try:
                if rem:
                    log(f"{slug}: enviando pelo Chrome do {rem.nome}")
                    vid, st = _uma_vez(dict(e, porta=rem.porta_local), None)
                else:
                    if maq:
                        log(f"{slug}: enviando por este PC")
                    with Trava():
                        proc = abrir_conta(e)
                        vid, st = _uma_vez(e, proc)
                ultimo = None
                res_maq = "ok"
                break
            except Falha as f:
                ultimo = f
                res_maq = f"{f.status}: {str(f)[:120]}"
                if FINAL_CLICADO:
                    log(f"{slug}: falhou DEPOIS do botão final no {rem.nome if rem else 'PC1'} — não reenvio (o vídeo "
                        "pode já estar no canal; conferir no Studio)")
                    break
                if rem and f.status in ("erro", "morto"):
                    log(f"{slug}: falhou no {rem.nome} [{f.status}] {str(f)[:120]} — tento na próxima máquina")
                    pular_notebooks = pular_notebooks or ARQUIVO_ENVIADO
                    continue
                break
            finally:
                if not rem:
                    fechar_chrome(proc, e)
                _registrar_envio(slug, rem.nome if rem else "pc1", a.video, time.time() - t_maq, res_maq, a.tipo)
    finally:
        REMOTO = None
        if hasattr(ordem, "close"):
            ordem.close()
    if ultimo:
        print(f"ERRO navegador [{ultimo.status}]: {ultimo}", file=sys.stderr)
        _fim(ultimo.status, str(ultimo), EXIT_FALHA)

    url = f"https://youtu.be/{vid}"
    if st == "ensaio":
        _fim("ensaio", url)
    publish_at = politica.rfc3339(alvo) if alvo else None
    politica.registrar_upload(canal, vid, a.video, publish_at, projeto=a.projeto, tipo=a.tipo)
    # 23/10 (dona: "vídeo só no Acer"): não abre mais no notebook logo depois do envio (abria no X200MA com o vídeo
    # ainda agendado). Quem mostra é o telão do Acer quando o vídeo fica público (D:\video-fila\vitrine.py), com o like
    # da conta pessoal da dona.
    if publish_at:
        print(f"AGENDADO: {url}  (canal: {canal['nome'].strip()}, navegador) → publica {publish_at}")
    else:
        print(f"POSTADO: {url}  (canal: {canal['nome'].strip()}, navegador)")
    _fim("ok", url)


if __name__ == "__main__":
    main()
