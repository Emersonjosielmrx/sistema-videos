#!/usr/bin/env python3
"""workers.py - mandar trabalho para outro PC da Tailscale (Onda 4.1 do plano geral, 16/10).

Generaliza D:\\hipercool-videos\\bin\\pc2.py (que e amarrado ao hipercool) para qualquer projeto:
  no_ar(host)                         ssh responde?
  livre(host)                         pode receber trabalho agora? (no desktop: o dono NAO esta gravando - OBS
                                      fechado - e a CPU esta folgada; no pc2: nunca, ver abaixo)
  enviar(host, base, nomes, destino)  arquivos/pastas (relativos a base) -> destino remoto, por tar dentro do ssh
  baixar(host, origem, nomes, destino)
  sincronizar(host, pasta_local, pasta_remota)  so o que mudou (tamanho/data), como o sincronizar_bin do pc2.py
  disparar(host, comando, log_remoto) processo DESLIGADO da sessao ssh (Win32_Process.Create via CIM): continua
                                      rodando depois que o ssh fecha; devolve o PID
  rodando(host, pid) / ler(host, arquivo)
  2 falhas seguidas no mesmo host -> pausa de 6 h (config/workers_estado.json), como o "desiste apos 2 falhas".

Hosts em HOSTS. O PC2 e do hipercool (regra do dono: nao mexer nos workers/pastas de la, NUNCA matar pythonw):
aqui ele so tem leitura de estado (so_status) - trabalho para ele vai pela fila do proprio hipercool.

Uso rapido: python bin/workers.py status        |   python bin/workers.py teste desktop
"""
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ESTADO = ROOT / "config" / "workers_estado.json"
HOSTS = {
    # desktop-su00b7v (100.73.7.19): i5 2 nucleos, sem GPU, onde o dono GRAVA o manhwa-react -> so tarefa leve e so
    # com o OBS fechado. Shell remoto = PowerShell 5 (separar comandos com ';', nunca '&&').
    "desktop": {"ssh": "desktop", "shell": "powershell", "base": "C:/workers", "cpu_max": 50, "so_status": False},
    "pc2": {"ssh": "pc2", "shell": "cmd", "base": None, "cpu_max": 0, "so_status": True},
}
PAUSA_H = 6


def _estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _registrar(host, ok):
    st = _estado()
    h = st.setdefault(host, {})
    h["falhas"] = 0 if ok else h.get("falhas", 0) + 1
    if h["falhas"] >= 2:
        h["pausado_ate"] = (datetime.now() + timedelta(hours=PAUSA_H)).isoformat(timespec="minutes")
        h["falhas"] = 0
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def pausado(host):
    h = _estado().get(host, {})
    return any(h.get(k) and datetime.now() < datetime.fromisoformat(h[k]) for k in ("pausado_ate", "descanso_ate"))


DESCANSO_MIN = {"desktop": 12}


def descansar(host):
    """Fim de job: o host fica de folga. 16/10: depois de CADA job de teste (tar + processo por WMI) o OpenSSH 7.7 do
    desktop recusou toda conexao por ~10 min (3 vezes, mesmo com 8 conexoes espacadas) - causa nao achada com ele
    fora do ar. Ate o dono atualizar o OpenSSH Server de la, 1 job e depois folga."""
    minutos = DESCANSO_MIN.get(host)
    if minutos:
        st = _estado()
        st.setdefault(host, {})["descanso_ate"] = (datetime.now() + timedelta(minutes=minutos)).isoformat(timespec="minutes")
        ESTADO.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


_ULTIMA = {}
ESPACO_S = 3  # entre conexoes ao mesmo host


def ssh(host, cmd, timeout=120, entrada=None):
    """1 conexao. 16/10: ~13 conexoes em ~70 s fizeram o OpenSSH 7.7 do desktop recusar TUDO por ~8 min (reset logo
    depois da troca de chaves) - por isso o espaco minimo entre conexoes e o modulo junta comandos sempre que da."""
    espera = ESPACO_S - (time.time() - _ULTIMA.get(host, 0))
    if espera > 0:
        time.sleep(espera)
    try:
        return subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOSTS[host]["ssh"], cmd],
                              capture_output=True, timeout=timeout, input=entrada)
    finally:
        _ULTIMA[host] = time.time()


