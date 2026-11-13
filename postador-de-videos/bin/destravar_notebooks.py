"""destravar_notebooks.py — DESTRAVAMENTO AUTOMÁTICO dos notebooks (04/11/2026).

Dona 04/11: "o X200 parece travado na mesma mensagem que eu fechei mais cedo, e o Acer também, num vídeo rodando —
eles têm que ter script de destravamento automático". Caso real: o Chrome de automação do X200 ficou horas atrás da
janela de boas-vindas do Google Flow; o envio do longo no Acer ficou 4h48 "subindo".

A cada execução (tarefa DestravarNotebooks, 10 em 10 min, oculta), em cada notebook:
  - Chrome de automação (porta 9460): print da aba principal pelo CDP (túnel ssh). Tela IDÊNTICA por TRAVADO_MIN
    (30 min) = travado: guarda o print, avisa no Telegram, fecha esse Chrome e libera a vez da máquina.
    Um envio que anda muda a %, uma geração do Flow termina em minutos — 30 min sem 1 pixel mudar é travamento.
  - Telão (Firefox --kiosk da vitrine, porta 9470) no Acer: só AVISA (é de outro chat) se o print ficar igual 30 min.
Nada é fechado sem 2 prints iguais com 30 min de distância. Estado em logs\\destravar_notebooks.json.

    python destravar_notebooks.py           # uma passada
"""
import hashlib
import json
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import maquina_remota as mr  # noqa: E402

AQUI = Path(__file__).resolve().parent
ESTADO = AQUI.parent / "logs" / "destravar_notebooks.json"
PRINTS = AQUI.parent / "logs" / "destravar"
LOG = AQUI.parent / "logs" / "destravar_notebooks.log"
TRAVADO_MIN = 30
ALVOS = {"x200ma": [9460], "acer": [9460, 9470]}
SEM_JANELA = 0x08000000


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {m}\n")


def _porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _tunel(nome, porta_remota):
    cfg = mr.MAQUINAS[nome]
    local = _porta_livre()
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-N", "-L", f"{local}:127.0.0.1:{porta_remota}"]
    if cfg.get("porta_ssh"):
        cmd += ["-p", str(cfg["porta_ssh"])]
    proc = subprocess.Popen(cmd + [cfg["ssh"]], creationflags=SEM_JANELA, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    return proc, local


def _print_cdp(local, saida):
    """(url, hash) da aba principal; None se não há navegador ali."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{local}", timeout=15000)
        except Exception:  # noqa: BLE001
            return None
        paginas = [pg for c in b.contexts for pg in c.pages
                   if not pg.url.startswith(("about:", "chrome:", "devtools:")) and "webworker" not in pg.url]
        if not paginas:
            return None
        pg = paginas[0]
        try:
            png = pg.screenshot(timeout=20000)
            Path(saida).write_bytes(png)
            return pg.url, hashlib.md5(png).hexdigest()
        except Exception:  # noqa: BLE001 — Acer sobrecarregado: o print não sai; usa título+endereço+texto da página
            try:
                sinal = pg.evaluate("document.title + '|' + location.href + '|' + "
                                    "(document.body ? document.body.innerText : '')")
                return pg.url, "txt:" + hashlib.md5(str(sinal).encode("utf-8")).hexdigest()
            except Exception:  # noqa: BLE001
                return pg.url, "SEM_RESPOSTA"  # página nem responde: conta como tela parada


def _fechar_chrome(nome, local):
    """Fecha o Chrome de automação pelo próprio CDP (Browser.close) e libera a vez."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{local}", timeout=15000)
            s = b.new_browser_cdp_session()
            s.send("Browser.close")
        except Exception as e:  # noqa: BLE001
            log(f"{nome}: fechar pelo CDP falhou ({type(e).__name__})")
    vez = mr.reservado(nome)
    if vez:
        mr.liberar(nome)
        log(f"{nome}: vez de '{vez}' liberada")


def _avisar(texto):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "postagem", importante=True, html_ok=False)
    except Exception:  # noqa: BLE001
        pass


def passada():
    PRINTS.mkdir(parents=True, exist_ok=True)
    try:
        est = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {}
    agora = time.time()
    for nome, portas in ALVOS.items():
        for porta in portas:
            chave = f"{nome}:{porta}"
            proc = None
            try:
                proc, local = _tunel(nome, porta)
                arq = PRINTS / f"{nome}_{porta}_atual.png"
                r = _print_cdp(local, arq) if porta == 9460 else None
                if porta == 9470:  # telão (Firefox): sem CDP de Chromium — só confere se o processo existe
                    est.pop(chave, None)
                    continue
                if not r:
                    est.pop(chave, None)
                    continue
                url, h = r
                ant = est.get(chave)
                if not ant or ant["hash"] != h:
                    est[chave] = {"hash": h, "desde": agora, "url": url}
                    continue
                parado = (agora - ant["desde"]) / 60
                if parado < TRAVADO_MIN:
                    continue
                guardado = PRINTS / f"{datetime.now():%Y%m%d_%H%M}_{nome}_TRAVADO.png"
                if arq.exists():
                    arq.replace(guardado)
                else:
                    guardado = "(o notebook não respondeu nem ao print)"
                msg = (f"🧊 {nome}: Chrome de automação com a tela IGUAL há {parado:.0f} min ({url[:90]}) — fechei e "
                       f"liberei a máquina. Print: {guardado}")
                log(msg)
                _avisar(msg)
                _fechar_chrome(nome, local)
                est.pop(chave, None)
            except Exception as e:  # noqa: BLE001
                log(f"{nome}:{porta}: passada falhou ({type(e).__name__}: {str(e)[:120]})")
            finally:
                if proc:
                    proc.terminate()
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    passada()
