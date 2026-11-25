r"""despacho.py — FILA INVISÍVEL ÚNICA: manda cada trabalho pesado pra máquina certa da rede (dona 24/11: "deve haver
uma fila invisível que distribui pros PCs considerando as contas que eles têm logadas"; "tudo que consumir CPU e der
pra mandar pra outro PC deve ser feito no outro; o PC1 é pro VS Code").

Junta o que já existia separado:
  - celulares.py        : vez por máquina (estado\celulares\<host>.json) + medida (CPU/RAM/disco) + ffmpeg remoto
  - maquina_remota.py   : em que máquina cada conta está logada (postador-de-videos\config\netbooks_logins.json)
  - CAPAZ (abaixo)      : o que cada máquina sabe fazer (ffmpeg, remotion, python...)
A vez é a MESMA do celulares.py: as duas filas nunca mandam 2 trabalhos pra mesma máquina.

Regras de escolha (escolher):
  1. só máquina CAPAZ do tipo;
  2. trabalho de CONTA (conta=perfil): só máquina onde a conta está logada (netbooks_logins) — senão PC1 (onde todas
     estão). NUNCA leva conta pra máquina onde ela não está: regra de IP fixo (Kaggle/Google) continua valendo;
  3. livre agora (vez + medida de no máx. 2 min);
  4. mais rápida primeiro; PC1 só se nenhuma der (devolve None: quem chamou roda aqui, em prioridade baixa).

Uso em código:
    import despacho
    with despacho.maquina("remotion", rotulo="solar X") as host:   # None = nenhuma livre -> rode no PC1
        ...
    despacho.remotion(pasta_remotion, id_video, pasta_public, saida_mp4, args)   # render Remotion inteiro lá
Linha de comando:
    python despacho.py estado                 # quem pode o quê, livre/ocupado, contas logadas por máquina
    python despacho.py escolher remotion      # quem pegaria agora (não pega a vez)
    python despacho.py onde <perfil>          # máquinas onde a conta está logada
Desligar: DESPACHO=0 (tudo volta pro PC1 como antes).
"""
import contextlib
import json
import os
import shlex
import subprocess
import sys
import tarfile
import threading
import time
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import celulares  # noqa: E402 — vez, medida e ssh já testados

LOGINS = Path(r"D:\postador-de-videos\config\netbooks_logins.json")
LOG = BASE / "logs" / "despacho.log"

# O que cada máquina sabe fazer (medido/instalado). Ordem = preferência (mais rápida primeiro).
# remotion: node + chromium + ~/claude-code-video/remotion com npm ci.
# 24/11 dona: "todos devem ser capazes, tirando o acer x200ma e o asus-eepc que são fracos".
# sti e hp: ffmpeg em ~/bin (estático), sem node/chromium (Remotion não roda lá por enquanto).
# pc2 e desktop: Windows, ffmpeg em D:\hipercool-materiais\bin, node instalado.
# celulares (s20, s20ultra, g20): só ffmpeg do Termux (Remotion não roda).
CAPAZ = {
    "asusx": {"ffmpeg", "remotion", "python"},   # Omarchy, i5-4200U, 11 GB — Remotion instalado 24/11
    "itau": {"ffmpeg", "remotion", "python"},     # Omarchy, i5-2520M, 11 GB — Remotion instalado 24/11
    "sti": {"ffmpeg", "python"},                  # Mint, i5, 16 GB — ffmpeg ~/bin, sem node
    "desktop": {"ffmpeg", "python"},              # Windows, i7, node — Remotion possível depois
    "pc2": {"ffmpeg", "python"},                  # Windows, render do hipercool — Remotion possível depois
    "hp": {"ffmpeg", "python"},                   # Mint, AMD Turion, 8 GB — lento, sem node
    "s20ultra": {"ffmpeg"},
    "s20": {"ffmpeg"},
    "g20": {"ffmpeg"},
}
REMOTION_DIR = "claude-code-video/remotion"   # relativo ao ~ da máquina


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%d/%m %H:%M:%S')} {msg}\n")


def ligado():
    return os.environ.get("DESPACHO", "1") != "0"


