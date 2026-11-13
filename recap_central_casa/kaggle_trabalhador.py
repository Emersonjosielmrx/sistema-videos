"""Roda no KAGGLE (qualquer conta do pool, kernel GPU com internet): pega pedidos da fila pelo rclone.
O rclone.conf vem do dataset privado recap-worker-conf de cada conta. QUEM = KAGGLE_USERNAME.
"""
import io
import json
import re
import os
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

INICIO = time.time()
# Kaggle corta em 12 h e um longo leva ~3 h: pedido novo só nas primeiras 8 h. Na VPS (Docker): TRAB_LIMITE_H=0 = sem fim
_LIM_H = float(os.environ.get("TRAB_LIMITE_H", "7"))  # 27/10: 8 h + longo de 4,2 h passava das 12 h do Kaggle (Cozy Home cortado)
LIMITE_S = _LIM_H * 3600 if _LIM_H > 0 else float("inf")
def _base_maior():
    # 02/11: /kaggle/working tem ~20 GB — longo de 2 h (cLF1, GFrKL) enchia o disco no fim ("Error writing", todo ffmpeg
    # falhando e a sessão morrendo). O trabalho vai pro disco da máquina com MAIS espaço livre (/kaggle/tmp ou /tmp)
    import shutil as _sh
    melhor, livre = Path("/kaggle/working"), -1
    for c in ("/kaggle/working", "/kaggle/tmp", "/tmp"):
        try:
            Path(c).mkdir(parents=True, exist_ok=True)
            f = _sh.disk_usage(c).free
        except OSError:
            continue
        if f > livre:
            melhor, livre = Path(c) if c == "/kaggle/working" else Path(c) / "trab", f
    print(f"[disco] trabalho em {melhor} ({livre / 1e9:.0f} GB livres)", flush=True)
    return melhor


BASE = Path(os.environ["TRAB_BASE"]) if os.environ.get("TRAB_BASE") else _base_maior()
BASE.mkdir(parents=True, exist_ok=True)
QUEM = os.environ.get("TRAB_NOME") or os.environ.get("KAGGLE_USERNAME") or "kaggle"
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
                    "psutil", "pydub", "soundfile", "rapidocr_onnxruntime"], check=True)
    t0 = time.time()
    rc("copy", "manhwa-drive:colab_recap/raiz", str(RAIZ), "--transfers", "16", "--checkers", "32", "--fast-list")
    print(f"raiz copiada em {time.time() - t0:.0f} s", flush=True)
    # 02/11 (dona: "aplique logo o nosso maior problema: produção"; pesquisa H6): encode na T4 (NVENC) em vez dos 4 vCPUs.
    # Teste real de 1 s; passou = ENCODER_GPU=1 e o sitecustomize (colab_traduz) troca libx264 por h264_nvenc em todo
    # ffmpeg (com volta pro libx264 se algum der erro). Não passou = tudo como antes.
    try:
        t = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1920x1080:r=60:d=1",
                            "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "21", "-b:v", "0",
                            "/tmp/_nvenc_teste.mp4"], capture_output=True, text=True, timeout=120)
        if t.returncode == 0 and Path("/tmp/_nvenc_teste.mp4").stat().st_size > 10000:
            os.environ["ENCODER_GPU"] = "1"
            # com o encode na GPU a CPU sobra pros filtros: 3 clipes ao mesmo tempo (anime_segments)
            os.environ.setdefault("ANIME_CLIPES_PARALELO", "3")
            # passada da legenda em 4 fatias (cada uma só com os seus efeitos); no PC (4 núcleos ocupados) empatou —
            # aqui o encode é da GPU e o libass ocupa 1 núcleo, então as fatias usam os outros. Falhou = passada única
            os.environ.setdefault("ANIME_LEGENDA_FATIAS", "4")
            print("NVENC ok: encode na GPU (ENCODER_GPU=1) + 3 clipes em paralelo", flush=True)
        else:
            print(f"NVENC indisponível ({t.stderr[-200:]}) — encode na CPU", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"NVENC teste falhou ({e}) — encode na CPU", flush=True)
    # 02/11: transições em shader (realce_visual): moderngl + contexto OpenGL sem tela (EGL). Falhou = o realce_visual
    # diz "indisponível" e segue no xfade de sempre (nunca derruba o render)
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "moderngl"], check=True, timeout=300)
        os.environ.setdefault("REALCE_TOOLS", str(RAIZ / "D/hipercool-materiais/tools"))
        # 03/11: o 1º anime saiu SEM as gl-transitions ("XOpenDisplay: cannot open display") — sem tela o contexto só
        # abre pelo EGL, e a lib dele pode faltar na imagem: instala libegl1/libgl1 (falhou = segue no xfade)
        subprocess.run("apt-get install -y -qq libegl1 libgl1 libgles2 >/dev/null 2>&1 || "
                       "(apt-get update -qq >/dev/null 2>&1 && apt-get install -y -qq libegl1 libgl1 libgles2 "
                       ">/dev/null 2>&1)", shell=True, timeout=300)
        os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
    except Exception as e:  # noqa: BLE001
        print(f"moderngl não instalou ({e}) — sem transição em shader", flush=True)
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
    preparar_applio()


APPLIO_DIR, APPLIO_VENV = Path("/tmp/applio"), Path("/tmp/applio_venv")
APPLIO_COMMIT = "5379cf261fa7d8085c3b077aa42dabca7c85310b"  # o mesmo do PC (17/10/2026)
_APPLIO_OK = False
_APPLIO_MSG = "não tentou"  # 26/10: vai no vivo_<conta>.json — sem isso não dava pra saber por que o clone não ligou


def preparar_applio():
    """Voz clonada (25/10): com GPU, instala o Applio do PC num ambiente PRÓPRIO (o pip dele troca numpy/torch e
    quebraria o render) + o nosso pipeline.py + contentvec/rmvpe/fcpe. Sem GPU ou falhou = longo sem clone."""
    global _APPLIO_OK, _APPLIO_MSG
    if subprocess.run(["nvidia-smi"], capture_output=True).returncode != 0:
        _APPLIO_MSG = "sem GPU"
        print("sem GPU: longo sem voz clonada", flush=True)
        return
    t0 = time.time()
    try:
        if not (APPLIO_DIR / "core.py").exists():
            APPLIO_DIR.mkdir(parents=True, exist_ok=True)
            for c in (["git", "init", "-q"], ["git", "remote", "add", "origin", "https://github.com/IAHispano/Applio.git"],
                      ["git", "fetch", "-q", "--depth", "1", "origin", APPLIO_COMMIT], ["git", "checkout", "-q", "FETCH_HEAD"]):
                subprocess.run(c, cwd=APPLIO_DIR, check=True, capture_output=True)
        if not (APPLIO_VENV / "bin" / "python").exists():
            # 26/10: no Kaggle o `python -m venv` falha (sem ensurepip/python3-venv) — era por isso que a voz clonada
            # NUNCA ligava. Falhou = virtualenv pelo pip (faz o mesmo ambiente separado, com pip dentro).
            if subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", str(APPLIO_VENV)],
                              capture_output=True).returncode != 0:
                shutil.rmtree(APPLIO_VENV, ignore_errors=True)
                subprocess.run([sys.executable, "-m", "pip", "install", "-q", "virtualenv"], check=True)
                subprocess.run([sys.executable, "-m", "virtualenv", "--system-site-packages", str(APPLIO_VENV)],
                               check=True, capture_output=True)
            subprocess.run([str(APPLIO_VENV / "bin" / "pip"), "install", "-q", "-r",
                            str(APPLIO_DIR / "requirements-engine.txt")], check=True, timeout=3600)
        # 26/10 (dona: "as vozes clonadas dos Cortes"): base Kokoro na nuvem — o lote do voz_clonada_nuvem gera aqui
        r = subprocess.run([str(APPLIO_VENV / "bin" / "pip"), "install", "-q", "kokoro-onnx", "soundfile"],
                           capture_output=True, text=True, timeout=1800)
        if r.returncode != 0:
            print(f"kokoro-onnx não instalou ({r.stderr[-200:]}) — base Kokoro cai pra Francisca", flush=True)
        else:
            os.environ["KOKORO_NUVEM"] = "1"  # o anime_tts só usa a base Kokoro com isto (o amb herda o os.environ)
        patch =RAIZ / "D/hipercool-materiais/tools/applio/rvc/infer/pipeline.py"
        if patch.exists():
            shutil.copyfile(patch, APPLIO_DIR / "rvc" / "infer" / "pipeline.py")
        subprocess.run([str(APPLIO_VENV / "bin" / "python"), "-c",
                        "import os,sys; os.chdir('/tmp/applio'); sys.path.insert(0,'.'); "
                        "from core import run_prerequisites_script; "
                        "run_prerequisites_script(pretraineds_hifigan=False, models=True, exe=False)"],
                       check=True, timeout=1800)
        _APPLIO_OK = True
        _APPLIO_MSG = f"ok em {time.time() - t0:.0f} s"
        print(f"Applio pronto em {time.time() - t0:.0f} s (voz clonada ligada)", flush=True)
    except Exception as e:  # noqa: BLE001
        _APPLIO_MSG = f"falhou: {type(e).__name__}: {str(e)[-300:]} {str(getattr(e, 'stderr', '') or '')[-300:]}"
        print(f"Applio falhou ({type(e).__name__}: {str(e)[-300:]}) — longo sem voz clonada", flush=True)


