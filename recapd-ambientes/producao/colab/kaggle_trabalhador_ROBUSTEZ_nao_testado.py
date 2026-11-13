"""Roda no KAGGLE (conta emersonjosiel649, kernel CPU com internet) e nas VPS (Docker, variáveis TRAB_*): mesmo trabalho
do trabalhador.py da Colab, mas lendo a fila pelo rclone. Plano: producao/COLAB_RECAP_LONGO.md e colab/MELHORIAS_ROBUSTEZ.md.

25/10 (robustez): rclone tenta de novo com espera crescente (o Google devolve 403 de cota na chave pública do rclone a
qualquer hora); uma listagem só da fila por rodada; sinal de vida a cada 10 min DURANTE o render (marca própria + vivo);
confere o vídeo pronto antes de entregar; o laço não morre por exceção; quando parado, troca sozinho pelo trabalhador
novo do Drive (manhwa-drive:colab_recap/kaggle_trabalhador.py). Kaggle ganha nome por sessão (kaggle-MMDDHHMM).
"""
import hashlib
import io
import json
import os
import random
import re
import shutil
import site
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# relógio da sessão sobrevive à troca de versão (Kaggle corta 12 h depois do início do kernel, não da versão nova)
INICIO = float(os.environ.get("TRAB_INICIO") or time.time())
os.environ["TRAB_INICIO"] = str(INICIO)
# Kaggle corta em 12 h e um longo leva horas: pedido novo só nas primeiras 6 h. Na VPS (Docker): TRAB_LIMITE_H=0 = sem fim
_LIM_H = float(os.environ.get("TRAB_LIMITE_H", "6"))
LIMITE_S = _LIM_H * 3600 if _LIM_H > 0 else float("inf")
BASE = Path(os.environ.get("TRAB_BASE", "/kaggle/working"))
# nome por sessão no Kaggle: duas sessões com o mesmo nome se achariam "eu" e pegariam o mesmo pedido
QUEM = os.environ.get("TRAB_NOME") or f"kaggle-{datetime.fromtimestamp(INICIO, timezone.utc):%m%d%H%M}"
os.environ["TRAB_NOME"] = QUEM
CONF = Path(os.environ["RCLONE_CONF"]) if os.environ.get("RCLONE_CONF") else next(Path("/kaggle/input").rglob("rclone.conf"))
RC = Path(os.environ.get("TRAB_RCLONE") or (BASE / "rclone"))
FILA = os.environ.get("TRAB_FILA", "manhwa-drive:colab_recap/fila")
FILA_SRC = os.environ.get("TRAB_FILA_SRC", "manhwa-drive:colab_recap/fila_src")
RAIZ_REMOTA = os.environ.get("TRAB_RAIZ", "manhwa-drive:colab_recap/raiz")
VIVO_DIR = FILA.rsplit("/", 1)[0]
EU_REMOTO = f"{VIVO_DIR}/kaggle_trabalhador.py"
os.environ["RCLONE_DRIVE_USE_TRASH"] = "false"
RAIZ = BASE / "raiz"
PRODUCAO = RAIZ / "D/recapd-ambientes/producao"
TRABALHO = BASE / "trabalho"
os.environ["RAIZ_WIN"] = str(RAIZ)
PULSO_S = int(os.environ.get("TRAB_PULSO_S", "600"))
ESPERA_VAZIA_S = int(os.environ.get("TRAB_ESPERA_S", "90"))
_TRANSITORIO = ("quota", "rate limit", "ratelimit", "userratelimit", "403", "429", "500", "502", "503", "504",
                "timeout", "timed out", "connection reset", "connection refused", "unexpected eof", "tls handshake",
                "no such host", "temporary", "try again", "internal error", "backend error")


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rc(*args, tentativas=7):
    """rclone com nova tentativa: cota (403/429), 5xx e rede esperam 20 s, 40 s ... até 10 min (~20 min no total).
    'não existe' (rc 3/4) e erro de uso sobem na hora — quem chama decide."""
    for i in range(tentativas):
        r = subprocess.run([str(RC), "--config", str(CONF), *args], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout
        err = (r.stderr or "")[-800:]
        transitorio = r.returncode in (5, 6, 8) or (r.returncode not in (1, 3, 4)
                                                    and any(t in err.lower() for t in _TRANSITORIO))
        if not transitorio or i == tentativas - 1:
            raise RuntimeError(f"rclone {args[0]} (rc={r.returncode}): {err[-300:]}")
        espera = min(600, 20 * 2 ** i) + random.uniform(0, 15)
        print(f"[{_agora()}] rclone {args[0]} falhou (temporário, rc={r.returncode}) — de novo em {espera:.0f} s",
              flush=True)
        time.sleep(espera)


def preparar():
    # gravável (o rclone regrava o token) e FORA do /kaggle/working, que vira saída pública do kernel
    if not os.environ.get("RCLONE_CONF"):
        conf = Path("/tmp/rclone.conf")
        shutil.copy(CONF, conf)
        globals()["CONF"] = conf
    if not RC.exists():
        pedido = urllib.request.Request("https://downloads.rclone.org/rclone-current-linux-amd64.zip",
                                        headers={"User-Agent": "Mozilla/5.0"})  # sem UA o site responde 403
        z = urllib.request.urlopen(pedido).read()
        with zipfile.ZipFile(io.BytesIO(z)) as zf:
            nome = next(n for n in zf.namelist() if n.endswith("/rclone"))
            RC.write_bytes(zf.read(nome))
        RC.chmod(0o755)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "edge-tts==7.3.1", "opencv-python-headless",
                    "psutil", "pydub", "soundfile"], check=True)
    t0 = time.time()
    rc("copy", RAIZ_REMOTA, str(RAIZ), "--transfers", "16", "--checkers", "32", "--fast-list")
    print(f"raiz copiada em {time.time() - t0:.0f} s", flush=True)
    sp = Path(site.getsitepackages()[0])
    rc("copyto", f"{VIVO_DIR}/sitecustomize.py", str(sp / "colab_traduz.py"))
    (sp / "colab_traduz.pth").write_text("import colab_traduz\n")
    (PRODUCAO / "workspace" / "anime").mkdir(parents=True, exist_ok=True)
    if not (PRODUCAO / "workspace" / "assets").exists():
        os.symlink(RAIZ / "D/hipercool-materiais/assets", PRODUCAO / "workspace" / "assets")
    (PRODUCAO / "venv" / "Scripts").mkdir(parents=True, exist_ok=True)
    py = PRODUCAO / "venv" / "Scripts" / "python.exe"
    if not py.exists():
        os.symlink(sys.executable, py)


