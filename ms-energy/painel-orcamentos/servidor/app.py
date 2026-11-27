# /opt/orcamentos-ms/servidor/app.py
"""Painel de Orçamentos MS Energy — servidor (FastAPI + SQLite + Chromium/Playwright para o PDF).

Rotas principais:
  /                      painel (SPA em web/)
  /api/...               API do painel (login por cookie)
  /p/<token>             proposta pública para o cliente (sem login) + /p/<token>/pdf
Dados em PASTA_DADOS (volume): banco.sqlite, pdf/ (cache), CREDENCIAIS_INICIAIS.txt (1ª execução).
Documentação: ../ARQUITETURA.md
"""
import asyncio
import csv
import datetime as dt
import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import threading
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import motor

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.environ.get("PASTA_DADOS", os.path.join(AQUI, "dados"))
WEB = os.path.join(AQUI, "web")
URL_PUBLICA = os.environ.get("URL_PUBLICA", "https://orcamentos.opus-sem-limites.com.br").rstrip("/")
os.makedirs(os.path.join(DADOS, "pdf"), exist_ok=True)
BANCO = os.path.join(DADOS, "banco.sqlite")
COOKIE = "orc_sessao"
STATUS = ["rascunho", "enviado", "negociando", "fechado", "perdido"]
_trava = threading.RLock()


