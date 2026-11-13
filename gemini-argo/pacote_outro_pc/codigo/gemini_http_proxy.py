#!/usr/bin/env python3
r"""gemini_http_proxy.py — Proxy OpenAI-compatible para o Gemini via HTTP puro.

Mesma interface do gemini_proxy.py (navegador), mas por baixo usa o gemini_http
(sem Chrome): mais rápido, mais leve e com streaming real token-a-token.

Roda local; o OmniRoute / Claude Code se conecta aqui.

Uso:
    python gemini_http_proxy.py            # porta 20141
    python gemini_http_proxy.py --porta 20141
"""
import json
import sys
import time
import threading
import uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, r"D:\gemini-argo")
import gemini_http

# HTTP é leve, mas cada conta responde uma pergunta por vez: uma vaga por conta do rodízio (27/10: eram 6 fixas)
VAGAS = threading.BoundedSemaphore(max(6, len(gemini_http._ler_contas()["contas"])))

MODELO_PADRAO = "argon"


def _mapear_modelo(nome):
    n = (nome or "").lower()
    if "flash-lite" in n or "flash_lite" in n:
        return "flash-lite"
    if "flash" in n:
        return "flash"
    if "pro" in n:
        return "pro"
    return "argon"


def _montar_prompt(messages):
    partes = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(p.get("text", "") for p in content if p.get("type") == "text")
        if role == "system":
            partes.append(f"[Instrução do sistema]\n{content}")
        elif role == "assistant":
            partes.append(f"[Assistente]\n{content}")
        else:
            partes.append(content)
    return "\n\n".join(partes)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {fmt % args}\n")

    def _erro(self, codigo, msg):
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": {"message": msg, "type": "server_error"}}).encode())

    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/chat/completions"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        prompt = _montar_prompt(body.get("messages", []))
        stream = body.get("stream", False)
        modelo = _mapear_modelo(body.get("model"))
        chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        ts = int(time.time())

        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                with VAGAS:
                    mandou = False
                    for delta in gemini_http.perguntar_stream(prompt, modelo=modelo):
                        if not mandou:
                            # primeiro chunk com role
                            delta_obj = {"role": "assistant", "content": delta}
                            mandou = True
                        else:
                            delta_obj = {"content": delta}
                        chunk = {"id": chat_id, "object": "chat.completion.chunk", "created": ts,
                                 "model": f"gemini-4-{modelo}",
                                 "choices": [{"index": 0, "delta": delta_obj, "finish_reason": None}]}
                        self.wfile.write(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                if not mandou:
                    raise RuntimeError("resposta vazia")
            except Exception as e:
                err = {"id": chat_id, "object": "chat.completion.chunk", "created": ts,
                       "model": f"gemini-4-{modelo}",
                       "choices": [{"index": 0, "delta": {"content": f"\n[erro Argon: {e}]"},
                                    "finish_reason": "stop"}]}
                try:
                    self.wfile.write(f"data: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8"))
                except Exception:
                    return
            stop = {"id": chat_id, "object": "chat.completion.chunk", "created": ts,
                    "model": f"gemini-4-{modelo}",
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
            self.wfile.write(f"data: {json.dumps(stop)}\n\n".encode())
            self.wfile.write(b"data: [DONE]\n\n")
            return

        # não-streaming
        try:
            with VAGAS:
                resposta = gemini_http.perguntar(prompt, modelo=modelo)
        except Exception as e:
            self._erro(500, str(e))
            return
        if not resposta:
            self._erro(500, "Argon retornou resposta vazia")
            return
        result = {"id": chat_id, "object": "chat.completion", "created": ts, "model": f"gemini-4-{modelo}",
                  "choices": [{"index": 0, "message": {"role": "assistant", "content": resposta},
                               "finish_reason": "stop"}],
                  "usage": {"prompt_tokens": len(prompt) // 4, "completion_tokens": len(resposta) // 4,
                            "total_tokens": (len(prompt) + len(resposta)) // 4}}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path in ("/v1/models", "/models"):
            data = {"object": "list", "data": [
                {"id": f"gemini-4-{m}", "object": "model", "owned_by": "google", "created": int(time.time())}
                for m in gemini_http.MODELOS]}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
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
    p.add_argument("--porta", type=int, default=20141)
    args = p.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.porta), Handler)
    print(f"Gemini HTTP proxy (sem navegador) em http://127.0.0.1:{args.porta}")
    print("  POST /v1/chat/completions   GET /v1/models")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
