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
import socket
import sys
import time
import threading
import uuid
from datetime import datetime
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


# ─────────── 29/10: reuso de conversa (dona: "não mandar a conversa toda de novo") ───────────
# Depois de cada resposta guardo {conta, modelo, ids da conversa do Gemini} pela chave = hash das mensagens enviadas.
# No turno seguinte o Claude Code reenvia essas mesmas mensagens + a resposta (assistant) + o que é novo: se o começo
# bate, mando SÓ do assistant em diante, continuando a mesma conversa na mesma conta. Qualquer falha = histórico
# inteiro como antes. A resposta do assistant entra de novo porque pode ter vindo do modelo reserva (híbridos).
import hashlib  # noqa: E402

CONVERSAS = {}
_trava_conv = threading.Lock()
CONV_TTL = 60 * 60
CONV_MAX = 400
REUSO = {"acertos": 0, "erros": 0, "pulados": 0, "chars_poupados": 0}


def _texto_msg(msg):
    content = msg.get("content", "")
    if isinstance(content, list):
        content = " ".join(p.get("text", "") for p in content if p.get("type") == "text")
    return " ".join(str(content).split())


def _chave(msgs):
    norm = [[m.get("role", "user"), _texto_msg(m)] for m in msgs]
    return hashlib.sha1(json.dumps(norm, ensure_ascii=False).encode("utf-8")).hexdigest()


def _achar_continuacao(msgs, modelo):
    """(sessão guardada, índice do assistant) se o histórico continua uma conversa conhecida; senão None."""
    if len(msgs) < 3:
        return None
    agora = time.time()
    with _trava_conv:
        for i in range(len(msgs) - 1, 0, -1):
            if msgs[i].get("role") != "assistant":
                continue
            s = CONVERSAS.get(_chave(msgs[:i]))
            if s and s["modelo"] == modelo and agora - s["t"] < CONV_TTL:
                if not _conta_pronta(s["conta"]):
                    # 30/10: conta da conversa já marcada sem cota/cookie morto: ir direto ao histórico inteiro (antes
                    # gastava um pedido ao Google só para ouvir "Flash Lite (limite atingido)": 28 vezes em 1 dia)
                    REUSO["pulados"] += 1
                    return None
                return s, i
    return None


def _conta_pronta(apelido):
    agora = datetime.now().isoformat()
    try:
        return any(c["apelido"] == apelido and gemini_http.pronta(c, agora) for c in gemini_http._ler_contas()["contas"])
    except (OSError, ValueError):
        return True  # não deu para ler a fila: tenta como antes


