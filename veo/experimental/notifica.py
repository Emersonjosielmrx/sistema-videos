# -*- coding: utf-8 -*-
"""
========================================================================
notifica.py  —  Pop-up no canto da tela (Windows toast)
========================================================================

Avisa a dona no canto da tela quando algo importante acontece — igual o app
de limpeza de RAM dela faz. Usado pra: "video pronto", "pausei por carga",
"retomei a producao".

Tenta 3 metodos, do mais bonito pro mais simples, e NUNCA quebra o bot se a
notificacao falhar (e so um aviso).
"""
import subprocess


def avisar_desktop(titulo, msg):
    """Mostra um balao/toast no canto da tela. Best-effort: se falhar, ignora."""
    try:
        # Metodo 1: BurntToast (se a dona tiver instalado) — toast nativo bonito.
        ps = (
            "if (Get-Module -ListAvailable -Name BurntToast) {"
            "  Import-Module BurntToast;"
            f"  New-BurntToastNotification -Text '{_esc(titulo)}','{_esc(msg)}';"
            "} else {"
            # Metodo 2: balloon tip via NotifyIcon (sempre existe no Windows).
            "  Add-Type -AssemblyName System.Windows.Forms;"
            "  $n = New-Object System.Windows.Forms.NotifyIcon;"
            "  $n.Icon = [System.Drawing.SystemIcons]::Information;"
            "  $n.Visible = $true;"
            f"  $n.ShowBalloonTip(5000,'{_esc(titulo)}','{_esc(msg)}',"
            "     [System.Windows.Forms.ToolTipIcon]::Info);"
            "  Start-Sleep -Seconds 6; $n.Dispose();"
            "}"
        )
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _esc(s):
    """Escapa aspas simples pra nao quebrar o comando PowerShell."""
    return str(s).replace("'", "''")


if __name__ == "__main__":
    avisar_desktop("Veo: teste", "notificacao de teste no canto da tela")
    print("disparado (veja o canto da tela)")
