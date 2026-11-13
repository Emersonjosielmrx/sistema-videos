#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor API-fake do Roteador VEO.

Expoe o Flow (labs.google/fx) como se fosse uma API HTTP. Rode e chame:

    POST http://127.0.0.1:8790/v1/videos/generations
    { "prompt": "um gato samurai", "account": "fabrica" }

Retorna { "created":..., "data":[ {"local_path": "...", "url": "file://..."} ] }

Uso:
    python api_server.py            # sobe o servidor
    GET /health                     # ver contas disponiveis
"""
import os, json, time, threading, random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import config
import flow_bot

_lock = threading.Lock()
_account_idx = 0  # rotacao round-robin


def _accounts():
    return [f[:-5] for f in os.listdir(config.SESSIONS_DIR) if f.endswith(".json")]


def _next_account():
    global _account_idx
    accts = _accounts()
    if not accts:
        return None
    acc = accts[_account_idx % len(accts)]
    _account_idx += 1
    return acc


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silencia log padrao

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send(200, {"status": "ok", "accounts": _accounts()})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/v1/videos/generations"):
            return self._handle_generate()
        elif self.path.startswith("/v1/videos/extend"):
            return self._handle_extend()
        else:
            self._send(404, {"error": {"message": "unknown route"}})

    def _handle_generate(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            self._send(400, {"error": {"message": f"json invalido: {e}"}})
            return

        prompt = (req.get("prompt") or "").strip()
        if not prompt:
            self._send(400, {"error": {"message": "prompt obrigatorio"}})
            return

        accts = _accounts()
        if not accts:
            self._send(503, {"error": {"message": "nenhuma sessao. rode capture_session.py"}})
            return
        account = req.get("account")
        if account == "auto" or not account:
            account = _next_account()
        if account not in accts:
            self._send(400, {"error": {"message": f"conta '{account}' nao existe. use: {accts}"}})
            return

        logs = []
        def log(msg):
            logs.append(msg)
            print(msg, flush=True)

        kwargs = {
            "aspect_ratio": req.get("aspect_ratio"),
            "duration": req.get("duration"),
            "model": req.get("model"),
            "audio": req.get("audio"),
            "image": req.get("image"),
        }
        if "auto_confirm" in req:
            kwargs["auto_confirm"] = bool(req.get("auto_confirm"))
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        with _lock:
            try:
                path = flow_bot.generate(account, prompt, log=log, **kwargs)
            except Exception as e:
                self._send(502, {"error": {"message": str(e)}, "logs": logs})
                return

        self._send(200, {
            "created": int(time.time()),
            "data": [{
                "local_path": path,
                "url": "file:///" + path.replace("\\", "/"),
                "format": "mp4",
            }],
            "account": account,
            "params": kwargs,
        })

    def _handle_extend(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            self._send(400, {"error": {"message": f"json invalido: {e}"}})
            return

        video_path = (req.get("video_path") or "").strip()
        if not video_path or not os.path.exists(video_path):
            self._send(400, {"error": {"message": f"video_path invalido ou nao encontrado: {video_path}"}})
            return

        accts = _accounts()
        if not accts:
            self._send(503, {"error": {"message": "nenhuma sessao"}})
            return
        account = req.get("account")
        if account == "auto" or not account:
            account = _next_account()
        if account not in accts:
            self._send(400, {"error": {"message": f"conta '{account}' nao existe. use: {accts}"}})
            return

        logs = []
        def log(msg):
            logs.append(msg)
            print(msg, flush=True)

        kwargs = {}
        if req.get("prompt"):
            kwargs["extend_prompt"] = req["prompt"]
        if req.get("model"):
            kwargs["model"] = req["model"]
        if req.get("audio") is not None:
            kwargs["audio"] = req["audio"]

        with _lock:
            try:
                path = flow_bot.extend(account, video_path, log=log, **kwargs)
            except Exception as e:
                self._send(502, {"error": {"message": str(e)}, "logs": logs})
                return

        self._send(200, {
            "created": int(time.time()),
            "data": [{
                "local_path": path,
                "url": "file:///" + path.replace("\\", "/"),
                "format": "mp4",
            }],
            "account": account,
            "original_video": video_path,
        })


def main():
    srv = ThreadingHTTPServer((config.API_HOST, config.API_PORT), Handler)
    print(f"Roteador VEO API-fake em http://{config.API_HOST}:{config.API_PORT}")
    print(f"Contas: {_accounts() or '(nenhuma — rode capture_session.py)'}")
    print("POST /v1/videos/generations  { prompt, account? }")
    srv.serve_forever()


if __name__ == "__main__":
    main()
