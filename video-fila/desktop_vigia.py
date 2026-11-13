"""desktop_vigia.py — põe o desktop pra trabalhar sozinho, aos poucos, enquanto o ssh dele cai (dona 29/10/2026: "crie
crons pra ir tentando de vez em quando e quando conseguir vá mandando os arquivos e executando na medida do possível").

O sshd do desktop aceita a chave e derruba a sessão em boa parte das conexões (29/10: cai também pela rede de casa,
192.168.18.45, então não é a Tailscale; PerSourcePenalties já está "no"). Comando curto passa mais; scp e comando
grande quase nunca. Por isso: 1 conexão de teste por rodada e no máximo 1 passo pesado; arquivo vai por HTTP (o
desktop PUXA do PC1 por um servidor temporário que só serve os arquivos do passo), nunca por stdin/scp.

Passos (cada um só uma vez; o estado fica em estado\\desktop_vigia.json):
  1 telao   C:\\vitrine (telao_win.py + painel + moldura), medidor de CPU/RAM 1 linha/min, tarefa Desktop_Telao e os
            atalhos DESLIGAR/LIGAR TELAO na área de trabalho (vitrine\\instalar_desktop.ps1). Reinstala se o
            telao_win.py daqui mudar. Feito = grava estado\\telao_desktop.json (o vitrine.py passa a mandar o painel e o
            analise_maquinas.py passa a ler o desktop).
  1b conferir  a tarefa Desktop_Telao roda e o medidor responde (127.0.0.1:8791/saude.json); não = reinstala
  1c chave  chave ssh própria do desktop; só a pública vem (estado\\desktop_chave.pub) — a dona autoriza
  2 nsn     worker do "navegador sem navegador" (maquina_remota.py instalar-nsn desktop)
  3 colher  cookies Google/Flow de até 2 perfis por rodada (maquina_remota.py colher-flow <perfil> desktop), só com a
            máquina livre (sem câmera/chamada, sem Chrome de outro trabalho)
  4 saude   maquina_remota.py saude-flow desktop (quem está logado no Flow lá, por HTTP)
Telegram: 1º contato depois de muito tempo fora, cada passo concluído, e 24 h sem conseguir entrar (com o guia
D:\\video-fila\\linhas\\DESKTOP_PRINCIPAL.md).

    python desktop_vigia.py            # 1 rodada (tarefa DesktopVigia, a cada 10 min, pythonw)
    python desktop_vigia.py --status   # imprime o estado
"""
import functools
import hashlib
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
ESTADO = BASE / "estado" / "desktop_vigia.json"
LOG = BASE / "logs" / "desktop_vigia.log"
TRAVA = BASE / "estado" / "desktop_vigia.lock"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
PY = r"D:\veo\venv\Scripts\python.exe"
MR = r"D:\postador-de-videos\bin\maquina_remota.py"
PC1_IP = "100.118.234.102"  # Tailscale do PC1 (o desktop puxa daqui)
PORTA_HTTP = 8798
SEM_JANELA = 0x08000000
ARQS_TELAO = ("telao_win.py", "moldura_desktop.html", "painel.html")
COLHER_POR_RODADA = 4  # 30/10 05h30: 2 deixava 46 perfis pra ~4 h; cada colher ~25 s e a rodada para se o ssh cair
AVISO_FORA_H = 24


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] {m}\n")


def _ler():
    try:
        return json.loads(ESTADO.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(e):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(e, ensure_ascii=False, indent=1), "utf-8")
    os.replace(tmp, ESTADO)


def _avisar(msg, importante=True):
    try:
        import avisos
        avisos.enviar(msg, "desktop-vigia", importante=importante, html_ok=False)
    except Exception as ex:  # noqa: BLE001
        log(f"aviso não saiu: {ex}")


