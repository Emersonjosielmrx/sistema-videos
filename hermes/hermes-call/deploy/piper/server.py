# -*- coding: utf-8 -*-
"""Piper TTS - servidor HTTP local (127.0.0.1:8090).
Carrega as vozes UMA vez na memoria (sem reload por request => baixa latencia).
Endpoints:
  GET  /health                      -> {"status":"ok","voices":[...]}
  POST /tts        (JSON)           -> audio/wav   (WAV completo)
  POST /tts/stream (JSON)           -> audio raw PCM s16le em chunks (menor TTFB p/ VoIP)
Body JSON: {"text":"...", "voice":"faber"}   # voice opcional (default faber)
"""
import io, json, wave, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from piper import PiperVoice

MODELS_DIR = "/opt/piper-tts/models"
HOST, PORT = "127.0.0.1", 8090
DEFAULT_VOICE = "faber"

# mapeia nome curto -> arquivo .onnx
VOICE_FILES = {
    "faber": f"{MODELS_DIR}/pt_BR-faber-medium.onnx",
    "jeff":  f"{MODELS_DIR}/pt_BR-jeff-medium.onnx",
    "cadu":  f"{MODELS_DIR}/pt_BR-cadu-medium.onnx",
}

print("carregando vozes...", flush=True)
VOICES = {}
for name, path in VOICE_FILES.items():
    if os.path.exists(path):
        VOICES[name] = PiperVoice.load(path)
        print(f"  ok: {name}", flush=True)
print(f"pronto. vozes: {list(VOICES.keys())}", flush=True)


def synth_wav_bytes(voice, text):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        voice.synthesize_wav(text, wf)
    return buf.getvalue()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silencia log ruidoso
        pass

    def _json_body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def _err(self, code, msg):
        b = json.dumps({"error": msg}).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path == "/health":
            b = json.dumps({"status": "ok", "voices": list(VOICES.keys())}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        else:
            self._err(404, "not found")

    def do_POST(self):
        try:
            data = self._json_body()
        except Exception:
            return self._err(400, "invalid json")
        text = (data.get("text") or "").strip()
        vname = data.get("voice") or DEFAULT_VOICE
        if not text:
            return self._err(400, "missing 'text'")
        voice = VOICES.get(vname)
        if voice is None:
            return self._err(400, f"unknown voice '{vname}', use {list(VOICES.keys())}")

        if self.path == "/tts":
            audio = synth_wav_bytes(voice, text)
            self.send_response(200); self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(audio))); self.end_headers()
            self.wfile.write(audio)

        elif self.path == "/tts/stream":
            # PCM cru s16le em chunked -> menor tempo ate o 1o byte (ideal VoIP)
            self.send_response(200)
            self.send_header("Content-Type", "audio/L16")
            self.send_header("X-Sample-Rate", str(voice.config.sample_rate))
            self.send_header("Transfer-Encoding", "chunked"); self.end_headers()
            try:
                for chunk in voice.synthesize(text):
                    pcm = chunk.audio_int16_bytes
                    self.wfile.write(f"{len(pcm):X}\r\n".encode()); self.wfile.write(pcm); self.wfile.write(b"\r\n")
                self.wfile.write(b"0\r\n\r\n")
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self._err(404, "not found")


if __name__ == "__main__":
    srv = ThreadingHTTPServer((HOST, PORT), H)
    print(f"escutando http://{HOST}:{PORT}", flush=True)
    srv.serve_forever()
