#!/usr/bin/env python3
# COMUM — fonte única: D:\hipercool-materiais\comum\notificar.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir notificar.py --de <projeto>
"""Aviso no Telegram E no canto da tela do PC (pedido do dono, 16/10/2026).

O projeto já avisava só no Telegram (`fila.avisar`), e o dono pediu também a notificação do Windows,
como a que o Veo mostra no canto da tela: assim ele vê o capítulo ficar pronto sem precisar abrir o
celular nem o terminal.

    import notificar
    notificar.aviso("Capítulo 4 pronto", "7min12s, análise ok")        # tela + Telegram
    notificar.aviso("Capítulo 5 reprovado", "...", nivel="erro")       # idem, com cara de erro
    notificar.tela("só na tela", "sem Telegram")

A notificação de tela usa o balão do próprio Windows (System.Windows.Forms.NotifyIcon pelo
PowerShell): não precisa instalar nada e não depende de módulo externo. Se falhar — sessão sem área
de trabalho, PowerShell bloqueado —, o aviso segue pro Telegram do mesmo jeito: avisar nunca pode
derrubar o render.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# 18/10: versão única (hipercool, manhwa-react...): o nome do projeto vem da pasta onde a cópia está
_PROJETOS = {"hipercool-videos": ("Hipercool", "hipercool"), "manhwa-react": ("ManhwaReact", "manhwa-react"),
             "historias-em-frames": ("Histórias em Frames", "historias"), "recapd-ambientes": ("Recap", "recapd"),
             "veo": ("Veo", "veo"), "postador-de-videos": ("Postador", "postador")}
TITULO_PADRAO, PREFIXO = next((_PROJETOS[p] for p in Path(__file__).resolve().parts if p in _PROJETOS),
                              ("Vídeos", "vídeos"))
ICONES = {"ok": "Info", "info": "Info", "aviso": "Warning", "erro": "Error"}


def _ps_escape(t):
    return str(t).replace("'", "''").replace("\r", " ").replace("\n", " ")[:250]


def tela(titulo, texto="", nivel="ok", segundos=12):
    """Balão no canto da tela. Devolve True se conseguiu mostrar."""
    icone = ICONES.get(nivel, "Info")
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "$n = New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon = [System.Drawing.SystemIcons]::Information;"
        "$n.Visible = $true;"
        f"$n.ShowBalloonTip({int(segundos * 1000)}, '{_ps_escape(titulo)}', "
        f"'{_ps_escape(texto)}', [System.Windows.Forms.ToolTipIcon]::{icone});"
        f"Start-Sleep -Seconds {min(int(segundos), 20)};"
        "$n.Dispose()"
    )
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except Exception:  # noqa: BLE001 — avisar não derruba nada
        return False


# O Telegram da postagem fica no POSTADOR (bot que o dono lê); o segredo não é copiado pros projetos.
TELEGRAM_POSTADOR = Path(r"D:\postador-de-videos\config\telegram.json")


def _credencial():
    try:
        d = json.loads(TELEGRAM_POSTADOR.read_text(encoding="utf-8"))
        if d.get("bot_token") and d.get("chat_id"):
            return d["bot_token"], str(d["chat_id"])
    except (OSError, ValueError, KeyError):
        pass
    return None, None


def telegram(msg, importante=True):
    """Mesmo Telegram que a postagem já usa. True se mandou (ou entregou ao portão).
    19/10: passa pelo PORTÃO ÚNICO (D:\\video-fila\\avisos.py) — repetido não sai; importante=False vai pro resumo
    das 9h/14h/21h. Sem o portão, manda direto como antes."""
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(f"🎬 {PREFIXO}: {msg}"[:4000], PREFIXO, importante=importante, html_ok=False)
        return True
    except Exception:  # noqa: BLE001
        pass
    token, chat = _credencial()
    if not token:
        return False
    try:
        import urllib.parse
        import urllib.request
        dados = urllib.parse.urlencode({"chat_id": chat, "text": f"🎬 {PREFIXO}: {msg}"[:4000],
                                        "disable_web_page_preview": "true"}).encode()
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage",
                                    data=dados, timeout=15) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001 — avisar nunca derruba o render
        return False


def aviso(titulo, texto="", nivel="ok", so_tela=False, so_telegram=False):
    """Avisa nos dois lugares. Devolve (foi pra tela, foi pro telegram)."""
    emoji = {"ok": "✅", "info": "ℹ️", "aviso": "⚠️", "erro": "❌"}.get(nivel, "")
    t = tela(f"{TITULO_PADRAO} — {titulo}", texto, nivel) if not so_telegram else False
    # erro/aviso sai na hora (o vigia: "quebrou" = erro, "CONSERTEI" = aviso); ok/info vai pro resumo (dono 19/10)
    g = telegram(f"{emoji} {titulo}" + (f"\n{texto}" if texto else ""),
                 importante=nivel in ("erro", "aviso")) if not so_tela else False
    return t, g


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Avisa no Telegram e no canto da tela")
    ap.add_argument("titulo")
    ap.add_argument("texto", nargs="?", default="")
    ap.add_argument("--nivel", default="ok", choices=sorted(ICONES))
    ap.add_argument("--so-tela", action="store_true")
    ap.add_argument("--so-telegram", action="store_true")
    a = ap.parse_args()
    t, g = aviso(a.titulo, a.texto, a.nivel, a.so_tela, a.so_telegram)
    print(f"tela={'ok' if t else 'não'} telegram={'ok' if g else 'não'}")


if __name__ == "__main__":
    main()
