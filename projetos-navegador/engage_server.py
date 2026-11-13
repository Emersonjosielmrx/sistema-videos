import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import os
import subprocess
import time
import sys

sys.path.append("D:/projetos-navegador")

CONFIG_FILE = Path("D:/projetos-navegador/engage_config.json")
STOP_FLAG = Path("D:/projetos-navegador/engage_stop.flag")
RESTART_FLAG = Path("D:/projetos-navegador/engage_restart.flag")
PROGRESS_FILE = Path("D:/projetos-navegador/mega_engage_progress.json")
LOG_FILE = Path("D:/projetos-navegador/mega_engage_log.txt")

class EngageHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Rebuild panel before serving
            try:
                subprocess.run(["D:/hipercool-videos/venv/Scripts/python.exe", "D:/projetos-navegador/build_painel.py"], capture_output=True)
            except Exception as e:
                print(f"Error rebuilding panel: {e}")
                
            try:
                with open("D:/projetos-navegador/painel_engage.html", "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            except Exception as e:
                self.wfile.write(f"Error reading panel: {e}".encode("utf-8"))
                
        elif self.path == '/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            except Exception:
                self.wfile.write(json.dumps({}).encode("utf-8"))
                
        elif self.path == '/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                result = subprocess.run(["D:/hipercool-videos/venv/Scripts/python.exe", "D:/projetos-navegador/build_painel.py", "--json"], capture_output=True, text=True)
                self.wfile.write(result.stdout.encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif self.path == '/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                result = subprocess.run(["D:/hipercool-videos/venv/Scripts/python.exe", "D:/projetos-navegador/build_painel.py", "--json"], capture_output=True, text=True)
                # O script build_painel.py agora pode precisar cuspir só o JSON se `--json` for passado, 
                # mas pra nao mudar o build_painel.py só pra isso, vamos ler o json gerado por ele e retornar.
                # Ele dá print do json, entao vamos usar stdout:
                self.wfile.write(result.stdout.encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            
    def do_POST(self):
        if self.path == '/save-config':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_data)
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"msg": "Configuracao salva com sucesso!"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                
        elif self.path == '/pause':
            try:
                if CONFIG_FILE.exists():
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    data = {}
                data["paused"] = not data.get("paused", False)
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"paused": data["paused"], "msg": "Robo pausado" if data["paused"] else "Robo retomado"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()

        elif self.path == '/restart':
            RESTART_FLAG.touch()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"msg": "Reiniciando robo no proximo ciclo..."}).encode("utf-8"))

        elif self.path == '/stop':
            STOP_FLAG.touch()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"msg": "Parada de emergencia enviada!"}).encode("utf-8"))

        elif self.path == '/clear-progress':
            try:
                if PROGRESS_FILE.exists():
                    PROGRESS_FILE.unlink()
                if LOG_FILE.exists():
                    LOG_FILE.unlink()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"msg": "Progresso e logs limpos!"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server_address = ('', 8850)
    httpd = HTTPServer(server_address, EngageHTTPRequestHandler)
    print("Serving on http://localhost:8850")
    httpd.serve_forever()