def _marcar(pid, nome, dados, destino=None):
    # 04/11: 2 longos por sessão (loop_duplo) — temporário com nome por thread (o pronto.json de um não sobe no do outro)
    tmp = BASE / f"_m{threading.get_ident()}_{nome}"
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        rc("copyto", str(tmp), destino or f"{FILA}/{pid}/{nome}")
    finally:
        tmp.unlink(missing_ok=True)


def _livre(arquivos):
    return "pedido.json" in arquivos and not ({"pronto.json", "erro.json"} & arquivos
                                              or any(a.startswith("em_andamento") for a in arquivos))


_DEIXADOS = set()  # pedidos que esta sessão não pode fazer direito (revezamento sem voz clonada)


def proximo():
    for pid in sorted(rc("lsf", FILA, "--dirs-only").split()):
        pid = pid.rstrip("/")
        if pid in _DEIXADOS:
            continue
        # 02/11 (revisão sonnet): conta cortada por cota no meio do longo deixa a marca e agora fica "sem cota" até
        # sexta (não volta pra soltar). Sessão do Kaggle dura <= 12 h: marca com mais de 12,5 h é de sessão morta.
        nomes = _soltar_abandonadas(FILA, pid, set(rc("lsf", f"{FILA}/{pid}").split()), "longo", limite_s=45000)
        if _livre(nomes) and _pegar(pid):
            return pid
    return None


def _soltar(pid):
    for marca in (f"em_andamento_{QUEM}.json", "em_andamento.json"):
        try:
            rc("deletefile", f"{FILA}/{pid}/{marca}")
        except RuntimeError:
            pass


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


def _progresso(pid, titulo, local, log, parar):
    """Dona 25/10: acompanhar o longo (só a %) sem depender do PC. A cada 2 min grava em
    manhwa-drive:colab_recap/progresso_<QUEM>.json a fase e a % pelo pipeline.log (a VPS lê e mostra)."""
    while not parar.wait(120):
        try:
            txt = log.read_text(encoding="utf-8", errors="ignore") if log.exists() else ""
            rot = local / "roteiro.txt"
            total = sum(1 for l in rot.read_text(encoding="utf-8").splitlines() if l.strip()) + 2 if rot.exists() else 0
            audios, clipes = txt.count("wrote audio_"), txt.count("build_clip_from_video] clipe")
            if not total:
                fase, pct = "transcrevendo (Whisper)", 2
            elif "concatenando" in txt:
                # 30/10 (dona: "faz horas que está em 92%"): o acabamento são 4-5 recodificações do vídeo inteiro (~1 h
                # num longo de 80 min) — mostra o passo em que está, pra não parecer travado
                passos = [("queimando música", "acabamento: trilha", 93), ("mascote em", "acabamento: mascote", 94),
                          ("queimando legendas", "acabamento: legenda na tela", 95),
                          ("master:", "acabamento: som final e cortes pros Shorts", 98), ("PRONTO", "subindo o vídeo", 99)]
                fase, pct = "acabamento: juntando os trechos", 92
                for marca, nome, p in passos:
                    if marca in txt:
                        fase, pct = nome, p
            elif clipes:
                fase, pct = "montando os trechos", 50 + 40 * min(clipes, total) // total
            else:
                fase, pct = "narrando", 5 + 45 * min(audios, total) // total
            _marcar(None, "p.json", {"pid": pid, "titulo": titulo, "fase": fase, "pct": pct, "frases": total,
                                     "em": _agora(), "por": QUEM},
                    destino=f"manhwa-drive:colab_recap/progresso_{QUEM}.json")
            # vivo também durante o render (o loop só grava vivo entre pedidos; sem isto o alimentador do PC acha o
            # trabalhador "morto" depois de 30 min renderizando e para de abastecer a fila proporcional às GPUs)
            _marcar(None, "v.json", {"em": _agora()}, destino=f"manhwa-drive:colab_recap/vivo_{QUEM}.json")
        except Exception as e:  # noqa: BLE001 — progresso nunca derruba o render
            print(f"progresso falhou: {e}", flush=True)


