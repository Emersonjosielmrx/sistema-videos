#!/usr/bin/env python3
"""Vigia com agente: mantém a produção rodando sem o VS Code aberto (pedido do dono, 17/10/2026).

Roda pela tarefa agendada `HipercoolVigia` (a cada 20 min). Duas camadas:

1. Checagem BARATA, em Python, sem modelo: lê os logs e os processos. Se está tudo andando, grava uma
   linha em logs/vigia.log e sai — nenhum token gasto.
2. Problema achado (render parado, FALHOU/Traceback novo nos logs) ou ronda de rotina a cada 4 h ->
   chama o Claude Code headless pelo proxy (secrets/claude_proxy.json, Sonnet do Kiro) com liberdade
   pra investigar e consertar.

O modelo é inferior ao que o dono usa pra revisar, então a regra é RASTRO: toda ação vai pro
docs/VIGIA_DIARIO.md, todo arquivo mexido tem cópia em workspace/vigia_backups/<hora>/ antes, e ao fim
de cada intervenção sai um Telegram dizendo o que fez e se precisa de revisão.

    python bin/vigia_agente.py            # uma rodada (o que a tarefa agendada chama)
    python bin/vigia_agente.py --forcar   # chama o agente mesmo sem problema
    python bin/vigia_agente.py --so-checar
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

PROJ = Path(__file__).resolve().parent.parent
LOGS = PROJ / "logs"
ESTADO = PROJ / "workspace" / "vigia_estado.json"
TRAVA = PROJ / "workspace" / "vigia_agente.lock"
DIARIO = PROJ / "docs" / "VIGIA_DIARIO.md"
CLAUDE = PROJ / "tools" / "claude" / "claude.exe"
PROXY = PROJ / "secrets" / "claude_proxy.json"

PARADO_MIN = 45          # render rodando sem escrever no log há mais que isso = travado
RONDA_H = 4              # ronda de rotina, mesmo sem problema
AGENTE_TIMEOUT_MIN = 40
LOGS_VIGIADOS = ["refazer_caps.log", "fila_ciclo.log", "fila_postagem.log", "corrigir_pendentes.log",
                 "lancamento_pt.log"]
ERRO = re.compile(r"\bFALHOU\b|Traceback|\[X\]|\bERRO\b", re.I)  # \b: "interrompe" casava com "erro"
# Ruído de rotina que NÃO é problema (cota/chave trocando sozinha, proxy, análise recusando vídeo): sem este
# filtro o vigia chamaria o agente a cada 20 min por causa de um 429 do Gemini.
RUIDO = re.compile(r"Gemini LLM|HTTP 4\d\d|trocando combo|proxy|esgotou max_attempts|quota|cota|"
                   r"nao_aprovado|sem cota|capa IA|versão anterior em uso", re.I)
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha)
    with open(LOGS / "vigia.log", "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_estado(e):
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")


def _processos():
    """Linhas de comando dos python/ffmpeg do hipercool rodando agora."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name like 'python%' or Name like 'ffmpeg%'\" | "
          "ForEach-Object { $_.CommandLine }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                       timeout=60, creationflags=_SEM_JANELA, encoding="utf-8", errors="replace")
    return [l for l in (r.stdout or "").splitlines() if "hipercool" in l.lower()]


