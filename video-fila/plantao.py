"""plantao.py — o Funcionário de Plantão no Telegram (@plantao_emerson_bot), sempre de pé (dona 01/11: "mandei um oi
mas não respondeu; se eu mandar algo, mesmo que esteja desligado, ele tem que responder, ou até ligar se eu pedir").

Por quê separado: quem lia o bot era o notificar_telegram (tarefa NotificarTelegram, 5 em 5 min), que faz tudo em fila —
YouTube, Drive (rclone lsjson -R), comentários. Em 01/11 15:17 uma rodada travou 40 min e, com a tarefa em "IgnoreNew",
nenhuma outra começou: a mensagem dela ficou parada no bot. Aqui só o plantão, a cada minuto, nada de rede além do
Telegram. Uma trava de arquivo evita duas rodadas juntas.

  ping / oi / olá        -> responde NA HORA, sem IA ("estou aqui" + o que está ligado/desligado)
  status                 -> resumo da produção na hora (vigia_telegram.status)
  liga X / desliga X     -> controle.py (produção/postagem de cada projeto)  — "ligado"/"desligado" no controle.json
  qualquer outra coisa   -> fila do vigia (agente) com bot="plantao": ele responde e vai contando o que faz

    python plantao.py             (tarefa PlantaoTelegram, a cada 1 min, escondida)
    python plantao.py --uma "oi"  (testa a resposta sem o Telegram)
"""
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
BOTS = Path(r"D:\postador-de-videos\config\telegram_bots.json")
CHAT = Path(r"D:\postador-de-videos\config\telegram.json")
EST = BASE / "estado" / "plantao.json"
TRAVA = BASE / "estado" / "plantao.lock"
LOG = BASE / "estado" / "plantao.log"
FILA_VIGIA = Path(r"D:\hipercool-videos\workspace\vigia_perguntas.jsonl")
VIGIA = [r"D:\hipercool-videos\venv\Scripts\python.exe", "-X", "utf8", r"D:\hipercool-videos\bin\vigia_telegram.py",
         "--fila"]
SEM_JANELA = 0x08000000

OI = re.compile(r"^\W*(oi+|ol[aá]|opa|e\s*a[ií]|fala|bom\s*dia|boa\s*(tarde|noite)|tudo\s*bem|ping|t[aá]\s*a[ií]|"
                r"est[aá]\s*a[ií]|alguem|algu[eé]m)\W*$", re.I)
STATUS = re.compile(r"^\W*(status|s|estado|como (est[aá]|t[aá])|o que (est[aá]|t[aá]) rodando)\W*$", re.I)
LIGA = re.compile(r"^\W*(liga|ligar|ligue|religa|desliga|desligar|desligue|para|parar|pare)\b\s*(.*)$", re.I)


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {msg}\n")
    except OSError:
        pass


def _bot():
    b = json.loads(BOTS.read_text(encoding="utf-8-sig"))["plantao"]
    return b["bot_token"], str(b["chat_id"])


def _api(metodo, dados, timeout=20):
    token, _chat = _bot()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{metodo}",
                                 data=urllib.parse.urlencode(dados).encode("utf-8"), method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def enviar(texto, responder_a=None):
    _token, chat = _bot()
    dados = {"chat_id": chat, "text": texto[:3900], "disable_web_page_preview": "true"}
    if responder_a:
        dados["reply_to_message_id"] = str(responder_a)
    try:
        ok = _api("sendMessage", dados).get("ok")
        log(f"respondi ({'ok' if ok else 'recusado'}): {texto[:80]!r}")
        return ok
    except Exception as e:  # noqa: BLE001
        log(f"envio falhou: {e}")
        return False


APELIDOS = {"manhwa": "hipercool", "hiper": "hipercool", "hipercool": "hipercool", "parceiro": "parceiro",
            "parceiros": "parceiro", "cortes": "cortes", "corte": "cortes", "anime": "anime", "animes": "anime",
            "react": "manhwa-react", "manhwa-react": "manhwa-react", "historia": "historias", "historias": "historias",
            "histórias": "historias", "veo": "veo", "msenergy": "msenergy", "ms": "msenergy", "solar": "msenergy",
            "controlador": "controlador", "postador": "postador", "desktop": "desktop", "tudo": "tudo", "todos": "tudo",
            "geral": "tudo"}


def _controle():
    """(ligados, desligados) pelo controle.py ("projeto etapa"); ([], []) se não deu."""
    try:
        sys.path.insert(0, str(BASE))
        import controle
        lig, des = [], []
        for p in controle.PROJETOS:
            for e in (("producao",) if p == "desktop" else controle.ETAPAS):
                (lig if controle.ligado(p, e)[0] else des).append(
                    f"{controle.NOMES.get(p, p)} {'produção' if e == 'producao' else 'postagem'}")
        return lig, des
    except Exception as e:  # noqa: BLE001
        log(f"controle: {e}")
        return [], []


