import time
import os
import re
import psutil
from collections import Counter
from pathlib import Path
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.align import Align
from PIL import Image
import msvcrt

import subprocess

ASCII_CACHE = {"path": None, "text": "[dim]Aguardando imagem...[/dim]"}

def get_net_usage(last_net, last_time):
    net = psutil.net_io_counters()
    now = time.time()
    dt = now - last_time
    if dt == 0: dt = 1
    dn_mbps = (net.bytes_recv - last_net.bytes_recv) / dt / 1024 / 1024
    up_mbps = (net.bytes_sent - last_net.bytes_sent) / dt / 1024 / 1024
    return net, now, dn_mbps, up_mbps

def image_to_ascii(image_path, width=40):
    global ASCII_CACHE
    if not image_path or not os.path.exists(image_path):
        return "[dim]Imagem não encontrada.[/dim]"

    if ASCII_CACHE["path"] == image_path:
        return ASCII_CACHE["text"]

    try:
        img = Image.open(image_path).convert('RGB')
        w, h = img.size
        # Adjust aspect ratio for terminal chars (usually 2:1 height/width)
        ratio = h / w
        height = int(width * ratio * 0.45)
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        pixels = img.load()

        chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
        result = []
        for y in range(height):
            line = []
            for x in range(width):
                r, g, b = pixels[x, y]
                br = int(0.299 * r + 0.587 * g + 0.114 * b)
                idx = int((br / 255.0) * 9)
                # Add it using a basic color mapped to the prominent channel (optional)
                # but let's stick to safe plain text to avoid HEX block issues!
                line.append(chars[idx])
            result.append("".join(line))

        final_str = "\n".join(result)
        ASCII_CACHE = {"path": image_path, "text": final_str}
        return final_str
    except Exception as e:
        return f"[red]Erro ao ler Imagem:[/red] {str(e)[:20]}"

def check_gemini_radar():
    """Relatório detalhado dos engines TTS: Gemini, ElevenLabs, edge-tts."""
    result = {
        "status_html": "[dim]N/A[/dim]",
        "errors_429": 0, "rotations": 0,
        "engine_atual": "edge-tts",
        "gemini_keys_total": 0, "gemini_keys_blocked": 0,
        "eleven_keys_total": 0, "eleven_keys_used": 0,
        "eleven_last_ok": None,
        "gemini_last_err": None,
    }

    # Engine atual (env)
    result["engine_atual"] = os.environ.get("TTS_ENGINE", "edge")

    # Gemini TTS log
    try:
        with open("D:/hipercool-inferior-fix/logs/gemini-tts.log", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-200:]
        result["rotations"] = sum(1 for x in lines if "Rotating" in x or "Chave esgotada" in x)
        result["errors_429"] = sum(1 for x in lines if "429" in x or "Quota Exceeded" in x)
        for x in reversed(lines):
            if "429" in x or "Quota" in x or "PROHIBITED" in x or "erro" in x.lower():
                m = re.search(r'\[([^\]]+)\]', x)
                if m:
                    result["gemini_last_err"] = m.group(1).split("T")[-1].replace("Z", "")
                    break
    except Exception:
        pass

    # Gemini keys count
    try:
        import json as _j
        gk = Path("D:/hipercool-inferior-fix/secrets/gemini_keys.json")
        if gk.exists():
            gdata = _j.loads(gk.read_text(encoding="utf-8"))
            keys = gdata if isinstance(gdata, list) else gdata.get("keys", [])
            result["gemini_keys_total"] = len(keys)
            result["gemini_keys_blocked"] = sum(1 for k in keys if k.get("blocked") or k.get("status") == "exhausted")
    except Exception:
        pass

    # ElevenLabs keys
    try:
        import json as _j
        ek = Path("D:/hipercool-inferior-fix/secrets/elevenlabs_keys.json")
        if ek.exists():
            edata = _j.loads(ek.read_text(encoding="utf-8"))
            ekeys = edata.get("keys", [])
            result["eleven_keys_total"] = len(ekeys)
            result["eleven_keys_used"] = sum(1 for k in ekeys if k.get("used_at"))
    except Exception:
        pass

    # Status resumido
    e429 = result["errors_429"]
    if e429 > 15:
        result["status_html"] = f"[bold red]🚨 LIMITADO (QUOTA)[/bold red] (Último: {result['gemini_last_err'] or 'N/A'})"
    elif e429 > 0 or result["rotations"] > 0:
        result["status_html"] = f"[bold yellow]⚠ INSTÁVEL (Rotacionando)[/bold yellow] (Último: {result['gemini_last_err'] or 'N/A'})"
    else:
        result["status_html"] = "[bold green]✅ SAUDÁVEL[/bold green]"

    return result

