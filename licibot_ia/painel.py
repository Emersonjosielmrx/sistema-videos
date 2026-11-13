"""
LiciBot-IA · painel.py — painel de controle (servidor HTTP do Python, sem dependências).

Escuta só em endereços internos (127.0.0.1 e a ponte do Docker 172.18.0.1); quem publica com HTTPS é o
Traefik, por um nginx no Swarm (ver painel_stack.yml). Acesso com a chave em painel.chave:
    https://licitacoes.157-173-207-22.sslip.io/?k=<CHAVE>
A chave vira cookie na 1ª visita, e depois a URL limpa funciona.

Rotas (todas exigem a chave):
  GET  /                      página
  GET  /api/resumo            números do topo + status do robô
  GET  /api/editais?aba=...   lista (oportunidades | fila | descartadas | todas | decididas)
  GET  /api/edital?n=...      detalhe completo (itens, documentos lidos, JSON da IA)
  GET  /api/execucoes | /api/cnaes | /api/log
  POST /api/varrer            {"sem_ia": bool}  -> dispara main.py --scan em segundo plano
  POST /api/parar             encerra a varredura em andamento
  POST /api/agendamento       {"ligado": bool}  -> liga/desliga o cron
  POST /api/ajustes           {"IA_MAX_POR_VARREDURA": 120, ...} -> grava ajustes.json
  POST /api/decisao           {"n": ..., "decisao": "participar"|"ignorar"|null, "anotacao": "..."}
  POST /api/reanalisar        {"n": ...} -> volta o edital para a fila da IA
  POST /api/avisar            dispara o aviso das oportunidades pendentes
"""

import csv
import hmac
import io
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import config  # noqa: E402
import database as db  # noqa: E402

CHAVE_ARQ = BASE / "painel.chave"
if not CHAVE_ARQ.exists():
    CHAVE_ARQ.write_text(secrets.token_urlsafe(24))
    os.chmod(CHAVE_ARQ, 0o600)
CHAVE = CHAVE_ARQ.read_text().strip()      # código longo: vai no cookie da sessão e no link ?k=
# senha da tela de login (a dona escolhe; 11/11: "põe só 1234"). Separada da CHAVE para o cookie continuar
# sendo um código que ninguém adivinha, mesmo com senha simples.
SENHA_ARQ = BASE / "painel.senha"
SENHA = SENHA_ARQ.read_text().strip() if SENHA_ARQ.exists() else CHAVE
CRON_ARQ = Path("/etc/cron.d/licibot")
CRON_MODELO = BASE / "licibot.cron"
SAIDA_MANUAL = BASE / "painel_varredura.out"
HTML = (BASE / "painel.html").read_text(encoding="utf-8")
ENDERECOS = os.getenv("PAINEL_ENDERECOS", "127.0.0.1,172.18.0.1").split(",")
PORTA = int(os.getenv("PAINEL_PORTA", "20180"))

# ajustes que o painel pode mudar (nome -> (tipo, mínimo, máximo))
AJUSTAVEIS = {
    "IA_MAX_POR_VARREDURA": (int, 0, 2000),
    "NOTIFICAR_SCORE_MIN": (int, 0, 100),
    "NOTIFICAR_MAX": (int, 1, 50),
    "LLM_PARALELO": (int, 1, 6),
    "LLM_EFFORT": (str, None, None),
    "IA_TEXTO_MAX_CHARS": (int, 10_000, 200_000),
    "DOCS_ATE_VALOR": (int, 0, 50_000_000),
    "DIAS_A_FRENTE": (int, 5, 120),
    "MEI_FATURADO_ANO": (float, 0, 1_000_000),
    "COMISSAO_AMIGO_SOLAR": (float, 0, 1),
    "LLM_CADEIA": (list, None, None),
    "LLM_PROMPT": (str, None, None),
}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
# modelos que o painel oferece (nome no OmniRoute -> rótulo). Só entram os testados no LiciBot.
def _modelos_gratis() -> dict:
    from ai_analyzer import MODELOS_GRATIS
    return {k: v["nome"] for k, v in MODELOS_GRATIS.items()}
