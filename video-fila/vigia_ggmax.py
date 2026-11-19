"""vigia_ggmax.py — vigia a loja GGMax (usuário inovare) SEM NAVEGADOR e dispara o alarme_vendas:
💰 venda nova, 💬 pergunta nos anúncios e 💬 mensagem nova em pedido de venda.

19/11 dona: "o vigia não pode ficar 24 h [com Chrome aberto]; veja como funcionam os projetos navegador-sem-navegador
e o argo gemini para fazer essas conferências a cada x minutos sem precisar deixar aberto". Igual ao zelador do Gemini:
  • tudo por HTTP na API do site (https://ggmax.com.br/api/...), com Authorization: Bearer <token de 5 min>;
  • o token sai de POST /api/auth/refresh-token com o refresh_token (vale ~28 dias, guardado em estado/ggmax_sessao.json);
  • só se o refresh morrer: abre o Chrome do cofre ESCONDIDO ~20 s, copia os cookies auth.* e FECHA (renovar_cookies).
As páginas /conta/... ficam atrás do Cloudflare ("Just a moment" no requests); a API não.

Fontes (as mesmas que a página usa):
  /api/user/v4/orders?filter=sales                     -> vendas
  /api/user/v2/notifications?types=...                 -> pergunta (announcement_question), mensagem em pedido
                                                          (unread_order_chat_items), venda (sale), ticket
A conta NÃO é do Kaggle (cofre.saida_kaggle = None): sai pela casa.

    python vigia_ggmax.py              uma rodada (tarefa VigiaGGMax, 5/5 min, oculta)
    python vigia_ggmax.py --zerar      marca o que já existe como visto (não alarma o passado)
    python vigia_ggmax.py --renovar    força pegar cookies novos no Chrome (abre escondido e fecha)
Desligar: VIGIA_GGMAX=0.
"""
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
EST = BASE / "estado" / "vigia_ggmax.json"
SESSAO = BASE / "estado" / "ggmax_sessao.json"
LOG = BASE / "estado" / "vigia_ggmax.log"
CONTA = "fabricadeautomacoesia@gmail.com"
SITE = "https://ggmax.com.br"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
TIPOS = ("announcement,announcement_question,announcement_reply,message_filtered,ticket,sale,"
         "unread_order_chat_items")


def log(m):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {m}\n")
    except OSError:
        pass


