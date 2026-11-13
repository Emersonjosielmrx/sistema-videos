"""vitrine.py — manda pros TELÕES (notebooks) cada vídeo do YouTube na hora em que ele entra no ar (dono, 22/10/2026).

Lê o ledger de uploads (D:\\postador-de-videos\\logs\\uploads_ledger.jsonl): vídeo cujo horário de abrir (publish_at)
acabou de passar vai pra fila de UM dos telões (alternando), com a duração tirada do arquivo (ffprobe) quando ele ainda
está no PC. Quem toca é o player.py de cada notebook (~/vitrine/fila.txt). Nada aqui posta nem muda vídeo.

    python vitrine.py                 # uma passada (mostra o que mandou)
    python vitrine.py --rodar 39      # vivo por 39 min, conferindo a cada 2 min (o vigia geral relança a cada 20)
    python vitrine.py --instalar      # copia/atualiza o player nos notebooks e liga o telão
    python vitrine.py --instalar-pc2  # PC2 (Windows) como telão só do painel (vitrine\\telao_win.py)
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
LEDGER = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
ESTADO = BASE / "estado" / "vitrine.json"
LOG = BASE / "logs" / "vitrine.log"
PLAYER = BASE / "vitrine" / "player.py"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
PORTA_SSH = {"emerson@100.87.195.108": 2222}  # 24/10: a 22 do x200ma virou Tailscale SSH (pede login); sshd na 2222
FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
# 22/10 (dono): só o ACER exibe; o X200MA é RESERVA (só recebe se o Acer não responder) e toca a 70%
TELOES = ["emerson-ia@100.98.55.125", "emerson@100.87.195.108"]
VOLUME = {"emerson-ia@100.98.55.125": 100, "emerson@100.87.195.108": 70}
TELA = {"emerson-ia@100.98.55.125": "acer", "emerson@100.87.195.108": "x200ma"}  # que quadros cada um gira
TELOES_VIDEO = ["emerson-ia@100.98.55.125", "emerson@100.87.195.108"]  # dona 23/10: só o Acer; X200MA só se o Acer falhar (70%)
# 12/11 (dona): telão = STI e PC2 (só painel). Acer e X200MA saem, mas o vídeo + like/comentário da conta pessoal
# deles fica num INTERRUPTOR (estado\telao_notebooks.json {"ligado": false}); desligado = ~/vitrine/PAUSADO neles.
TELAO_NOTEBOOKS = BASE / "estado" / "telao_notebooks.json"
TELOES_PAINEL = ["emerson-sti-st@100.98.49.0"]  # Linux só com o painel (sem vídeo, sem like)
TELA["emerson-sti-st@100.98.49.0"] = "sti"


def notebooks_ligados():
    try:
        return bool(json.loads(TELAO_NOTEBOOKS.read_text(encoding="utf-8")).get("ligado"))
    except (OSError, ValueError):
        return False


PAINEL_HTML = BASE / "vitrine" / "painel.html"
# 23/10 (dona): o PC2 também é telão — só o PAINEL (Windows: vitrine\telao_win.py em C:\vitrine, Chrome em tela cheia)
TELOES_WIN = ["pc2"]
SCP = r"C:\Program Files\Git\usr\bin\scp.exe"
PYTHONW_PC2 = r"C:\Users\Emerson-IA\AppData\Local\Programs\Python\Python313\pythonw.exe"
# 27/10 (dona): o desktop também é telão (só quando trabalha: câmera/mic/OBS livres) + medidor CPU/RAM 24 h.
# Desktop = 1 conexão ssh por rodada (rajada de ssh trava o sshd dele): painel e conferências num script só.
TELAO_DESKTOP = BASE / "estado" / "telao_desktop.json"  # {"pythonw": ...} gravado pelo --instalar-desktop
SEM_JANELA = 0x08000000
MAX_SEG = 4 * 3600  # dona 23/10: vídeo inteiro (conta tempo de exibição); só um teto de segurança
COMPILADO_SEG = 30 * 60  # mais que isso = compilado: não vai pro telão


def log(m):
    linha = f"[{time.strftime('%d/%m %H:%M:%S')}] {m}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _ssh(alvo, comando, entrada=None, timeout=60):
    args = [SSH, "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=10", "-o", f"Port={PORTA_SSH.get(alvo, 22)}", alvo,
            comando]
    if hasattr(entrada, "read"):  # arquivo (vídeo de aprovação): vai direto pelo stdin, sem carregar na memória
        return subprocess.run(args, stdin=entrada, capture_output=True, timeout=timeout, creationflags=SEM_JANELA)
    if entrada is None:  # 29/10 (Fable): sob pythonw não há stdin e o ssh travava até o timeout ("curtir ...: TimeoutExpired")
        return subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, creationflags=SEM_JANELA)
    return subprocess.run(args, input=entrada, capture_output=True, timeout=timeout, creationflags=SEM_JANELA)


def _dt(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.astimezone()
    except (ValueError, TypeError):
        return None


def _vivo(alvo):
    """O telão está ligado com o player rodando? (ssh responde e o player.py está vivo)"""
    try:
        r = _ssh(alvo, "pgrep -f vitrine/player.py >/dev/null && echo VIVO", timeout=25)
        return b"VIVO" in (r.stdout or b"")
    except subprocess.TimeoutExpired:
        return False


def _duracao(caminho, tipo, vid=None):
    """Duração REAL: do arquivo (ffprobe) se ainda está no PC; senão do próprio YouTube (metadado pequeno, sai pelo
    proxy da vez única — não gasta o IP de casa). 22/10 (dono): o padrão de 75 s fazia Short de 20 s rodar 3x."""
    try:
        r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", caminho],
                           capture_output=True, text=True, timeout=30, creationflags=SEM_JANELA)
        return min(MAX_SEG, float(r.stdout.strip()))
    except (ValueError, OSError, subprocess.TimeoutExpired):
        pass
    if vid:
        try:
            sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
            import ytdlp_vez
            with ytdlp_vez.vez("vitrine: metadado"):
                r = subprocess.run(["yt-dlp", "--skip-download", "--no-warnings", "--print", "%(duration)s",
                                    f"https://www.youtube.com/watch?v={vid}"], capture_output=True, text=True,
                                   timeout=90, creationflags=SEM_JANELA)
            return min(MAX_SEG, float(r.stdout.strip().splitlines()[-1]))
        except Exception:  # noqa: BLE001
            pass
    return 45.0 if (tipo or "short") not in ("completo", "longo", "compilado") else 1200.0  # sem duração: 20 min


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def passada():
    est = _ler()
    agora = datetime.now(timezone.utc)
    desde = _dt(est.get("ate")) or (agora - timedelta(hours=1))
    enviados = set(est.get("enviados", []))
    novos = []
    for linha in LEDGER.read_text(encoding="utf-8").splitlines()[-3000:]:
        try:
            r = json.loads(linha)
        except ValueError:
            continue
        vid = r.get("video_id")
        abre = _dt(r.get("publish_at") or r.get("ts"))
        if not vid or vid in enviados or not abre or not (desde < abre <= agora):
            continue
        tipo = r.get("tipo") or ""
        if tipo == "compilado":  # dona 23/10: compilado é longo demais pro telão
            enviados.add(vid)
            continue
        longo = tipo in ("completo", "longo", "compilado")
        url = f"https://www.youtube.com/watch?v={vid}" if longo else f"https://www.youtube.com/shorts/{vid}"
        novos.append((abre, url, _duracao(r.get("caminho") or "", tipo, vid), f"{r.get('canal', '?')} | {tipo}", vid))
    novos.sort()
    i = int(est.get("vez", 0))
    nao_entregue = None  # revisão 23/10: vídeo que não chegou no telão não pode sair da janela da próxima passada
    for _abre, url, seg, rotulo, vid in novos:
        if seg > COMPILADO_SEG:  # completo que na verdade é compilado (1-4 h): não abre no telão
            enviados.add(vid)
            log(f"telão: pulei {rotulo} {url} ({seg / 60:.0f} min, longo demais)")
            continue
        linha = f"{url}\t{seg:.0f}\t{rotulo}\n"
        if not notebooks_ligados():  # interruptor do Acer/X200MA desligado: ninguém toca vídeo
            enviados.add(vid)
            continue
        r = None
        for alvo in TELOES_VIDEO:  # 22/10 23:50 (dono): vídeo SÓ no Acer; o X200MA fica só com o painel
            if _reservado_veo(alvo):  # 23/10 (dona): máquina gerando Veo não toca vídeo
                continue
            if _vivo(alvo):
                r = _ssh(alvo, "mkdir -p ~/vitrine && cat >> ~/vitrine/fila.txt", entrada=linha.encode("utf-8"))
                if r.returncode == 0:
                    break
        if r is None or r.returncode != 0:
            log(f"nenhum telão recebeu — {url} fica pra próxima")
            nao_entregue = nao_entregue or _abre
            continue
        enviados.add(vid)
        i += 1
        log(f"telão {alvo.split('@')[1]}: {rotulo} {url} ({seg:.0f}s)")
    ate = agora if nao_entregue is None else min(agora, nao_entregue - timedelta(seconds=1))
    est.update(ate=ate.isoformat(), vez=i, enviados=list(enviados)[-2000:])
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(est, ensure_ascii=False), encoding="utf-8")
    return len(novos)


RESERVADOS = Path(r"D:\postador-de-videos\config\notebooks_reservados.json")
NOME_DO_TELAO = {"emerson-ia@100.98.55.125": "acer", "emerson@100.87.195.108": "x200ma", "desktop": "desktop"}


def _reservado_veo(alvo):
    """Motivo da VEZ da máquina ("" = livre). Dona 23/10: "um navegador por vez" — Veo (cadeia_veo), login
    (maquina_remota.logar/ocupar) ou outro dono gravam {maquina: {por, ate}} em notebooks_reservados.json."""
    try:
        r = json.loads(RESERVADOS.read_text(encoding="utf-8")).get(NOME_DO_TELAO.get(alvo, "")) or {}
        return str(r.get("por") or "reservado") if float(r.get("ate", 0)) > time.time() else ""
    except (OSError, ValueError, TypeError):
        return ""


def painel():
    """Manda os dados do painel (vitrine_painel.py) pros telões ligados. Também é o sinal de vida do PC1: telão sem
    dado novo há 12 min mostra "PC1 SEM SINAL"."""
    import vitrine_painel
    dados = json.dumps(vitrine_painel.montar(), ensure_ascii=False).encode("utf-8")
    ligados = notebooks_ligados()
    for alvo in TELOES + TELOES_PAINEL:
        try:
            if alvo in TELOES:  # interruptor: desligado = PAUSADO (o player fecha o painel e não toca vídeo/like)
                _ssh(alvo, "rm -f ~/vitrine/PAUSADO" if ligados else "touch ~/vitrine/PAUSADO", timeout=30)
                if not ligados:
                    continue
            _ssh(alvo, "cat > ~/vitrine/painel.json.tmp && mv ~/vitrine/painel.json.tmp ~/vitrine/painel.json",
                 entrada=dados, timeout=40)
            if alvo in TELOES_PAINEL:
                _ssh(alvo, "touch ~/vitrine/SO_PAINEL", timeout=30)  # STI: só painel, nunca vídeo da fila
                continue
            # 23/10 (dona): reservado pelo Veo = o player mostra só o painel (não pega vídeo da fila)
            vez = _reservado_veo(alvo)  # o motivo vai dentro do arquivo: "login ..." = o player fecha até o painel
            if vez:
                _ssh(alvo, "cat > ~/vitrine/SO_PAINEL", entrada=vez.encode("utf-8"), timeout=30)
            else:
                _ssh(alvo, "rm -f ~/vitrine/SO_PAINEL", timeout=30)
        except subprocess.TimeoutExpired:
            pass
    for alvo in TELOES_WIN:  # Windows: cópia + troca no lugar (o cmd do PC2 não tem cat/mv)
        try:
            tmp = BASE / "estado" / f"painel_{alvo}.json"
            tmp.write_bytes(dados)
            r = subprocess.run([SCP, "-q", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=10",
                                str(tmp), f"{alvo}:C:/vitrine/painel.json.tmp"], capture_output=True, timeout=40,
                               creationflags=SEM_JANELA)
            if r.returncode == 0:
                _ssh(alvo, r"move /y C:\vitrine\painel.json.tmp C:\vitrine\painel.json >nul", timeout=30)
                # 26/10 (dona): login na máquina = painel fora da tela (o telao_win fecha enquanto login.txt existe)
                if "login" in _reservado_veo(alvo).lower():
                    _ssh(alvo, r"echo login > C:\vitrine\login.txt", timeout=30)
                else:
                    _ssh(alvo, r"del C:\vitrine\login.txt 2>nul", timeout=30)
                # 24/10: o telao_win do PC2 morreu (porta 8791 fora) e a tela ficou em "SEM SINAL" com dado novo no
                # disco; a tarefa é só "ao entrar no Windows", então o PC1 religa
                t = _ssh(alvo, "curl -s -m 5 -o NUL -w %{http_code} http://127.0.0.1:8791/painel.json", timeout=30)
                if (t.stdout or b"").strip() != b"200":
                    _ssh(alvo, "schtasks /run /tn PC2_Telao", timeout=30)
                    log(f"painel {alvo}: servidor do telão fora, religado")
            else:
                log(f"painel {alvo}: cópia falhou rc={r.returncode} {(r.stderr or b'').decode(errors='replace')[-150:]}")
        except (subprocess.TimeoutExpired, OSError) as e:
            log(f"painel {alvo}: {type(e).__name__}")
    _painel_desktop(dados)


def _shell_desktop():
    try:
        return json.loads(TELAO_DESKTOP.read_text("utf-8")).get("shell", "cmd")
    except (OSError, ValueError):
        return "cmd"


def _ps_desktop(partes, timeout=60, shell=None):
    """1 script por conexão no desktop (27/10). NUNCA stdin: pipe pelo ssh derruba o sshd dele e o OpenSSH castiga a
    origem. Shell padrão do ssh = PowerShell -> -EncodedCommand (até ~30 mil); cmd -> -Command numa linha (até 8 mil,
    sem aspas duplas nem %). `partes` = comandos PowerShell sem aspas duplas nem % (valem nos 2 jeitos)."""
    import base64
    script = "; ".join(partes)
    if (shell or _shell_desktop()) == "powershell":
        cmd = "powershell -NoProfile -EncodedCommand " + base64.b64encode(script.encode("utf-16-le")).decode()
        lim = 30000
    else:
        if '"' in script or "%" in script:
            raise ValueError("script do desktop com aspas duplas ou % (o cmd quebra)")
        cmd, lim = f'powershell -NoProfile -Command "{script}"', 8000
    if len(cmd) > lim:
        raise ValueError(f"comando grande demais pro desktop ({len(cmd)} > {lim})")
    return _ssh("desktop", cmd, timeout=timeout)


def _gz64(dados):
    import base64
    import gzip
    return base64.b64encode(gzip.compress(dados, 9)).decode()


def _gravar_gz64(origem_b64, destino):
    """Comando PowerShell: lê o arquivo .b64 (gzip) e grava `destino` descomprimido."""
    return (f"$z = New-Object IO.Compression.GZipStream((New-Object IO.MemoryStream(,[Convert]::FromBase64String("
            f"[IO.File]::ReadAllText('{origem_b64}')))), [IO.Compression.CompressionMode]::Decompress); "
            f"$o = New-Object IO.MemoryStream; $z.CopyTo($o); [IO.File]::WriteAllBytes('{destino}', $o.ToArray())")


def _painel_desktop(dados):
    """Painel pro telão do desktop numa conexão só (gravar + login + religar o servidor se caiu)."""
    if not TELAO_DESKTOP.exists():
        return
    try:
        sys.path.insert(0, str(BASE))
        import controle
        if not controle.ligado("desktop", "producao")[0]:
            return  # dona 21/10: desktop desligado no painel = ninguém mexe nele
    except Exception:  # noqa: BLE001
        pass
    login = "1" if "login" in _reservado_veo("desktop").lower() else "0"
    # 30/10 (D38b): o painel ia DENTRO do comando (gzip+base64, ~20 mil caracteres) e o sshd do desktop derruba comando
    # grande — o telão ficava "sem dados, esperando do PC1". Agora o desktop PUXA o painel.json de um HTTP temporário
    # do PC1 (maquina_remota._HttpTemp) com um comando curto.
    import tempfile
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    import maquina_remota
    tmp = Path(tempfile.mkdtemp(prefix="painel_desktop_"))
    try:
        (tmp / "painel.json").write_bytes(dados if isinstance(dados, bytes) else str(dados).encode("utf-8"))
        srv = maquina_remota._HttpTemp(tmp)
        try:
            r = maquina_remota.Remoto("desktop")._ps_enc(
                f"Invoke-WebRequest -UseBasicParsing -TimeoutSec 60 '{srv.url}/painel.json' -OutFile C:\\vitrine\\painel.json.tmp; "
                "Move-Item -Force C:\\vitrine\\painel.json.tmp C:\\vitrine\\painel.json; "
                f"if ('{login}' -eq '1') {{ Set-Content C:\\vitrine\\login.txt login }} "
                "else { Remove-Item C:\\vitrine\\login.txt -EA SilentlyContinue }; "
                "try { $ok = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 http://127.0.0.1:8791/saude.json).StatusCode }"
                " catch { $ok = 0 }; "
                "if ($ok -ne 200) { $null = schtasks /run /tn Desktop_Telao; 'religado' } else { 'ok' }", timeout=90)
        finally:
            srv.fechar()
        if b"religado" in (r.stdout or b""):
            log("painel desktop: servidor do telão fora, religado")
        elif b"ok" not in (r.stdout or b""):
            log(f"painel desktop: não confirmou ({' '.join(((r.stdout or b'') + (r.stderr or b'')).decode(errors='replace').split())[-120:]})")
    except (subprocess.TimeoutExpired, OSError, ValueError) as e:
        log(f"painel desktop: {type(e).__name__}: {str(e)[:120]}")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def instalar_desktop():
    """Desktop como telão (dona 27/10): C:\\vitrine com telao_win.py + painel + moldura_desktop.html, maquina.txt =
    desktop, tarefa Desktop_Telao ao entrar no Windows e 2 atalhos na área de trabalho (desligar / religar o telão).
    1 comando curto por conexão, 60 s entre elas (regra do desktop); arquivo em pedaços de 5 mil caracteres."""
    def conectar(partes, shell=None, timeout=120):
        r = _ps_desktop(partes, timeout=timeout, shell=shell)
        return (r.stdout or b"").decode(errors="replace"), (r.stderr or b"").decode(errors="replace")

    # 1) qual shell o ssh do desktop usa: no cmd o %COMSPEC% vira o caminho; no PowerShell fica literal
    r = _ssh("desktop", "echo %COMSPEC%", timeout=60)
    shell = "cmd" if b"cmd.exe" in (r.stdout or b"").lower() else "powershell"
    log(f"instalar desktop: shell do ssh = {shell} ({(r.stdout or b'').decode(errors='replace').strip()[:60]})")
    arqs = {"telao_win.py": BASE / "vitrine" / "telao_win.py", "painel.html": PAINEL_HTML,
            "moldura_desktop.html": BASE / "vitrine" / "moldura_desktop.html"}
    for nome, p in arqs.items():
        b = _gz64(p.read_bytes())
        pedacos = [b[i:i + 5000] for i in range(0, len(b), 5000)]
        for n, pd in enumerate(pedacos):
            time.sleep(60)
            ini = ["New-Item -ItemType Directory -Force C:\\vitrine | Out-Null"] if n == 0 else []
            verbo = "Set-Content" if n == 0 else "Add-Content"
            fim = [_gravar_gz64(f"C:\\vitrine\\{nome}.b64", f"C:\\vitrine\\{nome}")] if n == len(pedacos) - 1 else []
            out, err = conectar(ini + [f"{verbo} -NoNewline -Path C:\\vitrine\\{nome}.b64 -Value '{pd}'"] + fim
                                + [f"'PEDACO {n + 1}/{len(pedacos)}'"], shell)
            log(f"instalar desktop: {nome} {out.strip()[-40:]} {err.strip()[-120:]}")
            if "PEDACO" not in out:
                log("instalar desktop: parei")
                return
    time.sleep(60)
    nl = "[Environment]::NewLine"
    out, err = conectar([
        "Set-Content -NoNewline C:\\vitrine\\maquina.txt desktop",
        "$py = (Get-Command pythonw -EA SilentlyContinue).Source",
        "if (-not $py) { $py = (Get-ChildItem C:\\Python3*\\pythonw.exe, $env:LOCALAPPDATA\\Programs\\Python\\*\\pythonw.exe"
        " -EA SilentlyContinue | Select-Object -First 1).FullName }",
        "if (-not $py) { 'SEM_PYTHON'; exit 1 }",
        "$area = [Environment]::GetFolderPath('Desktop')",
        f"Set-Content -Path (Join-Path $area 'DESLIGAR TELAO.bat') -Value ('@echo off' + {nl} + "
        f"'echo desligado > C:\\vitrine\\desligado.txt' + {nl} + 'echo Telao desligado. O desktop segue trabalhando.' + "
        f"{nl} + 'timeout /t 3')",
        f"Set-Content -Path (Join-Path $area 'LIGAR TELAO.bat') -Value ('@echo off' + {nl} + "
        f"'del C:\\vitrine\\desligado.txt 2>nul' + {nl} + 'echo Telao volta em ate 1 minuto.' + {nl} + 'timeout /t 3')",
        "$null = schtasks /create /tn Desktop_Telao /tr ([char]34 + $py + [char]34 + ' C:\\vitrine\\telao_win.py')"
        " /sc onlogon /it /f",
        "$null = schtasks /run /tn Desktop_Telao",
        "'PY=' + $py"], shell, timeout=180)
    log(f"instalar desktop: {out.strip()[-200:]} {err.strip()[-200:]}")
    if "PY=" in out:
        TELAO_DESKTOP.write_text(json.dumps({"pythonw": out.split("PY=")[-1].strip(), "shell": shell,
                                             "instalado": time.strftime("%Y-%m-%d %H:%M")}), "utf-8")
        painel()


def instalar_pc2():
    """PC2 como telão do painel: copia painel.html + telao_win.py pra C:\\vitrine e cria a tarefa PC2_Telao (ao entrar
    no Windows, na sessão da tela; pelo schtasks — no PC2 os cmdlets de tarefa estão quebrados) e já liga."""
    for alvo in TELOES_WIN:
        _ssh(alvo, r"if not exist C:\vitrine mkdir C:\vitrine", timeout=30)
        for f in (PAINEL_HTML, BASE / "vitrine" / "telao_win.py", BASE / "vitrine" / "moldura_pc2.html"):
            r = subprocess.run([SCP, "-q", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", str(f),
                                f"{alvo}:C:/vitrine/{f.name}"], capture_output=True, timeout=60, creationflags=SEM_JANELA)
            log(f"instalar {alvo}: {f.name} rc={r.returncode} {(r.stderr or b'').decode(errors='replace')[-150:]}")
        painel()
        r = _ssh(alvo, f'schtasks /create /tn PC2_Telao /tr "\\"{PYTHONW_PC2}\\" C:\\vitrine\\telao_win.py" '
                       '/sc onlogon /it /f & schtasks /run /tn PC2_Telao', timeout=60)
        log(f"instalar {alvo}: tarefa {(r.stdout or b'').decode(errors='replace').strip()[-200:]} "
            f"{(r.stderr or b'').decode(errors='replace').strip()[-200:]}")


CURTIDOS = BASE / "estado" / "vitrine_curtidos.json"
JS_GOSTEI = r"""() => {
  const deslogado = [...document.querySelectorAll('a[href*="accounts.google.com/ServiceLogin"], ytd-button-renderer a[href*="signin"]')]
    .some(a => a.offsetParent);
  const bs = [...document.querySelectorAll('button[aria-pressed]')].filter(b => {
    const l = (b.getAttribute('aria-label') || '').toLowerCase();
    return b.offsetParent && /gostei|like/.test(l) && !/não gostei|nao gostei|dislike/.test(l);
  });
  if (!bs.length) return deslogado ? 'deslogado' : 'sem_botao';
  if (bs[0].getAttribute('aria-pressed') === 'true') return 'ja';
  bs[0].click();
  return 'ok';
}"""


# O Firefox do Acer recebe a versão enxuta do Short (só o vídeo, sem botões — por isso roda leve). O like vai pela
# MESMA chamada que o botão "Gostei" faz na página, com o login da dona que está no navegador (sem chave de API).
JS_GOSTEI_PAGINA = r"""async () => {
  const vid = location.pathname.split('/').filter(Boolean).pop();
  const cfg = window.ytcfg;
  if (!cfg || !vid) return 'sem_pagina';
  // 12/11 (dona: "minha conta aparece logada e sempre vem o aviso de deslogada"): o YouTube passou a exigir os 3
  // hashes (SAPISID, 1PAPISID e 3PAPISID) no Authorization — só o SAPISIDHASH volta 401 com a conta LOGADA.
  const jar = Object.fromEntries(document.cookie.split(';').map(s => s.trim().split('=')).map(([k, ...v]) => [k, v.join('=')]));
  const s1 = jar['SAPISID'] || jar['__Secure-3PAPISID'];
  if (!s1) return 'deslogado';
  const ts = Math.floor(Date.now() / 1000);
  const sha = async (v) => [...new Uint8Array(await crypto.subtle.digest('SHA-1',
    new TextEncoder().encode(`${ts} ${v} ${location.origin}`)))].map(b => b.toString(16).padStart(2, '0')).join('');
  let auth = `SAPISIDHASH ${ts}_${await sha(s1)}`;
  if (jar['__Secure-1PAPISID']) auth += ` SAPISID1PHASH ${ts}_${await sha(jar['__Secure-1PAPISID'])}`;
  if (jar['__Secure-3PAPISID']) auth += ` SAPISID3PHASH ${ts}_${await sha(jar['__Secure-3PAPISID'])}`;
  const r = await fetch('/youtubei/v1/like/like?prettyPrint=false', {method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json', 'Authorization': auth, 'X-Origin': location.origin,
              'X-Goog-AuthUser': String(cfg.get('SESSION_INDEX') || 0)},
    body: JSON.stringify({context: cfg.get('INNERTUBE_CONTEXT'), target: {videoId: vid}})});
  // 12/11 (dona: "continua chegando aviso de conta deslogada no x200ma mesmo estando logada"): 401 com a página
  // LOGADA (ytcfg LOGGED_IN) é a chamada que o YouTube recusou, não falta de login — não vira aviso de deslogado.
  // LOGGED_IN às vezes não vem no ytcfg do player; o avatar no topo ou o cookie de sessão (SID/__Secure-3PSID não
  // são legíveis pelo JS, mas LOGIN_INFO e o SAPISID já lido acima são) também provam que a conta está logada.
  // 12/11 19h55 (diagnóstico no x200ma): o Chrome tinha SÓ os cookies __Secure-3P* (SID/SAPISID/1PSID sumiram) e o
  // ytcfg dizia LOGGED_IN=false — deslogado DE VERDADE. O "s1" (3PAPISID) não prova login: só LOGGED_IN/avatar provam.
  const logada = cfg.get('LOGGED_IN') || !!document.querySelector('#avatar-btn, ytd-topbar-menu-button-renderer img#img');
  if (!r.ok && (r.status === 401 || r.status === 403) && logada) return 'recusado_logado_' + r.status;
  return r.ok ? 'ok' : ('http_' + r.status);
}"""

# Comentário comum (não fixado) da conta pessoal da dona: a página não traz a caixa de comentário, então pega o
# createCommentParams na resposta do /next (ou na continuação dos comentários) e posta pela mesma chamada da caixa.
JS_COMENTAR_PAGINA = r"""async (texto) => {
  const vid = location.pathname.split('/').filter(Boolean).pop().split('v=').pop();
  const cfg = window.ytcfg;
  if (!cfg || !vid) return 'sem_pagina';
  // 12/11 (dona: "minha conta aparece logada e sempre vem o aviso de deslogada"): o YouTube passou a exigir os 3
  // hashes (SAPISID, 1PAPISID e 3PAPISID) no Authorization — só o SAPISIDHASH volta 401 com a conta LOGADA.
  const jar = Object.fromEntries(document.cookie.split(';').map(s => s.trim().split('=')).map(([k, ...v]) => [k, v.join('=')]));
  const s1 = jar['SAPISID'] || jar['__Secure-3PAPISID'];
  if (!s1) return 'deslogado';
  const ts = Math.floor(Date.now() / 1000);
  const sha = async (v) => [...new Uint8Array(await crypto.subtle.digest('SHA-1',
    new TextEncoder().encode(`${ts} ${v} ${location.origin}`)))].map(b => b.toString(16).padStart(2, '0')).join('');
  let auth = `SAPISIDHASH ${ts}_${await sha(s1)}`;
  if (jar['__Secure-1PAPISID']) auth += ` SAPISID1PHASH ${ts}_${await sha(jar['__Secure-1PAPISID'])}`;
  if (jar['__Secure-3PAPISID']) auth += ` SAPISID3PHASH ${ts}_${await sha(jar['__Secure-3PAPISID'])}`;
  const hdr = {'Content-Type': 'application/json', 'Authorization': auth, 'X-Origin': location.origin,
               'X-Goog-AuthUser': String(cfg.get('SESSION_INDEX') || 0)};
  const ctx = cfg.get('INNERTUBE_CONTEXT');
  const api = async (ep, corpo) => {
    const r = await fetch(`/youtubei/v1/${ep}?prettyPrint=false`, {method: 'POST', credentials: 'include', headers: hdr,
      body: JSON.stringify(Object.assign({context: ctx}, corpo))});
    return r.ok ? r.json() : null;
  };
  const achar = (o, chave, out) => {
    if (!o || typeof o !== 'object') return out;
    for (const [k, v] of Object.entries(o)) {
      if (k === chave) out.push(v); else achar(v, chave, out);
    }
    return out;
  };
  const prox = await api('next', {videoId: vid});
  if (!prox) return 'sem_next|sem_next';
  let params = achar(prox, 'createCommentParams', [])[0];
  let lista = null;  // resposta que traz os comentários (pra achar o fixado)
  for (const t of achar(prox, 'continuationCommand', []).map(c => c.token).filter(Boolean)) {
    const c = await api('next', {continuation: t});
    if (!c) continue;
    params = params || achar(c, 'createCommentParams', [])[0];
    if (achar(c, 'commentViewModel', []).length || achar(c, 'commentRenderer', []).length) { lista = c; break; }
  }
  let com = 'pulado';
  if (texto) {
    if (!params) com = 'comentarios_fechados';
    else com = (await api('comment/create_comment', {createCommentParams: params, commentText: texto})) ? 'ok' : 'falhou';
  }
  // like no comentário do CANAL (o fixado; sem canal verificado ele fica só como 1º do criador): formato novo
  // (commentViewModel -> commentEntityPayload.author.isCreator + entidade da barra) ou antigo (commentRenderer)
  let fix = 'sem_fixado';
  if (lista) {
    let acao = null;
    const criador = new Set(achar(lista, 'commentEntityPayload', []).filter(e => e && e.author && e.author.isCreator).map(e => e.key));
    const vms = achar(lista, 'commentViewModel', []).map(v => (v && v.commentViewModel) || v);
    const vm = vms.find(v => v && v.pinnedText) || vms.find(v => v && criador.has(v.commentKey));
    if (vm && vm.toolbarSurfaceKey) {
      const m = achar(lista, 'mutations', []).flat().find(x => x && x.entityKey === vm.toolbarSurfaceKey);
      const lk = m && achar(m, 'likeCommand', [])[0];
      acao = lk && (achar(lk, 'performCommentActionEndpoint', [])[0] || {}).action;
    }
    if (!acao) {
      const cr = achar(lista, 'commentRenderer', []).find(c => c && (c.pinnedCommentBadge || c.authorIsChannelOwner));
      const lb = cr && achar(cr, 'likeButton', [])[0];
      acao = lb && (achar(lb, 'performCommentActionEndpoint', [])[0] || {}).action;
    }
    if (vm || acao) fix = acao ? ((await api('comment/perform_comment_action', {actions: [acao]})) ? 'ok' : 'falhou') : 'sem_acao';
  }
  return com + '|' + fix;
}"""

# Frases prontas por idioma (sem IA). O idioma sai do nome do canal (IDIOMA_CANAL); o resto da rede é brasileiro.
FRASES = {
    "pt": (["", "Nossa, ", "Gente, ", "Sério, ", "Caramba, ", "Olha, ", "Mano, ", "Uau, "],
           ["{t}... que história boa", "{t} me prendeu do começo ao fim", "amei {t}", "{t} ficou demais",
            "quero mais de {t}", "não esperava isso em {t}", "{t} merece mais views",
            "{c} sempre trazendo coisa boa", "{c} acertou de novo", "mais um ótimo do {c}",
            "que final", "essa parte me pegou", "assisti duas vezes", "alguém mais ficou curioso pro resto?",
            "quero a continuação", "que virada", "melhor que muita coisa por aí", "o ritmo desse ficou perfeito",
            "a narração ficou ótima", "esse merecia ser mais longo", "salvei pra ver de novo", "manda a parte 2 logo"],
           [" kkk"]),
    "en": (["", "Wow, ", "Man, ", "Honestly, ", "Damn, ", "Bro, ", "Okay, "],
           ["{t} is so good", "{t} got me hooked", "loved {t}", "need more of {t}", "{t} deserves more views",
            "{c} never misses", "another great one from {c}", "that ending though", "didn't see that coming",
            "watched it twice", "part 2 please", "the pacing on this one is perfect", "this should've been longer",
            "great narration", "saving this to rewatch", "who else wants the next part?"],
           [" lol"]),
    "es": (["", "Wow, ", "Uff, ", "En serio, ", "Madre mía, ", "Bro, "],
           ["{t} está buenísimo", "{t} me atrapó", "me encantó {t}", "quiero más de {t}", "{t} merece más vistas",
            "{c} nunca falla", "otro buenísimo de {c}", "qué final", "no me lo esperaba", "lo vi dos veces",
            "segunda parte por favor", "la narración está genial", "debería ser más largo", "quién más quiere la continuación?"],
           [" jajaja"]),
    "ru": (["", "Вау, ", "Ого, ", "Блин, ", "Честно, ", "Слушайте, "],
           ["{t} — просто огонь", "{t} затянул с первой минуты", "обожаю {t}", "хочу ещё {t}",
            "{c} как всегда на высоте", "ещё одно отличное видео от {c}", "вот это концовка", "такого я не ожидал",
            "посмотрел два раза", "ждём продолжение", "отличная озвучка", "жаль, что так коротко",
            "сохранил, пересмотрю", "кто ещё ждёт следующую часть?"],
           [" ахах"]),
    "th": (["", "ว้าว ", "โอ้โห ", "จริงๆ นะ "],
           ["{t} สนุกมาก", "ชอบ {t} มาก", "อยากดู {t} ต่ออีก", "{c} ไม่เคยทำให้ผิดหวัง", "ตอนจบเด็ดมาก",
            "ไม่คิดว่าจะเป็นแบบนี้", "ดูซ้ำสองรอบแล้ว", "รอภาคต่ออยู่นะ", "พากย์ดีมาก", "อยากให้ยาวกว่านี้",
            "ใครรอตอนต่อไปบ้าง"],
           [" 555"]),
    "vi": (["", "Wow, ", "Trời ơi, ", "Thật sự, ", "Ôi, "],
           ["{t} hay quá", "{t} cuốn thật sự", "mê {t} luôn", "muốn xem thêm {t}", "{c} chưa bao giờ làm thất vọng",
            "thêm một video hay của {c}", "cái kết đỉnh quá", "không ngờ luôn", "xem lại hai lần rồi",
            "mong phần tiếp theo", "giọng đọc hay quá", "ước gì dài hơn", "ai đang chờ phần sau không?"],
           [" haha"]),
    "hi": (["", "वाह, ", "यार, ", "सच में, ", "अरे, "],
           ["{t} बहुत बढ़िया है", "{t} ने बांध के रखा", "{t} बहुत पसंद आया", "{t} का और चाहिए",
            "{c} कभी निराश नहीं करता", "{c} का एक और शानदार वीडियो", "क्या एंडिंग थी", "ये तो सोचा ही नहीं था",
            "दो बार देख लिया", "पार्ट 2 जल्दी लाओ", "आवाज़ बहुत अच्छी है", "और लंबा होना चाहिए था",
            "अगले पार्ट का कौन इंतज़ार कर रहा है?"],
           [" 😂"]),
    "id": (["", "Wah, ", "Gila, ", "Serius, ", "Asli, "],
           ["{t} keren banget", "{t} bikin nagih", "suka banget sama {t}", "mau lagi {t}", "{c} gak pernah gagal",
            "satu lagi video mantap dari {c}", "endingnya gila", "gak nyangka sama sekali", "udah nonton dua kali",
            "lanjut part 2 dong", "narasinya mantap", "harusnya lebih panjang", "siapa lagi yang nunggu lanjutannya?"],
           [" wkwk"]),
    "it": (["", "Wow, ", "Ragazzi, ", "Davvero, ", "Mamma mia, "],
           ["{t} è bellissimo", "{t} mi ha preso subito", "adoro {t}", "voglio ancora {t}", "{c} non sbaglia mai",
            "un altro video top di {c}", "che finale", "non me l'aspettavo", "l'ho visto due volte",
            "seconda parte per favore", "narrazione perfetta", "doveva essere più lungo", "chi altro aspetta il seguito?"],
           [" ahah"]),
    "fr": (["", "Wow, ", "Franchement, ", "Sérieux, ", "Oh là là, "],
           ["{t} est trop bien", "{t} m'a captivé", "j'adore {t}", "je veux encore {t}", "{c} ne déçoit jamais",
            "encore une pépite de {c}", "quelle fin", "je ne m'y attendais pas", "vu deux fois",
            "la suite svp", "super narration", "ça aurait dû être plus long", "qui attend la suite aussi ?"],
           [" mdr"]),
}
FINAIS = ["", "", " 🔥", " ❤️", " 👏", " 😍", " 🔥🔥", "!!", "!", " 👀", " 💯"]
IDIOMA_CANAL = [("manhwaverseru", "ru"), ("versethai", "th"), ("verseviet", "vi"), ("versehindi", "hi"),
                ("verseind", "id"), ("verseita", "it"), ("french", "fr"), ("manhwaversees", "es"),
                ("inovaremanhwaverse", "en")]


def _idioma(canal):
    nome = canal.lower().replace(" ", "")
    return next((lg for chave, lg in IDIOMA_CANAL if chave in nome), "pt")


def _texto_comentario(vid):
    """Comentário variado montado com o título e o canal do próprio vídeo (oEmbed público), sem IA."""
    import random
    import urllib.request
    titulo, canal = "", ""
    try:
        with urllib.request.urlopen(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}"
                                    "&format=json", timeout=20) as r:
            d = json.loads(r.read().decode("utf-8"))
        titulo, canal = d.get("title") or "", d.get("author_name") or ""
    except Exception:  # noqa: BLE001
        pass
    canal_ledger = ""
    for linha in reversed(LEDGER.read_text(encoding="utf-8").splitlines()[-3000:]):
        if vid in linha:
            canal_ledger = (json.loads(linha).get("canal") or "").removeprefix("YouTube ")
            break
    canal = canal or canal_ledger
    inicios, modelos, risos = FRASES[_idioma(canal_ledger or canal)]
    t = " ".join(titulo.split("#")[0].replace("|", " ").split()[:5]).strip(" .,!?:-")
    if len(t) > 35:  # tailandês não tem espaço entre palavras: o título inteiro vinha junto
        t = ""
    modelos = [m for m in modelos if ("{t}" not in m or t) and ("{c}" not in m or canal)]
    frase = random.choice(modelos).format(t=t, c=canal)
    ini = random.choice(inicios)
    frase = ini + frase if ini else frase[:1].upper() + frase[1:]
    return frase + random.choice(FINAIS + risos)


def _gostei_firefox(porta, vid, js=JS_GOSTEI_PAGINA, arg=None):
    """Firefox do telão (WebDriver BiDi, a porta de controle do Firefox): acha a aba do vídeo e clica "Gostei" com
    calma — o Acer é lento e o Short monta os botões depois do vídeo começar (procura por até ~30 s)."""
    import websocket
    ws = websocket.create_connection(f"ws://127.0.0.1:{porta}/session", timeout=60, suppress_origin=True,
                                     host="127.0.0.1:9470")  # o Firefox recusa Origin/Host diferentes (400)
    n = [0]

    def chamar(metodo, params):
        n[0] += 1
        ws.send(json.dumps({"id": n[0], "method": metodo, "params": params}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == n[0]:
                if r.get("type") == "error":
                    raise RuntimeError(f"{metodo}: {r.get('error')} {str(r.get('message'))[:80]}")
                return r.get("result") or {}

    try:
        chamar("session.new", {"capabilities": {}})
        abas = chamar("browsingContext.getTree", {}).get("contexts", [])
        aba = next((c["context"] for c in abas if vid in (c.get("url") or "")), None)
        if not aba:
            return "video_ja_fechou"
        res = "sem_pagina"
        for _ in range(12):  # devagar: o Acer é lento e o ytcfg só existe depois de a página montar
            arg_js = json.dumps(arg, ensure_ascii=False) if arg is not None else ""
            r = chamar("script.evaluate", {"expression": f"({js})({arg_js})", "target": {"context": aba},
                                           "awaitPromise": True})
            res = ((r.get("result") or {}).get("value")) or "sem_resposta"
            if res != "sem_pagina":
                break
            time.sleep(2.5)
        return res
    finally:
        try:
            chamar("session.end", {})
        except Exception:  # noqa: BLE001
            pass
        ws.close()


def _gostei_chrome(porta, vid, js=JS_GOSTEI_PAGINA, arg=None):
    """X200MA (reserva do telão) toca no Chrome: mesma chamada da página, pela porta de controle do Chrome."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=60000)
        pg = next((x for c in br.contexts for x in c.pages if vid in x.url), None)
        if not pg:
            return "video_ja_fechou"
        res = "sem_pagina"
        for _ in range(12):
            res = pg.evaluate(js, arg)
            if res != "sem_pagina":
                break
            pg.wait_for_timeout(2500)
        return res