def find_latest_log():
    logs = list(Path("D:/hipercool-inferior-fix/logs/").glob("*.log")) + list(Path("D:/hipercool-inferior-fix/").glob("*.log"))
    # Ignore internal/unrelated logs
    logs = [log for log in logs if log.name not in ("painel.log", "painel_out.log", "monitor_stdout.log", "monitor_explorer.log", "gemini-tts.log")]
    if not logs: return None
    return sorted(logs, key=lambda x: x.stat().st_mtime, reverse=True)[0]

def get_recent_videos():
    try:
        videos_dir = Path("D:/hipercool-inferior-fix/workspace/videos")
        mp4_files = list(videos_dir.rglob("*.mp4"))
        if not mp4_files: return []
        now = time.time()
        mp4_files = [f for f in mp4_files if (now - f.stat().st_mtime) <= 172800]
        mp4_files = sorted(mp4_files, key=lambda x: x.stat().st_mtime, reverse=True)
        return mp4_files[:5]
    except:
        return []

def parse_log(log_path):
    info = {
        "obra": "?", "caps_pedidos": "", "lista_caps": [], "cap_atual": None, "caps_concluidos": [],
        "cap_fase": "Iniciando", "cap_progresso_txt": "Lendo...", "cap_pct": 0, "linhas_recentes": [],
        "ult_atividade": "Aguardando...", "tts_cache": 0, "tts_new": 0,
        "personas": Counter(), "sfx_count": 0, "memes_count": 0, "censura_count": 0, "censura_n2": 0, "erros_vistos": 0,
        "ultima_img": None
    }

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except: return info

    info["linhas_recentes"] = [line.strip() for line in lines[-12:] if line.strip()]

    cap_regex = re.compile(r"\[GERAR_OBRA\] FASE \d: .*  (.*)-cap(\d+)")
    queue_fila_regex = re.compile(r"Fila: (\d+) cap.tulos? .+ \[([0-9, ]+)\]")
    queue_cap_regex = re.compile(r"CAPÍTULO (\d+): (.+?)(?:\s*—|\s*$)")
    pipeline_regex = re.compile(r"Pipeline: (.+?)\s*[-—–]\s*Cap.tulo\s+(\d+)\s*\((\d+)\s*pain.is\)")
    clip_regex_1 = re.compile(r"Clip (\d+)/(\d+)")
    clip_regex_2 = re.compile(r"\[ensemble\] lote \d+-(\d+)/(\d+)")
    img_regex = re.compile(r"painel=(.*?\.jpg)")
    panels_dir_regex = re.compile(r"--panels-dir\s+[\"']?([^\"'\s]+)")
    persona_regex = re.compile(r"persona=(.*)")

    current_cap_in_loop = None
    detected_panels_dir = None
    for line in lines:
        line = line.strip()

        # Erros
        if "Traceback" in line or "Exception" in line or "Error" in line:
            info["erros_vistos"] += 1

        # queue-runner: "Fila: 4 capítulos → [6, 7, 8, 9]"
        m_fila = queue_fila_regex.search(line)
        if m_fila:
            caps_str = m_fila.group(2)
            info["lista_caps"] = [int(x.strip()) for x in caps_str.split(",") if x.strip().isdigit()]
            info["caps_pedidos"] = f"{info['lista_caps'][0]}-{info['lista_caps'][-1]}" if info["lista_caps"] else ""

        # queue-runner: "║  CAPÍTULO 7: The Meek Cat — Capítulo 7"
        m_qcap = queue_cap_regex.search(line)
        if m_qcap:
            cap_num = int(m_qcap.group(1))
            obra_name = m_qcap.group(2).strip()
            current_cap_in_loop = cap_num
            info["cap_atual"] = cap_num
            if info["obra"] == "?":
                info["obra"] = obra_name
            info["cap_fase"] = "Iniciando"
            info["cap_progresso_txt"] = "Preparando..."
            info["cap_pct"] = 0
            info["tts_cache"] = 0; info["tts_new"] = 0
            info["sfx_count"] = 0; info["memes_count"] = 0
            info["censura_count"] = 0; info["censura_n2"] = 0
            info["personas"].clear()

        # Detecta --panels-dir no log (queue-runner ou pipeline)
        m_pdir = panels_dir_regex.search(line)
        if m_pdir:
            detected_panels_dir = m_pdir.group(1).replace("\\", "/")

        # queue-runner/pipeline: "Pipeline: The Meek Cat — Capítulo 6 (87 painéis)"
        m_pipe = pipeline_regex.search(line)
        if m_pipe:
            if info["obra"] == "?":
                info["obra"] = m_pipe.group(1)
            cap_num = int(m_pipe.group(2))
            current_cap_in_loop = cap_num
            info["cap_atual"] = cap_num
            info["cap_fase"] = "Renderização dos Clipes (TTS+Img)"
            info["cap_progresso_txt"] = f"0/{m_pipe.group(3)} clipes"
            info["cap_pct"] = 5

        if "INICIANDO lote:" in line:
            parts = line.split("INICIANDO lote: ")[1].split(" caps ")
            if len(parts) >= 2:
                info["obra"] = parts[0]
                info["caps_pedidos"] = parts[1].strip()
                if "-" in info["caps_pedidos"]:
                    try:
                        a,b = map(int, info["caps_pedidos"].split("-"))
                        info["lista_caps"] = list(range(a, b+1))
                    except: pass
                else:
                    info["lista_caps"] = [int(x) for x in info["caps_pedidos"].split(",") if x.strip().isdigit()]

        if "[GERAR_OBRA] FASE" in line:
            m = cap_regex.search(line.replace("—", ""))
            if m:
                cap_num = int(m.group(2))
                current_cap_in_loop = cap_num
                if "FASE 1" in line:
                    info["cap_atual"] = cap_num
                    info["cap_fase"] = "Ensemble/Leitura"
                    info["cap_progresso_txt"] = "Iniciando..."
                    info["cap_pct"] = 0
                    info["tts_cache"] = 0; info["tts_new"] = 0
                    info["sfx_count"] = 0; info["memes_count"] = 0
                    info["censura_count"] = 0; info["censura_n2"] = 0
                    info["personas"].clear()

        # Cache Counters
        if "TTS:" in line:
            if "[CACHE]" in line: info["tts_cache"] += 1
            else: info["tts_new"] += 1

        # Sensitivo / Censura
        if "censurando" in line.lower() or "detectado +18" in line.lower() or "exodia" in line.lower():
            info["censura_count"] += 1
        if "blur_251" in line.lower() or "nivel2" in line.lower():
            info["censura_n2"] += 1

        # SFX / Memes
        if "sfx=" in line and "sfx=None" not in line:
            info["sfx_count"] += 1
        if "Meme inserido" in line:
            info["memes_count"] += 1

        m_ens = clip_regex_2.search(line)
        if m_ens:
            info["cap_fase"] = "Visão/Transcrição dos Balões"
            c, t = int(m_ens.group(1)), int(m_ens.group(2))
            info["cap_progresso_txt"] = f"{c}/{t} extraídos"
            info["cap_pct"] = int((c/t)*25)

        m_clip = clip_regex_1.search(line)
        if m_clip:
            info["cap_fase"] = "Renderização dos Clipes (TTS+Img)"
            c, t = int(m_clip.group(1)), int(m_clip.group(2))
            info["cap_progresso_txt"] = f"{c}/{t} clipes"
            info["cap_pct"] = 25 + int((c/t)*50)
            # Find image
            mi = img_regex.search(line)
            if mi and current_cap_in_loop:
                fname = mi.group(1)
                if detected_panels_dir:
                    img_path = f"{detected_panels_dir}/{fname}"
                else:
                    obra_slug = re.sub(r"[^a-z0-9]+", "-", info['obra'].lower()).strip("-")
                    cap_str = f"cap{current_cap_in_loop:02d}"
                    img_path = f"D:/hipercool-inferior-fix/workspace/panels/{obra_slug}-{cap_str}/{fname}"
                if os.path.exists(img_path):
                    info["ultima_img"] = img_path
                else:
                    import glob as _glob
                    alt = _glob.glob(f"D:/hipercool-inferior-fix/workspace/panels/*-cap{current_cap_in_loop:02d}/{fname}")
                    if alt:
                        info["ultima_img"] = alt[0]
            # Find persona
            mp = persona_regex.search(line)
            if mp:
                info["personas"][mp.group(1).strip()] += 1

        if "Concatenando" in line and "clips com trans" in line:
            info["cap_fase"] = "Pós-produção (SFX / Transições)"
            m_concat = re.search(r"(\d+) clips", line)
            if m_concat:
                info["cap_progresso_txt"] = f"{m_concat.group(1)} clips"
            info["cap_pct"] = 80
        if "Adicionando trilha dinâmica" in line:
            info["cap_fase"] = "Montagem de Áudio Final"
            info["cap_progresso_txt"] = "Trilha dinâmica..."
            info["cap_pct"] = 90
        if "Gerando legendas" in line:
            info["cap_fase"] = "Render Terminal (FFMPEG)"
            info["cap_pct"] = 95
        # queue-runner: "✓ Capítulo N — CONCLUÍDO"
        if "CONCLU" in line and current_cap_in_loop:
            if current_cap_in_loop not in info["caps_concluidos"]:
                info["caps_concluidos"].append(current_cap_in_loop)
                info["cap_pct"] = 100
        if ("Auto-validação: APROVADO" in line or "Salvo em: " in line):
            if current_cap_in_loop and current_cap_in_loop not in info["caps_concluidos"]:
                info["caps_concluidos"].append(current_cap_in_loop)
                info["cap_pct"] = 100

        if line.startswith("[") and "]" in line:
            info["ult_atividade"] = line[line.find("]")+1:].strip()

    if not info["cap_atual"] and current_cap_in_loop:
        info["cap_atual"] = current_cap_in_loop

    return info

