# -*- coding: utf-8 -*-
"""transferencias.py — trocar uma tarefa de PC pelo painel (kanban das Máquinas, dono 24/10/2026: "quero em
colunas pra poder trocar a tarefa de PC, ex.: colocar no PC3 mesmo sendo a regra de não usar com câmera ligada,
assim posso desafogar um PC que esteja usando na hora; o vigia deve conferir se a transferência funcionou mesmo").

Arrastar = PARA a tarefa no PC de origem e RECOMEÇA no destino (resposta do dono 24/10; o que já tinha sido feito
daquele vídeo se perde). O destino fica FIXO pra aquela tarefa (o controlador não devolve ela pro PC antigo) até o
dono arrastar de novo ou "soltar" (volta à regra normal). Fixo no PC3 passa por cima da regra de OBS/chamada.

Estado: estado/transferencias.json = {"fixos": {tarefa: pc}, "pedidos": [...]}. Situações de um pedido:
  pendente -> disparado -> confirmado | falhou        (ou recusado, quando a troca não é possível)
Quem confere: o vigia_geral (a cada 20 min) e o próprio pedido (2 min depois de disparar). 15 min sem a tarefa
rodando no destino = falhou + aviso de erro no Telegram (portão avisos.py).

    python transferencias.py executar <id>      # o painel chama isto ao soltar o cartão
    python transferencias.py conferir           # o vigia chama
    python transferencias.py estado
"""
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
ESTADO = BASE / "estado" / "transferencias.json"
LOG = BASE / "logs" / "transferencias.log"
CONFIRMAR_MIN = 15
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# tarefa -> rótulo, onde pode rodar e, por PC, as marcas da linha de comando que provam que ela roda lá. As marcas
# do PC1 que aparecem num pedido pro PC2 são o lançador local (o fila.py pc2 / anime_auto --engine worker).
TAREFAS = {
    # 26/10: voz clonada instalada no PC2 (instalar_pc2_cortes.py) — ele entra nos Cortes
    "cortes": {"rotulo": "Cortes: Shorts de parceiro", "pcs": ["pc1", "pc2", "desktop"],
               "marcas": {"pc1": ["parceiro_diario.py producao", "cron_parceiro.bat producao"],
                          "pc2": ["anime_auto.py --modo short"],
                          "desktop": ["parceiro_diario.py producao", "anime_auto.py"]}},
    "hipercool": {"rotulo": "Hipercool: renders do capítulo/línguas", "pcs": ["pc1", "pc2"],
                  "marcas": {"pc1": ["fila.py ciclo", "fila.py faltantes", "hiper-pipeline", "hiper-longo"],
                             "pc2": ["hiper-pipeline", "hiper-longo"]}},
    "anime_longo": {"rotulo": "Anime longo", "pcs": ["pc2", "pc1"],
                    "marcas": {"pc1": ["--engine local"], "pc2": ["anime-pipeline"]}},
    "veo": {"rotulo": "Veo: gerar no Flow", "pcs": ["pc1", "pc2", "desktop", "x200ma", "acer", "sti"],
            "marcas": {"pc1": ["cron_gerar_video_llm.py"]}, "proxima_vez": True},
}
NOMES = {"pc1": "PC1", "pc2": "PC2", "desktop": "PC3 (desktop)", "x200ma": "X200MA", "acer": "Acer", "sti": "STI", "kaggle": "Kaggle", "colab": "Colab"}
PADRAO = {"cortes": "pc1", "hipercool": "pc1", "anime_longo": "pc2", "veo": None}  # None = a cadeia do Veo escolhe


def log(msg):
    LOG.parent.mkdir(exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def ler():
    try:
        d = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    d.setdefault("fixos", {})
    d.setdefault("pedidos", [])
    return d


def gravar(d):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    d["pedidos"] = d["pedidos"][-60:]
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ESTADO)


def fixo(tarefa):
    """PC fixado pelo dono pra essa tarefa, ou None (regra normal)."""
    return ler()["fixos"].get(tarefa)


def _atualizar(pid, **campos):
    d = ler()
    for p in d["pedidos"]:
        if p["id"] == pid:
            p.update(campos)
    gravar(d)


# ─── processos em cada máquina ───────────────────────────────────────────────
def _ps_remoto(host, ps, timeout=60):
    import base64
    import maquinas
    enc = base64.b64encode(ps.encode("utf-16-le")).decode()
    r = subprocess.run([maquinas.SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host,
                        "powershell -NoProfile -EncodedCommand " + enc],
                       capture_output=True, timeout=timeout, creationflags=_SEM_JANELA)
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace")


