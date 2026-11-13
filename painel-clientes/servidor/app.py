#!/usr/bin/env python3
"""Painel de Clientes — servidor (hermes-prod, Docker, porta 127.0.0.1:8098). Só biblioteca padrão.

Dona 24/10/2026: painel só dos CLIENTES (Açaí O Precioso, MS Energy, a outra empresa de energia solar) e dos
Instagram de PRODUTOS: as pessoas que entraram em contato, as campanhas/impulsionamentos e as métricas para mostrar
ao cliente ("quantas pessoas entraram em contato" etc.). Visual igual ao painel :8790 (web/index.html).

De onde vem cada número (nada é inventado; fonte que não existe aparece como "não conectado"):
  - Instagram (perfil, alcance, toques no link da bio, posts, Direct e comentários): o coletor do PC1
    (D:\\painel-clientes\\coletor\\coletar_instagram.py) lê a API com o token e manda em POST /api/coleta.
  - Pedidos e WhatsApp da loja (acai-lojas) e visitas dos sites (log do nginx): coletor_vps.py, no cron da própria
    VPS, grava fontes/*.json; este servidor importa quando o arquivo muda.
  - Cliques: links rastreados /r/<código> deste servidor (contam e mandam pro WhatsApp/site).
  - Campanhas: cadastradas à mão ou importadas do CSV do Gerenciador de Anúncios (sem API de anúncios por enquanto).

Dados em PASTA_DADOS: painel.db (SQLite), clientes.json (quem aparece), segredos.json (chaves; nunca no código),
fontes/ (o que o coletor da VPS grava). Contrato da API: ../docs/ESPECIFICACAO.md.
"""
import csv
import gzip
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PASTA = Path(os.environ.get("PASTA_DADOS", "/app/dados"))
WEB = Path(__file__).resolve().parent / "web"
PORTA = int(os.environ.get("PORTA", "8098"))
HOST = os.environ.get("HOST", "0.0.0.0")
FUSO = timezone(timedelta(hours=-3))  # Pará (America/Belem): sem horário de verão
DB = PASTA / "painel.db"
CONFIG = PASTA / "clientes.json"
SEGREDOS = PASTA / "segredos.json"
FONTES = PASTA / "fontes"
MAX_CORPO = 3 * 1024 * 1024
CANAIS = {"ig_dm": "Direct do Instagram", "ig_comentario": "Comentário no Instagram", "whatsapp": "WhatsApp da loja",
          "pedido": "Pedido no site"}
STATUS = ["novo", "em atendimento", "virou cliente", "sem interesse"]
ICONE_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#052e1f"/>'
             '<rect x="7" y="17" width="4" height="8" rx="1.5" fill="#34d399"/><rect x="14" y="11" width="4" height="14" '
             'rx="1.5" fill="#34d399"/><rect x="21" y="6" width="4" height="19" rx="1.5" fill="#34d399"/></svg>')
ROBO = re.compile(r"bot|crawl|spider|slurp|facebookexternalhit|facebot|whatsapp/|telegram|preview|curl|python|wget|"
                  r"headless|monitor|uptime|httpclient|okhttp|go-http", re.I)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS eventos (
  id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT NOT NULL, canal TEXT NOT NULL, ext_id TEXT NOT NULL,
  pessoa TEXT NOT NULL, nome TEXT NOT NULL DEFAULT '', em TEXT NOT NULL, texto TEXT NOT NULL DEFAULT '',
  ref TEXT NOT NULL DEFAULT '', origem TEXT NOT NULL DEFAULT '', UNIQUE (cliente, canal, ext_id));
CREATE INDEX IF NOT EXISTS eventos_cli_em ON eventos (cliente, em);
CREATE TABLE IF NOT EXISTS pessoas (
  cliente TEXT NOT NULL, pessoa TEXT NOT NULL, nome TEXT NOT NULL DEFAULT '', contato TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'novo', nota TEXT NOT NULL DEFAULT '', respondido INTEGER, atualizado_em TEXT,
  PRIMARY KEY (cliente, pessoa));
CREATE TABLE IF NOT EXISTS ig_dia (
  cliente TEXT NOT NULL, conta TEXT NOT NULL, dia TEXT NOT NULL, alcance INTEGER, novos_seguidores INTEGER,
  visitas_perfil INTEGER, toques_link INTEGER, contas_engajadas INTEGER, interacoes INTEGER, visualizacoes INTEGER,
  PRIMARY KEY (cliente, conta, dia));
CREATE TABLE IF NOT EXISTS ig_perfil (
  cliente TEXT NOT NULL, conta TEXT NOT NULL, dia TEXT NOT NULL, seguidores INTEGER, posts INTEGER, em TEXT,
  PRIMARY KEY (cliente, conta, dia));
CREATE TABLE IF NOT EXISTS ig_posts (
  cliente TEXT NOT NULL, conta TEXT NOT NULL, id TEXT NOT NULL, em TEXT, tipo TEXT, legenda TEXT, link TEXT,
  visualizacoes INTEGER, alcance INTEGER, curtidas INTEGER, comentarios INTEGER, compartilhamentos INTEGER,
  salvos INTEGER, atualizado_em TEXT, PRIMARY KEY (cliente, id));
CREATE TABLE IF NOT EXISTS visitas (
  cliente TEXT NOT NULL, site TEXT NOT NULL, dia TEXT NOT NULL, paginas INTEGER, visitantes INTEGER,
  PRIMARY KEY (cliente, site, dia));
CREATE TABLE IF NOT EXISTS visitas_codigo (
  cliente TEXT NOT NULL, codigo TEXT NOT NULL, dia TEXT NOT NULL, visitas INTEGER, PRIMARY KEY (cliente, codigo, dia));
CREATE TABLE IF NOT EXISTS pedidos (
  cliente TEXT NOT NULL, id INTEGER NOT NULL, em TEXT, nome TEXT, telefone TEXT, total REAL, status TEXT,
  pagamento TEXT, cupom TEXT, itens TEXT, entrega TEXT, avaliacao INTEGER, origem TEXT, PRIMARY KEY (cliente, id));
CREATE TABLE IF NOT EXISTS links (
  codigo TEXT PRIMARY KEY, cliente TEXT NOT NULL, nome TEXT NOT NULL DEFAULT '', destino TEXT NOT NULL,
  campanha_id INTEGER, criado_em TEXT);
CREATE TABLE IF NOT EXISTS cliques (
  id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT NOT NULL, cliente TEXT NOT NULL, em TEXT NOT NULL,
  visitante TEXT, ua TEXT, ref TEXT);
CREATE INDEX IF NOT EXISTS cliques_cli_em ON cliques (cliente, em);
CREATE TABLE IF NOT EXISTS campanhas (
  id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT NOT NULL, nome TEXT NOT NULL, plataforma TEXT NOT NULL DEFAULT '',
  objetivo TEXT NOT NULL DEFAULT '', inicio TEXT NOT NULL, fim TEXT, orcamento REAL, gasto REAL, alcance INTEGER,
  impressoes INTEGER, cliques INTEGER, resultados INTEGER, resultado_tipo TEXT NOT NULL DEFAULT '',
  link_codigo TEXT NOT NULL DEFAULT '', obs TEXT NOT NULL DEFAULT '', fonte TEXT NOT NULL DEFAULT 'manual',
  criado_em TEXT, atualizado_em TEXT);
CREATE TABLE IF NOT EXISTS fontes (
  cliente TEXT NOT NULL, fonte TEXT NOT NULL, em TEXT NOT NULL, ok INTEGER NOT NULL, detalhe TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (cliente, fonte));
CREATE TABLE IF NOT EXISTS juntadas (
  cliente TEXT NOT NULL, pessoa TEXT NOT NULL, principal TEXT NOT NULL, em TEXT, PRIMARY KEY (cliente, pessoa));
CREATE TABLE IF NOT EXISTS whatsapp (
  cliente TEXT PRIMARY KEY, sid TEXT NOT NULL, criado_em TEXT, ultimo_status_em TEXT, ultimo_erro TEXT NOT NULL DEFAULT '',
  status_enviados INTEGER NOT NULL DEFAULT 0);
