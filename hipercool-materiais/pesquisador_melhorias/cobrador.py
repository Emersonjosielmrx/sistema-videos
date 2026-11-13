r"""cobrador.py - de hora em hora manda ao chat de cada linha os achados PENDENTES do pesquisador (dona 04/11/2026).

"Ele não implanta nada: faz como o vigia que manda 'continue' nos chats, só que com as descobertas, pedindo aos chats
que analisem se faz sentido, implantem o que der e retornem documentado (o que foi implantado e o que não, e por quê),
para o pesquisador não pesquisar mais a mesma coisa." / 05/11: "se não houver resposta dos chats ele manda de novo,
porque pode ser que não tenha recebido".

Tarefa do Windows CobradorPesquisador (1 em 1 h, oculta):  python cobrador.py   (--simular = só mostra)
Ciclo por linha (CURTOS, LONGOS, CAPAS, VEO_HIPERCOOL):
  1. chat da linha = chats_linhas.json (`motor_pesquisador.py sou <LINHA> <nome>`); aberto? = ~\.claude-vscode\sessions
     (nome -> sessionId -> histórico). Fechado = não manda e mostra no painel.
  2. ENTREGA PROVADA: cada mensagem leva um código [cobranca LINHA-AAAAMMDDHHMM]. Na volta seguinte o código tem que
     estar no histórico do chat; não está = manda de novo (até 3x; depois avisa no painel/log).
  3. RESPOSTA MEDIDA: progresso = blocos [x] AVALIADO + retornos (implantados/reprovados) daquela linha. Chegou e
     nada mudou em 3 h = lembrete (até 3; depois "chat não responde" no painel). Bloco novo na caixa = mensagem nova.
Envio: claude.exe -p com o Gemini (agy/gemini-3.8-flash-high, não gasta Opus) usando SendMessage — igual ao sentinela.
Log: cobrador.log | estado: cobrador_estado.json (lido também pelo painel do motor)
"""
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import motor_pesquisador as m  # noqa: E402

LOG = BASE / "cobrador.log"
ESTADO = BASE / "cobrador_estado.json"
# 06/11: o Gemini levava 34 s só para responder "OK" e estourava 240 s ao chamar o SendMessage (o sentinela também).
# Sonnet web: 7 s, também não gasta Opus. Gemini fica como 2ª tentativa.
MODELOS = ["gemini/gemini-2.5-flash-lite", "gemini-4-argon"]  # 09/11 dona: 2.5 como fallback; 2.5-flash-lite entregou em 15 s (prova no histórico); Argon de reserva; Antigravity e Sonnet travam
MODELO = MODELOS[0]
CFG = Path(os.path.expanduser(r"~\.claude-vscode"))  # config dos chats: o SendMessage precisa achar as sessões
LEMBRETE_H = 3          # chegou e o chat não mexeu em nada nesse tempo -> lembrete
MAX_REENVIO = 3         # não chegou -> reenvia até 3x
MAX_LEMBRETE = 3        # 3 lembretes sem progresso -> "chat não responde"


def log(msg):
    linha = f"{datetime.now():%d/%m %H:%M:%S} {msg}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


# ------------------------------------------------------------------ sessões abertas (igual ao sentinela)

def vivo(pid):
    return m.vivo(pid)  # 05/11: a versão daqui quebrava com acento do tasklist; usa a do motor (lê bytes)


def sessoes():
    """nome -> {sid, status, pid} só das sessões interativas com processo vivo."""
    out = {}
    for f in glob.glob(str(CFG / "sessions" / "*.json")):
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if d.get("kind") != "interactive" or not d.get("name") or not vivo(d.get("pid", 0)):
            continue
        out[d["name"]] = {"sid": d.get("sessionId"), "status": d.get("status"), "pid": d.get("pid")}
    return out


def chegou(sid, codigo):
    """True se o histórico do chat tem o código da cobrança (prova de que a mensagem foi entregue)."""
    for f in glob.glob(str(CFG / "projects" / "*" / f"{sid}.jsonl")):
        try:
            with open(f, "rb") as fh:
                fh.seek(max(0, os.path.getsize(f) - 6_000_000))
                if codigo.encode() in fh.read():
                    return True
        except OSError:
            pass
    return False


# ------------------------------------------------------------------ caixa e progresso

def caixa(linha):
    arq = m.ENTREGAS / f"{linha}.md"
    t = arq.read_text(encoding="utf-8") if arq.exists() else ""
    pend = [l[len("## [ ] PENDENTE — "):].strip() for l in t.splitlines() if l.startswith("## [ ] PENDENTE")]
    avaliados = t.count("## [x] AVALIADO")
    return pend, avaliados


def progresso(linha):
    """Número que só cresce quando o chat da linha trabalha: avaliados + implantados + reprovados dele."""
    _, av = caixa(linha)
    ret = sum(1 for r in m.implantados() + m.reprovados() if str(r.get("quem", "")).upper().startswith(linha))
    return av + ret


