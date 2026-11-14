# -*- coding: utf-8 -*-
"""celulares.py — os Galaxy S20 (Termux + Tailscale) como workers de FFmpeg (dona 04/11/2026: "adicionar um S20 ao nosso
sistema ... pra renderizar vídeos"; "adicionei mais um"; "põe pra rodar, documente"). Doc: D:\\video-fila\\CELULARES.md

O celular não tem o pipeline (Python do Cortes, voz clonada, Gemini...): ele recebe UM comando FFmpeg pronto, com as
entradas, e devolve o arquivo de saída. Quem chama monta o comando como sempre e troca o subprocess.run por:

    if not (celulares and celulares.rodar_ffmpeg(cmd, timeout=900, rotulo="xfade")):
        subprocess.run(cmd, check=True, capture_output=True, timeout=900)    # local, como antes

rodar_ffmpeg devolve True só se o arquivo de saída chegou inteiro aqui. Qualquer coisa fora do normal (celular fora do ar,
fora da tomada com bateria baixa, quente, ocupado, comando com caminho escondido no filtro, erro do ffmpeg, queda da
rede) = False, e o render segue no PC como sempre. O celular nunca pode atrasar a produção mais que uma tentativa.

Por conexão: 1 ssh leva as entradas (tar pelo stdin) e roda o ffmpeg; 1 ssh traz a saída e apaga a pasta de lá.

    python celulares.py                 # mede os celulares (CPU, RAM, disco, bateria, temperatura, vaga)
    python celulares.py testar [host]   # render de prova (xfade de 3 clipes 1080x1920) no celular x no PC1
    python celulares.py limpar          # apaga ~/render dos celulares (sobras de job que caiu)
Desligar: controle.py desligar celulares producao  (ou env CELULARES=0 no processo)
"""
import json
import os
import shlex
import subprocess
import sys
import tarfile
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
EST = BASE / "estado"
LOCKS = EST / "celulares"
MEDIDAS = EST / "celulares_medida.json"
STATS = EST / "celulares_stats.json"
LOG = BASE / "logs" / "celulares.log"
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# ssh do Git: o do Windows (System32\OpenSSH) trava depois de autenticar e corta o fim de tar grande (maquinas.py 17/10,
# hipercool pc2.py 22/10)
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe" if Path(r"C:\Program Files\Git\usr\bin\ssh.exe").exists() else "ssh"

# Ordem = preferência (o Ultra tem 14 GB e encoda 1080x1920 ~30% mais rápido). Alias em C:\Users\Haylla\.ssh\config.
HOSTS = {
    # 11/11 dona ("notebook STI is1442 ligado ao sistema, já pode usar pra processar"): i5 4 núcleos, 16 GB, Mint,
    # ffmpeg 7.0.2 estático em ~/bin. Vem 1º: é bem mais rápido que os celulares. Sem bateria de Termux (fica vazia).
    "sti": {"nome": "Notebook STI", "modelo": "is1442", "ip": "100.98.49.0", "notebook": True},
    "s20ultra": {"nome": "S20 Ultra", "modelo": "SM-G988B", "ip": "100.103.218.7"},
    "s20": {"nome": "S20", "modelo": "SM-G980F", "ip": "100.117.134.73"},
    # 13/11 dona ("adicione no sistema o HP Pavilion"): AMD Turion II N530 (2010, 2 núcleos), 8 GB, Mint 22.3, ffmpeg
    # 7.0.2 estático em ~/bin (copiado do STI). Medido: 8 s 1080x1920 veryfast em 9 s — mais lento que o STI e os S20,
    # fica depois deles. Na tomada (bateria morta: 0%).
    "hp": {"nome": "Notebook HP", "modelo": "pavilion dv6", "ip": "100.123.69.41", "notebook": True, "lento": True},
    # 12/11 dona ("A2, A3 e Moto G20 ligados"): Moto G20 (8 núcleos, 3,5 GB, ffmpeg do Termux). A2/A3 entram quando o
    # sshd do Termux deles responder (instalar_vigia.py instala o vigia sozinho).
    "g20": {"nome": "Moto G20", "modelo": "moto g(20)", "ip": "100.75.139.24", "ram_min": 1.0},
    # 12/11: Redmi A3 testado — xfade 8 s 1080x1920 passou de 200 s (G20 = 23 s): lento demais pro render; só o vigia
}
# Regras de vaga. 04/11 (dona: "vão trabalhar acima da temperatura, o local é quente; não tem problema se der pau, são
# velhos e descartáveis, só servem pra isso"): SEM limite de temperatura — só aparece no painel. None = desligado.
TEMP_MAX = None          # °C da bateria (termux-battery-status)
# Bateria fora da tomada não é proteção do celular: é pra não apagar no meio do render (aí o trecho volta pro PC)
BATERIA_MIN_FORA = 20    # % mínimo fora da tomada (na tomada qualquer carga serve)
RAM_MIN_GB = 1.5
DISCO_MIN_GB = 5
ENTRADA_MAX_MB = 3000    # entradas maiores que isso não compensam subir pela rede
MEDIDA_VALE_S = 120      # medida guardada vale 2 min (não abrir ssh a cada segmento)
LOCK_MAX_H = 4
REMOTO = "render"        # ~/render/<job> no Termux

