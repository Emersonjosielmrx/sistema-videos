"""Roda no KAGGLE (conta emersonjosiel649, kernel CPU com internet): mesmo trabalho do trabalhador.py da Colab, mas
lendo a fila pelo rclone (Kaggle não monta o Drive). Pega pedidos de manhwa-drive:colab_recap/fila até ~11 h de sessão.
O rclone.conf vem do dataset privado recap-worker-conf. Plano: producao/COLAB_RECAP_LONGO.md.
"""
import io
import json
import os
import shutil
import site
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

INICIO = time.time()
# Kaggle corta em 12 h e um longo leva horas: pedido novo só nas primeiras 6 h. Na VPS (Docker): TRAB_LIMITE_H=0 = sem fim
_LIM_H = float(os.environ.get("TRAB_LIMITE_H", "6"))
LIMITE_S = _LIM_H * 3600 if _LIM_H > 0 else float("inf")
BASE = Path(os.environ.get("TRAB_BASE", "/kaggle/working"))
QUEM = os.environ.get("TRAB_NOME", "kaggle")
CONF = Path(os.environ["RCLONE_CONF"]) if os.environ.get("RCLONE_CONF") else next(Path("/kaggle/input").rglob("rclone.conf"))
RC = BASE / "rclone"
FILA = "manhwa-drive:colab_recap/fila"
FILA_SRC = "manhwa-drive:colab_recap/fila_src"
os.environ["RCLONE_DRIVE_USE_TRASH"] = "false"
RAIZ = BASE / "raiz"
PRODUCAO = RAIZ / "D/recapd-ambientes/producao"
TRABALHO = BASE / "trabalho"
os.environ["RAIZ_WIN"] = str(RAIZ)


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rc(*args, saida=False):
    r = subprocess.run([str(RC), "--config", str(CONF), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"rclone {args[0]}: {r.stderr[-300:]}")
    return r.stdout


def preparar():
    # gravável (o rclone regrava o token) e FORA do /kaggle/working, que vira saída pública do kernel
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
    rc("copy", "manhwa-drive:colab_recap/raiz", str(RAIZ), "--transfers", "16", "--checkers", "32", "--fast-list")
    print(f"raiz copiada em {time.time() - t0:.0f} s", flush=True)
    sp = Path(site.getsitepackages()[0])
    rc("copyto", "manhwa-drive:colab_recap/sitecustomize.py", str(sp / "colab_traduz.py"))
    (sp / "colab_traduz.pth").write_text("import colab_traduz\n")
    (PRODUCAO / "workspace" / "anime").mkdir(parents=True, exist_ok=True)
    if not (PRODUCAO / "workspace" / "assets").exists():
        os.symlink(RAIZ / "D/hipercool-materiais/assets", PRODUCAO / "workspace" / "assets")
    (PRODUCAO / "venv" / "Scripts").mkdir(parents=True, exist_ok=True)
    py = PRODUCAO / "venv" / "Scripts" / "python.exe"
    if not py.exists():
        os.symlink(sys.executable, py)


def _marcar(pid, nome, dados, destino=None):
    tmp = BASE / nome
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    rc("copyto", str(tmp), destino or f"{FILA}/{pid}/{nome}")


def _livre(arquivos):
    return "pedido.json" in arquivos and not ({"pronto.json", "erro.json"} & arquivos
                                              or any(a.startswith("em_andamento") for a in arquivos))


def proximo():
    for pid in sorted(rc("lsf", FILA, "--dirs-only").split()):
        pid = pid.rstrip("/")
        if _livre(set(rc("lsf", f"{FILA}/{pid}").split())) and _pegar(pid):
            return pid
    return None


def _pegar(pid):
    """Marca o pedido e confere se ficou só pra mim. 25/10: Kaggle e VPS pegaram o MESMO pedido no mesmo segundo (os
    dois liam "livre" e gravavam em_andamento.json; o Drive aceita 2 arquivos com o mesmo nome) e renderizaram o mesmo
    vídeo 2x. Agora: marca própria em_andamento_<QUEM>.json + o em_andamento.json de sempre (os trabalhadores antigos só
    olham esse), espera, e se houver outra marca, fica quem marcou primeiro (empate: nome). Quem perde desiste."""
    eu = {"desde": _agora(), "por": QUEM}
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
    return True


def fazer(pid):
    local = TRABALHO / pid
    shutil.rmtree(local, ignore_errors=True)
    rc("copy", f"{FILA}/{pid}", str(local))
    if not (local / "source.mp4").exists():  # pedidos novos: original no manhwa-drive (Drive da 649 é pequeno)
        try:
            rc("copyto", f"{FILA_SRC}/{pid}/source.mp4", str(local / "source.mp4"))
        except RuntimeError as e:  # sem original: vira erro.json logo abaixo (antes derrubava o trabalhador)
            print(f"[{_agora()}] {pid}: original não baixou: {e}", flush=True)
    for parte in ("bin", "config", "secrets"):  # código novo do PC
        rc("copy", f"manhwa-drive:colab_recap/raiz/D/recapd-ambientes/producao/{parte}", str(PRODUCAO / parte))
    pedido = json.loads((local / "pedido.json").read_text(encoding="utf-8"))
    print(f"[{_agora()}] pedido {pid}: {pedido.get('titulo', '')[:60]}", flush=True)
    t0 = time.time()
    fonte = local / "source.mp4"
    if not fonte.exists() or fonte.stat().st_size < 1_000_000:  # 25/10: sem isto narrava 2 h um vídeo que não existia
        _marcar(pid, "erro.json", {"ok": False, "error": "original (source.mp4) não chegou", "segundos": 0, "por": QUEM})
        for marca in (f"em_andamento_{QUEM}.json", "em_andamento.json"):
            try:
                rc("deletefile", f"{FILA}/{pid}/{marca}")
            except RuntimeError:
                pass
        shutil.rmtree(local, ignore_errors=True)
        print(f"[{_agora()}] {pid}: ERRO sem original", flush=True)
        return
    log = local / "pipeline.log"
    cmd = [sys.executable, "-X", "utf8", str(PRODUCAO / "bin" / "anime-pipeline.py"),
           "--video-source", str(local / "source.mp4"), "--script", str(local / "roteiro.txt"),
           "--titulo", pedido["titulo"], "--formato", "deitado"]
    with open(log, "w", encoding="utf-8") as f:
        rcod = subprocess.run(cmd, cwd=PRODUCAO, stdout=f, stderr=subprocess.STDOUT,
                              env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
                                   "GEMINI_TTS_PROXY_ENABLED": "0"}).returncode
    seg = round(time.time() - t0)
    final = local / "final_anime_deitado.mp4"
    rc("copyto", str(log), f"{FILA}/{pid}/pipeline.log")
    if rcod == 0 and final.exists():
        rc("copyto", str(final), f"{FILA_SRC}/{pid}/final_anime_deitado.mp4")
        for lugar in (FILA, FILA_SRC):
            try:
                rc("deletefile", f"{lugar}/{pid}/source.mp4")
            except RuntimeError:
                pass
        _marcar(pid, "pronto.json", {"fim": _agora(), "segundos": seg, "por": QUEM})
    else:
        _marcar(pid, "erro.json", {"ok": False, "error": f"rc={rcod}" if rcod else "sem final", "segundos": seg,
                                   "log": log.read_text(encoding="utf-8", errors="ignore")[-4000:], "por": QUEM})
    for marca in (f"em_andamento_{QUEM}.json", "em_andamento.json"):
        try:
            rc("deletefile", f"{FILA}/{pid}/{marca}")
        except RuntimeError:
            pass
    shutil.rmtree(local, ignore_errors=True)
    print(f"[{_agora()}] {pid}: {'OK' if rcod == 0 and final.exists() else 'ERRO'} ({seg} s)", flush=True)