"""
# WhatsApp do cliente ligado na API do Hermes Call (dona 30/10): os vídeos postados no Instagram também vão para o
# status dele. Cada cliente = 1 conta (sessão) no Hermes, do usuário dono da chave "hermes_chave" (segredos.json).
HERMES = os.environ.get("HERMES_URL", "https://hermescall.opus-sem-limites.com.br").rstrip("/")
MAX_VIDEO = 60 * 1024 * 1024  # POST /api/whatsapp/status (vídeo em base64; o contêiner tem 256 MB)
CASA = PASTA / "casa.json"  # navegadores (IP + navegador) de quem entrou no painel: não contam como visita nem clique
BACKUPS = PASTA / "backups"


def log(m):
    print(f"[{datetime.now(FUSO):%d/%m %H:%M:%S}] {m}", flush=True)


# ───────────────────────────── configuração e chaves ─────────────────────────────
_CFG = {"t": None, "clientes": [], "seg": {}, "ignorar": set()}
_CFG_LOCK = threading.Lock()


def cfg():
    """{'clientes': [...], 'seg': {...}, 'ignorar': {pessoas da casa}} relido quando clientes.json/segredos.json mudam."""
    try:
        marca = (CONFIG.stat().st_mtime, SEGREDOS.stat().st_mtime)
    except OSError:
        marca = None
    with _CFG_LOCK:
        if marca != _CFG["t"]:
            try:
                conf = json.loads(CONFIG.read_text(encoding="utf-8"))
                seg = json.loads(SEGREDOS.read_text(encoding="utf-8"))
                cl = conf.get("clientes") or []
                # contas/telefones da casa: ficam guardados, mas não contam como pessoa que entrou em contato
                ign = {chave_tel(x) if re.fullmatch(r"\+?[\d\s()-]{8,}", str(x)) else chave_ig(x)
                       for x in conf.get("ignorar") or []}
                _CFG.update(t=marca, clientes=[c for c in cl if c.get("id") and c.get("ativo", True)], seg=seg,
                            ignorar={x for x in ign if x})
            except (OSError, ValueError) as e:
                log(f"config ilegível: {e}")
        return _CFG


def cliente_cfg(cid):
    return next((c for c in cfg()["clientes"] if c["id"] == cid), None)


def _igual(a, b):
    # em bytes: compare_digest com texto não-ASCII (cabeçalho mal formado) dá TypeError
    return hmac.compare_digest(str(a).encode("utf-8"), str(b).encode("utf-8"))


def papel(chave):
    """('admin', None) | ('cliente', id) | (None, None)."""
    if not chave:
        return None, None
    seg = cfg()["seg"]
    if seg.get("admin") and _igual(chave, seg["admin"]):
        return "admin", None
    for cid, k in (seg.get("clientes") or {}).items():
        if k and _igual(chave, k) and cliente_cfg(cid):
            return "cliente", cid
    return None, None


# ───────────────────────────── tentativas erradas e navegadores da casa ─────────────────────────────
_ERROS = {}  # ip -> [horários das tentativas erradas]
_ERROS_LOCK = threading.Lock()
MAX_ERROS, JANELA_ERROS = 20, 600


def bloqueado(ip):
    """Mais de MAX_ERROS chaves/senhas erradas do mesmo IP em 10 min: recusa até a janela passar."""
    agora = time.time()
    with _ERROS_LOCK:
        ts = [t for t in _ERROS.get(ip, []) if agora - t < JANELA_ERROS]
        _ERROS[ip] = ts
        if not ts:
            _ERROS.pop(ip, None)
        return len(ts) >= MAX_ERROS


def anotar_erro(ip):
    with _ERROS_LOCK:
        _ERROS.setdefault(ip, []).append(time.time())
        if len(_ERROS) > 5000:  # não cresce sem fim
            for k in list(_ERROS)[:2500]:
                _ERROS.pop(k, None)


_CASA = {"vis": None, "gravado": 0.0, "mudou": False}
_CASA_LOCK = threading.Lock()


def _casa():
    """{'<ip>\\t<navegador>': 'AAAA-MM-DD'} de quem entrou no painel (dona, equipe, o próprio cliente)."""
    if _CASA["vis"] is None:
        try:
            _CASA["vis"] = json.loads(CASA.read_text(encoding="utf-8")).get("navegadores") or {}
        except (OSError, ValueError):
            _CASA["vis"] = {}
    return _CASA["vis"]


def anotar_casa(ip, ua):
    """Quem tem a chave e abre o site/link do próprio cliente não é cliente novo: o coletor_vps.py e os cliques do
    /r/ deixam esse IP + navegador de fora. Grava no máximo a cada 5 min."""
    if not ip or not ua:
        return
    k, d = f"{ip}\t{ua[:200]}", hoje().isoformat()
    with _CASA_LOCK:
        vis = _casa()
        novo = k not in vis  # navegador novo grava na hora; só a data do dia espera os 5 min
        if vis.get(k) != d:
            vis[k] = d
            _CASA["mudou"] = True
        if _CASA["mudou"] and (novo or time.time() - _CASA["gravado"] > 300):
            corte = (hoje() - timedelta(days=60)).isoformat()
            _CASA["vis"] = vis = {x: y for x, y in vis.items() if y >= corte}
            try:
                tmp = CASA.with_suffix(".tmp")
                tmp.write_text(json.dumps({"_leia": "gerado pelo app.py: IP + navegador de quem entrou no painel",
                                           "navegadores": vis}, ensure_ascii=False), encoding="utf-8")
                tmp.replace(CASA)
                _CASA.update(gravado=time.time(), mudou=False)
            except OSError as e:
                log(f"casa.json: {e}")


def eh_casa(ip, ua):
    with _CASA_LOCK:
        return f"{ip}\t{ua[:200]}" in _casa()


# ───────────────────────────── tempo e chaves de pessoa ─────────────────────────────
def utc_iso(s):
    """Qualquer ISO (Z, +0000, +00:00, sem fuso = UTC) -> 'AAAA-MM-DDTHH:MM:SSZ'. '' se não der."""
    if not s:
        return ""
    t = str(s).strip().replace(" ", "T")
    t = re.sub(r"Z$", "+00:00", t)
    t = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", t)
    try:
        d = datetime.fromisoformat(t)
    except ValueError:
        return ""
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def para_dt(iso):
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def dia_local(iso):
    return para_dt(iso).astimezone(FUSO).date().isoformat()


def hoje():
    return datetime.now(FUSO).date()


def faixa(de, ate):
    """Datas locais [de, ate] (inclusive) -> (ini, fim) em UTC ISO, fim exclusivo."""
    ini = datetime.combine(de, datetime.min.time(), FUSO).astimezone(timezone.utc)
    fim = datetime.combine(ate + timedelta(days=1), datetime.min.time(), FUSO).astimezone(timezone.utc)
    return ini.strftime("%Y-%m-%dT%H:%M:%SZ"), fim.strftime("%Y-%m-%dT%H:%M:%SZ")


def agora_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def chave_tel(t):
    d = re.sub(r"\D", "", str(t or ""))
    if len(d) in (10, 11):
        d = "55" + d
    return "tel:" + d if len(d) >= 8 else ""


def chave_ig(u):
    u = str(u or "").strip().lstrip("@").lower()
    return "ig:" + u if u else ""


def slug(s, n=24):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:n] or "link"


def num(v):
    """'1.234,56' / '1234.56' / 1234 -> float; None se vazio."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-]", "", str(v))
    if not s or s in "-.,":
        return None
    if re.fullmatch(r"-?\d{1,3}([.,]\d{3})+", s):
        s = s.replace(".", "").replace(",", "")  # 1.234 / 1,234 / 12.345.678 = milhar (CSV do Gerenciador)
    elif "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def inteiro(v):
    x = num(v)
    return int(round(x)) if x is not None else None


def data_br(v):
    """'2026-10-20', '20/10/2026' -> date; None se não der."""
    s = str(v or "").strip()[:10]
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None


# ───────────────────────────── banco ─────────────────────────────
def conectar():
    c = sqlite3.connect(DB, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=15000")
    return c


@contextmanager
def banco():
    """Conexão que grava no fim (ou desfaz se der erro) e SEMPRE fecha."""
    c = conectar()
    try:
        with c:
            yield c
    finally:
        c.close()


def criar_banco():
    PASTA.mkdir(parents=True, exist_ok=True)
    FONTES.mkdir(parents=True, exist_ok=True)
    with banco() as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.executescript(ESQUEMA)
        # 30/10: miniatura do post (link do Instagram) para os "posts mais vistos"
        if "capa" not in {r["name"] for r in c.execute("PRAGMA table_info(ig_posts)")}:
            c.execute("ALTER TABLE ig_posts ADD COLUMN capa TEXT")


def marcar_fonte(c, cliente, fonte, ok, detalhe=""):
    c.execute("INSERT INTO fontes (cliente, fonte, em, ok, detalhe) VALUES (?,?,?,?,?) ON CONFLICT(cliente, fonte) "
              "DO UPDATE SET em=excluded.em, ok=excluded.ok, detalhe=excluded.detalhe",
              (cliente, fonte, agora_iso(), 1 if ok else 0, str(detalhe)[:300]))


def gravar_eventos(c, cliente, eventos):
    novos = 0
    for e in eventos or []:
        canal, ext, pessoa = e.get("canal"), str(e.get("ext_id") or ""), str(e.get("pessoa") or "")
        em = utc_iso(e.get("em"))
        if canal not in CANAIS or not ext or not pessoa or not em:
            continue
        nome, contato = str(e.get("nome") or "")[:120], str(e.get("contato") or "")[:120]
        cur = c.execute("INSERT OR IGNORE INTO eventos (cliente, canal, ext_id, pessoa, nome, em, texto, ref, origem) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (cliente, canal, ext, pessoa, nome, em, str(e.get("texto") or "")[:400],
                         str(e.get("ref") or "")[:400], str(e.get("origem") or "")[:60]))
        novos += cur.rowcount
        c.execute("INSERT INTO pessoas (cliente, pessoa, nome, contato) VALUES (?,?,?,?) ON CONFLICT(cliente, pessoa) DO "
                  "UPDATE SET nome = CASE WHEN excluded.nome != '' THEN excluded.nome ELSE pessoas.nome END, "
                  "contato = CASE WHEN excluded.contato != '' THEN excluded.contato ELSE pessoas.contato END",
                  (cliente, pessoa, nome, contato))
    return novos


# ───────────────────────────── importação ─────────────────────────────
def ingerir_coleta(d):
    """POST /api/coleta (coletor do PC1): uma conta de Instagram de um cliente."""
    cliente, conta = d.get("cliente"), str(d.get("conta") or "").lstrip("@").lower()
    if not cliente_cfg(cliente) or not conta:
        return {"erro": "cliente ou conta desconhecido"}
    fonte = f"instagram:{conta}"
    with banco() as c:
        if d.get("erro"):
            marcar_fonte(c, cliente, fonte, False, d["erro"])
            return {"ok": True, "registrado": "erro"}
        p = d.get("perfil") or {}
        if p.get("seguidores") is not None:
            c.execute("INSERT INTO ig_perfil (cliente, conta, dia, seguidores, posts, em) VALUES (?,?,?,?,?,?) "
                      "ON CONFLICT(cliente, conta, dia) DO UPDATE SET seguidores=excluded.seguidores, "
                      "posts=excluded.posts, em=excluded.em",
                      (cliente, conta, hoje().isoformat(), inteiro(p.get("seguidores")), inteiro(p.get("posts")),
                       agora_iso()))
        campos = ("alcance", "novos_seguidores", "visitas_perfil", "toques_link", "contas_engajadas", "interacoes",
                  "visualizacoes")
        for x in d.get("dias") or []:
            if not data_br(x.get("dia")):
                continue
            vals = [inteiro(x.get(k)) for k in campos]
            # só sobrescreve o que veio (o coletor pode mandar um dia com parte das métricas)
            c.execute(f"INSERT INTO ig_dia (cliente, conta, dia, {', '.join(campos)}) VALUES (?,?,?,{','.join('?' * len(campos))}) "
                      f"ON CONFLICT(cliente, conta, dia) DO UPDATE SET "
                      + ", ".join(f"{k}=COALESCE(excluded.{k}, ig_dia.{k})" for k in campos),
                      (cliente, conta, x["dia"][:10], *vals))
        for x in d.get("posts") or []:
            if not x.get("id"):
                continue
            capa = str(x.get("capa") or "")
            c.execute("INSERT INTO ig_posts (cliente, conta, id, em, tipo, legenda, link, visualizacoes, alcance, curtidas, "
                      "comentarios, compartilhamentos, salvos, atualizado_em, capa) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                      "ON CONFLICT(cliente, id) DO UPDATE SET tipo=excluded.tipo, legenda=excluded.legenda, "
                      "link=excluded.link, capa=COALESCE(excluded.capa, ig_posts.capa), "
                      "visualizacoes=COALESCE(excluded.visualizacoes, ig_posts.visualizacoes), "
                      "alcance=COALESCE(excluded.alcance, ig_posts.alcance), curtidas=COALESCE(excluded.curtidas, ig_posts.curtidas), "
                      "comentarios=COALESCE(excluded.comentarios, ig_posts.comentarios), "
                      "compartilhamentos=COALESCE(excluded.compartilhamentos, ig_posts.compartilhamentos), "
                      "salvos=COALESCE(excluded.salvos, ig_posts.salvos), atualizado_em=excluded.atualizado_em",
                      (cliente, conta, str(x["id"]), utc_iso(x.get("em")), str(x.get("tipo") or "")[:20],
                       str(x.get("legenda") or "")[:300], str(x.get("link") or "")[:300], inteiro(x.get("visualizacoes")),
                       inteiro(x.get("alcance")), inteiro(x.get("curtidas")), inteiro(x.get("comentarios")),
                       inteiro(x.get("compartilhamentos")), inteiro(x.get("salvos")), agora_iso(),
                       capa if capa.startswith("https://") else None))
        novos = gravar_eventos(c, cliente, d.get("eventos"))
        for r in d.get("respondidos") or []:  # última mensagem da conversa foi da empresa?
            pes = chave_ig(r.get("conta"))
            if pes:
                c.execute("UPDATE pessoas SET respondido=? WHERE cliente=? AND pessoa=?",
                          (1 if r.get("respondido") else 0, cliente, pes))
        marcar_fonte(c, cliente, fonte, True,
                     f"{len(d.get('dias') or [])} dias, {len(d.get('posts') or [])} posts, {novos} contatos novos")
    return {"ok": True, "contatos_novos": novos}