def fazer(pid, gpu=None):
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
    # 29/10: as gravações da mascote (e o texto de cada uma) crescem todo dia (tarefa MascoteProducao); antes só
    # vinham quando a GPU ligava e o longo saía sem a pausa com a voz dela
    try:
        rc("copy", "manhwa-drive:colab_recap/raiz/D/hipercool-materiais/assets/mascote_viva",
           str(RAIZ / "D/hipercool-materiais/assets/mascote_viva"))
    except RuntimeError:
        pass
    # 11/11 dona (Medieval 9: meme com apito no começo; memes novos não usados): memes novos do resumo + lista de
    # memes proibidos pelo som (memes_apito.py). Falhou = segue com o que veio no dataset
    for sub in ("memes_img/memes_novos", "memes_img/memes_proibidos_som.json"):
        try:
            cmd = "copy" if not sub.endswith(".json") else "copyto"
            rc(cmd, f"manhwa-drive:colab_recap/raiz/D/hipercool-materiais/assets/{sub}",
               str(RAIZ / "D/hipercool-materiais/assets" / sub))
        except RuntimeError:
            pass
    pedido = json.loads((local / "pedido.json").read_text(encoding="utf-8"))
    print(f"[{_agora()}] pedido {pid}: {pedido.get('titulo', '')[:60]}", flush=True)
    if pedido.get("vozes_lista") and not _APPLIO_OK:
        # 26/10: revezamento de narradores sem voz clonada sairia com 1 voz só — devolve pra fila (outra sessão faz)
        print(f"[{_agora()}] {pid}: revezamento precisa do clone (Applio: {_APPLIO_MSG}) — devolvo pra fila", flush=True)
        _DEIXADOS.add(pid)
        _soltar(pid)
        shutil.rmtree(local, ignore_errors=True)
        return
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
    if pedido.get("tipo") == "manhwa" and (PRODUCAO / "bin" / "marca_site.py").exists():
        # 26/10: marca d'água do site de scan (COLAMANHUA.com...) sai do ORIGINAL antes do render (dona: "remover;
        # se não der, tarja branca com a nossa"). Falhou = segue com o original como estava.
        limpo = local / "source_limpo.mp4"
        try:
            with open(local / "marca_site.log", "w", encoding="utf-8") as f:
                subprocess.run([sys.executable, "-X", "utf8", str(PRODUCAO / "bin" / "marca_site.py"), "limpar",
                                str(fonte), str(limpo)], stdout=f, stderr=subprocess.STDOUT, timeout=3 * 3600)
            if limpo.exists() and limpo.stat().st_size > 1_000_000:
                limpo.replace(fonte)
            print(f"[{_agora()}] {pid}: marca do site: "
                  f"{(local / 'marca_site.log').read_text(encoding='utf-8', errors='ignore').strip()[-160:]}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[{_agora()}] {pid}: limpeza da marca falhou ({type(e).__name__}) — segue o original", flush=True)
    cmd = [sys.executable, "-X", "utf8", str(PRODUCAO / "bin" / "anime-pipeline.py"),
           "--video-source", str(local / "source.mp4"), "--script", str(local / "roteiro.txt"),
           "--titulo", pedido["titulo"], "--formato", "deitado"]
    parar = threading.Event()
    threading.Thread(target=_progresso, args=(pid, pedido.get("titulo", ""), local, log, parar), daemon=True).start()
    amb = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "GEMINI_TTS_PROXY_ENABLED": "0"}
    # 04/11 (dois longos por sessão, loop_duplo): só 1 longo por vez na parte de CPU (anime_segments._vez_da_cpu); a
    # marca _fase_cpu avisa que este entrou nela; cada longo na sua T4 (o NVENC e a voz clonada não disputam)
    amb["TRAB_CPU_LOCK"] = str(BASE / "_cpu.lock")
    amb["TRAB_FASE_CPU_ARQ"] = str(local / "_fase_cpu")
    if gpu is not None:
        amb["CUDA_VISIBLE_DEVICES"] = str(gpu)
        print(f"[{_agora()}] {pid}: GPU {gpu}", flush=True)
    # 12/11 dona ("os longos em outras línguas já deveriam existir; faça do jeito mais eficiente"): pedido com "idioma"
    # = longo traduzido (roteiro.txt já vem na língua, feito no PC pelo longo_idiomas.py). Mesmo pipeline, só troca a
    # voz-base da língua, a fonte da legenda e o "outra língua" (igual ao anime_idiomas dos Shorts).
    if pedido.get("idioma"):
        li = pedido["idioma"]
        amb.update(ANIME_TTS_VOICE=li["voz"], ANIME_LANG_NOME=li["nome"], ANIME_OUTRA_LINGUA="1",
                   ANIME_DESCARACT_FLIP="0")
        for chave, var in (("fonte_png", "ANIME_SUB_FONT_PNG"), ("fonte_ass", "ANIME_SUB_FONT_ASS"),
                           ("engine", "ANIME_SUB_ENGINE")):
            if li.get(chave):  # caminho Windows (D:\...) -> a cópia da raiz aqui (RAIZ/D/...)
                v = li[chave]
                amb[var] = str(RAIZ / v[0].upper() / v[3:].replace("\\", "/")) if re.match(r"^[A-Za-z]:\\", v) else v
        print(f"[{_agora()}] {pid}: LONGO EM {li['nome'].upper()} (voz-base {li['voz']})", flush=True)
    if pedido.get("longo_override"):  # 28/10: variante do teste A/B do melhorador (anime-pipeline._cfg_longo)
        amb["ANIME_LONGO_OVERRIDE"] = json.dumps(pedido["longo_override"], ensure_ascii=False)
        print(f"[{_agora()}] {pid}: variante {pedido.get('variante')}: {amb['ANIME_LONGO_OVERRIDE']}", flush=True)
    voz = pedido.get("voz_clonada")
    if voz and _APPLIO_OK:  # 25/10: voz clonada dos Cortes no longo (GPU)
        try:
            destino_voz = RAIZ / "D/hipercool-materiais/models/rvc/vozes" / voz
            # 26/10: vozes ficam num cache único do Drive (colab_recap/vozes/<voz>); pedido antigo ainda traz a dele
            try:
                rc("copy", f"manhwa-drive:colab_recap/vozes/{voz}", str(destino_voz))
            except RuntimeError:
                pass
            if not (destino_voz / f"{voz}.pth").exists():
                rc("copy", f"{FILA_SRC}/{pid}/voz", str(destino_voz))
            amb.update(VOZ_CLONADA=voz, VOZ_CLONADA_BASE=pedido.get("voz_clonada_base") or "francisca",
                       VOZ_CLONADA_VERSAO="2",
                       VOZES_PY_NUVEM=str(APPLIO_VENV / "bin" / "python"), APPLIO_DIR=str(APPLIO_DIR))
            print(f"[{_agora()}] {pid}: voz clonada {voz}", flush=True)
            # 26/10 teste de narradores: revezamento — as outras vozes vêm do mesmo cache; só as que baixaram entram
            lista = []
            for v in pedido.get("vozes_lista") or []:
                dv = RAIZ / "D/hipercool-materiais/models/rvc/vozes" / v
                try:
                    rc("copy", f"manhwa-drive:colab_recap/vozes/{v}", str(dv))
                except RuntimeError:
                    pass
                if (dv / f"{v}.pth").exists() and (dv / f"{v}.index").exists():
                    lista.append(v)
            for v in pedido.get("vozes_extra") or []:  # 28/10: vozes de personagem (anime-pipeline._falas_personagem)
                try:
                    rc("copy", f"manhwa-drive:colab_recap/vozes/{v}", str(RAIZ / "D/hipercool-materiais/models/rvc/vozes" / v))
                except RuntimeError:
                    print(f"[{_agora()}] {pid}: voz de personagem {v} não baixou — essas falas ficam com o narrador",
                          flush=True)
            # 05/11 dona ("as falas estão aprovadas, pode começar"): banco de falas REAIS de cada narrador do longo
            # (manhwa-drive:narradores_originais/<voz>/banco, falas_narradores.py) vai pra pasta do vídeo; o
            # anime_segments._falas_reais encaixa reação/piada/bordão no bloco do mesmo narrador. Sem banco = como antes.
            # 12/11 dona: longo em OUTRA LÍNGUA não leva as falas reais dos narradores (são em português)
            for v in ([] if pedido.get("idioma") else dict.fromkeys([voz] + lista)):
                try:
                    rc("copy", f"manhwa-drive:narradores_originais/{v}/banco", str(local / "falas_reais" / v),
                       "--exclude", "previa_*.wav")
                except (RuntimeError, NameError):
                    pass
            if len(lista) >= 2:
                amb["VOZ_CLONADA_LISTA"] = ",".join(lista)
                print(f"[{_agora()}] {pid}: revezamento de {len(lista)} narradores: {', '.join(lista)}", flush=True)
        except RuntimeError as e:
            print(f"[{_agora()}] {pid}: voz {voz} não baixou ({e}) — sem clone", flush=True)
    elif voz:
        print(f"[{_agora()}] {pid}: pedido com voz {voz}, mas sem GPU/Applio nesta sessão — sem clone", flush=True)
    with open(log, "w", encoding="utf-8") as f:
        rcod = subprocess.run(cmd, cwd=PRODUCAO, stdout=f, stderr=subprocess.STDOUT, env=amb).returncode
    parar.set()
    seg = round(time.time() - t0)
    final = local / "final_anime_deitado.mp4"
    rc("copyto", str(log), f"{FILA}/{pid}/pipeline.log")
    try:  # 04/11: uso de CPU/GPU minuto a minuto durante ESTE longo (medir o ganho dos 2 longos juntos)
        linhas = [l for l in USO_LOG.read_text(encoding="utf-8").splitlines() if l and float(l.split()[0]) >= t0]
        (local / "uso.log").write_text("\n".join(linhas) + "\n", encoding="utf-8")
        rc("copyto", str(local / "uso.log"), f"{FILA}/{pid}/uso.log")
    except Exception:  # noqa: BLE001
        pass
    if rcod == 0 and final.exists():
        # 26/10: KkJZ saiu com 9 min pra 1069 frases (render perdeu a maior parte) e foi marcado pronto. Abaixo de 1 s
        # por frase do roteiro = render quebrado: vira erro (não vai pro canal) e o log fica na fila pra investigar.
        try:
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                        str(final)], capture_output=True, text=True).stdout.strip())
            rot = local / "roteiro.txt"
            frases = sum(1 for l in rot.read_text(encoding="utf-8").splitlines() if l.strip()) if rot.exists() else 0
            if frases >= 40 and dur < 1.0 * frases:
                print(f"[{_agora()}] {pid}: vídeo curto demais ({dur:.0f} s pra {frases} frases) — erro", flush=True)
                rcod = 99
                with open(log, "a", encoding="utf-8") as f:
                    f.write(f"\n[trabalhador] VIDEO CURTO: {dur:.0f} s pra {frases} frases\n")
                rc("copyto", str(log), f"{FILA}/{pid}/pipeline.log")
        except (ValueError, OSError):
            pass
    if rcod == 0 and final.exists():
        # 25/10: roteiro feito aqui (sem legenda do YouTube) e capítulos do longo voltam pra ficha do PC
        for extra in ("roteiro.txt", "capitulos.json", "resumo_fim.json"):  # 12/11: resumo_fim = compilado da série
            if (local / extra).exists():
                try:
                    rc("copyto", str(local / extra), f"{FILA}/{pid}/{extra}")
                except RuntimeError:
                    pass
        # 04/11 (pesquisa qc-skill, QA dos longos igual ao dos Shorts): varredura do vídeo inteiro (preto, congelado,
        # mudo, volume — bin\qa_video.py) decodificando na GPU, ENQUANTO o final sobe pro Drive; qa.json vai pra fila
        # antes do pronto.json (o PC copia pra ficha e o postar_longos avisa). Nunca trava o vídeo (só censura trava).
        def _qa():
            try:
                t_qa = time.time()
                r = subprocess.run([sys.executable, "-X", "utf8", str(PRODUCAO / "bin" / "qa_video.py"), str(final)],
                                   cwd=str(PRODUCAO / "bin"), capture_output=True, text=True, timeout=3600,
                                   env={**amb, "QA_HWACCEL": "cuda"} if _GPUS and _GPUS[0] else amb)
                if (local / "qa.json").exists():
                    rc("copyto", str(local / "qa.json"), f"{FILA}/{pid}/qa.json")
                print(f"[{_agora()}] {pid}: QA em {time.time() - t_qa:.0f} s: {(r.stdout or r.stderr).strip()[-200:]}",
                      flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"[{_agora()}] {pid}: QA falhou ({type(e).__name__}: {e})", flush=True)
        qa_th = threading.Thread(target=_qa, daemon=True)
        qa_th.start()
        # 30/10: VgQU renderizou inteiro (PRONTO 13:57 UTC, master e 5 cortes) e o envio do final (~1 GB) pro Drive
        # falhou 1x — a exceção derrubou o kernel sem pronto.json e as 5 h de GPU se perderam. Agora 5 tentativas.
        for tentativa in range(5):
            try:
                rc("copyto", str(final), f"{FILA_SRC}/{pid}/final_anime_deitado.mp4")
                break
            except RuntimeError as e:
                print(f"[{_agora()}] {pid}: envio do final falhou ({tentativa + 1}/5): {str(e)[-150:]}", flush=True)
                if tentativa == 4:
                    raise
                time.sleep(60 * (tentativa + 1))
        # 28/10: os melhores trechos (bin\melhores_cortes.py) vão junto pros canais de cortes
        if (local / "cortes_longo" / "cortes.json").exists():
            try:
                rc("copy", str(local / "cortes_longo"), f"{FILA_SRC}/{pid}/cortes_longo")
            except RuntimeError:
                pass
        for lugar in (FILA, FILA_SRC):
            try:
                rc("deletefile", f"{lugar}/{pid}/source.mp4")
            except RuntimeError:
                pass
        # 26/10 (dona: "assim que tiver vídeo com a narração nova, me mande"): 40 s de áudio pra ela ouvir no Telegram
        try:
            amostra = local / "amostra.mp3"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "90", "-t", "40", "-i", str(final), "-vn",
                            "-c:a", "libmp3lame", "-b:a", "128k", str(amostra)], check=True, timeout=300)
            rc("copyto", str(amostra), f"{FILA}/{pid}/amostra.mp3")
        except (subprocess.SubprocessError, RuntimeError, OSError):
            pass
        # 26/10: registro do que saiu (a dona confere voz clonada/marca sem precisar do log do Kaggle)
        try:  # 31/10: versão do código que fez este longo (montar_pacote._carimbar_versao) — vai pro Telegram
            versao = json.loads((PRODUCAO / "config" / "versao_codigo.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            versao = None
        marcas = None  # 01/11 dona: onde cada novidade aparece no vídeo (lista "o que testar" da prévia)
        try:
            # 02/11: a de MAIS marcas = a do longo (os cortes em pé, feitos depois, gravam a deles mais tarde — na
            # PREVIA5 a lista veio do corte, só até 0:24)
            _mv = list(local.rglob("marcas_visuais.json"))
            if _mv:
                marcas = max((json.loads(p.read_text(encoding="utf-8")) for p in _mv), key=len)
        except (OSError, ValueError):
            pass
        qa_th.join(timeout=1800)  # 04/11: qa.json na fila antes do pronto (o PC só recolhe com o pronto lá)
        _marcar(pid, "pronto.json", {"fim": _agora(), "segundos": seg, "por": QUEM, "versao": versao, "marcas": marcas,
                                     "variante": pedido.get("variante"), "experimento": pedido.get("experimento"),
                                     "tipo": pedido.get("tipo"),  # 02/11: anime_recap = título próprio na postagem
                                     # 02/11 (acompanhamento): o que acelerou este render — pra comparar tempos
                                     "render_gpu": {k: os.environ.get(k) for k in ("ENCODER_GPU", "ANIME_LEGENDA_FATIAS",
                                                                                  "ANIME_CLIPES_PARALELO", "TRAB_COTA_H")},
                                     "longo_override": pedido.get("longo_override"),
                                     # 30/10: variantes A/B por fator e modo de narradores (comparar pelas views)
                                     "ab": pedido.get("ab"), "narradores_modo": pedido.get("narradores_modo"),
                                     "voz_clonada": amb.get("VOZ_CLONADA"), "applio_ok": _APPLIO_OK,
                                     "voz_base": amb.get("VOZ_CLONADA_BASE"),
                                     "vozes_lista": amb.get("VOZ_CLONADA_LISTA"),
                                     "kokoro_nuvem": os.environ.get("KOKORO_NUVEM") == "1",
                                     "marca_site": ((local / "marca_site.log").read_text(encoding="utf-8", errors="ignore")
                                                    .strip()[-200:] if (local / "marca_site.log").exists() else None)})
    else:
        _marcar(pid, "erro.json", {"ok": False, "error": f"rc={rcod}" if rcod else "sem final", "segundos": seg,
                                   "voz_clonada": amb.get("VOZ_CLONADA"), "applio": _APPLIO_MSG,
                                   "log": log.read_text(encoding="utf-8", errors="ignore")[-4000:], "por": QUEM})
    for marca in (f"em_andamento_{QUEM}.json", "em_andamento.json"):
        try:
            rc("deletefile", f"{FILA}/{pid}/{marca}")
        except RuntimeError:
            pass
    shutil.rmtree(local, ignore_errors=True)
    print(f"[{_agora()}] {pid}: {'OK' if rcod == 0 and final.exists() else 'ERRO'} ({seg} s)", flush=True)


# ───────── Shorts de comentários (projeto D:\videos-comentarios, dona 01/11: "produzir em lotes no Kaggle" para liberar
# RAM/CPU do PC1 pro Veo). O PC1 manda o pedido PRONTO (comentários lidos, elenco, roteiro e efeitos escolhidos pela IA)
# em fila_comentarios/<id>/ (pedido.json = cfg do comentarios_video.py + roteiro.json + efeitos.json + source.mp4); aqui
# só voz clonada (GPU) + render. Lote = todos os pedidos livres a cada volta, antes do recap longo (cada um leva minutos).
FILA_COM = "manhwa-drive:colab_recap/fila_comentarios"
COM_DIR = RAIZ / "D/videos-comentarios"


def _pegar_com(pid):
    eu = {"desde": _agora(), "por": QUEM}
    _marcar(None, "c.json", eu, destino=f"{FILA_COM}/{pid}/em_andamento_{QUEM}.json")
    time.sleep(15)
    outros = [n for n in rc("lsf", f"{FILA_COM}/{pid}").split()
              if n.startswith("em_andamento_") and n != f"em_andamento_{QUEM}.json"]
    for n in outros:
        try:
            d = json.loads(rc("cat", f"{FILA_COM}/{pid}/{n}"))
            if (d.get("desde", ""), d.get("por", n)) < (eu["desde"], QUEM):
                rc("deletefile", f"{FILA_COM}/{pid}/em_andamento_{QUEM}.json")
                return False
        except (RuntimeError, ValueError):
            pass
    return True


_GPUS = []


def _gpu_paralela():
    """02/11 (pesquisa GPU): o Kaggle só dá T4 x2 hoje (P100 aposentada) e o longo usa só a GPU 0. A linha paralela
    (Shorts/comentários) vai pra GPU 1 — cada T4 tem o próprio NVENC, então um não espera o outro. 1 GPU = como antes."""
    if not _GPUS:
        try:
            _GPUS.append(subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True).stdout.count("GPU "))
        except OSError:
            _GPUS.append(0)
    return {"CUDA_VISIBLE_DEVICES": "1"} if _GPUS[0] >= 2 else {}


def fazer_comentario(pid):
    local = TRABALHO / "com" / pid
    shutil.rmtree(local, ignore_errors=True)
    rc("copy", f"{FILA_COM}/{pid}", str(local))
    for origem, destino in (("D/videos-comentarios/bin", COM_DIR / "bin"), ("D/ms-energy/bin", RAIZ / "D/ms-energy/bin"),
                            ("D/tmp_logs/sons_novos/cortados", RAIZ / "D/tmp_logs/sons_novos/cortados"),
                            ("C/Windows/Fonts", RAIZ / "C/Windows/Fonts")):
        try:
            rc("copy", f"manhwa-drive:colab_recap/raiz/{origem}", str(destino))
        except RuntimeError as e:
            print(f"[{_agora()}] comentários {pid}: {origem} não veio ({str(e)[-120:]})", flush=True)
    cfg = json.loads((local / "pedido.json").read_text(encoding="utf-8"))
    for voz in {f["voz"] for f in cfg["falas"]}:
        try:
            rc("copy", f"manhwa-drive:colab_recap/vozes/{voz}", str(RAIZ / "D/hipercool-materiais/models/rvc/vozes" / voz))
        except RuntimeError:
            pass
    cache = COM_DIR / "tmp" / cfg["cache"]
    cache.mkdir(parents=True, exist_ok=True)
    for nome in ("roteiro.json", "efeitos.json"):
        if (local / nome).exists():
            shutil.copy(local / nome, cache / nome)
    cfg.update(video_base=str(local / "source.mp4"), output=str(local / "video.mp4"))
    (local / "cfg.json").write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    amb = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
           "VOZES_PY_NUVEM": str(APPLIO_VENV / "bin" / "python"), "APPLIO_DIR": str(APPLIO_DIR), **_gpu_paralela()}
    t0 = time.time()
    log = local / "comentarios.log"
    with open(log, "w", encoding="utf-8") as f:
        rcod = subprocess.run([sys.executable, "-X", "utf8", str(COM_DIR / "bin" / "comentarios_video.py"), "--config",
                               str(local / "cfg.json")], cwd=str(COM_DIR), stdout=f, stderr=subprocess.STDOUT,
                              env=amb, timeout=3600).returncode
    seg = round(time.time() - t0)
    video = local / "video.mp4"
    if rcod == 0 and video.exists() and video.stat().st_size > 500_000:
        rc("copyto", str(video), f"{FILA_COM}/{pid}/video.mp4")
        final = cache / "falas_final.json"
        if final.exists():
            rc("copyto", str(final), f"{FILA_COM}/{pid}/falas_final.json")
        _marcar(None, "c.json", {"fim": _agora(), "segundos": seg, "por": QUEM}, destino=f"{FILA_COM}/{pid}/pronto.json")
    else:
        _marcar(None, "c.json", {"ok": False, "error": f"rc={rcod}", "segundos": seg, "por": QUEM, "applio": _APPLIO_MSG,
                                 "log": log.read_text(encoding="utf-8", errors="ignore")[-4000:]},
                destino=f"{FILA_COM}/{pid}/erro.json")
    try:
        rc("deletefile", f"{FILA_COM}/{pid}/em_andamento_{QUEM}.json")
    except RuntimeError:
        pass
    shutil.rmtree(local, ignore_errors=True)
    shutil.rmtree(cache, ignore_errors=True)
    print(f"[{_agora()}] comentários {pid}: {'OK' if rcod == 0 and video.exists() else 'ERRO'} ({seg} s)", flush=True)