def _soltar_os_meus():
    """Sessão anterior deste trabalhador caiu no meio de um pedido: solta a marca (senão o pedido fica preso)."""
    for pid in rc("lsf", FILA, "--dirs-only").split():
        pid = pid.rstrip("/")
        if f"em_andamento_{QUEM}.json" in rc("lsf", f"{FILA}/{pid}").split():
            for marca in (f"em_andamento_{QUEM}.json", "em_andamento.json"):
                try:
                    if marca == "em_andamento.json" and json.loads(rc("cat", f"{FILA}/{pid}/{marca}")).get("por") != QUEM:
                        continue
                    rc("deletefile", f"{FILA}/{pid}/{marca}")
                except (RuntimeError, ValueError):
                    pass
            print(f"[{_agora()}] {pid}: marca velha minha solta (sessão anterior caiu)", flush=True)


def loop():
    TRABALHO.mkdir(exist_ok=True)
    try:
        _soltar_os_meus()
    except RuntimeError as e:
        print(f"soltar marcas velhas falhou: {e}", flush=True)
    while time.time() - INICIO < LIMITE_S:
        _marcar(None, f"vivo_{QUEM}.json", {"em": _agora()}, destino=f"manhwa-drive:colab_recap/vivo_{QUEM}.json")
        pid = proximo()
        if pid:
            fazer(pid)
        else:
            time.sleep(60)
    print("limite da sessão: saindo pro PC relançar", flush=True)


if __name__ == "__main__":
    preparar()
    loop()