def ingerir_loja(dados):
    """fontes/loja_<id>.json (coletor_vps.py): pedidos e WhatsApp da loja no acai-lojas."""
    loja = dados.get("loja")
    for cl in [c for c in cfg()["clientes"] if c.get("loja") == loja]:
        cid = cl["id"]
        with banco() as c:
            c.execute("DELETE FROM pedidos WHERE cliente=?", (cid,))
            evs = []
            for p in dados.get("pedidos") or []:
                em = utc_iso(p.get("criado_em"))
                c.execute("INSERT OR REPLACE INTO pedidos (cliente, id, em, nome, telefone, total, status, pagamento, cupom, "
                          "itens, entrega, avaliacao, origem) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (cid, int(p["id"]), em, p.get("nome") or "", p.get("telefone") or "", num(p.get("total")) or 0,
                           p.get("status") or "", p.get("forma_pagamento") or "", p.get("cupom") or "",
                           str(p.get("itens") or "")[:400], p.get("tipo_entrega") or "", p.get("avaliacao"),
                           p.get("origem") or ""))
                pes = chave_tel(p.get("telefone"))
                if pes and em:
                    evs.append({"canal": "pedido", "ext_id": f"p{p['id']}", "pessoa": pes, "nome": p.get("nome") or "",
                                "contato": p.get("telefone") or "", "em": em, "ref": cl.get("site") or "",
                                "texto": f"Pedido #{p['id']} · R$ {num(p.get('total')) or 0:.2f} · {p.get('status') or ''}"})
            for m in dados.get("mensagens") or []:
                pes = chave_tel(m.get("telefone"))
                if pes:
                    evs.append({"canal": "whatsapp", "ext_id": f"w{m.get('id')}", "pessoa": pes, "nome": m.get("nome") or "",
                                "contato": m.get("telefone") or "", "em": m.get("em"), "texto": m.get("texto") or ""})
            novos = gravar_eventos(c, cid, evs)
            marcar_fonte(c, cid, "loja", True, f"{len(dados.get('pedidos') or [])} pedidos, "
                         f"{len(dados.get('mensagens') or [])} mensagens de WhatsApp, {novos} contatos novos")
            if dados.get("whatsapp_conectado") is not None:
                marcar_fonte(c, cid, "whatsapp_loja", bool(dados["whatsapp_conectado"]),
                             "conectado" if dados["whatsapp_conectado"] else "WhatsApp da loja não conectado no sistema")


def ingerir_visitas(dados):
    """fontes/visitas.json: {'dias': {dia: {host: {paginas, visitantes, codigos: {cod: n}}}}}."""
    mapa = {}
    for cl in cfg()["clientes"]:
        for h in cl.get("sites") or []:
            mapa[h.lower()] = cl["id"]
    with banco() as c:
        tocados = set()
        for dia, hosts in (dados.get("dias") or {}).items():
            if not data_br(dia):
                continue
            for host, v in (hosts or {}).items():
                cid = mapa.get(host.lower())
                if not cid:
                    continue
                tocados.add(cid)
                c.execute("INSERT INTO visitas (cliente, site, dia, paginas, visitantes) VALUES (?,?,?,?,?) "
                          "ON CONFLICT(cliente, site, dia) DO UPDATE SET paginas=excluded.paginas, visitantes=excluded.visitantes",
                          (cid, host.lower(), dia, int(v.get("paginas") or 0), int(v.get("visitantes") or 0)))
                for cod, n in (v.get("codigos") or {}).items():
                    c.execute("INSERT INTO visitas_codigo (cliente, codigo, dia, visitas) VALUES (?,?,?,?) "
                              "ON CONFLICT(cliente, codigo, dia) DO UPDATE SET visitas=excluded.visitas",
                              (cid, slug(cod, 40), dia, int(n or 0)))
        for cl in cfg()["clientes"]:
            if cl.get("sites"):
                marcar_fonte(c, cl["id"], "site", True, "log do nginx (páginas abertas, sem robôs)")


_VISTOS = {}


def fazer_backup():
    """Cópia do banco 1x por dia em dados/backups (campanhas, situações, anotações e cliques só existem aqui); 14 dias."""
    BACKUPS.mkdir(parents=True, exist_ok=True)
    alvo = BACKUPS / f"painel_{hoje():%Y%m%d}.db"
    if alvo.exists():
        return
    tmp = alvo.with_suffix(".tmp")
    origem, destino = conectar(), sqlite3.connect(tmp)
    try:
        origem.backup(destino)
    finally:
        destino.close()
        origem.close()
    tmp.replace(alvo)
    for velho in sorted(BACKUPS.glob("painel_*.db"))[:-14]:
        velho.unlink(missing_ok=True)
    log(f"backup do banco: {alvo.name}")


def vigiar_fontes():
    """Importa fontes/*.json quando mudam (coletor_vps.py grava a cada 5 min) e faz o backup do dia."""
    while True:
        for f in sorted(FONTES.glob("*.json")):
            try:
                m = f.stat().st_mtime
                if _VISTOS.get(f.name) == m:
                    continue
                _VISTOS[f.name] = m  # arquivo com erro não é relido a cada minuto (só quando mudar de novo)
                dados = json.loads(f.read_text(encoding="utf-8"))
                if f.name.startswith("loja_"):
                    ingerir_loja(dados)
                elif f.name == "visitas.json":
                    ingerir_visitas(dados)
            except Exception as e:  # noqa: BLE001 — um arquivo ruim não trava os outros, e o laço nunca morre
                log(f"importar {f.name}: {type(e).__name__}: {e}")
        try:
            fazer_backup()
        except Exception as e:  # noqa: BLE001
            log(f"backup: {type(e).__name__}: {e}")
        time.sleep(60)


# ───────────────────────────── cálculo do painel ─────────────────────────────
def _soma(rows, k):
    vs = [r[k] for r in rows if r[k] is not None]
    return sum(vs) if vs else None


def _dias(de, ate):
    return [(de + timedelta(days=i)).isoformat() for i in range((ate - de).days + 1)]


def _campanha_metricas(c, cl, camp, eventos, primeiros):
    ini_d = data_br(camp["inicio"]) or hoje()
    fim_cfg = data_br(camp["fim"]) or hoje()
    fim_d = max(ini_d, min(fim_cfg, hoje()))  # campanha que ainda vai começar: 1 dia, sem contatos
    dur = (fim_d - ini_d).days + 1
    i, f = faixa(ini_d, fim_d)
    ia, fa = faixa(ini_d - timedelta(days=dur), ini_d - timedelta(days=1))
    durante = {e["pessoa"] for e in eventos if i <= e["em"] < f}
    antes = {e["pessoa"] for e in eventos if ia <= e["em"] < fa}
    novas = {p for p in durante if primeiros.get(p, "") >= i}
    cod = camp["link_codigo"] or ""
    cliques = visitantes = vis_cod = 0
    if cod:
        r = c.execute("SELECT COUNT(*) n, COUNT(DISTINCT visitante) u FROM cliques WHERE codigo=? AND em>=? AND em<?",
                      (cod, i, f)).fetchone()
        cliques, visitantes = r["n"], r["u"]
        vis_cod = c.execute("SELECT COALESCE(SUM(visitas),0) n FROM visitas_codigo WHERE cliente=? AND codigo=? AND dia>=? "
                            "AND dia<=?", (cl["id"], cod, ini_d.isoformat(), fim_d.isoformat())).fetchone()["n"]
    gasto = camp["gasto"]
    d = dict(camp)
    d.update(dias=dur, ativa=fim_cfg >= hoje() >= ini_d,
             contatos_durante=len(durante), contatos_novos=len(novas), contatos_antes=len(antes),
             variacao=len(durante) - len(antes), cliques_link=cliques, pessoas_link=visitantes, visitas_link=vis_cod,
             custo_por_contato=round(gasto / len(durante), 2) if gasto and durante else None,
             custo_por_resultado=round(gasto / camp["resultados"], 2) if gasto and camp["resultados"] else None)
    return d