def _soltar_abandonadas(fila, pid, nomes, rotulo, limite_s=7200):
    """02/11: a sessão que pegou o pedido acabou no meio e a marca ficou órfã (comentário oyIlXAs1REE preso 5 h; Short
    TESTE_lote preso 8 h). Um Short leva minutos: marca com mais de 2 h sem pronto/erro = abandonada -> volta pra fila."""
    if "pedido.json" in nomes and not ({"pronto.json", "erro.json"} & nomes):
        for n in [x for x in nomes if x.startswith("em_andamento")]:
            try:
                txt = rc("cat", f"{fila}/{pid}/{n}")
            except RuntimeError:  # erro de rede/Drive: não sabemos — nunca apagar a marca de quem pode estar vivo
                continue
            try:
                desde = json.loads(txt).get("desde", "")
                velha = (datetime.now(timezone.utc) - datetime.fromisoformat(desde)).total_seconds() > limite_s
            except ValueError:  # marca corrompida
                velha = True
            if velha:
                rc("deletefile", f"{fila}/{pid}/{n}")
                nomes.discard(n)
                print(f"[{_agora()}] {rotulo} {pid}: marca abandonada {n} solta", flush=True)
    return nomes


def lote_comentarios():
    """Todos os pedidos de comentários livres agora (só com voz clonada: sem Applio o Short sairia com voz errada)."""
    if not _APPLIO_OK:
        return
    try:
        pids = sorted(p.rstrip("/") for p in rc("lsf", FILA_COM, "--dirs-only").split())
    except RuntimeError:
        return
    for pid in pids:
        if time.time() - INICIO > SESSAO_MAX_S - 1800:
            return
        try:
            nomes = _soltar_abandonadas(FILA_COM, pid, set(rc("lsf", f"{FILA_COM}/{pid}").split()), "comentários")
            if _livre(nomes):
                _ocupado(lambda: _pegar_com(pid) and fazer_comentario(pid))
        except Exception as e:  # noqa: BLE001 — comentário nunca derruba o trabalhador do recap
            print(f"[{_agora()}] comentários {pid}: falhou ({type(e).__name__}: {str(e)[-200:]})", flush=True)
            try:
                rc("deletefile", f"{FILA_COM}/{pid}/em_andamento_{QUEM}.json")
            except RuntimeError:
                pass