# ─── contas ──────────────────────────────────────────────────────────────────
def _logins():
    for _ in range(10):  # outro processo pode estar no meio do os.replace: tenta de novo
        try:
            return json.loads(LOGINS.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            time.sleep(0.3)
    return {}


def onde(perfil, servico="google"):
    """Máquinas (fora o PC1) onde a conta está logada no serviço (google/youtube/tiktok/instagram)."""
    p = (perfil or "").split("@")[0].lower()
    reg = _logins().get(p) or {}
    return [m for m, s in reg.items() if isinstance(s, dict) and s.get(servico)]


# ─── escolha ─────────────────────────────────────────────────────────────────
def candidatas(tipo, conta=None, servico="google"):
    hosts = [h for h, c in CAPAZ.items() if tipo in c and h in celulares.HOSTS]
    if conta:
        logada = set(onde(conta, servico))
        hosts = [h for h in hosts if h in logada]
    return hosts


def escolher(tipo, rotulo="", conta=None, servico="google", pegar=True):
    """Máquina livre para o trabalho (pega a vez se pegar=True). None = nenhuma: rode no PC1."""
    if not ligado():
        return None
    for h in candidatas(tipo, conta, servico):
        if pegar and not celulares._pegar(h, f"{tipo}: {rotulo}"):
            continue
        if not pegar and celulares._dono_lock(h):
            continue
        m = celulares.medir(h, vale_s=celulares.MEDIDA_VALE_S)
        if m.get("ocioso"):
            return h
        if pegar:
            celulares._soltar(h)
    return None


@contextlib.contextmanager
def maquina(tipo, rotulo="", conta=None, servico="google"):
    h = escolher(tipo, rotulo, conta, servico)
    log(f"[{tipo}] {rotulo[:60]} -> {h or 'PC1 (nenhuma livre)'}")
    try:
        yield h
    finally:
        if h:
            celulares._soltar(h)


# ─── trabalhos prontos ───────────────────────────────────────────────────────
def _ssh(h, cmd, timeout=60, entrada=None, stdout=None):
    return celulares._ssh(h, cmd, timeout=timeout, entrada=entrada, stdout=stdout)


def remotion(raiz, vid, public, saida, args=(), timeout=1800, rotulo=""):
    """Render Remotion numa máquina livre. raiz = pasta remotion do PC1; vid = id em src/videos; public = pasta de
    insumos; saida = mp4 aqui. Leva src/lib + src/videos/<vid> + public (tar pelo ssh), roda lá, traz o mp4.
    -> (True, "") | (False, motivo). False = quem chamou renderiza no PC1 como antes."""
    raiz, public, saida = Path(raiz), Path(public), Path(saida)
    with maquina("remotion", rotulo or vid) as h:
        if not h:
            return False, "nenhuma máquina livre"
        job = f"job_{time.strftime('%m%d_%H%M%S')}_{uuid.uuid4().hex[:5]}"
        ini = time.time()
        rem = f"~/{REMOTION_DIR}"
        extra = " ".join(shlex.quote(a) for a in args if not str(a).startswith("--public-dir"))
        remoto = (f"export PATH=$HOME/.local/share/mise/shims:$PATH; cd {rem} && mkdir -p jobs/{job} && "
                  f"tar -xf - -C jobs/{job} && rm -rf src/lib src/videos/{shlex.quote(vid)} && "
                  f"cp -r jobs/{job}/src/lib src/lib && mkdir -p src/videos && "
                  f"cp -r jobs/{job}/src/videos/{shlex.quote(vid)} src/videos/ && "
                  f"nice -n 5 npx remotion render src/videos/{shlex.quote(vid)}/index.ts Main jobs/{job}/out.mp4 "
                  f"--public-dir=jobs/{job}/public --browser-executable=/usr/bin/chromium {extra} "
                  f"> jobs/{job}/render.log 2>&1; rc=$?; tail -c 1500 jobs/{job}/render.log >&2; exit $rc")
        p = subprocess.Popen([celulares.SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o",
                              "ServerAliveInterval=15", "-o", "ServerAliveCountMax=8", celulares._rota(h), remoto],
                             stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                             creationflags=celulares._SEM_JANELA)
        erro_tar = []

        def _mandar():
            try:
                with tarfile.open(fileobj=p.stdin, mode="w|") as t:
                    t.add(str(raiz / "src" / "lib"), arcname="src/lib")
                    t.add(str(raiz / "src" / "videos" / vid), arcname=f"src/videos/{vid}")
                    if public.exists():
                        t.add(str(public), arcname="public")
            except Exception as ex:  # noqa: BLE001
                erro_tar.append(ex)
            finally:
                try:
                    p.stdin.close()
                except OSError:
                    pass
        th = threading.Thread(target=_mandar, daemon=True)
        th.start()
        try:
            try:
                p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                p.kill()
                _ssh(h, "pkill -f 'remotion render' ; pkill -f chromium.*remotion", timeout=30)
                return False, f"{h}: passou de {timeout // 60} min"
            err = p.stderr.read().decode("utf-8", "replace")
            th.join(30)
            if erro_tar or p.returncode != 0:
                log(f"[remotion] {vid} em {h}: FALHOU rc {p.returncode} {erro_tar[:1]} {err[-300:]}")
                return False, f"{h}: rc {p.returncode} {err[-800:]}"
            parcial = saida.with_name(saida.name + ".despacho.part")
            with open(parcial, "wb") as f:
                r = _ssh(h, f"cat {rem}/jobs/{job}/out.mp4", timeout=600, stdout=f)
            if r.returncode != 0 or parcial.stat().st_size < 10000:
                parcial.unlink(missing_ok=True)
                return False, f"{h}: o mp4 não veio (rc {r.returncode})"
            os.replace(parcial, saida)
            log(f"[remotion] {vid} em {h}: ok em {time.time() - ini:.0f} s ({saida.stat().st_size / 1048576:.1f} MB)")
            return True, ""
        finally:
            _ssh(h, f"rm -rf {rem}/jobs/{job}", timeout=60)


# ─── linha de comando ────────────────────────────────────────────────────────
def estado():
    for h, cap in CAPAZ.items():
        if h not in celulares.HOSTS:
            continue
        m = celulares.medir(h, vale_s=celulares.MEDIDA_VALE_S)
        print(f"{h:9} {'LIVRE ' if m.get('ocioso') else 'ocupada'} [{','.join(sorted(cap))}] {m.get('motivo', '')[:90]}")
    reg = _logins()
    por = {}
    for p, ms in reg.items():
        if isinstance(ms, dict):
            for mq, s in ms.items():
                if isinstance(s, dict) and s.get("google"):
                    por.setdefault(mq, []).append(p)
    print("contas logadas (Google) por máquina, fora o PC1:")
    for mq, ps in sorted(por.items()):
        print(f"  {mq:9} {len(ps):3}  {', '.join(sorted(ps)[:6])}{' ...' if len(ps) > 6 else ''}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["estado"]
    if a[0] == "estado":
        estado()
    elif a[0] == "escolher":
        print(escolher(a[1], "teste", pegar=False) or "PC1 (nenhuma livre)")
    elif a[0] == "onde":
        print(", ".join(onde(a[1])) or "só no PC1")
    else:
        print(__doc__)
