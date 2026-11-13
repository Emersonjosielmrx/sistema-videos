#!/usr/bin/env python3
"""Simple exec server - replaces the Go daemon on port 8771."""
import json, subprocess, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8", errors="replace"))
            cmd = data.get("cmd", "")
            r = subprocess.run(
                cmd, shell=True, capture_output=True,
                timeout=300, cwd="C:/recapd-e-animes"
            )
            resp = {
                "returncode": r.returncode,
                "stdout": r.stdout.decode("utf-8", errors="replace"),
                "stderr": r.stderr.decode("utf-8", errors="replace"),
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"returncode": 1, "stdout": "", "stderr": str(e)}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

HTTPServer(("0.0.0.0", 8771), H).serve_forever()
