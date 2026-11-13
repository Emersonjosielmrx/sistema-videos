"""leads_whatsapp.py — só LEAD REAL do WhatsApp chega no bot "Interessados no produto" (dona, 01/11/2026).

Antes: a ponte do Hermes (D:\\hermes\\pc-base\\cmd\\server\\lead_bridge.go, no hermes-prod) mandava direto ao
Telegram TODA mensagem recebida nas linhas da conta e TODA resposta da IA: ~300 por semana, quase tudo conversa
pessoal, fornecedor e spam. Agora a ponte só LÊ as respostas da dona (HERMES_LEADS_SKIP_PHONES = todas as linhas) e
este vigia, a cada 3 min:
  1. lê no banco do Hermes (só leitura, 1 ssh) as mensagens recebidas desde a última passada;
  2. separa por conversa: lead (pediu orçamento, preço, contato, plano, "Tenho interesse", texto pronto da landing),
     teste (palavra teste ou linha da própria dona), ruído (spam/sorteio/propaganda, figurinha, "Bloquear") e
     conversa (o resto: família, fornecedor, recado);
  3. lead -> avisos.enviar(..., "produto-lead", chave por contato) com nome/@, produto, canal, mensagem original e
     como responder. O rodapé "L:<linha> J:<contato>" é o da ponte: marcando a mensagem no Telegram e escrevendo,
     o cliente recebe pelo mesmo número (lead_bridge.go handleOwner). O resto: só registro (avisos.jsonl).

    python leads_whatsapp.py                 # uma passada (a tarefa Leads_WhatsApp roda a cada 3 min)
    python leads_whatsapp.py --seco 168      # mostra como separaria as últimas 168 h, sem mandar nem gravar
    python leads_whatsapp.py --relatorio 24  # quantas de cada tipo nas últimas 24 h (lê o banco, não manda)
Estado: estado\\leads_whatsapp.json; log: logs\\leads_whatsapp.log.
"""
import html
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
ESTADO = BASE / "estado" / "leads_whatsapp.json"
LOG = BASE / "logs" / "leads_whatsapp.log"
HOST = "hermes-prod"
CONTA = "4e8adf4a-6530-47e2-af4c-1c268e6e68d7"  # HERMES_LEADS_USER_ID da ponte
JANELA_LEAD_H = 72  # o mesmo contato vira lead de novo só depois disso
PRIMEIRA_VEZ_MIN = 15  # sem estado: começa 15 min atrás (cobre a troca da ponte)

LANDING = re.compile(r"ol[aá],? quero (?:saber mais sobre o|o plano (?P<plano>.+?) do) (?P<prod>[^.?!\n]+)", re.I)
INTERESSE = re.compile(r"or[cç]amento|pre[cç]o|\bvalor(es)?\b|quanto (custa|fica|sai|[eé]\b|cobra|t[aá])|"
                       r"tenho interesse|interessad|quero (contratar|comprar|saber|o plano|testar|fazer (o|um|uma)|"
                       r"instalar)|contratar|como funciona|\bplanos? (essencial|profissional|b[aá]sico|completo)|"
                       r"mensalidade|teste gr[aá]tis|energia solar|placa solar|or[cç]ar", re.I)
RUIDO = re.compile(r"sorteio|promo[cç][aã]o|compre e concorra|\bcupom\b|desconto|\boferta|imperd[ií]vel|"
                   r"https?://|bit\.ly|clique (aqui|no link)|inscreva|segue (a gente|nosso)|"
                   r"temos aquele|quantos litros", re.I)
# resposta automática de outra empresa (atendente "*Maria:*", "agradece seu contato", "estou fora do WhatsApp")
AUTOMATICA = re.compile(r"^\s*\*[^*\n]{1,30}:\*|agradece (o )?seu contato|como (podemos|posso) (lhe |te )?ajudar|"
                        r"estou fora do whats|responderei|mensagem autom[aá]tica|hor[aá]rio de atendimento", re.I)
