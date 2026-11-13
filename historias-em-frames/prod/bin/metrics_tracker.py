# -*- coding: utf-8 -*-
"""metrics_tracker.py — Coleta de métricas granulares por geração de vídeo.

Grava 1 linha JSONL por vídeo em logs/pipeline_metrics.jsonl com:
  - tempo por ETAPA (roteiro, imagens, tts, render, concat, pos, censura...)
  - hardware (pico de RAM/CPU durante a geração)
  - contadores de erro/recuperação (429/402, fallback pollinations, proxy morto, quarentena)
  - resultado (ok/fail), duração final do vídeo, genero, story_id

Formato JSONL (1 objeto por linha) pra ser trivial de parsear depois em
pandas/Grafana/qualquer dashboard. NÃO usa nenhuma API externa — só psutil local
(com fallback silencioso se psutil faltar).

Uso no pipeline:
    from metrics_tracker import MetricsTracker
    mt = MetricsTracker(story_id, genero, titulo)
    mt.step("roteiro"); ... ; mt.step("imagens"); ...
    mt.count("img_fallback_pollinations")     # incrementa contador nomeado
    mt.event("proxy_morto", "webshare 402")   # registra evento pontual
    mt.finalize(status="ok", video_duration_s=65.4, video_path=..., warnings=[...])
"""
import json
import time
from pathlib import Path
from datetime import datetime

try:
    import psutil
    _HAS_PSUTIL = True
except Exception:
    _HAS_PSUTIL = False

PROJECT_DIR = Path(__file__).resolve().parent.parent
METRICS_FILE = PROJECT_DIR / "logs" / "pipeline_metrics.jsonl"


class MetricsTracker:
    def __init__(self, story_id="", genero="", titulo=""):
        self.story_id = story_id
        self.genero = genero
        self.titulo = titulo
        self.t_start = time.time()
        self.steps = {}          # nome_etapa -> segundos
        self.counters = {}       # nome_contador -> int
        self.events = []         # [{t, tipo, detalhe}]
        self.peak_ram_gb = 0.0
        self.peak_cpu = 0.0
        self.min_free_ram_gb = 999.0
        self._cur = None
        self._cur_t0 = None
        self.sample()            # amostra inicial de hardware

    # ---- hardware ----
    def sample(self):
        """Amostra RAM/CPU e atualiza os picos. Chamar em pontos-chave (barato)."""
        if not _HAS_PSUTIL:
            return
        try:
            vm = psutil.virtual_memory()
            used_gb = vm.used / (1024 ** 3)
            free_gb = vm.available / (1024 ** 3)
            cpu = psutil.cpu_percent(interval=None)
            if used_gb > self.peak_ram_gb:
                self.peak_ram_gb = round(used_gb, 2)
            if free_gb < self.min_free_ram_gb:
                self.min_free_ram_gb = round(free_gb, 2)
            if cpu > self.peak_cpu:
                self.peak_cpu = round(cpu, 1)
        except Exception:
            pass

    # ---- etapas ----
    def step(self, nome):
        """Fecha a etapa atual (grava duração) e abre uma nova chamada `nome`."""
        now = time.time()
        if self._cur is not None and self._cur_t0 is not None:
            self.steps[self._cur] = round(now - self._cur_t0, 2)
        self._cur = nome
        self._cur_t0 = now
        self.sample()

    # ---- contadores e eventos ----
    def count(self, nome, inc=1):
        self.counters[nome] = self.counters.get(nome, 0) + inc

    def event(self, tipo, detalhe=""):
        self.events.append({
            "t": round(time.time() - self.t_start, 1),
            "tipo": tipo,
            "detalhe": str(detalhe)[:200],
        })

    # ---- fechamento ----
    def finalize(self, status="ok", video_duration_s=0.0, video_path=None,
                 audio_duration_s=0.0, warnings=None, extra=None):
        # fecha a última etapa aberta
        if self._cur is not None and self._cur_t0 is not None:
            self.steps[self._cur] = round(time.time() - self._cur_t0, 2)
            self._cur = None
        self.sample()

        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "story_id": self.story_id,
            "genero": self.genero,
            "titulo": self.titulo,
            "status": status,
            "total_s": round(time.time() - self.t_start, 2),
            "video_duration_s": round(float(video_duration_s or 0), 2),
            "audio_duration_s": round(float(audio_duration_s or 0), 2),
            "av_desync_s": round(abs(float(video_duration_s or 0) - float(audio_duration_s or 0)), 2),
            "steps_s": self.steps,
            "counters": self.counters,
            "events": self.events,
            "hw": {
                "peak_ram_gb": self.peak_ram_gb,
                "min_free_ram_gb": None if self.min_free_ram_gb > 900 else self.min_free_ram_gb,
                "peak_cpu_pct": self.peak_cpu,
                "psutil": _HAS_PSUTIL,
            },
            "video": str(video_path) if video_path else None,
            "warnings": warnings or [],
        }
        if extra:
            record["extra"] = extra

        try:
            METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(METRICS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"  [metrics] falha ao gravar: {e}", flush=True)
        return record


def _noop_tracker():
    """Tracker nulo (todos os métodos viram no-op) pra usar quando desabilitado."""
    class _Noop:
        def __getattr__(self, _):
            return lambda *a, **k: None
    return _Noop()