def format_eta(seconds):
    if seconds <= 0: return "00m 00s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}h {m:02d}m" if h > 0 else f"{m:02d}m {s:02d}s"

def execute_hotkey(key, info, recent_videos):
    k = key.lower()
    msg = ""
    folder_worked = False

    if k == b'o':
        # Tenta abrir o cap atual
        pasta = f"D:\\hipercool-inferior-fix\\workspace\\videos\\{info['obra']}\\cap{info['cap_atual']:02d}"
        if os.path.exists(pasta):
            os.startfile(pasta)
            msg = f"Aberto: cap{info['cap_atual']}"
            folder_worked = True
        elif recent_videos:
             os.startfile(recent_videos[0].parent)
             msg = "Aberto último gerado!"
             folder_worked = True
        else:
             msg = "Pasta não pronta ainda."

    elif k == b's':
        # Escreve arquivo de instrucao de pulo (se o pipeline suportasse)
        with open("D:/hipercool-inferior-fix/COMMAND_SKIP.txt", "w") as f: f.write("1")
        msg = "Comando 'SKIP' enviado."

    elif k == b'p':
        with open("D:/hipercool-inferior-fix/COMMAND_PAUSE.txt", "w") as f: f.write("1")
        msg = "Comando 'PAUSE' enviado suavemente."

    elif k == b'r':
        msg = "Métricas recarregadas à força."

    return msg