def _ligar(texto):
    """'liga hipercool', 'desliga postagem parceiro', 'liga tudo'... -> controle.py; devolve a resposta em texto."""
    m = LIGA.match(texto)
    verbo, alvo = m.group(1).lower(), (m.group(2) or "").strip().lower()
    ligar = verbo.startswith(("liga", "ligu", "relig"))
    projeto = next((APELIDOS[w] for w in re.findall(r"[\wçãáéíóúâêô-]+", alvo) if w in APELIDOS), None)
    if not projeto:
        return ("Liga ou desliga o quê? Exemplos: \"liga manhwa\", \"desliga postagem parceiro\", \"liga produção "
                "anime\", \"liga tudo\". Projetos: " + ", ".join(sorted(set(APELIDOS.values()))))
    etapas = (["postagem"] if "post" in alvo else ["producao"] if "produ" in alvo else ["producao", "postagem"])
    if projeto == "desktop":
        etapas = ["producao"]
    saida = ""
    for etapa in etapas:
        cmd = [sys.executable, "-X", "utf8", str(BASE / "controle.py"), "ligar" if ligar else "desligar", projeto,
               etapa, "pelo plantão (Telegram)"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                               creationflags=SEM_JANELA)
            saida = (r.stdout or r.stderr or "").strip()
        except Exception as e:  # noqa: BLE001
            saida = f"não consegui rodar o controle ({e})"
    log(f"{'ligar' if ligar else 'desligar'} {projeto} {etapas}: {saida[:200]}")
    atencao = [l for l in saida.splitlines() if l.startswith("atenção")]
    nome = {"producao": "produção", "postagem": "postagem"}
    return (f"{'✅ Liguei' if ligar else '⏸ Desliguei'}: {projeto} — {' e '.join(nome[e] for e in etapas)}"
            + ("\n⚠️ " + "\n⚠️ ".join(a.removeprefix("atenção: ") for a in atencao) if atencao else "")
            + "\n\n" + saida[-1500:])


def resposta_rapida(texto):
    """Resposta sem IA, ou None (vai pro agente)."""
    if OI.match(texto):
        lig, des = _controle()
        partes = ["👷 Estou aqui, de plantão."]
        if des:
            partes.append("Desligado agora: " + ", ".join(des[:12]))
        partes.append("Pode perguntar ou pedir conserto que eu chamo o agente e vou contando o que faço. "
                      "Mande \"status\" pro resumo, ou \"liga X\" / \"desliga X\".")
        return "\n".join(partes)
    if LIGA.match(texto):
        return _ligar(texto)
    if STATUS.match(texto) and len(texto) <= 40:
        try:
            sys.path.insert(0, r"D:\hipercool-videos\bin")
            import vigia_telegram
            return vigia_telegram.status()
        except Exception as e:  # noqa: BLE001
            return f"Não consegui montar o status agora ({type(e).__name__}). Tente de novo em 1 min."
    return None


def _para_agente(texto, mid, ctx):
    item = {"texto": texto, "message_id": mid, "bot": "plantao",
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if ctx:
        item["contexto_reply"] = ctx[:500]
    FILA_VIGIA.parent.mkdir(parents=True, exist_ok=True)
    with open(FILA_VIGIA, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    subprocess.Popen(VIGIA, cwd=r"D:\hipercool-videos", creationflags=SEM_JANELA,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def rodada():
    if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < 60:  # rodada dura no máximo 50 s (_vigia_tempo)
        return
    TRAVA.write_text("1")
    try:
        try:
            est = json.loads(EST.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            est = {}
        if "offset" not in est:  # 1ª vez: continua de onde o notificar_telegram parou (não perde nem repete)
            try:
                est["offset"] = json.loads(Path(r"D:\postador-de-videos\config\telegram_estado.json")
                                           .read_text(encoding="utf-8")).get("tg_update_id_plantao", 0)
            except (OSError, ValueError):
                est["offset"] = 0
        dono = json.loads(CHAT.read_text(encoding="utf-8")).get("chat_id")
        r = _api("getUpdates", {"offset": est["offset"], "timeout": 0, "allowed_updates": '["message"]'})
        for upd in r.get("result") or []:
            est["offset"] = upd["update_id"] + 1
            EST.write_text(json.dumps(est), encoding="utf-8")  # grava já: erro abaixo não repete a mensagem
            msg = upd.get("message") or {}
            texto, mid = (msg.get("text") or "").strip(), msg.get("message_id")
            if not texto or msg.get("chat", {}).get("id") != dono:
                continue
            log(f"dona: {texto[:200]}")
            rapida = resposta_rapida(texto)
            if rapida:
                enviar(rapida, mid)
                continue
            enviar("Recebido — chamando o agente. Vou te contando o que ele faz.", mid)
            _para_agente(texto, mid, (msg.get("reply_to_message") or {}).get("text"))
        EST.write_text(json.dumps(est), encoding="utf-8")
    finally:
        TRAVA.unlink(missing_ok=True)


def _vigia_tempo(limite_s=50):
    """01/11: rodada pela tarefa ficou parada 2+ min (CPU 0, sem conexão) segurando a trava; sem isto a próxima
    rodada não começa. Passou do limite = encerra o processo (a trava sai junto) e a tarefa roda de novo em 1 min."""
    import os
    import threading

    def fim():
        log(f"rodada passou de {limite_s}s — encerrada")
        TRAVA.unlink(missing_ok=True)
        os._exit(3)
    t = threading.Timer(limite_s, fim)
    t.daemon = True
    t.start()


if __name__ == "__main__":
    import socket
    socket.setdefaulttimeout(20)
    _vigia_tempo()
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.argv[1:2] == ["--uma"]:
        print(resposta_rapida(" ".join(sys.argv[2:])) or "(vai pro agente)")
    else:
        rodada()