def _marcar(pid, nome, dados, destino=None):
    tmp = BASE / f"_{threading.get_ident()}_{nome}"  # o pulso grava em paralelo com o laço
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        rc("copyto", str(tmp), destino or f"{FILA}/{pid}/{nome}")
    finally:
        tmp.unlink(missing_ok=True)


def _fila():
    """{pid: {arquivo}} numa chamada só (antes: 1 + 1 por pedido a cada minuto, por trabalhador)."""
    out = {}
    for i in json.loads(rc("lsjson", "-R", "--files-only", "--max-depth", "2", FILA) or "[]"):
        if "/" in i["Path"]:
            pid, nome = i["Path"].split("/", 1)
            out.setdefault(pid, set()).add(nome)
    return out


def _livre(arquivos):
    return "pedido.json" in arquivos and not ({"pronto.json", "erro.json"} & arquivos
                                              or any(a.startswith("em_andamento") for a in arquivos))


def proximo():
    fila = _fila()
    for pid in sorted(fila):
        if _livre(fila[pid]) and _pegar(pid):
            return pid
    return None


def _pegar(pid):
    """Marca o pedido e confere se ficou só pra mim. 25/10: Kaggle e VPS pegaram o MESMO pedido no mesmo segundo (os
    dois liam "livre" e gravavam em_andamento.json; o Drive aceita 2 arquivos com o mesmo nome) e renderizaram o mesmo
    vídeo 2x. Agora: marca própria em_andamento_<QUEM>.json + o em_andamento.json de sempre (os trabalhadores antigos só
    olham esse), espera, e se houver outra marca, fica quem marcou primeiro (empate: nome). Quem perde desiste."""
    eu = {"desde": _agora(), "por": QUEM, "pulso": _agora(), "v": 2}
    _marcar(pid, f"em_andamento_{QUEM}.json", eu)
    _marcar(pid, "em_andamento.json", eu)
    time.sleep(15)
    itens = json.loads(rc("lsjson", f"{FILA}/{pid}", "--files-only"))
    nomes = [i["Name"] for i in itens]
    rivais = []
    for n in sorted(set(nomes)):
        if n.startswith("em_andamento_") and n != f"em_andamento_{QUEM}.json":
            try:
                d = json.loads(rc("cat", f"{FILA}/{pid}/{n}"))
                rivais.append((d.get("desde", ""), d.get("por", n)))
            except (RuntimeError, ValueError):
                rivais.append(("", n))
    # trabalhador antigo (só em_andamento.json, sem marca própria): 2 cópias do nome, ou a cópia única regravada por
    # outro depois da minha = alguém além de mim
    if not rivais:
        if nomes.count("em_andamento.json") > 1:
            rivais.append(("", "trabalhador antigo"))
        else:
            try:
                por = json.loads(rc("cat", f"{FILA}/{pid}/em_andamento.json")).get("por")
            except (RuntimeError, ValueError):
                por = QUEM
            if por and por != QUEM:
                rivais.append(("", por))
    if any((d, p) < (eu["desde"], QUEM) for d, p in rivais):
        print(f"[{_agora()}] {pid}: já pego por {', '.join(p for _, p in rivais)} — deixo pra ele", flush=True)
        try:
            rc("deletefile", f"{FILA}/{pid}/em_andamento_{QUEM}.json")
        except RuntimeError:
            pass
        return False
    _Pulso.desde[pid] = eu["desde"]
    return True


