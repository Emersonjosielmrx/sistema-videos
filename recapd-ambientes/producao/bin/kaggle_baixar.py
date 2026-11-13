"""kaggle_baixar.py — o PC1 pede ao BAIXADOR do Kaggle (colab\\kaggle_baixador.py) o vídeo + legenda e traz pelo Drive
(30/10/2026, D43). Uso quando o IP de casa está barrado pelo YouTube (ytdlp_vez.pausado()): o Kaggle tem outro IP.

    python kaggle_baixar.py lancar            # sobe/relança o kernel emersonjosiel/baixador-yt (CPU + internet)
    python kaggle_baixar.py status            # estado do kernel + vivo.json
    python kaggle_baixar.py manter            # relança se não estiver rodando (tarefa KaggleBaixador, 20 min)
    python kaggle_baixar.py teste <url>       # baixa 1 vídeo pelo Kaggle numa pasta temporária e mostra

Biblioteca: from kaggle_baixar import vivo, baixar
    video, legendas = baixar(url, vid, pasta)  # video = Path de source.mp4 ou None
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

RCLONE = r"D:\tools\rclone.exe"
RAIZ = "manhwa-drive:baixador"
KERNEL = "emersonjosiel/baixador-yt"
COLAB = Path(r"D:\recapd-ambientes\producao\colab")
SEM_JANELA = 0x08000000


def _rc(*args, timeout=180):
    try:
        r = subprocess.run([RCLONE, *args], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL,
                           creationflags=SEM_JANELA, env={**__import__("os").environ, "RCLONE_DRIVE_USE_TRASH": "false"})
    except subprocess.TimeoutExpired:  # Drive lento (30/10 11:27: lsf > 60 s): quem chama trata como "ainda não"
        raise RuntimeError(f"rclone {args[0]}: passou de {timeout} s")
    if r.returncode != 0:
        raise RuntimeError(f"rclone {args[0]}: {r.stderr[-200:]}")
    return r.stdout


def vivo(max_min=3):
    """O baixador do Kaggle respondeu nos últimos `max_min` minutos?"""
    try:
        d = json.loads(_rc("cat", f"{RAIZ}/vivo.json", timeout=60))
        em = datetime.fromisoformat(d["em"])
        return (datetime.now(timezone.utc) - em).total_seconds() < max_min * 60
    except Exception:  # noqa: BLE001
        return False


def baixar(url, vid, pasta, max_height=720, legendas=("pt", "es"), timeout=900, log=print):
    """Pede, espera e traz para `pasta`. (Path do vídeo ou None, [legendas]). Erro do Kaggle = (None, [])."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="kbaixar_"))
    try:
        (tmp / f"{vid}.json").write_text(json.dumps({"id": vid, "url": url, "max_height": max_height,
                                                      "legendas": list(legendas)}), encoding="utf-8")
        _rc("purge", f"{RAIZ}/prontos/{vid}", timeout=60) if _existe(f"{RAIZ}/prontos/{vid}") else None
        _rc("copyto", str(tmp / f"{vid}.json"), f"{RAIZ}/pedidos/{vid}.json")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(15)
        try:
            nomes = set(_rc("lsf", f"{RAIZ}/prontos/{vid}", timeout=60).split())
        except RuntimeError:
            continue
        if "erro.json" in nomes:
            erro = json.loads(_rc("cat", f"{RAIZ}/prontos/{vid}/erro.json", timeout=60)).get("erro", "?")
            _rc("purge", f"{RAIZ}/prontos/{vid}", timeout=60)
            log(f"[kaggle] {vid}: erro lá ({erro[:150]})")
            return None, []
        if "ok.json" in nomes:
            _rc("copy", f"{RAIZ}/prontos/{vid}", str(pasta), "--exclude", "ok.json", timeout=900)
            info = json.loads(_rc("cat", f"{RAIZ}/prontos/{vid}/ok.json", timeout=60))
            _rc("purge", f"{RAIZ}/prontos/{vid}", timeout=60)
            video = pasta / info["video"] if info.get("video") else None
            legs = [pasta / n for n in info.get("legendas", [])]
            log(f"[kaggle] {vid}: {info.get('mb')} MB em {info.get('s')} s lá + {round(time.time() - t0)} s total "
                f"(IP {info.get('ip')}), legendas {info.get('legendas')}")
            return (video if video and video.exists() else None), [l for l in legs if l.exists()]
    log(f"[kaggle] {vid}: não voltou em {timeout} s — pedido retirado")
    try:
        _rc("deletefile", f"{RAIZ}/pedidos/{vid}.json", timeout=60)
    except RuntimeError:
        pass
    return None, []


def _existe(caminho):
    try:
        return bool(_rc("lsf", caminho, timeout=60).strip())
    except RuntimeError:
        return False


# ── lançar/manter o kernel (mesma conta/chave do colab\kaggle_lancar.py) ──
def _kg(*args):
    # 30/10 (dona: "não misture o lugar de saída"): a conta emersonjosiel649 é da hermes-prod (kaggle_pool.json) — o
    # PC1 (IP de casa) não fala com o Kaggle por ela. Quem mantém o baixador é a hermes-prod
    # (/opt/recap_central/baixador/baixador_manter.sh, cron 20 min); a tarefa KaggleBaixador do PC1 foi desligada.
    if sys.platform == "win32":
        raise SystemExit("kaggle_baixar: lançar/status do baixador só pela hermes-prod (saída da conta 649) — "
                         "ssh hermes-prod /opt/recap_central/baixador/baixador_manter.sh")
    sys.path.insert(0, str(COLAB))
    import kaggle_lancar as kl
    return subprocess.run([str(kl.KAGGLE), *args], env=kl._env(), capture_output=True, text=True,
                          creationflags=SEM_JANELA, stdin=subprocess.DEVNULL)


def lancar():
    sys.path.insert(0, str(COLAB))
    import kaggle_lancar as kl
    d = kl.TMP / "baixador"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    shutil.copy(COLAB / "kaggle_baixador.py", d / "kaggle_baixador.py")
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": KERNEL, "title": "baixador-yt", "code_file": "kaggle_baixador.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_internet": True,
         "dataset_sources": [kl.DATASET], "competition_sources": [], "kernel_sources": []}), encoding="utf-8")
    r = _kg("kernels", "push", "-p", str(d))
    return (r.stdout + r.stderr).strip()[-300:]


def status():
    r = _kg("kernels", "status", KERNEL)
    return (r.stdout + r.stderr).strip().lower()


def manter():
    st = status()
    if "running" in st or "queued" in st:
        return f"rodando ({st[-60:]})"
    return "relançado: " + lancar()


def main(a):
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = a[0] if a else "status"
    if cmd == "lancar":
        print(lancar())
    elif cmd == "manter":
        print(manter())
    elif cmd == "status":
        print(status(), "| vivo:", vivo())
    elif cmd == "teste" and len(a) > 1:
        d = Path(tempfile.mkdtemp(prefix="kteste_"))
        v, legs = baixar(a[1], "teste_" + str(int(time.time())), d)
        print("video:", v, v.stat().st_size if v else "", "| legendas:", [l.name for l in legs])
        shutil.rmtree(d, ignore_errors=True)
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
