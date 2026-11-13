"""avisos.py — PORTÃO ÚNICO do Telegram dos projetos de vídeo (dono 19/10/2026: "o telegram manda muita mensagem e
acabo não lendo; reduza, principalmente as duplicadas; prioridade: inscritos, comentários e o vigia — saber se quebrou
e se consertou").

Antes: ~30 scripts mandavam direto pro mesmo bot, sem saber um do outro e sem guardar o que mandaram (o monitor do
anime repetia o MESMO alerta toda hora; a lista de postagens saía a cada 28 min).

    sys.path.insert(0, r"D:\\video-fila"); import avisos
    avisos.enviar(texto, "anime-monitor", importante=True)        # sai na hora (se não repetiu)
    avisos.enviar(texto, "postagens")                             # rotina: vai pro RESUMO
    python avisos.py            # o que saiu, segurou e repetiu nas últimas 24 h, por origem
    python avisos.py resumo     # manda o resumo agora

- REPETIDO: o mesmo aviso (mesma origem, mesmo texto sem números/horas — ou a mesma `chave`) dentro de JANELA_H não
  sai de novo; quando volta a sair, diz quantas vezes repetiu.
- IMPORTANTE (inscrito, comentário, vigia quebrou/consertou, erro, conta deslogada): na hora.
- ROTINA (postagens, capítulo pronto, filas, mil views, relatórios): junta e sai num RESUMO nas HORAS_RESUMO
  (despachar_resumo é chamado pela tarefa NotificarTelegram a cada 5 min).
- Tudo o que passa por aqui fica em estado/avisos.jsonl (enviado / resumo / repetido) — dá pra medir.
Falhou o portão (arquivo travado, JSON quebrado) = manda direto: aviso nunca pode sumir por defeito daqui.
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
EST = BASE / "estado" / "avisos_estado.json"
LOG = BASE / "estado" / "avisos.jsonl"
TRAVA = BASE / "estado" / "avisos.lock"
BOT = Path(r"D:\postador-de-videos\config\telegram.json")
JANELA_H = 12
HORAS_RESUMO = (9, 14, 21)
LIMITE = 3900  # Telegram corta em 4096


BOTS = Path(r"D:\postador-de-videos\config\telegram_bots.json")
ROTA = {  # dono 21–22/10: um bot por assunto (chave em telegram_bots.json); fora daqui = bot geral
    "aprendizado": "aprendizado",
    "postagens": "postagem", "filas de postagem": "postagem",
    "ritmo de postagem": "postagem", "postador": "postagem", "no ar": "postagem",
    "rampa de canais": "postagem",
    "comentarios": "comentarios",
    "opus-monitor": "opus",
    # dona 27/10: crédito de todos os modelos no MESMO bot (Opus 4.6, Opus 5.5 do sentinela e o Argon)
    "argon-monitor": "opus", "sentinela-credito": "opus",
    "studio": "bloqueios",
    "inscritos": "metricas", "mil views": "metricas",
    "tiktok-views": "metricas", "msenergy-metricas": "metricas",
    "contas com problema": "pendencias_humanas",
    "checar_canais": "pendencias_humanas", "trechos_noite": "pendencias_humanas",
    "hipercool": "producao", "manhwa-react": "producao", "historias": "producao",
    "recapd": "producao", "veo": "producao", "vídeos": "producao",
    "monitor do anime": "producao", "revisão do anime": "producao",
    "produção do parceiro": "producao", "guarda de testes": "producao",
    "vigia de melhorias": "producao", "painel ia": "producao", "vigia mútuo": "producao",
    "tiktok notebooks": "pendencias_humanas",
    "resumo dos notebooks": "producao", "conferência do áudio": "producao",
    "melhoria contínua": "producao",
    # 31/10 (dona: "o Claude code bot tinha 300 mensagens, não tem como ver todas"): o que caía no bot geral sem rota
    "argon": "opus", "sonnet-web": "opus", "sonnet-monitor": "opus", "troca-modelo": "opus",
    "melhorador central": "producao", "supervisor_melhorador": "producao", "engenharia_reversa": "producao",
    "maquinas-24h": "producao", "longo": "producao", "recap-longo": "producao", "desktop-vigia": "producao",
    "banimento": "pendencias_humanas", "nsn": "pendencias_humanas", "telao": "pendencias_humanas",
    "vigia desktop": "pendencias_humanas", "instagram login": "pendencias_humanas",
    "instagram auto": "pendencias_humanas",  # 01/11: caiu no bot geral (conta suspensa do Instagram)
    "credenciais-kaggle": "pendencias_humanas", "credenciais-groq": "pendencias_humanas",
    "postagem": "postagem", "no ar longo": "postagem",
    # 01/11: bot "Interessados no produto" = SÓ lead real (pediu orçamento/contato); 1 aviso por lead (chave)
    "produto-lead": "integracao_produto",
}
GERAL_DE_PROPOSITO = {"msenergy-clientes", "msenergy-carrossel", "portão de avisos", "resumo"}
# 31/10 (dona): só fica registrado (avisos.jsonl / painel), não vai pro Telegram
MUDO = {
    # "não precisa avisar de limite de postagem virtual, só dos limites do próprio YouTube" — o ritmo/rampa é teto
    # NOSSO; o limite do YouTube sai em "contas com problema"
    "ritmo de postagem", "rampa de canais",
    # 01/11: canais de produto que NÃO são lead real: spam/sorteio, teste, conversa pessoal (só log)
    "produto-ruido", "produto-teste", "produto-conversa",
    # 01/11: troca automática Opus 5.5 <-> 4.6 do chat (11 registros em 45 min): rotina do trocador, nada para a dona
    "troca-modelo",
}
# rotina que se resolve sozinha: nunca sai na hora, só no resumo (a dona só quer o que precisa dela)
SO_RESUMO = {"banimento", "troca-modelo", "sonnet-web", "argon", "nsn", "desktop-vigia", "melhorador central",
             "engenharia_reversa", "supervisor_melhorador"}
# conserto automático que já deu certo (proxy/túnel religado, conta que voltou sozinha): só registro
SO_REGISTRO = re.compile(r"proxy :?\d+ subiu|t[úu]nel restaurado|religuei|reiniciei sozinho|"
                         r"conta\(s\)? de volta|login voltou|: VOLTOU|voltou sozinh|"
                         r"voltou ao normal|voltaram ao normal|voltaram a ser produzid|voltou a responder", re.I)
NADA_A_FAZER = re.compile(r"(o que fazer|a[cç][aã]o)\s*:\s*(n[aã]o (precisa|[eé] preciso)|nada)", re.I)
VOLTA_DE_COTA = {"sonnet-monitor", "argon-monitor", "opus-monitor", "sentinela-credito"}  # "voltou" aqui é o pedido
_SEM_CHAT = set()  # bot novo que ainda não recebeu o "Iniciar" do dono: cai no bot de sempre

# dono 23/10: de madrugada e "vídeo no ar" chegam sem tocar o celular (disable_notification)
SILENCIOSO = {"no ar"}
NOITE_ATE = 7
# dono 23/10: o mesmo problema avisado por vários robôs vira 1 aviso; quando passa, sai o "voltou ao normal"
INCIDENTES = {"disco": re.compile(r"disco.{0,60}(chei|ench|livre|espa[cç]o)|no space left|sem espa[cç]o", re.I | re.S)}
RESOLVEU = re.compile(r"CONSERTEI|consert(ou|ei)|resolvid|voltou ao normal", re.I)
DISCO_OK_GB = 8

# dono 22/10: "qualquer pessoa tem que entender" — a IA reescreve o aviso em linguagem simples (avisos_simples.txt).
# Já simples, ou o texto exato importa (resposta SIM/NÃO, comentário): sai como veio.
SEM_SIMPLIFICAR = {"aprendizado", "comentarios", "inscritos", "no ar", "no ar longo", "mil views", "opus-monitor",
                   "longo",  # 01/11: a ficha do longo já é simples e tem horas/links que não podem mudar
                   "postagens", "sonnet-monitor",
                   "produto-lead",  # 01/11: a mensagem do cliente sai como ele escreveu
                   "argon-monitor",  # 27/10: hora exata da volta da cota, não pode ser reescrita
                   "resumo dos notebooks",  # 23/10: já escrito simples, com números que não podem mudar
                   "melhoria contínua",
                   "credenciais-groq", "credenciais-kaggle"}  # 23/10: leva o comando pronto pra rodar  # 23/10: texto simples com comando ("melhorias reserva sim") que não pode mudar
NOMES = {"postagens": "Vídeos postados", "mil views": "Vídeos que passaram de 5.000 views",
         "inscritos": "Novos inscritos", "no ar": "Vídeos no ar"}
INSTRUCOES = BASE / "avisos_simples.txt"
MODELOS = ("qwen/qwen3.8-27b", "openai/gpt-oss-120b")
# termo técnico que escapou da reescrita (23/10: "O que fazer: REVISAR", "parceiro_postar.log: KeyError")
TECNICO = re.compile(r"\.(py|log|json|bat)\b|Traceback|Exception|\w+Error\b|\bREVISAR\b|\bCONSERTEI\b|status=|"
                     r"\bporta \d{3,}|HTTP \d{3}|\b[a-z]+_[a-z]+_[a-z_]+\b")
PEDIDO_RESUMO = ("\nEste texto é um resumo com vários avisos agrupados por assunto. Escreva um título curto e simples "
                 "para cada assunto e cada aviso numa linha começando com \"- \" e o horário. Avisos iguais viram uma "
                 "linha só dizendo quantas vezes aconteceram.")


def simplificar(texto, pedido=""):
    """Texto em linguagem simples pelo Groq (proxy Webshare do groq_api do hipercool) ou None se não deu."""
    try:
        import importlib.util
        pasta = r"D:\hipercool-videos\bin"
        if pasta not in sys.path:
            sys.path.append(pasta)
        spec = importlib.util.spec_from_file_location("_groq_avisos", pasta + r"\groq_api.py")
        g = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(g)
        g.PROXY_TENTATIVAS = 2  # aviso não pode prender o script que avisa
        plano = html.unescape(re.sub(r"<[^>]+>", "", texto)).strip()
        sistema = INSTRUCOES.read_text(encoding="utf-8") + pedido
        chaves = g.chaves()
        melhor = None
        for i, modelo in enumerate(MODELOS):
            if not chaves:
                return melhor
            corpo = {"model": modelo, "temperature": 0.1, "max_completion_tokens": 2500,
                     "reasoning_effort": "low" if "gpt-oss" in modelo else "none",
                     "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": plano}]}
            st, j, _p = g._pedido("POST", "/chat/completions", chaves[i % len(chaves)][2], timeout=25, json=corpo)
            if st == 200:
                saida = (j["choices"][0]["message"].get("content") or "").replace("**", "").strip()
                if saida and not TECNICO.search(saida):
                    return saida
                melhor = melhor or saida or None  # 23/10: ainda com termo técnico -> tenta o outro modelo
        return melhor
    except Exception:  # noqa: BLE001 — sem IA o aviso sai como veio
        pass
    return None


# 01/11 (dona: "dividir mais em outros bots que eu posso criar"): o bot NOVO de cada origem. Só vale depois que a
# chave existir em telegram_bots.json (com bot_token e chat_id); até lá a origem segue na ROTA de sempre.
# Medido 29/10–01/11 (3 dias): postagem 388 (272 "no ar"), producao 292, opus 261 (187 argon), pendencias 242.
ROTA_NOVA = {
    "melhorador central": "plantao", "vigia de melhorias": "plantao",
    "engenharia_reversa": "plantao", "supervisor_melhorador": "plantao", "painel ia": "plantao",
    "longo": "longos", "recap-longo": "longos",
    "argon": "opus", "argon-monitor": "opus", "sonnet-monitor": "opus",
    "sonnet-web": "opus", "troca-modelo": "opus",
    "banimento": "contas", "nsn": "contas", "instagram login": "contas",
    "instagram auto": "contas", "telao": "contas", "checar_canais": "contas",
}


# 09/11 (dona: "unificar avisos de erros em um bot Telegram só; tudo com formatação, separação e emojis; cada mensagem
# num doc pra eu dizer 'verifica uma a uma'; pendências humanas só login/contestação, com deslogado confirmado e onde").
# Desligar tudo: AVISOS_UNIFICADO=0.
UNIFICADO = os.environ.get("AVISOS_UNIFICADO", "1") != "0"
FICHAS = BASE / "avisos_fichas"
ERRO_RX = re.compile(r"\berr[oa]\b|\bERRO\b|falh|rc=\d|não conseguiu|nao conseguiu|travad|parou|caiu|"
                     r"exception|traceback|🔴|❌", re.I)
HUMANO_RX = re.compile(r"\blogin\b|deslogad|logar|senha|c[óo]digo (de seguran|por e-?mail|sms)|\bSMS\b|"
                       r"contesta|suspens|verifica[çc][ãa]o de idade|recurso|banid", re.I)
HUMANO_ORIGENS = {"pendencias_humanas", "contas com problema", "nsn", "instagram login", "tiktok notebooks",
                  "checar_canais", "instagram auto"}
EMOJI_TIPO = [(re.compile(r"SAIU A SÉRIE QUE VOCÊ ACOMPANHA", re.I), "🔥 SÉRIE QUE VOCÊ ACOMPANHA"),
              (re.compile(r"login|deslogad|senha|SMS|c[óo]digo", re.I), "🔐 PRECISA DE VOCÊ"),
              (ERRO_RX, "🔴 ERRO"), (re.compile(r"PRONTO|no ar|PUBLICADO|✅", re.I), "✅ FEITO"),
              (re.compile(r"views|inscrit|meta", re.I), "📈 MÉTRICA")]


# 11/11 (Medieval 9 'no ar longo' saiu "🔴 ERRO" e foi pro bot de erros só porque a ficha cita a melhoria proposta
# "corrigir erro de digitação"): aviso de vídeo POSTADO/PRONTO nunca é erro por palavra solta. AVISOS_POSTADO_NAO_ERRO=0
# volta ao antigo.
ORIGENS_POSTADO = {"no ar longo", "recap-longo"}
POSTADO_RX = re.compile(r"PRONTO|AGENDADO|PUBLICADO|no ar|SAIU|✅", re.I)


def _e_erro(texto, origem=""):
    if not (texto and ERRO_RX.search(texto)):
        return False
    if os.environ.get("AVISOS_POSTADO_NAO_ERRO", "1") != "0" and origem in ORIGENS_POSTADO             and POSTADO_RX.search(texto) and not re.search(r"🔴|❌|traceback|exception", texto, re.I):
        return False
    return True


# Saem na hora sempre (gente ou o que a dona pediu na hora): inscritos, comentários, lead, série que ela acompanha
SEMPRE_NA_HORA = {"inscritos", "comentarios", "produto-lead", "aprendizado", "opus-monitor", "argon-monitor",
                  "sonnet-monitor", "sentinela-credito", "drive-chave"}
# dona 10/11: "quero ser notificada com ênfase assim que postar" a série que ela acompanha
SERIE_DONA = re.compile(r"SAIU A SÉRIE QUE VOCÊ ACOMPANHA", re.I)
ESPERA_ERRO_MIN = int(os.environ.get("AVISOS_ESPERA_ERRO_MIN", "30"))


def _por_em_espera(texto, origem, chave, html_ok):
    try:
        with _trava():
            d = _ler()
            d.setdefault("espera", []).append({"em": datetime.now().isoformat(timespec="seconds"), "origem": origem,
                                               "chave": chave, "html_ok": html_ok, "texto": texto})
            _gravar(d)
    except Exception:  # noqa: BLE001 — sem trava: manda direto (aviso nunca some)
        _mandar(texto, html_ok, None, origem)


def _fechar_espera(origem):
    try:
        with _trava():
            d = _ler()
            antes = len(d.get("espera", []))
            d["espera"] = [x for x in d.get("espera", []) if x["origem"] != origem]
            if len(d["espera"]) != antes:
                _gravar(d)
    except Exception:  # noqa: BLE001
        pass


def liberar_esperas():
    """Erro que passou ESPERA_ERRO_MIN sem conserto da mesma origem -> Telegram. Chamado pela NotificarTelegram."""
    try:
        with _trava():
            d = _ler()
            agora = datetime.now()
            vencidos = [x for x in d.get("espera", [])
                        if agora - datetime.fromisoformat(x["em"]) >= timedelta(minutes=ESPERA_ERRO_MIN)]
            if not vencidos:
                return 0
            d["espera"] = [x for x in d["espera"] if x not in vencidos]
            _gravar(d)
    except Exception:  # noqa: BLE001
        return 0
    vistos = set()
    for x in vencidos:  # a mesma origem com vários erros em espera = 1 mensagem (o último)
        if x["origem"] in vistos:
            continue
        vistos.add(x["origem"])
        ultimo = [y for y in vencidos if y["origem"] == x["origem"]][-1]
        n = sum(1 for y in vencidos if y["origem"] == x["origem"])
        texto = ultimo["texto"] + (f"\n(continua sem conserto há {ESPERA_ERRO_MIN} min; {n} aviso(s) juntos)")
        os.environ["AVISOS_SO_ERRO_ABERTO"] = "0"  # já passou pelo filtro: agora sai de verdade
        try:
            enviar(texto, x["origem"], importante=True, chave=ultimo.get("chave"), html_ok=ultimo["html_ok"])
        finally:
            os.environ.pop("AVISOS_SO_ERRO_ABERTO", None)
    return len(vencidos)


def _humano_ok(texto):
    """Pendência humana só passa se fala de login/senha/código/contestação/suspensão E diz onde (conta/máquina)."""
    t = re.sub(r"<[^>]+>", "", texto)
    return bool(HUMANO_RX.search(t)) and bool(re.search(r"@|conta|canal|pc\d|x200|acer|desktop|cofre", t, re.I))


def _ficha(texto, origem):
    """Grava a mensagem como documento numerado e devolve o número (a dona diz 'verifica a ficha N')."""
    try:
        FICHAS.mkdir(parents=True, exist_ok=True)
        cont = FICHAS / "_contador.txt"
        n = int(cont.read_text() or 0) + 1 if cont.exists() else 1
        cont.write_text(str(n))
        limpo = re.sub(r"<[^>]+>", "", texto)
        (FICHAS / f"{n:05d}_{datetime.now():%Y%m%d_%H%M}_{re.sub(r'[^a-z0-9]+', '-', origem.lower())[:30]}.md").write_text(
            f"# Ficha {n} — {origem}\n\n- Quando: {datetime.now():%d/%m %H:%M}\n- Situação: [ ] verificar\n\n"
            f"## Mensagem\n\n{limpo}\n\n## Verificação (preencher)\n\n- Causa:\n- Feito:\n", encoding="utf-8")
        return n
    except OSError:
        return None


def _formatar(texto, html_ok, origem, n):
    ficha = f" · ficha #{n}" if n else ""
    if _rota(origem, texto) == "metricas":
        # 10/11 (dona): no bot de métricas o cabeçalho "📈 MÉTRICA · inscritos" repete o nome do bot; a 1ª linha
        # tem que ser a métrica em si (de quanto pra quanto). A ficha vai pro fim.
        if not n:
            return texto
        return f"{texto}\n<i>ficha #{n}</i>" if html_ok else f"{texto}\nficha #{n}"
    cab = next((rot for rx, rot in EMOJI_TIPO if rx.search(texto) and not (rx is ERRO_RX and not _e_erro(texto, origem))),
               "ℹ️ AVISO")
    sep = "━━━━━━━━━━━━"
    if html_ok:
        return f"<b>{cab}</b>  <i>{html.escape(origem, quote=False)}{ficha}</i>\n{sep}\n{texto}"
    return f"{cab}  ({origem}{ficha})\n{sep}\n{texto}"


def _rota(origem, texto=""):
    """Chave do bot desta origem: a nova (se o bot já foi criado) ou a de sempre."""
    if UNIFICADO and _e_erro(texto, origem):  # 09/11: todo erro num bot só ("erros", ou o geral)
        try:
            b = json.loads(BOTS.read_text(encoding="utf-8-sig")).get("erros") or {}
            if b.get("bot_token") and b.get("chat_id"):
                return "erros"
        except (OSError, ValueError):
            pass
        return None
    nova = ROTA_NOVA.get(origem)
    if nova:
        try:
            b = json.loads(BOTS.read_text(encoding="utf-8-sig")).get(nova) or {}
            if b.get("bot_token") and b.get("chat_id") and str(b.get("em_uso", True)) != "False":
                return nova
        except (OSError, ValueError):
            pass
    return ROTA.get(origem)


def _bot(origem=None, texto=""):
    d = json.loads(BOT.read_text(encoding="utf-8"))
    qual = _rota(origem, texto)
    if qual and qual not in _SEM_CHAT:
        try:
            b = json.loads(BOTS.read_text(encoding="utf-8"))[qual]
            return b["bot_token"], str(b["chat_id"]), d.get("ativo", True)
        except (OSError, ValueError, KeyError):
            pass
    return d["bot_token"], str(d["chat_id"]), d.get("ativo", True)


def _silencioso(origem):
    return origem in SILENCIOSO or datetime.now().hour < NOITE_ATE


def _incidente(texto):
    inc = next((n for n, rx in INCIDENTES.items() if rx.search(texto)), None)
    if inc == "disco" and re.search(r"\bC:|PC2", texto):  # só o D: do PC1 tem o "voltou ao normal" automático
        return None
    return inc


def _mandar(texto, html_ok=True, responder_a=None, origem=None):
    """Manda de verdade (em pedaços se for grande). message_id do 1º pedaço ou None."""
    qual = _rota(origem, texto)
    if qual and qual not in _SEM_CHAT:
        token, chat, _a = _bot(origem, texto)
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getChat?chat_id={chat}", timeout=15).read()
        except Exception:  # noqa: BLE001 — "chat not found": o dono ainda não apertou Iniciar nesse bot
            _SEM_CHAT.add(qual)
    token, chat, ativo = _bot(origem, texto)
    if not ativo:
        return None
    primeiro = None
    for i in range(0, max(1, len(texto)), LIMITE):
        dados = {"chat_id": chat, "text": texto[i:i + LIMITE], "disable_web_page_preview": "true"}
        if _silencioso(origem):
            dados["disable_notification"] = "true"
        if html_ok:
            dados["parse_mode"] = "HTML"
        if responder_a and i == 0:
            dados["reply_to_message_id"] = str(responder_a)
        for tentativa in range(2):
            try:
                req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage",
                                             data=urllib.parse.urlencode(dados).encode("utf-8"), method="POST")
                with urllib.request.urlopen(req, timeout=20) as r:
                    j = json.loads(r.read())
                    primeiro = primeiro or (j.get("result") or {}).get("message_id")
                    break
            except Exception:  # noqa: BLE001
                if html_ok and tentativa == 0:  # HTML quebrado: manda sem formatação
                    dados.pop("parse_mode", None)
                    dados["text"] = re.sub(r"<[^>]+>", "", dados["text"])
                    continue
                return primeiro
    return primeiro


@contextmanager
def _trava():
    for _ in range(100):
        try:
            fd = os.open(TRAVA, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - TRAVA.stat().st_mtime > 60:
                    TRAVA.unlink(missing_ok=True)
                    continue
            except OSError:
                pass
            time.sleep(0.1)
    else:
        raise TimeoutError("trava dos avisos ocupada")
    try:
        yield
    finally:
        TRAVA.unlink(missing_ok=True)


def _ler():
    try:
        d = json.loads(EST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    d.setdefault("enviados", {})
    d.setdefault("resumo", [])
    return d


def _gravar(d):
    EST.parent.mkdir(parents=True, exist_ok=True)
    corte = (datetime.now() - timedelta(days=3)).isoformat()
    d["enviados"] = {k: v for k, v in d["enviados"].items() if v.get("em", "") >= corte}
    tmp = EST.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(EST)


def _registro(origem, situacao, importante, texto):
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "origem": origem,
                                 "situacao": situacao, "importante": importante,
                                 "texto": re.sub(r"<[^>]+>", "", texto)[:300]}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _chave(texto, origem):
    """Mesmo aviso = mesma origem e mesmo texto sem números, horas, links e tags (o alerta que só muda o horário)."""
    t = re.sub(r"<[^>]+>|https?://\S+", "", texto.lower())
    t = re.sub(r"\d+", "#", t)
    return origem + ":" + " ".join(t.split())[:400]


PRIORIDADE_FORA = {"vigia_trader",  # outro projeto: não recebe aviso dos vídeos
                   "integracao_produto"}  # 01/11: bot "Interessados no produto" recebe SÓ lead real


def prioridade(texto, origem="prioridade"):
    """Aviso de PRIORIDADE (dona 23/10: "avisar como prioridade em todos os telegram"): o bot geral E todos os bots
    de assunto (telegram_bots.json), sempre com som (mesmo de madrugada), sem resumo nem reescrita. Quantos saíram."""
    destinos = []
    try:
        d = json.loads(BOT.read_text(encoding="utf-8"))
        destinos.append((d["bot_token"], str(d["chat_id"])))
    except (OSError, ValueError, KeyError):
        pass
    try:
        for nome, b in json.loads(BOTS.read_text(encoding="utf-8")).items():
            if (isinstance(b, dict) and nome not in PRIORIDADE_FORA and b.get("em_uso", True)
                    and b.get("bot_token") and b.get("chat_id")):
                destinos.append((b["bot_token"], str(b["chat_id"])))
    except (OSError, ValueError):
        pass
    def _um(destino):
        token, chat = destino
        try:
            dados = {"chat_id": chat, "text": ("🚨 PRIORIDADE\n" + texto)[:LIMITE], "disable_web_page_preview": "true"}
            req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage",
                                         data=urllib.parse.urlencode(dados).encode("utf-8"), method="POST")
            urllib.request.urlopen(req, timeout=20).read()
            return 1
        except Exception:  # noqa: BLE001 — bot sem "Iniciar" apertado: os outros seguem
            return 0
    # em paralelo: um por vez levou 2+ min no teste de 23/10 (10 bots) e o vigia mútuo roda a cada 2 min
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=12) as ex:
        ok = sum(ex.map(_um, list(dict.fromkeys(destinos))))
    try:
        _registro(origem, "prioridade", True, texto)
    except Exception:  # noqa: BLE001
        pass
    return ok


def enviar(texto, origem, importante=False, chave=None, html_ok=True, responder_a=None, janela_h=JANELA_H):
    """Porta única. Importante sai na hora; rotina vai pro resumo; repetido dentro da janela não sai.
    html_ok: o texto já está em HTML do Telegram (escapado); False = texto puro. Devolve message_id quando mandou."""
    if not texto:
        return None
    if origem in MUDO or (origem not in VOLTA_DE_COTA and SO_REGISTRO.search(texto)):
        if origem not in MUDO:
            _fechar_espera(origem)  # 11/11: conserto automático fecha o erro que estava esperando
        _registro(origem, "mudo", importante, texto)
        return None
    if origem in SO_RESUMO:
        importante = False
    # 11/11 dona ("se não foi um erro não precisava ter chegado ao Telegram; só devem ir lá erros que não foram
    # corrigidos de fato pelo vigia, por você, pelo melhorador ou qualquer outro"). AVISOS_SO_ERRO_ABERTO=0 desliga.
    if importante and not responder_a and os.environ.get("AVISOS_SO_ERRO_ABERTO", "1") != "0" \
            and origem not in SEMPRE_NA_HORA and not _humano_ok(texto) and not SERIE_DONA.search(texto):
        if RESOLVEU.search(texto) or SO_REGISTRO.search(texto):  # conserto: fecha o erro em espera e não manda
            _fechar_espera(origem)
            _registro(origem, "consertado", importante, texto)
            return None
        if not _e_erro(texto, origem):  # feito/postado/métrica: só no resumo
            importante = False
        else:  # erro: espera ESPERA_ERRO_MIN; se ninguém consertar, sai (liberar_esperas, tarefa NotificarTelegram)
            _por_em_espera(texto, origem, chave, html_ok)
            _registro(origem, "em espera", importante, texto)
            return None
    try:
        with _trava():
            d = _ler()
            k = chave or _chave(texto, origem)
            ult = d["enviados"].get(k)
            agora = datetime.now()
            if ult and agora - datetime.fromisoformat(ult["em"]) < timedelta(hours=janela_h):
                ult["repetiu"] = ult.get("repetiu", 0) + 1
                _gravar(d)
                _registro(origem, "repetido", importante, texto)
                return None
            incs = d.setdefault("incidentes", {})
            inc = _incidente(texto) if origem not in SEM_SIMPLIFICAR else None  # comentário de gente nunca entra
            aberto = incs.get(inc) if inc else None
            if aberto and agora - datetime.fromisoformat(aberto["desde"]) > timedelta(hours=24):
                aberto = None  # problema velho: avisa de novo (lembrete diário)
            if inc and RESOLVEU.search(texto):
                incs.pop(inc, None)
            elif aberto:
                aberto["vezes"] = aberto.get("vezes", 0) + 1
                _gravar(d)
                _registro(origem, "mesmo problema", importante, texto)
                return None
            elif inc:
                incs[inc] = {"desde": agora.isoformat(timespec="seconds"), "origem": origem, "vezes": 0}
            if origem not in ROTA and origem not in GERAL_DE_PROPOSITO and origem not in d.setdefault("sem_bot", []):
                d["sem_bot"].append(origem)
                d["resumo"].append({"em": agora.isoformat(timespec="minutes"), "origem": "portão de avisos",
                                    "texto": html.escape(f"Aviso novo sem bot próprio: \"{origem}\" está caindo no bot "
                                                         "geral (pôr na ROTA do avisos.py).", quote=False)})
            repetiu = (ult or {}).get("repetiu", 0)
            d["enviados"][k] = {"em": agora.isoformat(timespec="seconds"), "repetiu": 0, "origem": origem}
            if not importante:
                d["resumo"].append({"em": agora.isoformat(timespec="minutes"), "origem": origem,
                                    "texto": texto if html_ok else html.escape(texto, quote=False)})
                _gravar(d)
                _registro(origem, "resumo", importante, texto)
                return None
            _gravar(d)
    except Exception:  # noqa: BLE001 — o portão com defeito não pode engolir aviso
        repetiu = 0
    if origem not in SEM_SIMPLIFICAR and not responder_a and not SERIE_DONA.search(texto):
        simples = simplificar(texto)
        if simples:
            texto, html_ok = simples, False
        # 01/11 (dona: "notificar apenas quando precisar de mim"): a própria reescrita disse que não há nada a fazer
        # (madrugada de 01/11: 2 avisos do bot de produção "O que fazer: não precisa fazer nada") -> vai pro resumo
        if simples and NADA_A_FAZER.search(simples) and not RESOLVEU.search(simples):
            try:
                with _trava():
                    d = _ler()
                    d["resumo"].append({"em": datetime.now().isoformat(timespec="minutes"), "origem": origem,
                                        "texto": html.escape(simples, quote=False)})
                    _gravar(d)
                _registro(origem, "resumo", importante, simples)
                return None
            except Exception:  # noqa: BLE001 — sem trava: manda como antes
                pass
    if repetiu:
        nota = f"(repetiu {repetiu}x nas últimas {janela_h} h)"
        texto = f"{texto}\n<i>{nota}</i>" if html_ok else f"{texto}\n{nota}"
    if UNIFICADO and not responder_a:
        # pendência humana sem login/contestação ou sem dizer onde -> resumo (não interrompe a dona)
        if origem in HUMANO_ORIGENS and not _humano_ok(texto):
            try:
                with _trava():
                    d = _ler()
                    d["resumo"].append({"em": datetime.now().isoformat(timespec="minutes"), "origem": origem,
                                        "texto": texto if html_ok else html.escape(texto, quote=False)})
                    _gravar(d)
                _registro(origem, "resumo", importante, texto)
                return None
            except Exception:  # noqa: BLE001
                pass
        texto = _formatar(texto, html_ok, origem, _ficha(texto, origem))
    mid = _mandar(texto, html_ok, responder_a, origem)
    _registro(origem, "enviado" if mid else "falhou", importante, texto)
    return mid


def enviar_arquivo(caminho, legenda, origem, responder_a=None):
    """Vídeo (.mp4) ou áudio (.mp3/.m4a/.ogg) no Telegram, como resposta a uma mensagem já liberada pelo portão
    (ex.: o trecho de um achado do aprendizado). message_id ou None."""
    try:
        token, chat, ativo = _bot(origem)
        if not ativo:
            return None
        caminho = Path(caminho)
        metodo, campo = (("sendVideo", "video") if caminho.suffix.lower() == ".mp4" else ("sendAudio", "audio"))
        lim = "----avisos" + os.urandom(8).hex()
        partes = []
        campos = {"chat_id": chat, "caption": legenda[:1000]}
        if _silencioso(origem):
            campos["disable_notification"] = "true"
        if responder_a:
            campos["reply_to_message_id"] = str(responder_a)
        for k, v in campos.items():
            partes.append(f"--{lim}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8"))
        partes.append(f"--{lim}\r\nContent-Disposition: form-data; name=\"{campo}\"; filename=\"{caminho.name}\"\r\n"
                      "Content-Type: application/octet-stream\r\n\r\n".encode("utf-8") + caminho.read_bytes() + b"\r\n")
        partes.append(f"--{lim}--\r\n".encode("utf-8"))
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{metodo}", data=b"".join(partes),
                                     headers={"Content-Type": f"multipart/form-data; boundary={lim}"}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as r:
            mid = (json.loads(r.read()).get("result") or {}).get("message_id")
    except Exception:  # noqa: BLE001
        mid = None
    _registro(origem, "enviado" if mid else "falhou", True, f"[arquivo {Path(caminho).name}] {legenda}")
    return mid


def _marca_resumo():
    agora = datetime.now()
    slot = max([h for h in HORAS_RESUMO if h <= agora.hour], default=None)
    return None if slot is None else f"{agora:%Y-%m-%d} {slot}"


def resumo_devido():
    """True quando o próximo despachar_resumo() vai mandar (horário novo de HORAS_RESUMO)."""
    marca = _marca_resumo()
    return bool(marca) and _ler().get("ultimo_resumo") != marca


def fechar_incidentes():
    """Disco: o D: voltou a ter DISCO_OK_GB livres -> "voltou ao normal" no bot de quem abriu o problema."""
    import shutil
    with _trava():
        d = _ler()
        inc = d.get("incidentes", {}).get("disco")
        livre = shutil.disk_usage("D:\\").free / 1e9
        if not inc or livre < DISCO_OK_GB:
            return
        d["incidentes"].pop("disco")
        _gravar(d)
    desde = datetime.fromisoformat(inc["desde"])
    texto = (f"✅ Disco voltou ao normal: {livre:.0f} GB livres no D: (o problema começou {desde:%d/%m às %H:%M}"
             + (f"; segurei {inc['vezes']} aviso(s) repetidos sobre ele)" if inc.get("vezes") else ")"))
    mid = _mandar(texto, html_ok=False, origem=inc["origem"])
    _registro(inc["origem"], "enviado" if mid else "falhou", True, texto)


def despachar_resumo(forcar=False):
    """Manda o resumo da rotina num horário de HORAS_RESUMO (uma vez por horário). Devolve quantos itens mandou.
    Cada bot recebe só os itens cujas origens pertencem a ele; origens sem ROTA vão no bot geral."""
    try:
        fechar_incidentes()
    except Exception:  # noqa: BLE001 — o resumo não pode parar por causa disso
        pass
    try:  # 11/11: erros em espera há 30 min sem conserto saem agora
        liberar_esperas()
    except Exception:  # noqa: BLE001
        pass
    marca = _marca_resumo()
    with _trava():
        d = _ler()
        if not forcar and (marca is None or d.get("ultimo_resumo") == marca):
            return 0
        marca = marca or f"{datetime.now():%Y-%m-%d} None"
        itens = d["resumo"]
        d["resumo"], d["ultimo_resumo"] = [], marca
        _gravar(d)
    if not itens:
        return 0
    por_bot = {}
    for it in itens:
        bot_key = _rota(it["origem"])
        por_bot.setdefault(bot_key, []).append(it)
    for bot_key, bot_itens in por_bot.items():
        por_origem = {}
        for it in bot_itens:
            por_origem.setdefault(it["origem"], []).append(it)
        fixos, partes = [], []  # fixos: já vêm organizados (canal, narrador, links) e saem como estão
        for origem, lst in sorted(por_origem.items(), key=lambda kv: -len(kv[1])):
            alvo = fixos if origem in SEM_SIMPLIFICAR else partes
            alvo.append(f"\n<b>{html.escape(NOMES.get(origem, origem))}</b> ({len(lst)})")
            for it in lst[-8:]:
                corpo = it["texto"].strip()
                alvo.append(f"• {it['em'][11:16]} {corpo if alvo is fixos else corpo[:600]}")
            if len(lst) > 8:
                alvo.append(f"• ... e mais {len(lst) - 8} anteriores")
        texto = "\n".join(partes)
        simples = simplificar(texto, PEDIDO_RESUMO) if partes else None
        corpo = "\n".join(fixos) + ("\n\n" + html.escape(simples) if simples else ("\n" + texto if partes else ""))
        mid = _mandar(f"<b>Resumo das últimas horas</b> ({len(bot_itens)} aviso(s))\n{corpo}",
                      origem=bot_itens[0]["origem"])
        _registro(bot_key or "resumo_geral", "enviado" if mid else "falhou", False,
                  f"{bot_key or 'geral'}: {len(bot_itens)} itens")
        if not mid:  # 23/10: o envio falhou (rede, Telegram fora) — os itens voltam pra fila e saem no próximo resumo
            try:
                with _trava():
                    d = _ler()
                    d["resumo"] = bot_itens + d["resumo"]
                    _gravar(d)
            except Exception:  # noqa: BLE001
                pass
    return len(itens)


def relatorio(horas=24):
    from collections import Counter
    desde = (datetime.now() - timedelta(hours=horas)).isoformat()
    c = Counter()
    for ln in LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r["em"] >= desde:
            c[(r["origem"], r["situacao"])] += 1
    for (o, s), n in sorted(c.items(), key=lambda kv: -kv[1]):
        print(f"{n:5} {s:9} {o}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.argv[1:2] == ["resumo"]:
        print("itens:", despachar_resumo(forcar=True))
    else:
        relatorio()