def make_layout(info, log_path, recent_videos, net_mbps_down, net_mbps_up, last_hotkey_msg):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="body")
    )

    layout["body"].split_row(
        Layout(name="left", ratio=28),  # Progress & API
        Layout(name="mid", ratio=45),   # TV, Analytics, Current Cap
        Layout(name="right", ratio=27)  # Stats, Logs, Hotkeys
    )

    layout["left"].split_column(
        Layout(name="left_top", ratio=75),
        Layout(name="left_bot", ratio=25)
    )

    layout["mid"].split_column(
        Layout(name="mid_top", ratio=45), # Mini TV
        Layout(name="mid_bot", ratio=55)  # Cap Tracking & Bar
    )

    layout["right"].split_column(
        Layout(name="right_1", ratio=30), # Hotkeys
        Layout(name="right_2", ratio=40), # Recent Videos
        Layout(name="right_3", ratio=30)  # Stats & Censura
    )

    # 1. HEADER (DISCO & REDE)
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('D:\\')

    status_hw = f"💿 DISCO D: [cyan]{disk.free / (1024**3):.1f}GB Livres[/cyan] ({100-disk.percent}%)\n"
    status_hw += f"🌐 REDE: ↓[green]{net_mbps_down:.1f} MB/s[/green]  ↑[magenta]{net_mbps_up:.1f} MB/s[/magenta]"

    pc_status = f"🖥️ PC WORKER | CPU: [yellow]{cpu}%[/yellow] | RAM: [yellow]{ram.percent}%[/yellow]"

    head_t = Table.grid(expand=True)
    head_t.add_column(justify="left", ratio=1)
    head_t.add_column(justify="center", ratio=1)
    head_t.add_column(justify="right", ratio=1)
    head_t.add_row(
        "[bold white on blue] 🛸 ESTAÇÃO CONTROLE HIPERCOOL [/bold white on blue]",
        f"Alvo: [magenta]{log_path.name if log_path else 'Buscando...'}[/magenta]",
        pc_status
    )
    head_t.add_row(
        f"[dim]Aviso: CTRL+Clique nos links roxos funciona![/dim]",
        "",
        status_hw
    )
    layout["header"].update(Panel(head_t, box=box.ROUNDED, style="blue"))

    # 2. LEFT: PROGRESS LIST & GEMINI RADAR
    t_left = Table(expand=True, box=box.MINIMAL, show_header=False)
    t_left.add_column("Status")

    lista = info["lista_caps"]
    concluidos = info["caps_concluidos"]
    atual = info["cap_atual"]

    totais = len(lista) if lista else 1
    feitos = len(concluidos)
    tempo_medio_seg = 15 * 60
    eta_lote = max(0, (totais - feitos) * tempo_medio_seg)
    minutos_gerados = feitos * 12

    t_left.add_row(f"[bold cyan]OBRA:[/bold cyan] {info['obra']}")
    t_left.add_row(f"📦 [bold cyan]EM PACOTE:[/bold cyan] {feitos}/{totais} Eps")
    t_left.add_row(f"⏱️ Lote Fila: [bold yellow]{format_eta(eta_lote)}[/bold yellow]")
    t_left.add_row(f"📼 Video Rend: [green]+{minutos_gerados} mins prontas[/green]")
    t_left.add_row("")

    if lista:
        idx = max(0, lista.index(atual) - 5) if atual in lista else 0
        for c in lista[idx:idx+13]:
            if c in concluidos: t_left.add_row(f"✅ Cap {c:<3} [green]COMPLETO[/green]")
            elif c == atual:    t_left.add_row(f"👉 Cap {c:<3} [bold yellow]RENDERIZANDO[/bold yellow]")
            else:               t_left.add_row(f"⏳ Cap {c:<3} [dim white]Aguardando[/dim white]")
        if len(lista) > idx + 13: t_left.add_row("...")
    layout["left_top"].update(Panel(t_left, title="[bold]ESTADO DA FILA (GERAL)[/bold]", box=box.ROUNDED, style="magenta"))

    api_status, e429, rots = check_gemini_radar()
    api_txt = f"{api_status}\n[dim]429/Quotas estouradas (Hoje):[/dim] {e429}\n[dim]Transições de Key (Proxy):[/dim] {rots}"
    layout["left_bot"].update(Panel(api_txt, title="[bold]RADAR GEMINI API[/bold]", box=box.ROUNDED, style="cyan"))

    # 3. MID: TV & CAP TRACKING
    if info['ultima_img']:
        art = image_to_ascii(info['ultima_img'], width=35)
        layout["mid_top"].update(Panel(art, title=f"[bold]MINI-TV / {Path(info['ultima_img']).name}[/bold]", box=box.ROUNDED))
    else:
        layout["mid_top"].update(Panel(Align.center("\n\n\n[dim]Sem transmissão (Lendo texto ou FFMPEG)[/dim]"), title="[bold]MINI-TV[/bold]"))

    c_pct = max(0, min(100, info["cap_pct"]))
    c_eta_str = "00m 00s" if c_pct == 100 else format_eta(int((100 - c_pct) / 100 * tempo_medio_seg))
    bar_c = "█" * int((c_pct/100) * 45) + "░" * (45 - int((c_pct/100) * 45))

    t_mid = Table(expand=True, box=box.MINIMAL, show_header=False)
    t_mid.add_column("")
    t_mid.add_row(f"🎬 [bold cyan]FOCADO:[/bold cyan] Cap {info.get('cap_atual', 'N/A')}")
    t_mid.add_row(f"⚙️ [bold]FASE:[/bold] {info['cap_fase']}  [dim]({info['cap_progresso_txt']})[/dim]")
    t_mid.add_row(f"[{'green' if c_pct==100 else 'yellow'}]{bar_c} {c_pct}%[/]")
    t_mid.add_row(f"⏱️ ETA do Episódio: [yellow]{c_eta_str}[/yellow]")
    t_mid.add_row("")
    cache = info["tts_cache"]; new_tts = info["tts_new"];
    pct_cache = int((cache/(cache+new_tts))*100) if (cache+new_tts)>0 else 0
    t_mid.add_row(f"🔊 [bold]USO CACHE:[/bold] [green]{cache} Reaps[/green] | [red]{new_tts} Novos[/red] -> [cyan]{pct_cache}% Economia (API)[/cyan]")
    t_mid.add_row(f"📝 [dim]LAST:[dim] {info['ult_atividade'][:70]}")
    layout["mid_bot"].update(Panel(t_mid, title="[bold]MONITORAMENTO INDIVIDUAL (AO VIVO)[/bold]", box=box.ROUNDED, style="green"))

    # 4. RIGHT: HOTKEYS, OUTPUTS, STATS
    # Hotkeys
    msg_alerta = f"\n[bold magenta]>> {last_hotkey_msg} <<[/bold magenta]" if last_hotkey_msg else ""
    hk_txt = f"Aperte as Teclas (sem Enter!):\n\n[bold white][ O ][/bold white] - Abrir Pasta do Capítulo Atual no Windows\n[bold white][ S ][/bold white] - Mandar Sinal de Pular Cap\n[bold white][ P ][/bold white] - Mandar Sinal de Pause\n[bold white][ R ][/bold white] - Atualizar Tela{msg_alerta}"
    layout["right_1"].update(Panel(hk_txt, title="🎛️ CONTROLES HARDWARE", box=box.ROUNDED, style="yellow"))

    # Recent Vids
    t_vid = Table(expand=True, box=box.MINIMAL, show_header=False)
    t_vid.add_column("Videos Recentes")
    if recent_videos:
        for i, v in enumerate(recent_videos[:3]):
            folder_uri = "file:///" + str(v.parent.resolve()).replace('\\', '/')
            name = v.parent.parent.name + "/" + v.name
            t_vid.add_row(f"🎥 [bold][link={folder_uri}]{name}[/link][/bold] ({(v.stat().st_size / (1024*1024)):.1f}MB)")
    else: t_vid.add_row("[dim]Nenhum video novo...[/dim]")
    layout["right_2"].update(Panel(t_vid, title="🔥 OUTPUTS 2H (CTRL+Click na linha)", box=box.ROUNDED, style="cyan"))

    # Analytics / Stats
    err_color = "red" if info["erros_vistos"] > 0 else "dim"
    s_txt = f"🧨 [bold {err_color}]Exceções Python (Bugs): {info['erros_vistos']}[/bold {err_color}]\n"
    s_txt += f"🔞 [bold magenta]Censura / Impróprio:[/bold magenta] {info['censura_count']} quadros (Nível 2 Blur: {info['censura_n2']})\n"
    s_txt += f"💥 [bold]Efeitos Injetados:[/bold] {info['sfx_count']} Audios | {info['memes_count']} Memes\n"

    s_txt += "\n🏆 [bold]Top Personagens Atuando:[/bold]\n"
    if info["personas"]:
        for p, c in info["personas"].most_common(3):
            s_txt += f"  - {p[:20]}: {c} falas\n"
    else:
        s_txt += "  [dim]Aguardando vozes...[/dim]"

    layout["right_3"].update(Panel(s_txt, title="📊 ESTATÍSTICAS DO CAP (RADAR XYZ)", box=box.ROUNDED, style="white"))

    return layout

