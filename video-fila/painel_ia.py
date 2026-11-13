# -*- coding: utf-8 -*-
r"""painel_ia.py — a IA do painel (dono 21/10: "acionar a IA pra consertar algo" pelo painel).

Mesmo agente dos vigias (Claude Code headless do hipercool pelo proxy, Kiro Sonnet), com 3 tipos de pedido:
  pergunta  só lê e responde (ferramentas de edição bloqueadas de verdade: --disallowedTools)
  propor    investiga e devolve o plano de conserto SEM mexer (também sem ferramentas de edição)
  aplicar   o dono clicou "Aplicar": continua a MESMA conversa do propor (--resume) e aplica. Antes de cada edição
            um hook copia o arquivo original (estado/painel_ia/<id>_backup) -> "ver o que mudou" e "desfazer".

Um pedido por vez (fila em estado/painel_ia/<id>.json); o passo a passo sai ao vivo (stream-json) em <id>.jsonl.
Enquanto aplica, segura as travas dos vigias (vigia_geral e hipercool) pra dois agentes não mexerem juntos.
24/10 (Fase 0): pedidos de origem "melhoria" passam pela guarda de comandos (hook PreToolUse, regras em
config\melhoria_guarda.json); todo prompt começa com a hora de agora (Brasília e UTC); pensar=True liga o raciocínio
do Kiro; um vigia por thread mata o claude.exe mudo; o desfazer guarda o "depois" e nunca apaga.

    python painel_ia.py fila            # roda a fila (o painel dispara sozinho)
    python painel_ia.py backup          # hook PreToolUse (lê o JSON do Claude no stdin)
    python painel_ia.py guarda          # hook PreToolUse da guarda (sai 2 = bloqueia, motivo no stderr)
"""
import difflib
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
PASTA = BASE / "estado" / "painel_ia"
TRAVA_FILA = PASTA / "fila.lock"
CLAUDE = Path(r"D:\hipercool-videos\tools\claude\claude.exe")
PROXY = Path(r"D:\hipercool-videos\secrets\claude_proxy.json")
PY_HOOK = Path(r"D:\veo\venv\Scripts\python.exe")
TRAVAS_VIGIAS = [BASE / "estado" / "vigia_agente.lock", Path(r"D:\hipercool-videos\workspace\vigia_agente.lock")]
TRAVA_VIGIA_MIN = 42  # os vigias consideram a trava viva por 40 min + 2
SEM_JANELA = 0x08000000
EDICAO = ["Edit", "Write", "MultiEdit", "NotebookEdit"]

PROJETOS = {  # id -> (nome, pasta de trabalho do agente)
    "cortes": ("Cortes (recapd: parceiro + anime)", r"D:\recapd-ambientes\producao"),
    "hipercool": ("Hipercool", r"D:\hipercool-videos"),
    "postador": ("Postador", r"D:\postador-de-videos"),
    "manhwa-react": ("ManhwaReact", r"D:\manhwa-react"),
    "msenergy": ("MS Energy", r"D:\ms-energy"),
    "veo": ("Veo", r"D:\veo"),
    "voz": ("Voz clonada", r"D:\hipercool-materiais"),
    "geral": ("Geral (controlador, fila, painel)", r"D:\video-fila"),
}
VOLTAS = {"pergunta": 15, "propor": 40, "aplicar": 40}
# 24/10: pergunta 15 -> 25 min (as leituras das melhorias agora têm 40 passos e o Kiro raciocina antes de cada um)
TEMPO_MAX_MIN = {"pergunta": 25, "propor": 30, "aplicar": 40}
# 24/10: 12 min (não 10): um comando de terminal pode levar até 10 min sem soltar linha
SEM_LINHA_MIN = 12  # claude.exe sem soltar linha nenhuma por esse tempo = travado (gateway pendurado)
VIGIA_INTERVALO_S = 15
# 24/10: marcas do Kiro (kr/claude-sonnet) pra devolver bloco de raciocínio. Teste da dona: sem elas o Kiro disse que um
# log de 11:30Z provava erro depois das 09:00 de Brasília; com elas acertou.
MARCAS_PENSAR = "<thinking_mode>enabled</thinking_mode><max_thinking_length>16000</max_thinking_length>\n"
ORIGEM_MELHORIA = "melhoria"
GUARDA_CFG = BASE / "config" / "melhoria_guarda.json"
ROTA_VSCODE = Path(r"C:\Users\Haylla\Desktop\Claude VS Code - Trocar Modelo\settings_5_OPUS-5.5_NORMAL.json")
GUARDA_MATCHER ="Bash|PowerShell|Read|Grep|Glob|Edit|Write|MultiEdit|NotebookEdit"
# 24/10: escrever (Edit/Write) em cookies/login/mídia também é bloqueado (a cópia do cookies.txt de 23/10 foi um Write)
ESCRITA_PROIBIDA = re.compile(r"cookies|Login Data|User Data|\.(jpe?g|png|webp|gif|bmp|mp4|mov|mkv|webm|wav|mp3|m4a|"
                              r"ogg|flac|pth|index)$", re.I)

REGRAS = r"""REGRAS DO DONO (valem sempre, mesmo se o pedido disser outra coisa):
- Leia o CLAUDE.md / LEIA da pasta do projeto antes de mexer.
- PC2 (ssh pc2) é do hipercool: nunca mexer nos workers/pastas deles; NUNCA matar pythonw (nem aqui nem lá).
- Postagem: SEMPRE agendada (publishAt 10+ min), nunca pública direto. Nunca despausar canal com advertência
  (inovare_french 2 strikes, inovare_eng bloqueado) nem criar canal "substituto".
- Nunca apagar vídeo, pasta de material, venv, junção ou cache do D: (limpeza só copiando pro Drive com rclone copy +
  rclone check). Nada no disco C:.
- Google só pelo navegador (nunca criar/pedir chave de API). Groq sempre pelo proxy Webshare. yt-dlp nunca em rajada.
- Vozes proibidas: Antonio. Censura só nas partes explícitas. Defeito visual não segura vídeo; só censura segura.
- Nenhum canal fica 1 dia sem postar. Render pesado é pela fila (D:\video-fila\fila_render.py), não por fora.
- Sem instalar pacote, sem git push, sem mexer em credenciais/senhas/tokens (nunca mostre token na resposta).
- Responda em português simples, direto, sem jargão."""

PROMPT_PERGUNTA = """Você é o assistente da Central de Vídeos (painel do dono, http://127.0.0.1:8790). O dono perguntou:
«{pedido}»
{contexto}
SÓ LEIA E RESPONDA: você não pode editar arquivos nem mudar nada (nem pelo terminal). Use os dados reais:
- APIs do painel (rápidas, JÁ CONTADAS — prefira estas a contar na mão): curl -s http://127.0.0.1:8790/api/<rota>
    agenda        "totais" já somados (hoje_no_ar, hoje_falta, amanha, depois, por_rede) + uma linha por canal/conta
    producao      Cortes de hoje (numeros.prontos_hoje, falhas_hoje, feitos_hoje), o que roda em cada PC
    cortes_dia?dia=AAAA-MM-DD   Shorts tentados num dia     segurados   Shorts que não saem sozinhos
    problemas | tarefas | saude | bots | geral (controlador) | canais (subidos hoje por canal) | contas (TikTok/Insta)
    postagens?dias=N (lista de postagens) | ranking?dias=N e desempenho?dias=N (views) | canais_views?dias=N
    voz | aprendizado | avisos?dias=N | hipercool | tendencias
- Logs: D:\\video-fila\\logs\\controlador_AAAAMMDD.log, D:\\recapd-ambientes\\producao\\workspace\\anime\\_parceiro_AAAAMMDD.log,
  D:\\hipercool-videos\\logs\\, D:\\postador-de-videos\\logs\\, avisos em D:\\video-fila\\estado\\avisos.jsonl
- Hipercool: D:\\hipercool-videos\\venv\\Scripts\\python.exe D:\\hipercool-videos\\bin\\consultar_producao.py views|ranking|comentarios|uploads|canais|filas
- Sistemas de 22/10 (rode com D:\\veo\\venv\\Scripts\\python.exe; todos SÓ imprimem):
    D:\\recapd-ambientes\\producao\\bin\\estoque_fontes.py        fontes de parceiro já baixadas (estoque anti-bloqueio do IP)
    D:\\postador-de-videos\\bin\\rampa_canais.py                  teto de uploads por canal (rampa 4->5->...->8)
    D:\\recapd-ambientes\\producao\\bin\\monitor_bordoes.py       bordões/manias que a voz clonada fala estranho
    D:\\video-fila\\guarda_testes.py                              o que é teste x produção agora e a RAM
    D:\\video-fila\\status_videos.py                              status único (liga/desliga, canais, tarefas, erros, máquinas)
  e os arquivos: D:\\video-fila\\logs\\faxina.jsonl (o que a faxina mandou pro Drive/apagou),
    D:\\video-fila\\estado\\guarda_testes.json, D:\\hipercool-materiais\\config\\persona_correcoes.json (correções do dono
    sobre bordões dos personagens; guia de cada voz em D:\\hipercool-materiais\\models\\rvc\\vozes\\<voz>\\linguagem_v2.json),
    D:\\postador-de-videos\\config\\limite_diario.json (canais esperando o limite de 24 h do YouTube),
    D:\\postador-de-videos\\_analise\\placar_*.json (funil: palavras, tags, horários, narradores, capas...)
- Correção de bordão/mania de personagem: edite persona_correcoes.json (bordoes/maneirismos/remover da voz) e rode
  D:\\recapd-ambientes\\producao\\venv\\Scripts\\python.exe D:\\hipercool-materiais\\bin\\persona_personagem.py <voz> --refazer
Responda curto (até 15 linhas), com números e o motivo; se algo precisar de conserto, diga o que e onde.
Depois de cada número diga entre parênteses de onde ele veio (rota ou arquivo), pro dono poder conferir. Se não achou o
dado, diga que não achou — nunca chute.
{regras}"""