def checar(estado):
    """Lista de problemas (texto curto cada). Atualiza os offsets dos logs no estado."""
    problemas = []
    procs = _processos()
    pipeline = [p for p in procs if "hiper-pipeline.py" in p]
    if pipeline:
        caps = sorted(LOGS.glob("fila_*-cap*.log"), key=lambda p: p.stat().st_mtime, reverse=True)

        def _terminou(p):  # 22/10: o log do cap14 acabou em 19/10 com "Vídeo pronto" e virava "travado há 4611 min"
            try:
                with open(p, "rb") as fh:
                    fh.seek(max(0, p.stat().st_size - 2000))
                    return b"V\xc3\xaddeo pronto" in fh.read()
            except OSError:
                return False
        caps = [p for p in caps[:5] if not _terminou(p)]  # o render vivo escreve num log que ainda não terminou
        if caps:
            parado = (time.time() - caps[0].stat().st_mtime) / 60
            if parado > PARADO_MIN:
                problemas.append(f"render rodando mas {caps[0].name} sem escrever há {parado:.0f} min (travado?)")
    offs = estado.setdefault("offsets", {})
    for nome in LOGS_VIGIADOS + [p.name for p in LOGS.glob("fila_*-cap*.log")]:
        arq = LOGS / nome
        if not arq.exists():
            continue
        tam = arq.stat().st_size
        ini = offs.get(nome, tam)  # log visto pela 1ª vez: só o que vier depois conta
        if tam < ini:
            ini = 0
        if tam > ini:
            with open(arq, "rb") as f:
                f.seek(ini)
                novo = f.read().decode("utf-8", "replace")
            ruins = [l.strip() for l in novo.splitlines() if ERRO.search(l) and not RUIDO.search(l)]
            if ruins:
                problemas.append(f"{nome}: " + " | ".join(r[:160] for r in ruins[-3:]))
        offs[nome] = tam
    estado["ultima_checagem"] = time.time()
    estado["processos"] = len(procs)
    return problemas


PROMPT = """Você é o VIGIA da produção de vídeos do hipercool (D:\\hipercool-videos), rodando sozinho,
sem ninguém olhando. O dono está fora; outro agente mais forte vai revisar tudo o que você fizer.

MOTIVO DESTA CHAMADA:
{motivo}

PRIMEIRO leia: CLAUDE.md, docs/VIGIA_DIARIO.md (o que vigias anteriores já fizeram), e os logs em logs/
(refazer_caps.log, fila_ciclo.log, fila_postagem.log, fila_<obra>-capNN.log, vigia.log).

SEU TRABALHO: manter a produção andando. Investigue o motivo acima. Se for problema real e o conserto
for claro, conserte (pode editar código em bin/, relançar o que caiu do jeito que já é lançado). Se não
tiver certeza, NÃO mexa: descreva e peça revisão.

REGRAS DURAS (quebrar qualquer uma é pior do que deixar parado):
- Antes de editar QUALQUER arquivo, copie o original para workspace/vigia_backups/{hora}/ (mesmo nome).
- NUNCA apague vídeos, Shorts, caches, roteiros ou pastas de workspace/videos, workspace/shorts,
  D:/hipercool-materiais. NUNCA rode limpeza de disco.
- NUNCA poste nada nem mexa em config de postagem (postar_pt, rede_canais, credenciais, canais).
- NUNCA afrouxe censura (limiares, LIMIAR_DUVIDA, níveis) nem pule bin/revisao_video.py.
- NUNCA mate processos pythonw em outra máquina (pc2). Aqui, só mate um processo se provar que está
  travado (log parado e sem CPU), e diga qual.
- Render pesado é um por vez: não lance render se já houver hiper-pipeline rodando.
- Não troque vozes do elenco (config/elenco) nem o motor de TTS.
- NUNCA ligue/desligue a fila nem a postagem: não apague nem crie config/FILA_DESLIGADA.json ou
  config/POSTAGEM_DESLIGADA.json, não rode `fila.py ligar/desligar`, não mexa em tarefas agendadas.
  Fila desligada quase sempre é DE PROPÓSITO (ex.: bin/refazer_caps.py fazendo o trabalho dela).
  (17/10: o 1º teste do vigia religou a fila no meio de um refazer_caps e teve de ser desfeito.)
- NUNCA edite workspace/fila_estado.json: quem grava ali é a fila e o refazer_caps. Se o estado parecer
  errado, descreva e peça revisão.
- Vídeo terminando (revisão/análise rodando depois do "[OK] Vídeo pronto") NÃO é travamento.
- Não faça git push, não instale pacotes.
- Nada de mudança grande: conserto pequeno e cirúrgico. Refatoração = pedir revisão.

RASTRO OBRIGATÓRIO: ao terminar, ACRESCENTE (não reescreva) ao fim de docs/VIGIA_DIARIO.md uma seção:
## {hora} — <resumo em 1 linha>
- Motivo: ...
- O que achei (com trecho de log): ...
- O que fiz (comandos e arquivos mexidos, com caminho do backup): ...
- Como desfazer: ...
- Estado: RESOLVIDO | PRECISA REVISÃO | NADA A FAZER

ÚLTIMA LINHA da sua resposta, exatamente uma destas:
STATUS: OK
STATUS: CONSERTEI - <o que, em 1 linha>
STATUS: REVISAR - <por que, em 1 linha>
"""