PROMPTS = {"v1": "v1 · original", "v2": "v2 · regras de julgamento explícitas"}
AVISOS_TIPOS = {  # chave -> tipo esperado
    "tg_token": str, "tg_chat": str, "oportunidade": bool, "lembrete_prazo": bool, "erro": bool,
    "sem_credito": bool, "resumo_diario": bool, "hora_resumo": int, "silencio_de": int, "silencio_ate": int,
    "carteiras": list, "tipos": list, "ufs": list, "liquido_min": float, "invest_min": float, "invest_max": float,
    "valor_min": float, "valor_max": float,
}
UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
       "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]

_proc: subprocess.Popen | None = None
_trava = threading.Lock()
_TENTATIVAS: dict[str, list[float]] = {}   # IP -> horários de senha errada (5 em 10 min = espera)

LOGIN_HTML = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>LiciBot · Entrar</title>
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E%3Ctext y=%22.9em%22 font-size=%2290%22%3E%F0%9F%93%91%3C/text%3E%3C/svg%3E">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#0D1117;--verde:#10B981;--verde2:#34D399;--txt:#E5E7EB;--txt2:#94A3B8;--borda:rgba(148,163,184,.16)}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--txt);font:15px Inter,system-ui,sans-serif}
body{display:grid;place-items:center;padding:16px;
  background:radial-gradient(60% 50% at 20% 15%,rgba(16,185,129,.22),transparent 70%),radial-gradient(50% 40% at 85% 85%,rgba(56,189,248,.12),transparent 70%),var(--bg)}
.box{width:100%;max-width:380px;padding:30px 26px;border-radius:22px;background:rgba(17,24,39,.65);border:1px solid rgba(16,185,129,.35);
  backdrop-filter:blur(16px);box-shadow:0 20px 60px rgba(0,0,0,.5);animation:e .5s ease both}
