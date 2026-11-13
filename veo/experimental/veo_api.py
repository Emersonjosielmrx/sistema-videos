#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Veo API (assincrona) para o n8n.

Expoe o Google Flow/Veo (via gera_auto.py + Chrome CDP) como uma API HTTP que o
n8n REMOTO pode chamar. O render leva de 1 a 15 min, entao o fluxo e assincrono:

  1) n8n faz POST /v1/jobs  { "prompt": "...", "aspect": "9:16", ... }
     -> resposta imediata: { "job_id": "...", "status": "queued" }
  2) n8n faz GET /v1/jobs/{job_id} em loop (polling)
     -> { "status": "running" } ... ate ... { "status": "done", "video_url": "..." }
  3) n8n baixa GET {video_url}  (o proprio servidor serve o mp4)

Config por env:
  VEO_API_HOST   (default 0.0.0.0  — escuta em todas as interfaces p/ n8n remoto)
  VEO_API_PORT   (default 8799)
  VEO_PUBLIC_URL (default http://<host>:<port> — base das video_url; troque pelo
                  IP publico ou URL do tunel/ngrok quando o n8n for remoto)
  VEO_API_TOKEN  (opcional; se setado, exige header Authorization: Bearer <token>)
  FLOW_PORT      (porta CDP do Chrome logado no Flow; default 9224 = conta seebotsia)
  FLOW_PROJ      (URL do projeto Flow da conta)

