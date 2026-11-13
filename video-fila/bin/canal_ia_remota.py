#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canal de comunicação bidirecional com IAs remotas via SSH + arquivos JSON.
PC1 envia tarefas, aguarda resposta automática da IA remota.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Forçar UTF-8 no stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

MAQUINAS_LINUX = {
    "x200ma": {
        "ip": "100.87.195.108",
        "nome": "emerson-x200ma",
        "usuario": "emerson"
    },
    "server2": {
        "ip": "100.101.154.80",
        "nome": "server2-vps",
        "usuario": "root"
    }
}

def executar_remoto(maquina_id, comando, timeout=30):
    """Executa comando via SSH e retorna saída"""
    if maquina_id not in MAQUINAS_LINUX:
        return {"erro": f"Máquina {maquina_id} desconhecida"}

    maq = MAQUINAS_LINUX[maquina_id]
    ssh_cmd = f'ssh -o ConnectTimeout=10 -o BatchMode=yes {maq["usuario"]}@{maq["ip"]} "{comando}"'

    try:
        result = subprocess.run(
            ssh_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return {
            "saida": result.stdout,
            "erro": result.stderr,
            "codigo": result.returncode,
            "sucesso": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"erro": f"Timeout após {timeout}s", "sucesso": False}
    except Exception as e:
        return {"erro": str(e), "sucesso": False}


def enviar_tarefa_ia(maquina_id, instrucoes, timeout_resposta=60):
    """
    Envia instruções estruturadas para a IA remota executar.
    Aguarda resposta por até timeout_resposta segundos.
    """
    if maquina_id not in MAQUINAS_LINUX:
        return {"erro": f"Máquina {maquina_id} desconhecida"}

    maq = MAQUINAS_LINUX[maquina_id]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    tarefa = {
        "id": f"tarefa_{timestamp}",
        "enviado_por": "PC1-IA",
        "enviado_em": datetime.now().isoformat(),
        "maquina_destino": maquina_id,
        "instrucoes": instrucoes,
        "responder_em": f"/tmp/ia-resposta_{timestamp}.json"
    }

    # Salva localmente
    local_dir = Path("D:/video-fila/logs/tarefas_remotas")
    local_dir.mkdir(parents=True, exist_ok=True)
    arquivo_local = local_dir / f"{maquina_id}_{timestamp}.json"
    arquivo_local.write_text(json.dumps(tarefa, ensure_ascii=False, indent=2), encoding="utf-8")

    # Cria diretório remoto
    exec_result = executar_remoto(maquina_id, "mkdir -p /tmp/ia-tarefas")
    if not exec_result.get("sucesso"):
        return {"erro": f"Falha ao criar diretório remoto: {exec_result.get('erro')}"}

    # Envia arquivo via SCP
    arquivo_remoto = f"/tmp/ia-tarefas/tarefa_{timestamp}.json"
    scp_cmd = f'scp -o ConnectTimeout=10 -o BatchMode=yes "{arquivo_local}" {maq["usuario"]}@{maq["ip"]}:{arquivo_remoto}'

    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return {"erro": f"Falha no SCP: {result.stderr}"}

    # Cria marcador para IA remota
    instrucoes_texto = json.dumps(instrucoes, ensure_ascii=False)
    marcador_cmd = f"echo 'TAREFA: Execute as instrucoes em {arquivo_remoto} e salve resultado em {tarefa['responder_em']}' > /tmp/ia-tarefas/NOVA_TAREFA && echo '{instrucoes_texto}' >> /tmp/ia-tarefas/NOVA_TAREFA"
    executar_remoto(maquina_id, marcador_cmd)

    print(f"✅ Tarefa enviada para {maq['nome']}")
    print(f"   Arquivo remoto: {arquivo_remoto}")
    print(f"   Aguardando resposta por até {timeout_resposta}s...")

    # Aguarda resposta
    arquivo_resposta = tarefa['responder_em']
    tentativas = 0
    max_tentativas = timeout_resposta // 2

    while tentativas < max_tentativas:
        time.sleep(2)
        tentativas += 1

        # Verifica se arquivo de resposta existe
        check = executar_remoto(maquina_id, f"test -f {arquivo_resposta} && cat {arquivo_resposta}")

        if check.get("sucesso") and check.get("saida"):
            try:
                resposta = json.loads(check["saida"])

                # Salva resposta localmente
                arquivo_resp_local = local_dir / f"{maquina_id}_{timestamp}_resposta.json"
                arquivo_resp_local.write_text(json.dumps(resposta, ensure_ascii=False, indent=2), encoding="utf-8")

                print(f"✅ Resposta recebida após {tentativas * 2}s")
                return resposta
            except json.JSONDecodeError:
                print(f"⚠️  Resposta malformada, tentando novamente...")
                continue

        if tentativas % 5 == 0:
            print(f"   Aguardando... ({tentativas * 2}s)")

    return {"erro": f"Timeout: nenhuma resposta após {timeout_resposta}s"}


def testar_conectividade(maquina_id):
    """Testa conexão SSH básica"""
    print(f"\n🔍 Testando {maquina_id}...")

    result = executar_remoto(maquina_id, "hostname && tailscale ip -4 && echo OK")

    if result.get("sucesso"):
        print(f"✅ Conectado com sucesso")
        print(f"   Saída: {result['saida'].strip()}")
        return True
    else:
        print(f"❌ Falha na conexão")
        print(f"   Erro: {result.get('erro', 'Desconhecido')}")
        return False


def obter_status(maquina_id):
    """Consulta API de status da máquina remota"""
    if maquina_id not in MAQUINAS_LINUX:
        return {"erro": f"Máquina {maquina_id} desconhecida"}

    maq = MAQUINAS_LINUX[maquina_id]
    ip = maq["ip"]

    result = executar_remoto(maquina_id, f"curl -s http://localhost:5000/")

    if result.get("sucesso") and result.get("saida"):
        try:
            status = json.loads(result["saida"])
            return status
        except json.JSONDecodeError:
            return {"erro": "Resposta malformada da API"}
    else:
        erro_msg = result.get("erro", "")
        if "Connection refused" in erro_msg or "Failed to connect" in erro_msg:
            return {
                "erro": "API nao esta rodando",
                "solucao": "Execute o script de configuracao primeiro: python D:\\video-fila\\bin\\preparar_pc_linux.py e cole o conteudo gerado no terminal do Linux"
            }
        return {"erro": "API nao respondeu", "detalhes": erro_msg}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("📡 Canal de Comunicação IA Remota\n")
        print("Uso:")
        print("  python canal_ia_remota.py testar <maquina>")
        print("  python canal_ia_remota.py status <maquina>")
        print("  python canal_ia_remota.py executar <maquina> '<comando>'")
        print("  python canal_ia_remota.py tarefa <maquina> '<instrucoes_json>'")
        print("\nMáquinas: x200ma, server2")
        print("\nExemplos:")
        print('  python canal_ia_remota.py testar x200ma')
        print('  python canal_ia_remota.py status server2')
        print('  python canal_ia_remota.py executar x200ma "ls -lah /opt"')
        print('  python canal_ia_remota.py tarefa x200ma "{\\"acao\\": \\"verificar_disco\\", \\"pasta\\": \\"/opt\\"}"')
        sys.exit(1)

    comando = sys.argv[1]

    if comando == "testar":
        maquina = sys.argv[2] if len(sys.argv) > 2 else "x200ma"
        sucesso = testar_conectividade(maquina)
        sys.exit(0 if sucesso else 1)

    elif comando == "status":
        maquina = sys.argv[2] if len(sys.argv) > 2 else "x200ma"
        status = obter_status(maquina)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        sys.exit(0 if "erro" not in status else 1)

    elif comando == "executar":
        if len(sys.argv) < 4:
            print("❌ Uso: python canal_ia_remota.py executar <maquina> '<comando>'")
            sys.exit(1)

        maquina = sys.argv[2]
        cmd = sys.argv[3]

        print(f"🚀 Executando em {maquina}: {cmd}")
        result = executar_remoto(maquina, cmd)

        if result.get("sucesso"):
            print("\n✅ Sucesso:")
            print(result["saida"])
        else:
            print("\n❌ Erro:")
            print(result.get("erro", "Desconhecido"))

        sys.exit(0 if result.get("sucesso") else 1)

    elif comando == "tarefa":
        if len(sys.argv) < 4:
            print("❌ Uso: python canal_ia_remota.py tarefa <maquina> '<instrucoes_json>'")
            sys.exit(1)

        maquina = sys.argv[2]
        try:
            instrucoes = json.loads(sys.argv[3])
        except json.JSONDecodeError:
            print("❌ Instruções inválidas (não é JSON válido)")
            sys.exit(1)

        resposta = enviar_tarefa_ia(maquina, instrucoes, timeout_resposta=60)

        print("\n📥 Resposta:")
        print(json.dumps(resposta, ensure_ascii=False, indent=2))

        sys.exit(0 if "erro" not in resposta else 1)

    else:
        print(f"❌ Comando desconhecido: {comando}")
        sys.exit(1)