def montar_painel(cid, de, ate, completo=True):
    cl = cliente_cfg(cid)
    n = (ate - de).days + 1
    de_a, ate_a = de - timedelta(days=n), de - timedelta(days=1)
    ini, fim = faixa(de, ate)
    ini_a, fim_a = faixa(de_a, ate_a)
    with banco() as c:
        ign = cfg()["ignorar"]
        # "juntar pessoas": a mesma pessoa no Instagram e no telefone conta 1 vez (vale o registro principal)
        junta = {r["pessoa"]: r["principal"] for r in c.execute("SELECT pessoa, principal FROM juntadas WHERE cliente=?",
                                                                 (cid,))}
        todos = []
        for r in c.execute("SELECT * FROM eventos WHERE cliente=? ORDER BY em", (cid,)):
            if r["pessoa"] in ign:
                continue
            e = dict(r)
            e["pessoa"] = junta.get(e["pessoa"], e["pessoa"])
            todos.append(e)
        primeiros = {}
        for e in todos:
            primeiros.setdefault(e["pessoa"], e["em"])
        atual = [e for e in todos if ini <= e["em"] < fim]
        anterior = [e for e in todos if ini_a <= e["em"] < fim_a]
        pes_atual = {e["pessoa"] for e in atual}
        pes_ant = {e["pessoa"] for e in anterior}
        novos = {p for p in pes_atual if primeiros.get(p, "") >= ini}
        por_canal = {k: len({e["pessoa"] for e in atual if e["canal"] == k}) for k in CANAIS}

        fontes = {r["fonte"]: dict(r) for r in c.execute("SELECT * FROM fontes WHERE cliente=?", (cid,))}
        ig_ok = any(k.startswith("instagram:") and v["ok"] for k, v in fontes.items())
        ig_dia = [dict(r) for r in c.execute("SELECT * FROM ig_dia WHERE cliente=? AND dia>=? AND dia<=?",
                                             (cid, de_a.isoformat(), ate.isoformat()))]
        ig_at = [r for r in ig_dia if r["dia"] >= de.isoformat()]
        ig_an = [r for r in ig_dia if r["dia"] < de.isoformat()]
        # seguidores: o último número de CADA conta até o fim do período (conta que falhou num dia não some da soma)
        segs = lambda lim, op: c.execute(  # noqa: E731
            f"SELECT SUM(seguidores) s FROM ig_perfil p WHERE cliente=? AND dia=(SELECT MAX(dia) FROM ig_perfil q "
            f"WHERE q.cliente=p.cliente AND q.conta=p.conta AND q.dia {op} ? AND q.seguidores IS NOT NULL)",
            (cid, lim)).fetchone()
        perfil, perfil_antes = segs(ate.isoformat(), "<="), segs(de.isoformat(), "<")
        tem_ig_dia = c.execute("SELECT 1 FROM ig_dia WHERE cliente=? LIMIT 1", (cid,)).fetchone() is not None
        # posts publicados no período: curtidas sempre; visualizações quando a conta não dá o número por dia
        pp = lambda a, b: c.execute(  # noqa: E731
            "SELECT COUNT(*) n, SUM(visualizacoes) v, SUM(curtidas) c FROM ig_posts WHERE cliente=? AND em>=? AND em<?",
            (cid, a, b)).fetchone()
        pp_at, pp_an = pp(ini, fim), pp(ini_a, fim_a)
        tem_posts = c.execute("SELECT 1 FROM ig_posts WHERE cliente=? LIMIT 1", (cid,)).fetchone() is not None
        vis = [dict(r) for r in c.execute("SELECT dia, SUM(paginas) paginas, SUM(visitantes) visitantes FROM visitas "
                                          "WHERE cliente=? AND dia>=? AND dia<=? GROUP BY dia",
                                          (cid, de_a.isoformat(), ate.isoformat()))]
        vis_at = [r for r in vis if r["dia"] >= de.isoformat()]
        vis_an = [r for r in vis if r["dia"] < de.isoformat()]
        cq = lambda a, b: c.execute("SELECT COUNT(*) n, COUNT(DISTINCT visitante) u FROM cliques WHERE cliente=? AND em>=? "  # noqa: E731
                                    "AND em<?", (cid, a, b)).fetchone()
        cq_at, cq_an = cq(ini, fim), cq(ini_a, fim_a)
        n_links = c.execute("SELECT COUNT(*) n FROM links WHERE cliente=?", (cid,)).fetchone()["n"]
        validos = "status NOT IN ('cancelado','aguardando')"
        ped = lambda a, b: c.execute(f"SELECT COUNT(*) n, COALESCE(SUM(total),0) t FROM pedidos WHERE cliente=? AND em>=? "  # noqa: E731
                                     f"AND em<? AND {validos}", (cid, a, b)).fetchone()
        ped_at, ped_an = ped(ini, fim), ped(ini_a, fim_a)
        camps = [dict(r) for r in c.execute("SELECT * FROM campanhas WHERE cliente=? ORDER BY inicio DESC, id DESC", (cid,))]
        camps = [_campanha_metricas(c, cl, x, todos, primeiros) for x in camps]

        # gasto das campanhas no período: proporcional aos dias que caem dentro dele
        def gasto_em(a, b):
            tot, tem = 0.0, False
            for x in camps:
                if not x["gasto"]:
                    continue
                i0 = data_br(x["inicio"])
                f0 = data_br(x["fim"]) or hoje()
                if not i0 or f0 < i0:
                    continue
                sob = (min(f0, b) - max(i0, a)).days + 1
                if sob > 0:
                    tot += x["gasto"] * sob / ((f0 - i0).days + 1)
                    tem = True
            return round(tot, 2) if tem else None
        gasto_at, gasto_an = gasto_em(de, ate), gasto_em(de_a, ate_a)

        loja = bool(cl.get("loja"))
        sites = bool(cl.get("sites"))
        tem_ig = bool(cl.get("instagram"))
        ig_motivo = ("" if ig_ok else
                     "; ".join(v["detalhe"] for k, v in fontes.items() if k.startswith("instagram:") and not v["ok"])
                     or ("Instagram ainda não conectado" if tem_ig else "sem Instagram cadastrado"))
        # números por dia (alcance, toques na bio...) só vêm da API de conta comercial; a leitura pela sessão (conta
        # pessoal) traz seguidores, posts e contatos — sem isso o cartão mostraria 0 como se fosse número de verdade
        ig_dia_ok = ig_ok and tem_ig_dia
        ig_dia_motivo = ig_motivo or "esta conta não dá números por dia (só conta comercial ligada à API)"

        def card(id_, titulo, valor, anterior, fonte, conectado=True, sub="", fmt="num", motivo=""):
            return {"id": id_, "titulo": titulo, "valor": valor, "anterior": anterior, "fonte": fonte,
                    "conectado": conectado, "sub": sub, "fmt": fmt, "motivo": motivo}

        ig_fonte = (("Instagram (lido pela sessão da conta, " if cl.get("instagram_http") else "Instagram (API oficial, conta ")
                    + ", ".join("@" + x for x in cl.get("instagram") or []) + ")")
        seg = perfil["s"] if perfil else None
        seg_ant = perfil_antes["s"] if perfil_antes else None
        cards = [
            card("pessoas", "Pessoas que entraram em contato", len(pes_atual), len(pes_ant),
                 "Direct e comentários do Instagram, WhatsApp da loja e pedidos do site — cada pessoa conta 1 vez",
                 True, f"{len(novos)} pela primeira vez"),
            card("toques_bio", "Toques no link da bio", _soma(ig_at, "toques_link"), _soma(ig_an, "toques_link"),
                 ig_fonte + " — botão/link do perfil (ex.: WhatsApp)", ig_dia_ok, motivo=ig_dia_motivo),
            card("cliques", "Cliques nos links rastreados", cq_at["n"], cq_an["n"],
                 "Links /r/ deste painel (cada campanha tem o seu)", n_links > 0,
                 "1 pessoa" if cq_at["u"] == 1 else f"{cq_at['u']} pessoas diferentes",
                 motivo="nenhum link rastreado criado ainda"),
            card("visitas", "Visitas ao site", _soma(vis_at, "visitantes"), _soma(vis_an, "visitantes"),
                 "Log do servidor do site (pessoas por dia, sem robôs)", sites,
                 (lambda n: f"{n} página aberta" if n == 1 else f"{n} páginas abertas")(_soma(vis_at, "paginas") or 0),
                 motivo="sem site cadastrado"),
            card("pedidos", "Pedidos pelo site", ped_at["n"], ped_an["n"], "Sistema de pedidos da loja (sem cancelados)",
                 loja, motivo="sem loja online"),
            card("faturamento", "Vendido pelo site", round(ped_at["t"], 2), round(ped_an["t"], 2),
                 "Soma dos pedidos do site (sem cancelados)", loja,
                 f"ticket médio R$ {ped_at['t'] / ped_at['n']:.2f}".replace(".", ",") if ped_at["n"] else "",
                 fmt="brl", motivo="sem loja online"),
            card("alcance", "Alcance no Instagram", _soma(ig_at, "alcance"), _soma(ig_an, "alcance"),
                 ig_fonte + " — soma do alcance de cada dia", ig_dia_ok, motivo=ig_dia_motivo),
            # dona 30/10: visualizações são o foco do painel. Conta com número por dia: tudo que foi visto no período;
            # conta sem (leitura pela sessão): as visualizações dos posts publicados no período
            (card("visualizacoes", "Visualizações no Instagram", _soma(ig_at, "visualizacoes"),
                  _soma(ig_an, "visualizacoes"), ig_fonte + " — tudo que foi visto no período (posts, Reels e Stories)",
                  ig_dia_ok, motivo=ig_dia_motivo) if ig_dia_ok else
             card("visualizacoes", "Visualizações no Instagram", pp_at["v"], pp_an["v"],
                  ig_fonte + " — soma das visualizações dos posts publicados no período", ig_ok and tem_posts,
                  f"{pp_at['n']} post publicado" if pp_at["n"] == 1 else f"{pp_at['n']} posts publicados",
                  motivo=ig_motivo or "nenhum post lido ainda")),
            card("curtidas", "Curtidas", pp_at["c"], pp_an["c"],
                 ig_fonte + " — soma das curtidas dos posts publicados no período", ig_ok and tem_posts,
                 f"{pp_at['n']} post publicado" if pp_at["n"] == 1 else f"{pp_at['n']} posts publicados",
                 motivo=ig_motivo or "nenhum post lido ainda"),
            card("visitas_perfil", "Visitas ao perfil", _soma(ig_at, "visitas_perfil"), _soma(ig_an, "visitas_perfil"),
                 ig_fonte, ig_dia_ok, motivo=ig_dia_motivo),
            card("seguidores", "Seguidores", seg, seg_ant, ig_fonte, ig_ok and seg is not None,
                 (f"{seg - seg_ant:+d} no período" if seg is not None and seg_ant is not None else
                  (f"+{_soma(ig_at, 'novos_seguidores')} novos no período" if _soma(ig_at, "novos_seguidores") else "")),
                 motivo=ig_motivo),
            card("gasto", "Investido em campanhas", gasto_at, gasto_an,
                 "Campanhas cadastradas (valor proporcional aos dias do período)", bool(camps), fmt="brl",
                 motivo="nenhuma campanha cadastrada"),
            card("custo_contato", "Custo por pessoa que entrou em contato",
                 round(gasto_at / len(pes_atual), 2) if gasto_at and pes_atual else None,
                 round(gasto_an / len(pes_ant), 2) if gasto_an and pes_ant else None,
                 "Investido no período ÷ pessoas que entraram em contato no período", bool(camps), fmt="brl",
                 motivo="nenhuma campanha cadastrada"),
        ]
        out = {"cliente": {k: cl.get(k) for k in ("id", "nome", "tipo", "cor", "cidade", "instagram", "site", "whatsapp",
                                                  "loja", "sites")},
               "periodo": {"de": de.isoformat(), "ate": ate.isoformat(), "dias": n, "anterior_de": de_a.isoformat(),
                           "anterior_ate": ate_a.isoformat()},
               "cards": cards, "por_canal": {CANAIS[k]: v for k, v in por_canal.items()},
               "atualizado_em": max([v["em"] for v in fontes.values()] or [""]),
               "fontes": [{"fonte": k, "ok": bool(v["ok"]), "em": v["em"], "detalhe": v["detalhe"]} for k, v in
                          sorted(fontes.items())]}
        if not completo:
            return out
        dias = _dias(de, ate)
        serie = {d: {CANAIS[k]: set() for k in CANAIS} for d in dias}
        for e in atual:
            d = dia_local(e["em"])
            if d in serie:
                serie[d][CANAIS[e["canal"]]].add(e["pessoa"])
        out["serie_contatos"] = {"dias": dias, "series": {CANAIS[k]: {d: len(serie[d][CANAIS[k]]) for d in dias if
                                                                      serie[d][CANAIS[k]]} for k in CANAIS}}
        igm = {r["dia"]: r for r in ig_at}
        vism = {r["dia"]: r for r in vis_at}
        cqd = {}
        for r in c.execute("SELECT em FROM cliques WHERE cliente=? AND em>=? AND em<?", (cid, ini, fim)):
            d = dia_local(r["em"])
            cqd[d] = cqd.get(d, 0) + 1
        out["serie_dia"] = [{"dia": d, "alcance": (igm.get(d) or {}).get("alcance"),
                             "visualizacoes": (igm.get(d) or {}).get("visualizacoes"),
                             "toques_link": (igm.get(d) or {}).get("toques_link"),
                             "visitas_perfil": (igm.get(d) or {}).get("visitas_perfil"),
                             "visitas_site": (vism.get(d) or {}).get("visitantes"), "cliques": cqd.get(d, 0)}
                            for d in dias]
        # pessoas do período (cada uma com tudo o que fez no período)
        info = {r["pessoa"]: dict(r) for r in c.execute("SELECT * FROM pessoas WHERE cliente=?", (cid,))}
        grupo = {}
        for e in atual:
            g = grupo.setdefault(e["pessoa"], {"canais": set(), "n": 0, "ultimo": None, "origem": ""})
            g["canais"].add(CANAIS[e["canal"]])
            g["n"] += 1
            if not g["ultimo"] or e["em"] >= g["ultimo"]["em"]:
                g["ultimo"] = e
            g["origem"] = g["origem"] or e["origem"]
        apelidos = {}
        for alias, princ in junta.items():
            apelidos.setdefault(princ, []).append(alias)
        contato_de = lambda p: (info.get(p, {}).get("contato")  # noqa: E731
                                or ("@" + p[3:] if p.startswith("ig:") else p[4:]))
        pessoas = []
        for p, g in grupo.items():
            i = info.get(p, {})
            u = g["ultimo"]
            outras = sorted(apelidos.get(p, []))
            # pessoa juntada: a situação/anotação é a do registro principal; "respondido" vem de quem tiver (Direct)
            resp = next((info.get(x, {}).get("respondido") for x in [p, *outras]
                         if info.get(x, {}).get("respondido") is not None), None)
            pessoas.append({"pessoa": p, "nome": i.get("nome") or u["nome"] or p.split(":", 1)[-1],
                            "contato": " · ".join(dict.fromkeys(contato_de(x) for x in [p, *outras] if contato_de(x))),
                            "canais": sorted(g["canais"]), "primeiro_em": primeiros.get(p), "ultimo_em": u["em"],
                            "mensagens": g["n"], "texto": u["texto"], "ref": u["ref"], "origem": g["origem"],
                            "novo": primeiros.get(p, "") >= ini, "status": i.get("status") or "novo",
                            "nota": i.get("nota") or "", "respondido": resp, "juntadas": outras})
        out["pessoas"] = sorted(pessoas, key=lambda x: x["ultimo_em"], reverse=True)
        out["campanhas"] = camps
        base = os.environ.get("URL_PUBLICA", "https://clientes.opus-sem-limites.com.br").rstrip("/")
        links = []
        for r in c.execute("SELECT * FROM links WHERE cliente=? ORDER BY criado_em DESC", (cid,)):
            t = c.execute("SELECT COUNT(*) n FROM cliques WHERE codigo=?", (r["codigo"],)).fetchone()["n"]
            p = c.execute("SELECT COUNT(*) n, COUNT(DISTINCT visitante) u FROM cliques WHERE codigo=? AND em>=? AND em<?",
                          (r["codigo"], ini, fim)).fetchone()
            links.append({**dict(r), "url": f"{base}/r/{r['codigo']}", "cliques_total": t, "cliques_periodo": p["n"],
                          "pessoas_periodo": p["u"],
                          "campanha": next((x["nome"] for x in camps if x["id"] == r["campanha_id"]), "")})
        out["links"] = links
        out["pedidos"] = [dict(r) for r in c.execute("SELECT * FROM pedidos WHERE cliente=? AND em>=? AND em<? ORDER BY "
                                                     "em DESC", (cid, ini, fim))] if loja else []
        out["posts"] = [dict(r) for r in c.execute("SELECT * FROM ig_posts WHERE cliente=? ORDER BY em DESC LIMIT 300",
                                                   (cid,))]
        out["status_opcoes"] = STATUS
    return out


