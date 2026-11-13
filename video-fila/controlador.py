# -*- coding: utf-8 -*-
"""controlador.py — controlador GERAL dos projetos de vídeo (dono 19/10/2026: "deve ter um controlador geral").

Roda a cada 10 min (tarefa ControladorVideos, pythonw do D:\\veo\\venv). Em cada rodada vê o que já roda no PC1 (lista
de processos + trabalhos que ele mesmo disparou) e no PC2 (medidor comum), monta as necessidades em ordem de
prioridade e dispara no máximo 1 render no PC1, 1 trabalho de Flow, 1 limpeza do Drive e 1 trabalho no PC2:
  1 MS Energy (2/dia)   2 hipercool URGENTE (estoque <= 2)   3 Cortes (filas abaixo do alvo)
  4 hipercool capítulo novo (estoque < 5)   5 hipercool faltantes (PC1) e línguas (PC2)
  6 Veo (limpar brutos do Drive; gerar novo só com o Drive vazio)   7 enchimento (anime longo no PC2)

    python controlador.py               # 1 rodada real
    python controlador.py --simular     # mostra o que faria e por quê, sem disparar nem trazer nada do PC2

Liga/desliga: `python controle.py desligar controlador producao`. Dispara com os mesmos comandos das tarefas antigas
(rodar_oculto.vbs pros .bat, venv de cada projeto). Não marca nada no fila_render: os renders pedem a vez sozinhos.
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — 29/10 (dona): nenhum processo filho (yt-dlp, ssh, ffmpeg) abre janela
import json
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, date
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import controle  # noqa: E402
import maquinas  # noqa: E402
import fila_render  # noqa: E402

ESTADO = BASE / "estado" / "controlador.json"
LOG_DIR = BASE / "logs"
LOCK = BASE / "estado" / "controlador.lock"
EST_PC2_PARCEIRO = BASE / "estado" / "pc2_parceiro.json"

PY_POST = Path(r"D:\veo\venv\Scripts\python.exe")
PY_HIPER = Path(r"D:\hipercool-videos\venv\Scripts\python.exe")
PY_MR = Path(r"D:\manhwa-react\.venv\Scripts\python.exe")
VBS = Path(r"D:\rodar_oculto.vbs")
RECAPD = Path(r"D:\recapd-ambientes\producao")
HIPER = Path(r"D:\hipercool-videos")
MS_ENERGY = Path(r"D:\ms-energy")
VEO_BETA = Path(r"D:\veo\beta")
LIMPOS = Path(r"D:\hipercool-materiais\veo\limpos")
POSTADOR_LOGS = Path(r"D:\postador-de-videos\logs")
RCLONE = Path(r"D:\tools\rclone.exe")
DRIVE_BRUTOS = "manhwa-drive:videos-backup/veo/brutos_veo_videos_iniciais"

_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_FORA_DO_JOB = 0x01000000  # CREATE_BREAKAWAY_FROM_JOB
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

HIPER_ESTOQUE_MIN = 5
HIPER_ESTOQUE_URGENTE = 2
MSENERGY_POR_DIA = 2
RESERVA_DIAS = 7  # 02/11 dona: todo projeto guarda 1 semana de vídeos (doc: MELHORIAS_PARA_TODOS_OS_PROJETOS.md)
MSENERGY_TENTATIVAS_DIA = 3
VEO_TETO_DIA = 40
VEO_LIMPAR_LOTE = 5
VEO_LIMPAR_DIA = 150  # 23/10: eram 40 — 211 brutos nunca processados no Drive e o TikTok com 13 Veo sobrando
VEO_RESERVA_MIN = 100
VEO_RESERVA_MAX = 400
ESPERA_REPETIR_MIN = {"msenergy": 60}
MARCA_PC2_VELHA_H = 6

PESADOS_PC1 = ("parceiro_diario.py producao", "fila.py ciclo", "fila.py faltantes", "hiper-pipeline", "hiper-longo",
               "anime-pipeline.py", "manhwareact.py batch")
FLOW = ("gerar_short_veo.py", "cron_gerar_video_llm.py", "cron_gerar_ms_energy.bat", "sonda_contas_veo.py")
HIPER_PC1 = ("hiper-pipeline", "hiper-longo", "fila.py ciclo", "fila.py faltantes")
ROTULOS_PC1 = (("parceiro_diario.py producao", "Cortes: produção de Shorts"),
               ("parceiro_diario.py postar", "Cortes: postagem"),
               ("fila.py ciclo", "hipercool: capítulo novo"),
               ("fila.py faltantes", "hipercool: faltantes (correções, línguas, 16:9)"),
               ("gerar_short_veo.py", "MS Energy: gerando no Flow"),
               ("cron_gerar_video_llm.py", "Veo: gerando no Flow"),
               ("limpar_veo.py", "Veo: limpando brutos do Drive"),
               ("manhwareact.py batch", "ManhwaReact: lote de gravações"),
               ("youtube_web_poster.py", "subindo no YouTube"))
PAINEL_DE = {"cron_parceiro.bat producao": "parceiro_diario.py producao", "cron_gerar_ms_energy.bat": "gerar_short_veo.py"}


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_DIR / f"controlador_{datetime.now():%Y%m%d}.log", "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _ler_estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(d):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ESTADO)


def _pegar_lock():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            if time.time() - LOCK.stat().st_mtime < 600:
                return False
        except OSError:
            pass
    LOCK.write_text(str(os.getpid()))
    return True


# ─── o que roda no PC1 ───────────────────────────────────────────────────────

def _processos():
    """{pid: (minutos de vida, linha de comando)} dos python/wscript/cmd do PC1; {} se a consulta falhar."""
    # 02/11: com a CPU em 100% o WMI (WmiPrvSE com 90 min de CPU) fez o wmic passar de 30 s e TODAS as rodadas desde
    # 11:11 foram puladas. psutil lê direto do Windows, sem WMI (~1 s); wmic fica de reserva.
    # 03/11: o controlador ficou 1h40 parado (07:42→09:20) dentro do psutil: pedia a linha de comando de TODOS os
    # processos (Chrome, ffmpeg...) e um processo travado fazia o retry_error_partial_copy girar sem fim. Agora só lê a
    # linha dos python/wscript/cmd, e a consulta inteira tem 60 s; passou = wmic.
    import threading
    res = {}

    def _ler():
        import psutil
        out, agora = {}, time.time()
        for p in psutil.process_iter(["pid", "name"]):
            if (p.info["name"] or "").lower() in ("python.exe", "pythonw.exe", "wscript.exe", "cmd.exe"):
                try:
                    cmd = subprocess.list2cmdline(p.cmdline() or [])
                    out[p.info["pid"]] = (int((agora - p.create_time()) / 60), cmd)
                except (psutil.Error, OSError):
                    continue  # saiu no meio ou sem acesso
        res["out"] = out

    t = threading.Thread(target=_ler, daemon=True)
    t.start()
    t.join(180)  # 03/11 10h: com a CPU em 100% leva de 1 a 60+ s (pythonw 15,6 s às 10:25); 60 s pulava rodadas
    if res.get("out"):
        return res["out"]
    log("[!] psutil não respondeu em 180 s (ou falhou) — tentando wmic")
    try:
        # WMIC em vez de PowerShell (PowerShell intermitentemente trava 90s; WMIC é instantâneo)
        # 25/10: CreationDate removido — causava timeout/lista vazia intermitente (28 rodadas puladas hoje)
        r = subprocess.run(
            ["wmic", "process", "where",
             "name='python.exe' or name='pythonw.exe' or name='wscript.exe' or name='cmd.exe'",
             "get", "ProcessId,CommandLine", "/format:csv"],
            capture_output=True, text=True, timeout=90,
            encoding="utf-8", errors="replace", creationflags=_SEM_JANELA)
    except Exception as e:  # noqa: BLE001
        log(f"[!] lista de processos falhou: {e}")
        return {}
    out = {}
    # CSV do WMIC: Node,CommandLine,ProcessId (ProcessId na posição 2)
    for linha in (r.stdout or "").splitlines():
        if not linha.strip() or "Node,CommandLine" in linha:  # pula vazias e cabeçalho
            continue
        partes = linha.split(",", 2)  # split em até 3 partes (Node, CommandLine, ProcessId)
        if len(partes) == 3 and partes[2].strip().isdigit():
            pid = int(partes[2])
            cmd = partes[1].strip()  # CommandLine está na posição 1
            minutos = 0  # tempo de vida não é crítico (só exibição); CreationDate era instável
            out[pid] = (minutos, cmd)
    return out


def _achar(procs, marcas):
    return [(pid, m, cmd) for pid, (m, cmd) in procs.items() if any(x in cmd for x in marcas)]


def _detalhe(cmd):
    """Nome do vídeo numa linha de comando (--video / --video-source), pro painel."""
    m = re.search(r'--video(?:-source)?\s+(?:"([^"]+)"|(\S+))', cmd)
    if not m:
        return ""
    p = Path(m.group(1) or m.group(2))
    return p.parent.name if p.stem.lower() in ("video", "final") else p.stem


def _vivo(job, procs):
    p = procs.get(job.get("pid"))
    return bool(p) and job.get("marca", "") in p[1]


def _atualizar_jobs(est, procs):
    """Tira do estado os trabalhos disparados que terminaram e guarda quanto duraram (base da previsão do painel)."""
    jobs = est.setdefault("jobs", {})
    for nome, j in list(jobs.items()):
        if _vivo(j, procs):
            continue
        dur = round((time.time() - j.get("desde", time.time())) / 60)
        hist = est.setdefault("duracoes", {}).setdefault(nome, [])
        hist.append(dur)
        est["duracoes"][nome] = hist[-10:]
        log(f"  terminou: {j.get('rotulo', nome)} ({dur} min)")
        del jobs[nome]
    return jobs


# ─── medidores de necessidade ────────────────────────────────────────────────

def _estoque_msenergy():
    """Shorts do MS Energy ainda sem post no Instagram (chave do postagem_log.json = nome sem .mp4)."""
    try:
        postados = json.loads((MS_ENERGY / "videos" / "postagem_log.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        postados = {}
    return sum(1 for f in (MS_ENERGY / "videos" / "shorts_veo").glob("*.mp4")
               if "insta" not in (postados.get(f.stem) or {}))


def _msenergy_gerados_hoje():
    return sum(1 for _ in (MS_ENERGY / "videos" / "shorts_veo").glob(f"ms_energy_solar_{date.today():%Y%m%d}_*.mp4"))


def _hipercool():
    """(estoque pt = capítulos prontos com vídeo e Shorts pt não postados, [(língua no PC2, desde)] das marcas com
    menos de MARCA_PC2_VELHA_H, quantas marcas mais velhas — vídeo que o fila.py não conseguiu trazer, não render)."""
    try:
        est = json.loads((HIPER / "workspace" / "fila_estado.json").read_text(encoding="utf-8"))
        c = json.loads((HIPER / "config" / "fila.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, [], 0
    panels = Path(r"D:\hipercool-materiais\panels")
    estoque = 0
    for o in c.get("obras", []):
        for num in range(o.get("de", 1), o.get("ate", 0) + 1):
            pasta = next((p for p in (panels / f"{o['slug']}-cap{num:02d}", panels / f"{o['slug']}-cap{num}")
                          if p.is_dir()), None)
            e = est.get(pasta.name, {}) if pasta else {}
            if e.get("situacao") == "pronto" and e.get("video") and not e.get("pt_shorts_ok"):
                estoque += 1
    no_pc2, velhas = [], 0
    for k, e in est.items():
        for lang, li in ((e.get("idiomas") or {}).items() if isinstance(e, dict) else ()):
            if not (isinstance(li, dict) and li.get("pc2")):
                continue
            desde = li["pc2"].get("desde") if isinstance(li["pc2"], dict) else None
            try:
                idade_h = (datetime.now() - datetime.fromisoformat(desde)).total_seconds() / 3600
            except (TypeError, ValueError):
                idade_h = 0
            if idade_h > MARCA_PC2_VELHA_H or (isinstance(li["pc2"], dict) and li["pc2"].get("recuperado")):
                velhas += 1
            else:
                no_pc2.append((f"{k} {lang}", desde))
    return estoque, no_pc2, velhas


def _cortes_sem_fonte():
    """Motivo (str) quando a linha do parceiro NÃO TEM COMO produzir — IP pausado, estoque de fontes vazio e sem
    banda de emergência no proxy. '' = pode produzir (mesmo com o IP pausado: o estoque/emergência seguram).
    Dono 22/10: 'entende o máximo pra não ficar batendo e vai fazer outro projeto enquanto isso'."""
    try:
        if str(RECAPD / "bin") not in sys.path:
            sys.path.insert(0, str(RECAPD / "bin"))
        import anime_fetch
        import estoque_fontes
        import ytdlp_vez
        falta = ytdlp_vez.pausado()
        if not falta:
            return ""
        if estoque_fontes._entradas():
            return ""  # tem fonte baixada: produz mesmo com o IP pausado
        # 23/10: o anime_auto agora usa mesmo a emergência (antes encerrava a rodada e o controlador insistia a cada
        # 10 min sem sair nada); sem proxy na roda também não tem como
        if anime_fetch._banda_proxy_livre() > 25 and ytdlp_vez.proxy_url():
            return ""  # o download de emergência pelo proxy ainda tem banda
        return (f"IP pausado ({falta / 60:.0f} min), estoque vazio e "
                + ("banda de emergência do dia esgotada" if anime_fetch._banda_proxy_livre() <= 25 else "proxies fora da roda"))
    except Exception:  # noqa: BLE001 — na dúvida, produz (fail-open)
        return ""


def _cortes():
    """(canais pt ativos abaixo do alvo, quantos com a fila vazia)."""
    try:
        sys.path.insert(0, str(RECAPD / "bin"))
        import parceiro_diario as pdi
        c = pdi.cfg()
        fila = pdi._fila(pdi.itens(c))
        # 12/11: alvo DOBRADO pra quem rende (>= 300 views/48 h), igual ao parceiro_diario._alvo — com o alvo puro (21)
        # os 5 canais que mais rendem pareciam cheios e o controlador dizia "nada novo" com PC1/desktop livres
        try:
            rend = pdi._rendimento_canais() if os.environ.get("PARCEIRO_RESERVA_POR_RENDIMENTO", "1") != "0" else {}
        except Exception:  # noqa: BLE001
            rend = {}
        try:
            travados = pdi._canais_travados(c)
        except Exception:  # noqa: BLE001
            travados = set()
        pts = [d for d in c["pt"] if d.get("ativo", True) and d["canal"] not in travados]
        abaixo = [d for d in pts if fila[d["canal"]] < pdi.alvo_por_rendimento(d, rend, d.get("fila_alvo",
                                                                                               c.get("fila_alvo", 2)))]
        # 12/11 dona ("o Short nos dispositivos não pode parar; pode fazer os internacionais"): filas pt cheias mas
        # LÍNGUA abaixo do alvo = ainda há trabalho (o PC2/desktop faz o Short + as versões nas línguas — ocioso.
        # _escolher_pc2). Conta como 1 "abaixo" pra o controlador disparar. LINGUAS_QUANDO_CHEIO=0 desliga.
        if not abaixo and os.environ.get("LINGUAS_QUANDO_CHEIO", "1") != "0":
            ling = [d for d in (c.get("idiomas") or {}).values()
                    if d.get("ativo", True) and fila[d["canal"]] < d.get("fila_alvo", 2)]
            if ling:
                return 1, 0
        return len(abaixo), sum(1 for d in pts if fila[d["canal"]] == 0)
    except Exception as e:  # noqa: BLE001
        log(f"[!] fila do Cortes indisponível: {type(e).__name__}: {e}")
        return 0, 0


def _brutos_no_drive(est):
    """Brutos .mp4 no Drive (cache de 1 h). None = nunca conseguiu contar: aí não gera Veo novo."""
    cache = est.get("drive_brutos", {})
    if time.time() - cache.get("ts", 0) < 3600:
        return cache.get("n")
    n = cache.get("n")
    try:
        r = subprocess.run([str(RCLONE), "lsf", DRIVE_BRUTOS, "--include", "*.mp4"], capture_output=True, text=True,
                           timeout=120, encoding="utf-8", errors="replace", creationflags=_SEM_JANELA)
        if r.returncode == 0:
            # 23/10: só os AINDA NÃO processados (o limpar_veo pula quem tem .json em veo/limpos). Contava os 672 —
            # 461 já feitos — e o Veo "nunca tinha Drive vazio" pra gerar
            n = len([x for x in r.stdout.splitlines() if x.strip()
                     and not (LIMPOS / x.strip()).with_suffix(".json").exists()])
        else:
            log(f"[!] rclone falhou (fica o último número, {n}): {(r.stderr or '').strip()[-200:]}")
    except Exception as e:  # noqa: BLE001
        log(f"[!] rclone falhou (fica o último número, {n}): {e}")
    est["drive_brutos"] = {"n": n, "ts": time.time()}
    return n


def _reserva_veo():
    """Veo limpo ainda NÃO postado no TikTok (a saída que mais gasta: ~100/dia). 23/10 (dona: "verifique se tem mesmo
    504, porque posta mais de cem por dia no TikTok e aparece sem nos avisos"): contava todo .mp4 de veo/limpos, os já
    postados também — dava 504 com só 13 sobrando pro TikTok e o Veo nunca gerava. Lê o catálogo da última sincronia
    (rápido); sem catálogo, volta à contagem antiga."""
    try:
        bin_postador = r"D:\postador-de-videos\bin"
        if bin_postador not in sys.path:
            sys.path.insert(0, bin_postador)
        import catalogo
        cat = catalogo._ler(catalogo.CATALOGO, {})
        return sum(1 for v in cat.get("videos", []) if v.get("projeto") == "veo" and v.get("tipo") == "final"
                   and not any(p.get("plataforma") == "tiktok" for p in v.get("postagens") or [])
                   and catalogo.versao_limpa(v))
    except Exception as e:  # noqa: BLE001
        log(f"[!] reserva do Veo pelo catálogo falhou ({type(e).__name__}: {e}) — contando a pasta")
    try:
        return sum(1 for _ in LIMPOS.glob("*.mp4"))
    except OSError:
        return None


# ─── disparadores: devolvem (pid ou None, marca na linha de comando, rótulo) ou None se nada saiu ─────────────

def _lancar(cmd, cwd=None, log_path=None, env=None):
    fh = open(log_path, "a", encoding="utf-8") if log_path else subprocess.DEVNULL
    try:
        kw = dict(cwd=cwd, env=env or ENV, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT)
        try:  # fora do job da tarefa agendada quando o Windows deixa: o filho não depende da rodada que o disparou
            return subprocess.Popen(cmd, creationflags=_SEM_JANELA | _FORA_DO_JOB, **kw)
        except OSError:
            return subprocess.Popen(cmd, creationflags=_SEM_JANELA, **kw)
    finally:
        if log_path:
            fh.close()


def _msenergy(lote):
    p = _lancar(["wscript.exe", str(VBS), str(MS_ENERGY / "bin" / "cron_gerar_ms_energy.bat"), str(lote)],
                cwd=str(MS_ENERGY))
    return p.pid, "cron_gerar_ms_energy.bat", f"MS Energy: gerar {lote} no Flow"


def _cortes_pc1():
    p = _lancar(["wscript.exe", str(VBS), str(RECAPD / "cron_parceiro.bat"), "producao"])
    return p.pid, "cron_parceiro.bat producao", "Cortes: produção de Shorts no PC1"


def _porta_8772_pc2():
    """True se tem processo escutando na 8772 do PC2 (worker vivo, talvez ocupado). Na dúvida, False."""
    try:
        r = subprocess.run([maquinas.SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "pc2",
                            'powershell -NoProfile -c "(Get-NetTCPConnection -LocalPort 8772 -State Listen '
                            '-ErrorAction SilentlyContinue | Measure-Object).Count"'],
                           capture_output=True, text=True, timeout=40, creationflags=_SEM_JANELA)
        return any(l.strip().isdigit() and int(l.strip()) > 0 for l in (r.stdout or "").splitlines())
    except Exception:  # noqa: BLE001
        return False


def _reiniciar_anime_daemon_pc2():
    """Inicia o anime_worker_daemon no PC2 via SSH. Não falha se não conseguir.
    21/10: com Start-Process o worker morria junto com a sessão do ssh (o sshd fecha o "job" dela) e o anime longo
    não saía havia dias; pelo WMI (Win32_Process.Create) o processo nasce fora da sessão e fica no ar."""
    import base64
    ps = ("Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="
          "'C:\\recapd-e-animes\\venv\\Scripts\\pythonw.exe bin\\anime_worker_daemon.py --port 8772';"
          "CurrentDirectory='C:\\recapd-e-animes'} | Out-Null")
    enc = base64.b64encode(ps.encode("utf-16-le")).decode()
    try:
        subprocess.run([maquinas.SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "pc2",
                        "powershell -NoProfile -EncodedCommand " + enc],
                       capture_output=True, timeout=30, creationflags=_SEM_JANELA)
    except Exception:  # noqa: BLE001
        pass


def _cortes_pc2():
    import ocioso
    import pc2_recapd
    ocioso.log = log
    sinc, recado = pc2_recapd.sincronizar_bin()
    log(f"  PC2: {recado}")
    # 26/10: o PC2 ganhou a voz clonada (instalar_pc2_cortes.py; 1º Short com clone saiu 09:15) — volta a fazer Short
    if controle.ligado("parceiro", "producao")[0]:
        # 21/10: com a vaga do PC2 ocupada o vez() esperava até 15 min AQUI e segurava a rodada inteira (PC1 sem
        # trabalho, rodada seguinte pulada). Vaga ocupada = pula o Short nesta rodada e segue (anime longo, PC1).
        try:
            cfg_fr = fila_render._cfg()
            vagas = int((cfg_fr.get("slots_maquina") or {}).get("pc2", 1))
            ocupadas = len(fila_render._ler(fila_render._pastas("pc2")[0], cfg_fr.get("max_h", 6)))
        except Exception:  # noqa: BLE001
            vagas, ocupadas = 1, 0
        if ocupadas >= vagas:
            log(f"  PC2: vaga do Short ocupada ({ocupadas}/{vagas}) — pula o Short nesta rodada")
        else:
            with fila_render.vez("parceiro", "disparo de Short no PC2", espera_max_h=0.02, maquina="pc2"):
                vaga, motivo = ocioso.pc2_vaga_short()  # 27/10: até 3 Shorts juntos, com folga
                if not vaga:
                    log(f"  PC2: sem vaga pro Short — {motivo}")
                elif ocioso._disparar_parceiro_pc2():
                    # 30/10 (D39): o resto das vagas do PC2 é do alimentar_pc2.py (tarefa AlimentarPC2, 5 min), fora da
                    # rodada — escolher+baixar a fonte leva 10+ min e segurava a rodada inteira
                    return None, "", "Cortes: Short de parceiro no PC2"
    if not (sinc and controle.ligado("anime", "producao")[0]):
        return None
    # 27/10 (dona): "recap longo só nas GPUs; se usa a CPU do PC2 pra produzir está errado — o PC2 foca no máximo de
    # Shorts". O longo vai pelo cliente.py -> VPS -> Kaggle. O worker 8772 continua no ar (o Short usa outro caminho).
    ok_longo, motivo_longo = ocioso.longo_pc2_permitido()  # 30/10 (D39): longo só como reserva do PC2 parado
    if not ok_longo:
        log(f"  PC2: anime longo não roda no PC2 agora ({motivo_longo}) — PC2 fica pros Shorts")
        return None
    sys.path.insert(0, str(RECAPD / "bin"))
    import anime_worker_client
    if not anime_worker_client.is_online("100.125.7.77", 8772, timeout=10):
        # 21/10: o worker atende 1 pedido por vez; rodando um anime o /health não responde e o controlador abria outro
        # worker a cada rodada (ficaram 3 no PC2). Porta escutando = ocupado, não fora do ar.
        if _porta_8772_pc2():
            log("  PC2: worker do anime ocupado (rodando um anime longo) — nada pra disparar nele agora")
            return None
        log("  PC2: worker do anime (8772) fora do ar — tentando reiniciar...")
        _reiniciar_anime_daemon_pc2()
        time.sleep(5)
        if not anime_worker_client.is_online("100.125.7.77", 8772, timeout=10):
            log("  PC2: worker do anime não voltou — anime longo não sai")
            return None
        log("  PC2: worker do anime reiniciado com sucesso")
    if _fixos().get("anime_longo") == "pc1":
        log("  PC2: anime longo fixado no PC1 pelo dono (kanban) — não vai pro PC2")
        return None
    if ocioso.disparar_anime_longo():
        return None, "", "Cortes: anime longo no PC2"
    return None


def _anime_longo_pc1():
    """Anime longo renderizado AQUI (engine local) — só quando o dono fixa o anime longo no PC1 (kanban, 24/10)."""
    p = _lancar([str(RECAPD / "venv" / "Scripts" / "python.exe"), "-X", "utf8", str(RECAPD / "bin" / "anime_auto.py"),
                 "--modo", "deitado", "--engine", "local", "--limit", "1", "--top", "5"], cwd=str(RECAPD / "bin"),
                log_path=RECAPD / "logs" / f"anime_pc1_{datetime.now():%Y%m%d}.log", env=dict(ENV, ANIME_DESTINO="drive"))
    return p.pid, "--engine local", "Cortes: anime longo no PC1 (fixado pelo dono)"


def _cortes_desktop():
    # 12/11: o disparo do PC3 BAIXA a fonte aqui e esperava a vez do yt-dlp (até 30 min + espaçamento) DENTRO da rodada —
    # o controlador inteiro parava (rodadas 08:20 e 09:20 presas em ytdlp_vez.vez; painel "controlador parado"). Agora
    # vai num processo próprio (disparar_pc3.py, com trava); o job "cortes_desktop" impede outro enquanto ele vive.
    # CONTROLADOR_PC3_NA_RODADA=1 volta ao jeito antigo.
    if os.environ.get("CONTROLADOR_PC3_NA_RODADA") == "1":
        import transferencias
        try:
            return None, "", transferencias.disparar("cortes", "desktop")
        except RuntimeError as e:
            log(f"  PC3: {e}")
            return None
    p = _lancar([sys.executable, str(BASE / "disparar_pc3.py")], cwd=str(BASE),
                log_path=BASE / "logs" / "disparar_pc3.log")
    return p.pid, "disparar_pc3.py", "Cortes: Short no PC3 (escolhe, baixa e dispara em fundo)"


def _fixos():
    try:
        import transferencias
        return transferencias.ler()["fixos"]
    except Exception:  # noqa: BLE001
        return {}


def _fila_hiper_vazia():
    """True quando o último fila.py ciclo (últimas 3 h) terminou com "fila de capítulos terminada" (sem obra nova)."""
    f = HIPER / "logs" / "fila_ciclo.log"
    try:
        if time.time() - f.stat().st_mtime > 3 * 3600:
            return False
        with open(f, "rb") as fh:
            fh.seek(max(0, f.stat().st_size - 600))
            fim = fh.read().decode("utf-8", "replace").strip().splitlines()
    except OSError:
        return False
    if not fim or "fila de capítulos terminada" not in fim[-1]:
        return False
    try:
        import avisos
        avisos.enviar("hipercool: a fila de obras acabou (config/fila.json) — o Manhwa Noturno está com 0 capítulo de "
                      "estoque e nada novo é feito até entrar a próxima obra.", "controlador", importante=True,
                      chave="<SEGREDO_REMOVIDO>")
    except Exception:  # noqa: BLE001
        pass
    return True


def _hipercool_pc1(comando):
    p = _lancar([str(PY_HIPER), str(HIPER / "bin" / "fila.py"), comando], cwd=str(HIPER),
                log_path=HIPER / "logs" / f"fila_{comando}.log")
    rot = "hipercool: capítulo novo" if comando == "ciclo" else "hipercool: faltantes (correções, línguas, 16:9)"
    return p.pid, f"fila.py {comando}", rot


def _hipercool_pc2():
    p = _lancar([str(PY_HIPER), str(HIPER / "bin" / "fila.py"), "pc2"], cwd=str(HIPER),
                log_path=HIPER / "logs" / "fila_pc2.log")
    return p.pid, "fila.py pc2", "hipercool: próxima língua no PC2"


def _veo_tetos():
    """29/10 (D33, dona: "subir os tetos com monitor de banimento"): teto/dia e reserva mínima do Veo vêm da rampa
    (D:\\postador-de-videos\\config\\tetos.json, global.veo, mexida só por tools\\monitor_banimento.py do nsn).
    Sem o arquivo, valem as constantes de sempre."""
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import tetos
        return (int(tetos.teto("veo", None, padrao=VEO_TETO_DIA, chave="<SEGREDO_REMOVIDO>")),
                int(tetos.teto("veo", None, padrao=VEO_RESERVA_MIN, chave="<SEGREDO_REMOVIDO>")))
    except Exception:  # noqa: BLE001
        return VEO_TETO_DIA, VEO_RESERVA_MIN


def _veo_limpar():
    p = _lancar([str(PY_MR), str(Path(r"D:\postador-de-videos\bin\limpar_veo.py")), "--drive", "--max",
                 str(VEO_LIMPAR_LOTE)], log_path=POSTADOR_LOGS / f"limpar_veo_{datetime.now():%Y%m%d}.log")
    return p.pid, "limpar_veo.py", f"Veo: limpar {VEO_LIMPAR_LOTE} brutos do Drive"


def _veo_gerar():
    env = dict(ENV, FLOW_HEADLESS="1", FLOW_SESSION="seebotsia", FLOW_PROJ="https://labs.google/fx/pt/tools/flow",
               FLOW_ASPECT="9:16", FLOW_MODEL="Veo 3.1 - Fast", FLOW_DURATION="8S", FLOW_PORT="9250",
               FLOW_PROFILE="chrome_gen_seebotsia")
    cmd = (f'cmd.exe /d /s /c "call {VEO_BETA / "configurar_llm.bat"} >nul 2>&1 & '
           f'{PY_POST} -X utf8 -u cron_gerar_video_llm.py run"')
    p = _lancar(cmd, cwd=str(VEO_BETA), log_path=LOG_DIR / "controlador_veo_gerar.log", env=env)
    return p.pid, "cron_gerar_video_llm.py", "Veo: gerar 1 no Flow"


# ─── lógica central ──────────────────────────────────────────────────────────

def necessidades(est, estoque_hiper):
    """Em ordem de prioridade: dicts com nome, prio, pc, tipo (render|flow|leve|pc2), projeto, job, fn e info."""
    d = est.get("disparos_hoje", {})
    nec = []

    def add(nome, prio, pc, tipo, projeto, fn, info, job=None):
        nec.append(dict(nome=nome, prio=prio, pc=pc, tipo=tipo, projeto=projeto, fn=fn, info=info, job=job or nome))

    if controle.ligado("msenergy", "producao")[0]:
        feitos = _msenergy_gerados_hoje()
        # 02/11 dona: reserva de 1 SEMANA em todo projeto — abaixo de 7 dias de estoque gera o dobro por dia
        estoque_ms = _estoque_msenergy()
        meta_dia = MSENERGY_POR_DIA * (2 if estoque_ms < RESERVA_DIAS * MSENERGY_POR_DIA else 1)
        if feitos < meta_dia and d.get("msenergy", 0) < MSENERGY_TENTATIVAS_DIA * (meta_dia // MSENERGY_POR_DIA):
            add("msenergy", 1, "pc1", "flow", "msenergy", lambda: _msenergy(meta_dia - feitos),
                f"gerados hoje {feitos}/{meta_dia}, {estoque_ms} sem post no Insta "
                f"(reserva meta {RESERVA_DIAS * MSENERGY_POR_DIA})")

    hiper_ok = controle.ligado("hipercool", "producao")[0] and estoque_hiper is not None
    # 04/11 (vigilância da madrugada): a fila de obras do hipercool acabou ("fila de capítulos terminada — adicione a
    # próxima obra em config/fila.json", desde 03/11) e o "capítulo novo URGENTE" (prioridade 2, acima dos Cortes) era
    # disparado a cada 10 min, rodava 8-9 min sem fazer nada e tirava a vez do PC1 dos Shorts. Fila vazia = não dispara
    # capítulo novo (faltantes/línguas seguem) e avisa a dona 1x a cada 12 h.
    fila_hiper_vazia = _fila_hiper_vazia()
    if hiper_ok and fila_hiper_vazia:
        log("  hipercool: fila de obras vazia (config/fila.json) — capítulo novo não dispara; adicione a próxima obra")
    if hiper_ok and estoque_hiper <= HIPER_ESTOQUE_URGENTE and not fila_hiper_vazia:
        add("hipercool_capitulo", 2, "pc1", "render", "hipercool", lambda: _hipercool_pc1("ciclo"),
            f"URGENTE: Manhwa Noturno com {estoque_hiper} capítulo(s) de estoque", "hipercool_pc1")

    abaixo, vazios = _cortes()
    if abaixo:
        info = f"{abaixo} canal(is) abaixo do alvo, {vazios} com a fila vazia"
        sem_fonte = _cortes_sem_fonte()
        if sem_fonte:
            # 22/10 (dono: "não fica batendo; vai fazer outro projeto e volta quando der"): sem fonte possível,
            # os cortes CEDEM a vez desta rodada — o laço de prioridade segue pro hipercool/veo normalmente.
            log(f"  cortes: {sem_fonte} — vez cedida ao próximo projeto (balancer)")
        else:
            if controle.ligado("parceiro", "producao")[0]:
                add("cortes_pc1", 3, "pc1", "render", "cortes", _cortes_pc1, info)
            add("cortes_pc2", 3, "pc2", "pc2", "cortes", _cortes_pc2, info)
            if controle.ligado("parceiro", "producao")[0]:
                # 27/10 (dona: "o desktop, se a câmera não estiver ligada, pode usar à vontade"): Short automático lá
                # também (antes só fixando no kanban) — só com ele LIVRE (sem OBS/câmera/microfone)
                add("cortes_desktop_auto", 3, "desktop", "desktop", "cortes", _cortes_desktop, info, job="cortes_desktop")

    if hiper_ok and HIPER_ESTOQUE_URGENTE < estoque_hiper < HIPER_ESTOQUE_MIN and not fila_hiper_vazia:
        add("hipercool_capitulo", 4, "pc1", "render", "hipercool", lambda: _hipercool_pc1("ciclo"),
            f"estoque {estoque_hiper} (< {HIPER_ESTOQUE_MIN})", "hipercool_pc1")
    if hiper_ok:
        add("hipercool_faltantes", 5, "pc1", "render", "hipercool", lambda: _hipercool_pc1("faltantes"),
            f"estoque {estoque_hiper}: correções, línguas e 16:9 dos capítulos feitos", "hipercool_pc1")
        if estoque_hiper > HIPER_ESTOQUE_URGENTE:
            add("hipercool_pc2", 5, "pc2", "pc2", "hipercool", _hipercool_pc2, "línguas do hipercool no PC2")

    reserva, brutos = _reserva_veo(), _brutos_no_drive(est)
    VEO_TETO_DIA, VEO_RESERVA_MIN = _veo_tetos()  # 29/10 (D33): rampa em postador config\tetos.json
    if reserva is not None:
        # 23/10 (dona: prioridade 2 é o Veo3): limpar e gerar NÃO são mais "um ou outro" — limpar é CPU ("leve"),
        # gerar é Flow ("flow"); rodam juntos. Gerar não espera mais o Drive zerar: os brutos antigos rendem pouco
        # (marca do Grok) e o TikTok gasta ~100/dia.
        if brutos and reserva < VEO_RESERVA_MAX and d.get("veo_limpar", 0) * VEO_LIMPAR_LOTE < VEO_LIMPAR_DIA:
            add("veo_limpar", 6, "pc1", "leve", "veo", _veo_limpar,
                f"{reserva} Veo pro TikTok (< {VEO_RESERVA_MAX}), {brutos} bruto(s) ainda não processado(s) no Drive")
        if (reserva < VEO_RESERVA_MIN and d.get("veo_gerar", 0) < VEO_TETO_DIA
                and controle.ligado("veo", "producao")[0]):
            add("veo_gerar", 6, "pc1", "flow", "veo", _veo_gerar,
                f"só {reserva} Veo pro TikTok (< {VEO_RESERVA_MIN}), gerados hoje {d.get('veo_gerar', 0)}/{VEO_TETO_DIA}")

    if not abaixo:
        add("anime_longo_pc2", 7, "pc2", "pc2", "cortes", _cortes_pc2, "enchimento: filas do Cortes cheias")
    return _aplicar_fixos(nec)


def _aplicar_fixos(nec):
    """Tarefa que o dono arrastou pra outro PC no kanban (transferencias.py) fica lá até ele soltar.
    Hipercool fixo no PC2 ainda deixa o capítulo URGENTE no PC1 (nenhum canal sem postagem)."""
    fx = _fixos()
    out = []
    for n in nec:
        if fx.get("cortes") == "desktop" and n["nome"] == "cortes_pc1":
            n = dict(n, nome="cortes_desktop", pc="desktop", tipo="desktop", fn=_cortes_desktop, job="cortes_desktop",
                     info=n["info"] + " (fixado no PC3 pelo dono)")
        elif fx.get("hipercool") == "pc2" and n["projeto"] == "hipercool" and n["pc"] == "pc1" and n["prio"] != 2:
            continue
        elif fx.get("hipercool") == "pc1" and n["nome"] == "hipercool_pc2":
            continue
        elif fx.get("anime_longo") == "pc1" and n["nome"] == "anime_longo_pc2":
            n = dict(n, nome="anime_longo_pc1", pc="pc1", tipo="render", fn=_anime_longo_pc1, job="anime_longo_pc1",
                     info=n["info"] + " (fixado no PC1 pelo dono)")
        out.append(n)
    return out


def _bloqueio(n, jobs, ocup, hiper_em, medidas, est):
    """Motivo pra NÃO disparar agora (texto) ou "" se pode."""
    if n["job"] in jobs:
        return f"já rodando (pid {jobs[n['job']]['pid']})"
    espera = ESPERA_REPETIR_MIN.get(n["nome"])
    if espera and time.time() - (est.get("ultimo_disparo") or {}).get(n["nome"], 0) < espera * 60:
        return f"disparado há menos de {espera} min"
    if n["nome"] == "cortes_pc2":
        # 27/10 (dona: PC2 no máximo de Shorts): o Short tem regra própria (ocioso.pc2_vaga_short: até 3 juntos, com
        # folga de CPU/RAM/disco) — outro trabalho rodando lá ou um Short em andamento não barra o próximo
        if ocup["pc2"] and ocup["pc2"].startswith("outro despacho"):
            return ocup["pc2"]
        ok, motivo = __import__("ocioso").pc2_vaga_short()
        return "" if ok else motivo
    if n["tipo"] == "pc2":
        if ocup["pc2"]:
            return ocup["pc2"]
    elif n["tipo"] == "desktop":
        # fixado no PC3 pelo dono: passa por cima de OBS/chamada (24/10), mas não com o PC3 fora do ar ou já rodando
        md = medidas.get("desktop") or {}
        if md.get("cpu") is None:
            return f"PC3 sem resposta ({md.get('motivo')})"
        if (BASE / "estado" / "pc3_parceiro.json").exists():
            return "PC3 ainda fazendo o Short anterior"
        if n["nome"] == "cortes_desktop_auto" and not md.get("ocioso"):
            return f"desktop em uso ({md.get('motivo')})"  # automático respeita câmera/OBS; o fixado no kanban não
    elif n["tipo"] == "render":
        if ocup["render"]:
            return ocup["render"]
        if not medidas["pc1"].get("ocioso"):
            return f"PC1 ocupado ({medidas['pc1'].get('motivo')})"
    elif ocup[n["tipo"]]:
        return ocup[n["tipo"]]
    outro = "pc2" if n["pc"] == "pc1" else "pc1"
    if n["projeto"] == "hipercool" and hiper_em[outro]:
        return f"hipercool já está no {outro.upper()} ({hiper_em[outro]}) — um projeto não usa os 2 PCs"
    return ""


def _agora(procs, jobs, rod_pc1, hiper_pc2, est):
    """O que cada PC está fazendo: {"pc1": [{"o_que", "min", "eta_min"}], "pc2": [...]}."""
    pc1, pc2, cobertos = [], [], set()
    for nome, j in jobs.items():
        if j["pc"] != "pc1":
            continue
        minutos = round((time.time() - j["desde"]) / 60)
        hist = (est.get("duracoes") or {}).get(nome) or []
        eta = max(0, round(statistics.median(hist)) - minutos) if hist else None
        pc1.append({"o_que": j["rotulo"], "min": minutos, "eta_min": eta})
        cobertos.add(j.get("painel", ""))
    for _p, d in rod_pc1:
        pc1.append({"o_que": f"render {d['projeto']}: {d.get('rotulo', '')}", "min": round((time.time() - d["desde"]) / 60)})
    for marca, rotulo in ROTULOS_PC1:
        achados = _achar(procs, (marca,))
        if not achados or marca in cobertos:
            continue
        detalhes = sorted({_detalhe(cmd) for _pid, _m, cmd in achados} - {""})
        pc1.append({"o_que": rotulo + (f": {', '.join(detalhes)}" if detalhes else ""),
                    "min": max(m for _pid, m, _c in achados)})
    for texto, desde in hiper_pc2:
        minutos = round((datetime.now() - datetime.fromisoformat(desde)).total_seconds() / 60) if desde else None
        pc2.append({"o_que": f"hipercool língua: {texto}", "min": minutos})
    import ocioso  # 27/10: vários Shorts ao mesmo tempo no PC2 (1 arquivo por Short)
    for _arq, p in ocioso._pc2_estados():
        try:
            minutos = round((datetime.now() - datetime.fromisoformat(p["inicio"])).total_seconds() / 60)
            pc2.append({"o_que": f"Cortes: Short {p.get('id')} pra {p.get('destino')} — {p.get('titulo', '')[:60]}",
                        "min": minutos})
        except (ValueError, KeyError):
            pass
    for _p, d in fila_render._ler("rodando_pc2", fila_render._cfg().get("max_h", 6)):
        pc2.append({"o_que": f"{d['projeto']}: {d.get('rotulo', '')}", "min": round((time.time() - d["desde"]) / 60)})
    return {"pc1": pc1, "pc2": pc2}


def rodada(simular=False):
    ok, motivo = controle.ligado("controlador", "producao")
    if not ok:
        log(f"desligado: {motivo}")
        return
    est = _ler_estado()
    if not simular:  # 06/11: batimento no INÍCIO — a rodada que espera o ssh do PC2 fora do ar passava de 25 min e o
        _gravar({**est, "inicio_rodada": datetime.now().isoformat(timespec="seconds")})  # painel acusava "parado"
    hoje = date.today().isoformat()
    if est.get("dia") != hoje:
        est.update(dia=hoje, disparos_hoje={})
    procs = _processos()
    if not procs:
        log("[!] sem a lista de processos do PC1 não dá pra saber o que já roda — rodada pulada")
        return
    if simular:
        jobs = {k: j for k, j in (est.get("jobs") or {}).items() if _vivo(j, procs)}
    else:
        jobs = _atualizar_jobs(est, procs)
    medidas = {h: maquinas.medir(h) for h in ("pc1", "pc2")}
    try:
        medidas["desktop"] = maquinas.medir("desktop")
    except Exception:  # noqa: BLE001 — desktop offline não impede a rodada
        medidas["desktop"] = {"host": "desktop", "ocioso": False, "motivo": "offline"}
    medidas["x200ma"] = maquinas.medir("x200ma")  # só visualizador: aparece no painel, nunca recebe trabalho
    medidas["acer"] = maquinas.medir("acer")  # 24/10: telão + Flow do Veo (cadeia_veo); render nunca
    medidas["kaggle"] = maquinas.medir("kaggle")  # GPU só de voz clonada (gpu_fila): aparece, nunca recebe render
    medidas["colab"] = maquinas.medir("colab")  # 24/10: contas da Colab; só quem pede pelo nome
    for cel in ("s20ultra", "s20"):  # 04/11: Galaxy S20 — recebem o FFmpeg do junta-trechos (celulares.py), não disparos
        medidas[cel] = maquinas.medir(cel)
    log(" | ".join(f"{h}: {'LIVRE' if m.get('ocioso') else 'ocupado'} ({m.get('motivo')})" for h, m in medidas.items()))

    if (BASE / "estado" / "pc3_parceiro.json").exists() and not simular:  # 24/10: Short feito no PC3 volta pra cá
        try:
            import ocioso
            ocioso.log = log
            ocioso.buscar_parceiro_pc3()
        except Exception as e:  # noqa: BLE001
            log(f"[!] trazer o Short do PC3: {type(e).__name__}: {e}")
    import ocioso
    parceiro_pc2 = len(ocioso._pc2_estados())  # 27/10: quantos Shorts rodando no PC2 (até ocioso.PC2_SHORTS_MAX)
    if parceiro_pc2 and not simular:
        try:
            import ocioso
            ocioso.log = log
            parceiro_pc2 = ocioso._buscar_parceiro_pc2()
        except Exception as e:  # noqa: BLE001
            log(f"[!] trazer o Short do PC2: {type(e).__name__}: {e}")

    rod_pc1 = fila_render._ler("rodando", fila_render._cfg().get("max_h", 6))
    # quem dispara pro PC2 segura a vez dele enquanto mede/copia/dispara (minutos); esperar ali travava a rodada 15 min
    despacho_pc2 = [d["projeto"] for _p, d in fila_render._ler("rodando_pc2", fila_render._cfg().get("max_h", 6))
                    if d.get("rotulo", "").startswith("disparo") and d.get("pid") != os.getpid()]
    estoque_hiper, hiper_pc2, hiper_pc2_velhas = _hipercool()
    if hiper_pc2_velhas != est.get("hiper_pc2_velhas"):
        log(f"[!] hipercool: {hiper_pc2_velhas} língua(s) marcadas no PC2 há mais de {MARCA_PC2_VELHA_H} h sem vídeo "
            "trazido — marca velha, não conta como render no PC2")
    est["hiper_pc2_velhas"] = hiper_pc2_velhas
    pesados = {m for m in PESADOS_PC1 if _achar(procs, (m,))}

    def job_de(tipo):
        return next((j["rotulo"] for j in jobs.values() if j["tipo"] == tipo and j["pc"] == "pc1"), "")

    ocup = {
        "render": ("PC1 já renderizando: " + ", ".join(sorted(pesados))) if pesados else job_de("render"),
        "flow": "Flow em uso: " + ", ".join(m for m in FLOW if _achar(procs, (m,))) if _achar(procs, FLOW) else job_de("flow"),
        "leve": "limpeza do Drive já rodando" if _achar(procs, ("limpar_veo.py",)) else job_de("leve"),
        "pc2": (f"outro despacho pro PC2 em andamento ({', '.join(despacho_pc2)})" if despacho_pc2 else
                "" if medidas["pc2"].get("ocioso") and not parceiro_pc2 else
                f"PC2 ocupado ({'Short de parceiro em andamento' if parceiro_pc2 else medidas['pc2'].get('motivo')})"),
    }
    hipercool_pc1 = [m for m in HIPER_PC1 if _achar(procs, (m,))]
    hipercool_pc1 += [d.get("rotulo", "fila_render") for _p, d in rod_pc1 if d.get("projeto") == "hipercool"]
    hiper_em = {"pc1": ", ".join(hipercool_pc1), "pc2": ", ".join(t for t, _d in hiper_pc2)}

    necs = necessidades(est, estoque_hiper)
    if simular:
        log("=== SIMULAÇÃO (nada é disparado) ===")
    disparados = []
    for n in necs:
        motivo = _bloqueio(n, jobs, ocup, hiper_em, medidas, est)
        if motivo:
            if simular:
                log(f"  [{n['prio']}] {n['nome']:20} {n['pc']}: não — {motivo} | {n['info']}")
            continue
        if simular:
            log(f"  [{n['prio']}] {n['nome']:20} {n['pc']}: DISPARARIA | {n['info']}")
            res = (None, "", n["nome"])
        else:
            try:
                res = n["fn"]()
            except Exception as e:  # noqa: BLE001
                log(f"[!] {n['nome']}: falhou ao disparar ({type(e).__name__}: {e})")
                continue
            if not res:
                log(f"  {n['pc']}: {n['nome']} — nada pra disparar agora")
                continue
        pid, marca, rotulo = res
        ocup[n["tipo"]] = rotulo
        if n["projeto"] == "hipercool":
            hiper_em[n["pc"]] = rotulo
        if simular:
            continue
        est["disparos_hoje"][n["nome"]] = est["disparos_hoje"].get(n["nome"], 0) + 1
        est.setdefault("ultimo_disparo", {})[n["nome"]] = time.time()
        if pid:
            jobs[n["job"]] = {"pid": pid, "pc": n["pc"], "tipo": n["tipo"], "projeto": n["projeto"], "marca": marca,
                              "painel": PAINEL_DE.get(marca, marca), "rotulo": rotulo, "desde": time.time()}
        disparados.append(f"{n['pc']}: {rotulo}")
        log(f"  DISPAROU {n['pc']}: {rotulo} — {n['info']}" + (f" (pid {pid})" if pid else ""))

    agora = _agora(procs, jobs, rod_pc1, hiper_pc2, est)
    agora["desktop"] = []
    try:
        p3 = json.loads((BASE / "estado" / "pc3_parceiro.json").read_text(encoding="utf-8"))
        agora["desktop"].append({"o_que": f"Cortes: Short {p3.get('id')} pra {p3.get('destino')} — {p3.get('titulo', '')[:60]}",
                                 "min": round((datetime.now() - datetime.fromisoformat(p3["inicio"])).total_seconds() / 60)})
    except (OSError, ValueError, KeyError):
        pass
    resumo = {pc: "; ".join(x["o_que"] for x in agora[pc])[:300] or "livre" for pc in ("pc1", "pc2")}
    desk_m = medidas.get("desktop", {})
    resumo["desktop"] = desk_m.get("motivo", "offline")
    if simular:
        log(f"  agora PC1: {resumo['pc1']}")
        log(f"  agora PC2: {resumo['pc2']}")
        log(f"  desktop: {'LIVRE' if desk_m.get('ocioso') else 'ocupado'} ({resumo['desktop']})")
        log(f"  estoque hipercool pt: {estoque_hiper} | MS Energy sem post no Insta: {_estoque_msenergy()} "
            f"(gerados hoje {_msenergy_gerados_hoje()}) | reserva Veo: {_reserva_veo()} | "
            f"brutos no Drive: {est.get('drive_brutos', {}).get('n')}")
        log("  liga/desliga produção: " + ", ".join(f"{p}={'on' if controle.ligado(p, 'producao')[0] else 'OFF'}"
                                                     for p in ("msenergy", "parceiro", "anime", "hipercool", "veo")))
        _gravar({**_ler_estado(), "drive_brutos": est.get("drive_brutos", {})})
        return
    if not disparados:
        log("  nada novo (ocupado ou sem necessidade)")
    est.update(ultima_rodada=datetime.now().isoformat(timespec="seconds"), jobs=jobs, agora=agora,
               pc1=resumo["pc1"], pc2=resumo["pc2"], desktop=resumo["desktop"],
               medidas={h: {**{k: m.get(k) for k in ("ocioso", "motivo", "cpu", "ram_gb", "disco_gb", "renders")},
                            **{k: m[k] for k in ("gpu", "colab", "lotes", "fila", "gpu_h", "contas", "vez", "central", "webshare",
                                             "celular", "bateria", "tomada", "temp")
                               if k in m}}  # kaggle: GPU (+ central das GPUs do recap/Shorts, 02/11)
                        for h, m in medidas.items()},
               necessidades=[{k: n[k] for k in ("nome", "prio", "pc", "tipo", "info")} for n in necs],
               estoques={"hipercool_pt": estoque_hiper, "msenergy_insta": _estoque_msenergy(),
                         "msenergy_hoje": _msenergy_gerados_hoje(), "veo_reserva": _reserva_veo(),
                         # 12/11: a meta real (dobra com reserva < 7 dias) — o painel mostrava "/2" fixo
                         "msenergy_meta": MSENERGY_POR_DIA * (2 if _estoque_msenergy() < RESERVA_DIAS * MSENERGY_POR_DIA else 1)},
               historico=((est.get("historico") or []) + [f"{datetime.now():%d/%m %H:%M} {x}" for x in disparados])[-50:])
    _gravar(est)


def status_txt():
    """Seção Controlador pro status_videos.py."""
    est = _ler_estado()
    linhas = [f"última rodada: {est.get('ultima_rodada', 'nunca')}"]
    for pc in ("pc1", "pc2"):
        itens = (est.get("agora") or {}).get(pc) or []
        linhas.append(f"{pc.upper()}: " + ("; ".join(f"{x['o_que']} ({x.get('min')} min)" for x in itens) or "livre"))
    desk = (est.get("medidas") or {}).get("desktop", {})
    linhas.append(f"DESKTOP: {'LIVRE' if desk.get('ocioso') else 'ocupado'} ({desk.get('motivo', 'sem dados')})")
    for n in est.get("necessidades", []):
        linhas.append(f"  [{n['prio']}] {n['nome']} ({n['pc']}): {n['info']}")
    d = est.get("disparos_hoje", {})
    if d:
        linhas.append("disparos hoje: " + ", ".join(f"{k}={v}" for k, v in d.items()))
    return "\n".join(linhas)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()
    if not _pegar_lock():
        log("outra rodada ainda está rodando — pulando")
        return
    try:
        rodada(simular=a.simular)
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
