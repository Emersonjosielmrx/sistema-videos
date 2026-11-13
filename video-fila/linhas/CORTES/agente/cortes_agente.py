# -*- coding: utf-8 -*-
"""cortes_agente.py — o agente da linha CORTES (dona 27/10/2026: "o sistema que vai substituir este chat a cada
rodada, com os meus pedidos extras; abrir um chat pra falar com ele onde ele está; corrigir código com o modelo que
eu passar; tirar quadros, cortar, corrigir e testar; mexer no PC2").

Uma sessão SÓ do Claude Code (pasta desta linha\\agente, instruções no CLAUDE.md, permissões em .claude\\settings.json,
Argon como ferramenta pelo .mcp.json). As rodadas continuam a mesma conversa; o atalho abre ESSA conversa no
terminal pra dona digitar. Enquanto ela conversa, a rodada não roda (trava .conversando).

    python cortes_agente.py rodada [--forcar]   # 1 rodada (tarefa Cortes_Agente; DESLIGADA até a dona mandar)
    python cortes_agente.py conversar           # abre a conversa no terminal (atalho da Área de Trabalho)
    python cortes_agente.py status
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CFG = AQUI / "agente.json"
TRAVA = AQUI / ".conversando"
LOG = AQUI / "rodadas.log"
ULTIMA = AQUI / "ULTIMA_RODADA.md"
GATEWAY = Path(r"D:\claude-code-video\config.json")  # gateway (proxy :20133, onde estão Argon/argon-flash) e chave
FERRAMENTAS = "Bash,Read,Edit,Write,Glob,Grep,mcp__gemini-argon__ask_argon"


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M}] {m}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _cfg():
    return json.loads(CFG.read_text(encoding="utf-8"))


def _gravar(c):
    CFG.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")


def _exe():
    achados = sorted((Path.home() / ".vscode" / "extensions").glob(
        "anthropic.claude-code-*/resources/native-binary/claude.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not achados:
        sys.exit("claude.exe não encontrado nas extensões do VS Code")
    return str(achados[0])


def _env(modelo):
    g = json.loads(GATEWAY.read_text(encoding="utf-8"))
    env = dict(os.environ, ANTHROPIC_BASE_URL=g["gateway"], ANTHROPIC_AUTH_TOKEN=g["chave"], ANTHROPIC_MODEL=modelo,
               ANTHROPIC_DEFAULT_OPUS_MODEL=modelo, ANTHROPIC_DEFAULT_SONNET_MODEL=modelo,
               ANTHROPIC_DEFAULT_HAIKU_MODEL=modelo, ANTHROPIC_SMALL_FAST_MODEL=modelo,
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", PYTHONIOENCODING="utf-8")
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def _conversando():
    try:
        pid = int(TRAVA.read_text().strip())
    except (OSError, ValueError):
        return False
    try:
        import psutil
        return psutil.pid_exists(pid)
    except ImportError:
        return True


def _turno(c, modelo, texto):
    cmd = [_exe(), "-p", "--output-format", "json", "--max-turns", str(c.get("max_turnos_rodada", 80)),
           "--setting-sources", "project", "--allowedTools", FERRAMENTAS]
    if c.get("sessao"):
        cmd += ["--resume", c["sessao"]]
    p = subprocess.run(cmd, cwd=AQUI, env=_env(modelo), input=texto.encode("utf-8"), capture_output=True,
                       timeout=int(c.get("timeout_rodada_s", 3600)), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    saida = p.stdout.decode("utf-8", "replace")
    for linha in reversed(saida.strip().splitlines()):
        if linha.startswith("{"):
            try:
                return json.loads(linha)
            except ValueError:
                pass
    return {"is_error": True, "result": (saida + p.stderr.decode("utf-8", "replace"))[-500:]}


def rodada(forcar=False, texto=None):
    c = _cfg()
    if not forcar and not c.get("ligado"):
        return log("desligado (agente.json ligado=false) — nada")
    if _conversando():
        return log("a dona está conversando com o agente — rodada fica pra próxima")
    texto = texto or (f"RODADA AUTOMÁTICA {datetime.now():%d/%m/%Y %H:%M}. Siga a seção 'Uma rodada' do CLAUDE.md "
                      "(UMA tarefa, com prova real, teste, PC2 sincronizado e DECISOES/ESTADO). Termine com o resumo.")
    for modelo in (c["modelo"], c.get("modelo_reserva")):
        if not modelo:
            continue
        try:
            r = _turno(c, modelo, texto)
        except subprocess.TimeoutExpired:
            r = {"is_error": True, "result": f"timeout {c.get('timeout_rodada_s')} s"}
        if not r.get("is_error") and r.get("subtype") == "success":
            c["sessao"] = r.get("session_id") or c.get("sessao")
            _gravar(c)
            ULTIMA.write_text(f"# Rodada {datetime.now():%d/%m %H:%M} ({modelo})\n\n{r.get('result', '')}\n", encoding="utf-8")
            return log(f"rodada ok ({modelo}, {r.get('num_turns')} turnos): {str(r.get('result', ''))[:300]}")
        log(f"rodada com {modelo} falhou: {str(r.get('result'))[:300]} — reserva")
    log("rodada sem resposta dos modelos")


def conversar():
    c = _cfg()
    TRAVA.write_text(str(os.getpid()))
    try:
        cmd = [_exe(), "--setting-sources", "project"] + (["--resume", c["sessao"]] if c.get("sessao") else [])
        print(f"Conversa com o agente da linha CORTES ({c['modelo']}). Para sair: /exit\n", flush=True)
        subprocess.call(cmd, cwd=AQUI, env=_env(c["modelo"]))
    finally:
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else "status"
    if acao == "rodada":
        rodada(forcar="--forcar" in sys.argv)
    elif acao == "conversar":
        conversar()
    else:
        c = _cfg()
        print(f"ligado={c.get('ligado')} modelo={c['modelo']} reserva={c.get('modelo_reserva')} sessao={c.get('sessao')} "
              f"conversando={_conversando()}")
