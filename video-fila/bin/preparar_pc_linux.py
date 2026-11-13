#!/usr/bin/env python3
"""
Script simplificado: gera instruções que o DONO copia/cola no terminal do PC Linux.
Mais simples que SSH se as portas ainda não estão abertas.
"""

INSTRUCOES_COMPLETAS = """
# ============================================================
# INSTRUÇÕES PARA CONFIGURAR PC LINUX COMO WORKER DE VÍDEOS
# ============================================================
# Copie este bloco inteiro e cole no terminal do PC Linux

# 1. Informações do sistema (me envie o resultado)
echo "=== INFORMAÇÕES DO SISTEMA ==="
hostname
tailscale ip -4
cat /etc/os-release | grep PRETTY_NAME
nproc
free -h
nvidia-smi 2>/dev/null || echo "Sem GPU NVIDIA"
df -h | grep -E '^/dev/'
echo ""

# 2. Habilitar SSH
echo "=== CONFIGURANDO SSH ==="
sudo systemctl enable --now ssh
sudo systemctl status ssh --no-pager | head -10
echo ""

# 3. Firewall - portas para Tailscale
echo "=== ABRINDO PORTAS NO FIREWALL ==="
if command -v ufw >/dev/null; then
    sudo ufw allow from 100.64.0.0/10 to any port 22 comment 'SSH Tailscale'
    sudo ufw allow from 100.64.0.0/10 to any port 8791 comment 'Worker API'
    sudo ufw allow from 100.64.0.0/10 to any port 5000 comment 'Status API'
    sudo ufw status numbered
elif command -v firewall-cmd >/dev/null; then
    sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="100.64.0.0/10" port port="22" protocol="tcp" accept'
    sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="100.64.0.0/10" port port="8791" protocol="tcp" accept'
    sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="100.64.0.0/10" port port="5000" protocol="tcp" accept'
    sudo firewall-cmd --reload
    sudo firewall-cmd --list-all
else
    echo "⚠️  Firewall não detectado (ufw/firewalld) - pode precisar configurar manualmente"
fi
echo ""

# 4. Criar estrutura de diretórios
echo "=== CRIANDO ESTRUTURA ==="
sudo mkdir -p /opt/video-producao/{fila,work,cache,logs,bin}
sudo chown -R $USER:$USER /opt/video-producao
chmod 755 /opt/video-producao
ls -la /opt/video-producao
echo ""

# 5. Instalar dependências
echo "=== INSTALANDO DEPENDÊNCIAS ==="
python3 --version

if command -v apt >/dev/null; then
    sudo apt update
    sudo apt install -y python3-pip python3-venv ffmpeg curl git rsync htop psmisc
elif command -v dnf >/dev/null; then
    sudo dnf install -y python3-pip ffmpeg curl git rsync htop psmisc
fi

python3 -m pip install --user psutil
ffmpeg -version | head -n1
echo ""

# 6. Criar arquivo de configuração da máquina
echo "=== CRIANDO CONFIGURAÇÃO ==="
HOSTNAME=$(hostname)
IP_TS=$(tailscale ip -4 2>/dev/null || echo "SEM_TAILSCALE")
NUCLEOS=$(nproc)
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
HAS_GPU="false"
if nvidia-smi >/dev/null 2>&1; then HAS_GPU="true"; fi

cat > /opt/video-producao/maquina.json <<EOFCONFIG
{
  "nome": "$HOSTNAME",
  "ip_tailscale": "$IP_TS",
  "capacidades": {
    "gpu": $HAS_GPU,
    "nucleos": $NUCLEOS,
    "ram_gb": $RAM_GB,
    "tipos_permitidos": ["anime", "manhwa", "shorts"]
  },
  "status": "disponivel",
  "adicionado_em": "$(date -Iseconds)"
}
EOFCONFIG

cat /opt/video-producao/maquina.json
echo ""

# 7. Criar API de status (porta 5000)
echo "=== CRIANDO API DE STATUS ==="
cat > /opt/video-producao/bin/status_api.py <<'EOFPY'
#!/usr/bin/env python3
import json, psutil, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            config = json.loads(Path("/opt/video-producao/maquina.json").read_text())
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disco = psutil.disk_usage("/opt/video-producao")

            procs_video = sum(1 for p in psutil.process_iter(['name', 'cmdline'])
                            if 'ffmpeg' in p.info['name'].lower() or
                               ('python' in p.info['name'].lower() and
                                any('video' in str(c).lower() for c in (p.info['cmdline'] or []))))

            resp = {
                **config,
                "cpu_uso": round(cpu, 1),
                "ram_uso_percent": round(mem.percent, 1),
                "ram_livre_gb": round(mem.available / (1024**3), 2),
                "disco_livre_gb": round(disco.free / (1024**3), 2),
                "processos_video": procs_video,
                "ocupado": cpu > 80 or mem.percent > 90 or procs_video >= config["capacidades"]["nucleos"]
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"erro": str(e)}).encode())

    def log_message(self, *args): pass

if __name__ == "__main__":
    print(f"Status API rodando em http://0.0.0.0:5000 (PID: {os.getpid()})")
    HTTPServer(("0.0.0.0", 5000), StatusHandler).serve_forever()
EOFPY

chmod +x /opt/video-producao/bin/status_api.py
echo ""

# 8. Criar serviço systemd
echo "=== CRIANDO SERVIÇO SYSTEMD ==="
sudo tee /etc/systemd/system/video-status.service > /dev/null <<EOFSVC
[Unit]
Description=Video Production Status API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/video-producao
ExecStart=/usr/bin/python3 /opt/video-producao/bin/status_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFSVC

sudo systemctl daemon-reload
sudo systemctl enable video-status
sudo systemctl start video-status
sleep 2
sudo systemctl status video-status --no-pager | head -15
echo ""

# 9. Instalar e iniciar daemon worker (monitora tarefas remotas)
echo "=== INSTALANDO WORKER DAEMON ==="
cat > /opt/video-producao/bin/worker_daemon.py <<'EOFWORKER'
#!/usr/bin/env python3
import json, subprocess, time, os
from pathlib import Path
from datetime import datetime

PASTA = Path("/tmp/ia-tarefas")
MARCADOR = PASTA / "NOVA_TAREFA"

def executar(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='replace')
        return {"saida": r.stdout, "erro": r.stderr, "codigo": r.returncode, "sucesso": r.returncode == 0}
    except subprocess.TimeoutExpired:
        return {"erro": f"Timeout {timeout}s", "sucesso": False}
    except Exception as e:
        return {"erro": str(e), "sucesso": False}

def processar(arq):
    try:
        t = json.loads(arq.read_text(encoding='utf-8'))
        print(f"[{datetime.now():%H:%M:%S}] Processando: {t.get('id','?')}")
        inst = t.get("instrucoes", {})
        resp_arq = t.get("responder_em", "/tmp/ia-resposta_default.json")
        results = []

        if "passos" in inst:
            for p in inst["passos"]:
                if isinstance(p, dict):
                    for cmd in p.get("comandos", []):
                        results.append({"comando": cmd, "resultado": executar(cmd)})
                    if "script" in p:
                        results.append({"script": "ok", "resultado": executar(p["script"])})
                elif isinstance(p, str):
                    results.append({"comando": p, "resultado": executar(p)})
        elif "acao" in inst:
            if inst["acao"] == "info_sistema":
                for cmd in ["hostname", "tailscale ip -4", "nproc", "free -h"]:
                    results.append({"comando": cmd, "resultado": executar(cmd)})
            elif inst["acao"] == "verificar_disco":
                pasta = inst.get("pasta", "/opt/video-producao")
                results.append({"comando": f"df -h {pasta}", "resultado": executar(f"df -h {pasta}")})

        resp = {"tarefa_id": t.get("id"), "processado_em": datetime.now().isoformat(), "status": "SUCESSO", "resultados": results}
        Path(resp_arq).write_text(json.dumps(resp, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"[{datetime.now():%H:%M:%S}] Resposta: {resp_arq}")
        return True
    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] ERRO: {e}")
        return False

print(f"Worker Daemon PID={os.getpid()}")
PASTA.mkdir(parents=True, exist_ok=True)
while True:
    try:
        if MARCADOR.exists():
            arqs = sorted(PASTA.glob("tarefa_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if arqs:
                processar(arqs[0])
            MARCADOR.unlink(missing_ok=True)
        time.sleep(2)
    except KeyboardInterrupt:
        print("Encerrado")
        break
    except Exception as e:
        print(f"Erro loop: {e}")
        time.sleep(2)
EOFWORKER

chmod +x /opt/video-producao/bin/worker_daemon.py

# Service do worker
sudo tee /etc/systemd/system/video-worker.service > /dev/null <<EOFWSVC
[Unit]
Description=Video Production Worker Daemon
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/video-producao
ExecStart=/usr/bin/python3 /opt/video-producao/bin/worker_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFWSVC

sudo systemctl daemon-reload
sudo systemctl enable video-worker
sudo systemctl start video-worker
sleep 2
sudo systemctl status video-worker --no-pager | head -10
echo ""

# 10. Testes finais
echo "=== TESTES FINAIS ==="
echo "API status:"
curl -s http://localhost:5000/ | python3 -m json.tool

echo ""
echo "Servicos ativos:"
sudo systemctl is-active video-status video-worker

echo ""
echo "IP Tailscale:"
echo "$IP_TS"

echo ""
echo "CONFIGURACAO CONCLUIDA!"
echo ""
echo "PROXIMOS PASSOS:"
echo "1. Envie este IP ao PC1: $IP_TS"
echo "2. Do PC1 teste: curl http://$IP_TS:5000/"
echo "3. Do PC1 envie tarefa: python canal_ia_remota.py tarefa <maquina> '{\"acao\":\"info_sistema\"}'"
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Forçar UTF-8 no stdout
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    # Salvar em arquivo primeiro
    arquivo = Path("D:/video-fila/logs/instrucoes_linux.sh")
    arquivo.parent.mkdir(exist_ok=True)
    arquivo.write_text(INSTRUCOES_COMPLETAS, encoding="utf-8")

    print(f"Script bash salvo em: {arquivo}")
    print("\nCOMO USAR:")
    print("  1. Copie o conteudo do arquivo acima")
    print("  2. Cole no terminal do PC Linux (x200ma ou server2)")
    print("  3. Me envie o IP Tailscale que aparecer no final")
    print(f"\nOu leia o arquivo com: cat {arquivo}")
