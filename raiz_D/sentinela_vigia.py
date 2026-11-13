r"""sentinela_vigia.py - vigia o sentinela (3ª camada): tarefa do Windows "SentinelaVigia", a cada 10 min.

Dona 30/10/2026: "segundas e terceiras camadas pra ter certeza de chamar". O sentinela_disparo.py grava
D:\sentinela_batimento.json a cada rodada. Esta vigia confere:
  - tarefa SentinelaContinue apagada -> recria pela cópia D:\sentinela_tarefa_continue.xml (guardada a cada rodada);
  - tarefa desligada -> religa; ligada mas sem próxima execução (gatilho quebrado) -> avisa;
  - batimento parado há mais de 15 min -> mata rodada travada (python do sentinela com mais de 15 min) e roda a tarefa;
    avisa no começo, de novo se passar de 1 h parado (com o erro do log) e quando volta ao normal;
  - leitura de crédito falhando 3 rodadas seguidas (ssh da 157) -> avisa a dona, e avisa quando volta.
Cada conserto vai para D:\sentinela_disparo.log e para o Telegram (portão avisos.py).
`--simular`: só confere e escreve no log o que faria, sem mexer em nada nem avisar.
"""
import csv
import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

BATIMENTO = Path(r"D:\sentinela_batimento.json")
LOG = Path(r"D:\sentinela_disparo.log")
ESTADO = Path(r"D:\sentinela_vigia_estado.json")  # incidente aberto: avisa uma vez no começo e uma quando resolve
COPIA_TAREFA = Path(r"D:\sentinela_tarefa_continue.xml")
TAREFA = "SentinelaContinue"
PARADO_MIN = 15
REAVISO_MIN = 60
LEITURA_MAX = 3
LOG_MAX = 5 * 1024 * 1024
LIMITE_S = 240  # a tarefa SentinelaVigia é cortada em 5 min: tudo tem que caber antes disso
OCULTO = getattr(subprocess, "CREATE_NO_WINDOW", 0)
NS = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
SIMULAR = "--simular" in sys.argv
INICIO = time.monotonic()
RESULTADOS = {0x0: "terminou bem", 0x1: "o python deu erro", 0x41301: "está rodando agora",
              0x41306: "foi encerrada (limite de 20 min ou vigia)", 0x8004131F: "já estava rodando",
              0x41303: "ainda não rodou"}


def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} [vigia]{' [simular]' if SIMULAR else ''} {msg}\n")


def avisar(texto, chave, importante):
    if SIMULAR:
        log(f"avisaria: {texto}")
        return
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.append(r"D:\video-fila")  # no fim: pasta de outro projeto nunca na frente do sys.path
        import avisos
        avisos.enviar(f"Sentinela: {texto}", "sentinela-credito", importante=importante, chave=chave, html_ok=False)
    except Exception as falha:  # noqa: BLE001 — o aviso nunca pode parar a vigia
        log(f"aviso do Telegram falhou: {falha!r}")


def resta():
    return LIMITE_S - (time.monotonic() - INICIO)


def rodar(cmd, timeout):
    """(código de saída, stdout+stderr em bytes); código None = não respondeu a tempo."""
    # stdin=DEVNULL: pythonw do Agendador não tem stdin; o filho não herda nada estranho
    try:
        r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, creationflags=OCULTO,
                           timeout=max(5, min(timeout, resta())))
    except subprocess.TimeoutExpired:
        log(f"{cmd[0]} não respondeu a tempo (CPU cheia?): {' '.join(cmd[1:4])}")
        return None, b""
    return r.returncode, r.stdout + r.stderr


def prioridade_normal():
    # o Agendador roda tarefa na prioridade 7 (abaixo do normal) e os filhos herdam: com a CPU a 100% o schtasks
    # passou de 60 s (30/10). Desde 30/10 as tarefas SentinelaVigia/SentinelaContinue têm <Priority>6</Priority>;
    # isto aqui é a segunda camada, se alguém recriar a tarefa sem ela. Normal, não alta: não atrapalha ninguém.
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetPriorityClass(k.GetCurrentProcess(), 0x20)  # NORMAL_PRIORITY_CLASS
    except (AttributeError, OSError):
        pass


def schtasks(*args):
    # schtasks, não PowerShell: com a CPU a 100% o PowerShell levou mais de 90 s só para abrir (30/10)
    rc, saida = rodar(["schtasks", *args], 90)
    return rc, saida.decode("cp850", "replace")


def resultado(cod):
    try:
        n = int(cod) & 0xFFFFFFFF
    except ValueError:
        return cod
    return f"0x{n:X} ({RESULTADOS.get(n, 'código desconhecido')})"