# ============================================================================ banco
def db():
    c = sqlite3.connect(BANCO, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def iniciar_banco():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY, nome TEXT NOT NULL, usuario TEXT UNIQUE NOT NULL, senha TEXT NOT NULL,
            papel TEXT NOT NULL DEFAULT 'vendedor', telefone TEXT DEFAULT '', email TEXT DEFAULT '',
            ativo INTEGER NOT NULL DEFAULT 1, meta REAL DEFAULT 0, comissao_pct REAL DEFAULT 0,
            cor TEXT DEFAULT '', criado TEXT NOT NULL, ultimo_login TEXT);
        CREATE TABLE IF NOT EXISTS sessoes(token TEXT PRIMARY KEY, uid INTEGER NOT NULL, expira REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS orcamentos(
            id INTEGER PRIMARY KEY, num TEXT UNIQUE, token TEXT UNIQUE, vendedor_id INTEGER,
            cliente_nome TEXT, cliente_doc TEXT, cliente_tel TEXT, cliente_cidade TEXT,
            consumo REAL, kwp REAL, valor REAL, valor_max REAL, tipo TEXT, status TEXT DEFAULT 'rascunho',
            dados TEXT, resumo TEXT, criado TEXT, atualizado TEXT, apagado INTEGER DEFAULT 0,
            visualizacoes INTEGER DEFAULT 0, ultima_visualizacao TEXT, fechado_em TEXT, motivo_perda TEXT DEFAULT '',
            proximo_contato TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS eventos(id INTEGER PRIMARY KEY, orc_id INTEGER, uid INTEGER, tipo TEXT, texto TEXT, quando TEXT);
        CREATE TABLE IF NOT EXISTS config(chave TEXT PRIMARY KEY, valor TEXT);
        CREATE INDEX IF NOT EXISTS ix_orc_vend ON orcamentos(vendedor_id);
        CREATE INDEX IF NOT EXISTS ix_orc_status ON orcamentos(status);
        CREATE INDEX IF NOT EXISTS ix_ev_orc ON eventos(orc_id);
        """)
        cols = [r[1] for r in c.execute("PRAGMA table_info(usuarios)")]
        if "acrescimo_pct" not in cols:  # acréscimo OCULTO no preço do vendedor (só o admin vê)
            c.execute("ALTER TABLE usuarios ADD COLUMN acrescimo_pct REAL DEFAULT 0")
        for col in ("fluxia_login", "fluxia_senha"):  # acesso do vendedor ao FluxIA (WhatsApp com robô)
            if col not in cols:
                c.execute(f"ALTER TABLE usuarios ADD COLUMN {col} TEXT DEFAULT ''")
        if "acrescimo_ar_pct" not in cols:  # acréscimo OCULTO sobre o preço de ar-condicionado que o vendedor digita
            c.execute("ALTER TABLE usuarios ADD COLUMN acrescimo_ar_pct REAL DEFAULT 10")
        if not c.execute("SELECT 1 FROM usuarios WHERE papel='admin'").fetchone():
            senha = secrets.token_urlsafe(9)
            c.execute("INSERT INTO usuarios(nome,usuario,senha,papel,criado) VALUES(?,?,?,?,?)",
                      ("Administrador", "admin", hash_senha(senha), "admin", agora()))
            with open(os.path.join(DADOS, "CREDENCIAIS_INICIAIS.txt"), "w", encoding="utf-8") as f:
                f.write(f"Painel de Orçamentos MS Energy\n{URL_PUBLICA}\nusuario: admin\nsenha: {senha}\n"
                        "Troque a senha em Minha conta depois de entrar.\n")
            print(f"[orcamentos] admin criado; senha em {DADOS}/CREDENCIAIS_INICIAIS.txt", flush=True)


def agora():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_senha(s, sal=None):
    sal = sal or secrets.token_hex(8)
    h = hashlib.pbkdf2_hmac("sha256", s.encode(), sal.encode(), 200_000).hex()
    return f"{sal}${h}"


def conferir_senha(s, guardado):
    try:
        sal, _ = guardado.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_senha(s, sal), guardado)


def ler_config():
    with db() as c:
        r = c.execute("SELECT valor FROM config WHERE chave='<SEGREDO_REMOVIDO>'").fetchone()
    salvo = json.loads(r["valor"]) if r else {}
    return motor.mesclar(motor.CONFIG_PADRAO, salvo)


def gravar_config(cfg):
    with db() as c:
        c.execute("INSERT INTO config(chave,valor) VALUES('empresa_cfg',?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
                  (json.dumps(cfg, ensure_ascii=False),))


def fator_de(c, uid):
    """1 + acréscimo oculto do vendedor dono do orçamento."""
    r = c.execute("SELECT acrescimo_pct FROM usuarios WHERE id=?", (uid,)).fetchone() if uid else None
    return 1 + float((r["acrescimo_pct"] if r else 0) or 0) / 100


def fator_ar_de(c, uid):
    """1 + acréscimo oculto sobre o preço de ar-condicionado digitado pelo vendedor (padrão 10%)."""
    r = c.execute("SELECT acrescimo_ar_pct FROM usuarios WHERE id=?", (uid,)).fetchone() if uid else None
    v = r["acrescimo_ar_pct"] if r and r["acrescimo_ar_pct"] is not None else 10
    return 1 + float(v or 0) / 100


def e_ar(item):
    """Ar-condicionado = preço livre (o vendedor digita) e não leva o acréscimo do material solar."""
    return bool(item) and (item.get("preco_livre") or item.get("icone") == "ar")


def cfg_para(u, c):
    """Config que vai para a tela. Vendedor recebe preços de catálogo já com o acréscimo dele e sem as regras internas."""
    cfg = ler_config()
    cfg["fin_fator"] = motor.fator_fin(cfg)
    if u["papel"] == "admin":
        return cfg
    f = fator_de(c, u["id"])
    cfg = json.loads(json.dumps(cfg))
    cfg["preco"] = {"arredondar": cfg["preco"].get("arredondar", 100)}
    for lista in ("extras", "baterias"):
        for x in cfg[lista]:
            if lista == "extras" and e_ar(x):
                x["preco"] = 0
                x["preco_livre"] = True
            else:
                x["preco"] = motor.com_fator(x.get("preco"), f)
    cfg["pagamento"]["financiamento"].pop("margem_pct", None)
    return cfg


def travar_dados_vendedor(dados, cfg, fator, fator_ar=1.10):
    """Vendedor não muda as regras de preço: só pode SUBIR o valor e acrescentar itens/outros custos.
    Ar-condicionado: o vendedor digita o preço (preco_vendedor) e entra +acréscimo_ar oculto; não leva o do solar."""
    d = json.loads(json.dumps(dados or {}))
    for e in d.get("extras") or []:
        cat = motor.achar(cfg["extras"], e.get("id"))
        if cat and e_ar(cat):
            try:
                pv = max(0.0, float(e.get("preco_vendedor") or 0))
            except (TypeError, ValueError):
                pv = 0.0
            e["preco_vendedor"] = pv
            e["preco"] = round(pv * fator_ar, 2)
            e["no_valor"] = True
            continue
        if cat:  # item do catálogo: preço nunca abaixo do catálogo (com o acréscimo dele)
            base = motor.com_fator(cat.get("preco"), fator)
            try:
                e["preco"] = max(float(e.get("preco") or 0), base)
            except (TypeError, ValueError):
                e["preco"] = base
        else:  # item livre / outros custos
            e["preco"] = max(0.0, float(e.get("preco") or 0))
        e["no_valor"] = True  # sem cortesia
    for b in d.get("baterias") or []:
        cat = motor.achar(cfg["baterias"], b.get("id"))
        base = motor.com_fator(cat.get("preco"), fator) if cat else 0
        try:
            b["preco"] = max(float(b.get("preco") or 0), base)
        except (TypeError, ValueError):
            b["preco"] = base
    # pagamento: só liga/desliga as formas; os números são os da empresa
    pg_emp = cfg["pagamento"]
    pg = d.get("pagamento") or {}
    novo = json.loads(json.dumps(pg_emp))
    for k in novo:
        if isinstance(pg.get(k), dict) and "ativo" in pg[k]:
            novo[k]["ativo"] = bool(pg[k]["ativo"])
    d["pagamento"] = novo
    d["mostrar_desconto"] = False
    return d


def proximo_num(c):
    """Próximo número do mês (MSaamm-0001). Usa a MESMA conexão/transação de quem grava o orçamento."""
    hoje = dt.date.today()
    chave = f"seq_{hoje:%y%m}"
    r = c.execute("SELECT valor FROM config WHERE chave=?", (chave,)).fetchone()
    n = int(r["valor"]) + 1 if r else 1
    c.execute("INSERT INTO config(chave,valor) VALUES(?,?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor", (chave, str(n)))
    return f"MS{hoje:%y%m}-{n:04d}"


def evento(c, orc_id, uid, tipo, texto=""):
    c.execute("INSERT INTO eventos(orc_id,uid,tipo,texto,quando) VALUES(?,?,?,?,?)", (orc_id, uid, tipo, texto, agora()))


# ============================================================================ PDF (Chromium via Playwright)
class Impressora:
    def __init__(self):
        self.pw = None
        self.browser = None
        self.sem = asyncio.Semaphore(2)

    async def abrir(self):
        if self.browser and self.browser.is_connected():
            return
        from playwright.async_api import async_playwright
        if not self.pw:
            self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])

    async def pdf(self, html):
        async with self.sem:
            await self.abrir()
            ctx = await self.browser.new_context()
            try:
                pg = await ctx.new_page()
                await pg.set_content(html, wait_until="load")
                return await pg.pdf(format="A4", print_background=True, prefer_css_page_size=True)
            finally:
                await ctx.close()

    async def fechar(self):
        try:
            if self.browser:
                await self.browser.close()
            if self.pw:
                await self.pw.stop()
        except Exception:
            pass


IMP = Impressora()


@asynccontextmanager
async def ciclo(app):
    iniciar_banco()
    yield
    await IMP.fechar()


app = FastAPI(title="Orçamentos MS Energy", lifespan=ciclo, docs_url=None, redoc_url=None)


# ============================================================================ autenticação
def usuario_atual(request: Request):
    tok = request.cookies.get(COOKIE)
    if not tok:
        raise HTTPException(401, "Entre de novo")
    with db() as c:
        r = c.execute("SELECT u.* FROM sessoes s JOIN usuarios u ON u.id=s.uid WHERE s.token=? AND s.expira>? AND u.ativo=1",
                      (tok, time.time())).fetchone()
    if not r:
        raise HTTPException(401, "Sessão expirada")
    return dict(r)


def so_admin(u=Depends(usuario_atual)):
    if u["papel"] != "admin":
        raise HTTPException(403, "Só o administrador pode fazer isso")
    return u


def publico_usuario(u, admin=False):
    campos = ["id", "nome", "usuario", "papel", "telefone", "email", "ativo", "meta", "comissao_pct", "cor", "criado", "ultimo_login"]
    if admin:
        campos += ["acrescimo_pct", "acrescimo_ar_pct", "fluxia_login"]
    out = {k: u[k] for k in campos if k in u}
    out["tem_whatsapp"] = bool(u.get("fluxia_login"))
    return out


@app.post("/api/login")
async def login(request: Request):
    b = await request.json()
    with db() as c:
        r = c.execute("SELECT * FROM usuarios WHERE lower(usuario)=lower(?)", ((b.get("usuario") or "").strip(),)).fetchone()
        if not r or not r["ativo"] or not conferir_senha(b.get("senha") or "", r["senha"]):
            await asyncio.sleep(0.8)
            raise HTTPException(401, "Usuário ou senha incorretos")
        tok = secrets.token_urlsafe(32)
        dias = 30 if b.get("lembrar", True) else 1
        c.execute("INSERT INTO sessoes(token,uid,expira) VALUES(?,?,?)", (tok, r["id"], time.time() + dias * 86400))
        c.execute("UPDATE usuarios SET ultimo_login=? WHERE id=?", (agora(), r["id"]))
        c.execute("DELETE FROM sessoes WHERE expira<?", (time.time(),))
    resp = JSONResponse({"ok": True, "usuario": publico_usuario(dict(r))})
    resp.set_cookie(COOKIE, tok, max_age=dias * 86400, httponly=True, samesite="lax", secure=request.url.scheme == "https")
    return resp


@app.post("/api/logout")
async def logout(request: Request):
    tok = request.cookies.get(COOKIE)
    if tok:
        with db() as c:
            c.execute("DELETE FROM sessoes WHERE token=?", (tok,))
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(COOKIE)
    return resp


@app.get("/api/eu")
async def eu(u=Depends(usuario_atual)):
    return publico_usuario(u)


@app.put("/api/eu")
async def eu_editar(request: Request, u=Depends(usuario_atual)):
    b = await request.json()
    with db() as c:
        if b.get("senha_nova"):
            if not conferir_senha(b.get("senha_atual") or "", u["senha"]):
                raise HTTPException(400, "Senha atual incorreta")
            if len(b["senha_nova"]) < 6:
                raise HTTPException(400, "A senha nova precisa de pelo menos 6 caracteres")
            c.execute("UPDATE usuarios SET senha=? WHERE id=?", (hash_senha(b["senha_nova"]), u["id"]))
        for campo in ("nome", "telefone", "email", "cor"):
            if campo in b:
                c.execute(f"UPDATE usuarios SET {campo}=? WHERE id=?", (str(b[campo])[:120], u["id"]))
        r = c.execute("SELECT * FROM usuarios WHERE id=?", (u["id"],)).fetchone()
    return publico_usuario(dict(r))


# ============================================================================ configuração / catálogo
@app.get("/api/config")
async def config_ler(u=Depends(usuario_atual)):
    with db() as c:
        return {"cfg": cfg_para(u, c), "status": STATUS}


@app.put("/api/config")
async def config_gravar(request: Request, u=Depends(so_admin)):
    b = await request.json()
    cfg = motor.mesclar(motor.CONFIG_PADRAO, b.get("cfg") or {})
    for lista in ("paineis", "inversores", "estruturas", "extras", "baterias", "financeiras"):
        if lista in (b.get("cfg") or {}):
            cfg[lista] = b["cfg"][lista]
    cfg.pop("fin_fator", None)
    gravar_config(cfg)
    cfg["fin_fator"] = motor.fator_fin(cfg)
    return {"ok": True, "cfg": cfg}


@app.post("/api/config/restaurar")
async def config_restaurar(u=Depends(so_admin)):
    gravar_config(motor.CONFIG_PADRAO)
    return {"ok": True, "cfg": motor.CONFIG_PADRAO}


# ============================================================================ vendedores
@app.get("/api/vendedores")
async def vendedores(u=Depends(usuario_atual)):
    with db() as c:
        linhas = c.execute("SELECT * FROM usuarios ORDER BY ativo DESC, nome").fetchall()
        mes = dt.date.today().strftime("%Y-%m")
        stats = {r["vendedor_id"]: dict(r) for r in c.execute(
            "SELECT vendedor_id, count(*) n, sum(valor) total, sum(CASE WHEN status='fechado' THEN valor ELSE 0 END) fechado,"
            " sum(CASE WHEN status='fechado' THEN 1 ELSE 0 END) nf FROM orcamentos WHERE apagado=0 AND substr(criado,1,7)=? GROUP BY vendedor_id", (mes,))}
    out = []
    for r in linhas:
        if u["papel"] != "admin" and r["id"] != u["id"]:
            continue
        p = publico_usuario(dict(r), admin=u["papel"] == "admin")
        p["mes"] = stats.get(r["id"], {"n": 0, "total": 0, "fechado": 0, "nf": 0})
        out.append(p)
    return out


@app.post("/api/vendedores")
async def vendedor_criar(request: Request, u=Depends(so_admin)):
    b = await request.json()
    usuario = (b.get("usuario") or "").strip().lower()
    if not usuario or not b.get("nome"):
        raise HTTPException(400, "Nome e usuário são obrigatórios")
    senha = b.get("senha") or secrets.token_urlsafe(6)
    try:
        with db() as c:
            c.execute("INSERT INTO usuarios(nome,usuario,senha,papel,telefone,email,meta,comissao_pct,cor,criado,acrescimo_pct,acrescimo_ar_pct) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                      (b["nome"].strip(), usuario, hash_senha(senha), "admin" if b.get("papel") == "admin" else "vendedor",
                       b.get("telefone", ""), b.get("email", ""), float(b.get("meta") or 0), float(b.get("comissao_pct") or 0),
                       b.get("cor", ""), agora(), max(0.0, float(b.get("acrescimo_pct") or 0)),
                       max(0.0, float(b["acrescimo_ar_pct"] if b.get("acrescimo_ar_pct") not in (None, "") else 10))))
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Esse usuário já existe")
    if b.get("fluxia_login"):
        with db() as c:
            c.execute("UPDATE usuarios SET fluxia_login=?, fluxia_senha=? WHERE lower(usuario)=?", (b["fluxia_login"].strip(), b.get("fluxia_senha") or "", usuario))
    return {"ok": True, "senha": senha}


@app.put("/api/vendedores/{vid}")
async def vendedor_editar(vid: int, request: Request, u=Depends(so_admin)):
    b = await request.json()
    with db() as c:
        if not c.execute("SELECT 1 FROM usuarios WHERE id=?", (vid,)).fetchone():
            raise HTTPException(404, "Não encontrado")
        for campo in ("nome", "telefone", "email", "cor"):
            if campo in b:
                c.execute(f"UPDATE usuarios SET {campo}=? WHERE id=?", (b[campo], vid))
        for campo in ("fluxia_login", "fluxia_senha"):
            if campo in b and (campo == "fluxia_login" or b[campo]):
                c.execute(f"UPDATE usuarios SET {campo}=? WHERE id=?", (str(b[campo] or "").strip(), vid))
            if campo in b and campo == "fluxia_login":
                WA_TOKENS.pop(vid, None)
        for campo in ("meta", "comissao_pct", "acrescimo_pct", "acrescimo_ar_pct"):
            if campo in b:
                c.execute(f"UPDATE usuarios SET {campo}=? WHERE id=?", (max(0.0, float(b[campo] or 0)), vid))
        if "ativo" in b:
            if vid == u["id"] and not b["ativo"]:
                raise HTTPException(400, "Você não pode desativar a si mesmo")
            c.execute("UPDATE usuarios SET ativo=? WHERE id=?", (1 if b["ativo"] else 0, vid))
            if not b["ativo"]:
                c.execute("DELETE FROM sessoes WHERE uid=?", (vid,))
        if "papel" in b and vid != u["id"]:
            c.execute("UPDATE usuarios SET papel=? WHERE id=?", ("admin" if b["papel"] == "admin" else "vendedor", vid))
        nova = None
        if b.get("nova_senha"):
            nova = b["nova_senha"] if isinstance(b["nova_senha"], str) and len(b["nova_senha"]) >= 6 else secrets.token_urlsafe(6)
            c.execute("UPDATE usuarios SET senha=? WHERE id=?", (hash_senha(nova), vid))
            c.execute("DELETE FROM sessoes WHERE uid=?", (vid,))
    return {"ok": True, "senha": nova}


# ============================================================================ cálculo ao vivo
def preparar(u, dados, c, dono=None):
    """Devolve (dados, fator, dono_id) prontos para o motor, com as regras de preço aplicadas."""
    cfg = ler_config()
    if u["papel"] == "admin":
        dono = int(dados.get("vendedor_id") or 0) or dono or u["id"]
    else:
        dono = u["id"]
    f = fator_de(c, dono)
    if u["papel"] != "admin":
        dados = travar_dados_vendedor(dados, cfg, f, fator_ar_de(c, dono))
    return dados, f, dono, cfg


@app.post("/api/calcular")
async def calcular(request: Request, u=Depends(usuario_atual)):
    b = await request.json()
    try:
        with db() as c:
            dados, f, _, cfg = preparar(u, b.get("dados") or {}, c)
        return motor.resumo(dados, cfg, f)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"Não consegui calcular: {e}")


@app.post("/api/previa", response_class=HTMLResponse)
async def previa(request: Request, u=Depends(usuario_atual)):
    b = await request.json()
    with db() as c:
        dados, f, dono, cfg = preparar(u, b.get("dados") or {}, c)
        v = c.execute("SELECT nome,telefone FROM usuarios WHERE id=?", (dono,)).fetchone()
    html, _ = motor.montar_html(dados, cfg, vendedor=dict(v) if v else None, num=b.get("num") or "PRÉVIA", fator=f)
    return HTMLResponse(html)


# ============================================================================ orçamentos
def pode_ver(u, r):
    return u["papel"] == "admin" or r["vendedor_id"] == u["id"]


def linha_orc(r, nomes=None):
    d = dict(r)
    d.pop("dados", None)
    d["resumo"] = json.loads(r["resumo"] or "{}")
    d["link"] = f"{URL_PUBLICA}/p/{r['token']}"
    if nomes is not None:
        d["vendedor_nome"] = nomes.get(r["vendedor_id"], "?")
    return d


def nomes_vendedores(c):
    return {r["id"]: r["nome"] for r in c.execute("SELECT id,nome FROM usuarios")}


def gravar_orc(c, oid, dados, u, novo=False):
    dono_atual = None
    if oid:
        r0 = c.execute("SELECT vendedor_id FROM orcamentos WHERE id=?", (oid,)).fetchone()
        dono_atual = r0["vendedor_id"] if r0 else None
    dados, f, dono, cfg = preparar(u, dict(dados), c, dono_atual)
    d = motor.dimensionar(dados, cfg, f)
    if u["papel"] != "admin":
        for e in dados.get("extras") or []:
            if e_ar(motor.achar(cfg["extras"], e.get("id"))) and not e.get("preco_vendedor"):
                raise HTTPException(400, "Informe o preço de cada ar-condicionado.")
    if u["papel"] != "admin" and d["valor"] < d["preco_sugerido"] - 0.01:
        raise HTTPException(400, f"O valor não pode ficar abaixo de R$ {motor.brl(d['preco_sugerido'])}. "
                                 "Você pode aumentar o valor ou acrescentar itens, mas não baixar.")
    res = motor.resumo(dados, cfg, f)
    campos = dict(cliente_nome=(dados.get("cliente_nome") or "").strip(), cliente_doc=dados.get("cliente_doc") or "",
                  cliente_tel=dados.get("cliente_tel") or "", cliente_cidade=dados.get("cliente_cidade") or "",
                  consumo=res["consumo"], kwp=res["kwp"], valor=res["valor"], valor_max=max(o["valor"] for o in res["opcoes"]),
                  tipo=d["tipo"], dados=json.dumps(dados, ensure_ascii=False), resumo=json.dumps(res, ensure_ascii=False),
                  atualizado=agora(), proximo_contato=dados.get("proximo_contato") or "")
    if novo:
        campos.update(num=proximo_num(c), token=secrets.token_urlsafe(10), vendedor_id=u["id"], criado=agora(),
                      status=dados.get("status") or "rascunho")
        if u["papel"] == "admin" and dados.get("vendedor_id"):
            campos["vendedor_id"] = int(dados["vendedor_id"])
        cols = ",".join(campos)
        cur = c.execute(f"INSERT INTO orcamentos({cols}) VALUES({','.join('?' * len(campos))})", tuple(campos.values()))
        oid = cur.lastrowid
        evento(c, oid, u["id"], "criado", f"Orçamento {campos['num']} criado · R$ {motor.brl(res['valor'])}")
    else:
        if u["papel"] == "admin" and dados.get("vendedor_id"):
            campos["vendedor_id"] = int(dados["vendedor_id"])
        sets = ",".join(f"{k}=?" for k in campos)
        c.execute(f"UPDATE orcamentos SET {sets} WHERE id=?", (*campos.values(), oid))
        evento(c, oid, u["id"], "editado", f"Atualizado · R$ {motor.brl(res['valor'])}")
    return oid


@app.get("/api/orcamentos")
async def orc_listar(request: Request, u=Depends(usuario_atual)):
    q = request.query_params
    sql, par = "SELECT * FROM orcamentos WHERE apagado=0", []
    if u["papel"] != "admin":
        sql += " AND vendedor_id=?"
        par.append(u["id"])
    elif q.get("vendedor"):
        sql += " AND vendedor_id=?"
        par.append(int(q["vendedor"]))
    if q.get("status"):
        sql += " AND status=?"
        par.append(q["status"])
    if q.get("tipo"):
        sql += " AND tipo=?"
        par.append(q["tipo"])
    if q.get("de"):
        sql += " AND substr(criado,1,10)>=?"
        par.append(q["de"])
    if q.get("ate"):
        sql += " AND substr(criado,1,10)<=?"
        par.append(q["ate"])
    if q.get("q"):
        t = f"%{q['q'].strip()}%"
        sql += " AND (cliente_nome LIKE ? OR num LIKE ? OR cliente_doc LIKE ? OR cliente_tel LIKE ? OR cliente_cidade LIKE ?)"
        par += [t] * 5
    sql += " ORDER BY id DESC LIMIT ?"
    par.append(min(int(q.get("limite") or 500), 2000))
    with db() as c:
        nomes = nomes_vendedores(c)
        return [linha_orc(r, nomes) for r in c.execute(sql, par)]


@app.post("/api/orcamentos")
async def orc_criar(request: Request, u=Depends(usuario_atual)):
    b = await request.json()
    with _trava, db() as c:
        oid = gravar_orc(c, None, b.get("dados") or {}, u, novo=True)
        r = c.execute("SELECT * FROM orcamentos WHERE id=?", (oid,)).fetchone()
        return linha_orc(r, nomes_vendedores(c))


@app.get("/api/orcamentos/{oid}")
async def orc_ler(oid: int, u=Depends(usuario_atual)):
    with db() as c:
        r = c.execute("SELECT * FROM orcamentos WHERE id=? AND apagado=0", (oid,)).fetchone()
        if not r or not pode_ver(u, r):
            raise HTTPException(404, "Orçamento não encontrado")
        out = linha_orc(r, nomes_vendedores(c))
        out["dados"] = json.loads(r["dados"] or "{}")
        nomes = nomes_vendedores(c)
        out["eventos"] = [dict(e, quem=nomes.get(e["uid"], "Cliente")) for e in
                          c.execute("SELECT * FROM eventos WHERE orc_id=? ORDER BY id DESC LIMIT 100", (oid,))]
        return out


@app.put("/api/orcamentos/{oid}")
async def orc_editar(oid: int, request: Request, u=Depends(usuario_atual)):
    b = await request.json()
    with _trava, db() as c:
        r = c.execute("SELECT * FROM orcamentos WHERE id=? AND apagado=0", (oid,)).fetchone()
        if not r or not pode_ver(u, r):
            raise HTTPException(404, "Orçamento não encontrado")
        gravar_orc(c, oid, b.get("dados") or {}, u)
        _apagar_pdf(r["token"])
        r = c.execute("SELECT * FROM orcamentos WHERE id=?", (oid,)).fetchone()
        return linha_orc(r, nomes_vendedores(c))


@app.put("/api/orcamentos/{oid}/status")
async def orc_status(oid: int, request: Request, u=Depends(usuario_atual)):
    b = await request.json()
    st = b.get("status")
    if st not in STATUS:
        raise HTTPException(400, "Status inválido")
    with db() as c:
        r = c.execute("SELECT * FROM orcamentos WHERE id=? AND apagado=0", (oid,)).fetchone()
        if not r or not pode_ver(u, r):
            raise HTTPException(404, "Orçamento não encontrado")
        c.execute("UPDATE orcamentos SET status=?, atualizado=?, fechado_em=?, motivo_perda=? WHERE id=?",
                  (st, agora(), agora() if st == "fechado" else r["fechado_em"], b.get("motivo") or r["motivo_perda"] or "", oid))
        evento(c, oid, u["id"], "status", f"Status: {st}" + (f" · {b['motivo']}" if b.get("motivo") else ""))
    return {"ok": True}


@app.post("/api/orcamentos/{oid}/nota")
async def orc_nota(oid: int, request: Request, u=Depends(usuario_atual)):
    b = await request.json()
    with db() as c:
        r = c.execute("SELECT * FROM orcamentos WHERE id=? AND apagado=0", (oid,)).fetchone()
        if not r or not pode_ver(u, r):
            raise HTTPException(404, "Orçamento não encontrado")
        evento(c, oid, u["id"], "nota", (b.get("texto") or "")[:2000])
        if b.get("proximo_contato") is not None:
            c.execute("UPDATE orcamentos SET proximo_contato=? WHERE id=?", (b["proximo_contato"], oid))
    return {"ok": True}


@app.post("/api/orcamentos/{oid}/duplicar")
async def orc_duplicar(oid: int, u=Depends(usuario_atual)):
    with _trava, db() as c:
        r = c.execute("SELECT * FROM orcamentos WHERE id=? AND apagado=0", (oid,)).fetchone()
        if not r or not pode_ver(u, r):
            raise HTTPException(404, "Orçamento não encontrado")
        dados = json.loads(r["dados"] or "{}")
        dados["status"] = "rascunho"
        novo = gravar_orc(c, None, dados, u, novo=True)
        evento(c, novo, u["id"], "duplicado", f"Cópia do {r['num']}")
        return linha_orc(c.execute("SELECT * FROM orcamentos WHERE id=?", (novo,)).fetchone(), nomes_vendedores(c))


@app.delete("/api/orcamentos/{oid}")
async def orc_apagar(oid: int, u=Depends(usuario_atual)):
    with db() as c:
        r = c.execute("SELECT * FROM orcamentos WHERE id=? AND apagado=0", (oid,)).fetchone()
        if not r or not pode_ver(u, r):
            raise HTTPException(404, "Orçamento não encontrado")
        c.execute("UPDATE orcamentos SET apagado=1, atualizado=? WHERE id=?", (agora(), oid))
        evento(c, oid, u["id"], "apagado", "")
    return {"ok": True}


def _pdf_caminho(token):
    return os.path.join(DADOS, "pdf", f"{token}.pdf")


def _apagar_pdf(token):
    try:
        os.remove(_pdf_caminho(token))
    except OSError:
        pass


def _html_orc(r, c):
    vend = c.execute("SELECT nome,telefone FROM usuarios WHERE id=?", (r["vendedor_id"],)).fetchone()
    data = dt.datetime.strptime(r["criado"], "%Y-%m-%d %H:%M:%S").date()
    html, _ = motor.montar_html(json.loads(r["dados"] or "{}"), ler_config(), vendedor=dict(vend) if vend else None,
                                num=r["num"], data=data, fator=fator_de(c, r["vendedor_id"]))
    return html


async def _pdf_orc(r):
    caminho = _pdf_caminho(r["token"])
    if os.path.exists(caminho) and os.path.getmtime(caminho) > time.time() - 7 * 86400:
        return caminho
    with db() as c:
        html = _html_orc(r, c)
    dados = await IMP.pdf(html)
    with open(caminho, "wb") as f:
        f.write(dados)
    return caminho


def _nome_pdf(r):
    nome = "".join(ch for ch in (r["cliente_nome"] or "Cliente") if ch.isalnum() or ch in " -").strip()[:60]
    return f"Proposta MS Energy - {nome} - {r['num']}.pdf"


@app.get("/api/orcamentos/{oid}/html", response_class=HTMLResponse)
async def orc_html(oid: int, u=Depends(usuario_atual)):
    with db() as c:
        r = c.execute("SELECT * FROM orcamentos WHERE id=? AND apagado=0", (oid,)).fetchone()
        if not r or not pode_ver(u, r):
            raise HTTPException(404, "Orçamento não encontrado")
        return HTMLResponse(_html_orc(r, c))


@app.get("/api/orcamentos/{oid}/pdf")
async def orc_pdf(oid: int, u=Depends(usuario_atual)):
    with db() as c:
        r = c.execute("SELECT * FROM orcamentos WHERE id=? AND apagado=0", (oid,)).fetchone()
    if not r or not pode_ver(u, r):
        raise HTTPException(404, "Orçamento não encontrado")
    caminho = await _pdf_orc(r)
    with db() as c:
        evento(c, oid, u["id"], "pdf", "PDF baixado")
    return FileResponse(caminho, media_type="application/pdf", filename=_nome_pdf(r))


@app.get("/api/exportar.csv")
async def exportar(u=Depends(usuario_atual)):
    with db() as c:
        nomes = nomes_vendedores(c)
        sql = "SELECT * FROM orcamentos WHERE apagado=0" + ("" if u["papel"] == "admin" else " AND vendedor_id=?")
        linhas = c.execute(sql + " ORDER BY id DESC", () if u["papel"] == "admin" else (u["id"],)).fetchall()
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Número", "Criado", "Vendedor", "Cliente", "CPF/CNPJ", "Telefone", "Cidade", "Tipo", "Consumo kWh", "kWp",
                "Valor (R$)", "Maior opção (R$)", "Status", "Visualizações", "Link"])
    for r in linhas:
        w.writerow([r["num"], r["criado"], nomes.get(r["vendedor_id"], ""), r["cliente_nome"], r["cliente_doc"], r["cliente_tel"],
                    r["cliente_cidade"], r["tipo"], r["consumo"], str(r["kwp"]).replace(".", ","), motor.brl(r["valor"]),
                    motor.brl(r["valor_max"] or r["valor"]), r["status"], r["visualizacoes"], f"{URL_PUBLICA}/p/{r['token']}"])
    dados = "﻿" + buf.getvalue()
    return StreamingResponse(iter([dados]), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="orcamentos_{dt.date.today():%Y%m%d}.csv"'})


# ============================================================================ painel (métricas)
@app.get("/api/painel")
async def painel(request: Request, u=Depends(usuario_atual)):
    dias = int(request.query_params.get("dias") or 30)
    desde = (dt.date.today() - dt.timedelta(days=dias - 1)).isoformat()
    filtro, par = ("", []) if u["papel"] == "admin" else (" AND vendedor_id=?", [u["id"]])
    with db() as c:
        base = f"FROM orcamentos WHERE apagado=0 AND substr(criado,1,10)>=?{filtro}"
        p = [desde] + par
        tot = dict(c.execute(f"SELECT count(*) n, coalesce(sum(valor),0) soma, coalesce(avg(valor),0) media, coalesce(sum(kwp),0) kwp,"
                             f" coalesce(sum(CASE WHEN status='fechado' THEN valor END),0) fechado,"
                             f" coalesce(sum(CASE WHEN status='fechado' THEN 1 END),0) nf,"
                             f" coalesce(sum(CASE WHEN status='perdido' THEN 1 END),0) np,"
                             f" coalesce(sum(visualizacoes),0) views {base}", p).fetchone())
        por_status = {r["status"]: {"n": r["n"], "valor": r["v"]} for r in
                      c.execute(f"SELECT status, count(*) n, coalesce(sum(valor),0) v {base} GROUP BY status", p)}
        por_dia = {r["d"]: {"n": r["n"], "valor": r["v"]} for r in
                   c.execute(f"SELECT substr(criado,1,10) d, count(*) n, coalesce(sum(valor),0) v {base} GROUP BY d", p)}
        serie = []
        for i in range(dias):
            dia = (dt.date.today() - dt.timedelta(days=dias - 1 - i)).isoformat()
            serie.append({"dia": dia, **por_dia.get(dia, {"n": 0, "valor": 0})})
        nomes = nomes_vendedores(c)
        ranking = [dict(r, nome=nomes.get(r["vendedor_id"], "?")) for r in c.execute(
            f"SELECT vendedor_id, count(*) n, coalesce(sum(valor),0) v, coalesce(sum(CASE WHEN status='fechado' THEN valor END),0) f {base}"
            " GROUP BY vendedor_id ORDER BY f DESC, v DESC", p)]
        por_tipo = {r["tipo"]: r["n"] for r in c.execute(f"SELECT tipo, count(*) n {base} GROUP BY tipo", p)}
        faixas = {r["faixa"]: r["n"] for r in c.execute(
            f"SELECT CASE WHEN consumo<400 THEN 'até 400' WHEN consumo<700 THEN '400–700' WHEN consumo<1000 THEN '700–1.000'"
            f" WHEN consumo<2000 THEN '1.000–2.000' ELSE '2.000+' END faixa, count(*) n {base} GROUP BY faixa", p)}
        recentes = [linha_orc(r, nomes) for r in c.execute(
            f"SELECT * FROM orcamentos WHERE apagado=0{filtro} ORDER BY id DESC LIMIT 8", par)]
        hoje = dt.date.today().isoformat()
        retornos = [linha_orc(r, nomes) for r in c.execute(
            f"SELECT * FROM orcamentos WHERE apagado=0 AND proximo_contato<>'' AND proximo_contato<=? AND status NOT IN ('fechado','perdido'){filtro}"
            " ORDER BY proximo_contato LIMIT 10", [hoje] + par)]
        vistos = [linha_orc(r, nomes) for r in c.execute(
            f"SELECT * FROM orcamentos WHERE apagado=0 AND ultima_visualizacao IS NOT NULL{filtro} ORDER BY ultima_visualizacao DESC LIMIT 6", par)]
        meta = None
        if u["papel"] != "admin" and u.get("meta"):
            mes = dt.date.today().strftime("%Y-%m")
            fm = c.execute("SELECT coalesce(sum(valor),0) f FROM orcamentos WHERE apagado=0 AND status='fechado' AND vendedor_id=? AND substr(fechado_em,1,7)=?",
                           (u["id"], mes)).fetchone()["f"]
            meta = {"meta": u["meta"], "feito": fm, "comissao_pct": u.get("comissao_pct") or 0}
    conv = (tot["nf"] / (tot["nf"] + tot["np"]) * 100) if (tot["nf"] + tot["np"]) else 0
    return {"totais": tot, "conversao": round(conv, 1), "por_status": por_status, "serie": serie, "ranking": ranking,
            "por_tipo": por_tipo, "faixas": faixas, "recentes": recentes, "retornos": retornos, "vistos": vistos, "meta": meta}


@app.get("/api/clientes")
async def clientes(u=Depends(usuario_atual)):
    filtro, par = ("", []) if u["papel"] == "admin" else (" AND vendedor_id=?", [u["id"]])
    with db() as c:
        nomes = nomes_vendedores(c)
        linhas = c.execute(
            f"SELECT lower(trim(cliente_nome)) k, max(cliente_nome) nome, max(cliente_doc) doc, max(cliente_tel) tel, max(cliente_cidade) cidade,"
            f" count(*) n, max(valor) maior, max(criado) ultimo, group_concat(status) sts, max(vendedor_id) vid"
            f" FROM orcamentos WHERE apagado=0 AND cliente_nome<>''{filtro} GROUP BY k ORDER BY ultimo DESC", par).fetchall()
    out = []
    for r in linhas:
        sts = (r["sts"] or "").split(",")
        out.append({"nome": r["nome"], "doc": r["doc"], "tel": r["tel"], "cidade": r["cidade"], "n": r["n"], "maior": r["maior"],
                    "ultimo": r["ultimo"], "fechado": "fechado" in sts, "vendedor": nomes.get(r["vid"], "")})
    return out


# ============================================================================ página pública do cliente
PAGINA_PUBLICA = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Proposta {num} – MS Energy</title>
<meta property="og:title" content="Proposta de energia solar – MS Energy"><meta property="og:description" content="{desc}">
<style>
body{{margin:0;background:#0b0f0d;font-family:Inter,Segoe UI,Arial,sans-serif}}
.barra{{position:sticky;top:0;z-index:5;display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;
 padding:12px 16px;background:rgba(8,12,10,.92);backdrop-filter:blur(10px);border-bottom:1px solid rgba(34,197,94,.25);color:#e5e7eb}}
.barra b{{color:#fff}} .barra small{{color:#9ca3af;display:block}}
.bt{{display:inline-flex;align-items:center;gap:8px;padding:10px 16px;border-radius:12px;font-weight:700;text-decoration:none;font-size:14px}}
.pdf{{background:#22c55e;color:#04130a}} .wa{{background:#25d366;color:#04130a}} .bts{{display:flex;gap:8px;flex-wrap:wrap}}
iframe{{width:100%;border:0;display:block;height:calc(100vh - 66px)}}
@media(max-width:820px){{iframe{{height:calc(100vh - 110px)}}}}
</style></head><body>
<div class="barra"><div><b>Proposta {num} · MS Energy</b><small>{cliente}{valor}</small></div>
<div class="bts"><a class="bt pdf" href="/p/{token}/pdf">⬇ Baixar PDF</a>{wa}</div></div>
<iframe src="/p/{token}/html" title="Proposta"></iframe></body></html>"""


def _orc_por_token(token):
    with db() as c:
        return c.execute("SELECT * FROM orcamentos WHERE token=? AND apagado=0", (token,)).fetchone()


def _registrar_visita(request, r):
    if request.cookies.get(COOKIE):
        return  # o próprio vendedor/admin abrindo não conta
    with db() as c:
        c.execute("UPDATE orcamentos SET visualizacoes=visualizacoes+1, ultima_visualizacao=? WHERE id=?", (agora(), r["id"]))
        if r["status"] == "rascunho":
            c.execute("UPDATE orcamentos SET status='enviado' WHERE id=?", (r["id"],))
        evento(c, r["id"], 0, "visualizado", "Cliente abriu a proposta")


@app.get("/p/{token}", response_class=HTMLResponse)
async def publica(token: str, request: Request):
    r = _orc_por_token(token)
    if not r:
        return HTMLResponse("<h2 style='font-family:sans-serif'>Proposta não encontrada.</h2>", 404)
    _registrar_visita(request, r)
    with db() as c:
        v = c.execute("SELECT nome,telefone FROM usuarios WHERE id=?", (r["vendedor_id"],)).fetchone()
    tel = "".join(ch for ch in ((v["telefone"] if v else "") or ler_config()["empresa"]["telefone"]) if ch.isdigit())
    if tel and not tel.startswith("55"):
        tel = "55" + tel
    msg = f"Olá! Vi a proposta {r['num']} de energia solar e quero conversar."
    wa = f'<a class="bt wa" href="https://wa.me/{tel}?text={msg.replace(" ", "%20")}">💬 Falar no WhatsApp</a>' if tel else ""
    return HTMLResponse(PAGINA_PUBLICA.format(
        num=r["num"], token=token, wa=wa, cliente=motor.esc(r["cliente_nome"] or ""),
        valor=f" · R$ {motor.brl(r['valor'])}" if r["valor"] else "",
        desc=f"Sistema de {motor.kwp_txt(r['kwp'] or 0)} kWp para {int(r['consumo'] or 0)} kWh/mês"))


@app.get("/p/{token}/html", response_class=HTMLResponse)
async def publica_html(token: str):
    r = _orc_por_token(token)
    if not r:
        raise HTTPException(404)
    with db() as c:
        return HTMLResponse(_html_orc(r, c))


@app.get("/p/{token}/pdf")
async def publica_pdf(token: str):
    r = _orc_por_token(token)
    if not r:
        raise HTTPException(404)
    caminho = await _pdf_orc(r)
    return FileResponse(caminho, media_type="application/pdf", filename=_nome_pdf(r))


# ============================================================================ WhatsApp do vendedor (FluxIA + Hermes Call)
# O vendedor conecta o WhatsApp e liga/desliga o robô pela API de CLIENTE do FluxIA (login dele, guardado aqui).
# As conversas vêm direto do Hermes Call (mesma linha do FluxIA), com a chave que fica em dados/segredos.json.
import asyncio as _aio
import urllib.error
import urllib.request

WA_TOKENS = {}   # uid -> token do FluxIA
WA_SESSAO = {}   # nome do fluxo -> (session_id, quando)


def _segredos():
    try:
        with open(os.path.join(DADOS, "segredos.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _http(metodo, url, corpo=None, cab=None, tempo=40):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo, headers={"Content-Type": "application/json", **(cab or {})})
    try:
        with urllib.request.urlopen(req, timeout=tempo) as r:
            t = r.read().decode() or "{}"
            return r.status, json.loads(t) if t.strip()[:1] in "[{" else {"texto": t}
    except urllib.error.HTTPError as e:
        t = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(t)
        except ValueError:
            return e.code, {"detail": t[:300]}
    except Exception as e:  # noqa: BLE001
        return 599, {"detail": f"sem resposta ({type(e).__name__})"}


async def http(*a, **k):
    return await _aio.to_thread(_http, *a, **k)


def _dono_wa(u, request):
    """Admin pode ver o WhatsApp de um vendedor (?vendedor=ID); vendedor só o dele."""
    vid = request.query_params.get("vendedor") if u["papel"] == "admin" else None
    with db() as c:
        r = c.execute("SELECT * FROM usuarios WHERE id=?", (int(vid) if vid else u["id"],)).fetchone()
    if not r or not r["fluxia_login"]:
        raise HTTPException(404, "WhatsApp ainda não liberado para este usuário. Peça ao administrador.")
    return dict(r)


async def fluxia(dono, metodo, caminho, corpo=None, tempo=40):
    seg = _segredos()
    base = (seg.get("fluxia_url") or "").rstrip("/")
    if not base:
        raise HTTPException(503, "Integração do WhatsApp não configurada")
    for tentativa in (1, 2):
        tok = WA_TOKENS.get(dono["id"])
        if not tok:
            st, j = await http("POST", base + "/api/auth/login", {"email": dono["fluxia_login"], "password": dono["fluxia_senha"]}, tempo=20)
            if st != 200:
                raise HTTPException(502, "Não consegui entrar no sistema do WhatsApp (login do FluxIA). Fale com o administrador.")
            tok = WA_TOKENS[dono["id"]] = j["token"]
        st, j = await http(metodo, base + caminho, corpo, {"Authorization": "Bearer " + tok}, tempo=tempo)
        if st == 401 and tentativa == 1:
            WA_TOKENS.pop(dono["id"], None)
            continue
        if st >= 400:
            raise HTTPException(st if st < 599 else 502, (j or {}).get("detail") or "Serviço do WhatsApp indisponível. Tente de novo.")
        return j


async def fluxo_do(dono):
    fl = await fluxia(dono, "GET", "/api/client/flows")
    if not fl:
        raise HTTPException(404, "Nenhum robô de WhatsApp ligado a esta conta.")
    return fl[0]


async def hermes(metodo, caminho, corpo=None):
    seg = _segredos()
    st, j = await http(metodo, seg["hermes_url"].rstrip("/") + caminho, corpo, {"X-API-Key": seg["hermes_key"]})
    if st >= 400:
        raise HTTPException(502, (j or {}).get("error") or (j or {}).get("detail") or "Hermes indisponível")
    return j


async def sessao_hermes(nome_fluxo):
    agora_ = time.time()
    s0 = WA_SESSAO.get(nome_fluxo)
    if s0 and agora_ - s0[1] < 300:
        return s0[0]
    j = await hermes("GET", "/api/sessions")
    for sx in j.get("sessions", []):
        if sx.get("name") == f"FluxIA - {nome_fluxo}":
            WA_SESSAO[nome_fluxo] = (sx["id"], agora_)
            return sx["id"]
    raise HTTPException(404, "A linha do WhatsApp ainda não existe. Conecte o WhatsApp primeiro.")


@app.get("/api/wa/status")
async def wa_status(request: Request, u=Depends(usuario_atual)):
    dono = _dono_wa(u, request)
    f = await fluxo_do(dono)
    return {"fluxo_id": f["id"], "nome": f["name"], "robo_ligado": f["active"], "whatsapp": f["whatsapp"],
            "hoje": f.get("today", {}), "config": f.get("settings", {})}


@app.post("/api/wa/qr")
async def wa_qr(request: Request, u=Depends(usuario_atual)):
    dono = _dono_wa(u, request)
    f = await fluxo_do(dono)
    WA_SESSAO.pop(f["name"], None)
    return await fluxia(dono, "POST", f"/api/client/flows/{f['id']}/qr", {}, tempo=45)


@app.post("/api/wa/codigo")
async def wa_codigo(request: Request, u=Depends(usuario_atual)):
    dono = _dono_wa(u, request)
    b = await request.json()
    f = await fluxo_do(dono)
    WA_SESSAO.pop(f["name"], None)
    return await fluxia(dono, "POST", f"/api/client/flows/{f['id']}/pair", {"phone": b.get("telefone") or ""}, tempo=45)


@app.post("/api/wa/desconectar")
async def wa_desconectar(request: Request, u=Depends(usuario_atual)):
    dono = _dono_wa(u, request)
    f = await fluxo_do(dono)
    r = await fluxia(dono, "POST", f"/api/client/flows/{f['id']}/disconnect", {})
    print(f"[wa] {u['usuario']} desconectou o WhatsApp do fluxo {f['id']} ({f['name']})", flush=True)
    return r


@app.put("/api/wa/robo")
async def wa_robo(request: Request, u=Depends(usuario_atual)):
    """Liga/desliga o robô (fluxo do FluxIA). Corpo: {"ligado": true|false}."""
    dono = _dono_wa(u, request)
    b = await request.json()
    f = await fluxo_do(dono)
    if bool(b.get("ligado")) != bool(f["active"]):
        await fluxia(dono, "PUT", f"/api/client/flows/{f['id']}/toggle", {})
    return {"ok": True, "robo_ligado": bool(b.get("ligado"))}


@app.put("/api/wa/config")
async def wa_config(request: Request, u=Depends(usuario_atual)):
    dono = _dono_wa(u, request)
    b = await request.json()
    f = await fluxo_do(dono)
    return await fluxia(dono, "PUT", f"/api/client/flows/{f['id']}/settings", b)


def _num(jid):
    return str(jid or "").split("@")[0].split(":")[0]


@app.get("/api/wa/conversas")
async def wa_conversas(request: Request, u=Depends(usuario_atual)):
    dono = _dono_wa(u, request)
    f = await fluxo_do(dono)
    sid = await sessao_hermes(f["name"])
    chats = await hermes("GET", f"/api/sessions/{sid}/chats?limit=150")
    try:
        contatos = await fluxia(dono, "GET", f"/api/client/flows/{f['id']}/contacts")
    except HTTPException:
        contatos = []
    por_num = {_num(x.get("phone")): x for x in contatos or []}
    out = []
    for ch in chats if isinstance(chats, list) else chats.get("chats", []):
        jid = ch.get("id") or ch.get("chat")
        if not jid or jid == "status@broadcast" or jid.endswith("@newsletter"):
            continue
        ct = por_num.get(_num(jid), {})
        out.append({"jid": jid, "nome": ct.get("customer_name") or "", "numero": _num(jid) if jid.endswith("@s.whatsapp.net") else "",
                    "grupo": jid.endswith("@g.us"), "ultima": ch.get("lastMessage") or "", "tipo": ch.get("lastType") or "text",
                    "quando": ch.get("timestamp") or 0, "minha": bool(ch.get("lastFromMe")), "total": ch.get("count") or 0,
                    "conv_id": ct.get("id"), "ia_desligada": bool(ct.get("ai_off")), "pausada_ate": ct.get("paused_until") or ""})
    out.sort(key=lambda x: x["quando"], reverse=True)
    return out


@app.get("/api/wa/conversas/{jid}/mensagens")
async def wa_mensagens(jid: str, request: Request, u=Depends(usuario_atual)):
    dono = _dono_wa(u, request)
    f = await fluxo_do(dono)
    sid = await sessao_hermes(f["name"])
    lim = min(int(request.query_params.get("limite") or 80), 300)
    ms = await hermes("GET", f"/api/sessions/{sid}/chats/{jid}/messages?limit={lim}")
    ms = ms if isinstance(ms, list) else ms.get("messages", [])
    return [{"id": m.get("id"), "minha": bool(m.get("fromMe")), "quando": m.get("timestamp") or 0, "tipo": m.get("type") or "text",
             "texto": m.get("body") or m.get("caption") or ""} for m in sorted(ms, key=lambda m: m.get("timestamp") or 0)]


@app.post("/api/wa/conversas/{jid}/enviar")
async def wa_enviar(jid: str, request: Request, u=Depends(usuario_atual)):
    dono = _dono_wa(u, request)
    b = await request.json()
    texto = (b.get("texto") or "").strip()
    if not texto:
        raise HTTPException(400, "Escreva a mensagem")
    f = await fluxo_do(dono)
    sid = await sessao_hermes(f["name"])
    await hermes("POST", f"/api/sessions/{sid}/messages/text", {"to": jid, "text": texto[:4000]})
    return {"ok": True}


@app.put("/api/wa/conversas/{conv_id}/robo")
async def wa_robo_conversa(conv_id: int, request: Request, u=Depends(usuario_atual)):
    """Liga/desliga o robô só nesta conversa. Corpo: {"ligado": true|false}."""
    dono = _dono_wa(u, request)
    b = await request.json()
    f = await fluxo_do(dono)
    return await fluxia(dono, "POST", f"/api/client/flows/{f['id']}/conversations/{conv_id}/ai", {"on": bool(b.get("ligado"))})


# ============================================================================ estáticos / SPA
@app.get("/saude")
async def saude():
    return {"ok": True, "hora": agora()}


app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/{caminho:path}", response_class=HTMLResponse)
async def spa(caminho: str):
    # só a raiz e rotas sem ponto abrem o painel; /.env, /wp-..., /api/inexistente etc. = 404 (robôs de varredura)
    if "." in caminho or caminho.startswith(("api/", "wp", "p/")) or len(caminho) > 60:
        return HTMLResponse("Não encontrado", 404)
    return FileResponse(os.path.join(WEB, "index.html"), headers={"Cache-Control": "no-cache"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORTA", "8101")), proxy_headers=True,
                forwarded_allow_ips="*")
