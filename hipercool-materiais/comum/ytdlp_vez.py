# -*- coding: utf-8 -*-
# COMUM — fonte única: D:\hipercool-materiais\comum\ytdlp_vez.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir ytdlp_vez.py --de <projeto>
"""ytdlp_vez.py — vez ÚNICA do yt-dlp neste PC, pra todos os projetos de vídeo.

Por quê: consultas do yt-dlp em paralelo (vários projetos ao mesmo tempo) bloquearam o IP da casa e pararam PC1 e
PC2. Aqui: 1 chamada por vez no PC inteiro (trava de arquivo do Windows — solta sozinha se o processo morrer) e
INTERVALO segundos entre o fim de uma e o começo da outra. Quem esperar mais de ESPERA_MAX segue assim mesmo (com
aviso no stderr): travar a produção por causa de uma vez presa é pior.

    import ytdlp_vez
    with ytdlp_vez.vez("parceiro: lista do canal"):
        subprocess.run(["yt-dlp", ...])

Dentro da vez, chamar vez() de novo no mesmo processo não espera (não trava a si mesmo).
"""
import contextlib
import json
import msvcrt
import os
import sys
import threading
import time
from pathlib import Path

TRAVA = Path(r"D:\video-fila\ytdlp_vez.lock")
ULTIMA = Path(r"D:\video-fila\ytdlp_vez.json")
INTERVALO = 6
ESPERA_MAX = 30 * 60
# Pausa quando o YouTube barra o IP (21/10: das 13h às 14h o parceiro tentou 33 vídeos, ~7 pedidos cada, todos
# barrados — cada pedido durante o bloqueio só alonga o bloqueio). Quem baixa pergunta pausado() antes.
PAUSA = Path(r"D:\video-fila\ytdlp_pausa.json")
PAUSA_MIN = 20
PAUSA_MAX = 120
# 21-22/10: em 7 de 14 bloqueios o IP foi barrado de novo 0-12 min depois do fim de uma pausa de 20 min (o YouTube
# ainda marcava o IP e o 1º pedido renovava o bloqueio): bloqueio até VOLTA_LOGO_MIN depois do fim da pausa dobra a próxima
VOLTA_LOGO_MIN = 30
SINAIS_BLOQUEIO = ("not a bot", "sign in to confirm", "http error 429", "too many requests")

_local = threading.local()


def bloqueio(texto):
    """True se a saída do yt-dlp é o YouTube barrando o IP (anti-robô / 429), não defeito do vídeo.
    429 só da LEGENDA (timedtext, comum com legenda traduzida) não conta: é outro limite e não barra o download."""
    linhas = (texto or "").lower().replace("’", "'").replace(" | ", "\n").splitlines()
    return any(s in l for l in linhas if "subtitle" not in l for s in SINAIS_BLOQUEIO)


# ─── proxy Webshare pras consultas PEQUENAS (22/10, dono: "falei pra usar o webshare") ────────────────────────
# Listagem/legenda/metadado (KB) sai por proxy rotativo e NÃO gasta o IP da casa; o DOWNLOAD grande (MB)
# continua direto ou pela VPS (baixar_vps) — a banda da Webshare é limitada e um mp4 a evaporaria.
PROXIES_TXT = (Path(r"D:\hipercool-videos\secrets\proxies.txt"),
               Path(r"D:\postador-de-videos\secrets\proxies.txt"))
PROXY_ESTADO = Path(r"D:\video-fila\ytdlp_proxy.json")
PROXY_RUIM_MIN = 60  # proxy que falhou volta pra roda em 1 h (a Webshare renova banda sozinha)


def _sem_banda():
    """09/11: contas com 402 na última medição da tarefa WebshareSaude (D:\\video-fila\\estado\\webshare.json) — o
    sorteio caía nelas e a lista do canal falhava inteira. WEBSHARE_PULA_402=0 desliga."""
    if os.environ.get("WEBSHARE_PULA_402", "1") == "0":
        return set()
    try:
        j = json.loads(Path(r"D:\video-fila\estado\webshare.json").read_text(encoding="utf-8"))
        return {c["conta"] for c in j.get("contas", []) if "402" in str(c.get("estado"))}
    except (OSError, ValueError, KeyError):
        return set()


def _proxies():
    fora = _sem_banda()
    for arq in PROXIES_TXT:
        try:
            linhas = [l.split("#")[0].strip() for l in arq.read_text(encoding="utf-8").splitlines()]
            out = [l for l in linhas if l.startswith("http")]
            limpo = [l for l in out if l.split("//", 1)[-1].split("-rotate", 1)[0] not in fora]
            out = limpo or out
            if out:
                return out
        except OSError:
            continue
    return []


