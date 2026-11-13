#!/usr/bin/env python3
"""
Monitora limites das contas Antigravity DIRETO no Google
SEM fazer chamadas de teste ao modelo
"""
import requests
import json
import sys
from datetime import datetime
from pathlib import Path

# Telegram
TELEGRAM_TOKEN = "<SEGREDO_REMOVIDO>"
TELEGRAM_CHAT_ID = "7911666809"

# Estado
STATE_FILE = Path("D:/opus_limites_state.json")

def carregar_estado():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"contas_com_limite": [], "ultimo_aviso": None}

def salvar_estado(estado):
    STATE_FILE.write_text(json.dumps(estado, indent=2, ensure_ascii=False))

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except:
        return False

def buscar_contas_omniroute():
    """Busca credenciais Antigravity do banco do OmniRoute"""
    import subprocess
    
    cmd = [
        'ssh', '-i', '/c/Users/Haylla/.ssh/id_ed25519_hermes',
        'root@157.173.207.22',
        "sqlite3 /opt/omniroute/data/storage.sqlite "
        "\"SELECT id, credentials FROM provider_connections "
        "WHERE provider = 'antigravity' AND is_active = 1 LIMIT 10;\""
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        linhas = result.stdout.strip().split('\n')
        
        contas = []
        for linha in linhas:
            if '|' in linha:
                id_conta, creds_json = linha.split('|', 1)
                try:
                    creds = json.loads(creds_json)
                    if 'apiKey' in creds or 'token' in creds:
                        contas.append({
                            'id': id_conta.strip(),
                            'credentials': creds
                        })
                except:
                    pass
        
        return contas
    except Exception as e:
        print(f"Erro ao buscar contas: {e}")
        return []

def verificar_quota_google(credentials):
    """
    Verifica quota diretamente na API do Google Cloud Code Assist
    Retorna (tem_quota: bool, detalhes: str)
    """
    try:
        # Google Cloud Code Assist quota endpoint
        # Endpoint varia dependendo de qual API key/token está nas credentials
        
        if 'apiKey' in credentials:
            # Tenta endpoint público do Gemini Code Assist
            url = "https://cloudcode-pa.googleapis.com/v1/models"
            headers = {"x-goog-api-key": credentials['apiKey']}
            
            r = requests.get(url, headers=headers, timeout=10)
            
            if r.status_code == 200:
                # Tem acesso
                data = r.json()
                # Procura por claude-opus-4-6-thinking nos modelos disponíveis
                modelos = [m.get('name', '') for m in data.get('models', [])]
                if any('claude' in m.lower() for m in modelos):
                    return True, "Tem acesso aos modelos Claude"
                else:
                    return False, "Sem acesso ao Claude"
            elif r.status_code == 429:
                return False, "Rate limited (sem quota)"
            elif r.status_code == 403:
                return False, "Acesso negado"
            else:
                return False, f"Status {r.status_code}"
        
        return None, "Formato de credencial não suportado"
        
    except Exception as e:
        return None, f"Erro: {str(e)[:50]}"

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificando limites Antigravity...")
    
    # Busca contas do OmniRoute
    print("  Buscando contas do OmniRoute...")
    contas = buscar_contas_omniroute()
    
    if not contas:
        print("  ERRO: Nenhuma conta encontrada")
        return
    
    print(f"  {len(contas)} contas encontradas")
    print()
    
    estado = carregar_estado()
    contas_ok = []
    contas_erro = []
    
    for conta in contas[:5]:  # Testa apenas as primeiras 5
        id_conta = conta['id'][:8]
        print(f"  Testando {id_conta}...", end=" ")
        
        tem_quota, detalhes = verificar_quota_google(conta['credentials'])
        
        if tem_quota:
            print(f"OK - {detalhes}")
            contas_ok.append(id_conta)
        elif tem_quota is None:
            print(f"? - {detalhes}")
        else:
            print(f"X - {detalhes}")
            contas_erro.append(id_conta)
    
    print()
    print(f"Resultado: {len(contas_ok)} com quota, {len(contas_erro)} sem quota")
    
    # Avisa no Telegram se mudou o estado
    if contas_ok and len(contas_ok) > len(estado.get("contas_com_limite", [])):
        mensagem = (
            f"+ *{len(contas_ok)} CONTAS COM QUOTA!*\n\n"
            f"Opus 4.6 pode estar disponivel!\n"
            f"Hora: {datetime.now().strftime('%H:%M')}\n\n"
            f"Teste agora: python /d/testar_opus.py"
        )
        
        if enviar_telegram(mensagem):
            print("Telegram enviado!")
    
    elif not contas_ok and estado.get("contas_com_limite"):
        mensagem = (
            f"- *Todas as contas sem quota*\n\n"
            f"Hora: {datetime.now().strftime('%H:%M')}\n"
            f"Continuarei monitorando..."
        )
        enviar_telegram(mensagem)
    
    # Salva estado
    estado["contas_com_limite"] = contas_ok
    estado["ultimo_aviso"] = datetime.now().isoformat()
    salvar_estado(estado)

if __name__ == "__main__":
    main()