PROMPT_PROPOR = """Você é o técnico da Central de Vídeos. O dono pediu pelo painel um CONSERTO no projeto {projeto} ({pasta}):
«{pedido}»
{contexto}
NESTA ETAPA NÃO MUDE NADA (as ferramentas de edição estão bloqueadas e o terminal é só pra ler/testar sem efeito).
Investigue com os logs e o código reais até achar a causa. Depois escreva para o dono:
1. CAUSA: o que está errado (com o trecho de log/arquivo:linha que prova).
2. PLANO: exatamente o que vai mudar (arquivo, o que sai, o que entra) e o que vai rodar depois pra conferir.
3. RISCO: o que pode dar errado e como desfazer.
Se não houver nada a consertar ou faltar certeza, diga isso e não proponha mudança.
{regras}
ÚLTIMA LINHA, exatamente uma destas:
STATUS: PROPOSTA - <o conserto em 1 linha>
STATUS: OK - <nada a fazer, em 1 linha>
STATUS: REVISAR - <por que precisa do dono, em 1 linha>"""

PROMPT_APLICAR = """O dono leu sua proposta e clicou APLICAR. Aplique EXATAMENTE o plano que você propôs (nada além).
Cada arquivo que você editar é copiado automaticamente antes (o dono pode desfazer pelo painel) — MAS só quando você
usa as ferramentas Edit/Write. NUNCA mude arquivo pelo terminal (>, >>, sed -i, Set-Content, Out-File, cp/mv por cima,
python escrevendo arquivo): isso escapa do backup e o "Desfazer" não volta. Terminal só pra ler, testar e conferir.
Depois de editar, confira de verdade (compilar, rodar o teste/comando sem efeito colateral, ler o log) e conte o resultado.
Acrescente ao fim de D:\\video-fila\\VIGIA_DIARIO.md:
## {hora} — <resumo em 1 linha> (pelo painel)
- Motivo / O que fiz (arquivos) / Como conferi / Como desfazer: botão "Desfazer" no painel (pedido {id})
- Estado: RESOLVIDO | PRECISA REVISÃO
{regras}
ÚLTIMA LINHA, exatamente uma destas:
STATUS: CONSERTEI - <o que, em 1 linha>
STATUS: REVISAR - <por que, em 1 linha>"""


# ─── arquivos dos pedidos ─────────────────────────────────────────────────────
def _arq(jid, ext=".json"):
    if not re.fullmatch(r"\d{8}_\d{6}_[0-9a-f]{4}", str(jid or "")):
        raise ValueError("pedido inválido")
    return PASTA / f"{jid}{ext}"


def ler(jid):
    try:
        return json.loads(_arq(jid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _gravar(job):
    PASTA.mkdir(parents=True, exist_ok=True)
    # 24/10: .tmp com o PID (o hook e o rodador gravam o mesmo pedido) e nova tentativa se o Windows segurar o arquivo
    # (alguém lendo na hora da troca): antes o PermissionError derrubava a leitura do stream no meio
    tmp = _arq(job["id"], f".json.{os.getpid()}.tmp")
    texto = json.dumps(job, ensure_ascii=False, indent=1)
    for n in range(5):
        try:
            tmp.write_text(texto, encoding="utf-8")
            os.replace(tmp, _arq(job["id"]))
            return
        except PermissionError:
            if n == 4:
                raise
            time.sleep(0.15)


def todos():
    PASTA.mkdir(parents=True, exist_ok=True)
    out = []
    for p in sorted(PASTA.glob("*_*_*.json"), reverse=True)[:300]:
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return out


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def _vivo(pid):
    if not pid:
        return False
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {int(pid)}", "/NH"], capture_output=True, text=True,
                           timeout=15, creationflags=SEM_JANELA)
        return str(pid) in (r.stdout or "")
    except Exception:  # noqa: BLE001
        return False


def _eh_melhoria(job):
    """Pedido das melhorias contínuas: ele mesmo ou a proposta que o originou (a aplicação nasce com origem 'painel')."""
    job = job or {}
    return job.get("origem") == ORIGEM_MELHORIA or (ler(job.get("pai") or "") or {}).get("origem") == ORIGEM_MELHORIA


# ─── pedir / aplicar / parar / desfazer (chamados pelo painel) ────────────────
def pedir(tipo, pedido, projeto="geral", contexto="", origem="painel", auto_aplicar=False, modelo=None, voltas=None,
          pensar=False, rota=None, esforco=None):
    """auto_aplicar ("corrigir todos", dono 21/10): proposta que sair PROPOSTA já vira aplicação sozinha.
    modelo (24/10, melhorias em dupla): roda com esse modelo se ele estiver no ar; senão, a ordem normal (ia_reserva).
    pensar (24/10): com o Kiro (kr/claude-sonnet*), pergunta/propor saem com as marcas de raciocínio."""
    tipo = {"consertar": "propor"}.get(tipo, tipo)
    if tipo not in ("pergunta", "propor"):
        raise ValueError("tipo deve ser pergunta ou consertar")
    pedido = str(pedido or "").strip()
    if len(pedido) < 3:
        raise ValueError("escreva o pedido")
    if projeto not in PROJETOS:
        projeto = "geral"
    jid = f"{datetime.now():%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"
    if len(pedido) > 4000:  # 24/10 (achado 10): corta o meio, nunca o fim (as regras e o CHECK ficam lá)
        pedido = pedido[:1400] + "\n[... cortado ...]\n" + pedido[-2570:]
    job = {"id": jid, "tipo": tipo, "pedido": pedido[:4000], "projeto": projeto, "contexto": str(contexto or "")[:6000],
           "origem": origem, "status": "fila", "criado": _agora(), "passos": [], "resposta": "", "status_ia": None,
           "detalhe": None, "sessao": None, "cwd": PROJETOS[projeto][1]}
    if auto_aplicar and tipo == "propor":
        job["auto_aplicar"] = True
    if modelo:
        job["modelo_fixo"] = str(modelo)
    if voltas:  # 24/10: o Gemini estourava as 15 voltas da pergunta em todas as leituras das melhorias
        job["voltas_max"] = int(voltas)
    if pensar:
        job["pensar"] = True
    if rota:  # 24/10 (Opus 5.5): "vscode" = endereço/chave do VS Code (settings_5), lidos na hora; nunca no job
        job["rota"] = str(rota)
    if esforco:  # 24/10: --effort do Claude Code (low|medium|high|xhigh|max)
        job["esforco"] = str(esforco)
    _gravar(job)
    garantir_fila()
    return job


def aplicar(jid):
    pai = ler(jid)
    if not pai or pai.get("tipo") != "propor" or pai.get("status_ia") != "PROPOSTA" or not pai.get("sessao"):
        raise ValueError("só dá pra aplicar uma proposta pronta")
    if pai.get("aplicado_em"):
        raise ValueError(f"já foi aplicado (pedido {pai['aplicado_em']})")
    nid = f"{datetime.now():%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"
    job = {"id": nid, "tipo": "aplicar", "pedido": pai["pedido"], "projeto": pai["projeto"], "contexto": "",
           "origem": "painel", "status": "fila", "criado": _agora(), "passos": [], "resposta": "", "status_ia": None,
           "detalhe": None, "sessao": pai["sessao"], "cwd": pai["cwd"], "pai": jid}
    for k in ("pensar", "modelo_fixo", "voltas_max", "rota", "esforco"):  # 24/10: herda modelo/rota/raciocínio da proposta
        if pai.get(k):
            job[k] = pai[k]
    _gravar(job)
    pai["aplicado_em"] = nid
    _gravar(pai)
    garantir_fila()
    return job


def parar(jid):
    job = ler(jid)
    if not job:
        raise ValueError("pedido não existe")
    if job["status"] == "fila":
        job.update(status="parado", fim=_agora(), detalhe="cancelado pelo dono antes de começar")
        _gravar(job)
        return job
    if job["status"] != "rodando":
        raise ValueError("esse pedido não está rodando")
    _arq(jid, ".parar").write_text("1")  # sinal em arquivo próprio: o rodador regrava o .json a cada passo
    if job.get("pid"):
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(job["pid"])], capture_output=True, timeout=30,
                       creationflags=SEM_JANELA)
    return ler(jid)


