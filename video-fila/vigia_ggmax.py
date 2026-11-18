"""vigia_ggmax.py — vigia a loja GGMax (usuário inovare, Chrome do cofre fabricadeautomacoesia, porta 9725) e dispara o
alarme_vendas: 💰 venda nova (Minhas vendas), 💬 pergunta nos anúncios (Perguntas recebidas) e 💬 mensagem nova em
pedido (Central de notificações). Dona 18/11: "avisar de compra feita ou mensagem recebida, máxima prioridade até ser
respondido". A conta NÃO é do Kaggle (cofre.saida_kaggle = None): sai pela casa.

Só LÊ (3 páginas por rodada, sem clicar em nada). Tarefa VigiaGGMax a cada 5 min, oculta.
    python vigia_ggmax.py            uma rodada
    python vigia_ggmax.py --zerar    marca tudo o que já existe como visto (não alarma o passado)
Desligar: VIGIA_GGMAX=0.
"""
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
EST = BASE / "estado" / "vigia_ggmax.json"
LOG = BASE / "estado" / "vigia_ggmax.log"
PORTA = 9725
CONTA = "fabricadeautomacoesia@gmail.com"
SITE = "https://ggmax.com.br"


def log(m):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {m}\n")
    except OSError:
        pass


def _ler():
    try:
        return json.loads(EST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"vistos": [], "primeira": True}


def _gravar(d):
    d["vistos"] = d["vistos"][-1500:]
    EST.parent.mkdir(parents=True, exist_ok=True)
    EST.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _cdp_vivo():
    import urllib.request
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/json/version", timeout=5).read()
        return True
    except Exception:  # noqa: BLE001
        return False


def _abrir_chrome():
    """Chrome da conta fechado (a LimpezaChrome fecha de madrugada): reabre escondido pelo cofre."""
    sys.path.insert(0, r"D:\logins-google")
    import cofre
    cofre.abrir(CONTA, url=f"{SITE}/conta/notificacoes", visivel=False)
    log("Chrome da conta reaberto")


def _pagina(pg, caminho):
    pg.goto(SITE + caminho, wait_until="load", timeout=60000)
    time.sleep(6)
    t = pg.inner_text("body")
    if "Identifique-se" in t or "Entrar com Google" in t:
        raise RuntimeError("deslogou do GGMax")
    return t


def _corpo(t, inicio, fim="Somos um marketplace"):
    i = t.find(inicio)
    j = t.find(fim, i + 1)
    return t[i:j] if i >= 0 else ""


def coletar(pg):
    """Lista de eventos {id, tipo, titulo, texto, link}."""
    ev = []
    # 1. vendas
    t = _corpo(_pagina(pg, "/conta/vendas"), "Acompanhe suas vendas")
    if "Nenhuma venda encontrada" not in t:
        cods = re.findall(r"#([A-Z0-9]{6,8})\b", t)
        for cod in dict.fromkeys(cods):
            i = t.find("#" + cod)
            ev.append({"id": f"venda:{cod}", "tipo": "venda", "titulo": f"Pedido #{cod}",
                       "texto": " ".join(t[i:i + 400].split()), "link": f"{SITE}/conta/vendas"})
        if not cods:  # formato desconhecido: alarma pela mudança da página (não perde venda)
            ev.append({"id": "venda:pagina:" + str(abs(hash(" ".join(t.split()))) % 10**9), "tipo": "venda",
                       "titulo": "Mudou a página Minhas vendas", "texto": " ".join(t.split())[:600],
                       "link": f"{SITE}/conta/vendas"})
    # 2. perguntas nos anúncios: a página vazia diz "Nenhuma pergunta recebida"; qualquer outra coisa = pergunta
    t = _corpo(_pagina(pg, "/conta/perguntas-recebidas"), "Responda às perguntas", "Somos um marketplace")
    if t and "Nenhuma pergunta recebida" not in t:
        linhas = [l.strip() for l in t.splitlines() if l.strip() and l.strip() not in
                  ("Responda às perguntas dos compradores em seus anúncios.", "Status")]
        ev.append({"id": "perguntas:" + str(abs(hash(" ".join(linhas))) % 10**9), "tipo": "mensagem",
                   "titulo": "Pergunta nos seus anúncios", "texto": "\n".join(linhas)[:700],
                   "link": f"{SITE}/conta/perguntas-recebidas"})
    # 3. mensagens em pedidos (Central de notificações) — só das VENDAS (pedido que está em Minhas vendas)
    vendas = {e["id"].split(":")[1] for e in ev if e["tipo"] == "venda"}
    t = _corpo(_pagina(pg, "/conta/notificacoes"), "Marcar todos como lido")
    for m in re.finditer(r"Mensagens no pedido: #([A-Z0-9]{6,8})\n(.+?)\n(há [^\n]+)", t):
        cod, msg, quando = m.group(1), m.group(2).strip(), m.group(3)
        if cod not in vendas:  # 18/11: mensagem de pedido que a dona COMPROU de outro vendedor não é alarme de venda
            continue
        ev.append({"id": f"msgpedido:{cod}:{msg[:80]}", "tipo": "mensagem", "titulo": f"Mensagem no pedido #{cod}",
                   "texto": msg[:600], "link": f"{SITE}/conta/vendas"})
    return ev


def rodada(zerar=False):
    if os.environ.get("VIGIA_GGMAX", "1") == "0":
        return
    from playwright.sync_api import sync_playwright
    if not _cdp_vivo():
        _abrir_chrome()
    d = _ler()
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}")
        ctx = br.contexts[0]
        pg = ctx.new_page()  # aba própria: não mexe na aba que outro script esteja usando
        try:
            ev = coletar(pg)
        finally:
            pg.close()
    novos = [e for e in ev if e["id"] not in d["vistos"]]
    sys.path.insert(0, str(BASE))
    import alarme_vendas
    for e in novos:
        d["vistos"].append(e["id"])
        if zerar or d.get("primeira"):
            continue
        alarme_vendas.alertar(e["tipo"], "GGMax", e["titulo"], e["texto"], e["link"], chave="<SEGREDO_REMOVIDO>" + e["id"])
        log(f"ALARME {e['tipo']}: {e['titulo']} | {e['texto'][:100]}")
    if d.get("primeira") or zerar:
        log(f"1ª rodada: {len(novos)} itens antigos marcados como vistos (sem alarme)")
    d["primeira"] = False
    d["ultima"] = datetime.now().isoformat(timespec="seconds")
    _gravar(d)
    log(f"rodada ok: {len(ev)} itens, {len(novos)} novos")


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        rodada(zerar="--zerar" in sys.argv)
    except Exception as e:  # noqa: BLE001
        log(f"falhou: {str(e)[:200]}")
        if "deslogou" in str(e):
            sys.path.insert(0, str(BASE))
            import avisos
            avisos.enviar("GGMax: a conta inovare saiu do login — o vigia de vendas não consegue ver as vendas. "
                          "Entrar de novo com o Google fabricadeautomacoesia.", "contas com problema", importante=True)
        raise
