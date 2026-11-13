#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daemon que monitora /tmp/ia-tarefas/ e executa tarefas automaticamente.
Roda como serviço no PC Linux remoto.
"""

import json
import subprocess
import time
import os
from pathlib import Path
from datetime import datetime
import sys

PASTA_TAREFAS = Path("/tmp/ia-tarefas")
ARQUIVO_MARCADOR = PASTA_TAREFAS / "NOVA_TAREFA"
INTERVALO_CHECK = 2  # segundos

def executar_comando(cmd, timeout=30):
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(
            cmd,
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

def processar_tarefa(arquivo_tarefa):
    """Processa uma tarefa do arquivo JSON"""
    try:
        tarefa = json.loads(arquivo_tarefa.read_text(encoding='utf-8'))

        print(f"[{datetime.now():%H:%M:%S}] Processando tarefa: {tarefa.get('id', 'sem-id')}")

        instrucoes = tarefa.get("instrucoes", {})
        arquivo_resposta = tarefa.get("responder_em", "/tmp/ia-resposta_default.json")

        resultados = []

        # Se tem campo 'passos', executa cada passo
        if "passos" in instrucoes:
            for passo in instrucoes["passos"]:
                if isinstance(passo, dict):
                    if "comandos" in passo:
                        for cmd in passo["comandos"]:
                            result = executar_comando(cmd)
                            resultados.append({
                                "comando": cmd,
                                "resultado": result
                            })
                    elif "script" in passo:
                        result = executar_comando(passo["script"])
                        resultados.append({
                            "script": "executado",
                            "resultado": result
                        })
                elif isinstance(passo, str):
                    result = executar_comando(passo)
                    resultados.append({
                        "comando": passo,
                        "resultado": result
                    })

        # Se é instrução simples com campo 'acao'
        elif "acao" in instrucoes:
            acao = instrucoes["acao"]

            if acao == "info_sistema":
                cmds = ["hostname", "tailscale ip -4", "nproc", "free -h"]
                for cmd in cmds:
                    result = executar_comando(cmd)
                    resultados.append({"comando": cmd, "resultado": result})

            elif acao == "verificar_disco":
                pasta = instrucoes.get("pasta", "/opt/video-producao")
                result = executar_comando(f"df -h {pasta}")
                resultados.append({"comando": f"df -h {pasta}", "resultado": result})

            else:
                resultados.append({"erro": f"Ação desconhecida: {acao}"})

        # Monta resposta
        resposta = {
            "tarefa_id": tarefa.get("id"),
            "processado_em": datetime.now().isoformat(),
            "status": "SUCESSO",
            "resultados": resultados
        }

        # Salva resposta
        Path(arquivo_resposta).write_text(
            json.dumps(resposta, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        print(f"[{datetime.now():%H:%M:%S}] ✓ Resposta salva em: {arquivo_resposta}")
        return True

    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] ✗ Erro ao processar: {e}")

        # Tenta salvar erro
        try:
            resposta_erro = {
                "status": "ERRO",
                "erro": str(e),
                "processado_em": datetime.now().isoformat()
            }
            Path(tarefa.get("responder_em", "/tmp/ia-resposta_erro.json")).write_text(
                json.dumps(resposta_erro, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        except:
            pass

        return False

def monitorar():
    """Loop principal de monitoramento"""
    print(f"[{datetime.now():%H:%M:%S}] Daemon iniciado")
    print(f"Monitorando: {PASTA_TAREFAS}")
    print(f"Marcador: {ARQUIVO_MARCADOR}")
    print("")

    # Cria pasta se não existir
    PASTA_TAREFAS.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            # Verifica se existe marcador NOVA_TAREFA
            if ARQUIVO_MARCADOR.exists():
                print(f"[{datetime.now():%H:%M:%S}] Nova tarefa detectada!")

                # Lê conteúdo do marcador para identificar arquivo da tarefa
                try:
                    marcador_texto = ARQUIVO_MARCADOR.read_text(encoding='utf-8')

                    # Procura arquivos de tarefa recentes
                    arquivos_tarefa = sorted(
                        PASTA_TAREFAS.glob("tarefa_*.json"),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )

                    if arquivos_tarefa:
                        arquivo_mais_recente = arquivos_tarefa[0]
                        processar_tarefa(arquivo_mais_recente)

                except Exception as e:
                    print(f"[{datetime.now():%H:%M:%S}] Erro ao ler marcador: {e}")

                # Remove marcador
                ARQUIVO_MARCADOR.unlink(missing_ok=True)

            time.sleep(INTERVALO_CHECK)

        except KeyboardInterrupt:
            print(f"\n[{datetime.now():%H:%M:%S}] Daemon encerrado pelo usuário")
            break
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] Erro no loop: {e}")
            time.sleep(INTERVALO_CHECK)

if __name__ == "__main__":
    print("Worker IA - Daemon de Tarefas Remotas")
    print("=" * 50)
    print(f"PID: {os.getpid()}")
    print("")

    monitorar()
