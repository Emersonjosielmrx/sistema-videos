# -*- coding: utf-8 -*-
"""
notifica.py — Pop-up no canto da tela (Windows toast).

Avisa quando um video fica pronto (ou quando a producao pausa/retoma), igual
o projeto veo faz. Tenta 2 metodos do mais bonito pro mais simples e NUNCA
quebra o produtor se a notificacao falhar — e so um aviso.

Uso:
    from notifica import avisar_desktop
    avisar_desktop("[PROD] Video pronto", "terror — 'voz do ralo' (412s)")
"""
import subprocess


def avisar_desktop(titulo, msg):
    """Mostra um balao/toast no canto da tela. Best-effort: se falhar, ignora."""
    try:
        ps = (
            # Metodo 1: BurntToast (se instalado) — toast nativo bonito.
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
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def _esc(s):
    """Escapa aspas simples pra nao quebrar o comando PowerShell."""
    return str(s).replace("'", "''")


if __name__ == "__main__":
    avisar_desktop("historias-em-frames: teste", "notificacao de teste no canto da tela")
    print("disparado (veja o canto da tela)")
