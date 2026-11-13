"""maquinas.py — medidor de ociosidade dos 3 PCs (+ x200ma, Linux, só visualizador: aparece mas nunca fica "livre") (dono 17/10/2026: "a ociosidade tem que ser medida nos 3, o desktop
também pode ajudar, mas só se não estiver rodando OBS nem nenhum vibe code, porque eu gravo nele").

  PC1  (este, local)        : ocupado se a fila de render (D:\\video-fila) tem alguém RODANDO ou CPU/RAM no limite
  PC2  (ssh pc2)            : ocupado se há render do hipercool/anime lá ou CPU/RAM/disco no limite
  DESK (ssh desktop)        : ocupado SÓ se o OBS estiver aberto ou houver CHAMADA (microfone/câmera em uso: Meet,
                              Zoom...) — regra reduzida pelo dono em 22/10 — ou CPU/RAM no limite. Só tarefa leve
                              (i5, sem GPU). Acesso: Windows SEM SENHA desde 24/10 -> só chave (BatchMode).
                              Dona 28/10: é a máquina MAIS LIVRE; câmera fixa ter e qui 10-12 h, sex 16-18 h
                              (AGENDA_CAMERA); fora disso muito raramente ocupada.
    python maquinas.py      # mede os 3 e imprime
"""
import base64
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# 18/10 (unificação): medidor ÚNICO dos 3 PCs — pc2_recapd.medir e hipercool-materiais\bin\ociosidade.py usam este.
# ssh do Git: o do Windows (System32\OpenSSH) trava depois de autenticar (17/10); tarefa agendada pode pegar ele no PATH.
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe" if Path(r"C:\Program Files\Git\usr\bin\ssh.exe").exists() else "ssh"

PS_MEDIR = (
    "$c = (1..3 | ForEach-Object { (Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average;"
    " Start-Sleep 3 } | Measure-Object -Average).Average;"
    "$r = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1);"
    "$d = [math]::Round(((Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Free -and (-not '__DRIVE__' -or $_.Name -eq '__DRIVE__') } | Measure-Object Free -Maximum).Maximum)/1GB,1);"
    # 1 trabalho = o processo raiz (o lançador do venv e os filhos têm a mesma marca); raiz com mais de __MAXH__ h = travado
    "$rp = @(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match "
    # 03/11: Short EXTRA do Kaggle (-X abastecedor_kaggle) só prepara aqui e espera o Kaggle: não ocupa a máquina
    "'hiper-pipeline|hiper-longo|anime-pipeline|anime_auto' -and $_.CommandLine -notmatch 'abastecedor_kaggle' });"
    " $ids = @($rp | ForEach-Object { $_.ProcessId });"
    "$raiz = @($rp | Where-Object { $ids -notcontains $_.ParentProcessId });"
    "$p = @($raiz | Where-Object { ((Get-Date) - $_.CreationDate).TotalHours -lt __MAXH__ }).Count;"
    "$t = $raiz.Count - $p;"
    # 22/10 (dono): o desktop só fica ocupado por OBS ou CHAMADA (Meet etc.). Chamada = microfone/câmera EM USO agora,
    # lido do registro do Windows (CapabilityAccessManager: LastUsedTimeStop = 0 enquanto o app usa) — vale pra
    # Meet no Chrome, Zoom, Teams... sem precisar ver a janela (via ssh não há tela).
    "$u = @(Get-Process | Where-Object { $_.ProcessName -match '^(obs64|obs32|obs)$' }"
    " | Select-Object -ExpandProperty ProcessName -Unique);"
    "$cap = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore';"
    "$u += @(foreach ($k in 'microphone','webcam') { Get-ChildItem \"$cap\\$k\" -Recurse -ErrorAction SilentlyContinue"
    " | Where-Object { $_.GetValue('LastUsedTimeStop') -eq 0 -and $_.GetValue('LastUsedTimeStart') }"
    " | ForEach-Object { \"${k}:\" + (($_.PSChildName -split '#')[-1]) } });"
    "$u = (@($u | Where-Object { $_ } | Select-Object -Unique) -join ',');"
    # minutos sem teclado/mouse (regra do desktop, veio do ociosidade.py); via ssh pode não ter sessão: -1 = não sabe
    "try { Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class LI { "
    "[StructLayout(LayoutKind.Sequential)] struct L { public uint s; public uint t; } [DllImport(\"user32.dll\")] "
    "static extern bool GetLastInputInfo(ref L l); public static double Min() { L l = new L(); l.s = 8; "
    "if (!GetLastInputInfo(ref l)) return -1; return (Environment.TickCount - (int)l.t) / 60000.0; } }'; "
    "$i = [math]::Round([LI]::Min()) } catch { $i = -1 };"
    "Write-Output \"$c|$r|$d|$p|$u|$i|$t\"")