# ───────── Shorts de parceiros/cortes em LOTE (dona 02/11: "usar o Kaggle pra produzir em lotes os Shorts de corte —
# um só não compensa, lote sim — e liberar RAM/CPU do PC pros Veo 3"). O PC1 (bin\lote_shorts_kaggle.py) põe em
# fila_shorts/<id>/ o pedido (pedido.json = argumentos do anime_auto.py --modo short) + source.mp4 já baixado (yt-dlp fica
# no PC: o IP do Kaggle é bloqueado pelo YouTube). Aqui: anime_auto com a voz clonada (GPU) e o vídeo volta pro Drive;
# o PC recolhe e posta como antes. Mesma linha paralela dos comentários.
FILA_SH = "manhwa-drive:colab_recap/fila_shorts"


def fazer_short(pid):
    local = TRABALHO / "sh" / pid
    shutil.rmtree(local, ignore_errors=True)
    rc("copy", f"{FILA_SH}/{pid}", str(local))
    ped = json.loads((local / "pedido.json").read_text(encoding="utf-8"))
    for voz in ped.get("vozes") or []:
        try:
            rc("copy", f"manhwa-drive:colab_recap/vozes/{voz}", str(RAIZ / "D/hipercool-materiais/models/rvc/vozes" / voz))
        except RuntimeError:
            pass
    env_ped = {k: str(v) for k, v in (ped.get("env") or {}).items()}
    if env_ped.get("VOZ_CLONADA"):  # anime_tts e voz_clonada_nuvem esperam SÓ o nome da voz (igual ao longo na linha 367)
        env_ped["VOZ_CLONADA"] = Path(env_ped["VOZ_CLONADA"]).name
    # 02/11: sem VOZES_PY_NUVEM o lote da voz clonada rodava no python do kernel (sem Applio) e TODO Short com voz
    # clonada falhava em 0,3 s (1º Short real de parceiro, wFe7L3BNXQM). O longo (fazer) e os comentários já passavam.
    amb = {**os.environ, **env_ped, **_gpu_paralela(), "VOZES_PY_NUVEM": str(APPLIO_VENV / "bin" / "python"),
           "APPLIO_DIR": str(APPLIO_DIR), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "ANIME_ORIENT": "vertical",
           "ANIME_MAX_CPU_PCT": "0"}  # a guarda de CPU do PC não vale aqui (o longo na GPU usa CPU o tempo todo)
    t0 = time.time()
    log = local / "short.log"
    # mesmo comando do anime_auto.fazer_short no PC: o roteiro/voz já vieram escolhidos, aqui só renderiza
    args = [sys.executable, "-X", "utf8", str(PRODUCAO / "bin" / "anime-pipeline.py"), "--video-source",
            str(local / "source.mp4"), "--script", str(local / "roteiro.txt"), "--titulo", ped.get("titulo", ""),
            "--formato", "short", "--short-source-kind", ped.get("short_kind", "reframe")]
    with open(log, "w", encoding="utf-8") as f:
        rcod = subprocess.run(args, cwd=str(local), stdout=f, stderr=subprocess.STDOUT, env=amb,
                              timeout=2400).returncode
    seg = round(time.time() - t0)
    videos = sorted(local.rglob("final_anime_short*.mp4"))
    if rcod == 0 and videos and videos[0].stat().st_size > 300_000:
        rc("copyto", str(videos[0]), f"{FILA_SH}/{pid}/video.mp4")
        for extra in ("marcas_visuais.json", "_testes_usados.json"):
            for p in local.rglob(extra):
                rc("copyto", str(p), f"{FILA_SH}/{pid}/{extra}")
                break
        _marcar(None, "s.json", {"fim": _agora(), "segundos": seg, "por": QUEM}, destino=f"{FILA_SH}/{pid}/pronto.json")
    else:
        clone_log = next(iter(local.rglob("clone.log")), None)  # o motivo da voz clonada fica aqui, não no short.log
        _marcar(None, "s.json", {"ok": False, "error": f"rc={rcod}", "segundos": seg, "por": QUEM, "applio": _APPLIO_MSG,
                                 "log": log.read_text(encoding="utf-8", errors="ignore")[-4000:],
                                 "clone_log": clone_log.read_text(encoding="utf-8", errors="ignore")[-2500:]
                                 if clone_log else None},
                destino=f"{FILA_SH}/{pid}/erro.json")
    try:
        rc("deletefile", f"{FILA_SH}/{pid}/em_andamento_{QUEM}.json")
    except RuntimeError:
        pass
    shutil.rmtree(local, ignore_errors=True)
    print(f"[{_agora()}] short {pid}: {'OK' if rcod == 0 and videos else 'ERRO'} ({seg} s)", flush=True)


def lote_shorts():
    """Todos os Shorts livres agora (precisa da voz clonada: sem Applio o Short sairia com voz errada)."""
    if not _APPLIO_OK:
        return
    try:
        pids = sorted(p.rstrip("/") for p in rc("lsf", FILA_SH, "--dirs-only").split())
    except RuntimeError:
        return
    for pid in pids:
        if time.time() - INICIO > SESSAO_MAX_S - 1800:
            return
        try:
            nomes = _soltar_abandonadas(FILA_SH, pid, set(rc("lsf", f"{FILA_SH}/{pid}").split()), "short")
            if _livre(nomes) and "source.mp4" in nomes:
                # pegar dentro do _ocupado: a sessão não sai no meio da marca (deixaria órfã — revisão sonnet 02/11)
                _ocupado(lambda: _pegar_sh(pid) and fazer_short(pid))
        except Exception as e:  # noqa: BLE001 — Short nunca derruba o trabalhador do recap
            print(f"[{_agora()}] short {pid}: falhou ({type(e).__name__}: {str(e)[-200:]})", flush=True)
            try:
                rc("deletefile", f"{FILA_SH}/{pid}/em_andamento_{QUEM}.json")
            except RuntimeError:
                pass


FILA_TR = "manhwa-drive:colab_recap/fila_treino"