def _guardar(msgs):
    info = getattr(gemini_http.ULTIMA, "info", None)
    if not info:
        return
    with _trava_conv:
        if len(CONVERSAS) >= CONV_MAX:
            for k in sorted(CONVERSAS, key=lambda k: CONVERSAS[k]["t"])[:CONV_MAX // 4]:
                CONVERSAS.pop(k, None)
        CONVERSAS[_chave(msgs)] = {**info, "t": time.time()}


def _prompt_continuacao(msgs, i):
    return ("[Continuação desta mesma conversa. O que foi executado depois da sua última resposta e as mensagens "
            "novas vêm abaixo; as instruções do sistema continuam valendo.]\n\n" + _montar_prompt(msgs[i:]))


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
        sem_cota = "Nenhuma conta com cota" in msg
        self.send_response(429 if sem_cota else codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": {"message": msg, "type": "sem_cota" if sem_cota else "server_error"}},
                                    ensure_ascii=False).encode("utf-8"))

    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/chat/completions"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length)) if length else {}
        except ValueError as e:
            self._erro(400, f"JSON inválido: {e}")
            return
        prompt = _montar_prompt(body.get("messages", []))
        stream = body.get("stream", False)
        modelo = _mapear_modelo(body.get("model"))
        chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        ts = int(time.time())

        if not VAGAS.acquire(timeout=120):  # 29/10: antes esperava sem limite; cliente recebe 503 e tenta outro provedor
            self._erro(503, "Argon lotado (todas as vagas ocupadas há 2 min)")
            return
        try:
            self._atender(body, prompt, stream, modelo, chat_id, ts)
        finally:
            VAGAS.release()

    def _cliente_foi_embora(self):
        """Conexão do cliente fechada? (socket legível e recv com PEEK vazio = o outro lado fechou)."""
        import select
        try:
            legivel, _, _ = select.select([self.connection], [], [], 0)
            return bool(legivel) and self.connection.recv(1, socket.MSG_PEEK) == b""
        except OSError:
            return True

    def _gerador(self, msgs, prompt, modelo):
        """Deltas da resposta: tenta continuar a conversa guardada (só o turno novo, mesma conta); se falhar ANTES do
        1º pedaço, faz como antes (histórico inteiro, fila de contas)."""
        gemini_http.ULTIMA.info = None
        cont = _achar_continuacao(msgs, modelo)
        if cont:
            s, i = cont
            curto = _prompt_continuacao(msgs, i)
            mandou = False
            try:
                for d in gemini_http.perguntar_stream(curto, conta=s["conta"], modelo=modelo, tentativas=1,
                                                       meta=s["meta"]):
                    mandou = True
                    yield d
                REUSO["acertos"] += 1
                REUSO["chars_poupados"] += max(0, len(prompt) - len(curto))
                sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] reuso: {s['conta']} mandou {len(curto)} chars em vez "
                                 f"de {len(prompt)} ({REUSO['acertos']} acertos, {REUSO['erros']} falhas)\n")
                return
            except Exception as e:  # noqa: BLE001
                if mandou:
                    raise
                REUSO["erros"] += 1
                sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] reuso falhou ({str(e)[:80]}): histórico inteiro\n")
                gemini_http.ULTIMA.info = None
        yield from gemini_http.perguntar_stream(prompt, modelo=modelo)

    def _atender(self, body, prompt, stream, modelo, chat_id, ts):
        msgs = body.get("messages", [])
        if not stream:
            # não-streaming (o proxy da VPS usa assim com ferramentas): junta os deltas do mesmo gerador
            partes = []
            gerador = self._gerador(msgs, prompt, modelo)
            try:
                for d in gerador:
                    partes.append(d)
                    if self._cliente_foi_embora():
                        # 30/10: a VPS desistiu (Esc no Claude Code, prazo): corta o Gemini e libera a conta e a vaga
                        # (antes ia até o fim da resposta, minutos, para jogar fora)
                        gerador.close()
                        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] cliente desistiu no meio: Argon cortado "
                                         f"({sum(map(len, partes))} chars)\n")
                        return
                resposta = "".join(partes)
            except Exception as e:  # noqa: BLE001
                self._erro(500, str(e))
                return
            if not resposta.strip():
                self._erro(500, "Argon retornou resposta vazia")
                return
            _guardar(msgs)
            result = {"id": chat_id, "object": "chat.completion", "created": ts, "model": f"gemini-4-{modelo}",
                      "choices": [{"index": 0, "message": {"role": "assistant", "content": resposta},
                                   "finish_reason": "stop"}],
                      "usage": {"prompt_tokens": len(prompt) // 4, "completion_tokens": len(resposta) // 4,
                                "total_tokens": (len(prompt) + len(resposta)) // 4}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return
        if stream:
            # 28/10: cabeçalho só no 1º pedaço; erro antes dele (sem cota) vira status de erro, não texto da resposta
            mandou = False
            tudo = []
            try:
                if True:
                    for delta in self._gerador(msgs, prompt, modelo):
                        tudo.append(delta)
                        if not mandou:
                            self.send_response(200)
                            self.send_header("Content-Type", "text/event-stream")
                            self.send_header("Cache-Control", "no-cache")
                            self.end_headers()
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
                if not mandou:
                    self._erro(500, str(e))
                    return
                # 29/10 (Fable): erro no meio do stream vai como evento de erro (o cliente vê falha), não como texto
                # da resposta com status 200
                err = {"id": chat_id, "object": "chat.completion.chunk", "created": ts, "model": f"gemini-4-{modelo}",
                       "choices": [{"index": 0, "delta": {}, "finish_reason": "error"}],
                       "error": {"message": f"Argon: {e}", "type": "server_error"}}
                try:
                    self.wfile.write(f"data: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8"))
                    self.wfile.write(b"data: [DONE]\n\n")
                except Exception:
                    pass
                return
            stop = {"id": chat_id, "object": "chat.completion.chunk", "created": ts,
                    "model": f"gemini-4-{modelo}",
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
            self.wfile.write(f"data: {json.dumps(stop)}\n\n".encode())
            self.wfile.write(b"data: [DONE]\n\n")
            _guardar(msgs)
            return

    def do_GET(self):
        if self.path in ("/v1/models", "/models"):
            data = {"object": "list", "data": [
                {"id": f"gemini-4-{m}", "object": "model", "owned_by": "google", "created": int(time.time())}
                for m in gemini_http.MODELOS]}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        elif self.path == "/cota":
            # Quantas contas estão prontas na fila, sem gastar pergunta (o proxy da VPS confere antes de cada pedido)
            from datetime import datetime
            agora = datetime.now().isoformat()
            contas = gemini_http._ler_contas()["contas"]
            prontas = [c for c in contas if gemini_http.pronta(c, agora)]
            volta = min((c["sem_cota_ate"] for c in contas if c.get("sem_cota_ate") and c["sem_cota_ate"] > agora), default=None)
            mortas = sum(1 for c in contas if c.get("cookies_mortos_ate") and agora < c["cookies_mortos_ate"])
            sem_cota = sum(1 for c in contas if c.get("sem_cota_ate") and agora < c["sem_cota_ate"])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"prontas": len(prontas), "contas": len(contas), "cookies_mortos": mortas,
                                         "sem_cota": sem_cota, "volta": volta[11:16] if volta else None,
                                         "reuso": {**REUSO, "conversas": len(CONVERSAS)}}).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_error(404)


class Servidor(ThreadingHTTPServer):
    """30/10: porta EXCLUSIVA. O ThreadingHTTPServer liga SO_REUSEADDR, que no Windows deixa um 2º processo escutar na
    mesma porta (visto: 2 proxies na :20141, pedidos caindo no que ainda estava subindo e /health levando 25 s). Agora o
    2º falha ao subir e o argon_manter percebe."""
    allow_reuse_address = False
    daemon_threads = True

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def handle_error(self, request, client_address):
        # cliente que desistiu (timeout do /health, VPS que cortou) não é erro do proxy: uma linha, sem traceback
        e = sys.exc_info()[1]
        if isinstance(e, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] cliente {client_address[0]} fechou a conexão ({type(e).__name__})\n")
            return
        super().handle_error(request, client_address)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=20141)
    args = p.parse_args()
    try:
        server = Servidor(("127.0.0.1", args.porta), Handler)
    except OSError as e:
        print(f"porta {args.porta} já em uso por outro proxy ({e}); saindo", file=sys.stderr)
        sys.exit(3)
    print(f"Gemini HTTP proxy (sem navegador) em http://127.0.0.1:{args.porta}")
    print("  POST /v1/chat/completions   GET /v1/models")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
