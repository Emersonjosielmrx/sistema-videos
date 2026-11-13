#!/usr/bin/env python3
"""O vigia RESPONDE no Telegram — pelo MESMO bot do postador (pedido do dono, 17/10/2026).

Por que assim: o bot que o dono usa é o do postador (D:\\postador-de-videos\\config\\telegram.json), e quem lê as
mensagens dele é a tarefa NotificarTelegram (notificar_telegram.responder, a cada 5 min). Dois programas lendo o mesmo
bot (getUpdates) roubam mensagens um do outro, então o vigia NÃO lê o bot: o notificar_telegram, quando a mensagem do
dono não é resposta a um comentário do YouTube, grava a pergunta em workspace/vigia_perguntas.jsonl e chama
`vigia_telegram.py --fila`. Aqui a pergunta é respondida e a resposta volta pelo mesmo bot, citando a mensagem dele.

  status / s / como está / produção -> resumo NA HORA, sem IA (fila de render de todos os projetos, render do
                                        hipercool, últimos vídeos postados, próximos Shorts)
  ajuda                              -> lista de comandos
  qualquer outra coisa               -> agente (Claude Code headless pelo proxy, kr/claude-sonnet-4.5 — o mesmo do
                                        trocador do desktop), com as regras duras e o rastro do bin/vigia_agente.py

    python bin/vigia_telegram.py --fila            (o que o notificar_telegram chama)
    python bin/vigia_telegram.py --status          (imprime o resumo, pra testar)
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vigia_agente as va  # noqa: E402

FILA = va.PROJ / "workspace" / "vigia_perguntas.jsonl"
FEITAS = va.PROJ / "workspace" / "vigia_perguntas_feitas.jsonl"
TRAVA = va.PROJ / "workspace" / "vigia_telegram.lock"
BOT = Path(r"D:\postador-de-videos\config\telegram.json")
STATUS = re.compile(r"^\W*(status|s|estado|como (est[aá]|t[aá])|produ[cç][aã]o|o que (est[aá]|t[aá]) rodando)\W*", re.I)


BOTS = Path(r"D:\postador-de-videos\config\telegram_bots.json")
_BOT_ATUAL = [None]  # 01/11: a pergunta veio do bot do plantão -> a resposta volta por ele (item["bot"])


def _bot():
    d = json.loads(BOT.read_text(encoding="utf-8"))
    if _BOT_ATUAL[0]:
        try:
            b = json.loads(BOTS.read_text(encoding="utf-8-sig"))[_BOT_ATUAL[0]]
            return b["bot_token"], str(b["chat_id"])
        except (OSError, ValueError, KeyError):
            pass
    return d["bot_token"], str(d["chat_id"])


def enviar(texto, responder_a=None):
    token, chat = _bot()
    for i in range(0, max(1, len(texto)), 3900):
        dados = {"chat_id": chat, "text": texto[i:i + 3900] or "(vazio)", "disable_web_page_preview": "true"}
        if responder_a and i == 0:
            dados["reply_to_message_id"] = str(responder_a)
        try:
            with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage",
                                        data=urllib.parse.urlencode(dados).encode(), timeout=20) as r:
                r.read()
        except Exception as e:  # noqa: BLE001
            va.log(f"[telegram] envio falhou: {e}")


def _ultima(arq, padrao=None):
    try:
        linhas = Path(arq).read_text(encoding="utf-8", errors="replace").strip().splitlines()
    except OSError:
        return ""
    if padrao:
        linhas = [l for l in linhas if re.search(padrao, l)]
    return (linhas[-1] if linhas else "").strip()[:200]


def status():
    """Resumo da produção sem IA: o que o dono quer ver quando pergunta 'como está'."""
    out = [f"📊 Produção — {datetime.now():%d/%m %H:%M}"]
    try:  # fila comum de render (todos os projetos, PC1)
        sys.path.insert(0, r"D:\video-fila")
        import fila_render
        rod = fila_render._ler("rodando", 6)
        esp = sorted(fila_render._ler("esperando", 24), key=lambda x: (x[1]["prio"], x[1]["desde"]))
        out.append("\n🖥️ PC1 renderizando: " + (", ".join(f"{d['projeto']} ({d['rotulo'][:45]}, {int((time.time() - d['desde']) / 60)} min)"
                                                      for _p, d in rod) or "nada"))
        if esp:
            out.append("⏳ Esperando: " + ", ".join(f"{d['projeto']} ({d['rotulo'][:35]})" for _p, d in esp))
        out.append("Prioridade: " + ", ".join(f"{k}={v}" for k, v in sorted(fila_render._cfg().get("prioridade", {}).items(), key=lambda x: x[1])))
    except Exception as e:  # noqa: BLE001
        out.append(f"(fila comum indisponível: {e})")
    try:
        sys.path.insert(0, r"D:\video-fila")
        import maquinas
        for pc in ("pc2", "desktop"):
            m = maquinas.medir(pc)
            out.append(f"{'💤' if m.get('ocioso') else '⚙️'} {pc}: {'livre' if m.get('ocioso') else 'ocupado'} — {m.get('motivo', '')}"[:160])
    except Exception:  # noqa: BLE001
        pass
    try:  # status único (D:\video-fila\status_videos.py): botões de todos os projetos + canais do cadastro único
        import status_videos
        out.append(f"\n🎛️ Botões: {status_videos.controle_curto()}")
        out.append(f"🤖 Controlador: {status_videos.controlador_curto()}")
        out.append(f"📺 Canais: {status_videos.canais_curto()}")
    except Exception as e:  # noqa: BLE001
        out.append(f"(status único indisponível: {type(e).__name__})")
    # hipercool
    import fila
    est = fila.ler_estado()
    caps = fila.capitulos()
    rod = [k for k, *_ in caps if (est.get(k) or {}).get("render") == "rodando"]
    prontos = [k for k, *_ in caps if (est.get(k) or {}).get("situacao") == "pronto"]
    revisar = [k for k, *_ in caps if (est.get(k) or {}).get("situacao") in ("revisar", "revisar_pendente")]
    feitos = [k for k, *_ in caps if (est.get(k) or {}).get("render") == "ok"]
    nome = lambda ks: ", ".join(k.split("-cap")[-1].lstrip("0") for k in ks) or "-"  # noqa: E731
    out.append(f"\n🎬 Hipercool (The Inheritor, {len(caps)} caps): fila {'DESLIGADA' if fila.DESLIGADA.exists() else 'ligada'}")
    out.append(f"• renderizando: cap {nome(rod)}")
    for k in rod:
        out.append(f"  último passo: {_ultima(fila.PROJECT / 'logs' / f'fila_{k}.log')[:150]}")
    out.append(f"• feitos: {len(feitos)} | prontos: cap {nome(prontos)}")
    if revisar:
        out.append(f"• esperando você liberar (análise reprovou): cap {nome(revisar)}")
    out.append(f"• Shorts: {_ultima(fila.PROJECT / 'logs' / 'shorts_2h.log')[16:150] or '-'}")
    # últimos uploads (ledger do postador, todos os projetos)
    try:
        # 23/10: o bin do postador ficava NA FRENTE do sys.path pro resto do processo — import tardio de claude_client,
        # effects_engine... (20 módulos com o mesmo nome e outra versão lá) pegava o do postador. Mesmo defeito que
        # matou Shorts no recap (monitor_bordoes). O politica só usa biblioteca padrão: entra, importa e sai.
        _pb = r"D:\postador-de-videos\bin"
        sys.path.append(_pb)
        try:
            import politica
        finally:
            while _pb in sys.path:
                sys.path.remove(_pb)
        ups = [r for r in politica._ler_ledger() if r.get("video_id")][-5:]
        out.append("\n📤 Últimos uploads:")
        out += [f"• {str(r.get('ts', ''))[5:16].replace('T', ' ')} {r.get('canal', '')[:22]}: {r.get('arquivo', '')[:40]} https://youtu.be/{r['video_id']}"
                for r in reversed(ups)]
    except Exception as e:  # noqa: BLE001
        out.append(f"(ledger indisponível: {e})")
    vg = _ultima(r"D:\video-fila\vigia_geral.log")
    if vg:
        out.append(f"\n👀 Vigia geral (outros projetos): {vg[:180]}")
    out.append(f"🛡️ Vigia hipercool: {_ultima(va.LOGS / 'vigia.log')[16:170]}")
    return "\n".join(out)


AJUDA = ("Comandos: 'status' (ou 'como está') = resumo na hora, sem gastar IA. Qualquer outra mensagem vai pro agente "
         "(Sonnet 4.5 do Kiro), que investiga e age com as regras do vigia — ele NÃO posta, não liga/desliga fila, não "
         "apaga vídeo e não afrouxa censura — e deixa tudo em docs/VIGIA_DIARIO.md. Resposta a mensagem de comentário "
         "do YouTube continua indo pro YouTube, como antes.")


def _historico_chat(limite=10):
    """Últimas mensagens trocadas com o dono (perguntas + respostas) para dar contexto ao agente."""
    linhas = []
    try:
        for arq in (FEITAS, FILA):
            if not arq.exists():
                continue
            for l in arq.read_text(encoding="utf-8").splitlines()[-limite:]:
                try:
                    linhas.append(json.loads(l))
                except ValueError:
                    pass
    except OSError:
        pass
    linhas.sort(key=lambda x: x.get("ts", ""))
    if not linhas:
        return ""
    out = ["HISTÓRICO RECENTE DO CHAT (últimas mensagens do dono pelo Telegram):"]
    for m in linhas[-limite:]:
        ts = m.get("ts", "")[:16]
        out.append(f"  [{ts}] «{m.get('texto', '')[:200]}»")
    return "\n".join(out)


SAUDACAO = re.compile(r"^\W*(ol[aá]|oi|hey|hi|hello|e\s*a[ií]|fala|bom\s*dia|boa\s*(tarde|noite)|tudo\s*bem|\?\??|\.+)\W*$", re.I)


ACAO = re.compile(r"(consert|corrig|fix|edit|mude|alter|modific|implemen|cri[ea]|delet|apag|reinici|relanc|restau|refaz)", re.I)


def responder(item):
    texto, mid = (item.get("texto") or "").strip(), item.get("message_id")
    va.log(f"[telegram] dono: {texto[:200]}")
    if STATUS.match(texto) and len(texto) <= 40:
        enviar(status(), mid)
        return
    if texto.lower().strip("/ ") in ("ajuda", "start", "help"):
        enviar(AJUDA, mid)
        return
    if SAUDACAO.match(texto) and len(texto) <= 20:
        enviar("Oi! Mande 'status' pro resumo da produção, ou pergunte qualquer coisa que eu chamo o agente.", mid)
        return
    precisa_acao = bool(ACAO.search(texto))
    modo = "vigia" if precisa_acao else "consulta"
    turns = 30 if precisa_acao else 10
    enviar("Recebido — " + ("chamando o agente pra investigar/agir." if precisa_acao
                             else "consultando..."), mid)
    hist = _historico_chat()
    ctx_reply = item.get("contexto_reply", "")
    ctx = ""
    if ctx_reply:
        ctx = f"\n  (O dono respondeu a esta mensagem do bot: «{ctx_reply}»)\n"
    motivo = (f"- MENSAGEM DO DONO pelo Telegram: «{texto}»{ctx}\n"
              f"  {hist}\n\n"
              "  Se ele perguntar do estado da produção, use este resumo como ponto de partida:\n"
              + status() + "\n\n"
              "FERRAMENTAS DE CONSULTA disponíveis (rode com o venv do hipercool):\n"
              "  python bin/consultar_producao.py views                  # views por canal (2 dias)\n"
              "  python bin/consultar_producao.py views --dias 7         # views últimos 7 dias\n"
              "  python bin/consultar_producao.py views --canal \"Nome\"   # um canal específico\n"
              "  python bin/consultar_producao.py ranking                # top vídeos por views (48h)\n"
              "  python bin/consultar_producao.py comentarios            # comentários recentes\n"
              "  python bin/consultar_producao.py comentarios --canal X  # comentários de um canal\n"
              "  python bin/consultar_producao.py uploads --n 20         # últimos uploads\n"
              "  python bin/consultar_producao.py canais                 # lista de canais com inscritos\n"
              "  python bin/consultar_producao.py filas                  # filas de postagem\n"
              "  D:\\postador-de-videos\\venv\\Scripts\\python.exe -X utf8 D:\\postador-de-videos\\bin\\stats_views.py --dias 3  # views detalhadas\n"
              "Use estas ferramentas SEMPRE que o dono perguntar sobre views, ranking, comentários, uploads, canais ou filas.\n")
    plantao = _BOT_ATUAL[0] == "plantao"  # 01/11 (dona): no plantão ele conta o que está fazendo, como no chat
    res = va.chamar_agente(motivo, avisar=False, max_turns=turns, modo=modo,
                           progresso=(lambda t: enviar(t, mid)) if plantao else None)
    if not res:
        enviar("O agente já está rodando outra tarefa. Mande de novo em alguns minutos (ou 'status' pro resumo na hora).", mid)
        return
    st, detalhe, saida = res
    resp = [l.split("RESPOSTA:", 1)[1].strip() for l in saida.splitlines() if "RESPOSTA:" in l]
    enviar((resp[-1] if resp else detalhe or "(o agente não devolveu resposta — ver logs/vigia_agente_*.log)") + f"\n\n[{st}]", mid)


def processar_fila():
    if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < va.AGENTE_TIMEOUT_MIN * 60 + 300:
        return  # outro --fila já está respondendo; ele pega o que chegou depois
    TRAVA.write_text("1")
    try:
        while FILA.exists():
            linhas = FILA.read_text(encoding="utf-8").splitlines()
            FILA.unlink()
            for l in linhas:
                try:
                    item = json.loads(l)
                except ValueError:
                    continue
                TRAVA.write_text("1")
                _BOT_ATUAL[0] = item.get("bot")
                try:
                    responder(item)
                except Exception as e:  # noqa: BLE001
                    va.log(f"[telegram] erro respondendo: {e}")
                    enviar(f"Deu erro ao responder: {str(e)[:200]}", item.get("message_id"))
                with open(FEITAS, "a", encoding="utf-8") as f:
                    f.write(json.dumps({**item, "respondido_em": datetime.now().isoformat(timespec="seconds")},
                                       ensure_ascii=False) + "\n")
    finally:
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    if "--status" in sys.argv:
        print(status())
    else:
        processar_fila()