def _ps(script, timeout=120):
    """1 conexão: script PowerShell por -EncodedCommand (o shell do ssh do desktop é PowerShell). Nunca stdin."""
    import base64
    # 30/10 02:06: sem isto o Invoke-WebRequest do PowerShell 5 manda a barra de progresso (CLIXML) e fica lento
    script = "$ProgressPreference = 'SilentlyContinue'; " + script
    cmd = "powershell -NoProfile -EncodedCommand " + base64.b64encode(script.encode("utf-16-le")).decode()
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=20", "desktop", cmd],
                       stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, creationflags=SEM_JANELA)
    return r.returncode, ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")


def _md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def _servir(pasta):
    """Servidor HTTP temporário só com os arquivos do passo, na Tailscale do PC1. Devolve o servidor (shutdown no fim)."""
    class Quieto(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):  # sob pythonw não há stderr: o log padrão derrubava cada download (29/10 23:49)
            pass
    socketserver.TCPServer.allow_reuse_address = True
    s = socketserver.ThreadingTCPServer((PC1_IP, PORTA_HTTP), functools.partial(Quieto, directory=str(pasta)))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def passo_telao(e):
    vit = BASE / "vitrine"
    assin = "|".join(_md5(vit / a) for a in ARQS_TELAO)
    tmp = Path(tempfile.mkdtemp(prefix="desktop_vigia_"))
    for a in ARQS_TELAO:
        shutil.copy2(vit / a, tmp / a)
    script = (vit / "instalar_desktop.ps1").read_text("utf-8").replace("__URL__", f"http://{PC1_IP}:{PORTA_HTTP}")
    srv = _servir(tmp)
    try:
        rc, out = _ps(script, timeout=240)
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    linhas = [l.strip() for l in out.splitlines() if l.strip().startswith(("ERRO", "PY=", "SEM_PYTHON", "ARQ", "FIM"))]
    log("telao: " + (" | ".join(linhas)[:400] or f"rc={rc} {' '.join(out.split())[-200:]}"))
    if "FIM" in out and "PY=" in out and "ERRO" not in out:
        py = out.split("PY=")[-1].splitlines()[0].strip()  # "C:\Program Files\..." tem espaço
        (BASE / "estado" / "telao_desktop.json").write_text(json.dumps(
            {"pythonw": py, "shell": "powershell", "instalado": time.strftime("%Y-%m-%d %H:%M")}), "utf-8")
        e["telao"] = {"quando": time.strftime("%Y-%m-%d %H:%M"), "assinatura": assin}
        _avisar("🖥️ Desktop: telão + medidor de CPU/RAM instalados (atalhos DESLIGAR TELAO / LIGAR TELAO na área de "
                "trabalho). O telão só aparece com a câmera desligada.")
        return True
    return False


def passo_conferir_telao(e):
    """Depois da instalação: a tarefa está rodando e o medidor responde? Não = instala de novo na próxima rodada."""
    # 30/10 00:08: o telão subiu como "pc2" (sem C:\vitrine\maquina.txt) = moldura errada e SEM a regra da câmera.
    # Aqui o maquina.txt é regravado (sem BOM) e o telão reiniciado quando não diz "desktop".
    rc, out = _ps('$m = try { [IO.File]::ReadAllText("C:\\vitrine\\maquina.txt").Trim() } catch { "" }; '
                  'if ($m -ne "desktop") { [IO.File]::WriteAllText("C:\\vitrine\\maquina.txt", "desktop"); '
                  'Stop-ScheduledTask -TaskName Desktop_Telao -EA SilentlyContinue; '
                  'Get-CimInstance Win32_Process -Filter "Name=\'pythonw.exe\'" | Where-Object { $_.CommandLine -like "*telao_win*" }'
                  ' | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; Start-Sleep 3; '
                  'Start-ScheduledTask -TaskName Desktop_Telao; Start-Sleep 12; "CORRIGIDO maquina.txt era [" + $m + "]" }; '
                  '"TAREFA " + (Get-ScheduledTask -TaskName Desktop_Telao -EA SilentlyContinue).State; '
                  'try { "SAUDE " + (Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 http://127.0.0.1:8791/saude.json).Content }'
                  ' catch { "SAUDE erro" }; "FIM"', timeout=120)
    if "FIM" not in out:
        return False  # ssh caiu: tenta de novo na próxima
    log("conferir telão: " + " ".join(l.strip() for l in out.splitlines()
                                       if l.startswith(("TAREFA", "SAUDE", "CORRIGIDO")))[:300])
    if "SAUDE {" in out and '"maquina": "desktop"' in out:
        e["telao_conferido"] = time.strftime("%Y-%m-%d %H:%M")
        return True
    e.pop("telao", None)  # não subiu: reinstala
    return False


