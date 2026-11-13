"""
LiciBot-IA · database.py
SQLite (WAL) com as tabelas editais, itens_edital e relatorio_cnaes.
Cada função abre a própria conexão, então pode ser chamada de vários fios ao mesmo tempo.
"""

import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from config import CNAES_MEI, DB_PATH

# status do edital:
#   novo        -> passou no filtro, falta baixar itens e documentos
#   enriquecido -> itens e texto prontos, falta a IA
#   analisado   -> IA respondeu
#   sem_analise -> IA falhou LLM_MAX_TENTATIVAS vezes (não avisa; --reanalisar tenta de novo)
#   revogado    -> anulado/revogado/suspenso no PNCP
#   expirado    -> prazo passou antes de analisar
_SCHEMA = """
CREATE TABLE IF NOT EXISTS editais (
    numero_controle     TEXT PRIMARY KEY,
    cnpj_orgao          TEXT NOT NULL,
    razao_social        TEXT,
    poder_id            TEXT,
    esfera_id           TEXT,
    uf                  TEXT,
    municipio           TEXT,
    unidade             TEXT,
    ano_compra          INTEGER,
    sequencial_compra   INTEGER,
    modalidade_id       INTEGER,
    modalidade_nome     TEXT,
    modo_disputa        TEXT,
    srp                 INTEGER DEFAULT 0,
    objeto_compra       TEXT,
    info_complementar   TEXT,
    amparo_legal        TEXT,
    valor_estimado      REAL DEFAULT 0,
    data_abertura       TEXT,
    data_encerramento   TEXT,
    data_publicacao     TEXT,
    atualizado_pncp     TEXT,
    link_sistema        TEXT,
    link_pncp           TEXT,

    gaveta              TEXT,
    kw_match            TEXT,

    texto_docs          TEXT,
    docs_lidos          TEXT,
    exclusivo_me_epp    INTEGER DEFAULT 0,
    qtd_itens           INTEGER DEFAULT 0,

    carteira            TEXT,
    score_viabilidade   REAL DEFAULT 0,
    score_pagador       REAL DEFAULT 0,
    nota_final          REAL DEFAULT 0,
    entrega_remota      INTEGER,
    exige_presencial    INTEGER DEFAULT 0,
    aceita_pf           INTEGER,
    cnae_sugerido       TEXT,
    valor_lance         REAL DEFAULT 0,
    custo_estimado      REAL DEFAULT 0,
    liquido_mei         REAL,
    liquido_cpf         REAL,
    margem_estimada     REAL DEFAULT 0,
    resumo_ia           TEXT,
    exigencias          TEXT,
    riscos              TEXT,
    json_ia             TEXT,
    modelo_ia           TEXT,
    tokens_ia           INTEGER DEFAULT 0,

    status              TEXT DEFAULT 'novo',
    tentativas_ia       INTEGER DEFAULT 0,
    ultimo_erro         TEXT,
    notificado          INTEGER DEFAULT 0,
    resultado_coletado  INTEGER DEFAULT 0,
    criado_em           TEXT DEFAULT (datetime('now','localtime')),
    atualizado_em       TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_editais_status   ON editais(status);
CREATE INDEX IF NOT EXISTS idx_editais_carteira ON editais(carteira);
CREATE INDEX IF NOT EXISTS idx_editais_fim      ON editais(data_encerramento);

CREATE TABLE IF NOT EXISTS itens_edital (
    numero_controle     TEXT NOT NULL,
    numero_item         INTEGER NOT NULL,
    descricao           TEXT,
    material_ou_servico TEXT,
    valor_unitario      REAL DEFAULT 0,
    valor_total         REAL DEFAULT 0,
    quantidade          REAL DEFAULT 0,
    unidade             TEXT,
    tipo_beneficio      INTEGER,
    tipo_beneficio_nome TEXT,
    criterio_julgamento TEXT,
    orcamento_sigiloso  INTEGER DEFAULT 0,
    situacao            TEXT,
    -- resultado (preço vencedor), coletado depois que a licitação fecha
    valor_homologado    REAL,
    vencedor_porte      TEXT,
    vencedor_tipo       TEXT,
    PRIMARY KEY (numero_controle, numero_item)
);

CREATE TABLE IF NOT EXISTS relatorio_cnaes (
    cnae_codigo         TEXT PRIMARY KEY,
    cnae_descricao      TEXT,
    total_oportunidades INTEGER DEFAULT 0,
    valor_total         REAL DEFAULT 0,
    margem_total        REAL DEFAULT 0,
    nota_media          REAL DEFAULT 0,
    atualizado_em       TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS execucoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    inicio          TEXT DEFAULT (datetime('now','localtime')),
    fim             TEXT,
    lidos           INTEGER DEFAULT 0,
    filtrados       INTEGER DEFAULT 0,
    novos           INTEGER DEFAULT 0,
    analisados      INTEGER DEFAULT 0,
    falhas_ia       INTEGER DEFAULT 0,
    tokens          INTEGER DEFAULT 0,
    notificados     INTEGER DEFAULT 0,
    erro            TEXT
);
"""