def mensagem(linha, blocos, codigo, tipo):
    temas = ", ".join(sorted({re.sub(r"^.*? — ", "", b).split(" (`")[0] for b in blocos}))[:300]
    abre = {"nova": "", "reenvio": "(reenvio: a anterior parece não ter chegado) ",
            "lembrete": "(lembrete: nada foi avaliado desde a última) "}[tipo]
    nomes = {"CURTOS": "VÍDEOS CURTOS (Shorts/cortes)", "LONGOS": "VÍDEOS LONGOS", "CAPAS": "CAPAS/IMAGEM dos vídeos",
             "VEO_HIPERCOOL": "VEO/HIPERCOOL"}
    return (f"SÓ PARA O CHAT DA LINHA {nomes.get(linha, linha)}. Se este chat NÃO trabalha nessa linha de vídeo, "
            f"IGNORE esta mensagem: não responda, não rode nada e siga o que estava fazendo. "
            f"[cobranca {codigo}] Pesquisador {abre}(pedido da dona, de hora em hora): a caixa "
            f"D:\\hipercool-materiais\\pesquisador_melhorias\\ENTREGAS\\{linha}.md tem {len(blocos)} bloco(s) "
            f"[ ] PENDENTE ({temas}). Quando puder, sem largar a prioridade atual da dona: analise se faz sentido para o "
            f"projeto, implante o que der seguindo video-fila\\aprendizado\\LEIA_ANTES_DE_MELHORAR.md, e RETORNE "
            f"documentado. Implantou: python D:\\hipercool-materiais\\pesquisador_melhorias\\motor_pesquisador.py "
            f"implantado dono/repo \"arquivo/função e chave que desliga\" {linha}. Não serve: ... reprovar dono/repo "
            f"\"motivo\" {linha}. Deixou para depois: escreva o porquê no bloco. No fim troque [ ] PENDENTE por "
            f"[x] AVALIADO <data> — X implantados, Y reprovados, Z deixados.")


def enviar(nome, texto):
    erro = ""
    for modelo in MODELOS:
        ok, saida = _enviar(nome, texto, modelo)
        if ok:
            return True, saida
        erro = f"{modelo}: {saida[-150:]}"
    return False, erro


