# -*- coding: utf-8 -*-
"""anime_health_monitor — vigia a cadeia de recap de anime e AUTO-CORRIGE o que
e seguro, avisando o resto no Telegram.

Contexto do incidente (2026-07-31): a noite inteira saiu 0 recap. Causa dupla:
  1) o cron 'AnimeRecapNoturno' NAO estava registrado no Agendador -> ninguem
     acordava o supervisor de madrugada.
  2) o _dispatch_deitado.py morria com UnicodeEncodeError ('->') ao imprimir a
     resposta do worker no cp1252 -> render podia ter sido feito e o resultado
     se perdia.

Este monitor roda de hora em hora e checa:
  A) tarefa 'AnimeOcioso' registrada?           -> alerta (desde 17/10; o noturno foi aposentado, não recriar)
  B) worker PC2 responde?                       -> alerta (nao da pra consertar daqui)
  C) saiu recap novo na ultima janela noturna?  -> alerta se a noite passou seca
  D) algum log recente com Traceback/erro?      -> alerta com o trecho

AUTO-FIX so faz o que e reversivel/seguro (re-registrar cron). O resto vira
alerta com diagnostico pronto. Sempre loga em logs/anime_health_monitor.log.

Uso:
    python bin\\anime_health_monitor.py            # 1 checagem
    python bin\\anime_health_monitor.py --auto-fix # idem, aplicando correcoes seguras
    python bin\\anime_health_monitor.py --dry-run  # so reporta, nao corrige
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_BASE = Path(__file__).resolve().parent.parent          # D:\recapd-ambientes\producao
_LOGS = _BASE / "logs"
_LOGS.mkdir(exist_ok=True)
_MON_LOG = _LOGS / "anime_health_monitor.log"
_STATE = _LOGS / "anime_health_monitor_state.json"

# Onde os recaps chegam neste PC (destino do PC2).
_SAIDA_RECAP = Path(r"D:\hipercool-materiais\animes recap")

# Worker PC2: tenta Tailscale primeiro, depois LAN.
_WORKERS = [("100.125.7.77", 8772), ("192.168.18.7", 8771)]

# 17/10: o turno da noite (AnimeRecapNoturno, cron_anime_noturno.bat) foi trocado pelo modo ocioso (D:\video-fila\ocioso.py).
# Recriar o noturno aqui religaria o que o dono desligou: só confere se o AnimeOcioso existe e avisa.
_CRON_NOME = "AnimeOcioso"

# Janela noturna em que a producao deveria acontecer.
_JANELA_INI_H = 0
_JANELA_FIM_H = 6


def log(msg):
    linha = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(linha, flush=True)
    try:
        with open(_MON_LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Telegram (opcional — so avisa se achar token). Nao quebra se nao houver.
# ---------------------------------------------------------------------------
def _tg_token():
    tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    if tok:
        return tok
    for nome in ("telegram-aviso-video-gerado.json", "telegram.json"):
        p = _BASE / "secrets" / nome
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")).get("bot_token")
            except Exception:
                pass
    # reusa o helper do projeto se ele tiver token configurado
    try:
        sys.path.insert(0, str(_BASE / "bin"))
        import _tg_safe  # noqa
        return _tg_safe._token()
    except Exception:
        return None


def avisar(texto, chat_id=None):
    """Manda alerta no Telegram se der; sempre loga. Retorna True se enviou."""
    log(f"ALERTA: {texto.splitlines()[0] if texto else ''}")
    try:  # 19/10: portão único — o MESMO alerta saía toda hora (24/dia); repetido em 12 h não sai mais
        if r"D:\video-fila" not in sys.path:
            sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "monitor do anime", importante=True, html_ok=False)
        return True
    except Exception as e:  # noqa: BLE001
        log(f"  (portão de avisos fora: {e}; mando direto)")
    token = _tg_token()
    chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not chat:
        try:
            import _tg_safe  # noqa — já no sys.path por _tg_token; chat do mesmo bot do token
            chat = _tg_safe.chat()
        except Exception:
            chat = "7988990790"
    if not token:
        log("  (Telegram sem token — alerta so no log. Defina TELEGRAM_BOT_TOKEN "
            "ou secrets/telegram-aviso-video-gerado.json pra receber no celular.)")
        return False
    try:
        import urllib.parse
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": str(chat), "text": texto,
            "disable_web_page_preview": "true",
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:
        log(f"  (falha ao enviar Telegram: {e})")
        return False


# ---------------------------------------------------------------------------
# Checagens
# ---------------------------------------------------------------------------
def check_cron(auto_fix):
    """A) cron registrado? AUTO-FIX seguro: re-registra."""
    try:
        r = subprocess.run(
            ["schtasks", "/query", "/tn", _CRON_NOME],
            capture_output=True, text=True, encoding="cp850",
            errors="replace", timeout=15)
        existe = r.returncode == 0
    except Exception as e:
        return {"ok": False, "detalhe": f"schtasks falhou: {e}", "corrigido": False}

    if existe:
        return {"ok": True, "detalhe": "cron registrado", "corrigido": False}

    return {"ok": False, "corrigido": False,
            "detalhe": f"tarefa '{_CRON_NOME}' NAO registrada (pythonw D:\\video-fila\\ocioso.py a cada 15 min)"}


def check_worker():
    """B) worker PC2 responde em algum endereco?"""
    for host, port in _WORKERS:
        try:
            with urllib.request.urlopen(
                    f"http://{host}:{port}/health", timeout=4) as r:
                d = json.loads(r.read().decode())
                jobs = d.get("active_jobs", "?")
                return {"ok": True,
                        "detalhe": f"worker online {host}:{port} (jobs={jobs})"}
        except Exception:
            continue
    return {"ok": False,
            "detalhe": f"worker PC2 NAO responde em {_WORKERS} — "
                       "cheque se o PC2 esta ligado e o daemon rodando"}


def check_saida_recente(horas=12):
    """C) chegou recap novo nas ultimas N horas?"""
    if not _SAIDA_RECAP.exists():
        return {"ok": False, "detalhe": f"pasta de saida nao existe: {_SAIDA_RECAP}"}
    corte = time.time() - horas * 3600
    recentes = []
    for mp4 in _SAIDA_RECAP.rglob("*.mp4"):
        try:
            if mp4.stat().st_mtime >= corte:
                recentes.append(mp4)
        except Exception:
            pass
    if recentes:
        return {"ok": True, "detalhe": f"{len(recentes)} recap(s) nas ultimas {horas}h"}
    return {"ok": False,
            "detalhe": f"NENHUM recap novo em {_SAIDA_RECAP.name} nas ultimas {horas}h"}


def _erros_recentes(txt, corte_dt):
    """Linhas de erro depois do corte. Linha sem data herda a data da última linha datada acima dela (o Traceback de
    ontem no meio do log não conta como erro de agora). WARNING/INFO não é erro (23/10: o 429 da legenda virava alerta)."""
    ultimo, out = None, []
    for l in txt.splitlines():
        m = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", l)
        if m:
            try:
                ultimo = datetime.strptime(m.group(0), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        if (re.search(r"Error|Traceback|Exception", l) and not re.search(r"WARNING|\bINFO\b", l)
                and (ultimo is None or ultimo >= corte_dt)):
            out.append(l)
    return out


def check_logs_erro(horas=3):
    """D) algum log com erro nas últimas `horas` (o monitor roda de hora em hora)?"""
    corte = time.time() - horas * 3600
    achados = []
    corte_dt = datetime.fromtimestamp(corte)
    for lg in _LOGS.glob("*.log"):
        try:
            # 19/10: o proprio log repete os erros que achou e o alerta nunca parava
            if lg == _MON_LOG or lg.stat().st_mtime < corte:
                continue
            linhas = _erros_recentes(lg.read_text(encoding="utf-8", errors="replace"), corte_dt)
            if linhas:
                achados.append(f"{lg.name}: {linhas[-1][:140]}")
        except Exception:
            pass
    if not achados:
        return {"ok": True, "detalhe": "nenhum erro recente nos logs"}
    return {"ok": False, "detalhe": "erros recentes:\n  " + "\n  ".join(achados[:6]), "achados": achados[:6]}


def dentro_janela_ou_manha():
    """So cobra 'saiu recap?' de manha (depois da janela noturna)."""
    h = datetime.now().hour
    return _JANELA_FIM_H <= h <= 12  # entre 6h e meio-dia, a noite ja deveria ter produzido


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto-fix", action="store_true",
                    help="aplica correcoes seguras (re-registrar cron)")
    ap.add_argument("--dry-run", action="store_true",
                    help="so reporta, nao corrige (sobrepoe --auto-fix)")
    args = ap.parse_args()
    auto_fix = args.auto_fix and not args.dry_run

    log("=== anime_health_monitor: checagem iniciada "
        f"(auto_fix={auto_fix}) ===")

    problemas = []
    corrigidos = []
    try:
        antes = json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        antes = {}
    tipos_antes = set(antes.get("tipos") or [])
    erros_avisados = antes.get("erros_avisados") or {}
    tipos = set()

    c = check_cron(auto_fix)
    log(f"A) cron: {c['detalhe']}")
    # dono 22/10: um aviso por problema, em palavras simples (antes: um bloco "CRON/WORKER/LOGS" que ninguém entendia)
    simples = []
    if not c["ok"]:
        problemas.append(f"CRON: {c['detalhe']}")
        tipos.add("CRON")
        simples.append("A produção automática dos vídeos de anime está desligada: a tarefa que liga ela a cada "
                       "15 minutos sumiu do computador. O que fazer: pedir para religar.")

    w = check_worker()
    log(f"B) worker: {w['detalhe']}")
    if not w["ok"]:
        problemas.append(f"WORKER: {w['detalhe']}")
        tipos.add("WORKER")
        simples.append("O segundo computador (PC2) não está respondendo, então os vídeos de anime não estão "
                       "sendo feitos. O que fazer: ver se o PC2 está ligado.")

    e = check_logs_erro()
    log(f"D) logs: {e['detalhe']}")
    if not e["ok"]:
        problemas.append(f"LOGS: {e['detalhe']}")
        tipos.add("LOGS")
        etapas = {"anime_ocioso": "fazer os vídeos de anime", "parceiro_postar": "postar os vídeos dos parceiros",
                  "parceiro_producao": "produzir os vídeos dos parceiros", "anime_publish": "publicar os vídeos de anime",
                  "parceiro": "os vídeos dos parceiros", "anime": "os vídeos de anime"}
        for x in e.get("achados", []):
            nome, _, linha = x.partition(": ")
            # 23/10: só erro NOVO (o mesmo erro, mudando só a hora, saía de hora em hora)
            assinatura = re.sub(r"\d", "", linha)
            if erros_avisados.get(nome) == assinatura:
                continue
            erros_avisados[nome] = assinatura
            etapa = next((v for k, v in etapas.items() if nome.startswith(k)), "os vídeos de anime")
            simples.append(f"Deu erro na hora de {etapa}. Detalhe do erro: {linha}")
    else:
        erros_avisados = {}

    # so cobra saida se a noite ja passou
    if dentro_janela_ou_manha():
        s = check_saida_recente()
        log(f"C) saida: {s['detalhe']}")
        if not s["ok"]:
            problemas.append(f"SAIDA: {s['detalhe']}")
            tipos.add("SAIDA")
            simples.append("Nenhum vídeo de anime novo foi feito nas últimas 12 horas.")
    else:
        log("C) saida: (fora do horario de cobranca — pulado)")
        tipos |= tipos_antes & {"SAIDA"}  # sem checar agora: não dá pra dizer que voltou

    # monta alerta
    if corrigidos or problemas:
        for x in corrigidos:
            avisar(f"Vídeos de anime: consertado sozinho — {x}")
        for x in simples:
            avisar(x)
    else:
        log("Tudo OK — nada a reportar.")
    # 23/10 (dono: "saber se quebrou e se consertou"): o que estava com problema e passou
    voltou = {"CRON": "a produção automática voltou a ficar ligada",
              "WORKER": "o segundo computador (PC2) voltou a responder",
              "LOGS": "sem erros novos nas últimas 3 horas — os erros avisados antes pararam",
              "SAIDA": "voltaram a sair vídeos novos"}
    for t in sorted(tipos_antes - tipos):
        avisar(f"✅ Vídeos de anime voltaram ao normal: {voltou[t]}.")

    # estado pra historico
    try:
        _STATE.write_text(json.dumps({
            "ts": datetime.now().isoformat(),
            "corrigidos": corrigidos, "problemas": problemas,
            "tipos": sorted(tipos), "erros_avisados": erros_avisados,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    log("=== checagem encerrada ===")
    return 0 if not problemas else 1


if __name__ == "__main__":
    sys.exit(main())