IDLE_MIN = 20  # desktop: minutos sem teclado/mouse antes de ajudar (dono 17/10)
TRAVADO_H = 6  # render vivo há mais que isso (o PC2 teve um anime-pipeline parado 16 h a 0% de CPU em 19-20/10)

# 20/10 (dono: "o PC2 tem que estar sempre no máximo"): o PC2 (4 núcleos, 12 GB) aceita um 2º trabalho com folga
LIMITES = {
    # 21/10: CPU não barra o PC1 — testes de voz (amostras/separador, prioridade baixa) deixavam a CPU em 100% e a produção
    # ficou parada 4 h; dois renders juntos quem impede é a fila de render
    # 03/11 (dona: "coloque como o mínimo 1 GB"): RAM mínima 3/4 -> 1 GB no PC1 e no PC2, igual ao desktop
    "pc1": {"cpu": 101, "ram": 1, "disco": 5, "ver_uso": False},
    "pc2": {"cpu": 40, "ram": 1, "disco": 3, "ver_uso": False, "drive": "C",
            "slots": 2, "cpu_2o": 50, "ram_2o": 6, "disco_2o": 5},
    # 22/10 (dono: "reduzir a regra do PC3 pra só OBS ou chamada de Meet, assim usamos mais ele"): sem a regra de
    # teclado/mouse parado e sem as ferramentas de código — "idle": False desliga a checagem de inatividade
    "desktop": {"cpu": 30, "ram": 1, "disco": 10, "ver_uso": True, "idle": False},  # 31/10 (dona): RAM minima 3 -> 1 GB
    # 22/10: x200ma (Linux, Celeron N2830 2 núcleos, 1,8 GB, sem GPU útil) é só o VISUALIZADOR (visualizador.py): nunca
    # recebe render — x264 1080x1920 sai a ~0,6x do tempo real em vídeo sintético e a RAM mal cabe o Chrome
    "x200ma": {"linux": True},
    # 24/10 (dono: "o acer não está lá também"): Atom 2 GB, telão principal + Flow do Veo pela cadeia_veo; nunca render
    "acer": {"linux": True, "ssh": "emerson-ia@100.98.55.125"},
    # 22/10 (dono: "adicione ela pra ser usada como um dos nossos PCs"): GPU T4 x2 do Kaggle, pelo navegador. Só faz
    # voz clonada (conversão da gpu_fila, treino, piloto), 1 sessão por vez, ~15-25 min de ida e volta: aparece como
    # máquina, mas render comum nunca vai pra ela (ninguém despacha pra "qualquer livre"; todos pedem pelo nome)
    "kaggle": {"gpu": True},
    # 24/10 (dono: "adicione no painel como no de gpu do kaggle pra serem usadas"): Colab grátis de cada conta do cofre
    # (logins pelo D:\logins-google\colab_empresas.py). Como o Kaggle: só quem pede pelo nome; 1 trabalho por conta
    "colab": {"colab": True},
    # 04/11 (dona: "adicionar um S20 ... pra renderizar vídeos"; "adicionei mais um"): Galaxy S20 com Termux. Só FFmpeg
    # mandado pelo celulares.rodar_ffmpeg (junta-trechos do fx_clips); medida e regras de vaga em celulares.py
    "s20ultra": {"celular": True},
    "s20": {"celular": True},
}
COLAB_CONTAS = BASE / "estado" / "colab_contas.json"
KAGGLE = Path(r"D:\hipercool-materiais\amostras_voz")
KAGGLE_LOTES = {"conversor": KAGGLE / "kaggle_conversor" / "estado.json", "treino": KAGGLE / "kaggle" / "estado.json",
                "piloto": KAGGLE / "kaggle_piloto" / "estado.json"}