.logo{width:52px;height:52px;border-radius:15px;display:grid;place-items:center;font-size:26px;margin:0 auto 14px;
  background:linear-gradient(135deg,var(--verde),#059669);box-shadow:0 0 30px rgba(16,185,129,.55)}
h1{margin:0;text-align:center;font-size:21px;font-weight:800}p{margin:6px 0 22px;text-align:center;color:var(--txt2);font-size:13.5px}
input{width:100%;padding:13px 14px;border-radius:12px;border:1px solid var(--borda);background:#0b1220;color:var(--txt);font:inherit;outline:none}
input:focus{border-color:var(--verde);box-shadow:0 0 0 3px rgba(16,185,129,.2)}
button{width:100%;margin-top:12px;padding:13px;border:0;border-radius:12px;font:inherit;font-weight:700;color:#fff;cursor:pointer;
  background:linear-gradient(135deg,var(--verde),#059669);box-shadow:0 8px 24px rgba(16,185,129,.35);transition:.18s}
button:hover{transform:translateY(-1px)}
.erro{margin:-8px 0 14px;padding:9px 12px;border-radius:10px;background:rgba(248,113,113,.12);color:#FCA5A5;font-size:13.5px;text-align:center}
@keyframes e{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
</style></head><body>
<form class="box" method="post" action="/entrar">
  <div class="logo">📑</div><h1>LiciBot</h1><p>Painel de licitações · entre com a senha</p>
  {{ERRO}}
  <input type="password" name="senha" placeholder="Senha" autocomplete="current-password" autofocus required>
  <button type="submit">Entrar</button>
</form></body></html>"""


# ═════════════════════════════════════════════════════════════════════════════
# dados
# ═════════════════════════════════════════════════════════════════════════════

def _rows(sql: str, args: tuple = ()) -> list[dict]:
    with db.conexao() as c:
        return [dict(r) for r in c.execute(sql, args)]


def _um(sql: str, args: tuple = ()):
    with db.conexao() as c:
        r = c.execute(sql, args).fetchone()
        return r[0] if r else None


def varredura_rodando() -> dict:
    """Varredura em andamento (pelo cron ou pelo painel): procura o processo."""
    try:
        out = subprocess.run(["pgrep", "-af", "main.py --scan"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        out = ""
    linhas = [l for l in out.splitlines() if "pgrep" not in l and "python" in l]
    return {"rodando": bool(linhas), "pids": [int(l.split()[0]) for l in linhas]}


def etapa_atual() -> str:
    """Última linha de etapa do log (Estágio N / fila da IA)."""
    try:
        with open(config.LOG_PATH, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 60_000))
            linhas = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return ""
    for l in reversed(linhas):
        if "▶" in l or "fila da IA" in l or "lidas," in l:
            return l.split(": ", 1)[-1].strip()
    return ""


def agendamento() -> dict:
    ligado = CRON_ARQ.exists()
    linha = ""
    fonte = CRON_ARQ if ligado else CRON_MODELO
    try:
        linha = next((l for l in fonte.read_text().splitlines() if l and not l.startswith("#")), "")
    except OSError:
        pass
    return {"ligado": ligado, "linha": linha}


def modo_tokens() -> dict:
    try:
        return json.loads(Path(config.MODO_TOKENS_ARQ).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def resumo() -> dict:
    por_status = {r["status"]: r["n"] for r in _rows("SELECT status, count(*) n FROM editais GROUP BY status")}
    abertas = "data_encerramento > datetime('now','localtime')"
    oport = _rows(f"SELECT count(*) n, coalesce(sum(margem_estimada),0) liq, coalesce(sum(valor_estimado),0) val "
                  f"FROM editais WHERE status='analisado' AND carteira!='DESCARTADO' AND {abertas} "
                  f"AND coalesce(decisao,'')!='ignorar'")[0]
    boas = _um(f"SELECT count(*) FROM editais WHERE status='analisado' AND carteira!='DESCARTADO' AND {abertas} "
               f"AND nota_final>=? AND coalesce(decisao,'')!='ignorar'", (config.NOTIFICAR_SCORE_MIN,))
    fecha_48h = _um(f"SELECT count(*) FROM editais WHERE status='analisado' AND carteira!='DESCARTADO' AND {abertas} "
                    "AND data_encerramento <= datetime('now','localtime','+48 hours') AND coalesce(decisao,'')!='ignorar'")
    participar = _um(f"SELECT count(*) FROM editais WHERE decisao='participar' AND {abertas}")
    por_carteira = _rows(f"SELECT carteira, count(*) n, coalesce(sum(margem_estimada),0) liq FROM editais "
                         f"WHERE status='analisado' AND {abertas} AND coalesce(decisao,'')!='ignorar' GROUP BY carteira")
    tokens_24h = _um("SELECT coalesce(sum(tokens_ia),0) FROM editais WHERE atualizado_em > datetime('now','localtime','-1 day')")
    tokens_total = _um("SELECT coalesce(sum(tokens_ia),0) FROM editais")
    ult = _rows("SELECT * FROM execucoes ORDER BY id DESC LIMIT 1")
    lidos = _rows("SELECT lidos, filtrados FROM execucoes WHERE lidos>0 ORDER BY id DESC LIMIT 1")
    aj = {k: getattr(config, k, None) for k in AJUSTAVEIS}
    aj.update({k: v for k, v in _ler_ajustes().items() if k in AJUSTAVEIS})
    return {
        "agora": time.strftime("%Y-%m-%d %H:%M:%S"),
        "por_status": por_status,
        "oportunidades": oport["n"], "liquido_total": oport["liq"], "valor_total": oport["val"],
        "boas": boas, "fecha_48h": fecha_48h, "participar": participar,
        "fila_ia": por_status.get("enriquecido", 0), "fila_docs": por_status.get("novo", 0),
        "por_carteira": por_carteira,
        "tokens_24h": tokens_24h, "tokens_total": tokens_total,
        "ultima": ult[0] if ult else None,
        "ultima_leitura": lidos[0] if lidos else None,
        "varredura": {**varredura_rodando(), "etapa": etapa_atual()},
        "agendamento": agendamento(),
        "ajustes": aj,
        "modo_tokens": modo_tokens(),
        "modelo": "cadeia-gratis",
        "modelo_nome": " → ".join(_modelos_gratis()[m] for m in __import__("ai_analyzer").cadeia_atual()) + " (grátis)",
        "cadeia": __import__("ai_analyzer").cadeia_atual(),
        "telegram": bool(config.avisos()["tg_token"] and config.avisos()["tg_chat"]),
        "webhook": bool(config.WEBHOOK_URL),
    }


_COLS_LISTA = ("numero_controle, status, carteira, gaveta, nota_final, score_viabilidade, score_pagador, "
               "valor_estimado, valor_lance, margem_estimada, liquido_mei, liquido_cpf, objeto_compra, razao_social, "
               "uf, municipio, poder_id, esfera_id, modalidade_nome, data_encerramento, data_publicacao, "
               "exclusivo_me_epp, entrega_remota, exige_presencial, aceita_pf, cnae_sugerido, qtd_itens, "
               "kw_match, link_pncp, link_sistema, resumo_ia, decisao, anotacao, notificado, tentativas_ia, "
               "ultimo_erro, tokens_ia, modelo_ia, srp, custo_estimado, length(texto_docs) tam_docs")


def editais(aba: str) -> list[dict]:
    abertas = "data_encerramento > datetime('now','localtime')"
    filtros = {
        "oportunidades": f"status='analisado' AND carteira!='DESCARTADO' AND {abertas} AND coalesce(decisao,'')!='ignorar'",
        "decididas": "decisao IS NOT NULL",
        "fila": f"status IN ('novo','enriquecido','sem_analise') AND {abertas}",
        "descartadas": "status='analisado' AND carteira='DESCARTADO'",
        "encerradas": "status IN ('expirado','revogado') OR (status='analisado' AND NOT " + abertas + ")",
        "todas": "1=1",
    }
    where = filtros.get(aba, filtros["oportunidades"])
    linhas = _rows(f"SELECT {_COLS_LISTA} FROM editais WHERE {where} ORDER BY nota_final DESC, data_encerramento")
    for l in linhas:
        l["tipo"] = config.GAVETA_TIPO.get(l["gaveta"], "servico")
    if aba == "fila":
        from ai_analyzer import pre_nota
        for l in linhas:
            l["pre_nota"] = round(pre_nota(l, tam_docs=l["tam_docs"] or 0), 1)
        linhas.sort(key=lambda l: (l["status"] != "enriquecido", -l["pre_nota"]))
    return linhas


def edital(n: str) -> dict | None:
    e = db.buscar(n)
    if not e:
        return None
    e["itens"] = db.itens_de(n)
    txt = e.pop("texto_docs", None) or ""
    e["texto_inicio"] = txt[:6000]
    e["tam_docs"] = len(txt)
    try:
        e["ia"] = json.loads(e.pop("json_ia") or "null")
    except ValueError:
        e["ia"] = None
    return e


def comparacoes() -> list[dict]:
    """Resumo de cada comparar_modelos.py rodado (para a aba Modelos)."""
    out = []
    for f in sorted(BASE.glob("comparacao_*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        ls = d.get("linhas") or []
        ok, total = len(ls), len(ls) + len(d.get("falhas") or [])
        med = lambda k: round(sum((l.get(k) or 0) for l in ls) / ok, 1) if ok else None
        cob = lambda k: (round(100 * sum(l[k] for l in ls if l.get(k) is not None) /
                               max(1, sum(1 for l in ls if l.get(k) is not None))) if ok else None)
        out.append({"arquivo": f.name, "modelo": d.get("modelo"), "nome": _modelos_gratis().get(d.get("modelo"), d.get("modelo")),
                    "prompt": f.stem.split("_")[-2] if f.stem.count("_") >= 3 else "v1",
                    "grupo": f.stem.split("_")[-1] if f.stem.count("_") >= 3 else "misto",
                    "respondeu": f"{ok}/{total}",
                    "mesma_carteira": round(100 * sum(l["mesma_carteira"] for l in ls) / ok) if ok else None,
                    "mesmo_lado": round(100 * sum(l["mesmo_lado"] for l in ls) / ok) if ok else None,
                    "cob_riscos": cob("cob_riscos") if ls and "cob_riscos" in ls[0] else None,
                    "cob_exig": cob("cob_exig") if ls and "cob_exig" in ls[0] else None,
                    "dif_viab": med("dif_viab") if ls and "dif_viab" in ls[0] else None,
                    "riscos": med("outro_n_riscos"), "riscos_opus": med("opus_n_riscos"),
                    "seg": med("outro_seg"), "tokens": med("outro_tokens"),
                    "em": time.strftime("%d/%m %H:%M", time.localtime(f.stat().st_mtime))})
    return sorted(out, key=lambda x: x["em"], reverse=True)


def ler_log(linhas: int = 300) -> list[str]:
    try:
        with open(config.LOG_PATH, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 200_000))
            return f.read().decode("utf-8", "replace").splitlines()[-linhas:]
    except OSError:
        return []


# ═════════════════════════════════════════════════════════════════════════════
# ações
# ═════════════════════════════════════════════════════════════════════════════

def _ler_ajustes() -> dict:
    try:
        return json.loads(config.AJUSTES_ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gravar_ajustes(novos: dict) -> dict:
    atuais = _ler_ajustes()
    for k, v in novos.items():
        if k not in AJUSTAVEIS:
            raise ValueError(f"ajuste desconhecido: {k}")
        tipo, mn, mx = AJUSTAVEIS[k]
        if tipo is list:
            v = [str(x) for x in (v or [])]
            if k == "LLM_CADEIA":
                livres = _modelos_gratis()
                if not v or not set(v) <= set(livres):
                    raise ValueError("a cadeia só aceita modelos grátis: " + ", ".join(livres))
            atuais[k] = v
            continue
        if tipo is str:
            v = str(v).strip()
            if k == "LLM_EFFORT" and v not in EFFORTS:
                raise ValueError(f"esforço inválido: {v}")
            pass
            if k == "LLM_PROMPT" and v not in PROMPTS:
                raise ValueError(f"prompt inválido: {v}")
        else:
            v = tipo(v)
            if not (mn <= v <= mx):
                raise ValueError(f"{k} fora do intervalo {mn}–{mx}")
        atuais[k] = v
    tmp = config.AJUSTES_ARQ.with_suffix(".tmp")
    tmp.write_text(json.dumps(atuais, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(config.AJUSTES_ARQ)
    return atuais


def _mascarar(token: str) -> str:
    return (token[:6] + "…" + token[-4:]) if len(token) > 12 else ("…" if token else "")


def ler_avisos() -> dict:
    cfg = config.avisos()
    return {**{k: cfg[k] for k in AVISOS_TIPOS}, "tg_token": _mascarar(cfg["tg_token"]),
            "tg_token_definido": bool(cfg["tg_token"]), "nota_min": cfg["nota_min"],
            "max_por_aviso": cfg["max_por_aviso"], "ufs_todas": UFS, "vizinhas": config.UFS_VIZINHAS}


def gravar_avisos(novos: dict) -> str:
    atuais = _ler_ajustes()
    av = dict(atuais.get("AVISOS") or {})
    for k, v in novos.items():
        if k not in AVISOS_TIPOS:
            raise ValueError(f"campo de aviso desconhecido: {k}")
        tipo = AVISOS_TIPOS[k]
        if k == "tg_token":
            v = str(v).strip()
            if "…" in v:          # é a versão mascarada que o painel mostrou: não muda
                continue
            if v and not re.fullmatch(r"\d{6,12}:[A-Za-z0-9_-]{30,50}", v):
                raise ValueError("token do bot com formato inválido (ex.: 123456789:AA...)")
        elif k == "tg_chat":
            v = str(v).strip()
            if v and not re.fullmatch(r"-?\d{5,16}|@[A-Za-z0-9_]{5,}", v):
                raise ValueError("chat inválido (número do chat ou @canal)")
        elif tipo is bool:
            v = bool(v)
        elif tipo is int:
            v = int(v)
            if k.startswith(("hora_", "silencio_")) and not 0 <= v <= 23:
                raise ValueError(f"{k}: hora entre 0 e 23")
        elif tipo is float:
            v = float(v or 0)
            if v < 0:
                raise ValueError(f"{k} não pode ser negativo")
        elif tipo is list:
            v = [str(x) for x in (v or [])]
            permitido = {"carteiras": {"MEI", "CPF", "AMIGO_SOLAR"}, "tipos": {"produto", "servico", "obra"},
                         "ufs": set(UFS)}[k]
            if not set(v) <= permitido:
                raise ValueError(f"{k}: valor inválido {set(v) - permitido}")
        av[k] = v
    if av.get("invest_max") and av.get("invest_min", 0) > av["invest_max"]:
        raise ValueError("investimento: o mínimo é maior que o máximo")
    if av.get("valor_max") and av.get("valor_min", 0) > av["valor_max"]:
        raise ValueError("valor: o mínimo é maior que o máximo")
    atuais["AVISOS"] = av
    tmp = config.AJUSTES_ARQ.with_suffix(".tmp")
    tmp.write_text(json.dumps(atuais, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(config.AJUSTES_ARQ)
    # filtro mudou: o que tinha ficado de fora volta a ser avaliado no próximo aviso
    reabertos = db.reabrir_fora_dos_filtros()
    return "avisos gravados" + (f"; {reabertos} licitação(ões) voltam a ser avaliadas" if reabertos else "")


def iniciar_varredura(sem_ia: bool) -> str:
    global _proc
    with _trava:
        if varredura_rodando()["rodando"]:
            return "já tem uma varredura rodando"
        cmd = [sys.executable, str(BASE / "main.py"), "--scan"] + (["--sem-ia"] if sem_ia else [])
        _proc = subprocess.Popen(["nice", "-n", "10", *cmd], cwd=BASE, stdout=open(SAIDA_MANUAL, "ab"),
                                 stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        return "varredura iniciada" + (" (sem IA)" if sem_ia else "")


def parar_varredura() -> str:
    pids = varredura_rodando()["pids"]
    for p in pids:
        try:
            os.kill(p, signal.SIGTERM)
        except OSError:
            pass
    if pids:
        with db.conexao() as c:
            c.execute("UPDATE execucoes SET fim=datetime('now','localtime'), erro='parada pelo painel' WHERE fim IS NULL")
    return f"{len(pids)} processo(s) parado(s)" if pids else "nada rodando"


def mudar_agendamento(ligado: bool) -> str:
    if ligado:
        CRON_ARQ.write_text(CRON_MODELO.read_text())
        os.chmod(CRON_ARQ, 0o644)
        return "agendamento ligado"
    if CRON_ARQ.exists():
        CRON_ARQ.unlink()
    return "agendamento desligado"


def decidir(n: str, decisao: str | None, anotacao: str | None) -> str:
    if decisao not in (None, "", "participar", "ignorar"):
        raise ValueError("decisão inválida")
    campos = {"decisao": decisao or None, "decisao_em": time.strftime("%Y-%m-%d %H:%M:%S") if decisao else None}
    if anotacao is not None:
        campos["anotacao"] = anotacao[:2000]
    db.atualizar_edital(n, campos)
    return "ok"


def reanalisar(n: str) -> str:
    e = db.buscar(n)
    if not e:
        raise ValueError("edital não existe")
    novo = "novo" if not e.get("texto_docs") and e["status"] in ("novo", "expirado") else "enriquecido"
    db.atualizar_edital(n, {"status": novo, "tentativas_ia": 0, "notificado": 0, "ultimo_erro": None})
    return f"voltou para a fila ({novo}); sai na próxima varredura"


def avisar_agora() -> str:
    import main
    return f"{main.avisar(forcar=True)} aviso(s) de oportunidade enviado(s)"


def csv_de(linhas: list[dict]) -> bytes:
    if not linhas:
        return b""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(linhas[0].keys()), delimiter=";", extrasaction="ignore")
    w.writeheader()
    w.writerows(linhas)
    return ("﻿" + buf.getvalue()).encode("utf-8")


# ═════════════════════════════════════════════════════════════════════════════
# HTTP
# ═════════════════════════════════════════════════════════════════════════════

class Handler(BaseHTTPRequestHandler):
    server_version = "LiciBot"

    def log_message(self, fmt, *args):  # sem log de cada pedido (a chave vai na URL na 1ª visita)
        pass

    def _autorizado(self, q: dict) -> bool:
        k = (q.get("k") or [""])[0]
        if k and hmac.compare_digest(k, CHAVE):
            return True
        c = SimpleCookie(self.headers.get("Cookie", ""))
        return "lb" in c and hmac.compare_digest(c["lb"].value, CHAVE)

    def _enviar(self, codigo: int, corpo, tipo="application/json; charset=utf-8", extra=None):
        if isinstance(corpo, (dict, list)):
            corpo = json.dumps(corpo, ensure_ascii=False, default=str).encode("utf-8")
        elif isinstance(corpo, str):
            corpo = corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 100_000:
            raise ValueError("corpo grande demais")
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def _ip(self) -> str:
        # atrás do Traefik o IP real vem no X-Forwarded-For (o 1º da lista)
        return (self.headers.get("X-Forwarded-For") or self.client_address[0]).split(",")[0].strip()

    def _cookie_ok(self) -> dict:
        return {"Set-Cookie": f"lb={CHAVE}; Path=/; Max-Age=31536000; HttpOnly; Secure; SameSite=Lax", "Location": "/"}

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/sair":
            return self._enviar(302, b"", "text/plain", {"Set-Cookie": "lb=; Path=/; Max-Age=0", "Location": "/"})
        if not self._autorizado(q):
            if u.path.startswith("/api/"):
                return self._enviar(401, {"erro": "faça login"})
            return self._enviar(200, LOGIN_HTML.replace("{{ERRO}}", ""), "text/html; charset=utf-8")
        try:
            if u.path == "/":
                if q.get("k"):  # grava o cookie e tira a chave da URL
                    return self._enviar(302, b"", "text/plain", self._cookie_ok())
                return self._enviar(200, HTML, "text/html; charset=utf-8")
            if u.path == "/api/resumo":
                return self._enviar(200, resumo())
            if u.path == "/api/editais":
                aba = (q.get("aba") or ["oportunidades"])[0]
                linhas = editais(aba)
                if (q.get("formato") or [""])[0] == "csv":
                    return self._enviar(200, csv_de(linhas), "text/csv; charset=utf-8",
                                        {"Content-Disposition": f'attachment; filename="licibot_{aba}.csv"'})
                return self._enviar(200, linhas)
            if u.path == "/api/edital":
                e = edital((q.get("n") or [""])[0])
                return self._enviar(200 if e else 404, e or {"erro": "não achei"})
            if u.path == "/api/execucoes":
                return self._enviar(200, _rows("SELECT * FROM execucoes ORDER BY id DESC LIMIT 200"))
            if u.path == "/api/cnaes":
                return self._enviar(200, db.ranking_cnaes())
            if u.path == "/api/log":
                return self._enviar(200, ler_log())
            if u.path == "/api/descontos":
                return self._enviar(200, db.descontos_historicos())
            if u.path == "/api/avisos":
                return self._enviar(200, ler_avisos())
            if u.path == "/api/opcoes":
                return self._enviar(200, {"modelos": _modelos_gratis(), "prompts": PROMPTS, "efforts": sorted(EFFORTS)})
            if u.path == "/api/comparacoes":
                return self._enviar(200, comparacoes())
            return self._enviar(404, {"erro": "rota não existe"})
        except Exception as err:  # o painel nunca derruba o servidor
            return self._enviar(500, {"erro": f"{type(err).__name__}: {err}"})

    def _login(self):
        ip = self._ip()
        agora = time.time()
        with _trava:
            erros = [t for t in _TENTATIVAS.get(ip, []) if agora - t < 600]
            _TENTATIVAS[ip] = erros
        if len(erros) >= 5:
            pag = LOGIN_HTML.replace("{{ERRO}}", '<div class="erro">Muitas tentativas. Espere 10 minutos.</div>')
            return self._enviar(429, pag, "text/html; charset=utf-8")
        n = int(self.headers.get("Content-Length") or 0)
        dados = parse_qs(self.rfile.read(min(n, 2000)).decode("utf-8", "replace")) if n else {}
        senha = (dados.get("senha") or [""])[0].strip()
        if senha and (hmac.compare_digest(senha, SENHA) or hmac.compare_digest(senha, CHAVE)):
            with _trava:
                _TENTATIVAS.pop(ip, None)
            return self._enviar(303, b"", "text/plain", self._cookie_ok())
        with _trava:
            _TENTATIVAS.setdefault(ip, []).append(agora)
        time.sleep(1)  # atrasa quem tenta adivinhar
        pag = LOGIN_HTML.replace("{{ERRO}}", '<div class="erro">Senha errada.</div>')
        return self._enviar(401, pag, "text/html; charset=utf-8")

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/entrar":
            return self._login()
        if not self._autorizado(parse_qs(u.query)):
            return self._enviar(401, {"erro": "faça login"})
        # proteção simples contra pedido vindo de outro site (o cookie é SameSite=Strict, isto é a 2ª camada)
        if self.headers.get("X-Painel") != "1":
            return self._enviar(403, {"erro": "pedido sem cabeçalho do painel"})
        try:
            d = self._corpo()
            if u.path == "/api/varrer":
                msg = iniciar_varredura(bool(d.get("sem_ia")))
            elif u.path == "/api/parar":
                msg = parar_varredura()
            elif u.path == "/api/agendamento":
                msg = mudar_agendamento(bool(d.get("ligado")))
            elif u.path == "/api/ajustes":
                gravar_ajustes(d)
                msg = "ajustes gravados; valem a partir da próxima varredura"
            elif u.path == "/api/decisao":
                msg = decidir(d["n"], d.get("decisao"), d.get("anotacao"))
            elif u.path == "/api/reanalisar":
                msg = reanalisar(d["n"])
            elif u.path == "/api/avisar":
                msg = avisar_agora()
            elif u.path == "/api/avisos":
                msg = gravar_avisos(d)
            elif u.path == "/api/simular":
                import simulador
                pm = simulador.Parametros()
                for k, v in d.items():
                    if not hasattr(pm, k):
                        raise ValueError(f"parâmetro desconhecido: {k}")
                    atual = getattr(pm, k)
                    if isinstance(atual, bool):
                        v = bool(v)
                    elif isinstance(atual, tuple):
                        v = tuple(str(x) for x in (v or []))
                    elif isinstance(atual, int):
                        v = int(v)
                    elif isinstance(atual, float):
                        v = float(v)
                    setattr(pm, k, v)
                if not (0 < pm.capital <= 50_000_000):
                    raise ValueError("capital entre R$ 1 e R$ 50 milhões")
                if not (0 <= pm.margem_min <= 5) or not (0.01 <= pm.realismo <= 1):
                    raise ValueError("margem entre 0 e 500%; realismo entre 0,01 e 1")
                return self._enviar(200, simulador.para_json(simulador.simular(pm)))
            elif u.path == "/api/testar_telegram":
                import notifier
                msg = notifier.testar()
            else:
                return self._enviar(404, {"erro": "rota não existe"})
            return self._enviar(200, {"ok": True, "msg": msg})
        except (ValueError, KeyError) as err:
            return self._enviar(400, {"ok": False, "msg": str(err)})
        except Exception as err:
            return self._enviar(500, {"ok": False, "msg": f"{type(err).__name__}: {err}"})


def main():
    db.init_db()
    servidores = []
    for end in ENDERECOS:
        end = end.strip()
        try:
            s = ThreadingHTTPServer((end, PORTA), Handler)
        except OSError as err:
            print(f"não consegui escutar em {end}:{PORTA}: {err}", flush=True)
            continue
        s.daemon_threads = True
        threading.Thread(target=s.serve_forever, daemon=True).start()
        servidores.append(s)
        print(f"painel em http://{end}:{PORTA}", flush=True)
    if not servidores:
        raise SystemExit("nenhum endereço disponível")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