Uma geracao por vez (o Flow/Chrome e recurso unico): _gen_lock serializa.
"""
import os, sys, json, time, uuid, threading, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gera_auto

HOST = os.environ.get("VEO_API_HOST", "0.0.0.0")
PORT = int(os.environ.get("VEO_API_PORT", "8799"))
PUBLIC_URL = os.environ.get("VEO_PUBLIC_URL", f"http://127.0.0.1:{PORT}").rstrip("/")
TOKEN = os.environ.get("VEO_API_TOKEN", "").strip()
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos", "api_jobs")
os.makedirs(OUT_DIR, exist_ok=True)

_JOBS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs_state.json")

_jobs = {}            # job_id -> dict(status, prompt, video_path, error, logs, ...)
_jobs_lock = threading.Lock()
_gen_lock = threading.Lock()  # so 1 render por vez (Chrome/Flow e recurso unico)


def _persist_jobs():
    """Salva _jobs em disco (chamado dentro de _jobs_lock)."""
    try:
        snapshot = {jid: {k: v for k, v in j.items() if k != "logs"}
                    for jid, j in _jobs.items()}
        tmp = _JOBS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False)
        os.replace(tmp, _JOBS_FILE)
    except Exception as e:
        print(f"[persist] erro ao salvar jobs: {e}", flush=True)


def _load_jobs():
    """Carrega jobs do disco na inicializacao."""
    global _jobs
    if not os.path.exists(_JOBS_FILE):
        return
    try:
        with open(_JOBS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        for jid, j in data.items():
            j.setdefault("logs", [])
            if j.get("status") == "running":
                j["status"] = "error"
                j["error"] = "servidor reiniciou durante render"
            _jobs[jid] = j
        print(f"[persist] {len(_jobs)} jobs restaurados do disco", flush=True)
    except Exception as e:
        print(f"[persist] erro ao carregar jobs: {e}", flush=True)


def _now():
    return int(time.time())


def _run_job(job_id):
    """Roda em thread: chama gera_auto.gerar() e atualiza o job."""
    with _jobs_lock:
        job = _jobs[job_id]
        prompt = job["prompt"]
        aspect = job["aspect"]
        modelo = job["model"]
        duration = job["duration"]
        image = job["image"]
    out_path = os.path.join(OUT_DIR, f"{job_id}.mp4")

    logs = []
    def log(msg):
        logs.append(str(msg))
        with _jobs_lock:
            _jobs[job_id]["logs"] = logs[-200:]
        print(f"[{job_id[:8]}] {msg}", flush=True)

    with _gen_lock:  # serializa: Flow/Chrome nao suporta 2 renders juntos
        with _jobs_lock:
            _jobs[job_id]["status"] = "running"
            _jobs[job_id]["started_at"] = _now()
            _persist_jobs()
        try:
            gera_auto.gerar(prompt, out_path, image=image, aspect=aspect,
                            modelo=modelo, duration=duration, log=log)
            ok = os.path.exists(out_path) and os.path.getsize(out_path) > 100_000
            with _jobs_lock:
                if ok:
                    _jobs[job_id]["status"] = "done"
                    _jobs[job_id]["video_path"] = out_path
                    _jobs[job_id]["video_url"] = f"{PUBLIC_URL}/v1/jobs/{job_id}/video"
                    _jobs[job_id]["bytes"] = os.path.getsize(out_path)
                else:
                    _jobs[job_id]["status"] = "error"
                    _jobs[job_id]["error"] = "render terminou sem mp4 valido"
                _jobs[job_id]["finished_at"] = _now()
                _persist_jobs()
        except Exception as e:
            log("ERRO: " + repr(e))
            log(traceback.format_exc())
            with _jobs_lock:
                _jobs[job_id]["status"] = "error"
                _jobs[job_id]["error"] = str(e)
                _jobs[job_id]["finished_at"] = _now()
                _persist_jobs()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _auth_ok(self):
        if not TOKEN:
            return True
        got = self.headers.get("Authorization", "")
        return got == f"Bearer {TOKEN}"

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path):
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition",
                         f'attachment; filename="{os.path.basename(path)}"')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            with _jobs_lock:
                n = len(_jobs)
            self._send(200, {"status": "ok", "jobs": n,
                             "flow_port": gera_auto.PORT, "public_url": PUBLIC_URL})
            return
        if not self._auth_ok():
            self._send(401, {"error": "unauthorized"})
            return
        # GET /v1/jobs/{id}  ou  /v1/jobs/{id}/video
        parts = self.path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "v1" and parts[1] == "jobs":
            job_id = parts[2]
            with _jobs_lock:
                job = _jobs.get(job_id)
            if not job:
                self._send(404, {"error": "job nao encontrado"})
                return
            if len(parts) == 4 and parts[3] == "video":
                if job["status"] == "done" and os.path.exists(job["video_path"]):
                    self._send_file(job["video_path"])
                else:
                    self._send(409, {"error": "video ainda nao pronto",
                                     "status": job["status"]})
                return
            # status do job (sem os bytes)
            self._send(200, {k: v for k, v in job.items() if k != "video_path"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth_ok():
            self._send(401, {"error": "unauthorized"})
            return
        if self.path.rstrip("/") != "/v1/jobs":
            self._send(404, {"error": "unknown route"})
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            self._send(400, {"error": f"json invalido: {e}"})
            return
        prompt = (req.get("prompt") or "").strip()
        if not prompt:
            self._send(400, {"error": "prompt obrigatorio"})
            return
        job_id = uuid.uuid4().hex
        with _jobs_lock:
            _jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "prompt": prompt,
                "aspect": req.get("aspect", "9:16"),
                "model": req.get("model", "Veo 3.1 - Fast"),
                "duration": req.get("duration", "8S"),
                "image": req.get("image"),
                "created_at": _now(),
                "logs": [],
            }
            _persist_jobs()
        threading.Thread(target=_run_job, args=(job_id,), daemon=True).start()
        self._send(202, {"job_id": job_id, "status": "queued",
                         "status_url": f"{PUBLIC_URL}/v1/jobs/{job_id}"})


def main():
    _load_jobs()
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Veo API em http://{HOST}:{PORT}  (public: {PUBLIC_URL})", flush=True)
    print(f"Flow CDP port: {gera_auto.PORT}", flush=True)
    print("POST /v1/jobs {prompt, aspect?, model?, duration?, image?}", flush=True)
    print("GET  /v1/jobs/{id}        -> status", flush=True)
    print("GET  /v1/jobs/{id}/video  -> mp4", flush=True)
    if TOKEN:
        print("auth: Bearer token EXIGIDO", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