def passo_chave(e):
    """Chave ssh PRÓPRIA do desktop (dona 29/10: "dê acesso desse PC a ele e aos outros", plano B de o desktop virar o
    PC principal). Só a parte pública vem pra cá (estado\\desktop_chave.pub); a privada nunca sai de lá. Autorizar a
    chave no PC1/PC2/notebooks é mudança de segurança: quem roda é a dona (linhas\\DESKTOP_PRINCIPAL.md, passo 1)."""
    rc, out = _ps('$k = Join-Path $env:USERPROFILE ".ssh\\id_ed25519"; '
                  'if (-not (Test-Path $k)) { New-Item -ItemType Directory -Force (Split-Path $k) | Out-Null; '
                  # 30/10 01:21: `& ssh-keygen -N ""` no PowerShell 5 some com o "" e o keygen fica esperando a senha
                  # (InvokeMethodOnNull 4x). Start-Process com a linha inteira preserva as aspas; caminho completo.
                  '$kg = (Get-Command ssh-keygen -EA SilentlyContinue).Source; '
                  'if (-not $kg) { $kg = "C:\\Program Files\\OpenSSH\\ssh-keygen.exe" }; "KEYGEN " + $kg; '
                  'Start-Process -FilePath $kg -ArgumentList (\'-q -t ed25519 -N "" -C desktop-dona -f "\' + $k + \'"\') '
                  '-Wait -NoNewWindow }; '
                  'if ((Test-Path $k) -and -not (Test-Path ($k + ".pub"))) { '
                  '$kg2 = (Get-Command ssh-keygen -EA SilentlyContinue).Source; if (-not $kg2) { $kg2 = "C:\\Program Files\\OpenSSH\\ssh-keygen.exe" }; '
                  '& $kg2 -y -f $k | Set-Content -Encoding ascii ($k + ".pub") }; '
                  'if (-not (Test-Path ($k + ".pub"))) { "SEM_PUB"; "FIM"; exit }; '
                  '$cfg = Join-Path $env:USERPROFILE ".ssh\\config"; '
                  'if (-not (Test-Path $cfg) -or -not (Select-String -Path $cfg -Pattern "^Host pc1" -Quiet)) { '
                  'Add-Content $cfg ("`r`n# 29/10 (desktop_vigia): as outras maquinas, com a chave propria do desktop`r`n'
                  'Host pc1`r`n    HostName 100.118.234.102`r`n    User Haylla`r`n    IdentityFile ~/.ssh/id_ed25519`r`n'
                  'Host pc2`r`n    HostName 100.125.7.77`r`n    User Emerson-IA`r`n    IdentityFile ~/.ssh/id_ed25519`r`n'
                  'Host x200ma`r`n    HostName 100.87.195.108`r`n    User emerson`r`n    Port 2222`r`n'
                  '    IdentityFile ~/.ssh/id_ed25519`r`n'
                  'Host acer`r`n    HostName 100.98.55.125`r`n    User emerson-ia`r`n    IdentityFile ~/.ssh/id_ed25519`r`n") }; '
                  '"PUB " + (Get-Content ($k + ".pub") -Raw).Trim(); "FIM"', timeout=90)
    pub = next((l[4:].strip() for l in out.splitlines() if l.startswith("PUB ssh-")), "")
    if not pub:
        log(f"chave: não veio ({' '.join(out.split())[-150:]})")
        return False
    (BASE / "estado" / "desktop_chave.pub").write_text(pub + "\n", "utf-8")
    e["chave"] = time.strftime("%Y-%m-%d %H:%M")
    log("chave: pública do desktop guardada em estado\\desktop_chave.pub")
    _avisar("🔑 Desktop: chave ssh própria criada lá. Para ele acessar o PC1/PC2/notebooks, rode no PC1 o passo 1 de "
            "D:\\video-fila\\linhas\\DESKTOP_PRINCIPAL.md (autorizar_desktop.ps1).", importante=False)
    return True


