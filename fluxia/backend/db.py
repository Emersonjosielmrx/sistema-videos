import aiosqlite
import os
from pathlib import Path

DB_PATH = Path(os.environ.get("FLUXIA_DB", str(Path(__file__).parent.parent / "fluxia.db")))

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'admin',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS client_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    flow_id INTEGER NOT NULL REFERENCES flows(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(account_id, flow_id)
);

CREATE TABLE IF NOT EXISTS whatsapp_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    session_id TEXT NOT NULL,
    phone TEXT DEFAULT '',
    label TEXT DEFAULT '',
    hermes_url TEXT NOT NULL,
    api_key TEXT NOT NULL,
    webhook_token TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    connection_id INTEGER REFERENCES whatsapp_connections(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'delivery',
    config TEXT NOT NULL DEFAULT '{}',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL REFERENCES flows(id),
    category TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    price REAL NOT NULL DEFAULT 0,
    available INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL REFERENCES flows(id),
    customer_phone TEXT NOT NULL,
    customer_name TEXT DEFAULT '',
    items TEXT NOT NULL DEFAULT '[]',
    total REAL NOT NULL DEFAULT 0,
    address TEXT DEFAULT '',
    pix_code TEXT DEFAULT '',
    pix_key TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    receipt_path TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL REFERENCES flows(id),
    connection_id INTEGER REFERENCES whatsapp_connections(id),
    direction TEXT NOT NULL DEFAULT 'in',
    phone TEXT NOT NULL,
    message_type TEXT NOT NULL DEFAULT 'text',
    content TEXT NOT NULL DEFAULT '',
    agent_response TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'ok',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL REFERENCES flows(id),
    phone TEXT NOT NULL,
    history TEXT NOT NULL DEFAULT '[]',
    state TEXT NOT NULL DEFAULT 'greeting',
    order_id INTEGER REFERENCES orders(id),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(flow_id, phone)
);

CREATE TABLE IF NOT EXISTS flow_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL REFERENCES flows(id),
    config TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'painel',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL REFERENCES flows(id),
    phone TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'arquivo',
    path TEXT NOT NULL,
    mimetype TEXT NOT NULL DEFAULT '',
    caption TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS admin_state (
    connection_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'admin',
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (connection_id, phone)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    flow_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS polls (
    message_id TEXT PRIMARY KEY,
    flow_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'buttons',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Colunas novas em tabelas que já existiam na VPS (CREATE TABLE IF NOT EXISTS não as adiciona).
MIGRATIONS = [
    ("conversations", "jid", "TEXT NOT NULL DEFAULT ''"),
    ("conversations", "customer_name", "TEXT NOT NULL DEFAULT ''"),
    ("conversations", "paused_until", "TEXT NOT NULL DEFAULT ''"),
    ("conversations", "closed_notice_at", "TEXT NOT NULL DEFAULT ''"),
    ("orders", "kind", "TEXT NOT NULL DEFAULT 'pedido'"),
]


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        for table, column, decl in MIGRATIONS:
            cols = [r["name"] for r in await db.execute_fetchall(f"PRAGMA table_info({table})")]
            if column not in cols:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        await db.commit()
    finally:
        await db.close()


def snapshot(keep: int = 7) -> Path | None:
    """Cópia diária do banco dentro do volume; o backup semanal das VPS leva as 7 últimas para o Drive."""
    import sqlite3
    from datetime import date
    folder = DB_PATH.parent / "backups"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"fluxia-{date.today():%Y-%m-%d}.db"
    if target.exists():
        return None
    src = sqlite3.connect(str(DB_PATH))
    dst = sqlite3.connect(str(target))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    for old in sorted(folder.glob("fluxia-*.db"))[:-keep]:
        old.unlink()
    return target


async def record_event(kind: str, detail: str, flow_id: int | None = None, level: str = "ERRO"):
    """Evento que precisa ser visto na hora: vai para o log do contêiner (monitorado) e para o painel."""
    print(f"[FLUXIA-{level}] {kind}: {detail}", flush=True)
    db = await get_db()
    try:
        await db.execute("INSERT INTO events (kind, detail, flow_id) VALUES (?, ?, ?)", (kind, detail[:2000], flow_id))
        await db.execute("DELETE FROM events WHERE id <= (SELECT MAX(id) - 500 FROM events)")
        await db.commit()
    finally:
        await db.close()


async def get_setting(key: str, default: str = "") -> str:
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT value FROM settings WHERE key = ?", (key,))
        return rows[0]["value"] if rows else default
    finally:
        await db.close()


async def set_setting(key: str, value: str):
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        await db.commit()
    finally:
        await db.close()