@contextmanager
def conexao() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


_COLUNAS_NOVAS = {
    # decisão da dona no painel: participar | ignorar | NULL
    "decisao": "TEXT",
    "decisao_em": "TEXT",
    "anotacao": "TEXT",
    "lembrado": "INTEGER DEFAULT 0",   # lembrete de prazo já mandado
}


def init_db() -> None:
    with conexao() as c:
        c.executescript(_SCHEMA)
        existentes = {r["name"] for r in c.execute("PRAGMA table_info(editais)")}
        for col, tipo in _COLUNAS_NOVAS.items():
            if col not in existentes:
                c.execute(f"ALTER TABLE editais ADD COLUMN {col} {tipo}")
        if "leitura" not in {r["name"] for r in c.execute("PRAGMA table_info(execucoes)")}:
            c.execute("ALTER TABLE execucoes ADD COLUMN leitura TEXT")   # completa | incremental


# ── editais ──────────────────────────────────────────────────────────────────

def salvar_proposta(p: dict[str, Any]) -> str:
    """Insere ou atualiza o que veio da listagem. Devolve 'novo', 'alterado' ou 'igual'.
    'alterado' (o órgão mexeu no edital depois que já analisamos) volta o edital para baixar de novo."""
    with conexao() as c:
        atual = c.execute("SELECT atualizado_pncp, status, data_encerramento, notificado FROM editais "
                          "WHERE numero_controle=?",
                          (p["numero_controle"],)).fetchone()
        if atual is None:
            cols = ", ".join(p)
            c.execute(f"INSERT INTO editais ({cols}) VALUES ({', '.join('?' * len(p))})", list(p.values()))
            return "novo"
        if (p.get("atualizado_pncp") or "") > (atual["atualizado_pncp"] or "") and atual["status"] != "revogado":
            campos = {k: v for k, v in p.items() if k != "numero_controle"}
            # reanalisa; só avisa de novo se o órgão mudou o prazo (esclarecimento/anexo não gera aviso repetido)
            mudou_prazo = (p.get("data_encerramento") or "") != (atual["data_encerramento"] or "")
            campos.update(status="novo", tentativas_ia=0, notificado=0 if mudou_prazo else atual["notificado"])
            sets = ", ".join(f"{k}=?" for k in campos)
            c.execute(f"UPDATE editais SET {sets}, atualizado_em=datetime('now','localtime') WHERE numero_controle=?",
                      [*campos.values(), p["numero_controle"]])
            return "alterado"
        return "igual"


def marcar_revogado(numero_controle: str, motivo: str) -> bool:
    with conexao() as c:
        return c.execute("UPDATE editais SET status='revogado', ultimo_erro=?, atualizado_em=datetime('now','localtime') "
                         "WHERE numero_controle=? AND status IN ('novo','enriquecido','analisado','sem_analise')",
                         (motivo, numero_controle)).rowcount > 0


def atualizar_edital(numero_controle: str, campos: dict[str, Any]) -> None:
    sets = ", ".join(f"{k}=?" for k in campos)
    with conexao() as c:
        c.execute(f"UPDATE editais SET {sets}, atualizado_em=datetime('now','localtime') WHERE numero_controle=?",
                  [*campos.values(), numero_controle])


def listar_por_status(status: str, limite: int = 10_000) -> list[dict[str, Any]]:
    """Abertos primeiro os que fecham antes (prazo é o que manda)."""
    with conexao() as c:
        rows = c.execute(
            "SELECT * FROM editais WHERE status=? AND data_encerramento > datetime('now','localtime') "
            "ORDER BY data_encerramento LIMIT ?", (status, limite)).fetchall()
    return [dict(r) for r in rows]


def expirar_vencidos() -> int:
    with conexao() as c:
        cur = c.execute("UPDATE editais SET status='expirado', atualizado_em=datetime('now','localtime') "
                        "WHERE status IN ('novo','enriquecido') AND data_encerramento <= datetime('now','localtime')")
        return cur.rowcount


def para_notificar(nota_min: float) -> list[dict[str, Any]]:
    with conexao() as c:
        rows = c.execute(
            "SELECT * FROM editais WHERE status='analisado' AND notificado=0 AND carteira!='DESCARTADO' "
            "AND coalesce(decisao,'')!='ignorar' "
            "AND nota_final>=? AND data_encerramento > datetime('now','localtime') "
            "ORDER BY nota_final DESC", (nota_min,)).fetchall()
    return [dict(r) for r in rows]