def _sha(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return None


def mudancas(jid):
    """[{arquivo, existia, diff}] do que o pedido 'aplicar' mudou (backup x arquivo atual)."""
    job = ler(jid)
    if not job:
        raise ValueError("pedido não existe")
    out = []
    for orig, info in (job.get("manifesto") or {}).items():
        antes = Path(info["backup"]).read_text(encoding="utf-8", errors="replace") if info.get("existia") else ""
        try:
            depois = Path(orig).read_text(encoding="utf-8", errors="replace")
        except OSError:
            depois = ""
        diff = "".join(difflib.unified_diff(antes.splitlines(True), depois.splitlines(True),
                                            "antes/" + Path(orig).name, "agora/" + Path(orig).name, n=3))
        out.append({"arquivo": orig, "existia": info.get("existia"), "diff": diff[:60000] or "(sem diferença)",
                    "mudou_depois": bool(info.get("depois_sha") and _sha(orig) != info["depois_sha"])})
    return out


def _quem_txt(quem):
    quem = str(quem or "painel")
    return {"painel": "pelo dono no painel", "dona": "pela dona", "dono": "pelo dono"}.get(quem, f"por {quem}")


def desfazer(jid, forcar=False, quem="painel"):
    """Volta os arquivos do conserto. 24/10: antes de voltar, copia a versão ATUAL de cada arquivo pra <id>_depois\\
    (dá pra refazer se o desfazer foi errado); arquivo que o conserto CRIOU vai pra <id>_criados\\ (mover, regra
    "nunca apagar"); grava quem desfez (job["desfeito_por"])."""
    job = ler(jid)
    if not job or job.get("tipo") != "aplicar":
        raise ValueError("só dá pra desfazer um conserto aplicado")
    if job.get("desfeito_em"):
        raise ValueError("já foi desfeito")
    man = job.get("manifesto") or {}
    if not man:
        raise ValueError("esse conserto não mudou nenhum arquivo")
    mexidos = [o for o, i in man.items() if i.get("depois_sha") and _sha(o) != i["depois_sha"]]
    if mexidos and not forcar:
        raise ValueError("arquivo mudou depois do conserto: " + ", ".join(Path(m).name for m in mexidos)
                         + " — confirme pra desfazer mesmo assim")
    pasta_depois, pasta_criados = PASTA / f"{jid}_depois", PASTA / f"{jid}_criados"
    depois = {}
    for n, orig in enumerate(man, 1):  # primeiro a cópia do "depois" de todos; só então mexe em algum
        if Path(orig).is_file():
            pasta_depois.mkdir(parents=True, exist_ok=True)
            dest = pasta_depois / f"{n:02d}_{Path(orig).name}"
            shutil.copy2(orig, dest)
            depois[orig] = str(dest)
    feitos = []
    for n, (orig, info) in enumerate(man.items(), 1):
        if info.get("existia"):
            shutil.copy2(info["backup"], orig)
            feitos.append(f"voltou {orig}")
        elif Path(orig).exists():
            pasta_criados.mkdir(parents=True, exist_ok=True)
            dest = pasta_criados / f"{n:02d}_{Path(orig).name}"
            shutil.move(orig, str(dest))
            feitos.append(f"tirou {orig} (criado pelo conserto) -> {dest}")
    job.update(desfeito_em=_agora(), desfeito=feitos, desfeito_por=str(quem or "painel"))
    if depois:
        job["depois"] = depois
    _gravar(job)
    try:
        with open(BASE / "VIGIA_DIARIO.md", "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now():%Y%m%d_%H%M} — conserto {jid} DESFEITO {_quem_txt(quem)}\n"
                    + "".join(f"- {x}\n" for x in feitos)
                    + (f"- versão de antes do desfazer guardada em {pasta_depois} (pra refazer)\n" if depois else ""))
    except OSError:
        pass
    _documentar(job)
    return job


# ─── conversa e documento de cada pedido (frente E, dono 21/10: "1 clique abre a janela com a conversa da resolução;
#     tudo documentado do que fez, pra outra IA continuar") ──────────────────────
DOCS = BASE / "consertos_ia"


def conversa(jid, limite=500):
    """A conversa do agente (stream-json em <id>.jsonl) em mensagens legíveis: texto da IA, ferramenta usada e o que
    ela devolveu (resumido)."""
    out = []
    try:
        linhas = _arq(jid, ".jsonl").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for linha in linhas:
        try:
            ev = json.loads(linha)
        except ValueError:
            continue
        tipo = ev.get("type")
        for c in ((ev.get("message") or {}).get("content") or []) if tipo in ("assistant", "user") else []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text" and tipo == "assistant" and c.get("text", "").strip():
                out.append({"quem": "ia", "texto": c["text"].strip()[:6000]})
            elif c.get("type") == "tool_use":
                ent = c.get("input") or {}
                det = ent.get("command") or ent.get("file_path") or ent.get("pattern") or ent.get("url") or ""
                extra = ""
                if c.get("name") in EDICAO:
                    extra = str(ent.get("new_string") or ent.get("content") or "")[:1500]
                out.append({"quem": "ferramenta", "texto": f"{_resumo_passo(c.get('name'), ent)}",
                            "detalhe": (str(det)[:1500] + ("\n" + extra if extra else ""))})
            elif c.get("type") == "tool_result":
                cont = c.get("content")
                if isinstance(cont, list):
                    cont = "\n".join(x.get("text", "") for x in cont if isinstance(x, dict))
                out.append({"quem": "resultado", "texto": str(cont or "")[:1500], "erro": bool(c.get("is_error"))})
        if tipo == "result":
            out.append({"quem": "fim", "texto": f"fim: {ev.get('subtype') or ''} · {ev.get('num_turns') or '?'} voltas"
                                                  + (" · ERRO" if ev.get("is_error") else "")})
    return out[-limite:]


def conversa_vigia(vigia, hora):
    """Bloco do diário + a saída do agente do vigia daquela hora (logs\\vigia_agente_<hora>.log)."""
    if not re.fullmatch(r"\d{8}_\d{4}", str(hora or "")):
        raise ValueError("hora inválida")
    pares = {"vigia geral": (BASE / "VIGIA_DIARIO.md", BASE / "logs"),
             "vigia hipercool": (Path(r"D:\hipercool-videos\docs\VIGIA_DIARIO.md"), Path(r"D:\hipercool-videos\logs"))}
    if vigia not in pares:
        raise ValueError("vigia desconhecido")
    diario, logs = pares[vigia]
    bloco = ""
    try:
        for b in re.split(r"\n(?=## )", diario.read_text(encoding="utf-8", errors="replace")):
            if b.strip().startswith(f"## {hora}"):
                bloco = b.strip()
    except OSError:
        pass
    log, aviso = logs / f"vigia_agente_{hora}.log", None
    if bloco and not log.exists():  # o agente às vezes escreve a hora do diário em UTC (+3 h): o log mais perto antes
        alvo, melhor = datetime.strptime(hora, "%Y%m%d_%H%M"), None
        for cand in logs.glob("vigia_agente_*_*.log"):
            try:
                t = datetime.strptime(cand.stem[len("vigia_agente_"):], "%Y%m%d_%H%M")
            except ValueError:
                continue
            for desvio_h in (0, 3):
                d = (alvo - t).total_seconds() / 60 - desvio_h * 60
                if 0 <= d <= 15 and (melhor is None or d < melhor[0]):
                    melhor = (d, cand)
        if melhor:
            log, aviso = melhor[1], f"a hora do diário não bate com nenhum log: este é o mais próximo ({melhor[1].name})"
    try:
        texto = log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        texto = ""
    return {"vigia": vigia, "hora": hora, "bloco": bloco[:12000], "log": str(log) if texto else None,
            "aviso": aviso if texto else None, "conversa": texto[-40000:]}


def _documentar(job):
    """consertos_ia\\<id>.md (pedido, contexto, resposta, passos, arquivos mudados, como desfazer) + 1 linha no
    consertos_ia\\INDICE.md. Gerado pelo código (não depende da IA lembrar). Nunca derruba o rodador."""
    try:
        DOCS.mkdir(parents=True, exist_ok=True)
        jid, nome = job["id"], {"pergunta": "Pergunta", "propor": "Conserto: proposta", "aplicar": "Conserto: aplicação"}
        st = job.get("status_ia") or job.get("status")
        partes = [f"# {nome.get(job['tipo'], job['tipo'])} {jid} — {' '.join(job['pedido'].split())[:150]}", "",
                  f"- Projeto: {job.get('projeto')} ({job.get('cwd')}) · origem: {job.get('origem')}"
                  + (" · corrigir todos (aplica sozinho)" if job.get("auto_aplicar") else ""),
                  f"- Pedido em {job.get('criado')} · início {job.get('inicio') or '-'} · fim {job.get('fim') or '-'}"
                  + (f" · {job['voltas']} voltas" if job.get("voltas") else ""),
                  f"- Situação: {job.get('status')} / {st}" + (f" — {job['detalhe']}" if job.get("detalhe") else "")]
        if job.get("pai"):
            partes.append(f"- Proposta que originou: [{job['pai']}]({job['pai']}.md)")
        if job.get("aplicado_em"):
            partes.append(f"- Aplicação: [{job['aplicado_em']}]({job['aplicado_em']}.md)")
        if job.get("desfeito_em"):
            partes.append(f"- DESFEITO {_quem_txt(job.get('desfeito_por'))} em {job['desfeito_em']}: "
                          + "; ".join(job.get("desfeito") or []))
            if job.get("depois"):
                partes.append(f"- Versão de antes do desfazer (pra refazer): {PASTA / (jid + '_depois')}")
        partes += ["", "## Pedido", "", job["pedido"]]
        if job.get("contexto"):
            partes += ["", "## Contexto (da tela do painel)", "", job["contexto"]]
        partes += ["", "## Resposta da IA", "", job.get("resposta") or "(sem resposta)"]
        if job.get("bloqueios") or job.get("suspeitos"):
            partes += ["", "## Guarda das melhorias (comandos barrados ou suspeitos)", ""]
            partes += [f"- BLOQUEADO {b.get('t', '')} {b.get('ferramenta', '')}: {b.get('comando', '')} — {b.get('motivo', '')}"
                       for b in job.get("bloqueios") or []]
            partes += [f"- suspeito {b.get('t', '')} {b.get('ferramenta', '')}: {b.get('comando', '')} — {b.get('motivo', '')}"
                       for b in job.get("suspeitos") or []]
        if job.get("manifesto"):
            partes += ["", "## Arquivos mudados (backup feito antes de cada um)", ""]
            for orig, info in job["manifesto"].items():
                partes.append(f"- {orig}" + (f" — backup: {info['backup']}" if info.get("backup") else " — arquivo novo"))
            partes += ["", "Como desfazer: botão Desfazer no painel (aba IA, pedido " + jid + ") ou copiar cada backup de volta."]
            try:
                for m in mudancas(jid):
                    partes += ["", f"### diff {Path(m['arquivo']).name}", "", "```diff", m["diff"][:8000], "```"]
            except Exception:  # noqa: BLE001
                pass
        if job.get("passos"):
            partes += ["", "## Passo a passo (ferramentas usadas)", ""] + [f"- {p['t']} {p['o']}" for p in job["passos"]]
        partes += ["", "## Conversa completa", "",
                   f"D:\\video-fila\\estado\\painel_ia\\{jid}.jsonl (stream-json do Claude Code)"
                   + (f"; sessão {job['sessao']} (dá pra continuar com --resume)" if job.get("sessao") else "")]
        (DOCS / f"{jid}.md").write_text("\n".join(partes) + "\n", encoding="utf-8")
        indice = DOCS / "INDICE.md"
        if not indice.exists():
            indice.write_text("# Consertos e perguntas da IA do painel (1 linha por pedido; o mais novo embaixo)\n\n",
                              encoding="utf-8")
        with open(indice, "a", encoding="utf-8") as f:
            f.write(f"- {(job.get('fim') or job.get('criado') or '')[:16].replace('T', ' ')} | {job['tipo']} | {st}"
                    + (" | DESFEITO" if job.get("desfeito_em") else "")
                    + f" | {' '.join(job['pedido'].split())[:120]} → [{jid}.md]({jid}.md)\n")
    except Exception:  # noqa: BLE001
        pass


def documento(jid):
    try:
        return (DOCS / f"{_arq(jid).stem}.md").read_text(encoding="utf-8")
    except OSError:
        return None


# ─── histórico dos vigias (o que a IA já fez sozinha) ─────────────────────────
def historico_vigias(limite=80):
    out = []
    for nome, arq in (("vigia geral", BASE / "VIGIA_DIARIO.md"),
                      ("vigia hipercool", Path(r"D:\hipercool-videos\docs\VIGIA_DIARIO.md"))):
        try:
            texto = arq.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for bloco in re.split(r"\n(?=## )", texto):
            m = re.match(r"## (\S+)\s+[—-]\s+(.+)", bloco.strip())
            if not m:
                continue
            est = re.search(r"Estado\**:?\**\s*(.+)", bloco)
            desf = re.search(r"Como desfazer\**:?\**\s*(.+)", bloco)
            q = m.group(1)
            quando = (f"{q[:4]}-{q[4:6]}-{q[6:8]} {q[9:11]}:{q[11:13]}" if re.fullmatch(r"\d{8}_\d{4}", q) else q)
            out.append({"quando": quando, "vigia": nome, "titulo": m.group(2)[:200],
                        "estado": (est.group(1).strip()[:80] if est else ""),
                        "como_desfazer": (desf.group(1).strip()[:300] if desf else ""), "texto": bloco[:3000],
                        "hora": q if re.fullmatch(r"\d{8}_\d{4}", q) else None})
    out.sort(key=lambda x: x["quando"], reverse=True)
    return out[:limite]


# ─── fila ─────────────────────────────────────────────────────────────────────
def _fila_viva():
    try:
        pid = int(TRAVA_FILA.read_text().strip())
    except (OSError, ValueError):
        return False
    return _vivo(pid)


def garantir_fila():
    """Dispara o rodador da fila (processo separado: o pedido continua mesmo se o painel reiniciar)."""
    if _fila_viva():
        return
    py = Path(sys.executable)
    pyw = py.with_name("pythonw.exe") if py.with_name("pythonw.exe").exists() else py
    for flags in (SEM_JANELA | 0x01000000 | 0x00000008, SEM_JANELA | 0x00000008, SEM_JANELA):
        try:
            subprocess.Popen([str(pyw), str(Path(__file__)), "fila"], cwd=str(BASE), creationflags=flags,
                             close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return
        except OSError:
            continue


def rodar_fila():
    PASTA.mkdir(parents=True, exist_ok=True)
    if _fila_viva():
        return
    TRAVA_FILA.write_text(str(os.getpid()))
    try:
        while True:
            # aplicação primeiro: o conserto aprovado (ou do "corrigir todos") sai logo depois da sua proposta
            pend = sorted((j for j in todos() if j.get("status") == "fila"),
                          key=lambda j: (j.get("tipo") != "aplicar", j["criado"]))
            if not pend:
                return
            _rodar(pend[0])
    finally:
        TRAVA_FILA.unlink(missing_ok=True)


def _travas_ocupadas():
    return [str(t) for t in TRAVAS_VIGIAS if t.exists() and time.time() - t.stat().st_mtime < TRAVA_VIGIA_MIN * 60]


def _resumo_passo(nome, ent):
    ent = ent or {}
    alvo = (ent.get("file_path") or ent.get("notebook_path") or ent.get("command") or ent.get("pattern")
            or ent.get("url") or ent.get("description") or ent.get("prompt") or "")
    verbo = {"Read": "lendo", "Edit": "editando", "Write": "escrevendo", "MultiEdit": "editando", "Bash": "rodando",
             "Grep": "procurando", "Glob": "listando", "PowerShell": "rodando", "WebFetch": "abrindo",
             "TodoWrite": "anotando tarefas"}.get(nome, nome)
    return f"{verbo} {str(alvo)[:180]}".strip()


# ─── montagem do pedido ao agente (24/10: fatorado pra dar pra testar) ─────────
def _linha_agora(agora=None):
    """A hora de agora em Brasília e em UTC (24/10: o agente lia linha de log com 'Z' como se fosse hora de Brasília)."""
    utc = (agora or datetime.now(timezone.utc)).astimezone(timezone.utc)
    br = utc - timedelta(hours=3)  # Brasília sem horário de verão desde 2019
    return (f"AGORA: {br:%d/%m/%Y %H:%M} em Brasília (UTC-3) = {utc:%H:%M} UTC. Linha de log com 'Z' ou UTC está "
            "3 h na frente de Brasília; linha sem data não prova nada de hoje.")


def _montar_prompt(job, modelo, ctx="", agora=None):
    """Marcas de raciocínio (se pensar + Kiro + pergunta/propor) + linha AGORA + o prompt do tipo."""
    tipo = job["tipo"]
    nome_proj, pasta = PROJETOS.get(job.get("projeto"), PROJETOS["geral"])
    if tipo == "pergunta":
        corpo = PROMPT_PERGUNTA.format(pedido=job["pedido"], contexto=ctx, regras=REGRAS)
    elif tipo == "propor":
        corpo = PROMPT_PROPOR.format(pedido=job["pedido"], contexto=ctx, regras=REGRAS, projeto=nome_proj, pasta=pasta)
    else:
        corpo = PROMPT_APLICAR.format(hora=datetime.now().strftime("%Y%m%d_%H%M"), id=job["id"], regras=REGRAS)
        try:
            import ia_reserva
            if ia_reserva.eh_reserva(modelo):
                corpo += ia_reserva.AVISO_RESERVA
        except ImportError:
            pass
    # o aplicar retoma a sessão do propor (--resume), que já tem as marcas
    marcas = (MARCAS_PENSAR if job.get("pensar") and str(modelo or "").startswith("kr/claude-sonnet")
              and tipo in ("pergunta", "propor") else "")
    return marcas + _linha_agora(agora) + "\n" + corpo


def _hooks(job):
    """--settings dos hooks PreToolUse: backup antes de editar (aplicar) + guarda de comandos (origem melhoria, 24/10;
    mesmo JSON, duas entradas). None = sem hook."""
    entradas = []
    if job["tipo"] == "aplicar":
        entradas.append({"matcher": "|".join(EDICAO),
                         "hooks": [{"type": "command", "command": f'"{PY_HOOK}" "{Path(__file__)}" backup'}]})
    if _eh_melhoria(job):
        entradas.append({"matcher": GUARDA_MATCHER,  # timeout explícito (achado 21); sempre com bloquear_aplicar (18)
                         "hooks": [{"type": "command", "timeout": 90,
                                    "command": f'"{PY_HOOK}" "{Path(__file__)}" guarda aplicar'}]})
    return {"hooks": {"PreToolUse": entradas}} if entradas else None


def _matar_arvore(pid):
    """taskkill /T /F só no PID do claude.exe deste pedido (e o que ele abriu)."""
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, timeout=60, creationflags=SEM_JANELA)


class _Vigia(threading.Thread):
    """24/10: vigia por thread do pedido rodando. Antes o teto de tempo só era conferido quando chegava linha nova: um
    claude.exe mudo (gateway pendurado) ficava preso pra sempre e segurava a fila. A cada `intervalo` s confere o teto
    e o silêncio; mata só o PID do processo deste pedido; para sozinho quando o processo termina."""

    def __init__(self, proc, limite_min, sem_linha_min=SEM_LINHA_MIN, intervalo=VIGIA_INTERVALO_S, matar=None):
        super().__init__(daemon=True)
        self.proc, self.limite_min, self.sem_linha_min, self.intervalo = proc, limite_min, sem_linha_min, intervalo
        self.inicio = self.ultima = time.time()
        self.motivo = None
        self._matar = matar or _matar_arvore
        self._fim = threading.Event()

    def linha(self):
        self.ultima = time.time()

    def parar(self):
        self._fim.set()

    def run(self):
        while not self._fim.wait(self.intervalo):
            if self.proc.poll() is not None:
                return
            agora = time.time()
            if agora - self.inicio > self.limite_min * 60:
                self.motivo = f"passou de {self.limite_min:g} min e foi interrompido"
            elif agora - self.ultima > self.sem_linha_min * 60:
                self.motivo = f"travou: {int((agora - self.ultima) // 60)} min sem resposta"
            else:
                continue
            try:
                self._matar(self.proc.pid)
            except Exception:  # noqa: BLE001
                pass
            return


def _executar(cmd, cwd, env, job, limite_min, ao_linha, sem_linha_min=SEM_LINHA_MIN, intervalo=VIGIA_INTERVALO_S):
    """Roda o agente com o _Vigia de olho; entrega cada linha (não vazia) do stdout a ao_linha(linha).
    Se o vigia matou, grava job["detalhe"] com o motivo. -> motivo do vigia ou None."""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, creationflags=SEM_JANELA)
    job["pid"] = proc.pid
    _gravar(job)
    vigia = _Vigia(proc, limite_min, sem_linha_min, intervalo)
    vigia.start()
    erros = 0
    try:
        for bruto in proc.stdout:
            vigia.linha()
            linha = bruto.decode("utf-8", "replace").strip()
            if linha:
                try:
                    ao_linha(linha)
                except Exception:  # noqa: BLE001 — falha ao gravar 1 linha não pode largar o agente sem leitor
                    erros += 1
        proc.wait(timeout=60)
    finally:
        vigia.parar()
    if erros:
        job["erros_leitura"] = erros
    if vigia.motivo:
        job["detalhe"] = vigia.motivo
        _gravar(job)
    return vigia.motivo


