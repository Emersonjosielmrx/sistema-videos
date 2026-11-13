# -*- coding: utf-8 -*-
"""
========================================================================
supervisor.py  —  Controlador de recursos dos 3 ambientes Veo/Flow
========================================================================

A REGRA (definida pela dona, fixa e importante):
- Ambientes tem PRIORIDADE: prod(1) > beta(2) > experimental(3) (ver ambientes.json).
- Enquanto ha FOLGA, rodam todos os ambientes ativos.
- Faltando recurso (apertado): pausa o de MENOR prioridade ativo (experimental).
- Faltando mais (critico): pausa tambem a beta, deixa rodar 1 teste na
  experimental e RELIGA a live (beta) assim que o teste acabar.
- A LIVE (o ativo de maior prioridade) NUNCA fica parada, exceto a janela
  de 1 teste no caso critico.

Como liga/pausa: cada ambiente e um loop `run_cron_loop_3contas.bat` na sua
pasta. Ligar = Start-Process do .bat. Pausar = criar `logs/PAUSE_SYSTEM` no
ambiente (o worker checa e aborta antes de abrir Chrome) + matar os Chromes/loop
daquele ambiente. Reaproveita a mesma flag de pausa que o gera_auto.py ja le.

Uso:
    python supervisor.py            # 1 avaliacao agora (liga/pausa conforme carga)
    python supervisor.py --loop     # fica supervisionando (default a cada 60s)
    python supervisor.py status     # mostra o estado atual de cada ambiente
"""
import os, sys, json, time, datetime, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "beta"))
import sem_janela  # noqa: F401,E402  (powershell/cron filhos sem janela na tela - dono, 15/10; item BX-02, 16/10)

BASE = os.path.dirname(os.path.abspath(__file__))  # D:\veo
AMBIENTES_JSON = os.path.join(BASE, "ambientes.json")

sys.path.insert(0, BASE)
try:
    import recursos  # usa o mesmo sensor dos ambientes (copiado em cada pasta)
except Exception:
    # fallback: importa da beta (todas as copias sao iguais)
    sys.path.insert(0, os.path.join(BASE, "beta"))
    import recursos


def _log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [supervisor] {msg}", flush=True)


def carregar_ambientes():
    with open(AMBIENTES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    ambs = [a for a in data["ambientes"] if a.get("ativo")]
    ambs.sort(key=lambda a: a["prioridade"])  # prod, beta, experimental
    return ambs


def pasta_de(amb):
    return os.path.join(BASE, amb["pasta"])


def pause_file_de(amb):
    return os.path.join(pasta_de(amb), "logs", "PAUSE_SYSTEM")


# ------------------------------------------------------------------
# Deteccao: um ambiente esta "rodando" se ha um cmd.exe do loop cujo
# working dir e a pasta desse ambiente (identificamos pela pasta no cmdline).
# ------------------------------------------------------------------
def _ps(cmd, timeout=30):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                          capture_output=True, text=True, timeout=timeout)


def loop_rodando(amb):
    """True se ha loop/cron/gera_auto rodando cuja cmdline cita a pasta do ambiente.

    Cada ambiente vive em pasta propria (beta/experimental/prod), entao o nome da
    pasta no CommandLine identifica a qual ambiente o processo pertence.
    """
    marca = "\\\\" + amb["pasta"] + "\\\\"  # ex.: \\beta\\  (evita casar 'beta' solto)
    cmd = (
        "(Get-CimInstance Win32_Process | Where-Object { "
        "($_.CommandLine -match 'run_cron_loop_3contas' -or $_.CommandLine -match 'cron_gerar_video_llm') "
        "-and $_.CommandLine -match '" + marca + "' }).Count"
    )
    try:
        out = _ps(cmd).stdout.strip().splitlines()
        n = int(out[-1]) if out and out[-1].strip().isdigit() else 0
        return n > 0
    except Exception:
        return False


def ligar(amb):
    """Sobe o loop do ambiente (remove pausa antes)."""
    pf = pause_file_de(amb)
    if os.path.exists(pf):
        os.remove(pf)
    if loop_rodando(amb):
        return  # ja esta de pe
    bat = os.path.join(pasta_de(amb), "run_cron_loop_3contas.bat")
    headless = "1" if amb.get("headless") else "0"
    cmd = (f"$env:FLOW_HEADLESS='{headless}'; "
           f"Start-Process -FilePath '{bat}' -WorkingDirectory '{pasta_de(amb)}' -WindowStyle Minimized")
    _ps(cmd)
    _log(f"LIGOU {amb['nome']} (headless={headless})")