def _rodar(args, timeout=900):
    r = subprocess.run([PY, "-X", "utf8", MR, *args], stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
                       creationflags=SEM_JANELA, cwd=str(Path(MR).parent))
    return ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")


NSN = Path(r"D:\projeto-navegador-sem-navegador")


def passo_nsn(e):
    """Worker do nsn pelo mesmo caminho do telão (30/10 01:51: o `instalar-nsn` manda o pacote por scp e o desktop
    derruba): empacota aqui (sem cookies), o desktop PUXA por HTTP e extrai preservando cookies\\ venv\\ saida\\ de lá."""
    import tarfile
    subprocess.run([PY, "-X", "utf8", str(NSN / "tools" / "empacotar_worker.py")], check=True, cwd=str(NSN),
                   stdin=subprocess.DEVNULL, capture_output=True, creationflags=SEM_JANELA, timeout=180)
    tmp = Path(tempfile.mkdtemp(prefix="desktop_vigia_nsn_"))
    with tarfile.open(tmp / "nsn_worker.tgz", "w:gz") as t:
        t.add(NSN / "dist" / "nsn_worker", arcname="nsn_worker")
    script = (
        'if (-not (Test-Path C:\\postador-worker\\nsn\\venv\\Scripts\\python.exe)) { "SEM_VENV"; "FIM"; exit }; '
        'Set-Location C:\\postador-worker; '
        f'Invoke-WebRequest -UseBasicParsing -TimeoutSec 300 http://{PC1_IP}:{PORTA_HTTP}/nsn_worker.tgz '
        '-OutFile C:\\postador-worker\\nsn_worker.tgz; '
        'tar -xzf nsn_worker.tgz; '
        'robocopy nsn_worker C:\\postador-worker\\nsn /E /XD cookies venv saida /NFL /NDL /NJH /NJS | Out-Null; '
        'Remove-Item -Recurse -Force nsn_worker, nsn_worker.tgz; Set-Location C:\\postador-worker\\nsn; '
        'New-Item -ItemType Directory -Force saida, cookies | Out-Null; '
        "& .\\venv\\Scripts\\python.exe -c \"import services.instagram.postar, services.veo_flow.flow_gerar, os; "
        "print('nsn ok', len(os.listdir('cookies')), 'cookies')\"; \"FIM\"")
    srv = _servir(tmp)
    try:
        rc, out = _ps(script, timeout=420)
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    uteis = [l.strip() for l in out.splitlines() if l.strip() and not l.lstrip().startswith(("<", "#<"))]
    log("nsn: " + (" | ".join(uteis)[-300:] or " ".join(out.split())[-200:]))
    if "SEM_VENV" in out:
        log("nsn: desktop sem o venv do worker (C:\\postador-worker\\nsn\\venv) — IMPLANTAR_MAQUINA.md passo 3a")
    if "nsn ok" in out:
        e["nsn"] = time.strftime("%Y-%m-%d %H:%M")
        _avisar("🖥️ Desktop: worker do navegador-sem-navegador instalado (" + out.split("nsn ok")[-1].split("\n")[0].strip()
                + "). Próximo: colher os cookies das contas de lá, aos poucos.")
        return True
    return False


