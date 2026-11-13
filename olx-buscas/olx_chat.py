# -*- coding: utf-8 -*-
"""Chat com vendedores da OLX pelo Chrome logado da dona (perfil D:\\hipercool-materiais\\perfis_chrome\\olx).

A dona autorizou (04/11/2026) o robô a mandar mensagens sozinho, sem confirmação. Cuidados:
  - só conversa que o ROBÔ começou (anúncio aprovado pela busca); conversa que a dona já tinha = não toca;
  - teto de mensagens por dia (config chat_max_dia) e intervalo mínimo entre envios;
  - nunca fecha compra, nunca passa telefone/Pix/dados, nunca negocia fora da OLX; no máximo N mensagens por conversa;
  - toda resposta do vendedor vai pro Telegram com resumo e o link.
"""
import json, re, socket, subprocess, time, html, urllib.parse, ctypes
from contextlib import contextmanager
from datetime import datetime, date
from pathlib import Path

import olx_buscas as o

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PERFIL = r"D:\hipercool-materiais\perfis_chrome\olx"
PORTA = 9788
CONVERSAS = o.BASE / "estado" / "conversas.json"
FILA = o.BASE / "estado" / "fila_chat.json"

JS_BOLHAS = r"""() => Array.from(document.querySelectorAll("div[class*='group/bubble']")).map(e => {
  let a = e; for (let i = 0; i < 3 && a; i++) a = a.parentElement;
  const cl = (a && a.className || '').toString();
  return [cl.includes('items-end') ? 'eu' : 'vendedor', (e.innerText || '').trim()];
})"""


def ram_livre_mb():
    class M(ctypes.Structure):
        _fields_ = [("l", ctypes.c_ulong), ("p", ctypes.c_ulong), ("t", ctypes.c_ulonglong),
                    ("a", ctypes.c_ulonglong)] + [(f"x{i}", ctypes.c_ulonglong) for i in range(5)]
    m = M(); m.l = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.a // (1024 * 1024)


def _porta_aberta():
    s = socket.socket(); s.settimeout(1)
    try:
        return s.connect_ex(("127.0.0.1", PORTA)) == 0
    finally:
        s.close()


@contextmanager
def navegador():
    """Usa o Chrome da OLX se já estiver aberto; senão abre fora da tela e fecha no fim."""
    from playwright.sync_api import sync_playwright
    abri = None
    if not _porta_aberta():
        if ram_livre_mb() < 1200:
            raise RuntimeError(f"RAM baixa ({ram_livre_mb()} MB), chat fica pra depois")
        abri = subprocess.Popen([CHROME, f"--user-data-dir={PERFIL}", f"--remote-debugging-port={PORTA}",
                                 "--no-first-run", "--no-default-browser-check", "--window-position=-32000,-32000",
                                 # janela fora da tela não pode "dormir" (screenshot/render travavam)
                                 "--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding",
                                 "--disable-background-timer-throttling",
                                 "--window-size=1280,900", "about:blank"], creationflags=0x08000000)
        for _ in range(30):
            if _porta_aberta():
                break
            time.sleep(1)
        else:
            abri.terminate()
            raise RuntimeError("Chrome da OLX não abriu (perfil ainda fechando?), tento no próximo ciclo")
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}")
        ctx = b.contexts[0]
        pg = ctx.new_page()
        try:
            yield pg
        finally:
            try:
                pg.close()
            except Exception:
                pass
            if abri:
                try:
                    b.new_browser_cdp_session().send("Browser.close")  # fecha de verdade o Chrome que eu abri
                except Exception:
                    pass
    if abri:
        try:
            abri.terminate()
        except Exception:
            pass


def _abrir_conversa(pg, list_id):
    pg.goto(f"https://chat.olx.com.br/?list-id={list_id}", wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)
    for _ in range(3):  # fecha o pop-up de novidades
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)
    if "conta.olx.com.br" in pg.url or "acesso" in pg.url:
        raise RuntimeError("deslogado da OLX")
    campo = pg.locator("textarea[placeholder^='Responder'], input[placeholder^='Responder']").first
    campo.wait_for(timeout=15000)
    return campo


def ler_bolhas(pg):
    return list(reversed(pg.evaluate(JS_BOLHAS)))  # DOM vem do mais novo pro mais velho


def enviar(pg, list_id, texto, so_se_vazia=False):
    campo = _abrir_conversa(pg, list_id)
    antes = ler_bolhas(pg)
    if so_se_vazia and antes:
        return None, antes  # já existe conversa (a dona falou com ele) -> não mexe
    campo.click()
    campo.fill(texto)
    pg.wait_for_timeout(500)
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(4000)
    depois = ler_bolhas(pg)
    ok = any(l == "eu" and texto[:30] in t for l, t in depois[-3:])
    if not ok:
        raise RuntimeError("mensagem não apareceu na conversa depois de enviar")
    m = re.search(r"chat-id=([^&]+)", pg.url)
    return (urllib.parse.unquote(m.group(1)) if m else None), depois


