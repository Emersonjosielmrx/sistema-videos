#!/usr/bin/env python3
import sys
sys.exit("DESATIVADO em 23/10/2026: lia o bot GERAL do Telegram (getUpdates) e roubava as mensagens do dono do "
         "D:\\postador-de-videos\\bin\\notificar_telegram.py, que já trata o comando 'opus' (D:\\monitor_opus.py).")
import requests  # noqa: E402
import json
import time
from datetime import datetime
from pathlib import Path

# Telegram
TOKEN = "<SEGREDO_REMOVIDO>"
CHAT_ID = "7911666809"
API = f"https://api.telegram.org/bot{TOKEN}"

# OmniRoute
OMNIROUTE_URL = "http://157.173.207.22:20128/v1/messages"
OMNIROUTE_KEY = "<SEGREDO_REMOVIDO>"

# Estado
STATE = Path("D:/opus_monitor.json")

def carregar_estado():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"funcionando": False, "ultima_checagem": None, "ultimo_update_id": 0}

def salvar_estado(estado):
    STATE.write_text(json.dumps(estado, indent=2))

def enviar(msg):
    try:
        r = requests.post(f"{API}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        return r.status_code == 200
    except:
        return False

def testar_opus():
    try:
        r = requests.post(
            OMNIROUTE_URL,
            headers={"Content-Type": "application/json", "x-api-key": OMNIROUTE_KEY, "anthropic-version": "2023-06-01"},
            json={"model": "claude-opus-4-6-thinking", "max_tokens": 1, "messages": [{"role": "user", "content": "x"}]},
            timeout=30
        )
        return r.status_code == 200
    except:
        return False

def verificar_comandos(estado):
    try:
        r = requests.get(f"{API}/getUpdates", params={"offset": estado["ultimo_update_id"] + 1, "timeout": 1}, timeout=5)
        if r.status_code != 200:
            return estado
        
        data = r.json()
        if not data.get("result"):
            return estado
        
        for update in data["result"]:
            estado["ultimo_update_id"] = max(estado["ultimo_update_id"], update["update_id"])
            
            msg = update.get("message", {})
            texto = msg.get("text", "").strip()
            
            # Aceita "opus" em qualquer formato: opus, Opus, OPUS, etc
            if texto.lower() == "opus":
                enviar("🔍 Testando Opus 4.6...")
                ok = testar_opus()
                
                if ok:
                    enviar("✅ *OPUS 4.6 FUNCIONANDO!*\n\nPode usar agora!")
                    estado["funcionando"] = True
                else:
                    enviar("❌ Opus 4.6 sem quota\n\nContinuarei monitorando")
                    estado["funcionando"] = False
                
                salvar_estado(estado)
        
        return estado
    except Exception as e:
        print(f"Erro verificar_comandos: {e}")
        return estado

print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitor iniciado")
print("Intervalo: 5 HORAS")
print("Comando: 'opus' (qualquer formato)")
print("")

enviar("🔍 Monitor Opus 4.6 ATIVO\n\nComando: opus\nTeste a cada 5h")

estado = carregar_estado()
ultimo_teste_auto = time.time()

while True:
    try:
        estado = verificar_comandos(estado)
        
        agora = time.time()
        if agora - ultimo_teste_auto >= 5 * 3600:
            hora = datetime.now().strftime("%H:%M")
            print(f"[{hora}] Teste automatico...")
            
            ok = testar_opus()
            
            if ok and not estado["funcionando"]:
                enviar(f"✅ *OPUS 4.6 VOLTOU!*\n\nHora: {hora}")
                estado["funcionando"] = True
            elif not ok and estado["funcionando"]:
                enviar(f"❌ Opus caiu\n\nHora: {hora}")
                estado["funcionando"] = False
            
            estado["ultima_checagem"] = hora
            salvar_estado(estado)
            ultimo_teste_auto = agora
        
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\nParado")
        enviar("🛑 Monitor PARADO")
        break
    except Exception as e:
        print(f"Erro: {e}")
        time.sleep(60)
