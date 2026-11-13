# -*- coding: utf-8 -*-
"""Banco SQLite local - substitui Postgres/Redis/RabbitMQ."""
import sqlite3
import json
import time
from pathlib import Path
from config import DB_PATH

DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT UNIQUE,
        canal TEXT,
        modo TEXT,
        titulo TEXT,
        prompt_video TEXT,
        prompt_imagem TEXT,
        status TEXT DEFAULT 'pending',
        video_path TEXT,
        video_url TEXT,
        source_url TEXT,
        source_titulo TEXT,
        estatisticas TEXT,
        created_at REAL,
        started_at REAL,
        finished_at REAL,
        error TEXT,
        veo_job_id TEXT
    );

    CREATE TABLE IF NOT EXISTS canais (
        nome TEXT PRIMARY KEY,
        descricao TEXT,
        tema TEXT,
        ultimo_video_at REAL,
        total_videos INTEGER DEFAULT 0,
        visualizacoes INTEGER DEFAULT 0,
        inscritos INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS historico_ideias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canal TEXT,
        ideia TEXT,
        angulo TEXT,
        created_at REAL
    );

    CREATE TABLE IF NOT EXISTS execucoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        input_data TEXT,
        output_data TEXT,
        duracao_s REAL,
        status TEXT,
        error TEXT,
        created_at REAL
    );
    """)
    # Migrate: add veo_job_id if missing
    try:
        conn.execute("ALTER TABLE videos ADD COLUMN veo_job_id TEXT")
    except Exception:
        pass
    conn.close()


def add_video(canal, modo, titulo, prompt_video, prompt_imagem="", source_url="", source_titulo=""):
    conn = get_conn()
    import uuid
    job_id = uuid.uuid4().hex
    conn.execute(
        "INSERT INTO videos (job_id, canal, modo, titulo, prompt_video, prompt_imagem, source_url, source_titulo, created_at, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (job_id, canal, modo, titulo, prompt_video, prompt_imagem, source_url, source_titulo, time.time(), "pending")
    )
    conn.commit()
    conn.close()
    return job_id


def update_video(job_id, **kwargs):
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [job_id]
    conn.execute(f"UPDATE videos SET {sets} WHERE job_id=?", vals)
    conn.commit()
    conn.close()


def get_pending_videos():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM videos WHERE status='pending' ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_videos(limit=20):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM videos ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_historico_ideias(canal=None, limit=10):
    conn = get_conn()
    if canal:
        rows = conn.execute("SELECT * FROM historico_ideias WHERE canal=? ORDER BY created_at DESC LIMIT ?", (canal, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM historico_ideias ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_ideia(canal, ideia, angulo=""):
    conn = get_conn()
    conn.execute("INSERT INTO historico_ideias (canal, ideia, angulo, created_at) VALUES (?,?,?,?)",
                 (canal, ideia, angulo, time.time()))
    conn.commit()
    conn.close()


def log_execucao(tipo, input_data, output_data, duracao_s, status, error=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO execucoes (tipo, input_data, output_data, duracao_s, status, error, created_at) VALUES (?,?,?,?,?,?,?)",
        (tipo, json.dumps(input_data, ensure_ascii=False)[:5000],
         json.dumps(output_data, ensure_ascii=False)[:10000] if output_data else None,
         duracao_s, status, error, time.time())
    )
    conn.commit()
    conn.close()


def get_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM videos WHERE status='done'").fetchone()[0]
    errors = conn.execute("SELECT COUNT(*) FROM videos WHERE status='error'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM videos WHERE status='pending'").fetchone()[0]
    conn.close()
    return {"total": total, "done": done, "errors": errors, "pending": pending}


# Init on import
init_db()
