# -*- coding: utf-8 -*-
"""
========================================================================
monitor_recursos.py  —  Cron de retomada automatica do bot Veo/Flow
========================================================================

Pra que serve:
- O bot se pausa quando a maquina esta afogada (RAM/CPU alta) com PAUSE_SYSTEM
  sem prazo ("ate recurso voltar").
- Este monitor roda periodicamente (via agendador do Windows a cada ~15min OU
  pelo run_monitor_recursos.bat no loop) e religa o bot quando:
    a) a maquina voltou a ter folga (RAM livre subiu, CPU caiu), OU
    b) passou das 0h Brasil (janela noturna — dona dorme, sem disputa).

Tambem aproveita a folga pra ENCHER a fila de prompts prontos (so LLM, barato),
assim quando o Flow voltar a renderizar ja tem trabalho pronto.

Uso:
    python monitor_recursos.py             # uma checagem agora
    python monitor_recursos.py --loop      # loop a cada 15min ate Ctrl+C
"""
import os, sys, json, datetime, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PAUSE_FILE = os.path.join(BASE, "logs", "PAUSE_SYSTEM")


def _log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _pausa_pra_recurso():
    """True se ha PAUSE_SYSTEM sem until (pausa por carga, so religa o monitor)."""
    if not os.path.exists(PAUSE_FILE):
        return False
    try:
        with open(PAUSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("until") is None
    except Exception:
        return False


def _janela_noturna():
    """True se estamos depois da meia-noite local (a dona dorme)."""
    return datetime.datetime.now().hour >= 0  # 0h-23h sempre ok; ajuste se quiser


def _disco_ok():
    import recursos
    return recursos.disco_ok() and recursos.slots_por_recurso() >= 1


def _remover_pausa():
    if os.path.exists(PAUSE_FILE):
        os.remove(PAUSE_FILE)
        _log("PAUSE_SYSTEM removido — sistema religado")


def _tem_loop_rodando():
    """True se o .bat de loop esta rodando (procura por 3contas no cmdline)."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match '3contas|loop_cron' }).ProcessId"],
            capture_output=True, text=True, timeout=20).stdout
        return out.strip()
    except Exception:
        return False


def _religar_loop(headless=True):
    """Sobe o run_cron_loop_3contas.bat com FLOW_HEADLESS conforme o parametro."""
    env = os.environ.copy()
    env["FLOW_HEADLESS"] = "1" if headless else "0"
    subprocess.Popen(
        ["cmd", "/c", "start", "", "run_cron_loop_3contas.bat"],
        cwd=BASE, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _log(f"loop religado em modo {'invisivel' if headless else 'visivel'}")


def _encher_fila():
    """Enche a fila de prompts via comando CLI do orquestrador (so LLM)."""
    try:
        subprocess.run(
            [sys.executable, os.path.join(BASE, "cron_gerar_video_llm.py"), "encher_fila"],
            cwd=BASE, timeout=120)
    except Exception as e:
        _log(f"encher_fila falhou: {str(e)[:80]}")


def checar_uma_vez():
    """Uma checagem completa: decide se religa o bot e/ou enche a fila."""
    import recursos

    # 1) sistema pausado POR CARGA (PAUSE_SYSTEM sem until)?
    if not _pausa_pra_recurso():
        # Nao pausado por carga. Aproveita e ve se fila precisa encher.
        try:
            import fila
            if fila.precisa_encher():
                _log(f"fila abaixo do minimo ({fila.tamanho()}/{fila.FILA_MIN}) — enchendo")
                _encher_fila()
        except Exception as e:
            _log(f"cheque de fila falhou: {str(e)[:80]}")
        return False  # nada pra religar

    # 2) pausado por carga. Recurso voltou OU virou noite?
    resumo = recursos.resumo()
    nivel = recursos.nivel_carga()
    noturna = _janela_noturna()
    disco = recursos.disco_ok()

    _log(f"pausado por carga | {resumo} | noturna={noturna}")
    if (nivel in ("folgado", "medio") or noturna) and disco and recursos.slots_por_recurso() >= 1:
        _remover_pausa()
        # notifica e religa em modo invisivel (mais leve, deixa a maquina livre)
        try:
            from notifica import avisar_desktop
            avisar_desktop("Veo: retomei a producao", f"{nivel} + janela noturna" if noturna else nivel)
        except Exception:
            pass
        if not _tem_loop_rodando():
            _religar_loop(headless=True)
        # aproveita a folga pra encher a fila
        try:
            import fila
            if fila.precisa_encher():
                _encher_fila()
        except Exception:
            pass
        return True
    _log(f"ainda sem folga ({nivel}) — esperando...")
    return False


def main():
    args = sys.argv[1:]
    if "--loop" in args:
        import time
        _log("monitor_recursos em loop (Ctrl+C pra parar)")
        while True:
            try:
                checar_uma_vez()
            except Exception as e:
                _log(f"erro no ciclo: {str(e)[:120]}")
            time.sleep(15 * 60)  # 15min
    else:
        checar_uma_vez()


if __name__ == "__main__":
    main()