def _rodar(job):
    jid, tipo = job["id"], job["tipo"]
    if tipo == "aplicar":  # nunca dois agentes mexendo juntos: espera o vigia que estiver consertando
        inicio_espera = time.time()
        while _travas_ocupadas() and time.time() - inicio_espera < 45 * 60:
            job.update(status="fila", detalhe="esperando o vigia terminar o conserto dele")
            _gravar(job)
            time.sleep(20)
            job = ler(jid) or job
            if job.get("status") == "parado":
                return
    cfg = json.loads(PROXY.read_text(encoding="utf-8"))
    import ia_reserva  # 22/10: Kiro sem crédito (zera antes do dia 1) -> reserva grátis do gateway
    # 26/10 (dono: "Gemini pra coisas menores, Kiro apenas para as correções"): propor/aplicar = conserto -> pode Kiro;
    # pergunta -> Gemini. Melhoria contínua (parada) nunca leva Kiro.
    conserto = tipo in ("propor", "aplicar") and not _eh_melhoria(job)
    modelo = ia_reserva.modelos(cfg["modelo"], conserto=conserto)[0]
    fixo = job.get("modelo_fixo")
    if (fixo and fixo not in (job.get("modelos_recusados") or []) and not ia_reserva._fora(ia_reserva._ler(), fixo)
            and not (ia_reserva.eh_kiro(fixo) and ia_reserva.modelos(fixo, conserto=conserto)[0] != fixo)):
        modelo = fixo  # 24/10: melhorias em dupla (o 2º modelo busca/vota/revisa); fora do ar = ordem normal
    job["modelo"] = modelo
    base_url, token = cfg["base_url"], cfg["auth_token"]
    if job.get("rota") == "vscode":  # 24/10 (Opus 5.5): a rota do VS Code (porta 20133) com a chave dela, lida agora
        try:
            vs = json.loads(ROTA_VSCODE.read_text(encoding="utf-8"))
            ev = {x["name"]: x["value"] for x in vs["claudeCode.environmentVariables"]}
            base_url, token = ev["ANTHROPIC_BASE_URL"], ev["ANTHROPIC_AUTH_TOKEN"]
        except (OSError, ValueError, KeyError, TypeError):
            pass  # sem o arquivo: vai pela rota padrão (o modelo pode não existir lá e o pedido falha visível)
    env = dict(os.environ, ANTHROPIC_BASE_URL=base_url, ANTHROPIC_AUTH_TOKEN=token, PYTHONUTF8="1",
               PATH=r"D:\hipercool-materiais\bin" + os.pathsep + os.environ.get("PATH", ""), PAINEL_IA_JOB=jid)
    env.pop("ANTHROPIC_API_KEY", None)
    ctx = f"\nCONTEXTO (da tela do painel):\n{job['contexto']}\n" if job.get("contexto") else ""
    if tipo in ("pergunta", "propor"):  # frente E: o que a base já sabe de casos parecidos (o vigia/IA aprende)
        try:
            import base_consertos
            parecidos = base_consertos.bloco_prompt(f"{job['pedido']} {job.get('contexto') or ''}")
            if parecidos:
                ctx += f"\n{parecidos}\n"
                job["base_usada"] = parecidos[:3000]
        except Exception:  # noqa: BLE001
            pass
    prompt = _montar_prompt(job, modelo, ctx)
    # sem as configurações de usuário: os hooks do Claude interativo do dono (portão de qualidade que exige
    # planejador/revisor) travavam o conserto e faziam o agente abrir subagentes (teste 21/10)
    cmd = [str(CLAUDE), "-p", prompt, "--model", modelo, "--output-format", "stream-json", "--verbose",
           "--max-turns", str(job.get("voltas_max") or VOLTAS[tipo]), "--dangerously-skip-permissions", "--setting-sources", "project,local"]
    if job.get("esforco"):
        cmd += ["--effort", job["esforco"]]
    hooks = _hooks(job)
    if hooks:
        cmd += ["--settings", json.dumps(hooks)]
    if tipo in ("pergunta", "propor"):
        cmd += ["--disallowedTools", *EDICAO]
    else:
        cmd += ["--resume", job["sessao"]]
    travas = []
    if tipo == "aplicar":
        for t in TRAVAS_VIGIAS:
            try:
                t.write_text(f"painel {jid}")
                travas.append(t)
            except OSError:
                pass
    job.update(status="rodando", inicio=_agora(), detalhe=None)
    _gravar(job)
    stream = _arq(jid, ".jsonl")
    texto, final, ferramentas = [], None, 0
    travou = None

    def ao_linha(linha):
        nonlocal final, ferramentas
        fs.write(linha + "\n")
        fs.flush()
        try:
            ev = json.loads(linha)
        except ValueError:
            if not linha.startswith("[claude-code"):  # aviso interno do Claude Code, não é passo
                job["passos"].append({"t": _agora()[11:], "o": linha[:200]})
            return
        if ev.get("session_id") and tipo != "aplicar":
            job["sessao"] = ev["session_id"]
        if ev.get("type") == "assistant":
            for c in (ev.get("message") or {}).get("content") or []:
                if c.get("type") == "text" and c.get("text", "").strip():
                    texto.append(c["text"])
                elif c.get("type") == "tool_use":
                    ferramentas += 1
                    job["passos"].append({"t": _agora()[11:], "o": _resumo_passo(c.get("name"), c.get("input"))})
        elif ev.get("type") == "result":
            final = ev
        job["passos"] = job["passos"][-300:]
        job["resposta"] = "\n\n".join(texto)[-20000:]
        atual = ler(jid) or {}
        job["manifesto"] = atual.get("manifesto") or job.get("manifesto") or {}  # o hook grava no mesmo arquivo
        _juntar_guarda(job)
        _gravar(job)

    try:
        with open(stream, "a", encoding="utf-8") as fs:
            travou = _executar(cmd, job["cwd"], env, job, float(job.get("tempo_max_min") or TEMPO_MAX_MIN[tipo]),
                               ao_linha)
    except Exception as e:  # noqa: BLE001
        job["detalhe"] = f"erro ao rodar o agente: {type(e).__name__}: {e}"
    finally:
        for t in travas:
            t.unlink(missing_ok=True)
    atual = ler(jid) or {}
    job["manifesto"] = atual.get("manifesto") or job.get("manifesto") or {}
    _juntar_guarda(job)
    for orig, info in (job.get("manifesto") or {}).items():
        info["depois_sha"] = _sha(orig)
    resultado = (final or {}).get("result") or "\n\n".join(texto)
    recusados = job.get("modelos_recusados") or []
    if (not travou and ia_reserva.falhou_sem_trabalhar(resultado, ferramentas)
            and len(recusados) < len(ia_reserva.RESERVAS)
            and not _arq(jid, ".parar").exists()):  # gateway recusou antes de qualquer passo: repete com a reserva
        ia_reserva.marcar(modelo)
        job["modelos_recusados"] = recusados + [modelo]
        job["passos"].append({"t": _agora()[11:], "o": f"modelo {modelo} recusado pelo gateway "
                              f"({' '.join(resultado.split())[:120]}): repetindo com a reserva"})
        job.update(resposta=None, detalhe=None)
        _gravar(job)
        return _rodar(job)
    job["resposta"] = resultado[-20000:]
    m = re.findall(r"STATUS:?\**\s*\**\s*(OK|CONSERTEI|REVISAR|PROPOSTA|CONCLU[IÍ]DO)\**\s*[-—:]?\s*(.*)", resultado, re.I)
    if m:
        st = m[-1][0].upper()
        if st.startswith("CONCLU"):  # o modelo às vezes escreve "CONCLUÍDO" no lugar
            st = "CONSERTEI" if tipo == "aplicar" else "OK"
        job["status_ia"], det = st, m[-1][1].strip()
        job["detalhe"] = job.get("detalhe") or det[:300]
    elif tipo == "pergunta" and resultado.strip():
        job["status_ia"] = "OK"
    if final:
        job["voltas"] = final.get("num_turns")
        job["custo_usd"] = final.get("total_cost_usd")
        if final.get("is_error") and not job.get("detalhe"):
            job["detalhe"] = str(final.get("subtype") or "erro do agente")
    parado = _arq(jid, ".parar").exists()
    job["status"] = "parado" if parado else ("terminou" if (final and not final.get("is_error")) else "erro")
    job["fim"] = _agora()
    job.pop("pid", None)
    _gravar(job)
    if (tipo == "propor" and job.get("auto_aplicar") and job["status"] == "terminou"
            and job.get("status_ia") == "PROPOSTA"):  # "corrigir todos": aplica sem esperar o clique
        try:
            aplicar(jid)
            job = ler(jid) or job
        except Exception as e:  # noqa: BLE001
            job["detalhe"] = f"(corrigir todos) não aplicou: {e}"[:300]
            _gravar(job)
    _documentar(job)
    if not job.get("aplicado_em") or not job.get("auto_aplicar"):  # aplicação automática: avisa só o resultado dela
        _avisar(job)