def _enviar(nome, texto, modelo):
    exe = m.claude_exe()
    if not exe:
        return False, "claude.exe não achado"
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(CFG), ANTHROPIC_BASE_URL=m.OMNIROUTE, ANTHROPIC_API_KEY=m.CHAVE,
               ANTHROPIC_AUTH_TOKEN=m.CHAVE, ANTHROPIC_MODEL=modelo, ANTHROPIC_SMALL_FAST_MODEL=modelo,
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    pedido = (f"Use a ferramenta SendMessage UMA vez: to = \"{nome}\", e message = o texto entre <<< e >>> EXATAMENTE "
              f"como está, sem mudar nada. Não faça mais nada. No fim responda só ENVIADO ou o erro que deu.\n"
              f"<<<{texto}>>>")
    try:
        # 07/11: com o pedido pelo stdin o Gemini gerava >64 mil tokens e o Sonnet travava (59 falhas desde 06/11
        # 17h); o sentinela passa o pedido como ARGUMENTO do -p e entrega. Igual a ele agora.
        p = subprocess.run([exe, "-p", pedido, "--model", modelo, "--output-format", "text",
                            "--allowedTools", "SendMessage,ListAgents",
                            "--settings", '{"disableAllHooks": true}', "--strict-mcp-config",
                            # 10/11: o settings global virou bypassPermissions e os chats SEGURAM mensagem de modo
                            # diferente (nada chegou de 07:17 a 15:40). Modo fixo aqui: entregou com prova.
                            "--permission-mode", "default"],
                           stdin=subprocess.DEVNULL, capture_output=True, env=env, cwd=r"D:\tmp", timeout=180,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        return False, "retransmissor passou de 120 s (OmniRoute travou no pedido com ferramenta)"
    out = p.stdout.decode("utf-8", "replace").strip()
    ok = p.returncode == 0 and "ENVIADO" in out.upper()
    return ok, out[-300:]


# ------------------------------------------------------------------ ciclo

def main():
    simular = "--simular" in sys.argv
    est = m.q._ler_json(str(ESTADO), {})
    agora = datetime.now()
    chats = m.chats_linhas()
    abertas = sessoes()
    for linha in m.LINHAS:
        pend, _ = caixa(linha)
        e = est.setdefault(linha, {})
        e["pendentes"] = len(pend)
        if not pend:
            e["situacao"] = "em dia"
            continue
        chat = chats.get(linha)
        if not chat:
            e["situacao"] = "sem chat registrado"
            log(f"{linha}: {len(pend)} pendente(s), nenhum chat registrado (quem abrir: `motor_pesquisador.py sou {linha} <nome>`)")
            continue
        nome = chat["nome"]
        sess = abertas.get(nome)
        # 06/11: o nome muda quando o VS Code reinicia (claude-42 -> claude-ef), o id do histórico não. Acha pelo id.
        if chat.get("sid") and (not sess or sess["sid"] != chat["sid"]):
            novo = next((n for n, s in abertas.items() if s["sid"] == chat["sid"]), None)
            if novo:
                log(f"{linha}: chat da linha mudou de nome {nome} -> {novo} (mesmo histórico); atualizado")
                todos = m.chats_linhas()
                for ln, c in todos.items():
                    if c.get("sid") == chat["sid"]:
                        c["nome"] = novo
                m.q._gravar_json(str(m.CHATS), todos)
                nome, sess = novo, abertas[novo]
        if not sess:
            e["situacao"] = f"chat {nome} FECHADO"
            log(f"{linha}: {len(pend)} pendente(s), mas o chat {nome} não está aberto; espera um chat novo se registrar")
            continue
        # 05/11: nomes se repetem entre sessões. O nome agora é de OUTRO chat (talvez nem de vídeo)? Não manda.
        if chat.get("sid") and sess["sid"] != chat["sid"]:
            e["situacao"] = f"o nome {nome} agora é de outro chat — esperando o chat da linha se registrar de novo"
            log(f"{linha}: {nome} mudou de sessão ({chat['sid'][:8]} -> {sess['sid'][:8]}); NÃO mando para não "
                f"cair em chat de outro assunto")
            continue

        # 1) a última cobrança chegou?
        ult = e.get("ultima")
        tipo = None
        if ult and not ult.get("chegou"):
            if chegou(sess["sid"], ult["codigo"]):
                ult["chegou"] = agora.isoformat(timespec="minutes")
                log(f"{linha}: cobrança {ult['codigo']} CHEGOU em {nome}")
            elif ult.get("tentativas", 1) >= MAX_REENVIO:
                e["situacao"] = f"{MAX_REENVIO} envios sem chegar em {nome} — conferir o chat"
                log(f"{linha}: ALERTA {e['situacao']}")
                continue
            else:
                tipo = "reenvio"
        # 2) o chat respondeu desde que recebeu?
        prog = progresso(linha)
        novos = [b for b in pend if b not in e.get("blocos_enviados", [])]
        desde_ult = agora - datetime.fromisoformat(ult["em"]) if ult else None
        if tipo is None:
            # bloco novo só gera mensagem nova se a última foi há >= 3 h (não atropelar chat no meio da avaliação)
            if not ult or (novos and desde_ult >= timedelta(hours=LEMBRETE_H)):
                tipo = "nova"
            elif ult.get("chegou"):
                if prog > ult.get("progresso", 0):
                    e["lembretes"] = 0
                    e["situacao"] = f"respondendo ({prog - ult.get('progresso', 0)} retorno(s) desde a cobrança)"
                    ult["progresso"] = prog  # mexeu: zera o relógio do lembrete
                    ult["em"] = agora.isoformat(timespec="minutes")
                    continue
                if agora - datetime.fromisoformat(ult["em"]) >= timedelta(hours=LEMBRETE_H):
                    if e.get("lembretes", 0) >= MAX_LEMBRETE:
                        e["situacao"] = f"chat {nome} NÃO RESPONDE ({MAX_LEMBRETE} lembretes)"
                        log(f"{linha}: ALERTA {e['situacao']}")
                        continue
                    tipo = "lembrete"
        if tipo is None:
            e["situacao"] = "aguardando o chat (cobrança entregue)"
            continue

        codigo = f"{linha}-{agora:%Y%m%d%H%M}"
        texto = mensagem(linha, pend, codigo, tipo)
        if simular:
            log(f"[simular] {linha} -> {nome} ({sess['status']}): {tipo}, {len(pend)} pendente(s), {len(novos)} novo(s)")
            continue
        ok, saida = enviar(nome, texto)
        if not ok:
            e["situacao"] = f"envio falhou: {saida[:120]}"
            log(f"{linha} -> {nome}: NÃO enviou ({saida})")
            continue
        tent = (ult.get("tentativas", 1) + 1) if tipo == "reenvio" else 1
        e["ultima"] = {"codigo": codigo, "em": agora.isoformat(timespec="minutes"), "tipo": tipo, "chegou": None,
                       "tentativas": tent, "progresso": prog}
        e["blocos_enviados"] = sorted(set(e.get("blocos_enviados", [])) | set(pend))
        if tipo == "lembrete":
            e["lembretes"] = e.get("lembretes", 0) + 1
        e["situacao"] = f"{tipo} enviada {agora:%H:%M}, conferindo entrega na próxima volta"
        log(f"{linha} -> {nome}: {tipo} [{codigo}] com {len(pend)} pendente(s) ({len(novos)} novo(s))")
    if not simular:
        m.q._gravar_json(str(ESTADO), est)
        m.painel()


if __name__ == "__main__":
    main()