def fazer_treino(pid):
    """06/11 dona ("faça o retreino, mantenha as duas versões, quero ver se a voz dos dubladores melhorou"): treina a
    voz <pedido.voz> com o material LONGO (voz.wav de 1-2 h, já separada na hermes-staging) e devolve o modelo NOVO
    + amostra da MESMA frase no modelo atual e no novo. Nada substitui o modelo de produção: vai pra
    <pid>/saida/<voz>_v4.pth/.index e amostras/{atual,novo}.wav. Applio igual ao do notebook v3 (Ov2Super 32k)."""
    local = TRABALHO / "tr" / pid
    shutil.rmtree(local, ignore_errors=True)
    rc("copy", f"{FILA_TR}/{pid}", str(local))
    ped = json.loads((local / "pedido.json").read_text(encoding="utf-8"))
    voz, epocas = ped["voz"], int(ped.get("epocas", 200))
    py = str(APPLIO_VENV / "bin" / "python")
    t0 = time.time()
    log = local / "treino.log"
    try:
        pre = Path("/tmp/pretrained_ov2super")
        pre.mkdir(exist_ok=True)
        import urllib.request
        for n in ("f0Ov2Super32kG.pth", "f0Ov2Super32kD.pth"):
            if not (pre / n).exists():
                urllib.request.urlretrieve(f"https://huggingface.co/ORVC/Ov2Super/resolve/main/{n}", pre / n)
        dados = local / "dados"
        dados.mkdir(exist_ok=True)
        if ped.get("separar"):  # áudio com música (trecho do vídeo): voz limpa na GPU antes (treinar com música estraga)
            sep_pkgs = Path("/tmp/sep_pkgs")
            if not (sep_pkgs / "audio_separator").exists():
                subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--target", str(sep_pkgs),
                                "audio-separator[gpu]"], check=True, timeout=1800)
            sep_out = local / "sep"
            sep_out.mkdir(exist_ok=True)
            subprocess.run([sys.executable, "-c", "import sys; from audio_separator.utils.cli import main; "
                            "sys.argv[0]='audio-separator'; main()", str(local / "voz.wav"), "-m", "Kim_Vocal_2.onnx",
                            "--model_file_dir", "/tmp/sep_modelos", "--output_dir", str(sep_out), "--output_format",
                            "WAV", "--single_stem", "Vocals"], check=True, timeout=3 * 3600,
                           env=dict(os.environ, PYTHONPATH=str(sep_pkgs)))
            vocais = next(sep_out.glob("*Vocals*.wav"))
            shutil.move(str(vocais), dados / "voz.wav")
            (local / "voz.wav").unlink(missing_ok=True)
        else:
            shutil.move(str(local / "voz.wav"), dados / "voz.wav")
        nome = f"{voz}_v4"
        cpus = str(os.cpu_count() or 4)
        etapas = [  # nomes do core.py do Applio 5379cf2 (click: --opcao-com-hifen; sim/não = flag sem valor)
            ["prerequisites", "--no-pretraineds-hifigan", "--models", "--no-exe"],
            ["preprocess", "--model-name", nome, "--dataset-path", str(dados), "--sample-rate", "32000",
             "--cpu-cores", cpus, "--cut-preprocess", "Automatic", "--chunk-len", "3.0", "--overlap-len", "0.3",
             "--normalization-mode", "post"],
            ["extract", "--model-name", nome, "--f0-method", "rmvpe", "--cpu-cores", cpus, "--gpu", "0",
             "--sample-rate", "32000", "--embedder-model", "contentvec"],
            ["train", "--model-name", nome, "--save-every-epoch", "50", "--save-only-latest", "--save-every-weights",
             "--total-epoch", str(epocas), "--sample-rate", "32000", "--batch-size", "8", "--gpu", "0",
             "--pretrained", "--custom-pretrained", "--g-pretrained-path", str(pre / "f0Ov2Super32kG.pth"),
             "--d-pretrained-path", str(pre / "f0Ov2Super32kD.pth")],
            ["index", "--model-name", nome],
        ]
        with open(log, "w", encoding="utf-8") as f:
            for e in etapas:
                r = subprocess.run([py, "core.py", *e], cwd=str(APPLIO_DIR), stdout=f, stderr=subprocess.STDOUT,
                                   timeout=6 * 3600)
                if r.returncode != 0:
                    raise RuntimeError(f"etapa {e[0]} falhou (rc {r.returncode})")
        logs = APPLIO_DIR / "logs" / nome
        pesos = sorted(logs.glob(f"{nome}_*e_*s.pth"), key=lambda p: int(re.search(r"_(\d+)e_", p.name).group(1)))
        indice = next(logs.glob("*.index"), None)
        if not pesos or not indice:
            raise RuntimeError("treino terminou sem .pth/.index")
        saida = local / "saida"
        saida.mkdir(exist_ok=True)
        shutil.copyfile(pesos[-1], saida / f"{nome}.pth")
        shutil.copyfile(indice, saida / f"{nome}.index")
        # mesma frase nos dois modelos (base edge Francisca do pedido, mesmos parâmetros da produção)
        am = saida / "amostras"
        am.mkdir(exist_ok=True)
        tom = str(ped.get("tom", 0))
        for rot, pth, idx in (("atual", local / "atual" / f"{voz}.pth", local / "atual" / f"{voz}.index"),
                              ("novo", saida / f"{nome}.pth", saida / f"{nome}.index")):
            if pth.exists():
                subprocess.run([py, "core.py", "infer", "--input-path", str(local / "base.wav"),
                                "--output-path", str(am / f"{rot}.wav"), "--pth-path", str(pth), "--index-path",
                                str(idx), "--pitch", tom, "--index-rate", "0.5", "--protect", "0.33",
                                "--f0-method", "rmvpe", "--export-format", "WAV", "--embedder-model", "contentvec"],
                               cwd=str(APPLIO_DIR), capture_output=True, timeout=1800)
        rc("copy", str(saida), f"{FILA_TR}/{pid}/saida")
        seg = int(time.time() - t0)
        _marcar(None, "t.json", {"fim": _agora(), "segundos": seg, "por": QUEM, "epocas": epocas},
                destino=f"{FILA_TR}/{pid}/pronto.json")
        print(f"[{_agora()}] treino {voz}: OK em {seg // 60} min", flush=True)
    except Exception as e:  # noqa: BLE001
        cauda = log.read_text(encoding="utf-8", errors="replace")[-1500:] if log.exists() else ""
        _marcar(None, "t.json", {"erro": f"{type(e).__name__}: {e}", "log": cauda, "por": QUEM},
                destino=f"{FILA_TR}/{pid}/erro.json")
        print(f"[{_agora()}] treino {voz}: ERRO {e}", flush=True)
    finally:
        try:
            rc("deletefile", f"{FILA_TR}/{pid}/em_andamento_{QUEM}.json")
        except RuntimeError:
            pass
        shutil.rmtree(local, ignore_errors=True)
        shutil.rmtree(APPLIO_DIR / "logs" / f"{voz}_v4", ignore_errors=True)


def lote_treino():
    """Pedidos de retreino livres (1 por vez; precisa do Applio)."""
    if not _APPLIO_OK:
        return
    try:
        pids = sorted(p.rstrip("/") for p in rc("lsf", FILA_TR, "--dirs-only").split())
    except RuntimeError:
        return
    # 10/11 dona ("assim que acabar o treinamento a produção deve estar logo atrás na fila"): no máximo TREINO_POR_VEZ
    # (1) treino por chamada — depois dele a conta volta ao loop e pega um trabalho de produção; o próximo treino fica pra
    # próxima volta. Treino e produção se alternam, ninguém fica horas só em treino.
    por_vez, feitos = int(os.environ.get("TREINO_POR_VEZ", "1")), 0
    for pid in pids:
        if feitos >= por_vez:
            return
        if time.time() - INICIO > SESSAO_MAX_S - 3 * 3600:  # treino leva ~1-2 h: não começa no fim da sessão
            return
        try:
            nomes = set(rc("lsf", f"{FILA_TR}/{pid}").split())
            if "voz.wav" in nomes and _livre(nomes):
                pegou = []  # fazer_treino não devolve nada: conta pela reserva (_pegar_tr), não pelo retorno

                def _um(p=pid):
                    if _pegar_tr(p):
                        pegou.append(p)
                        fazer_treino(p)
                _ocupado(_um)
                if pegou:
                    feitos += 1
        except Exception as e:  # noqa: BLE001
            print(f"[{_agora()}] treino {pid}: falhou ({type(e).__name__}: {str(e)[-200:]})", flush=True)


def _pegar_tr(pid):
    eu = {"desde": _agora(), "por": QUEM}
    _marcar(None, "t.json", eu, destino=f"{FILA_TR}/{pid}/em_andamento_{QUEM}.json")
    time.sleep(15)
    for n in rc("lsf", f"{FILA_TR}/{pid}").split():
        if n.startswith("em_andamento_") and n != f"em_andamento_{QUEM}.json":
            rc("deletefile", f"{FILA_TR}/{pid}/em_andamento_{QUEM}.json")
            return False
    return True


def _pegar_sh(pid):
    eu = {"desde": _agora(), "por": QUEM}
    _marcar(None, "s.json", eu, destino=f"{FILA_SH}/{pid}/em_andamento_{QUEM}.json")
    time.sleep(15)
    outros = [n for n in rc("lsf", f"{FILA_SH}/{pid}").split()
              if n.startswith("em_andamento_") and n != f"em_andamento_{QUEM}.json"]
    for n in outros:
        try:
            d = json.loads(rc("cat", f"{FILA_SH}/{pid}/{n}"))
            if (d.get("desde", ""), d.get("por", n)) < (eu["desde"], QUEM):
                rc("deletefile", f"{FILA_SH}/{pid}/em_andamento_{QUEM}.json")
                return False
        except (RuntimeError, ValueError):
            pass
    return True


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
    # 02/11: Shorts e comentários também (o TESTE_lote ficou preso 8 h com a marca de uma sessão morta minha)
    for fila in (FILA_SH, FILA_COM):
        try:
            for pid in rc("lsf", fila, "--dirs-only").split():
                pid = pid.rstrip("/")
                if f"em_andamento_{QUEM}.json" in rc("lsf", f"{fila}/{pid}").split():
                    rc("deletefile", f"{fila}/{pid}/em_andamento_{QUEM}.json")
                    print(f"[{_agora()}] {pid}: marca velha minha solta em {fila.rsplit('/', 1)[-1]}", flush=True)
        except RuntimeError:
            pass


def _comentarios_sempre():
    """Linha paralela: o longo leva horas e os Shorts de comentários não podem esperar ele acabar."""
    while time.time() - INICIO < LIMITE_S:
        lote_comentarios()
        lote_shorts()  # 02/11: Shorts de parceiros/cortes na mesma linha paralela
        time.sleep(300)


# 02/11 22h dona (divisão longo/curto): a central põe TRAB_PAPEL no topo do script. "longo" = só a fila do recap longo
# (sem a linha paralela de Shorts); "curto" = só Shorts de Cortes + Comédia, em lote, sai quando a fila esvazia.
# Sem papel (sessão antiga) = os dois, como era.
PAPEL = os.environ.get("TRAB_PAPEL", "")


