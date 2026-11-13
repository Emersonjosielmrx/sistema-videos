#!/usr/bin/env python3
"""
Checa Opus 4.6 e avisa no Telegram
Roda via agendador (Task Scheduler Windows / cron)
"""
import requests
import json
from datetime import datetime
from pathlib import Path

# Telegram
TELEGRAM_TOKEN = "<SEGREDO_REMOVIDO>"
TELEGRAM_CHAT_ID = "7911666809"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# OmniRoute
OMNIROUTE_URL = "http://157.173.207.22:20128/v1/messages"
OMNIROUTE_KEY = "<SEGREDO_REMOVIDO>"

# Arquivo de estado (guarda última vez que funcionou)
STATE_FILE = Path("D:/opus_monitor_state.json")

def carregar_estado():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"ultimo_sucesso": None, "ultima_falha": None}

def salvar_estado(estado):
    STATE_FILE.write_text(json.dumps(estado, indent=2))

def enviar_telegram(mensagem):
    try:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }
        response = requests.post(TELEGRAM_API, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def testar_opus():
    """Testa Opus 4.6 rapidamente"""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": OMNIROUTE_KEY,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": "claude-opus-4-6-thinking",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "1"}]
    }
    
    try:
        response = requests.post(
            OMNIROUTE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        return response.status_code == 200
    except:
        return False

def main():
    agora = datetime.now()
    hora = agora.strftime("%H:%M")
    
    estado = carregar_estado()
    
    funcionando = testar_opus()
    
    if funcionando:
        # SUCESSO!
        # Avisa apenas se última vez foi falha ou nunca avisou
        if estado["ultimo_sucesso"] != agora.strftime("%Y-%m-%d"):
            mensagem = (
                f"✅ *OPUS 4.6 DISPONÍVEL!*\n\n"
                f"Hora: {hora}\n"
                f"Status: Respondendo normalmente\n\n"
                f"Pode usar! 🚀"
            )
            
            if enviar_telegram(mensagem):
                estado["ultimo_sucesso"] = agora.strftime("%Y-%m-%d")
                estado["ultima_falha"] = None
                salvar_estado(estado)
                print(f"[{hora}] ✓ Opus funcionando - Telegram enviado")
            else:
                print(f"[{hora}] ✓ Opus funcionando - Falha ao enviar Telegram")
        else:
            print(f"[{hora}] ✓ Opus funcionando (já avisado hoje)")
    
    else:
        # SEM QUOTA
        # Avisa apenas a cada 3h
        ultima_falha = estado.get("ultima_falha")
        deve_avisar = False
        
        if ultima_falha is None:
            deve_avisar = True
        else:
            try:
                dt_ultima = datetime.fromisoformat(ultima_falha)
                horas_desde = (agora - dt_ultima).total_seconds() / 3600
                if horas_desde >= 3:
                    deve_avisar = True
            except:
                deve_avisar = True
        
        if deve_avisar:
            mensagem = (
                f"⏳ *Opus 4.6 ainda indisponível*\n\n"
                f"Hora: {hora}\n"
                f"Status: Sem quota\n\n"
                f"Continuarei checando..."
            )
            
            if enviar_telegram(mensagem):
                estado["ultima_falha"] = agora.isoformat()
                salvar_estado(estado)
                print(f"[{hora}] ✗ Sem quota - Telegram enviado")
            else:
                print(f"[{hora}] ✗ Sem quota - Falha ao enviar Telegram")
        else:
            print(f"[{hora}] ✗ Sem quota (já avisado recentemente)")

if __name__ == "__main__":
    main()