def _json(p, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


class SessaoMorta(Exception):
    pass


# ───────────── sessão (sem navegador) ─────────────
def renovar_cookies():
    """Só quando o refresh_token morreu: abre o Chrome do cofre ESCONDIDO, lê os cookies auth.* e fecha."""
    sys.path.insert(0, r"D:\logins-google")
    import cofre
    from playwright.sync_api import sync_playwright
    porta, proc = cofre.abrir(CONTA, url="about:blank", visivel=False)
    br = None
    try:
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = br.contexts[0]
            pg = ctx.new_page()
            pg.goto(SITE + "/conta/notificacoes", wait_until="load", timeout=60000)
            time.sleep(5)
            ck = {c["name"]: c["value"] for c in ctx.new_cdp_session(pg).send("Network.getAllCookies")["cookies"]
                  if "ggmax" in c.get("domain", "")}
            pg.close()
            cofre.fechar(proc, br, CONTA)  # proc=None (aberto por outro) = não fecha
    except Exception:
        cofre.fechar(proc, None, CONTA)
        raise
    if "auth.refresh_token" not in ck:
        raise SessaoMorta("o Chrome da conta não está logado no GGMax (sem auth.refresh_token)")
    _gravar(SESSAO, {"refresh_token": urllib.parse.unquote(ck["auth.refresh_token"]),
                     "pego_em": datetime.now().isoformat(timespec="seconds")})
    log("cookies renovados pelo Chrome (aberto escondido e fechado)")


def _sessao():
    """requests.Session já com o token de acesso novo (5 min)."""
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json", "Origin": SITE, "Referer": SITE + "/conta/vendas"})
    for tentativa in range(2):
        ses = _json(SESSAO, {})
        if not ses.get("refresh_token"):
            renovar_cookies()
            continue
        r = s.post(SITE + "/api/auth/refresh-token", json={"refresh_token": ses["refresh_token"]}, timeout=30)
        tok = (r.json().get("data") or {}).get("token") if r.ok else None
        if tok:
            s.headers["Authorization"] = "Bearer " + tok
            if r.cookies.get("auth.refresh_token"):  # o servidor pode girar o refresh: guarda o novo
                ses["refresh_token"] = urllib.parse.unquote(r.cookies["auth.refresh_token"])
                _gravar(SESSAO, ses)
            return s
        log(f"refresh recusado ({r.status_code} {r.text[:120]}) — renovando cookies")
        if tentativa == 0:
            renovar_cookies()
    raise SessaoMorta("não consegui sessão no GGMax nem com cookies novos")


def _get(s, caminho):
    r = s.get(SITE + "/api" + caminho, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not j.get("success", True):
        raise RuntimeError(f"{caminho}: {str(j)[:150]}")
    return j.get("data") or {}


# ───────────── coleta ─────────────
def _txt(n):
    """Texto legível de uma notificação (os campos variam por tipo)."""
    partes = []
    for k in ("title", "message", "text", "body", "description", "content"):
        v = n.get(k)
        if isinstance(v, str) and v.strip():
            partes.append(v.strip())
    for k in ("data", "payload", "meta"):
        if isinstance(n.get(k), dict):
            for kk in ("title", "message", "text", "question", "announcement_title"):
                v = n[k].get(kk)
                if isinstance(v, str) and v.strip():
                    partes.append(v.strip())
    return " | ".join(dict.fromkeys(partes))[:700] or json.dumps(n, ensure_ascii=False)[:500]


def coletar(s):
    ev = []
    # 1. vendas
    for o in (_get(s, "/user/v4/orders?filter=sales&offset=0").get("orders") or []):
        oid = str(o.get("id"))
        desc = o.get("description") or (o.get("announcement") or {}).get("title") or ""
        ev.append({"id": f"venda:{oid}", "tipo": "venda", "titulo": f"Pedido {oid} — R$ {o.get('subtotal', '?')}",
                   "texto": f"{desc} | status: {o.get('status')} | criado {o.get('date_created')}".strip(" |"),
                   "link": f"{SITE}/conta/vendas"})
    vendas = {e["id"].split(":", 1)[1] for e in ev}
    # 2. notificações: pergunta, mensagem em pedido, venda, ticket
    dados = _get(s, f"/user/v2/notifications?offset=0&limit=30&include_total_by_type=true&types={TIPOS}")
    for n in dados.get("notifications") or []:
        tipo = str(n.get("type") or n.get("notification_type") or "")
        nid = str(n.get("id") or n.get("uuid") or hash(json.dumps(n, sort_keys=True)))
        texto = _txt(n)
        pedido = str(n.get("order_id") or (n.get("data") or {}).get("order_id") or "")
        if "question" in tipo or "reply" in tipo:
            ev.append({"id": f"pergunta:{nid}", "tipo": "mensagem", "titulo": "Pergunta no seu anúncio", "texto": texto,
                       "link": f"{SITE}/conta/perguntas-recebidas"})
        elif "order_chat" in tipo or "chat" in tipo:
            if pedido and vendas and pedido not in vendas:
                continue  # 18/11: mensagem de pedido que a dona COMPROU de outro vendedor não alarma
            ev.append({"id": f"msgpedido:{nid}", "tipo": "mensagem", "titulo": f"Mensagem no pedido {pedido}".strip(),
                       "texto": texto, "link": f"{SITE}/conta/vendas"})
        elif "sale" in tipo:
            ev.append({"id": f"venda:notif:{nid}", "tipo": "venda", "titulo": "Venda (notificação)", "texto": texto,
                       "link": f"{SITE}/conta/vendas"})
        elif "ticket" in tipo:
            ev.append({"id": f"ticket:{nid}", "tipo": "mensagem", "titulo": "Resposta do suporte (ticket)",
                       "texto": texto, "link": f"{SITE}/conta/notificacoes"})
        elif tipo not in ("announcement", "message_filtered"):  # anúncio aprovado/reprovado = rotina, sem alarme
            # 19/11: tipo que ainda não vimos (o feed estava vazio no teste) — avisa em vez de perder
            ev.append({"id": f"outro:{nid}", "tipo": "mensagem", "titulo": f"Notificação do GGMax ({tipo or '?'})",
                       "texto": texto, "link": f"{SITE}/conta/notificacoes"})
            log(f"tipo novo de notificação: {tipo!r} {json.dumps(n, ensure_ascii=False)[:300]}")
    return ev


def rodada(zerar=False):
    if os.environ.get("VIGIA_GGMAX", "1") == "0":
        return
    d = _json(EST, {"vistos": [], "primeira": True})
    s = _sessao()
    ev = coletar(s)
    sys.path.insert(0, str(BASE))
    import alarme_vendas
    # 19/11: pergunta/mensagem que sumiu (a dona respondeu/leu) fecha o alarme sozinho. Venda só fecha com "ok".
    agora_ids = {"ggmax:" + e["id"] for e in ev}
    for ch in alarme_vendas.abertos("ggmax:"):
        if ch not in agora_ids and not ch.startswith("ggmax:venda:"):
            alarme_vendas.resolvido(ch, "respondido no GGMax")
    novos = [e for e in ev if e["id"] not in d["vistos"]]
    for e in novos:
        d["vistos"].append(e["id"])
        if zerar or d.get("primeira"):
            continue
        alarme_vendas.alertar(e["tipo"], "GGMax", e["titulo"], e["texto"], e["link"], chave="<SEGREDO_REMOVIDO>" + e["id"])
        log(f"ALARME {e['tipo']}: {e['titulo']} | {e['texto'][:100]}")
    if d.get("primeira") or zerar:
        log(f"1ª rodada: {len(novos)} itens marcados como vistos (sem alarme)")
    d["primeira"] = False
    d["ultima"] = datetime.now().isoformat(timespec="seconds")
    d["vistos"] = d["vistos"][-1500:]
    _gravar(EST, d)
    log(f"rodada ok (sem navegador): {len(ev)} itens, {len(novos)} novos")


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        if "--renovar" in sys.argv:
            renovar_cookies()
        rodada(zerar="--zerar" in sys.argv)
    except SessaoMorta as e:
        log(f"falhou: {e}")
        sys.path.insert(0, str(BASE))
        import avisos
        avisos.enviar("GGMax: a conta inovare saiu do login — o vigia de vendas não consegue ver as vendas. "
                      "Entrar de novo com o Google fabricadeautomacoesia.", "contas com problema", importante=True,
                      chave="<SEGREDO_REMOVIDO>")
        raise
    except Exception as e:  # noqa: BLE001
        log(f"falhou: {str(e)[:200]}")
        raise