def _perfis_desktop():
    sys.path.insert(0, str(Path(MR).parent))
    import maquina_remota as mr
    d = mr._logins()
    return [p for p, info in d.items() if not p.startswith("_") and isinstance(info, dict)
            and isinstance(info.get("desktop"), dict) and (info["desktop"].get("youtube") or info["desktop"].get("google"))
            and p not in mr.FLOW_BLOQUEADAS]


def passo_colher(e):
    sys.path.insert(0, str(Path(MR).parent))
    import maquina_remota as mr
    # 30/10 03:18: o maquina_livre faz 1 ssh a mais e, com o ssh do desktop caindo, dizia "ocupado" à toa. A sonda da
    # rodada já viu o Chrome (e["_chrome_livre"]); câmera e vez (login) são locais.
    motivo = ("Chrome de outro trabalho aberto" if not e.get("_chrome_livre") else mr._camera_agendada("desktop")
              or ("login" in mr.reservado("desktop").lower() and "login aberto pela dona"))  # = regra do maquina_livre
    if motivo:
        log(f"colher: desktop ocupado agora ({motivo}) — fica pra próxima")
        return False
    feitos = set(e.get("colhidos", []))
    falta = [p for p in _perfis_desktop() if p not in feitos]
    if not falta:
        e["colher_fim"] = time.strftime("%Y-%m-%d %H:%M")
        _avisar(f"🖥️ Desktop: cookies do Flow colhidos em {len(feitos)} perfis. Ele já entra na produção por HTTP.")
        return True
    for p in falta[:COLHER_POR_RODADA]:
        e["colhendo"] = p  # se o ssh cair no meio, a próxima sonda fecha ESTE Chrome na hora (é nosso)
        _gravar(e)
        out = _rodar(["colher-flow", p, "desktop"], timeout=300)
        ok = "COLHIDO" in out or "google_logado=True" in out
        log(f"colher {p}: {'ok' if ok else ' '.join(out.split())[-160:]}")
        if ok or "logado=False" in out:  # deslogado lá também conta como visto (não fica tentando pra sempre)
            e.setdefault("colhidos", []).append(p)
        if "reset" in out.lower():
            break  # ssh caiu: para a rodada (e["colhendo"] fica: a sonda fecha o Chrome que sobrou)
        e.pop("colhendo", None)
        if "OCUPADO" in out or "sem resposta" in out:
            break  # 07:51: a produção pegou o desktop (Veo/imagem) — as próximas só dariam "sem resposta"
    return False


def passo_saude(e):
    out = _rodar(["saude-flow", "desktop"], timeout=600)
    log("saude: " + " ".join(out.split())[-300:])
    e["saude"] = {"quando": time.strftime("%Y-%m-%d %H:%M"), "saida": " ".join(out.split())[-300:]}
    return True