GPU_FILA = Path(r"D:\hipercool-materiais\gpu_fila")
LINUX_MEDIR = (
    "import json,os,shutil,subprocess,time\n"
    "def st():\n"
    " v=[int(x) for x in open('/proc/stat').readline().split()[1:]]\n"
    " return sum(v), v[3]+v[4]\n"
    "t1,i1=st(); time.sleep(3); t2,i2=st()\n"
    "mem={l.split(':')[0]: int(l.split()[1]) for l in open('/proc/meminfo')}\n"
    "env=dict(os.environ, XDG_RUNTIME_DIR='/run/user/%d' % os.getuid())\n"
    "srv=subprocess.run(['systemctl','--user','is-active','visualizador'],capture_output=True,text=True,env=env).stdout.strip()\n"
    "try: e=json.load(open(os.path.expanduser('~/visualizador/estado.json')))\n"
    "except Exception: e={}\n"
    "print(json.dumps({'cpu': round(100*(1-(i2-i1)/max(t2-t1,1))), 'ram_gb': round(mem['MemAvailable']/1048576,1),"
    " 'disco_gb': round(shutil.disk_usage('/').free/1073741824,1), 'servico': srv, 'situacao': e.get('situacao')}))\n")


def _vez_notebook(host):
    """Quem está com o navegador do notebook agora (Veo, TikTok, login, telão...) — reservados do postador."""
    try:
        if r"D:\postador-de-videos\bin" not in sys.path:
            sys.path.append(r"D:\postador-de-videos\bin")  # append: nunca na frente dos módulos daqui
        import maquina_remota
        return maquina_remota.reservado(host)
    except Exception:  # noqa: BLE001
        return ""


def _medir_linux(host):
    """Máquina Linux que não renderiza: só mostra se está no ar, CPU/RAM/disco e o que o visualizador está fazendo."""
    try:
        r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", LIMITES[host].get("ssh", host),
                            "python3", "-"], input=LINUX_MEDIR.encode(), capture_output=True, timeout=60,
                           creationflags=_SEM_JANELA)
        m = json.loads((r.stdout or b"").decode("utf-8", "replace").strip().splitlines()[-1])
    except Exception as e:  # noqa: BLE001
        return {"host": host, "ocioso": False, "motivo": f"não respondeu ({type(e).__name__})"}
    vez = _vez_notebook(host)
    return {"host": host, "ocioso": False, "renders": 0, "cpu": m["cpu"], "ram_gb": m["ram_gb"], "disco_gb": m["disco_gb"],
            "vez": vez, "motivo": (f"navegador com: {vez} | " if vez else "") +
            f"visualizador {m['servico']}: {m.get('situacao') or 'sem estado'} (não renderiza)"}


STATUS_CENTRAL = "https://produtos.opus-sem-limites.com.br/recap-5a857ed863/status.json"