def girar_log():
    try:
        if LOG.stat().st_size > LOG_MAX:
            LOG.replace(LOG.with_name(LOG.name + ".1"))
    except OSError:
        pass  # sem log ainda, ou o sentinela está escrevendo nele agora: gira na próxima


def conferir_tarefa():
    """Recria/religa a tarefa e devolve o último resultado dela ('' se não deu para ler)."""
    rc, xml = schtasks("/Query", "/TN", TAREFA, "/XML")
    if rc is None:
        return ""
    if rc != 0:
        if not COPIA_TAREFA.exists():
            log(f"a tarefa {TAREFA} sumiu e não tenho cópia para recriar: {xml.strip()}")
            avisar(f"a tarefa {TAREFA} sumiu do Windows e a vigia não tem cópia para recriar. Precisa refazer à mão.",
                   f"sentinela-vigia-sumiu-{datetime.now():%Y%m%d}", True)
            return ""
        if not SIMULAR:
            rc, saida = schtasks("/Create", "/TN", TAREFA, "/XML", str(COPIA_TAREFA), "/F")
            schtasks("/Change", "/TN", TAREFA, "/ENABLE")  # a cópia pode ter sido guardada com ela desligada
            schtasks("/Run", "/TN", TAREFA)
        else:
            rc, saida = 0, ""
        log(f"a tarefa {TAREFA} sumiu: recriei pela cópia (rc={rc}) {saida.strip()}")
        avisar(f"a tarefa {TAREFA} tinha sumido do Windows; a vigia recriou pela cópia"
               + ("." if rc == 0 else f", mas o Windows recusou: {saida.strip()[:200]}"),
               f"sentinela-vigia-recriou-{datetime.now():%Y%m%d%H%M}", True)
        return ""
    xml = xml.replace("\r\r\n", "\n").strip()
    try:
        raiz = ET.fromstring(xml.split("?>", 1)[-1])  # o ET não aceita str com a declaração encoding="UTF-16"
    except ET.ParseError as falha:
        log(f"não entendi o XML da tarefa {TAREFA}: {falha}")
        return ""
    try:
        if not SIMULAR and (not COPIA_TAREFA.exists() or COPIA_TAREFA.read_text(encoding="utf-16") != xml + "\n"):
            COPIA_TAREFA.write_text(xml + "\n", encoding="utf-16")  # /Create /XML pede UTF-16
    except OSError as falha:
        log(f"não consegui guardar a cópia da tarefa: {falha!r}")
    if (raiz.findtext("t:Settings/t:Enabled", "true", NS) or "").strip().lower() == "false":
        if not SIMULAR:
            schtasks("/Change", "/TN", TAREFA, "/ENABLE")
        log(f"a tarefa {TAREFA} estava desligada: religuei")
        avisar(f"a tarefa {TAREFA} estava desligada e a vigia religou.",
               f"sentinela-vigia-religou-{datetime.now():%Y%m%d%H%M}", True)
        return ""
    # colunas do CSV /V (a ordem não muda com o idioma): 2 próxima execução, 6 último resultado
    rc, texto = schtasks("/Query", "/TN", TAREFA, "/FO", "CSV", "/NH", "/V")
    linha = next((l for l in texto.splitlines() if l.strip()), "")
    campos = next(csv.reader([linha]), []) if rc == 0 else []
    if len(campos) < 7:
        return ""
    if campos[2].strip().upper() in ("N/A", ""):
        log(f"a tarefa {TAREFA} está ligada mas sem próxima execução marcada (gatilho quebrado?)")
        avisar(f"a tarefa {TAREFA} está ligada mas o Windows não marcou a próxima execução (gatilho quebrado). "
               "A vigia vai rodando ela quando o sentinela passa de 15 min parado, mas precisa consertar o agendamento.",
               f"sentinela-vigia-sem-gatilho-{datetime.now():%Y%m%d}", True)
    return resultado(campos[6].strip())


def travados():
    """PIDs de python rodando o sentinela_disparo.py há mais de PARADO_MIN minutos."""
    limite = datetime.now() - timedelta(minutes=PARADO_MIN)
    # wmic antes do PowerShell: abre bem mais rápido com a CPU cheia
    rc, saida = rodar(["wmic", "process", "where",
                       "name like 'python%' and commandline like '%sentinela_disparo.py%'",
                       "get", "CreationDate,ProcessId", "/format:csv"], 90)
    if rc == 0:
        pids = []
        for linha in saida.decode("cp850", "replace").splitlines():
            partes = linha.strip().split(",")
            if len(partes) == 3 and partes[2].isdigit():
                try:
                    if datetime.strptime(partes[1][:14], "%Y%m%d%H%M%S") < limite:
                        pids.append(partes[2])
                except ValueError:
                    pass
        return pids
    if resta() < 60:
        return []
    rc, saida = rodar(["powershell.exe", "-NoProfile", "-Command",
                       "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' "
                       "-and $_.CommandLine -match 'sentinela_disparo\\.py' "
                       f"-and $_.CreationDate -lt (Get-Date).AddMinutes(-{PARADO_MIN}) }} | "
                       "ForEach-Object { $_.ProcessId }"], resta() - 20)
    return [p for p in saida.decode("utf-8", "replace").split() if p.isdigit()]