def _avisar(job):
    """Resultado de conserto vai pro bot do vigia (pergunta só aparece no painel)."""
    if job["tipo"] == "pergunta" or job["status"] == "parado":
        return
    if job.get("origem") == "melhoria" or (ler(job.get("pai") or "") or {}).get("origem") == "melhoria":
        return  # 23/10: melhorias contínuas avisam pelo bots_conversa (com APLICAR/DESFAZER), não aqui
    try:
        sys.path.insert(0, str(BASE))
        import avisos
        rot = {"propor": "IA propôs um conserto (abra o painel pra aplicar)", "aplicar": "IA aplicou o conserto"}[job["tipo"]]
        avisos.enviar(f"🤖 {rot}\n{job['pedido'][:200]}\n→ {job.get('status_ia') or job['status']}: "
                      f"{(job.get('detalhe') or '')[:300]}\nPainel: aba IA, pedido {job['id']}",
                      origem="painel ia", importante=job.get("status_ia") in ("REVISAR", None))
    except Exception:  # noqa: BLE001
        pass


# ─── hook de backup (PreToolUse) ──────────────────────────────────────────────
def hook_backup():
    """Copia o arquivo antes da 1ª edição do conserto. Nunca bloqueia o agente (sai 0 sempre)."""
    try:
        jid = os.environ.get("PAINEL_IA_JOB", "")
        dados = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        ent = dados.get("tool_input") or {}
        alvo = ent.get("file_path") or ent.get("notebook_path")
        if not jid or not alvo:
            return
        alvo = str(Path(alvo).resolve())
        for _ in range(20):  # o rodador também grava o job: tenta de novo se pegar no meio da troca
            job = ler(jid)
            if job:
                break
            time.sleep(0.2)
        if not job:
            return
        if _eh_melhoria(job):  # 24/10 (achado 22): Write que a guarda vai barrar não copia nem entra no manifesto
            try:
                if guarda_decidir(dados.get("tool_name") or "Write", ent, aplicar=True)["bloquear"]:
                    return
            except Exception:  # noqa: BLE001
                return
        man = job.get("manifesto") or {}  # o rodador pode ter gravado null aqui
        job["manifesto"] = man
        if alvo in man:
            return
        pasta = PASTA / f"{jid}_backup"
        pasta.mkdir(parents=True, exist_ok=True)
        info = {"existia": Path(alvo).exists()}
        if info["existia"]:
            dest = pasta / f"{len(man) + 1:02d}_{Path(alvo).name}"
            shutil.copy2(alvo, dest)
            info["backup"] = str(dest)
        man[alvo] = info
        _gravar(job)
    except Exception:  # noqa: BLE001
        pass