PROMPT_CONSULTA = """Você é o assistente de produção de vídeos. O dono mandou uma mensagem pelo Telegram
e você responde RÁPIDO — NÃO leia arquivos nem logs a menos que a pergunta exija.

MENSAGEM:
{motivo}

COMO RESPONDER:
- Para dados (views, ranking, comentários, uploads, canais, filas): rode o comando certo e resuma o resultado.
- Para estado da produção: o resumo já está acima, use ele. Só leia logs se o dono pedir detalhes.
- Para algo que precise modificar código/config: siga as REGRAS DURAS abaixo.
- Responda em português, curto e direto.

REGRAS DURAS (valem sempre):
- NUNCA apague vídeos, Shorts, caches ou pastas de workspace/videos, workspace/shorts, D:/hipercool-materiais.
- NUNCA poste nada nem mexa em config de postagem, censura, elenco ou fila.
- NUNCA ligue/desligue a fila nem a postagem.
- NUNCA edite workspace/fila_estado.json.
- NUNCA mate processos pythonw em outra máquina (pc2).
- Antes de editar QUALQUER arquivo, copie o original para workspace/vigia_backups/ primeiro.
- Se não tiver certeza, NÃO mexa: descreva e peça revisão.

Antes da linha STATUS, escreva uma linha começando com 'RESPOSTA:' com a resposta pro dono,
curta, em português simples (até 800 caracteres).

ÚLTIMA LINHA: STATUS: OK
"""


_FERRAMENTA = {"Bash": "rodando comando", "PowerShell": "rodando comando", "Read": "lendo", "Grep": "procurando",
               "Glob": "procurando arquivos", "Edit": "editando", "Write": "gravando", "WebFetch": "abrindo página"}


def _passo(bloco):
    """Texto curto de 1 passo do agente (stream-json) para o Telegram, ou None."""
    if bloco.get("type") == "text":
        t = " ".join((bloco.get("text") or "").split())
        return ("💬 " + t[:400]) if len(t) > 15 and "STATUS:" not in t and "RESPOSTA:" not in t else None
    if bloco.get("type") == "tool_use":
        nome, ent = bloco.get("name", "?"), bloco.get("input") or {}
        alvo = ent.get("description") or ent.get("file_path") or ent.get("pattern") or ent.get("command") or ""
        return f"🔧 {_FERRAMENTA.get(nome, nome)}: {str(alvo)[:160]}"
    return None