def erros_recentes():
    try:
        linhas = LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]
    except OSError:
        return ""
    erros = [l for l in linhas if "ERRO" in l and "[vigia]" not in l]
    return erros[-1][20:220] if erros else ""


def ler_batimento():
    """(batimento, idade em minutos); idade None = não tem batimento legível."""
    try:
        b = json.loads(BATIMENTO.read_text(encoding="utf-8"))
        em = datetime.fromisoformat(b["em"].replace("Z", "+00:00"))
        if em.tzinfo is None:
            em = em.replace(tzinfo=timezone.utc)
        return b, (datetime.now(timezone.utc) - em).total_seconds() / 60
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {}, None


def main():
    prioridade_normal()
    girar_log()
    try:
        estado = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        estado = {}
    ultimo = conferir_tarefa()
    b, idade = ler_batimento()
    agora = datetime.now().isoformat(timespec="seconds")

    if idade is None or idade > PARADO_MIN:
        # rodada travada segura as próximas (a tarefa não começa outra enquanto uma roda)
        mortos = travados()
        if not SIMULAR:
            for pid in mortos:
                rodar(["taskkill", "/T", "/F", "/PID", pid], 30)
            rc, saida = schtasks("/Run", "/TN", TAREFA)
        else:
            rc, saida = 0, ""
        quanto = "nunca" if idade is None else f"há {idade:.0f} min"
        log(f"sentinela sem rodar ({quanto}, último resultado da tarefa: {ultimo or '?'}); "
            f"matei travados [{','.join(mortos)}] e rodei a tarefa (rc={rc})"
            + (f": {saida.strip()[:200]}" if rc != 0 else ""))
        desde = estado.setdefault("parado_desde", agora)
        minutos = (datetime.fromisoformat(agora) - datetime.fromisoformat(desde)).total_seconds() / 60
        if desde == agora:
            avisar(f"o sentinela parou (última rodada {quanto}). A vigia destravou e rodou de novo"
                   + (f" (processos travados encerrados: {', '.join(mortos)})." if mortos else "."),
                   f"sentinela-vigia-parado-{desde}", True)
        elif minutos >= REAVISO_MIN and not estado.get("reavisou"):
            estado["reavisou"] = True
            erro = erros_recentes()
            avisar(f"o sentinela continua parado há {minutos:.0f} min mesmo com a vigia rodando ele de novo. "
                   f"Último resultado da tarefa: {ultimo or '?'}." + (f" Último erro no log: {erro}" if erro else ""),
                   f"sentinela-vigia-parado-{desde}-reaviso", True)
    elif "parado_desde" in estado:
        desde = estado.pop("parado_desde")
        estado.pop("reavisou", None)
        log(f"sentinela voltou ao normal (estava parado desde {desde})")
        avisar(f"o sentinela voltou ao normal (estava parado desde {desde[11:16]}).",
               f"sentinela-vigia-voltou-{desde}", True)

    if idade is not None and idade <= PARADO_MIN:  # batimento velho = erro_leitura velho também
        n = b.get("erro_leitura", 0)
        if n >= LEITURA_MAX and "leitura_desde" not in estado:
            estado["leitura_desde"] = agora
            log(f"leitura de crédito falhando há {n} rodadas (ssh hermes-bloqueio / OmniRoute 157)")
            avisar(f"não consigo ler o crédito no OmniRoute há {n} rodadas (ssh da VPS 157). "
                   "Os chats continuam recebendo pelo último crédito lido.",
                   f"sentinela-vigia-leitura-{agora}", False)
        elif n == 0 and "leitura_desde" in estado:
            desde = estado.pop("leitura_desde")
            log(f"leitura de crédito voltou ao normal (falhava desde {desde})")
            avisar("a leitura de crédito no OmniRoute voltou ao normal.", f"sentinela-vigia-leitura-ok-{desde}", False)

    if not SIMULAR:
        ESTADO.write_text(json.dumps(estado, indent=1), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:  # pythonw não mostra nada
        log(f"ERRO: {erro!r}")
        avisar(f"a vigia do sentinela deu erro: {erro!r}"[:300], f"sentinela-vigia-erro-{datetime.now():%Y%m%d}", True)
        raise
