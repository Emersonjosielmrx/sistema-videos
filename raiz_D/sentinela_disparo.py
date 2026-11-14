r"""sentinela_disparo.py - manda "continue" nos chats que pararam por erro da API, quando o crédito volta.

Roda FORA de qualquer chat (tarefa do Windows "SentinelaContinue", a cada 5 min), para não depender de um chat
sentinela com crédito. Dona 28/10/2026: o sentinela antigo (Monitor num chat) morria a cada 30 min e, sem crédito,
ninguém o religava.

    python D:\sentinela_disparo.py             # confere e dispara
    python D:\sentinela_disparo.py --simular   # só mostra quem receberia

Quem recebe: chat interativo, parado (idle), cujo último turno terminou em "API Error" (429, 502 vazio, 403...).
Chat esperando resposta da dona NÃO recebe. O mesmo chat só recebe de novo se der erro DEPOIS do último envio.
Só recebe quando há crédito no provedor que ELE usa (cc/... = CC, antigravity/... = Antigravity, opus-auto = qualquer);
quando esse crédito volta, as 3 tentativas zeram na hora (dona 28/10: o CC voltou 12:40 e ninguém acordou).
O envio é por um Claude sem tela (claude.exe -p) com o Gemini, que usa o SendMessage (não gasta Opus).
Log: D:\sentinela_disparo.log

03/11/2026 — VS Code fechado para economizar RAM:
Quando a dona fecha o VS Code, os sessions/*.json somem. O sentinela agora lê os chats que estavam abertos
direto do state.vscdb do workspace (panelTabSessions) e confere o .jsonl de cada um. Se há chat parado por erro
COM crédito E o VS Code está fechado, o sentinela abre o VS Code, espera os sessions/*.json aparecerem, e depois
manda o continue normalmente. Assim a dona pode fechar o VS Code quando não tem crédito e ele abre sozinho.
"""
import glob
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "D:\\")
import sentinela_credito as sc  # noqa: E402

CFG = Path(os.path.expanduser(r"~\.claude-vscode"))
ESTADO = Path(r"D:\sentinela_disparo_state.json")
LOG = Path(r"D:\sentinela_disparo.log")
BATIMENTO = Path(r"D:\sentinela_batimento.json")
CLAUDE = max(glob.glob(os.path.expanduser(
    r"~\.vscode\extensions\anthropic.claude-code-*-win32-x64\resources\native-binary\claude.exe")), default=None)
# 09/11 (dona: "2.5 como fallback"): o Antigravity foi desativado pelo Google em 06/11 ~17h ("This version of
# Antigravity is no longer supported") e agy/gemini-3.8 virou laço de 64 mil tokens -> nenhum continue chegou de
# 06/11 17:51 a 09/11. gemini/gemini-2.5-flash-lite (API direta, fora do Antigravity) entregou em 15 s com prova.
# Quando o Antigravity for atualizado, pode voltar para "agy/gemini-3.8-flash-high".
MODELO = "gemini/gemini-2.5-flash-lite"
CHAVE = "<SEGREDO_REMOVIDO>"
CODE_CMD = os.path.expanduser(r"~\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd")
WORKSPACE_URI = "file:///d%3A/"
OCULTO = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# tempo que o VS Code leva para abrir + extensão iniciar + sessions/*.json serem criados
ESPERA_VSCODE_ABRIR_S = 90
ESPERA_VSCODE_POLL_S = 5