def _txt(r):
    return (r.stdout or b"").decode("utf-8", "replace").strip()


def no_ar(host):
    try:
        return ssh(host, "echo ok", timeout=30).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def livre(host):
    """(pode, motivo). Desktop: OBS fechado e CPU abaixo de cpu_max. PC2: nunca (so leitura)."""
    h = HOSTS[host]
    if h["so_status"]:
        return False, "so leitura de estado (regra do dono)"
    if pausado(host):
        h = _estado().get(host, {})
        return False, f"pausado/descansando ate {h.get('descanso_ate') or h.get('pausado_ate')}"
    try:  # 1 conexao so (sem o no_ar separado)
        r = ssh(host, "if (Get-Process obs64,obs32 -ErrorAction SilentlyContinue) {'GRAVANDO'} else {'livre'}; "
                      "[math]::Round((Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average)")
    except subprocess.TimeoutExpired:
        return False, "fora do ar"
    if r.returncode != 0:
        return False, "fora do ar"
    linhas = _txt(r).splitlines()
    if not linhas or linhas[0].strip() == "GRAVANDO":
        return False, "o dono esta gravando (OBS aberto)"
    cpu = int(linhas[-1]) if linhas[-1].strip().isdigit() else 100
    return (cpu <= h["cpu_max"], f"CPU {cpu}%")


def _lista(nomes):
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8", newline="\n")
    f.write("".join(n + "\n" for n in nomes))
    f.close()
    return f.name


def enviar(host, base, nomes, destino):
    """Arquivos/pastas (relativos a base) -> destino remoto (criado se faltar). tar -T: sem limite de linha de comando."""
    if not nomes:
        return True
    ssh(host, f"New-Item -ItemType Directory -Force '{destino}' | Out-Null" if HOSTS[host]["shell"] == "powershell"
        else f'mkdir "{destino}"')
    lista = _lista(nomes)
    try:
        tar = subprocess.Popen(["tar", "-cf", "-", "-C", str(base), "-T", lista], stdout=subprocess.PIPE)
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", HOSTS[host]["ssh"], f"tar -xf - -C {destino}"],
                           stdin=tar.stdout, capture_output=True, timeout=3600)
        tar.stdout.close()
        ok = tar.wait() == 0 and r.returncode == 0
    finally:
        Path(lista).unlink(missing_ok=True)
    _registrar(host, ok)
    return ok


def baixar(host, origem, nomes, destino):
    """Arquivos de origem (pasta remota) -> destino local. A lista vai pelo stdin (o cmd/PowerShell de la corta linha)."""
    if not nomes:
        return True
    Path(destino).mkdir(parents=True, exist_ok=True)
    lista = _lista(nomes)
    try:
        with open(lista, "rb") as f:
            rem = subprocess.Popen(["ssh", "-o", "BatchMode=yes", HOSTS[host]["ssh"], f"tar -cf - -C {origem} -T -"],
                                   stdin=f, stdout=subprocess.PIPE)
        r = subprocess.run(["tar", "-xf", "-", "-C", str(destino)], stdin=rem.stdout, capture_output=True, timeout=3600)
        rem.stdout.close()
        ok = rem.wait() == 0 and r.returncode == 0
    finally:
        Path(lista).unlink(missing_ok=True)
    _registrar(host, ok)
    return ok


def _remotos(host, pasta):
    """{nome: (tamanho, data unix)} da pasta remota (PowerShell)."""
    r = ssh(host, f"Get-ChildItem -File '{pasta}' -ErrorAction SilentlyContinue | ForEach-Object "
                  "{ $_.Name + '|' + $_.Length + '|' + [int][double]::Parse((Get-Date $_.LastWriteTimeUtc -UFormat %s)) }")
    out = {}
    for l in _txt(r).splitlines():
        p = l.rsplit("|", 2)
        if len(p) == 3 and p[1].isdigit():
            out[p[0]] = (int(p[1]), int(float(p[2])))
    return out


