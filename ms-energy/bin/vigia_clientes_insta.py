# -*- coding: utf-8 -*-
"""Vigia de cliente interessado no @msenergycap: comentario novo ou mensagem nova no Direct -> aviso NA HORA no
Telegram (portao D:\\video-fila\\avisos.py; comentario e o que a regra deixa sair na hora). Dono 22/10/2026: quem
pede orcamento e fica sem resposta e cliente perdido (no Direct, 13 de 25 conversas antigas acabaram no cliente).

Estado em cache\\vigia_clientes.json: na 1a vez so marca o que ja existe (nao avisa coisa velha).
Tarefa MSEnergy_VigiaClientes (a cada 15 min, sem janela).

Resposta automatica (dono 22/10 18:20 "1, sim, ai avisa pelo telegram"): mensagem nova no Direct -> resposta com o
link do WhatsApp (1x por pessoa a cada 24 h; nao responde se alguem da empresa ja respondeu depois). Comentario novo
-> resposta privada no Direct (Private Replies, ate 7 dias) + resposta publica curta. A API so deixa responder Direct
ate 24 h depois da ultima mensagem do cliente: as conversas antigas (2025) nao tem como.
"""
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CREDS = Path(r"D:\credenciais-canais\instagram_contas.json")
BASE = "https://graph.instagram.com/v21.0"
ESTADO = Path(r"D:\ms-energy\cache\vigia_clientes.json")
DIRECT = "https://www.instagram.com/direct/inbox/"
WHATSAPP = "https://wa.me/message/RTCI5IGNUZVIF1"  # link da bio do @msenergycap (22/10)
RESPOSTA_DM = ("Olá! Obrigado por chamar a MS Energy ☀️ Fazemos instalação e manutenção de energia solar em "
               "Paragominas e região (residencial, comercial e rural).\n\nPara um orçamento grátis e mais rápido, fale "
               f"com a gente no WhatsApp: {WHATSAPP}\n\nSe preferir, mande aqui sua cidade e o valor médio da sua conta "
               "de luz que a equipe responde o quanto antes.")
RESPOSTA_COMENTARIO = "Oi, @{u}! Te mandamos uma mensagem no Direct 😉"
SPAM = re.compile(r"promot|collab|send (it|pic)|dm (us|me)|check (my|our)|followers|\bbio\b|link na minha", re.I)
# 25/10 (legenda nova: pergunta + "Comente SOL"): cada comentario recebe a resposta que combina com ele. Antes TODO
# comentario ganhava o mesmo Direct e a mesma resposta publica (texto igual em serie = cara de robo).
INTERESSE = re.compile(r"\?|or[cç]amento|pre[cç]o|valor|quanto|custa|whats|zap|contato|instala|interess|quero|"
                       r"como fa[cç]o|financ|parcel|visita|telefone|n[uú]mero", re.I)
PUBLICA_DIRECT = ["Oi, @{u}! Te mandamos uma mensagem no Direct 😉", "@{u}, te chamamos no Direct ☀️",
                  "Já te respondemos no Direct, @{u}! 😉", "@{u}, olha o Direct que mandamos as informações ☀️"]
PUBLICA_ELOGIO = ["Obrigado, @{u}! ☀️", "Valeu demais, @{u}! 🙌", "Que bom que gostou, @{u}! ☀️"]
PUBLICA_CONVERSA = ["Valeu por contar, @{u}! Se quiser um orçamento, é só comentar {p} ☀️",
                    "Obrigado, @{u}! Quer saber quanto ficaria aí? Comenta {p} que a gente te chama ☀️"]


def _variante(lista, chave, **kw):
    """Mesma resposta pro mesmo comentario, variando entre comentarios (md5, nunca hash())."""
    import hashlib
    return lista[int(hashlib.md5(str(chave).encode()).hexdigest(), 16) % len(lista)].format(**kw)


def _tipo_comentario(texto, conta="msenergycap"):
    """palavra (comentou SOL) | interesse (pergunta/orcamento) | elogio (emoji/curto) | conversa (respondeu a pergunta)."""
    try:
        if r"D:\postador-de-videos\bin" not in sys.path:
            sys.path.append(r"D:\postador-de-videos\bin")
        import legenda_empresa
        if legenda_empresa.tem_palavra(conta, texto):
            return "palavra"
    except Exception:  # noqa: BLE001
        pass
    if INTERESSE.search(texto or ""):
        return "interesse"
    palavras = re.findall(r"[A-Za-zÀ-ÿ]{2,}", texto or "")
    if not palavras or (len(palavras) <= 4 and ELOGIO.search(texto or "")):
        return "elogio"  # so emoji, ou "top", "parabéns pelo trabalho"...
    return "conversa"  # ex.: "Belém", "cerâmica" — respondeu a pergunta do post