# ---------------- texto das mensagens (Sonnet) ----------------
PRIMEIRA = """Escreva a PRIMEIRA mensagem da compradora para o vendedor de um usado na OLX.
Estilo dela (copie o jeito): curto, informal, direto, sem emoji, sem se apresentar. Exemplos reais dela:
 "Confirma pra mim a ram dele processador, se as teclas e bateria funciona"
 "Ate quanto faz ? Quanto a bateria dura ? Todas as teclas funcionam ?"
 "Qual o processador ? Tem quanto de ram ? Quanto de hd ?"
Anúncio: {titulo} — {preco}
O que já se sabe: {resumo} | {itens}
O que as fotos mostram: {fotos}
Dúvidas que as regras dela pedem e o anúncio não responde: {duvidas}
Regras da busca: {regras}
Pergunte SÓ o que falta (no máximo 3 coisas) e termine pedindo desconto ("Ate quanto faz ?" ou parecido).
Nunca peça telefone/WhatsApp, nunca ofereça pagar fora da OLX. Responda só o texto da mensagem."""

SEGUINTE = """Você negocia na OLX em nome da compradora (ela quer o mais barato que FUNCIONE; compra pelo envio da OLX).
Anúncio: {titulo} — {preco} | teto dela para esse produto: R$ {teto}
Regras da busca: {regras}
Conversa até agora (mais antiga primeiro):
{conversa}
Responda SÓ um JSON:
{{"resumo": "1-2 frases pra compradora: o que o vendedor respondeu e o que importa",
  "veredito": "comprar" | "negociando" | "descartar" | "aguardar",
  "motivo": "por quê (defeito revelado, preço, falta info...)",
  "preco_final": número ou null (menor preço que o vendedor aceitou),
  "responder": "próxima mensagem curta no estilo dela (informal, sem emoji) ou vazio se não precisa responder"}}
Regras: pode fazer contraproposta razoável (uns 10-20% abaixo, nunca acima do teto). Se o vendedor revelar defeito que as
regras não aceitam, veredito "descartar" e responda educado agradecendo ("Blz, obrigado"). Se já está tudo claro e o
preço é bom, veredito "comprar" e responder vazio (a compradora fecha). NUNCA diga que vai comprar/fechar, nunca passe
telefone, Pix, endereço, nem aceite negociar fora da OLX."""


def _txt_ia(prompt):
    j = o.ler(o.OMNI, {})
    for modelo in (o.cfg().get("modelo_assistente", "sonnet-fila"), "gemini/gemini-4-argon", o.cfg()["modelo_ia"]):
        try:
            r = o.cr.post(j["base_url"].rstrip("/") + "/v1/chat/completions", timeout=120,
                          headers={"Authorization": "Bearer " + j["api_key"]},
                          json={"model": modelo, "temperature": 0.4, "max_tokens": 800,
                                "messages": [{"role": "user", "content": prompt}]})
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            o.log(f"chat IA {modelo} falhou: {e}")
    return None


def _limpa(t):
    t = (t or "").strip().strip('"').strip()
    t = re.sub(r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}", "", t)  # nunca número de telefone
    return t[:400]


# ---------------- fila e ciclo ----------------
def enfileirar(b, a, v):
    """Chamado quando um anúncio é aprovado: agenda a 1ª mensagem."""
    if not o.cfg().get("chat_ligado", True):
        return
    with o.trava_arq:
        conv = o.ler(CONVERSAS, {})
        fila = o.ler(FILA, [])
        lid = str(a["listId"])
        if lid in conv or any(x["listId"] == lid for x in fila):
            return
        fila.append({"listId": lid, "busca": b["id"], "titulo": a.get("subject"), "preco": a.get("priceValue"),
                     "url": a.get("url"), "resumo": v.get("resumo"), "itens": v.get("itens"),
                     "duvidas": v.get("duvidas"), "fotos": v.get("fotos_info"), "quando": time.time()})
        o.gravar(FILA, fila)


def _enviadas_hoje(conv):
    hoje = date.today().isoformat()
    return sum(1 for c in conv.values() for m in c.get("minhas", []) if m.get("dia") == hoje)