def rodada():
    e = _ler()
    agora = time.time()
    try:
        # 30/10 02:58: Chrome aberto por um trabalho cujo ssh caiu antes do `fechar` (colher 02:41) segurava o desktop
        # para TUDO (o chrome_conta só solta login velho). A sonda fecha o que passou de 45 min e não é login da dona.
        # 06:23: o Chrome do colher que caiu (05:41) também esperava 45 min; o perfil que a vigia estava colhendo é dela:
        # fecha logo (o nome só tem letras/números/._-, então vai direto na string).
        meu = "".join(ch for ch in str(e.get("colhendo") or "") if ch.isalnum() or ch in "._-")
        rc, out = _ps(f'$meu = "{meu}"; '
                      '$o = "C:\\postador-worker\\ocupado"; if (Test-Path $o) { try { $d = Get-Content $o -Raw | ConvertFrom-Json; '
                      '$min = ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - [double]$d.desde) / 60; '
                      'if (-not $d.login -and ($min -gt 45 -or ($meu -and $d.perfil -eq $meu -and $min -gt 2))) { '
                      '& python C:\\postador-worker\\chrome_conta.py fechar $d.porta | Out-Null; '
                      '"FECHOU_VELHO " + $d.perfil + " " + [int]$min + " min" } } catch {} }; '
                      'if (Test-Path $o) { "ABERTO " + (Get-Content $o -Raw | ConvertFrom-Json).perfil } else { "LIVRE_CHROME" }; '
                      '\'OK\'', timeout=90)
        e["_chrome_livre"] = "LIVRE_CHROME" in out  # o passo_colher usa (o maquina_livre era 1 ssh a mais, que cai)
        if "FECHOU_VELHO" in out:
            log("faxina: " + next(l.strip() for l in out.splitlines() if "FECHOU_VELHO" in l))
            e.pop("colhendo", None)
        elif "LIVRE_CHROME" in out:
            e.pop("colhendo", None)
    except subprocess.TimeoutExpired:
        rc, out = -1, "timeout"
    if rc != 0 or "OK" not in out:
        e["falhas_seguidas"] = e.get("falhas_seguidas", 0) + 1
        e.setdefault("fora_desde", agora)
        log(f"ssh não entrou ({' '.join(out.split())[-100:]}) — {e['falhas_seguidas']} seguidas")
        if agora - e["fora_desde"] > AVISO_FORA_H * 3600 and not e.get("avisou_fora"):
            e["avisou_fora"] = True
            _avisar(f"⚠️ Desktop: {AVISO_FORA_H} h sem conseguir entrar por ssh (o sshd de lá derruba a sessão depois de "
                    "aceitar a chave). Plano B: rodar a IA no próprio desktop — guia em "
                    "D:\\video-fila\\linhas\\DESKTOP_PRINCIPAL.md (copiar pelo pendrive ou pelo Drive).")
        _gravar(e)
        return
    if e.get("fora_desde") and agora - e["fora_desde"] > 3 * 3600:
        _avisar(f"🖥️ Desktop: ssh voltou depois de {int((agora - e['fora_desde']) / 3600)} h fora.", importante=False)
    e.update(falhas_seguidas=0, ultimo_ok=time.strftime("%Y-%m-%d %H:%M"), avisou_fora=False)
    e.pop("fora_desde", None)
    time.sleep(20)  # o sshd de lá cai mais com conexões coladas
    try:
        vit = BASE / "vitrine"
        assin = "|".join(_md5(vit / a) for a in ARQS_TELAO)
        if e.get("pendentes"):  # 30/10 10h: comando avulso que não pegou janela boa do ssh — roda na 1ª que pegar
            p = e["pendentes"][0]
            rc2, out2 = _ps(p["script"] + '; "FIM"', timeout=180)
            log(f"pendente '{p['nome']}': " + " | ".join(l.strip() for l in out2.splitlines()
                                                         if l.strip() and not l.lstrip().startswith(("<", "#<")))[-250:])
            if "FIM" in out2:
                e["pendentes"].pop(0)
        elif not e.get("telao") or e["telao"].get("assinatura") != assin:
            passo_telao(e)
            e.pop("telao_conferido", None)
        elif not e.get("telao_conferido"):
            passo_conferir_telao(e)
        elif not e.get("chave"):
            passo_chave(e)
        elif not e.get("nsn"):
            passo_nsn(e)
        elif not e.get("colher_fim"):
            passo_colher(e)
        elif not e.get("saude") or agora - time.mktime(time.strptime(e["saude"]["quando"], "%Y-%m-%d %H:%M")) > 6 * 3600:
            passo_saude(e)
    except Exception as ex:  # noqa: BLE001 — a vigia nunca para
        log(f"passo falhou: {type(ex).__name__}: {str(ex)[:200]}")
    _gravar(e)


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--status" in sys.argv:
        print(json.dumps(_ler(), ensure_ascii=False, indent=1))
        return
    import msvcrt
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    f = open(TRAVA, "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        return  # rodada anterior ainda trabalhando
    rodada()


if __name__ == "__main__":
    main()