# ───────────────────────────── ações (POST) ─────────────────────────────
def salvar_pessoa(d, papel_, cid_papel):
    cid = d.get("cliente")
    if papel_ != "admin" and cid != cid_papel:
        return 403, {"erro": "sem permissão"}
    st = d.get("status")
    if st is not None and st not in STATUS:
        return 400, {"erro": "status inválido"}
    with banco() as c:
        r = c.execute("SELECT 1 FROM pessoas WHERE cliente=? AND pessoa=?", (cid, d.get("pessoa"))).fetchone()
        if not r:
            return 404, {"erro": "pessoa não encontrada"}
        if st is not None:
            c.execute("UPDATE pessoas SET status=?, atualizado_em=? WHERE cliente=? AND pessoa=?",
                      (st, agora_iso(), cid, d["pessoa"]))
        if d.get("nota") is not None:
            c.execute("UPDATE pessoas SET nota=?, atualizado_em=? WHERE cliente=? AND pessoa=?",
                      (str(d["nota"])[:500], agora_iso(), cid, d["pessoa"]))
    return 200, {"ok": True}


def juntar_pessoa(d, papel_, cid_papel):
    """{cliente, pessoa, com}: 'pessoa' passa a contar como 'com' (ex.: o @ do Instagram e o telefone do pedido são a
    mesma pessoa). Nada é apagado: {cliente, pessoa, separar: true} desfaz."""
    cid, pes, com = d.get("cliente"), str(d.get("pessoa") or ""), str(d.get("com") or "")
    if papel_ != "admin" and cid != cid_papel:
        return 403, {"erro": "sem permissão"}
    with banco() as c:
        if d.get("separar"):
            c.execute("DELETE FROM juntadas WHERE cliente=? AND pessoa=?", (cid, pes))
            return 200, {"ok": True}
        existe = lambda p: c.execute("SELECT * FROM pessoas WHERE cliente=? AND pessoa=?", (cid, p)).fetchone()  # noqa: E731
        r = c.execute("SELECT principal FROM juntadas WHERE cliente=? AND pessoa=?", (cid, com)).fetchone()
        com = r["principal"] if r else com  # juntar com quem já foi juntado = juntar com o principal dele
        a, b = existe(pes), existe(com)
        if not a or not b:
            return 404, {"erro": "pessoa não encontrada"}
        if pes == com:
            return 400, {"erro": "é a mesma pessoa"}
        agora = agora_iso()
        # quem estava juntado na 'pessoa' passa para o principal novo (sem corrente de juntadas)
        c.execute("UPDATE juntadas SET principal=?, em=? WHERE cliente=? AND principal=?", (com, agora, cid, pes))
        c.execute("INSERT INTO juntadas (cliente, pessoa, principal, em) VALUES (?,?,?,?) ON CONFLICT(cliente, pessoa) "
                  "DO UPDATE SET principal=excluded.principal, em=excluded.em", (cid, pes, com, agora))
        # a situação e a anotação que já existiam não se perdem
        if (b["status"] or "novo") == "novo" and (a["status"] or "novo") != "novo":
            c.execute("UPDATE pessoas SET status=?, atualizado_em=? WHERE cliente=? AND pessoa=?", (a["status"], agora, cid, com))
        if a["nota"] and a["nota"] not in (b["nota"] or ""):
            nota = ((b["nota"] + " | ") if b["nota"] else "") + a["nota"]
            c.execute("UPDATE pessoas SET nota=?, atualizado_em=? WHERE cliente=? AND pessoa=?", (nota[:500], agora, cid, com))
    return 200, {"ok": True, "principal": com}


def _codigo_livre(c, base):
    """Código nunca é reaproveitado (nem de link apagado): os cliques antigos não passam para o link novo."""
    cod, i = base, 2
    while (c.execute("SELECT 1 FROM links WHERE codigo=?", (cod,)).fetchone()
           or c.execute("SELECT 1 FROM cliques WHERE codigo=? LIMIT 1", (cod,)).fetchone()):
        cod = f"{base}-{i}"
        i += 1
    return cod


def _destino_padrao(cl):
    return cl.get("whatsapp") or cl.get("site") or ""


def destino_ok(u):
    return bool(re.match(r"^https://[^\s/]+\.[^\s]+$", str(u or "")))


def salvar_link(d):
    cl = cliente_cfg(d.get("cliente"))
    if not cl:
        return 400, {"erro": "cliente desconhecido"}
    destino = (d.get("destino") or _destino_padrao(cl)).strip()
    if not destino_ok(destino):
        return 400, {"erro": "destino precisa ser um link https:// (WhatsApp, site, Instagram...)"}
    with banco() as c:
        cod = _codigo_livre(c, slug(d.get("codigo") or f"{cl['id'][:10]}-{d.get('nome') or 'link'}", 40))
        c.execute("INSERT INTO links (codigo, cliente, nome, destino, campanha_id, criado_em) VALUES (?,?,?,?,?,?)",
                  (cod, cl["id"], str(d.get("nome") or cod)[:80], destino, d.get("campanha_id"), agora_iso()))
    return 200, {"ok": True, "codigo": cod}


def apagar_link(d):
    with banco() as c:
        c.execute("DELETE FROM links WHERE codigo=?", (d.get("codigo"),))
        c.execute("UPDATE campanhas SET link_codigo='' WHERE link_codigo=?", (d.get("codigo"),))
    return 200, {"ok": True}


CAMPOS_CAMP = ("nome", "plataforma", "objetivo", "inicio", "fim", "orcamento", "gasto", "alcance", "impressoes", "cliques",
               "resultados", "resultado_tipo", "obs")


def _limpar_camp(d):
    x = {}
    for k in CAMPOS_CAMP:
        v = d.get(k)
        if k in ("orcamento", "gasto"):
            x[k] = num(v)
        elif k in ("alcance", "impressoes", "cliques", "resultados"):
            x[k] = inteiro(v)
        elif k in ("inicio", "fim"):
            dt = data_br(v)
            x[k] = dt.isoformat() if dt else None
        else:
            x[k] = str(v or "").strip()[:300]
    return x