MEDIR_PY = r"""
import json, os, shutil, subprocess
def sh(c, t=20):
    try:
        return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t).stdout
    except Exception:
        return ""
cpu = None
for l in sh("top -b -n 2 -d 1 2>/dev/null").splitlines():
    if "%cpu" in l and "%idle" in l:   # 2a amostra fica por último: '800%cpu 12%user ... 760%idle ...'
        p = {x.split("%")[1]: float(x.split("%")[0]) for x in l.split() if "%" in x and x.split("%")[0].replace(".", "").isdigit()}
        if p.get("cpu"):
            cpu = round(100 * (1 - p.get("idle", 0) / p["cpu"]))
mem = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo") if len(l.split()) > 1}
try:
    b = json.loads(sh("termux-battery-status", 15) or "{}")
except ValueError:
    b = {}
print(json.dumps({"cpu": cpu, "ram_gb": round(mem.get("MemAvailable", 0) / 1048576, 1),
                  "disco_gb": round(shutil.disk_usage(os.path.expanduser("~")).free / 1073741824, 1),
                  "bateria": b.get("percentage"), "tomada": b.get("plugged"), "temp": b.get("temperature"),
                  "ffmpeg": len([x for x in sh("pgrep -x ffmpeg").split() if x.strip()])}))
"""


def log(msg):
    LOG.parent.mkdir(exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    try:
        print(linha, flush=True)
    except Exception:  # noqa: BLE001 — pythonw sem stdout
        pass
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _ssh(host, comando, timeout=60, entrada=None, stdout=None):
    return subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15",
                           "-o", "ServerAliveCountMax=4", host, comando], input=entrada, timeout=timeout,
                          stdout=stdout if stdout is not None else subprocess.PIPE, stderr=subprocess.PIPE,
                          creationflags=_SEM_JANELA)


def _ligado():
    if os.environ.get("CELULARES") == "0":
        return False, "CELULARES=0 neste processo"
    try:
        # pelo caminho do arquivo: este módulo roda DENTRO do pipeline do Cortes (fx_clips) e D:\video-fila na frente do
        # sys.path trocaria módulos de mesmo nome do projeto (regra: pasta de outro projeto nunca na frente)
        import importlib.util
        spec = importlib.util.spec_from_file_location("controle_videofila", str(BASE / "controle.py"))
        controle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(controle)
        return controle.ligado("celulares", "producao")
    except Exception:  # noqa: BLE001 — defeito do controle não para nada
        return True, ""