class _Pulso(threading.Thread):
    """Sinal de vida durante o render: renova a marca do pedido e o vivo a cada PULSO_S. Marca parada > 45 min = o
    alimentador solta o pedido pra outro trabalhador (trabalhador morto não prende mais pedido)."""
    desde = {}

    def __init__(self, pid):
        super().__init__(daemon=True)
        self.pid, self.parar = pid, threading.Event()

    def run(self):
        while not self.parar.wait(PULSO_S):
            agora = _agora()
            try:
                _marcar(self.pid, f"em_andamento_{QUEM}.json",
                        {"desde": self.desde.get(self.pid, agora), "por": QUEM, "pulso": agora, "v": 2})
                _marcar(None, f"vivo_{QUEM}.json", {"em": agora, "pedido": self.pid},
                        destino=f"{VIVO_DIR}/vivo_{QUEM}.json")
            except Exception as e:  # noqa: BLE001 — pulso que falha não pode derrubar o render
                print(f"[{agora}] pulso falhou: {e}", flush=True)


def _duracao(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip() or 0)
    except ValueError:
        return 0.0


def conferir(final, fonte):
    """Vídeo pronto ruim não vai pro Drive (25/10). None = ok; texto = motivo."""
    d, ds = _duracao(final), _duracao(fonte)
    if d < 60:
        return f"vídeo pronto curto demais ({d:.0f} s)"
    if ds and d < 0.25 * ds:
        return f"vídeo pronto com {d / 60:.0f} min para original de {ds / 60:.0f} min"
    a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of",
                        "csv=p=0", str(final)], capture_output=True, text=True)
    if not a.stdout.strip():
        return "vídeo pronto sem áudio"
    for frac in (0.1, 0.5, 0.9):  # narração em 3 pontos do vídeo
        r = subprocess.run(["ffmpeg", "-v", "info", "-ss", f"{d * frac:.0f}", "-t", "20", "-i", str(final),
                            "-vn", "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
        m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stderr or "")
        if m and float(m.group(1)) > -50:
            return None
    return "vídeo pronto mudo (volume abaixo de -50 dB nos 3 pontos conferidos)"


def _soltar(pid):
    for marca in (f"em_andamento_{QUEM}.json", "em_andamento.json"):
        try:
            rc("deletefile", f"{FILA}/{pid}/{marca}")
        except RuntimeError:
            pass


def fazer(pid):
    local = TRABALHO / pid
    shutil.rmtree(local, ignore_errors=True)
    pulso = _Pulso(pid)
    pulso.start()
    try:
        rc("copy", f"{FILA}/{pid}", str(local))
        if not (local / "source.mp4").exists():  # pedidos novos: original no manhwa-drive (Drive da 649 é pequeno)
            try:
                rc("copyto", f"{FILA_SRC}/{pid}/source.mp4", str(local / "source.mp4"))
            except RuntimeError as e:  # sem original: vira erro.json logo abaixo (antes derrubava o trabalhador)
                print(f"[{_agora()}] {pid}: original não baixou: {e}", flush=True)
        for parte in ("bin", "config", "secrets"):  # código novo do PC
            rc("copy", f"{RAIZ_REMOTA}/D/recapd-ambientes/producao/{parte}", str(PRODUCAO / parte))
        pedido = json.loads((local / "pedido.json").read_text(encoding="utf-8"))
        print(f"[{_agora()}] pedido {pid}: {pedido.get('titulo', '')[:60]}", flush=True)
        t0 = time.time()
        fonte = local / "source.mp4"
        if not fonte.exists() or fonte.stat().st_size < 1_000_000:  # 25/10: sem isto narrava 2 h um vídeo que não existia
            _marcar(pid, "erro.json", {"ok": False, "error": "original (source.mp4) não chegou", "segundos": 0,
                                       "por": QUEM})
            print(f"[{_agora()}] {pid}: ERRO sem original", flush=True)
            return
        log = local / "pipeline.log"
        cmd = [sys.executable, "-X", "utf8", str(PRODUCAO / "bin" / "anime-pipeline.py"),
               "--video-source", str(fonte), "--script", str(local / "roteiro.txt"),
               "--titulo", pedido["titulo"], "--formato", "deitado"]
        with open(log, "w", encoding="utf-8") as f:
            rcod = subprocess.run(cmd, cwd=PRODUCAO, stdout=f, stderr=subprocess.STDOUT,
                                  env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
                                       "GEMINI_TTS_PROXY_ENABLED": "0"}).returncode
        seg = round(time.time() - t0)
        final = local / "final_anime_deitado.mp4"
        try:
            rc("copyto", str(log), f"{FILA}/{pid}/pipeline.log")
        except RuntimeError as e:
            print(f"[{_agora()}] log não subiu: {e}", flush=True)
        motivo = None if rcod == 0 and final.exists() else (f"rc={rcod}" if rcod else "sem final")
        if not motivo:
            motivo = conferir(final, fonte)
        if not motivo:
            rc("copyto", str(final), f"{FILA_SRC}/{pid}/final_anime_deitado.mp4")
            _marcar(pid, "pronto.json", {"fim": _agora(), "segundos": seg, "por": QUEM,
                                         "duracao_s": round(_duracao(final))})
            try:  # o original só sai depois do pronto gravado (se cair antes, outro refaz sem baixar do YouTube)
                rc("deletefile", f"{FILA_SRC}/{pid}/source.mp4")
            except RuntimeError:
                pass
        else:
            _marcar(pid, "erro.json", {"ok": False, "error": motivo, "segundos": seg, "por": QUEM,
                                       "log": log.read_text(encoding="utf-8", errors="ignore")[-4000:]})
        print(f"[{_agora()}] {pid}: {'OK' if not motivo else 'ERRO ' + motivo} ({seg} s)", flush=True)
    finally:
        pulso.parar.set()
        pulso.join(timeout=60)
        _Pulso.desde.pop(pid, None)
        _soltar(pid)
        shutil.rmtree(local, ignore_errors=True)