def salvar_campanha(d):
    cl = cliente_cfg(d.get("cliente"))
    if not cl:
        return 400, {"erro": "cliente desconhecido"}
    x = _limpar_camp(d)
    if not x["nome"] or not x["inicio"]:
        return 400, {"erro": "nome e data de início são obrigatórios"}
    if x["fim"] and x["fim"] < x["inicio"]:
        return 400, {"erro": "a data de fim é antes do início"}
    if d.get("id") and not str(d["id"]).isdigit():
        return 400, {"erro": "campanha inválida"}
    with banco() as c:
        if d.get("id"):
            r = c.execute("SELECT * FROM campanhas WHERE id=? AND cliente=?", (int(d["id"]), cl["id"])).fetchone()
            if not r:
                return 404, {"erro": "campanha não encontrada"}
            c.execute(f"UPDATE campanhas SET {', '.join(k + '=?' for k in CAMPOS_CAMP)}, atualizado_em=? WHERE id=?",
                      (*[x[k] for k in CAMPOS_CAMP], agora_iso(), int(d["id"])))
            cid_camp, cod = int(d["id"]), r["link_codigo"]
        else:
            cur = c.execute(f"INSERT INTO campanhas (cliente, {', '.join(CAMPOS_CAMP)}, fonte, criado_em, atualizado_em) "
                            f"VALUES (?, {','.join('?' * len(CAMPOS_CAMP))}, ?, ?, ?)",
                            (cl["id"], *[x[k] for k in CAMPOS_CAMP], d.get("fonte") or "manual", agora_iso(), agora_iso()))
            cid_camp, cod = cur.lastrowid, ""
        # cada campanha ganha o seu link rastreado (o destino padrão do cliente, ou o que veio)
        if not cod and (d.get("destino") or _destino_padrao(cl)) and d.get("criar_link", True):
            destino = (d.get("destino") or _destino_padrao(cl)).strip()
            if destino_ok(destino):
                cod = _codigo_livre(c, slug(f"{cl['id'][:10]}-{x['nome']}", 40))
                c.execute("INSERT INTO links (codigo, cliente, nome, destino, campanha_id, criado_em) VALUES (?,?,?,?,?,?)",
                          (cod, cl["id"], x["nome"][:80], destino, cid_camp, agora_iso()))
                c.execute("UPDATE campanhas SET link_codigo=? WHERE id=?", (cod, cid_camp))
    return 200, {"ok": True, "id": cid_camp, "link_codigo": cod}


def apagar_campanha(d):
    if not str(d.get("id") or "").isdigit():
        return 400, {"erro": "campanha inválida"}
    with banco() as c:
        r = c.execute("SELECT link_codigo FROM campanhas WHERE id=?", (int(d.get("id") or 0),)).fetchone()
        if not r:
            return 404, {"erro": "campanha não encontrada"}
        c.execute("DELETE FROM campanhas WHERE id=?", (int(d["id"]),))
        c.execute("UPDATE links SET campanha_id=NULL WHERE campanha_id=?", (int(d["id"]),))
    return 200, {"ok": True}


# Gerenciador de Anúncios (exportar → CSV): cabeçalhos em português ou inglês
COLS_CSV = {
    "nome": ["nome da campanha", "campaign name", "nome do anúncio", "ad name", "nome do conjunto de anúncios",
             "ad set name", "campanha"],
    "inicio": ["início dos relatórios", "reporting starts", "início", "data de início", "starts"],
    "fim": ["término dos relatórios", "reporting ends", "término", "data de término", "ends"],
    "gasto": ["valor usado (brl)", "amount spent (brl)", "valor usado", "amount spent", "gasto"],
    "alcance": ["alcance", "reach"],
    "impressoes": ["impressões", "impressions"],
    "cliques": ["cliques no link", "link clicks", "cliques (todos)", "clicks (all)", "cliques"],
    "resultados": ["resultados", "results"],
    "resultado_tipo": ["indicador de resultado", "result indicator", "tipo de resultado", "result type"],
    "orcamento": ["orçamento", "budget", "orçamento do conjunto de anúncios"],
}


def importar_csv(d):
    cl = cliente_cfg(d.get("cliente"))
    if not cl:
        return 400, {"erro": "cliente desconhecido"}
    txt = str(d.get("csv") or "").lstrip("\ufeff")
    if not txt.strip():
        return 400, {"erro": "CSV vazio"}
    try:
        dialeto = csv.Sniffer().sniff(txt[:4000], delimiters=",;\t")
    except csv.Error:
        dialeto = csv.excel
    linhas = list(csv.reader(io.StringIO(txt), dialeto))
    if len(linhas) < 2:
        return 400, {"erro": "o CSV não tem linhas de campanha"}
    cab = [h.strip().lower() for h in linhas[0]]
    idx = {}
    for campo, nomes in COLS_CSV.items():
        for nm in nomes:
            if nm in cab:
                idx[campo] = cab.index(nm)
                break
    if "nome" not in idx:
        return 400, {"erro": "não achei a coluna do nome da campanha (ex.: \"Nome da campanha\")",
                     "colunas": linhas[0][:20]}
    criadas = atualizadas = ignoradas = 0
    with banco() as c:
        existentes = {r["nome"].lower(): dict(r) for r in c.execute("SELECT * FROM campanhas WHERE cliente=?", (cl["id"],))}
    # o mesmo nome em várias linhas (exportação por conjunto de anúncios ou por anúncio) vira UMA campanha com os
    # números somados e o período de ponta a ponta
    grupos = {}
    for ln in linhas[1:]:
        if not any(x.strip() for x in ln):
            continue
        v = {k: (ln[i] if i < len(ln) else "") for k, i in idx.items()}
        nome = v["nome"].strip()
        if not nome or nome.lower() in ("total", "resultados totais", "total results"):
            ignoradas += 1
            continue
        g = grupos.setdefault(nome.lower(), {"nome": nome})
        for k in ("gasto", "orcamento", "alcance", "impressoes", "cliques", "resultados"):
            x = num(v.get(k))
            if x is not None:
                g[k] = (g.get(k) or 0) + x
        for k, escolhe in (("inicio", min), ("fim", max)):
            dt = data_br(v.get(k))
            if dt:
                g[k] = escolhe(g[k], dt) if g.get(k) else dt
        if v.get("resultado_tipo", "").strip() and not g.get("resultado_tipo"):
            g["resultado_tipo"] = v["resultado_tipo"].strip()
    for chave, g in grupos.items():
        reg = {"cliente": cl["id"], "plataforma": d.get("plataforma") or "Meta (Instagram/Facebook)", "fonte": "csv",
               **{k: (g[k].isoformat() if hasattr(g.get(k), "isoformat") else g.get(k)) for k in COLS_CSV}}
        ant = existentes.get(chave)
        if ant:
            for k in CAMPOS_CAMP:  # o CSV atualiza os números; o resto (obs, objetivo) fica
                if reg.get(k) in (None, "") and ant.get(k) not in (None, ""):
                    reg[k] = ant[k]
            reg["id"] = ant["id"]
        if not data_br(reg.get("inicio")):
            reg["inicio"] = (ant or {}).get("inicio") or hoje().isoformat()
        st, r = salvar_campanha(reg)
        if st != 200:
            ignoradas += 1
        elif ant:
            atualizadas += 1
        else:
            criadas += 1
    return 200, {"ok": True, "criadas": criadas, "atualizadas": atualizadas, "ignoradas": ignoradas,
                 "colunas_lidas": sorted(idx)}


# ───────────────────────────── WhatsApp do cliente (status) pela API do Hermes Call ─────────────────────────────
_PAREAR = {}  # sid -> {"qr", "qr_t", "codigo", "codigo_t", "ouvindo", "pareado"}
_PAREAR_LOCK = threading.Lock()


