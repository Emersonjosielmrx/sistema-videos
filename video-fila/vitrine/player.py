#!/usr/bin/env python3
"""player.py — TELÃO de conferência (roda nos notebooks; dono 22/10/2026: "abrir o YouTube e mostrar o vídeo
automaticamente quando sair e depois fechar sozinho" + "a tela não fica ociosa: exibe o painel girando").

O PC1 (D:\\video-fila\\vitrine.py) acrescenta linhas em ~/vitrine/fila.txt:  <url>\t<segundos>\t<rótulo>
e manda ~/vitrine/painel.json a cada ~2 min. Este loop:
  - tem vídeo na fila: fecha o painel, abre o vídeo em TELA CHEIA com som, espera a duração e fecha;
  - não tem: mostra ~/vitrine/painel.html (servido em 127.0.0.1:8787, só nesta máquina) girando os quadros;
  - botões do painel: "Abrir" põe o vídeo na fila daqui; "Ver" (vídeo esperando aprovação) vira pedido em
    ~/vitrine/pedidos.txt, o PC1 manda o arquivo pra ~/vitrine/locais/ e ele toca como file://.
~/vitrine/PAUSADO para tudo; ~/postador-worker/ocupado (o notebook está postando) fecha o painel pra sobrar memória.
Só biblioteca padrão do Python (nada instalado).
"""
import json
import os
import shutil
import signal
import subprocess
import threading
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PASTA = Path.home() / "vitrine"
FILA = PASTA / "fila.txt"
TOCADOS = PASTA / "tocados.txt"
PEDIDOS = PASTA / "pedidos.txt"
LOCAIS = PASTA / "locais"
LOG = PASTA / "player.log"
PERFIL = PASTA / "perfil_navegador"
PORTA = 8787
PAINEL_REINICIO_S = 2 * 3600  # navegador aberto o dia todo vaza memória: reabre a cada 2 h
PAINEL = {"proc": None, "desde": 0.0}


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%d/%m %H:%M:%S ") + m + "\n")


CHROME_LOCAL = Path.home() / ".local" / "chrome" / "opt" / "google" / "chrome" / "chrome"
PERFIL_CHROME = PASTA / "perfil_chrome"  # Acer: a conta PESSOAL da dona fica logada aqui (o like é dela, 1 por vídeo)
PORTA_CDP = 9470


def _navegador(url):
    """Comando do navegador em tela cheia, perfil próprio (não mexe no do dono), autoplay com som liberado."""
    PERFIL.mkdir(parents=True, exist_ok=True)
    # 23/10 (dona: "tela preta com as vozes, engasgando na RAM/processador"): o Chrome com o YouTube inteiro é pesado
    # demais pro Atom do Acer — voltou o Firefox (só o vídeo). O like não sai mais daqui (ver vitrine.py).
    if False and _tela() == "acer" and CHROME_LOCAL.exists():
        # 23/10 (dona: "o like só numa conta, a minha pessoal, no Acer que já abre o vídeo pra eu ver"): Chrome com a
        # porta de controle SÓ local; o PC1 clica em "Gostei" pelo túnel ssh enquanto o vídeo toca
        PERFIL_CHROME.mkdir(parents=True, exist_ok=True)
        return [str(CHROME_LOCAL), "--kiosk", "--autoplay-policy=no-user-gesture-required", "--no-first-run",
                "--disable-session-crashed-bubble", "--disable-infobars", "--noerrdialogs", "--password-store=basic",
                f"--remote-debugging-port={PORTA_CDP}", "--remote-allow-origins=*", f"--user-data-dir={PERFIL_CHROME}",
                url]
    for chrome in ("google-chrome", "chromium", "chromium-browser"):
        if shutil.which(chrome):
            return [chrome, "--kiosk", "--autoplay-policy=no-user-gesture-required", "--no-first-run",
                    "--disable-session-crashed-bubble", "--disable-infobars", "--noerrdialogs",
                    f"--remote-debugging-port={PORTA_CDP}", "--remote-allow-origins=*",  # like da dona (reserva)
                    "--password-store=basic", f"--user-data-dir={PERFIL}", url]
    ff = PERFIL / "user.js"  # Firefox: autoplay com som e sem "restaurar sessão"
    ff.write_text('user_pref("media.autoplay.default", 0);\n'
                  'user_pref("media.autoplay.blocking_policy", 0);\n'
                  'user_pref("browser.sessionstore.resume_from_crash", false);\n'
                  'user_pref("browser.shell.checkDefaultBrowser", false);\n'
                  'user_pref("datareporting.policy.dataSubmissionEnabled", false);\n'
                  'user_pref("remote.active-protocols", 1);\n', encoding="utf-8")
    # 23/10: porta de controle (WebDriver BiDi) SÓ local — o PC1 dá o like da conta pessoal da dona pelo túnel ssh
    porta = ["--remote-debugging-port", str(PORTA_CDP)] if _tela() == "acer" else []
    return ["firefox", "--kiosk", "--no-remote", *porta, "-profile", str(PERFIL), url]