COMENTARIO_FEITO = ("ok", "comentarios_fechados", "pulado")
FIXADO_FEITO = ("ok", "sem_fixado", "sem_acao")
COMENTARIOS_DIA = 20


def curtir_no_telao():
    """Like da conta PESSOAL da dona no vídeo que o telão está tocando (dona 23/10: "só numa conta, a minha pessoal,
    no Acer que já abre o vídeo pra eu ver"; X200MA quando ele é a reserva). 1 vez por vídeo; só os vídeos que o
    telão toca; conta não logada = não faz nada (fica no log)."""
    if not notebooks_ligados():  # 12/11: interruptor do Acer/X200MA
        return
    for alvo in TELOES_VIDEO:
        try:
            _curtir_em(alvo)
        except Exception as e:  # noqa: BLE001
            log(f"curtir {alvo.split('@')[1]}: {type(e).__name__}")


DESLOGADO = BASE / "estado" / "telao_deslogado.json"  # 29/10 (dona): aviso MUITO claro no telão, no painel e no Telegram
_DESLOGADO_SINAIS = ("http_401", "deslogado", "http_403")


def _avisar_deslogado(alvo, vid, res, com):
    """Like/comentário voltou 'deslogado' (401/403) -> grava o sinal (o telão mostra tela cheia, o painel lista como
    problema) e manda Telegram na hora (1 aviso a cada 4 h). Like 'ok' apaga o sinal e avisa que voltou."""
    maq = TELA.get(alvo, alvo.split("@")[-1])
    deslog = str(res).startswith(_DESLOGADO_SINAIS) or str(com).startswith("deslogado")
    try:
        atual = json.loads(DESLOGADO.read_text(encoding="utf-8")) if DESLOGADO.exists() else {}
    except (OSError, ValueError):
        atual = {}
    if deslog:
        n = int(atual.get("seguidos") or 0) + 1 if atual.get("maquina") == maq else 1
        novo = {"maquina": maq, "alvo": alvo, "desde": atual.get("desde") or datetime.now().isoformat(timespec="minutes"),
                "em": datetime.now().isoformat(timespec="minutes"), "ultimo_video": vid, "resultado": res, "seguidos": n,
                "como_resolver": f"python D:\\video-fila\\vitrine.py --logar-telao{' x200ma' if maq == 'x200ma' else ''}  (entrar com a conta pessoal; o telão volta sozinho)"}
        DESLOGADO.parent.mkdir(parents=True, exist_ok=True)
        DESLOGADO.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
        try:
            import avisos
            avisos.enviar(f"🔴 TELÃO {maq.upper()}: a conta do like/comentário está DESLOGADA ({res}). Nenhum vídeo exibido "
                          f"recebe like até você entrar de novo. Como: {novo['como_resolver']}", origem="telao", importante=True,
                          chave=f"telao_deslogado:{maq}:{datetime.now():%Y%m%d}-{datetime.now().hour // 4}")  # 1 aviso a cada 4 h
        except Exception as e:  # noqa: BLE001
            log(f"aviso deslogado: {type(e).__name__}")
    elif res in ("ok", "ja") and atual.get("maquina") == maq:
        DESLOGADO.unlink(missing_ok=True)
        try:
            import avisos
            avisos.enviar(f"🟢 TELÃO {maq.upper()}: conta do like voltou (like ok em {vid})", origem="telao", importante=False,
                          chave=f"telao_voltou:{maq}:{datetime.now():%Y%m%d}")
        except Exception:  # noqa: BLE001
            pass