def ciclo():
    c = o.cfg()
    if not c.get("chat_ligado", True):
        return
    conv = o.ler(CONVERSAS, {})
    fila = o.ler(FILA, [])
    ativas = [k for k, x in conv.items() if x.get("status") in ("aguardando", "negociando")]
    if not fila and not ativas:
        return
    limite = int(c.get("chat_max_dia", 20))
    intervalo = int(c.get("chat_intervalo_s", 180))
    buscas = {b["id"]: b for b in o.ler(o.BUSCAS, [])}
    ultimo_envio = max([m.get("t", 0) for x in conv.values() for m in x.get("minhas", [])] + [0])
    with navegador() as pg:
        # 1) respostas dos vendedores nas conversas abertas pelo robô
        for lid in ativas:
            x = conv[lid]
            try:
                _abrir_conversa(pg, lid)
                bolhas = ler_bolhas(pg)
            except Exception as e:
                o.log(f"chat ler {lid}: {e}")
                continue
            n_vend = sum(1 for l, _ in bolhas if l == "vendedor")
            if n_vend <= x.get("lidas_vendedor", 0):
                if time.time() - x.get("inicio", time.time()) > 3 * 86400:
                    x["status"] = "sem resposta"
                continue
            x["lidas_vendedor"] = n_vend
            b = buscas.get(x["busca"], {"max": "?", "regras": []})
            conversa = "\n".join(f"{'COMPRADORA' if l == 'eu' else 'VENDEDOR'}: {t}" for l, t in bolhas[-20:])
            r = _txt_ia(SEGUINTE.format(titulo=x["titulo"], preco=x["preco"], teto=b.get("max"),
                                        regras="; ".join(o.regras(b)) or "(padrão)", conversa=conversa))
            try:
                d = json.loads(re.search(r"\{.*\}", r or "", re.S).group(0))
            except Exception:
                o.log(f"chat {lid}: IA não devolveu JSON")
                continue
            ult_vend = next((t for l, t in reversed(bolhas) if l == "vendedor"), "")
            icone = {"comprar": "🟢 VALE COMPRAR", "negociando": "💬", "descartar": "❌ descartado",
                     "aguardar": "⏳"}.get(d.get("veredito"), "💬")
            msg = (f"{icone} <b>{html.escape(x['titulo'] or '')}</b> — {html.escape(x['preco'] or '')}\n"
                   f"Vendedor: <i>“{html.escape(ult_vend[:300])}”</i>\n{html.escape(d.get('resumo') or '')}")
            if d.get("preco_final"):
                msg += f"\n💰 aceitou R$ {d['preco_final']}"
            resp = _limpa(d.get("responder"))
            pode = (len(x.get("minhas", [])) < int(c.get("chat_max_por_conversa", 4)) and _enviadas_hoje(conv) < limite)
            if resp and pode:
                espera = intervalo - (time.time() - ultimo_envio)
                if espera > 0:
                    time.sleep(min(espera, intervalo))
                try:
                    enviar(pg, lid, resp)
                    x.setdefault("minhas", []).append({"t": time.time(), "dia": date.today().isoformat(), "txt": resp})
                    ultimo_envio = time.time()
                    msg += f"\n↪️ respondi: <i>{html.escape(resp)}</i>"
                except Exception as e:
                    msg += f"\n⚠️ não consegui responder: {html.escape(str(e))}"
            msg += f'\n<a href="https://chat.olx.com.br/?list-id={lid}">Abrir conversa</a> · <a href="{x["url"]}">anúncio</a>'
            x["status"] = {"comprar": "pronto", "descartar": "descartado"}.get(d.get("veredito"), "negociando")
            o.mandar(msg)
            o.gravar(CONVERSAS, conv)
        # 2) primeiras mensagens da fila
        while fila and _enviadas_hoje(conv) < limite:
            item = fila.pop(0)
            lid = item["listId"]
            b = buscas.get(item["busca"])
            if not b or lid in conv:
                continue
            texto = _limpa(_txt_ia(PRIMEIRA.format(titulo=item["titulo"], preco=item["preco"], resumo=item["resumo"],
                                                   itens=item["itens"], duvidas=item["duvidas"] or "nenhuma",
                                                   fotos=item.get("fotos") or "não analisadas",
                                                   regras="; ".join(o.regras(b)) or "(padrão)")))
            if not texto:
                fila.insert(0, item)
                break
            espera = intervalo - (time.time() - ultimo_envio)
            if espera > 0:
                time.sleep(espera)
            try:
                chat_id, bolhas = enviar(pg, lid, texto, so_se_vazia=True)
            except Exception as e:
                o.log(f"chat enviar {lid}: {e}")
                if "deslogado" in str(e):
                    o.mandar("⚠️ A OLX deslogou o Chrome do robô. Preciso que você entre de novo na conta.")
                    fila.insert(0, item)
                    break
                continue
            if chat_id is None:
                conv[lid] = {**item, "status": "da dona", "inicio": time.time()}  # ela já conversava: não mexe
            else:
                conv[lid] = {**item, "status": "aguardando", "inicio": time.time(), "chat_id": chat_id,
                             "lidas_vendedor": sum(1 for l, _ in bolhas if l == "vendedor"),
                             "minhas": [{"t": time.time(), "dia": date.today().isoformat(), "txt": texto}]}
                ultimo_envio = time.time()
                o.log(f"chat: 1ª msg em {lid}: {texto!r}")
                o.mandar(f"✉️ Perguntei ao vendedor de <b>{html.escape(item['titulo'] or '')}</b> "
                         f"({html.escape(item['preco'] or '')}):\n<i>{html.escape(texto)}</i>")
            o.gravar(CONVERSAS, conv)
            o.gravar(FILA, fila)
    o.gravar(CONVERSAS, conv)
    o.gravar(FILA, fila)
