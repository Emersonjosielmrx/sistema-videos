# -*- coding: utf-8 -*-
"""
acesso_total.py  —  Modo "acesso total" ao navegador

A dona LIGA este modo quando NAO esta usando o Chrome pra nada pessoal.
Com ele ligado, o bot pode:
  - fechar os Chromes OCIOSOS dela (libera RAM/CPU), e
  - derrubar os Chromes VELHOS/travados do proprio bot pra respawnar limpos,
deixando aberto SO o(s) que o bot esta realmente usando.

Sem este modo, o bot e "educado" e nao encosta em Chrome que nao seja dele.

Identificacao do Chrome do BOT: usa remote-debugging-port numa das portas das
contas (contas.py) OU perfil chrome_gen_*. Todo o resto e "Chrome dela".

Uso:
    python acesso_total.py ligar      # cria flag + limpa ociosos + respawn limpo
    python acesso_total.py desligar   # remove flag (bot volta a ser educado)
    python acesso_total.py status
"""
import os, sys, json, datetime, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
FLAG = os.path.join(BASE, "logs", "ACESSO_TOTAL")


def _log(m):
    print(f"[{datetime.datetime.now():%H:%M:%S}] {m}", flush=True)


def _portas_do_bot():
    try:
        import contas
        return set(str(c["port"]) for c in contas.CONTAS)
    except Exception:
        return {"9250", "9260", "9270"}


def ligado():
    return os.path.exists(FLAG)


def _ps(cmd, timeout=40):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                          capture_output=True, text=True, timeout=timeout)


def _fechar_chromes_dela():
    """Fecha chrome.exe que NAO sao do bot (sem debug-port de conta, sem chrome_gen_)."""
    portas = "|".join(_portas_do_bot())
    cmd = (
        "$portas='" + portas + "';"
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'chrome.exe' } | "
        "Where-Object { $_.CommandLine -notmatch 'chrome_gen_' -and "
        "  $_.CommandLine -notmatch ('remote-debugging-port=(' + $portas + ')') } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    _ps(cmd)
    _log("Chromes ociosos (pessoais) fechados")


def _derrubar_chromes_velhos_do_bot():
    """Mata os Chromes do bot pra respawnar limpos (resolve v150 travado/ECONNREFUSED)."""
    portas = "|".join(_portas_do_bot())
    cmd = (
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'chrome.exe' } | "
        "Where-Object { $_.CommandLine -match 'chrome_gen_' -or "
        "  $_.CommandLine -match ('remote-debugging-port=(' + $portas + ')') } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    _ps(cmd)
    _log("Chromes do bot derrubados (vao respawnar limpos no proximo ciclo)")


def _contar_chromes():
    try:
        out = _ps("(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'chrome.exe' }).Count").stdout.strip()
        return out
    except Exception:
        return "?"


def ligar():
    os.makedirs(os.path.dirname(FLAG), exist_ok=True)
    with open(FLAG, "w", encoding="utf-8") as f:
        json.dump({"ligado_em": datetime.datetime.now().isoformat()}, f)
    _log(f"ACESSO TOTAL ligado (antes: {_contar_chromes()} chrome.exe)")
    _fechar_chromes_dela()
    _derrubar_chromes_velhos_do_bot()
    _log(f"limpeza feita (agora: {_contar_chromes()} chrome.exe)")
    try:
        from notifica import avisar_desktop
        avisar_desktop("Veo: acesso total LIGADO", "fechei os Chromes ociosos, deixei so os em uso")
    except Exception:
        pass


def desligar():
    if os.path.exists(FLAG):
        os.remove(FLAG)
    _log("ACESSO TOTAL desligado (bot volta a nao encostar nos seus Chromes)")
    try:
        from notifica import avisar_desktop
        avisar_desktop("Veo: acesso total DESLIGADO", "nao vou mais fechar seus Chromes")
    except Exception:
        pass


def status():
    _log(f"acesso_total = {'LIGADO' if ligado() else 'desligado'} | chrome.exe abertos: {_contar_chromes()}")


def main():
    acao = (sys.argv[1] if len(sys.argv) > 1 else "status").lower()
    if acao == "ligar":
        ligar()
    elif acao == "desligar":
        desligar()
    else:
        status()


if __name__ == "__main__":
    main()