def proxy_url():
    """Um proxy da rotação (http://<USUARIO>:<SEGREDO_REMOVIDO>@host:porta) ou None (sem lista = comportamento antigo, direto)."""
    todos = _proxies()
    if not todos:
        return None
    try:
        est = json.loads(PROXY_ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {}
    import hashlib
    agora = time.time()
    ruins = {k: v for k, v in (est.get("ruins") or {}).items() if v > agora}
    vivos = [p for p in todos if hashlib.md5(p.encode()).hexdigest()[:12] not in ruins] or todos
    i = int(est.get("i", -1)) + 1
    try:
        PROXY_ESTADO.write_text(json.dumps({"i": i, "ruins": ruins}), encoding="utf-8")
    except OSError:
        pass
    return vivos[i % len(vivos)]


def proxy_ruim(url, motivo=""):
    """Tira o proxy da roda por PROXY_RUIM_MIN (bloqueio/timeout é do PROXY, não do IP da casa — não pausar o PC)."""
    if not url:
        return
    import hashlib
    try:
        est = json.loads(PROXY_ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {}
    est.setdefault("ruins", {})[hashlib.md5(url.encode()).hexdigest()[:12]] = time.time() + PROXY_RUIM_MIN * 60
    try:
        PROXY_ESTADO.write_text(json.dumps(est), encoding="utf-8")
    except OSError:
        pass
    print(f"[ytdlp_vez] proxy fora da roda por {PROXY_RUIM_MIN} min ({(motivo or '')[:80]})", file=sys.stderr)


# 22/10 (dono: "entender qual o máximo pra não ficar batendo"): espaçamento ADAPTATIVO entre DOWNLOADS grandes —
# cada bloqueio do dia aumenta o espaço mínimo entre downloads (0 bloqueios = sem espaço; 1-2 = 5 min; 3-5 = 10;
# 6+ = 15). A espera é dormindo ANTES de pegar a vez (devagar, nunca erro) e não segura as consultas pequenas.
BLOQUEIOS = Path(r"D:\video-fila\ytdlp_bloqueios.json")
DL_TS = Path(r"D:\video-fila\ytdlp_download_ts.json")


def _bloqueios_hoje(bump=False):
    hoje = time.strftime("%Y-%m-%d")
    try:
        d = json.loads(BLOQUEIOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    if d.get("dia") != hoje:
        d = {"dia": hoje, "n": 0}
    if bump:
        d["n"] = int(d.get("n", 0)) + 1
        try:
            BLOQUEIOS.write_text(json.dumps(d), encoding="utf-8")
        except OSError:
            pass
    return int(d.get("n", 0))


def _espaco_download_s():
    n = _bloqueios_hoje()
    return 0 if n == 0 else 300 if n <= 2 else 600 if n <= 5 else 900


def pausar(motivo="", minutos=None):
    """Pausa o yt-dlp do PC inteiro (vale pra todo projeto que pergunta pausado()). Sem `minutos`: PAUSA_MIN; se o
    bloqueio voltou até VOLTA_LOGO_MIN depois do fim da pausa anterior, o dobro dela (até PAUSA_MAX); outro processo
    vendo o MESMO bloqueio durante a pausa não dobra."""
    agora = time.time()
    if minutos is None:
        minutos = PAUSA_MIN
        try:
            ant = json.loads(PAUSA.read_text(encoding="utf-8"))
            ant_ate, ant_min = float(ant.get("ate") or 0), int(ant.get("minutos") or PAUSA_MIN)
            if ant_ate > agora:
                minutos = ant_min
            elif agora - ant_ate < VOLTA_LOGO_MIN * 60:
                minutos = min(PAUSA_MAX, ant_min * 2)
        except (OSError, ValueError, AttributeError, TypeError):
            pass
    try:
        PAUSA.write_text(json.dumps({"ate": agora + minutos * 60, "minutos": minutos, "motivo": (motivo or "")[-200:],
                                     "pid": os.getpid()}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    n = _bloqueios_hoje(bump=True)  # 22/10: alimenta o espaçamento adaptativo dos downloads
    print(f"[ytdlp_vez] YouTube barrando o IP: yt-dlp em pausa por {minutos} min ({n}º bloqueio hoje)", file=sys.stderr)


def espera_download_s():
    """23/10: segundos que o próximo download grande vai esperar no espaçamento (0 = sai na hora). Só lê: quem tem outra
    opção (o estoque do recap) usa ela em vez de dormir."""
    espaco = _espaco_download_s()
    if not espaco:
        return 0.0
    try:
        ultimo = float(json.loads(DL_TS.read_text(encoding="utf-8")).get("fim") or 0)
    except (OSError, ValueError):
        return 0.0
    return max(0.0, ultimo + espaco - time.time())


def pausado():
    """Segundos que faltam da pausa (0 = pode usar o yt-dlp)."""
    try:
        ate = float(json.loads(PAUSA.read_text(encoding="utf-8")).get("ate") or 0)
    except (OSError, ValueError, AttributeError):
        return 0
    return max(0.0, ate - time.time())


PRIO_PC2 = Path(r"D:\video-fila\ytdlp_prioridade_pc2.json")


def _vivo(pid):
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        codigo = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(codigo))
        ctypes.windll.kernel32.CloseHandle(h)
        return codigo.value == 259  # STILL_ACTIVE
    except Exception:  # noqa: BLE001
        return False


def _pc2_esperando():
    """Há um preparo do PC2 (vivo, < 20 min) esperando a vez do yt-dlp?"""
    try:
        d = json.loads(PRIO_PC2.read_text(encoding="utf-8"))
        return time.time() - float(d.get("desde") or 0) < 20 * 60 and int(d.get("pid") or 0) != os.getpid() \
            and _vivo(d.get("pid"))
    except (OSError, ValueError, TypeError):
        return False


def _soltar_prio_pc2():
    try:
        if int(json.loads(PRIO_PC2.read_text(encoding="utf-8")).get("pid") or 0) == os.getpid():
            PRIO_PC2.unlink(missing_ok=True)
    except (OSError, ValueError):
        pass


@contextlib.contextmanager
def vez(rotulo=""):
    if getattr(_local, "dentro", 0):
        _local.dentro += 1
        try:
            yield
        finally:
            _local.dentro -= 1
        return
    # 22/10: espaçamento adaptativo SÓ pros downloads grandes — dorme ANTES de pegar a vez (não trava os pequenos)
    eh_download = "download" in (rotulo or "").lower()
    if eh_download:
        espaco = _espaco_download_s()
        while espaco:
            try:
                ultimo = float(json.loads(DL_TS.read_text(encoding="utf-8")).get("fim") or 0)
            except (OSError, ValueError):
                break
            falta = ultimo + espaco - time.time()
            if falta <= 0:
                break
            print(f"[ytdlp_vez] espaçando downloads ({_bloqueios_hoje()} bloqueio(s) hoje): "
                  f"esperando {falta / 60:.0f} min", file=sys.stderr)
            time.sleep(min(falta, 60))
    try:
        TRAVA.parent.mkdir(parents=True, exist_ok=True)
        f = open(TRAVA, "a+b")
    except OSError:  # PC2/desktop recebem o bin/ por cópia e não têm D:\video-fila: segue sem a vez
        yield
        return
    t0, pegou = time.time(), False
    # 30/10 (D39, dona: "a prioridade do que for baixado é do PC2"): o preparo do Short do PC2 marca YTDLP_PRIORIDADE=pc2;
    # enquanto ele espera a vez, os outros (Cortes do PC1, ER...) não pegam a trava. Pedido de processo morto ou com
    # mais de 20 min não vale.
    prio_pc2 = os.environ.get("YTDLP_PRIORIDADE") == "pc2"
    if prio_pc2:
        try:
            PRIO_PC2.write_text(json.dumps({"pid": os.getpid(), "desde": time.time(), "rotulo": rotulo}), encoding="utf-8")
        except OSError:
            prio_pc2 = False
    while True:
        if not prio_pc2 and _pc2_esperando() and time.time() - t0 < ESPERA_MAX:
            time.sleep(2)
            continue
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            pegou = True
            if prio_pc2:
                _soltar_prio_pc2()
            break
        except OSError:
            if time.time() - t0 > ESPERA_MAX:
                print(f"[ytdlp_vez] esperou {ESPERA_MAX // 60} min pela vez do yt-dlp ({rotulo}); seguindo sem ela",
                      file=sys.stderr)
                break
            time.sleep(2)
    _local.dentro = 1
    # 22/10 (dono: "falei pra usar o webshare"): operação PEQUENA (busca/legenda/probe/lista, KB) sai por proxy
    # rotativo via env http_proxy — cobre todos os chamadores sem mexer neles; DOWNLOAD (MB) segue direto (a
    # banda da Webshare é limitada). Quem passa --proxy explícito não é afetado (a flag vence a env).
    import re as _re
    px = proxy_url() if _re.search(r"busca|legenda|lista|probe|metad|checar|canal|discover|search|sub",
                                   rotulo or "", _re.I) else None
    env_antes = {k: os.environ.get(k) for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY")}
    if px:
        for k in env_antes:
            os.environ[k] = px
    try:
        try:
            ult = float(json.loads(ULTIMA.read_text(encoding="utf-8")).get("fim") or 0)
        except (OSError, ValueError):
            ult = 0.0
        falta = ult + INTERVALO - time.time()
        if falta > 0:
            time.sleep(min(falta, INTERVALO))
        yield
    finally:
        if px:
            for k, v in env_antes.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        if eh_download:
            try:
                DL_TS.write_text(json.dumps({"fim": time.time(), "rotulo": rotulo}), encoding="utf-8")
            except OSError:
                pass
        _local.dentro = 0
        try:
            ULTIMA.write_text(json.dumps({"fim": time.time(), "rotulo": rotulo, "pid": os.getpid()}), encoding="utf-8")
        except OSError:
            pass
        if pegou:
            try:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        f.close()