SUPERFLUOS = ("mintUpdate", "mintreport-tray", "blueman-applet", "update-notifier", "gnome-software",
             "snap-store", "evolution-alarm-notify", "tracker-miner-fs-3", "deja-dup-monitor", "orca", "zeitgeist")


def liberar_ram():
    """Dona 23/10: "limpar a RAM e processos desnecessários antes de cada execução". Fecha (sinal normal) o que é
    supérfluo no notebook: bandeja/atualização do Mint e Ubuntu e navegador NOSSO que sobrou. Nunca toca no
    navegador pessoal da dona nem no sistema."""
    for nome in SUPERFLUOS:
        subprocess.run(["pkill", "-x", nome[:15]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not (PAINEL["proc"] and PAINEL["proc"].poll() is None):
        subprocess.run(["pkill", "-f", "[v]itrine/perfil_"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sync"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _destravar_firefox():
    """O Firefox fechado à força deixa a trava do perfil ("lock"/".parentlock") e a próxima abertura desiste achando
    que já está aberto (23/10: a janela de login não abria). Sem Firefox nosso vivo, tira a trava."""
    if subprocess.run(["pgrep", "-f", "[f]irefox.*vitrine/perfil_navegador"], stdout=subprocess.DEVNULL).returncode == 0:
        return
    for nome in ("lock", ".parentlock"):
        try:
            (PERFIL / nome).unlink()
        except OSError:
            pass


def _abrir(url):
    liberar_ram()
    _destravar_firefox()
    return subprocess.Popen(_navegador(url), start_new_session=True, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def _fechar(p):
    if not p:
        return
    try:
        os.killpg(p.pid, signal.SIGTERM)
        for _ in range(12):
            if p.poll() is not None:
                break
            time.sleep(0.25)
        os.killpg(p.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        p.wait(timeout=5)
    except Exception:  # noqa: BLE001
        pass


# ─────────────────────────── painel ────────────────────────────────────────
class Pagina(SimpleHTTPRequestHandler):
    """Só o painel (html/json) e os botões; nada mais da pasta é servido (perfil, logs, fila)."""

    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(PASTA), **k)

    def log_message(self, *a):
        pass

    def _texto(self, codigo, txt):
        corpo = txt.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/pedido":
            q = urllib.parse.parse_qs(u.query)
            tipo, v = (q.get("tipo") or [""])[0], (q.get("v") or [""])[0]
            if tipo == "abrir" and v.startswith(("https://www.youtube.com/", "https://youtu.be/")):
                if _tela() != "acer":  # dono 22/10: vídeo só no Acer — o PC1 repassa o pedido pra lá
                    with open(PEDIDOS, "a", encoding="utf-8") as f:
                        f.write(f"abrir\t{v}\t{int(time.time())}\n")
                    return self._texto(200, "Vai tocar no Acer em até 1 minuto")
                seg = 600 if "watch?v=" in v else 65
                with open(FILA, "a", encoding="utf-8") as f:
                    f.write(f"{v}#pedido{int(time.time())}\t{seg}\tpedido no painel\n")
                return self._texto(200, "Abrindo o vídeo…")
            if tipo == "ver" and v and len(v) < 200 and "\n" not in v and "\t" not in v:
                with open(PEDIDOS, "a", encoding="utf-8") as f:
                    f.write(f"ver\t{v}\t{int(time.time())}\n")
                return self._texto(200, "Pedido enviado ao PC1: o vídeo chega em até 1 minuto")
            return self._texto(400, "pedido inválido")
        if u.path == "/pc1":  # 28/10 (dona): "sem sinal" só se NÃO houver conexão de verdade com o PC1
            import socket
            # 30/10 (dona: "sem conexão só se a perda for real"): o PC1 não tem ssh (22 fechada) e, sobrecarregado, a
            # 8790 passava dos 3 s com ele ligado. 8790 com 8 s; senão ping pela Tailscale.
            try:
                with socket.create_connection(("100.118.234.102", 8790), timeout=8):
                    ok = True
            except OSError:
                try:
                    ok = subprocess.run(["ping", "-c", "2", "-W", "3", "100.118.234.102"], capture_output=True,
                                        timeout=15).returncode == 0
                except Exception:  # noqa: BLE001
                    ok = False
            corpo = json.dumps({"conectado": ok}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return None
        if u.path not in ("/painel.html", "/painel.json"):
            return self._texto(404, "não existe")
        return super().do_GET()


def servidor():
    try:
        s = ThreadingHTTPServer(("127.0.0.1", PORTA), Pagina)
    except OSError as e:
        log(f"painel: porta {PORTA} ocupada ({e})")
        return
    threading.Thread(target=s.serve_forever, daemon=True).start()


def _ram_livre_mb():
    try:
        for linha in open("/proc/meminfo", encoding="utf-8"):
            if linha.startswith("MemAvailable:"):
                return int(linha.split()[1]) // 1024
    except OSError:
        pass
    return 9999


def _tela():
    try:
        return (PASTA / "tela.txt").read_text(encoding="utf-8").strip() or "acer"
    except OSError:
        return "acer"


def painel_abrir():
    p = PAINEL["proc"]
    if p and p.poll() is None and time.time() - PAINEL["desde"] < PAINEL_REINICIO_S:
        return
    _fechar(p)
    if not (PASTA / "painel.html").exists():
        return
    PAINEL["proc"] = _abrir(f"http://127.0.0.1:{PORTA}/painel.html?tela={urllib.parse.quote(_tela())}")
    PAINEL["desde"] = time.time()


def painel_fechar():
    _fechar(PAINEL["proc"])
    PAINEL["proc"] = None


# ─────────────────────────── vídeos ────────────────────────────────────────
def _tocados():
    try:
        return set(TOCADOS.read_text(encoding="utf-8").split())
    except OSError:
        return set()


def proximo():
    ja = _tocados()
    try:
        for linha in FILA.read_text(encoding="utf-8").splitlines():
            partes = linha.split("\t")
            if partes and partes[0].startswith(("http", "file://")) and partes[0] not in ja:
                try:
                    seg = float(partes[1]) if len(partes) > 1 and partes[1] else 75
                except ValueError:  # linha torta na fila não derruba o player
                    seg = 75
                return partes[0], seg, (partes[2] if len(partes) > 2 else "")
    except OSError:
        pass
    return None


def _mudo_agora():
    """True se o som do sistema está mudo agora (pactl/wpctl/amixer); None se não deu pra ler.
    12/11: o x200ma só tem amixer — sem ler o mudo, o player desmutava a cada vídeo."""
    try:
        if not shutil.which("pactl") and not shutil.which("wpctl") and shutil.which("amixer"):
            r = subprocess.run(["amixer", "get", "Master"], capture_output=True, text=True, timeout=10)
            if "[off]" in r.stdout:
                return True
            return False if "[on]" in r.stdout else None
        if shutil.which("pactl"):
            r = subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"], capture_output=True, text=True, timeout=10)
            return "yes" in r.stdout.lower() or "sim" in r.stdout.lower()
        if shutil.which("wpctl"):
            r = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True, timeout=10)
            return "MUTED" in r.stdout
    except Exception:  # noqa: BLE001
        return None
    return None


def volume_maximo():
    """Dono 22/10: volume fixo antes de CADA vídeo, sem mudo — 100% (telão principal) ou o que estiver em
    ~/vitrine/volume.txt (reserva: 70). PipeWire/PulseAudio pelo pactl; wpctl ou amixer se for o que houver.
    11/11 (dona: "toda vez que eu mudo o Acer ele volta o volume no próximo vídeo; se eu mutar quero que fique mudo"):
    se a dona MUTOU, o player marca ~/vitrine/mudo_manual e não tira mais o mudo. Desmutou à mão = volta ao normal
    (apaga a marca sozinho). Apagar ~/vitrine/mudo_manual também volta ao normal."""
    marca = PASTA / "mudo_manual"
    mudo = _mudo_agora()
    # 12/11 dona ("deixe o x200ma no mudo também"): com a marca, NUNCA desmuta — nem quando não deu pra ler o estado
    if marca.exists() and mudo is None:
        log("marca de mudo da dona — não mexo no volume")
        return
    if mudo:
        if not marca.exists():
            marca.write_text("mutado pela dona — o player não desmuta\n", encoding="utf-8")
            log("som mudo pela dona — mantenho mudo")
        return
    if mudo is False and marca.exists():
        marca.unlink()  # desmutou à mão: volta a valer o volume fixo
    try:
        pct = max(0, min(150, int((PASTA / "volume.txt").read_text(encoding="utf-8").strip())))
    except (OSError, ValueError):
        pct = 100
    cmds = [["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"],
            ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"],
            ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{pct / 100:.2f}"],
            ["amixer", "-q", "-D", "pulse", "sset", "Master", f"{pct}%", "unmute"],
            ["amixer", "-q", "sset", "Master", f"{pct}%", "unmute"]]
    for c in cmds:
        if shutil.which(c[0]):
            subprocess.run(c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)


def tela_sempre_acesa():
    """Dono 22/10: "brilho sempre no máximo; o Acer ainda apaga a tela quando fica sem nada". No X11 (Cinnamon do
    Acer) quem apaga é o DPMS/protetor do próprio X — xset desliga; no GNOME/Wayland vale o gsettings. Brilho 100%
    pelo serviço de energia da sessão (sem senha). Repetido a cada volta: se algo religar, volta a valer."""
    rodar = lambda c: subprocess.run(c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)  # noqa: E731
    if shutil.which("xset"):
        for c in (["xset", "s", "off"], ["xset", "s", "noblank"], ["xset", "-dpms"]):
            rodar(c)
    for chave, valor in (("org.cinnamon.desktop.session", "idle-delay"), ("org.gnome.desktop.session", "idle-delay")):
        rodar(["gsettings", "set", chave, valor, "0"])
    for esquema in ("org.cinnamon.settings-daemon.plugins.power", "org.gnome.settings-daemon.plugins.power"):
        for k, v in (("idle-dim", "false"), ("idle-dim-battery", "false"), ("idle-dim-time", "0"),
                     ("sleep-display-ac", "0"), ("sleep-display-battery", "0"), ("idle-brightness", "100"),
                     ("sleep-inactive-ac-type", "nothing"), ("sleep-inactive-battery-type", "nothing")):
            rodar(["gsettings", "set", esquema, k, v])
    if shutil.which("gdbus"):
        for dest, caminho, iface in (
                ("org.cinnamon.SettingsDaemon.Power", "/org/cinnamon/SettingsDaemon/Power",
                 "org.cinnamon.SettingsDaemon.Power.Screen"),
                ("org.gnome.SettingsDaemon.Power", "/org/gnome/SettingsDaemon/Power",
                 "org.gnome.SettingsDaemon.Power.Screen")):
            rodar(["gdbus", "call", "--session", "--dest", dest, "--object-path", caminho, "--method",
                   "org.freedesktop.DBus.Properties.Set", iface, "Brightness", "<int32 100>"])
            rodar(["gdbus", "call", "--session", "--dest", dest, "--object-path", caminho, "--method",
                   f"{iface}.SetPercentage", "100"])
    if shutil.which("brightnessctl"):
        rodar(["brightnessctl", "set", "100%"])


def login_em_andamento():
    """Janela de login da dona aberta neste notebook: ~/postador-worker/ocupado com login=true (chrome_conta.logar, na
    hora) ou ~/vitrine/SO_PAINEL com "login" (reserva do PC1, chega em até 2 min)."""
    ocupado = Path.home() / "postador-worker" / "ocupado"
    try:
        if time.time() - ocupado.stat().st_mtime < 3 * 3600 and json.loads(ocupado.read_text(encoding="utf-8")).get("login"):
            return True
    except (OSError, ValueError, AttributeError):
        pass
    so_painel = PASTA / "SO_PAINEL"
    try:
        return (time.time() - so_painel.stat().st_mtime < 15 * 60
                and "login" in so_painel.read_text(encoding="utf-8", errors="replace").lower())
    except OSError:
        return False


def _esperar(seg):
    """Dorme `seg` olhando a cada 2 s; False = começou um login (o vídeo tem que sair da tela)."""
    fim = time.time() + seg
    while time.time() < fim:
        if login_em_andamento():
            return False
        time.sleep(min(2.0, max(0.0, fim - time.time())))
    return True


def tocar(url, seg, rotulo):
    """Toca e marca como tocado. Login começou no meio (dona 23/10: "se estivermos logando, não entrem vídeos —
    fiquem segurando pra mostrar depois"): fecha na hora e NÃO marca — o vídeo volta quando o login acabar."""
    painel_fechar()  # mesmo perfil do navegador: um de cada vez
    tela_sempre_acesa()
    volume_maximo()
    log(f"tocando {url} ({seg:.0f}s) {rotulo}")
    # 23/10 (dona: "um navegador por vez, em fila"): quem quer o notebook (login do TikTok, Veo) vê que está tocando
    tocando = PASTA / "TOCANDO"
    try:
        tocando.write_text(f"{url}\n", encoding="utf-8")
    except OSError:
        pass
    p = _abrir(url)
    if url.startswith("https://www.youtube.com/"):  # Acer, ou o X200MA quando ele é a reserva
        # 2ª exibição (o like/comentário falhou na 1ª): o aviso velho do PC1 não pode fechar o vídeo antes da hora
        (PASTA / "curtido" / url.split("#")[0].rstrip("/").split("/")[-1].split("v=")[-1][:11]).unlink(missing_ok=True)
        with open(PASTA / "curtir.txt", "a", encoding="utf-8") as f:  # o PC1 lê e dá o like (conta pessoal da dona)
            f.write(f"{url.split('#')[0]}\t{int(time.time())}\n")
    try:
        # duração + tempo de o navegador abrir e carregar no notebook fraco; NUNCA mais que 2 passadas do vídeo
        # (dono 22/10: "fecha só depois de terminar o vídeo; pode exibir no máximo duas vezes")
        if not _esperar(max(8.0, min(seg + 10, 2 * seg + 3))):
            log(f"login começou: {url} interrompido, volta depois")
            return
        if url.startswith("https://www.youtube.com/"):
            # 23/10: Short de 8 s fechava antes do PC1 dar o like (ele confere a cada 20 s). Espera o aviso dele
            # (~/vitrine/curtido/<id>) no máximo 120 s a mais (like + comentário: 40 s não davam nos Shorts de 20-40 s)
            vid = url.split("#")[0].rstrip("/").split("/")[-1].split("v=")[-1][:11]
            fim = time.time() + 120
            while time.time() < fim and not (PASTA / "curtido" / vid).exists():
                if login_em_andamento():  # o vídeo já passou inteiro: conta como tocado
                    break
                time.sleep(2)
    finally:
        _fechar(p)
        tocando.unlink(missing_ok=True)
        try:  # 24/10: fim do vídeo; o PC1 (maquina_remota.exibindo) espera 2 min antes de abrir outro Chrome aqui
            (PASTA / "TOCOU").write_text(f"{url}\n", encoding="utf-8")
        except OSError:
            pass
    with open(TOCADOS, "a", encoding="utf-8") as f:
        f.write(url + "\n")
    if url.startswith("file://"):  # vídeo de aprovação mandado pelo PC1: só serve pra esta exibição
        try:
            Path(urllib.parse.unquote(url[7:])).unlink()
        except OSError:
            pass


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    LOCAIS.mkdir(parents=True, exist_ok=True)
    # navegador que sobrou de um player anterior (ele roda em sessão própria) — fecha antes de começar
    subprocess.run(["pkill", "-f", "[v]itrine/perfil_navegador"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    servidor()
    try:  # vigia mútuo (dono 22/10): esta máquina também confere as outras e avisa no Telegram quem caiu
        import vigia_mutuo
        eu = {"acer": "Acer", "x200ma": "X200MA"}.get(_tela(), _tela())
        threading.Thread(target=vigia_mutuo.laco, args=(eu,), daemon=True).start()
    except Exception as e:  # noqa: BLE001
        log(f"vigia mútuo não ligou: {e}")
    log("telão ligado")
    ultima_tela = 0.0
    while True:
        if time.time() - ultima_tela > 60:  # reforça tela acesa + brilho + volume mesmo sem vídeo na fila
            try:
                tela_sempre_acesa()
                volume_maximo()
            except Exception as e:  # noqa: BLE001
                log(f"ajuste de tela/volume falhou: {e}")
            ultima_tela = time.time()
        # PAUSADO: crie ~/vitrine/PAUSADO pra parar de exibir. ocupado: o notebook está postando (só um Chrome por vez)
        ocupado = Path.home() / "postador-worker" / "ocupado"
        if (PASTA / "PAUSADO").exists():
            painel_fechar()
            time.sleep(30)
            continue
        try:  # o chrome_conta apaga o "ocupado" a qualquer hora: entre o exists e o stat o player morria (revisão 23/10)
            postando = ocupado.exists() and time.time() - ocupado.stat().st_mtime < 3 * 3600
        except OSError:
            postando = False
        if postando:
            # Chrome do postador aberto (postagem, Flow, Veo, login): dona 24/10 "estou vendo 2 navegadores, coisa que
            # não deveria acontecer" — um navegador por vez: sai o painel e os vídeos esperam na fila. O PC1 não abre
            # Chrome aqui com vídeo passando (maquina_remota.exibindo), então o telão não fica a manhã toda parado.
            painel_fechar()
            time.sleep(10)
            continue
        # dona 23/10: "o Veo não pode fazer se tiver exibindo vídeo". Máquina reservada pelo Veo (o PC1 põe/tira
        # ~/vitrine/SO_PAINEL a cada 2 min; velho de 15 min = PC1 parado, ignora): só o painel, a fila espera
        so_painel = PASTA / "SO_PAINEL"
        try:
            reservado = so_painel.exists() and time.time() - so_painel.stat().st_mtime < 15 * 60
        except OSError:
            reservado = False
        if reservado:
            try:  # login (dona: "login em andamento = nem exibição") fecha até o painel; Veo/outros: só o painel
                if "login" in so_painel.read_text(encoding="utf-8", errors="replace").lower():
                    painel_fechar()
                else:
                    painel_abrir()
            except Exception as e:  # noqa: BLE001
                log(f"painel falhou: {e}")
            time.sleep(10)
            continue
        # dona 23/10: vídeo só no Acer; o X200MA só recebe vídeo quando o Acer falha (o PC1 decide em vitrine.py)
        item = proximo()
        if item and login_em_andamento():  # SO_PAINEL de login chegou antes do ocupado (ou vice-versa): segura a fila
            painel_fechar()
            time.sleep(10)
            continue
        if item:
            try:
                tocar(*item)
            except Exception as e:  # noqa: BLE001
                log(f"falhou: {e}")
                time.sleep(20)
        else:
            try:
                painel_abrir()
            except Exception as e:  # noqa: BLE001
                log(f"painel falhou: {e}")
            time.sleep(5)  # confere a fila a cada 5 s: o botão "Abrir" responde rápido


if __name__ == "__main__":
    main()