def main():
    last_net_io = psutil.net_io_counters()
    last_net_time = time.time()
    last_msg = ""

    with Live(refresh_per_second=1, screen=False) as live:
        while True:
            # Check Keys
            if msvcrt.kbhit():
                try:
                    k = msvcrt.getch()
                    log_path = find_latest_log()
                    info = parse_log(log_path) if log_path else None
                    if info: last_msg = execute_hotkey(k, info, get_recent_videos())
                except: pass

            log_path = find_latest_log()
            recent_vids = get_recent_videos()
            info = parse_log(log_path) if log_path else None

            if not info:
                info = {"linhas_recentes": [], "lista_caps": [], "caps_concluidos": [], "obra": "?", "cap_atual": "?", "cap_pct": 0, "tts_cache":0, "tts_new":0, "cap_fase": "...", "ultima_img": None, "personas": Counter(), "sfx_count": 0, "memes_count": 0, "censura_count": 0, "censura_n2": 0, "erros_vistos": 0}

            net, last_net_time, dn, up = get_net_usage(last_net_io, last_net_time)
            last_net_io = net

            live.update(make_layout(info, log_path, recent_vids, dn, up, last_msg))
            time.sleep(2)

            if last_msg: last_msg = "" # clear msg next frame

if __name__ == "__main__":
    main()