def loop_curto():
    """Conta de papel "curto": Shorts e comentários um atrás do outro (usa as 2 T4: comentários na GPU 1 já pelo
    _gpu_paralela, Shorts idem); sai depois de OCIOSO_MAX_S sem nada (GPU parada gasta cota)."""
    while time.time() - INICIO < LIMITE_S:
        _marcar(None, f"vivo_{QUEM}.json", {"em": _agora(), "applio": _APPLIO_OK, "applio_msg": _APPLIO_MSG,
                                            "kokoro": os.environ.get("KOKORO_NUVEM") == "1", "papel": "curto"},
                destino=f"manhwa-drive:colab_recap/vivo_{QUEM}.json")
        antes = _TRAB["ultimo"]
        # 10/11 dona ("treino de voz precisa de alguns Kaggle de prioridade antes de continuar a produção"): treino
        # PRIMEIRO; sem treino na fila não muda nada (Shorts/comentários seguem). TREINO_PRIORIDADE=0 = como antes.
        if os.environ.get("TREINO_PRIORIDADE", "1") != "0":
            lote_treino()
        lote_comentarios()
        lote_shorts()
        if os.environ.get("TREINO_PRIORIDADE", "1") == "0":
            lote_treino()  # 06/11: retreino de voz (fila_treino) quando a fila de Shorts esvazia
        if _TRAB["ultimo"] == antes and time.time() - _TRAB["ultimo"] > OCIOSO_MAX_S:
            print(f"[{_agora()}] curto: fila de Shorts/comentários vazia há {OCIOSO_MAX_S / 60:.0f} min — saio", flush=True)
            break
        if _TRAB["ultimo"] == antes:
            time.sleep(60)
    print("curto: fim da sessão", flush=True)


USO_LOG = BASE / "uso.log"


