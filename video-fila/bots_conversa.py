"""bots_conversa.py — cada bot do Telegram ATENDE o dono no tema dele (dono, 22/10/2026).

Pedido do dono: "tem que ser pelo Telegram eu falando pra corrigir; todos os bots têm que me responder sobre seus temas
e poder acessar os outros se precisar pra reparo ou informações".

Antes só o bot geral lia o que o dono escrevia. Aqui os bots temáticos (produção, postagem, métricas, bloqueios,
pendências, comentários) passam a ler as mensagens do dono e transformam cada uma num pedido da IA do painel
(painel_ia.py — o caminho SEGURO: pergunta só lê; conserto primeiro PROPÕE sem mexer; só aplica com o "aplicar" do dono,
com backup de cada arquivo e "desfazer"). A resposta volta NO MESMO bot, como resposta à mensagem do dono.
  pergunta solta              -> pergunta (agente só lê; pode consultar QUALQUER projeto)
  "corrige/conserta/tira/põe/muda/arruma/troca/adiciona/remove ..." -> proposta de conserto
  responder a proposta com "aplicar" (ou sim/pode/manda) -> aplica   |  "não" -> descarta
  responder ao resultado com "desfazer"                  -> desfaz

Bots NÃO lidos aqui (já têm leitor; dois leitores no mesmo bot roubam mensagens um do outro): o GERAL e o APRENDIZADO
(notificar_telegram.py), o OPUS (monitor_opus_telegram.py) e o VIGIA_TRADER (outro projeto).

    python bots_conversa.py --rodar 39    # atendente vivo por 39 min (o vigia geral relança a cada 20)
Estado: estado\\bots_conversa.json; log: logs\\bots_conversa.log.
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
BOTS_JSON = Path(r"D:\postador-de-videos\config\telegram_bots.json")
ESTADO = BASE / "estado" / "bots_conversa.json"
LOG = BASE / "logs" / "bots_conversa.log"
TRAVA = BASE / "estado" / "bots_conversa.lock"

# bot -> (projeto padrão no painel_ia, tema que o agente atende)
TEMAS = {
    "producao": ("cortes", "produção dos vídeos (recap de parceiros/anime, hipercool, veo), vozes e narração"),
    "postagem": ("postador", "postagens, agenda, filas e ritmo de postagem nos canais"),
    "metricas": ("geral", "visualizações, inscritos, desempenho dos vídeos, canais e títulos"),
    "bloqueios": ("postador", "bloqueios do YouTube Studio, direitos autorais, limites e avisos dos canais"),
    "pendencias_humanas": ("geral", "o que precisa do dono: logins, contas, verificações, decisões"),
    "comentarios": ("postador", "comentários dos vídeos e respostas"),
}
# palavras que levam o pedido pra outro projeto (o agente lê todos; aqui é só onde ele PROPÕE o conserto)
PROJETO_POR_PALAVRA = [
    (r"voz|bord[aã]o|personagem|narrador|chiquinha|chaves|clone|sotaque|fala ", "voz"),
    (r"hipercool|cap[ií]tulo|manhwa noturno|the inheritor|censura", "hipercool"),
    (r"\bveo\b|flow", "veo"),
    (r"react|rede de canais|manhwareact", "manhwa-react"),
    (r"post|agend|canal|tiktok|insta|studio", "postador"),
    (r"parceiro|short|recap|anime", "cortes"),
]
CONSERTO = re.compile(r"^\s*(corrig|consert|arrum|tir[ae]|p[oõ]e|ponha|coloc|mud[ae]|troc|adicion|remov|tira|inclu|"
                      r"desliga|liga|aument|diminu|para de|pare de|faz|fa[cç]a)", re.I)
SIM = re.compile(r"^\s*(aplicar|aplica|sim|pode|manda|ok|confirmo|bora)\b", re.I)
NAO = re.compile(r"^\s*(n[aã]o|cancela|esquece)\b", re.I)
DESFAZER = re.compile(r"^\s*desfaz", re.I)


def log(msg):
    linha = f"[{time.strftime('%d/%m %H:%M:%S')}] {msg}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _bots():
    b = json.loads(BOTS_JSON.read_text(encoding="utf-8"))
    return {k: v for k, v in b.items() if k in TEMAS and isinstance(v, dict) and v.get("em_uso")
            and v.get("bot_token") and v.get("chat_id")}


def _api(token, metodo, dados):
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{metodo}",
                                 json.dumps(dados).encode("utf-8"), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def _mandar(bot, texto, responder_a=None, teclado=None):
    dados = {"chat_id": bot["chat_id"], "text": texto[:3900], "disable_web_page_preview": True}
    if responder_a:
        dados["reply_to_message_id"] = responder_a
    if teclado:  # botões fixos embaixo do chat (23/10: "aperto um botão" das melhorias contínuas)
        dados["reply_markup"] = teclado
    try:
        return (_api(bot["bot_token"], "sendMessage", dados).get("result") or {}).get("message_id")
    except Exception as e:  # noqa: BLE001
        log(f"falha ao responder: {type(e).__name__}: {e}")
        return None


def _mandar_documento(bot, caminho, legenda="", responder_a=None):
    """Arquivo como documento do Telegram (23/10: o pacote de revisão das melhorias, pra encaminhar a qualquer IA)."""
    import os
    caminho = Path(caminho)
    lim = "----bots" + os.urandom(8).hex()
    campos = {"chat_id": str(bot["chat_id"]), "caption": legenda[:1000]}
    if responder_a:
        campos["reply_to_message_id"] = str(responder_a)
    corpo = b"".join(f"--{lim}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8")
                     for k, v in campos.items())
    corpo += (f"--{lim}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{caminho.name}\"\r\n"
              "Content-Type: text/markdown\r\n\r\n").encode("utf-8") + caminho.read_bytes() + f"\r\n--{lim}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{bot['bot_token']}/sendDocument", corpo,
                                 {"Content-Type": f"multipart/form-data; boundary={lim}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return (json.loads(r.read()).get("result") or {}).get("message_id")
    except Exception as e:  # noqa: BLE001
        log(f"falha ao mandar documento: {type(e).__name__}: {e}")
        return None


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"offset": {}, "pedidos": {}, "por_msg": {}}


def _gravar(est):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_name(ESTADO.name + ".tmp")
    tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    # 11/11: o Windows nega a troca enquanto outro programa (antivírus, backup, painel) está lendo o arquivo
    # ("WinError 5 Acesso negado" no log várias vezes por dia) — tenta de novo por até ~3 s antes de desistir
    for tentativa in range(6):
        try:
            tmp.replace(ESTADO)
            return
        except PermissionError:
            if tentativa == 5:
                raise
            time.sleep(0.5)


def _projeto(chave, texto):
    for rx, proj in PROJETO_POR_PALAVRA:
        if re.search(rx, texto, re.I):
            return proj
    return TEMAS[chave][0]


def _novo_pedido(est, chave, bot, msg):
    import painel_ia
    texto = (msg.get("text") or "").strip()
    tipo = "consertar" if CONSERTO.search(texto) else "pergunta"
    contexto = (f"Mensagem enviada pelo dono no bot do Telegram de {TEMAS[chave][1]}. Responda sobre esse tema; se "
                f"precisar de informação ou conserto de OUTRO projeto, consulte/proponha nele também.")
    if msg.get("reply_to_message"):
        contexto += f"\nEle respondeu a esta mensagem do bot: «{(msg['reply_to_message'].get('text') or '')[:600]}»"
    job = painel_ia.pedir(tipo, texto, projeto=_projeto(chave, texto), contexto=contexto, origem=f"telegram:{chave}")
    est["pedidos"][job["id"]] = {"bot": chave, "msg": msg["message_id"], "tipo": job["tipo"], "avisado": False}
    _mandar(bot, ("Entendi, vou ver isso e já te respondo aqui." if tipo == "pergunta" else
                  "Entendi o conserto. Vou investigar e te mando o plano ANTES de mexer em qualquer coisa."),
            msg["message_id"])
    log(f"{chave}: {job['tipo']} {job['id']} <- {texto[:80]}")


def _resposta_a_pedido(est, chave, bot, msg):
    """Dono respondeu (reply) a uma mensagem nossa: aplicar / não / desfazer."""
    import painel_ia
    alvo = est["por_msg"].get(f"{chave}:{msg['reply_to_message']['message_id']}")
    if not alvo:
        return False
    texto = (msg.get("text") or "").strip()
    jid = alvo["job"]
    try:
        if alvo["tipo"] == "propor" and SIM.search(texto):
            novo = painel_ia.aplicar(jid)
            est["pedidos"][novo["id"]] = {"bot": chave, "msg": msg["message_id"], "tipo": "aplicar", "avisado": False}
            _mandar(bot, "Aplicando agora (cada arquivo tem backup). Te aviso quando terminar.", msg["message_id"])
            log(f"{chave}: aplicar {jid} -> {novo['id']}")
            return True
        if alvo["tipo"] == "propor" and NAO.search(texto):
            _mandar(bot, "Ok, descartei a proposta. Nada foi mudado.", msg["message_id"])
            return True
        if alvo["tipo"] == "aplicar" and DESFAZER.search(texto):
            painel_ia.desfazer(jid, quem="dona (Telegram)")  # 24/10 (achado 9)
            _mandar(bot, "Desfeito: os arquivos voltaram como estavam antes do conserto.", msg["message_id"])
            log(f"{chave}: desfazer {jid}")
            return True
    except Exception as e:  # noqa: BLE001
        _mandar(bot, f"Não consegui: {e}", msg["message_id"])
        return True
    return False


def _entregar(est, bots):
    """Pedidos terminados: manda a resposta no bot de origem."""
    import painel_ia
    try:  # 23/10: resultados e perguntas das melhorias contínuas saem no bot de produção (DESFAZER/APLICAR valem)
        import melhoria_continua
        # 24/10 (achado 1): o aviso da auditoria final cai num job que JÁ foi avisado (o "✅ Feito"): sem isto ele
        # nunca saía. Cada aviso novo da auditoria (por_que diferente) reabre o job uma vez; o registro fica aqui
        aud = (melhoria_continua._estado().get("auditoria_dona") or {})
        enviados = est.setdefault("auditoria_enviada", {})
        for jid in melhoria_continua.para_entregar():
            info = est["pedidos"].setdefault(jid, {"bot": "producao", "msg": None, "tipo": "melhoria", "avisado": False})
            a = aud.get(jid)
            marca = f"{(a or {}).get('veredito')}|{(a or {}).get('por_que')}"[:300]
            if a and enviados.get(jid) != marca:
                info["avisado"] = False
                info["auditoria"] = marca
        if len(enviados) > 200:
            est["auditoria_enviada"] = dict(list(enviados.items())[-200:])
    except Exception as e:  # noqa: BLE001
        log(f"melhorias contínuas: não peguei o que entregar ({type(e).__name__}: {e})")
    for jid, info in list(est["pedidos"].items()):
        if info.get("avisado"):
            continue
        job = painel_ia.ler(jid)
        if not job or job.get("status") in ("fila", "rodando"):
            continue
        bot = bots.get(info["bot"])
        info["avisado"] = True
        if not bot:
            continue
        resp = re.sub(r"\n?STATUS:.*$", "", (job.get("resposta") or job.get("detalhe") or "(sem resposta)").strip(),
                      flags=re.S | re.I).strip()
        st = job.get("status_ia")
        if job["tipo"] == "propor" and st == "PROPOSTA":
            rodape = "\n\n➡️ Responda esta mensagem com APLICAR pra eu fazer, ou NÃO pra descartar."
        elif job["tipo"] == "aplicar" and st == "CONSERTEI":
            rodape = "\n\n✅ Feito. Se não gostou, responda esta mensagem com DESFAZER."
        elif job.get("status") == "erro":
            rodape = "\n\n⚠️ O agente não conseguiu terminar."
        else:
            rodape = ""
        texto = None
        try:  # 23/10: melhorias contínuas -> mensagem curta e em português simples (melhoria_continua.texto_entrega)
            import melhoria_continua
            if melhoria_continua.eh_melhoria(job):
                texto = melhoria_continua.texto_entrega(job)
        except Exception as e:  # noqa: BLE001
            log(f"melhorias contínuas: texto simples falhou ({type(e).__name__}: {e})")
        mid = _mandar(bot, texto or (resp[:3500] + rodape), info["msg"])
        if info.get("auditoria"):
            est.setdefault("auditoria_enviada", {})[jid] = info.pop("auditoria")
        if mid:
            est["por_msg"][f"{info['bot']}:{mid}"] = {"job": jid, "tipo": job["tipo"]}
        log(f"{info['bot']}: respondido {jid} ({job['tipo']}, {st})")


def ciclo(est, bots):
    for chave, bot in bots.items():
        try:
            r = _api(bot["bot_token"], "getUpdates", {"offset": est["offset"].get(chave, 0), "timeout": 0,
                                                       "allowed_updates": ["message"]})
        except Exception as e:  # noqa: BLE001
            log(f"{chave}: getUpdates falhou ({type(e).__name__})")
            continue
        for upd in r.get("result") or []:
            est["offset"][chave] = upd["update_id"] + 1
            msg = upd.get("message") or {}
            if str((msg.get("chat") or {}).get("id")) != str(bot["chat_id"]) or not (msg.get("text") or "").strip():
                continue  # só o dono
            if (msg.get("text") or "").strip().startswith("/start"):
                teclado = None
                if chave == "producao":
                    try:
                        import melhoria_continua
                        teclado = melhoria_continua.TECLADO
                    except Exception:  # noqa: BLE001
                        pass
                _mandar(bot, f"Oi! Aqui eu atendo sobre {TEMAS[chave][1]}. Pode perguntar ou pedir conserto."
                        + ("\nOs botões embaixo ligam, param e mostram as melhorias contínuas." if teclado else ""),
                        teclado=teclado)
                continue
            if msg.get("reply_to_message") and _resposta_a_pedido(est, chave, bot, msg):
                continue
            if chave == "producao" and re.match(r"^\s*melhorias?\b", msg.get("text") or "", re.I):
                try:  # 23/10: liga/para/status/prompt das melhorias contínuas (melhoria_continua.py)
                    import melhoria_continua
                    _mandar(bot, melhoria_continua.comando(msg["text"]), msg["message_id"],
                            teclado=melhoria_continua.TECLADO)
                    if re.match(r"^\s*melhorias?\s+revis", msg["text"], re.I):
                        _mandar_documento(bot, melhoria_continua.REVISAO,
                                          "Pacote de revisão: anexe este arquivo no chat de IA junto com o texto acima.")
                except Exception as e:  # noqa: BLE001
                    _mandar(bot, f"Não consegui mexer nas melhorias: {e}", msg["message_id"])
                continue
            if chave == "producao" and re.match(r"^\s*gemini\b", msg.get("text") or "", re.I):
                try:  # 26/10: notas e status do aprendizado do Gemini nos vigias (gemini_aprendiz.py)
                    import gemini_aprendiz
                    _mandar(bot, gemini_aprendiz.comando(msg["text"]), msg["message_id"])
                except Exception as e:  # noqa: BLE001
                    _mandar(bot, f"Não consegui mexer no aprendizado do Gemini: {e}", msg["message_id"])
                continue
            _novo_pedido(est, chave, bot, msg)
        _gravar(est)
    _entregar(est, bots)
    _gravar(est)


def rodar(minutos):
    if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < 120:
        return  # já há um atendente vivo (ele renova a trava a cada volta)
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    est, fim = _ler(), time.time() + minutos * 60
    est.setdefault("offset", {})
    est.setdefault("pedidos", {})
    est.setdefault("por_msg", {})
    try:
        while time.time() < fim:
            TRAVA.write_text(str(time.time()), encoding="utf-8")
            try:
                ciclo(est, _bots())
            except Exception as e:  # noqa: BLE001
                log(f"ciclo falhou ({type(e).__name__}: {e})")
            time.sleep(6)
    finally:
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--rodar" in sys.argv:
        i = sys.argv.index("--rodar")
        rodar(float(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 39)
    else:
        print("bots atendidos:", ", ".join(_bots()))