def log(msg):
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(linha, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def ultimo_turno(session_id):
    """(timestamp, erro, modelo) do último turno user/assistant do chat; erro=None se não terminou em erro da API.
    modelo = o que o chat pediu na última chamada à API (diz de qual crédito ele depende)."""
    tr = glob.glob(str(CFG / "projects" / "*" / f"{session_id}.jsonl"))
    if not tr:
        return None, None, None
    with open(tr[0], "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 400_000))
        linhas = f.read().decode("utf-8", "replace").splitlines()
    turno, modelo = None, None
    for linha in reversed(linhas):
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if modelo is None and d.get("type") == "api-request":
            modelo = (d.get("params") or {}).get("model")
        if turno is None and d.get("type") in ("user", "assistant"):
            m = d.get("message") or {}
            c = m.get("content")
            if d["type"] == "user" and isinstance(c, str) and c.lstrip().startswith("<task-notification>"):
                continue  # aviso de tarefa em 2º plano sem resposta: o chat segue parado no erro de antes (28/10)
            texto = c if isinstance(c, str) else " ".join(
                x.get("text", "") for x in (c or []) if isinstance(x, dict) and x.get("type") == "text")
            erro = d.get("isApiErrorMessage") or (m.get("model") == "<synthetic>" and "API Error" in texto)
            turno = (d.get("timestamp"), texto[:160] if erro else None)
        if turno and modelo:
            break
    return (*(turno or (None, None)), modelo)


def provedor(modelo):
    """De qual crédito o chat depende: 'claude' (Opus 5.5 pago), 'antigravity' (Opus 5.5 Antigravity),
    'ag46' (Opus 4.6 Antigravity), 'auto' (opus-auto / genspark: qualquer Opus 5.5) ou None (outros modelos)."""
    m = (modelo or "").lower()
    if "fable" in m:  # 13/11 (dona): Fable 5.2 tem limite próprio nas contas cc; acorda só quando o Fable volta
        return "fable"
    if m.startswith(("cc/", "claude/")):
        return "claude"
    if "opus-4-6" in m:
        return "ag46"
    if m.startswith(("antigravity/", "ag-opus", "ag-sonnet")):
        return "antigravity"
    if m.startswith(("opus-auto", "genspark-opus")):
        return "auto"
    return None


# 09/11 (dona): modo automático (pago ou grátis) acorda quando QUALQUER Opus 5.5 voltar, não só o cc
FONTES = {"claude": ("claude",), "antigravity": ("antigravity",), "ag46": ("ag46",), "fable": ("fable",),
          "auto": ("claude", "antigravity"), None: ("claude", "antigravity", "ag46")}


def credito(cota, prov):
    return sum(cota.get(p, 0) for p in FONTES.get(prov, FONTES[None]))


def falta_cota(erro):
    """Erro de crédito do OmniRoute (429 'exhausted their quota', 503 'pre-dispatch filters'): o chat não tem defeito."""
    return bool(re.search(r"exhausted their quota|pre-dispatch filters", erro or ""))


def ler_modo():
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.append(r"D:\video-fila")
        import melhorador_central as _mc
        return _mc.modo_tokens().get("modo")
    except Exception:  # noqa: BLE001
        return "normal"


def escolher(alvos, cota):
    """Quem acorda agora: erro mais antigo primeiro e, por provedor, no máximo as contas com crédito (mínimo MIN_POR_PROV)."""
    total = sum(cota.values())
    por_prov, escolhidos = {}, []
    # 09/11 (dona): modo do vigia de tokens (VPS 157, modo_tokens.py). 'gastar' (outra pessoa usando as contas ou a
    # janela de 5 h virando com saldo) = acorda TODOS os chats parados; 'poupar' (só nós) = só MIN_POR_PROV por provedor
    # (os mais antigos = os que pararam primeiro). Sem leitura = como antes.
    modo = ler_modo()
    if modo == "gastar":
        log(f"modo GASTAR: acordo os {len(alvos)} chat(s) parados")
        return sorted(alvos, key=lambda x: x["quando"] or "")
    for a in sorted(alvos, key=lambda x: x["quando"] or ""):
        # poupar/gastar vem das contas cc: só vale para chat que gasta cc
        poupa = modo == "poupar" and a["prov"] in ("claude", "fable", "auto", "qualquer")
        limite = MIN_POR_PROV if poupa else max(MIN_POR_PROV, credito(cota, a["prov"]) or total)
        if por_prov.get(a["prov"], 0) < limite:
            por_prov[a["prov"]] = por_prov.get(a["prov"], 0) + 1
            escolhidos.append(a)
    return escolhidos


def epoca_de(estado, prov):
    """Quantas vezes entrou crédito novo no provedor (uma conta renovou); sem provedor definido, a soma dos dois."""
    ep = estado.get("_epoca", {})
    return sum(ep.get(p, 0) for p in FONTES.get(prov, FONTES[None]))


MAX_TENTATIVAS = 3  # seguidas sem o chat voltar a responder; depois espera ESPERA_DEPOIS_MIN e tenta de novo
ESPERA_DEPOIS_MIN = 60
ESPERA_ENVIO_S = 240  # abaixo dos 5 min da tarefa, para uma rodada não encavalar na outra
MIN_POR_PROV = 2  # chats acordados por rodada em cada provedor, mesmo com uma só conta com crédito


def _agora_z():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _min_desde(iso_z):
    if not iso_z:
        return 1e9
    return (datetime.now(timezone.utc) - datetime.fromisoformat(iso_z.replace("Z", "+00:00"))).total_seconds() / 60


def avisar_dona(nome, sid, erro):
    """Chat que não volta nem com crédito: entra no RESUMO do Telegram (9h/14h/21h, bot do crédito), 1 vez a cada 12 h
    por chat. Dona 28/10: antes o sentinela desistia calado."""
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.append(r"D:\video-fila")  # no fim: pasta de outro projeto nunca na frente do sys.path
        import avisos
        avisos.enviar(f"Sentinela: o chat {nome} recebeu {MAX_TENTATIVAS} \"continue\" com crédito e continua dando "
                      f"erro ({erro[:90]}). Provável defeito do próprio chat: abra um chat novo para essa tarefa.",
                      "sentinela-credito", importante=False, chave=f"sentinela-desistiu-{sid}", html_ok=False)
    except Exception as falha:  # noqa: BLE001 — aviso nunca pode parar o sentinela
        log(f"aviso do Telegram falhou: {falha!r}")


# ---------------------------------------------------------------------------
# VS Code: detectar se está aberto, abrir, e ler abas salvas no state.vscdb
# ---------------------------------------------------------------------------

def vscode_aberto():
    """True se o VS Code está rodando."""
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Code.exe", "/FO", "CSV", "/NH"],
                           capture_output=True, timeout=15, creationflags=OCULTO)
        return b"Code.exe" in r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return True  # na dúvida, assume que está aberto (não tenta abrir de novo)


def abrir_vscode(simular=False):
    """Abre o VS Code na pasta d:\\ e espera os sessions/*.json aparecerem.
    Devolve True se abriu e os sessions apareceram, False se falhou."""
    if not os.path.isfile(CODE_CMD):
        log(f"code.cmd não encontrado em {CODE_CMD}")
        return False
    if simular:
        log("[simular] abriria o VS Code")
        return True
    log("abrindo o VS Code para os chats voltarem...")
    try:
        subprocess.Popen(["cmd", "/c", CODE_CMD, "--folder-uri", WORKSPACE_URI],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=OCULTO)
    except OSError as falha:
        log(f"não consegui abrir o VS Code: {falha!r}")
        return False
    inicio = time.monotonic()
    while time.monotonic() - inicio < ESPERA_VSCODE_ABRIR_S:
        time.sleep(ESPERA_VSCODE_POLL_S)
        sessoes = list((CFG / "sessions").glob("*.json"))
        if sessoes:
            log(f"VS Code abriu, {len(sessoes)} session(s) apareceram em {time.monotonic() - inicio:.0f}s")
            time.sleep(5)  # dar mais um tempo para todas as abas inicializarem
            return True
    log(f"VS Code não criou sessions/*.json em {ESPERA_VSCODE_ABRIR_S}s")
    return False


def ler_abas_vscdb():
    """Lê os panelTabSessions do state.vscdb do workspace d:\\ (as abas que estavam abertas quando o VS Code fechou).
    Devolve [{sessionId, title}, ...] ou [] se não conseguir ler."""
    storage = Path(os.path.expanduser(r"~\AppData\Roaming\Code\User\workspaceStorage"))
    if not storage.exists():
        return []
    for pasta in storage.iterdir():
        wj = pasta / "workspace.json"
        if not wj.exists():
            continue
        try:
            w = json.loads(wj.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if (w.get("folder") or "").lower().rstrip("/") != "file:///d%3a":
            continue
        db_path = pasta / "state.vscdb"
        if not db_path.exists():
            continue
        try:
            db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
            row = db.execute("SELECT value FROM ItemTable WHERE key=?", ("Anthropic.claude-code",)).fetchone()
            db.close()
            if not row:
                return []
            dados = json.loads(row[0])
            abas = dados.get("panelTabSessions", [])
            return [{"sessionId": a["sessionId"], "title": a.get("title", "")}
                    for a in abas if isinstance(a, dict) and a.get("sessionId")]
        except (sqlite3.Error, ValueError, OSError, KeyError) as falha:
            log(f"não consegui ler state.vscdb: {falha!r}")
            return []
    return []


# ---------------------------------------------------------------------------
# Chats parados por erro
# ---------------------------------------------------------------------------

def _avaliar_chat(sid, nome, status, estado, cota, voltou, motivos):
    """Avalia um chat e devolve o dict do alvo ou None."""
    quando, erro, modelo = ultimo_turno(sid)
    if not erro:
        estado.pop(sid, None)
        motivos.pop(sid, None)
        return None

    def pulou(motivo):
        if motivos.get(sid) != motivo:
            log(f"{nome}: parado por erro, sem continue: {motivo}")
            motivos[sid] = motivo

    # status só é confiável quando vem de sessions/*.json; com VS Code fechado passamos None
    if status is not None and status != "idle":
        pulou(f"status {status}")
        return None
    prov = provedor(modelo)
    if not credito(cota, prov):
        pulou(f"sem crédito de {prov or 'nenhum provedor'} ({modelo})")
        return None
    e = estado.get(sid, {})
    if e.get("em", "") >= (quando or ""):
        pulou("já recebeu continue depois deste erro, esperando ele responder")
        return None
    ep = epoca_de(estado, prov)
    novo_credito = ep > e.get("ep", 0)
    # 09/11 (dona): o chat já recebeu continue e errou de novo -> só repete quando voltar crédito de algum Opus
    # (antes repetia de 5 em 5 min em erro que não era de cota, ex.: "Opus 4.6 is no longer available")
    if e and not novo_credito:
        pulou("já recebeu continue e errou de novo: espera voltar crédito de algum Opus")
        return None
    if e.get("n", 0) >= MAX_TENTATIVAS and (
            _min_desde(e.get("em")) >= ESPERA_DEPOIS_MIN or novo_credito
            or any(p in voltou for p in FONTES.get(prov, FONTES[None]))):
        e = {"em": e.get("em", ""), "ep": ep, "n": 0}
    if e.get("n", 0) >= MAX_TENTATIVAS:
        if not e.get("avisado"):
            log(f"{nome}: parei de mandar continue ({MAX_TENTATIVAS} tentativas sem voltar): {erro[:100]}")
            avisar_dona(nome, sid, erro)
            estado[sid] = {**e, "avisado": True}
        return None
    return {"nome": nome, "sid": sid, "quando": quando, "erro": erro, "n": e.get("n", 0),
            "prov": prov or "qualquer"}


def parados_por_erro(estado, cota):
    """Chats parados por erro. Lê de sessions/*.json (VS Code aberto) OU do state.vscdb (VS Code fechado)."""
    antes = estado.get("_credito", {})
    voltou = {p for p, n in cota.items() if n > 0 and antes.get(p, 0) == 0}
    saida = []
    motivos = estado.setdefault("_motivo", {})

    # 1) VS Code aberto: ler de sessions/*.json (caminho normal)
    sessoes_json = list((CFG / "sessions").glob("*.json"))
    if sessoes_json:
        for f in sessoes_json:
            try:
                s = json.loads(f.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            sid = s.get("sessionId")
            if s.get("kind") != "interactive" or not sid:
                continue
            alvo = _avaliar_chat(sid, s.get("name"), s.get("status"), estado, cota, voltou, motivos)
            if alvo:
                saida.append(alvo)
        return saida

    # 2) VS Code fechado: ler as abas do state.vscdb e conferir o .jsonl de cada uma
    abas = ler_abas_vscdb()
    if not abas:
        return saida
    for aba in abas:
        sid = aba["sessionId"]
        nome = aba.get("title") or sid[:8]
        alvo = _avaliar_chat(sid, nome, None, estado, cota, voltou, motivos)
        if alvo:
            alvo["_vscode_fechado"] = True
            saida.append(alvo)
    return saida


def enviar(nomes, modelo=MODELO, espera=ESPERA_ENVIO_S):
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(CFG), ANTHROPIC_BASE_URL="http://157.173.207.22:20133",
               ANTHROPIC_API_KEY=CHAVE, ANTHROPIC_AUTH_TOKEN=CHAVE, ANTHROPIC_MODEL=modelo,
               ANTHROPIC_SMALL_FAST_MODEL=modelo, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    pedido = ("Use a ferramenta SendMessage para mandar a mensagem exata `continue` para cada uma destas sessões, "
              f"uma chamada por sessão: {', '.join(nomes)}. Não faça mais nada. No fim responda só com os nomes que "
              "deram certo.")
    p = subprocess.Popen([CLAUDE, "-p", pedido, "--model", modelo, "--allowedTools", "SendMessage,ListAgents",
                          "--output-format", "text",
                          # sem os hooks (voz, portões) e sem MCP: com eles o início levava 30–200 s e estourava (28/10)
                          "--settings", '{"disableAllHooks": true}', "--strict-mcp-config",
                          # 10/11: settings global em bypassPermissions -> chats seguravam o continue (modo diferente)
                          "--permission-mode", "default"],
                         env=env, cwd=r"D:\tmp", stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        out, _ = p.communicate(timeout=espera)
    except subprocess.TimeoutExpired:
        # o Gemini às vezes trava depois de mandar; mata a árvore e quem diz se chegou é o histórico do chat
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        out, _ = p.communicate()
        return "tempo", out.decode("utf-8", "replace").strip()[-400:]
    return p.returncode, out.decode("utf-8", "replace").strip()[-400:]


def chegou(sid, desde):
    """True se o histórico do chat tem mensagem 'continue' de outra sessão depois de `desde` (prova da entrega)."""
    tr = glob.glob(str(CFG / "projects" / "*" / f"{sid}.jsonl"))
    if not tr:
        return False
    with open(tr[0], "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 400_000))
        linhas = f.read().decode("utf-8", "replace").splitlines()
    for linha in reversed(linhas):
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if not d.get("timestamp"):
            continue  # snapshot/resumo sem horário: não serve de marco
        if d["timestamp"] < desde:
            break
        texto = json.dumps(d.get("message") or d.get("content"), ensure_ascii=False)
        if d.get("type") in ("user", "queue-operation") and "cross-session-message" in texto \
                and "continue" in texto.lower():
            return True
    return False


# envio em camadas (dona 30/10: "segundas e terceiras camadas"): 28 de 123 envios não chegavam (23%), 15 por tempo
# esgotado e 13 em que o Gemini disse que mandou mas pulou nomes. Testado 30/10: Sonnet web trava, Gemini Pro e Argon
# escrevem a chamada como texto (não mandam), Cline sem saldo; só o Opus 4.6 entregou de verdade.
# 06/11: o Opus 4.6 do Antigravity morreu ("no longer available") -> camada 2 = Opus 5.5 Antigravity (combo ag-opus-5-5).
MODELO_RESERVA = "ag-opus-5-5"
# 06/11 (dona "sim"): das 06:34 às 07:14 nenhum continue chegou — o Gemini levava 34 s só para responder "OK" e estourava.
# O cobrador do pesquisador entregou 2/2 com o Sonnet web hoje (em 30/10 ele travava aqui). Entra como camada 2b, sem
# tirar nenhuma camada antiga: Gemini todos -> Opus 4.6 -> Sonnet web -> Gemini um por vez.
MODELO_SONNET = "cw/claude-sonnet-5-5"


def entregar(alvos, cota):
    """Manda continue até chegar: 1) Gemini para todos; 2) Opus 4.6 para quem faltou (se o Antigravity tem crédito);
    3) Gemini um chat por vez. Devolve (quem recebeu, [(camada, rc, saída)])."""
    ok, tentativas = [], []

    def rodada(camada, grupo, modelo, espera):
        antes = _agora_z()
        rc, saida = enviar([a["nome"] for a in grupo], modelo, espera)
        time.sleep(10)  # o chat grava a mensagem recebida no histórico logo depois
        chegaram = [a for a in grupo if chegou(a["sid"], antes)]
        for a in chegaram:
            a["camada"], a["antes"] = camada, antes
        ok.extend(chegaram)
        tentativas.append((camada, rc, "" if len(chegaram) == len(grupo) else saida))

    rodada(1, alvos, MODELO, 150)
    falta = [a for a in alvos if a not in ok]
    if falta and (cota.get("antigravity", 0) or cota.get("ag46", 0)):
        rodada(2, falta, MODELO_RESERVA if cota.get("antigravity", 0) else "antigravity/claude-opus-4-6-thinking", 120)
    falta = [a for a in alvos if a not in ok]
    if falta:
        rodada("2b", falta, MODELO_SONNET, 120)
    for a in [a for a in alvos if a not in ok]:
        rodada(3, [a], MODELO, 90)
    return ok, tentativas


def main():
    simular = "--simular" in sys.argv
    try:
        estado = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        estado = {}
    leituras = [sc.consultar("claude"), sc.consultar("antigravity"), sc.consultar("ag46"), sc.consultar("fable")]
    cota = {p["provider"]: p.get("com_credito", 0) for p in leituras}
    # 2ª camada da leitura: ssh caiu = usa o último crédito lido, em vez de achar que é 0 e não acordar ninguém
    falhas = [p for p in leituras if p.get("erro")]
    for p in falhas:
        cota[p["provider"]] = estado.get("_credito", {}).get(p["provider"], 0)
    estado["_erro_leitura"] = estado.get("_erro_leitura", 0) + 1 if falhas else 0
    if falhas:
        log(f"leitura de crédito falhou ({estado['_erro_leitura']}ª seguida), uso o último valor: "
            + "; ".join(f"{p['provider']}: {str(p['erro'])[:120]}" for p in falhas))
    BATIMENTO.write_text(json.dumps({"em": _agora_z(), "cota": cota, "erro_leitura": estado["_erro_leitura"]}),
                         encoding="utf-8")  # a vigia (sentinela_vigia.py) confere que o sentinela está rodando
    # crédito novo no provedor (uma conta renovou): quem desistiu tenta de novo na hora; a 2ª conta de 17:20 não acordou ninguém (29/10)
    epoca = estado.setdefault("_epoca", {})
    for p in leituras:
        if not p.get("erro") and p.get("com_credito", 0) > estado.get("_credito", {}).get(p["provider"], 0):
            epoca[p["provider"]] = epoca.get(p["provider"], 0) + 1
    # 09/11 (dona): outra pessoa começou a usar as contas cc (modo gastar) = vale como crédito novo do cc:
    # acorda também os chats que já tinham recebido continue e estavam esperando
    modo = ler_modo()
    if modo == "gastar" and estado.get("_modo") != "gastar":
        epoca["claude"] = epoca.get("claude", 0) + 1
        log("modo GASTAR começou (outra pessoa usando as contas cc ou janela de 5 h virando com saldo)")
    estado["_modo"] = modo
    alvos = parados_por_erro(estado, cota)

    # --- limpeza de estado de chats que não existem mais ---
    # só limpa quando o VS Code está aberto (sessions/*.json existe); com ele fechado, os .json somem
    # e limpar aqui apagaria o estado de todos os chats (bug de 03/11)
    sessoes_json = list((CFG / "sessions").glob("*.json"))
    if sessoes_json:
        vivos, leu_todas = set(), True
        for f in sessoes_json:
            try:
                vivos.add(json.loads(f.read_text(encoding="utf-8")).get("sessionId"))
            except (ValueError, OSError):
                leu_todas = False
        # também considerar "vivos" os chats que o vscdb conhece (abas sem processo ativo)
        for aba in ler_abas_vscdb():
            vivos.add(aba["sessionId"])
        if leu_todas:
            for sid in [k for k in estado if not k.startswith("_") and k not in vivos]:
                del estado[sid]
            for sid in [k for k in estado.get("_motivo", {}) if k not in vivos]:
                del estado["_motivo"][sid]
    # crédito desta rodada, para a próxima perceber quando ele volta; leitura com erro (ssh caiu) não conta
    credito = estado.setdefault("_credito", {})
    credito.update({p["provider"]: p.get("com_credito", 0) for p in leituras if not p.get("erro")})
    if simular:
        log(f"[simular] crédito cc={cota.get('claude')} ag55={cota.get('antigravity')} ag46={cota.get('ag46')} fable={cota.get('fable')}"
            f" vscode={'aberto' if sessoes_json else 'FECHADO'}")
        for a in alvos:
            extra = " [VS Code fechado, abriria]" if a.get("_vscode_fechado") else ""
            log(f"[simular] receberia: {a['nome']} (depende de {a['prov']}, {a['n']} tentativas){extra} {a['erro']}")
        if not alvos:
            log("[simular] nenhum chat parado que o crédito de agora resolva")
        return
    ESTADO.write_text(json.dumps(estado, indent=1), encoding="utf-8")
    if not alvos:
        return

    # --- se o VS Code está fechado e há alvos, abre ele primeiro ---
    precisa_abrir = any(a.get("_vscode_fechado") for a in alvos)
    if precisa_abrir:
        if not vscode_aberto():
            abriu = abrir_vscode(simular=False)
            if not abriu:
                log("não consegui abrir o VS Code, tentando na próxima rodada")
                return
            # re-ler os alvos agora que o VS Code está aberto e os sessions/*.json existem
            alvos = parados_por_erro(estado, cota)
            if not alvos:
                log("VS Code abriu mas nenhum chat precisa de continue agora")
                return
        else:
            # VS Code aberto mas sessions/*.json ainda não apareceu (pode estar iniciando)
            log("VS Code parece aberto mas sessions/*.json ainda não apareceu, esperando...")
            inicio = time.monotonic()
            while time.monotonic() - inicio < 30:
                time.sleep(5)
                if list((CFG / "sessions").glob("*.json")):
                    break
            alvos = parados_por_erro(estado, cota)
            if not alvos:
                return

    # com pouca cota, mandar continue para muitos de vez faz todos disputarem a mesma conta e todos perderem (429):
    # por provedor só tantos chats quanto contas com crédito (mínimo 2), o erro mais antigo primeiro
    # (dona 29/10: 7 chats acordaram com 1 conta, gastaram em segundos e as 3 tentativas acabaram em 15 min)
    escolhidos = escolher(alvos, cota)
    if len(escolhidos) < len(alvos):
        log(f"limitando ao crédito: {len(alvos) - len(escolhidos)} chat(s) ficam para a próxima rodada")
    alvos = escolhidos

    ok, tentativas = entregar(alvos, cota)
    falhou = [a["nome"] for a in alvos if a not in ok]
    log(f"crédito cc={cota.get('claude')} ag55={cota.get('antigravity')} ag46={cota.get('ag46')} -> continue para "
        f"{', '.join(a['nome'] + '(' + a['prov'] + ')' for a in alvos)} "
        f"chegou: {', '.join(a['nome'] + '[camada ' + str(a['camada']) + ']' for a in ok) or 'nenhum'}"
        + (f" | NÃO chegou: {', '.join(falhou)} " + " ".join(f"c{c} rc={rc} {s[-150:]!r}" for c, rc, s in tentativas if s)
           if falhou else ""))
    for a in ok:  # só conta tentativa no chat que recebeu de verdade; erro de falta de crédito não conta (não é defeito do chat)
        # "em" = antes do envio que chegou: um erro que o chat der depois disso conta como novo
        estado[a["sid"]] = {"em": a["antes"], "ep": epoca_de(estado, a["prov"]),
                            "n": a["n"] + (0 if falta_cota(a["erro"]) else 1)}
    ESTADO.write_text(json.dumps(estado, indent=1), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:  # pythonw não mostra nada: sem isto um erro some calado
        log(f"ERRO: {erro!r}")
        raise