def _curtir_em(alvo):
    r = _ssh(alvo, "test -s ~/vitrine/curtir.txt && mv ~/vitrine/curtir.txt ~/vitrine/curtir.lendo && "
                   "cat ~/vitrine/curtir.lendo && rm -f ~/vitrine/curtir.lendo", timeout=25)
    pedidos = [l.split("\t") for l in (r.stdout or b"").decode("utf-8", "replace").splitlines() if l.strip()]
    if not pedidos:
        return
    try:
        feitos = json.loads(CURTIDOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        feitos = {}
    import random
    import socket
    hoje = datetime.now().date().isoformat()
    dia = feitos.pop("_dia", None) or {}
    if dia.get("data") != hoje:
        dia = {"data": hoje, "n": 0}
    for url, *_ in pedidos:
        vid = url.rstrip("/").split("/")[-1].split("v=")[-1][:11]
        curtir_ok = feitos.get(vid) in ("ok", "ja")
        comentar_ok = feitos.get(f"c:{vid}") in COMENTARIO_FEITO
        fixado_ok = feitos.get(f"f:{vid}") in FIXADO_FEITO
        if curtir_ok and comentar_ok and fixado_ok:
            _ssh(alvo, f"mkdir -p ~/vitrine/curtido && touch ~/vitrine/curtido/{vid}", timeout=20)
            continue
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            porta = s.getsockname()[1]
        tunel = subprocess.Popen([SSH, "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-N", "-L",
                                  f"{porta}:127.0.0.1:9470", "-o", f"Port={PORTA_SSH.get(alvo, 22)}", alvo], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, creationflags=SEM_JANELA)
        fazer = _gostei_firefox if alvo == TELOES_VIDEO[0] else _gostei_chrome
        res = feitos.get(vid) if curtir_ok else "sem_resposta"
        com = feitos.get(f"c:{vid}") if comentar_ok else "sem_resposta"
        fix = feitos.get(f"f:{vid}") if fixado_ok else "sem_resposta"
        try:
            time.sleep(4)
            if not curtir_ok:
                try:
                    res = fazer(porta, vid)
                except Exception as e:  # noqa: BLE001
                    res = f"erro: {type(e).__name__}: {str(e)[:80]}"
            if (not comentar_ok or not fixado_ok) and res != "video_ja_fechou":
                texto = None
                # dona 23/10: comentário em ~metade dos vídeos e no máximo 20/dia (a mesma conta em todos parece spam)
                if not comentar_ok and dia["n"] < COMENTARIOS_DIA and random.random() < 0.5:
                    texto = _texto_comentario(vid)
                try:
                    c, f = (fazer(porta, vid, JS_COMENTAR_PAGINA, texto) + "|").split("|")[:2]
                except Exception as e:  # noqa: BLE001
                    c = f = f"erro: {type(e).__name__}: {str(e)[:80]}"
                if not comentar_ok:
                    com = c if texto else "pulado"
                    dia["n"] += com == "ok"
                if not fixado_ok:
                    fix = f or c
        finally:
            tunel.terminate()
        feitos[vid] = res
        feitos[f"c:{vid}"] = com
        feitos[f"f:{vid}"] = fix
        log(f"telão curtir {vid}: {res} | comentar: {com} | fixado: {fix}")
        _avisar_deslogado(alvo, vid, res, com)
        falhou = res not in ("ok", "ja") or com not in COMENTARIO_FEITO or fix not in FIXADO_FEITO
        if falhou and feitos.get(f"r:{vid}", 0) < 1:  # dona 23/10: o vídeo pode rodar até 2 vezes -> 1 repetição
            feitos[f"r:{vid}"] = feitos.get(f"r:{vid}", 0) + 1
            try:
                _ssh(alvo, f"grep -F '{url.split(chr(35))[0]}' ~/vitrine/fila.txt | head -1 | "
                           f"awk -F'\\t' -v OFS='\\t' '{{$1=$1\"#de-novo\"; print}}' >> ~/vitrine/fila.txt", timeout=20)
                log(f"telão curtir {vid}: falhou, volta pra fila pra tocar de novo")
            except subprocess.TimeoutExpired:
                pass
        try:  # avisa o player que já tentou: ele pode fechar o vídeo (antes fechava antes do like)
            _ssh(alvo, f"mkdir -p ~/vitrine/curtido && touch ~/vitrine/curtido/{vid} && "
                       "find ~/vitrine/curtido -type f -mmin +1440 -delete", timeout=20)
        except subprocess.TimeoutExpired:
            pass
    feitos = dict(list(feitos.items())[-6000:])
    feitos["_dia"] = dia
    CURTIDOS.parent.mkdir(parents=True, exist_ok=True)
    CURTIDOS.write_text(json.dumps(feitos, ensure_ascii=False), encoding="utf-8")


def vigia_pc1():
    """Vigia mútuo (vitrine/vigia_mutuo.py): o PC1 confere PC2/Acer/X200MA e avisa no Telegram quem caiu."""
    sys.path.insert(0, str(BASE / "vitrine"))
    import vigia_mutuo
    for m in vigia_mutuo.passada("PC1"):
        log(f"vigia mútuo: {m}")


def _telao_de_video():
    """Acer; o X200MA só quando o Acer não responde (dona 23/10)."""
    return next((a for a in TELOES_VIDEO if _vivo(a)), TELOES_VIDEO[0])


def pedidos():
    """Botão "Ver" do painel (vídeo esperando aprovação): manda o arquivo pro telão que pediu e põe na fila dele."""
    import vitrine_painel
    for alvo in TELOES:
        try:
            # mv é atômico: o que o player gravar depois cai num pedidos.txt novo (antes o ": >" apagava no meio)
            r = _ssh(alvo, "test -s ~/vitrine/pedidos.txt && mv ~/vitrine/pedidos.txt ~/vitrine/pedidos.lendo && "
                           "cat ~/vitrine/pedidos.lendo && rm -f ~/vitrine/pedidos.lendo", timeout=25)
        except subprocess.TimeoutExpired:
            continue
        for linha in (r.stdout or b"").decode("utf-8", "replace").splitlines():
            partes = linha.split("\t")
            if len(partes) >= 2 and partes[0] == "abrir" and partes[1].startswith("https://"):
                # botão "Abrir" no painel do X200MA: o vídeo toca no Acer (único telão de vídeo)
                seg = 600 if "watch?v=" in partes[1] else 65
                _ssh(_telao_de_video(), "cat >> ~/vitrine/fila.txt",
                     entrada=f"{partes[1]}#pedido{int(time.time())}\t{seg}\tpedido no painel do {alvo.split('@')[0]}\n".encode())
                continue
            if len(partes) < 2 or partes[0] != "ver":
                continue
            caminho = vitrine_painel.caminho_pendente(partes[1])
            if not caminho or not Path(caminho).is_file():
                log(f"pedido ver {partes[1]}: arquivo não achado")
                continue
            # nome único por pedido: o mesmo file:// já estava em tocados.txt e o 2º "Ver" nunca tocava (revisão 23/10)
            nome = ("".join(c if c.isalnum() or c in "._-" else "_" for c in partes[1])[-80:]
                    + f"_{int(time.time())}.mp4")
            alvo = _telao_de_video()  # pedido de qualquer painel: toca no Acer (X200MA se o Acer falhar)
            try:
                with open(caminho, "rb") as f:
                    rr = _ssh(alvo, f"mkdir -p ~/vitrine/locais && cat > ~/vitrine/locais/{nome} && echo $HOME",
                              entrada=f, timeout=900)
            except subprocess.TimeoutExpired:  # um envio lento não leva junto os outros pedidos desta leitura
                log(f"pedido ver {partes[1]}: envio estourou o tempo")
                continue
            home = (rr.stdout or b"").decode().strip().splitlines()[-1:] or [""]
            if rr.returncode != 0 or not home[0].startswith("/"):
                log(f"pedido ver {partes[1]}: envio falhou")
                continue
            seg = _duracao(caminho, "longo" if Path(caminho).stat().st_size > 150e6 else "short")
            linha_fila = f"file://{home[0]}/vitrine/locais/{nome}\t{seg:.0f}\tAprovação: {partes[1]}\n"
            _ssh(alvo, "cat >> ~/vitrine/fila.txt", entrada=linha_fila.encode("utf-8"))
            log(f"telão {alvo.split('@')[1]}: aprovação {partes[1]} ({seg:.0f}s)")


INICIAR = r"""
pkill -f 'vitrine/player.py' 2>/dev/null; sleep 1
# o navegador roda em sessão própria: se o player morrer no meio do vídeo, ele fica aberto — fecha junto
pkill -TERM -f '[v]itrine/perfil_navegador' 2>/dev/null; sleep 2; pkill -KILL -f '[v]itrine/perfil_navegador' 2>/dev/null
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/vitrine.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Telao de videos
Exec=python3 %h/vitrine/player.py
X-GNOME-Autostart-enabled=true
EOF
sed -i "s#%h#$HOME#" ~/.config/autostart/vitrine.desktop
# liga já, dentro da sessão gráfica (pega DISPLAY/WAYLAND do gerenciador do usuário; senão :0)
eval "$(systemctl --user show-environment 2>/dev/null | grep -E '^(DISPLAY|WAYLAND_DISPLAY|XAUTHORITY|DBUS_SESSION_BUS_ADDRESS|XDG_RUNTIME_DIR)=' | sed 's/^/export /')"
export DISPLAY=${DISPLAY:-:0}
export XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
nohup setsid python3 ~/vitrine/player.py >/dev/null 2>&1 &
sleep 2; pgrep -f 'vitrine/player.py' >/dev/null && echo "TELAO LIGADO (DISPLAY=$DISPLAY WAYLAND=$WAYLAND_DISPLAY)"
"""


def instalar():
    codigo = PLAYER.read_bytes().replace(b"\r\n", b"\n")
    for alvo in TELOES + TELOES_PAINEL:
        try:  # 24/10: o X200MA sem SSH travava a instalação e o Acer ficava com o player velho
            _ssh(alvo, "true", timeout=30)
        except subprocess.TimeoutExpired:
            log(f"instalar {alvo}: não respondeu, fica pra próxima")
            continue
        r1 = _ssh(alvo, "mkdir -p ~/vitrine && cat > ~/vitrine/player.py", entrada=codigo)
        _ssh(alvo, "cat > ~/vitrine/volume.txt", entrada=f"{VOLUME.get(alvo, 0)}\n".encode())
        _ssh(alvo, "cat > ~/vitrine/tela.txt", entrada=f"{TELA.get(alvo, 'acer')}\n".encode())
        _ssh(alvo, "cat > ~/vitrine/painel.html", entrada=PAINEL_HTML.read_bytes())
        _ssh(alvo, "cat > ~/vitrine/vigia_mutuo.py", entrada=(BASE / "vitrine" / "vigia_mutuo.py").read_bytes())
        try:  # bot do Telegram pro vigia mútuo avisar daqui (só token e chat; arquivo só do usuário)
            # 01/11 (dona): máquina fora vai no bot de pendências humanas, não no geral
            cfg = json.loads(Path(r"D:\postador-de-videos\config\telegram_bots.json").read_text(encoding="utf-8-sig"))[
                "pendencias_humanas"]
            _ssh(alvo, "umask 077 && cat > ~/vitrine/telegram.json && chmod 600 ~/vitrine/telegram.json",
                 entrada=json.dumps({"bot_token": cfg["bot_token"], "chat_id": cfg["chat_id"]}).encode())
        except (OSError, KeyError, ValueError) as e:
            log(f"instalar {alvo}: sem o bot do Telegram ({e})")
        r2 = _ssh(alvo, "bash -s", entrada=INICIAR.replace("\r\n", "\n").encode("utf-8"))
        saida = (r2.stdout or b"").decode("utf-8", "replace").strip()
        log(f"instalar {alvo}: copia rc={r1.returncode} | {saida or (r2.stderr or b'').decode()[-200:]}")


LOGAR_TELAO = r"""
touch ~/vitrine/PAUSADO; sleep 3
pkill -f '[v]itrine/perfil_navegador' 2>/dev/null; pkill -f '[v]itrine/perfil_chrome' 2>/dev/null; sleep 2
eval "$(systemctl --user show-environment | grep -E '^(DISPLAY|XAUTHORITY|DBUS_SESSION_BUS_ADDRESS|XDG_RUNTIME_DIR)=' | sed 's/^/export /')"
export DISPLAY=${DISPLAY:-:0}
mkdir -p ~/vitrine/perfil_chrome
rm -f ~/vitrine/perfil_navegador/lock ~/vitrine/perfil_navegador/.parentlock
for p in mintUpdate mintreport-tray blueman-applet update-notifier; do pkill -x $p; done
nohup setsid firefox --no-remote -profile $HOME/vitrine/perfil_navegador https://accounts.google.com >/dev/null 2>&1 &
sleep 3; echo JANELA_ABERTA
"""


def main():
    if "--instalar-pc2" in sys.argv:
        instalar_pc2()
        return
    if "--instalar-desktop" in sys.argv:
        instalar_desktop()
        return
    if "--instalar" in sys.argv:
        instalar()
        return
    # a dona entra com a conta PESSOAL no navegador do telão (1 vez). "x200ma" = o Chrome do telão reserva (24/10:
    # perfil_navegador de lá estava sem login e todo like/comentário saía "deslogado")
    x200 = "x200ma" in sys.argv
    alvo_telao = TELOES_VIDEO[1] if x200 else TELOES_VIDEO[0]
    if "--logar-telao" in sys.argv:
        script = LOGAR_TELAO.replace(
            "nohup setsid firefox --no-remote -profile $HOME/vitrine/perfil_navegador",
            "nohup setsid google-chrome --password-store=basic --no-first-run "
            "--user-data-dir=$HOME/vitrine/perfil_navegador") if x200 else LOGAR_TELAO
        r = _ssh(alvo_telao, "bash -s", entrada=script.encode("utf-8"), timeout=60)
        print((r.stdout or b"").decode("utf-8", "replace").strip() or (r.stderr or b"").decode()[-200:])
        print(f"Telão pausado. Entre com a sua conta pessoal na janela do {'X200MA' if x200 else 'Acer'}, "
              "feche a janela e rode:\n  python D:\\video-fila\\vitrine.py --retomar-telao" + (" x200ma" if x200 else ""))
        return
    if "--retomar-telao" in sys.argv:
        _ssh(alvo_telao, "pkill -f '[v]itrine/perfil_navegador'; rm -f ~/vitrine/PAUSADO", timeout=30)
        print(f"telão do {'X200MA' if x200 else 'Acer'} voltou")
        return
    if "--rodar" in sys.argv:
        i = sys.argv.index("--rodar")
        fim = time.time() + float(sys.argv[i + 1] if len(sys.argv) > i + 1 else 39) * 60
        trava = BASE / "estado" / "vitrine.lock"
        # 23/10: quem chega com outra rodada viva ESPERA ela acabar e assume na hora (antes saía, e entre o fim da
        # rodada de 39 min e o próximo relançamento do vigia o painel ficava 10-20 min parado: telão "PC1 SEM SINAL")
        while trava.exists() and time.time() - trava.stat().st_mtime < 300:
            if time.time() >= fim:
                return
            time.sleep(20)
        # 24/10: o painel vai numa linha própria — quando curtir/tailscale travavam o laço (20:34→20:56) o PC2
        # ficava sem dados e mostrava "PC1 SEM SINAL"
        def _laco_painel():
            while time.time() < fim:
                try:
                    painel()
                except Exception as e:  # noqa: BLE001
                    log(f"painel falhou: {e}")
                time.sleep(120)
        import threading
        threading.Thread(target=_laco_painel, daemon=True).start()
        # 27/10: o laço principal travou às 16:15 num passo sem prazo e o processo ficou vivo 4 h: o vigia não relançava
        # (achava que rodava) e todos os telões ficaram "sem sinal". Passou 5 min do fim previsto = sai na marra.
        import os as _os
        threading.Timer(max(fim - time.time(), 0) + 300, lambda: (log("rodada passou do tempo: encerro"),
                                                                  _os._exit(3))).start()
        try:
            ultima = 0.0
            while time.time() < fim:
                trava.write_text(str(time.time()))
                if time.time() - ultima >= 120:  # vídeos que abriram a cada 2 min
                    ultima = time.time()
                    for f in (passada, vigia_pc1):
                        try:
                            f()
                        except Exception as e:  # noqa: BLE001
                            log(f"{f.__name__} falhou: {e}")
                try:  # botão "Ver" do painel: responde em até ~20 s
                    pedidos()
                except Exception as e:  # noqa: BLE001
                    log(f"pedidos falhou: {e}")
                try:  # like da conta pessoal da dona no vídeo que o Acer está tocando
                    curtir_no_telao()
                except Exception as e:  # noqa: BLE001
                    log(f"curtir falhou: {e}")
                time.sleep(20)
        finally:
            trava.unlink(missing_ok=True)
        return
    print("novos:", passada())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