def marcar_notificados(numeros: list[str], valor: int = 1) -> None:
    """valor 1 = avisado; 2 = ficou fora dos filtros de aviso (não reavalia toda varredura)."""
    with conexao() as c:
        c.executemany("UPDATE editais SET notificado=? WHERE numero_controle=?", [(valor, n) for n in numeros])


def reabrir_fora_dos_filtros() -> int:
    """Quando a dona muda os filtros no painel, o que ficou de fora volta a ser avaliado."""
    with conexao() as c:
        return c.execute("UPDATE editais SET notificado=0 WHERE notificado=2").rowcount


def lembretes_prazo() -> list[dict[str, Any]]:
    with conexao() as c:
        rows = c.execute(
            "SELECT * FROM editais WHERE decisao='participar' AND coalesce(lembrado,0)=0 "
            "AND data_encerramento > datetime('now','localtime') "
            "AND data_encerramento <= datetime('now','localtime','+24 hours') ORDER BY data_encerramento").fetchall()
    return [dict(r) for r in rows]


def marcar_lembrados(numeros: list[str]) -> None:
    with conexao() as c:
        c.executemany("UPDATE editais SET lembrado=1 WHERE numero_controle=?", [(n,) for n in numeros])


def abertas_analisadas() -> list[dict[str, Any]]:
    with conexao() as c:
        rows = c.execute(
            "SELECT numero_controle, carteira, gaveta, uf, nota_final, margem_estimada, custo_estimado, "
            "valor_estimado, objeto_compra, data_encerramento, decisao FROM editais WHERE status='analisado' "
            "AND carteira!='DESCARTADO' AND coalesce(decisao,'')!='ignorar' "
            "AND data_encerramento > datetime('now','localtime')").fetchall()
    return [dict(r) for r in rows]


def resetar_sem_analise() -> int:
    with conexao() as c:
        return c.execute("UPDATE editais SET status='enriquecido', tentativas_ia=0 "
                         "WHERE status='sem_analise'").rowcount


def buscar(numero_controle: str) -> dict[str, Any] | None:
    with conexao() as c:
        r = c.execute("SELECT * FROM editais WHERE numero_controle=?", (numero_controle,)).fetchone()
    return dict(r) if r else None


# ── itens ────────────────────────────────────────────────────────────────────

def salvar_itens(numero_controle: str, itens: list[dict[str, Any]]) -> None:
    with conexao() as c:
        c.execute("DELETE FROM itens_edital WHERE numero_controle=?", (numero_controle,))
        for it in itens:
            row = {"numero_controle": numero_controle, **it}
            c.execute(f"INSERT OR REPLACE INTO itens_edital ({', '.join(row)}) VALUES ({', '.join('?' * len(row))})",
                      list(row.values()))


def itens_de(numero_controle: str) -> list[dict[str, Any]]:
    with conexao() as c:
        rows = c.execute("SELECT * FROM itens_edital WHERE numero_controle=? ORDER BY numero_item",
                         (numero_controle,)).fetchall()
    return [dict(r) for r in rows]


def salvar_resultado_item(numero_controle: str, numero_item: int, valor: float, porte: str, tipo: str) -> None:
    with conexao() as c:
        c.execute("UPDATE itens_edital SET valor_homologado=?, vencedor_porte=?, vencedor_tipo=? "
                  "WHERE numero_controle=? AND numero_item=?", (valor, porte, tipo, numero_controle, numero_item))


def pendentes_resultado(dias_apos: int, limite: int = 200) -> list[dict[str, Any]]:
    with conexao() as c:
        rows = c.execute(
            "SELECT * FROM editais WHERE resultado_coletado=0 AND gaveta IS NOT NULL AND status!='revogado' "
            "AND data_encerramento <= datetime('now','localtime', ?) ORDER BY data_encerramento LIMIT ?",
            (f"-{dias_apos} days", limite)).fetchall()
    return [dict(r) for r in rows]