RECUSA = re.compile(r"n[aã]o tenho interesse|n[aã]o quero|n[aã]o preciso|pare de|remov[ae]|sair da lista|"
                    r"^\W*bloquear\W*$", re.I)
BOTAO_SIM = re.compile(r"^\W*tenho interesse\W*$", re.I)  # botão do 1º contato do disparo (campaign_buttons.go)
TESTE = re.compile(r"\bteste\b|\btestando\b", re.I)
NOVO_DIAS = 90  # "interesse" só vale de contato sem mensagem recebida antes nesse prazo (família/fornecedor não)
# números da própria dona fora das linhas desta conta (wa.me das landings em D:\landings-produtos\site): é teste
FONES_DA_DONA = {"5591984698653"}
TIPOS_RUIDO = {"sticker", "unknown", "reaction", "protocol"}
JID_OK = re.compile(r"^[0-9A-Za-z._:-]{3,40}@(s\.whatsapp\.net|lid)$")
SID_OK = re.compile(r"^[0-9a-f]{32}$")


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass
    if sys.stdout:
        print(linha, flush=True)


def _sql(sql, banco="wacalls_main"):
    """Linhas JSON de uma consulta só-leitura no Postgres do hermes-prod (1 ssh)."""
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", HOST,
           f"runuser -u postgres -- psql -d {banco} -X -A -t -q -v ON_ERROR_STOP=1"]
    r = subprocess.run(cmd, input=("BEGIN READ ONLY;\n" + sql + "\nCOMMIT;\n").encode("utf-8"), capture_output=True,
                       timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode:
        raise RuntimeError(f"psql {r.returncode}: {r.stderr.decode('utf-8', 'replace')[:300]}")
    return [json.loads(x) for x in r.stdout.decode("utf-8", "replace").splitlines() if x.startswith("{")]


def mensagens(desde_ms):
    """Recebidas e enviadas desde desde_ms nas linhas da conta (conversas 1-a-1), mais antigas primeiro."""
    return _sql(f"""
select row_to_json(t) from (
  select m.session_id sid, s.name linha_nome, split_part(split_part(coalesce(s.jid,''),'@',1),':',1) linha_fone,
         m.chat_jid jid, m.msg_id id, m.from_me eu, m.ts, m.type tipo, coalesce(m.body,'') texto
  from messages m join sessions s on s.id = m.session_id
  where s.user_id = '{CONTA}' and m.ts > {int(desde_ms)}
    and (m.chat_jid like '%@s.whatsapp.net' or m.chat_jid like '%@lid')
  order by m.ts
) t;""")


def linhas_da_conta():
    return {r["fone"] for r in _sql(f"select row_to_json(t) from (select split_part(split_part(jid,'@',1),':',1) fone "
                                     f"from sessions where user_id='{CONTA}' and coalesce(jid,'')<>'') t;") if r["fone"]}


def contato(sid, jid):
    """(nome, telefone) do contato no banco da linha (whatsmeow). Vazio se não achou."""
    if not (SID_OK.match(sid) and JID_OK.match(jid)):
        return "", ""
    user = jid.split("@")[0].split(":")[0]
    try:
        r = _sql(f"""
select row_to_json(t) from (select
  coalesce((select pn from whatsmeow_lid_map where lid = '{user}' limit 1), case when '{jid}' like '%@s.whatsapp.net' then '{user}' end) fone,
  (select coalesce(nullif(full_name,''), nullif(push_name,''), nullif(business_name,'')) from whatsmeow_contacts
    where their_jid in ('{jid}', (select pn from whatsmeow_lid_map where lid = '{user}' limit 1) || '@s.whatsapp.net')
    order by (full_name <> '') desc limit 1) nome) t;""", banco=f"wacalls_{sid}")
        return (r[0].get("nome") or "", r[0].get("fone") or "") if r else ("", "")
    except Exception as e:  # noqa: BLE001 — sem nome o lead sai do mesmo jeito
        log(f"contato {jid[-12:]}: {type(e).__name__}: {e}")
        return "", ""


def recebidas_antes(sid, jid, antes_ms):
    """Quantas mensagens o contato mandou antes de antes_ms (NOVO_DIAS): 0 = contato novo."""
    if not (SID_OK.match(sid) and JID_OK.match(jid)):
        return 1
    r = _sql(f"select row_to_json(t) from (select count(*) n from messages where session_id='{sid}' and chat_jid='{jid}'"
             f" and not from_me and ts < {int(antes_ms)} and ts > {int(antes_ms) - NOVO_DIAS * 86400000}) t;")
    return r[0]["n"] if r else 1


def sinal(m):
    """O que UMA mensagem recebida indica: landing | botao | recusa | ruido | teste | interesse | neutro."""
    t = m["texto"]
    if m["tipo"] in TIPOS_RUIDO:
        return "ruido"
    if LANDING.search(t):
        return "landing"
    if BOTAO_SIM.search(t):
        return "botao"
    if RECUSA.search(t):
        return "recusa"
    if RUIDO.search(t) or AUTOMATICA.search(t) or t.count("*") >= 4:
        return "ruido"
    if TESTE.search(t):
        return "teste"
    return "interesse" if INTERESSE.search(t) else "neutro"


def classificar(recebidas, linhas, novo=lambda: False, fone=lambda: ""):
    """lead | teste | ruido | conversa para as mensagens recebidas de UMA conversa (+ produto e canal do lead).
    novo(): o contato não mandou nada antes; fone(): telefone dele (os dois só são consultados quando precisa)."""
    if recebidas[0]["jid"].split("@")[0].split(":")[0] in linhas:
        return "teste", None, None  # uma linha da dona falando com outra
    sinais = [sinal(m) for m in recebidas]
    for m, s in zip(recebidas, sinais):
        if s == "landing":
            land = LANDING.search(m["texto"])
            prod = land.group("prod").strip()
            return "lead", prod + (f" (plano {land.group('plano').strip()})" if land.group("plano") else ""), "landing"
    botoes = [s for s in sinais if s in ("botao", "recusa")]
    if botoes and botoes[-1] == "botao":  # vale o último toque (tocou Bloquear e depois Tenho interesse = lead)
        if re.sub(r"\D", "", fone()) in FONES_DA_DONA:
            return "teste", None, None  # a dona testando o disparo com o próprio número
        return "lead", "campanha do WhatsApp (tocou Tenho interesse)", "WhatsApp (campanha)"
    if botoes:
        return "ruido", None, None
    if "interesse" in sinais and novo():
        return "lead", "não disse (pediu preço/informação)", "WhatsApp"
    if all(s == "ruido" for s in sinais):
        return "ruido", None, None
    if "teste" in sinais:
        return "teste", None, None
    return "conversa", None, None


def _fone_bonito(f):
    d = re.sub(r"\D", "", f or "")
    if d.startswith("55") and len(d) in (12, 13):
        return f"+55 ({d[2:4]}) {d[4:-4]}-{d[-4:]}"
    return f"+{d}" if d else ""


def texto_lead(c, recebidas, resposta, prod, canal, nome, fone):
    quem = html.escape(nome or "sem nome salvo") + (f" · {_fone_bonito(fone)}" if fone else "")
    linha = html.escape(c["linha_nome"]) + (f" ({_fone_bonito(c['linha_fone'])})" if c["linha_fone"] else "")
    msgs = "\n".join(f"“{html.escape(m['texto'][:400])}”" if m["texto"] else f"[{html.escape(m['tipo'])}]"
                     for m in recebidas[-5:])
    partes = [f"🙋 <b>Lead: {html.escape(prod)}</b>", f"Quem: {quem}", f"Canal: {html.escape(canal)} → linha {linha}",
              f"Mensagem:\n{msgs}"]
    if resposta:
        partes.append(f"Já respondido (IA ou você): “{html.escape(resposta[:300])}”")
    if fone:
        partes.append(f"Responder: https://wa.me/{re.sub(r'[^0-9]', '', fone)} ou marque esta mensagem e escreva")
    else:
        partes.append("Responder: marque esta mensagem e escreva (ele recebe pelo mesmo número)")
    # rodapé da ponte (lead_bridge.go leadFooterRe): é por ele que a resposta marcada chega no cliente
    partes.append(f"\n↩️ marque esta mensagem para responder · L:{c['sid']} J:{c['jid']}")
    return "\n".join(partes)


def passada(desde_ms, seco=False):
    """Separa e (fora do --seco) manda. Devolve (maior ts visto, Counter por tipo)."""
    linhas = linhas_da_conta()
    todas = mensagens(desde_ms)
    por_conversa = defaultdict(list)
    for m in todas:
        por_conversa[(m["sid"], m["jid"])].append(m)
    cont = Counter()
    if not seco:
        import avisos
    for (sid, jid), msgs in por_conversa.items():
        recebidas = [m for m in msgs if not m["eu"]]
        if not recebidas:
            continue
        dados = {}

        def _contato():
            if "c" not in dados:
                dados["c"] = contato(sid, jid)
            return dados["c"]
        tipo, prod, canal = classificar(recebidas, linhas,
                                        lambda: recebidas_antes(sid, jid, recebidas[0]["ts"]) == 0,
                                        lambda: _contato()[1])
        cont[tipo] += 1
        fim = jid.split("@")[0][-4:]
        if tipo == "lead":
            nome, fone = _contato()
            depois = [m for m in msgs if m["eu"] and m["ts"] >= recebidas[-1]["ts"] and m["texto"]]
            texto = texto_lead(recebidas[0], recebidas, depois[-1]["texto"] if depois else "", prod, canal, nome, fone)
            if seco:
                print(f"\n=== LEAD ({len(recebidas)} msg)\n{re.sub(r'<[^>]+>', '', texto)}")
            else:
                avisos.enviar(texto, "produto-lead", importante=True, chave=f"lead:whatsapp:{jid}",
                              janela_h=JANELA_LEAD_H)
            continue
        if seco:
            amostra = " | ".join((m["texto"] or f"[{m['tipo']}]")[:60] for m in recebidas[-3:])
            print(f"{tipo:9} …{fim} ({len(recebidas)} msg): {amostra}")
        elif tipo == "ruido":
            avisos.enviar(f"WhatsApp ruído de …{fim}: " + html.escape(" | ".join(
                (m["texto"] or m["tipo"])[:80] for m in recebidas[-2:])), "produto-ruido")
        else:  # conversa/teste: só a contagem (conversa pessoal não é copiada pro registro)
            avisos.enviar(f"WhatsApp {tipo} de …{fim}: {len(recebidas)} mensagem(ns)", f"produto-{tipo}")
    return max([desde_ms] + [m["ts"] for m in todas]), cont


def main():
    args = sys.argv[1:]
    if args[:1] in (["--seco"], ["--relatorio"]):
        import contextlib
        import io
        horas = float(args[1]) if len(args) > 1 else 24
        saida = io.StringIO() if args[0] == "--relatorio" else sys.stdout
        with contextlib.redirect_stdout(saida):
            _, cont = passada((time.time() - horas * 3600) * 1000, seco=True)
        print(f"\nconversas nas últimas {horas:g} h por tipo: {dict(cont)}")
        return
    try:
        est = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {}
    desde = est.get("ultimo_ts") or (time.time() - PRIMEIRA_VEZ_MIN * 60) * 1000
    try:
        ultimo, cont = passada(desde)
    except Exception as e:  # noqa: BLE001 — VPS fora: tenta na próxima, do mesmo ponto (nada se perde)
        log(f"passada falhou: {type(e).__name__}: {e}")
        return
    est.update(ultimo_ts=ultimo, ultima_passada=datetime.now().isoformat(timespec="seconds"))
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_name(ESTADO.name + ".tmp")
    tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ESTADO)
    if cont:
        log(f"conversas: {dict(cont)}")


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