def _hermes(metodo, caminho, corpo=None, timeout=60):
    chave = cfg()["seg"].get("hermes_chave")
    if not chave:
        raise RuntimeError("sem_chave")
    req = urllib.request.Request(HERMES + caminho, method=metodo,
                                 data=json.dumps(corpo).encode() if corpo is not None else None,
                                 headers={"X-API-Key": chave, "Content-Type": "application/json",
                                          "User-Agent": "painel-clientes/1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read()
            return json.loads(txt) if txt.strip() else {}
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read() or b"{}").get("error") or ""
        except ValueError:
            msg = ""
        raise RuntimeError(f"o Hermes respondeu {e.code} {msg}".strip()) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise RuntimeError(f"sem conexão com o Hermes ({type(e).__name__})") from None


def _sessao_hermes(sid):
    return next((s for s in _hermes("GET", "/api/sessions").get("sessions") or [] if s.get("id") == sid), None)


def _ouvir_pareamento(sid, segundos=240):
    """Fica ouvindo os eventos do Hermes (/api/events) enquanto o cliente aponta o celular: guarda o QR mais novo
    (ele troca a cada ~20 s) e para quando o WhatsApp conecta."""
    ate = time.time() + segundos
    chave = cfg()["seg"].get("hermes_chave") or ""
    try:
        while time.time() < ate:
            req = urllib.request.Request(HERMES + "/api/events", headers={"X-API-Key": chave,
                                                                          "Accept": "text/event-stream"})
            try:
                with urllib.request.urlopen(req, timeout=45) as r:
                    for linha in r:
                        if time.time() > ate:
                            return
                        linha = linha.decode("utf-8", "replace").strip()
                        if not linha.startswith("data:"):
                            continue
                        try:
                            ev = json.loads(linha[5:])
                        except ValueError:
                            continue
                        if ev.get("sessionId") != sid:
                            continue
                        with _PAREAR_LOCK:
                            st = _PAREAR.setdefault(sid, {})
                            if ev.get("qr"):
                                st.update(qr=ev["qr"], qr_t=time.time())
                            if ev.get("type") == "auth-state" and ev.get("paired") and ev.get("state") == "open":
                                st.update(pareado=True, qr="", codigo="")
                                return
            except (urllib.error.URLError, TimeoutError, OSError):
                time.sleep(2)  # caiu a conexão de eventos: abre de novo até o prazo
    finally:
        with _PAREAR_LOCK:
            _PAREAR.setdefault(sid, {})["ouvindo"] = False


def whatsapp_estado(cid):
    if not cfg()["seg"].get("hermes_chave"):
        return {"estado": "sem_chave"}
    with banco() as c:
        r = c.execute("SELECT * FROM whatsapp WHERE cliente=?", (cid,)).fetchone()
    if not r:
        return {"estado": "desconectado"}
    base = {"ultimo_status_em": r["ultimo_status_em"], "status_enviados": r["status_enviados"],
            "ultimo_erro": r["ultimo_erro"]}
    try:
        s = _sessao_hermes(r["sid"])
    except RuntimeError as e:
        return {"estado": "erro", "erro": str(e), **base}
    if not s:
        return {"estado": "desconectado", **base}
    if s.get("paired"):
        numero = str(s.get("jid") or "").split("@")[0].split(":")[0].split(".")[0]
        return {"estado": "conectado", "numero": numero, "online": bool(s.get("connected")), **base}
    with _PAREAR_LOCK:
        st = dict(_PAREAR.get(r["sid"]) or {})
    if st.get("codigo") and time.time() - st.get("codigo_t", 0) < 170:
        return {"estado": "codigo", "codigo": st["codigo"], **base}
    if st.get("qr") and time.time() - st.get("qr_t", 0) < 60:
        return {"estado": "qr", "qr": st["qr"], **base}
    if st.get("ouvindo"):
        return {"estado": "gerando", **base}
    return {"estado": "desconectado", **base}


def whatsapp_conectar(cid, numero=""):
    """Cria (1x) a conta do cliente no Hermes e começa o pareamento: QR (padrão) ou código pelo número do celular
    (para quem abre o painel no próprio celular e não tem como escanear a tela)."""
    cl = cliente_cfg(cid)
    with banco() as c:
        r = c.execute("SELECT sid FROM whatsapp WHERE cliente=?", (cid,)).fetchone()
    sid = r["sid"] if r else ""
    if sid and not _sessao_hermes(sid):
        sid = ""  # apagada no Hermes: cria outra
    if not sid:
        sid = str(_hermes("POST", "/api/sessions", {"name": f"Status · {cl['nome']}"}).get("id") or "")
        if not sid:
            raise RuntimeError("o Hermes não criou a conta")
        with banco() as c:
            c.execute("INSERT INTO whatsapp (cliente, sid, criado_em) VALUES (?,?,?) ON CONFLICT(cliente) DO UPDATE "
                      "SET sid=excluded.sid, criado_em=excluded.criado_em", (cid, sid, agora_iso()))
    s = _sessao_hermes(sid)
    if s and s.get("paired"):
        return whatsapp_estado(cid)
    with _PAREAR_LOCK:
        st = _PAREAR.setdefault(sid, {})
        st.update(qr="", codigo="", pareado=False)
        ouvir = not st.get("ouvindo")
        st["ouvindo"] = True
    if ouvir:  # escuta ANTES de pedir o QR: o primeiro sai em menos de 1 s
        threading.Thread(target=_ouvir_pareamento, args=(sid,), daemon=True).start()
        time.sleep(1.0)
    dig = re.sub(r"\D", "", str(numero or ""))
    if dig:
        if len(dig) in (10, 11):
            dig = "55" + dig
        cod = _hermes("POST", f"/api/sessions/{sid}/pair-code", {"phone": dig}).get("code") or ""
        with _PAREAR_LOCK:
            _PAREAR[sid].update(codigo=cod, codigo_t=time.time())
    else:
        _hermes("POST", f"/api/sessions/{sid}/pair")
        for _ in range(16):  # espera o 1º QR chegar pelos eventos (até ~8 s)
            with _PAREAR_LOCK:
                if _PAREAR[sid].get("qr"):
                    break
            time.sleep(0.5)
    return whatsapp_estado(cid)


def whatsapp_desconectar(cid):
    with banco() as c:
        r = c.execute("SELECT sid FROM whatsapp WHERE cliente=?", (cid,)).fetchone()
    if r:
        try:
            _hermes("POST", f"/api/sessions/{r['sid']}/logout")
        except RuntimeError as e:
            log(f"whatsapp desconectar {cid}: {e}")
    return {"estado": "desconectado"}


def whatsapp_status(d):
    """POST /api/whatsapp/status {cliente, video_base64, legenda?}: o postador do PC manda o vídeo que acabou de sair
    no Instagram; vai para o status do WhatsApp do cliente (se ele conectou)."""
    cid = d.get("cliente")
    if not cliente_cfg(cid):
        return 400, {"erro": "cliente desconhecido"}
    est = whatsapp_estado(cid)
    if est["estado"] != "conectado":
        return 409, {"erro": "WhatsApp do cliente não conectado", "estado": est["estado"]}
    b64 = str(d.get("video_base64") or "")
    if len(b64) < 1000:
        return 400, {"erro": "vídeo vazio"}
    with banco() as c:
        sid = c.execute("SELECT sid FROM whatsapp WHERE cliente=?", (cid,)).fetchone()["sid"]
    try:
        _hermes("POST", f"/api/sessions/{sid}/status/video",
                {"base64": b64, "caption": str(d.get("legenda") or "")[:700], "mimetype": "video/mp4"}, timeout=300)
    except RuntimeError as e:
        with banco() as c:
            c.execute("UPDATE whatsapp SET ultimo_erro=? WHERE cliente=?", (f"{agora_iso()} {e}"[:300], cid))
        return 502, {"erro": str(e)}
    with banco() as c:
        c.execute("UPDATE whatsapp SET ultimo_status_em=?, ultimo_erro='', status_enviados=status_enviados+1 "
                  "WHERE cliente=?", (agora_iso(), cid))
    return 200, {"ok": True}


# ───────────────────────────── HTTP ─────────────────────────────

# ── APROVAÇÃO DE PUBLICAÇÕES (dona 05/11/2026 13h: "crie no painel uma área de publicações pra aprovação, o mais
# parecido com como vai ficar no Instagram; o que clicar em Aprovar é postado"). O PC1 envia (admin), o cliente ou a
# administração aprova/recusa, o PC1 vê as aprovadas, posta e marca postado com o link.
APROV = PASTA / "aprovacao"
_ID_OK = re.compile(r"^[\w.-]{1,80}$")


def _aprov_dir(cli, iid=None):
    if not cliente_cfg(cli) or (iid is not None and not _ID_OK.match(str(iid))):
        return None
    return APROV / cli / iid if iid is not None else APROV / cli


def aprov_listar(cli):
    base = _aprov_dir(cli)
    out = []
    for m in sorted(base.glob("*/meta.json"), key=lambda x: x.stat().st_mtime, reverse=True) if base and base.exists() else []:
        try:
            out.append(json.loads(m.read_text("utf-8")))
        except ValueError:
            continue
    return out


def aprov_enviar(d):
    import base64
    cli, iid = str(d.get("cliente") or ""), str(d.get("id") or "")
    pasta = _aprov_dir(cli, iid)
    if not pasta:
        return 400, {"erro": "cliente ou id inválido"}
    pasta.mkdir(parents=True, exist_ok=True)
    nomes = []
    for a in d.get("arquivos") or []:
        nome = re.sub(r"[^\w.-]", "_", str(a.get("nome") or ""))[:60]
        if not nome or not nome.lower().endswith((".jpg", ".jpeg", ".png", ".mp4")):
            continue
        (pasta / nome).write_bytes(base64.b64decode(a.get("b64") or ""))
        nomes.append(nome)
    meta = {"id": iid, "cliente": cli, "tipo": d.get("tipo") or "carrossel", "legenda": str(d.get("legenda") or "")[:2200],
            "arquivos": nomes, "status": "pendente", "criado": agora_iso(), "titulo": str(d.get("titulo") or "")[:120]}
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), "utf-8")
    return 200, meta


def aprov_mudar(d, p, cid, campo):
    cli, iid = str(d.get("cliente") or ""), str(d.get("id") or "")
    if p != "admin" and cli != cid:
        return 403, {"erro": "sem permissão"}
    pasta = _aprov_dir(cli, iid)
    if not pasta or not (pasta / "meta.json").exists():
        return 404, {"erro": "publicação não encontrada"}
    meta = json.loads((pasta / "meta.json").read_text("utf-8"))
    if campo == "decidir":
        acao = d.get("acao")
        if acao not in ("aprovar", "recusar") or meta.get("status") not in ("pendente", "recusado", "aprovado"):
            return 409, {"erro": "não dá pra mudar essa publicação agora"}
        meta["status"] = "aprovado" if acao == "aprovar" else "recusado"
        meta["decidido"] = agora_iso()
        meta["por"] = p
        if d.get("obs"):
            meta["obs"] = str(d["obs"])[:500]
    else:  # postado (só admin, pelo PC1)
        meta["status"] = "postado"
        meta["link"] = str(d.get("link") or "")[:300]
        meta["postado"] = agora_iso()
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), "utf-8")
    return 200, meta


