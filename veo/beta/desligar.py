# -*- coding: utf-8 -*-
"""
desligar.py  —  Desliga o bot Veo/Flow DE VERDADE.

1) cria PAUSE_SYSTEM manual (o worker checa e aborta antes de abrir Chrome);
2) mata os Chromes do bot (por porta das contas);
3) mata o loop .bat / python do cron, se estiver rodando.

Chamado pelo botao "Veo — DESLIGAR" do desktop.
"""
import os, sys, json, datetime, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PAUSE_FILE = os.path.join(BASE, "logs", "PAUSE_SYSTEM")


def _log(m):
    print(f"[{datetime.datetime.now():%H:%M:%S}] {m}", flush=True)


def criar_pausa_manual():
    os.makedirs(os.path.dirname(PAUSE_FILE), exist_ok=True)
    with open(PAUSE_FILE, "w", encoding="utf-8") as f:
        json.dump({"until": None, "motivo": "manual",
                   "criado_em": datetime.datetime.now().isoformat()}, f)
    _log("PAUSE_SYSTEM manual criado — worker vai abortar antes de abrir Chrome")


def matar_chromes():
    """Reusa a rotina do orquestrador se der; senao mata Chrome de perfil do bot."""
    try:
        import cron_gerar_video_llm as cron
        if hasattr(cron, "matar_chromes_do_bot"):
            cron.matar_chromes_do_bot()
            _log("Chromes do bot encerrados (via orquestrador)")
            return
    except Exception as e:
        _log(f"nao usei o orquestrador ({str(e)[:60]}); indo pelo perfil")
    # fallback: mata Chrome que usa perfil chrome_gen_ (os do bot)
    ps = ("Get-CimInstance Win32_Process | "
          "Where-Object { $_.CommandLine -match 'chrome_gen_|remote-debugging-port=925' } | "
          "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], timeout=30)
    _log("Chromes do bot encerrados (fallback por perfil)")


def matar_loop():
    """Mata o .bat de loop e o python do cron (pra nao reabrir Chrome)."""
    ps = ("Get-CimInstance Win32_Process | "
          "Where-Object { $_.CommandLine -match 'cron_gerar_video_llm|run_cron_loop_3contas|CronVeoLLM' } | "
          "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], timeout=30)
    _log("loop/cron encerrados")


def main():
    criar_pausa_manual()
    matar_chromes()
    if "--keep-loop" not in sys.argv:
        matar_loop()
    try:
        from notifica import avisar_desktop
        avisar_desktop("Veo: DESLIGADO", "producao pausada manualmente")
    except Exception:
        pass
    _log("desligado.")


if __name__ == "__main__":
    main()