# ─── guarda das melhorias (hook PreToolUse; 24/10, Fase 0) ─────────────────────
# Dona 24/10: as melhorias automáticas rodaram pip, rodaram a rede de postagem à mão, pararam tarefa agendada,
# recortaram/moveram ~290 fotos do Veo e copiaram cookies. O "Desfazer" não volta nada disso: tem de ser barrado ANTES.
# Regras em config\melhoria_guarda.json: listas de regex (sem diferenciar maiúscula). Comentários (?#...) no começo da
# regex: o 1º texto livre é o motivo; (?#exec) = só vale quando o trecho EXECUTA algo (não quando só lê/mostra: cat,
# grep, ls, echo, Get-Content...); (?#fora_aspas) = testa sem o que está entre aspas; (?#grep) = testa o padrão da
# ferramenta Grep. "permitir" apaga o trecho que casou antes das outras listas (vence o bloqueio naquele trecho).
_LEITORES = {
    "cat", "head", "tail", "less", "more", "grep", "egrep", "fgrep", "rg", "ls", "dir", "ll", "wc", "file", "stat",
    "du", "df", "find", "type", "tree", "sort", "uniq", "cut", "awk", "sed", "tr", "jq", "diff", "cmp", "md5sum",
    "sha256sum", "sha1sum", "strings", "od", "xxd", "hexdump", "basename", "dirname", "realpath", "readlink", "which",
    "where", "whereis", "test", "[", "[[", "cd", "pushd", "popd", "pwd", "date", "git", "tasklist", "ps", "pgrep",
    "nproc", "free", "uptime", "hostname", "whoami", "column", "nl", "fold", "iconv", "base64", "true", "false",
    "sleep", "get-content", "gc", "select-string", "sls", "findstr", "get-childitem", "gci", "get-item", "gi",
    "get-itemproperty", "gp", "test-path", "resolve-path", "split-path", "join-path", "measure-object", "measure",
    "select-object", "select", "where-object", "sort-object", "format-table", "ft", "format-list", "fl", "out-string",
    "get-date", "get-filehash", "get-command", "gcm", "get-process", "gps", "convertfrom-json", "convertto-json",
    "get-member", "gm", "set-location", "sl", "push-location", "pop-location", "get-location", "start-sleep",
    "group-object", "get-counter", "get-ciminstance", "get-wmiobject", "get-psdrive", "get-volume", "out-host",
}
_INERTES = {"echo", "printf", "write-host", "write-output", "write-verbose", "write-warning", "write-information"}
_PREFIXOS = {"then", "do", "else", "elif", "if", "while", "until", "time", "sudo", "nohup", "exec", "!", "{", "(",
             "command", "builtin", "env"}
_INTERP = re.compile(r"(?:python[w0-9.]*|py|pyw|node|bash|sh|zsh|powershell|pwsh|cmd|perl|ruby|php|sqlite3|psql|wsl|"
                     r"iex|invoke-expression|start-process|saps)", re.I)
# 24/10 (achado 11): o que vem depois destes é OUTRO comando de terminal (powershell -Command "...", bash -c '...',
# cmd /c ..., iex "..."): é quebrado e conferido de novo como comando, senão o que está entre aspas escapava das regras
_SHELLS = re.compile(r"(?:bash|sh|zsh|powershell|pwsh|cmd|wsl|iex|invoke-expression|start-process|saps)", re.I)
_FLAGS_SHELL = re.compile(r"^(?:-(?:NoProfile|NonInteractive|NoLogo|nop|noni|Command|c|e|lc|ic|l|i|File|f|"
                          r"ExecutionPolicy|ep|WindowStyle|w|ArgumentList|FilePath|Wait|NoNewWindow|Verb)|"
                          r"/[cCkKsSqQ]|//[cCkK]|--?login|Bypass|Unrestricted|RemoteSigned|Hidden|RunAs)$", re.I)
# 24/10 (achado 17): Edit/Write nestes nomes é barrado (motor, guarda e sistema da dona: mudança à mão). Igual ao
# NUCLEO do melhoria_continua.py (o hook não importa o motor)
NUCLEO_GUARDA = {"melhoria_continua.py", "painel_ia.py", "bots_conversa.py", "vigia_geral.py", "ia_reserva.py",
                 "avisos.py", "notificar_telegram.py", "faxina.py", "telegram_bots.json", "telegram.json",
                 "claude_proxy.json", "camada_opus.py", "auditoria_final.py", "monitor_opus.py", "melhoria_guarda.json"}
_EXT_SCRIPT = re.compile(r"\.(?:py|pyw|ps1|psm1|bat|cmd|sh|js|mjs|vbs)$", re.I)
# o que ainda executa/expande dentro de aspas duplas (o resto da string some quando ela é só texto)
_SUBST = {"Bash": re.compile(r"\$\([^)]*\)|(?<!\\)`(?:[^`\\]|\\.)*`|\$\{[^}]*\}|\$\w+"),
          "PowerShell": re.compile(r"\$\([^)]*\)|\$\{[^}]*\}|\$(?:env:)?\w+")}
_LISTAS_GUARDA = ("segredos", "permitir", "bloquear", "bloquear_aplicar", "suspeito")