def linha_uso():
    """04/11: a cada 60 s grava 'epoch hora cpu% load gpu0% enc0% mem0 gpu1% enc1% mem1' (medir o ganho dos 2 longos)."""
    ant = None
    while True:
        try:
            with open("/proc/stat") as f:
                v = [int(x) for x in f.readline().split()[1:]]
            ocioso, total = v[3] + v[4], sum(v)
            cpu = None
            if ant:
                dt = total - ant[1]
                cpu = round(100 * (1 - (ocioso - ant[0]) / dt)) if dt else 0
            ant = (ocioso, total)
            g = subprocess.run(["nvidia-smi", "--query-gpu=index,utilization.gpu,utilization.encoder,memory.used",
                                "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=20).stdout
            if not g.strip():
                g = subprocess.run(["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used",
                                    "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=20).stdout
            gpus = " ".join("/".join(x.strip() for x in l.split(",")[1:]) for l in g.strip().splitlines())
            if cpu is not None:
                with open(USO_LOG, "a", encoding="utf-8") as f:
                    f.write(f"{time.time():.0f} {_agora()[11:16]} cpu={cpu}% load={os.getloadavg()[0]:.1f} "
                            f"gpu={gpus} longos={_TRAB['ocupados']}\n")
        except Exception:  # noqa: BLE001
            pass
        time.sleep(60)


def _estimativa(pid):
    """Segundos do render inteiro deste pedido (mesma conta do _cabe)."""
    try:
        rot = rc("cat", f"{FILA}/{pid}/roteiro.txt")
        return (sum(1 for l in rot.splitlines() if l.strip()) + 20) * S_POR_FRASE
    except RuntimeError:
        return 7 * 3600


DOIS_LONGOS_TESTE = {"emerso", "emersonia"}  # 04/11: 1º só nestas (medir); depois em todas (TRAB_DOIS_LONGOS=1)


def _dois_longos():
    quer = os.environ.get("TRAB_DOIS_LONGOS", "")
    if quer == "0" or LIMITE_S == float("inf") or (quer != "1" and QUEM not in DOIS_LONGOS_TESTE):
        return False
    _gpu_paralela()  # preenche _GPUS
    return bool(_GPUS and _GPUS[0] >= 2)


# parte do longo ANTES da CPU (transcrição, roteiro, narradores, Edge, voz clonada) — medido 03/11 no waaQ: 1h25 de 5h18
PRE_FRACAO = 0.27


def loop_duplo():
    """04/11 dona ("se a CPU e a GPU rodarem sempre a 100% pode ser muito mais rápido"): 2 longos por sessão. O 1º, ao
    entrar na parte de CPU (marca _fase_cpu), libera o 2º, que faz o que é de rede/GPU na OUTRA T4 e espera a vez da
    CPU (anime_segments._vez_da_cpu). Só entra o 2º se ele terminar antes do Kaggle cortar: fim = max(agora + parte
    de antes, fim estimado do 1º) + parte de CPU. TRAB_DOIS_LONGOS=0 volta ao loop de 1 por vez."""
    ativos = {}
    print(f"[{_agora()}] 2 longos por sessão (CPU de um enquanto o outro narra na outra GPU)", flush=True)
    while True:
        _marcar(None, f"vivo_{QUEM}.json", {"em": _agora(), "applio": _APPLIO_OK, "applio_msg": _APPLIO_MSG,
                                            "kokoro": os.environ.get("KOKORO_NUVEM") == "1", "limite_h": _LIM_H,
                                            "longos": sorted(ativos)},
                destino=f"manhwa-drive:colab_recap/vivo_{QUEM}.json")
        # 10/11 dona: treino de voz antes do longo — só com a sessão livre (não briga com render em curso)
        if not ativos and os.environ.get("TREINO_PRIORIDADE", "1") != "0":
            lote_treino()
        for p in [p for p, a in ativos.items() if not a["th"].is_alive()]:
            print(f"[{_agora()}] {p}: terminou ({(time.time() - ativos[p]['t0']) / 3600:.1f} h)", flush=True)
            del ativos[p]
        pode = time.time() - INICIO < LIMITE_S
        vaga = pode and (not ativos or (len(ativos) == 1 and
                                        (next(iter(ativos.values()))["local"] / "_fase_cpu").exists()))
        if vaga:
            pid = proximo()
            if pid:
                est = _estimativa(pid)
                fim = time.time() + est
                if ativos:
                    a = next(iter(ativos.values()))
                    fim = max(time.time() + PRE_FRACAO * est, a["t0"] + a["est"]) + (1 - PRE_FRACAO) * est
                if fim - INICIO > SESSAO_MAX_S:
                    _soltar(pid)
                    _DEIXADOS.add(pid)
                    _TRAB["nao_coube"] = True
                    print(f"[{_agora()}] {pid}: não cabe no que resta da sessão/cota — fica pra outra conta", flush=True)
                    continue
                _TRAB["nao_coube"] = False
                usadas = {a["gpu"] for a in ativos.values()}
                gpu = 0 if 0 not in usadas else 1
                th = threading.Thread(target=_ocupado, args=(fazer, pid, gpu))
                ativos[pid] = {"th": th, "t0": time.time(), "est": est, "gpu": gpu, "local": TRABALHO / pid}
                th.start()
                continue
        if not ativos:
            if not pode:
                break
            if LIMITE_S != float("inf") and not _TRAB["ocupados"] and (
                    (_TRAB["nao_coube"] and time.time() - _TRAB["ultimo"] > 300)
                    or time.time() - _TRAB["ultimo"] > OCIOSO_MAX_S):
                print(f"[{_agora()}] " + ("o que sobrou na fila não cabe nesta sessão" if _TRAB["nao_coube"] else
                                          f"sem trabalho há {OCIOSO_MAX_S / 60:.0f} min") +
                      " — saio pra não gastar a cota de GPU", flush=True)
                break
        time.sleep(30)
    print("limite da sessão: saindo pro PC relançar", flush=True)


def loop():
    TRABALHO.mkdir(exist_ok=True)
    _TRAB["ultimo"] = time.time()  # a preparação (Applio/Kokoro) não conta como ociosa
    try:
        _soltar_os_meus()
    except RuntimeError as e:
        print(f"soltar marcas velhas falhou: {e}", flush=True)
    if PAPEL == "curto":
        return loop_curto()
    if PAPEL != "longo":  # sessão sem papel (antiga): mantém a linha paralela de antes
        threading.Thread(target=_comentarios_sempre, daemon=True).start()
    elif _dois_longos():
        return loop_duplo()
    while time.time() - INICIO < LIMITE_S:
        _marcar(None, f"vivo_{QUEM}.json", {"em": _agora(), "applio": _APPLIO_OK, "applio_msg": _APPLIO_MSG,
                                            "kokoro": os.environ.get("KOKORO_NUVEM") == "1", "limite_h": _LIM_H},
                destino=f"manhwa-drive:colab_recap/vivo_{QUEM}.json")
        if os.environ.get("TREINO_PRIORIDADE", "1") != "0":  # 10/11 dona: treino de voz antes do longo
            lote_treino()
        pid = proximo()
        if pid and not _cabe(pid):
            # 30/10 (Fable): o Pastor (984 frases) foi pego com 6,5 h de sessão e o Kaggle cortou em 12 h no acabamento
            # (01:15) — 7 h de render perdidas. Sem tempo pro pedido inteiro: solta. 02/11: em vez de sair, tenta o
            # próximo (um menor pode caber; conta de 6 h nunca caberia o grande) — o grande fica pra conta com mais cota
            _soltar(pid)
            _DEIXADOS.add(pid)
            _TRAB["nao_coube"] = True
            print(f"[{_agora()}] {pid}: não cabe no que resta da sessão/cota — fica pra outra conta", flush=True)
            continue
        if pid:
            _TRAB["nao_coube"] = False
            _ocupado(fazer, pid)
        elif LIMITE_S != float("inf") and not _TRAB["ocupados"] and (
                (_TRAB["nao_coube"] and time.time() - _TRAB["ultimo"] > 300)  # 5 min pra linha paralela pegar Shorts
                or time.time() - _TRAB["ultimo"] > OCIOSO_MAX_S):
            print(f"[{_agora()}] " + ("o que sobrou na fila não cabe nesta sessão" if _TRAB["nao_coube"] else
                                      f"sem trabalho há {OCIOSO_MAX_S / 60:.0f} min") +
                  " — saio pra não gastar a cota de GPU", flush=True)
            break
        else:
            time.sleep(60)
    print("limite da sessão: saindo pro PC relançar", flush=True)


SESSAO_MAX_S = float(os.environ.get("TRAB_SESSAO_MAX_H", "11.5")) * 3600  # Kaggle corta em 12 h
# 02/11: a central manda a cota de GPU livre da semana (conta nova tem 6 h, não 30). O Kaggle corta a sessão quando a
# cota acaba — então a sessão vale o menor dos dois, com 15 min de folga.
_COTA_H = float(os.environ.get("TRAB_COTA_H") or 0)
if _COTA_H > 0:
    SESSAO_MAX_S = min(SESSAO_MAX_S, _COTA_H * 3600 - 900)
    LIMITE_S = min(LIMITE_S, SESSAO_MAX_S)
S_POR_FRASE = float(os.environ.get("TRAB_S_POR_FRASE", "24"))  # medido 29/10: Top Fighter 894 frases em 4h44 (19 s) + folga
# 02/11: GPU parada também gasta a cota da semana. Sem longo, Short nem comentário por este tempo = sai (a central só
# relança quando aparece trabalho). Só no Kaggle (na VPS LIMITE_S é infinito).
OCIOSO_MAX_S = float(os.environ.get("TRAB_OCIOSO_MIN", "20")) * 60
_TRAB = {"ocupados": 0, "ultimo": time.time(), "nao_coube": False}
_TRAVA_TRAB = threading.Lock()  # longo e linha paralela mexem no contador ao mesmo tempo


def _ocupado(fn, *a):
    with _TRAVA_TRAB:
        _TRAB["ocupados"] += 1
    try:
        return fn(*a)
    finally:
        with _TRAVA_TRAB:
            _TRAB["ocupados"] -= 1
            _TRAB["ultimo"] = time.time()


def _cabe(pid):
    """O render deste pedido termina antes do Kaggle cortar a sessão? Estimativa pelo roteiro (frases × S_POR_FRASE);
    sem roteiro (o trabalhador transcreve) = o pior caso medido (7 h). Sem limite de sessão (VPS) = sempre cabe."""
    if LIMITE_S == float("inf"):
        return True
    try:
        rot = rc("cat", f"{FILA}/{pid}/roteiro.txt")
        est = (sum(1 for l in rot.splitlines() if l.strip()) + 20) * S_POR_FRASE
    except RuntimeError:
        est = 7 * 3600
    return time.time() - INICIO + est <= SESSAO_MAX_S


# ───────── BAIXADOR do YouTube em TODAS as sessões (04/11 dona: "se o gargalo é download, usa as 11 Kaggles pra baixar e
# põe no Drive; cada uma pega de um IP; junto com os longos sem atrapalhar"). Mesma fila do kaggle_baixador.py
# (manhwa-drive:baixador/pedidos -> prontos/<id>/ com ok.json por último) e mesmo formato do anime_fetch. Só rede e
# disco (yt-dlp + merge), 1 por vez — não disputa a GPU dos longos. Pegar = RENOMEAR o pedido para tomados/ (2 sessões
# não pegam o mesmo). IP desta sessão barrado ("Sign in to confirm", 429) = devolve o pedido pra outra sessão e fica
# 1 h sem baixar. Não conta como trabalho (não segura sessão ociosa gastando cota de GPU).
BX = "manhwa-drive:baixador"
_BX_TRAB = BASE / "baixador"


def _bx_baixar(p):
    vid, url, mh = p["id"], p["url"], int(p.get("max_height") or 720)
    d = _BX_TRAB / vid
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    t0 = time.time()
    fmt = f"bv*[aspect_ratio<0.9][width<={mh}]+ba/bv*[height<={mh}]+ba/b[height<={mh}]/b"
    r = subprocess.run([sys.executable, "-m", "yt_dlp", url, "-f", fmt, "-S", "res,vcodec:h264",
                        "--merge-output-format", "mp4", "-o", str(d / "source.%(ext)s"), "--no-warnings",
                        "--no-playlist"], capture_output=True, text=True, timeout=1800)
    video = next((f for f in d.glob("source.*") if f.suffix.lower() in (".mp4", ".mkv", ".webm")), None)
    if r.returncode != 0 or not video:
        txt = r.stdout + r.stderr
        linhas = [l for l in txt.splitlines() if "ERROR" in l] or txt.splitlines()[-1:]
        barrado = bool(re.search(r"Sign in to confirm|not a bot|HTTP Error (?:429|403)|Too Many Requests|Forbidden", txt))  # 04/11: o aviso fica no COMEÇO; o corte [-300:] escondia
        return {"erro": ("BARRADO: " if barrado else "") + " ".join(linhas)[:300]}
    for lang in p.get("legendas") or []:
        subprocess.run([sys.executable, "-m", "yt_dlp", url, "--skip-download", "--write-auto-subs", "--sub-langs", lang,
                        "--sub-format", "vtt", "-o", str(d / "cap"), "--no-warnings", "--no-playlist"],
                       capture_output=True, text=True, timeout=180)
        if any(d.glob(f"cap*.{lang}*.vtt")):
            break
    return {"video": video.name, "mb": round(video.stat().st_size / 1e6, 1), "s": round(time.time() - t0),
            "legendas": sorted(f.name for f in d.glob("cap*.vtt"))}


def linha_baixador():
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "yt-dlp"], check=True, timeout=600)
    except Exception as e:  # noqa: BLE001
        print(f"[baixador] yt-dlp não instalou ({e}) — sem baixador nesta sessão", flush=True)
        return
    barrado_ate = 0.0
    sinal = 0.0
    print(f"[{_agora()}] [baixador] linha no ar ({QUEM})", flush=True)
    while time.time() - INICIO < LIMITE_S:
        if time.time() - sinal > 120:  # 11 sessões no mesmo Drive: 1 sinal a cada 2 min (cota da API do Drive)
            sinal = time.time()
            try:
                _marcar(None, "bx.json", {"em": _agora(), "por": QUEM, "barrado": time.time() < barrado_ate},
                        destino=f"{BX}/vivos/{QUEM}.json")
                if time.time() >= barrado_ate:  # o PC só pede com o vivo.json fresco: quem pode baixar é que avisa
                    _marcar(None, "bx.json", {"em": _agora(), "desde": INICIO, "por": QUEM}, destino=f"{BX}/vivo.json")
            except Exception:  # noqa: BLE001
                pass
        if time.time() < barrado_ate:
            time.sleep(120)
            continue
        # 04/11 (claude-71, chat dos longos): o longo usa até ~20 GB no fim — com menos de 60 GB livres, não pega pedido
        if shutil.disk_usage(str(BASE)).free < 60e9:
            time.sleep(300)
            continue
        try:
            pedidos = sorted(l.strip() for l in rc("lsf", f"{BX}/pedidos", "--files-only").splitlines()
                             if l.strip().endswith(".json"))
        except Exception as e:  # noqa: BLE001
            # 403/limite de taxa do Drive: espera 10 min (não disputa a cota com o envio do longo)
            time.sleep(600 if any(s in str(e) for s in ("403", "ateLimit", "Quota")) else 60)
            continue
        if not pedidos:
            time.sleep(20)
            continue
        nome = pedidos[0]
        tomado = f"{BX}/tomados/{QUEM}_{nome}"
        try:
            rc("moveto", f"{BX}/pedidos/{nome}", tomado)  # outra sessão já pegou = falha aqui
            p = json.loads(rc("cat", tomado))
        except Exception:  # noqa: BLE001
            time.sleep(5)
            continue
        try:
            res = _bx_baixar(p)
        except Exception as e:  # noqa: BLE001
            res = {"erro": f"{type(e).__name__}: {str(e)[:250]}"}
        erro = str(res.get("erro") or "")
        if erro.startswith("BARRADO") or any(s in erro for s in ("Sign in to confirm", "not a bot", "429", "Too Many Requests", "403", "Forbidden")):
            barrado_ate = time.time() + 3600
            try:
                rc("moveto", tomado, f"{BX}/pedidos/{nome}")  # devolve: outra sessão (outro IP) baixa
            except Exception:  # noqa: BLE001
                pass
            shutil.rmtree(_BX_TRAB / p["id"], ignore_errors=True)
            print(f"[{_agora()}] [baixador] IP desta sessão barrado pelo YouTube — {p['id']} devolvido; 1 h sem baixar",
                  flush=True)
            continue
        res.update(id=p["id"], em=_agora(), por=QUEM)
        d = _BX_TRAB / p["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / ("erro.json" if erro else "ok.json")).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        try:  # arquivos primeiro, o marcador por último (o PC só pega com ok.json lá)
            for f in sorted(d.iterdir(), key=lambda x: x.name in ("ok.json", "erro.json")):
                rc("copyto", str(f), f"{BX}/prontos/{p['id']}/{f.name}")
            rc("deletefile", tomado)
        except Exception as e:  # noqa: BLE001
            print(f"[baixador] subir {p['id']}: {e}", flush=True)
            if any(s in str(e) for s in ("403", "ateLimit", "Quota")):
                time.sleep(600)  # limite de taxa do Drive: 10 min parado, o envio do longo vem primeiro
        shutil.rmtree(d, ignore_errors=True)
        print(f"[{_agora()}] [baixador] {p['id']}: {json.dumps(res, ensure_ascii=False)[:200]}", flush=True)


if __name__ == "__main__":
    preparar()
    threading.Thread(target=linha_uso, daemon=True).start()
    if os.environ.get("TRAB_BAIXADOR", "1") != "0":
        threading.Thread(target=linha_baixador, daemon=True).start()
    loop()
