#!/usr/bin/env python3
r"""Proxy OpenAI-compatible que roteia pro Gemini Argon via browser.

Roda no PC local e aceita chamadas /v1/chat/completions.
O OmniRoute ou Claude Code se conecta aqui.

Uso:
    python gemini_proxy.py                 # porta 20140
    python gemini_proxy.py --porta 20140
"""
import json
import sys
import time
import threading
import uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, r"D:\gemini-argo")
from gemini_argon import perguntar

# Cada pedido abre um Chrome; mais de 2 ao mesmo tempo estoura a RAM do PC1
VAGAS = threading.BoundedSemaphore(2)


class GeminiHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {fmt % args}\n")

    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/chat/completions"):
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        messages = body.get("messages", [])
        stream = body.get("stream", False)

        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") for p in content if p.get("type") == "text"
                )
            if role == "system":
                prompt_parts.append(f"[Instrução do sistema]\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"[Assistente]\n{content}")
            else:
                prompt_parts.append(content)

        prompt = "\n\n".join(prompt_parts)

        try:
            with VAGAS:
                resposta = perguntar(prompt, raciocinio_alto=True, visivel=False)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": {"message": str(e), "type": "server_error"}
            }).encode())
            return

        if not resposta:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": {"message": "Argon retornou resposta vazia", "type": "server_error"}
            }).encode())
            return

        chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        ts = int(time.time())

        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()

            content_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": ts,
                "model": "gemini-4-argon",
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": resposta or ""},
                    "finish_reason": None,
                }],
            }
            self.wfile.write(f"data: {json.dumps(content_chunk)}\n\n".encode())
            stop_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": ts,
                "model": "gemini-4-argon",
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }],
            }
            self.wfile.write(f"data: {json.dumps(stop_chunk)}\n\n".encode())
            self.wfile.write(b"data: [DONE]\n\n")
        else:
            result = {
                "id": chat_id,
                "object": "chat.completion",
                "created": ts,
                "model": "gemini-4-argon",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": resposta},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": len(prompt) // 4, "completion_tokens": len(resposta) // 4, "total_tokens": (len(prompt) + len(resposta)) // 4},
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

    def do_GET(self):
        if self.path in ("/v1/models", "/models"):
            models = {
                "object": "list",
                "data": [
                    {"id": "gemini-4-argon", "object": "model", "owned_by": "google", "created": int(time.time())},
                ],
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(models).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_error(404)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=20140)
    args = p.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.porta), GeminiHandler)
    print(f"Gemini Argon proxy rodando em http://127.0.0.1:{args.porta}")
    print(f"  POST /v1/chat/completions  (OpenAI-compatible)")
    print(f"  GET  /v1/models")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nParando...")
        server.shutdown()


if __name__ == "__main__":
    main()