def _status_central():
    """status.json da central do Kaggle (hermes-prod, recapd colab\\vps_central.py, a cada 5 min). {} se não respondeu."""
    import urllib.request
    try:
        with urllib.request.urlopen(STATUS_CENTRAL, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — sem central = painel usa a reserva
        return {}


def _medir_kaggle():
    """Kaggle = GPU de voz clonada. Livre = nenhum lote (conversor/treino/piloto) na GPU e a tarefa GpuKaggleFila ativa
    (é ela que manda e traz). Mostra a fila de conversões e as horas de GPU que o Kaggle disse que restam na semana."""
    lotes, gpu = [], []
    for nome, arq in KAGGLE_LOTES.items():
        try:
            e = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if e.get("lote"):
            lotes.append({"o_que": f"{nome}: {e['lote'].get('notebook', '?')}", "enviado": e["lote"].get("enviado")})
        m = re.match(r"([\d.]+) h de GPU restantes na semana \(visto em (\d\d/\d\d \d\d:\d\d)", e.get("gpu") or "")
        if m:
            gpu.append((datetime.strptime(m.group(2), "%d/%m %H:%M"), float(m.group(1)), m.group(2)))
    fila = {n: sum(1 for p in (GPU_FILA / n).glob("*") if p.is_dir()) for n in ("pendentes", "enviados", "falhas")}
    try:
        r = subprocess.run(["schtasks", "/query", "/tn", "GpuKaggleFila", "/fo", "csv", "/nh"], capture_output=True,
                           text=True, timeout=30, creationflags=_SEM_JANELA)
        tarefa = "desab" not in r.stdout.lower() and "disabled" not in r.stdout.lower() if r.returncode == 0 else False
    except Exception:  # noqa: BLE001
        tarefa = False
    m = {"host": "kaggle", "gpu": True, "renders": len(lotes), "lotes": lotes, "fila": fila,
         "gpu_h": max(gpu)[1] if gpu else None, "gpu_visto": max(gpu)[2] if gpu else None, "tarefa": tarefa}
    if not tarefa:
        m.update(ocioso=False, motivo="tarefa GpuKaggleFila desabilitada: nada vai pro Kaggle")
    elif lotes:
        m.update(ocioso=False, motivo="GPU em uso: " + ", ".join(x["o_que"] for x in lotes))
    else:
        m.update(ocioso=True, motivo="GPU livre (só voz clonada)")
    m["motivo"] += f" | fila de voz: {fila['pendentes']} esperando, {fila['falhas']} falhas"
    st = _status_central()
    if st.get("contas_detalhe"):
        # 02/11 (dona: "controle no painel pra saber quantas contas ainda tem"): cota REAL de cada conta do pool, medida
        # de hora em hora pela API do Kaggle na central de cada saída (vps_central.py) — sem navegador, sem misturar IP
        m["contas"] = [{"conta": c["conta"], "horas": c.get("livre_h"), "usadas": c.get("usadas_h"),
                        "total": c.get("total_h"), "renova": (c.get("renova") or "")[:16],
                        "visto": (c.get("cota_visto") or "")[5:16].replace("T", " "), "erro": c.get("cota_erro"),
                        "estado": c.get("estado"), "saida": c.get("saida"), "webshare_ip": c.get("webshare_ip"),
                        "motivo": c.get("motivo")} for c in st["contas_detalhe"]]
        m["gpu_h"], m["gpu_visto"] = st.get("gpu_livre_h"), st.get("atualizado")
        m["central"] = {"gpus": st.get("gpus") or [], "pedidos": st.get("pedidos") or [], "atualizado": st.get("atualizado")}
    else:
        try:  # reserva: kaggle_horas.py (Chrome do cofre, 1x/dia — quebrado em 02/11: 401 em quase todas)
            kh = json.loads((BASE / "estado" / "kaggle_horas.json").read_text(encoding="utf-8"))
            m["contas"] = kh.get("contas") or []
            livres = [c["horas"] for c in m["contas"] if c.get("horas") is not None]
            if livres:
                m["gpu_h"], m["gpu_visto"] = round(sum(livres), 1), datetime.fromisoformat(kh["em"]).strftime("%d/%m %H:%M")
        except (OSError, ValueError, KeyError):
            pass
    try:  # 02/11: estado real das contas Webshare (webshare_saude.py, 6 em 6 h): 200 = tem banda, 402 = acabou
        ws = json.loads((BASE / "estado" / "webshare.json").read_text(encoding="utf-8"))
        m["webshare"] = {k: ws.get(k) for k in ("em", "total", "ok", "sem_banda")}
    except (OSError, ValueError):
        pass
    uteis = [c for c in m.get("contas") or [] if c.get("estado") in ("rodando", "livre")]
    if uteis:
        m["motivo"] += (f" | {len(uteis)} de {len(m['contas'])} contas utilizáveis, "
                        f"{sum(1 for c in uteis if c['estado'] == 'rodando')} rodando")
    if m["gpu_h"] is not None:
        n = len([c for c in m.get("contas") or [] if c.get("horas") is not None]) or 1
        m["motivo"] += f" | ~{m['gpu_h']:g} h de GPU na semana em {n} conta(s) (visto {m['gpu_visto']})"
    return m


def _medir_colab():
    """Colab = contas Google logadas na Colab (estado gravado pelo colab_empresas.py). Livre = conta logada sem uso."""
    try:
        e = json.loads(COLAB_CONTAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"host": "colab", "colab": True, "ocioso": False, "contas": [],
                "motivo": "sem contas: rodar D:\\logins-google\\colab_empresas.py"}
    contas = e.get("contas") or []
    ok = [c for c in contas if c.get("logada")]
    uso = [c for c in ok if c.get("uso")]
    m = {"host": "colab", "colab": True, "contas": contas, "renders": len(uso),
         "lotes": [{"o_que": f"{c['conta']}: {c['uso']}"} for c in uso], "ocioso": len(ok) > len(uso),
         "motivo": f"{len(ok)} de {len(contas)} contas logadas | {len(ok) - len(uso)} livres, {len(uso)} em uso"}
    if e.get("em"):
        m["motivo"] += f" (visto {datetime.fromisoformat(e['em']).strftime('%d/%m %H:%M')})"
    return m


def _rodar(host, script):
    enc = base64.b64encode(script.encode("utf-16-le")).decode()
    cmd = ["powershell", "-NoProfile", "-EncodedCommand", enc]
    if host != "pc1":
        cmd = [SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host, " ".join(cmd)]
    r = subprocess.run(cmd, capture_output=True, timeout=120, creationflags=_SEM_JANELA)
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace")


# Dona 28/10: o desktop é a máquina MAIS LIVRE; a câmera só fica ocupada nestes horários fixos (fora deles, muito
# raramente — o OBS/chamada medidos ao vivo continuam valendo). dia: 0 = segunda ... 6 = domingo.
AGENDA_CAMERA = [(1, "10:00", "12:00"), (3, "10:00", "12:00"), (4, "16:00", "18:00")]  # ter, qui, sex


def camera_agendada(agora=None):
    """Texto do horário fixo de gravação no desktop se `agora` cai nele, senão None."""
    agora = agora or datetime.now()
    hm = agora.strftime("%H:%M")
    for dia, ini, fim in AGENDA_CAMERA:
        if agora.weekday() == dia and ini <= hm < fim:
            return f"câmera agendada ({['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom'][dia]} {ini}-{fim})"
    return None


def _desktop_desligado():
    """Dono 21/10: botão pra não usar o desktop (é onde ele grava). Vale pra todo mundo que mede por aqui."""
    try:
        sys.path.insert(0, str(BASE))
        import controle
        return not controle.ligado("desktop", "producao")[0]
    except Exception:  # noqa: BLE001 — defeito no liga/desliga não pode travar a medida
        return False


def _medir_pc1_local():
    """12/11: a medida do PC1 era o mesmo PowerShell+WMI das outras máquinas (Get-CimInstance 3x + Win32_Process) — com
    a CPU em 100% o WMI passava de 2x120 s ("pc1: não respondeu (TimeoutExpired, 2 tentativas)"), cada rodada do
    controlador levava 30+ min (painel: "controlador parado há 29 min") e o PC1 virava "ocupado" justo quando tinha que
    produzir. Do PC1 só valem CPU (não barra: limite 101), RAM, disco e renders (o fila_render substitui) — ver_uso é
    False. psutil lê direto do Windows em < 1 s. None = falhou (cai no PowerShell como antes).
    MAQUINAS_PC1_PSUTIL=0 volta ao PowerShell."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=2)
        ram = round(psutil.virtual_memory().available / 1024 ** 3, 1)
        livres = []
        for p in psutil.disk_partitions(all=False):
            if "fixed" in (p.opts or "") or p.fstype:
                try:
                    livres.append(psutil.disk_usage(p.mountpoint).free)
                except OSError:
                    continue
        disco = round(max(livres) / 1024 ** 3, 1) if livres else 0.0
        return {"cpu": round(cpu), "ram_gb": ram, "disco_gb": disco, "renders": 0, "em_uso": "", "idle_min": None,
                "travados": 0, "medida": "psutil"}
    except Exception:  # noqa: BLE001
        return None


def medir(host):
    lim = LIMITES[host]
    if lim.get("gpu"):
        return _medir_kaggle()
    if lim.get("colab"):
        return _medir_colab()
    if lim.get("celular"):
        try:
            import celulares
            return celulares.medir(host, vale_s=60)
        except Exception as e:  # noqa: BLE001 — celular nunca derruba a medida dos PCs
            return {"host": host, "celular": True, "ocioso": False, "motivo": f"medida falhou ({type(e).__name__})"}
    if lim.get("linux"):
        return _medir_linux(host)
    if host == "desktop" and _desktop_desligado():
        return {"host": host, "ocioso": False, "desligado": True, "motivo": "desligado pelo dono (painel: Liga/desliga)"}
    if host == "desktop" and camera_agendada():
        return {"host": host, "ocioso": False, "motivo": camera_agendada()}
    m = _medir_pc1_local() if host == "pc1" and os.environ.get("MAQUINAS_PC1_PSUTIL", "1") != "0" else None
    for tentativa in ((1, 2) if m is None else ()):  # 21/10 07:01: PC1 a 100% devolveu linha incompleta (ValueError)
        try:
            rc, txt = _rodar(host, PS_MEDIR.replace("__DRIVE__", lim.get("drive", "")).replace("__MAXH__", str(TRAVADO_H)))
            cpu, ram, disco, procs, uso, idle, travados = txt.strip().splitlines()[-1].split("|")
            m = {"cpu": round(float(cpu)), "ram_gb": float(ram), "disco_gb": float(disco), "renders": int(procs),
                 "em_uso": uso, "idle_min": float(idle) if idle not in ("", "-1") else None, "travados": int(travados)}
            break
        except Exception as e:  # noqa: BLE001
            if tentativa == 2:
                # 24/10: clarear IndexError/ValueError (ssh caiu, timeout, resposta vazia) vs outros erros
                if isinstance(e, (IndexError, ValueError)):
                    return {"host": host, "ocioso": False, "motivo": "ssh falhou ou timeout (2 tentativas, resposta vazia/incompleta)"}
                return {"host": host, "ocioso": False, "motivo": f"não respondeu ({type(e).__name__}, 2 tentativas)"}
            time.sleep(5)
    m["host"] = host
    sys.path.insert(0, str(BASE))
    import fila_render
    if host == "pc1":
        rod = fila_render._ler("rodando", fila_render._cfg().get("max_h", 6))
        m["renders"] = len(rod)
    else:  # vez/despacho já reservado pra esta máquina (fila_render maquina=...), sem contar quem está medindo
        m["renders"] += len(fila_render.ocupando(host))
    if lim["ver_uso"] and uso:
        m.update(ocioso=False, motivo=f"dono usando: {uso}")
    elif lim["ver_uso"] and lim.get("idle", True) and m["idle_min"] is not None and m["idle_min"] < IDLE_MIN:
        m.update(ocioso=False, motivo=f"teclado/mouse há {m['idle_min']:.0f} min")
    elif m["renders"] >= lim.get("slots", 1):
        m.update(ocioso=False, motivo=f"render rodando ({m['renders']})")
    elif m["renders"] and m["cpu"] > lim["cpu_2o"]:
        m.update(ocioso=False, motivo=f"{m['renders']} render rodando, CPU {m['cpu']}% (2º trabalho só até {lim['cpu_2o']}%)")
    elif m["renders"] and m["ram_gb"] < lim["ram_2o"]:
        m.update(ocioso=False, motivo=f"{m['renders']} render rodando, RAM {m['ram_gb']} GB (2º trabalho só com {lim['ram_2o']} GB)")
    elif m["renders"] and m["disco_gb"] < lim.get("disco_2o", lim["disco"]):
        m.update(ocioso=False, motivo=f"{m['renders']} render rodando, disco {m['disco_gb']} GB (2º trabalho só com {lim.get('disco_2o', lim['disco'])} GB)")
    elif m["renders"]:
        m.update(ocioso=True, motivo=f"{m['renders']} render rodando, folga pra mais 1 (CPU {m['cpu']}%, RAM {m['ram_gb']} GB)")
    elif m["cpu"] > lim["cpu"]:
        m.update(ocioso=False, motivo=f"CPU {m['cpu']}%")
    elif m["ram_gb"] < lim["ram"]:
        m.update(ocioso=False, motivo=f"RAM {m['ram_gb']} GB")
    elif m["disco_gb"] < lim["disco"]:
        m.update(ocioso=False, motivo=f"disco {m['disco_gb']} GB")
    else:
        m.update(ocioso=True, motivo="ocioso")
    if m["travados"]:
        m["motivo"] += f" | {m['travados']} render travado há mais de {TRAVADO_H} h (não conta)"
    return m


def medir_todos():
    return {h: medir(h) for h in LIMITES}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for h, m in medir_todos().items():
        print(f"{h:8} {'LIVRE  ' if m.get('ocioso') else 'OCUPADO'} {m.get('motivo')} | "
              f"cpu {m.get('cpu')}% ram {m.get('ram_gb')} GB disco {m.get('disco_gb')} GB")
