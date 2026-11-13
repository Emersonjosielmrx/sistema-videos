# -*- coding: utf-8 -*-
"""Daemon HTTP minimal para execucao de comandos no PC2.

Endpoints:
  POST /exec  {"cmd": "...", "cwd": "C:/", "timeout": 300}
    Executa comando via cmd.exe (shell). Retorna {returncode, stdout, stderr}.

  POST /run   {"script": "python code..."}
    Executa codigo Python diretamente (sem cmd.exe, UNC paths funcionam).
    Retorna {returncode, stdout, stderr}.
"""
import http.server, json, socket, threading, os, subprocess, sys, io

PORT = 8771


class ExecHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/exec":
            self._handle_exec()
        elif self.path == "/run":
            self._handle_run()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = json.dumps({"host": socket.gethostname(), "python": sys.version.split()[0]})
            self.wfile.write(resp.encode())
        else:
            self.send_error(404)

    def _handle_exec(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            cmd = body.get("cmd", "")
            cwd = body.get("cwd", "C:/")
        except Exception as e:
            self.send_error(400, str(e))
            return

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=body.get("timeout", 300),
            )
            self._json_resp({"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        except subprocess.TimeoutExpired:
            self._json_resp({"returncode": -2, "stdout": "", "stderr": "timeout"}, code=408)
        except Exception as e:
            self._json_resp({"returncode": -1, "stdout": "", "stderr": str(e)}, code=500)

    def _handle_run(self):
        """Executa codigo Python diretamente — sem cmd.exe shell."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            script = body.get("script", "")
        except Exception as e:
            self.send_error(400, str(e))
            return

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        local_vars = {"__name__": "__daemon__"}
        rc = 0

        try:
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout = stdout_buf
            sys.stderr = stderr_buf
            try:
                exec(script, local_vars)
            finally:
                sys.stdout = old_out
                sys.stderr = old_err
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 0
        except Exception as e:
            rc = 1
            stderr_buf.write(f"{type(e).__name__}: {e}")

        self._json_resp({
            "returncode": rc,
            "stdout": stdout_buf.getvalue(),
            "stderr": stderr_buf.getvalue(),
        })

    def _json_resp(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, fmt, *args):
        print(f"[{args[0]}]", flush=True)


if __name__ == "__main__":
    print(f"Daemon starting on port {PORT}...", flush=True)
    while True:
        try:
            server = http.server.HTTPServer(("0.0.0.0", PORT), ExecHandler)
            print(f"Daemon running on http://0.0.0.0:{PORT}", flush=True)
            server.serve_forever()
        except Exception as e:
            print(f"Daemon crashed: {e}, restarting in 5s...", flush=True)
            import time; time.sleep(5)