ELOGIO = re.compile(r"\b(top|show|parab[eé]ns|lindo|linda|massa|incr[ií]vel|muito bom|demais|sucesso|[oó]timo|"
                    r"bacana|legal|perfeito|maravilh|amei|gostei|excelente|top+)\b", re.I)


def _lead(quem, canal, mensagem, link, extra=""):
    """Aviso de lead real (01/11): quem, produto, canal de origem, mensagem original e link para responder."""
    return (f"🙋 <b>Lead: MS Energy (energia solar)</b>\nQuem: @{quem}\nCanal: Instagram @msenergycap, {canal}\n"
            f"Mensagem: \"{html.escape(mensagem[:600])}\"\nResponder: {link}{extra}")


def _get(path, **params):
    url = path if path.startswith("http") else f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    return json.loads(urllib.request.urlopen(url, timeout=60).read())


def _post(path, tok, corpo):
    req = urllib.request.Request(f"{BASE}/{path}", data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
    try:
        urllib.request.urlopen(req, timeout=60).read()
        return None
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())["error"]["message"][:150]
        except Exception:  # noqa: BLE001
            return f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {e}"[:150]


def _recente(iso, horas):
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("+0000", "+00:00")) < timedelta(hours=horas)
    except Exception:  # noqa: BLE001
        return False


def _resultado(erro, o_que):
    return f"\n↪️ {o_que} automaticamente" if erro is None else f"\n⚠️ resposta automática falhou: {html.escape(erro)}"