def _regras_guarda(caminho=None):
    try:
        return json.loads(Path(caminho or GUARDA_CFG).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _compilar_regra(texto, lista):
    opcoes, motivo, resto = set(), None, str(texto)
    while True:
        m = re.match(r"\(\?#([^)]*)\)", resto)
        if not m:
            break
        c = m.group(1).strip()
        if c in ("exec", "fora_aspas", "grep"):
            opcoes.add(c)
        elif c and not motivo:
            motivo = c
        resto = resto[m.end():]
    try:
        rx = re.compile(str(texto), re.I | re.M)
    except re.error:
        return None
    return {"re": rx, "motivo": motivo or f"regra da lista {lista} ({resto[:60]})", "opcoes": opcoes}


def _compilar_regras(regras):
    return {k: [r for r in (_compilar_regra(x, k) for x in (regras.get(k) or []) if isinstance(x, str)) if r]
            for k in _LISTAS_GUARDA}


def _nome_cmd(palavra):
    nome = re.split(r"[\\/]", str(palavra).strip().strip("\"'&").strip())[-1].lower()
    return nome[:-4] if nome.endswith(".exe") else nome


def _tirar_heredoc(cmd):
    """Tira o corpo de heredoc (bash) e here-string (PowerShell) que só é texto (ex.: o registro no VIGIA_DIARIO, falso
    positivo conhecido). Mantém quando o corpo vai pra um interpretador (python - <<EOF), que executa."""
    linhas, out, i = cmd.split("\n"), [], 0
    while i < len(linhas):
        ln = linhas[i]
        out.append(ln)
        m = re.search(r"(?<!<)<<(-?)\s*(['\"]?)([A-Za-z_][\w-]*)\2", ln)
        if m:
            cab = re.split(r"\|\||&&|[|;&(]", ln[:m.start()])[-1].split()
            interp = bool(cab) and bool(_INTERP.fullmatch(_nome_cmd(cab[0])))
            # 24/10 (achado 12): corpo gravado num arquivo (> >> tee) que não é o VIGIA_DIARIO pode ser um script que
            # roda depois: fica pra ser conferido
            if not interp and re.search(r"(?:(?<![>\w-])>>?|\btee\s+(?:-a\s+|--append\s+)?)\s*(?=[^\s;&|<>])"
                                        r"(?![^\s;&|]*VIGIA_DIARIO\.md)", ln[:m.start()] + " " + ln[m.end():]):
                interp = True
            fim, tira_tab, j = m.group(3), m.group(1) == "-", i + 1
            while j < len(linhas) and (linhas[j].lstrip("\t") if tira_tab else linhas[j]).strip() != fim:
                if interp:
                    out.append(linhas[j])
                j += 1
            if j < len(linhas):
                out.append(linhas[j])
            i = j + 1
            continue
        m = re.search(r"@(['\"])\s*$", ln)
        if m:
            q, j, corpo = m.group(1), i + 1, []
            while j < len(linhas) and not linhas[j].lstrip().startswith(q + "@"):
                corpo.append(linhas[j])
                j += 1
            depois = linhas[j].lstrip()[2:] if j < len(linhas) else ""
            if re.match(r"\s*\|\s*&?\s*\S*(?:python|py|node|powershell|pwsh|cmd|bash|iex|invoke-expression)", depois, re.I):
                out.extend(corpo)
            elif q == '"':  # @"..."@ executa o que estiver em $(...)
                out.extend(_SUBST["PowerShell"].findall("\n".join(corpo)))
            if j < len(linhas):
                out.append(linhas[j])
            i = j + 1
            continue
        i += 1
    return "\n".join(out)


def _segmentos(cmd):
    """Quebra o comando nos separadores fora de aspas (; && || | & quebra de linha) -> [[(aspas, texto), ...], ...]."""
    segs, partes, buf, i, n = [], [], [], 0, len(cmd)
    while i < n:
        ch = cmd[i]
        if ch == "\\" and i + 1 < n and cmd[i + 1] in "'\"":
            buf.append(cmd[i:i + 2])
            i += 2
            continue
        if ch in "'\"":
            if buf:
                partes.append(("", "".join(buf)))
                buf = []
            j, cont = i + 1, []
            while j < n and cmd[j] != ch:
                if ch == '"' and cmd[j] in "\\`" and j + 1 < n:
                    cont.append(cmd[j:j + 2])
                    j += 2
                    continue
                cont.append(cmd[j])
                j += 1
            partes.append((ch, "".join(cont)))
            i = j + 1
            continue
        if ch in "|;&\n":
            if ch == "&" and ((i and cmd[i - 1] in "<>") or cmd[i + 1:i + 2] == ">"):  # 2>&1, &>
                buf.append(ch)
                i += 1
                continue
            if buf:
                partes.append(("", "".join(buf)))
                buf = []
            if partes:
                segs.append(partes)
            partes = []
            i += 2 if cmd[i:i + 2] in ("||", "&&") else 1
            continue
        buf.append(ch)
        i += 1
    if buf:
        partes.append(("", "".join(buf)))
    if partes:
        segs.append(partes)
    return [p for p in segs if "".join(t for _, t in p).strip()]


def _cabeca(partes):
    for aspas, txt in partes:
        if aspas:
            if txt.strip():
                return txt.strip()
            continue
        for p in txt.split():
            p2 = p.lstrip("({!")
            if not p2 or p2.lower() in _PREFIXOS or re.fullmatch(r"[A-Za-z_]\w*=\S*", p2):
                continue
            return p2
    return ""


def _sub_comando(partes, nome):
    """Texto do comando que um shell (powershell -Command, bash -c, cmd /c, iex...) vai rodar: tudo depois da cabeça,
    sem as aspas e sem as opções do próprio shell. '' se não houver."""
    pals, viu_cabeca = [], False
    for aspas, txt in partes:
        if aspas:
            if not viu_cabeca and txt.strip() and _nome_cmd(txt) == nome:
                viu_cabeca = True
                continue
            pals.append(txt)
            continue
        for p in txt.split():
            if not viu_cabeca:
                if _nome_cmd(p.lstrip("({!&")) == nome:
                    viu_cabeca = True
                continue
            pals.append(p)
    while pals and (_FLAGS_SHELL.match(pals[0]) or pals[0] in ("&", ".")):
        pals.pop(0)
    return " ".join(pals).strip()


def _vistas_comando(cmd, permitir=(), shell="Bash", _nivel=0):
    """O comando em 2 vistas pra testar as regras: 'texto' (sem corpo de heredoc; sem as aspas de echo/Write-Host e
    sem strings longas, menos as de interpretador) e 'fora' (sem nada entre aspas), mais os segmentos com a classe do
    comando de cada um (leitura | inerte | interp | outro). Shell dentro de shell é aberto e conferido também."""
    segs, subst = [], _SUBST.get(shell, _SUBST["Bash"])
    for partes in _segmentos(_tirar_heredoc(str(cmd or ""))):
        nome = _nome_cmd(_cabeca(partes))
        if _nivel < 3 and _SHELLS.fullmatch(nome):
            sub = _sub_comando(partes, nome)
            if sub:
                interno = "PowerShell" if nome in ("powershell", "pwsh", "iex", "invoke-expression", "start-process",
                                                   "saps") else "Bash"
                segs.extend(_vistas_comando(sub, permitir, interno, _nivel + 1)["segmentos"])
        classe = ("interp" if _INTERP.fullmatch(nome) else "inerte" if nome in _INERTES
                  else "leitura" if nome in _LEITORES else "outro")
        marc = []
        for aspas, txt in partes:
            if not aspas:
                marc.append(txt)
                continue
            if classe == "inerte" or (classe != "interp" and len(txt) > 200):
                txt = " ".join(subst.findall(txt)) if aspas == '"' else ""
            marc.append(f"\x01{aspas}{txt}{aspas}\x02")
        m = "".join(marc)
        for r in permitir:
            m = r["re"].sub(" ", m)
        texto = m.replace("\x01", "").replace("\x02", "")
        fora = re.sub(r"\x01[^\x01\x02]*\x02", '""', m).replace("\x01", "").replace("\x02", "")
        segs.append({"cabeca": nome, "classe": classe, "texto": texto, "fora": fora})
    return {"segmentos": segs, "texto": "\n".join(s["texto"] for s in segs), "fora": "\n".join(s["fora"] for s in segs)}


def _casa(r, v):
    chave = "fora" if "fora_aspas" in r["opcoes"] else "texto"
    if "exec" in r["opcoes"]:
        return any(r["re"].search(s[chave]) for s in v["segmentos"] if s["classe"] not in ("leitura", "inerte"))
    return bool(r["re"].search(v[chave]))


_BUSCADORES = {"grep", "egrep", "fgrep", "rg", "findstr", "select-string", "sls", "ag", "ack"}


def _caminho_win(p):
    p = str(p).strip().strip("\"'")
    m = re.match(r"^/([a-zA-Z])(?:/|$)(.*)", p)
    return f"{m.group(1).upper()}:/{m.group(2)}" if m else p


def _raiz_tem_segredo(base):
    """A pasta (ou até 2 níveis abaixo) tem 'secrets' ou cookies*. Só olha disco; erro = não."""
    try:
        raiz = Path(_caminho_win(base))
        if not raiz.is_dir():
            return False
        for nivel in (raiz, *[d for d in raiz.iterdir() if d.is_dir()][:300]):
            for filho in nivel.iterdir():
                n = filho.name.lower()
                if n == "secrets" or n.startswith("cookie"):
                    return True
    except OSError:
        return False
    return False


def _filtro_seguro(filtro):
    """glob/type que só pega código/texto de projeto (não .json/.txt/.env, onde ficam chaves e cookies)."""
    f = str(filtro or "").strip().lower()
    if not f or re.search(r"secret|cookie|\.env|json|txt|jsonl", f):
        return False
    return bool(re.search(r"(?:\.(?:py|pyw|md|log|ps1|bat|cmd|js|ts|tsx|jsx|html|css|csv|sh|yaml|yml|toml|ini)\}?|"
                          r"^(?:py|python|js|ts|md|markdown|html|css|sh|ps1|yaml|toml))$", f))


def _grep_recursivo_em_segredo(segmentos, cwd):
    """24/10 (achado 15): grep -r/rg/findstr /s/Select-String -Recurse numa raiz com secrets/cookies, sem excluir
    nem limitar o tipo de arquivo, lê o conteúdo das chaves. -> motivo ou None."""
    tudo = "\n".join(s["texto"] for s in segmentos)
    for s in segmentos:
        cab, t = s["cabeca"], s["texto"]
        if cab in ("select-string", "sls"):  # sem -Recurse no comando, lê só o que veio pelo pipe ou o -Path
            rec = bool(re.search(r"-Recurse\b", tudo, re.I))
        elif cab in ("rg", "ag", "ack"):
            rec = True
        elif cab == "findstr":
            rec = bool(re.search(r"(?:^|\s)/[sS]\b", t))
        elif cab in _BUSCADORES:
            rec = bool(re.search(r"(?:^|\s)-(?!-)[a-zA-Z]{0,6}[rR][a-zA-Z]{0,6}(?=\s|$)|--recursive\b|--dereference-recursive",
                                 t))
        else:
            continue
        if not rec:
            continue
        if re.search(r"secret", t, re.I) and re.search(r"cookie", t, re.I) and re.search(
                r"--exclude|-g\s*['\"]?!|--glob\s*['\"]?!|-Exclude\b", t, re.I):
            continue
        if re.search(r"--include[= ]|(?:-g|--glob|-t|--type)\s*['\"]?[^!\s'\"]|-Include\b|-Filter\b", t, re.I):
            inc = re.findall(r"(?:--include[= ]|-g\s*|--glob\s*|-t\s*|--type\s*|-Include\s+|-Filter\s+)['\"]?([^\s'\"]+)",
                             t, re.I)
            if inc and all(_filtro_seguro(i) for i in inc):
                continue
        raizes = []
        for p in t.split()[1:]:  # os caminhos da busca (padrão e opções ficam de fora pelo teste de pasta)
            p = p.strip("\"'")
            if not p or p.startswith("-") or (p.startswith("/") and len(p) <= 3 and not re.match(r"^/[a-zA-Z]/?$", p)):
                continue
            cam = _caminho_win(p)
            if not re.match(r"^[A-Za-z]:", cam):
                if not re.search(r"[\\/*]|^\.{1,2}$", cam):
                    continue  # palavra solta (o padrão buscado)
                cam = os.path.join(cwd or "", cam)
            if re.search(r"[*?]|\.\w{1,5}$", Path(cam).name):  # arquivo ou glob de arquivo: vale a pasta dele
                cam = str(Path(cam).parent)
            raizes.append(cam)
        if not raizes and cab not in ("select-string", "sls"):
            raizes = [cwd or ""]
        if any(r and _raiz_tem_segredo(r) for r in raizes):
            return ("busca recursiva no conteúdo de uma pasta que tem secrets/cookies: exclua secrets e *cookie* "
                    "(--exclude-dir=secrets --exclude=*cookie*) ou limite o tipo (--include=*.py)")
    return None


def guarda_decidir(ferramenta, entrada, aplicar=False, regras=None, cwd=None):
    """Decide um passo do agente. -> {"bloquear": bool, "motivo": str|None, "suspeitos": [motivo, ...]}.
    regras=None lê config\\melhoria_guarda.json (sem arquivo = deixa tudo)."""
    regras = _regras_guarda() if regras is None else regras
    res = {"bloquear": False, "motivo": None, "suspeitos": []}
    if not regras:
        return res
    comp = _compilar_regras(regras)
    ent = entrada if isinstance(entrada, dict) else {}
    if ferramenta in ("Bash", "PowerShell"):
        v = _vistas_comando(ent.get("command") or "", comp["permitir"], ferramenta)
        for r in comp["segredos"]:
            if r["re"].search(v["texto"]):
                res.update(bloquear=True, motivo=f"mexer em segredo ({r['motivo']})")
                return res
        motivo = _grep_recursivo_em_segredo(v["segmentos"], cwd)
        if motivo:
            res.update(bloquear=True, motivo=motivo)
            return res
        listas = ["bloquear"] + (["bloquear_aplicar"] if aplicar else [])
        for lista in listas:
            for r in comp[lista]:
                if "grep" not in r["opcoes"] and _casa(r, v):
                    res.update(bloquear=True, motivo=r["motivo"])
                    return res
        sus = [r["motivo"] for r in comp["suspeito"] if "grep" not in r["opcoes"] and _casa(r, v)]
        if ent.get("run_in_background"):
            sus.append("rodou em segundo plano (pode continuar rodando depois do pedido)")
        res["suspeitos"] = list(dict.fromkeys(sus))
        return res
    if ferramenta in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        alvo = str(ent.get("file_path") or ent.get("notebook_path") or "")
        for r in comp["segredos"]:
            if alvo and r["re"].search(alvo):
                res.update(bloquear=True, motivo=f"escrever em segredo ({r['motivo']})")
                return res
        if ESCRITA_PROIBIDA.search(alvo):
            res.update(bloquear=True, motivo="escrever em cookies/login/mídia/voz (proibido: anote pra dona)")
            return res
        nome_alvo = Path(alvo).name.lower() if alvo else ""
        if nome_alvo in NUCLEO_GUARDA or re.search(r"\.claude[\\/]+settings", alvo, re.I):
            res.update(bloquear=True, motivo=f"escrever no NÚCLEO/config da guarda ({nome_alvo}): mudança só à mão, "
                                             "anote pra dona")
            return res
        # 24/10 (achado 12): script NOVO (ou em pasta temporária) gravado pra rodar depois passa pelas mesmas regras
        # do terminal. Edição de código que já existe não (o código do projeto tem shutil/os.replace legítimos)
        if ferramenta == "Write" and _EXT_SCRIPT.search(alvo) and (
                not Path(alvo).exists() or re.search(r"[\\/](?:tmp|temp)[\\/]", alvo, re.I)):
            corpo = str(ent.get("content") or "")
            v = {"segmentos": [{"cabeca": "python", "classe": "interp", "texto": corpo, "fora": corpo}],
                 "texto": corpo, "fora": corpo}
            for r in comp["bloquear"]:
                if "grep" not in r["opcoes"] and _casa(r, v):
                    res.update(bloquear=True, motivo=f"script novo faz o que é proibido ({r['motivo']})")
                    return res
        return res
    if ferramenta in ("Read", "Grep", "Glob"):
        base = str(ent.get("path") or cwd or "")
        if ferramenta == "Read":
            alvos = [str(ent.get("file_path") or ent.get("notebook_path") or "")]
        else:
            extra = str(ent.get("pattern" if ferramenta == "Glob" else "glob") or "")
            alvos = [base, os.path.join(base, extra) if extra else ""]
        for r in comp["segredos"]:
            if any(a and r["re"].search(a) for a in alvos):
                res.update(bloquear=True, motivo=f"ler segredo ({r['motivo']})")
                return res
        if ferramenta == "Grep" and base:  # 24/10 (achado 15): busca no conteúdo numa raiz com secrets/cookies
            filtro = str(ent.get("glob") or ent.get("type") or "")  # (Glob só lista nomes: não lê conteúdo)
            if _raiz_tem_segredo(base) and not _filtro_seguro(filtro):
                res.update(bloquear=True, motivo="busca recursiva numa pasta que tem secrets/cookies: "
                                                 "limite com glob (ex.: *.py) ou busque numa subpasta")
                return res
        if ferramenta == "Grep":
            busca = str(ent.get("pattern") or "")
            for r in comp["bloquear"]:
                if "grep" in r["opcoes"] and r["re"].search(busca):
                    res.update(bloquear=True, motivo=r["motivo"])
                    return res
    return res


def _cmd_curto(ferramenta, ent):
    ent = ent if isinstance(ent, dict) else {}
    if ferramenta in ("Bash", "PowerShell"):
        txt = str(ent.get("command") or "")
    elif ferramenta in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit"):
        txt = str(ent.get("file_path") or ent.get("notebook_path") or "")
    else:
        txt = f"{ent.get('pattern') or ''} em {ent.get('path') or '.'}" + (f" ({ent['glob']})" if ent.get("glob") else "")
    txt = " ".join(txt.split())  # nada de token no registro (24/10, achado 14: as mesmas trocas do camada_opus)
    txt = re.sub(r"(?:sk|pk|rk)-[\w-]{8,}", "<chave>", txt)
    txt = re.sub(r"(?i)(bearer\s+|x-api-key[\"':=\s]+|auth_token[\"':=\s]+)\S+", r"\1<chave>", txt)
    txt = re.sub(r"[A-Za-z0-9_\-+/=]{30,}", "<...>", txt)
    return txt[:300]


def _juntar_guarda(job):
    """Copia pro job os bloqueios/suspeitos que o hook anotou em <id>.guarda.jsonl (o rodador regrava o .json a cada
    linha; o arquivo à parte não se perde nessa troca)."""
    try:
        linhas = _arq(job["id"], ".guarda.jsonl").read_text(encoding="utf-8").splitlines()
    except (OSError, ValueError):
        return
    regs = {"bloqueios": [], "suspeitos": []}
    for ln in linhas:
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        campo = d.pop("campo", None)
        if campo in regs:
            regs[campo].append(d)
    for campo, lista in regs.items():
        if lista:
            job[campo] = lista[-200:]


def _registrar_guarda(jid, ferramenta, ent, res):
    novos = ([("bloqueios", res["motivo"])] if res.get("bloquear") else []) + [("suspeitos", s) for s in res.get("suspeitos") or []]
    if not novos or not jid:
        return
    curto = _cmd_curto(ferramenta, ent)
    regs = [{"campo": c, "t": _agora(), "ferramenta": ferramenta, "comando": curto, "motivo": m} for c, m in novos]
    try:
        with open(_arq(jid, ".guarda.jsonl"), "a", encoding="utf-8") as f:
            f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in regs))
    except (OSError, ValueError):
        return
    for _ in range(10):  # também no .json do pedido; rodando, quem junta é o rodador (a cada linha do stream), pra
        job = ler(jid)  # não disputar a gravação do .json com ele nem com o hook de backup (manifesto)
        if job:
            if job.get("status") != "rodando":
                try:
                    _juntar_guarda(job)
                    _gravar(job)
                except Exception:  # noqa: BLE001
                    pass
            return
        time.sleep(0.1)