def pausar(amb, motivo="carga"):
    """Cria PAUSE_SYSTEM no ambiente + mata Chromes/loop dele."""
    pf = pause_file_de(amb)
    os.makedirs(os.path.dirname(pf), exist_ok=True)
    with open(pf, "w", encoding="utf-8") as f:
        json.dump({"until": None, "motivo": motivo,
                   "por": "supervisor",
                   "criado_em": datetime.datetime.now().isoformat()}, f)
    # mata o loop .bat e o cron/gera_auto que citam a pasta do ambiente
    cmd = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "($_.CommandLine -match 'run_cron_loop_3contas' -or $_.CommandLine -match 'cron_gerar_video_llm' "
        "-or $_.CommandLine -match 'gera_auto') -and $_.CommandLine -match '" + amb["pasta"] + "' } | "
        "ForEach-Object { taskkill /PID $_.ProcessId /T /F 2>&1 | Out-Null }"
    )
    _ps(cmd)
    _log(f"PAUSOU {amb['nome']} ({motivo})")


def _notifica(titulo, msg):
    try:
        sys.path.insert(0, os.path.join(BASE, "beta"))
        from notifica import avisar_desktop
        avisar_desktop(titulo, msg)
    except Exception:
        pass


# ------------------------------------------------------------------
# A REGRA
# ------------------------------------------------------------------
def avaliar_uma_vez():
    ambs = carregar_ambientes()
    if not ambs:
        _log("nenhum ambiente ativo em ambientes.json")
        return
    nivel = recursos.nivel_carga()
    live = ambs[0]                 # maior prioridade ativa (a que nunca para)
    secundarios = ambs[1:]         # os demais, do mais pro menos importante
    _log(f"{recursos.resumo()}")

    if nivel in ("folgado", "medio"):
        # folga: liga todos os ativos
        for a in ambs:
            ligar(a)
        return

    if nivel == "apertado":
        # pausa o(s) de menor prioridade; mantem a live e, se der, os do meio.
        # Regra simples: mantem so a live rodando; pausa o resto.
        ligar(live)
        for a in secundarios:
            pausar(a, motivo="apertado")
        return

    # critico: pausa TODOS (inclusive a live), roda 1 teste na experimental,
    # e religa a live assim que o teste acabar.
    if nivel == "critico":
        exp = next((a for a in ambs if a["nome"] == "experimental"), None)
        _log("CRITICO — pausando tudo, rodando 1 teste na experimental, depois religa a live")
        for a in ambs:
            pausar(a, motivo="critico")
        _notifica("Veo: recurso critico", "pausei tudo, 1 teste na experimental e religo a live")
        if exp:
            _rodar_um_teste(exp)
        # religa a live (a experimental volta a ser gerida no proximo ciclo do --loop)
        ligar(live)
        _log(f"RELIGOU a live ({live['nome']}) apos o teste")
        return


def _rodar_um_teste(exp):
    """Roda 1 unico ciclo do cron da experimental (sincrono), sem loop."""
    pf = pause_file_de(exp)
    if os.path.exists(pf):
        os.remove(pf)  # libera pra esse 1 ciclo
    py = os.path.join(BASE, "venv", "Scripts", "python.exe")
    cron = os.path.join(pasta_de(exp), "cron_gerar_video_llm.py")
    try:
        _log(f"rodando 1 teste na experimental...")
        subprocess.run([py, "-u", cron], cwd=pasta_de(exp), timeout=1800)
    except subprocess.TimeoutExpired:
        _log("teste da experimental estourou 30min — seguindo")
    except Exception as e:
        _log(f"teste da experimental falhou: {str(e)[:80]}")


def status():
    ambs_all = json.load(open(AMBIENTES_JSON, encoding="utf-8"))["ambientes"]
    _log(recursos.resumo())
    for a in ambs_all:
        ativo = "ativo" if a.get("ativo") else "OFF"
        pausado = os.path.exists(os.path.join(BASE, a["pasta"], "logs", "PAUSE_SYSTEM"))
        rod = loop_rodando(a) if a.get("ativo") else False
        print(f"  [{a['prioridade']}] {a['nome']:<12} {ativo:<5} "
              f"{'RODANDO' if rod else 'parado':<8} {'(pausado)' if pausado else ''}")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "status":
        status()
    elif arg == "--loop":
        _log("supervisor em loop (Ctrl+C pra parar)")
        while True:
            try:
                avaliar_uma_vez()
            except Exception as e:
                _log(f"erro no ciclo: {str(e)[:120]}")
            time.sleep(60)
    else:
        avaliar_uma_vez()


if __name__ == "__main__":
    main()
