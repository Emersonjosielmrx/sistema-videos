#!/usr/bin/env python3
"""
Monitor Telegram — escuta comandos do bot e responde com status/ações.
Bot: @Claude_code_emerso_nchat_bot
Dono: chat_id 7911666809
"""
import os, sys, time, json, glob, subprocess, traceback
sys.exit("DESATIVADO em 23/10/2026: usa o token do bot GERAL do Telegram e o getUpdates dele roubava as mensagens do "
         "dono do D:\\postador-de-videos\\bin\\notificar_telegram.py (só pode haver 1 leitor por bot).")
import requests  # noqa: E402

BOT_TOKEN = "<SEGREDO_REMOVIDO>"
CHAT_ID = 7911666809
API = f"https://api.telegram.org/bot{BOT_TOKEN}"
POLL_INTERVAL = 5  # segundos

MS_ENERGY_DIR = r"D:\ms-energy"
VEO_DIR = r"D:\veo\beta"
VENV_PY = r"D:\veo\venv\Scripts\python.exe"  # o venv do hipercool-videos foi apagado

def send(text, chat_id=CHAT_ID):
    try:
        r = requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text[:4096],
            "parse_mode": "HTML",
        }, timeout=15)
        return r.json().get("ok", False)
    except Exception as e:
        print(f"[ERRO send] {e}")
        return False

def get_updates(offset=None):
    try:
        params = {"timeout": 30, "allowed_updates": ["message"]}
        if offset:
            params["offset"] = offset
        r = requests.get(f"{API}/getUpdates", params=params, timeout=35)
        data = r.json()
        return data.get("result", [])
    except Exception:
        return []

def contar_videos_ms():
    pasta = os.path.join(MS_ENERGY_DIR, "videos", "shorts_veo")
    if not os.path.isdir(pasta):
        return 0, []
    mp4s = sorted(glob.glob(os.path.join(pasta, "*.mp4")), key=os.path.getmtime, reverse=True)
    return len(mp4s), mp4s[:5]

def status_ms_energy():
    total, recentes = contar_videos_ms()
    lines = [f"<b>MS Energy</b> - {total} videos gerados"]
    for f in recentes:
        nome = os.path.basename(f)
        tam = os.path.getsize(f) / (1024*1024)
        lines.append(f"  {nome} ({tam:.1f}MB)")
    # processo rodando?
    try:
        out = subprocess.check_output(
            'wmic process where "name=\'python.exe\'" get commandline',
            shell=True, text=True, timeout=10
        )
        if "gerar_short_veo" in out:
            lines.append("\nLoop MS Energy: RODANDO")
        else:
            lines.append("\nLoop MS Energy: PARADO")
    except Exception:
        lines.append("\nLoop MS Energy: (nao consegui verificar)")
    # pausa?
    pause_file = os.path.join(VEO_DIR, "logs", "PAUSE_SYSTEM")
    if os.path.exists(pause_file):
        lines.append("Sistema: PAUSADO")
    else:
        lines.append("Sistema: ATIVO")
    return "\n".join(lines)

def status_veo():
    try:
        pasta = os.path.join(VEO_DIR, "..", "videos", "cron_shorts")
        if not os.path.isdir(pasta):
            pasta = os.path.join(VEO_DIR, "videos", "cron_shorts")
        if not os.path.isdir(pasta):
            return "Veo: pasta de videos nao encontrada"
        mp4s = sorted(glob.glob(os.path.join(pasta, "*.mp4")), key=os.path.getmtime, reverse=True)
        lines = [f"<b>Veo Principal</b> - {len(mp4s)} videos"]
        for f in mp4s[:5]:
            nome = os.path.basename(f)
            tam = os.path.getsize(f) / (1024*1024)
            lines.append(f"  {nome} ({tam:.1f}MB)")
        return "\n".join(lines)
    except Exception as e:
        return f"Veo: erro ao verificar - {e}"

def ligar_ms_energy():
    try:
        subprocess.Popen(
            f'start "MS-Energy-Loop" cmd /c "D:\\ms-energy\\MSEnergy_LIGAR.bat"',
            shell=True, cwd=MS_ENERGY_DIR
        )
        return "MS Energy LIGADO - loop iniciado em nova janela."
    except Exception as e:
        return f"Erro ao ligar MS Energy: {e}"

def desligar_ms_energy():
    try:
        subprocess.run(
            f'cmd /c "D:\\ms-energy\\MSEnergy_DESLIGAR.bat"',
            shell=True, cwd=MS_ENERGY_DIR, timeout=15
        )
        return "MS Energy DESLIGADO."
    except Exception as e:
        return f"Erro ao desligar: {e}"

def pausar_sistema():
    pause_file = os.path.join(VEO_DIR, "logs", "PAUSE_SYSTEM")
    os.makedirs(os.path.dirname(pause_file), exist_ok=True)
    with open(pause_file, "w") as f:
        json.dump({"motivo": "pausa via telegram", "ts": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
    return "Sistema PAUSADO (MS Energy + Veo)."

def despausar_sistema():
    pause_file = os.path.join(VEO_DIR, "logs", "PAUSE_SYSTEM")
    if os.path.exists(pause_file):
        os.remove(pause_file)
        return "Sistema DESPAUSADO - producao liberada."
    return "Sistema ja estava ativo (sem pausa)."

HELP_TEXT = """<b>Comandos disponiveis:</b>

/status - Status geral (MS Energy + Veo)
/ms - Status MS Energy
/veo - Status Veo principal
/ligar - Ligar loop MS Energy
/desligar - Desligar loop MS Energy
/pausar - Pausar todo o sistema
/despausar - Despausar sistema
/help - Esta mensagem"""

def handle_command(text):
    cmd = text.strip().lower().split()[0] if text.strip() else ""
    if cmd in ("/start", "/help"):
        return HELP_TEXT
    elif cmd == "/status":
        return status_ms_energy() + "\n\n" + status_veo()
    elif cmd == "/ms":
        return status_ms_energy()
    elif cmd == "/veo":
        return status_veo()
    elif cmd == "/ligar":
        return ligar_ms_energy()
    elif cmd == "/desligar":
        return desligar_ms_energy()
    elif cmd == "/pausar":
        return pausar_sistema()
    elif cmd == "/despausar":
        return despausar_sistema()
    else:
        return f"Comando '{cmd}' nao reconhecido.\n\n{HELP_TEXT}"

def main():
    print(f"[telegram_monitor] Iniciando polling... (chat_id={CHAT_ID})")
    send("Monitor Telegram ativo! Use /help pra ver os comandos.")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                chat = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                if chat != CHAT_ID:
                    continue
                if not text:
                    continue
                print(f"[CMD] {text}")
                resp = handle_command(text)
                send(resp)
        except KeyboardInterrupt:
            print("\n[telegram_monitor] Encerrado pelo usuario.")
            break
        except Exception as e:
            print(f"[ERRO] {e}")
            traceback.print_exc()
            time.sleep(10)

if __name__ == "__main__":
    main()