class Painel(BaseHTTPRequestHandler):
    server_version = "PainelClientes/1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *a):  # sem log por pedido (tem chave no cabeçalho, não na URL; mesmo assim, enxuto)
        pass

    def _ip(self):
        return (self.headers.get("X-Forwarded-For") or self.client_address[0]).split(",")[0].strip()

    def _enviar(self, status, corpo, tipo="application/json; charset=utf-8", extra=None):
        if isinstance(corpo, (dict, list)):
            corpo = json.dumps(corpo, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        elif isinstance(corpo, str):
            corpo = corpo.encode("utf-8")
        # página (73 KB) e painel com posts/pessoas: comprimidos chegam bem mais rápido no 4G do celular
        zipar = (len(corpo) > 1400 and tipo.startswith(("text/", "application/json", "image/svg"))
                 and "gzip" in (self.headers.get("Accept-Encoding") or ""))
        if zipar:
            corpo = gzip.compress(corpo, 6)
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        if zipar:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("X-Robots-Tag", "noindex, nofollow")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corpo)

    def _auth(self):
        ip, chave = self._ip(), self.headers.get("X-Chave") or ""
        self._bloq = bloqueado(ip)
        if self._bloq:
            return None, None
        p, cid = papel(chave)
        if p:
            anotar_casa(ip, self.headers.get("User-Agent") or "")
        elif chave:
            anotar_erro(ip)
            time.sleep(1.0)  # chave errada: devagar (tentativa em massa)
        return p, cid

    def _negado(self):
        if getattr(self, "_bloq", False):
            return self._enviar(429, {"erro": "muitas tentativas erradas; espere 10 minutos"}, extra={"Retry-After": "600"})
        return self._enviar(401, {"erro": "chave inválida"})

    def _periodo(self, q):
        ate = data_br((q.get("ate") or [""])[0]) or hoje()
        de = data_br((q.get("de") or [""])[0]) or ate - timedelta(days=29)
        if de > ate:
            de, ate = ate, de
        de = max(de, ate - timedelta(days=730))
        return de, ate

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        try:
            u = urllib.parse.urlsplit(self.path)
            q = urllib.parse.parse_qs(u.query)
            if u.path in ("/", "/index.html"):
                return self._enviar(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8",
                                    {"Content-Security-Policy": "frame-ancestors 'none'"})
            if u.path == "/robots.txt":
                return self._enviar(200, "User-agent: *\nDisallow: /\n", "text/plain; charset=utf-8")
            if u.path in ("/favicon.ico", "/favicon.svg"):
                return self._enviar(200, ICONE_SVG, "image/svg+xml", {"Cache-Control": "max-age=86400"})
            if u.path.startswith("/r/"):
                return self._redirecionar(u.path[3:].strip("/"))
            if u.path == "/api/saude":
                with banco() as c:
                    n = c.execute("SELECT COUNT(*) n FROM eventos").fetchone()["n"]
                return self._enviar(200, {"ok": True, "em": agora_iso(), "eventos": n})
            p, cid = self._auth()
            if not p:
                return self._negado()
            if u.path == "/api/eu":
                seg = cfg()["seg"]
                cls = [c for c in cfg()["clientes"] if p == "admin" or c["id"] == cid]
                base = os.environ.get("URL_PUBLICA", "https://clientes.opus-sem-limites.com.br").rstrip("/")
                return self._enviar(200, {"papel": p, "clientes": [
                    # 12/11 (dona): "cliente_desde" = botão "Desde que é cliente" no período
                    {**{k: c.get(k) for k in ("id", "nome", "tipo", "cor", "cidade", "instagram", "site", "whatsapp", "historico",
                                              "cliente_desde")},
                     **({"link_cliente": f"{base}/#k={(seg.get('clientes') or {}).get(c['id'])}"}
                        if p == "admin" and (seg.get("clientes") or {}).get(c["id"]) else {})} for c in cls]})
            if u.path == "/api/painel":
                alvo = (q.get("cliente") or [""])[0]
                if p != "admin" and alvo != cid:
                    return self._enviar(403, {"erro": "sem permissão"})
                if not cliente_cfg(alvo):
                    return self._enviar(404, {"erro": "cliente não encontrado"})
                de, ate = self._periodo(q)
                return self._enviar(200, montar_painel(alvo, de, ate))
            if u.path == "/api/aprovacao":
                alvo = (q.get("cliente") or [""])[0]
                if p != "admin" and alvo != cid:
                    return self._enviar(403, {"erro": "sem permissão"})
                return self._enviar(200, {"itens": aprov_listar(alvo)})
            if u.path == "/api/aprovacao/arquivo":
                alvo, iid, nome = ((q.get(k) or [""])[0] for k in ("cliente", "id", "nome"))
                if p != "admin" and alvo != cid:
                    return self._enviar(403, {"erro": "sem permissão"})
                pasta = _aprov_dir(alvo, iid)
                arq = pasta / nome if pasta and _ID_OK.match(nome) else None
                if not arq or not arq.is_file():
                    return self._enviar(404, {"erro": "arquivo não encontrado"})
                tipo = "video/mp4" if nome.lower().endswith(".mp4") else "image/jpeg"
                return self._enviar(200, arq.read_bytes(), tipo, {"Cache-Control": "private, max-age=3600"})
            if u.path == "/api/whatsapp":
                alvo = (q.get("cliente") or [""])[0]
                if p != "admin" and alvo != cid:
                    return self._enviar(403, {"erro": "sem permissão"})
                if not cliente_cfg(alvo):
                    return self._enviar(404, {"erro": "cliente não encontrado"})
                return self._enviar(200, whatsapp_estado(alvo))
            if u.path == "/api/geral" and p == "admin":
                de, ate = self._periodo(q)
                linhas = []
                for cl in cfg()["clientes"]:
                    r = montar_painel(cl["id"], de, ate, completo=False)
                    cs = {x["id"]: x for x in r["cards"]}
                    linhas.append({"id": cl["id"], "nome": cl["nome"], "tipo": cl.get("tipo") or "cliente",
                                   "cor": cl.get("cor"), **{k: (cs[k]["valor"] if cs[k]["conectado"] else None)
                                                            for k in cs}, "atualizado_em": r["atualizado_em"],
                                   "fontes_ok": sum(1 for f in r["fontes"] if f["ok"]),
                                   "fontes_erro": [f["fonte"] + ": " + f["detalhe"] for f in r["fontes"] if not f["ok"]]})
                return self._enviar(200, {"periodo": {"de": de.isoformat(), "ate": ate.isoformat()}, "linhas": linhas})
            return self._enviar(404, {"erro": "rota não existe"})
        except Exception as e:  # noqa: BLE001
            log(f"GET {self.path.split('?')[0]}: {type(e).__name__}: {e}")
            return self._enviar(500, {"erro": "erro interno do painel"})

    def do_POST(self):
        try:
            u = urllib.parse.urlsplit(self.path)
            tam = (self.headers.get("Content-Length") or "0").strip()
            if not tam.isdigit():
                return self._enviar(400, {"erro": "pedido inválido"})
            n = int(tam)
            if n > (MAX_VIDEO if u.path in ("/api/whatsapp/status", "/api/aprovacao/enviar") else MAX_CORPO):
                return self._enviar(413, {"erro": "arquivo grande demais"})
            try:
                d = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            except ValueError:
                return self._enviar(400, {"erro": "JSON inválido"})
            if u.path == "/api/entrar":  # 30/10: login com usuário e senha -> a chave do cliente
                ip = self._ip()
                if bloqueado(ip):
                    return self._enviar(429, {"erro": "Muitas tentativas erradas. Espere 10 minutos e tente de novo."},
                                        extra={"Retry-After": "600"})
                seg = cfg()["seg"]
                usuario = str(d.get("usuario") or "").strip().lower()
                senha = str(d.get("senha") or "").strip().lower()
                lg = (seg.get("logins") or {}).get(usuario)
                sha = hashlib.sha256(f"{seg.get('sal') or ''}|{senha}".encode()).hexdigest()
                if lg and hmac.compare_digest(sha, lg.get("sha") or "") and cliente_cfg(lg.get("cliente")):
                    chave = (seg.get("clientes") or {}).get(lg["cliente"])
                    if chave:
                        return self._enviar(200, {"chave": chave})
                anotar_erro(ip)
                time.sleep(1.5)  # senha errada: devagar
                return self._enviar(401, {"erro": "usuário ou senha incorretos"})
            p, cid = self._auth()
            if not p:
                return self._negado()
            if u.path == "/api/pessoa":
                st, r = salvar_pessoa(d, p, cid)
                return self._enviar(st, r)
            if u.path == "/api/pessoa/juntar":
                st, r = juntar_pessoa(d, p, cid)
                return self._enviar(st, r)
            if u.path in ("/api/whatsapp/conectar", "/api/whatsapp/desconectar"):  # o próprio cliente pode
                alvo = d.get("cliente")
                if p != "admin" and alvo != cid:
                    return self._enviar(403, {"erro": "sem permissão"})
                if not cliente_cfg(alvo):
                    return self._enviar(404, {"erro": "cliente não encontrado"})
                if not cfg()["seg"].get("hermes_chave"):
                    return self._enviar(409, {"estado": "sem_chave", "erro": "a ligação com o Hermes Call ainda não foi configurada"})
                try:
                    r = (whatsapp_desconectar(alvo) if u.path.endswith("/desconectar")
                         else whatsapp_conectar(alvo, d.get("numero") or ""))
                except RuntimeError as e:
                    return self._enviar(502, {"erro": str(e)})
                return self._enviar(200, r)
            if u.path == "/api/aprovacao/decidir":  # cliente (a dele) ou administração
                st, r = aprov_mudar(d, p, cid, "decidir")
                return self._enviar(st, r)
            if p != "admin":
                return self._enviar(403, {"erro": "só a administração pode fazer isso"})
            if u.path == "/api/aprovacao/enviar":
                st, r = aprov_enviar(d)
                return self._enviar(st, r)
            if u.path == "/api/aprovacao/postado":
                st, r = aprov_mudar(d, p, cid, "postado")
                return self._enviar(st, r)
            rotas = {"/api/coleta": lambda: (200, ingerir_coleta(d)), "/api/link": lambda: salvar_link(d),
                     "/api/link/apagar": lambda: apagar_link(d), "/api/campanha": lambda: salvar_campanha(d),
                     "/api/campanha/apagar": lambda: apagar_campanha(d),
                     "/api/campanhas/importar": lambda: importar_csv(d),
                     "/api/whatsapp/status": lambda: whatsapp_status(d)}
            if u.path not in rotas:
                return self._enviar(404, {"erro": "rota não existe"})
            st, r = rotas[u.path]()
            return self._enviar(st, r)
        except Exception as e:  # noqa: BLE001
            log(f"POST {self.path.split('?')[0]}: {type(e).__name__}: {e}")
            return self._enviar(500, {"erro": "erro interno do painel"})

    def _redirecionar(self, codigo):
        codigo = slug(codigo, 60)
        with banco() as c:
            ln = c.execute("SELECT * FROM links WHERE codigo=?", (codigo,)).fetchone()
            if not ln:
                return self._enviar(404, "<!doctype html><meta charset=utf-8><title>Link não encontrado</title>"
                                         "<p style='font-family:sans-serif'>Link não encontrado.</p>",
                                    "text/html; charset=utf-8")
            ua, ip = self.headers.get("User-Agent") or "", self._ip()
            # robô (prévia do WhatsApp/Facebook) e quem entrou no painel (dona testando o link) não contam
            if not ROBO.search(ua) and self.command == "GET" and not eh_casa(ip, ua):
                sal = cfg()["seg"].get("sal") or "painel"
                vis = hashlib.sha256(f"{sal}|{ip}|{ua}|{hoje()}".encode()).hexdigest()[:16]
                c.execute("INSERT INTO cliques (codigo, cliente, em, visitante, ua, ref) VALUES (?,?,?,?,?,?)",
                          (codigo, ln["cliente"], agora_iso(), vis, ua[:200], (self.headers.get("Referer") or "")[:200]))
        destino = ln["destino"]
        partes = urllib.parse.urlsplit(destino)
        # o site sabe de que campanha veio (?c=código), a não ser que o link já diga
        if (partes.hostname or "").endswith("opus-sem-limites.com.br") and "c" not in urllib.parse.parse_qs(partes.query):
            destino += ("&" if "?" in destino else "?") + "c=" + codigo
        # cabeçalho HTTP só aceita ASCII: acento no destino vira %XX (antes dava erro 500)
        destino = urllib.parse.quote(destino, safe=":/?#[]@!$&'()*+,;=%~")
        return self._enviar(302, b"", "text/plain", {"Location": destino})


def main():
    criar_banco()
    if not SEGREDOS.exists():
        SEGREDOS.write_text(json.dumps({"admin": secrets.token_urlsafe(24), "sal": secrets.token_hex(16),
                                        "clientes": {}}, indent=1), encoding="utf-8")
        log("segredos.json criado (chave de admin nova)")
    threading.Thread(target=vigiar_fontes, daemon=True).start()
    srv = ThreadingHTTPServer((HOST, PORTA), Painel)
    srv.daemon_threads = True
    log(f"painel de clientes em {HOST}:{PORTA} (dados em {PASTA})")
    srv.serve_forever()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
