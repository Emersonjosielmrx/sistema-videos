"""Motor: Claude Code sem janela (claude.exe -p) pelo OmniRoute, com o modelo da config (Opus 5.5 das contas pagas).

Ele roda dentro da pasta do trabalho e pode LER as imagens dela (ferramenta Read) — é assim que "enxerga" as cenas
e os quadros do vídeo. Só leitura: não edita nem roda comando (quem renderiza é o Python).

Erros:
  SemCota   429/limite/créditos -> quem chamou pausa o trabalho até a cota voltar (vídeo do zero) ou segue sem o
            Claude (adicional)
  MotorErro qualquer outra falha (resposta vazia, JSON inválido, timeout)
Cada chamada vai para estado/consumo.jsonl (tokens + pontos antes) para recalibrar o custo da config.
"""
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONSUMO = RAIZ / "estado" / "consumo.jsonl"
EXT = Path.home() / ".vscode" / "extensions"


class SemCota(Exception):
    pass


class MotorErro(Exception):
    pass


def _exe():
    """claude.exe da extensão mais nova (a pasta muda de nome a cada atualização)."""
    achados = sorted(EXT.glob("anthropic.claude-code-*/resources/native-binary/claude.exe"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
    if not achados:
        raise MotorErro("claude.exe não encontrado nas extensões do VS Code")
    return str(achados[0])


_SEM_COTA = re.compile(r"429|rate.?limit|quota|exhausted|credit|usage limit|limit reached|overloaded", re.I)


_SOBRA_RENDER = ("puppeteer_dev_chrome_profile-", "playwright-artifacts-", "react-motion-render",
                 "remotion-webpack-bundle-", "remotion-v4")


def _limpar_tmp(tmp, idade=2 * 3600):
    """29/10: cada render/still deixava o perfil do Chrome do Remotion no TEMP — 435 perfis, 11 GB, disco a 1,7 GB."""
    import shutil
    agora = time.time()
    for nome in os.listdir(tmp):
        p = os.path.join(tmp, nome)
        try:
            if nome.startswith(_SOBRA_RENDER) and agora - os.path.getmtime(p) > idade:
                shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass


def executar(cmd, cwd, timeout, env=None, entrada=None, baixa=False):
    """subprocess com saída em ARQUIVO e morte da árvore inteira no tempo limite. 26/10: o Chrome do Remotion
    travou, o timeout matou só o npx e os netos seguraram o pipe — o gerar.py ficou 2h20 parado em communicate().
    Devolve (código, saída+erro) ou levanta subprocess.TimeoutExpired."""
    import tempfile
    import psutil
    # 27/10: render deu "ENOSPC" com o C: quase cheio (o Remotion grava os quadros no TEMP) -> temporários no D:
    tmp = r"D:\hipercool-materiais\tmp\claude-code-video"
    os.makedirs(tmp, exist_ok=True)
    _limpar_tmp(tmp)
    env = dict(env or os.environ, TEMP=tmp, TMP=tmp)
    with tempfile.TemporaryFile(dir=tmp) as out:
        # baixa: só o que é PESADO (render, clone, editor com stills) cede a CPU às outras linhas; comando curto não
        # (27/10: com tudo em prioridade baixa e a CPU a 100%, um ffmpeg de 1 s estourou 15 min)
        p = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.PIPE if entrada is not None else None,
                             stdout=out, stderr=subprocess.STDOUT,
                             creationflags=0x08000000 | (0x00004000 if baixa else 0))  # sem janela sempre
        try:
            if entrada is not None:
                p.stdin.write(entrada)
                p.stdin.close()
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                for x in psutil.Process(p.pid).children(recursive=True) + [psutil.Process(p.pid)]:
                    x.kill()
            except psutil.Error:
                pass
            raise
        out.seek(0)
        return p.returncode, out.read().decode("utf-8", "replace")


SO_LER = ("Read", "Bash,Edit,Write,WebFetch,WebSearch,Agent")
# modo EDITOR (25/10): o Claude Code escreve a edição em código (Remotion), roda o render de quadros e olha
EDITOR = ("Read,Write,Edit,Glob,Grep,Bash", "WebFetch,WebSearch,Agent")


_CONTINUE = ("Outro modelo começou esta tarefa e parou no prazo; o que ele já fez está no disco: confira, continue e "
             "termine (não recomece do zero).\n\n")


def chamar(prompt, pasta, projeto, etapa, timeout=600, max_turnos=12, ferramentas=SO_LER, modelo=None,
           aceitar_limite=False):
    """Cadeia para o vídeo não demorar (dona 27/10): Argon (prazo curto) -> Gemini 3.8 Antigravity (prazo curto) ->
    Gemini por API no OmniRoute (prazo inteiro). Começa no degrau do modelo pedido; estourou ou falhou = próximo
    degrau, que continua do que já está no disco. Cada troca vai para consumo.jsonl como fallback_<etapa>."""
    cfg = json.loads((RAIZ / "config.json").read_text("utf-8"))
    cadeia = cfg.get("cadeia_modelos") or []
    modelo_ef = modelo or cfg["modelo"]
    # "tambem": outros modelos que valem como esse degrau (27/10: hx-maos-gemini no editor, argon-gemini no roteiro)
    ini = next((i for i, d in enumerate(cadeia) if modelo_ef == d["modelo"] or modelo_ef in d.get("tambem", [])), None)
    if ini is None:
        return _chamar1(prompt, pasta, projeto, etapa, timeout, max_turnos, ferramentas, modelo, aceitar_limite)
    degraus = [{**cadeia[ini], "modelo": modelo_ef}] + cadeia[ini + 1:]
    for n, d in enumerate(degraus):
        ultimo = n == len(degraus) - 1
        prazo = timeout if ultimo else min(timeout, (d.get("prazos") or {}).get(etapa, d.get("padrao", 600)))
        try:
            txt = _chamar1(prompt, pasta, projeto, etapa, prazo, max_turnos, ferramentas, d["modelo"],
                           aceitar_limite)
            if ultimo or not txt.startswith("(parou no tempo limite"):
                return txt
            motivo = f"passou de {prazo}s"
            if not prompt.startswith(_CONTINUE):
                prompt = _CONTINUE + prompt
        except (MotorErro, SemCota) as e:
            if ultimo:
                raise
            motivo = str(e)[:120]
        _registrar(projeto, f"fallback_{etapa}", datetime.now(), None,
                   f"{d['modelo']} -> {degraus[n + 1]['modelo']}: {motivo}")


def _chamar1(prompt, pasta, projeto, etapa, timeout, max_turnos, ferramentas, modelo, aceitar_limite):
    cfg = json.loads((RAIZ / "config.json").read_text("utf-8"))
    modelo = modelo or cfg["modelo"]
    env = dict(os.environ, ANTHROPIC_BASE_URL=cfg["gateway"], ANTHROPIC_AUTH_TOKEN=cfg["chave"],
               ANTHROPIC_MODEL=modelo, ANTHROPIC_DEFAULT_OPUS_MODEL=modelo, ANTHROPIC_DEFAULT_SONNET_MODEL=modelo,
               ANTHROPIC_DEFAULT_HAIKU_MODEL=modelo, ANTHROPIC_SMALL_FAST_MODEL=modelo,
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
               # MURAL 26/10 (PRODUTOS): editor/corretor estourava "32000 output tokens" reescrevendo arquivo grande
               CLAUDE_CODE_MAX_OUTPUT_TOKENS="64000")
    env.pop("ANTHROPIC_API_KEY", None)
    cmd = [_exe(), "-p", "--output-format", "json", "--max-turns", str(max_turnos),
           "--setting-sources", "project",          # sem os hooks/prompts do chat do dono
           "--allowedTools", ferramentas[0], "--disallowedTools", ferramentas[1]]
    ini = datetime.now()
    etapa = etapa if modelo == cfg["modelo"] else f"{etapa}[{modelo}]"
    try:
        _, saida = executar(cmd, pasta, timeout, env=env, entrada=prompt.encode("utf-8"), baixa=ferramentas == EDITOR)
    except subprocess.TimeoutExpired:
        _registrar(projeto, etapa, ini, None, "timeout")
        if aceitar_limite:
            return f"(parou no tempo limite de {timeout}s)"
        raise MotorErro(f"timeout {timeout}s")
    res = None
    for linha in reversed(saida.strip().splitlines()):
        if linha.startswith("{"):
            try:
                res = json.loads(linha)
                break
            except ValueError:
                pass
    if res is None:
        erro = saida[-400:]
        _registrar(projeto, etapa, ini, None, erro)
        if _SEM_COTA.search(erro):
            raise SemCota(erro)
        raise MotorErro(f"saída inválida: {erro}")
    _registrar(projeto, etapa, ini, res, None if not res.get("is_error") else str(res.get("result"))[:300])
    if aceitar_limite and res.get("subtype") == "error_max_turns":
        # editor/corretor: o que ele mudou já está no disco; quem chamou renderiza e confere
        return (res.get("result") or "").strip() or "(parou no limite de turnos)"
    if res.get("is_error") or res.get("subtype") != "success":
        txt = f"{res.get('api_error_status')} {res.get('result')}"
        if res.get("api_error_status") == 429 or _SEM_COTA.search(txt):
            raise SemCota(txt[:300])
        raise MotorErro(txt[:300])
    texto = (res.get("result") or "").strip()
    if not texto:
        raise MotorErro("resposta vazia")
    return texto


def chamar_json(prompt, pasta, projeto, etapa, **kw):
    """Como chamar(), mas devolve o 1º objeto JSON da resposta (1 nova tentativa se vier quebrado)."""
    for tentativa in range(2):
        txt = chamar(prompt if not tentativa else prompt + "\n\nIMPORTANTE: responda SÓ o JSON válido, nada mais.",
                     pasta, projeto, etapa, **kw)
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                pass
    raise MotorErro(f"JSON inválido: {txt[:200]}")


def _registrar(projeto, etapa, ini, res, erro):
    u = (res or {}).get("usage") or {}
    linha = {"em": ini.isoformat(timespec="seconds"), "projeto": projeto, "etapa": etapa,
             "segundos": round((datetime.now() - ini).total_seconds(), 1),
             "entrada": u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
             "cache_lido": u.get("cache_read_input_tokens", 0), "saida": u.get("output_tokens", 0),
             "turnos": (res or {}).get("num_turns"), "erro": erro}
    CONSUMO.parent.mkdir(exist_ok=True)
    with CONSUMO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