def descontos_historicos() -> dict[str, dict[str, float]]:
    """Desconto real dado pelos vencedores (1 - homologado/estimado), por gaveta. Ignora valores absurdos."""
    with conexao() as c:
        rows = c.execute(
            "SELECT e.gaveta g, 1.0 - i.valor_homologado / i.valor_total d FROM itens_edital i "
            "JOIN editais e USING (numero_controle) WHERE i.valor_homologado > 0 AND i.valor_total > 0").fetchall()
    por: dict[str, list[float]] = {}
    for r in rows:
        if -0.2 <= r["d"] <= 0.9:
            por.setdefault(r["g"], []).append(r["d"])
    out = {}
    for g, v in por.items():
        v.sort()
        out[g] = {"mediana": v[len(v) // 2], "n": len(v)}
    return out


# ── relatórios ───────────────────────────────────────────────────────────────

def refazer_relatorio_cnaes() -> None:
    """Reconstrói do zero a partir dos editais analisados (não conta duas vezes quando reanalisa)."""
    with conexao() as c:
        c.execute("DELETE FROM relatorio_cnaes")
        rows = c.execute(
            "SELECT cnae_sugerido cnae, count(*) n, sum(valor_estimado) v, sum(margem_estimada) m, avg(nota_final) nf "
            "FROM editais WHERE status='analisado' AND carteira!='DESCARTADO' AND cnae_sugerido IS NOT NULL "
            "GROUP BY cnae_sugerido").fetchall()
        for r in rows:
            c.execute("INSERT INTO relatorio_cnaes (cnae_codigo, cnae_descricao, total_oportunidades, valor_total, "
                      "margem_total, nota_media) VALUES (?,?,?,?,?,?)",
                      (r["cnae"], CNAES_MEI.get(r["cnae"], "(fora da lista do MEI)"), r["n"], r["v"] or 0,
                       r["m"] or 0, round(r["nf"] or 0, 1)))


def ranking_cnaes() -> list[dict[str, Any]]:
    refazer_relatorio_cnaes()
    with conexao() as c:
        return [dict(r) for r in c.execute("SELECT * FROM relatorio_cnaes ORDER BY margem_total DESC")]


def estatisticas() -> dict[str, Any]:
    with conexao() as c:
        por_status = {r["status"]: r["n"] for r in c.execute("SELECT status, count(*) n FROM editais GROUP BY status")}
        por_carteira = [dict(r) for r in c.execute(
            "SELECT carteira, count(*) n, sum(valor_estimado) valor, sum(margem_estimada) margem, "
            "round(avg(nota_final),1) nota FROM editais WHERE status='analisado' GROUP BY carteira ORDER BY margem DESC")]
        por_gaveta = [dict(r) for r in c.execute(
            "SELECT gaveta, count(*) n FROM editais GROUP BY gaveta ORDER BY n DESC")]
        abertas = [dict(r) for r in c.execute(
            "SELECT numero_controle, carteira, nota_final, margem_estimada, valor_estimado, objeto_compra, "
            "data_encerramento, uf, municipio FROM editais WHERE status='analisado' AND carteira!='DESCARTADO' "
            "AND data_encerramento > datetime('now','localtime') ORDER BY nota_final DESC LIMIT 15")]
        ult = c.execute("SELECT * FROM execucoes ORDER BY id DESC LIMIT 5").fetchall()
        tokens = c.execute("SELECT coalesce(sum(tokens_ia),0) t FROM editais").fetchone()["t"]
    return {"por_status": por_status, "por_carteira": por_carteira, "por_gaveta": por_gaveta,
            "abertas": abertas, "execucoes": [dict(r) for r in ult], "tokens": tokens,
            "descontos": descontos_historicos()}


def ultima_leitura_ok(so_completa: bool = False) -> str | None:
    """Início da última varredura cuja leitura do PNCP terminou sem falha (incremental parte daí)."""
    with conexao() as c:
        r = c.execute("SELECT max(inicio) FROM execucoes WHERE leitura IS NOT NULL" +
                      (" AND leitura='completa'" if so_completa else "")).fetchone()
    return r[0] if r else None


def limpar_texto_encerrados(dias: int = 2) -> int:
    """O texto dos documentos é o que mais pesa no banco e não serve depois que a licitação fecha."""
    with conexao() as c:
        return c.execute("UPDATE editais SET texto_docs=NULL WHERE texto_docs IS NOT NULL "
                         "AND data_encerramento < datetime('now','localtime', ?)", (f"-{dias} days",)).rowcount


def abrir_execucao() -> int:
    with conexao() as c:
        return c.execute("INSERT INTO execucoes (inicio) VALUES (datetime('now','localtime'))").lastrowid


def fechar_execucao(eid: int, dados: dict[str, Any]) -> None:
    dados = {**dados, "fim": None}
    sets = ", ".join(f"{k}=?" if k != "fim" else "fim=datetime('now','localtime')" for k in dados)
    vals = [v for k, v in dados.items() if k != "fim"]
    with conexao() as c:
        c.execute(f"UPDATE execucoes SET {sets} WHERE id=?", [*vals, eid])


def exportar_json(numero_controle: str) -> str:
    e = buscar(numero_controle)
    if not e:
        return "{}"
    e["itens"] = itens_de(numero_controle)
    e.pop("texto_docs", None)
    return json.dumps(e, ensure_ascii=False, indent=2, default=str)