def _soltar_os_meus():
    """Sessão anterior deste trabalhador caiu no meio de um pedido: solta a marca (senão o pedido fica preso)."""
    for pid, arquivos in _fila().items():
        if f"em_andamento_{QUEM}.json" in arquivos:
            for marca in (f"em_andamento_{QUEM}.json", "em_andamento.json"):
                try:
                    if marca == "em_andamento.json" and json.loads(rc("cat", f"{FILA}/{pid}/{marca}")).get("por") != QUEM:
                        continue
                    rc("deletefile", f"{FILA}/{pid}/{marca}")
                except (RuntimeError, ValueError):
                    pass
            print(f"[{_agora()}] {pid}: marca velha minha solta (sessão anterior caiu)", flush=True)


def _md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def atualizar_se_mudou():
    """Trabalhador novo no Drive → troca e recomeça (só chamado com o trabalhador parado). Assim uma correção chega
    às 3 VPS e ao Kaggle sem ninguém subir à mão."""
    try:
        info = json.loads(rc("lsjson", "--hash", EU_REMOTO, tentativas=2) or "[]")
        md5 = ((info[0].get("Hashes") or {}).get("md5") if info else None)
    except (RuntimeError, ValueError, IndexError):
        return
    eu = Path(__file__).resolve()
    if not md5 or _md5(eu) == md5:
        return
    novo = BASE / "kaggle_trabalhador_novo.py"
    rc("copyto", EU_REMOTO, str(novo))
    if _md5(novo) != md5:
        return
    try:
        compile(novo.read_text(encoding="utf-8"), str(novo), "exec")
    except SyntaxError as e:
        print(f"[{_agora()}] trabalhador novo não compila ({e}) — sigo com o atual", flush=True)
        return
    alvo = novo
    if os.access(eu, os.W_OK) and str(eu).startswith(str(BASE.resolve())):  # VPS: troca o arquivo do contêiner
        shutil.copy(novo, eu)
        alvo = eu
    print(f"[{_agora()}] trabalhador novo ({md5[:8]}) — recomeçando com ele", flush=True)
    os.execv(sys.executable, [sys.executable, "-u", str(alvo)])


def loop():
    TRABALHO.mkdir(exist_ok=True)
    try:
        _soltar_os_meus()
    except RuntimeError as e:
        print(f"soltar marcas velhas falhou: {e}", flush=True)
    while time.time() - INICIO < LIMITE_S:
        try:
            _marcar(None, f"vivo_{QUEM}.json", {"em": _agora()}, destino=f"{VIVO_DIR}/vivo_{QUEM}.json")
            pid = proximo()
            if pid:
                fazer(pid)
                continue
            atualizar_se_mudou()
        except Exception as e:  # noqa: BLE001 — Drive fora do ar, cota, etc.: espera e tenta de novo, nunca sai
            print(f"[{_agora()}] rodada falhou: {type(e).__name__}: {str(e)[-300:]}", flush=True)
            time.sleep(120)
        time.sleep(ESPERA_VAZIA_S + random.uniform(0, 30))
    print("limite da sessão: saindo pro PC relançar", flush=True)


if __name__ == "__main__":
    preparar()
    loop()