def processos(host):
    """[(pid, linha de comando)] dos python/cmd da máquina. Levanta erro se não conseguir ler (ssh caiu)."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name like 'python%' or Name='cmd.exe' or Name='wscript.exe'\" | "
          "ForEach-Object { \"$($_.ProcessId)|$($_.Name)|$($_.CommandLine)\" }")
    if host == "pc1":
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=90,
                           encoding="utf-8", errors="replace", creationflags=_SEM_JANELA)
        rc, txt = r.returncode, r.stdout or ""
    else:
        rc, txt = _ps_remoto(host, ps)
    if rc != 0 and not txt.strip():
        raise RuntimeError(f"não consegui ler os processos do {NOMES.get(host, host)} (ssh/powershell rc={rc})")
    out = []
    for linha in txt.splitlines():
        p = linha.split("|", 2)
        if len(p) == 3 and p[0].strip().isdigit():
            out.append((int(p[0]), p[1].strip().lower(), p[2]))
    return out


def rodando(tarefa, host):
    """True/False se a tarefa roda no host; None = não dá pra saber (máquina sem resposta / sem marca)."""
    if host in ("x200ma", "acer", "sti", "desktop", "pc2") and tarefa == "veo":
        try:
            sys.path.insert(0, r"D:\postador-de-videos\bin")
            import maquina_remota
            return "veo" in maquina_remota.reservado(host).lower()
        except Exception:  # noqa: BLE001
            return None
    marcas = TAREFAS[tarefa]["marcas"].get(host)
    if not marcas:
        return None
    try:
        procs = processos(host)
    except Exception:  # noqa: BLE001
        return None
    return any(any(m in cmd for m in marcas) for _pid, _nome, cmd in procs)


def parar(tarefa, host):
    """Mata a tarefa no host (árvore inteira no PC1; no PC2/PC3 só os python.exe da marca — NUNCA pythonw no PC2,
    que são os workers do hipercool). Devolve quantos processos parou."""
    if tarefa == "veo":
        return 0  # o Veo não é morto no meio (gasta crédito do Flow): a próxima geração já vai pro destino
    marcas = list(TAREFAS[tarefa]["marcas"].get(host) or [])
    if tarefa == "hipercool" and host == "pc2":
        marcas_pc1 = ["fila.py pc2"]
    elif tarefa == "anime_longo" and host == "pc2":
        marcas_pc1 = ["--engine worker"]
    else:
        marcas_pc1 = []
    n = 0
    if host == "pc1":
        alvos = [pid for pid, _n, cmd in processos("pc1") if any(m in cmd for m in marcas)]
    else:
        alvos = [pid for pid, nome, cmd in processos(host) if nome == "python.exe" and any(m in cmd for m in marcas)]
        if alvos:
            _ps_remoto(host, "; ".join(f"Stop-Process -Id {p} -Force -ErrorAction SilentlyContinue" for p in alvos))
            n += len(alvos)
        alvos = [pid for pid, _n, cmd in processos("pc1") if any(m in cmd for m in marcas_pc1)] if marcas_pc1 else []
    for pid in alvos:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, creationflags=_SEM_JANELA)
        n += 1
    log(f"parar {tarefa} no {host}: {n} processo(s)")
    return n


# ─── disparar no destino ─────────────────────────────────────────────────────
def disparar(tarefa, host):
    """Dispara a tarefa no host passando por cima da regra de ocupado (o dono mandou). Devolve texto do que fez;
    levanta RuntimeError quando não tem como."""
    import controlador
    if tarefa == "cortes" and host == "pc1":
        return controlador._cortes_pc1()[2]
    if tarefa == "cortes" and host == "desktop":
        import ocioso
        ocioso.log = log
        if not ocioso.pc3_instalado():
            raise RuntimeError("o Cortes ainda não está instalado no PC3 (ou o ssh dele recusou): instalar_pc3.py / tarefa InstalarPC3")
        return ocioso.disparar_parceiro_pc3()
    if tarefa == "cortes" and host == "pc2":
        import ocioso
        ocioso.log = log
        if not ocioso._disparar_parceiro_pc2():
            raise RuntimeError("o PC2 não aceitou o Short agora (sem vídeo na fila, download falhou ou PC2 fora)")
        return "Cortes: Short de parceiro no PC2"
    if tarefa == "hipercool" and host == "pc1":
        return controlador._hipercool_pc1("faltantes")[2]
    if tarefa == "hipercool" and host == "pc2":
        return controlador._hipercool_pc2()[2]
    if tarefa == "anime_longo" and host == "pc2":
        import ocioso
        ocioso.log = log
        if not ocioso.disparar_anime_longo():
            raise RuntimeError("o PC2 não aceitou o anime longo agora (worker ocupado ou fora do ar)")
        return "anime longo no PC2"
    if tarefa == "anime_longo" and host == "pc1":
        return controlador._anime_longo_pc1()[2]
    if tarefa == "veo":
        return f"Veo: próxima geração vai primeiro pro {NOMES[host]} (cadeia_veo lê o fixo)"
    raise RuntimeError(f"{TAREFAS[tarefa]['rotulo']} não roda no {NOMES.get(host, host)}")


# ─── pedido (painel) ─────────────────────────────────────────────────────────
def pedir(tarefa, de, para):
    """Valida e registra. Devolve o pedido (dict); situacao 'recusado' quando não é possível."""
    t = TAREFAS.get(tarefa)
    p = {"id": uuid.uuid4().hex[:8], "tarefa": tarefa, "de": de, "para": para,
         "pedido_em": datetime.now().isoformat(timespec="seconds"), "situacao": "pendente", "detalhe": ""}
    if not t:
        p.update(situacao="recusado", detalhe=f"tarefa desconhecida: {tarefa}")
    elif para not in t["pcs"]:
        p.update(situacao="recusado", detalhe=(t.get("nao") or {}).get(para) or
                 f"{t['rotulo']} não roda no {NOMES.get(para, para)} (só {', '.join(NOMES[x] for x in t['pcs'])})")
    d = ler()
    if p["situacao"] == "pendente":
        d["fixos"][tarefa] = para
    d["pedidos"].append(p)
    gravar(d)
    log(f"pedido {p['id']}: {tarefa} {de} -> {para} ({p['situacao']} {p['detalhe']})")
    return p


def soltar(tarefa):
    """Volta a tarefa à regra normal do controlador."""
    d = ler()
    d["fixos"].pop(tarefa, None)
    gravar(d)
    log(f"soltar {tarefa}: volta à regra normal")


def executar(pid):
    p = next((x for x in ler()["pedidos"] if x["id"] == pid), None)
    if not p or p["situacao"] != "pendente":
        return
    try:
        estava = rodando(p["tarefa"], p["de"]) if p["de"] in NOMES else None
        parados = parar(p["tarefa"], p["de"]) if estava else 0
        if parados:
            time.sleep(5)
        feito = disparar(p["tarefa"], p["para"])
        _atualizar(pid, situacao="disparado", disparado_em=datetime.now().isoformat(timespec="seconds"),
                   detalhe=f"{'parou ' + str(parados) + ' processo(s) no ' + NOMES.get(p['de'], p['de']) + '; ' if parados else ''}{feito}")
    except Exception as e:  # noqa: BLE001
        _atualizar(pid, situacao="falhou", detalhe=f"{type(e).__name__}: {e}"[:300])
        _avisar_falha({**p, "detalhe": str(e)})
        return
    time.sleep(120)
    conferir()


# ─── conferência (vigia) ─────────────────────────────────────────────────────
def _avisar_falha(p):
    try:
        import avisos
        avisos.enviar(f"<b>Troca de PC não funcionou</b>\n{TAREFAS.get(p['tarefa'], {}).get('rotulo', p['tarefa'])}: "
                      f"{NOMES.get(p['de'], p['de'])} → {NOMES.get(p['para'], p['para'])}\n{p.get('detalhe', '')[:300]}",
                      "vigia", importante=True, chave=f"transferencia_{p['id']}")
    except Exception as e:  # noqa: BLE001
        log(f"[!] aviso da falha não saiu: {e}")


def conferir():
    """Confere os pedidos disparados: rodando no destino = confirmado; 15 min sem rodar = falhou (+ aviso).
    Devolve a lista de textos de problema (o vigia_geral junta nos problemas dele)."""
    problemas = []
    for p in [x for x in ler()["pedidos"] if x["situacao"] == "disparado"]:
        if TAREFAS.get(p["tarefa"], {}).get("proxima_vez"):
            _atualizar(p["id"], situacao="confirmado", conferido_em=datetime.now().isoformat(timespec="seconds"),
                       detalhe=p["detalhe"] + " | fixo gravado (vale na próxima geração)")
            continue
        r = rodando(p["tarefa"], p["para"])
        idade = (datetime.now() - datetime.fromisoformat(p["disparado_em"])).total_seconds() / 60
        if r:
            _atualizar(p["id"], situacao="confirmado", conferido_em=datetime.now().isoformat(timespec="seconds"))
            log(f"conferido {p['id']}: {p['tarefa']} rodando no {p['para']}")
        elif idade >= CONFIRMAR_MIN:
            det = ("não deu pra ler os processos do destino" if r is None else "a tarefa não está rodando no destino")
            _atualizar(p["id"], situacao="falhou", detalhe=f"{p['detalhe']} | {det} {idade:.0f} min depois")
            _avisar_falha({**p, "detalhe": det})
            problemas.append(f"troca de PC falhou: {p['tarefa']} {p['de']} -> {p['para']} ({det})")
    return problemas


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if a[:1] == ["executar"] and len(a) > 1:
        executar(a[1])
    elif a[:1] == ["conferir"]:
        print(conferir())
    else:
        print(json.dumps(ler(), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