# ─── medida ──────────────────────────────────────────────────────────────────
def _guardadas():
    try:
        return json.loads(MEDIDAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _guardar(host, m):
    d = _guardadas()
    d[host] = m
    MEDIDAS.parent.mkdir(parents=True, exist_ok=True)
    tmp = MEDIDAS.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(MEDIDAS)


def medir(host, vale_s=0):
    """Mesmo formato do maquinas.medir: {"host", "ocioso", "motivo", cpu, ram_gb, disco_gb, bateria, tomada, temp,
    renders, vez}. vale_s > 0 = aceita a medida guardada se tiver menos que isso."""
    if vale_s:
        g = _guardadas().get(host)
        if g and time.time() - g.get("em", 0) < vale_s:
            return {**g, "ocioso": g.get("ocioso") and not _dono_lock(host), "vez": _trabalho(host) or g.get("vez")}
    m = {"host": host, "celular": True, "nome": HOSTS[host]["nome"], "em": time.time()}
    try:
        r = _ssh(host, "python3 -", timeout=45, entrada=MEDIR_PY.encode())
        m.update(json.loads((r.stdout or b"").decode("utf-8", "replace").strip().splitlines()[-1]))
    except Exception as e:  # noqa: BLE001
        m.update(ocioso=False, motivo=f"não respondeu ({type(e).__name__}) — Termux fechado, sem Tailscale ou sem rede")
        _guardar(host, m)
        return m
    m["renders"] = m.pop("ffmpeg", 0)
    trab = _trabalho(host) if _dono_lock(host) else ""  # a vez pega por ESTE processo (em _escolher) não é ocupado
    m["vez"] = trab
    na_tomada = (m.get("tomada") or "UNPLUGGED") != "UNPLUGGED" or HOSTS[host].get("notebook")
    bat = f"bateria {m.get('bateria')}%{' na tomada' if na_tomada else ' FORA da tomada'}, {m.get('temp')} °C"
    lig, motivo_off = _ligado()
    if not lig:
        m.update(ocioso=False, motivo=f"desligado: {motivo_off} | {bat}")
    elif trab or m["renders"]:
        m.update(ocioso=False, motivo=f"renderizando ({trab or str(m['renders']) + ' ffmpeg'}) | {bat}")
    elif TEMP_MAX and (m.get("temp") or 0) > TEMP_MAX:
        m.update(ocioso=False, motivo=f"quente: {m['temp']} °C (máx {TEMP_MAX}) | {bat}")
    elif not na_tomada and (m.get("bateria") or 0) < BATERIA_MIN_FORA:
        m.update(ocioso=False, motivo=f"fora da tomada com {m.get('bateria')}% (mín {BATERIA_MIN_FORA}%) | {bat}")
    elif (m.get("ram_gb") or 0) < HOSTS[host].get("ram_min", RAM_MIN_GB):  # 12/11: G20 (3,5 GB) usa 1 GB de mínimo
        m.update(ocioso=False, motivo=f"RAM {m.get('ram_gb')} GB (mín {HOSTS[host].get('ram_min', RAM_MIN_GB)}) | {bat}")
    elif (m.get("disco_gb") or 0) < DISCO_MIN_GB:
        m.update(ocioso=False, motivo=f"disco {m.get('disco_gb')} GB (mín {DISCO_MIN_GB}) | {bat}")
    else:
        m.update(ocioso=True, motivo=f"livre pra FFmpeg | {bat}")
    st = _stats().get(_hoje(), {}).get(host)
    if st:
        m["motivo"] += f" | hoje {st['ok']} render(s), {st['falhas']} falha(s), {round(st['seg'] / 60)} min"
    _guardar(host, m)
    return m


def medir_todos(vale_s=0):
    return {h: medir(h, vale_s) for h in HOSTS}


# ─── vez (1 render por celular) ──────────────────────────────────────────────
def _vivo(pid):
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", creationflags=_SEM_JANELA, timeout=30)
        return str(pid) in (r.stdout or "")
    except Exception:  # noqa: BLE001
        return True


def _ler_lock(host):
    f = LOCKS / f"{host}.json"
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if time.time() - d.get("desde", 0) > LOCK_MAX_H * 3600 or not _vivo(d.get("pid", 0)):
        f.unlink(missing_ok=True)  # dono morreu ou esquecido: libera
        return None
    return d


def _dono_lock(host):
    d = _ler_lock(host)
    return bool(d) and d.get("pid") != os.getpid()


def _trabalho(host):
    d = _ler_lock(host)
    if not d:
        return ""
    return f"{d.get('rotulo') or 'ffmpeg'} há {round((time.time() - d['desde']) / 60)} min"


def _pegar(host, rotulo):
    LOCKS.mkdir(parents=True, exist_ok=True)
    _ler_lock(host)  # limpa lock morto
    try:
        fd = os.open(str(LOCKS / f"{host}.json"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"pid": os.getpid(), "desde": time.time(), "rotulo": rotulo[:80]}, f)
    return True


def _soltar(host):
    d = _ler_lock(host)
    if d and d.get("pid") == os.getpid():
        (LOCKS / f"{host}.json").unlink(missing_ok=True)


# ─── estatística (painel) ────────────────────────────────────────────────────
def _hoje():
    return datetime.now().strftime("%Y-%m-%d")


def _stats():
    try:
        return json.loads(STATS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _contar(host, ok, seg):
    d = _stats()
    d = {k: v for k, v in d.items() if k >= (datetime.now().fromtimestamp(time.time() - 14 * 86400)).strftime("%Y-%m-%d")}
    h = d.setdefault(_hoje(), {}).setdefault(host, {"ok": 0, "falhas": 0, "seg": 0})
    h["ok" if ok else "falhas"] += 1
    h["seg"] += round(seg)
    tmp = STATS.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATS)


# ─── o render ────────────────────────────────────────────────────────────────
_SUSPEITOS = ("movie=", "amovie=", "subtitles=", "ass=", "fontfile=", "textfile=", "lut3d=", "haldclut", "sendcmd",
              "file=")


def _preparar(cmd):
    """(entradas, saida, args_remotos, nome_saida, mb) ou ValueError com o motivo de não mandar pro celular."""
    if not cmd or not Path(str(cmd[0])).name.lower().startswith("ffmpeg"):
        raise ValueError("não é ffmpeg")
    cmd = [str(c) for c in cmd]
    saida = Path(cmd[-1])
    if not saida.parent.is_dir():
        raise ValueError("pasta da saída não existe")
    entradas, args, i = [], [], 1
    while i < len(cmd) - 1:
        a = cmd[i]
        if a == "-i" and i + 1 < len(cmd) - 1:
            p = Path(cmd[i + 1])
            if not p.is_file():
                raise ValueError(f"entrada não é arquivo local: {cmd[i + 1][:80]}")
            if p in entradas:
                nome = f"in{entradas.index(p)}{p.suffix}"
            else:
                nome = f"in{len(entradas)}{p.suffix}"
                entradas.append(p)
            args += ["-i", nome]
            i += 2
            continue
        if a in ("-f",) and i + 1 < len(cmd) - 1 and cmd[i + 1] in ("concat", "lavfi"):
            raise ValueError(f"-f {cmd[i + 1]} lê arquivos por dentro")
        baixo = a.lower()
        if any(s in baixo for s in _SUSPEITOS) or (":\\" in a or ":/" in a) or (len(a) > 3 and Path(a).exists()):
            raise ValueError(f"argumento aponta pra arquivo daqui: {a[:80]}")
        args.append(a)
        i += 1
    if not entradas:
        raise ValueError("sem entradas")
    if saida in entradas:
        raise ValueError("saída = entrada")
    mb = sum(p.stat().st_size for p in entradas) / 1048576
    if mb > ENTRADA_MAX_MB:
        raise ValueError(f"entradas com {mb:.0f} MB (máx {ENTRADA_MAX_MB})")
    nome_saida = "out" + (saida.suffix or ".mp4")
    return entradas, saida, ["ffmpeg", "-nostdin", *[a for a in args if a != "-nostdin"], nome_saida], nome_saida, mb


def _escolher(rotulo):
    """Primeiro celular livre (vez pega ANTES de medir: 2 renders do PC1 não escolhem o mesmo). None = nenhum."""
    # 12/11 dona ("põe render nos celulares, uso de todos os dispositivos ao máximo"): a ordem fixa dava TUDO ao STI
    # (12 renders hoje) e 0 aos S20/G20. Agora vai primeiro quem fez MENOS hoje (empate = ordem de HOSTS); quem falhou
    # hoje vai pro fim. Falhou/ocupado = próximo; nenhum = PC, como antes. CELULARES_RODIZIO=0 volta a ordem fixa.
    ordem = list(HOSTS)
    if os.environ.get("CELULARES_RODIZIO", "1") != "0":
        hoje = _stats().get(_hoje(), {})
        # 13/11 22:55 (dona: "veja a forma mais eficiente de usar o HP"): "quem fez menos hoje vai primeiro" punha o
        # aparelho recém-chegado na frente — e o HP é o mais lento da casa. Mesma prova (xfade 1080x1920): PC1 31 s,
        # S20 Ultra 36 s, S20 42 s, STI 71 s, HP 267 s. Um trecho que caísse nele segurava o Short inteiro 4 min.
        # Agora "lento": True (HOSTS) vai sempre DEPOIS dos rápidos: só pega render com todos eles ocupados. O melhor
        # uso do HP é navegador (maquina_remota: uploads/logins), que não depende de processador.
        # CELULARES_LENTO_IGUAL=1 volta ao rodízio puro.
        lento = (lambda h: False) if os.environ.get("CELULARES_LENTO_IGUAL") == "1" else \
            (lambda h: bool(HOSTS[h].get("lento")))
        ordem.sort(key=lambda h: (lento(h), hoje.get(h, {}).get("falhas", 0) > 0, hoje.get(h, {}).get("ok", 0)))
    for host in ordem:
        if not _pegar(host, rotulo):
            continue
        m = medir(host, vale_s=MEDIDA_VALE_S)
        if m.get("ocioso"):
            return host
        _soltar(host)
    return None


def rodar_ffmpeg(cmd, timeout=900, rotulo="ffmpeg"):
    """Roda o comando ffmpeg num celular livre. True = a saída (último argumento) chegou inteira aqui."""
    lig, _motivo = _ligado()
    if not lig:
        return False
    try:
        entradas, saida, args, nome_saida, mb = _preparar(cmd)
    except (ValueError, OSError) as e:
        log(f"[{rotulo}] fica no PC: {e}")
        return False
    host = _escolher(rotulo)
    if not host:
        return False
    job = f"{datetime.now():%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"
    pasta = f"{REMOTO}/{job}"
    ini = time.time()
    ok = False
    parcial = saida.with_name(saida.name + ".celular.part")
    try:
        # 1ª conexão: tar das entradas pelo stdin (nomes in0.mp4, in1.mp4...) e o ffmpeg em seguida
        # 11/11: notebook Linux (STI) tem o ffmpeg estático em ~/bin (sem sudo); no Termux ~/bin não existe = igual
        remoto = (f"export PATH=$HOME/bin:$PATH; mkdir -p ~/{pasta} && cd ~/{pasta} && tar -xf - && "
                  + " ".join(shlex.quote(a) for a in args) + " 2> ffmpeg.err; rc=$?; tail -c 1500 ffmpeg.err >&2; exit $rc")
        p = subprocess.Popen([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15",
                              "-o", "ServerAliveCountMax=4", host, remoto], stdin=subprocess.PIPE,
                             stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=_SEM_JANELA)
        erro_tar = []

        def _mandar():
            try:
                with tarfile.open(fileobj=p.stdin, mode="w|") as t:
                    for k, e in enumerate(entradas):
                        t.add(str(e), arcname=f"in{k}{e.suffix}")
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
            p.wait(timeout=timeout)  # communicate() fecharia o stdin no meio do tar da outra thread
        except subprocess.TimeoutExpired:
            p.kill()
            raise
        err = p.stderr.read()  # só a cauda do ffmpeg.err (1,5 KB): não enche o pipe
        th.join(30)
        if erro_tar or p.returncode != 0:
            msg = (err or b"").decode("utf-8", "replace").strip().splitlines()[-3:]
            raise RuntimeError(f"rc {p.returncode} {erro_tar[:1]} {' | '.join(msg)[:400]}")
        ffmpeg_s = time.time() - ini
        # 2ª conexão: traz a saída e apaga a pasta de lá
        with open(parcial, "wb") as f:
            r = _ssh(host, f"cat ~/{pasta}/{nome_saida}", timeout=max(600, timeout // 2), stdout=f)
        if r.returncode != 0 or parcial.stat().st_size < 1000:
            raise RuntimeError(f"não veio a saída (rc {r.returncode}, {parcial.stat().st_size} bytes)")
        os.replace(parcial, saida)
        ok = True
        seg = time.time() - ini
        log(f"[{rotulo}] {HOSTS[host]['nome']}: ok em {seg:.0f} s (ffmpeg+envio {ffmpeg_s:.0f} s; {mb:.0f} MB entrada, "
            f"{saida.stat().st_size / 1048576:.1f} MB saída) -> {saida.name}")
        return True
    except Exception as e:  # noqa: BLE001
        log(f"[{rotulo}] {HOSTS[host]['nome']}: FALHOU ({type(e).__name__}: {str(e)[:400]}) — volta pro PC")
        return False
    finally:
        try:
            parcial.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            _ssh(host, f"rm -rf ~/{pasta}", timeout=60)
        except Exception:  # noqa: BLE001
            pass
        _contar(host, ok, time.time() - ini)
        _soltar(host)


# ─── linha de comando ────────────────────────────────────────────────────────
def _testar(host=None):
    """Render de prova: 3 clipes 1080x1920 (8 s, com som) juntos por xfade — o mesmo tipo de comando do
    fx_clips._render_xfade_segment. Compara com o PC1 e confere a saída com ffprobe."""
    import shutil
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="celular_teste_", dir=str(EST)))
    try:
        clipes = []
        for k, cor in enumerate(("testsrc2", "smptehdbars", "mandelbrot")):
            c = tmp / f"c{k}.mp4"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"{cor}=size=1080x1920:rate=30:duration=8"
                            if cor != "mandelbrot" else "mandelbrot=size=1080x1920:rate=30", "-f", "lavfi", "-i",
                            f"sine=frequency={300 + 100 * k}:duration=8", "-t", "8", "-c:v", "libx264", "-preset",
                            "ultrafast", "-c:a", "aac", "-shortest", str(c)], check=True, creationflags=_SEM_JANELA)
            clipes.append(str(c))
        fc = ";".join([f"[{i}:v]format=yuv420p,fps=30,scale=1080:1920,setsar=1,settb=AVTB,setpts=PTS-STARTPTS,fps=30[v{i}]"
                       for i in range(3)] + [f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]"
                                             for i in range(3)]
                      + ["[v0][v1]xfade=transition=fade:duration=0.5:offset=7.5[vx1]", "[a0][a1]acrossfade=d=0.5[ax1]",
                         "[vx1][v2]xfade=transition=slideleft:duration=0.5:offset=15[vx2]", "[ax1][a2]acrossfade=d=0.5[ax2]"])

        def cmd(out):
            return ["ffmpeg", "-y", *sum((["-i", c] for c in clipes), []), "-filter_complex", fc, "-map", "[vx2]",
                    "-map", "[ax2]", "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "44100", "-ac", "2", "-movflags", "+faststart", "-pix_fmt", "yuv420p", str(out)]
        t0 = time.time()
        subprocess.run(cmd(tmp / "pc1.mp4"), check=True, capture_output=True, creationflags=_SEM_JANELA)
        print(f"PC1: {time.time() - t0:.1f} s")
        for h in ([host] if host else list(HOSTS)):
            if h not in HOSTS:
                print(f"{h}: desconhecido ({', '.join(HOSTS)})")
                continue
            outros = [x for x in HOSTS if x != h]  # força este celular: os outros ficam "ocupados" pelo teste
            presos = [x for x in outros if _pegar(x, "teste (reservado)")]
            t0 = time.time()
            out = tmp / f"{h}.mp4"
            ok = rodar_ffmpeg(cmd(out), timeout=600, rotulo=f"teste {h}")
            for x in presos:
                _soltar(x)
            pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height:format=duration",
                                 "-of", "compact", str(out)], capture_output=True, text=True,
                                creationflags=_SEM_JANELA).stdout.strip() if ok else ""
            print(f"{h}: {'OK' if ok else 'FALHOU'} {time.time() - t0:.1f} s (com envio/volta) {pr.replace(chr(10), ' | ')}")
            if ok:  # o fx_clips junta os segmentos com concat -c copy: trecho do PC1 + trecho do celular tem que tocar
                lst = tmp / "lista.txt"
                lst.write_text(f"file '{(tmp / 'pc1.mp4').as_posix()}'\nfile '{out.as_posix()}'\n", encoding="utf-8")
                junto = tmp / f"junto_{h}.mp4"
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                                str(junto)], capture_output=True, creationflags=_SEM_JANELA)
                dec = subprocess.run(["ffmpeg", "-v", "error", "-i", str(junto), "-f", "null", "-"], capture_output=True,
                                     text=True, creationflags=_SEM_JANELA)
                dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                      str(junto)], capture_output=True, text=True, creationflags=_SEM_JANELA).stdout.strip()
                print(f"  concat -c copy PC1+{h}: {dur} s, decodificação "
                      + ("LIMPA" if junto.exists() and not dec.stderr.strip() else f"COM ERRO: {dec.stderr.strip()[:300]}"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if a[:1] == ["testar"]:
        _testar(a[1] if len(a) > 1 else None)
    elif a[:1] == ["limpar"]:
        for h in HOSTS:
            if _ler_lock(h):
                print(f"{h}: renderizando agora — não mexo")
                continue
            r = _ssh(h, f"rm -rf ~/{REMOTO}/* && echo limpo", timeout=60)
            print(f"{h}: {(r.stdout or b'').decode().strip() or 'falhou'}")
    else:
        for h, m in medir_todos().items():
            print(f"{h:9} {'LIVRE  ' if m.get('ocioso') else 'OCUPADO'} {m.get('motivo')} | cpu {m.get('cpu')}% "
                  f"ram {m.get('ram_gb')} GB disco {m.get('disco_gb')} GB")


if __name__ == "__main__":
    main()