def main():
    contas = json.loads(CREDS.read_text("utf-8"))
    tok = next(c for c in contas if "msenergycap" in c["name"].lower())["data"]["accessToken"]
    eu = _get("me", fields="user_id,username", access_token=tok)
    meus_ids = {str(eu.get("user_id")), str(eu.get("id"))}
    primeira = not ESTADO.exists()
    st = json.loads(ESTADO.read_text("utf-8")) if not primeira else {"contagens": {}, "comentarios": {},
                                                                       "mensagens": {}}
    avisos = []

    # comentarios: so abre os posts cuja contagem mudou
    res = _get("me/media", fields="id,comments_count,permalink,caption", limit=100, access_token=tok)
    midias = list(res.get("data", []))
    while res.get("paging", {}).get("next"):
        res = _get(res["paging"]["next"])
        midias += res.get("data", [])
    for m in midias:
        n = m.get("comments_count") or 0
        if not n or st["contagens"].get(m["id"]) == n:
            continue
        cs = _get(f"{m['id']}/comments", fields="id,text,timestamp,from{id,username},replies{from{id,username}}",
                  limit=50, access_token=tok)
        for c in cs.get("data", []):
            if c["id"] in st["comentarios"]:
                continue
            st["comentarios"][c["id"]] = c.get("timestamp")
            de = c.get("from") or {}
            if str(de.get("id")) in meus_ids or de.get("username") == eu.get("username"):
                continue
            post = (m.get("caption") or "").split("\n")[0][:50]
            extra = ""
            # 25/10: a empresa (pessoa, n8n ou rodada anterior) ja respondeu esse comentario -> nao responde de novo
            ja_resp = any(str((r.get("from") or {}).get("id")) in meus_ids
                          or (r.get("from") or {}).get("username") == eu.get("username")
                          for r in (c.get("replies") or {}).get("data", []))
            texto_c = c.get("text") or ""
            tipo = _tipo_comentario(texto_c)
            if (not primeira and not ja_resp and _recente(c.get("timestamp") or "", 24 * 7)
                    and not SPAM.search(texto_c)):
                u = de.get("username") or ""
                if tipo in ("palavra", "interesse"):
                    erro = _post("me/messages", tok, {"recipient": {"comment_id": c["id"]},
                                                       "message": {"text": RESPOSTA_DM}})
                    if erro is None:
                        _post(f"{c['id']}/replies", tok, {"message": _variante(PUBLICA_DIRECT, c["id"], u=u)})
                    extra = _resultado(erro, f"({tipo}) chamei no Direct com o WhatsApp e respondi o comentário")
                else:  # elogio/emoji ou resposta a pergunta do post: so agradece em publico (sem Direct nao pedido)
                    lista = PUBLICA_ELOGIO if tipo == "elogio" else PUBLICA_CONVERSA
                    erro = _post(f"{c['id']}/replies", tok, {"message": _variante(lista, c["id"], u=u, p="SOL")})
                    extra = _resultado(erro, f"({tipo}) respondi o comentário em público")
            elif ja_resp:
                extra = "\n↪️ a empresa já tinha respondido esse comentário"
            quem = html.escape(de.get("username") or "?")
            if SPAM.search(texto_c):  # 01/11: ruído -> só log
                avisos.append((f"spam no comentário de @{quem}: {html.escape(texto_c[:200])}", "produto-ruido", None))
            elif tipo in ("palavra", "interesse") and not ja_resp and _recente(c.get("timestamp") or "", 24 * 7):
                avisos.append((_lead(quem, f"comentário no post \"{html.escape(post)}\"", texto_c,
                                     m.get("permalink"), extra), "produto-lead", f"lead:msenergycap:comentario:{c['id']}"))
            else:  # elogio, conversa, já respondido ou antigo: vai pro resumo
                avisos.append((f"💬 <b>MS Energy — comentário novo</b> de @{quem} no post \"{html.escape(post)}\":\n"
                               f"\"{html.escape(texto_c[:300])}\"\nResponder: {m.get('permalink')}{extra}",
                               "msenergy-clientes", None))
        st["contagens"][m["id"]] = n

    # Direct: conversas mais recentes primeiro; ultimas 5 mensagens de cada
    cv = _get("me/conversations", platform="instagram",
              fields="id,updated_time,messages.limit(5){id,created_time,from,message}", access_token=tok)
    eh_meu = lambda de: str(de.get("id")) in meus_ids or de.get("username") == eu.get("username")  # noqa: E731
    respondidos = st.setdefault("respondidos", {})
    for conversa in cv.get("data", []):
        msgs = (conversa.get("messages") or {}).get("data", [])  # mais nova primeiro
        empresa_ja_respondeu = bool(msgs) and eh_meu(msgs[0].get("from") or {})
        novas = []
        for msg in msgs:
            if msg["id"] in st["mensagens"]:
                continue
            st["mensagens"][msg["id"]] = msg.get("created_time")
            if not eh_meu(msg.get("from") or {}):
                novas.append(msg)
        if not novas:
            continue
        de = novas[0].get("from") or {}
        extra = ""
        if (not primeira and not empresa_ja_respondeu and _recente(novas[0].get("created_time") or "", 23)
                and not _recente(respondidos.get(str(de.get("id"))) or "", 24)):
            erro = _post("me/messages", tok, {"recipient": {"id": de.get("id")}, "message": {"text": RESPOSTA_DM}})
            if erro is None:
                respondidos[str(de.get("id"))] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            extra = _resultado(erro, "respondi com o link do WhatsApp")
        bruto = "\n".join((m.get("message") or "(foto, áudio ou anexo)")[:300] for m in reversed(novas[:3]))
        quem = html.escape(de.get("username") or "?")
        link = f"https://ig.me/m/{de['username']}" if de.get("username") else DIRECT
        if SPAM.search(bruto):  # 01/11: ruído -> só log
            avisos.append((f"spam no Direct de @{quem}: {html.escape(bruto[:200])}", "produto-ruido", None))
        elif empresa_ja_respondeu:  # a empresa já está na conversa: resumo
            avisos.append((f"📩 <b>MS Energy — Direct</b> de @{quem} (a empresa já respondeu):\n"
                           f"\"{html.escape(bruto)}\"\nResponder: {link}", "msenergy-clientes", None))
        else:
            avisos.append((_lead(quem, "Direct", bruto, link, extra), "produto-lead",
                           f"lead:msenergycap:direct:{novas[0]['id']}"))

    st["mensagens"] = dict(sorted(st["mensagens"].items(), key=lambda kv: kv[1] or "")[-3000:])
    st["ultima_checagem"] = datetime.now().isoformat(timespec="seconds")
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(ESTADO)

    try:  # 25/10: o funil do Instagram (placar por pauta/formato/horário) mede os posts de 48 h, 1x por dia
        import funil_insta
        funil_insta.pontuar_dia()
    except Exception as e:  # noqa: BLE001  (medição nunca derruba o vigia)
        print(f"funil do Instagram falhou: {type(e).__name__}: {e}")
    try:  # 25/10: vídeo/foto já usados vão pro Drive 1x por dia (bin\arquivar_drive_ms.py)
        import arquivar_drive_ms
        arquivar_drive_ms.arquivar_dia()
    except Exception as e:  # noqa: BLE001
        print(f"arquivar no Drive falhou: {type(e).__name__}: {e}")
    if primeira:
        print(f"1a checagem: marcados {len(st['comentarios'])} comentários e {len(st['mensagens'])} mensagens "
              "que já existiam (sem aviso)")
        return
    if avisos:
        sys.path.insert(0, r"D:\video-fila")
        import avisos as portao
        # 01/11: lead real -> bot "Interessados no produto" na hora (chave = 1 aviso por lead); resto -> resumo/log
        for texto, origem, chave in avisos:
            portao.enviar(texto, origem, importante=origem == "produto-lead", chave=chave)
    print(f"{datetime.now():%d/%m %H:%M} avisos: {len(avisos)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