def hook_guarda(eh_aplicar=False):
    """Hook PreToolUse (Bash|PowerShell|Read|Grep|Glob) dos pedidos de origem melhoria. -> 0 deixa, 2 bloqueia (motivo
    no stderr, o agente lê). Só vale com "ligado": true no melhoria_guarda.json."""
    try:
        bruto = sys.stdin.buffer.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return 0
    regras = _regras_guarda()
    jid = os.environ.get("PAINEL_IA_JOB", "")
    if not regras:  # 24/10 (achado 17): config ilegível num pedido do painel = fecha (antes abria tudo)
        if jid:
            sys.stderr.buffer.write("BLOQUEADO: a config da guarda (config\\melhoria_guarda.json) não abre; "
                                    "nada roda até a dona consertar.".encode("utf-8"))
            sys.stderr.flush()
            return 2
        return 0
    if not regras.get("ligado"):
        return 0
    job = None
    for _ in range(15):  # o rodador também grava o job: tenta de novo se pegar no meio da troca
        job = ler(jid) if jid else None
        if job or not jid:
            break
        time.sleep(0.1)
    if job is not None:
        if not _eh_melhoria(job):
            return 0
        # 24/10 (achado 18): os papéis "só leitura" (pergunta/propor: buscador, votante, críticos, revisores) também
        # não gravam pelo terminal. Todo pedido de melhoria leva o bloquear_aplicar
        eh_aplicar = True
    elif not jid:
        return 0  # sem pedido não é o painel (o hook só é ligado nos pedidos de origem melhoria)
    try:
        dados = json.loads(bruto or "{}")
    except ValueError:
        return 0
    nome, ent = dados.get("tool_name") or "", dados.get("tool_input") or {}
    try:
        res = guarda_decidir(nome, ent, aplicar=eh_aplicar, regras=regras, cwd=dados.get("cwd") or (job or {}).get("cwd"))
    except Exception as e:  # noqa: BLE001 — regra quebrada não pode abrir a porta
        res = {"bloquear": True, "suspeitos": [],
               "motivo": f"a guarda deu erro ao conferir ({type(e).__name__}); por segurança não deixei"}
    try:
        _registrar_guarda(jid, nome, ent, res)
    except Exception:  # noqa: BLE001
        pass
    if res["bloquear"]:
        msg = f"BLOQUEADO pela guarda das melhorias: {res['motivo']}. Isso é proibido aqui; anote pra dona em vez de fazer."
        sys.stderr.buffer.write(msg.encode("utf-8"))
        sys.stderr.flush()
        return 2
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fila":
        rodar_fila()
    elif len(sys.argv) > 1 and sys.argv[1] == "backup":
        hook_backup()
    elif len(sys.argv) > 1 and sys.argv[1] == "guarda":
        sys.exit(hook_guarda(eh_aplicar=len(sys.argv) > 2 and sys.argv[2] == "aplicar"))
    else:
        print(__doc__)