def sincronizar(host, pasta_local, pasta_remota, filtro=lambda p: not p.name.startswith(("_", ".")) and ".bak" not in p.name):
    """Manda so o que mudou (tamanho diferente ou mais novo aqui). Devolve (ok, recado)."""
    local = {p.name: (p.stat().st_size, int(p.stat().st_mtime)) for p in Path(pasta_local).iterdir()
             if p.is_file() and filtro(p)}
    remoto = _remotos(host, pasta_remota)
    mudou = sorted(n for n, (t, d) in local.items() if n not in remoto or remoto[n][0] != t or d > remoto[n][1] + 2)
    if not mudou:
        return True, f"{host}: {pasta_remota} ja igual ({len(local)} conferidos)"
    ok = enviar(host, pasta_local, mudou, pasta_remota)
    return ok, f"{host}: {len(mudou)} arquivo(s) {'copiados' if ok else 'FALHOU copiar'} para {pasta_remota}"


def disparar(host, comando, log_remoto):
    """Comando (linha do cmd.exe) num processo DESLIGADO da sessao ssh, saida em log_remoto. Devolve o PID ou None."""
    if HOSTS[host]["so_status"]:
        raise PermissionError(f"{host}: so leitura de estado")
    log_win = log_remoto.replace("/", "\\")
    if " " in log_win:  # o cmd.exe nao aceita \" como aspas escapadas (1o teste de 16/10: log vazio): caminho sem espaco
        raise ValueError(f"log_remoto com espaco: {log_remoto}")
    linha = f'cmd /c "{comando} > {log_win} 2>&1"'.replace("'", "''")
    r = ssh(host, f"$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{{CommandLine='{linha}'}}; "
                  "'' + $r.ReturnValue + '|' + $r.ProcessId")
    rv, _, pid = _txt(r).partition("|")
    ok = rv.strip() == "0" and pid.strip().isdigit()
    _registrar(host, ok)
    return int(pid) if ok else None


def esperar(host, pid, timeout_s=600):
    """Espera o processo acabar DO LADO DE LA (Wait-Process), numa conexao so. True = acabou."""
    r = ssh(host, f"Wait-Process -Id {int(pid)} -Timeout {int(timeout_s)} -ErrorAction SilentlyContinue; "
                  f"if (Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue) {{'rodando'}} else {{'acabou'}}",
            timeout=timeout_s + 60)
    return _txt(r).endswith("acabou")


def rodando(host, pid):
    return _txt(ssh(host, f"if (Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue) {{'sim'}} else {{'nao'}}")) == "sim"


def ler(host, arquivo):
    return _txt(ssh(host, f"Get-Content -Raw -Encoding UTF8 '{arquivo}' -ErrorAction SilentlyContinue"))


def _teste(host):
    """Ida e volta de verdade: envia um script, dispara desligado, espera, le o log e traz o resultado."""
    base = HOSTS[host]["base"]
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "eco.py").write_text("import sys, time, platform\ntime.sleep(3)\n"
                                   "open('eco_saida.txt','w').write('ok de ' + platform.node())\nprint('rodou')\n",
                                   encoding="utf-8")
        print("livre:", livre(host))
        ok, recado = sincronizar(host, td, f"{base}/teste")
        print(recado)
        pid = disparar(host, f"cd /d {base.replace('/', chr(92))}\\teste && python eco.py", f"{base}/teste/eco.log")
        print("pid:", pid)
        print("acabou:", esperar(host, pid, 120) if pid else None)  # 1 conexao, espera do lado de la
        print("log remoto:", ler(host, f"{base}/teste/eco.log"))
        print("trouxe:", baixar(host, f"{base}/teste", ["eco_saida.txt"], td / "volta"),
              (td / "volta" / "eco_saida.txt").read_text(encoding="utf-8") if (td / "volta" / "eco_saida.txt").exists() else "-")
        descansar(host)


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if a[:1] == ["teste"] and len(a) == 2:
        _teste(a[1])
    else:
        for h in HOSTS:
            print(f"{h:8} no ar: {no_ar(h)} | pausado: {pausado(h)} | " + (f"livre: {livre(h)}" if not HOSTS[h]['so_status'] else "so leitura"))