def _rodar_com_progresso(cmd, env, progresso, minimo_s=20):
    """Roda o claude em stream-json e manda os passos por `progresso(texto)` (no máximo 1 a cada `minimo_s`, juntando
    os do meio). Devolve o texto final (o "result"), igual ao modo text."""
    p = subprocess.Popen(cmd, cwd=str(PROJ), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", creationflags=_SEM_JANELA)
    fim, final, juntos, ultimo = time.time() + AGENTE_TIMEOUT_MIN * 60, "", [], 0.0
    textos = []
    try:
        for ln in p.stdout:
            if time.time() > fim:
                p.kill()
                final += f"\n[vigia] agente passou de {AGENTE_TIMEOUT_MIN} min e foi interrompido"
                break
            try:
                ev = json.loads(ln)
            except ValueError:
                textos.append(ln)
                continue
            if ev.get("type") == "result":
                final = ev.get("result") or final
            elif ev.get("type") == "assistant":
                for b in (ev.get("message") or {}).get("content") or []:
                    if b.get("type") == "text":
                        textos.append(b.get("text") or "")
                    s = _passo(b)
                    if s:
                        juntos.append(s)
            if juntos and time.time() - ultimo >= minimo_s:
                try:
                    progresso("\n".join(juntos[-6:]))
                except Exception:  # noqa: BLE001 — Telegram fora não para o agente
                    pass
                juntos, ultimo = [], time.time()
        p.wait(timeout=30)
    except Exception as e:  # noqa: BLE001
        final += f"\n[vigia] erro lendo o agente: {e}"
    return (final or "\n".join(textos)).strip()


def chamar_agente(motivo, avisar=True, max_turns=60, modo="vigia", modelos=None, extra_args=(), progresso=None):
    """Roda o agente. Devolve (status, detalhe, texto da resposta) ou None se outro já está rodando.
    modo='vigia' usa PROMPT (lê tudo, conserta). modo='consulta' usa PROMPT_CONSULTA (rápido, só responde).
    modelos/extra_args (26/10): o vigia geral passa só Gemini e bloqueia as ferramentas de escrita (modo só aviso)."""
    if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < AGENTE_TIMEOUT_MIN * 60 + 120:
        log("agente já rodando (trava) — pulo")
        return None
    TRAVA.write_text(str(os.getpid()))
    hora = datetime.now().strftime("%Y%m%d_%H%M")
    cfg = json.loads(PROXY.read_text(encoding="utf-8"))
    env = dict(os.environ, ANTHROPIC_BASE_URL=cfg["base_url"], ANTHROPIC_AUTH_TOKEN=cfg["auth_token"],
               PYTHONUTF8="1", PATH=r"D:\hipercool-materiais\bin" + os.pathsep + os.environ.get("PATH", ""))
    env.pop("ANTHROPIC_API_KEY", None)
    if modelos:  # 26/10: título da sessão ("haiku") também sai do Kiro
        env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = env["ANTHROPIC_SMALL_FAST_MODEL"] = list(modelos)[0]
    if r"D:\video-fila" not in sys.path:  # ia_reserva e base_consertos (comuns do vigia geral); no PC2 não existe
        sys.path.append(r"D:\video-fila")
    parecidos = ""
    if modo == "vigia":  # frente E (dono 21/10, "o vigia aprende"): casos parecidos já resolvidos, como no vigia geral
        try:
            import base_consertos
            parecidos = base_consertos.bloco_prompt(motivo)
        except Exception:  # noqa: BLE001  (a base nunca derruba o vigia)
            parecidos = ""
        if parecidos:
            log(f"base de consertos: {parecidos.count(chr(10))} caso(s) parecido(s) no prompt")
    tpl = PROMPT_CONSULTA if modo == "consulta" else PROMPT
    prompt = tpl.format(motivo=motivo + (f"\n\n{parecidos}" if parecidos else ""), hora=hora)
    saida = LOGS / f"vigia_agente_{hora}.log"
    try:  # 22/10: Kiro sem crédito (zera antes do dia 1) -> reserva grátis do gateway (D:\video-fila\ia_reserva.py)
        import ia_reserva
        ordem = list(modelos) if modelos else ia_reserva.modelos(cfg["modelo"])
    except ImportError:
        ia_reserva, ordem = None, list(modelos) if modelos else [cfg["modelo"]]
    texto = ""
    try:
        for modelo in ordem:
            log(f"chamando agente ({modelo}, {modo}, {max_turns}t): {motivo[:200]}")
            extra = (ia_reserva.AVISO_RESERVA if ia_reserva and ia_reserva.eh_reserva(modelo) and modo != "consulta"
                     and not modelos else "")
            if progresso:  # 01/11: Funcionário de Plantão — os passos vão pro Telegram enquanto ele trabalha
                texto = _rodar_com_progresso([str(CLAUDE), "-p", prompt + extra, "--model", modelo,
                                              "--output-format", "stream-json", "--verbose", "--max-turns",
                                              str(max_turns), "--dangerously-skip-permissions", *extra_args],
                                             env, progresso)
                if not (ia_reserva and ia_reserva.falhou_sem_trabalhar(texto)):
                    break
                ia_reserva.marcar(modelo)
                continue
            try:
                r = subprocess.run([str(CLAUDE), "-p", prompt + extra, "--model", modelo, "--output-format", "text",
                                    "--max-turns", str(max_turns), "--dangerously-skip-permissions", *extra_args],
                                   cwd=str(PROJ), env=env, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=AGENTE_TIMEOUT_MIN * 60, creationflags=_SEM_JANELA)
                texto = (r.stdout or "") + ("\n[stderr]\n" + r.stderr if r.stderr else "")
            except subprocess.TimeoutExpired as e:
                texto = (e.stdout or "") if isinstance(e.stdout, str) else ""
                texto += f"\n[vigia] agente passou de {AGENTE_TIMEOUT_MIN} min e foi interrompido"
                break
            if not (ia_reserva and ia_reserva.falhou_sem_trabalhar(texto)):
                break
            ia_reserva.marcar(modelo)
            log(f"modelo {modelo} recusado pelo gateway ({' '.join(texto.split())[:150]}): fica fora 1 h, vai o próximo")
    finally:
        TRAVA.unlink(missing_ok=True)
    saida.write_text(texto, encoding="utf-8")
    # o modelo às vezes escreve "**STATUS:** OK" (markdown) ou "CONCLUÍDO": aceita os dois
    m = re.findall(r"STATUS:?\**\s*\**\s*(OK|CONSERTEI|REVISAR|CONCLU[IÍ]DO)\**[ \t]*[-—:]?[ \t]*(.*)", texto, re.I)
    m = [("OK" if s.upper().startswith("CONCLU") else s.upper(), d) for s, d in m]
    status, detalhe = m[-1] if m else ("REVISAR", "agente não devolveu STATUS (ver log)")
    log(f"agente terminou: {status} {detalhe[:200]} -> {saida.name}")
    if status != "OK" and avisar:
        try:
            import notificar
            nivel = "aviso" if status == "CONSERTEI" else "erro"
            notificar.aviso(f"Vigia: {status}", f"{detalhe[:300]}\nMotivo: {motivo[:300]}\n"
                            f"Rastro: docs/VIGIA_DIARIO.md e logs/{saida.name}", nivel=nivel)
        except Exception as e:  # noqa: BLE001
            log(f"[!] Telegram falhou: {e}")
    return status, detalhe, texto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forcar", action="store_true")
    ap.add_argument("--so-checar", action="store_true")
    a = ap.parse_args()
    if not DIARIO.exists():
        DIARIO.write_text("# Diário do vigia\n\nCada intervenção do vigia automático (bin/vigia_agente.py, "
                          "Sonnet pelo proxy). Revisar o que estiver marcado PRECISA REVISÃO.\n", encoding="utf-8")
    est = _estado()
    problemas = checar(est)
    ronda = time.time() - est.get("ultima_ronda", 0) > RONDA_H * 3600
    _gravar_estado(est)
    if not problemas:
        log(f"ok ({est['processos']} processos hipercool)" + (" — ronda de rotina" if ronda else ""))
    else:
        log("PROBLEMAS: " + " || ".join(problemas))
    if a.so_checar:
        return
    if problemas or ronda or a.forcar:
        motivo = ("\n".join(f"- {p}" for p in problemas) if problemas else
                  "- Ronda de rotina (nenhum erro achado pela checagem automática): confira se a fila está "
                  "andando de verdade (capítulo novo saindo, nada parado há horas) e não mexa no que está bem.")
        chamar_agente(motivo)
        est = _estado()
        est["ultima_ronda"] = time.time()
        _gravar_estado(est)


if __name__ == "__main__":
    main()
