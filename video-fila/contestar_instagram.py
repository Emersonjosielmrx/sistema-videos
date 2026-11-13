r"""contestar_instagram.py — abre as contas suspensas do Instagram UMA POR VEZ, visíveis, pra dona contestar (10/11).

Cada conta abre no Chrome dela do cofre (perfil e máquina de sempre — nada de conta nova no mesmo navegador).
Passa pra próxima quando:
  - a dona FECHA a janela, ou
  - a página muda pra confirmação de contestação enviada (o script fecha sozinho), ou
  - 30 min sem nada (fecha e segue).
Registro: logs\contestar_instagram.log e estado\contestacoes_ig.json (quando contestou; conferir ~1 h depois).

    wscript D:\rodar_oculto.vbs python D:\video-fila\contestar_instagram.py ig_conta1 ig_conta2 ...
"""
import json
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
import websocket  # noqa: E402

BASE = Path(__file__).resolve().parent
LOG = BASE / "logs" / "contestar_instagram.log"
REG = BASE / "estado" / "contestacoes_ig.json"
FEITO = re.compile(r"recebemos|enviamos (sua|seu)|em análise|em revisão|vamos analisar|analisaremos|we received|"
                   r"under review|we'll review|appeal (was )?submitted|solicitação (foi )?enviada|obrigad[oa] por", re.I)
MAX_S = 30 * 60


def log(t):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {t}"
    print(linha, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _paginas(porta):
    try:
        return [x for x in json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json", timeout=5).read())
                if x.get("type") == "page"]
    except Exception:  # noqa: BLE001
        return None  # janela fechada


def _texto(pg):
    try:
        ws = websocket.create_connection(pg["webSocketDebuggerUrl"], timeout=10)
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                            "params": {"expression": "document.body ? document.body.innerText : ''",
                                       "returnByValue": True}}))
        for _ in range(20):
            m = json.loads(ws.recv())
            if m.get("id") == 1:
                ws.close()
                return ((m.get("result") or {}).get("result") or {}).get("value") or ""
        ws.close()
    except Exception:  # noqa: BLE001
        pass
    return ""


def _fechar(porta):
    try:
        info = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=5).read())
        ws = websocket.create_connection(info["webSocketDebuggerUrl"], timeout=10)
        ws.send(json.dumps({"id": 1, "method": "Browser.close"}))
        ws.close()
    except Exception:  # noqa: BLE001
        pass


def _registrar(nome, como):
    try:
        d = json.loads(REG.read_text("utf-8"))
    except (OSError, ValueError):
        d = {}
    d[nome] = {"quando": datetime.now().isoformat(timespec="minutes"), "como": como}
    REG.parent.mkdir(parents=True, exist_ok=True)
    REG.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def uma(nome):
    porta, _proc = cofre.abrir(nome, "https://www.instagram.com/", visivel=True)
    log(f"{nome}: aberta (porta {porta}) — esperando a dona contestar")
    time.sleep(8)
    pgs = _paginas(porta) or []
    inicial = " ".join(_texto(p) for p in pgs)
    url0 = " ".join(p.get("url", "") for p in pgs)
    if pgs and "suspended" not in url0 and "challenge" not in url0 and "disabled" not in url0:
        log(f"{nome}: não está na tela de suspensão ({url0[:90]}) — pode já ter voltado")
        # 12/11 dona ("várias contas que abriu já estavam logadas normal, não precisou contestar"): conta normal fecha
        # sozinha e tira a pausa dela (volta a postar); não fica esperando a dona. CONTESTAR_PULA_NORMAL=0 desliga.
        import os as _os
        if _os.environ.get("CONTESTAR_PULA_NORMAL", "1") != "0":
            _fechar(porta)
            _registrar(nome, "estava normal (sem suspensão) — liberada")
            try:  # tira a pausa (config\instagram_pausas.json do postar_insta_auto): a conta volta a postar
                arq = Path(r"D:\postador-de-videos\config\instagram_pausas.json")
                pz = json.loads(arq.read_text(encoding="utf-8"))
                curto = nome.replace("ig_", "", 1)
                for k in [k for k in pz if k in (nome, curto)]:
                    pz.pop(k)
                arq.write_text(json.dumps(pz, ensure_ascii=False, indent=1), encoding="utf-8")
            except (OSError, ValueError):
                pass
            log(f"{nome}: normal — fechada sozinha, segue a próxima")
            return
    fim = time.time() + MAX_S
    while time.time() < fim:
        time.sleep(5)
        pgs = _paginas(porta)
        if pgs is None or not pgs:
            log(f"{nome}: a dona fechou a janela")
            _registrar(nome, "janela fechada pela dona")
            return
        txt = " ".join(_texto(p) for p in pgs)
        achou = FEITO.search(txt)
        if achou and not FEITO.search(inicial):
            log(f"{nome}: contestação enviada ('{achou.group(0)}') — fechando em 6 s")
            _registrar(nome, f"confirmação na tela: {achou.group(0)}")
            time.sleep(6)
            _fechar(porta)
            return
    log(f"{nome}: 30 min sem contestar — fechando e seguindo")
    _fechar(porta)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for nome in sys.argv[1:]:
        try:
            uma(nome)
        except Exception as e:  # noqa: BLE001
            log(f"{nome}: erro {type(e).__name__}: {str(e)[:150]}")
        time.sleep(3)
    log("fim da lista")


if __name__ == "__main__":
    main()
